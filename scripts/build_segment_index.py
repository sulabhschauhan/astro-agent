"""
PERMANENT BUILD SCRIPT. Builds `data/segment_index_bphs_career3.json`, a
fine-grained, individually-citable segment index over exactly three BPHS-1
chapter units already isolated by `data/chapter_index_bphs.json`
(`bphs1_ch21`, `bphs1_ch24`, `bphs1_ch34`).

WHY THIS EXISTS: a prior spike asked an LLM-style interpreter to answer a
career question by reproducing VERBATIM quotes from these three chapters'
raw OCR text. 8 of 11 quotes mismatched the true source; two were real
fabrications (an invented "5th lord in 2nd house" rule and a "Raja Yoga"
verse that may not exist as quoted). The fix is architectural: instead of
asking an interpreter to reproduce text from memory, it will cite a
LOCATION (`segment_id`) and the system will mechanically fetch the real
text at that location. This script builds those addressable locations. It
does NOT fix the interpreter or re-run the spike.

Does NOT modify `data/chapter_index_bphs.json` or any book JSON. Makes no
LLM/API/embedding call -- pure local text/offset processing. Writes exactly
two things: this artifact (only if every mandatory validation check passes)
and `diagnostics/latest_run.md` (always, overwrite mode, per the project's
diagnostic-output convention). If validation fails, `diagnostics/latest_run.md`
explains exactly what failed and the artifact is NOT written.

ARCHITECTURE (book-agnostic by design -- see CLAUDE.md's "keep this
book-agnostic" instruction for this task):

  select_strategy(text, marker_detector)
      Generic strategy-selection: given a unit's text and a PLUGGABLE
      marker-detection function, decides "sloka" vs "paragraph" purely by
      how many markers the detector finds and how densely. Contains NO
      book-specific regex of its own.

  detect_bphs_sloka_markers(text)
      The ONLY book-specific piece. Detects BPHS's own two sloka-number
      marker conventions (Devanagari end-of-verse `॥<digits>॥`, and the
      Arabic leading-number that opens the English translation paragraph,
      sometimes as a combined range like "11-12."). A future book with a
      different structure (numbered topics, no numbering at all, etc.)
      plugs in its own detector here and calls the same generic
      `segment_by_sloka_markers` / `select_strategy` machinery -- nothing
      else in this file would need to change.

  segment_by_sloka_markers(text, markers) / segment_by_paragraph(text)
      Generic segmenters, given already-detected markers (or none, for the
      paragraph fallback). Neither knows anything about BPHS.

MARKER RECONCILIATION (BPHS-specific finding, see report for full detail):
Devanagari verse-end markers are used as the SOLE driver of both segment
BOUNDARIES and segment NUMBERING. Arabic leading-numbers are detected too
(and their presence is reported as corroborating evidence for the
strategy choice) but are deliberately NOT used to assign segment_number,
because they routinely span COMBINED multi-verse ranges printed as one
translation paragraph (e.g. "11-12.", "2-7.", "8-10.", "94-99." were all
observed in these three chapters) which do not map to a single int the
way an individual Devanagari end-of-verse marker does. Devanagari markers
are themselves not immune to OCR corruption (a real case was found: sloka
12's marker was corrupted past recognition while its Arabic-side "11-12."
sibling survived) -- when that happens the verse is silently absorbed into
the segment of whichever neighbouring marker WAS detected, and the result
surfaces honestly as a reported monotonicity break, never a silent fix.
"""

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = REPO_ROOT / "data" / "chapter_index_bphs.json"
OUTPUT_PATH = REPO_ROOT / "data" / "segment_index_bphs_career3.json"
DIAG_PATH = REPO_ROOT / "diagnostics" / "latest_run.md"

TARGET_UNIT_IDS = ["bphs1_ch21", "bphs1_ch24", "bphs1_ch34"]

# v2: bump this string whenever the splitting logic itself changes (marker
# detection, boundary rules, drop-filtering). Recorded on every artifact so
# a downstream consumer can detect "this index was built by different
# segmentation logic than the one I validated against" without re-diffing.
SEGMENTER_VERSION = "seg-1.0"

# v2: keywords for the Change-3 mechanical audit of bphs1_ch34 (the alleged
# angular-lord/trinal-lord "Raja Yoga" claim). Case-insensitive substring
# match against each segment's raw text (Devanagari script cannot contain
# these Latin substrings, so no separate English-only extraction is needed).
RAJA_YOGA_AUDIT_KEYWORDS = [
    "angle", "angular", "trine", "trinal", "kendra", "trikona", "raja", "rajayoga", "yoga",
]

