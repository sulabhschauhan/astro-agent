# See CLAUDE.md § "Known Source Divergences (V1)" — Saptavargaja Bala scoring.
"""Sthana Bala — positional strength component of Shadbala.

Specification: BPHS Ch. 27, B.V. Raman "Graha and Bhava Balas".
Five sub-components implemented here:
  1. Ochcha Bala (max 60 Virupa) — distance from debilitation point.
  2. Saptavargaja Bala (max 225 Virupa) — Panchadha Maitri compound
     friendship over 7 vargas (D1/D2/D3/D7/D9/D12/D30).
  3. Ojayugmarasyamsa Bala (max 30 Virupa) — odd/even sign placement
     in D1 and D9.
  4. Kendra Bala (max 60 Virupa) — angular house strength.
  5. Drekkana Bala (fixed 1 Virupa per AstroSage/JHora parity) — BPHS 27.6
     specifies a binary 15/0 scheme (male/neutral/female × decanate) but
     both AstroSage and JHora emit 1 Virupa flat; locked per the three-tier
     source hierarchy (AstroSage parity > classical text, Session 29).

sthan_total = ochcha + saptavargaja + ojayugma + kendra + drekkana.
All values in Virupa (1 Rupa = 60 Virupa).

SOURCE DIVERGENCE — Saptavargaja scoring tiers:
  BPHS 27.2-4 (implemented):  Mooltrikona=45, Svastha=30, Pramudita=20,
                               Shanta=15, Din=10, Duhkhita=4, Khala=2
  B.V. Raman (Graha & Bhava): 22.5 / 15 / 7.5 / 3.75 / 1.875
  AstroSage (observed):        unpublished — cannot be reverse-engineered
                               consistently from public PDFs.
  AstroSage Saptavargaja fixtures are INFORMATIONAL, not test oracles.

EPHEMERIS NOTE (Session 52 migration): the per-planet sidereal longitude
loop delegates to helpers/ephemeris.py's sidereal_longitude().
"""

import swisseph as swe

from agent.calculations.core._dignity_tables import MOOLATRIKONA
from agent.calculations.core.friendship import natural_friendship, pancha_dha_maitri
from agent.calculations.helpers import ephemeris
from agent.calculations.vargas.navamsa import compute_navamsa

_SIGN_NAMES: list[str] = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
_SIGN_TO_IDX: dict[str, int] = {s: i for i, s in enumerate(_SIGN_NAMES)}

# Traditional sign lords indexed by sign (0=Aries … 11=Pisces); no outer planets.
_SIGN_LORDS: list[str] = [
    "Mars",    # 0  Aries
    "Venus",   # 1  Taurus
    "Mercury", # 2  Gemini
    "Moon",    # 3  Cancer
    "Sun",     # 4  Leo
    "Mercury", # 5  Virgo
    "Venus",   # 6  Libra
    "Mars",    # 7  Scorpio
    "Jupiter", # 8  Sagittarius
    "Saturn",  # 9  Capricorn
    "Saturn",  # 10 Aquarius
    "Jupiter", # 11 Pisces
]

_PLANETS: list[str] = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

_SWE_IDS: dict[str, int] = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
    "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS, "Saturn": swe.SATURN,
}

# BPHS 27.1: debilitation absolute longitude (0° = start of Aries, range 0–360°).
_DEBILITATION_LON: dict[str, float] = {
    "Sun":     190.0,  # 10° Libra
    "Moon":    213.0,  # 3°  Scorpio
    "Mars":    118.0,  # 28° Cancer
    "Mercury": 345.0,  # 15° Pisces
    "Jupiter": 275.0,  # 5°  Capricorn
    "Venus":   177.0,  # 27° Virgo
    "Saturn":   20.0,  # 20° Aries
}

_CANONICAL_SIGNS: tuple = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

