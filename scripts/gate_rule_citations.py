"""
scripts/gate_rule_citations.py
S114 -- deterministic citation-verification gate for the LIVE palm rule
files (data/palm_rules/palm_rules_*.json's own validated_candidates and
parked_* sections).

REPLACES the S84-era version of this script, which was hardcoded to
data/palm_rules/_candidates/deterministic_rule_book.json (a legacy
candidate pool with ZERO FT_/H_/L_ live rule_ids) and
data/chunked_chunks.json, and matched a rule's printed source_page
directly against the corpus's own page_ref field. Neither target guarded
anything real: the live rules were never checked, and even a live rule's
own printed source_page does not equal the corpus chunk's page_ref (a
non-trivial, roughly-constant offset -- e.g. FT_007's source_page=104,
its quote anchors at cheiro_clean_v1.json page_ref=164, offset +60).

Independently re-derives whether each live/parked rule's source_quote is
actually anchored SOMEWHERE in data/cheiro/cheiro_clean_v1.json's text --
a WHOLE-CORPUS anchor search (substring, or the same >=6-token/>=0.85
overlap primitive this script always used), not a source_page-vs-page_ref
comparison. REPORT-ONLY: never writes to any data/palm_rules/ file --
only diagnostics/latest_run.md. Quarantine-only in spirit: a
NOT_FOUND_ANYWHERE rule is surfaced for Sulabh's human review, never
auto-fixed or auto-flagged into the rule file itself.

Design note on thresholds (CLAUDE.md Working Style #4, THRESHOLD
DISCIPLINE): _MIN_TOKENS_FOR_OVERLAP=6 and _OVERLAP_THRESHOLD=0.85 are
UNCHANGED from the original S84 script -- not retuned here, per this
task's own explicit instruction. Still provisional in the same sense the
original docstring flagged.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RULES_GLOB = "data/palm_rules/palm_rules_*.json"
DEFAULT_CORPUS_PATH = ROOT / "data" / "cheiro" / "cheiro_clean_v1.json"
REPORT_PATH = ROOT / "diagnostics" / "latest_run.md"
BOOK_NAME = "cheiroslanguageo00chei_1"

_MIN_TOKENS_FOR_OVERLAP = 6
_OVERLAP_THRESHOLD = 0.85

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


# ─── S114: UNCHANGED from the original S84 script (verbatim) ─────────────
# Reused exactly as-is -- substring-or-overlap matching is correct and
# already threshold-disciplined; this task does not retune it.

def normalize(text: str) -> str:
    """Lowercase, non-alphanumerics -> space, collapse whitespace. OCR/
    smart-quote/stray-glyph robust by construction: anything not
    [a-z0-9] (after lowercasing) is treated as a separator, so leading
    junk glyphs (e.g. a stray Devanagari character, a broken ligature
    like 'pereussion') never break token boundaries -- they just become
    their own (harmless, unmatched) token or vanish as a separator."""
    return " ".join(_TOKEN_PATTERN.findall(text.lower()))


def tokens_of(normalized_text: str) -> list[str]:
    return normalized_text.split()


def token_overlap(quote_tokens: list[str], page_token_set: set[str]) -> float:
    """Fraction of quote_tokens (with repetition) present in page_token_set."""
    if not quote_tokens:
        return 0.0
    present = sum(1 for t in quote_tokens if t in page_token_set)
    return present / len(quote_tokens)


def quote_matches_page(quote_norm: str, quote_tokens: list[str], page_norm: str, page_token_set: set[str]) -> tuple[bool, float | None]:
    """Returns (matched, overlap_score). overlap_score is None when the
    quote is too short for the overlap test (scope guard: >=6 tokens
    only) -- those quotes are substring-only, no score to log."""
    if quote_norm and quote_norm in page_norm:
        return True, (token_overlap(quote_tokens, page_token_set) if len(quote_tokens) >= _MIN_TOKENS_FOR_OVERLAP else None)
    if len(quote_tokens) < _MIN_TOKENS_FOR_OVERLAP:
        return False, None
    score = token_overlap(quote_tokens, page_token_set)
    return score >= _OVERLAP_THRESHOLD, score


# ─── S114: corpus loading -- whole-corpus, page-indexed AND concatenated ──

def build_page_text_index(chunks: list[dict]) -> dict[int, str]:
    """page_ref (int) -> normalized concatenation of every chunk's text on
    that page (chunk order doesn't matter for a bag-of-tokens/substring
    check; diagram chunks contribute empty text, harmless). Filters to
    BOOK_NAME defensively -- cheiro_clean_v1.json is 100% this one book
    today (confirmed at S114 pre-flight), but a future multi-book merge
    into this same file must not silently start matching against a
    DIFFERENT book's text."""
    by_page: dict[int, list[str]] = defaultdict(list)
    for c in chunks:
        if c.get("book_name") != BOOK_NAME:
            continue
        page_ref = c.get("page_ref")
        if not isinstance(page_ref, int):
            continue
        by_page[page_ref].append(c.get("text", "") or "")
    return {page: normalize(" ".join(texts)) for page, texts in by_page.items()}


