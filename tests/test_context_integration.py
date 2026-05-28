"""
tests/test_context_integration.py
Integration tests for context_order routing and prompt assembly.
No GPT calls — build_prompts() is called directly with route() output.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.prompt_builder import build_prompts
from agent.context_router import route

_FAKE_SOURCES = [
    {
        "chunk_id": "BPHS_p1_c0",
        "text": "Jupiter in the 7th house bestows a noble spouse.",
        "topic": "planets",
        "language": "eng",
        "page_ref": 1,
        "image_path": None,
        "book_name": "BPHS - 1 RSanthanam",
        "page_type": "text",
        "score": 0.58,
    },
    {
        "chunk_id": "Saravali_p10_c1",
        "text": "Venus aspecting the 7th lord brings beauty and harmony.",
        "topic": "yoga",
        "language": "eng",
        "page_ref": 10,
        "image_path": None,
        "book_name": "Saravali of Kalyana Varma Santhanam R. (Astrology)",
        "page_type": "text",
        "score": 0.54,
    },
]

_KUNDALI    = "BIRTH DETAILS\nName: Test User\nCurrent period: Venus 2025-2027"
_PDF        = "ASTROSAGE PDF DATA:\n[Varshaphal]\nThis year looks favourable for travel."
_PALM       = "Long life line, strong heart line, well-developed mount of Venus."
_PALM_RIGHT = "Right hand: fate line strong, head line curves down."


def _get_prompts(question, kundali=None, pdf=None, palm_left=None, palm_right=None):
    """Call route() then build_prompts() — mirrors the ask() pipeline without GPT."""
    r = route(
        question=question,
        has_kundali=kundali is not None,
        has_pdf=pdf is not None,
        has_palm=palm_left is not None or palm_right is not None,
    )
    user_msg = build_prompts(
        question=question,
        sources=_FAKE_SOURCES,
        kundali_context=kundali,
        pdf_context=pdf,
        palm_left=palm_left,
        palm_right=palm_right,
        context_order=r.get("context_order", ["rag", "kundali", "pdf"]),
    )["user"]
    return r["context_order"], user_msg


# ── 1. No context, classical question ────────────────────────────────────────

def test_no_context_classical_question():
    order, user = _get_prompts("What is Jupiter in 7th house?")
    assert order == ["rag", "kundali", "pdf"]
    assert "LEFT HAND" not in user
    assert "AstroSage Annual Report" not in user
    assert "KUNDALI CONTEXT" not in user


# ── 2. Kundali only, classical question ──────────────────────────────────────

def test_kundali_only_classical_question():
    order, user = _get_prompts(
        "Explain my lagna lord",
        kundali=_KUNDALI,
    )
    assert order == ["rag", "kundali", "pdf"]
    assert "KUNDALI CONTEXT" in user
    assert "LEFT HAND" not in user
    assert "AstroSage Annual Report" not in user


# ── 3. PDF only, forecast question ───────────────────────────────────────────

def test_pdf_only_forecast_question():
    order, user = _get_prompts("What does my varshaphal say?", pdf=_PDF)
    assert order == ["pdf", "kundali", "rag"]
    assert "AstroSage Annual Report" in user
    assert "KUNDALI CONTEXT" not in user
    assert "LEFT HAND" not in user


# ── 4. Palm only, palm question ───────────────────────────────────────────────

def test_palm_only_palm_question():
    order, user = _get_prompts("What do my palm lines say about marriage?", palm_left=_PALM, palm_right=_PALM_RIGHT)
    assert order == ["palm", "kundali", "rag"]
    assert "LEFT HAND (innate potential)" in user
    assert "RIGHT HAND (current trajectory)" in user
    assert "KUNDALI CONTEXT" not in user
    assert "AstroSage Annual Report" not in user


# ── 5. Kundali + PDF, forecast question ──────────────────────────────────────

def test_kundali_and_pdf_forecast_question():
    order, user = _get_prompts(
        "What does my 2026 muntha predict?",
        kundali=_KUNDALI,
        pdf=_PDF,
    )
    assert order == ["pdf", "kundali", "rag"]
    assert "AstroSage Annual Report" in user
    assert "KUNDALI CONTEXT" in user
    assert "LEFT HAND" not in user


# ── 6. Kundali + palm, palm question ─────────────────────────────────────────

def test_kundali_and_palm_palm_question():
    order, user = _get_prompts(
        "Will I be wealthy based on my palm?",
        kundali=_KUNDALI,
        palm_left=_PALM,
        palm_right=_PALM_RIGHT,
    )
    assert order == ["palm", "kundali", "rag"]
    assert "LEFT HAND (innate potential)" in user
    assert "RIGHT HAND (current trajectory)" in user
    assert "KUNDALI CONTEXT" in user
    assert "AstroSage Annual Report" not in user


# ── 7. All three contexts, forecast question ─────────────────────────────────

def test_all_three_contexts_forecast_question():
    order, user = _get_prompts(
        "What does sade sati mean for my wealth palm?",
        kundali=_KUNDALI,
        pdf=_PDF,
        palm_left=_PALM,
        palm_right=_PALM_RIGHT,
    )
    assert order == ["pdf", "palm", "kundali", "rag"]
    assert "AstroSage Annual Report" in user
    assert "LEFT HAND (innate potential)" in user
    assert "RIGHT HAND (current trajectory)" in user
    assert "KUNDALI CONTEXT" in user


# ── 8. All three contexts, mixed health/year/palm question ───────────────────

def test_all_three_contexts_mixed_question():
    order, user = _get_prompts(
        "My lal kitab and fate line — what do they say?",
        kundali=_KUNDALI,
        pdf=_PDF,
        palm_left=_PALM,
        palm_right=_PALM_RIGHT,
    )
    assert order == ["pdf", "palm", "kundali", "rag"]
    assert "AstroSage Annual Report" in user
    assert "LEFT HAND (innate potential)" in user
    assert "RIGHT HAND (current trajectory)" in user
    assert "KUNDALI CONTEXT" in user
