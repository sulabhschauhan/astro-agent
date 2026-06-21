# Chunking-Layer Code Audit -- X / X_c0 Duplicate Pattern

**Generated:** 2026-06-21 09:22:46 UTC  
**Read-only audit** -- no code, data, or ChromaDB changes made by this script.

Source diagnostic: `diagnostics/chromadb_dup_report_20260621_080119.md` -- 2,892 duplicate-text groups, 100% of which match a chunk_id `X` / `X_c<N>` pair holding byte-identical text, across 8 of 14 books.

## 1. Files implementing chunking and the recursive split

- `ingestion/chunker.py`
  - `chunk_page(parent)` -- per-page dispatcher (diagram/text/mixed routing)
  - `chunk_all(chunks)` -- driver loop, calls `chunk_page()` once per input item
  - `_make_sub_chunks(segments, parent)` -- builds sub-chunk dicts, assigns `_c{i}` ids
  - `sliding_window(text)` -- the actual long-text splitter (400-word window, 50-word overlap)
  - `split_on_paragraphs()` / `merge_paragraphs()` -- pre-split helpers feeding the threshold check

There is no in-function recursion anywhere in `chunker.py` -- `chunk_page()` does not call itself, and `chunk_all()`'s loop is a single flat pass. The "recursive" behavior in the bug hypothesis is the **pipeline** re-invoking `chunk_all()` across separate process runs on data that already passed through it once, not literal recursion within the module.

`chunk_all()` call sites (exhaustive grep, excludes the `chunker.py` `__main__` self-test):
- `ingestion/run_overnight.py:99`
- `ingestion/run_single_book.py:108`

## 2. Under what condition is the splitter invoked?

`chunk_page()` is invoked unconditionally on every item in `chunk_all()`'s input list:

```python
def chunk_all(chunks: list[dict]) -> list[dict]:
    """Process all page chunks. Returns flat list with full schema populated."""
    output = []
    for chunk in chunks:
        sub_chunks = chunk_page(chunk)
        output.extend(sub_chunks)
        logger.info(f"{chunk['chunk_id']} → {len(sub_chunks)} sub-chunk(s)")
    logger.info(f"Total output chunks: {len(output)}")
    return output

```
No check exists here (or anywhere in `chunk_all`/`chunk_page`) for whether `chunk["chunk_id"]` already carries a `_c<N>` suffix from a prior pass.

Inside `chunk_page()`, the word-count splitter (`sliding_window`) *is* gated:

```python
    segments = []
    for segment in merge_paragraphs(paragraphs):
        if len(segment.split()) > SPLIT_THRESHOLD:
            segments.extend(sliding_window(segment))
        else:
            segments.append(segment)

```
Gate: `len(segment.split()) > SPLIT_THRESHOLD` (SPLIT_THRESHOLD = 500).

## 3. What does the splitter emit below SPLIT_THRESHOLD?

Full `chunk_page()` for reference (diagram branches + the text/mixed branch):

```python
def chunk_page(parent: dict) -> list[dict]:
    """
    Process a single page chunk into output sub-chunks.

    - diagram + empty text  → pass through unchanged (no enrichment, no _c suffix)
    - diagram + filled text → enrich (language/topic/word_count), no split, append _c0
    - text / mixed          → paragraph split → merge → sliding window if >500 words
    """
    text = parent.get("text", "").strip()

    if parent["page_type"] == "diagram" and not text:
        return [{**parent, "chunk_id": f"{parent['chunk_id']}_c0"}]

    if parent["page_type"] == "diagram" and text:
        enriched = {
            **parent,
            "chunk_id": f"{parent['chunk_id']}_c0",
            "topic": detect_topic(text),
            "language": detect_language(text),
            "word_count": len(text.split()),
        }
        return [enriched]

    # text and mixed pages — strip Devanagari before chunking
    text = strip_devanagari(text)
    paragraphs = split_on_paragraphs(text)
    if not paragraphs:
        return []

    segments = []
    for segment in merge_paragraphs(paragraphs):
        if len(segment.split()) > SPLIT_THRESHOLD:
            segments.extend(sliding_window(segment))
        else:
            segments.append(segment)

    return _make_sub_chunks(segments, parent)

```
Trace for a text/mixed page whose merged text is already under SPLIT_THRESHOLD (true for any page that was already chunked once): `merge_paragraphs()` reduces to a single buffer, the `else: segments.append(segment)` branch fires (segment unmodified), `segments` ends up as a 1-element list holding the text byte-for-byte, and `_make_sub_chunks()` emits exactly one sub-chunk with `chunk_id = f"{parent['chunk_id']}_c0"` and `text` identical to the input. This is the exact mechanism that produces a child byte-identical to its parent.

