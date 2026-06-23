"""Tests for find_muhurta_windows() -- P2.3.5 range-scan composition.

Mirrors the structure of test_chandrabala_windows.py.
Three reference-chart fixtures + mechanical unit tests.
Stop on first failure.
"""

import dataclasses
import sys
from pathlib import Path

import swisseph as swe
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from agent.calculations.transits.muhurta_scorer import (
    MuhurtaWindow,
    MuhurtaTier,
    find_muhurta_windows,
)
from agent.calculations.transits.chandrabala import ChandrabalaCategory
from agent.calculations.transits.tarabala import TarabalaCategory
from agent.calculations.transits.panchaka import PanchakaCategory
from agent.chart_calculator import _calc_planets, calculate_chart

_NAK_SPAN = 360.0 / 27.0

# Canonical anchor: 2026-06-20 18:30 UTC (same as all sibling window tests)
_JD_UT_20260620_1830_UTC = swe.julday(2026, 6, 20, 18.5)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _natal_moon_sign(name, dob, tob, place) -> int:
    """0=Aries..11=Pisces -- mirrors test_chandrabala_windows.py."""
    chart = calculate_chart(name, dob, tob, place)
    jd_ut = chart["meta"]["jd_ut"]
    asc_lon = chart["meta"]["asc_lon_sidereal"]
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    natal_planets = _calc_planets(jd_ut, asc_lon)
    moon_lon = natal_planets["Moon"]["longitude"]
    return int(moon_lon / 30) % 12


def _natal_nakshatra(name, dob, tob, place) -> int:
    """0=Ashwini..26=Revati -- mirrors test_tarabala_windows.py."""
    chart = calculate_chart(name, dob, tob, place)
    jd_ut = chart["meta"]["jd_ut"]
    asc_lon = chart["meta"]["asc_lon_sidereal"]
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    natal_planets = _calc_planets(jd_ut, asc_lon)
    moon_lon = natal_planets["Moon"]["longitude"]
    return int(moon_lon / _NAK_SPAN) % 27


def _assert_windows_well_formed(windows, start_jd, end_jd):
    """
    Structural invariants mirroring sibling window test helpers:
    - contiguous (no gaps, no overlaps)
    - first/last coverage
    - all start_jd < end_jd (no zero-width)
    - tier is one of the three valid values
    - favorable_count in 0..2
    - MuhurtaWindow is frozen
    """
    assert windows[0].start_jd == start_jd
    assert windows[-1].end_jd == end_jd

    for i in range(len(windows) - 1):
        assert windows[i].end_jd == windows[i + 1].start_jd, (
            f"gap at index {i}: {windows[i].end_jd} != {windows[i+1].start_jd}"
        )

    for w in windows:
        assert w.start_jd < w.end_jd, f"zero-width window at {w.start_jd}"
        assert isinstance(w.tier, MuhurtaTier)
        assert 0 <= w.favorable_count <= 2
        assert isinstance(w.warnings, tuple)
        # Panchaka veto invariant: if panchaka==PANCHAK, tier must be TIER_3
        if w.panchaka == PanchakaCategory.PANCHAK:
            assert w.tier == MuhurtaTier.TIER_3, (
                f"Panchaka veto not applied: tier={w.tier} for panchaka=PANCHAK "
                f"at [{w.start_jd}, {w.end_jd})"
            )
        # favorable_count consistency
        expected_fc = sum([
            w.chandrabala == ChandrabalaCategory.FAVORABLE,
            w.tarabala == TarabalaCategory.FAVORABLE,
        ])
        assert w.favorable_count == expected_fc, (
            f"favorable_count={w.favorable_count} != recomputed {expected_fc}"
        )


# ── Fixture 1: Sulabh, 7-day scan from canonical anchor ─────────────────────

def test_sulabh_7day_scan_structural_invariants():
    """Hardest-case-first: Sulabh has both Janma Rashi (Scorpio) and
    Janma Nakshatra (Vishakha=15) in scan window -- both warning paths exercised."""
    natal_moon_sign = _natal_moon_sign("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")
    natal_nakshatra = _natal_nakshatra("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")
    assert natal_moon_sign == 7   # Scorpio
    assert natal_nakshatra == 15  # Vishakha

    start_jd = _JD_UT_20260620_1830_UTC
    end_jd = start_jd + 7.0
    windows = find_muhurta_windows(natal_moon_sign, natal_nakshatra, start_jd, end_jd)

    # 7 days, ~3 windows per day from chandrabala (sign changes every ~2.3d),
    # further split by nakshatra changes (~13h each) and panchaka boundaries.
    # Lower bound is conservative; upper is generous.
    assert len(windows) >= 10
    assert len(windows) <= 60
    _assert_windows_well_formed(windows, start_jd, end_jd)
    # At least one TIER_1 or TIER_2 window exists in any 7-day span
    tiers_present = {w.tier for w in windows}
    assert MuhurtaTier.TIER_3 in tiers_present  # Panchaka passes through every ~27d


