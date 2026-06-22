"""Tests for agent/calculations/transits/chandrabala.py -- P2.3.1 Chandrabala
(instant primitive).

Layer B: reference-chart fixtures, all computed programmatically (no
hand-copied expected values -- there is no AstroSage Chandrabala report on
file to source a hand-copied parity value from; see the P2.3.1 design
proposal's Section B finding that AstroSage exposes no dedicated
Chandrabala export for any of the 4 reference charts). Locked design
decisions (favorable-house enum, Janma-Rashi handling, sign convention,
vedha-sthana deferral) live in
agent/calculations/transits/chandrabala.py's module docstring -- not
duplicated here.

Imports go through the direct module path
(agent.calculations.transits.chandrabala), not through
agent.calculations.transits -- that package's __init__.py is intentionally
empty (Session 21 locked convention; re-confirmed during P2.3.1).
"""

import dataclasses
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # project root

import pytest
import swisseph as swe

import agent.calculations.transits.chandrabala as chandrabala_module
from agent.calculations.transits.chandrabala import (
    ChandrabalaCategory,
    compute_chandrabala,
)
from agent.chart_calculator import _calc_planets, calculate_chart

# Canonical transit fixture moment: 2026-06-20 18:30 UTC. Shared with
# test_gochara.py's / test_sade_sati.py's _JD_UT_20260620_1830_UTC -- see
# test_gochara.py's ANCHOR CONVENTION note for the (provisional) 18:30 UTC
# rationale. Not imported, to keep this test file's fixture self-contained,
# matching the existing transit test files' own convention.
_JD_UT_20260620_1830_UTC = swe.julday(2026, 6, 20, 18.5)

# Second fixture moment: lands transit Moon inside Sulabh's Janma Rashi
# (Scorpio) window. Diagnostic scan (P2.3.1 design proposal, Section D)
# found the window 2026-06-26 ~08:30 UTC -- 2026-06-28 ~20:30 UTC;
# 2026-06-27 14:30 UTC sits comfortably mid-window (verified below at
# ~15.6 degrees into Scorpio, nowhere near either boundary).
_JD_UT_JANMA_RASHI = swe.julday(2026, 6, 27, 14.5)


def _natal_moon_sign(name: str, dob: str, tob: str, place: str) -> int:
    """Resolve a reference chart's natal Moon sign (0=Aries..11=Pisces),
    programmatically -- mirrors test_gochara.py's _natal_lons() pattern
    (calculate_chart() + chart_calculator._calc_planets, no hand-copied
    degree values).
    """
    chart = calculate_chart(name, dob, tob, place)
    jd_ut = chart["meta"]["jd_ut"]
    asc_lon = chart["meta"]["asc_lon_sidereal"]
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    natal_planets = _calc_planets(jd_ut, asc_lon)
    moon_lon = natal_planets["Moon"]["longitude"]
    return int(moon_lon / 30.0) % 12


# ─── Fixture 1: Sulabh, canonical anchor ────────────────────────────────────

def test_sulabh_canonical_anchor_favorable():
    # Birth data shared with tests/test_chart_calculator.py and the
    # tests/manual/*_check.py scripts -- not redefined here.
    natal_moon_sign = _natal_moon_sign(
        "Sulabh", "6 Apr 1988", "00:30", "Calcutta, India"
    )
    # Cross-checked against data/default_user/kundali_summary.txt ("Rasi
    # (Moon Sign): Scorpio") during the P2.3.1 design proposal -- both
    # agree.
    assert natal_moon_sign == 7  # Scorpio

    status = compute_chandrabala(natal_moon_sign, _JD_UT_20260620_1830_UTC)

    assert status.natal_moon_sign == 7
    assert status.house_from_natal_moon == 10, (
        f"Sulabh house_from_natal_moon={status.house_from_natal_moon}, "
        "expected 10 (transit Moon in Leo at the canonical anchor)"
    )
    assert status.category == ChandrabalaCategory.FAVORABLE
    assert status.is_janma_rashi is False


# ─── Fixture 2: Sulabh, Janma-Rashi case ────────────────────────────────────

