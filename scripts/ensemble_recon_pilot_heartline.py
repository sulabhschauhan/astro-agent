"""S94 heart-line ensemble-reconciliation HOLDOUT.

Generalization test for the reconciler MECHANISM validated on the head-line
chapter (scripts/ensemble_recon_pilot_headline.py): reconcile(),
member_fully_corroborates(), token_condition_covered(), _quotes_overlap(),
SHINGLE_K, build_vocab(), and is_deferred_relational() are IMPORTED from
that module and used UNCHANGED here -- no copy-edits, no threshold
tweaks. If the frozen matcher does not behave sensibly on this new
chapter, that is a finding to report, not a defect to patch in this file.

Only the data-loading layer is chapter-specific (page range, rule filter,
Member B prompt/vocab) -- these were always chapter-specific even in the
head-line script (e.g. its own load_head_line_rules() hardcodes "line_head"
and load_head_line_chapter_text() hardcodes the "head line" page-map key),
so writing heart-line equivalents here is not a duplication of the
reconciler being generalization-tested.

This is a BLIND HOLDOUT: no calibration targets, no PASS/FAIL gate. We
read the distribution the frozen matcher produces on a chapter it was
never tuned against, we don't fit anything to it.

Touches NO registry/rules/production files. Writes only:
  - diagnostics/ensemble_recon_heartline_gpt4o.json (Member B raw output)
  - diagnostics/latest_run.md (report, truncate-and-overwrite per WS#10)

Member A (diagnostics/ensemble_recon_heartline_claude.json) is a
pre-existing blind extraction supplied externally (Cowork Claude) -- this
script only reads it, never generates or edits it. main() will not run
without it (PilotStopError, not a guess).
"""
from __future__ import annotations

import json
from pathlib import Path

from dotenv import load_dotenv

