"""Panchaka -- transit Moon's zodiacal longitude band classification (instant primitive).

Purpose: classify whether the transit Moon's current sidereal longitude
falls inside the classical "Panchaka" (five-nakshatra) inauspicious band,
for muhurta/electional use. Unlike Chandrabala and Tarabala, Panchaka is
NOT natal-relative -- it depends only on the Moon's position against the
fixed zodiac, so this module has no natal-chart parameter anywhere on its
public surface.

LOCKED DECISIONS (P2.3.4):
- Definition B locked: Panchaka as a fixed sidereal-longitude band
  [_PANCHAK_START_DEG, _PANCHAK_END_DEG) = [300, 360) degrees -- the last
  60 degrees of the zodiac (Aquarius + Pisces). Source: Muhurtha-
  Chinthamani p.84 ("As long as the Moon remains in the Ascendants [signs]
  of Aquarius and Pisces ... the deeds like the cremation [of a dead body,
  southward journeys, weaving a cot, thatching a house] should not be
  done"), which states this round-sign framing in the same breath as the
  nakshatra-pada-exact framing below -- the source treats the two as
  equivalent glosses of the same window, not as competing definitions.
- Definition A (nakshatra-pada-exact: from Dhanishtha's 3rd pada,
  ~293d20m, through the end of Revati, 360d -- "the 5 Nakshtras from
  Dhanishtha to Rewati are referred to as 'Panchaka'", same Muhurtha-
  Chinthamani p.84 passage) is NOT implemented. The ~6d40m gap between
  293d20m and the round 300-degree sign boundary is real and unreconciled
  -- locked out for V1 as a round-degree simplification (same
  risk-accepted-for-simplicity shape as chandrabala.py's vedha-sthana
  deferral). V1.1 candidate if classical-fidelity demand emerges.
- Binary category only: PANCHAK / NOT_PANCHAK. No NEUTRAL bucket -- matches
  chandrabala.py / tarabala.py's binary-only precedent.
- Named-type sub-classification (mainstream popular-Muhurta convention
  labels a Panchaka occurrence by the weekday it begins on -- e.g.
  Agni/Raj/Mrityu/Chor/Roga Panchaka) is explicitly OUT OF SCOPE for V1 --
  not sourced from this project's classical-text RAG corpus, and not
  needed for the binary calculation-engine surface this phase targets.
- Panchaka Rahita (the remedial/pacification-exception layer -- Muhurtha-
  Chinthamani p.85's "the pacification of the Panchakas should be done as
  per the rules prescribed in the Shastras" when an activity cannot be
  avoided, and p.309-310's activity-specific Nakshatra exceptions for
  house construction) is explicitly OUT OF SCOPE for V1. This module
  returns a classification only, never remedial guidance.
- No natal parameter: Panchaka depends solely on the transit Moon's
  longitude against the fixed zodiac, not on any natal chart value --
  structurally distinct from chandrabala.py / tarabala.py, both of which
  take a natal_* parameter. compute_panchaka(jd_ut) and
  find_panchaka_windows(start_jd, end_jd) take no natal argument anywhere.
- Ephemeris dependency: independent _moon_sidereal_longitude(jd_ut) helper,
  not cross-imported from chandrabala.py's _moon_sign() or tarabala.py's
  _moon_nakshatra() -- same cross-module-coupling avoidance rationale as
  those two modules.

Range-scan (P2.3.4 continued):
- find_panchaka_windows(start_jd, end_jd) returns the contiguous
  PanchakaWindow list covering [start_jd, end_jd]. Algorithm: the same
  discrete-state bisection shape as chandrabala.py's
  find_chandrabala_windows / tarabala.py's find_tarabala_windows (itself
  mirroring Skyfield's almanac.find_discrete; skyfield is NOT a
  dependency). Reimplemented independently in this module --
  _bisect_transition is NOT imported from chandrabala.py or tarabala.py,
  same cross-module-coupling rationale as the ephemeris helper above.
  Coarse scan at a fixed, internal-only 0.5 JD (12h) step: Moon's sidereal
  angular speed is ~13 deg/day, so 13 * 0.5 = 6.5 deg, well under the
  60-degree Panchak band width -- no entry/exit can be skipped between two
  consecutive coarse samples (wider safety margin than chandrabala.py's
  30-degree sign width or tarabala.py's 13.333-degree nakshatra width).
  Each detected state change is then bisected down to 1e-6 JD (~0.09s)
  precision, same constant value as chandrabala.py / tarabala.py.
- Unlike sade_sati.py's Saturn-transit scan, the Moon never retrogrades, so
  Panchak entry/exit is strictly monotonic forward in time -- no
  retrograde-double-ingress handling is needed here, same as
  chandrabala.py / tarabala.py.
- Bisects on PanchakaCategory alone, not a composite tuple -- unlike
  chandrabala.py's (category, is_janma_rashi, house_from_natal_moon)
  triple or tarabala.py's (category, is_janma_tara, tara_number) triple,
  PanchakaStatus carries no auxiliary natal-relative fields, so there is
  nothing else to bisect on. _bisect_transition's state parameters are
  typed PanchakaCategory directly, not tuple.
- This is the THIRD module to carry an independently-duplicated
  _bisect_transition (chandrabala.py, tarabala.py, panchaka.py) -- per
  CLAUDE.md's Locked Decisions ("extraction threshold set at three
  modules"), this triggers helpers/discrete_scan.py extraction as a
  separate follow-up task, not folded into this implementation.
- Reuses compute_panchaka / _moon_sidereal_longitude from the instant
  primitive above -- no duplicated ephemeris or classification logic.
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

import swisseph as swe

_PANCHAK_START_DEG = 300.0   # inclusive
_PANCHAK_END_DEG = 360.0     # exclusive


class PanchakaCategory(Enum):
    PANCHAK = "PANCHAK"
    NOT_PANCHAK = "NOT_PANCHAK"


class EphemerisError(RuntimeError):
    """A pyswisseph ephemeris calculation failed for a specific planet/JD."""

    def __init__(self, jd_ut: float, planet: str, detail: str):
        self.jd_ut = jd_ut
        self.planet = planet
        super().__init__(
            f"compute_panchaka: ephemeris failure for {planet} at "
            f"jd_ut={jd_ut}: {detail}"
        )


@dataclass(frozen=True)
class PanchakaStatus:
    jd_ut: float
    moon_longitude: float          # sidereal degrees, [0, 360)
    category: PanchakaCategory


def _moon_sidereal_longitude(jd_ut: float) -> float:
    """Moon's sidereal longitude (degrees, [0, 360)) at jd_ut.

    TODO: migrate to helpers/ephemeris.py once that wrapper is built out
    (currently a stub per Session 19); direct swe.calc_ut matches the
    chandrabala.py / tarabala.py / gochara.py / sade_sati.py / navamsa.py
    convention.
    """
    try:
        xx, ret = swe.calc_ut(
            jd_ut, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        )
    except Exception as exc:
        raise EphemerisError(jd_ut, "Moon", str(exc)) from exc
    if ret < 0:
        raise EphemerisError(jd_ut, "Moon", f"retflag={ret}")
    return xx[0] % 360.0


def compute_panchaka(jd_ut: float) -> PanchakaStatus:
    """
    Panchaka: transit Moon's sidereal longitude classified PANCHAK /
    NOT_PANCHAK against the fixed [_PANCHAK_START_DEG, _PANCHAK_END_DEG)
    band (see module docstring for Definition B sourcing and the
    Definition A / named-type / Panchaka-Rahita deferrals).

    Args:
        jd_ut: Julian Day (UT) of the moment being evaluated. Trusted,
            not validated (matches chandrabala.py / tarabala.py
            precedent).

    Returns:
        PanchakaStatus with jd_ut, moon_longitude, and category. No natal
        parameter -- Panchaka is not natal-relative (see module
        docstring).

    Raises:
        EphemerisError: a pyswisseph calculation failed for the Moon.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    moon_longitude = _moon_sidereal_longitude(jd_ut)
    category = (
        PanchakaCategory.PANCHAK
        if _PANCHAK_START_DEG <= moon_longitude < _PANCHAK_END_DEG
        else PanchakaCategory.NOT_PANCHAK
    )

    return PanchakaStatus(
        jd_ut=jd_ut,
        moon_longitude=moon_longitude,
        category=category,
    )


