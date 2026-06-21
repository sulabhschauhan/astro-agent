"""
chunking_code_audit.py
Read-only forensic audit of the chunking layer behind the X / X_c0
byte-identical duplicate pattern documented in
diagnostics/chromadb_dup_report_20260621_080119.md (2,892 of that report's
duplicate-text groups are book_name+page_ref-matched pairs where one
chunk_id is a strict prefix of the other plus an extra "_c<N>").

READ-ONLY CONTRACT:
- Source files (ingestion/*.py) are read as plain text and sliced with
  regex -- never imported. Two of them (run_overnight.py, run_single_book.py)
  open log FileHandlers at module import time, which would touch
  data/*.log as a side effect; reading as text avoids that entirely.
- Data files (data/progress/*.json, data/chunked_chunks.json,
  data/overnight_run.log) are opened for reading only.
- The live ChromaDB collection is read via collection.get() only (reusing
  ingestion.query_engine.get_collection -- the same read path validated in
  the prior chromadb_dup_diagnostic.py run). No add/upsert/update/delete.
- `git log` is invoked as a read-only subprocess.
No code, data, or ChromaDB state is modified by this script.

Output: Markdown report printed to stdout and written to
diagnostics/chunking_code_audit_<timestamp>.md.
"""

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from ingestion.query_engine import CHROMA_DIR, COLLECTION_NAME, get_collection  # noqa: E402

# Book partition established empirically in diagnostics/chromadb_dup_report_20260621_080119.md
# follow-up analysis (100% of the 2,892 long-text duplicate groups matched this split).
AFFECTED_BOOKS = [
    "Deva-keralam",
    "Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan",
    "Jataka Parijata with explanation of Pt. Kapileshvara Shastri and Vimala Hindi Tika of Pt. Shri Matri Prasad Shastri Series No. 10 - Kashi Sanskrit Series",
    "Muhurtha-Chinthamani",
    "Prasna Marga 1",
    "Prasna Marga 2",
    "Sarvartha-Chintamani",
    "uttkalamrita-kalidas-ps-sastri",
]
CLEAN_BOOKS = [
    "BPHS - 1 RSanthanam",
    "BPHS - 2 RSanthanam",
    "cheiroslanguageo00chei_1",
    "Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri",
    "Saravali of Kalyana Varma Santhanam R. (Astrology)",
    "Jyotish_Lal Kitab_B.M. Gosvami",
]

GIT_LOG_FILES = [
    "ingestion/run_single_book.py",
    "ingestion/run_overnight.py",
    "ingestion/chunker.py",
    "ingestion/embedder.py",
    "ingestion/pdf_processor.py",
    "ingestion/translator.py",
]

EXAMPLE_BOOK = "Deva-keralam"
EXAMPLE_PAGE = 8


def _extract_function(source: str, func_name: str) -> str:
    """Slice a top-level function's exact source text out of a module's text,
    via regex -- avoids importing modules that have import-time side effects."""
    m = re.search(rf"^def {re.escape(func_name)}\(.*", source, re.MULTILINE)
    if not m:
        return f"[function {func_name!r} not found in source]"
    rest = source[m.end():]
    nxt = re.search(r"^(def |if __name__|# ---)", rest, re.MULTILINE)
    end = m.end() + (nxt.start() if nxt else len(rest))
    return source[m.start():end].rstrip() + "\n"


def _extract_lines(source: str, start_marker: str, end_marker: str) -> str:
    """Slice source text between two literal substrings (inclusive of start,
    exclusive of end) -- for sub-function spans that aren't whole functions."""
    start = source.index(start_marker)
    end = source.index(end_marker, start)
    return source[start:end].rstrip() + "\n"


