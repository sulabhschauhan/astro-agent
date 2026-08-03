"""
scripts/gate_rule_citations.py
S84 -- deterministic citation-verification gate for data/deterministic_rule_book.json.

Independently re-derives whether each rule's source_quote is actually
anchored in the corpus text at its claimed source_page (or +/-1), and
flags four additional deterministic defect classes, all independent of
citation match. ANNOTATES the rule book additively -- never edits any
rule's antecedents/claim/source_quote/source_page, only adds new keys.
Quarantine-only: humans (Sulabh) decide fixes; this script draws no
conclusions beyond "does the citation check out" and "does this
structural pattern appear."

Design note on thresholds (CLAUDE.md Working Style #4, THRESHOLD
DISCIPLINE): the instructing prompt fixed 0.85 and >=6 tokens itself, not
derived here -- this script logs the overlap-score distribution to the
report specifically so that number can be revisited against real data,
per the prompt's own tuning note. Not re-justified here; treat 0.85 as
provisional until diagnostics/latest_run.md's distribution is reviewed.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULE_BOOK_PATH = ROOT / "data" / "deterministic_rule_book.json"
CHUNKS_PATH = ROOT / "data" / "chunked_chunks.json"
REPORT_PATH = ROOT / "diagnostics" / "latest_run.md"
BOOK_NAME = "cheiroslanguageo00chei_1"

_MIN_TOKENS_FOR_OVERLAP = 6
_OVERLAP_THRESHOLD = 0.85

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


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


def jaccard(tokens_a: list[str], tokens_b: list[str]) -> float:
    set_a, set_b = set(tokens_a), set(tokens_b)
    if not set_a and not set_b:
        return 1.0
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)


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


def build_page_text_index(chunks: list[dict]) -> dict[int, str]:
    """page_ref (int) -> normalized concatenation of every chunk's text
    on that page (chunk order doesn't matter for a bag-of-tokens/
    substring check; diagram chunks contribute empty text, harmless)."""
    by_page: dict[int, list[str]] = defaultdict(list)
    for c in chunks:
        if c.get("book_name") != BOOK_NAME:
            continue
        page_ref = c.get("page_ref")
        if not isinstance(page_ref, int):
            continue
        by_page[page_ref].append(c.get("text", "") or "")
    return {page: normalize(" ".join(texts)) for page, texts in by_page.items()}


def classify_citation(rule: dict, page_text: dict[int, str]) -> tuple[str, float | None, str | None]:
    """Returns (citation_status, overlap_score_used, matched_page_kind).
    matched_page_kind in {"same", "adjacent", None} -- diagnostic only."""
    quote_raw = rule.get("source_quote", "") or ""
    if quote_raw.strip().startswith("~"):
        return "GENERATOR_PLACEHOLDER", None, None

    page = rule.get("source_page")
    quote_norm = normalize(quote_raw)
    quote_tokens = tokens_of(quote_norm)

    same_page_norm = page_text.get(page, "")
    same_page_tokens = set(tokens_of(same_page_norm))
    matched, score = quote_matches_page(quote_norm, quote_tokens, same_page_norm, same_page_tokens)
    if matched:
        return "CLEAN", score, "same"

    best_adjacent_score = score
    for adj in (page - 1 if isinstance(page, int) else None, page + 1 if isinstance(page, int) else None):
        if adj is None:
            continue
        adj_norm = page_text.get(adj, "")
        adj_tokens = set(tokens_of(adj_norm))
        adj_matched, adj_score = quote_matches_page(quote_norm, quote_tokens, adj_norm, adj_tokens)
        if adj_score is not None and (best_adjacent_score is None or adj_score > best_adjacent_score):
            best_adjacent_score = adj_score
        if adj_matched:
            return "ADJACENT", adj_score, "adjacent"

    return "UNMATCHED", best_adjacent_score, None


def antecedent_key(antecedents: list[dict]) -> frozenset:
    return frozenset(
        (a.get("feature"), a.get("attribute"), a.get("value")) for a in antecedents
    )


def compute_defect_flags(rules: list[dict]) -> dict[str, set[str]]:
    """Returns rule_id -> set of defect flag names. All four checks are
    independent of citation_status, per the instructing prompt."""
    flags: dict[str, set[str]] = defaultdict(set)

    # SHARED_QUOTE: group by normalized source_quote; flag the whole
    # group if it has >=2 rules AND their claims are not all identical.
    by_quote: dict[str, list[dict]] = defaultdict(list)
    for r in rules:
        by_quote[normalize(r.get("source_quote", "") or "")].append(r)
    for quote_norm, group in by_quote.items():
        if not quote_norm or len(group) < 2:
            continue
        claims = {r.get("claim") for r in group}
        if len(claims) >= 2:
            for r in group:
                flags[r["rule_id"]].add("SHARED_QUOTE")

    # DUPLICATE_SENTENCE: same source_page, quote-to-quote Jaccard
    # overlap >= 0.85, but differing antecedents (feature+attribute+value
    # set) -> flag both members of each such pair.
    by_page: dict[int, list[dict]] = defaultdict(list)
    for r in rules:
        page = r.get("source_page")
        if isinstance(page, int):
            by_page[page].append(r)
    for page, group in by_page.items():
        n = len(group)
        for i in range(n):
            for j in range(i + 1, n):
                r1, r2 = group[i], group[j]
                q1 = tokens_of(normalize(r1.get("source_quote", "") or ""))
                q2 = tokens_of(normalize(r2.get("source_quote", "") or ""))
                if not q1 or not q2:
                    continue
                sim = jaccard(q1, q2)
                if sim >= _OVERLAP_THRESHOLD and antecedent_key(r1["antecedents"]) != antecedent_key(r2["antecedents"]):
                    flags[r1["rule_id"]].add("DUPLICATE_SENTENCE")
                    flags[r2["rule_id"]].add("DUPLICATE_SENTENCE")

    # NEEDS_RELATION_TARGET: any antecedent attribute=="Proximity" with
    # value in {"close","distant"} (relational, no target-feature slot).
    for r in rules:
        for a in r.get("antecedents", []):
            if a.get("attribute") == "Proximity" and a.get("value") in ("close", "distant"):
                flags[r["rule_id"]].add("NEEDS_RELATION_TARGET")
                break

    # NEGATION_ABSENCE: any antecedent condition_type=="negation" whose
    # rule's claim contains " without "/" absent "/" free from " (padded
    # so a match at the very start/end of the claim string isn't missed).
    negation_phrases = (" without ", " absent ", " free from ")
    for r in rules:
        has_negation = any(a.get("condition_type") == "negation" for a in r.get("antecedents", []))
        if not has_negation:
            continue
        padded_claim = f" {(r.get('claim') or '').lower()} "
        if any(p in padded_claim for p in negation_phrases):
            flags[r["rule_id"]].add("NEGATION_ABSENCE")

    return flags


def main() -> None:
    rule_book = json.loads(RULE_BOOK_PATH.read_text(encoding="utf-8"))
    chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))

    page_text = build_page_text_index(chunks)
    rules = rule_book["rules"]

    citation_results: dict[str, tuple[str, float | None, str | None]] = {}
    overlap_scores: list[float] = []
    for r in rules:
        status, score, _kind = classify_citation(r, page_text)
        citation_results[r["rule_id"]] = (status, score, _kind)
        if score is not None:
            overlap_scores.append(score)

    defect_flags = compute_defect_flags(rules)

    # ── Annotate additively ──────────────────────────────────────────
    citation_counter: dict[str, int] = defaultdict(int)
    defect_counter: dict[str, int] = defaultdict(int)
    for r in rules:
        status, score, _kind = citation_results[r["rule_id"]]
        r["citation_status"] = status
        citation_counter[status] += 1
        this_defects = sorted(defect_flags.get(r["rule_id"], set()))
        r["defect_flags"] = this_defects
        for d in this_defects:
            defect_counter[d] += 1
        r["verified"] = False
        r["verifier"] = None
        r["verified_date"] = None
        r["source_fidelity"] = None

    rule_book["meta"]["status"] = "candidate_unverified"
    rule_book["meta"]["gate_run_date"] = date.today().isoformat()
    rule_book["meta"]["gate_summary"] = {
        "citation_status_counts": dict(citation_counter),
        "defect_flag_counts": dict(defect_counter),
        "overlap_score_count": len(overlap_scores),
        "overlap_threshold_used": _OVERLAP_THRESHOLD,
        "min_tokens_for_overlap_test": _MIN_TOKENS_FOR_OVERLAP,
    }

    RULE_BOOK_PATH.write_text(
        json.dumps(rule_book, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # ── Report ────────────────────────────────────────────────────────
    lines: list[str] = []
    lines.append("# S84 rule-citation gate report (scripts/gate_rule_citations.py)\n")
    lines.append(f"Run date: {date.today().isoformat()}. Rule book: `{RULE_BOOK_PATH}` (annotated additively, in place).\n")

    lines.append("## Gate-measured citation_status vs. generator's self-report\n")
    gen_meta = rule_book["meta"]
    lines.append("| status | gate-measured count | generator self-report field | generator count |")
    lines.append("|---|---|---|---|")
    lines.append(f"| CLEAN | {citation_counter.get('CLEAN', 0)} | clean_source_quotes | {gen_meta.get('clean_source_quotes')} |")
    lines.append(f"| ADJACENT | {citation_counter.get('ADJACENT', 0)} | adjacent_page_source_quotes | {gen_meta.get('adjacent_page_source_quotes')} |")
    lines.append(f"| UNMATCHED | {citation_counter.get('UNMATCHED', 0)} | unmatched_source_quotes | {gen_meta.get('unmatched_source_quotes')} |")
    lines.append(f"| GENERATOR_PLACEHOLDER | {citation_counter.get('GENERATOR_PLACEHOLDER', 0)} | (no separate self-report field -- generator's own UNMATCHED/ADJACENT counts likely already include these) | -- |")
    lines.append(f"\nTotal rules: {len(rules)} (generator's `total_rules`: {gen_meta.get('total_rules')})\n")

    lines.append("## Defect flag counts (independent of citation_status)\n")
    lines.append("| flag | count |")
    lines.append("|---|---|")
    for flag_name in ("SHARED_QUOTE", "DUPLICATE_SENTENCE", "NEEDS_RELATION_TARGET", "NEGATION_ABSENCE"):
        lines.append(f"| {flag_name} | {defect_counter.get(flag_name, 0)} |")
    lines.append("")

    trustworthy = sum(
        1 for r in rules
        if r["citation_status"] == "CLEAN" and not r["defect_flags"]
    )
    lines.append(
        f"**Fully trustworthy (CLEAN citation AND zero defect flags): {trustworthy} / {len(rules)} "
        f"({trustworthy / len(rules) * 100:.1f}%)** -- this is stricter than the generator's own "
        f"292/393 CLEAN-only self-report, since it also excludes rules whose citation matched "
        f"but which carry an independent structural defect (shared/duplicate quotes, unrepresentable "
        f"relations, or negation-overload).\n"
    )

    lines.append("## Overlap-score distribution (tuning note per instructing prompt)\n")
    if overlap_scores:
        s = sorted(overlap_scores)
        n = len(s)
        def pct(p):
            idx = min(n - 1, int(p * n))
            return s[idx]
        lines.append(f"n={n} scores logged (quotes with >=6 tokens only; shorter quotes use substring-only match, no score)\n")
        lines.append(f"- min: {s[0]:.3f}")
        lines.append(f"- p25: {pct(0.25):.3f}")
        lines.append(f"- median: {pct(0.50):.3f}")
        lines.append(f"- p75: {pct(0.75):.3f}")
        lines.append(f"- max: {s[-1]:.3f}")
        buckets = [0, 0, 0, 0, 0]
        edges = [0.0, 0.5, 0.7, 0.85, 0.95, 1.001]
        for score in s:
            for i in range(5):
                if edges[i] <= score < edges[i + 1]:
                    buckets[i] += 1
                    break
        lines.append("\nHistogram (score range -> count):")
        for i in range(5):
            lines.append(f"  [{edges[i]:.2f}, {edges[i+1]:.2f}) : {buckets[i]}")
    else:
        lines.append("No overlap scores logged.")
    lines.append("")

    lines.append("## Hardest-case proof (5 assertions)\n")

    def status_of(rule_id: str) -> str:
        return citation_results[rule_id][0]

    def flags_of(rule_id: str) -> set[str]:
        return defect_flags.get(rule_id, set())

    assertions = []

    s = status_of("R_233")
    ok = s in ("UNMATCHED", "GENERATOR_PLACEHOLDER")
    assertions.append(("R_233 -> UNMATCHED or GENERATOR_PLACEHOLDER", ok, f"actual citation_status={s}"))

    shared = all("SHARED_QUOTE" in flags_of(rid) for rid in ("R_335", "R_336", "R_337"))
    assertions.append(("R_335/R_336/R_337 -> SHARED_QUOTE group", shared,
                        f"R_335={('SHARED_QUOTE' in flags_of('R_335'))}, R_336={('SHARED_QUOTE' in flags_of('R_336'))}, R_337={('SHARED_QUOTE' in flags_of('R_337'))}"))

    dup = ("DUPLICATE_SENTENCE" in flags_of("R_152")) and ("DUPLICATE_SENTENCE" in flags_of("R_334"))
    assertions.append(("R_152 vs R_334 -> DUPLICATE_SENTENCE (p160, soft-hand vs head-close)", dup,
                        f"R_152 flags={sorted(flags_of('R_152'))}, R_334 flags={sorted(flags_of('R_334'))}"))

    needs_rel = "NEEDS_RELATION_TARGET" in flags_of("R_342")
    assertions.append(("R_342 -> NEEDS_RELATION_TARGET", needs_rel, f"R_342 flags={sorted(flags_of('R_342'))}"))

    neg_abs = "NEGATION_ABSENCE" in flags_of("R_355")
    assertions.append(("R_355 -> NEGATION_ABSENCE", neg_abs, f"R_355 flags={sorted(flags_of('R_355'))}"))

    for label, ok, detail in assertions:
        lines.append(f"- [{'PASS' if ok else 'FAIL'}] {label} -- {detail}")
    lines.append("")

    lines.append("## Quarantined rule_ids grouped by reason\n")
    lines.append("A rule is quarantined if citation_status != CLEAN OR it carries any defect_flag.\n")

    def rule_ids_with_status(status: str) -> list[str]:
        return sorted(rid for rid, (s, _, _) in citation_results.items() if s == status)

    def rule_ids_with_flag(flag: str) -> list[str]:
        return sorted(rid for rid, fs in defect_flags.items() if flag in fs)

    for status in ("ADJACENT", "UNMATCHED", "GENERATOR_PLACEHOLDER"):
        ids = rule_ids_with_status(status)
        lines.append(f"### citation_status = {status} ({len(ids)})")
        lines.append(", ".join(ids) if ids else "(none)")
        lines.append("")

    for flag in ("SHARED_QUOTE", "DUPLICATE_SENTENCE", "NEEDS_RELATION_TARGET", "NEGATION_ABSENCE"):
        ids = rule_ids_with_flag(flag)
        lines.append(f"### defect_flag = {flag} ({len(ids)})")
        lines.append(", ".join(ids) if ids else "(none)")
        lines.append("")

    quarantined_all = sorted(
        rid for rid in citation_results
        if citation_results[rid][0] != "CLEAN" or defect_flags.get(rid)
    )
    lines.append(f"**Total distinct quarantined rule_ids: {len(quarantined_all)} / {len(rules)}**\n")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT_PATH} ; annotated {RULE_BOOK_PATH} in place.")
    print(f"citation_status counts: {dict(citation_counter)}")
    print(f"defect_flag counts: {dict(defect_counter)}")


if __name__ == "__main__":
    main()
