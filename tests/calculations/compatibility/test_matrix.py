"""Tests for agent/calculations/compatibility/matrix.py -- P2.4.1c
symmetric-matrix-lookup koota calculator (Yoni only; Nadi deferred).

AstroSage reference pair: Sulabh (boy) x Surbhi (girl), same
calculate_chart() derivation path as test_trivial.py / test_sign_lord.py.
Sulabh's nakshatra (15, Vishakha) resolves to yoni Vyaghra; Surbhi's (23,
Shatabhisha) resolves to Ashwa -- the locked oracle anchor scores this
pair 1/4.

KNOWN TABLE ASYMMETRY, surfaced rather than silently worked around: the
P2.4.1c prompt's YN-5 spec assumes "every yoni has at least two
nakshatras mapped to it" so a same-yoni diagonal cell can always be
exercised via two DISTINCT nakshatra indices. This is true for 13 of the
14 yonis, but ak.YONI_BY_NAKSHATRA maps exactly ONE nakshatra (index 20,
Uttara Ashadha) to Nakula -- per that table's own citation, Abhijit was
classically paired with Uttara Ashadha for Nakula, and folding Abhijit
back into the 27-nakshatra convention (no separate 28th slot) leaves
Nakula a single-member group, not two. test_yn5_same_yoni_score_is_max
therefore uses the SAME nakshatra index for both boy and girl in the
Nakula case only (i == j, not i != j) -- this still genuinely exercises
the diagonal score=4.0 cell, since compute_yoni_koota's same-yoni check
operates on the resolved yoni string, not on nakshatra-index distinctness.
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
from agent.calculations.compatibility.matrix import compute_yoni_koota
from agent.calculations.compatibility.matrix import compute_nadi_koota
from agent.chart_calculator import _calc_planets, calculate_chart

_ARBITRARY_VALID_SIGN = 0
_ARBITRARY_VALID_LON = 5.0


def _nak(nakshatra: int) -> KootaNatalInfo:
    return KootaNatalInfo(_ARBITRARY_VALID_SIGN, _ARBITRARY_VALID_LON, nakshatra)


def _natal_info(name: str, dob: str, tob: str, place: str) -> KootaNatalInfo:
    """Real natal info via calculate_chart() -- identical derivation path to
    test_trivial.py / test_sign_lord.py's helper of the same name (not
    imported from there; each test file derives its own fixtures per the
    project's per-module duplication convention).
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


# ── YN-1: AstroSage reference parity ────────────────────────────────────────

def test_yn1_sulabh_surbhi_astrosage_reference_vyaghra_ashwa():
    result = compute_yoni_koota(_sulabh(), _surbhi())
    assert result.score == 1.0
    assert result.max_score == 4
    assert result.details["boy_yoni"] == "Vyaghra"
    assert result.details["girl_yoni"] == "Ashwa"


# ── YN-2: same-yoni max, diagonal sanity check ───────────────────────────────

def test_yn2_ashwini_shatabhisha_both_ashwa_scores_max():
    # Ashwini (nakshatra 0) and Shatabhisha (nakshatra 23) both = Ashwa.
    result = compute_yoni_koota(_nak(0), _nak(23))
    assert result.score == 4.0
    assert result.details["is_same_yoni"] is True


# ── YN-3: Mahabair enemy pair, zero score ────────────────────────────────────

def test_yn3_ashwini_hasta_ashwa_mahisha_mahabair_scores_zero():
    # Ashwini (nakshatra 0, Ashwa) x Hasta (nakshatra 12, Mahisha) --
    # one of the 7 classically-locked Mahabair extreme-enmity pairs.
    result = compute_yoni_koota(_nak(0), _nak(12))
    assert result.score == 0.0
    assert result.details["is_same_yoni"] is False


# ── YN-4: full Mahabair coverage (all 7 pairs) ──────────────────────────────

_MAHABAIR_NAKSHATRA_PAIRS = [
    (0, 12, "Ashwa-Mahisha"),     # Ashwini, Hasta
    (1, 22, "Gaja-Simha"),        # Bharani, Dhanishtha
    (2, 19, "Mesha-Vanara"),      # Krittika, Purva Ashadha
    (3, 20, "Sarpa-Nakula"),      # Rohini, Uttara Ashadha
    (5, 16, "Shwana-Mriga"),      # Ardra, Anuradha
    (6, 9, "Marjara-Mushaka"),    # Punarvasu, Magha
    (13, 11, "Vyaghra-Gow"),      # Chitra, Uttara Phalguni
]


