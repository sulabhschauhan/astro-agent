"""scan_quantised_crossings -- pure tests, zero ephemeris, zero swisseph.

The headline test is `test_sub_step_round_trip_is_found`: it encodes the defect
the S148 roster found in the original design (sampling two coarse endpoints and
bisecting the bracket), and it fails against that approach while passing against
the adaptive prune. Everything else guards the index arithmetic and the span
contract.
"""
import math

import pytest

from agent.calculations.helpers.discrete_scan import (
    Crossing, _division_index, default_initial_step, find_state_segments,
    scan_quantised_crossings,
)


# ── the defect the design review caught ──────────────────────────────────────

def test_sub_step_round_trip_is_found():
    """A boundary crossed and re-crossed INSIDE one coarse step yields two
    crossings. The naive state-sampling approach yields zero -- asserted below in
    the same test so the contrast is the test, not a comment."""
    boundary, t0 = 30.0, 100.0
    # Parabolic excursion peaking 0.05 deg past the 30 deg cusp; above-boundary
    # residence is 2*sqrt(0.05/2) = 0.316 d, well inside the 3.4 d first stride.
    angle = lambda t: boundary + 0.05 - 2.0 * (t - t0) ** 2  # noqa: E731
    rate = 2.0 * 2.0 * 5.0  # |d/dt| <= 4*|t-t0| <= 20 on [95, 105]

    found = scan_quantised_crossings(angle, 12, 95.0, 105.0,
                                     rate_bound=rate, initial_step_jd=3.4)
    inner = [c for c in found if {c.from_index, c.to_index} == {0, 1}]
    assert len(inner) == 2
    assert inner[0].from_index == 0 and inner[0].to_index == 1
    assert inner[1].from_index == 1 and inner[1].to_index == 0
    # analytic roots t0 -+ sqrt(0.05/2)
    root = math.sqrt(0.05 / 2.0)
    assert inner[0].jd == pytest.approx(t0 - root, abs=1e-5)
    assert inner[1].jd == pytest.approx(t0 + root, abs=1e-5)

    # the rejected approach, same inputs: the excursion is invisible
    states = [s.state for s in find_state_segments(
        lambda t: int((angle(t) % 360.0) * 12 / 360.0) % 12, 95.0, 105.0, 3.4)]
    assert 1 not in states


def test_result_is_not_step_dependent():
    """The same crossings are reported at a coarse and a fine first stride --
    i.e. correctness comes from the prune, not from the step."""
    angle = lambda t: 30.0 + 0.05 - 2.0 * (t - 100.0) ** 2  # noqa: E731
    coarse = scan_quantised_crossings(angle, 12, 95.0, 105.0,
                                      rate_bound=20.0, initial_step_jd=3.4)
    fine = scan_quantised_crossings(angle, 12, 95.0, 105.0,
                                    rate_bound=20.0, initial_step_jd=0.05)
    assert [(c.from_index, c.to_index) for c in coarse] == \
           [(c.from_index, c.to_index) for c in fine]
    for a, b in zip(coarse, fine):
        assert a.jd == pytest.approx(b.jd, abs=1e-5)


# ── index arithmetic ─────────────────────────────────────────────────────────

def test_monotone_ramp_full_circle_and_wraparound():
    angle = lambda t: (t - 100.0)  # noqa: E731  1 deg/day, 0 -> 360
    cs = scan_quantised_crossings(angle, 12, 100.0, 460.0, rate_bound=1.0)
    assert len(cs) == 12
    assert [c.from_index for c in cs] == list(range(12))
    assert cs[-1].from_index == 11 and cs[-1].to_index == 0   # wrap, not 12
    assert all(0 <= c.from_index < 12 and 0 <= c.to_index < 12 for c in cs)
    assert all(cs[i].jd < cs[i + 1].jd for i in range(len(cs) - 1))


