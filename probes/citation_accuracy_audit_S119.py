"""
probes/citation_accuracy_audit_S119.py
Step 0 of the self-grounding consolidation. READ-ONLY. Standalone -- not
imported by anything in the pipeline.

Measures, across all 99 live rules (validated_candidates only, all 4
data/palm_rules/palm_rules_*.json files), whether the CHUNK
agent/interpretive/rule_to_claim.resolve_chunk_id() actually resolves for
a rule's source_page is the CORRECT chunk to cite -- i.e. whether that
chunk's own text really contains the rule's source_quote -- and if not,
whether the quote can be found somewhere else in the chunk corpus.

Two different corpora are in play, verified at HEAD before writing this:
  - resolve_chunk_id() resolves against data/chunked_chunks.json (8290
    chunks across all books; chunk-level granularity -- 579 chunks for
    book_name="cheiroslanguageo00chei_1", the Cheiro book every palm rule
    cites). This is what palm_reading's real citation path actually uses.
  - scripts/gate_rule_citations.py's existing authoring-time gate instead
    anchors quotes against data/cheiro/cheiro_clean_v1.json (310 records,
    PAGE-level granularity, one text blob per page rather than per chunk)
    and reports NOT_FOUND_ANYWHERE: 0 across all live+parked rules -- i.e.
    every quote is a genuine, verbatim excerpt of the book SOMEWHERE.
    That gate guarantees quote authenticity; it does NOT guarantee
    resolve_chunk_id() lands on the chunk containing that quote, because
    chunking can split a page's text across multiple chunk_ids and
    resolve_chunk_id() deterministically picks the LOWEST-chunk_id
    non-empty chunk on the page, not the one that happens to contain the
    quote. That gap is exactly what this probe measures.

Overlap primitive: reused verbatim from scripts/gate_rule_citations.py
(normalize/tokens_of/token_overlap/quote_matches_page, substring-or-token-
overlap>=0.85 test on quotes >=6 tokens) -- not reinvented here, per this
task's own instruction.

Classification (exactly one per rule):
  RESOLVED_CORRECT   -- resolve_chunk_id() returned a chunk_id, and the
                        quote matches THAT chunk's own text (substring, or
                        >=0.85 token overlap for quotes >=6 tokens).
  RESOLVED_WRONG      -- resolve_chunk_id() returned a chunk_id, that
                        chunk's text does NOT match the quote, but the
                        quote DOES match some OTHER chunk in the cheiro
                        corpus (book_name=cheiroslanguageo00chei_1).
  DROPPED_NONE        -- resolve_chunk_id() returned None (no non-empty
                        chunk exists on that source_page in
                        data/chunked_chunks.json at all). The evidence
                        table still records whether the quote anchors
                        SOMEWHERE in the corpus regardless, per the
                        instructing prompt.
  NO_ANCHOR_ANYWHERE  -- resolve_chunk_id() returned a chunk_id, that
                        chunk's text does not match, AND the quote does
                        not match any other chunk in the corpus either.
                        Per the instructing prompt, these are expected to
                        be chunk-boundary splits: the quote is CLEAN at
                        the page level (scripts/gate_rule_citations.py's
                        own page-level corpus) but happens to straddle a
                        chunk boundary that neither individual chunk's
                        text fully contains. This probe re-runs that
                        exact page-level gate classifier
                        (classify_rule_citation, unmodified import) on
                        every NO_ANCHOR_ANYWHERE rule to confirm/annotate
                        this, rather than asserting it.

No pipeline/source file is read for writing. No data/palm_rules/ file, no
data/chunked_chunks.json, no data/cheiro/ file is ever modified. This
script only prints/returns a report; diagnostics/latest_run.md is written
by the invoking session, not by this file.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from agent.interpretive.palm_rules_table import PalmRule, load_rules
from agent.interpretive.rule_to_claim import resolve_chunk_id, _CHUNKS_PATH, _BOOK_NAME
from scripts.gate_rule_citations import (
    normalize,
    tokens_of,
    quote_matches_page,
    build_page_text_index,
    build_full_corpus_text,
    classify_rule_citation,
    DEFAULT_CORPUS_PATH,
)

ROOT = Path(__file__).resolve().parent.parent

_RULE_FILES = (
    ("fate", ROOT / "data" / "palm_rules" / "palm_rules_fate_line_v1.json"),
    ("head_heart", ROOT / "data" / "palm_rules" / "palm_rules_head_heart_v1.json"),
    ("life", ROOT / "data" / "palm_rules" / "palm_rules_life_line_v1.json"),
    ("mounts", ROOT / "data" / "palm_rules" / "palm_rules_mounts_v1.json"),
)


def _load_chunk_corpus(chunks_path: Path | str = _CHUNKS_PATH) -> list[dict]:
    return json.loads(Path(chunks_path).read_text(encoding="utf-8"))


def _build_chunk_index(chunks: list[dict], book_name: str = _BOOK_NAME) -> dict[str, dict]:
    """chunk_id -> chunk dict, filtered to the one Cheiro book every palm
    rule cites -- same book_name filter resolve_chunk_id() itself applies."""
    return {c["chunk_id"]: c for c in chunks if c.get("book_name") == book_name}


def _quote_matches_text(quote_raw: str, text: str) -> tuple[bool, float | None]:
    """Same substring-or->=0.85-token-overlap test gate_rule_citations.py
    uses, applied to a single chunk's raw text instead of a page's."""
    quote_norm = normalize(quote_raw)
    quote_tokens = tokens_of(quote_norm)
    text_norm = normalize(text or "")
    text_token_set = set(tokens_of(text_norm))
    return quote_matches_page(quote_norm, quote_tokens, text_norm, text_token_set)


def _find_anchor_elsewhere(
    quote_raw: str, exclude_chunk_id: str | None, chunk_index: dict[str, dict]
) -> tuple[str | None, int | None, float | None]:
    """Searches every OTHER chunk in the Cheiro corpus for an anchor.
    Returns (anchor_chunk_id, anchor_page_ref, score) -- first match found
    (chunk_id sort order, deterministic), or (None, None, best_score) if
    none matched (best_score is the highest partial score seen, for the
    evidence table's human-review column; None if every candidate quote
    was too short to score)."""
    best_score: float | None = None
    for chunk_id in sorted(chunk_index):
        if chunk_id == exclude_chunk_id:
            continue
        chunk = chunk_index[chunk_id]
        matched, score = _quote_matches_text(quote_raw, chunk.get("text", ""))
        if score is not None and (best_score is None or score > best_score):
            best_score = score
        if matched:
            return chunk_id, chunk.get("page_ref"), score
    return None, None, best_score


def audit_rules(
    chunks_path: Path | str = _CHUNKS_PATH,
    rule_files: tuple = _RULE_FILES,
) -> dict:
    """Runs the full audit. Returns a dict with per-file breakdown, totals,
    and the evidence table for RESOLVED_WRONG/DROPPED_NONE rules."""
    chunks = _load_chunk_corpus(chunks_path)
    chunk_index = _build_chunk_index(chunks)

    per_file: dict[str, dict[str, int]] = {}
    evidence_rows: list[dict] = []
    no_anchor_rules: list[tuple[str, PalmRule]] = []
    totals = defaultdict(int)

    for label, path in rule_files:
        rules = load_rules(path)
        counts = defaultdict(int)
        for rule in rules:
            chunk_id = resolve_chunk_id(rule.source_page, chunks_path)

            if chunk_id is None:
                anchor_chunk_id, anchor_page_ref, _ = _find_anchor_elsewhere(
                    rule.source_quote, None, chunk_index
                )
                counts["DROPPED_NONE"] += 1
                evidence_rows.append({
                    "rule_id": rule.rule_id,
                    "file": label,
                    "category": "DROPPED_NONE",
                    "source_page": rule.source_page,
                    "resolved_chunk_id": None,
                    "anchor_page_ref": anchor_page_ref,
                    "anchor_chunk_id": anchor_chunk_id,
                })
                continue

            resolved_chunk = chunk_index.get(chunk_id, {})
            matched, _score = _quote_matches_text(rule.source_quote, resolved_chunk.get("text", ""))
            if matched:
                counts["RESOLVED_CORRECT"] += 1
                continue

            anchor_chunk_id, anchor_page_ref, _ = _find_anchor_elsewhere(
                rule.source_quote, chunk_id, chunk_index
            )
            if anchor_chunk_id is not None:
                counts["RESOLVED_WRONG"] += 1
                evidence_rows.append({
                    "rule_id": rule.rule_id,
                    "file": label,
                    "category": "RESOLVED_WRONG",
                    "source_page": rule.source_page,
                    "resolved_chunk_id": chunk_id,
                    "anchor_page_ref": anchor_page_ref,
                    "anchor_chunk_id": anchor_chunk_id,
                })
            else:
                counts["NO_ANCHOR_ANYWHERE"] += 1
                no_anchor_rules.append((label, rule, chunk_id))

        per_file[label] = dict(counts)
        for k, v in counts.items():
            totals[k] += v

    # Cross-check NO_ANCHOR_ANYWHERE rules against the page-level gate.
    page_level_confirmations = []
    if no_anchor_rules:
        corpus = json.loads(DEFAULT_CORPUS_PATH.read_text(encoding="utf-8"))
        page_text = build_page_text_index(corpus)
        page_token_sets = {p: set(tokens_of(t)) for p, t in page_text.items()}
        full_text = build_full_corpus_text(page_text)
        full_token_set = set(tokens_of(full_text))
        for label, rule, chunk_id in no_anchor_rules:
            gate_result = classify_rule_citation(
                {"source_quote": rule.source_quote, "source_page": rule.source_page},
                page_text, page_token_sets, full_text, full_token_set,
            )
            page_level_confirmations.append({
                "rule_id": rule.rule_id,
                "file": label,
                "source_page": rule.source_page,
                "resolved_chunk_id": chunk_id,
                "page_level_gate_status": gate_result["status"],
                "page_level_matched_pages": gate_result["matched_pages"],
            })

    return {
        "per_file": per_file,
        "totals": dict(totals),
        "evidence_rows": evidence_rows,
        "page_level_confirmations": page_level_confirmations,
        "total_rules": sum(sum(c.values()) for c in per_file.values()),
    }


def format_report(result: dict) -> str:
    lines = []
    lines.append("# Citation-accuracy audit (probes/citation_accuracy_audit_S119.py)\n")
    lines.append(
        f"Total live rules audited: {result['total_rules']} "
        "(validated_candidates across all 4 data/palm_rules/palm_rules_*.json files).\n"
    )

    categories = ("RESOLVED_CORRECT", "RESOLVED_WRONG", "DROPPED_NONE", "NO_ANCHOR_ANYWHERE")
    lines.append("## Per-file breakdown\n")
    lines.append("| file | RESOLVED_CORRECT | RESOLVED_WRONG | DROPPED_NONE | NO_ANCHOR_ANYWHERE | total |")
    lines.append("|---|---|---|---|---|---|")
    for label, _path in _RULE_FILES:
        counts = result["per_file"].get(label, {})
        row_total = sum(counts.get(c, 0) for c in categories)
        lines.append(
            f"| {label} | {counts.get('RESOLVED_CORRECT', 0)} | {counts.get('RESOLVED_WRONG', 0)} | "
            f"{counts.get('DROPPED_NONE', 0)} | {counts.get('NO_ANCHOR_ANYWHERE', 0)} | {row_total} |"
        )
    totals = result["totals"]
    lines.append(
        f"| **TOTAL** | **{totals.get('RESOLVED_CORRECT', 0)}** | **{totals.get('RESOLVED_WRONG', 0)}** | "
        f"**{totals.get('DROPPED_NONE', 0)}** | **{totals.get('NO_ANCHOR_ANYWHERE', 0)}** | **{result['total_rules']}** |"
    )
    lines.append("")

    lines.append("## Evidence table: RESOLVED_WRONG / DROPPED_NONE\n")
    lines.append("| rule_id | file | category | source_page | resolved_chunk_id | anchor_page_ref | anchor_chunk_id |")
    lines.append("|---|---|---|---|---|---|---|")
    for row in sorted(result["evidence_rows"], key=lambda r: (r["file"], r["category"], r["rule_id"])):
        lines.append(
            f"| {row['rule_id']} | {row['file']} | {row['category']} | {row['source_page']} | "
            f"{row['resolved_chunk_id']} | {row['anchor_page_ref']} | {row['anchor_chunk_id']} |"
        )
    lines.append("")

    lines.append("## NO_ANCHOR_ANYWHERE rules cross-checked against the page-level gate\n")
    if result["page_level_confirmations"]:
        lines.append("| rule_id | file | source_page | resolved_chunk_id | page_level_gate_status | page_level_matched_pages |")
        lines.append("|---|---|---|---|---|---|")
        for row in result["page_level_confirmations"]:
            lines.append(
                f"| {row['rule_id']} | {row['file']} | {row['source_page']} | {row['resolved_chunk_id']} | "
                f"{row['page_level_gate_status']} | {row['page_level_matched_pages']} |"
            )
    else:
        lines.append("(none -- zero NO_ANCHOR_ANYWHERE rules this run)")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    result = audit_rules()
    print(format_report(result))
