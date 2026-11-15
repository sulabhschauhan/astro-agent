"""
tests/astro/test_timing_ranker.py
Unit tests for agent.astro.timing_ranker -- the deterministic convergence
ranker. Pure (no ephemeris): inputs are the REAL significators / transit
house-from-lagna / dasha windows for the Sulabh reference chart, transcribed
from a live pilot fact block, so the test validates the actual production case
without needing swisseph.

Covers: (1) the marriage ranking matches the desktop benchmark (Mercury-Rahu
top, Mercury-Mercury second) and is DERIVED, not tuned; (2) the ranker is
domain-neutral -- changing the target houses reorders the windows; (3) the
Saturn-return scope guard -- the milestone bonus fires only when natal Saturn
actually contacts a target house.
"""
from __future__ import annotations

from agent.astro import timing_ranker as tr

# Real computed KP significators for the Sulabh chart (engine output / oracle).
_SIG = {
    "Sun": (3, 7, 9), "Moon": (1, 3, 4, 8, 10), "Mars": (1, 3, 4, 11, 12),
    "Mercury": (2, 3, 7, 9, 12), "Jupiter": (1, 3, 4, 8), "Venus": (3, 5, 6, 10),
    "Saturn": (2, 8, 12), "Rahu": (1, 2, 3, 4, 12), "Ketu": (3, 8),
}
# (ad_lord, start, end, Saturn-house-from-lagna) from the real fact block.
_SAT_MD = [
    ("Saturn", "1 Aug 1989", "4 Aug 1992", 2), ("Mercury", "4 Aug 1992", "14 Apr 1995", 3),
    ("Ketu", "14 Apr 1995", "23 May 1996", 3), ("Venus", "23 May 1996", "24 Jul 1999", 4),
    ("Sun", "24 Jul 1999", "5 Jul 2000", 5), ("Moon", "5 Jul 2000", "3 Feb 2002", 6),
    ("Mars", "3 Feb 2002", "15 Mar 2003", 7), ("Rahu", "15 Mar 2003", "19 Jan 2006", 7),
    ("Jupiter", "19 Jan 2006", "1 Aug 2008", 8),
]
_MER_MD = [
    ("Mercury", "1 Aug 2008", "29 Dec 2010", 10), ("Ketu", "29 Dec 2010", "26 Dec 2011", 10),
    ("Venus", "26 Dec 2011", "26 Oct 2014", 11), ("Sun", "26 Oct 2014", "1 Sep 2015", 12),
    ("Moon", "1 Sep 2015", "31 Jan 2017", 12), ("Mars", "31 Jan 2017", "28 Jan 2018", 12),
    ("Rahu", "28 Jan 2018", "16 Aug 2020", 1), ("Jupiter", "16 Aug 2020", "22 Nov 2022", 2),
    ("Saturn", "22 Nov 2022", "1 Aug 2025", 3),
]
_NATAL_SATURN_HOUSE = 1  # Sulabh: Saturn in the 1st (Sagittarius/Lagna)


def _tree():
    def node(md_lord, ads):
        return {"mahadasha": {"lord": md_lord}, "phase": "past",
                "antardashas": [{"lord": l, "start": s, "end": e} for l, s, e, _ in ads]}
    return [node("Saturn", _SAT_MD), node("Mercury", _MER_MD)]


def _periods():
    p = {}
    for md in (_SAT_MD, _MER_MD):
        for l, s, _e, hl in md:
            p[f"{l}|{s}"] = {"saturn_house_from_lagna": hl}
    return p


def _rank(target, natal=_NATAL_SATURN_HOUSE):
    return tr.rank_windows(_tree(), _SIG, _periods(), target, natal)


def test_marriage_top_window_is_mercury_rahu():
    w = _rank({2, 7, 11})
    top = w[0]
    assert (top["md_lord"], top["ad_lord"], top["start"]) == ("Mercury", "Rahu", "28 Jan 2018")
    assert top["is_saturn_return"] is True
    assert top["sig_hits"] == [2] and top["transit_hits"] == [7]


def test_marriage_second_is_mercury_mercury_below_rahu():
    w = _rank({2, 7, 11})
    second = w[1]
    assert (second["md_lord"], second["ad_lord"]) == ("Mercury", "Mercury")
    assert second["is_saturn_return"] is False
    assert w[0]["score"] > second["score"]           # the return breaks the tie


def test_venus_never_tops_marriage():
    # The naive karaka pick signifies none of {2,7,11}; it must not lead.
    w = _rank({2, 7, 11})
    assert not (w[0]["ad_lord"] == "Venus")
    venus = [x for x in w if x["ad_lord"] == "Venus"]
    assert all(x["sig_hits"] == [] for x in venus)     # only transit could place it, weakly