@pytest.mark.parametrize("angle,n,expected", [
    (360.0, 12, 0),      # float residue of `% 360` must not invent division n
    (0.0, 12, 0),
    (359.999, 12, 11),
    (-0.001, 12, 11),
    (30.0, 12, 1),       # exactly on a boundary -> the band being entered
    (720.5, 2, 0),
])
def test_division_index_is_always_in_range(angle, n, expected):
    assert _division_index(angle, n) == expected


def test_degenerate_angle_on_a_boundary_raises_rather_than_hanging():
    """An angle sitting exactly ON a division boundary has zero distance to one,
    so the prune can never fire and the span subdivides to tol. That is a
    degenerate input; it must fail loudly and quickly, not hang."""
    with pytest.raises(RuntimeError, match="max_evaluations"):
        scan_quantised_crossings(lambda t: 360.0, 12, 0.0, 10.0,
                                 rate_bound=1.0, max_evaluations=5000)


def test_negative_angle_normalises():
    cs = scan_quantised_crossings(lambda t: -1.0 + (t - 100.0), 12,
                                  100.0, 102.0, rate_bound=1.0)
    assert len(cs) == 1
    assert cs[0].from_index == 11 and cs[0].to_index == 0


# ── span contract ────────────────────────────────────────────────────────────

def test_empty_and_degenerate_spans():
    angle = lambda t: t  # noqa: E731
    assert scan_quantised_crossings(angle, 12, 5.0, 5.0, rate_bound=1.0) == []
    with pytest.raises(ValueError):
        scan_quantised_crossings(angle, 12, 9.0, 5.0, rate_bound=1.0)


def test_window_inside_one_division_reports_nothing():
    angle = lambda t: 15.0 + 0.1 * (t - 100.0)  # noqa: E731
    assert scan_quantised_crossings(angle, 12, 100.0, 110.0, rate_bound=0.1) == []


def test_split_window_invariant_for_interior_crossings():
    """Scanning [a,b] and [a,m]+[m,b] agree on every crossing not at a split
    point -- the property the masa driver's over-scan relies on."""
    angle = lambda t: (t - 100.0)  # noqa: E731
    whole = scan_quantised_crossings(angle, 12, 100.0, 400.0, rate_bound=1.0)
    left = scan_quantised_crossings(angle, 12, 100.0, 255.0, rate_bound=1.0)
    right = scan_quantised_crossings(angle, 12, 255.0, 400.0, rate_bound=1.0)
    assert [round(c.jd, 4) for c in whole] == \
           [round(c.jd, 4) for c in left + right]


def test_crossing_exactly_at_start_is_not_reported():
    """Documented limitation, pinned so it cannot change silently: the scan sees
    a CHANGE of index, and at start_jd there is nothing to change from. This is
    why masa_scan over-scans instead of trusting the window edge."""
    angle = lambda t: (t - 100.0)  # noqa: E731  crosses 30 at t=130
    at_edge = scan_quantised_crossings(angle, 12, 130.0, 140.0, rate_bound=1.0)
    assert at_edge == []
    before = scan_quantised_crossings(angle, 12, 129.0, 140.0, rate_bound=1.0)
    assert len(before) == 1


# ── argument guards ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("kwargs", [
    {"n_divisions": 0}, {"rate_bound": 0.0}, {"rate_bound": -1.0},
    {"tol_jd": 0.0}, {"initial_step_jd": 0.0}, {"initial_step_jd": -2.0},
    {"max_evaluations": 0},
])
def test_invalid_arguments_raise_rather_than_hang(kwargs):
    base = dict(n_divisions=12, rate_bound=1.0)
    base.update(kwargs)
    n = base.pop("n_divisions")
    with pytest.raises(ValueError):
        scan_quantised_crossings(lambda t: t, n, 0.0, 10.0, **base)


def test_default_initial_step_is_half_a_band_at_the_bounding_rate():
    assert default_initial_step(12, 1.0) == pytest.approx(15.0)
    assert default_initial_step(2, 15.0) == pytest.approx(6.0)


def test_crossing_is_hashable_and_frozen():
    c = Crossing(jd=1.0, from_index=0, to_index=1)
    assert hash(c)
    with pytest.raises(Exception):
        c.jd = 2.0  # type: ignore[misc]
