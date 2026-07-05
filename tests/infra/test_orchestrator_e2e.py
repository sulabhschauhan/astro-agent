"""End-to-end tests for the thin-slice answer pipeline (S44.5 checkpoint).

Exercises the full real path: answer_question() -> route_question() ->
build_domain_profile() -> format_answer() -> demotion merge. No mocks --
these are integration tests against real calculate_chart() output for the
4 reference charts (Sulabh, Surbhi, Sheridan, David).

DEVIATIONS FROM THE ORIGINAL TASK PROMPT (each verified against actual
runtime behavior before being written in, per CLAUDE.md's REVIEW-before-
PROCEED working style -- not silently accepted from the prompt as given):

1. Career question changed from "How strong is my career potential?" to
   "How is my career and job strength?". The original scores only 1
   keyword hit ("career") = 0.333 confidence, below calc_router.py's 0.4
   floor -- it is REFUSED, not routed, as-is. Confirmed via a direct
   route_question() call before writing Group A.
2. surbhi_chart fixture uses the canonical Surbhi birth data already used
   by every other Surbhi fixture in this repo (11 Sep 1992, 10:30, Patna,
   India -- see test_kala_bala.py, test_shadbala_totals.py, etc.), NOT the
   (16 Dec 1991, 10:15, Delhi, India) data given in the original task
   prompt. The prompt's own data produces total_score=16.5 for Group C,
   not the 27.5 the prompt itself asserts; the canonical data is the only
   one that produces 27.5. Confirmed by computing both and diffing.
3. test_career_surbhi asserts uncertainty_virupa == 59.0, not 2.0 --
   chart_profile.py has a documented Surbhi-specific override (Kala Bala
   Sun/Jupiter/Saturn Abda/Masa cross-chart divergence, see CLAUDE.md
   "Shadbala Kala Bala" section) that is NOT the general envelope constant
   used for the other 3 charts. That general envelope was lowered 6.0 -> 2.0
   Session 47: envelope basis = AstroSage parity, Ayana Bala Kranti + Sun
   Chesta both RESOLVED Session 47 (see CLAUDE.md "Known Source Divergences
   (V1)" -> "Ayana Bala Kranti"); Surbhi's 59.0 override is unchanged.
4. test_refusal_marriage_no_partner uses "Check our marriage
   compatibility" instead of "Are we compatible?". The latter ties
   marriage_compatibility/career_strength at 0.333 confidence each and is
   refused by the generic confidence-floor path BEFORE ever reaching the
   has_partner_data guard -- it doesn't exercise the code path the test is
   meant to exercise. "Check our marriage compatibility" scores
   marriage_compatibility at 1.0 confidence and is refused specifically
   via route_question's has_partner_data guard
   (demotion_reason="marriage_compatibility requires partner birth data").

Import restriction (per task spec): only answer_question (orchestrator)
and AnswerTier (chart_profile) are imported -- no calc_router,
chart_profile.DomainAnswer, or result_formatter imports. P7.0d's
test_dasha_boundary_reason_selection targets calc_router._near_dasha_boundary
via monkeypatch.setattr's dotted-string form specifically to respect this
restriction without adding an import statement.
"""

import pytest

from agent.infra.chart_profile import AnswerTier
from agent.infra.orchestrator import answer_question

