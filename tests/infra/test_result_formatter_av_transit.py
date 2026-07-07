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

Session 56 adds 5 more tests (+1 assertion on test 6 above) covering
_format_career()/_format_dasha()'s OPTIONAL "timing_enrichment" key,
which reuses this file's own _render_av_timing() rendering path (see
result_formatter.py). Hardest case first:
9.  Adversarial leak guard: resolution_note (enrichment-only) must never
    appear anywhere in the av_transit DOMAIN's own answer_payload.
10. career_strength WITHOUT timing_enrichment: answer_payload/sources
    byte-identical to the pre-Session-56 shape.
11. current_dasha WITH a valid timing_enrichment block: key renders,
    resolution_note present, sources extends, and -- with near_boundary
    forced True so demotion_reason is a real (non-None) string -- that
    demotion_reason carries NO enrichment language (GOLDEN STAKE GUARD).
12. Enrichment key present but sub_windows=[]: dropped silently (NOT the
    domain-level never-collapse ValueError -- deliberate inversion, S54
    lock's spirit without its fail-closed letter).
13. career_strength WITH a valid timing_enrichment block (mirrors 11 for
    the other enrichment-eligible domain).
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


# Session 56: domain-generic profile builder for the new career_strength/
# current_dasha enrichment tests below -- _profile() above is intentionally
# left untouched (hardcodes domain="av_transit", used by all 8 original
# tests) rather than widened, per this file's surgical-addition convention.
def _domain_profile(domain: str, payload: dict) -> DomainChartProfile:
    return DomainChartProfile(
        domain=domain,
        chart_id="Sulabh",
        evaluated_at_jd=2460000.0,
        payload=payload,
        stub_caveats=(),
        uncertainty_virupa=0.0,
        uncertainty_days=37.0,
    )


# Session 56: minimal career_strength payload -- read directly off
# _format_career()'s own dict indexing (result_formatter.py) rather than
# guessed. Required keys/shape:
#   "shadbala": dict keyed by planet name, each row needing
#       "shadbala_rupa"/"ratio"/"rank" (read by _significator_block());
#       at least one row with rank==1 (for strongest_planet's next()) and
#       one with rank==7 (for weakest_planet's next()) -- a next() over an
#       empty matching generator raises StopIteration, not a soft default.
#       "sun" and "saturn" keys are ALWAYS read directly (sun_row/
#       saturn_row), independent of tenth_lord.
#   "bhava_bala": dict keyed by house number; only house 10 is read
#       (bhava_bala[10]["total_rupa"]).
#   "tenth_lord": must be a valid key into "shadbala" (reused as "sun"
#       here to avoid a 3rd synthetic planet row -- rank==1 doubles as
#       both the 10th lord and the strongest planet in this fixture).
_CAREER_SHADBALA = {
    "sun": {"shadbala_rupa": 5.0, "ratio": 1.5, "rank": 1},
    "saturn": {"shadbala_rupa": 3.0, "ratio": 0.6, "rank": 7},
}
_CAREER_BHAVA_BALA = {10: {"total_rupa": 4.0}}


def _career_payload(**extra) -> dict:
    return {
        "shadbala": _CAREER_SHADBALA,
        "bhava_bala": _CAREER_BHAVA_BALA,
        "tenth_lord": "sun",
        **extra,
    }


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
    # Session 56 ride-along (passthrough gap flagged in design chat at
    # this file's creation): uncertainty_days is copied straight from
    # profile.uncertainty_days -- never asserted until now.
    assert answer.uncertainty_days == 37.0


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


# ─── Session 56: OPTIONAL "timing_enrichment" (career_strength/current_dasha) ─


def test_enrichment_resolution_note_never_leaks_into_av_transit_domain():
    """Adversarial leak guard: _render_av_timing() is shared between this
    domain's own answer_payload and the enrichment block, but only the
    enrichment call sites (result_formatter.py's _format_career()/
    _format_dasha()) add "resolution_note" on top of its return value --
    _format_av_transit() must never pick it up, at any nesting level.
    """
    profile = _profile(
        {
            "transit_planet": "Saturn",
            "dasha_envelope": _ENVELOPE,
            "sub_windows": [_window(rank=1)],
        }
    )
    answer = format_answer(profile)

    assert set(answer.answer_payload.keys()) == {
        "transit_planet",
        "dasha_envelope",
        "sub_windows",
    }
    assert "resolution_note" not in answer.answer_payload
    assert "resolution_note" not in answer.answer_payload["dasha_envelope"]
    for window in answer.answer_payload["sub_windows"]:
        assert "resolution_note" not in window


def test_career_enrichment_absent_key_byte_identical():
    """No "timing_enrichment" in the payload -> answer_payload/sources are
    exactly the pre-Session-56 shape -- enrichment is purely additive,
    never touches the base career_strength render.
    """
    profile = _domain_profile("career_strength", _career_payload())
    answer = format_answer(profile)

    assert set(answer.answer_payload.keys()) == {
        "career_significators",
        "strongest_planet",
        "weakest_planet",
        "bhava_10_rupa",
    }
    assert "timing_enrichment" not in answer.answer_payload
    assert answer.sources == ("shadbala", "bhava_bala")


def test_dasha_enrichment_present_renders_block_and_extends_sources():
    """current_dasha WITH a valid timing_enrichment block: the block
    renders (dates as "D Mon YYYY", resolution_note present), sources
    extends by the 3 AV modules. near_boundary is forced True so
    demotion_reason is a real, non-None string here -- GOLDEN STAKE
    GUARD: even though timing_enrichment is present, that string must
    carry NONE of the enrichment's own disclosure language.
    """
    payload = {
        "current_mahadasha": {"lord": "Saturn", "start": "1 Jan 2020", "end": "1 Jan 2039"},
        "current_antardasha": {"lord": "Mercury", "start": "1 Jan 2024", "end": "1 Jan 2027"},
        "near_boundary": True,
        "timing_enrichment": {
            "transit_planet": "Saturn",
            "dasha_envelope": {**_ENVELOPE, "start_jd": 2451545.0},
            "sub_windows": [_window(rank=1)],
        },
    }
    profile = _domain_profile("current_dasha", payload)
    answer = format_answer(profile)

    enrichment = answer.answer_payload["timing_enrichment"]
    assert enrichment["dasha_envelope"]["start"] == "1 Jan 2000"
    assert "resolution_note" in enrichment
    assert "37-day" in enrichment["resolution_note"]
    assert "day-level" in enrichment["resolution_note"]

    assert answer.sources == (
        "vimshottari_dasha",
        "ashtakavarga",
        "av_transit_scorer",
        "av_transit_scanner",
    )

    assert answer.demotion_reason is not None
    assert "day-level" not in answer.demotion_reason
    assert "resolution" not in answer.demotion_reason.lower()


def test_enrichment_empty_sub_windows_block_dropped_silently():
    """Enrichment key present but sub_windows=[] -> the whole block is
    dropped silently, sources stays at the base tuple, NO exception.

    Deliberate INVERSION of test_empty_sub_windows_raises_never_collapse_
    value_error above: that test's domain-level av_transit branch is
    REQUIRED and explicitly requested, so it fail-closes (Session 54
    locked decision 2). This OPTIONAL enrichment add-on honors that same
    guard's SPIRIT -- an envelope with no ranked sub-windows is not a
    renderable timing block -- without its fail-closed LETTER, since a
    raise here would block career_strength's own already-valid answer
    over an unrelated, optional enrichment failure (Session 56 locked
    decision: degradation, not fail-closed).
    """
    payload = _career_payload(
        timing_enrichment={
            "transit_planet": "Saturn",
            "dasha_envelope": _ENVELOPE,
            "sub_windows": [],
        }
    )
    profile = _domain_profile("career_strength", payload)

    answer = format_answer(profile)  # must NOT raise

    assert "timing_enrichment" not in answer.answer_payload
    assert answer.sources == ("shadbala", "bhava_bala")


def test_career_enrichment_present_renders_block():
    """career_strength WITH a valid timing_enrichment block -- mirrors
    test_dasha_enrichment_present_renders_block_and_extends_sources for
    the other enrichment-eligible domain, confirming both append paths
    work independently (each domain owns its own base `sources` tuple).
    """
    payload = _career_payload(
        timing_enrichment={
            "transit_planet": "Saturn",
            "dasha_envelope": {**_ENVELOPE, "start_jd": 2451545.0},
            "sub_windows": [_window(rank=1)],
        }
    )
    profile = _domain_profile("career_strength", payload)
    answer = format_answer(profile)

    enrichment = answer.answer_payload["timing_enrichment"]
    assert enrichment["dasha_envelope"]["start"] == "1 Jan 2000"
    assert "resolution_note" in enrichment
    assert "37-day" in enrichment["resolution_note"]
    assert "day-level" in enrichment["resolution_note"]

    assert answer.sources == (
        "shadbala",
        "bhava_bala",
        "ashtakavarga",
        "av_transit_scorer",
        "av_transit_scanner",
    )

    # GOLDEN STAKE GUARD: career_strength's own demotion_reason is always
    # None (result_formatter.py's _format_career() hardcodes it) --
    # confirms enrichment presence didn't somehow introduce one.
    assert answer.demotion_reason is None
