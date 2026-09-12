"""Tests for the ADVISORY planet-in-house reader (S129).

The reader records a verdict and never removes a claim. These tests exist to
prove two things before it could ever be promoted to enforcing:
  1. it judges the shapes it claims to judge, on Sulabh's REAL positions;
  2. it refuses -- returns None -- on every shape it cannot judge safely,
     above all the sentence that states BOTH a lord and a planet condition.

HARDEST CASE FIRST: every disqualifier test below is a case where a naive
matcher would have produced a confident, wrong verdict.
"""
from __future__ import annotations

import pytest

from agent.astro import silence_gate as SG

# Sulabh, verified 12/12 against the JHora oracle (S129).
_POS = {"Sun": 4, "Moon": 12, "Mars": 2, "Mercury": 4, "Jupiter": 5,
        "Venus": 6, "Saturn": 1, "Rahu": 3, "Ketu": 9}


# ── it judges what it says it judges ───────────────────────────────────────

@pytest.mark.parametrize("stmt,expected", [
    ("Saturn is in the 1st, which steadies your early life.", SG.APPLICABLE),
    ("With Venus in the 6th, service and rivalry colour your comforts.", SG.APPLICABLE),
    ("Jupiter is placed in the 5th.", SG.APPLICABLE),
    ("Ketu happens to be in the 9th.", SG.APPLICABLE),
    ("Mars is in the 7th, straining partnership.", SG.NOT_APPLICABLE),
    ("The Moon is in the 4th.", SG.NOT_APPLICABLE),
])
def test_plain_planet_in_house_is_judged_against_the_real_chart(stmt, expected):
    verdict, why = SG.judge_planet_claim(stmt, _POS)
    assert verdict == expected, why


def test_applicable_reason_names_the_graha_and_house():
    _, why = SG.judge_planet_claim("Saturn is in the 1st.", _POS)
    assert "Saturn" in why and "1" in why


def test_not_applicable_reason_states_where_the_planet_actually_is():
    _, why = SG.judge_planet_claim("Mars is in the 7th.", _POS)
    assert "in the 2" in why, why


# ── the ambiguity rule: both shapes in one sentence ────────────────────────

def test_a_sentence_stating_both_shapes_is_refused_not_guessed():
    """"The 3rd lord Mars is in the 7th" satisfies BOTH readers. Measured: 5
    such sentences in the whole corpus. Guessing one reading lets a single
    sentence produce two different verdicts."""
    stmt = "The 3rd lord Mars is in the 7th."
    assert SG._CONDITION_RE.search(stmt), "premise: the lord reader must match this"
    rel, why = SG.read_planet_condition(stmt)
    assert rel is None
    assert "both" in why.lower() and "ambiguous" in why.lower()
    assert SG.judge_planet_claim(stmt, _POS)[0] == SG.UNDETERMINED


def test_appositive_lord_phrasing_reads_as_a_planet_claim_and_that_is_correct():
    """"Mars, the lord of the 3rd, is in the 7th" is NOT ambiguous: the lord
    reader does not match it at all (see the blind-spot test below), and the
    sentence's actual assertion is that MARS is in the 7th. Reading it as a
    planet claim is the correct reading, not a guess."""
    rel, _ = SG.read_planet_condition("Mars, the lord of the 3rd, is in the 7th.")
    assert rel == ("Mars", 7)


def test_enforcing_lord_reader_blind_spot_is_recorded_not_silently_relied_on():
    """PRE-EXISTING, S129 finding, fails in the SAFE direction.

    `_CONDITION_RE` requires "<ordinal> lord". It does not match the equally
    common "the lord of the <ordinal>" phrasing, so such a claim is never
    judged and is kept by fail-open. That is the safe direction, so this is
    recorded rather than fixed: widening a matcher that can DROP requires the
    measured-evidence bar S125 set, and nothing here supplies it.
    """
    assert SG.read_condition("The lord of the 3rd is in the 7th.")[0] is None
    assert SG.read_condition("The 3rd lord is in the 7th.")[0] == (3, 7)


def test_the_lord_reader_is_untouched_by_the_new_shape():
    """Regression guard: adding the planet reader must not change a single
    verdict the enforcing lord reader already produces."""
    rel, _ = SG.read_condition("With the 10th lord in the 4th, you gain.")
    assert rel == (10, 4)


# ── every disqualifier, each a would-be confident wrong answer ─────────────

@pytest.mark.parametrize("stmt,marker", [
    ("Saturn is not in the 1st.", "negated"),
    ("Unless Saturn is in the 1st, this does not apply.", "negated"),
    ("Venus is in the 6th from the Moon.", "reference frame"),
    ("In the Navamsa, Venus is in the 6th.", "reference frame"),
    ("Jupiter aspecting the lord is in the 5th.", "aspecting"),
    ("Saturn conjunct Mars is in the 1st.", "aspecting"),
    ("During the Saturn dasha, Venus is in the 6th.", "aspecting"),
    ("Saturn is in the 1st or the 7th.", "alternative"),
    ("Saturn is in the 1st, the 4th.", "alternative"),
])
def test_disqualified_shapes_return_none_with_a_reason(stmt, marker):
    rel, why = SG.read_planet_condition(stmt)
    assert rel is None, f"should not have judged: {stmt}"
    assert marker in why, why


