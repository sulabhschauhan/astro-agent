"""Tests for agent/astro/chart_facts.py -- the Path B chart_facts adapter.

The load-bearing test is test_real_sulabh_chart_round_trips_through_payload_builder:
it runs a REAL calculate_chart() and feeds the adapter's output straight into
payload_builder.parse_lord_house_map. Everything else is edge-case guarding.
"""
from __future__ import annotations

import copy

import pytest

from agent.astro import chart_facts as CF
from agent.astro import payload_builder as PB
from agent.chart_calculator import calculate_chart


# Same birth data the rest of the suite uses for Sulabh
# (tests/calculations/helpers/test_ephemeris.py:39, tests/test_yogini_routing.py:147).
_SULABH = ("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")
_DAVID = ("David", "19 Jan 1976", "22:00", "London, UK")


def _synthetic_chart(rows=None, ascendant="Sagittarius", planets=None):
    """Minimal well-formed calculate_chart()-shaped dict, for edge cases."""
    if rows is None:
        rows = [{"house": h, "sign": "X", "lord": "Y", "lord_in_house": ((h + 3) % 12) + 1}
                for h in range(1, 13)]
    chart = {"house_lord_mapping": rows, "lagna_chart": {"ascendant": ascendant}}
    if planets is not None:
        chart["planetary_positions"] = planets
    return chart


_GOOD_PLANETS = {
    "Sun": {"house": 4, "sign": "Pisces", "dignity": "Neutral", "retrograde": False,
            "longitude": 352.5},
    "Rahu": {"house": 3, "sign": "Aquarius", "dignity": "Neutral", "retrograde": True,
             "longitude": 310.1},
}


# ── planet positions (S129) ────────────────────────────────────────────────

def test_planet_positions_restate_house_and_sign_only():
    facts = CF.build_chart_facts(_synthetic_chart(planets=_GOOD_PLANETS))
    assert facts["planet_positions"] == {
        "Sun": {"house": 4, "sign": "Pisces"},
        "Rahu": {"house": 3, "sign": "Aquarius"},
    }


def test_longitude_retrograde_and_contested_dignity_are_not_restated():
    """S130 SPLIT dignity: Exalted/Debilitated/Own Sign ARE now restated (fixed
    S21 PVR Table 6 tables, tested before _FRIENDS), while Friendly/Inimical/
    Neutral are NOT (the contested tail). _GOOD_PLANETS carries "Neutral", so
    these positions still render as house+sign only. Longitude and retrograde
    stay excluded for their own recorded reasons -- see the module docstring.
    A future widening must justify itself, not slip in."""
    facts = CF.build_chart_facts(_synthetic_chart(planets=_GOOD_PLANETS))
    for pos in facts["planet_positions"].values():
        assert set(pos) == {"house", "sign"}


def test_planets_come_out_in_classical_graha_order_not_dict_order():
    scrambled = {"Ketu": {"house": 9, "sign": "Leo"},
                 "Moon": {"house": 12, "sign": "Scorpio"},
                 "Sun": {"house": 4, "sign": "Pisces"}}
    facts = CF.build_chart_facts(_synthetic_chart(planets=scrambled))
    assert list(facts["planet_positions"]) == ["Sun", "Moon", "Ketu"]


def test_real_chart_planet_positions_match_the_calculator():
    chart = calculate_chart(*_SULABH)
    facts = CF.build_chart_facts(chart)
    assert len(facts["planet_positions"]) == 9          # 7 grahas + 2 nodes
    for planet, pos in facts["planet_positions"].items():
        src = chart["planetary_positions"][planet]
        assert pos["house"] == src["house"]
        assert pos["sign"] == src["sign"]


def test_two_planets_sharing_a_house_are_both_kept():
    """Sulabh has Sun and Mercury both in the 4th -- a real, common case."""
    facts = CF.build_chart_facts(calculate_chart(*_SULABH))
    in_4 = [p for p, v in facts["planet_positions"].items() if v["house"] == 4]
    assert "Sun" in in_4 and "Mercury" in in_4


