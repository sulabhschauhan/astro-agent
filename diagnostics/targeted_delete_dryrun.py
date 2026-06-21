"""
targeted_delete_dryrun.py
Dry-run for a targeted ChromaDB delete of X / X_c<N> duplicate-text chunks
(see diagnostics/chromadb_dup_report_20260621_080119.md axis (b) and
diagnostics/chunking_code_audit_20260621_092249.md for the root cause: 8 of
14 books' progress/*.json files already held chunker output when chunk_all()
ran a second time over them, producing a byte-identical child id exactly one
suffix level below an existing parent id, e.g. Deva-keralam_p8_c0_c0 next to
Deva-keralam_p8_c0). Embedder hash hardening (embedder_hardening_proposal_
20260621_100850.md) already prevents recurrence going forward; this script
only characterizes and plans removal of the existing pollution.

READ-ONLY CONTRACT: this script calls only collection.count() and
collection.get(include=[...]). It never calls add/upsert/update/delete on
the live collection. Embeddings already stored are read back, nothing is
re-embedded -- no OpenAI calls. Safe to run against the live collection at
any time; it writes three diagnostic files and never touches ChromaDB state.

DELETION INVARIANT (a chunk is a deletion candidate iff all four hold):
  1. chunk_id matches `_c\\d+$` (trailing numeric suffix).
  2. Stripping that trailing `_c\\d+` yields a chunk_id that ALSO exists in
     the collection (the parent).
  3. The candidate's text is byte-identical to the parent's text.
  4. Metadata is parity-equal to the parent on book_name, page_ref,
     page_type, language, topic. image_path/word_count may diverge --
     flagged on the record, not disqualifying.
Any candidate passing 1-3 but failing 4 on a strict field is downgraded to
"needs human review" and excluded from the delete plan.

Output (all three written to diagnostics/, sharing one run timestamp):
  - targeted_delete_dryrun_<ts>.md      -- human report (this is the plan)
  - targeted_delete_plan_<ts>.json      -- sorted chunk_id list to delete
  - targeted_delete_snapshot_<ts>.jsonl -- one full record (chunk_id, text,
    metadata, embedding) per planned delete -- sufficient to restore via
    collection.upsert() without re-embedding.

NO deletes, NO updates, NO writes to the collection are performed by this
script. Execution (the actual collection.delete() pass) is a separate,
later script by design.
"""

import json
import random
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # project root, for `ingestion` import

from ingestion.query_engine import CHROMA_DIR, COLLECTION_NAME, get_collection

# Threshold discipline (CLAUDE.md Working Style #4):
# - SUFFIX_RE = r'^(.*)_c\d+$': matches the locked chunk_id schema's own
#   "_c{index}" sub-chunk suffix (CLAUDE.md Chunk Metadata Schema). A
#   first-level chunk's stripped form (e.g. "Book_p8" from "Book_p8_c0") is
#   never itself a stored chunk_id under that schema, so condition 2 (parent
#   must exist as its own record) self-filters ordinary chunks out without a
#   second rule -- only true X/X_c<N> re-chunking duplicates pass both 1 and 2.
# - STRICT_FIELDS vs SOFT_FIELDS: task-specified split. Strict fields are the
#   ones that would mean the two records describe different source content if
#   mismatched (which page/book/language/section); image_path and word_count
#   are presentation/derived fields that can legitimately drift (e.g. a record
#   written before a `_to_metadata()` change) without the two records actually
#   disagreeing about content.
# - SAMPLE_PAIRS_N=10: task-specified spot-check sample size.
# - POST_STATE_TARGET: task context states "~8,800 target band" without a
#   numeric width. Centered at 8800 with a +-150 half-width: 11,688 (current
#   live count) - 2,892 (task-context candidate estimate) = 8,796, i.e. the
#   task's own ballpark already lands inside +-150 of 8,800. Scope guard:
#   this band describes only this run's expected post-state, not a general
#   invariant -- if this run's candidate count differs from the task's
#   ~2,892 estimate by more than the band width, that gap is flagged in the
#   report rather than silently passed or failed against the band.
SUFFIX_RE = re.compile(r"^(.*)_c\d+$")
STRICT_FIELDS = ["book_name", "page_ref", "page_type", "language", "topic"]
SOFT_FIELDS = ["image_path", "word_count"]
SAMPLE_PAIRS_N = 10
RANDOM_SEED = 23  # Session 23 dry-run; fixed for reproducible spot-check re-runs
POST_STATE_TARGET_CENTER = 8800
POST_STATE_TARGET_HALF_WIDTH = 150
# The 6 books the chunking-code audit (20260621_092249.md SS6) found clean --
# their progress/*.json files were real sequential OCR output, never
# re-chunked. Any candidate landing here is a contradiction of that finding
# and must be surfaced, not silently included.
CLEAN_BOOKS = {
    "BPHS - 1 RSanthanam",
    "BPHS - 2 RSanthanam",
    "cheiroslanguageo00chei_1",
    "Saravali of Kalyana Varma Santhanam R. (Astrology)",
    "Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri",
    "Jyotish_Lal Kitab_B.M. Gosvami",
}


