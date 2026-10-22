"""Tests for the point-1 Jaimini fact-block wiring: composer + render + gate."""
from __future__ import annotations

from agent.astro import pipeline, capability_gate
from agent.astro import jaimini_facts
from agent.astro.jaimini_facts import build_jaimini_facts

_S = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
      "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
_EIGHT = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu")
_ORDER = ("AK", "AmK", "BK", "MK", "PiK", "PK", "GK", "DK")


class _KR:
    def __init__(self, k): self.karakas = k


class _AR:
    def __init__(self, s): self.arudha_sign = s


class _BP:
    def __init__(self, house_num, sign):
        self.house_num = house_num
        self.result = _AR(sign)


class _BPS:
    def __init__(self, padas): self.padas = padas


def _fake_bhava_padas(asc_sign, lon):
    for p in _EIGHT + ("Ketu",):
        if p not in lon:
            raise ValueError(f"missing {p}")
    a = _S.index(asc_sign)
    return _BPS([_BP(h, _S[(a + h) % 12]) for h in range(1, 13)])


def _chart(asc="Sagittarius"):
    a = _S.index(asc)
    hlm = [{"house": h, "sign": _S[(a + h - 1) % 12]} for h in range(1, 13)]
    pp = {p: {"longitude": (i * 37.5) % 360}
          for i, p in enumerate(list(_EIGHT) + ["Ketu"])}
    return {"planetary_positions": pp, "house_lord_mapping": hlm}


def _fake_karakas(lon):
    for p in _EIGHT:
        if p not in lon:
            raise ValueError(f"missing {p}")
    return _KR(tuple((_ORDER[i], _EIGHT[i]) for i in range(8)))


def _fake_arudha(house_sign, lon):
    for p in _EIGHT + ("Ketu",):
        if p not in lon:
            raise ValueError(f"missing {p}")
    if house_sign == "Scorpio":
        raise ValueError("co-lord cascade boom")  # rare raise
    return _AR(_S[(_S.index(house_sign) + 2) % 12])


def _patch(mp):
    mp.setattr(jaimini_facts, "compute_chara_karakas", _fake_karakas)
    mp.setattr(jaimini_facts, "compute_arudha_pada", _fake_arudha)
    mp.setattr(jaimini_facts, "compute_bhava_padas", _fake_bhava_padas)


def _min_facts(**extra):
    f = {"ascendant_sign": "Aries",
         "lord_house_map": {h: (h % 12) + 1 for h in range(1, 13)}}
    f.update(extra)
    return f


def test_capability_gate_declares_jaimini():
    assert "jaimini" in capability_gate.FACT_BLOCK_PROVIDES


def test_build_karakas_and_arudhas(monkeypatch):
    _patch(monkeypatch)
    out = build_jaimini_facts(_chart(asc="Aries"))  # house12 = Pisces, no raise
    assert set(out["chara_karakas"]) == set(_ORDER)
    assert "arudha_lagna" in out and "upapada_lagna" in out


def test_per_part_failsoft_arudha_raise_keeps_karakas(monkeypatch):
    _patch(monkeypatch)
    out = build_jaimini_facts(_chart(asc="Sagittarius"))  # house12 = Scorpio -> arudha raises
    assert "chara_karakas" in out          # survives
    assert "upapada_lagna" not in out      # dropped


def test_failsoft_empty(monkeypatch):
    _patch(monkeypatch)
    assert build_jaimini_facts({}) == {}


def test_fact_block_renders(monkeypatch):
    _patch(monkeypatch)
    facts = _min_facts(jaimini=build_jaimini_facts(_chart(asc="Aries")))
    fb = pipeline._fact_block(facts)
    assert "Jaimini chara karakas" in fb
    assert "AK (soul/self):" in fb
    assert "DK (spouse):" in fb
    assert "Arudha Lagna (AL" in fb
    assert "Upapada Lagna (UL" in fb


def test_fact_block_absent_when_missing():
    assert "Jaimini chara karakas" not in pipeline._fact_block(_min_facts())


# ── Karakamsa (PVR Ch.7 Sec.7.3.6): AK's navamsa sign, a pure restate ────────
# The fake karakas map AK -> _EIGHT[0] == "Sun"; a navamsa composed onto the
# chart carries Sun's D9 sign, which Karakamsa must restate verbatim.

def _chart_with_navamsa(asc="Aries", ak_d9_sign="Leo"):
    c = _chart(asc=asc)
    c["navamsa"] = {"d9_lagna_sign": "Libra",
                    "placements": {"Sun": {"sign": ak_d9_sign}}}
    return c


def test_karakamsa_restates_ak_navamsa_sign(monkeypatch):
    _patch(monkeypatch)
    out = build_jaimini_facts(_chart_with_navamsa(asc="Aries", ak_d9_sign="Leo"))
    assert out["karakamsa"] == {"atmakaraka": "Sun", "sign": "Leo"}


def test_karakamsa_absent_without_navamsa_but_karakas_survive(monkeypatch):
    _patch(monkeypatch)
    out = build_jaimini_facts(_chart(asc="Aries"))  # no navamsa composed
    assert "karakamsa" not in out
    assert "chara_karakas" in out


def test_karakamsa_failsoft_does_not_drop_karakas_on_bad_navamsa(monkeypatch):
    _patch(monkeypatch)
    c = _chart(asc="Aries")
    c["navamsa"] = {"placements": {"Sun": {}}}  # AK present but no 'sign' key
    out = build_jaimini_facts(c)
    assert "karakamsa" not in out              # nothing to restate -> omitted
    assert set(out["chara_karakas"]) == set(_ORDER)  # karakas intact


def test_fact_block_renders_karakamsa(monkeypatch):
    _patch(monkeypatch)
    facts = _min_facts(jaimini=build_jaimini_facts(_chart_with_navamsa(asc="Aries")))
    fb = pipeline._fact_block(facts)
    assert "Karakamsa" in fb
    assert ": Leo." in fb


# ── Bhava Arudhas (PVR Ch.9 Sec.9.2): all 12 arudha padas, A1(=AL)..A12(=UL) ──
# Validated against PVR Example 29 in tests/calculations/test_jaimini_padas.py;
# here we only pin the wiring: all 12 surface, in a block separate from AL/UL.

def test_bhava_padas_surfaces_all_twelve(monkeypatch):
    _patch(monkeypatch)
    out = build_jaimini_facts(_chart(asc="Aries"))
    assert set(out["bhava_padas"]) == set(range(1, 13))
    assert all(isinstance(v, str) for v in out["bhava_padas"].values())


def test_bhava_padas_block_independent_of_al_ul_failsoft(monkeypatch):
    # house12 = Scorpio makes _fake_arudha raise (UL dropped), but the all-12
    # orchestrator block is independent and still surfaces.
    _patch(monkeypatch)
    out = build_jaimini_facts(_chart(asc="Sagittarius"))
    assert "upapada_lagna" not in out            # AL/UL block dropped UL
    assert set(out["bhava_padas"]) == set(range(1, 13))  # all-12 block survived


def test_fact_block_renders_bhava_padas(monkeypatch):
    _patch(monkeypatch)
    facts = _min_facts(jaimini=build_jaimini_facts(_chart(asc="Aries")))
    fb = pipeline._fact_block(facts)
    assert "Bhava Arudhas (Jaimini" in fb
    assert "A10 (career/public-image):" in fb
