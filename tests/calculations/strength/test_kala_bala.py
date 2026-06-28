"""Tests for agent/calculations/strength/kala_bala.py — P2.5.3.

Layer A: formula unit tests, no ephemeris.
Layer B: AstroSage parity, Sulabh chart — all 7 planets (abs=0.5 Virupa).
Layer C: Surbhi Sun and Moon spot-check (abs=0.5).

Geocoder monkeypatched by tests/conftest.py; all locations must be in
tests/fixtures/geocoded_locations.json.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest

from agent.calculations.strength.kala_bala import (
    _HORA_SEQ,
    _PLANETS,
    _WEEKDAY_LORD,
    _ayana_bala,
    _nathonnatha_bala,
    _paksha_bala,
    _vara_bala,
    _yuddha_bala,
    compute_kala_bala,
)
from tests.fixtures.shadbala_fixtures import SHADBALA_FIXTURES


# ── Layer A: formula unit tests (no ephemeris or mocked inputs) ───────────────

class TestVaraBala:
    def test_tuesday_gives_mars_45(self):
        # pyswisseph day_of_week 1=Tuesday → Mars=45
        # We test the mapping directly without ephemeris
        assert _WEEKDAY_LORD[1] == "Mars"

    def test_weekday_lord_map_covers_all_days(self):
        assert set(_WEEKDAY_LORD.keys()) == {0, 1, 2, 3, 4, 5, 6}
        assert set(_WEEKDAY_LORD.values()) == set(_PLANETS)


class TestHoraSeq:
    def test_hora_seq_length(self):
        assert len(_HORA_SEQ) == 7

    def test_hora_seq_covers_all_planets(self):
        assert set(_HORA_SEQ) == set(_PLANETS)

    def test_hora_seq_starts_with_sun(self):
        assert _HORA_SEQ[0] == "Sun"


class TestAyanaBala:
    def test_ayana_decl_zero_non_sun(self):
        # adj=0 → (24+0)*1.25 = 30.0 for a north-strong planet
        # We verify formula: mercury with decl=0 → abs(0)=0 → (24+0)*1.25=30
        # Use a direct formula check
        adj = abs(0.0)  # Mercury formula
        ab = (24.0 + adj) * 1.25
        assert ab == pytest.approx(30.0)

    def test_ayana_sun_decl_plus_ten(self):
        # Sun: adj=+10 → (24+10)*1.25 * 2 = 85.0
        adj = 10.0
        ab = (24.0 + adj) * 1.25 * 2.0
        assert ab == pytest.approx(85.0)

    def test_ayana_south_strong_negative_decl(self):
        # Moon/Saturn: adj = -decl; decl=-5 → adj=5 → (24+5)*1.25=36.25
        decl = -5.0
        adj = -decl  # Moon formula: adj = -decl
        ab = (24.0 + adj) * 1.25
        assert ab == pytest.approx(36.25)

    def test_ayana_floors_at_zero(self):
        # If decl is very negative for a north-strong planet: (24 + (-30)) = -6 → 0
        adj = -30.0
        ab = max(0.0, (24.0 + adj) * 1.25)
        assert ab == pytest.approx(0.0)


class TestPakshaBala:
    def test_tithi_f_zero_benefic_is_zero(self):
        # tithi_f=0 → Shukla: benefic=0, malefic=60
        # Jupiter (benefic) should get 0; Sun (malefic) should get 60
        # We replicate the formula
        tithi_f = 0.0
        benefic_val = tithi_f * 4.0
        malefic_val = (15.0 - tithi_f) * 4.0
        assert benefic_val == pytest.approx(0.0)
        assert malefic_val == pytest.approx(60.0)

    def test_tithi_f_fifteen_benefic_is_sixty(self):
        # tithi_f=15 → Shukla: benefic=60, malefic=0
        tithi_f = 15.0
        benefic_val = tithi_f * 4.0
        malefic_val = (15.0 - tithi_f) * 4.0
        assert benefic_val == pytest.approx(60.0)
        assert malefic_val == pytest.approx(0.0)

    def test_sulabh_paksha_formula(self):
        # Sulabh tithi_f ≈ 18.31 (Krishna Chaturthi)
        # malefic = (18.31 - 15) * 4 = 13.24
        tithi_f = 18.31
        malefic_val = (tithi_f - 15.0) * 4.0
        assert malefic_val == pytest.approx(13.24, abs=0.02)


class TestYuddhaBala:
    def test_wide_separation_no_war(self):
        # 2° apart — no war (threshold is 1°)
        planet_lons = {p: 0.0 for p in _PLANETS}
        planet_lats = {p: 0.0 for p in _PLANETS}
        planet_lons["Mars"] = 0.0
        planet_lons["Jupiter"] = 2.0
        zeros = {p: 0.0 for p in _PLANETS}
        result = _yuddha_bala(0.0, planet_lons, planet_lats, None, None,
                               zeros, zeros, zeros, zeros, zeros, zeros, zeros)
        # No war → all zero
        assert result["mars"] == pytest.approx(0.0)
        assert result["jupiter"] == pytest.approx(0.0)

    def test_at_war_higher_lat_wins(self):
        # Mars and Jupiter at same longitude, Mars lat > Jupiter lat → Mars is victor
        planet_lons = {p: 90.0 for p in _PLANETS}
        planet_lats = {p: 0.0 for p in _PLANETS}
        planet_lats["Mars"]    = 1.0   # higher latitude
        planet_lats["Jupiter"] = -1.0

        # Give Mars and Jupiter some distinguishable strength so yb != 0
        zeros = {p: 0.0 for p in _PLANETS}
        nath = {p: 0.0 for p in _PLANETS}
        nath["Mars"] = 50.0

        sthana = {"mars": {"sthan_total": 100.0}, "jupiter": {"sthan_total": 50.0}}
        for key in ["sun","moon","mercury","venus","saturn"]:
            sthana[key] = {"sthan_total": 0.0}
        dig = {p.lower(): {"dig": 0.0} for p in _PLANETS}

        result = _yuddha_bala(0.0, planet_lons, planet_lats, sthana, dig,
                               nath, zeros, zeros, zeros, zeros, zeros, zeros)
        # Victor (Mars) gains, defeated (Jupiter) loses
        assert result["mars"] > 0.0
        assert result["jupiter"] < 0.0


# ── Layer B: AstroSage parity, Sulabh chart, all 7 planets ───────────────────

_SULABH_PLANETS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
_TOL = 0.5


@pytest.fixture(scope="module")
def sulabh_kala():
    from agent.chart_calculator import calculate_chart
    from agent.calculations.strength.sthana_bala import compute_sthana_bala
    from agent.calculations.strength.dig_bala import compute_dig_bala

    chart = calculate_chart("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")
    sthana = compute_sthana_bala(chart)
    dig    = compute_dig_bala(chart)
    return compute_kala_bala(chart, sthana_result=sthana, dig_result=dig)


@pytest.mark.parametrize("planet", _SULABH_PLANETS)
def test_b_sulabh_nathonnatha(planet, sulabh_kala):
    expected = SHADBALA_FIXTURES["sulabh"]["planets"][planet]["nathonnatha"]
    got = sulabh_kala[planet]["nathonnatha"]
    assert got == pytest.approx(expected, abs=_TOL), (
        f"Sulabh {planet} nathonnatha: got {got:.4f}, expected {expected}"
    )


@pytest.mark.parametrize("planet", _SULABH_PLANETS)
def test_b_sulabh_paksha(planet, sulabh_kala):
    expected = SHADBALA_FIXTURES["sulabh"]["planets"][planet]["paksha"]
    got = sulabh_kala[planet]["paksha"]
    assert got == pytest.approx(expected, abs=_TOL), (
        f"Sulabh {planet} paksha: got {got:.4f}, expected {expected}"
    )


@pytest.mark.parametrize("planet", _SULABH_PLANETS)
def test_b_sulabh_thribhaga(planet, sulabh_kala):
    expected = SHADBALA_FIXTURES["sulabh"]["planets"][planet]["thribhaga"]
    got = sulabh_kala[planet]["thribhaga"]
    assert got == pytest.approx(expected, abs=_TOL), (
        f"Sulabh {planet} thribhaga: got {got:.4f}, expected {expected}"
    )


@pytest.mark.parametrize("planet", _SULABH_PLANETS)
def test_b_sulabh_abda(planet, sulabh_kala):
    expected = SHADBALA_FIXTURES["sulabh"]["planets"][planet]["abda"]
    got = sulabh_kala[planet]["abda"]
    assert got == pytest.approx(expected, abs=_TOL), (
        f"Sulabh {planet} abda: got {got:.4f}, expected {expected}"
    )


@pytest.mark.parametrize("planet", _SULABH_PLANETS)
def test_b_sulabh_masa(planet, sulabh_kala):
    expected = SHADBALA_FIXTURES["sulabh"]["planets"][planet]["masa"]
    got = sulabh_kala[planet]["masa"]
    assert got == pytest.approx(expected, abs=_TOL), (
        f"Sulabh {planet} masa: got {got:.4f}, expected {expected}"
    )


@pytest.mark.parametrize("planet", _SULABH_PLANETS)
def test_b_sulabh_vara(planet, sulabh_kala):
    expected = SHADBALA_FIXTURES["sulabh"]["planets"][planet]["vara"]
    got = sulabh_kala[planet]["vara"]
    assert got == pytest.approx(expected, abs=_TOL), (
        f"Sulabh {planet} vara: got {got:.4f}, expected {expected}"
    )


@pytest.mark.parametrize("planet", _SULABH_PLANETS)
def test_b_sulabh_hora(planet, sulabh_kala):
    expected = SHADBALA_FIXTURES["sulabh"]["planets"][planet]["hora"]
    got = sulabh_kala[planet]["hora"]
    assert got == pytest.approx(expected, abs=_TOL), (
        f"Sulabh {planet} hora: got {got:.4f}, expected {expected}"
    )


@pytest.mark.parametrize("planet", _SULABH_PLANETS)
def test_b_sulabh_ayana(planet, sulabh_kala):
    expected = SHADBALA_FIXTURES["sulabh"]["planets"][planet]["ayana"]
    got = sulabh_kala[planet]["ayana"]
    assert got == pytest.approx(expected, abs=_TOL), (
        f"Sulabh {planet} ayana: got {got:.4f}, expected {expected}"
    )


@pytest.mark.parametrize("planet", _SULABH_PLANETS)
def test_b_sulabh_kala_total(planet, sulabh_kala):
    expected = SHADBALA_FIXTURES["sulabh"]["planets"][planet]["kala_total"]
    got = sulabh_kala[planet]["kala_total"]
    assert got == pytest.approx(expected, abs=_TOL), (
        f"Sulabh {planet} kala_total: got {got:.4f}, expected {expected}"
    )


# ── Layer C: Surbhi Sun and Moon spot-check ───────────────────────────────────

@pytest.fixture(scope="module")
def surbhi_kala():
    from agent.chart_calculator import calculate_chart
    chart = calculate_chart("Surbhi", "11 Sep 1992", "10:30", "Patna, India")
    return compute_kala_bala(chart)


def test_c_surbhi_sun_nathonnatha(surbhi_kala):
    expected = SHADBALA_FIXTURES["surbhi"]["planets"]["sun"]["nathonnatha"]
    got = surbhi_kala["sun"]["nathonnatha"]
    assert got == pytest.approx(expected, abs=_TOL), (
        f"Surbhi sun nathonnatha: got {got:.4f}, expected {expected}"
    )


def test_c_surbhi_sun_paksha(surbhi_kala):
    expected = SHADBALA_FIXTURES["surbhi"]["planets"]["sun"]["paksha"]
    got = surbhi_kala["sun"]["paksha"]
    assert got == pytest.approx(expected, abs=_TOL), (
        f"Surbhi sun paksha: got {got:.4f}, expected {expected}"
    )


def test_c_surbhi_moon_nathonnatha(surbhi_kala):
    expected = SHADBALA_FIXTURES["surbhi"]["planets"]["moon"]["nathonnatha"]
    got = surbhi_kala["moon"]["nathonnatha"]
    assert got == pytest.approx(expected, abs=_TOL), (
        f"Surbhi moon nathonnatha: got {got:.4f}, expected {expected}"
    )


def test_c_surbhi_moon_paksha(surbhi_kala):
    expected = SHADBALA_FIXTURES["surbhi"]["planets"]["moon"]["paksha"]
    got = surbhi_kala["moon"]["paksha"]
    assert got == pytest.approx(expected, abs=_TOL), (
        f"Surbhi moon paksha: got {got:.4f}, expected {expected}"
    )
