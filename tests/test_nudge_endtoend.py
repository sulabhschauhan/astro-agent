"""
tests/test_nudge_endtoend.py
End-to-end tests for context_classifier.classify_context().
All tests make real GPT-4o-mini calls — no mocking.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.context_classifier import classify_context

_PALM_Q     = "What do my palm lines tell me about my future?"
_FORECAST_Q = "Will this year be good for me?"
_VEDIC_Q    = "What does a strong lagna lord mean in Vedic astrology?"


def test_classify_needs_palm_when_palm_missing():
    result = classify_context(
        question=_PALM_Q,
        has_kundali=False,
        has_pdf=False,
        has_palm=False,
    )
    assert result["proceed"] is False
    assert "palm" in result["needs"]


def test_classify_needs_pdf_when_pdf_missing():
    result = classify_context(
        question=_FORECAST_Q,
        has_kundali=False,
        has_pdf=False,
        has_palm=False,
    )
    assert result["proceed"] is False
    assert "pdf" in result["needs"]


def test_classify_proceeds_when_palm_present():
    result = classify_context(
        question=_PALM_Q,
        has_kundali=False,
        has_pdf=False,
        has_palm=True,
    )
    assert result["proceed"] is True
    assert result["needs"] == []


def test_classify_proceeds_when_pdf_present():
    result = classify_context(
        question=_FORECAST_Q,
        has_kundali=False,
        has_pdf=True,
        has_palm=False,
    )
    assert result["proceed"] is True
    assert result["needs"] == []


def test_classify_proceeds_on_general_vedic_query():
    result = classify_context(
        question=_VEDIC_Q,
        has_kundali=False,
        has_pdf=False,
        has_palm=False,
    )
    assert result["proceed"] is True
    assert result["needs"] == []
