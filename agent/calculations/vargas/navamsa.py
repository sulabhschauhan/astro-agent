"""Navamsa (D9) — the first and most consulted divisional chart (varga) in
classical Vedic astrology; used for marriage/spouse analysis and to gauge
the deeper strength of a D1 placement via vargottama (D1 sign == D9 sign).

CITATIONS:
- PVR Narasimha Rao, "Vedic Astrology: An Integrated Approach", Ch. 7 —
  Navamsa construction: the pada formula (each rasi divided into 9 equal
  3°20' parts) and the movable/fixed/dual starting-sign convention.
- BPHS (Brihat Parashara Hora Shastra) Ch. 6 — cross-reference; agrees with
  PVR on both the pada formula and the starting-sign convention.
- JHora + AstroSage — numerical validation oracles for the 4 reference
  charts (Sulabh, Surbhi, Sheridan, David). Fixture values pending manual
  extraction (see tests/calculations/vargas/test_navamsa.py, Layer B).

DESIGN NOTE: NavamsaChart is the first dataclass-shaped varga in
calculations/. If subsequent vargas (D10/D7/D12) converge on an identical
shape, refactor to a generic VargaChart at the P2.5 boundary — not before.
"""

from dataclasses import dataclass

import swisseph as swe

_CANONICAL_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

_SWE_IDS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
    "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS, "Saturn": swe.SATURN,
}

# PVR Ch. 7 / BPHS Ch. 6: each rasi's Navamsa count starts from the movable
# sign of its own triplicity (trikona) — fire triplicity (Aries, Leo,
# Sagittarius) starts from Aries; earth (Taurus, Virgo, Capricorn) from
# Capricorn; air (Gemini, Libra, Aquarius) from Libra; water (Cancer,
# Scorpio, Pisces) from Cancer. Equivalent classical phrasing: movable
# signs start from themselves, fixed signs start from the 9th sign from
# themselves, dual signs start from the 5th sign from themselves — both
# phrasings produce this same table. Hardcoded (not computed from modality
# at runtime) so this comment block remains the citation anchor.
_NAVAMSA_START_SIGN: dict[str, str] = {
    "Aries": "Aries", "Taurus": "Capricorn", "Gemini": "Libra", "Cancer": "Cancer",
    "Leo": "Aries", "Virgo": "Capricorn", "Libra": "Libra", "Scorpio": "Cancer",
    "Sagittarius": "Aries", "Capricorn": "Capricorn", "Aquarius": "Libra", "Pisces": "Cancer",
}

assert len(_NAVAMSA_START_SIGN) == 12, (
    f"_NAVAMSA_START_SIGN must have exactly 12 entries, got {len(_NAVAMSA_START_SIGN)}"
)
assert set(_NAVAMSA_START_SIGN.keys()) == set(_CANONICAL_SIGNS), (
    "_NAVAMSA_START_SIGN keys must be exactly the 12 canonical rasis"
)
assert all(v in _CANONICAL_SIGNS for v in _NAVAMSA_START_SIGN.values()), (
    "_NAVAMSA_START_SIGN values must all be canonical sign names"
)


@dataclass(frozen=True)
class NavamsaPlacement:
    planet: str
    d1_sign: str              # source sign in D1 (for vargottama detection)
    d1_longitude: float       # 0-360 sidereal, retained for traceability
    pada_index: int           # 0-8 within d1_sign
    d9_sign: str              # resulting Navamsa sign
    d9_house: int             # 1-12, Whole Sign from d9_lagna_sign
    retrograde: bool          # inherited from D1 ephemeris call


@dataclass(frozen=True)
class NavamsaChart:
    d9_lagna_sign: str
    d9_lagna_pada_index: int           # 0-8 within natal lagna sign
    d9_lagna_d1_longitude: float       # for traceability
    placements: dict[str, NavamsaPlacement]  # keyed by planet name
    ayanamsa: float                    # Lahiri ayanamsa at jd_ut, for audit


def _pada_index(longitude: float) -> int:
    """PVR Ch. 7 / BPHS Ch. 6 pada formula: each 30deg rasi divides into 9
    equal 3deg20' (30.0/9.0) padas. Exact arithmetic, not a rounded 3.333
    constant, to avoid compounding float error across the divide.
    """
    longitude_in_rasi = longitude % 30.0
    pada = int(longitude_in_rasi / (30.0 / 9.0))
    return min(pada, 8)  # defensive clamp -- the modulo above already keeps this <9


