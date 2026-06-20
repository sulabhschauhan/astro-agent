"""Tests for agent/calculations/vargas/navamsa.py — P2.1 Navamsa (D9).

Layer A: structural / input-validation (no ephemeris).
Layer B: reference-chart parity against the 4 AstroSage PDFs (skipped --
    fixture extraction is deferred, see each test's skip message).
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
# Fixture population is deferred to next session (manual extraction from
# each chart's AstroSage Shodashvarga page, cross-checked against JHora --
# see playbook_export/reference/reference_charts.md for the natal data
# already on file for these 4 charts). Do not fabricate expected values here.

_REFERENCE_CHARTS = [
    {"name": "David", "source": "David's AstroSage PDF, Shodashvarga (D9) page"},
    {"name": "Sulabh", "source": "Sulabh's AstroSage PDF, Shodashvarga (D9) page"},
    {"name": "Surbhi", "source": "Surbhi's AstroSage PDF, Shodashvarga (D9) page"},
    {"name": "Sheridan", "source": "Sheridan's AstroSage PDF, Shodashvarga (D9) page"},
]


@pytest.mark.parametrize(
    "chart", _REFERENCE_CHARTS, ids=[c["name"] for c in _REFERENCE_CHARTS]
)
def test_navamsa_reference_chart_parity(chart):
    pytest.skip(f"Reference fixture pending manual extraction from {chart['source']}")


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
