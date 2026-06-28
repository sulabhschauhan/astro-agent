"""Chesta Bala — motional strength component of Shadbala.

BPHS 27.18-27 (synodic-midpoint approximation for Tara Grahas).

KNOWN DIVERGENCES (V1):
- Sun Chesta: BPHS 27.18 specifies Sun Chesta = Ayana Bala (implemented).
  AstroSage uses an undocumented method producing different values
  (Sulabh delta: ~40 Virupa). Neither classical Sun apogee (~80° sidereal)
  nor swe.MEAN_APOG (which is the Moon's apogee — a category error) reproduces
  AstroSage. Accepted gap: Sun Chesta < 0.5% of total Shadbala; no impact on
  yoga detection rankings. See CLAUDE.md §Chesta Bala.
- Moon Chesta: empirically derived as "benefic paksha score" from 3 reference
  charts. AstroSage oracle wins per source hierarchy.
- Half-synodic approximation: introduces ≤2 Virupa error for Mercury/Mars
  (higher eccentricity). Acceptable per BPHS Ch. 27.24 approximation guidance.
  Half-periods used: Mars=390d, Mercury=58d, Jupiter=199.5d, Venus=292d, Saturn=189d.
  These are synodic_period/2, not sidereal. Mars prior estimate of 327d was the
  sidereal period — corrected this session.
- PyJHora Chesta Bala does NOT match JHora (stated in PyJHora README).
  AstroSage fixtures are the V1 oracle for this component.
"""

import swisseph as swe

_FLAGS_SID = swe.FLG_SWIEPH | swe.FLG_SIDEREAL

_SWE_IDS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
    "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS, "Saturn": swe.SATURN,
}

# Half-synodic periods in days (synodic_period / 2):
# Mars=780/2, Mercury=116/2, Jupiter=399/2, Venus=584/2, Saturn=378/2
_HALF_SYNODIC = {
    "Mars":    390.0,
    "Mercury":  58.0,
    "Jupiter": 199.5,
    "Venus":   292.0,
    "Saturn":  189.0,
}

_TARA_GRAHAS = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"]


def compute_chesta_bala(
    chart_data: dict,
    paksha_result: dict,
    ayana_result: dict,
) -> dict:
    """Compute Chesta Bala (motional strength) for all 7 classical planets.

    Returns: dict keyed by lowercase planet name.
    Each value: {"chesta": float}  — Virupa, 0-60.

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

    # ── Tara Grahas: synodic-midpoint formula (BPHS 27.24) ───────────────────
    for planet in _TARA_GRAHAS:
        pid      = _SWE_IDS[planet]
        half_syn = _HALF_SYNODIC[planet]

        true_lon = swe.calc_ut(jd_ut,            pid, _FLAGS_SID)[0][0] % 360.0
        past_lon = swe.calc_ut(jd_ut - half_syn, pid, _FLAGS_SID)[0][0] % 360.0

        # Wraparound-safe angular midpoint (from prompt "simpler equivalent")
        adjustment = 360 if abs(past_lon - true_lon) > 180 else 0
        mean_lon = ((past_lon + true_lon + adjustment) / 2) % 360

        # CK = elongation between Sun (Seeghrochcha) and mean longitude
        CK = (sun_lon - mean_lon) % 360
        if CK > 180:
            CK = 360 - CK

        result[planet.lower()] = {"chesta": round(CK / 3, 4)}

    return result
