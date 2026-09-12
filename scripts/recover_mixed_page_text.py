"""
Full recovery run: OCRs every empty-text, page_type mixed/diagram entry of
a given book's progress JSON via ingestion.pdf_processor.ocr_image()
(unmodified), and stages the results into
data/recovery/<slug>_mixed_recovery_v1.json.

Read-only against data/progress/*.json -- never writes there. No vision API
calls. Recovered text is stored verbatim, uncleaned; this script produces
merge CANDIDATES only, it does not decide what gets merged.

Idempotent / resumable: on restart, any page_ref already present in the
staging file is skipped, never re-OCR'd. Checkpoints every 10 pages.

Usage: python scripts/recover_mixed_page_text.py [--book "BOOK NAME"] [--slug slug]
Defaults preserve original BPHS-1 behavior when run with no args.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from PIL import Image
from ingestion.pdf_processor import ocr_image  # noqa: E402  (unmodified project function)

SCRIPT_PATH = "scripts/recover_mixed_page_text.py"

PLANET_TOKENS = [
    "Sun", "Moon", "Mars", "Merc", "Jup", "Ven", "Sat",
    "Rahu", "Ketu", "Asc", "Ascdt", "Rasi", "RASI",
]
PLANET_RE = re.compile(r"\b(?:" + "|".join(re.escape(t) for t in PLANET_TOKENS) + r")\b")
LATIN_WORD_RE = re.compile(r"[A-Za-z]+")
DIGIT_TOKEN_RE = re.compile(r"\b\d+\b")
DEVANAGARI_RE = re.compile(r"[ऀ-ॿ]")
LEADING_INT_RE = re.compile(r"^\s*(\d{1,3})\b")


def git_head():
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT)
        return out.decode().strip()
    except Exception:
        return None


def compute_signals(text):
    lines = text.split("\n")

    devanagari_char_count = len(DEVANAGARI_RE.findall(text))
    latin_word_count = len(LATIN_WORD_RE.findall(text))
    digit_token_count = len(DIGIT_TOKEN_RE.findall(text))
    planet_token_hits = len(PLANET_RE.findall(text))

    sloka_numbers_found = []
    for line in lines:
        m = LEADING_INT_RE.match(line)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 200:
                sloka_numbers_found.append(n)

    longest_prose_run = 0
    cur = 0
    for line in lines:
        w = len(LATIN_WORD_RE.findall(line))
        if w >= 6:
            cur += 1
            longest_prose_run = max(longest_prose_run, cur)
        else:
            cur = 0

    return {
        "devanagari_char_count": devanagari_char_count,
        "latin_word_count": latin_word_count,
        "digit_token_count": digit_token_count,
        "planet_token_hits": planet_token_hits,
        "sloka_numbers_found": sloka_numbers_found,
        "longest_prose_run": longest_prose_run,
    }


def load_staging():
    if os.path.exists(STAGING_PATH):
        with open(STAGING_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"meta": {}, "pages": []}


def save_staging(staging):
    os.makedirs(os.path.dirname(STAGING_PATH), exist_ok=True)
    pages = staging["pages"]
    succeeded = sum(1 for p in pages if p["ocr_status"] == "ok")
    failed = sum(1 for p in pages if p["ocr_status"] != "ok")
    staging["meta"] = {
        "source_progress_file": PROGRESS_PATH,
        "source_book_name": BOOK_NAME,
        "script_path": SCRIPT_PATH,
        "ocr_function": "ingestion.pdf_processor.ocr_image",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "git_head": git_head(),
        "total_pages_attempted": len(pages),
        "succeeded": succeeded,
        "failed": failed,
    }
    tmp_path = STAGING_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(staging, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, STAGING_PATH)


def main():
    global PROGRESS_PATH, BOOK_NAME, STAGING_PATH

    parser = argparse.ArgumentParser()
    parser.add_argument("--book", default="BPHS - 1 RSanthanam",
                         help='Book name, matches data/progress/<book>.json')
    parser.add_argument("--slug", default="bphs1",
                         help="Staging file slug -> data/recovery/<slug>_mixed_recovery_v1.json")
    args = parser.parse_args()

    BOOK_NAME = args.book
    PROGRESS_PATH = f"data/progress/{BOOK_NAME}.json"
    STAGING_PATH = f"data/recovery/{args.slug}_mixed_recovery_v1.json"

    with open(PROGRESS_PATH, encoding="utf-8") as f:
        progress = json.load(f)

    targets = [
        e for e in progress
        if e.get("text", "") == "" and e.get("page_type") in ("mixed", "diagram")
    ]
    print(f"Found {len(targets)} target entries (empty text, page_type mixed/diagram).")

    staging = load_staging()
    done_refs = {p["page_ref"] for p in staging["pages"]}
    print(f"Staging file already has {len(done_refs)} pages recorded; resuming.")

    processed_this_run = 0
    for entry in targets:
        page_ref = entry["page_ref"]
        if page_ref in done_refs:
            continue

        image_path = entry["image_path"]
        page_record = {
            "chunk_id": entry["chunk_id"],
            "page_ref": page_ref,
            "printed_page": page_ref + 1,
            "page_type": entry["page_type"],
            "image_path": image_path,
            "image_bytes": None,
            "recovered_text": "",
            "char_count": 0,
            "line_count": 0,
            "ocr_status": None,
            "ocr_error": None,
            "signals": None,
        }

        if not os.path.exists(image_path):
            page_record["ocr_status"] = "image_missing"
            page_record["signals"] = compute_signals("")
        else:
            page_record["image_bytes"] = os.path.getsize(image_path)
            try:
                img = Image.open(image_path)
                recovered = ocr_image(img)
                page_record["recovered_text"] = recovered
                page_record["char_count"] = len(recovered)
                page_record["line_count"] = len(recovered.splitlines())
                page_record["ocr_status"] = "ok"
                page_record["signals"] = compute_signals(recovered)
            except Exception as e:
                page_record["ocr_status"] = "ocr_error"
                page_record["ocr_error"] = f"{type(e).__name__}: {e}"
                page_record["signals"] = compute_signals("")

        staging["pages"].append(page_record)
        done_refs.add(page_ref)
        processed_this_run += 1

        if processed_this_run % 10 == 0:
            print(
                f"Progress: {processed_this_run} processed this run "
                f"({len(done_refs)}/{len(targets)} total done). Checkpointing."
            )
            save_staging(staging)

    save_staging(staging)
    print(
        f"Done. {processed_this_run} pages processed this run. "
        f"{len(done_refs)}/{len(targets)} total in staging file."
    )


if __name__ == "__main__":
    main()
