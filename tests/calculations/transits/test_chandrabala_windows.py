"""Tests for agent/calculations/transits/chandrabala.py's range-scan surface
-- P2.3.1.2 / P2.3.2 find_chandrabala_windows().

Separate file from test_chandrabala.py: the range-scan (bisection over the
instant primitive) is conceptually distinct from the instant primitive
itself, per the P2.3.2 prompt.

Layer B: reference-chart fixtures, all computed programmatically -- no
hand-copied expected values (no AstroSage Chandrabala report exists to
source one from; see the P2.3.1 design proposal's Section B finding).
Locked design decisions (coarse-step/bisection-precision justification,
no-retrograde-handling rationale, bisecting on the full
(category, is_janma_rashi, house_from_natal_moon) triple) live in
chandrabala.py's module docstring's Range-scan section -- not duplicated
here.

Imports go through the direct module path
(agent.calculations.transits.chandrabala), not through
agent.calculations.transits -- that package's __init__.py is intentionally
empty (Session 21 locked convention).
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
    find_chandrabala_windows,
)
from agent.chart_calculator import _calc_planets, calculate_chart

_FAVORABLE_HOUSES = {1, 3, 6, 7, 10, 11}

# Canonical transit fixture moment, same as test_chandrabala.py / test_gochara.py
# / test_sade_sati.py -- redefined inline per this test family's
# self-containment convention, not imported.
_JD_UT_20260620_1830_UTC = swe.julday(2026, 6, 20, 18.5)


def _natal_moon_sign(name: str, dob: str, tob: str, place: str) -> int:
    """Resolve a reference chart's natal Moon sign (0=Aries..11=Pisces),
    programmatically -- mirrors test_gochara.py's _natal_lons() /
    test_chandrabala.py's _natal_moon_sign() pattern.
    """
    chart = calculate_chart(name, dob, tob, place)
    jd_ut = chart["meta"]["jd_ut"]
    asc_lon = chart["meta"]["asc_lon_sidereal"]
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    natal_planets = _calc_planets(jd_ut, asc_lon)
    moon_lon = natal_planets["Moon"]["longitude"]
    return int(moon_lon / 30.0) % 12


def _assert_windows_well_formed(windows, natal_moon_sign, start_jd, end_jd):
    """Shared structural checks reused across all three fixtures: per-window
    classification correctness (re-derived independently, not hand-copied),
    boundary-ingress alignment, contiguity, and start/end coverage.
    """
    assert windows[0].start_jd == start_jd
    assert windows[-1].end_jd == end_jd

    for i in range(len(windows) - 1):
        assert windows[i].end_jd == windows[i + 1].start_jd

    for w in windows:
        midpoint = (w.start_jd + w.end_jd) / 2.0
        transit_sign_mid = chandrabala_module._moon_sign(midpoint)
        expected_house = ((transit_sign_mid - natal_moon_sign) % 12) + 1
        assert w.house_from_natal_moon == expected_house, (
            f"window [{w.start_jd}, {w.end_jd}): house={w.house_from_natal_moon} "
            f"vs expected {expected_house} at midpoint"
        )
        expected_category = (
            ChandrabalaCategory.FAVORABLE
            if expected_house in _FAVORABLE_HOUSES
            else ChandrabalaCategory.UNFAVORABLE
        )
        assert w.category == expected_category
        assert w.is_janma_rashi == (expected_house == 1)

    # Boundary-ingress alignment: every window after the first starts at an
    # actual Moon sign ingress (sign differs just before vs just after).
    # The first window's start_jd is the caller's start_jd, not an ingress.
    for w in windows[1:]:
        sign_before = chandrabala_module._moon_sign(w.start_jd - 1e-3)
        sign_after = chandrabala_module._moon_sign(w.start_jd + 1e-3)
        assert sign_before != sign_after, (
            f"window boundary at jd={w.start_jd} does not align with a "
            "Moon sign ingress"
        )


# ─── Fixture 1: Sulabh, 7-day scan from canonical anchor ───────────────────

def test_sulabh_7day_scan_from_canonical_anchor():
    natal_moon_sign = _natal_moon_sign(
        "Sulabh", "6 Apr 1988", "00:30", "Calcutta, India"
    )
    assert natal_moon_sign == 7  # Scorpio

    start_jd = _JD_UT_20260620_1830_UTC
    end_jd = start_jd + 7.0
    windows = find_chandrabala_windows(natal_moon_sign, start_jd, end_jd)

    # Moon moves through ~3 signs in 7 days (~2.25 days/sign); a partial
    # window at each end of the scan can push this to 3 or 4 -- not pinning
    # the exact count, which is an artifact of where the scan starts/ends,
    # not the thing actually under test.
    assert 3 <= len(windows) <= 4

    _assert_windows_well_formed(windows, natal_moon_sign, start_jd, end_jd)


# ─── Fixture 2: Sulabh, 30-day scan from a known Janma-Rashi entry ─────────

def test_sulabh_30day_scan_covers_janma_rashi():
    natal_moon_sign = _natal_moon_sign(
        "Sulabh", "6 Apr 1988", "00:30", "Calcutta, India"
    )

    # Moon enters Scorpio (Sulabh's natal sign) around 2026-06-26 08:30 UTC
    # per the P2.3.1 design proposal's diagnostic scan; starting the window
    # at 00:00 UTC that day means the very first window should already be
    # the Janma-Rashi one.
    start_jd = swe.julday(2026, 6, 26, 0.0)
    end_jd = start_jd + 30.0
    windows = find_chandrabala_windows(natal_moon_sign, start_jd, end_jd)

    assert len(windows) >= 12  # Moon cycles every ~27.3 days -> ~13 ingresses in 30 days
    assert any(w.is_janma_rashi for w in windows)

    total_span = sum(w.end_jd - w.start_jd for w in windows)
    assert abs(total_span - 30.0) <= 1e-5

    _assert_windows_well_formed(windows, natal_moon_sign, start_jd, end_jd)


# ─── Fixture 3: David, 7-day scan from canonical anchor (cross-chart) ──────

def test_david_7day_scan_from_canonical_anchor():
    natal_moon_sign = _natal_moon_sign("David", "19 Jan 1976", "22:00", "London, UK")

    start_jd = _JD_UT_20260620_1830_UTC
    end_jd = start_jd + 7.0
    windows = find_chandrabala_windows(natal_moon_sign, start_jd, end_jd)

    assert 3 <= len(windows) <= 4
    _assert_windows_well_formed(windows, natal_moon_sign, start_jd, end_jd)


# ─── Unit tests: mechanical correctness, no fixtures ───────────────────────

def test_empty_range_returns_empty_list():
    assert find_chandrabala_windows(7, _JD_UT_20260620_1830_UTC, _JD_UT_20260620_1830_UTC) == []


def test_inverted_range_raises_value_error():
    with pytest.raises(ValueError):
        find_chandrabala_windows(7, _JD_UT_20260620_1830_UTC + 1.0, _JD_UT_20260620_1830_UTC)


def test_natal_moon_sign_below_range_raises():
    with pytest.raises(ValueError):
        find_chandrabala_windows(-1, _JD_UT_20260620_1830_UTC, _JD_UT_20260620_1830_UTC + 1.0)


def test_natal_moon_sign_above_range_raises():
    with pytest.raises(ValueError):
        find_chandrabala_windows(12, _JD_UT_20260620_1830_UTC, _JD_UT_20260620_1830_UTC + 1.0)


def test_chandrabala_window_is_frozen():
    windows = find_chandrabala_windows(
        7, _JD_UT_20260620_1830_UTC, _JD_UT_20260620_1830_UTC + 1.0
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        windows[0].category = ChandrabalaCategory.UNFAVORABLE


def test_bisect_transition_converges_to_known_threshold(monkeypatch):
    # Contrive a sign transition at a specific, known fractional JD inside
    # one coarse-step bracket, mocking _moon_sign directly (sign 0 before
    # the threshold, sign 1 after) -- then verify _bisect_transition
    # converges to within _BISECT_TOL_JD of that exact, known value.
    t_lo = 2461212.0
    true_transition = t_lo + 0.337  # arbitrary offset within the bracket
    t_hi = t_lo + chandrabala_module._COARSE_STEP_JD

    def fake_moon_sign(jd_ut):
        return 0 if jd_ut < true_transition else 1

    monkeypatch.setattr(chandrabala_module, "_moon_sign", fake_moon_sign)

    natal_moon_sign = 5

    def classify(jd):
        status = compute_chandrabala(natal_moon_sign, jd)
        return status.category, status.is_janma_rashi, status.house_from_natal_moon

    state_lo = classify(t_lo)
    state_hi = classify(t_hi)
    assert state_lo != state_hi

    result = chandrabala_module._bisect_transition(t_lo, t_hi, state_lo, state_hi, classify)
    assert abs(result - true_transition) <= chandrabala_module._BISECT_TOL_JD


def test_window_contiguity_invariant():
    natal_moon_sign = _natal_moon_sign(
        "Sulabh", "6 Apr 1988", "00:30", "Calcutta, India"
    )
    start_jd = _JD_UT_20260620_1830_UTC
    end_jd = start_jd + 7.0
    windows = find_chandrabala_windows(natal_moon_sign, start_jd, end_jd)

    assert len(windows) >= 2
    for i in range(len(windows) - 1):
        assert windows[i].end_jd == windows[i + 1].start_jd


def test_window_first_last_coverage_invariant():
    natal_moon_sign = _natal_moon_sign(
        "Sulabh", "6 Apr 1988", "00:30", "Calcutta, India"
    )
    start_jd = _JD_UT_20260620_1830_UTC
    end_jd = start_jd + 7.0
    windows = find_chandrabala_windows(natal_moon_sign, start_jd, end_jd)

    assert windows[0].start_jd == start_jd
    assert windows[-1].end_jd == end_jd
