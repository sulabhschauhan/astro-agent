"""Behavioral tests for natural_friendship(), tatkalika_friendship(), and
pancha_dha_maitri() in agent/calculations/core/friendship.py.

Covers behavioral spot checks, error paths, the tatkalika symmetry
invariant, PVR worked-example golden cases for pancha_dha_maitri, the
explicit Rahu/Ketu pre-check added in commit d9a89ef, error propagation,
a return-label integrity smoke test, and CLASSICAL_PLANETS invariants.

Data correctness of NATURAL_FRIENDSHIP and COMPOUND_RELATIONSHIP_MAP is
covered in test__friendship_tables.py and not duplicated here.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # project root

import pytest

from agent.calculations.core.friendship import (
    natural_friendship,
    tatkalika_friendship,
    pancha_dha_maitri,
    CLASSICAL_PLANETS,
)
from agent.calculations.core._friendship_tables import NATURAL_FRIENDSHIP

CANONICAL_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


# ── 1. natural_friendship() behavioral spot checks ──────────────────────────

@pytest.mark.parametrize(
    "planet_a,planet_b,expected",
    [
        ("Sun", "Moon", "Friend"),
        ("Sun", "Mercury", "Neutral"),
        ("Sun", "Saturn", "Enemy"),
        ("Moon", "Mercury", "Friend"),
        ("Mercury", "Moon", "Enemy"),  # asymmetric: Moon -> Mercury is Friend
    ],
    ids=[
        "sun-moon-friend", "sun-mercury-neutral", "sun-saturn-enemy",
        "moon-mercury-friend", "mercury-moon-enemy-asymmetric",
    ],
)
def test_natural_friendship_spot_checks(planet_a, planet_b, expected):
    result = natural_friendship(planet_a, planet_b)
    assert result == expected, f"{planet_a} -> {planet_b}: expected {expected}, got {result}"


# ── 2. natural_friendship() error paths ─────────────────────────────────────

def test_natural_friendship_unknown_planet_raises():
    with pytest.raises(ValueError, match="Pluto"):
        natural_friendship("Pluto", "Sun")


def test_natural_friendship_empty_string_raises():
    with pytest.raises(ValueError):
        natural_friendship("", "Sun")


def test_natural_friendship_same_planet_raises():
    with pytest.raises(ValueError, match="Sun"):
        natural_friendship("Sun", "Sun")


def test_natural_friendship_rahu_as_planet_a_raises():
    with pytest.raises(ValueError, match="Rahu") as exc_info:
        natural_friendship("Rahu", "Sun")
    assert "Table 7" in str(exc_info.value)


def test_natural_friendship_ketu_as_planet_b_raises():
    with pytest.raises(ValueError, match="Ketu") as exc_info:
        natural_friendship("Sun", "Ketu")
    assert "Table 7" in str(exc_info.value)


def test_natural_friendship_case_sensitive():
    with pytest.raises(ValueError):
        natural_friendship("sun", "Moon")


# ── 3. tatkalika_friendship() behavioral checks (PVR §3.4.2 Example 4, Sree Rama) ──

def _independent_tatkalika_rule(sign_a: str, sign_b: str) -> str:
    """Reimplementation of PVR's count rule, independent of
    tatkalika_friendship(), so this test catches drift between the rule
    and the implementation rather than just mirroring it."""
    count = (CANONICAL_SIGNS.index(sign_b) - CANONICAL_SIGNS.index(sign_a)) % 12 + 1
    if count in (2, 3, 4, 10, 11, 12):
        return "Friend"
    return "Enemy"


@pytest.mark.parametrize("sign_b", CANONICAL_SIGNS, ids=CANONICAL_SIGNS)
def test_tatkalika_friendship_matches_independent_rule_from_aries(sign_b):
    expected = _independent_tatkalika_rule("Aries", sign_b)
    result = tatkalika_friendship("Aries", sign_b)
    assert result == expected, f"Aries -> {sign_b}: expected {expected}, got {result}"


def test_tatkalika_friendship_same_sign_is_enemy():
    assert tatkalika_friendship("Cancer", "Cancer") == "Enemy"


# ── 4. tatkalika_friendship() structural symmetry property ─────────────────
#
# tatkalika_friendship(a, b) == tatkalika_friendship(b, a) for every ordered
# pair, same-sign included. This isn't just empirically true -- it is
# mathematically guaranteed: the friend set {2, 3, 4, 10, 11, 12} is closed
# under count -> (14 - count) mod 12 (mapped into 1..12), which is exactly
# the count transformation produced by swapping (a, b). This test is a
# future-proofing regression guard against an accidental change to the
# friend-set definition silently breaking that closure property, not just
# hand-verification of the current values.

_ALL_SIGN_PAIRS = [(a, b) for a in CANONICAL_SIGNS for b in CANONICAL_SIGNS]


@pytest.mark.parametrize(
    "sign_a,sign_b", _ALL_SIGN_PAIRS,
    ids=[f"{a}-{b}" for a, b in _ALL_SIGN_PAIRS],
)
def test_tatkalika_friendship_is_symmetric(sign_a, sign_b):
    forward = tatkalika_friendship(sign_a, sign_b)
    backward = tatkalika_friendship(sign_b, sign_a)
    assert forward == backward, (
        f"{sign_a} <-> {sign_b}: tatkalika_friendship not symmetric "
        f"({sign_a}->{sign_b}={forward}, {sign_b}->{sign_a}={backward})"
    )


# ── 5. tatkalika_friendship() error paths ───────────────────────────────────

def test_tatkalika_friendship_unknown_sign_raises():
    with pytest.raises(ValueError, match="Pluto"):
        tatkalika_friendship("Pluto", "Aries")


def test_tatkalika_friendship_empty_string_raises():
    with pytest.raises(ValueError):
        tatkalika_friendship("", "Aries")


def test_tatkalika_friendship_case_sensitive():
    with pytest.raises(ValueError):
        tatkalika_friendship("aries", "Taurus")


# ── 6. pancha_dha_maitri() PVR worked-example golden cases ──────────────────
#
# Sree Rama's chart, PVR §3.4: Sun in Aries, Moon in Cancer, Mercury in
# Taurus, Mars in Capricorn, Jupiter in Cancer, Venus in Pisces, Saturn in
# Libra.

_GOLDEN_CASES = [
    # PVR Example 5 -- Sun (in Aries)
    ("Sun", "Aries", "Moon", "Cancer", "Adhimitra"),
    ("Sun", "Aries", "Mars", "Capricorn", "Adhimitra"),
    ("Sun", "Aries", "Jupiter", "Cancer", "Adhimitra"),
    ("Sun", "Aries", "Mercury", "Taurus", "Mitra"),
    ("Sun", "Aries", "Venus", "Pisces", "Sama"),
    ("Sun", "Aries", "Saturn", "Libra", "Adhisatru"),

    # PVR Example 5 -- Moon (in Cancer)
    ("Moon", "Cancer", "Sun", "Aries", "Adhimitra"),
    ("Moon", "Cancer", "Mercury", "Taurus", "Adhimitra"),
    ("Moon", "Cancer", "Saturn", "Libra", "Mitra"),
    ("Moon", "Cancer", "Mars", "Capricorn", "Satru"),
    ("Moon", "Cancer", "Jupiter", "Cancer", "Satru"),
    ("Moon", "Cancer", "Venus", "Pisces", "Satru"),

    # PVR Exercise 6 -- Jupiter (in Cancer). Jupiter -> Venus is
    # deliberately OMITTED from this golden set:
    #   - PVR Exercise 6's prose calls Venus "a neutral planet in natural
    #     relationship" relative to Jupiter, which would yield compound =
    #     Satru.
    #   - PVR Table 7 lists Venus in Jupiter's enemies (also confirmed by
    #     the §3.4.1 moolatrikona derivation, all 4 AstroSage reference
    #     PDFs, and JHora).
    #   - Table 7 is authoritative; Exercise 6's prose at this one case is
    #     a PVR-internal errata, not a second valid source.
    #   - The implementation correctly returns "Adhisatru" for this pair
    #     per the table; the case is omitted here so this test doesn't
    #     encode the errata as a golden value. A spec-reference note
    #     covering this errata will be added separately.
    ("Jupiter", "Cancer", "Sun", "Aries", "Adhimitra"),
    ("Jupiter", "Cancer", "Saturn", "Libra", "Mitra"),
    ("Jupiter", "Cancer", "Mercury", "Taurus", "Sama"),
    ("Jupiter", "Cancer", "Moon", "Cancer", "Sama"),
    ("Jupiter", "Cancer", "Mars", "Capricorn", "Sama"),

    # PVR Exercise 6 -- Venus (in Pisces)
    ("Venus", "Pisces", "Mercury", "Taurus", "Adhimitra"),
    ("Venus", "Pisces", "Mars", "Capricorn", "Mitra"),
    ("Venus", "Pisces", "Sun", "Aries", "Sama"),
    ("Venus", "Pisces", "Saturn", "Libra", "Sama"),
    ("Venus", "Pisces", "Jupiter", "Cancer", "Satru"),
    ("Venus", "Pisces", "Moon", "Cancer", "Adhisatru"),
]


@pytest.mark.parametrize(
    "planet_a,sign_a,planet_b,sign_b,expected",
    _GOLDEN_CASES,
    ids=[f"{p_a}-in-{s_a}_vs_{p_b}-in-{s_b}" for p_a, s_a, p_b, s_b, _ in _GOLDEN_CASES],
)
def test_pancha_dha_maitri_pvr_golden_cases(planet_a, sign_a, planet_b, sign_b, expected):
    result = pancha_dha_maitri(planet_a, sign_a, planet_b, sign_b)
    assert result == expected, (
        f"{planet_a} (in {sign_a}) -> {planet_b} (in {sign_b}): "
        f"expected {expected!r}, got {result!r}"
    )


# ── 7. pancha_dha_maitri() Rahu/Ketu pre-check ──────────────────────────────

@pytest.mark.parametrize(
    "planet_a,sign_a,planet_b,sign_b,offending_node",
    [
        ("Rahu", "Aries", "Sun", "Taurus", "Rahu"),
        ("Ketu", "Aries", "Sun", "Taurus", "Ketu"),
        ("Sun", "Aries", "Rahu", "Taurus", "Rahu"),
        ("Sun", "Aries", "Ketu", "Taurus", "Ketu"),
        ("Rahu", "Aries", "Ketu", "Taurus", "Rahu"),
    ],
    ids=["rahu-as-a", "ketu-as-a", "rahu-as-b", "ketu-as-b", "rahu-and-ketu"],
)
def test_pancha_dha_maitri_rejects_nodes(planet_a, sign_a, planet_b, sign_b, offending_node):
    with pytest.raises(ValueError) as exc_info:
        pancha_dha_maitri(planet_a, sign_a, planet_b, sign_b)
    message = str(exc_info.value)
    assert "pancha_dha_maitri" in message, (
        f"error message does not name the function: {message!r}"
    )
    assert offending_node in message, (
        f"error message does not name the offending node {offending_node!r}: {message!r}"
    )


# ── 8. pancha_dha_maitri() error propagation ────────────────────────────────

def test_pancha_dha_maitri_unknown_planet_propagates():
    with pytest.raises(ValueError, match="Pluto"):
        pancha_dha_maitri("Pluto", "Aries", "Sun", "Taurus")


def test_pancha_dha_maitri_same_planet_propagates():
    with pytest.raises(ValueError, match="Sun"):
        pancha_dha_maitri("Sun", "Aries", "Sun", "Taurus")


def test_pancha_dha_maitri_unknown_sign_propagates():
    with pytest.raises(ValueError, match="Atlantis"):
        pancha_dha_maitri("Sun", "Aries", "Moon", "Atlantis")


# ── 9. pancha_dha_maitri() return-label validity smoke test ────────────────
#
# Return-set integrity check, not a correctness check: catches a new label
# being silently introduced or the COMPOUND_RELATIONSHIP_MAP partition
# breaking, across the full 42-pair directed cross product of
# CLASSICAL_PLANETS at a fixed, arbitrary sign pair.

_VALID_COMPOUND_LABELS = {"Adhimitra", "Mitra", "Sama", "Satru", "Adhisatru"}

_DIRECTED_PLANET_PAIRS = [
    (planet_a, planet_b)
    for planet_a in CLASSICAL_PLANETS
    for planet_b in CLASSICAL_PLANETS
    if planet_a != planet_b
]


@pytest.mark.parametrize(
    "planet_a,planet_b", _DIRECTED_PLANET_PAIRS,
    ids=[f"{a}-{b}" for a, b in _DIRECTED_PLANET_PAIRS],
)
def test_pancha_dha_maitri_return_label_is_valid(planet_a, planet_b):
    result = pancha_dha_maitri(planet_a, "Aries", planet_b, "Taurus")
    assert result in _VALID_COMPOUND_LABELS, (
        f"{planet_a} -> {planet_b}: returned {result!r}, not one of {_VALID_COMPOUND_LABELS}"
    )


# ── 10. CLASSICAL_PLANETS module-level invariants ───────────────────────────

def test_classical_planets_is_a_tuple():
    assert isinstance(CLASSICAL_PLANETS, tuple), (
        f"CLASSICAL_PLANETS: expected tuple, got {type(CLASSICAL_PLANETS)}"
    )


def test_classical_planets_has_seven_entries():
    assert len(CLASSICAL_PLANETS) == 7, (
        f"CLASSICAL_PLANETS: expected 7 entries, got {len(CLASSICAL_PLANETS)}"
    )


def test_classical_planets_exact_pvr_ordering():
    expected = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
    assert CLASSICAL_PLANETS == expected, (
        f"CLASSICAL_PLANETS: expected PVR's standard ordering {expected}, "
        f"got {CLASSICAL_PLANETS}"
    )


def test_classical_planets_matches_natural_friendship_keys():
    assert set(CLASSICAL_PLANETS) == set(NATURAL_FRIENDSHIP.keys()), (
        f"CLASSICAL_PLANETS {sorted(CLASSICAL_PLANETS)} != "
        f"NATURAL_FRIENDSHIP.keys() {sorted(NATURAL_FRIENDSHIP.keys())}"
    )


def test_rahu_not_in_classical_planets():
    assert "Rahu" not in CLASSICAL_PLANETS


def test_ketu_not_in_classical_planets():
    assert "Ketu" not in CLASSICAL_PLANETS
