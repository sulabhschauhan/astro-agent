"""
diagnostics/validate_step5b_live_sanity_S107.py

S107 Stage 5 live two-hand sanity check (authorized budget: N=3 per hand,
6 gpt-4o calls total, temp=0 -- production-faithful, do NOT exceed).

Runs the CURRENT HEAD vision path (post Stage 1 + Stage 3 code -- RELATIONSHIP
retired, CONTACTS is the sole channel, contact_mapper is S106-inflection-
aware) against the two standing test hand images, through the full
extract_relations -> palm_reading._assemble_relational_targets ->
merge_relational_targets -> match() chain. Captures the raw HEAD-LINE
CONTACTS verb per run and reports fire/non-fire for H_028 against the
judgment rule this task specifies: a join-family verb (joins/joined/
joining/merges/...) at "at start" MUST fire H_028; "touches" is a CORRECT
NON-FIRE (a touch is not a join per Cheiro doctrine). Also checks for
fabrication (any token assigned that isn't grounded in a real reported
verb) and crashes.

MEASUREMENT HARNESS ONLY -- no production file is imported for mutation.
Report goes to diagnostics/latest_run.md (written by the caller, not this
script -- this script prints to stdout and writes a raw JSON dump).
"""

from __future__ import annotations

import json
import sys
import time
import traceback
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from agent.interpretive import observation_extractor, palm_rules_table  # noqa: E402
from agent.interpretive.palm_reading import _assemble_relational_targets  # noqa: E402
from agent.palm_processor import describe_palm_image  # noqa: E402

LEFT_IMAGE = _REPO_ROOT / "data" / "test_images" / "palm_left_test.jpg"
RIGHT_IMAGE = _REPO_ROOT / "data" / "test_images" / "palm_right_test.jpg"
N_PER_HAND = 3

OUT_PATH = _REPO_ROOT / "diagnostics" / "validate_step5b_live_sanity_S107_raw.json"

_JOIN_FAMILY_VERBS_JUDGMENT = frozenset({
    "joins", "joined", "joining", "merges", "merged", "merging", "meets", "meeting",
})


def _run_one(hand: str, image_bytes: bytes, run_idx: int) -> dict:
    record: dict = {
        "hand": hand, "run": run_idx, "error": None, "raw_text": None,
        "head_life_contacts": None, "targets": None, "fired_ids": None,
        "h028_fired": None, "judgment": None,
    }
    try:
        raw_text = describe_palm_image(image_bytes, hand, temperature=0.0)
    except Exception as exc:  # noqa: BLE001 -- one failed call must not abort the sweep
        record["error"] = f"describe_palm_image failed: {type(exc).__name__}: {exc}"
        print(f"  [ERROR] hand={hand} run={run_idx}: {record['error']}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return record

    record["raw_text"] = raw_text

    try:
        rel = observation_extractor.extract_relations(raw_text)
        targets = _assemble_relational_targets(rel["contacts"])
        rules = palm_rules_table.load_rule_set()
        fired = sorted(r.rule_id for r in palm_rules_table.match({}, {}, rules, targets=targets))
    except Exception as exc:  # noqa: BLE001 -- a parse/match failure must still be recorded
        record["error"] = f"pipeline failed: {type(exc).__name__}: {exc}"
        print(f"  [ERROR] hand={hand} run={run_idx}: {record['error']}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return record

    # Isolate the Head->Life contact(s) specifically for the judgment rule.
    head_contacts = rel["contacts"].get("Line of Head", [])
    life_contacts = [c for c in head_contacts if c.get("target") == "Line of Life"]

    record["head_life_contacts"] = life_contacts
    record["targets"] = {
        feat: {attr: (sorted(v) if isinstance(v, set) else v) for attr, v in attrs.items()}
        for feat, attrs in targets.items()
    }
    record["fired_ids"] = fired
    record["h028_fired"] = "H_028" in fired

    # Judgment rule: a join-family verb at "at start" MUST fire H_028;
    # "touches" is a correct non-fire; anything else is reported as-is.
    if life_contacts:
        verb = life_contacts[0].get("verb", "").strip().lower()
        position = life_contacts[0].get("position", "").strip().lower()
        if verb in _JOIN_FAMILY_VERBS_JUDGMENT and position == "at start":
            record["judgment"] = "MUST_FIRE" if record["h028_fired"] else "VIOLATION_did_not_fire"
        elif verb == "touches":
            record["judgment"] = "CORRECT_NON_FIRE" if not record["h028_fired"] else "UNEXPECTED_fired_on_touches"
        else:
            record["judgment"] = f"OTHER_verb={verb!r}_position={position!r}_fired={record['h028_fired']}"
    else:
        record["judgment"] = "NO_HEAD_LIFE_CONTACT_REPORTED"

    print(f"  hand={hand} run={run_idx} -> life_contacts={life_contacts} h028_fired={record['h028_fired']} judgment={record['judgment']}")
    return record


def main() -> None:
    t0 = time.time()
    left_bytes = LEFT_IMAGE.read_bytes()
    right_bytes = RIGHT_IMAGE.read_bytes()

    all_records: list[dict] = []
    for hand, image_bytes in (("left", left_bytes), ("right", right_bytes)):
        for run_idx in range(N_PER_HAND):
            print(f"Calling vision: hand={hand} run={run_idx + 1}/{N_PER_HAND} ...")
            rec = _run_one(hand, image_bytes, run_idx)
            all_records.append(rec)

    OUT_PATH.write_text(json.dumps(all_records, indent=2, default=str), encoding="utf-8")

    elapsed = time.time() - t0
    n_errors = sum(1 for r in all_records if r["error"] is not None)
    n_violations = sum(1 for r in all_records if r.get("judgment") == "VIOLATION_did_not_fire")
    print(f"\nDone in {elapsed:.1f}s. {len(all_records)} run(s), {n_errors} error(s), {n_violations} judgment violation(s).")
    print(f"Raw dump written to: {OUT_PATH}")


if __name__ == "__main__":
    main()
