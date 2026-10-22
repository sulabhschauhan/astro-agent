"""Astro Agent -- NARAYANA DASA FACTS composer (Path B).

Composes the book- and JHora-validated Narayana engine
(agent.calculations.dashas.narayana) into a compact fact-block entry, exactly
like yogini_facts: the CALLER (static_facts.build_static_facts) attaches the
result onto chart_facts["narayana"]; pipeline._fact_block renders it; the
interpreter grounds its meaning in the retrieved chapters.

SCOPE -- MAHADASHA ONLY (both cycles). The engine returns 24 rasi major periods
(two 12-rasi cycles). Antardasas (§18.3) are NOT composed yet -- honest V1
scope, like Yogini's MD-only cut; do not synthesise sub-periods.

INTERVALS, NOT A BAKED "NOW" (S147 lock). Each period is a dated interval
(start/end ISO date in the BIRTH's local timezone); past/current/future is
resolved at ANSWER time in pipeline._fact_block, never baked in here. Dates are
cumulative MEAN-solar years (365.2425 d) from the birth datetime -- date-
approximate (±~1 day drift vs JHora's true-solar-year boundaries over decades),
which is finer than the Vimshottari ±37-day convention and fine for a reading.
The ENGINE's periods (sequence + whole-year lengths) are the oracle-validated
part (JHora end-to-end on Sulabh); the dates here are the composer's rendering.

RESTATE, NEVER RECOMPUTE (S124): reads the natal ascendant sign + the 9 planet
longitudes and calls the validated engine; computes no astrology of its own.

Narayana carries NO verification predicate (a rasi-dasa, not a D1 placement
predicate) -> unfittable; NO capability-gate Requirement -- additive context,
same posture as yogini/jaimini.

FAIL-SOFT: a chart missing the ascendant, a planet longitude, or the birth
datetime -- or any engine fail-closed tie -- costs the Narayana facts, never the
answer. Returns {}. Never raises.

Python 3.11.
"""
from __future__ import annotations

import logging
from datetime import timedelta

from agent.calculations.dashas.narayana import compute_narayana_dasa

logger = logging.getLogger(__name__)

__all__ = ["build_narayana_facts"]

_SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
          "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
_NINE = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
         "Rahu", "Ketu")
_SOLAR_YEAR_DAYS = 365.2425


def build_narayana_facts(chart: dict) -> dict:
    """Narayana dasa (D1) for `chart`, as dated intervals.

    Args:
        chart: calculate_chart() output. Reads meta['asc_lon_sidereal'],
            meta['local_datetime'] (tz-aware birth datetime), and
            planetary_positions[p]['longitude'] for the 9 classical+node planets.

    Returns:
        {} if any required input is missing (fail-soft). Otherwise:
        {"seed": <sign>, "progression_case": "normal|saturn|ketu",
         "mahadashas": [{"rasi","lord","years","cycle","start","end"}]}
        in time order from birth (24 periods, two cycles). Phase is NOT included
        -- it is computed at answer time. Never raises.
    """
    try:
        meta = (chart or {}).get("meta") or {}
        pp = (chart or {}).get("planetary_positions") or {}
        asc_lon = meta.get("asc_lon_sidereal")
        ldt = meta.get("local_datetime")
        if asc_lon is None or ldt is None:
            logger.warning("narayana: asc_lon_sidereal or local_datetime missing")
            return {}
        asc_sign = _SIGNS[int(float(asc_lon) // 30) % 12]

        lons: dict[str, float] = {}
        for p in _NINE:
            v = (pp.get(p) or {}).get("longitude")
            if v is None:
                logger.warning("narayana: %s longitude missing", p)
                return {}
            lons[p] = float(v)

        nd = compute_narayana_dasa(asc_sign, lons)

        mds = []
        cum_days = 0.0
        for per in nd.periods:
            start = ldt + timedelta(days=cum_days)
            cum_days += per.years * _SOLAR_YEAR_DAYS
            end = ldt + timedelta(days=cum_days)
            mds.append({
                "rasi": per.rasi, "lord": per.lord, "years": per.years,
                "cycle": per.cycle,
                "start": start.date().isoformat(),
                "end": end.date().isoformat(),
            })
        if not mds:
            return {}
        return {"seed": nd.seed, "progression_case": nd.progression_case,
                "mahadashas": mds}
    except Exception as exc:  # noqa: BLE001 -- a bad input costs Narayana, not the answer
        logger.warning("build_narayana_facts failed; omitting narayana: %s", exc)
        return {}
