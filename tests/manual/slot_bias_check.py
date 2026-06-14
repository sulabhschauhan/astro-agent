"""
tests/manual/slot_bias_check.py
Throwaway diagnostic — do not add to pytest suite.

Calls validate_palm_image() twice with the same image bytes,
once with slot="left" and once with slot="right", to determine
whether GPT-4o's hand classification is influenced by the slot
argument or is purely image-driven.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.palm_processor import validate_palm_image

_DATA = Path(__file__).parent.parent.parent / "data" / "test_images"

for fname in ("palm_left_test.jpg", "palm_right_test.jpg"):
    image_bytes = (_DATA / fname).read_bytes()
    print(f"Image: {fname}  ({len(image_bytes)} bytes)")
    r_left  = validate_palm_image(image_bytes, "left")
    r_right = validate_palm_image(image_bytes, "right")
    print(f"  slot=left   -> hand={r_left['hand']!r:10}  matches_slot={r_left.get('matches_slot')}")
    print(f"  slot=right  -> hand={r_right['hand']!r:10}  matches_slot={r_right.get('matches_slot')}")
    identical = r_left["hand"] == r_right["hand"]
    print(f"  slot-independent: {identical}\n")
