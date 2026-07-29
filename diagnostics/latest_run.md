S81 OPEN — Astro Agent. Corpus loss attribution closed; F4 remediation arc.

MODEL: Opus for architecture rulings and 9-agent deliberation.
Sonnet 4.6 for Claude Code implementation. Haiku 4.5 for read-only metadata probes.

=== ONE-LINE STATE ===
S80 found the corpus loss is NOT primarily text corruption. It is F4: pdf_processor.py
discards OCR text for pages classified "mixed", and classify_page() misclassifies ordinary
astrology prose as "mixed" because PLANET_MATCH_THRESHOLD over-fires on planet-dense text.
416/416 Jyotish Lal Kitab empty pages are 100% page_type="mixed", 100% have native text.
Fully recoverable at zero API cost.

=== ARCHITECTURE RULINGS (LOCKED IN S80) ===
- PATH C RETIRED. In-place text replacement in frozen chunks. Killed by C2=210
  native-corrupt tokens (blind "prefer native" would inject errors) and by 322 mid-page
  C5a prose tokens requiring INSERTION into frozen boundaries.
- PATH D LOCKED, CHEIRO-FIRST. Re-ingest from native text, boundaries seeded from existing
  chunk spans, zero-chunk pages created fresh, F2/F4/F6/F7 fixed at source, pipeline becomes
  the reproducible source of truth. Cheiro is the pilot ONLY because it holds the sole
  labelled eval set (Ring 3). It is not the biggest win.
- OPTION C CHUNKING (user ruling): chunking strategy PLUGGABLE — paragraph-boundary vs
  fixed-window-with-overlap — decided by U4 A/B retrieval comparison, not by argument.
- SEED ACCEPTANCE FLOOR 0.90. Justification: Cheiro match_ratio p10=0.934, median=0.975;
  0.90 sits just below p10 so it rejects only the broken tail. Chunks below it are NOT
  discarded — boundary interpolated from sibling spans. SCOPE GUARD: Cheiro only; every
  other book needs its own distribution measured. TUNING NOTE: re-derive after U4; if
  interpolation fires on >10% of a book's chunks, the floor is wrong for that book's OCR
  quality, not a reason to lower it globally.
- F4 FIX IS SEPARABLE FROM PATH D. It is a branch fix plus targeted re-ingest of affected
  pages. Do not couple it to the Cheiro rebuild. Ship it first.

=== RULINGS I RETRACTED IN S80 — DO NOT RE-INHERIT THE ORIGINALS ===
1. "F5 FALSIFIED, U6 removed" — WRONG. Falsified for the NATIVE path only. strip_devanagari
   operates on TESSERACT output and DELETES Devanagari >=0.25 by explicit Session-2 design.
   CONFIRMED on the OCR path. U6 restored, rescoped.
2. "Tesseract language mismatch" hypothesis — DEAD. OCR ran eng+hin, hin installed and
   verified. Never re-test OCR language configs.
3. "translator.py is dead code, delete it" — WRONG. It is MIS-ORDERED. Module order is
   chunker -> translator; strip_devanagari deletes at >=0.25 exactly what translator's
   >=0.25 guard was built to catch. Mutually exclusive by construction. Verified:
   original_hindi populated ZERO times in progress JSON or ChromaDB. It never translated
   anything in production. Hasta Samudrika and Jataka Parijata were declared "translated" on
   a HARDCODED language="eng" field. Working Style #5 failure that shipped.
4. GATE 1 "67.8% seeding viability" — denominator error, corrected to 166/180 = 92.2% over
   MAPPED pages. 65 pages were never span-mapped.
5. U1c GATE "42.2%" — measured PRECISION when RECALL is the meaningful quantity. Chunks hold
   multiple paragraphs, so precision was capped near 47% before the run. U1d recall recompute
   SPECIFIED BUT NEVER RUN. Deferred, low priority now.

=== DEFECT REGISTER ===
F1  native text layer never read                    — 5,354 text pages. Fixed by Path D.
F2  classify_page routes on Tesseract output        — circular. ROOT CAUSE of F4 trigger.
F3  GPT-4o diagram fill ran for 1 of 15 books       — 370 pages never filled. Open.
F4  mixed excluded from both branches, text=""      — CONFIRMED DOMINANT CAUSE. See below.
F5  strip_devanagari mass deletion                  — CONFIRMED on OCR path. Native: N/A.
F6  no whitespace normalization                     — all books. Open.
F7  embed filter non-empty only, no min length      — 11 folio-only chunks confirmed in Cheiro.
F8  support floor 0.30 near noise; bare substring   — all retrieval. Open, R2-threshold.
F9  MULTI-COLUMN LAYOUT UNHANDLED (new, S80)        — Deva-keralam bimodal 5/5. Sampled only
    POPULATED pages = selection bias. NOT CLEARED. Suspect Phaladeepika, Saravali,
    Sarvartha-Chintamani, Jataka Parijata (Sanskrit+commentary editions are conventionally
    two-column).
F10 TWO-PAGE SPREADS UNSPLIT (new, S80)             — split_spreads=False never verified for
    the 9-book overnight batch. Session 2's "all 5 confirmed single-page" covered BPHS x2,
    Phaladeepika, Saravali, Cheiro only. Hasta Samudrika is a PHOTOGRAPH of an open book:
    two facing pages per PDF page, spine shadow, curved lines.

=== F4 MECHANISM, FULLY TRACED IN SOURCE (S80) ===
classify_page() PLANET_MATCH_THRESHOLD over-fires on planet-dense narrative prose
  -> page labelled "mixed"
  -> pdf_processor.py discards the OCR text for mixed pages
  -> image_extractor.py refills only "diagram" pages, never "mixed"
  -> embedder.py skips empty text
  -> page vanishes from the corpus.
