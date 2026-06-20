"""Tests for agent/calculations/vargas/navamsa.py — P2.1 Navamsa (D9).

Layer A: structural / input-validation (no ephemeris).
Layer B: reference-chart parity against the 4 AstroSage PDFs (David, Sulabh,
    Surbhi, Sheridan -- all 4 active).
Layer C: internal consistency (real ephemeris, synthetic jd_ut).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # project root

import pytest
import swisseph as swe

from agent.calculations.vargas.navamsa import (
    NavamsaChart,
    NavamsaPlacement,
    _NAVAMSA_START_SIGN,
    _pada_index,
    compute_navamsa,
)
from agent.chart_calculator import calculate_chart

_CANONICAL_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


# ── Layer A: input validation (no ephemeris) ─────────────────────────────────

@pytest.mark.parametrize("jd_ut", [0.0, -1.0, -100.5])
def test_compute_navamsa_rejects_nonpositive_jd_ut(jd_ut):
    with pytest.raises(ValueError, match="jd_ut"):
        compute_navamsa(jd_ut, 45.0)


@pytest.mark.parametrize("asc_lon", [-0.001, 360.0, 400.0, -50.0])
def test_compute_navamsa_rejects_out_of_range_asc_lon(asc_lon):
    with pytest.raises(ValueError, match="asc_lon_sidereal"):
        compute_navamsa(2451545.0, asc_lon)


# ── Layer A: pada formula edge cases (no ephemeris) ──────────────────────────

@pytest.mark.parametrize("longitude,expected_pada", [
    (0.0, 0),                          # rasi start
    (3 + 19 / 60 + 59 / 3600, 0),      # 3d19'59" -- just under the 1st pada boundary
    (3 + 20 / 60, 1),                  # 3d20'00" -- exact 1st pada boundary
    (26 + 40 / 60, 8),                 # 26d40'00" -- exact 8th (last) pada boundary
    (29 + 59 / 60 + 59 / 3600, 8),     # 29d59'59" -- just under the next rasi
])
def test_pada_index_edge_cases(longitude, expected_pada):
    assert _pada_index(longitude) == expected_pada


# ── Layer A: starting-sign table (no ephemeris) ──────────────────────────────

def test_navamsa_start_sign_table_has_12_entries():
    assert len(_NAVAMSA_START_SIGN) == 12


def test_navamsa_start_sign_table_keys_and_values_are_canonical():
    assert set(_NAVAMSA_START_SIGN.keys()) == set(_CANONICAL_SIGNS)
    assert all(v in _CANONICAL_SIGNS for v in _NAVAMSA_START_SIGN.values())


@pytest.mark.parametrize("rasi,expected_start", [
    ("Aries", "Aries"),       # movable -- starts from itself
    ("Taurus", "Capricorn"),  # fixed -- starts from the 9th sign from itself
    ("Gemini", "Libra"),      # dual -- starts from the 5th sign from itself
])
def test_navamsa_start_sign_locked_values(rasi, expected_start):
    assert _NAVAMSA_START_SIGN[rasi] == expected_start


# ── Layer B: reference-chart parity (HARDEST CASE FIRST) ─────────────────────
#
# All 4 charts active: David (this session's hardest case -- boundary-prone
# London/BST chart, see CLAUDE.md), then Sulabh, Surbhi, Sheridan.

# Source: David_Kundli.pdf page 40, AstroSage Shodashvarga Bhav Table,
# Navamsha row (top row = sign, bottom row = house counted from D9 Lagna).
# Sign numbering 1=Aries..12=Pisces translated to _CANONICAL_SIGNS names.
_DAVID_EXPECTED_D9_LAGNA_SIGN = "Aquarius"
_DAVID_EXPECTED_PLACEMENTS = {
    "Sun":     {"d9_sign": "Aquarius",    "d9_house": 1},
    "Moon":    {"d9_sign": "Cancer",      "d9_house": 6},
    "Mars":    {"d9_sign": "Cancer",      "d9_house": 6},
    "Mercury": {"d9_sign": "Aries",       "d9_house": 3},
    "Jupiter": {"d9_sign": "Aquarius",    "d9_house": 1},
    "Venus":   {"d9_sign": "Pisces",      "d9_house": 2},
    "Saturn":  {"d9_sign": "Leo",         "d9_house": 7},
    "Rahu":    {"d9_sign": "Taurus",      "d9_house": 4},
    "Ketu":    {"d9_sign": "Scorpio",     "d9_house": 10},
}


def test_navamsa_reference_chart_parity_david():
    # Birth data shared with tests/test_chart_calculator.py and the
    # tests/manual/*_check.py scripts -- not redefined here.
    chart = calculate_chart("David", "19 Jan 1976", "22:00", "London, UK")
    nav = compute_navamsa(
        chart["meta"]["jd_ut"], chart["meta"]["asc_lon_sidereal"]
    )

    assert nav.d9_lagna_sign == _DAVID_EXPECTED_D9_LAGNA_SIGN

    for planet, expected in _DAVID_EXPECTED_PLACEMENTS.items():
        placement = nav.placements[planet]
        assert placement.d9_sign == expected["d9_sign"], (
            f"David {planet}: d9_sign {placement.d9_sign} vs "
            f"expected {expected['d9_sign']}"
        )
        assert placement.d9_house == expected["d9_house"], (
            f"David {planet}: d9_house {placement.d9_house} vs "
            f"expected {expected['d9_house']}"
        )


# Source: VedicReport5242026100151PM.pdf page 40, AstroSage Shodashvarga Bhav
# Table, Navamsha row (top row = sign, bottom row = house from D9 Lagna).
# ASC cross-check: reference_charts.md Chart 1 (Sulabh) records natal ayanamsha
# but omits a degree-level natal ASC -- only the sign-level "Ascendant:
# Sagittarius" is on file (data/default_user/kundali_summary.txt). Computed
# asc_lon_sidereal=262.6938 (Sagittarius 22d41'38") matches that sign;
# no AstroSage degree figure exists to diff against the +-57.77" Lahiri
# cross-implementation tolerance (see playbook_export/decisions/
# ayanamsa-investigation.md) for this chart specifically.
_SULABH_EXPECTED_D9_LAGNA_SIGN = "Libra"
_SULABH_EXPECTED_PLACEMENTS = {
    "Sun":     {"d9_sign": "Capricorn",   "d9_house": 4},
    "Moon":    {"d9_sign": "Cancer",      "d9_house": 10},
    "Mars":    {"d9_sign": "Aquarius",    "d9_house": 5},
    "Mercury": {"d9_sign": "Virgo",       "d9_house": 12},
    "Jupiter": {"d9_sign": "Cancer",      "d9_house": 10},
    "Venus":   {"d9_sign": "Pisces",      "d9_house": 6},
    "Saturn":  {"d9_sign": "Gemini",      "d9_house": 9},
    "Rahu":    {"d9_sign": "Gemini",      "d9_house": 9},
    "Ketu":    {"d9_sign": "Sagittarius", "d9_house": 3},
}


def test_navamsa_reference_chart_parity_sulabh():
    # Birth data shared with tests/test_chart_calculator.py and the
    # tests/manual/*_check.py scripts -- not redefined here.
    chart = calculate_chart("Sulabh", "6 April 1988", "00:30", "Calcutta, India")
    nav = compute_navamsa(
        chart["meta"]["jd_ut"], chart["meta"]["asc_lon_sidereal"]
    )

    assert nav.d9_lagna_sign == _SULABH_EXPECTED_D9_LAGNA_SIGN

    for planet, expected in _SULABH_EXPECTED_PLACEMENTS.items():
        placement = nav.placements[planet]
        assert placement.d9_sign == expected["d9_sign"], (
            f"Sulabh {planet}: d9_sign {placement.d9_sign} vs "
            f"expected {expected['d9_sign']}"
        )
        assert placement.d9_house == expected["d9_house"], (
            f"Sulabh {planet}: d9_house {placement.d9_house} vs "
            f"expected {expected['d9_house']}"
        )


# Source: Wife_VedicReport.pdf page 40, AstroSage Shodashvarga Bhav Table,
# Navamsha row (top row = sign, bottom row = house from D9 Lagna).
# ASC cross-check: reference_charts.md Chart 2 (Surbhi) -- AstroSage natal
# ASC = Libra 29-52-55 = 209.8819 sidereal. Computed asc_lon_sidereal=209.8932,
# diff 0.0113deg = 40.7" -- inside the documented +-57.77" Lahiri
# cross-implementation tolerance (playbook_export/decisions/
# ayanamsa-investigation.md).
_SURBHI_EXPECTED_D9_LAGNA_SIGN = "Gemini"
_SURBHI_EXPECTED_PLACEMENTS = {
    "Sun":     {"d9_sign": "Scorpio",     "d9_house": 6},
    "Moon":    {"d9_sign": "Aquarius",    "d9_house": 9},
    "Mars":    {"d9_sign": "Scorpio",     "d9_house": 6},
    "Mercury": {"d9_sign": "Libra",       "d9_house": 5},
    "Jupiter": {"d9_sign": "Sagittarius", "d9_house": 7},
    "Venus":   {"d9_sign": "Gemini",      "d9_house": 1},
    "Saturn":  {"d9_sign": "Gemini",      "d9_house": 1},
    "Rahu":    {"d9_sign": "Aries",       "d9_house": 11},
    "Ketu":    {"d9_sign": "Libra",       "d9_house": 5},
}


def test_navamsa_reference_chart_parity_surbhi():
    # Birth data shared with tests/test_chart_calculator.py and the
    # tests/manual/*_check.py scripts -- not redefined here.
    chart = calculate_chart("Surbhi", "11 Sep 1992", "10:30", "Patna, India")
    nav = compute_navamsa(
        chart["meta"]["jd_ut"], chart["meta"]["asc_lon_sidereal"]
    )

    assert nav.d9_lagna_sign == _SURBHI_EXPECTED_D9_LAGNA_SIGN

    for planet, expected in _SURBHI_EXPECTED_PLACEMENTS.items():
        placement = nav.placements[planet]
        assert placement.d9_sign == expected["d9_sign"], (
            f"Surbhi {planet}: d9_sign {placement.d9_sign} vs "
            f"expected {expected['d9_sign']}"
        )
        assert placement.d9_house == expected["d9_house"], (
            f"Surbhi {planet}: d9_house {placement.d9_house} vs "
            f"expected {expected['d9_house']}"
        )


# Source: Sheridan_Kundli.pdf page 40, AstroSage Shodashvarga Bhav Table,
# Navamsha row (top row = sign, bottom row = house from D9 Lagna).
# ASC cross-check: reference_charts.md Chart 3 (Sheridan) -- AstroSage natal
# ASC = Taurus 28-46-17 = 58.7714 sidereal. Computed asc_lon_sidereal=58.76,
# diff 0.0114deg = 41.0" -- inside the documented +-57.77" Lahiri
# cross-implementation tolerance (playbook_export/decisions/
# ayanamsa-investigation.md).
_SHERIDAN_EXPECTED_D9_LAGNA_SIGN = "Virgo"
_SHERIDAN_EXPECTED_PLACEMENTS = {
    "Sun":     {"d9_sign": "Aries",  "d9_house": 8},
    "Moon":    {"d9_sign": "Aries",  "d9_house": 8},
    "Mars":    {"d9_sign": "Aries",  "d9_house": 8},
    "Mercury": {"d9_sign": "Virgo",  "d9_house": 1},
    "Jupiter": {"d9_sign": "Virgo",  "d9_house": 1},
    "Venus":   {"d9_sign": "Pisces", "d9_house": 7},
    "Saturn":  {"d9_sign": "Pisces", "d9_house": 7},
    "Rahu":    {"d9_sign": "Aries",  "d9_house": 8},
    "Ketu":    {"d9_sign": "Libra",  "d9_house": 2},
}


def test_navamsa_reference_chart_parity_sheridan():
    # Birth data shared with tests/test_chart_calculator.py and the
    # tests/manual/*_check.py scripts -- not redefined here.
    chart = calculate_chart("Sheridan", "27 May 1984", "08:00", "Durban, South Africa")
    nav = compute_navamsa(
        chart["meta"]["jd_ut"], chart["meta"]["asc_lon_sidereal"]
    )

    assert nav.d9_lagna_sign == _SHERIDAN_EXPECTED_D9_LAGNA_SIGN

    for planet, expected in _SHERIDAN_EXPECTED_PLACEMENTS.items():
        placement = nav.placements[planet]
        assert placement.d9_sign == expected["d9_sign"], (
            f"Sheridan {planet}: d9_sign {placement.d9_sign} vs "
            f"expected {expected['d9_sign']}"
        )
        assert placement.d9_house == expected["d9_house"], (
            f"Sheridan {planet}: d9_house {placement.d9_house} vs "
            f"expected {expected['d9_house']}"
        )


# ── Layer C: internal consistency (real ephemeris, synthetic jd_ut) ─────────

def _synthetic_chart() -> NavamsaChart:
    jd_ut = swe.julday(2000, 1, 1, 12.0)
    return compute_navamsa(jd_ut, 45.5)


def test_compute_navamsa_all_nine_placements_present():
    chart = _synthetic_chart()
    expected_planets = {
        "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
    }
    assert set(chart.placements.keys()) == expected_planets
    assert all(isinstance(p, NavamsaPlacement) for p in chart.placements.values())


def test_compute_navamsa_placement_fields_in_range():
    chart = _synthetic_chart()
    assert 0 <= chart.d9_lagna_pada_index <= 8
    assert chart.d9_lagna_sign in _CANONICAL_SIGNS

    for placement in chart.placements.values():
        assert 0 <= placement.pada_index <= 8
        assert 1 <= placement.d9_house <= 12
        assert placement.d9_sign in _CANONICAL_SIGNS
        assert placement.d1_sign in _CANONICAL_SIGNS


def test_compute_navamsa_rahu_ketu_opposition_preserved_in_d1():
    chart = _synthetic_chart()
    rahu = chart.placements["Rahu"]
    ketu = chart.placements["Ketu"]
    assert abs(((ketu.d1_longitude - rahu.d1_longitude) % 360) - 180.0) < 1e-6
    assert rahu.retrograde is True
    assert ketu.retrograde is True


def test_compute_navamsa_vargottama_smoke():
    # Vargottama = D1 sign == D9 sign. No specific count asserted (depends
    # on the chosen jd_ut) -- this just confirms the comparison is always
    # computable without error for every placement.
    chart = _synthetic_chart()
    for placement in chart.placements.values():
        vargottama = placement.d1_sign == placement.d9_sign
        assert isinstance(vargottama, bool)
