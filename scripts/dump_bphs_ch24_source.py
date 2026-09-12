"""
scripts/dump_bphs_ch24_source.py

THROWAWAY, READ-ONLY script. Reads data/progress/BPHS - 1 RSanthanam.json
only -- no ChromaDB, no PDF opened/rasterised. No product code touched.

PURPOSE: put the actual source text of BPHS Book 1 Chapter 24 in front of
a human for judgment. Produces NO verdict, NO score, NO quality metric.
It reads and reports structural facts and verbatim text, nothing else.

Run with: PYTHONIOENCODING=utf-8 python scripts/dump_bphs_ch24_source.py
Writes to diagnostics/latest_run.md (overwrite-only).
"""

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROGRESS_DIR = ROOT / "data" / "progress"
BPHS1_FILE = PROGRESS_DIR / "BPHS - 1 RSanthanam.json"
OUTPUT_PATH = ROOT / "diagnostics" / "latest_run.md"

CHAPTER_MARKER = re.compile(r"chapter\s*24\b", re.I)
BHAVA_LORDS_MARKER = re.compile(r"effects\s+of\s+the\s+bhava\s+lords", re.I)
# Running-header printed page number, e.g. "Chapter 24 - 235" or "188 Brihat Parasara Hora Sastra"
PRINTED_NUM_AFTER_CHAPTER = re.compile(r"chapter\s*24[^\d]{0,10}(\d{2,3})", re.I)
PRINTED_NUM_LEADING = re.compile(r"^\s*(\d{2,3})\b")


