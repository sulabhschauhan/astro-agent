"""Regression for Varsha Yogini dasa (sub-engine E). Pins the JHora-validated
seed (advance-nakshatra-by-years), cycle order, and period model (2025/26/27).
"""
import math

import pytest

from agent.calculations.annual.yogini import (
    YOGINIS,
    yogini_dasha,
    yogini_seed_index,
)

VISAKHA = 16
FRAC = 1.101 / 13.3333  # Visakha remaining at birth ~= 0.0826


def _order(completed):
    return [p["lord"] for p in yogini_dasha(VISAKHA, completed, FRAC, 0.0, 365.25)]


def test_seed_matches_oracle():
    assert YOGINIS[yogini_seed_index(VISAKHA, 37)][0] == "Bhadrika"   # Mercury
    assert YOGINIS[yogini_seed_index(VISAKHA, 38)][0] == "Ulka"       # Saturn
    assert YOGINIS[yogini_seed_index(VISAKHA, 39)][0] == "Bhramari"   # Mars


def test_order_2025():
    assert _order(37) == ["Mercury", "Saturn", "Venus", "Rahu",
                          "Moon", "Sun", "Jupiter", "Mars"]


def test_order_2026():
    assert _order(38) == ["Saturn", "Venus", "Rahu", "Moon",
                          "Sun", "Jupiter", "Mars", "Mercury"]


def test_order_2027():
    assert _order(39) == ["Mars", "Mercury", "Saturn", "Venus",
                          "Rahu", "Moon", "Sun", "Jupiter"]


def test_periods_sum_to_cycle():
    ps = yogini_dasha(VISAKHA, 37, FRAC, 100.0, 465.25)
    assert math.isclose(sum(p["days"] for p in ps), 365.25, abs_tol=1e-6)


def test_seed_straddles_pravesh():
    # the seed yogini begins before the pravesh by its elapsed fraction
    ps = yogini_dasha(VISAKHA, 37, FRAC, 1000.0, 1365.25)
    assert ps[0]["start_jd"] < 1000.0


def test_bad_inputs_raise():
    with pytest.raises(ValueError):
        yogini_seed_index(0, 37)
    with pytest.raises(ValueError):
        yogini_dasha(VISAKHA, 37, 0.0, 0.0, 365.25)      # fraction must be > 0
    with pytest.raises(ValueError):
        yogini_dasha(VISAKHA, 37, FRAC, 365.25, 0.0)     # non-positive cycle