def build_full_corpus_text(page_text: dict[int, str]) -> str:
    """Whole-book normalized text, pages concatenated in page_ref order --
    the FALLBACK anchor search a per-page-only check would miss for a
    quote that genuinely spans a page boundary (rare, but a per-page-only
    search cannot find it even when it's genuinely present verbatim in
    the book)."""
    return " ".join(page_text[p] for p in sorted(page_text))


# ─── S114: whole-corpus anchor classification (replaces the old
# source_page-vs-page_ref +/-1 adjacency check) ───────────────────────────

def classify_rule_citation(
    rule: dict,
    page_text: dict[int, str],
    page_token_sets: dict[int, set[str]],
    full_text: str,
    full_token_set: set[str],
) -> dict:
    """Returns {"status": "CLEAN"|"NOT_FOUND_ANYWHERE"|"UNCITED"|
    "GENERATOR_PLACEHOLDER", "matched_pages": [int, ...], "score": float|
    None, "best_score_page": int|None, "implied_offsets": [int, ...]}.

    UNCITED: no source_quote at all (report, never fail the run over it).
    GENERATOR_PLACEHOLDER: quote starts with "~" (unchanged convention).
    CLEAN: the quote anchors (substring, or the existing >=6-token/>=0.85
    overlap primitive) on AT LEAST ONE page, OR -- failing every
    individual page -- in the full-corpus concatenation (a page-spanning
    quote). `matched_pages` lists every page_ref where it anchored
    individually (empty if only the full-corpus fallback matched).
    `implied_offsets` is `[page_ref - source_page for page_ref in
    matched_pages]` when source_page is an int, else [].
    NOT_FOUND_ANYWHERE: matched nowhere -- the genuine fabrication/
    mis-transcription signal. `best_score_page`/`score` report the
    nearest partial match (by overlap score) even though it fell below
    threshold, for human review; both None if the quote was too short for
    the overlap test at every page (substring-only, nothing to score)."""
    quote_raw = (rule.get("source_quote") or "").strip()
    if not quote_raw:
        return {
            "status": "UNCITED", "matched_pages": [], "score": None,
            "best_score_page": None, "implied_offsets": [],
        }
    if quote_raw.startswith("~"):
        return {
            "status": "GENERATOR_PLACEHOLDER", "matched_pages": [], "score": None,
            "best_score_page": None, "implied_offsets": [],
        }

    source_page = rule.get("source_page")
    quote_norm = normalize(quote_raw)
    quote_tokens = tokens_of(quote_norm)

    matched_pages: list[int] = []
    best_score: float | None = None
    best_score_page: int | None = None
    for page_ref, page_norm in page_text.items():
        matched, score = quote_matches_page(quote_norm, quote_tokens, page_norm, page_token_sets[page_ref])
        if score is not None and (best_score is None or score > best_score):
            best_score, best_score_page = score, page_ref
        if matched:
            matched_pages.append(page_ref)

    if matched_pages:
        matched_pages.sort()
        offsets = [p - source_page for p in matched_pages] if isinstance(source_page, int) else []
        return {
            "status": "CLEAN", "matched_pages": matched_pages, "score": best_score,
            "best_score_page": best_score_page, "implied_offsets": offsets,
        }

    # Full-corpus fallback: catches a quote genuinely spanning a page boundary.
    matched, score = quote_matches_page(quote_norm, quote_tokens, full_text, full_token_set)
    if score is not None and (best_score is None or score > best_score):
        best_score, best_score_page = score, None  # whole-corpus match has no single page to name
    if matched:
        return {
            "status": "CLEAN", "matched_pages": [], "score": best_score,
            "best_score_page": None, "implied_offsets": [],
        }

    return {
        "status": "NOT_FOUND_ANYWHERE", "matched_pages": [], "score": best_score,
        "best_score_page": best_score_page, "implied_offsets": [],
    }


