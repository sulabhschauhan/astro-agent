"""Chandrabala -- transit Moon's house position from natal Moon (instant primitive).

Purpose: classify the transit Moon's current house-from-natal-Moon position as
FAVORABLE or UNFAVORABLE for muhurta/electional use, per the mainstream
Chandrabala convention (AstroSage / Drik Panchang / Muhurta Chintamani
lineage).

LOCKED DECISIONS (P2.3.1):
- Favorable-house enum {1, 3, 6, 7, 10, 11} from natal Moon (Janma Rashi).
  Source: PVR Ch. 26 Section 26.3 "Rasi Gochara Vedha", Table 63, Moon row --
  "1 (5), 3 (9), 6 (12), 7 (2), 10 (4), 11 (8)" (favorable houses outside
  parens; vedha sthanas in parens, see deferral note below). NOT sourced
  from PVR's own Muhurta chapter (Ch. 36) -- PVR's stated Muhurta
  methodology names only Tarabala (nakshatra-based) as a muhurta limb
  (Ch.36 Section 36.3); Table 63 is presented in Ch.26 as general transit
  theory, not as a named Muhurta criterion there. Chandrabala as
  implemented here is the mainstream-Muhurta-lineage criterion (AstroSage
  / Drik Panchang / Muhurta Chintamani convention); PVR Table 63's Moon
  row independently corroborates the favorable-house enum.
- Janma Rashi (house 1, transit Moon back on its own natal sign) is part
  of the FAVORABLE bucket, not a separate category -- matches PVR Table 63
  (house 1 listed as auspicious there). Surfaced via is_janma_rashi: bool
  so the answer-pipeline can name it explicitly without fragmenting the
  enum.
- Binary enum only: FAVORABLE / UNFAVORABLE. No NEUTRAL bucket.
- Vedha-sthana (obstruction) mechanism explicitly DEFERRED to V1.1
  (P2.3.1b) -- mirrors the Small Panoti / Kantaka Shani shelving in
  sade_sati.py (see that module's docstring, "Small Panoti ... explicitly
  OUT OF SCOPE"). PVR's Table 63 vedha-sthana column is not implemented
  here; a favorable house being "obstructed" by another planet's transit
  position is out of scope until P2.3.1b.
- Sign convention: 0-11 (0=Aries..11=Pisces), matching sade_sati.py.
  Deliberately NOT gochara.py's 1-12 convention -- that refactor is not in
  scope for this module. house_from_natal_moon (the only user-facing house
  field) uses classical 1-12 numbering, matching gochara.py's
  house_from_moon naming.
- Ephemeris dependency: independent _moon_sign(jd_ut) helper, NOT a call
  into gochara.compute_gochara() -- avoids a new cross-module dependency
  and an 8-planet computation for a 1-planet need. helpers/ephemeris.py
  consolidation remains tracked as a separate backlog item (Session 19+).
- V1 scope: instant primitive only -- given (natal_moon_sign, transit_jd),
  returns one classification. No range-scan (P2.3.2), no Tarabala/Panchaka
  aggregation hooks.

Range-scan (P2.3.2):
- find_chandrabala_windows(natal_moon_sign, start_jd, end_jd) returns the
  contiguous (category, is_janma_rashi, house_from_natal_moon) windows
  covering [start_jd, end_jd]. Same enum source ladder as the instant
  primitive above (PVR Ch. 26 Table 63 Moon row; AstroSage / Drik
  Panchang / Muhurta Chintamani lineage corroborating) -- vedha-sthana
  remains deferred to V1.1 for the range-scan too.
- Algorithm: discrete-state bisection, the same shape as Skyfield's
  almanac.find_discrete (skyfield itself is NOT a dependency -- the
  algorithm is reimplemented locally against pyswisseph). Coarse scan at
  a fixed, internal-only 0.5 JD (12h) step: Moon's sidereal angular speed
  is ~13 deg/day, so 13 * 0.5 = 6.5 deg < 30 deg (one sign width) --
  no sign ingress can be skipped between two consecutive coarse samples.
  Each detected state change is then bisected down to 1e-6 JD (~0.09s)
  precision, below any meaningful Muhurta time-of-day display precision.
  Both constants are internal; no step/precision parameter is exposed on
  the public surface.
- Unlike sade_sati.py's Saturn-transit scan, the Moon never retrogrades,
  so sign ingress is strictly monotonic forward in time -- no
  retrograde-double-ingress handling (cf. sade_sati.py's
  is_retrograde_split / PhaseWindow.segments) is needed here.
- Bisects on the full (category, is_janma_rashi, house_from_natal_moon)
  triple, not category alone -- house_from_natal_moon changes at every
  Moon sign ingress (~every 2.25 days) even when category doesn't flip,
  and a caller may need to know which favorable/unfavorable house it is,
  not just the binary verdict. In practice the three fields always change
  together (house_from_natal_moon is a bijective function of
  transit_moon_sign for fixed natal_moon_sign), so this is equivalent to
  bisecting on Moon sign ingress directly.
- Reuses compute_chandrabala / _moon_sign from the instant primitive
  above -- no duplicated ephemeris or classification logic.
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

import swisseph as swe

_FAVORABLE_HOUSES = frozenset({1, 3, 6, 7, 10, 11})


class ChandrabalaCategory(Enum):
    FAVORABLE = "FAVORABLE"
    UNFAVORABLE = "UNFAVORABLE"


class EphemerisError(RuntimeError):
    """A pyswisseph ephemeris calculation failed for a specific planet/JD."""

    def __init__(self, jd_ut: float, planet: str, detail: str):
        self.jd_ut = jd_ut
        self.planet = planet
        super().__init__(
            f"compute_chandrabala: ephemeris failure for {planet} at "
            f"jd_ut={jd_ut}: {detail}"
        )


@dataclass(frozen=True)
class ChandrabalaStatus:
    natal_moon_sign: int            # 0=Aries..11=Pisces
    transit_moon_sign: int          # 0=Aries..11=Pisces
    house_from_natal_moon: int      # 1-12, classical house numbering
    category: ChandrabalaCategory
    is_janma_rashi: bool


def _moon_sign(jd_ut: float) -> int:
    """Moon's sidereal sign (0=Aries..11=Pisces) at jd_ut.

    TODO: migrate to helpers/ephemeris.py once that wrapper is built out
    (currently a stub per Session 19); direct swe.calc_ut matches the
    gochara.py / sade_sati.py / navamsa.py convention.
    """
    try:
        xx, ret = swe.calc_ut(jd_ut, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
    except Exception as exc:
        raise EphemerisError(jd_ut, "Moon", str(exc)) from exc
    if ret < 0:
        raise EphemerisError(jd_ut, "Moon", f"retflag={ret}")
    return int((xx[0] % 360.0) / 30.0) % 12


def compute_chandrabala(natal_moon_sign: int, transit_jd: float) -> ChandrabalaStatus:
    """
    Chandrabala: transit Moon's house position counted from natal Moon
    (Janma Rashi), classified FAVORABLE/UNFAVORABLE per the {1,3,6,7,10,11}
    enum (PVR Table 63 Moon row; see module docstring for sourcing and the
    vedha-sthana deferral).

    Args:
        natal_moon_sign: Natal Moon's sidereal sign, 0=Aries..11=Pisces.
        transit_jd: Julian Day (UT) of the moment being evaluated. Trusted,
            not validated (matches sade_sati.py precedent).

    Returns:
        ChandrabalaStatus with both signs, the classical 1-12
        house-from-natal-Moon position, category, and is_janma_rashi.

    Raises:
        ValueError: natal_moon_sign not in 0..11.
        EphemerisError: a pyswisseph calculation failed for the Moon.
    """
    if not (0 <= natal_moon_sign <= 11):
        raise ValueError(f"natal_moon_sign must be in 0..11, got {natal_moon_sign}")

    swe.set_sid_mode(swe.SIDM_LAHIRI)

    transit_moon_sign = _moon_sign(transit_jd)
    house_from_natal_moon = ((transit_moon_sign - natal_moon_sign) % 12) + 1
    category = (
        ChandrabalaCategory.FAVORABLE
        if house_from_natal_moon in _FAVORABLE_HOUSES
        else ChandrabalaCategory.UNFAVORABLE
    )

    return ChandrabalaStatus(
        natal_moon_sign=natal_moon_sign,
        transit_moon_sign=transit_moon_sign,
        house_from_natal_moon=house_from_natal_moon,
        category=category,
        is_janma_rashi=(house_from_natal_moon == 1),
    )


# Coarse-scan step, internal only -- 12 hours. Moon's sidereal angular speed
# is ~13 deg/day; 13 * 0.5 = 6.5 deg < 30 deg (one sign width), so a sign
# ingress cannot be skipped between two consecutive coarse samples. Not a
# function parameter -- see module docstring's Range-scan section.
_COARSE_STEP_JD = 0.5

# Bisection precision, internal only -- ~0.09 seconds. Below any meaningful
# Muhurta time-of-day display precision. Not a function parameter.
_BISECT_TOL_JD = 1e-6


@dataclass(frozen=True)
class ChandrabalaWindow:
    start_jd: float                 # inclusive
    end_jd: float                   # exclusive
    category: ChandrabalaCategory
    is_janma_rashi: bool
    house_from_natal_moon: int


def _bisect_transition(
    t_lo: float,
    t_hi: float,
    state_lo: tuple,
    state_hi: tuple,
    classify: Callable[[float], tuple],
    max_iters: int = 40,
) -> float:
    """Bisects [t_lo, t_hi] -- where classify(t_lo) == state_lo,
    classify(t_hi) == state_hi, and state_lo != state_hi -- down to
    _BISECT_TOL_JD precision, returning the transition JD. Mirrors
    sade_sati.py's _refine_boundary bisection loop, generalized from a
    boolean in_target predicate to tuple-state equality.

    Takes `classify` as an explicit callable rather than relying on a
    closure, unlike find_chandrabala_windows' own nested _classify --
    this is what makes _bisect_transition independently unit-testable
    (see tests/calculations/transits/test_chandrabala_windows.py's
    bisection-convergence test, which mocks _moon_sign directly). Same
    parameter shape as sade_sati.py's _refine_boundary(jd_a, jd_b,
    in_target: Callable[[float], bool]).

    max_iters=40: log2(_COARSE_STEP_JD / _BISECT_TOL_JD) =
    log2(0.5 / 1e-6) ~= 19; 40 is a 2x safety margin, not a tuned or
    load-bearing constant -- by construction (state_lo != state_hi over a
    bracket no wider than one coarse step) convergence happens well
    before 40 iterations.
    """
    lo, hi = t_lo, t_hi
    for _ in range(max_iters):
        if hi - lo < _BISECT_TOL_JD:
            break
        mid = (lo + hi) / 2.0
        if classify(mid) == state_lo:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def find_chandrabala_windows(
    natal_moon_sign: int, start_jd: float, end_jd: float
) -> list[ChandrabalaWindow]:
    """
    Scans [start_jd, end_jd] for contiguous Chandrabala windows -- spans
    where (category, is_janma_rashi, house_from_natal_moon) all stay
    constant. Boundaries are bisected to _BISECT_TOL_JD precision; see
    the module docstring's Range-scan section for the algorithm and
    constant justifications.

    Args:
        natal_moon_sign: Natal Moon's sidereal sign, 0=Aries..11=Pisces.
        start_jd: Julian Day (UT), inclusive lower bound of the scan.
        end_jd: Julian Day (UT), exclusive upper bound of the scan.

    Returns:
        List of ChandrabalaWindow, ordered by time, contiguous and
        gap-free over [start_jd, end_jd] (windows[0].start_jd ==
        start_jd, windows[-1].end_jd == end_jd, windows[i].end_jd ==
        windows[i+1].start_jd). Empty list if start_jd == end_jd.

    Raises:
        ValueError: natal_moon_sign not in 0..11, or start_jd > end_jd.
        EphemerisError: a pyswisseph calculation failed for the Moon.
    """
    if not (0 <= natal_moon_sign <= 11):
        raise ValueError(f"natal_moon_sign must be in 0..11, got {natal_moon_sign}")
    if start_jd > end_jd:
        raise ValueError(f"start_jd ({start_jd}) must be <= end_jd ({end_jd})")
    if start_jd == end_jd:
        return []

    def _classify(jd: float) -> tuple:
        status = compute_chandrabala(natal_moon_sign, jd)
        return status.category, status.is_janma_rashi, status.house_from_natal_moon

    samples_jd = []
    jd = start_jd
    while jd < end_jd:
        samples_jd.append(jd)
        jd += _COARSE_STEP_JD
    if samples_jd[-1] != end_jd:
        samples_jd.append(end_jd)

    states = [_classify(jd) for jd in samples_jd]

    boundary_jds = [start_jd]
    boundary_states = [states[0]]
    for i in range(len(samples_jd) - 1):
        if states[i] != states[i + 1]:
            transition_jd = _bisect_transition(
                samples_jd[i], samples_jd[i + 1], states[i], states[i + 1], _classify
            )
            boundary_jds.append(transition_jd)
            boundary_states.append(states[i + 1])
    boundary_jds.append(end_jd)

    return [
        ChandrabalaWindow(
            start_jd=boundary_jds[i],
            end_jd=boundary_jds[i + 1],
            category=boundary_states[i][0],
            is_janma_rashi=boundary_states[i][1],
            house_from_natal_moon=boundary_states[i][2],
        )
        for i in range(len(boundary_jds) - 1)
    ]
