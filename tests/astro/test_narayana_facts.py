"""Tests for the S153 Narayana fact-block wiring: composer shape + fail-soft.

The ENGINE's correctness (sequence + lengths) is validated end-to-end against
JHora in tests/calculations/test_narayana_dasa.py. This file only pins the
COMPOSER's shape, birth-anchoring and fail-soft contract, and the capability
gate / render pairing is pinned in tests/astro/test_capability_gate.py.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from agent.astro import capability_gate
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
    assert set(first) == {"rasi", "lord", "years", "cycle", "start", "end"}
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
