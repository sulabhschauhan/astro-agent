"""
diagnostics/s121_2bii_live_sample.py

S121 #2b-ii live sample verification. ONE intentional vision call on
data/test_images/palm_right_test.jpg (the SAME image s120_live_palm_run.py
used, so its output is directly comparable to the saved s120 free-prose
tokens) via describe_palm_image, now carrying the new forced menus for
Depth/Width/Length/Curve/Continuity. n=1 -- reported as such, not
overclaimed as stable.
"""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from agent.palm_processor import describe_palm_image

IMAGE = pathlib.Path("data/test_images/palm_right_test.jpg")
OUT = pathlib.Path("diagnostics/s121_2bii_live_sample_raw.json")


def main() -> None:
    image_bytes = IMAGE.read_bytes()
    description = describe_palm_image(image_bytes, "right")

    OUT.write_text(
        json.dumps({"image": str(IMAGE), "hand": "right", "raw": description}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(description)
    print(f"\nWROTE {OUT}")


if __name__ == "__main__":
    main()