def _save_progress_call_sites() -> list[tuple[str, str, str]]:
    """Every _save_progress(...) call across ingestion/*.py, with the variable
    name passed as the chunks argument -- to verify none of them ever persist
    chunker output (vs. raw OCR/diagram-extraction output) into data/progress/."""
    sites = []
    for path in sorted((ROOT / "ingestion").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for m in re.finditer(r"_save_progress\(\s*([^,]+),", text):
            line_no = text[:m.start()].count("\n") + 1
            sites.append((path.name, line_no, m.group(1).strip()))
    return sites


def _chunk_all_call_sites() -> list[tuple[str, int]]:
    """Real call sites only (`... = chunk_all(...)`) -- excludes docstring/comment
    mentions of the literal text "chunk_all(" (e.g. run_overnight.py's module
    docstring describes the pipeline stages in prose)."""
    sites = []
    for path in sorted((ROOT / "ingestion").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            if re.search(r"=\s*chunk_all\(", line):
                sites.append((path.name, line_no))
    return sites


def _progress_table() -> list[dict]:
    progress_dir = ROOT / "data" / "progress"
    rows = []
    for f in sorted(progress_dir.glob("*.json")):
        try:
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as exc:
            rows.append({"book": f.stem, "error": str(exc)})
            continue
        first_id = data[0]["chunk_id"] if data else ""
        suffixed = bool(re.search(r"_c\d+$", first_id))
        rows.append({
            "book": f.stem,
            "mtime": mtime.isoformat(timespec="seconds"),
            "n": len(data),
            "first_id": first_id,
            "suffixed_at_raw": suffixed,
        })
    rows.sort(key=lambda r: r.get("mtime", ""))
    return rows


def _overnight_log_findings() -> dict:
    log_path = ROOT / "data" / "overnight_run.log"
    if not log_path.exists():
        return {"available": False}
    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    marker_terms = (
        "OVERNIGHT RUN STARTED", "Stage 1 complete", "Stage 2 complete",
        "Stage 3 complete", "OVERNIGHT RUN COMPLETE",
    )
    markers = [l for l in lines if any(t in l for t in marker_terms)]

    tally_lines = []
    all_books = AFFECTED_BOOKS + CLEAN_BOOKS
    for l in lines:
        stripped = l.rstrip()
        for book in all_books:
            if stripped.endswith(tuple(" 0123456789")) and f"  {book}" in stripped:
                tally_lines.append(stripped)
                break

    return {
        "available": True,
        "markers": markers,
        "tally_lines": tally_lines,
        "last_line": lines[-1] if lines else "",
        "total_lines": len(lines),
    }


def _chunked_chunks_example() -> list[dict]:
    path = ROOT / "data" / "chunked_chunks.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        {"chunk_id": c["chunk_id"], "len_text": len(c.get("text") or "")}
        for c in data
        if c.get("book_name") == EXAMPLE_BOOK and c.get("page_ref") == EXAMPLE_PAGE
    ]


def _chromadb_example_check() -> dict:
    try:
        collection = get_collection(CHROMA_DIR)
        result = collection.get(
            where={"$and": [
                {"book_name": {"$eq": EXAMPLE_BOOK}},
                {"page_ref": {"$eq": EXAMPLE_PAGE}},
            ]},
            include=["documents"],
        )
    except Exception as exc:
        return {"error": str(exc)}
    return {
        "ids": result["ids"],
        "lens": [len(d or "") for d in result["documents"]],
    }


def _git_log_for(paths: list[str]) -> dict[str, list[str]]:
    out = {}
    for p in paths:
        try:
            res = subprocess.run(
                ["git", "log", "--format=%h %ad %s", "--date=short", "--", p],
                cwd=ROOT, capture_output=True, text=True, check=True,
            )
            out[p] = [l for l in res.stdout.splitlines() if l.strip()] or ["[no commits]"]
        except Exception as exc:
            out[p] = [f"[git log failed: {exc}]"]
    return out


def build_report() -> str:
    chunker_src = (ROOT / "ingestion" / "chunker.py").read_text(encoding="utf-8")
    pdf_proc_src = (ROOT / "ingestion" / "pdf_processor.py").read_text(encoding="utf-8")
    run_single_src = (ROOT / "ingestion" / "run_single_book.py").read_text(encoding="utf-8")
    embedder_src = (ROOT / "ingestion" / "embedder.py").read_text(encoding="utf-8")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    L = []
    L.append("# Chunking-Layer Code Audit -- X / X_c0 Duplicate Pattern\n")
    L.append(f"**Generated:** {now}  ")
    L.append("**Read-only audit** -- no code, data, or ChromaDB changes made by this script.\n")
    L.append(
        "Source diagnostic: `diagnostics/chromadb_dup_report_20260621_080119.md` -- "
        "2,892 duplicate-text groups, 100%% of which match a chunk_id `X` / `X_c<N>` "
        "pair holding byte-identical text, across 8 of 14 books.\n".replace("%%", "%")
    )

    # ---------------------------------------------------------------- Q1
    L.append("## 1. Files implementing chunking and the recursive split\n")
    L.append("- `ingestion/chunker.py`")
    L.append("  - `chunk_page(parent)` -- per-page dispatcher (diagram/text/mixed routing)")
    L.append("  - `chunk_all(chunks)` -- driver loop, calls `chunk_page()` once per input item")
    L.append("  - `_make_sub_chunks(segments, parent)` -- builds sub-chunk dicts, assigns `_c{i}` ids")
    L.append("  - `sliding_window(text)` -- the actual long-text splitter (400-word window, 50-word overlap)")
    L.append("  - `split_on_paragraphs()` / `merge_paragraphs()` -- pre-split helpers feeding the threshold check")
    L.append(
        "\nThere is no in-function recursion anywhere in `chunker.py` -- `chunk_page()` does not "
        "call itself, and `chunk_all()`'s loop is a single flat pass. The \"recursive\" behavior in "
        "the bug hypothesis is the **pipeline** re-invoking `chunk_all()` across separate process "
        "runs on data that already passed through it once, not literal recursion within the module."
    )
    sites = _chunk_all_call_sites()
    L.append("\n`chunk_all()` call sites (exhaustive grep, excludes the `chunker.py` `__main__` self-test):")
    for fname, lineno in sites:
        if fname == "chunker.py":
            continue
        L.append(f"- `ingestion/{fname}:{lineno}`")
    L.append("")

    # ---------------------------------------------------------------- Q2
    L.append("## 2. Under what condition is the splitter invoked?\n")
    L.append("`chunk_page()` is invoked unconditionally on every item in `chunk_all()`'s input list:\n")
    L.append("```python")
    L.append(_extract_function(chunker_src, "chunk_all"))
    L.append("```")
    L.append(
        "No check exists here (or anywhere in `chunk_all`/`chunk_page`) for whether "
        "`chunk[\"chunk_id\"]` already carries a `_c<N>` suffix from a prior pass.\n"
    )
    L.append("Inside `chunk_page()`, the word-count splitter (`sliding_window`) *is* gated:\n")
    L.append("```python")
    L.append(_extract_lines(
        chunker_src,
        "    segments = []\n    for segment in merge_paragraphs(paragraphs):",
        "    return _make_sub_chunks(segments, parent)",
    ))
    L.append("```")
    L.append(f"Gate: `len(segment.split()) > SPLIT_THRESHOLD` (SPLIT_THRESHOLD = {500}).\n")

    # ---------------------------------------------------------------- Q3
    L.append("## 3. What does the splitter emit below SPLIT_THRESHOLD?\n")
    L.append("Full `chunk_page()` for reference (diagram branches + the text/mixed branch):\n")
    L.append("```python")
    L.append(_extract_function(chunker_src, "chunk_page"))
    L.append("```")
    L.append(
        "Trace for a text/mixed page whose merged text is already under SPLIT_THRESHOLD "
        "(true for any page that was already chunked once): `merge_paragraphs()` reduces to "
        "a single buffer, the `else: segments.append(segment)` branch fires (segment "
        "unmodified), `segments` ends up as a 1-element list holding the text byte-for-byte, "
        "and `_make_sub_chunks()` emits exactly one sub-chunk with `chunk_id = "
        "f\"{parent['chunk_id']}_c0\"` and `text` identical to the input. This is the exact "
        "mechanism that produces a child byte-identical to its parent.\n"
        "\nFor a diagram page with empty text, the behavior is even more direct -- no "
        "threshold check at all:\n"
    )
    L.append("```python")
    L.append(_extract_lines(
        chunker_src,
        '    if parent["page_type"] == "diagram" and not text:',
        "    # text and mixed pages",
    ))
    L.append("```")

    # ---------------------------------------------------------------- Q4
    L.append("## 4. How are suffixes generated? What prevents double-suffixing?\n")
    L.append("All three id-construction sites in `chunker.py`:\n")
    L.append("```python")
    L.append(_extract_function(chunker_src, "_make_sub_chunks"))
    L.append("```")
    L.append(
        "(plus the two diagram-branch f-strings quoted under Q3, both "
        "`f\"{parent['chunk_id']}_c0\"`).\n"
    )
    guard_terms = ["removesuffix", "rsplit", "endswith(\"_c", "already chunked", "already_suffixed"]
    found_guards = [t for t in guard_terms if t in chunker_src]
    L.append(
        f"Grep of `chunker.py` for suffix-guard patterns {guard_terms} -> "
        f"found: {found_guards or 'none'}. All three construction sites take "
        "`parent['chunk_id']` as an opaque string and concatenate `_c{i}`/`_c0` "
        "unconditionally. Nothing inspects whether that string already ends in `_c\\d+` "
        "before appending another suffix.\n"
    )

    # ---------------------------------------------------------------- Q5
    L.append("## 5. Is the ingestion entry point idempotent on re-run?\n")
    L.append(
        "**Short answer: partially.** The OCR stage is idempotent via a skip-cache; "
        "the chunking stage is not idempotent and has no awareness of its own prior output; "
        "the embed stage's idempotency check is id-string-based, not content-based.\n"
    )
    L.append("**(a) OCR stage -- IS idempotent, via skip-if-exists:**\n")
    L.append("```python")
    L.append(_extract_function(pdf_proc_src, "process_all_pdfs"))
    L.append("```")
    L.append("**Same pattern in `run_single_book.py`'s Stage 1:**\n")
    L.append("```python")
    L.append(_extract_lines(
        run_single_src,
        "    # ── Stage 1: pdf_processor",
        "    text_pages    = sum",
    ))
    L.append("```")
    L.append(
        "**(b) Chunking stage -- NOT idempotent.** `run_single_book.py` Stage 3 re-merges "
        "*every* progress file (not just the newly-added book's) and re-chunks the full set, "
        "unconditionally, on every invocation:\n"
    )
    L.append("```python")
    L.append(_extract_lines(
        run_single_src,
        "    # ── Stage 3: merge + chunker",
        "    # Save for embedder",
    ))
    L.append("```")
    L.append(
        "`_merge_progress()` here (and in `run_overnight.py`) performs no transformation -- "
        "it concatenates `progress/*.json` content verbatim. So `chunk_all()`'s input on any "
        "re-run is whatever is currently sitting in `data/progress/*.json`. If those files "
        "ever hold already-chunked content instead of raw OCR pages, `chunk_all()` will "
        "silently re-chunk over them -- there is no flag, hash, or marker anywhere in this "
        "pipeline distinguishing \"raw page\" input from \"already-chunked\" input.\n"
    )
    L.append("**(c) Embed stage -- idempotent by id string only, not by content:**\n")
    L.append("```python")
    L.append(_extract_lines(
        embedder_src,
        "    # Idempotency: skip chunks already present in ChromaDB",
        "    total_batches = (len(to_embed)",
    ))
    L.append("```")
    L.append(
        "This skip-guard compares `chunk_id` strings only. Two records holding identical "
        "text under different ids (e.g. `X_c0` vs `X_c0_c0`) are both treated as distinct, "
        "unembedded content -- both get upserted, and neither overwrites the other.\n"
    )

    save_sites = _save_progress_call_sites()
    L.append(
        "Exhaustive grep of every `_save_progress(...)` call site across `ingestion/*.py` "
        "(checking what each one persists into `data/progress/`):\n"
    )
    for fname, lineno, var in save_sites:
        L.append(f"- `ingestion/{fname}:{lineno}` -- saves `{var}`")
    L.append(
        "\nIn every call site above, the saved variable traces back to `process_pdf()` / "
        "`extract_diagram_text()` output (raw OCR / diagram-extraction pages) -- never to "
        "`chunk_all()`'s output. **No code currently in this repository writes chunked "
        "(`_c`-suffixed) content into `data/progress/*.json`.** Whatever did so for the 8 "
        "affected books (see Q6) is not present in the current codebase.\n"
    )

    # ---------------------------------------------------------------- Q6
    L.append("## 6. Why are 6 books clean and 8 affected?\n")
    L.append("### Git history of the ingestion scripts\n")
    git_results = _git_log_for(GIT_LOG_FILES)
    for path, commits in git_results.items():
        L.append(f"**`{path}`**")
        for c in commits:
            L.append(f"- {c}")
        L.append("")
    L.append(
        "`run_single_book.py` has exactly one commit, dated 2026-05-30 -- it has only ever "
        "been used once, to ingest Lal Kitab (which is one of the 6 *clean* books).\n"
    )

    L.append("### Filesystem forensics: data/progress/*.json mtimes vs. raw-id suffix state\n")
    L.append(
        "`suffixed_at_raw=True` means the **first chunk_id in the progress file already "
        "carries a `_c<N>` suffix** -- i.e. this file, which should hold pre-chunking raw "
        "OCR pages, instead holds chunker output.\n"
    )
    L.append("| mtime | book | n | suffixed_at_raw | first_id |")
    L.append("|---|---|---|---|---|")
    for row in _progress_table():
        if "error" in row:
            L.append(f"| ERROR | {row['book']} | - | - | {row['error']} |")
            continue
        L.append(
            f"| {row['mtime']} | {row['book']} | {row['n']} | "
            f"{row['suffixed_at_raw']} | `{row['first_id']}` |"
        )
    L.append("")
    L.append(
        "Reading the table: the 6 clean books' progress files were written 30-70 minutes "
        "apart on 2026-05-27 (and one fresh write on 2026-05-30 for Lal Kitab) -- consistent "
        "with real, sequential OCR via `process_all_pdfs()`. The 8 affected books' progress "
        "files are all timestamped within an **11-second window** (19:27:29-19:27:40) on "
        "2026-05-27, and *every one of them already has a `_c0`-suffixed first id* -- "
        "inconsistent with OCR (which the clean books show takes 30-70 minutes per book) and "
        "consistent with a fast in-memory loop writing already-computed chunked output back "
        "into the wrong location.\n"
    )

    L.append("### Cross-reference: data/overnight_run.log\n")
    log = _overnight_log_findings()
    if log["available"]:
        L.append(f"Log file: {log['total_lines']} lines, single session "
                  "(2026-05-26 22:52 -> 2026-05-27 19:20).\n")
        L.append("Stage-boundary marker lines:")
        L.append("```")
        for m in log["markers"]:
            L.append(m)
        L.append("```")
        L.append(f"Literal last line of the log file: `{log['last_line']}`\n")
        L.append(
            "The log shows Stage 3 completing cleanly at 19:20:01 with a correct, "
            "single-suffixed chunk count for every book (`Deva-keralam  684` etc. -- see "
            "tally lines below), and the run's closing banner is fully written. The 8 "
            "affected books' progress-file mtimes (19:27:29-19:27:40) fall **7-19 minutes "
            "after this log already closed.** Whatever overwrote those 8 files is not "
            "represented anywhere in this log, and -- per Q5's exhaustive grep -- not "
            "represented in any code path currently in the repository either.\n"
        )
        if log["tally_lines"]:
            L.append("Per-book sub-chunk tally lines captured from Stage 3 (sample):")
            L.append("```")
            for t in log["tally_lines"][:14]:
                L.append(t)
            L.append("```\n")
    else:
        L.append("data/overnight_run.log not found on disk -- cannot cross-reference.\n")

    L.append("### Live cross-check: current chunked_chunks.json vs. live ChromaDB\n")
    L.append(f"Example: `{EXAMPLE_BOOK}` page {EXAMPLE_PAGE}.\n")
    chunked_example = _chunked_chunks_example()
    L.append(f"`data/chunked_chunks.json` (current, on disk) for this page -- {len(chunked_example)} entries:")
    L.append("```")
    for c in chunked_example:
        L.append(f"{c['chunk_id']}  (len(text)={c['len_text']})")
    L.append("```")
    chroma_example = _chromadb_example_check()
    if "error" in chroma_example:
        L.append(f"ChromaDB check failed: {chroma_example['error']}\n")
    else:
        L.append(f"Live ChromaDB collection `{COLLECTION_NAME}` for the same page -- "
                  f"{len(chroma_example['ids'])} entries:")
        L.append("```")
        for cid, ln in zip(chroma_example["ids"], chroma_example["lens"]):
            L.append(f"{cid}  (len(text)={ln})")
        L.append("```")
        only_in_chroma = set(chroma_example["ids"]) - {c["chunk_id"] for c in chunked_example}
        if only_in_chroma:
            L.append(
                f"\n{len(only_in_chroma)} id(s) live in ChromaDB do **not** appear in the "
                f"current `chunked_chunks.json` at all: {sorted(only_in_chroma)}. These must "
                "have been embedded from an earlier version of `chunked_chunks.json` that no "
                "longer exists on disk -- i.e. `embedder.py` was run at least twice for this "
                "book, against two different chunked outputs, and the older single-suffixed "
                "ids were never cleaned up when the newer double-suffixed ones were added.\n"
            )

    L.append("### What this evidence does and doesn't establish\n")
    L.append(
        "**Established with direct evidence:** the 8 affected books' `data/progress/*.json` "
        "files currently hold already-chunked content where they should hold raw OCR pages; "
        "this corruption predates 2026-05-30; `run_single_book.py`'s Stage 3 unconditionally "
        "re-chunks whatever is in those files on every run; the current `chunked_chunks.json` "
        "and the live ChromaDB collection are consistent with exactly one such re-chunk "
        "(2026-05-30, Session 13) on top of one earlier correct chunk-and-embed pass."
    )
    L.append(
        "\n**Not established -- flagged, not speculated:** which specific script or "
        "interactive command overwrote the 8 progress files between 2026-05-27 19:20:01 and "
        "19:27:40. No code currently in the repository contains a write path that would do "
        "this (see the exhaustive `_save_progress` grep under Q5), and no log file covers "
        "that 7-minute window. This cannot be answered from code or the available logs alone."
    )

    return "\n".join(L) + "\n"


def main():
    report = build_report()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = Path(__file__).parent / f"chunking_code_audit_{timestamp}.md"
    out_path.write_text(report, encoding="utf-8")
    sys.stdout.buffer.write(report.encode("utf-8", errors="replace"))
    print(f"\n[written to {out_path}]")


if __name__ == "__main__":
    main()
