"""Combustion (Asta) WINDOW scan over a forward time range (V1.5, S147).

Where core/combustion.py answers "is planet X combust AT this (natal) moment?",
this answers "over [start_jd, end_jd), WHICH spans is planet X combust?" -- the
interval form the dated timeline store needs. It is the transit-mode companion
to the point-wise natal engine, and it is CHART-INDEPENDENT: combustion depends
only on Sun-planet separation, so these intervals are the same for every chart.
Chart-relative relevance (which combust planet matters for a given question) is
applied downstream, never here.

ASSEMBLY, not new astronomy -- three oracle-validated parts are reused:
  * core.combustion._ORB_DIRECT / _ORB_RETRO / _min_separation -- the SINGLE
    source of truth for the Surya-Siddhanta orbs (citation + PVR-silence
    fall-through live in that module; do NOT duplicate the table here).
  * helpers.ephemeris.sidereal_longitude / sidereal_position -- Lahiri sidereal
    longitude, and signed daily speed so retrograde is read LIVE from the
    ephemeris (speed < 0), NOT from natal chart_data. This is the one semantic
    difference from the natal engine: at a transit moment there is no natal
    retrograde flag to read, so the sign of the speed decides the orb.
  * helpers.discrete_scan.find_state_segments -- the bisection range-scanner the
    three transit modules already use; we pass it a combust/not-combust
    predicate and keep the True segments.

THE ONE NEW PIECE is `_is_combust_at` -- the transit-mode predicate. Everything
else is wiring.

MOON IS EXCLUDED (Parashara + core/combustion.py's own V1 note): lunar
"combustion" is amavasya, recurring ~monthly and already carried by the
panchanga / tithi layer -- including it here double-penalises the new-Moon. The
five taragrahas (Mars, Mercury, Jupiter, Venus, Saturn) are scanned. Excluding
the Moon also removes the fastest-flipping body, which is what makes the coarse
step below safe.

Python 3.11.
"""
from __future__ import annotations

import logging

import swisseph as swe

from agent.calculations.helpers import ephemeris
from agent.calculations.helpers.discrete_scan import find_state_segments
# Single source of truth for the citation-grounded orbs -- imported, never
# duplicated. Underscore names are intentional reuse of core/combustion.py's
# validated table; keeping them there avoids a second place to drift.
from agent.calculations.core.combustion import (
    _ORB_DIRECT, _ORB_RETRO, _min_separation,
)

logger = logging.getLogger(__name__)

__all__ = ["scan_combustion_windows", "COARSE_STEP_JD", "TARAGRAHA_SWE_IDS"]

# Coarse-scan step for find_state_segments (THRESHOLD, S147). 0.5 JD (12h)
# mirrors the three validated transit scanners (chandrabala/tarabala/panchaka).
# Justification: the narrowest combust episode among the five taragrahas is
# Mercury's (orb 14 deg / 12 deg retro, Mercury-Sun relative motion), lasting
# days-to-weeks -- an order of magnitude wider than this step, so no episode
# edge can be skipped between two samples. Scope guard: this holds ONLY because
# the Moon (a ~2-day combust episode) is excluded; re-adding a fast body REQUIRES
# tightening this. Tuning note: shrink toward 0.125 if a future body's episode
# approaches ~1 day; the scan is a one-time per-window build, so finer is cheap.
COARSE_STEP_JD = 0.5

# The five taragrahas scanned (Moon excluded -- see module docstring). Sun is the
# reference body, never combust; Rahu/Ketu have no disc, out of scope.
TARAGRAHA_SWE_IDS: dict[str, int] = {
    "mars": swe.MARS, "mercury": swe.MERCURY, "jupiter": swe.JUPITER,
    "venus": swe.VENUS, "saturn": swe.SATURN,
}


def _orb_for(planet_name: str, retrograde: bool) -> float:
    """Orb in force for `planet_name` given its live retrograde state.

    Mirrors core/combustion.py line-for-line: only Mercury and Venus narrow
    their orb when retrograde (the _ORB_RETRO keys); every other planet keeps
    its direct orb regardless. core/combustion.py keys its orb tables by
    Capitalised name while lowercasing its OUTPUT, so we take lowercase planet
    names (the output convention) and capitalise only to index the reused table.
    """
    key = planet_name.capitalize()
    if retrograde and key in _ORB_RETRO:
        return _ORB_RETRO[key]
    return _ORB_DIRECT[key]


def _is_combust_at(jd_ut: float, planet_name: str, pid: int) -> bool:
    """Transit-mode combustion predicate: is `planet_name` combust at `jd_ut`?

    The sole new logic in this module. Reads Sun + planet sidereal longitude and
    the planet's signed speed from the shared ephemeris wrapper, derives
    retrograde from the sign of the speed (the transit-mode substitute for a
    natal retrograde flag), and applies the reused orb table. Total over the
    scan: EphemerisError propagates (find_state_segments does not catch it), so a
    bad ephemeris read fails the build loudly rather than silently dropping a
    window -- caught and downgraded to fail-soft one level up, at the composer.
    """
    sun_lon = ephemeris.sidereal_longitude(jd_ut, swe.SUN)
    pos = ephemeris.sidereal_position(jd_ut, pid)
    retrograde = pos.speed < 0.0
    separation = _min_separation(pos.longitude, sun_lon)
    return separation < _orb_for(planet_name, retrograde)


def scan_combustion_windows(
    start_jd: float,
    end_jd: float,
    *,
    coarse_step_jd: float = COARSE_STEP_JD,
    planets: dict[str, int] | None = None,
) -> dict:
    """Combust intervals for each taragraha over [start_jd, end_jd).

    Args:
        start_jd: Julian Day (UT), inclusive lower bound.
        end_jd: Julian Day (UT), exclusive upper bound.
        coarse_step_jd: see COARSE_STEP_JD. Overridable for tests/tuning.
        planets: {name: swe_id} to scan; defaults to the five taragrahas.

    Returns:
        {
          "scanned": {"start_jd", "end_jd", "planets": [names]},
          "intervals": [ {"planet", "start_jd", "end_jd", "retrograde_at_mid"} ]
        }
        intervals are time-ordered within each planet and concatenated planet by
        planet; each is a maximal span where the planet is continuously combust.
        An empty list means no taragraha is combust anywhere in the window.

    Raises:
        ValueError: start_jd > end_jd (propagated from find_state_segments).
        ephemeris.EphemerisError: a pyswisseph read failed mid-scan.
    """
    planets = planets or TARAGRAHA_SWE_IDS
    intervals: list[dict] = []
    for name, pid in planets.items():
        # find_state_segments wants a hashable state; bool is_combust is enough.
        segments = find_state_segments(
            lambda jd, _n=name, _p=pid: _is_combust_at(jd, _n, _p),
            start_jd, end_jd, coarse_step_jd,
        )
        for seg in segments:
            if seg.state:  # keep only the combust spans
                mid = (seg.start_jd + seg.end_jd) / 2.0
                retro_mid = ephemeris.sidereal_position(mid, pid).speed < 0.0
                intervals.append({
                    "planet": name,
                    "start_jd": seg.start_jd,
                    "end_jd": seg.end_jd,
                    "retrograde_at_mid": retro_mid,
                })
    return {
        "scanned": {"start_jd": start_jd, "end_jd": end_jd,
                    "planets": list(planets.keys())},
        "intervals": intervals,
    }
