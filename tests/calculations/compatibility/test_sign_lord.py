"""Tests for agent/calculations/compatibility/sign_lord.py -- P2.4.1b
sign-lord-routed koota calculators (Graha Maitri, Bhakoot).

The cancellation matrix exercised below (GM-1..GM-5, BK-1..BK-7) is the
locked test specification from the P2.4.1b design chat -- sign pairs are
not improvised; each anchors a specific NATURAL_FRIENDSHIP/SIGN_LORD
cancellation path. BK-5 is the critical lock test: it formally verifies
that the STRICT mutual-friendship definition (both directions must be
"Friend") rejects the asymmetric Cancer x Sagittarius (Moon-Jupiter) pair,
which a looser "at least one direction Friend" reading would have wrongly
cancelled.

AstroSage reference pair (GM-1, BK-1): Sulabh (boy) x Surbhi (girl), same
calculate_chart() derivation path as test_trivial.py -- real natal info,
not synthetic. All other cases (GM-2..GM-5, BK-2..BK-7) use synthetic
KootaNatalInfo built directly from a sign index, since sign_lord.py's two
calculators consume only moon_sign; nakshatra/moon_longitude are filled
with arbitrary valid placeholders.
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
from agent.calculations.compatibility.sign_lord import (
    compute_bhakoot_koota,
    compute_graha_maitri_koota,
)
from agent.chart_calculator import _calc_planets, calculate_chart

ARIES, TAURUS, GEMINI, CANCER, LEO, VIRGO = 0, 1, 2, 3, 4, 5
LIBRA, SCORPIO, SAGITTARIUS, CAPRICORN, AQUARIUS, PISCES = 6, 7, 8, 9, 10, 11

_ARBITRARY_VALID_LON = 5.0
_ARBITRARY_VALID_NAK = 0


def _sign(sign: int) -> KootaNatalInfo:
    return KootaNatalInfo(sign, _ARBITRARY_VALID_LON, _ARBITRARY_VALID_NAK)


def _natal_info(name: str, dob: str, tob: str, place: str) -> KootaNatalInfo:
    """Real natal info via calculate_chart() -- identical derivation path to
    test_trivial.py's helper of the same name (not imported from there;
    each test file derives its own fixtures per the project's per-module
    duplication convention).
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


# ── Graha Maitri ─────────────────────────────────────────────────────────────

def test_gm1_sulabh_surbhi_astrosage_reference_asymmetric_neutral_enemy():
    # Mars (Sulabh's Scorpio lord) x Saturn (Surbhi's Aquarius lord):
    # Mars->Saturn=Neutral, Saturn->Mars=Enemy -> GRAHA_MAITRI_SCORE[
    # ("Neutral","Enemy")] = 0.5.
    result = compute_graha_maitri_koota(_sulabh(), _surbhi())
    assert result.score == 0.5
    assert result.max_score == 5
    assert result.details["boy_moon_sign_lord"] == "Mars"
    assert result.details["girl_moon_sign_lord"] == "Saturn"
    assert result.details["boy_relation_to_girl_lord"] == "Neutral"
    assert result.details["girl_relation_to_boy_lord"] == "Enemy"


def test_gm2_aries_scorpio_same_mars_lord_short_circuits_to_max():
    result = compute_graha_maitri_koota(_sign(ARIES), _sign(SCORPIO))
    assert result.score == 5.0
    assert result.max_score == 5
    assert result.details["boy_moon_sign_lord"] == "Mars"
    assert result.details["girl_moon_sign_lord"] == "Mars"
    assert result.details["shortcut"] == "same_lord"


def test_gm3_leo_sagittarius_sun_jupiter_mutual_friend_scores_max():
    result = compute_graha_maitri_koota(_sign(LEO), _sign(SAGITTARIUS))
    assert result.score == 5.0
    assert result.details["boy_relation_to_girl_lord"] == "Friend"
    assert result.details["girl_relation_to_boy_lord"] == "Friend"
    assert "shortcut" not in result.details  # genuine friend lookup, not same-lord


