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
pdf_processor.py   → raw page chunks + saved diagram images
image_extractor.py → fills text field on diagram chunks via GPT-4o
chunker.py         → splits/refines chunks, sets topic + language fields
embedder.py        → writes chunks to ChromaDB collection "astro_chunks"
query_engine.py    → reads ChromaDB, returns ranked chunks
astrologer.py      → calls query_engine + prompt_builder, returns answer
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
- Session 3: full 5-PDF re-run with updated classifier + chunker → embedder → query_engine — NOT STARTED



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

## Coding Standards

- Python 3.11
- Surgical edits only — no full file rewrites
- Always use `try/except` with meaningful error messages
- Preserve all interfaces and the chunk metadata schema above
