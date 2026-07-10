"""End-to-end + router-provenance tests for arudha_lagna's staged rollout
closing gate (Session 59): orchestrator.py's _VALID_DOMAINS now admits
"arudha_lagna", closing router (S58) -> formatter (S59) -> chart_profile
dispatch (S59) -> orchestrator gate (S59).

MEASURE-FIRST FINDING (reported before any assertion was written, per
CLAUDE.md Working Style #2/#3): calc_router._score_domain's formula is
`min(matched_keywords, 3) / 3` (a fixed [0, 1] saturating scale, NOT
matched/len(keywords)) -- confirmed by reading the function directly, not
assumed from the 0.333 figure in diagnostics/calc_router_stage2.log.
arudha_lagna's keyword list (_ARUDHA_LAGNA_KEYWORDS) has 4 entries:
"arudha lagna", "arudha pada", "public image", "public perception". A
single-keyword hit therefore always scores 1/3 = 0.333, below
_CONFIDENCE_FLOOR (0.4) regardless of list length -- "what is my arudha
lagna" cannot clear Stage 1 alone (CLAUDE.md carry-forward, logged
2026-07-10). A 2-keyword hit scores 2/3 = 0.667, comfortably clearing both
floor and margin. Candidate phrasings measured directly against
route_question() with a recording sentinel client (records the call, then
raises -- see _RecordingClient below) BEFORE writing any Layer A test:

    "what is my arudha lagna and public image"   -> score 0.667, sentinel
                                                     NEVER invoked (Stage 1 alone)
    "arudha lagna public image"                  -> score 0.667, sentinel
                                                     NEVER invoked
    "what is my arudha pada and public perception" -> score 0.667, sentinel
                                                     NEVER invoked
    "what is my arudha lagna"                    -> score 0.333, sentinel
                                                     INVOKED (Stage 2 attempted),
                                                     fails closed to REFUSAL
    "how do people see me in public"             -> score 0.0, sentinel
                                                     INVOKED, fails closed to REFUSAL

_STAGE1_CLEAN_QUESTION below ("what is my arudha lagna and public image")
is the phrasing this file uses for every Stage-1-only assertion. It was
chosen (not "arudha lagna public image") because it reads as an actual
question, matching this repo's existing phrasing convention
(test_orchestrator_e2e.py's _CAREER_QUESTION/_DASHA_QUESTION are both full
questions, not keyword fragments).

Layer C's "recording sentinel" is NOT route_question's `_stage2_client`
kwarg -- confirmed by reading agent/infra/orchestrator.py's
answer_question() signature, which never accepts or threads that kwarg
through to route_question(). The correct seam for a full-chain spy is
monkeypatching calc_router._stage2_classify directly (module-level
function, called only from _stage2_fallback): if Stage 1 resolves cleanly
(this file's whole point), _stage2_classify is never reached regardless of
how it's patched, and the patch call-recording proves it directly rather
than assuming route_question's internal short-circuit holds through the
orchestrator layer too.
"""
from __future__ import annotations

import pytest
import swisseph as swe

from agent.infra import calc_router
from agent.infra.calc_router import route_question
from agent.infra.chart_profile import AnswerTier, build_domain_profile
from agent.infra.orchestrator import answer_question
from agent.infra.result_formatter import format_answer

# Stage-1-clean phrasing (2 keyword hits: "arudha lagna" + "public image"),
# ratified by direct measurement against route_question() -- see module
# docstring above. Scores 0.667, clears both _CONFIDENCE_FLOOR (0.4) and
# _CONFIDENCE_MARGIN (0.15) against every other domain's 0.0.
_STAGE1_CLEAN_QUESTION = "what is my arudha lagna and public image"

# Single-keyword phrasing -- scores 0.333, below _CONFIDENCE_FLOOR. Pins
# the CURRENT (not desired) Stage-1-unreachable-for-single-mention finding.
_STAGE1_MISS_QUESTION = "what is my arudha lagna"

_SULABH_EXPECTED_PAYLOAD = {
    "arudha_sign": "Leo",
    "lagna_sign": "Sagittarius",
    "lord": "Jupiter",
    "co_lord_deciding_step": None,
}

_CANONICAL_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


# ─── Fixtures (mirrors test_orchestrator_e2e.py's own style) ───────────────


@pytest.fixture(scope="module")
def sulabh_chart():
    from agent.chart_calculator import calculate_chart
    return calculate_chart("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")


