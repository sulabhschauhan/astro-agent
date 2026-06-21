"""
targeted_delete_execute.py
Executes the targeted ChromaDB delete planned and snapshotted by
targeted_delete_dryrun.py (diagnostics/targeted_delete_dryrun_20260621_120557.md).
Deletes the 3,945 X_c<N> duplicate-text child chunks identified there,
keeping their X parents. ChromaDB is a derived cache of the source PDFs
(project_files/classical_references/) -- this delete does not touch source
content, progress files, chunked_chunks.json, or any ingestion/ code.

WRITE CONTRACT: exactly one ChromaDB write call in this script --
collection.delete(ids=plan). No .update()/.upsert()/.add()/.modify().
Four pre-execute sanity checks must ALL pass before that call is made; any
single failure aborts before .delete() is ever invoked. Restoration
insurance is the existing snapshot file (diagnostics/targeted_delete_
snapshot_20260621_120557.jsonl) -- read by no one here, only referenced in
the report; the restore command itself is documented, not executed.

NOT safe to blindly re-run after a successful execution: pre-execute sanity
check #4 (pre-count == 11,688) fails by design once the delete has
happened, since the collection is then at 7,743 -- that mismatch is the
re-run guard, not a bug.
"""

import json
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # project root, for `ingestion` import

from ingestion.query_engine import CHROMA_DIR, COLLECTION_NAME, get_collection

DIAG_DIR = Path(__file__).parent
PLAN_PATH = DIAG_DIR / "targeted_delete_plan_20260621_120557.json"
SNAPSHOT_PATH = DIAG_DIR / "targeted_delete_snapshot_20260621_120557.jsonl"

EXPECTED_PLAN_COUNT = 3945
EXPECTED_PRE_COUNT = 11688
EXPECTED_POST_COUNT = 7743
SAMPLE_N = 20
RANDOM_SEED = 23  # matches the dry-run's spot-check seed, for traceability only -- not a correctness requirement

SUFFIX_RE = re.compile(r"^(.*)_c\d+$")


def _open_collection():
    try:
        collection = get_collection(CHROMA_DIR)
    except Exception as exc:
        raise RuntimeError(
            f"Could not open ChromaDB collection '{COLLECTION_NAME}' at '{CHROMA_DIR}': {exc}"
        ) from exc
    return collection


def check_plan_file() -> tuple[bool, str, list]:
    if not PLAN_PATH.exists():
        return False, f"Plan file not found: {PLAN_PATH}", []
    try:
        plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, f"Plan file failed to parse as JSON: {exc}", []
    if not isinstance(plan, list):
        return False, f"Plan file does not contain a JSON list (got {type(plan).__name__})", []
    if len(plan) != EXPECTED_PLAN_COUNT:
        return False, f"Plan count {len(plan)} != expected {EXPECTED_PLAN_COUNT}", plan
    return True, f"Plan file `{PLAN_PATH.name}` parses as a JSON list of {len(plan)} chunk_ids.", plan


def check_snapshot_file() -> tuple[bool, str, list]:
    if not SNAPSHOT_PATH.exists():
        return False, f"Snapshot file not found: {SNAPSHOT_PATH}", []
    try:
        raw_lines = SNAPSHOT_PATH.read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        return False, f"Snapshot file failed to read: {exc}", []
    lines = [l for l in raw_lines if l.strip()]
    if len(lines) != EXPECTED_PLAN_COUNT:
        return False, f"Snapshot line count {len(lines)} != expected {EXPECTED_PLAN_COUNT}", lines
    return True, f"Snapshot file `{SNAPSHOT_PATH.name}` has {len(lines)} lines.", lines


def check_cross_reference(plan: list, snapshot_lines: list) -> tuple[bool, str]:
    if not snapshot_lines:
        return False, "No snapshot lines to spot-check (snapshot file check already failed)."
    try:
        first_record = json.loads(snapshot_lines[0])
    except Exception as exc:
        return False, f"Snapshot's first line failed to parse as JSON: {exc}"
    chunk_id = first_record.get("chunk_id")
    if chunk_id not in set(plan):
        return False, f"Snapshot's first record chunk_id {chunk_id!r} is NOT present in the plan."
    return True, f"Snapshot's first record chunk_id `{chunk_id}` confirmed present in the plan."


