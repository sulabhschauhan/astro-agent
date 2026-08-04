"""
tests/interpretive/test_palm_reading_rules_engine.py
Covers the feature-flagged DETERMINISTIC rule-engine path added to
palm_reading.prepare_palm_reading() -- the flag itself, the OFF-path
no-op guarantee, the wired ON path, and its fail-closed boundary.

Lives in its OWN file rather than in test_palm_reading.py (1970 lines,
already carrying a "monolith split" carry-forward in CLAUDE.md): the
shared fakes are imported from that module rather than re-rolled, so
there is exactly one _FakeSearch/_FakeClient definition in the suite.

NO live LLM call anywhere here: observation_extractor's single call is
answered by the same `client` seam fake test_palm_reading.py already
uses for Stage 1/Stage 2.

CONFOUND, stated up front because it shapes the L_001 test below: every
rule in data/palm_rules/palm_rules_life_line_v1.json currently carries
verified=false, and palm_rules_table.match() skips unverified rules
outright. So "L_001 did not fire" is true for TWO independent reasons on
the live rule set, and asserting only the pipeline outcome would prove
nothing about tokens. test_l001_does_not_fire_without_narrow_token_
verified_confound_removed isolates the token reason by force-verifying a
copy of the real L_001 in the test (dataclasses.replace, test-side only
-- the rule FILE is never touched).
"""

from __future__ import annotations

import dataclasses
import json

import pytest

from agent.interpretive import claim_extraction, palm_reading
from agent.interpretive import palm_rules_table
from agent.interpretive.palm_reading import generate_palm_reading
from agent.prompt_builder import DISCLAIMER
from tests.interpretive.test_palm_reading import (
    _CLEAN_STUB_TEXT,
    _FakeClient,
    _FakeSearch,
    _chunk,
    _single_feature_client,
)


# ─── Fixtures: the captured LEFT life-line prose ────────────────────────
#
# Shape and wording taken from the real dogfood LIFE LINE field
# (diagnostics/dogfood_capture.md's own phrasing, the same
# "no breaks, chains, forks, or islands visible" clause CLAUDE.md's F-B
# entry quotes verbatim). Deliberately NOT absence-phrased overall, so
# _is_absence leaves it alone and retrieval/the gate behave normally.
_CAPTURED_LEFT_LIFE_LINE = (
    "LIFE LINE: Present, deep, and long, curving around the base of the "
    "thumb. No breaks, chains, forks, or islands visible."
)


def _observation_response(observations: dict) -> str:
    """observation_extractor's contracted response shape."""
    return json.dumps({"observations": observations})


def _engine_diag(result) -> dict:
    """The engine block as it reaches PalmReadingResult -- proves the
    diagnostics actually survive the prep -> complete hand-off rather
    than only existing on the prep."""
    return result.stage1_feature_diagnostics["_rules_engine"]


@pytest.fixture
def rules_engine_on(monkeypatch):
    monkeypatch.setattr(palm_reading, "_DETERMINISTIC_RULES_ENABLED", True)


@pytest.fixture
def no_llm_extraction(monkeypatch):
    """Hard proof that the ON path never reaches the LLM extractor: the
    real extract_claims is replaced by a detonator, so any fallback --
    silent or otherwise -- fails the test loudly."""
    def _explode(*args, **kwargs):
        raise AssertionError(
            "claim_extraction.extract_claims must not be called on the "
            "deterministic path"
        )

    monkeypatch.setattr(claim_extraction, "extract_claims", _explode)


# ─── The flag itself ────────────────────────────────────────────────────


def test_flag_defaults_off():
    """Pins the SHIPPED value. A flag that silently ships ON is the whole
    risk this branch was gated to avoid."""
    assert palm_reading._DETERMINISTIC_RULES_ENABLED is False
    assert palm_reading._deterministic_rules_enabled() is False


