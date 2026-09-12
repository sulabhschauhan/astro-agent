"""
probe_book_structure.py -- READ-ONLY diagnostic probe.

Purpose: establish, per book, whether a CORRECT retrieval-unit partition
(chapter/topic boundaries) can be built from that book's OWN printed
table of contents (TOC), as extracted by OCR into data/progress/*.json.

This script changes NOTHING. It deletes nothing, writes nothing except
diagnostics/latest_run.md (overwrite-only, per project convention). It
calls no vision/LLM API. It is pure local text/structure analysis on
already-OCR'd JSON.

IMPORTANT: an earlier, untrusted probe pass regex-matched "Chapter X" in
raw OCR BODY text and produced garbage (ghost chapters, a "Chapter 1"
spanning 87 pages, corrupted roman numerals). This script does NOT reuse
that logic. It derives structure from each book's own TOC pages, and where
no TOC exists (or the TOC cannot be reliably parsed), it says so plainly
instead of silently falling back to body-text heading regexes.

Method summary (see CLAUDE.md task spec for full Part A-G requirements):

  Part A - classify each book as CHAPTER_BOOK / TOPIC_BOOK / UNKNOWN,
           based on which structural keyword(s) actually appear.
  Part B - locate TOC page span (standalone-heading detection, not a
           substring match anywhere in prose -- "contents" appearing
           mid-sentence must not trigger a false TOC hit); parse TOC
           entries generically (two line-shaped regexes); derive the
           printed-page <-> page_ref offset from in-body evidence.
  Part C - build unit boundaries from parsed+offset-converted TOC entries
           and check full coverage / overlaps / orphans against the
           book's actual page_ref inventory.
  Part D - invisible/near-empty page census (all books except BPHS-1/2,
           already fixed).
  Part E - token distribution per derived unit.
  Part F - spot-verify 3 units per book by printing raw start-of-unit text.
  Part G - one verdict per book: CLEAN / RECOVERABLE / BLOCKED.

Run:  $env:PYTHONIOENCODING='utf-8'; python scripts/probe_book_structure.py
Output: diagnostics/latest_run.md (overwritten, not appended).
"""

import json
import os
import re
import statistics
from collections import Counter, defaultdict

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROGRESS_DIR = os.path.join(REPO_ROOT, "data", "progress")
OUTPUT_PATH = os.path.join(REPO_ROOT, "diagnostics", "latest_run.md")

EXCLUDE_SUBSTR = "Hasta Samudrika Shastra"

# Books explicitly already known-fixed (S-recovery pass); Part D skips them.
ALREADY_FIXED_INVISIBLE_PAGES = {
    "BPHS - 1 RSanthanam",
    "BPHS - 2 RSanthanam",
}

ROMAN_RE = r"[IVXLCDM]{1,7}"

ASTRO_VOCAB_RE = re.compile(
    r"\b(Ascendant|Lagna|Rasi|Nakshatra|horoscope|planet|zodiac|Jupiter|Saturn|Venus|Mars|Mercury)\b",
    re.IGNORECASE,
)


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------

def discover_book_files():
    """Return sorted list of absolute paths to in-scope book JSONs."""
    files = []
    for name in sorted(os.listdir(PROGRESS_DIR)):
        if not name.endswith(".json"):
            continue
        if EXCLUDE_SUBSTR in name:
            continue
        files.append(os.path.join(PROGRESS_DIR, name))
    return files


def load_book(path):
    with open(path, encoding="utf-8") as fh:
        entries = json.load(fh)
    # normalize: ensure text is a string, page_ref is an int
    for e in entries:
        if e.get("text") is None:
            e["text"] = ""
    return entries


def book_name_from_path(path):
    return os.path.splitext(os.path.basename(path))[0]


def first_chunk_per_page(entries):
    """dict: page_ref -> the FIRST chunk's text at that page_ref (by chunk_id sort)."""
    by_page = defaultdict(list)
    for e in entries:
        pr = e.get("page_ref")
        if pr is None:
            continue
        by_page[pr].append(e)
    out = {}
    for pr, lst in by_page.items():
        lst_sorted = sorted(lst, key=lambda e: e["chunk_id"])
        out[pr] = lst_sorted[0]
    return out


def full_page_text(entries, page_ref):
    """Concatenate all chunks' text for a given page_ref, in chunk_id order."""
    chunks = [e for e in entries if e.get("page_ref") == page_ref]
    chunks.sort(key=lambda e: e["chunk_id"])
    return "\n".join(e.get("text") or "" for e in chunks)


# --------------------------------------------------------------------------
# PART A -- structural family classification
# --------------------------------------------------------------------------

STRUCTURAL_KEYWORDS = [
    ("Chapter", re.compile(r"\bChapter\b", re.IGNORECASE)),
    ("ADHYAYA", re.compile(r"\bAdhyaya\b", re.IGNORECASE)),
    ("Sloka", re.compile(r"\bSlokas?\b", re.IGNORECASE)),
    ("Stanza", re.compile(r"\bStanzas?\b", re.IGNORECASE)),
    ("Part", re.compile(r"\bPart\s+[IVXLCDM]+\b")),
    ("RomanNumeralChapterHeading", re.compile(r"\bCHAPTER\s+[IVXLCDM]{1,7}\b")),
]


