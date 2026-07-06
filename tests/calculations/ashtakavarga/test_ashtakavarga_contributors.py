"""Tests for compute_bav_contributors() in
agent/calculations/ashtakavarga/ashtakavarga.py.

This targets the contributor-SET function added for future Prastaara
Ashtakavarga kakshya scoring (module CITATION (e)), not compute_bav/
compute_sav/AV_TABLES themselves (those stay locked per
test_ashtakavarga.py and test_ashtakavarga_cross_charts.py).

Layer A: cardinality invariant, checked via the PUBLIC API rather than
         trusting compute_bav_contributors's own internal assert -- for
         all four reference charts (David hardcoded, as in
         test_ashtakavarga.py; Sulabh/Surbhi/Sheridan derived live via
         calculate_chart(), as in test_ashtakavarga_cross_charts.py),
         len(contributors[owner][sign]) must equal compute_bav(...)
         [owner][sign] for all 96 cells per chart (384 total).

Layer B: membership oracle -- the part cardinality cannot catch (two
         cells could swap a contributor and still match in count). David's
         complete Sun-BAV contributor sets, hand-derived in design review
         2026-07-06 from PVR Table 19 (cardinalities independently
         cross-checked against tests/fixtures/jhora_david_ashtakavarga.md's
         Sun row -- 3,5,4,4,5,2,5,5,3,5,4,3 -- before this test was
         written).

Layer C: type/immutability (returned sets are frozenset) and error paths,
         which mirror compute_bav's exactly since compute_bav_contributors
         delegates validation to it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # project root

import pytest

from agent.calculations.ashtakavarga.ashtakavarga import (
    compute_bav,
    compute_bav_contributors,
)
from agent.chart_calculator import SIGNS, calculate_chart

_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

# David's D-1 sign placements -- same literals as test_ashtakavarga.py's
# _DAVID_PLACEMENTS (tests/fixtures/jhora_david_ashtakavarga.md "D-1
# positions" table), independently duplicated here per this project's
# per-module duplication convention.
_DAVID_PLACEMENTS: dict[str, str] = {
    "Sun": "Capricorn",
    "Moon": "Leo",
    "Mars": "Taurus",
    "Mercury": "Capricorn",
    "Jupiter": "Pisces",
    "Venus": "Scorpio",
    "Saturn": "Cancer",
    "Lagna": "Virgo",
}

# Same literals as test_ashtakavarga_cross_charts.py's _BIRTH_ARGS (which
# in turn matches tests/calculations/strength/test_bhava_bala.py's own
# _BIRTH_ARGS), independently duplicated here per this project's
# per-module duplication convention.
_BIRTH_ARGS: dict[str, tuple[str, str, str, str]] = {
    "sulabh":   ("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India"),
    "surbhi":   ("Surbhi", "11 Sep 1992", "10:30", "Patna, India"),
    "sheridan": ("Sheridan", "27 May 1984", "08:00", "Durban, South Africa"),
}

# David's complete Sun-BAV contributor sets, hand-derived in design review
# 2026-07-06 from PVR Table 19 (Sun's benefic-house table applied to
# David's placements: Sun=Capricorn, Moon=Leo, Mars=Taurus,
# Mercury=Capricorn, Jupiter=Pisces, Venus=Scorpio, Saturn=Cancer,
# Lagna=Virgo). Cardinalities independently match
# tests/fixtures/jhora_david_ashtakavarga.md's Sun row
# (3,5,4,4,5,2,5,5,3,5,4,3, Aries..Pisces) before this membership oracle
# was written.
_DAVID_SUN_CONTRIBUTORS: dict[str, frozenset[str]] = {
    "Aries":       frozenset({"Sun", "Venus", "Saturn"}),
    "Taurus":      frozenset({"Moon", "Mars", "Mercury", "Venus", "Saturn"}),
    "Gemini":      frozenset({"Moon", "Mars", "Mercury", "Lagna"}),
    "Cancer":      frozenset({"Sun", "Jupiter", "Saturn", "Lagna"}),
    "Leo":         frozenset({"Sun", "Mars", "Jupiter", "Saturn", "Lagna"}),
    "Virgo":       frozenset({"Sun", "Mercury"}),
    "Libra":       frozenset({"Sun", "Moon", "Mercury", "Venus", "Saturn"}),
    "Scorpio":     frozenset({"Sun", "Mars", "Mercury", "Jupiter", "Lagna"}),
    "Sagittarius": frozenset({"Mars", "Mercury", "Lagna"}),
    "Capricorn":   frozenset({"Sun", "Moon", "Mars", "Jupiter", "Saturn"}),
    "Aquarius":    frozenset({"Sun", "Mars", "Saturn", "Lagna"}),
    "Pisces":      frozenset({"Mars", "Mercury", "Saturn"}),
}


@pytest.fixture(scope="module")
def charts_placements() -> dict[str, dict[str, str]]:
    """{chart_key: placements} for all four reference charts -- David
    hardcoded, the other three derived live via calculate_chart() (network-
    free: tests/conftest.py's session-scoped geocoder patch is already
    active by the time this module-scoped fixture runs).
    """
    data: dict[str, dict[str, str]] = {"david": _DAVID_PLACEMENTS}
    for key, args in _BIRTH_ARGS.items():
        chart = calculate_chart(*args)
        placements = {"Lagna": chart["lagna_chart"]["ascendant"]}
        pp = chart["planetary_positions"]
        for planet in _PLANETS:
            placements[planet] = pp[planet]["sign"]
        data[key] = placements
    return data


@pytest.fixture(scope="module")
def charts_bav(charts_placements) -> dict[str, dict[str, dict[str, int]]]:
    return {key: compute_bav(placements) for key, placements in charts_placements.items()}


@pytest.fixture(scope="module")
def charts_contributors(charts_placements) -> dict[str, dict[str, dict[str, frozenset]]]:
    return {
        key: compute_bav_contributors(placements)
        for key, placements in charts_placements.items()
    }


# ── Layer A: cardinality invariant via public API, all 4 charts x 96 cells ──

_ALL_CHART_CELLS = [
    (chart_key, owner, sign)
    for chart_key in ("david", "sulabh", "surbhi", "sheridan")
    for owner in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Lagna")
    for sign in SIGNS
]


@pytest.mark.parametrize(
    "chart_key,owner,sign",
    _ALL_CHART_CELLS,
    ids=[f"{c}-{o}-{s}" for c, o, s in _ALL_CHART_CELLS],
)
def test_contributor_count_matches_compute_bav(charts_bav, charts_contributors, chart_key, owner, sign):
    """Does not trust compute_bav_contributors's own internal assert --
    re-derives the same check from the public return values of both
    functions.
    """
    expected = charts_bav[chart_key][owner][sign]
    got = len(charts_contributors[chart_key][owner][sign])
    assert got == expected, (
        f"{chart_key}: contributor count for owner={owner!r} sign={sign!r} "
        f"is {got}, but compute_bav says {expected}"
    )


# ── Layer B: membership oracle -- David's Sun row, PVR Table 19 hand-derive ──

@pytest.mark.parametrize("sign", SIGNS)
def test_david_sun_contributor_membership(charts_contributors, sign):
    expected = _DAVID_SUN_CONTRIBUTORS[sign]
    got = charts_contributors["david"]["Sun"][sign]
    assert got == expected, (
        f"David Sun/{sign!r} contributor set mismatch: got {sorted(got)}, "
        f"expected {sorted(expected)} (symmetric difference: "
        f"{sorted(got ^ expected)}) -- see PVR Table 19 hand-derivation in "
        f"this file's _DAVID_SUN_CONTRIBUTORS comment"
    )


# ── Layer C: type/immutability + error paths (mirror compute_bav's) ────────

@pytest.mark.parametrize("owner,sign", [(o, s) for o in _PLANETS + ("Lagna",) for s in SIGNS])
def test_contributor_set_is_frozenset(charts_contributors, owner, sign):
    assert isinstance(charts_contributors["david"][owner][sign], frozenset)


def test_compute_bav_contributors_missing_contributor_raises_value_error():
    incomplete = dict(_DAVID_PLACEMENTS)
    del incomplete["Saturn"]
    with pytest.raises(ValueError, match="missing required contributor"):
        compute_bav_contributors(incomplete)


def test_compute_bav_contributors_unknown_contributor_raises_value_error():
    bad = dict(_DAVID_PLACEMENTS)
    bad["Rahu"] = "Aries"
    with pytest.raises(ValueError, match="unknown contributor"):
        compute_bav_contributors(bad)


def test_compute_bav_contributors_unknown_sign_raises_value_error():
    bad = dict(_DAVID_PLACEMENTS)
    bad["Sun"] = "Ophiuchus"
    with pytest.raises(ValueError, match="unrecognized sign"):
        compute_bav_contributors(bad)
