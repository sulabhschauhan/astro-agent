"""Astro Agent -- JAIMINI FACTS composer (Path B).

Composes the already-validated Jaimini layer into a compact fact-block entry,
like yoga/transit/shadbala/ashtakavarga: the CALLER attaches the result onto
chart_facts["jaimini"] after calculate_chart(); pipeline._fact_block renders it.

Surfaces the two highest-value Jaimini facts for a natal reading:
  - the 8 chara karakas (PVR Ch.8 scheme, Rahu included), each the planet that
    signifies a life role (AK soul .. DK spouse), computed in
    agent/calculations/jaimini/karakas.py (JHora-validated, 4 charts, 8/8);
  - Arudha Lagna (AL, the image/perception of the self = arudha of house 1) and
    Upapada Lagna (UL, the marriage/spouse arudha = arudha of house 12), from
    agent/calculations/jaimini/arudha.py.

RESTATE, NEVER RECOMPUTE (S124): calls the validated calc functions; computes
no astrology of its own.

Karakas and arudhas carry NO verification predicate (Jaimini concepts --
`Karakamsa`/`Arudha` are named `unfittable` in predicates.py) -> the silence
gate ships a claim resting on them hedged. NO capability-gate Requirement.

FAIL-SOFT, PER PART: the karakas and the arudhas are computed in separate try
blocks, so a rare Arudha co-lord cascade failure (Scorpio/Aquarius house sign)
drops only the arudhas, never the karakas. Returns {} if nothing succeeds;
never raises.

Python 3.11.
"""
from __future__ import annotations

import logging

from agent.calculations.jaimini.karakas import compute_chara_karakas
from agent.calculations.jaimini.arudha import compute_arudha_pada

logger = logging.getLogger(__name__)

__all__ = ["build_jaimini_facts"]

_EIGHT = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu")
_NINE = _EIGHT + ("Ketu",)


def build_jaimini_facts(chart: dict) -> dict:
    """Reshape the Jaimini layer into a compact fact-block entry.

    Returns {"chara_karakas": {abbr: planet}, "arudha_lagna": sign,
    "upapada_lagna": sign} -- any subset that succeeds; {} if none do.
    """
    out: dict = {}
    try:
        pp = chart.get("planetary_positions") or {}
        hlm = chart.get("house_lord_mapping") or []
        house_sign = {r["house"]: r["sign"] for r in hlm if isinstance(r, dict)}

        try:
            lon8 = {p: pp[p]["longitude"] for p in _EIGHT}
            res = compute_chara_karakas(lon8)
            out["chara_karakas"] = {abbr: planet for abbr, planet in res.karakas}
        except Exception as exc:  # noqa: BLE001
            logger.warning("Jaimini chara karakas unavailable: %s", exc)

        try:
            lon9 = {p: pp[p]["longitude"] for p in _NINE}
            if 1 in house_sign:
                out["arudha_lagna"] = compute_arudha_pada(house_sign[1], lon9).arudha_sign
            if 12 in house_sign:
                out["upapada_lagna"] = compute_arudha_pada(house_sign[12], lon9).arudha_sign
        except Exception as exc:  # noqa: BLE001
            logger.warning("Jaimini arudhas unavailable: %s", exc)

        return out
    except Exception as exc:  # fail-soft outer guard
        logger.warning("build_jaimini_facts failed; omitting jaimini: %s", exc)
        return {}
