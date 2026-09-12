"""
scripts/verb_to_token_llm_map_probe.py

MEASUREMENT HARNESS ONLY -- no production file is imported for mutation, no
source commit follows this run. Report goes to diagnostics/latest_run.md
(overwrite).

Single TEXT-ONLY call (no vision, no image): asks an LLM to map the 6
distinct free verbs captured by the free_verb_capture_probe.py (S100
follow-up) run onto the closed 8-token typed-relationship vocabulary, or
"unclear" if no token clearly fits. This is a sanity check on the
deterministic substring-mapping table used there (which was found to miss
"starts together" and "runs alongside") -- an independent, LLM-judged
second opinion on the same 6 verbs, not a re-run of any vision probe.
"""

from __future__ import annotations

import json
import sys
import time
import traceback
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

import agent.palm_processor as pp  # noqa: E402  (production module, read-only use)
from openai import OpenAI  # noqa: E402

# ─────────────────────────── CONFIG ───────────────────────────────────────
# The 6 distinct free verbs captured in the last vision run (S100 follow-up,
# free_verb_capture_probe.py) -- hardcoded verbatim, NOT re-derived from a
# fresh vision call.
VERBS: list[str] = [
    "starts together", "merges with", "starts from",
    "touches", "crosses", "runs alongside",
]

# Cheiro-grounded one-line gloss per token, as supplied by the instructing
# prompt. Token STRINGS themselves are reused from agent.palm_processor's
# own SSOT menu helper below, never re-listed independently of it.
TOKEN_GLOSSES: dict[str, str] = {
    "joins_at_origin": "two lines share/merge at their beginning",
    "meets": "lines come together / one reaches and joins another mid-course",
    "cuts": "this line crosses over another",
    "cut_by": "another line crosses over this one",
    "touches": "lines make contact without crossing",
    "stopped_by": "this line is barred/halted by another",
    "takes_possession_of": "this line leaves its place and absorbs/overtakes another",
    "branch_in": "a branch runs in and joins from another line/mount",
}

MODEL = "gpt-4o"
TEMPERATURE = 0.0

REPORT_PATH = _REPO_ROOT / "diagnostics" / "latest_run.md"


def _token_menu_list() -> list[str]:
    """Reuses agent.palm_processor._relationship_type_menu for the exact
    token strings (SSOT), parsed out of its "{a | b | c}" format -- not
    re-listed independently."""
    raw = pp._relationship_type_menu()
    return [t.strip() for t in raw.strip("{}").split("|")]


def build_prompt(tokens: list[str]) -> str:
    gloss_lines = "\n".join(f"  {tok} = {TOKEN_GLOSSES[tok]}" for tok in tokens)
    verb_list = "\n".join(f"  - {v!r}" for v in VERBS)
    return (
        "You are mapping free-text verbs describing a palm-line crossing "
        "onto a closed, Cheiro-grounded vocabulary of relationship types. "
        "Here are the 8 tokens and their one-line glosses:\n"
        f"{gloss_lines}\n\n"
        "Here are the free verbs to map:\n"
        f"{verb_list}\n\n"
        "For EACH verb, decide which ONE token it clearly matches, if any. "
        "If a verb does not clearly match exactly one token, return "
        "\"unclear\" for that verb's token -- never force a fit.\n\n"
        "Return STRICT JSON only, no markdown, no commentary, in exactly "
        "this shape:\n"
        "{\n"
        '  "<verb>": {"token": "<one of the 8 tokens above, or \\"unclear\\">", '
        '"confidence": "high|low", "reason": "<short reason>"},\n'
        "  ...\n"
        "}\n"
        "Include all 6 verbs as keys, exactly as given above."
    )


def call_llm(prompt: str) -> str:
    client = OpenAI()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=TEMPERATURE,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


def main() -> None:
    t0 = time.time()
    tokens = _token_menu_list()
    missing_glosses = [t for t in tokens if t not in TOKEN_GLOSSES]
    if missing_glosses:
        raise RuntimeError(
            f"verb_to_token_llm_map_probe: TOKEN_GLOSSES missing entries for "
            f"{missing_glosses} -- registry token set and the supplied gloss "
            "set have diverged."
        )

    prompt = build_prompt(tokens)

    error_detail: str | None = None
    parsed: dict | None = None
    try:
        raw = call_llm(prompt)
        parsed = json.loads(raw)
    except Exception as exc:  # noqa: BLE001 -- a single failed call must still produce a report
        error_detail = f"{type(exc).__name__}: {exc}"
        print(f"  [ERROR] LLM call/parse failed: {error_detail}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)

    # ── report assembly ─────────────────────────────────────────────
    lines_out: list[str] = []
    lines_out.append("# Verb-to-Token LLM Mapping Probe (S100 follow-up, text-only)\n")
    lines_out.append(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines_out.append(f"**Model:** {MODEL}, temperature={TEMPERATURE} (text-only, no vision, no image)  ")
    lines_out.append(
        "**Scope:** measurement harness only. No production file modified. "
        "No commit follows this run.\n"
    )
    lines_out.append(
        "**Context:** the 6 verbs below are the distinct free verbs captured "
        "by free_verb_capture_probe.py's live ARM G output (a prior vision "
        "run, NOT re-run here) -- this is a single text-only LLM call asking "
        "for an independent second opinion on the deterministic substring-"
        "mapping table used there (which was found to miss \"starts "
        "together\" and \"runs alongside\").\n"
    )

    if error_detail:
        lines_out.append(f"## ERROR\n\nLLM call or JSON parse failed: {error_detail}\n")
        lines_out.append("No table produced -- see error above.\n")
    else:
        rows = []
        high_count = 0
        low_count = 0
        unclear_count = 0
        anomalies = []
        for verb in VERBS:
            entry = parsed.get(verb) if isinstance(parsed, dict) else None
            if not isinstance(entry, dict):
                anomalies.append(f"{verb!r}: missing or malformed entry in LLM response")
                rows.append((verb, "MISSING", "-", "no entry returned by LLM"))
                continue
            token = entry.get("token", "MISSING")
            confidence = entry.get("confidence", "-")
            reason = entry.get("reason", "-")
            if token != "unclear" and token not in tokens:
                anomalies.append(f"{verb!r}: LLM returned token {token!r}, not in the 8-token vocab or 'unclear'")
            if token == "unclear":
                unclear_count += 1
            elif confidence == "high":
                high_count += 1
            elif confidence == "low":
                low_count += 1
            else:
                anomalies.append(f"{verb!r}: unexpected confidence value {confidence!r}")
            rows.append((verb, token, confidence, reason))

        lines_out.append("## Mapping Results\n")
        lines_out.append("| Free verb | Mapped token | Confidence | Reason |")
        lines_out.append("|---|---|---|---|")
        for verb, token, confidence, reason in rows:
            lines_out.append(f"| {verb} | {token} | {confidence} | {reason} |")

        lines_out.append(f"\n**Summary:** {high_count}/6 high-confidence mapped, "
                          f"{low_count}/6 low-confidence mapped, {unclear_count}/6 unclear.\n")

        if anomalies:
            lines_out.append("**Anomalies (response shape issues, not silently ignored):**\n")
            for a in anomalies:
                lines_out.append(f"  - {a}")
            lines_out.append("")

    report_text = "\n".join(lines_out) + "\n"
    REPORT_PATH.write_text(report_text, encoding="utf-8")

    elapsed = time.time() - t0
    print(f"Done in {elapsed:.1f}s. Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
