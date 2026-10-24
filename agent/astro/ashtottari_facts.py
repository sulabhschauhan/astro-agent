"""Astro Agent -- ASHTOTTARI FACTS composer (Path B, S155).

TWO surfaces for the conditional Ashtottari dasa, both fail-soft and additive
(no capability-gate Requirement, no predicate -- same posture as yogini/narayana):

  * build_ashtottari_applicability_facts (THIS unit, S155) -- the CONDITIONAL
    applicability of Ashtottari to a chart, as a STRUCTURED fact. Ashtottari is
    a conditional dasa; whether it "applies" is contested across classical
    authorities, so this does NOT gate the dasa computation and does NOT emit a
    single pass/fail verdict. It surfaces all THREE classical criteria
    independently, each with its inputs + its basis, plus a met-count. The
    interpreter weights the dasa by which criteria hold (design S155, ratified).

  * build_ashtottari_facts (S155) -- the dated MD + proportional-AD composition.
    Composes agent.calculations.dashas.ashtottari the way narayana_facts composes
    the Narayana engine: dated intervals (phase resolved at answer time), the
    applicability fact nested under "applicability". Per-MD AD fail-soft.

RESTATE, NEVER RECOMPUTE (S124): reads fields calculate_chart() already
produced -- the ascendant lord (lagna_chart.ascendant_lord, the chart's OWN
single-lord convention, so applicability inherits the same lord the rest of the
chart uses, co-lord disputes and all), planet houses, Sun/Moon longitudes, the
ascendant longitude. The only live computation is the tithi (Sun-Moon elongation)
and sunrise/sunset (day vs night), both from the chart's own inputs.

THE THREE CRITERIA (research S155; satyori / astrosutras; PyJHora encodes only #1):
  1. positional (BPHS, most-cited): Rahu in a kendra (1,4,7,10) OR trikona
     (1,5,9) from the lagna LORD's house, and Rahu not in the lagna.
  2. paksha/time: day birth in Krishna paksha OR night birth in Shukla paksha.
     The rule DIRECTION varies by tradition, so the raw inputs (paksha,
     day/night) are surfaced alongside the verdict -- usable even to a tradition
     that flips it.
  3. lagna_nakshatra: the lagna falls in a Rahu nakshatra (Ardra/Swati/Shatabhisha).

NO COLLAPSED VERDICT (Working Style #9, anchored-judgment): there is deliberately
NO top-level boolean "applicable". Each criterion reports independently; a
"criteria_met" count is provided, never a yes/no.

FAIL-SOFT, PER CRITERION: a criterion whose inputs are missing is simply omitted
(the others still surface); day/night that cannot be resolved marks that
criterion's `applicable` as None with birth_period "undetermined". A wholly
unresolvable chart returns {}. Never raises.

Python 3.11.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import swisseph as swe

from agent.chart_calculator import NAKSHATRAS, _nakshatra
from agent.calculations.dashas.ashtottari import (
    compute_ashtottari_bhukti,
    compute_ashtottari_dasha,
)

logger = logging.getLogger(__name__)

__all__ = [
    "build_ashtottari_facts",
    "build_ashtottari_applicability_facts",
    "RAHU_NAKSHATRAS",
]

# Engine lord strings (Yogini fixture convention) -> full planet names, so the
# interpreter sees one vocabulary across every dasa fact class.
_LORD_FULL = {
    "Sun": "Sun", "Moon": "Moon", "Mars": "Mars", "Merc": "Mercury",
    "Sat": "Saturn", "Jup": "Jupiter", "Rah": "Rahu", "Ven": "Venus",
}


def _local_date_iso(jd: float, offset: timedelta) -> str:
    """Julian Day (UT) -> 'YYYY-MM-DD' in the birth's local timezone, matching
    yogini_facts / the Vimshottari convention (render in the birth frame, not UT)."""
    y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
    utc_dt = datetime(y, m, d, tzinfo=timezone.utc) + timedelta(hours=h)
    return (utc_dt + offset).date().isoformat()

# The three Rahu-ruled nakshatras (Vimshottari lordship). Reachability guard
# (Working Style #21): if any name drifts from the canonical NAKSHATRAS list the
# lagna-nakshatra criterion silently always-fails, so assert the contract here.
RAHU_NAKSHATRAS = ("Ardra", "Swati", "Shatabhisha")
assert all(n in NAKSHATRAS for n in RAHU_NAKSHATRAS), (
    "RAHU_NAKSHATRAS drifted from chart_calculator.NAKSHATRAS -- lagna-nakshatra "
    "criterion would silently always-fail"
)

_TITHI_SPAN_DEG = 12.0  # Sun->Moon elongation per tithi; 15 tithis per paksha


def _kendras_from(house: int) -> set[int]:
    """The 4 kendras (1st/4th/7th/10th) counted FROM `house`, whole-sign."""
    return {((house - 1 + k) % 12) + 1 for k in (0, 3, 6, 9)}


def _trikonas_from(house: int) -> set[int]:
    """The 3 trikonas (1st/5th/9th) counted FROM `house`, whole-sign."""
    return {((house - 1 + k) % 12) + 1 for k in (0, 4, 8)}


def _day_or_night(meta: dict, birth_details: dict) -> str:
    """'day' | 'night' | 'undetermined' for the birth moment.

    Uses the chart's own birth datetime + location and the panchanga sunrise/
    sunset. 'undetermined' (not an error) when datetime or lat/lon is absent or
    the ephemeris call fails -- the paksha criterion degrades to applicable=None.
    """
    try:
        from agent.calculations.core.panchanga import (
            calculate_sunrise, calculate_sunset,
        )
        birth = meta.get("local_datetime")
        lat = birth_details.get("lat")
        lon = birth_details.get("lon")
        if birth is None or lat is None or lon is None:
            return "undetermined"
        sunrise = calculate_sunrise(birth, float(lat), float(lon))
        sunset = calculate_sunset(birth, float(lat), float(lon))
        return "day" if sunrise <= birth < sunset else "night"
    except Exception as exc:  # noqa: BLE001 -- day/night is optional, never fatal
        logger.warning("ashtottari applicability: day/night undetermined: %s", exc)
        return "undetermined"


def build_ashtottari_applicability_facts(chart: dict) -> dict:
    """The three classical Ashtottari-applicability criteria for `chart`.

    Args:
        chart: calculate_chart() output. Reads lagna_chart['ascendant_lord'],
            planetary_positions[...]['house'|'longitude'], meta['asc_lon_sidereal'
            |'local_datetime'], and birth_details['lat'|'lon'].

    Returns:
        {} if nothing is resolvable. Otherwise:
        {"criteria": {<name>: {"applicable": bool|None, ...inputs..., "basis": str}},
         "criteria_met": int, "criteria_evaluated": int, "note": str}
        with NO top-level pass/fail. Never raises.
    """
    try:
        meta = (chart or {}).get("meta") or {}
        pp = (chart or {}).get("planetary_positions") or {}
        lagna = (chart or {}).get("lagna_chart") or {}
        bd = (chart or {}).get("birth_details") or {}
    except Exception:  # noqa: BLE001 -- a non-dict chart costs the facts, not the answer
        return {}

    criteria: dict[str, dict] = {}

    # ── 1. Positional (BPHS, most-cited) ─────────────────────────────────────
    try:
        lord = lagna.get("ascendant_lord")
        lord_house = (pp.get(lord) or {}).get("house") if lord else None
        rahu_house = (pp.get("Rahu") or {}).get("house")
        if lord_house is not None and rahu_house is not None:
            lh, rh = int(lord_house), int(rahu_house)
            in_kendra_or_trikona = rh in (_kendras_from(lh) | _trikonas_from(lh))
            criteria["positional"] = {
                "applicable": in_kendra_or_trikona and rh != 1,
                "lagna_lord": lord,
                "lagna_lord_house": lh,
                "rahu_house": rh,
                "rahu_in_lagna": rh == 1,
                "basis": ("Rahu in a kendra (1,4,7,10) or trikona (1,5,9) from the "
                          "lagna lord's house, and not in the lagna"),
            }
    except Exception as exc:  # noqa: BLE001 -- one criterion's failure costs only it
        logger.warning("ashtottari applicability: positional failed: %s", exc)

    # ── 2. Paksha / time-of-birth ────────────────────────────────────────────
    try:
        sun = (pp.get("Sun") or {}).get("longitude")
        moon = (pp.get("Moon") or {}).get("longitude")
        if sun is not None and moon is not None:
            elong = (float(moon) - float(sun)) % 360.0
            tithi_idx = int(elong / _TITHI_SPAN_DEG)          # 0..29
            paksha = "Shukla" if tithi_idx < 15 else "Krishna"
            period = _day_or_night(meta, bd)
            if period == "undetermined":
                applicable = None
            else:
                applicable = ((period == "day" and paksha == "Krishna")
                              or (period == "night" and paksha == "Shukla"))
            criteria["paksha"] = {
                "applicable": applicable,
                "paksha": paksha,
                "birth_period": period,
                "basis": ("day birth in Krishna paksha OR night birth in Shukla "
                          "paksha (rule direction varies by tradition)"),
            }
    except Exception as exc:  # noqa: BLE001
        logger.warning("ashtottari applicability: paksha failed: %s", exc)

    # ── 3. Lagna in a Rahu nakshatra ─────────────────────────────────────────
    try:
        asc_lon = meta.get("asc_lon_sidereal")
        if asc_lon is not None:
            nak = _nakshatra(float(asc_lon))[0]
            criteria["lagna_nakshatra"] = {
                "applicable": nak in RAHU_NAKSHATRAS,
                "lagna_nakshatra": nak,
                "basis": "lagna in a Rahu nakshatra (Ardra, Swati, Shatabhisha)",
            }
    except Exception as exc:  # noqa: BLE001
        logger.warning("ashtottari applicability: lagna_nakshatra failed: %s", exc)

    if not criteria:
        return {}

    met = sum(1 for c in criteria.values() if c.get("applicable") is True)
    return {
        "criteria": criteria,
        "criteria_met": met,
        "criteria_evaluated": len(criteria),
        "note": ("Ashtottari applicability is contested across classical "
                 "authorities; these criteria are not equivalent (whether they are "
                 "alternative, cumulative, or primary-plus-confirmation is itself "
                 "disputed). No single pass/fail verdict is asserted -- weight the "
                 "dasa by how many and which criteria hold."),
    }


def build_ashtottari_facts(chart: dict) -> dict:
    """Ashtottari dasa (MD + proportional AD) for `chart`, as dated intervals,
    with the conditional-applicability fact nested under "applicability".

    Args:
        chart: calculate_chart() output. Reads planetary_positions['Moon']
            ['longitude'] (sidereal degrees) and meta['jd_ut'] (birth JD UT) for
            the engine; meta['local_datetime'] for the render frame; plus whatever
            build_ashtottari_applicability_facts reads.

    Returns:
        {} if nothing is resolvable (fail-soft). Otherwise, any of:
        {"mahadashas": [{"lord","start","end","years",
                         "antardashas": [{"lord","start","end"}]}],
         "applicability": {...},  # from build_ashtottari_applicability_facts
         "note": str}
        in time order from the seed (pre-birth) MD. Phase is NOT included -- it is
        resolved at answer time in pipeline._fact_block. A per-MD antardasa failure
        costs only that MD's sub-periods. Never raises.
    """
    try:
        meta = (chart or {}).get("meta") or {}
        pp = (chart or {}).get("planetary_positions") or {}
        out: dict = {}

        moon_lon = (pp.get("Moon") or {}).get("longitude")
        jd = meta.get("jd_ut")
        if moon_lon is not None and jd is not None:
            _ldt = meta.get("local_datetime")
            _off = (_ldt.utcoffset() if (_ldt is not None
                                         and _ldt.utcoffset() is not None)
                    else timedelta(0))
            periods = compute_ashtottari_dasha(float(moon_lon), float(jd))
            mds = []
            for p in periods:
                md = {
                    "lord": _LORD_FULL.get(p.lord, p.lord),
                    "start": _local_date_iso(p.begin_jd, _off),
                    "end": _local_date_iso(p.end_jd, _off),
                    "years": p.years,
                }
                # Proportional antardasas, per-MD fail-soft (a bad AD compose
                # costs only this MD's sub-periods, not the MD or the answer).
                try:
                    ads = compute_ashtottari_bhukti(p)
                    md["antardashas"] = [{
                        "lord": _LORD_FULL.get(a.lord, a.lord),
                        "start": _local_date_iso(a.begin_jd, _off),
                        "end": _local_date_iso(a.end_jd, _off),
                    } for a in ads]
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "ashtottari: antardasa compose failed for %s MD: %s",
                        p.lord, exc)
                mds.append(md)
            if mds:
                out["mahadashas"] = mds
        else:
            logger.warning("ashtottari: Moon longitude or birth jd_ut not resolvable")

        # Applicability composes independently (own fail-soft); nest if present.
        appl = build_ashtottari_applicability_facts(chart)
        if appl:
            out["applicability"] = appl

        if not out:
            return {}
        out["note"] = ("Ashtottari is a CONDITIONAL nakshatra dasa; weight it by "
                       "the `applicability` criteria -- do not treat it as "
                       "unconditionally in force.")
        return out
    except Exception as exc:  # noqa: BLE001 -- a bad input costs Ashtottari, not the answer
        logger.warning("build_ashtottari_facts failed; omitting ashtottari: %s", exc)
        return {}
