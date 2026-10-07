"""Generic discrete-state bisection range-scan, extracted from the three
transit modules that independently carried an identical implementation.

Extraction trigger (Session 26): CLAUDE.md's Locked Decisions set the
extraction threshold for the duplicated `_bisect_transition` helper at
three modules. `chandrabala.py` (Session 24), `tarabala.py` (Session 24),
and `panchaka.py` (Session 25) each shipped their own copy; panchaka.py
crossing the threshold is what triggered this module.

Caller audit (Session 26, performed before writing a line of this module):
read `_bisect_transition` plus the surrounding `find_*_windows` assembly
logic in all three modules and compared on five axes -- boundary
semantics (closed start_jd / open end_jd, tie-breaking), behavior under a
constant state across the whole window, behavior when a transition lands
within `tol_jd` of `start_jd`/`end_jd`, behavior on an inverted/empty
window, and state-function exception handling. All three are
byte-for-byte identical on every axis (panchaka.py was deliberately
written to mirror the already-locked chandrabala.py/tarabala.py pattern
the session before this one). The one non-behavioral difference --
chandrabala.py/tarabala.py classify to a 3-tuple, panchaka.py to a bare
enum -- doesn't affect any audited axis, since equality comparison works
identically on tuples and hashable scalars; this is exactly why `T` below
is a `Hashable`-bound TypeVar rather than a fixed tuple shape. Mirrored
from `chandrabala.py`'s `find_chandrabala_windows` / `_bisect_transition`
(arbitrary pick among the three, since the audit found all three
equivalent).

Algorithm: coarse-step sampling over [start_jd, end_jd), forcing end_jd
as the final sample if the step doesn't land on it exactly, followed by
bisection of every coarse-sample-to-coarse-sample state change down to
`tol_jd` precision. Same shape as Skyfield's almanac.find_discrete
(skyfield itself is not a project dependency; this is a local
reimplementation against the caller-supplied `state_fn`).

tol_jd vs. coarse_step_jd -- these are NOT interchangeable knobs:
- `tol_jd` (default 1e-6 JD, ~0.0864 seconds) is a generic JD bisection
  precision floor. It is domain-independent -- the same value used by
  all three audited callers -- and has a sensible default because no
  caller has ever needed a coarser-than-default convergence target.
- `coarse_step_jd` is band-width-dependent (it must be small enough that
  the tracked quantity cannot cross an entire band between two
  consecutive coarse samples -- e.g. chandrabala.py picked 0.5 JD against
  the Moon's ~13 deg/day speed and a 30-degree sign width; tarabala.py
  picked the same 0.5 JD against a narrower 13.333-degree nakshatra
  width; panchaka.py picked the same 0.5 JD against a wider 60-degree
  band). Because the safe step size depends on the caller's own domain,
  it has NO default here and must be supplied by every call site.

`state_fn` exceptions (e.g. an EphemerisError from a caller's ephemeris
lookup) are never caught here -- they propagate to find_state_segments'
caller unchanged, matching all three audited callers (none of which wrap
their classify/state functions in try/except).

Migration note: chandrabala.py, tarabala.py, and panchaka.py are NOT
refactored to call this helper in this task -- out of scope per the
extraction task's own constraints (no edits to those three files). Their
own `_bisect_transition` copies remain live and unchanged; switching them
over to `find_state_segments` is a separate follow-up task.
"""

from collections.abc import Callable, Hashable
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T", bound=Hashable)


@dataclass(frozen=True)
class StateSegment(Generic[T]):
    start_jd: float                 # inclusive
    end_jd: float                   # exclusive
    state: T


