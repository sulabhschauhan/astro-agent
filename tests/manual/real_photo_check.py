"""
tests/manual/real_photo_check.py
Throwaway diagnostic — do not add to pytest suite.

Calls validate_palm_image() on palm_left_test.jpg and palm_right_test.jpg
with both slot values to confirm hand detection on the actual test images.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.palm_processor import validate_palm_image

_DATA = Path(__file__).parent.parent.parent / "data" / "test_images"

for fname in ("palm_left_test.jpg", "palm_right_test.jpg"):
    image_bytes = (_DATA / fname).read_bytes()
    for slot in ("left", "right"):
        result = validate_palm_image(image_bytes, slot)
        print(f"{fname:<25} slot={slot:<5} -> hand={result['hand']!r}")
