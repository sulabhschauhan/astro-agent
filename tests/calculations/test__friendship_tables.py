"""Structural invariant tests for agent/calculations/core/_friendship_tables.py.

Natural friendship is asymmetric by design — Section 4 cross-checks every
directed (actor, target) pair against a literal source grid transcribed
from PVR Table 7 / AstroSage's "Permanent Friendship" table, proving the
asymmetry was preserved and not silently collapsed into a symmetric matrix.

Independent of other test files and of any other production module by
design — reaches into _friendship_tables only, plus stdlib + pytest.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # project root

import pytest

from agent.calculations.core._friendship_tables import (
    NATURAL_FRIENDSHIP,
    COMPOUND_RELATIONSHIP_MAP,
)

CANONICAL_PLANETS = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
]

# Literal directed expected-relation grid, transcribed from PVR Table 7
# (equivalently, the "Permanent Friendship" table identical across all 4
# AstroSage reference PDFs). Row = acting planet, column = target planet,
# value = the acting planet's relation to the target. Diagonal (a planet's
# relation to itself) is not applicable and is omitted.
EXPECTED_RELATION = {
    "Sun":     {"Moon": "Friend",  "Mars": "Friend",  "Mercury": "Neutral", "Jupiter": "Friend",  "Venus": "Enemy",    "Saturn": "Enemy"},
    "Moon":    {"Sun": "Friend",   "Mars": "Neutral", "Mercury": "Friend",  "Jupiter": "Neutral", "Venus": "Neutral",  "Saturn": "Neutral"},
    "Mars":    {"Sun": "Friend",   "Moon": "Friend",  "Mercury": "Enemy",   "Jupiter": "Friend",  "Venus": "Neutral",  "Saturn": "Neutral"},
    "Mercury": {"Sun": "Friend",   "Moon": "Enemy",   "Mars": "Neutral",    "Jupiter": "Neutral", "Venus": "Friend",   "Saturn": "Neutral"},
    "Jupiter": {"Sun": "Friend",   "Moon": "Friend",  "Mars": "Friend",     "Mercury": "Enemy",   "Venus": "Enemy",    "Saturn": "Neutral"},
    "Venus":   {"Sun": "Enemy",    "Moon": "Enemy",   "Mars": "Neutral",    "Mercury": "Friend",  "Jupiter": "Neutral", "Saturn": "Friend"},
    "Saturn":  {"Sun": "Enemy",    "Moon": "Enemy",   "Mars": "Enemy",      "Mercury": "Friend",  "Jupiter": "Neutral", "Venus": "Friend"},
}

_ORDERED_PAIRS = [
    (actor, target)
    for actor in CANONICAL_PLANETS
    for target in CANONICAL_PLANETS
    if actor != target
]


def _actor_relation(actor: str, target: str) -> str:
    membership = [
        relation
        for relation, list_name in (
            ("Friend", "friends"), ("Neutral", "neutral"), ("Enemy", "enemies")
        )
        if target in NATURAL_FRIENDSHIP[actor][list_name]
    ]
    if len(membership) != 1:
        raise ValueError(
            f"{actor} -> {target}: expected exactly one relation, found {membership}"
        )
    return membership[0]


# ── 1. Completeness ───────────────────────────────────────────────────────

def test_natural_friendship_has_exactly_seven_canonical_planets():
    assert set(NATURAL_FRIENDSHIP.keys()) == set(CANONICAL_PLANETS), (
        f"NATURAL_FRIENDSHIP: keys {sorted(NATURAL_FRIENDSHIP.keys())} != "
        f"canonical planet set {sorted(CANONICAL_PLANETS)}"
    )
    assert len(NATURAL_FRIENDSHIP) == 7, (
        f"NATURAL_FRIENDSHIP: expected 7 entries, got {len(NATURAL_FRIENDSHIP)}"
    )


# ── 2. Partition completeness, all 7 planets ────────────────────────────────

@pytest.mark.parametrize("planet", CANONICAL_PLANETS)
def test_partition_completeness(planet):
    entry = NATURAL_FRIENDSHIP[planet]
    friends, neutral, enemies = entry["friends"], entry["neutral"], entry["enemies"]
    others = set(CANONICAL_PLANETS) - {planet}

    union = set(friends) | set(neutral) | set(enemies)
    assert union == others, (
        f"{planet}: union of friends/neutral/enemies {sorted(union)} != "
        f"other 6 canonical planets {sorted(others)}"
    )

    assert not (set(friends) & set(neutral)), (
        f"{planet}: friends and neutral overlap — {set(friends) & set(neutral)}"
    )
    assert not (set(friends) & set(enemies)), (
        f"{planet}: friends and enemies overlap — {set(friends) & set(enemies)}"
    )
    assert not (set(neutral) & set(enemies)), (
        f"{planet}: neutral and enemies overlap — {set(neutral) & set(enemies)}"
    )

    assert planet not in friends and planet not in neutral and planet not in enemies, (
        f"{planet}: self-reference found in its own friends/neutral/enemies lists"
    )

    total = len(friends) + len(neutral) + len(enemies)
    assert total == 6, (
        f"{planet}: combined list length {total} != 6 "
        f"(friends={friends}, neutral={neutral}, enemies={enemies}) — "
        f"possible duplicate within a single list"
    )


# ── 3. Planet-name validity (typo / scope guard) ────────────────────────────

def test_all_planet_names_are_canonical():
    for planet, entry in NATURAL_FRIENDSHIP.items():
        for list_name in ("friends", "neutral", "enemies"):
            for name in entry[list_name]:
                assert name in CANONICAL_PLANETS, (
                    f"{planet}.{list_name}: unrecognized/out-of-scope planet "
                    f"name {name!r} (also catches accidental Rahu/Ketu inclusion)"
                )


# ── 4. Full directed cross-check against the literal source grid ───────────

@pytest.mark.parametrize("actor,target", _ORDERED_PAIRS)
def test_directed_relation_matches_source_grid(actor, target):
    expected = EXPECTED_RELATION[actor][target]
    actual = _actor_relation(actor, target)
    assert actual == expected, (
        f"{actor} -> {target}: expected {expected!r}, got {actual!r}"
    )


# ── 5. Compound relationship map completeness ───────────────────────────────

def test_compound_relationship_map_has_exactly_six_keys():
    assert len(COMPOUND_RELATIONSHIP_MAP) == 6, (
        f"COMPOUND_RELATIONSHIP_MAP: expected 6 entries, got "
        f"{len(COMPOUND_RELATIONSHIP_MAP)}"
    )


def test_compound_relationship_map_keys_are_full_cross_product():
    expected_keys = {
        (natural, temporal)
        for natural in ("Friend", "Neutral", "Enemy")
        for temporal in ("Friend", "Enemy")
    }
    assert set(COMPOUND_RELATIONSHIP_MAP.keys()) == expected_keys, (
        f"COMPOUND_RELATIONSHIP_MAP: keys {sorted(COMPOUND_RELATIONSHIP_MAP.keys())} "
        f"!= full cross product {sorted(expected_keys)}"
    )


@pytest.mark.parametrize(
    "key,expected_value",
    [
        (("Friend", "Friend"), "Adhimitra"),
        (("Friend", "Enemy"), "Sama"),
        (("Neutral", "Friend"), "Mitra"),
        (("Neutral", "Enemy"), "Satru"),
        (("Enemy", "Friend"), "Sama"),
        (("Enemy", "Enemy"), "Adhisatru"),
    ],
)
def test_compound_relationship_values_match_pvr_table_8(key, expected_value):
    assert COMPOUND_RELATIONSHIP_MAP[key] == expected_value, (
        f"COMPOUND_RELATIONSHIP_MAP[{key}]: expected {expected_value!r}, "
        f"got {COMPOUND_RELATIONSHIP_MAP[key]!r}"
    )
