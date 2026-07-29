"""
scripts/span_mapping_probe_S80.py
S80 U1 -- chunk-to-native SPAN MAPPING PROBE, Cheiro only, read-only,
diagnostics-only. Run manually; never invoked from CI or the pytest suite.

GATES PATH D (re-ingest from native text, seeding new chunk boundaries from
EXISTING chunk spans rather than a fresh paragraph splitter). PATH C
(in-place text replacement) IS RETIRED per design-chat ruling -- this file
does NOT write align_chunk_to_native() or any repair/merge function. No
writes to ChromaDB, no shadow collection, no re-ingestion, no imports from
pdf_processor.py/chunker.py/embedder.py/query_engine.py.

REUSE, NOT REINVENTION -- everything this probe needs that already exists
is imported, not re-derived:
  - scripts/bidirectional_corruption_census_S80.py (imported as `census`):
    CHEIRO_PDF, CHEIRO_BOOK, CHROMA_DIR, _sha256_file, _load_wordset,
    _get_collection, _native_text, _tokenize, _run_mandatory_self_checks,
    _align_and_classify (used ONLY for the requirement-(g) C5b regeneration
    pass below, not for span computation), _CHUNK_SUFFIX_PATTERN,
    _is_roman_numeral.
  - scripts/c5_decomposition_S80.py (imported as `c5mod`): _subcategorize
    (the FULL 7-rule taxonomy -- roman numeral / punctuation-single-char /
    plate caption / running head / proper noun / ordinary prose word /
    other-unclassified -- reused verbatim, not re-implemented, per
    instruction).
  - tests/fixtures/native_coverage_S80.json / diagnostics/
    bidirectional_corruption_census_S80_data.json were CHECKED as reuse
    candidates for native/corpus text, but neither actually persists
    PER-CHUNK text (the census sidecar only has per-page aggregates and
    top-40 pair examples; the coverage file has no text at all) -- so
    native text and per-chunk corpus text are RE-EXTRACTED here via the
    same `census._native_text()` / a thin `_get_ordered_chunks()` wrapper
    around `census._get_collection()`, not duplicated logic, just a fresh
    read through the same helpers the census used.

WHAT'S GENUINELY NEW HERE (not reused from either prior script): the span-
computation function `_compute_span()` (difflib.SequenceMatcher applied
CHUNK-tokens-vs-PAGE-tokens, a different granularity than either prior
script's PAGE-vs-PAGE alignment), the per-page monotonicity/overlap/gap
aggregation, and the requirement-(g) orchestration loop that reconnects a
C5b ordinary-prose token back to the specific chunk it came from (neither
prior script tracked chunk-level identity for C5b tokens, only page-level).

METHOD:
  1. Native page text tokenized via census._tokenize (alpha-only tokens,
     same convention as both prior scripts).
  2. Live corpus chunks for that page fetched via ChromaDB metadata filter
     (book_name + page_ref), ordered by NUMERIC chunk_id c-suffix (c0, c1,
     ..., c10 -- not lexicographic "c10" < "c2"), via
     census._CHUNK_SUFFIX_PATTERN.
  3. Each chunk's own tokens are aligned against the FULL native page's
     tokens via difflib.SequenceMatcher(chunk_tokens_lower, native_tokens_
     lower).get_matching_blocks() -- lowercased for the match, same
     case-insensitivity convention as U0.5/U0.6 (a pure case difference is
     never treated as a mismatch anywhere in this project's alignment
     work). span_start/span_end = min/max NATIVE index across all
     non-empty matching blocks; span_len = span_end - span_start + 1;
     matched_token_count = sum of matched block sizes; match_ratio =
     matched_token_count / chunk_token_count (NOT / span_len -- per
     instruction, the denominator is the chunk's own token count).
  4. Per page: monotonic = span_start non-decreasing across chunks in
     chunk-index order (chunks with no matched tokens at all -- span is
     None -- are excluded from the monotonicity check, since there is
     nothing to compare; noted separately, never silently dropped from the
     per-chunk record). overlap_token_count/gap_token_count are computed
     by treating each chunk's [span_start, span_end] as a CLOSED interval
     (matching the instruction's own span_start/span_end/span_len
     definition, not just the literally-matched discrete positions inside
     it) and counting, per native token index, how many chunk intervals
     cover it.
  5. Every gap token (covered by zero chunk intervals) is subcategorized
     via c5mod._subcategorize -- the exact same function U0.6 used, same
     7-way taxonomy, imported not copied.

Zero-live-chunk pages (p19, p191 at minimum -- confirmed the FULL set
during this run, not assumed to be just those two) are reported in their
own section (f), NOT span-mapped (there is nothing to map). Chunks with
very low match_ratio are kept in every aggregate, never filtered out
silently.

Requirement (g) needs to know, for each of U0.6's 146 C5b ordinary-prose
token OCCURRENCES, which specific chunk it came from (U0.6 itself only
tracked page-level C5b identity, via the whole-page-joined-corpus-text
alignment in census._align_and_classify -- it never needed per-chunk
attribution for its own purpose). This probe regenerates that SAME
page-level C5b ordinary-prose list (same function, same wordset, same
per-page joined-corpus-text construction) and adds chunk attribution by
checking which of that page's SPAN-MAPPED chunks contains the token as one
of its own tokens. A FIDELITY CHECK asserts the regenerated total exactly
equals U0.6's already-reported 146 before this section is trusted -- if it
doesn't match, this script fails loudly rather than silently reporting on
a different token set than U0.6 already ratified.

No recommendation anywhere in this script or its report on seeding
viability, match_ratio acceptance thresholds, or Path D itself -- report
only, per instruction.
"""

