"""tests/astro/test_maraka_strength.py
Real-Sulabh-chart guard for facts["maraka"]["maraka_strength"] (S167 longevity build).
Mirrors test_fact_block_completeness.py: real calculate_chart -> build_static_facts,
NO model call. Asserts the strength PARAMETERS populate (not a silently-empty block);
it asserts no verdict/weight -- importance is corpus doctrine (S166 ruling).
"""
from __future__ import annotations

import pytest

from agent.chart_calculator import calculate_chart
from agent.astro.static_facts import build_static_facts

_SULABH = ("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")
_PARAM_KEYS = {
    "is_2nd_lord", "is_7th_lord", "is_8th_lord", "is_ayushkaraka",
    "natural_malefic", "shadbala", "afflicts_2", "afflicts_7",
    "benefic_save_present",
}
_BOOL_KEYS = _PARAM_KEYS - {"shadbala"}
_PHYSICAL = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}


@pytest.fixture(scope="module")
def strength() -> dict:
    facts = build_static_facts(calculate_chart(*_SULABH))
    return (facts.get("maraka") or {}).get("maraka_strength")


def test_a_block_exists_and_is_non_empty(strength):
    assert isinstance(strength, dict) and strength


def test_b_nine_param_keys_and_bool_flags(strength):
    for planet, p in strength.items():
        assert set(p) == _PARAM_KEYS, (planet, set(p) ^ _PARAM_KEYS)
        for k in _BOOL_KEYS:
            assert isinstance(p[k], bool), (planet, k, p[k])


def test_c_shadbala_read_through(strength):
    for planet, p in strength.items():
        sb = p["shadbala"]
        if planet in _PHYSICAL:
            assert sb is not None and isinstance(sb["rupa"], float), (planet, sb)
        else:  # Rahu / Ketu have no shadbala
            assert sb is None, (planet, sb)


def test_d_saturn_is_ayushkaraka_with_shadbala(strength):
    assert "Saturn" in strength, sorted(strength)
    sat = strength["Saturn"]
    assert sat["is_ayushkaraka"] is True
    assert sat["shadbala"] is not None


def test_e_protective_signal_populates_on_hardest_case(strength):
    assert any(
        p["benefic_save_present"] or (p["shadbala"] or {}).get("meets_minimum") is True
        for p in strength.values()
    ), "no maraka planet shows any protective/strength signal -- block silently empty?"
