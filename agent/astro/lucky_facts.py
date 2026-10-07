"""Lucky / unlucky weekdays -- CALCULATED from the chart, never parsed (S147).

Classical functional-nature rule (BPHS): a planet that lords a TRIKONA (1/5/9 --
the fortune/dharma trines, lagna included) is a functional benefic; one that
lords a DUSTHANA (6/8/12) without any trikona is a functional malefic. Each
weekday has a fixed planetary lord, so the chart's OWN house lordships decide
which weekdays are favourable or to be avoided -- personalised, computed, no
external source and nothing use-case-specific.

TRIKONA LORDSHIP DOMINATES: a planet that lords both a trikona and a dusthana is
favourable (a trikona lord is auspicious even when it also owns a dusthana --
BPHS functional-nature doctrine). This is the choice that reproduces the
standard output: a Sagittarius lagna -> Jupiter(1) Thursday + Mars(5, also 12)
Tuesday favourable, Venus(6) Friday avoid.

v1 FIRST-ORDER rule. The fuller refinements (kendradhipati dosha for natural
benefics, maraka 2/7, and the chart's single most-afflicted "bad planet" as a
separate fact) are recorded enhancements, each to be validated across the 4
reference charts before it changes a verdict -- not bundled in here.

PURE over chart_facts['house_lords'] -- no ephemeris. Fail-soft: {} if the house
lordships are absent. Python 3.11.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

__all__ = ["build_lucky_facts", "WEEKDAY_LORD"]

# Fixed planetary rulership of the seven weekdays (classical, invariant).
WEEKDAY_LORD = (
    ("Sunday", "Sun"), ("Monday", "Moon"), ("Tuesday", "Mars"),
    ("Wednesday", "Mercury"), ("Thursday", "Jupiter"), ("Friday", "Venus"),
    ("Saturday", "Saturn"),
)
_TRIKONA = frozenset({1, 5, 9})      # lagna + fortune/dharma trines -> benefic lords
_DUSTHANA = frozenset({6, 8, 12})    # dusthanas -> malefic lords (unless also trikona)


def _houses_by_lord(house_lords: dict) -> dict:
    """{planet: sorted[houses it lords]} from chart_facts['house_lords'].

    house_lords keys may be int or str (both forms seen in the fact block), so
    look up each house both ways -- the same tolerance pipeline._fact_block uses.
    """
    out: dict = {}
    for h in range(1, 13):
        hl = house_lords.get(h) or house_lords.get(str(h))
        if hl and hl.get("lord"):
            out.setdefault(hl["lord"], []).append(h)
    return {p: sorted(hs) for p, hs in out.items()}


def _verdict(houses: list) -> str:
    is_trik = any(h in _TRIKONA for h in houses)
    is_dus = any(h in _DUSTHANA for h in houses)
    if is_trik:            # trikona lordship dominates (auspicious even if also dusthana)
        return "favourable"
    if is_dus:
        return "avoid"
    return "neutral"


def build_lucky_facts(chart_facts: dict) -> dict:
    """Per-weekday favourability from the chart's house lordships.

    Returns {} if house_lords is absent. Otherwise:
    {"weekdays": {day: {"lord","houses_ruled","verdict"}},
     "favourable_days": [...], "avoid_days": [...]}.
    Never raises.
    """
    try:
        house_lords = (chart_facts or {}).get("house_lords") or {}
        by_lord = _houses_by_lord(house_lords)
        if not by_lord:
            return {}
        weekdays: dict = {}
        favourable: list = []
        avoid: list = []
        for day, planet in WEEKDAY_LORD:
            houses = by_lord.get(planet, [])
            v = _verdict(houses)
            weekdays[day] = {"lord": planet, "houses_ruled": houses, "verdict": v}
            if v == "favourable":
                favourable.append(day)
            elif v == "avoid":
                avoid.append(day)
        return {"weekdays": weekdays,
                "favourable_days": favourable, "avoid_days": avoid}
    except Exception as exc:  # noqa: BLE001 -- additive fact class, never fatal
        logger.warning("lucky facts unavailable: %s: %s", type(exc).__name__, exc)
        return {}
