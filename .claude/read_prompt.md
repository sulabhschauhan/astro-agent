# Read Prompt

#Paste your instructions here. Then tell Claude: Read .claude/read_prompt.md and execute

MODEL: Haiku 4.5

TASK (one task only): Append two session blocks to SESSION_LOG.md. Docs-only.

=== TOKEN DISCIPLINE — BINDING ===
- Do NOT read, cat, view, grep, head, or tail SESSION_LOG.md. Not before, not after.
- Do NOT run git log / git show / git diff / git blame. Every hash below is verified.
- Do NOT run pytest. Docs-only; the suite cannot be affected.
- Do NOT summarize or echo file contents back to me.
- Verify ONLY via the script's own printed integers.
- Final reply: max 8 lines.

=== METHOD ===
Write the block below to a temp file, then append via Python (NOT `>>`).
SESSION_LOG.md does not end with a newline — a bare `>>` fuses the new
heading onto the last line. The script must handle this.

import pathlib
p = pathlib.Path("SESSION_LOG.md")
before = p.stat().st_size
old = p.read_text(encoding="utf-8")
new = pathlib.Path("/tmp/s79_s80_block.md").read_text(encoding="utf-8")
assert "## S79 —" not in old, "S79 block already present — STOP, report, change nothing"
assert "## S80 —" not in old, "S80 block already present — STOP, report, change nothing"
sep = "" if old.endswith("\n\n") else ("\n" if old.endswith("\n") else "\n\n")
p.write_text(old + sep + new, encoding="utf-8")
print("bytes_before", before, "bytes_after", p.stat().st_size,
      "delta", p.stat().st_size - before)

Wrap in try/except; on failure print the exception and the file's byte size,
change nothing further, stop.

=== BLOCK TO APPEND (verbatim, no edits, no reflow) ===
## S79 — Corpus integrity arc opened; F1-F8 register; Path C selected (2026-07-29)

Opened as palm Q&A routing architecture. SUSPENDED at open: the routing problem is
downstream of a corpus defect. Investigation only, no production code touched.

Commits: 181965d (R1-P0 page triage — SUPERSEDED, global off-by-one page index bug;
corrected re-run OUTSTANDING, deferred), 3178fdc (native text probe). HEAD at close 3178fdc.
Diagnostics: e2g_preflight_S79.md, corpus_export_S79.md, native_text_probe_S79.md,
r1_p0_page_triage_S79.md (superseded), corpus_export_cheiro_S79.jsonl (463 Cheiro chunks,
held untracked at S79 close, landed later in 162539e).

ROOT FINDING. The ingestion pipeline discards each PDF's native embedded text layer and
re-OCRs with Tesseract. ~104 corruption tokens corpus-wide, incl. systematic line->hne and
life->hfe. These directly cause the retrieval failures seen across Ring 3 passes 3/4/5.
Verified by the user copy-pasting a suspect glyph straight out of the PDF.

TWO LONG-CARRIED FINDINGS CLOSED.
- Heart-line corpus gap CLOSED. PDF p157/p158 are Plate XVIII plus its blank verso — a
  plate spread, not missing doctrine. Carried as an accepted gap for six sessions on a
  wrong inference. Doctrine is complete.
- Fate-line "barely visible" re-diagnosed: NOT a corpus gap. p165_c2 exists; p163_c1
  (origin doctrine) simply outranks it. Query-to-chunk vocabulary mismatch.

CENSUS. 1,361 of 7,357 pages (18.5%) carry empty text. Six classical chart sources lose
26-53% of pages via a `mixed` page-type handler that was designed and never implemented.
Three books effectively blank while classified ingested: LAL KITAB-1941, Hasta Samudrika
Shastra, Jataka Parijata. Hasta Samudrika Shastra is the Indian palmistry classic — palm
readings ground exclusively on Cheiro by accident, not design.

RULINGS.
1. Vision-fill chunks are citation-ineligible until human-verified; `text_source` stamped
   in chunk metadata.
