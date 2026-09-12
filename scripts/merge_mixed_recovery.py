"""
Merges a book's Tesseract-recovered pages (data/recovery/<slug>_mixed_recovery_v1.json)
into its data/progress/<book>.json, tagging every entry's provenance with
text_source/content_class.

Backs up the progress file FIRST (byte-verified via SHA-256) -- data/progress
is gitignored from git's perspective by history predating this repo's own
tracking of it in some clones, and in any case this script must never touch
production data without an independently-verified backup.

Merge matches on chunk_id, not page_ref. For recovered entries, text is
replaced with recovered_text VERBATIM (uncleaned, Devanagari kept as-is).
For entries that already had text, text is left untouched -- only the two
new keys are added. page_type/page_ref/image_path/book_name/topic/language
are never touched for any entry.

content_class is derived per-page from the recovery staging file's own
mechanical signals (planet_token_hits / longest_prose_run), not a hardcoded
page_ref list -- this is the same "chart-dominant" rule used for BPHS-1
(planet_token_hits >= 5 AND longest_prose_run <= 2 => non_prose).

Does NOT run chunker.py or embedder.py. Does NOT touch ChromaDB. Does NOT
reclassify page_type. Does NOT clean any text.

Usage: python scripts/merge_mixed_recovery.py [--book "BOOK NAME"] [--slug slug]
Defaults preserve original BPHS-1 behavior when run with no args.
"""
import argparse
import hashlib
import json
import os

PLANET_HITS_THRESHOLD = 5
PROSE_RUN_THRESHOLD = 2


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def backup_and_verify(progress_path, backup_path):
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    with open(progress_path, "rb") as src:
        data = src.read()
    with open(backup_path, "wb") as dst:
        dst.write(data)
    src_hash = sha256_of(progress_path)
    bak_hash = sha256_of(backup_path)
    return src_hash, bak_hash


def is_chart_dominant(rec):
    sig = rec.get("signals") or {}
    return (
        sig.get("planet_token_hits", 0) >= PLANET_HITS_THRESHOLD
        and sig.get("longest_prose_run", 0) <= PROSE_RUN_THRESHOLD
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--book", default="BPHS - 1 RSanthanam",
                         help='Book name, matches data/progress/<book>.json')
    parser.add_argument("--slug", default="bphs1",
                         help="Recovery staging slug -> data/recovery/<slug>_mixed_recovery_v1.json")
    args = parser.parse_args()

    book = args.book
    progress_path = f"data/progress/{book}.json"
    backup_dir = "data/progress/_backup"
    backup_path = os.path.join(backup_dir, f"{book}.pre_recovery_v1.json")
    recovery_path = f"data/recovery/{args.slug}_mixed_recovery_v1.json"

    src_hash, bak_hash = backup_and_verify(progress_path, backup_path)
    print(f"source sha256: {src_hash}")
    print(f"backup sha256: {bak_hash}")
    if src_hash != bak_hash:
        print("HASH MISMATCH -- STOPPING, no merge performed.")
        return
    print("Backup verified byte-identical.")

    with open(recovery_path, encoding="utf-8") as f:
        recovery = json.load(f)

    recovery_by_chunk_id = {p["chunk_id"]: p for p in recovery["pages"]}

    non_ok = [cid for cid, p in recovery_by_chunk_id.items() if p["ocr_status"] != "ok"]
    if non_ok:
        print(f"REFUSING TO MERGE -- {len(non_ok)} recovery entries are not ocr_status=='ok': {non_ok}")
        return

    with open(progress_path, encoding="utf-8") as f:
        progress = json.load(f)

    recovered_count = 0
    original_count = 0
    chart_dominant_refs = []
    for entry in progress:
        chunk_id = entry["chunk_id"]
        if chunk_id in recovery_by_chunk_id:
            rec = recovery_by_chunk_id[chunk_id]
            entry["text"] = rec["recovered_text"]
            entry["text_source"] = "tesseract_recovery_v1"
            if is_chart_dominant(rec):
                entry["content_class"] = "non_prose"
                chart_dominant_refs.append(rec["page_ref"])
            else:
                entry["content_class"] = "prose"
            recovered_count += 1
        else:
            entry["text_source"] = "original_ingest"
            entry["content_class"] = "prose"
            original_count += 1

    print(f"Merged: {recovered_count} recovered entries, {original_count} original entries.")
    print(f"Chart-dominant (non_prose) page_refs: {sorted(chart_dominant_refs)}")

    with open(progress_path, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

    print(f"Wrote merged file: {progress_path}")


if __name__ == "__main__":
    main()
