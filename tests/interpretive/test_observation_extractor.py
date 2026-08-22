"""
tests/interpretive/test_observation_extractor.py
Tests for agent/interpretive/observation_extractor.py's extract_observation()
and to_vision_payload() -- the capture-complete ObservationRecord contract.
MOCKS the LLM throughout -- no live API call. Fake OpenAI client classes
transplanted from tests/interpretive/test_claim_extraction.py (same
client.chat.completions.create(...) surface, same responses=[(content,
exception), ...] call-order convention, simplified here since this module
makes at most ONE call, never a retry).

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
    ObservationRecord,
    all_aliased_features,
    extract_observation,
    extract_relational_targets,
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
    def __init__(self, content: str | None = None):
        self._content = content
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return _FakeResponse(self._content)


class _FakeClient:
    def __init__(self, content: str | None = None):
        self.completions = _FakeCompletions(content=content)
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


def test_extract_relational_targets_builds_correct_mapping_from_validated_athira_output():
    # TERMINATION's raw value "Mount of Mars" is not itself a
    # relation_target_registry member (only "Upper Mount of Mars"/"Lower
    # Mount of Mars" are) -- correctly fail-closed dropped, not coerced.
    targets = extract_relational_targets(_ATHIRA_ORIGINAL_RUN_1)
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


def test_extract_relational_targets_drops_none_and_out_of_registry_landmarks():
    text = (
        "HEAD LINE RELATIONAL:\n"
        "  ORIGIN: none\n"
        "  PROXIMITY: n/a to none\n"
        "  TERMINATION: Not A Real Landmark\n"
        "  BRANCHES_TO: Line of Head\n"
    )
    targets = extract_relational_targets(text)
    assert targets == {"Line of Head": {"Branching": "Line of Head"}}


def test_extract_relational_targets_empty_for_text_without_relational_block():
    assert extract_relational_targets("HAND SHAPE: elongated palm, medium build") == {}


def test_extract_relational_targets_raises_typeerror_for_non_str_input():
    with pytest.raises(TypeError):
        extract_relational_targets(None)


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
    extract_relational_targets(_ATHIRA_ORIGINAL_RUN_1)
    record = extract_observation({"head line": ["straight across"]}, client=fake)
    assert record.features["Line of Head"].tokens == {
        "Direction": {"value": "straight", "confidence": 1.0}
    }
