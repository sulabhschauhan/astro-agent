"""
diagnostics/validate_step5b_live_sanity.py

S104 Step 5b Stage 5 live two-hand sanity check. Runs the real vision call
on the two standing test hand images (data/test_images/palm_left_test.jpg,
palm_right_test.jpg -- one call per hand, within the instructing prompt's
own budget guard), through the now-sole CONTACTS -> palm_reading.
_assemble_relational_targets -> merge_relational_targets -> match() chain,
and reports whether Head-joins-Life (H_028) fires, any quarantined
contacts (fabrication/off-menu check), and the full fired rule-id list.

MEASUREMENT HARNESS ONLY -- no production file is imported for mutation.
Report goes to diagnostics/latest_run.md (appended by the caller, not this
script -- this script prints to stdout only).
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from agent.interpretive import observation_extractor, palm_rules_table
from agent.interpretive.palm_reading import _assemble_relational_targets
from agent.palm_processor import describe_palm_image

LEFT_IMAGE = _REPO_ROOT / "data" / "test_images" / "palm_left_test.jpg"
RIGHT_IMAGE = _REPO_ROOT / "data" / "test_images" / "palm_right_test.jpg"


def main() -> None:
    left_bytes = LEFT_IMAGE.read_bytes()
    right_bytes = RIGHT_IMAGE.read_bytes()

    print("Calling vision for LEFT hand...")
    left_raw = describe_palm_image(left_bytes, "left")
    print("Calling vision for RIGHT hand...")
    right_raw = describe_palm_image(right_bytes, "right")

    assert "RELATIONSHIP" not in left_raw, "RELATIONSHIP leaked into live LEFT vision output!"
    assert "RELATIONSHIP" not in right_raw, "RELATIONSHIP leaked into live RIGHT vision output!"

    left_rel = observation_extractor.extract_relations(left_raw)
    right_rel = observation_extractor.extract_relations(right_raw)

    left_ct = _assemble_relational_targets(left_rel["contacts"])
    right_ct = _assemble_relational_targets(right_rel["contacts"])
    targets = observation_extractor.merge_relational_targets(
        left_rel["targets"], right_rel["targets"], left_ct, right_ct,
    )

    rules = palm_rules_table.load_rule_set()
    fired = palm_rules_table.match({}, {}, rules, targets=targets)
    fired_ids = sorted(r.rule_id for r in fired)

    print("\n--- LEFT raw CONTACTS lines ---")
    for line in left_raw.splitlines():
        if "CONTACTS" in line:
            print(" ", line.strip())
    print("\n--- RIGHT raw CONTACTS lines ---")
    for line in right_raw.splitlines():
        if "CONTACTS" in line:
            print(" ", line.strip())

    print("\n--- Parsed contacts (left) ---")
    print(left_rel["contacts"])
    print("--- Parsed contacts (right) ---")
    print(right_rel["contacts"])

    print("\n--- Bridge-derived targets (left) ---")
    print(left_ct)
    print("--- Bridge-derived targets (right) ---")
    print(right_ct)

    print("\n--- Merged targets ---")
    print(targets)

    print("\n--- Fired rule ids ---")
    print(fired_ids)

    print("\nH_028 fired:", "H_028" in fired_ids)
    print("L_026 fired:", "L_026" in fired_ids)

    print("\nDone.")


if __name__ == "__main__":
    main()
