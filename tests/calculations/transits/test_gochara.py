"""Tests for agent/calculations/transits/gochara.py — P2.2.1 Gochara (transit
snapshot).

Layer B: reference-chart parity against AstroSage's "Transit today" report,
dated 2026-06-20, for Surbhi and Sheridan. Locked design decisions (Mean
Node, dual house-reference, ayanamsa, 9-body scope) live in
agent/calculations/transits/gochara.py's module docstring -- not duplicated
here.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # project root

import swisseph as swe

from agent.calculations.transits.gochara import compute_gochara
from agent.chart_calculator import _calc_planets, calculate_chart

# Canonical transit fixture moment: 2026-06-20 18:30 UTC (= 00:00 IST
# 2026-06-21, the IST midnight rollover at end of June 20 IST-day).
#
# ANCHOR CONVENTION -- UNRESOLVED:
# Session 21 diagnostic on 2026-06-20 found this is the only anchor in
# {12:00 UTC, 18:30 UTC, 18:29 UTC, 06:30 UTC, 00:00 UTC} where all 9
# transit planets simultaneously match AstroSage's "Today's Transit" output
# for this date. However, Mars crosses the Aries-Taurus boundary within
# ~60 seconds of IST midnight that day, so the margin is sub-arcsecond on
# the binding planet -- a strong lead, not a proven rule. AstroSage's
# actual snapshot convention (end-of-IST-day vs current query moment vs
# other) has NOT been corroborated on a second date where boundaries are
# not razor-thin. Treat the 18:30 UTC anchor as provisional until a
# second-date validation comes in.
#
# Implication for production: calculation layer is anchor-agnostic (takes
# JD as input). Anchor convention is an answer-pipeline (P7) concern, not
# a calculation concern. Whatever rule AstroSage uses, downstream code
# will pass the matching JD.
_JD_UT_20260620_1830_UTC = swe.julday(2026, 6, 20, 18.5)


def _natal_lons(name: str, dob: str, tob: str, place: str) -> tuple[float, float]:
    """Resolve (natal_asc_lon, natal_moon_lon) for a canonical reference
    chart. calculate_chart()'s public dict exposes sign/house but not raw
    longitude, so natal Moon's longitude is pulled the same way the
    pre-existing manual scripts do (tests/manual/dasha_timezone_check.py):
    via chart_calculator._calc_planets, fed the chart's own (jd_ut, asc_lon)
    -- no second geocode/timezone resolution, no birth-data redefinition.
    """
    chart = calculate_chart(name, dob, tob, place)
    jd_ut = chart["meta"]["jd_ut"]
    asc_lon = chart["meta"]["asc_lon_sidereal"]
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    natal_planets = _calc_planets(jd_ut, asc_lon)
    return asc_lon, natal_planets["Moon"]["longitude"]


# Source: AstroSage "Transit today" report dated 2026-06-20, accessed Session
# 21. Surbhi's report text is the canonical citation for both charts below --
# the global transit positions at 2026-06-20 18:30 UTC (see
# _JD_UT_20260620_1830_UTC's ANCHOR CONVENTION note above -- anchor is
# provisional) are the same for every natal frame; only the house mappings
# differ per chart. Quoted verbatim: "Sun is transiting through Gemini,
# Moon through Leo, Mars through Taurus, Mercury through Gemini, Jupiter
# through Cancer, Venus through Cancer, Saturn through Pisces, Rahu through
# Aquarius, Ketu through Leo."
_SURBHI_EXPECTED = {
    "Sun":     {"sign": 3,  "house_from_lagna": 9,  "house_from_moon": 5},
    "Moon":    {"sign": 5,  "house_from_lagna": 11, "house_from_moon": 7},
    "Mars":    {"sign": 2,  "house_from_lagna": 8,  "house_from_moon": 4},
    "Mercury": {"sign": 3,  "house_from_lagna": 9,  "house_from_moon": 5},
    "Jupiter": {"sign": 4,  "house_from_lagna": 10, "house_from_moon": 6},
    "Venus":   {"sign": 4,  "house_from_lagna": 10, "house_from_moon": 6},
    "Saturn":  {"sign": 12, "house_from_lagna": 6,  "house_from_moon": 2},
    "Rahu":    {"sign": 11, "house_from_lagna": 5,  "house_from_moon": 1},
    "Ketu":    {"sign": 5,  "house_from_lagna": 11, "house_from_moon": 7},
}


def test_gochara_reference_chart_parity_surbhi():
    # Birth data shared with tests/test_chart_calculator.py and the
    # tests/manual/*_check.py scripts -- not redefined here.
    natal_asc_lon, natal_moon_lon = _natal_lons(
        "Surbhi", "11 Sep 1992", "10:30", "Patna, India"
    )
    snapshot = compute_gochara(_JD_UT_20260620_1830_UTC, natal_asc_lon, natal_moon_lon)

    placements = {p.planet_name: p for p in snapshot.placements}
    assert set(placements) == set(_SURBHI_EXPECTED)

    for planet, expected in _SURBHI_EXPECTED.items():
        p = placements[planet]
        assert p.sign == expected["sign"], (
            f"Surbhi {planet}: sign {p.sign} vs expected {expected['sign']}"
        )
        assert p.house_from_lagna == expected["house_from_lagna"], (
            f"Surbhi {planet}: house_from_lagna {p.house_from_lagna} vs "
            f"expected {expected['house_from_lagna']}"
        )
        assert p.house_from_moon == expected["house_from_moon"], (
            f"Surbhi {planet}: house_from_moon {p.house_from_moon} vs "
            f"expected {expected['house_from_moon']}"
        )
        assert 1 <= p.nakshatra <= 27

    assert placements["Rahu"].is_retrograde is True
    assert placements["Ketu"].is_retrograde is True


# ─── Retrograde-flag regression guard (Session 52) ──────────────────────────
#
# gochara.py's migration to helpers/ephemeris.sidereal_position() (Session
# 52) incidentally fixed a dormant bug: the module's own flags previously
# omitted FLG_SPEED, so is_retrograde was always False for the 7 non-node
# grahas (same bug class as chart_calculator.py's Session 51 FLG_SPEED fix).
# No existing test asserted the corrected behavior (only Rahu/Ketu's
# hardcoded-True was covered above) -- these two tests pin it against
# silent regression.

def test_gochara_mercury_retrograde_at_david_jd():
    """David's natal JD is the corpus's known real-chart Mercury-retrograde
    moment (test_combustion.py Layer A oracle row ("david", "mercury"):
    retro=True; test_ephemeris.py's david_jd fixture derives the same JD
    the same way) -- reused here rather than inventing a new date."""
    natal_asc_lon, natal_moon_lon = _natal_lons(
        "David", "19 Jan 1976", "22:00", "London, UK"
    )
    chart = calculate_chart("David", "19 Jan 1976", "22:00", "London, UK")
    david_jd = chart["meta"]["jd_ut"]

    snapshot = compute_gochara(david_jd, natal_asc_lon, natal_moon_lon)
    placements = {p.planet_name: p for p in snapshot.placements}

    assert placements["Mercury"].is_retrograde is True


def test_gochara_sun_not_retrograde_at_sulabh_jd():
    """Companion guard at Sulabh's natal JD (derived via calculate_chart(),
    same pattern as test_ephemeris.py's sulabh_jd fixture): Sun never
    retrogrades, so this catches the inverse failure mode (a speed-sign
    misread that flips everything to True instead of leaving everything
    False)."""
    natal_asc_lon, natal_moon_lon = _natal_lons(
        "Sulabh", "6 Apr 1988", "00:30", "Calcutta, India"
    )
    chart = calculate_chart("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")
    sulabh_jd = chart["meta"]["jd_ut"]

    snapshot = compute_gochara(sulabh_jd, natal_asc_lon, natal_moon_lon)
    placements = {p.planet_name: p for p in snapshot.placements}

    assert placements["Sun"].is_retrograde is False


# Source: AstroSage "Transit today" report dated 2026-06-20, accessed Session
# 21 (see Surbhi's citation above for the quoted report text -- the global
# transit positions at 2026-06-20 18:30 UTC are identical for every natal
# frame; only the house mappings differ per chart). Anchor uncertainty
# documented at _JD_UT_20260620_1830_UTC's ANCHOR CONVENTION note above --
# treat as provisional until corroborated on a second date.
_SHERIDAN_EXPECTED = {
    "Sun":     {"sign": 3,  "house_from_lagna": 2,  "house_from_moon": 3},
    "Moon":    {"sign": 5,  "house_from_lagna": 4,  "house_from_moon": 5},
    "Mars":    {"sign": 2,  "house_from_lagna": 1,  "house_from_moon": 2},
    "Mercury": {"sign": 3,  "house_from_lagna": 2,  "house_from_moon": 3},
    "Jupiter": {"sign": 4,  "house_from_lagna": 3,  "house_from_moon": 4},
    "Venus":   {"sign": 4,  "house_from_lagna": 3,  "house_from_moon": 4},
    "Saturn":  {"sign": 12, "house_from_lagna": 11, "house_from_moon": 12},
    "Rahu":    {"sign": 11, "house_from_lagna": 10, "house_from_moon": 11},
    "Ketu":    {"sign": 5,  "house_from_lagna": 4,  "house_from_moon": 5},
}


def test_gochara_reference_chart_parity_sheridan():
    # Birth data shared with tests/test_chart_calculator.py and the
    # tests/manual/*_check.py scripts -- not redefined here.
    natal_asc_lon, natal_moon_lon = _natal_lons(
        "Sheridan", "27 May 1984", "08:00", "Durban, South Africa"
    )
    snapshot = compute_gochara(_JD_UT_20260620_1830_UTC, natal_asc_lon, natal_moon_lon)

    placements = {p.planet_name: p for p in snapshot.placements}
    assert set(placements) == set(_SHERIDAN_EXPECTED)

    for planet, expected in _SHERIDAN_EXPECTED.items():
        p = placements[planet]
        assert p.sign == expected["sign"], (
            f"Sheridan {planet}: sign {p.sign} vs expected {expected['sign']}"
        )
        assert p.house_from_lagna == expected["house_from_lagna"], (
            f"Sheridan {planet}: house_from_lagna {p.house_from_lagna} vs "
            f"expected {expected['house_from_lagna']}"
        )
        assert p.house_from_moon == expected["house_from_moon"], (
            f"Sheridan {planet}: house_from_moon {p.house_from_moon} vs "
            f"expected {expected['house_from_moon']}"
        )
        assert 1 <= p.nakshatra <= 27

    assert placements["Rahu"].is_retrograde is True
    assert placements["Ketu"].is_retrograde is True
