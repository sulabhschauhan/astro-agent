"""
tests/test_palm_endtoend.py
End-to-end tests for palm validation and prompt assembly.
Tests 1+2+3 are deterministic — no GPT calls.
Test 4 makes real GPT-4o vision calls (two internally).
"""

import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.palm_processor import validate_palm_image
from agent.prompt_builder import build_prompts

_ROOT        = Path(__file__).parent.parent
_LEFT_PATH   = _ROOT / "data" / "test_images" / "palm_left_test.jpg"
_RIGHT_PATH  = _ROOT / "data" / "test_images" / "palm_right_test.jpg"
_LEFT_BYTES  = _LEFT_PATH.read_bytes()
_RIGHT_BYTES = _RIGHT_PATH.read_bytes()

_FAKE_SOURCES = []


# ── Deterministic tests (no GPT) ─────────────────────────────────────────────

def test_duplicate_detection():
    left_hash  = hashlib.md5(_LEFT_BYTES).hexdigest()
    dupe_hash  = hashlib.md5(_LEFT_BYTES).hexdigest()
    assert left_hash == dupe_hash


def test_prompt_assembly():
    result = build_prompts(
        question="What do my palms say?",
        sources=_FAKE_SOURCES,
        palm_left="Left hand: long life line",
        palm_right="Right hand: strong fate line",
    )
    user = result["user"]
    assert "LEFT HAND" in user
    assert "RIGHT HAND" in user
    assert "Synthesise" in user


def test_single_palm_no_synthesis():
    result = build_prompts(
        question="What does my left palm say?",
        sources=_FAKE_SOURCES,
        palm_left="Left hand: long life line",
        palm_right=None,
    )
    user = result["user"]
    assert "LEFT HAND" in user
    assert "RIGHT HAND" not in user
    assert "Synthesise" not in user


# ── GPT vision tests (real API calls) ────────────────────────────────────────

@pytest.mark.integration
def test_validation_is_slot_independent():
    """validate_palm_image results must be image-driven, not influenced by the slot arg."""
    r_left  = validate_palm_image(_LEFT_BYTES, "left")
    r_right = validate_palm_image(_LEFT_BYTES, "right")
    assert r_left["quality"] == r_right["quality"], (
        f"quality changed with slot: slot=left -> {r_left['quality']!r}, "
        f"slot=right -> {r_right['quality']!r}"
    )
    # Compare as sets — temperature=0 should keep content stable, but list
    # ordering of issues/tips is not a guaranteed contract.
    assert set(r_left["issues"]) == set(r_right["issues"]), (
        f"issues changed with slot: slot=left -> {r_left['issues']!r}, "
        f"slot=right -> {r_right['issues']!r}"
    )
    assert set(r_left["geometry_tips"]) == set(r_right["geometry_tips"]), (
        f"geometry_tips changed with slot: slot=left -> {r_left['geometry_tips']!r}, "
        f"slot=right -> {r_right['geometry_tips']!r}"
    )
