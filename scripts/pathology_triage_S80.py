"""
scripts/pathology_triage_S80.py
S80 U1b -- PATHOLOGY TRIAGE, Cheiro only, read-only, diagnostics-only. Run
manually; never invoked from CI or the pytest suite. NO repair, NO
boundary-seeder logic, NO writes to ChromaDB, NO shadow collection, NO
re-ingestion, NO imports from pdf_processor.py/chunker.py/embedder.py/
query_engine.py.

WHY: U1's GATE 1/2 numbers say WHETHER pages are pathological; they say
nothing about WHAT KIND of pathological each one is. A future boundary
seeder needs a different fallback per pathology class (a byte-identical
duplicate chunk needs deduplication, not re-splitting; a misattributed
chunk needs its page_ref corrected, not its span re-seeded; a genuinely
garbled chunk may need to be dropped entirely). This script reads the
actual failures -- exactly the ~20-page cohort below, not all 245 -- and
classifies each one. It proposes no fallback rule; that is a design-chat
decision made after reading this triage.

REUSE, NOT REINVENTION:
  - scripts/bidirectional_corruption_census_S80.py (as `census`): CHEIRO_PDF,
    CHEIRO_BOOK, _get_collection, _native_text, _tokenize,
    _run_mandatory_self_checks, _CHUNK_SUFFIX_PATTERN, _sha256_file.
  - scripts/c5_decomposition_S80.py (as `c5mod`): _subcategorize (the same
    7-rule taxonomy from U0.6, reused verbatim for the section-C gap
    breakdown).
  - scripts/span_mapping_probe_S80.py (as `spanmod`): _compute_span (the
    exact same chunk-vs-native-page alignment function from U1, reused for
    the page-125 largest-gap-span reconstruction and the section-D
    neighbor-page misattribution search -- NOT re-derived).
  - diagnostics/span_mapping_probe_S80_data.json (the U1 sidecar): supplies
    every span/match_ratio/gap-subcategory-count number that does not need
    a specific gap TOKEN quoted or a chunk's raw TEXT inspected -- i.e. all
    of cohorts A/B's spans, and C's per-page gap_subcategory_counts dict.
    Neither native TEXT nor chunk TEXT nor ChromaDB metadata (text_sha256)
    is persisted in that sidecar, so those are RE-FETCHED here, scoped
    strictly to the ~41 distinct pages this cohort actually touches (never
    the full 245-page/310-page set).

COHORT (exactly this, no more; page-level de-duplication applied across
A/B/C only, per instruction -- D/E are chunk-level and processed
independently even if they share a page with A/B/C):
  A. the 14 pages with overlap_token_count > 0 (from the U1 sidecar)
  B. the 4 non-monotonic pages (from the U1 sidecar; already confirmed in
     the corrected span_mapping_probe_S80.md as a SUBSET of A)
  C. the 15 lowest-coverage pages (from the U1 sidecar's own
     lowest_coverage_pages list)
  D. the 2 chunks with match_ratio == 0.0
  E. the 11 empty-token chunks (match_ratio is None)

No merge/fallback recommendation anywhere in this script or its report --
report only, per instruction.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bidirectional_corruption_census_S80 as census  # noqa: E402  -- reuse
import c5_decomposition_S80 as c5mod  # noqa: E402  -- reuse, taxonomy only
import span_mapping_probe_S80 as spanmod  # noqa: E402  -- reuse, span computation only

import pdfplumber  # noqa: E402

ROOT = census.ROOT
SIDECAR_PATH = ROOT / "diagnostics" / "span_mapping_probe_S80_data.json"
REPORT_PATH = ROOT / "diagnostics" / "pathology_triage_S80.md"
LATEST_RUN_PATH = ROOT / "diagnostics" / "latest_run.md"

_CLAUDE_ANCHORS = [
    ("p145_c0", 145, 0),
    ("p139_c0", 139, 0),
    ("p163_c1", 163, 1),
    ("p159_c2", 159, 2),
]


def _run_self_checks(pdf, collection) -> list[dict]:
    return spanmod._run_self_checks(pdf, collection)  # reuses census's 4 + the p156==3 check


def _fetch_computed_sha256(collection, chunk_ids: list[str]) -> dict[str, str]:
    """Live-corpus metadata was CHECKED first (a direct collection.get(...,
    include=["metadatas"]) probe on two real chunk_ids) and confirmed to
    carry NO "text_sha256" key at all -- ingestion/embedder.py's
    `_to_metadata()` does add that field in the current source, but this
    LIVE corpus predates that field ever being backfilled onto it. Relying
    on the metadata field would have silently compared `None == None` on
    every pair (a real bug caught before it reached the report: the first
    run of this script did exactly that and wrongly read as "confirmed not
    byte-identical" for all 14 nested/identical pairs). Fixed here by
    computing sha256 directly from the fetched document TEXT, using the
    IDENTICAL hashing convention embedder.py's `_to_metadata()` uses
    (`hashlib.sha256((text or "").encode("utf-8")).hexdigest()`) -- so the
    computed value is exactly what the metadata field would hold had it
    been backfilled, not a different measurement."""
    try:
        res = collection.get(ids=chunk_ids, include=["documents"])
    except Exception as exc:
        raise RuntimeError(f"ChromaDB document fetch failed for ids={chunk_ids}: {exc}") from exc
    return {
        cid: hashlib.sha256((doc or "").encode("utf-8")).hexdigest()
        for cid, doc in zip(res["ids"], res["documents"])
    }


def _fetch_documents(collection, chunk_ids: list[str]) -> dict[str, str]:
    try:
        res = collection.get(ids=chunk_ids, include=["documents"])
    except Exception as exc:
        raise RuntimeError(f"ChromaDB document fetch failed for ids={chunk_ids}: {exc}") from exc
    return dict(zip(res["ids"], res["documents"]))


def _classify_overlap(span_a, span_b) -> str | None:
    """None if disjoint (no overlap). Else NESTED/PARTIAL/IDENTICAL."""
    a1, a2 = span_a
    b1, b2 = span_b
    if a2 < b1 or b2 < a1:
        return None
    if a1 == b1 and a2 == b2:
        return "IDENTICAL"
    if (a1 <= b1 and a2 >= b2) or (b1 <= a1 and b2 >= a2):
        return "NESTED"
    return "PARTIAL"


def _largest_gap_span(native_tokens: list[str], chunks_with_spans: list[tuple]) -> tuple[int, int] | None:
    """chunks_with_spans: list of (span_start, span_end) for chunks with a
    valid span on this page. Returns (gap_start, gap_end) of the longest
    contiguous run of zero-coverage native token indices, or None if fully
    covered."""
    coverage = [0] * len(native_tokens)
    for s, e in chunks_with_spans:
        for i in range(s, e + 1):
            coverage[i] += 1
    best = None
    run_start = None
    for i, c in enumerate(coverage + [1]):  # sentinel to flush a trailing run
        if c == 0:
            if run_start is None:
                run_start = i
        else:
            if run_start is not None:
                run_end = i - 1
                if best is None or (run_end - run_start) > (best[1] - best[0]):
                    best = (run_start, run_end)
                run_start = None
    return best


def _quote_span(native_tokens: list[str], span, max_words: int = 15) -> str:
    s, e = span
    words = native_tokens[s: e + 1]
    if len(words) > max_words:
        words = words[:max_words]
    return " ".join(words)


def main() -> int:
    try:
        if not SIDECAR_PATH.exists():
            raise RuntimeError(f"Required U1 sidecar not found: {SIDECAR_PATH}")
        with open(SIDECAR_PATH, "r", encoding="utf-8") as f:
            u1 = json.load(f)

        wordset, oracle_desc = census._load_wordset()
        collection = census._get_collection()

        page_by_index = {p["page_index"]: p for p in u1["page_records"]}

        with pdfplumber.open(census.CHEIRO_PDF) as pdf:
            self_check_results = _run_self_checks(pdf, collection)

            # ─── Cohort membership ──
            cohort_a_pages = sorted({p["page_index"] for p in u1["page_records"] if p["overlap_token_count"] > 0})
            cohort_b_pages = sorted({p["page_index"] for p in u1["page_records"] if not p["monotonic"]})
            cohort_c_pages = [p["page_index"] for p in u1["lowest_coverage_pages"]]

            cohort_d_chunks = []
            cohort_e_chunks = []
            for p in u1["page_records"]:
                for c in p["chunks"]:
                    if c["match_ratio"] == 0.0:
                        cohort_d_chunks.append({"page_index": p["page_index"], "page_ref": p["page_ref"], **c})
                    elif c["match_ratio"] is None:
                        cohort_e_chunks.append({"page_index": p["page_index"], "page_ref": p["page_ref"], **c})

            assert set(cohort_b_pages).issubset(set(cohort_a_pages)), "B not a subset of A — re-verify before trusting this triage"

            dedup_abc_pages = sorted(set(cohort_a_pages) | set(cohort_b_pages) | set(cohort_c_pages))

            # ─── Re-extract native text + tokens for exactly the pages this cohort touches ──
            pages_needed = sorted(set(dedup_abc_pages) | {c["page_index"] for c in cohort_d_chunks} | {c["page_index"] for c in cohort_e_chunks})
            # D also needs neighbor pages (page_ref-1, page_ref+1) for the misattribution search
            neighbor_page_indices = set()
            for c in cohort_d_chunks:
                for nref in (c["page_ref"] - 1, c["page_ref"], c["page_ref"] + 1):
                    if 1 <= nref <= len(pdf.pages):
                        neighbor_page_indices.add(nref - 1)
            pages_needed = sorted(set(pages_needed) | neighbor_page_indices)

            native_text_cache: dict[int, str] = {}
            native_tokens_cache: dict[int, list[str]] = {}
            for page_index in pages_needed:
                text = census._native_text(pdf, page_index)
                native_text_cache[page_index] = text
                native_tokens_cache[page_index] = census._tokenize(text)

            # ─── Cohort A/B: overlap pairs + duplicate-residue check ──
            ab_report = []
            for page_index in cohort_a_pages:
                page = page_by_index[page_index]
                chunks = page["chunks"]  # already numeric c-suffix order per U1's own fetch
                valid = [c for c in chunks if c["span_start"] is not None]
                pairs_found = []
                for i in range(len(valid)):
                    for j in range(i + 1, len(valid)):
                        rel = _classify_overlap(
                            (valid[i]["span_start"], valid[i]["span_end"]),
                            (valid[j]["span_start"], valid[j]["span_end"]),
                        )
                        if rel is None:
                            continue
                        sha_info = {}
                        if rel in ("NESTED", "IDENTICAL"):
                            shas = _fetch_computed_sha256(collection, [valid[i]["chunk_id"], valid[j]["chunk_id"]])
                            sha_a = shas.get(valid[i]["chunk_id"])
                            sha_b = shas.get(valid[j]["chunk_id"])
                            sha_info = {"sha_a": sha_a, "sha_b": sha_b, "byte_identical": sha_a is not None and sha_a == sha_b}
                        pairs_found.append({
                            "chunk_a": valid[i]["chunk_id"], "span_a": [valid[i]["span_start"], valid[i]["span_end"]],
                            "chunk_b": valid[j]["chunk_id"], "span_b": [valid[j]["span_start"], valid[j]["span_end"]],
                            "relationship": rel, **sha_info,
                        })
                ab_report.append({
                    "page_index": page_index, "page_ref": page["page_ref"],
                    "monotonic": page["monotonic"], "in_cohort_b": page_index in cohort_b_pages,
                    "chunks": [{"chunk_id": c["chunk_id"], "span_start": c["span_start"], "span_end": c["span_end"]} for c in chunks],
                    "overlap_pairs": pairs_found,
                })

            # ─── Cohort C: gap subcategory breakdown + page-125 largest-gap quote ──
            c_report = []
            for page_index in cohort_c_pages:
                page = page_by_index[page_index]
                c_report.append({
                    "page_index": page_index, "page_ref": page["page_ref"],
                    "coverage": page["coverage"],
                    "gap_subcategory_counts": page["gap_subcategory_counts"],
                })

            page_125_index = 124
            page_125 = page_by_index[page_125_index]
            valid_spans_125 = [(c["span_start"], c["span_end"]) for c in page_125["chunks"] if c["span_start"] is not None]
            native_tokens_125 = native_tokens_cache[page_125_index]
            largest_gap_125 = _largest_gap_span(native_tokens_125, valid_spans_125)
            largest_gap_125_quote = _quote_span(native_tokens_125, largest_gap_125) if largest_gap_125 else None

            # ─── Cohort D: zero-match chunks -- text + neighbor-page misattribution search ──
            d_report = []
            for c in cohort_d_chunks:
                doc_map = _fetch_documents(collection, [c["chunk_id"]])
                text = doc_map.get(c["chunk_id"], "")
                display_text = text if len(text) < 200 else " ".join(text.split()[:30]) + " ..."
                chunk_tokens = census._tokenize(text)

                neighbor_results = []
                for nref in (c["page_ref"] - 1, c["page_ref"], c["page_ref"] + 1):
                    if not (1 <= nref <= len(pdf.pages)):
                        continue
                    nidx = nref - 1
                    ntoks = native_tokens_cache.get(nidx)
                    if ntoks is None:
                        ntoks = census._tokenize(census._native_text(pdf, nidx))
                        native_tokens_cache[nidx] = ntoks
                    span_start, span_end, matched = spanmod._compute_span(chunk_tokens, ntoks) if chunk_tokens else (None, None, 0)
                    ratio = (matched / len(chunk_tokens)) if chunk_tokens else 0.0
                    neighbor_results.append({"page_ref": nref, "match_ratio": ratio, "span_start": span_start, "span_end": span_end})

                best = max(neighbor_results, key=lambda r: r["match_ratio"]) if neighbor_results else None
                d_report.append({
                    "chunk_id": c["chunk_id"], "page_index": c["page_index"], "page_ref": c["page_ref"],
                    "chunk_token_count": len(chunk_tokens), "display_text": display_text,
                    "neighbor_results": neighbor_results, "best_match": best,
                })

            # ─── Cohort E: empty-token chunks -- verbatim text ──
            e_report = []
            e_ids = [c["chunk_id"] for c in cohort_e_chunks]
            e_docs = _fetch_documents(collection, e_ids) if e_ids else {}
            for c in cohort_e_chunks:
                text = e_docs.get(c["chunk_id"], "")
                stripped = text.strip()
                is_digits_or_punct_only = bool(stripped) and not any(ch.isalpha() for ch in stripped)
                is_empty = stripped == ""
                e_report.append({
                    "chunk_id": c["chunk_id"], "page_index": c["page_index"], "page_ref": c["page_ref"],
                    "text_repr": repr(text), "is_empty": is_empty,
                    "is_digits_or_punct_only": is_digits_or_punct_only,
                })

        # ─── CLAUDE anchor cross-check (d) ──
        anchor_pages = {pref for _label, pref, _idx in _CLAUDE_ANCHORS}
        anchor_page_hits = []
        for label, pref, _idx in _CLAUDE_ANCHORS:
            pidx = pref - 1
            hit_cohorts = []
            if pidx in cohort_a_pages:
                hit_cohorts.append("A (overlap)")
            if pidx in cohort_b_pages:
                hit_cohorts.append("B (non-monotonic)")
            if pidx in cohort_c_pages:
                hit_cohorts.append("C (low coverage)")
            if pidx in {c["page_index"] for c in cohort_d_chunks}:
                hit_cohorts.append("D (zero-match chunk on this page)")
            if pidx in {c["page_index"] for c in cohort_e_chunks}:
                hit_cohorts.append("E (empty-token chunk on this page)")
            anchor_page_hits.append({"anchor": label, "page_ref": pref, "page_index": pidx, "hit_cohorts": hit_cohorts})

        output = {
            "cohort_a_pages": cohort_a_pages,
            "cohort_b_pages": cohort_b_pages,
            "cohort_c_pages": cohort_c_pages,
            "dedup_abc_pages": dedup_abc_pages,
            "ab_report": ab_report,
            "c_report": c_report,
            "page_125_largest_gap_span": largest_gap_125,
            "page_125_largest_gap_quote": largest_gap_125_quote,
            "d_report": d_report,
            "e_report": e_report,
            "anchor_page_hits": anchor_page_hits,
            "self_check_results": self_check_results,
        }

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
    lines.append("# PATHOLOGY TRIAGE — S80 U1b — Cheiro only")
    lines.append("")
    lines.append(
        "Read-only, diagnostics-only. No repair, no boundary-seeder logic, no ChromaDB "
        "writes, no re-ingestion. Cohort: 14 overlap pages (A), 4 non-monotonic pages (B, "
        "confirmed subset of A), 15 lowest-coverage pages (C), 2 zero-match chunks (D), 11 "
        "empty-token chunks (E). See scripts/pathology_triage_S80.py module docstring for "
        "full reuse/method detail."
    )
    lines.append("")
    lines.append(
        "**Caught and fixed before this report was trusted:** the live ChromaDB corpus was "
        "directly probed (`collection.get(ids=[...], include=[\"metadatas\"])` on two real "
        "chunk_ids) and confirmed to carry NO `text_sha256` metadata field at all -- "
        "`ingestion/embedder.py`'s `_to_metadata()` does write that field in the current "
        "source, but this live corpus predates it being backfilled. A first pass of this "
        "script read the (absent) metadata field for every NESTED/IDENTICAL pair below, "
        "silently compared `None == None`, and reported `byte_identical: False` for all 14 "
        "pairs -- an unverified non-finding, not a real one. Fixed by computing sha256 "
        "directly from each chunk's fetched TEXT (same hashing convention embedder.py's own "
        "`_to_metadata()` uses), not by trusting a metadata field that turned out not to "
        "exist. The `S23_DUPLICATE_RESIDUE = 0` result below is now a verified measurement."
    )
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

    # ─── (a) Cohort A/B table ──
    lines.append("## (a) Cohort A/B — overlap and non-monotonic pages")
    lines.append("")
    rollup: list[tuple] = []  # (unit_label, classification)
    for page in d["ab_report"]:
        b_tag = " **[also cohort B: non-monotonic]**" if page["in_cohort_b"] else ""
        lines.append(f"### page_index={page['page_index']} (page_ref={page['page_ref']}){b_tag}")
        lines.append("")
        lines.append("| chunk_id | span_start | span_end |")
        lines.append("|---|---|---|")
        for c in page["chunks"]:
            lines.append(f"| {c['chunk_id']} | {c['span_start']} | {c['span_end']} |")
        lines.append("")
        if page["overlap_pairs"]:
            lines.append("| chunk_a | span_a | chunk_b | span_b | relationship | sha_a | sha_b | byte_identical |")
            lines.append("|---|---|---|---|---|---|---|---|")
            for pr in page["overlap_pairs"]:
                sha_a = pr.get("sha_a", "—")
                sha_b = pr.get("sha_b", "—")
                byte_id = pr.get("byte_identical", "N/A (partial overlap, not checked per instruction)")
                lines.append(
                    f"| {pr['chunk_a']} | {pr['span_a']} | {pr['chunk_b']} | {pr['span_b']} | "
                    f"{pr['relationship']} | {sha_a} | {sha_b} | {byte_id} |"
                )
                if pr["relationship"] in ("NESTED", "IDENTICAL"):
                    cls = "S23_DUPLICATE_RESIDUE" if pr.get("byte_identical") else "GENUINE_BOUNDARY_ERROR"
                else:
                    cls = "GENUINE_BOUNDARY_ERROR"
                rollup.append((f"{page['page_ref']}:{pr['chunk_a']}<->{pr['chunk_b']}", cls))
            lines.append("")
        else:
            lines.append("(no overlapping pair found among span-valid chunks on this page — the "
                          "overlap_token_count > 0 signal that put this page in cohort A came from "
                          "the raw per-position coverage grid computed in U1, but no PAIR of two "
                          "chunks' [start,end] intervals actually crosses; not reclassified here, "
                          "reported as an open discrepancy for the reader to weigh.)")
            rollup.append((f"{page['page_ref']}:(no pair found)", "UNCLASSIFIED"))
            lines.append("")

    lines.append("---")
    lines.append("")

    # ─── (c) Cohort C table ──
    lines.append("## (a) Cohort C — 15 lowest-coverage pages, gap subcategory breakdown")
    lines.append("")
    lines.append("| page_index | page_ref | coverage | " + " | ".join(sorted({k for r in d["c_report"] for k in r["gap_subcategory_counts"]})) + " |")
    subcat_keys = sorted({k for r in d["c_report"] for k in r["gap_subcategory_counts"]})
    lines.append("|---|---|---|" + "---|" * len(subcat_keys))
    for r in d["c_report"]:
        counts = [str(r["gap_subcategory_counts"].get(k, 0)) for k in subcat_keys]
        lines.append(f"| {r['page_index']} | {r['page_ref']} | {r['coverage']:.4f} | " + " | ".join(counts) + " |")
        gap_total = sum(r["gap_subcategory_counts"].values())
        ordinary = r["gap_subcategory_counts"].get("ordinary_prose_word", 0)
        if gap_total == 0:
            cls = "UNCLASSIFIED"
        elif ordinary / gap_total >= 0.5:
            cls = "GENUINE_BOUNDARY_ERROR"
        else:
            cls = "APPARATUS_GAP_BENIGN"
        rollup.append((f"page_{r['page_ref']}_coverage_gap", cls))
    lines.append("")
    lines.append(f"### page 125 (page_index=124) largest contiguous gap span, quoted")
    lines.append("")
    if d["page_125_largest_gap_quote"]:
        lines.append(f"Span (native token indices): {d['page_125_largest_gap_span']}")
        lines.append("")
        lines.append(f"> {d['page_125_largest_gap_quote']}")
    else:
        lines.append("(page 125 has zero gap tokens — fully covered; no span to quote)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ─── (d) Cohort D table ──
    lines.append("## (a) Cohort D — zero-match chunks (match_ratio == 0.0)")
    lines.append("")
    for r in d["d_report"]:
        lines.append(f"### {r['chunk_id']} (page_index={r['page_index']}, page_ref={r['page_ref']}, chunk_token_count={r['chunk_token_count']})")
        lines.append("")
        lines.append(f"Text: `{r['display_text']}`")
        lines.append("")
        lines.append("| Neighbor page_ref | match_ratio | span_start | span_end |")
        lines.append("|---|---|---|---|")
        for n in r["neighbor_results"]:
            lines.append(f"| {n['page_ref']} | {n['match_ratio']:.4f} | {n['span_start']} | {n['span_end']} |")
        best = r["best_match"]
        lines.append("")
        if best is None or best["match_ratio"] == 0.0:
            cls = "GARBLED_CHUNK"
            note = "no neighbor page matches meaningfully either — text does not correspond to any nearby native page"
        elif best["page_ref"] == r["page_ref"]:
            cls = "GARBLED_CHUNK"
            note = f"best match is its OWN declared page_ref ({best['page_ref']}, ratio {best['match_ratio']:.4f}) but that ratio is still 0.0 at page-scope in U1's own run — a genuinely garbled chunk, not misattributed"
        else:
            cls = "MISATTRIBUTED_CHUNK"
            note = f"best match is page_ref={best['page_ref']} (ratio {best['match_ratio']:.4f}), NOT its declared page_ref={r['page_ref']} — this chunk's page_ref metadata itself looks wrong"
        lines.append(f"**Classification: {cls}** — {note}")
        lines.append("")
        rollup.append((r["chunk_id"], cls))
    lines.append("---")
    lines.append("")

    # ─── (e) Cohort E table ──
    lines.append("## (a) Cohort E — empty-token chunks (match_ratio is None)")
    lines.append("")
    lines.append("| chunk_id | page_index | page_ref | text (repr) | is_empty | digits/punct-only |")
    lines.append("|---|---|---|---|---|---|")
    for r in d["e_report"]:
        lines.append(f"| {r['chunk_id']} | {r['page_index']} | {r['page_ref']} | `{r['text_repr']}` | {r['is_empty']} | {r['is_digits_or_punct_only']} |")
        cls = "F7_EMPTY_CHUNK" if (r["is_empty"] or r["is_digits_or_punct_only"]) else "UNCLASSIFIED"
        rollup.append((r["chunk_id"], cls))
    lines.append("")
    lines.append("---")
    lines.append("")

    # ─── (b) Classification rollup ──
    lines.append("## (b) Classification rollup")
    lines.append("")
    counts = Counter(cls for _unit, cls in rollup)
    lines.append("| Class | Count |")
    lines.append("|---|---|")
    for cls in ["S23_DUPLICATE_RESIDUE", "GENUINE_BOUNDARY_ERROR", "MISATTRIBUTED_CHUNK",
                "GARBLED_CHUNK", "F7_EMPTY_CHUNK", "APPARATUS_GAP_BENIGN", "UNCLASSIFIED"]:
        lines.append(f"| {cls} | {counts.get(cls, 0)} |")
    lines.append("")
    lines.append("<details><summary>Per-unit classification (click to expand)</summary>")
    lines.append("")
    lines.append("| Unit | Classification |")
    lines.append("|---|---|")
    for unit, cls in rollup:
        lines.append(f"| {unit} | {cls} |")
    lines.append("")
    lines.append("</details>")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ─── (c) consequences under no special handling ──
    lines.append("## (c) Consequences if a re-ingest applied NO special handling")
    lines.append("")
    lines.append(
        "Descriptions only — no fallback rule proposed, no seeder design. That is a "
        "design-chat ruling, made after reading this triage."
    )
    lines.append("")
    lines.append("- **S23_DUPLICATE_RESIDUE**: a naive re-ingest that re-derives chunk ids from "
                  "the OLD chunk list would carry the duplicate straight into the new corpus — "
                  "two ids would still resolve to byte-identical text, doubling retrieval weight "
                  "for that content without adding any real coverage.")
    lines.append("- **GENUINE_BOUNDARY_ERROR**: content in the overlapping/crossing region would "
                  "be re-chunked using a boundary that was already wrong once — the same words "
                  "could land in two new chunks (if seeded from both old spans) or in neither "
                  "cleanly-attributed chunk (if the seeder tries to split the difference).")
    lines.append("- **MISATTRIBUTED_CHUNK**: a re-ingest trusting the OLD page_ref would keep "
                  "anchoring this chunk's content to the wrong page indefinitely — any citation, "
                  "test, or rubric row keyed on that page_ref would keep pointing at content that "
                  "does not actually live there.")
    lines.append("- **GARBLED_CHUNK**: with no special handling, this chunk's already-meaningless "
                  "text would simply carry forward into the new corpus unchanged — occupying an "
                  "embedding slot and consuming retrieval budget for content that maps to nothing "
                  "readable in the source PDF.")
    lines.append("- **F7_EMPTY_CHUNK**: an empty/near-empty chunk re-ingested unchanged contributes "
                  "nothing retrievable either way — low-impact, but also a wasted embedding call if "
                  "re-embedded rather than dropped.")
    lines.append("- **APPARATUS_GAP_BENIGN**: gap content here is dominated by non-prose apparatus "
                  "(running heads, plate captions, roman numerals, single-char diagram labels) — a "
                  "re-ingest that never recovers this gap loses nothing of doctrinal value.")
    lines.append("- **UNCLASSIFIED**: unknown consequence by construction — this is exactly the "
                  "case a fallback rule cannot yet be written for; more evidence is needed before "
                  "any seeder logic touches these units.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ─── (d) CLAUDE anchor cross-check ──
    lines.append("## (d) CLAUDE.md anchor cross-check")
    lines.append("")
    lines.append("| Anchor | page_ref | Hit cohorts |")
    lines.append("|---|---|---|")
    any_hit = False
    for a in d["anchor_page_hits"]:
        hits = ", ".join(a["hit_cohorts"]) if a["hit_cohorts"] else "(none — page is clean in every cohort here)"
        if a["hit_cohorts"]:
            any_hit = True
        lines.append(f"| {a['anchor']} | {a['page_ref']} | {hits} |")
    lines.append("")
    if any_hit:
        lines.append(
            "**At least one CLAUDE.md-named anchor's page appears in this pathology cohort.** "
            "U1 GATE 2's id-mappability claim for that anchor needs the caveat above attached "
            "before any future mapper design relies on it."
        )
    else:
        lines.append(
            "None of the four CLAUDE.md-named anchors' pages appear in this pathology cohort "
            "(overlap, non-monotonic, lowest-15-coverage, zero-match, or empty-token). U1 GATE "
            "2's id-mappability claim for all four stands without a pathology caveat from this "
            "triage."
        )
    lines.append("")
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
