"""Phase 1 (S137) -- the interpreter emits typed preconditions and the gate
evaluates them.

The invariant every test here defends: **the typed path may confirm or refute,
and its absence or failure may never cost a claim.** Phase 1 is additive, so an
interpreter that emits nothing new must behave exactly as it did before.
"""
from __future__ import annotations

import json

import pytest

from agent.astro import interpreter as I
from agent.astro import predicates as P
from agent.astro import silence_gate as SG


FACTS = {
    "ascendant_sign": "Sagittarius",
    "lord_house_map": {1: 5, 6: 6, 9: 4, 10: 4, 11: 6},
    "planet_positions": {"Jupiter": {"house": 5, "sign": "Aries"},
                         "Mercury": {"house": 4, "sign": "Pisces"}},
    "yogas": {"fired": [{"id": "adhi", "name": "Adhi"}],
              "ruled_out": [{"id": "gajakesari_yoga", "name": "Gajakesari"}]},
}

PAYLOAD = {"segments": [{"segment_id": "ch21_s005", "text": "verse text", "kept": True}],
           "units": []}


def _stub(obj):
    def llm(system, user, *, model, reasoning_effort):
        llm.system = system
        return json.dumps(obj), {"prompt_tokens": 1}
    return llm


# ── the emission contract ──────────────────────────────────────────────────

def test_the_prompt_carries_the_vocabulary_generated_from_the_registry():
    """One closed vocabulary, one owner (P-030). If the prompt ever stops being
    generated, a registry edit silently stops reaching the model."""
    vocab = P.vocabulary_prompt()
    for name, (_fn, _cls, gloss, guard) in P.PREDICATES.items():
        assert f'"type": "{name}"' in vocab, name
        assert gloss in vocab and guard in vocab, f"{name} lost its gloss/guard"
    assert "unfittable" in vocab


def test_the_vocabulary_reaches_the_live_system_prompt():
    llm = _stub({"claims": [{"statement": "s", "segment_ids": ["ch21_s005"]}],
                 "silent_on": [], "refused": False})
    I.interpret("q", "FACTS", PAYLOAD, llm=llm)
    assert "PRECONDITIONS" in llm.system
    assert '"type": "yoga_fired"' in llm.system


def test_valid_preconditions_survive_onto_the_claim():
    llm = _stub({"claims": [{"statement": "s", "segment_ids": ["ch21_s005"],
                             "preconditions": [{"type": "lord_in_house",
                                                "lord_of": 10, "house": 4}]}],
                 "silent_on": [], "refused": False})
    out = I.interpret("q", "F", PAYLOAD, llm=llm)
    assert out["claims"][0]["preconditions"] == [
        {"type": "lord_in_house", "lord_of": 10, "house": 4}]
    assert out["claims_with_preconditions"] == 1
    assert out["precondition_rejects"] == []


@pytest.mark.parametrize("bad", [
    {"type": "planet_nakshatra", "graha": "Sun"},        # outside the vocabulary
    {"type": "lord_in_house", "lord_of": 10},            # missing an argument
    {"type": "yoga_fired", "yoga_id": "adhi", "orb": 3},  # invented argument
    "not an object",
])
def test_an_illegal_precondition_is_dropped_and_recorded_never_costing_the_claim(bad):
    llm = _stub({"claims": [{"statement": "s", "segment_ids": ["ch21_s005"],
                             "preconditions": [bad]}],
                 "silent_on": [], "refused": False})
    out = I.interpret("q", "F", PAYLOAD, llm=llm)
    assert len(out["claims"]) == 1, "the claim must survive an illegal precondition"
    assert out["claims"][0]["preconditions"] == []
    assert len(out["precondition_rejects"]) == 1


def test_a_claim_with_no_preconditions_is_unchanged_and_kept():
    """Phase 1 is ADDITIVE: an interpreter that ignores the new field behaves
    exactly as before."""
    llm = _stub({"claims": [{"statement": "s", "segment_ids": ["ch21_s005"]}],
                 "silent_on": [], "refused": False})
    out = I.interpret("q", "F", PAYLOAD, llm=llm)
    assert out["claims"][0]["preconditions"] == []
    assert out["claims_with_preconditions"] == 0


def test_the_ghost_guard_is_still_the_only_thing_that_drops_a_claim():
    llm = _stub({"claims": [{"statement": "s", "segment_ids": ["ch99_s001"],
                             "preconditions": [{"type": "yoga_fired",
                                                "yoga_id": "adhi"}]}],
                 "silent_on": [], "refused": False})
    out = I.interpret("q", "F", PAYLOAD, llm=llm)
    assert out["claims"] == [] and out["ghost_citations"] == ["ch99_s001"]


