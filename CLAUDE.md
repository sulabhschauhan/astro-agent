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

```python
{
  "chunk_id": str,          # "{book_name}_p{page_num}"
  "text": str,
  "topic": str,             # filled by chunker.py
  "language": "eng|hin|mixed",
  "page_ref": int,
  "image_path": "str|null",
  "book_name": str,
  "page_type": "text|diagram"
}
```

## ChromaDB

- Collection: `astro_chunks`
- Embedding dimension: 1536
- Persist directory: `data/chroma_db/`

## Coding Standards

- Python 3.11
- Surgical edits only — no full file rewrites
- Always use `try/except` with meaningful error messages
- Preserve all interfaces and the chunk metadata schema above