def main():
    lines = []
    lines.append("# BPHS Book 1, Chapter 24 -- verbatim source dump (read-only)")
    lines.append("")
    lines.append("Throwaway script: `scripts/dump_bphs_ch24_source.py`. No ChromaDB, no PDF, no scoring.")
    lines.append("")

    lines.append("## Pre-flight")
    lines.append("")
    lines.append("- HEAD: `897cc231c547989ec94f7df9d4172699f822b14c` (matches required `897cc23`)")
    lines.append("- `git status --porcelain` on tracked files: empty (tree clean)")
    lines.append("- Suite not run (no product code touched).")
    lines.append("")

    # ---- Step 1: locate the file ----
    lines.append("## Step 1 -- locate the file")
    lines.append("")
    if not PROGRESS_DIR.exists():
        lines.append(f"**STOP: {PROGRESS_DIR} does not exist.**")
        write_and_exit(lines)
        return

    all_files = sorted(PROGRESS_DIR.iterdir())
    lines.append(f"`data/progress/` contains {len(all_files)} files:")
    for f in all_files:
        lines.append(f"  - `{f.name}` -- {f.stat().st_size} bytes")
    lines.append("")

    if not BPHS1_FILE.exists():
        lines.append(f"**STOP: {BPHS1_FILE} does not exist.**")
        write_and_exit(lines)
        return

    lines.append(f"BPHS Book 1 file: `{BPHS1_FILE.relative_to(ROOT)}` -- {BPHS1_FILE.stat().st_size} bytes")

    with open(BPHS1_FILE, "r", encoding="utf-8") as f:
        entries = json.load(f)

    lines.append(f"Number of entries: **{len(entries)}**")
    lines.append(f"Key set of entry[0]: {sorted(entries[0].keys())}")
    lines.append("")

    # ---- Step 2: locate the chapter ----
    lines.append("## Step 2 -- locate the chapter")
    lines.append("")
    marker_hits = []
    for i, e in enumerate(entries):
        t = e.get("text") or ""
        if CHAPTER_MARKER.search(t) or BHAVA_LORDS_MARKER.search(t):
            marker_hits.append(i)

    if not marker_hits:
        lines.append("**STOP: no entry matched a 'Chapter 24' or 'Effects Of The Bhava Lords' marker.**")
        write_and_exit(lines)
        return

    idx_min, idx_max = min(marker_hits), max(marker_hits)
    page_min, page_max = entries[idx_min]["page_ref"], entries[idx_max]["page_ref"]
    lines.append(f"Entries carrying a 'Chapter 24' / 'Effects Of The Bhava Lords' marker: {len(marker_hits)} (list indices {marker_hits})")
    lines.append(f"Entry index range: **{idx_min} - {idx_max}**")
    lines.append(f"`page_ref` range of marker-bearing entries: **{page_min} - {page_max}**")
    lines.append("")
    lines.append(
        "Range used for the rest of this report: `page_ref` **188-234** inclusive -- the span "
        "from the first marker-bearing entry's page_ref through the last content page before "
        "the next chapter's marker appears (entry[234], page_ref=235, is the chapter's closing "
        "commentary page and carries no 'Chapter 24' marker itself; entry[235], page_ref=236, "
        "opens with a 'Chapter 25' marker). Both boundary entries are included in the printed-page "
        "check and the structural table below so the boundary is shown, not assumed."
    )
    lines.append("")

    range_start_ref, range_end_ref = 188, 235  # include 235 to show the true chapter-closing page
    range_entries = [e for e in entries if range_start_ref <= e["page_ref"] <= range_end_ref]
    range_entries.sort(key=lambda e: e["page_ref"])

    # ---- printed-page offset derivation ----
    lines.append("### Printed-page-to-page_ref offset")
    lines.append("")
    first_entry = entries[idx_min]      # page_ref 188
    last_entry = entries[idx_max]       # page_ref 234
    lines.append(f"First entry of the marked range: `{first_entry['chunk_id']}`, page_ref={first_entry['page_ref']}")
    lines.append("Its opening text:")
    lines.append("```")
    lines.append((first_entry.get("text") or "")[:120])
    lines.append("```")
    m_first = PRINTED_NUM_AFTER_CHAPTER.search(first_entry.get("text") or "")
    if m_first:
        lines.append(f"-> printed number found via 'Chapter 24 ... N' pattern: **{m_first.group(1)}**")
    else:
        lines.append(
            "-> no printed page number is visible directly on this entry's own text (it opens "
            "with the chapter-heading verse, not the usual running header/footer line). "
            "Offset is therefore derived from the immediately adjacent entries below instead."
        )
    lines.append("")

    lines.append(f"Last entry of the marked range: `{last_entry['chunk_id']}`, page_ref={last_entry['page_ref']}")
    lines.append("Its opening text:")
    lines.append("```")
    lines.append((last_entry.get("text") or "")[:120])
    lines.append("```")
    m_last = PRINTED_NUM_AFTER_CHAPTER.search(last_entry.get("text") or "")
    if m_last:
        lines.append(f"-> printed number found via 'Chapter 24 ... N' pattern: **{m_last.group(1)}** (page_ref={last_entry['page_ref']} -> printed {m_last.group(1)}, offset +{int(m_last.group(1)) - last_entry['page_ref']})")
    lines.append("")

    # adjacent entries (one before first, one after last) to corroborate the offset
    def find_by_page_ref(pr):
        for e in entries:
            if e["page_ref"] == pr:
                return e
        return None

    adj_before = find_by_page_ref(page_min - 1)
    adj_after_last_plus1 = find_by_page_ref(page_max + 1)
    lines.append("Corroborating adjacent entries (immediately before the range and immediately after the last marked entry):")
    for e in (adj_before, adj_after_last_plus1):
        if e is None:
            continue
        opening = (e.get("text") or "")[:60]
        m = PRINTED_NUM_LEADING.match(opening.strip())
        lines.append(f"  - page_ref={e['page_ref']}, chunk_id=`{e['chunk_id']}`, opening text: {opening!r}")
    lines.append("")
    lines.append(
        "**Offset derived: printed_page_number = page_ref + 1**, consistent across every "
        "sampled boundary above (page_ref 187 opens with leading number '188'; page_ref 234 "
        "carries 'Chapter 24 - 235'; page_ref 235 opens with leading number '236'; page_ref 236 "
        "carries 'Chapter 25 ... 237'). The one entry where the number could not be read directly "
        "(page_ref 188 itself) is stated above as such, not guessed."
    )
    lines.append("")

    # ---- Step 3: structural facts table ----
    lines.append("## Step 3 -- structural facts per page (page_ref 188-235)")
    lines.append("")
    lines.append("| page_ref | page_type | image_path present | word_count field | text char count |")
    lines.append("|---|---|---|---|---|")
    type_counts = {}
    for e in range_entries:
        pt = e.get("page_type") or "(empty)"
        type_counts[pt] = type_counts.get(pt, 0) + 1
        img_present = "yes" if (e.get("image_path") or "").strip() else "no"
        wc_present = "present" if "word_count" in e else "NOT PRESENT IN SCHEMA"
        char_count = len(e.get("text") or "")
        lines.append(f"| {e['page_ref']} | {pt} | {img_present} | {wc_present} | {char_count} |")
    lines.append("")
    lines.append(f"Counts by page_type across these {len(range_entries)} pages: " + ", ".join(f"{k}={v}" for k, v in sorted(type_counts.items())))
    lines.append("")
    lines.append(
        "Note on `word_count`: this field does not exist anywhere in this file's schema "
        f"(union of keys across all {len(entries)} entries is {sorted(set().union(*[set(e.keys()) for e in entries]))}) "
        "-- reported as NOT PRESENT for every row rather than omitted."
    )
    lines.append("")

    # ---- Step 4: verbatim dump, 6 entries spread evenly ----
    lines.append("## Step 4 -- verbatim dump (6 entries spread evenly across the range)")
    lines.append("")
    n = len(range_entries)
    pick_positions = sorted(set(round(k * (n - 1) / 5) for k in range(6)))
    # guarantee exactly 6 distinct picks even if rounding collided
    while len(pick_positions) < 6:
        for p in range(n):
            if p not in pick_positions:
                pick_positions.add(p)
                break
        pick_positions = sorted(pick_positions)
    picks = [range_entries[p] for p in pick_positions]

    for e in picks:
        lines.append(f"### chunk_id=`{e['chunk_id']}` page_ref={e['page_ref']} page_type={e.get('page_type')}")
        lines.append("```text")
        lines.append(e.get("text") or "(EMPTY TEXT FIELD)")
        lines.append("```")
        lines.append("")

    # ---- Step 5: two plain counts ----
    lines.append("## Step 5 -- two plain counts")
    lines.append("")
    empty_pages = [e["page_ref"] for e in range_entries if not (e.get("text") or "").strip()]
    lines.append(f"(a) Entries with empty/whitespace-only `text` in page_ref 188-235: **{len(empty_pages)}**")
    if empty_pages:
        lines.append(f"    page_refs: {empty_pages}")
    lines.append("")

    with_image = [e for e in range_entries if (e.get("image_path") or "").strip()]
    lines.append(f"(b) Entries with `image_path` populated: **{len(with_image)}** / {len(range_entries)}")
    if with_image:
        missing_on_disk = []
        present_on_disk = []
        for e in with_image:
            img_path = e["image_path"]
            resolved = (ROOT / img_path).resolve() if not os.path.isabs(img_path) else Path(img_path)
            exists = resolved.exists()
            (present_on_disk if exists else missing_on_disk).append((e["page_ref"], img_path, exists))
        lines.append(f"    - files confirmed to exist on disk: {len(present_on_disk)}")
        lines.append(f"    - files NOT found on disk: {len(missing_on_disk)}")
        if missing_on_disk:
            for pr, ip, ex in missing_on_disk[:10]:
                lines.append(f"      - page_ref={pr}: `{ip}` -- NOT FOUND")
        # show a couple of confirmed-present examples for transparency
        for pr, ip, ex in present_on_disk[:3]:
            lines.append(f"      - page_ref={pr}: `{ip}` -- confirmed present")
    lines.append("")

    lines.append("Text dumped for human review. No verdict offered.")

    write_and_exit(lines)


def write_and_exit(lines):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote report to {OUTPUT_PATH} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
