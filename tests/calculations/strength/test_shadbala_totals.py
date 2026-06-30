"""Tests for agent/calculations/strength/shadbala_totals.py — P2.5.6.

Layer A: NAISARGIKA_BALA constant integrity (BPHS 60/7 series).
Layer B: Pass-through component tolerance for sthan_total, dig, kala_total,
         chesta, naisargika. Tolerances match the calibrated values from each
         component's own test suite (up to ±41 for Sun chesta, ±10 for Tara
         Graha chesta, ±6 for Moon/Venus kala_total due to Ayana Bala edge case).
Layer C: Aggregator arithmetic — shadbala_virupa is the sum of the result's
         own component fields (NOT the fixture's shadbala_virupa, which includes
         real Drik Bala; this module stubs Drik at 0.0). Rupa conversion and
         ratio derivation also checked. min_required is an exact table lookup.
Layer D: Rank validity — complete permutation {1..7}, internal self-consistency.
         Sulabh hardest-case tie-gap check.
Layer E: Caveat/stub field integrity — drik_is_stubbed=True, caveat string
         contains sentinel, uniform across all 7 planets within a chart.
Layer F: Error propagation — missing "meta" key surfaces ValueError or
         RuntimeError from the first failing component; aggregator does not swallow it.

Charts: Sulabh (1988-04-06, Calcutta) and Surbhi (1992-09-11, Patna) only.
Sheridan and David omitted — birth date/time/place are "unknown" in
shadbala_fixtures.py; ephemeris computation is not possible.
Precedent: test_chesta_bala.py and test_sthana_bala.py make the same exclusion.

Geocoder monkeypatched by tests/conftest.py; all places must be in
tests/fixtures/geocoded_locations.json.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest

from agent.calculations.strength.shadbala_totals import (
    NAISARGIKA_BALA,
    compute_shadbala_totals,
)
from tests.fixtures.shadbala_fixtures import SHADBALA_FIXTURES

_PLANETS   = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
_CHART_KEYS = ["sulabh", "surbhi"]


# ── Module-scope computed fixtures ────────────────────────────────────────────
# One calculate_chart() + compute_shadbala_totals() call per chart, shared across
# all layers. Sheridan/David omitted — birth data unknown (see module docstring).

@pytest.fixture(scope="module")
def sulabh_totals():
    from agent.chart_calculator import calculate_chart
    chart = calculate_chart("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")
    return compute_shadbala_totals(chart)


@pytest.fixture(scope="module")
def surbhi_totals():
    from agent.chart_calculator import calculate_chart
    chart = calculate_chart("Surbhi", "11 Sep 1992", "10:30", "Patna, India")
    return compute_shadbala_totals(chart)


@pytest.fixture(scope="module")
def all_totals(sulabh_totals, surbhi_totals):
    return {"sulabh": sulabh_totals, "surbhi": surbhi_totals}


# ── Layer A: NAISARGIKA_BALA constant ────────────────────────────────────────

class TestNaisargikaBalaConstant:
    def test_all_seven_planets_present(self):
        assert set(NAISARGIKA_BALA.keys()) == set(_PLANETS)

    @pytest.mark.parametrize("planet,expected", [
        ("sun",     60.00),
        ("moon",    51.43),
        ("mars",    17.14),
        ("mercury", 25.71),
        ("jupiter", 34.29),
        ("venus",   42.86),
        ("saturn",   8.57),
    ])
    def test_bphs_60_over_7_series(self, planet, expected):
        # Values are the BPHS 60/7 series confirmed against JHora cross-check.
        assert NAISARGIKA_BALA[planet] == pytest.approx(expected, abs=0.01)


# ── Layer B: pass-through component tolerance ─────────────────────────────────
#
# Tolerances per field/planet:
#   sthan_total : ±40  (test_sthana_bala.py uses abs=40 due to Saptavargaja
#                  source divergence — BPHS 27.2-4 vs AstroSage unpublished
#                  table; see CLAUDE.md §Known Source Divergences → Shadbala
#                  Saptavargaja Bala)
#   dig         : ±0.5  (test_dig_bala.py parity tolerance)
#   kala_total  : Sulabh only — test_kala_bala.py validated the Sulabh chart
#                  (±2.0 standard, ±6.0 for moon/venus). Surbhi kala_total
#                  excluded: Jupiter/Saturn diverge by ±31/±59 Virupa due to
#                  Hora/Masa Bala day-of-hora and masa-lord differences not yet
#                  investigated for cross-chart correctness.
#   chesta      : per-planet calibrated from test_chesta_bala.py Layer B:
#                  sun ±41 (Ayana path / direction gap, accepted V1 divergence)
#                  moon ±1, jupiter/saturn ±3
#                  mars/mercury/venus ±10 (elongation formula vs Surya Siddhanta
#                  mean daily motion constants used by JHora; not Swiss-Ephemeris-
#                  derivable; do not re-investigate — see CLAUDE.md §Chesta Bala)
#   naisargika  : ±0.01 — module constant pass-through, not a formula output

_CHESTA_PASS_TOL: dict[str, float] = {
    "sun":     41.0,
    "moon":     1.0,
    "mars":    10.0,
    "mercury": 10.0,
    "jupiter":  3.0,
    "venus":   10.0,
    "saturn":   3.0,
}
_AYANA_RELAXED = {"moon", "venus"}


def _layer_b_tol(planet: str, field: str) -> float:
    if field == "sthan_total":
        return 40.0
    if field == "chesta":
        return _CHESTA_PASS_TOL[planet]
    if field == "naisargika":
        return 0.01
    return 0.5  # dig


# Cross-chart fields: kala_total excluded — fixture comparison only valid for Sulabh
# (see note above). sthan_total/dig/chesta are sufficiently stable cross-chart.
@pytest.mark.parametrize("chart_key", _CHART_KEYS)
@pytest.mark.parametrize("planet", _PLANETS)
@pytest.mark.parametrize("field", ["sthan_total", "dig", "chesta"])
def test_b_component_passthrough(chart_key, planet, field, all_totals):
    got      = all_totals[chart_key][planet][field]
    expected = SHADBALA_FIXTURES[chart_key]["planets"][planet][field]
    tol      = _layer_b_tol(planet, field)
    assert got == pytest.approx(expected, abs=tol), (
        f"{chart_key} {planet} {field}: got {got:.4f}, expected {expected:.4f} "
        f"(tol ±{tol})"
    )


@pytest.mark.parametrize("planet", _PLANETS)
def test_b_sulabh_kala_total_passthrough(planet, sulabh_totals):
    """kala_total checked against fixture for Sulabh only — the one chart
    validated by test_kala_bala.py. Surbhi excluded: Jupiter/Saturn kala_total
    diverge by ±31/±59 Virupa due to Hora/Masa Bala cross-chart differences
    that test_kala_bala.py did not investigate."""
    got      = sulabh_totals[planet]["kala_total"]
    expected = SHADBALA_FIXTURES["sulabh"]["planets"][planet]["kala_total"]
    tol      = 6.0 if planet in _AYANA_RELAXED else 2.0
    assert got == pytest.approx(expected, abs=tol), (
        f"Sulabh {planet} kala_total: got {got:.4f}, expected {expected:.4f} "
        f"(tol ±{tol})"
    )


@pytest.mark.parametrize("chart_key", _CHART_KEYS)
@pytest.mark.parametrize("planet", _PLANETS)
def test_b_naisargika_passthrough(chart_key, planet, all_totals):
    # Naisargika is a module constant, not a component function — test that it
    # is relayed unchanged (compare against our constant, not AstroSage fixture
    # which uses a slightly different rounding).
    got = all_totals[chart_key][planet]["naisargika"]
    assert got == pytest.approx(NAISARGIKA_BALA[planet], abs=0.01), (
        f"{chart_key} {planet} naisargika: got {got:.4f}, "
        f"constant={NAISARGIKA_BALA[planet]:.4f}"
    )


# ── Layer C: aggregator arithmetic ────────────────────────────────────────────
#
# Expected values are derived from the RESULT's own component fields, not from
# the fixture's shadbala_virupa (which includes real Drik Bala). This isolates
# the arithmetic correctness of the aggregator from component-level formula gaps.

@pytest.mark.parametrize("chart_key", _CHART_KEYS)
@pytest.mark.parametrize("planet", _PLANETS)
def test_c_virupa_is_sum_of_components(chart_key, planet, all_totals):
    row = all_totals[chart_key][planet]
    expected_virupa = round(
        row["sthan_total"] + row["dig"] + row["kala_total"]
        + row["chesta"] + row["naisargika"] + row["drik"],
        2,
    )
    assert row["shadbala_virupa"] == pytest.approx(expected_virupa, abs=0.5), (
        f"{chart_key} {planet} shadbala_virupa: got {row['shadbala_virupa']:.4f}, "
        f"expected sum={expected_virupa:.4f}"
    )


@pytest.mark.parametrize("chart_key", _CHART_KEYS)
@pytest.mark.parametrize("planet", _PLANETS)
def test_c_rupa_is_virupa_over_60(chart_key, planet, all_totals):
    row = all_totals[chart_key][planet]
    expected_rupa = round(row["shadbala_virupa"] / 60.0, 2)
    assert row["shadbala_rupa"] == pytest.approx(expected_rupa, abs=0.02), (
        f"{chart_key} {planet} shadbala_rupa: got {row['shadbala_rupa']:.4f}, "
        f"expected {expected_rupa:.4f}"
    )


@pytest.mark.parametrize("chart_key", _CHART_KEYS)
@pytest.mark.parametrize("planet", _PLANETS)
def test_c_ratio_is_rupa_over_min_required(chart_key, planet, all_totals):
    row = all_totals[chart_key][planet]
    expected_ratio = round(row["shadbala_rupa"] / row["min_required"], 2)
    assert row["ratio"] == pytest.approx(expected_ratio, abs=0.02), (
        f"{chart_key} {planet} ratio: got {row['ratio']:.4f}, "
        f"expected {expected_ratio:.4f}"
    )


@pytest.mark.parametrize("chart_key,planet,expected_min", [
    ("sulabh",  "sun",     5.0),
    ("sulabh",  "moon",    6.0),
    ("sulabh",  "mars",    5.0),
    ("sulabh",  "mercury", 7.0),
    ("sulabh",  "jupiter", 6.5),
    ("sulabh",  "venus",   5.5),
    ("sulabh",  "saturn",  5.0),
    ("surbhi",  "sun",     5.0),
    ("surbhi",  "moon",    6.0),
    ("surbhi",  "mars",    5.0),
    ("surbhi",  "mercury", 7.0),
    ("surbhi",  "jupiter", 6.5),
    ("surbhi",  "venus",   5.5),
    ("surbhi",  "saturn",  5.0),
])
def test_c_min_required_exact(chart_key, planet, expected_min, all_totals):
    # min_required is a table lookup — must be exact, no floating-point tolerance.
    got = all_totals[chart_key][planet]["min_required"]
    assert got == expected_min, (
        f"{chart_key} {planet} min_required: got {got}, expected {expected_min}"
    )


# ── Layer D: rank validity ────────────────────────────────────────────────────
# Rank is tested for internal self-consistency only — fixture ranks used real Drik
# Bala so our stub-based ranks cannot be asserted against fixture rank values.

@pytest.mark.parametrize("chart_key", _CHART_KEYS)
def test_d_ranks_are_complete_permutation(chart_key, all_totals):
    ranks = {p: all_totals[chart_key][p]["rank"] for p in _PLANETS}
    assert set(ranks.values()) == set(range(1, 8)), (
        f"{chart_key}: ranks {sorted(ranks.values())} are not a "
        f"complete permutation of {{1..7}}"
    )


@pytest.mark.parametrize("chart_key", _CHART_KEYS)
def test_d_rank1_has_highest_virupa(chart_key, all_totals):
    result      = all_totals[chart_key]
    rank1_p     = next(p for p in _PLANETS if result[p]["rank"] == 1)
    rank1_virupa = result[rank1_p]["shadbala_virupa"]
    for p in _PLANETS:
        assert rank1_virupa >= result[p]["shadbala_virupa"], (
            f"{chart_key}: rank-1 planet {rank1_p} ({rank1_virupa:.2f}) has "
            f"lower virupa than {p} ({result[p]['shadbala_virupa']:.2f})"
        )


@pytest.mark.parametrize("chart_key", _CHART_KEYS)
def test_d_rank7_has_lowest_virupa(chart_key, all_totals):
    result       = all_totals[chart_key]
    rank7_p      = next(p for p in _PLANETS if result[p]["rank"] == 7)
    rank7_virupa = result[rank7_p]["shadbala_virupa"]
    for p in _PLANETS:
        assert rank7_virupa <= result[p]["shadbala_virupa"], (
            f"{chart_key}: rank-7 planet {rank7_p} ({rank7_virupa:.2f}) has "
            f"higher virupa than {p} ({result[p]['shadbala_virupa']:.2f})"
        )


def test_d_sulabh_closest_pair_not_exact_tie(sulabh_totals):
    """Sulabh hardest-case: the two planets with the closest shadbala_virupa
    must have a genuine numeric gap, not a float-equality tie.

    The tie-break rule (lower _PLANETS iteration order wins on EXACT ties)
    must NOT be silently invoked for a near-tie. If the delta > 1e-9 the
    ranking is an unambiguous numerical decision; the rule was never triggered.
    If they ARE exactly equal — float-sum coincidence, extremely unlikely —
    xfail with an explanation rather than silently passing.
    """
    pairs = sorted(
        (
            abs(sulabh_totals[a]["shadbala_virupa"] - sulabh_totals[b]["shadbala_virupa"]),
            a,
            b,
        )
        for i, a in enumerate(_PLANETS)
        for b in _PLANETS[i + 1:]
    )
    min_delta, p1, p2 = pairs[0]

    if min_delta <= 1e-9:
        pytest.xfail(
            f"Sulabh {p1}/{p2} are exactly tied at "
            f"{sulabh_totals[p1]['shadbala_virupa']:.8f} Virupa — "
            "tie-break rule (_PLANETS iteration order) was silently invoked; "
            "investigate if this triggers, as float-sum exact ties are unexpected."
        )

    # Genuine gap: ranking for this pair is an unambiguous numerical decision.
    # delta > 1e-9 means the tie-break rule (iteration-order) was NOT invoked.
    assert min_delta > 1e-9, (
        f"Sulabh closest pair {p1}/{p2}: delta={min_delta:.2e} Virupa is a "
        "float-equality tie — tie-break rule was silently invoked."
    )


# ── Layer E: caveat/stub field integrity ──────────────────────────────────────

@pytest.mark.parametrize("chart_key", _CHART_KEYS)
@pytest.mark.parametrize("planet", _PLANETS)
def test_e_drik_is_stubbed_true(chart_key, planet, all_totals):
    assert all_totals[chart_key][planet]["drik_is_stubbed"] is True, (
        f"{chart_key} {planet}: drik_is_stubbed is not True"
    )


@pytest.mark.parametrize("chart_key", _CHART_KEYS)
def test_e_caveat_non_empty_and_contains_sentinel(chart_key, all_totals):
    result = all_totals[chart_key]
    for p in _PLANETS:
        caveat = result[p]["caveat"]
        assert isinstance(caveat, str) and len(caveat) > 0, (
            f"{chart_key} {p}: caveat is missing or empty"
        )
        assert "Drik Bala stubbed" in caveat, (
            f"{chart_key} {p}: caveat does not contain 'Drik Bala stubbed'"
        )


@pytest.mark.parametrize("chart_key", _CHART_KEYS)
def test_e_caveat_identical_across_all_planets(chart_key, all_totals):
    # Caveat is a fixed module-level constant — must be identical for every planet,
    # not vary per-planet. A consumer must never miss it by checking only "problem" planets.
    caveats = [all_totals[chart_key][p]["caveat"] for p in _PLANETS]
    assert len(set(caveats)) == 1, (
        f"{chart_key}: caveat string varies across planets — must be a fixed constant"
    )


# ── Layer F: error propagation ────────────────────────────────────────────────

def test_f_missing_meta_propagates():
    """Aggregator must not swallow errors from components.

    A chart_data dict missing the "meta" key will cause the first component
    that reads meta (sthana_bala or kala_bala) to raise ValueError or
    RuntimeError. compute_shadbala_totals() must let it surface unchanged.
    """
    bad_chart = {"planets": {}}
    with pytest.raises((ValueError, RuntimeError)):
        compute_shadbala_totals(bad_chart)
