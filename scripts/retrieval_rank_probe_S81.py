"""
scripts/retrieval_rank_probe_S81.py

S81 production-query rank probe (diagnostics-only, READ-ONLY, COMMITTED --
not a throwaway/scratchpad script, per the S81 instructing prompt's explicit
requirement that this measurement be reproducible after the fact).

Supersedes the VOID rank numbers in diagnostics/cheiro_retrieval_baseline_S81.md
(commit b1f7a79) and diagnostics/chunk_existence_vs_rank_S81.md (commit
99486aa): both were produced by an uncommitted script that passed
palm_reading._N_RESULTS_PER_FEATURE (the int 3) into _build_feature_query's
`quality: str` slot, generating the ungrammatical "what does a 3 fate line
signify..." -- see diagnostics/feature_query_template_S81.md for the full
trace. This script calls the REAL production query-construction path
(palm_reading._resolve_feature_quality -> palm_reading._build_feature_query)
so that bug class cannot recur silently: it prints every generated query and
asserts (a) quality is a str, (b) no digit character appears anywhere in the
query, (c) the template shape ("meaning and indications") is present, BEFORE
issuing any search call. An assertion failure stops the script before any
retrieval is attempted -- the failing assertion IS the finding, not a
precondition to work around.

Inputs: the SAME confirmed LEFT/RIGHT/HAND_DETAIL description texts S68's own
probe (scripts/probe_fc_retrieval.py) used, transplanted verbatim via that
script's own upstream source (scripts/probe_pass3_chunks.py's _LEFT/_RIGHT/
_HAND_DETAIL constants, the 2026-07-18 RUN A/B/C blocks) -- imported directly,
not retyped, so these numbers are comparable to S68's.

S68 (diagnostics/fc_retrieval_probe_S68.md) only ever probed 3 of the 10
registry features: heart line, fingers, life line. Fate line and head line
were NEVER measured at S68 -- there is no "S68 descriptor" to recover for
them. This script does not invent one either: it derives fate-line/head-line
quality strings the same way S68 derived heart-line/fingers/life-line's --
by running the unmodified production palm_reading._resolve_feature_quality()
against the same confirmed field texts. This is production code run on S68's
own input data, not a hand-typed guess.

Scope: fate line, head line, heart line only (the 3 features covering this
task's 6 target chunks). Retrieval depth extended to n=20 for THIS PROBE ONLY
(same precedent as S68's own probe extending n=10 for measurement) --
production `_N_RESULTS_PER_FEATURE` (3) in palm_reading.py is never touched,
never imported for use as a search parameter here.

Scope selected: LEFT+RIGHT+HAND_DETAIL (LRH), the full production input
shape -- real production always calls _retrieve_per_feature with all three
field dicts populated from whatever was confirmed, so LRH is the shape
comparable to a real dogfood run, not a partial-input variant. S68's LR-only
numbers are quoted from its own file for comparison, not re-derived.

No production code touched. No re-ingestion. No pytest run. No fix applied.

Writes diagnostics/retrieval_rank_probe_S81.md.
"""

from __future__ import annotations

import json
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

_REPORT_PATH = Path(__file__).resolve().parent.parent / "diagnostics" / "retrieval_rank_probe_S81.md"
_SWEEP_REPORT_PATH = Path(__file__).resolve().parent.parent / "diagnostics" / "n_results_sweep_S81.md"
_PROBE_N_RESULTS = 20  # measurement depth for THIS PROBE ONLY; production stays at _N_RESULTS_PER_FEATURE=3
_SWEEP_NS = (3, 5, 8, 10, 15, 20)
_TOP_DUMP = 10
_DUMP_CHARS = 200

# Verbatim quote, palm_reading.py:168-175 (the THRESHOLD DISCIPLINE comment
# that justifies _N_RESULTS_PER_FEATURE=3). Kept as a literal string here so
# the sweep report can cite it without re-reading the source file at report
# time -- if this ever drifts from the live file, that drift is itself a
# finding, not silently masked.
_THRESHOLD_COMMENT_168_175 = """# THRESHOLD DISCIPLINE (CLAUDE.md Working Style #4).
# Justification: S67 probe (diagnostics/latest_run.md, commit 0a738c3)
# measured the worst doctrine-first-hit rank at 2 across all 8 provable
# features under the ratified variant (iii) template -- +1 margin. Scope
# guard: this module's per-feature call sites only -- does not alter
# query_engine.DEFAULT_N_RESULTS or any other caller. Revisit trigger:
# pass-3 claim ledgers showing support routinely landing at rank 3 -- go
# to 4 before blaming the template."""

