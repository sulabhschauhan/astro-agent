"""
scripts/probe_fc_retrieval.py

S68 F-C retrieval-gap evidence probe (diagnostics-only, throwaway,
read-only). Measure-first: reports observed ranks only, asserts
nothing, proposes no threshold changes. Does NOT modify
agent/interpretive/palm_reading.py, touch the support gate, change
production n, or add tests.

Purpose: F-C needs a design decision on whether the current variant-iii
doctrine-interrogative query template (`_build_feature_query`, S67 R1)
is the right retrieval template for heart-line/fingers, or whether a
variant-iv attribute-conditioned template does better -- and F-D needs
evidence on how much per-feature retrieval drifts when the query is
built from a different source-text scope (LEFT+RIGHT only vs.
+HAND_DETAIL). This script generates that evidence; it decides neither
question.

Same read-only introspection pattern as scripts/probe_pass3_chunks.py:
imports agent.interpretive.palm_reading's private helpers, no
production code touched. Confirmed descriptions (LEFT/RIGHT/HAND_DETAIL)
transplanted VERBATIM from .claude/read_prompt.md's three 2026-07-18 RUN
blocks -- reusing probe_pass3_chunks.py's own transplanted constants
rather than retyping them, per that script's own citation trail.

Retrieval depth is extended to n=10 for THIS PROBE ONLY (a plain
`ingestion.query_engine.search()` call with n_results=10) -- production
`_N_RESULTS_PER_FEATURE` (3) in palm_reading.py is never touched.

Scope: 3 features only (heart line, fingers, life line) -- the ones
F-C's design-chat brief and pass 3's ledger flagged as the sharpest
grounding gaps. ChromaDB retrieval only, no LLM calls.

## Query variants tested

1. BASELINE (variant-iii, current production template) -- built via
   palm_reading._resolve_feature_quality() + palm_reading.
   _build_feature_query() unmodified. _resolve_feature_quality's own
   _extract_quality() call takes only the FIRST non-generic clause
   from each source's confirmed field text (documented fail-open
   behavior in palm_reading.py) -- this is a real information-loss
   point worth having concrete evidence on, not asserted here as a
   defect.

2. VARIANT-IV CANDIDATE -- pure Python string assembly off the SAME
   confirmed field text: every non-absent source's text is comma-split
   (`text.rstrip(".").split(",")`, the same primitive
   palm_reading._extract_quality already uses), a leading bare
   "present" clause is dropped, and every remaining clause from every
   applicable source is joined (case-insensitive de-duplication,
   first-seen order) into "{feature noun} {clause1}, {clause2}, ...".
   No LLM, no hand-authored doctrine language, no clause deemed more
   "important" than another -- a strictly mechanical alternative to
   variant-iii's single-clause quality extraction.

Both variants are run twice per feature: (i) LEFT+RIGHT fields only
(Run A/B shape), (ii) LEFT+RIGHT+HAND_DETAIL (Run C shape) -- the F-D
source-scope axis. 3 features x 2 variants x 2 shapes = 12 ranked
n=10 lists.

## Target-chunk lookups (lookup only, not a judgment)
- heart line: flags, per rank, whether the chunk text contains
  "below the first finger" or "mount of jupiter" (case-insensitive
  substring) -- the positive-configuration doctrine region pass 3's
  ledger cited as ~p.158-159, never itself asserted as "the" answer.
- fingers: flags presence of chunk_id `cheiroslanguageo00chei_1_p98_c1`
  (the chunk pass 3 found CONTRADICTS the "long fingers -> intellect"
  claim -- "erroneous and misleading").
- life line: flags presence of chunk_id `cheiroslanguageo00chei_1_p134_c2`
  (the head-line/life-line-joining doctrine chunk pass 3 found present
  in Run A/B's gate but absent from Run C's).

Writes diagnostics/fc_retrieval_probe_S68.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.interpretive import palm_reading
from ingestion.query_engine import search
from scripts.probe_pass3_chunks import _HAND_DETAIL, _LEFT, _RIGHT

_REPORT_PATH = Path(__file__).resolve().parent.parent / "diagnostics" / "fc_retrieval_probe_S68.md"
_PROBE_N_RESULTS = 10
_SUPPORT_GATE_FLOOR = 0.30  # existing production floor, reported as a line marker only

_FEATURES = ("heart line", "fingers", "life line")

_HEART_LINE_NEEDLES = ("below the first finger", "mount of jupiter")
_FINGERS_TARGET_CHUNK = "cheiroslanguageo00chei_1_p98_c1"
_LIFE_LINE_TARGET_CHUNK = "cheiroslanguageo00chei_1_p134_c2"


def _build_variant_iv_query(feature: str, raw_texts: list[str]) -> str | None:
    """Pure Python string assembly off the confirmed field text -- see
    module docstring for the exact algorithm. No LLM, no doctrine
    language beyond the feature noun itself."""
    non_absent = [t for t in raw_texts if not palm_reading._is_absence(t)]
    if not non_absent:
        return None
    seen: set[str] = set()
    ordered_clauses: list[str] = []
    for t in non_absent:
        clauses = [c.strip() for c in t.rstrip(".").split(",")]
        for c in clauses:
            if not c:
                continue
            key = c.lower()
            if key == "present":
                continue
            if key not in seen:
                seen.add(key)
                ordered_clauses.append(c)
    if not ordered_clauses:
        return None
    noun = feature.split("/")[0]
    return f"{noun} " + ", ".join(ordered_clauses)


def _build_baseline_query(feature: str, raw_texts: list[str]) -> str | None:
    """Exact production variant-iii query -- palm_reading's own
    _resolve_feature_quality + _build_feature_query, unmodified."""
    quality = palm_reading._resolve_feature_quality(feature, raw_texts)
    if quality is None:
        return None
    return palm_reading._build_feature_query(feature, quality)


def _run_query(query: str) -> list[dict]:
    return search(query, n_results=_PROBE_N_RESULTS, book_name=palm_reading._CHEIRO_BOOK)


def _target_flags(feature: str, chunk: dict) -> list[str]:
    flags: list[str] = []
    low = chunk["text"].lower()
    if feature == "heart line":
        for needle in _HEART_LINE_NEEDLES:
            if needle in low:
                flags.append(f'contains "{needle}"')
    elif feature == "fingers":
        if chunk["chunk_id"] == _FINGERS_TARGET_CHUNK:
            flags.append(f"IS target chunk {_FINGERS_TARGET_CHUNK}")
    elif feature == "life line":
        if chunk["chunk_id"] == _LIFE_LINE_TARGET_CHUNK:
            flags.append(f"IS target chunk {_LIFE_LINE_TARGET_CHUNK}")
    return flags


def _fmt_ranked_table(results: list[dict], feature: str) -> list[str]:
    lines = ["| rank | chunk_id | page_ref | score | vs. 0.30 floor | target flags |",
             "|---|---|---|---|---|---|"]
    floor_marker_emitted = False
    for rank, r in enumerate(results, 1):
        if not floor_marker_emitted and r["score"] < _SUPPORT_GATE_FLOOR:
            lines.append("| -- | -- | -- | **0.30 support-gate floor** | -- | -- |")
            floor_marker_emitted = True
        vs_floor = "above" if r["score"] >= _SUPPORT_GATE_FLOOR else "below"
        flags = _target_flags(feature, r)
        flag_str = "; ".join(flags) if flags else "--"
        lines.append(
            f"| {rank} | `{r['chunk_id']}` | p.{r['page_ref']} | {r['score']:.4f} | {vs_floor} | {flag_str} |"
        )
    if not floor_marker_emitted:
        lines.append("| -- | -- | -- | (all {} results above the 0.30 floor) | -- | -- |".format(len(results)))
    return lines


def main() -> None:
    left_fields = palm_reading._parse_fields(_LEFT)
    right_fields = palm_reading._parse_fields(_RIGHT)
    hd_fields = palm_reading._parse_bullet_fields(_HAND_DETAIL)

    # (i) LEFT+RIGHT only shape
    texts_lr = palm_reading._gather_feature_texts(left_fields, right_fields, {})
    # (ii) +HAND_DETAIL shape (Run C)
    texts_lrh = palm_reading._gather_feature_texts(left_fields, right_fields, hd_fields)

    lines: list[str] = []
    lines.append("# F-C retrieval-gap evidence probe (S68)")
    lines.append("")
    lines.append(
        "Diagnostics-only, throwaway, read-only (`scripts/probe_fc_retrieval.py`). "
        "Measure-first: reports observed ranks only, asserts nothing, proposes no "
        "threshold changes. No production code touched (palm_reading.py, the "
        "support gate, and production `n` are all unmodified; retrieval depth "
        "here is extended to n=10 for THIS PROBE ONLY)."
    )
    lines.append("")
    lines.append(
        "Confirmed descriptions transplanted verbatim from "
        "`.claude/read_prompt.md`'s three 2026-07-18 RUN blocks, reusing "
        "`scripts/probe_pass3_chunks.py`'s own transplanted `_LEFT`/`_RIGHT`/"
        "`_HAND_DETAIL` constants directly (not retyped)."
    )
    lines.append("")
    lines.append(
        "Two query variants per feature, run against two source-text scopes "
        "each (the F-D axis): **BASELINE** = current production variant-iii "
        "template (`palm_reading._build_feature_query`, unmodified) at n=10; "
        "**VARIANT-IV** = pure Python string assembly off every comma-split "
        "clause of the confirmed field text (see script docstring for the "
        "exact algorithm), also at n=10. `LR` = LEFT+RIGHT fields only "
        "(Run A/B shape); `LRH` = +HAND_DETAIL (Run C shape)."
    )
    lines.append("")

    for feature in _FEATURES:
        lines.append(f"## {feature}")
        lines.append("")

        raw_lr = texts_lr.get(feature, [])
        raw_lrh = texts_lrh.get(feature, [])

        baseline_lr_q = _build_baseline_query(feature, raw_lr)
        baseline_lrh_q = _build_baseline_query(feature, raw_lrh)
        v4_lr_q = _build_variant_iv_query(feature, raw_lr)
        v4_lrh_q = _build_variant_iv_query(feature, raw_lrh)

        lines.append("### Query strings")
        lines.append("")
        lines.append("| Variant | Scope | Query |")
        lines.append("|---|---|---|")
        lines.append(f"| BASELINE (variant-iii) | LR | `{baseline_lr_q}` |")
        lines.append(f"| BASELINE (variant-iii) | LRH | `{baseline_lrh_q}` |")
        lines.append(f"| VARIANT-IV | LR | `{v4_lr_q}` |")
        lines.append(f"| VARIANT-IV | LRH | `{v4_lrh_q}` |")
        lines.append("")

        combos = [
            ("BASELINE / LR", baseline_lr_q),
            ("BASELINE / LRH", baseline_lrh_q),
            ("VARIANT-IV / LR", v4_lr_q),
            ("VARIANT-IV / LRH", v4_lrh_q),
        ]
        for label, query in combos:
            lines.append(f"### {label}")
            lines.append("")
            if query is None:
                lines.append("_(no query -- feature unresolvable from this source scope)_")
                lines.append("")
                continue
            results = _run_query(query)
            lines += _fmt_ranked_table(results, feature)
            lines.append("")

    lines.append("## Raw counts (measure-first summary, no interpretation)")
    lines.append("")
    lines.append("| Feature | Variant/Scope | Target-flag hits in top-10 | Rank of first target-flag hit |")
    lines.append("|---|---|---|---|")
    for feature in _FEATURES:
        raw_lr = texts_lr.get(feature, [])
        raw_lrh = texts_lrh.get(feature, [])
        combos = [
            ("BASELINE / LR", _build_baseline_query(feature, raw_lr)),
            ("BASELINE / LRH", _build_baseline_query(feature, raw_lrh)),
            ("VARIANT-IV / LR", _build_variant_iv_query(feature, raw_lr)),
            ("VARIANT-IV / LRH", _build_variant_iv_query(feature, raw_lrh)),
        ]
        for label, query in combos:
            if query is None:
                lines.append(f"| {feature} | {label} | N/A (no query) | N/A |")
                continue
            results = _run_query(query)
            hit_ranks = [
                rank for rank, r in enumerate(results, 1) if _target_flags(feature, r)
            ]
            count = len(hit_ranks)
            first = hit_ranks[0] if hit_ranks else "none in top-10"
            lines.append(f"| {feature} | {label} | {count} | {first} |")
    lines.append("")

    _REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report written to {_REPORT_PATH}")


if __name__ == "__main__":
    main()