2. S79 re-scoped to corpus integrity; palm Q&A routing deferred.
3. S71 V1-palm-drop: evidence base COMPROMISED — every Ring 3 pass was scored against a
   corpus with F1-F7 active. PENDING RE-ADJUDICATION at U5. Do not reopen before U5.
4. PATH C SELECTED — freeze chunk boundaries and ids, replace only the text inside each
   chunk with the aligned native span. Chosen over full re-ingest (breaks all Ring 3 rubric
   anchors) and enumerated token repair (fixes only known corruptions). RETIRED at S80.
5. U0-U7 staged ladder designed; hard stop at U4 if A/B retrieval does not improve.
6. R2 SPLIT. R2-structural (bigram needle not bare substring, `low_visibility` third state
   in _is_absence, deterministic doctrinal lexicon expansion — not HyDE, propagate
   validate_palm_image.quality into Stage 1) runs parallel with U0-U2, text-quality-
   independent. R2-threshold (0.30 floor re-derivation, NLI calibration) waits for U4.
7. E-3 replacement queued post-U4, in order: quote-anchored extraction (Stage 1 emits
   verbatim evidence_quote, gate checks the span as a normalized substring, claim_text
   paraphrases freely — retires the "Medium" vs "Medium relative" class with no threshold
   at all), then NLI entailment WITH a polarity check. Not embedding cosine: cosine is
   topicality and would pass both p145_c0 and p139_c0.

CONVENTIONS REINFORCED. Every Code prompt: durable topic file + overwrite
diagnostics/latest_run.md + push topic file only; no RATIFIED token for diagnostics-only
commits. Every read-only probe carries four ground-truth self-check assertions and fails
loudly. diagnostics/latest_run.md is overwrite-only scratch, never a citation target. Repo
sulabhschauhan/astro-agent is PUBLIC and clonable for design-chat access — stop pasting
file contents.

## S80 — F4 confirmed dominant cause; PATH C RETIRED, PATH D LOCKED (2026-07-29)

Commits (12, all pushed): c4efca7 U0 golden fixture diagnostics + Path C census + F5
falsified on native path · b497c8d U0 fixture generator + tests · 166d8ee U0.5
bidirectional OCR-corruption census (Cheiro) · ec30ef1 U0.5 script + machine-readable
sidecar · 6fec8bf U0.6 C5 decomposition + augmented-oracle delta (Cheiro) · f2cc395 U0.6
script · 66125c6 chunk-id coupling census, repo-wide · b55933a U1 chunk-to-native span
mapping probe (Cheiro) · fb82213 U1 script · cbf6450 U1 correction + U1b pathology triage
(Cheiro) · 56ad4e3 U1b script · 6e69b73 U1c layout-based paragraph recovery probe (Cheiro).
HEAD at close d2623ff.

Suite 3304 baseline -> 3341 passed / 0 failed / 7 skipped / 1 xpassed (+37 U0 tests). The
3302-vs-3304 discrepancy is RESOLVED: 3302 was stale SESSION_LOG prose, 3304 was S78's real
commit-time count, confirmed independently as 3341 - 37.

ROOT FINDING — F4, NOT TEXT CORRUPTION. pdf_processor.py discards the OCR text for pages
classified "mixed", and classify_page() misclassifies ordinary astrology prose as "mixed"
because PLANET_MATCH_THRESHOLD over-fires on planet-dense text. Traced in source end to
end: classify_page over-fires -> page labelled "mixed" -> pdf_processor discards its OCR
text -> image_extractor refills only "diagram" pages, never "mixed" -> embedder skips empty
text -> page vanishes from the corpus. Sample false-positive rate 10/10 Lal Kitab pages
were plain narrative. Session 1's design intent was that mixed pages KEEP text AND get an
image pass; the text-retention half was never built, the image half never ran on mixed
pages. 416/416 Jyotish Lal Kitab empty pages are 100% page_type="mixed" and 100% have
native text present. Fully recoverable at zero API cost.

