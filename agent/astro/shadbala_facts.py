"""Astro Agent -- SHADBALA FACTS composer (Path B).

Composes the already-validated Shadbala totals into a compact fact-block
entry, exactly like yoga_facts / transit_facts: the CALLER attaches the result
onto chart_facts["shadbala"] after calculate_chart(), and pipeline._fact_block
renders it. `chart_facts` stays a pure restatement; this module owns the
reshape.

RESTATE, NEVER RECOMPUTE (S124). All six balas are computed and oracle-
validated in agent/calculations/strength/ (shadbala_totals aggregates them,
Drik Bala 28/28 vs JHora v8). This module only reshapes that output.

Shadbala is a declared `unfittable` concept (agent/astro/predicates.py): it
carries NO verification predicate and NO capability-gate Requirement. It is
additive strength context, so the silence gate types any claim resting on it
as `unfittable` and ships it hedged.

FAIL-SOFT. Any failure costs the strength block, never the answer: returns {}
and never raises. Same posture as the D9 / yoga / transit wiring.

Python 3.11.
"""
from __future__ import annotations

import logging

from agent.calculations.strength.shadbala_totals import compute_shadbala_totals

logger = logging.getLogger(__name__)

__all__ = ["build_shadbala_facts"]

# compute_shadbala_totals returns lowercase graha keys; the fact block uses
# Title-case to match every other composed fact. Shadbala is defined for the
# seven physical grahas only (BPHS) -- no Rahu/Ketu.
_TITLE = {
    "sun": "Sun", "moon": "Moon", "mars": "Mars", "mercury": "Mercury",
    "jupiter": "Jupiter", "venus": "Venus", "saturn": "Saturn",
}


def build_shadbala_facts(chart: dict) -> dict:
    """Reshape compute_shadbala_totals() output into a compact fact-block entry.

    Args:
        chart: output of calculate_chart(). Read-only; not mutated.

    Returns:
        {"planets": {<Title>: {"rupa": float, "ratio": float, "rank": int,
                               "meets_minimum": bool}},
         "strongest": <Title, rank 1>, "weakest": <Title, rank 7>,
         "caveat": <str>}
        or {} on any failure (fail-soft).
    """
    try:
        totals = compute_shadbala_totals(chart)
        if not isinstance(totals, dict) or not totals:
            return {}

        planets: dict[str, dict] = {}
        caveat = ""
        for low, row in totals.items():
            name = _TITLE.get(low, str(low).capitalize())
            ratio = row["ratio"]
            planets[name] = {
                "rupa": row["shadbala_rupa"],
                "ratio": ratio,
                # ratio >= 1.0 == meets the BPHS minimum (_MIN_REQUIRED in
                # shadbala_totals). The ONLY sourced cut -- no invented bands.
                "meets_minimum": ratio >= 1.0,
                "rank": row["rank"],
            }
            caveat = caveat or row.get("caveat", "")

        # Shadbala is defined for exactly 7 grahas; a different count means a
        # malformed result -- drop the block rather than ship a partial one.
        if len(planets) != 7:
            return {}

        by_rank = sorted(planets.items(), key=lambda kv: kv[1]["rank"])
        return {
            "planets": planets,
            "strongest": by_rank[0][0],
            "weakest": by_rank[-1][0],
            "caveat": caveat,
        }
    except Exception as exc:  # fail-soft: strength block is optional context
        logger.warning("build_shadbala_facts failed; omitting shadbala: %s", exc)
        return {}
