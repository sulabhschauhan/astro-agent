"""
chromadb_dup_diagnostic.py
Read-only diagnostic -- characterizes duplication in the ChromaDB
"astro_chunks" collection across three independent axes ahead of any
dedup re-index. See SESSION_LOG.md Session 22 spike note: retrieval for
"Saturn transit eleventh house effects classical" returned 3 duplicate
pairs in 8 chunks (1=2, 4=5, 6=7), suggesting systematic ingestion-time
duplication rather than a query-time artifact.

READ-ONLY CONTRACT: this script only calls collection.count() and
collection.get(). It never calls add/upsert/update/delete, and makes no
OpenAI calls (existing stored embeddings are read back, nothing is
re-embedded). Safe to run against the live collection at any time.

Axes:
  (a) Exact chunk_id collisions -- same id stored more than once.
  (b) Distinct chunk_ids with byte-identical document text.
  (c) Distinct chunk_ids with near-identical embeddings (cosine > 0.99)
      on a random 500-chunk sample, not full O(n^2) pairwise.

Output: Markdown report printed to stdout and written to
diagnostics/chromadb_dup_report_<timestamp>.md.
"""

import hashlib
import random
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))  # project root, for `ingestion` import

from ingestion.query_engine import CHROMA_DIR, COLLECTION_NAME, get_collection

# Threshold discipline (CLAUDE.md Working Style #4):
# - SAMPLE_SIZE=500: task-specified. Full pairwise at ~11.7k chunks is
#   ~68M comparisons -- 500 keeps axis (c) to a single in-memory matmul
#   (500^2 = 250k). Scope guard: axis (c) characterizes the sample only;
#   do not extrapolate its group counts linearly to the full corpus.
# - SIMILARITY_THRESHOLD=0.99: task-specified, conventional near-duplicate
#   cosine cutoff for OpenAI text-embedding-3-small. Tuning note: identical
#   text embeds deterministically near-identically, so if axis (b) finds
#   exact-text groups whose members land in the axis (c) sample but axis
#   (c) still finds 0 groups, the threshold is not the bottleneck -- the
#   sample/threshold combination needs re-examination before trusting it.
SAMPLE_SIZE = 500
SIMILARITY_THRESHOLD = 0.99
RANDOM_SEED = 22  # fixed for reproducible re-runs of this diagnostic
TOP_BOOKS_SHOWN = 8


class _UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


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
        raise RuntimeError(
            f"collection.count() failed on '{COLLECTION_NAME}': {exc}"
        ) from exc
    if total == 0:
        raise RuntimeError(
            f"Collection '{COLLECTION_NAME}' is empty -- nothing to diagnose. "
            "Run embedder.py first."
        )
    return collection, total


def _fetch_all_ids_docs_meta(collection):
    try:
        result = collection.get(include=["documents", "metadatas"])
    except Exception as exc:
        raise RuntimeError(f"collection.get(documents, metadatas) failed: {exc}") from exc
    return result["ids"], result["documents"], result["metadatas"]


def axis_a_id_collisions(ids: list[str]) -> dict:
    counts = Counter(ids)
    groups = {cid: n for cid, n in counts.items() if n > 1}
    return {"groups": groups, "total_ids": len(ids), "unique_ids": len(counts)}


def axis_b_text_duplicates(documents: list[str]) -> dict:
    by_hash: dict[str, list[int]] = defaultdict(list)
    for i, text in enumerate(documents):
        h = hashlib.sha256((text or "").encode("utf-8")).hexdigest()
        by_hash[h].append(i)
    groups = {h: idxs for h, idxs in by_hash.items() if len(idxs) > 1}
    return {"groups": groups}


