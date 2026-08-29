"""
tests/interpretive/test_observation_extractor.py
Tests for agent/interpretive/observation_extractor.py's extract_observation()
and to_vision_payload() -- the capture-complete ObservationRecord contract.
MOCKS the LLM throughout -- no live API call. Fake OpenAI client classes
transplanted from tests/interpretive/test_claim_extraction.py (same
client.chat.completions.create(...) surface, same call-order-indexed
`responses=[content, ...]` convention -- content-only here, no per-call
exception slot, since this module's only raised-from-the-API-call error
is the whole-call RuntimeError in `_call_llm`, not exercised per-attempt
the way test_claim_extraction.py's does).

Hardest case first, per project convention: real captured life-line prose
("deep, long, curves around the base of the thumb, no breaks") where a
genuine observation ("curves around the base of the thumb") has no
matching ontology value token. Proves CAPTURE, not drop: it must land in
`unmapped`, not vanish, while "long"/"deep" still tokenize normally.
"""

from __future__ import annotations

import json

import pytest

from agent.interpretive.observation_extractor import (
    _CLOSED_VOCAB,
    _FEATURE_ALIAS,
    _MOUNT_DEVELOPMENT_MENUS,
    ObservationRecord,
    all_aliased_features,
    extract_mount_development,
    extract_observation,
    extract_relations,
    merge_relational_targets,
    to_vision_payload,
)

# ─── Fake OpenAI client -- transplanted from test_claim_extraction.py ────


class _FakeMessage:
    def __init__(self, content: str):
        self.content = content


class _FakeChoice:
    def __init__(self, content: str):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content: str):
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    """`responses`, if given, is a list of content strings consumed in call
    order -- lets a single fake answer the first attempt and a retry
    attempt differently (e.g. malformed JSON then valid JSON), matching
    test_claim_extraction.py's call-order convention. Past the end of
    `responses`, the LAST entry is reused (clamped index) -- a test
    proving "never a further call" must assert `len(.calls)` explicitly,
    not rely on this clamping to crash."""

    def __init__(self, content: str | None = None, responses: list[str] | None = None):
        self._content = content
        self._responses = responses
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self._responses is not None:
            idx = min(len(self.calls) - 1, len(self._responses) - 1)
            return _FakeResponse(self._responses[idx])
        return _FakeResponse(self._content)


class _FakeClient:
    def __init__(self, content: str | None = None, responses: list[str] | None = None):
        self.completions = _FakeCompletions(content=content, responses=responses)
        self.chat = type("_FakeChat", (), {"completions": self.completions})()


def _response(observations: dict, unmapped: dict | None = None) -> str:
    return json.dumps({"observations": observations, "unmapped": unmapped or {}})


# ─── Sanity: registry-derived constants sane before relying on them ──────


def test_alias_table_has_nineteen_keys_seventeen_mapped_two_none():
    # S96: 9 more mount aliases (7 new mounts + 2 extra Cheiro synonyms --
    # "mount of apollo" and "mount of the moon" -- collapsing onto an
    # already-mapped canonical feature) landed alongside the original 10-key
    # table's 8 mapped + 2 None entries. Measured, not assumed: 19 total
    # keys, 17 mapped (to 15 DISTINCT ontology features, since two of the
    # mapped keys are synonyms of another mapped key), 2 still None.
    assert len(_FEATURE_ALIAS) == 19
    mapped = {k: v for k, v in _FEATURE_ALIAS.items() if v is not None}
    unmapped = {k: v for k, v in _FEATURE_ALIAS.items() if v is None}
    assert len(mapped) == 17
    assert set(unmapped) == {"fingers", "markings/other features"}
    for ontology_feature in mapped.values():
        assert ontology_feature in _CLOSED_VOCAB


# ─── HARDEST CASE FIRST: capture, not drop ───────────────────────────────