# ─── S114: live rule-file loading -- section-generic, never per-file-hardcoded ──

def load_rules_from_file(path: Path) -> tuple[list[dict], list[dict]]:
    """Returns (live_rules, parked_rules) for ONE rule file. `live_rules`
    is `validated_candidates` (the LIVE/fires set). `parked_rules` is the
    union of every top-level key starting with "parked_" that is itself a
    list (matches BOTH palm_rules_fate_line_v1.json's/palm_rules_life_
    line_v1.json's "parked_pending" and palm_rules_head_heart_v1.json's
    differently-named "parked_pending_relation_target" -- confirmed at
    S114 pre-flight the section names differ across files -- generic
    prefix match, no per-file hardcoding). `retired_superseded` is
    deliberately skipped (dead rules, out of scope for this gate).
    Non-list top-level keys (e.g. palm_rules_life_line_v1.json's own
    "meta") are skipped defensively -- this function never assumes a
    fixed section list."""
    data = json.loads(path.read_text(encoding="utf-8"))
    live = list(data.get("validated_candidates", []) or [])
    parked: list[dict] = []
    for key, value in data.items():
        if key.startswith("parked_") and isinstance(value, list):
            parked.extend(value)
    return live, parked


def _default_rule_files(rules_glob: str) -> list[Path]:
    """Resolves the glob relative to ROOT. The default pattern
    (data/palm_rules/palm_rules_*.json) is non-recursive -- it naturally
    EXCLUDES data/palm_rules/_candidates/deterministic_rule_book.json
    (a different directory, the legacy S84 pool) without needing an
    explicit exclusion check."""
    return sorted(ROOT.glob(rules_glob))