# ── the gate consumes them ─────────────────────────────────────────────────

def _judge(preconds):
    claim = {"statement": "With the 10th lord in the 4th, you gain.",
             "segment_ids": ["ch21_s005"], "preconditions": preconds}
    return SG.judge_claim(claim, {"ch21_s005": "text"}, {10: 4}, FACTS)


def test_satisfied_maps_to_applicable_and_is_marked_typed():
    v = _judge([{"type": "yoga_fired", "yoga_id": "adhi"}])
    assert v.verdict == SG.APPLICABLE and v.decided_by == "typed"
    assert v.predicate_detail and "adhi" in v.reason


def test_contradicted_maps_to_not_applicable__the_only_drop_authority():
    v = _judge([{"type": "yoga_fired", "yoga_id": "gajakesari_yoga"}])
    assert v.verdict == SG.NOT_APPLICABLE and v.decided_by == "typed"


def test_unevaluable_maps_to_undetermined_so_the_claim_still_ships():
    v = _judge([{"type": "yoga_fired", "yoga_id": "chamara"}])
    assert v.verdict == SG.UNDETERMINED and v.decided_by == "typed"


def test_a_yoga_claim_is_now_judgeable__the_defect_that_started_this():
    """Live 20260918T193426Z: five yoga claims were demoted as 'unverified'
    while the detector had already computed them. Typed, they come back
    APPLICABLE."""
    for yid in ("adhi",):
        assert _judge([{"type": "yoga_fired", "yoga_id": yid}]).verdict == SG.APPLICABLE


def test_typed_verdicts_do_not_fall_back_to_the_prose_reader():
    """A typed UNEVALUABLE must NOT be re-judged by the regex, which could
    overturn it. The statement below WOULD satisfy the prose reader (10th lord
    in the 4th is true here); the typed verdict must still stand."""
    v = _judge([{"type": "yoga_fired", "yoga_id": "chamara"}])
    assert v.verdict == SG.UNDETERMINED
    assert v.decided_by == "typed"


def test_no_preconditions_still_uses_the_prose_reader_unchanged():
    v = SG.judge_claim({"statement": "With the 10th lord in the 4th, you gain.",
                        "segment_ids": ["ch21_s005"]},
                       {"ch21_s005": "t"}, {10: 4}, FACTS)
    assert v.verdict == SG.APPLICABLE and v.decided_by == "prose"


def test_judge_claim_keeps_its_old_three_argument_signature():
    """Every existing caller and test passes three positional arguments."""
    v = SG.judge_claim({"statement": "With the 10th lord in the 4th, you gain.",
                        "segment_ids": ["ch21_s005"]}, {"ch21_s005": "t"}, {10: 4})
    assert v.verdict == SG.APPLICABLE and v.decided_by == "prose"


# ── end to end through the gate ────────────────────────────────────────────

def test_apply_silence_gate_reports_the_migration_metrics():
    out = {"claims": [
        {"statement": "a", "segment_ids": ["ch21_s005"],
         "preconditions": [{"type": "yoga_fired", "yoga_id": "adhi"}]},
        {"statement": "b", "segment_ids": ["ch21_s005"],
         "preconditions": [{"type": "yoga_fired", "yoga_id": "gajakesari_yoga"}]},
        {"statement": "With the 10th lord in the 4th, you gain.",
         "segment_ids": ["ch21_s005"]},
    ], "silent_on": []}
    res = SG.apply_silence_gate(out, PAYLOAD, FACTS)
    assert res.stats["typed_decided"] == 2
    assert res.stats["prose_decided"] == 1
    assert res.stats["claims_dropped"] == 1        # only the contradicted one
    assert res.stats["predicate_coverage"]["by_fact_class"]["yogas"][P.SATISFIED] == 1
    assert res.error is None


def test_an_empty_fact_block_drops_nothing():
    """The gate's own fail-open (S129) still governs: `_lord_house_map` raises on
    an unusable fact block, the gate records the error and ships every claim
    UNMODIFIED. The typed path must not change that -- a verifier that cannot
    run keeps, it does not discard."""
    claim = {"statement": "a", "segment_ids": ["ch21_s005"],
             "preconditions": [{"type": "lord_in_house", "lord_of": 10, "house": 4}]}
    res = SG.apply_silence_gate({"claims": [claim], "silent_on": []}, PAYLOAD, {})
    assert res.dropped_claims == []
    assert res.kept_claims == [claim]
    assert res.stats.get("gate_failed") is True and res.error


