# GOLDEN FIXTURES — S80 U0 — 2026-07-29T12:07:03Z — 3178fdc

Read-only golden-fixture generator + tests for the Cheiro PDF-native-text vs.
live-corpus quality gap. No production code touched (pdf_processor.py,
chunker.py, embedder.py, query_engine.py untouched, unimported). No repair
logic anywhere — this run captures the DEFECT as it exists today. The fix
lands at a future U-numbered prompt.

Deliverables: `scripts/build_golden_fixtures_S80.py` (generator, opt-in,
never run in CI) → `tests/fixtures/golden_S80.json` (5 fixtures) +
`tests/fixtures/native_coverage_S80.json` (22-row native-text-coverage
census) → `tests/test_golden_fixtures_S80.py` (37 tests, in the default
suite, no PDFs/ChromaDB needed to run it).

---

## Mandatory self-check results (generator, before any output written)

| Assertion | Expected | Observed | Status |
|---|---|---|---|
| Cheiro page count == 310 | 310 | 310 | PASS |
| Cheiro p157 native contains "Plate XVIII" | present | present | PASS |
| Cheiro p158 native char_count == 0 | 0 | 0 | PASS |
| Cheiro p156 native contains "CHAPTER X" | present | present | PASS |

These specifically guard against a recurrence of the `181965d` off-by-one
(see below).

---

## Fixture table

| Fixture | Page (project conv.) | Native chars | Corpus chars (summed) | Corrupt/notable tokens | classify_page_label |
|---|---|---|---|---|---|
| cheiro_p156_chapter_x | 156 (idx 155) | 1719 | 1708 (3 chunks) | native="rnensal", corpus has "hne" (×2, in c1/c0) and "mensal" | text |
| cheiro_p157_plate_xviii | 157 (idx 156) | 12 | 0 | native="Plate XVIII." | diagram |
| cheiro_p158_plate_verso | 158 (idx 157) | 0 | 0 | genuinely blank | diagram |
| cheiro_p191_mixed_empty_corpus | 191 (idx 190) | 1706 | 0 | "mixed" page_type discards OCR text by construction | mixed |
| path_c_boundary_page | Deva-keralam, project p102 (idx 101) | 0 | 3760 (6 chunks) | corpus-only content, no native source | text |

`source_pdf_sha256` (Cheiro, all 4 Cheiro fixtures): `0e3271fbd3108110bd9217e662f9064206ec2d8435a6f2768ee4786440b9ccb1`
`source_pdf_sha256` (Deva-keralam, path_c_boundary_page): `6e97b59cdd03a6b256053f67a8e2c4d08030c8c2b949a51d8ba1dab4cf55fe94`

---

## Verified deviations from the instructing prompt

1. **`181965d` off-by-one, confirmed and isolated.** `diagnostics/r1_p0_page_triage_S79.md`'s "Full Metrics Table" and "TARGETED SUB-REPORT" (and, on closer inspection, even its nominally-JSON-sourced "MIXED PAGE_TYPE PAGES" sub-table) all display page numbers ONE HIGHER than this project's own convention (`page_ref` metadata / `chunk_id` `_p<n>_` / pdf.pages[n-1]). Its `printed_page_no` column is unaffected (read directly off page-footer text) — cross-checked folio 98 → project p156 (CHAPTER X) and folio 125 → project p191 (CHAPTER XIX), both independently reproduced via direct `pdfplumber` calls, not read off the diagnostic transcript. The 4 mandatory self-checks above exist to catch a recurrence of exactly this bug in this generator.

2. **Cheiro p156 native text: "rnensal", not "mensal".** Independently reproduced via a direct `pdfplumber.extract_text()` call. This is a real ligature-merge artifact baked into the archive.org-embedded NATIVE text layer itself — NOT something Tesseract introduced. The live corpus (Tesseract OCR) actually has "mensal" for this word; native has "rnensal". `test_native_p156_preserve_case_rnensal` asserts the true token.

3. **Cheiro p90 is no longer an empty-corpus page.** Live ChromaDB has 3 non-empty chunks for page_ref=90 (923+613+910 chars) — diverged from the stale `data/progress/cheiroslanguageo00chei_1.json` snapshot (page_type="mixed", text="") an earlier diagnostic pass read from; the corpus has been re-ingested since. Of this book's 5 originally `page_type="mixed"` pages ([19, 20, 90, 191, 220]), only page_ref 19 and 191 still show zero live chunks today (verified via a live `collection.get()` call). Fixture 4 uses p191 instead (CHAPTER XIX, 1706 native chars, clean chapter-opening prose, currently zero live chunks).

