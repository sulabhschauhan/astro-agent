"""
query_engine.py
Embeds a user question → queries ChromaDB "astro_chunks" → returns ranked results.
"""

from pathlib import Path
from dotenv import load_dotenv
import chromadb
from openai import OpenAI

load_dotenv(Path(__file__).parent.parent / ".env")

CHROMA_DIR = "data/chroma_db"
COLLECTION_NAME = "astro_chunks"
EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_N_RESULTS = 5
VALID_FILTER_KEYS = {"book_name", "topic", "page_type"}


def get_collection(persist_dir: str = CHROMA_DIR) -> chromadb.Collection:
    client = chromadb.PersistentClient(path=persist_dir)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _build_where(filters: dict) -> dict | None:
    """Convert kwargs filters to ChromaDB where clause syntax."""
    invalid = set(filters) - VALID_FILTER_KEYS
    if invalid:
        raise ValueError(f"Invalid filter keys: {invalid}. Allowed: {VALID_FILTER_KEYS}")
    clauses = [{k: {"$eq": v}} for k, v in filters.items()]
    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def search(
    question: str,
    n_results: int = DEFAULT_N_RESULTS,
    persist_dir: str = CHROMA_DIR,
    **filters,
) -> list[dict]:
    """
    Embed question and return top-n ranked chunks from ChromaDB.

    Args:
        question: User question string (must be non-empty).
        n_results: Max results to return; clamped to collection size.
        persist_dir: ChromaDB persist directory path.
        **filters: Metadata filters — allowed keys: book_name, topic, page_type.

    Returns:
        List of dicts with keys: chunk_id, text, score, book_name, topic,
        page_type, language, page_ref, image_path.
        score is similarity (1 - cosine distance), range [0, 1].

    Raises:
        ValueError: Empty question or invalid filter key.
        RuntimeError: Collection is empty (embedder.py not yet run).
    """
    if not question.strip():
        raise ValueError("question must not be empty.")

    collection = get_collection(persist_dir)

    total = collection.count()
    if total == 0:
        raise RuntimeError(
            "ChromaDB collection 'astro_chunks' is empty — run embedder.py first."
        )

    safe_n = min(n_results, total)
    where = _build_where(filters)

    openai_client = OpenAI()
    response = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=question)
    query_embedding = response.data[0].embedding

    query_kwargs: dict = {
        "query_embeddings": [query_embedding],
        "n_results": safe_n,
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        query_kwargs["where"] = where

    raw = collection.query(**query_kwargs)

    return [
        {
            "chunk_id":   chunk_id,
            "text":       text,
            "score":      round(1 - distance, 4),
            "book_name":  meta.get("book_name", ""),
            "topic":      meta.get("topic", ""),
            "page_type":  meta.get("page_type", ""),
            "language":   meta.get("language", ""),
            "page_ref":   meta.get("page_ref", 0),
            "image_path": meta.get("image_path", ""),
        }
        for chunk_id, text, meta, distance in zip(
            raw["ids"][0],
            raw["documents"][0],
            raw["metadatas"][0],
            raw["distances"][0],
        )
    ]


if __name__ == "__main__":
    question = "What is the significance of Jupiter in the 7th house?"
    print(f"Query: {question}\n")

    results = search(question, n_results=5)

    for i, r in enumerate(results, 1):
        print(f"[{i}] score={r['score']} | {r['book_name']} p.{r['page_ref']}")
        print(f"     topic:  {r['topic']}")
        print(f"     text:   {r['text'][:200]}")
        print()
