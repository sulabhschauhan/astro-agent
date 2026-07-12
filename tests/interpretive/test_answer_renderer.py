"""
tests/interpretive/test_answer_renderer.py

Ring 1/2 test file for agent/interpretive/answer_renderer.py -- fully
deterministic renderer, so every test here uses hand-built DomainAnswer
stubs (no live pipeline, no LLM, no ChromaDB). Payload shapes are copied
verbatim from agent/infra/result_formatter.py's actual _format_*() branch
code (read directly, not guessed) -- see each stub's own comment for its
source function.

Hardest cases first (CLAUDE.md Working Style #3): the fail-closed/fail-
loud battery (REFUSAL passthrough, unknown-domain ValueError, missing-key
KeyError) comes before the 7 per-domain happy-path tests.
"""
from __future__ import annotations

import re

import pytest

from agent.infra.chart_profile import AnswerTier, DomainAnswer
from agent.interpretive import palm_reading
from agent.interpretive.answer_renderer import render_answer

# ─── Jargon-gloss compliance helper ────────────────────────────────────
#
# Reuses palm_reading._JARGON_BLACKLIST directly (not duplicated) -- same
# blacklist, single source of truth, per the task's "no jargon from
# palm_reading.py's blacklist" instruction. Rule 5 explicitly permits
# domain-inherent terms as TOPIC NAMES (its own examples: "Sade Sati",
# "Arudha Lagna" are fine) provided they are glossed inline, not used as
# unexplained qualifiers -- so this check is NOT "the term must never
# appear," it is "every occurrence must either be immediately glossed
# (followed by an explanatory parenthetical) or have been glossed
# earlier in the same text" (natural language legitimately refers back
# to an already-explained term without re-explaining it every time --
# see e.g. answer_renderer._render_current_dasha()'s second, backward-
# referencing use of "Mahadasha" inside its Antardasha explanation).

_JARGON_TERM_RE = re.compile(
    r"\b(" + "|".join(re.escape(t) for t in palm_reading._JARGON_BLACKLIST) + r")\b",
    re.IGNORECASE,
)


def _assert_no_unglossed_jargon(text: str) -> None:
    glossed_terms: set[str] = set()
    for match in _JARGON_TERM_RE.finditer(text):
        term = match.group(0).lower()
        tail = text[match.end():match.end() + 5]
        glossed_here = bool(re.match(r"\s*\(", tail))
        if glossed_here:
            glossed_terms.add(term)
        else:
            assert term in glossed_terms, (
                f"unglossed jargon term {match.group(0)!r} found with no "
                f"prior gloss earlier in this text: {text!r}"
            )


# ─── Fail-closed / fail-loud battery (hardest case first) ──────────────


def test_refusal_returns_user_message_verbatim_no_demotion_append():
    """Rule 2 + design note: REFUSAL short-circuits render_answer() --
    domain dispatch is skipped entirely (domain is None here, mirroring
    result_formatter.format_refusal()'s route_result.domain passthrough),
    and demotion_reason is NOT separately appended, since it already
    determined which user_message was chosen upstream."""
    user_message = (
        "I couldn't confidently tell what you're asking. Could you try "
        "rephrasing?"
    )
    answer = DomainAnswer(
        domain=None,
        tier=AnswerTier.REFUSAL,
        answer_payload={"user_message": user_message},
        stub_caveats=(),
        uncertainty_virupa=0.0,
        demotion_reason="question not classifiable with confidence",
        sources=(),
        uncertainty_days=0.0,
    )
    result = render_answer(answer)
    assert result == user_message
    assert "Accuracy note" not in result


def test_unknown_domain_raises_value_error():
    answer = DomainAnswer(
        domain="not_a_real_domain",
        tier=AnswerTier.TIER_1_EXACT,
        answer_payload={},
        stub_caveats=(),
        uncertainty_virupa=0.0,
        demotion_reason=None,
        sources=(),
        uncertainty_days=0.0,
    )
    with pytest.raises(ValueError, match="not_a_real_domain"):
        render_answer(answer)


def test_missing_payload_key_raises_keyerror_fail_loud():
    """Rule 6: renderer never invents defaults for a missing expected key
    -- direct dict indexing must raise KeyError, not silently degrade."""
    answer = DomainAnswer(
        domain="marriage_compatibility",
        tier=AnswerTier.TIER_1_EXACT,
        answer_payload={"total_score": 28.0, "max_score": 36.0},  # missing koota_scores/mangal_dosha/verdict
        stub_caveats=(),
        uncertainty_virupa=0.0,
        demotion_reason=None,
        sources=(),
        uncertainty_days=0.0,
    )
    with pytest.raises(KeyError):
        render_answer(answer)


