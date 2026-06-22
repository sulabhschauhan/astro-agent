"""Tests for agent/calculations/transits/panchaka.py's range-scan surface --
P2.3.4 find_panchaka_windows().

Separate file from test_panchaka.py: the range-scan (bisection over the
instant primitive) is conceptually distinct from the instant primitive
itself, mirroring test_chandrabala_windows.py's / test_tarabala_windows.py's
split from their instant-primitive test files.

Panchaka is NOT natal-relative (see panchaka.py's module docstring) -- no
reference-chart fixtures here; the scan-window fixtures below are locked JD
ranges from the P2.3.4 design proposal, not recomputed in this file.

Imports go through the direct module path
(agent.calculations.transits.panchaka), not through
agent.calculations.transits -- that package's __init__.py is intentionally
empty (Session 21 locked convention).
"""

import dataclasses
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # project root

import pytest
import swisseph as swe

from agent.calculations.transits.panchaka import (
    PanchakaCategory,
    compute_panchaka,
    find_panchaka_windows,
)

# Canonical transit fixture moment, same as test_panchaka.py / test_chandrabala.py
# / test_tarabala.py / test_gochara.py / test_sade_sati.py -- redefined
# inline per this test family's self-containment convention, not imported.
_JD_UT_20260620_1830_UTC = swe.julday(2026, 6, 20, 18.5)

# 12-day scan bracketing the July Panchak window: 2026-06-29 00:00 UTC --
# 2026-07-11 00:00 UTC. Locked from the P2.3.4 design proposal -- not
# recomputed here.
_JD_UT_BRACKET_START = 2461221.5
_JD_UT_BRACKET_END = 2461233.5

# 2-day scan inside the Panchak band: 2026-07-05 00:00 UTC -- 2026-07-07
# 00:00 UTC. Locked from the P2.3.4 design proposal -- not recomputed here.
_JD_UT_INSIDE_BAND_START = 2461226.5
_JD_UT_INSIDE_BAND_END = 2461228.5


# ─── Fixture 1: 7-day scan from canonical anchor ───────────────────────────

def test_seven_day_scan_from_canonical_anchor_yields_single_not_panchak_window():
    start_jd = _JD_UT_20260620_1830_UTC
    end_jd = start_jd + 7.0
    windows = find_panchaka_windows(start_jd, end_jd)

    assert len(windows) == 1
    assert windows[0].category == PanchakaCategory.NOT_PANCHAK
    assert windows[0].start_jd == start_jd
    assert windows[0].end_jd == end_jd


# ─── Fixture 2: 12-day scan bracketing the July Panchak window ─────────────

def test_twelve_day_bracketing_scan_yields_three_alternating_windows():
    start_jd = _JD_UT_BRACKET_START
    end_jd = _JD_UT_BRACKET_END
    windows = find_panchaka_windows(start_jd, end_jd)

    assert len(windows) == 3
    assert [w.category for w in windows] == [
        PanchakaCategory.NOT_PANCHAK,
        PanchakaCategory.PANCHAK,
        PanchakaCategory.NOT_PANCHAK,
    ]
    for i in (0, 1):
        assert windows[i].end_jd == windows[i + 1].start_jd
    assert windows[0].start_jd == start_jd
    assert windows[-1].end_jd == end_jd


# ─── Fixture 3: 2-day scan inside the Panchak band ─────────────────────────

def test_two_day_inside_band_scan_yields_single_panchak_window():
    start_jd = _JD_UT_INSIDE_BAND_START
    end_jd = _JD_UT_INSIDE_BAND_END
    windows = find_panchaka_windows(start_jd, end_jd)

    assert len(windows) == 1
    assert windows[0].category == PanchakaCategory.PANCHAK
    assert windows[0].start_jd == start_jd
    assert windows[0].end_jd == end_jd


# ─── Unit tests: mechanical correctness, no fixtures ───────────────────────

def test_empty_range_returns_empty_list():
    assert find_panchaka_windows(2461227.5, 2461227.5) == []


def test_inverted_range_raises_valueerror():
    with pytest.raises(ValueError, match="start_jd"):
        find_panchaka_windows(2461227.5, 2461220.5)


def test_panchaka_window_is_frozen():
    windows = find_panchaka_windows(_JD_UT_INSIDE_BAND_START, _JD_UT_INSIDE_BAND_END)
    with pytest.raises(dataclasses.FrozenInstanceError):
        windows[0].category = PanchakaCategory.NOT_PANCHAK


def test_bisection_converges_to_panchak_entry_threshold():
    # Moon moves ~13 deg/day = ~1.5e-4 deg/sec; _BISECT_TOL_JD = 1e-6 day
    # (~0.09s) -> max longitude drift ~1.4e-5 deg. 1e-4 deg tolerance gives
    # comfortable headroom.
    windows = find_panchaka_windows(_JD_UT_BRACKET_START, _JD_UT_BRACKET_END)
    t_entry = windows[0].end_jd
    assert t_entry == windows[1].start_jd

    status = compute_panchaka(t_entry)
    assert abs(status.moon_longitude - 300.0) <= 1e-4


def test_bisection_converges_to_panchak_exit_threshold():
    windows = find_panchaka_windows(_JD_UT_BRACKET_START, _JD_UT_BRACKET_END)
    t_exit = windows[1].end_jd
    assert t_exit == windows[2].start_jd

    status = compute_panchaka(t_exit)
    wraparound_distance = min(
        abs(status.moon_longitude - 0.0), abs(status.moon_longitude - 360.0)
    )
    assert wraparound_distance <= 1e-4


def test_window_contiguity_and_full_coverage_invariant():
    start_jd = _JD_UT_BRACKET_START
    end_jd = _JD_UT_BRACKET_END
    windows = find_panchaka_windows(start_jd, end_jd)

    assert windows[0].start_jd == start_jd
    assert windows[-1].end_jd == end_jd
    assert all(
        windows[i].end_jd == windows[i + 1].start_jd
        for i in range(len(windows) - 1)
    )