_VALID_PLANETS = {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"}

# See deviation #1 above -- must score >=2 career keyword hits to clear
# calc_router.py's 0.4 confidence floor.
_CAREER_QUESTION = "How is my career and job strength?"
_DASHA_QUESTION = "What dasha period am I in right now?"

# Golden q14's exact wording (tests/fixtures/golden_qa_sulabh.py) -- routes
# via calc_router._BUILT_MODULE_FASTPATH (Session 50/P7.2c), never through
# domain-keyword scoring.
_SADE_SATI_QUESTION = "Am I currently in Sade Sati, and when does the next cycle begin?"


# ─── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def sulabh_chart():
    from agent.chart_calculator import calculate_chart
    return calculate_chart("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")


@pytest.fixture(scope="module")
def surbhi_chart():
    # See deviation #2 above -- canonical Surbhi fixture, not the prompt's
    # (16 Dec 1991, Delhi) data.
    from agent.chart_calculator import calculate_chart
    return calculate_chart("Surbhi", "11 Sep 1992", "10:30", "Patna, India")


@pytest.fixture(scope="module")
def david_chart():
    from agent.chart_calculator import calculate_chart
    return calculate_chart("David", "19 Jan 1976", "22:00", "London, UK")


@pytest.fixture(scope="module")
def sheridan_chart():
    from agent.chart_calculator import calculate_chart
    return calculate_chart("Sheridan", "27 May 1984", "08:00", "Durban, South Africa")


# ─── Shared assertion helpers ────────────────────────────────────────────
# Standalone test functions per chart (locked reference-chart fixture
# template, Session 20) -- these helpers just avoid repeating the same
# assertion block 4x; each chart still gets its own named test function.


def _assert_career_answer(result, *, expected_uncertainty_virupa: float) -> None:
    assert result.domain == "career_strength"
    assert result.tier == AnswerTier.TIER_2_RANGE
    assert result.demotion_reason is not None
    assert "envelope" in result.demotion_reason
    assert result.uncertainty_virupa == expected_uncertainty_virupa

    payload = result.answer_payload
    assert "career_significators" in payload
    sig = payload["career_significators"]
    assert "tenth_lord" in sig
    assert sig["tenth_lord"]["planet"] in _VALID_PLANETS

    assert isinstance(payload["strongest_planet"], str)
    assert isinstance(payload["weakest_planet"], str)

    assert isinstance(result.stub_caveats, tuple)
    assert len(result.stub_caveats) > 0

    for block in sig.values():
        for value in block.values():
            assert isinstance(value, (str, int, float, bool))


def _assert_refusal(result) -> None:
    assert result.tier == AnswerTier.REFUSAL
    assert result.domain is None
    assert result.answer_payload == {}
    assert result.demotion_reason is not None
    assert result.sources == ()


# ─── Group A: Career domain (David first -- hardest case) ─────────────────


def test_career_david(david_chart):
    # envelope basis = AstroSage parity; Ayana Bala Kranti + Sun Chesta both
    # RESOLVED Session 47 -- general envelope lowered 6.0 -> 2.0. Surbhi's
    # ±59 Kala Bala Abda/Masa override (test_career_surbhi below) is unchanged.
    result = answer_question(_CAREER_QUESTION, david_chart)
    _assert_career_answer(result, expected_uncertainty_virupa=2.0)


def test_career_sheridan(sheridan_chart):
    # envelope basis = AstroSage parity; Ayana Bala Kranti + Sun Chesta both
    # RESOLVED Session 47 -- general envelope lowered 6.0 -> 2.0. Surbhi's
    # ±59 Kala Bala Abda/Masa override (test_career_surbhi below) is unchanged.
    result = answer_question(_CAREER_QUESTION, sheridan_chart)
    _assert_career_answer(result, expected_uncertainty_virupa=2.0)


def test_career_surbhi(surbhi_chart):
    # See deviation #3 above -- Surbhi carries a documented 59.0 Virupa
    # override, not the general 2.0 envelope constant used by the other 3
    # charts.
    result = answer_question(_CAREER_QUESTION, surbhi_chart)
    _assert_career_answer(result, expected_uncertainty_virupa=59.0)


def test_career_sulabh(sulabh_chart):
    # envelope basis = AstroSage parity; Ayana Bala Kranti + Sun Chesta both
    # RESOLVED Session 47 -- general envelope lowered 6.0 -> 2.0. Surbhi's
    # ±59 Kala Bala Abda/Masa override (test_career_surbhi above) is unchanged.
    result = answer_question(_CAREER_QUESTION, sulabh_chart)
    _assert_career_answer(result, expected_uncertainty_virupa=2.0)


# ─── Group B: Dasha domain (David first -- hardest case) ───────────────────


def _assert_dasha_answer_shape(result) -> None:
    assert result.domain == "current_dasha"
    # current_dasha is ALWAYS TIER_2_RANGE in V1 (P7.0c design-chat reversal
    # of the Session 45 conditional-demotion behavior): the payload always
    # carries Mahadasha/Antardasha boundary DATES, which carry the
    # documented +/-37-day AstroSage drift regardless of how far
    # evaluated_at sits from a boundary. The old `tier in {T1, T2}`
    # set-membership check would pass just as happily on a T1 regression --
    # tightened to an exact assertion so that can never ship silently again.
    assert result.tier == AnswerTier.TIER_2_RANGE
    assert result.demotion_reason
    # "37-day" is a stable fragment shared by BOTH calc_router demotion_reason
    # wordings (mid-period and near-boundary) -- asserting the fragment, not
    # the full string, so a wording-only edit doesn't churn this test.
    assert "37-day" in result.demotion_reason
    assert "mahadasha" in result.answer_payload
    assert "antardasha" in result.answer_payload
    maha = result.answer_payload["mahadasha"]
    antar = result.answer_payload["antardasha"]
    assert isinstance(maha["lord"], str)
    assert isinstance(antar["lord"], str)
    assert isinstance(maha["start"], str)
    assert isinstance(maha["end"], str)


def test_dasha_david(david_chart):
    result = answer_question(_DASHA_QUESTION, david_chart)
    _assert_dasha_answer_shape(result)


def test_dasha_sheridan(sheridan_chart):
    result = answer_question(_DASHA_QUESTION, sheridan_chart)
    _assert_dasha_answer_shape(result)


def test_dasha_surbhi(surbhi_chart):
    result = answer_question(_DASHA_QUESTION, surbhi_chart)
    _assert_dasha_answer_shape(result)


def test_dasha_sulabh(sulabh_chart):
    result = answer_question(_DASHA_QUESTION, sulabh_chart)
    _assert_dasha_answer_shape(result)
    assert result.answer_payload["mahadasha"]["lord"].lower() == "ketu"


def test_dasha_boundary_reason_selection(sulabh_chart, monkeypatch):
    """Lock WHICH demotion_reason wording calc_router selects, independent
    of wall-clock boundary proximity.

    P7.0c made current_dasha's tier unconditionally TIER_2_RANGE in both
    branches -- only the reason wording depends on _near_dasha_boundary
    now. Monkeypatches calc_router._near_dasha_boundary directly (verified
    call site: route_question's current_dasha branch calls it as a bare
    module-level name, so patching the module attribute is the correct
    seam) rather than constructing a chart that happens to sit near a real
    boundary right now, which would couple this test to wall-clock time.
    """
    monkeypatch.setattr("agent.infra.calc_router._near_dasha_boundary", lambda *a, **k: True)
    near_result = answer_question(_DASHA_QUESTION, sulabh_chart)
    assert near_result.tier == AnswerTier.TIER_2_RANGE
    assert "flip which lord is actually current" in near_result.demotion_reason

    monkeypatch.setattr("agent.infra.calc_router._near_dasha_boundary", lambda *a, **k: False)
    mid_result = answer_question(_DASHA_QUESTION, sulabh_chart)
    assert mid_result.tier == AnswerTier.TIER_2_RANGE
    assert "current lord itself is reliable" in mid_result.demotion_reason
    assert "flip which lord is actually current" not in mid_result.demotion_reason


# ─── Group C: Marriage domain ───────────────────────────────────────────


def test_marriage_sulabh_surbhi(sulabh_chart, surbhi_chart):
    result = answer_question(
        "Are we compatible for marriage?",
        sulabh_chart,
        partner_chart_data=surbhi_chart,
        primary_role="boy",
    )
    assert result.domain == "marriage_compatibility"
    assert result.tier == AnswerTier.TIER_1_EXACT
    assert result.demotion_reason is None
    assert result.answer_payload["total_score"] == 27.5
    assert result.answer_payload["max_score"] == 36.0
    assert "koota_scores" in result.answer_payload
    assert len(result.answer_payload["koota_scores"]) == 8
    assert isinstance(result.answer_payload["mangal_dosha"]["boy"], bool)
    assert isinstance(result.answer_payload["mangal_dosha"]["girl"], bool)
    assert result.answer_payload["verdict"] in {
        "highly_compatible",
        "compatible",
        "moderately_compatible",
        "incompatible",
    }


# ─── Group D: Refusal cases ─────────────────────────────────────────────


def test_refusal_health(sulabh_chart):
    result = answer_question("What about my health this year?", sulabh_chart)
    _assert_refusal(result)


def test_refusal_travel(sulabh_chart):
    result = answer_question("Will I travel abroad?", sulabh_chart)
    _assert_refusal(result)


def test_refusal_lottery(sulabh_chart):
    result = answer_question("What are my lucky lottery numbers?", sulabh_chart)
    _assert_refusal(result)


def test_refusal_gemstone(sulabh_chart):
    result = answer_question("Recommend a gemstone for me", sulabh_chart)
    _assert_refusal(result)


def test_refusal_marriage_no_partner(sulabh_chart):
    # See deviation #4 above -- this wording (unlike "Are we compatible?")
    # actually clears the domain-confidence floor and gets refused via
    # route_question's has_partner_data guard specifically.
    result = answer_question("Check our marriage compatibility", sulabh_chart)
    _assert_refusal(result)


# ─── Group F: Sade Sati domain (Session 50/P7.2c-e) ────────────────────
#
# sade_sati routes via calc_router._BUILT_MODULE_FASTPATH, a deterministic
# phrase match checked BEFORE domain-keyword scoring -- never through
# _score_domain, never through Stage 2 (test_sade_sati_never_reaches_
# stage2 below guards that). Always TIER_1_EXACT, always
# demotion_reason=None (chart_profile.py's sade_sati payload carries no
# dated dasha claims, so it never inherits current_dasha's ALWAYS-T2 rule
# -- Session 49/P7.0c "tier = payload property" principle).
#
# Hardest case first (CLAUDE.md Working Style #3): the NOT-active branch
# (Sulabh) is structurally more interesting than the active one -- it must
# correctly OMIT current_cycle_start/end while still reporting
# previous_cycle_end + next_cycle_start.


def test_sade_sati_sulabh(sulabh_chart):
    """WALL-CLOCK COUPLING (P7.2e item 6, comment only, no machinery):
    these exact dates hold until Sulabh's own next Sade Sati cycle begins
    (27 Jan 2041, per the P7.2a/golden q14 verified ephemeris scan) -- a
    real astronomical fact, not a maintenance burden before then.
    """
    result = answer_question(_SADE_SATI_QUESTION, sulabh_chart)

    assert result.domain == "sade_sati"
    assert result.tier == AnswerTier.TIER_1_EXACT
    assert result.demotion_reason is None

    payload = result.answer_payload
    assert payload["active"] is False
    assert payload["previous_cycle_end"] == "24 Jan 2020"
    assert payload["next_cycle_start"] == "27 Jan 2041"

    # Payload-property tier lock, asserted structurally: sade_sati earns
    # TIER_1_EXACT BECAUSE this payload carries no dated Mahadasha/
    # Antardasha claims, unlike current_dasha's (always demoted). If a
    # future edit ever merged the two payload shapes, this catches it.
    assert "mahadasha" not in payload
    assert "antardasha" not in payload
    assert "current_cycle_start" not in payload  # only present when active
    assert "current_cycle_end" not in payload


def test_sade_sati_surbhi_active(surbhi_chart):
    """Active-case coverage. Verified (not guessed) which of the 4
    reference charts is currently in an active Sade Sati cycle by a
    direct answer_question() call before writing this test: as of this
    session, Surbhi (SETTING) and Sheridan (RISING) both are; Sulabh and
    David are not. Uses the real, no-mocks answer_question() path (this
    file's own convention) -- the task's historical-evaluated_at_jd
    build_domain_profile() fallback (for when no reference chart is
    currently active) was not needed here.

    WALL-CLOCK COUPLING: Surbhi's current cycle ends 23 Feb 2028 (this
    session's verified value) -- a shorter runway than
    test_sade_sati_sulabh's ~2041. Comment only, no machinery.
    """
    result = answer_question(_SADE_SATI_QUESTION, surbhi_chart)

    assert result.domain == "sade_sati"
    assert result.tier == AnswerTier.TIER_1_EXACT
    assert result.demotion_reason is None

    payload = result.answer_payload
    assert payload["active"] is True
    assert payload["phase"] == "SETTING"
    assert payload["current_cycle_start"] == "24 Jan 2020"
    assert payload["current_cycle_end"] == "23 Feb 2028"
    assert payload["next_cycle_start"] == "20 Oct 2027"
    assert "previous_cycle_end" not in payload  # only present when NOT active
    assert "mahadasha" not in payload
    assert "antardasha" not in payload


def test_sade_sati_never_reaches_stage2(sulabh_chart, monkeypatch):
    """Determinism guard: the sade_sati fast-path must resolve entirely
    within Stage 1, never falling through to Stage 2.

    Patches calc_router._stage2_fallback, NOT _stage2_classify --
    verified this is the correct seam: _stage2_classify's exceptions are
    caught by _stage2_fallback's own fail-closed except-Exception (Stage 2
    always fails CLOSED to REFUSAL), so patching _stage2_classify to raise
    would be silently swallowed into an ordinary REFUSAL and never surface
    as a visible test failure -- the same trap documented in
    tests/conftest.py's Stage 2 stub. _stage2_fallback itself is called
    directly from route_question() with no enclosing try/except, so an
    exception raised here propagates all the way up through
    answer_question() uncaught, which is what actually proves
    non-invocation.
    """
    def _explode(*args, **kwargs):
        raise AssertionError("Stage 2 must not fire for a sade_sati fast-path question")

    monkeypatch.setattr("agent.infra.calc_router._stage2_fallback", _explode)

    result = answer_question(_SADE_SATI_QUESTION, sulabh_chart)
    assert result.domain == "sade_sati"
    assert result.tier == AnswerTier.TIER_1_EXACT


def test_refusal_ashtakavarga_still_unbuilt(sulabh_chart):
    """Regression guard for the fastpath insertion-point ordering (P7.2c):
    _BUILT_MODULE_FASTPATH is checked AFTER _UNBUILT_MODULE_KEYWORDS --
    confirms adding the new sade_sati fast-path didn't accidentally
    reorder or short-circuit the pre-existing unbuilt-module refusal for
    a genuinely unbuilt module.
    """
    result = answer_question("What is my Ashtakavarga strength?", sulabh_chart)
    _assert_refusal(result)
    assert "Ashtakavarga" in result.demotion_reason


# ─── Group E: Error handling ────────────────────────────────────────────


def test_error_partner_without_role(sulabh_chart, surbhi_chart):
    with pytest.raises(ValueError):
        answer_question(
            "Check our marriage compatibility",
            sulabh_chart,
            partner_chart_data=surbhi_chart,
            primary_role=None,
        )


def test_error_empty_question(sulabh_chart):
    result = answer_question("", sulabh_chart)
    # Can't isinstance-check DomainAnswer directly -- only answer_question
    # and AnswerTier are permitted imports here (see module docstring).
    # Duck-type via the DomainAnswer contract fields instead.
    assert result.tier in {
        AnswerTier.TIER_1_EXACT,
        AnswerTier.TIER_2_RANGE,
        AnswerTier.REFUSAL,
    }
    assert hasattr(result, "domain")
    assert hasattr(result, "answer_payload")
    assert hasattr(result, "sources")
