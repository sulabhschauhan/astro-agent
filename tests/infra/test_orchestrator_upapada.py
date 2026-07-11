"""End-to-end + router-provenance tests for upapada_lagna's staged rollout
closing gate (Session 63-70): orchestrator.py's _VALID_DOMAINS now admits
"upapada_lagna", closing chart_profile builder (S63) -> formatter (S64) ->
router Stage 1/Stage 2 (S65) -> orchestrator gate (S66) -> golden harness
mapping (S69) -> golden fixture re-ratification (S70). Mirrors
test_orchestrator_arudha_lagna.py's structure, fixtures, sentinel pattern,
and per-file duplication conventions exactly (read end-to-end before
writing this file).

TWO-SOURCE RATIFICATION for _SULABH_EXPECTED_PAYLOAD (same standard as
tests/fixtures/golden_qa_sulabh.py's own sulabh_arudha_q3_refusal_probe
row, S70): (1) S57 JHora capture -- dual-confirmed render + blind PVR
derivation, full BPHS/PVR Ch.15 Section 15.5.1 co-lord cascade (step-1
Mars/Ketu tie on Scorpio -- Sulabh's house-12 sign is Scorpio, itself
co-lorded -- step-2 Ketu wins via Jupiter's rasi aspect, 7th-from-Scorpio
exception) -> Aquarius, lord Ketu. (2) S63 chart_profile.py smoke test:
upapada_sign="Aquarius", lagna_sign="Sagittarius", lord="Ketu",
co_lord_deciding_step="step_2" -- exact match, pipeline validates the
full cascade path end-to-end, not just the Aquarius endpoint.

MEASURE-FIRST FINDING (reported before any assertion was written, per
CLAUDE.md Working Style #2/#3): _UPAPADA_LAGNA_KEYWORDS
(calc_router.py) has 2 entries -- "upapada", "upapada lagna" -- under
the same `min(matched_keywords, 3) / 3` saturating formula
test_orchestrator_arudha_lagna.py's own docstring documents. Both
candidate phrasings measured directly against route_question() with a
recording sentinel client (records the call, then raises -- see
_RecordingClient below) BEFORE writing any Layer A test:

    "what is my upapada lagna" -> upapada_lagna score 0.667 (both
                                   keyword entries match: "upapada"
                                   token + "upapada lagna" phrase),
                                   sentinel NEVER invoked (Stage 1 alone)
    "what is my upapada"       -> upapada_lagna score 0.333 (only the
                                   bare "upapada" token matches, no
                                   "lagna" following), sentinel INVOKED
                                   (Stage 2 attempted), fails closed to
                                   REFUSAL

Confirms the task prompt's own stated numbers exactly. Also confirmed
by grep (tests/fixtures/golden_qa_sulabh.py, this suite's own file):
neither candidate string collides with any golden-set question
("what does my upapada lagna say about my marriage" is a different,
longer phrasing) or with test_orchestrator_arudha_lagna.py's own
_STAGE1_CLEAN_QUESTION/_STAGE1_MISS_QUESTION constants (those are
arudha, not upapada, phrasings).

Layer C's "recording sentinel" is NOT route_question's `_stage2_client`
kwarg -- same reasoning as test_orchestrator_arudha_lagna.py's own
module docstring: orchestrator.py's answer_question() never accepts or
threads that kwarg through to route_question(). The correct seam for a
full-chain spy is monkeypatching calc_router._stage2_classify directly
(module-level function, called only from _stage2_fallback): if Stage 1
resolves cleanly (this file's whole point), _stage2_classify is never
reached regardless of how it's patched, and the patch call-recording
proves it directly rather than assuming route_question's internal
short-circuit holds through the orchestrator layer too.
"""
from __future__ import annotations

import dataclasses

import pytest
import swisseph as swe

from agent.infra import calc_router
from agent.infra.calc_router import route_question
from agent.infra.chart_profile import AnswerTier, build_domain_profile
from agent.infra.orchestrator import answer_question
from agent.infra.result_formatter import format_answer

# Stage-1-clean phrasing (2 keyword hits: "upapada" token + "upapada lagna"
# phrase), ratified by direct measurement against route_question() -- see
# module docstring above. Scores 0.667, clears both _CONFIDENCE_FLOOR (0.4)
# and _CONFIDENCE_MARGIN (0.15) against every other domain's 0.0.
_STAGE1_CLEAN_QUESTION = "what is my upapada lagna"

# Bare single-keyword phrasing -- scores 0.333, below _CONFIDENCE_FLOOR
# (only "upapada" matches; "upapada lagna" does not, no "lagna" present).
_STAGE1_MISS_QUESTION = "what is my upapada"

_SULABH_EXPECTED_PAYLOAD = {
    "upapada_sign": "Aquarius",
    "lagna_sign": "Sagittarius",
    "lord": "Ketu",
    "co_lord_deciding_step": "step_2",
}

