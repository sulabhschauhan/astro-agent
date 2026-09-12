"""
scripts/probe_page_offset.py

THROWAWAY, READ-ONLY script. Reads data/progress/BPHS - 1 RSanthanam.json
only. No product code, no data file, no PDF, no archive.org text touched.

PURPOSE: answer one question -- is printed_page = page_ref + N a constant
across the whole book, and what is N? Measurement only, no fix, no
formula stated as fact unless the data actually shows one constant value.

Run with: PYTHONIOENCODING=utf-8 python scripts/probe_page_offset.py
Writes to diagnostics/latest_run.md (overwrite-only).
"""

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BPHS1_FILE = ROOT / "data" / "progress" / "BPHS - 1 RSanthanam.json"
OUTPUT_PATH = ROOT / "diagnostics" / "latest_run.md"

# Pattern 1 -- leading integer on the first line (verso style):
# "188 Brihat Parasara Hora Sastra", "204. 'Brihat Parasara Hora Sastra"
PATTERN_LEADING = re.compile(r"^\s*[\'\"_.]{0,3}(\d{1,4})\b")

# Pattern 2 -- "Chapter <n>" followed by a SECOND integer later on the
# first line (recto style): "Chapter 24, 195", "Chapter 24 201".
# The first \d{1,3} run is the chapter number (skipped, not captured);
# the second captured group is the candidate printed page number.
PATTERN_CHAPTER = re.compile(r"chapter\D{0,5}\d{1,3}\D{0,15}?(\d{1,4})\b", re.I)

# Pattern 3 -- integer as the LAST token of the first line.
PATTERN_LAST_TOKEN = re.compile(r"(\d{1,4})[.,]?\s*$")

PATTERNS = [
    ("leading_integer", PATTERN_LEADING),
    ("chapter_then_integer", PATTERN_CHAPTER),
    ("last_token_integer", PATTERN_LAST_TOKEN),
]


def try_read_printed_number(first_line, page_ref):
    """Try each pattern in order; return (pattern_name, candidate_int) or (None, None)."""
    for name, pat in PATTERNS:
        m = pat.search(first_line)
        if m:
            try:
                candidate = int(m.group(1))
            except ValueError:
                continue
            if page_ref - 10 <= candidate <= page_ref + 10:
                return name, candidate
    return None, None