# ---------------------------------------------------------------------------
# Threshold discipline (Working Style #4): a unit qualifies for the "sloka"
# strategy if the BPHS marker detector finds at least MIN_MARKERS_IN_WINDOW
# markers within the first EVIDENCE_WINDOW_CHARS characters (or the whole
# unit, if shorter) AND at least MIN_MARKERS_TOTAL markers across the whole
# unit. Rationale: one marker could be an incidental digit-period match;
# two or more within a short window is reasonably strong evidence of a
# systematic verse-numbering convention, not noise. SCOPE GUARD: this
# threshold governs strategy SELECTION only, never segment boundaries.
# TUNING NOTE: all three target units clear this by a wide margin (13-98
# markers detected per unit); revisit only if a future book's own detector
# produces a genuinely borderline count.
# ---------------------------------------------------------------------------
EVIDENCE_WINDOW_CHARS = 5000
MIN_MARKERS_IN_WINDOW = 2
MIN_MARKERS_TOTAL = 3

DEVANAGARI_DIGIT_TRANS = str.maketrans("०१२३४५६७८९", "0123456789")
DEVANAGARI_BLOCK_RE = re.compile(r"[ऀ-ॿ]")
ENGLISH_RUN_RE = re.compile(r"[A-Za-z]{3,}")
BLANK_LINE_RE = re.compile(r"\n[ \t]*\n")

# BPHS-specific marker regexes (kept local to the BPHS detector function).
_BPHS_DEVANAGARI_MARKER_RE = re.compile(r"[।॥]\s*([०-९]+)\s*[।॥]")
_BPHS_ARABIC_MARKER_RE = re.compile(
    r"(?:\A|\n[ \t]*\n)\s*(\d{1,3})(?:[-–](\d{1,3}))?\.\s+(?=[A-Z\"'])"
)


# ---------------------------------------------------------------------------
# Book-specific marker detection (BPHS only -- the pluggable piece)
# ---------------------------------------------------------------------------
def detect_bphs_sloka_markers(text):
    """Detect BPHS's Devanagari end-of-verse markers.

    Returns a list of dicts, one per detected marker, in text order:
      {"start": int, "end": int, "number": int}
    `start`/`end` bound the marker text itself (e.g. "॥११२॥"); `number` is
    the Devanagari digit group translated to an int. This is the sole
    marker form used for BOUNDARIES and NUMBERING (see module docstring).
    """
    markers = []
    for m in _BPHS_DEVANAGARI_MARKER_RE.finditer(text):
        try:
            number = int(m.group(1).translate(DEVANAGARI_DIGIT_TRANS))
        except ValueError:
            continue
        markers.append({"start": m.start(), "end": m.end(), "number": number})
    return markers


def detect_bphs_arabic_markers(text):
    """Detect BPHS's Arabic leading-number markers (paragraph-initial).

    Returns a list of (start, first_number, second_number_or_None) tuples.
    Used ONLY as corroborating evidence for strategy selection and for the
    report's reconciliation narrative -- never for segment numbering (see
    module docstring for why: combined ranges like "11-12." don't map to
    a single int the way a Devanagari marker does).
    """
    out = []
    for m in _BPHS_ARABIC_MARKER_RE.finditer(text):
        n1 = int(m.group(1))
        n2 = int(m.group(2)) if m.group(2) else None
        out.append((m.start(), n1, n2))
    return out


# ---------------------------------------------------------------------------
# Generic strategy selection (book-agnostic)
# ---------------------------------------------------------------------------
def select_strategy(text, marker_detector):
    """Decide 'sloka' vs 'paragraph' for a unit's text.

    `marker_detector` is any callable(text) -> list of {"start","end","number"}
    dicts (see detect_bphs_sloka_markers for the BPHS implementation). This
    function itself knows nothing about what a marker looks like -- only
    how many were found and how densely -- so a future book supplies its
    own detector without touching this logic.
    """
    markers = marker_detector(text)
    window = text[:EVIDENCE_WINDOW_CHARS]
    window_markers = marker_detector(window)
    evidence = {
        "markers_in_first_%d_chars" % EVIDENCE_WINDOW_CHARS: len(window_markers),
        "markers_total": len(markers),
    }
    if len(window_markers) >= MIN_MARKERS_IN_WINDOW and len(markers) >= MIN_MARKERS_TOTAL:
        return "sloka", markers, evidence
    return "paragraph", [], evidence


# ---------------------------------------------------------------------------
# Generic segmenters (book-agnostic)
# ---------------------------------------------------------------------------
def _paragraph_starts(text):
    starts = [0]
    for m in BLANK_LINE_RE.finditer(text):
        starts.append(m.end())
    return starts