def _d9_sign(longitude: float) -> tuple[str, int]:
    """Resolve (d9_sign, pada_index) for a sidereal longitude per the
    movable/fixed/dual starting-sign convention in _NAVAMSA_START_SIGN.
    """
    rasi = _CANONICAL_SIGNS[int(longitude / 30.0) % 12]
    pada = _pada_index(longitude)
    start_idx = _CANONICAL_SIGNS.index(_NAVAMSA_START_SIGN[rasi])
    d9_idx = (start_idx + pada) % 12
    return _CANONICAL_SIGNS[d9_idx], pada


def _calc_graha(jd_ut: float, planet: str, pid: int, flags: int) -> tuple[float, bool]:
    """Sidereal longitude + retrograde flag for one graha via swe.calc_ut.

    Wrapped in try/except per project error-handling convention -- any
    pyswisseph failure (raised exception or a bad retflag) becomes a
    RuntimeError naming the planet and jd_ut, not a bare propagated error.
    """
    try:
        xx, ret = swe.calc_ut(jd_ut, pid, flags)
    except Exception as exc:
        raise RuntimeError(
            f"compute_navamsa: pyswisseph calc_ut raised for {planet} at "
            f"jd_ut={jd_ut}: {exc}"
        ) from exc
    if ret < 0:
        raise RuntimeError(
            f"compute_navamsa: pyswisseph error calculating {planet} at "
            f"jd_ut={jd_ut} (retflag={ret})"
        )
    return xx[0] % 360, xx[3] < 0


def compute_navamsa(jd_ut: float, asc_lon_sidereal: float) -> NavamsaChart:
    """
    Compute the Navamsa (D9) chart: sidereal D1 longitudes for the 9 grahas
    plus the natal Lagna, each mapped through the classical pada -> D9-sign
    transform (see module docstring for the PVR Ch. 7 / BPHS Ch. 6 citation).

    Pure function of (jd_ut, asc_lon_sidereal) -- no I/O beyond the
    pyswisseph ephemeris calls.

    Args:
        jd_ut: Julian Day (UT), e.g. from chart_calculator.to_julian_day or
            swe.julday directly.
        asc_lon_sidereal: Natal Lagna's sidereal longitude in degrees,
            0 <= asc_lon_sidereal < 360 (Lahiri ayanamsa, project-wide
            convention).

    Returns:
        NavamsaChart with the D9 Lagna and all 9 graha placements.

    Raises:
        ValueError: jd_ut <= 0, or asc_lon_sidereal outside [0, 360).
        RuntimeError: a pyswisseph ephemeris calculation failed.
    """
    if jd_ut <= 0:
        raise ValueError(f"jd_ut must be > 0, got {jd_ut}")
    if not (0.0 <= asc_lon_sidereal < 360.0):
        raise ValueError(
            f"asc_lon_sidereal must be in [0, 360), got {asc_lon_sidereal}"
        )

    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayanamsa = swe.get_ayanamsa_ut(jd_ut)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL

    # TODO: migrate to helpers/ephemeris.py once that wrapper is built
    # out (currently stub).
    longitudes: dict[str, float] = {}
    retrogrades: dict[str, bool] = {}
    for planet, pid in _SWE_IDS.items():
        longitudes[planet], retrogrades[planet] = _calc_graha(jd_ut, planet, pid, flags)

    rahu_lon, _ = _calc_graha(jd_ut, "Rahu", swe.MEAN_NODE, flags)
    longitudes["Rahu"] = rahu_lon
    retrogrades["Rahu"] = True  # Mean Node convention -- always retrograde
    longitudes["Ketu"] = (rahu_lon + 180) % 360
    retrogrades["Ketu"] = True  # Mean Node convention -- Ketu mirrors Rahu (180deg opposite)

    lagna_d9_sign, lagna_pada = _d9_sign(asc_lon_sidereal)

    placements: dict[str, NavamsaPlacement] = {}
    for planet, lon in longitudes.items():
        d1_sign = _CANONICAL_SIGNS[int(lon / 30.0) % 12]
        d9_sign, pada = _d9_sign(lon)
        d9_house = ((_CANONICAL_SIGNS.index(d9_sign)
                     - _CANONICAL_SIGNS.index(lagna_d9_sign)) % 12) + 1
        placements[planet] = NavamsaPlacement(
            planet=planet,
            d1_sign=d1_sign,
            d1_longitude=lon,
            pada_index=pada,
            d9_sign=d9_sign,
            d9_house=d9_house,
            retrograde=retrogrades[planet],
        )

    return NavamsaChart(
        d9_lagna_sign=lagna_d9_sign,
        d9_lagna_pada_index=lagna_pada,
        d9_lagna_d1_longitude=asc_lon_sidereal,
        placements=placements,
        ayanamsa=ayanamsa,
    )
