"""
tests/test_context_integration.py
Tests for build_prompts() rendering with classifier-style context_order inputs.
No imports of route or classify. No GPT calls. build_prompts() called directly
with hardcoded context_order lists that mirror what classify() would return.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.prompt_builder import build_prompts

_SOURCES = [
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
    }
]

_KUNDALI     = "BIRTH DETAILS\nName: Test User\nCurrent period: Venus 2025-2027"
_OWN_PDF     = "ASTROSAGE PDF DATA:\n[Varshaphal]\nThis year looks favourable."
_SPOUSE_PDF  = "SPOUSE ASTROSAGE DATA:\n[Varshaphal]\nSpouse year looks positive."
_PALM_LEFT   = "Long life line, strong heart line."
_PALM_RIGHT  = "Strong fate line, prominent mount of Jupiter."
_HAND_DETAIL = "Long fingers, flexible thumb, strong Mercury mount."


def test_vedic_context_order():
    user = build_prompts(
        question="What does a strong Jupiter mean?",
        sources=_SOURCES,
        kundali_context=_KUNDALI,
        context_order=["kundali", "rag"],
    )["user"]
    assert "KUNDALI CONTEXT" in user
    assert "Retrieved passages" in user
    assert "AstroSage Annual Report" not in user
    assert "LEFT HAND" not in user


def test_palmistry_context_order():
    user = build_prompts(
        question="What do my palm lines say?",
        sources=_SOURCES,
        palm_left=_PALM_LEFT,
        palm_right=_PALM_RIGHT,
        context_order=["palm_left", "palm_right", "rag"],
    )["user"]
    assert "LEFT HAND (innate potential)" in user
    assert "RIGHT HAND (current trajectory)" in user
    assert "KUNDALI CONTEXT" not in user


def test_own_pdf_context_order():
    user = build_prompts(
        question="What does my annual report say?",
        sources=_SOURCES,
        pdf_context=_OWN_PDF,
        context_order=["own_pdf", "kundali", "rag"],
    )["user"]
    assert "AstroSage Annual Report" in user
    assert _OWN_PDF in user


def test_full_context_order_all_slots():
    user = build_prompts(
        question="Give me a complete reading.",
        sources=_SOURCES,
        kundali_context=_KUNDALI,
        pdf_context=_OWN_PDF,
        spouse_pdf=_SPOUSE_PDF,
        palm_left=_PALM_LEFT,
        palm_right=_PALM_RIGHT,
        hand_detail=_HAND_DETAIL,
        context_order=[
            "kundali", "own_pdf", "spouse_pdf",
            "palm_left", "palm_right", "hand_detail", "rag",
        ],
    )["user"]
    assert "KUNDALI CONTEXT" in user
    assert "AstroSage Annual Report" in user
    assert "Spouse AstroSage Annual Report" in user
    assert "LEFT HAND (innate potential)" in user
    assert "RIGHT HAND (current trajectory)" in user
    assert "Hand Detail Analysis" in user
    assert "Retrieved passages" in user
