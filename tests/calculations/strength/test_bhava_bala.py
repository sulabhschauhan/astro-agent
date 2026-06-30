"""Tests for agent/calculations/strength/bhava_bala.py — Bhavadhipati Bala.

Layer A: Full 12-house validation, all 4 charts (48 parametrized assertions).
         Oracle: AstroSage fixture shadbala_virupa values for each chart's
         ruling planets. Uses fixture-based shadbala_totals, NOT live
         compute_shadbala_totals(), because the V1 Drik Bala stub causes
         divergence of up to ~20 Virupa per planet between live compute and
         AstroSage — making the required ±0.5 tolerance infeasible with live
         compute. Fixture values == AstroSage oracle, which is exactly what
         compute_bhavadhipati_bala is supposed to return.

Layer B: Same-lord pair — two houses sharing a lord return identical Virupa.

Layer C: Error handling — 4 scenarios, each must raise ValueError naming the
         specific problem (house key, sign string, or missing planet).

Layer D: Output shape — returned dict has exactly keys 1-12, all float values.

Source divergence note: Bhavadhipati Bala is a pure lookup (no new computation).
Expected values are fixture shadbala_virupa values for the house's sign lord.

Reference: reference_charts.md for Lagna signs.
  Sulabh=Sagittarius  (AstroSage Vedic Report PDF)
  Surbhi=Libra        (reference_charts.md: ASC Libra 29-52-55)
  Sheridan=Taurus     (reference_charts.md: ASC Taurus 28-46-17)
  David=Virgo         (reference_charts.md: ASC Virgo 05-16-57)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest

from agent.calculations.strength.bhava_bala import compute_bhavadhipati_bala
from agent.chart_calculator import SIGN_LORDS
from tests.fixtures.shadbala_fixtures import SHADBALA_FIXTURES

# ── Shared test data ──────────────────────────────────────────────────────────

# Whole-sign house maps derived from each chart's natal Lagna sign.
# Lagna sign = house 1; subsequent signs in zodiacal order fill houses 2-12.
_HOUSE_SIGNS: dict[str, dict[int, str]] = {
    "sulabh": {
        1: "Sagittarius", 2: "Capricorn", 3: "Aquarius",  4: "Pisces",
        5: "Aries",       6: "Taurus",    7: "Gemini",    8: "Cancer",
        9: "Leo",        10: "Virgo",    11: "Libra",    12: "Scorpio",
    },
    "surbhi": {
        1: "Libra",      2: "Scorpio",   3: "Sagittarius", 4: "Capricorn",
        5: "Aquarius",   6: "Pisces",    7: "Aries",       8: "Taurus",
        9: "Gemini",    10: "Cancer",   11: "Leo",        12: "Virgo",
    },
    "sheridan": {
        1: "Taurus",     2: "Gemini",    3: "Cancer",    4: "Leo",
        5: "Virgo",      6: "Libra",     7: "Scorpio",   8: "Sagittarius",
        9: "Capricorn", 10: "Aquarius", 11: "Pisces",   12: "Aries",
    },
    "david": {
        1: "Virgo",      2: "Libra",     3: "Scorpio",   4: "Sagittarius",
        5: "Capricorn",  6: "Aquarius",  7: "Pisces",    8: "Aries",
        9: "Taurus",    10: "Gemini",   11: "Cancer",   12: "Leo",
    },
}


def _totals_from_fixture(chart_key: str) -> dict[str, float]:
    """Build shadbala_totals dict (title-case planet → virupa) from AstroSage fixture."""
    return {
        p.capitalize(): SHADBALA_FIXTURES[chart_key]["planets"][p]["shadbala_virupa"]
        for p in SHADBALA_FIXTURES[chart_key]["planets"]
    }


# Build Layer A parametrize cases at import time: (chart, house, expected_virupa).
# expected_virupa = lord's shadbala_virupa from AstroSage fixture — the oracle value.
_LAYER_A_CASES: list[tuple[str, int, float]] = []
for _chart in ("sulabh", "surbhi", "sheridan", "david"):
    _totals = _totals_from_fixture(_chart)
    for _house in range(1, 13):
        _sign = _HOUSE_SIGNS[_chart][_house]
        _lord = SIGN_LORDS[_sign]
        _LAYER_A_CASES.append((_chart, _house, _totals[_lord]))


# ── Layer A: Full 12-house validation, all 4 charts ──────────────────────────

@pytest.mark.parametrize("chart_name,house,expected", _LAYER_A_CASES)
def test_a_bhavadhipati_matches_astrosage_oracle(chart_name, house, expected):
    """Bhavadhipati Bala for each house equals the ruling planet's AstroSage Shadbala total."""
    result = compute_bhavadhipati_bala(
        _HOUSE_SIGNS[chart_name],
        _totals_from_fixture(chart_name),
    )
    assert abs(result[house] - expected) <= 0.5, (
        f"{chart_name} house {house} (sign={_HOUSE_SIGNS[chart_name][house]!r}): "
        f"got {result[house]}, expected {expected}"
    )


