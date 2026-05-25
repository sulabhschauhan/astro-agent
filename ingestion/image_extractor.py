"""
image_extractor.py
Sends diagram page images to GPT-4o vision to extract structured text.
Fills the 'text' field on diagram chunks. Idempotent via a JSON log file.
"""

import os
import base64
import json
import time
import logging
from pathlib import Path
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

PROCESSED_LOG = "data/processed_chunks.json"
REQUEST_DELAY = 1.0  # seconds between GPT-4o calls — stay within RPM limits

EXTRACTION_PROMPT = """You are analyzing a scanned diagram from a classical Vedic astrology or palmistry text.
Extract ALL information visible in this image with complete precision.

For astrology diagrams (birth charts, kundalis, planetary tables, nakshatra grids):
- All planetary symbols and their positions (e.g. Sun in 7th house, Mars at 14°32')
- House numbers (1–12) and their contents
- Degree and minute values for planets and cusps
- Rashi (zodiac sign) names in Sanskrit and/or English
- Nakshatra names, padas, and any grid values
- Dasha/antardasha tables if present
- All Sanskrit and English labels, abbreviations, and annotations

For palmistry diagrams (hand maps, line charts, mount diagrams):
- All line names (life line, head line, heart line, fate line, sun line, etc.)
- Mount names and their locations (Mount of Venus, Jupiter, Saturn, etc.)
- Hand zones and regions with their labels
- Finger names and associated labels
- All text annotations, markings, and symbols

Return a structured plain-text description that captures every piece of information in the diagram.
Preserve all numbers, labels, and spatial relationships. Do not omit anything."""


def load_processed_ids(log_path: str) -> set:
    """Return set of chunk_ids already successfully processed."""
    if not Path(log_path).exists():
        return set()
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception as e:
        logger.warning(f"Could not read processed log ({log_path}): {e} — starting fresh")
        return set()


def save_processed_id(chunk_id: str, log_path: str) -> None:
    """Append chunk_id to the processed log."""
    processed = load_processed_ids(log_path)
    processed.add(chunk_id)
    os.makedirs(Path(log_path).parent, exist_ok=True)
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(list(processed), f)
    except Exception as e:
        logger.error(f"Failed to write processed log: {e}")


def encode_image(image_path: str) -> str:
    """Read image file and return base64-encoded string."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def call_gpt4o_vision(image_path: str, client: OpenAI, model: str) -> str:
    """Send a single image to GPT-4o vision and return extracted text."""
    b64 = encode_image(image_path)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": EXTRACTION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64}",
                            "detail": "high",
                        },
                    },
                ],
            }
        ],
        max_tokens=1024,
    )
    return response.choices[0].message.content.strip()


def extract_diagram_text(
    chunks: list[dict],
    model: str = "gpt-4o",
    log_path: str = PROCESSED_LOG,
) -> list[dict]:
    """
    Fill the 'text' field on diagram chunks using GPT-4o vision.
    Skips chunks that are already processed (idempotent).

    Args:
        chunks:   Full chunk list from pdf_processor — only diagram chunks are touched.
        model:    GPT-4o model ID.
        log_path: Path to the JSON resume log.

    Returns:
        Same chunk list with 'text' populated on diagram pages.
    """
    client = OpenAI()  # uses OPENAI_API_KEY from environment
    processed_ids = load_processed_ids(log_path)

    diagram_chunks = [
        c for c in chunks
        if c["page_type"] == "diagram" and c.get("image_path")
    ]
    total = len(diagram_chunks)
    skipped = sum(1 for c in diagram_chunks if c["chunk_id"] in processed_ids)
    logger.info(f"Diagram chunks: {total} total, {skipped} already processed, {total - skipped} to extract")

    for i, chunk in enumerate(diagram_chunks, start=1):
        chunk_id = chunk["chunk_id"]

        if chunk_id in processed_ids:
            logger.info(f"[{i}/{total}] Skipping {chunk_id} (already processed)")
            continue

        image_path = chunk["image_path"]
        if not Path(image_path).exists():
            logger.error(f"[{i}/{total}] Image not found: {image_path} — skipping")
            continue

        try:
            logger.info(f"[{i}/{total}] Extracting: {chunk_id}")
            extracted_text = call_gpt4o_vision(image_path, client, model)
            chunk["text"] = extracted_text
            save_processed_id(chunk_id, log_path)
            logger.info(f"[{i}/{total}] Done — {len(extracted_text.split())} words extracted")
        except Exception as e:
            logger.error(f"[{i}/{total}] GPT-4o failed for {chunk_id}: {e} — skipping")
            continue

        if i < total:
            time.sleep(REQUEST_DELAY)

    return chunks


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from ingestion.pdf_processor import process_pdf

    PDF_DIR = "data/pdfs"
    OUTPUT_DIR = "data/extracted_images"

    test_pdf = list(Path(PDF_DIR).glob("*.pdf"))[0]
    logger.info(f"Test run on: {test_pdf.name}")

    chunks = process_pdf(str(test_pdf), OUTPUT_DIR)
    chunks = extract_diagram_text(chunks)

    diagram_chunks = [c for c in chunks if c["page_type"] == "diagram"]
    filled = [c for c in diagram_chunks if c["text"]]
    print(f"\n--- Results ---")
    print(f"Diagram pages: {len(diagram_chunks)}")
    print(f"Text extracted: {len(filled)}")
    if filled:
        print(f"\nSample extraction:\n{filled[0]['text'][:500]}")
