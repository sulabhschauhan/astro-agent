# run_single_book.py Validation Proposal — refuse already-chunked progress files at the merge entry point

**Generated:** 2026-06-21 11:38:29 UTC
**Read-only proposal** — no code, data, or ChromaDB changes made or implied by writing this file.

Source diagnostics: `diagnostics/chunking_code_audit_20260621_092249.md` (mechanism + exhaustive `_save_progress` call-site grep) and `diagnostics/provenance_audit_20260621_100237.md` (timeline/forensics — corruption window 2026-05-27T19:27:29–19:27:40, re-chunked once more on 2026-05-30 via this exact script). All structural claims below were independently re-verified against the live files on disk for this report, not just cited from the prior audits.

## 1. Current shape of run_single_book.py

- **File path:** `ingestion/run_single_book.py`
- **Total line count:** 144

**The re-merge logic — verbatim, lines 52–65 (`_merge_progress`, the function that loads progress files and hands them to the chunker):**

```python
def _merge_progress(progress_dir: str, output_path: str) -> list[dict]:
    progress_path = Path(progress_dir)
    progress_files = sorted(progress_path.glob("*.json"))
    all_chunks: list[dict] = []
    for pf in progress_files:
        chunks = json.loads(pf.read_text(encoding="utf-8"))
        all_chunks.extend(chunks)
        logger.info("Merged %-60s  %d chunks", pf.name, len(chunks))
    out = Path(output_path)
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps(all_chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(out)
    logger.info("all_chunks.json written — %d total page chunks", len(all_chunks))
    return all_chunks
```

**Where it's called and handed to the chunker — verbatim, lines 105–108 (`main`, Stage 3):**

```python
    # ── Stage 3: merge + chunker ──────────────────────────────────────────────
    logger.info("Stage 3 — merging all progress files → chunker")
    all_raw = _merge_progress(PROGRESS_DIR, ALL_CHUNKS)
    sub_chunks = chunk_all(all_raw)
```

`_merge_progress()` re-reads **every** file under `data/progress/*.json` (line 54: `progress_path.glob("*.json")`), not just the new book's — so any pre-existing corruption in any of the other 13 files is pulled in unconditionally on every single-book run, independent of which book is actually being ingested.

**Existing input validation on progress-file contents: none.** `json.loads(pf.read_text(...))` (line 57) parses JSON syntax only — there is no check anywhere in this function, or in `main()`, on the *shape* of what comes back. Confirmed by reading the full file (144 lines) end to end: zero `assert`, zero schema check, zero key-presence check on loaded chunk dicts before they reach `chunk_all()`.

## 2. Schema of a CORRECT (raw-OCR) progress file

Read directly: `data/progress/BPHS - 1 RSanthanam.json` (482 entries, one of the 6 confirmed-clean books).

- **Top-level shape:** a JSON list of 482 dicts.
- **Key set — identical across all 482 entries:** `{book_name, chunk_id, image_path, language, page_ref, page_type, text, topic}` — exactly 8 keys, no variation anywhere in the file.
- **`word_count` field:** absent from all 482 entries (0/482).
- **`chunk_id` shape:** `"BPHS - 1 RSanthanam_p1"`, `"BPHS - 1 RSanthanam_p2"`, … — `{book_name}_p{page_num}` only. **0/482 entries** have a trailing `_c<N>` suffix.
- Sample diagram entry: `{"chunk_id": "BPHS - 1 RSanthanam_p1", "text": "", "topic": "", "language": "eng", "page_ref": 1, "image_path": "data/extracted_images\\BPHS - 1 RSanthanam_page_1.jpg", "book_name": "BPHS - 1 RSanthanam", "page_type": "diagram"}`
- Sample text entry: `{"chunk_id": "BPHS - 1 RSanthanam_p2", "text": "CONTENTS |\n\nCh. Details . > | Page...", "topic": "", "language": "eng", "page_ref": 2, "image_path": null, "book_name": "BPHS - 1 RSanthanam", "page_type": "text"}`

Checked across **all 6 clean files** (BPHS-1, BPHS-2, cheiroslanguageo00chei_1, Saravali, Phaladeepika, Jyotish_Lal Kitab — 2,724 entries total): **0/2,724** have a `_c<N>` chunk_id suffix, **0/2,724** have a `word_count` key.

**Structural signature of raw OCR output:** `chunk_id` ends in `_p{digits}` (or `_p{digits}L`/`_p{digits}R` for the unused split-spread path — confirmed against `pdf_processor.py:145`, `chunk_id = f"{book_name}_p{page_num}{side}"`, `side ∈ {"", "L", "R"}`), and `word_count` is never present. This is the producer's own construction — `pdf_processor.py` never appends a `_c` suffix anywhere, and `image_extractor.py` (Stage 2, fills in diagram text) only *reads* `chunk["chunk_id"]` to track already-processed pages (`image_extractor.py:140,142`) — confirmed by grep, it never rewrites the field.