def test_hardest_case_unmatched_quality_captured_not_dropped():
    fake = _FakeClient(content=_response(
        observations={
            "Line of Life": {
                "Length": {"value": "long"},
                "Depth": {"value": "deep"},
            },
        },
        unmapped={
            "Line of Life": [
                {"quality": "curves around the base of the thumb", "attribute_guess": "Curve"},
            ],
        },
    ))
    record = extract_observation(
        {"life line": ["deep, long, curves around the base of the thumb, no breaks"]},
        client=fake,
    )
    assert isinstance(record, ObservationRecord)
    fobs = record.features["Line of Life"]
    assert fobs.tokens == {
        "Length": {"value": "long", "confidence": 1.0},
        "Depth": {"value": "deep", "confidence": 1.0},
    }
    assert {"quality": "curves around the base of the thumb", "attribute_guess": "Curve"} in fobs.unmapped
    assert fobs.raw_prose == "deep, long, curves around the base of the thumb, no breaks"
    assert len(fake.completions.calls) == 1


# ─── enabled_features: allow-list applied AFTER capture ─────────────────


def test_disabled_feature_fully_captured_but_dropped_from_payload():
    fake = _FakeClient(content=_response(
        observations={
            "Line of Life": {"Length": {"value": "long"}},
            "Line of Head": {"Direction": {"value": "straight"}},
        },
    ))
    record = extract_observation(
        {"life line": ["long"], "head line": ["straight"]},
        enabled_features={"Line of Head"},
        client=fake,
    )
    # capture is total regardless of enabled_features
    assert "Line of Life" in record.features
    assert record.features["Line of Life"].tokens == {
        "Length": {"value": "long", "confidence": 1.0},
    }
    assert record.dropped_disabled == ["Line of Life"]

    payload = to_vision_payload(record, enabled_features={"Line of Head"})
    assert "Line of Life" not in payload
    assert payload == {"Line of Head": {"Direction": {"value": "straight", "confidence": 1.0}}}


# ─── Quality with no token and no attribute guess -> unmapped, not tokens ─


def test_quality_with_no_attribute_guess_lands_in_unmapped_not_tokens():
    fake = _FakeClient(content=_response(
        observations={},
        unmapped={
            "Line of Head": [
                {"quality": "an odd texture near the start", "attribute_guess": None},
            ],
        },
    ))
    record = extract_observation({"head line": ["an odd texture near the start"]}, client=fake)
    fobs = record.features["Line of Head"]
    assert fobs.tokens == {}
    assert fobs.unmapped == [{"quality": "an odd texture near the start", "attribute_guess": None}]


# ─── Empty feature_texts -> empty record, no raise, no LLM call ─────────


def test_empty_feature_texts_returns_empty_record_no_llm_call():
    fake = _FakeClient(content="should never be read")
    record = extract_observation({}, client=fake)
    assert record == ObservationRecord(features={}, dropped_disabled=[], unmappable_prose_features=[])
    assert len(fake.completions.calls) == 0


def test_feature_texts_with_only_blank_strings_returns_empty_record_no_llm_call():
    fake = _FakeClient(content="should never be read")
    record = extract_observation({"life line": ["", "   "]}, client=fake)
    assert record.features == {}
    assert len(fake.completions.calls) == 0


# ─── all_aliased_features: single source of truth, never hardcoded ──────


def test_all_aliased_features_is_the_non_none_value_set_of_feature_alias():
    """DERIVATION, not a literal list: must equal every non-None value in
    `_FEATURE_ALIAS`, so a future alias addition widens this with no code
    edit at any call site. The literal set is asserted too, as a canary --
    15 DISTINCT features (S96), not 17: "mount of apollo"/"mount of the
    moon" are Cheiro synonyms collapsing onto "Mount of the Sun"/"Mount of
    Luna", each already reached by another key."""
    expected = frozenset(f for f in _FEATURE_ALIAS.values() if f is not None)
    assert all_aliased_features() == expected
    assert all_aliased_features() == frozenset({
        "Line of Life", "Line of Head", "Line of Heart", "Line of Fate",
        "Line of Sun", "Thumb", "Mount of Venus", "Mount of Jupiter",
        "Mount of Saturn", "Mount of the Sun", "Mount of Mercury",
        "Upper Mount of Mars", "Lower Mount of Mars", "Mount of Luna",
        "Plain of Mars",
    })
    # The two None entries ("fingers", "markings/other features") must
    # never surface here -- they have no ontology counterpart to unblock.
    assert None not in all_aliased_features()


