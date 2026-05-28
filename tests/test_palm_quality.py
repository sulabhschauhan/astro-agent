"""
tests/test_palm_quality.py
Quality / hallucination tests for palm context in ask().
All 4 tests make real GPT calls — marked as integration.
Run with: pytest -m integration -v
"""

import time
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.astrologer import ask

_ROOT = Path(__file__).parent.parent

# ── Fixtures ─────────────────────────────────────────────────────────────────

_KUNDALI_PATH = _ROOT / "data" / "default_user" / "kundali_summary.txt"
_KUNDALI = (
    _KUNDALI_PATH.read_text(encoding="utf-8")
    if _KUNDALI_PATH.exists()
    else "Sun in Aries, Moon in Cancer, Jupiter in 7th house, Ketu mahadasha until 2025."
)

_PALM_LEFT = (
    "LEFT HAND: Long deep life line with slight fork near termination, "
    "long head line sloping toward Luna mount, moderate heart line "
    "originating under Jupiter mount, fate line present and clearer upward "
    "toward Saturn mount, Venus mount well developed."
)

_PALM_RIGHT = (
    "RIGHT HAND: Long deep life line with minor outward branches, "
    "long head line moderate to deep sloping toward Luna, "
    "heart line medium to long with minor upward branches, "
    "fate line medium depth with slight interruptions mid-palm, "
    "faint sun/Apollo line, Venus mount well developed."
)

PALM_TERMS = ["left hand", "right hand", "life line", "fate line", "heart line"]

QUESTION_NO_PALM   = "What does my career and wealth trajectory look like?"
QUESTION_WITH_PALM = "What do my palm lines reveal about my career and wealth?"


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.integration
def test_no_context_no_hallucination():
    result = ask(question=QUESTION_NO_PALM)
    answer = result["answer"].lower()
    print(f"\n[test_no_context_no_hallucination]\n{result['answer']}\n")
    assert not any(term in answer for term in PALM_TERMS), (
        f"Palm term found in answer without palm context: {[t for t in PALM_TERMS if t in answer]}"
    )


@pytest.mark.integration
def test_kundali_only_no_hallucination():
    time.sleep(2)
    result = ask(question=QUESTION_NO_PALM, kundali_context=_KUNDALI)
    answer = result["answer"].lower()
    print(f"\n[test_kundali_only_no_hallucination]\n{result['answer']}\n")
    assert not any(term in answer for term in PALM_TERMS), (
        f"Palm term found in answer without palm context: {[t for t in PALM_TERMS if t in answer]}"
    )


@pytest.mark.integration
def test_palm_only_terms_present():
    time.sleep(2)
    result = ask(question=QUESTION_WITH_PALM, palm_left=_PALM_LEFT, palm_right=_PALM_RIGHT)
    answer = result["answer"].lower()
    print(f"\n[test_palm_only_terms_present]\n{result['answer']}\n")
    assert any(term in answer for term in PALM_TERMS), (
        f"No palm term found in answer despite palm context provided."
    )


@pytest.mark.integration
def test_kundali_and_palm_both_referenced():
    time.sleep(2)
    result = ask(
        question=QUESTION_WITH_PALM,
        kundali_context=_KUNDALI,
        palm_left=_PALM_LEFT,
        palm_right=_PALM_RIGHT,
    )
    answer = result["answer"].lower()
    print(f"\n[test_kundali_and_palm_both_referenced]\n{result['answer']}\n")
    assert any(term in answer for term in PALM_TERMS), (
        f"No palm term found in answer despite palm context provided."
    )
    assert any(term in answer for term in ["period", "antardasha", "mahadasha", "venus", "ketu"]), (
        f"No kundali term found in answer despite kundali context provided."
    )