def test_a_compound_two_planet_claim_is_refused():
    """Two DIFFERENT (graha, house) pairs cannot be judged one part at a time."""
    rel, why = SG.read_planet_condition("Saturn is in the 1st. Venus is in the 6th.")
    assert rel is None
    assert "compound" in why


def test_two_planets_joined_by_and_in_one_sentence_is_also_refused():
    """Caught by the disjunction guard rather than the compound guard -- either
    reason is fine, refusing is what matters."""
    rel, why = SG.read_planet_condition("Saturn is in the 1st and Venus is in the 6th.")
    assert rel is None, why


def test_same_condition_stated_twice_is_still_judgeable():
    """Two matches of the SAME (graha, house) pair is not a compound claim."""
    rel, _ = SG.read_planet_condition("Saturn is in the 1st. Saturn is in the 1st.")
    assert rel == ("Saturn", 1)


def test_no_planet_condition_at_all():
    rel, why = SG.read_planet_condition("Your career will prosper through effort.")
    assert rel is None
    assert "no plain planet-in-house condition" in why


# ── failure posture: advisory must never break anything ────────────────────

def test_empty_positions_yields_undetermined_not_a_crash():
    assert SG.judge_planet_claim("Saturn is in the 1st.", {})[0] == SG.UNDETERMINED


def test_planet_absent_from_positions_is_undetermined():
    v, why = SG.judge_planet_claim("Ketu is in the 9th.", {"Sun": 4})
    assert v == SG.UNDETERMINED
    assert "not in the supplied positions" in why


@pytest.mark.parametrize("stmt", [None, "", "   ", 12345])
def test_malformed_statement_never_raises(stmt):
    v, _ = SG.judge_planet_claim(stmt if isinstance(stmt, str) else str(stmt), _POS)
    assert v in (SG.APPLICABLE, SG.NOT_APPLICABLE, SG.UNDETERMINED)


# ── the gate stays ADVISORY: it must not remove anything ───────────────────

def test_apply_silence_gate_never_drops_on_the_planet_shape():
    """A planet claim that is FALSE for this chart must still ship, because the
    reader has not earned drop authority (no measured wrong-drop distribution)."""
    interp = {"claims": [{"statement": "Mars is in the 7th, straining partnership.",
                          "segment_ids": ["s1"]}],
              "silent_on": [], "refused": False}
    payload = {"segments": [{"segment_id": "s1", "text": "Mars in the 7th ...",
                             "kept": True}], "units": []}
    facts = {"lord_house_map": {h: 1 for h in range(1, 13)},
             "ascendant_sign": "Sagittarius",
             "planet_positions": {p: {"house": h, "sign": "X"} for p, h in _POS.items()}}

    g = SG.apply_silence_gate(interp, payload, facts)

    assert len(g.kept_claims) == 1, "advisory reader must not drop"
    assert g.dropped_claims == []
    assert g.stats["planet_reader_mode"] == "advisory"
    assert g.stats["advisory_not_applicable"] == 1
    assert g.stats["advisory_would_drop_a_kept_claim"] == 1, (
        "this is the promotion metric -- it must SEE the disagreement")
    assert g.stats["advisory_detail"][0]["enforced_verdict"] == SG.UNDETERMINED


def test_advisory_detail_is_recorded_for_every_claim():
    interp = {"claims": [{"statement": "Saturn is in the 1st.", "segment_ids": ["s1"]},
                         {"statement": "Your career prospers.", "segment_ids": ["s1"]}],
              "silent_on": [], "refused": False}
    payload = {"segments": [{"segment_id": "s1", "text": "x", "kept": True}], "units": []}
    facts = {"lord_house_map": {h: 1 for h in range(1, 13)}, "ascendant_sign": "Sag",
             "planet_positions": {p: {"house": h, "sign": "X"} for p, h in _POS.items()}}
    g = SG.apply_silence_gate(interp, payload, facts)
    assert len(g.stats["advisory_detail"]) == 2
    assert g.stats["advisory_applicable"] == 1
    assert g.stats["advisory_undetermined"] == 1


def test_gate_without_planet_positions_still_works_unchanged():
    """Legacy chart_facts (fact_block_text path) carries no positions."""
    interp = {"claims": [{"statement": "With the 1st lord in the 1st, you lead.",
                          "segment_ids": ["s1"]}], "silent_on": [], "refused": False}
    payload = {"segments": [{"segment_id": "s1", "text": "x", "kept": True}], "units": []}
    facts = {"lord_house_map": {h: 1 for h in range(1, 13)}, "ascendant_sign": "Sag"}
    g = SG.apply_silence_gate(interp, payload, facts)
    assert g.error is None
    assert g.stats["advisory_undetermined"] == 1
