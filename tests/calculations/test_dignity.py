"""Behavioral tests for get_dignity_status() in agent/calculations/core/dignity.py.

Covers Moolatrikona/Own boundary correctness, the Moon/Mercury shared
exaltation-MT sign special case, whole-sign exaltation/debilitation, the
no-special-dignity case, and input validation.

Independent of test__dignity_tables.py by design — constants are redefined
here rather than imported across test files, plus stdlib + pytest.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # project root

import pytest

from agent.calculations.core.dignity import get_dignity_status
from agent.calculations.core._dignity_tables import (
    EXALTATION,
    DEBILITATION,
    MOOLATRIKONA,
    OWN_SIGNS,
)

CANONICAL_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
CANONICAL_PLANETS = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
]

EPSILON = 0.001


# ── A. Moolatrikona right-edge, all 9 planets ───────────────────────────────

@pytest.mark.parametrize("planet", CANONICAL_PLANETS)
def test_mt_right_edge_is_moolatrikona(planet):
    mt_sign, mt_start, mt_end = MOOLATRIKONA[planet]
    result = get_dignity_status(planet, mt_sign, mt_end - EPSILON)
    assert result == "Moolatrikona", (
        f"{planet} at {mt_sign} {mt_end - EPSILON}: expected Moolatrikona, got {result}"
    )


@pytest.mark.parametrize("planet", CANONICAL_PLANETS)
def test_status_exactly_at_mt_end(planet):
    mt_sign, mt_start, mt_end = MOOLATRIKONA[planet]
    if mt_end == 30.0:
        pytest.skip(f"{planet}: MT spans the full sign (mt_end == 30.0); degree 30.0 is out of domain")

    expected = None
    for own_sign, own_start, own_end in OWN_SIGNS[planet]:
        if own_sign == mt_sign and own_start == mt_end:
            expected = "Own"
            break

    result = get_dignity_status(planet, mt_sign, mt_end)
    assert result == expected, (
        f"{planet} at {mt_sign} {mt_end}: expected {expected}, got {result}"
    )


# ── B. Exalt/MT internal boundary, Moon and Mercury only ───────────────────

_SHARED_SIGN_PLANETS = [
    planet for planet in CANONICAL_PLANETS
    if EXALTATION[planet][0] == MOOLATRIKONA[planet][0]
]


@pytest.mark.parametrize("planet", _SHARED_SIGN_PLANETS)
def test_exalt_mt_internal_boundary(planet):
    mt_sign, mt_start, mt_end = MOOLATRIKONA[planet]

    below = get_dignity_status(planet, mt_sign, mt_start - EPSILON)
    assert below == "Exalted", (
        f"{planet} at {mt_sign} {mt_start - EPSILON}: expected Exalted, got {below}"
    )

    at_start = get_dignity_status(planet, mt_sign, mt_start)
    assert at_start == "Moolatrikona", (
        f"{planet} at {mt_sign} {mt_start}: expected Moolatrikona, got {at_start}"
    )


# ── C. Whole-sign exaltation for the other 7 planets ────────────────────────

_DISTINCT_SIGN_PLANETS = [
    planet for planet in CANONICAL_PLANETS
    if EXALTATION[planet][0] != MOOLATRIKONA[planet][0]
]


@pytest.mark.parametrize("planet", _DISTINCT_SIGN_PLANETS)
def test_whole_sign_exaltation(planet):
    exalt_sign, _ = EXALTATION[planet]

    low = get_dignity_status(planet, exalt_sign, 0.0)
    assert low == "Exalted", f"{planet} at {exalt_sign} 0.0: expected Exalted, got {low}"

    high = get_dignity_status(planet, exalt_sign, 29.99)
    assert high == "Exalted", f"{planet} at {exalt_sign} 29.99: expected Exalted, got {high}"


# ── D. Whole-sign debilitation, all 9 planets ───────────────────────────────

@pytest.mark.parametrize("planet", CANONICAL_PLANETS)
def test_whole_sign_debilitation(planet):
    debil_sign, _ = DEBILITATION[planet]

    low = get_dignity_status(planet, debil_sign, 0.0)
    assert low == "Debilitated", f"{planet} at {debil_sign} 0.0: expected Debilitated, got {low}"

    high = get_dignity_status(planet, debil_sign, 29.99)
    assert high == "Debilitated", f"{planet} at {debil_sign} 29.99: expected Debilitated, got {high}"


# ── E. Regular / no-special-dignity case ────────────────────────────────────

def _uninvolved_sign(planet: str) -> str:
    exalt_sign, _ = EXALTATION[planet]
    debil_sign, _ = DEBILITATION[planet]
    mt_sign, _, _ = MOOLATRIKONA[planet]
    involved = {exalt_sign, debil_sign, mt_sign}
    involved.update(sign for sign, _, _ in OWN_SIGNS[planet])

    for sign in CANONICAL_SIGNS:
        if sign not in involved:
            return sign

    raise AssertionError(f"{planet}: all 12 signs are involved, no uninvolved sign to test against")


@pytest.mark.parametrize("planet", CANONICAL_PLANETS)
def test_no_special_dignity_in_uninvolved_sign(planet):
    sign = _uninvolved_sign(planet)
    result = get_dignity_status(planet, sign, 15.0)
    assert result is None, f"{planet} at {sign} 15.0: expected None, got {result}"


# ── F. Input validation ─────────────────────────────────────────────────────

def test_unrecognized_planet_raises():
    with pytest.raises(ValueError):
        get_dignity_status("Pluto", "Aries", 10.0)


def test_unrecognized_sign_raises():
    with pytest.raises(ValueError):
        get_dignity_status("Sun", "Ophiuchus", 10.0)


def test_degree_below_zero_raises():
    with pytest.raises(ValueError):
        get_dignity_status("Sun", "Aries", -0.01)


def test_degree_at_thirty_raises():
    with pytest.raises(ValueError):
        get_dignity_status("Sun", "Aries", 30.0)