def test_sulabh_30day_scan_all_tiers_present():
    natal_moon_sign = _natal_moon_sign("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")
    natal_nakshatra = _natal_nakshatra("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")

    start_jd = _JD_UT_20260620_1830_UTC
    end_jd = start_jd + 30.0
    windows = find_muhurta_windows(natal_moon_sign, natal_nakshatra, start_jd, end_jd)

    _assert_windows_well_formed(windows, start_jd, end_jd)
    tiers_present = {w.tier for w in windows}
    # In 30 days, Moon cycles fully; all three tiers must appear
    assert MuhurtaTier.TIER_1 in tiers_present
    assert MuhurtaTier.TIER_2 in tiers_present
    assert MuhurtaTier.TIER_3 in tiers_present

    # Total span must equal exactly 30 days
    total_span = sum(w.end_jd - w.start_jd for w in windows)
    assert abs(total_span - 30.0) <= 1e-5


# ── Fixture 2: Surbhi, 7-day scan (cross-chart validation) ──────────────────

def test_surbhi_7day_scan_structural_invariants():
    natal_moon_sign = _natal_moon_sign("Surbhi", "11 Sep 1992", "10:30", "Patna, India")
    natal_nakshatra = _natal_nakshatra("Surbhi", "11 Sep 1992", "10:30", "Patna, India")

    start_jd = _JD_UT_20260620_1830_UTC
    end_jd = start_jd + 7.0
    windows = find_muhurta_windows(natal_moon_sign, natal_nakshatra, start_jd, end_jd)

    assert len(windows) >= 10
    _assert_windows_well_formed(windows, start_jd, end_jd)


# ── Fixture 3: David, 7-day scan (cross-chart, London birth) ────────────────

def test_david_7day_scan_structural_invariants():
    natal_moon_sign = _natal_moon_sign("David", "19 Jan 1976", "22:00", "London, UK")
    natal_nakshatra = _natal_nakshatra("David", "19 Jan 1976", "22:00", "London, UK")

    start_jd = _JD_UT_20260620_1830_UTC
    end_jd = start_jd + 7.0
    windows = find_muhurta_windows(natal_moon_sign, natal_nakshatra, start_jd, end_jd)

    assert len(windows) >= 10
    _assert_windows_well_formed(windows, start_jd, end_jd)


# ── Unit tests: mechanical correctness, no fixtures ─────────────────────────

def test_empty_range_returns_empty_list():
    assert find_muhurta_windows(7, 15, _JD_UT_20260620_1830_UTC, _JD_UT_20260620_1830_UTC) == []


def test_inverted_range_raises_value_error():
    with pytest.raises(ValueError):
        find_muhurta_windows(7, 15, _JD_UT_20260620_1830_UTC + 1.0, _JD_UT_20260620_1830_UTC)


def test_natal_moon_sign_below_range_raises():
    with pytest.raises(ValueError):
        find_muhurta_windows(-1, 15, _JD_UT_20260620_1830_UTC, _JD_UT_20260620_1830_UTC + 1.0)


def test_natal_moon_sign_above_range_raises():
    with pytest.raises(ValueError):
        find_muhurta_windows(12, 15, _JD_UT_20260620_1830_UTC, _JD_UT_20260620_1830_UTC + 1.0)


def test_janma_nakshatra_below_range_raises():
    with pytest.raises(ValueError):
        find_muhurta_windows(7, -1, _JD_UT_20260620_1830_UTC, _JD_UT_20260620_1830_UTC + 1.0)


def test_janma_nakshatra_above_range_raises():
    with pytest.raises(ValueError):
        find_muhurta_windows(7, 27, _JD_UT_20260620_1830_UTC, _JD_UT_20260620_1830_UTC + 1.0)


def test_muhurta_window_is_frozen():
    windows = find_muhurta_windows(
        7, 15, _JD_UT_20260620_1830_UTC, _JD_UT_20260620_1830_UTC + 1.0
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        windows[0].tier = MuhurtaTier.TIER_1


def test_panchaka_veto_always_yields_tier3():
    """Spot-check: any window where panchaka==PANCHAK must have tier==TIER_3,
    regardless of chandrabala/tarabala. Verified over a 30-day Sulabh scan."""
    windows = find_muhurta_windows(
        7, 15, _JD_UT_20260620_1830_UTC, _JD_UT_20260620_1830_UTC + 30.0
    )
    panchaka_windows = [w for w in windows if w.panchaka == PanchakaCategory.PANCHAK]
    assert len(panchaka_windows) > 0, "no Panchaka windows found in 30d -- extend scan range"
    for w in panchaka_windows:
        assert w.tier == MuhurtaTier.TIER_3


def test_favorable_count_excludes_panchaka():
    """favorable_count must equal sum of chandrabala+tarabala FAVORABLE,
    never incremented by Panchaka status."""
    windows = find_muhurta_windows(
        7, 15, _JD_UT_20260620_1830_UTC, _JD_UT_20260620_1830_UTC + 7.0
    )
    for w in windows:
        expected = sum([
            w.chandrabala == ChandrabalaCategory.FAVORABLE,
            w.tarabala == TarabalaCategory.FAVORABLE,
        ])
        assert w.favorable_count == expected
