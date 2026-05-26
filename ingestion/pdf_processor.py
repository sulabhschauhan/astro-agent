"""
pdf_processor.py
Converts PDF pages to images, classifies as text/diagram,
runs Tesseract OCR on text pages.
Output: list of chunk dicts with metadata
"""

import os
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Tesseract executable path — Windows
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Poppler path — required by pdf2image on Windows
POPPLER_PATH = r"C:\Program Files\poppler-26.02.0\Library\bin"

# Thresholds
MIN_TEXT_WORDS = 50  # pages with fewer words treated as diagram pages

def pdf_to_images(pdf_path: str) -> list[Image.Image]:
    """Convert all pages of a PDF to PIL images."""
    try:
        images = convert_from_path(
            pdf_path,
            dpi=300,  # high DPI for better OCR accuracy
            poppler_path=POPPLER_PATH
        )
        logger.info(f"Converted {len(images)} pages from {Path(pdf_path).name}")
        return images
    except Exception as e:
        logger.error(f"Failed to convert PDF {pdf_path}: {e}")
        raise

PLANETARY_KEYWORDS = {"Ketu", "Merc", "Sun", "Moon", "Mars", "Jup", "Sat", "Rahu", "Ven", "Asc", "Rasi", "Lagna"}
PLANET_MATCH_THRESHOLD = 3
NUMBER_DENSITY_THRESHOLD = 0.30
MIXED_NUMBER_DENSITY_MIN = 0.20   # numeric density between this and 0.30 → table embedded in prose


def classify_page(text: str) -> str:
    """Classify page as 'text', 'diagram', or 'mixed' based on word count, number density, and planetary keywords."""
    tokens = text.split()
    word_count = len(tokens)

    if word_count < MIN_TEXT_WORDS:
        return "diagram"

    numeric_count = sum(1 for t in tokens if any(ch.isdigit() for ch in t))
    numeric_density = numeric_count / word_count

    tokens_lower = [t.lower() for t in tokens]
    matched = sum(1 for kw in PLANETARY_KEYWORDS if kw.lower() in tokens_lower)

    # High number density — mixed if substantial prose present, else pure diagram
    if numeric_density > NUMBER_DENSITY_THRESHOLD:
        return "mixed" if word_count > 250 else "diagram"

    # Strong planetary keyword presence — mixed if prose present, else pure diagram
    if matched >= PLANET_MATCH_THRESHOLD:
        return "mixed" if word_count > 150 else "diagram"

    # Moderate number density alongside prose
    if numeric_density > MIXED_NUMBER_DENSITY_MIN and word_count >= 150:
        return "mixed"

    # Pattern 3 — structural grid tables (body part grids, house grids)
    STRUCTURAL_KEYWORDS = ["left", "right", "ascendant", "decanate",
                           "trunk", "shoulder", "neck", "thigh", "knee", "navel", "pelvis"]
    structural_count = sum(1 for kw in STRUCTURAL_KEYWORDS if kw in tokens_lower)
    if structural_count >= 4 and word_count >= 150:
        return "mixed"

    # Pattern 4 — illustration with prose (Cheiro hand drawings)
    ILLUSTRATION_MARKERS = ["plate", "fig.", "figure", "no.",
                            "illustration", "clubbed", "jointed", "phalange"]
    illustration_count = sum(1 for kw in ILLUSTRATION_MARKERS if kw in tokens_lower)
    if illustration_count >= 2 and word_count >= 200:
        return "mixed"

    return "text"

def split_page(image: Image.Image) -> tuple[Image.Image, Image.Image]:
    """Split a full-page image vertically at the midpoint. Returns (left, right)."""
    mid = image.width // 2
    left = image.crop((0, 0, mid, image.height))
    right = image.crop((mid, 0, image.width, image.height))
    return left, right


def ocr_image(image: Image.Image) -> str:
    """Run Tesseract OCR on a PIL image. Supports English + Hindi."""
    try:
        text = pytesseract.image_to_string(
            image,
            lang="eng+hin",  # bilingual OCR
            config="--psm 3"  # fully automatic page segmentation
        )
        return text.strip()
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return ""