def _bisect_transition(
    t_lo: float,
    t_hi: float,
    state_lo: T,
    state_hi: T,
    state_fn: Callable[[float], T],
    tol_jd: float,
    max_iters: int = 40,
) -> float:
    """Bisects [t_lo, t_hi] -- where state_fn(t_lo) == state_lo,
    state_fn(t_hi) == state_hi, and state_lo != state_hi -- down to
    tol_jd precision, returning the transition JD. Identical loop shape
    to the three audited callers' own `_bisect_transition` functions.

    max_iters=40: not exposed on find_state_segments' public surface,
    matching the audited callers (internal-only, not a tuned or
    load-bearing constant -- by construction, convergence happens well
    before 40 iterations for any bracket no wider than one coarse step).
    """
    lo, hi = t_lo, t_hi
    for _ in range(max_iters):
        if hi - lo < tol_jd:
            break
        mid = (lo + hi) / 2.0
        if state_fn(mid) == state_lo:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def find_state_segments(
    state_fn: Callable[[float], T],
    start_jd: float,
    end_jd: float,
    coarse_step_jd: float,
    *,
    tol_jd: float = 1e-6,
) -> list[StateSegment[T]]:
    """
    Scans [start_jd, end_jd) for contiguous StateSegments -- spans where
    state_fn(jd) stays constant. Boundaries are bisected to tol_jd
    precision. See module docstring for the algorithm, the audit that
    justifies this generalization, and the tol_jd-vs-coarse_step_jd
    distinction.

    Args:
        state_fn: maps a Julian Day (UT) to a hashable state value.
            Exceptions propagate uncaught (see module docstring).
        start_jd: Julian Day (UT), inclusive lower bound of the scan.
        end_jd: Julian Day (UT), exclusive upper bound of the scan.
        coarse_step_jd: coarse-scan step, JD. Caller-required -- must be
            small enough that state_fn cannot skip an entire state band
            between two consecutive coarse samples (see module docstring).
        tol_jd: bisection convergence precision, JD. Defaults to 1e-6
            (~0.0864 seconds), matching all three audited callers.

    Returns:
        List of StateSegment, ordered by time, contiguous and gap-free
        over [start_jd, end_jd) (segments[0].start_jd == start_jd,
        segments[-1].end_jd == end_jd, segments[i].end_jd ==
        segments[i+1].start_jd). Empty list if start_jd == end_jd.

    Raises:
        ValueError: start_jd > end_jd.
    """
    if start_jd > end_jd:
        raise ValueError(f"start_jd ({start_jd}) must be <= end_jd ({end_jd})")
    if start_jd == end_jd:
        return []

    samples_jd = []
    jd = start_jd
    while jd < end_jd:
        samples_jd.append(jd)
        jd += coarse_step_jd
    if samples_jd[-1] != end_jd:
        samples_jd.append(end_jd)

    states = [state_fn(jd) for jd in samples_jd]

    boundary_jds = [start_jd]
    boundary_states = [states[0]]
    for i in range(len(samples_jd) - 1):
        if states[i] != states[i + 1]:
            transition_jd = _bisect_transition(
                samples_jd[i], samples_jd[i + 1], states[i], states[i + 1],
                state_fn, tol_jd,
            )
            boundary_jds.append(transition_jd)
            boundary_states.append(states[i + 1])
    boundary_jds.append(end_jd)

    return [
        StateSegment(
            start_jd=boundary_jds[i],
            end_jd=boundary_jds[i + 1],
            state=boundary_states[i],
        )
        for i in range(len(boundary_jds) - 1)
    ]


# ──────────────────────────────────────────────────────────────────────────────
# QUANTISED-ANGLE CROSSING SCAN (S148)
# ──────────────────────────────────────────────────────────────────────────────
# WHY THIS IS NOT find_state_segments WITH AN int() STATE FUNCTION.
# The obvious reuse -- state_fn = floor(angle*n/360) fed to find_state_segments --
# is UNSOUND for this family, and the S148 roster review caught it before any
# code was written (Architect HIGH-1, Critic HIGH-1, QA HIGH-3, independently).
# find_state_segments compares CONSECUTIVE COARSE SAMPLES and then bisects each
# bracket ASSUMING EXACTLY ONE transition inside it. Both halves of that fail here:
#   (a) a body that crosses a division boundary and crosses BACK inside one coarse
#       step leaves both samples in the same band -> ZERO crossings reported, with
#       no error and no way for a consumer to notice. This is precisely the
#       retrograde-station-near-a-cusp case, which is the case this family exists
#       to catch.
#   (b) when a bracket does contain three states (k, k-1, k), _bisect_transition
#       converges on one arbitrary point and labels it with the two ENDPOINT
#       states -- a crossing that never happened, at a time that is not a root.
# combustion_scan.py is safe from (a) only because its episodes are days-to-weeks
# wide and its own docstring states that as an explicit scope guard. Quantised
# ingress has no such floor: band residence near a station is unbounded-small.
#
# THE FIX IS A PROOF, NOT A FINER STEP. No fixed sampling rate can bound (a) --
# the dither window shrinks faster than any constant. So this scanner subdivides
# ADAPTIVELY and prunes a sub-interval only when a crossing inside it is
# ARITHMETICALLY IMPOSSIBLE:
#
#   If angle(t) is reachable-rate-bounded by R (deg/day) on [a, b], and d(a), d(b)
#   are the angular distances from angle(a), angle(b) to their NEAREST division
#   boundary, then any crossing at time tc in [a, b] requires
#       tc - a >= d(a)/R   and   b - tc >= d(b)/R
#   hence  b - a >= (d(a) + d(b)) / R.
#   CONTRAPOSITIVE (the prune):  (b - a) * R < d(a) + d(b)  =>  no crossing in [a, b].
#
# Correctness therefore depends on `rate_bound` being a true upper bound on
# |d(angle)/dt| over the window -- a MEASURED quantity, not a tuned one -- and NOT
# on the step size, which only affects how much work the pruning saves.
# `initial_step_jd` is a performance knob; `rate_bound` is the correctness knob.


