"""Chesta Bala — motional strength component of Shadbala.

ALGORITHM: BPHS 27.24-25.
  CK = (sun_true_lon - planet_mean_lon) % 360, folded 0-180°, /3.
  Mean longitude = heliocentric sidereal lon + Sun sidereal lon (mod 360).
  This is the classical geocentric mean longitude: heliocentric position
  referenced to Earth via the Sun. Continuous CK/3 formula confirmed by
  back-solving from JHora v8 non-round values (30.34, 7.81, 3.19 Virupa).

ORACLES: JHora v8 + AstroSage converge ±0.25 Virupa all 7 planets (Sulabh).
KNOWN DIVERGENCES (V1):
- Sun: Chesta = Ayana Bala (BPHS 27.18). Ayana Bala directional issue
  suspected in kala_bala.py (Session 33); investigate separately there.
- Moon: Chesta = benefic Paksha Bala (BPHS 27.18). Confirmed 3/3 charts.
- Inner planets (Mercury/Venus): heliocentric + sun formula applied
  uniformly. Inner planet geocentric mean longitude derivation differs
  from outer planets in classical texts; validate against JHora fixture.
- Session 33 investigation: speed-based (Option A) rejected 1/7 ranking.
  Discrete lookup rejected — bucket errors from mean_lon approximation.
  Synodic-midpoint approximation rejected — 60°+ error for Mars.
  Final: heliocentric-derived mean longitude + continuous CK/3.
"""

import swisseph as swe

_FLAGS_SID  = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
_FLAGS_HELI = swe.FLG_SWIEPH | swe.FLG_HELCTR   # heliocentric, tropical

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

    # ── Sun: Chesta = Ayana Bala (BPHS 27.18) ────────────────────────────────
    result["sun"] = {"chesta": round(ayana_result["Sun"], 4)}

    # ── Moon and Sun positions needed for paksha detection and Tara Grahas ────
    moon_lon = swe.calc_ut(jd_ut, swe.MOON, _FLAGS_SID)[0][0] % 360.0
    sun_lon  = swe.calc_ut(jd_ut, swe.SUN,  _FLAGS_SID)[0][0] % 360.0

    # ── Moon: Chesta = benefic paksha score ───────────────────────────────────
    # Copy of _paksha_bala() Shukla/Krishna detection (kala_bala.py lines 199-201)
    is_shukla = ((moon_lon - sun_lon) % 360.0) < 180.0

    moon_paksha = paksha_result["moon"]
    if is_shukla:
        result["moon"] = {"chesta": round(moon_paksha, 4)}
    else:
        result["moon"] = {"chesta": round(60.0 - moon_paksha, 4)}

    # ── Tara Grahas: heliocentric mean longitude + CK/3 (BPHS 27.24-25) ─────
    ayanamsa = swe.get_ayanamsa_ut(jd_ut)

    for planet in _TARA_GRAHAS:
        pid = _SWE_IDS[planet]

        geo_true  = swe.calc_ut(jd_ut, pid, _FLAGS_SID )[0][0] % 360.0  # noqa: F841
        heli_trop = swe.calc_ut(jd_ut, pid, _FLAGS_HELI)[0][0] % 360.0
        heli_sid  = (heli_trop - ayanamsa) % 360.0
        mean_lon  = (heli_sid + sun_lon) % 360.0

        CK = (sun_lon - mean_lon) % 360.0
        if CK > 180:
            CK = 360 - CK

        result[planet.lower()] = {"chesta": round(CK / 3, 4)}

    return result
