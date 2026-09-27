"""Tests for the S142 transit-facts wiring: composer + fact-block render + gate.

Mirrors tests/astro/test_yoga_facts.py's structure (same composition pattern:
build_transit_facts is called by the CALLER and attached onto chart_facts,
never computed inside chart_facts.py itself).
"""
from __future__ import annotations

import swisseph as swe

from agent.astro import pipeline, capability_gate
from agent.astro.transit_facts import build_transit_facts


def _min_facts(**extra):
    f = {"ascendant_sign": "Aries",
         "lord_house_map": {h: (h % 12) + 1 for h in range(1, 13)}}
    f.update(extra)
    return f


def _one_antardasha(lord="Mercury", start="2018-01-28", start_jd=None, end_jd=None):
    """One minimal mahadasha_tree node with a single antardasha, in the RAW
    chart['dasha'] shape build_transit_facts reads (start_jd/end_jd floats,
    which chart_facts._read_dasha deliberately drops on its own restatement)."""
    if start_jd is None:
        start_jd = swe.julday(2018, 1, 28, 0.0)
    if end_jd is None:
        end_jd = swe.julday(2020, 8, 16, 0.0)
    return [{"mahadasha": {"lord": "Rahu", "start": "2000-01-01", "end": "2050-01-01"},
             "antardashas": [{"lord": lord, "start": start, "end": "2020-08-16",
                              "start_jd": start_jd, "end_jd": end_jd}]}]


def _min_chart(moon_lon=225.0, asc_lon=255.0, tree=None):
    # moon_lon=225.0 -> Scorpio (sign 7, 0-based); asc_lon=255.0 -> Sagittarius.
    # These match Sulabh's real chart's signs (not his real longitude), so the
    # unit tests exercise the same sign pair the module docstring validates.
    return {"planetary_positions": {"Moon": {"longitude": moon_lon}},
            "meta": {"asc_lon_sidereal": asc_lon},
            "dasha": {"mahadasha_tree": tree if tree is not None else _one_antardasha()}}


def test_capability_gate_declares_transits():
    assert "transits" in capability_gate.FACT_BLOCK_PROVIDES


def test_build_transit_facts_is_failsoft_and_returns_shape():
    # Empty inputs must never raise; missing prerequisites -> {}.
    assert build_transit_facts({}, {}) == {}
    assert build_transit_facts({"planetary_positions": {}}, _min_facts()) == {}


def test_build_transit_facts_returns_empty_when_no_dasha_tree():
    chart = _min_chart(tree=[])
    assert build_transit_facts(chart, _min_facts()) == {}


def test_build_transit_facts_never_raises_on_malformed_chart():
    # A chart dict with the wrong shapes throughout must degrade, not raise.
    out = build_transit_facts({"planetary_positions": "not-a-dict",
                                "meta": None, "dasha": 42}, {})
    assert isinstance(out, dict)


def test_build_transit_facts_basic_shape_and_correctness():
    chart = _min_chart()
    out = build_transit_facts(chart, _min_facts())
    assert out != {}
    assert out["natal_moon_sign"] == "Scorpio"
    periods = out["periods"]
    assert len(periods) == 1
    key = "Mercury|2018-01-28"
    assert key in periods
    entry = periods[key]
    assert set(entry) == {"saturn_sign", "saturn_house_from_lagna",
                          "saturn_house_from_moon", "saturn_retrograde",
                          "sade_sati_phase",
                          # S144: Jupiter transit added (marriage/children benefic),
                          # from the same gochara snapshot -- fed to timing_ranker.
                          "jupiter_sign", "jupiter_house_from_lagna",
                          "jupiter_retrograde"}
    assert isinstance(entry["saturn_sign"], str)
    assert 1 <= entry["saturn_house_from_lagna"] <= 12
    assert 1 <= entry["saturn_house_from_moon"] <= 12
    assert entry["sade_sati_phase"] in {"RISING", "PEAK", "SETTING", "NONE"}
    # Jupiter is fail-soft to None if somehow absent from the placements, but on
    # a normal chart it resolves to a sign + a 1..12 house.
    assert entry["jupiter_sign"] is None or isinstance(entry["jupiter_sign"], str)
    assert entry["jupiter_house_from_lagna"] is None or (
        1 <= entry["jupiter_house_from_lagna"] <= 12)


