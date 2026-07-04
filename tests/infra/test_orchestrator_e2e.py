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
3. test_career_surbhi asserts uncertainty_virupa == 59.0, not 6.0 --
   chart_profile.py has a documented Surbhi-specific override (Kala Bala
   Sun/Jupiter/Saturn Abda/Masa cross-chart divergence, see CLAUDE.md
   "Shadbala Kala Bala" section) that is NOT the general Ayana Bala
   Moon/Venus envelope constant used for the other 3 charts (see CLAUDE.md
   "Known Source Divergences (V1)" -> Ayana Bala).
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
chart_profile.DomainAnswer, or result_formatter imports.
"""

import pytest

from agent.infra.chart_profile import AnswerTier
from agent.infra.orchestrator import answer_question

_VALID_PLANETS = {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"}

# See deviation #1 above -- must score >=2 career keyword hits to clear
# calc_router.py's 0.4 confidence floor.
_CAREER_QUESTION = "How is my career and job strength?"
_DASHA_QUESTION = "What dasha period am I in right now?"


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
    result = answer_question(_CAREER_QUESTION, david_chart)
    _assert_career_answer(result, expected_uncertainty_virupa=6.0)


def test_career_sheridan(sheridan_chart):
    result = answer_question(_CAREER_QUESTION, sheridan_chart)
    _assert_career_answer(result, expected_uncertainty_virupa=6.0)


def test_career_surbhi(surbhi_chart):
    # See deviation #3 above -- Surbhi carries a documented 59.0 Virupa
    # override, not the general 6.0 Ayana Bala Moon/Venus envelope constant.
    result = answer_question(_CAREER_QUESTION, surbhi_chart)
    _assert_career_answer(result, expected_uncertainty_virupa=59.0)


def test_career_sulabh(sulabh_chart):
    result = answer_question(_CAREER_QUESTION, sulabh_chart)
    _assert_career_answer(result, expected_uncertainty_virupa=6.0)


# ─── Group B: Dasha domain (David first -- hardest case) ───────────────────


def _assert_dasha_answer_shape(result) -> None:
    assert result.domain == "current_dasha"
    assert result.tier in {AnswerTier.TIER_1_EXACT, AnswerTier.TIER_2_RANGE}
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
    # Diagnostic -- verify dasha demotion is conditional on near_boundary,
    # not unconditional. If ALL four charts show TIER_2_RANGE, investigate
    # _near_dasha_boundary logic.
    print(f"[dasha diagnostic] David: tier={result.tier}, demotion_reason={result.demotion_reason!r}")


def test_dasha_sheridan(sheridan_chart):
    result = answer_question(_DASHA_QUESTION, sheridan_chart)
    _assert_dasha_answer_shape(result)
    # Diagnostic -- verify dasha demotion is conditional on near_boundary,
    # not unconditional. If ALL four charts show TIER_2_RANGE, investigate
    # _near_dasha_boundary logic.
    print(f"[dasha diagnostic] Sheridan: tier={result.tier}, demotion_reason={result.demotion_reason!r}")


def test_dasha_surbhi(surbhi_chart):
    result = answer_question(_DASHA_QUESTION, surbhi_chart)
    _assert_dasha_answer_shape(result)
    # Diagnostic -- verify dasha demotion is conditional on near_boundary,
    # not unconditional. If ALL four charts show TIER_2_RANGE, investigate
    # _near_dasha_boundary logic.
    print(f"[dasha diagnostic] Surbhi: tier={result.tier}, demotion_reason={result.demotion_reason!r}")


def test_dasha_sulabh(sulabh_chart):
    result = answer_question(_DASHA_QUESTION, sulabh_chart)
    _assert_dasha_answer_shape(result)
    assert result.answer_payload["mahadasha"]["lord"].lower() == "ketu"
    # Diagnostic -- verify dasha demotion is conditional on near_boundary,
    # not unconditional. If ALL four charts show TIER_2_RANGE, investigate
    # _near_dasha_boundary logic.
    print(f"[dasha diagnostic] Sulabh: tier={result.tier}, demotion_reason={result.demotion_reason!r}")


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