4. **F5 FALSIFIED, not merely unverified.** The originally-specified "LAL KITAB Devanagari-orphan" fixture was tested against reality by scanning **every page of all 22 PDFs in `data/pdfs/`** for U+0900–U+097F codepoints in native text (not just the Lal Kitab book). Result: **zero Devanagari codepoints anywhere, in any book's native text layer, corpus-wide.** This is not a coverage gap in the scan — it was a full corpus-wide, all-pages sweep. `strip_devanagari()`/`detect_language()`'s Devanagari-handling machinery in `chunker.py` exists for OCR-hallucinated (Tesseract) Devanagari, never for anything present in any of these PDFs' own native text. The Lal-Kitab-named ingested book (`Jyotish_Lal Kitab_B.M. Gosvami`) is an English translation edition (99.87% Path-C-eligible, see census below); `LAL KITAB-1941.pdf` exists on disk but is not an ingested book_name and independently fails to open as a paginated document under pdfplumber (`page_count == 0`, malformed page tree). **U6 (the native-Devanagari-repair step implied by the original F5 defect class) is removed from the ladder — there is nothing there to fix.**

5. **Fixture 5 replaced with a Path-C-boundary case (per design-chat ruling).** "Path C" = a future native-text-alignment repair (reconciling live corpus chunks against the PDF's own native text layer). For a page where `native_char_count == 0`, Path C has no source to align against — it is structurally out of scope for that repair, regardless of how much (Tesseract-OCR'd) text the live corpus holds for that page. Selected by rule, not hardcoded: from the book(s) tied for the lowest native chars-per-page average across the full 22-book census, take the single page with the highest live corpus chunk char total where `native_char_count == 0`. Six books tie exactly at a 0.0 average (see census below); the tie was broken by searching across all six for the globally-best-populated page, landing on **Deva-keralam, project page 102** (3760 corpus chars across 6 chunks, genuine Jaimini-astrology prose, entirely Tesseract-sourced with zero native text to check it against).

6. **PDF count corrected: 22, not 19.** An early exploratory `ls data/pdfs/ | head -20` truncated the listing; `ls data/pdfs/*.pdf | wc -l` confirms 22. The census covers all 22; the test file's `test_census_covers_all_pdfs` and both module docstrings were corrected to say 22 before this run.

---

## PATH C COVERAGE — full census, ranked by `path_c_eligible` ascending

| book_name | page_count | native_text_pages | zero_native_pages | total_native_chars | mean_chars/page | path_c_eligible |
|---|---|---|---|---|---|---|
| LAL KITAB-1941 | 0 | 0 | 0 | 0 | N/A (0 pages, malformed) | N/A |
| Deva-keralam | 298 | 0 | 298 | 0 | 0.0 | 0.0000 |
| Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan | 527 | 0 | 527 | 0 | 0.0 | 0.0000 |
| Jataka Parijata with explanation of Pt. Kapileshvara Shastri and Vimala Hindi Tika of Pt. Shri Matri Prasad Shastri Series No. 10 - Kashi Sanskrit Series | 588 | 0 | 588 | 0 | 0.0 | 0.0000 |
| Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri | 473 | 0 | 473 | 0 | 0.0 | 0.0000 |
| Saravali of Kalyana Varma Santhanam R. (Astrology) | 352 | 0 | 352 | 0 | 0.0 | 0.0000 |
| Sarvartha-Chintamani | 400 | 0 | 400 | 0 | 0.0 | 0.0000 |
| uttkalamrita-kalidas-ps-sastri | 256 | 181 | 75 | 268760 | 1049.8 | 0.7070 |
| cheiroslanguageo00chei_1 | 310 | 245 | 65 | 339325 | 1094.6 | 0.7903 |
| David Kundli | 56 | 54 | 2 | 118546 | 2116.9 | 0.9643 |
| Sheridan Kundli | 56 | 54 | 2 | 122773 | 2192.4 | 0.9643 |
| VedicReport5-24-202610-01-26PM | 56 | 54 | 2 | 119726 | 2138.0 | 0.9643 |
| Wife_VedicReport | 56 | 54 | 2 | 119324 | 2130.8 | 0.9643 |
| Vedic Astrology_ PVR Narashimha Rao | 515 | 512 | 3 | 816857 | 1586.1 | 0.9942 |
| Jyotish_Lal Kitab_B.M. Gosvami | 778 | 777 | 1 | 1125089 | 1446.1 | 0.9987 |
| [Deepak Kapoor] Astronomy and Mathematical Astrology_text | 123 | 123 | 0 | 356401 | 2897.6 | 1.0000 |
| Bhava and Graha Balas_B.V.Raman 1996 | 129 | 129 | 0 | 126158 | 978.0 | 1.0000 |
| BPHS - 1 RSanthanam | 482 | 482 | 0 | 762227 | 1581.4 | 1.0000 |
| BPHS - 2 RSanthanam | 552 | 552 | 0 | 742066 | 1344.3 | 1.0000 |
| Muhurtha-Chinthamani | 322 | 322 | 0 | 920400 | 2858.4 | 1.0000 |
| Prasna Marga 1 | 278 | 278 | 0 | 604644 | 2175.0 | 1.0000 |
| Prasna Marga 2 | 242 | 242 | 0 | 547987 | 2264.4 | 1.0000 |