def test_a_fact_block_missing_only_the_typed_classes_still_drops_nothing():
    """The realistic partial case: lord_house_map present (so the gate runs),
    but the yoga report absent. Every yoga precondition must land UNEVALUABLE
    and the claim must survive."""
    facts = {"lord_house_map": {10: 4}}
    claim = {"statement": "a", "segment_ids": ["ch21_s005"],
             "preconditions": [{"type": "yoga_fired", "yoga_id": "adhi"}]}
    res = SG.apply_silence_gate({"claims": [claim], "silent_on": []}, PAYLOAD, facts)
    assert res.error is None
    assert res.stats["claims_dropped"] == 0
    assert res.verdicts[0].verdict == SG.UNDETERMINED


# ── S137 fix pass: the two live defects ────────────────────────────────────
# Measured on diagnostics/qa_capture/20260919T072700Z.md: typed_share_pct was
# 100% but `yoga_fired` was used ZERO times on a yoga question and `unfittable`
# took 9 of 15 predicate slots. Both were PROMPT defects, not architecture.

def test_the_yoga_catalogue_is_enumerated_in_the_prompt():
    """P-030, the version I shipped myself: `yoga_id` is a closed value space
    the model cannot guess. Listing it is the fix."""
    vocab = P.vocabulary_prompt(FACTS)
    assert "adhi" in vocab and "gajakesari_yoga" in vocab
    assert "this list is COMPLETE" in vocab


def test_the_catalogue_is_fired_plus_ruled_out__not_just_fired():
    """A ruled-out yoga must be nameable, or `yoga_ruled_out` can never be used
    and the counterweight half of the answer stays unreachable."""
    assert P.yoga_catalogue(FACTS) == ["adhi", "gajakesari_yoga"]


def test_no_catalogue_means_the_prompt_forbids_yoga_predicates():
    """Fail-safe: without a catalogue the model must not invent ids."""
    vocab = P.vocabulary_prompt({})
    assert "do not emit" in vocab and "`yoga_fired`" in vocab


def test_the_catalogue_reaches_the_live_system_prompt_via_chart_facts():
    llm = _stub({"claims": [{"statement": "s", "segment_ids": ["ch21_s005"]}],
                 "silent_on": [], "refused": False})
    I.interpret("q", "F", PAYLOAD, llm=llm, chart_facts=FACTS)
    assert "adhi" in llm.system


def test_interpret_without_chart_facts_still_works():
    """Backward compatible: every existing caller passes three positionals."""
    llm = _stub({"claims": [{"statement": "s", "segment_ids": ["ch21_s005"]}],
                 "silent_on": [], "refused": False})
    out = I.interpret("q", "F", PAYLOAD, llm=llm)
    assert len(out["claims"]) == 1
    assert "do not emit" in llm.system


def test_the_prompt_tells_the_model_a_compound_condition_is_several_predicates():
    """Live: 'Saturn, Mars and 10th lord all in the 7th' became `unfittable`
    when it is three predicates -- and would have been correctly CONTRADICTED."""
    vocab = P.vocabulary_prompt(FACTS)
    assert "SEVERAL PREDICATES" in vocab and "ANDed" in vocab


def test_the_prompt_forbids_unfittable_for_merely_absent_facts():
    """Live notes read 'not provided in chart facts' nine times -- the model was
    checking the facts instead of stating the verse's condition."""
    vocab = P.vocabulary_prompt(FACTS)
    assert "NOT AGAINST THE CHART FACTS" in vocab
    assert "Karakamsa" in vocab      # what unfittable IS for


def test_coverage_receives_real_claim_verdicts_not_placeholders():
    """Live capture showed claim_verdicts 0/0/0 because the gate passed "". """
    out = {"claims": [
        {"statement": "a", "segment_ids": ["ch21_s005"],
         "preconditions": [{"type": "yoga_fired", "yoga_id": "adhi"}]},
        {"statement": "b", "segment_ids": ["ch21_s005"],
         "preconditions": [{"type": "yoga_fired", "yoga_id": "gajakesari_yoga"}]},
        {"statement": "c", "segment_ids": ["ch21_s005"],
         "preconditions": [{"type": "yoga_fired", "yoga_id": "chamara"}]},
    ], "silent_on": []}
    cov = SG.apply_silence_gate(out, PAYLOAD, FACTS).stats["predicate_coverage"]
    assert cov["claim_verdicts"] == {P.SATISFIED: 1, P.CONTRADICTED: 1,
                                     P.UNEVALUABLE: 1}


# ── S137 amendment: statement coverage (ADVISORY) ──────────────────────────
# Fixtures are the REAL shipped claims of diagnostics/qa_capture/20260919T080136Z.md.
# Four of eight carried a chart assertion their preconditions never tested. The
# counter must see them; it must never act on them.

