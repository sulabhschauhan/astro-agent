# CLAUDE.md
<!-- TOKEN BUDGET: Keep this file under 80 lines. No session logs, no completed module designs, no book registries here. Those live in separate files loaded on demand. Before adding anything, ask: does Claude need this every single query? If not, it belongs elsewhere. -->

## Project
Astrologer AI Agent with RAG — Vedic astrology + palmistry PDFs → OCR → embed → ChromaDB → LLM Q&A agent.

## Current Session Focus
**Session 9 COMPLETE** — astrosage_parser.py done, PDF upload wired, needs_disclaimer() wired. Next: Session 10 — UI fixes (sidebar, time input, place autocomplete, nudge) + create tests/test_astrosage_parser.py.
<!-- UPDATE THIS every session. One line only. -->

## Stack
| Layer | Tool |
|---|---|
| OCR | Tesseract + pytesseract + pdf2image |
| Embeddings | OpenAI `text-embedding-3-small` (dim=1536) |
| Vector DB | ChromaDB → Pinecone (prod) |
| Inference | GPT-4o-mini |
| Backend | FastAPI (`api/`) |
| Frontend | Streamlit → React (prod) |
| Auth/Payments | Supabase + Stripe |

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

## Sessions Completed
0–5 complete. See `SESSION_LOG.md` for details. Do NOT load unless asked.
ChromaDB: 7,281 chunks — 14/14 books embedded, 158 diagram chunks pending `image_extractor`.

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
7. **AGENT INVOCATION** — invoke relevant agents automatically before any design decision or code change. Do not wait to be asked. New file → all 6 agents. Frontend change → ui_ux mandatory. Conflict → debate last, always. Never write code before agent review is complete.

## Token Hygiene Rules
- This file must stay under 80 lines
- No session logs in this file — use `SESSION_LOG.md`
- No completed module designs — archive to relevant session plan file
- No book registries — use `BOOKS.md`
- Run `/compact` after each major task; `/clear` when switching tasks
- If adding content here, remove something of equal or greater size first
- No file exploration before coding if spec is already provided
- Read only files directly relevant to the current task