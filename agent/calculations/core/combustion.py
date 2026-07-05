"""Combustion (Asta) detection for the 6 non-Sun classical planets.

CITATION:
  Orb source: Surya Siddhanta convention — Moon 12°, Mars 17°, Mercury 14°
  (12° retrograde), Jupiter 11°, Venus 10° (8° retrograde), Saturn 15°.
  PVR "Vedic Astrology: An Integrated Approach" is SILENT on combustion
  orbs — p.114 (Budha-Aditya Yoga note) is qualitative only ("too close to
  Sun"), no degrees, no retrograde rule anywhere in the book. PVR-first
  hierarchy therefore falls through to classical convention + user-perceived
  correctness (AstroSage Deeptadi avastha 'Vikala' = combust; tiebreaker
  principle, CLAUDE.md Locked Decisions).

  KNOWN DIVERGENCE: PyJHora const.py lines 608-609 uses direct orbs
  [12,17,14,10,11,15] (Jupiter/Venus SWAPPED vs classical: Jupiter 10,
  Venus 11) and retro orbs [12,8,12,11,8,16] (Mars 8, Saturn 16 —
  non-classical), with a commented-out alternate [12,17,12,8,11,15]
  matching the classical retro convention. We follow classical, not
  PyJHora's active line. Outcome-sensitive only for a planet sitting
  10-11 deg from Sun.

  V1 SCOPE NOTES:
  (1) No deep/casual combustion sub-threshold — no classical source at
      hand quantifies one; binary flag + exact separation only.
  (2) Moon combustion included per table but interpretively overlaps
      Paksha Bala (new-Moon weakness already captured there) —
      downstream consumers should not double-penalize.

  Validation anchors (informational): Sulabh — zero combust planets
  (Mercury-Sun 14.65 deg > 14; AstroSage p.23 Deeptadi shows no Vikala).
  Surbhi — Mercury ~3.59 deg and Jupiter ~4.98 deg from Sun, both combust.

EPHEMERIS NOTE (Session 52 migration): the per-planet sidereal longitude
loop delegates to helpers/ephemeris.py's sidereal_longitude() (not
sidereal_position() -- retrograde is sourced from chart_data, not from a
speed reading here). See inline comment at the call site for why the
RuntimeError wrapping is kept rather than letting ephemeris.EphemerisError
propagate unwrapped.
"""

import swisseph as swe

from agent.calculations.helpers import ephemeris

_PLANETS: list[str] = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

_SWE_IDS: dict[str, int] = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
    "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS, "Saturn": swe.SATURN,
}

# Surya Siddhanta direct-motion combustion orbs (degrees).
_ORB_DIRECT: dict[str, float] = {
    "Moon": 12.0, "Mars": 17.0, "Mercury": 14.0,
    "Jupiter": 11.0, "Venus": 10.0, "Saturn": 15.0,
}

# Retrograde overrides — only Mercury and Saturn's classical counterparts
# (Mercury, Venus) narrow their orb when retrograde; all others unchanged.
_ORB_RETRO: dict[str, float] = {"Mercury": 12.0, "Venus": 8.0}


def _min_separation(lon_a: float, lon_b: float) -> float:
    """Minimum angular distance between two longitudes (0-360°), result in [0,180]."""
    d = abs(lon_a - lon_b) % 360.0
    if d > 180.0:
        d = 360.0 - d
    return d


def compute_combustion(chart_data: dict) -> dict:
    """Detect combustion (Asta) for the 6 non-Sun classical planets.

    Args:
        chart_data: output of calculate_chart(). Required keys:
            ["meta"]["jd_ut"],
            ["planetary_positions"][planet]["retrograde"] for planet in
            Moon, Mars, Mercury, Jupiter, Venus, Saturn.
            Planet longitudes are re-derived from pyswisseph (not in chart_data).

    Returns:
        Dict keyed by lowercase planet name ("moon" … "saturn"). Each value
        is a dict: is_combust (bool), separation_deg (float, 4dp),
        orb_used (float), retrograde (bool).
        Rahu/Ketu are out of scope (never combust); Sun is the reference
        body, not a key in the output.

    Raises:
        ValueError: required key absent in chart_data.
        RuntimeError: pyswisseph ephemeris calculation failed.
    """
    try:
        jd_ut: float = chart_data["meta"]["jd_ut"]
    except KeyError as exc:
        raise ValueError(
            f"compute_combustion: missing key in chart_data['meta']: {exc}"
        ) from exc

    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # chart_data["planetary_positions"] carries retrograde flags but not
    # longitude. Re-derive precise sidereal longitudes from the ephemeris.
    # Session 52 migration: delegates to helpers/ephemeris.py's
    # sidereal_longitude() (only longitude is read here -- retrograde
    # comes from chart_data above, not from this call, so sidereal_
    # position()'s speed field would go unused). The except clause below
    # re-wraps ephemeris.EphemerisError into this module's own RuntimeError
    # wording, preserving the planet NAME (not ephemeris.py's numeric swe
    # id) in the message -- test_c_calc_ut_raising_surfaces_runtimeerror
    # asserts pytest.raises(RuntimeError, match="Sun").
    planet_lons: dict[str, float] = {}
    for planet, pid in _SWE_IDS.items():
        try:
            planet_lons[planet] = ephemeris.sidereal_longitude(jd_ut, pid)
        except ephemeris.EphemerisError as exc:
            raise RuntimeError(
                f"compute_combustion: ephemeris failure for {planet} "
                f"at jd_ut={jd_ut}: {exc.detail}"
            ) from exc

    lon_sun = planet_lons["Sun"]

    result: dict[str, dict] = {}
    for planet in _PLANETS:
        try:
            retrograde: bool = bool(
                chart_data["planetary_positions"][planet]["retrograde"]
            )
        except KeyError as exc:
            raise ValueError(
                f"compute_combustion: missing "
                f"planetary_positions['{planet}']['retrograde']: {exc}"
            ) from exc

        separation_deg = _min_separation(planet_lons[planet], lon_sun)
        orb_used = _ORB_RETRO[planet] if (retrograde and planet in _ORB_RETRO) else _ORB_DIRECT[planet]
        is_combust = separation_deg < orb_used

        result[planet.lower()] = {
            "is_combust": is_combust,
            "separation_deg": round(separation_deg, 4),
            "orb_used": orb_used,
            "retrograde": retrograde,
        }

    return result
