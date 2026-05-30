"""
tests/test_prompt_builder.py
Tests for build_prompts() with the updated signature — spouse_pdf, hand_detail,
new slot keys ("own_pdf", "spouse_pdf", "hand_detail"), and removal of the
PALM_TOPICS nudge block (now owned by context_classifier).
No GPT calls — all deterministic.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.prompt_builder import build_prompts

_SOURCES = []

_SPOUSE_PDF  = "SPOUSE ASTROSAGE DATA:\n[Varshaphal]\nThis year looks positive."
_HAND_DETAIL = "Long fingers, flexible thumb, strong Mercury mount."
_PALM_LEFT   = "Long life line, strong heart line."
_PALM_RIGHT  = "Strong fate line, prominent mount of Jupiter."


def test_spouse_pdf_slot_renders():
    result = build_prompts(
        question="How will my wife's year go?",
        sources=_SOURCES,
        spouse_pdf=_SPOUSE_PDF,
        context_order=["spouse_pdf"],
    )
    assert "Spouse AstroSage Annual Report" in result["user"]
    assert "SPOUSE ASTROSAGE DATA" in result["user"]


def test_hand_detail_slot_renders():
    result = build_prompts(
        question="What do my hand features say?",
        sources=_SOURCES,
        hand_detail=_HAND_DETAIL,
        context_order=["hand_detail"],
    )
    assert "Hand Detail Analysis" in result["user"]
    assert _HAND_DETAIL in result["user"]


def test_dual_palm_synthesis_present():
    result = build_prompts(
        question="Tell me about my future",
        sources=_SOURCES,
        palm_left=_PALM_LEFT,
        palm_right=_PALM_RIGHT,
        context_order=["palm"],
    )
    assert "Synthesise both" in result["user"]
    assert "LEFT HAND (innate potential)" in result["user"]
    assert "RIGHT HAND (current trajectory)" in result["user"]


def test_palm_topics_nudge_removed():
    # Regression guard: PALM_TOPICS nudge block must be absent after removal.
    result = build_prompts(
        question="Will I get rich?",
        sources=_SOURCES,
        palm_left=None,
        palm_right=None,
    )
    assert "[If you have a palm description available" not in result["user"]