@pytest.mark.parametrize("boy_nak,girl_nak,pair_name", _MAHABAIR_NAKSHATRA_PAIRS)
def test_yn4_all_seven_mahabair_pairs_score_zero(boy_nak, girl_nak, pair_name):
    result = compute_yoni_koota(_nak(boy_nak), _nak(girl_nak))
    assert result.score == 0.0, f"{pair_name} did not score 0"
    # Cross-check the pair really is one of the 7 locked Mahabair pairs --
    # guards against a typo in the nakshatra-index table above silently
    # testing the wrong animals.
    boy_yoni, girl_yoni = result.details["boy_yoni"], result.details["girl_yoni"]
    assert frozenset({boy_yoni, girl_yoni}) in ak.YONI_MAHABAIR_PAIRS


def test_yn4_seven_mahabair_pairs_cover_all_locked_pairs_no_duplicates():
    covered = {frozenset({ak.YONI_BY_NAKSHATRA[b], ak.YONI_BY_NAKSHATRA[g]})
               for b, g, _ in _MAHABAIR_NAKSHATRA_PAIRS}
    assert covered == set(ak.YONI_MAHABAIR_PAIRS)
    assert len(covered) == 7


# ── YN-5: full same-yoni diagonal coverage (all 14 yonis) ───────────────────

# (boy_nak, girl_nak, yoni_name) -- two distinct nakshatra indices per
# yoni, EXCEPT Nakula (only one nakshatra, index 20, maps to it -- see
# module docstring's KNOWN TABLE ASYMMETRY note).
_SAME_YONI_NAKSHATRA_PAIRS = [
    (0, 23, "Ashwa"),
    (1, 26, "Gaja"),
    (2, 7, "Mesha"),
    (3, 4, "Sarpa"),
    (5, 18, "Shwana"),
    (6, 8, "Marjara"),
    (9, 10, "Mushaka"),
    (11, 25, "Gow"),
    (12, 14, "Mahisha"),
    (13, 15, "Vyaghra"),
    (16, 17, "Mriga"),
    (19, 21, "Vanara"),
    (20, 20, "Nakula"),  # single-member yoni -- i == j, see module docstring
    (22, 24, "Simha"),
]


@pytest.mark.parametrize("boy_nak,girl_nak,yoni_name", _SAME_YONI_NAKSHATRA_PAIRS)
def test_yn5_same_yoni_score_is_max(boy_nak, girl_nak, yoni_name):
    result = compute_yoni_koota(_nak(boy_nak), _nak(girl_nak))
    assert result.score == 4.0, f"{yoni_name} diagonal did not score 4"
    assert result.details["is_same_yoni"] is True
    assert result.details["boy_yoni"] == result.details["girl_yoni"] == yoni_name


def test_yn5_fourteen_pairs_cover_all_locked_yonis_no_duplicates():
    covered = {name for _, _, name in _SAME_YONI_NAKSHATRA_PAIRS}
    assert covered == set(ak.YONI_ANIMALS)
    assert len(covered) == 14


# ── Structural invariants ───────────────────────────────────────────────────

def test_inv1_koota_result_is_frozen():
    result = compute_yoni_koota(_nak(0), _nak(23))
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.score = 99.0


_INVALID_NAKSHATRAS = [-1, 27, -100, 1000]


@pytest.mark.parametrize("invalid_nak", _INVALID_NAKSHATRAS)
def test_inv2_raises_value_error_for_invalid_boy_nakshatra(invalid_nak):
    with pytest.raises(ValueError):
        compute_yoni_koota(_nak(invalid_nak), _nak(0))


@pytest.mark.parametrize("invalid_nak", _INVALID_NAKSHATRAS)
def test_inv2_raises_value_error_for_invalid_girl_nakshatra(invalid_nak):
    with pytest.raises(ValueError):
        compute_yoni_koota(_nak(0), _nak(invalid_nak))


