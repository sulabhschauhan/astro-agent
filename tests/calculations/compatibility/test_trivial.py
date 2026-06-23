"""Tests for agent/calculations/compatibility/trivial.py -- P2.4.1a
trivial-arithmetic koota calculators (Varna, Vashya, Tara, Gana).

AstroSage reference pair: Sulabh (boy) x Surbhi (girl), per
tests/fixtures/astrosage_sulabh_surbhi_kundli_milan.md (human-audit only --
NOT parsed here; expected values are hardcoded directly per that file's
own stated convention). Real natal info is derived via calculate_chart()
(same entry point as test_muhurta_windows.py) plus chandrabala.py's
_moon_sign() / tarabala.py's _moon_nakshatra() reused directly -- no
duplicated derivation arithmetic.

Tara symmetry note: TARA_SCORE is value-symmetric by construction (see
trivial.py's module docstring), so compute_tara_koota's SCORE is provably
swap-invariant. The symmetry-contract test for Tara therefore asserts
swap-invariance of the score (documenting the proof) and swap-dependence
of the per-direction intermediates in `details` instead of asserting a
score difference -- resolved explicitly with Sulabh this session, see the
P2.4.1a report.
"""

import dataclasses
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # project root

import pytest
import swisseph as swe

import agent.calculations.transits.chandrabala as chandrabala_module
import agent.calculations.transits.tarabala as tarabala_module
from agent.calculations.compatibility import _ashtakoot_tables as ak
from agent.calculations.compatibility.koota_types import KootaNatalInfo, KootaResult
from agent.calculations.compatibility.trivial import (
    _vashya_group,
    compute_gana_koota,
    compute_tara_koota,
    compute_varna_koota,
    compute_vashya_koota,
)
from agent.chart_calculator import _calc_planets, calculate_chart


def _natal_info(name: str, dob: str, tob: str, place: str) -> KootaNatalInfo:
    """Real natal info via calculate_chart() + the existing chandrabala.py /
    tarabala.py derivation helpers, reused directly -- not re-derived.
    """
    chart = calculate_chart(name, dob, tob, place)
    jd_ut = chart["meta"]["jd_ut"]
    asc_lon = chart["meta"]["asc_lon_sidereal"]
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    moon_longitude = _calc_planets(jd_ut, asc_lon)["Moon"]["longitude"]
    moon_sign = chandrabala_module._moon_sign(jd_ut)
    nakshatra = tarabala_module._moon_nakshatra(jd_ut)
    return KootaNatalInfo(
        moon_sign=moon_sign, moon_longitude=moon_longitude, nakshatra=nakshatra
    )


def _sulabh() -> KootaNatalInfo:
    return _natal_info("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")


def _surbhi() -> KootaNatalInfo:
    return _natal_info("Surbhi", "11 Sep 1992", "10:30", "Patna, India")


# ── 0. Sanity: real fixture data matches the AstroSage report's classifications ──

def test_sulabh_surbhi_real_natal_info_matches_fixture_basis():
    sulabh, surbhi = _sulabh(), _surbhi()
    assert sulabh.moon_sign == 7    # Scorpio -- fixture "Boy: Scorpio" (Bhakoot row)
    assert sulabh.nakshatra == 15   # Vishakha
    assert surbhi.moon_sign == 10   # Aquarius -- fixture "Girl: Aquarius" (Bhakoot row)
    assert surbhi.nakshatra == 23   # Shatabhisha


# ── 1. AstroSage reference parity ───────────────────────────────────────────────

def test_varna_koota_astrosage_parity():
    result = compute_varna_koota(_sulabh(), _surbhi())
    assert result.score == 1
    assert result.max_score == 1
    assert result.details == {"boy_varna": "Brahmin", "girl_varna": "Shudra"}


def test_varna_koota_reversed_pair_differs_from_forward():
    forward = compute_varna_koota(_sulabh(), _surbhi())
    reversed_ = compute_varna_koota(_surbhi(), _sulabh())
    assert reversed_.score == 0  # Shudra boy >= Brahmin girl is false
    assert reversed_.score != forward.score


def test_vashya_koota_astrosage_parity():
    result = compute_vashya_koota(_sulabh(), _surbhi())
    assert result.score == 1
    assert result.max_score == 2
    assert result.details == {"boy_vashya_group": "Keeta", "girl_vashya_group": "Manava"}


def test_vashya_koota_reversed_pair_real_data_coincidentally_equal():
    # Documented, not a bug: VASHYA_SCORE[("Manava","Keeta")] ==
    # VASHYA_SCORE[("Keeta","Manava")] == 1 for this specific pair of
    # groups, even though the matrix is genuinely asymmetric overall (see
    # test_vashya_koota_symmetry_contract_synthetic_asymmetric_pair below
    # for a pair where it does differ).
    forward = compute_vashya_koota(_sulabh(), _surbhi())
    reversed_ = compute_vashya_koota(_surbhi(), _sulabh())
    assert reversed_.score == 1
    assert reversed_.score == forward.score