def test_gm4_cancer_aries_moon_mars_asymmetric_neutral_friend_scores_4():
    result = compute_graha_maitri_koota(_sign(CANCER), _sign(ARIES))
    assert result.score == 4
    assert result.details["boy_moon_sign_lord"] == "Moon"
    assert result.details["girl_moon_sign_lord"] == "Mars"
    assert result.details["boy_relation_to_girl_lord"] == "Neutral"   # Moon->Mars
    assert result.details["girl_relation_to_boy_lord"] == "Friend"    # Mars->Moon
    # The two relation fields genuinely differ -- proves the asymmetric
    # lookup (not a same-value placeholder) is wired correctly.
    assert result.details["boy_relation_to_girl_lord"] != result.details["girl_relation_to_boy_lord"]


def test_gm5_leo_aquarius_sun_saturn_mutual_enemy_scores_zero():
    result = compute_graha_maitri_koota(_sign(LEO), _sign(AQUARIUS))
    assert result.score == 0
    assert result.details["boy_relation_to_girl_lord"] == "Enemy"
    assert result.details["girl_relation_to_boy_lord"] == "Enemy"


# ── Bhakoot ──────────────────────────────────────────────────────────────────

def test_bk1_sulabh_surbhi_astrosage_reference_no_dosha():
    result = compute_bhakoot_koota(_sulabh(), _surbhi())
    assert result.score == 7
    assert result.max_score == 7
    assert result.details["distance_boy_to_girl"] == 4
    assert result.details["distance_girl_to_boy"] == 10
    assert result.details["dosha_type"] is None
    assert result.details["cancellation"] is None
    assert result.details["auspicious_distance_pair"] == (4, 10)


def test_bk2_aries_scorpio_68_same_mars_lord_cancelled():
    result = compute_bhakoot_koota(_sign(ARIES), _sign(SCORPIO))
    assert result.score == 7
    assert result.details["distance_boy_to_girl"] == 8
    assert result.details["distance_girl_to_boy"] == 6
    assert result.details["dosha_type"] == (6, 8)
    assert result.details["cancellation"] == "same_lord"


def test_bk3_capricorn_aquarius_2_12_same_saturn_lord_cancelled():
    result = compute_bhakoot_koota(_sign(CAPRICORN), _sign(AQUARIUS))
    assert result.score == 7
    assert result.details["distance_boy_to_girl"] == 2
    assert result.details["distance_girl_to_boy"] == 12
    assert result.details["dosha_type"] == (2, 12)
    assert result.details["cancellation"] == "same_lord"


def test_bk4_leo_sagittarius_5_9_sun_jupiter_mutual_friend_cancelled():
    result = compute_bhakoot_koota(_sign(LEO), _sign(SAGITTARIUS))
    assert result.score == 7
    assert result.details["distance_boy_to_girl"] == 5
    assert result.details["distance_girl_to_boy"] == 9
    assert result.details["dosha_type"] == (5, 9)
    assert result.details["cancellation"] == "friend_lords_strict"
    assert result.details["boy_relation_to_girl_lord"] == "Friend"
    assert result.details["girl_relation_to_boy_lord"] == "Friend"


def test_bk5_cancer_sagittarius_68_strict_rejects_asymmetric_moon_jupiter():
    # CRITICAL LOCK TEST: Moon->Jupiter=Neutral, Jupiter->Moon=Friend. STRICT
    # requires BOTH directions Friend, so this asymmetric Friend/Neutral pair
    # must NOT cancel -- a looser "either direction Friend" reading would
    # wrongly cancel this dosha. Same-lord also fails (Moon != Jupiter).
    result = compute_bhakoot_koota(_sign(CANCER), _sign(SAGITTARIUS))
    assert result.score == 0
    assert result.details["distance_boy_to_girl"] == 6
    assert result.details["distance_girl_to_boy"] == 8
    assert result.details["dosha_type"] == (6, 8)
    assert result.details["cancellation"] is None
    assert result.details["boy_relation_to_girl_lord"] == "Neutral"   # Moon->Jupiter
    assert result.details["girl_relation_to_boy_lord"] == "Friend"    # Jupiter->Moon
    assert result.details["cancellation_failure_reason"] == "asymmetric_friendship_fails_strict"