# Coarse-scan step, internal only -- 12 hours. Moon's sidereal angular speed
# is ~13 deg/day; 13 * 0.5 = 6.5 deg, well under the 60-degree Panchak band
# width -- no Panchak entry/exit can be skipped between two consecutive
# coarse samples (wider safety margin than chandrabala.py's 30-degree sign
# width or tarabala.py's 13.333-degree nakshatra width). Same value as both
# sibling modules; independently justified here against the wider band. Not
# a function parameter -- see module docstring's Range-scan section.
_COARSE_STEP_JD = 0.5

# Bisection precision, internal only -- ~0.09 seconds. Below any meaningful
# Muhurta time-of-day display precision. Same value as chandrabala.py /
# tarabala.py. Not a function parameter.
_BISECT_TOL_JD = 1e-6


@dataclass(frozen=True)
class PanchakaWindow:
    start_jd: float                 # inclusive
    end_jd: float                   # exclusive
    category: PanchakaCategory


def _bisect_transition(
    t_lo: float,
    t_hi: float,
    state_lo: PanchakaCategory,
    state_hi: PanchakaCategory,
    classify: Callable[[float], PanchakaCategory],
    max_iters: int = 40,
) -> float:
    """Bisects [t_lo, t_hi] -- where classify(t_lo) == state_lo,
    classify(t_hi) == state_hi, and state_lo != state_hi -- down to
    _BISECT_TOL_JD precision, returning the transition JD. Independently
    reimplemented (not imported) from chandrabala.py's / tarabala.py's
    functions of the same name -- see module docstring's
    cross-module-coupling rationale.

    NOTE: third module carrying this duplicated helper (chandrabala.py,
    tarabala.py, panchaka.py). Triggers helpers/discrete_scan.py
    extraction -- separate task per Session 25 scope (see module
    docstring's Range-scan section).

    State is typed PanchakaCategory directly, not a tuple -- unlike
    chandrabala.py / tarabala.py, PanchakaStatus has no auxiliary
    natal-relative fields to bisect on alongside category.

    Takes `classify` as an explicit callable rather than relying on a
    closure, so this function is independently unit-testable -- same
    rationale as chandrabala.py / tarabala.py's functions of the same
    name.

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


def find_panchaka_windows(start_jd: float, end_jd: float) -> list[PanchakaWindow]:
    """
    Scans [start_jd, end_jd] for contiguous Panchaka windows -- spans
    where category stays constant. Boundaries are bisected to
    _BISECT_TOL_JD precision; see the module docstring's Range-scan
    section for the algorithm and constant justifications.

    Args:
        start_jd: Julian Day (UT), inclusive lower bound of the scan.
        end_jd: Julian Day (UT), exclusive upper bound of the scan.

    Returns:
        List of PanchakaWindow, ordered by time, contiguous and gap-free
        over [start_jd, end_jd] (windows[0].start_jd == start_jd,
        windows[-1].end_jd == end_jd, windows[i].end_jd ==
        windows[i+1].start_jd). Empty list if start_jd == end_jd. No
        natal parameter -- Panchaka is not natal-relative (see module
        docstring).

    Raises:
        ValueError: start_jd > end_jd.
        EphemerisError: a pyswisseph calculation failed for the Moon.
    """
    if start_jd > end_jd:
        raise ValueError(f"start_jd ({start_jd}) must be <= end_jd ({end_jd})")
    if start_jd == end_jd:
        return []

    def _classify(jd: float) -> PanchakaCategory:
        return compute_panchaka(jd).category

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
        PanchakaWindow(
            start_jd=boundary_jds[i],
            end_jd=boundary_jds[i + 1],
            category=boundary_states[i],
        )
        for i in range(len(boundary_jds) - 1)
    ]
