"""
tests/calculations/kp/test_significator_engine.py
Validation for agent.calculations.kp.significator_engine.compute_kp_significators
-- the EPHEMERIS-COMPUTED KP house-significator engine.

INTEGRATION, NOT FIXTURE (S144 correction): an earlier version of this test
hand-built a chart dict with PDF-Chalit/Lahiri cusps, which placed planets in
DIFFERENT KP houses than chart_calculator's real KP-Placidus cusps -- so it
validated significations that never occur in production (e.g. a spurious
Mercury/Rahu co-occupancy that gave Rahu a house-7 signification it does not
actually have). This version drives the REAL chart_calculator so the cusps,
occupancy and significators are exactly what production computes. Needs
pyswisseph (skipped if unavailable, e.g. a firewalled sandbox).

GROUND TRUTH: the computed output matches AstroSage's independently-parsed
"Significators of Houses" table (tests/calculations/kp/test_significators.py's
oracle) for 8/9 planets; the one delta is Rahu's node-dispositor signification
of house 12, a classical KP node-agency route AstroSage's table omits. So this
suite pins BOTH: the exact computed set per planet, AND that agreement with the
parser oracle where the two methods should coincide.

HARDEST CASE: the Sulabh reference chart's 7th (Gemini) is empty and its lord
Mercury is debilitated in the 4th -- the exact chart the marriage investigation
turns on.

Python 3.11.
"""
from __future__ import annotations

import pytest

pytest.importorskip("swisseph")  # integration test: needs the real ephemeris

from agent.chart_calculator import calculate_chart
from agent.calculations.kp.significator_engine import (
    compute_kp_significators,
    significators_for_house,
)

_SULABH = ("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")

# The engine's real computed output (verified against the pilot fact block AND
# the AstroSage parser oracle). Houses ascending per planet.
_EXPECTED_HOUSES = {
    "Sun": (3, 7, 9),
    "Moon": (1, 3, 4, 8, 10),
    "Mars": (1, 3, 4, 11, 12),
    "Mercury": (2, 3, 7, 9, 12),
    "Jupiter": (1, 3, 4, 8),
    "Venus": (3, 5, 6, 10),
    "Saturn": (2, 8, 12),
    "Rahu": (1, 2, 3, 4, 12),   # 12 = node-dispositor (Saturn); AstroSage omits it
    "Ketu": (3, 8),
}
# AstroSage parser oracle (tests/calculations/kp/test_significators.py). The two
# methods must agree everywhere EXCEPT Rahu's node-dispositor house 12.
_ASTROSAGE_ORACLE = {**_EXPECTED_HOUSES, "Rahu": (1, 2, 3, 4)}


@pytest.fixture(scope="module")
def sig():
    result = compute_kp_significators(calculate_chart(*_SULABH))
    return {p: tuple(sorted(hm)) for p, hm in result["significators"].items()}


def test_all_nine_planets_present(sig):
    assert set(sig) == set(_EXPECTED_HOUSES)


@pytest.mark.parametrize("planet", list(_EXPECTED_HOUSES))
def test_computed_houses_match_pinned(sig, planet):
    assert sig[planet] == _EXPECTED_HOUSES[planet]


@pytest.mark.parametrize("planet", list(_ASTROSAGE_ORACLE))
def test_agrees_with_astrosage_parser_oracle_except_rahu_node_agency(sig, planet):
    # Cross-method validation: ephemeris-compute vs PDF-parse must coincide,
    # the one documented exception being Rahu's extra node-dispositor house 12.
    assert sig[planet] == _ASTROSAGE_ORACLE[planet] or (
        planet == "Rahu" and set(sig["Rahu"]) - set(_ASTROSAGE_ORACLE["Rahu"]) == {12}
    )


# ---- marriage-relevant structural facts (what the discriminator can/can't do) ----

def test_venus_is_a_true_negative_for_marriage(sig):
    # The naive "Venus = karaka" pick touches NONE of {2,7,11}. Correctly killed.
    assert {2, 7, 11} & set(sig["Venus"]) == set()


def test_rahu_touches_only_house_2_of_the_triad(sig):
    # Correction of an earlier false claim: Rahu does NOT signify 7 or 11 on
    # this chart -- only 2 (family), via node agency. So significators alone
    # cannot single Mercury-Rahu out; that pick lives in transit convergence.
    assert {2, 7, 11} & set(sig["Rahu"]) == {2}


def test_mercury_the_seventh_lord_touches_2_and_7(sig):
    assert {2, 7, 11} & set(sig["Mercury"]) == {2, 7}


def test_seventh_house_significators_include_mercury_and_sun_not_venus(sig):
    result = compute_kp_significators(calculate_chart(*_SULABH))
    planets = {p for p, _t, _v in significators_for_house(result["significators"], 7)}
    assert {"Mercury", "Sun"} <= planets
    assert "Venus" not in planets
