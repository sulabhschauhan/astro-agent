"""Astro Agent -- FRIENDSHIP FACTS composer (Path B, S152).

Composes the already-built, PVR-sourced friendship layer
(agent.calculations.core.friendship) into a compact fact-block entry, exactly
like jaimini/shadbala/divisional: the CALLER (static_facts.build_static_facts)
attaches the result onto chart_facts["friendship"]; pipeline._fact_block renders
it; the interpreter grounds its MEANING in the retrieved chapters.

WHAT IT SURFACES -- the five-fold compound relationship (Pancha-dha maitri, PVR
Section 3.4 / Table 8) of each of the 7 classical planets TOWARD every other,
combining natural (sthira) + temporary (tatkalika) friendship. Directional and
asymmetric by design: A's relation to B is a separate cell from B's to A.

NODES EXCLUDED BY DOCTRINE: natural friendship (PVR Table 7) and therefore
pancha-dha maitri are defined only for the 7 classical planets; Rahu/Ketu carry
no natural-friendship row. This matches all 4 AstroSage reference charts, whose
Friendship Table also stops at the 7 -- it is not a gap (core/friendship.py
raises on a node for exactly this reason).

RESTATE, NEVER RECOMPUTE (S124): reads each planet's SIGN from the chart and
calls the validated calc functions; computes no astrology of its own.

S130 CONTEXT: S130 restated only exalt/deb/own-sign dignity and deliberately
left the friendship tiers out, calling them "contested". S152 (ratified by
Sulabh) surfaces them: the engine is PVR-sourced and complete, AstroSage computes
them by the same Parashari method (so the Friendship Table is a direct oracle),
and the fact is labelled as computed Pancha-dha maitri so the interpreter grounds
it rather than asserting it. Carries NO verification predicate and NO capability-
gate Requirement -- additive context, same posture as jaimini/divisional.

FAIL-SOFT: a chart missing a planet's sign, or any bad input, costs the
friendship facts, never the answer -- returns {}. Never raises.

Python 3.11.
"""
from __future__ import annotations

import logging

from agent.calculations.core.friendship import pancha_dha_maitri

logger = logging.getLogger(__name__)

__all__ = ["build_friendship_facts", "SEVEN_CLASSICAL", "COMPOUND_ORDER"]

# The 7 classical planets, in the canonical order used across the fact block.
SEVEN_CLASSICAL = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

# PVR's five compound labels, strongest friend -> strongest enemy. The render
# reads this order so the output is deterministic and never model-ordered.
COMPOUND_ORDER = ("Adhimitra", "Mitra", "Sama", "Satru", "Adhisatru")


def build_friendship_facts(chart: dict) -> dict:
    """Pancha-dha maitri for the 7 classical planets, from their natal signs.

    Args:
        chart: calculate_chart() output. Reads planetary_positions[p]["sign"]
            for each of the 7 classical planets.

    Returns:
        {} if the required signs are not resolvable (fail-soft). Otherwise:
        {
          "signs":    {planet: sign},                 # the signs used
          "compound": {a: {b: label, ...}, ...},      # directional, a != b
          "by_planet":{a: {"Adhimitra":[...], "Mitra":[...], "Sama":[...],
                           "Satru":[...], "Adhisatru":[...]}},
        }
        label is one of COMPOUND_ORDER. Never raises.
    """
    try:
        pp = (chart or {}).get("planetary_positions") or {}
        signs: dict[str, str] = {}
        for p in SEVEN_CLASSICAL:
            sign = (pp.get(p) or {}).get("sign")
            if not sign:
                logger.warning("friendship: %s sign not resolvable; omitting", p)
                return {}
            signs[p] = sign

        compound: dict[str, dict[str, str]] = {}
        by_planet: dict[str, dict[str, list]] = {}
        for a in SEVEN_CLASSICAL:
            row: dict[str, str] = {}
            buckets: dict[str, list] = {lab: [] for lab in COMPOUND_ORDER}
            for b in SEVEN_CLASSICAL:
                if a == b:
                    continue
                label = pancha_dha_maitri(a, signs[a], b, signs[b])
                row[b] = label
                buckets[label].append(b)
            compound[a] = row
            by_planet[a] = buckets
        return {"signs": signs, "compound": compound, "by_planet": by_planet}
    except Exception as exc:  # noqa: BLE001 -- a bad input costs friendship, not the answer
        logger.warning("build_friendship_facts failed; omitting friendship: %s", exc)
        return {}