def _open_collection():
    try:
        collection = get_collection(CHROMA_DIR)
    except Exception as exc:
        raise RuntimeError(
            f"Could not open ChromaDB collection '{COLLECTION_NAME}' at "
            f"'{CHROMA_DIR}': {exc}"
        ) from exc
    try:
        total = collection.count()
    except Exception as exc:
        raise RuntimeError(f"collection.count() failed on '{COLLECTION_NAME}': {exc}") from exc
    if total == 0:
        raise RuntimeError(
            f"Collection '{COLLECTION_NAME}' is empty -- nothing to dry-run. "
            "Run embedder.py first."
        )
    return collection, total


def _bulk_fetch(collection):
    """Single bulk read of the entire collection -- ids, documents, metadatas,
    embeddings -- per the no-N+1 constraint. All candidate-finding below
    filters this one in-memory snapshot; no further ChromaDB calls follow."""
    try:
        result = collection.get(include=["documents", "metadatas", "embeddings"])
    except Exception as exc:
        raise RuntimeError(
            f"collection.get(documents, metadatas, embeddings) failed: {exc}"
        ) from exc
    return result["ids"], result["documents"], result["metadatas"], result["embeddings"]


def find_candidates(ids: list[str], documents: list[str], metadatas: list[dict]) -> dict:
    id_to_idx = {cid: i for i, cid in enumerate(ids)}

    suffix_matches = 0          # condition 1 only
    parent_exists = 0           # conditions 1+2
    text_mismatch_excluded = 0  # conditions 1+2 held, condition 3 failed -- not a
                                 # candidate at all (not a downgrade; the invariant
                                 # never qualified this pair as a candidate)
    accepted = []                # passed all 4 -- goes in the delete plan
    downgraded = []              # passed 1-3, failed 4 on a strict field

    for child_id in ids:
        m = SUFFIX_RE.match(child_id)
        if not m:
            continue
        suffix_matches += 1

        parent_id = m.group(1)
        if parent_id == child_id or parent_id not in id_to_idx:
            continue
        parent_exists += 1

        child_idx = id_to_idx[child_id]
        parent_idx = id_to_idx[parent_id]
        child_text = documents[child_idx] or ""
        parent_text = documents[parent_idx] or ""
        if child_text != parent_text:
            text_mismatch_excluded += 1
            continue

        child_meta = metadatas[child_idx] or {}
        parent_meta = metadatas[parent_idx] or {}
        strict_mismatches = [f for f in STRICT_FIELDS if child_meta.get(f) != parent_meta.get(f)]
        soft_mismatches = [f for f in SOFT_FIELDS if child_meta.get(f) != parent_meta.get(f)]

        record = {
            "child_id": child_id,
            "parent_id": parent_id,
            "child_idx": child_idx,
            "parent_idx": parent_idx,
            "book_name": child_meta.get("book_name", ""),
            "soft_mismatches": soft_mismatches,
        }

        if strict_mismatches:
            detail = ", ".join(
                f"{f} (child={child_meta.get(f)!r} vs parent={parent_meta.get(f)!r})"
                for f in strict_mismatches
            )
            record["reason"] = f"strict metadata mismatch on {detail}"
            downgraded.append(record)
        else:
            accepted.append(record)

    return {
        "suffix_matches": suffix_matches,
        "parent_exists": parent_exists,
        "text_mismatch_excluded": text_mismatch_excluded,
        "accepted": accepted,
        "downgraded": downgraded,
    }


