# cheiro_clean_v1 -- page-anchored citation corpus build + validation report

Report-first, NO commit, NO re-ingest/re-embed. Builds a citation corpus from the Cheiro PDF's own text layer -- does not touch the existing corpus or ChromaDB.

## STEP 0 -- preserve first

- `diagnostics/latest_run.md` copied verbatim to `data\cheiro\cheiro_pdf_fulltext.md` BEFORE this script ran.
- Byte length: source 336273, copy 336273 -- MATCH.
- `diagnostics/latest_run.md` NOT touched by this script (only read, for nothing -- this script reads the STEP 0 copy, never the live latest_run.md).

## STEP 1 -- inputs

- PDF: `data\pdfs\cheiroslanguageo00chei_1.pdf`
- Existing JSON: `data\chunked_chunks.json` (read-only) -- 579 chunks across 305 distinct page_refs for 'cheiroslanguageo00chei_1'.
- Reference: `data\cheiro\cheiro_pdf_fulltext.md` (STEP 0 copy) -- 1826 lines.

## STEP 2/3 -- extraction + entry build

- 310 entries built (1 per PDF page, no sub-chunking). 0 page(s) failed extraction: none.

- Corpus written: `data\cheiro\cheiro_clean_v1.json` (310 entries).

## STEP 4a -- page-ref alignment (new extraction vs existing JSON)

8 text pages spread across the book (evenly sampled from 201 total text pages): [2, 37, 82, 119, 155, 192, 224, 309]

| page_ref | rare token (from new entry) | in old JSON same page_ref? | verdict |
|---|---|---|---|
| 2 | 'COPYRIGHT' | False | MISMATCH |
| 37 | 'distinguishable' | True | MATCH |
| 82 | 'characteristics' | True | MATCH |
| 119 | 'interesting' | True | MATCH |
| 155 | 'superstitious' | True | MATCH |
| 192 | 'disappointment' | True | MATCH |
| 224 | 'Malformation' | True | MATCH |
| 309 | None | n/a | SKIP (no >=8-char word found to test) |

1 mismatch(es) -- within tolerance (task's stop condition is >1).

Investigated the page_ref 2 mismatch directly (not left unexplained): the old JSON's `p2_c0` chunk has `text=""` (an empty/image-only page in the existing corpus), while the new pdfplumber extraction of the same page returns ~1450 chars of OCR-noise-like fragments (`'V *,*<A .0^ A\...'`) -- consistent with page 2 being a frontispiece/signature illustration page that pdfplumber attempts to run text extraction over anyway, rather than a genuine prose page. Not a page-ref offset bug; the two extractions simply disagree about whether this specific page has any real text at all. Flagged for awareness -- `page_type` for this entry in the new corpus should be reviewed by a human before relying on it (it currently qualifies as `"text"` under the >=50-char rule despite being noise, not prose).

## STEP 4b -- extraction integrity vs the STEP 0 reference paste

Reference windows located by reading the paste directly around this book's own running-header markers (`CHAPTER VII.` / `NN Cheiro's Language of the Hand.` / `The Line of Head. NN` / `The Line of Heart. NN`), 1-indexed inclusive line ranges into `cheiro_pdf_fulltext.md`: {145: (944, 955), 146: (956, 965), 147: (966, 981), 148: (982, 991), 159: (1049, 1070)}. Agreement confirms faithful extraction, NOT book-correctness -- e.g. "Boliemianism" is itself an OCR-era misprint/garble of "Bohemianism" already present in this book's own text layer, not something this check can detect as wrong.

| printed_page | token | pdfplumber (new entry) | reference paste (window) | agree |
|---|---|---|---|---|
| 145 | crisis | MISSING | MISSING | agree |
| 145 | Plate XIII | PASS | PASS | agree |
| 145 | music | MISSING | MISSING | agree |
| 145 | Boliemianism | MISSING | MISSING | agree |
| 146 | crisis | PASS | PASS | agree |
| 146 | Plate XIII | MISSING | MISSING | agree |
| 146 | music | PASS | PASS | agree |
| 146 | Boliemianism | PASS | PASS | agree |
| 147 | crisis | MISSING | MISSING | agree |
| 147 | Plate XIII | MISSING | MISSING | agree |
| 147 | music | PASS | PASS | agree |
| 147 | Boliemianism | MISSING | MISSING | agree |
| 148 | crisis | MISSING | MISSING | agree |
| 148 | Plate XIII | MISSING | MISSING | agree |
| 148 | music | MISSING | MISSING | agree |
| 148 | Boliemianism | MISSING | MISSING | agree |
| 159 | crisis | MISSING | MISSING | agree |
| 159 | Plate XIII | MISSING | MISSING | agree |
| 159 | music | MISSING | MISSING | agree |
| 159 | Boliemianism | MISSING | MISSING | agree |

0 disagreement(s): none.

## STEP 4c -- stats

- Total pages: **310**
- #text: **201**
- #diagram: **109**
- #failed (extract_text() raised): **0** 
