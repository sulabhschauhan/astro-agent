"""Tests for the S133 yoga-facts wiring: composer + fact-block render + gate."""
from __future__ import annotations

from agent.astro import pipeline, capability_gate
from agent.astro.yoga_facts import build_yoga_facts


def _min_facts(**extra):
    f = {"ascendant_sign": "Aries",
         "lord_house_map": {h: (h % 12) + 1 for h in range(1, 13)}}
    f.update(extra)
    return f


def test_capability_gate_declares_yogas():
    assert "yogas" in capability_gate.FACT_BLOCK_PROVIDES


def test_fact_block_renders_fired_and_ruled_out():
    facts = _min_facts(yogas={
        "fired": [{"id": "harsha_yoga", "name": "Harsha Yoga",
                   "reason": "the 6th lord (Venus) is in the 6th"}],
        "ruled_out": [{"id": "gajakesari_yoga", "name": "Gajakesari Yoga",
                       "reason": "Jupiter is 6th from the Moon"}],
    })
    fb = pipeline._fact_block(facts)
    assert "Yogas PRESENT in the chart" in fb
    assert "Harsha Yoga -- the 6th lord (Venus) is in the 6th" in fb
    assert "Yogas CHECKED and NOT present" in fb
    assert "Gajakesari Yoga" in fb


def test_fact_block_has_no_yoga_section_when_absent():
    fb = pipeline._fact_block(_min_facts())
    assert "Yogas PRESENT" not in fb
    assert "Yogas CHECKED" not in fb


def test_growth_contract_every_rendered_class_has_a_gate_key():
    # The yoga section renders only when chart_facts carries "yogas", and
    # "yogas" must be declared in FACT_BLOCK_PROVIDES (the pin the real
    # test_capability_gate enforces). This guards the pair locally too.
    facts = _min_facts(yogas={"fired": [{"id": "x", "name": "X", "reason": "y"}],
                              "ruled_out": []})
    assert "Yogas PRESENT" in pipeline._fact_block(facts)
    assert "yogas" in capability_gate.FACT_BLOCK_PROVIDES


def test_build_yoga_facts_is_failsoft_and_returns_shape():
    # Empty inputs must never raise; the result always has the two lists.
    out = build_yoga_facts({}, {})
    assert isinstance(out, dict)
    assert "fired" in out and "ruled_out" in out
    assert isinstance(out["fired"], list) and isinstance(out["ruled_out"], list)


def test_build_yoga_facts_restates_mangal_and_kalsarpa():
    # S135: chart_calculator._calc_yogas bools are RESTATED as yoga rows (not recomputed),
    # one fired + one ruled_out, in the detector's {id, name, reason} shape.
    chart = {"yogas_doshas": {"mangal_dosha": True, "kalsarpa_yoga": False},
             "planetary_positions": {"Mars": {"house": 7}}}
    out = build_yoga_facts(chart, _min_facts())
    fired_ids = {y["id"] for y in out["fired"]}
    ruled_ids = {y["id"] for y in out["ruled_out"]}
    assert "mangal_dosha" in fired_ids
    assert "kalsarpa_yoga" in ruled_ids
    # restated, not recomputed: the reason carries the OBSERVED house
    mangal = next(y for y in out["fired"] if y["id"] == "mangal_dosha")
    assert "7" in mangal["reason"]


def test_build_yoga_facts_omits_calc_yogas_when_absent():
    # No yogas_doshas on the chart -> no mangal/kalsarpa rows (no-op restatement).
    out = build_yoga_facts({"planetary_positions": {}}, _min_facts())
    ids = {y["id"] for y in out["fired"]} | {y["id"] for y in out["ruled_out"]}
    assert "mangal_dosha" not in ids and "kalsarpa_yoga" not in ids
