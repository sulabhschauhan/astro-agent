"""
agent/astro/kp_facts.py
KP (Krishnamurti Paddhati) fact composer -- 7th-cusp sub-lord (S143).

Restates agent.calculations.kp.sub_lords into a new fact class for the
interpreter, same posture as yoga_facts.py (S133) and transit_facts.py
(S142): chart_facts stays a pure restatement of the calculator, and this
module owns the KP-specific reading (a DIFFERENT ayanamsha -- see
chart_calculator.py's S143 comment at the ayanamsha_kp block) chart_facts.py's
own law forbids it from computing internally.

WHY. S141/S142 established that marriage-timing SELECTION accuracy is gated
on cross-system corroboration, not calculation: correct dasha math alone
picked the wrong window (the Venus-karaka false positive), and Sade Sati /
Saturn transit was fed as the first corroborating input (S142). KP's 7th-
cusp sub-lord is the second: in KP practice, a house's own sub-lord decides
whether that house's matter is granted (Krishnamurti's "sub lord theory") --
the 7th cusp's sub-lord is read as marriage's own significator condition,
the same role Sade Sati plays for Saturn's transit corroboration.

WHAT IS COMPUTED, AND HOW CHEAPLY. chart['meta']['house_cusps_kp_sidereal']
(12 floats, already computed by chart_calculator.calculate_chart() under
swe.SIDM_KRISHNAMURTI) is looked up via
agent.calculations.kp.sub_lords.sub_lord_for_longitude(). Pure table lookup,
no ephemeris call -- this module is essentially free given the cusps already
exist. SCOPE (S153): ALL 12 cusp sub-lords are now composed -- each house's
own cusp sub-lord governs that house's matter in KP, the same doctrine the 7th
cusp uses for marriage. The 7th-cusp value is ALSO surfaced on its own key
(seventh_cusp_sub_lord), unchanged, because its marriage-corroboration framing
and its FACT_BLOCK_PROVIDES entry / renderer paragraph depend on it. All 12
share the one engine, already oracle-validated 47/48 across 4 charts x 12
cusps (S143, agent/calculations/kp/sub_lords.py) -- widening needs no new
validation.

VALIDATED (S143, offline, see agent/calculations/kp/sub_lords.py and
tests/calculations/kp/test_kp_oracle_validation.py): 46/48 exact match
against AstroSage's own KP cuspal tables across 4 reference charts, the 2
misses being documented geocoding-boundary artifacts, not table defects.

FAIL-SOFT. Any failure costs the KP fact, never the answer -- same posture
as yoga_facts.build_yoga_facts / transit_facts.build_transit_facts.

Python 3.11.
"""
from __future__ import annotations

from agent.calculations.kp.sub_lords import sub_lord_for_longitude


def build_kp_facts(chart: dict) -> dict:
    """The KP sub-lord of the 7th house's Placidus cusp.

    Args:
        chart: the dict from agent.chart_calculator.calculate_chart() --
            read for meta['house_cusps_kp_sidereal']. Read-only.

    Returns:
        {} if the input does not support it (no house_cusps_kp_sidereal, or
        not a 12-element list -- e.g. a pre-S143 chart dict). Otherwise:
        {"seventh_cusp_sub_lord": "Saturn",            # house 7, retained
         "cusp_sub_lords": {1: "Venus", ..., 12: "Mars"}}  # all 12 houses
        (planet names). Never raises.
    """
    try:
        meta = chart.get("meta") or {}
        cusps = meta.get("house_cusps_kp_sidereal")
        if not isinstance(cusps, (list, tuple)) or len(cusps) != 12:
            return {}
        # One lookup per cusp; index h-1 is house h's Placidus cusp.
        cusp_sub_lords = {h: sub_lord_for_longitude(cusps[h - 1]) for h in range(1, 13)}
        return {
            "seventh_cusp_sub_lord": cusp_sub_lords[7],  # unchanged key/semantics
            "cusp_sub_lords": cusp_sub_lords,
        }
    except Exception as e:  # noqa: BLE001 -- a bad chart costs the KP fact, not the answer
        return {"error": f"{type(e).__name__}: {e}"}
