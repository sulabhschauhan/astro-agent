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

Layer G: compute_bhava_drishti_bala stub — same shape as old Layer F.

Layer H: compute_bhava_bala_totals aggregator — arithmetic correctness
         (bhava_dig is now real; bhava_drishti stub still makes AstroSage
         total_virupa parity impossible, same precedent as
         shadbala_totals.py Layer C), rank full-permutation validity, and
         caveat/stub-flag integrity.

Reference: reference_charts.md for Lagna signs.
  Sulabh=Sagittarius, Surbhi=Libra, Sheridan=Taurus, David=Virgo
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest

from agent.calculations.strength.bhava_bala import (
    compute_bhavadhipati_bala,
    compute_bhava_dig_bala,
    compute_bhava_drishti_bala,
    compute_bhava_bala_totals,
)
from agent.chart_calculator import SIGN_LORDS, calculate_chart, compute_porphyry_house_cusps
from tests.fixtures.shadbala_fixtures import SHADBALA_FIXTURES
from tests.fixtures.bhava_dig_bala_astrosage import BHAVA_DIG_BALA_ASTROSAGE

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


# ── Layer G: Bhava Drishti Bala stub ─────────────────────────────────────────

def test_g_drishti_bala_stub_returns_twelve_zeros():
    """compute_bhava_drishti_bala returns exactly 12 zero floats (V1 stub)."""
    result = compute_bhava_drishti_bala(_HOUSE_SIGNS["sulabh"])
    assert set(result.keys()) == set(range(1, 13)), (
        f"Expected keys 1-12, got {sorted(result.keys())}"
    )
    for house, val in result.items():
        assert val == 0.0, f"House {house}: expected 0.0, got {val!r}"


def test_g_drishti_bala_stub_raises_on_missing_house():
    """compute_bhava_drishti_bala raises ValueError when a house key is absent."""
    bad = {k: v for k, v in _HOUSE_SIGNS["sulabh"].items() if k != 9}
    with pytest.raises(ValueError, match="1-12"):
        compute_bhava_drishti_bala(bad)


def test_g_drishti_bala_stub_raises_on_extra_key():
    """compute_bhava_drishti_bala raises ValueError when an out-of-range key is present."""
    bad = {**_HOUSE_SIGNS["sulabh"], 0: "Sagittarius"}
    with pytest.raises(ValueError, match="1-12"):
        compute_bhava_drishti_bala(bad)


# ── Layer H: compute_bhava_bala_totals aggregator ────────────────────────────

def test_h_totals_arithmetic_matches_components(_house_cusps_by_chart):
    """total_virupa = bhavadhipati + bhava_dig + 0.0; total_rupa = round(total_virupa/60, 2).

    Does NOT compare total_virupa against AstroSage's total — the bhava_drishti
    stub still makes that impossible. bhava_dig itself IS AstroSage-validated
    (Layer F); this test validates only the aggregator's internal arithmetic
    (same precedent as shadbala_totals.py Layer C).
    """
    cusps = _house_cusps_by_chart["sulabh"]
    totals = compute_bhava_bala_totals(_HOUSE_SIGNS["sulabh"], _totals_from_fixture("sulabh"), cusps)
    bhav = compute_bhavadhipati_bala(_HOUSE_SIGNS["sulabh"], _totals_from_fixture("sulabh"))
    dig = compute_bhava_dig_bala(_HOUSE_SIGNS["sulabh"], cusps)["values"]
    for h in range(1, 13):
        assert totals[h]["bhavadhipati"] == bhav[h], f"House {h}: bhavadhipati mismatch"
        assert totals[h]["bhava_dig"] == dig[h], f"House {h}: bhava_dig mismatch"
        assert totals[h]["bhava_drishti"] == 0.0, f"House {h}: bhava_drishti should be 0.0"
        assert totals[h]["total_virupa"] == bhav[h] + dig[h], (
            f"House {h}: total_virupa should equal bhavadhipati + bhava_dig (drishti stub is 0.0)"
        )
        assert totals[h]["total_rupa"] == round((bhav[h] + dig[h]) / 60, 2), (
            f"House {h}: total_rupa = round(total_virupa/60, 2) mismatch"
        )


def test_h_rank_is_full_permutation_of_1_to_12(_house_cusps_by_chart):
    """Ranks across all 12 houses form exactly {1, ..., 12} — no gaps, no duplicates."""
    totals = compute_bhava_bala_totals(
        _HOUSE_SIGNS["sulabh"], _totals_from_fixture("sulabh"), _house_cusps_by_chart["sulabh"]
    )
    ranks = [totals[h]["rank"] for h in range(1, 13)]
    assert sorted(ranks) == list(range(1, 13)), (
        f"Ranks are not a full 1-12 permutation: {ranks}"
    )


def test_h_rank_ordering_consistent_with_total_virupa(_house_cusps_by_chart):
    """Higher total_virupa → lower rank number; equal virupa → lower house wins."""
    totals = compute_bhava_bala_totals(
        _HOUSE_SIGNS["sulabh"], _totals_from_fixture("sulabh"), _house_cusps_by_chart["sulabh"]
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


def test_h_stub_flags_and_caveat_integrity(_house_cusps_by_chart):
    """dig_is_stubbed is False (real, this session); drishti_is_stubbed is True
    (still stubbed); caveat is non-empty — all 12 houses."""
    totals = compute_bhava_bala_totals(
        _HOUSE_SIGNS["david"], _totals_from_fixture("david"), _house_cusps_by_chart["david"]
    )
    for h in range(1, 13):
        assert totals[h]["dig_is_stubbed"] is False, f"House {h}: dig_is_stubbed should be False"
        assert totals[h]["drishti_is_stubbed"] is True, f"House {h}: drishti_is_stubbed should be True"
        assert isinstance(totals[h]["caveat"], str) and totals[h]["caveat"], (
            f"House {h}: caveat must be a non-empty string"
        )


def test_h_totals_raises_on_malformed_house_signs(_house_cusps_by_chart):
    """compute_bhava_bala_totals propagates ValueError from sub-components on bad input."""
    bad = {k: v for k, v in _HOUSE_SIGNS["sulabh"].items() if k != 3}
    with pytest.raises(ValueError, match="1-12"):
        compute_bhava_bala_totals(bad, _totals_from_fixture("sulabh"), _house_cusps_by_chart["sulabh"])
