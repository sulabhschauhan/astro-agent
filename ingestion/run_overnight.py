"""
run_overnight.py
Overnight PDF ingestion pipeline with crash recovery and auto-retry.

Stage 1 — process_all_pdfs(): OCR all PDFs, save per-book progress to data/progress/
Stage 2 — Merge: reads all progress/*.json → data/all_chunks.json (atomic write)
Stage 3 — Chunker: runs chunk_all() on merged output, saves to data/chunked_chunks.json

Log: data/overnight_run.log (console + file, DEBUG level)
"""

import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Configure logging BEFORE importing modules that call logging.basicConfig() at
# module level (chunker.py, embedder.py). basicConfig() is no-op if handlers exist.
_LOG_FILE = "data/overnight_run.log"
Path("data").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(_LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent))
from ingestion.pdf_processor import process_all_pdfs  # noqa: E402
from ingestion.chunker import chunk_all               # noqa: E402

PDF_DIR        = "data/pdfs"
OUTPUT_DIR     = "data/extracted_images"
PROGRESS_DIR   = "data/progress"
ALL_CHUNKS     = "data/all_chunks.json"
CHUNKED_CHUNKS = "data/chunked_chunks.json"
RETRY_LIMIT    = 3
RETRY_DELAY    = 30


def _run_ocr_with_retry() -> list[dict]:
    for attempt in range(1, RETRY_LIMIT + 1):
        try:
            logger.info("Stage 1 — OCR pipeline (attempt %d/%d)", attempt, RETRY_LIMIT)
            chunks = process_all_pdfs(PDF_DIR, OUTPUT_DIR, PROGRESS_DIR)
            logger.info("Stage 1 complete — %d raw page chunks", len(chunks))
            return chunks
        except Exception as e:
            logger.error("Stage 1 attempt %d failed: %s", attempt, e)
            if attempt < RETRY_LIMIT:
                logger.info("Retrying in %ds...", RETRY_DELAY)
                time.sleep(RETRY_DELAY)
            else:
                raise RuntimeError(
                    f"Stage 1 failed after {RETRY_LIMIT} attempts — check {_LOG_FILE}"
                ) from e


def _merge_progress(progress_dir: str, pdf_dir: str, output_path: str) -> list[dict]:
    progress_path = Path(progress_dir)
    pdf_sizes = {p.stem: p.stat().st_size for p in Path(pdf_dir).glob("*.pdf")}
    progress_files = sorted(
        progress_path.glob("*.json"),
        key=lambda p: pdf_sizes.get(p.stem, 0),
    )
    if not progress_files:
        raise RuntimeError(f"No progress files in {progress_dir} — did Stage 1 complete?")

    all_chunks: list[dict] = []
    for pf in progress_files:
        try:
            chunks = json.loads(pf.read_text(encoding="utf-8"))
            all_chunks.extend(chunks)
            logger.info("Merged %-50s %d chunks", pf.name, len(chunks))
        except Exception as e:
            logger.error("Failed to read %s: %s", pf.name, e)
            raise

    out = Path(output_path)
    tmp = out.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(all_chunks, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(out)
    except Exception as e:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"Failed to write {output_path}: {e}") from e

    logger.info("Stage 2 complete — %d total chunks → %s", len(all_chunks), output_path)
    return all_chunks


def _run_chunker(raw_chunks: list[dict]) -> list[dict]:
    logger.info("Stage 3 — chunker (validation, no API calls)")
    sub_chunks = chunk_all(raw_chunks)

    by_lang, by_type, by_book = {}, {}, {}
    for c in sub_chunks:
        by_lang[c.get("language", "?")] = by_lang.get(c.get("language", "?"), 0) + 1
        by_type[c.get("page_type",  "?")] = by_type.get(c.get("page_type", "?"), 0) + 1
        by_book[c.get("book_name",  "?")] = by_book.get(c.get("book_name", "?"), 0) + 1

    logger.info("Stage 3 complete — %d sub-chunks", len(sub_chunks))
    logger.info("By language:  %s", by_lang)
    logger.info("By page type: %s", by_type)
    logger.info("By book:")
    for book, count in sorted(by_book.items()):
        logger.info("  %-60s %d", book, count)

    return sub_chunks


def main() -> None:
    start = datetime.now(timezone.utc)
    logger.info("=" * 70)
    logger.info("OVERNIGHT RUN STARTED  %s", start.isoformat())
    logger.info("=" * 70)

    raw_chunks = _run_ocr_with_retry()
    all_chunks = _merge_progress(PROGRESS_DIR, PDF_DIR, ALL_CHUNKS)
    sub_chunks = _run_chunker(all_chunks)

    # Save chunked output — embedder reads from this file
    out = Path(CHUNKED_CHUNKS)
    tmp = out.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(sub_chunks, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(out)
        logger.info("Chunked output saved → %s", CHUNKED_CHUNKS)
    except Exception as e:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"Failed to save {CHUNKED_CHUNKS}: {e}") from e

    end = datetime.now(timezone.utc)
    elapsed = (end - start).total_seconds()
    h, rem = divmod(int(elapsed), 3600)
    m, s   = divmod(rem, 60)
    logger.info("=" * 70)
    logger.info("OVERNIGHT RUN COMPLETE")
    logger.info("Elapsed:      %dh %dm %ds", h, m, s)
    logger.info("Raw pages:    %d", len(all_chunks))
    logger.info("Sub-chunks:   %d", len(sub_chunks))
    logger.info("Output:       %s", ALL_CHUNKS)
    logger.info("Chunked:      %s", CHUNKED_CHUNKS)
    logger.info("Log:          %s", _LOG_FILE)
    logger.info("Next step:    python ingestion/embedder.py")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
