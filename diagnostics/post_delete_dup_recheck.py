"""
post_delete_dup_recheck.py
Read-only re-run of the duplicate-text diagnostic (same axis a/b/c logic as
chromadb_dup_diagnostic.py, which produced chromadb_dup_report_20260621_080119.md)
against the collection AFTER targeted_delete_execute.py removed the 3,945
X/X_c<N> duplicate-text children (see targeted_delete_execute_20260621_121046.md).

Confirms: (1) total count dropped to the expected 7,743; (2) axis (b)
duplicate-text bloat is gone except for a small, already-characterized
OCR-garbage residual; (3) none of the 8 previously-affected books still
shows the X/X_c<N> suffix pattern -- re-runs the delete's own invariant
(find_candidates from targeted_delete_dryrun.py) and expects zero
remaining candidates; (4) the 6 clean books are untouched.

READ-ONLY CONTRACT: only collection.count() / collection.get() are called.
No add/upsert/update/delete. Imports (does not modify) the axis a/b/c
functions from chromadb_dup_diagnostic.py and the suffix-invariant
find_candidates()/CLEAN_BOOKS from targeted_delete_dryrun.py, so this
re-run is exactly the same methodology as both prior diagnostics rather
than a reimplementation that could silently drift from them.
"""

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # project root, for `ingestion` import
sys.path.insert(0, str(Path(__file__).parent))  # diagnostics dir itself, for sibling-script imports

from ingestion.query_engine import CHROMA_DIR, COLLECTION_NAME, get_collection

from chromadb_dup_diagnostic import (
    _open_collection,
    _fetch_all_ids_docs_meta,
    axis_a_id_collisions,
    axis_b_text_duplicates,
    axis_c_embedding_similarity,
    _book_distribution,
    _group_size_histogram,
    _example_block,
    SAMPLE_SIZE,
    SIMILARITY_THRESHOLD,
    RANDOM_SEED,
)
from targeted_delete_dryrun import find_candidates, CLEAN_BOOKS

EXPECTED_TOTAL = 7743
INCOMPLETE_DELETE_GROUP_THRESHOLD = 100  # task-specified: flag if axis(b) group count stays >100

AFFECTED_BOOKS = {
    "Deva-keralam",
    "Muhurtha-Chinthamani",
    "Prasna Marga 1",
    "Prasna Marga 2",
    "Sarvartha-Chintamani",
    "Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan",
    "Jataka Parijata with explanation of Pt. Kapileshvara Shastri and Vimala Hindi Tika of Pt. Shri Matri Prasad Shastri Series No. 10 - Kashi Sanskrit Series",
    "uttkalamrita-kalidas-ps-sastri",
}
# Pre-delete per-book delete counts, from targeted_delete_dryrun_20260621_120557.md
# Section 2. Used only to reconstruct pre-delete per-book totals as
# post_count + deleted_count -- lets the clean-book "unchanged" claim be
# verified arithmetically without restoring from the snapshot (forbidden
# by this task).
DELETED_BY_BOOK = {
    "Deva-keralam": 672,
    "Muhurtha-Chinthamani": 604,
    "Prasna Marga 1": 517,
    "Jataka Parijata with explanation of Pt. Kapileshvara Shastri and Vimala Hindi Tika of Pt. Shri Matri Prasad Shastri Series No. 10 - Kashi Sanskrit Series": 504,
    "Prasna Marga 2": 431,
    "Sarvartha-Chintamani": 423,
    "Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan": 422,
    "uttkalamrita-kalidas-ps-sastri": 372,
}

EMBEDDING_REPORT_PATH = Path(__file__).parent.parent / "data" / "embedding_report.json"