ARCHITECTURE RULINGS.
- PATH C RETIRED. Killed by C2=210 native-corrupt tokens (a blind "prefer native" rule
  would inject errors) and by 322 mid-page C5a prose tokens requiring INSERTION into frozen
  chunk boundaries.
- PATH D LOCKED, CHEIRO-FIRST. Re-ingest from native text, boundaries seeded from existing
  chunk spans, zero-chunk pages created fresh, F2/F4/F6/F7 fixed at source, pipeline becomes
  the reproducible source of truth. Cheiro is the pilot ONLY because it holds the sole
  labelled eval set (Ring 3). It is not the biggest win.
- OPTION C CHUNKING (user ruling): chunking strategy PLUGGABLE — paragraph-boundary vs
  fixed-window-with-overlap — decided by U4 A/B retrieval comparison, not by argument.
- SEED ACCEPTANCE FLOOR 0.90. JUSTIFICATION: Cheiro match_ratio p10=0.934, median=0.975;
  0.90 sits just below p10 so it rejects only the broken tail. Sub-floor chunks are NOT
  discarded — boundary interpolated from sibling spans. SCOPE GUARD: Cheiro only; every
  other book needs its own distribution measured. TUNING NOTE: re-derive after U4; if
  interpolation fires on >10% of a book's chunks the floor is wrong for that book's OCR
  quality, not a reason to lower it globally.
- F4 FIX IS SEPARABLE FROM PATH D — a branch fix plus targeted re-ingest of affected pages.
  Do not couple it to the Cheiro rebuild. Ship it first.

RETRACTIONS — DO NOT RE-INHERIT THE ORIGINALS.
1. "F5 falsified, U6 removed" — WRONG. Falsified for the NATIVE path only. strip_devanagari
   operates on TESSERACT output and DELETES Devanagari >=0.25 by explicit Session-2 design.
   CONFIRMED on the OCR path. U6 restored, rescoped.
2. "Tesseract language mismatch" — DEAD. OCR ran eng+hin, hin installed and verified. Never
   re-test OCR language configs.
3. "translator.py is dead code, delete it" — WRONG. It is MIS-ORDERED. Module order is
   chunker -> translator; strip_devanagari deletes at >=0.25 exactly what translator's
   >=0.25 guard was built to catch. Mutually exclusive by construction. Verified:
   original_hindi populated ZERO times in progress JSON or ChromaDB — it never translated
   anything in production. Hasta Samudrika and Jataka Parijata were declared "translated" on
   a HARDCODED language="eng" field. Working Style #5 failure that shipped.
4. GATE 1 "67.8% seeding viability" — denominator error. Corrected to 166/180 = 92.2% over
   MAPPED pages; 65 pages were never span-mapped.
5. U1c gate "42.2%" — measured PRECISION where RECALL is the meaningful quantity. Chunks
   hold multiple paragraphs, so precision was capped near 47% before the run. U1d recall
   recompute SPECIFIED BUT NEVER RUN. Deferred, low priority.

U0 FIXTURE DEVIATIONS (documented, not silently forced).
- Corpus-wide scan of all 22 PDFs found ZERO Devanagari codepoints in any native text layer
  — the LAL KITAB Devanagari-orphan defect class is falsified on the native path, not merely
  unverified. Fixture 5 became a Path-C-boundary case instead: Deva-keralam project page
  102, 0 native chars, 3760 live corpus chars across 6 chunks, entirely Tesseract-sourced
  with no native source to align a future repair against.
- Cheiro p156 native text is "rnensal", not "mensal" — a real archive.org ligature artifact.
  The corpus's Tesseract OCR got this one right.
- p90 is no longer an empty-corpus page (re-ingested since the earlier diagnostic) —
  substituted p191. PDF count corrected 19 -> 22.
- New artifact tests/fixtures/native_coverage_S80.json censuses all 22 PDFs. Of the five
  named worst-hit books, only Phaladeepika and Saravali are actually Path-C-ineligible
  (0.0); Jyotish Lal Kitab 0.9987, BPHS-1 and BPHS-2 1.0000 are highly eligible — flagged
  rather than silently reconciled.

