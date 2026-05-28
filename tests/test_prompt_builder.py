"""
tests/test_prompt_builder.py
Acceptance tests for Option C palm nudge (debate-agreed implementation).
Tests 1 and 3 fail until prompt_builder.py is updated with expanded PALM_TOPICS,
has_palm_description flag, and combine instruction.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.prompt_builder import build_prompts

_SOURCES = []  # nudge and combine logic does not depend on retrieved sources


def test_nudge_present_when_palm_missing_and_topic_matches():
    # "rich" must be in PALM_TOPICS after expansion — this test fails until that change lands
    result = build_prompts(
        question="Will I get rich?",
        sources=_SOURCES,
        palm_description=None,
    )
    # If nudge wording in build_prompts() changes, update this string
    assert "[If you have a palm description available" in result["user"]


def test_nudge_absent_when_palm_missing_and_no_topic_match():
    # Factual query with no PALM_TOPICS keyword — nudge must never fire here
    result = build_prompts(
        question="What is Vedic astrology?",
        sources=_SOURCES,
        palm_description=None,
    )
    # If nudge wording in build_prompts() changes, update this string
    assert "[If you have a palm description available" not in result["user"]


def test_combine_language_present_when_palm_description_set():
    # Combine instruction fires when palm_description provided; nudge must be suppressed
    # This test fails until the has_palm_description flag and combine instruction land
    result = build_prompts(
        question="Tell me about my future",
        sources=_SOURCES,
        palm_description="Long life line, strong heart line",
    )
    # If combine wording in build_prompts() changes, update this string
    assert "synthesise both" in result["user"]
    # If nudge wording changes, update this string
    assert "[If you have a palm description available" not in result["user"]