## 3. Schema of a CORRUPTED (already-chunked) progress file

Read directly: `data/progress/Deva-keralam.json` (684 entries, one of the 8 confirmed-corrupted books).

- **Top-level shape:** a JSON list of 684 dicts — same outer shape as a clean file (a flat list), which is exactly why `json.loads()` alone can't catch this.
- **Key set — two variants present:** `{book_name, chunk_id, image_path, language, page_ref, page_type, text, topic}` (8 keys, 12 entries) **and** the same 8 plus `word_count` (9 keys, 672 entries).
- **`word_count` field:** present in 672/684 entries (98.2%) — **not 100%.** The 12 missing cases are diagram pages with empty text, which hit `chunker.py`'s pass-through branch (`chunk_page()`: `if parent["page_type"] == "diagram" and not text: return [{**parent, "chunk_id": f"{parent['chunk_id']}_c0"}]`) — that branch appends the chunk_id suffix but does **not** add `word_count`. `word_count`-presence alone would under-count by 12/684 on this file.
- **`chunk_id` shape:** `"Deva-keralam_p1_c0"`, `"Deva-keralam_p2_c0"`, … — **684/684 entries (100%)** carry a trailing `_c<N>` suffix.

Checked across **all 8 corrupted files** (3,734 entries total): **3,734/3,734 (100%)** have the `_c<N>` chunk_id suffix; only 3,673/3,734 (98.4%) have `word_count`. The suffix check has zero false negatives on this evidence; the word_count check has 61.

**Structural difference:** every corrupted entry's `chunk_id` carries a `_c{i}`/`_c0` suffix appended by `chunker.py`'s own id-construction (`_make_sub_chunks()`: `f"{parent['chunk_id']}_c{i}"`; both diagram branches: `f"{parent['chunk_id']}_c0"` — `chunker.py` lines confirmed in the prior audit). Raw OCR output never produces this suffix at any code site in the repository.

## 4. Recommended detection invariant

**`any(re.search(r"_c\d+$", c.get("chunk_id", "")) for c in chunks)`** — per progress file, before merging it into `all_chunks`. If true for any entry, the file holds chunker output, not raw OCR pages.

Why a structural check over a heuristic, and why it's the single most reliable one available:
- **100% sensitivity and 100% specificity** on every entry across all 14 live progress files (6,458 entries total checked) — strictly better than `word_count`-presence, which is 100% specific but only 98.4% sensitive on the corrupted set (misses 61/3,734 entries — the empty-diagram-page pass-through case).
- **Not a length/heuristic guess** — it's checking for the literal byte-pattern that the one and only code path capable of producing it (`chunker.py`) always and only writes. There is no text-length, language, or word-count heuristic involved.

Why it can't be spoofed by realistic future ingestion variants:
- The suffix is `chunker.py`'s own id-construction convention, used at exactly three call sites (`_make_sub_chunks()` plus the two diagram-branch f-strings) — confirmed by grep, no other site in the codebase ever writes a `_c\d+` suffix onto a `chunk_id`.
- `pdf_processor.py` (the only raw-OCR producer) constructs `chunk_id` as `f"{book_name}_p{page_num}{side}"` with `side ∈ {"", "L", "R"}` — structurally incapable of producing a digit-suffixed `_c<N>` tail. A future split-spread or multi-column OCR variant would still go through this same f-string; it would need a deliberate, unrelated naming change to collide with `_c\d+$`, not an accidental one.
- `image_extractor.py` and `translator.py` (the other two stages that touch chunk dicts before/after chunking) were grepped directly for this report and neither writes to `chunk_id` at all — `image_extractor.py` only reads it for dedup tracking; `translator.py` operates downstream of the chunker on `chunked_chunks.json`, never on `data/progress/*.json` (confirmed: zero references to `progress` or `chunked_chunks` paths in `translator.py`).

**On the `text_sha256` field named in the task's constraints:** confirmed by direct grep — `text_sha256` appears in **zero** files under `data/progress/*.json` or in `data/chunked_chunks.json`, for both the 6 clean and 8 corrupted books alike. This is expected and was locked in the prior session's design: `text_sha256` is computed inside `embedder.py`'s `_to_metadata()` at embed time and written only into ChromaDB metadata — it never round-trips back into any JSON file the chunker or OCR stages touch. **It is not a usable signal for this validator** — it can't distinguish raw-OCR from already-chunked progress files because neither schema ever contains it. The `_c<N>` chunk_id suffix is the correct (and only available) structural signal at this layer.