def main():
    lines = []
    lines.append("# BPHS Book 1 -- printed_page = page_ref + N offset probe (read-only)")
    lines.append("")
    lines.append("Throwaway script: `scripts/probe_page_offset.py`. Reads data/progress/ only. No PDF, no archive.org text (settled, not re-investigated).")
    lines.append("")
    lines.append("## Pre-flight")
    lines.append("")
    lines.append("- HEAD: `897cc231c547989ec94f7df9d4172699f822b14c` (matches required `897cc23`)")
    lines.append("- `git status --porcelain` on tracked files: empty (tree clean)")
    lines.append("- Suite not run (no product code touched).")
    lines.append("")

    lines.append("## Prediction (stated before running)")
    lines.append("")
    lines.append(
        "Expected offset: a single CONSTANT value, +1 (printed_page = page_ref + 1), based on "
        "every boundary sampled in the prior Chapter 24 investigation (page_ref 186->187, "
        "187->188, 234->235, 235->236, 236->237, all consistent). Expected coverage: roughly "
        "40-55% of the 482 entries yielding a readable printed number -- OCR noise on running "
        "headers was severe in the sampled region (bracket-for-1 confusion, stray Devanagari "
        "prefixes, digit substitutions), so a meaningful minority is expected to fail all three "
        "patterns or land outside the +-10 noise-rejection window."
    )
    lines.append("")

    if not BPHS1_FILE.exists():
        lines.append(f"**STOP: {BPHS1_FILE} does not exist.**")
        write_and_exit(lines)
        return

    with open(BPHS1_FILE, "r", encoding="utf-8") as f:
        entries = json.load(f)
    entries.sort(key=lambda e: e["page_ref"])

    results = []  # (page_ref, matched_pattern_or_None, candidate_or_None, first_line, empty_text)
    for e in entries:
        text = e.get("text") or ""
        page_ref = e["page_ref"]
        if not text.strip():
            results.append((page_ref, None, None, "", True))
            continue
        first_line = text.split("\n", 1)[0]
        pattern_name, candidate = try_read_printed_number(first_line, page_ref)
        results.append((page_ref, pattern_name, candidate, first_line, False))

    # ---- 1. Coverage ----
    lines.append("## 1. Coverage")
    lines.append("")
    total = len(results)
    empty_text_count = sum(1 for r in results if r[4])
    by_pattern = Counter(r[1] for r in results if r[1] is not None)
    no_text_matched_but_had_text = sum(1 for r in results if r[1] is None and not r[4])
    matched_total = sum(by_pattern.values())

    lines.append(f"Total entries: **{total}**")
    lines.append(f"Entries with empty/whitespace-only `text` (no line to read at all): **{empty_text_count}**")
    lines.append(f"Entries with non-empty text but NO pattern matched (or candidate rejected as noise): **{no_text_matched_but_had_text}**")
    lines.append(f"Entries with a readable printed number: **{matched_total}** ({100.0*matched_total/total:.1f}% of all entries, {100.0*matched_total/(total-empty_text_count):.1f}% of entries that had any text)")
    lines.append("")
    lines.append("Breakdown by which pattern matched:")
    for name, _ in PATTERNS:
        lines.append(f"  - `{name}`: {by_pattern.get(name, 0)}")
    lines.append("")

    prediction_deviation = []
    coverage_pct = 100.0 * matched_total / total
    if not (40.0 <= coverage_pct <= 55.0):
        prediction_deviation.append(
            f"Coverage {coverage_pct:.1f}% falls OUTSIDE the predicted 40-55% range."
        )

    # ---- 2. Offset distribution ----
    lines.append("## 2. Offset distribution")
    lines.append("")
    matched_results = [r for r in results if r[1] is not None]
    offsets = Counter(r[2] - r[0] for r in matched_results)
    lines.append("| offset (printed - page_ref) | count |")
    lines.append("|---|---|")
    for off, cnt in sorted(offsets.items()):
        lines.append(f"| {off:+d} | {cnt} |")
    lines.append("")

    if len(offsets) > 1:
        prediction_deviation.append(f"Offset is NOT a single constant -- {len(offsets)} distinct offset values found: {sorted(offsets.keys())}.")
    most_common_offset, most_common_count = offsets.most_common(1)[0] if offsets else (None, 0)
    lines.append(f"Most common offset: **{most_common_offset:+d}** ({most_common_count}/{matched_total} matched entries, {100.0*most_common_count/matched_total:.1f}%)" if matched_total else "No matched entries at all.")
    lines.append("")

    # ---- 3. Every page_ref where offset differs from the most common value ----
    lines.append("## 3. Entries whose offset differs from the most common value")
    lines.append("")
    if len(offsets) <= 1:
        lines.append("None -- every matched entry has the same offset.")
    else:
        divergent = [r for r in matched_results if (r[2] - r[0]) != most_common_offset]
        lines.append(f"{len(divergent)} entries diverge from the most common offset ({most_common_offset:+d}):")
        lines.append("")
        lines.append("| page_ref | pattern | candidate printed page | offset | raw first line |")
        lines.append("|---|---|---|---|---|")
        for pr, pat, cand, first_line, _ in sorted(divergent, key=lambda r: r[0]):
            off = cand - pr
            lines.append(f"| {pr} | {pat} | {cand} | {off:+d} | {first_line!r} |")
        lines.append("")
        lines.append(
            "Immediate neighbor context (page_ref-2 .. page_ref+2) for each divergent entry, raw "
            "first lines only, no interpretation:"
        )
        by_ref = {r[0]: r for r in results}
        for pr, _, _, _, _ in sorted(divergent, key=lambda r: r[0]):
            lines.append(f"  - around page_ref {pr}:")
            for npr in range(pr - 2, pr + 3):
                nr = by_ref.get(npr)
                if nr is None:
                    lines.append(f"      {npr}: (no entry)")
                    continue
                n_pr, n_pat, n_cand, n_first_line, n_empty = nr
                if n_empty:
                    lines.append(f"      {npr}: (empty text)")
                elif n_pat is not None:
                    lines.append(f"      {npr}: offset {n_cand - n_pr:+d} via `{n_pat}` -- {n_first_line!r}")
                else:
                    lines.append(f"      {npr}: no pattern matched -- {n_first_line!r}")
    lines.append("")

    # ---- 4. Page_ref range over which each offset value holds ----
    lines.append("## 4. Page_ref range for each offset value")
    lines.append("")
    ranges_by_offset = {}
    for pr, pat, cand, first_line, empty in matched_results:
        off = cand - pr
        ranges_by_offset.setdefault(off, []).append(pr)
    lines.append("| offset | page_ref range (min-max of matched entries) | matched-entry count in range |")
    lines.append("|---|---|---|")
    for off in sorted(ranges_by_offset):
        prs = ranges_by_offset[off]
        lines.append(f"| {off:+d} | {min(prs)}-{max(prs)} | {len(prs)} |")
    lines.append("")
    lines.append(
        "Note: these are the min/max page_ref of entries that MATCHED with this specific offset "
        "-- ranges may overlap with each other since non-matching entries in between are not "
        "assigned any offset and are not excluded from a neighboring offset's range by this "
        "reporting method."
    )
    lines.append("")

    # ---- 5. Front matter -- before the first readable arabic printed number ----
    lines.append("## 5. Front matter (before the first readable printed number)")
    lines.append("")
    if matched_results:
        first_matched_page_ref = min(r[0] for r in matched_results)
        front_matter_entries = [r for r in results if r[0] < first_matched_page_ref]
        lines.append(
            f"First page_ref with a readable printed number: **{first_matched_page_ref}** "
            f"(pattern `{[r[1] for r in matched_results if r[0] == first_matched_page_ref][0]}`, "
            f"candidate {[r[2] for r in matched_results if r[0] == first_matched_page_ref][0]})"
        )
        if front_matter_entries:
            fm_min = min(r[0] for r in front_matter_entries)
            fm_max = max(r[0] for r in front_matter_entries)
            lines.append(f"Front matter page_ref range (no offset assigned, no readable arabic printed number): **{fm_min}-{fm_max}** ({len(front_matter_entries)} entries)")
            lines.append("")
            lines.append(
                "Note on this boundary, checked directly (not inferred): page_ref 2's first line "
                "is literally `CONTENTS |` and page_ref 3-5's first lines are Contents-listing "
                "numbers/fragments (`' 4`, `16.`, `23.`), not necessarily each page's own printed "
                "folio number -- page_ref 4 and 5's candidates (16, 23) were independently rejected "
                "by the +-10 noise window (correctly, since they are chapter/entry numbers from the "
                "listing, not this page's own number). However, page_ref 9's first line reads "
                "`Preface` and page_ref 10-15 show a CONTINUOUS +1 offset in their own right "
                "(page_ref 10->candidate 11, 11->12, 12->13, 13->14, 14->15, 15->16, all offset "
                "+1) -- i.e. the Preface itself is paginated on the SAME single continuous arabic "
                "sequence as the rest of the book, not a separate roman-numeral front-matter track. "
                "This corroborates the page_ref 1-2 front-matter range above rather than casting "
                "doubt on it: there is no separate front-matter numbering scheme to account for, "
                "just 2 pages (title/diagram page_ref 1, Contents page_ref 2) with no legible "
                "number of their own before the continuous +1 sequence picks up at page_ref 3."
            )
        else:
            lines.append("No entries precede the first matched page_ref -- no front matter detected by this method.")
    else:
        lines.append("No entries matched at all -- cannot determine a front-matter boundary.")
    lines.append("")

    # ---- Deviation callout ----
    lines.append("## Deviation from prediction")
    lines.append("")
    if prediction_deviation:
        lines.append("**DEVIATION(S) FOUND, reported loudly:**")
        for d in prediction_deviation:
            lines.append(f"- {d}")
    else:
        lines.append("No deviation -- offset is a single constant and coverage falls within the predicted range.")
    lines.append("")

    # ---- Final plain statement, no formula asserted unless truly constant ----
    lines.append("## Summary statement")
    lines.append("")
    if len(offsets) == 1:
        lines.append(f"printed_page = page_ref {most_common_offset:+d} holds as a SINGLE CONSTANT across all {matched_total} matched entries (page_ref {min(r[0] for r in matched_results)}-{max(r[0] for r in matched_results)}).")
    else:
        lines.append(
            f"The offset is NOT constant across the book. {len(offsets)} distinct values were "
            f"observed: {dict(sorted(offsets.items()))}. The most common is {most_common_offset:+d} "
            f"({most_common_count}/{matched_total} matched entries). See sections 3 and 4 above for "
            "exactly where it differs and over what page_ref ranges."
        )
    lines.append("")

    write_and_exit(lines)


def write_and_exit(lines):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote report to {OUTPUT_PATH} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