# ─── to_vision_payload round-trips into to_tokens()'s expected shape ─────


def test_to_vision_payload_round_trips_into_to_tokens_accepted_shape():
    from agent.interpretive import observation_to_tokens

    fake = _FakeClient(content=_response(
        observations={"Line of Life": {"Length": {"value": "long"}, "Depth": {"value": "deep"}}},
    ))
    record = extract_observation({"life line": ["long, deep"]}, client=fake)
    payload = to_vision_payload(record)
    observation, magnitudes = observation_to_tokens.to_tokens(payload)
    assert observation == {"Line of Life": {"Length": "long", "Depth": "deep"}}
    assert magnitudes["Line of Life"] == {"Length": 1.0, "Depth": 1.0}


def test_to_vision_payload_omits_feature_with_no_tokens():
    fake = _FakeClient(content=_response(
        observations={},
        unmapped={"Line of Life": [{"quality": "something vague", "attribute_guess": None}]},
    ))
    record = extract_observation({"life line": ["something vague"]}, client=fake)
    assert to_vision_payload(record) == {}


# ─── Unmappable prose feature (fingers/markings) -- visible, not invisible ─


def test_unmappable_prose_feature_visible_not_invisible():
    fake = _FakeClient(content=_response(
        observations={"Line of Life": {"Length": {"value": "long"}}},
    ))
    record = extract_observation(
        {"fingers": ["long and slender"], "life line": ["long"]},
        client=fake,
    )
    assert record.unmappable_prose_features == [
        {"prose_feature": "fingers", "raw_prose": "long and slender"},
    ]
    # never reached the prompt
    sent_prompt = fake.completions.calls[0]["messages"][1]["content"]
    assert "Finger" not in sent_prompt


# ─── Out-of-vocabulary LLM emission -- folded into unmapped, never tokens ─


def test_out_of_vocabulary_emission_folded_into_unmapped_not_tokens():
    # "shimmery" is confirmed absent from the full registry value pool --
    # if the LLM violates its own closed-vocabulary instruction, the
    # Python-side guard must still keep it out of `tokens`, but it must
    # now be VISIBLE in `unmapped` rather than silently vanishing.
    fake = _FakeClient(content=_response(
        observations={"Line of Head": {"Direction": {"value": "shimmery"}}},
    ))
    record = extract_observation(
        {"head line": ["the head line looks faintly wavy and shimmery"]},
        client=fake,
    )
    fobs = record.features["Line of Head"]
    assert fobs.tokens == {}
    assert {"quality": "shimmery", "attribute_guess": "Direction"} in fobs.unmapped


# ─── JSON parse failure -> ValueError with snippet ───────────────────────


def test_json_parse_failure_raises_value_error_with_snippet():
    fake = _FakeClient(content="this is not valid json at all")
    with pytest.raises(ValueError, match="not valid json"):
        extract_observation({"life line": ["long"]}, client=fake)


def test_missing_observations_key_raises_value_error_with_snippet():
    fake = _FakeClient(content=json.dumps({"wrong_key": {}}))
    with pytest.raises(ValueError, match="observations"):
        extract_observation({"life line": ["long"]}, client=fake)


def test_missing_unmapped_key_does_not_raise_defaults_empty():
    # older/partially-compliant response shape: only "observations" present
    fake = _FakeClient(content=json.dumps({
        "observations": {"Line of Life": {"Length": {"value": "long"}}},
    }))
    record = extract_observation({"life line": ["long"]}, client=fake)
    assert record.features["Line of Life"].unmapped == []


# ─── Parse-failure crash fix: bounded resample regression tests ─────────
# Real-hand dogfood hit a malformed/truncated-JSON response escaping
# `_parse_response`'s ValueError before the (separate) dropped-feature
# retry logic ever ran, crashing the whole extraction; a manual retry of
# the same call succeeded. `_call_llm_and_parse` fixes this with a
# bounded resample scoped to parse failures. Input text here ("long") is
# deliberately short/trivial -- `_is_substantive_prose`'s 15-char floor
# keeps it out of the SEPARATE dropped-feature retry loop, so these
# tests isolate the parse-failure path from that other retry mechanism.


