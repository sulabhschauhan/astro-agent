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

CONFOUND, stated up front because it shapes the test below it names:
whenever a rule is genuinely unverified, palm_rules_table.match() skips it
outright, so "the rule did not fire" would be true for TWO independent
reasons (unverified AND missing token) and asserting only the pipeline
outcome would prove nothing about tokens specifically.
test_l001_does_not_fire_without_narrow_token_verified_confound_removed
isolates the token reason with a SYNTHETIC unverified rule built entirely
in-test (not tied to any production rule_id or file) -- so this test's
validity never depends on which production rules happen to be verified on
any given day. (Earlier version of this test pinned the real L_001's
verified flag directly; that anchor went stale the day L_001 was marked
verified=true -- data/palm_rules/palm_rules_life_line_v1.json, 2026-08-04 --
while the test's actual intent, proving match() enforces the token
independent of the verified flag, was never invalidated. Rebuilt on a
synthetic fixture so a future verified-flag edit can never re-break it.)
"""

from __future__ import annotations

import dataclasses
import json

import pytest

from agent.interpretive import claim_extraction, palm_reading
from agent.interpretive import observation_extractor, palm_rules_table
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


def _observation_response(observations: dict, unmapped: dict | None = None) -> str:
    """observation_extractor's contracted response shape. `unmapped` is
    the SECOND half of that contract (qualities the model saw but could
    not tokenize) -- omitted entirely when None, which the extractor
    tolerates by design (its docstring point 7)."""
    body: dict = {"observations": observations}
    if unmapped is not None:
        body["unmapped"] = unmapped
    return json.dumps(body)


def _engine_diag(result) -> dict:
    """The engine block as it reaches PalmReadingResult -- proves the
    diagnostics actually survive the prep -> complete hand-off rather
    than only existing on the prep."""
    return result.stage1_feature_diagnostics["_rules_engine"]


def _record_diag(result) -> dict:
    """The full ObservationRecord projection, as it reaches
    PalmReadingResult (same channel as suppression_log)."""
    return _engine_diag(result)["observation_record"]


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


def _make_synthetic_unverified_rule() -> palm_rules_table.PalmRule:
    """Test-only fixture, never persisted to any rule file and never
    loaded via load_rule_set() -- rule_id is deliberately NOT a real
    production id, so this test's validity can never depend on which
    production rules happen to be verified on any given day (see the
    module docstring's CONFOUND note). Same 3-antecedent shape as the
    real L_001 (Length=long, Width=narrow, Depth=deep) purely because
    that shape is what this test needs to exercise -- not because it is
    meant to represent L_001 specifically."""
    antecedents = (
        palm_rules_table.Antecedent(
            feature="Line of Life", attribute="Length", value="long",
            condition_type="standard", comparator=None, comparator_feature=None,
        ),
        palm_rules_table.Antecedent(
            feature="Line of Life", attribute="Width", value="narrow",
            condition_type="standard", comparator=None, comparator_feature=None,
        ),
        palm_rules_table.Antecedent(
            feature="Line of Life", attribute="Depth", value="deep",
            condition_type="standard", comparator=None, comparator_feature=None,
        ),
    )
    return palm_rules_table.PalmRule(
        rule_id="L_SYNTH_UNVERIFIED_TEST",
        source_page=0,
        topic_group="test_synthetic",
        is_compound=True,
        antecedents=antecedents,
        claim="synthetic test fixture -- never voiced, never loaded from a rule file",
        source_quote="synthetic test fixture -- not real classical text",
        verified=False,
        verifier=None,
        verified_date=None,
        source_fidelity=None,
        schema_flags=(),
        baseline=False,
    )


def test_l001_does_not_fire_without_narrow_token_verified_confound_removed():
    """De-confounded companion to the test above, at engine level.

    Uses a SYNTHETIC unverified rule (see module docstring CONFOUND note
    and _make_synthetic_unverified_rule) rather than the real L_001, so
    this test can never go stale again when a production rule's verified
    flag changes. This test force-verifies a COPY of the synthetic rule
    (dataclasses.replace, the synthetic fixture itself is untouched) and
    runs match, so the only remaining reason it cannot fire is the absent
    "narrow" Width token. Control arm included: adding Width=narrow to the
    same observation DOES fire the force-verified rule, which is what
    proves the negative arm is about the token and nothing else."""
    synthetic_rule = _make_synthetic_unverified_rule()
    assert synthetic_rule.verified is False  # the confound, by construction
    verified_rule = dataclasses.replace(synthetic_rule, verified=True)

    required = {(a.attribute, a.value) for a in verified_rule.antecedents}
    assert ("Width", "narrow") in required

    observed = {"Line of Life": {"Length": "long", "Depth": "deep"}}
    magnitudes: dict = {}
    assert palm_rules_table.match(observed, magnitudes, [verified_rule]) == []

    with_narrow = {"Line of Life": {"Length": "long", "Depth": "deep", "Width": "narrow"}}
    fired = palm_rules_table.match(with_narrow, magnitudes, [verified_rule])
    assert [r.rule_id for r in fired] == ["L_SYNTH_UNVERIFIED_TEST"]


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
    # ... and the rejected token is now TRACEABLE rather than gone: the
    # extractor folds its own out-of-vocabulary rejects into unmapped
    # (its docstring point 2), and that survives to the result.
    assert _record_diag(result)["features"]["Line of Life"]["unmapped"] == [
        {"quality": "shimmery", "attribute_guess": "Depth"}
    ]

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

    # Not a silent nothing: the prose IS captured, under the category that
    # says WHY it never became a token -- no ontology counterpart at all,
    # so it was never sent to the LLM (distinct from dropped_disabled).
    record = _record_diag(result)
    assert record["features"] == {}
    assert record["dropped_disabled"] == []
    assert [u["prose_feature"] for u in record["unmappable_prose_features"]] == ["fingers"]
    assert "knotty" in record["unmappable_prose_features"][0]["raw_prose"]


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


# ─── enabled_features: rule-derivation still exists standalone ──────────


def test_enabled_features_derived_from_the_loaded_rule_set():
    """Pins the DERIVATION, not a literal list: `_enabled_features_from_
    rules`/`rule_engine_enabled_features()` still compute the antecedent-
    feature set of whatever rules are loaded -- unchanged by the
    ALL-FEATURES UNBLOCK below, which stopped FEEDING this set into the
    extraction seam but did not remove the function itself (still useful
    standalone: "what can the rule engine actually consume"). The literal
    set is asserted too, as a canary -- if a new chapter changes it, this
    assertion is the intended place to notice."""
    rules = palm_rules_table.load_rule_set()
    expected = {a.feature for r in rules for a in r.antecedents}
    expected |= {a.comparator_feature for r in rules for a in r.antecedents if a.comparator_feature}

    derived = palm_reading._enabled_features_from_rules(rules)
    assert derived == expected
    assert palm_reading.rule_engine_enabled_features() == derived

    assert derived == frozenset({
        "Hand", "Line of Fate", "Line of Head", "Line of Heart",
        "Line of Life", "Mount of Venus", "Quadrangle",
        # S117 mounts chapter addition (palm_rules_mounts_v1.json).
        "Mount of Jupiter", "Mount of Saturn", "Mount of the Sun",
        "Upper Mount of Mars",
    })
    # Real ontology features with no rule behind them are STILL excluded
    # from this rule-derived set -- that hasn't changed. What changed is
    # that the extraction seam no longer uses this set as its allow-list
    # (see the tests below). "Line of Fate" moved OUT of this unruled list
    # (S97 Fate-line chapter gave it real antecedent/comparator_feature
    # behavior, confirmed above); "Mount of Jupiter" moved OUT of this
    # unruled list too (S117 mounts chapter, M_014, gave it real antecedent
    # behavior, same pattern as "Line of Fate"'s S97 move); "Palm"/"Square"
    # are absent from `derived` too, but for a different reason -- their
    # rules (L_003/L_020/L_021) were retired (S96), not merely "never
    # ruled" like this list's members.
    for unruled in ("Line of Sun", "Thumb"):
        assert unruled not in derived


# ─── ALL-FEATURES UNBLOCK: the extraction seam's real allow-list ────────


def test_enabled_features_at_the_seam_is_all_aliased_features(
    rules_engine_on, no_llm_extraction, monkeypatch
):
    """Pins the UNBLOCK itself: the allow-list actually passed to
    extract_observation/to_vision_payload is observation_extractor.
    all_aliased_features() (every ontology feature the LLM call can ever
    produce), NOT the narrower rule-derived set pinned above -- those two
    sets are byte-different (the rule-derived set includes non-LLM-
    producible tokens like "Hand"/"Palm" and excludes 4 real LLM
    features). Spied directly on the extract_observation call so this
    proves what was PASSED, not just a downstream consequence."""
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_chunk()]))
    real_extract = observation_extractor.extract_observation
    captured: dict = {}

    def _spy(*args, **kwargs):
        captured["enabled_features"] = kwargs.get("enabled_features")
        return real_extract(*args, **kwargs)

    monkeypatch.setattr(observation_extractor, "extract_observation", _spy)
    client = _FakeClient(responses=[(_observation_response({}), None)])

    result = generate_palm_reading(
        palm_left=_CAPTURED_LEFT_LIFE_LINE, palm_right=None, client=client
    )

    assert captured["enabled_features"] == observation_extractor.all_aliased_features()
    # And the record's own "enabled_features" diagnostic (built from the
    # SAME variable, also fed to to_vision_payload) agrees.
    record = _record_diag(result)
    assert set(record["enabled_features"]) == observation_extractor.all_aliased_features()
    assert record["dropped_disabled"] == []


def test_thumb_now_reaches_observation_and_record_but_fires_no_rules(
    rules_engine_on, no_llm_extraction, monkeypatch
):
    """"Thumb" has no rule anywhere in the loaded set (pinned as one of the
    4 unruled features above). Before the ALL-FEATURES UNBLOCK it would
    have been silently withheld at to_vision_payload (dropped_disabled);
    now it reaches `observation` in full, same as any ruled feature, and
    produces zero claims only because no rule exists for it -- an honest
    decline visible end to end, not a silent drop before the engine ever
    saw it."""
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_chunk()]))
    client = _FakeClient(responses=[(
        _observation_response({
            "Thumb": {"Suppleness": {"value": "stiff"}},
        }),
        None,
    )])

    result = generate_palm_reading(
        palm_left="THUMB: Notably stiff and set low on the hand.",
        palm_right=None,
        client=client,
    )

    diag = _engine_diag(result)
    assert diag["failed"] is False
    assert diag["observation"].get("Thumb") == {"Suppleness": "stiff"}
    assert diag["fired_rule_ids"] == []

    record = _record_diag(result)
    assert "Thumb" in record["enabled_features"]
    assert record["dropped_disabled"] == []
    assert record["features"]["Thumb"]["tokens"] == {
        "Suppleness": {"value": "stiff", "confidence": 1.0}
    }
    assert result.claims == ()


def test_unmappable_prose_features_unaffected_by_the_unblock(
    rules_engine_on, no_llm_extraction, monkeypatch
):
    """The ALL-FEATURES UNBLOCK widens `enabled_features`, but "fingers"
    and "markings/other features" still have NO ontology counterpart at
    all (_FEATURE_ALIAS -> None) -- no allow-list, however wide, can
    unblock a feature the extractor never sends to the LLM in the first
    place. Still routed to `unmappable_prose_features`, not `observation`,
    same as before this task."""
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_chunk()]))
    client = _FakeClient(exception=AssertionError("no LLM call expected"))

    result = generate_palm_reading(
        palm_left="FINGERS: Long and smooth, with slightly knotty joints.",
        palm_right=None,
        client=client,
    )

    record = _record_diag(result)
    assert record["dropped_disabled"] == []
    assert [u["prose_feature"] for u in record["unmappable_prose_features"]] == ["fingers"]


# ─── HARDEST CASE: real prose with no ontology token for what it says ──


def test_life_line_thumb_clause_is_visible_in_unmapped_end_to_end(
    rules_engine_on, no_llm_extraction, monkeypatch
):
    """HARDEST CASE, and the whole reason for the record contract.

    "curves around the base of the thumb" is a genuine, correctly-observed
    life-line quality with NO ontology token to hold it (CLAUDE.md's F-A
    entry uses this exact clause as its landmark-exclusion example). Under
    the old dict contract it vanished: the payload only ever carried
    tokens, so the caller could not tell this apart from "the LLM saw
    nothing about the life line".

    Required: the clause reaches the RESULT's diagnostics, under the life
    line's own `unmapped[]`, on the same run where it produces no life
    line claim. Both facts asserted together -- the silence has to be
    explained, not merely present."""
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_chunk()]))
    client = _FakeClient(responses=[(
        _observation_response(
            {"Line of Life": {"Length": {"value": "long"}, "Depth": {"value": "deep"}}},
            unmapped={"Line of Life": [
                {"quality": "curves around the base of the thumb",
                 "attribute_guess": "Curve"},
            ]},
        ),
        None,
    )])

    result = generate_palm_reading(
        palm_left=_CAPTURED_LEFT_LIFE_LINE, palm_right=None, client=client
    )

    life_line = _record_diag(result)["features"]["Line of Life"]
    assert life_line["unmapped"] == [
        {"quality": "curves around the base of the thumb", "attribute_guess": "Curve"}
    ]
    # Same run, the other half of the story: what DID tokenize, and the
    # raw prose the LLM was actually given.
    assert life_line["tokens"] == {
        "Length": {"value": "long", "confidence": 1.0},
        "Depth": {"value": "deep", "confidence": 1.0},
    }
    # raw_prose is the field VALUE, label already stripped by _parse_fields
    # -- pinned literally so a future parser change is visible here.
    assert life_line["raw_prose"] == _CAPTURED_LEFT_LIFE_LINE.split(": ", 1)[1]
    assert "curving around the base of the thumb" in life_line["raw_prose"]

    # No life-line claim, and now that is a TRACEABLE outcome rather than
    # an undiagnosable silence.
    assert _engine_diag(result)["fired_rule_ids"] == []
    assert result.claims == ()


# ─── Fail-closed is now SCOPED: contract breaks must not be masked ─────


def test_contract_break_at_the_adapter_seam_propagates_and_is_not_masked(
    rules_engine_on, no_llm_extraction, monkeypatch
):
    """REGRESSION GUARD for the bug this rewire fixes.

    The old blanket `except Exception` turned the extractor's return-type
    change into "engine produced zero claims" -- an honest-looking decline
    on every single ON-path run, with nothing but a log line to show for
    it. The record -> payload -> tokens seam is now OUTSIDE the fail-closed
    boundary: a TypeError there is a code defect, and it must reach the
    caller (and the test suite) as one."""
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_chunk()]))

    def _wrong_contract(*args, **kwargs):
        raise TypeError("to_vision_payload: contract mismatch")

    monkeypatch.setattr(observation_extractor, "to_vision_payload", _wrong_contract)
    client = _FakeClient(responses=[(
        _observation_response({"Line of Head": {"Length": {"value": "short"}}}), None,
    )])

    with pytest.raises(TypeError, match="contract mismatch"):
        generate_palm_reading(
            palm_left="HEAD LINE: Short and clearly marked.", palm_right=None, client=client
        )


def test_failed_stage_is_recorded_so_a_broad_catch_cannot_hide_where_it_broke(
    rules_engine_on, no_llm_extraction, monkeypatch
):
    """The two remaining broad catches stay broad (a rule-file or engine
    failure IS an operational decline), but they can no longer be
    anonymous: `failed_stage` says which boundary caught it."""
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

    diag = _engine_diag(result)
    assert diag["failed_stage"] == "rule_matching"
    # Extraction succeeded before the engine broke, so the record it
    # produced is still reported rather than blanked out.
    assert diag["observation_record"]["features"]["Line of Head"]["tokens"] == {
        "Length": {"value": "short", "confidence": 1.0}
    }


def test_extractor_api_failure_records_its_stage_and_an_empty_record(
    rules_engine_on, no_llm_extraction, monkeypatch
):
    """The narrow boundary: a RuntimeError out of the LLM call is an
    operational failure and still declines honestly -- but it is labelled,
    and the allow-list it got as far as deriving is still reported."""
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_chunk()]))
    client = _FakeClient(exception=RuntimeError("simulated API failure"))

    result = generate_palm_reading(
        palm_left="HEAD LINE: Short and clearly marked.", palm_right=None, client=client
    )

    diag = _engine_diag(result)
    assert diag["failed"] is True
    assert diag["failed_stage"] == "observation_extraction"
    assert diag["observation_record"]["features"] == {}
    assert "Line of Head" in diag["observation_record"]["enabled_features"]


def test_engine_diagnostics_stay_json_serializable(
    rules_engine_on, no_llm_extraction, monkeypatch
):
    """The record projection rides the dogfood-capture channel, which
    writes JSON. A dataclass leaking into the diagnostics would break the
    capture at write time, not here -- so it is asserted here."""
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_head_line_chunk()]))
    client = _short_head_line_client(
        "A thoroughly material nature, lacking imaginative faculties.[C1] "
        "It foreshadows a nature little given to mental strain.[C2]"
    )

    result = generate_palm_reading(
        palm_left="HEAD LINE: Short and clearly marked.", palm_right=None, client=client
    )

    json.dumps(_engine_diag(result))  # raises TypeError if anything leaks


# ─── 5c step 1: proximity-degree (P) wiring, inert-and-isolated ─────────


def test_proximity_degree_reaches_flat_observation_through_p_wiring(
    rules_engine_on, no_llm_extraction, monkeypatch
):
    """Proves the 5c step-1 P-wiring is live end to end (inline PROXIMITY
    subfield -> extract_relations()'s proximity path -> _flatten_proximity_degrees
    -> merged into the flat `observation` dict) using an EMPTY LLM
    observation response as the isolation lever: with nothing coming from
    the LLM, any "Proximity" token reaching `observation` can only have
    arrived via the deterministic P-merge, never via to_tokens."""
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_head_line_chunk()]))
    client = _FakeClient(responses=[(_observation_response({}), None)])

    result = generate_palm_reading(
        palm_left=(
            "HEAD LINE: present, deep.\n"
            "ORIGIN: Mount of Jupiter\n"
            "PROXIMITY: touching to Line of Life"
        ),
        palm_right=None,
        client=client,
    )

    diag = _engine_diag(result)
    assert diag["proximity_observations"]["Line of Head"]["Proximity"] == "touching"
    assert diag["observation"]["Line of Head"]["Proximity"] == "touching"  # P is sole source
    assert diag["targets"]["Line of Head"]["Proximity"] == "Line of Life"  # landmark half unaffected

    # Inert by design: H_027 (the only loaded rule with a Proximity
    # antecedent) still keys on its pre-migration compound value
    # "touching_Line_of_Life", not the plain degree token this step wires
    # in -- so the signal is live but nothing reads it yet (step 3's job).
    assert "H_027" not in diag["fired_rule_ids"]


def test_proximity_degree_wins_over_llm_emitted_proximity(
    rules_engine_on, no_llm_extraction, monkeypatch
):
    """Proves P-wins precedence: the LLM's own pool-valid 'medium' survives
    to_tokens into `observation` first, then the deterministic PROXIMITY
    parse overwrites it with 'touching'. A pool-valid (not dropped) LLM
    value is the isolation lever here -- if to_tokens had discarded it
    instead, the overwrite would prove nothing about precedence."""
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_head_line_chunk()]))
    client = _FakeClient(responses=[(
        _observation_response({"Line of Head": {"Proximity": {"value": "medium"}}}),
        None,
    )])

    result = generate_palm_reading(
        palm_left=(
            "HEAD LINE: present, deep.\n"
            "PROXIMITY: touching to Line of Life"
        ),
        palm_right=None,
        client=client,
    )

    diag = _engine_diag(result)
    assert diag["observation"]["Line of Head"]["Proximity"] == "touching"  # P overwrote the LLM's 'medium'


# ─── Pattern D: n-way convergence rule firing (L_026, S98/S99/S107) ─────
# Definition-of-done for the Generalization/Pattern D arc: the 3-way
# life+head+heart join rule (data/palm_rules/palm_rules_life_line_v1.json,
# L_026) must actually FIRE from a real vision string, through the real
# chain (extract_relations -> palm_reading._assemble_relational_targets ->
# merge_relational_targets -> load_rule_set -> match()) -- no LLM stub
# needed, since the joins_at_origin signal is 100% deterministic (the
# targets channel), same as FT_016's own mechanism. S99 Step 5c migrated
# the rule's own wording from untyped Convergence to the typed
# joins_at_origin token (see the rule's own schema_flags). S107 cut the
# rule over again -- from the typed RELATIONSHIP field (retired) to the
# free-verb CONTACTS field, mapped through contact_mapper.map_contact
# (S106-inflection-aware) via palm_reading._assemble_relational_targets --
# the tests below were updated to emit CONTACTS wording and route through
# that bridge accordingly.


def test_l_026_three_way_convergence_fires_end_to_end_from_vision_string():
    """Positive: a HEAD LINE block emitting two CONTACTS lines (joins Heart
    at start, joins Life at start) and a HEART LINE block emitting one
    (joins Life at start) -- the S107 cutover of this rule's signal source
    from typed RELATIONSHIP to free-verb CONTACTS, mirroring the exact
    real-image methodology Steps 5b/5c already used for the typed wording
    (H_028's own "Line of Head" block reporting its own joins_at_origin,
    S99 Step 5a). Unlike the old CONVERGENCE mechanism, neither the typed
    RELATIONSHIP parser nor its CONTACTS successor canonicalize by
    alphabetical owner -- a relation is filed under whichever feature's
    block reports it, so the synthetic text below reports each pairwise
    join from the same side the rule's own antecedents key on (Head
    reports both its joins, Heart reports its remaining one to Life).
    Proves the rule fires and its claim is directly readable off the fired
    PalmRule object -- no claim_extraction/LLM path involved, matching how
    palm_reading._prepare_claims_from_rules itself builds `targets`."""
    text = (
        "HEAD LINE: present\n"
        "  CONTACTS: Line of Heart | joins | at start | clear\n"
        "  CONTACTS: Line of Life | joins | at start | clear\n"
        "\n"
        "HEART LINE: present\n"
        "  CONTACTS: Line of Life | joins | at start | clear\n"
    )
    result = observation_extractor.extract_relations(text)
    targets = palm_reading._assemble_relational_targets(result["contacts"])

    # Each pairwise join is filed under the feature whose block reported it
    # (no canonicalization, same as the retired typed-RELATIONSHIP path):
    # Head reports both its own joins (Heart, Life); Heart reports its
    # remaining one (Life).
    assert targets == {
        "Line of Head": {"joins_at_origin": {"Line of Heart", "Line of Life"}},
        "Line of Heart": {"joins_at_origin": {"Line of Life"}},
    }

    rules = palm_rules_table.load_rule_set()
    fired = palm_rules_table.match({}, {}, rules, targets=targets)
    fired_ids = [r.rule_id for r in fired]
    assert "L_026" in fired_ids

    l_026 = next(r for r in fired if r.rule_id == "L_026")
    assert l_026.claim == (
        "When the lines of life, head, and heart are all joined together at "
        "their commencement, it is regarded as a very unfortunate sign, "
        "indicating a reckless temperament that rushes blindly into danger."
    )


def test_l_026_does_not_fire_with_only_two_of_three_pairwise_crossings():
    """Negative: HEAD<->HEART only (the Life crossings entirely absent) --
    L_026 requires all three pairwise antecedents (AND-of-all), so it must
    NOT fire on a partial join."""
    text = "HEAD LINE: present\n  CONTACTS: Line of Heart | joins | at start | clear\n"
    result = observation_extractor.extract_relations(text)
    targets = palm_reading._assemble_relational_targets(result["contacts"])
    assert targets == {"Line of Head": {"joins_at_origin": {"Line of Heart"}}}

    rules = palm_rules_table.load_rule_set()
    fired = palm_rules_table.match({}, {}, rules, targets=targets)
    assert "L_026" not in [r.rule_id for r in fired]


# ─── H_028 single-antecedent typed-relationship rule firing (S107) ──────
# H_028 (data/palm_rules/palm_rules_head_heart_v1.json) is the other of the
# two rules the S107 cutover migrated -- a single joins_at_origin
# antecedent (Head -> Life), unlike L_026's 3-way AND. Kept as its own
# minimal fixture (Stage 0's "old-only" reference analogue) rather than
# folded into the L_026 tests above, since it exercises the single-
# antecedent, single-hand-block path the 3-way fixture doesn't cover.


def test_h_028_fires_end_to_end_from_contacts_vision_string():
    """Positive: a HEAD LINE block emitting one CONTACTS line (joins Life
    at start) fires H_028 via the same extract_relations ->
    palm_reading._assemble_relational_targets -> match() chain L_026 uses
    above."""
    text = "HEAD LINE: present\n  CONTACTS: Line of Life | joins | at start | clear\n"
    result = observation_extractor.extract_relations(text)
    targets = palm_reading._assemble_relational_targets(result["contacts"])
    assert targets == {"Line of Head": {"joins_at_origin": {"Line of Life"}}}

    rules = palm_rules_table.load_rule_set()
    fired = palm_rules_table.match({}, {}, rules, targets=targets)
    fired_ids = [r.rule_id for r in fired]
    assert "H_028" in fired_ids

    h_028 = next(r for r in fired if r.rule_id == "H_028")
    assert h_028.claim == (
        "A head line rising from the commencement of the life line, and "
        "connected with it, indicates a sensitive and more nervous "
        "temperament, with an excess of caution that leads even clever "
        "people to hold themselves back too tightly."
    )


def test_h_028_does_not_fire_without_a_life_line_contact():
    """Negative: a HEAD LINE block reporting a contact to a DIFFERENT line
    (Heart, not Life) must not fire H_028, whose sole antecedent keys on
    Line of Life specifically."""
    text = "HEAD LINE: present\n  CONTACTS: Line of Heart | joins | at start | clear\n"
    result = observation_extractor.extract_relations(text)
    targets = palm_reading._assemble_relational_targets(result["contacts"])
    assert targets == {"Line of Head": {"joins_at_origin": {"Line of Heart"}}}

    rules = palm_rules_table.load_rule_set()
    fired = palm_rules_table.match({}, {}, rules, targets=targets)
    assert "H_028" not in [r.rule_id for r in fired]


def test_h_028_fires_from_inflected_joined_via_s106_normalization():
    """S106/S107 integration proof: the CONTACTS line uses the PAST-TENSE
    "joined" (the exact verb-form that aborted the first S104 5b attempt)
    -- must still resolve through contact_mapper's inflection map and fire
    H_028 identically to the base-form "joins" case above."""
    text = "HEAD LINE: present\n  CONTACTS: Line of Life | joined | at start | clear\n"
    result = observation_extractor.extract_relations(text)
    targets = palm_reading._assemble_relational_targets(result["contacts"])
    assert targets == {"Line of Head": {"joins_at_origin": {"Line of Life"}}}

    rules = palm_rules_table.load_rule_set()
    fired = palm_rules_table.match({}, {}, rules, targets=targets)
    assert "H_028" in [r.rule_id for r in fired]


# ─── FT_007/FT_008: migrated to typed stopped_by, false-positive-fix (S112) ─
# FT_007 (Fate stopped-by Heart, F025a) and FT_008 (Fate stopped-by Head,
# F026) were migrated IN PLACE from the ambiguous TERMINATION-landmark
# antecedent (attribute "Position" + relation_target, S97) to the typed
# stopped_by verb token (via free-verb CONTACTS + contact_mapper) -- see
# each rule's own S112 MIGRATION schema_flag in
# data/palm_rules/palm_rules_fate_line_v1.json. Rule_ids, claims,
# source_quotes, doctrine_sentence_ids, and verified status are all
# UNCHANGED; only the antecedent's detection mechanism moved. The tests
# below prove BOTH that the new mechanism fires correctly AND that the
# false-positive the migration closes (a bare TERMINATION landmark, which
# is ambiguous between "stopped" and "joined-and-continued") no longer
# fires -- the false-positive-fix proof is the point of this section, not
# just a firing smoke test.


def _fired_ids_for_fate_contacts(text: str) -> tuple[dict, list[str]]:
    """Shared helper: routes raw Fate-line text through the SAME
    extract_relations -> merge_relational_targets(directional +
    CONTACTS-bridge) chain prepare_palm_reading itself uses, and returns
    (targets, fired_ids)."""
    result = observation_extractor.extract_relations(text)
    ct = palm_reading._assemble_relational_targets(result["contacts"])
    targets = observation_extractor.merge_relational_targets(result["targets"], ct)
    rules = palm_rules_table.load_rule_set()
    fired = sorted(r.rule_id for r in palm_rules_table.match({}, {}, rules, targets=targets))
    return targets, fired


def test_ft007_fires_on_stopped_by_heart_ft008_does_not():
    """Positive: an explicit "stopped by" CONTACTS report on Line of
    Heart fires FT_007 (Fate stopped-by Heart) and NOT FT_008 (Head)."""
    text = "FATE LINE: present\n  CONTACTS: Line of Heart | stopped by | at end | clear\n"
    targets, fired = _fired_ids_for_fate_contacts(text)
    assert targets == {"Line of Fate": {"stopped_by": "Line of Heart"}}
    assert "FT_007" in fired
    assert "FT_008" not in fired


def test_ft008_fires_on_stopped_by_head_ft007_does_not():
    """Positive: an explicit "stopped by" CONTACTS report on Line of
    Head fires FT_008 (Fate stopped-by Head) and NOT FT_007 (Heart)."""
    text = "FATE LINE: present\n  CONTACTS: Line of Head | stopped by | at end | clear\n"
    targets, fired = _fired_ids_for_fate_contacts(text)
    assert targets == {"Line of Fate": {"stopped_by": "Line of Head"}}
    assert "FT_008" in fired
    assert "FT_007" not in fired


def test_ft007_false_positive_fix_landmark_only_stays_silent():
    """THE REGRESSION-FIX PROOF (S112's whole point). A Fate line whose
    TERMINATION lands on Line of Heart, with NO stopped_by CONTACTS
    report -- the ambiguous "landmark only" case that could equally mean
    "abruptly halted" (this rule's bad-omen doctrine) or "joined and
    continued to Jupiter" (FT_016's opposite, good-omen doctrine). Under
    the OLD (pre-S112) antecedent shape (`attribute: "Position", value:
    null, relation_target: "Line of Heart"`), this exact `targets` dict
    -- {"Line of Fate": {"Position": "Line of Heart"}} -- WOULD have
    satisfied FT_007's single antecedent and fired the false "success
    ruined" claim on what might genuinely be a good-omen hand. Under the
    migrated `stopped_by` antecedent, this landmark-only signal does not
    satisfy it -- FT_007 stays honestly silent instead of guessing."""
    text = "FATE LINE: present\n  ORIGIN: Wrist\n  TERMINATION: Line of Heart\n  PROXIMITY: n/a to none\n  BRANCHES_TO: none\n  CONTACTS: none\n"
    targets, fired = _fired_ids_for_fate_contacts(text)
    # The OLD antecedent's exact trigger shape IS present in targets --
    # proving this fixture genuinely exercises the ambiguous case, not a
    # vacuously-different one.
    assert targets["Line of Fate"]["Position"] == "Line of Heart"
    assert "stopped_by" not in targets["Line of Fate"]
    assert "FT_007" not in fired  # the false positive this migration closes
    assert "FT_016" not in fired  # nor does the (unrelated) good-omen rule fire on a bare landmark


def test_ft016_join_continue_scenario_does_not_trigger_ft007_bad_omen():
    """DOCTRINAL-INTEGRITY PROOF: on the SAME Fate<->Heart interaction
    that satisfies FT_016's positive "joins Heart and ascends to Jupiter"
    doctrine (good omen), FT_007's migrated stopped_by antecedent must
    NOT also fire the negative "success ruined" claim -- no bad-omen
    claim on a good-omen hand. FT_016 itself requires a `location`
    ("Mount of Jupiter") that free-verb CONTACTS structurally cannot
    supply (S104/S107 finding: CONTACTS has no location/mount channel,
    which is why FT_016 stays parked/unreachable from live CONTACTS text
    -- unchanged by this migration). This constructs the targets dict
    directly via observation_extractor._store_relationship, the SAME
    filing primitive _assemble_relational_targets itself calls, rather
    than routing through CONTACTS text (which cannot express this case)."""
    targets: dict = {}
    observation_extractor._store_relationship(
        targets, "Line of Fate", "meets", "Line of Heart", "Mount of Jupiter",
    )
    assert targets == {
        "Line of Fate": {
            "meets": {"Line of Heart"},
            "meets__location": {"Line of Heart": "Mount of Jupiter"},
        }
    }

    rules = palm_rules_table.load_rule_set()
    fired = sorted(r.rule_id for r in palm_rules_table.match({}, {}, rules, targets=targets))
    assert "FT_016" in fired
    assert "FT_007" not in fired


def test_david_right_shape_neither_stopped_by_rule_fires():
    """The real hand from S110's probe (David_right): Fate terminates at
    Mount of Saturn, crosses Head mid-course -- the inert `cuts` signal
    (no rule consumes it, per S110's own finding) must not trip either
    stopped-by rule. Correct silence, not a pipeline gap."""
    text = (
        "FATE LINE: present\n"
        "  ORIGIN: Wrist\n"
        "  TERMINATION: Mount of Saturn\n"
        "  PROXIMITY: medium to Line of Head\n"
        "  BRANCHES_TO: none\n"
        "  CONTACTS: Line of Head | crosses | mid-course | clear\n"
    )
    targets, fired = _fired_ids_for_fate_contacts(text)
    assert targets["Line of Fate"]["cuts"] == {"Line of Head"}
    assert "FT_007" not in fired
    assert "FT_008" not in fired