def segment_by_sloka_markers(text, markers):
    """Build sloka-scheme segments from a marker list (start/end/number),
    already sorted in text order.

    Segment boundaries: for marker i (1-indexed among KEPT markers), the
    segment starts where marker i's own Sanskrit-verse PARAGRAPH begins
    (the nearest preceding blank-line boundary) and ends where the NEXT
    kept marker's own verse-paragraph begins (or at end-of-text for the
    last marker). The first segment's start is forced to 0 so any leading
    spillover content is folded in rather than left as an uncovered gap.
    This means each segment holds: [previous marker's translation+notes
    tail is NOT included -- see reconciliation note] its OWN verse's
    Sanskrit, plus its own English translation and notes, up to the point
    the next verse begins.

    Markers whose computed verse-paragraph-start does not advance past the
    previous KEPT marker's (i.e. two or more markers land in the same
    un-blank-line-separated Sanskrit block, a real pattern observed in
    ch.34) are DROPPED -- they would otherwise produce a zero-length,
    content-free segment. The content is not lost: it is absorbed into the
    next marker that DOES advance. Returns (segments, dropped_marker_numbers).
    """
    if not markers:
        return [], []

    para_starts = _paragraph_starts(text)

    def verse_start_for(pos):
        # nearest paragraph start at or before `pos`
        lo, hi = 0, len(para_starts) - 1
        best = para_starts[0]
        for p in para_starts:
            if p <= pos:
                best = p
            else:
                break
        return best

    kept = []
    dropped = []
    last_vs = None
    for mk in markers:
        vs = verse_start_for(mk["start"])
        if last_vs is not None and vs <= last_vs:
            dropped.append(mk["number"])
            continue
        kept.append({"number": mk["number"], "verse_start": vs})
        last_vs = vs

    if not kept:
        return [], [m["number"] for m in markers]

    segments = []
    for i, mk in enumerate(kept):
        start = 0 if i == 0 else kept[i]["verse_start"]
        end = kept[i + 1]["verse_start"] if i + 1 < len(kept) else len(text)
        segments.append({"segment_number": mk["number"], "start_char": start, "end_char": end})

    return segments, dropped


def segment_by_paragraph(text):
    """Build paragraph-scheme segments (fallback strategy), numbered
    ordinally from 1. Each segment's span includes its own trailing
    blank-line separator so consecutive segments are exactly contiguous
    (no interior gap is ever dropped).
    """
    cut_points = [0]
    for m in BLANK_LINE_RE.finditer(text):
        cut_points.append(m.end())
    if cut_points[-1] != len(text):
        cut_points.append(len(text))
    segments = []
    n = 1
    for i in range(len(cut_points) - 1):
        start, end = cut_points[i], cut_points[i + 1]
        if start == end:
            continue
        segments.append({"segment_number": n, "start_char": start, "end_char": end})
        n += 1
    return segments


# ---------------------------------------------------------------------------
# Field assembly
# ---------------------------------------------------------------------------
def has_devanagari(s):
    return bool(DEVANAGARI_BLOCK_RE.search(s))


def has_english(s):
    return bool(ENGLISH_RUN_RE.search(s))


def citation_label(book, chapter_number, scheme, segment_number):
    kind = "sloka" if scheme == "sloka" else "para"
    return "BPHS Ch.%s, %s %d" % (chapter_number, kind, segment_number)


def build_unit_segments(unit, scheme, raw_segments):
    text = unit["text"]
    unit_id = unit["unit_id"]
    book = unit["book"]
    chapter_number = unit["chapter_number"]
    prefix = "s" if scheme == "sloka" else "p"

    used_numbers = {}
    out = []
    for ordinal, seg in enumerate(raw_segments, start=1):
        n = seg["segment_number"]
        start, end = seg["start_char"], seg["end_char"]
        span_text = text[start:end]
        count = used_numbers.get(n, 0)
        used_numbers[n] = count + 1
        # v2: ordinal position is now the citation key; segment_id is
        # "{unit_id}#{ordinal}". The old sloka-number-based id form
        # (prefix + segment_number + a/b/c suffix for repeats) is retired.
        segment_id = "%s#%d" % (unit_id, ordinal)
        # v2: the OCR-detected printed number, kept as metadata only. Never
        # used to address a segment -- printed numbers are unreliable
        # (ghost values, repeats) per the module's own reconciliation note.
        printed_sloka_number = n if scheme == "sloka" else None
        out.append(
            {
                "segment_id": segment_id,
                "ordinal": ordinal,
                "printed_sloka_number": printed_sloka_number,
                "unit_id": unit_id,
                "book": book,
                "chapter_number": chapter_number,
                "scheme": scheme,
                "segment_number": n,
                "start_char": start,
                "end_char": end,
                "text": span_text,
                "char_count": len(span_text),
                "has_devanagari": has_devanagari(span_text),
                "has_english": has_english(span_text),
                "citation_label": citation_label(book, chapter_number, scheme, n),
                # v2: hash of this segment's exact text, so a future silent
                # edit to the underlying book text is DETECTABLE (hash
                # mismatch) rather than resolving quietly to the wrong verse.
                "text_sha256": hashlib.sha256(span_text.encode("utf-8")).hexdigest(),
            }
        )
    return out


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate_contiguous_and_coverage(unit_id, unit_text, segments):
    """Checks 1 and 2 combined per unit. Returns a dict of measurements."""
    ordered = sorted(segments, key=lambda s: s["start_char"])
    gaps_or_overlaps = []
    for i in range(len(ordered) - 1):
        a, b = ordered[i], ordered[i + 1]
        if a["end_char"] != b["start_char"]:
            gaps_or_overlaps.append((a["segment_id"], a["end_char"], b["segment_id"], b["start_char"]))
    leading_gap = ordered[0]["start_char"] - 0 if ordered else None
    trailing_gap = len(unit_text) - ordered[-1]["end_char"] if ordered else None
    concatenated = "".join(unit_text[s["start_char"]:s["end_char"]] for s in ordered)
    covered_text = unit_text[ordered[0]["start_char"]:ordered[-1]["end_char"]] if ordered else ""
    delta = len(concatenated) - len(covered_text)
    exact_match = concatenated == covered_text
    return {
        "segment_count": len(ordered),
        "interior_gaps_or_overlaps": gaps_or_overlaps,
        "leading_gap_chars": leading_gap,
        "trailing_gap_chars": trailing_gap,
        "concatenation_delta_chars": delta,
        "concatenation_exact_match": exact_match,
    }


