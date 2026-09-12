#!/usr/bin/env python
"""
rebuild_book_embeddings.py
Book-scoped purge and rebuild of a single book's rows in ChromaDB.

Parameterised by --book (exact book_name match). Nothing outside that book is
ever deleted or re-embedded. All intermediate files are book-scoped under
data/recovery/ and data/_backup/ -- the shared corpus-wide files
(data/all_chunks.json, data/chunked_chunks.json, data/pending_chunks.json,
data/embedding_report.json) are never touched.

Steps run individually so a human gate sits between each one:

  0  backup      copy chroma_db, export this book's rows, snapshot all counts
  1  chunk       progress JSON -> chunker.chunk_all -> book-scoped chunk file
  2  sample      embed 5 chunks into a THROWAWAY chroma dir and read them back
  3  purge       collection.delete(where={"book_name": <book>})
  4  rebuild     embedder.run_pipeline over the book-scoped chunk file
  5  verify      counts, metadata distributions, page coverage, one page dump
  6  query       semantic search restricted to this book

Usage:
  python scripts/rebuild_book_embeddings.py --book "BPHS - 1 RSanthanam" \
      --slug bphs1 --step 0
"""

import argparse
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ingestion import chunker, embedder  # noqa: E402

PROGRESS_DIR = REPO_ROOT / "data" / "progress"
RECOVERY_DIR = REPO_ROOT / "data" / "recovery"
BACKUP_DIR = REPO_ROOT / "data" / "_backup"
CHROMA_DIR = REPO_ROOT / "data" / "chroma_db"

FORBIDDEN_PATHS = {
    "data/all_chunks.json",
    "data/chunked_chunks.json",
    "data/pending_chunks.json",
    "data/embedding_report.json",
}