def test_sulabh_janma_rashi_favorable():
    natal_moon_sign = _natal_moon_sign(
        "Sulabh", "6 Apr 1988", "00:30", "Calcutta, India"
    )

    status = compute_chandrabala(natal_moon_sign, _JD_UT_JANMA_RASHI)

    assert status.transit_moon_sign == natal_moon_sign, (
        "transit Moon expected back in Sulabh's natal sign (Scorpio) at "
        f"this JD; got transit_moon_sign={status.transit_moon_sign} vs "
        f"natal_moon_sign={natal_moon_sign}"
    )
    assert status.house_from_natal_moon == 1
    assert status.category == ChandrabalaCategory.FAVORABLE
    assert status.is_janma_rashi is True


# ─── Fixture 3: David, canonical anchor (cross-chart robustness) ───────────

def test_david_canonical_anchor_cross_chart():
    # Birth data from playbook_export/reference/reference_charts.md Chart 4,
    # same place string used project-wide (tests/test_chart_calculator.py,
    # tests/calculations/vargas/test_navamsa.py, tests/manual/*_check.py).
    natal_moon_sign = _natal_moon_sign("David", "19 Jan 1976", "22:00", "London, UK")

    status = compute_chandrabala(natal_moon_sign, _JD_UT_20260620_1830_UTC)

    assert status.natal_moon_sign == natal_moon_sign
    assert 0 <= status.transit_moon_sign <= 11

    # No AstroSage Chandrabala report exists for David to pin against (see
    # module docstring on this file) -- expected value is derived from the
    # same formula compute_chandrabala uses, written out independently
    # here, not hand-copied. This is a cross-chart consistency check, not
    # an independent-oracle parity check.
    expected_house = ((status.transit_moon_sign - natal_moon_sign) % 12) + 1
    expected_category = (
        ChandrabalaCategory.FAVORABLE
        if expected_house in {1, 3, 6, 7, 10, 11}
        else ChandrabalaCategory.UNFAVORABLE
    )
    assert status.house_from_natal_moon == expected_house
    assert status.category == expected_category
    assert status.is_janma_rashi == (expected_house == 1)


# ─── Unit tests: mechanical correctness, no fixtures ───────────────────────

def test_chandrabala_status_is_frozen():
    natal_moon_sign = _natal_moon_sign(
        "Sulabh", "6 Apr 1988", "00:30", "Calcutta, India"
    )
    status = compute_chandrabala(natal_moon_sign, _JD_UT_20260620_1830_UTC)
    with pytest.raises(dataclasses.FrozenInstanceError):
        status.category = ChandrabalaCategory.UNFAVORABLE


def test_natal_moon_sign_below_range_raises():
    with pytest.raises(ValueError):
        compute_chandrabala(-1, _JD_UT_20260620_1830_UTC)


def test_natal_moon_sign_above_range_raises():
    with pytest.raises(ValueError):
        compute_chandrabala(12, _JD_UT_20260620_1830_UTC)


def test_moon_sign_boundary_just_below_sign_edge(monkeypatch):
    # 29.9 degrees of Aries -- still sign index 0. transit_jd is a dummy;
    # swe.calc_ut is mocked so the assertion targets _moon_sign's own
    # division/mod sign-assignment logic, not Swiss Ephemeris precision.
    def fake_calc_ut(jd_ut, planet, flags):
        return ([29.9, 0.0, 0.0, 0.0, 0.0, 0.0], 0)

    monkeypatch.setattr(chandrabala_module.swe, "calc_ut", fake_calc_ut)
    assert chandrabala_module._moon_sign(0.0) == 0  # Aries


def test_moon_sign_boundary_just_above_sign_edge(monkeypatch):
    # 30.1 degrees -- 0.1 degree into Taurus, sign index 1.
    def fake_calc_ut(jd_ut, planet, flags):
        return ([30.1, 0.0, 0.0, 0.0, 0.0, 0.0], 0)

    monkeypatch.setattr(chandrabala_module.swe, "calc_ut", fake_calc_ut)
    assert chandrabala_module._moon_sign(0.0) == 1  # Taurus


def test_is_janma_rashi_iff_house_one(monkeypatch):
    natal_moon_sign = 0  # Aries, arbitrary fixed reference
    for transit_sign in range(12):
        monkeypatch.setattr(
            chandrabala_module, "_moon_sign", lambda jd, s=transit_sign: s
        )
        status = compute_chandrabala(natal_moon_sign, 0.0)
        expected_house = (transit_sign - natal_moon_sign) % 12 + 1
        assert status.house_from_natal_moon == expected_house
        assert status.is_janma_rashi == (expected_house == 1), (
            f"transit_sign={transit_sign}: house={expected_house}, "
            f"is_janma_rashi={status.is_janma_rashi}"
        )
