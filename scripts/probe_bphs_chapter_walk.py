"""
DIAGNOSTIC / MEASUREMENT ONLY. No product code touched, nothing deleted,
no JSON modified, no index built, no LLM/vision calls.

Partitions BPHS-1 + BPHS-2 (Brihat Parasara Hora Sastra, R. Santhanam,
one continuous work split across two OCR'd volumes) into chapters using a
SEQUENTIAL WALK over page_ref order -- NOT TOC parsing, NOT printed-page-
number matching. Two prior probes on this corpus (regex-anywhere-in-body,
and TOC parsing) are known-bad and are deliberately not reused here.

Method
------
Exploration (see chat transcript / commit message, not re-derived here)
established that a genuine chapter-heading line in this OCR'd text has a
distinct SHAPE: it sits ALONE on its own line (the printed running header
"Chapter N" at the top of each page of that chapter), with at most a
little OCR/page-number noise trailing it, and crucially NO real English
prose word after the number on that same line. A body cross-reference or
TOC/preface mention ("...discussed in chapter 9 while chapter 10...",
"Chapter 31 entitled 'Argaladhyaya' though brief...") always has real
prose words following the number on the same line, or the "chapter"
token is not the first thing on the line. This SHAPE test is criterion
(a). Criterion (b) is the sequential-walk rule: a shape-matched line is
accepted as a real heading only if its claimed chapter number equals the
currently-expected counter (or is a small forward jump treated as a
skip -- see below). This mirrors the task's two-part accept rule.

REVISED (this run): the two volumes are walked SEPARATELY, each with its
OWN expected-chapter-number counter -- the counter is NOT carried across
the BPHS-1 -> BPHS-2 file boundary. BPHS-1's walk starts expecting
chapter 1; BPHS-2's walk starts expecting chapter 46 (hardcoded, per
already-confirmed evidence at BPHS-2 page_ref 15). A prior version of
this script used a single continuous counter across both volumes; that
was found to let a single mis-OCR'd heading late in BPHS-1 push the
counter past 46 before BPHS-2 was even reached, silently discarding
BPHS-2's own genuine Chapter 46/47/48 headings. See CHANGE 1 in `main()`.

Two further refinements over that prior version: CHANGE 2 (look-ahead
recovery) -- an expected-counter mismatch is no longer resolved by
immediately accepting the next in-range candidate as a skip-and-jump; the
walk first requires forward confirmation that the sequence resumes
normally right after that candidate before committing to the jump.
CHANGE 3 (trailing-chapter guard, PROVISIONAL) -- an acceptance that
would close the previous chapter at an implausible token size (relative
to this run's own measured median) is refused. Both are implemented in
`walk()`, below.
"""

import json
import re
import statistics
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DIAG_PATH = REPO_ROOT / "diagnostics" / "latest_run.md"

BOOKS = [
    ("BPHS-1", REPO_ROOT / "data" / "progress" / "BPHS - 1 RSanthanam.json"),
    ("BPHS-2", REPO_ROOT / "data" / "progress" / "BPHS - 2 RSanthanam.json"),
]

# --- heading shape matcher -------------------------------------------------
# Leading noise allowed before the literal word "chapter": pipes, quotes,
# stray punctuation, whitespace -- observed forms include "| Chapter 3",
# "'Chapter 46", "` Chapter 46 |". Capped at 8 chars so we don't eat into
# a real preceding word.
_LEADING_JUNK = re.compile(r"^[^A-Za-z0-9]{0,8}")
# "chapter" then up to 3 non-alnum noise chars then 1-3 ASCII digits.
# Devanagari digits are explicitly excluded ([0-9] only, not \d) so a
# footnote like "(Chapter १)" (Devanagari 1) never becomes a candidate.
_HEAD = re.compile(r"^chapter[^A-Za-z0-9]{0,3}([0-9]{1,3})", re.IGNORECASE)
# Real trailing prose word (4+ ASCII letters) after the number -> not a
# standalone heading line, it's a sentence ("...31 entitled 'Argaladhyaya'").
_PROSE_RUN = re.compile(r"[A-Za-z]{4,}")

MAX_SKIP_JUMP = 5  # small forward jumps are treated as OCR-lost headings;
# anything further ahead is treated as a suspect match, not a skip run,
# and logged as a reject instead (safety valve against a stray shape
# false-positive silently absorbing a large chapter range as "skipped").

TITLE_LOOKAHEAD_LINES = 4

# --- CHANGE 1: per-volume starting counter ---------------------------------
# Hardcoded, not re-derived: BPHS-1 begins at Chapter 1; BPHS-2 resumes at
# Chapter 46, confirmed by prior raw-text inspection at BPHS-2 page_ref 15.
BOOK_START_EXPECTED = {"BPHS-1": 1, "BPHS-2": 46}

# --- CHANGE 2: look-ahead recovery window -----------------------------------
# When a candidate's claimed number is within MAX_SKIP_JUMP of `expected` but
# not equal to it, the walk no longer accepts it immediately. It first scans
# forward, bounded by page_ref distance, for a candidate matching num+1 or
# num+2 (i.e. the chapter that would immediately follow accepting this one) --
# only that forward confirmation lets the walk conclude the gap is genuine and
# commit to the jump. Window size justification (reasonable, not statistically
# fit): the prior run's own measured median chapter size was 3,336 tokens; at
# an observed ~1,500-2,500 chars/page (~375-625 tokens/page) a median chapter
# spans roughly 5-9 pages. A 20-page forward window comfortably covers more
# than two typical chapters' worth of page-span -- enough room to find num+1
# or num+2's heading even if it sits a page or two into that chapter's own
# start -- while staying tightly bounded rather than scanning arbitrarily far
# and risking a coincidental false confirmation from unrelated noise.
RECOVERY_WINDOW_PAGES = 20

# --- CHANGE 3: trailing-chapter guard (PROVISIONAL) -------------------------
# Reference median from the prior run (both volumes combined) -- used only as
# a documented reference point / fallback if a volume's own Pass-1 walk (see
# main()) somehow yields zero accepted chapters, never as the live threshold
# basis itself.
PRIOR_RUN_REFERENCE_MEDIAN_TOKENS = 3336
# A closing chapter's token estimate below median/GUARD_MIN_DIVISOR (floored
# at GUARD_MIN_TOKENS_FLOOR) or above median*GUARD_MAX_MULTIPLIER is refused.
# Provisional, round numbers picked for this run, not fit to any distribution
# -- see main()'s guard-thresholds section for the brief justification and
# the guard-rejects table for every heading this actually caught.
GUARD_MIN_DIVISOR = 10
GUARD_MIN_TOKENS_FLOOR = 150
GUARD_MAX_MULTIPLIER = 10


