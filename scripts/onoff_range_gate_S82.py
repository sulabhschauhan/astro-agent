"""
scripts/onoff_range_gate_S82.py

S82 prompt 5 (three-arm version): OFF/ON/WIDE comparison of the page-range
gate at and beyond production depth, across all 10 _FEATURE_REGISTRY
features. _FEATURE_PAGE_FILTER_ENABLED is never flipped -- module state is
untouched.

  OFF  : search(query, n_results=_N_RESULTS_PER_FEATURE, book_name=_CHEIRO_BOOK)
  ON   : palm_reading._search_with_page_filter(feature, query) -- real
         production function, called directly.
  WIDE : search(query, n_results=_WIDE_N, book_name=_CHEIRO_BOOK) -- unfiltered,
         deeper. Diagnostic-only depth; never passed to any production caller.

Inputs: the SAME confirmed LEFT/RIGHT/HAND_DETAIL description texts as
scripts/retrieval_rank_probe_S81.py, imported verbatim from
scripts/probe_pass3_chunks.py, not retyped.

Pre-search guards (ported from retrieval_rank_probe_S81.py, same three
assertions, same fail-stop discipline): quality is str, no digit in the
query, template shape present. A guard failure stops the script.

No relevance scoring. The only labelling applied to WIDE results is a
mechanical page_ref-in-range check, not a relevance judgement. No
comparison to the six JSON _comment target chunk_ids (never human-verified,
reconciled against the pre-correction ranges). Writes
diagnostics/onoff_range_gate_S82.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from agent.interpretive import palm_reading
except Exception as exc:  # noqa: BLE001
    print(f"FATAL: could not import agent.interpretive.palm_reading: {exc}")
    sys.exit(1)

try:
    from ingestion.query_engine import search
except Exception as exc:  # noqa: BLE001
    print(f"FATAL: could not import ingestion.query_engine.search: {exc}")
    sys.exit(1)

try:
    from scripts.probe_pass3_chunks import _HAND_DETAIL, _LEFT, _RIGHT
except Exception as exc:  # noqa: BLE001
    print(f"FATAL: could not import confirmed field texts from scripts/probe_pass3_chunks.py: {exc}")
    sys.exit(1)

_REPORT_PATH = Path(__file__).resolve().parent.parent / "diagnostics" / "onoff_range_gate_S82.md"
_DUMP_CHARS = 200

_ALL_FEATURES = palm_reading._FEATURE_REGISTRY  # all 10, registry order
_GATE = palm_reading._N_RESULTS_PER_FEATURE      # read-only reference, never hardcoded
_CHEIRO_BOOK = palm_reading._CHEIRO_BOOK          # read-only reference, never hardcoded

# Diagnostic-only depth for the WIDE arm. ~3x the production gate -- enough
# to reveal whether in-range doctrine exists just below the production
# cutoff. Scope guard: this script only; never passed to
# _search_with_page_filter or any production caller. Tuning note: if
# in-range chunks cluster at ranks 8-10 below, re-run at 20 before
# concluding depth is sufficient.
_WIDE_N = 10

_embedding_call_count = 0


def _build_production_query(feature: str, raw_texts: list[str]) -> tuple[str | None, str | None]:
    """Mirrors retrieval_rank_probe_S81.py's own helper exactly: unmodified
    palm_reading._resolve_feature_quality -> palm_reading._build_feature_query."""
    try:
        quality = palm_reading._resolve_feature_quality(feature, raw_texts)
    except Exception as exc:  # noqa: BLE001
        print(f"FATAL: _resolve_feature_quality raised for feature={feature!r}: {exc}")
        sys.exit(1)
    if quality is None:
        return None, None
    try:
        query = palm_reading._build_feature_query(feature, quality)
    except Exception as exc:  # noqa: BLE001
        print(f"FATAL: _build_feature_query raised for feature={feature!r}, quality={quality!r}: {exc}")
        sys.exit(1)
    return query, quality


def _guard_query(feature: str, query: str, quality: str) -> None:
    """The three mandatory pre-search assertions, ported verbatim from
    retrieval_rank_probe_S81.py. A failure STOPS the script -- the failing
    assertion is the finding, never worked around."""
    print(f"[{feature}] quality={quality!r}")
    print(f"[{feature}] query={query!r}")
    assert isinstance(quality, str), f"quality must be str, got {type(quality)} for feature={feature!r}"
    assert not any(ch.isdigit() for ch in query), f"digit in query — int/str mix-up: {query!r}"
    assert "meaning and indications" in query, f"template shape unexpected: {query!r}"


def _in_range(page_range: tuple[int, int] | None, page_ref: int) -> bool:
    if page_range is None:
        return True  # null range: every result counts as in-range by definition
    start, end = page_range
    return start <= page_ref <= end


def main() -> None:
    global _embedding_call_count
    failures_off = 0
    failures_on = 0
    failures_wide = 0

    try:
        left_fields = palm_reading._parse_fields(_LEFT)
        right_fields = palm_reading._parse_fields(_RIGHT)
        hd_fields = palm_reading._parse_bullet_fields(_HAND_DETAIL)
        texts_lrh = palm_reading._gather_feature_texts(left_fields, right_fields, hd_fields)
    except Exception as exc:  # noqa: BLE001
        print(f"FATAL: field parsing / gather raised: {exc}")
        sys.exit(1)

    lines: list[str] = []
    lines.append("# S82 Prompt 5 — OFF/ON/WIDE page-range gate comparison\n")
    lines.append(
        f"`_FEATURE_PAGE_FILTER_ENABLED` is never flipped (stays `False` "
        f"module-wide); ON calls `palm_reading._search_with_page_filter()` "
        f"directly. OFF/ON query at production depth `_N_RESULTS_PER_FEATURE` "
        f"= {_GATE}; WIDE queries unfiltered at `_WIDE_N` = {_WIDE_N} "
        f"(diagnostic-only depth, never used by production). Book: "
        f"`{_CHEIRO_BOOK}`. No relevance scoring — WIDE's in-range/out-of-range "
        f"label is a mechanical page_ref comparison only. No comparison to "
        f"the six JSON `_comment` chunk_ids.\n"
    )

    # ── pre-search guard, all 10 features ───────────────────────────────
    lines.append("## Pre-search guard\n")
    per_feature_query: dict[str, str] = {}
    guard_failure: str | None = None

    for feature in _ALL_FEATURES:
        raw_texts = texts_lrh.get(feature, [])
        query, quality = _build_production_query(feature, raw_texts)
        if query is None:
            lines.append(f"- **{feature}**: quality resolved to None — SKIPPED, no search issued.")
            continue
        try:
            _guard_query(feature, query, quality)
        except AssertionError as exc:
            guard_failure = f"{feature}: {exc}"
            lines.append(f"- **{feature}**: ASSERTION FAILED — `{exc}`")
            break
        per_feature_query[feature] = query
        lines.append(f"- **{feature}**: quality=`{quality}` — query=`{query}` — PASSED all 3 assertions")

    lines.append("")

    if guard_failure is not None:
        lines.append(f"**GUARD FAILURE: {guard_failure} — STOPPING. No search issued.**")
        _REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        _REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
        print(f"Report written to {_REPORT_PATH}")
        print(f"GUARD FAILURE: {guard_failure}")
        sys.exit(1)

    # ── per-feature OFF/ON/WIDE searches ─────────────────────────────────
    per_feature_off: dict[str, list[dict]] = {}
    per_feature_on: dict[str, list[dict]] = {}
    per_feature_wide: dict[str, list[dict]] = {}

    for feature in _ALL_FEATURES:
        if feature not in per_feature_query:
            per_feature_off[feature] = []
            per_feature_on[feature] = []
            per_feature_wide[feature] = []
            continue
        query = per_feature_query[feature]

        try:
            per_feature_off[feature] = search(query, n_results=_GATE, book_name=_CHEIRO_BOOK)
            _embedding_call_count += 1
        except Exception as exc:  # noqa: BLE001
            failures_off += 1
            print(f"FAILED OFF path for feature={feature!r}: {exc}")
            per_feature_off[feature] = []

        try:
            per_feature_on[feature] = palm_reading._search_with_page_filter(feature, query)
            _embedding_call_count += 1
        except Exception as exc:  # noqa: BLE001
            failures_on += 1
            print(f"FAILED ON path for feature={feature!r}: {exc}")
            per_feature_on[feature] = []

        try:
            per_feature_wide[feature] = search(query, n_results=_WIDE_N, book_name=_CHEIRO_BOOK)
            _embedding_call_count += 1
        except Exception as exc:  # noqa: BLE001
            failures_wide += 1
            print(f"FAILED WIDE path for feature={feature!r}: {exc}")
            per_feature_wide[feature] = []

    # ── THE DECIDING TABLE, first ─────────────────────────────────────────
    lines.append("## The deciding table\n")
    lines.append(
        "| feature | verified range | OFF: n of {gate} out-of-range | "
        "WIDE: ranks of in-range chunks | WIDE: n of {wide} in-range | "
        "ON chunk_ids shared with OFF |".format(gate=_GATE, wide=_WIDE_N)
    )
    lines.append("|---|---|---|---|---|---|")

    for feature in _ALL_FEATURES:
        page_range = palm_reading._FEATURE_PAGE_RANGES.get(feature)
        range_str = f"{page_range[0]}-{page_range[1]}" if page_range else "null"
        off = per_feature_off.get(feature, [])
        on = per_feature_on.get(feature, [])
        wide = per_feature_wide.get(feature, [])
        off_ids = {r["chunk_id"] for r in off}
        on_ids = {r["chunk_id"] for r in on}

        if page_range is None:
            off_outside_str = "n/a (null range)"
        else:
            start, end = page_range
            off_outside = sum(1 for r in off if not _in_range(page_range, r.get("page_ref", -1)))
            off_outside_str = str(off_outside)

        wide_in_ranks = [
            rank for rank, r in enumerate(wide, 1)
            if _in_range(page_range, r.get("page_ref", -1))
        ]
        wide_ranks_str = ",".join(str(r) for r in wide_in_ranks) if wide_in_ranks else "(none)"
        wide_in_count = len(wide_in_ranks)

        shared = len(off_ids & on_ids)
        lines.append(
            f"| {feature} | {range_str} | {off_outside_str} | {wide_ranks_str} | "
            f"{wide_in_count} of {len(wide)} | {shared} |"
        )

    lines.append("")

    # ── Side-by-side per feature, all three arms ─────────────────────────
    lines.append("## Side-by-side per feature (all three arms)\n")
    for feature in _ALL_FEATURES:
        page_range = palm_reading._FEATURE_PAGE_RANGES.get(feature)
        range_str = f"{page_range[0]}-{page_range[1]}" if page_range else "null"
        lines.append(f"### {feature} (range: {range_str})\n")

        off = per_feature_off.get(feature, [])
        on = per_feature_on.get(feature, [])
        wide = per_feature_wide.get(feature, [])

        lines.append("**OFF:**\n")
        if not off:
            lines.append("(no results)\n")
        else:
            lines.append("| chunk_id | page_ref | score | text (first 200 chars) |")
            lines.append("|---|---|---|---|")
            for r in off:
                excerpt = r["text"][:_DUMP_CHARS].replace("\n", " ").replace("|", "\\|")
                lines.append(f"| `{r['chunk_id']}` | {r['page_ref']} | {r['score']:.4f} | {excerpt} |")
            lines.append("")

        lines.append("**ON:**\n")
        if not on:
            lines.append("(no results)\n")
        else:
            lines.append("| chunk_id | page_ref | score | text (first 200 chars) |")
            lines.append("|---|---|---|---|")
            for r in on:
                excerpt = r["text"][:_DUMP_CHARS].replace("\n", " ").replace("|", "\\|")
                lines.append(f"| `{r['chunk_id']}` | {r['page_ref']} | {r['score']:.4f} | {excerpt} |")
            lines.append("")

        lines.append(f"**WIDE (n={_WIDE_N}, in-range marked by mechanical page_ref check only):**\n")
        if not wide:
            lines.append("(no results)\n")
        else:
            lines.append("| rank | chunk_id | page_ref | in-range? | score | text (first 200 chars) |")
            lines.append("|---|---|---|---|---|---|")
            for rank, r in enumerate(wide, 1):
                excerpt = r["text"][:_DUMP_CHARS].replace("\n", " ").replace("|", "\\|")
                in_range_str = "in-range" if _in_range(page_range, r.get("page_ref", -1)) else "out-of-range"
                lines.append(
                    f"| {rank} | `{r['chunk_id']}` | {r['page_ref']} | {in_range_str} | "
                    f"{r['score']:.4f} | {excerpt} |"
                )
            lines.append("")

    # ── markings/other features null-range identity check ───────────────
    lines.append("## markings/other features — null-range identity check\n")
    off_marks = per_feature_off.get("markings/other features", [])
    on_marks = per_feature_on.get("markings/other features", [])
    wide_marks = per_feature_wide.get("markings/other features", [])
    off_marks_ids = [r["chunk_id"] for r in off_marks]
    on_marks_ids = [r["chunk_id"] for r in on_marks]
    identical = off_marks_ids == on_marks_ids
    lines.append(f"- OFF chunk_ids (order-sensitive): {off_marks_ids}")
    lines.append(f"- ON chunk_ids (order-sensitive): {on_marks_ids}")
    lines.append(f"- WIDE result count: {len(wide_marks)} (all count as in-range by definition, null range)")
    if identical:
        lines.append("- **IDENTICAL — correct: null range means ON and OFF are the same call.**")
    else:
        lines.append(
            "- **MISMATCH — null-range branch is NOT returning identical "
            "results. Something is wrong with the null-range branch.**"
        )
    lines.append("")

    lines.append(f"## Embedding calls made\n\nTotal: **{_embedding_call_count}**\n")
    lines.append("## Failures\n")
    lines.append(f"- OFF arm failures: **{failures_off}**")
    lines.append(f"- ON arm failures: **{failures_on}**")
    lines.append(f"- WIDE arm failures: **{failures_wide}**")
    total_failures = failures_off + failures_on + failures_wide
    lines.append(f"- Total: **{total_failures}**")
    if total_failures:
        lines.append(
            "\nA nonzero failure count means this comparison is PARTIAL -- "
            "do not treat it as complete."
        )

    try:
        _REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        _REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        print(f"FAILED writing report to {_REPORT_PATH}: {exc}")
        raise

    print(f"Report written to {_REPORT_PATH}")
    print(f"Total embedding calls: {_embedding_call_count}")
    print(f"Total failures: {total_failures} (OFF={failures_off}, ON={failures_on}, WIDE={failures_wide})")


if __name__ == "__main__":
    main()
