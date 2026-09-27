"""
Astro Agent -- TRANSIT FACTS composer (Path B, S142).

Restates agent.calculations.transits.{gochara,sade_sati} into a new fact class
for the interpreter. Composed by the CALLER exactly like yoga_facts.py (S133)
and the D9 navamsa composition (S130): chart_facts stays a pure restatement of
the calculator, and this module owns the extra astronomy the transit layer
needs but chart_facts.py's own law forbids it from importing.

WHY (S142 handover). S141 proved LIVE that correct dasha math still
MIS-SELECTED the marriage window: the interpreter picked the Venus-karaka
false positive (Mercury-Venus antardasha, 2011-14) and passed over the
antardasha that actually contains the desktop benchmark's ~2019 window
(Mercury-Rahu, 2018-20), because the Saturn-transit corroboration the
benchmark used to override the Venus reading was not in the facts. Accuracy is
gated on INPUT SYSTEMS, not calculation (S141 lock) -- Sade Sati / Saturn
gochara is the first of those systems to be fed.

VALIDATED (offline, S142): for Sulabh's chart (Moon in Scorpio, Ascendant
Sagittarius), the Mercury-Rahu antardasha (28 Jan 2018 - 16 Aug 2020) has
Saturn transiting Sagittarius -- house 1 from lagna (i.e. transiting the
ascendant itself) and house 2 from Moon (Sade Sati SETTING phase) -- while the
false-positive Mercury-Venus antardasha (26 Dec 2011 - 26 Oct 2014) has Saturn
in house 10-11 from lagna and house 11-12 from Moon (Sade Sati RISING, not yet
at the ascendant). This is exactly the corroborating signal the desktop
benchmark used; it was simply not in the fact block before this module.

WHAT IS COMPUTED, AND HOW CHEAPLY. For every ANTARDASHA already restated by
chart_facts._read_dasha (S141), this module reads that sub-period's start_jd/
end_jd from the RAW chart['dasha']['mahadasha_tree'] -- chart_facts drops those
floats on purpose (the drift note calls the dates approximate) -- takes the
MIDPOINT, and calls gochara.compute_gochara() ONCE for Saturn's sign/house-
from-lagna/house-from-moon/retrograde at that moment. Sade Sati's phase
(RISING/PEAK/SETTING/NONE) is then read off that SAME sign via
sade_sati.sade_sati_phase_for_signs() -- a cheap restatement of the already
oracle-locked 12th/1st/2nd-from-Moon rule (Session 20), not a new calculation.
compute_sade_sati()'s own window-scan machinery (a multi-year daily scan with
bisection, ~0.4s per call) is deliberately NOT invoked per period: 60+
antardashas x 0.4s would add tens of seconds to every chart, for boundary
precision this per-period snapshot does not need. Measured: 70
compute_gochara() calls cost ~13ms total.

MAHADASHA-level lines are NOT annotated. A mahadasha spans up to two decades --
long enough for Saturn to cross several signs -- so one snapshot at MD level
would misrepresent the period. Antardashas (roughly 1-3 years here) are narrow
enough that a midpoint snapshot is a fair representative reading; this mirrors
S141's own reasoning for restating dasha at the antardasha, not just the
mahadasha, level.

FAIL-SOFT. Any failure costs the transit facts, never the answer -- same
posture as yoga_facts.build_yoga_facts.

Python 3.11.
"""
from __future__ import annotations

from agent.calculations.transits import gochara as _gochara
from agent.calculations.transits import sade_sati as _sade_sati

_SIGN_NAMES = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


