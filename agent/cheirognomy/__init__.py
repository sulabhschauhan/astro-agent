"""
agent/cheirognomy — Cheirognomy (hand-type) capture.

Rubric + schema: data/palm_rules/_doctrine/CHEIROGNOMY_HAND_TYPE.md

VLM-ONLY. The doctrine's §3 arm split originally assigned the objective
geometry primitives to a MediaPipe arm; that arm is scrapped. A single VLM arm
now emits BOTH halves as qualitative doctrine words, and the two-arm
reconciliation of §6 is replaced by SELF-CONSISTENCY across repeated runs —
same rule, same consequence: disagreement is a flag, never a forced call.

The whole-hand type is DERIVED from the emitted primitives (§5), never captured
directly, so "mixed" means "the fingers disagree" rather than "unknown".
"""

from agent.cheirognomy.vlm_arm import (
    CheirognomyDoctrineError,
    CheirognomyResult,
    VLMArmError,
    classify_hand,
    compare_hands,
    load_doctrine,
)

__all__ = [
    "classify_hand",
    "compare_hands",
    "load_doctrine",
    "CheirognomyResult",
    "CheirognomyDoctrineError",
    "VLMArmError",
]
