"""Tests for agent/calculations/transits/tarabala.py's range-scan surface --
P2.3.3 find_tarabala_windows().

Separate file from test_tarabala.py: the range-scan (bisection over the
instant primitive) is conceptually distinct from the instant primitive
itself, mirroring test_chandrabala_windows.py's split from test_chandrabala.py.

Layer B: reference-chart fixtures, all computed programmatically -- no
hand-copied expected values. Locked design decisions (coarse-step/
bisection-precision justification, no-retrograde-handling rationale,
bisecting on the (category, is_janma_tara, tara_number) triple) live in
tarabala.py's module docstring's Range-scan section -- not duplicated here.

Imports go through the direct module path
(agent.calculations.transits.tarabala), not through
agent.calculations.transits -- that package's __init__.py is intentionally
empty (Session 21 locked convention).
"""

import dataclasses
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # project root

import pytest
import swisseph as swe

import agent.calculations.transits.tarabala as tarabala_module
from agent.calculations.transits.tarabala import (
    TarabalaCategory,
    TaraName,
    compute_tarabala,
    find_tarabala_windows,
)
from agent.chart_calculator import _calc_planets, calculate_chart

_NAK_SPAN = 360.0 / 27.0
_FAVORABLE_TARA_NUMBERS = {2, 4, 6, 8, 9}
_JANMA_TARA_COUNTS = {1, 10, 19}

# Locked 9-tara name table, redefined independently here (not imported from
# tarabala.py's private _TARA_NAMES_BY_NUMBER) -- mirrors test_tarabala.py's
# and test_chandrabala_windows.py's self-containment convention.
_EXPECTED_TARA_NAME_BY_NUMBER = {
    1: TaraName.JANMA,
    2: TaraName.SAMPAT,
    3: TaraName.VIPAT,
    4: TaraName.KSHEMA,
    5: TaraName.PRATYARI,
    6: TaraName.SADHAKA,
    7: TaraName.VADHA,
    8: TaraName.MITRA,
    9: TaraName.ATI_MITRA,
}

# Canonical transit fixture moment, same as test_tarabala.py / test_gochara.py
# / test_sade_sati.py / test_chandrabala.py -- redefined inline per this test
# family's self-containment convention, not imported.
_JD_UT_20260620_1830_UTC = swe.julday(2026, 6, 20, 18.5)


def _natal_nakshatra(name: str, dob: str, tob: str, place: str) -> int:
    """Resolve a reference chart's natal Moon nakshatra (0=Ashwini..26=Revati),
    programmatically -- mirrors test_tarabala.py's _natal_nakshatra() pattern.
    """
    chart = calculate_chart(name, dob, tob, place)
    jd_ut = chart["meta"]["jd_ut"]
    asc_lon = chart["meta"]["asc_lon_sidereal"]
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    natal_planets = _calc_planets(jd_ut, asc_lon)
    moon_lon = natal_planets["Moon"]["longitude"]
    return int(moon_lon / _NAK_SPAN) % 27


def _assert_windows_well_formed(windows, natal_nakshatra, start_jd, end_jd):
    """Shared structural checks reused across all three fixtures: per-window
    classification correctness (re-derived independently, not hand-copied),
    boundary-ingress alignment, contiguity, and start/end coverage. Mirrors
    test_chandrabala_windows.py's helper of the same name.
    """
    assert windows[0].start_jd == start_jd
    assert windows[-1].end_jd == end_jd

    for i in range(len(windows) - 1):
        assert windows[i].end_jd == windows[i + 1].start_jd

    for w in windows:
        midpoint = (w.start_jd + w.end_jd) / 2.0
        transit_nak_mid = tarabala_module._moon_nakshatra(midpoint)
        expected_count = ((transit_nak_mid - natal_nakshatra) % 27) + 1
        expected_tara_number = ((expected_count - 1) % 9) + 1
        assert w.nakshatra_count == expected_count, (
            f"window [{w.start_jd}, {w.end_jd}): count={w.nakshatra_count} "
            f"vs expected {expected_count} at midpoint"
        )
        assert w.transit_nakshatra == transit_nak_mid
        assert w.tara_name == _EXPECTED_TARA_NAME_BY_NUMBER[expected_tara_number]
        expected_category = (
            TarabalaCategory.FAVORABLE
            if expected_tara_number in _FAVORABLE_TARA_NUMBERS
            else TarabalaCategory.UNFAVORABLE
        )
        assert w.category == expected_category
        assert w.is_janma_tara == (expected_count in _JANMA_TARA_COUNTS)

    # Boundary-ingress alignment: every window after the first starts at an
    # actual Moon nakshatra ingress (nakshatra differs just before vs just
    # after). The first window's start_jd is the caller's start_jd, not an
    # ingress.
    for w in windows[1:]:
        nak_before = tarabala_module._moon_nakshatra(w.start_jd - 1e-3)
        nak_after = tarabala_module._moon_nakshatra(w.start_jd + 1e-3)
        assert nak_before != nak_after, (
            f"window boundary at jd={w.start_jd} does not align with a "
            "Moon nakshatra ingress"
        )


