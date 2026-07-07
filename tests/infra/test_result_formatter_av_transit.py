"""Tests for agent/infra/result_formatter.py's "av_transit" domain branch
(_format_av_transit(), Session 55).

No dedicated result_formatter.py test file existed before this one (grepped
tests/ for "format_answer": only tests/infra/test_orchestrator_e2e.py hits,
and that file is an explicit no-mocks, real-chart end-to-end suite per its
own docstring -- not a home for synthetic-payload unit tests of a single
render branch). This file fills that gap for the av_transit branch only.

All profiles are synthetic DomainChartProfile instances built directly
(frozen dataclass) -- no chart computation, no ephemeris calls. The
av_transit branch is not yet reachable via any live router/orchestrator
path (Session 54 Conflict A: formatter lands before convergence wiring and
router), so format_answer() is exercised directly here rather than through
answer_question().

8 tests, hardest case first:
1. Empty sub_windows -> never-collapse ValueError (Session 54 locked
   decision 2).
2. Rank order preserved even when it contradicts bindu-score ordering --
   the designed-adversarial case that catches an accidental re-sort.
3. Retrograde re-entry: two windows, same sign, different date ranges ->
   both survive, not deduplicated.
4. kakshya_lord=None (Sun/Mars, sign-level only) rendered as None, not
   dropped or stringified.
5. JD rendering at the J2000 epoch anchor (2451545.0 -> "1 Jan 2000"),
   hand-verifiable against swe.revjul().
6. Tier is always TIER_2_RANGE; demotion_reason names both uncertainty
   axes ("37-day" envelope drift + "day-level" sub-window resolution).
7. sources tuple is exactly the 4 contributing modules, in order.
8. Missing "dasha_envelope" key -> KeyError (fail-closed, no partial
   render).
"""

import pytest

from agent.infra.chart_profile import AnswerTier, DomainChartProfile
from agent.infra.result_formatter import format_answer

# Minimal valid dasha_envelope shared by tests that don't specifically
# target envelope fields.
_ENVELOPE = {
    "mahadasha_lord": "Saturn",
    "antardasha_lord": "Mercury",
    "start_jd": 2460000.0,
    "end_jd": 2460100.0,
}


def _window(
    rank: int,
    start_jd: float = 2460000.0,
    end_jd: float = 2460010.0,
    sign: str = "Capricorn",
    bav_bindus: int = 5,
    sav_bindus: int = 28,
    bav_band: str = "moderate",
    sav_band: str = "strong",
    verdict: str = "favorable",
    kakshya_lord: str | None = "Saturn",
) -> dict:
    return {
        "rank": rank,
        "start_jd": start_jd,
        "end_jd": end_jd,
        "sign": sign,
        "bav_bindus": bav_bindus,
        "sav_bindus": sav_bindus,
        "bav_band": bav_band,
        "sav_band": sav_band,
        "verdict": verdict,
        "kakshya_lord": kakshya_lord,
    }


def _profile(payload: dict) -> DomainChartProfile:
    return DomainChartProfile(
        domain="av_transit",
        chart_id="Sulabh",
        evaluated_at_jd=2460000.0,
        payload=payload,
        stub_caveats=(),
        uncertainty_virupa=0.0,
        uncertainty_days=37.0,
    )


def test_empty_sub_windows_raises_never_collapse_value_error():
    profile = _profile(
        {
            "transit_planet": "Saturn",
            "dasha_envelope": _ENVELOPE,
            "sub_windows": [],
        }
    )
    with pytest.raises(ValueError, match="Session 54") as excinfo:
        format_answer(profile)
    assert "never-collapse" in str(excinfo.value)


def test_rank_order_preserved_not_resorted():
    # Rank 1 deliberately has LOWER bav_bindus than rank 2 -- any
    # accidental re-sort by score instead of preserving convergence-layer
    # rank order fails this test.
    windows = [
        _window(rank=1, bav_bindus=2, sign="Capricorn"),
        _window(rank=2, bav_bindus=6, sign="Aquarius"),
    ]
    profile = _profile(
        {
            "transit_planet": "Saturn",
            "dasha_envelope": _ENVELOPE,
            "sub_windows": windows,
        }
    )
    answer = format_answer(profile)
    rendered = answer.answer_payload["sub_windows"]
    assert [w["rank"] for w in rendered] == [1, 2]
    assert [w["sign"] for w in rendered] == ["Capricorn", "Aquarius"]
    assert [w["bav_bindus"] for w in rendered] == [2, 6]


def test_retrograde_reentry_same_sign_not_deduplicated():
    windows = [
        _window(rank=1, sign="Capricorn", start_jd=2460000.0, end_jd=2460010.0),
        _window(rank=2, sign="Capricorn", start_jd=2460050.0, end_jd=2460060.0),
    ]
    profile = _profile(
        {
            "transit_planet": "Saturn",
            "dasha_envelope": _ENVELOPE,
            "sub_windows": windows,
        }
    )
    answer = format_answer(profile)
    rendered = answer.answer_payload["sub_windows"]
    assert len(rendered) == 2
    assert rendered[0]["sign"] == rendered[1]["sign"] == "Capricorn"
    assert rendered[0]["start"] != rendered[1]["start"]


def test_kakshya_lord_none_for_sign_level_planet():
    windows = [_window(rank=1, kakshya_lord=None)]
    profile = _profile(
        {
            "transit_planet": "Sun",
            "dasha_envelope": _ENVELOPE,
            "sub_windows": windows,
        }
    )
    answer = format_answer(profile)
    rendered_window = answer.answer_payload["sub_windows"][0]
    assert "kakshya_lord" in rendered_window
    assert rendered_window["kakshya_lord"] is None


def test_jd_rendering_epoch_anchor():
    envelope = {**_ENVELOPE, "start_jd": 2451545.0}
    profile = _profile(
        {
            "transit_planet": "Saturn",
            "dasha_envelope": envelope,
            "sub_windows": [_window(rank=1)],
        }
    )
    answer = format_answer(profile)
    assert answer.answer_payload["dasha_envelope"]["start"] == "1 Jan 2000"


def test_tier_always_tier_2_range_and_demotion_reason_fixed():
    profile = _profile(
        {
            "transit_planet": "Jupiter",
            "dasha_envelope": _ENVELOPE,
            "sub_windows": [_window(rank=1)],
        }
    )
    answer = format_answer(profile)
    assert answer.tier == AnswerTier.TIER_2_RANGE
    assert "37-day" in answer.demotion_reason
    assert "day-level" in answer.demotion_reason


def test_sources_tuple_exact():
    profile = _profile(
        {
            "transit_planet": "Mars",
            "dasha_envelope": _ENVELOPE,
            "sub_windows": [_window(rank=1, kakshya_lord=None)],
        }
    )
    answer = format_answer(profile)
    assert answer.sources == (
        "ashtakavarga",
        "av_transit_scorer",
        "av_transit_scanner",
        "vimshottari_dasha",
    )


def test_missing_payload_key_raises_key_error():
    profile = _profile(
        {
            "transit_planet": "Saturn",
            "sub_windows": [_window(rank=1)],
            # "dasha_envelope" intentionally omitted.
        }
    )
    with pytest.raises(KeyError):
        format_answer(profile)
