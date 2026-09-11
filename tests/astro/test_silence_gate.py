"""
Silence gate tests. No LLM anywhere.

Hardest cases first, per Working Style #3. The cases that matter are the
ones where a WRONG drop would silence a true claim -- those are invisible
in production, so they are pinned hardest here.
"""
import pytest

from agent.astro import silence_gate as SG

# Sulabh's real chart, the one every S125 measurement used.
CHART = {"lord_house_map": {1: 1, 2: 2, 3: 3, 4: 4, 5: 2, 6: 6,
                            7: 12, 8: 12, 9: 9, 10: 4, 11: 5, 12: 6},
         "ascendant_sign": "Sagittarius"}


def _c(statement, ids=("ch24_s001",)):
    return {"statement": statement, "segment_ids": list(ids)}


def _gate(claims, payload=None, chart=CHART):
    payload = payload or {"units": [], "segments": []}
    return SG.apply_silence_gate({"claims": claims, "silent_on": []},
                                 payload, chart)


# ------------------------------------------------- THE THREE REAL DROPS ----
@pytest.mark.parametrize("statement", [
    "The native's health may be affected by phlegmatic disorders if the "
    "12th lord is in the ascendant.",
    "If the 5th lord is in the 5th, the native will have progeny if related "
    "to a benefic.",
    "If the 5th lord is in the 6th, the native will obtain such sons who "
    "will be equal to his enemies.",
])
def test_real_mismatched_claims_are_dropped(statement):
    """Verbatim from the live 2026-09-05 run. Chart: 12th->6, 5th->2."""
    r = _gate([_c(statement)])
    assert r.stats["claims_dropped"] == 1, r.verdicts[0].reason


@pytest.mark.parametrize("statement", [
    "If the 6th lord is in the 6th house, the native will be free from diseases.",
    "If the 5th lord is in the 2nd, the native will have many sons and wealth.",
    "The 10th lord is in the 4th house.",
])
def test_real_matching_claims_are_kept(statement):
    r = _gate([_c(statement)])
    assert r.stats["claims_dropped"] == 0
    assert r.verdicts[0].verdict == SG.APPLICABLE


# --------------------------------------------- FALSE-DROP PROTECTION -------
def test_disjunctive_claim_is_never_judged():
    """THE hardest case. The extractor reads only the first alternative, so
    judging this risks silencing a claim that genuinely applies."""
    r = _gate([_c("If the 5th lord is exalted or in the 2nd, 5th, or 9th "
                  "from the ascendant, obtainment of children will be there.")])
    assert r.verdicts[0].verdict == SG.UNDETERMINED
    assert "alternative houses" in r.verdicts[0].reason
    assert r.stats["claims_dropped"] == 0


def test_disjunction_guard_does_not_over_trigger():
    """A comma followed by prose is not a disjunction -- this claim MUST
    still be judged, or the guard would disable the gate entirely."""
    r = _gate([_c("If the 5th lord is in the 5th, the native will have progeny.")])
    assert r.verdicts[0].verdict == SG.NOT_APPLICABLE


@pytest.mark.parametrize("statement", [
    "If Saturn, the Moon, and Mercury are together in the 9th there will be "
    "no son at all.",
    "During the Dasa of the rasi owned or occupied by the Moon, there will "
    "be gain of wealth.",
    "Recognition from Government is indicated in the Dasa of the lord of the 10th.",
])
def test_unreadable_conditions_are_kept_not_dropped(statement):
    """Conjunctions and dasha statements carry no lord-in-house condition.
    Silence here would delete most of the corpus."""
    r = _gate([_c(statement)])
    assert r.verdicts[0].verdict == SG.UNDETERMINED
    assert r.stats["claims_dropped"] == 0


