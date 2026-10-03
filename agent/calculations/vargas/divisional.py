"""Divisional charts (vargas) — the generic engine for D2..D60 EXCEPT D9.

D9 (Navamsa) is NOT re-implemented here: agent/calculations/vargas/navamsa.py
remains its oracle-clean authority (do not touch it). This module is the
generalization navamsa.py's own DESIGN NOTE calls for "at the P2.5 boundary,
once D10/D7/D12 converge" -- that boundary is now.

STRUCTURE (mirrors navamsa.py):
  - The DIVISION RULE for each varga is a pure function longitude -> sign
    index (0..11). Pure arithmetic, swisseph-free, unit-testable in isolation.
  - compute_varga() reuses navamsa's ephemeris pattern (helpers/ephemeris) to
    get sidereal longitudes, then applies the rule and derives whole-sign
    houses from the varga lagna.

VALIDATION: every rule below reproduces the AstroSage "Shodashvarga Table"
for the Sulabh reference chart, 10/10 bodies incl. the lagna, EXCEPT:
  - D7 (Saptamsa): across the 4 reference charts the textbook rule matched
    every AstroSage cell except 3 slow/retrograde planets sitting <0.6deg past
    a part boundary (Sulabh Saturn, Sheridan Mars, Sheridan Saturn), where the
    rule lands one part later than AstroSage's arcsecond-rounded longitude.
    Sulabh Saturn was adjudicated against JHora: JHora puts it in AQUARIUS =
    the rule, confirming AstroSage's Capricorn was the outlier (near-stationary
    Saturn, internal vs printed longitude). The two Sheridan cells are the same
    shape and very likely AstroSage outliers too (Sheridan JHora check pending).
    The rule was NOT tuned to AstroSage -- doing so would have broken it against
    JHora. (AstroSage also printed 0 for David's D7 Mars/Rahu -- invalid,
    excluded from validation.)

CITATIONS: PVR Narasimha Rao "Vedic Astrology" Ch.7; BPHS Ch.6-7. Division
conventions:
  D2 Hora: 2 x 15deg -- odd sign 1st half Leo / 2nd Cancer; even reversed.
  D3 Drekkana: 3 x 10deg from self, step 4 (self / 5th / 9th).
  D4: 4 x 7.5deg from self, step 3 (kendras: self / 4th / 7th / 10th).
  D7 Saptamsa: 7 parts -- odd from self, even from the 7th; step 1.
  D10 Dasamsa: 10 parts -- odd from self, even from the 9th; step 1.
  D12: 12 x 2.5deg from self; step 1.
  D16/D45: parts from the modality sign (movable Aries / fixed Leo / dual Sag).
  D20: movable Aries / fixed Sagittarius / dual Leo.
  D24: odd from Leo, even from Cancer.
  D27: by triplicity (fire Aries / earth Cancer / air Libra / water Capricorn).
  D30 Trimsamsa: 5 UNEQUAL parts (5/5/8/7/5), odd Mars-Sat-Jup-Mer-Ven ->
    Ari/Aqu/Sag/Gem/Lib; even reversed Ven-Mer-Jup-Sat-Mars -> Tau/Vir/Pis/Cap/Sco.
  D40: odd from Aries, even from Libra; step 1.
  D60: 60 x 0.5deg from self; step 1.

Python 3.11.
"""
from __future__ import annotations

from dataclasses import dataclass

import swisseph as swe

from agent.calculations.helpers import ephemeris

_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)
_SWE_IDS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN,
}
_MOVABLE = frozenset({0, 3, 6, 9})
_FIXED = frozenset({1, 4, 7, 10})
_FIRE = frozenset({0, 4, 8})
_EARTH = frozenset({1, 5, 9})
_AIR = frozenset({2, 6, 10})


def _rasi(lon: float) -> int:
    return int(lon / 30.0) % 12


def _part(lon: float, n: int) -> int:
    """0-based index of the equal n-part division the longitude falls in."""
    return min(int((lon % 30.0) / (30.0 / n)), n - 1)


# ---- per-varga division rules: longitude -> varga sign index (0..11) --------

def _d2(lon):            # Hora
    r = _rasi(lon); first = (lon % 30.0) < 15.0; odd = r % 2 == 0
    if odd:
        return 4 if first else 3
    return 3 if first else 4


def _d3(lon):  return (_rasi(lon) + 4 * _part(lon, 3)) % 12
def _d4(lon):  return (_rasi(lon) + 3 * _part(lon, 4)) % 12
def _d7(lon):
    r = _rasi(lon); start = r if r % 2 == 0 else (r + 6) % 12
    return (start + _part(lon, 7)) % 12
def _d10(lon):
    r = _rasi(lon); start = r if r % 2 == 0 else (r + 8) % 12
    return (start + _part(lon, 10)) % 12
def _d12(lon): return (_rasi(lon) + _part(lon, 12)) % 12
def _modal(r): return 0 if r in _MOVABLE else 4 if r in _FIXED else 8
def _d16(lon): return (_modal(_rasi(lon)) + _part(lon, 16)) % 12
def _d20(lon):
    r = _rasi(lon); start = 0 if r in _MOVABLE else 8 if r in _FIXED else 4
    return (start + _part(lon, 20)) % 12
def _d24(lon):
    r = _rasi(lon); start = 4 if r % 2 == 0 else 3
    return (start + _part(lon, 24)) % 12
