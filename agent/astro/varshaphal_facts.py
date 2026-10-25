"""Astro Agent -- VARSHAPHAL FACTS composer (Path B, S156).

Composes the validated annual engines into one compact fact-block entry, like
narayana_facts / ashtottari_facts: static_facts attaches the result onto
chart_facts["varshaphal"]; pipeline._fact_block renders it; the interpreter
grounds meaning in the retrieved chapters.

SUB-ENGINES (all validated vs the JHora oracle, see
data/default_user/jhora_sulabh_varshaphal.md):
  A  varsha_pravesh.compute_varsha_pravesh  -> pravesh instant + annual D1 cast
  B  muntha.compute_muntha                  -> Muntha sign/house
  C1 panchavargeeya.compute_panchavargeeya  -> Pancha-vargeeya bala (surfaced)
  C2 varshesha.lord_of_the_year             -> year-lord (consensus rule)
  E  mudda / patyayini / yogini _dasha       -> the three annual dashas

YEAR-FIXED, NOT CHART-FIXED (ratified S156). The annual chart switches at every
solar return, so this composer takes a target_year (default: the solar year that
contains `as_of`). It is attached in static_facts for reachability now, BUT the
chart-fixed fact_store cache would serve a STALE year once the pravesh rolls
over -- the dated-layer re-anchor (timeline_store, pravesh-span) is the required
follow-up (decision #2). Until then, callers that cache must key/invalidate on
the solar year stamped in the result ("year").

RESTATE, NEVER RECOMPUTE: reads the natal chart and calls the validated engines.
Cast at BIRTHPLACE (Raman default + oracle match).

INTERVALS, NOT A BAKED "NOW": dashas are dated intervals (ISO dates, UT-based --
date-approximate by up to the tz offset vs JHora's birth-local display, same
posture as narayana_facts); current/past/future is resolved at answer time.

FAIL-SOFT: any missing input or engine failure costs the varshaphal facts, never
the answer. Returns {}. A single failed dasha costs only that dasha. Never raises.

Python 3.11.
"""
from __future__ import annotations

import datetime as _dt
import logging

import swisseph as swe

from agent.calculations.annual.muntha import compute_muntha
from agent.calculations.annual.mudda import mudda_dasha
from agent.calculations.annual.panchavargeeya import compute_panchavargeeya
from agent.calculations.annual.patyayini import patyayini_dasha
from agent.calculations.annual.varsha_pravesh import compute_varsha_pravesh
from agent.calculations.annual.varshesha import LAGNA_KEY, lord_of_the_year
from agent.calculations.annual.yogini import yogini_dasha

logger = logging.getLogger(__name__)

__all__ = ["build_varshaphal_facts"]

_SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
          "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
_SEVEN = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
_NAME_TO_SWE = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
                "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
                "Venus": swe.VENUS, "Saturn": swe.SATURN}
_SWE_TO_NAME = {v: k for k, v in _NAME_TO_SWE.items()}
_NAK = 360.0 / 27.0


def _is_night(jd_ut: float, lat: float, lon: float) -> bool:
    """True if the Sun is below the horizon at (jd_ut, place). Fail-soft: on any
    ephemeris error assumes DAY (False) rather than crashing the composer."""
    try:
        eq, _ = swe.calc_ut(jd_ut, swe.SUN, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)
        hor = swe.azalt(jd_ut, swe.EQU2HOR, [lon, lat, 0.0], 0.0, 0.0,
                        [eq[0], eq[1]])
        return hor[1] < 0.0  # altitude
    except Exception as exc:  # noqa: BLE001
        logger.warning("varshaphal: day/night calc failed, assuming day: %s", exc)
        return False


def _iso(jd_ut: float, tz_offset_days: float) -> str:
    """Julian Day (UT) -> local civil date 'YYYY-MM-DD' using a fixed tz offset."""
    y, m, d, _h = swe.revjul(jd_ut + tz_offset_days)
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"


def _periods_iso(periods, tz):
    out = []
    for p in periods:
        e = {k: v for k, v in p.items() if not k.endswith("_jd")}
        e["start"] = _iso(p["start_jd"], tz)
        e["end"] = _iso(p["end_jd"], tz)
        out.append(e)
    return out


def _solar_year_of(as_of: _dt.date, birth_month: int, birth_day: int) -> int:
    """The target Varsha year whose pravesh (~birth month/day) opens the annual
    period containing `as_of`."""
    if (as_of.month, as_of.day) >= (birth_month, birth_day):
        return as_of.year
    return as_of.year - 1