def test_ranker_is_domain_neutral():
    # Same machinery, different targets -> different rankings (career surfaces
    # Venus windows that marriage does not).
    marriage = [(x["md_lord"], x["ad_lord"]) for x in _rank({2, 7, 11})]
    career = [(x["md_lord"], x["ad_lord"]) for x in _rank({2, 6, 10, 11})]
    assert marriage != career
    career_venus = [x for x in _rank({2, 6, 10, 11}) if x["ad_lord"] == "Venus"]
    assert any(x["sig_hits"] for x in career_venus)    # Venus signifies 6,10 -> real for career


def test_saturn_return_scope_guard():
    # If natal Saturn sat in a house whose contacts miss the target set, the
    # return bonus must NOT fire even when Saturn transits that house.
    # Natal Saturn in house 5 contacts {5,7,11,2}; against target {6,10} -> no contact.
    w = tr.rank_windows(_tree(), _SIG, _periods(), {6, 10}, natal_saturn_house=5)
    assert all(x["is_saturn_return"] is False for x in w)


def test_no_signal_windows_are_dropped():
    # A target no lord signifies and no transit contacts yields an empty ranking.
    assert _rank({8}) == [] or all(x["score"] > 0 for x in _rank({8}))


def test_jupiter_contact_geometry():
    # Jupiter at house 1 casts 5th/7th/9th aspects -> houses {1,5,7,9}.
    assert tr._jupiter_contact_houses(1) == {1, 5, 7, 9}


def test_jupiter_transit_adds_activation():
    # Jupiter transiting house 1 (Sagittarius) aspects the 7th (Gemini) -- the
    # marriage/children benefic contact the Saturn-only view was blind to. Adding
    # it must raise exactly that window's score by W_JUP, not reorder unrelated ones.
    base = {f"{w['ad_lord']}|{w['start']}": w["score"] for w in _rank({2, 7, 11})}
    periods = _periods()
    periods["Jupiter|16 Aug 2020"]["jupiter_house_from_lagna"] = 1
    boosted = {f"{w['ad_lord']}|{w['start']}": w
               for w in tr.rank_windows(_tree(), _SIG, periods, {2, 7, 11}, _NATAL_SATURN_HOUSE)}
    mj = boosted["Jupiter|16 Aug 2020"]
    assert mj["jupiter_hits"] == [7]
    assert mj["score"] == base["Jupiter|16 Aug 2020"] + tr.W_JUP


# --- S145: role-weighted targets -----------------------------------------------
from agent.astro import house_roles as hr


def _key(w):
    return f"{w['md_lord']}-{w['ad_lord']}|{w['start']}"


def test_weighted_all_ones_equals_set_path():
    # A weight dict of all 1.0 must score byte-identically to the set path.
    from_set = _rank({2, 7, 11})
    from_dict = tr.rank_windows(_tree(), _SIG, _periods(), {2: 1.0, 7: 1.0, 11: 1.0},
                                _NATAL_SATURN_HOUSE)
    assert [(_key(a), a["score"]) for a in from_set] == [(_key(b), b["score"]) for b in from_dict]


def test_marriage_role_weighted_top_still_mercury_rahu_same_score():
    # The whole point: zeroing the 8th must NOT disturb the validated #1 window.
    flat = _rank({2, 7, 8, 11})            # planner's raw emission (8 included)
    weights = hr.weighted_targets(["marriage"], [2, 7, 8, 11])
    weighted = tr.rank_windows(_tree(), _SIG, _periods(), weights, _NATAL_SATURN_HOUSE)
    top = weighted[0]
    assert (top["md_lord"], top["ad_lord"], top["start"]) == ("Mercury", "Rahu", "28 Jan 2018")
    assert top["is_saturn_return"] is True
    # Mercury-Rahu scores only on promotion houses (2 sig, 7 transit) + return,
    # so its score is unchanged whether or not the 8th is zeroed.
    flat_top = next(w for w in flat if _key(w) == _key(top))
    assert top["score"] == flat_top["score"]


def test_role_weighting_strips_eighth_house_credit():
    # Windows whose ONLY significator hit was the 8th lose that credit.
    flat = {_key(w): w for w in _rank({2, 7, 8, 11})}
    weights = hr.weighted_targets(["marriage"], [2, 7, 8, 11])
    weighted = {_key(w): w for w in
                tr.rank_windows(_tree(), _SIG, _periods(), weights, _NATAL_SATURN_HOUSE)}
    # Mercury-Ketu (Ketu signifies 3,8): under flat the 8 counted; weighted it must not.
    k = "Mercury-Ketu|29 Dec 2010"
    assert 8 in [h for h in (3, 8) if h in (2, 7, 8, 11)]  # sanity: 8 is a flat target
    assert flat[k]["sig_hits"] == [8]                      # flat rewarded the 8th
    assert weighted[k]["sig_hits"] == []                   # weighted strips it
    assert weighted[k]["score"] < flat[k]["score"]         # score genuinely dropped


