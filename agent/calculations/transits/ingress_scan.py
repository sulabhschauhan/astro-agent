"""Divisional ingress scan -- WHEN a graha crosses into the next sign/nakshatra.

Where `gochara.compute_gochara` answers "where is every graha AT this instant?",
this answers "over [start_jd, end_jd), WHEN does graha X change division?" -- the
interval/event form the dated timeline store needs. It is the general engine the
S147 carry-forward asked for: `sade_sati.py` already searched boundaries, but only
Saturn's, and only for its own phase logic.

CHART-INDEPENDENT. An ingress instant depends on the graha and the ayanamsa, never
on a natal chart; the same table serves every chart. Which ingress MATTERS for a
given person (Saturn into their 7th) is a chart-relative question applied
downstream, never here.

ASSEMBLY, not new astronomy:
  * helpers.ephemeris.sidereal_longitude / sidereal_position -- the single Lahiri
    wrapper, with signed speed.
  * helpers.discrete_scan.scan_quantised_crossings -- the S148 adaptive scanner,
    whose prune proof is what makes a near-station cusp crossing findable at all
    (see that module's note; the naive state-sampling approach drops them).
The only thing this module adds is binding a swisseph body id to an angle
function and supplying its MEASURED rate bound.

RATE BOUNDS ARE MEASURED, NOT REMEMBERED. `MAX_ABS_SPEED_DEG_PER_DAY` below was
produced by sampling |speed| for each body at 0.5-day steps across 2010-2040 on
this ephemeris and taking the maximum, then padding (see the constant's note).
The scanner's correctness -- not merely its cost -- depends on these being true
upper bounds, so they are recorded as a measurement with its window, and are
re-derivable by `scripts/measure_ephemeris_rates.py`.

AYANAMSA: Lahiri (nirayana), inherited from helpers/ephemeris.py, which hardcodes
it. Every result carries `ayanamsa` and `nirayana` in its `scanned` block rather
than leaving the frame implicit -- an ingress instant is meaningless without the
ayanamsa that defines the cusp, and a silently-defaulted frame is exactly what the
Ephemeris Auditor charter forbids.

Python 3.11.
"""
from __future__ import annotations

import logging

import swisseph as swe

from agent.calculations.helpers import ephemeris
from agent.calculations.helpers.discrete_scan import (
    Crossing, scan_quantised_crossings,
)

logger = logging.getLogger(__name__)

__all__ = [
    "scan_divisional_ingresses", "scan_ingress_table",
    "MAX_ABS_SPEED_DEG_PER_DAY", "DEFAULT_BODIES", "AYANAMSA_NAME",
]

AYANAMSA_NAME = "LAHIRI"

# MEASURED upper bounds on |d(sidereal longitude)/dt|, deg/day.
#
# PROVENANCE (S148): sampled at 0.5-day steps (0.25 for Sun/Moon) over
# 2010-01-01 .. 2040-01-01 UT via helpers/ephemeris, Moshier backend. Raw maxima:
#   Sun 1.0197  Moon 15.3851  Mercury 2.2024  Venus 1.2588
#   Mars 0.7913  Jupiter 0.2420  Saturn 0.1305
# Stored values are those maxima rounded UP to a round figure. The padding is
# deliberate and one-directional: scan_quantised_crossings' prune is only valid
# if the bound is a TRUE upper bound, so an over-estimate costs a little time
# while an under-estimate silently drops crossings. Never tune these DOWN to make
# a scan faster.
# SCOPE GUARD: measured on a 30-year window around the present. A scan far outside
# it (deep history, or the nodes' osculating variants) must re-measure rather than
# assume these hold. TUNING NOTE: re-derive with scripts/measure_ephemeris_rates.py
# and widen if a new body or a wider epoch is added.
MAX_ABS_SPEED_DEG_PER_DAY: dict[str, float] = {
    "sun": 1.1, "moon": 16.0, "mercury": 2.5, "venus": 1.5,
    "mars": 1.0, "jupiter": 0.3, "saturn": 0.2,
}