def test_parse_failure_recovers_on_resample():
    # T1 RECOVERY: malformed JSON on attempt 1, valid JSON on attempt 2.
    valid = _response(observations={"Line of Life": {"Length": {"value": "long"}}})
    fake = _FakeClient(responses=["not valid json at all", valid])
    record = extract_observation({"life line": ["long"]}, client=fake)
    assert record.features["Line of Life"].tokens["Length"]["value"] == "long"
    # exactly 2 calls: attempt 1 (malformed) + 1 resample (valid) -- proves
    # the resample fired and recovery came from it, not a lucky first try.
    assert len(fake.completions.calls) == 2


def test_parse_failure_exhausts_retries_and_raises_same_value_error():
    # T2 FAIL-CLOSED: malformed JSON on EVERY attempt.
    fake = _FakeClient(content="still not valid json")
    with pytest.raises(ValueError, match="not valid json"):
        # pytest.raises proves extract_observation raised rather than
        # returning any value -- no fabricated/empty ObservationRecord
        # is ever produced on final parse-failure exhaustion.
        extract_observation({"life line": ["long"]}, client=fake)
    # ASTRO_EXTRACT_PARSE_RETRIES default is 2 -> 3 attempts total (initial
    # + 2 resamples) for this parse-failure path; only ONE outer
    # dropped-feature-retry iteration runs (trivial "long" prose never
    # triggers that separate loop), so this is also the TOTAL call count.
    assert len(fake.completions.calls) == 3


def test_parse_failure_resample_raises_max_tokens_and_appends_corrective_message():
    # T3 RETRY SHAPE: cleanly assertable via `.calls`' recorded kwargs.
    valid = _response(observations={"Line of Life": {"Length": {"value": "long"}}})
    fake = _FakeClient(responses=["not valid json at all", valid])
    extract_observation({"life line": ["long"]}, client=fake)
    assert len(fake.completions.calls) == 2
    first_call, retry_call = fake.completions.calls
    # Canary literals -- must track _call_llm's ASTRO_EXTRACT_MAX_TOKENS
    # default (1500) and _call_llm_and_parse's ASTRO_EXTRACT_PARSE_RETRY_
    # MAX_TOKENS default (2400); not derived from the source to keep this
    # a real regression check rather than a tautology.
    assert first_call["max_tokens"] == 1500
    assert retry_call["max_tokens"] == 2400
    # retry's message list = original + exactly one corrective message
    assert len(retry_call["messages"]) == len(first_call["messages"]) + 1
    corrective = retry_call["messages"][-1]
    assert corrective["role"] == "user"
    assert "valid complete JSON" in corrective["content"]


# ─── Confidence: prose hedging lowers it, else defaults to 1.0 ──────────


def test_hedged_prose_lowers_confidence():
    fake = _FakeClient(content=_response(
        observations={"Line of Head": {"Direction": {"value": "straight"}}},
    ))
    record = extract_observation(
        {"head line": ["the head line is possibly straight"]},
        client=fake,
    )
    assert record.features["Line of Head"].tokens["Direction"]["confidence"] == 0.6


def test_non_hedged_prose_defaults_confidence_to_one():
    fake = _FakeClient(content=_response(
        observations={"Line of Head": {"Direction": {"value": "straight"}}},
    ))
    record = extract_observation(
        {"head line": ["the head line is straight"]},
        client=fake,
    )
    assert record.features["Line of Head"].tokens["Direction"]["confidence"] == 1.0


# ─── LLM emits a feature outside the requested batch -> dropped entirely ─


def test_llm_emitted_feature_outside_requested_batch_is_dropped():
    fake = _FakeClient(content=_response(
        observations={
            "Line of Life": {"Length": {"value": "long"}},
            "Line of Heart": {"Position": {"value": "high"}},  # never requested this call
        },
    ))
    record = extract_observation({"life line": ["long"]}, client=fake)
    assert set(record.features) == {"Line of Life"}


# ─── Relational targets -- directed antecedent parsing (S89 -> S90 wiring) ──
# _ATHIRA_ORIGINAL_RUN_1 is the real, validated vision output ("ORIGINAL
# RUN 1" of the S89 A/B probe, diagnostics/relational_ab_raw.txt) -- not a
# hand-constructed fixture.

