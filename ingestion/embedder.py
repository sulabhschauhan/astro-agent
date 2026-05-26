"""
embedder.py
Embeds chunk text via OpenAI text-embedding-3-small and upserts into ChromaDB.
Idempotent — upsert handles re-runs safely. Skips chunks with empty text.
"""

import json
import logging
from pathlib import Path
import chromadb
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

CHROMA_DIR = "data/chroma_db"
COLLECTION_NAME = "astro_chunks"
EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 100  # chunks per OpenAI embeddings request


def get_collection(persist_dir: str = CHROMA_DIR) -> chromadb.Collection:
    """Get or create the persistent ChromaDB collection."""
    client = chromadb.PersistentClient(path=persist_dir)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _embed_batch(texts: list[str], client: OpenAI) -> list[list[float]]:
    """Call OpenAI embeddings API for a batch of texts."""
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def _to_metadata(chunk: dict) -> dict:
    """Extract ChromaDB-safe metadata from a chunk (no None values)."""
    return {
        "topic":      chunk.get("topic") or "",
        "language":   chunk.get("language") or "eng",
        "page_ref":   chunk.get("page_ref") or 0,
        "image_path": chunk.get("image_path") or "",
        "book_name":  chunk.get("book_name") or "",
        "page_type":  chunk.get("page_type") or "",
        "word_count": chunk.get("word_count") or 0,
    }


def embed_chunks(chunks: list[dict], persist_dir: str = CHROMA_DIR) -> None:
    """
    Embed all chunks with non-empty text and upsert into ChromaDB.

    Args:
        chunks:      Chunk list from chunker.chunk_all() — full schema required.
        persist_dir: ChromaDB persist directory.
    """
    openai_client = OpenAI()  # uses OPENAI_API_KEY from environment
    collection = get_collection(persist_dir)

    embeddable = [c for c in chunks if c.get("text", "").strip()]
    skipped = len(chunks) - len(embeddable)
    total_batches = (len(embeddable) + BATCH_SIZE - 1) // BATCH_SIZE
    logger.info(
        f"Chunks to embed: {len(embeddable)}, skipped (empty text): {skipped}, "
        f"batches: {total_batches}"
    )

    for batch_num, i in enumerate(range(0, len(embeddable), BATCH_SIZE), start=1):
        batch = embeddable[i: i + BATCH_SIZE]
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
            logger.error(f"Batch {batch_num}/{total_batches} failed: {e} — skipping")
            continue

    logger.info(f"Done. Collection total: {collection.count()} chunks")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from ingestion.chunker import chunk_all

    RAW_CHUNKS_PATH = "data/all_chunks.json"

    logger.info(f"Loading raw chunks from {RAW_CHUNKS_PATH}")
    with open(RAW_CHUNKS_PATH, "r", encoding="utf-8") as f:
        raw_chunks = json.load(f)
    logger.info(f"Loaded {len(raw_chunks)} raw page chunks")

    chunked = chunk_all(raw_chunks)
    logger.info(f"Chunker produced {len(chunked)} sub-chunks")

    embed_chunks(chunked)

    # Summary
    collection = get_collection()
    count = collection.count()
    print(f"\n--- Results ---")
    print(f"Raw pages:        {len(raw_chunks)}")
    print(f"Sub-chunks:       {len(chunked)}")
    print(f"Embedded (total): {count}")
