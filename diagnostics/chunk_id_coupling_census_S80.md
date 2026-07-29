# CHUNK-ID COUPLING CENSUS — S80 — Cheiro-neutral, repo-wide

Pure static text analysis. No PDFs, no ChromaDB, no network, no production imports, no repair logic. Scope: agent/, tests/, diagnostics/, .claude/, docs/, scripts/, frontend/, and *.md files at repo root. data/ and .git excluded per instruction; ingestion/ (pdf_processor.py/chunker.py/embedder.py/query_engine.py) excluded because it was not named in the instructing prompt's own inclusion list -- noted here rather than silently scanned or silently assumed empty.

Files scanned: 329. Files skipped: 3 (see end of report).

---

## (a) Totals — literal chunk-id occurrences

- **Full chunk-id-shaped matches** (`<book_name>_p<digits>_c<digits>`): **4946** occurrences, **4065** distinct ids.
- **Bare page-anchor matches** (`p<digits>_c<digits>`, no book prefix), counted SEPARATELY: **224** occurrences, **32** distinct anchors.

**Methodology note on multi-word book names:** the regex's book_name prefix (`[A-Za-z0-9_.\-]+`) does not match spaces, so for a book whose real name contains spaces (e.g. "Hasta Samudrika Shastra ... Janata Prakashan"), only the trailing contiguous word before `_p<n>_c<n>` is captured as the "id" (e.g. `Prakashan_p92_c0`), not the full book name. This is intentional, per the instruction to match on shape rather than a known-id list — it means table (e)'s distinct-id list contains some ids that are really fragments of a longer, space-containing book name, most visibly inside `diagnostics/targeted_delete_plan_20260621_120557.json` (which is entirely made of such fragment-style ids, 3945 of them). Section (f) below covers the full,  un-fragmented book-name strings directly.

---

## (b) Breakdown by file — full chunk-ids, sorted descending by occurrence count

| Path | Occurrences | Distinct ids | Classification |
|---|---|---|---|
| diagnostics/targeted_delete_plan_20260621_120557.json | 3945 | 3945 | rubric or diagnostic markdown (non-.md artifact) |
| diagnostics/fh_stage1_probe_S69.md | 181 | 14 | rubric or diagnostic markdown |
| diagnostics/fc_retrieval_probe_S68.md | 126 | 47 | rubric or diagnostic markdown |
| diagnostics/archive/dogfood_capture_pre_S70_pass5.md | 99 | 18 | rubric or diagnostic markdown |
| diagnostics/ring3_evidence_S68_pass4.md | 96 | 14 | rubric or diagnostic markdown |
| diagnostics/pass5_preflight_S70.md | 64 | 28 | rubric or diagnostic markdown |
| scripts/probe_fh_stage1_extraction.py | 57 | 14 | production code (diagnostic/probe script, NOT app-serving; excluded from the agent/frontend gate by directory, see note) |
| diagnostics/e2f_retrieval_topk.md | 43 | 25 | rubric or diagnostic markdown |
| diagnostics/dogfood_capture.md | 38 | 11 | rubric or diagnostic markdown |
| diagnostics/ring3_chunks_S67_pass3.md | 35 | 33 | rubric or diagnostic markdown |
| diagnostics/fc_heartline_corpus_S68.md | 31 | 15 | rubric or diagnostic markdown |
| diagnostics/path_c_validation_20260621_173724.md | 27 | 18 | rubric or diagnostic markdown |
| diagnostics/post_delete_saturn11_retrieval_20260621_130514.md | 25 | 9 | rubric or diagnostic markdown |
| tests/interpretive/test_palm_reading.py | 24 | 9 | test assertion |
| diagnostics/chunking_code_audit_20260621_092249.md | 20 | 11 | rubric or diagnostic markdown |
| diagnostics/targeted_delete_dryrun_20260621_120557.md | 20 | 10 | rubric or diagnostic markdown |
| diagnostics/dogfood_capture_pre_s78.md | 18 | 9 | rubric or diagnostic markdown |
| diagnostics/post_delete_dup_recheck_20260621_130108.md | 13 | 13 | rubric or diagnostic markdown |
| tests/fixtures/golden_S80.json | 9 | 9 | test fixture or stub |
| diagnostics/chromadb_dup_report_20260621_080119.md | 8 | 7 | rubric or diagnostic markdown |
| diagnostics/post_delete_saturn11_retrieval.py | 8 | 8 | rubric or diagnostic markdown (non-.md artifact) |
| tests/test_app_dogfood_capture.py | 8 | 2 | test assertion |
| diagnostics/ring3_chunks_S66_pass2.md | 7 | 7 | rubric or diagnostic markdown |
| diagnostics/ring3_chunks_S66.md | 6 | 6 | rubric or diagnostic markdown |
| diagnostics/ring3_palm_rubric_S70_pass5.md | 5 | 5 | rubric or diagnostic markdown |
| diagnostics/provenance_audit_20260621_100237.md | 4 | 4 | rubric or diagnostic markdown |
| scripts/probe_fc_retrieval.py | 4 | 2 | production code (diagnostic/probe script, NOT app-serving; excluded from the agent/frontend gate by directory, see note) |
| agent/interpretive/palm_reading.py | 3 | 2 | production code |
| diagnostics/embedder_hardening_proposal_20260621_100850.md | 3 | 1 | rubric or diagnostic markdown |
| diagnostics/ring3_palm_rubric_S68_pass4.md | 3 | 2 | rubric or diagnostic markdown |
| diagnostics/run_single_book_validation_proposal_20260621_113829.md | 3 | 3 | rubric or diagnostic markdown |
| diagnostics/targeted_delete_dryrun.py | 3 | 2 | rubric or diagnostic markdown (non-.md artifact) |
| diagnostics/e2g_preflight_S79.md | 2 | 2 | rubric or diagnostic markdown |
| SESSION_LOG.md | 2 | 2 | docs |
| CLAUDE.md | 1 | 1 | docs |
| diagnostics/targeted_delete_execute_20260621_121046.md | 1 | 1 | rubric or diagnostic markdown |
| scripts/probe_fc_heartline_corpus.py | 1 | 1 | production code (diagnostic/probe script, NOT app-serving; excluded from the agent/frontend gate by directory, see note) |
| scripts/probe_neutral_chunk_valence.py | 1 | 1 | production code (diagnostic/probe script, NOT app-serving; excluded from the agent/frontend gate by directory, see note) |
| tests/test_context_integration.py | 1 | 1 | test assertion |
| tests/test_embedder.py | 1 | 1 | test assertion |

### Bare page-anchor breakdown by file (separate count, per instruction)

