"""Regression for Mudda (Varsha-Vimshottari) dasa (sub-engine E). Pins the
JHora-validated seed lords (2025/26/27, exact) and the proportional period model.
"""
import math

import pytest

from agent.calculations.annual.mudda import (
    VIMSHOTTARI_SEQUENCE,
    mudda_dasha,
    mudda_start_lord,
)

VISAKHA = 16  # Sulabh's Moon birth nakshatra (Ashwini=1)


def test_seed_lords_match_oracle():
    # completed years 37/38/39 at the 2025/26/27 praveshes
    assert mudda_start_lord(37, VISAKHA) == "Saturn"
    assert mudda_start_lord(38, VISAKHA) == "Mercury"
    assert mudda_start_lord(39, VISAKHA) == "Ketu"


def test_seed_steps_one_vimshottari_place_per_year():
    lords = [mudda_start_lord(y, VISAKHA) for y in (37, 38, 39)]
    idx = [VIMSHOTTARI_SEQUENCE.index(x) for x in lords]
    assert idx[1] == (idx[0] + 1) % 9
    assert idx[2] == (idx[1] + 1) % 9


def test_full_cycle_order_from_seed():
    order = [p["lord"] for p in mudda_dasha(37, VISAKHA, 0.0, 365.25)]
    assert order[0] == "Saturn"
    i = VIMSHOTTARI_SEQUENCE.index("Saturn")
    assert order == [VIMSHOTTARI_SEQUENCE[(i + k) % 9] for k in range(9)]


def test_periods_sum_to_cycle():
    ps = mudda_dasha(38, VISAKHA, 10.0, 375.25)
    assert math.isclose(sum(p["days"] for p in ps), 365.25, abs_tol=1e-6)


def test_intervals_are_contiguous():
    ps = mudda_dasha(39, VISAKHA, 100.0, 465.25)
    for a, b in zip(ps, ps[1:]):
        assert math.isclose(a["end_jd"], b["start_jd"], abs_tol=1e-9)


def test_bad_nakshatra_raises():
    with pytest.raises(ValueError):
        mudda_start_lord(37, 0)
    with pytest.raises(ValueError):
        mudda_start_lord(37, 28)


def test_non_positive_cycle_raises():
    with pytest.raises(ValueError):
        mudda_dasha(37, VISAKHA, 365.25, 0.0)