# ─── Fixture 1: Sulabh, 7-day scan from canonical anchor ───────────────────

def test_sulabh_7day_scan_from_canonical_anchor():
    natal_nakshatra = _natal_nakshatra(
        "Sulabh", "6 Apr 1988", "00:30", "Calcutta, India"
    )
    assert natal_nakshatra == 15  # Vishakha

    start_jd = _JD_UT_20260620_1830_UTC
    end_jd = start_jd + 7.0
    windows = find_tarabala_windows(natal_nakshatra, start_jd, end_jd)

    # Moon moves through ~7 nakshatras in 7 days (~1.0125 days/nakshatra); a
    # partial window at each end of the scan can push this to 7 or 8 -- not
    # pinning the exact count, which is an artifact of where the scan
    # starts/ends, not the thing actually under test.
    assert 7 <= len(windows) <= 9

    _assert_windows_well_formed(windows, natal_nakshatra, start_jd, end_jd)


# ─── Fixture 2: Sulabh, 30-day scan covering a Janma-Tara entry ────────────

def test_sulabh_30day_scan_covers_janma_tara():
    natal_nakshatra = _natal_nakshatra(
        "Sulabh", "6 Apr 1988", "00:30", "Calcutta, India"
    )

    start_jd = swe.julday(2026, 6, 26, 0.0)
    end_jd = start_jd + 30.0
    windows = find_tarabala_windows(natal_nakshatra, start_jd, end_jd)

    # Moon cycles through all 27 nakshatras in ~27.3 days -> 30 days
    # guarantees a Janma-Tara hit (and ~29-30 ingresses).
    assert len(windows) >= 25
    assert any(w.is_janma_tara for w in windows)

    total_span = sum(w.end_jd - w.start_jd for w in windows)
    assert abs(total_span - 30.0) <= 1e-5

    _assert_windows_well_formed(windows, natal_nakshatra, start_jd, end_jd)


# ─── Fixture 3: David, 7-day scan from canonical anchor (cross-chart) ──────

def test_david_7day_scan_from_canonical_anchor():
    natal_nakshatra = _natal_nakshatra("David", "19 Jan 1976", "22:00", "London, UK")

    start_jd = _JD_UT_20260620_1830_UTC
    end_jd = start_jd + 7.0
    windows = find_tarabala_windows(natal_nakshatra, start_jd, end_jd)

    assert 7 <= len(windows) <= 9
    _assert_windows_well_formed(windows, natal_nakshatra, start_jd, end_jd)


# ─── Unit tests: mechanical correctness, no fixtures ───────────────────────

def test_empty_range_returns_empty_list():
    assert find_tarabala_windows(15, _JD_UT_20260620_1830_UTC, _JD_UT_20260620_1830_UTC) == []


def test_inverted_range_raises_value_error():
    with pytest.raises(ValueError):
        find_tarabala_windows(15, _JD_UT_20260620_1830_UTC + 1.0, _JD_UT_20260620_1830_UTC)


def test_natal_nakshatra_below_range_raises():
    with pytest.raises(ValueError):
        find_tarabala_windows(-1, _JD_UT_20260620_1830_UTC, _JD_UT_20260620_1830_UTC + 1.0)


def test_natal_nakshatra_above_range_raises():
    with pytest.raises(ValueError):
        find_tarabala_windows(27, _JD_UT_20260620_1830_UTC, _JD_UT_20260620_1830_UTC + 1.0)


def test_tarabala_window_is_frozen():
    windows = find_tarabala_windows(
        15, _JD_UT_20260620_1830_UTC, _JD_UT_20260620_1830_UTC + 1.0
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        windows[0].category = TarabalaCategory.FAVORABLE
