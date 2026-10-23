"""Astro Agent -- NARAYANA DASA FACTS composer (Path B).

Composes the book- and JHora-validated Narayana engine
(agent.calculations.dashas.narayana) into a compact fact-block entry, exactly
like yogini_facts: the CALLER (static_facts.build_static_facts) attaches the
result onto chart_facts["narayana"]; pipeline._fact_block renders it; the
interpreter grounds its meaning in the retrieved chapters.

SCOPE -- MAHADASHA + ANTARDASHA (both cycles). The engine returns 24 rasi major
periods (two 12-rasi cycles); each non-zero period carries its 12 PVR Ch.18.3
antardasas (compute_narayana_antardasha), composed here as equal 1/12 sub-
intervals. EQUAL subdivision is the DOCTRINE (Sanjay Rath, "Narayana Dasa": "the
dasa period is equally divided into 12 antardasa"; Jaimini Sutramritam; PVR
Sec.18.3 "each antardasa is for n months"). It is deliberately NOT JHora-desktop's
true-solar-arc dating, which breathes +/-~4 days with the Sun's orbital speed --
a software precision artifact, not doctrine (S154 design decision, agent roster +
sources). The AD rasi SEQUENCE (seed/lord/direction) is the oracle-validated part
-- checked vs JHora v8 on Sulabh across all 12 MDs (forward + backward, co-lord
seed, Ketu-in-MD-sign); the dates are the composer's approximate rendering.

INTERVALS, NOT A BAKED "NOW" (S147 lock). Each period is a dated interval
(start/end ISO date in the BIRTH's local timezone); past/current/future is
resolved at ANSWER time in pipeline._fact_block, never baked in here. Dates are
cumulative MEAN-solar years (365.2425 d) from the birth datetime -- date-
approximate (MD +/-~1 day, AD boundaries +/-~4 days vs JHora's true-solar-year
boundaries over decades), finer than the Vimshottari +/-37-day convention and
fine for a reading. Antardasas subdivide each MD's own interval, so they nest
exactly inside their MD regardless of the year constant. The ENGINE's periods
(sequence + whole-year lengths) are the oracle-validated part (JHora end-to-end
on Sulabh); the dates here are the composer's rendering.

RESTATE, NEVER RECOMPUTE (S124): reads the natal ascendant sign + the 9 planet
longitudes and calls the validated engine; computes no astrology of its own.

Narayana carries NO verification predicate (a rasi-dasa, not a D1 placement
predicate) -> unfittable; NO capability-gate Requirement -- additive context,
same posture as yogini/jaimini.

FAIL-SOFT: a chart missing the ascendant, a planet longitude, or the birth
datetime -- or any engine fail-closed tie -- costs the Narayana facts, never the
answer. Returns {}. A per-MD antardasa failure costs only that MD's sub-periods
(not the MD, not the other MDs, not the answer). Never raises.

Python 3.11.
"""
from __future__ import annotations

import logging
from datetime import timedelta

from agent.calculations.dashas.narayana import (
    compute_narayana_antardasha,
    compute_narayana_dasa,
)

logger = logging.getLogger(__name__)

__all__ = ["build_narayana_facts"]

_SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
          "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
_NINE = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
         "Rahu", "Ketu")
_SOLAR_YEAR_DAYS = 365.2425


def build_narayana_facts(chart: dict) -> dict:
    """Narayana dasa (D1) for `chart`, as dated intervals with antardasas.

    Args:
        chart: calculate_chart() output. Reads meta['asc_lon_sidereal'],
            meta['local_datetime'] (tz-aware birth datetime), and
            planetary_positions[p]['longitude'] for the 9 classical+node planets.

    Returns:
        {} if any required input is missing (fail-soft). Otherwise:
        {"seed": <sign>, "progression_case": "normal|saturn|ketu",
         "mahadashas": [{"rasi","lord","years","cycle","start","end",
                         "antardashas": [{"rasi","start","end"}]}]}
        in time order from birth (24 periods, two cycles). A zero-length cycle-2
        period carries no "antardashas" key. Phase is NOT included -- it is
        computed at answer time. Never raises.
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

        # The 12-AD rasi order is a pure function of (dasa rasi, chart); there are
        # <=12 distinct rasis across the 24 periods, so memoize to avoid repeating
        # the stronger_rasi resolution 24 times (mirrors PyJHora's antar cache).
        ad_order_cache: dict[str, tuple] = {}

        def _ad_order(rasi: str) -> tuple:
            seq = ad_order_cache.get(rasi)
            if seq is None:
                seq = compute_narayana_antardasha(rasi, lons)
                ad_order_cache[rasi] = seq
            return seq

        mds = []
        cum_days = 0.0
        for per in nd.periods:
            start = ldt + timedelta(days=cum_days)
            span_days = per.years * _SOLAR_YEAR_DAYS
            cum_days += span_days
            end = ldt + timedelta(days=cum_days)
            md = {
                "rasi": per.rasi, "lord": per.lord, "years": per.years,
                "cycle": per.cycle,
                "start": start.date().isoformat(),
                "end": end.date().isoformat(),
            }
            # Antardasas: 12 EQUAL 1/12 sub-intervals of THIS MD's own span (so
            # they nest exactly: the 12th AD ends on the MD end). Doctrine = equal
            # (see module docstring). Per-MD fail-soft -- a bad AD order costs this
            # MD's sub-periods only. A zero-length cycle-2 MD carries none.
            if per.years > 0:
                try:
                    order = _ad_order(per.rasi)
                    ads = []
                    for i, ad_rasi in enumerate(order):
                        a = start + timedelta(days=span_days * i / 12.0)
                        b = start + timedelta(days=span_days * (i + 1) / 12.0)
                        ads.append({
                            "rasi": ad_rasi,
                            "start": a.date().isoformat(),
                            "end": b.date().isoformat(),
                        })
                    md["antardashas"] = ads
                except Exception as exc:  # noqa: BLE001 -- bad AD costs this MD's sub-periods only
                    logger.warning(
                        "narayana: antardasa compose failed for %s MD: %s",
                        per.rasi, exc)
            mds.append(md)
        if not mds:
            return {}
        return {"seed": nd.seed, "progression_case": nd.progression_case,
                "mahadashas": mds}
    except Exception as exc:  # noqa: BLE001 -- a bad input costs Narayana, not the answer
        logger.warning("build_narayana_facts failed; omitting narayana: %s", exc)
        return {}