def _slug(book: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", book).strip("_").lower()


class Paths:
    def __init__(self, book: str, slug: str):
        self.book = book
        self.slug = slug
        self.progress = PROGRESS_DIR / f"{book}.json"
        self.chunked = RECOVERY_DIR / f"{slug}_chunked_v1.json"
        self.pending = RECOVERY_DIR / f"{slug}_pending_chunks.json"
        self.report = RECOVERY_DIR / f"{slug}_embedding_report.json"
        self.sample_chunks = RECOVERY_DIR / f"{slug}_sample5_chunked.json"
        self.sample_pending = RECOVERY_DIR / f"{slug}_sample5_pending.json"
        self.sample_report = RECOVERY_DIR / f"{slug}_sample5_report.json"
        self.sample_chroma = RECOVERY_DIR / f"{slug}_sample_chroma"
        self.backup_chroma = BACKUP_DIR / f"chroma_db.pre_{slug}_rebuild"
        self.export = BACKUP_DIR / f"{slug}_chunks_pre_rebuild.json"
        self.counts0 = RECOVERY_DIR / f"{slug}_counts_step0.json"

    def guard(self) -> None:
        """Fail loudly if any output path resolves onto a shared corpus file."""
        outputs = (self.chunked, self.pending, self.report, self.sample_chunks,
                   self.sample_pending, self.sample_report, self.counts0)
        for path in outputs:
            rel = path.relative_to(REPO_ROOT).as_posix()
            if rel in FORBIDDEN_PATHS:
                raise SystemExit(f"REFUSING: output path {rel} is a shared corpus file")


def _dir_bytes(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def _per_book_counts(collection) -> dict:
    metas = collection.get(include=["metadatas"])["metadatas"]
    return dict(sorted(Counter(m.get("book_name") or "<none>" for m in metas).items()))


# --------------------------------------------------------------------------- 0
def step0(p: Paths) -> None:
    print("=== STEP 0 -- BACKUP GATE ===")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    RECOVERY_DIR.mkdir(parents=True, exist_ok=True)

    src_bytes = _dir_bytes(CHROMA_DIR)
    if p.backup_chroma.exists():
        raise SystemExit(f"STOP: backup dir already exists: {p.backup_chroma}")
    shutil.copytree(CHROMA_DIR, p.backup_chroma)
    dst_bytes = _dir_bytes(p.backup_chroma)
    print(f"(a) chroma_db source : {src_bytes:,} bytes")
    print(f"(a) chroma_db backup : {dst_bytes:,} bytes  -> {p.backup_chroma}")
    if dst_bytes != src_bytes:
        raise SystemExit("STOP: backup byte size differs from source")

    collection = embedder.get_collection(str(CHROMA_DIR))
    got = collection.get(where={"book_name": p.book}, include=["documents", "metadatas"])
    rows = [{"id": i, "document": d, "metadata": m}
            for i, d, m in zip(got["ids"], got["documents"], got["metadatas"])]
    p.export.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"(b) exported rows    : {len(rows)}  -> {p.export}")
    if not rows:
        raise SystemExit("STOP: exported 0 rows for this book -- check book_name")

    total = collection.count()
    per_book = _per_book_counts(collection)
    p.counts0.write_text(
        json.dumps({"total": total, "by_book": per_book}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"(c) collection total : {total}")
    print(f"(c) distinct books   : {len(per_book)}")
    for book, n in per_book.items():
        print(f"      {n:>6}  {book}")


# --------------------------------------------------------------------------- 1
def step1(p: Paths) -> None:
    print("=== STEP 1 -- CHUNK ===")
    entries = json.loads(p.progress.read_text(encoding="utf-8"))
    entries = [e for e in entries if e.get("book_name") == p.book]
    print(f"input entries (filtered to book): {len(entries)}")

    out = chunker.chunk_all(entries)
    p.chunked.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"output chunks: {len(out)}  -> {p.chunked}")

    print(f"text_source  : {dict(Counter(c.get('text_source') for c in out))}")
    print(f"content_class: {dict(Counter(c.get('content_class') for c in out))}")

    bad = [c["chunk_id"] for c in out
           if c.get("text_source") is None or c.get("content_class") is None]
    if bad:
        raise SystemExit(
            f"STOP: {len(bad)} chunks carry None text_source/content_class: {bad[:5]}")
    print("passthrough OK -- no None values")

    text_counts = Counter(c.get("text") or "" for c in out)
    repeats = sum(n - 1 for n in text_counts.values() if n > 1)
    print(f"NOTE in-book duplicate-text repeats: {repeats} "
          f"(embedder skips repeats by text_sha256 -- expect embedded rows to fall "
          f"short of the chunk count by at least this margin)")


# --------------------------------------------------------------------------- 2
def step2(p: Paths) -> None:
    print("=== STEP 2 -- SAMPLE BEFORE SCALE (throwaway chroma dir) ===")
    out = json.loads(p.chunked.read_text(encoding="utf-8"))

    def nonempty(chunks):
        return [c for c in chunks if (c.get("text") or "").strip()]

    recovered = nonempty([c for c in out if c.get("text_source") == "tesseract_recovery_v1"
                          and c.get("content_class") == "prose"])
    non_prose = nonempty([c for c in out if c.get("content_class") == "non_prose"])
    original = nonempty([c for c in out if c.get("text_source") == "original_ingest"])

    sample = recovered[:2] + non_prose[:1] + original[:2]
    if len(sample) != 5:
        raise SystemExit(f"STOP: could only assemble {len(sample)} sample chunks")
    for c in sample:
        print(f"  sample: {c['chunk_id']}  page_ref={c['page_ref']} "
              f"text_source={c['text_source']} content_class={c['content_class']}")

    p.sample_chunks.write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8")
    if p.sample_chroma.exists():
        shutil.rmtree(p.sample_chroma)
    p.sample_chroma.mkdir(parents=True)

    rep = embedder.run_pipeline(
        raw_chunks_path=str(p.sample_chunks),
        persist_dir=str(p.sample_chroma),
        pending_path=str(p.sample_pending),
        report_path=str(p.sample_report),
    )
    print(f"sample report: embedded={rep['total_embedded']} pending={rep['total_pending']} "
          f"failed={rep['total_failed']} dup_text={rep['skipped_duplicate_text']} "
          f"collection_count={rep['collection_count']}")

    coll = embedder.get_collection(str(p.sample_chroma))
    got = coll.get(ids=[c["chunk_id"] for c in sample], include=["metadatas"])
    if len(got["ids"]) != 5:
        raise SystemExit(f"STOP: read back {len(got['ids'])}/5 rows")

    ok = True
    for cid, meta in zip(got["ids"], got["metadatas"]):
        print(f"\n  {cid}")
        for k in sorted(meta):
            print(f"      {k}: {meta[k]}")
        if meta.get("text_source") in (None, "", "unknown"):
            ok = False
            print("      !! text_source WRONG")
        if meta.get("content_class") in (None, "", "unknown"):
            ok = False
            print("      !! content_class WRONG")
    if not ok:
        raise SystemExit("STOP: sample metadata wrong -- do not purge")

    print("\nall 5 sample rows carry correct text_source and content_class")
    # Best-effort cleanup: on Windows the Chroma client still holds an open
    # handle on data_level0.bin while this process lives, so removal can fail
    # with PermissionError. The verification above has already passed at this
    # point -- a leftover scratch directory is not a failure of this step.
    shutil.rmtree(p.sample_chroma, ignore_errors=True)
    if p.sample_chroma.exists():
        print(f"NOTE throwaway chroma dir still locked, delete manually: {p.sample_chroma}")
    else:
        print(f"throwaway chroma dir removed: {p.sample_chroma}")


# --------------------------------------------------------------------------- 3
def step3(p: Paths) -> None:
    print("=== STEP 3 -- PURGE ===")
    before = json.loads(p.counts0.read_text(encoding="utf-8"))
    collection = embedder.get_collection(str(CHROMA_DIR))
    collection.delete(where={"book_name": p.book})

    after_total = collection.count()
    after_books = _per_book_counts(collection)
    print(f"{p.book} count now : {after_books.get(p.book, 0)} (expect 0)")
    print(f"collection total   : {before['total']} -> {after_total} "
          f"(delta {after_total - before['total']})")

    collateral = []
    for book, n in before["by_book"].items():
        if book == p.book:
            continue
        now = after_books.get(book, 0)
        if now != n:
            collateral.append((book, n, now))
        print(f"  {n:>6} -> {now:>6}  {book}{'  <-- CHANGED' if now != n else ''}")
    if collateral:
        raise SystemExit(
            f"STOP: collateral damage {collateral} -- restore from {p.backup_chroma}")
    print("no collateral damage")


# --------------------------------------------------------------------------- 4
def step4(p: Paths) -> None:
    print("=== STEP 4 -- REBUILD ===")
    p.guard()
    rep = embedder.run_pipeline(
        raw_chunks_path=str(p.chunked),
        persist_dir=str(CHROMA_DIR),
        pending_path=str(p.pending),
        report_path=str(p.report),
    )
    print(f"sub-chunks in       : {rep['total_sub_chunks']}")
    print(f"embeddable          : {rep['total_embedded']}")
    print(f"pending (empty text): {rep['total_pending']}")
    print(f"failed batches      : {rep['total_failed']}  ids={rep['failed_chunk_ids'][:5]}")
    print(f"skipped dup text    : {rep['skipped_duplicate_text']}")
    print(f"collection total    : {rep['collection_count']}")


# --------------------------------------------------------------------------- 5
def step5(p: Paths, page_dump: int) -> None:
    print("=== STEP 5 -- VERIFY ===")
    before = json.loads(p.counts0.read_text(encoding="utf-8"))
    expected = json.loads(p.chunked.read_text(encoding="utf-8"))
    collection = embedder.get_collection(str(CHROMA_DIR))

    got = collection.get(where={"book_name": p.book}, include=["metadatas"])
    ids, metas = got["ids"], got["metadatas"]
    verdict = "MATCH" if len(ids) == len(expected) else "MISMATCH"
    print(f"(a) rows now={len(ids)}  expected from step 1={len(expected)}  {verdict}")
    if len(ids) != len(expected):
        missing = sorted(set(c["chunk_id"] for c in expected) - set(ids))
        print(f"    missing {len(missing)} ids, first 20: {missing[:20]}")

    after_books = _per_book_counts(collection)
    print("(b) per-book vs step 0:")
    for book, n in before["by_book"].items():
        now = after_books.get(book, 0)
        mark = "" if (book == p.book or now == n) else "  <-- CHANGED"
        print(f"      {n:>6} -> {now:>6}  {book}{mark}")

    print(f"(c) text_source  : {dict(Counter(m.get('text_source') for m in metas))}")
    print(f"(c) content_class: {dict(Counter(m.get('content_class') for m in metas))}")
    print(f"(c) page_type    : {dict(Counter(m.get('page_type') for m in metas))}")

    pages_now = {m.get("page_ref") for m in metas}
    src_entries = [e for e in json.loads(p.progress.read_text(encoding="utf-8"))
                   if e.get("book_name") == p.book]
    recovered_pages = {e["page_ref"] for e in src_entries
                       if e.get("text_source") == "tesseract_recovery_v1"}
    missing_recovered = sorted(recovered_pages - pages_now)
    print(f"(d) distinct page_refs with >=1 chunk: {len(pages_now)} / {len(src_entries)} source pages")
    print(f"(d) recovered page_refs: {len(recovered_pages)}  "
          f"missing: {len(missing_recovered)} {missing_recovered[:20]}")

    print(f"(e) page_ref {page_dump} verbatim:")
    dump = collection.get(
        where={"$and": [{"book_name": p.book}, {"page_ref": page_dump}]},
        include=["documents", "metadatas"],
    )
    if not dump["ids"]:
        print("    NO ROWS")
    for cid, doc, meta in zip(dump["ids"], dump["documents"], dump["metadatas"]):
        print(f"\n    --- {cid} ---")
        print(f"    metadata: {json.dumps(meta, ensure_ascii=False, sort_keys=True)}")
        print("    document:")
        for line in (doc or "").splitlines():
            print(f"      {line}")


# --------------------------------------------------------------------------- 6
def step6(p: Paths, queries: list[str]) -> None:
    print("=== STEP 6 -- SEMANTIC QUERY (book-filtered) ===")
    from openai import OpenAI

    client = OpenAI()
    collection = embedder.get_collection(str(CHROMA_DIR))

    for q in queries:
        emb = client.embeddings.create(model=embedder.EMBEDDING_MODEL, input=[q]).data[0].embedding
        res = collection.query(
            query_embeddings=[emb],
            n_results=3,
            where={"book_name": p.book},
            include=["documents", "metadatas", "distances"],
        )
        print(f"\n--- QUERY: {q!r}")
        for rank, (cid, doc, meta, dist) in enumerate(
                zip(res["ids"][0], res["documents"][0],
                    res["metadatas"][0], res["distances"][0]), start=1):
            snippet = " ".join((doc or "")[:200].split())
            print(f"  {rank}. {cid}  page_ref={meta.get('page_ref')}  "
                  f"text_source={meta.get('text_source')}  cos_dist={dist:.4f}")
            print(f"     {snippet}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", required=True)
    ap.add_argument("--slug", default=None)
    ap.add_argument("--step", required=True, choices=list("0123456"))
    ap.add_argument("--page-dump", type=int, default=204)
    ap.add_argument("--query", action="append", default=[])
    args = ap.parse_args()

    p = Paths(args.book, args.slug or _slug(args.book))
    p.guard()

    dispatch = {
        "0": lambda: step0(p),
        "1": lambda: step1(p),
        "2": lambda: step2(p),
        "3": lambda: step3(p),
        "4": lambda: step4(p),
        "5": lambda: step5(p, args.page_dump),
        "6": lambda: step6(p, args.query),
    }
    dispatch[args.step]()


if __name__ == "__main__":
    main()