def test_demotion_reason_appended_as_accuracy_note_verbatim():
    """Rule 3: demotion_reason, when present, is appended as a plain-
    language 'Accuracy note:' paragraph -- verbatim, never dropped."""
    demotion_text = (
        "Antardasha boundaries carry ±37-day drift vs AstroSage; current "
        "lord is reliable except near period boundaries"
    )
    answer = DomainAnswer(
        domain="current_dasha",
        tier=AnswerTier.TIER_2_RANGE,
        answer_payload={
            "mahadasha": {"lord": "jupiter", "start": "12 Jan 2020", "end": "12 Jan 2036"},
            "antardasha": {"lord": "saturn", "start": "5 Mar 2024", "end": "18 Aug 2026"},
            "near_boundary": True,
            "boundary_note": "some boundary note text",
        },
        stub_caveats=(),
        uncertainty_virupa=0.0,
        demotion_reason=demotion_text,
        sources=("vimshottari_dasha",),
        uncertainty_days=0.0,
    )
    result = render_answer(answer)
    assert result.endswith("\n\nAccuracy note: " + demotion_text)


# ─── Per-domain happy paths (payload shapes from result_formatter.py) ──

# Each stub is built and rendered once here, and reused by the muhurta-
# relabeling and jargon-compliance checks below.

_CURRENT_DASHA_ANSWER = DomainAnswer(
    domain="current_dasha",
    tier=AnswerTier.TIER_1_EXACT,
    answer_payload={
        "mahadasha": {"lord": "jupiter", "start": "12 Jan 2020", "end": "12 Jan 2036"},
        "antardasha": {"lord": "saturn", "start": "5 Mar 2024", "end": "18 Aug 2026"},
        "near_boundary": False,
        "boundary_note": None,
    },
    stub_caveats=(),
    uncertainty_virupa=0.0,
    demotion_reason=None,
    sources=("vimshottari_dasha",),
    uncertainty_days=0.0,
)

_SADE_SATI_ANSWER = DomainAnswer(
    domain="sade_sati",
    tier=AnswerTier.TIER_1_EXACT,
    answer_payload={
        "active": True,
        "phase": "PEAK",
        "next_cycle_start": "3 Jun 2054",
        "current_cycle_start": "10 Apr 2022",
        "current_cycle_end": "22 Jun 2027",
    },
    stub_caveats=(),
    uncertainty_virupa=0.0,
    demotion_reason=None,
    sources=("sade_sati",),
    uncertainty_days=0.0,
)

_CAREER_ANSWER = DomainAnswer(
    domain="career_strength",
    tier=AnswerTier.TIER_2_RANGE,
    answer_payload={
        "career_significators": {
            "tenth_lord": {"planet": "saturn", "rupa": 380.5, "ratio": 1.35, "rank": 2, "label": "strong", "above_min": True},
            "sun": {"planet": "sun", "rupa": 310.2, "ratio": 1.05, "rank": 4, "label": "adequate", "above_min": True},
            "saturn": {"planet": "saturn", "rupa": 380.5, "ratio": 1.35, "rank": 2, "label": "strong", "above_min": True},
        },
        "strongest_planet": "jupiter",
        "weakest_planet": "mercury",
        "bhava_10_rupa": 245.7,
    },
    stub_caveats=(),
    uncertainty_virupa=0.0,
    demotion_reason=None,
    sources=("shadbala", "bhava_bala"),
    uncertainty_days=0.0,
)

_MARRIAGE_ANSWER = DomainAnswer(
    domain="marriage_compatibility",
    tier=AnswerTier.TIER_1_EXACT,
    answer_payload={
        "total_score": 28.5,
        "max_score": 36.0,
        "koota_scores": {
            "varna": {"score": 1.0, "max": 1.0},
            "vashya": {"score": 2.0, "max": 2.0},
            "tara": {"score": 3.0, "max": 3.0},
            "yoni": {"score": 3.0, "max": 4.0},
            "graha_maitri": {"score": 4.0, "max": 5.0},
            "gana": {"score": 5.0, "max": 6.0},
            "bhakoota": {"score": 6.0, "max": 7.0},
            "nadi": {"score": 4.5, "max": 8.0},
        },
        "mangal_dosha": {"boy": True, "girl": False, "both_have": False},
        "verdict": "highly_compatible",
    },
    stub_caveats=(),
    uncertainty_virupa=0.0,
    demotion_reason=None,
    sources=("ashtakoot", "mangal_dosha"),
    uncertainty_days=0.0,
)

_ARUDHA_LAGNA_ANSWER = DomainAnswer(
    domain="arudha_lagna",
    tier=AnswerTier.TIER_1_EXACT,
    answer_payload={
        "arudha_sign": "Leo",
        "lagna_sign": "Sagittarius",
        "lord": "sun",
        "co_lord_deciding_step": "step_2",
    },
    stub_caveats=(),
    uncertainty_virupa=0.0,
    demotion_reason=None,
    sources=("padas.py",),
    uncertainty_days=0.0,
)

