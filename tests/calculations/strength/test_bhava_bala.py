"""Tests for agent/calculations/strength/bhava_bala.py.

Layer A: Full 12-house Bhavadhipati Bala validation, all 4 charts (48
         parametrized assertions). Oracle: AstroSage fixture shadbala_virupa.
         Uses fixture-based shadbala_totals (NOT live compute_shadbala_totals)
         because the V1 Drik Bala stub causes up to ~20 Virupa divergence per
         planet, making ±0.5 tolerance infeasible with live compute.

Layer B: Same-lord pair — two houses sharing a lord return identical Virupa.

Layer C: Error handling for compute_bhavadhipati_bala — 4 ValueError scenarios.

Layer D: Output shape — exactly keys 1-12, all float values.

Layer E: Live-compute wiring smoke (compute_shadbala_totals → bhavadhipati).

Layer F: compute_bhava_dig_bala — real implementation (PyJHora rasi-animal-
         group formula, Porphyry cusps). Exact-match against AstroSage's
         BhavBala Bhavdig row for all 4 charts (clean multiples of 10, no
         tolerance band) + ValueError on malformed input.

Layer G: compute_bhava_drishti_bala kernel structural spot-checks (Session
         53, no ephemeris) — exact values at the add-on-special boundaries
         (Saturn/Mars/Jupiter) and one plain-base case. Deliberately does
         NOT assert continuity at these boundaries (unlike
         test_drik_bala.py's Layer A) — the bhava kernel's add-on specials
         are intentionally discontinuous; see Layer G's own module note.

Layer H: compute_bhava_drishti_bala — real implementation (Session 53).
         AstroSage BhavBala oracle parity, all 4 charts, 48 parametrized
         assertions, tolerance +/-0.5 Virupa (mirrors test_drik_bala.py's
         Session 46 JHora parity convention; measured max |delta| 0.15 on
         repo ephemeris this session, 3x headroom). Hardest case first:
         Sheridan (the only chart where Moon classifies malefic).

Layer I: compute_bhava_bala_totals aggregator — arithmetic correctness
         (bhava_dig AND bhava_drishti are both now real; total_virupa
         includes all three components, structurally recomputed from the
         sub-components themselves, not magic numbers), rank
         full-permutation validity, and caveat/stub-flag integrity
         (dig_is_stubbed and drishti_is_stubbed are both always False).

Session 53 note: the old Layer G (compute_bhava_drishti_bala V1 stub,
always-0.0 shape tests) is DELETED, not ported — the stub itself no
longer exists (bhava_bala.py now has a real implementation with a
different signature: house_cusps + planet_lons, not house_signs).

Reference: reference_charts.md for Lagna signs.
  Sulabh=Sagittarius, Surbhi=Libra, Sheridan=Taurus, David=Virgo
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest
import swisseph as swe

from agent.calculations.helpers import ephemeris
from agent.calculations.strength.bhava_bala import (
    compute_bhavadhipati_bala,
    compute_bhava_dig_bala,
    compute_bhava_drishti_bala,
    compute_bhava_bala_totals,
    _sphuta_bhava_drishti,
)
from agent.chart_calculator import SIGN_LORDS, calculate_chart, compute_porphyry_house_cusps
from tests.fixtures.shadbala_fixtures import SHADBALA_FIXTURES
from tests.fixtures.bhava_dig_bala_astrosage import BHAVA_DIG_BALA_ASTROSAGE

_BHAVA_DRISHTI_SWE_IDS: dict[str, int] = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
    "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS, "Saturn": swe.SATURN,
}

# Canonical birth args per chart — same literals used across
# tests/calculations/strength/{test_dig_bala,test_kala_bala,test_ishta_kashta}.py.
_BIRTH_ARGS: dict[str, tuple[str, str, str, str]] = {
    "sulabh":   ("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India"),
    "surbhi":   ("Surbhi", "11 Sep 1992", "10:30", "Patna, India"),
    "sheridan": ("Sheridan", "27 May 1984", "08:00", "Durban, South Africa"),
    "david":    ("David", "19 Jan 1976", "22:00", "London, UK"),
}

# ── Shared test data ──────────────────────────────────────────────────────────

# Whole-sign house maps derived from each chart's natal Lagna sign.
# Lagna sign = house 1; subsequent signs in zodiacal order fill houses 2-12.
_HOUSE_SIGNS: dict[str, dict[int, str]] = {
    "sulabh": {
        1: "Sagittarius", 2: "Capricorn", 3: "Aquarius",  4: "Pisces",
        5: "Aries",       6: "Taurus",    7: "Gemini",    8: "Cancer",
        9: "Leo",        10: "Virgo",    11: "Libra",    12: "Scorpio",
    },
    "surbhi": {
        1: "Libra",      2: "Scorpio",   3: "Sagittarius", 4: "Capricorn",
        5: "Aquarius",   6: "Pisces",    7: "Aries",       8: "Taurus",
        9: "Gemini",    10: "Cancer",   11: "Leo",        12: "Virgo",
    },
    "sheridan": {
        1: "Taurus",     2: "Gemini",    3: "Cancer",    4: "Leo",
        5: "Virgo",      6: "Libra",     7: "Scorpio",   8: "Sagittarius",
        9: "Capricorn", 10: "Aquarius", 11: "Pisces",   12: "Aries",
    },
    "david": {
        1: "Virgo",      2: "Libra",     3: "Scorpio",   4: "Sagittarius",
        5: "Capricorn",  6: "Aquarius",  7: "Pisces",    8: "Aries",
        9: "Taurus",    10: "Gemini",   11: "Cancer",   12: "Leo",
    },
}


@pytest.fixture(scope="module")
def _house_cusps_by_chart() -> dict[str, dict[int, float]]:
    """Real Porphyry house cusps per chart, computed once per test module.

    Uses calculate_chart() only to get jd_ut/lat/lon (network-free under
    tests/conftest.py's session-scoped geocoder patch, which — being
    session-scoped and autouse — is already active by the time this
    module-scoped fixture runs). house_signs stays whole-sign (_HOUSE_SIGNS
    above); this is deliberately a SEPARATE cusp system, per
    compute_bhava_dig_bala's documented distinction between the two.
    """
    return {
        chart_name: compute_porphyry_house_cusps(
            chart["meta"]["jd_ut"],
            chart["birth_details"]["lat"],
            chart["birth_details"]["lon"],
        )
        for chart_name, chart in (
            (name, calculate_chart(*args)) for name, args in _BIRTH_ARGS.items()
        )
    }


@pytest.fixture(scope="module")
def _planet_lons_by_chart() -> dict[str, dict[str, float]]:
    """Real sidereal planet longitudes per chart (title-case, 7 classical
    planets), for compute_bhava_drishti_bala's planet_lons parameter.

    Same derivation pattern as _house_cusps_by_chart above (calculate_chart()
    for jd_ut, network-free under tests/conftest.py's geocoder patch) --
    via helpers/ephemeris.py's sidereal_longitude(), matching
    chart_profile.py's own Session 53 wiring for this exact parameter.
    """
    return {
        chart_name: {
            planet: ephemeris.sidereal_longitude(chart["meta"]["jd_ut"], swe_id)
            for planet, swe_id in _BHAVA_DRISHTI_SWE_IDS.items()
        }
        for chart_name, chart in (
            (name, calculate_chart(*args)) for name, args in _BIRTH_ARGS.items()
        )
    }


def _totals_from_fixture(chart_key: str) -> dict[str, float]:
    """Build shadbala_totals dict (title-case planet → virupa) from AstroSage fixture."""
    return {
        p.capitalize(): SHADBALA_FIXTURES[chart_key]["planets"][p]["shadbala_virupa"]
        for p in SHADBALA_FIXTURES[chart_key]["planets"]
    }


# Build Layer A parametrize cases at import time: (chart, house, expected_virupa).
# expected_virupa = lord's shadbala_virupa from AstroSage fixture — the oracle value.
_LAYER_A_CASES: list[tuple[str, int, float]] = []
for _chart in ("sulabh", "surbhi", "sheridan", "david"):
    _totals = _totals_from_fixture(_chart)
    for _house in range(1, 13):
        _sign = _HOUSE_SIGNS[_chart][_house]
        _lord = SIGN_LORDS[_sign]
        _LAYER_A_CASES.append((_chart, _house, _totals[_lord]))


# ── Layer A: Full 12-house validation, all 4 charts ──────────────────────────

@pytest.mark.parametrize("chart_name,house,expected", _LAYER_A_CASES)
def test_a_bhavadhipati_matches_astrosage_oracle(chart_name, house, expected):
    """Bhavadhipati Bala for each house equals the ruling planet's AstroSage Shadbala total."""
    result = compute_bhavadhipati_bala(
        _HOUSE_SIGNS[chart_name],
        _totals_from_fixture(chart_name),
    )
    assert abs(result[house] - expected) <= 0.5, (
        f"{chart_name} house {house} (sign={_HOUSE_SIGNS[chart_name][house]!r}): "
        f"got {result[house]}, expected {expected}"
    )


# ── Layer B: Same-lord pair returns identical Bhavadhipati Bala ──────────────

def test_b_same_lord_houses_return_identical_value():
    """Two houses with the same sign-lord return the same Bhavadhipati Bala (not just equal floats)."""
    # Sulabh: house 2 = Capricorn and house 3 = Aquarius — both Saturn-ruled.
    # Expected: both return Saturn's shadbala_virupa (423.16 from AstroSage fixture).
    result = compute_bhavadhipati_bala(
        _HOUSE_SIGNS["sulabh"],
        _totals_from_fixture("sulabh"),
    )
    assert result[2] == result[3], (
        f"Houses 2 and 3 both Saturn-ruled (Capricorn + Aquarius), "
        f"but got different values: {result[2]} vs {result[3]}"
    )
    # Confirm the shared value is Saturn's fixture total, not an arbitrary match.
    saturn_total = SHADBALA_FIXTURES["sulabh"]["planets"]["saturn"]["shadbala_virupa"]
    assert result[2] == saturn_total, (
        f"Expected Saturn's fixture total {saturn_total}, got {result[2]}"
    )


def test_b_jupiter_ruled_pair_david():
    """David's houses 4 and 7 (Sagittarius + Pisces, both Jupiter-ruled) return identical Bhavadhipati Bala."""
    result = compute_bhavadhipati_bala(
        _HOUSE_SIGNS["david"],
        _totals_from_fixture("david"),
    )
    assert result[4] == result[7], (
        f"Houses 4 (Sagittarius) and 7 (Pisces) both Jupiter-ruled, "
        f"but got {result[4]} vs {result[7]}"
    )
    jupiter_total = SHADBALA_FIXTURES["david"]["planets"]["jupiter"]["shadbala_virupa"]
    assert result[4] == jupiter_total


# ── Layer C: Error handling ───────────────────────────────────────────────────

_VALID_HOUSE_SIGNS = _HOUSE_SIGNS["sulabh"].copy()
_VALID_TOTALS = _totals_from_fixture("sulabh")

_LAYER_C_CASES = [
    pytest.param(
        {k: v for k, v in _VALID_HOUSE_SIGNS.items() if k != 7},   # missing house 7
        _VALID_TOTALS,
        r"missing=\[7\]",   # error message says: missing=[7], extra=[]
        id="missing_house_7",
    ),
    pytest.param(
        {**_VALID_HOUSE_SIGNS, 13: "Aries"},                        # bogus key 13
        _VALID_TOTALS,
        "13",
        id="extra_key_13",
    ),
    pytest.param(
        {**_VALID_HOUSE_SIGNS, 5: "Ophiuchus"},                     # invalid sign
        _VALID_TOTALS,
        "Ophiuchus",
        id="invalid_sign_name",
    ),
    pytest.param(
        _VALID_HOUSE_SIGNS,
        {k: v for k, v in _VALID_TOTALS.items() if k != "Jupiter"}, # lord missing (house 1=Sagittarius→Jupiter)
        "Jupiter",
        id="missing_lord_jupiter",
    ),
]


@pytest.mark.parametrize("house_signs,shadbala_totals,expected_fragment", _LAYER_C_CASES)
def test_c_raises_valueerror_naming_the_problem(house_signs, shadbala_totals, expected_fragment):
    """ValueError names the specific problem (which house, sign, or planet is missing)."""
    with pytest.raises(ValueError, match=expected_fragment):
        compute_bhavadhipati_bala(house_signs, shadbala_totals)


# ── Layer D: Output shape ─────────────────────────────────────────────────────

@pytest.mark.parametrize("chart_name", ["sulabh", "surbhi", "sheridan", "david"])
def test_d_output_has_exactly_keys_1_to_12_all_float(chart_name):
    """Returned dict has exactly keys 1-12 and all values are floats."""
    result = compute_bhavadhipati_bala(
        _HOUSE_SIGNS[chart_name],
        _totals_from_fixture(chart_name),
    )
    assert set(result.keys()) == set(range(1, 13)), (
        f"{chart_name}: expected keys 1-12, got {sorted(result.keys())}"
    )
    for house, val in result.items():
        assert isinstance(val, float), (
            f"{chart_name} house {house}: value {val!r} is {type(val).__name__}, expected float"
        )


# ── Layer E: Live-compute wiring smoke test ───────────────────────────────────

def test_e_live_compute_wiring_smoke():
    """Integration smoke: live compute_shadbala_totals() -> compute_bhavadhipati_bala() wiring.

    Does NOT validate numeric parity with AstroSage — Layer A handles that using
    fixture-based input (required because the V1 Drik Bala stub causes >0.5 Virupa
    divergence per planet). This test guards only that the live integration path
    wires together without error and produces a structurally valid result.

    Assertions: 12 entries, all positive floats, non-degenerate spread (max - min > 0).
    The spread check detects silent wiring failures where every house collapses to the
    same value (e.g. wrong dict shape passed to compute_bhavadhipati_bala causing all
    lookups to resolve via some unexpected default).
    """
    from agent.chart_calculator import calculate_chart
    from agent.calculations.strength.shadbala_totals import compute_shadbala_totals

    chart = calculate_chart("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")
    raw_totals = compute_shadbala_totals(chart)
    # compute_shadbala_totals keys are lowercase; SIGN_LORDS values are Title-case.
    live_totals = {p.capitalize(): raw_totals[p]["shadbala_virupa"] for p in raw_totals}

    result = compute_bhavadhipati_bala(_HOUSE_SIGNS["sulabh"], live_totals)

    assert set(result.keys()) == set(range(1, 13)), \
        f"Expected keys 1-12, got {sorted(result.keys())}"
    for house, val in result.items():
        assert isinstance(val, float) and val > 0, \
            f"House {house}: expected positive float, got {val!r}"
    spread = max(result.values()) - min(result.values())
    assert spread > 0, (
        "All 12 Bhavadhipati Bala values are identical — "
        "likely a wiring bug (wrong dict shape passed to compute_bhavadhipati_bala)"
    )


# ── Layer F: Bhava Dig Bala — real implementation ────────────────────────────

def test_f_dig_bala_sulabh_hardest_case_zeros(_house_cusps_by_chart):
    """Hardest case first: Sulabh houses 4 and 7 are AstroSage's two zeros,
    not the easy non-zero majority. Verify these before the parametrized
    48-case sweep below, so a broken formula fails loud on the edge case
    (a house at maximum classically-strong dignity but zero Dig Bala) first.
    """
    result = compute_bhava_dig_bala(_HOUSE_SIGNS["sulabh"], _house_cusps_by_chart["sulabh"])
    assert result["values"][4] == 0.0, (
        f"Sulabh house 4: expected 0.0 (AstroSage), got {result['values'][4]}"
    )
    assert result["values"][7] == 0.0, (
        f"Sulabh house 7: expected 0.0 (AstroSage), got {result['values'][7]}"
    )


_LAYER_F_CASES: list[tuple[str, int]] = [
    (chart, house)
    for chart in ("sulabh", "surbhi", "sheridan", "david")
    for house in range(1, 13)
]


@pytest.mark.parametrize("chart_name,house", _LAYER_F_CASES)
def test_f_dig_bala_matches_astrosage_exact(chart_name, house, _house_cusps_by_chart):
    """compute_bhava_dig_bala matches AstroSage's BhavBala Bhavdig row exactly.

    Exact match, not tolerance-band: the rasi-animal-group taper only ever
    produces clean multiples of 10 (see bhava_bala.py docstring), unlike the
    fuzzy-tolerance patterns used for Kala/Chesta Bala elsewhere in this suite.
    """
    result = compute_bhava_dig_bala(_HOUSE_SIGNS[chart_name], _house_cusps_by_chart[chart_name])
    expected = BHAVA_DIG_BALA_ASTROSAGE[chart_name][house]
    assert result["values"][house] == expected, (
        f"{chart_name} house {house}: got {result['values'][house]}, expected {expected}"
    )


def test_f_dig_bala_raises_on_missing_house_signs_key(_house_cusps_by_chart):
    """compute_bhava_dig_bala raises ValueError when a house_signs key is absent."""
    bad = {k: v for k, v in _HOUSE_SIGNS["sulabh"].items() if k != 6}
    with pytest.raises(ValueError, match="1-12"):
        compute_bhava_dig_bala(bad, _house_cusps_by_chart["sulabh"])


def test_f_dig_bala_raises_on_extra_house_signs_key(_house_cusps_by_chart):
    """compute_bhava_dig_bala raises ValueError when an out-of-range house_signs key is present."""
    bad = {**_HOUSE_SIGNS["sulabh"], 13: "Aries"}
    with pytest.raises(ValueError, match="1-12"):
        compute_bhava_dig_bala(bad, _house_cusps_by_chart["sulabh"])


def test_f_dig_bala_raises_on_missing_house_cusps_key(_house_cusps_by_chart):
    """compute_bhava_dig_bala raises ValueError when a house_cusps key is absent."""
    bad_cusps = {k: v for k, v in _house_cusps_by_chart["sulabh"].items() if k != 6}
    with pytest.raises(ValueError, match="1-12"):
        compute_bhava_dig_bala(_HOUSE_SIGNS["sulabh"], bad_cusps)


def test_f_dig_bala_raises_on_extra_house_cusps_key(_house_cusps_by_chart):
    """compute_bhava_dig_bala raises ValueError when an out-of-range house_cusps key is present."""
    bad_cusps = {**_house_cusps_by_chart["sulabh"], 13: 100.0}
    with pytest.raises(ValueError, match="1-12"):
        compute_bhava_dig_bala(_HOUSE_SIGNS["sulabh"], bad_cusps)


# ── Layer G: Bhava Drishti Bala kernel structural spot-checks (Session 53) ──
#
# NOTE on why this is NOT a continuity-test layer (unlike test_drik_bala.py's
# Layer A TestXDrishtiBoundaries.test_continuous_at_boundary classes): the
# bhava kernel's ADD-ON specials are strict-inequality-bounded (e.g. Saturn's
# "60 < D <= 90") and ADDITIVE on top of an otherwise-continuous base taper --
# so at D=90+epsilon the add-on switches off while the base taper itself
# stays continuous, producing a real, by-design jump (e.g. Saturn: 90 Virupa
# at D=90 down to 45 just past it). Asserting continuity here would encode a
# false expectation; drik_bala.py's SMOOTH-TAPER CORRECTIONS were specifically
# chosen to eliminate such jumps in the graha kernel -- the bhava kernel
# deliberately does not do the same (see bhava_bala.py CITATION point (a)).

def test_g_saturn_addon_at_d75():
    """D=75: base D-45=30 (60<D<90 branch) + Saturn add-on 45 (60<D<=90) = 75."""
    assert _sphuta_bhava_drishti("Saturn", 75.0) == pytest.approx(75.0, abs=1e-9)


def test_g_mars_addon_at_d105():
    """D=105: base 30+(120-D)/2=37.5 (90<D<120 branch) + Mars add-on 15 (90<D<=120) = 52.5."""
    assert _sphuta_bhava_drishti("Mars", 105.0) == pytest.approx(52.5, abs=1e-9)


def test_g_jupiter_addon_at_d135():
    """D=135: base 150-D=15 (120<D<150 branch) + Jupiter add-on 30 (120<D<=150) = 45."""
    assert _sphuta_bhava_drishti("Jupiter", 135.0) == pytest.approx(45.0, abs=1e-9)


def test_g_venus_plain_base_at_d180():
    """D=180: plain base taper only (Venus has no add-on special) --
    (300-D)/2 = 60 (D=180 falls in the 180<=D<300 branch, not 150<D<180)."""
    assert _sphuta_bhava_drishti("Venus", 180.0) == pytest.approx(60.0, abs=1e-9)


# ── Layer H: Bhava Drishti Bala — AstroSage BhavBala oracle parity ──────────
#
# AstroSage BhavBala table, houses 1-12, hand-extracted and verified Session
# 53 (design-chat back-solve — see bhava_bala.py compute_bhava_drishti_bala
# CITATION). Cross-checked against this file's own _BIRTH_ARGS before use;
# all 4 birth data points already match the existing fixture, no discrepancy.
#
# Hardest case first: Sheridan is the only chart in this set where Moon
# classifies malefic (drik_bala.py SHERIDAN EDGE CASE), which also flips
# Mercury's same-rasi classification tally here — same hardest-case-first
# convention as test_drik_bala.py's _JHORA_DRIK dict.
_BHAVA_DRISHTI_ASTROSAGE: dict[str, list[float]] = {
    "sheridan": [-11.33, 0.40, -19.33, 35.35, -49.17, -60.93, -50.71,
                 -52.37, -17.48, 36.25, 16.59, 17.99],
    "sulabh":   [55.64, 20.52, -15.55, -20.85, -11.86, -31.33, -34.93,
                 12.28, -19.18, -26.86, 18.40, 23.07],
    "surbhi":   [25.45, 69.33, 67.60, 23.53, 99.70, 70.59, 56.31,
                 32.02, -1.98, -6.94, -7.34, -3.47],
    "david":    [-32.43, 8.46, 30.55, 49.24, -15.86, -0.02, -2.11,
                 -38.25, -39.50, 33.13, -11.21, -11.89],
}

# Mirrors test_drik_bala.py's Session 46 JHora parity tolerance convention.
# Measured max |delta| 0.15 Virupa on repo ephemeris this session (3x
# headroom). Tuning note: tighten toward 0.2 only if a 5th reference chart
# validates under that tighter bound — do not tighten preemptively on
# 4-chart data (THRESHOLD DISCIPLINE, CLAUDE.md Working Style #4).
_TOL_BHAVA_DRISHTI = 0.5

_LAYER_H_CASES: list[tuple[str, int]] = [
    (chart, house)
    for chart in ("sheridan", "sulabh", "surbhi", "david")
    for house in range(1, 13)
]


@pytest.mark.parametrize("chart_name,house", _LAYER_H_CASES)
def test_h_drishti_bala_matches_astrosage(
    chart_name, house, _house_cusps_by_chart, _planet_lons_by_chart
):
    """compute_bhava_drishti_bala matches AstroSage's BhavBala row within ±0.5 Virupa."""
    result = compute_bhava_drishti_bala(
        _house_cusps_by_chart[chart_name], _planet_lons_by_chart[chart_name]
    )
    expected = _BHAVA_DRISHTI_ASTROSAGE[chart_name][house - 1]
    assert result[house] == pytest.approx(expected, abs=_TOL_BHAVA_DRISHTI), (
        f"{chart_name} house {house}: got {result[house]}, expected {expected} "
        f"(AstroSage, tol ±{_TOL_BHAVA_DRISHTI})"
    )


def test_h_drishti_bala_raises_on_missing_house_cusps_key(_planet_lons_by_chart):
    """compute_bhava_drishti_bala raises ValueError when a house_cusps key is absent."""
    bad_cusps = {h: float(h) for h in range(1, 13) if h != 9}
    with pytest.raises(ValueError, match="1-12"):
        compute_bhava_drishti_bala(bad_cusps, _planet_lons_by_chart["sulabh"])


def test_h_drishti_bala_raises_on_extra_house_cusps_key(_planet_lons_by_chart):
    """compute_bhava_drishti_bala raises ValueError when an out-of-range house_cusps key is present."""
    bad_cusps = {h: float(h) for h in range(1, 13)}
    bad_cusps[13] = 100.0
    with pytest.raises(ValueError, match="1-12"):
        compute_bhava_drishti_bala(bad_cusps, _planet_lons_by_chart["sulabh"])


def test_h_drishti_bala_raises_on_missing_planet(_house_cusps_by_chart, _planet_lons_by_chart):
    """compute_bhava_drishti_bala raises ValueError when planet_lons is missing a classical planet."""
    bad_lons = {p: v for p, v in _planet_lons_by_chart["sulabh"].items() if p != "Mercury"}
    with pytest.raises(ValueError, match="Mercury"):
        compute_bhava_drishti_bala(_house_cusps_by_chart["sulabh"], bad_lons)


# ── Layer I: compute_bhava_bala_totals aggregator ────────────────────────────

def test_i_totals_arithmetic_matches_components(_house_cusps_by_chart, _planet_lons_by_chart):
    """total_virupa = bhavadhipati + bhava_dig + bhava_drishti (all 3 real,
    Session 53); total_rupa = round(total_virupa/60, 2).

    Recomputes expected drishti/dig/bhavadhipati from the sub-components
    themselves (structural assertion), not hand-copied magic numbers --
    Layers F and H already validate those sub-components against AstroSage
    independently; this test validates only the aggregator's own arithmetic
    (same precedent as shadbala_totals.py Layer C).
    """
    cusps = _house_cusps_by_chart["sulabh"]
    plons = _planet_lons_by_chart["sulabh"]
    totals = compute_bhava_bala_totals(
        _HOUSE_SIGNS["sulabh"], _totals_from_fixture("sulabh"), cusps, plons
    )
    bhav = compute_bhavadhipati_bala(_HOUSE_SIGNS["sulabh"], _totals_from_fixture("sulabh"))
    dig = compute_bhava_dig_bala(_HOUSE_SIGNS["sulabh"], cusps)["values"]
    drishti = compute_bhava_drishti_bala(cusps, plons)
    for h in range(1, 13):
        assert totals[h]["bhavadhipati"] == bhav[h], f"House {h}: bhavadhipati mismatch"
        assert totals[h]["bhava_dig"] == dig[h], f"House {h}: bhava_dig mismatch"
        assert totals[h]["bhava_drishti"] == drishti[h], f"House {h}: bhava_drishti mismatch"
        expected_total = bhav[h] + dig[h] + drishti[h]
        assert totals[h]["total_virupa"] == expected_total, (
            f"House {h}: total_virupa should equal bhavadhipati + bhava_dig + bhava_drishti"
        )
        assert totals[h]["total_rupa"] == round(expected_total / 60, 2), (
            f"House {h}: total_rupa = round(total_virupa/60, 2) mismatch"
        )


def test_i_rank_is_full_permutation_of_1_to_12(_house_cusps_by_chart, _planet_lons_by_chart):
    """Ranks across all 12 houses form exactly {1, ..., 12} — no gaps, no duplicates."""
    totals = compute_bhava_bala_totals(
        _HOUSE_SIGNS["sulabh"], _totals_from_fixture("sulabh"),
        _house_cusps_by_chart["sulabh"], _planet_lons_by_chart["sulabh"],
    )
    ranks = [totals[h]["rank"] for h in range(1, 13)]
    assert sorted(ranks) == list(range(1, 13)), (
        f"Ranks are not a full 1-12 permutation: {ranks}"
    )


def test_i_rank_ordering_consistent_with_total_virupa(_house_cusps_by_chart, _planet_lons_by_chart):
    """Higher total_virupa → lower rank number; equal virupa → lower house wins."""
    totals = compute_bhava_bala_totals(
        _HOUSE_SIGNS["sulabh"], _totals_from_fixture("sulabh"),
        _house_cusps_by_chart["sulabh"], _planet_lons_by_chart["sulabh"],
    )
    for ha in range(1, 13):
        for hb in range(ha + 1, 13):
            va, vb = totals[ha]["total_virupa"], totals[hb]["total_virupa"]
            ra, rb = totals[ha]["rank"], totals[hb]["rank"]
            if va > vb:
                assert ra < rb, (
                    f"House {ha} (virupa={va}) > house {hb} (virupa={vb}) "
                    f"but rank {ra} >= {rb}"
                )
            elif vb > va:
                assert rb < ra, (
                    f"House {hb} (virupa={vb}) > house {ha} (virupa={va}) "
                    f"but rank {rb} >= {ra}"
                )
            else:
                # tie: lower house number must get the better (lower) rank
                assert ra < rb, (
                    f"Houses {ha} and {hb} tied at virupa={va}; "
                    f"expected house {ha} rank < house {hb} rank, got {ra} vs {rb}"
                )


def test_i_stub_flags_and_caveat_integrity(_house_cusps_by_chart, _planet_lons_by_chart):
    """dig_is_stubbed and drishti_is_stubbed are both False (both real,
    Bhava Dig since Session 42, Bhava Drishti since Session 53); caveat is
    non-empty — all 12 houses."""
    totals = compute_bhava_bala_totals(
        _HOUSE_SIGNS["david"], _totals_from_fixture("david"),
        _house_cusps_by_chart["david"], _planet_lons_by_chart["david"],
    )
    for h in range(1, 13):
        assert totals[h]["dig_is_stubbed"] is False, f"House {h}: dig_is_stubbed should be False"
        assert totals[h]["drishti_is_stubbed"] is False, f"House {h}: drishti_is_stubbed should be False"
        assert isinstance(totals[h]["caveat"], str) and totals[h]["caveat"], (
            f"House {h}: caveat must be a non-empty string"
        )


def test_i_totals_raises_on_malformed_house_signs(_house_cusps_by_chart, _planet_lons_by_chart):
    """compute_bhava_bala_totals propagates ValueError from sub-components on bad input."""
    bad = {k: v for k, v in _HOUSE_SIGNS["sulabh"].items() if k != 3}
    with pytest.raises(ValueError, match="1-12"):
        compute_bhava_bala_totals(
            bad, _totals_from_fixture("sulabh"),
            _house_cusps_by_chart["sulabh"], _planet_lons_by_chart["sulabh"],
        )