# ------------------------------------------------------- MECHANICS ---------
def test_claim_text_beats_a_coincidental_source_match():
    """Live defect: ch30_s001 carried an unrelated 2nd-lord-in-2nd verse
    that this chart satisfies, which passed a planets-in-the-9th claim for
    the wrong reason. The source must never decide."""
    payload = {"units": [], "segments": [
        {"segment_id": "ch30_s001", "kept": True,
         "text": "If the 2nd lord is in the 2nd the native gains wealth. "
                 "If Saturn, the Moon and Mercury are in the 9th, no son."}]}
    r = _gate([_c("If Saturn, the Moon, and Mercury are together in the 9th "
                  "there will be no son at all.", ["ch30_s001"])], payload)
    assert r.verdicts[0].verdict == SG.UNDETERMINED
    # the source is still recorded for audit, and it disagrees -- that is fine
    assert r.verdicts[0].sources[0].verdict == SG.APPLICABLE


def test_uncited_claim_is_still_judged_on_its_own_words():
    """Renamed: the old name said "kept" while the behaviour dropped it, and
    the kept/dropped routing was never asserted. Citation coverage is a
    different check; an uncited claim is judged on what it says."""
    r = _gate([{"statement": "If the 5th lord is in the 5th, progeny.",
                "segment_ids": []}])
    assert r.verdicts[0].verdict == SG.NOT_APPLICABLE
    assert r.kept_claims == [] and len(r.dropped_claims) == 1


def test_dropped_claims_add_a_silence_note():
    r = _gate([_c("If the 5th lord is in the 5th, the native will have progeny.")])
    assert any("this chart does not have" in s for s in r.silent_on)


def test_nothing_dropped_adds_no_note():
    r = _gate([_c("If the 6th lord is in the 6th house, free from diseases.")])
    assert r.silent_on == []


def test_string_keyed_lord_house_map_is_accepted():
    """JSON round-trips make int keys strings; must not silently misjudge."""
    chart = {"lord_house_map": {str(k): v
                                for k, v in CHART["lord_house_map"].items()}}
    r = _gate([_c("If the 6th lord is in the 6th house, free from diseases.")],
              chart=chart)
    assert r.verdicts[0].verdict == SG.APPLICABLE


def test_ungated_pct_is_reported():
    r = _gate([_c("If the 6th lord is in the 6th house, free from diseases."),
               _c("During the Dasa of the Moon there will be gain.")])
    assert r.stats["ungated_pct"] == 50.0


# ------------------------------------------------------- FAIL OPEN ---------
def test_missing_lord_house_map_ships_the_answer_unchanged():
    claims = [_c("If the 5th lord is in the 5th, progeny.")]
    r = SG.apply_silence_gate({"claims": claims, "silent_on": ["x"]},
                              {"units": [], "segments": []}, {})
    assert r.error and r.stats.get("gate_failed") is True
    assert r.kept_claims == claims and r.dropped_claims == []
    assert r.silent_on == ["x"]


def test_malformed_claims_list_fails_open():
    r = SG.apply_silence_gate({"claims": "not a list"},
                              {"units": [], "segments": []}, CHART)
    assert r.error and r.dropped_claims == []


def test_non_dict_claim_entries_are_skipped_not_fatal():
    r = _gate([_c("If the 6th lord is in the 6th house, free from diseases."),
               "junk", None])
    assert r.error is None and r.stats["claims_in"] == 1


def test_empty_answer_is_a_noop():
    r = _gate([])
    assert r.kept_claims == [] and r.error is None


def test_audit_renders_without_error():
    r = _gate([_c("If the 5th lord is in the 5th, progeny."),
               _c("If the 6th lord is in the 6th, free from diseases.")])
    out = SG.render_audit(r)
    assert "silence-gate-1.0" in out and "not_applicable" in out