# Panchadha Maitri → Saptavargaja Virupa scores (BPHS 27.2-4 literal).
SAPTAVARGAJA_SCORE: dict[str, float] = {
    "Adhimitra": 20.0,   # Pramudita Rasi (BPHS 27.2-4)
    "Mitra":     15.0,   # Shanta Rasi
    "Sama":      10.0,   # Din Rasi
    "Satru":      4.0,   # Duhkhita Rasi
    "Adhisatru":  2.0,   # Khala Rasi
}
# Own sign (Svastha) = 30, Mooltrikona (D1 only) = 45 — handled in
# scoring branch logic, not this dict.

# Moolatrikona sign index and degree range per _dignity_tables.MOOLATRIKONA.
_MT_SIGN_IDX: dict[str, int]    = {p: _SIGN_TO_IDX[MOOLATRIKONA[p][0]] for p in _PLANETS}
_MT_LOW:      dict[str, float]  = {p: MOOLATRIKONA[p][1]                for p in _PLANETS}
_MT_HIGH:     dict[str, float]  = {p: MOOLATRIKONA[p][2]                for p in _PLANETS}

# Female planets score for even signs; all others (male + neutral) for odd signs.
_FEMALE_PLANETS: frozenset = frozenset({"Moon", "Venus"})


# ── Varga sign calculators ───────────────────────────────────────────────────
# TODO: extract to calculations/vargas/ once a second consumer module exists.

def _compute_hora_sign(lon: float) -> int:
    """D2 sign index.
    Sun's hora (Cancer, sign 3): 0–15° of odd signs and 15–30° of even signs.
    Moon's hora (Leo, sign 4): 15–30° of odd signs and 0–15° of even signs.
    Returns 3 (Cancer) or 4 (Leo).
    """
    sign = int(lon / 30.0) % 12
    deg  = lon % 30.0
    if sign % 2 == 0:        # odd zodiac sign (Aries, Gemini, Leo …)
        return 3 if deg < 15.0 else 4
    else:                     # even zodiac sign (Taurus, Cancer, Virgo …)
        return 4 if deg < 15.0 else 3


def _compute_drekkana_sign(lon: float) -> int:
    """D3 sign index.  0–10° → same sign; 10–20° → sign+4; 20–30° → sign+8 (mod 12)."""
    sign = int(lon / 30.0) % 12
    deg  = lon % 30.0
    if deg < 10.0:
        return sign
    elif deg < 20.0:
        return (sign + 4) % 12
    else:
        return (sign + 8) % 12


def _compute_saptamsha_sign(lon: float) -> int:
    """D7 sign index.
    Odd signs: seven 30/7° spans start from the same sign.
    Even signs: seven spans start from the 7th sign (sign+6).
    """
    sign = int(lon / 30.0) % 12
    deg  = lon % 30.0
    span = min(int(deg / (30.0 / 7.0)), 6)  # defensive clamp to [0,6]
    if sign % 2 == 0:   # odd zodiac sign
        return (sign + span) % 12
    else:                # even zodiac sign
        return (sign + 6 + span) % 12


def _compute_dwadashamsha_sign(lon: float) -> int:
    """D12 sign index.  12 × 2.5° parts starting from the same sign."""
    sign = int(lon / 30.0) % 12
    deg  = lon % 30.0
    span = min(int(deg / 2.5), 11)
    return (sign + span) % 12