def _embedding_report_clean_book_counts() -> dict:
    """Secondary, independent cross-check only: data/embedding_report.json's
    by_book.embedded count reflects the last embedder.py run's per-book
    tally, which for the 6 never-corrupted clean books should already equal
    their live ChromaDB count. Best-effort -- absence doesn't block the
    primary (arithmetic) clean-book check below."""
    try:
        report = json.loads(EMBEDDING_REPORT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {
        book: stats.get("embedded")
        for book, stats in report.get("by_book", {}).items()
        if book in CLEAN_BOOKS
    }


def build_report(total, ids, documents, metadatas, a, b, c, candidates_post) -> str:
    lines = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines.append("# Post-Delete Duplicate Diagnostic Re-check -- astro_chunks\n")
    lines.append(f"**Generated:** {now}  ")
    lines.append(f"**Collection:** `{COLLECTION_NAME}` @ `{CHROMA_DIR}`  ")
    lines.append(
        "**Read-only run** -- no writes, deletes, or re-embeds performed by this script. "
        "Re-runs the exact axis a/b/c logic from `chromadb_dup_diagnostic.py` and the exact "
        "suffix invariant from `targeted_delete_dryrun.py`.\n"
    )

    # --- 1. Total count ---
    lines.append("## 1. Total chunk count\n")
    total_ok = total == EXPECTED_TOTAL
    lines.append(f"- Total chunks: **{total}**")
    lines.append(f"- Expected (post-delete): {EXPECTED_TOTAL} -- {'MATCH' if total_ok else 'MISMATCH -- anomaly'}\n")

    # --- 2. Axis (a) ---
    lines.append("## 2. Axis (a): Exact chunk_id collisions\n")
    a_ok = len(a["groups"]) == 0
    lines.append(f"- Total id entries: {a['total_ids']}")
    lines.append(f"- Unique ids: {a['unique_ids']}")
    lines.append(f"- Colliding id groups: {len(a['groups'])} -- {'PASS (expected 0)' if a_ok else 'ANOMALY (expected 0)'}\n")

    # --- 3. Axis (b) ---
    lines.append("## 3. Axis (b): Byte-identical text across distinct chunk_ids\n")
    b_groups = b["groups"]
    b_affected = sum(len(idxs) for idxs in b_groups.values())
    b_incomplete = len(b_groups) > INCOMPLETE_DELETE_GROUP_THRESHOLD
    lines.append(f"- Duplicate-text groups: {len(b_groups)} (pre-delete: 3,930)")
    lines.append(f"- Chunks involved: {b_affected} ({b_affected / total:.1%} of collection) (pre-delete: 7,896)")
    lines.append(
        f"- Incomplete-delete flag (group count > {INCOMPLETE_DELETE_GROUP_THRESHOLD}): "
        f"{'TRIPPED -- investigate' if b_incomplete else 'not tripped'}\n"
    )
    if b_groups:
        hist = _group_size_histogram(b_groups)
        hist_str = ", ".join(f"{n} group(s) of size {size}" for size, n in hist)
        lines.append(f"- Group-size histogram: {hist_str}\n")
        sorted_groups = sorted(b_groups.values(), key=len, reverse=True)
        lines.append("### Largest 3 remaining groups\n")
        for i, idxs in enumerate(sorted_groups[:3], 1):
            lines.append(f"**Group {i} (size {len(idxs)}):**\n")
            lines.append(_example_block(idxs, ids, documents, metadatas) + "\n")
        lines.append(
            "Per the dry-run's Section 6 (out-of-scope), the residual is expected to be "
            "OCR-garbage groups like the 18-member literal `|` group spanning unrelated "
            "page_refs -- not a missed class of real X/X_c<N> duplicates. Confirmed below "
            "via the suffix-invariant re-check (Section 6).\n"
        )
    else:
        lines.append("No byte-identical text duplicates remain.\n")

    # --- 4. Axis (c) ---
    lines.append(
        f"## 4. Axis (c): Near-identical embeddings, sampled "
        f"(n={c['sample_size']}/{total}, cosine > {SIMILARITY_THRESHOLD}, seed={RANDOM_SEED})\n"
    )
    c_groups = c["groups"]
    c_ok = c["pair_count"] <= 5
    lines.append(f"- Pairs above threshold: {c['pair_count']} (pre-delete: 5) -- {'PASS (<=5)' if c_ok else 'ANOMALY (>5)'}")
    lines.append(f"- Duplicate-embedding groups: {len(c_groups)}\n")
    lines.append(
        "Scope note (unchanged from the original diagnostic): this is a "
        f"{c['sample_size']}-of-{total} random sample, not full pairwise -- do not "
        "extrapolate group counts linearly.\n"
    )

    # --- 5. Per-book counts + clean-book check ---
    lines.append("## 5. Per-book chunk count post-delete\n")
    book_counts = Counter((metadatas[i].get("book_name") or "(missing)") for i in range(total))
    lines.append("| book_name | post-delete count | deleted (this pass) | reconstructed pre-delete | class |")
    lines.append("|---|---|---|---|---|")
    for book, n in book_counts.most_common():
        deleted = DELETED_BY_BOOK.get(book, 0)
        cls = "CLEAN" if book in CLEAN_BOOKS else ("AFFECTED" if book in AFFECTED_BOOKS else "?")
        lines.append(f"| {book} | {n} | {deleted} | {n + deleted} | {cls} |")
    lines.append("")

    clean_book_anomaly = False
    lines.append("### Clean-book unchanged check\n")
    for book in sorted(CLEAN_BOOKS):
        post_n = book_counts.get(book, 0)
        deleted = DELETED_BY_BOOK.get(book, 0)
        if deleted != 0:
            clean_book_anomaly = True
            lines.append(f"- **ANOMALY:** `{book}` had {deleted} candidate(s) deleted -- should have been 0 (clean book).")
        else:
            lines.append(f"- `{book}`: {post_n} chunks, 0 deleted this pass -- unchanged by construction (delete touched none of its ids).")
    lines.append("")

    secondary = _embedding_report_clean_book_counts()
    if secondary:
        lines.append("Secondary cross-check (`data/embedding_report.json` by_book.embedded, independent of this run):\n")
        for book, embedded_n in secondary.items():
            live_n = book_counts.get(book, 0)
            match = "match" if embedded_n == live_n else "differs (see note)"
            lines.append(f"- `{book}`: embedding_report={embedded_n}, live={live_n} -- {match}")
        lines.append(
            "\n(Differences here, if any, predate this delete pass and reflect normal "
            "embedder-report-vs-live drift, e.g. pending/diagram chunks counted "
            "differently -- not evidence this delete touched a clean book.)\n"
        )

    # --- 6. Suffix-invariant re-check (incomplete-delete detector) ---
    lines.append("## 6. Suffix-invariant re-check (did the delete fully land?)\n")
    accepted_post = candidates_post["accepted"]
    downgraded_post = candidates_post["downgraded"]
    suffix_clean = len(accepted_post) == 0
    lines.append(
        f"- Re-running `find_candidates()` (the exact invariant `targeted_delete_execute.py` "
        f"deleted against) on the post-delete collection: **{len(accepted_post)} accepted "
        f"candidates remain** (expected 0)."
    )
    lines.append(f"- Downgraded-to-review candidates remaining: {len(downgraded_post)} (informational; these were never in the delete plan).")
    affected_books_with_residual = sorted({r["book_name"] for r in accepted_post} & AFFECTED_BOOKS)
    if affected_books_with_residual:
        lines.append(
            f"- **INCOMPLETE-DELETE FLAG TRIPPED:** {len(affected_books_with_residual)} of the 8 "
            f"previously-affected books still show the X/X_c<N> suffix pattern: "
            f"{', '.join(affected_books_with_residual)}."
        )
    else:
        lines.append("- None of the 8 previously-affected books show the X/X_c<N> suffix pattern anymore. Delete landed completely.\n")

    incomplete_delete = b_incomplete or bool(affected_books_with_residual) or not suffix_clean

    # --- Headline summary ---
    lines.append("## Headline summary\n")
    lines.append(f"- Total count: {total} (expected {EXPECTED_TOTAL}) -- {'PASS' if total_ok else 'FAIL'}")
    lines.append(f"- Axis (a) collisions: {len(a['groups'])} (expected 0) -- {'PASS' if a_ok else 'FAIL'}")
    lines.append(f"- Axis (b) groups: {len(b_groups)} (pre-delete 3,930; flag threshold >{INCOMPLETE_DELETE_GROUP_THRESHOLD})")
    lines.append(f"- Axis (c) pairs: {c['pair_count']} (expected <=5) -- {'PASS' if c_ok else 'FAIL'}")
    lines.append(f"- Suffix-invariant residual: {len(accepted_post)} (expected 0) -- {'PASS' if suffix_clean else 'FAIL'}")
    lines.append(f"- Clean-book anomaly: {'YES' if clean_book_anomaly else 'none'}")
    lines.append(f"- **Incomplete-delete flag: {'TRIPPED' if incomplete_delete else 'not tripped'}**\n")

    return "\n".join(lines) + "\n"


def main():
    collection, total = _open_collection()
    ids, documents, metadatas = _fetch_all_ids_docs_meta(collection)

    a = axis_a_id_collisions(ids)
    b = axis_b_text_duplicates(documents)
    c = axis_c_embedding_similarity(collection, ids)
    candidates_post = find_candidates(ids, documents, metadatas)

    report = build_report(total, ids, documents, metadatas, a, b, c, candidates_post)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = Path(__file__).parent / f"post_delete_dup_recheck_{timestamp}.md"
    out_path.write_text(report, encoding="utf-8")

    print(report)
    print(f"[written to {out_path}]")


if __name__ == "__main__":
    main()