def test_env_override_turns_flag_on_without_code_edit(monkeypatch):
    monkeypatch.setenv("PALM_RULES_ENGINE", "1")
    assert palm_reading._deterministic_rules_enabled() is True


@pytest.mark.parametrize("value", ["0", "true", "", "yes"])
def test_env_override_only_literal_1_enables(monkeypatch, value):
    """Boundary: any value other than the literal "1" leaves the flag
    alone -- same `== "1"` comparison _DOGFOOD_CAPTURE already uses."""
    monkeypatch.setenv("PALM_RULES_ENGINE", value)
    assert palm_reading._deterministic_rules_enabled() is False


def test_module_constant_honored_when_env_unset(monkeypatch):
    monkeypatch.delenv("PALM_RULES_ENGINE", raising=False)
    monkeypatch.setattr(palm_reading, "_DETERMINISTIC_RULES_ENABLED", True)
    assert palm_reading._deterministic_rules_enabled() is True


# ─── Flag OFF: zero behavioural change ──────────────────────────────────


def test_flag_off_full_pipeline_never_touches_the_rule_engine(monkeypatch):
    """The OFF-path no-op proof. `_prepare_claims_from_rules` is replaced
    by a detonator; a standard full-pipeline run must complete normally,
    which it can only do by never entering the branch.

    (The suite-wide proof is stronger and is the one that actually
    matters: all 195 pre-existing tests in tests/interpretive/ pass
    unchanged with the flag defaulted OFF.)"""
    def _explode(*args, **kwargs):
        raise AssertionError("rule engine must not run with the flag OFF")

    monkeypatch.setattr(palm_reading, "_prepare_claims_from_rules", _explode)

    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))
    client = _single_feature_client("life line", chunk, _CLEAN_STUB_TEXT)

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long, unbroken life line.", palm_right=None, client=client
    )

    assert result.validation.passed is True
    assert "_rules_engine" not in result.stage1_feature_diagnostics
    assert result.claims  # LLM Stage 1 produced the claims, as before


# ─── Flag ON: the captured life-line prose (the honest-stricter case) ───


