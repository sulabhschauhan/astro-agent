"""Panchanga-limb suitability for Muhurta (electional) -- Tier A.

Completes the muhurta picture that transits/muhurta_scorer.py leaves out: the
three jd_ut-only panchanga limbs (tithi, nitya-yoga, karana) and their classical
auspiciousness for electional work. muhurta_scorer already votes Chandrabala +
Tarabala + Panchaka; this adds the "panchanga shuddhi" limbs.

STANDALONE BY DESIGN: it does NOT modify muhurta_scorer (whose favorable_count/
tier/warnings sequences are pinned by the S64 golden tests). Folding these limbs
into the muhurta composite is a small additive step for whenever muhurta gets a
live answer surface -- do it there so the goldens re-pin in the same change.

The limb COMPUTATION mirrors core/panchanga.py's formulas (identical spans) and
reuses its name arrays (the single source of spellings), but is jd_ut-only (no
location), matching muhurta_scorer's instant contract: tithi/yoga/karana depend
only on Sun/Moon longitudes, not on sunrise/location (unlike vara/choghadiya).

CLASSICAL SOURCES (fixed muhurta doctrine, not chart-specific):
  - 9 inauspicious nitya yogas (ashubha): Vishkambha, Atiganda, Shula, Ganda,
    Vyaghata, Vajra, Vyatipata, Parigha, Vaidhriti.
  - Karana: Vishti (Bhadra) is the strongly-avoided movable karana; the fixed
    Sakuni/Chatushpada/Naga are inauspicious for auspicious beginnings;
    Kintughna and the other movable karanas are suitable.
  - Rikta tithis (4th/9th/14th of either paksha) and Amavasya are avoided for
    auspicious beginnings.

Python 3.11.
"""
from __future__ import annotations

from dataclasses import dataclass

import swisseph as swe

from agent.calculations.helpers import ephemeris
from agent.calculations.core._panchanga_tables import (
    TITHI_NAMES, YOGA_NAMES, KARANA_SEQ,
)

# ── classical suitability tables (names, matching _panchanga_tables spellings) ──
INAUSPICIOUS_YOGAS = frozenset({
    "Vishkambha", "Atiganda", "Shula", "Ganda", "Vyaghata", "Vajra",
    "Vyatipata", "Parigha", "Vaidhriti",
})
_RIKTA_TITHIS = frozenset({
    "Sukla Chaturthi", "Krishna Chaturthi", "Sukla Navami", "Krishna Navami",
    "Sukla Chaturdashi", "Krishna Chaturdashi",
})
_FIXED_INAUSPICIOUS_KARANAS = frozenset({"Sakuni", "Chatushpada", "Naga"})


def tithi_suitability(name: str) -> str:
    """'avoid' for Rikta tithis (4/9/14) and Amavasya; else 'auspicious'."""
    if name == "Amavasya" or name in _RIKTA_TITHIS:
        return "avoid"
    return "auspicious"


def yoga_suitability(name: str) -> str:
    """'avoid' for the 9 ashubha nitya yogas; else 'auspicious'."""
    return "avoid" if name in INAUSPICIOUS_YOGAS else "auspicious"


def karana_suitability(name: str) -> str:
    """'avoid' for Vishti (Bhadra); 'caution' for Sakuni/Chatushpada/Naga; else
    'auspicious' (Kintughna and the movable karanas)."""
    if name == "Vishti":
        return "avoid"
    if name in _FIXED_INAUSPICIOUS_KARANAS:
        return "caution"
    return "auspicious"


@dataclass(frozen=True)
class PanchangaMuhurta:
    tithi: str
    yoga: str
    karana: str
    tithi_suitability: str
    yoga_suitability: str
    karana_suitability: str
    avoid_count: int                 # limbs classed 'avoid' (0-3)
    warnings: tuple[str, ...]        # one plain line per non-auspicious limb


def score_panchanga_muhurta(jd_ut: float) -> PanchangaMuhurta:
    """Tithi/nitya-yoga/karana at a jd_ut instant, with muhurta suitability.

    Pure function of jd_ut apart from the two ephemeris calls (Sun, Moon).
    Mirrors core/panchanga.py's span formulas; location-independent.

    Raises:
        ValueError: jd_ut <= 0.
        RuntimeError: a pyswisseph ephemeris calculation failed.
    """
    if jd_ut <= 0:
        raise ValueError(f"jd_ut must be > 0, got {jd_ut}")
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    sun = ephemeris.sidereal_position(jd_ut, swe.SUN).longitude
    moon = ephemeris.sidereal_position(jd_ut, swe.MOON).longitude

    elong = (moon - sun) % 360.0
    tithi = TITHI_NAMES[int(elong / 12.0)]                 # 0..29
    yoga = YOGA_NAMES[int(((moon + sun) % 360.0) / (360.0 / 27)) % 27]
    karana = KARANA_SEQ[int(elong / 6.0) % 60]

    ts = tithi_suitability(tithi)
    ys = yoga_suitability(yoga)
    ks = karana_suitability(karana)

    warnings = []
    if ts == "avoid":
        warnings.append(f"Tithi {tithi} is a Rikta/Amavasya tithi -- avoided for "
                        f"auspicious beginnings.")
    if ys == "avoid":
        warnings.append(f"Nitya yoga {yoga} is one of the 9 inauspicious yogas.")
    if ks == "avoid":
        warnings.append(f"Karana {karana} (Bhadra/Vishti) is strongly avoided for "
                        f"muhurta.")
    elif ks == "caution":
        warnings.append(f"Karana {karana} is a fixed karana unfavourable for "
                        f"auspicious beginnings.")

    avoid_count = sum(1 for s in (ts, ys, ks) if s == "avoid")
    return PanchangaMuhurta(
        tithi=tithi, yoga=yoga, karana=karana,
        tithi_suitability=ts, yoga_suitability=ys, karana_suitability=ks,
        avoid_count=avoid_count, warnings=tuple(warnings),
    )
