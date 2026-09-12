"""
THROWAWAY PROBE — read-only sample of mixed-page OCR recovery.

Does NOT write to any JSON, does NOT call any vision API, does NOT modify
ingestion/ or agent/. Imports and calls ingestion.pdf_processor.ocr_image()
unchanged (same lang="eng+hin", psm=3) so recovered text is directly
comparable to the rest of the book's OCR'd text pages.

Samples 8 fixed page_refs from data/progress/BPHS - 1 RSanthanam.json,
loads each entry's saved image_path, runs ocr_image() on it, and writes
a full report to diagnostics/latest_run.md (overwrite-only).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image
from ingestion.pdf_processor import ocr_image  # noqa: E402  (unmodified project function)

PROGRESS_PATH = "data/progress/BPHS - 1 RSanthanam.json"
TARGET_PAGE_REFS = [201, 204, 206, 226, 35, 82, 280, 350]
OUT_PATH = "diagnostics/latest_run.md"


def main():
    with open(PROGRESS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    by_ref = {e["page_ref"]: e for e in data}

    lines = []
    lines.append("# Probe: mixed-page OCR recovery sample (S126 continuation)")
    lines.append("")
    lines.append(f"Source progress file: `{PROGRESS_PATH}`")
    lines.append(f"Sample page_refs: {TARGET_PAGE_REFS}")
    lines.append("")

    results = []

    for pr in TARGET_PAGE_REFS:
        entry = by_ref.get(pr)
        lines.append(f"## page_ref {pr}")
        if entry is None:
            lines.append("**MISSING ENTRY IN PROGRESS JSON — skipped.**")
            lines.append("")
            results.append((pr, None, None))
            continue

        image_path = entry["image_path"]
        printed_page = pr + 1
        image_exists = os.path.exists(image_path)
        image_size = os.path.getsize(image_path) if image_exists else None

        lines.append(f"- page_ref: {pr}")
        lines.append(f"- printed page (page_ref+1): {printed_page}")
        lines.append(f"- page_type (progress json): {entry.get('page_type')}")
        lines.append(f"- image_path: `{image_path}`")
        lines.append(f"- image file size: {image_size} bytes" if image_exists else "- image file MISSING")
        lines.append("")

        if not image_exists:
            results.append((pr, entry, None))
            continue

        img = Image.open(image_path)
        recovered = ocr_image(img)

        char_count = len(recovered)
        line_count = len(recovered.splitlines())

        lines.append(f"Character count: {char_count}")
        lines.append(f"Line count: {line_count}")
        lines.append("")
        lines.append("Recovered text (verbatim, unedited):")
        lines.append("```")
        lines.append(recovered)
        lines.append("```")
        lines.append("")

        results.append((pr, entry, recovered))

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Wrote report to {OUT_PATH}")
    for pr, entry, recovered in results:
        if recovered is None:
            print(f"page_ref {pr}: NO TEXT RECOVERED / MISSING")
        else:
            print(f"page_ref {pr}: {len(recovered)} chars, {len(recovered.splitlines())} lines")


if __name__ == "__main__":
    main()
