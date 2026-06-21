"""Gochara (transit) positions and natal-house placements.

Purpose: snapshot of transit planet positions at a given JD relative to a
natal chart.

LOCKED DECISIONS (Session 20):
- Mean Node convention (swe.MEAN_NODE) for transit Rahu/Ketu -- self-
  consistency with natal layer. JHora defaults to True Node; we deliberately
  diverge for AstroSage/Prokerala parity AND natal-layer self-consistency.
  See Session 20 SESSION_LOG.md.
- Dual-reference output: each TransitPlacement reports house_from_lagna AND
  house_from_moon. Both populated unconditionally. Answer-pipeline
  (downstream) selects per question type -- Saturn-from-Moon for
  psychological, Saturn-from-Lagna for material, per classical convention.
- Whole-sign houses (Lahiri sidereal), matching the rest of the calculation
  stack.
- Ayanamsa: swe.SIDM_LAHIRI.
- 9 classical-Vedic bodies covered: Sun, Moon, Mars, Mercury, Jupiter, Venus,
  Saturn, Rahu, Ketu. Outer planets (Uranus/Neptune/Pluto) explicitly
  excluded -- not part of Vedic classical canon. Matches navamsa.py and
  friendship.py scope conventions.
"""

from dataclasses import dataclass

import swisseph as swe

_SWE_IDS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
    "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS, "Saturn": swe.SATURN,
}

# Fixed canonical order for TransitSnapshot.placements -- downstream code may
# rely on positional access, not just dict/name lookup.
_PLANET_ORDER = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)


@dataclass(frozen=True)
class TransitPlacement:
    planet_name: str
    sign: int                  # 1-12 (1=Aries..12=Pisces), integer convention from navamsa
    longitude_sidereal: float  # degrees, 0-360
    nakshatra: int             # 1-27
    is_retrograde: bool
    house_from_lagna: int      # 1-12, whole sign
    house_from_moon: int       # 1-12, whole sign (Chandra Lagna)


@dataclass(frozen=True)
class TransitSnapshot:
    jd_ut: float
    placements: tuple[TransitPlacement, ...]  # tuple, not list -- frozen-immutability


def _calc_transit_graha(jd_ut: float, planet: str, pid: int, flags: int) -> tuple[float, bool]:
    """Sidereal longitude + retrograde flag for one graha via swe.calc_ut.

    Wrapped in try/except per project error-handling convention -- any
    pyswisseph failure (raised exception or a bad retflag) becomes a
    RuntimeError naming the planet and jd_ut, not a bare propagated error.
    Mirrors navamsa.py's _calc_graha.
    """
    try:
        xx, ret = swe.calc_ut(jd_ut, pid, flags)
    except Exception as exc:
        raise RuntimeError(
            f"compute_gochara: pyswisseph calc_ut raised for {planet} at "
            f"jd_ut={jd_ut}: {exc}"
        ) from exc
    if ret < 0:
        raise RuntimeError(
            f"compute_gochara: pyswisseph error calculating {planet} at "
            f"jd_ut={jd_ut} (retflag={ret})"
        )
    return xx[0] % 360, xx[3] < 0


def compute_gochara(
    jd_ut: float, natal_asc_lon: float, natal_moon_lon: float
) -> TransitSnapshot:
    """Inputs are primitives (sidereal longitudes in degrees); returns
    snapshot of all 9 classical Vedic bodies at jd_ut, with house mappings
    against both natal Lagna and natal Moon.

    Args:
        jd_ut: Julian Day (UT) of the transit moment.
        natal_asc_lon: Natal Lagna's sidereal longitude in degrees.
        natal_moon_lon: Natal Moon's sidereal longitude in degrees.

    Returns:
        TransitSnapshot with all 9 placements, in _PLANET_ORDER.

    Raises:
        ValueError: jd_ut <= 0, or either natal longitude outside [0, 360).
        RuntimeError: a pyswisseph ephemeris calculation failed.
    """
    if jd_ut <= 0:
        raise ValueError(f"jd_ut must be > 0, got {jd_ut}")
    if not (0.0 <= natal_asc_lon < 360.0):
        raise ValueError(f"natal_asc_lon must be in [0, 360), got {natal_asc_lon}")
    if not (0.0 <= natal_moon_lon < 360.0):
        raise ValueError(f"natal_moon_lon must be in [0, 360), got {natal_moon_lon}")

    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL

    natal_lagna_sign = int(natal_asc_lon / 30.0) % 12 + 1
    natal_moon_sign = int(natal_moon_lon / 30.0) % 12 + 1

    # TODO: migrate to helpers/ephemeris.py once that wrapper is built
    # out (currently stub).
    longitudes: dict[str, float] = {}
    retrogrades: dict[str, bool] = {}
    for planet, pid in _SWE_IDS.items():
        longitudes[planet], retrogrades[planet] = _calc_transit_graha(jd_ut, planet, pid, flags)

    rahu_lon, _ = _calc_transit_graha(jd_ut, "Rahu", swe.MEAN_NODE, flags)
    longitudes["Rahu"] = rahu_lon
    retrogrades["Rahu"] = True  # Mean Node convention -- always retrograde (LOCKED, Session 20)
    longitudes["Ketu"] = (rahu_lon + 180) % 360
    retrogrades["Ketu"] = True  # Mean Node convention -- Ketu mirrors Rahu (180deg opposite)

    placements = []
    for planet in _PLANET_ORDER:
        lon = longitudes[planet]
        sign = int(lon / 30.0) % 12 + 1
        nakshatra = int(lon / (360.0 / 27.0)) % 27 + 1
        placements.append(TransitPlacement(
            planet_name=planet,
            sign=sign,
            longitude_sidereal=lon,
            nakshatra=nakshatra,
            is_retrograde=retrogrades[planet],
            house_from_lagna=((sign - natal_lagna_sign) % 12) + 1,
            house_from_moon=((sign - natal_moon_sign) % 12) + 1,
        ))

    return TransitSnapshot(jd_ut=jd_ut, placements=tuple(placements))
