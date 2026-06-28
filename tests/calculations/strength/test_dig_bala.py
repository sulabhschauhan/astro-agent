"""Tests for agent/calculations/strength/dig_bala.py — P2.5.2.

Layer A: structural / formula unit tests, no ephemeris.
Layer B: AstroSage parity, Sulabh chart — all 7 planets (hardest case first).
Layer C: cross-chart spot-check, Surbhi Sun.

Geocoder monkeypatched by tests/conftest.py; all locations must be in
tests/fixtures/geocoded_locations.json.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # project root

import pytest

from agent.calculations.strength.dig_bala import _dig_score, compute_dig_bala
from tests.fixtures.shadbala_fixtures import SHADBALA_FIXTURES


# ── Layer A: structural / formula unit tests (no ephemeris) ──────────────────

class TestDigScore:
    def test_planet_at_cusp_is_sixty(self):
        assert _dig_score(45.0, 45.0) == pytest.approx(60.0)

    def test_planet_opposite_cusp_is_zero(self):
        # 180° opposite → arc=180 → (180-180)/3 = 0
        assert _dig_score(225.0, 45.0) == pytest.approx(0.0)

    def test_planet_ninety_from_cusp_is_thirty(self):
        assert _dig_score(135.0, 45.0) == pytest.approx(30.0)

    def test_wrap_359_cusp_1_uses_min_arc(self):
        # min arc = 2°, not 358°; dig = (180-2)/3 = 59.333…
        result = _dig_score(359.0, 1.0)
        assert result == pytest.approx((180.0 - 2.0) / 3.0, abs=1e-9)

    def test_wrap_1_cusp_359_symmetric(self):
        result = _dig_score(1.0, 359.0)
        assert result == pytest.approx((180.0 - 2.0) / 3.0, abs=1e-9)


# ── Layer B: AstroSage Sulabh parity, all 7 planets ─────────────────────────

_SULABH_PLANETS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]


@pytest.fixture(scope="module")
def sulabh_dig():
    from agent.chart_calculator import calculate_chart
    chart = calculate_chart("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")
    return compute_dig_bala(chart)


@pytest.mark.parametrize("planet", _SULABH_PLANETS)
def test_sulabh_dig_bala_parity(planet, sulabh_dig):
    expected = SHADBALA_FIXTURES["sulabh"]["planets"][planet]["dig"]
    assert sulabh_dig[planet]["dig"] == pytest.approx(expected, abs=0.5)


# ── Layer C: cross-chart spot-check, Surbhi Sun ──────────────────────────────

def test_surbhi_sun_dig_bala():
    from agent.chart_calculator import calculate_chart
    chart = calculate_chart("Surbhi", "11 Sep 1992", "10:30", "Patna, India")
    result = compute_dig_bala(chart)
    expected = SHADBALA_FIXTURES["surbhi"]["planets"]["sun"]["dig"]
    assert result["sun"]["dig"] == pytest.approx(expected, abs=0.5)