def test_absent_planetary_positions_yields_empty_not_an_error():
    """A chart_facts dict with no planet block is a complete absence, not a
    partial one -- the capability gate decides what that costs."""
    facts = CF.build_chart_facts(_synthetic_chart())
    assert facts["planet_positions"] == {}


def test_planetary_positions_not_a_dict_raises():
    with pytest.raises(CF.ChartFactsError, match="must be a dict"):
        CF.build_chart_facts(_synthetic_chart(planets=["Sun"]))


@pytest.mark.parametrize("bad", [
    {"Sun": {"sign": "Pisces"}},                       # no house
    {"Sun": {"house": 4}},                             # no sign
    {"Sun": {"house": 4, "sign": "   "}},              # blank sign
])
def test_partial_planet_row_raises_rather_than_half_reporting(bad):
    with pytest.raises(CF.ChartFactsError):
        CF.build_chart_facts(_synthetic_chart(planets=bad))


def test_planet_house_out_of_range_raises():
    with pytest.raises(CF.ChartFactsError, match="houses must lie in 1..12"):
        CF.build_chart_facts(_synthetic_chart(planets={"Sun": {"house": 13, "sign": "Aries"}}))


def test_unknown_planet_name_is_ignored_not_rendered():
    """Only the nine classical grahas are restated; anything else the
    calculator might add is not silently promoted into the fact block."""
    facts = CF.build_chart_facts(_synthetic_chart(
        planets={"Sun": {"house": 1, "sign": "Aries"},
                 "Chiron": {"house": 2, "sign": "Taurus"}}))
    assert list(facts["planet_positions"]) == ["Sun"]


# ── the real test ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("birth", [_SULABH, _DAVID], ids=["sulabh", "david"])
def test_real_chart_round_trips_through_payload_builder(birth):
    """A real chart must survive adapter -> parse_lord_house_map untouched."""
    chart = calculate_chart(*birth)

    facts = CF.build_chart_facts(chart)

    lord_house, asc = PB.parse_lord_house_map(facts)

    assert set(lord_house) == set(range(1, 13))
    assert all(1 <= v <= 12 for v in lord_house.values())
    assert asc == chart["lagna_chart"]["ascendant"]
    # The adapter restates; it must not invent. Every pair must be present in
    # the calculator's own output.
    source = {r["house"]: r["lord_in_house"] for r in chart["house_lord_mapping"]}
    assert lord_house == source


def test_real_chart_input_is_not_mutated():
    chart = calculate_chart(*_SULABH)
    before = copy.deepcopy(chart)
    CF.build_chart_facts(chart)
    assert chart == before


# ── shape guards ───────────────────────────────────────────────────────────

def test_returns_exactly_the_expected_keys():
    """S130 widened this to five keys. `navamsa` is the exception -- it is added
    ONLY when the caller supplies a D9 chart, because composition is the caller's
    job (see _read_navamsa) and an empty key would misreport an honest absence."""
    facts = CF.build_chart_facts(_synthetic_chart())
    assert set(facts) == {"lord_house_map", "ascendant_sign", "planet_positions",
                          "house_lords", "aspects"}


def test_ascendant_is_stripped():
    facts = CF.build_chart_facts(_synthetic_chart(ascendant="  Leo  "))
    assert facts["ascendant_sign"] == "Leo"


# ── raise-cases: each must name the offending field ────────────────────────

def test_non_dict_chart_raises():
    with pytest.raises(CF.ChartFactsError, match="calculate_chart"):
        CF.build_chart_facts(["not", "a", "dict"])


def test_missing_house_lord_mapping_raises():
    with pytest.raises(CF.ChartFactsError, match="house_lord_mapping"):
        CF.build_chart_facts({"lagna_chart": {"ascendant": "Leo"}})


def test_house_lord_mapping_not_a_list_raises():
    chart = _synthetic_chart()
    chart["house_lord_mapping"] = {"1": 5}
    with pytest.raises(CF.ChartFactsError, match="must be a list"):
        CF.build_chart_facts(chart)


