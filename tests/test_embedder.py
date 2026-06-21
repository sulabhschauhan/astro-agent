"""
tests/test_embedder.py
Coverage for ingestion/embedder.py text-hash idempotency hardening
(diagnostics/embedder_hardening_proposal_20260621_100850.md).
All tests use a temp-dir PersistentClient and a mocked OpenAI client —
no network calls, no writes to the live data/chroma_db collection.
"""

import hashlib
import json
import logging
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.embedder import _to_metadata, run_pipeline, get_collection


def _seed_chunk(persist_dir: str, chunk_id: str, text: str, book_name: str = "TestBook") -> None:
    """Insert one chunk directly via the production metadata path (_to_metadata), so
    text_sha256 is populated exactly as the real pipeline would populate it."""
    collection = get_collection(persist_dir)
    chunk = {"chunk_id": chunk_id, "text": text, "book_name": book_name, "page_type": "text"}
    collection.upsert(
        ids=[chunk_id],
        embeddings=[[0.0] * 8],
        documents=[text],
        metadatas=[_to_metadata(chunk)],
    )


def _write_chunks(path: Path, chunks: list[dict]) -> None:
    path.write_text(json.dumps(chunks), encoding="utf-8")


def _run_pipeline_mocked(tmp_path: Path, raw_chunks_path: Path, persist_dir: str) -> dict:
    """run_pipeline() with the OpenAI client and embedding call both mocked — no network."""
    with patch("ingestion.embedder.OpenAI"), \
         patch("ingestion.embedder._embed_batch", return_value=[[0.0] * 8]):
        return run_pipeline(
            raw_chunks_path=str(raw_chunks_path),
            persist_dir=persist_dir,
            pending_path=str(tmp_path / "pending.json"),
            report_path=str(tmp_path / "report.json"),
        )


# ── Unit test ────────────────────────────────────────────────────────────────

def test_to_metadata_text_sha256():
    """Pure function — no ChromaDB client, no OpenAI client, no I/O."""
    chunk = {
        "text": "hello world",
        "topic": "t",
        "language": "eng",
        "page_ref": 1,
        "image_path": None,
        "book_name": "Book",
        "page_type": "text",
        "word_count": 2,
    }
    meta = _to_metadata(chunk)
    assert meta["text_sha256"] == hashlib.sha256(b"hello world").hexdigest()


# ── Integration tests (temp-dir ChromaDB, mocked OpenAI) ─────────────────────

def test_x_c0_duplicate_text_rejected(tmp_path, caplog):
    """Reproduces the documented Deva-keralam_p8_c0 / _c0_c0 failure mode:
    chunk_id X already embedded; incoming X_c0 carries byte-identical text.
    Must be rejected by the text-hash check, not the chunk_id check."""
    persist_dir = str(tmp_path / "chroma")
    _seed_chunk(persist_dir, chunk_id="X", text="identical body")

    raw_chunks_path = tmp_path / "chunked_chunks.json"
    _write_chunks(raw_chunks_path, [
        {"chunk_id": "X_c0", "text": "identical body", "book_name": "TestBook", "page_type": "text"},
    ])

    caplog.set_level(logging.INFO, logger="ingestion.embedder")
    report = _run_pipeline_mocked(tmp_path, raw_chunks_path, persist_dir)

    collection = get_collection(persist_dir)
    assert collection.count() == 1
    assert "X_c0" not in set(collection.get(include=[])["ids"])
    assert report["skipped_duplicate_text"] == 1

    # skipped_existing isn't exposed in the report dict; verified indirectly —
    # the chunk_id-collision branch only logs when skipped_existing > 0 (embedder.py
    # lines 107-108), so its absence here confirms X_c0 was caught by the new
    # text-hash check, not the pre-existing chunk_id check.
    assert not any("already in ChromaDB" in r.message for r in caplog.records)

    warnings = [r for r in caplog.records if r.levelname == "WARNING" and "X_c0" in r.message]
    assert len(warnings) == 1
    assert "text_sha256" in warnings[0].message


def test_intra_batch_duplicate_text_rejected(tmp_path, caplog):
    """Two new chunks in the same run, different ids, identical text — the
    in-batch `seen` set must catch the second one even with an empty collection."""
    persist_dir = str(tmp_path / "chroma")

    raw_chunks_path = tmp_path / "chunked_chunks.json"
    _write_chunks(raw_chunks_path, [
        {"chunk_id": "A", "text": "same text", "book_name": "TestBook", "page_type": "text"},
        {"chunk_id": "B", "text": "same text", "book_name": "TestBook", "page_type": "text"},
    ])

    caplog.set_level(logging.INFO, logger="ingestion.embedder")
    report = _run_pipeline_mocked(tmp_path, raw_chunks_path, persist_dir)

    collection = get_collection(persist_dir)
    assert collection.count() == 1
    assert report["skipped_duplicate_text"] == 1

    warnings = [r for r in caplog.records if r.levelname == "WARNING" and "B" in r.message]
    assert len(warnings) == 1
    assert "in-batch" in warnings[0].message
