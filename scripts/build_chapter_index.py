"""
PERMANENT BUILD SCRIPT. Builds `data/chapter_index_bphs.json`, a retrieval-
unit index partitioning BPHS-1 and BPHS-2 (Brihat Parasara Hora Sastra,
R. Santhanam translation -- one continuous classical work split across two
OCR'd volumes: `data/progress/BPHS - 1 RSanthanam.json` and
`data/progress/BPHS - 2 RSanthanam.json`) into chapter-shaped units.

Does NOT modify either source book JSON. Builds no embeddings, calls no
vision/LLM API. Writes exactly two things: this artifact (only if all
validation checks pass) and `diagnostics/latest_run.md` (always, overwrite
mode, per the project's diagnostic-output convention).

Boundary-detection core (SEQUENTIAL WALK over page_ref order, NOT TOC
parsing, NOT printed-page-number matching) is PORTED from
`scripts/probe_bphs_chapter_walk.py`, a throwaway diagnostic probe whose
walk logic is settled/validated: 96 of 97 real chapters correctly located
(BPHS-1: 45, BPHS-2: 51), zero overlaps, median chapter size 3,336 tokens.
See that script's own module docstring for the full method writeup
(heading-shape criterion + sequential expected-counter criterion +
look-ahead recovery + trailing-chapter-size guard) -- not re-derived here.

This script adds THREE corrections on top of that settled walk, each
discovered by human inspection of the source pages after the probe run
(not re-litigated here, applied as given):

  (a) BPHS-1 has NO real Chapter 46. A running header the OCR read as
      "Chapter 46" around page_ref 470-472 is a digit-misread of "Chapter
      45" (BPHS-1's real chapters are 1-45 only). Any BPHS-1 heading
      candidate claiming a number > 45 is hard-rejected before the walk
      even sees it (a candidate-list filter, not a post-hoc correction),
      so real Chapter 45 naturally absorbs the whole tail through to the
      book's last page (subject to correction (d) below).

  (b) Chapters 38 (BPHS-1) and 91 (BPHS-2) have no recoverable heading
      anywhere in the OCR text (confirmed absent, not just missed by the
      walk's look-ahead recovery). Their pages are never silently folded
      into the PRECEDING chapter's range (which is what
      `build_chapter_page_ranges`'s "extend to next accepted heading's
      start" rule would otherwise do by construction) -- they are carved
      out as their own `unlabelled_gap` units, `chapter_number=null`.
      Boundary rule (mechanical, reuses already-computed candidate data,
      no hardcoded page numbers): the gap starts the page AFTER the LAST
      page where the previous chapter's own number was heading-shape-
      matched (accepted or repeat), and ends the page BEFORE the next
      accepted chapter's start (i.e. exactly the range the preceding
      chapter would otherwise have swallowed). Verified against source
      text: BPHS-1 gap 38 = page 385 only (chapter 37 shows repeat
      headers only at 383/384); BPHS-2 gap 91 = pages 532-535 (chapter 90
      shows repeat headers at 529/531) -- and page 533 inside that range
      does independently contain a garbled "...Chapter 91..." fragment
      the shape-matcher regex cannot see (prefixed with stray OCR noise
      "ne " that breaks the `^chapter` anchor), consistent with the
      carved range being correct.

  (d) BPHS-1 page_ref 482, and ONLY that page, is a genuine errata
      appendix (confirmed by direct read: the page's OCR text opens
      "FRRATA" -- an OCR misread of "ERRATA" -- followed by an
      errata-table layout, structurally different from chapter prose).
      Carved out of Chapter 45 as its own `back_matter` unit. Every other
      page in the ex-"Chapter 46" tail zone stays inside Chapter 45's
      `text`, per correction (a).

Schema, validation checks, and report content are all specified in the
instructing prompt for this build; see `main()` below.
"""

import json
import re
import statistics
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DIAG_PATH = REPO_ROOT / "diagnostics" / "latest_run.md"
OUTPUT_PATH = REPO_ROOT / "data" / "chapter_index_bphs.json"