# The seven moving bodies. The nodes are EXCLUDED by construction, not by policy:
# under the project's locked mean-node convention (gochara.py, S20) Rahu moves at
# a fixed mean rate and is always retrograde, so its ingresses are exactly
# periodic and carry no event information a scan would discover. Adding true-node
# support means adding a measured rate bound for it first.
DEFAULT_BODIES: dict[str, int] = {
    "sun": swe.SUN, "moon": swe.MOON, "mars": swe.MARS,
    "mercury": swe.MERCURY, "jupiter": swe.JUPITER,
    "venus": swe.VENUS, "saturn": swe.SATURN,
}


def _rate_bound(body: str) -> float:
    try:
        return MAX_ABS_SPEED_DEG_PER_DAY[body]
    except KeyError:
        raise ValueError(
            f"no measured rate bound for body {body!r}; add one to "
            "MAX_ABS_SPEED_DEG_PER_DAY by measurement before scanning it"
        ) from None


def scan_divisional_ingresses(
    body: str,
    start_jd: float,
    end_jd: float,
    *,
    n_divisions: int = 12,
    swe_id: int | None = None,
    tol_jd: float = 1e-6,
) -> list[Crossing]:
    """Division crossings of one body over [start_jd, end_jd).

    Args:
        body: lowercase name, a key of MAX_ABS_SPEED_DEG_PER_DAY.
        n_divisions: 12 for rashi (sign) ingress, 27 for nakshatra. Any divisor
            of the circle works; nothing in this function is specific to 12.
        swe_id: override the body id (tests inject a stub); defaults to
            DEFAULT_BODIES[body].

    Returns:
        Crossings in time order. A retrograde body re-crossing a cusp yields the
        full out-and-back sequence, so `to_index` may be `from_index - 1`.

    Raises:
        ValueError: unknown body, or an invalid span (propagated).
        ephemeris.EphemerisError: a pyswisseph read failed mid-scan.
    """
    pid = DEFAULT_BODIES[body] if swe_id is None else swe_id
    return scan_quantised_crossings(
        lambda jd: ephemeris.sidereal_longitude(jd, pid),
        n_divisions, start_jd, end_jd,
        rate_bound=_rate_bound(body), tol_jd=tol_jd,
    )


def scan_ingress_table(
    start_jd: float,
    end_jd: float,
    *,
    bodies: dict[str, int] | None = None,
    n_divisions: int = 12,
) -> dict:
    """Ingress events for several bodies over one window.

    PER-BODY ERROR ISOLATION. One body's ephemeris failure must not discard the
    six that already succeeded -- a timeline build that loses Saturn because
    Mercury faulted is worse than one that reports Mercury missing. Failures are
    collected in `errors` and the body is simply absent from `events`; the caller
    decides whether a partial table is usable. This is the ONE place that
    swallows an EphemerisError, and it records what it swallowed.

    Returns:
        {
          "scanned": {start_jd, end_jd, n_divisions, bodies, ayanamsa, nirayana},
          "events":  [ {body, jd, from_index, to_index, retrograde} ],
          "errors":  {body: "message"},
        }
        `retrograde` is read LIVE from the sign of the speed at the crossing
        instant -- motion, never assumption -- so a cusp re-crossing is
        self-describing.
    """
    bodies = bodies or DEFAULT_BODIES
    events: list[dict] = []
    errors: dict[str, str] = {}
    for name, pid in bodies.items():
        try:
            for c in scan_divisional_ingresses(
                name, start_jd, end_jd, n_divisions=n_divisions, swe_id=pid
            ):
                events.append({
                    "body": name,
                    "jd": c.jd,
                    "from_index": c.from_index,
                    "to_index": c.to_index,
                    "retrograde": ephemeris.sidereal_position(c.jd, pid).speed < 0.0,
                })
        except Exception as exc:  # noqa: BLE001 -- isolation is the point; recorded
            logger.warning("ingress_scan: %s failed (%s)", name, exc)
            errors[name] = str(exc)
    events.sort(key=lambda e: (e["jd"], e["body"]))
    return {
        "scanned": {
            "start_jd": start_jd, "end_jd": end_jd,
            "n_divisions": n_divisions, "bodies": list(bodies.keys()),
            "ayanamsa": AYANAMSA_NAME, "nirayana": True,
        },
        "events": events,
        "errors": errors,
    }