_CANONICAL_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

# Classical (single) sign lords -- Scorpio/Aquarius deliberately excluded
# (co-lorded, routed through stronger_co_lord). Independently duplicated
# here rather than imported, per this project's per-module duplication
# convention (see test_chart_profile_arudha_lagna.py's own
# _CLASSICAL_SIGN_LORDS precedent, which this dict is copied from).
_CLASSICAL_SIGN_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn",
    "Pisces": "Jupiter",
}


def _house_12_sign(lagna_sign: str) -> str:
    """Whole-sign house 12 = the sign immediately before lagna_sign in
    zodiacal order (12th from lagna, inclusive counting -> index - 1).

    NOTE: this is the SIGN OCCUPYING house 12, NOT the same thing as
    upapada_sign (the Arudha PADA computed FROM house 12 via the
    co-lord-cascade counting procedure) -- confirmed empirically before
    writing Layer B's shape assertions: for Sulabh, house_12_sign("Sagi
    ttarius") == "Scorpio", while upapada_sign == "Aquarius" -- these
    are two different signs. The "lord" payload field is the (possibly
    co-lord-cascade-resolved) lord of THIS house-12 sign, used as an
    input to the Arudha-pada counting procedure -- not the lord of the
    resulting upapada_sign. This is exactly why Sulabh's house-12 sign
    (Scorpio, co-lorded Mars/Ketu) triggers co_lord_deciding_step
    ("step_2") even though the resulting upapada_sign (Aquarius) is
    itself also a co-lorded sign in its own right -- the cascade fires
    on the INPUT sign, not the output.
    """
    idx = _CANONICAL_SIGNS.index(lagna_sign)
    return _CANONICAL_SIGNS[(idx - 1) % 12]


# ─── Fixtures (mirrors test_orchestrator_arudha_lagna.py's own style) ──────


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
# Mirrors test_orchestrator_arudha_lagna.py's own _RecordingCompletions/
# _RecordingClient pattern (records every call in `.calls`, raises a canned
# exception) -- duplicated rather than imported, per this project's
# per-test-file self-containment convention.


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
        assert result.domain == "upapada_lagna"
        assert result.tier == AnswerTier.TIER_1_EXACT
        assert result.demotion_reason is None
        assert result.requires_partner is False

    def test_a2_single_keyword_phrasing_attempts_stage2_and_refuses(self):
        """PINS CURRENT BEHAVIOR, NOT desired behavior: "what is my
        upapada" scores 0.333 (a single keyword hit under the
        min(matched,3)/3 formula -- only "upapada" matches, "upapada
        lagna" does not), below _CONFIDENCE_FLOOR, so Stage 1 alone
        REFUSEs and Stage 2 is attempted. The sentinel raises
        RuntimeError inside _stage2_classify's
        client.chat.completions.create() call; _stage2_fallback's own
        except-Exception fails this closed to a generic REFUSAL (never
        propagates, never guesses a domain) -- this swallowing is part
        of what this test pins, not a re-derivation.
        """
        client = _RecordingClient()
        result = route_question(_STAGE1_MISS_QUESTION, _stage2_client=client)

        assert len(client.completions.calls) == 1  # sentinel WAS invoked
        assert result.domain is None
        assert result.tier == AnswerTier.REFUSAL


# ─── Layer B: e2e oracle (router bypassed, no LLM) ──────────────────────────


def _evaluated_at_jd() -> float:
    # upapada_lagna is a purely natal calculation -- build_domain_profile's
    # own docstring documents evaluated_at_jd as "accepted uniformly but
    # genuinely unused" for this domain (same precedent as arudha_lagna/
    # av_transit). Any JD value is safe here; a fixed placeholder avoids a
    # spurious datetime.now() dependency in what is otherwise a
    # deterministic test.
    return swe.julday(2000, 1, 1, 0.0)