BOOKS = [
    ("BPHS-1", REPO_ROOT / "data" / "progress" / "BPHS - 1 RSanthanam.json"),
    ("BPHS-2", REPO_ROOT / "data" / "progress" / "BPHS - 2 RSanthanam.json"),
]

# --- ported verbatim from scripts/probe_bphs_chapter_walk.py (settled) -----
_LEADING_JUNK = re.compile(r"^[^A-Za-z0-9]{0,8}")
_HEAD = re.compile(r"^chapter[^A-Za-z0-9]{0,3}([0-9]{1,3})", re.IGNORECASE)
_PROSE_RUN = re.compile(r"[A-Za-z]{4,}")

MAX_SKIP_JUMP = 5
TITLE_LOOKAHEAD_LINES = 4
BOOK_START_EXPECTED = {"BPHS-1": 1, "BPHS-2": 46}
RECOVERY_WINDOW_PAGES = 20
PRIOR_RUN_REFERENCE_MEDIAN_TOKENS = 3336
GUARD_MIN_DIVISOR = 10
GUARD_MIN_TOKENS_FLOOR = 150
GUARD_MAX_MULTIPLIER = 10

# --- this build's corrections (settled facts, not re-derived) --------------
BPHS1_MAX_REAL_CHAPTER = 45          # correction (a)
BPHS1_ERRATA_PAGE = 482              # correction (d)
KNOWN_UNHEADED_GAPS = {"BPHS-1": 38, "BPHS-2": 91}  # correction (b)
CH24_CANARY_START = 188              # regression canary

NEEDS_SPLIT_TOKEN_THRESHOLD = 15000

PREDICTED_TOTAL_UNITS = 100  # stated BEFORE the run; see report Prediction section
PREDICTED_CHAR_DELTA = 0


# ---------------------------------------------------------------------------
# ported walk machinery (unmodified behavior)
# ---------------------------------------------------------------------------

