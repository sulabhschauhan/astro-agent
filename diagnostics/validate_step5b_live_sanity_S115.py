"""
diagnostics/validate_step5b_live_sanity_S115.py

S115 live sanity check (authorized budget: N=1 per hand, 2 gpt-4o vision
calls total -- do NOT exceed). A prompt-touching change (removing
joins_at_origin/meets from attribute_feature_mapping) warrants one live
confirmation that H_028 still fires via CONTACTS, zero fabrication, no
new silence, and the reading is unchanged in substance vs prior S107/S109
live runs.

MEASUREMENT HARNESS ONLY -- no production file is imported for mutation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from agent.interpretive import observation_extractor, palm_rules_table  # noqa: E402
from agent.interpretive.palm_reading import _assemble_relational_targets  # noqa: E402
from agent.palm_processor import describe_palm_image  # noqa: E402

LEFT_IMAGE = _REPO_ROOT / "data" / "test_images" / "palm_left_test.jpg"
RIGHT_IMAGE = _REPO_ROOT / "data" / "test_images" / "palm_right_test.jpg"

OUT_PATH = _REPO_ROOT / "diagnostics" / "validate_step5b_live_sanity_S115_raw.json"


def main() -> None:
    left_bytes = LEFT_IMAGE.read_bytes()
    right_bytes = RIGHT_IMAGE.read_bytes()

    print("Calling vision for LEFT hand (1 call)...")
    left_raw = describe_palm_image(left_bytes, "left", temperature=0.0)
    print("Calling vision for RIGHT hand (1 call)...")
    right_raw = describe_palm_image(right_bytes, "right", temperature=0.0)

    assert "joins_at_origin" not in left_raw and "meets" not in left_raw, "typed tokens leaked into raw vision text"

    left_rel = observation_extractor.extract_relations(left_raw)
    right_rel = observation_extractor.extract_relations(right_raw)

    left_ct = _assemble_relational_targets(left_rel["contacts"])
    right_ct = _assemble_relational_targets(right_rel["contacts"])
    targets = observation_extractor.merge_relational_targets(left_ct, right_ct)

    rules = palm_rules_table.load_rule_set()
    fired = sorted(r.rule_id for r in palm_rules_table.match({}, {}, rules, targets=targets))

    head_life_left = [c for c in left_rel["contacts"].get("Line of Head", []) if c.get("target") == "Line of Life"]
    head_life_right = [c for c in right_rel["contacts"].get("Line of Head", []) if c.get("target") == "Line of Life"]

    result = {
        "left_head_life_contacts": head_life_left,
        "right_head_life_contacts": head_life_right,
        "left_ct": {k: {a: (sorted(v) if isinstance(v, set) else v) for a, v in attrs.items()} for k, attrs in left_ct.items()},
        "right_ct": {k: {a: (sorted(v) if isinstance(v, set) else v) for a, v in attrs.items()} for k, attrs in right_ct.items()},
        "fired_rule_ids": fired,
        "h028_fired": "H_028" in fired,
        "left_raw_text": left_raw,
        "right_raw_text": right_raw,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

    print("\n--- Head->Life contacts ---")
    print("LEFT:", head_life_left)
    print("RIGHT:", head_life_right)
    print("\n--- left_ct / right_ct ---")
    print("left_ct:", left_ct)
    print("right_ct:", right_ct)
    print("\n--- Fired rule ids ---")
    print(fired)
    print("\nH_028 fired:", "H_028" in fired)
    print(f"\nRaw dump written to: {OUT_PATH}")


if __name__ == "__main__":
    main()
