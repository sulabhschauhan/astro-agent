"""
scripts/probe_fc_heartline_corpus.py

S68 F-C heart-line corpus lookup (diagnostics-only, throwaway,
read-only). Measure-first: reports what is found, asserts nothing,
proposes no fixes.

Purpose: scripts/probe_fc_retrieval.py's evidence found ZERO occurrences
of "below the first finger" / "mount of jupiter" needles across all 12
top-10 embedding-retrieval runs for the heart-line feature. That is
retrieval-layer evidence -- it does not by itself distinguish "the
doctrine isn't in the corpus at all" from "the doctrine is in the
corpus but embedding retrieval never surfaces it." This script answers
the corpus-existence question directly: a deterministic ChromaDB
METADATA lookup (`collection.get(where=...)`, no embedding call, no
`ingestion.query_engine.search()`) for every chunk whose `page_ref` in
`cheiroslanguageo00chei_1` falls in [156, 162] -- Cheiro's heart-line
chapter region, per the page numbers cited in pass 3's ledger and
probe_fc_retrieval.py's top-10 lists (p.159-161 chunks appear
repeatedly there).

Does NOT touch agent/interpretive/palm_reading.py, does not modify
ingestion, does not run any embedding query, and does not propose any
fix -- data only.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.query_engine import get_collection

_REPORT_PATH = Path(__file__).resolve().parent.parent / "diagnostics" / "fc_heartline_corpus_S68.md"
_BOOK_NAME = "cheiroslanguageo00chei_1"
_PAGE_LOW = 156
_PAGE_HIGH = 162

# Literal substring flags (case-insensitive, NOT word-boundary) -- same
# accepted-deviation precedent as palm_reading.py's _chunk_supports_feature
# (chunk-side text is OCR-scanned and unreliable at the word level, so
# permissive substring matching is the correct-direction choice there;
# same reasoning applies to this lookup).
_NEEDLES: tuple[str, ...] = (
    "first finger",
    "jupiter",
    "below the",
    # OCR-tolerant variants, per the task's own examples
    "finst",
    "fnger",
    "inpiter",
)


def _flags_for(text: str) -> list[str]:
    low = text.lower()
    return [n for n in _NEEDLES if n in low]


def _whitespace_normalized_flags_for(text: str) -> list[str]:
    """Same needles, but collapses all whitespace (including embedded
    newlines from the source PDF's line-wrapping, preserved verbatim in
    chunk text) to single spaces first. A companion check only -- the
    primary `_flags_for` above is the literal, as-instructed lookup;
    this one exists because a real case was found during this probe
    (p159_c2's "...the first\\nfinger." -- the phrase IS in the corpus
    but a newline mid-substring defeats the strict literal check)."""
    normalized = " ".join(text.split())
    return _flags_for(normalized)


def main() -> None:
    collection = get_collection()

    where = {
        "$and": [
            {"book_name": {"$eq": _BOOK_NAME}},
            {"page_ref": {"$gte": _PAGE_LOW}},
            {"page_ref": {"$lte": _PAGE_HIGH}},
        ]
    }
    result = collection.get(where=where, include=["documents", "metadatas"])

    ids = result["ids"]
    docs = result["documents"]
    metas = result["metadatas"]

    # Sort by (page_ref, chunk_id) for a stable, readable report -- collection.get()
    # does not guarantee page-ascending order.
    rows = sorted(
        zip(ids, docs, metas), key=lambda r: (r[2].get("page_ref", 0), r[0])
    )

    lines: list[str] = []
    lines.append("# F-C heart-line corpus lookup (S68)")
    lines.append("")
    lines.append(
        "Diagnostics-only, throwaway, read-only (`scripts/probe_fc_heartline_corpus.py`). "
        "Deterministic ChromaDB METADATA lookup via `collection.get(where=...)` -- "
        "NOT an embedding query, NOT `ingestion.query_engine.search()`. Measure-first: "
        "reports what is found, asserts nothing, proposes no fixes."
    )
    lines.append("")
    lines.append(
        f"Filter: `book_name == \"{_BOOK_NAME}\"` AND `{_PAGE_LOW} <= page_ref <= "
        f"{_PAGE_HIGH}` (Cheiro's heart-line chapter region, per the page numbers "
        "cited in pass 3's ledger and `probe_fc_retrieval.py`'s top-10 lists)."
    )
    lines.append("")
    lines.append(f"**{len(rows)} chunks matched.**")
    lines.append("")

    if not rows:
        lines.append("## Zero chunks in range -- nearest populated page_refs")
        lines.append("")
        all_pages = sorted(
            {
                m.get("page_ref", 0)
                for m in collection.get(
                    where={"book_name": {"$eq": _BOOK_NAME}}, include=["metadatas"]
                )["metadatas"]
            }
        )
        below = [p for p in all_pages if p < _PAGE_LOW]
        above = [p for p in all_pages if p > _PAGE_HIGH]
        nearest_below = below[-3:] if below else []
        nearest_above = above[:3] if above else []
        lines.append(f"- Nearest populated pages below {_PAGE_LOW}: {nearest_below}")
        lines.append(f"- Nearest populated pages above {_PAGE_HIGH}: {nearest_above}")
        lines.append("")
    else:
        pages_present = sorted({m.get("page_ref", 0) for _, _, m in rows})
        pages_missing = [
            p for p in range(_PAGE_LOW, _PAGE_HIGH + 1) if p not in pages_present
        ]
        lines.append(f"Pages with at least one chunk: {pages_present}")
        lines.append(
            f"Pages in range with ZERO chunks (chunking-gap evidence, not "
            f"interpreted further): {pages_missing if pages_missing else 'none'}"
        )
        lines.append("")

        lines.append("## Full chunk dump (verbatim, OCR garbling preserved)")
        lines.append("")
        flag_map: dict[str, list[str]] = {}
        ws_flag_map: dict[str, list[str]] = {}
        for chunk_id, text, meta in rows:
            page = meta.get("page_ref", 0)
            flags = _flags_for(text)
            ws_flags = _whitespace_normalized_flags_for(text)
            flag_map[chunk_id] = flags
            ws_flag_map[chunk_id] = ws_flags
            lines.append(f"### `{chunk_id}` (p.{page})")
            lines.append("")
            lines.append("```")
            lines.append(text)
            lines.append("```")
            lines.append(f"Flags (literal): {', '.join(flags) if flags else '(none)'}")
            extra_ws = [f for f in ws_flags if f not in flags]
            if extra_ws:
                lines.append(
                    f"Flags (whitespace-normalized only, NOT caught by the literal "
                    f"check -- see note below): {', '.join(extra_ws)}"
                )
            lines.append("")

        lines.append("## Summary table: chunk_id x flags")
        lines.append("")
        lines.append(
            "`(literal)` columns are the exact as-instructed substring check. "
            "`ws-extra` lists any needle that ONLY matches after collapsing "
            "embedded whitespace/newlines (see note below the table)."
        )
        lines.append("")
        header = ["chunk_id", "page_ref"] + list(_NEEDLES) + ["ws-extra"]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "---|" * len(header))
        for chunk_id, text, meta in rows:
            page = meta.get("page_ref", 0)
            flags = flag_map[chunk_id]
            ws_extra = [f for f in ws_flag_map[chunk_id] if f not in flags]
            row = [f"`{chunk_id}`", str(page)] + [
                "x" if n in flags else "" for n in _NEEDLES
            ] + [", ".join(ws_extra) if ws_extra else ""]
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")

        total_with_any_flag = sum(1 for f in flag_map.values() if f)
        total_with_ws_extra = sum(
            1 for cid in flag_map if any(f not in flag_map[cid] for f in ws_flag_map[cid])
        )
        lines.append(
            f"**{total_with_any_flag}/{len(rows)} chunks in range have at least "
            "one literal flag hit.**"
        )
        if total_with_ws_extra:
            lines.append(
                f"**{total_with_ws_extra} additional chunk(s) match a needle only "
                "after whitespace normalization** -- see note below."
            )
        lines.append("")

        if total_with_ws_extra:
            lines.append("## Note: literal-vs-whitespace-normalized discrepancy")
            lines.append("")
            lines.append(
                "The exact-as-instructed literal substring check (`\"first finger\" "
                "in text.lower()`) is defeated when the source PDF's own line-wrap "
                "puts a newline between the two words. Observed case: "
                "`cheiroslanguageo00chei_1_p159_c2`'s chunk text contains "
                "`\"...reaching the base of the first\\nfinger.\"` (verified via "
                "`repr()` against the live collection) -- the phrase \"first finger\" "
                "genuinely exists in this chunk's source sentence, but the literal "
                "check reports no hit because of the embedded newline. Reported here "
                "as a fact about this lookup's methodology, not a proposed fix to "
                "the needle list or the chunking pipeline."
            )
            lines.append("")

    _REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report written to {_REPORT_PATH} ({len(rows)} chunks)")


if __name__ == "__main__":
    main()