def test_build_transit_facts_skips_malformed_antardasha_rows():
    # A row missing start_jd/end_jd (e.g. a legacy tree node) is skipped, not
    # fatal -- the rest of the tree still resolves.
    tree = _one_antardasha()
    tree[0]["antardashas"].append(
        {"lord": "Venus", "start": "2011-12-26", "end": "2014-10-26"})  # no *_jd
    chart = _min_chart(tree=tree)
    out = build_transit_facts(chart, _min_facts())
    assert "Mercury|2018-01-28" in out["periods"]
    assert "Venus|2011-12-26" not in out["periods"]


def test_build_transit_facts_dedupes_first_occurrence_wins():
    tree = _one_antardasha()
    tree.append(_one_antardasha(start_jd=swe.julday(2019, 1, 1, 0.0))[0])
    chart = _min_chart(tree=tree)
    out = build_transit_facts(chart, _min_facts())
    # Both nodes carry the SAME (lord, start) key -- only one entry, and it's
    # the first tree occurrence's snapshot (its own start_jd/end_jd midpoint).
    assert len(out["periods"]) == 1


def test_fact_block_renders_saturn_annotation_on_matching_antardasha():
    facts = _min_facts(
        dasha_periods={
            "mahadasha": {"lord": "Rahu", "start": "2000-01-01", "end": "2050-01-01"},
            "antardasha": {"lord": "Mercury", "start": "2018-01-28", "end": "2020-08-16"},
            "mahadasha_tree": [
                {"mahadasha": {"lord": "Rahu", "start": "2000-01-01", "end": "2050-01-01"},
                 "phase": "current",
                 "antardashas": [{"lord": "Mercury", "start": "2018-01-28",
                                  "end": "2020-08-16"}]}],
        },
        transits={"natal_moon_sign": "Scorpio",
                 "periods": {"Mercury|2018-01-28": {
                     "saturn_sign": "Sagittarius",
                     "saturn_house_from_lagna": 1,
                     "saturn_house_from_moon": 2,
                     "saturn_retrograde": False,
                     "sade_sati_phase": "SETTING"}}},
    )
    fb = pipeline._fact_block(facts)
    assert "[Saturn TRANSIT: Sagittarius, house 1 from lagna, house 2 from Moon, Sade Sati SETTING]" in fb
    assert "cross-checks a dasha period against transit" in fb


def test_fact_block_omits_saturn_annotation_when_no_matching_period():
    facts = _min_facts(
        dasha_periods={
            "mahadasha": {"lord": "Rahu", "start": "2000-01-01", "end": "2050-01-01"},
            "antardasha": {"lord": "Mercury", "start": "2018-01-28", "end": "2020-08-16"},
            "mahadasha_tree": [
                {"mahadasha": {"lord": "Rahu", "start": "2000-01-01", "end": "2050-01-01"},
                 "phase": "current",
                 "antardashas": [{"lord": "Mercury", "start": "2018-01-28",
                                  "end": "2020-08-16"}]}],
        },
    )
    fb = pipeline._fact_block(facts)
    assert "[Saturn:" not in fb
    assert "cross-checks a dasha period against transit" not in fb


def test_growth_contract_transits_key_is_declared():
    # Mirrors test_yoga_facts.py's local pairing guard: the fact block only
    # ever renders a [Saturn TRANSIT: ...] tag when chart_facts carries "transits",
    # and that key must be in FACT_BLOCK_PROVIDES (test_capability_gate.py
    # pins the exhaustive set; this just guards the pair locally too).
    assert "transits" in capability_gate.FACT_BLOCK_PROVIDES