def axis_c_embedding_similarity(collection, ids: list[str]) -> dict:
    sample_size = min(SAMPLE_SIZE, len(ids))
    rng = random.Random(RANDOM_SEED)
    sample_ids = rng.sample(ids, sample_size)

    try:
        result = collection.get(
            ids=sample_ids, include=["embeddings", "documents", "metadatas"]
        )
    except Exception as exc:
        raise RuntimeError(
            f"collection.get(embeddings) failed for {sample_size}-chunk sample: {exc}"
        ) from exc

    sampled_ids = result["ids"]
    documents = result["documents"]
    metadatas = result["metadatas"]
    embeddings = np.asarray(result["embeddings"], dtype=np.float64)

    n = len(sampled_ids)
    if n < 2:
        return {
            "sample_size": n, "groups": {}, "pair_count": 0,
            "ids": sampled_ids, "documents": documents, "metadatas": metadatas,
        }

    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1e-12  # defensive: a zero embedding would otherwise NaN out cosine sim
    normalized = embeddings / norms
    sim_matrix = normalized @ normalized.T

    uf = _UnionFind(n)
    iu, ju = np.triu_indices(n, k=1)
    sims = sim_matrix[iu, ju]
    above = sims > SIMILARITY_THRESHOLD
    pair_count = int(above.sum())
    for i, j in zip(iu[above], ju[above]):
        uf.union(int(i), int(j))

    components: dict[int, list[int]] = defaultdict(list)
    for idx in range(n):
        components[uf.find(idx)].append(idx)
    groups = {root: members for root, members in components.items() if len(members) > 1}

    return {
        "sample_size": n, "groups": groups, "pair_count": pair_count,
        "ids": sampled_ids, "documents": documents, "metadatas": metadatas,
    }


def _book_distribution(indices, metadatas) -> list[tuple[str, int]]:
    counts = Counter((metadatas[i].get("book_name") or "(missing)") for i in indices)
    return counts.most_common(TOP_BOOKS_SHOWN)


def _group_size_histogram(groups: dict) -> list[tuple[int, int]]:
    sizes = Counter(len(members) for members in groups.values())
    return sorted(sizes.items())


def _example_block(indices, ids, documents, metadatas) -> str:
    i = indices[0]
    chunk_ids = ", ".join(ids[k] for k in indices[:6])
    if len(indices) > 6:
        chunk_ids += f", ... (+{len(indices) - 6} more)"
    meta = metadatas[i]
    snippet = (documents[i] or "")[:200].replace("\n", " ")
    return (
        f"- chunk_ids: {chunk_ids}\n"
        f"- book_name: {meta.get('book_name', '')}\n"
        f"- page_ref: {meta.get('page_ref', '')}\n"
        f"- text (first 200 chars):\n```\n{snippet}\n```"
    )