from __future__ import annotations

import difflib
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bidirectional_corruption_census_S80 as census  # noqa: E402  -- reuse
import c5_decomposition_S80 as c5mod  # noqa: E402  -- reuse, taxonomy only

import pdfplumber  # noqa: E402

ROOT = census.ROOT
REPORT_PATH = ROOT / "diagnostics" / "span_mapping_probe_S80.md"
SIDECAR_PATH = ROOT / "diagnostics" / "span_mapping_probe_S80_data.json"
LATEST_RUN_PATH = ROOT / "diagnostics" / "latest_run.md"

_EXPECTED_C5B_ORDINARY_PROSE_TOTAL = 146  # U0.6's already-reported, committed number

_CLAUDE_ANCHORS = [
    ("p145_c0", 145, 0),
    ("p139_c0", 139, 0),
    ("p163_c1", 163, 1),
    ("p159_c2", 159, 2),
]

_LOWEST_COVERAGE_TOP_N = 15
_WORST_MONOTONIC_TOP_N = 3
_WORST_OVERLAP_TOP_N = 3


# ─── Reused-primitive thin wrappers ────────────────────────────────────────


def _get_ordered_chunks(collection, page_ref: int, page_index: int) -> list[tuple[str, str]]:
    """(chunk_id, text) pairs for this page, ordered by NUMERIC c-suffix."""
    try:
        res = collection.get(
            where={"$and": [{"book_name": {"$eq": census.CHEIRO_BOOK}}, {"page_ref": {"$eq": page_ref}}]},
            include=["documents"],
        )
    except Exception as exc:
        raise RuntimeError(
            f"ChromaDB read failed for page_index={page_index} (page_ref={page_ref}): {exc}"
        ) from exc

    def _suffix(chunk_id: str) -> int:
        m = census._CHUNK_SUFFIX_PATTERN.search(chunk_id)
        return int(m.group(1)) if m else 0

    return sorted(zip(res["ids"], res["documents"]), key=lambda pair: _suffix(pair[0]))


