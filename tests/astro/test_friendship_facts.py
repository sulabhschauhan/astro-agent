"""Tests for agent.astro.friendship_facts (S152 pancha-dha maitri fact class).

These pin the ADAPTER's shape and its fail-soft contract, and that it is
CONSISTENT with the underlying PVR engine (every cell equals a direct
pancha_dha_maitri call). They deliberately do NOT hardcode specific friendship
labels -- the doctrinal correctness of the engine is validated against the
AstroSage Friendship Table on real charts (the oracle run), not re-asserted here.
"""
from __future__ import annotations

from agent.astro.friendship_facts import (
    build_friendship_facts, SEVEN_CLASSICAL, COMPOUND_ORDER,
)
from agent.calculations.core.friendship import pancha_dha_maitri


def _chart(signs: dict) -> dict:
    pp = {p: {"sign": s, "house": 1} for p, s in signs.items()}
    return {"planetary_positions": pp}


# A spread of signs so some pairs land friend and some enemy (not all identical).
_SIGNS = {
    "Sun": "Leo", "Moon": "Cancer", "Mars": "Aries", "Mercury": "Gemini",
    "Jupiter": "Sagittarius", "Venus": "Libra", "Saturn": "Aquarius",
    "Rahu": "Taurus", "Ketu": "Scorpio",   # present but must be ignored
}


def test_shape_is_directional_over_the_seven_classical():
    out = build_friendship_facts(_chart(_SIGNS))
    assert set(out["signs"]) == set(SEVEN_CLASSICAL)          # nodes excluded
    assert set(out["compound"]) == set(SEVEN_CLASSICAL)
    for a in SEVEN_CLASSICAL:
        # each planet relates to the other six, never to itself
        assert set(out["compound"][a]) == set(SEVEN_CLASSICAL) - {a}
        assert a not in out["compound"][a]


def test_every_cell_is_consistent_with_the_engine():
    out = build_friendship_facts(_chart(_SIGNS))
    for a in SEVEN_CLASSICAL:
        for b in SEVEN_CLASSICAL:
            if a == b:
                continue
            assert out["compound"][a][b] == pancha_dha_maitri(
                a, _SIGNS[a], b, _SIGNS[b])                   # adapter adds no astrology of its own


def test_by_planet_buckets_partition_the_row_into_valid_labels():
    out = build_friendship_facts(_chart(_SIGNS))
    for a in SEVEN_CLASSICAL:
        buckets = out["by_planet"][a]
        assert set(buckets) == set(COMPOUND_ORDER)
        flat = [p for lab in COMPOUND_ORDER for p in buckets[lab]]
        assert sorted(flat) == sorted(set(SEVEN_CLASSICAL) - {a})  # every other planet, once
        for lab, members in buckets.items():
            for m in members:
                assert out["compound"][a][m] == lab          # bucket label matches the cell


def test_relationship_is_asymmetric_capable():
    # pancha-dha maitri is directional; the adapter must preserve that (not force
    # symmetry). At least assert both directions are independently present.
    out = build_friendship_facts(_chart(_SIGNS))
    assert "Saturn" in out["compound"]["Sun"]
    assert "Sun" in out["compound"]["Saturn"]


def test_fail_soft_when_a_classical_planet_sign_is_missing():
    signs = dict(_SIGNS)
    del signs["Venus"]                                       # a required classical planet
    assert build_friendship_facts(_chart(signs)) == {}


def test_fail_soft_on_empty_or_bad_chart():
    assert build_friendship_facts({}) == {}
    assert build_friendship_facts({"planetary_positions": {}}) == {}
    assert build_friendship_facts(None) == {}
