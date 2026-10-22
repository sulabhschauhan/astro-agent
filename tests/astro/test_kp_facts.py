"""Tests for the S143 KP-facts wiring: composer + fact-block render + gate.

Mirrors tests/astro/test_transit_facts.py's structure (same composition
pattern: build_kp_facts is called by the CALLER and attached onto
chart_facts, never computed inside chart_facts.py itself). The sub-lord
table's own logic is tested separately in
tests/calculations/kp/test_sub_lords.py; the AstroSage oracle cross-check is
in tests/calculations/kp/test_kp_oracle_validation.py. This file only tests
the composer's shape/fail-soft behaviour and the fact-block render/gate.
"""
from __future__ import annotations

from agent.astro import pipeline, capability_gate
from agent.astro.kp_facts import build_kp_facts


def _min_facts(**extra):
    f = {"ascendant_sign": "Sagittarius",
         "lord_house_map": {h: (h % 12) + 1 for h in range(1, 13)}}
    f.update(extra)
    return f


def _min_chart(cusps=None):
    if cusps is None:
        # 12 arbitrary but valid sidereal degrees, one per house.
        cusps = [i * 30.0 for i in range(12)]
    return {"meta": {"house_cusps_kp_sidereal": cusps}}


def test_capability_gate_declares_kp():
    assert "kp_seventh_cusp_sub_lord" in capability_gate.FACT_BLOCK_PROVIDES
    assert "kp_cusp_sub_lords" in capability_gate.FACT_BLOCK_PROVIDES  # S153 all-12


def test_build_kp_facts_is_failsoft_and_returns_shape():
    # Empty/malformed inputs must never raise; missing prerequisites -> {}.
    assert build_kp_facts({}) == {}
    assert build_kp_facts({"meta": {}}) == {}
    assert build_kp_facts({"meta": {"house_cusps_kp_sidereal": [1.0] * 11}}) == {}
    assert build_kp_facts({"meta": None}) == {}


def test_build_kp_facts_never_raises_on_malformed_chart():
    out = build_kp_facts({"meta": "not-a-dict"})
    assert isinstance(out, dict)
    out = build_kp_facts({"meta": {"house_cusps_kp_sidereal": "not-a-list"}})
    assert isinstance(out, dict)


def test_build_kp_facts_reads_house_7_specifically():
    # House 7 is index 6 -- confirm it's the 7th cusp, not the 1st or 8th.
    cusps = [i * 30.0 for i in range(12)]  # house h -> h*30 - 30 deg (0-indexed i)
    out = build_kp_facts(_min_chart(cusps))
    from agent.calculations.kp.sub_lords import sub_lord_for_longitude
    assert out["seventh_cusp_sub_lord"] == sub_lord_for_longitude(cusps[6])
    assert out["cusp_sub_lords"][7] == sub_lord_for_longitude(cusps[6])


def test_build_kp_facts_basic_shape():
    out = build_kp_facts(_min_chart())
    assert set(out) == {"seventh_cusp_sub_lord", "cusp_sub_lords"}  # S153 widened
    assert isinstance(out["seventh_cusp_sub_lord"], str)


def test_build_kp_facts_surfaces_all_twelve_cusps():
    # S153: all 12 cusp sub-lords, a pure restate of the already-validated
    # engine (sub_lord_for_longitude) over every house cusp; the 7th stays
    # consistent with its dedicated key.
    from agent.calculations.kp.sub_lords import sub_lord_for_longitude
    cusps = [i * 30.0 for i in range(12)]
    out = build_kp_facts(_min_chart(cusps))
    csl = out["cusp_sub_lords"]
    assert set(csl) == set(range(1, 13))                      # every house 1..12
    assert all(isinstance(v, str) for v in csl.values())      # planet names
    assert csl[7] == out["seventh_cusp_sub_lord"]             # 7th consistent
    for h in range(1, 13):
        assert csl[h] == sub_lord_for_longitude(cusps[h - 1])  # restate, no new astrology


def test_fact_block_renders_kp_line_when_facts_carry_it():
    facts = _min_facts(kp={"seventh_cusp_sub_lord": "Saturn"})
    fb = pipeline._fact_block(facts)
    assert "KP (Krishnamurti Paddhati) -- NATAL fact" in fb
    assert "the 7th house cusp's sub-lord is Saturn." in fb
    # S143-followup: the fact must explicitly disclaim a same-name-planet
    # transit-tag coincidence as corroboration -- this is the actual fix for
    # the measured false-corroboration defect (Mercury-Venus getting a bogus
    # "KP corroboration" from an unrelated transiting Saturn).
    assert "NOT itself" in fb or "NOT a transiting position" in fb


def test_fact_block_renders_all_twelve_kp_line():
    facts = _min_facts(kp={
        "seventh_cusp_sub_lord": "Saturn",
        "cusp_sub_lords": {**{h: "Venus" for h in range(1, 13)}, 7: "Saturn", 10: "Mars"},
    })
    fb = pipeline._fact_block(facts)
    assert "KP cusp sub-lords (Krishnamurti Paddhati)" in fb
    assert "7 (marriage/partnership): Saturn" in fb
    assert "10 (career/status): Mars" in fb


def test_fact_block_omits_kp_line_when_absent():
    facts = _min_facts()
    fb = pipeline._fact_block(facts)
    assert "KP (Krishnamurti" not in fb


def test_fact_block_omits_kp_line_on_empty_kp_dict():
    # build_kp_facts() returns {} on unsupported input -- confirm the render
    # guard treats that the same as "kp" being entirely absent.
    facts = _min_facts(kp={})
    fb = pipeline._fact_block(facts)
    assert "KP (Krishnamurti" not in fb


def test_growth_contract_kp_key_is_declared():
    # Mirrors test_transit_facts.py's local pairing guard: the fact block only
    # ever renders the KP line when chart_facts carries "kp", and that key
    # must be in FACT_BLOCK_PROVIDES (test_capability_gate.py pins the
    # exhaustive set; this just guards the pair locally too).
    assert "kp_seventh_cusp_sub_lord" in capability_gate.FACT_BLOCK_PROVIDES
    assert "kp_cusp_sub_lords" in capability_gate.FACT_BLOCK_PROVIDES