_ATHIRA_ORIGINAL_RUN_1 = """HAND SHAPE: elongated palm, medium build

FINGERS: medium length relative to palm, straight, rounded fingertips, medium spacing

THUMB: medium size, low set, moderate angle from the palm

LIFE LINE: present, deep, narrow, long, curves around the base of the thumb, no breaks/chains/forks/islands visible

HEAD LINE: present, deep, narrow, long, straight across
  SLOPE: straight

HEART LINE: present, deep, narrow, long, curves slightly upward
  SLOPE: upward

FATE LINE: present, deep, narrow, long, runs vertically towards the middle finger
  SLOPE: straight

HEAD LINE RELATIONAL:
  ORIGIN: Line of Life
  PROXIMITY: medium to Line of Life
  TERMINATION: Mount of Mars
  BRANCHES_TO: none

HEART LINE RELATIONAL:
  ORIGIN: Mount of Jupiter
  PROXIMITY: medium to Line of Head
  TERMINATION: Mount of Mercury
  BRANCHES_TO: none

FATE LINE RELATIONAL:
  ORIGIN: Wrist
  PROXIMITY: medium to Line of Life
  TERMINATION: Mount of Saturn
  BRANCHES_TO: none

OTHER LINES: none clearly visible

MOUNTS: Mount of Venus developed, others unremarkable

MARKS: none clearly visible
"""


def test_extract_relations_builds_correct_mapping_from_validated_athira_output():
    # TERMINATION's raw value "Mount of Mars" is not itself a
    # relation_target_registry member (only "Upper Mount of Mars"/"Lower
    # Mount of Mars" are) -- correctly fail-closed dropped, not coerced.
    targets = extract_relations(_ATHIRA_ORIGINAL_RUN_1)["targets"]
    assert targets == {
        "Line of Head": {
            "Starting_Point": "Line of Life",
            "Proximity": "Line of Life",
        },
        "Line of Heart": {
            "Starting_Point": "Mount of Jupiter",
            "Proximity": "Line of Head",
            "Position": "Mount of Mercury",
        },
        "Line of Fate": {
            "Starting_Point": "Wrist",
            "Proximity": "Line of Life",
            "Position": "Mount of Saturn",
        },
    }


def test_extract_relations_drops_none_and_out_of_registry_landmarks():
    text = (
        "HEAD LINE RELATIONAL:\n"
        "  ORIGIN: none\n"
        "  PROXIMITY: n/a to none\n"
        "  TERMINATION: Not A Real Landmark\n"
        "  BRANCHES_TO: Line of Head\n"
    )
    targets = extract_relations(text)["targets"]
    assert targets == {"Line of Head": {"Branching": "Line of Head"}}


def test_extract_relations_empty_for_text_without_relational_block():
    assert extract_relations("HAND SHAPE: elongated palm, medium build")["targets"] == {}


def test_extract_relations_targets_raises_typeerror_for_non_str_input():
    with pytest.raises(TypeError):
        extract_relations(None)["targets"]


def test_merge_relational_targets_right_hand_wins_on_collision():
    left = {"Line of Head": {"Starting_Point": "Line of Life"}}
    right = {
        "Line of Head": {"Starting_Point": "Mount of Jupiter"},
        "Line of Fate": {"Position": "Mount of Saturn"},
    }
    merged = merge_relational_targets(left, right)
    assert merged == {
        "Line of Head": {"Starting_Point": "Mount of Jupiter"},
        "Line of Fate": {"Position": "Mount of Saturn"},
    }


def test_existing_observation_extraction_unchanged_alongside_relational_parsing():
    """Parsing relational targets shares no state with extract_observation's
    LLM-mediated token extraction -- calling one first must not perturb
    the other's result for the same underlying input."""
    fake = _FakeClient(content=_response(
        observations={"Line of Head": {"Direction": {"value": "straight"}}},
    ))
    extract_relations(_ATHIRA_ORIGINAL_RUN_1)["targets"]
    record = extract_observation({"head line": ["straight across"]}, client=fake)
    assert record.features["Line of Head"].tokens == {
        "Direction": {"value": "straight", "confidence": 1.0}
    }