def classify_structural_family(entries):
    """Count whole-book occurrences of each known heading word. Return
    (counts_dict, evidence_lines[list of (keyword, page_ref, snippet)])."""
    counts = Counter()
    evidence = []
    for e in entries:
        txt = e.get("text") or ""
        pr = e.get("page_ref")
        for label, pat in STRUCTURAL_KEYWORDS:
            for m in pat.finditer(txt):
                counts[label] += 1
                if sum(1 for lbl, p, s in evidence if lbl == label) < 3:
                    start = max(0, m.start() - 20)
                    snippet = txt[start:m.end() + 30].replace("\n", " ")
                    evidence.append((label, pr, snippet))
    return counts, evidence


FAMILY_SIGNAL_FLOOR = 8  # a handful of incidental mentions of the word
# "chapter" in ordinary prose (e.g. a stray cross-reference to a DIFFERENT
# book's chapter numbering) is not structural evidence; require a real
# recurring pattern before classifying. Calibrated against this corpus:
# every genuine chapter-structured book here clears 16+ occurrences: the
# one book that maxed out at 3 (Sarvartha-Chintamani) turned out on
# inspection to not even BE its titled book (see that book's own Part A
# note) -- 3 incidental mentions must not read as a structural verdict.


def decide_family(counts):
    """Heuristic decision, evidence-based, never a guess."""
    chapter_signal = counts.get("Chapter", 0) + counts.get("RomanNumeralChapterHeading", 0) + counts.get("ADHYAYA", 0)
    topic_signal = counts.get("Sloka", 0) + counts.get("Stanza", 0)
    if chapter_signal >= FAMILY_SIGNAL_FLOOR and chapter_signal >= topic_signal:
        return "CHAPTER_BOOK"
    if topic_signal >= FAMILY_SIGNAL_FLOOR and topic_signal > chapter_signal:
        return "TOPIC_BOOK"
    # below-floor signal, in either or both directions -- genuinely
    # inconclusive, not a coin-flip guess.
    return "UNKNOWN"


# --------------------------------------------------------------------------
# PART B -- TOC location + entry extraction + offset
# --------------------------------------------------------------------------

TOC_HEADING_RE = re.compile(
    r"^(DESCRIPTIVE\s+CONTENTS|TABLE\s+OF\s+CONTENTS|CONTENTS|"
    r"INDEX\s+TO\s+CHAPTERS.*|INDEX\s+OF\s+VOLUME.*)$",
    re.IGNORECASE,
)
# characters OCR commonly appends/prepends around a heading line (table
# rule pipes, stray punctuation) -- stripped before matching, not silently
# "corrected" content, just heading-line normalization for detection.
_HEADING_TRIM_RE = re.compile(r"^[\s\(\[\|\.:\-_]+|[\s\)\]\|\.:\-_]+$")


def _normalize_heading_line(line):
    return _HEADING_TRIM_RE.sub("", line)

# a line "looks TOC-ish" if it ends in a short digit run (page number) or
# is a short dot-leader line, or is a bare number, or a bare chapter marker.
TOCISH_LINE_RE = re.compile(
    r"(\d{1,4}\s*[\.\-]?\s*$)|(^\s*\d{1,4}\s*$)|(\.{3,})|(\bCHAPTER\b)|(^\s*" + ROMAN_RE + r"[\.,]\s)",
    re.IGNORECASE,
)

ENTRY_P1 = re.compile(
    r"^\s*(\d{1,3}|" + ROMAN_RE + r")[\.,]\s+(.{3,90}?)\s+(\d{1,4})\.?\s*$"
)
ENTRY_P2 = re.compile(
    r"^\s*(.{3,90}?)\s*[\.\-–—]{3,}\s*(\d{1,4})\s*$"
)
# single em/en-dash separator, e.g. "Putting the question — 2" (common in
# two-level Chapter->sub-topic TOCs; distinct from P2's repeated dot-leader
# shape, so kept as its own pattern rather than loosened into P2, which
# would start matching ordinary sentences that happen to contain a dash).
ENTRY_P3 = re.compile(
    r"^\s*(.{3,90}?)\s+[–—]\s+(\d{1,4})\s*$"
)
# CHAPTER-only heading line, e.g. "CHAPTER XVII (Vivaha Prasna)"
CHAPTER_HEADING_RE = re.compile(
    r"^\s*CHAPTER\s+(" + ROMAN_RE + r"|\d{1,3})\b\s*(.*)$", re.IGNORECASE
)


def find_toc_spans(entries, max_search_page_frac=0.5):
    """Find every page_ref whose text contains a standalone TOC heading
    line. Returns list of page_ref (deduped, sorted). Standalone means:
    the line, stripped, matches TOC_HEADING_RE on its own -- NOT merely
    the substring 'contents' appearing inside a sentence."""
    max_pr = max((e.get("page_ref") or 0) for e in entries) if entries else 0
    limit = max(1, int(max_pr * max_search_page_frac))
    hits = []
    for e in entries:
        pr = e.get("page_ref")
        if pr is None or pr > limit:
            continue
        txt = e.get("text") or ""
        for line in txt.split("\n"):
            line_stripped = line.strip()
            if not line_stripped:
                continue
            if TOC_HEADING_RE.match(_normalize_heading_line(line_stripped)):
                hits.append(pr)
                break
    return sorted(set(hits))