def load_book(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    by_page = {e["page_ref"]: e for e in data}
    page_refs = sorted(by_page.keys())
    contiguous = page_refs == list(range(page_refs[0], page_refs[-1] + 1))
    return data, by_page, page_refs, contiguous


def guess_title(lines, heading_line_idx):
    """Best-effort following-line title text. Ported unmodified from the
    probe script -- this IS this build's `title_raw` extraction. Roughly a
    third of results are body prose accidentally captured instead of a
    genuine title (probe finding #3); cleaning that is explicitly a
    separate future task, not attempted here (`title_clean` stays null)."""
    collected = []
    for j in range(heading_line_idx + 1, min(len(lines), heading_line_idx + 1 + TITLE_LOOKAHEAD_LINES)):
        raw = lines[j].strip()
        if not raw:
            if collected:
                break
            continue
        letters = sum(1 for c in raw if c.isalpha() and ord(c) < 128)
        total_alpha = sum(1 for c in raw if c.isalpha())
        if total_alpha == 0:
            continue
        if letters / total_alpha < 0.6:
            if collected:
                break
            continue
        cleaned = raw.lstrip("_|'‘’ .-")
        if cleaned:
            collected.append(cleaned)
        if len(collected) >= 2:
            break
    return " ".join(collected)[:120] if collected else ""


def find_candidates(book_label, by_page, page_refs):
    candidates = []
    for pr in page_refs:
        entry = by_page[pr]
        text = entry.get("text") or ""
        lines = text.split("\n")
        for idx, line in enumerate(lines):
            stripped_leading = _LEADING_JUNK.sub("", line)
            m = _HEAD.match(stripped_leading)
            if not m:
                continue
            remainder = stripped_leading[m.end():]
            if _PROSE_RUN.search(remainder):
                continue
            num = int(m.group(1))
            candidates.append({
                "book": book_label,
                "page_ref": pr,
                "num": num,
                "line_text": line.strip(),
                "title_guess": guess_title(lines, idx),
            })
    return candidates


def chapter_token_count(r, by_page):
    total_chars = 0
    for p in range(r["start_page_ref"], r["end_page_ref"] + 1):
        e = by_page.get(p)
        if e:
            total_chars += len(e.get("text") or "")
    return total_chars / 4


def walk(candidates, start_expected, by_page=None, guard_thresholds=None):
    """Sequential walk, ported unmodified from the probe script. See that
    script's `walk()` docstring for the full CHANGE 1/2/3 rationale."""
    accepted = []
    skipped = []
    rejects = []
    expected = start_expected
    last_pos = None
    last_accept_start = None

    def guard_blocks(candidate_page_ref):
        if guard_thresholds is None or last_accept_start is None or by_page is None:
            return False
        size = chapter_token_count(
            {"start_page_ref": last_accept_start, "end_page_ref": candidate_page_ref - 1}, by_page
        )
        return size < guard_thresholds["min_tokens"] or size > guard_thresholds["max_tokens"]

    i = 0
    while i < len(candidates):
        c = candidates[i]
        num = c["num"]

        if num == expected:
            if guard_blocks(c["page_ref"]):
                rejects.append({"book": c["book"], "page_ref": c["page_ref"], "claimed_num": num})
                i += 1
                continue
            accepted.append({
                "chapter_number": expected, "title": c["title_guess"], "book": c["book"],
                "start_page_ref": c["page_ref"], "line_text": c["line_text"],
            })
            last_pos = (c["book"], c["page_ref"])
            last_accept_start = c["page_ref"]
            expected += 1
            i += 1
            continue

        if expected < num <= expected + MAX_SKIP_JUMP:
            window_end = c["page_ref"] + RECOVERY_WINDOW_PAGES
            confirmed_target = None
            for target in (num + 1, num + 2):
                for j in range(i + 1, len(candidates)):
                    cj = candidates[j]
                    if cj["page_ref"] > window_end:
                        break
                    if cj["num"] == target:
                        confirmed_target = target
                        break
                if confirmed_target is not None:
                    break
            end_of_volume_fallback = confirmed_target is None and (i + 1 >= len(candidates))

            if confirmed_target is None and not end_of_volume_fallback:
                rejects.append({"book": c["book"], "page_ref": c["page_ref"], "claimed_num": num})
                i += 1
                continue

            if guard_blocks(c["page_ref"]):
                rejects.append({"book": c["book"], "page_ref": c["page_ref"], "claimed_num": num})
                i += 1
                continue

            for skipped_num in range(expected, num):
                skipped.append({"book": c["book"], "chapter_number": skipped_num})
            accepted.append({
                "chapter_number": num, "title": c["title_guess"], "book": c["book"],
                "start_page_ref": c["page_ref"], "line_text": c["line_text"],
            })
            last_pos = (c["book"], c["page_ref"])
            last_accept_start = c["page_ref"]
            expected = num + 1
            i += 1
            continue

        rejects.append({"book": c["book"], "page_ref": c["page_ref"], "claimed_num": num})
        i += 1

    return accepted, skipped, rejects


def build_chapter_page_ranges(accepted, book_page_bounds):
    ranges = []
    for idx, ch in enumerate(accepted):
        book = ch["book"]
        start = ch["start_page_ref"]
        end = book_page_bounds[book][1]
        for nxt in accepted[idx + 1:]:
            if nxt["book"] == book:
                end = nxt["start_page_ref"] - 1
            break
        ranges.append({
            "chapter_number": ch["chapter_number"], "title": ch["title"], "book": book,
            "start_page_ref": start, "end_page_ref": end,
        })
    return ranges


# ---------------------------------------------------------------------------
# this build's own logic
# ---------------------------------------------------------------------------

def run_guarded_walk(label, candidates, by_page, book_page_bounds):
    """Two-pass guarded walk (Pass 1 measures this volume's own median to
    set the trailing-chapter guard's thresholds; Pass 2 is the walk
    actually used), exactly as the probe script's main() does."""
    p1_accepted, _, _ = walk(candidates, BOOK_START_EXPECTED[label], by_page=None, guard_thresholds=None)
    p1_ranges = build_chapter_page_ranges(p1_accepted, book_page_bounds)
    p1_tokens = sorted(chapter_token_count(r, by_page) for r in p1_ranges)
    p1_median = statistics.median(p1_tokens) if p1_tokens else PRIOR_RUN_REFERENCE_MEDIAN_TOKENS
    min_tokens = max(GUARD_MIN_TOKENS_FLOOR, round(p1_median / GUARD_MIN_DIVISOR))
    max_tokens = round(p1_median * GUARD_MAX_MULTIPLIER)
    accepted, skipped, rejects = walk(
        candidates, BOOK_START_EXPECTED[label], by_page=by_page,
        guard_thresholds={"min_tokens": min_tokens, "max_tokens": max_tokens},
    )
    return accepted, skipped, rejects


def carve_unheaded_gap(gap_num, book, candidates, ranges_by_key):
    """Correction (b): carve the unheaded chapter's page range out of the
    PRECEDING chapter's swallowed range. gap_start = 1 page past the last
    heading-shape occurrence of the preceding chapter's own number;
    gap_end = the preceding chapter's original (swallowed) end_page_ref.
    Mutates the preceding chapter's range in place (shrinks its end).
    Returns (gap_start, gap_end) or None if no gap exists (defensive --
    not expected to trigger for the two known cases)."""
    prev_num = gap_num - 1
    prev_range = ranges_by_key[(book, prev_num)]
    occurrences = [c["page_ref"] for c in candidates if c["num"] == prev_num]
    last_prev_occurrence = max(occurrences) if occurrences else prev_range["start_page_ref"]
    gap_start = last_prev_occurrence + 1
    gap_end = prev_range["end_page_ref"]
    if gap_start > gap_end:
        return None
    prev_range["end_page_ref"] = last_prev_occurrence
    return gap_start, gap_end


def concat_text(by_page, start, end):
    """Plain concatenation, NO separator inserted between pages -- this is
    required to satisfy validation check 6 (unit char_count sum must equal
    the exact source char_count sum with zero delta); any inserted
    separator would inflate the total by a fixed per-page-boundary amount."""
    parts = []
    for pr in range(start, end + 1):
        e = by_page.get(pr)
        parts.append((e.get("text") or "") if e else "")
    return "".join(parts)


def make_unit(unit_id, book, kind, chapter_number, title_raw, start, end, by_page):
    text = concat_text(by_page, start, end)
    char_count = len(text)
    token_estimate = char_count // 4
    return {
        "unit_id": unit_id,
        "book": book,
        "kind": kind,
        "chapter_number": chapter_number,
        "title_raw": title_raw,
        "title_clean": None,
        "start_page_ref": start,
        "end_page_ref": end,
        "page_count": end - start + 1,
        "char_count": char_count,
        "token_estimate": token_estimate,
        "text": text,
        "needs_split": token_estimate > NEEDS_SPLIT_TOKEN_THRESHOLD,
    }


def main():
    report = []

    def w(s=""):
        report.append(s)

    def write_report_and_exit(success, extra_note=None):
        with open(DIAG_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(report) + "\n")
        print(f"Wrote {DIAG_PATH} ({len(report)} lines).")
        if not success:
            print("VALIDATION FAILED -- artifact NOT written. See report for detail.")
            if extra_note:
                print(extra_note)
            sys.exit(1)

    w("# BPHS Chapter Index Build")
    w()
    w("Permanent build script: `scripts/build_chapter_index.py`. Output artifact: "
      "`data/chapter_index_bphs.json`. Source books unmodified. No embeddings, "
      "no vision/LLM calls, no git operations.")
    w()

    w("## Prediction (stated independent of / before this run's actual output)")
    w()
    w(f"- **Predicted total units**: {PREDICTED_TOTAL_UNITS} "
      "(front_matter x2 [1/book] + chapter x95 [BPHS-1: chapters 1-45 minus "
      "skipped 38 = 44; BPHS-2: chapters 46-97 minus skipped 91 = 51] + "
      "unlabelled_gap x2 [38, 91] + back_matter x1 [BPHS-1 page 482 only -- "
      "no back_matter correction was specified for BPHS-2, so none is "
      "invented]). Basis: the prior probe run's settled 96-of-97 accepted "
      "figure (45+51), minus the spurious BPHS-1 'Chapter 46' this build's "
      "correction (a) removes (45 -> 44 real BPHS-1 chapters), plus the two "
      "unlabelled_gap units and the two front_matter units correction (b)/"
      "the schema explicitly require, plus the one back_matter unit "
      "correction (d) explicitly requires.")
    w(f"- **Predicted char_count delta (check 6)**: {PREDICTED_CHAR_DELTA}. Every "
      "page is assigned to exactly one unit (partition, no page dropped or "
      "duplicated) and unit text is built by PLAIN concatenation of its "
      "member pages' raw text with no separator inserted -- so the sum of "
      "all units' char_count is definitionally equal to the sum of all "
      "source pages' char_count, provided the partition itself is correct.")
    w()

    # ---------- load + candidate generation ---------------------------------
    all_data = {}
    book_page_bounds = {}
    candidates_by_book = {}
    source_char_by_book = {}
    contiguity_ok = True
    for label, path in BOOKS:
        data, by_page, page_refs, contiguous = load_book(path)
        all_data[label] = (data, by_page, page_refs)
        book_page_bounds[label] = (page_refs[0], page_refs[-1])
        source_char_by_book[label] = sum(len(e.get("text") or "") for e in data)
        if not contiguous:
            contiguity_ok = False
        cands = find_candidates(label, by_page, page_refs)
        if label == "BPHS-1":
            # correction (a): hard-reject any BPHS-1 heading claiming > 45
            # BEFORE the walk ever sees it.
            cands = [c for c in cands if c["num"] <= BPHS1_MAX_REAL_CHAPTER]
        candidates_by_book[label] = cands

    if not contiguity_ok:
        w("## VALIDATION ABORTED PRE-WALK")
        w()
        w("One or both source books' `page_ref` values are not a contiguous "
          "integer range starting at their minimum. This build's page-range "
          "arithmetic assumes contiguity; refusing to proceed. Artifact NOT written.")
        write_report_and_exit(False)
        return

    # ---------- guarded walk per book ---------------------------------------
    accepted = []
    skipped = []
    for label, _ in BOOKS:
        _, by_page, _ = all_data[label]
        b_accepted, b_skipped, _ = run_guarded_walk(label, candidates_by_book[label], by_page, book_page_bounds)
        accepted.extend(b_accepted)
        skipped.extend(b_skipped)

    ranges = build_chapter_page_ranges(accepted, book_page_bounds)
    ranges_by_key = {(r["book"], r["chapter_number"]): r for r in ranges}

    # ---------- correction (b): carve unlabelled_gap units ------------------
    gap_units_raw = {}  # book -> (gap_start, gap_end)
    for book, gap_num in KNOWN_UNHEADED_GAPS.items():
        result = carve_unheaded_gap(gap_num, book, candidates_by_book[book], ranges_by_key)
        gap_units_raw[book] = result  # may be None (defensive)

    # ---------- correction (d): carve BPHS-1 page 482 as back_matter --------
    ch45 = ranges_by_key.get(("BPHS-1", 45))
    back_matter_range = None
    if ch45 is not None and ch45["end_page_ref"] >= BPHS1_ERRATA_PAGE:
        back_matter_range = (BPHS1_ERRATA_PAGE, BPHS1_ERRATA_PAGE)
        ch45["end_page_ref"] = BPHS1_ERRATA_PAGE - 1

    # ---------- front_matter units -------------------------------------------
    front_matter_range = {}
    for label, _ in BOOKS:
        first_page = book_page_bounds[label][0]
        first_chapter_start = min(a["start_page_ref"] for a in accepted if a["book"] == label)
        if first_chapter_start > first_page:
            front_matter_range[label] = (first_page, first_chapter_start - 1)
        else:
            front_matter_range[label] = None

    # ---------- assemble final unit list -------------------------------------
    units = []
    for label, _ in BOOKS:
        _, by_page, _ = all_data[label]
        prefix = "bphs1" if label == "BPHS-1" else "bphs2"

        fm = front_matter_range[label]
        if fm is not None:
            units.append(make_unit(f"{prefix}_frontmatter", label, "front_matter", None, None, fm[0], fm[1], by_page))

        for r in sorted((rr for rr in ranges_by_key.values() if rr["book"] == label), key=lambda x: x["chapter_number"]):
            units.append(make_unit(
                f"{prefix}_ch{r['chapter_number']}", label, "chapter", r["chapter_number"],
                r["title"] if r["title"] else "", r["start_page_ref"], r["end_page_ref"], by_page,
            ))

        gap = gap_units_raw.get(label)
        if gap is not None:
            gap_num = KNOWN_UNHEADED_GAPS[label]
            units.append(make_unit(f"{prefix}_gap{gap_num}", label, "unlabelled_gap", None, None, gap[0], gap[1], by_page))

        if label == "BPHS-1" and back_matter_range is not None:
            units.append(make_unit("bphs1_backmatter", label, "back_matter", None, None,
                                    back_matter_range[0], back_matter_range[1], by_page))

    # ---------- validation checks ---------------------------------------------
    checks = []  # (name, passed, detail)

    # 1 + 3: every page_ref belongs to exactly one unit / zero orphans
    coverage_issues = []
    orphan_total = 0
    for label, _ in BOOKS:
        _, by_page, page_refs = all_data[label]
        book_units = [u for u in units if u["book"] == label]
        count_by_page = {pr: 0 for pr in page_refs}
        for u in book_units:
            for pr in range(u["start_page_ref"], u["end_page_ref"] + 1):
                count_by_page[pr] = count_by_page.get(pr, 0) + 1
        missing = [pr for pr, c in count_by_page.items() if c == 0]
        multi = [pr for pr, c in count_by_page.items() if c > 1]
        orphan_total += len(missing)
        if missing:
            coverage_issues.append(f"{label}: {len(missing)} page(s) with NO unit: {missing[:20]}{'...' if len(missing) > 20 else ''}")
        if multi:
            coverage_issues.append(f"{label}: {len(multi)} page(s) claimed by >1 unit: {multi[:20]}{'...' if len(multi) > 20 else ''}")
    check1_pass = not coverage_issues
    checks.append(("1. Every page_ref belongs to exactly one unit", check1_pass,
                    "all pages covered exactly once" if check1_pass else "; ".join(coverage_issues)))

    # 2: zero overlaps (pairwise, per book)
    overlaps = []
    for label, _ in BOOKS:
        book_units_sorted = sorted((u for u in units if u["book"] == label), key=lambda u: u["start_page_ref"])
        for a_idx in range(len(book_units_sorted) - 1):
            a, b = book_units_sorted[a_idx], book_units_sorted[a_idx + 1]
            if a["end_page_ref"] >= b["start_page_ref"]:
                overlaps.append(f"{label}: {a['unit_id']} (end {a['end_page_ref']}) overlaps {b['unit_id']} (start {b['start_page_ref']})")
    check2_pass = not overlaps
    checks.append(("2. Zero overlaps between units", check2_pass,
                    "0 overlaps" if check2_pass else "; ".join(overlaps)))

    # 3: zero orphans (restated explicitly)
    check3_pass = orphan_total == 0
    checks.append(("3. Zero orphan pages", check3_pass, f"orphan page count = {orphan_total}"))

    # 4: unique unit_ids
    ids = [u["unit_id"] for u in units]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    check4_pass = not dupes
    checks.append(("4. All unit_id values unique", check4_pass,
                    "all unique" if check4_pass else f"duplicate ids: {dupes}"))

    # 5: no BPHS-1 unit has chapter_number > 45
    over45 = [u["unit_id"] for u in units if u["book"] == "BPHS-1" and u["chapter_number"] is not None and u["chapter_number"] > BPHS1_MAX_REAL_CHAPTER]
    check5_pass = not over45
    checks.append((f"5. No BPHS-1 unit has chapter_number > {BPHS1_MAX_REAL_CHAPTER}", check5_pass,
                    "none found" if check5_pass else f"offending units: {over45}"))

    # 6: char_count sum matches source exactly
    total_unit_chars = sum(u["char_count"] for u in units)
    total_source_chars = sum(source_char_by_book.values())
    delta = total_unit_chars - total_source_chars
    check6_pass = delta == 0
    checks.append(("6. Sum of unit char_count == sum of source char_count", check6_pass,
                    f"unit total = {total_unit_chars}, source total = {total_source_chars}, delta = {delta:+d}"))

    # 7: regression canary
    ch24_unit = next((u for u in units if u["unit_id"] == "bphs1_ch24"), None)
    check7_pass = ch24_unit is not None and ch24_unit["start_page_ref"] == CH24_CANARY_START
    checks.append((f"7. bphs1_ch24 start_page_ref == {CH24_CANARY_START}", check7_pass,
                    f"actual start_page_ref = {ch24_unit['start_page_ref'] if ch24_unit else '(unit not found)'}"))

    all_pass = all(c[1] for c in checks)

    # ---------- report: validation table -------------------------------------
    w("## Validation results")
    w()
    w("| # | Check | Result | Measured value |")
    w("|---|---|---|---|")
    for name, passed, detail in checks:
        w(f"| {name.split('.')[0]} | {name.split('.', 1)[1].strip()} | {'PASS' if passed else 'FAIL'} | {detail} |")
    w()

    if not all_pass:
        w("## RESULT: FAILED -- artifact NOT written")
        w()
        w("At least one validation check failed (see table above). Per the "
          "fail-loudly rule, `data/chapter_index_bphs.json` was NOT written. "
          "No partial/best-effort output produced.")
        w()
        write_report_and_exit(False)
        return

    w("## RESULT: ALL 7 CHECKS PASSED -- artifact written")
    w()

    # ---------- unit counts by kind, per book --------------------------------
    w("## Unit counts by kind")
    w()
    w("| Book | chapter | front_matter | back_matter | unlabelled_gap | Total |")
    w("|---|---|---|---|---|---|")
    grand = {"chapter": 0, "front_matter": 0, "back_matter": 0, "unlabelled_gap": 0}
    for label, _ in BOOKS:
        book_units = [u for u in units if u["book"] == label]
        counts = {"chapter": 0, "front_matter": 0, "back_matter": 0, "unlabelled_gap": 0}
        for u in book_units:
            counts[u["kind"]] += 1
        for k in grand:
            grand[k] += counts[k]
        w(f"| {label} | {counts['chapter']} | {counts['front_matter']} | {counts['back_matter']} | {counts['unlabelled_gap']} | {len(book_units)} |")
    w(f"| **Total** | {grand['chapter']} | {grand['front_matter']} | {grand['back_matter']} | {grand['unlabelled_gap']} | **{len(units)}** |")
    w()

    # ---------- BPHS-1 Chapter 45 detail --------------------------------------
    w("## BPHS-1 Chapter 45 (extended range per correction (a))")
    w()
    ch45_unit = next(u for u in units if u["unit_id"] == "bphs1_ch45")
    w(f"- Final page range: {ch45_unit['start_page_ref']}-{ch45_unit['end_page_ref']} "
      f"({ch45_unit['page_count']} pages)")
    w(f"- token_estimate: {ch45_unit['token_estimate']}")
    w()
    _, bphs1_by_page, _ = all_data["BPHS-1"]
    w("Verbatim first 200 chars at page_ref 470, 471, 472 (the misread-header zone):")
    w()
    for pr in (470, 471, 472):
        e = bphs1_by_page.get(pr)
        raw = (e.get("text") or "")[:200] if e else "(page missing)"
        w(f"**page_ref {pr}:**")
        w()
        w("```")
        w(raw)
        w("```")
        w()

    # ---------- needs_split -----------------------------------------------
    w("## Units flagged needs_split (token_estimate > 15,000)")
    w()
    split_units = [u for u in units if u["needs_split"]]
    if not split_units:
        w("None.")
    else:
        w("| unit_id | token_estimate |")
        w("|---|---|")
        for u in sorted(split_units, key=lambda x: -x["token_estimate"]):
            w(f"| {u['unit_id']} | {u['token_estimate']} |")
    w()

    # ---------- unlabelled_gap detail -----------------------------------------
    w("## unlabelled_gap units (chapters 38 and 91)")
    w()
    for u in units:
        if u["kind"] == "unlabelled_gap":
            w(f"**{u['unit_id']}** ({u['book']}): page_ref {u['start_page_ref']}-{u['end_page_ref']} "
              f"({u['page_count']} pages), char_count={u['char_count']}")
            w()
            w("First 200 chars, verbatim:")
            w()
            w("```")
            w(u["text"][:200])
            w("```")
            w()

    # ---------- back_matter detail ---------------------------------------------
    w("## back_matter unit (BPHS-1 page_ref 482)")
    w()
    bm_unit = next((u for u in units if u["kind"] == "back_matter"), None)
    if bm_unit is None:
        w("(none -- unexpected, correction (d) should always produce one)")
    else:
        w(f"**{bm_unit['unit_id']}**: page_ref {bm_unit['start_page_ref']}-{bm_unit['end_page_ref']}, "
          f"char_count={bm_unit['char_count']}")
        w()
        w("First 200 chars, verbatim:")
        w()
        w("```")
        w(bm_unit["text"][:200])
        w("```")
        w()

    # ---------- prediction vs actual -------------------------------------------
    w("## Prediction vs. actual")
    w()
    w(f"- Predicted total units: {PREDICTED_TOTAL_UNITS}. Actual: {len(units)}.")
    if len(units) != PREDICTED_TOTAL_UNITS:
        w(f"  **DEVIATION -- called out explicitly**: actual differs from predicted by "
          f"{len(units) - PREDICTED_TOTAL_UNITS:+d}.")
    else:
        w("  Matches prediction exactly.")
    w(f"- Predicted char_count delta: {PREDICTED_CHAR_DELTA}. Actual: {delta:+d}.")
    if delta != PREDICTED_CHAR_DELTA:
        w("  **DEVIATION -- called out explicitly** (this should be impossible given "
          "check 6 passed, which requires delta==0; flagging the contradiction if seen).")
    else:
        w("  Matches prediction exactly.")
    w()

    # ---------- unit_id convention note -----------------------------------------
    w("## unit_id convention")
    w()
    w("`bphs{1|2}_ch{N}` for chapters; `bphs{1|2}_frontmatter` for front matter; "
      "`bphs1_backmatter` for the single BPHS-1 errata page; `bphs{1|2}_gap{N}` for "
      "unlabelled_gap units. All globally unique by the book prefix.")
    w()
    w("## Output artifact shape")
    w()
    w('`data/chapter_index_bphs.json` = `{"units": [ ... ]}`, a flat list of unit '
      "records under the `units` key, each carrying exactly the schema fields "
      "specified for this build (unit_id, book, kind, chapter_number, title_raw, "
      "title_clean, start_page_ref, end_page_ref, page_count, char_count, "
      "token_estimate, text, needs_split).")
    w()

    write_report_and_exit(True)

    # ---------- write artifact (only reached on full pass) ---------------------
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"units": units}, f, ensure_ascii=False, indent=2)
    print(f"Wrote {OUTPUT_PATH} ({len(units)} units).")


if __name__ == "__main__":
    main()