**Note on the five named "worst-hit chart books" (Jyotish Lal Kitab, Phaladeepika, BPHS-1, BPHS-2, Saravali):** only **2 of 5** are actually Path C ineligible — **Phaladeepika (0.0000)** and **Saravali (0.0000)**, both fully-scanned PDFs with zero native text anywhere. The other 3 are, in fact, HIGHLY Path-C-eligible, not ineligible: **Jyotish_Lal Kitab_B.M. Gosvami (0.9987)**, **BPHS - 1 RSanthanam (1.0000)**, **BPHS - 2 RSanthanam (1.0000)**. Flagging this precisely rather than silently reconciling: the assumption that these 5 books cluster together on Path-C-eligibility does not hold — the corpus splits sharply into a "1.0-ish" cluster (9 books, all textual reference works with clean embedded text) and a "0.0" cluster (6 books, fully scanned image PDFs with no embedded text layer at all), with Cheiro (0.79) and uttkalamrita (0.71) sitting in between as the only two genuinely mixed-coverage books.

---

## Full test suite

- **Before this task's new file:** 3304 passed / 0 failed / 7 skipped / 1 xpassed (reconciled below).
- **After adding `tests/test_golden_fixtures_S80.py` (37 new tests, all passing):** **3341 passed / 0 failed / 7 skipped / 1 xpassed**, 105.04s.

### Reconciling the 3302-vs-3304 discrepancy

`SESSION_LOG.md` line 4845 (S77 close-out) is the last count actually WRITTEN into that file's prose: **3302 pass / 0 fail / 7 skip / 1 xpassed**. That figure predates S78's own work — commits `16f6439` and `be35a1a` each added a test and reported **3304 pass / 0 fail / 7 skip / 1 xpassed** in their own commit messages, but neither `SESSION_LOG.md` nor `CLAUDE.md` ever had this newer figure written back into their prose (`diagnostics/e2g_preflight_S79.md` already flagged this exact gap during S79 preflight). Independent confirmation this run: `3341 (this run's total) − 37 (this task's new tests) = 3304` — matching S78's commit-time figure exactly, not the stale 3302 in `SESSION_LOG.md`. **3304 is the correct pre-existing baseline; 3302 is stale prose that was never updated after S78.** Not fixed here (docs-only correction belongs to a future session-close bookkeeping pass per this task's own scope — no CLAUDE.md/SESSION_LOG.md edit made).

---

## Commit discipline note

Per CLAUDE.md Working Style #14 (commit ratification token), this task's
instructing prompt does not contain the literal line `RATIFIED: commit
authorized`. `scripts/build_golden_fixtures_S80.py`, `tests/test_golden_fixtures_S80.py`,
`tests/fixtures/golden_S80.json`, and `tests/fixtures/native_coverage_S80.json`
are source/test/fixture files, not docs — **not committed this run**, surfaced
to the user instead. Only this file (`diagnostics/golden_fixtures_S80.md`,
docs-exempt) plus the two pending S79 diagnostics files
(`diagnostics/e2g_preflight_S79.md`, `diagnostics/corpus_export_S79.md`) are
committed.
