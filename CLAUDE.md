# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in this repository.

## Project

Production-ready Astrologer AI Agent with RAG. Vedic astrology and palmistry PDFs are OCR'd, embedded, and stored for vector search, enabling an LLM-powered Q&A agent.

## Stack

| Layer | Dev | Prod |
|---|---|---|
| OCR | Tesseract + pytesseract + pdf2image | same |
| Diagram interpretation | GPT-4o (ingestion only) | same |
| Embeddings | OpenAI `text-embedding-3-small` (dim=1536) | same |
| Vector DB | ChromaDB (local, `data/chroma_db/`) | Pinecone |
| Inference | GPT-4o-mini | same |
| Backend | FastAPI (`api/`) | same |
| Frontend | Streamlit (`frontend/app.py`) | React |
| Auth | Supabase | same |
| Payments | Stripe | same |

## Windows Dependencies

Tesseract and Poppler paths are hardcoded for Windows in `ingestion/pdf_processor.py`:
- Tesseract: `C:\Program Files\Tesseract-OCR\tesseract.exe`
- Poppler: `C:\Program Files\poppler-26.02.0\Library\bin`

## Running the Pipeline

```bash
# Test PDF ingestion on the first PDF in data/pdfs/
python ingestion/pdf_processor.py

# Process all PDFs
# (call process_all_pdfs from ingestion/pdf_processor.py)
```

## Module Dependency Order

```
pdf_processor.py    → raw page chunks + saved diagram images
image_extractor.py  → fills text field on diagram chunks via GPT-4o
translator.py       → translates Hindi/Sanskrit chunks to English (Session 4)
chunker.py          → splits/refines chunks, sets topic + language fields
embedder.py         → writes chunks to ChromaDB collection "astro_chunks"
query_engine.py     → reads ChromaDB, returns ranked chunks
chart_calculator.py → calculates kundali_context dict from birth details (Session 5)
astrologer.py       → calls query_engine + prompt_builder, returns answer
session_manager.py  → stores conversation history + notes, persists to disk
```

## Chunk Metadata Schema (locked — do not alter)

Sub-chunks from `chunker.py` always have `_c{index}` appended to `chunk_id` (e.g. `BPHS - 1 RSanthanam_p12_c0`).

```python
{
  "chunk_id": str,          # "{book_name}_p{page_num}_c{index}"
  "text": str,
  "topic": str,             # filled by chunker.py
  "language": "eng|hin|mixed",
  "page_ref": int,
  "image_path": "str|null",
  "book_name": str,
  "page_type": "text|diagram|mixed",
  "word_count": int,        # per sub-chunk, filled by chunker.py
}
```

## ChromaDB

- Collection: `astro_chunks`
- Embedding dimension: 1536
- Persist directory: `data/chroma_db/`

## Running the Ingestion Pipeline

```bash
# Step 1 — OCR all PDFs, save raw chunks
python -c "
import json, sys; sys.path.insert(0, '.')
from ingestion.pdf_processor import process_all_pdfs
chunks = process_all_pdfs('data/pdfs', 'data/extracted_images')
json.dump(chunks, open('data/all_chunks.json', 'w'), ensure_ascii=False, indent=2)
"

# Step 2 — Extract text from diagram images via GPT-4o (requires OPENAI_API_KEY)
# python ingestion/image_extractor.py   # resumes from data/processed_chunks.json

# Step 3 — Chunk, detect language, tag topics
# python ingestion/chunker.py
```

## Session Log

- Session 0 (2026-05-25): Repo created, folder structure, `.cursorrules`, `CLAUDE.md` — COMPLETE
- Session 1 (2026-05-25): `pdf_processor.py` complete + validated on BPHS Vol 1 (482 pages, 155 diagram); fixed kundali misclassification via number density + planetary keyword checks; `image_extractor.py` complete; `chunker.py` complete — COMPLETE
- Session 2 (2026-05-26): `embedder.py` written; `classify_page()` extended with mixed detection (5 patterns: number density, planetary keywords, structural grids, illustration markers, diagram override for word_count > 250); `strip_devanagari()` added to `chunker.py`; split_page() added to `pdf_processor.py` with `split_spreads=False` default; all 5 books confirmed as single-page portrait scans — COMPLETE
- Session 3 (2026-05-26): four-agent review system (qa.md added); query_engine.py complete, all QA passed; astrologer.py complete, 13/15 QA passed — 2 failures: response time 6-11s (fix: SSE streaming in FastAPI layer); prompt_builder.py complete 12/12 tests passed; astrologer.py migrated atomically 7/7 regression passed; session_manager.py complete — get_recent_history (sliding 6-turn window), MAX_HISTORY_SAVE=100 trim logic, atomic JSON persist, 24/24 QA passed; astrologer.py session wiring complete — history prepend, introduce suppression, failed-call guard, all crashes fixed — COMPLETE
- Session 4: translator.py — Hindi book translation pipeline (GPT-4o-mini for prose, GPT-4o vision for Sanskrit/diagrams); books: Hasta Samudrika, Jataka Parijata, Lal Kitab 1941 — NOT STARTED
- Session 5: chart_calculator.py — pyswisseph + Lahiri ayanamsha, IST timezone, verification against Sulabh's AstroSage chart first, output kundali_context dict — NOT STARTED
- Session 6: FastAPI — SSE streaming, all routes with session management, chart_calculator integrated into /ask endpoint — NOT STARTED
- Session 7: Streamlit UI — birth details form + auto chart calculation, chat interface with streaming, palm photo upload — NOT STARTED
- Session 8: Stripe + Supabase + deployment — NOT STARTED



