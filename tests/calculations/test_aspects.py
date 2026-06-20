"""Behavioral tests for the public aspect (graha drishti) functions in
agent/calculations/core/aspects.py: signs_aspected_by, does_planet_aspect_sign,
aspects_between, and the ASPECTING_PLANETS constant.

Data correctness of ASPECTED_HOUSES_BY_PLANET (the table these functions
consume) is covered in test__aspects_tables.py and not duplicated here --
this file covers the functions that consume that table, not the table
itself.
"""

# ── 1. Imports & Fixtures ────────────────────────────────────────────────────

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # project root

import pytest

from agent.calculations.core.aspects import (
    ASPECTING_PLANETS,
    aspects_between,
    does_planet_aspect_sign,
    signs_aspected_by,
)

_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

# Hardcoded independently of ASPECTED_HOUSES_BY_PLANET on purpose -- Section 6
# checks the function's output against this golden expectation, not against
# the table it's literally built from, so a drift in either one gets caught
# rather than the test silently mirroring whatever the table currently says.
_EXPECTED_ASPECT_COUNT = {
    "Sun": 1, "Moon": 1, "Mercury": 1, "Venus": 1,
    "Mars": 3, "Jupiter": 3, "Saturn": 3, "Rahu": 3, "Ketu": 3,
}


def _seventh_sign(sign: str) -> str:
    """The classical 7th-house sign from `sign` -- the opposite sign on the
    zodiac wheel, independent of any planet's identity or special aspects."""
    return _SIGNS[(_SIGNS.index(sign) + 6) % 12]


# ── 2. PVR §10.2 Example 34 golden worked cases ──────────────────────────────

def test_mars_in_leo_aspects_pvr_example_34():
    # PVR §10.2 Example 34: Mars in Leo -> 4th/7th/8th = Scorpio/Aquarius/Pisces.
    result = signs_aspected_by("Mars", "Leo")
    assert set(result) == {"Scorpio", "Aquarius", "Pisces"}


def test_jupiter_in_gemini_aspects_pvr_example_34():
    # PVR §10.2 Example 34: Jupiter in Gemini -> 5th/7th/9th = Libra/Sagittarius/Aquarius.
    result = signs_aspected_by("Jupiter", "Gemini")
    assert set(result) == {"Libra", "Sagittarius", "Aquarius"}


def test_saturn_in_sagittarius_aspects_pvr_example_34():
    # PVR §10.2 Example 34: Saturn in Sagittarius -> 3rd/7th/10th = Aquarius/Gemini/Virgo.
    result = signs_aspected_by("Saturn", "Sagittarius")
    assert set(result) == {"Aquarius", "Gemini", "Virgo"}


# ── 3. Citation-regression locks for Rahu/Ketu ───────────────────────────────

_RAHU_KETU_LOCK_MESSAGE = (
    "Rahu/Ketu lock = (5,7,9). User-perceived correctness tiebreaker applied; "
    "see _aspects_tables.py §3-§4 for full source landscape and decision "
    "rationale. PyJHora (7,)-only and JHora-UI 2,5,7,9-asymmetric are "
    "explicitly rejected alternatives."
)


def test_rahu_jupiter_pattern_citation_lock():
    # _aspects_tables.py §3-§4 tiebreaker: Rahu locked to Jupiter-pattern (5,7,9).
    result = signs_aspected_by("Rahu", "Aries")
    assert set(result) == {"Leo", "Libra", "Sagittarius"}, _RAHU_KETU_LOCK_MESSAGE


def test_ketu_jupiter_pattern_citation_lock():
    # _aspects_tables.py §3-§4 tiebreaker: Ketu locked to Jupiter-pattern (5,7,9).
    result = signs_aspected_by("Ketu", "Cancer")
    assert set(result) == {"Scorpio", "Capricorn", "Pisces"}, _RAHU_KETU_LOCK_MESSAGE


# ── 4. Universal 7th-aspect mutual symmetry (structural invariant) ──────────

def test_universal_seventh_aspect_is_mutually_symmetric_across_all_planet_pairs():
    # Every planet aspects its own 7th, and 7th-from-S / 7th-from-T is always
    # mutual (opposite signs on the wheel) -- this must hold for every
    # distinct planet pair, independent of which planet sits where.
    for planet_a in ASPECTING_PLANETS:
        for planet_b in ASPECTING_PLANETS:
            if planet_a == planet_b:
                continue
            for sign_s in _SIGNS:
                sign_t = _seventh_sign(sign_s)
                assert does_planet_aspect_sign(planet_a, sign_s, sign_t), (
                    f"{planet_a} in {sign_s} must aspect its universal "
                    f"7th, {sign_t}"
                )
                assert does_planet_aspect_sign(planet_b, sign_t, sign_s), (
                    f"7th-aspect symmetry broken for pair "
                    f"{planet_a}/{planet_b}: {planet_b} in {sign_t} must "
                    f"aspect its universal 7th, {sign_s}"
                )


# ── 5. Error-path coverage ───────────────────────────────────────────────────

def test_signs_aspected_by_rejects_unrecognized_planet_name():
    with pytest.raises(ValueError, match="Pluto"):
        signs_aspected_by("Pluto", "Aries")


def test_does_planet_aspect_sign_rejects_unrecognized_target_sign():
    with pytest.raises(ValueError, match="Atlantis"):
        does_planet_aspect_sign("Mars", "Leo", "Atlantis")


def test_aspects_between_rejects_same_planet_pair():
    # Confirmed against aspects.py's actual contract: same-planet input
    # raises ValueError, it does not silently return False.
    with pytest.raises(ValueError, match="Mars"):
        aspects_between("Mars", "Leo", "Mars", "Scorpio")


def test_signs_aspected_by_is_case_sensitive_rejects_uppercase_planet_name():
    # aspects.py does not normalize case -- "RAHU" is not "Rahu" and is
    # rejected the same as any other unrecognized planet name.
    with pytest.raises(ValueError, match="RAHU"):
        signs_aspected_by("RAHU", "Aries")


# ── 6. Full integrity smoke test ─────────────────────────────────────────────

@pytest.mark.parametrize("planet", ASPECTING_PLANETS)
def test_signs_aspected_by_full_integrity_smoke(planet):
    # Iterates all 12 signs per planet inside one parametrized case (108
    # planet/sign combinations total across the 9 invocations) rather than
    # exploding into 108 separately collected tests.
    expected_length = _EXPECTED_ASPECT_COUNT[planet]

    for sign in _SIGNS:
        result = signs_aspected_by(planet, sign)

        assert isinstance(result, tuple), (
            f"{planet} in {sign}: expected tuple, got {type(result)}"
        )
        assert len(result) == expected_length, (
            f"{planet} in {sign}: expected {expected_length} aspected "
            f"signs, got {len(result)} ({result})"
        )
        assert _seventh_sign(sign) in result, (
            f"{planet} in {sign}: universal 7th-aspect sign "
            f"{_seventh_sign(sign)!r} missing from {result}"
        )
        assert len(result) == len(set(result)), (
            f"{planet} in {sign}: duplicate signs in {result}"
        )
        assert all(s in _SIGNS for s in result), (
            f"{planet} in {sign}: non-canonical sign name in {result}"
        )
