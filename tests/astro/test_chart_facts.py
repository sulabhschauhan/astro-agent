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


# ── dasha restatement (S141) ───────────────────────────────────────────────

def _dasha_chart(dasha):
    """A synthetic calculate_chart()-shaped dict carrying a given `dasha` block."""
    chart = _synthetic_chart()
    if dasha is not None:
        chart["dasha"] = dasha
    return chart


_FULL_DASHA = {
    "current_mahadasha": {"lord": "Mercury", "start": "1 Aug 2008", "end": "1 Aug 2025",
                          "start_jd": 2454679.0, "end_jd": 2460889.0},
    "current_antardasha": {"lord": "Mercury", "start": "1 Aug 2008", "end": "29 Dec 2010"},
    "next_5_antardashas": [{"lord": "Ketu", "start": "29 Dec 2010", "end": "26 Dec 2011"},
                           {"lord": "Venus", "start": "26 Dec 2011", "end": "27 Oct 2014"}],
    "next_3_mahadashas": [{"lord": "Ketu", "start": "1 Aug 2025", "end": "1 Aug 2032"},
                          {"lord": "Venus", "start": "1 Aug 2032", "end": "1 Aug 2052"}],
    "past_mahadashas": [{"lord": "Jupiter", "start": "6 Apr 1988", "end": "1 Aug 1989"},
                        {"lord": "Rahu", "start": "1 Aug 1989", "end": "1 Aug 2008"}],
    # COMPLETE tree (S141 gap #2): full mahadashas each with their antardashas.
    "mahadasha_tree": [
        {"mahadasha": {"lord": "Mercury", "start": "1 Aug 2008", "end": "1 Aug 2025"},
         "antardashas": [{"lord": "Mercury", "start": "1 Aug 2008", "end": "29 Dec 2010"},
                         {"lord": "Sun", "start": "28 Oct 2014", "end": "4 Sep 2015"}],
         "phase": "past"},
        {"mahadasha": {"lord": "Ketu", "start": "1 Aug 2025", "end": "1 Aug 2032"},
         "antardashas": [{"lord": "Ketu", "start": "1 Aug 2025", "end": "29 Dec 2025"}],
         "phase": "current"}],
    # Both suppressed on Path B. Sentinel start/end so the suppression proof can
    # test for their absence even though Saturn/Moon are legitimate tree lords.
    "current_pratyantar": {"lord": "Saturn", "start": "PT_SENTINEL", "end": "PT_SENTINEL"},
    "next_5_pratyantars": [{"lord": "Moon", "start": "PT_SENTINEL", "end": "PT_SENTINEL"}],
}


def test_dasha_is_restated_md_and_ad_with_pratyantar_suppressed():
    facts = CF.build_chart_facts(_dasha_chart(_FULL_DASHA))
    d = facts["dasha_periods"]
    assert d["mahadasha"] == {"lord": "Mercury", "start": "1 Aug 2008", "end": "1 Aug 2025"}
    assert d["antardasha"]["lord"] == "Mercury"
    assert [p["lord"] for p in d["past_mahadashas"]] == ["Jupiter", "Rahu"]   # S141
    assert [p["lord"] for p in d["upcoming_mahadashas"]] == ["Ketu", "Venus"]
    assert [p["lord"] for p in d["upcoming_antardashas"]] == ["Ketu", "Venus"]
    # COMPLETE tree (gap #2): the past Mercury MD carries its own sub-periods --
    # incl. Mercury->Sun (2014-15), the marriage-relevant one the pilot had to
    # invent because it was absent. Now it is a fact to READ.
    tree = d["mahadasha_tree"]
    assert [n["mahadasha"]["lord"] for n in tree] == ["Mercury", "Ketu"]
    assert tree[0]["phase"] == "past" and tree[1]["phase"] == "current"
    merc_ads = [a["lord"] for a in tree[0]["antardashas"]]
    assert merc_ads == ["Mercury", "Sun"]
    assert any(a["lord"] == "Sun" and a["start"] == "28 Oct 2014"
               for a in tree[0]["antardashas"])
    assert "drift" in d["drift_note"].lower() or "+/-37" in d["drift_note"]
    # PRATYANTAR SUPPRESSION (S129 lock) + no JD floats leak into the block.
    blob = repr(d)
    assert "pratyantar" not in blob.lower(), "pratyantar leaked into the fact class"
    assert "PT_SENTINEL" not in blob, "suppressed pratyantar data leaked into the block"
    assert "start_jd" not in blob and "_jd" not in blob, "raw JD floats leaked past the drift note"
    assert set(d["mahadasha"]) == {"lord", "start", "end"}