def test_tara_koota_astrosage_parity():
    result = compute_tara_koota(_sulabh(), _surbhi())
    assert result.score == 3.0
    assert result.max_score == 3
    assert result.details["boy_to_girl_category"] == "AUSPICIOUS"
    assert result.details["girl_to_boy_category"] == "AUSPICIOUS"


def test_tara_koota_reversed_pair_score_is_provably_equal():
    # See module docstring / test-file docstring: TARA_SCORE is
    # value-symmetric, so this is not a coincidence of this specific pair.
    forward = compute_tara_koota(_sulabh(), _surbhi())
    reversed_ = compute_tara_koota(_surbhi(), _sulabh())
    assert reversed_.score == forward.score == 3.0


def test_gana_koota_astrosage_parity():
    result = compute_gana_koota(_sulabh(), _surbhi())
    assert result.score == 6
    assert result.max_score == 6
    assert result.details == {"boy_gana": "Rakshasa", "girl_gana": "Rakshasa"}


def test_gana_koota_reversed_pair_equal_symmetric_by_design():
    forward = compute_gana_koota(_sulabh(), _surbhi())
    reversed_ = compute_gana_koota(_surbhi(), _sulabh())
    assert reversed_.score == forward.score == 6


# ── 2. Structural invariants across the full relevant input space ──────────────

_ARBITRARY_VALID_NAK = 0
_ARBITRARY_VALID_LON = 5.0


def test_varna_koota_structural_invariant_full_sign_space():
    for boy_sign in range(12):
        for girl_sign in range(12):
            boy = KootaNatalInfo(boy_sign, _ARBITRARY_VALID_LON, _ARBITRARY_VALID_NAK)
            girl = KootaNatalInfo(girl_sign, _ARBITRARY_VALID_LON, _ARBITRARY_VALID_NAK)
            result = compute_varna_koota(boy, girl)
            assert result.max_score == ak.KOOTA_SCORE_WEIGHTS["Varna"]
            assert 0 <= result.score <= result.max_score


# Representative longitudes per sign: one value for the 10 unsplit signs,
# both halves (just past 0deg and just past 15deg in-sign) for Sag/Cap.
_REPRESENTATIVE_LONGITUDES_BY_SIGN = {
    sign: [sign * 30.0 + 7.0, sign * 30.0 + 22.0] if sign in (8, 9) else [sign * 30.0 + 10.0]
    for sign in range(12)
}


def test_vashya_koota_structural_invariant_full_sign_and_half_space():
    for boy_sign in range(12):
        for boy_lon in _REPRESENTATIVE_LONGITUDES_BY_SIGN[boy_sign]:
            for girl_sign in range(12):
                for girl_lon in _REPRESENTATIVE_LONGITUDES_BY_SIGN[girl_sign]:
                    boy = KootaNatalInfo(boy_sign, boy_lon, _ARBITRARY_VALID_NAK)
                    girl = KootaNatalInfo(girl_sign, girl_lon, _ARBITRARY_VALID_NAK)
                    result = compute_vashya_koota(boy, girl)
                    assert result.max_score == ak.KOOTA_SCORE_WEIGHTS["Vashya"]
                    assert 0 <= result.score <= result.max_score


def test_tara_koota_structural_invariant_full_nakshatra_space():
    for boy_nak in range(27):
        for girl_nak in range(27):
            boy = KootaNatalInfo(0, _ARBITRARY_VALID_LON, boy_nak)
            girl = KootaNatalInfo(0, _ARBITRARY_VALID_LON, girl_nak)
            result = compute_tara_koota(boy, girl)
            assert result.max_score == ak.KOOTA_SCORE_WEIGHTS["Tara"]
            assert 0 <= result.score <= result.max_score
            assert result.score in (0, 1.5, 3.0)


def test_gana_koota_structural_invariant_full_nakshatra_space():
    for boy_nak in range(27):
        for girl_nak in range(27):
            boy = KootaNatalInfo(0, _ARBITRARY_VALID_LON, boy_nak)
            girl = KootaNatalInfo(0, _ARBITRARY_VALID_LON, girl_nak)
            result = compute_gana_koota(boy, girl)
            assert result.max_score == ak.KOOTA_SCORE_WEIGHTS["Gana"]
            assert 0 <= result.score <= result.max_score


# ── 3. Symmetry contract ────────────────────────────────────────────────────────

def test_varna_koota_symmetry_contract_is_asymmetric():
    boy, girl = _sulabh(), _surbhi()
    assert compute_varna_koota(boy, girl).score != compute_varna_koota(girl, boy).score


def test_vashya_koota_symmetry_contract_synthetic_asymmetric_pair():
    # Leo (Vanachara) x Aries (Chatushpada) -- a cell pair where
    # VASHYA_SCORE genuinely differs by direction (1.5 vs 0), unlike the
    # real Sulabh x Surbhi pair which happens to coincide at 1 either way.
    leo = KootaNatalInfo(4, 4 * 30.0 + 10.0, 0)
    aries = KootaNatalInfo(0, 0 * 30.0 + 10.0, 0)
    forward = compute_vashya_koota(leo, aries)
    reversed_ = compute_vashya_koota(aries, leo)
    assert forward.score != reversed_.score
    assert {forward.score, reversed_.score} == {0, 1.5}


