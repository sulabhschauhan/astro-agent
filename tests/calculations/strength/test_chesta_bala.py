"""Tests for agent/calculations/strength/chesta_bala.py — P2.5.4.

Layer A: structural unit tests (A1-A3 use real ephemeris at J2000 for Tara
         Graha paths; A4-A5 monkeypatch swe.calc_ut to inject synthetic
         Moon/Sun positions for paksha-branch isolation).
Layer B: AstroSage parity, Sulabh chart — all 7 planets.
         Sun tolerance ±40.0 (accepted BPHS-vs-AstroSage gap).
         Mercury tolerance ±8.0 (synodic-midpoint approximation error).
Layer C: cross-chart spot-checks (Surbhi Moon, David Moon skipped, Surbhi Mars).

Note on ayana_result key casing: chesta_bala.py line 75 accesses
ayana_result["Sun"] (capitalized). The test-prompt fixture snippet omitted
.capitalize() — that is a typo in the prompt. All fixtures below use
{p.capitalize(): kala[p]["ayana"] for p in kala} to match the implementation.

Geocoder monkeypatched by tests/conftest.py; all locations must be in
tests/fixtures/geocoded_locations.json.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest

from agent.calculations.strength.chesta_bala import compute_chesta_bala
from tests.fixtures.shadbala_fixtures import SHADBALA_FIXTURES


# ── Shared helpers ────────────────────────────────────────────────────────────

_PLANETS_LOWER = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]

# J2000: no geocoder call; Tara Graha paths use real ephemeris
_MINIMAL_CHART = {"meta": {"jd_ut": 2451545.0}}


def _make_inputs(paksha_val: float = 20.0, ayana_val: float = 30.0):
    """Synthetic paksha/ayana dicts for Layer A structural tests."""
    paksha = {p: paksha_val for p in _PLANETS_LOWER}
    # chesta_bala.py line 75: ayana_result["Sun"] — must use capitalized keys
    ayana = {p.capitalize(): ayana_val for p in _PLANETS_LOWER}
    return paksha, ayana


def _build_chesta(chart_data: dict, kala_result: dict) -> dict:
    """Extract paksha/ayana from kala_result and return compute_chesta_bala()."""
    paksha = {p: kala_result[p]["paksha"] for p in kala_result}
    # chesta_bala.py accesses ayana_result["Sun"] (capitalized — confirmed Step 0).
    ayana = {p.capitalize(): kala_result[p]["ayana"] for p in kala_result}
    return compute_chesta_bala(chart_data, paksha, ayana)


# ── Layer A: structural unit tests ───────────────────────────────────────────

class TestA1Keys:
    def test_a1_seven_lowercase_keys(self):
        paksha, ayana = _make_inputs()
        result = compute_chesta_bala(_MINIMAL_CHART, paksha, ayana)
        assert set(result.keys()) == set(_PLANETS_LOWER)


class TestA2Shape:
    def test_a2_each_value_has_chesta_key(self):
        paksha, ayana = _make_inputs()
        result = compute_chesta_bala(_MINIMAL_CHART, paksha, ayana)
        for planet in _PLANETS_LOWER:
            assert "chesta" in result[planet], f"{planet} missing 'chesta' key"


class TestA3Range:
    def test_a3_all_chesta_in_range_0_to_60(self):
        # ayana["Sun"]=30.0 → sun chesta=30.0 ≤ 60.
        # Moon chesta = 20.0 or 40.0 depending on J2000 paksha state.
        # Tara Grahas: CK/3 always in [0, 60] by construction.
        paksha, ayana = _make_inputs(paksha_val=20.0, ayana_val=30.0)
        result = compute_chesta_bala(_MINIMAL_CHART, paksha, ayana)
        for planet in _PLANETS_LOWER:
            val = result[planet]["chesta"]
            assert isinstance(val, float), f"{planet} chesta is not a float"
            assert 0.0 <= val <= 60.0, (
                f"{planet} chesta={val:.4f} outside [0.0, 60.0]"
            )


class TestA4MoonKrishna:
    def test_a4_krishna_moon_chesta_inverts_paksha(self, monkeypatch):
        # Krishna: (moon_lon - sun_lon) % 360 = (200 - 10) % 360 = 190 > 180
        # → chesta = 60 - paksha["moon"]
        import agent.calculations.strength.chesta_bala as cb

        def _fake_calc_ut(jd, planet, flags):
            if planet == cb.swe.MOON:
                return ([200.0, 0.0, 0.0, 0.0, 0.0, 0.0], 0)
            if planet == cb.swe.SUN:
                return ([10.0, 0.0, 0.0, 0.0, 0.0, 0.0], 0)
            return ([90.0, 0.0, 0.0, 0.0, 0.0, 0.0], 0)

        monkeypatch.setattr(cb.swe, "calc_ut", _fake_calc_ut)
        paksha = {p: 15.0 for p in _PLANETS_LOWER}
        ayana = {p.capitalize(): 30.0 for p in _PLANETS_LOWER}
        result = compute_chesta_bala(_MINIMAL_CHART, paksha, ayana)
        assert result["moon"]["chesta"] == pytest.approx(45.0)  # 60 - 15


class TestA5MoonShukla:
    def test_a5_shukla_moon_chesta_equals_paksha(self, monkeypatch):
        # Shukla: (moon_lon - sun_lon) % 360 = (100 - 10) % 360 = 90 < 180
        # → chesta = paksha["moon"]
        import agent.calculations.strength.chesta_bala as cb

        def _fake_calc_ut(jd, planet, flags):
            if planet == cb.swe.MOON:
                return ([100.0, 0.0, 0.0, 0.0, 0.0, 0.0], 0)
            if planet == cb.swe.SUN:
                return ([10.0, 0.0, 0.0, 0.0, 0.0, 0.0], 0)
            return ([90.0, 0.0, 0.0, 0.0, 0.0, 0.0], 0)

        monkeypatch.setattr(cb.swe, "calc_ut", _fake_calc_ut)
        paksha = {p: 40.0 for p in _PLANETS_LOWER}
        ayana = {p.capitalize(): 30.0 for p in _PLANETS_LOWER}
        result = compute_chesta_bala(_MINIMAL_CHART, paksha, ayana)
        assert result["moon"]["chesta"] == pytest.approx(40.0)  # same as paksha


# ── Layer B: AstroSage parity, Sulabh chart, all 7 planets ───────────────────

_CHESTA_TOL: dict[str, float] = {
    "sun":      40.0,  # accepted gap — BPHS Ayana path vs AstroSage undocumented method
    "moon":      1.0,
    "mercury":   8.0,  # synodic-midpoint approximation, high-eccentricity orbit
    "mars":      3.0,
    "jupiter":   3.0,
    "venus":     3.0,
    "saturn":    3.0,
}


@pytest.fixture(scope="module")
def sulabh_chesta():
    from agent.chart_calculator import calculate_chart
    from agent.calculations.strength.kala_bala import compute_kala_bala

    chart = calculate_chart("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")
    kala = compute_kala_bala(chart)
    return _build_chesta(chart, kala)


@pytest.mark.parametrize("planet", _PLANETS_LOWER)
def test_b_sulabh_chesta(planet, sulabh_chesta):
    expected = SHADBALA_FIXTURES["sulabh"]["planets"][planet]["chesta"]
    got = sulabh_chesta[planet]["chesta"]
    tol = _CHESTA_TOL[planet]

    if planet == "sun":
        # Sun Chesta: accepted gap — BPHS rule (Ayana Bala) vs AstroSage undocumented
        # seeghrochcha. Delta ~40 Virupa. See CLAUDE.md §Chesta Bala. Informational only.
        assert got == pytest.approx(expected, abs=tol), (
            f"Sulabh sun chesta: got {got:.4f}, expected {expected:.4f} "
            f"(accepted gap ±40.0; BPHS Ayana path vs AstroSage undocumented method)"
        )
    elif planet == "mercury":
        # Mercury Chesta: synodic-midpoint approximation error. Canary=10.92, fixture=3.37.
        # Delta within expected range for half-synodic method on high-eccentricity orbit.
        # Tolerance widened to ±8.0 per design-chat decision Session 33.
        assert got == pytest.approx(expected, abs=tol), (
            f"Sulabh mercury chesta: got {got:.4f}, expected {expected:.4f} "
            f"(synodic-approx tolerance ±8.0)"
        )
    else:
        assert got == pytest.approx(expected, abs=tol), (
            f"Sulabh {planet} chesta: got {got:.4f}, expected {expected:.4f}"
        )


# ── Layer C: cross-chart spot-checks ──────────────────────────────────────────

@pytest.fixture(scope="module")
def surbhi_chesta():
    from agent.chart_calculator import calculate_chart
    from agent.calculations.strength.kala_bala import compute_kala_bala

    chart = calculate_chart("Surbhi", "11 Sep 1992", "10:30", "Patna, India")
    kala = compute_kala_bala(chart)
    return _build_chesta(chart, kala)


def test_c1_surbhi_moon_shukla_chesta(surbhi_chesta):
    # Surbhi: Shukla paksha → chesta = paksha = 56.75
    expected = SHADBALA_FIXTURES["surbhi"]["planets"]["moon"]["chesta"]  # 56.75
    got = surbhi_chesta["moon"]["chesta"]
    assert got == pytest.approx(expected, abs=1.0), (
        f"Surbhi moon chesta: got {got:.4f}, expected {expected:.4f}"
    )


def test_c2_david_moon_krishna_chesta():
    # David: Krishna paksha (fixture paksha=12.07 → chesta=47.93 = 60-12.07).
    # Birth location is "unknown" in shadbala_fixtures.py meta — cannot compute ephemeris.
    pytest.skip("David birth location unknown — cannot compute ephemeris")


def test_c3_surbhi_mars_chesta(surbhi_chesta):
    # Surbhi Mars — expected 35.19, tolerance ±3.0
    expected = SHADBALA_FIXTURES["surbhi"]["planets"]["mars"]["chesta"]  # 35.19
    got = surbhi_chesta["mars"]["chesta"]
    assert got == pytest.approx(expected, abs=3.0), (
        f"Surbhi mars chesta: got {got:.4f}, expected {expected:.4f}"
    )


# Sheridan Venus Chesta: fixture not available in PDF; skipped (GAP-3).
# Sheridan birth location is also "unknown" in shadbala_fixtures.py meta —
# ephemeris computation not possible regardless of fixture availability.