def save_diagram_image(image: Image.Image, book_name: str, page_num: int, output_dir: str) -> str:
    """Save diagram page as image file for later GPT-4o processing."""
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{book_name}_page_{page_num}.jpg"
    filepath = os.path.join(output_dir, filename)
    image.save(filepath, "JPEG", quality=85)
    return filepath

def process_pdf(pdf_path: str, output_dir: str, split_spreads: bool = False) -> list[dict]:
    """
    Main processor: converts PDF → images → OCR → classified chunks.

    Args:
        pdf_path:      Full path to PDF file
        output_dir:    Directory to save diagram images
        split_spreads: Set True only for double-page spread PDFs. Each image is
                       split at width // 2 and processed as separate L/R chunks.

    Returns:
        List of chunk dicts with metadata
    """
    book_name = Path(pdf_path).stem  # filename without extension
    chunks = []

    logger.info(f"Processing: {book_name} (split_spreads={split_spreads})")
    images = pdf_to_images(pdf_path)

    for page_num, image in enumerate(images, start=1):
        halves = list(zip(split_page(image), ("L", "R"))) if split_spreads else [(image, "")]
        for half, side in halves:
            try:
                raw_text = ocr_image(half)
                page_type = classify_page(raw_text)
                chunk_id = f"{book_name}_p{page_num}{side}"

                if page_type == "text":
                    chunk = {
                        "chunk_id": chunk_id,
                        "text": raw_text,
                        "topic": "",           # filled by chunker.py later
                        "language": "eng",     # updated by chunker.py later
                        "page_ref": page_num,
                        "image_path": None,
                        "book_name": book_name,
                        "page_type": "text"
                    }
                else:
                    img_label = f"{page_num}{side}" if split_spreads else page_num
                    image_path = save_diagram_image(half, book_name, img_label, output_dir)
                    chunk = {
                        "chunk_id": chunk_id,
                        "text": "",            # filled by image_extractor.py later
                        "topic": "",
                        "language": "eng",
                        "page_ref": page_num,
                        "image_path": image_path,
                        "book_name": book_name,
                        "page_type": page_type
                    }

                chunks.append(chunk)
                logger.info(f"Page {page_num}{side}/{len(images)} — {page_type} — words: {len(raw_text.split())}")

            except Exception as e:
                logger.error(f"Failed on page {page_num}{side} of {book_name}: {e}")
                continue

    logger.info(f"Completed {book_name}: {len(chunks)} pages processed")
    return chunks

def process_all_pdfs(pdf_dir: str, output_dir: str) -> list[dict]:
    """Process all PDFs in a directory. Sorted by file size ascending — largest runs last."""
    all_chunks = []
    pdf_files = sorted(Path(pdf_dir).glob("*.pdf"), key=lambda p: p.stat().st_size)

    if not pdf_files:
        logger.warning(f"No PDFs found in {pdf_dir}")
        return []

    logger.info(f"Found {len(pdf_files)} PDFs to process")

    for pdf_path in pdf_files:
        try:
            chunks = process_pdf(str(pdf_path), output_dir)
            all_chunks.extend(chunks)
        except Exception as e:
            logger.error(f"Skipping {pdf_path.name} due to error: {e}")
            continue

    logger.info(f"Total chunks extracted: {len(all_chunks)}")
    return all_chunks


# Quick test — run this file directly to validate
if __name__ == "__main__":
    PDF_DIR = "data/pdfs"
    OUTPUT_DIR = "data/extracted_images"

    # Test with single PDF first
    test_pdf = list(Path(PDF_DIR).glob("*.pdf"))[0]
    logger.info(f"Test run on: {test_pdf.name}")

    chunks = process_pdf(str(test_pdf), OUTPUT_DIR)

    # Print summary
    text_pages = [c for c in chunks if c["page_type"] == "text"]
    diagram_pages = [c for c in chunks if c["page_type"] == "diagram"]

    print(f"\n--- Results ---")
    print(f"Total pages: {len(chunks)}")
    print(f"Text pages: {len(text_pages)}")
    print(f"Diagram pages: {len(diagram_pages)}")
    print(f"\nSample chunk:")
    print(chunks[0] if chunks else "No chunks")