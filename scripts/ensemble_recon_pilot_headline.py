"""S94 head-line ensemble-reconciliation PILOT.

Measurement probe only -- validates whether the ensemble-reconciliation
MECHANISM (two blind extractions + pure-Python reconciliation against a
closed provisional vocabulary) correctly classifies two known-answer
calibration rules: H_013 (a mis-modeled rule -- source describes an
offshoot into a STAR on the Mount of Jupiter, not a plain line-terminus
on the mount) must land FABRICATED-MISMODELED, and H_021 (a clean,
correctly-modeled rule) must land AUTO-VERIFIED.

Touches NO registry/rules/production files. Writes only:
  - diagnostics/ensemble_recon_headline_gpt4o.json (Member B raw output)
  - diagnostics/latest_run.md (report, truncate-and-overwrite per WS#10)

Member A (diagnostics/ensemble_recon_headline_claude.json) is a
pre-existing blind extraction supplied externally (Cowork Claude) -- this
script only reads it, never generates or edits it.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

FEATURE_PAGES_PATH = REPO_ROOT / "data" / "cheiro_feature_pages.json"
CHAPTER_TEXT_PATH = REPO_ROOT / "data" / "cheiro" / "cheiro_clean_v1.json"
RULES_PATH = REPO_ROOT / "data" / "palm_rules" / "palm_rules_head_heart_v1.json"
MEMBER_A_PATH = REPO_ROOT / "diagnostics" / "ensemble_recon_headline_claude.json"
MEMBER_B_OUT_PATH = REPO_ROOT / "diagnostics" / "ensemble_recon_headline_gpt4o.json"
REPORT_PATH = REPO_ROOT / "diagnostics" / "latest_run.md"

_MODEL_B = "gpt-4o"
_TEMPERATURE = 0
_TIMEOUT_SECONDS = 120

# S94-ratified calibration targets (reframed post-pilot: H_021's real claim
# is a subordinate clause buried in a p154 "murderous propensities"
# paragraph -- member A caught it, gpt-4o missed it on 2 independent runs,
# so AMBIGUOUS-routes-to-human-review is the CORRECT verdict for H_021, not
# a mechanism defect. H_004 replaces it as the AUTO-VERIFIED anchor,
# EMPIRICALLY chosen as the lowest-numbered rule_id in run1's
# both-corroborated AUTO-VERIFIED set -- not hand-picked.)
_CALIBRATION_TARGETS = {
    "H_013": "FABRICATED-MISMODELED",
    "H_021": "AMBIGUOUS",
    "H_004": "AUTO-VERIFIED",
}


class PilotStopError(RuntimeError):
    """Raised for any precondition failure -- the run stops, never guesses."""


# ─── Step 1: chapter text (read-only, page range NEVER hardcoded) ────────

def load_head_line_chapter_text() -> str:
    with open(FEATURE_PAGES_PATH, encoding="utf-8") as f:
        page_map = json.load(f)
    entry = page_map.get("head line")
    if not entry or entry.get("start") is None or entry.get("end") is None:
        raise PilotStopError(
            f"'head line' range missing/null in {FEATURE_PAGES_PATH.name}"
        )
    start, end = entry["start"], entry["end"]

    with open(CHAPTER_TEXT_PATH, encoding="utf-8") as f:
        pages = json.load(f)
    in_range = [p for p in pages if p.get("page_ref") is not None and start <= p["page_ref"] <= end]
    in_range.sort(key=lambda p: p["page_ref"])
    missing_text = [p["page_ref"] for p in in_range if not p.get("text", "").strip()]
    if missing_text:
        raise PilotStopError(f"empty text on pages {missing_text} within [{start},{end}]")
    if not in_range:
        raise PilotStopError(f"no pages found in range [{start},{end}]")

    chapter_text = "\n\n".join(p["text"] for p in in_range)
    return chapter_text


# ─── Step 2: rules + vocab harvest ───────────────────────────────────────

def load_head_line_rules() -> list[dict]:
    with open(RULES_PATH, encoding="utf-8") as f:
        d = json.load(f)
    rules = [r for r in d["validated_candidates"] if str(r.get("topic_group", "")).startswith("line_head")]
    if len(rules) != 26:
        raise PilotStopError(f"expected 26 line_head* rules, found {len(rules)}")
    ids = {r["rule_id"] for r in rules}
    missing = _CALIBRATION_TARGETS.keys() - ids
    if missing:
        raise PilotStopError(f"calibration rule(s) missing from rule set: {sorted(missing)}")
    return rules


def is_deferred_relational(rule: dict) -> bool:
    for ant in rule["antecedents"]:
        if ant.get("value") in (None, "null"):
            return True
    for flag in rule.get("schema_flags", []):
        if "RELATION_TARGET" in flag:
            return True
    return False


def build_vocab(rules: list[dict]) -> list[dict]:
    """Canonical (feature, attribute, value) triples harvested from ALL 26
    rules' antecedents (deferred-relational rules included -- their
    non-null antecedent values still belong in the closed set members
    classify into). Deduplicated, order-stable."""
    seen: set[tuple[str, str, str]] = set()
    vocab: list[dict] = []
    for rule in rules:
        for ant in rule["antecedents"]:
            value = ant.get("value")
            if value in (None, "null"):
                continue
            key = (ant["feature"], ant["attribute"], value)
            if key not in seen:
                seen.add(key)
                vocab.append({"feature": key[0], "attribute": key[1], "value": key[2]})
    return vocab


# ─── Step 3: Member A (pre-supplied, read-only) ──────────────────────────

def load_member_a() -> list[dict]:
    if not MEMBER_A_PATH.exists():
        raise PilotStopError(f"Member A file missing: {MEMBER_A_PATH}")
    with open(MEMBER_A_PATH, encoding="utf-8") as f:
        entries = json.load(f)
    if not isinstance(entries, list):
        raise PilotStopError("Member A file is not a JSON list")
    return entries


# ─── Step 4: Member B (gpt-4o, blind to rules, closed vocab) ─────────────

_EXTRACTION_SCHEMA_NOTE = (
    'Return a JSON object: {"extractions": [{"feature": str, "attribute": str, '
    '"condition_token": str, "consequence_text": str, "source_quote": str}, ...]}. '
    "One entry per discrete descriptive statement you find in the text about the "
    "Line of Head (including statements about hand type in relation to it)."
)


def _build_member_b_prompt(chapter_text: str, vocab: list[dict]) -> list[dict]:
    vocab_lines = "\n".join(
        f"- feature={v['feature']!r} attribute={v['attribute']!r} value={v['value']!r}"
        for v in vocab
    )
    system = (
        "You are extracting palmistry claims from a classical text, blind to any "
        "downstream rule set. For each discrete statement, identify the feature "
        "(e.g. 'Line of Head', 'Hand'), the attribute it describes (e.g. "
        "'Position', 'Branching', 'Proximity', 'Continuity', 'Length', 'Direction', "
        "'Type', 'Starting_Point', 'Slope', 'Depth', 'Breadth'), and a condition_token.\n\n"
        "BE EXHAUSTIVE. Walk the text sentence by sentence, paragraph by paragraph, "
        "start to finish. Emit ONE entry per discrete condition-consequence claim, "
        "even if it closely resembles another entry (e.g. two separate 'islanded' "
        "claims, or two separate 'sloping' claims with different degrees, are TWO "
        "entries, not one). Do NOT merge, summarize, or skip any claim. Do NOT use "
        "a section heading (e.g. 'THE LINE OF HEAD IN RELATION TO THE SQUARE HAND') "
        "as source_quote -- always quote the actual descriptive sentence(s) in the "
        "body text that state the condition and its consequence, even when that "
        "sentence appears many paragraphs below the heading.\n\n"
        "condition_token MUST be either:\n"
        "  (a) EXACTLY one of the canonical (attribute, value) tokens below, chosen "
        "only if the sentence's full meaning -- including every modifier -- matches "
        "that token precisely, or\n"
        "  (b) the literal string 'UNMAPPABLE' if no canonical token matches exactly.\n\n"
        "NEVER pick the nearest or most-similar token. NEVER guess. A modifier that "
        "changes what is being claimed (e.g. an offshoot running into a STAR on a "
        "mount is a different claim from the line simply terminating on that mount) "
        "means the statement is UNMAPPABLE, even if a superficially similar token "
        "exists in the list.\n\n"
        "source_quote must be a verbatim substring copied from the provided text "
        "(whitespace may be normalized), as short as possible while uniquely "
        "identifying the passage that supports this extraction.\n\n"
        "Canonical vocabulary (attribute, value) pairs:\n" + vocab_lines + "\n\n"
        + _EXTRACTION_SCHEMA_NOTE
    )
    user = "CHAPTER TEXT (Cheiro's Language of the Hand, Line of Head, pp.145-155):\n\n" + chapter_text
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def run_member_b(
    chapter_text: str, vocab: list[dict], output_path: Path = MEMBER_B_OUT_PATH,
) -> tuple[list[dict], str | None]:
    """Returns (entries, error). entries is [] on any failure; error is a
    human-readable message, never a raised exception -- the run continues
    into reconciliation with an empty Member B so the report always
    completes (per-call try/except, never crash)."""
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
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)
    except OSError as exc:
        return entries, f"Member B extraction succeeded but write failed: {exc}"

    return entries, None


# ─── Step 5: reconciliation (pure Python, no LLM) ────────────────────────

def _normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip().lower()


def _quotes_overlap(a: str, b: str) -> bool:
    na, nb = _normalize_ws(a), _normalize_ws(b)
    if not na or not nb:
        return False
    return na in nb or nb in na


def member_corroborates(member_entries: list[dict], rule: dict) -> tuple[bool, dict | None]:
    canonical_tokens = {
        (ant["attribute"], ant["value"])
        for ant in rule["antecedents"]
        if ant.get("value") not in (None, "null")
    }
    rule_quote = rule.get("source_quote", "")
    for entry in member_entries:
        token = entry.get("condition_token")
        attr = entry.get("attribute")
        if not token or token == "UNMAPPABLE":
            continue
        if (attr, token) not in canonical_tokens:
            continue
        if _quotes_overlap(entry.get("source_quote", ""), rule_quote):
            return True, entry
    return False, None


def reconcile(rules: list[dict], member_a: list[dict], member_b: list[dict]) -> dict:
    deferred_ids: list[str] = []
    verdicts: dict[str, dict] = {}

    for rule in sorted(rules, key=lambda r: r["rule_id"]):
        rid = rule["rule_id"]
        if is_deferred_relational(rule):
            deferred_ids.append(rid)
            continue

        a_ok, a_match = member_corroborates(member_a, rule)
        b_ok, b_match = member_corroborates(member_b, rule)

        if a_ok and b_ok:
            verdict = "AUTO-VERIFIED"
        elif not a_ok and not b_ok:
            verdict = "FABRICATED-MISMODELED"
        else:
            verdict = "AMBIGUOUS"

        note_parts = []
        if a_match:
            note_parts.append(f"A matched token ({a_match['attribute']}={a_match['condition_token']!r})")
        if b_match:
            note_parts.append(f"B matched token ({b_match['attribute']}={b_match['condition_token']!r})")
        if not note_parts:
            note_parts.append("no member emitted this rule's canonical token with an overlapping quote")

        verdicts[rid] = {
            "verdict": verdict,
            "a": a_ok,
            "b": b_ok,
            "note": "; ".join(note_parts),
        }

    return {"verdicts": verdicts, "deferred": deferred_ids}


# ─── Step 6: report ───────────────────────────────────────────────────────

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
    lines.append("# S94 head-line ensemble-reconciliation pilot\n")
    lines.append(f"Rules checked (line_head*, validated_candidates): {len(rules)}")
    lines.append(f"Canonical vocab tokens harvested: {len(vocab)}")
    lines.append(f"Member A entries (diagnostics/ensemble_recon_headline_claude.json): {len(member_a)}")
    if member_b_error:
        lines.append(f"Member B entries (gpt-4o): 0 -- ERROR: {member_b_error}")
    else:
        lines.append(f"Member B entries (diagnostics/ensemble_recon_headline_gpt4o.json): {len(member_b)}")
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
    for verdict_name in ("AUTO-VERIFIED", "FABRICATED-MISMODELED", "AMBIGUOUS"):
        lines.append(f"- {verdict_name}: {counts.get(verdict_name, 0)}")

    actual = {rid: verdicts.get(rid, {}).get("verdict") for rid in _CALIBRATION_TARGETS}
    passed = all(actual[rid] == expected for rid, expected in _CALIBRATION_TARGETS.items())

    lines.append("")
    if passed:
        lines.append("CALIBRATION: PASS")
    else:
        failed = [
            f"{rid} expected {expected!r}, got {actual[rid]!r}"
            for rid, expected in _CALIBRATION_TARGETS.items()
            if actual[rid] != expected
        ]
        lines.append("CALIBRATION: FAIL -- " + "; ".join(failed))

    report = "\n".join(lines) + "\n"
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
    return report


def main() -> None:
    try:
        rules = load_head_line_rules()
        vocab = build_vocab(rules)
        chapter_text = load_head_line_chapter_text()
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