# ─── Convergence targets -- Pattern C step 2a (S98) ──────────────────────
# Convergence/Convergence_Location are one of the parse strategies the
# unified extract_relations() (Generalization step 2a/2c-i, S98) dispatches
# on -- these tests exercise that strategy in isolation, via extract_
# relations()'s "targets" output.


def test_convergence_noncanonical_emission_flips_owner_to_alphabetically_first():
    """HEART LINE emits the convergence, but "Line of Head" sorts before
    "Line of Heart" -- owner must be the canonical feature, not whichever
    block happened to emit the statement."""
    text = (
        "HEART LINE RELATIONAL:\n"
        "  CONVERGENCE: Line of Head\n"
    )
    targets = extract_relations(text)["targets"]
    assert targets == {"Line of Head": {"Convergence": {"Line of Heart"}}}


def test_convergence_emitted_from_both_blocks_is_idempotent_no_conflict():
    """The SAME real convergence stated from EITHER line's own block must
    collapse to one identical canonical entry, not two entries or a
    conflicting overwrite."""
    text = (
        "HEAD LINE RELATIONAL:\n"
        "  CONVERGENCE: Line of Heart\n"
        "\n"
        "HEART LINE RELATIONAL:\n"
        "  CONVERGENCE: Line of Head\n"
    )
    targets = extract_relations(text)["targets"]
    assert targets == {"Line of Head": {"Convergence": {"Line of Heart"}}}


def test_convergence_location_before_convergence_resolves_correct_owner():
    """LOCATION appearing BEFORE CONVERGENCE in source order must still be
    filed under the block's eventual canonical owner, not dropped or
    misfiled under the emitting (non-canonical) feature."""
    text = (
        "FATE LINE RELATIONAL:\n"
        "  CONVERGENCE_LOCATION: Mount of Jupiter\n"
        "  CONVERGENCE: Line of Heart\n"
    )
    targets = extract_relations(text)["targets"]
    assert targets == {
        "Line of Fate": {
            "Convergence": {"Line of Heart"},
            "Convergence_Location": "Mount of Jupiter",
        }
    }


def test_convergence_f025b_shape_fate_heart_ascend_jupiter():
    """F025b: Fate and Heart converge and ascend together to Mount of
    Jupiter -- owner is Line of Fate ("Fate" < "Heart" alphabetically)."""
    text = (
        "FATE LINE RELATIONAL:\n"
        "  CONVERGENCE: Line of Heart\n"
        "  CONVERGENCE_LOCATION: Mount of Jupiter\n"
    )
    targets = extract_relations(text)["targets"]
    assert targets == {
        "Line of Fate": {
            "Convergence": {"Line of Heart"},
            "Convergence_Location": "Mount of Jupiter",
        }
    }


def test_convergence_target_not_in_registry_drops_convergence_and_its_location():
    """Drop case 1: an invalid CONVERGENCE target drops the convergence AND
    its block's location -- no owner ever resolves, so the location has
    nothing to canonicalize against."""
    text = (
        "FATE LINE RELATIONAL:\n"
        "  CONVERGENCE: Not A Real Landmark\n"
        "  CONVERGENCE_LOCATION: Mount of Jupiter\n"
    )
    assert extract_relations(text)["targets"] == {}


def test_convergence_self_convergence_is_dropped():
    """Drop case 2: a feature stating convergence with itself is invalid --
    dropped, no owner resolves."""
    text = (
        "FATE LINE RELATIONAL:\n"
        "  CONVERGENCE: Line of Fate\n"
    )
    assert extract_relations(text)["targets"] == {}


def test_convergence_location_orphan_with_no_convergence_in_block_is_dropped():
    """Drop case 3: CONVERGENCE_LOCATION with no valid CONVERGENCE anywhere
    in the same block is an orphan -- dropped, nothing filed."""
    text = (
        "FATE LINE RELATIONAL:\n"
        "  CONVERGENCE_LOCATION: Mount of Jupiter\n"
    )
    assert extract_relations(text)["targets"] == {}