def _d27(lon):
    # Bhamsa start by triplicity: fire->Aries(0), earth->Cancer(3),
    # air->Libra(6), water->Capricorn(9).
    r = _rasi(lon)
    start = 0 if r in _FIRE else 3 if r in _EARTH else 6 if r in _AIR else 9
    return (start + _part(lon, 27)) % 12
def _d30(lon):
    r = _rasi(lon); d = lon % 30.0; odd = r % 2 == 0
    if odd:
        return 0 if d < 5 else 10 if d < 10 else 8 if d < 18 else 2 if d < 25 else 6
    return 1 if d < 5 else 5 if d < 12 else 11 if d < 20 else 9 if d < 25 else 7
def _d40(lon):
    r = _rasi(lon); start = 0 if r % 2 == 0 else 6
    return (start + _part(lon, 40)) % 12
def _d45(lon): return (_modal(_rasi(lon)) + _part(lon, 45)) % 12
def _d60(lon): return (_rasi(lon) + _part(lon, 60)) % 12


# Registry. Keys are the standard varga codes. D9 intentionally absent.
VARGA_RULES = {
    "D2": _d2, "D3": _d3, "D4": _d4, "D7": _d7, "D10": _d10, "D12": _d12,
    "D16": _d16, "D20": _d20, "D24": _d24, "D27": _d27, "D30": _d30,
    "D40": _d40, "D45": _d45, "D60": _d60,
}
VARGA_NAMES = {
    "D2": "Hora", "D3": "Drekkana", "D4": "Chaturthamsa", "D7": "Saptamsa",
    "D10": "Dasamsa", "D12": "Dwadasamsa", "D16": "Shodasamsa",
    "D20": "Vimsamsa", "D24": "Chaturvimsamsa", "D27": "Bhamsa",
    "D30": "Trimsamsa", "D40": "Khavedamsa", "D45": "Akshavedamsa",
    "D60": "Shashtiamsa",
}


def varga_sign_index(longitude: float, varga: str) -> int:
    """Pure division rule: sidereal longitude [0,360) -> varga sign index 0..11.

    swisseph-free; the unit-testable core. Raises ValueError on an unknown
    varga or an out-of-range longitude.
    """
    if varga not in VARGA_RULES:
        raise ValueError(f"unknown varga {varga!r}; known: {sorted(VARGA_RULES)}")
    if not (0.0 <= longitude < 360.0):
        raise ValueError(f"longitude must be in [0, 360), got {longitude}")
    return VARGA_RULES[varga](longitude)


@dataclass(frozen=True)
class VargaPlacement:
    planet: str
    d1_sign: str
    d1_longitude: float
    varga_sign: str
    varga_house: int          # whole-sign from the varga lagna
    retrograde: bool


@dataclass(frozen=True)
class VargaChart:
    varga: str                # e.g. "D10"
    name: str                 # e.g. "Dasamsa"
    lagna_sign: str
    placements: dict          # planet -> VargaPlacement
    ayanamsa: float


def _calc_graha(jd_ut: float, pid: int) -> tuple[float, bool]:
    pos = ephemeris.sidereal_position(jd_ut, pid)
    return pos.longitude, pos.speed < 0


def compute_varga(jd_ut: float, asc_lon_sidereal: float, varga: str) -> VargaChart:
    """Compute one divisional chart for the 9 grahas + lagna.

    Pure function of (jd_ut, asc_lon_sidereal, varga) apart from the pyswisseph
    ephemeris calls -- same contract and validation posture as
    navamsa.compute_navamsa. D9 is not supported here (use compute_navamsa).

    Raises:
        ValueError: unknown/unsupported varga, jd_ut <= 0, or asc_lon_sidereal
            outside [0, 360).
        RuntimeError: a pyswisseph ephemeris calculation failed.
    """
    if varga not in VARGA_RULES:
        raise ValueError(f"unsupported varga {varga!r}; D9 uses navamsa.compute_navamsa")
    if jd_ut <= 0:
        raise ValueError(f"jd_ut must be > 0, got {jd_ut}")
    if not (0.0 <= asc_lon_sidereal < 360.0):
        raise ValueError(f"asc_lon_sidereal must be in [0, 360), got {asc_lon_sidereal}")

    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayanamsa = swe.get_ayanamsa_ut(jd_ut)

    longitudes: dict[str, float] = {}
    retro: dict[str, bool] = {}
    for planet, pid in _SWE_IDS.items():
        longitudes[planet], retro[planet] = _calc_graha(jd_ut, pid)
    rahu_lon, _ = _calc_graha(jd_ut, swe.MEAN_NODE)
    longitudes["Rahu"] = rahu_lon; retro["Rahu"] = True
    longitudes["Ketu"] = (rahu_lon + 180.0) % 360.0; retro["Ketu"] = True

    lagna_idx = varga_sign_index(asc_lon_sidereal, varga)
    lagna_sign = _SIGNS[lagna_idx]

    placements: dict[str, VargaPlacement] = {}
    for planet, lon in longitudes.items():
        v_idx = varga_sign_index(lon, varga)
        house = ((v_idx - lagna_idx) % 12) + 1
        placements[planet] = VargaPlacement(
            planet=planet,
            d1_sign=_SIGNS[_rasi(lon)],
            d1_longitude=lon,
            varga_sign=_SIGNS[v_idx],
            varga_house=house,
            retrograde=retro[planet],
        )
    return VargaChart(varga=varga, name=VARGA_NAMES[varga],
                      lagna_sign=lagna_sign, placements=placements, ayanamsa=ayanamsa)