# ─── CLI ───────────────────────────────────────────────────────────────

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Whole-corpus citation-anchor gate over the LIVE palm rule files "
            "(validated_candidates + parked_*). Report-only -- writes only "
            "diagnostics/latest_run.md, never a data/palm_rules/ file."
        )
    )
    parser.add_argument(
        "--rules-glob",
        default=DEFAULT_RULES_GLOB,
        help=f"Glob (relative to repo root) for rule files to scan (default: {DEFAULT_RULES_GLOB}).",
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=DEFAULT_CORPUS_PATH,
        help=f"Corpus JSON path to anchor-search against (default: {DEFAULT_CORPUS_PATH}).",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = _parse_args()
    rule_files = _default_rule_files(args.rules_glob)
    if not rule_files:
        raise RuntimeError(
            f"gate_rule_citations: glob {args.rules_glob!r} (relative to {ROOT}) "
            "matched zero rule files -- refusing to report a false-clean empty run."
        )

    chunks = json.loads(args.corpus.read_text(encoding="utf-8"))
    page_text = build_page_text_index(chunks)
    if not page_text:
        raise RuntimeError(
            f"gate_rule_citations: {args.corpus} yielded zero pages for "
            f"book_name={BOOK_NAME!r} -- corpus path or BOOK_NAME has drifted."
        )
    page_token_sets = {p: set(tokens_of(t)) for p, t in page_text.items()}
    full_text = build_full_corpus_text(page_text)
    full_token_set = set(tokens_of(full_text))

    # ── Classify every rule in every file, live and parked separately ──
    per_file: dict[str, dict] = {}
    all_not_found: list[dict] = []
    all_clean_offsets: list[int] = []
    per_file_clean_offsets: dict[str, list[int]] = {}

    for path in rule_files:
        live, parked = load_rules_from_file(path)
        file_result = {"live": [], "parked": []}
        file_offsets: list[int] = []
        for bucket_name, bucket in (("live", live), ("parked", parked)):
            for rule in bucket:
                result = classify_rule_citation(rule, page_text, page_token_sets, full_text, full_token_set)
                row = {
                    "rule_id": rule.get("rule_id"),
                    "source_page": rule.get("source_page"),
                    "source_quote": rule.get("source_quote"),
                    **result,
                }
                file_result[bucket_name].append(row)
                if result["status"] == "CLEAN":
                    all_clean_offsets.extend(result["implied_offsets"])
                    file_offsets.extend(result["implied_offsets"])
                if result["status"] == "NOT_FOUND_ANYWHERE":
                    all_not_found.append({"file": path.name, "bucket": bucket_name, **row})
        per_file_clean_offsets[path.name] = file_offsets
        per_file[path.name] = file_result

    # ── Report (report-only: no rule file is ever written) ─────────────
    lines: list[str] = []
    lines.append("# S114 rule-citation gate report (scripts/gate_rule_citations.py)\n")
    lines.append(f"Run date: {date.today().isoformat()}. Corpus: `{args.corpus}`. "
                 f"Rule files scanned: {len(rule_files)} ({', '.join(p.name for p in rule_files)}).\n")
    lines.append(
        "**REPORT-ONLY**: this run writes nothing except this report -- no "
        "data/palm_rules/ file is read-and-rewritten. Whole-corpus anchor "
        "search (not a source_page-vs-page_ref comparison): a quote is "
        "CLEAN if it anchors on ANY page or in the full-corpus concatenation, "
        "regardless of which page_ref that is -- printed source_page and the "
        "corpus's own page_ref are different numbering schemes with a "
        "non-trivial (roughly-constant per book) offset.\n"
    )

    lines.append("## Per-file citation-status counts\n")
    lines.append("| file | bucket | CLEAN | NOT_FOUND_ANYWHERE | UNCITED | GENERATOR_PLACEHOLDER | total |")
    lines.append("|---|---|---|---|---|---|---|")
    for fname, buckets in per_file.items():
        for bucket_name in ("live", "parked"):
            rows = buckets[bucket_name]
            counts = defaultdict(int)
            for r in rows:
                counts[r["status"]] += 1
            label = "validated_candidates (LIVE)" if bucket_name == "live" else "parked_* (PARKED)"
            lines.append(
                f"| {fname} | {label} | {counts['CLEAN']} | {counts['NOT_FOUND_ANYWHERE']} | "
                f"{counts['UNCITED']} | {counts['GENERATOR_PLACEHOLDER']} | {len(rows)} |"
            )
    lines.append("")

    # ── Prominent NOT_FOUND_ANYWHERE list (the point of the gate) ──────
    lines.append("## NOT_FOUND_ANYWHERE -- every one, for human review (never auto-fixed)\n")
    if all_not_found:
        lines.append(f"**{len(all_not_found)} rule(s) with a source_quote that anchors NOWHERE in the corpus:**\n")
        for row in sorted(all_not_found, key=lambda r: (r["file"], r["rule_id"] or "")):
            nearest = (
                f"page_ref {row['best_score_page']}, overlap score {row['score']:.3f}"
                if row["best_score_page"] is not None and row["score"] is not None
                else "(no partial match -- quote too short for overlap scoring, or zero token overlap anywhere)"
            )
            lines.append(f"### {row['file']} :: {row['rule_id']} ({row['bucket']}) -- source_page {row['source_page']}")
            lines.append(f"- quote: {row['source_quote']!r}")
            lines.append(f"- nearest partial match: {nearest}")
            lines.append("")
    else:
        lines.append("**None. Every cited rule (live and parked) anchors somewhere in the corpus.**\n")

    # ── Implied-offset distribution across CLEAN rules ──────────────────
    lines.append("## Implied-offset distribution (found page_ref - source_page), CLEAN rules only\n")
    if all_clean_offsets:
        s = sorted(all_clean_offsets)
        n = len(s)
        def pct(p: float) -> int:
            idx = min(n - 1, int(p * n))
            return s[idx]
        lines.append(f"n={n} offset data points (a rule matching multiple pages contributes one point per matched page).\n")
        lines.append(f"- min: {s[0]}")
        lines.append(f"- p25: {pct(0.25)}")
        lines.append(f"- median: {pct(0.50)}")
        lines.append(f"- p75: {pct(0.75)}")
        lines.append(f"- max: {s[-1]}")
        top_offsets = Counter(s).most_common(5)
        lines.append(f"\nMost common offset values: {', '.join(f'{v} (x{c})' for v, c in top_offsets)}")
    else:
        lines.append("No CLEAN rules matched an individual page (either zero CLEAN rules, or every CLEAN match was full-corpus-only).")
    lines.append("")

    lines.append(
        "**IMPORTANT per-file finding, not a single global offset**: the "
        "combined distribution above blends together what are actually "
        "TWO distinct, each internally-tight, per-file conventions -- "
        "see the breakdown below. A future rule-authoring session should "
        "know which convention its own chapter's `source_page` field is "
        "already using before assuming a fixed +60.\n"
    )
    lines.append("### Per-file dominant offset\n")
    lines.append("| file | n | dominant offset | count at dominant | other offsets seen |")
    lines.append("|---|---|---|---|---|")
    for fname, offsets in per_file_clean_offsets.items():
        if not offsets:
            lines.append(f"| {fname} | 0 | -- | -- | -- |")
            continue
        counts = Counter(offsets)
        dominant, dom_count = counts.most_common(1)[0]
        others = [f"{v} (x{c})" for v, c in counts.most_common() if v != dominant]
        lines.append(
            f"| {fname} | {len(offsets)} | {dominant:+d} | {dom_count}/{len(offsets)} | "
            f"{', '.join(others) if others else '(none)'} |"
        )
    lines.append("")

    # ── Spot-check: the rules this task names explicitly ────────────────
    lines.append("## Spot-check: FT_007 / FT_008 / H_028 / L_026\n")
    lines.append("| rule_id | file | bucket | status | matched_pages | implied_offsets |")
    lines.append("|---|---|---|---|---|---|")
    spot_check_ids = {"FT_007", "FT_008", "H_028", "L_026"}
    found_spot_check: set[str] = set()
    for fname, buckets in per_file.items():
        for bucket_name in ("live", "parked"):
            for row in buckets[bucket_name]:
                if row["rule_id"] in spot_check_ids:
                    found_spot_check.add(row["rule_id"])
                    lines.append(
                        f"| {row['rule_id']} | {fname} | {bucket_name} | {row['status']} | "
                        f"{row['matched_pages']} | {row['implied_offsets']} |"
                    )
    missing_spot_check = spot_check_ids - found_spot_check
    if missing_spot_check:
        lines.append(f"\n**MISSING from scan: {sorted(missing_spot_check)}** -- rule_id not found in any scanned file/bucket.")
    lines.append("")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    total_live = sum(len(b["live"]) for b in per_file.values())
    total_parked = sum(len(b["parked"]) for b in per_file.values())
    print(f"Wrote {REPORT_PATH}")
    print(f"Scanned {len(rule_files)} rule file(s): {total_live} live rule(s), {total_parked} parked rule(s).")
    print(f"NOT_FOUND_ANYWHERE: {len(all_not_found)}")


if __name__ == "__main__":
    main()