def _run_self_checks(pdf, collection) -> list[dict]:
    """4 checks reused verbatim from census._run_mandatory_self_checks
    (raises internally on failure), plus the 5th check this probe adds:
    p156 live chunk count == 3."""
    results = census._run_mandatory_self_checks(pdf)
    chunks = _get_ordered_chunks(collection, 156, 155)
    count = len(chunks)
    if count != 3:
        raise AssertionError(
            f"MANDATORY SELF-CHECK FAILED — refusing to write output:\n"
            f"  - Cheiro p156 live chunk count == 3: expected 3, got {count}"
        )
    results.append({
        "assertion": "Cheiro p156 live chunk count == 3",
        "expected": 3, "observed": count, "status": "PASS",
    })
    return results


# ─── New: chunk-to-native span computation ────────────────────────────────


def _compute_span(chunk_tokens: list[str], native_tokens: list[str]):
    """Returns (span_start, span_end, matched_token_count). span_start/end
    are None if the chunk has zero matched tokens against this page (a real
    possibility for a badly garbled chunk; reported, never crashed on)."""
    chunk_lower = [t.lower() for t in chunk_tokens]
    native_lower = [t.lower() for t in native_tokens]
    sm = difflib.SequenceMatcher(None, chunk_lower, native_lower, autojunk=False)
    matched_native_indices: list[int] = []
    matched_token_count = 0
    for block in sm.get_matching_blocks():
        if block.size == 0:
            continue
        matched_token_count += block.size
        matched_native_indices.extend(range(block.b, block.b + block.size))
    if not matched_native_indices:
        return None, None, 0
    return min(matched_native_indices), max(matched_native_indices), matched_token_count


def _looks_like_ocr_garbage(token: str) -> bool:
    """STATED heuristic for requirement (g), applied independently of
    chunk-mapping status. Two OR'd signals, both directly motivated by
    U0.6's own top-C5b-token examples (eee, cece, ccc, cee, ene, nent):
      1. A run of 3+ identical consecutive characters (catches "eee",
         "ccc"), OR a 2-character unit repeated 2+ times covering a token
         of length <= 8 (catches "cece").
      2. The longest run of consecutive same-class letters (all-vowel or
         all-consonant) is >= 3 -- ordinary English words rarely stack 3+
         vowels or 3+ consonants in a row (catches "eee" again via a
         different signal, and would catch e.g. "nnn" or "aeiou"-style
         degenerate runs not caught by signal 1).
    Neither signal is tuned against a negative-control set of genuine rare
    English words (unlike this project's earlier support-score floors) --
    reported as a stated, not empirically-validated, heuristic, per
    instruction."""
    low = token.lower()
    if re.search(r"(.)\1{2,}", low):
        return True
    if len(low) <= 8 and re.search(r"(..)\1{1,}", low):
        return True
    vowels = set("aeiou")
    classes = ["V" if c in vowels else "C" for c in low if c.isalpha()]
    if not classes:
        return False
    longest_run, cur = 1, 1
    for i in range(1, len(classes)):
        if classes[i] == classes[i - 1]:
            cur += 1
            longest_run = max(longest_run, cur)
        else:
            cur = 1
    return longest_run >= 3


