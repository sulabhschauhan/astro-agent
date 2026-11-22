"""Protective / Arishta-bhanga facts -- the COUNTERBALANCE to the maraka layer
(S167 longevity build).

The maraka layer (maraka_facts) emits the death-inflicting side: which planets
are marakas, their strength, the risk windows. Longevity is NEVER read from that
side alone -- the S166 falsification ("0-36" from a single-factor method) is the
proof. Classical longevity doctrine (BPHS 43-44; the Arishta-bhanga / protective
yogas) weighs the PROTECTIVE side against it: the lifespan significator's
strength, the lagna and its lord (the body and its vitality), benefic aspects
that cancel arishta, and the strength of the longevity houses (3rd, 8th).

PARAMETERS ONLY (S166 locked decision). This emits structural flags + a read-
through of the REAL shadbala virupas. It computes NO chart fact (P-022) and
invents NO importance weight, NO composite "protection score" and NO verdict --
what the protections are WORTH is corpus doctrine, applied by the interpreter.

ENRICHMENT PASS: it needs shadbala, so static_facts calls it AFTER the shadbala
composer and attaches the result under the existing ``maraka`` key (one coherent
longevity block -- NO new FACT_BLOCK_PROVIDES entry).

FAIL-SOFT: any missing input -> {} (costs the protective block, not the answer).
Python 3.11.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

__all__ = ["build_protective_facts"]

_AYUSHKARAKA = "Saturn"
_NATURAL_BENEFICS = {"Jupiter", "Venus"}


def _lord_of(house_lords: dict, house: int) -> str | None:
    row = house_lords.get(house) or house_lords.get(str(house)) or {}
    lord = row.get("lord") if isinstance(row, dict) else None
    return lord.strip() if isinstance(lord, str) and lord.strip() else None


def _position(positions: dict, planet: str | None) -> dict:
    """house / sign / dignity restated for a planet; {} when unknown."""
    if not planet:
        return {}
    pos = positions.get(planet) or {}
    return {"house": pos.get("house"), "sign": pos.get("sign"),
            "dignity": pos.get("dignity")}


def _shadbala_of(shadbala_planets: dict, planet: str | None) -> dict | None:
    """Read-through of the REAL shadbala row; None for a graha with no shadbala
    (Rahu/Ketu) or a malformed source. Never invents a value."""
    row = shadbala_planets.get(planet) if planet else None
    if not isinstance(row, dict):
        return None
    return {"rupa": row.get("rupa"), "ratio": row.get("ratio"),
            "meets_minimum": row.get("meets_minimum"), "rank": row.get("rank")}


def _benefics_aspecting_house(aspects_by_planet: dict, house: int) -> list[str]:
    return sorted(b for b in _NATURAL_BENEFICS
                  if house in (aspects_by_planet.get(b) or []))


def _benefics_aspecting_planet(aspected_by: dict, planet: str | None) -> list[str]:
    if not planet:
        return []
    return sorted(_NATURAL_BENEFICS & set(aspected_by.get(planet) or []))


def build_protective_facts(facts: dict) -> dict:
    """Arishta-bhanga / protective PARAMETERS, read from the assembled facts.

    Reads ``house_lords``, ``planet_positions``, ``aspects`` and ``shadbala``
    (+ ``ascendant_sign``). Returns structural flags + real shadbala read-
    throughs, or {} on any missing input (fail-soft). Never raises.
    """
    try:
        house_lords = (facts or {}).get("house_lords") or {}
        if not house_lords:
            return {}
        positions = facts.get("planet_positions") or {}
        shadbala = ((facts.get("shadbala") or {}).get("planets")) or {}
        aspects = facts.get("aspects") or {}
        by_planet = aspects.get("aspects_by_planet") or {}
        aspected_by = aspects.get("aspected_by") or {}

        lagna_lord = _lord_of(house_lords, 1)
        third_lord = _lord_of(house_lords, 3)
        eighth_lord = _lord_of(house_lords, 8)

        return {
            # Ayushkaraka -- the natural significator of lifespan; a strong one
            # is the first protective factor (it sustains life).
            "ayushkaraka": {
                "planet": _AYUSHKARAKA,
                **_position(positions, _AYUSHKARAKA),
                "shadbala": _shadbala_of(shadbala, _AYUSHKARAKA),
            },
            # Lagna = the body; benefic aspects to it cancel arishta.
            "lagna": {
                "sign": facts.get("ascendant_sign"),
                "benefic_aspects": _benefics_aspecting_house(by_planet, 1),
            },
            # Lagna lord = vitality of the body; its strength + benefic aspects.
            "lagna_lord": {
                "planet": lagna_lord,
                **_position(positions, lagna_lord),
                "shadbala": _shadbala_of(shadbala, lagna_lord),
                "benefic_aspects": _benefics_aspecting_planet(aspected_by, lagna_lord),
            },
            # The longevity houses themselves (3rd, 8th) via their lords' strength.
            "third_lord": {
                "planet": third_lord,
                **_position(positions, third_lord),
                "shadbala": _shadbala_of(shadbala, third_lord),
            },
            "eighth_lord": {
                "planet": eighth_lord,
                **_position(positions, eighth_lord),
                "shadbala": _shadbala_of(shadbala, eighth_lord),
            },
        }
    except Exception as exc:  # noqa: BLE001 -- protective costs only itself
        logger.warning("build_protective_facts failed; omitting: %s", exc)
        return {}