_UPAPADA_LAGNA_ANSWER = DomainAnswer(
    domain="upapada_lagna",
    tier=AnswerTier.TIER_1_EXACT,
    answer_payload={
        "upapada_sign": "Aquarius",
        "lagna_sign": "Sagittarius",
        "lord": "ketu",
        "co_lord_deciding_step": "step_2",
    },
    stub_caveats=(),
    uncertainty_virupa=0.0,
    demotion_reason=None,
    sources=("padas.py",),
    uncertainty_days=0.0,
)

_MUHURTA_WINDOW_ANSWER = DomainAnswer(
    domain="muhurta_window",
    tier=AnswerTier.TIER_3_MUHURTA,
    answer_payload={
        "windows": [
            {"start": "1 Aug 2026 09:00 UTC", "end": "1 Aug 2026 11:30 UTC", "tier": "TIER_1", "favorable_count": 3, "warnings": ()},
            {"start": "1 Aug 2026 11:30 UTC", "end": "1 Aug 2026 14:00 UTC", "tier": "TIER_2", "favorable_count": 2, "warnings": ("Janma Tara",)},
            {"start": "1 Aug 2026 14:00 UTC", "end": "1 Aug 2026 16:00 UTC", "tier": "TIER_3", "favorable_count": 1, "warnings": ("Janma Tara", "Panchaka")},
        ],
        "summary": {"tier1_window_count": 1, "earliest_tier1_start": "1 Aug 2026 09:00 UTC"},
    },
    stub_caveats=(),
    uncertainty_virupa=0.0,
    demotion_reason=None,
    sources=("muhurta_scorer.py",),
    uncertainty_days=0.0,
)

_ALL_HAPPY_PATH_ANSWERS = [
    _CURRENT_DASHA_ANSWER,
    _SADE_SATI_ANSWER,
    _CAREER_ANSWER,
    _MARRIAGE_ANSWER,
    _ARUDHA_LAGNA_ANSWER,
    _UPAPADA_LAGNA_ANSWER,
    _MUHURTA_WINDOW_ANSWER,
]


def test_render_current_dasha_happy_path():
    result = render_answer(_CURRENT_DASHA_ANSWER)
    assert "Jupiter" in result
    assert "12 Jan 2020" in result and "12 Jan 2036" in result
    assert "Saturn" in result
    assert "5 Mar 2024" in result and "18 Aug 2026" in result
    assert "Mahadasha" in result and "Antardasha" in result


def test_render_sade_sati_happy_path():
    result = render_answer(_SADE_SATI_ANSWER)
    assert "Sade Sati" in result
    assert "10 Apr 2022" in result and "22 Jun 2027" in result
    assert "3 Jun 2054" in result
    assert "peak phase" in result.lower()


def test_render_career_happy_path():
    result = render_answer(_CAREER_ANSWER)
    assert "Saturn" in result
    assert "strong" in result
    assert "Jupiter" in result and "Mercury" in result
    assert "245.7" in result
    assert "rank 2 of 7" in result


def test_render_marriage_happy_path():
    result = render_answer(_MARRIAGE_ANSWER)
    assert "28.5" in result and "36.0" in result
    assert "highly compatible" in result
    assert "Varna" in result and "Nadi" in result
    assert "groom's chart" in result
    assert "Mangal Dosha" in result


def test_render_arudha_lagna_happy_path():
    result = render_answer(_ARUDHA_LAGNA_ANSWER)
    assert "Leo" in result
    assert "Sagittarius" in result
    assert "Sun" in result
    assert "step_2" in result
    assert "Arudha Lagna" in result


def test_render_upapada_lagna_happy_path():
    result = render_answer(_UPAPADA_LAGNA_ANSWER)
    assert "Aquarius" in result
    assert "Sagittarius" in result
    assert "Ketu" in result
    assert "step_2" in result
    assert "Upapada Lagna" in result


def test_render_muhurta_window_happy_path():
    result = render_answer(_MUHURTA_WINDOW_ANSWER)
    assert "1 Aug 2026 09:00 UTC" in result
    assert "Janma Tara" in result
    assert "Panchaka" in result
    assert "1 window(s) rated excellent" in result


# ─── Muhurta tier relabeling (rule 4, closes CLAUDE.md S64 carry-forward) ─


def test_muhurta_tier_relabeling_replaces_raw_jargon():
    result = render_answer(_MUHURTA_WINDOW_ANSWER)
    assert "excellent" in result
    assert "good" in result
    assert "favorable for you specifically" in result
    # The raw MuhurtaTier value strings must be fully replaced, not just
    # labeled alongside -- proves relabeling actually substitutes them.
    assert "TIER_1" not in result
    assert "TIER_2" not in result
    assert "TIER_3" not in result


# ─── Jargon-gloss compliance across every rendered output ──────────────


def test_no_unglossed_jargon_across_all_domain_outputs():
    for answer in _ALL_HAPPY_PATH_ANSWERS:
        result = render_answer(answer)
        _assert_no_unglossed_jargon(result)