def test_a_true_precondition_that_is_not_the_statements_condition_is_flagged():
    """B4, the sharpest live case: "With the 11th lord in the 10th ..." declared
    ONLY `house_lord_is(11, Venus)` -- true, and silent about where the 11th
    lord sits (the 6th). Run A typed the same segment as lord_in_house(11,10),
    got CONTRADICTED and correctly dropped it."""
    cov = P.statement_coverage(
        "With the 11th lord in the 10th, the text says you are honoured by authority.",
        [{"type": "house_lord_is", "house": 11, "graha": "Venus"}])
    assert "h10" in cov["uncovered"] and cov["covered"] is False


def test_an_untested_ascendant_assertion_is_flagged():
    """B1: "... and aspecting the ascendant", declared as an aspect to house 10.
    Without ascendant -> h1 this, the commonest live under-coverage, is invisible."""
    cov = P.statement_coverage(
        "With the 10th lord in the 4th and aspecting the ascendant, texts grant a Raja Yoga.",
        [{"type": "planet_in_house", "graha": "Mercury", "house": 4},
         {"type": "aspects_house", "graha": "Mercury", "house": 10}])
    assert "h1" in cov["uncovered"]


def test_a_yoga_predicate_covers_no_grahas_the_sentence_names():
    """B3: two genuinely FIRED yoga predicates, and the parenthetical "Jupiter
    and Mars mutually aspect" rides in untested (it is false -- Jupiter aspects
    1/9/11, Mars is in 2)."""
    cov = P.statement_coverage(
        "When the ascendant lord is strong (Jupiter and Mars mutually aspect), a Raja Yoga.",
        [{"type": "yoga_fired", "yoga_id": "kendra_trikona_1_5"},
         {"type": "yoga_fired", "yoga_id": "kendra_trikona_4_5"}])
    assert set(cov["uncovered"]) >= {"Jupiter", "Mars"}


def test_an_honestly_covered_claim_is_not_flagged():
    cov = P.statement_coverage(
        "With the 10th lord in the 4th and the 9th lord also in the 4th, you gain.",
        [{"type": "lord_in_house", "lord_of": 10, "house": 4},
         {"type": "lord_in_house", "lord_of": 9, "house": 4}])
    assert cov["uncovered"] == [] and cov["covered"] and cov["coverage_ratio"] == 1.0


def test_the_advisory_never_changes_a_verdict_or_drops_a_claim():
    """THE INVARIANT. An entirely uncovered statement still ships, still
    APPLICABLE. A counter, not a judge."""
    claim = {"statement": "With the 11th lord in the 10th, Saturn exalted in Leo, you rise.",
             "segment_ids": ["ch21_s005"],
             "preconditions": [{"type": "yoga_fired", "yoga_id": "adhi"}]}
    res = SG.apply_silence_gate({"claims": [claim], "silent_on": []}, PAYLOAD, FACTS)
    assert res.stats["claims_dropped"] == 0
    assert res.verdicts[0].verdict == SG.APPLICABLE
    assert res.verdicts[0].uncovered_tokens
    assert res.stats["claims_with_uncovered_tokens"] == 1


def test_the_advisory_rate_is_reported_for_promotion():
    out = {"claims": [
        {"statement": "With the 10th lord in the 4th, you gain.", "segment_ids": ["ch21_s005"],
         "preconditions": [{"type": "lord_in_house", "lord_of": 10, "house": 4}]},
        {"statement": "With the 11th lord in the 10th, you are honoured.",
         "segment_ids": ["ch21_s005"],
         "preconditions": [{"type": "house_lord_is", "house": 11, "graha": "Venus"}]},
    ], "silent_on": []}
    st = SG.apply_silence_gate(out, PAYLOAD, FACTS).stats
    assert st["claims_with_uncovered_tokens"] == 1
    assert st["typed_decided"] == 2
    assert st["statement_coverage_advisory"][0]["uncovered_tokens"] == ["h10"]


def test_composer_and_the_counter_share_ONE_token_extractor():
    """Two copies of a closed vocabulary drift (P-030), and the enforcing check
    and the advisory counter must agree on what a chart token IS or their rates
    cannot be compared."""
    from agent.astro import composer as C
    assert C.chart_tokens is P.chart_tokens


def test_the_prompt_forbids_asserting_what_was_not_declared():
    vocab = P.vocabulary_prompt(FACTS)
    assert "DO NOT ASSERT IN THE SENTENCE WHAT YOU HAVE NOT DECLARED" in vocab