@dataclass(frozen=True)
class Crossing:
    """One division-boundary crossing of a quantised angle.

    jd: the crossing instant (UT), resolved to tol_jd.
    from_index / to_index: division indices either side, each in [0, n_divisions).
    NOTE: to_index is NOT always from_index + 1 -- it is from_index - 1 on a
    retrograde crossing, and wraps (11 -> 0, 0 -> 11). Consumers must use modular
    arithmetic, never a +1 assumption.
    """
    jd: float
    from_index: int
    to_index: int


def _division_index(angle_deg: float, n_divisions: int) -> int:
    """Division index of `angle_deg`, always in [0, n_divisions).

    The modulo is load-bearing, not defensive: an angle_fn returning exactly
    360.0 (a common float residue of `x % 360`) would otherwise index
    n_divisions, inventing a phantom division adjacent to 0.
    """
    return int((angle_deg % 360.0) * n_divisions / 360.0) % n_divisions


def _distance_to_boundary(angle_deg: float, n_divisions: int) -> float:
    """Angular distance (deg) from `angle_deg` to its nearest division boundary."""
    band = 360.0 / n_divisions
    within = (angle_deg % 360.0) % band
    return min(within, band - within)


def default_initial_step(n_divisions: int, rate_bound: float) -> float:
    """A starting subdivision granularity: half a band at the bounding rate.

    DERIVED, NOT TUNED, and NOT a safety guarantee -- correctness comes from the
    prune proof above, which holds at any step. This only picks a granularity at
    which most of a window prunes on the first pass. Scope guard: it is an upper
    bound on the first-pass stride, never a floor on resolution.
    """
    return (180.0 / n_divisions) / rate_bound


