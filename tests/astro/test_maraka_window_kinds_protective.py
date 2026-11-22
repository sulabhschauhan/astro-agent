"""tests/astro/test_maraka_window_kinds_protective.py
Real-Sulabh-chart guards (no model) for (A) risk_window "kinds" and
(B) facts["maraka"]["protective_factors"] -- S167 longevity build. PARAMETERS only.
"""
from __future__ import annotations

from datetime import datetime

import pytest

from agent.chart_calculator import calculate_chart
from agent.astro.static_facts import build_static_facts

_SULABH = ("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")
_KINDS = {"maraka", "randhra", "ayushkaraka"}


def _d(s):
    return datetime.strptime(s, "%d %b %Y")


@pytest.fixture(scope="module")
def maraka() -> dict:
    return build_static_facts(calculate_chart(*_SULABH)).get("maraka") or {}


def test_a_every_window_has_valid_non_empty_kinds(maraka):
    ws = maraka["risk_windows"]
    assert ws
    for w in ws:
        assert w["kinds"] and set(w["kinds"]) <= _KINDS, w


def test_b_seventh_lord_mercury_is_maraka_only(maraka):
    ws = [w for w in maraka["risk_windows"] if w["lord"] == "Mercury"]
    assert ws and all(w["kinds"] == ["maraka"] for w in ws)


def test_c_moon_window_2027_is_randhra_not_maraka(maraka):
    w0, w1 = datetime(2027, 7, 1), datetime(2028, 2, 29)
    ws = [w for w in maraka["risk_windows"] if w["lord"] == "Moon"
          and _d(w["start"]) <= w1 and _d(w["end"]) >= w0]
    assert ws, "no Moon window covers 2027-07..2028-02"
    assert all(w["kinds"] == ["randhra"] for w in ws), ws


def test_d_saturn_window_is_maraka_then_ayushkaraka(maraka):
    ws = [w for w in maraka["risk_windows"] if w["lord"] == "Saturn"]
    assert ws and all(w["kinds"] == ["maraka", "ayushkaraka"] for w in ws)


def test_e_protective_factors_populate(maraka):
    pf = maraka.get("protective_factors")
    assert isinstance(pf, dict) and pf
    assert pf["ayushkaraka"]["planet"] == "Saturn"
    assert isinstance(pf["ayushkaraka"]["shadbala"]["rupa"], float)
    assert pf["lagna"]["sign"] == "Sagittarius"
    assert isinstance(pf["lagna"]["benefic_aspects"], list)
    ll = pf["lagna_lord"]
    assert ll["planet"] == "Jupiter" and isinstance(ll["shadbala"]["rupa"], float)
    assert isinstance(ll["benefic_aspects"], list)
    assert pf["eighth_lord"]["planet"] == "Moon"