@pytest.fixture(scope="module")
def surbhi_chart():
    from agent.chart_calculator import calculate_chart
    return calculate_chart("Surbhi", "11 Sep 1992", "10:30", "Patna, India")


@pytest.fixture(scope="module")
def sheridan_chart():
    from agent.chart_calculator import calculate_chart
    return calculate_chart("Sheridan", "27 May 1984", "08:00", "Durban, South Africa")


@pytest.fixture(scope="module")
def david_chart():
    from agent.chart_calculator import calculate_chart
    return calculate_chart("David", "19 Jan 1976", "22:00", "London, UK")


# ─── Recording sentinel (Layer A) ───────────────────────────────────────────
# Mirrors tests/infra/test_calc_router_stage2.py's _FakeCompletions/_FakeClient
# pattern (records every call in `.calls`, raises a canned exception) --
# duplicated rather than imported, per this project's per-test-file
# self-containment convention (see test_chart_profile_arudha_lagna.py's own
# _CLASSICAL_SIGN_LORDS duplication-not-import precedent).


class _RecordingCompletions:
    def __init__(self):
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        raise RuntimeError("sentinel: stage2 should not have been reached")


class _RecordingClient:
    """Records every `.chat.completions.create()` call, then raises --
    proves non-invocation via `.completions.calls == []` directly (not by
    inferring it from the absence of a crash)."""

    def __init__(self):
        self.completions = _RecordingCompletions()
        self.chat = type("_FakeChat", (), {"completions": self.completions})()


# ─── Layer A: router provenance ─────────────────────────────────────────────


class TestLayerARouterProvenance:
    def test_a1_stage1_clean_phrasing_never_touches_stage2(self):
        client = _RecordingClient()
        result = route_question(_STAGE1_CLEAN_QUESTION, _stage2_client=client)

        assert client.completions.calls == []  # sentinel NEVER invoked
        assert result.domain == "arudha_lagna"
        assert result.tier == AnswerTier.TIER_1_EXACT
        assert result.demotion_reason is None
        assert result.requires_partner is False

    def test_a2_single_keyword_phrasing_attempts_stage2_and_refuses(self):
        """PINS CURRENT BEHAVIOR (CLAUDE.md carry-forward, 2026-07-10),
        NOT desired behavior: "what is my arudha lagna" scores 0.333 (a
        single keyword hit under the min(matched,3)/3 formula), below
        _CONFIDENCE_FLOOR, so Stage 1 alone REFUSEs and Stage 2 is
        attempted. The sentinel raises RuntimeError inside
        _stage2_classify's client.chat.completions.create() call;
        _stage2_fallback's own except-Exception fails this closed to a
        generic REFUSAL (never propagates, never guesses a domain) -- this
        swallowing is part of what this test pins, not a re-derivation.
        A future scorecard-gated tuning (_BUILT_MODULE_FASTPATH entry or a
        multi-word exact-name floor exemption) should flip this test
        deliberately, not by accident.
        """
        client = _RecordingClient()
        result = route_question(_STAGE1_MISS_QUESTION, _stage2_client=client)

        assert len(client.completions.calls) == 1  # sentinel WAS invoked
        assert result.domain is None
        assert result.tier == AnswerTier.REFUSAL


# ─── Layer B: e2e oracle (router bypassed, no LLM) ──────────────────────────


def _evaluated_at_jd() -> float:
    # arudha_lagna is a purely natal calculation -- build_domain_profile's
    # own docstring documents evaluated_at_jd as "accepted uniformly but
    # genuinely unused" for this domain (same precedent as av_transit).
    # Any JD value is safe here; a fixed placeholder avoids a spurious
    # datetime.now() dependency in what is otherwise a deterministic test.
    return swe.julday(2000, 1, 1, 0.0)


