"""E2E pipeline tests for agent/calculations/ashtakavarga/ashtakavarga.py --
ephemeris -> D-1 sign extraction -> compute_bav/compute_sav wiring.

Deliberately different from test_ashtakavarga.py: that file hardcodes
David's placements and already locked the kernel cell-by-cell against
tests/fixtures/jhora_david_ashtakavarga.md. This file derives each chart's
placements live via agent.chart_calculator.calculate_chart() instead, so a
failure here can point at the ephemeris/sign-extraction wiring rather than
re-litigating the already-locked AV_TABLES kernel.

Oracle: tests/fixtures/jhora_ashtakavarga_cross_charts.md -- Sulabh
(reference=Sagittarius), Surbhi (reference=Libra), Sheridan
(reference=Taurus), each checksum-validated at capture (21/21: 8 BAV row
totals + 12 SAV column sums + grand total 337).

Birth data matches the existing e2e fixtures used across
tests/calculations/strength/{test_bhava_bala,test_dig_bala,test_kala_bala,
test_ishta_kashta}.py's own _BIRTH_ARGS convention (same literals,
independently duplicated here per this project's per-module duplication
convention -- see test_ashtakoot.py's docstring for the same rationale).

KNOWN RISK -- Sheridan's Moon: Sheridan's Moon is Ashvini pada 1
(0d00'-3d20' Aries per AstroSage). If it ever sits within ~1 arc-minute of
0d Aries, the documented 57.77-arcsecond pyswisseph-vs-JHora Lahiri
ayanamsa gap (CLAUDE.md Known Source Divergences) could flip the computed
sign and cascade into a wholesale Moon-row BAV mismatch (Moon is a
reference for its own row plus a contributor to every other owner's Moon
column). As of this writing Sheridan's sidereal Moon longitude is ~2.16
degrees into Aries -- comfortably clear of that boundary -- so this is a
documented latent risk, not a currently-triggered one. If a future run of
this file fails on Moon-related cells for Sheridan ONLY (not other owners/
signs), the full-grid assertion below prints the live computed Moon
longitude; treat that as a boundary case for design review. Do NOT adjust
tolerances or fixture values to paper over it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # project root

import pytest

from agent.calculations.ashtakavarga.ashtakavarga import compute_bav, compute_sav
from agent.chart_calculator import SIGNS, _calc_planets, calculate_chart

_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

# Same literals as tests/calculations/strength/test_bhava_bala.py's own
# _BIRTH_ARGS -- independently duplicated here, not imported (per-module
# duplication convention).
_BIRTH_ARGS: dict[str, tuple[str, str, str, str]] = {
    "sulabh":   ("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India"),
    "surbhi":   ("Surbhi", "11 Sep 1992", "10:30", "Patna, India"),
    "sheridan": ("Sheridan", "27 May 1984", "08:00", "Durban, South Africa"),
}

_EXPECTED_LAGNA: dict[str, str] = {
    "sulabh": "Sagittarius",
    "surbhi": "Libra",
    "sheridan": "Taurus",
}

# tests/fixtures/jhora_ashtakavarga_cross_charts.md's BAV tables,
# Aries..Pisces column order.
_FIXTURE_BAV: dict[str, dict[str, list[int]]] = {
    "sulabh": {
        "Sun":     [4, 2, 2, 3, 5, 6, 5, 5, 4, 5, 4, 3],
        "Moon":    [3, 7, 2, 4, 3, 5, 6, 4, 2, 5, 5, 3],
        "Mars":    [3, 3, 1, 4, 4, 4, 4, 1, 4, 5, 3, 3],
        "Mercury": [2, 3, 3, 6, 6, 6, 3, 4, 5, 6, 5, 5],
        "Jupiter": [6, 5, 5, 4, 3, 4, 5, 5, 4, 6, 4, 5],
        "Venus":   [3, 2, 3, 5, 5, 4, 4, 4, 5, 6, 6, 5],
        "Saturn":  [4, 3, 2, 0, 2, 4, 6, 2, 4, 3, 4, 5],
        "Lagna":   [3, 5, 4, 2, 5, 5, 6, 1, 5, 6, 4, 3],
    },
    "surbhi": {
        "Sun":     [6, 2, 4, 5, 4, 4, 2, 3, 5, 5, 4, 4],
        "Moon":    [2, 5, 5, 4, 5, 1, 4, 6, 4, 2, 4, 7],
        "Mars":    [4, 2, 4, 6, 3, 2, 4, 1, 5, 5, 1, 2],
        "Mercury": [5, 4, 4, 8, 3, 4, 4, 4, 5, 7, 2, 4],
        "Jupiter": [4, 5, 8, 3, 5, 4, 5, 4, 4, 4, 4, 6],
        "Venus":   [6, 6, 6, 2, 3, 4, 5, 4, 5, 4, 3, 4],
        "Saturn":  [3, 4, 4, 5, 4, 1, 2, 3, 3, 3, 2, 5],
        "Lagna":   [5, 4, 5, 3, 4, 3, 3, 7, 4, 6, 1, 4],
    },
    "sheridan": {
        "Sun":     [5, 4, 5, 3, 6, 2, 5, 4, 2, 5, 4, 3],
        "Moon":    [2, 0, 3, 6, 4, 3, 5, 4, 5, 4, 7, 6],
        "Mars":    [3, 4, 3, 4, 3, 4, 6, 2, 1, 2, 4, 3],
        "Mercury": [4, 6, 5, 5, 5, 4, 5, 4, 3, 6, 3, 4],
        "Jupiter": [2, 5, 4, 4, 5, 5, 5, 3, 5, 6, 7, 5],
        "Venus":   [3, 4, 6, 5, 7, 5, 1, 1, 7, 4, 4, 5],
        "Saturn":  [2, 3, 2, 2, 4, 3, 3, 3, 4, 1, 6, 6],
        "Lagna":   [3, 3, 3, 6, 5, 4, 5, 1, 4, 5, 4, 6],
    },
}

_FIXTURE_SAV: dict[str, list[int]] = {
    "sulabh":   [25, 25, 18, 26, 28, 33, 33, 25, 28, 36, 31, 29],
    "surbhi":   [30, 28, 35, 33, 27, 20, 26, 25, 31, 30, 20, 32],
    "sheridan": [21, 26, 28, 29, 34, 26, 30, 21, 27, 28, 35, 32],
}
_FIXTURE_SAV_TOTAL = 337


@pytest.fixture(scope="module")
def charts_data() -> dict[str, dict]:
    """Real chart -> placements -> BAV/SAV, computed once per chart for the
    whole module (network-free: tests/conftest.py's session-scoped geocoder
    patch is already active by the time this module-scoped fixture runs).
    """
    data: dict[str, dict] = {}
    for key, args in _BIRTH_ARGS.items():
        chart = calculate_chart(*args)
        placements = {"Lagna": chart["lagna_chart"]["ascendant"]}
        pp = chart["planetary_positions"]
        for planet in _PLANETS:
            placements[planet] = pp[planet]["sign"]

        # Sheridan's known-risk comment (module docstring) needs the live
        # Moon longitude on hand for the full-grid failure message.
        jd_ut = chart["meta"]["jd_ut"]
        asc_lon = chart["meta"]["asc_lon_sidereal"]
        moon_lon = _calc_planets(jd_ut, asc_lon)["Moon"]["longitude"]

        bav = compute_bav(placements)
        sav = compute_sav(bav)
        data[key] = {
            "placements": placements,
            "bav": bav,
            "sav": sav,
            "moon_longitude": moon_lon,
        }
    return data


# ── (c) Placement-sanity: pin the derived lagna sign per chart ─────────────

@pytest.mark.parametrize("chart_key,expected_lagna", sorted(_EXPECTED_LAGNA.items()))
def test_derived_lagna_sign(charts_data, chart_key, expected_lagna):
    """Pins the ephemeris-derived ascendant sign so a placement-wiring
    failure (wrong chart, wrong lagna extraction) is distinguishable from a
    kernel failure in the grid/SAV parity tests below.
    """
    got = charts_data[chart_key]["placements"]["Lagna"]
    assert got == expected_lagna, (
        f"{chart_key}: derived Lagna sign {got!r} != expected {expected_lagna!r} "
        f"-- this is a placement/ephemeris wiring failure, not a kernel failure"
    )


# ── (a) Full-grid parity: 3 charts x 8 owners x 12 signs = 288 cells ────────

_ALL_CELLS = [
    (chart_key, owner, sign)
    for chart_key, owners in _FIXTURE_BAV.items()
    for owner in owners
    for sign in SIGNS
]


@pytest.mark.parametrize(
    "chart_key,owner,sign",
    _ALL_CELLS,
    ids=[f"{c}-{o}-{s}" for c, o, s in _ALL_CELLS],
)
def test_full_grid_parity_against_jhora_fixture(charts_data, chart_key, owner, sign):
    expected = _FIXTURE_BAV[chart_key][owner][SIGNS.index(sign)]
    got = charts_data[chart_key]["bav"][owner][sign]
    if got != expected:
        extra = ""
        if chart_key == "sheridan" and owner == "Moon":
            extra = (
                f" [KNOWN-RISK: Sheridan's Moon longitude is "
                f"{charts_data[chart_key]['moon_longitude']:.6f} degrees sidereal -- "
                f"see module docstring's ayanamsa-boundary note before adjusting "
                f"tolerances or fixture values]"
            )
        assert got == expected, (
            f"BAV mismatch chart={chart_key!r} owner={owner!r} sign={sign!r}: "
            f"got {got}, expected {expected} "
            f"(tests/fixtures/jhora_ashtakavarga_cross_charts.md){extra}"
        )


# ── (b) SAV parity: 12 signs per chart + grand total 337 ────────────────────

_ALL_SAV_CELLS = [
    (chart_key, sign) for chart_key in _FIXTURE_SAV for sign in SIGNS
]


@pytest.mark.parametrize(
    "chart_key,sign",
    _ALL_SAV_CELLS,
    ids=[f"{c}-{s}" for c, s in _ALL_SAV_CELLS],
)
def test_sav_parity_against_jhora_fixture(charts_data, chart_key, sign):
    expected = _FIXTURE_SAV[chart_key][SIGNS.index(sign)]
    got = charts_data[chart_key]["sav"][sign]
    assert got == expected, (
        f"SAV mismatch chart={chart_key!r} sign={sign!r}: got {got}, "
        f"expected {expected} (tests/fixtures/jhora_ashtakavarga_cross_charts.md)"
    )


@pytest.mark.parametrize("chart_key", sorted(_FIXTURE_SAV))
def test_sav_grand_total_is_337(charts_data, chart_key):
    assert sum(charts_data[chart_key]["sav"].values()) == _FIXTURE_SAV_TOTAL
