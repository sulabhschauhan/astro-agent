"""Tests for agent/calculations/helpers/discrete_scan.py -- Session 26
extraction of the duplicated _bisect_transition / find_*_windows pattern
from chandrabala.py, tarabala.py, and panchaka.py.

All state_fns here are synthetic closed-form functions of jd (no
ephemeris, no swisseph dependency) -- the goal is to pin down
find_state_segments' own algorithmic behavior in isolation, independent
of any specific astrological domain. The Session 26 caller audit (see
discrete_scan.py's module docstring) found chandrabala.py / tarabala.py /
panchaka.py byte-identical on every axis tested below; these tests encode
that audited behavior as a regression suite for the extracted helper.

Path note: this module's path is tests/calculations/helpers/, mirroring
agent/calculations/helpers/ -- the project's existing tests/calculations/
<subpackage>/ convention (see test_chandrabala.py, test_navamsa.py, etc.),
not the flat tests/helpers/ path, since the helper itself lives under
agent/calculations/helpers/, not agent/helpers/ (neither pre-existed; the
sibling agent/calculations/helpers/house_counting.py settled the parent).
"""

import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # project root

import pytest

from agent.calculations.helpers.discrete_scan import StateSegment, find_state_segments


# ─── Single transition mid-window ──────────────────────────────────────────

def test_single_transition_mid_window():
    threshold = 5.3

    def state_fn(jd):
        return "A" if jd < threshold else "B"

    segments = find_state_segments(state_fn, 0.0, 10.0, 1.0)

    assert len(segments) == 2
    assert segments[0].state == "A"
    assert segments[1].state == "B"
    assert segments[0].start_jd == 0.0
    assert segments[-1].end_jd == 10.0
    assert segments[0].end_jd == segments[1].start_jd
    assert abs(segments[0].end_jd - threshold) <= 1e-6


# ─── Multiple transitions in same window ───────────────────────────────────

def test_multiple_transitions_in_same_window():
    # Four states over [0, 10): A < 2.5 <= B < 5.5 <= C < 8.2 <= D.
    thresholds = (2.5, 5.5, 8.2)
    names = ("A", "B", "C", "D")

    def state_fn(jd):
        idx = sum(1 for t in thresholds if jd >= t)
        return names[idx]

    segments = find_state_segments(state_fn, 0.0, 10.0, 0.5)

    assert len(segments) == 4
    assert [s.state for s in segments] == ["A", "B", "C", "D"]
    assert segments[0].start_jd == 0.0
    assert segments[-1].end_jd == 10.0
    for i in range(len(segments) - 1):
        assert segments[i].end_jd == segments[i + 1].start_jd
    for seg, threshold in zip(segments[1:], thresholds):
        assert abs(seg.start_jd - threshold) <= 1e-6


# ─── Constant state, no transitions ────────────────────────────────────────

def test_constant_state_no_transitions():
    def state_fn(jd):
        return "X"

    segments = find_state_segments(state_fn, 0.0, 10.0, 1.0)

    assert len(segments) == 1
    assert segments[0].state == "X"
    assert segments[0].start_jd == 0.0
    assert segments[0].end_jd == 10.0


# ─── Transition exactly at start_jd ─────────────────────────────────────────

def test_transition_exactly_at_start_jd():
    # Threshold coincides with start_jd: every sample in [start_jd, end_jd)
    # is already on the "after" side, so the "before" state is never
    # observed -- the scan absorbs the boundary-exact transition into a
    # single uniform segment, matching the audited callers' behavior.
    start_jd = 3.0
    threshold = start_jd

    def state_fn(jd):
        return "before" if jd < threshold else "after"

    segments = find_state_segments(state_fn, start_jd, 10.0, 1.0)

    assert len(segments) == 1
    assert segments[0].state == "after"
    assert segments[0].start_jd == start_jd
    assert segments[0].end_jd == 10.0


# ─── Transition exactly at end_jd ───────────────────────────────────────────

def test_transition_exactly_at_end_jd():
    # Threshold coincides with end_jd: the forced final sample AT end_jd
    # reports "after" while every prior coarse sample reports "before",
    # so a (possibly sub-coarse-step-width) transition segment is
    # detected and bisected right at the boundary -- matching the
    # audited callers' near-boundary behavior (never dropped, never
    # collapsed away).
    end_jd = 10.0
    threshold = end_jd

    def state_fn(jd):
        return "before" if jd < threshold else "after"

    segments = find_state_segments(state_fn, 0.0, end_jd, 1.0)

    assert len(segments) == 2
    assert segments[0].state == "before"
    assert segments[1].state == "after"
    assert segments[0].start_jd == 0.0
    assert segments[-1].end_jd == end_jd
    assert abs(segments[1].start_jd - threshold) <= 1e-6


# ─── Transition within tol_jd of a boundary ────────────────────────────────

def test_transition_within_tol_jd_of_boundary():
    end_jd = 10.0
    tol_jd = 1e-6
    threshold = end_jd - 3e-7  # strictly inside tol_jd of end_jd

    def state_fn(jd):
        return "before" if jd < threshold else "after"

    segments = find_state_segments(state_fn, 0.0, end_jd, 1.0, tol_jd=tol_jd)

    assert len(segments) == 2
    assert segments[0].state == "before"
    assert segments[1].state == "after"
    assert segments[-1].end_jd == end_jd
    assert abs(segments[1].start_jd - threshold) <= tol_jd


# ─── state_fn raising must propagate ───────────────────────────────────────

def test_state_fn_exception_propagates():
    def raising_state_fn(jd):
        raise RuntimeError("synthetic failure")

    with pytest.raises(RuntimeError, match="synthetic failure"):
        find_state_segments(raising_state_fn, 0.0, 10.0, 1.0)


# ─── Inverted window ────────────────────────────────────────────────────────

def test_inverted_window_raises_valueerror():
    def state_fn(jd):
        return "X"

    with pytest.raises(ValueError, match="start_jd"):
        find_state_segments(state_fn, 10.0, 5.0, 1.0)


# ─── Empty window (start_jd == end_jd) ─────────────────────────────────────

def test_empty_window_returns_empty_list():
    def state_fn(jd):
        return "X"

    assert find_state_segments(state_fn, 5.0, 5.0, 1.0) == []


# ─── StateSegment is frozen ─────────────────────────────────────────────────

def test_state_segment_is_frozen():
    segment = StateSegment(start_jd=0.0, end_jd=1.0, state="X")
    with pytest.raises(FrozenInstanceError):
        segment.state = "Y"


# ─── Tuple state plumbing ───────────────────────────────────────────────────

def test_tuple_state_segments():
    # Tuple-state plumbing -- mirrors the (enum, bool, int) shape used
    # by chandrabala.py / tarabala.py to verify the Hashable TypeVar
    # bound works for composite states, not just scalar enums.
    threshold = 4.7

    def state_fn(jd):
        if jd < threshold:
            return ("LOW", True, 1)
        return ("HIGH", False, 7)

    segments = find_state_segments(state_fn, 0.0, 10.0, 1.0)

    assert len(segments) == 2
    assert segments[0].state == ("LOW", True, 1)
    assert segments[1].state == ("HIGH", False, 7)
    assert abs(segments[0].end_jd - threshold) <= 1e-6