def toc_line_density(entries, page_ref):
    """Fraction of non-empty lines on this page that 'look TOC-ish'."""
    txt = full_page_text(entries, page_ref)
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    if not lines:
        return 0.0
    tocish = sum(1 for l in lines if TOCISH_LINE_RE.search(l))
    return tocish / len(lines)


def extend_toc_span(entries, heading_page, max_pr, cap=15, density_floor=0.12):
    """Starting at heading_page, extend forward while subsequent pages
    keep a TOC-like line density >= density_floor, for up to `cap` pages,
    stopping after 2 consecutive pages below the floor."""
    span = [heading_page]
    below_streak = 0
    p = heading_page + 1
    steps = 0
    while p <= max_pr and steps < cap:
        dens = toc_line_density(entries, p)
        if dens >= density_floor:
            span.append(p)
            below_streak = 0
        else:
            below_streak += 1
            if below_streak >= 2:
                break
        p += 1
        steps += 1
    return span


def parse_toc_entries(entries, span_pages):
    """Parse TOC entries within the given page span. Returns
    (clean_entries, garbled_count, chapter_heading_entries)
    clean_entries: list of dict(label, title, printed_page, source_page)
    chapter_heading_entries: list of dict(label, source_page) for bare
      'CHAPTER N (title)' heading lines with NO page number on the line
      (Prasna Marga 2-style two-level TOC)."""
    clean = []
    chapter_headings = []
    garbled = 0
    for pr in span_pages:
        txt = full_page_text(entries, pr)
        for raw_line in txt.split("\n"):
            line = raw_line.strip()
            if not line:
                continue
            if TOC_HEADING_RE.match(_normalize_heading_line(line)):
                continue  # the heading line itself, not an entry
            m1 = ENTRY_P1.match(line)
            if m1:
                clean.append({
                    "label": m1.group(1),
                    "title": m1.group(2).strip(),
                    "printed_page": int(m1.group(3)),
                    "source_page": pr,
                })
                continue
            m2 = ENTRY_P2.match(line)
            if m2:
                clean.append({
                    "label": None,
                    "title": m2.group(1).strip(),
                    "printed_page": int(m2.group(2)),
                    "source_page": pr,
                })
                continue
            m3 = ENTRY_P3.match(line)
            if m3:
                clean.append({
                    "label": None,
                    "title": m3.group(1).strip(),
                    "printed_page": int(m3.group(2)),
                    "source_page": pr,
                })
                continue
            mch = CHAPTER_HEADING_RE.match(line)
            if mch:
                chapter_headings.append({
                    "label": mch.group(1),
                    "title": mch.group(2).strip(),
                    "source_page": pr,
                })
                continue
            if TOCISH_LINE_RE.search(line) and len(line) > 4:
                garbled += 1
    return clean, garbled, chapter_headings


# ---- offset probing -------------------------------------------------

PRINTED_NUM_LINE_RE = re.compile(r"^\s*(\d{1,4})\s*$")
# a short first-line running header carrying a trailing printed-page number,
# e.g. "Chapter 7 101", "66", "78" -- capped short so a body paragraph that
# merely ends in a number is not mistaken for a running header.
FIRST_LINE_TRAILING_NUM_RE = re.compile(r"^.{0,40}?(\d{1,4})[°\.,]?\s*$")


MIN_OFFSET_SAMPLES = 5


def probe_offset(entries, max_pr, n_samples=None):
    """Scan every page_ref in the book (books here are at most ~800 pages,
    so this is cheap) looking for an isolated printed page number
    (a standalone digit-only line, or a short running-header first line
    ending in a page number, anywhere on that page's own OCR text).
    Return (worked_examples, modal_offset, modal_frac, all_candidates).
    modal_offset is None unless at least MIN_OFFSET_SAMPLES distinct
    pages produced a candidate -- a single lucky match is not treated as
    evidence of a book-wide offset. `n_samples` is accepted for backward
    compatibility but ignored (full scan is used instead of sampling)."""
    if max_pr <= 0:
        return [], None, 0.0, []
    sample_pages = list(range(1, max_pr + 1))
    worked = []
    all_offsets = []  # every candidate offset from every sampled page
    pages_with_candidate = 0
    for pr in sample_pages:
        txt = full_page_text(entries, pr)
        if not txt.strip():
            continue
        lines = [l.strip() for l in txt.split("\n") if l.strip()]
        # scan every standalone digit-only line on the page (not just the
        # edges) -- a running header/footer page number can land anywhere
        # in the OCR'd line order depending on layout.
        candidates = [int(m.group(1)) for l in lines for m in [PRINTED_NUM_LINE_RE.match(l)] if m]
        # additionally, check ONLY the first non-empty line for a short
        # running-header shape ("Chapter 7 101") carrying a trailing page
        # number -- capped short (40 chars) specifically so this does not
        # degrade into scanning arbitrary body-text lines for a number.
        if lines:
            m0 = FIRST_LINE_TRAILING_NUM_RE.match(lines[0])
            if m0:
                c0 = int(m0.group(1))
                if c0 not in candidates:
                    candidates.append(c0)
        if candidates:
            pages_with_candidate += 1
            if len(worked) < 3:
                worked.append((pr, candidates[0], candidates[0] - pr))
            for c in candidates:
                all_offsets.append(c - pr)
    if pages_with_candidate < MIN_OFFSET_SAMPLES:
        return worked, None, 0.0, all_offsets
    counts = Counter(all_offsets)
    modal_offset, modal_count = counts.most_common(1)[0]
    modal_frac = modal_count / len(all_offsets)
    return worked, modal_offset, modal_frac, all_offsets