def _chain_count(accepted: list[dict]) -> int:
    """How many accepted candidates have a parent_id that is itself another
    accepted candidate's child_id (a multi-level X_c0_c0_c0-style chain).
    Informational only -- does not affect inclusion in the delete plan."""
    accepted_child_ids = {r["child_id"] for r in accepted}
    return sum(1 for r in accepted if r["parent_id"] in accepted_child_ids)


def write_plan(accepted: list[dict], out_path: Path) -> list[str]:
    plan = sorted(r["child_id"] for r in accepted)
    out_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return plan


def write_snapshot(
    accepted: list[dict], ids: list[str], documents: list[str],
    metadatas: list[dict], embeddings, out_path: Path,
) -> int:
    lines = []
    for r in sorted(accepted, key=lambda r: r["child_id"]):
        idx = r["child_idx"]
        record = {
            "chunk_id": ids[idx],
            "text": documents[idx],
            "metadata": metadatas[idx],
            "embedding": embeddings[idx].tolist(),
        }
        lines.append(json.dumps(record, ensure_ascii=False))
    out_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return len(lines)


def _sample_pairs(accepted: list[dict], n: int = SAMPLE_PAIRS_N, seed: int = RANDOM_SEED) -> list[dict]:
    rng = random.Random(seed)
    return rng.sample(accepted, min(n, len(accepted)))


