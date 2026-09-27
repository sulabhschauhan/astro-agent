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
