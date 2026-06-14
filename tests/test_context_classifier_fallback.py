"""
tests/test_context_classifier_fallback.py
Tests _fail_open() fallback behaviour when classify()'s API call raises.
No real API calls — OpenAI client is patched to raise immediately.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.context_bundle import ContextBundle
from agent.context_classifier import classify


def _make_client_that_raises():
    client = MagicMock()
    client.chat.completions.create.side_effect = RuntimeError("simulated API failure")
    return client


def test_fallback_kundali_palm_left_palm_right():
    """Fallback with kundali + palm_left + palm_right (no own_pdf) should include
    all three slots plus rag, and set retrieval_profile to vedic (kundali present)."""
    bundle = ContextBundle(
        kundali="BIRTH DETAILS\nName: Test",
        palm_left="Long life line.",
        palm_right="Strong fate line.",
    )
    with patch("agent.context_classifier.OpenAI", return_value=_make_client_that_raises()):
        result = classify("What does my chart say?", bundle)

    assert result["proceed"] is True
    assert result["hard_block"] is False
    assert result["blocked_on"] is None
    assert result["context_order"] == ["kundali", "palm_left", "palm_right", "rag"]
    assert result["retrieval_profile"] == "vedic"


def test_fallback_palm_only_returns_palmistry_profile():
    """When only palm images are present (no kundali/own_pdf), fallback should
    set retrieval_profile to 'palmistry'."""
    bundle = ContextBundle(palm_left="Long life line.", palm_right="Strong fate line.")
    with patch("agent.context_classifier.OpenAI", return_value=_make_client_that_raises()):
        result = classify("Read my palm.", bundle)

    assert result["context_order"] == ["palm_left", "palm_right", "rag"]
    assert result["retrieval_profile"] == "palmistry"


def test_fallback_empty_bundle_returns_rag_only():
    """Empty bundle should fall back to just ['rag'] with 'vedic' profile."""
    bundle = ContextBundle()
    with patch("agent.context_classifier.OpenAI", return_value=_make_client_that_raises()):
        result = classify("Tell me about Saturn.", bundle)

    assert result["context_order"] == ["rag"]
    assert result["retrieval_profile"] == "vedic"


def test_fallback_all_slots_present():
    """All context slots present should appear in fallback context_order in canonical order."""
    bundle = ContextBundle(
        kundali="chart",
        own_pdf="pdf",
        spouse_pdf="spouse",
        palm_left="left",
        palm_right="right",
        hand_detail="detail",
    )
    with patch("agent.context_classifier.OpenAI", return_value=_make_client_that_raises()):
        result = classify("Full reading please.", bundle)

    assert result["context_order"] == [
        "kundali", "own_pdf", "spouse_pdf", "palm_left", "palm_right", "hand_detail", "rag"
    ]
    assert result["retrieval_profile"] == "vedic"