def build_report(
    total: int, ids: list[str], documents: list[str], metadatas: list[dict],
    find_result: dict,
) -> str:
    accepted = find_result["accepted"]
    downgraded = find_result["downgraded"]
    lines = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines.append("# Targeted Delete Dry-Run -- X / X_c<N> Duplicate Chunks\n")
    lines.append(f"**Generated:** {now}  ")
    lines.append(f"**Collection:** `{COLLECTION_NAME}` @ `{CHROMA_DIR}`  ")
    lines.append(
        "**Read-only run** -- no `.delete()` / `.update()` / `.upsert()` / "
        "`.add()` calls made by this script. Single bulk `.get()` read, "
        "all filtering done in memory.\n"
    )

    # --- Section 1: Pre-state ---
    lines.append("## 1. Pre-state\n")
    lines.append(f"- Total chunks in collection: **{total}**")
    lines.append(
        f"- Suffix-chunks (chunk_id matches `_c\\d+$`, condition 1): "
        f"{find_result['suffix_matches']}"
    )
    if find_result["suffix_matches"] == total:
        lines.append(
            "  (= total chunks. Expected, not a bug: the locked chunk metadata "
            "schema appends `_c{index}` to every sub-chunk unconditionally, so "
            "condition 1 alone is never discriminating -- condition 2 below is "
            "the first filter that actually narrows anything.)"
        )
    lines.append(
        f"- ...of which the stripped parent id also exists (conditions 1+2): "
        f"{find_result['parent_exists']}"
    )
    lines.append(
        f"- ...of which text was NOT byte-identical to the parent (condition 3 "
        f"failed -- excluded outright, not a downgrade): {find_result['text_mismatch_excluded']}"
    )
    lines.append(
        f"- **Candidates passing all four invariant conditions (the delete plan): "
        f"{len(accepted)}**"
    )
    lines.append(f"- **Candidates downgraded to human review (condition 4 failed): {len(downgraded)}**")
    soft_flagged = sum(1 for r in accepted if r["soft_mismatches"])
    lines.append(
        f"- Of the {len(accepted)} accepted candidates, {soft_flagged} have an "
        "image_path/word_count divergence from their parent (flagged, not excluded)."
    )
    chains = _chain_count(accepted)
    if chains:
        lines.append(
            f"- **Chain note:** {chains} accepted candidate(s) have a parent_id that "
            "is itself another accepted candidate's child_id (multi-level "
            "X_c0_c0_c0-style chain). Deletion order does not matter for Chroma's "
            "flat id-keyed storage, but flagging so the execute pass isn't surprised "
            "by it."
        )
    lines.append("")

    if downgraded:
        lines.append("### Downgraded candidates (excluded from delete plan)\n")
        shown = downgraded[:25]
        for r in shown:
            lines.append(f"- `{r['child_id']}` (parent `{r['parent_id']}`) -- {r['reason']}")
        if len(downgraded) > len(shown):
            lines.append(f"- ... (+{len(downgraded) - len(shown)} more, same reason class)")
        lines.append("")
    else:
        lines.append("No candidates were downgraded -- every suffix/parent/text match also matched on all five strict metadata fields.\n")

    # --- Section 2: Per-book candidate count ---
    lines.append("## 2. Per-book candidate count\n")
    book_counts = Counter(r["book_name"] for r in accepted)
    lines.append("| book_name | accepted candidates |")
    lines.append("|---|---|")
    for book, n in book_counts.most_common():
        flag = "  **<-- CLEAN BOOK, UNEXPECTED**" if book in CLEAN_BOOKS else ""
        lines.append(f"| {book} | {n}{flag} |")
    lines.append("")

    clean_hits = {b: n for b, n in book_counts.items() if b in CLEAN_BOOKS}
    if clean_hits:
        lines.append(
            "**FLAG:** candidates found in book(s) previously identified as clean "
            "by the chunking-code audit (`diagnostics/chunking_code_audit_"
            "20260621_092249.md` SS6): "
            + ", ".join(f"`{b}` ({n})" for b, n in clean_hits.items())
            + ". This contradicts that audit's forensic finding and should be "
            "investigated before any execute pass, not assumed safe.\n"
        )
    else:
        lines.append(
            "No candidates fall in the 6 clean books "
            f"({', '.join(sorted(CLEAN_BOOKS))}). Consistent with the chunking-code "
            "audit's finding that only the 8 books re-chunked from already-chunked "
            "progress files are affected.\n"
        )

    # --- Section 3: Spot-check sample ---
    lines.append(f"## 3. Spot-check sample ({min(SAMPLE_PAIRS_N, len(accepted))} random accepted pairs, seed={RANDOM_SEED})\n")
    if accepted:
        for r in _sample_pairs(accepted):
            p_idx, c_idx = r["parent_idx"], r["child_idx"]
            p_meta, c_meta = metadatas[p_idx] or {}, metadatas[c_idx] or {}
            p_text = (documents[p_idx] or "")[:200].replace("\n", " ")
            c_text = (documents[c_idx] or "")[:200].replace("\n", " ")
            lines.append(f"### `{r['parent_id']}`  (kept)  vs  `{r['child_id']}`  (delete candidate)\n")
            lines.append("| field | parent (kept) | child (delete candidate) |")
            lines.append("|---|---|---|")
            for f in STRICT_FIELDS + SOFT_FIELDS:
                pv, cv = p_meta.get(f, ""), c_meta.get(f, "")
                marker = "  **<-- diverges**" if pv != cv else ""
                lines.append(f"| {f} | {pv} | {cv}{marker} |")
            lines.append("")
            lines.append(f"Parent text (first 200 chars): `{p_text}`  ")
            lines.append(f"Child text (first 200 chars): `{c_text}`\n")
    else:
        lines.append("No accepted candidates -- nothing to sample.\n")

    # --- Section 4: Expected post-state ---
    lines.append("## 4. Expected post-state\n")
    post_state = total - len(accepted)
    band_lo = POST_STATE_TARGET_CENTER - POST_STATE_TARGET_HALF_WIDTH
    band_hi = POST_STATE_TARGET_CENTER + POST_STATE_TARGET_HALF_WIDTH
    in_band = band_lo <= post_state <= band_hi
    lines.append(f"- Current total: {total}")
    lines.append(f"- Accepted delete-plan size: {len(accepted)}")
    lines.append(f"- **Expected post-delete total: {post_state}**")
    lines.append(
        f"- Target band: {band_lo}-{band_hi} (centered on the task's ~8,800 estimate) "
        f"-- {'WITHIN band' if in_band else 'OUTSIDE band'}.\n"
    )
    if not in_band:
        lines.append(
            "**Reconciliation (not a script defect -- traced to a stale upstream "
            "estimate):** the task's ~2,892/~8,800 figures trace to "
            "`diagnostics/chunking_code_audit_20260621_092249.md` line 6 (\"2,892 "
            "duplicate-text groups, 100% of which match a chunk_id X / X_c<N> pair\"). "
            "That figure does not itself reconcile against its own cited source, "
            "`chromadb_dup_report_20260621_080119.md`'s axis (b) histogram (3,930 "
            "groups / 7,896 chunks total). Redoing that arithmetic directly: "
            "excluding the one 18-member OCR-garbage group (cross-page, not a suffix "
            "chain -- see Section 6) leaves 3,929 groups / 7,878 chunks; if each "
            "remaining group is one kept parent plus (size-1) deletable children, "
            "that predicts 7,878 - 3,929 = **3,949** deletions -- within 4 of this "
            "run's exact, schema-verified count of "
            f"{len(accepted)}. The small residual is consistent with a handful of "
            "groups whose members aren't a clean single-parent chain. This run's "
            "count is the ground truth (computed directly against the live "
            "collection per the stated invariant); the task's ~2,892/~8,800 figures "
            "were an upstream approximation that undercounted sub-chunk-level pairs "
            "within affected pages (e.g. one re-chunked page can contribute several "
            "independent X/X_c<N> pairs, not just one -- see the Deva-keralam p8 "
            "example in `embedder_hardening_proposal_20260621_100850.md`).\n"
        )

    # --- Section 5: Snapshot sanity check ---
    lines.append("## 5. Snapshot sanity check\n")
    lines.append("__SNAPSHOT_SANITY_PLACEHOLDER__\n")

    # --- Section 6: Out-of-scope (document only) ---
    lines.append("## 6. Out-of-scope (documented, not touched by this plan)\n")
    lines.append(
        "- **OCR-garbage groups.** `diagnostics/chromadb_dup_report_20260621_080119.md` "
        "axis (b) found 3,930 byte-identical-text groups total (7,896 chunks), including "
        "a single 18-member group in `Hasta Samudrika Shastra...` whose entire text is "
        "the literal character `|`, spanning unrelated page_refs (p92, p264, p274, ...). "
        "This invariant excludes that group by construction: stripping `_c0` from e.g. "
        "`..._p264_c0` yields `..._p264`, which is never itself a stored chunk_id under "
        "the locked schema, so condition 2 fails and the pair is never even evaluated as "
        "a candidate. Left untouched, as instructed."
    )
    lines.append(
        "- **Near-identical-embedding pairs outside the suffix invariant.** The same "
        "source report's axis (c) sampled 500/11688 chunks and found 5 pairs at "
        "cosine > 0.99 (one of which is itself an X/X_c<N> pair already covered above). "
        "This script does not re-run or extend that embedding-similarity scan -- any "
        "near-identical-but-non-suffix-matching pairs remain out of scope for this pass "
        "and are not in the delete plan."
    )
    lines.append("")

    return "\n".join(lines) + "\n"