def test_weighting_never_raises_a_window_score():
    # Monotonicity: no window can score HIGHER once obstacle houses are zeroed.
    flat = {_key(w): w for w in _rank({2, 7, 8, 11})}
    weights = hr.weighted_targets(["marriage"], [2, 7, 8, 11])
    weighted = {_key(w): w for w in
                tr.rank_windows(_tree(), _SIG, _periods(), weights, _NATAL_SATURN_HOUSE)}
    for k, w in weighted.items():
        assert w["score"] <= flat[k]["score"], k


def test_build_timing_ranking_reports_only_positive_houses():
    # The fact block must advertise houses 2,7,11 -- not the zeroed 8 the planner emitted.
    facts = {
        "dasha_periods": {"mahadasha_tree": _tree()},
        "kp_planet_significations": {"planet_significations": {k: list(v) for k, v in _SIG.items()}},
        "transits": {"periods": _periods()},
        "planet_positions": {"Saturn": {"house": _NATAL_SATURN_HOUSE}},
    }
    weights = hr.weighted_targets(["marriage"], [2, 7, 8, 11])
    ranking = tr.build_timing_ranking(facts, weights)
    assert ranking["target_houses"] == [2, 7, 11]
    assert ranking["windows"][0]["ad_lord"] == "Rahu"


# --- S158: five-year lead window ------------------------------------------------
import datetime as _dt_t


def _syn_facts(periods_extra=None, ads=None):
    """A controlled synthetic chart: one MD 'M' whose lord and three AD lords all
    signify house 7, so every window scores 1.5 (1 significator + 0.5 MD). C also
    gets a Saturn transit contacting 7 (+1 -> 2.5), making it the lifetime peak.
    Saturn natal house is None, so the return bonus is disabled."""
    sig = {"M": [7], "A": [7], "B": [7], "C": [7]}
    ads = ads if ads is not None else [
        {"lord": "A", "start": "1 Jan 2020", "end": "1 Jan 2022"},   # past of 2027
        {"lord": "B", "start": "1 Jan 2028", "end": "1 Jan 2030"},   # in 2027+5y
        {"lord": "C", "start": "1 Jan 2040", "end": "1 Jan 2043"},   # far future
    ]
    tree = [{"mahadasha": {"lord": "M"}, "phase": "future", "antardashas": ads}]
    periods = {"C|1 Jan 2040": {"saturn_house_from_lagna": 7}}
    periods.update(periods_extra or {})
    return {
        "dasha_periods": {"mahadasha_tree": tree},
        "kp_planet_significations": {"planet_significations": sig},
        "transits": {"periods": periods},
        "planet_positions": {"Saturn": {"house": None}},  # disable return bonus
    }


def test_five_year_window_leads_and_differs_from_lifetime_peak():
    r = tr.build_timing_ranking(_syn_facts(), {7}, as_of=_dt_t.date(2027, 1, 1))
    assert r["five_year_window"]["ad_lord"] == "B"      # only window in [2027, 2032]
    assert r["lifetime_peak"]["ad_lord"] == "C"         # higher score, but far off
    assert r["five_year_window"]["score"] < r["lifetime_peak"]["score"]


def test_five_year_equals_lifetime_when_peak_is_near():
    r = tr.build_timing_ranking(_syn_facts(), {7}, as_of=_dt_t.date(2039, 1, 1))
    # C (2040-2043) now falls inside the five-year horizon and is also the peak.
    assert r["five_year_window"]["ad_lord"] == "C"
    assert (r["five_year_window"]["md_lord"], r["five_year_window"]["start"]) == \
           (r["lifetime_peak"]["md_lord"], r["lifetime_peak"]["start"])


def test_five_year_window_none_when_nothing_in_horizon():
    r = tr.build_timing_ranking(_syn_facts(), {7}, as_of=_dt_t.date(2044, 1, 1))
    assert r["five_year_window"] is None               # all windows end by 2043
    assert r["lifetime_peak"]["ad_lord"] == "C"        # peak still surfaced


