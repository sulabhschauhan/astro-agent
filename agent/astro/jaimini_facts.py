"""Astro Agent -- JAIMINI FACTS composer (Path B).

Composes the already-validated Jaimini layer into a compact fact-block entry,
like yoga/transit/shadbala/ashtakavarga: the CALLER attaches the result onto
chart_facts["jaimini"] after calculate_chart(); pipeline._fact_block renders it.

Surfaces the highest-value Jaimini facts for a natal reading:
  - the 8 chara karakas (PVR Ch.8 scheme, Rahu included), each the planet that
    signifies a life role (AK soul .. DK spouse), computed in
    agent/calculations/jaimini/karakas.py (JHora-validated, 4 charts, 8/8);
  - Arudha Lagna (AL, the image/perception of the self = arudha of house 1) and
    Upapada Lagna (UL, the marriage/spouse arudha = arudha of house 12), from
    agent/calculations/jaimini/arudha.py;
  - Karakamsa (PVR Ch.7 Sec.7.3.6: "the rasi occupied by atma karaka in
    [navamsa] is called Karakamsa"), the soul's reference sign in D9 -- a pure
    RESTATE joining the AK from the chara karakas above with that planet's D9
    sign from the navamsa chart static_facts already composes onto `chart`
    (agent/calculations/vargas/navamsa.py, AstroSage parity 4/4). "Swamsa" is
    deliberately NOT surfaced: PVR (and JHora) never use that term -- where it
    is classical it is a synonym for Karakamsa, and relabelling the navamsa
    lagna "Swamsa" would inject vocabulary the primary spec does not carry.

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
from agent.calculations.jaimini.padas import compute_bhava_padas

logger = logging.getLogger(__name__)

__all__ = ["build_jaimini_facts"]

_EIGHT = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu")
_NINE = _EIGHT + ("Ketu",)


def build_jaimini_facts(chart: dict) -> dict:
    """Reshape the Jaimini layer into a compact fact-block entry.

    Returns {"chara_karakas": {abbr: planet}, "arudha_lagna": sign,
    "upapada_lagna": sign, "karakamsa": {"atmakaraka": planet, "sign": sign},
    "bhava_padas": {1..12: arudha_sign}} -- any subset that succeeds; {} if
    none do. bhava_padas[1] == arudha_lagna and [12] == upapada_lagna by
    construction (same arudha kernel); both are kept for backward compat and
    so AL/UL survive even if the all-12 orchestration fails on a rare chart.
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

        # KARAKAMSA (PVR Ch.7 Sec.7.3.6): the navamsa sign occupied by the
        # Atmakaraka. Pure restate -- AK is the rank-0 chara karaka above; its
        # D9 sign is read from the navamsa static_facts composes onto `chart`
        # BEFORE this runs. SEPARATE fail-soft block: a chart with no navamsa
        # composed (e.g. a bare unit-test chart) costs only Karakamsa, never
        # the karakas or arudhas.
        try:
            ak = (out.get("chara_karakas") or {}).get("AK")
            nav = chart.get("navamsa") or {}
            ak_d9 = (nav.get("placements") or {}).get(ak, {}).get("sign") if ak else None
            if ak and ak_d9:
                out["karakamsa"] = {"atmakaraka": ak, "sign": ak_d9}
        except Exception as exc:  # noqa: BLE001
            logger.warning("Jaimini karakamsa unavailable: %s", exc)

        try:
            lon9 = {p: pp[p]["longitude"] for p in _NINE}
            if 1 in house_sign:
                out["arudha_lagna"] = compute_arudha_pada(house_sign[1], lon9).arudha_sign
            if 12 in house_sign:
                out["upapada_lagna"] = compute_arudha_pada(house_sign[12], lon9).arudha_sign
        except Exception as exc:  # noqa: BLE001
            logger.warning("Jaimini arudhas unavailable: %s", exc)

        # ALL 12 BHAVA ARUDHAS (PVR Ch.9 Sec.9.2): A1(=AL) .. A12(=UL), the
        # image/perception of each house's matters. Validated 12/12 against PVR
        # Example 29 (tests/calculations/test_jaimini_padas.py). SEPARATE block
        # from AL/UL above on purpose: compute_bhava_padas is all-or-nothing
        # (one house hitting the fail-closed D2 co-lord gap raises for the whole
        # set), so running it here -- never above -- keeps AL/UL robust even
        # when the full set drops on a rare chart.
        try:
            lon9 = {p: pp[p]["longitude"] for p in _NINE}
            asc_sign = house_sign.get(1)
            if asc_sign:
                bps = compute_bhava_padas(asc_sign, lon9)
                out["bhava_padas"] = {p.house_num: p.result.arudha_sign
                                      for p in bps.padas}
        except Exception as exc:  # noqa: BLE001 -- all-12 is additive; AL/UL already set
            logger.warning("Jaimini bhava padas (all-12) unavailable: %s", exc)

        return out
    except Exception as exc:  # fail-soft outer guard
        logger.warning("build_jaimini_facts failed; omitting jaimini: %s", exc)
        return {}