def test_l001_does_not_fire_on_captured_life_line_prose(rules_engine_on, no_llm_extraction, monkeypatch):
    """INTENDED CONTRAST, wired end to end: the live LLM path reads this
    same field as "long, narrow, deep" and lets L_001's ideal-life-line
    claim through. The engine only ever sees tokens the prose actually
    states -- "narrow" is nowhere in it -- so L_001's third antecedent is
    unsatisfied and the rule stays silent. The engine is honestly
    STRICTER than the live path here, and the user gets a decline rather
    than an unearned promise of vitality."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))

    # The extractor emits only what the prose states: long + deep.
    client = _FakeClient(responses=[(
        _observation_response({
            "Line of Life": {
                "Length": {"value": "long"},
                "Depth": {"value": "deep"},
            }
        }),
        None,
    )])

    result = generate_palm_reading(
        palm_left=_CAPTURED_LEFT_LIFE_LINE, palm_right=None, client=client
    )

    diag = _engine_diag(result)
    assert diag["failed"] is False
    observed = diag["observation"]["Line of Life"]
    assert observed == {"Length": "long", "Depth": "deep"}
    assert "Width" not in observed  # the missing token, stated explicitly
    assert "L_001" not in diag["fired_rule_ids"]
    assert diag["fired_rule_ids"] == []

    # Honest decline, not silence, and no claim invented to fill the gap.
    assert result.claims == ()
    assert "life line" in result.reading_text
    assert result.reading_text.endswith(DISCLAIMER)

    # Exactly one LLM call on this whole run: the observation extractor.
    # Stage 2 is never called because the inventory is empty.
    assert len(client.completions.calls) == 1


def test_l001_does_not_fire_without_narrow_token_verified_confound_removed():
    """De-confounded companion to the test above, at engine level.

    L_001 currently carries verified=false, so match() would skip it even
    if every antecedent were satisfied. This test force-verifies a COPY
    of the real L_001 (the rule file is untouched) and re-runs match, so
    the only remaining reason it cannot fire is the absent "narrow"
    Width token. Control arm included: adding Width=narrow to the same
    observation DOES fire the force-verified rule, which is what proves
    the negative arm is about the token and nothing else."""
    l001 = next(
        r for r in palm_rules_table.load_rule_set() if r.rule_id == "L_001"
    )
    assert l001.verified is False  # the confound, pinned
    verified_l001 = dataclasses.replace(l001, verified=True)

    required = {(a.attribute, a.value) for a in verified_l001.antecedents}
    assert ("Width", "narrow") in required

    observed = {"Line of Life": {"Length": "long", "Depth": "deep"}}
    magnitudes: dict = {}
    assert palm_rules_table.match(observed, magnitudes, [verified_l001]) == []

    with_narrow = {"Line of Life": {"Length": "long", "Depth": "deep", "Width": "narrow"}}
    fired = palm_rules_table.match(with_narrow, magnitudes, [verified_l001])
    assert [r.rule_id for r in fired] == ["L_001"]


# ─── Flag ON: hardest case -- prose yields zero valid tokens ────────────


def test_zero_valid_tokens_declines_honestly_without_raising(
    rules_engine_on, no_llm_extraction, monkeypatch
):
    """HARDEST CASE: the extractor emits something, but nothing in it
    survives the closed-vocabulary gate ("shimmery" is absent from the
    full 214-value registry pool -- observation_extractor's own test
    fixture uses the same token for the same reason).

    Required outcome: an honest no-claim result. No exception, no
    fabricated claim, no fallback to the LLM extraction path, and no
    Stage-2 call to compose prose out of nothing."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))

    client = _FakeClient(responses=[(
        _observation_response({
            "Line of Life": {"Depth": {"value": "shimmery"}}
        }),
        None,
    )])

    result = generate_palm_reading(
        palm_left=_CAPTURED_LEFT_LIFE_LINE, palm_right=None, client=client
    )

    diag = _engine_diag(result)
    assert diag["failed"] is False
    assert diag["observation"] == {}
    # MEASURED, worth knowing: the token is dropped by the EXTRACTOR's own
    # closed-vocabulary filter, one layer above to_tokens, so the payload
    # handed to to_tokens is already {} and magnitudes["_dropped"] comes
    # back empty. Two independent gates reject it and the "dropped_tokens"
    # diagnostic only ever records the second one -- so an empty
    # dropped_tokens is NOT evidence that nothing was rejected on this run.
    assert diag["dropped_tokens"] == []
    assert diag["fired_rule_ids"] == []
    assert diag["surviving_rule_ids"] == []

    assert result.claims == ()
    assert result.reading_text_tagged == ""
    assert "life line" in result.reading_text
    assert result.reading_text.endswith(DISCLAIMER)
    # One call total (the extractor). Stage 2 never fires on an empty
    # inventory -- the no_llm_extraction fixture covers the other half.
    assert len(client.completions.calls) == 1