## 5. Where the validator should live

**Option A — inline in `run_single_book.py` at the `_merge_progress()` entry point.**
- For: matches this task's explicit single-file scope; the check is two lines of logic with one regex constant; no new module, no new import surface; mirrors the precedent just set for `embedder.py` (kept the hash check inline rather than extracting a helper).
- Against: `run_overnight.py` has its **own**, differently-signatured `_merge_progress(progress_dir, pdf_dir, output_path)` (confirmed by reading `ingestion/run_overnight.py:64`) that reads from the exact same `data/progress/*.json` directory and is just as exposed to this failure mode — an inline fix in `run_single_book.py` does not protect it.

**Option B — a separate `ingestion/validators.py` (or `helpers/`) module, called from both scripts.**
- For: single point of truth, immediately reusable by `run_overnight.py` without duplicating the regex/logic.
- Against: there is no `helpers/` or `validators.py` precedent anywhere under `ingestion/` today (confirmed by directory listing — `chunker.py`, `embedder.py`, `image_extractor.py`, `pdf_processor.py`, `query_engine.py`, `run_overnight.py`, `run_single_book.py`, `translator.py`, nothing else); creating one for a single four-line check, for a caller this proposal isn't scoped to touch, is new architecture in service of a hypothetical second caller this task explicitly excludes.

**Recommend: Option A, inline in `run_single_book.py`.** The task's own scope is this script and "the re-merge code path that triggered the 2026-05-30 cascade" specifically — `run_overnight.py`'s log shows it completed cleanly before the corruption (per the provenance audit) and is not implicated in the incident. Per the task's own tie-breaker instruction ("single-file scope preference if argument is close"), and because the gap is close (one caller protected now vs. an unused abstraction for a caller not in scope), inline wins. **Flagging explicitly, not silently deferring:** `run_overnight.py`'s independent `_merge_progress()` remains unprotected by this proposal and should get the identical check in a follow-up pass — noted in §9, not resolved here.

## 6. Failure behavior on detection

**Invocation context, confirmed before recommending:** `run_single_book.py` is a manual, foreground CLI tool — its own docstring usage example is `python ingestion/run_single_book.py "data/pdfs/....pdf"` (lines 6–7), it prints human-readable `[Stage N COMPLETE]` banners at every stage (lines 94, 103, 113, 127–129) clearly meant for someone watching the terminal in real time, and per the provenance audit it has exactly one historical invocation, run interactively to ingest one book (Lal Kitab, Session 13). This contrasts with `run_overnight.py`, which is explicitly the unattended/scheduled batch script (per its own docstring and "OVERNIGHT RUN" banner). `run_single_book.py` is interactive.

- **(a) Raise hard, halt the pipeline.** A human is at the keyboard; an uncaught/explicit exception prints a traceback to the console and to `data/run_single_book.log` (both already wired via the `FileHandler`+`StreamHandler` setup at lines 21–24) and gives Python's free non-zero exit code. The failure surfaces at Stage 3, before any chunking or embedding touches the poisoned data.
- **(b) Log warning + skip the bad file, continue with the rest.** Rejected. This is the same "looks fine, nobody notices" failure shape that let the original corruption sit undetected for 3+ days — the script would still print all four `COMPLETE` banners, `total_sub_chunks` would just silently be smaller than expected, and the dropped book's prior content would vanish from `all_chunks.json` with only a log line as a trace. Directly conflicts with CLAUDE.md Working Style #5 (no unreviewed AI/script decisions chained without a human checkpoint).
- **(c) Log warning + halt with a non-zero exit.** Functionally near-identical to (a) for this script — raising already produces a non-zero exit and a traceback, and the existing logging handlers already capture it to both sinks. (c) would mean catching the condition, calling `logger.error()`, then manually `sys.exit(1)` — an extra moving part (a catch/exit pair) that duplicates what raising already gets for free, and a CLI-exit-code convention this script doesn't otherwise use anywhere (its only existing `sys.exit(1)` is the argument-count usage error at lines 141–143, a different category of failure).

**Recommend: (a).** Raise a `RuntimeError` from inside `_merge_progress()`, naming the offending file — this exactly mirrors the project's own existing convention in this file: `_save_progress()` (lines 42–49) already does `raise RuntimeError(f"Failed to save progress to {path}: {e}") from e` on failure. No new failure-handling idiom is introduced.

## 7. Minimal diff description (prose only — no code written)

Single file: `ingestion/run_single_book.py`.

