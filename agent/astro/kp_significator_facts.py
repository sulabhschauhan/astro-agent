"""
agent/astro/kp_significator_facts.py
KP house-significator fact composer (S144: now EPHEMERIS-COMPUTED).

WHY THIS EXISTS: S143's KP fact (7th cuspal sub-lord) is a single static
value, true for the whole chart -- it cannot discriminate between two
antardashas within the same mahadasha. This composer supplies the missing
period-varying signal: which houses each planet signifies, so "does the
ACTING antardasha lord signify a relevant house" becomes a fact the
interpreter reads per sub-period (tagged in pipeline._fact_block next to each
antardasha's lord, exactly like the Saturn-transit tag).

SOURCE CHANGED IN S144 (was parse_kp_significators, an AstroSage-PDF parse):
now agent.calculations.kp.significator_engine.compute_kp_significators, an
ephemeris computation from the chart's own primitives (KP Reader II fourfold +
Reader IV node agency). This severs the PDF dependency -- a served answer no
longer needs an AstroSage PDF present (PDF-AS-ORACLE-ONLY, S143). The PDF
parser (agent/calculations/kp/significators.py) is retained ONLY as the
offline oracle for tests, not called here.

SAME COMPOSER PATTERN as yoga_facts.py/transit_facts.py/kp_facts.py: called
by the CALLER (frontend/app.py, scripts/expert_pilot.py) with the computed
`chart` dict, attached onto chart_facts post-hoc, wrapped fail-soft.

OUTPUT SHAPE is UNCHANGED from the parser era, so pipeline._fact_block /
capability_gate / interpreter need no changes: {"planet_significations":
{planet: (house_ints, ascending)}}. The engine's per-house tier/via detail is
flattened away here (v1) -- a planet signifies a house or it doesn't; the
strength RANKING is a v2 interpreter upgrade, kept out of the fact block for
now to avoid touching downstream consumers.
"""
from __future__ import annotations

from agent.calculations.kp.significator_engine import compute_kp_significators


def build_kp_significator_facts(chart: dict | None) -> dict:
    """KP house significators for all 9 planets, ephemeris-computed.

    Args:
        chart: a calculate_chart() dict (needs planetary_positions +
            meta['house_cusps_kp_sidereal']). None -> {} (fail-soft).

    Returns:
        {"planet_significations": {"Mercury": (2, 3, 7, 10, 12), ...}} with
        houses ascending per planet, or {} if chart is None / malformed / any
        error (this fact being absent must never break an answer).
    """
    if not chart:
        return {}
    try:
        computed = compute_kp_significators(chart)["significators"]
        if not computed:
            return {}
        table = {
            planet: tuple(sorted(house_map))          # {house: {...}} -> (houses,)
            for planet, house_map in computed.items()
        }
        return {"planet_significations": table}
    except Exception as e:  # noqa: BLE001 -- fail-soft; a bad chart shape must not break the answer
        return {"error": f"{type(e).__name__}: {e}"}