| Path | Occurrences | Distinct anchors | Classification |
|---|---|---|---|
| tests/interpretive/test_claim_extraction.py | 56 | 5 | test assertion |
| diagnostics/ring3_palm_rubric_S68_pass4.md | 46 | 14 | rubric or diagnostic markdown |
| SESSION_LOG.md | 27 | 13 | docs |
| diagnostics/e2f_retrieval_topk.md | 17 | 4 | rubric or diagnostic markdown |
| diagnostics/fh_stage1_probe_S69.md | 13 | 2 | rubric or diagnostic markdown |
| diagnostics/ring3_palm_rubric_S67_pass3.md | 13 | 9 | rubric or diagnostic markdown |
| scripts/probe_neutral_chunk_valence.py | 11 | 3 | production code (diagnostic/probe script, NOT app-serving; excluded from the agent/frontend gate by directory, see note) |
| diagnostics/ring3_palm_rubric_S70_pass5.md | 10 | 6 | rubric or diagnostic markdown |
| CLAUDE.md | 9 | 4 | docs |
| scripts/probe_fh_stage1_extraction.py | 8 | 5 | production code (diagnostic/probe script, NOT app-serving; excluded from the agent/frontend gate by directory, see note) |
| diagnostics/e2g_preflight_S79.md | 7 | 4 | rubric or diagnostic markdown |
| agent/interpretive/palm_reading.py | 3 | 2 | production code |
| scripts/bidirectional_corruption_census_S80.py | 2 | 1 | production code (diagnostic/probe script, NOT app-serving; excluded from the agent/frontend gate by directory, see note) |
| diagnostics/bidirectional_corruption_census_S80.md | 1 | 1 | rubric or diagnostic markdown |
| scripts/probe_fc_heartline_corpus.py | 1 | 1 | production code (diagnostic/probe script, NOT app-serving; excluded from the agent/frontend gate by directory, see note) |

---

## (c) THE GATE NUMBER

- Occurrences in production code under agent/ or frontend/: **3**
- Occurrences in test files under tests/: **43**

**GATE NUMBER = 46**

