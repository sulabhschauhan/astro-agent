"""Sade Sati and Dhaiya — Saturn transit over natal Moon.

Purpose: detect current Sade Sati status from natal Moon sign.

LOCKED DECISIONS (Session 20):
- Boundaries computed from natal Moon SIGN (Janma Rashi), NOT nakshatra.
  Matches BPHS, AstroSage, Prokerala, Drik Panchang, mainstream Indian
  astrologer convention (KN Rao, BV Raman, Sanjay Rath). Nakshatra-based
  Sade Sati is essentially absent from mainstream practice.
- Phase taxonomy:
    NONE     -- Saturn not in 12/1/2 from natal Moon
    RISING   -- Saturn in 12th from Moon (Dhaiya 1)
    PEAK     -- Saturn in 1st from Moon (Dhaiya 2, Janma Shani)
    SETTING  -- Saturn in 2nd from Moon (Dhaiya 3)
- Small Panoti / Kantaka Shani (Saturn 4th or 8th from Moon) is explicitly
  OUT OF SCOPE for P2.2.2 -- collapses to phase=NONE rather than a
  dedicated tag. Revisit only if user pressure surfaces.

LOCKED DECISIONS (P2.2.2, this implementation):
- Retrograde-induced double-ingress is mainline, not an edge case --
  confirmed across both reference-chart fixtures (Sheridan, Surbhi), each
  showing a Pisces-Aries-Pisces oscillation at the live RISING/PEAK
  boundary. PhaseWindow.segments carries every contiguous occupancy of the
  current phase sign found in the scan window; is_retrograde_split is True
  whenever more than one segment is found.
- current_phase_window is built from a +-2 year daily-resolution scan
  around transit_jd; macro_sade_sati (the ~7.5y RISING->PEAK->SETTING
  envelope) is built from a +-10 year scan. Both are wide enough to fully
  bracket Saturn's slow transit of 1 (current_phase_window) or 3
  (macro_sade_sati) contiguous signs without window-edge truncation, given
  Saturn's ~29.5y orbital period keeps any unrelated prior/next cycle well
  outside either window.
- Boundary refinement: direct boolean bisection on the sign-membership
  predicate (no explicit degree-boundary algebra needed), to <60s
  precision. Mirrors the bisection pattern in chart_calculator.py's
  calculate_solar_return.
- Anchor convention: inherits gochara.py's provisional 18:30 UTC (00:00
  IST next-day) transit-fixture anchor -- see gochara.py's module
  docstring and test_gochara.py's ANCHOR CONVENTION note. If transit_jd
  lands within 60s of a phase boundary, this module reports whichever
  side of the boundary transit_jd falls on; it does not resolve which
  anchor convention is "correct".

Ephemeris dependency (Session 52 migration): _saturn_sign(jd_ut) delegates
to helpers/ephemeris.py's sidereal_longitude(); the module's own
EphemerisError is now an alias for ephemeris.EphemerisError. Performance
note: the +-2y/+-10y window scans in _find_segments call _saturn_sign
(and therefore the helper's per-call swe.set_sid_mode) thousands of times
per compute_sade_sati() call -- deliberately left uncached/unhoisted per
CLAUDE.md YAGNI guidance; set_sid_mode is a cheap C call and full-suite
timing showed no meaningful regression from this migration.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

import swisseph as swe

from agent.calculations.helpers import ephemeris

_YEAR_DAYS = 365.25
_PHASE_SCAN_YEARS = 2
_MACRO_SCAN_YEARS = 10
_TOL_DAYS = 60.0 / 86400.0  # 60 seconds, matching the <60s boundary precision spec
_MAX_BISECT_ITER = 50


# Session 52 migration: delegates to helpers/ephemeris.py's canonical
# EphemerisError rather than keeping a module-local copy.
EphemerisError = ephemeris.EphemerisError


class BoundaryRefinementError(RuntimeError):
    """Bisection failed to converge on a sign-boundary crossing."""

    def __init__(self, jd_lo: float, jd_hi: float, detail: str = ""):
        self.jd_lo = jd_lo
        self.jd_hi = jd_hi
        msg = (
            f"compute_sade_sati: boundary refinement did not converge in "
            f"range [{jd_lo}, {jd_hi}]"
        )
        if detail:
            msg += f": {detail}"
        super().__init__(msg)


@dataclass(frozen=True)
class PhaseWindow:
    first_ingress_jd: float
    final_exit_jd: float
    segments: tuple[tuple[float, float], ...]  # immutable, ordered
    is_retrograde_split: bool


@dataclass(frozen=True)
class MacroSadeSati:
    overall_start_jd: float
    overall_end_jd: float


@dataclass(frozen=True)
class SadeSatiStatus:
    active: bool
    phase: Literal["RISING", "PEAK", "SETTING", "NONE"]
    saturn_sign: int               # 0=Aries..11=Pisces
    natal_moon_sign: int
    current_phase_window: PhaseWindow | None    # None when phase=NONE
    macro_sade_sati: MacroSadeSati | None        # None when not in 7.5y envelope


def _saturn_sign(jd_ut: float) -> int:
    """Saturn's sidereal sign (0=Aries..11=Pisces) at jd_ut.

    Delegates to helpers/ephemeris.py's sidereal_longitude() (Session 52
    migration) for the underlying swe.calc_ut convention. Called
    thousands of times per multi-year window scan (_find_segments); the
    helper's per-call set_sid_mode is a cheap C call, so this is
    deliberately not cached or hoisted (see module docstring's
    performance note).
    """
    return int(ephemeris.sidereal_longitude(jd_ut, swe.SATURN) / 30.0) % 12


def _phase_for_diff(diff: int) -> Literal["RISING", "PEAK", "SETTING", "NONE"]:
    """diff = (saturn_sign - natal_moon_sign) % 12 -- the house-from-Moon
    position minus 1 (0 = 1st-from-Moon/Janma Rashi, 11 = 12th-from-Moon).
    """
    if diff == 11:
        return "RISING"
    if diff == 0:
        return "PEAK"
    if diff == 1:
        return "SETTING"
    # diff in (3, 7): Small Panoti / Kantaka Shani (Saturn 4th/8th from
    # Moon) -- explicitly out of scope for P2.2.2; not a distinct phase.
    return "NONE"


def _refine_boundary(jd_a: float, jd_b: float, in_target: Callable[[float], bool]) -> float:
    """Bisects a ~1-day bracket [jd_a, jd_b] where in_target(jd_a) !=
    in_target(jd_b) down to <60s precision. Direction-agnostic -- works for
    both ingress and egress crossings since it only tracks which side of
    the boundary each endpoint is on, not the sign of a degree offset.
    """
    lo, hi = jd_a, jd_b
    lo_state = in_target(lo)
    for _ in range(_MAX_BISECT_ITER):
        if hi - lo < _TOL_DAYS:
            return (lo + hi) / 2.0
        mid = (lo + hi) / 2.0
        if in_target(mid) == lo_state:
            lo = mid
        else:
            hi = mid
    raise BoundaryRefinementError(jd_a, jd_b, "did not converge after 50 iterations")


def _find_segments(
    scan_lo_jd: float, scan_hi_jd: float, in_target: Callable[[float], bool]
) -> list[tuple[float, float]]:
    """Daily-resolution scan over [scan_lo_jd, scan_hi_jd]; collapses
    contiguous in_target() runs into boundary-refined (entry_jd, exit_jd)
    segments, ordered by time. A run touching the scan window's edge has no
    bracket to refine against, so it falls back to the raw edge JD.
    """
    n_days = int(scan_hi_jd - scan_lo_jd) + 1
    days = [scan_lo_jd + i for i in range(n_days)]
    flags = [in_target(d) for d in days]

    segments: list[tuple[float, float]] = []
    i = 0
    n = len(days)
    while i < n:
        if not flags[i]:
            i += 1
            continue
        run_start = i
        while i < n and flags[i]:
            i += 1
        run_end = i - 1

        entry_jd = (
            days[0] if run_start == 0
            else _refine_boundary(days[run_start - 1], days[run_start], in_target)
        )
        exit_jd = (
            days[n - 1] if run_end == n - 1
            else _refine_boundary(days[run_end], days[run_end + 1], in_target)
        )
        segments.append((entry_jd, exit_jd))
    return segments


def compute_sade_sati(natal_moon_sign: int, transit_jd: float) -> SadeSatiStatus:
    """
    Sade Sati from natal Moon SIGN (locked: not nakshatra).
    Phases: RISING = Saturn in 12th from Moon
            PEAK   = Saturn in 1st from Moon
            SETTING = Saturn in 2nd from Moon
            NONE   = Saturn outside 12/1/2 from Moon at transit_jd

    Phase is determined by Saturn's actual sign at transit_jd. No fudging
    for narrative continuity across retrograde gaps.

    Args:
        natal_moon_sign: Natal Moon's sidereal sign, 0=Aries..11=Pisces.
        transit_jd: Julian Day (UT) of the moment being evaluated.

    Returns:
        SadeSatiStatus with phase, Saturn's current sign, and (when active)
        the current PhaseWindow and the macro 7.5y MacroSadeSati envelope.

    Raises:
        ValueError: natal_moon_sign not in 0..11.
        EphemerisError: a pyswisseph calculation failed for Saturn.
        BoundaryRefinementError: bisection failed to converge on a
            sign-boundary crossing.
    """
    if not (0 <= natal_moon_sign <= 11):
        raise ValueError(f"natal_moon_sign must be in 0..11, got {natal_moon_sign}")

    swe.set_sid_mode(swe.SIDM_LAHIRI)

    saturn_sign = _saturn_sign(transit_jd)
    diff = (saturn_sign - natal_moon_sign) % 12
    phase = _phase_for_diff(diff)
    active = phase != "NONE"

    rising_sign = (natal_moon_sign - 1) % 12
    setting_sign = (natal_moon_sign + 1) % 12

    # Scoped per-boundary-sign, NOT as one combined 3-sign envelope block:
    # a mid-cycle retrograde dip out of the *current* phase sign can pass
    # through a sign outside the 3-sign set (e.g. Pisces -> Aries -> Pisces
    # when Aries is not part of this native's envelope), which would
    # falsely truncate a combined-block scan at that gap. Scanning
    # rising_sign and setting_sign independently and taking the earliest
    # entry / latest exit sidesteps that, and matches the task wording
    # directly ("first ingress into 12th-from-Moon ... final exit from
    # 2nd-from-Moon").
    #
    # Computed unconditionally (not just when active): macro_sade_sati
    # reflects the whole multi-year envelope, including the brief
    # retrograde excursions outside {rising, peak, setting} that occur
    # *within* that envelope (Test 3 case) -- gating is "does this window
    # contain transit_jd", independent of the instantaneous phase.
    macro_scan_lo = transit_jd - _MACRO_SCAN_YEARS * _YEAR_DAYS
    macro_scan_hi = transit_jd + _MACRO_SCAN_YEARS * _YEAR_DAYS
    rising_segments = _find_segments(
        macro_scan_lo, macro_scan_hi, lambda jd: _saturn_sign(jd) == rising_sign
    )
    setting_segments = _find_segments(
        macro_scan_lo, macro_scan_hi, lambda jd: _saturn_sign(jd) == setting_sign
    )
    macro_sade_sati = None
    if rising_segments and setting_segments:
        overall_start_jd = rising_segments[0][0]
        overall_end_jd = setting_segments[-1][1]
        if overall_start_jd <= transit_jd <= overall_end_jd:
            macro_sade_sati = MacroSadeSati(
                overall_start_jd=overall_start_jd,
                overall_end_jd=overall_end_jd,
            )
    # else: no rising/setting occupancy at all in the +-10y scan -- this
    # transit_jd is genuinely between Sade Sati cycles (~29.5y apart, so a
    # 20y window can legitimately miss both edges). Not an error; leaves
    # macro_sade_sati=None.

    if not active:
        return SadeSatiStatus(
            active=False,
            phase="NONE",
            saturn_sign=saturn_sign,
            natal_moon_sign=natal_moon_sign,
            current_phase_window=None,
            macro_sade_sati=macro_sade_sati,
        )

    target_sign = saturn_sign  # the sign currently producing this phase

    phase_scan_lo = transit_jd - _PHASE_SCAN_YEARS * _YEAR_DAYS
    phase_scan_hi = transit_jd + _PHASE_SCAN_YEARS * _YEAR_DAYS
    phase_segments = _find_segments(
        phase_scan_lo, phase_scan_hi, lambda jd: _saturn_sign(jd) == target_sign
    )
    current_phase_window = PhaseWindow(
        first_ingress_jd=phase_segments[0][0],
        final_exit_jd=phase_segments[-1][1],
        segments=tuple(phase_segments),
        is_retrograde_split=len(phase_segments) > 1,
    )

    return SadeSatiStatus(
        active=True,
        phase=phase,
        saturn_sign=saturn_sign,
        natal_moon_sign=natal_moon_sign,
        current_phase_window=current_phase_window,
        macro_sade_sati=macro_sade_sati,
    )
