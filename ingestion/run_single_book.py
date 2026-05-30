"""
run_single_book.py
Ingestion pipeline for a single new PDF (English, no translator).
Stages: pdf_processor → image_extractor → chunker → embedder

Usage:
    python ingestion/run_single_book.py "data/pdfs/Jyotish_Lal Kitab_B.M. Gosvami.pdf"
"""

import json
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path

_LOG_FILE = "data/run_single_book.log"
Path("data").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(_LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.pdf_processor import process_pdf       # noqa: E402
from ingestion.image_extractor import extract_diagram_text  # noqa: E402
from ingestion.chunker import chunk_all               # noqa: E402
from ingestion.embedder import run_pipeline           # noqa: E402

PDF_DIR        = "data/pdfs"
OUTPUT_DIR     = "data/extracted_images"
PROGRESS_DIR   = "data/progress"
ALL_CHUNKS     = "data/all_chunks.json"
CHUNKED_CHUNKS = "data/chunked_chunks.json"


def _save_progress(chunks: list[dict], path: Path) -> None:
    tmp = path.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
    except Exception as e:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"Failed to save progress to {path}: {e}") from e


def _merge_progress(progress_dir: str, output_path: str) -> list[dict]:
    progress_path = Path(progress_dir)
    progress_files = sorted(progress_path.glob("*.json"))
    all_chunks: list[dict] = []
    for pf in progress_files:
        chunks = json.loads(pf.read_text(encoding="utf-8"))
        all_chunks.extend(chunks)
        logger.info("Merged %-60s  %d chunks", pf.name, len(chunks))
    out = Path(output_path)
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps(all_chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(out)
    logger.info("all_chunks.json written — %d total page chunks", len(all_chunks))
    return all_chunks


def main(pdf_path: str) -> None:
    start = datetime.now(timezone.utc)
    book_name = Path(pdf_path).stem
    progress_dir = Path(PROGRESS_DIR)
    progress_dir.mkdir(parents=True, exist_ok=True)
    progress_file = progress_dir / f"{book_name}.json"

    logger.info("=" * 70)
    logger.info("SINGLE BOOK INGEST STARTED  %s", start.isoformat())
    logger.info("PDF:       %s", pdf_path)
    logger.info("book_name: %s", book_name)
    logger.info("=" * 70)

    # ── Stage 1: pdf_processor ──────────────────────────────────────────────
    if progress_file.exists():
        logger.info("Stage 1 — SKIPPED (progress file exists): %s", progress_file)
        raw_chunks = json.loads(progress_file.read_text(encoding="utf-8"))
    else:
        logger.info("Stage 1 — pdf_processor (OCR, %s)", pdf_path)
        raw_chunks = process_pdf(pdf_path, OUTPUT_DIR)
        _save_progress(raw_chunks, progress_file)

    text_pages    = sum(1 for c in raw_chunks if c["page_type"] == "text")
    diagram_pages = sum(1 for c in raw_chunks if c["page_type"] in ("diagram", "mixed"))
    logger.info("Stage 1 DONE — pages: %d  (text=%d, diagram/mixed=%d)",
                len(raw_chunks), text_pages, diagram_pages)
    print(f"\n[Stage 1 COMPLETE] page count: {len(raw_chunks)}  text={text_pages}  diagram/mixed={diagram_pages}\n")

    # ── Stage 2: image_extractor ─────────────────────────────────────────────
    logger.info("Stage 2 — image_extractor (GPT-4o vision on diagram pages)")
    diagram_before = sum(1 for c in raw_chunks if c["page_type"] == "diagram" and c.get("image_path"))
    raw_chunks = extract_diagram_text(raw_chunks)
    diagram_filled = sum(1 for c in raw_chunks if c["page_type"] == "diagram" and c.get("text", "").strip())
    _save_progress(raw_chunks, progress_file)
    logger.info("Stage 2 DONE — diagram pages: %d, text extracted: %d", diagram_before, diagram_filled)
    print(f"\n[Stage 2 COMPLETE] diagram pages: {diagram_before}  text extracted: {diagram_filled}\n")

    # ── Stage 3: merge + chunker ──────────────────────────────────────────────
    logger.info("Stage 3 — merging all progress files → chunker")
    all_raw = _merge_progress(PROGRESS_DIR, ALL_CHUNKS)
    sub_chunks = chunk_all(all_raw)

    # Isolate new book's chunks for reporting
    new_chunks = [c for c in sub_chunks if c["book_name"] == book_name]
    logger.info("Stage 3 DONE — total sub-chunks: %d  new book: %d", len(sub_chunks), len(new_chunks))
    print(f"\n[Stage 3 COMPLETE] chunk count (new book only): {len(new_chunks)}  total: {len(sub_chunks)}\n")

    # Save for embedder
    out = Path(CHUNKED_CHUNKS)
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps(sub_chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(out)
    logger.info("chunked_chunks.json written → %s", CHUNKED_CHUNKS)

    # ── Stage 4: embedder ─────────────────────────────────────────────────────
    logger.info("Stage 4 — embedder (OpenAI + ChromaDB upsert)")
    report = run_pipeline()
    logger.info("Stage 4 DONE — ChromaDB total: %d", report["collection_count"])
    new_book_stats = report["by_book"].get(book_name, {})
    print(f"\n[Stage 4 COMPLETE] ChromaDB total: {report['collection_count']}")
    print(f"New book embedded: {new_book_stats.get('embedded', 'N/A')}  pending: {new_book_stats.get('pending', 'N/A')}")
    print(f"\nExact book_name stored in ChromaDB: '{book_name}'")

    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    h, rem = divmod(int(elapsed), 3600)
    m, s   = divmod(rem, 60)
    logger.info("=" * 70)
    logger.info("SINGLE BOOK INGEST COMPLETE  elapsed: %dh %dm %ds", h, m, s)
    logger.info("book_name in ChromaDB: '%s'", book_name)
    logger.info("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingestion/run_single_book.py <pdf_path>")
        sys.exit(1)
    main(sys.argv[1])