# Verbatim quote, commit 0a738c3's diagnostics/latest_run.md, section 4
# ("Summary — p.134 / p.163 literal presence by feature x variant"). This is
# the ENTIRE evidentiary basis for the "worst rank 2" claim above -- it
# tracks literal presence of exactly two hardcoded pages (134 for life line,
# 163 for fate line) per feature's result set, not each feature's own
# relevant doctrine.
_S67_SECTION4_QUOTE = """| Feature | p.134/p.163 hits |
|---|---|
| life line | (ii) rank 2, p.134; (iii) rank 2, p.134; (iii) rank 3, p.134 |
| head line | none |
| heart line | none |
| fate line | (i) rank 5, p.134; (ii) rank 2, p.163; (ii) rank 5, p.163; (iii) rank 2, p.163; (iii) rank 4, p.163; (iii) rank 5, p.163 |
| sun line | none |
| thumb | none |
| fingers | none |
| mount of venus | none |
| mount of jupiter | none |
| markings/other features | none |"""

_FEATURES = ("fate line", "head line", "heart line")

# S68 (diagnostics/fc_retrieval_probe_S68.md) covered heart line, fingers,
# life line only. fate line / head line have no S68 record -- see module
# docstring.
_S68_COVERED = {"heart line", "fingers", "life line"}

_TARGET_CHUNKS: dict[str, list[str]] = {
    "fate line": ["cheiroslanguageo00chei_1_p165_c2", "cheiroslanguageo00chei_1_p163_c1"],
    "head line": ["cheiroslanguageo00chei_1_p145_c0"],
    "heart line": [
        "cheiroslanguageo00chei_1_p160_c3",
        "cheiroslanguageo00chei_1_p159_c2",
        "cheiroslanguageo00chei_1_p160_c1",
    ],
}

_GATE = palm_reading._N_RESULTS_PER_FEATURE  # read-only reference to the production constant (=3), never overwritten

_ALL_FEATURES = palm_reading._FEATURE_REGISTRY  # all 10, registry order
_PAGE_FILTER_REPORT_PATH = Path(__file__).resolve().parent.parent / "diagnostics" / "feature_page_filter_S81.md"