Sample false-positive rate: 10/10 Lal Kitab pages were plain narrative misclassified mixed.
Design intent (Session 1 record) was that mixed pages KEEP their text AND also get an image
pass. The text-retention half was never built. The image half was never run on mixed pages.

=== RECOVERY LEDGER ===
NATIVE-RECOVERABLE, ZERO API COST:
  Jyotish Lal Kitab   416 pages, 100% mixed, 100% native text present  <- largest single win
  Cheiro               65 zero-chunk pages
  BPHS-1 / BPHS-2     165 + 162, 100% native eligible
  Phaladeepika / Saravali — same F4 pattern confirmed; note 0.0 native eligibility, so
  recovery is via OCR text retention, not native extraction.
TWO-COLUMN (F9): Deva-keralam, Sarvartha-Chintamani + suspects above. Local OCR config work.
EFFECTIVELY LOST: Hasta Samudrika Shastra (photograph, spreads, pure Devanagari, zero
  English — needs split + dewarp + Devanagari OCR + translate; four unbuilt stages for one
  book). Likely Jataka Parijata. RECOMMENDATION: re-source English editions or accept loss.
  Cheiro carries palm for V1.1 regardless.

=== S81 FIRST ACTION ===
Corpus-wide page_type census. METADATA ONLY from data/progress/*.json — no OCR, no
rasterization, no PDF opening. Haiku 4.5. Minutes.
Purpose: size F4 across all 22 books before fixing anything. Per book: page count, and counts
of page_type text / diagram / mixed / absent, cross-tabulated against whether that page has
live corpus chunks. The number that matters: of the 1,361 corpus-wide empty pages, how many
are page_type="mixed". If that fraction is high, F4 is the single dominant defect and the fix
is one branch.
ONE PROMPT, ONE TASK. Do not fix classify_page in the same prompt. Do not re-ingest.

=== THEN, IN ORDER, GATED ===
1. F4 remediation design (Opus, 9-agent): mixed-branch text retention + PLANET_MATCH_THRESHOLD
   re-derivation under THRESHOLD DISCIPLINE. Threshold must be derived from the measured
   planet-keyword density distribution across text vs genuine-diagram pages, with scope guard
   and tuning note. Not chosen.
2. Targeted re-ingest of F4-affected pages, ONE BOOK AT A TIME, Lal Kitab first.
3. Path D Cheiro pilot: boundary seeder, shadow collection, U4 A/B gate.
   IF RETRIEVAL DOES NOT IMPROVE AT U4, PATH D IS WRONG AND WE STOP.
4. F9 column handling. 5. F5/translator pipeline reorder or removal decision. 6. F3 vision fill.

=== OUTSTANDING HOUSEKEEPING ===
- scripts/corpus_loss_attribution_S80.py UNCOMMITTED, awaiting ratification.
- diagnostics/corpus_export_cheiro_S79.jsonl untracked, deferred (463-chunk dump).
- CLAUDE.md CORRECTIONS PENDING (docs commit, no code):
  (a) accepted-gap (c): p157-158 is a PLATE SPREAD, not a doctrine gap. Heart-line doctrine
      complete. Correct the inference, keep the observation.
  (b) F1-F10 register with the S80 status of each.
  (c) T4 / V1-PALM-DROPPED (S71): evidence base COMPROMISED — every Ring 3 pass scored
      against a corpus with F1-F7 active. PENDING RE-ADJUDICATION. Do not reopen before U5.
  (d) Chunk Metadata Schema is ASPIRATIONAL not descriptive: text_sha256 is declared in the
      locked schema but ABSENT from live corpus data. The S23 embedder idempotency guard has
      therefore never run against production data. Any A/B harness must not assume both
      collections carry the same fields.
  (e) Working Style #7 says "all 6 agents"; the roster is 8 (architect, business, critic, qa,
      ui_ux, debate + Ephemeris Auditor, Validation Source per S19). S19 calls it 9. The 9th
      is documented nowhere. Reconcile or rename.
  (f) SESSION_LOG 3302 is stale prose; 3304 was S78's real commit-time count. Current baseline
      3341 (3304 + 37 U0 tests).
- data/test_images/ holds three real hand photos, tracked, PUBLIC repo. Decide.
- tests/test_palm_endtoend.py test 4 makes real GPT-4o vision calls in the suite. Marker it.
- data/chroma_db and data/pdfs untracked — corpus unreproducible from a fresh clone. Path D
  is the fix; until then this is the standing top risk.

=== PROVIDER AGNOSTICISM (raised S80, deferred to V1.1) ===
Embeddings CANNOT move off OpenAI (Anthropic has no embedding endpoint; changing model
invalidates _SUPPORT_SCORE_FLOOR). Movable: GPT-4o vision fill (low risk, human-gated),
GPT-4o-mini translation (likely removable entirely), calc_router Stage 2 (real risk — locked
golden scorecard). Correct fix is an LLM client abstraction + pinned model ids in config +
golden set parameterised by provider. NOT funded by the subscription extra-usage balance —
that pool does not cover API-key calls. Separate Console balance required.

=== CONFIRM AT OPEN ===
- git log origin/main..HEAD --oneline — expected empty
- HEAD hash: [Sulabh to fill] (S80 closed at d2623ff)
- Full suite: expect 3341 passed / 0 failed / 7 skipped / 1 xpassed
- Confirm scripts/corpus_loss_attribution_S80.py still uncommitted in the working tree