def _compute_trimshamsha_sign(lon: float) -> int:
    """D30 sign index (Trimshamsha).
    Odd signs:  Aries(0) 0–5°, Aquarius(10) 5–10°, Sagittarius(8) 10–18°,
                Gemini(2) 18–25°, Libra(6) 25–30°.
    Even signs: Taurus(1) 0–5°, Virgo(5) 5–12°, Pisces(11) 12–20°,
                Capricorn(9) 20–25°, Scorpio(7) 25–30°.
    Returns the primary own-sign of the span ruler
    (Mars→Aries for odd spans, Mars→Scorpio for even spans).
    """
    sign = int(lon / 30.0) % 12
    deg  = lon % 30.0
    if sign % 2 == 0:        # odd zodiac sign
        if   deg <  5.0: return  0   # Aries      (Mars)
        elif deg < 10.0: return 10   # Aquarius   (Saturn)
        elif deg < 18.0: return  8   # Sagittarius (Jupiter)
        elif deg < 25.0: return  2   # Gemini     (Mercury)
        else:            return  6   # Libra      (Venus)
    else:                     # even zodiac sign
        if   deg <  5.0: return  1   # Taurus     (Venus)
        elif deg < 12.0: return  5   # Virgo      (Mercury)
        elif deg < 20.0: return 11   # Pisces     (Jupiter)
        elif deg < 25.0: return  9   # Capricorn  (Saturn)
        else:            return  7   # Scorpio    (Mars)


# ── Friendship helpers ───────────────────────────────────────────────────────

def _natural_relation(planet: str, other: str) -> str:
    return natural_friendship(planet, other).lower()


def _varga_score(
    planet: str,
    varga_sign: int,
    planet_d1_sign: str,
    all_lons: dict,
    is_d1: bool = False,
    lon: float = 0.0,
) -> float:
    """Score one varga placement for Saptavargaja Bala (Panchadha Maitri).

    Priority (D1 only): Moolatrikona (45) > Own sign (30) > Compound friendship.
    Other vargas:       Own sign (30) > Compound friendship.
    """
    if is_d1:
        deg = lon % 30.0
        if (varga_sign == _MT_SIGN_IDX[planet]
                and _MT_LOW[planet] <= deg < _MT_HIGH[planet]):
            return 45.0

    lord = _SIGN_LORDS[varga_sign]
    if lord == planet:
        return 30.0

    lord_d1_sign = _CANONICAL_SIGNS[int(all_lons[lord] / 30.0) % 12]
    compound = pancha_dha_maitri(planet, planet_d1_sign, lord, lord_d1_sign)
    return SAPTAVARGAJA_SCORE[compound]


# ── Sub-components ───────────────────────────────────────────────────────────

def _ochcha_bala(planet: str, lon: float) -> float:
    """BPHS 27.1: arc from debilitation point (min-arc ≤ 180°) ÷ 3."""
    arc = abs(lon - _DEBILITATION_LON[planet])
    if arc > 180.0:
        arc = 360.0 - arc
    return arc / 3.0


def _saptavargaja_bala(
    planet: str,
    lon: float,
    all_lons: dict[str, float],
    d9_sign_idx: int,
) -> float:
    """Saptavargaja Bala: Panchadha Maitri summed over D1/D2/D3/D7/D9/D12/D30."""
    d1_sign = int(lon / 30.0) % 12
    planet_d1_sign = _CANONICAL_SIGNS[d1_sign]

    return (
        _varga_score(planet, d1_sign,                           planet_d1_sign, all_lons, is_d1=True, lon=lon)
        + _varga_score(planet, _compute_hora_sign(lon),         planet_d1_sign, all_lons)
        + _varga_score(planet, _compute_drekkana_sign(lon),     planet_d1_sign, all_lons)
        + _varga_score(planet, _compute_saptamsha_sign(lon),    planet_d1_sign, all_lons)
        + _varga_score(planet, d9_sign_idx,                     planet_d1_sign, all_lons)
        + _varga_score(planet, _compute_dwadashamsha_sign(lon), planet_d1_sign, all_lons)
        + _varga_score(planet, _compute_trimshamsha_sign(lon),  planet_d1_sign, all_lons)
    )


def _ojayugma_bala(planet: str, d1_sign: int, d9_sign: int) -> float:
    """Ojayugmarasyamsa Bala.
    Female planets (Moon, Venus): +15 per even sign (idx%2==1) in D1 and D9.
    All others (male: Sun/Mars/Jupiter; neutral: Mercury/Saturn): +15 per odd sign (idx%2==0).
    Max 30 Virupa.
    """
    if planet in _FEMALE_PLANETS:
        return (15.0 if d1_sign % 2 == 1 else 0.0) + (15.0 if d9_sign % 2 == 1 else 0.0)
    return (15.0 if d1_sign % 2 == 0 else 0.0) + (15.0 if d9_sign % 2 == 0 else 0.0)


