# CLAUDE.md
<!-- TOKEN BUDGET: Keep this file under 80 lines. No session logs, no completed module designs, no book registries here. Those live in separate files loaded on demand. Before adding anything, ask: does Claude need this every single query? If not, it belongs elsewhere. -->

## Project
Astrologer AI Agent with RAG — Vedic astrology + palmistry PDFs → OCR → embed → ChromaDB → LLM Q&A agent.

## Current Session Focus
**P2.2.2 Sade Sati CLOSED. Interpretive-text spike FAILED (0/4 rubric) — RAG corpus + layering prompt both broken. P2.2.3+ PAUSED pending Session 23 architectural debate.** 623 passed, 3 skipped.
- `agent/calculations/transits/sade_sati.py`
- `tests/calculations/transits/test_sade_sati.py`
<!-- UPDATE THIS every session. One line only. -->

## Locked Decisions
- **Hand-laterality via vision LLM** — evaluated Sessions 15-16 under 3 framings; consistently unreliable (worst case 5/6 right-bias on unlabeled images). Permanent: human confirmation at upload, no GPT laterality judgment.
- **Tiebreaker principle (memory #10)** — when classical sources are genuinely fragmented, user-perceived correctness wins over single-source purity. Locked via the Rahu/Ketu graha drishti decision (Session 19); applies to all contested P2-P7 decisions, including roadmap sequencing.
- **No Chart dataclass / VargaType enum** (Session 20) — neither exists; Navamsa built as a pure `(jd_ut, asc_lon_sidereal)` function instead. Revisit only when a varga module genuinely needs shared chart-identity state.
- **Reference-chart fixture template** (Session 20) — one standalone test per chart, not `@pytest.mark.parametrize`, when expected-value structures differ; delete skip-stub parametrize blocks once empty.
- **Transit fixture anchor** (Session 21, PROVISIONAL) — 18:30 UTC (00:00 IST next day); needs second-date corroboration before treating as final.
- **P2 order** (locked Session 20, PAUSED Session 22) — Gochara → Sade Sati → Muhurta engine → Ashtakoot/Mangal dosha → Shadbala → D7 → D10 (demoted); P3+ deferred. On hold pending interpretive-layer architecture.
- **V1 scope** — LLM-generated interpretive Q&A is OUT (see `diagnostics/path_c_validation_20260621_173724.md`, Session 23 close 2026-06-21). AstroSage paragraph terminal; palm primary; deterministic calculation-engine output is V1's only structured Q&A surface.

## Windows Paths (hardcoded)
- Tesseract: `C:\Program Files\Tesseract-OCR\tesseract.exe`
- Poppler: `C:\Program Files\poppler-26.02.0\Library\bin`

## Module Order
```
pdf_processor → image_extractor → chunker → translator → embedder → ChromaDB
query_engine + chart_calculator → astrologer → session_manager
```

## Chunk Metadata Schema (locked — do not alter)
```python
{
  "chunk_id": str,       # "{book_name}_p{page_num}_c{index}"
  "text": str,
  "topic": str,
  "language": "eng|hin|mixed",
  "page_ref": int,
  "image_path": "str|null",
  "book_name": str,
  "page_type": "text|diagram|mixed",
  "word_count": int,
  "text_sha256": str,    # SHA-256 hex digest of `text`; embedder-computed, ChromaDB-metadata-only (not chunker-emitted)
}
```
Sub-chunks always have `_c{index}` appended to `chunk_id`.
Schema lock permits additive fields with safe defaults; renames and removals require explicit sign-off. `text_sha256` added per `diagnostics/embedder_hardening_proposal_20260621_100850.md`.

## Reference Files (load only when relevant)
| File | Load when |
|---|---|
| .claude/architect.md | new file, schema, pipeline change |
| .claude/business.md  | new file, user-facing change |
| .claude/critic.md    | new file, any code change |
| .claude/qa.md        | new file, any code change |
| .claude/ui_ux.md     | any frontend or UX change |
| .claude/debate.md    | agents conflict, multiple valid options |

## Working Style (non-negotiable)
1. **REVIEW before PROCEED** — flag at least one issue before approving any edit
2. **SAMPLE before SCALE** — propose sample validation before full dataset runs
3. **HARDEST CASE first** — test on edge cases, not simple ones
4. **THRESHOLD DISCIPLINE** — every numeric threshold needs justification + scope guard + tuning note
5. **AI reviewing AI** — flag when output has no human review; never chain AI decisions without human checkpoint
6. **SURGICAL EDITS** — no full file rewrites; Python 3.11; always `try/except` with meaningful errors
7. **AGENT INVOCATION** — auto-invoke all 6 before any design/code decision. Surface conflicts only. New agents need explicit approval.
8. **LAYER FIRST** — before any fix, state which layer owns the problem: Data, Retrieval, Prompt, or UI. A fix in the wrong layer creates narrow patches and technical debt.
9. **NO ANCHORED JUDGMENT** — never give an LLM call both a stated expectation and a request to judge against it in the same call. LLM observes independently; Python compares the observation to the expectation deterministically.

## Varshaphal House-Counting Convention (Session 18)
`resolve_house_counting_lagna()` is the canonical house-counting reference for any Varshaphal-derived bhav calculation (prefers AstroSage parsed Lagna, year-matched; else computed + boundary flag); call it rather than reading Lagna directly off `varshaphal_data`.

## Calculation Architecture (Session 19+)
Every new calculation module lives in its `calculations/` subpackage; never add calculation logic to a top-level file.

**Package structure:** `core/` (chart_d1, panchanga, aspects, dignity) · `vargas/` (D2-D60, vimshopaka) · `strength/` (shadbala, ishta_kashta, bhava_bala) · `dashas/` (vimshottari, yogini, chara, ashtottari, mudda) · `yogas/` (detector + catalog/) · `transits/` (gochara, sade_sati, transit_aspects) · `ashtakavarga/` (bav, sav) · `jaimini/` (karakas, arudha, padas) · `annual/` (varshaphal, muntha, sahams) · `helpers/` (house_counting, ephemeris)
**Canonical helpers:** `resolve_house_counting_lagna()` (`helpers/house_counting.py`) — canonical for ANY Varshaphal-derived bhav calc; `helpers/ephemeris.py` — planned pyswisseph wrapper, currently a stub (interim: direct `swe.calc_ut` + a `# TODO` marker per call site).
**Validation protocol** (per module, on top of Working Style #2/#3): empirical validation across 4 reference charts before locking a formula; zero free parameters (test alternative hypotheses, rule them out); AstroSage parity where applicable, JHora oracle where not; document irreducible cross-software noise as discovered.

## Reference Materials
**Calculation specifications:** `project_files/classical_references/PVR_Vedic_Astrology_Integrated_Approach.pdf` — primary reference for P1-P6; PVR authored both this book and JHora (book = formulas/justification, JHora = numerical ground truth); both consulted before implementing any new calculation module.
**Validation oracles:** AstroSage PDFs (4 reference charts) for secondary parity; JHora exports as primary parity where AstroSage doesn't expose the calculation.
**Interpretive RAG (separate, do not pollute):** ChromaDB ~7,281 chunks across 14 classical texts, for Tier 4 interpretive answers in Parashara's voice. Modern textbooks (incl. PVR's) are deliberately excluded from RAG to preserve classical voice and avoid single-author bias.
