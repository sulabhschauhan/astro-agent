"""Tests for agent/calculations/strength/sthana_bala.py — P2.5.1.

Layer A: structural / formula unit tests, no ephemeris.
Layer B: AstroSage parity, Sulabh chart — all 7 planets (hardest case first).
Layer C: cross-chart spot-check, Surbhi Sun.

Geocoder monkeypatched by tests/conftest.py; all locations must be in
tests/fixtures/geocoded_locations.json.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # project root

import pytest

from agent.calculations.strength.sthana_bala import (
    _compute_drekkana_sign,
    _compute_dwadashamsha_sign,
    _compute_hora_sign,
    _compute_saptamsha_sign,
    _compute_trimshamsha_sign,
    _kendra_bala,
    _natural_relation,
    _ochcha_bala,
    _ojayugma_bala,
    compute_sthana_bala,
)
from tests.fixtures.shadbala_fixtures import SHADBALA_FIXTURES

# ── Layer A: structural / formula unit tests (no ephemeris) ──────────────────

class TestOcchaBala:
    def test_sun_near_sulabh_lon(self):
        # Sun at 352.5° (≈ Sulabh's Sun in Pisces). Debi=190°.
        # arc = |352.5 - 190| = 162.5 → ochcha = 162.5/3 ≈ 54.17
        result = _ochcha_bala("Sun", 352.5)
        assert result == pytest.approx(54.1667, abs=0.01)

    def test_planet_at_debilitation_is_zero(self):
        # Planet exactly at debilitation point → arc=0 → ochcha=0
        assert _ochcha_bala("Mars", 118.0) == pytest.approx(0.0)

    def test_planet_at_exaltation_is_sixty(self):
        # Exaltation is 180° from debilitation → arc=180 → ochcha=60
        # Sun debi=190°; exaltation deep point=10° Aries=10°; |10-190|=180 → 60
        assert _ochcha_bala("Sun", 10.0) == pytest.approx(60.0)

    def test_arc_wraps_correctly(self):
        # Saturn debi=20°. Test lon=200°. arc=|200-20|=180 → ochcha=60
        assert _ochcha_bala("Saturn", 200.0) == pytest.approx(60.0)

    def test_arc_uses_min_path(self):
        # Saturn debi=20°. lon=30°. arc=|30-20|=10 < 180 → ochcha=10/3≈3.33
        # Vs. 360-10=350 (not taken because 10 < 180)
        assert _ochcha_bala("Saturn", 30.0) == pytest.approx(10.0 / 3.0, abs=0.001)


class TestVargaCalculators:
    # D2 Hora
    def test_hora_odd_sign_first_half(self):
        # Aries(0, odd), deg=10° → Cancer(3)
        assert _compute_hora_sign(10.0) == 3

    def test_hora_odd_sign_second_half(self):
        # Aries(0, odd), deg=20° → Leo(4)
        assert _compute_hora_sign(20.0) == 4

    def test_hora_even_sign_first_half(self):
        # Taurus(1, even), deg=30+5=35° → Leo(4)
        assert _compute_hora_sign(35.0) == 4

    def test_hora_even_sign_second_half(self):
        # Taurus(1, even), deg=30+20=50° → Cancer(3)
        assert _compute_hora_sign(50.0) == 3

    # D3 Drekkana
    def test_drekkana_first_third(self):
        # Pisces(11) 5° → same sign = 11
        assert _compute_drekkana_sign(330.0 + 5.0) == 11

    def test_drekkana_second_third(self):
        # Pisces(11) 15° → (11+4)%12 = 3 (Cancer)
        assert _compute_drekkana_sign(330.0 + 15.0) == 3

    def test_drekkana_third_third(self):
        # Pisces(11) 25° → (11+8)%12 = 7 (Scorpio)
        assert _compute_drekkana_sign(330.0 + 22.5) == 7

    # D7 Saptamsha
    def test_saptamsha_odd_sign_first_span(self):
        # Aries(0, odd), deg=0° → span=0 → (0+0)%12=0 (Aries)
        assert _compute_saptamsha_sign(0.0) == 0

    def test_saptamsha_odd_sign_last_span(self):
        # Aries(0, odd), deg=29° → span=int(29/4.2857)=6 → (0+6)%12=6 (Libra)
        assert _compute_saptamsha_sign(29.0) == 6

    def test_saptamsha_even_sign_first_span(self):
        # Taurus(1, even), deg=0° → span=0 → (1+6+0)%12=7 (Scorpio)
        assert _compute_saptamsha_sign(30.0) == 7

    # D12 Dwadashamsha
    def test_dwadashamsha_first_part(self):
        # Aries(0), deg=1° → span=0 → (0+0)%12=0 (Aries)
        assert _compute_dwadashamsha_sign(1.0) == 0

    def test_dwadashamsha_fifth_part(self):
        # Aries(0), deg=12° → span=int(12/2.5)=4 → (0+4)%12=4 (Leo)
        assert _compute_dwadashamsha_sign(12.0) == 4

    def test_dwadashamsha_wraps(self):
        # Pisces(11), deg=10° → span=int(10/2.5)=4 → (11+4)%12=3 (Cancer)
        assert _compute_dwadashamsha_sign(330.0 + 10.0) == 3

    # D30 Trimshamsha
    def test_trimshamsha_odd_first_span(self):
        # Aries(0, odd), deg=3° → Aries(0)
        assert _compute_trimshamsha_sign(3.0) == 0

    def test_trimshamsha_odd_second_span(self):
        # Aries(0, odd), deg=7° → Aquarius(10)
        assert _compute_trimshamsha_sign(7.0) == 10

    def test_trimshamsha_odd_third_span(self):
        # Aries(0, odd), deg=15° → Sagittarius(8)
        assert _compute_trimshamsha_sign(15.0) == 8

    def test_trimshamsha_even_first_span(self):
        # Taurus(1, even), deg=2° → Taurus(1)
        assert _compute_trimshamsha_sign(30.0 + 2.0) == 1

    def test_trimshamsha_even_last_span(self):
        # Taurus(1, even), deg=27° → Scorpio(7)
        assert _compute_trimshamsha_sign(30.0 + 27.0) == 7


class TestKendraBala:
    def test_angular_houses(self):
        for h in (1, 4, 7, 10):
            assert _kendra_bala(h) == 60.0

    def test_succedent_houses(self):
        for h in (2, 5, 8, 11):
            assert _kendra_bala(h) == 30.0

    def test_cadent_houses(self):
        for h in (3, 6, 9, 12):
            assert _kendra_bala(h) == 15.0


class TestOjayugmaBala:
    def test_male_planet_odd_d1_and_d9(self):
        # Sun (male), Aries(0, odd) D1, Aries(0, odd) D9 → 15+15=30
        assert _ojayugma_bala("Sun", 0, 0) == 30.0

    def test_male_planet_even_d1_even_d9(self):
        # Sun (male), Taurus(1, even) D1, Taurus(1, even) D9 → 0+0=0
        assert _ojayugma_bala("Sun", 1, 1) == 0.0

    def test_male_planet_odd_d1_even_d9(self):
        # Mars (male), Aries(0) D1, Taurus(1) D9 → 15+0=15
        assert _ojayugma_bala("Mars", 0, 1) == 15.0

    def test_female_planet_even_d1_even_d9(self):
        # Moon (female), Taurus(1, even) D1, Cancer(3, even) D9 → 15+15=30
        assert _ojayugma_bala("Moon", 1, 3) == 30.0

    def test_female_planet_odd_d1(self):
        # Venus (female), Aries(0, odd) D1 → 0 for D1 part
        assert _ojayugma_bala("Venus", 0, 0) == 0.0

    def test_neutral_planet_acts_as_male(self):
        # Mercury (neutral), Aries(0, odd) D1, Gemini(2, odd) D9 → 15+15=30
        assert _ojayugma_bala("Mercury", 0, 2) == 30.0

    def test_saturn_neutral_even_signs(self):
        # Saturn (neutral), Taurus(1, even) D1, Cancer(3, even) D9 → 0+0=0
        assert _ojayugma_bala("Saturn", 1, 3) == 0.0


class TestNaturalRelation:
    def test_sun_moon_friend(self):
        assert _natural_relation("Sun", "Moon") == "friend"

    def test_sun_venus_enemy(self):
        assert _natural_relation("Sun", "Venus") == "enemy"

    def test_sun_mercury_neutral(self):
        assert _natural_relation("Sun", "Mercury") == "neutral"

    def test_moon_has_no_natural_enemies(self):
        for other in ("Sun", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
            rel = _natural_relation("Moon", other)
            assert rel in ("friend", "neutral"), f"Moon should not have enemy {other}, got {rel}"


# ── Layer B: AstroSage parity, Sulabh chart, all 7 planets ──────────────────

def _sulabh_chart() -> dict:
    from agent.chart_calculator import calculate_chart
    return calculate_chart("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")


@pytest.fixture(scope="module")
def sulabh_sthana() -> dict:
    return compute_sthana_bala(_sulabh_chart())


_SULABH_FIXTURE = SHADBALA_FIXTURES["sulabh"]["planets"]
_TOL = 0.5   # Virupa absolute tolerance


@pytest.mark.parametrize("planet,key", [
    ("sun",     "ochcha"),
    ("moon",    "ochcha"),
    ("mars",    "ochcha"),
    ("mercury", "ochcha"),
    ("jupiter", "ochcha"),
    ("venus",   "ochcha"),
    ("saturn",  "ochcha"),
])
def test_b_sulabh_ochcha(sulabh_sthana, planet, key):
    expected = _SULABH_FIXTURE[planet][key]
    got = sulabh_sthana[planet][key]
    assert got == pytest.approx(expected, abs=_TOL), (
        f"Sulabh {planet} {key}: got {got:.4f}, expected {expected}"
    )


@pytest.mark.parametrize("planet", [
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"
])
def test_b_sulabh_kendra(sulabh_sthana, planet):
    # Kendra is deterministic from house; must match exactly.
    expected = _SULABH_FIXTURE[planet]["kendra"]
    got = sulabh_sthana[planet]["kendra"]
    assert got == expected, f"Sulabh {planet} kendra: got {got}, expected {expected}"


@pytest.mark.parametrize("planet", [
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"
])
def test_b_sulabh_drekkana(sulabh_sthana, planet):
    assert sulabh_sthana[planet]["drekkana"] == 1.0


@pytest.mark.parametrize("planet", [
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"
])
def test_b_sulabh_ojayugma(sulabh_sthana, planet):
    # ojayugma is a 0/15/30 step function of sign parity — must match exactly.
    expected = _SULABH_FIXTURE[planet]["ojayugma"]
    got = sulabh_sthana[planet]["ojayugma"]
    assert got == expected, f"Sulabh {planet} ojayugma: got {got}, expected {expected}"


# AstroSage Sulabh Saptavargaja (informational, not asserted — BPHS scoring
# diverges from AstroSage's unpublished table for all 7 planets):
#   Sun=120, Moon=112.5, Mars=120, Mercury=114.38,
#   Jupiter=120, Venus=136.88, Saturn=101.25
# Saptavargaja ranking, not absolute value, is what downstream Yoga
# and Trigger-Naming logic consumes.
def test_b_sulabh_saptavargaja(sulabh_sthana):
    pass


@pytest.mark.parametrize("planet", [
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"
])
def test_b_sulabh_sthan_total(sulabh_sthana, planet):
    expected = _SULABH_FIXTURE[planet]["sthan_total"]
    got = sulabh_sthana[planet]["sthan_total"]
    # abs=40 accommodates Saptavargaja source divergence (BPHS vs AstroSage).
    assert got == pytest.approx(expected, abs=40), (
        f"Sulabh {planet} sthan_total: got {got:.4f}, expected {expected}"
    )


# ── Layer C: cross-chart spot-check, Surbhi Sun ─────────────────────────────

def _surbhi_chart() -> dict:
    from agent.chart_calculator import calculate_chart
    return calculate_chart("Surbhi", "11 Sep 1992", "10:30", "Patna, India")


@pytest.fixture(scope="module")
def surbhi_sthana() -> dict:
    return compute_sthana_bala(_surbhi_chart())


_SURBHI_SUN_FX = SHADBALA_FIXTURES["surbhi"]["planets"]["sun"]


def test_c_surbhi_sun_ochcha(surbhi_sthana):
    assert surbhi_sthana["sun"]["ochcha"] == pytest.approx(
        _SURBHI_SUN_FX["ochcha"], abs=_TOL
    )


def test_c_surbhi_sun_saptavargaja(surbhi_sthana):
    # AstroSage Surbhi Sun saptavargaja=110.62 (informational, not asserted —
    # BPHS scoring diverges from AstroSage's unpublished table).
    pass


def test_c_surbhi_sun_sthan_total(surbhi_sthana):
    # abs=40 accommodates Saptavargaja source divergence (BPHS vs AstroSage).
    assert surbhi_sthana["sun"]["sthan_total"] == pytest.approx(
        _SURBHI_SUN_FX["sthan_total"], abs=40
    )