def build_report(total, ids, documents, metadatas, a, b, c) -> str:
    lines = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines.append("# ChromaDB Duplication Diagnostic -- astro_chunks\n")
    lines.append(f"**Generated:** {now}  ")
    lines.append(f"**Collection:** `{COLLECTION_NAME}` @ `{CHROMA_DIR}`  ")
    lines.append(f"**Total chunks in collection:** {total}  ")
    lines.append(
        "**Read-only run** -- no writes, deletes, or re-embeds performed by this script.\n"
    )

    if total > 9000:  # CLAUDE.md documents ~7,281 chunks across 14 books
        lines.append(
            f"> Note: collection count ({total}) is well above the ~7,281 chunks "
            "documented in CLAUDE.md's RAG corpus description. That gap is itself "
            "consistent with systematic duplicate ingestion and is worth carrying "
            "into fix-design discussion, not just the per-axis group counts below.\n"
        )

    # --- Axis (a) ---
    lines.append("## Axis (a): Exact chunk_id collisions\n")
    lines.append(f"- Total id entries returned: {a['total_ids']}")
    lines.append(f"- Unique ids: {a['unique_ids']}")
    lines.append(f"- Colliding id groups: {len(a['groups'])}\n")
    if a["groups"]:
        worst_id, worst_n = max(a["groups"].items(), key=lambda kv: kv[1])
        lines.append(f"Representative: id `{worst_id}` stored {worst_n} times.\n")
    else:
        lines.append(
            "No id stored more than once. Consistent with Chroma enforcing id "
            "uniqueness as primary key, and `embedder.py` using `.upsert()` "
            "(overwrites on existing id rather than duplicating).\n"
        )

    # --- Axis (b) ---
    lines.append("## Axis (b): Byte-identical text across distinct chunk_ids\n")
    b_groups = b["groups"]
    b_affected = sum(len(idxs) for idxs in b_groups.values())
    lines.append(f"- Duplicate-text groups: {len(b_groups)}")
    lines.append(f"- Chunks involved: {b_affected} ({b_affected / total:.1%} of collection)")
    if b_groups:
        hist = _group_size_histogram(b_groups)
        hist_str = ", ".join(f"{n} group(s) of size {size}" for size, n in hist)
        lines.append(f"- Group-size histogram: {hist_str}")
        all_b_indices = [i for idxs in b_groups.values() for i in idxs]
        dist = _book_distribution(all_b_indices, metadatas)
        lines.append("- Source book distribution (duplicate-involved chunks):")
        for book, n in dist:
            lines.append(f"  - {book}: {n}")
        lines.append("")
        largest = max(b_groups.values(), key=len)
        lines.append("Representative example (largest group):\n")
        lines.append(_example_block(largest, ids, documents, metadatas) + "\n")
    else:
        lines.append("No byte-identical text duplicates found across distinct chunk_ids.\n")

    # --- Axis (c) ---
    lines.append(
        f"## Axis (c): Near-identical embeddings, sampled "
        f"(n={c['sample_size']}/{total}, cosine > {SIMILARITY_THRESHOLD})\n"
    )
    c_groups = c["groups"]
    c_affected = sum(len(idxs) for idxs in c_groups.values())
    lines.append(f"- Sample size: {c['sample_size']} (seed={RANDOM_SEED})")
    lines.append(f"- Pairs above threshold: {c['pair_count']}")
    lines.append(f"- Duplicate-embedding groups (connected components): {len(c_groups)}")
    lines.append(f"- Sampled chunks involved: {c_affected}")
    if c_groups:
        hist = _group_size_histogram(c_groups)
        hist_str = ", ".join(f"{n} group(s) of size {size}" for size, n in hist)
        lines.append(f"- Group-size histogram: {hist_str}")
        all_c_indices = [i for idxs in c_groups.values() for i in idxs]
        dist = _book_distribution(all_c_indices, c["metadatas"])
        lines.append("- Source book distribution (duplicate-involved sampled chunks):")
        for book, n in dist:
            lines.append(f"  - {book}: {n}")
        lines.append("")
        largest = max(c_groups.values(), key=len)
        lines.append("Representative example (largest group):\n")
        lines.append(
            _example_block(largest, c["ids"], c["documents"], c["metadatas"]) + "\n"
        )
    else:
        lines.append(
            "No near-identical embedding pairs found in the sample at this threshold.\n"
        )

    # --- Scope notes ---
    lines.append("## Scope notes\n")
    lines.append(
        f"- Axis (c) is a {c['sample_size']}-of-{total} random sample "
        f"(seed={RANDOM_SEED}), not full pairwise -- do not extrapolate its "
        "group counts linearly to the full corpus."
    )
    lines.append(
        "- Axes are independent and may overlap (e.g. a byte-identical-text pair "
        "is expected to also show near-identical embeddings if both members "
        "happen to land in the axis (c) sample)."
    )
    lines.append(
        "- No fix is proposed in this report. Findings are reported as observed "
        "for Session 23 fix-design (chunk_id collision logic vs. embedder "
        "re-run vs. source page double-ingest)."
    )

    return "\n".join(lines) + "\n"


def main():
    collection, total = _open_collection()
    ids, documents, metadatas = _fetch_all_ids_docs_meta(collection)

    a = axis_a_id_collisions(ids)
    b = axis_b_text_duplicates(documents)
    c = axis_c_embedding_similarity(collection, ids)

    report = build_report(total, ids, documents, metadatas, a, b, c)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = Path(__file__).parent / f"chromadb_dup_report_{timestamp}.md"
    out_path.write_text(report, encoding="utf-8")

    print(report)
    print(f"[written to {out_path}]")


if __name__ == "__main__":
    main()
