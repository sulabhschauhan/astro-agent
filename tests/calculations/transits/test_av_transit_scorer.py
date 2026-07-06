"""Tests for agent/calculations/transits/av_transit_scorer.py --
score_av_transit() / AvTransitScore.

Natal tables are Sulabh's, sourced via the same live-pipeline path as
tests/calculations/ashtakavarga/test_ashtakavarga_cross_charts.py
(calculate_chart() -> compute_bav/compute_sav/compute_bav_contributors),
not hardcoded placements -- so a placement/ephemeris wiring failure is
distinguishable from a scorer-logic failure (Layer 0 below).

Layer 0: placement sanity -- pins all 8 of Sulabh's D-1 sign placements
         before anything else runs.

Layer 1: oracle cases T1-T7, hand-derived in design review 2026-07-06
         from PVR Table 60 (kakshya lord order/divisions) + PVR Tables
         19-26 (BAV benefic-house tables) applied to Sulabh's placements.
         Each case's contributor-set CARDINALITY was independently
         cross-checked against Sulabh's row in
         tests/fixtures/jhora_ashtakavarga_cross_charts.md before this
         oracle was written (that fixture is compute_bav's own JHora
         parity oracle -- see test_ashtakavarga_cross_charts.py); this
         file adds the kakshya/verdict/intensity layer on top, which that
         fixture does not itself cover. Every field of every case is
         asserted individually so a mismatch names the exact case+field.

Layer 2: error paths -- Moon/Mercury/Venus fail-closed exclusion,
         degrees_in_sign boundary/negative rejection, unknown planet/sign.

Layer 3: AvTransitScore is a frozen dataclass.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # project root

from dataclasses import FrozenInstanceError

import pytest

from agent.calculations.ashtakavarga.ashtakavarga import (
    compute_bav,
    compute_bav_contributors,
    compute_sav,
)
from agent.calculations.transits.av_transit_scorer import (
    AvTransitScore,
    AvVerdictBand,
    BavBand,
    BavIntensity,
    score_av_transit,
)
from agent.chart_calculator import calculate_chart

_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

# Same literals as test_ashtakavarga_cross_charts.py's _BIRTH_ARGS["sulabh"]
# (which in turn matches tests/calculations/strength/test_bhava_bala.py's
# own _BIRTH_ARGS), independently duplicated here per this project's
# per-module duplication convention.
_SULABH_BIRTH_ARGS: tuple[str, str, str, str] = (
    "Sulabh", "6 Apr 1988", "00:30", "Calcutta, India",
)

_EXPECTED_PLACEMENTS: dict[str, str] = {
    "Sun": "Pisces",
    "Moon": "Scorpio",
    "Mars": "Capricorn",
    "Mercury": "Pisces",
    "Jupiter": "Aries",
    "Venus": "Taurus",
    "Saturn": "Sagittarius",
    "Lagna": "Sagittarius",
}

# T1-T7 oracle, hand-derived in design review 2026-07-06 from PVR Table 60
# + PVR Tables 19-26 vs Sulabh's placements above. Each case's contributor
# set CARDINALITY independently matched
# tests/fixtures/jhora_ashtakavarga_cross_charts.md's Sulabh BAV grid
# before being written here (see module docstring, Layer 1).
_CASES: dict[str, dict] = {
    # T1: plain UNFAVORABLE/UNFAVORABLE, no SAV-dominance, kakshya no-rekha.
    "T1": {
        "planet": "Saturn", "sign": "Scorpio", "degrees": 5.0,
        "bav_rekhas": 2, "bav_band": BavBand.UNFAVORABLE, "bav_intensity": None,
        "sav_value": 25, "sav_band": AvVerdictBand.AVERAGE,
        "verdict": AvVerdictBand.UNFAVORABLE,
        "kakshya_index": 1, "kakshya_lord": "Jupiter", "kakshya_has_rekha": False,
        # contributors = {Mars, Mercury}
    },
    # T2: plain FAVORABLE/FAVORABLE, EXCELLENT intensity, kakshya has-rekha,
    # last kakshya index (7 -> Lagna).
    "T2": {
        "planet": "Jupiter", "sign": "Capricorn", "degrees": 27.0,
        "bav_rekhas": 6, "bav_band": BavBand.FAVORABLE,
        "bav_intensity": BavIntensity.EXCELLENT,
        "sav_value": 36, "sav_band": AvVerdictBand.FAVORABLE,
        "verdict": AvVerdictBand.FAVORABLE,
        "kakshya_index": 7, "kakshya_lord": "Lagna", "kakshya_has_rekha": True,
        # contributors = {Sun, Mars, Mercury, Jupiter, Venus, Lagna}
    },
    # T3: SAV-dominance DOWN-override -- BAV favorable but SAV unfavorable
    # drags verdict down.
    "T3": {
        "planet": "Jupiter", "sign": "Gemini", "degrees": 12.0,
        "bav_rekhas": 5, "bav_band": BavBand.FAVORABLE, "bav_intensity": None,
        "sav_value": 18, "sav_band": AvVerdictBand.UNFAVORABLE,
        "verdict": AvVerdictBand.UNFAVORABLE,
        "kakshya_index": 3, "kakshya_lord": "Sun", "kakshya_has_rekha": True,
        # contributors = {Sun, Mercury, Jupiter, Venus, Lagna}
    },
    # T4: SAV-dominance UP-override -- BAV unfavorable but SAV favorable
    # lifts verdict up; ALSO the zero-degree kakshya boundary (index 0).
    "T4": {
        "planet": "Saturn", "sign": "Capricorn", "degrees": 0.0,
        "bav_rekhas": 3, "bav_band": BavBand.UNFAVORABLE, "bav_intensity": None,
        "sav_value": 36, "sav_band": AvVerdictBand.FAVORABLE,
        "verdict": AvVerdictBand.FAVORABLE,
        "kakshya_index": 0, "kakshya_lord": "Saturn", "kakshya_has_rekha": False,
        # contributors = {Sun, Moon, Mercury}
    },
    # T5: Sun, sign-level only -- all kakshya fields None regardless of degree.
    "T5": {
        "planet": "Sun", "sign": "Virgo", "degrees": 14.2,
        "bav_rekhas": 6, "bav_band": BavBand.FAVORABLE,
        "bav_intensity": BavIntensity.EXCELLENT,
        "sav_value": 33, "sav_band": AvVerdictBand.FAVORABLE,
        "verdict": AvVerdictBand.FAVORABLE,
        "kakshya_index": None, "kakshya_lord": None, "kakshya_has_rekha": None,
    },
    # T6: Mars, sign-level only -- VERY_POOR intensity, kakshya fields None.
    "T6": {
        "planet": "Mars", "sign": "Scorpio", "degrees": 10.0,
        "bav_rekhas": 1, "bav_band": BavBand.UNFAVORABLE,
        "bav_intensity": BavIntensity.VERY_POOR,
        "sav_value": 25, "sav_band": AvVerdictBand.AVERAGE,
        "verdict": AvVerdictBand.UNFAVORABLE,
        "kakshya_index": None, "kakshya_lord": None, "kakshya_has_rekha": None,
    },
    # T7: NEUTRAL BAV -> AVERAGE verdict mapping; ALSO the exact 3.75-degree
    # half-open boundary -- must land in kakshya_index=1 (Jupiter), NOT 0
    # (Saturn), per av_transit_scorer.py's CITATION (e) convention.
    "T7": {
        "planet": "Saturn", "sign": "Aries", "degrees": 3.75,
        "bav_rekhas": 4, "bav_band": BavBand.NEUTRAL, "bav_intensity": None,
        "sav_value": 25, "sav_band": AvVerdictBand.AVERAGE,
        "verdict": AvVerdictBand.AVERAGE,
        "kakshya_index": 1, "kakshya_lord": "Jupiter", "kakshya_has_rekha": False,
        # contributors = {Sun, Moon, Venus, Saturn}
    },
}

_SCORE_FIELDS: tuple[str, ...] = (
    "bav_rekhas", "bav_band", "bav_intensity", "sav_value", "sav_band",
    "verdict", "kakshya_index", "kakshya_lord", "kakshya_has_rekha",
)


@pytest.fixture(scope="module")
def sulabh_placements() -> dict[str, str]:
    """Sulabh's D-1 sign placements via the live pipeline (network-free:
    tests/conftest.py's session-scoped geocoder patch is already active by
    the time this module-scoped fixture runs).
    """
    chart = calculate_chart(*_SULABH_BIRTH_ARGS)
    placements = {"Lagna": chart["lagna_chart"]["ascendant"]}
    pp = chart["planetary_positions"]
    for planet in _PLANETS:
        placements[planet] = pp[planet]["sign"]
    return placements


@pytest.fixture(scope="module")
def sulabh_bav(sulabh_placements) -> dict[str, dict[str, int]]:
    return compute_bav(sulabh_placements)


@pytest.fixture(scope="module")
def sulabh_sav(sulabh_bav) -> dict[str, int]:
    return compute_sav(sulabh_bav)


@pytest.fixture(scope="module")
def sulabh_contributors(sulabh_placements) -> dict[str, dict[str, frozenset]]:
    return compute_bav_contributors(sulabh_placements)


@pytest.fixture(scope="module")
def case_scores(sulabh_bav, sulabh_sav, sulabh_contributors) -> dict[str, AvTransitScore]:
    return {
        case_id: score_av_transit(
            case["planet"], case["sign"], case["degrees"],
            sulabh_bav, sulabh_sav, sulabh_contributors,
        )
        for case_id, case in _CASES.items()
    }


# ── Layer 0: placement sanity ────────────────────────────────────────────

@pytest.mark.parametrize("contributor,expected_sign", sorted(_EXPECTED_PLACEMENTS.items()))
def test_sulabh_placement_sanity(sulabh_placements, contributor, expected_sign):
    """Pins each placement so a placement/ephemeris wiring failure is
    distinguishable from a scorer-logic failure in the Layer 1 oracle
    cases below.
    """
    got = sulabh_placements[contributor]
    assert got == expected_sign, (
        f"Sulabh's derived {contributor} sign {got!r} != expected "
        f"{expected_sign!r} -- this is a placement/ephemeris wiring "
        f"failure, not a scorer failure"
    )


# ── Layer 1: T1-T7 oracle, every field individually ─────────────────────

_CASE_FIELD_PAIRS = [
    (case_id, field) for case_id in _CASES for field in _SCORE_FIELDS
]


@pytest.mark.parametrize(
    "case_id,field",
    _CASE_FIELD_PAIRS,
    ids=[f"{c}-{f}" for c, f in _CASE_FIELD_PAIRS],
)
def test_oracle_case_field(case_scores, case_id, field):
    case = _CASES[case_id]
    score = case_scores[case_id]
    expected = case[field]
    got = getattr(score, field)
    assert got == expected, (
        f"{case_id} ({case['planet']}/{case['sign']}@{case['degrees']}deg): "
        f"field {field!r} mismatch -- got {got!r}, expected {expected!r}"
    )


# ── Layer 2: error paths ─────────────────────────────────────────────────

@pytest.mark.parametrize("excluded_planet", ["Moon", "Mercury", "Venus"])
def test_excluded_planet_raises_value_error(sulabh_bav, sulabh_sav, sulabh_contributors, excluded_planet):
    with pytest.raises(ValueError, match="excluded from V1"):
        score_av_transit(excluded_planet, "Aries", 5.0, sulabh_bav, sulabh_sav, sulabh_contributors)


@pytest.mark.parametrize("bad_degrees", [30.0, -0.0001, -5.0])
def test_degrees_out_of_range_raises_value_error(sulabh_bav, sulabh_sav, sulabh_contributors, bad_degrees):
    with pytest.raises(ValueError, match="degrees_in_sign"):
        score_av_transit("Sun", "Aries", bad_degrees, sulabh_bav, sulabh_sav, sulabh_contributors)


def test_unknown_planet_raises_value_error(sulabh_bav, sulabh_sav, sulabh_contributors):
    with pytest.raises(ValueError, match="unknown transit_planet"):
        score_av_transit("Rahu", "Aries", 5.0, sulabh_bav, sulabh_sav, sulabh_contributors)


def test_unknown_sign_raises_value_error(sulabh_bav, sulabh_sav, sulabh_contributors):
    with pytest.raises(ValueError, match="unrecognized transit_sign"):
        score_av_transit("Sun", "Ophiuchus", 5.0, sulabh_bav, sulabh_sav, sulabh_contributors)


# ── Layer 3: immutability ────────────────────────────────────────────────

def test_av_transit_score_is_frozen(case_scores):
    with pytest.raises(FrozenInstanceError):
        case_scores["T1"].bav_rekhas = 99
