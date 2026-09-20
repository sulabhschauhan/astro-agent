"""
P-033 silence-judging tests. Runs against the real predicates.py via
silence_gate.judge_silence. Cases drawn from the live capture
20260919T122618Z where possible. HARDEST-CASE first (WS#3).

These passed 13/13 in an isolated cloud harness before landing; kept here as
the regression set for the inverted mapping and the resolution guard.
"""
from agent.astro.silence_gate import (
    judge_silence, SilenceVerdict, JUSTIFIED, CAUGHT_MISS, UNCHECKABLE,
)

# Minimal chart_facts shaped exactly as predicates.py reads it.
# Mars = 5th lord, Exalted (Capricorn) -- the ch15_s003 case.
# 11th lord sits in the 6th -- the ch24_s108 case.
CHART = {
    "ascendant_sign": "Virgo",
    "lord_house_map": {11: 6, 5: 10, 8: 8},
    "house_lords": {5: {"lord": "Mars", "sign": "Capricorn"}},
    "planet_positions": {
        "Mars": {"house": 10, "sign": "Capricorn", "dignity": "Exalted"},
        "Saturn": {"house": 7, "sign": "Aries"},
        "Jupiter": {"house": 3, "sign": "Scorpio"},
    },
    "navamsa": {"placements": {"Mars": {"house": 1, "sign": "Aries", "dignity": "Exalted"}}},
    "yogas": {"fired": [{"id": "adhi"}], "ruled_out": [{"id": "gajakesari_yoga"}]},
}


# --- HARDEST CASES FIRST ---------------------------------------------------

def test_compound_all_hold_is_caught_miss():
    s = {"topic": "x", "note": "needs Saturn 7 and Mars 10", "withheld_because": [
        {"type": "planet_in_house", "graha": "Saturn", "house": 7},
        {"type": "planet_in_house", "graha": "Mars", "house": 10}]}
    assert judge_silence(s, CHART).verdict == CAUGHT_MISS


def test_compound_one_fails_is_justified():
    s = {"topic": "x", "note": "needs Saturn 7 and Mars 7", "withheld_because": [
        {"type": "planet_in_house", "graha": "Saturn", "house": 7},
        {"type": "planet_in_house", "graha": "Mars", "house": 7}]}
    assert judge_silence(s, CHART).verdict == JUSTIFIED


def test_partial_unevaluable_never_alarms():
    s = {"topic": "x", "note": "needs Saturn 7 and Venus exalted", "withheld_because": [
        {"type": "planet_in_house", "graha": "Saturn", "house": 7},
        {"type": "planet_dignity", "graha": "Venus", "dignity": "Exalted"}]}
    v = judge_silence(s, CHART)
    assert v.verdict == UNCHECKABLE and v.downgraded_fragile is False


def test_navamsa_satisfied_is_downgraded_not_alarmed():
    s = {"topic": "x", "note": "needs Mars exalted in navamsa", "withheld_because": [
        {"type": "navamsa_dignity", "graha": "Mars", "dignity": "Exalted"}]}
    v = judge_silence(s, CHART)
    assert v.verdict == UNCHECKABLE and v.downgraded_fragile is True


# --- THE LIVE ch15_s003 DEFECT (the reason P-033 exists) -------------------

def test_ch15_s003_caught_miss():
    s = {"topic": "housing (ch15 v3)", "segment_ids": ["ch15_s003"],
         "note": "needs 5th lord own sign/navamsa or exalted; not met here",
         "withheld_because": [{"type": "planet_dignity", "graha": "Mars", "dignity": "Exalted"}]}
    v = judge_silence(s, CHART)
    assert v.verdict == CAUGHT_MISS and v.decided_by == "typed"


# --- JUSTIFIED / UNCHECKABLE from real capture silences --------------------

def test_ch24_s108_lord_in_house_justified():
    s = {"topic": "11th lord in 12th", "segment_ids": ["ch24_s108"],
         "note": "11th lord in the 12th; here it is in the 6th",
         "withheld_because": [{"type": "lord_in_house", "lord_of": 11, "house": 12}]}
    assert judge_silence(s, CHART).verdict == JUSTIFIED


def test_dasha_unfittable_is_uncheckable():
    s = {"topic": "maraka timing", "note": "requires dasha timing not provided",
         "withheld_because": [{"type": "unfittable", "note": "dasha timing"}]}
    assert judge_silence(s, CHART).verdict == UNCHECKABLE


def test_yoga_fired_silence_is_caught_miss():
    s = {"topic": "adhi", "note": "adhi not present",
         "withheld_because": [{"type": "yoga_fired", "yoga_id": "adhi"}]}
    assert judge_silence(s, CHART).verdict == CAUGHT_MISS


# --- BACK-COMPAT + FAIL-SAFE -----------------------------------------------

def test_legacy_bare_string_is_uncheckable_prose():
    v = judge_silence("ch15_s006: requires multiple placements not present", CHART)
    assert v.verdict == UNCHECKABLE and v.decided_by == "prose"


def test_empty_withheld_because_is_uncheckable():
    assert judge_silence({"topic": "off topic", "note": "off topic"}, CHART).verdict == UNCHECKABLE


def test_malformed_never_raises():
    for junk in (None, 42, [], {"withheld_because": "not a list"},
                 {"withheld_because": [{"type": "no_such_pred"}]},
                 {"withheld_because": [{"type": "planet_dignity"}]}):
        v = judge_silence(junk, CHART)
        assert v.verdict in (JUSTIFIED, CAUGHT_MISS, UNCHECKABLE)
        assert v.verdict != CAUGHT_MISS


def test_no_chart_facts_is_uncheckable():
    s = {"topic": "x", "withheld_because": [
        {"type": "planet_dignity", "graha": "Mars", "dignity": "Exalted"}]}
    assert judge_silence(s, {}).verdict == UNCHECKABLE


def test_advisory_uncovered_tokens_recorded_never_acted():
    s = {"topic": "x", "note": "the 5th lord and Jupiter both matter",
         "withheld_because": [{"type": "planet_dignity", "graha": "Mars", "dignity": "Exalted"}]}
    v = judge_silence(s, CHART)
    assert v.verdict == CAUGHT_MISS and "Jupiter" in v.uncovered_tokens