def compute_monotonicity_breaks(segments_in_position_order):
    numbers = [s["segment_number"] for s in segments_in_position_order]
    breaks = []
    for i in range(len(numbers) - 1):
        if numbers[i + 1] != numbers[i] + 1:
            breaks.append((numbers[i], numbers[i + 1]))
    return breaks


# ---------------------------------------------------------------------------
# Report writer
# ---------------------------------------------------------------------------
def write_report(lines):
    DIAG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DIAG_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def median(vals):
    s = sorted(vals)
    n = len(s)
    if n == 0:
        return None
    mid = n // 2
    if n % 2 == 1:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    report = []
    report.append("# build_segment_index.py -- latest run")
    report.append("")
    report.append("Input: `data/chapter_index_bphs.json`")
    report.append("Target units: %s" % ", ".join(TARGET_UNIT_IDS))
    report.append("")

    report.append("## Prediction (stated before running the final build)")
    report.append("")
    report.append(
        "Based on the calibration scan run against real text from these three "
        "units before finalizing the segmentation code (raw devanagari-marker "
        "regex counts, no drop-filtering applied yet at scan time):"
    )
    report.append("")
    report.append("| unit_id | predicted segment count (raw marker count) | predicted monotonicity breaks (raw) |")
    report.append("|---|---|---|")
    report.append("| bphs1_ch21 | 14 | 6 |")
    report.append("| bphs1_ch24 | 98 | 48 |")
    report.append("| bphs1_ch34 | 33 | 15 |")
    report.append("")
    report.append(
        "These raw-marker predictions will differ slightly from the actual "
        "shipped segment counts below, because the final segmenter DROPS any "
        "marker whose verse-paragraph start does not advance past the "
        "previous kept marker's (multiple verses sharing one un-blank-line-"
        "separated Sanskrit block, a real pattern found in ch.34 slokas "
        "2/3/5) -- those verses are absorbed into the next marker that does "
        "advance rather than producing empty segments. Any such deviation "
        "is called out explicitly below, not silently absorbed into the "
        "narrative."
    )
    report.append("")

    if not INPUT_PATH.exists():
        report.append("## FAILURE")
        report.append("")
        report.append("Input file `%s` does not exist." % INPUT_PATH)
        write_report(report)
        return

    with open(INPUT_PATH, encoding="utf-8") as f:
        data = json.load(f)
    units_by_id = {u["unit_id"]: u for u in data.get("units", [])}

    # v2 drift-protection header fields (see module docstring / report for
    # the one-line "why" on each).
    source_index_sha256 = hashlib.sha256(INPUT_PATH.read_bytes()).hexdigest()
    generated_at = datetime.now(timezone.utc).isoformat()

    missing = [uid for uid in TARGET_UNIT_IDS if uid not in units_by_id]
    if missing:
        report.append("## FAILURE")
        report.append("")
        report.append("Target unit_id(s) not found in input file: %s" % missing)
        write_report(report)
        return

    all_segments = []
    per_unit_info = {}
    validation_rows = []
    all_failed = False

    strategy_evidence_rows = []

    for uid in TARGET_UNIT_IDS:
        unit = units_by_id[uid]
        text = unit["text"]

        strategy, markers, evidence = select_strategy(text, detect_bphs_sloka_markers)
        arabic_markers = detect_bphs_arabic_markers(text)

        strategy_evidence_rows.append(
            (uid, strategy, evidence, len(markers), len(arabic_markers))
        )

        if strategy == "sloka":
            raw_segments, dropped = segment_by_sloka_markers(text, markers)
        else:
            raw_segments, dropped = segment_by_paragraph(text), []

        segments = build_unit_segments(unit, strategy, raw_segments)
        all_segments.extend(segments)

        cov = validate_contiguous_and_coverage(uid, text, segments)
        ordered = sorted(segments, key=lambda s: s["start_char"])
        breaks = compute_monotonicity_breaks(ordered) if strategy == "sloka" else []

        sizes = [s["char_count"] for s in segments]
        dev_only = sum(1 for s in segments if s["has_devanagari"] and not s["has_english"])

        per_unit_info[uid] = {
            "unit": unit,
            "strategy": strategy,
            "segments": segments,
            "ordered": ordered,
            "coverage": cov,
            "breaks": breaks,
            "dropped_markers": dropped,
            "sizes": sizes,
            "dev_only_count": dev_only,
            "raw_marker_count": len(markers),
            "arabic_marker_count": len(arabic_markers),
        }

        # per-unit hard-gate checks (1: contiguity, 2: coverage)
        check1_pass = len(cov["interior_gaps_or_overlaps"]) == 0
        check2_pass = cov["concatenation_exact_match"] and cov["concatenation_delta_chars"] == 0
        validation_rows.append((uid, "1_contiguous_non_overlapping", check1_pass, cov))
        validation_rows.append((uid, "2_full_coverage_reproduction", check2_pass, cov))
        if not check1_pass or not check2_pass:
            all_failed = True

    # check 3: global uniqueness across all 3 units
    all_ids = [s["segment_id"] for s in all_segments]
    dup_ids = sorted({sid for sid in all_ids if all_ids.count(sid) > 1})
    check3_pass = len(dup_ids) == 0
    if not check3_pass:
        all_failed = True

    # check 4 (v2): ordinal runs 1..N with no gaps, per unit
    check4_rows = []
    for uid in TARGET_UNIT_IDS:
        segs = per_unit_info[uid]["segments"]
        ordinals = [s["ordinal"] for s in segs]
        expected = list(range(1, len(segs) + 1))
        ok = ordinals == expected
        check4_rows.append((uid, ok, len(segs)))
        if not ok:
            all_failed = True

    # check 5 (v2): every segment has a non-empty text_sha256
    missing_sha = [s["segment_id"] for s in all_segments if not s.get("text_sha256")]
    check5_pass = len(missing_sha) == 0
    if not check5_pass:
        all_failed = True

    if all_failed:
        report.append("## VALIDATION FAILED -- artifact NOT written")
        report.append("")
        for uid, name, ok, cov in validation_rows:
            if not ok:
                report.append("- FAIL `%s` on `%s`: %s" % (name, uid, cov))
        if not check3_pass:
            report.append("- FAIL `3_global_unique_ids`: duplicate segment_id(s): %s" % dup_ids)
        for uid, ok, n in check4_rows:
            if not ok:
                report.append("- FAIL `4_ordinal_no_gaps` on `%s`: ordinals not exactly 1..%d" % (uid, n))
        if not check5_pass:
            report.append("- FAIL `5_text_sha256_present`: segment(s) with empty/missing text_sha256: %s" % missing_sha)
        write_report(report)
        return

    # ---- All hard gates passed. Build the rest of the report + write artifact. ----

    report.append("## Segmentation strategy per unit")
    report.append("")
    report.append("| unit_id | strategy chosen | devanagari markers (first %d chars / total) | arabic markers (total, informational only) |" % EVIDENCE_WINDOW_CHARS)
    report.append("|---|---|---|---|")
    for uid, strategy, evidence, total_dev, total_ar in strategy_evidence_rows:
        win_key = "markers_in_first_%d_chars" % EVIDENCE_WINDOW_CHARS
        report.append(
            "| %s | %s | %d / %d | %d |"
            % (uid, strategy, evidence[win_key], evidence["markers_total"], total_ar)
        )
    report.append("")
    report.append(
        "Marker-form reconciliation (same for all three units): BOTH marker "
        "forms are present (Devanagari end-of-verse `॥<digits>॥`, and an "
        "Arabic leading-number that opens each verse's English translation, "
        "sometimes as a combined range printed for several verses at once, "
        "e.g. `11-12.`, `2-7.`, `8-10.`, `94-99.` -- all four observed live "
        "in these three chapters). Segmentation is keyed on the DEVANAGARI "
        "form ONLY, for both boundaries and segment_number. Reasons: (1) "
        "Arabic markers routinely bundle several verses into one combined-"
        "range translation paragraph, which cannot map to a single "
        "`segment_number` int the way one Devanagari end-of-verse marker "
        "always does; and (2) a real case of the opposite failure was also "
        "found and would corrupt an Arabic-driven scheme in a different "
        "way -- English commentary ('Notes:') sections themselves contain "
        "numbered sub-points in the identical 'N. Text' format as a genuine "
        "verse translation (e.g. ch.34's Notes on slokas 2-7 contain "
        "'1. Kendradhipatya Dosha :', '2. Malefic as owner of angle :', "
        "etc., immediately after the real combined '2-7.' translation), "
        "which a naive global Arabic-marker scan cannot distinguish from a "
        "genuine sloka number. Devanagari markers never appear inside "
        "English Notes prose, so this confound cannot occur for them. When "
        "a Devanagari marker is itself OCR-corrupted past recognition "
        "(confirmed for ch.24 sloka 12 -- its `॥१२॥` marker OCR'd as "
        "unreadable garbage while its Arabic-side `11-12.` sibling survived "
        "intact), that verse is absorbed into the segment of the nearest "
        "detected neighbour and the resulting gap surfaces honestly as a "
        "reported monotonicity break (see below), never silently patched."
    )
    report.append("")

    report.append("## Validation results")
    report.append("")
    report.append("| unit_id | check | result | measured |")
    report.append("|---|---|---|---|")
    for uid in TARGET_UNIT_IDS:
        info = per_unit_info[uid]
        cov = info["coverage"]
        report.append(
            "| %s | 1_contiguous_non_overlapping | PASS | interior gaps/overlaps: %d |"
            % (uid, len(cov["interior_gaps_or_overlaps"]))
        )
        report.append(
            "| %s | 2_full_coverage_reproduction | PASS | leading_gap=%d chars, trailing_gap=%d chars, concatenation_delta=%d chars, exact_match=%s |"
            % (uid, cov["leading_gap_chars"], cov["trailing_gap_chars"], cov["concatenation_delta_chars"], cov["concatenation_exact_match"])
        )
    report.append(
        "| (all 3 combined) | 3_global_unique_ids | PASS | %d segment_ids total, 0 duplicates |"
        % len(all_ids)
    )
    for uid, ok, n in check4_rows:
        report.append(
            "| %s | 4_ordinal_no_gaps | %s | ordinal runs 1..%d, no gaps |"
            % (uid, "PASS" if ok else "FAIL", n)
        )
    report.append(
        "| (all 3 combined) | 5_text_sha256_present | %s | %d/%d segments have a non-empty text_sha256 |"
        % ("PASS" if check5_pass else "FAIL", len(all_segments) - len(missing_sha), len(all_segments))
    )
    for uid in TARGET_UNIT_IDS:
        info = per_unit_info[uid]
        if info["strategy"] == "sloka":
            report.append(
                "| %s | sloka_monotonicity (informational, not gated, unrelated to check 4 above) | PASS (reported, not gated -- see breaks below) | %d breaks out of %d segments |"
                % (uid, len(info["breaks"]), len(info["segments"]))
            )
        else:
            report.append("| %s | sloka_monotonicity (informational, not gated) | N/A (paragraph scheme) | -- |" % uid)
    report.append("")
    report.append(
        "Note on sloka_monotonicity: per the task spec, a monotonicity break is "
        "EVIDENCE of OCR damage to be reported honestly, not a fix target "
        "and not an artifact-blocking failure -- 'PASS' above means the "
        "detection+reporting itself succeeded, not that zero breaks exist."
    )
    report.append("")

    report.append("## Sloka-sequence breaks (check 4 detail)")
    report.append("")
    any_breaks = False
    for uid in TARGET_UNIT_IDS:
        info = per_unit_info[uid]
        if info["strategy"] != "sloka":
            continue
        report.append("### %s (%d breaks)" % (uid, len(info["breaks"])))
        if not info["breaks"]:
            report.append("- none")
        else:
            any_breaks = True
            for a, b in info["breaks"]:
                report.append("- after sloka %d, next detected sloka number is %d" % (a, b))
        if info["dropped_markers"]:
            report.append(
                "- dropped markers (verse shared a paragraph with an earlier "
                "kept marker, no blank-line separation between them -- "
                "content absorbed into the next marker that DID advance, "
                "not lost): %s" % info["dropped_markers"]
            )
        report.append("")
    if not any_breaks:
        report.append("(zero breaks across all sloka-scheme units)")
        report.append("")

    report.append("## Deviation from prediction")
    report.append("")
    pred_counts = {"bphs1_ch21": (14, 6), "bphs1_ch24": (98, 48), "bphs1_ch34": (33, 15)}
    for uid in TARGET_UNIT_IDS:
        info = per_unit_info[uid]
        pred_n, pred_breaks = pred_counts[uid]
        actual_n = len(info["segments"])
        actual_breaks = len(info["breaks"])
        n_note = "" if actual_n == pred_n else " <-- DEVIATES (raw marker count was %d, %d dropped as zero-length)" % (info["raw_marker_count"], len(info["dropped_markers"]))
        b_note = "" if actual_breaks == pred_breaks else " <-- DEVIATES"
        report.append(
            "- %s: predicted %d segments / %d breaks -> actual %d segments%s / %d breaks%s"
            % (uid, pred_n, pred_breaks, actual_n, n_note, actual_breaks, b_note)
        )
    report.append("")

    report.append("## Segment size distribution per unit (char_count)")
    report.append("")
    report.append("| unit_id | count | min | median | max |")
    report.append("|---|---|---|---|---|")
    for uid in TARGET_UNIT_IDS:
        info = per_unit_info[uid]
        sizes = info["sizes"]
        report.append(
            "| %s | %d | %d | %s | %d |"
            % (uid, len(sizes), min(sizes) if sizes else 0, median(sizes), max(sizes) if sizes else 0)
        )
    report.append("")

    report.append("## Devanagari-only, no-English segments (uncitable for an English answer)")
    report.append("")
    report.append("| unit_id | count |")
    report.append("|---|---|")
    total_dev_only = 0
    for uid in TARGET_UNIT_IDS:
        info = per_unit_info[uid]
        total_dev_only += info["dev_only_count"]
        report.append("| %s | %d |" % (uid, info["dev_only_count"]))
    report.append("| **total** | **%d** |" % total_dev_only)
    report.append("")
    report.append(
        "has_english heuristic: a run of 3+ consecutive ASCII letters "
        "(`[A-Za-z]{3,}`) anywhere in the segment text. has_devanagari: any "
        "character in the Devanagari Unicode block (U+0900-U+097F)."
    )
    report.append("")

    # ---- Targeted spot checks ----
    report.append("## Targeted spot checks")
    report.append("")

    ch24_segs = {s["segment_number"]: s for s in per_unit_info["bphs1_ch24"]["segments"] if s["scheme"] == "sloka"}

    report.append("### (a) bphs1_ch24 sloka 112 -- expected: '10th lord in the 4th house' rule")
    report.append("")
    if 112 in ch24_segs:
        report.append("segment_id: `%s`" % ch24_segs[112]["segment_id"])
        report.append("")
        report.append("```")
        report.append(ch24_segs[112]["text"])
        report.append("```")
    else:
        report.append("MISMATCH: no segment_number=112 found in bphs1_ch24's sloka segments.")
    report.append("")

    report.append("### (b) bphs1_ch24 slokas 50, 51, 52 -- prior spike's alleged '5th lord in 2nd house' area")
    report.append("")
    for n in (50, 51, 52):
        report.append("**sloka %d**" % n)
        if n in ch24_segs:
            report.append("segment_id: `%s`" % ch24_segs[n]["segment_id"])
            report.append("")
            report.append("```")
            report.append(ch24_segs[n]["text"])
            report.append("```")
        else:
            report.append("(no segment_number=%d found)" % n)
        report.append("")

    report.append("### (c) Change 3 audit -- bphs1_ch34, exhaustive keyword walk (Raja Yoga question)")
    report.append("")
    report.append(
        "Prior spike claim under review: an angular lord and a trinal lord "
        "joining together produces a yoga making the native a king. The "
        "verifier that reported this as 'unmatched' used an unreliable "
        "closest-source-text finder (it wrongly pointed a correct sloka-50 "
        "quote at sloka 51 elsewhere) -- that finder is NOT trusted here. "
        "This is instead a mechanical, exhaustive, unjudged walk of every "
        "segment in bphs1_ch34, in ordinal order, printed verbatim for "
        "human review."
    )
    report.append("")
    report.append(
        "Keyword list (case-insensitive substring match against each "
        "segment's raw text): %s" % ", ".join("`%s`" % k for k in RAJA_YOGA_AUDIT_KEYWORDS)
    )
    report.append("")
    ch34_ordered = sorted(per_unit_info["bphs1_ch34"]["segments"], key=lambda s: s["ordinal"])
    ch34_hits = []
    ch34_misses = []
    for s in ch34_ordered:
        low = s["text"].lower()
        matched = [kw for kw in RAJA_YOGA_AUDIT_KEYWORDS if kw in low]
        if matched:
            ch34_hits.append((s, matched))
        else:
            ch34_misses.append(s)
    for s, matched in ch34_hits:
        report.append(
            "**segment_id: `%s`** (ordinal %d, printed_sloka_number=%s) -- matched: %s"
            % (s["segment_id"], s["ordinal"], s["printed_sloka_number"], ", ".join(matched))
        )
        report.append("")
        report.append("```")
        report.append(s["text"])
        report.append("```")
        report.append("")
    report.append(
        "**Summary: %d of %d bphs1_ch34 segments matched; %d did not.**"
        % (len(ch34_hits), len(ch34_ordered), len(ch34_misses))
    )
    report.append("")
    if ch34_misses:
        report.append("Non-matching segment_ids: %s" % ", ".join(s["segment_id"] for s in ch34_misses))
    else:
        report.append("Non-matching segment_ids: (none -- every segment matched)")
    report.append("")

    # ---- Known leading-spillover callouts (measured, not asserted) ----
    report.append("## Leading-segment spillover callout")
    report.append("")
    report.append(
        "Each unit's segment 1 starts at character 0 by construction (any "
        "content before the first detected marker is folded in rather than "
        "left as an uncovered gap -- see check 2). For all three units the "
        "very first detected Devanagari number is implausibly large/out of "
        "chapter-start sequence, consistent with leading spillover from the "
        "PRECEDING chapter's tail (already present in the input unit's own "
        "`text` field, not altered here). Printed verbatim below for human "
        "judgment, not corrected:"
    )
    report.append("")
    for uid in TARGET_UNIT_IDS:
        info = per_unit_info[uid]
        if info["strategy"] != "sloka" or not info["ordered"]:
            continue
        first = info["ordered"][0]
        preview = first["text"][:300].replace("\n", "\\n")
        report.append("- `%s` first segment `%s` (segment_number=%d, %d chars) starts: `%s...`" % (uid, first["segment_id"], first["segment_number"], first["char_count"], preview))
    report.append("")

    report.append("## Ordinal is now the primary address (Change 1)")
    report.append("")
    report.append(
        "`ordinal` (1..N, position within its unit) is the citation key from "
        "now on. `segment_id` is rewritten to `{unit_id}#{ordinal}`, e.g. "
        "`bphs1_ch24#87`. The old sloka-number-based id form is retired. "
        "`printed_sloka_number` (the OCR-detected printed number) is kept "
        "as metadata only and is never used to address a segment."
    )
    report.append("")
    report.append("| unit_id | ordinal range (confirmed) | segment count |")
    report.append("|---|---|---|")
    for uid in TARGET_UNIT_IDS:
        segs = per_unit_info[uid]["segments"]
        ords = sorted(s["ordinal"] for s in segs)
        report.append(
            "| %s | %d..%d | %d |" % (uid, ords[0], ords[-1], len(segs))
        )
    report.append("")

    report.append("## Drift protection (Change 2) -- why each field exists")
    report.append("")
    report.append("| field | why it exists |")
    report.append("|---|---|")
    report.append("| `text_sha256` (per segment) | detects a silent future edit to this exact segment's text, so a stale citation resolves loudly (hash mismatch) instead of quietly pointing at the wrong verse |")
    report.append("| `index_version` (header) | lets a downstream consumer refuse or branch on an index shape it doesn't understand yet, instead of guessing |")
    report.append("| `generated_at` (header) | timestamps this exact build, so staleness can be judged without re-deriving it from file mtimes |")
    report.append("| `source_index_sha256` (header) | detects a silent change to the underlying `data/chapter_index_bphs.json` input, so a rebuild-needed condition is loud rather than assumed |")
    report.append("| `segmenter_version` (header) | detects that this index was produced by different splitting logic than a consumer last validated against, without diffing code |")
    report.append("")
    report.append("Header values this run: `index_version=v2`, `generated_at=%s`, `source_index_sha256=%s`, `segmenter_version=%s`" % (generated_at, source_index_sha256, SEGMENTER_VERSION))
    report.append("")

    header_only = {
        "source_file": "data/chapter_index_bphs.json",
        "generated_by": "scripts/build_segment_index.py",
        "index_version": "v2",
        "generated_at": generated_at,
        "source_index_sha256": source_index_sha256,
        "segmenter_version": SEGMENTER_VERSION,
        "units_processed": TARGET_UNIT_IDS,
        "segment_count": len(all_segments),
    }
    report.append("## New artifact header, verbatim (`segments` array omitted here, see below for samples)")
    report.append("")
    report.append("```json")
    report.append(json.dumps(header_only, ensure_ascii=False, indent=2))
    report.append("```")
    report.append("")

    report.append("## Three sample segment records in full (showing new fields)")
    report.append("")
    sample_lookup = {"bphs1_ch21": 1, "bphs1_ch24": 87, "bphs1_ch34": 3}
    for uid, want_ordinal in sample_lookup.items():
        seg = next(s for s in per_unit_info[uid]["segments"] if s["ordinal"] == want_ordinal)
        report.append("### `%s` (ordinal %d)" % (uid, want_ordinal))
        report.append("")
        report.append("```json")
        report.append(json.dumps(seg, ensure_ascii=False, indent=2))
        report.append("```")
        report.append("")

    report.append("## Output artifact")
    report.append("")
    report.append("Written: `data/segment_index_bphs_career3.json`")
    report.append(
        "Shape: `{\"source_file\": ..., \"generated_by\": ..., \"index_version\": \"v2\", "
        "\"generated_at\": ..., \"source_index_sha256\": ..., \"segmenter_version\": ..., "
        "\"units_processed\": [...], \"segment_count\": N, \"segments\": [...]}`"
    )
    report.append("Total segments across all 3 units: %d" % len(all_segments))
    report.append("")

    write_report(report)

    output = {
        "source_file": "data/chapter_index_bphs.json",
        "generated_by": "scripts/build_segment_index.py",
        "index_version": "v2",
        "generated_at": generated_at,
        "source_index_sha256": source_index_sha256,
        "segmenter_version": SEGMENTER_VERSION,
        "units_processed": TARGET_UNIT_IDS,
        "segment_count": len(all_segments),
        "segments": all_segments,
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