# INV-3: score is swap-invariant -- ak.YONI_SCORE_MATRIX is symmetric by
# classical convention (P2.4.0's own test_yoni_score_matrix_is_symmetric
# structural test enforces this), so swapping boy/girl can never change
# the score. Same documentation pattern as the Tara/Bhakoot/Graha Maitri
# swap-invariance tests from P2.4.1a/b. Three pairs spanning the score
# range: a zero, a mid-range, and a max.
@pytest.mark.parametrize(
    "boy_nak,girl_nak,expected_score",
    [
        (0, 12, 0.0),   # Ashwa x Mahisha -- Mahabair, zero
        (0, 1, 2.0),    # Ashwa x Gaja -- mid-range
        (0, 23, 4.0),   # Ashwa x Ashwa -- same yoni, max
    ],
)
def test_inv3_yoni_koota_score_is_swap_invariant(boy_nak, girl_nak, expected_score):
    forward = compute_yoni_koota(_nak(boy_nak), _nak(girl_nak))
    reversed_ = compute_yoni_koota(_nak(girl_nak), _nak(boy_nak))
    assert forward.score == reversed_.score == expected_score


# INV-4: details ARE direction-aware even though the score is swap-
# invariant -- boy_yoni/girl_yoni swap correctly on reversal.
def test_inv4_sulabh_surbhi_yoni_details_swap_on_reversal():
    forward = compute_yoni_koota(_sulabh(), _surbhi())
    reversed_ = compute_yoni_koota(_surbhi(), _sulabh())

    assert forward.details["boy_yoni"] == reversed_.details["girl_yoni"] == "Vyaghra"
    assert forward.details["girl_yoni"] == reversed_.details["boy_yoni"] == "Ashwa"
    assert forward.score == reversed_.score  # score itself unaffected


# ═════════════════════════════════════════════════════════════════════════
# Nadi -- P2.4.1c Prompt 2 of 2 (AstroSage parity, no cancellation)
# ═════════════════════════════════════════════════════════════════════════

# ── ND-1: AstroSage reference parity ────────────────────────────────────────

def test_nd1_sulabh_surbhi_astrosage_reference_no_dosha():
    result = compute_nadi_koota(_sulabh(), _surbhi())
    assert result.score == 8.0
    assert result.max_score == 8
    assert result.details["boy_nadi"] == "Antya"   # Sulabh, Vishakha
    assert result.details["girl_nadi"] == "Adi"    # Surbhi, Shatabhisha
    assert result.details["dosha"] is False
    assert result.warnings == ()


# ── ND-2/3/4: AstroSage empirical-lock fixtures (synthetic pairs) ──────────
# Three synthetic pairs from the P2.4.1c design chat, designed to isolate
# Nadi cancellation Rule #1 (same Rashi, different Nakshatra) and Rule #3
# (different Rashi, different Nakshatra) independently from the
# same-nakshatra-different-pada case -- AstroSage returned 0/8 on all
# three, confirming NO cancellation logic is applied. See module
# docstring / ak.NADI_CANCELLATION_RULE_CLASSICAL_V1_1.

def test_nd2_pair1_same_rashi_different_nakshatra_not_cancelled():
    # Vishakha + Swati, both Antya Nadi (same Libra Rashi, different
    # Nakshatra) -- AstroSage empirical lock: 0/8, not cancelled.
    boy = _natal_info("ND2-Boy", "1995-02-27", "12:00", "Delhi, India")
    girl = _natal_info("ND2-Girl", "1995-01-24", "12:00", "Delhi, India")
    result = compute_nadi_koota(boy, girl)
    assert result.details["boy_nadi"] == result.details["girl_nadi"] == "Antya"
    assert result.score == 0.0
    assert result.details["dosha"] is True
    assert result.details["cancellation"] is None
    assert result.warnings != ()


def test_nd3_pair2_same_nakshatra_different_pada_not_cancelled():
    # Pushya pada 1 + Pushya pada 3 -- same Nakshatra, different Pada --
    # the EXACT classical cancellation condition (MC p.180), yet AstroSage
    # empirical lock: 0/8, not cancelled in V1.
    boy = _natal_info("ND3-Boy", "1995-02-13", "12:00", "Delhi, India")
    girl = _natal_info("ND3-Girl", "1995-03-13", "12:00", "Delhi, India")
    result = compute_nadi_koota(boy, girl)
    assert result.details["boy_nadi"] == result.details["girl_nadi"] == "Madhya"
    assert result.score == 0.0
    assert result.details["dosha"] is True
    assert result.details["cancellation"] is None


def test_nd4_pair3_different_rashi_different_nakshatra_not_cancelled():
    # Bharani + Chitra, both Madhya Nadi (different Rashi, different
    # Nakshatra) -- AstroSage empirical lock: 0/8, not cancelled.
    boy = _natal_info("ND4-Boy", "1995-03-06", "12:00", "Delhi, India")
    girl = _natal_info("ND4-Girl", "1995-02-19", "12:00", "Delhi, India")
    result = compute_nadi_koota(boy, girl)
    assert result.details["boy_nadi"] == result.details["girl_nadi"] == "Madhya"
    assert result.score == 0.0
    assert result.details["dosha"] is True