def test_dasha_is_fail_soft_on_missing_or_error_or_partial():
    assert "dasha_periods" not in CF.build_chart_facts(_dasha_chart(None))          # no dasha key
    assert "dasha_periods" not in CF.build_chart_facts(_dasha_chart({}))            # empty
    assert "dasha_periods" not in CF.build_chart_facts(
        _dasha_chart({"error": "Current mahadasha not found; verify birth data"}))  # error chart
    assert "dasha_periods" not in CF.build_chart_facts(
        _dasha_chart({"current_mahadasha": {"lord": "", "start": "x", "end": "y"}}))  # blank lord


def test_dasha_md_only_chart_omits_the_antardasha_key():
    facts = CF.build_chart_facts(_dasha_chart({
        "current_mahadasha": {"lord": "Sun", "start": "s", "end": "e"},
        "current_antardasha": None, "next_5_antardashas": [], "next_3_mahadashas": []}))
    d = facts["dasha_periods"]
    assert "antardasha" not in d          # absent, not a None-valued key
    assert d["upcoming_mahadashas"] == [] and d["upcoming_antardashas"] == []
    assert d["past_mahadashas"] == []     # absent past key -> empty, not missing
    assert d["mahadasha_tree"] == []      # absent tree -> empty, not missing


def test_real_sulabh_chart_surfaces_the_current_and_past_dasha():
    """End-to-end against the real engine: calculate_chart() -> build_chart_facts.
    Anchored to the oracle MD table (sulabh.md section 5e): Mercury MD ends
    1 Aug 2025, Ketu MD runs to 1 Aug 2032, so the current major period is Ketu.
    The 7th lord Mercury's OWN period (2008-2025) is now in past_mahadashas --
    that is the marriage-relevant dasha a retrospective question needs (S141).
    VALID until Aug 2032; revisit the expected lord after that."""
    facts = CF.build_chart_facts(calculate_chart(*_SULABH))
    d = facts["dasha_periods"]
    assert d["mahadasha"]["lord"] == "Ketu"
    assert "antardasha" in d              # a real chart always has a current sub-period
    assert d["drift_note"]
    # the retrospective fix: Mercury's elapsed period is present and dated
    past_lords = [p["lord"] for p in d["past_mahadashas"]]
    assert "Mercury" in past_lords, f"7th-lord Mercury's past MD missing: {past_lords}"
    assert any(p["lord"] == "Mercury" and "2025" in p["end"] for p in d["past_mahadashas"])
    # gap #2: the tree carries Mercury's OWN antardashas, incl. a Sun sub-period
    # in the mid-2010s -- the exact thing the pilot fabricated because it was
    # absent. It is now a fact the interpreter reads, not computes.
    merc = next((n for n in d["mahadasha_tree"] if n["mahadasha"]["lord"] == "Mercury"), None)
    assert merc is not None and merc["phase"] == "past"
    merc_ad_lords = [a["lord"] for a in merc["antardashas"]]
    assert merc_ad_lords == ["Mercury", "Ketu", "Venus", "Sun", "Moon",
                             "Mars", "Rahu", "Jupiter", "Saturn"], merc_ad_lords
    assert any(a["lord"] == "Sun" and "2014" in a["start"] for a in merc["antardashas"])
    # the suppression holds on the real block too
    assert "pratyantar" not in repr(d).lower()


def test_real_dasha_output_now_carries_past_and_tree():
    """S127 characterization on _calc_dasha's own output: it STILL returns every
    pre-S141 key AND the additive past_mahadashas + mahadasha_tree, chronological.
    Guards the chart_calculator contract the fact class rests on."""
    da = calculate_chart(*_SULABH)["dasha"]
    for k in ("current_mahadasha", "current_antardasha", "next_5_antardashas",
              "next_3_mahadashas", "past_mahadashas", "mahadasha_tree"):
        assert k in da, f"dasha output lost key {k!r}"
    assert da["past_mahadashas"], "past list is empty for a mid-life chart"
    # each past MD ends no later than the current MD begins (chronological, no overlap)
    assert da["past_mahadashas"][-1]["end_jd"] <= da["current_mahadasha"]["start_jd"] + 1e-6
    # tree: every full node carries nine antardashas; the birth node (index 0) is
    # window-only; exactly one node is the current phase.
    tree = da["mahadasha_tree"]
    assert tree[0]["antardashas"] == [], "birth (balance) MD must not expand ADs"
    assert all(len(n["antardashas"]) == 9 for n in tree[1:]), "full MDs need nine ADs each"
    assert sum(1 for n in tree if n["phase"] == "current") == 1
    # the current node's ADs match the separately-computed current_antardasha
    cur = next(n for n in tree if n["phase"] == "current")
    assert cur["mahadasha"]["lord"] == da["current_mahadasha"]["lord"]
    assert da["current_antardasha"]["lord"] in [a["lord"] for a in cur["antardashas"]]
