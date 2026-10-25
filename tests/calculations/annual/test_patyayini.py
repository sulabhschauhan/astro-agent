"""Regression for Patyayini dasa (sub-engine E). Pins the JHora-validated order
(2025 + 2026, exact) and the period mechanic. No desktop oracle beyond order/dates.
"""
import math

import pytest

from agent.calculations.annual.patyayini import patyayini_dasha

# Annual D1 sidereal longitudes (deg) from the JHora oracle
# (data/default_user/jhora_sulabh_varshaphal.md).
L2025 = {"Sun": 352.5157, "Moon": 96.9617, "Mars": 91.2008, "Mercury": 332.6795,
         "Jupiter": 52.6177, "Venus": 331.3412, "Saturn": 330.9149, "Asc": 96.4857}
L2026 = {"Sun": 352.5157, "Moon": 222.4686, "Mars": 333.2313, "Mercury": 324.9168,
         "Jupiter": 81.9622, "Venus": 14.2392, "Saturn": 342.0167, "Asc": 181.3623}


def _order(longs):
    return [p["lord"] for p in patyayini_dasha(longs, 0.0, 365.25)]


def test_order_2025():
    assert _order(L2025) == ["Saturn", "Mars", "Venus", "Mercury",
                             "Asc", "Moon", "Sun", "Jupiter"]


def test_order_2026():
    assert _order(L2026) == ["Asc", "Mars", "Saturn", "Moon",
                             "Venus", "Jupiter", "Sun", "Mercury"]


def test_periods_sum_to_cycle():
    ps = patyayini_dasha(L2025, 100.0, 465.25)
    assert math.isclose(sum(p["days"] for p in ps), 365.25, abs_tol=1e-6)


def test_first_patyamsha_is_own_degree():
    ps = patyayini_dasha(L2025, 0.0, 365.25)
    # first body is Saturn at 330.9149 deg -> deg-in-sign 0.9149
    assert math.isclose(ps[0]["patyamsha_deg"], 330.9149 % 30, abs_tol=1e-9)


def test_intervals_are_contiguous():
    ps = patyayini_dasha(L2025, 50.0, 415.25)
    for a, b in zip(ps, ps[1:]):
        assert math.isclose(a["end_jd"], b["start_jd"], abs_tol=1e-9)


def test_missing_body_raises():
    bad = dict(L2025)
    del bad["Asc"]
    with pytest.raises(ValueError):
        patyayini_dasha(bad, 0.0, 365.25)


def test_non_positive_cycle_raises():
    with pytest.raises(ValueError):
        patyayini_dasha(L2025, 365.25, 0.0)