For a diagram page with empty text, the behavior is even more direct -- no threshold check at all:

```python
    if parent["page_type"] == "diagram" and not text:
        return [{**parent, "chunk_id": f"{parent['chunk_id']}_c0"}]

    if parent["page_type"] == "diagram" and text:
        enriched = {
            **parent,
            "chunk_id": f"{parent['chunk_id']}_c0",
            "topic": detect_topic(text),
            "language": detect_language(text),
            "word_count": len(text.split()),
        }
        return [enriched]

```
## 4. How are suffixes generated? What prevents double-suffixing?

All three id-construction sites in `chunker.py`:

```python
def _make_sub_chunks(segments: list[str], parent: dict) -> list[dict]:
    return [
        {
            "chunk_id": f"{parent['chunk_id']}_c{i}",
            "text": text,
            "topic": detect_topic(text),
            "language": detect_language(text),
            "page_ref": parent["page_ref"],
            "image_path": parent.get("image_path"),
            "book_name": parent["book_name"],
            "page_type": parent["page_type"],
            "word_count": len(text.split()),
        }
        for i, text in enumerate(segments)
    ]

```
(plus the two diagram-branch f-strings quoted under Q3, both `f"{parent['chunk_id']}_c0"`).

Grep of `chunker.py` for suffix-guard patterns ['removesuffix', 'rsplit', 'endswith("_c', 'already chunked', 'already_suffixed'] -> found: none. All three construction sites take `parent['chunk_id']` as an opaque string and concatenate `_c{i}`/`_c0` unconditionally. Nothing inspects whether that string already ends in `_c\d+` before appending another suffix.

## 5. Is the ingestion entry point idempotent on re-run?

**Short answer: partially.** The OCR stage is idempotent via a skip-cache; the chunking stage is not idempotent and has no awareness of its own prior output; the embed stage's idempotency check is id-string-based, not content-based.

**(a) OCR stage -- IS idempotent, via skip-if-exists:**

```python
def process_all_pdfs(
    pdf_dir: str,
    output_dir: str,
    progress_dir: str = "data/progress",
) -> list[dict]:
    """Process all PDFs sorted by file size ascending. Saves per-book progress to
    progress_dir after each book — skips books with existing progress on restart."""
    progress_path = Path(progress_dir)
    progress_path.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(Path(pdf_dir).glob("*.pdf"), key=lambda p: p.stat().st_size)
    if not pdf_files:
        logger.warning(f"No PDFs found in {pdf_dir}")
        return []

    logger.info(f"Found {len(pdf_files)} PDFs to process")
    all_chunks = []

    for pdf_path in pdf_files:
        book_stem = pdf_path.stem
        progress_file = progress_path / f"{book_stem}.json"

        if progress_file.exists():
            try:
                with open(progress_file, "r", encoding="utf-8") as f:
                    chunks = json.load(f)
                logger.info(f"[SKIP] {book_stem} — {len(chunks)} chunks loaded from progress")
                all_chunks.extend(chunks)
                continue
            except Exception as e:
                logger.warning(f"Progress file corrupted for {book_stem}: {e} — reprocessing")

        try:
            chunks = process_pdf(str(pdf_path), output_dir)
            _save_progress(chunks, progress_file)
            all_chunks.extend(chunks)
            logger.info(f"[DONE] {book_stem} — {len(chunks)} chunks saved to progress")
        except Exception as e:
            logger.error(f"[FAIL] {pdf_path.name}: {e}")
            continue

    logger.info(f"Total chunks extracted: {len(all_chunks)}")
    return all_chunks


# Quick test — run this file directly to validate

```
**Same pattern in `run_single_book.py`'s Stage 1:**