def test_convergence_location_not_in_registry_drops_location_only():
    """Drop case 4: an invalid CONVERGENCE_LOCATION drops only the
    location -- the block's own valid CONVERGENCE is unaffected."""
    text = (
        "FATE LINE RELATIONAL:\n"
        "  CONVERGENCE: Line of Heart\n"
        "  CONVERGENCE_LOCATION: Not A Real Landmark\n"
    )
    targets = extract_relations(text)["targets"]
    assert targets == {"Line of Fate": {"Convergence": {"Line of Heart"}}}


def test_convergence_malformed_empty_none_na_values_are_dropped():
    """Drop case 5: 'none'/'n-a'/empty values are dropped the same way
    the directional strategy treats them -- for both subfields, and
    across separate blocks in the same call."""
    text = (
        "FATE LINE RELATIONAL:\n"
        "  CONVERGENCE: none\n"
        "  CONVERGENCE_LOCATION: n/a\n"
        "\n"
        "HEAD LINE RELATIONAL:\n"
        "  CONVERGENCE: \n"
    )
    assert extract_relations(text)["targets"] == {}


def test_convergence_empty_raw_text_returns_empty_dict_no_raise():
    assert extract_relations("")["targets"] == {}


def test_convergence_targets_empty_for_text_without_convergence_subfields():
    assert extract_relations("HAND SHAPE: elongated palm, medium build")["targets"] == {}


def test_convergence_raises_typeerror_for_non_str_input():
    with pytest.raises(TypeError):
        extract_relations(None)["targets"]


def test_convergence_inline_line_header_format_also_recognized():
    """The inline "<LINE>:" header format (no separate RELATIONAL: block)
    must be recognized identically to the RELATIONAL: block format."""
    text = "FATE LINE: present, deep\n  CONVERGENCE: Line of Heart\n"
    targets = extract_relations(text)["targets"]
    assert targets == {"Line of Fate": {"Convergence": {"Line of Heart"}}}


# ─── extract_relations -- Generalization step 2a (S98) ───────────────────
# The one-time >=25-case differential battery that proved extract_relations()
# byte-identical to the (now-migrated-off-of) three original functions was
# deleted here at Generalization 2c-i: its purpose (a new==old parity proof)
# is complete and preserved in commit history; it cannot run once those
# three functions are retired (2c-ii), and calling already-migrated tests
# "differential" against themselves would be meaningless.


def test_extract_relations_raises_typeerror_for_non_str_input():
    with pytest.raises(TypeError):
        extract_relations(None)


# ─── extract_mount_development -- S117 vision-emission follow-up ─────────
# Hardest case first (project convention): per-mount menu enforcement,
# since it is the one behavior that would be silently wrong under a naive
# "single global Development vocabulary" implementation (the shape
# ontology_registry.json's attribute_value_binding is limited to today --
# see the section comment above extract_mount_development for why this
# function does NOT ride that mechanism).


def test_extract_mount_development_per_mount_menu_enforcement_not_global():
    """A value that IS legal for Venus ('full and large') but NOT legal
    for Jupiter, emitted under Jupiter's own DEVELOPMENT line, must be
    rejected -- proving the menus are genuinely per-mount, not one shared
    global vocabulary a Venus-legal value could sneak through anywhere."""
    assert "full and large" in _MOUNT_DEVELOPMENT_MENUS["mount of venus"]
    assert "full and large" not in _MOUNT_DEVELOPMENT_MENUS["mount of jupiter"]

    text = "  DEVELOPMENT (Jupiter): full and large\n"
    assert extract_mount_development(text) == {}

    # Sanity: the SAME value, emitted under Venus (where it belongs), is accepted.
    text_venus = "  DEVELOPMENT (Venus): full and large\n"
    assert extract_mount_development(text_venus) == {
        "mount of venus": {"Development": "full and large"}
    }