def _percentile(sorted_vals: list[float], p: float) -> float:
    """Linear-interpolation percentile (numpy-style), p in [0, 100]."""
    if not sorted_vals:
        return float("nan")
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    rank = (p / 100) * (len(sorted_vals) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = rank - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def main() -> int:
    try:
        wordset, oracle_desc = census._load_wordset()
        collection = census._get_collection()
        pdf_sha256 = census._sha256_file(census.CHEIRO_PDF)

        page_records = []
        zero_chunk_pages = []
        all_chunk_records = []  # flat list across all mapped pages, for global aggregates

        with pdfplumber.open(census.CHEIRO_PDF) as pdf:
            self_check_results = _run_self_checks(pdf, collection)

            for page_index in range(len(pdf.pages)):
                native_text = census._native_text(pdf, page_index)
                if len(native_text) == 0:
                    continue
                page_ref = page_index + 1
                native_tokens = census._tokenize(native_text)
                chunks = _get_ordered_chunks(collection, page_ref, page_index)

                if not chunks:
                    whole_page_subcats = Counter(
                        c5mod._subcategorize(tok, wordset) for tok in native_tokens
                    )
                    zero_chunk_pages.append({
                        "page_index": page_index,
                        "page_ref": page_ref,
                        "native_char_count": len(native_text),
                        "native_token_count": len(native_tokens),
                        "ordinary_prose_token_count": whole_page_subcats.get("ordinary_prose_word", 0),
                    })
                    continue

                chunk_records = []
                for chunk_id, text in chunks:
                    chunk_tokens = census._tokenize(text)
                    if not chunk_tokens:
                        chunk_records.append({
                            "chunk_id": chunk_id, "span_start": None, "span_end": None,
                            "span_len": 0, "chunk_token_count": 0, "matched_token_count": 0,
                            "match_ratio": None, "note": "empty token list (no alpha tokens in chunk text)",
                        })
                        continue
                    span_start, span_end, matched = _compute_span(chunk_tokens, native_tokens)
                    if span_start is None:
                        chunk_records.append({
                            "chunk_id": chunk_id, "span_start": None, "span_end": None,
                            "span_len": 0, "chunk_token_count": len(chunk_tokens),
                            "matched_token_count": 0, "match_ratio": 0.0,
                            "note": "zero matched tokens against this page's native text",
                        })
                        continue
                    match_ratio = matched / len(chunk_tokens)
                    chunk_records.append({
                        "chunk_id": chunk_id,
                        "span_start": span_start, "span_end": span_end,
                        "span_len": span_end - span_start + 1,
                        "chunk_token_count": len(chunk_tokens),
                        "matched_token_count": matched,
                        "match_ratio": match_ratio,
                        "note": "",
                    })

                # ── per-page aggregation ──
                valid = [r for r in chunk_records if r["span_start"] is not None]
                monotonic = all(
                    valid[i]["span_start"] <= valid[i + 1]["span_start"]
                    for i in range(len(valid) - 1)
                ) if len(valid) >= 2 else True

                coverage_count = [0] * len(native_tokens)
                for r in valid:
                    for i in range(r["span_start"], r["span_end"] + 1):
                        coverage_count[i] += 1

                overlap_token_count = sum(1 for c in coverage_count if c >= 2)
                gap_indices = [i for i, c in enumerate(coverage_count) if c == 0]
                gap_token_count = len(gap_indices)
                coverage = (len(native_tokens) - gap_token_count) / len(native_tokens) if native_tokens else 1.0

                gap_subcats = Counter(c5mod._subcategorize(native_tokens[i], wordset) for i in gap_indices)

                # monotonicity violation count (adjacent-pair inversions)
                mono_violations = sum(
                    1 for i in range(len(valid) - 1)
                    if valid[i]["span_start"] > valid[i + 1]["span_start"]
                )

                page_rec = {
                    "page_index": page_index, "page_ref": page_ref,
                    "native_char_count": len(native_text), "native_token_count": len(native_tokens),
                    "chunk_count": len(chunk_records),
                    "monotonic": monotonic, "mono_violations": mono_violations,
                    "overlap_token_count": overlap_token_count, "gap_token_count": gap_token_count,
                    "coverage": coverage,
                    "gap_subcategory_counts": dict(gap_subcats),
                    "gap_ordinary_prose_count": gap_subcats.get("ordinary_prose_word", 0),
                    "chunks": chunk_records,
                }
                page_records.append(page_rec)
                for r in chunk_records:
                    all_chunk_records.append({**r, "page_index": page_index, "page_ref": page_ref})

        # ─── requirement (g): regenerate U0.6's C5b ordinary-prose list, with chunk attribution ──
        c5b_occurrences = []
        page_by_index = {p["page_index"]: p for p in page_records}
        with pdfplumber.open(census.CHEIRO_PDF) as pdf2:
            for page_index in range(len(pdf2.pages)):
                native_text = census._native_text(pdf2, page_index)
                if len(native_text) == 0:
                    continue
                page_ref = page_index + 1
                corpus_text, _chunk_count = census._corpus_text_for_page(collection, page_ref, page_index)
                if not corpus_text:
                    continue
                native_tokens = census._tokenize(native_text)
                corpus_tokens = census._tokenize(corpus_text)
                _counts, pairs = census._align_and_classify(native_tokens, corpus_tokens, wordset)
                for p in pairs:
                    if p["class"] != "C5" or p.get("corpus") is None:
                        continue
                    tok = p["corpus"]
                    if c5mod._subcategorize(tok, wordset) != "ordinary_prose_word":
                        continue
                    c5b_occurrences.append({"page_index": page_index, "token": tok})

        if len(c5b_occurrences) != _EXPECTED_C5B_ORDINARY_PROSE_TOTAL:
            raise AssertionError(
                f"FIDELITY CHECK FAILED — regenerated C5b ordinary-prose count "
                f"{len(c5b_occurrences)} does not match U0.6's already-reported "
                f"{_EXPECTED_C5B_ORDINARY_PROSE_TOTAL}. Refusing to trust requirement (g) "
                "on a token set that disagrees with the ratified U0.6 report."
            )

        sits_in_mapped_span = 0
        garbage_like = 0

        # Build a page_index -> {chunk_id: set(lowered tokens)} cache for attribution,
        # reusing the same chunk fetch (one extra ChromaDB read per page with C5b hits;
        # negligible -- this is a diagnostics probe, not a hot path).
        pages_needing_attribution = sorted({occ["page_index"] for occ in c5b_occurrences})
        chunk_token_cache: dict[int, dict[str, set]] = {}
        for page_index in pages_needing_attribution:
            page_ref = page_index + 1
            chunks = _get_ordered_chunks(collection, page_ref, page_index)
            chunk_token_cache[page_index] = {
                cid: {t.lower() for t in census._tokenize(text)} for cid, text in chunks
            }

        for occ in c5b_occurrences:
            page = page_by_index.get(occ["page_index"])
            tok_lower = occ["token"].lower()
            in_mapped = False
            if page is not None:
                token_map = chunk_token_cache.get(occ["page_index"], {})
                span_by_chunk = {c["chunk_id"]: c for c in page["chunks"]}
                for cid, toks in token_map.items():
                    if tok_lower in toks:
                        rec = span_by_chunk.get(cid)
                        if rec is not None and rec["span_start"] is not None:
                            in_mapped = True
                            break
            occ["sits_in_mapped_span"] = in_mapped
            occ["garbage_like"] = _looks_like_ocr_garbage(occ["token"])
            if in_mapped:
                sits_in_mapped_span += 1
            if occ["garbage_like"]:
                garbage_like += 1

        # ─── GATE 1 ──
        seeding_viable_pages = [p for p in page_records if p["monotonic"] and p["overlap_token_count"] == 0]
        gate1_fraction = len(seeding_viable_pages) / 245
        total_gap_ordinary_prose = sum(p["gap_ordinary_prose_count"] for p in page_records)
        gate1_gap_fraction_of_c5a = total_gap_ordinary_prose / 579  # U0.6's C5a ordinary-prose total

        # ─── GATE 2 ──
        claude_anchor_report = []
        for anchor_label, page_ref, chunk_idx in _CLAUDE_ANCHORS:
            page_index = page_ref - 1
            page = page_by_index.get(page_index)
            if page is None:
                claude_anchor_report.append({
                    "anchor": anchor_label, "found": False,
                    "note": "page not in mapped set (zero live chunks or zero native chars)",
                })
                continue
            full_id = f"{census.CHEIRO_BOOK}_p{page_ref}_c{chunk_idx}"
            match = next((c for c in page["chunks"] if c["chunk_id"] == full_id), None)
            if match is None:
                claude_anchor_report.append({
                    "anchor": anchor_label, "found": False,
                    "note": f"expected chunk_id {full_id} not present among this page's live chunks",
                })
                continue
            siblings = [c for c in page["chunks"] if c["chunk_id"] != full_id and c["span_start"] is not None]
            disjoint = True
            if match["span_start"] is not None:
                for sib in siblings:
                    if not (match["span_end"] < sib["span_start"] or match["span_start"] > sib["span_end"]):
                        disjoint = False
                        break
            else:
                disjoint = False
            claude_anchor_report.append({
                "anchor": anchor_label, "found": True, "chunk_id": full_id,
                "span_start": match["span_start"], "span_end": match["span_end"],
                "span_len": match["span_len"], "match_ratio": match["match_ratio"],
                "disjoint_from_siblings": disjoint,
            })

        # ─── (c) match_ratio distribution ──
        ratios = sorted(r["match_ratio"] for r in all_chunk_records if r["match_ratio"] is not None)
        ratio_stats = {
            "n": len(ratios),
            "min": ratios[0] if ratios else None,
            "p10": _percentile(ratios, 10), "p25": _percentile(ratios, 25),
            "median": _percentile(ratios, 50), "p75": _percentile(ratios, 75),
            "p90": _percentile(ratios, 90),
            "max": ratios[-1] if ratios else None,
        }
        histogram = Counter()
        for r in ratios:
            bucket = min(int(r / 0.05), 19)
            histogram[bucket] += 1

        # ─── (d) coverage distribution ──
        coverages = sorted(p["coverage"] for p in page_records)
        coverage_stats = {
            "min": coverages[0] if coverages else None,
            "median": _percentile(coverages, 50) if coverages else None,
            "max": coverages[-1] if coverages else None,
        }
        lowest_coverage_pages = sorted(page_records, key=lambda p: p["coverage"])[:_LOWEST_COVERAGE_TOP_N]

        # ─── (e) monotonicity/overlap worst ──
        non_monotonic_pages = [p for p in page_records if not p["monotonic"]]
        overlap_pages = [p for p in page_records if p["overlap_token_count"] > 0]
        worst_mono = sorted(non_monotonic_pages, key=lambda p: -p["mono_violations"])[:_WORST_MONOTONIC_TOP_N]
        worst_overlap = sorted(overlap_pages, key=lambda p: -p["overlap_token_count"])[:_WORST_OVERLAP_TOP_N]

        output = {
            "oracle": oracle_desc,
            "source_pdf_sha256": pdf_sha256,
            "self_check_results": self_check_results,
            "mapped_page_count": len(page_records),
            "zero_chunk_page_count": len(zero_chunk_pages),
            "gate1": {
                "seeding_viable_page_count": len(seeding_viable_pages),
                "fraction_of_245": gate1_fraction,
                "total_gap_ordinary_prose": total_gap_ordinary_prose,
                "fraction_of_c5a_579": gate1_gap_fraction_of_c5a,
            },
            "claude_anchor_report": claude_anchor_report,
            "match_ratio_stats": ratio_stats,
            "match_ratio_histogram": {f"{b*0.05:.2f}-{(b+1)*0.05:.2f}": histogram.get(b, 0) for b in range(20)},
            "coverage_stats": coverage_stats,
            "lowest_coverage_pages": lowest_coverage_pages,
            "non_monotonic_page_count": len(non_monotonic_pages),
            "overlap_page_count": len(overlap_pages),
            "worst_monotonic_violations": worst_mono,
            "worst_overlap_pages": worst_overlap,
            "zero_chunk_pages": zero_chunk_pages,
            "c5b_recheck": {
                "expected_total": _EXPECTED_C5B_ORDINARY_PROSE_TOTAL,
                "regenerated_total": len(c5b_occurrences),
                "sits_in_mapped_span_count": sits_in_mapped_span,
                "garbage_like_count": garbage_like,
                "occurrences": c5b_occurrences,
            },
            "page_records": page_records,
        }

        SIDECAR_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {SIDECAR_PATH} ({SIDECAR_PATH.stat().st_size} bytes)")

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
    lines.append("# CHUNK-TO-NATIVE SPAN MAPPING PROBE — S80 U1 — Cheiro only")
    lines.append("")
    lines.append(
        "Read-only, diagnostics-only. Gates PATH D (re-ingest, seeding new chunk "
        "boundaries from existing chunk spans). PATH C (in-place text replacement) is "
        "RETIRED -- no align_chunk_to_native() written. No ChromaDB writes, no shadow "
        "collection, no re-ingestion. See scripts/span_mapping_probe_S80.py module "
        "docstring for full reuse/method detail."
    )
    lines.append("")
    lines.append(f"- Oracle: {d['oracle']}")
    lines.append(f"- source_pdf_sha256: `{d['source_pdf_sha256']}`")
    lines.append(f"- Mapped pages (native_char_count > 0, >=1 live chunk): {d['mapped_page_count']}")
    lines.append(f"- Zero-live-chunk pages (native_char_count > 0, 0 chunks): {d['zero_chunk_page_count']}")
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
    lines.append("## (a) GATE 1 — Seeding viability")
    lines.append("")
    g1 = d["gate1"]
    lines.append(f"- Pages monotonic AND overlap_token_count == 0: **{g1['seeding_viable_page_count']} / 245 ({g1['fraction_of_245']*100:.2f}%)**")
    lines.append(f"- Total gap ORDINARY-PROSE tokens across all mapped pages: **{g1['total_gap_ordinary_prose']}**")
    lines.append(f"- That as a fraction of U0.6's C5a ordinary-prose total (579): **{g1['fraction_of_c5a_579']*100:.2f}%**")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## (b) GATE 2 — Id mappability, CLAUDE.md-named anchors")
    lines.append("")
    lines.append("| Anchor | Found | chunk_id | span_start | span_end | span_len | match_ratio | Disjoint from siblings |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for a in d["claude_anchor_report"]:
        if not a["found"]:
            lines.append(f"| {a['anchor']} | NO | — | — | — | — | — | {a['note']} |")
            continue
        mr = f"{a['match_ratio']:.4f}" if a["match_ratio"] is not None else "N/A"
        lines.append(f"| {a['anchor']} | yes | {a['chunk_id']} | {a['span_start']} | {a['span_end']} | {a['span_len']} | {mr} | {a['disjoint_from_siblings']} |")
    lines.append("")
    lines.append(
        "A disjoint, high-match span means the anchor can be mapped to a new chunk id "
        "deterministically under Path D. Overlapping or low-match means it cannot, and the "
        "labelled set built on that anchor is at risk. No mappability ruling made here."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## (c) match_ratio distribution — ALL chunks")
    lines.append("")
    rs = d["match_ratio_stats"]
    lines.append(f"- n = {rs['n']}")
    lines.append(f"- min = {rs['min']:.4f}, p10 = {rs['p10']:.4f}, p25 = {rs['p25']:.4f}, median = {rs['median']:.4f}, p75 = {rs['p75']:.4f}, p90 = {rs['p90']:.4f}, max = {rs['max']:.4f}")
    lines.append("")
    lines.append("| Bucket | Count |")
    lines.append("|---|---|")
    for bucket, count in d["match_ratio_histogram"].items():
        lines.append(f"| {bucket} | {count} |")
    lines.append("")
    lines.append(
        "This distribution is the DERIVED input for a future seeding acceptance threshold. "
        "**No threshold is proposed here** — that is a design-chat ruling, with its own "
        "scope guard and tuning note, per instruction."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## (d) Coverage distribution per page")
    lines.append("")
    cs = d["coverage_stats"]
    lines.append(f"- min = {cs['min']:.4f}, median = {cs['median']:.4f}, max = {cs['max']:.4f}")
    lines.append("")
    lines.append(f"### {_LOWEST_COVERAGE_TOP_N} lowest-coverage pages")
    lines.append("")
    lines.append("| Rank | page_index | page_ref | coverage | gap_ordinary_prose_count | chunk_count |")
    lines.append("|---|---|---|---|---|---|")
    for i, p in enumerate(d["lowest_coverage_pages"], 1):
        lines.append(f"| {i} | {p['page_index']} | {p['page_ref']} | {p['coverage']:.4f} | {p['gap_ordinary_prose_count']} | {p['chunk_count']} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## (e) Monotonicity / overlap detail")
    lines.append("")
    lines.append(f"- Non-monotonic pages: **{d['non_monotonic_page_count']} / {d['mapped_page_count']}**")
    lines.append(f"- Pages with any overlap (overlap_token_count > 0): **{d['overlap_page_count']} / {d['mapped_page_count']}**")
    lines.append("")
    lines.append(f"### {_WORST_MONOTONIC_TOP_N} worst non-monotonic pages")
    lines.append("")
    if d["worst_monotonic_violations"]:
        for p in d["worst_monotonic_violations"]:
            lines.append(f"**page_index={p['page_index']} (page_ref={p['page_ref']})**, {p['mono_violations']} adjacent-pair violation(s):")
            lines.append("")
            lines.append("| chunk_id | span_start | span_end |")
            lines.append("|---|---|---|")
            for c in p["chunks"]:
                lines.append(f"| {c['chunk_id']} | {c['span_start']} | {c['span_end']} |")
            lines.append("")
    else:
        lines.append("(none — every mapped page is monotonic)")
        lines.append("")
    lines.append(f"### {_WORST_OVERLAP_TOP_N} worst overlap pages")
    lines.append("")
    if d["worst_overlap_pages"]:
        for p in d["worst_overlap_pages"]:
            lines.append(f"**page_index={p['page_index']} (page_ref={p['page_ref']})**, overlap_token_count={p['overlap_token_count']}:")
            lines.append("")
            lines.append("| chunk_id | span_start | span_end |")
            lines.append("|---|---|---|")
            for c in p["chunks"]:
                lines.append(f"| {c['chunk_id']} | {c['span_start']} | {c['span_end']} |")
            lines.append("")
    else:
        lines.append("(none — zero overlap on every mapped page)")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## (f) Zero-live-chunk pages (NOT span-mapped — recoverable under Path D)")
    lines.append("")
    lines.append("| page_index | page_ref | native_char_count | ordinary_prose_token_count |")
    lines.append("|---|---|---|---|")
    for p in d["zero_chunk_pages"]:
        lines.append(f"| {p['page_index']} | {p['page_ref']} | {p['native_char_count']} | {p['ordinary_prose_token_count']} |")
    lines.append("")
    lines.append(
        "Under Path C these pages were permanently empty (no corpus text to align "
        "against). Under Path D, a fresh re-ingest would create new chunks for these "
        "pages from scratch -- recoverable, not gated on span-mapping at all."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## (g) C5b ordinary-prose re-check (retires the U0.6 146-token caveat)")
    lines.append("")
    c5b = d["c5b_recheck"]
    lines.append(f"- Regenerated total: **{c5b['regenerated_total']}** (matches U0.6's already-reported {c5b['expected_total']} — fidelity-checked before this section was trusted)")
    lines.append(f"- Sits inside a span-mapped chunk (the token's own chunk has a valid, non-None span on this probe): **{c5b['sits_in_mapped_span_count']} / {c5b['regenerated_total']}**")
    lines.append(f"- OCR-garbage-like by the stated heuristic (repeated-char/short-unit run, or a 3+ run of same vowel/consonant class): **{c5b['garbage_like_count']} / {c5b['regenerated_total']}**")
    lines.append("")
    lines.append(
        "These two counts are NOT a partition — a token can be both (garbage sitting "
        "inside an otherwise well-mapped chunk), either, or neither. Both are reported "
        "as independent measurements, per instruction."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## (h) Recommendation")
    lines.append("")
    lines.append(
        "**None made.** No ruling on seeding viability, match_ratio acceptance thresholds, "
        "or Path D itself — report only, per instruction. The gate 1/2 numbers, the "
        "match_ratio and coverage distributions, the monotonicity/overlap detail, the "
        "zero-chunk-page list, and the C5b recheck above are the evidence for that ruling."
    )
    lines.append("")
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