def check_pre_count(collection) -> tuple[bool, str, int]:
    try:
        count = collection.count()
    except Exception as exc:
        return False, f"collection.count() failed: {exc}", -1
    if count != EXPECTED_PRE_COUNT:
        return False, (
            f"Pre-delete count {count} != expected {EXPECTED_PRE_COUNT} -- something "
            "changed in the collection since the dry-run; the plan may be stale."
        ), count
    return True, f"Pre-delete collection.count() == {count}, matches the dry-run's pre-state.", count


def main():
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = []
    lines.append("# Targeted Delete Execute -- X / X_c<N> Duplicate Chunks\n")
    lines.append(f"**Generated:** {now}  ")
    lines.append(f"**Collection:** `{COLLECTION_NAME}` @ `{CHROMA_DIR}`  ")
    lines.append(f"**Plan file:** `{PLAN_PATH.name}` (not modified)  ")
    lines.append(f"**Snapshot file:** `{SNAPSHOT_PATH.name}` (restoration insurance, not modified)\n")

    collection = _open_collection()

    # --- Pre-execute sanity checks ---
    lines.append("## Sanity-check results\n")

    plan_ok, plan_msg, plan = check_plan_file()
    lines.append(f"1. Plan file valid, count == {EXPECTED_PLAN_COUNT}: {'PASS' if plan_ok else 'FAIL'} -- {plan_msg}")

    snap_ok, snap_msg, snapshot_lines = check_snapshot_file()
    lines.append(f"2. Snapshot file valid, line count == {EXPECTED_PLAN_COUNT}: {'PASS' if snap_ok else 'FAIL'} -- {snap_msg}")

    cross_ok, cross_msg = check_cross_reference(plan, snapshot_lines)
    lines.append(f"3. Snapshot/plan cross-reference spot-check: {'PASS' if cross_ok else 'FAIL'} -- {cross_msg}")

    pre_ok, pre_msg, pre_count = check_pre_count(collection)
    lines.append(f"4. Pre-delete collection.count() == {EXPECTED_PRE_COUNT}: {'PASS' if pre_ok else 'FAIL'} -- {pre_msg}\n")

    all_checks = [plan_ok, snap_ok, cross_ok, pre_ok]

    if not all(all_checks):
        lines.append("**ABORTED -- one or more pre-execute sanity checks failed. `.delete()` was NOT called.**\n")
        lines.append("## Numbers\n")
        lines.append(f"- Pre-count: {pre_count if pre_count >= 0 else 'unknown'}")
        lines.append(f"- Plan count: {len(plan)}")
        lines.append("- Post-count: N/A (delete not attempted)\n")
        report = "\n".join(lines) + "\n"
        out_path = DIAG_DIR / f"targeted_delete_execute_{timestamp}.md"
        out_path.write_text(report, encoding="utf-8")
        print(report)
        print(f"[report written to {out_path}]")
        sys.exit(1)

    # --- Execute: single delete call ---
    lines.append("## Delete call outcome\n")
    try:
        collection.delete(ids=plan)
        delete_ok = True
        lines.append(f"`collection.delete(ids=plan)` succeeded -- {len(plan)} ids submitted.\n")
    except Exception as exc:
        delete_ok = False
        lines.append(f"**`collection.delete(ids=plan)` RAISED AN EXCEPTION: {exc}**")
        lines.append("No retry attempted. Stopping here per the no-retry, no-partial-delete constraint.\n")

    if not delete_ok:
        lines.append("## Numbers\n")
        lines.append(f"- Pre-count: {pre_count}")
        lines.append(f"- Plan count: {len(plan)}")
        lines.append("- Post-count: unknown -- delete call failed, collection state not re-verified\n")
        report = "\n".join(lines) + "\n"
        out_path = DIAG_DIR / f"targeted_delete_execute_{timestamp}.md"
        out_path.write_text(report, encoding="utf-8")
        print(report)
        print(f"[report written to {out_path}]")
        sys.exit(1)

    # --- Post-execute verification ---
    try:
        post_count = collection.count()
    except Exception as exc:
        lines.append(f"**post-delete collection.count() failed: {exc}**\n")
        post_count = -1

    lines.append("## Post-count\n")
    post_ok = post_count == EXPECTED_POST_COUNT
    lines.append(f"- Post-delete collection.count(): **{post_count}**")
    lines.append(
        f"- Expected (from dry-run): {EXPECTED_POST_COUNT} -- "
        f"{'MATCH' if post_ok else 'MISMATCH -- anomaly, see below'}\n"
    )

    rng = random.Random(RANDOM_SEED)
    sample_children = rng.sample(plan, min(SAMPLE_N, len(plan)))
    sample_parent_map = {}
    for cid in sample_children:
        m = SUFFIX_RE.match(cid)
        if m:
            sample_parent_map[cid] = m.group(1)
    sample_parents = sorted(set(sample_parent_map.values()))

    lines.append(f"## Sample verification -- deleted children ({len(sample_children)} sampled, seed={RANDOM_SEED})\n")
    try:
        got_children = collection.get(ids=sample_children, include=[])
        still_present = set(got_children["ids"])
    except Exception as exc:
        lines.append(f"**collection.get(ids=sample_children) failed: {exc}**\n")
        still_present = None

    deleted_check_ok = True
    if still_present is not None:
        anomalies = [cid for cid in sample_children if cid in still_present]
        if anomalies:
            deleted_check_ok = False
            lines.append(f"**ANOMALY: {len(anomalies)} sampled child id(s) still present after delete:**")
            for cid in anomalies:
                lines.append(f"- `{cid}`")
            lines.append("")
        else:
            lines.append(f"All {len(sample_children)} sampled child ids confirmed absent (empty get() result). PASS.\n")
    else:
        deleted_check_ok = False

    lines.append(f"## Sample verification -- preserved parents ({len(sample_parents)} unique parents derived from the sample)\n")
    try:
        got_parents = collection.get(ids=sample_parents, include=[])
        found_parents = set(got_parents["ids"])
    except Exception as exc:
        lines.append(f"**collection.get(ids=sample_parents) failed: {exc}**\n")
        found_parents = None

    parents_check_ok = True
    if found_parents is not None:
        missing = [pid for pid in sample_parents if pid not in found_parents]
        if missing:
            parents_check_ok = False
            lines.append(f"**ANOMALY: {len(missing)} expected parent id(s) missing after delete:**")
            for pid in missing:
                lines.append(f"- `{pid}`")
            lines.append("")
        else:
            lines.append(f"All {len(sample_parents)} sampled parent ids confirmed still present. PASS.\n")
    else:
        parents_check_ok = False

    lines.append("## Numbers\n")
    lines.append(f"- Pre-count: {pre_count}")
    lines.append(f"- Plan count: {len(plan)}")
    lines.append(f"- Post-count: {post_count}\n")

    lines.append("## Anomalies\n")
    any_anomaly = not (post_ok and deleted_check_ok and parents_check_ok)
    if any_anomaly:
        if not post_ok:
            lines.append(f"- Post-count {post_count} did not match expected {EXPECTED_POST_COUNT}.")
        if not deleted_check_ok:
            lines.append("- One or more sampled deleted-children checks failed (see above).")
        if not parents_check_ok:
            lines.append("- One or more sampled parent-preservation checks failed (see above).")
        lines.append(
            "\nRestoration is available via the documented snapshot-upsert command "
            f"(`{SNAPSHOT_PATH.name}`) if these anomalies indicate the delete should be reverted. "
            "Not invoked by this script."
        )
    else:
        lines.append("None. Post-count matched, all sampled deletions confirmed, all sampled parents preserved.")
    lines.append("")

    report = "\n".join(lines) + "\n"
    out_path = DIAG_DIR / f"targeted_delete_execute_{timestamp}.md"
    out_path.write_text(report, encoding="utf-8")
    print(report)
    print(f"[report written to {out_path}]")

    if any_anomaly:
        sys.exit(1)


if __name__ == "__main__":
    main()