## Multi-Agent Review Process

Before writing ANY new file or component:
1. Load `.claude/architect.md` — review structure
2. Load `.claude/business.md` — review user value
3. Load `.claude/critic.md` — challenge assumptions
4. Load `.claude/qa.md` — validate test coverage
5. Reconcile all four before writing code

**Mandatory for:** new files, schema changes, threshold values, pipeline changes, API integrations

## Working Style Requirements
These are non-negotiable for every session:

1. REVIEW before PROCEED — never summarize a diff and say accept. 
   Identify at least one potential issue before approving any edit.

2. SAMPLE before SCALE — never suggest running full dataset without 
   first proposing a sample validation path.

3. HARDEST CASE first — when choosing test data, pick the most 
   complex/edge-case example, not the simplest.

4. OVERRIDE auto-suggestions — if auto-suggested next step skips 
   validation, flag it and suggest the validation step instead.

5. THRESHOLD DISCIPLINE — every numeric threshold needs:
   - Explicit justification for the value chosen
   - A scope guard (word_count, length, etc.) to prevent noise
   - A note on how to tune it if results are off

6. AI reviewing AI — flag explicitly when output hasn't had 
   human review. Never chain AI decisions without a human checkpoint.


## Agent Visual Intelligence

**Palmistry queries:**
- Proactively ask for photos using plain language — never say "palmar flexion crease" or "thenar eminence", say "the lines on your palm" or "the base of your thumb"
- Request a maximum of 2 photos at once
- If the user declines → answer from text knowledge and note the limitation explicitly
- For general questions answer from text; for personalized readings say: "I can share what the texts say generally, but a personalized reading would need your palm photo"

**Kundali queries:**
- Always ask for birth date, time, and place if not provided
- Or accept an uploaded kundali PDF
- Never guess planetary positions

## Source Books Registry (12 books — locked)

### English (9 — OCR'd or ready to process)
| # | Filename / ID | Title |
|---|---|---|
| 1 | BPHS - 1 RSanthanam | Brihat Parashara Hora Shastra Vol 1 |
| 2 | BPHS - 2 RSanthanam | Brihat Parashara Hora Shastra Vol 2 |
| 3 | cheiroslanguageo00chei_1 | Cheiro's Language of the Hand |
| 4 | Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri | Phaladeepika |
| 5 | Uttara Kalamrita | Uttara Kalamrita (already downloaded) |
| 6 | Deva Keralam / Chandra Kala Nadi | Deva Keralam (download Archive.org) |
| 7 | Sarvartha Chintamani | Sarvartha Chintamani (download Archive.org) |
| 8 | Muhurta Chintamani | Muhurta Chintamani (download Archive.org) |
| 9 | Prasna Marga | Prasna Marga (download Archive.org) |

### Hindi (3 — need translator.py before ingestion)
| # | Title | Author |
|---|---|---|
| 10 | Hasta Samudrika Shastra | Vasant Lal Vyas (1976) |
| 11 | Jataka Parijata | Kashi Sanskrit Series |
| 12 | Lal Kitab 1941 | Pt. Rup Chand Joshi |

**Removed as duplicates:** Saravali, Brihat Jataka, Chamatkar Chintamani

## chart_calculator.py Design (locked before Session 5)

- **Location:** `agent/chart_calculator.py`
- **Input:** `name, dob, tob, place` (city, country string)
- **Output:** `kundali_context` dict matching `kundali_summary.txt` format
- **Engine:** pyswisseph with `SIDM_LAHIRI` ayanamsha
- **Timezone:** IST handling (critical — birth times are local Indian time)
- **Geocoding:** geopy for lat/lon from city name
- **Verification:** must match Sulabh's AstroSage chart exactly before use in prod
- **Dependencies:** `pyswisseph`, `geopy`

## Coding Standards

- Python 3.11
- Surgical edits only — no full file rewrites
- Always use `try/except` with meaningful error messages
- Preserve all interfaces and the chunk metadata schema above