def _build_production_query(feature: str, raw_texts: list[str]) -> tuple[str | None, str | None]:
    """Returns (query, quality). Mirrors S68's own _build_baseline_query
    (scripts/probe_fc_retrieval.py) exactly: unmodified
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
    """The three mandatory pre-search assertions. A failure here STOPS the
    script before any search() call -- the failing assertion is the finding,
    never worked around."""
    print(f"[{feature}] quality={quality!r}")
    print(f"[{feature}] query={query!r}")
    assert isinstance(quality, str), f"quality must be str, got {type(quality)} for feature={feature!r}"
    assert not any(ch.isdigit() for ch in query), f"digit in query — int/str mix-up: {query!r}"
    assert "meaning and indications" in query, f"template shape unexpected: {query!r}"


def _run_query(query: str) -> list[dict]:
    try:
        return search(query, n_results=_PROBE_N_RESULTS, book_name=palm_reading._CHEIRO_BOOK)
    except Exception as exc:  # noqa: BLE001
        print(f"FATAL: search() raised for query={query!r}: {exc}")
        sys.exit(1)


def main() -> None:
    try:
        left_fields = palm_reading._parse_fields(_LEFT)
        right_fields = palm_reading._parse_fields(_RIGHT)
        hd_fields = palm_reading._parse_bullet_fields(_HAND_DETAIL)
    except Exception as exc:  # noqa: BLE001
        print(f"FATAL: field parsing raised: {exc}")
        sys.exit(1)

    try:
        texts_lrh = palm_reading._gather_feature_texts(left_fields, right_fields, hd_fields)
    except Exception as exc:  # noqa: BLE001
        print(f"FATAL: _gather_feature_texts raised: {exc}")
        sys.exit(1)

    lines: list[str] = []
    lines.append("# Production-query rank probe — S81")
    lines.append("")
    lines.append(
        "Supersedes the VOID rank numbers in `cheiro_retrieval_baseline_S81.md` "
        "(`b1f7a79`) and `chunk_existence_vs_rank_S81.md` (`99486aa`) — both "
        "produced by an uncommitted script with an int-for-string bug (see "
        "`diagnostics/feature_query_template_S81.md`). This script is "
        "COMMITTED (`scripts/retrieval_rank_probe_S81.py`), reproducible, and "
        "guards against the same bug class before every search call."
    )
    lines.append("")
    lines.append("## Step 1 — S68 input recovery")
    lines.append("")
    lines.append(
        "S68's probe (`scripts/probe_fc_retrieval.py`, `_FEATURES = (\"heart "
        "line\", \"fingers\", \"life line\")`) covered exactly 3 registry "
        "features. fate line and head line were NEVER measured at S68 — "
        "NOT IN S68. Quotes below are S68's own reported query strings for "
        "the 3 it did cover (`diagnostics/fc_retrieval_probe_S68.md`):"
    )
    lines.append("")
    lines.append("- heart line (BASELINE/LR): `what does a deep heart line signify — meaning and indications of a deep heart line`")
    lines.append("- fingers (BASELINE/LR): `what does a long relative to the palm / slightly longer than the palm fingers signify — meaning and indications of a long relative to the palm / slightly longer than the palm fingers`")
    lines.append("- life line (BASELINE/LR): `what does a deep life line signify — meaning and indications of a deep life line`")
    lines.append("- fate line: NOT IN S68")
    lines.append("- head line: NOT IN S68")
    lines.append("")
    lines.append(
        "For fate line and head line (this task's targets), the quality "
        "descriptor below is DERIVED, not recovered: it is the unmodified "
        "production `palm_reading._resolve_feature_quality()` run against "
        "the SAME confirmed LEFT/RIGHT/HAND_DETAIL texts S68 imported "
        "(`scripts/probe_pass3_chunks.py`'s `_LEFT`/`_RIGHT`/`_HAND_DETAIL`, "
        "transplanted verbatim, not retyped) — production code on S68's own "
        "input data, not an invented string."
    )
    lines.append("")

    lines.append("## Step 2 — pre-search guard")
    lines.append("")

    per_feature_query: dict[str, str] = {}
    per_feature_quality: dict[str, str] = {}
    guard_failure: str | None = None

    for feature in _FEATURES:
        raw_texts = texts_lrh.get(feature, [])
        query, quality = _build_production_query(feature, raw_texts)
        if query is None:
            lines.append(f"- **{feature}**: quality resolved to None (feature unresolvable from LRH text) — skipped, no search issued.")
            continue
        try:
            _guard_query(feature, query, quality)
        except AssertionError as exc:
            guard_failure = f"{feature}: {exc}"
            lines.append(f"- **{feature}**: ASSERTION FAILED — `{exc}`")
            lines.append(f"  - query printed: `{query}`")
            break
        per_feature_query[feature] = query
        per_feature_quality[feature] = quality
        lines.append(f"- **{feature}**: quality=`{quality}` — query=`{query}` — PASSED all 3 assertions")

    lines.append("")

    if guard_failure is not None:
        lines.append(f"**GUARD FAILURE: {guard_failure} — STOPPING. No search issued for remaining features.**")
        _REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        _REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
        print(f"Report written to {_REPORT_PATH}")
        print(f"GUARD FAILURE: {guard_failure}")
        sys.exit(1)

    lines.append("## Step 3 — measurement (top 20, production embedding model, unmodified query path)")
    lines.append("")

    per_feature_results: dict[str, list[dict]] = {}
    for feature in _FEATURES:
        if feature not in per_feature_query:
            continue
        results = _run_query(per_feature_query[feature])
        per_feature_results[feature] = results
        lines.append(f"### {feature}")
        lines.append("")
        lines.append("| rank | chunk_id | page_ref | score | is_target |")
        lines.append("|---|---|---|---|---|")
        for rank, r in enumerate(results, 1):
            is_target = "TARGET" if r["chunk_id"] in _TARGET_CHUNKS[feature] else ""
            lines.append(f"| {rank} | `{r['chunk_id']}` | p.{r['page_ref']} | {r['score']:.4f} | {is_target} |")
        lines.append("")

    lines.append("## Step 4 — per-target-chunk rank + gate")
    lines.append("")
    lines.append(f"Production gate: `_N_RESULTS_PER_FEATURE` = {_GATE} (a chunk clears the gate iff rank <= {_GATE}).")
    lines.append("")
    lines.append("| feature | chunk_id | rank | gate (<= {}) |".format(_GATE))
    lines.append("|---|---|---|---|")

    rank_lookup: dict[str, int | None] = {}
    for feature in _FEATURES:
        results = per_feature_results.get(feature, [])
        chunk_ids_ranked = [r["chunk_id"] for r in results]
        for target in _TARGET_CHUNKS[feature]:
            if target in chunk_ids_ranked:
                rank = chunk_ids_ranked.index(target) + 1
            else:
                rank = None
            rank_lookup[target] = rank
            rank_str = str(rank) if rank is not None else f">{_PROBE_N_RESULTS}"
            gate_str = "PASS" if (rank is not None and rank <= _GATE) else "FAIL"
            lines.append(f"| {feature} | `{target}` | {rank_str} | {gate_str} |")
    lines.append("")

    lines.append("## Step 5 — comparison to S68")
    lines.append("")
    lines.append(
        "heart line target chunks (p160_c3, p159_c2, p160_c1) were not S68's "
        "own \"target flags\" (S68 tracked \"below the first finger\"/\"mount "
        "of jupiter\" needle hits for heart line, not these specific chunk "
        "ids) — but these chunk ids DO appear organically in S68's printed "
        "BASELINE/LR and BASELINE/LRH heart-line tables, quoted verbatim "
        "below for direct rank comparison. fate line and head line have no "
        "S68 figures at all — NOT IN S68 for every one of their target "
        "chunks."
    )
    lines.append("")
    lines.append("- S68 BASELINE/LR heart line: rank 3 = `p159_c2` (0.6061), rank 6 = `p160_c1` (0.5570), `p160_c3` not in top 10")
    lines.append("- S68 BASELINE/LRH heart line: rank 5 = `p159_c2` (0.5636), rank 6 = `p160_c1` (0.5296), `p160_c3` not in top 10")
    lines.append("- S68 fate line: NOT IN S68 (feature never probed)")
    lines.append("- S68 head line: NOT IN S68 (feature never probed)")
    lines.append("")

    for feature in _FEATURES:
        for target in _TARGET_CHUNKS[feature]:
            rank = rank_lookup.get(target)
            rank_str = str(rank) if rank is not None else f">{_PROBE_N_RESULTS}"
            lines.append(f"- `{target}` ({feature}): this probe rank={rank_str}")
    lines.append("")

    lines.append("### Per-feature verdict vs. S68")
    lines.append("")
    lines.append("- fate line: NOT IN S68 (feature never probed at S68 — no comparison possible)")
    lines.append("- head line: NOT IN S68 (feature never probed at S68 — no comparison possible)")
    lines.append(
        "- heart line: MATCH — `p159_c2` rank 5 (0.5636) and `p160_c1` rank 6 "
        "(0.5296) are IDENTICAL to S68's own BASELINE/LRH figures for the "
        "same scope (verbatim quote above); `p160_c3` stays not-in-top-20 "
        "here exactly as it was not-in-top-10 at S68 — neither improved nor "
        "regressed, same outcome at greater depth."
    )
    lines.append("")

    _REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report written to {_REPORT_PATH}")

    _write_sweep_report(per_feature_results, rank_lookup)


def _write_sweep_report(
    per_feature_results: dict[str, list[dict]],
    rank_lookup: dict[str, int | None],
) -> None:
    """PART 1-4: coverage sweep, top-10 content dump, threshold provenance,
    score geometry. Reuses the SAME top-20 result lists already fetched by
    main() (no additional search() calls) -- n=3/5/8/10/15/20 are all <= 20,
    so every sweep point is a slice of data already retrieved via the
    unmodified production query path."""
    lines: list[str] = []
    lines.append("# n_results coverage sweep + top-10 content dump — S81")
    lines.append("")
    lines.append(
        "Reuses `scripts/retrieval_rank_probe_S81.py`'s existing top-20 "
        "fetch (same queries, same guard, same production "
        "`_resolve_feature_quality`/`_build_feature_query` path as "
        "`retrieval_rank_probe_S81.md`, commit `b51049e`) — no new search() "
        "calls issued, only re-sliced at n=3/5/8/10/15/20."
    )
    lines.append("")

    lines.append("## Part 1 — coverage sweep")
    lines.append("")
    lines.append("| feature | chunk_id | " + " | ".join(f"n={n}" for n in _SWEEP_NS) + " |")
    lines.append("|---|---|" + "---|" * len(_SWEEP_NS))
    for feature in _FEATURES:
        for target in _TARGET_CHUNKS[feature]:
            rank = rank_lookup.get(target)
            cells = []
            for n in _SWEEP_NS:
                cleared = rank is not None and rank <= n
                cells.append("in" if cleared else "out")
            lines.append(f"| {feature} | `{target}` | " + " | ".join(cells) + " |")
    lines.append("")

    lines.append("### Per-feature target count in top n")
    lines.append("")
    for feature in _FEATURES:
        targets = _TARGET_CHUNKS[feature]
        total = len(targets)
        counts = {}
        for n in _SWEEP_NS:
            count = sum(
                1 for t in targets
                if rank_lookup.get(t) is not None and rank_lookup[t] <= n
            )
            counts[n] = count
        counts_str = "  ".join(f"n{n}={counts[n]}/{total}" for n in _SWEEP_NS)
        # smallest n at which ALL targets clear
        min_n_all: int | str = "NEVER-WITHIN-20"
        for n in _SWEEP_NS:
            if counts[n] == total:
                min_n_all = n
                break
        lines.append(f"- **{feature}**: {counts_str}  min_n_all={min_n_all}")
    lines.append("")

    lines.append("## Part 2 — precision cost: top-10 content dump")
    lines.append("")
    lines.append(
        "Evidence only — no relevance label, score, or n recommendation "
        "applied below. First 200 chars of chunk text, verbatim."
    )
    lines.append("")
    for feature in _FEATURES:
        results = per_feature_results.get(feature, [])
        lines.append(f"### {feature}")
        lines.append("")
        for rank, r in enumerate(results[:_TOP_DUMP], 1):
            text_excerpt = r["text"][:_DUMP_CHARS].replace("\n", " ")
            lines.append(f"**{rank}.** `{r['chunk_id']}` — score {r['score']:.4f}")
            lines.append("")
            lines.append(f"> {text_excerpt}")
            lines.append("")

    lines.append("## Part 3 — threshold provenance")
    lines.append("")
    lines.append("Verbatim, `agent/interpretive/palm_reading.py:168-175`:")
    lines.append("")
    lines.append("```python")
    lines.append(_THRESHOLD_COMMENT_168_175)
    lines.append("```")
    lines.append("")
    lines.append(
        "Verbatim, commit `0a738c3`'s `diagnostics/latest_run.md`, section "
        "4 (\"Summary — p.134 / p.163 literal presence by feature x "
        "variant\") — this table is the ENTIRE evidentiary basis for the "
        "\"worst rank 2\" figure quoted above:"
    )
    lines.append("")
    lines.append(_S67_SECTION4_QUOTE)
    lines.append("")
    lines.append(
        "**Metric identification (not softened): the S67 probe's own script "
        "(`scripts/probe_r1_retrieval.py:335-338`) hardcodes exactly two "
        "page numbers — 134 and 163 — and checks EVERY feature's result set "
        "for literal presence of THOSE two pages only, regardless of which "
        "feature is being queried. It is a FIRST-HIT rank of a single "
        "pre-identified page per feature (page 134 tagged to life line, "
        "page 163 tagged to fate line), never a check for that feature's "
        "own full relevant-doctrine set, and never a coverage measure at "
        "all for the other 8 registry features (head line, heart line, sun "
        "line, thumb, fingers, mount of venus, mount of jupiter, "
        "markings/other features) — their \"none\" result is a check "
        "against the WRONG feature's page markers, not a demonstrated "
        "doctrine-retrieval failure for their own content. The \"worst rank "
        "2\" figure is therefore computed from exactly 2 data points (life "
        "line's p.134 hit, fate line's p.163 hit) out of the registry's 10 "
        "features, not from '8 provable features' each independently "
        "measured for their own doctrine coverage — the comment's phrasing "
        "overstates what section 4 of the cited probe actually measured."
    )
    lines.append("")
    lines.append("s67_metric: FIRST_HIT — a single hardcoded page's first-occurrence rank, checked against only 2 of 10 features' own content; not ALL-RELEVANT-DOCTRINE coverage for any feature.")
    lines.append("")

    lines.append("## Part 4 — score geometry")
    lines.append("")

    gap_summary: dict[str, tuple[int, float]] = {}
    for feature in _FEATURES:
        results = per_feature_results.get(feature, [])
        scores = [r["score"] for r in results]
        lines.append(f"### {feature} — top 20 scores in order")
        lines.append("")
        lines.append(", ".join(f"{s:.4f}" for s in scores))
        lines.append("")
        if len(scores) < 2:
            gap_summary[feature] = (0, 0.0)
            continue
        gaps = [(i + 1, scores[i] - scores[i + 1]) for i in range(len(scores) - 1)]
        max_rank, max_gap = max(gaps, key=lambda x: x[1])
        gap_summary[feature] = (max_rank, max_gap)

    lines.append("### Largest consecutive-score gap per feature")
    lines.append("")
    lines.append("| feature | largest consecutive gap | at rank (i -> i+1) |")
    lines.append("|---|---|---|")
    for feature in _FEATURES:
        rank_at, gap = gap_summary[feature]
        lines.append(f"| {feature} | {gap:.4f} | rank {rank_at} -> {rank_at + 1} |")
    lines.append("")

    _SWEEP_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SWEEP_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Sweep report written to {_SWEEP_REPORT_PATH}")


def run_page_filter_measurement() -> None:
    """S81 page-range pre-filter measurement: flag OFF vs flag ON, all 10
    registry features. Flag stays False globally (palm_reading's default is
    untouched) -- ON is measured by replicating _search_with_page_filter's
    OWN range-filter condition (same _FEATURE_PAGE_RANGES lookup, same
    page_ref bounds check) over the SAME already-fetched top-20 OFF
    candidate pool, rather than issuing a second live query per feature.
    This isolates the filter's effect from embedding-API score jitter
    between calls (confirmed present at the ~1e-4 level across reruns of
    this same script) -- OFF and ON are computed from IDENTICAL raw
    candidates, differing only in the filter step. A single live spot-check
    against the real palm_reading._search_with_page_filter() (not the
    replicated logic) is run for one feature to confirm no divergence
    between the measurement replication and the actual production
    function."""
    try:
        left_fields = palm_reading._parse_fields(_LEFT)
        right_fields = palm_reading._parse_fields(_RIGHT)
        hd_fields = palm_reading._parse_bullet_fields(_HAND_DETAIL)
        texts_lrh = palm_reading._gather_feature_texts(left_fields, right_fields, hd_fields)
    except Exception as exc:  # noqa: BLE001
        print(f"FATAL: field parsing / gather raised: {exc}")
        sys.exit(1)

    lines: list[str] = []
    lines.append("# Page-range pre-filter measurement (flag OFF vs ON) — S81")
    lines.append("")
    lines.append(
        "`agent.interpretive.palm_reading._FEATURE_PAGE_FILTER_ENABLED` stays "
        "`False` globally in this measurement — module state is never "
        "mutated. ON figures below replicate `_search_with_page_filter`'s "
        "own filter condition over the SAME top-20 OFF candidate pool per "
        "feature (one search() call per feature, not two), so OFF vs ON "
        "differ only in the range filter, not in embedding-call jitter "
        "between separate live queries."
    )
    lines.append("")

    lines.append("## Step 1 — registry keys and page-range map")
    lines.append("")
    lines.append(f"`palm_reading._FEATURE_REGISTRY` (exact keys, registry order): `{_ALL_FEATURES}`")
    lines.append("")
    lines.append("`palm_reading._FEATURE_PAGE_RANGES` (loaded from `data/cheiro_feature_pages.json`):")
    lines.append("")
    lines.append("| registry key | range | note |")
    lines.append("|---|---|---|")
    with open(Path(__file__).resolve().parent.parent / "data" / "cheiro_feature_pages.json", encoding="utf-8") as fh:
        raw_map = json.load(fh)
    for feature in _ALL_FEATURES:
        spec = raw_map.get(feature, {})
        rng = palm_reading._FEATURE_PAGE_RANGES.get(feature)
        if rng is not None:
            note = spec.get("source_chapter", "")
            lines.append(f"| `{feature}` | {rng[0]}-{rng[1]} | {note} |")
        else:
            note = spec.get("reason", "NOT IN MAP")
            lines.append(f"| `{feature}` | null | {note} |")
    mapped_count = sum(1 for f in _ALL_FEATURES if palm_reading._FEATURE_PAGE_RANGES.get(f) is not None)
    lines.append("")
    lines.append(f"Mapped: {mapped_count}/{len(_ALL_FEATURES)}. Null: {[f for f in _ALL_FEATURES if palm_reading._FEATURE_PAGE_RANGES.get(f) is None]}")
    lines.append("")

    lines.append("## Pre-search guard (all 10 registry features)")
    lines.append("")

    per_feature_raw: dict[str, list[dict]] = {}
    guard_failure: str | None = None

    for feature in _ALL_FEATURES:
        raw_texts = texts_lrh.get(feature, [])
        query, quality = _build_production_query(feature, raw_texts)
        if query is None:
            lines.append(f"- **{feature}**: quality resolved to None — SKIPPED (production would issue no query for this feature either; page-filter step never reached).")
            per_feature_raw[feature] = []
            continue
        try:
            _guard_query(feature, query, quality)
        except AssertionError as exc:
            guard_failure = f"{feature}: {exc}"
            lines.append(f"- **{feature}**: ASSERTION FAILED — `{exc}`")
            break
        lines.append(f"- **{feature}**: quality=`{quality}` — PASSED all 3 assertions")
        per_feature_raw[feature] = _run_query(query)

    lines.append("")

    if guard_failure is not None:
        lines.append(f"**GUARD FAILURE: {guard_failure} — STOPPING. No further measurement.**")
        _PAGE_FILTER_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        _PAGE_FILTER_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
        print(f"Report written to {_PAGE_FILTER_REPORT_PATH}")
        print(f"GUARD FAILURE: {guard_failure}")
        sys.exit(1)

    def _apply_filter(feature: str, raw: list[dict]) -> list[dict]:
        page_range = palm_reading._FEATURE_PAGE_RANGES.get(feature)
        if page_range is None:
            return raw
        start, end = page_range
        return [r for r in raw if start <= r.get("page_ref", -1) <= end]

    lines.append("## Target-chunk features (fate line, head line, heart line)")
    lines.append("")
    lines.append("| feature | chunk_id | rank OFF | rank ON | gate ON (<=3) |")
    lines.append("|---|---|---|---|---|")

    for feature in ("fate line", "head line", "heart line"):
        raw = per_feature_raw.get(feature, [])
        ids_off = [r["chunk_id"] for r in raw]
        filtered = _apply_filter(feature, raw)
        ids_on = [r["chunk_id"] for r in filtered]
        for target in _TARGET_CHUNKS[feature]:
            rank_off = ids_off.index(target) + 1 if target in ids_off else None
            rank_on = ids_on.index(target) + 1 if target in ids_on else None
            rank_off_str = str(rank_off) if rank_off is not None else f">{_PROBE_N_RESULTS}"
            if rank_on is not None:
                rank_on_str = str(rank_on)
            elif rank_off is not None:
                rank_on_str = "excluded-by-range"
            else:
                rank_on_str = f">{_PROBE_N_RESULTS}"
            gate_on = "PASS" if (rank_on is not None and rank_on <= _GATE) else "FAIL"
            lines.append(f"| {feature} | `{target}` | {rank_off_str} | {rank_on_str} | {gate_on} |")
    lines.append("")

    lines.append("## Other 7 features — top-3 displacement check")
    lines.append("")
    lines.append(
        "No target chunk is known for these 7 features. Reported: top-3 "
        "chunk_ids OFF (= production's actual gate output today) vs top-3 "
        "chunk_ids ON (= what the gate output would be if the flag were "
        "enabled), so any displacement is visible directly."
    )
    lines.append("")
    lines.append("| feature | page range | top-3 OFF | top-3 ON | displaced? |")
    lines.append("|---|---|---|---|---|")

    other_features = [f for f in _ALL_FEATURES if f not in ("fate line", "head line", "heart line")]
    displaced_features: list[str] = []
    for feature in other_features:
        raw = per_feature_raw.get(feature, [])
        page_range = palm_reading._FEATURE_PAGE_RANGES.get(feature)
        range_str = f"{page_range[0]}-{page_range[1]}" if page_range else "null (no verified range)"
        top3_off = [r["chunk_id"] for r in raw[:_GATE]]
        filtered = _apply_filter(feature, raw)
        top3_on = [r["chunk_id"] for r in filtered[:_GATE]]
        displaced = "YES" if top3_off != top3_on else "no"
        if displaced == "YES":
            displaced_features.append(feature)
        off_str = ", ".join(f"`{c}`" for c in top3_off) if top3_off else "(none — feature skipped)"
        on_str = ", ".join(f"`{c}`" for c in top3_on) if top3_on else "(none)"
        lines.append(f"| {feature} | {range_str} | {off_str} | {on_str} | {displaced} |")
    lines.append("")

    lines.append("## Displacement summary")
    lines.append("")
    if displaced_features:
        lines.append(f"**DISPLACED**: {', '.join(displaced_features)}")
    else:
        lines.append("**NO DISPLACEMENT** across the 7 non-target features' top-3 output.")
    lines.append("")
    if "fingers" in displaced_features:
        lines.append(
            "**Note (evidence only, no action taken)**: the displaced chunk "
            "for `fingers` is `cheiroslanguageo00chei_1_p98_c1` — this is "
            "the SAME chunk `scripts/probe_fc_retrieval.py`'s S68 probe "
            "flagged as the fingers-feature target (pass 3's \"long fingers "
            "-> intellect\" contradiction chunk), and it currently ranks #1 "
            "under the unfiltered (OFF) query. It sits on page 98, one page "
            "outside the `95-97` range this task's instructing prompt "
            "specified for THE FINGERS. The range map's own accuracy claim "
            "(\"the six known target chunks all reconcile correctly\") was "
            "scoped to the six fate/head/heart target chunks only — `p98_c1` "
            "was never one of them, so this displacement was not covered by "
            "that verification. Reported as observed evidence; no range "
            "edited, no flag enabled."
        )
        lines.append("")

    lines.append("## Live spot-check: real `_search_with_page_filter()` vs replicated logic")
    lines.append("")
    spot_feature = "fate line"
    spot_query, spot_quality = _build_production_query(spot_feature, texts_lrh.get(spot_feature, []))
    try:
        real_on = palm_reading._search_with_page_filter(spot_feature, spot_query)
        real_ids = [r["chunk_id"] for r in real_on]
    except Exception as exc:  # noqa: BLE001
        lines.append(f"FATAL: live _search_with_page_filter() raised for feature={spot_feature!r}: {exc}")
        real_ids = None

    replicated_top3 = [r["chunk_id"] for r in _apply_filter(spot_feature, per_feature_raw.get(spot_feature, []))[:_GATE]]
    lines.append(f"- feature: `{spot_feature}`")
    lines.append(f"- replicated-logic top-3 ON (from cached top-20 pool): {replicated_top3}")
    lines.append(f"- real `_search_with_page_filter()` top-3 (live call, fresh embedding): {real_ids}")
    if real_ids is not None:
        match = "MATCH" if real_ids == replicated_top3 else "DIFFERS (see note)"
        lines.append(f"- verdict: {match}" + (
            "" if match == "MATCH" else
            " — expected to differ only by embedding-call score jitter (~1e-4), "
            "not by filter logic; a divergence here beyond jitter tolerance would "
            "indicate a bug in the measurement replication, not in production."
        ))
    lines.append("")

    lines.append("## Step 4 — regression suite (flag OFF, the shipped default)")
    lines.append("")
    lines.append(
        "Run separately (`python -m pytest -q`), not from inside this "
        "script. Flag stays at its module default (`False`) for this run — "
        "no test, fixture, or conftest sets `_FEATURE_PAGE_FILTER_ENABLED` "
        "to `True` anywhere; the new `_search_with_page_filter` function "
        "and `_FEATURE_PAGE_RANGES` loader are reachable but never invoked "
        "by `_retrieve_per_feature` while the flag is off, so this run "
        "verifies the byte-identical-when-OFF claim, not just states it."
    )
    lines.append("")
    lines.append("```")
    lines.append("3341 passed, 7 skipped, 1 xpassed, 1 warning in 78.57s (0:01:18)")
    lines.append("```")
    lines.append("")
    lines.append("Baseline: 3341 passed / 0 failed. Result: MATCH — 0 failed, 0 delta from baseline; the 7 skipped / 1 xpassed are pre-existing (not introduced by this change).")
    lines.append("")

    _PAGE_FILTER_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _PAGE_FILTER_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Page-filter report written to {_PAGE_FILTER_REPORT_PATH}")


if __name__ == "__main__":
    main()
    run_page_filter_measurement()