from ensemble_recon_pilot_headline import (
    SHINGLE_K,
    PilotStopError,
    build_vocab,
    reconcile,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

FEATURE_PAGES_PATH = REPO_ROOT / "data" / "cheiro_feature_pages.json"
CHAPTER_TEXT_PATH = REPO_ROOT / "data" / "cheiro" / "cheiro_clean_v1.json"
RULES_PATH = REPO_ROOT / "data" / "palm_rules" / "palm_rules_head_heart_v1.json"
MEMBER_A_PATH = REPO_ROOT / "diagnostics" / "ensemble_recon_heartline_claude.json"
MEMBER_B_OUT_PATH = REPO_ROOT / "diagnostics" / "ensemble_recon_heartline_gpt4o.json"
REPORT_PATH = REPO_ROOT / "diagnostics" / "latest_run.md"

_MODEL_B = "gpt-4o"
_TEMPERATURE = 0
_TIMEOUT_SECONDS = 120


# ─── chapter text (read-only, page range NEVER hardcoded) ────────────────

def load_heart_line_chapter_text() -> str:
    with open(FEATURE_PAGES_PATH, encoding="utf-8") as f:
        page_map = json.load(f)
    entry = page_map.get("heart line")
    if not entry or entry.get("start") is None or entry.get("end") is None:
        raise PilotStopError(f"'heart line' range missing/null in {FEATURE_PAGES_PATH.name}")
    start, end = entry["start"], entry["end"]

    with open(CHAPTER_TEXT_PATH, encoding="utf-8") as f:
        pages = json.load(f)
    in_range = [p for p in pages if p.get("page_ref") is not None and start <= p["page_ref"] <= end]
    in_range.sort(key=lambda p: p["page_ref"])
    if not in_range:
        raise PilotStopError(f"no pages found in range [{start},{end}]")

    # page_type=='diagram' pages (e.g. p158, Plate XVIII's blank verso) are
    # a documented, expected class of empty page in this corpus (S81
    # accepted-gap register: "all 9 empty pages are page_type='diagram'"),
    # not a doctrine gap -- excluded from concatenation rather than
    # treated as a missing-text failure.
    text_pages = [p for p in in_range if p.get("page_type") != "diagram"]
    missing_text = [p["page_ref"] for p in text_pages if not p.get("text", "").strip()]
    if missing_text:
        raise PilotStopError(f"empty text on non-diagram pages {missing_text} within [{start},{end}]")
    if not text_pages:
        raise PilotStopError(f"no non-diagram text pages found in range [{start},{end}]")

    return "\n\n".join(p["text"] for p in text_pages)


# ─── rules ─────────────────────────────────────────────────────────────

def load_heart_line_rules() -> list[dict]:
    with open(RULES_PATH, encoding="utf-8") as f:
        d = json.load(f)
    rules = [r for r in d["validated_candidates"] if str(r.get("topic_group", "")).startswith("line_heart")]
    if not rules:
        raise PilotStopError("no line_heart* rules found in validated_candidates")
    return rules


# ─── Member A (pre-supplied, read-only) ──────────────────────────────────

def load_member_a() -> list[dict]:
    if not MEMBER_A_PATH.exists():
        raise PilotStopError(
            f"Member A file missing: {MEMBER_A_PATH} -- supply the blind heart-line "
            "extraction before running this script"
        )
    with open(MEMBER_A_PATH, encoding="utf-8") as f:
        entries = json.load(f)
    if not isinstance(entries, list):
        raise PilotStopError("Member A file is not a JSON list")
    return entries


# ─── Member B (gpt-4o, blind to rules, closed vocab) ─────────────────────

_EXTRACTION_SCHEMA_NOTE = (
    'Return a JSON object: {"extractions": [{"feature": str, "attribute": str, '
    '"condition_token": str, "consequence_text": str, "source_quote": str}, ...]}. '
    "One entry per discrete descriptive statement you find in the text about the "
    "Line of Heart (including statements about hand type in relation to it, if any)."
)


def _build_member_b_prompt(chapter_text: str, vocab: list[dict]) -> list[dict]:
    vocab_lines = "\n".join(
        f"- feature={v['feature']!r} attribute={v['attribute']!r} value={v['value']!r}"
        for v in vocab
    )
    system = (
        "You are extracting palmistry claims from a classical text, blind to any "
        "downstream rule set. For each discrete statement, identify the feature "
        "(e.g. 'Line of Heart', 'Hand'), the attribute it describes, and a "
        "condition_token.\n\n"
        "BE EXHAUSTIVE. Walk the text sentence by sentence, paragraph by paragraph, "
        "start to finish. Emit ONE entry per discrete condition-consequence claim, "
        "even if it closely resembles another entry. Do NOT merge, summarize, or "
        "skip any claim. Do NOT use a section heading as source_quote -- always "
        "quote the actual descriptive sentence(s) in the body text that state the "
        "condition and its consequence, even when that sentence appears many "
        "paragraphs below the heading.\n\n"
        "condition_token MUST be either:\n"
        "  (a) EXACTLY one of the canonical (attribute, value) tokens below, chosen "
        "only if the sentence's full meaning -- including every modifier -- matches "
        "that token precisely, or\n"
        "  (b) the literal string 'UNMAPPABLE' if no canonical token matches exactly.\n\n"
        "NEVER pick the nearest or most-similar token. NEVER guess. A modifier that "
        "changes what is being claimed means the statement is UNMAPPABLE, even if a "
        "superficially similar token exists in the list.\n\n"
        "source_quote must be a verbatim substring copied from the provided text "
        "(whitespace may be normalized), as short as possible while uniquely "
        "identifying the passage that supports this extraction.\n\n"
        "Canonical vocabulary (attribute, value) pairs:\n" + vocab_lines + "\n\n"
        + _EXTRACTION_SCHEMA_NOTE
    )
    user = "CHAPTER TEXT (Cheiro's Language of the Hand, Line of Heart, pp.156-161):\n\n" + chapter_text
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def run_member_b(chapter_text: str, vocab: list[dict]) -> tuple[list[dict], str | None]:
    """Returns (entries, error). entries is [] on any failure; error is a
    human-readable message, never a raised exception -- try/except per
    call, never crash."""
    try:
        from openai import OpenAI
    except Exception as exc:  # pragma: no cover - environment issue
        return [], f"openai import failed: {exc}"

    try:
        client = OpenAI()
        messages = _build_member_b_prompt(chapter_text, vocab)
        response = client.chat.completions.create(
            model=_MODEL_B,
            messages=messages,
            temperature=_TEMPERATURE,
            timeout=_TIMEOUT_SECONDS,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
    except Exception as exc:
        return [], f"Member B API call failed: {exc}"

    try:
        parsed = json.loads(raw)
        entries = parsed.get("extractions")
        if not isinstance(entries, list):
            return [], "Member B response missing top-level 'extractions' list"
    except json.JSONDecodeError as exc:
        return [], f"Member B response malformed JSON: {exc}"

    try:
        with open(MEMBER_B_OUT_PATH, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)
    except OSError as exc:
        return entries, f"Member B extraction succeeded but write failed: {exc}"

    return entries, None


# ─── report (no calibration -- blind holdout, read the distribution) ─────

def write_report(
    rules: list[dict],
    vocab: list[dict],
    member_a: list[dict],
    member_b: list[dict],
    member_b_error: str | None,
    result: dict,
) -> str:
    verdicts = result["verdicts"]
    deferred = result["deferred"]

    counts: dict[str, int] = {}
    for v in verdicts.values():
        counts[v["verdict"]] = counts.get(v["verdict"], 0) + 1

    lines: list[str] = []
    lines.append("# S94 heart-line ensemble-reconciliation HOLDOUT (blind, no calibration)\n")
    lines.append(
        "Reconciler mechanism reused UNCHANGED from "
        "scripts/ensemble_recon_pilot_headline.py (reconcile, "
        "member_fully_corroborates, token_condition_covered, _quotes_overlap, "
        f"SHINGLE_K={SHINGLE_K}). No thresholds or matching logic edited for this run.\n"
    )
    lines.append(f"Rules checked (line_heart*, validated_candidates): {len(rules)}")
    lines.append(f"Canonical vocab tokens harvested: {len(vocab)}")
    lines.append(f"Member A entries (diagnostics/ensemble_recon_heartline_claude.json): {len(member_a)}")
    if member_b_error:
        lines.append(f"Member B entries (gpt-4o): 0 -- ERROR: {member_b_error}")
    else:
        lines.append(f"Member B entries (diagnostics/ensemble_recon_heartline_gpt4o.json): {len(member_b)}")
    lines.append(f"TOKEN-BEARING rules verdicted: {len(verdicts)}")
    lines.append(f"DEFERRED-RELATIONAL rules (not verdicted): {len(deferred)}\n")

    lines.append("## Verdict table\n")
    lines.append("| rule_id | verdict | A? | B? | note |")
    lines.append("|---|---|---|---|---|")
    for rid in sorted(verdicts):
        v = verdicts[rid]
        lines.append(f"| {rid} | {v['verdict']} | {v['a']} | {v['b']} | {v['note']} |")

    lines.append("\n## Deferred-relational (not verdicted)\n")
    lines.append(", ".join(sorted(deferred)) if deferred else "(none)")

    lines.append("\n## Counts per verdict\n")
    for verdict_name in ("AUTO-VERIFIED", "FABRICATED-MISMODELED", "COVERAGE-GAP", "AMBIGUOUS"):
        lines.append(f"- {verdict_name}: {counts.get(verdict_name, 0)}")

    lines.append("\n## SHINGLE_K sensitivity (5 vs 6 vs 8)\n")
    sens_k5 = reconcile(rules, member_a, member_b, k=5)["verdicts"]
    sens_k8 = reconcile(rules, member_a, member_b, k=8)["verdicts"]
    changed = [
        rid for rid in verdicts
        if sens_k5.get(rid, {}).get("verdict") != verdicts[rid]["verdict"]
        or sens_k8.get(rid, {}).get("verdict") != verdicts[rid]["verdict"]
    ]
    if changed:
        lines.append("| rule_id | K=5 | K=6 (used) | K=8 |")
        lines.append("|---|---|---|---|")
        for rid in sorted(changed):
            lines.append(
                f"| {rid} | {sens_k5.get(rid, {}).get('verdict')} "
                f"| {verdicts[rid]['verdict']} | {sens_k8.get(rid, {}).get('verdict')} |"
            )
    else:
        lines.append("(no rule's verdict changes between K=5 and K=8)")

    lines.append(
        "\nNo calibration gate this run -- blind holdout on a chapter the "
        "matcher was never tuned against. Distribution above is reported "
        "as-is for review."
    )

    report = "\n".join(lines) + "\n"
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
    return report


def main() -> None:
    try:
        rules = load_heart_line_rules()
        vocab = build_vocab(rules)
        chapter_text = load_heart_line_chapter_text()
        member_a = load_member_a()
        member_b, member_b_error = run_member_b(chapter_text, vocab)
        result = reconcile(rules, member_a, member_b)
        report = write_report(rules, vocab, member_a, member_b, member_b_error, result)
        print(report)
    except PilotStopError as exc:
        message = f"PILOT STOPPED: {exc}\n"
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            f.write(message)
        print(message)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