(docs/, diagnostics/, .claude/, and scripts/ occurrences do NOT count toward this number, per instruction — stale ids in a report are harmless. scripts/ is excluded from the gate by directory regardless of how it is labeled in table (b)'s classification column.)

---

## (d) Test-file occurrences: ASSERTED VALUE vs STUB INPUT vs UNCERTAIN

Judged primarily via real AST parent-tracking (see the classification-method note below the counts table); marked UNCERTAIN rather than guessed where even that cannot resolve the usage. Scoped to FULL chunk-id occurrences only (matching (a)-(c)'s scope) — bare page-anchor occurrences are the separate count reported in table (b) and are not re-classified here.

| Usage | Count |
|---|---|
| ASSERTED VALUE | 7 |
| STUB INPUT | 35 |
| UNCERTAIN | 1 |

Classification method: real `ast`-parse with manual parent-tracking for every `.py` file under tests/ (an ancestor `ast.Assert` anywhere above the string constant -> ASSERTED VALUE; else an ancestor Call/Dict/Assign/keyword/List/Tuple/Set within 10 hops -> STUB INPUT; else UNCERTAIN) -- chosen over a line-proximity heuristic after that heuristic was directly caught mis-marking a real multi-line `assert ("..." "...") in content` statement in tests/test_app_dogfood_capture.py as UNCERTAIN. Line-heuristic fallback used only when ast.parse fails, or for occurrences with no enclosing string-literal AST node (e.g. inside a `#` comment).

<details><summary>Per-occurrence detail (click to expand)</summary>

| File | Line | Token | Usage | Method | Line text |
|---|---|---|---|---|---|
| tests/fixtures/golden_S80.json | 38 | cheiroslanguageo00chei_1_p156_c0 | STUB INPUT | line-heuristic-fallback (no matching AST constant found) | `"chunk_id": "cheiroslanguageo00chei_1_p156_c0",` |
| tests/fixtures/golden_S80.json | 43 | cheiroslanguageo00chei_1_p156_c1 | STUB INPUT | line-heuristic-fallback (no matching AST constant found) | `"chunk_id": "cheiroslanguageo00chei_1_p156_c1",` |
| tests/fixtures/golden_S80.json | 48 | cheiroslanguageo00chei_1_p156_c2 | STUB INPUT | line-heuristic-fallback (no matching AST constant found) | `"chunk_id": "cheiroslanguageo00chei_1_p156_c2",` |
| tests/fixtures/golden_S80.json | 95 | Deva-keralam_p102_c0 | STUB INPUT | line-heuristic-fallback (no matching AST constant found) | `"chunk_id": "Deva-keralam_p102_c0",` |
| tests/fixtures/golden_S80.json | 100 | Deva-keralam_p102_c1 | STUB INPUT | line-heuristic-fallback (no matching AST constant found) | `"chunk_id": "Deva-keralam_p102_c1",` |
| tests/fixtures/golden_S80.json | 105 | Deva-keralam_p102_c2 | STUB INPUT | line-heuristic-fallback (no matching AST constant found) | `"chunk_id": "Deva-keralam_p102_c2",` |
| tests/fixtures/golden_S80.json | 110 | Deva-keralam_p102_c3 | STUB INPUT | line-heuristic-fallback (no matching AST constant found) | `"chunk_id": "Deva-keralam_p102_c3",` |
| tests/fixtures/golden_S80.json | 115 | Deva-keralam_p102_c4 | STUB INPUT | line-heuristic-fallback (no matching AST constant found) | `"chunk_id": "Deva-keralam_p102_c4",` |
| tests/fixtures/golden_S80.json | 120 | Deva-keralam_p102_c5 | STUB INPUT | line-heuristic-fallback (no matching AST constant found) | `"chunk_id": "Deva-keralam_p102_c5",` |
| tests/interpretive/test_palm_reading.py | 540 | cheiroslanguageo00chei_1_p42_c1 | STUB INPUT | ast | `chunk_id="cheiroslanguageo00chei_1_p42_c1",` |
| tests/interpretive/test_palm_reading.py | 1563 | cheiroslanguageo00chei_1_p134_c2 | STUB INPUT | ast | `"[cheiroslanguageo00chei_1_p134_c2]"` |
| tests/interpretive/test_palm_reading.py | 1574 | cheiroslanguageo00chei_1_p134_c1 | STUB INPUT | ast | `"[cheiroslanguageo00chei_1_p134_c1][cheiroslanguageo00chei_1_p163_c3]"` |
| tests/interpretive/test_palm_reading.py | 1574 | cheiroslanguageo00chei_1_p163_c3 | STUB INPUT | ast | `"[cheiroslanguageo00chei_1_p134_c1][cheiroslanguageo00chei_1_p163_c3]"` |
| tests/interpretive/test_palm_reading.py | 1583 | cheiroslanguageo00chei_1_p999_c9 | STUB INPUT | ast | `text = "A claim citing a chunk that was never retrieved.[cheiroslanguageo00chei_1_p999_c9]"` |
| tests/interpretive/test_palm_reading.py | 1584 | cheiroslanguageo00chei_1_p134_c2 | STUB INPUT | ast | `valid_chunk_ids = frozenset({"cheiroslanguageo00chei_1_p134_c2"})` |
| tests/interpretive/test_palm_reading.py | 1590 | cheiroslanguageo00chei_1_p999_c9 | ASSERTED VALUE | ast | `"cheiroslanguageo00chei_1_p999_c9"` |
| tests/interpretive/test_palm_reading.py | 1598 | cheiroslanguageo00chei_1_p134_c2 | STUB INPUT | ast | `text = "A claim citing a stale, previously-valid chunk.[cheiroslanguageo00chei_1_p134_c2]"` |
| tests/interpretive/test_palm_reading.py | 1599 | cheiroslanguageo00chei_1_p163_c1 | STUB INPUT | ast | `valid_chunk_ids = frozenset({"cheiroslanguageo00chei_1_p163_c1"})` |
| tests/interpretive/test_palm_reading.py | 1605 | cheiroslanguageo00chei_1_p134_c2 | ASSERTED VALUE | ast | `"cheiroslanguageo00chei_1_p134_c2"` |
| tests/interpretive/test_palm_reading.py | 1610 | cheiroslanguageo00chei_1_p134_c2 | STUB INPUT | ast | `text = "A claim citing a genuinely gated chunk.[cheiroslanguageo00chei_1_p134_c2]"` |
| tests/interpretive/test_palm_reading.py | 1611 | cheiroslanguageo00chei_1_p134_c2 | STUB INPUT | ast | `valid_chunk_ids = frozenset({"cheiroslanguageo00chei_1_p134_c2"})` |
| tests/interpretive/test_palm_reading.py | 1628 | cheiroslanguageo00chei_1_p134_c2 | STUB INPUT | ast | `text = "A claim citing a chunk despite nothing being gated.[cheiroslanguageo00chei_1_p134_c2]"` |
| tests/interpretive/test_palm_reading.py | 1634 | cheiroslanguageo00chei_1_p134_c2 | ASSERTED VALUE | ast | `"cheiroslanguageo00chei_1_p134_c2"` |
| tests/interpretive/test_palm_reading.py | 1667 | cheiroslanguageo00chei_1_p134_c2 | STUB INPUT | ast | `chunk_id="cheiroslanguageo00chei_1_p134_c2",` |
| tests/interpretive/test_palm_reading.py | 1673 | cheiroslanguageo00chei_1_p134_c2 | STUB INPUT | ast | `"long life.[cheiroslanguageo00chei_1_p134_c2]"` |
| tests/interpretive/test_palm_reading.py | 1700 | cheiroslanguageo00chei_1_p200_c1 | STUB INPUT | ast | `_chunk(text="A broad, strong thumb.", chunk_id="cheiroslanguageo00chei_1_p200_c1"),` |
| tests/interpretive/test_palm_reading.py | 1716 | cheiroslanguageo00chei_1_p200_c1 | STUB INPUT | ast | `_chunk(text="A broad, strong thumb.", chunk_id="cheiroslanguageo00chei_1_p200_c1"),` |
| tests/interpretive/test_palm_reading.py | 1729 | cheiroslanguageo00chei_1_p200_c1 | STUB INPUT | ast | `_chunk(text="A broad, strong thumb.", chunk_id="cheiroslanguageo00chei_1_p200_c1"),` |
| tests/interpretive/test_palm_reading.py | 1732 | cheiroslanguageo00chei_1_p200_c1 | STUB INPUT | ast | `tagged_text = "The thumb is broad and strong.[cheiroslanguageo00chei_1_p200_c1]"` |
| tests/interpretive/test_palm_reading.py | 1746 | cheiroslanguageo00chei_1_p210_c3 | STUB INPUT | ast | `chunk_id="cheiroslanguageo00chei_1_p210_c3",` |
| tests/interpretive/test_palm_reading.py | 1752 | cheiroslanguageo00chei_1_p210_c3 | STUB INPUT | ast | `tagged_text = "The thumb is broad and strong.[cheiroslanguageo00chei_1_p210_c3]"` |
| tests/interpretive/test_palm_reading.py | 1763 | cheiroslanguageo00chei_1_p50_c1 | STUB INPUT | ast | `chunk_id="cheiroslanguageo00chei_1_p50_c1",` |
| tests/interpretive/test_palm_reading.py | 1767 | cheiroslanguageo00chei_1_p50_c1 | STUB INPUT | ast | `"quiet resolve.[cheiroslanguageo00chei_1_p50_c1]"` |
| tests/test_app_dogfood_capture.py | 166 | cheiroslanguageo00chei_1_p134_c2 | STUB INPUT | ast | `chunk_id="cheiroslanguageo00chei_1_p134_c2",` |
| tests/test_app_dogfood_capture.py | 177 | cheiroslanguageo00chei_1_p200_c1 | STUB INPUT | ast | `chunk_id="cheiroslanguageo00chei_1_p200_c1",` |
| tests/test_app_dogfood_capture.py | 284 | cheiroslanguageo00chei_1_p134_c2 | ASSERTED VALUE | ast | `"C1 \| life line \| cheiroslanguageo00chei_1_p134_c2 \| positive \| "` |
| tests/test_app_dogfood_capture.py | 293 | cheiroslanguageo00chei_1_p200_c1 | ASSERTED VALUE | ast | `"C2 \| fate line \| cheiroslanguageo00chei_1_p200_c1 \| positive \| "` |
| tests/test_app_dogfood_capture.py | 438 | cheiroslanguageo00chei_1_p134_c2 | STUB INPUT | ast | `chunk_id="cheiroslanguageo00chei_1_p134_c2",` |
| tests/test_app_dogfood_capture.py | 449 | cheiroslanguageo00chei_1_p200_c1 | STUB INPUT | ast | `chunk_id="cheiroslanguageo00chei_1_p200_c1",` |
| tests/test_app_dogfood_capture.py | 486 | cheiroslanguageo00chei_1_p134_c2 | ASSERTED VALUE | ast | `"C1 \| life line \| cheiroslanguageo00chei_1_p134_c2 \| positive \| "` |
| tests/test_app_dogfood_capture.py | 494 | cheiroslanguageo00chei_1_p200_c1 | ASSERTED VALUE | ast | `"C2 \| fate line \| cheiroslanguageo00chei_1_p200_c1 \| positive \| "` |
| tests/test_context_integration.py | 17 | BPHS_p1_c0 | STUB INPUT | ast | `"chunk_id": "BPHS_p1_c0",` |
| tests/test_embedder.py | 71 | Deva-keralam_p8_c0 | UNCERTAIN | ast | `"""Reproduces the documented Deva-keralam_p8_c0 / _c0_c0 failure mode:` |

</details>

---

## (e) Load-bearing anchors — distinct ids appearing in 3+ separate files

| Full id | # distinct files | Files |
|---|---|---|
| cheiroslanguageo00chei_1_p134_c1 | 14 | agent/interpretive/palm_reading.py, diagnostics/archive/dogfood_capture_pre_S70_pass5.md, diagnostics/dogfood_capture.md, diagnostics/dogfood_capture_pre_s78.md, diagnostics/fc_retrieval_probe_S68.md, diagnostics/fh_stage1_probe_S69.md, diagnostics/pass5_preflight_S70.md, diagnostics/ring3_chunks_S66.md, diagnostics/ring3_chunks_S66_pass2.md, diagnostics/ring3_chunks_S67_pass3.md, diagnostics/ring3_evidence_S68_pass4.md, diagnostics/ring3_palm_rubric_S70_pass5.md, scripts/probe_fh_stage1_extraction.py, tests/interpretive/test_palm_reading.py |
| cheiroslanguageo00chei_1_p98_c1 | 12 | diagnostics/archive/dogfood_capture_pre_S70_pass5.md, diagnostics/dogfood_capture.md, diagnostics/dogfood_capture_pre_s78.md, diagnostics/e2f_retrieval_topk.md, diagnostics/fc_retrieval_probe_S68.md, diagnostics/fh_stage1_probe_S69.md, diagnostics/pass5_preflight_S70.md, diagnostics/ring3_chunks_S67_pass3.md, diagnostics/ring3_evidence_S68_pass4.md, diagnostics/ring3_palm_rubric_S70_pass5.md, scripts/probe_fc_retrieval.py, scripts/probe_fh_stage1_extraction.py |
| cheiroslanguageo00chei_1_p145_c0 | 11 | CLAUDE.md, SESSION_LOG.md, diagnostics/archive/dogfood_capture_pre_S70_pass5.md, diagnostics/dogfood_capture.md, diagnostics/dogfood_capture_pre_s78.md, diagnostics/fh_stage1_probe_S69.md, diagnostics/ring3_chunks_S67_pass3.md, diagnostics/ring3_evidence_S68_pass4.md, diagnostics/ring3_palm_rubric_S70_pass5.md, scripts/probe_fh_stage1_extraction.py, scripts/probe_neutral_chunk_valence.py |
| cheiroslanguageo00chei_1_p160_c2 | 9 | diagnostics/archive/dogfood_capture_pre_S70_pass5.md, diagnostics/fc_heartline_corpus_S68.md, diagnostics/fc_retrieval_probe_S68.md, diagnostics/fh_stage1_probe_S69.md, diagnostics/pass5_preflight_S70.md, diagnostics/ring3_chunks_S67_pass3.md, diagnostics/ring3_evidence_S68_pass4.md, diagnostics/ring3_palm_rubric_S68_pass4.md, scripts/probe_fh_stage1_extraction.py |
| cheiroslanguageo00chei_1_p112_c0 | 9 | diagnostics/archive/dogfood_capture_pre_S70_pass5.md, diagnostics/dogfood_capture.md, diagnostics/dogfood_capture_pre_s78.md, diagnostics/fh_stage1_probe_S69.md, diagnostics/pass5_preflight_S70.md, diagnostics/ring3_chunks_S67_pass3.md, diagnostics/ring3_evidence_S68_pass4.md, diagnostics/ring3_palm_rubric_S70_pass5.md, scripts/probe_fh_stage1_extraction.py |
| cheiroslanguageo00chei_1_p139_c0 | 9 | diagnostics/archive/dogfood_capture_pre_S70_pass5.md, diagnostics/dogfood_capture.md, diagnostics/dogfood_capture_pre_s78.md, diagnostics/fc_retrieval_probe_S68.md, diagnostics/fh_stage1_probe_S69.md, diagnostics/ring3_chunks_S67_pass3.md, diagnostics/ring3_evidence_S68_pass4.md, diagnostics/ring3_palm_rubric_S70_pass5.md, scripts/probe_fh_stage1_extraction.py |
| cheiroslanguageo00chei_1_p163_c1 | 9 | diagnostics/archive/dogfood_capture_pre_S70_pass5.md, diagnostics/fh_stage1_probe_S69.md, diagnostics/pass5_preflight_S70.md, diagnostics/ring3_chunks_S66.md, diagnostics/ring3_chunks_S67_pass3.md, diagnostics/ring3_evidence_S68_pass4.md, diagnostics/ring3_palm_rubric_S68_pass4.md, scripts/probe_fh_stage1_extraction.py, tests/interpretive/test_palm_reading.py |
| cheiroslanguageo00chei_1_p96_c0 | 9 | diagnostics/archive/dogfood_capture_pre_S70_pass5.md, diagnostics/dogfood_capture_pre_s78.md, diagnostics/e2f_retrieval_topk.md, diagnostics/fc_retrieval_probe_S68.md, diagnostics/fh_stage1_probe_S69.md, diagnostics/pass5_preflight_S70.md, diagnostics/ring3_chunks_S67_pass3.md, diagnostics/ring3_evidence_S68_pass4.md, scripts/probe_fh_stage1_extraction.py |
| cheiroslanguageo00chei_1_p123_c0 | 9 | diagnostics/archive/dogfood_capture_pre_S70_pass5.md, diagnostics/dogfood_capture.md, diagnostics/fc_retrieval_probe_S68.md, diagnostics/fh_stage1_probe_S69.md, diagnostics/ring3_chunks_S66.md, diagnostics/ring3_chunks_S66_pass2.md, diagnostics/ring3_chunks_S67_pass3.md, diagnostics/ring3_evidence_S68_pass4.md, scripts/probe_fh_stage1_extraction.py |
| cheiroslanguageo00chei_1_p88_c1 | 8 | diagnostics/archive/dogfood_capture_pre_S70_pass5.md, diagnostics/e2f_retrieval_topk.md, diagnostics/fc_retrieval_probe_S68.md, diagnostics/fh_stage1_probe_S69.md, diagnostics/pass5_preflight_S70.md, diagnostics/ring3_chunks_S67_pass3.md, diagnostics/ring3_evidence_S68_pass4.md, scripts/probe_fh_stage1_extraction.py |
| cheiroslanguageo00chei_1_p134_c2 | 7 | agent/interpretive/palm_reading.py, diagnostics/fc_retrieval_probe_S68.md, diagnostics/pass5_preflight_S70.md, diagnostics/ring3_chunks_S67_pass3.md, scripts/probe_fc_retrieval.py, tests/interpretive/test_palm_reading.py, tests/test_app_dogfood_capture.py |
| cheiroslanguageo00chei_1_p88_c0 | 7 | diagnostics/archive/dogfood_capture_pre_S70_pass5.md, diagnostics/dogfood_capture.md, diagnostics/e2f_retrieval_topk.md, diagnostics/fh_stage1_probe_S69.md, diagnostics/ring3_chunks_S67_pass3.md, diagnostics/ring3_evidence_S68_pass4.md, scripts/probe_fh_stage1_extraction.py |
| cheiroslanguageo00chei_1_p147_c1 | 7 | diagnostics/archive/dogfood_capture_pre_S70_pass5.md, diagnostics/fc_retrieval_probe_S68.md, diagnostics/fh_stage1_probe_S69.md, diagnostics/pass5_preflight_S70.md, diagnostics/ring3_chunks_S67_pass3.md, diagnostics/ring3_evidence_S68_pass4.md, scripts/probe_fh_stage1_extraction.py |
| cheiroslanguageo00chei_1_p159_c3 | 7 | diagnostics/archive/dogfood_capture_pre_S70_pass5.md, diagnostics/fc_heartline_corpus_S68.md, diagnostics/fc_retrieval_probe_S68.md, diagnostics/fh_stage1_probe_S69.md, diagnostics/ring3_chunks_S67_pass3.md, diagnostics/ring3_evidence_S68_pass4.md, scripts/probe_fh_stage1_extraction.py |
| cheiroslanguageo00chei_1_p95_c0 | 6 | diagnostics/archive/dogfood_capture_pre_S70_pass5.md, diagnostics/dogfood_capture_pre_s78.md, diagnostics/fc_retrieval_probe_S68.md, diagnostics/fh_stage1_probe_S69.md, diagnostics/ring3_evidence_S68_pass4.md, scripts/probe_fh_stage1_extraction.py |
| Deva-keralam_p8_c0 | 6 | diagnostics/chunking_code_audit_20260621_092249.md, diagnostics/embedder_hardening_proposal_20260621_100850.md, diagnostics/provenance_audit_20260621_100237.md, diagnostics/targeted_delete_dryrun.py, diagnostics/targeted_delete_plan_20260621_120557.json, tests/test_embedder.py |
| cheiroslanguageo00chei_1_p87_c0 | 6 | diagnostics/dogfood_capture.md, diagnostics/dogfood_capture_pre_s78.md, diagnostics/e2f_retrieval_topk.md, diagnostics/fc_retrieval_probe_S68.md, diagnostics/pass5_preflight_S70.md, diagnostics/ring3_chunks_S67_pass3.md |
| cheiroslanguageo00chei_1_p159_c2 | 5 | diagnostics/fc_heartline_corpus_S68.md, diagnostics/fc_retrieval_probe_S68.md, diagnostics/pass5_preflight_S70.md, diagnostics/ring3_chunks_S67_pass3.md, scripts/probe_fc_heartline_corpus.py |
| cheiroslanguageo00chei_1_p135_c0 | 5 | diagnostics/fc_retrieval_probe_S68.md, diagnostics/pass5_preflight_S70.md, diagnostics/ring3_chunks_S66.md, diagnostics/ring3_chunks_S66_pass2.md, diagnostics/ring3_chunks_S67_pass3.md |
| cheiroslanguageo00chei_1_p165_c0 | 4 | diagnostics/archive/dogfood_capture_pre_S70_pass5.md, diagnostics/dogfood_capture.md, diagnostics/pass5_preflight_S70.md, diagnostics/ring3_chunks_S67_pass3.md |
| cheiroslanguageo00chei_1_p98_c0 | 4 | diagnostics/archive/dogfood_capture_pre_S70_pass5.md, diagnostics/e2f_retrieval_topk.md, diagnostics/fc_retrieval_probe_S68.md, diagnostics/ring3_chunks_S67_pass3.md |
| cheiroslanguageo00chei_1_p160_c1 | 4 | diagnostics/dogfood_capture.md, diagnostics/fc_heartline_corpus_S68.md, diagnostics/fc_retrieval_probe_S68.md, diagnostics/pass5_preflight_S70.md |
| cheiroslanguageo00chei_1_p89_c2 | 4 | diagnostics/e2f_retrieval_topk.md, diagnostics/fc_retrieval_probe_S68.md, diagnostics/pass5_preflight_S70.md, diagnostics/ring3_chunks_S67_pass3.md |
| cheiroslanguageo00chei_1_p96_c1 | 4 | diagnostics/e2f_retrieval_topk.md, diagnostics/fc_retrieval_probe_S68.md, diagnostics/pass5_preflight_S70.md, diagnostics/ring3_chunks_S67_pass3.md |
| Deva-keralam_p59_c2 | 4 | diagnostics/path_c_validation_20260621_173724.md, diagnostics/post_delete_saturn11_retrieval.py, diagnostics/post_delete_saturn11_retrieval_20260621_130514.md, diagnostics/targeted_delete_plan_20260621_120557.json |
| Deva-keralam_p153_c0 | 4 | diagnostics/path_c_validation_20260621_173724.md, diagnostics/post_delete_saturn11_retrieval.py, diagnostics/post_delete_saturn11_retrieval_20260621_130514.md, diagnostics/targeted_delete_plan_20260621_120557.json |
| Deva-keralam_p59_c0 | 4 | diagnostics/path_c_validation_20260621_173724.md, diagnostics/post_delete_saturn11_retrieval.py, diagnostics/post_delete_saturn11_retrieval_20260621_130514.md, diagnostics/targeted_delete_plan_20260621_120557.json |
| Deva-keralam_p147_c2 | 4 | diagnostics/path_c_validation_20260621_173724.md, diagnostics/post_delete_saturn11_retrieval.py, diagnostics/post_delete_saturn11_retrieval_20260621_130514.md, diagnostics/targeted_delete_plan_20260621_120557.json |
| Deva-keralam_p59_c1 | 4 | diagnostics/path_c_validation_20260621_173724.md, diagnostics/post_delete_saturn11_retrieval.py, diagnostics/post_delete_saturn11_retrieval_20260621_130514.md, diagnostics/targeted_delete_plan_20260621_120557.json |
| cheiroslanguageo00chei_1_p166_c1 | 3 | diagnostics/archive/dogfood_capture_pre_S70_pass5.md, diagnostics/pass5_preflight_S70.md, diagnostics/ring3_chunks_S66.md |
| Prakashan_p92_c0 | 3 | diagnostics/chromadb_dup_report_20260621_080119.md, diagnostics/post_delete_dup_recheck_20260621_130108.md, diagnostics/targeted_delete_plan_20260621_120557.json |
| Prakashan_p264_c0 | 3 | diagnostics/chromadb_dup_report_20260621_080119.md, diagnostics/post_delete_dup_recheck_20260621_130108.md, diagnostics/targeted_delete_plan_20260621_120557.json |
| Prakashan_p274_c0 | 3 | diagnostics/chromadb_dup_report_20260621_080119.md, diagnostics/post_delete_dup_recheck_20260621_130108.md, diagnostics/targeted_delete_plan_20260621_120557.json |
| Prakashan_p294_c0 | 3 | diagnostics/chromadb_dup_report_20260621_080119.md, diagnostics/post_delete_dup_recheck_20260621_130108.md, diagnostics/targeted_delete_plan_20260621_120557.json |
| Prakashan_p347_c0 | 3 | diagnostics/chromadb_dup_report_20260621_080119.md, diagnostics/post_delete_dup_recheck_20260621_130108.md, diagnostics/targeted_delete_plan_20260621_120557.json |
| Prakashan_p373_c0 | 3 | diagnostics/chromadb_dup_report_20260621_080119.md, diagnostics/post_delete_dup_recheck_20260621_130108.md, diagnostics/targeted_delete_plan_20260621_120557.json |
| Deva-keralam_p1_c0 | 3 | diagnostics/chunking_code_audit_20260621_092249.md, diagnostics/provenance_audit_20260621_100237.md, diagnostics/run_single_book_validation_proposal_20260621_113829.md |
| Deva-keralam_p8_c1 | 3 | diagnostics/chunking_code_audit_20260621_092249.md, diagnostics/provenance_audit_20260621_100237.md, diagnostics/targeted_delete_plan_20260621_120557.json |
| Deva-keralam_p8_c2 | 3 | diagnostics/chunking_code_audit_20260621_092249.md, diagnostics/provenance_audit_20260621_100237.md, diagnostics/targeted_delete_plan_20260621_120557.json |
| cheiroslanguageo00chei_1_p111_c1 | 3 | diagnostics/dogfood_capture_pre_s78.md, diagnostics/pass5_preflight_S70.md, diagnostics/ring3_chunks_S67_pass3.md |
| cheiroslanguageo00chei_1_p156_c0 | 3 | diagnostics/fc_heartline_corpus_S68.md, diagnostics/fc_retrieval_probe_S68.md, tests/fixtures/golden_S80.json |
| cheiroslanguageo00chei_1_p156_c1 | 3 | diagnostics/fc_heartline_corpus_S68.md, diagnostics/fc_retrieval_probe_S68.md, tests/fixtures/golden_S80.json |
| cheiroslanguageo00chei_1_p161_c0 | 3 | diagnostics/fc_heartline_corpus_S68.md, diagnostics/fc_retrieval_probe_S68.md, diagnostics/ring3_chunks_S67_pass3.md |
| cheiroslanguageo00chei_1_p134_c0 | 3 | diagnostics/fc_retrieval_probe_S68.md, diagnostics/pass5_preflight_S70.md, diagnostics/ring3_chunks_S67_pass3.md |
| cheiroslanguageo00chei_1_p111_c0 | 3 | diagnostics/pass5_preflight_S70.md, diagnostics/ring3_chunks_S66_pass2.md, diagnostics/ring3_chunks_S67_pass3.md |
| Deva-keralam_p147_c1 | 3 | diagnostics/post_delete_saturn11_retrieval.py, diagnostics/post_delete_saturn11_retrieval_20260621_130514.md, diagnostics/targeted_delete_plan_20260621_120557.json |
| Deva-keralam_p202_c2 | 3 | diagnostics/post_delete_saturn11_retrieval.py, diagnostics/post_delete_saturn11_retrieval_20260621_130514.md, diagnostics/targeted_delete_plan_20260621_120557.json |

### CLAUDE.md-named anchors — reported regardless of whether they clear the 3+ bar

| Anchor | Bare occurrence count | Bare: distinct files | Full-id variants found (id -> files) |
|---|---|---|---|
| p145_c0 | 22 | CLAUDE.md, SESSION_LOG.md, diagnostics/ring3_palm_rubric_S68_pass4.md, diagnostics/ring3_palm_rubric_S70_pass5.md, scripts/probe_neutral_chunk_valence.py | cheiroslanguageo00chei_1_p145_c0 (11 files: CLAUDE.md, SESSION_LOG.md, diagnostics/archive/dogfood_capture_pre_S70_pass5.md, diagnostics/dogfood_capture.md, diagnostics/dogfood_capture_pre_s78.md, diagnostics/fh_stage1_probe_S69.md, diagnostics/ring3_chunks_S67_pass3.md, diagnostics/ring3_evidence_S68_pass4.md, diagnostics/ring3_palm_rubric_S70_pass5.md, scripts/probe_fh_stage1_extraction.py, scripts/probe_neutral_chunk_valence.py); Deva-keralam_p145_c0 (1 files: diagnostics/targeted_delete_plan_20260621_120557.json); Prakashan_p145_c0 (1 files: diagnostics/targeted_delete_plan_20260621_120557.json); Series_p145_c0 (1 files: diagnostics/targeted_delete_plan_20260621_120557.json); 2_p145_c0 (1 files: diagnostics/targeted_delete_plan_20260621_120557.json); Sarvartha-Chintamani_p145_c0 (1 files: diagnostics/targeted_delete_plan_20260621_120557.json) |
| p139_c0 | 16 | CLAUDE.md, SESSION_LOG.md, diagnostics/e2g_preflight_S79.md, diagnostics/ring3_palm_rubric_S68_pass4.md, diagnostics/ring3_palm_rubric_S70_pass5.md, scripts/probe_neutral_chunk_valence.py | cheiroslanguageo00chei_1_p139_c0 (9 files: diagnostics/archive/dogfood_capture_pre_S70_pass5.md, diagnostics/dogfood_capture.md, diagnostics/dogfood_capture_pre_s78.md, diagnostics/fc_retrieval_probe_S68.md, diagnostics/fh_stage1_probe_S69.md, diagnostics/ring3_chunks_S67_pass3.md, diagnostics/ring3_evidence_S68_pass4.md, diagnostics/ring3_palm_rubric_S70_pass5.md, scripts/probe_fh_stage1_extraction.py); Deva-keralam_p139_c0 (1 files: diagnostics/targeted_delete_plan_20260621_120557.json); Prakashan_p139_c0 (1 files: diagnostics/targeted_delete_plan_20260621_120557.json); Series_p139_c0 (1 files: diagnostics/targeted_delete_plan_20260621_120557.json); Muhurtha-Chinthamani_p139_c0 (1 files: diagnostics/targeted_delete_plan_20260621_120557.json); 2_p139_c0 (1 files: diagnostics/targeted_delete_plan_20260621_120557.json); Sarvartha-Chintamani_p139_c0 (1 files: diagnostics/targeted_delete_plan_20260621_120557.json); uttkalamrita-kalidas-ps-sastri_p139_c0 (1 files: diagnostics/targeted_delete_plan_20260621_120557.json) |
| p163_c1 | 30 | SESSION_LOG.md, diagnostics/e2g_preflight_S79.md, diagnostics/fh_stage1_probe_S69.md, diagnostics/ring3_palm_rubric_S67_pass3.md, diagnostics/ring3_palm_rubric_S68_pass4.md, scripts/probe_fh_stage1_extraction.py, tests/interpretive/test_claim_extraction.py | cheiroslanguageo00chei_1_p163_c1 (9 files: diagnostics/archive/dogfood_capture_pre_S70_pass5.md, diagnostics/fh_stage1_probe_S69.md, diagnostics/pass5_preflight_S70.md, diagnostics/ring3_chunks_S66.md, diagnostics/ring3_chunks_S67_pass3.md, diagnostics/ring3_evidence_S68_pass4.md, diagnostics/ring3_palm_rubric_S68_pass4.md, scripts/probe_fh_stage1_extraction.py, tests/interpretive/test_palm_reading.py); Deva-keralam_p163_c1 (1 files: diagnostics/targeted_delete_plan_20260621_120557.json); uttkalamrita-kalidas-ps-sastri_p163_c1 (1 files: diagnostics/targeted_delete_plan_20260621_120557.json) |
| p159_c2 | 11 | CLAUDE.md, SESSION_LOG.md, agent/interpretive/palm_reading.py, diagnostics/e2g_preflight_S79.md, scripts/probe_fc_heartline_corpus.py, scripts/probe_neutral_chunk_valence.py | cheiroslanguageo00chei_1_p159_c2 (5 files: diagnostics/fc_heartline_corpus_S68.md, diagnostics/fc_retrieval_probe_S68.md, diagnostics/pass5_preflight_S70.md, diagnostics/ring3_chunks_S67_pass3.md, scripts/probe_fc_heartline_corpus.py); Deva-keralam_p159_c2 (1 files: diagnostics/targeted_delete_plan_20260621_120557.json); 1_p159_c2 (1 files: diagnostics/targeted_delete_plan_20260621_120557.json) |

---

## (f) Hardcoded book-name string references

Searched for each of the 14 canonical `book_name` strings (as literal substrings, case-sensitive) within the scanned scope. The two 100+ character names CLAUDE.md flags are marked explicitly.

| Book name | Total occurrences | Files (count each) |
|---|---|---|
| cheiroslanguageo00chei_1 | 1269 | diagnostics/archive/dogfood_capture_pre_S70_pass5.md (356), diagnostics/fh_stage1_probe_S69.md (181), diagnostics/fc_retrieval_probe_S68.md (126), diagnostics/ring3_evidence_S68_pass4.md (96), diagnostics/pass5_preflight_S70.md (69), diagnostics/dogfood_capture.md (68), scripts/probe_fh_stage1_extraction.py (57), diagnostics/e2f_retrieval_topk.md (43), diagnostics/dogfood_capture_pre_s78.md (35), diagnostics/ring3_chunks_S67_pass3.md (35), tests/interpretive/test_palm_reading.py (35), diagnostics/fc_heartline_corpus_S68.md (32), diagnostics/ring3_palm_rubric_S66.md (18), diagnostics/ring3_palm_rubric_S66_pass2.md (18), diagnostics/ring3_chunks_S66.md (13), tests/test_app_dogfood_capture.py (12), diagnostics/e2g_preflight_S79.md (9), diagnostics/ring3_chunks_S66_pass2.md (8), diagnostics/ring3_palm_rubric_S70_pass5.md (5), agent/interpretive/palm_reading.py (4), scripts/bidirectional_corruption_census_S80.py (4), scripts/probe_fc_retrieval.py (4), diagnostics/chunking_code_audit_20260621_092249.md (3), diagnostics/post_delete_dup_recheck_20260621_130108.md (3), diagnostics/provenance_audit_20260621_100237.md (3), diagnostics/ring3_palm_rubric_S68_pass4.md (3), scripts/build_golden_fixtures_S80.py (3), scripts/probe_fc_heartline_corpus.py (3), scripts/probe_neutral_chunk_valence.py (3), tests/fixtures/golden_S80.json (3), CLAUDE.md (2), diagnostics/golden_fixtures_S80.md (2), scripts/probe_r1_retrieval.py (2), SESSION_LOG.md (2), BOOKS.md (1), diagnostics/bidirectional_corruption_census_S80.md (1), diagnostics/chunking_code_audit.py (1), diagnostics/provenance_audit.py (1), diagnostics/r1_p0_page_triage_S79.md (1), diagnostics/run_single_book_validation_proposal_20260621_113829.md (1), diagnostics/targeted_delete_dryrun.py (1), diagnostics/targeted_delete_dryrun_20260621_120557.md (1), tests/fixtures/native_coverage_S80.json (1) |
| Deva-keralam | 836 | diagnostics/targeted_delete_plan_20260621_120557.json (672), diagnostics/post_delete_saturn11_retrieval_20260621_130514.md (37), diagnostics/path_c_validation_20260621_173724.md (36), diagnostics/chunking_code_audit_20260621_092249.md (17), diagnostics/post_delete_saturn11_retrieval.py (15), diagnostics/targeted_delete_dryrun_20260621_120557.md (10), diagnostics/provenance_audit_20260621_100237.md (8), tests/fixtures/golden_S80.json (8), diagnostics/provenance_audit.py (5), diagnostics/golden_fixtures_S80.md (4), SESSION_LOG.md (4), diagnostics/chunking_code_audit.py (3), diagnostics/embedder_hardening_proposal_20260621_100850.md (3), diagnostics/run_single_book_validation_proposal_20260621_113829.md (3), diagnostics/targeted_delete_dryrun.py (3), diagnostics/post_delete_dup_recheck.py (2), diagnostics/chromadb_dup_report_20260621_080119.md (1), diagnostics/post_delete_dup_recheck_20260621_130108.md (1), diagnostics/targeted_delete_execute_20260621_121046.md (1), scripts/build_golden_fixtures_S80.py (1), tests/fixtures/native_coverage_S80.json (1), tests/test_embedder.py (1) |
| Muhurtha-Chinthamani | 650 | diagnostics/targeted_delete_plan_20260621_120557.json (604), agent/calculations/compatibility/_ashtakoot_tables.py (18), SESSION_LOG.md (6), diagnostics/chunking_code_audit_20260621_092249.md (3), diagnostics/chromadb_dup_report_20260621_080119.md (2), diagnostics/post_delete_dup_recheck.py (2), diagnostics/provenance_audit_20260621_100237.md (2), agent/.claude/settings.local.json (1), agent/calculations/compatibility/matrix.py (1), agent/calculations/compatibility/trivial.py (1), agent/calculations/core/_pvr_spec_reference.json (1), agent/calculations/core/panchanga.py (1), BOOKS.md (1), diagnostics/chunking_code_audit.py (1), diagnostics/golden_fixtures_S80.md (1), diagnostics/post_delete_dup_recheck_20260621_130108.md (1), diagnostics/provenance_audit.py (1), diagnostics/targeted_delete_dryrun_20260621_120557.md (1), tests/calculations/fixtures/panchanga_fixtures.py (1), tests/fixtures/native_coverage_S80.json (1) |
| Prasna Marga 1 | 536 | diagnostics/targeted_delete_plan_20260621_120557.json (517), diagnostics/targeted_delete_dryrun_20260621_120557.md (5), diagnostics/chunking_code_audit_20260621_092249.md (3), diagnostics/chromadb_dup_report_20260621_080119.md (2), diagnostics/post_delete_dup_recheck.py (2), diagnostics/provenance_audit_20260621_100237.md (2), diagnostics/chunking_code_audit.py (1), diagnostics/golden_fixtures_S80.md (1), diagnostics/post_delete_dup_recheck_20260621_130108.md (1), diagnostics/provenance_audit.py (1), tests/fixtures/native_coverage_S80.json (1) |
| Jataka Parijata with explanation of Pt. Kapileshvara Shas... **[LONG NAME]** | 530 | diagnostics/targeted_delete_plan_20260621_120557.json (504), diagnostics/targeted_delete_dryrun_20260621_120557.md (9), diagnostics/chromadb_dup_report_20260621_080119.md (5), diagnostics/chunking_code_audit_20260621_092249.md (3), diagnostics/post_delete_dup_recheck.py (2), diagnostics/provenance_audit_20260621_100237.md (2), diagnostics/chunking_code_audit.py (1), diagnostics/golden_fixtures_S80.md (1), diagnostics/post_delete_dup_recheck_20260621_130108.md (1), diagnostics/provenance_audit.py (1), tests/fixtures/native_coverage_S80.json (1) |
| Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delh... **[LONG NAME]** | 455 | diagnostics/targeted_delete_plan_20260621_120557.json (422), diagnostics/post_delete_dup_recheck_20260621_130108.md (13), diagnostics/chromadb_dup_report_20260621_080119.md (8), diagnostics/chunking_code_audit_20260621_092249.md (3), diagnostics/post_delete_dup_recheck.py (2), diagnostics/provenance_audit_20260621_100237.md (2), diagnostics/chunking_code_audit.py (1), diagnostics/golden_fixtures_S80.md (1), diagnostics/provenance_audit.py (1), diagnostics/targeted_delete_dryrun_20260621_120557.md (1), tests/fixtures/native_coverage_S80.json (1) |
| Sarvartha-Chintamani | 447 | diagnostics/targeted_delete_plan_20260621_120557.json (423), diagnostics/targeted_delete_dryrun_20260621_120557.md (9), diagnostics/chunking_code_audit_20260621_092249.md (3), diagnostics/post_delete_dup_recheck.py (2), diagnostics/provenance_audit_20260621_100237.md (2), agent/.claude/settings.local.json (1), diagnostics/chromadb_dup_report_20260621_080119.md (1), diagnostics/chunking_code_audit.py (1), diagnostics/golden_fixtures_S80.md (1), diagnostics/post_delete_dup_recheck_20260621_130108.md (1), diagnostics/provenance_audit.py (1), scripts/build_golden_fixtures_S80.py (1), tests/fixtures/native_coverage_S80.json (1) |
| Prasna Marga 2 | 446 | diagnostics/targeted_delete_plan_20260621_120557.json (431), diagnostics/chunking_code_audit_20260621_092249.md (3), diagnostics/chromadb_dup_report_20260621_080119.md (2), diagnostics/post_delete_dup_recheck.py (2), diagnostics/provenance_audit_20260621_100237.md (2), diagnostics/chunking_code_audit.py (1), diagnostics/golden_fixtures_S80.md (1), diagnostics/post_delete_dup_recheck_20260621_130108.md (1), diagnostics/provenance_audit.py (1), diagnostics/targeted_delete_dryrun_20260621_120557.md (1), tests/fixtures/native_coverage_S80.json (1) |
| uttkalamrita-kalidas-ps-sastri | 399 | diagnostics/targeted_delete_plan_20260621_120557.json (372), diagnostics/targeted_delete_dryrun_20260621_120557.md (13), diagnostics/chunking_code_audit_20260621_092249.md (3), diagnostics/post_delete_dup_recheck.py (2), diagnostics/provenance_audit_20260621_100237.md (2), agent/.claude/settings.local.json (1), diagnostics/chromadb_dup_report_20260621_080119.md (1), diagnostics/chunking_code_audit.py (1), diagnostics/golden_fixtures_S80.md (1), diagnostics/post_delete_dup_recheck_20260621_130108.md (1), diagnostics/provenance_audit.py (1), tests/fixtures/native_coverage_S80.json (1) |
| BPHS - 1 RSanthanam | 40 | diagnostics/provenance_audit_20260621_100237.md (9), diagnostics/run_single_book_validation_proposal_20260621_113829.md (8), diagnostics/path_c_validation_20260621_173724.md (7), diagnostics/chunking_code_audit_20260621_092249.md (3), diagnostics/post_delete_dup_recheck_20260621_130108.md (3), diagnostics/golden_fixtures_S80.md (2), agent/.claude/settings.local.json (1), BOOKS.md (1), diagnostics/chunking_code_audit.py (1), diagnostics/provenance_audit.py (1), diagnostics/targeted_delete_dryrun.py (1), diagnostics/targeted_delete_dryrun_20260621_120557.md (1), tests/fixtures/native_coverage_S80.json (1), tests/test_context_integration.py (1) |
| Jyotish_Lal Kitab_B.M. Gosvami | 33 | diagnostics/path_c_validation_20260621_173724.md (11), diagnostics/provenance_audit_20260621_100237.md (5), diagnostics/chunking_code_audit_20260621_092249.md (3), diagnostics/golden_fixtures_S80.md (3), diagnostics/post_delete_dup_recheck_20260621_130108.md (3), .claude/settings.local.json (1), diagnostics/chunking_code_audit.py (1), diagnostics/provenance_audit.py (1), diagnostics/targeted_delete_dryrun.py (1), diagnostics/targeted_delete_dryrun_20260621_120557.md (1), scripts/build_golden_fixtures_S80.py (1), SESSION_LOG.md (1), tests/fixtures/native_coverage_S80.json (1) |
| Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri | 26 | diagnostics/post_delete_saturn11_retrieval_20260621_130514.md (7), diagnostics/post_delete_dup_recheck_20260621_130108.md (5), diagnostics/chunking_code_audit_20260621_092249.md (3), diagnostics/provenance_audit_20260621_100237.md (3), BOOKS.md (1), diagnostics/chunking_code_audit.py (1), diagnostics/golden_fixtures_S80.md (1), diagnostics/post_delete_saturn11_retrieval.py (1), diagnostics/provenance_audit.py (1), diagnostics/targeted_delete_dryrun.py (1), diagnostics/targeted_delete_dryrun_20260621_120557.md (1), tests/fixtures/native_coverage_S80.json (1) |
| BPHS - 2 RSanthanam | 19 | diagnostics/post_delete_dup_recheck_20260621_130108.md (5), diagnostics/chunking_code_audit_20260621_092249.md (3), diagnostics/provenance_audit_20260621_100237.md (3), diagnostics/golden_fixtures_S80.md (2), BOOKS.md (1), diagnostics/chunking_code_audit.py (1), diagnostics/provenance_audit.py (1), diagnostics/targeted_delete_dryrun.py (1), diagnostics/targeted_delete_dryrun_20260621_120557.md (1), tests/fixtures/native_coverage_S80.json (1) |
| Saravali of Kalyana Varma Santhanam R. (Astrology) | 17 | diagnostics/chunking_code_audit_20260621_092249.md (3), diagnostics/post_delete_dup_recheck_20260621_130108.md (3), diagnostics/provenance_audit_20260621_100237.md (3), diagnostics/path_c_validation_20260621_173724.md (2), diagnostics/chunking_code_audit.py (1), diagnostics/golden_fixtures_S80.md (1), diagnostics/provenance_audit.py (1), diagnostics/targeted_delete_dryrun.py (1), diagnostics/targeted_delete_dryrun_20260621_120557.md (1), tests/fixtures/native_coverage_S80.json (1) |

---

## (g) Merge/architecture recommendation

**No recommendation is made here.** Report only, per instruction. The gate number, the ASSERTED/STUB breakdown, the load-bearing anchor list, and the book-name-coupling table above are the evidence for the rebuild-vs-repair architecture ruling; that ruling is made after reading this census, not before.

---

## Skipped files

| Path | Reason |
|---|---|
| diagnostics/calc_router_stage2.log | untracked large artifact (1013605 bytes) |
| diagnostics/corpus_export_cheiro_S79.jsonl | untracked large artifact (447320 bytes) |
| diagnostics/targeted_delete_snapshot_20260621_120557.jsonl | untracked large artifact (127907942 bytes) |