def test_five_year_tie_breaks_to_chronologically_earlier_not_lexical():
    # Two in-horizon windows, equal score, dates where STRING order ("10 Jan" <
    # "9 Jan") disagrees with CHRONOLOGICAL order (9 Jan < 10 Jan). The pick must
    # be chronological.
    ads = [
        {"lord": "A", "start": "10 Jan 2028", "end": "1 Jan 2029"},
        {"lord": "B", "start": "9 Jan 2028", "end": "1 Jan 2029"},
    ]
    r = tr.build_timing_ranking(_syn_facts(periods_extra={}, ads=ads), {7},
                                as_of=_dt_t.date(2027, 1, 1))
    assert r["five_year_window"]["start"] == "9 Jan 2028"


def test_parse_and_overlap_helpers_fail_soft():
    assert tr._parse_window_date("28 Jan 2018") == _dt_t.date(2018, 1, 28)
    assert tr._parse_window_date("garbage") is None
    assert tr._parse_window_date(None) is None
    as_of, horizon = _dt_t.date(2027, 1, 1), _dt_t.date(2032, 1, 1)
    # unparseable start -> ineligible; parseable start + open-ended (bad) end -> eligible
    assert tr._overlaps_horizon({"start": "???", "end": "1 Jan 2030"}, as_of, horizon) is False
    assert tr._overlaps_horizon({"start": "1 Jan 2028", "end": "???"}, as_of, horizon) is True


# --- T1: equal-score ties are shown in full, not collapsed to one --------------


def test_five_year_windows_returns_all_tied_top():
    # Two in-horizon windows tie at the top score (both 1.5: one significator +
    # MD support, no transit). Both must be returned, chronological; the singular
    # key stays the earliest for back-compat.
    ads = [
        {"lord": "A", "start": "1 Jan 2028", "end": "1 Jan 2029"},
        {"lord": "B", "start": "1 Jan 2029", "end": "1 Jan 2030"},
    ]
    r = tr.build_timing_ranking(_syn_facts(ads=ads), {7}, as_of=_dt_t.date(2027, 1, 1))
    fw = r["five_year_windows"]
    assert [w["ad_lord"] for w in fw] == ["A", "B"]      # both tied, chronological
    assert fw[0]["score"] == fw[1]["score"] == 1.5
    assert r["five_year_window"]["ad_lord"] == "A"       # singular = earliest (back-compat)


def test_lifetime_peaks_returns_all_tied_top():
    # Two windows tie at the lifetime-top score (each 2.5: significator + MD +
    # Saturn transit). Both returned; singular key = earliest.
    ads = [
        {"lord": "A", "start": "1 Jan 2020", "end": "1 Jan 2022"},
        {"lord": "B", "start": "1 Jan 2024", "end": "1 Jan 2026"},
    ]
    extra = {"A|1 Jan 2020": {"saturn_house_from_lagna": 7},
             "B|1 Jan 2024": {"saturn_house_from_lagna": 7}}
    r = tr.build_timing_ranking(_syn_facts(periods_extra=extra, ads=ads), {7},
                                as_of=_dt_t.date(2030, 1, 1))
    lp = r["lifetime_peaks"]
    assert [w["ad_lord"] for w in lp] == ["A", "B"]
    assert lp[0]["score"] == lp[1]["score"] == 2.5
    assert r["lifetime_peak"]["ad_lord"] == "A"          # earliest (back-compat)


def test_peak_windows_first_equals_peak_window_singular():
    # Contract that keeps the singular keys byte-identical: _peak_windows(c)[0]
    # is exactly what _peak_window(c) returned.
    cands = [
        {"ad_lord": "X", "start": "9 Jan 2028", "score": 2.0},
        {"ad_lord": "Y", "start": "10 Jan 2028", "score": 2.0},
        {"ad_lord": "Z", "start": "1 Jan 2030", "score": 1.0},
    ]
    assert tr._peak_windows(cands)[0] == tr._peak_window(cands)
    assert [w["ad_lord"] for w in tr._peak_windows(cands)] == ["X", "Y"]  # chrono, tie only
    assert tr._peak_windows([]) == []


def test_render_flags_five_year_tie_and_names_all():
    ads = [
        {"lord": "A", "start": "1 Jan 2028", "end": "1 Jan 2029"},
        {"lord": "B", "start": "1 Jan 2029", "end": "1 Jan 2030"},
    ]
    r = tr.build_timing_ranking(_syn_facts(ads=ads), {7}, as_of=_dt_t.date(2027, 1, 1))
    txt = tr.render_ranking(r)
    assert "2 windows TIE at the top score" in txt
    assert "EQUALLY ranked" in txt
    # both tied windows named in the lead block as bullet items
    assert txt.count("      * ") >= 2


