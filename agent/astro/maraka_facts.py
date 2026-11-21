"""Maraka (longevity / death-inflicting) facts -- RESTATE layer (S165).

Identifies the classical maraka planets from the house-lord map, and flags the
Vimshottari dasa/antardasa windows ruled by them as periods of ELEVATED
longevity/health risk. Reads only what chart_facts already built; computes no
chart fact (P-022, same discipline as narayana_facts / transit_facts).

CLASSICAL BASIS (Phaladeepika; BPHS Ch.43-44):
  * The 2nd and 7th are the maraka ("death-inflicting") houses -- they are the
    12th from the 3rd and 8th longevity houses -- so their LORDS are the maraka
    planets.
  * The 8th lord (randhra / longevity) and Saturn (Ayushkaraka, the natural
    significator of lifespan) are supporting factors.
  * Mortality/health risk is TIMED to the dasa/antardasa of these planets.

This is a RISK-WINDOW layer, NEVER a death date. Parasara (BPHS 43.2) calls
longevity "difficult even for the Gods" and (44.12) bars the judgement before
age 20; the layer carries that caveat so the interpreter frames risk-and-
resilience, never a forecast.

FAIL-SOFT: missing house-lords or dasha tree -> {} (costs maraka, not the answer).
Python 3.11.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

__all__ = ["build_maraka_facts"]

# 2nd & 7th = maraka houses; 8th = longevity (randhra); Saturn = Ayushkaraka.
_MARAKA_HOUSE_ROLES = {
    2: "2nd lord (maraka)",
    7: "7th lord (maraka)",
    8: "8th lord (longevity / randhra)",
}
_AYUSHKARAKA = "Saturn"


def _lord_of(house_lords: dict, house: int) -> str | None:
    row = house_lords.get(house) or house_lords.get(str(house)) or {}
    lord = row.get("lord") if isinstance(row, dict) else None
    return lord.strip() if isinstance(lord, str) and lord.strip() else None


def build_maraka_facts(chart_facts: dict) -> dict:
    """Maraka planets + their dasa/antardasa risk windows, from chart_facts.

    Args:
        chart_facts: build_chart_facts() output -- reads ``house_lords``
            ({house: {"lord": planet, ...}}) and ``dasha_periods``
            ({"mahadasha_tree": [{"mahadasha": {lord,start,end},
            "antardashas": [...], "phase"?}]}).

    Returns:
        {} on any missing input or failure (fail-soft). Otherwise:
        {"maraka_planets": {planet: [roles]}, "risk_windows": [...],
         "caveat": str}. Never raises.
    """
    try:
        house_lords = (chart_facts or {}).get("house_lords") or {}
        dasha = (chart_facts or {}).get("dasha_periods") or {}
        tree = dasha.get("mahadasha_tree") or []
        if not house_lords or not tree:
            return {}

        # planet -> the maraka/longevity roles it carries in THIS chart
        roles: dict[str, list[str]] = {}
        for house, label in _MARAKA_HOUSE_ROLES.items():
            lord = _lord_of(house_lords, house)
            if lord:
                roles.setdefault(lord, []).append(label)
        roles.setdefault(_AYUSHKARAKA, []).append("Ayushkaraka (lifespan significator)")

        # flag every dasa/antardasa window ruled by one of those planets
        windows: list[dict] = []
        for node in tree:
            md = node.get("mahadasha") or {}
            md_lord = md.get("lord")
            md_phase = node.get("phase")
            if md_lord in roles:
                windows.append({
                    "level": "mahadasha", "lord": md_lord, "roles": roles[md_lord],
                    "start": md.get("start"), "end": md.get("end"), "phase": md_phase,
                })
            for ad in node.get("antardashas") or []:
                ad_lord = ad.get("lord")
                if ad_lord in roles:
                    windows.append({
                        "level": "antardasha", "lord": ad_lord, "roles": roles[ad_lord],
                        "under_mahadasha": md_lord, "start": ad.get("start"),
                        "end": ad.get("end"), "phase": md_phase,
                    })

        return {
            "maraka_planets": {p: roles[p] for p in roles},
            "risk_windows": windows,
            "caveat": (
                "Longevity is the most uncertain judgement in the classical corpus "
                "(BPHS 43.2: 'difficult even for the Gods'; 44.12 bars the judgement "
                "before age 20). These are periods of ELEVATED RISK under the maraka "
                "framework -- NOT a death date and NOT a certainty; present them as "
                "risk-and-resilience, cross-checked with the Mrityu/Apamrityu sahams "
                "and overall chart strength."
            ),
        }
    except Exception as exc:  # noqa: BLE001 -- maraka costs only itself
        logger.warning("build_maraka_facts failed; omitting maraka: %s", exc)
        return {}
