# CLAUDE.md
<!-- TOKEN BUDGET: Keep this file under 80 lines. No session logs, no completed module designs, no book registries here. Those live in separate files loaded on demand. Before adding anything, ask: does Claude need this every single query? If not, it belongs elsewhere. -->

## Project
Astrologer AI Agent with RAG — Vedic astrology + palmistry PDFs → OCR → embed → ChromaDB → LLM Q&A agent.

## Current Session Focus
**P1.3 Aspects COMPLETE. Next: P2.1 Navamsa (D9).** 593 passed, 3 skipped.
- `agent/calculations/core/_aspects_tables.py`, `agent/calculations/core/aspects.py`
- `tests/calculations/test__aspects_tables.py`, `tests/calculations/test_aspects.py`
<!-- UPDATE THIS every session. One line only. -->

## Locked Decisions
- **Hand-laterality via vision LLM** — evaluated across Sessions 15-16 under 3 framings (anchored chirality, unanchored chirality, thumb-side spatial position); consistently unreliable (Session 15: 5/6 right-bias on unlabeled images; Session 16: 3/4 thumb-side accuracy on N=4, one image misjudged, sample too small to trust). Permanent design: human confirmation at upload, no GPT laterality judgment.
- **Tiebreaker principle (memory #10)** — when classical sources are genuinely fragmented, user-perceived correctness wins over single-source-code purity. Established via the Rahu/Ketu graha drishti lock (SESSION_LOG.md, Session 19, P1.3 Aspects). Applies to all future contested P2-P7 decisions.

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
}
```
Sub-chunks always have `_c{index}` appended to `chunk_id`.


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
9. **NO ANCHORED JUDGMENT** — never give an LLM call both a stated expectation and a request to judge against it in the same call. LLM observes independently (no expectation context given); Python compares the observation to the expectation deterministically.

## Varshaphal House-Counting Convention (Session 18)
`resolve_house_counting_lagna()` is the canonical house-counting reference for any Varshaphal-derived bhav calculation (prefers AstroSage parsed Lagna, year-matched; else computed + boundary flag). Future Varshaphal functions (Sade Sati, transits) should call it rather than reading Lagna directly off `varshaphal_data`.


## Calculation Architecture (Session 19+)

The calculation layer is structured as the `calculations/` package. Every new calculation module lives in its appropriate subpackage. Never add calculation logic to a top-level file.

**Package structure:**
- `calculations/core/` — chart_d1, panchanga, aspects, dignity
- `calculations/vargas/` — divisional charts D2-D60, vimshopaka
- `calculations/strength/` — shadbala, ishta_kashta, bhava_bala
- `calculations/dashas/` — vimshottari, yogini, chara, ashtottari, mudda
- `calculations/yogas/` — detector + catalog/
- `calculations/transits/` — gochara, sade_sati, transit_aspects
- `calculations/ashtakavarga/` — bav, sav
- `calculations/jaimini/` — karakas, arudha, padas
- `calculations/annual/` — varshaphal, muntha, sahams
- `calculations/helpers/` — house_counting, ephemeris

**Canonical helpers:**
- `resolve_house_counting_lagna()` lives in `helpers/house_counting.py` — canonical reference for ANY Varshaphal-derived bhav calculation
- pyswisseph wrapper centralised in `helpers/ephemeris.py`

**Validation protocol (per module):**
1. Sample-before-scale: validate on Sulabh's chart first
2. Hardest-case-first: test edge cases before mainline
3. Empirical validation across 4 reference charts before locking formula
4. Zero free parameters: test alternative hypotheses and rule them out
5. AstroSage parity where applicable; JHora oracle where not
6. Document irreducible cross-software noise as discovered


## Reference Materials

**Calculation specifications:**
- `project_files/classical_references/PVR_Vedic_Astrology_Integrated_Approach.pdf`
  Primary calculation reference for all Phase P1-P6 modules. PVR Narasimha 
  Rao authored both this book and JHora — book = formulas + classical 
  justification; JHora = numerical ground truth. Both consulted before 
  implementing any new calculation module.

**Validation oracles:**
- AstroSage PDFs (4 reference charts) — secondary parity
- JHora exports — primary parity for non-AstroSage-exposed calculations

**Interpretive RAG (separate, do not pollute):**
- ChromaDB 7,281 chunks across 14 classical texts. RAG is for Tier 4 
  interpretive answers in Parashara's voice. Modern textbooks (including 
  PVR's) are deliberately excluded from RAG to preserve classical voice 
  and avoid single-author tradition bias in retrieval.