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
