"""Astro Agent -- YOGINI DASHA FACTS composer (Path B, S152).

Composes the already-built Yogini dasha engine
(agent.calculations.dashas.yogini) into a compact fact-block entry, like the
other static fact classes: the CALLER (static_facts.build_static_facts) attaches
the result onto chart_facts["yogini"]; pipeline._fact_block renders it; the
interpreter grounds its meaning in the retrieved chapters.

SCOPE -- MAHADASHA ONLY. The engine computes the 36-year, 8-Yogini Mahadasha
(MD) sequence; it has no antardasha (sub-period) function, so this fact class is
MD-only. That is honest V1 scope, not a gap to paper over -- do not synthesise
sub-periods.

INTERVALS, NOT A BAKED "NOW" (S147 lock). Each MD is stored as a dated interval
(start/end ISO date); whether a period is past / current / future is resolved at
ANSWER time in pipeline._fact_block against today's date, NOT baked in here. So
the cached static fact stays correct as the clock advances.

** VALIDATION CAVEAT (do not ignore) ** -- the engine's starting-index formula
`(nakshatra_number + 2) % 8` is validated against ONLY ONE reference chart
(Sulabh, Vishakha -> Dhanya); the engine's own docstring flags Surbhi / Sheridan
/ David as PENDING. Wiring this fact class does NOT validate it. It must clear
the 4-reference-chart oracle (scripts/validate_yogini_S152.py) against AstroSage
before it is trusted in a live reading; a chart that fails the formula is an
ENGINE fix in dashas/yogini.py, never a wiring change.

RESTATE, NEVER RECOMPUTE (S124): reads the natal Moon longitude + birth JD and
calls the validated engine; computes no astrology of its own.

FAIL-SOFT: a chart missing the Moon longitude or birth JD, or any bad input,
costs the Yogini facts, never the answer -- returns {}. Never raises.

Python 3.11.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import swisseph as swe

from agent.calculations.dashas.yogini import compute_yogini_dasha

logger = logging.getLogger(__name__)

__all__ = ["build_yogini_facts"]

# The engine's abbreviated lord strings (locked to the JHora fixture) -> the full
# planet names every other fact class uses, so the interpreter sees one vocabulary.
_LORD_FULL = {
    "Moon": "Moon", "Sun": "Sun", "Jup": "Jupiter", "Mars": "Mars",
    "Merc": "Mercury", "Sat": "Saturn", "Ven": "Venus", "Rah": "Rahu",
}


def _local_date_iso(jd: float, offset: timedelta) -> str:
    """Julian Day (UT) -> 'YYYY-MM-DD' in the BIRTH's local timezone.

    S152 fix: the engine's boundaries are JD UT; JHora (and the validated
    Vimshottari path, chart_calculator._calc_dasha/_fmt_date) display dates in
    birth-LOCAL time. Rendering the UT date instead shifted every boundary by
    the time-of-day crossing local midnight -> the measured 1-2 day, per-chart
    offsets against the JHora Yogini table (IST/SAST shifted, London ~exact).
    Applying the birth UTC offset before taking the date puts Yogini on the same
    frame as Vimshottari. Year length is identical on both (365.256363), so this
    is a rendering frame fix, not a dasha-math change.
    """
    y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
    utc_dt = datetime(y, m, d, tzinfo=timezone.utc) + timedelta(hours=h)
    return (utc_dt + offset).date().isoformat()


def build_yogini_facts(chart: dict) -> dict:
    """Yogini Mahadasha sequence for `chart`, as dated intervals.

    Args:
        chart: calculate_chart() output. Reads planetary_positions['Moon']
            ['longitude'] (sidereal degrees) and meta['jd_ut'] (birth JD UT) --
            the same two inputs the engine needs.

    Returns:
        {} if those inputs are not resolvable (fail-soft). Otherwise:
        {"mahadashas": [{"lord": <full planet>, "yogini": <name>,
                         "start": "YYYY-MM-DD", "end": "YYYY-MM-DD",
                         "years": <int nominal>}]}
        in time order from birth. Phase (past/current/future) is NOT included --
        it is computed at answer time. Never raises.
    """
    try:
        meta = (chart or {}).get("meta") or {}
        pp = (chart or {}).get("planetary_positions") or {}
        moon_lon = (pp.get("Moon") or {}).get("longitude")
        jd = meta.get("jd_ut")
        if moon_lon is None or jd is None:
            logger.warning("yogini: Moon longitude or birth jd_ut not resolvable")
            return {}

        # Render boundaries in the BIRTH's local timezone, matching the validated
        # Vimshottari convention (see _local_date_iso). meta['local_datetime'] is
        # the tz-aware birth datetime; its fixed UTC offset is carried forward to
        # every period, exactly as _calc_dasha carries birth_local's tzinfo. No
        # local_datetime -> fall back to UT (offset 0): the old behaviour, so a
        # chart lacking it is no worse than before, never an error.
        _ldt = meta.get("local_datetime")
        _off = _ldt.utcoffset() if (_ldt is not None
                                    and _ldt.utcoffset() is not None) else timedelta(0)

        periods = compute_yogini_dasha(float(moon_lon), float(jd))
        mds = [{
            "lord": _LORD_FULL.get(p.lord, p.lord),
            "yogini": p.yogini_name,
            "start": _local_date_iso(p.begin_jd, _off),
            "end": _local_date_iso(p.end_jd, _off),
            "years": p.years,
        } for p in periods]
        if not mds:
            return {}
        return {"mahadashas": mds}
    except Exception as exc:  # noqa: BLE001 -- a bad input costs Yogini, not the answer
        logger.warning("build_yogini_facts failed; omitting yogini: %s", exc)
        return {}
