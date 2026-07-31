"""
scripts/dump_fateline_retrieval.py
Read-only diagnostic dump for the "fate line" feature's retrieval path.

No production code touched, no writes, no ChromaDB mutation. Every function
called below is imported directly from agent.interpretive.palm_reading /
ingestion.query_engine -- nothing here reimplements parsing, quality
resolution, query building, or retrieval. The one unavoidable network call
is search()'s own OpenAI EMBEDDING call (needed to replicate the real
retrieval path); no chat/completions (LLM) call is made anywhere in this
script.

Three sections, printed in order:
  1. The exact query the pipeline builds for observation
     "FATE LINE: Barely visible." (via _parse_fields -> _gather_feature_texts
     -> _resolve_feature_quality -> _build_feature_query).
  2. Every chunk that query retrieves via the SAME one-call-per-feature path
     production uses (_search_with_page_filter, page-range gate ON),
     chunk_id/page/score/full untruncated text.
  3. Every chunk that exists in the fate-line verified page range
     (_FEATURE_PAGE_RANGES["fate line"]), fetched DIRECTLY via
     collection.get() -- independent of query wording or ranking --
     so absence of "barely visible line of fate" doctrine (if any) can be
     distinguished as a CORPUS gap vs. a RETRIEVAL/ranking gap.
"""

from __future__ import annotations

from agent.interpretive.palm_reading import (
    _CHEIRO_BOOK,
    _FEATURE_PAGE_RANGES,
    _build_feature_query,
    _gather_feature_texts,
    _parse_fields,
    _resolve_feature_quality,
    _search_with_page_filter,
)
from ingestion.query_engine import _build_where, get_collection

FEATURE = "fate line"
OBSERVATION_BLOCK = "FATE LINE: Barely visible."


def main() -> None:
    print("=" * 80)
    print("1. QUERY CONSTRUCTION")
    print("=" * 80)
    print(f"observation block: {OBSERVATION_BLOCK!r}")

    left_fields = _parse_fields(OBSERVATION_BLOCK)
    print(f"_parse_fields(...) -> {left_fields!r}")

    texts_by_feature = _gather_feature_texts(left_fields, {}, {})
    raw_texts = texts_by_feature[FEATURE]
    print(f"_gather_feature_texts(...)[{FEATURE!r}] -> {raw_texts!r}")

    quality = _resolve_feature_quality(FEATURE, raw_texts)
    print(f"_resolve_feature_quality({FEATURE!r}, {raw_texts!r}) -> {quality!r}")

    query = None
    if quality is None:
        print("query: None -- feature would be SKIPPED (no search call made in production)")
    else:
        query = _build_feature_query(FEATURE, quality)
        print(f"_build_feature_query({FEATURE!r}, {quality!r}) -> {query!r}")

    print()
    print("=" * 80)
    print("2. RETRIEVED CHUNKS (_search_with_page_filter, page-range gate ON, full text)")
    print("=" * 80)
    if query is None:
        print("(skipped -- no query)")
    else:
        sliced, _full_candidates = _search_with_page_filter(FEATURE, query)
        if not sliced:
            print("(empty result set -- zero chunks in-range for this query)")
        for i, r in enumerate(sliced, 1):
            print(f"--- rank {i} ---")
            print(f"chunk_id: {r['chunk_id']}")
            print(f"page_ref: {r['page_ref']}")
            print(f"score:    {r['score']}")
            print("text:")
            print(r["text"])
            print()

    print("=" * 80)
    print("3. ALL CHUNKS IN fate-line PAGE RANGE (direct fetch, no embedding query)")
    print("=" * 80)
    page_range = _FEATURE_PAGE_RANGES.get(FEATURE)
    print(f"_FEATURE_PAGE_RANGES[{FEATURE!r}] = {page_range}")
    if page_range is None:
        print("(no verified range -- nothing to fetch)")
    else:
        start, end = page_range
        where = _build_where({"book_name": _CHEIRO_BOOK, "page_ref": (start, end)})
        collection = get_collection()
        raw = collection.get(where=where, include=["documents", "metadatas"])
        rows = sorted(
            zip(raw["ids"], raw["documents"], raw["metadatas"]),
            key=lambda t: (t[2].get("page_ref", 0), t[0]),
        )
        print(f"{len(rows)} chunk(s) found in range {start}-{end}:")
        for chunk_id, text, meta in rows:
            print(f"--- {chunk_id} (page {meta.get('page_ref')}) ---")
            print(text)
            print()


if __name__ == "__main__":
    main()
