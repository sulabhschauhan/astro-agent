"""Tests for the point-1 Ashtakavarga fact-block wiring: composer + render + gate."""
from __future__ import annotations

from agent.astro import pipeline, capability_gate
from agent.astro import ashtakavarga_facts
from agent.astro.ashtakavarga_facts import build_ashtakavarga_facts

_SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
          "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
_SEVEN = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
_TOT = {"Sun": 48, "Moon": 49, "Mars": 39, "Mercury": 54, "Jupiter": 56,
        "Venus": 52, "Saturn": 39}  # sum 337


def _chart(asc="Sagittarius"):
    a = _SIGNS.index(asc)
    hlm = [{"house": h, "sign": _SIGNS[(a + h - 1) % 12]} for h in range(1, 13)]
    pp = {p: {"sign": _SIGNS[i % 12], "house": 1}
          for i, p in enumerate(list(_SEVEN) + ["Rahu", "Ketu"])}
    return {"planetary_positions": pp, "house_lord_mapping": hlm}


def _fake_bav(placements):
    out = {}
    for p in _SEVEN:
        base, rem = divmod(_TOT[p], 12)
        d = {s: base for s in _SIGNS}
        for i in range(rem):
            d[_SIGNS[i]] += 1
        out[p] = d
    out["Lagna"] = {s: 0 for s in _SIGNS}
    return out


def _fake_sav(bav):
    return {s: sum(bav[p][s] for p in _SEVEN) for s in _SIGNS}


def _patch(mp):
    mp.setattr(ashtakavarga_facts, "compute_bav", _fake_bav)
    mp.setattr(ashtakavarga_facts, "compute_sav", _fake_sav)


def _min_facts(**extra):
    f = {"ascendant_sign": "Aries",
         "lord_house_map": {h: (h % 12) + 1 for h in range(1, 13)}}
    f.update(extra)
    return f


def test_capability_gate_declares_ashtakavarga():
    assert "ashtakavarga" in capability_gate.FACT_BLOCK_PROVIDES


def test_build_shape_and_sum(monkeypatch):
    _patch(monkeypatch)
    out = build_ashtakavarga_facts(_chart())
    assert set(out["sav_by_house"]) == set(range(1, 13))
    assert sum(out["sav_by_house"].values()) == 337
    assert out["average_per_house"] == 28.08
    assert set(out["planet_bav_in_sign"]) == set(_SEVEN)
    assert out["strongest_house"] in range(1, 13)
    assert out["weakest_house"] in range(1, 13)


def test_sign_to_house_mapping(monkeypatch):
    _patch(monkeypatch)
    out = build_ashtakavarga_facts(_chart(asc="Sagittarius"))
    sav = _fake_sav(_fake_bav({}))
    assert out["sav_by_house"][1] == sav["Sagittarius"]   # house 1 == lagna sign
    assert out["sav_by_house"][2] == sav["Capricorn"]


def test_failsoft(monkeypatch):
    monkeypatch.setattr(ashtakavarga_facts, "compute_bav",
                        lambda p: (_ for _ in ()).throw(RuntimeError("bad")))
    assert build_ashtakavarga_facts(_chart()) == {}
    assert build_ashtakavarga_facts({}) == {}


def test_fact_block_renders(monkeypatch):
    _patch(monkeypatch)
    facts = _min_facts(ashtakavarga=build_ashtakavarga_facts(_chart()))
    fb = pipeline._fact_block(facts)
    assert "Sarvashtakavarga (SAV)" in fb
    assert "House 1:" in fb
    assert "Strongest house:" in fb
    assert "own BAV bindus" in fb


def test_fact_block_absent_when_missing():
    assert "Sarvashtakavarga" not in pipeline._fact_block(_min_facts())
