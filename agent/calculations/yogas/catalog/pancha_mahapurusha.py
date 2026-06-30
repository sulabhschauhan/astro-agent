"""Pancha Mahapurusha yogas — Ruchaka, Bhadra, Hamsa, Malavya, Sasa.

Source: BPHS Ch.75. Each yoga fires when its planet is BOTH in a kendra
house from Lagna (1, 4, 7, 10) AND in its own or exalted sign. Moolatrikona
counts as qualifying because MOOLATRIKONA degree ranges always fall inside the
planet's own-or-exaltation sign (per _dignity_tables.py) — it is not a
separate sign.

Combustion, affliction, and strength-grading are explicitly out of scope for
V1. This module detects yoga presence only.

SENSITIVE_TO: dignity.get_dignity_status — sign/degree validation delegates
there; changes to _dignity_tables.py affect which placements qualify.
"""

from __future__ import annotations

from dataclasses import dataclass

from agent.calculations.core.dignity import get_dignity_status

ELIGIBLE_PLANETS = ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")
KENDRA_HOUSES = (1, 4, 7, 10)

_QUALIFYING_DIGNITIES = frozenset({"Exalted", "Moolatrikona", "Own"})

_YOGA_NAMES: dict[str, str] = {
    "Mars":    "Ruchaka",
    "Mercury": "Bhadra",
    "Jupiter": "Hamsa",
    "Venus":   "Malavya",
    "Saturn":  "Shasha",
}


@dataclass(frozen=True)
class PlanetPlacement:
    planet: str
    sign: str
    degree_in_sign: float
    house_from_lagna: int


@dataclass(frozen=True)
class MahapurushaResult:
    yoga_name: str
    planet: str
    house_from_lagna: int
    sign: str
    dignity_status: str


def detect_pancha_mahapurusha(
    placements: list[PlanetPlacement],
) -> tuple[MahapurushaResult, ...]:
    """Detect all Pancha Mahapurusha Yogas present in the given placements.

    Returns 0-5 results (multiple yogas can coexist; no cap at 1). Only
    placements whose planet is in ELIGIBLE_PLANETS are evaluated; others are
    silently ignored.

    Raises:
        ValueError: if an eligible planet appears more than once in placements
            (duplicate/ambiguous input).
        ValueError: if get_dignity_status rejects a planet/sign/degree value
            (re-raised with the offending values named explicitly).
    """
    if not placements:
        return ()

    eligible = [p for p in placements if p.planet in ELIGIBLE_PLANETS]

    seen: set[str] = set()
    for p in eligible:
        if p.planet in seen:
            raise ValueError(
                f"Planet {p.planet!r} appears more than once in placements; "
                "input is ambiguous — deduplicate before calling."
            )
        seen.add(p.planet)

    results: list[MahapurushaResult] = []
    for p in eligible:
        if p.house_from_lagna not in KENDRA_HOUSES:
            continue

        try:
            dignity = get_dignity_status(p.planet, p.sign, p.degree_in_sign)
        except ValueError as exc:
            raise ValueError(
                f"get_dignity_status failed for planet={p.planet!r}, "
                f"sign={p.sign!r}, degree_in_sign={p.degree_in_sign!r}: {exc}"
            ) from exc

        if dignity in _QUALIFYING_DIGNITIES:
            results.append(
                MahapurushaResult(
                    yoga_name=_YOGA_NAMES[p.planet],
                    planet=p.planet,
                    house_from_lagna=p.house_from_lagna,
                    sign=p.sign,
                    dignity_status=dignity,
                )
            )

    return tuple(results)