def test_tara_koota_symmetry_contract_score_invariant_details_variant():
    boy, girl = _sulabh(), _surbhi()
    forward = compute_tara_koota(boy, girl)
    reversed_ = compute_tara_koota(girl, boy)

    # Score: provably swap-invariant (TARA_SCORE is value-symmetric).
    assert forward.score == reversed_.score

    # Intermediates: genuinely swap-dependent -- the two per-direction
    # counts are not equal to each other, and they cross-swap correctly.
    assert forward.details["boy_to_girl_count"] != forward.details["girl_to_boy_count"]
    assert forward.details["boy_to_girl_count"] == reversed_.details["girl_to_boy_count"]
    assert forward.details["girl_to_boy_count"] == reversed_.details["boy_to_girl_count"]


def test_gana_koota_symmetry_contract_is_symmetric():
    boy, girl = _sulabh(), _surbhi()
    assert compute_gana_koota(boy, girl).score == compute_gana_koota(girl, boy).score

    # Also check a genuinely cross-gana synthetic pair (not just same-gana).
    deva = KootaNatalInfo(0, _ARBITRARY_VALID_LON, 0)       # Ashwini -- Deva
    rakshasa = KootaNatalInfo(0, _ARBITRARY_VALID_LON, 2)   # Krittika -- Rakshasa
    assert compute_gana_koota(deva, rakshasa).score == compute_gana_koota(rakshasa, deva).score


# ── 4. ValueError on out-of-range natal info ────────────────────────────────────

_VALID = KootaNatalInfo(0, 0.0, 0)

_INVALID_NATAL_INFOS = [
    KootaNatalInfo(-1, 0.0, 0),
    KootaNatalInfo(12, 0.0, 0),
    KootaNatalInfo(0, 0.0, -1),
    KootaNatalInfo(0, 0.0, 27),
    KootaNatalInfo(0, -0.001, 0),
    KootaNatalInfo(0, 360.0, 0),
]

_CALCULATORS = [compute_varna_koota, compute_vashya_koota, compute_tara_koota, compute_gana_koota]


@pytest.mark.parametrize("calculator", _CALCULATORS)
@pytest.mark.parametrize("invalid", _INVALID_NATAL_INFOS)
def test_raises_value_error_for_invalid_boy(calculator, invalid):
    with pytest.raises(ValueError):
        calculator(invalid, _VALID)


@pytest.mark.parametrize("calculator", _CALCULATORS)
@pytest.mark.parametrize("invalid", _INVALID_NATAL_INFOS)
def test_raises_value_error_for_invalid_girl(calculator, invalid):
    with pytest.raises(ValueError):
        calculator(_VALID, invalid)


# ── 5. Frozen dataclasses ────────────────────────────────────────────────────────

def test_koota_natal_info_is_frozen():
    info = KootaNatalInfo(0, 0.0, 0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        info.moon_sign = 1


def test_koota_result_is_frozen():
    result = compute_varna_koota(_VALID, _VALID)
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.score = 99.0


# ── 6. Hardest-case-first: Vashya Sag/Cap half-sign boundary ────────────────────

@pytest.mark.parametrize(
    "sign,degree_in_sign,expected_group",
    [
        (8, 14.999, "Manava"),       # Sagittarius, just below boundary
        (8, 15.0, "Chatushpada"),    # Sagittarius, exactly on boundary -> half 1
        (8, 15.001, "Chatushpada"),  # Sagittarius, just above boundary
        (9, 14.999, "Chatushpada"),  # Capricorn, just below boundary
        (9, 15.0, "Jalachara"),      # Capricorn, exactly on boundary -> half 1
        (9, 15.001, "Jalachara"),    # Capricorn, just above boundary
    ],
)
def test_vashya_group_half_sign_boundary_at_exactly_15_degrees(sign, degree_in_sign, expected_group):
    info = KootaNatalInfo(sign, sign * 30.0 + degree_in_sign, 0)
    assert _vashya_group(info) == expected_group


def test_vashya_koota_half_sign_boundary_via_full_calculator():
    # Same boundary, exercised through the public calculator rather than
    # the private helper, with the partner held fixed at a clean Manava sign.
    partner = KootaNatalInfo(2, 2 * 30.0 + 10.0, 0)  # Gemini, Manava

    just_below = KootaNatalInfo(9, 9 * 30.0 + 14.999, 0)   # Capricorn -> Chatushpada
    on_boundary = KootaNatalInfo(9, 9 * 30.0 + 15.0, 0)    # Capricorn -> Jalachara
    just_above = KootaNatalInfo(9, 9 * 30.0 + 15.001, 0)   # Capricorn -> Jalachara

    below_score = compute_vashya_koota(just_below, partner).score
    on_score = compute_vashya_koota(on_boundary, partner).score
    above_score = compute_vashya_koota(just_above, partner).score

    assert below_score != on_score  # Chatushpada-Manava vs Jalachara-Manava
    assert on_score == above_score  # both half 1 -> Jalachara
