"""
tests/test_nudge_endtoend.py
Integration tests for context_classifier.classify() — new unified classifier
replacing the old classify_context() + route() pair.
All tests make real GPT-4o-mini calls — no mocking.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.context_classifier import classify
from agent.context_bundle import ContextBundle

_PALM_Q     = "What do my palm lines tell me about my future?"
_FORECAST_Q = "What will happen to me this year in 2026?"
_VEDIC_Q    = "What does a strong lagna lord mean in Vedic astrology?"


def test_palm_question_no_palm_hard_blocks():
    bundle = ContextBundle()
    result = classify(question=_PALM_Q, bundle=bundle)
    assert result["hard_block"] is True
    assert result["blocked_on"] == "palm"
    assert result["proceed"] is False


def test_forecast_question_no_pdf_hard_blocks():
    bundle = ContextBundle()
    result = classify(question=_FORECAST_Q, bundle=bundle)
    assert result["hard_block"] is True
    assert result["blocked_on"] == "own_pdf"
    assert result["proceed"] is False


def test_palm_question_palm_present_proceeds():
    bundle = ContextBundle(palm_left="Long life line, strong heart line.")
    result = classify(question=_PALM_Q, bundle=bundle)
    assert result["hard_block"] is False
    assert result["proceed"] is True


def test_forecast_question_pdf_present_proceeds():
    bundle = ContextBundle(own_pdf="Varshaphal 2026: favourable for travel.")
    result = classify(question=_FORECAST_Q, bundle=bundle)
    assert result["hard_block"] is False
    assert result["proceed"] is True


def test_general_vedic_question_empty_bundle():
    bundle = ContextBundle()
    result = classify(question=_VEDIC_Q, bundle=bundle)
    assert result["hard_block"] is False
    assert result["retrieval_profile"] == "vedic"
