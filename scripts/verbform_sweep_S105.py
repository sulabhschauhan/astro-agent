"""
scripts/verbform_sweep_S105.py

S105 pre-5b measurement sweep. READ-ONLY -- no production file is imported
for mutation, no source commit follows this run.

Runs the CURRENT HEAD vision path (agent.palm_processor.describe_palm_image,
temp=0, production-faithful) 3x per standing test hand image (6 live gpt-4o
calls total, the exact budget this task authorized -- do not raise N, do
not add images, do not vary temperature). Parses each run's CONTACTS lines
via the REAL observation_extractor.extract_relations (not re-implemented),
then labels every captured contact via the REAL contact_mapper.map_contact
-- this is the silence census: exactly which live verb-forms resolve to a
token today and which fall through to quarantine, and why.

Purpose: S104 Step 5b aborted on a single live silence ("joined" not in
contact_mapper's join-family verb table, N=1, both hands but only one
call each). Before designing an inflection-stem list or an LLM fallback,
this sweep measures real phrasing variance across N=3 per hand so the
fix is set against data, not one photo pair.

FAIL-CLOSED: a run that errors or returns no CONTACTS lines is recorded as
such, never skipped silently or back-filled with a prior run's output.
Each vision call is wrapped in its own try/except; one failed call does
not abort the sweep.

Report goes to diagnostics/latest_run.md (overwrite, per this project's own
diagnostics convention) -- this script prints to stdout only; the caller
writes the report.
"""

from __future__ import annotations

import json
import sys
import time
import traceback
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from agent.interpretive import observation_extractor  # noqa: E402
from agent.interpretive.contact_mapper import map_contact  # noqa: E402
from agent.palm_processor import describe_palm_image  # noqa: E402

LEFT_IMAGE = _REPO_ROOT / "data" / "test_images" / "palm_left_test.jpg"
RIGHT_IMAGE = _REPO_ROOT / "data" / "test_images" / "palm_right_test.jpg"
N_PER_HAND = 3

OUT_PATH = _REPO_ROOT / "diagnostics" / "verbform_sweep_S105_raw.json"


def _mime(image_bytes: bytes) -> str:
    return "image/png" if image_bytes[:8].startswith(b"\x89PNG") else "image/jpeg"


def _run_one(hand: str, image_bytes: bytes, run_idx: int) -> dict:
    """One live vision call + full parse/label pipeline for one run.
    Never raises -- any failure is captured into the returned record."""
    record: dict = {
        "hand": hand,
        "run": run_idx,
        "error": None,
        "raw_text": None,
        "contacts": None,
        "labeled_contacts": None,
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
        parsed = observation_extractor.extract_relations(raw_text)
        contacts = parsed["contacts"]
    except Exception as exc:  # noqa: BLE001 -- a parse failure must still be recorded, not silently dropped
        record["error"] = f"extract_relations failed: {type(exc).__name__}: {exc}"
        print(f"  [ERROR] hand={hand} run={run_idx}: {record['error']}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return record

    record["contacts"] = contacts

    labeled: list[dict] = []
    for feature, contact_list in contacts.items():
        for c in contact_list:
            try:
                mapped = map_contact(c)
            except Exception as exc:  # noqa: BLE001 -- a mapper crash on one contact must not lose the rest
                mapped = {
                    "token": None, "confidence": None,
                    "raw_verb": c.get("verb"), "target": c.get("target"),
                    "position": c.get("position"),
                    "reason": f"map_contact raised: {type(exc).__name__}: {exc}",
                }
            labeled.append({"feature": feature, **mapped, "clarity": c.get("clarity")})
    record["labeled_contacts"] = labeled

    print(
        f"  hand={hand} run={run_idx} -> OK "
        f"({sum(len(v) for v in contacts.values())} contact(s) across "
        f"{len(contacts)} feature(s))"
    )
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
    print(f"\nDone in {elapsed:.1f}s. {len(all_records)} run(s), {n_errors} error(s).")
    print(f"Raw dump written to: {OUT_PATH}")


if __name__ == "__main__":
    main()
