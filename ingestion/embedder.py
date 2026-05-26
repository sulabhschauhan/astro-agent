"""
embedder.py
Loads all_chunks.json → chunk_all() → embeds via OpenAI → writes to ChromaDB.
Pending chunks (empty text) saved to data/pending_chunks.json.
Coverage stats saved to data/embedding_report.json.
"""

import json
import logging
import time
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv
import chromadb
from openai import OpenAI, RateLimitError

load_dotenv(Path(__file__).parent.parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

CHROMA_DIR = "data/chroma_db"
COLLECTION_NAME = "astro_chunks"
EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 100
RATE_LIMIT_RETRIES = 4
RATE_LIMIT_BASE_DELAY = 10  # seconds; doubles each retry (10, 20, 40, 80)
ALL_CHUNKS_PATH = "data/all_chunks.json"
PENDING_CHUNKS_PATH = "data/pending_chunks.json"
EMBEDDING_REPORT_PATH = "data/embedding_report.json"


def get_collection(persist_dir: str = CHROMA_DIR) -> chromadb.Collection:
    client = chromadb.PersistentClient(path=persist_dir)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _embed_batch(texts: list[str], client: OpenAI) -> list[list[float]]:
    """Embed a batch of texts with exponential backoff on rate limit errors."""
    for attempt in range(RATE_LIMIT_RETRIES):
        try:
            response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
            return [item.embedding for item in response.data]
        except RateLimitError:
            if attempt == RATE_LIMIT_RETRIES - 1:
                raise
            delay = RATE_LIMIT_BASE_DELAY * (2 ** attempt)
            logger.warning(f"Rate limit hit — retrying in {delay}s (attempt {attempt + 1}/{RATE_LIMIT_RETRIES})")
            time.sleep(delay)


def _to_metadata(chunk: dict) -> dict:
    """ChromaDB-safe metadata — no None values, embedding_status excluded."""
    return {
        "topic":      chunk.get("topic") or "",
        "language":   chunk.get("language") or "eng",
        "page_ref":   chunk.get("page_ref") or 0,
        "image_path": chunk.get("image_path") or "",
        "book_name":  chunk.get("book_name") or "",
        "page_type":  chunk.get("page_type") or "",
        "word_count": chunk.get("word_count") or 0,
    }


def run_pipeline(
    raw_chunks_path: str = ALL_CHUNKS_PATH,
    persist_dir: str = CHROMA_DIR,
    pending_path: str = PENDING_CHUNKS_PATH,
    report_path: str = EMBEDDING_REPORT_PATH,
) -> dict:
    """
    Full pipeline: load raw chunks → chunk_all() → embed → report.
    Returns the embedding report dict.
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from ingestion.chunker import chunk_all

    # Step 1 — load raw page chunks
    logger.info(f"Loading raw chunks from {raw_chunks_path}")
    with open(raw_chunks_path, "r", encoding="utf-8") as f:
        raw_chunks = json.load(f)
    logger.info(f"Loaded {len(raw_chunks)} raw page chunks")

    # Step 2 — chunk_all
    sub_chunks = chunk_all(raw_chunks)
    logger.info(f"Chunker produced {len(sub_chunks)} sub-chunks")

    # Step 3 — assign embedding_status (JSON only, not stored in ChromaDB)
    for chunk in sub_chunks:
        chunk["embedding_status"] = "complete" if chunk.get("text", "").strip() else "pending"

    pending = [c for c in sub_chunks if c["embedding_status"] == "pending"]
    embeddable = [c for c in sub_chunks if c["embedding_status"] == "complete"]
    total_batches = (len(embeddable) + BATCH_SIZE - 1) // BATCH_SIZE
    logger.info(f"Embeddable: {len(embeddable)}, Pending (empty text): {len(pending)}, Batches: {total_batches}")

    # Step 4 — save pending sub-chunks for image_extractor resume
    with open(pending_path, "w", encoding="utf-8") as f:
        json.dump(pending, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(pending)} pending chunks to {pending_path}")

    # Step 5 — embed in batches and upsert to ChromaDB
    openai_client = OpenAI()
    collection = get_collection(persist_dir)

    # Idempotency: skip chunks already present in ChromaDB
    existing_ids = set(collection.get(include=[])["ids"])
    to_embed = [c for c in embeddable if c["chunk_id"] not in existing_ids]
    skipped_existing = len(embeddable) - len(to_embed)
    if skipped_existing:
        logger.info(f"Skipping {skipped_existing} chunks already in ChromaDB — {len(to_embed)} to embed")
    total_batches = (len(to_embed) + BATCH_SIZE - 1) // BATCH_SIZE

    failed_chunk_ids = []
    for batch_num, i in enumerate(range(0, len(to_embed), BATCH_SIZE), start=1):
        batch = to_embed[i: i + BATCH_SIZE]
        try:
            embeddings = _embed_batch([c["text"] for c in batch], openai_client)
            collection.upsert(
                ids=[c["chunk_id"] for c in batch],
                embeddings=embeddings,
                documents=[c["text"] for c in batch],
                metadatas=[_to_metadata(c) for c in batch],
            )
            logger.info(f"Batch {batch_num}/{total_batches} — {len(batch)} chunks upserted")
        except Exception as e:
            failed_ids = [c["chunk_id"] for c in batch]
            logger.error(f"Batch {batch_num}/{total_batches} failed: {e} — {len(batch)} chunks lost: {failed_ids[:3]}...")
            failed_chunk_ids.extend(failed_ids)
            continue

    # Step 6 — build and save embedding_report.json
    book_stats = defaultdict(lambda: {"text": 0, "diagram": 0, "mixed": 0, "embedded": 0, "pending": 0})
    for chunk in sub_chunks:
        book_stats[chunk["book_name"]][chunk["page_type"]] += 1
        stat_key = "embedded" if chunk["embedding_status"] == "complete" else "pending"
        book_stats[chunk["book_name"]][stat_key] += 1

    report = {
        "total_raw_pages":   len(raw_chunks),
        "total_sub_chunks":  len(sub_chunks),
        "total_embedded":    len(embeddable),
        "total_pending":     len(pending),
        "total_failed":      len(failed_chunk_ids),
        "failed_chunk_ids":  failed_chunk_ids,
        "collection_count":  collection.count(),
        "by_book": {book: dict(stats) for book, stats in sorted(book_stats.items())},
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    logger.info(f"Report saved to {report_path}")
    logger.info(f"ChromaDB collection total: {collection.count()} chunks")

    return report


if __name__ == "__main__":
    report = run_pipeline()
    print(f"\n--- Embedding Report ---")
    print(f"Raw pages:      {report['total_raw_pages']}")
    print(f"Sub-chunks:     {report['total_sub_chunks']}")
    print(f"Embedded:       {report['total_embedded']}")
    print(f"Pending:        {report['total_pending']}")
    print(f"Failed batches: {report['total_failed']}")
    print(f"ChromaDB total: {report['collection_count']}")
    print(f"\nBy book:")
    for book, stats in report["by_book"].items():
        print(f"  {book}: embedded={stats['embedded']}, pending={stats['pending']}")
