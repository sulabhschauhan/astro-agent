"""Astro Agent -- ASHTAKAVARGA FACTS composer (Path B).

Composes the already-validated Ashtakavarga (BAV + SAV) into a compact
fact-block entry, like yoga/transit/shadbala: the CALLER attaches the result
onto chart_facts["ashtakavarga"] after calculate_chart(), pipeline._fact_block
renders it.

RESTATE, NEVER RECOMPUTE (S124). BAV/SAV are computed and oracle-validated in
agent/calculations/ashtakavarga (48/48 houses vs AstroSage, Session 54). This
module extracts placements, calls them, and maps SAV from signs to houses
(whole-sign: house<->sign is 1:1).

Bindu counts carry NO verification predicate (a numeric strength, like
shadbala) -> the silence gate types a claim resting on them as `unfittable`
and ships it hedged. NO capability-gate Requirement: additive house-strength
context.

FAIL-SOFT: never raises; returns {} on any failure.

Python 3.11.
"""
from __future__ import annotations

import logging

from agent.calculations.ashtakavarga.ashtakavarga import compute_bav, compute_sav

logger = logging.getLogger(__name__)

__all__ = ["build_ashtakavarga_facts"]

_SEVEN = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
_SAV_TOTAL = 337  # JHora convention: 7 planets, Lagna excluded


def build_ashtakavarga_facts(chart: dict) -> dict:
    """Reshape BAV/SAV into a compact per-house entry; {} on any failure."""
    try:
        pp = chart["planetary_positions"]
        hlm = chart["house_lord_mapping"]

        sign_to_house = {row["sign"]: row["house"] for row in hlm}  # whole-sign 1:1
        lagna_sign = next(row["sign"] for row in hlm if row["house"] == 1)

        placements = {p: pp[p]["sign"] for p in _SEVEN}
        placements["Lagna"] = lagna_sign

        bav = compute_bav(placements)
        sav = compute_sav(bav)  # {sign: bindus}

        sav_by_house = {sign_to_house[sign]: b for sign, b in sav.items()}
        if set(sav_by_house) != set(range(1, 13)):
            return {}
        if sum(sav_by_house.values()) != _SAV_TOTAL:
            return {}

        planet_bav_in_sign = {p: bav[p][pp[p]["sign"]] for p in _SEVEN}
        strongest = max(sav_by_house, key=lambda h: (sav_by_house[h], -h))
        weakest = min(sav_by_house, key=lambda h: (sav_by_house[h], h))

        return {
            "sav_by_house": sav_by_house,
            "strongest_house": strongest,
            "weakest_house": weakest,
            "planet_bav_in_sign": planet_bav_in_sign,
            "average_per_house": round(_SAV_TOTAL / 12.0, 2),
        }
    except Exception as exc:  # fail-soft
        logger.warning("build_ashtakavarga_facts failed; omitting ashtakavarga: %s", exc)
        return {}