def _kendra_bala(house: int) -> float:
    """Angular (1,4,7,10) → 60; Succedent (2,5,8,11) → 30; Cadent (3,6,9,12) → 15."""
    if house in {1, 4, 7, 10}:
        return 60.0
    if house in {2, 5, 8, 11}:
        return 30.0
    return 15.0


# ── Public API ───────────────────────────────────────────────────────────────

def compute_sthana_bala(chart_data: dict) -> dict:
    """Compute Sthana Bala (positional strength) for all 7 classical planets.

    Args:
        chart_data: output of calculate_chart(). Required keys:
            ["meta"]["jd_ut"], ["meta"]["asc_lon_sidereal"],
            ["planetary_positions"][planet]["house"] for each of the 7 grahas.
            Planet longitudes are re-derived from pyswisseph (not in chart_data).

    Returns:
        Dict keyed by lowercase planet name ("sun" … "saturn"). Each value is a
        dict: ochcha, saptavargaja, ojayugma, kendra, drekkana, sthan_total
        (all floats, Virupa).

    Raises:
        ValueError: required key absent in chart_data.
        RuntimeError: (as ephemeris.EphemerisError, a RuntimeError
            subclass) a pyswisseph ephemeris calculation failed.
    """
    try:
        jd_ut: float = chart_data["meta"]["jd_ut"]
        asc_lon: float = chart_data["meta"]["asc_lon_sidereal"]
    except KeyError as exc:
        raise ValueError(
            f"compute_sthana_bala: missing key in chart_data['meta']: {exc}"
        ) from exc

    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # chart_data["planetary_positions"] carries sign/house/dignity but not
    # longitude. Re-derive precise sidereal longitudes from the ephemeris.
    # Session 52 migration: delegates to helpers/ephemeris.py's
    # sidereal_longitude(); calc_ut failures now surface as
    # ephemeris.EphemerisError (a RuntimeError subclass) naming the planet
    # id and jd_ut, rather than this module's own RuntimeError wording.
    planet_lons: dict[str, float] = {}
    for planet, pid in _SWE_IDS.items():
        planet_lons[planet] = ephemeris.sidereal_longitude(jd_ut, pid)

    # Single navamsa call provides D9 signs for Saptavargaja and Ojayugma.
    navamsa_chart = compute_navamsa(jd_ut, asc_lon)
    d9_signs: dict[str, int] = {
        p: _SIGN_TO_IDX[navamsa_chart.placements[p].d9_sign]
        for p in _PLANETS
    }

    result: dict[str, dict] = {}
    for planet in _PLANETS:
        try:
            house: int = chart_data["planetary_positions"][planet]["house"]
        except KeyError as exc:
            raise ValueError(
                f"compute_sthana_bala: missing "
                f"planetary_positions['{planet}']['house']: {exc}"
            ) from exc

        lon      = planet_lons[planet]
        d1_sign  = int(lon / 30.0) % 12
        d9_sign  = d9_signs[planet]

        ochcha       = _ochcha_bala(planet, lon)
        saptavargaja = _saptavargaja_bala(planet, lon, planet_lons, d9_sign)
        ojayugma     = _ojayugma_bala(planet, d1_sign, d9_sign)
        kendra       = _kendra_bala(house)
        drekkana     = 1.0
        sthan_total  = ochcha + saptavargaja + ojayugma + kendra + drekkana

        result[planet.lower()] = {
            "ochcha":       round(ochcha, 4),
            "saptavargaja": round(saptavargaja, 4),
            "ojayugma":     round(ojayugma, 4),
            "kendra":       kendra,
            "drekkana":     drekkana,
            "sthan_total":  round(sthan_total, 4),
        }

    return result