def build_transit_facts(chart: dict, chart_facts: dict) -> dict:
    """Compute per-antardasha Saturn transit context.

    Args:
        chart: the dict from agent.chart_calculator.calculate_chart() -- read
            for planetary_positions['Moon']['longitude'], meta['asc_lon_sidereal'],
            and dasha['mahadasha_tree'] (RAW, for the start_jd/end_jd floats
            chart_facts deliberately drops). Read-only.
        chart_facts: the built fact block (build_chart_facts output). Read-only;
            not required to already carry dasha_periods -- this module reads the
            RAW tree from `chart`, independently, so it works even if the caller
            composes transit facts before dasha facts.

    Returns:
        {} if the inputs do not support it (no moon longitude, no ascendant, no
        dasha tree) or every period was unreadable. Otherwise:
        {"natal_moon_sign": str,
         "periods": {"<lord>|<start>": {"saturn_sign": str,
                                         "saturn_house_from_lagna": int,
                                         "saturn_house_from_moon": int,
                                         "saturn_retrograde": bool,
                                         "sade_sati_phase": str,
                                         "jupiter_sign": str | None,
                                         "jupiter_house_from_lagna": int | None,
                                         "jupiter_retrograde": bool | None}, ...}}
        Never raises.
    """
    try:
        pp = chart.get("planetary_positions") or {}
        moon = pp.get("Moon") or {}
        meta = chart.get("meta") or {}
        moon_lon = moon.get("longitude")
        asc_lon = meta.get("asc_lon_sidereal")
        raw_tree = (chart.get("dasha") or {}).get("mahadasha_tree") or []
        if moon_lon is None or asc_lon is None or not raw_tree:
            return {}

        natal_moon_lon = float(moon_lon) % 360.0
        natal_asc_lon = float(asc_lon) % 360.0
        natal_moon_sign_0 = int(natal_moon_lon / 30.0) % 12  # 0=Aries..11=Pisces

        periods: dict[str, dict] = {}
        for node in raw_tree:
            if not isinstance(node, dict):
                continue
            for ad in node.get("antardashas") or []:
                if not isinstance(ad, dict):
                    continue
                key = _period_key(ad)
                if key is None or key in periods:
                    continue  # first tree occurrence wins; malformed rows skipped
                entry = _snapshot(ad, natal_asc_lon, natal_moon_lon, natal_moon_sign_0)
                if entry is not None:
                    periods[key] = entry

        if not periods:
            return {}
        return {"natal_moon_sign": _SIGN_NAMES[natal_moon_sign_0], "periods": periods}
    except Exception as e:  # noqa: BLE001 -- a bad chart costs transits, not the answer
        return {"periods": {}, "error": f"{type(e).__name__}: {e}"}


def _period_key(period_row: dict) -> str | None:
    """The same '<lord>|<start>' key pipeline._fact_block uses to look this
    period up while rendering the dasha tree -- lord and start (as the human-
    readable string _calc_dasha already produced) are exactly the two fields
    chart_facts._read_dasha's _dasha_period keeps, so the two sides always
    agree without either module knowing about the other's shape."""
    lord = period_row.get("lord")
    start = period_row.get("start")
    if not (isinstance(lord, str) and lord.strip() and start):
        return None
    return f"{lord.strip()}|{start}"


def _snapshot(period_row: dict, natal_asc_lon: float, natal_moon_lon: float,
              natal_moon_sign_0: int) -> dict | None:
    """One antardasha row -> Saturn's transit context at its midpoint JD, or
    None if the row lacks usable start_jd/end_jd (a malformed tree node)."""
    start_jd = period_row.get("start_jd")
    end_jd = period_row.get("end_jd")
    if not isinstance(start_jd, (int, float)) or not isinstance(end_jd, (int, float)):
        return None
    mid_jd = (float(start_jd) + float(end_jd)) / 2.0

    snap = _gochara.compute_gochara(mid_jd, natal_asc_lon, natal_moon_lon)
    saturn = next((p for p in snap.placements if p.planet_name == "Saturn"), None)
    if saturn is None:
        return None

    saturn_sign_0 = (saturn.sign - 1) % 12  # gochara is 1-based; sade_sati is 0-based
    phase = _sade_sati.sade_sati_phase_for_signs(natal_moon_sign_0, saturn_sign_0)
    # S144: Jupiter transit too -- the natural marriage/children benefic, whose
    # transit to/aspect on a target house is a first-order timing trigger the
    # Saturn-only view was blind to. Same snapshot, no extra ephemeris call;
    # fail-soft to None if Jupiter is somehow absent from the placements.
    jupiter = next((p for p in snap.placements if p.planet_name == "Jupiter"), None)
    return {
        "saturn_sign": _SIGN_NAMES[saturn_sign_0],
        "saturn_house_from_lagna": saturn.house_from_lagna,
        "saturn_house_from_moon": saturn.house_from_moon,
        "saturn_retrograde": saturn.is_retrograde,
        "sade_sati_phase": phase,
        "jupiter_sign": _SIGN_NAMES[(jupiter.sign - 1) % 12] if jupiter else None,
        "jupiter_house_from_lagna": jupiter.house_from_lagna if jupiter else None,
        "jupiter_retrograde": jupiter.is_retrograde if jupiter else None,
    }
