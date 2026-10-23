"""Tests for the S153 Narayana fact-block wiring: composer shape + fail-soft.

The ENGINE's correctness (sequence + lengths) is validated end-to-end against
JHora in tests/calculations/test_narayana_dasa.py. This file only pins the
COMPOSER's shape, birth-anchoring and fail-soft contract, and the capability
gate / render pairing is pinned in tests/astro/test_capability_gate.py.
"""
from __future__ import annotations

import datetime as _dtmod
from datetime import datetime, timedelta, timezone

from agent.astro import capability_gate, pipeline
from agent.calculations.dashas.narayana import compute_narayana_antardasha
from agent.astro.narayana_facts import build_narayana_facts

_IST = timezone(timedelta(hours=5, minutes=30))

# Sulabh's D1 (same longitudes as test_narayana_dasa.py), asc Sagittarius.
_SULABH = {
    "Sun": 352.520, "Moon": 212.229, "Mars": 275.576, "Mercury": 337.876,
    "Jupiter": 12.561, "Venus": 38.328, "Saturn": 248.843, "Rahu": 328.398,
    "Ketu": 148.398,
}


def _chart():
    return {
        "meta": {"asc_lon_sidereal": 262.769,
                 "local_datetime": datetime(1988, 4, 6, 0, 30, tzinfo=_IST)},
        "planetary_positions": {p: {"longitude": lon} for p, lon in _SULABH.items()},
    }


def test_capability_gate_declares_narayana():
    assert "narayana" in capability_gate.FACT_BLOCK_PROVIDES


def test_build_narayana_shape_and_birth_anchoring():
    out = build_narayana_facts(_chart())
    assert out["seed"] == "Sagittarius"
    assert out["progression_case"] == "saturn"
    mds = out["mahadashas"]
    assert len(mds) == 24                              # two cycles x 12
    first = mds[0]
    assert first["rasi"] == "Sagittarius" and first["cycle"] == 1
    assert first["years"] == 4
    assert first["start"] == "1988-04-06"              # anchored at birth
    # keys present per period
    assert set(first) == {"rasi", "lord", "years", "cycle", "start", "end",
                          "antardashas"}
    # start dates are non-decreasing (monotonic timeline)
    starts = [m["start"] for m in mds]
    assert starts == sorted(starts)
    # cycle 2 length mirrors 12 - cycle 1 (engine contract surfaced intact)
    c1 = {m["rasi"]: m["years"] for m in mds if m["cycle"] == 1}
    for m in mds:
        if m["cycle"] == 2:
            assert m["years"] == 12 - c1[m["rasi"]]


def test_build_narayana_failsoft():
    assert build_narayana_facts({}) == {}
    assert build_narayana_facts({"meta": {}}) == {}
    assert build_narayana_facts(None) == {}
    # missing a planet longitude -> {}
    ch = _chart()
    del ch["planetary_positions"]["Venus"]
    assert build_narayana_facts(ch) == {}
    # missing birth datetime -> {}
    ch2 = _chart()
    ch2["meta"].pop("local_datetime")
    assert build_narayana_facts(ch2) == {}


# ── Antardasa composition (S154): equal 1/12 sub-intervals, engine-ordered ───

def test_antardashas_count_and_zero_year_mds():
    mds = build_narayana_facts(_chart())["mahadashas"]
    zero = [m for m in mds if m["years"] == 0]
    assert zero, "Sulabh's Taurus cycle-2 MD is zero-length"
    for m in mds:
        if m["years"] > 0:
            assert len(m["antardashas"]) == 12
        else:
            assert "antardashas" not in m


def test_antardasha_sequence_matches_engine():
    mds = build_narayana_facts(_chart())["mahadashas"]
    for m in mds:
        if m["years"] > 0:
            got = tuple(a["rasi"] for a in m["antardashas"])
            assert got == compute_narayana_antardasha(m["rasi"], dict(_SULABH))


def test_antardasha_exact_nesting():
    for m in build_narayana_facts(_chart())["mahadashas"]:
        if m["years"] > 0:
            ads = m["antardashas"]
            assert ads[0]["start"] == m["start"]
            assert ads[-1]["end"] == m["end"]
            starts = [a["start"] for a in ads]
            assert starts == sorted(starts)


def test_antardasha_failsoft_missing_planet_returns_empty():
    ch = _chart()
    del ch["planetary_positions"]["Ketu"]
    assert build_narayana_facts(ch) == {}


# ── Fact-block render of the current MD's antardasas (clock frozen) ──────────

def _render_on(monkeypatch, today):
    class _FakeDate(_dtmod.date):
        @classmethod
        def today(cls):
            return today
    monkeypatch.setattr(_dtmod, "date", _FakeDate)
    facts = {"ascendant_sign": "Sagittarius",
             "lord_house_map": {h: (h % 12) + 1 for h in range(1, 13)},
             "narayana": build_narayana_facts(_chart())}
    return pipeline._fact_block(facts)


def test_fact_block_renders_current_md_antardashas(monkeypatch):
    fb = _render_on(monkeypatch, _dtmod.date(2026, 10, 23))
    lines = [l for l in fb.splitlines() if l.startswith("    sub-period ")]
    assert len(lines) == 12
    assert sum(l.endswith("[CURRENT]") for l in lines) == 1
    # MD rendering unchanged: exactly one CURRENT MD line, antardasas follow it
    md_cur = [l for l in fb.splitlines()
              if l.startswith("  ") and "(lord " in l and l.endswith("[CURRENT]")]
    assert len(md_cur) == 1
    assert "Taurus" in md_cur[0]


def test_fact_block_antardashas_absent_without_key(monkeypatch):
    class _FakeDate(_dtmod.date):
        @classmethod
        def today(cls):
            return _dtmod.date(2026, 10, 23)
    monkeypatch.setattr(_dtmod, "date", _FakeDate)
    nar = build_narayana_facts(_chart())
    for m in nar["mahadashas"]:
        m.pop("antardashas", None)
    fb = pipeline._fact_block({"ascendant_sign": "Sagittarius",
                               "lord_house_map": {h: (h % 12) + 1 for h in range(1, 13)},
                               "narayana": nar})
    assert not any(l.startswith("    sub-period ") for l in fb.splitlines())