# ============================================================================
# REGRESSION SUITE from the S125 adversarial review.
# Every row below was a REPRODUCED defect in silence-gate-1.0. They are the
# gate's real specification: each one must stay UNDETERMINED, because each is
# a way of silencing a claim that is true of the chart.
# ============================================================================
@pytest.mark.parametrize("statement,why", [
    # -- negation and exclusion: chart 5th lord IS in the 2nd, so these hold
    ("If the 5th lord is not in the 5th, the native will lack progeny.", "not"),
    ("Unless the 5th lord is in the 5th, there will be no children.", "unless"),
    ("The 5th lord is never in the 5th for this native.", "never"),
    ("If the 5th lord is other than in the 5th house, results differ.", "other than"),
    ("If the 5th lord is not in the 2nd, wealth is denied.", "negated match"),
    # -- cross-sentence bridging (the old 200-char DOTALL window)
    ("The 5th lord governs children. Jupiter, the natural karaka for progeny, "
     "is in the 9th house.", "two sentences"),
    ("The 9th lord rules fortune. Saturn is placed in the 12th house.", "two sentences"),
    ("The 10th lord shapes career.\nMars sits in the 8th house.", "newline"),
    # -- disjunctive alternatives the old literal guard missed
    ("If the 5th lord is in the 9th, in the 5th, or in the 2nd, children.", "or-list"),
    ("If the 5th lord is in the 9th house or in the 2nd house, children.", "house or house"),
    ("If the 5th lord is in the 9th, the 5th, or the 2nd, children.", "the-list"),
    # -- a reference frame the ascendant-based map cannot adjudicate
    ("If the 4th lord is in the 7th from the Moon, the native travels.", "from Moon"),
    ("The 10th lord from the Moon in the 4th gives career change.", "from Moon"),
    ("In the navamsa, the 5th lord is in the 9th.", "navamsa"),
    ("In the D-10 chart, the 10th lord is in the 10th.", "D-10"),
    ("From the Arudha Lagna, the 7th lord is in the 5th.", "arudha"),
    ("When the 5th lord transits in the 9th house, children are born.", "transit"),
    # -- the named house belongs to another body, not the lord
    ("If the 5th lord is aspected by Jupiter in the 9th, the native has sons.", "aspect"),
    ("If the 5th lord is conjunct a planet placed in the 9th house, gains follow.", "conjunct"),
    ("In the Dasa of the 5th lord, if benefics are in the 9th house, gains accrue.", "dasha"),
    # -- compound conditions cannot be judged one half at a time
    ("If the 5th lord is in the 9th and the 6th lord is in the 6th, results follow.", "AND"),
    # -- bare digits are not house references
    ("The 5th lord, per verse 9, in the 2 charts examined, gives progeny.", "numerals"),
])
def test_review_regressions_are_never_judged(statement, why):
    rel, reason = SG.read_condition(statement)
    assert rel is None, f"{why}: wrongly read as {rel} -- {reason}"
    assert _gate([_c(statement)]).stats["claims_dropped"] == 0


@pytest.mark.parametrize("statement,expected", [
    ("If the 5th lord is in the 5th, the native will have progeny if related "
     "to a benefic.", SG.NOT_APPLICABLE),
    ("If the 5th lord is in the 6th, the native will obtain such sons who "
     "will be equal to his enemies.", SG.NOT_APPLICABLE),
    ("The native's health may be affected by phlegmatic disorders if the "
     "12th lord is in the ascendant.", SG.NOT_APPLICABLE),
    # "free from diseases" is CONSEQUENT language -- it must not read as a
    # negated antecedent, or the gate silences itself on ordinary prose.
    ("If the 6th lord is in the 6th house, the native will be free from "
     "diseases and enjoy happiness of conveyances.", SG.APPLICABLE),
    ("If the 5th lord is in the 2nd, the native will have many sons and "
     "wealth, be honorable.", SG.APPLICABLE),
    ("The 10th lord is in the 4th house.", SG.APPLICABLE),
])
def test_the_gate_still_judges_what_it_should(statement, expected):
    """The guards must not be so broad that nothing is ever judged. These
    six are the live 2026-09-05 claims the gate exists to sort."""
    assert _gate([_c(statement)]).verdicts[0].verdict == expected


def test_audit_shows_the_claim_reason_not_a_source_note():
    """Review defect: a DROP row printed the SOURCE's "chart satisfies ..."
    note as its rationale -- the exact opposite of the verdict, on the only
    screen a human reviews drops from."""
    payload = {"units": [], "segments": [
        {"segment_id": "ch30_s001", "kept": True,
         "text": "If the 2nd lord is in the 2nd the native gains wealth."}]}
    r = _gate([_c("If the 5th lord is in the 5th, the native will have progeny.",
                  ["ch30_s001"])], payload)
    out = SG.render_audit(r)
    assert "claim requires" in out
    assert "chart satisfies" not in out
