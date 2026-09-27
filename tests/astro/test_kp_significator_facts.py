"""
tests/astro/test_kp_significator_facts.py
Contract test for agent.astro.kp_significator_facts.build_kp_significator_facts
after S144 (source swapped from PDF-parse to ephemeris-compute).

Guards the SHAPE pipeline._fact_block consumes ({"planet_significations":
{planet: (ascending house ints)}}) and the fail-soft posture, plus the
marriage discriminator survives the flatten (Rahu reaches 2 & 7, Venus only
11). Engine correctness itself is covered by
tests/calculations/kp/test_significator_engine.py; this only checks the
composer's flatten + fail-soft.
"""
from __future__ import annotations

from agent.astro.kp_significator_facts import build_kp_significator_facts

# Same Sulabh reference chart fixture as the engine test.
_PLANET_LON = {
    "Sun": 352.5203, "Moon": 212.2289, "Mars": 275.5756, "Mercury": 337.8761,
    "Jupiter": 12.5608, "Venus": 38.3278, "Saturn": 248.8433,
    "Rahu": 328.3983, "Ketu": 148.3983,
}
_CUSPS = [249.9886, 279.9886, 314.4292, 348.8697, 18.8697, 44.4292,
          69.9886, 99.9886, 134.4292, 168.8697, 198.8697, 224.4292]


def _chart() -> dict:
    return {
        "planetary_positions": {p: {"longitude": l} for p, l in _PLANET_LON.items()},
        "meta": {"house_cusps_kp_sidereal": list(_CUSPS)},
    }


def test_returns_planet_significations_shape():
    out = build_kp_significator_facts(_chart())
    assert set(out) == {"planet_significations"}
    table = out["planet_significations"]
    assert set(table) == set(_PLANET_LON)                 # all 9 planets
    for houses in table.values():
        assert isinstance(houses, tuple)
        assert all(isinstance(h, int) for h in houses)
        assert list(houses) == sorted(houses)             # ascending, pipeline joins in order


def test_none_chart_is_fail_soft():
    assert build_kp_significator_facts(None) == {}
    assert build_kp_significator_facts({}) == {}


def test_malformed_chart_never_raises():
    # Missing meta -> engine raises -> composer swallows to an {"error": ...}.
    out = build_kp_significator_facts({"planetary_positions": {}})
    assert "planet_significations" not in out


def test_marriage_discriminator_survives_flatten():
    table = build_kp_significator_facts(_chart())["planet_significations"]
    triad = {2, 7, 11}
    assert triad & set(table["Rahu"]) == {2, 7}    # antardasha lord reaches spouse+family
    assert triad & set(table["Venus"]) == {11}     # naive karaka pick: weakest house only
    assert triad & set(table["Mercury"]) == {2, 7}  # mahadasha lord = 7th lord
