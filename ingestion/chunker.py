"""
chunker.py
Splits, merges, and enriches page chunks from pdf_processor / image_extractor.
Adds language, topic, and word_count to all non-empty chunks.
"""

import re
import logging
from langdetect import detect, LangDetectException
from langdetect import DetectorFactory

DetectorFactory.seed = 0  # reproducible langdetect results

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Chunking parameters
MERGE_MIN_WORDS = 100
SPLIT_THRESHOLD = 500
WINDOW_SIZE = 400
WINDOW_OVERLAP = 50
LANGDETECT_MIN_WORDS = 30
DEVANAGARI_HIN_THRESHOLD = 0.25  # fraction of non-whitespace chars

# Topic keyword map — ordered by specificity, first match wins, case-insensitive
TOPIC_KEYWORDS = {
    "mahadasha": "dasha",
    "antardasha": "dasha",
    "dasha": "dasha",
    "nakshatra": "nakshatra",
    "pada": "nakshatra",
    "lagna": "lagna",
    "ascendant": "lagna",
    "yoga": "yoga",
    "bhava": "bhava",
    "house": "bhava",
    "rasi": "rasi",
    "rashi": "rasi",
    "zodiac": "rasi",
    "graha": "planets",
    "planet": "planets",
    "sun": "planets",
    "moon": "planets",
    "mars": "planets",
    "mercury": "planets",
    "jupiter": "planets",
    "venus": "planets",
    "saturn": "planets",
    "rahu": "planets",
    "ketu": "planets",
    "life line": "palmistry_lines",
    "head line": "palmistry_lines",
    "heart line": "palmistry_lines",
    "fate line": "palmistry_lines",
    "mount of": "palmistry_mounts",
    "mount": "palmistry_mounts",
}


def detect_language(text: str) -> str:
    """Devanagari check first, then langdetect, default 'eng' on failure."""
    non_ws = [c for c in text if not c.isspace()]
    if not non_ws:
        return "eng"

    devanagari_count = sum(1 for c in non_ws if "ऀ" <= c <= "ॿ")
    if devanagari_count > 0:
        return "hin" if (devanagari_count / len(non_ws)) >= DEVANAGARI_HIN_THRESHOLD else "mixed"

    if len(text.split()) < LANGDETECT_MIN_WORDS:
        return "eng"

    try:
        return "hin" if detect(text) == "hi" else "eng"
    except LangDetectException:
        return "eng"


def detect_topic(text: str) -> str:
    """Return first keyword match from TOPIC_KEYWORDS, or 'general'."""
    text_lower = text.lower()
    for keyword, topic in TOPIC_KEYWORDS.items():
        if keyword in text_lower:
            return topic
    return "general"


def split_on_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]


def merge_paragraphs(paragraphs: list[str]) -> list[str]:
    """Merge adjacent paragraphs until the buffer reaches MERGE_MIN_WORDS."""
    merged = []
    buffer = ""

    for para in paragraphs:
        if not buffer:
            buffer = para
        elif len(buffer.split()) < MERGE_MIN_WORDS:
            buffer = buffer + "\n\n" + para
        else:
            merged.append(buffer)
            buffer = para

    if buffer:
        merged.append(buffer)

    return merged


def sliding_window(text: str) -> list[str]:
    """400-word window with 50-word overlap."""
    words = text.split()
    step = WINDOW_SIZE - WINDOW_OVERLAP
    return [
        " ".join(words[i: i + WINDOW_SIZE])
        for i in range(0, len(words), step)
        if words[i: i + WINDOW_SIZE]
    ]


def _make_sub_chunks(segments: list[str], parent: dict) -> list[dict]:
    return [
        {
            "chunk_id": f"{parent['chunk_id']}_c{i}",
            "text": text,
            "topic": detect_topic(text),
            "language": detect_language(text),
            "page_ref": parent["page_ref"],
            "image_path": parent.get("image_path"),
            "book_name": parent["book_name"],
            "page_type": parent["page_type"],
            "word_count": len(text.split()),
        }
        for i, text in enumerate(segments)
    ]


def chunk_page(parent: dict) -> list[dict]:
    """
    Process a single page chunk into output sub-chunks.

    - diagram + empty text  → pass through unchanged (no enrichment, no _c suffix)
    - diagram + filled text → enrich (language/topic/word_count), no split, append _c0
    - text / mixed          → paragraph split → merge → sliding window if >500 words
    """
    text = parent.get("text", "").strip()

    if parent["page_type"] == "diagram" and not text:
        return [{**parent, "chunk_id": f"{parent['chunk_id']}_c0"}]

    if parent["page_type"] == "diagram" and text:
        enriched = {
            **parent,
            "chunk_id": f"{parent['chunk_id']}_c0",
            "topic": detect_topic(text),
            "language": detect_language(text),
            "word_count": len(text.split()),
        }
        return [enriched]

    # text and mixed pages
    paragraphs = split_on_paragraphs(text)
    if not paragraphs:
        return []

    segments = []
    for segment in merge_paragraphs(paragraphs):
        if len(segment.split()) > SPLIT_THRESHOLD:
            segments.extend(sliding_window(segment))
        else:
            segments.append(segment)

    return _make_sub_chunks(segments, parent)


def chunk_all(chunks: list[dict]) -> list[dict]:
    """Process all page chunks. Returns flat list with full schema populated."""
    output = []
    for chunk in chunks:
        sub_chunks = chunk_page(chunk)
        output.extend(sub_chunks)
        logger.info(f"{chunk['chunk_id']} → {len(sub_chunks)} sub-chunk(s)")
    logger.info(f"Total output chunks: {len(output)}")
    return output


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from ingestion.pdf_processor import process_pdf

    test_pdf = list(Path("data/pdfs").glob("*.pdf"))[0]
    logger.info(f"Test run on: {test_pdf.name}")

    chunks = process_pdf(str(test_pdf), "data/extracted_images")
    output = chunk_all(chunks)

    text_out = [c for c in output if c["page_type"] == "text"]
    diagram_out = [c for c in output if c["page_type"] == "diagram"]

    print(f"\n--- Results ---")
    print(f"Input pages:    {len(chunks)}")
    print(f"Output chunks:  {len(output)}")
    print(f"Text chunks:    {len(text_out)}")
    print(f"Diagram chunks: {len(diagram_out)}")
    print(f"Languages:      {sorted({c['language'] for c in output})}")
    print(f"Topics:         {sorted({c['topic'] for c in output})}")
    if text_out:
        s = text_out[0]
        print(f"\nSample chunk:")
        print(f"  chunk_id:   {s['chunk_id']}")
        print(f"  language:   {s['language']}")
        print(f"  topic:      {s['topic']}")
        print(f"  word_count: {s['word_count']}")
        print(f"  text[:200]: {s['text'][:200]}")