class TestLayerBRealChartOracle:
    def test_sulabh_full_assert(self, sulabh_chart):
        """Sulabh is the only chart with a FULLY ratified expected
        payload (see module docstring's two-source ratification), so it
        is the one row that gets a complete assertion, including the
        answer_payload exact-key-set check (pins no tier/sources
        meta-key leakage past chart_profile.py's documented PAYLOAD
        PASSTHROUGH into the formatter's own 4-key dict).
        """
        profile = build_domain_profile("upapada_lagna", sulabh_chart, _evaluated_at_jd())
        answer = format_answer(profile)

        assert answer.domain == "upapada_lagna"
        assert answer.tier == AnswerTier.TIER_1_EXACT
        assert answer.answer_payload == _SULABH_EXPECTED_PAYLOAD
        assert set(answer.answer_payload.keys()) == {
            "upapada_sign", "lagna_sign", "lord", "co_lord_deciding_step",
        }
        assert answer.demotion_reason is None
        assert answer.uncertainty_days == 0.0
        assert answer.sources == ("padas.py",)

    def _assert_shape_and_ratified(
        self,
        chart: dict,
        expected_upapada_sign: str,
        expected_lord: str,
        expected_step: str | None,
    ):
        """Shared shape assertion + RATIFIED literal assertion for the 3
        non-Sulabh charts. Derives house_12_sign from lagna_sign (NOT
        upapada_sign -- see _house_12_sign's own docstring for why these
        differ) and keeps the general co-lorded/non-co-lorded shape
        invariant as a sanity check alongside the exact ratified values
        (S72): none of David/Sheridan/Surbhi land on a co-lorded
        (Scorpio/Aquarius) house-12 sign -- only Sulabh does in this
        4-chart set, so this branch is expected to always take the
        `not in` path here.

        RATIFIED S72 (design-chat sign-off) -- plain-path output of the
        dual-oracle-validated padas kernel: PVR Example 29 (12-house
        book oracle, jaimini/padas.py's own CITATION) + Sulabh's S57
        JHora cascade capture (dual-confirmed render + blind PVR
        derivation) validate the underlying kernel these 3 rows also run
        through; each row's lord additionally cross-checked against
        design-chat whole-sign derivation for its own house-12 sign.
        Promotion mirrors test_orchestrator_arudha_lagna.py's own S59
        promotion diff exactly (commit b4be25a): print-only RATIFY lines
        removed now that real assertions exist; the shape-helper
        function (_house_12_sign) is KEPT (still exercised by the shape
        invariant above), unlike arudha's S59 promotion which removed
        its OWN now-unused `_print_ratify_line` helper -- the two
        helpers differ (this one still does real work post-promotion,
        that one didn't).
        """
        profile = build_domain_profile("upapada_lagna", chart, _evaluated_at_jd())
        answer = format_answer(profile)
        payload = answer.answer_payload

        assert payload["lagna_sign"] in _CANONICAL_SIGNS
        house_12_sign = _house_12_sign(payload["lagna_sign"])
        assert house_12_sign not in ("Scorpio", "Aquarius")

        assert payload["upapada_sign"] == expected_upapada_sign
        assert payload["lord"] == expected_lord
        assert payload["co_lord_deciding_step"] is expected_step

    def test_david_shape_and_ratified(self, david_chart):
        """David tested first among the 3 partial-assert rows per
        CLAUDE.md Working Style #3 (HARDEST CASE first), mirroring
        test_orchestrator_arudha_lagna.py's own ordering precedent
        (Session 57 cross-chart divergence, documented elsewhere in
        CLAUDE.md for this chart specifically).
        """
        self._assert_shape_and_ratified(david_chart, "Gemini", "Sun", None)

    def test_sheridan_shape_and_ratified(self, sheridan_chart):
        self._assert_shape_and_ratified(sheridan_chart, "Capricorn", "Mars", None)

    def test_surbhi_shape_and_ratified(self, surbhi_chart):
        self._assert_shape_and_ratified(surbhi_chart, "Cancer", "Mercury", None)


# ─── Layer C: full chain (router included, no LLM reached) ─────────────────


class TestLayerCFullChain:
    def test_sulabh_full_chain_matches_layer_b(self, sulabh_chart, monkeypatch):
        """Pins _merge_router_demotion's no-op passthrough for this
        domain end to end: route_question's own demotion_reason is None
        (Stage 1 resolves cleanly on _STAGE1_CLEAN_QUESTION), so
        orchestrator._merge_router_demotion returns the formatter's
        DomainAnswer completely unchanged -- this row must be
        byte-for-byte identical to Layer B's Sulabh row above.

        Recording sentinel: monkeypatches calc_router._stage2_classify
        itself (see module docstring for why this, not route_question's
        _stage2_client kwarg, is the correct seam for a full-chain spy).
        """
        calls: list[str] = []

        def _spy_stage2_classify(question, client=None):
            calls.append(question)
            raise AssertionError(
                "stage2 must not fire for a Stage-1-clean upapada_lagna phrasing"
            )

        monkeypatch.setattr(calc_router, "_stage2_classify", _spy_stage2_classify)

        result = answer_question(_STAGE1_CLEAN_QUESTION, sulabh_chart)

        assert calls == []  # sentinel NEVER invoked

        profile = build_domain_profile("upapada_lagna", sulabh_chart, _evaluated_at_jd())
        # route stamped by answer_question() (orchestrator-only concern);
        # Layer B's direct format_answer() output is legitimately un-stamped.
        expected = dataclasses.replace(format_answer(profile), route="stage1")

        assert result == expected
        assert result.domain == "upapada_lagna"
        assert result.tier == AnswerTier.TIER_1_EXACT
        assert result.answer_payload == _SULABH_EXPECTED_PAYLOAD
        assert result.demotion_reason is None
        assert result.uncertainty_days == 0.0
        assert result.sources == ("padas.py",)
