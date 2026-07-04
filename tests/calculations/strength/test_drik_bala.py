"""Tests for agent/calculations/strength/drik_bala.py — P2.5 Drik Bala V1.2.

Layer A: Sphuta Drishti kernel structural tests (no ephemeris) — formula
         boundary continuity per aspecting-planet family (hardest case
         first: exact segment values, not just "doesn't crash"), clamp
         bounds, Moon/Mercury classification edge cases.
Layer B: JHora v8 parity, all 4 reference charts, 28 parametrized
         assertions. Hardest case first: Sheridan (the chart that flips
         both Moon and Mercury's classification — see drik_bala.py's
         SHERIDAN EDGE CASE docstring note) before the other 3 charts.
Layer C: error contract + output shape.

Geocoder monkeypatched by tests/conftest.py; all locations already in
tests/fixtures/geocoded_locations.json.

CORRECTION vs. original task spec: Saturn's boundary list was given as
30/60/90/240/270/300. D=90 is not an actual segment transition for
Saturn — _saturn_drishti's 60-120 range is a single continuous branch
(2*D-60 up to D=60, then 90-D/2 from D=60 to D=120), so D=90 sits mid-
segment and asserting "continuity" there would be vacuous (same branch
on both sides). The real transition after D=60 is at D=120. Verified
directly against agent/calculations/strength/drik_bala.py's
_saturn_drishti before writing these assertions; using 120 in its place.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # project root

import pytest

from agent.calculations.strength.drik_bala import (
    _base_drishti,
    _mars_drishti,
    _jupiter_drishti,
    _saturn_drishti,
    _sphuta_drishti,
    _classify_moon,
    _classify_mercury,
    compute_drik_bala,
)

_PLANETS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
_EPS = 1e-6


def _left_limit(fn, D: float) -> float:
    return fn(D - _EPS)


# ── Layer A: Sphuta Drishti kernel (no ephemeris) ────────────────────────────

class TestBaseDrishtiBoundaries:
    """Sun/Moon/Mercury/Venus base taper — BPHS Ch.28."""

    @pytest.mark.parametrize("D,expected", [
        (30.0, 0.0),
        (60.0, 15.0),
        (90.0, 45.0),
        (120.0, 30.0),
        (150.0, 0.0),
        (180.0, 60.0),
        (300.0, 0.0),
    ])
    def test_exact_boundary_value(self, D, expected):
        assert _base_drishti(D) == pytest.approx(expected, abs=1e-9)

    @pytest.mark.parametrize("D", [30.0, 60.0, 90.0, 120.0, 150.0, 180.0, 300.0])
    def test_continuous_at_boundary(self, D):
        assert _left_limit(_base_drishti, D) == pytest.approx(
            _base_drishti(D), abs=1e-4
        )


class TestMarsDrishtiBoundaries:
    """Mars special-aspect segments."""

    @pytest.mark.parametrize("D,expected", [
        (60.0, 15.0),
        (90.0, 60.0),
        (150.0, 0.0),
        (210.0, 60.0),
        (240.0, 30.0),
    ])
    def test_exact_boundary_value(self, D, expected):
        assert _mars_drishti(D) == pytest.approx(expected, abs=1e-9)

    @pytest.mark.parametrize("D", [60.0, 90.0, 150.0, 210.0, 240.0])
    def test_continuous_at_boundary(self, D):
        assert _left_limit(_mars_drishti, D) == pytest.approx(
            _mars_drishti(D), abs=1e-4
        )

    def test_plateau_entry_at_180_continuous_by_construction(self):
        """D=180 is where the 150-180 base-taper segment (2*(D-150), value
        60 at D=180) hands off to the 180-210 flat plateau (constant 60).
        Both sides equal 60 by construction of the plateau's own value, not
        because any reference chart's aspect pair validated this point — no
        chart in the 4-chart JHora fixture set has an aspect pair landing in
        [180, 210) (see drik_bala.py docstring: "Mars 180-210 flat plateau
        ... UNTESTED by data"). This test documents the construction, it
        does not substitute for empirical validation.
        """
        assert _mars_drishti(180.0 - _EPS) == pytest.approx(60.0, abs=1e-4)
        assert _mars_drishti(180.0) == pytest.approx(60.0, abs=1e-9)


class TestJupiterDrishtiBoundaries:
    """Jupiter special-aspect segments."""

    @pytest.mark.parametrize("D,expected", [
        (90.0, 45.0),
        (120.0, 60.0),
        (150.0, 0.0),
        (210.0, 45.0),
        (240.0, 60.0),
        (270.0, 15.0),
    ])
    def test_exact_boundary_value(self, D, expected):
        assert _jupiter_drishti(D) == pytest.approx(expected, abs=1e-9)

    @pytest.mark.parametrize("D", [90.0, 120.0, 150.0, 210.0, 240.0, 270.0])
    def test_continuous_at_boundary(self, D):
        assert _left_limit(_jupiter_drishti, D) == pytest.approx(
            _jupiter_drishti(D), abs=1e-4
        )


class TestSaturnDrishtiBoundaries:
    """Saturn special-aspect segments.

    Boundary set corrected to 30/60/120/240/270/300 — see module
    docstring CORRECTION note (D=90 is not a real transition for Saturn).
    """

    @pytest.mark.parametrize("D,expected", [
        (30.0, 0.0),
        (60.0, 60.0),
        (120.0, 30.0),
        (240.0, 30.0),
        (270.0, 60.0),
        (300.0, 0.0),
    ])
    def test_exact_boundary_value(self, D, expected):
        assert _saturn_drishti(D) == pytest.approx(expected, abs=1e-9)

    @pytest.mark.parametrize("D", [30.0, 60.0, 120.0, 240.0, 270.0, 300.0])
    def test_continuous_at_boundary(self, D):
        assert _left_limit(_saturn_drishti, D) == pytest.approx(
            _saturn_drishti(D), abs=1e-4
        )


class TestClamp:
    """_sphuta_drishti clamps S to [0, 60] regardless of what the
    per-planet formula returns. None of the 4 formula families actually
    produce out-of-range values in-domain (every boundary above lands
    inside [0, 60]), so the clamp is defensive rather than load-bearing
    for real charts — tested directly here via monkeypatched formulas
    rather than relying on a formula ever misbehaving naturally.
    """

    def test_clamps_negative_to_zero(self, monkeypatch):
        from agent.calculations.strength import drik_bala
        monkeypatch.setitem(drik_bala._DRISHTI_FORMULA, "Sun", lambda D: -999.0)
        assert _sphuta_drishti("Sun", 50.0) == 0.0

    def test_clamps_excess_to_sixty(self, monkeypatch):
        from agent.calculations.strength import drik_bala
        monkeypatch.setitem(drik_bala._DRISHTI_FORMULA, "Sun", lambda D: 999.0)
        assert _sphuta_drishti("Sun", 50.0) == 60.0


class TestMoonClassification:
    """Elongation-based benefic window: 90 <= elongation < 270."""

    @pytest.mark.parametrize("elongation,expected_benefic", [
        (89.99, False),
        (90.0, True),
        (269.99, True),
        (270.0, False),
    ])
    def test_elongation_boundary(self, elongation, expected_benefic):
        planet_lons = {"Sun": 0.0, "Moon": elongation}
        assert _classify_moon(planet_lons) is expected_benefic


# ── Layer B: JHora v8 parity, all 4 reference charts ─────────────────────────
#
# JHora v8 Shadbala table, hand-transcribed Session 46. This is a SEPARATE
# oracle from tests/fixtures/shadbala_fixtures.py's "drik" field (that field
# is the AstroSage V1-stub-era fixture range, e.g. Sulabh sun=-15.1 there vs
# -17.22 here — the two sources disagree by more than the ±0.5 tolerance
# used below, which is expected: drik_bala.py's docstring states AstroSage
# parity was NOT checked for this version; JHora v8 is the sole oracle.
_JHORA_DRIK: dict[str, dict[str, float]] = {
    # Hardest case first: Sheridan flips both Moon and Mercury's
    # benefic/malefic classification relative to the other 3 charts.
    "sheridan": {
        "sun": -25.36, "moon": 0.58, "mars": -24.48, "mercury": -13.44,
        "jupiter": -31.95, "venus": -22.69, "saturn": -24.95,
    },
    "sulabh": {
        "sun": -17.22, "moon": 5.84, "mars": 16.39, "mercury": -9.84,
        "jupiter": -15.24, "venus": 1.46, "saturn": 17.46,
    },
    "surbhi": {
        "sun": -7.72, "moon": 4.12, "mars": 13.38, "mercury": -6.37,
        "jupiter": -9.59, "venus": -8.40, "saturn": 0.42,
    },
    "david": {
        "sun": -21.45, "moon": -24.08, "mars": 8.26, "mercury": -20.09,
        "jupiter": -9.06, "venus": 5.48, "saturn": -5.32,
    },
}

_CHART_ARGS: dict[str, tuple] = {
    "sheridan": ("Sheridan", "27 May 1984", "08:00", "Durban, South Africa"),
    "sulabh":   ("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India"),
    "surbhi":   ("Surbhi", "11 Sep 1992", "10:30", "Patna, India"),
    "david":    ("David", "19 Jan 1976", "22:00", "London, UK"),
}


@pytest.fixture(scope="module")
def sheridan_drik():
    from agent.chart_calculator import calculate_chart
    return compute_drik_bala(calculate_chart(*_CHART_ARGS["sheridan"]))


@pytest.fixture(scope="module")
def sulabh_drik():
    from agent.chart_calculator import calculate_chart
    return compute_drik_bala(calculate_chart(*_CHART_ARGS["sulabh"]))


@pytest.fixture(scope="module")
def surbhi_drik():
    from agent.chart_calculator import calculate_chart
    return compute_drik_bala(calculate_chart(*_CHART_ARGS["surbhi"]))


@pytest.fixture(scope="module")
def david_drik():
    from agent.chart_calculator import calculate_chart
    return compute_drik_bala(calculate_chart(*_CHART_ARGS["david"]))


@pytest.fixture(scope="module")
def all_drik(sheridan_drik, sulabh_drik, surbhi_drik, david_drik):
    return {
        "sheridan": sheridan_drik,
        "sulabh": sulabh_drik,
        "surbhi": surbhi_drik,
        "david": david_drik,
    }


@pytest.mark.parametrize("chart_key", ["sheridan", "sulabh", "surbhi", "david"])
@pytest.mark.parametrize("planet", _PLANETS)
def test_jhora_parity(chart_key, planet, all_drik):
    got = all_drik[chart_key][planet]["drik"]
    expected = _JHORA_DRIK[chart_key][planet]
    assert got == pytest.approx(expected, abs=0.5), (
        f"{chart_key} {planet} drik: got {got:.4f}, expected {expected:.4f} "
        f"(JHora v8, tol ±0.5)"
    )


# ── Layer C: error contract + output shape ───────────────────────────────────

def test_missing_meta_raises_value_error():
    with pytest.raises(ValueError):
        compute_drik_bala({})


def test_missing_jd_ut_raises_value_error():
    with pytest.raises(ValueError):
        compute_drik_bala({"meta": {}})


def test_output_shape(sulabh_drik):
    assert set(sulabh_drik.keys()) == set(_PLANETS)
    for planet in _PLANETS:
        assert set(sulabh_drik[planet].keys()) == {"drik"}
        assert isinstance(sulabh_drik[planet]["drik"], float)


# ── Informational: known divergences (not asserted here) ─────────────────────
#
# - Mars 180-210 plateau (S=60) is untested by any of the 4 reference charts'
#   aspect pairs — see TestMarsDrishtiBoundaries.test_plateau_entry_at_180_
#   continuous_by_construction above. If a future 5th reference chart lands
#   an aspect pair in [180, 210), it becomes the first empirical check of
#   this segment.
# - AstroSage diverges from JHora on Drik Bala; JHora is the primary oracle
#   per this project's validation hierarchy (see drik_bala.py PROVENANCE
#   CAVEAT), so AstroSage parity is NOT expected and NOT tested here.
#   Example: Sulabh Saturn — AstroSage fixture (shadbala_fixtures.py) says
#   +10.89, JHora v8 (this file's oracle) says +17.46, delta +6.57 — well
#   outside this file's ±0.5 JHora tolerance, and expected to be.
