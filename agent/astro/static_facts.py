"""Static per-chart fact assembly (V1.5, S147).

ONE place that computes the full STATIC fact block for a chart: navamsa (D9)
composed into the chart, then build_chart_facts, then every fail-soft composer
(yogas, transits, KP 7th-cusp sub-lord, KP significators, shadbala, ashtakavarga,
jaimini, divisional). This sequence previously lived inline in frontend/app.py;
centralising it lets fact_store cache the result per chart, and lets the runtime
dispatcher later compose the same block.

STATIC = chart-fixed: every value depends only on the birth chart, so the whole
dict is cacheable. The DYNAMIC, date-ranged facts (muhurta, transit-at-date) are
NOT here -- they are parametrised by the question and computed at answer time.

Faithful to the app.py block it replaces: same composition ORDER, same fail-soft
posture (a failing composer costs its own fact class, never the answer), same
keys (so capability_gate.FACT_BLOCK_PROVIDES and pipeline._fact_block are
unchanged). Widening (combustion, varshaphal, the report's lucky/unlucky) lands
HERE, in one place, next.

Python 3.11.
"""
from __future__ import annotations

import logging

from agent.chart_calculator import _dignity as _sign_dignity
from agent.calculations.vargas.navamsa import compute_navamsa
from agent.astro.chart_facts import build_chart_facts
from agent.astro.yoga_facts import build_yoga_facts
from agent.astro.transit_facts import build_transit_facts
from agent.astro.kp_facts import build_kp_facts
from agent.astro.kp_significator_facts import build_kp_significator_facts
from agent.astro.shadbala_facts import build_shadbala_facts
from agent.astro.ashtakavarga_facts import build_ashtakavarga_facts
from agent.astro.jaimini_facts import build_jaimini_facts
from agent.astro.divisional_facts import build_divisional_facts
from agent.astro.lucky_facts import build_lucky_facts

logger = logging.getLogger(__name__)

__all__ = ["build_static_facts"]


def _compose(facts: dict, key: str, fn) -> None:
    """Run one fail-soft composer into facts[key]; a failure costs only that key."""
    try:
        facts[key] = fn()
    except Exception as exc:  # noqa: BLE001 -- optional fact class, never fatal
        logger.warning("%s unavailable: %s: %s", key, type(exc).__name__, exc)


def build_static_facts(chart: dict) -> dict:
    """Assemble the full static fact block for `chart` (calculate_chart output).

    Mirrors the composition frontend/app.py ran inline. Returns the chart_facts
    dict. Never raises: every optional fact class is guarded.
    """
    _chart = chart

    # NAVAMSA (D9) is composed INTO the chart before build_chart_facts, which
    # restates it; losing D9 costs the Neecha Bhanga check, not the answer.
    try:
        meta = _chart.get("meta") or {}
        d9 = compute_navamsa(meta["jd_ut"], meta["asc_lon_sidereal"])
        _chart = dict(_chart, navamsa={
            "d9_lagna_sign": d9.d9_lagna_sign,
            "placements": {
                p: {"sign": pl.d9_sign, "house": pl.d9_house,
                    "dignity": _sign_dignity(p, pl.d9_sign)}
                for p, pl in d9.placements.items()},
        })
    except Exception as exc:  # noqa: BLE001 -- optional fact class
        logger.warning("D9 unavailable: %s: %s", type(exc).__name__, exc)

    facts = build_chart_facts(_chart)

    # Same order + semantics as the app.py block. yogas/transits take the fact
    # block as a 2nd arg (they read what is composed so far); the rest take the
    # raw chart. Each is fail-soft.
    _compose(facts, "yogas", lambda: build_yoga_facts(_chart, facts))
    _compose(facts, "transits", lambda: build_transit_facts(_chart, facts))
    _compose(facts, "kp", lambda: build_kp_facts(_chart))
    _compose(facts, "kp_planet_significations",
             lambda: build_kp_significator_facts(_chart))
    _compose(facts, "shadbala", lambda: build_shadbala_facts(_chart))
    _compose(facts, "ashtakavarga", lambda: build_ashtakavarga_facts(_chart))
    _compose(facts, "jaimini", lambda: build_jaimini_facts(_chart))
    _compose(facts, "divisional", lambda: build_divisional_facts(_chart))
    # lucky_unlucky reads the ASSEMBLED facts (house_lords), like yogas/transits,
    # so it runs last over the composed block -- not over the raw chart.
    _compose(facts, "lucky_unlucky", lambda: build_lucky_facts(facts))
    return facts