NEW DEFECTS.
F9 MULTI-COLUMN LAYOUT UNHANDLED — Deva-keralam bimodal 5/5. Sampled only POPULATED pages =
selection bias. NOT CLEARED. Suspects: Phaladeepika, Saravali, Sarvartha-Chintamani, Jataka
Parijata (Sanskrit+commentary editions are conventionally two-column).
F10 TWO-PAGE SPREADS UNSPLIT — split_spreads=False never verified for the 9-book overnight
batch. Session 2's "all 5 confirmed single-page" covered BPHS x2, Phaladeepika, Saravali,
Cheiro only. Hasta Samudrika is a PHOTOGRAPH of an open book: two facing pages per PDF page,
spine shadow, curved lines.

RECOVERY LEDGER.
Native-recoverable at zero API cost: Jyotish Lal Kitab 416 pages (largest single win),
Cheiro 65 zero-chunk pages, BPHS-1 165 + BPHS-2 162 at 100% native eligibility.
Phaladeepika / Saravali show the same F4 pattern but 0.0 native eligibility, so recovery is
via OCR text retention, not native extraction. Two-column (F9): Deva-keralam,
Sarvartha-Chintamani + suspects. EFFECTIVELY LOST: Hasta Samudrika Shastra — photograph,
spreads, pure Devanagari, zero English; needs split + dewarp + Devanagari OCR + translate,
four unbuilt stages for one book. Likely Jataka Parijata. RECOMMENDATION: re-source English
editions or accept the loss. Cheiro carries palm for V1.1 regardless.

PROVIDER AGNOSTICISM (raised S80, deferred to V1.1). Embeddings CANNOT move off OpenAI —
Anthropic has no embedding endpoint, and changing model invalidates _SUPPORT_SCORE_FLOOR.
Movable: GPT-4o vision fill (low risk, human-gated), GPT-4o-mini translation (likely
removable entirely), calc_router Stage 2 (real risk — locked golden scorecard). Correct fix
is an LLM client abstraction + pinned model ids in config + golden set parameterised by
provider. NOT funded by the subscription extra-usage balance — that pool does not cover
API-key calls; a separate Console balance is required.

CARRY-FORWARD TO S81, gated, in order. (1) Corpus-wide page_type census, metadata only —
size F4 across all 22 books before fixing anything. (2) F4 remediation design (Opus,
9-agent): mixed-branch text retention + PLANET_MATCH_THRESHOLD re-derivation from the
measured planet-keyword density distribution across text vs genuine-diagram pages, with
scope guard and tuning note. Derived, not chosen. (3) Targeted re-ingest of F4-affected
pages, ONE BOOK AT A TIME, Lal Kitab first. (4) Path D Cheiro pilot: boundary seeder, shadow
collection, U4 A/B gate — IF RETRIEVAL DOES NOT IMPROVE AT U4, PATH D IS WRONG AND WE STOP.
(5) F9 column handling. (6) F5/translator pipeline reorder-or-remove decision. (7) F3 vision
fill.

HOUSEKEEPING OPEN AT S81. data/test_images/ holds three real hand photos, tracked, PUBLIC
repo — decide. tests/test_palm_endtoend.py test 4 makes real GPT-4o vision calls in the
suite — marker it. data/chroma_db and data/pdfs untracked, corpus unreproducible from a
fresh clone — Path D is the fix; standing top risk until then.

RESOLVED BY 162539e. Every file held untracked at S80 close is now on origin/main:
scripts/corpus_loss_attribution_S80.py, scripts/build_golden_fixtures_S80.py,
tests/test_golden_fixtures_S80.py, tests/fixtures/golden_S80.json,
tests/fixtures/native_coverage_S80.json, diagnostics/corpus_export_cheiro_S79.jsonl.
=== END BLOCK ===

COMMIT: docs-only, Working Style #14 exempt. Message:
  docs(session-log): S79 + S80 blocks — corpus integrity arc, F4 attribution, Path D lock
Push. Report: the three integers, the commit hash, nothing else.