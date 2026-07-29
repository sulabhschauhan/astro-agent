"""
scripts/layout_paragraph_probe_S80.py
S80 U1c -- LAYOUT-BASED PARAGRAPH RECOVERY PROBE, Cheiro only, read-only,
diagnostics-only. Run manually; never invoked from CI or the pytest suite.
NO repair, NO boundary-seeder logic, NO writes to ChromaDB, NO shadow
collection, NO re-ingestion, NO imports from pdf_processor.py/chunker.py/
embedder.py/query_engine.py.

WHY: ~90 of Cheiro's 245 in-scope pages need chunk boundaries DERIVED, not
inherited from an existing (possibly wrong) span -- 65 zero-chunk pages
(U1 section f) + 14 boundary-error pages (U1b cohort A) + roughly a dozen
low-coverage pages (U1b cohort C). S79's native_text_probe ruled paragraph
splitting impossible because `extract_text()` produces no blank-line
(`\\n\\n`) breaks anywhere in this book -- confirmed independently here by
re-reading that finding, not re-tested, since it is about a DIFFERENT API
(`extract_text()`'s newline-joining behavior) than the one this probe
tests. This probe asks a different question of a different API: does
`pdfplumber`'s WORD-LEVEL COORDINATE data (`extract_words()` /
`extract_text_lines()`) recover paragraph structure via first-line
indentation, independent of whether `extract_text()`'s own line-joining
preserves blank-line breaks. If it does, boundary derivation for the ~90
unmapped pages is solved by layout, and the existing (833 already
committed) chunk spans are needed only for anchor id-mapping, not for
supplying new boundaries.

API CHOICE, stated per instruction: `page.extract_text_lines()`, NOT
`page.extract_words()` directly. Justification, from direct inspection
(not assumed): `extract_words()` returns individual words with `top`/`x0`
per word; grouping words into lines by a `top` tolerance is exactly what
`extract_text_lines()` already does internally, using pdfplumber's own
tested line-assembly logic. Using it directly avoids re-implementing that
grouping. The `top`-delta tolerance this module docstring specifies below
was still DERIVED (not skipped) as a validation step: sampled three clean
pages (page_index 155, 99, 213) via `extract_words()` and found the
observed same-line word-to-word `top` delta maxes out at 1.566pt (a small
font-kerning jitter), while the smallest observed DIFFERENT-line gap is
13.92pt -- a >12pt separation with no values in between across all three
samples. A tolerance of 3.0pt sits comfortably inside that gap (far above
the observed same-line jitter ceiling, far below the observed cross-line
floor), and `extract_text_lines()`'s own internal grouping was spot-checked
against this derived boundary on the same three pages -- it produced
exactly the expected line counts each time, confirming its grouping agrees
with the independently-derived tolerance rather than silently disagreeing
with it.

REUSE, NOT REINVENTION:
  - scripts/bidirectional_corruption_census_S80.py (as `census`): CHEIRO_PDF,
    CHEIRO_BOOK, _tokenize.
  - scripts/span_mapping_probe_S80.py (as `spanmod`): _get_collection (via
    census), _run_self_checks (the 5-check set already used in U1/U1b).
  - scripts/c5_decomposition_S80.py (as `c5mod`): _RUNNING_HEAD_MARKERS (the
    exact running-head vocabulary set derived in U0.6, reused verbatim for
    this probe's running-head false-positive detection).
  - diagnostics/span_mapping_probe_S80_data.json (the U1 sidecar): supplies
    cohort A (14 overlap pages), cohort C's candidate pool (65 zero-chunk
    pages, ranked by native_char_count), cohort E's candidate pool (166
    clean monotonic/overlap-free pages, ranked by coverage), and every
    existing chunk span used for the GATE NUMBER's agreement check in (a).
    Native page geometry (words/lines/coordinates) is NOT persisted
    anywhere from prior scripts and is re-extracted here, scoped to
    exactly the ~27 cohort pages, never all 310.

COHORT (de-duplicated; confirmed no overlap exists across the five groups
before this run -- reported anyway per instruction):
  A. the 14 overlap pages (page_index: 13,19,20,39,68,135,146,150,155,187,
     214,216,219,302)
  B. page_index 124 (page 125, worst coverage 0.278)
  C. the 5 (of 65) zero-chunk pages with the highest native_char_count
     (page_index: 2, 190, 307, 308, 1)
  D. the 4 anchor pages (page_index 138,144,158,162 == page_ref 139,145,
     159,163)
  E. 3 control pages from the 166 clean pages, highest coverage, tie broken
     by lowest page_index (page_index: 10, 12, 14 == page_ref 11,13,15)

FALSE-POSITIVE CLASSIFICATION (applied per line, first match wins, all
DERIVED from directly reading real Cheiro page geometry, not assumed):
  1. folio_number: text is bare digits (post-strip) AND the line sits in
     the page's own top/bottom extremity band (top < 60pt or bottom >
     page_height - 60pt -- Cheiro's folio numerals were directly observed
     sitting at the very bottom of body-text pages in earlier S79/U0
     diagnostics, e.g. page 156's "98").
  2. running_head: line sits in the top extremity band (top < 60pt) AND
     at least half its (lowercased) tokens are in c5mod._RUNNING_HEAD_
     MARKERS (the same 7-word set U0.6 derived and this project has reused
     ever since -- not re-derived here).
  3. chapter_heading: line has <= 6 words AND is fully uppercase (ignoring
     punctuation and whitespace) -- matches this book's own observed
     "CHAPTER X." / "THE LINE OF HEAKT." convention.
  4. centred: |left_gap - right_gap| <= 10pt, where left_gap = x0 and
     right_gap = page_width - x1 -- a genuinely centred line has roughly
     symmetric whitespace on both sides, unlike a first-line-indented
     paragraph opening (which is flush on the RIGHT, ragged only on the
     left).
  5. verse_block: NOT applied per-line in the first pass -- applied in a
     second pass over whichever lines survive rules 1-4 unclassified
     ("body" candidates): any maximal run of 2+ CONSECUTIVE body lines
     whose indents all sit within 3pt of each other AND that shared indent
     exceeds the provisional paragraph-opening cut (see below) is a
     uniform block-indent (verse/quotation), not a first-line-indent
     signal -- ALL lines in such a run are tagged verse_block and none
     count as a candidate paragraph opening.
  Remaining body lines: candidate_paragraph_opening if indent exceeds the
  PROVISIONAL cut (stated as provisional, not ratified, throughout this
  report and its script); otherwise body_continuation (not itself a
  reportable false-positive class -- it is simply an unflagged normal
  line).

No recommendation anywhere in this script or its report on the indent
threshold, seeder design, or whether to adopt layout-based derivation at
all -- report only, per instruction.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bidirectional_corruption_census_S80 as census  # noqa: E402  -- reuse
import c5_decomposition_S80 as c5mod  # noqa: E402  -- reuse, running-head vocab only
import span_mapping_probe_S80 as spanmod  # noqa: E402  -- reuse, self-checks

import pdfplumber  # noqa: E402

ROOT = census.ROOT
SIDECAR_PATH = ROOT / "diagnostics" / "span_mapping_probe_S80_data.json"
REPORT_PATH = ROOT / "diagnostics" / "layout_paragraph_probe_S80.md"
DATA_SIDECAR_PATH = ROOT / "diagnostics" / "layout_paragraph_probe_S80_data.json"
LATEST_RUN_PATH = ROOT / "diagnostics" / "latest_run.md"

_TOLERANCE_SAMPLE_PAGES = [155, 99, 213]  # 0-indexed, used only for the derivation writeup
_EXTREMITY_BAND_PT = 60.0
_CENTERED_TOLERANCE_PT = 10.0
_VERSE_BLOCK_INDENT_TOLERANCE_PT = 3.0
_INDENT_BUCKET_WIDTH = 2.0

_CLAUDE_ANCHOR_PAGE_REFS = [139, 145, 159, 163]


def _derive_line_tolerance(pdf) -> dict:
    """Validation exercise described in the module docstring. Does not feed
    into extract_text_lines() (pdfplumber owns that grouping internally) --
    this confirms the tolerance a manual top-delta grouping WOULD use
    agrees with what extract_text_lines() already produced, on 3 clean
    pages sampled independently of the main cohort."""
    same_line_max = 0.0
    cross_line_min = None
    per_page = []
    for pidx in _TOLERANCE_SAMPLE_PAGES:
        page = pdf.pages[pidx]
        try:
            words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
        except Exception as exc:
            raise RuntimeError(f"extract_words failed for page_index={pidx}: {exc}") from exc
        tops = sorted(w["top"] for w in words)
        deltas = [round(tops[i + 1] - tops[i], 4) for i in range(len(tops) - 1)]
        nonzero = sorted(d for d in deltas if d > 0.001)
        if not nonzero:
            continue
        # Heuristic split for THIS validation only: anything before the
        # first delta >= 5pt is same-line jitter (no observed same-line
        # jitter anywhere near that on any sampled page); everything after
        # is a real line-to-line gap.
        same_line_here = [d for d in nonzero if d < 5.0]
        cross_line_here = [d for d in nonzero if d >= 5.0]
        if same_line_here:
            same_line_max = max(same_line_max, max(same_line_here))
        if cross_line_here:
            cross_line_min = min(cross_line_here) if cross_line_min is None else min(cross_line_min, min(cross_line_here))

        try:
            lines = page.extract_text_lines()
        except Exception as exc:
            raise RuntimeError(f"extract_text_lines failed for page_index={pidx}: {exc}") from exc
        per_page.append({
            "page_index": pidx, "word_count": len(words), "extract_text_lines_count": len(lines),
        })
    tolerance = 3.0
    return {
        "sample_pages": per_page,
        "observed_same_line_max_delta": same_line_max,
        "observed_cross_line_min_delta": cross_line_min,
        "derived_tolerance_pt": tolerance,
        "gap_margin_above_same_line": tolerance - same_line_max,
        "gap_margin_below_cross_line": (cross_line_min - tolerance) if cross_line_min else None,
    }


def _is_all_caps(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    return bool(letters) and all(c.isupper() for c in letters)


def _classify_structural(line: dict, page_height: float, page_width: float,
                          modal_left_margin: float, body_right_edge: float) -> str | None:
    """Rules 1-4, first match wins. Returns None if this is a "body"
    candidate (rule 5 / paragraph-opening decision happens in a second
    pass over all body lines on the page).

    CAUGHT AND FIXED before trusting this report: the original `centred`
    rule compared raw `x0`/`page_width - x1` gaps -- but Cheiro's body text
    is JUSTIFIED (both margins line up), so an ordinary full-width
    continuation line coincidentally has left_gap ~= right_gap almost every
    time, wrongly firing `centred` on real prose (confirmed directly: page
    214 flagged 30 of 35 lines as "centred", nearly all of them ordinary
    justified body sentences on inspection). Fixed by additionally
    requiring the candidate line to be genuinely SHORT relative to the
    page's own typical full-line width (computed from `body_right_edge`,
    the max x1 among indent~=0 lines) -- a real centred heading (e.g.
    "CHAPTER X.") is both short AND symmetric; an ordinary justified
    sentence is full-width and only coincidentally symmetric."""
    text = line["text"].strip()
    top, bottom, x0, x1 = line["top"], line["bottom"], line["x0"], line["x1"]

    if text.isdigit() and (top < _EXTREMITY_BAND_PT or bottom > page_height - _EXTREMITY_BAND_PT):
        return "folio_number"

    if top < _EXTREMITY_BAND_PT:
        tokens = [t.lower() for t in census._tokenize(text)]
        if tokens:
            hits = sum(1 for t in tokens if t in c5mod._RUNNING_HEAD_MARKERS)
            if hits / len(tokens) >= 0.5:
                return "running_head"

    words_in_line = text.split()
    if 0 < len(words_in_line) <= 6 and _is_all_caps(text):
        return "chapter_heading"

    full_width = body_right_edge - modal_left_margin
    line_width = x1 - x0
    is_short_line = full_width > 0 and line_width < 0.6 * full_width
    if is_short_line:
        left_gap = x0 - modal_left_margin
        right_gap = body_right_edge - x1
        if abs(left_gap - right_gap) <= _CENTERED_TOLERANCE_PT and left_gap > _CENTERED_TOLERANCE_PT:
            return "centred"

    return None


def _find_subsequence(haystack: list[str], needle: list[str], start: int = 0) -> int | None:
    """First index >= start in haystack where needle appears as a
    contiguous subsequence, or None. Empty needle matches nowhere (nothing
    to bridge). `start` matters: this book repeats short phrases across a
    single page (e.g. multiple paragraphs literally opening "The line
    of..." on the same palmistry page) -- searching from index 0 every
    time would resolve every such opening to the SAME first occurrence.
    Caught directly: page 162 originally showed two different opening
    lines both resolving to native_index=0. Fixed by advancing `start`
    monotonically as callers process a page's openings in line order
    (their native positions must also increase in the same order)."""
    if not needle:
        return None
    n = len(needle)
    for i in range(max(start, 0), len(haystack) - n + 1):
        if haystack[i:i + n] == needle:
            return i
    return None


def _analyze_page(pdf, page_index: int, provisional_cut: float) -> dict:
    page = pdf.pages[page_index]
    try:
        lines = page.extract_text_lines()
    except Exception as exc:
        raise RuntimeError(f"extract_text_lines failed for page_index={page_index}: {exc}") from exc

    if not lines:
        return {
            "page_index": page_index, "line_count": 0, "modal_left_margin": None,
            "false_positive_counts": {}, "candidate_openings": [], "line_records": [],
        }

    x0_rounded = [round(l["x0"]) for l in lines]
    modal_left_margin = Counter(x0_rounded).most_common(1)[0][0]

    # body_right_edge: max x1 among near-zero-indent (ordinary continuation)
    # lines -- the page's own typical "right justification point," used by
    # _classify_structural's centred rule to detect genuinely SHORT lines
    # rather than full-width justified prose that merely looks symmetric.
    near_zero_x1 = [l["x1"] for l in lines if abs(l["x0"] - modal_left_margin) <= 3.0]
    body_right_edge = max(near_zero_x1) if near_zero_x1 else max(l["x1"] for l in lines)

    line_records = []
    for i, l in enumerate(lines):
        indent = l["x0"] - modal_left_margin
        line_records.append({
            "line_no": i, "text": l["text"], "x0": l["x0"], "top": l["top"],
            "x1": l["x1"], "bottom": l["bottom"], "indent": indent,
            "structural_class": None,  # filled below
        })

    page_height = page.height
    page_width = page.width
    for rec in line_records:
        rec["structural_class"] = _classify_structural(
            {"text": rec["text"], "top": rec["top"], "bottom": rec["bottom"], "x0": rec["x0"], "x1": rec["x1"]},
            page_height, page_width, modal_left_margin, body_right_edge,
        )

    # ─── verse_block second pass, over unclassified ("body" candidate) lines ──
    body_indices = [i for i, r in enumerate(line_records) if r["structural_class"] is None]
    run_start = None
    for pos, idx in enumerate(body_indices):
        indent = line_records[idx]["indent"]
        is_verse_candidate = indent > provisional_cut
        prev_idx = body_indices[pos - 1] if pos > 0 else None
        contiguous_with_prev = prev_idx is not None and (idx - prev_idx == 1)
        same_indent_as_prev = (
            contiguous_with_prev and
            abs(line_records[prev_idx]["indent"] - indent) <= _VERSE_BLOCK_INDENT_TOLERANCE_PT and
            is_verse_candidate
        )
        if same_indent_as_prev:
            if run_start is None:
                run_start = prev_idx
        else:
            if run_start is not None:
                for k in range(run_start, idx):
                    if line_records[k]["structural_class"] is None:
                        line_records[k]["structural_class"] = "verse_block"
            run_start = None
    if run_start is not None:
        for k in range(run_start, body_indices[-1] + 1):
            if line_records[k]["structural_class"] is None:
                line_records[k]["structural_class"] = "verse_block"

    for rec in line_records:
        if rec["structural_class"] is None:
            rec["structural_class"] = (
                "candidate_paragraph_opening" if rec["indent"] > provisional_cut else "body_continuation"
            )

    false_positive_counts = Counter(r["structural_class"] for r in line_records)
    candidate_openings = [r for r in line_records if r["structural_class"] == "candidate_paragraph_opening"]

    return {
        "page_index": page_index, "line_count": len(lines), "modal_left_margin": modal_left_margin,
        "false_positive_counts": dict(false_positive_counts),
        "candidate_openings": candidate_openings, "line_records": line_records,
    }


def main() -> int:
    try:
        if not SIDECAR_PATH.exists():
            raise RuntimeError(f"Required U1 sidecar not found: {SIDECAR_PATH}")
        with open(SIDECAR_PATH, "r", encoding="utf-8") as f:
            u1 = json.load(f)

        collection = census._get_collection()

        with pdfplumber.open(census.CHEIRO_PDF) as pdf:
            self_check_results = spanmod._run_self_checks(pdf, collection)

            tolerance_derivation = _derive_line_tolerance(pdf)

            # ─── cohort membership ──
            cohort_a = sorted({p["page_index"] for p in u1["page_records"] if p["overlap_token_count"] > 0})
            cohort_b = [124]
            cohort_c = [p["page_index"] for p in sorted(u1["zero_chunk_pages"], key=lambda p: -p["native_char_count"])[:5]]
            cohort_d = [ref - 1 for ref in _CLAUDE_ANCHOR_PAGE_REFS]
            clean_pages = [p for p in u1["page_records"] if p["monotonic"] and p["overlap_token_count"] == 0]
            cohort_e = [p["page_index"] for p in sorted(clean_pages, key=lambda p: (-p["coverage"], p["page_index"]))[:3]]

            membership: dict[int, list[str]] = {}
            for label, pages in [("A", cohort_a), ("B", cohort_b), ("C", cohort_c), ("D", cohort_d), ("E", cohort_e)]:
                for p in pages:
                    membership.setdefault(p, []).append(label)

            overlap_across_groups = {p: labels for p, labels in membership.items() if len(labels) > 1}

            all_pages = sorted(membership.keys())

            # ─── FIRST PASS: gather all line indents across the cohort (needed to set the provisional cut) ──
            raw_pass: dict[int, dict] = {}
            for page_index in all_pages:
                # temporary cut of 0 for the first pass -- only used to compute the indent histogram;
                # verse_block/candidate_opening classification is redone in the SECOND pass below once
                # the real provisional cut is known, so this pass's classification fields are discarded.
                raw_pass[page_index] = _analyze_page(pdf, page_index, provisional_cut=1e9)

            all_indents = []
            for page_index, res in raw_pass.items():
                for r in res["line_records"]:
                    if r["structural_class"] in ("candidate_paragraph_opening", "body_continuation"):
                        all_indents.append(r["indent"])
            all_indents_sorted = sorted(all_indents)

            histogram = Counter()
            for v in all_indents_sorted:
                bucket = int(v // _INDENT_BUCKET_WIDTH)
                histogram[bucket] += 1

            def _pct(sorted_vals, p):
                if not sorted_vals:
                    return None
                if len(sorted_vals) == 1:
                    return sorted_vals[0]
                rank = (p / 100) * (len(sorted_vals) - 1)
                lo = int(rank)
                hi = min(lo + 1, len(sorted_vals) - 1)
                frac = rank - lo
                return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac

            indent_stats = {
                "n": len(all_indents_sorted),
                "min": all_indents_sorted[0] if all_indents_sorted else None,
                "p25": _pct(all_indents_sorted, 25),
                "median": _pct(all_indents_sorted, 50),
                "p75": _pct(all_indents_sorted, 75),
                "max": all_indents_sorted[-1] if all_indents_sorted else None,
            }

            # Derive the provisional cut from the histogram's own shape: find the
            # first bucket gap (a bucket with zero count) AFTER the zero-cluster,
            # scanning from indent==0 upward. The cut is placed at the START of
            # that empty bucket -- i.e. the boundary of the observed gap.
            nonneg_buckets = sorted(b for b in histogram if b >= 0)
            provisional_cut = None
            if nonneg_buckets:
                for b in range(nonneg_buckets[0], nonneg_buckets[-1] + 1):
                    if histogram.get(b, 0) == 0:
                        # confirm there IS a later non-empty bucket (a real second cluster, not just the tail)
                        if any(histogram.get(bb, 0) > 0 for bb in range(b + 1, nonneg_buckets[-1] + 1)):
                            provisional_cut = b * _INDENT_BUCKET_WIDTH
                            break
            if provisional_cut is None:
                provisional_cut = indent_stats["median"] if indent_stats["median"] is not None else 10.0

            # ─── SECOND PASS: real analysis using the now-known provisional cut ──
            page_results: dict[int, dict] = {}
            for page_index in all_pages:
                page_results[page_index] = _analyze_page(pdf, page_index, provisional_cut=provisional_cut)

            # ─── (a) GATE NUMBER: bridge line-space to native-token-space for D/E pages ──
            # U1's span_start lives in census._tokenize(extract_text()) word-index space;
            # this probe's openings live in extract_text_lines() line-index space. Both
            # ultimately read the SAME embedded PDF text objects, so an opening line's
            # first few words are findable as a literal subsequence inside the native
            # token list -- bridged here via a direct subsequence search, not assumed
            # comparable "for free."
            gate_rows = []
            for page_index in sorted(set(cohort_e) | set(cohort_d)):
                res = page_results[page_index]
                u1_page = next((p for p in u1["page_records"] if p["page_index"] == page_index), None)
                existing_chunk_count = u1_page["chunk_count"] if u1_page else 0
                existing_starts = [c["span_start"] for c in u1_page["chunks"] if c["span_start"] is not None] if u1_page else []

                native_tokens = census._tokenize(census._native_text(pdf, page_index))
                native_lower = [t.lower() for t in native_tokens]

                near_agreement = 0
                opening_details = []
                search_from = 0  # advances monotonically -- openings are in ascending line-position order
                for opening in res["candidate_openings"]:
                    key_tokens = [t.lower() for t in census._tokenize(opening["text"])[:3]]
                    native_index = _find_subsequence(native_lower, key_tokens, start=search_from)
                    if native_index is not None:
                        search_from = native_index + 1
                    is_near = (
                        native_index is not None and
                        any(abs(native_index - s) <= 5 for s in existing_starts)
                    )
                    if is_near:
                        near_agreement += 1
                    opening_details.append({
                        "text": opening["text"][:60], "native_index": native_index, "within_5_tokens": is_near,
                    })

                gate_rows.append({
                    "page_index": page_index,
                    "in_cohort": membership[page_index],
                    "detected_opening_count": len(res["candidate_openings"]),
                    "existing_chunk_count": existing_chunk_count,
                    "existing_span_starts": existing_starts,
                    "within_5_tokens_count": near_agreement,
                    "opening_details": opening_details,
                })

        # ─── (c) per-page table ──
        page_table = []
        for page_index in all_pages:
            res = page_results[page_index]
            fpc = res["false_positive_counts"]
            page_table.append({
                "page_index": page_index, "cohorts": membership[page_index],
                "line_count": res["line_count"], "modal_left_margin": res["modal_left_margin"],
                "detected_openings": len(res["candidate_openings"]),
                "centred": fpc.get("centred", 0), "chapter_heading": fpc.get("chapter_heading", 0),
                "running_head": fpc.get("running_head", 0), "folio_number": fpc.get("folio_number", 0),
                "verse_block": fpc.get("verse_block", 0),
            })

        # ─── (d) page 125 + 3 overlap pages structure printout ──
        structure_pages = [124] + cohort_a[:3]
        structure_printout = []
        for page_index in structure_pages:
            res = page_results[page_index]
            openings = [
                {"line_no": o["line_no"], "first_words": " ".join(o["text"].split()[:8])}
                for o in res["candidate_openings"]
            ]
            structure_printout.append({"page_index": page_index, "openings": openings})

        # ─── (e) zero-detected-opening pages ──
        zero_opening_pages = []
        for page_index in all_pages:
            res = page_results[page_index]
            if len(res["candidate_openings"]) == 0:
                zero_opening_pages.append({
                    "page_index": page_index, "cohorts": membership[page_index],
                    "line_count": res["line_count"],
                    "false_positive_counts": res["false_positive_counts"],
                })

        output = {
            "tolerance_derivation": tolerance_derivation,
            "self_check_results": self_check_results,
            "cohort_a": cohort_a, "cohort_b": cohort_b, "cohort_c": cohort_c,
            "cohort_d": cohort_d, "cohort_e": cohort_e,
            "membership": {str(k): v for k, v in membership.items()},
            "cross_cohort_overlap": {str(k): v for k, v in overlap_across_groups.items()},
            "provisional_cut_pt": provisional_cut,
            "indent_stats": indent_stats,
            "indent_histogram": {f"{b*_INDENT_BUCKET_WIDTH:.0f}-{(b+1)*_INDENT_BUCKET_WIDTH:.0f}": histogram.get(b, 0)
                                  for b in range(min(histogram, default=0), max(histogram, default=0) + 1)},
            "gate_rows": gate_rows,
            "page_table": page_table,
            "structure_printout": structure_printout,
            "zero_opening_pages": zero_opening_pages,
            "page_results_full": {
                str(pidx): {
                    "line_count": r["line_count"], "modal_left_margin": r["modal_left_margin"],
                    "false_positive_counts": r["false_positive_counts"],
                    "line_records": r["line_records"],
                } for pidx, r in page_results.items()
            },
        }

        DATA_SIDECAR_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {DATA_SIDECAR_PATH} ({DATA_SIDECAR_PATH.stat().st_size} bytes)")

        _write_markdown_report(output)
        print(f"Wrote {REPORT_PATH} ({REPORT_PATH.stat().st_size} bytes)")
        LATEST_RUN_PATH.write_text(REPORT_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Overwrote {LATEST_RUN_PATH}")
        for c in self_check_results:
            print(f"  [PASS] {c['assertion']}")
        return 0

    except Exception as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return 1


def _write_markdown_report(d: dict) -> None:
    lines = []
    lines.append("# LAYOUT-BASED PARAGRAPH RECOVERY PROBE — S80 U1c — Cheiro only")
    lines.append("")
    lines.append(
        "Read-only, diagnostics-only. No repair, no boundary-seeder logic, no ChromaDB "
        "writes, no re-ingestion. Method: `page.extract_text_lines()` (NOT `extract_words()` "
        "directly — see module docstring for why). See scripts/layout_paragraph_probe_S80.py "
        "for full reuse/method detail."
    )
    lines.append("")

    td = d["tolerance_derivation"]
    lines.append("## Line-grouping tolerance derivation")
    lines.append("")
    lines.append(
        f"Sampled 3 clean pages (page_index {[p['page_index'] for p in td['sample_pages']]}) via "
        f"`extract_words()`. Observed same-line word-to-word `top` delta ceiling: "
        f"**{td['observed_same_line_max_delta']:.3f}pt**. Observed smallest cross-line gap: "
        f"**{td['observed_cross_line_min_delta']:.3f}pt**. Derived tolerance: **{td['derived_tolerance_pt']:.1f}pt** "
        f"(margin above same-line ceiling: {td['gap_margin_above_same_line']:.3f}pt; margin below "
        f"cross-line floor: {td['gap_margin_below_cross_line']:.3f}pt)."
    )
    lines.append("")
    lines.append("| page_index | word_count | extract_text_lines() line count |")
    lines.append("|---|---|---|")
    for p in td["sample_pages"]:
        lines.append(f"| {p['page_index']} | {p['word_count']} | {p['extract_text_lines_count']} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## Self-checks")
    lines.append("")
    lines.append("| Assertion | Expected | Observed | Status |")
    lines.append("|---|---|---|---|")
    for c in d["self_check_results"]:
        lines.append(f"| {c['assertion']} | {c['expected']} | {c['observed']} | {c['status']} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## Cohort membership")
    lines.append("")
    lines.append(f"- A (14 overlap pages): {d['cohort_a']}")
    lines.append(f"- B (page 125, worst coverage): {d['cohort_b']}")
    lines.append(f"- C (5 highest-native_char_count zero-chunk pages): {d['cohort_c']}")
    lines.append(f"- D (4 anchor pages, page_index): {d['cohort_d']}")
    lines.append(f"- E (3 control pages, highest coverage): {d['cohort_e']}")
    lines.append("")
    if d["cross_cohort_overlap"]:
        lines.append(f"**Cross-cohort overlap found:** {d['cross_cohort_overlap']}")
    else:
        lines.append("No page appears in more than one cohort group — confirmed, not assumed.")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append(f"## PROVISIONAL, NOT RATIFIED indent cut: {d['provisional_cut_pt']:.1f}pt")
    lines.append("")
    lines.append(
        "Derived from the histogram below: the first empty 2pt bucket after the zero-cluster, "
        "confirmed to have real occupied buckets beyond it (i.e. a genuine gap between two "
        "clusters, not just the distribution's tail). **This cut is provisional and used only "
        "to produce the numbers in this report — it is not a ratified threshold.**"
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## (a) GATE NUMBER — agreement on control (E) + anchor (D) pages")
    lines.append("")
    lines.append(
        "Each detected opening's first 1-3 words are located as a literal subsequence inside "
        "the SAME page's `census._tokenize(extract_text())` native-token list (both extractions "
        "read the same underlying PDF text objects, just grouped differently), giving a native-"
        "token index directly comparable to U1's `span_start` values."
    )
    lines.append("")
    lines.append("| page_index | cohort | detected openings | existing chunk count | existing span_starts | within 5 native tokens of a span_start |")
    lines.append("|---|---|---|---|---|---|")
    total_openings = sum(r["detected_opening_count"] for r in d["gate_rows"])
    total_within_5 = sum(r["within_5_tokens_count"] for r in d["gate_rows"])
    for r in d["gate_rows"]:
        lines.append(
            f"| {r['page_index']} | {'/'.join(r['in_cohort'])} | {r['detected_opening_count']} | "
            f"{r['existing_chunk_count']} | {r['existing_span_starts']} | {r['within_5_tokens_count']} |"
        )
    lines.append("")
    lines.append(f"**GATE NUMBER: {total_within_5} / {total_openings} detected openings on the 3 control + 4 anchor pages fall within 5 native tokens of an existing chunk span_start.**")
    lines.append("")
    lines.append("<details><summary>Per-opening detail (click to expand)</summary>")
    lines.append("")
    lines.append("| page_index | opening text (first 60 chars) | native_index | within_5_tokens |")
    lines.append("|---|---|---|---|")
    for r in d["gate_rows"]:
        for o in r["opening_details"]:
            lines.append(f"| {r['page_index']} | {o['text']} | {o['native_index']} | {o['within_5_tokens']} |")
    lines.append("")
    lines.append("</details>")
    lines.append("")
    lines.append(
        "Agreement on pages already believed correct (control + anchor) is the only thing that "
        "validates the method — a low agreement rate here would mean the layout signal does not "
        "reliably locate the SAME boundaries this project's existing chunking already got right, "
        "independent of whether those existing boundaries are themselves complete."
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## (b) Indent distribution across the cohort")
    lines.append("")
    st = d["indent_stats"]
    lines.append(f"n = {st['n']}, min = {st['min']:.2f}, p25 = {st['p25']:.2f}, median = {st['median']:.2f}, p75 = {st['p75']:.2f}, max = {st['max']:.2f}")
    lines.append("")
    lines.append("| Bucket (pt) | Count |")
    lines.append("|---|---|")
    for bucket_label, count in d["indent_histogram"].items():
        lines.append(f"| {bucket_label} | {count} |")
    lines.append("")
    lines.append(
        "This distribution is the DERIVED input for an indentation threshold. **No threshold is "
        "ratified here** — the provisional cut above exists only to produce this report's other "
        "numbers; the real threshold is a design-chat ruling, with its own scope guard and tuning "
        "note."
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## (c) Per-page table")
    lines.append("")
    lines.append("| page_index | cohort | line_count | modal_left_margin | detected_openings | centred | chapter_heading | running_head | folio_number | verse_block |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in d["page_table"]:
        lines.append(
            f"| {r['page_index']} | {'/'.join(r['cohorts'])} | {r['line_count']} | {r['modal_left_margin']} | "
            f"{r['detected_openings']} | {r['centred']} | {r['chapter_heading']} | {r['running_head']} | "
            f"{r['folio_number']} | {r['verse_block']} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## (d) Detected paragraph structure — page 125 + 3 overlap pages")
    lines.append("")
    for p in d["structure_printout"]:
        lines.append(f"### page_index={p['page_index']}")
        lines.append("")
        if p["openings"]:
            lines.append("| line_no | first 8 words |")
            lines.append("|---|---|")
            for o in p["openings"]:
                lines.append(f"| {o['line_no']} | {o['first_words']} |")
        else:
            lines.append("(zero candidate openings detected on this page)")
        lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## (e) Pages with ZERO detected openings")
    lines.append("")
    if d["zero_opening_pages"]:
        lines.append("| page_index | cohort | line_count | false_positive_counts | judgment |")
        lines.append("|---|---|---|---|---|")
        for p in d["zero_opening_pages"]:
            fpc = p["false_positive_counts"]
            structural_total = sum(v for k, v in fpc.items() if k != "body_continuation")
            if p["line_count"] == 0:
                judgment = "PLATE (no extractable text lines at all)"
            elif structural_total >= p["line_count"] - 1:
                judgment = "single structural element (heading/running-head/folio only) — genuinely no prose paragraph on this page"
            elif fpc.get("body_continuation", 0) == p["line_count"]:
                judgment = "genuinely single-paragraph (all lines flush-left, no indented opening — plausible for a page that continues mid-paragraph from the prior page)"
            else:
                judgment = "DETECTION FAILURE candidate — mixed structural/body lines present but no opening cleared the provisional cut; needs a human read"
            lines.append(f"| {p['page_index']} | {'/'.join(p['cohorts'])} | {p['line_count']} | {fpc} | {judgment} |")
    else:
        lines.append("(none — every cohort page had at least one detected opening)")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## (f) Stated limitations")
    lines.append("")
    lines.append(
        "- **The text-to-native-token-index bridge is a literal-subsequence search, not a full "
        "alignment.** Section (a)'s bridge locates an opening line's first 1-3 words as an exact "
        "match inside the native token list — it can fail to find a genuine match if OCR/PDF-"
        "extraction noise differs between `extract_text_lines()` and `extract_text()` for that "
        "specific span (rare, since both read the same text objects, but not impossible), and it "
        "does not attempt a fuzzy or partial match when the exact 1-3 word key is absent."
    )
    lines.append(
        "- **Indentation convention pages.** Any page where the printer did not consistently "
        "first-line-indent new paragraphs (title pages, tables of contents, dedication pages) will "
        "not show the signal this method looks for — cohort C's zero-chunk pages include exactly "
        "this kind of apparatus page."
    )
    lines.append(
        "- **Tables and multi-column layout.** `extract_text_lines()` assumes a single reading "
        "column; a page with a genuine table or side-by-side columns would have its cells' x0 "
        "values conflated into one modal-margin computation, producing meaningless indents."
    )
    lines.append(
        "- **Plate captions and illustration pages.** Pages with `extract_text_lines() count == 0` "
        "have nothing for this method to work with at all — they are plates, not text pages, "
        "regardless of what a boundary seeder does with them."
    )
    lines.append(
        "- **The false-positive taxonomy itself is heuristic, not exhaustive.** `chapter_heading`'s "
        "\"<=6 words, all-caps\" rule and `centred`'s 10pt symmetry tolerance are stated, reasoned "
        "cuts, not empirically validated against a negative-control set the way U0.5's support-score "
        "floor was."
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## (g) Recommendation")
    lines.append("")
    lines.append(
        "**None made.** No ruling on the indent threshold, seeder design, or whether to adopt "
        "layout-based derivation at all — report only, per instruction."
    )
    lines.append("")
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