# ── Layer B: Same-lord pair returns identical Bhavadhipati Bala ──────────────

def test_b_same_lord_houses_return_identical_value():
    """Two houses with the same sign-lord return the same Bhavadhipati Bala (not just equal floats)."""
    # Sulabh: house 2 = Capricorn and house 3 = Aquarius — both Saturn-ruled.
    # Expected: both return Saturn's shadbala_virupa (423.16 from AstroSage fixture).
    result = compute_bhavadhipati_bala(
        _HOUSE_SIGNS["sulabh"],
        _totals_from_fixture("sulabh"),
    )
    assert result[2] == result[3], (
        f"Houses 2 and 3 both Saturn-ruled (Capricorn + Aquarius), "
        f"but got different values: {result[2]} vs {result[3]}"
    )
    # Confirm the shared value is Saturn's fixture total, not an arbitrary match.
    saturn_total = SHADBALA_FIXTURES["sulabh"]["planets"]["saturn"]["shadbala_virupa"]
    assert result[2] == saturn_total, (
        f"Expected Saturn's fixture total {saturn_total}, got {result[2]}"
    )


def test_b_jupiter_ruled_pair_david():
    """David's houses 4 and 7 (Sagittarius + Pisces, both Jupiter-ruled) return identical Bhavadhipati Bala."""
    result = compute_bhavadhipati_bala(
        _HOUSE_SIGNS["david"],
        _totals_from_fixture("david"),
    )
    assert result[4] == result[7], (
        f"Houses 4 (Sagittarius) and 7 (Pisces) both Jupiter-ruled, "
        f"but got {result[4]} vs {result[7]}"
    )
    jupiter_total = SHADBALA_FIXTURES["david"]["planets"]["jupiter"]["shadbala_virupa"]
    assert result[4] == jupiter_total


# ── Layer C: Error handling ───────────────────────────────────────────────────

_VALID_HOUSE_SIGNS = _HOUSE_SIGNS["sulabh"].copy()
_VALID_TOTALS = _totals_from_fixture("sulabh")

_LAYER_C_CASES = [
    pytest.param(
        {k: v for k, v in _VALID_HOUSE_SIGNS.items() if k != 7},   # missing house 7
        _VALID_TOTALS,
        r"missing=\[7\]",   # error message says: missing=[7], extra=[]
        id="missing_house_7",
    ),
    pytest.param(
        {**_VALID_HOUSE_SIGNS, 13: "Aries"},                        # bogus key 13
        _VALID_TOTALS,
        "13",
        id="extra_key_13",
    ),
    pytest.param(
        {**_VALID_HOUSE_SIGNS, 5: "Ophiuchus"},                     # invalid sign
        _VALID_TOTALS,
        "Ophiuchus",
        id="invalid_sign_name",
    ),
    pytest.param(
        _VALID_HOUSE_SIGNS,
        {k: v for k, v in _VALID_TOTALS.items() if k != "Jupiter"}, # lord missing (house 1=Sagittarius→Jupiter)
        "Jupiter",
        id="missing_lord_jupiter",
    ),
]


@pytest.mark.parametrize("house_signs,shadbala_totals,expected_fragment", _LAYER_C_CASES)
def test_c_raises_valueerror_naming_the_problem(house_signs, shadbala_totals, expected_fragment):
    """ValueError names the specific problem (which house, sign, or planet is missing)."""
    with pytest.raises(ValueError, match=expected_fragment):
        compute_bhavadhipati_bala(house_signs, shadbala_totals)


# ── Layer D: Output shape ─────────────────────────────────────────────────────

@pytest.mark.parametrize("chart_name", ["sulabh", "surbhi", "sheridan", "david"])
def test_d_output_has_exactly_keys_1_to_12_all_float(chart_name):
    """Returned dict has exactly keys 1-12 and all values are floats."""
    result = compute_bhavadhipati_bala(
        _HOUSE_SIGNS[chart_name],
        _totals_from_fixture(chart_name),
    )
    assert set(result.keys()) == set(range(1, 13)), (
        f"{chart_name}: expected keys 1-12, got {sorted(result.keys())}"
    )
    for house, val in result.items():
        assert isinstance(val, float), (
            f"{chart_name} house {house}: value {val!r} is {type(val).__name__}, expected float"
        )