def test_short_mapping_raises_naming_the_count():
    chart = _synthetic_chart()
    chart["house_lord_mapping"] = chart["house_lord_mapping"][:11]
    with pytest.raises(CF.ChartFactsError, match="11 entries, expected 12"):
        CF.build_chart_facts(chart)


def test_row_not_a_dict_raises_with_index():
    chart = _synthetic_chart()
    chart["house_lord_mapping"][4] = "nope"
    with pytest.raises(CF.ChartFactsError, match=r"\[4\]"):
        CF.build_chart_facts(chart)


def test_duplicate_house_raises():
    chart = _synthetic_chart()
    chart["house_lord_mapping"][5]["house"] = 1
    with pytest.raises(CF.ChartFactsError, match="house 1 more than once"):
        CF.build_chart_facts(chart)


def test_house_number_out_of_range_raises():
    chart = _synthetic_chart()
    chart["house_lord_mapping"][0]["house"] = 13
    with pytest.raises(CF.ChartFactsError, match="must lie in 1..12"):
        CF.build_chart_facts(chart)


def test_null_lord_in_house_raises_naming_every_affected_house():
    chart = _synthetic_chart()
    chart["house_lord_mapping"][2]["lord_in_house"] = None
    chart["house_lord_mapping"][7]["lord_in_house"] = None
    with pytest.raises(CF.ChartFactsError, match=r"house\(s\) \[3, 8\]"):
        CF.build_chart_facts(chart)


def test_placement_out_of_range_raises():
    chart = _synthetic_chart()
    chart["house_lord_mapping"][0]["lord_in_house"] = 14
    with pytest.raises(CF.ChartFactsError, match="placed in house 14"):
        CF.build_chart_facts(chart)


def test_non_integer_house_raises_naming_the_field():
    chart = _synthetic_chart()
    chart["house_lord_mapping"][3]["house"] = "fourth"
    with pytest.raises(CF.ChartFactsError, match="not an integer"):
        CF.build_chart_facts(chart)


def test_bool_house_is_rejected_not_coerced_to_one():
    chart = _synthetic_chart()
    chart["house_lord_mapping"][0]["house"] = True
    with pytest.raises(CF.ChartFactsError, match="is a bool"):
        CF.build_chart_facts(chart)


def test_missing_lagna_chart_raises():
    chart = _synthetic_chart()
    del chart["lagna_chart"]
    with pytest.raises(CF.ChartFactsError, match="lagna_chart"):
        CF.build_chart_facts(chart)


def test_lagna_chart_not_a_dict_raises():
    chart = _synthetic_chart()
    chart["lagna_chart"] = "Sagittarius"
    with pytest.raises(CF.ChartFactsError, match="must be a dict"):
        CF.build_chart_facts(chart)


@pytest.mark.parametrize("bad", [None, "", "   ", 7])
def test_blank_or_non_string_ascendant_raises(bad):
    chart = _synthetic_chart()
    chart["lagna_chart"]["ascendant"] = bad
    with pytest.raises(CF.ChartFactsError, match="missing or blank"):
        CF.build_chart_facts(chart)


# ── the adapter must not smuggle in astrology ──────────────────────────────

def test_module_imports_no_calculation_dependency():
    """RESTATE-DON'T-COMPUTE guard: this module must never grow an ephemeris,
    sign-table or lord-table IMPORT.

    Checks real import statements via AST, not raw text -- the docstring
    legitimately names chart_calculator as the source contract, and a
    substring scan would flag that.
    """
    import ast
    import inspect

    banned = ("swisseph", "chart_calculator", "agent.calculations")
    tree = ast.parse(inspect.getsource(CF))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
            imported += [f"{node.module}.{a.name}" for a in node.names]

    for name in imported:
        for b in banned:
            assert b not in name, (
                f"chart_facts.py imports {name!r} -- it must restate, not compute. "
                "A change needing a calculation belongs in the calculator."
            )