# ── ND-5: same-Nadi parametrized (all three groups score 0) ────────────────

@pytest.mark.parametrize(
    "boy_nak,girl_nak,group_name",
    [
        (0, 5, "Adi"),       # Ashwini, Ardra
        (1, 4, "Madhya"),    # Bharani, Mrigashira
        (2, 3, "Antya"),     # Krittika, Rohini
    ],
)
def test_nd5_same_nadi_group_scores_zero(boy_nak, girl_nak, group_name):
    result = compute_nadi_koota(_nak(boy_nak), _nak(girl_nak))
    assert result.score == 0.0, f"{group_name} same-Nadi pair did not score 0"
    assert result.details["dosha"] is True
    assert result.details["boy_nadi"] == result.details["girl_nadi"] == group_name


# ── ND-6: different-Nadi parametrized (all 3 ordered cross-pairs score 8) ──

@pytest.mark.parametrize(
    "boy_nak,girl_nak,boy_group,girl_group",
    [
        (0, 1, "Adi", "Madhya"),     # Ashwini x Bharani
        (0, 2, "Adi", "Antya"),      # Ashwini x Krittika
        (1, 2, "Madhya", "Antya"),   # Bharani x Krittika
    ],
)
def test_nd6_different_nadi_group_scores_max(boy_nak, girl_nak, boy_group, girl_group):
    result = compute_nadi_koota(_nak(boy_nak), _nak(girl_nak))
    assert result.score == 8.0
    assert result.details["dosha"] is False
    assert result.details["boy_nadi"] == boy_group
    assert result.details["girl_nadi"] == girl_group
    assert result.warnings == ()


# ── Nadi structural invariants ───────────────────────────────────────────────

# INV-5: score is swap-invariant -- ak.NADI_SCORE is symmetric in both
# directions (NADI_SCORE[(a,b)] == NADI_SCORE[(b,a)] for every a,b in
# NADI_GROUPS, already enforced by P2.4.0's own
# test_nadi_score_same_nadi_is_zero_different_nadi_is_max structural
# test), so swapping boy/girl can never change the score. Same
# documentation pattern as the Yoni/Tara/Bhakoot/Graha Maitri
# swap-invariance tests from P2.4.1a/b/c. Three pairs: two dosha
# (same-Nadi) cases and one non-dosha (different-Nadi) case.
@pytest.mark.parametrize(
    "boy_nak,girl_nak,expected_score",
    [
        (0, 5, 0.0),    # Adi x Adi -- dosha case
        (1, 4, 0.0),    # Madhya x Madhya -- dosha case
        (0, 1, 8.0),    # Adi x Madhya -- non-dosha case
    ],
)
def test_inv5_nadi_koota_score_is_swap_invariant(boy_nak, girl_nak, expected_score):
    forward = compute_nadi_koota(_nak(boy_nak), _nak(girl_nak))
    reversed_ = compute_nadi_koota(_nak(girl_nak), _nak(boy_nak))
    assert forward.score == reversed_.score == expected_score


# INV-6: cancellation_v1_1 is always populated as a V1.1 expansion marker
# for the answer layer, regardless of dosha/no-dosha outcome -- swept
# across the full 27x27 nakshatra space, not just the named fixtures.
def test_inv6_cancellation_v1_1_marker_always_populated_full_space():
    for boy_nak in range(27):
        for girl_nak in range(27):
            result = compute_nadi_koota(_nak(boy_nak), _nak(girl_nak))
            assert result.details["cancellation_v1_1"] == "same_nakshatra_different_pada"
            assert result.details["cancellation"] is None


# INV-7: ValueError on nakshatra out of 0..26 for both boy and girl.
@pytest.mark.parametrize("invalid_nak", _INVALID_NAKSHATRAS)
def test_inv7_raises_value_error_for_invalid_boy_nakshatra_nadi(invalid_nak):
    with pytest.raises(ValueError):
        compute_nadi_koota(_nak(invalid_nak), _nak(0))


@pytest.mark.parametrize("invalid_nak", _INVALID_NAKSHATRAS)
def test_inv7_raises_value_error_for_invalid_girl_nakshatra_nadi(invalid_nak):
    with pytest.raises(ValueError):
        compute_nadi_koota(_nak(0), _nak(invalid_nak))
