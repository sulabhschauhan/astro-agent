"""Tests for the point-1 Shadbala fact-block wiring: composer + render + gate."""
from __future__ import annotations

from agent.astro import pipeline, capability_gate
from agent.astro import shadbala_facts
from agent.astro.shadbala_facts import build_shadbala_facts

_FAKE = {
    "sun":     {"shadbala_rupa": 6.2, "ratio": 1.24, "rank": 2, "caveat": "CAV"},
    "moon":    {"shadbala_rupa": 7.8, "ratio": 1.30, "rank": 1, "caveat": "CAV"},
    "mars":    {"shadbala_rupa": 4.0, "ratio": 0.80, "rank": 7, "caveat": "CAV"},
    "mercury": {"shadbala_rupa": 7.1, "ratio": 1.01, "rank": 4, "caveat": "CAV"},
    "jupiter": {"shadbala_rupa": 6.6, "ratio": 1.02, "rank": 3, "caveat": "CAV"},
    "venus":   {"shadbala_rupa": 5.5, "ratio": 1.00, "rank": 5, "caveat": "CAV"},  # boundary
    "saturn":  {"shadbala_rupa": 4.6, "ratio": 0.92, "rank": 6, "caveat": "CAV"},
}


def _min_facts(**extra):
    f = {"ascendant_sign": "Aries",
         "lord_house_map": {h: (h % 12) + 1 for h in range(1, 13)}}
    f.update(extra)
    return f


def test_capability_gate_declares_shadbala():
    assert "shadbala" in capability_gate.FACT_BLOCK_PROVIDES


def test_build_shadbala_facts_shape(monkeypatch):
    monkeypatch.setattr(shadbala_facts, "compute_shadbala_totals", lambda c: dict(_FAKE))
    out = build_shadbala_facts({})
    assert set(out["planets"]) == {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
    assert out["strongest"] == "Moon" and out["weakest"] == "Mars"
    assert out["planets"]["Sun"]["meets_minimum"] is True
    assert out["planets"]["Venus"]["meets_minimum"] is True   # ratio 1.00 boundary
    assert out["planets"]["Mars"]["meets_minimum"] is False
    assert out["planets"]["Moon"]["rupa"] == 7.8
    assert out["caveat"] == "CAV"


def test_build_shadbala_facts_failsoft(monkeypatch):
    def _boom(c): raise RuntimeError("bad chart")
    monkeypatch.setattr(shadbala_facts, "compute_shadbala_totals", _boom)
    assert build_shadbala_facts({}) == {}


def test_build_shadbala_facts_rejects_partial(monkeypatch):
    monkeypatch.setattr(shadbala_facts, "compute_shadbala_totals", lambda c: {"sun": _FAKE["sun"]})
    assert build_shadbala_facts({}) == {}


def test_fact_block_renders_shadbala(monkeypatch):
    monkeypatch.setattr(shadbala_facts, "compute_shadbala_totals", lambda c: dict(_FAKE))
    facts = _min_facts(shadbala=build_shadbala_facts({}))
    fb = pipeline._fact_block(facts)
    assert "Planetary strength (Shadbala)" in fb
    assert "Strongest: Moon. Weakest: Mars." in fb
    assert "rank 1/7 (meets the BPHS minimum)" in fb   # Moon
    assert "rank 7/7 (below the BPHS minimum)" in fb   # Mars


def test_fact_block_no_shadbala_section_when_absent():
    assert "Planetary strength (Shadbala)" not in pipeline._fact_block(_min_facts())