def test_no_mappable_features_makes_zero_llm_calls_at_all(
    rules_engine_on, no_llm_extraction, monkeypatch
):
    """Boundary below the case above: "fingers" has no ontology
    counterpart at all, so the extractor short-circuits to {} without
    calling the LLM even once. Still a non-raising honest decline."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))
    client = _FakeClient(exception=AssertionError("no LLM call expected"))

    result = generate_palm_reading(
        palm_left="FINGERS: Long and smooth, with slightly knotty joints.",
        palm_right=None,
        client=client,
    )

    assert client.completions.calls == []
    assert result.claims == ()
    assert _engine_diag(result)["failed"] is False
    assert result.reading_text.endswith(DISCLAIMER)


# ─── Flag ON: a rule that actually fires ────────────────────────────────


def _head_line_chunk() -> dict:
    """A retrieved chunk whose text actually supports the head line.

    NOT incidental: the retrieval support gate still runs on the
    deterministic path and still drives `unsupported_features`, which
    drives `_check_banned_feature_mentions`. A run whose rules fire for a
    feature the GATE calls unsupported produces a valid reading that then
    fails the banned-mention display check. See this file's report note
    -- reproduced deliberately in
    test_gate_unsupported_feature_with_fired_rules_fails_display_check."""
    return _chunk(
        text="The line of head, when short, indicates a material nature.",
        page_ref=147,
    )


def _short_head_line_client(voice_text: str) -> _FakeClient:
    """Head line Length=short fires H_005 and H_006 (both single-
    antecedent, same topic_group, equal set size -> benign siblings, both
    survive) -> claims C1 and C2."""
    return _FakeClient(responses=[
        (_observation_response({"Line of Head": {"Length": {"value": "short"}}}), None),
        (voice_text, None),
    ])


def test_fired_rules_become_claims_and_reach_stage_two(
    rules_engine_on, no_llm_extraction, monkeypatch
):
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_head_line_chunk()]))
    voice_text = (
        "This is a hand that meets the practical world squarely, with a "
        "steady, grounded confidence that shows in everything it "
        "undertakes.[FLOW] "
        "A thoroughly material nature, lacking imaginative faculties.[C1] "
        "It foreshadows a nature little given to mental strain.[C2]"
    )
    client = _short_head_line_client(voice_text)

    result = generate_palm_reading(
        palm_left="HEAD LINE: Short and clearly marked.", palm_right=None, client=client
    )

    diag = _engine_diag(result)
    assert diag["fired_rule_ids"] == ["H_005", "H_006"]
    assert diag["surviving_rule_ids"] == ["H_005", "H_006"]
    assert [c.claim_id for c in result.claims] == ["C1", "C2"]
    assert all(c.chunk_id.startswith("cheiroslanguageo00chei_1_p147") for c in result.claims)
    assert result.validation.passed is True
    assert len(client.completions.calls) == 2  # extractor + one voice call


def test_source_quote_stays_out_of_the_voicer_prompt(
    rules_engine_on, no_llm_extraction, monkeypatch
):
    """No new source_quote leakage: the 19th-century book prose that
    justifies each rule must reach diagnostics["citations"] and NOTHING
    that goes into the Stage-2 prompt. Checked against the real quote
    text of the rules that actually fired, not a proxy."""
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_head_line_chunk()]))
    client = _short_head_line_client(
        "A thoroughly material nature, lacking imaginative faculties.[C1] "
        "It foreshadows a nature little given to mental strain.[C2]"
    )

    result = generate_palm_reading(
        palm_left="HEAD LINE: Short and clearly marked.", palm_right=None, client=client
    )

    citations = _engine_diag(result)["citations"]
    assert {c["rule_id"] for c in citations.values()} == {"H_005", "H_006"}
    quotes = [c["source_quote"] for c in citations.values()]
    assert all(q.strip() for q in quotes)

    voice_call = client.completions.calls[1]
    voice_prompt = json.dumps(voice_call["messages"])
    for quote in quotes:
        assert quote not in voice_prompt
    # And the Claim objects themselves carry no quote-bearing field --
    # the shape claim_voicing sees is unchanged from the LLM path.
    assert not hasattr(result.claims[0], "source_quote")
    assert {f.name for f in dataclasses.fields(result.claims[0])} == {
        "claim_id", "feature", "chunk_id", "claim_text", "valence",
        "condition_text", "observation_basis", "excluded_from_voice",
        "exclusion_reason",
    }


def test_gate_unsupported_feature_with_fired_rules_fails_display_check(
    rules_engine_on, no_llm_extraction, monkeypatch
):
    """CHARACTERIZATION of a real structural tension found while wiring
    this, NOT an endorsement of the behavior.

    The retrieval support gate and the rule engine are independent
    graders. Here retrieval returns only life-line text, so the gate
    calls "head line" UNSUPPORTED -- while the rule engine, which grounds
    on the rule table rather than on this run's retrieval, fires H_005/
    H_006 for it anyway. Stage 2 duly voices them, and
    `_check_banned_feature_mentions` then fails the reading for
    discussing a feature the gate banned.

    Exact trigger, measured: that check is a literal feature-noun match on
    the voiced PROSE, so the failure fires precisely when the reading
    names the feature -- which a rule claim about the head line naturally
    does. Voiced text that never says "head" slips through with
    passed=True despite resting on the same gate-unsupported feature, so
    the current behavior is inconsistent in BOTH directions, not merely
    strict.

    Recorded as a test so the behavior cannot change silently. The design
    question -- whether the support gate should still govern the decline
    set and the banned-mention check on a path whose grounding is the
    rule table -- is not decided here."""
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_chunk()]))  # life-line text
    client = _short_head_line_client(
        "Your head line speaks of a thoroughly material nature, lacking "
        "imaginative faculties.[C1] "
        "It foreshadows a nature little given to mental strain.[C2]"
    )

    result = generate_palm_reading(
        palm_left="HEAD LINE: Short and clearly marked.", palm_right=None, client=client
    )

    assert "head line" in result.unsupported_features
    assert _engine_diag(result)["fired_rule_ids"] == ["H_005", "H_006"]
    assert result.validation.passed is False
    assert any("unsupported feature mentioned: head line" in f for f in result.validation.failures)


def test_claim_features_outside_registry_is_recorded(
    rules_engine_on, no_llm_extraction, monkeypatch
):
    """REGRESSION GUARD (was: FLAGGED CONSEQUENCE pinning a since-fixed
    bug -- rule-derived Claim.feature used to be the rule's raw
    topic_group, "line_head", not a _FEATURE_REGISTRY label, "head
    line"). rule_to_claim.claims_from_rules now maps topic_group ->
    registry feature before it ever reaches Claim.feature (see
    rule_to_claim._TOPIC_GROUP_TO_FEATURE), so claim_features_outside_
    registry stays empty and downstream consumers keyed on the registry
    token (_compute_decline_features, _build_sources_from_claims) see a
    real match instead of silently mismatching."""
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_head_line_chunk()]))
    client = _short_head_line_client(
        "A thoroughly material nature, lacking imaginative faculties.[C1] "
        "It foreshadows a nature little given to mental strain.[C2]"
    )

    result = generate_palm_reading(
        palm_left="HEAD LINE: Short and clearly marked.", palm_right=None, client=client
    )

    assert _engine_diag(result)["claim_features_outside_registry"] == []
    assert {c.feature for c in result.claims} == {"head line"}
    # ... and the decline block no longer wrongly names head line, since
    # it now has real fired-rule claims matched to it by registry key.
    assert "head line" not in result.reading_text


def test_suppression_log_is_captured_not_dropped(
    rules_engine_on, no_llm_extraction, monkeypatch
):
    """HL_004 (Starting_Point=rising_from_Mount_of_Saturn) is a proper
    antecedent-subset of HL_005 (that + Position=high), so an observation
    satisfying both suppresses HL_004. The suppression must be visible on
    the result, not silently swallowed."""
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_chunk()]))
    client = _FakeClient(responses=[
        (_observation_response({
            "Line of Heart": {
                "Starting_Point": {"value": "rising_from_Mount_of_Saturn"},
                "Position": {"value": "high"},
            }
        }), None),
        ("The heart line begins high beneath Saturn.[C1]", None),
    ])

    result = generate_palm_reading(
        palm_left="HEART LINE: Rising high from beneath the mount of Saturn.",
        palm_right=None,
        client=client,
    )

    diag = _engine_diag(result)
    suppression_log = diag["suppression_log"]
    assert ("HL_005", "HL_004") in [tuple(pair) for pair in suppression_log]
    assert "HL_004" in diag["fired_rule_ids"]
    assert "HL_004" not in diag["surviving_rule_ids"]
    assert "HL_005" in diag["surviving_rule_ids"]


# ─── Flag ON: fail-closed ───────────────────────────────────────────────


@pytest.mark.parametrize(
    "target, exception",
    [
        ("load_rule_set", ValueError("rules dir missing")),
        ("match", RuntimeError("engine exploded")),
        ("resolve_priority", KeyError("topic_group")),
    ],
)
def test_engine_failure_fails_closed_never_falls_back_to_llm_path(
    rules_engine_on, no_llm_extraction, monkeypatch, target, exception
):
    """Any failure anywhere in the chain -> honest empty result. The
    no_llm_extraction fixture is what makes "never falls back silently"
    an assertion rather than a claim: a fallback would raise
    AssertionError here instead of returning."""
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_chunk()]))

    def _raise(*args, **kwargs):
        raise exception

    monkeypatch.setattr(palm_rules_table, target, _raise)
    client = _FakeClient(responses=[(
        _observation_response({"Line of Head": {"Length": {"value": "short"}}}), None,
    )])

    result = generate_palm_reading(
        palm_left="HEAD LINE: Short and clearly marked.", palm_right=None, client=client
    )

    diag = _engine_diag(result)
    assert diag["failed"] is True
    assert type(exception).__name__ in diag["error"]
    assert diag["suppression_log"] == []  # key present even on failure
    assert result.claims == ()
    assert result.reading_text.endswith(DISCLAIMER)
    assert "head line" in result.reading_text  # declined, not silently dropped


def test_engine_failure_final_outcome_trips_the_s83_capture_net(
    rules_engine_on, no_llm_extraction, monkeypatch
):
    """frontend/app.py's _run_had_failure tags a run "all_rejected" when
    any stage1 diagnostics entry's final_outcome contains "failed". The
    engine block rides that same channel deliberately, so a broken engine
    earns a dogfood capture with no frontend edit."""
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_chunk()]))

    def _raise(*args, **kwargs):
        raise RuntimeError("engine exploded")

    monkeypatch.setattr(palm_rules_table, "match", _raise)
    client = _FakeClient(responses=[(
        _observation_response({"Line of Head": {"Length": {"value": "short"}}}), None,
    )])

    result = generate_palm_reading(
        palm_left="HEAD LINE: Short and clearly marked.", palm_right=None, client=client
    )

    assert "failed" in _engine_diag(result)["final_outcome"]


def test_extractor_failure_also_fails_closed(rules_engine_on, no_llm_extraction, monkeypatch):
    """The LLM half of the chain gets the same treatment: an API error
    inside observation_extractor is a RuntimeError, caught at the same
    boundary -- it must not surface as an exception to the caller and
    must not be retried through the LLM extraction path."""
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_chunk()]))
    client = _FakeClient(exception=RuntimeError("simulated API failure"))

    result = generate_palm_reading(
        palm_left="HEAD LINE: Short and clearly marked.", palm_right=None, client=client
    )

    assert _engine_diag(result)["failed"] is True
    assert result.claims == ()
    assert result.reading_text.endswith(DISCLAIMER)


# ─── Flag ON: retrieval-side records survive the substitution ──────────


def test_s83_candidate_records_survive_on_the_deterministic_path(
    rules_engine_on, no_llm_extraction, monkeypatch
):
    """Retrieval still runs on this path, so the S83 near-miss margin log
    must still be recorded -- dropping it would be a silent loss of the
    capture net's evidence."""
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_chunk()]))
    client = _FakeClient(responses=[(_observation_response({}), None)])

    result = generate_palm_reading(
        palm_left=_CAPTURED_LEFT_LIFE_LINE, palm_right=None, client=client
    )

    assert "candidates" in result.stage1_feature_diagnostics["life line"]