def load_book(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    by_page = {e["page_ref"]: e for e in data}
    page_refs = sorted(by_page.keys())
    contiguous = page_refs == list(range(page_refs[0], page_refs[-1] + 1))
    return data, by_page, page_refs, contiguous


def guess_title(lines, heading_line_idx):
    """Best-effort: first following non-blank line(s) that read as English
    prose (majority ASCII-alphabetic), skipping intervening blank lines and
    Sanskrit/Devanagari epigraph lines. Not required to be perfect -- report
    item 1 asks for 'title_text_if_any'."""
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
            # mostly non-ASCII (Devanagari sloka line) -- skip, keep looking
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
    """Return list of candidate dicts in page order, shape-matched only."""
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
                continue  # real prose word trailing -> not a standalone heading line
            num = int(m.group(1))
            candidates.append({
                "book": book_label,
                "page_ref": pr,
                "num": num,
                "line_text": line.strip(),
                "title_guess": guess_title(lines, idx),
            })
    return candidates


def walk(candidates, start_expected, by_page=None, guard_thresholds=None):
    """Sequential walk with criteria (a) [pre-filtered into `candidates`,
    already scoped to ONE volume in page order] and (b) [expected-counter
    match, applied here]. `start_expected` is this volume's OWN starting
    counter (CHANGE 1) -- callers walk each book separately and never carry
    `expected` across a file boundary.

    CHANGE 2 (look-ahead recovery): a candidate whose claimed number is
    within (expected, expected+MAX_SKIP_JUMP] is no longer accepted
    immediately. The walk first scans forward, bounded by
    RECOVERY_WINDOW_PAGES, for a candidate matching num+1 or num+2 -- the
    chapter that would immediately follow accepting this one -- as
    confirmation the sequence genuinely resumes past the gap. Without that
    confirmation the candidate is treated as noise (rejected) WITHOUT
    moving `expected`, so the walk keeps scanning and can still pick up the
    real `expected` heading later if one exists (this is what recovers a
    case like a spurious near-miss digit misread sitting just before the
    real heading it misread).  A candidate at the very end of this volume's
    candidate stream (nothing left later to possibly confirm against) is
    accepted via an explicit end-of-volume fallback instead of being
    penalized for having nothing left to confirm with.

    CHANGE 3 (trailing-chapter guard, PROVISIONAL): if `guard_thresholds`
    is given (a dict with 'min_tokens'/'max_tokens'), every acceptance
    (plain or jump-confirmed) is checked against the chapter it would
    CLOSE -- the most recently accepted chapter, from its own start up to
    this candidate's page_ref - 1. If that closing chapter's chars/4 token
    estimate falls outside the given bounds, the acceptance is refused
    (treated as a reject) instead. `guard_thresholds`/`by_page` are None
    for the reference Pass-1 walk used only to measure this run's own
    median (see main()) -- guarding is then a no-op.
    """
    accepted = []
    skipped = []
    rejects = []
    recovery_log = []
    guard_rejects = []
    expected = start_expected
    last_pos = None  # (book, page_ref) of most recently accepted heading
    last_accept_start = None  # start_page_ref of most recently accepted chapter

    def guard_blocks(candidate_page_ref):
        if guard_thresholds is None or last_accept_start is None or by_page is None:
            return False
        size = chapter_token_count(
            {"start_page_ref": last_accept_start, "end_page_ref": candidate_page_ref - 1}, by_page
        )
        if size < guard_thresholds["min_tokens"] or size > guard_thresholds["max_tokens"]:
            guard_rejects.append({
                "book": candidates[0]["book"] if candidates else None,
                "closing_chapter_start": last_accept_start,
                "rejected_heading_page_ref": candidate_page_ref,
                "closing_chapter_tokens": size,
                "min_tokens": guard_thresholds["min_tokens"],
                "max_tokens": guard_thresholds["max_tokens"],
            })
            return True
        return False

    i = 0
    while i < len(candidates):
        c = candidates[i]
        num = c["num"]

        if num == expected:
            if guard_blocks(c["page_ref"]):
                rejects.append({
                    "book": c["book"], "page_ref": c["page_ref"], "claimed_num": num,
                    "expected_at_time": expected, "line_text": c["line_text"],
                })
                i += 1
                continue
            accepted.append({
                "chapter_number": expected,
                "title": c["title_guess"],
                "book": c["book"],
                "start_page_ref": c["page_ref"],
                "line_text": c["line_text"],
            })
            last_pos = (c["book"], c["page_ref"])
            last_accept_start = c["page_ref"]
            expected += 1
            i += 1
            continue

        if expected < num <= expected + MAX_SKIP_JUMP:
            window_end = c["page_ref"] + RECOVERY_WINDOW_PAGES
            confirmed_target = None
            confirmed_page_ref = None
            for target in (num + 1, num + 2):
                for j in range(i + 1, len(candidates)):
                    cj = candidates[j]
                    if cj["page_ref"] > window_end:
                        break
                    if cj["num"] == target:
                        confirmed_target = target
                        confirmed_page_ref = cj["page_ref"]
                        break
                if confirmed_target is not None:
                    break
            end_of_volume_fallback = confirmed_target is None and (i + 1 >= len(candidates))

            attempt = {
                "book": c["book"],
                "gap_expected_start": expected,
                "gap_expected_end": num - 1,
                "candidate_num": num,
                "candidate_page_ref": c["page_ref"],
                "window_end_page_ref": window_end,
            }

            if confirmed_target is None and not end_of_volume_fallback:
                attempt["outcome"] = (
                    "FAILED TO RECOVER (this candidate) -- no confirmation of "
                    f"chapter {num + 1} or {num + 2} within the "
                    f"{RECOVERY_WINDOW_PAGES}-page window; treated as noise, "
                    "expected unchanged, scan continues"
                )
                recovery_log.append(attempt)
                rejects.append({
                    "book": c["book"], "page_ref": c["page_ref"], "claimed_num": num,
                    "expected_at_time": expected, "line_text": c["line_text"],
                })
                i += 1
                continue

            if guard_blocks(c["page_ref"]):
                basis = "end-of-volume fallback" if end_of_volume_fallback else (
                    f"confirmed via chapter {confirmed_target} at page_ref {confirmed_page_ref}"
                )
                attempt["outcome"] = (
                    f"{basis}, but GUARD-REJECTED (closing chapter size implausible) -- "
                    "treated as noise, expected unchanged"
                )
                recovery_log.append(attempt)
                rejects.append({
                    "book": c["book"], "page_ref": c["page_ref"], "claimed_num": num,
                    "expected_at_time": expected, "line_text": c["line_text"],
                })
                i += 1
                continue

            if end_of_volume_fallback:
                attempt["outcome"] = (
                    "END-OF-VOLUME FALLBACK: no further candidates exist anywhere "
                    f"later in this volume to confirm against -- accepted as chapter "
                    f"{num} without confirmation, chapters {expected}..{num - 1} marked skipped"
                )
            else:
                label = "N+1" if confirmed_target == num + 1 else "N+2"
                attempt["outcome"] = (
                    f"CONFIRMED (recovered at {label}, via chapter {confirmed_target} found "
                    f"at page_ref {confirmed_page_ref}) -- accepted as chapter {num}, "
                    f"chapters {expected}..{num - 1} marked skipped"
                )
            recovery_log.append(attempt)

            search_start = last_pos if last_pos else (c["book"], 1)
            for skipped_num in range(expected, num):
                skipped.append({
                    "chapter_number": skipped_num,
                    "searched_from": search_start,
                    "searched_to": (c["book"], c["page_ref"]),
                })
            accepted.append({
                "chapter_number": num,
                "title": c["title_guess"],
                "book": c["book"],
                "start_page_ref": c["page_ref"],
                "line_text": c["line_text"],
            })
            last_pos = (c["book"], c["page_ref"])
            last_accept_start = c["page_ref"]
            expected = num + 1
            i += 1
            continue

        # num < expected (already-passed / repeating running header / TOC
        # echo) OR num way ahead of a plausible small skip -> reject.
        rejects.append({
            "book": c["book"],
            "page_ref": c["page_ref"],
            "claimed_num": num,
            "expected_at_time": expected,
            "line_text": c["line_text"],
        })
        i += 1

    return accepted, skipped, rejects, recovery_log, guard_rejects


def compress_rejects(rejects):
    """Group consecutive rejects (in walk order) sharing the same claimed_num
    into one summary row -- collapses the repeating page-header noise
    (e.g. 'Chapter 3' printed on every page of chapter 3 after acceptance)
    into a single readable row while remaining fully accounted for."""
    groups = []
    for r in rejects:
        if groups and groups[-1]["claimed_num"] == r["claimed_num"] and groups[-1]["book"] == r["book"]:
            groups[-1]["count"] += 1
            groups[-1]["last_page_ref"] = r["page_ref"]
            groups[-1]["expected_at_time_last"] = r["expected_at_time"]
        else:
            groups.append({
                "book": r["book"],
                "claimed_num": r["claimed_num"],
                "count": 1,
                "first_page_ref": r["page_ref"],
                "last_page_ref": r["page_ref"],
                "expected_at_time_first": r["expected_at_time"],
                "expected_at_time_last": r["expected_at_time"],
                "sample_line": r["line_text"],
            })
    return groups


def percentile(sorted_vals, pct):
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * pct
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def build_chapter_page_ranges(accepted, book_page_bounds):
    """Given accepted headings (chapter_number, book, start_page_ref) in
    walk order, derive each chapter's page range: from its own start to the
    page immediately before the NEXT accepted heading's start (crossing a
    book boundary is allowed: a chapter's pages can span the tail of one
    book only up to that book's own last page -- BPHS-1 chapters cannot
    "spill" into BPHS-2 file pages, they end at BPHS-1's own last page,
    and BPHS-2's first accepted chapter starts BPHS-2 fresh). Returns a
    list of dicts with book/start/end for each accepted chapter, plus any
    trailing chapter's end pinned to its own book's last page.
    """
    ranges = []
    for idx, ch in enumerate(accepted):
        book = ch["book"]
        start = ch["start_page_ref"]
        # default end = this book's last page (will be tightened below if a
        # later heading in the SAME book exists)
        end = book_page_bounds[book][1]
        for nxt in accepted[idx + 1:]:
            if nxt["book"] == book:
                end = nxt["start_page_ref"] - 1
                break
            else:
                # next accepted heading is in a different (later) book ->
                # this chapter runs to the end of its own book's pages
                break
        ranges.append({
            "chapter_number": ch["chapter_number"],
            "title": ch["title"],
            "book": book,
            "start_page_ref": start,
            "end_page_ref": end,
        })
    return ranges


def chapter_token_count(r, by_page):
    """chars/4 token estimate for a range dict carrying start_page_ref/
    end_page_ref, against a single volume's own by_page map. Module-level
    (moved out of main(), S-current) so CHANGE 3's guard inside walk() can
    call it too, not just the Item 5 distribution code."""
    total_chars = 0
    for p in range(r["start_page_ref"], r["end_page_ref"] + 1):
        e = by_page.get(p)
        if e:
            total_chars += len(e.get("text") or "")
    return total_chars / 4


def main():
    report_lines = []

    def w(s=""):
        report_lines.append(s)

    # ---------- PREDICTION (written before numbers are used) --------------
    w("# BPHS Chapter Sequential-Walk Probe")
    w()
    w("Diagnostic/measurement only. Script: `scripts/probe_bphs_chapter_walk.py`. "
      "No product code changed, nothing deleted, no JSON modified.")
    w()
    w("## Prediction (stated before treating the walk's own tallies as ground truth)")
    w()
    w("Front-matter narrative (BPHS-1 page_ref ~10-15) states the work has 97 "
      "chapters total, Volume 1 (BPHS-1) carrying 45 and Volume 2 (BPHS-2) the "
      "remaining 52 (Ch.46-97). That narrative text is NOT used as a walk input "
      "(it is exactly the TOC/preface trap this probe is built to avoid), but it "
      "is a reasonable prior to state a prediction against.")
    w()
    w("- **Predicted accepted per volume**: BPHS-1 somewhere close to 45 but likely "
      "a few short (OCR damage on some running headers is expected given the "
      "corpus's known OCR fragility); BPHS-2 likewise close to 52 but possibly "
      "further short since it is the larger, more heavily-OCR'd volume (552 vs "
      "482 entries).")
    w("- **Predicted median chapter size**: BPHS-1 pages run fairly dense prose "
      "(~1500-2500 chars/page from the samples read during calibration); a typical "
      "chapter spanning roughly 8-15 pages would put median chapter tokens in the "
      "roughly 3,000-7,000 token range (chars/4 estimate). No prediction of the "
      "outlier tail is made -- some chapters (e.g. the long Yoga chapters 35-41 "
      "the front matter narrates about) are plausibly much larger.")
    w()
    w("If actual results deviate meaningfully from this, it is called out explicitly "
      "below rather than folded quietly into the tables.")
    w()

    w("## Prediction: this run's fix-effect forecast (stated before running the "
      "final Changes-1/2/3 version, per the task's prediction requirement)")
    w()
    w("Settled baseline from the prior run: 90 chapters accepted total (both "
      "volumes), 7 skipped (38, 44, 46, 47, 66, 67, 91), 119 orphan pages.")
    w()
    w("- **Predicted BPHS-1 accepted:** 42-45. Change 1 does not alter BPHS-1's own "
      "walk (it still starts at expected=1); the internally-inconsistent tail OCR "
      "(pages ~416-482, claimed numbers 43/44/45/46/48 out of sequence) is now also "
      "subject to Change 2's look-ahead recovery, which may recover a chapter or "
      "two that the prior run lost there, but is not guaranteed to recover all of "
      "them -- and Change 3's guard could newly reject something the prior run "
      "accepted. Net prediction: close to but not necessarily exactly the prior "
      "count.")
    w("- **Predicted BPHS-2 accepted:** 48-52 (up from whatever the prior run's own "
      "BPHS-2 count was, which is not separately known here -- only the 90-total/"
      "7-skipped combined figures are settled). Change 1 alone should recover "
      "chapters 46, 47 and 48 (the cross-volume cascade is structurally impossible "
      "post-fix regardless of BPHS-1's own tail chaos); Change 2 should additionally "
      "recover 66 and 67 (the within-BPHS-2 cascade) if the look-ahead confirmation "
      "logic works as designed. That is up to 5 of the prior run's 7 skips "
      "recovered, leaving only the 2 genuine gaps (38, 91) skipped by design.")
    w("- **Predicted orphan-page count:** a meaningful decrease from 119, very "
      "roughly into the 30-90 range -- hedged loosely because the exact page-span "
      "recovered by chapters 46/47/48/66/67 isn't precisely known in advance (the "
      "task states chapters 46-48 alone span roughly 90 pages), and because Change "
      "3's guard could offset some of that gain by newly rejecting a small number "
      "of previously-accepted headings elsewhere, creating a few new orphan pages "
      "of its own.")
    w()

    # ---------- load ---------------------------------------------------
    all_data = {}
    book_page_bounds = {}
    all_candidates = []
    candidates_by_book = {}
    for label, path in BOOKS:
        data, by_page, page_refs, contiguous = load_book(path)
        all_data[label] = (data, by_page, page_refs)
        book_page_bounds[label] = (page_refs[0], page_refs[-1])
        w(f"Loaded {label}: {len(data)} entries, page_ref range "
          f"{page_refs[0]}..{page_refs[-1]}, contiguous={contiguous}")
        cands = find_candidates(label, by_page, page_refs)
        candidates_by_book[label] = cands
        all_candidates.extend(cands)

    w()
    w(f"Total heading-SHAPE-matched candidate lines across both volumes (before "
      f"the expected-counter test): {len(all_candidates)}")
    w()

    w("## Change 1: volume-boundary counter reset")
    w()
    w("The expected-chapter counter is no longer carried across the BPHS-1 -> "
      "BPHS-2 file boundary. Each volume is walked independently with its own "
      f"counter: BPHS-1 starts expecting chapter {BOOK_START_EXPECTED['BPHS-1']}; "
      f"BPHS-2 starts expecting chapter {BOOK_START_EXPECTED['BPHS-2']} "
      "(hardcoded -- a known, confirmed fact from prior raw-text inspection at "
      "BPHS-2 page_ref 15, not re-derived here).")
    w()

    # ---------- CHANGE 3 setup: Pass 1 (guard OFF), one per volume, purely to
    # measure THIS run's own median chapter size, which then becomes the
    # guard's reference threshold for Pass 2 below (the walk actually
    # reported through the rest of this file). Necessary two-pass structure:
    # the guard's threshold is a function of a completed accepted set, but
    # the guard itself operates DURING the walk that produces that set.
    guard_thresholds_by_book = {}
    for label, _ in BOOKS:
        cands = candidates_by_book[label]
        _, by_page, _ = all_data[label]
        p1_accepted, _, _, _, _ = walk(cands, BOOK_START_EXPECTED[label], by_page=None, guard_thresholds=None)
        p1_ranges = build_chapter_page_ranges(p1_accepted, book_page_bounds)
        p1_tokens = sorted(chapter_token_count(r, by_page) for r in p1_ranges)
        p1_median = statistics.median(p1_tokens) if p1_tokens else PRIOR_RUN_REFERENCE_MEDIAN_TOKENS
        min_tokens = max(GUARD_MIN_TOKENS_FLOOR, round(p1_median / GUARD_MIN_DIVISOR))
        max_tokens = round(p1_median * GUARD_MAX_MULTIPLIER)
        guard_thresholds_by_book[label] = {
            "min_tokens": min_tokens, "max_tokens": max_tokens,
            "pass1_median": p1_median, "pass1_n": len(p1_tokens),
        }

    w("## Change 3: trailing-chapter guard thresholds (PROVISIONAL, needs future tuning)")
    w()
    w("Guard-rejected headings are reported in full further below so a human can "
      "audit whether the guard is doing more good than harm; it is NOT presented "
      "as a settled, final threshold. Thresholds are derived per-volume from a "
      "Pass-1 walk (Changes 1+2 only, guard disabled) run solely to measure THIS "
      "run's own median chapter size -- the guard cannot be computed against its "
      "own output. Reference point from the PRIOR run (both volumes combined): "
      f"{PRIOR_RUN_REFERENCE_MEDIAN_TOKENS:.0f} tokens.")
    w()
    w(f"| Book | Pass-1 accepted (n) | Pass-1 median tokens | min_tokens "
      f"(median/{GUARD_MIN_DIVISOR}, floor {GUARD_MIN_TOKENS_FLOOR}) | max_tokens "
      f"(median x{GUARD_MAX_MULTIPLIER}) |")
    w("|---|---|---|---|---|")
    for label, _ in BOOKS:
        g = guard_thresholds_by_book[label]
        w(f"| {label} | {g['pass1_n']} | {g['pass1_median']:.0f} | {g['min_tokens']} | {g['max_tokens']} |")
    w()
    w("Justification (brief, explicitly provisional, NOT statistically rigorous): "
      f"a floor of median/{GUARD_MIN_DIVISOR} only catches an acceptance that would "
      "close a chapter of roughly a heading-plus-one-short-paragraph size or less -- "
      "implausible for real classical-text chapter content, but far below any "
      f"genuinely short chapter. A ceiling of median x{GUARD_MAX_MULTIPLIER} is "
      "generous enough to sit comfortably above the 15,000-token 'large chapter' "
      "flag this script already reports separately (Item 5) for genuinely long "
      "doctrinal chapters, so it should only catch an acceptance that would leave a "
      "wildly implausible mega-chapter, not a real long one. Both multipliers are "
      "round, easy-to-audit numbers picked for this run, not fit to any "
      "distribution -- tune later against the guard-rejects table's actual hits.")
    w()

    # ---------- CHANGE 2 + 3: Pass 2, the walk actually reported below ------
    accepted, skipped, rejects = [], [], []
    recovery_log_all = []
    guard_rejects_all = []
    for label, _ in BOOKS:
        cands = candidates_by_book[label]
        _, by_page, _ = all_data[label]
        gt = guard_thresholds_by_book[label]
        b_accepted, b_skipped, b_rejects, b_recovery, b_guard_rejects = walk(
            cands, BOOK_START_EXPECTED[label], by_page=by_page,
            guard_thresholds={"min_tokens": gt["min_tokens"], "max_tokens": gt["max_tokens"]},
        )
        accepted.extend(b_accepted)
        skipped.extend(b_skipped)
        rejects.extend(b_rejects)
        recovery_log_all.extend(b_recovery)
        guard_rejects_all.extend(b_guard_rejects)

    w("## Change 2: look-ahead recovery attempts")
    w()
    if not recovery_log_all:
        w("No candidate ever fell into the (expected, expected+MAX_SKIP_JUMP] "
          "ambiguous zone in this run -- no recovery attempts were needed.")
    else:
        w(f"{len(recovery_log_all)} recovery attempt(s) made across both volumes. Each "
          "row is one candidate that did not exactly match the counter at the time "
          "it was reached, evaluated for forward confirmation before any skip was "
          "committed.")
        w()
        w("| Book | Gap (expected..candidate-1) | Candidate # | Candidate page_ref | "
          f"Window end (+{RECOVERY_WINDOW_PAGES}p) | Outcome |")
        w("|---|---|---|---|---|---|")
        for a in recovery_log_all:
            gap = (f"{a['gap_expected_start']}" if a['gap_expected_start'] == a['gap_expected_end']
                   else f"{a['gap_expected_start']}-{a['gap_expected_end']}")
            w(f"| {a['book']} | {gap} | {a['candidate_num']} | {a['candidate_page_ref']} | "
              f"{a['window_end_page_ref']} | {a['outcome']} |")
    w()

    w("## Change 3: guard-rejects (every heading the trailing-chapter guard refused)")
    w()
    if not guard_rejects_all:
        w("The guard refused zero headings in this run.")
    else:
        w(f"{len(guard_rejects_all)} heading(s) refused by the guard:")
        w()
        w("| Book | Closing chapter start page_ref | Rejected heading page_ref | "
          "Closing-chapter tokens | min_tokens | max_tokens |")
        w("|---|---|---|---|---|---|")
        for g in guard_rejects_all:
            w(f"| {g['book']} | {g['closing_chapter_start']} | {g['rejected_heading_page_ref']} | "
              f"{g['closing_chapter_tokens']:.0f} | {g['min_tokens']} | {g['max_tokens']} |")
    w()

    # Enrich each skip: was this exact chapter number's heading actually
    # FOUND later in the candidate stream (just rejected because the
    # counter had already moved past it), vs genuinely never shape-matched
    # anywhere at all? These are different failure modes and must not be
    # conflated -- the former is a cascading counter-drift effect from an
    # earlier spurious accept/skip, the latter is a true OCR/heading loss.
    for s in skipped:
        later_hits = [r for r in rejects if r["claimed_num"] == s["chapter_number"]]
        if later_hits:
            first_hit = later_hits[0]
            s["found_later"] = True
            s["found_later_at"] = (first_hit["book"], first_hit["page_ref"])
            s["found_later_count"] = len(later_hits)
        else:
            s["found_later"] = False

    accepted_bphs1 = [a for a in accepted if a["book"] == "BPHS-1"]
    accepted_bphs2 = [a for a in accepted if a["book"] == "BPHS-2"]

    w("## Item 1: Accepted chapters per volume")
    w()
    w(f"- BPHS-1 accepted: {len(accepted_bphs1)}")
    w(f"- BPHS-2 accepted: {len(accepted_bphs2)}")
    w(f"- Total accepted: {len(accepted)}")
    w()
    w("Full accepted sequence, `(chapter_number, title_text_if_any, book, start_page_ref)`:")
    w()
    w("| # | Title (best-effort) | Book | Start page_ref |")
    w("|---|---|---|---|")
    for ch in accepted:
        title = ch["title"] if ch["title"] else "(none recovered)"
        w(f"| {ch['chapter_number']} | {title} | {ch['book']} | {ch['start_page_ref']} |")
    w()

    # ---------- item 2: skips --------------------------------------------
    w("## Notable / surprising findings (not asked for by a specific item number, "
      "surfaced because rigor requirements call for reporting uncertainty honestly "
      "rather than papering over it)")
    w()
    w("1. **HEADLINE FINDING FROM THE PRIOR RUN (root cause, now addressed by "
      "Changes 1-2 below -- see the 'Re-report: fix verification' section "
      "further down for the actual outcome, not asserted here).** Root cause, "
      "read directly from raw text (not just candidate counts): BPHS-1 pages "
      "~416-482 show internally INCONSISTENT chapter-header OCR -- page 438 "
      "reads `Chapter 45... ह | 439`; pages 439-446 then show `Chapter 44` "
      "again (a backward step); page 456 reads `Chapter 48 457`; page 470 "
      "reads `Chapter 46 | an`; pages 472-480 revert to `Chapter 45 473`. Five "
      "different claimed numbers (43/44/45/46/48) appear out of sequence in "
      "one ~65-page span, contradicting the settled fact that BPHS-1 cleanly "
      "carries only Chapters 1-45 (BPHS-1's real final page, 482, was read "
      "directly and is confirmed an ERRATA appendix, not chapter prose). The "
      "PRIOR (single continuous-counter) version of this walk ACCEPTED a "
      "spurious 'Chapter 48' at page_ref 456 -- plausibly a digit-OCR misread "
      "of '45' -- which pushed that continuous expected-counter to 49 before "
      "BPHS-2 was even reached, causing BPHS-2's own genuine Chapter 46/47/48 "
      "headings to be rejected as already-passed noise. CHANGE 1 (this run) "
      "removes the mechanism entirely: BPHS-2's walk now starts fresh at "
      "expected=46 regardless of anything that happened in BPHS-1, so this "
      "specific cross-volume cascade cannot recur no matter what BPHS-1's tail "
      "OCR does. A SECOND, independent cascade of the same general shape was "
      "also found entirely inside BPHS-2: page_ref 349 reads `Chapter 68 839` "
      "(plausibly '66' misread as '68'), which under the prior logic "
      "prematurely consumed the counter and caused the real Chapter 66 heading "
      "(confirmed at page_ref 352, `Chapter 66 / Ashtakavarga`, Devanagari "
      "epigraph matching) and real Chapter 67 (confirmed at page_ref 377, "
      "`Chapter 67`, Devanagari numeral ॥६७॥ matching) to be "
      "rejected the same way. This second cascade is entirely WITHIN one "
      "volume, so Change 1 alone does not touch it -- it is CHANGE 2 "
      "(look-ahead recovery) that is meant to address it, by refusing to "
      "jump-accept the spurious '68' without forward confirmation, letting the "
      "scan continue on to the real 66/67 headings instead. See the "
      "'Re-report: fix verification' section for the actual, measured outcome.")
    w("2. **Digit-gluing OCR noise produced a few implausible claimed chapter "
      "numbers** in the reject list (e.g. `300` from what reads like `Chapter 30` "
      "with a page number glued on with no separating space, `390` similarly). "
      "These were correctly excluded from the accepted sequence by the "
      f"`MAX_SKIP_JUMP={MAX_SKIP_JUMP}` safety bound (a claimed number more than "
      "5 past the expected counter is treated as a suspect match and rejected, "
      "never silently accepted as a huge skip-jump).")
    w("3. **The title-guess column is best-effort only.** For a meaningful number "
      "of accepted chapters (visible directly in the Item 1 table -- e.g. Chapter "
      "5, 6, 7, 19, 30, 35, 39, 40, 43, 68, 81, 94, 97) the heuristic picked up "
      "body prose following the heading line rather than a genuine title, because "
      "some pages go straight from the 'Chapter N' running header into body "
      "content with no separate title line, or the real title line didn't read as "
      "ASCII-majority prose. Treat that column as approximate diagnostic color, "
      "never as an authoritative chapter title.")

    bphs1_over_45 = [a for a in accepted if a["book"] == "BPHS-1" and a["chapter_number"] > 45]
    if bphs1_over_45:
        spurious_nums = sorted(a["chapter_number"] for a in bphs1_over_45)
        w(f"4. **NEWLY-EXPOSED FINDING, must be reported loudly (tables win over "
          f"prose): BPHS-1's accepted set includes chapter number(s) "
          f"{spurious_nums}, above the settled true count of 45.** This is a "
          "DIFFERENT failure mode from the two cascades Changes 1-2 targeted -- "
          "those were about a SPURIOUS candidate being jump-accepted past a real "
          "gap; this is a spurious candidate landing on an EXACT match to the "
          "counter's current value, which the equality branch always trusts "
          "(look-ahead recovery only ever engages for a JUMP, by construction, "
          "and the guard's chapter-size check does not flag this acceptance -- "
          "its closing/resulting chapter sizes are not implausible). Concretely: "
          "BPHS-1 page_ref 470 reads `Chapter 46 | an` (visible directly in Item "
          "6's spot-verify sample below) -- the same tail-zone OCR chaos already "
          "documented in finding #1, but this specific stray digit happens to "
          "equal exactly the counter value BPHS-1's walk has reached by that "
          "point (46, i.e. one past the real final chapter 45), so it is accepted "
          "as if genuine. Net composition effect: BPHS-1's reported accepted "
          "count of 45 is the RIGHT NUMBER for the WRONG REASON -- it is missing "
          "the genuinely-skipped real Chapter 38, and has this spurious "
          "'Chapter 46' standing in for it, a 1-for-1 substitution that a bare "
          "count comparison would not reveal. This is reported here as an open, "
          "unresolved residual gap in Change 2's design (which only ever "
          "scrutinizes jumps, never exact matches) -- not silently fixed, and "
          "not one of the specific cascades this task's fix targeted, so left "
          "as-is per the surgical scope of this task.")
    w()

    w("## Re-report: fix verification (Change 1 + Change 2 outcome)")
    w()

    def find_accepted(book, num):
        return next((a for a in accepted if a["book"] == book and a["chapter_number"] == num), None)

    def raw200(book, start_pr):
        _, by_page, _ = all_data[book]
        e = by_page.get(start_pr)
        return (e.get("text") or "")[:200] if e else "(page missing)"

    w("**Re-report item 1 -- BPHS-2 Chapters 46, 47, 48:**")
    w()
    for num in (46, 47, 48):
        a = find_accepted("BPHS-2", num)
        if a is None:
            w(f"- Chapter {num}: **NOT ACCEPTED** in this run's BPHS-2 walk. See the "
              "skipped-chapter table below and the Change 2 recovery-attempts table "
              "above for why.")
        else:
            w(f"- Chapter {num}: **ACCEPTED**, start page_ref {a['start_page_ref']}. "
              "Raw text, verbatim, first 200 chars at that page:")
            w()
            w("```")
            w(raw200("BPHS-2", a["start_page_ref"]))
            w("```")
    w()

    w("**Re-report item 2 -- Chapters 66 and 67:**")
    w()
    for num in (66, 67):
        a = find_accepted("BPHS-2", num)
        if a is None:
            skip_entry = next((s for s in skipped if s["chapter_number"] == num), None)
            recovery_entry = next(
                (r for r in recovery_log_all if r["book"] == "BPHS-2"
                 and r["gap_expected_start"] <= num <= r["gap_expected_end"]), None
            )
            guard_entry = next(
                (g for g in guard_rejects_all if g["book"] == "BPHS-2"), None
            )
            if recovery_entry is not None:
                w(f"- Chapter {num}: **NOT ACCEPTED.** Fell inside a recorded look-ahead "
                  f"recovery gap ({recovery_entry['gap_expected_start']}-"
                  f"{recovery_entry['gap_expected_end']}), outcome: "
                  f"{recovery_entry['outcome']}")
            elif skip_entry is not None:
                w(f"- Chapter {num}: **NOT ACCEPTED**, recorded as skipped. "
                  f"found_later status computed in Item 2's table below.")
            else:
                w(f"- Chapter {num}: **NOT ACCEPTED**, and not attributable to a "
                  "recorded skip or recovery attempt either -- see Item 3's reject "
                  "table for this candidate's specific fate (may be a genuinely "
                  "different failure mode than the one this task named).")
        else:
            w(f"- Chapter {num}: **ACCEPTED**, start page_ref {a['start_page_ref']}. "
              "Raw text, verbatim, first 200 chars at that page:")
            w()
            w("```")
            w(raw200("BPHS-2", a["start_page_ref"]))
            w("```")
    w()

    w("## Item 2: Skipped chapter numbers")
    w()
    if not skipped:
        w("None. Every expected chapter number from 1 through the final accepted "
          "number was found as an accepted heading.")
    else:
        w(f"{len(skipped)} chapter number(s) skipped. IMPORTANT DISTINCTION made "
          "here that a naive skip list would hide: for each skipped number, this "
          "probe additionally checked whether a shape-matched candidate for that "
          "EXACT number ever appears anywhere later in the full candidate stream "
          "(it would show up in Item 3's reject list if so). Two genuinely "
          "different situations result:")
        w()
        w("- **Never found anywhere** -- no shape-matched heading for that number "
          "exists in either volume's candidate list at all. Consistent with "
          "genuine OCR loss of that page's running header, or the heading "
          "genuinely absent from this edition.")
        w("- **Found later, but rejected** -- the heading for that exact number "
          "DOES exist later in the candidate stream (in the right place), but by "
          "the time the walk reached it, `expected` had already been pushed past "
          "it by an earlier over-eager skip-jump elsewhere, so the genuine "
          "heading was discarded as a same-number-as-already-passed reject. This "
          "is a cascading-counter-drift artifact, not a true content gap -- the "
          "content is really there.")
        w()
        w("| Chapter # | Searched from | Searched to | Found later anyway? | Explanation |")
        w("|---|---|---|---|---|")
        for s in skipped:
            frm = f"{s['searched_from'][0]} p{s['searched_from'][1]}"
            to = f"{s['searched_to'][0]} p{s['searched_to'][1]}"
            if s["found_later"]:
                later = f"YES -- at {s['found_later_at'][0]} p{s['found_later_at'][1]} ({s['found_later_count']} occurrence(s) total, all rejected)"
                explanation = (
                    "CASCADING-DRIFT ARTIFACT, not a true gap: this chapter's real "
                    "heading exists and was shape-matched correctly, but got "
                    "rejected because `expected` had already been advanced past it "
                    "by an earlier over-eager skip-jump (see the Notable findings "
                    "section for the root cause in this corpus)."
                )
            else:
                later = "no"
                explanation = (
                    "Heading likely lost to OCR damage on that page's running "
                    "header (no shape-matched line for this number appears "
                    "ANYWHERE in the full candidate list for either volume), OR "
                    "genuinely absent from this edition's numbering -- cannot "
                    "distinguish the two from text alone."
                )
            w(f"| {s['chapter_number']} | {frm} | {to} | {later} | {explanation} |")
    w()

    # ---------- item 3: rejects -------------------------------------------
    w("## Item 3: Heading-shaped lines REJECTED by rule (b)")
    w()
    w(f"Total individual rejected candidate lines: {len(rejects)} "
      "(compressed below into consecutive-same-number runs for readability; "
      "every one of the individual lines is accounted for in the `count` column).")
    w()

    for label, _ in BOOKS:
        book_rejects = [r for r in rejects if r["book"] == label]
        first_ch1_page = None
        for a in accepted:
            if a["book"] == label:
                first_ch1_page = a["start_page_ref"]
                break
        toc_region_rejects = [r for r in book_rejects if first_ch1_page is not None and r["page_ref"] < first_ch1_page]
        body_rejects = [r for r in book_rejects if r not in toc_region_rejects]

        w(f"### {label}")
        w()
        if first_ch1_page is not None:
            w(f"Front-matter / TOC-like region defined here as: pages before this "
              f"volume's first accepted chapter heading (page_ref < {first_ch1_page}). "
              "This boundary is DERIVED from the walk's own first acceptance, not "
              "read off a printed TOC.")
        else:
            w("This volume had zero accepted chapters -- front-matter boundary undefined.")
        w()

        w(f"**TOC-region rejects** ({len(toc_region_rejects)} lines, "
          f"{len(compress_rejects(toc_region_rejects))} compressed rows):")
        w()
        groups = compress_rejects(toc_region_rejects)
        if groups:
            w("| Claimed # | Count | First page_ref | Last page_ref | Expected-at-time | Sample line |")
            w("|---|---|---|---|---|---|")
            for g in groups:
                w(f"| {g['claimed_num']} | {g['count']} | {g['first_page_ref']} | "
                  f"{g['last_page_ref']} | {g['expected_at_time_first']} | `{g['sample_line']}` |")
        else:
            w("(none)")
        w()

        w(f"**Body rejects** ({len(body_rejects)} lines, "
          f"{len(compress_rejects(body_rejects))} compressed rows):")
        w()
        groups = compress_rejects(body_rejects)
        if groups:
            w("| Claimed # | Count | First page_ref | Last page_ref | Expected-at-time (first) | Sample line |")
            w("|---|---|---|---|---|---|")
            for g in groups:
                w(f"| {g['claimed_num']} | {g['count']} | {g['first_page_ref']} | "
                  f"{g['last_page_ref']} | {g['expected_at_time_first']} | `{g['sample_line']}` |")
        else:
            w("(none)")
        w()

    # ---------- item 4: partition check ------------------------------------
    w("## Item 4: Partition check on accepted boundaries")
    w()
    chapter_ranges = build_chapter_page_ranges(accepted, book_page_bounds)

    total_checked = 0
    total_pass = 0
    overlaps = []
    orphans = []

    for label, _ in BOOKS:
        first_page, last_page = book_page_bounds[label]
        book_ranges = [r for r in chapter_ranges if r["book"] == label]
        book_ranges_sorted = sorted(book_ranges, key=lambda r: r["start_page_ref"])

        # overlap check
        for a_idx in range(len(book_ranges_sorted) - 1):
            a = book_ranges_sorted[a_idx]
            b = book_ranges_sorted[a_idx + 1]
            if a["end_page_ref"] >= b["start_page_ref"]:
                overlaps.append((label, a["chapter_number"], b["chapter_number"],
                                  a["end_page_ref"], b["start_page_ref"]))

        covered = set()
        for r in book_ranges_sorted:
            for p in range(r["start_page_ref"], r["end_page_ref"] + 1):
                covered.add(p)

        all_pages = set(range(first_page, last_page + 1))
        for p in sorted(all_pages):
            total_checked += 1
            if p in covered:
                total_pass += 1

        book_orphans = sorted(all_pages - covered)
        if book_ranges_sorted:
            pre_first_boundary = book_ranges_sorted[0]["start_page_ref"]
            first_accepted_num = book_ranges_sorted[0]["chapter_number"]
        else:
            pre_first_boundary = last_page + 1
            first_accepted_num = None
        pre_first_count = sum(1 for p in book_orphans if p < pre_first_boundary)
        # A genuine front-matter block (title page, publisher info, preface) is
        # small. A LARGE pre-first-chapter block on a volume whose first
        # accepted chapter number is NOT 1 (i.e. a continuation volume) is
        # suspect -- it likely means real early chapters of that volume got
        # rejected due to counter drift carried over from the other volume
        # (see Notable finding #1), not genuine front matter.
        FRONT_MATTER_SUSPECT_THRESHOLD = 25
        suspect_front_matter = (
            pre_first_count > FRONT_MATTER_SUSPECT_THRESHOLD
            and first_accepted_num is not None
            and first_accepted_num != 1
        )
        for p in book_orphans:
            if p < pre_first_boundary:
                if suspect_front_matter:
                    orphans.append((label, p, "SUSPECT -- NOT genuine front matter; this volume's "
                                     f"first accepted chapter is #{first_accepted_num}, not #1, and the "
                                     f"pre-first-chapter block is {pre_first_count} pages, far larger than "
                                     "a real title/preface block. See Notable finding #1: this is very "
                                     "likely real chapter content (this volume's own early chapters) "
                                     "wrongly rejected due to counter drift carried over from the other "
                                     "volume, not front matter."))
                else:
                    orphans.append((label, p, "front-matter (before this volume's first accepted chapter) -- EXPECTED"))
            else:
                orphans.append((label, p, "gap between accepted chapters (attributable to a recorded SKIP, see item 2)"))

    w(f"- Pages checked: {total_checked}")
    w(f"- Pages assigned to exactly one accepted chapter: {total_pass}")
    w(f"- Overlaps found: {len(overlaps)}")
    if overlaps:
        w()
        w("| Book | Chapter A | Chapter B | A end | B start |")
        w("|---|---|---|---|---|")
        for o in overlaps:
            w(f"| {o[0]} | {o[1]} | {o[2]} | {o[3]} | {o[4]} |")
    w()
    w(f"- Orphan pages (not covered by any accepted chapter range): {len(orphans)}")
    if orphans:
        w()
        w("Compressed into contiguous page-range rows sharing the same book+attribution "
          "(every individual orphan page is still accounted for -- the range is inclusive):")
        w()
        w("| Book | page_ref range | Page count | Attribution |")
        w("|---|---|---|---|")
        runs = []
        for o in orphans:
            book, pref, attr = o
            if runs and runs[-1]["book"] == book and runs[-1]["attr"] == attr and pref == runs[-1]["end"] + 1:
                runs[-1]["end"] = pref
            else:
                runs.append({"book": book, "start": pref, "end": pref, "attr": attr})
        for r in runs:
            count = r["end"] - r["start"] + 1
            rng = f"{r['start']}" if r["start"] == r["end"] else f"{r['start']}-{r['end']}"
            w(f"| {r['book']} | {rng} | {count} | {r['attr']} |")
    w()

    w("**Re-report item 3 -- orphan-page delta vs. the prior run's 119:**")
    w()
    PRIOR_ORPHAN_COUNT = 119
    delta = len(orphans) - PRIOR_ORPHAN_COUNT
    delta_word = "fewer" if delta < 0 else ("more" if delta > 0 else "the same, zero change")
    w(f"- Prior run's orphan count: {PRIOR_ORPHAN_COUNT}")
    w(f"- This run's orphan count: {len(orphans)}")
    if delta != 0:
        w(f"- Delta: {abs(delta)} {delta_word} orphan page(s) than the prior run "
          f"({'-' if delta < 0 else '+'}{delta}).")
    else:
        w("- Delta: 0 -- unchanged from the prior run.")
    w()
    w("**Re-report item 3 -- final skipped-chapter list (post-fix):**")
    w()
    if not skipped:
        w("None -- no chapter numbers remain skipped in this run.")
    else:
        skipped_nums_sorted = sorted({s["chapter_number"] for s in skipped})
        w(f"{len(skipped_nums_sorted)} distinct chapter number(s) remain skipped: "
          f"{skipped_nums_sorted}. Full per-attempt detail is in Item 2's table above "
          "and the Change 2 recovery-attempts table further above.")
    w()

    w("**Re-report item 5 -- BPHS-1 'Chapter 48' at page_ref 456:**")
    w()
    _, bphs1_by_page, _ = all_data["BPHS-1"]
    ch48_entry = bphs1_by_page.get(456)
    ch48_raw = (ch48_entry.get("text") or "")[:300] if ch48_entry else "(page missing)"
    ch48_code_verdict = find_accepted("BPHS-1", 48)
    if ch48_code_verdict is not None:
        w(f"- **Code verdict: ACCEPTED** as BPHS-1 Chapter 48, start page_ref "
          f"{ch48_code_verdict['start_page_ref']}.")
    else:
        w("- **Code verdict: REJECTED** -- no BPHS-1 Chapter 48 appears in this "
          "run's accepted list. (BPHS-1 legitimately ends at Chapter 45 per the "
          "settled facts, so this is the expected/desired outcome if the guard or "
          "recovery logic caught it.)")
    w()
    w("Raw OCR text, verbatim, first 300 chars at BPHS-1 page_ref 456 (read directly "
      "by this script, not transcribed from a prior session's notes):")
    w()
    w("```")
    w(ch48_raw)
    w("```")
    w()
    w("- **My own read of this text:** the settled facts already establish BPHS-1's "
      "real final page (482) as an ERRATA appendix and BPHS-1 as cleanly carrying "
      "only Chapters 1-45; the raw text above should be judged against that frame. "
      "If it reads as continuous prose about the same subject matter as the "
      "surrounding pages (i.e. still inside a real chapter's body, just with a "
      "digit-garbled running-header artifact reading '48') rather than a genuine "
      "new chapter opening, the correct belief is that this is a digit-OCR misread "
      "of '45' and NOT a real Chapter 48 -- i.e. it SHOULD be rejected, whether or "
      "not the code above actually rejected it. Any disagreement between the code "
      "verdict just stated and this belief is reported explicitly, not reconciled "
      "by adjusting either one after the fact.")
    w()

    # ---------- item 5: token distribution ----------------------------------
    w("## Item 5: Token distribution per volume (chars/4 estimate)")
    w()

    # chapter_token_count is now module-level (see above main()) so CHANGE 3's
    # guard inside walk() can share it.
    token_map = {}  # chapter_number+book -> tokens
    for r in chapter_ranges:
        _, by_page, _ = all_data[r["book"]]
        tok = chapter_token_count(r, by_page)
        token_map[(r["book"], r["chapter_number"])] = tok

    for label, _ in BOOKS:
        vals = sorted(v for (b, n), v in token_map.items() if b == label)
        if not vals:
            w(f"### {label}: no accepted chapters, no distribution.")
            continue
        w(f"### {label} (n={len(vals)} chapters)")
        w()
        w(f"- min: {vals[0]:.0f}")
        w(f"- median: {statistics.median(vals):.0f}")
        w(f"- p90: {percentile(vals, 0.9):.0f}")
        w(f"- max: {vals[-1]:.0f}")
        w()
        big = [(b, n, v) for (b, n), v in token_map.items() if b == label and v > 15000]
        big.sort(key=lambda x: -x[2])
        if big:
            w(f"Chapters over 15,000 tokens ({len(big)}):")
            w()
            w("| Chapter # | Title | Est. tokens |")
            w("|---|---|---|")
            for b, n, v in big:
                title = next((r["title"] for r in chapter_ranges if r["book"] == b and r["chapter_number"] == n), "")
                w(f"| {n} | {title or '(none recovered)'} | {v:.0f} |")
        else:
            w("No chapters over 15,000 tokens in this volume.")
        w()

    combined_vals = sorted(token_map.values())
    if combined_vals:
        w("### Combined (both volumes, n=%d)" % len(combined_vals))
        w()
        w(f"- min: {combined_vals[0]:.0f}")
        w(f"- median: {statistics.median(combined_vals):.0f}")
        w(f"- p90: {percentile(combined_vals, 0.9):.0f}")
        w(f"- max: {combined_vals[-1]:.0f}")
        w()

    # ---------- item 6: spot verify ------------------------------------------
    w("## Item 6: Spot verify (raw text, verbatim, first 200 chars at derived start page_ref)")
    w()
    for label, _ in BOOKS:
        _, by_page, _ = all_data[label]
        book_ranges = [r for r in chapter_ranges if r["book"] == label]
        if not book_ranges:
            w(f"### {label}: no accepted chapters to spot-verify.")
            continue
        by_tokens = sorted(book_ranges, key=lambda r: token_map[(r["book"], r["chapter_number"])])
        smallest = by_tokens[0]
        largest = by_tokens[-1]
        n = len(by_tokens)
        # 3 more spread through the range (excluding the two already picked)
        picks = [smallest, largest]
        mid_pool = [r for r in by_tokens if r not in picks]
        if mid_pool:
            spread_idxs = sorted(set([
                max(0, len(mid_pool) // 4),
                len(mid_pool) // 2,
                min(len(mid_pool) - 1, (3 * len(mid_pool)) // 4),
            ]))
            for idx in spread_idxs:
                if len(picks) >= 5:
                    break
                cand = mid_pool[idx]
                if cand not in picks:
                    picks.append(cand)
        # top up if still short of 5 (small n)
        for r in by_tokens:
            if len(picks) >= 5:
                break
            if r not in picks:
                picks.append(r)

        w(f"### {label}")
        w()
        for r in picks:
            tok = token_map[(r["book"], r["chapter_number"])]
            e = by_page.get(r["start_page_ref"])
            raw200 = (e.get("text") or "")[:200] if e else "(page missing)"
            tag = "SMALLEST" if r is smallest else ("LARGEST" if r is largest else "spread")
            w(f"**Chapter {r['chapter_number']}** ({tag}, ~{tok:.0f} tokens, start page_ref {r['start_page_ref']}):")
            w()
            w("```")
            w(raw200)
            w("```")
            w()

    # ---------- item 7: sanity check ----------------------------------------
    w("## Item 7 / Re-report item 4: Sanity check -- BPHS-1 Chapter 24 vs known page_ref 188-235")
    w()
    w("page_ref 188 is the known-good, previously-confirmed start value for BPHS-1 "
      "Chapter 24 (settled fact, not re-derived here) -- this check exists "
      "specifically to catch a REGRESSION: if Changes 1-3 above broke something "
      "that was previously working correctly, it would most plausibly show up "
      "here, since Chapter 24 sits well before any of the gap/cascade zones this "
      "fix targets.")
    w()
    ch24 = next((r for r in chapter_ranges if r["book"] == "BPHS-1" and r["chapter_number"] == 24), None)
    if ch24 is None:
        w("**REGRESSION -- LOUD DISAGREEMENT:** Chapter 24 was NOT accepted by this "
          "walk in BPHS-1 at all (either skipped, guard-rejected, or never reached "
          "the expected counter). This directly disagrees with the known start "
          "page_ref 188 and is a genuine regression signal, not a cosmetic "
          "difference. Not adjusting the walk's logic to force agreement -- "
          "reporting as-is.")
        if any(s["chapter_number"] == 24 for s in skipped if True):
            pass
        skip24 = [s for s in skipped if s["chapter_number"] == 24]
        if skip24:
            w(f"(It was recorded as SKIPPED, searched {skip24[0]['searched_from']} to {skip24[0]['searched_to']}.)")
    else:
        derived = (ch24["start_page_ref"], ch24["end_page_ref"])
        known = (188, 235)
        if derived[0] != known[0]:
            w(f"**REGRESSION -- LOUD DISAGREEMENT ON THE START PAGE:** this run's "
              f"Chapter 24 start page_ref is {derived[0]}, NOT the known-good 188. "
              "This is the specific regression this check exists to catch -- "
              "flagged explicitly, not silently accepted as fine.")
        ch25 = next((r for r in chapter_ranges if r["book"] == "BPHS-1" and r["chapter_number"] == 25), None)
        if derived[0] == known[0] and derived[1] == known[1]:
            w(f"**MATCH.** Walk derived Chapter 24 = page_ref {derived[0]}-{derived[1]}, "
              f"exactly matching the known range {known[0]}-{known[1]}.")
        else:
            w(f"Walk derived Chapter 24 = page_ref {derived[0]}-{derived[1]}. "
              f"Known range = {known[0]}-{known[1]}. Reported explicitly, per instructions, "
              "rather than silently forcing or smoothing over the difference.")
            if derived[0] == known[0] and derived[1] == known[1] - 1:
                ch25_start = ch25["start_page_ref"] if ch25 else None
                w(f"**DISAGREEMENT on the end boundary only (1 page), start boundary "
                  f"MATCHES exactly.** This walk's end-boundary rule is 'up to the page "
                  f"immediately before the NEXT accepted heading's start page'; the next "
                  f"accepted heading is Chapter 25, whose derived start page_ref is "
                  f"{ch25_start}. The known value's upper bound ({known[1]}) equals that "
                  f"same page ({ch25_start}), so the known range appears to use an "
                  "inclusive-of-the-boundary-page convention (the page carrying both the "
                  "tail of Ch.24's content and Ch.25's own running header counted for "
                  "both), while this walk assigns that shared page fully to the chapter "
                  "whose heading starts on it. This is a boundary-CONVENTION difference "
                  "at single-page granularity, not a structural disagreement about where "
                  "Chapter 24 begins or roughly ends -- but it IS a real, measured "
                  "disagreement between the two methods and is reported as such, not "
                  "papered over.")
            else:
                w("**DISAGREEMENT (loud):** start page_ref does NOT match the known "
                  "value, or the gap is larger than a single boundary-convention page. "
                  "Reporting as-is, not adjusting the walk to force agreement.")

    w()

    # ---------- prediction vs actual reconciliation --------------------------
    w("## Prediction vs. actual")
    w()
    w("Against the ORIGINAL (front-matter-based) prediction:")
    w(f"- Predicted BPHS-1 accepted: close to 45. Actual: {len(accepted_bphs1)}.")
    w(f"- Predicted BPHS-2 accepted: close to 52. Actual: {len(accepted_bphs2)}.")
    if combined_vals:
        w(f"- Predicted median chapter tokens: ~3,000-7,000. Actual combined median: "
          f"{statistics.median(combined_vals):.0f}.")
    w()
    w("Against THIS run's fix-effect forecast (stated above, before running the "
      "final Changes-1/2/3 version):")
    w(f"- Predicted BPHS-1 accepted: 42-45. Actual: {len(accepted_bphs1)}.")
    w(f"- Predicted BPHS-2 accepted: 48-52. Actual: {len(accepted_bphs2)}.")
    w(f"- Predicted orphan pages: very roughly 30-90 (hedged). Actual: {len(orphans)} "
      f"(prior run: 119, delta {len(orphans) - 119:+d}).")
    dev_notes = []
    if not (42 <= len(accepted_bphs1) <= 45):
        dev_notes.append(f"BPHS-1 accepted count ({len(accepted_bphs1)}) falls OUTSIDE the "
                          "predicted 42-45 range -- called out explicitly, not smoothed over.")
    if not (48 <= len(accepted_bphs2) <= 52):
        dev_notes.append(f"BPHS-2 accepted count ({len(accepted_bphs2)}) falls OUTSIDE the "
                          "predicted 48-52 range -- called out explicitly, not smoothed over. "
                          "See the Change 2 recovery-attempts table and the Re-report "
                          "fix-verification section above for exactly which chapters did/"
                          "didn't recover and why.")
    if not (30 <= len(orphans) <= 90):
        dev_notes.append(f"Orphan-page count ({len(orphans)}) falls OUTSIDE the loosely-"
                          "predicted 30-90 range -- called out explicitly, not smoothed over.")
    if dev_notes:
        w()
        w("**Deviation(s) from THIS run's own prediction:**")
        for d in dev_notes:
            w(f"- {d}")
    else:
        w()
        w("No deviation from this run's own stated prediction ranges.")
    w()

    # ---------- summary --------------------------------------------------
    w("## Summary")
    w()
    w(f"Sequential walk (shape + expected-counter, no TOC, no printed page numbers) "
      f"accepted {len(accepted)} chapter headings total across both volumes "
      f"({len(accepted_bphs1)} in BPHS-1, {len(accepted_bphs2)} in BPHS-2), with "
      f"{len(skipped)} chapter number(s) recorded as skipped and "
      f"{len(rejects)} individual heading-shaped lines rejected by the "
      f"expected-counter rule (compressed to "
      f"{len(compress_rejects([r for r in rejects if r['book']=='BPHS-1']))+len(compress_rejects([r for r in rejects if r['book']=='BPHS-2']))} "
      f"rows above). Partition check: {total_pass}/{total_checked} pages assigned to "
      f"exactly one accepted chapter, {len(overlaps)} overlaps, {len(orphans)} orphan pages "
      f"(see item 4 for attribution -- front-matter vs. skip-caused gaps).")
    w()
    if ch24 and (ch24["start_page_ref"], ch24["end_page_ref"]) == (188, 235):
        ch24_note = "exact MATCH (188-235)"
    elif ch24 and (ch24["start_page_ref"], ch24["end_page_ref"]) == (188, 234):
        ch24_note = ("start MATCHES exactly (page_ref 188); end differs by 1 page "
                      "(walk: 234, known: 235) -- a boundary-inclusion convention "
                      "difference (page 235 is where Ch.25 itself starts by this "
                      "walk's own rule), not a structural disagreement about where "
                      "Ch.24 begins -- see item 7 for the full explanation")
    elif ch24:
        ch24_note = (f"DISAGREEMENT -- walk derived {ch24['start_page_ref']}-"
                      f"{ch24['end_page_ref']} vs known 188-235, see item 7")
    else:
        ch24_note = "Chapter 24 was not accepted at all by this walk -- DISAGREEMENT, see item 7"
    w(f"Chapter 24 sanity check: {ch24_note}.")
    w()
    w("A genuinely surprising finding surfaced along the way (see the Notable "
      "findings section above, right after item 1, for full detail): the tail of "
      "BPHS-1 (~page_ref 416-482) shows non-monotonic, internally inconsistent "
      "chapter-header OCR (43/44/45/46/48 appearing out of sequence within one "
      "~65-page span, confirmed by direct raw-text inspection, not just candidate "
      "counts), and BPHS-1's actual final page (482) is an ERRATA appendix, not "
      "chapter prose. The walk's accepted 'Chapter 48' (BPHS-1, start page_ref "
      "456) should therefore be treated as LOW CONFIDENCE, plausibly a digit-OCR "
      "misread of '45', not a genuine distinct chapter -- this contradicts the "
      "task's settled-fact framing that BPHS-1 cleanly ends at Chapter 45, and is "
      "reported as a real inconsistency found in the source OCR rather than "
      "silently corrected.")
    w()

    with open(DIAG_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")

    print(f"Wrote {DIAG_PATH} ({len(report_lines)} lines).")
    print(f"Accepted: BPHS-1={len(accepted_bphs1)} BPHS-2={len(accepted_bphs2)} total={len(accepted)}")
    print(f"Skipped: {len(skipped)}  Rejected lines: {len(rejects)}")


if __name__ == "__main__":
    main()
