"""
tests/manual/letter_ground_truth_check.py
Throwaway diagnostic — do not add to pytest suite.

Right.* and Left.* have "R" / "L" written on the palms — ground-truth
labeled images. Calls validate_palm_image() with both slot values on each
to verify GPT-4o detects the correct hand from image content alone.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.palm_processor import validate_palm_image

_DATA = Path(__file__).parent.parent.parent / "data" / "test_images"
_EXTS = {".jpg", ".jpeg", ".png"}

def find(prefix):
    matches = [p for p in _DATA.iterdir() if p.stem.lower() == prefix.lower() and p.suffix.lower() in _EXTS]
    return matches[0] if matches else None

right_path = find("Right")
left_path  = find("Left")

for path in (right_path, left_path):
    if path is None:
        print(f"MISSING: {path}")
        continue
    image_bytes = path.read_bytes()
    for slot in ("left", "right"):
        result = validate_palm_image(image_bytes, slot)
        print(f"{path.name:<15} slot={slot:<5} -> hand={result['hand']!r}")
    print()
