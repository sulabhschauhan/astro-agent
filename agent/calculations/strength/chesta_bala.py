"""Chesta Bala — motional strength component of Shadbala.

ALGORITHM: BPHS 27.24-25.
  CK = (sun_true_lon - planet_mean_lon) % 360, folded 0-180°, /3.
  Mean longitude = heliocentric sidereal lon + Sun sidereal lon (mod 360).
  This is the classical geocentric mean longitude: heliocentric position
  referenced to Earth via the Sun. Continuous CK/3 formula confirmed by
  back-solving from JHora v8 non-round values (30.34, 7.81, 3.19 Virupa).

ORACLES: JHora v8 + AstroSage converge ±0.25 Virupa all 7 planets (Sulabh).
KNOWN DIVERGENCES (V1):
- Sun: RESOLVED Session 47. BPHS 27.18's "Chesta = Ayana Bala" holds only
  loosely — AstroSage and JHora both converge on chesta_sun = 30.0 + kranti
  (signed, no abs, no doubling), NOT the doubled Ayana Bala value. Formula is
  dual-oracle back-solved, not classically cited. Validated ±0.97 worst-case
  vs AstroSage 4/4 charts; downstream Ishta/Kashta ±0.73 worst vs JHora 4/4.
  See diagnostics/sun_chesta_characterization_20260704.py (attempt 1: undoubled
  Ayana/2, failed 0/4) and the Session 47 attempt-2 back-solve (30+kranti,
  passed 4/4) for the full candidate comparison. Revisit trigger: any 5th
  chart breaching ±1.0.
- Moon: Chesta = benefic Paksha Bala (BPHS 27.18). Confirmed exact 3/3 charts.
- Tara Grahas: elongation formula (CK = sun_lon - planet_true_lon, /3).
  JHora uses Surya Siddhanta mean daily motion constants for mean longitude —
  not derivable from Swiss Ephemeris. Tagged V1.1.
  Deltas vs JHora v8: Jupiter/Saturn ±2, Mars/Mercury/Venus ±10 (Surbhi worst).
  Do NOT re-investigate. 5 approaches tested and rejected across sessions 33-35.
  See CLAUDE.md §Chesta Bala.
"""

from math import asin, degrees, radians, sin

import swisseph as swe

_FLAGS_SID  = swe.FLG_SWIEPH | swe.FLG_SIDEREAL

_SWE_IDS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
    "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS, "Saturn": swe.SATURN,
}

_TARA_GRAHAS = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"]


def compute_chesta_bala(
    chart_data: dict,
    paksha_result: dict,
    ayana_result: dict,
) -> dict:
    """Compute Chesta Bala (motional strength) for all 7 classical planets.

    Returns: dict keyed by lowercase planet name.
    Each value: {"chesta": float}  — Virupa.

    Args:
        chart_data:    output of calculate_chart()
        paksha_result: {planet_lowercase: paksha_float} — extract from
                       compute_kala_bala() output as
                       {p: kala[p]["paksha"] for p in kala}.
        ayana_result:  {planet_capitalized: ayana_float} — extract from
                       compute_kala_bala() output as
                       {p.capitalize(): kala[p]["ayana"] for p in kala}.
    """
    try:
        jd_ut: float = chart_data["meta"]["jd_ut"]
    except KeyError as exc:
        raise ValueError(f"compute_chesta_bala: missing key in chart_data: {exc}") from exc

    swe.set_sid_mode(swe.SIDM_LAHIRI)

    result = {}

    # ── Moon and Sun positions needed for paksha detection and Tara Grahas ────
    moon_lon = swe.calc_ut(jd_ut, swe.MOON, _FLAGS_SID)[0][0] % 360.0
    sun_lon  = swe.calc_ut(jd_ut, swe.SUN,  _FLAGS_SID)[0][0] % 360.0

    # ── Sun: chesta_sun = 30.0 + kranti (dual-oracle back-solved, Session 47) ──
    ayanamsa = swe.get_ayanamsa_ut(jd_ut)
    sayana_lon = (sun_lon + ayanamsa) % 360.0
    eps_true = swe.calc_ut(jd_ut, swe.ECL_NUT, _FLAGS_SID)[0][0]
    kranti = degrees(asin(sin(radians(eps_true)) * sin(radians(sayana_lon))))
    result["sun"] = {"chesta": round(30.0 + kranti, 4)}

    # ── Moon: Chesta = benefic paksha score ───────────────────────────────────
    # Copy of _paksha_bala() Shukla/Krishna detection (kala_bala.py lines 199-201)
    is_shukla = ((moon_lon - sun_lon) % 360.0) < 180.0

    moon_paksha = paksha_result["moon"]
    if is_shukla:
        result["moon"] = {"chesta": round(moon_paksha, 4)}
    else:
        result["moon"] = {"chesta": round(60.0 - moon_paksha, 4)}

    # ── Tara Grahas: elongation formula CK/3 (BPHS 27.24-25) ────────────────
    for planet in _TARA_GRAHAS:
        pid = _SWE_IDS[planet]
        geo_lon = swe.calc_ut(jd_ut, pid, _FLAGS_SID)[0][0] % 360.0
        CK = (sun_lon - geo_lon) % 360.0
        if CK > 180.0:
            CK = 360.0 - CK
        result[planet.lower()] = {"chesta": round(CK / 3.0, 4)}

    return result
