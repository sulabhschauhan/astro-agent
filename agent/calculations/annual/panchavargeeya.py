"""Pancha-vargeeya Bala (Tajika five-fold varga strength) per planet.

Pure function of sidereal longitudes; no ephemeris call.

MODEL (validated vs JHora, data/default_user/jhora_sulabh_varshaphal.md
"C1 method status"; source B.V. Raman, Varshaphala, sec 32-37):
  Each planet's relationship to the DIVISION LORD of its own longitude, using
  NATURAL (naisargika) friendship only, 3-tier: own = max, friend = max/2,
  neutral AND enemy = max/4 (Raman has only Mitra/Swa/Satru, no Sama tier).
    Kshetra (D1 sign lord)          30 / 15 / 7.5
    Hadda   (Egyptian-terms lord)   15 / 7.5 / 3.75
    Drekkana(D3 sign lord)          10 / 5  / 2.5
    Navamsa (D9 sign lord)           5 / 2.5 / 1.25
  Uchcha = circular distance from the deep-debilitation point / 9.
  total = sum of the five / 4.  Bands: >=15 Very Strong, 10-15 Powerful,
  5-10 Ordinary, <5 Weak.

KNOWN RESIDUAL (documented, not tuned): the Moon's NEUTRAL relationships score
higher in JHora than "inimical"; Moon (all years) and Mercury 2026 are
under-predicted. Compound friendship was tested and is worse.
"""

import swisseph as swe

from agent.calculations.core._friendship_tables import NATURAL_FRIENDSHIP
from agent.calculations.vargas.divisional import _SIGNS, varga_sign_index
from agent.calculations.vargas.navamsa import _d9_sign

PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

# Sign index 0..11 -> classical lord.
_SIGN_LORD = ("Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
              "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter")

_DEEP_EXALT = {"Sun": 10.0, "Moon": 33.0, "Mars": 298.0, "Mercury": 165.0,
               "Jupiter": 95.0, "Venus": 357.0, "Saturn": 200.0}

# Standard Egyptian terms: per sign, (lord, upper-bound degree) in order.
# Cross-checked against PyJHora const.hadda_lords (whose Aquarius tail "50" is
# a typo for 30).
_J, _V, _M, _R, _S = "Jupiter", "Venus", "Mercury", "Mars", "Saturn"
_HADDA = (
    ((_J, 6), (_V, 12), (_M, 20), (_R, 25), (_S, 30)),   # Aries
    ((_V, 8), (_M, 14), (_J, 22), (_S, 27), (_R, 30)),   # Taurus
    ((_M, 6), (_J, 12), (_V, 17), (_R, 24), (_S, 30)),   # Gemini
    ((_R, 7), (_V, 13), (_M, 19), (_J, 26), (_S, 30)),   # Cancer
    ((_J, 6), (_V, 11), (_S, 18), (_M, 24), (_R, 30)),   # Leo
    ((_M, 7), (_V, 17), (_J, 21), (_R, 28), (_S, 30)),   # Virgo
    ((_S, 6), (_M, 14), (_J, 21), (_V, 28), (_R, 30)),   # Libra
    ((_R, 7), (_V, 11), (_M, 19), (_J, 24), (_S, 30)),   # Scorpio
    ((_J, 12), (_V, 17), (_M, 21), (_R, 26), (_S, 30)),  # Sagittarius
    ((_M, 7), (_J, 14), (_V, 22), (_S, 26), (_R, 30)),   # Capricorn
    ((_M, 7), (_V, 13), (_J, 20), (_R, 25), (_S, 30)),   # Aquarius
    ((_V, 12), (_J, 16), (_M, 19), (_R, 28), (_S, 30)),  # Pisces
)

# (own, friend, inimical) per component maximum.
_COMPONENT_MAX = {"kshetra": 30.0, "hadda": 15.0, "drekkana": 10.0, "navamsa": 5.0}


def _hadda_lord(lon: float) -> str:
    in_sign = lon % 30.0
    for lord, upper in _HADDA[int(lon // 30) % 12]:
        if in_sign < upper:
            return lord
    return _HADDA[int(lon // 30) % 12][-1][0]


def _relation_points(planet: str, lord: str, maximum: float) -> float:
    if lord == planet:
        return maximum
    if lord in NATURAL_FRIENDSHIP[planet]["friends"]:
        return maximum / 2.0
    return maximum / 4.0  # neutral and enemy both inimical (Raman 3-tier)


def _band(total: float) -> str:
    if total >= 15.0:
        return "Very Strong"
    if total >= 10.0:
        return "Powerful"
    if total >= 5.0:
        return "Ordinary"
    return "Weak"


def compute_panchavargeeya(lons: dict) -> dict:
    """Return {planet: {kshetra, hadda, drekkana, navamsa, uchcha, total, band}}.

    lons: planet name -> sidereal longitude in [0, 360), for the 7 classical
    planets (extra keys such as Rahu/Ketu are ignored).

    Raises:
        ValueError: a classical planet is missing or a longitude is out of range.
    """
    missing = [p for p in PLANETS if p not in lons]
    if missing:
        raise ValueError(f"panchavargeeya: missing longitudes for {missing}")
    out = {}
    for p in PLANETS:
        lon = lons[p]
        if not (0.0 <= lon < 360.0):
            raise ValueError(f"panchavargeeya: {p} longitude out of [0,360): {lon}")
        lords = {
            "kshetra": _SIGN_LORD[int(lon // 30) % 12],
            "hadda": _hadda_lord(lon),
            "drekkana": _SIGN_LORD[varga_sign_index(lon, "D3")],
            "navamsa": _SIGN_LORD[_SIGNS.index(_d9_sign(lon)[0])],
        }
        comp = {k: _relation_points(p, lords[k], _COMPONENT_MAX[k]) for k in lords}
        deb = (_DEEP_EXALT[p] + 180.0) % 360.0
        d = abs(lon - deb)
        comp["uchcha"] = min(d, 360.0 - d) / 9.0
        total = sum(comp.values()) / 4.0
        out[p] = {**comp, "total": total, "band": _band(total), "lords": lords}
    return out


_SWE_ID_TO_NAME = {
    swe.SUN: "Sun", swe.MOON: "Moon", swe.MARS: "Mars", swe.MERCURY: "Mercury",
    swe.JUPITER: "Jupiter", swe.VENUS: "Venus", swe.SATURN: "Saturn",
}


def pancha_vargeeya_bala(annual_d1_sidereal_longitudes: dict) -> dict:
    """Swisseph planet id -> (vishwa_bala, classification) for the 7 planets.

    Thin id-keyed view over compute_panchavargeeya; extra ids (nodes) ignored.

    Raises:
        ValueError: a classical planet id is missing or a longitude is invalid.
    """
    try:
        by_name = {name: annual_d1_sidereal_longitudes[pid]
                   for pid, name in _SWE_ID_TO_NAME.items()}
    except KeyError as exc:
        raise ValueError(f"pancha_vargeeya_bala: missing planet id {exc}") from exc
    res = compute_panchavargeeya(by_name)
    return {pid: (res[name]["total"], res[name]["band"])
            for pid, name in _SWE_ID_TO_NAME.items()}
