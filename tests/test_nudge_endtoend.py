"""
tests/test_nudge_endtoend.py
End-to-end nudge tests — route() only, no GPT, no build_prompts().
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.context_router import route

_PALM_Q = "What do my palm lines say about marriage?"
_PDF_Q  = "What does my varshaphal say?"
_BOTH_Q = "My lal kitab and fate line — what do they say?"


def test_palm_topic_no_palm_uploaded():
    r = route(question=_PALM_Q, has_kundali=True, has_pdf=False, has_palm=False)
    assert r["nudge"] is not None
    assert "palm" in r["nudge"].lower()


def test_pdf_topic_no_pdf_uploaded():
    r = route(question=_PDF_Q, has_kundali=True, has_pdf=False, has_palm=False)
    assert r["nudge"] is not None
    assert "AstroSage" in r["nudge"]


def test_palm_topic_palm_already_uploaded():
    r = route(question=_PALM_Q, has_kundali=True, has_pdf=False, has_palm=True)
    assert r["nudge"] is None


def test_pdf_topic_pdf_already_uploaded():
    r = route(question=_PDF_Q, has_kundali=True, has_pdf=True, has_palm=False)
    assert r["nudge"] is None


def test_both_topics_neither_uploaded():
    r = route(question=_BOTH_Q, has_kundali=True, has_pdf=False, has_palm=False)
    assert r["nudge"] is not None
    assert "palm" in r["nudge"].lower()
    assert "AstroSage" in r["nudge"]
