"""Tests for agent.astro.yogini_facts (S152 Yogini Mahadasha fact class).

Pins the ADAPTER's shape, its contiguity, its consistency with the underlying
engine, and its fail-soft contract. Deliberately does NOT assert which Yogini
runs when -- that is the engine's doctrine, validated against AstroSage on the
4 reference charts (scripts/validate_yogini_S152.py), not re-asserted here. The
engine's starting-index formula is itself only 1-of-4 oracle-validated (see the
yogini_facts validation caveat), so a value assertion here would merely pin an
unvalidated formula.
"""
from __future__ import annotations

from agent.astro.yogini_facts import build_yogini_facts, _LORD_FULL
from agent.calculations.dashas.yogini import compute_yogini_dasha

_MOON_LON = 201.0          # arbitrary sidereal longitude
_JD = 2451545.0            # arbitrary birth JD (UT)
_VALID_LORDS = {"Moon", "Sun", "Jupiter", "Mars", "Mercury", "Saturn",
                "Venus", "Rahu"}


def _chart(moon_lon=_MOON_LON, jd=_JD) -> dict:
    return {"planetary_positions": {"Moon": {"longitude": moon_lon}},
            "meta": {"jd_ut": jd}}


def test_shape_is_time_ordered_contiguous_md_sequence():
    out = build_yogini_facts(_chart())
    mds = out["mahadashas"]
    assert len(mds) == 24                       # engine default: 3 cycles x 8
    for m in mds:
        assert m["lord"] in _VALID_LORDS         # abbreviations expanded to full names
        assert 1 <= m["years"] <= 8
        assert m["start"] <= m["end"]
    for a, b in zip(mds, mds[1:]):
        assert a["end"] == b["start"]            # contiguous, no gaps/overlaps
        assert a["start"] <= b["start"]          # time-ordered


def test_consistent_with_the_engine_sequence():
    out = build_yogini_facts(_chart())
    engine = compute_yogini_dasha(_MOON_LON, _JD)
    assert [m["yogini"] for m in out["mahadashas"]] == [p.yogini_name for p in engine]
    assert [m["lord"] for m in out["mahadashas"]] == \
           [_LORD_FULL.get(p.lord, p.lord) for p in engine]


def test_fail_soft_when_moon_longitude_missing():
    assert build_yogini_facts({"meta": {"jd_ut": _JD},
                               "planetary_positions": {}}) == {}


def test_fail_soft_when_birth_jd_missing():
    assert build_yogini_facts({"planetary_positions":
                               {"Moon": {"longitude": _MOON_LON}}}) == {}


def test_fail_soft_on_empty_or_none_chart():
    assert build_yogini_facts({}) == {}
    assert build_yogini_facts(None) == {}