def test_bk6_leo_capricorn_68_mutual_enemies_distinct_failure_reason():
    # Sun-Saturn both directions Enemy -- same-lord fails, STRICT fails.
    # Failure reason must be distinct from BK-5's asymmetric-friendship case.
    result = compute_bhakoot_koota(_sign(LEO), _sign(CAPRICORN))
    assert result.score == 0
    assert result.details["dosha_type"] == (6, 8)
    assert result.details["cancellation"] is None
    assert result.details["boy_relation_to_girl_lord"] == "Enemy"
    assert result.details["girl_relation_to_boy_lord"] == "Enemy"
    assert result.details["cancellation_failure_reason"] == "mutual_enemies"
    assert result.details["cancellation_failure_reason"] != \
        compute_bhakoot_koota(_sign(CANCER), _sign(SAGITTARIUS)).details["cancellation_failure_reason"]


def test_bk7_cancer_leo_2_12_moon_sun_mutual_friend_cancelled():
    result = compute_bhakoot_koota(_sign(CANCER), _sign(LEO))
    assert result.score == 7
    assert result.details["distance_boy_to_girl"] == 2
    assert result.details["distance_girl_to_boy"] == 12
    assert result.details["dosha_type"] == (2, 12)
    assert result.details["cancellation"] == "friend_lords_strict"


# ── Structural invariants ───────────────────────────────────────────────────

_GM_CALCULATORS = [compute_graha_maitri_koota]
_BK_CALCULATORS = [compute_bhakoot_koota]
_ALL_CALCULATORS = _GM_CALCULATORS + _BK_CALCULATORS

_INVALID_SIGNS = [-1, 12, -100, 1000]


@pytest.mark.parametrize("calculator", _ALL_CALCULATORS)
@pytest.mark.parametrize("invalid_sign", _INVALID_SIGNS)
def test_inv2_raises_value_error_for_invalid_boy_moon_sign(calculator, invalid_sign):
    with pytest.raises(ValueError):
        calculator(_sign(invalid_sign), _sign(ARIES))


@pytest.mark.parametrize("calculator", _ALL_CALCULATORS)
@pytest.mark.parametrize("invalid_sign", _INVALID_SIGNS)
def test_inv2_raises_value_error_for_invalid_girl_moon_sign(calculator, invalid_sign):
    with pytest.raises(ValueError):
        calculator(_sign(ARIES), _sign(invalid_sign))


def test_inv1_koota_result_is_frozen():
    result = compute_graha_maitri_koota(_sign(ARIES), _sign(SCORPIO))
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.score = 99.0


# INV-3: score is swap-invariant for both calculators, by table construction
# (see sign_lord.py's module docstring for the proofs), not by coincidence
# of the specific pairs chosen -- same documentation pattern as
# test_trivial.py's Tara swap-invariance test.
@pytest.mark.parametrize(
    "boy_sign,girl_sign",
    [(LEO, SAGITTARIUS), (CANCER, ARIES), (LEO, AQUARIUS)],
)
def test_inv3_graha_maitri_score_is_swap_invariant(boy_sign, girl_sign):
    forward = compute_graha_maitri_koota(_sign(boy_sign), _sign(girl_sign))
    reversed_ = compute_graha_maitri_koota(_sign(girl_sign), _sign(boy_sign))
    assert forward.score == reversed_.score


@pytest.mark.parametrize(
    "boy_sign,girl_sign",
    [(ARIES, SCORPIO), (CANCER, SAGITTARIUS), (LEO, CAPRICORN)],
)
def test_inv3_bhakoot_score_is_swap_invariant(boy_sign, girl_sign):
    forward = compute_bhakoot_koota(_sign(boy_sign), _sign(girl_sign))
    reversed_ = compute_bhakoot_koota(_sign(girl_sign), _sign(boy_sign))
    assert forward.score == reversed_.score