def scan_quantised_crossings(
    angle_fn: Callable[[float], float],
    n_divisions: int,
    start_jd: float,
    end_jd: float,
    *,
    rate_bound: float,
    initial_step_jd: float | None = None,
    tol_jd: float = 1e-6,
    max_evaluations: int = 2_000_000,
) -> list[Crossing]:
    """Every division-boundary crossing of `angle_fn` in the OPEN span (start, end).

    Parameterised over the angle, so one primitive serves the whole family:
    n_divisions=12 over a graha's sidereal longitude gives sign ingress (the Sun's
    being sankranti); n_divisions=27 gives nakshatra ingress; n_divisions=2 over
    (moon - sun) % 360 gives new moon (-> index 0) and full moon (-> index 1).
    Nothing here is specific to any of them, and this module stays free of
    astronomy -- the caller supplies angle_fn and the rate bound.

    Args:
        angle_fn: Julian Day (UT) -> angle in degrees. Need not be pre-normalised.
            Exceptions propagate uncaught, matching find_state_segments.
        n_divisions: number of equal divisions of the circle. Must be >= 1.
        start_jd / end_jd: scan span, start inclusive / end exclusive in intent.
        rate_bound: a true UPPER BOUND on |d(angle)/dt| in deg/day over the span.
            CORRECTNESS DEPENDS ON THIS. Too small silently drops crossings; too
            large only costs time. Must be > 0. For composed angles the bound is
            the composed rate (elongation -> |moon| + |sun|, not the Moon's alone).
        initial_step_jd: first-pass stride; defaults to default_initial_step().
        tol_jd: resolution. Two crossings closer together than this are reported
            as at most one -- the documented resolution contract.
        max_evaluations: hard ceiling on angle_fn evaluations, as a GUARD not a
            tuning knob. The prune cannot fire on an angle that sits exactly ON a
            division boundary (its distance to one is zero), so such an input
            subdivides the whole span to tol_jd -- 2**24 nodes over ten days at
            the default tolerance. That is a degenerate input, not a normal scan;
            this ceiling turns it into a loud RuntimeError instead of a hang.
            SCOPE GUARD: a real scan of a moving body never approaches it (a year
            of Moon ingresses costs ~1e4). TUNING NOTE: if a legitimate scan ever
            trips it, widen the span's rate bound or coarsen tol_jd -- do not
            raise this to make a degenerate input finish.

    Returns:
        Crossings ordered by jd. A crossing lying exactly AT start_jd is NOT
        reported: the scan can only see a change of index, and at start_jd there
        is no earlier sample to change from. Callers that need a complete set of
        intervals must OVER-SCAN past both ends and trim (see masa_scan.py).

    Raises:
        ValueError: start_jd > end_jd, n_divisions < 1, rate_bound <= 0,
            initial_step_jd <= 0, tol_jd <= 0, or max_evaluations < 1.
        RuntimeError: max_evaluations exceeded (see that argument).
    """
    if n_divisions < 1:
        raise ValueError(f"n_divisions must be >= 1, got {n_divisions}")
    if rate_bound <= 0:
        raise ValueError(f"rate_bound must be > 0, got {rate_bound}")
    if tol_jd <= 0:
        raise ValueError(f"tol_jd must be > 0, got {tol_jd}")
    if max_evaluations < 1:
        raise ValueError(f"max_evaluations must be >= 1, got {max_evaluations}")
    if start_jd > end_jd:
        raise ValueError(f"start_jd ({start_jd}) must be <= end_jd ({end_jd})")
    if start_jd == end_jd:
        return []
    step = default_initial_step(n_divisions, rate_bound) if initial_step_jd is None \
        else initial_step_jd
    if step <= 0:
        raise ValueError(f"initial_step_jd must be > 0, got {step}")

    # Cache: adaptive subdivision revisits the same instants at every level, and
    # angle_fn is an ephemeris read. Without this the scan costs ~3x more.
    cache: dict[float, float] = {}

    def angle_at(t: float) -> float:
        a = cache.get(t)
        if a is None:
            if len(cache) >= max_evaluations:
                raise RuntimeError(
                    f"scan_quantised_crossings exceeded max_evaluations="
                    f"{max_evaluations} over [{start_jd}, {end_jd}) with "
                    f"n_divisions={n_divisions}, rate_bound={rate_bound}, "
                    f"tol_jd={tol_jd}. This usually means angle_fn sits on or "
                    "oscillates about a division boundary, which the prune "
                    "cannot bound; see max_evaluations in the docstring."
                )
            a = angle_fn(t)
            cache[t] = a
        return a

    crossings: list[Crossing] = []
    # Explicit stack rather than recursion: depth is log2(step/tol) ~ 19 at the
    # defaults but is unbounded in principle, and a blown Python stack mid-scan
    # would be a crash, not a bad answer.
    seg_start = start_jd
    while seg_start < end_jd:
        seg_end = min(seg_start + step, end_jd)
        stack: list[tuple[float, float]] = [(seg_start, seg_end)]
        local: list[Crossing] = []
        while stack:
            a, b = stack.pop()
            ang_a, ang_b = angle_at(a), angle_at(b)
            ia = _division_index(ang_a, n_divisions)
            ib = _division_index(ang_b, n_divisions)
            if ia == ib:
                # THE PRUNE (see module note): a crossing out and back needs at
                # least (d(a) + d(b)) / rate_bound of elapsed time.
                reach = (b - a) * rate_bound
                if reach < _distance_to_boundary(ang_a, n_divisions) \
                        + _distance_to_boundary(ang_b, n_divisions):
                    continue
            if b - a <= tol_jd:
                # Resolved. Equal indices here means an excursion narrower than
                # the resolution contract -- not reportable, by definition.
                if ia != ib:
                    local.append(Crossing(jd=(a + b) / 2.0,
                                          from_index=ia, to_index=ib))
                continue
            mid = (a + b) / 2.0
            stack.append((mid, b))   # pushed first so (a, mid) pops first
            stack.append((a, mid))
        crossings.extend(local)
        seg_start = seg_end

    crossings.sort(key=lambda c: c.jd)
    return crossings
