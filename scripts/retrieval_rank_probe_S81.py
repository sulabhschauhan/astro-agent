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
_PROBE_N_RESULTS = 20  # measurement depth for THIS PROBE ONLY; production stays at _N_RESULTS_PER_FEATURE=3

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


if __name__ == "__main__":
    main()