# INV-4: intermediates ARE direction-aware -- they cross-swap (not just
# stay equal) when boy/girl swap, for a genuinely asymmetric pair.
def test_inv4_graha_maitri_relation_intermediates_cross_swap_on_reversal():
    forward = compute_graha_maitri_koota(_sign(CANCER), _sign(ARIES))
    reversed_ = compute_graha_maitri_koota(_sign(ARIES), _sign(CANCER))

    assert forward.details["boy_relation_to_girl_lord"] != forward.details["girl_relation_to_boy_lord"]
    assert forward.details["boy_relation_to_girl_lord"] == reversed_.details["girl_relation_to_boy_lord"]
    assert forward.details["girl_relation_to_boy_lord"] == reversed_.details["boy_relation_to_girl_lord"]
    assert forward.details["boy_moon_sign_lord"] == reversed_.details["girl_moon_sign_lord"]
    assert forward.details["girl_moon_sign_lord"] == reversed_.details["boy_moon_sign_lord"]


def test_inv4_bhakoot_relation_intermediates_cross_swap_on_reversal():
    forward = compute_bhakoot_koota(_sign(CANCER), _sign(SAGITTARIUS))
    reversed_ = compute_bhakoot_koota(_sign(SAGITTARIUS), _sign(CANCER))

    assert forward.details["boy_relation_to_girl_lord"] != forward.details["girl_relation_to_boy_lord"]
    assert forward.details["boy_relation_to_girl_lord"] == reversed_.details["girl_relation_to_boy_lord"]
    assert forward.details["girl_relation_to_boy_lord"] == reversed_.details["boy_relation_to_girl_lord"]
    assert forward.details["distance_boy_to_girl"] == reversed_.details["distance_girl_to_boy"]
    assert forward.details["distance_girl_to_boy"] == reversed_.details["distance_boy_to_girl"]


# ── Structural invariant across the full relevant input space ──────────────
# Referenced by name in sign_lord.py's module docstring (Bhakoot
# cancellation-failure-reason note) -- exercises every sign pair, proving
# the swap-invariance proof holds generally, not just for the 7 locked
# BK fixtures, and that every dosha pair resolves to exactly one of the
# three documented failure-reason buckets when uncancelled.
def test_bhakoot_koota_structural_invariant_full_sign_space():
    for boy_sign in range(12):
        for girl_sign in range(12):
            boy, girl = _sign(boy_sign), _sign(girl_sign)
            result = compute_bhakoot_koota(boy, girl)
            reversed_ = compute_bhakoot_koota(girl, boy)
            assert result.max_score == ak.KOOTA_SCORE_WEIGHTS["Bhakoot"]
            assert result.score in (0.0, 7.0)
            assert result.score == reversed_.score  # swap-invariance, full space

            if result.details["dosha_type"] is None:
                assert result.score == 7.0
            elif result.details["cancellation"] is None:
                assert result.score == 0.0
                assert result.details["cancellation_failure_reason"] in (
                    "mutual_enemies",
                    "asymmetric_friendship_fails_strict",
                    "neither_lord_counts_the_other_a_friend",
                )
            else:
                assert result.score == 7.0
                assert result.details["cancellation"] in ("same_lord", "friend_lords_strict")


def test_graha_maitri_koota_structural_invariant_full_sign_space():
    for boy_sign in range(12):
        for girl_sign in range(12):
            boy, girl = _sign(boy_sign), _sign(girl_sign)
            result = compute_graha_maitri_koota(boy, girl)
            reversed_ = compute_graha_maitri_koota(girl, boy)
            assert result.max_score == ak.KOOTA_SCORE_WEIGHTS["GrahaMaitri"]
            assert 0 <= result.score <= 5
            assert result.score == reversed_.score  # swap-invariance, full space
