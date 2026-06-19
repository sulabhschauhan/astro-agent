"""Structural invariant tests for agent/calculations/core/_aspects_tables.py.

Structural-only: a regression guard against accidental edits to
ASPECTED_HOUSES_BY_PLANET, not a correctness oracle for the values
themselves. PVR worked-example correctness and aspects.py function
behavior belong in test_aspects.py, not here.

Independent of friendship.py, dignity.py, and any other production
module by design — reaches into _aspects_tables only, plus stdlib +
pytest.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # project root

import pytest

from agent.calculations.core._aspects_tables import ASPECTED_HOUSES_BY_PLANET

EXPECTED_PLANETS = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
)


# ── 1. Completeness: all 9 planets present ──────────────────────────────────

def test_has_exactly_nine_canonical_planets():
    assert set(ASPECTED_HOUSES_BY_PLANET.keys()) == set(EXPECTED_PLANETS), (
        f"ASPECTED_HOUSES_BY_PLANET: keys {sorted(ASPECTED_HOUSES_BY_PLANET.keys())} != "
        f"expected planet set {sorted(EXPECTED_PLANETS)}"
    )
    assert len(ASPECTED_HOUSES_BY_PLANET) == 9, (
        f"ASPECTED_HOUSES_BY_PLANET: expected 9 entries, got {len(ASPECTED_HOUSES_BY_PLANET)}"
    )


def test_rahu_and_ketu_are_present():
    assert "Rahu" in ASPECTED_HOUSES_BY_PLANET, (
        "Rahu missing from ASPECTED_HOUSES_BY_PLANET — this is the locked "
        "classical-conflict decision (nodes ARE aspect sources); scope must "
        "not silently narrow back to the 7 classical planets"
    )
    assert "Ketu" in ASPECTED_HOUSES_BY_PLANET, (
        "Ketu missing from ASPECTED_HOUSES_BY_PLANET — this is the locked "
        "classical-conflict decision (nodes ARE aspect sources); scope must "
        "not silently narrow back to the 7 classical planets"
    )


# ── 2. Value type and structure ─────────────────────────────────────────────

@pytest.mark.parametrize(
    "planet,aspect_tuple", list(ASPECTED_HOUSES_BY_PLANET.items()),
    ids=list(ASPECTED_HOUSES_BY_PLANET.keys()),
)
def test_value_is_a_nonempty_tuple_of_ints(planet, aspect_tuple):
    assert isinstance(aspect_tuple, tuple), (
        f"{planet}: expected tuple, got {type(aspect_tuple)}"
    )
    assert len(aspect_tuple) >= 1, (
        f"{planet}: expected at least one aspected house (the universal 7th), "
        f"got empty tuple"
    )
    for position in aspect_tuple:
        assert isinstance(position, int), (
            f"{planet}: position {position!r} is {type(position)}, expected int"
        )


# ── 3. House-number range ───────────────────────────────────────────────────

_ALL_PLANET_POSITION_PAIRS = [
    (planet, position)
    for planet, aspect_tuple in ASPECTED_HOUSES_BY_PLANET.items()
    for position in aspect_tuple
]


@pytest.mark.parametrize(
    "planet,position", _ALL_PLANET_POSITION_PAIRS,
    ids=[f"{p}-{n}" for p, n in _ALL_PLANET_POSITION_PAIRS],
)
def test_position_within_valid_house_range(planet, position):
    assert 1 <= position <= 12, (
        f"{planet}: position {position} outside valid range [1, 12]"
    )
    assert position != 1, (
        f"{planet}: position 1 (the planet's own sign) must never appear — "
        f"self-reference is excluded by classical design"
    )


# ── 4. Sorted-ascending invariant ───────────────────────────────────────────

@pytest.mark.parametrize(
    "planet,aspect_tuple", list(ASPECTED_HOUSES_BY_PLANET.items()),
    ids=list(ASPECTED_HOUSES_BY_PLANET.keys()),
)
def test_aspect_tuple_is_sorted_ascending_with_no_duplicates(planet, aspect_tuple):
    assert tuple(sorted(aspect_tuple)) == aspect_tuple, (
        f"{planet}: {aspect_tuple} is not sorted ascending"
    )
    assert len(set(aspect_tuple)) == len(aspect_tuple), (
        f"{planet}: {aspect_tuple} contains duplicate positions"
    )


# ── 5. Universal 7th-aspect invariant ───────────────────────────────────────

@pytest.mark.parametrize("planet", EXPECTED_PLANETS)
def test_every_planet_has_the_universal_seventh_aspect(planet):
    assert 7 in ASPECTED_HOUSES_BY_PLANET[planet], (
        f"{planet}: missing the universal 7th aspect (PVR §10.2: "
        f"\"all planets aspect the 7th house from them\") — "
        f"got {ASPECTED_HOUSES_BY_PLANET[planet]}"
    )


# ── 6. Special-aspect identity locks ────────────────────────────────────────

def test_mars_special_aspects():
    assert ASPECTED_HOUSES_BY_PLANET["Mars"] == (4, 7, 8), (
        "PVR §10.2 + Example 34: Mars aspects 4th, 7th, 8th"
    )


def test_jupiter_special_aspects():
    assert ASPECTED_HOUSES_BY_PLANET["Jupiter"] == (5, 7, 9), (
        "PVR §10.2 + Example 34: Jupiter aspects 5th, 7th, 9th"
    )


def test_saturn_special_aspects():
    assert ASPECTED_HOUSES_BY_PLANET["Saturn"] == (3, 7, 10), (
        "PVR §10.2 + Example 34: Saturn aspects 3rd, 7th, 10th"
    )


def test_rahu_special_aspects():
    assert ASPECTED_HOUSES_BY_PLANET["Rahu"] == (5, 7, 9), (
        "Locked classical-conflict resolution (Jun-2026): Rahu Jupiter-like "
        "5/7/9. JHora + Sanjay Rath + AstroSage convergence. See "
        "_aspects_tables.py comment block."
    )


def test_ketu_special_aspects():
    assert ASPECTED_HOUSES_BY_PLANET["Ketu"] == (5, 7, 9), (
        "Locked classical-conflict resolution (Jun-2026): Ketu Jupiter-like "
        "5/7/9. Same source convergence as Rahu. See _aspects_tables.py "
        "comment block."
    )


def test_non_special_planets_aspect_only_the_seventh():
    for planet in ("Sun", "Moon", "Mercury", "Venus"):
        assert ASPECTED_HOUSES_BY_PLANET[planet] == (7,), (
            f"PVR §10.2 default rule: {planet} has no special aspect, "
            f"expected (7,) only, got {ASPECTED_HOUSES_BY_PLANET[planet]}"
        )