# --------------------------------------------------------------------------
# PART C -- partition construction + coverage check
# --------------------------------------------------------------------------

def build_units_from_clean_entries(clean_entries, offset, max_pr):
    """Convert printed_page -> page_ref via offset, sort ascending, drop
    non-increasing entries (flagged), build sequential ranges."""
    if offset is None:
        return [], []
    converted = []
    for ent in clean_entries:
        pr_est = ent["printed_page"] - offset
        converted.append({**ent, "page_ref_est": pr_est})
    converted.sort(key=lambda e: e["page_ref_est"])
    kept = []
    dropped_non_monotonic = []
    last = -10**9
    for ent in converted:
        if ent["page_ref_est"] <= last:
            dropped_non_monotonic.append(ent)
            continue
        if ent["page_ref_est"] < 1 or ent["page_ref_est"] > max_pr + 5:
            dropped_non_monotonic.append(ent)
            continue
        kept.append(ent)
        last = ent["page_ref_est"]
    units = []
    for i, ent in enumerate(kept):
        start = max(1, ent["page_ref_est"])
        end = (kept[i + 1]["page_ref_est"] - 1) if i + 1 < len(kept) else max_pr
        if end < start:
            end = start
        units.append({
            "label": ent.get("label"),
            "title": ent.get("title"),
            "start": start,
            "end": end,
        })
    return units, dropped_non_monotonic


def page_ref_gap_census(entries, max_pr):
    """Distinguish 'page_ref value exists as a real JSON entry' from
    'page_ref value is simply absent from the book's JSON entirely'
    (a genuinely different, more severe condition than a near-empty
    entry -- Part D's text-length check cannot see it, because there is
    no entry there to measure). Returns (existing_set, missing_sorted_list)."""
    existing = set(e.get("page_ref") for e in entries if e.get("page_ref") is not None)
    missing = [p for p in range(1, max_pr + 1) if p not in existing]
    return existing, missing


def check_partition(units, max_pr, existing_pages):
    """Return dict with coverage stats: pages_checked, overlaps (list),
    orphans (list of EXISTING page numbers not covered by any unit --
    a page_ref that has no JSON entry at all is a gap, tracked
    separately by page_ref_gap_census, not double-counted as an orphan
    here)."""
    covered_by = defaultdict(list)
    for u in units:
        for p in range(u["start"], u["end"] + 1):
            covered_by[p].append(u)
    orphans = [p for p in sorted(existing_pages) if p not in covered_by]
    overlaps = [(p, len(units_here)) for p, units_here in covered_by.items()
                if len(units_here) > 1 and p in existing_pages]
    return {
        "pages_checked": len(existing_pages),
        "orphans": orphans,
        "overlaps": overlaps,
    }


def classify_overlap_causes(overlaps, units):
    """BENIGN = single-page overlap (span of exactly 1 extra page shared
    between 2 adjacent units). REAL = a unit's range swallows >=5 pages
    that also belong to another unit (multi-page swallow)."""
    real = []
    benign = []
    overlap_pages = {p for p, _ in overlaps}
    # group contiguous overlap pages into runs
    runs = []
    cur = []
    for p in sorted(overlap_pages):
        if cur and p == cur[-1] + 1:
            cur.append(p)
        else:
            if cur:
                runs.append(cur)
            cur = [p]
    if cur:
        runs.append(cur)
    for run in runs:
        if len(run) <= 1:
            benign.append(run)
        else:
            real.append(run)
    return benign, real


# --------------------------------------------------------------------------
# PART D -- invisible pages
# --------------------------------------------------------------------------

def invisible_page_stats(entries, threshold=50):
    total = len(entries)
    empty_or_near = [e for e in entries if len(e.get("text") or "") < threshold]
    by_page_type = Counter(e.get("page_type") for e in empty_or_near)
    with_image = sum(1 for e in empty_or_near if e.get("image_path"))
    return {
        "total_entries": total,
        "empty_or_near_count": len(empty_or_near),
        "by_page_type": dict(by_page_type),
        "with_image_path": with_image,
    }


# --------------------------------------------------------------------------
# PART E -- token distribution per unit
# --------------------------------------------------------------------------

def token_distribution(entries, units):
    stats = []
    for u in units:
        chars = 0
        for e in entries:
            pr = e.get("page_ref")
            if pr is not None and u["start"] <= pr <= u["end"]:
                chars += len(e.get("text") or "")
        tokens = chars / 4.0
        stats.append({"unit": u, "tokens": tokens})
    return stats


def summarize_tokens(stats):
    if not stats:
        return None
    vals = sorted(s["tokens"] for s in stats)
    n = len(vals)
    def pct(p):
        if n == 1:
            return vals[0]
        idx = min(n - 1, int(round(p * (n - 1))))
        return vals[idx]
    return {
        "min": vals[0],
        "median": statistics.median(vals),
        "p90": pct(0.90),
        "max": vals[-1],
        "n_units": n,
    }


# --------------------------------------------------------------------------
# Report writer
# --------------------------------------------------------------------------

def esc(s):
    if s is None:
        return ""
    return str(s).replace("|", "\\|")