def test_render_single_window_keeps_single_lead():
    # Default synthetic: only B is in horizon -> one window, no tie language.
    r = tr.build_timing_ranking(_syn_facts(), {7}, as_of=_dt_t.date(2027, 1, 1))
    txt = tr.render_ranking(r)
    assert "LEAD with the NEXT-FIVE-YEARS window" in txt
    assert "windows TIE at the top score" not in txt


# --- S161: KP-hierarchy significator weighting ---------------------------------


def test_sig_weight_tier_ladder():
    assert tr._sig_weight({7: 1}, 7) == 1.0      # star-of-occupant (strongest)
    assert tr._sig_weight({7: 2}, 7) == 0.75     # occupant
    assert tr._sig_weight({7: 3}, 7) == 0.5      # star-of-owner
    assert tr._sig_weight({7: 4}, 7) == 0.25     # owner (weakest)
    assert tr._sig_weight({7: None}, 7) == 0.25  # node agency: floored at weakest
    assert tr._sig_weight({7: 1}, 9) == 1.0      # house absent -> flat
    assert tr._sig_weight({}, 7) == 1.0          # empty map -> flat
    assert tr._sig_weight(None, 7) == 1.0        # no map -> flat (byte-identical)


def _two_lord_tree():
    return [{"mahadasha": {"lord": "M"}, "phase": "x", "antardashas": [
        {"lord": "A", "start": "1 Jan 2020", "end": "1 Jan 2021"},
        {"lord": "B", "start": "1 Jan 2021", "end": "1 Jan 2022"}]}]


def test_absent_tiers_is_byte_identical_to_flat():
    sig = {"A": (7,), "B": (7,)}
    w = tr.rank_windows(_two_lord_tree(), sig, {}, {7}, None)   # no signator_tiers
    assert {x["ad_lord"]: x["score"] for x in w} == {"A": 1.0, "B": 1.0}


def test_tier_weighting_discriminates_equal_house_count():
    # A signifies 7 as star-of-occupant (tier 1), B as owner (tier 4). Flat buries
    # them in a 1.0 == 1.0 tie; tiered, A must outrank B.
    sig = {"A": (7,), "B": (7,)}
    tiers = {"A": {7: 1}, "B": {7: 4}}
    w = tr.rank_windows(_two_lord_tree(), sig, {}, {7}, None, signator_tiers=tiers)
    sc = {x["ad_lord"]: x["score"] for x in w}
    assert sc["A"] == 1.0 and sc["B"] == 0.25
    assert w[0]["ad_lord"] == "A"
    # the reported hits do not change -- tier only moves the score, never the output
    assert all(x["sig_hits"] == [7] for x in w)


def test_mixed_tier_houses_sum_correctly():
    # One lord signifies 6 (occupant, 0.75) and 10 (owner, 0.25) -> 1.0 tiered,
    # vs 2.0 flat. Demonstrates a strong-looking flat score shrinking to its real
    # KP weight.
    tree = [{"mahadasha": {"lord": "M"}, "phase": "x", "antardashas": [
        {"lord": "V", "start": "1 Jan 2020", "end": "1 Jan 2021"}]}]
    sig = {"V": (6, 10)}
    tiered = tr.rank_windows(tree, sig, {}, {6, 10}, None,
                             signator_tiers={"V": {6: 2, 10: 4}})
    flat = tr.rank_windows(tree, sig, {}, {6, 10}, None)
    assert tiered[0]["score"] == 0.75 + 0.25
    assert flat[0]["score"] == 2.0


def test_build_timing_ranking_reads_tiers_key():
    facts = {
        "dasha_periods": {"mahadasha_tree": _two_lord_tree()},
        "kp_planet_significations": {
            "planet_significations": {"A": [7], "B": [7]},
            "planet_signification_tiers": {"A": {7: 1}, "B": {7: 4}}},
        "transits": {"periods": {}},
        "planet_positions": {"Saturn": {"house": None}},
    }
    r = tr.build_timing_ranking(facts, {7}, as_of=_dt_t.date(2019, 1, 1))
    sc = {w["ad_lord"]: w["score"] for w in r["windows"]}
    assert sc["A"] == 1.0 and sc["B"] == 0.25
    # Same facts WITHOUT the tiers key -> flat (back-compat for an older fact block).
    facts["kp_planet_significations"] = {"planet_significations": {"A": [7], "B": [7]}}
    r2 = tr.build_timing_ranking(facts, {7}, as_of=_dt_t.date(2019, 1, 1))
    sc2 = {w["ad_lord"]: w["score"] for w in r2["windows"]}
    assert sc2["A"] == sc2["B"] == 1.0
