"""Astro Agent -- YOGA FACTS composer (Path B, S133).

Runs the yoga detector over an AUGMENTED chart-facts block and returns the
verdicts as a new fact class for the interpreter. Composed by the CALLER
(frontend/app.py), exactly like the D9 navamsa is (S130), so `chart_facts`
stays a pure restatement and this module owns the extra inputs the yoga layer
needs but the interpreter payload must NOT carry.

WHAT GOES WHERE.
  - The detector needs chara karakas, the Ghati/Hora Lagna SIGNS, and each
    planet's degree-in-sign (for degree-accurate Pancha Mahapurusha). Those are
    computed here and fed to `detect_yogas` in a LOCAL dict -- they never enter
    `chart_facts`, so the interpreter payload stays degree-free (S129b/S130).
  - Only the yoga VERDICTS (`{"fired": [...], "ruled_out": [...]}`) are returned
    and merged into `chart_facts["yogas"]`. The growth contract is honoured by
    adding "yogas" to `capability_gate.FACT_BLOCK_PROVIDES` in the same change.

FAIL-SOFT. Any failure costs the yoga facts, never the answer: the function
returns `{"fired": [], "ruled_out": [], "error": "..."}` and never raises. Same
posture as the D9 wiring.

NO EPHEMERIS SURPRISES. Coordinates and the birth moment come from the chart's
own `birth_details` (already geocoded by calculate_chart), so this module does
no geocoding; special lagnas are reconstructed from those and the calc modules
that already own the astronomy.

Python 3.11.
"""
from __future__ import annotations

from agent.calculations.yogas.detector import detect_yogas

_CHARA = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu")


def build_yoga_facts(chart: dict, chart_facts: dict) -> dict:
    """Compute the chart's yogas. Returns a YogaReport dict; never raises.

    Args:
        chart: the dict from agent.chart_calculator.calculate_chart() -- read
            for planetary longitudes, birth details, and (via chart_facts) the
            navamsa the caller already composed.
        chart_facts: the built fact block (build_chart_facts output, with
            navamsa already attached). Read-only; not mutated.
    """
    try:
        det = dict(chart_facts)  # shallow copy: add detector-only inputs locally
        pp = chart.get("planetary_positions") or {}

        det["chara_karakas"] = _chara_karakas(pp)
        gl, hl = _special_lagna_signs(chart)
        if gl:
            det["ghati_lagna_sign"] = gl
        if hl:
            det["hora_lagna_sign"] = hl
        det["planet_degrees"] = {g: (r["longitude"] % 30.0)
                                 for g, r in pp.items()
                                 if isinstance(r, dict) and "longitude" in r}

        return detect_yogas(det).to_dict()
    except Exception as e:  # noqa: BLE001 -- a bad fact block costs yogas, not the answer
        return {"fired": [], "ruled_out": [], "errors": [f"{type(e).__name__}: {e}"],
                "detector_version": "unavailable"}


def _chara_karakas(planetary_positions: dict) -> dict:
    """{karaka_abbr: planet} from the eight sidereal longitudes (Ketu excluded
    by PVR's scheme). Empty dict if the longitudes are not all present."""
    from agent.calculations.jaimini.karakas import compute_chara_karakas
    lons = {}
    for g in _CHARA:
        row = planetary_positions.get(g)
        if not isinstance(row, dict) or "longitude" not in row:
            return {}
        lons[g] = row["longitude"] % 360.0
    return {abbr: planet for abbr, planet in compute_chara_karakas(lons).karakas}


def _special_lagna_signs(chart: dict):
    """(ghati_lagna_sign, hora_lagna_sign) reconstructed from the birth details
    calculate_chart() already resolved. (None, None) if unavailable."""
    from agent.calculations.jaimini.special_lagnas import compute_special_lagnas
    from agent.chart_calculator import to_julian_day, _local_datetime
    bd = chart.get("birth_details") or {}
    lat, lon = bd.get("lat"), bd.get("lon")
    dob, tob = bd.get("dob"), bd.get("tob")
    if None in (lat, lon, dob, tob):
        return (None, None)
    _, utc_dt = to_julian_day(dob, tob, float(lat), float(lon))
    moment = _local_datetime(utc_dt, float(lat), float(lon))
    sl = compute_special_lagnas(moment, float(lat), float(lon))
    return (sl["ghati_lagna"]["sign"], sl["hora_lagna"]["sign"])