1. Add `import re` to the top-of-file import block (near line 10–12).
2. Add one module-level constant near the other path constants (lines 35–39): `_CHUNKED_ID_RE = re.compile(r"_c\d+$")`.
3. Add one small named function, placed next to `_merge_progress()` (so it's independently importable for the unit test in §8): `_looks_already_chunked(chunks: list[dict]) -> bool`, body: `return any(_CHUNKED_ID_RE.search(c.get("chunk_id", "")) for c in chunks)`. One `def` line, one docstring line, one `return` line.
4. Inside `_merge_progress()`'s existing `for pf in progress_files:` loop (lines 56–59), insert a guard immediately after the `chunks = json.loads(...)` line and before `all_chunks.extend(chunks)`: an `if _looks_already_chunked(chunks):` block containing one `logger.error(...)` call naming `pf.name` and one `raise RuntimeError(...)` naming `pf.name` and the reason.

**Estimate: ~12–14 line-equivalents** (import: 1; constant: 1; function: 3; loop guard: ~3 logic lines + the `if`/raise pair). Comfortably under the task's 25-line ceiling, and confined to one file — no `validators.py` created.

## 8. Test plan

**`tests/test_run_single_book.py` does not currently exist** (confirmed by glob — no file under `tests/` references `run_single_book`). This proposal would establish that harness, the same way `tests/test_embedder.py` was established from zero in the prior session for `embedder.py`.

**Smallest unit test for the validator:**
- `_looks_already_chunked([{"chunk_id": "Book_p1"}, {"chunk_id": "Book_p2"}]) is False` (clean shape).
- `_looks_already_chunked([{"chunk_id": "Book_p1_c0"}]) is True` (corrupted shape).
- Pure function, no I/O, no ChromaDB, no OpenAI — same isolation level as the `_to_metadata()` unit test from the embedder proposal.

**Smallest integration test simulating the 2026-05-30 failure:**
1. In a `tmp_path` progress directory, write one clean fixture file (`Clean.json` — entries shaped like §2) and one corrupted fixture file (`Bad.json` — entries shaped like §3, i.e. `chunk_id` ending `_c0`).
2. Call `_merge_progress(str(tmp_path), str(tmp_path / "all_chunks.json"))` directly — same granularity as calling `run_pipeline()` directly in the embedder tests, no need to shell out to `main()`.
3. Assert `pytest.raises(RuntimeError, match="Bad.json")` (or whatever filename string the implementation embeds).
4. Assert the output file (`all_chunks.json`) was never written — true by construction once the raise happens, since the write (lines 60–63) sits after the loop; worth asserting explicitly (`not (tmp_path / "all_chunks.json").exists()`) so a future refactor that reorders the write doesn't silently reintroduce a partial/poisoned `all_chunks.json`.

## 9. Failure modes this proposal does not cover

- **Semantically-corrupt-but-structurally-valid progress files** — right schema (no `_c<N>` suffix, correct key set), wrong content: OCR garbage, a page merged under the wrong `book_name`, a truncated page range. The validator only checks chunk_id shape; it has no opinion on content correctness.
- **`run_overnight.py`'s independent `_merge_progress()`** (different signature, same `data/progress/*.json` input) is not covered by this single-file proposal — flagged in §5, carried forward as backlog, not blocking.
- **A future `chunker.py` convention change** (e.g. a different suffix delimiter than `_c{i}`) would silently defeat this exact regex with no code anywhere forced to update in lockstep — there's no shared/canonical constant for the suffix pattern between `chunker.py` and this validator today; this proposal doesn't introduce one (would add a second file/import to stay within single-file scope).
- **Partial corruption is handled, not missed** — worth stating as a non-gap: because the check is `any(...)` over every entry (not just the first, unlike the original forensics script), a progress file with even one chunked entry mixed into otherwise-clean raw OCR pages is still caught.

## 10. Compatibility risks

Searched for any legitimate workflow that intentionally feeds already-chunked content back through `run_single_book.py`'s merge path: **none found.** Re-confirmed independently in this report (not merely cited from the prior audit) via a fresh grep of every reference to `PROGRESS_DIR` / `data/progress` across the entire repository (`.py` files): the only writers into `data/progress/*.json` are `pdf_processor.py`'s `_save_progress()` (raw OCR pages) and `run_single_book.py`'s own `_save_progress()` calls (lines 88, 101 — also raw/diagram-extracted pages, never chunker output). `translator.py` and `chunker.py` never write to this directory. No script, doc, or comment anywhere describes an intentional "replay chunked output through the merge" workflow. **No legitimate use case would be broken by this validator.**

## Recommended next step

The proposal is ready for implementation as-is — no design question is blocking it (the `run_overnight.py` gap is a named, explicit follow-up item, not an open question about *this* script's fix), so the next step is the same surgical single-file pass already done for `embedder.py`: implement the ~12–14 line change in `ingestion/run_single_book.py` plus the new `tests/test_run_single_book.py` harness.
