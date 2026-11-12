"""Unit tests for agent.astro.tz_display (Part A, S159).

Pure logic -- no ephemeris. The four handover cases plus cache-safety and the
muhurta/ingress/combustion-only scope. timezonefinder + tzdata are project
dependencies on the run machine; the birthplace test needs them.
"""
from __future__ import annotations

import copy

from agent.astro import tz_display as tz


def test_instant_rolls_to_next_day_in_dubai_same_day_in_la():
    s = "2027-06-02 23:58 UT"
    assert tz.localize_ut(s, "Asia/Dubai") == "2027-06-03 03:58 (Asia/Dubai)"   # +04 -> next day
    la = tz.localize_ut(s, "America/Los_Angeles")
    assert la.startswith("2027-06-02")                                          # -07 (PDT) -> same day
    assert la.endswith("(America/Los_Angeles)")


def test_window_across_dst_converts_each_end_on_its_own_offset():
    # US spring-forward: 2027-03-14 02:00 local. Two UT instants straddling it in
    # America/New_York: 06:00 UT = 01:00 EST (UTC-5); 08:00 UT = 04:00 EDT (UTC-4).
    assert tz.localize_ut("2027-03-14 06:00 UT", "America/New_York") == \
        "2027-03-14 01:00 (America/New_York)"
    assert tz.localize_ut("2027-03-14 08:00 UT", "America/New_York") == \
        "2027-03-14 04:00 (America/New_York)"   # DST applied on the later instant


def test_no_zone_falls_back_to_birthplace_labelled():
    # No browser zone -> birthplace zone from Kolkata coords -> Asia/Kolkata (+05:30).
    zone = tz.resolve_display_zone(None, 22.5667, 88.35)
    assert zone == "Asia/Kolkata"
    assert tz.localize_ut("2027-06-02 23:58 UT", zone) == "2027-06-03 05:28 (Asia/Kolkata)"


def test_invalid_browser_zone_falls_back_then_ut_last_resort():
    assert tz.resolve_display_zone("Not/AZone", 22.5667, 88.35) == "Asia/Kolkata"
    assert tz.resolve_display_zone("Not/AZone", None, None) == "UT"
    assert tz.resolve_display_zone(None, None, None) == "UT"


def test_localize_dated_facts_copies_and_scopes_to_the_three_classes():
    facts = {
        "muhurta": {"searched": {"start": "2026-11-25 15:06 UT"},
                    "best": {"start": "2026-11-25 15:06 UT", "end": "2026-11-26 01:41 UT"}},
        "ingress": {"events": [{"date": "2027-06-02 23:58 UT", "to_sign": "Aries"}]},
        "combustion": {"windows": [{"start": "2027-01-01 00:00 UT"}]},
        "masa": {"current": {"start": "2026-11-10 12:00 UT"}},   # must stay UT (S148 lock)
        "dasha_periods": {"x": "2026-11-10 12:00 UT"},           # must stay UT (ruling)
    }
    original = copy.deepcopy(facts)
    out = tz.localize_dated_facts(facts, "Asia/Dubai")

    assert facts == original, "the input (a possible cache object) must not be mutated"
    assert out["muhurta"]["best"]["start"] == "2026-11-25 19:06 (Asia/Dubai)"
    assert out["muhurta"]["best"]["end"] == "2026-11-26 05:41 (Asia/Dubai)"
    assert out["ingress"]["events"][0]["date"] == "2027-06-03 03:58 (Asia/Dubai)"
    assert out["ingress"]["events"][0]["to_sign"] == "Aries"   # non-date fields untouched
    assert out["combustion"]["windows"][0]["start"].endswith("(Asia/Dubai)")
    # masa + dasha are OUT of scope -> still UT
    assert out["masa"]["current"]["start"] == "2026-11-10 12:00 UT"
    assert out["dasha_periods"]["x"] == "2026-11-10 12:00 UT"


def test_ut_zone_is_a_noop_same_object():
    facts = {"muhurta": {"best": {"start": "2026-11-25 15:06 UT"}}}
    assert tz.localize_dated_facts(facts, "UT") is facts     # byte-identical, no copy
    assert tz.localize_dated_facts(facts, "") is facts
