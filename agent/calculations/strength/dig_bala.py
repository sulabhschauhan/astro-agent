# See CLAUDE.md § "Known Source Divergences (V1)" — no Dig Bala divergence; AstroSage values are primary oracle.
"""Dig Bala — directional strength component of Shadbala.

Specification: BPHS Ch. 27.5, B.V. Raman "Graha and Bhava Balas".

Dig-strong cardinal point per planet:
  Sun, Mars         → MC   (meridian cusp, ascmc[1])
  Mercury, Jupiter  → ASC  (ascendant, ascmc[0])
  Moon, Venus       → IC   ((MC + 180) % 360)
  Saturn            → DSC  ((ASC + 180) % 360)

Formula:
    delta = abs(planet_lon - cusp_lon)
    arc   = min(delta, 360.0 - delta)
    dig   = (180.0 - arc) / 3.0      # Virupa; range [0, 60]

True sidereal MC, not Lagna + 270°:
  ASC and MC are derived from swe.houses_ex(..., b'W', swe.FLG_SIDEREAL).
  At non-equatorial latitudes (e.g. Calcutta 22.5°N) the true MC drifts
  measurably from Lagna ± 270°; the Lagna-quadrant approximation breaks
  Sun parity for charts like Sulabh where this drift is significant.

All values in Virupa (1 Rupa = 60 Virupa).

EPHEMERIS NOTE (Session 52 migration): the per-planet sidereal longitude
loop delegates to helpers/ephemeris.py's sidereal_longitude(). The
swe.houses_ex() call for ASC/MC is a separate pyswisseph API (not
swe.calc_ut()) and is out of this migration's scope.
"""

import swisseph as swe

from agent.calculations.helpers import ephemeris

_PLANETS: list[str] = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

_SWE_IDS: dict[str, int] = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
    "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS, "Saturn": swe.SATURN,
}

# BPHS 27.5 / Raman: dig-strong cardinal point per planet.
_DIG_STRONG_CUSP: dict[str, str] = {
    "Sun":     "mc",
    "Mars":    "mc",
    "Mercury": "asc",
    "Jupiter": "asc",
    "Moon":    "ic",
    "Venus":   "ic",
    "Saturn":  "dsc",
}


# ── Formula helper ────────────────────────────────────────────────────────────

def _dig_score(planet_lon: float, cusp_lon: float) -> float:
    """Dig Bala score (Virupa) for a planet relative to its dig-strong cusp.

    60 Virupa at the cusp, 0 Virupa at the opposite point.
    """
    delta = abs(planet_lon - cusp_lon)
    arc   = min(delta, 360.0 - delta)
    return max(0.0, (180.0 - arc) / 3.0)


# ── Public API ────────────────────────────────────────────────────────────────

def compute_dig_bala(chart_data: dict) -> dict:
    """Compute Dig Bala (directional strength) for all 7 classical planets.

    Args:
        chart_data: output of calculate_chart(). Required keys:
            ["meta"]["jd_ut"], ["meta"]["asc_lon_sidereal"],
            ["birth_details"]["lat"], ["birth_details"]["lon"].
            Planet longitudes are re-derived from pyswisseph (not in chart_data).

    Returns:
        Dict keyed by lowercase planet name ("sun" … "saturn"). Each value is
        {"dig": float (Virupa, range [0, 60])}.

    Raises:
        ValueError: required key absent in chart_data.
        RuntimeError: ASC sanity check mismatch, or (as
            ephemeris.EphemerisError, a RuntimeError subclass) a
            pyswisseph ephemeris calculation failed.
    """
    try:
        jd_ut: float     = chart_data["meta"]["jd_ut"]
        asc_check: float = chart_data["meta"]["asc_lon_sidereal"]
        lat: float       = chart_data["birth_details"]["lat"]
        lon_geo: float   = chart_data["birth_details"]["lon"]
    except KeyError as exc:
        raise ValueError(
            f"compute_dig_bala: missing key in chart_data: {exc}"
        ) from exc

    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # Re-derive precise sidereal longitudes — do not trust chart_data.
    # Session 52 migration: delegates to helpers/ephemeris.py's
    # sidereal_longitude(); calc_ut failures now surface as
    # ephemeris.EphemerisError (a RuntimeError subclass) naming the planet
    # id and jd_ut, rather than this module's own RuntimeError wording.
    planet_lons: dict[str, float] = {}
    for planet, pid in _SWE_IDS.items():
        planet_lons[planet] = ephemeris.sidereal_longitude(jd_ut, pid)

    # True sidereal ASC and MC (Whole Sign, Lahiri ayanamsa).
    try:
        _cusps, ascmc = swe.houses_ex(jd_ut, lat, lon_geo, b'W', swe.FLG_SIDEREAL)
    except Exception as exc:
        raise RuntimeError(
            f"compute_dig_bala: swe.houses_ex raised "
            f"at jd_ut={jd_ut}, lat={lat}, lon={lon_geo}: {exc}"
        ) from exc

    asc_lon = ascmc[0] % 360.0
    mc_lon  = ascmc[1] % 360.0

    if abs(asc_lon - asc_check) >= 0.01:
        raise RuntimeError(
            f"compute_dig_bala: ASC mismatch — computed={asc_lon:.4f}, "
            f"chart_data={asc_check:.4f}; check ayanamsa/house-system convention"
        )

    ic_lon  = (mc_lon  + 180.0) % 360.0
    dsc_lon = (asc_lon + 180.0) % 360.0
    cusps_map: dict[str, float] = {
        "asc": asc_lon,
        "mc":  mc_lon,
        "ic":  ic_lon,
        "dsc": dsc_lon,
    }

    result: dict[str, dict] = {}
    for planet in _PLANETS:
        cusp_name = _DIG_STRONG_CUSP[planet]
        cusp_lon  = cusps_map[cusp_name]
        dig       = _dig_score(planet_lons[planet], cusp_lon)
        result[planet.lower()] = {"dig": round(dig, 4)}

    return result