def test_extract_mount_development_maps_aliased_vision_names_to_registry_keys():
    """Each graded mount's value parses into the correct
    palm_reading._FEATURE_REGISTRY key -- including the two renamed
    aliases (vision says "the Sun"/"Upper Mount of Mars"; the registry key
    is "mount of apollo"/"mount of mars positive") plus the three
    non-aliased graded mounts (Venus/Jupiter/Saturn, vision name ==
    registry-key noun)."""
    text = (
        "  DEVELOPMENT (Venus): well developed\n"
        "  DEVELOPMENT (Jupiter): developed\n"
        "  DEVELOPMENT (Saturn): unusually high\n"
        "  DEVELOPMENT (the Sun): well developed\n"
        "  DEVELOPMENT (Upper Mount of Mars): large\n"
    )
    assert extract_mount_development(text) == {
        "mount of venus": {"Development": "well developed"},
        "mount of jupiter": {"Development": "developed"},
        "mount of saturn": {"Development": "unusually high"},
        "mount of apollo": {"Development": "well developed"},
        "mount of mars positive": {"Development": "large"},
    }


def test_extract_mount_development_escape_hatches_carry_through_as_values():
    """'cannot-tell' and 'not notably developed' are ordinary members of
    every per-mount menu -- they must be captured as real Development
    values, never silently dropped as if they were non-answers."""
    text = (
        "  DEVELOPMENT (Venus): cannot-tell\n"
        "  DEVELOPMENT (Jupiter): not notably developed\n"
        "  DEVELOPMENT (Saturn): cannot-tell\n"
        "  DEVELOPMENT (the Sun): not notably developed\n"
        "  DEVELOPMENT (Upper Mount of Mars): cannot-tell\n"
    )
    assert extract_mount_development(text) == {
        "mount of venus": {"Development": "cannot-tell"},
        "mount of jupiter": {"Development": "not notably developed"},
        "mount of saturn": {"Development": "cannot-tell"},
        "mount of apollo": {"Development": "not notably developed"},
        "mount of mars positive": {"Development": "cannot-tell"},
    }


def test_extract_mount_development_presence_only_mount_produces_no_observation():
    """Mercury/Lower Mount of Mars/Luna are presence-only (Step 2 never
    asks them a grade question) -- ordinary MOUNTS prose naming them with
    no DEVELOPMENT line must produce no Development observation at all,
    no crash, no phantom value. Also covers the defensive case of a rogue
    DEVELOPMENT line naming one anyway (should Step 2's prompt ever be
    violated) -- still dropped, not guessed, via the same quarantine path
    as any other rejection."""
    ordinary_prose = (
        "MOUNTS: Mount of Mercury is unremarkable, Lower Mount of Mars is "
        "unremarkable, Mount of the Moon is unremarkable.\n"
    )
    assert extract_mount_development(ordinary_prose) == {}

    rogue_line = (
        "  DEVELOPMENT (Mercury): well developed\n"
        "  DEVELOPMENT (Lower Mount of Mars): large\n"
        "  DEVELOPMENT (the Moon): well developed\n"
    )
    assert extract_mount_development(rogue_line) == {}


def test_extract_mount_development_off_menu_garbage_dropped_like_other_off_menu_values():
    """An off-menu DEVELOPMENT value is dropped + quarantined -- the same
    treatment _store_contact gives an off-menu CONTACTS target (see that
    function's own docstring: 'Off-menu -> dropped + logged (quarantine),
    never guessed'), not coerced to a nearest legal value and not raised
    as an error."""
    text = "  DEVELOPMENT (Venus): utterly massive\n"
    assert extract_mount_development(text) == {}

    # An unrecognized mount name entirely (not one of the 8 registry
    # mounts at all) is quarantined the same way, never guessed at.
    text_unknown_mount = "  DEVELOPMENT (Neptune): well developed\n"
    assert extract_mount_development(text_unknown_mount) == {}

    # A well-formed line for a real graded mount, but garbage everywhere
    # else in the text, doesn't crash or leak -- exactly one accepted key.
    text_mixed = (
        "HAND SHAPE: square palm\n"
        "  DEVELOPMENT (Venus): well developed\n"
        "  DEVELOPMENT (Jupiter): extremely gigantic\n"
    )
    assert extract_mount_development(text_mixed) == {
        "mount of venus": {"Development": "well developed"}
    }


def test_extract_mount_development_raises_typeerror_for_non_str_input():
    with pytest.raises(TypeError):
        extract_mount_development(None)


def test_extract_mount_development_empty_for_text_without_any_development_line():
    assert extract_mount_development("HAND SHAPE: elongated palm, medium build") == {}
