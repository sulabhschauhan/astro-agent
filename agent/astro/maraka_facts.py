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

__all__ = ["build_maraka_facts", "build_maraka_strength_facts"]

# 2nd & 7th = maraka houses; 8th = longevity (randhra); Saturn = Ayushkaraka.
_MARAKA_HOUSE_ROLES = {
    2: "2nd lord (maraka)",
    7: "7th lord (maraka)",
    8: "8th lord (longevity / randhra)",
}
_AYUSHKARAKA = "Saturn"

# Natural malefics -- the FIXED classical set only. Mercury (malefic by
# association) and the Moon (malefic when waning) are CONTEXTUAL and are
# deliberately NOT classified here: the corpus doctrine, applied by the
# interpreter, decides their valence (S167 -- no hardcoded per-planet rule).
_NATURAL_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
# Natural benefics used ONLY for the protective "benefic save" flag; Mercury/
# Moon excluded for the same contextual reason.
_NATURAL_BENEFICS = {"Jupiter", "Venus"}

# A window's role maps to a KIND -- the DEFINITIONAL distinction the engine
# already draws (2nd/7th = maraka houses; 8th = randhra; Saturn = Ayushkaraka),
# surfaced so the interpreter never conflates a death-inflicting (maraka) period
# with a transition/upheaval (randhra) one or the lifespan significator
# (S167 window-kind separation). This is NOT a health-vs-death classifier --
# it is the role label the calc already produces, normalised.
_ROLE_KIND = {
    "2nd lord (maraka)": "maraka",
    "7th lord (maraka)": "maraka",
    "8th lord (longevity / randhra)": "randhra",
    "Ayushkaraka (lifespan significator)": "ayushkaraka",
}


def _kinds_of(roles: list[str]) -> list[str]:
    """Normalise a planet's maraka/longevity roles to their definitional KINDs
    (maraka / randhra / ayushkaraka), deduped and ordered. A planet can carry
    more than one (Saturn = 2nd-lord maraka AND Ayushkaraka)."""
    kinds = {_ROLE_KIND[r] for r in roles if r in _ROLE_KIND}
    return [k for k in ("maraka", "randhra", "ayushkaraka") if k in kinds]


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
                    "kinds": _kinds_of(roles[md_lord]),
                    "start": md.get("start"), "end": md.get("end"), "phase": md_phase,
                })
            for ad in node.get("antardashas") or []:
                ad_lord = ad.get("lord")
                if ad_lord in roles:
                    windows.append({
                        "level": "antardasha", "lord": ad_lord, "roles": roles[ad_lord],
                        "kinds": _kinds_of(roles[ad_lord]),
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


def _planet_house(facts: dict, planet: str) -> int | None:
    pos = (facts.get("planet_positions") or {}).get(planet) or {}
    h = pos.get("house")
    return h if isinstance(h, int) else None


def _shadbala_of(shadbala_planets: dict, planet: str) -> dict | None:
    """Read-through of the REAL shadbala row; None for grahas with no shadbala
    (Rahu/Ketu) or a malformed source. Never invents a value."""
    row = shadbala_planets.get(planet)
    if not isinstance(row, dict):
        return None
    return {
        "rupa": row.get("rupa"),
        "ratio": row.get("ratio"),
        "meets_minimum": row.get("meets_minimum"),
        "rank": row.get("rank"),
    }


def build_maraka_strength_facts(facts: dict) -> dict:
    """Strength PARAMETERS for each maraka / longevity planet (S167 longevity build).

    ENRICHMENT PASS. Unlike build_maraka_facts (which runs inside build_chart_facts
    off house-lords + dasha alone), this needs shadbala, so it MUST be called from
    static_facts AFTER the shadbala composer has run -- `facts["shadbala"]` does not
    exist yet inside build_chart_facts. Reads only already-composed facts; computes
    no chart fact (P-022).

    Emits, per maraka planet build_maraka_facts already identified: structural flags
    (lord roles, natural_malefic, afflicts_2/7, benefic_save_present) + a read-
    through of the REAL shadbala virupas. There is NO invented importance weight, NO
    composite score and NO verdict here -- what a strong-or-weak maraka MEANS is
    corpus doctrine, applied by the interpreter (S166 locked decision: parameters
    from calcs, importance from corpus).

    Args:
        facts: the assembled static fact block AFTER shadbala -- reads
            ``maraka.maraka_planets``, ``shadbala.planets``, ``planet_positions``
            and ``aspects`` (aspects_by_planet / aspected_by).

    Returns:
        {planet: {params}} or {} on any missing input (fail-soft). Never raises.
    """
    try:
        maraka = (facts or {}).get("maraka") or {}
        planets = maraka.get("maraka_planets") or {}
        if not planets:
            return {}
        shadbala = ((facts.get("shadbala") or {}).get("planets")) or {}
        aspects = facts.get("aspects") or {}
        by_planet = aspects.get("aspects_by_planet") or {}   # {planet: [houses]}
        aspected_by = aspects.get("aspected_by") or {}       # {planet: [planets]}

        out: dict[str, dict] = {}
        for planet, roles in planets.items():
            own_house = _planet_house(facts, planet)
            aspect_houses = set(by_planet.get(planet) or [])
            aspectors = set(aspected_by.get(planet) or [])
            # A natural benefic SAVES the maraka when it aspects it, or shares its
            # house (conjunction = same house). Same-house avoids parsing the
            # free-form conjunction strings and uses the known positions shape.
            benefic_aspect = bool(_NATURAL_BENEFICS & aspectors)
            benefic_conj = own_house is not None and any(
                _planet_house(facts, b) == own_house for b in _NATURAL_BENEFICS
            )
            out[planet] = {
                "is_2nd_lord": any("2nd lord" in r for r in roles),
                "is_7th_lord": any("7th lord" in r for r in roles),
                "is_8th_lord": any("8th lord" in r for r in roles),
                "is_ayushkaraka": any("Ayushkaraka" in r for r in roles),
                "natural_malefic": planet in _NATURAL_MALEFICS,
                # REAL computed strength; None for Rahu/Ketu (no shadbala).
                "shadbala": _shadbala_of(shadbala, planet),
                # Does this planet ALSO afflict a maraka house -- occupy or aspect
                # the 2nd / 7th? (compounding the maraka role.)
                "afflicts_2": own_house == 2 or 2 in aspect_houses,
                "afflicts_7": own_house == 7 or 7 in aspect_houses,
                "benefic_save_present": benefic_aspect or benefic_conj,
            }
        return out
    except Exception as exc:  # noqa: BLE001 -- strength costs only itself
        logger.warning("build_maraka_strength_facts failed; omitting: %s", exc)
        return {}