def build_varshaphal_facts(chart: dict, target_year: int | None = None,
                           as_of: _dt.date | None = None) -> dict:
    """Varshaphal annual-chart facts for `chart` (calculate_chart output).

    Args:
        chart: reads meta['jd_ut','lat','lon','asc_lon_sidereal','local_datetime']
            and planetary_positions['Moon']['longitude'].
        target_year: Gregorian year of the Varsha Pravesh to compute. Default:
            the solar year containing `as_of` (or today).
        as_of: date used to pick the current solar year when target_year is None.

    Returns:
        {} on any missing input or failure (fail-soft). Otherwise a dict with the
        pravesh, annual positions, Muntha, year-lord (+ candidates), Pancha-
        vargeeya bala, and the three dashas as dated intervals. Never raises.
    """
    try:
        meta = (chart or {}).get("meta") or {}
        pp = (chart or {}).get("planetary_positions") or {}
        natal_jd = meta.get("jd_ut")
        lat = meta.get("lat")
        lon = meta.get("lon")
        natal_lagna = meta.get("asc_lon_sidereal")
        ldt = meta.get("local_datetime")
        moon = (pp.get("Moon") or {}).get("longitude")
        if None in (natal_jd, lat, lon, natal_lagna, ldt, moon):
            logger.warning("varshaphal: missing a required meta/Moon input")
            return {}

        tz = (ldt.utcoffset() or _dt.timedelta(0)).total_seconds() / 86400.0
        if target_year is None:
            ref = as_of or _dt.date.today()
            target_year = _solar_year_of(ref, ldt.month, ldt.day)
        completed_years = int(target_year) - int(ldt.year)
        if completed_years < 0:
            logger.warning("varshaphal: target_year before birth")
            return {}

        # A -- this pravesh + next pravesh (cast at birthplace).
        pr = compute_varsha_pravesh(natal_jd, lat, lon, target_year)
        prn = compute_varsha_pravesh(natal_jd, lat, lon, target_year + 1)
        pjd, npjd = pr["pravesh_jd_ut"], prn["pravesh_jd_ut"]
        asc = pr["ascendant_sid"]
        planets = pr["planets_sid"]              # name -> sidereal lon
        annual_lagna_sign = int(asc // 30) % 12

        # B -- Muntha.
        muntha = compute_muntha(float(natal_lagna), completed_years, annual_lagna_sign)

        # C2 -- year-lord (needs swe-id positions + Varsha Lagna + day/night).
        pos = {_NAME_TO_SWE[n]: planets[n] for n in _SEVEN}
        pos[LAGNA_KEY] = asc
        night = _is_night(pjd, float(lat), float(lon))
        natal_lagna_sign = int(float(natal_lagna) // 30) % 12
        yl = lord_of_the_year(pos, natal_lagna_sign, muntha["muntha_sign"], night)
        yl_candidates = [
            {**c, "planet": _SWE_TO_NAME.get(c["planet"], c["planet"])}
            for c in yl["candidates"]
        ]

        # C1 -- Pancha-vargeeya bala (surfaced for every planet).
        pv = compute_panchavargeeya({n: planets[n] for n in _SEVEN})
        pv_out = {n: {"total": round(pv[n]["total"], 2), "band": pv[n]["band"]}
                  for n in _SEVEN}

        # E -- the three annual dashas (each fail-soft).
        nak_no = int(float(moon) / _NAK) + 1
        frac_remaining = 1.0 - (float(moon) % _NAK) / _NAK
        if frac_remaining <= 0.0:
            frac_remaining = 1.0
        dashas: dict = {}
        for key, fn in (
            ("mudda", lambda: mudda_dasha(completed_years, nak_no, pjd, npjd)),
            ("patyayini", lambda: patyayini_dasha(
                {**{n: planets[n] for n in _SEVEN}, "Asc": asc}, pjd, npjd)),
            ("yogini", lambda: yogini_dasha(
                nak_no, completed_years, frac_remaining, pjd, npjd)),
        ):
            try:
                dashas[key] = _periods_iso(fn(), tz)
            except Exception as exc:  # noqa: BLE001 -- one dasha costs only itself
                logger.warning("varshaphal: %s dasha failed: %s", key, exc)

        return {
            "year": int(target_year),
            "completed_years": completed_years,
            "pravesh": _iso(pjd, tz),
            "pravesh_end": _iso(npjd, tz),
            "boundary_flag": bool(pr["boundary_flag"]),
            "cast": "birthplace",
            "annual_lagna": {"sign": _SIGNS[annual_lagna_sign],
                             "degree": round(asc % 30, 2)},
            "positions": {n: {"sign": _SIGNS[int(planets[n] // 30) % 12],
                              "degree": round(planets[n] % 30, 2)}
                          for n in _SEVEN},
            "muntha": {"sign": _SIGNS[muntha["muntha_sign"]],
                       "house_from_lagna": muntha["muntha_house_from_annual_lagna"]},
            "year_lord": {
                "winner": _SWE_TO_NAME.get(yl["winner"], yl["winner"]),
                "rule_path": yl["rule_path"],
                "candidates": yl_candidates,
            },
            "pancha_vargeeya_bala": pv_out,
            "dashas": dashas,
        }
    except Exception as exc:  # noqa: BLE001 -- bad input costs varshaphal, not the answer
        logger.warning("build_varshaphal_facts failed; omitting varshaphal: %s", exc)
        return {}