class TestLayerBRealChartOracle:
    def test_sulabh_full_assert(self, sulabh_chart):
        """Hardest-case-first note: David (below) is the actual hardest
        case per this task's own instruction ordering, but Sulabh is the
        only chart with a FULLY ratified expected payload (see
        test_chart_profile_arudha_lagna.py's own test_sulabh_al_is_leo_
        ratified), so it is the one row that gets a complete assertion,
        including the answer_payload exact-key-set check (pins no tier/
        sources meta-key leakage past chart_profile.py's documented
        PAYLOAD PASSTHROUGH into the formatter's own 4-key dict).
        """
        profile = build_domain_profile("arudha_lagna", sulabh_chart, _evaluated_at_jd())
        answer = format_answer(profile)

        assert answer.domain == "arudha_lagna"
        assert answer.tier == AnswerTier.TIER_1_EXACT
        assert answer.answer_payload == _SULABH_EXPECTED_PAYLOAD
        assert set(answer.answer_payload.keys()) == {
            "arudha_sign", "lagna_sign", "lord", "co_lord_deciding_step",
        }
        assert answer.demotion_reason is None
        assert answer.uncertainty_days == 0.0
        assert answer.sources == ("padas.py",)

    def test_david_arudha_sign_ratified(self, david_chart):
        """David is genuinely the hardest of the 4 reference charts for
        this domain (Session 57 cross-chart divergence precedent recorded
        elsewhere in CLAUDE.md), tested first among the 3 partial-assert
        rows per CLAUDE.md Working Style #3. arudha_sign="Taurus" verified
        directly against build_arudha_lagna_profile(david_chart) before
        writing this assertion (measured, not copied from the task prompt
        unverified) -- lord/co_lord_deciding_step now RATIFIED (see inline
        comment below).
        """
        profile = build_domain_profile("arudha_lagna", david_chart, _evaluated_at_jd())
        answer = format_answer(profile)

        assert answer.answer_payload["lagna_sign"] in _CANONICAL_SIGNS
        assert answer.answer_payload["arudha_sign"] == "Taurus"
        # RATIFIED S59 (design-chat sign-off, 2026-07-10) -- derived live,
        # cross-checked against S57 PVR counting ratification.
        assert answer.answer_payload["lord"] == "Mercury"
        assert answer.answer_payload["co_lord_deciding_step"] is None

    def test_sheridan_arudha_sign_ratified(self, sheridan_chart):
        profile = build_domain_profile("arudha_lagna", sheridan_chart, _evaluated_at_jd())
        answer = format_answer(profile)

        assert answer.answer_payload["lagna_sign"] in _CANONICAL_SIGNS
        assert answer.answer_payload["arudha_sign"] == "Aquarius"
        # RATIFIED S59 (design-chat sign-off, 2026-07-10) -- derived live,
        # cross-checked against S57 PVR counting ratification.
        assert answer.answer_payload["lord"] == "Venus"
        assert answer.answer_payload["co_lord_deciding_step"] is None

    def test_surbhi_arudha_sign_ratified(self, surbhi_chart):
        profile = build_domain_profile("arudha_lagna", surbhi_chart, _evaluated_at_jd())
        answer = format_answer(profile)

        assert answer.answer_payload["lagna_sign"] in _CANONICAL_SIGNS
        assert answer.answer_payload["arudha_sign"] == "Leo"
        # RATIFIED S59 (design-chat sign-off, 2026-07-10) -- derived live,
        # cross-checked against S57 PVR counting ratification.
        assert answer.answer_payload["lord"] == "Venus"
        assert answer.answer_payload["co_lord_deciding_step"] is None


# ─── Layer C: full chain (router included, no LLM reached) ─────────────────


class TestLayerCFullChain:
    def test_sulabh_full_chain_matches_layer_b(self, sulabh_chart, monkeypatch):
        """Pins _merge_router_demotion's no-op passthrough for this domain
        end to end: route_question's own demotion_reason is None (Stage 1
        resolves cleanly on _STAGE1_CLEAN_QUESTION), so
        orchestrator._merge_router_demotion returns the formatter's
        DomainAnswer completely unchanged -- this row must be byte-for-byte
        identical to Layer B's Sulabh row above.

        Recording sentinel: monkeypatches calc_router._stage2_classify
        itself (see module docstring for why this, not route_question's
        _stage2_client kwarg, is the correct seam for a full-chain spy).
        """
        calls: list[str] = []

        def _spy_stage2_classify(question, client=None):
            calls.append(question)
            raise AssertionError(
                "stage2 must not fire for a Stage-1-clean arudha_lagna phrasing"
            )

        monkeypatch.setattr(calc_router, "_stage2_classify", _spy_stage2_classify)

        result = answer_question(_STAGE1_CLEAN_QUESTION, sulabh_chart)

        assert calls == []  # sentinel NEVER invoked

        profile = build_domain_profile("arudha_lagna", sulabh_chart, _evaluated_at_jd())
        expected = format_answer(profile)

        assert result == expected
        assert result.domain == "arudha_lagna"
        assert result.tier == AnswerTier.TIER_1_EXACT
        assert result.answer_payload == _SULABH_EXPECTED_PAYLOAD
        assert result.demotion_reason is None
        assert result.uncertainty_days == 0.0
        assert result.sources == ("padas.py",)