```python
    # ── Stage 1: pdf_processor ──────────────────────────────────────────────
    if progress_file.exists():
        logger.info("Stage 1 — SKIPPED (progress file exists): %s", progress_file)
        raw_chunks = json.loads(progress_file.read_text(encoding="utf-8"))
    else:
        logger.info("Stage 1 — pdf_processor (OCR, %s)", pdf_path)
        raw_chunks = process_pdf(pdf_path, OUTPUT_DIR)
        _save_progress(raw_chunks, progress_file)

```
**(b) Chunking stage -- NOT idempotent.** `run_single_book.py` Stage 3 re-merges *every* progress file (not just the newly-added book's) and re-chunks the full set, unconditionally, on every invocation:

```python
    # ── Stage 3: merge + chunker ──────────────────────────────────────────────
    logger.info("Stage 3 — merging all progress files → chunker")
    all_raw = _merge_progress(PROGRESS_DIR, ALL_CHUNKS)
    sub_chunks = chunk_all(all_raw)

    # Isolate new book's chunks for reporting
    new_chunks = [c for c in sub_chunks if c["book_name"] == book_name]
    logger.info("Stage 3 DONE — total sub-chunks: %d  new book: %d", len(sub_chunks), len(new_chunks))
    print(f"\n[Stage 3 COMPLETE] chunk count (new book only): {len(new_chunks)}  total: {len(sub_chunks)}\n")

```
`_merge_progress()` here (and in `run_overnight.py`) performs no transformation -- it concatenates `progress/*.json` content verbatim. So `chunk_all()`'s input on any re-run is whatever is currently sitting in `data/progress/*.json`. If those files ever hold already-chunked content instead of raw OCR pages, `chunk_all()` will silently re-chunk over them -- there is no flag, hash, or marker anywhere in this pipeline distinguishing "raw page" input from "already-chunked" input.

**(c) Embed stage -- idempotent by id string only, not by content:**

```python
    # Idempotency: skip chunks already present in ChromaDB
    existing_ids = set(collection.get(include=[])["ids"])
    to_embed = [c for c in embeddable if c["chunk_id"] not in existing_ids]
    skipped_existing = len(embeddable) - len(to_embed)
    if skipped_existing:
        logger.info(f"Skipping {skipped_existing} chunks already in ChromaDB — {len(to_embed)} to embed")

```
This skip-guard compares `chunk_id` strings only. Two records holding identical text under different ids (e.g. `X_c0` vs `X_c0_c0`) are both treated as distinct, unembedded content -- both get upserted, and neither overwrites the other.

Exhaustive grep of every `_save_progress(...)` call site across `ingestion/*.py` (checking what each one persists into `data/progress/`):

- `ingestion/pdf_processor.py:182` -- saves `chunks: list[dict]`
- `ingestion/pdf_processor.py:227` -- saves `chunks`
- `ingestion/run_single_book.py:42` -- saves `chunks: list[dict]`
- `ingestion/run_single_book.py:88` -- saves `raw_chunks`
- `ingestion/run_single_book.py:101` -- saves `raw_chunks`

In every call site above, the saved variable traces back to `process_pdf()` / `extract_diagram_text()` output (raw OCR / diagram-extraction pages) -- never to `chunk_all()`'s output. **No code currently in this repository writes chunked (`_c`-suffixed) content into `data/progress/*.json`.** Whatever did so for the 8 affected books (see Q6) is not present in the current codebase.

## 6. Why are 6 books clean and 8 affected?

### Git history of the ingestion scripts

**`ingestion/run_single_book.py`**
- 7753349 2026-05-30 feat(session-13): ingest Jyotish_Lal Kitab_B.M. Gosvami, purge LAL KITAB-1941

**`ingestion/run_overnight.py`**
- 5afc37d 2026-05-26 Crash recovery: per-book progress saves, run_overnight.py pipeline, embedder reads pre-chunked input

**`ingestion/chunker.py`**
- 8a0b680 2026-05-26 Session 2: mixed classifier, strip_devanagari, agent visual intelligence notes
- 34de4c7 2026-05-26 Session 1 complete: pdf_processor, image_extractor, chunker + overnight run started

**`ingestion/embedder.py`**
- 5afc37d 2026-05-26 Crash recovery: per-book progress saves, run_overnight.py pipeline, embedder reads pre-chunked input
- fee33ef 2026-05-26 Fix: add load_dotenv() to image_extractor.py; fix stale docstring in embedder.py
- 43fda8a 2026-05-26 Session 2 complete: embedder working, 3029 chunks in ChromaDB
- df37752 2026-05-26 Session 2: classifier, chunker, embedder, agent personas
- 41ade88 2026-05-26 Add working style standards to cursorrules and CLAUDE.md

**`ingestion/pdf_processor.py`**
- 5afc37d 2026-05-26 Crash recovery: per-book progress saves, run_overnight.py pipeline, embedder reads pre-chunked input
- bce3dc9 2026-05-26 Pre-run config: sort PDFs by size, update book registry for Muhurta Chintamani
- 663abaf 2026-05-26 Fix classify_page(): remove dead Pattern 3 planetary sub-check
- df37752 2026-05-26 Session 2: classifier, chunker, embedder, agent personas
- 8a0b680 2026-05-26 Session 2: mixed classifier, strip_devanagari, agent visual intelligence notes
- 41ade88 2026-05-26 Add working style standards to cursorrules and CLAUDE.md
- 7277832 2026-05-25 Add book registry and topic tags to cursorrules

**`ingestion/translator.py`**
- f6ef437 2026-05-26 Session 4: translator.py â€” Hindi ingestion pipeline

`run_single_book.py` has exactly one commit, dated 2026-05-30 -- it has only ever been used once, to ingest Lal Kitab (which is one of the 6 *clean* books).

### Filesystem forensics: data/progress/*.json mtimes vs. raw-id suffix state

`suffixed_at_raw=True` means the **first chunk_id in the progress file already carries a `_c<N>` suffix** -- i.e. this file, which should hold pre-chunking raw OCR pages, instead holds chunker output.

| mtime | book | n | suffixed_at_raw | first_id |
|---|---|---|---|---|
| 2026-05-27T09:48:20 | BPHS - 1 RSanthanam | 482 | False | `BPHS - 1 RSanthanam_p1` |
| 2026-05-27T10:21:57 | BPHS - 2 RSanthanam | 552 | False | `BPHS - 2 RSanthanam_p1` |
| 2026-05-27T11:27:53 | cheiroslanguageo00chei_1 | 310 | False | `cheiroslanguageo00chei_1_p1` |
| 2026-05-27T11:52:23 | Saravali of Kalyana Varma Santhanam R. (Astrology) | 352 | False | `Saravali of Kalyana Varma Santhanam R. (Astrology)_p1` |
| 2026-05-27T12:43:11 | Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri | 473 | False | `Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri_p1` |
| 2026-05-27T19:27:29 | Deva-keralam | 684 | True | `Deva-keralam_p1_c0` |
| 2026-05-27T19:27:29 | Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan | 449 | True | `Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan_p1_c0` |
| 2026-05-27T19:27:30 | Jataka Parijata with explanation of Pt. Kapileshvara Shastri and Vimala Hindi Tika of Pt. Shri Matri Prasad Shastri Series No. 10 - Kashi Sanskrit Series | 513 | True | `Jataka Parijata with explanation of Pt. Kapileshvara Shastri and Vimala Hindi Tika of Pt. Shri Matri Prasad Shastri Series No. 10 - Kashi Sanskrit Series_p1_c0` |
| 2026-05-27T19:27:33 | Muhurtha-Chinthamani | 612 | True | `Muhurtha-Chinthamani_p1_c0` |
| 2026-05-27T19:27:35 | Prasna Marga 1 | 528 | True | `Prasna Marga 1_p1_c0` |
| 2026-05-27T19:27:37 | Prasna Marga 2 | 439 | True | `Prasna Marga 2_p1_c0` |
| 2026-05-27T19:27:38 | Sarvartha-Chintamani | 431 | True | `Sarvartha-Chintamani_p1_c0` |
| 2026-05-27T19:27:40 | uttkalamrita-kalidas-ps-sastri | 378 | True | `uttkalamrita-kalidas-ps-sastri_p1_c0` |
| 2026-05-30T10:45:37 | Jyotish_Lal Kitab_B.M. Gosvami | 778 | False | `Jyotish_Lal Kitab_B.M. Gosvami_p1` |

Reading the table: the 6 clean books' progress files were written 30-70 minutes apart on 2026-05-27 (and one fresh write on 2026-05-30 for Lal Kitab) -- consistent with real, sequential OCR via `process_all_pdfs()`. The 8 affected books' progress files are all timestamped within an **11-second window** (19:27:29-19:27:40) on 2026-05-27, and *every one of them already has a `_c0`-suffixed first id* -- inconsistent with OCR (which the clean books show takes 30-70 minutes per book) and consistent with a fast in-memory loop writing already-computed chunked output back into the wrong location.

### Cross-reference: data/overnight_run.log

Log file: 16920 lines, single session (2026-05-26 22:52 -> 2026-05-27 19:20).

Stage-boundary marker lines:
```
2026-05-26 22:52:49,350 - INFO - OVERNIGHT RUN STARTED  2026-05-26T18:52:49.350670+00:00
2026-05-27 07:44:52,987 - INFO - OVERNIGHT RUN STARTED  2026-05-27T03:44:52.987506+00:00
2026-05-27 19:18:57,633 - INFO - Stage 1 complete — 5601 raw page chunks
2026-05-27 19:18:59,154 - INFO - Stage 2 complete — 5601 total chunks → data/all_chunks.json
2026-05-27 19:20:01,104 - INFO - Stage 3 complete — 7521 sub-chunks
2026-05-27 19:20:01,404 - INFO - OVERNIGHT RUN COMPLETE
```
Literal last line of the log file: `2026-05-27 19:20:01,404 - INFO - ======================================================================`

The log shows Stage 3 completing cleanly at 19:20:01 with a correct, single-suffixed chunk count for every book (`Deva-keralam  684` etc. -- see tally lines below), and the run's closing banner is fully written. The 8 affected books' progress-file mtimes (19:27:29-19:27:40) fall **7-19 minutes after this log already closed.** Whatever overwrote those 8 files is not represented anywhere in this log, and -- per Q5's exhaustive grep -- not represented in any code path currently in the repository either.

Per-book sub-chunk tally lines captured from Stage 3 (sample):
```
2026-05-27 19:20:01,104 - INFO -   BPHS - 1 RSanthanam                                          717
2026-05-27 19:20:01,104 - INFO -   BPHS - 2 RSanthanam                                          736
2026-05-27 19:20:01,104 - INFO -   Deva-keralam                                                 684
2026-05-27 19:20:01,104 - INFO -   Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan 449
2026-05-27 19:20:01,104 - INFO -   Jataka Parijata with explanation of Pt. Kapileshvara Shastri and Vimala Hindi Tika of Pt. Shri Matri Prasad Shastri Series No. 10 - Kashi Sanskrit Series 513
2026-05-27 19:20:01,104 - INFO -   Muhurtha-Chinthamani                                         612
2026-05-27 19:20:01,104 - INFO -   Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri            603
2026-05-27 19:20:01,104 - INFO -   Prasna Marga 1                                               528
2026-05-27 19:20:01,104 - INFO -   Prasna Marga 2                                               439
2026-05-27 19:20:01,104 - INFO -   Saravali of Kalyana Varma Santhanam R. (Astrology)           476
2026-05-27 19:20:01,104 - INFO -   Sarvartha-Chintamani                                         431
2026-05-27 19:20:01,104 - INFO -   cheiroslanguageo00chei_1                                     579
2026-05-27 19:20:01,104 - INFO -   uttkalamrita-kalidas-ps-sastri                               378
```

### Live cross-check: current chunked_chunks.json vs. live ChromaDB

Example: `Deva-keralam` page 8.

`data/chunked_chunks.json` (current, on disk) for this page -- 3 entries:
```
Deva-keralam_p8_c0_c0  (len(text)=682)
Deva-keralam_p8_c1_c0  (len(text)=562)
Deva-keralam_p8_c2_c0  (len(text)=252)
```
Live ChromaDB collection `astro_chunks` for the same page -- 6 entries:
```
Deva-keralam_p8_c0  (len(text)=682)
Deva-keralam_p8_c1  (len(text)=562)
Deva-keralam_p8_c2  (len(text)=252)
Deva-keralam_p8_c0_c0  (len(text)=682)
Deva-keralam_p8_c1_c0  (len(text)=562)
Deva-keralam_p8_c2_c0  (len(text)=252)
```

3 id(s) live in ChromaDB do **not** appear in the current `chunked_chunks.json` at all: ['Deva-keralam_p8_c0', 'Deva-keralam_p8_c1', 'Deva-keralam_p8_c2']. These must have been embedded from an earlier version of `chunked_chunks.json` that no longer exists on disk -- i.e. `embedder.py` was run at least twice for this book, against two different chunked outputs, and the older single-suffixed ids were never cleaned up when the newer double-suffixed ones were added.

### What this evidence does and doesn't establish

**Established with direct evidence:** the 8 affected books' `data/progress/*.json` files currently hold already-chunked content where they should hold raw OCR pages; this corruption predates 2026-05-30; `run_single_book.py`'s Stage 3 unconditionally re-chunks whatever is in those files on every run; the current `chunked_chunks.json` and the live ChromaDB collection are consistent with exactly one such re-chunk (2026-05-30, Session 13) on top of one earlier correct chunk-and-embed pass.

**Not established -- flagged, not speculated:** which specific script or interactive command overwrote the 8 progress files between 2026-05-27 19:20:01 and 19:27:40. No code currently in the repository contains a write path that would do this (see the exhaustive `_save_progress` grep under Q5), and no log file covers that 7-minute window. This cannot be answered from code or the available logs alone.
