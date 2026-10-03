"""Tests for the point-2 divisional fact-block wiring: composer + render + gate."""
from __future__ import annotations

from agent.astro import pipeline, capability_gate
from agent.astro import divisional_facts
from agent.astro.divisional_facts import build_divisional_facts

_P = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
_NAMES = {"D10": "Dasamsa", "D7": "Saptamsa", "D2": "Hora", "D30": "Trimsamsa",
          "D12": "Dwadasamsa", "D3": "Drekkana", "D24": "Chaturvimsamsa"}


class _PL:
    def __init__(s, sign, house): s.varga_sign = sign; s.varga_house = house


class _VC:
    def __init__(s, code, lagna):
        s.varga = code; s.name = _NAMES[code]; s.lagna_sign = lagna; s.ayanamsa = 0.0
        s.placements = {p: _PL("Cancer", (i % 12) + 1) for i, p in enumerate(_P)}


def _fake_compute(jd, asc, code):
    if code == "D30":
        raise RuntimeError("one varga fails")   # exercise per-varga fail-soft
    return _VC(code, "Cancer")


def _patch(mp):
    mp.setattr(divisional_facts, "compute_varga", _fake_compute)


def _chart():
    return {"meta": {"jd_ut": 2447258.0, "asc_lon_sidereal": 262.7}}


def _min_facts(**extra):
    f = {"ascendant_sign": "Aries",
         "lord_house_map": {h: (h % 12) + 1 for h in range(1, 13)}}
    f.update(extra)
    return f


def test_capability_gate_declares_divisional():
    assert "divisional" in capability_gate.FACT_BLOCK_PROVIDES


def test_build_surfaces_six_when_one_fails(monkeypatch):
    _patch(monkeypatch)
    out = build_divisional_facts(_chart())
    assert "D30" not in out and "D10" in out        # per-varga fail-soft
    assert out["D10"]["domain"] == "career"
    assert len(out["D10"]["placements"]) == 9
    assert set(out["D10"]["placements"]["Sun"]) == {"sign", "house"}


def test_build_requires_meta():
    assert build_divisional_facts({}) == {}
    assert build_divisional_facts(None) == {}


def test_fact_block_renders(monkeypatch):
    _patch(monkeypatch)
    facts = _min_facts(divisional=build_divisional_facts(_chart()))
    fb = pipeline._fact_block(facts)
    assert "Divisional charts (vargas)" in fb
    assert "Dasamsa (D10, career)" in fb
    assert "Saptamsa (D7, children)" in fb
    assert "Trimsamsa (D30" not in fb               # the failed varga isn't rendered


def test_fact_block_absent_when_missing():
    assert "Divisional charts (vargas)" not in pipeline._fact_block(_min_facts())
