"""Tests for agent/calculations/yogas/catalog/pancha_mahapurusha.py — P3.

Layer A: Mercury/Virgo three-way dignity boundary (Bhadra Yoga) — hardest case,
         all three sub-ranges (Exalted/Moolatrikona/Own) share Virgo.
Layer B: Non-kendra rejection — same exalted Mercury/Virgo, all 8 non-kendra houses.
Layer C: Multi-yoga coexistence — two simultaneous, then all five ceiling case.
Layer D: Duplicate eligible planet → ValueError naming the planet.
Layer E: Ineligible planet filtering — Sun/Moon/Rahu/Ketu silently dropped.
Layer F: get_dignity_status error propagation → context-enriched ValueError.
Layer G: Empty input → empty tuple, no error.
Layer H: No-qualifying-dignity → kendra alone is not sufficient.
Layer I: Real-chart validation — 4 reference charts via calculate_chart().

Expected yogas in Layer I (derived from kendra_bala=60 in shadbala_fixtures.py +
ochcha/ojayugma cross-check + AstroSage Kundli PDF source):
  Sulabh  (ASC Sagittarius): 0 yogas — no eligible planet in kendra with
          qualifying dignity (Mars/2nd exalted, Mercury/4th debilitated,
          Saturn/1st in Sagittarius = no dignity). Confirmed: kundali_summary.txt
          "Other Yogas: NOT FOUND IN SOURCE."
  Surbhi  (ASC Libra):       Shasha — Saturn in Capricorn (4th kendra, own sign).
          Derived from kendra=60, ochcha=30.33 → Saturn at ~289° = Capricorn 19°.
  Sheridan (ASC Taurus):     Malavya — Venus in Taurus (1st kendra, own sign).
          Derived from kendra=60, ojayugma=30 (even sign), saptavargaja=120.
  David   (ASC Virgo):       Hamsa — Jupiter in Pisces (7th kendra, own sign).
          Derived from kendra=60, ochcha=26.3 → Jupiter at ~353.9° = Pisces 23°.

Geocoder monkeypatched by tests/conftest.py; all locations must be in
tests/fixtures/geocoded_locations.json.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest

from agent.calculations.yogas.catalog.pancha_mahapurusha import (
    ELIGIBLE_PLANETS,
    KENDRA_HOUSES,
    MahapurushaResult,
    PlanetPlacement,
    _QUALIFYING_DIGNITIES,
    _YOGA_NAMES,
    detect_pancha_mahapurusha,
)


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _build_eligible_placements(chart: dict) -> list[PlanetPlacement]:
    """Build PlanetPlacement list for eligible planets from a calculate_chart() result.

    calculate_chart() strips longitude from planetary_positions (sign/house/dignity only),
    so we re-derive degree_in_sign via a direct swe.calc_ut call on the chart's jd_ut —
    the same pattern used by sthana_bala.py and other strength modules.
    """
    import swisseph as swe

    _SWE_IDS = {
        "Mars":    swe.MARS,
        "Mercury": swe.MERCURY,
        "Jupiter": swe.JUPITER,
        "Venus":   swe.VENUS,
        "Saturn":  swe.SATURN,
    }

    jd_ut = chart["meta"]["jd_ut"]
    positions = chart["planetary_positions"]
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL

    placements = []
    for planet in ELIGIBLE_PLANETS:
        if planet not in positions:
            continue
        xx, _ = swe.calc_ut(jd_ut, _SWE_IDS[planet], flags)
        lon = xx[0] % 360
        placements.append(PlanetPlacement(
            planet=planet,
            sign=positions[planet]["sign"],
            degree_in_sign=lon % 30,
            house_from_lagna=positions[planet]["house"],
        ))
    return placements


# ── Module-scope real-chart fixtures ──────────────────────────────────────────

@pytest.fixture(scope="module")
def sulabh_placements():
    from agent.chart_calculator import calculate_chart
    chart = calculate_chart("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")
    return _build_eligible_placements(chart)


@pytest.fixture(scope="module")
def surbhi_placements():
    from agent.chart_calculator import calculate_chart
    chart = calculate_chart("Surbhi", "11 Sep 1992", "10:30", "Patna, India")
    return _build_eligible_placements(chart)


@pytest.fixture(scope="module")
def sheridan_placements():
    from agent.chart_calculator import calculate_chart
    chart = calculate_chart("Sheridan", "27 May 1984", "08:00", "Durban, South Africa")
    return _build_eligible_placements(chart)


@pytest.fixture(scope="module")
def david_placements():
    from agent.chart_calculator import calculate_chart
    chart = calculate_chart("David", "19 Jan 1976", "22:00", "London, UK")
    return _build_eligible_placements(chart)


# ── Layer A: Mercury/Virgo three-way dignity boundary (Bhadra Yoga) ───────────

@pytest.mark.parametrize("degree,expected_dignity", [
    (0.0,    "Exalted"),      # below MT start (15°) → Exalted
    (14.999, "Exalted"),      # just below MT start
    (15.0,   "Moolatrikona"), # MT start boundary (inclusive)
    (19.999, "Moolatrikona"), # just below MT end (20°)
    (20.0,   "Own"),          # Own start boundary (OWN_SIGNS Virgo 20-30)
    (29.999, "Own"),          # near sign boundary
])
def test_a_bhadra_virgo_all_sub_ranges_fire(degree, expected_dignity):
    """Bhadra fires at every Mercury/Virgo degree; dignity_status label matches the sub-range."""
    p = PlanetPlacement(planet="Mercury", sign="Virgo", degree_in_sign=degree, house_from_lagna=1)
    results = detect_pancha_mahapurusha([p])
    assert len(results) == 1
    r = results[0]
    assert r.yoga_name == "Bhadra"
    assert r.planet == "Mercury"
    assert r.sign == "Virgo"
    assert r.house_from_lagna == 1
    assert r.dignity_status == expected_dignity


def test_a_bhadra_gemini_own_kendra():
    """Bhadra fires for Mercury in Gemini (Own, no exalt/MT split) at a kendra house."""
    p = PlanetPlacement(planet="Mercury", sign="Gemini", degree_in_sign=10.0, house_from_lagna=4)
    results = detect_pancha_mahapurusha([p])
    assert len(results) == 1
    assert results[0].yoga_name == "Bhadra"
    assert results[0].sign == "Gemini"
    assert results[0].dignity_status == "Own"


# ── Layer B: Non-kendra rejection ─────────────────────────────────────────────

@pytest.mark.parametrize("house", [2, 3, 5, 6, 8, 9, 11, 12])
def test_b_non_kendra_exalted_mercury_no_yoga(house):
    """Exalted Mercury in Virgo fires no yoga when house_from_lagna is not a kendra."""
    p = PlanetPlacement(planet="Mercury", sign="Virgo", degree_in_sign=5.0, house_from_lagna=house)
    assert detect_pancha_mahapurusha([p]) == ()


# ── Layer C: Multi-yoga coexistence ───────────────────────────────────────────

def test_c_two_yogas_coexist():
    """Two qualifying placements both fire — guards the 'do NOT cap at 1' contract."""
    placements = [
        PlanetPlacement(planet="Mars",   sign="Aries",     degree_in_sign=5.0, house_from_lagna=1),
        PlanetPlacement(planet="Saturn", sign="Capricorn", degree_in_sign=5.0, house_from_lagna=10),
    ]
    results = detect_pancha_mahapurusha(placements)
    assert len(results) == 2
    names = {r.yoga_name for r in results}
    assert names == {"Ruchaka", "Shasha"}


def test_c_all_five_yogas_ceiling():
    """All five Pancha Mahapurusha yogas can coexist simultaneously in one input."""
    placements = [
        PlanetPlacement(planet="Mars",    sign="Aries",    degree_in_sign=5.0, house_from_lagna=1),
        PlanetPlacement(planet="Mercury", sign="Virgo",    degree_in_sign=5.0, house_from_lagna=4),
        PlanetPlacement(planet="Jupiter", sign="Cancer",   degree_in_sign=5.0, house_from_lagna=7),
        PlanetPlacement(planet="Venus",   sign="Libra",    degree_in_sign=5.0, house_from_lagna=10),
        PlanetPlacement(planet="Saturn",  sign="Aquarius", degree_in_sign=5.0, house_from_lagna=1),
    ]
    results = detect_pancha_mahapurusha(placements)
    assert len(results) == 5
    names = {r.yoga_name for r in results}
    assert names == {"Ruchaka", "Bhadra", "Hamsa", "Malavya", "Shasha"}
    planets = {r.planet for r in results}
    assert planets == set(ELIGIBLE_PLANETS)


# ── Layer D: Duplicate planet rejection ───────────────────────────────────────

def test_d_duplicate_mars_raises_with_name():
    """Two Mars entries raise ValueError and the message names 'Mars'."""
    placements = [
        PlanetPlacement(planet="Mars", sign="Aries", degree_in_sign=5.0, house_from_lagna=1),
        PlanetPlacement(planet="Mars", sign="Aries", degree_in_sign=5.0, house_from_lagna=1),
    ]
    with pytest.raises(ValueError, match="Mars"):
        detect_pancha_mahapurusha(placements)


def test_d_duplicate_ineligible_planet_is_not_duplicate_error():
    """Duplicate Sun entries do not raise — Sun is filtered before the duplicate check."""
    placements = [
        PlanetPlacement(planet="Sun", sign="Aries", degree_in_sign=10.0, house_from_lagna=1),
        PlanetPlacement(planet="Sun", sign="Aries", degree_in_sign=10.0, house_from_lagna=1),
    ]
    # Should return empty without error (both Sun entries silently dropped)
    assert detect_pancha_mahapurusha(placements) == ()


# ── Layer E: Ineligible planet silent filtering ────────────────────────────────

def test_e_sun_in_kendra_exalted_ignored():
    """Sun in Aries (exalted) at kendra house 1 is silently ignored, no error."""
    p = PlanetPlacement(planet="Sun", sign="Aries", degree_in_sign=10.0, house_from_lagna=1)
    assert detect_pancha_mahapurusha([p]) == ()


def test_e_moon_in_kendra_exalted_ignored():
    """Moon in Taurus (exalted) at kendra house 7 is silently ignored, no error."""
    p = PlanetPlacement(planet="Moon", sign="Taurus", degree_in_sign=3.0, house_from_lagna=7)
    assert detect_pancha_mahapurusha([p]) == ()


def test_e_rahu_ketu_in_kendra_ignored():
    """Rahu and Ketu in kendra houses are silently ignored before any dignity check."""
    placements = [
        PlanetPlacement(planet="Rahu", sign="Gemini",      degree_in_sign=5.0, house_from_lagna=1),
        PlanetPlacement(planet="Ketu", sign="Sagittarius", degree_in_sign=5.0, house_from_lagna=7),
    ]
    assert detect_pancha_mahapurusha(placements) == ()


def test_e_ineligible_mixed_with_eligible():
    """Ineligible planets mixed in are silently dropped; eligible planets still evaluated."""
    placements = [
        PlanetPlacement(planet="Sun",  sign="Aries", degree_in_sign=10.0, house_from_lagna=1),
        PlanetPlacement(planet="Mars", sign="Aries", degree_in_sign=5.0,  house_from_lagna=1),
    ]
    results = detect_pancha_mahapurusha(placements)
    assert len(results) == 1
    assert results[0].yoga_name == "Ruchaka"


# ── Layer F: get_dignity_status error propagation ─────────────────────────────

def test_f_invalid_sign_raises_with_context():
    """Invalid sign on a kendra-placed eligible planet raises ValueError naming planet, sign, degree."""
    p = PlanetPlacement(planet="Mercury", sign="BogusSign", degree_in_sign=5.0, house_from_lagna=1)
    with pytest.raises(ValueError) as exc_info:
        detect_pancha_mahapurusha([p])
    msg = str(exc_info.value)
    assert "Mercury" in msg
    assert "BogusSign" in msg
    assert "5.0" in msg


def test_f_non_kendra_invalid_sign_no_error():
    """Invalid sign on a non-kendra eligible planet does NOT raise — kendra gate fires first."""
    p = PlanetPlacement(planet="Mercury", sign="BogusSign", degree_in_sign=5.0, house_from_lagna=2)
    # house=2 is not a kendra; get_dignity_status is never reached
    assert detect_pancha_mahapurusha([p]) == ()


# ── Layer G: Empty input ───────────────────────────────────────────────────────

def test_g_empty_list_returns_empty_tuple():
    """Empty input list returns empty tuple without error."""
    assert detect_pancha_mahapurusha([]) == ()


# ── Layer H: No qualifying dignity ────────────────────────────────────────────

def test_h_mars_gemini_kendra_no_yoga():
    """Mars in Gemini (no special dignity) at kendra house fires no yoga."""
    p = PlanetPlacement(planet="Mars", sign="Gemini", degree_in_sign=10.0, house_from_lagna=1)
    assert detect_pancha_mahapurusha([p]) == ()


def test_h_saturn_cancer_kendra_no_yoga():
    """Saturn in Cancer (no special dignity) at kendra house fires no yoga."""
    p = PlanetPlacement(planet="Saturn", sign="Cancer", degree_in_sign=10.0, house_from_lagna=10)
    assert detect_pancha_mahapurusha([p]) == ()


def test_h_jupiter_debilitated_kendra_no_yoga():
    """Jupiter in Capricorn (debilitated) at kendra house fires no yoga — Debilitated is not qualifying."""
    p = PlanetPlacement(planet="Jupiter", sign="Capricorn", degree_in_sign=5.0, house_from_lagna=7)
    assert detect_pancha_mahapurusha([p]) == ()


# ── Layer I: Real-chart validation ────────────────────────────────────────────

class TestRealCharts:
    def test_i_sulabh_no_yogas(self, sulabh_placements):
        """Sulabh (ASC Sagittarius): 0 Pancha Mahapurusha yogas. No eligible planet in kendra
        with qualifying dignity — Mars exalted in 2nd, Mercury debilitated in 4th, Saturn
        in 1st with no dignity (Sagittarius). Confirmed: AstroSage source 'Other Yogas: NOT FOUND.'
        """
        results = detect_pancha_mahapurusha(sulabh_placements)
        assert results == ()

    def test_i_surbhi_shasha_yoga(self, surbhi_placements):
        """Surbhi (ASC Libra): Shasha Yoga — Saturn in Capricorn (4th house, own sign).
        Derived from kendra_bala=60 and ochcha=30.33 → Saturn at ~Capricorn 19°.
        """
        results = detect_pancha_mahapurusha(surbhi_placements)
        assert len(results) == 1
        r = results[0]
        assert r.yoga_name == "Shasha"
        assert r.planet == "Saturn"
        assert r.sign == "Capricorn"
        assert r.house_from_lagna == 4
        assert r.dignity_status == "Own"

    def test_i_sheridan_malavya_yoga(self, sheridan_placements):
        """Sheridan (ASC Taurus): Malavya Yoga — Venus in Taurus (1st house, own sign).
        Derived from kendra_bala=60, ojayugma=30 (even sign), saptavargaja=120.
        """
        results = detect_pancha_mahapurusha(sheridan_placements)
        assert len(results) == 1
        r = results[0]
        assert r.yoga_name == "Malavya"
        assert r.planet == "Venus"
        assert r.sign == "Taurus"
        assert r.house_from_lagna == 1
        assert r.dignity_status == "Own"

    def test_i_david_hamsa_yoga(self, david_placements):
        """David (ASC Virgo): Hamsa Yoga — Jupiter in Pisces (7th house, own sign).
        Derived from kendra_bala=60 and ochcha=26.3 → Jupiter at ~Pisces 23°.
        """
        results = detect_pancha_mahapurusha(david_placements)
        assert len(results) == 1
        r = results[0]
        assert r.yoga_name == "Hamsa"
        assert r.planet == "Jupiter"
        assert r.sign == "Pisces"
        assert r.house_from_lagna == 7
        assert r.dignity_status == "Own"

    def test_i_all_results_structurally_valid(
        self, sulabh_placements, surbhi_placements, sheridan_placements, david_placements
    ):
        """All four real-chart results have valid yoga_name, planet in ELIGIBLE_PLANETS,
        house_from_lagna in KENDRA_HOUSES, and dignity_status in qualifying set.
        """
        all_placements = {
            "sulabh":   sulabh_placements,
            "surbhi":   surbhi_placements,
            "sheridan": sheridan_placements,
            "david":    david_placements,
        }
        for chart_name, placements in all_placements.items():
            results = detect_pancha_mahapurusha(placements)
            for r in results:
                assert r.yoga_name in _YOGA_NAMES.values(), \
                    f"{chart_name}: unexpected yoga_name {r.yoga_name!r}"
                assert r.planet in ELIGIBLE_PLANETS, \
                    f"{chart_name}: unexpected planet {r.planet!r}"
                assert r.house_from_lagna in KENDRA_HOUSES, \
                    f"{chart_name}: house {r.house_from_lagna} not a kendra"
                assert r.dignity_status in _QUALIFYING_DIGNITIES, \
                    f"{chart_name}: dignity {r.dignity_status!r} not qualifying"