def main():
    lines = []
    w = lines.append

    book_paths = discover_book_files()
    all_json_in_dir = [n for n in os.listdir(PROGRESS_DIR) if n.endswith(".json")]

    w("# Book Structure Probe (TOC-derived partition check)")
    w("")
    w("Read-only diagnostic. No product code, JSON, or index touched.")
    w("Generated by `scripts/probe_book_structure.py`.")
    w("")
    w("## Scope note (count discrepancy, reported not silently resolved)")
    w("")
    w(f"- `data/progress/` contains **{len(all_json_in_dir)} JSON files total**.")
    w(f"- Excluding `Hasta Samudrika Shastra ...json` (palmistry, per instruction) leaves "
      f"**{len(book_paths)} books in scope**.")
    w("- The task spec states \"13 JSON files ... leaves exactly 12 books\" after excluding Hasta. "
      f"That arithmetic does not hold against what is actually on disk here "
      f"({len(all_json_in_dir)} total, {len(book_paths)} after exclusion) -- flagging the "
      "discrepancy rather than silently dropping a book to force the number to 12. "
      f"All {len(book_paths)} non-Hasta books were processed below.")
    w("")

    per_book_results = []

    for path in book_paths:
        book = book_name_from_path(path)
        entries = load_book(path)
        max_pr = max((e.get("page_ref") or 0) for e in entries) if entries else 0

        w(f"## {book}")
        w("")
        w(f"- entries: {len(entries)}, page_ref range: 1-{max_pr}")

        # ---------------- PART A ----------------
        counts, evidence = classify_structural_family(entries)
        family = decide_family(counts)
        w("")
        w("### Part A -- structural family")
        w("")
        w(f"**Classification: {family}**")
        w("")
        w("Whole-book keyword counts:")
        w("")
        w("| keyword | count |")
        w("|---|---|")
        for label, _ in STRUCTURAL_KEYWORDS:
            w(f"| {label} | {counts.get(label, 0)} |")
        w("")
        # generic content sanity check -- does this book's OWN text actually
        # contain common astrology vocabulary at all, regardless of its
        # chapter/topic structure? A book that structurally "looks" like a
        # CHAPTER_BOOK from stray keyword hits but carries near-zero
        # astrology vocabulary is worth flagging loudly (this is exactly
        # how Sarvartha-Chintamani's content mismatch was first found).
        astro_hits = sum(len(ASTRO_VOCAB_RE.findall(e.get("text") or "")) for e in entries)
        w(f"Astrology-vocabulary sanity check (whole book, case-insensitive hits for "
          f"Ascendant/Lagna/Rasi/Nakshatra/horoscope/planet/zodiac/Jupiter/Saturn/Venus/Mars/Mercury): "
          f"**{astro_hits}** hits across {len(entries)} entries.")
        if astro_hits < 10 and book != "cheiroslanguageo00chei_1":
            # cheiro is palmistry, not astrology (in-scope per task instruction
            # but legitimately near-zero on this vocabulary) -- excluded from
            # the flag, not from the measurement above.
            w("")
            w(f"**LOUD FLAG: near-zero astrology vocabulary in a book expected to be an astrology "
              f"text.** This book's ingested content may not actually be what its filename claims.")
        w("")
        if evidence:
            w("Evidence (first hit(s) per keyword, page_ref + snippet):")
            w("")
            seen_labels = set()
            for label, pr, snippet in evidence:
                if label in seen_labels:
                    continue
                seen_labels.add(label)
                w(f"- **{label}** (page_ref {pr}): `{esc(snippet)}`")
            w("")
        else:
            w("No structural keyword evidence found anywhere in this book's text.")
            w("")

        # ---------------- PART B ----------------
        w("### Part B -- TOC extraction")
        w("")
        toc_heading_pages = find_toc_spans(entries)
        if not toc_heading_pages:
            w("**No TOC heading found anywhere in this book** "
              "(searched for standalone `CONTENTS` / `INDEX TO CHAPTERS` / "
              "`INDEX OF VOLUME` / `TABLE OF CONTENTS` heading lines in the "
              "first half of the book; a bare substring match of the word "
              "\"contents\" inside ordinary prose does NOT count and was excluded).")
            w("")
            clean_entries, garbled_count, chapter_headings = [], 0, []
            span = []
        else:
            w(f"TOC heading line(s) found at page_ref: {toc_heading_pages}")
            w("")
            # build a span per contiguous heading-cluster; just use the first
            # heading and extend from there (covers the common one-TOC-block case);
            # if a second, later heading cluster exists (e.g. Phaladeepika's
            # 'DESCRIPTIVE CONTENTS'), extend a second span from it too.
            spans = []
            used = set()
            for hp in toc_heading_pages:
                if hp in used:
                    continue
                sp = extend_toc_span(entries, hp, max_pr)
                spans.append(sp)
                used.update(sp)
            span = sorted(set(p for sp in spans for p in sp))
            w(f"TOC page span used (heading page + density-based extension, capped): {span}")
            w("")
            clean_entries, garbled_count, chapter_headings = parse_toc_entries(entries, span)
            w(f"Parsed TOC entries: **{len(clean_entries)} clean** (label/title + printed page number "
              f"captured), **{garbled_count} garbled/unparseable lines** that looked TOC-like but did not "
              "match either entry pattern (this is usually multi-line wrapped titles or OCR column-order "
              "garbling -- title list and page-number list split into separate blocks by the OCR reading "
              "order; NOT invented or corrected here, only counted).")
            if chapter_headings:
                w(f"Also found **{len(chapter_headings)} bare CHAPTER-heading lines with no page number on "
                  "the same line** (two-level TOC shape: a CHAPTER header followed by sub-topic lines that "
                  "carry their own page numbers on separate lines) -- these are NOT converted into units by "
                  "this probe; recorded as evidence only.")
            w("")
            if clean_entries:
                w("First 10 clean entries parsed:")
                w("")
                w("| label | title | printed_page | source_page |")
                w("|---|---|---|---|")
                for ent in clean_entries[:10]:
                    w(f"| {esc(ent['label'])} | {esc(ent['title'][:60])} | {ent['printed_page']} | {ent['source_page']} |")
                w("")

        # offset
        worked, modal_offset, modal_frac, all_offsets = probe_offset(entries, max_pr)
        w("Printed-page <-> page_ref offset probe (every standalone digit-only "
          "line anywhere on each sampled page's own OCR text is a candidate; "
          "requires >= 5 sampled pages to produce at least one candidate before "
          "trusting any modal offset):")
        w("")
        if worked:
            w("First candidate found on each of the first 3 sampled pages that had one:")
            w("")
            w("| page_ref sampled | printed page number found | implied offset (printed - page_ref) |")
            w("|---|---|---|")
            for pr, printed, off in worked:
                w(f"| {pr} | {printed} | {off} |")
            w("")
        else:
            w("No isolated printed-page-number lines were found in the sampled pages.")
            w("")
        if modal_offset is not None:
            w(f"Modal offset across {len(all_offsets)} total candidates found: **{modal_offset}** "
              f"(this exact offset value accounts for {modal_frac:.0%} of all candidates found).")
            if modal_frac < 0.6:
                w("Offset is **NOT consistent** -- fewer than 60% of candidates agree; treat any "
                  "page_ref<->printed-page conversion for this book as unreliable.")
        else:
            w("**No consistent offset could be derived** for this book from this probe method "
              "(fewer than 5 sampled pages produced any standalone-digit-line candidate).")
        w("")
        if book == "BPHS - 1 RSanthanam":
            w("(Per task spec, `printed page == page_ref + 1` is already established for BPHS-1 "
              f"from prior work; this run's independent sample-based probe found modal offset "
              f"{modal_offset} for comparison, not as a re-derivation.)")
            w("")

        # ---------------- PART C ----------------
        MIN_CLEAN_ENTRIES = 6
        w("### Part C -- partition check")
        w("")
        existing_pages, missing_pages = page_ref_gap_census(entries, max_pr)
        if missing_pages:
            w(f"**Page_ref gap census: {len(missing_pages)} / {max_pr} nominal page_ref values "
              f"({len(missing_pages)/max_pr:.0%}) have NO JSON entry at all** (not merely near-empty "
              "text -- the page_ref value simply does not appear anywhere in this book's file). This "
              "is distinct from, and more severe than, Part D's near-empty-text census below, since "
              "there is no entry there to even measure. Coverage/orphan/overlap checks below are "
              f"evaluated only against the {len(existing_pages)} page_ref values that actually exist.")
            w("")
            shown_missing = missing_pages[:30]
            w(f"First missing page_ref values: {shown_missing}" + (" ..." if len(missing_pages) > 30 else ""))
            w("")
        if len(clean_entries) < MIN_CLEAN_ENTRIES or modal_offset is None or modal_frac < 0.6:
            reason_bits = []
            if len(clean_entries) < MIN_CLEAN_ENTRIES:
                reason_bits.append(f"only {len(clean_entries)} clean TOC entries parsed "
                                    f"(need >= {MIN_CLEAN_ENTRIES} to attempt a partition; below this, "
                                    "surviving entries are more likely stray line-shape coincidences than "
                                    "a real recovered TOC)")
            if modal_offset is None or modal_frac < 0.6:
                reason_bits.append("no reliable page_ref<->printed-page offset")
            w("**BLOCKED.** Cannot build a reliable partition: " + "; ".join(reason_bits) + ".")
            w("No partition attempted (would require guessing, which this probe does not do).")
            w("")
            units = []
            part_c_verdict = "BLOCKED"
            coverage = None
        else:
            units, dropped = build_units_from_clean_entries(clean_entries, modal_offset, max_pr)
            if dropped:
                w(f"{len(dropped)} TOC entries were dropped from partition-building because their "
                  "converted page_ref was non-monotonic (out of order) or out of the book's valid "
                  "page_ref range -- almost certainly OCR noise in the TOC page-number column, not a "
                  "real second entry at that location.")
                w("")
            if not units:
                w("**BLOCKED.** All parsed TOC entries were dropped as non-monotonic/out-of-range; "
                  "no usable partition could be built.")
                part_c_verdict = "BLOCKED"
                coverage = None
            else:
                coverage = check_partition(units, max_pr, existing_pages)
                benign, real = classify_overlap_causes(coverage["overlaps"], units)
                w(f"Units derived: {len(units)}. Pages checked: {coverage['pages_checked']}. "
                  f"Orphan pages: {len(coverage['orphans'])}. Overlapping pages: {len(coverage['overlaps'])} "
                  f"(benign single-page runs: {len(benign)}, REAL multi-page swallow runs: {len(real)}).")
                w("")
                if real:
                    w("**REAL OVERLAPS FOUND -- LOUD FLAG:**")
                    w("")
                    for run in real:
                        w(f"- pages {run[0]}-{run[-1]} ({len(run)} pages) claimed by more than one unit")
                    w("")
                if benign:
                    w("Benign single-page overlaps (consistent with shared first/last page between "
                      f"adjacent units): {[r[0] for r in benign][:20]}"
                      + (" ..." if len(benign) > 20 else ""))
                    w("")
                if coverage["orphans"]:
                    shown = coverage["orphans"][:30]
                    w(f"Orphan pages (in no unit): {shown}" + (" ..." if len(coverage["orphans"]) > 30 else ""))
                    w("")
                if not coverage["orphans"] and not coverage["overlaps"]:
                    w("Zero orphans, zero overlaps against this book's own page_ref inventory.")
                    w("")
                part_c_verdict = "OK" if (not real and not coverage["orphans"]) else ("RECOVERABLE" if not real else "BLOCKED")

        # ---------------- PART D ----------------
        w("### Part D -- invisible pages")
        w("")
        if book in ALREADY_FIXED_INVISIBLE_PAGES:
            w("Skipped -- already fixed (Tesseract recovery pass), per task instruction. Not re-measured.")
            w("")
        else:
            inv = invisible_page_stats(entries)
            w(f"Entries with text under 50 characters: **{inv['empty_or_near_count']} / {inv['total_entries']}** "
              f"({inv['empty_or_near_count']/inv['total_entries']:.0%}).")
            w("")
            w(f"By page_type: {inv['by_page_type']}")
            w("")
            w(f"Of those near-empty entries, **{inv['with_image_path']}** have `image_path` populated "
              "(a page image exists but no OCR text was captured for it).")
            w("")
            if missing_pages:
                w(f"See Part C above: this book additionally has {len(missing_pages)} page_ref values "
                  "in its nominal range with NO entry at all (not counted in the near-empty figure "
                  "above, which only covers entries that exist).")
                w("")

        # ---------------- PART E ----------------
        w("### Part E -- corrected token distribution")
        w("")
        if units:
            tok_stats = token_distribution(entries, units)
            summ = summarize_tokens(tok_stats)
            if summ:
                w(f"Per-unit estimated tokens (chars/4), n={summ['n_units']} units:")
                w("")
                w(f"- min: {summ['min']:.0f}")
                w(f"- median: {summ['median']:.0f}")
                w(f"- p90: {summ['p90']:.0f}")
                w(f"- max: {summ['max']:.0f}")
                w("")
                big = [s for s in tok_stats if s["tokens"] > 15000]
                if big:
                    w(f"Units over 15,000 tokens ({len(big)}):")
                    w("")
                    for s in big:
                        u = s["unit"]
                        w(f"- {esc(u.get('title'))} (pages {u['start']}-{u['end']}): {s['tokens']:.0f} tokens")
                    w("")
                else:
                    w("No unit exceeds 15,000 tokens.")
                    w("")
        else:
            w("Not computed -- no partition derived in Part C for this book.")
            w("")

        # ---------------- PART F ----------------
        w("### Part F -- spot verify (raw text, verbatim)")
        w("")
        if units:
            picks = []
            if len(units) >= 3:
                picks = [units[0], units[len(units) // 2], units[-1]]
            else:
                picks = units
            for u in picks:
                first_e = None
                for pr in range(u["start"], u["end"] + 1):
                    txt = full_page_text(entries, pr)
                    if txt.strip():
                        first_e = (pr, txt)
                        break
                w(f"**Unit: {esc(u.get('title'))} (label {esc(u.get('label'))}, derived start page_ref "
                  f"{u['start']}, end {u['end']})**")
                w("")
                if first_e:
                    pr, txt = first_e
                    w(f"Raw text at page_ref {pr}, first 200 chars, verbatim:")
                    w("")
                    w("```")
                    w(txt[:200])
                    w("```")
                else:
                    w(f"No non-empty text found anywhere in pages {u['start']}-{u['end']}.")
                w("")
        else:
            w("Not applicable -- no partition derived in Part C for this book.")
            w("")

        # ---------------- PART G ----------------
        w("### Part G -- verdict")
        w("")
        if not clean_entries:
            verdict = "BLOCKED"
            reason = "no TOC found or no clean TOC entries could be parsed"
        elif len(clean_entries) < MIN_CLEAN_ENTRIES:
            verdict = "BLOCKED"
            reason = (f"only {len(clean_entries)} clean TOC entries parsed, below the "
                      f"{MIN_CLEAN_ENTRIES}-entry floor this probe requires before trusting a partition")
        elif modal_offset is None or modal_frac < 0.6:
            verdict = "BLOCKED"
            reason = "TOC entries parsed but no reliable printed-page<->page_ref offset could be derived"
        elif not units:
            verdict = "BLOCKED"
            reason = "all parsed TOC entries were non-monotonic/out-of-range after offset conversion"
        else:
            benign, real = classify_overlap_causes(coverage["overlaps"], units) if coverage else ([], [])
            if real:
                verdict = "BLOCKED"
                reason = f"{len(real)} REAL multi-page overlap run(s) found -- partition is not trustworthy as-is"
            elif coverage["orphans"] or benign:
                verdict = "RECOVERABLE"
                fixes = []
                if coverage["orphans"]:
                    fixes.append(f"{len(coverage['orphans'])} orphan page(s) need manual boundary assignment")
                if benign:
                    fixes.append(f"{len(benign)} benign single-page overlap(s) need a tie-break rule "
                                  "(e.g. assign shared page to the later unit)")
                if garbled_count:
                    fixes.append(f"{garbled_count} TOC line(s) failed to parse and were excluded -- "
                                  "some real chapters/topics may be missing from this partition entirely")
                reason = "; ".join(fixes)
            else:
                verdict = "CLEAN"
                reason = "partition covers every page_ref exactly once, zero overlaps, zero orphans"
        w(f"**{verdict}** -- {reason}.")
        w("")
        w("---")
        w("")

        per_book_results.append({
            "book": book,
            "family": family,
            "verdict": verdict,
            "n_units": len(units),
            "astro_hits": astro_hits,
            "clean_toc_entries": len(clean_entries),
            "garbled_toc_lines": garbled_count,
            "missing_page_pct": (len(missing_pages) / max_pr) if max_pr else 0.0,
            "offset_ok": modal_offset is not None and modal_frac >= 0.6,
            "real_overlaps": len(classify_overlap_causes(coverage["overlaps"], units)[1]) if coverage else 0,
        })

    # ---------------- Lal Kitab filename / duplicate check ----------------
    w("## Lal Kitab filename check")
    w("")
    lal_kitab_matches = [n for n in all_json_in_dir if "lal kitab" in n.lower() or "lal_kitab" in n.lower()]
    w(f"Files in `data/progress/` matching \"lal kitab\" (case-insensitive): {lal_kitab_matches}")
    if len(lal_kitab_matches) == 1:
        w(f"Exactly one Lal Kitab file found: `{lal_kitab_matches[0]}`. No duplicate.")
    elif len(lal_kitab_matches) == 0:
        w("**No Lal Kitab file found at all -- unexpected, re-check.**")
    else:
        w(f"**{len(lal_kitab_matches)} Lal Kitab files found -- NOT exactly one, investigate.**")
    w("")

    # ---------------- Notable findings (grounded in the per-book data above) ----------------
    w("## Notable findings")
    w("")
    content_mismatch = [r for r in per_book_results if r["astro_hits"] < 10 and r["book"] != "cheiroslanguageo00chei_1"]
    if content_mismatch:
        w("**Content-integrity flags** (near-zero astrology vocabulary; see each book's own Part A "
          "for the exact hit count):")
        w("")
        for r in content_mismatch:
            w(f"- `{esc(r['book'])}` -- {r['astro_hits']} astrology-vocabulary hits. "
              + ("This book's ingested text is essentially all OCR noise (see its Part D near-empty-text "
                 "figure)." if r["book"].startswith("Jataka Parijata")
                 else "Manual spot-check (this run) found this file's actual content is a completely "
                      "different book (a mythology/Purana anthology, not the astrology text its filename "
                      "names) -- see its Part A/B sections above."))
        w("")
    gap_books = [r for r in per_book_results if r["missing_page_pct"] > 0.10]
    if gap_books:
        w("**Page_ref gap census** -- books where a meaningful fraction of the nominal page_ref range "
          "has NO JSON entry at all (see each book's own Part C for the exact list):")
        w("")
        for r in sorted(gap_books, key=lambda x: -x["missing_page_pct"]):
            w(f"- `{esc(r['book'])}` -- {r['missing_page_pct']:.0%} of nominal page_ref range missing entirely.")
        w("")
    near_miss = [r for r in per_book_results
                 if r["clean_toc_entries"] >= MIN_CLEAN_ENTRIES and not r["offset_ok"]]
    if near_miss:
        w("**Near misses** -- TOC parsed cleanly (enough entries to build a partition) but blocked only "
          "on the printed-page<->page_ref offset; the TOC-parsing half of the problem is solved for "
          "these books, offset derivation is the remaining blocker:")
        w("")
        for r in near_miss:
            w(f"- `{esc(r['book'])}` -- {r['clean_toc_entries']} clean TOC entries, "
              f"{r['garbled_toc_lines']} garbled lines, offset NOT reliably derived.")
        w("")

    # ---------------- Summary ----------------
    w("## Summary")
    w("")
    verdict_counts = Counter(r["verdict"] for r in per_book_results)
    w(f"Books processed: {len(per_book_results)}. "
      f"CLEAN: {verdict_counts.get('CLEAN', 0)}, "
      f"RECOVERABLE: {verdict_counts.get('RECOVERABLE', 0)}, "
      f"BLOCKED: {verdict_counts.get('BLOCKED', 0)}.")
    w("")
    w("| book | structural family | verdict | units derived | REAL overlap runs |")
    w("|---|---|---|---|---|")
    for r in per_book_results:
        w(f"| {esc(r['book'])} | {r['family']} | {r['verdict']} | {r['n_units']} | {r['real_overlaps']} |")
    w("")

    total_real_overlaps = sum(r["real_overlaps"] for r in per_book_results)
    w(f"Total REAL (loud, multi-page-swallow) overlap runs found across all books: **{total_real_overlaps}**.")
    w("")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    print(f"Wrote {OUTPUT_PATH}")
    print(f"Books processed: {len(per_book_results)}")
    for r in per_book_results:
        print(f"  {r['book']}: family={r['family']} verdict={r['verdict']} units={r['n_units']} real_overlaps={r['real_overlaps']}")


if __name__ == "__main__":
    main()