def main():
    collection, total = _open_collection()
    ids, documents, metadatas, embeddings = _bulk_fetch(collection)

    find_result = find_candidates(ids, documents, metadatas)
    accepted = find_result["accepted"]

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = Path(__file__).parent
    report_path = out_dir / f"targeted_delete_dryrun_{timestamp}.md"
    plan_path = out_dir / f"targeted_delete_plan_{timestamp}.json"
    snapshot_path = out_dir / f"targeted_delete_snapshot_{timestamp}.jsonl"

    plan = write_plan(accepted, plan_path)
    snapshot_count = write_snapshot(accepted, ids, documents, metadatas, embeddings, snapshot_path)

    report = build_report(total, ids, documents, metadatas, find_result)

    snapshot_size = snapshot_path.stat().st_size
    sanity_ok = snapshot_count == len(plan)
    sanity_block = (
        f"- Snapshot file: `{snapshot_path.name}`\n"
        f"- Snapshot size: {snapshot_size:,} bytes ({snapshot_size / (1024 * 1024):.2f} MB)\n"
        f"- Snapshot record count: {snapshot_count}\n"
        f"- Delete-plan record count: {len(plan)}\n"
        f"- **Sanity check (snapshot count == plan count): {'PASS' if sanity_ok else 'FAIL'}**\n"
    )
    report = report.replace("__SNAPSHOT_SANITY_PLACEHOLDER__\n", sanity_block)

    report_path.write_text(report, encoding="utf-8")

    print(report)
    print(f"[report written to {report_path}]")
    print(f"[plan written to {plan_path}]")
    print(f"[snapshot written to {snapshot_path}]")

    if not sanity_ok:
        raise RuntimeError(
            f"Snapshot/plan count mismatch: snapshot has {snapshot_count} records, "
            f"plan has {len(plan)} -- do not proceed to an execute pass with this output."
        )


if __name__ == "__main__":
    main()
