"""
THROWAWAY SPIKE (spike_career_v2). Tests location-based citation: the
interpreter is handed pre-numbered segments and cites the NUMBER, never
types a quote, so a fabricated citation cannot be constructed -- the
segment either exists and says it or it doesn't. This does not become
product code and is not wired into the app.

WHY TWO PHASES, NOT ONE SCRIPT: the interpreter for this run is a Claude
Code SUBAGENT (no API key is available), and a subagent can only be
invoked by the orchestrating Claude Code session's own Agent tool -- a
plain Python script has no way to spawn one. So this file is split:

  build   -- pure, deterministic, no LLM. Reads the existing widened fact
             block and the existing v2 segment index, produces (1) a
             REDACTED fact block (birth data kept, the name "Sulabh"
             removed -- the subagent must not be told whose chart this
             is) and (2) the full subagent prompt (redacted fact block +
             all 135 segments + the fixed question + the output
             contract). Writes the prompt verbatim to --prompt-out and
             writes --meta-out (JSON: both fact blocks, size counts, the
             valid segment_id set, and a segment_id -> text lookup) for
             the verify phase to consume. Makes no network/LLM call.

  verify  -- pure, deterministic, no LLM. Takes the subagent's raw
             response (--response-in, saved by the orchestrating session
             byte-for-byte, never retyped) and --meta-in, and does the
             MECHANICAL verification: every cited segment_id checked
             against the real index (this is the actual fabrication
             test), each cited segment's full text surfaced for human
             judgment, and a best-effort LOW-CONFIDENCE line-co-occurrence
             scan of which chart facts named in each claim's statement
             text are traceable to a line in the fact block. Writes
             diagnostics/latest_run.md (overwrite).

Neither phase modifies any book JSON or product code.
"""

import argparse
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FACT_BLOCK_PATH = REPO_ROOT / "diagnostics" / "_spike2_fact_block.txt"
SEGMENT_INDEX_PATH = REPO_ROOT / "data" / "segment_index_bphs_career3.json"
DIAG_PATH = REPO_ROOT / "diagnostics" / "latest_run.md"

TARGET_UNIT_IDS = ["bphs1_ch21", "bphs1_ch24", "bphs1_ch34"]

QUESTION = "What does my chart say about my career?"

# Stated in chat BEFORE this run's subagent call, reproduced here verbatim
# so the report is self-contained.
PREDICTION = (
    "Predicted claim count: 8-11 (comparable to the previous spike's 11, "
    "same three chapters, same fact block richness). Predicted invalid "
    "segment ids: 0, with a small acknowledged chance of 1 -- the "
    "mechanism forces citation from a fixed set of real, visible ids "
    "rather than free recall, but the payload is large (all 135 segments "
    "across 3 chapters, ordinals running up to 97), which is exactly the "
    "condition under which a model could misremember or transpose a "
    "number it saw rather than inventing one from nothing."
)

# ---------------------------------------------------------------------------
# Redaction: the subagent must not be told whose chart this is. Birth date/
# time/place are the actual chart facts and are kept (per "reuse the fact
# block unchanged" for chart content); only the name token is removed.
# ---------------------------------------------------------------------------
_NAME_LINE_RE = re.compile(r"^(CHART FACTS \(WIDENED\) -- )Sulabh (\(born .*\))$", re.MULTILINE)


def build_redacted_fact_block(full_fact_block):
    redacted, n = _NAME_LINE_RE.subn(r"\1\2", full_fact_block)
    if n != 1:
        raise RuntimeError(
            "Expected to redact exactly one name line from the fact block, "
            "found %d matches -- fact block format has drifted, stop and "
            "check by hand rather than shipping an unverified redaction." % n
        )
    return redacted


# ---------------------------------------------------------------------------
# Segment payload
# ---------------------------------------------------------------------------
def load_segment_index():
    with open(SEGMENT_INDEX_PATH, encoding="utf-8") as f:
        return json.load(f)


def build_segment_payload(index_data):
    segs = [s for s in index_data["segments"] if s["unit_id"] in TARGET_UNIT_IDS]
    segs.sort(key=lambda s: (TARGET_UNIT_IDS.index(s["unit_id"]), s["ordinal"]))
    blocks = []
    for s in segs:
        blocks.append("[%s]\n%s" % (s["segment_id"], s["text"]))
    payload = "\n\n".join(blocks)
    valid_ids = [s["segment_id"] for s in segs]
    text_by_id = {s["segment_id"]: s["text"] for s in segs}
    return payload, valid_ids, text_by_id


OUTPUT_CONTRACT = (
    'Return STRICT JSON ONLY -- no markdown code fences, no prose before or '
    'after, nothing but the JSON object itself. The object must have '
    'exactly this shape:\n'
    '{"claims": [{"statement": "...", "segment_ids": ["..."]}], '
    '"silent_on": ["..."], "reading": "..."}'
)

INSTRUCTIONS = (
    "INSTRUCTIONS:\n"
    "- Use ONLY the CHART FACTS block and the SEGMENTS below. Do not use "
    "any outside knowledge of astrology, of this specific chart, or of any "
    "other source.\n"
    "- Never state a chart fact that is not present in the CHART FACTS "
    "block above.\n"
    "- Where a specific rule and a general principle both apply to the "
    "same fact, prefer the specific rule.\n"
    "- Cite sources by segment id ONLY, e.g. \"bphs1_ch24#36\". Never "
    "quote or reproduce segment text in your answer.\n"
    "- Where the segments do not cover something, stay silent on it in "
    "your answer and say so in \"silent_on\" instead of guessing.\n"
    "- " + OUTPUT_CONTRACT
)

TOOL_LOCKDOWN_PREAMBLE = (
    "You are answering a single, self-contained question using ONLY the "
    "material given to you in this message. Do not use any tools of any "
    "kind (no file reads, no directory listing, no web search, no code "
    "execution). Do not look anything up. Do not ask clarifying "
    "questions. Everything you need is below. Respond with only the JSON "
    "object described in the instructions -- nothing else."
)


def build_subagent_prompt(redacted_fact_block, segment_payload):
    parts = [
        TOOL_LOCKDOWN_PREAMBLE,
        "",
        "CHART FACTS:",
        redacted_fact_block.strip(),
        "",
        "SEGMENTS (numbered source passages -- cite by the bracketed id):",
        segment_payload,
        "",
        "QUESTION: " + QUESTION,
        "",
        INSTRUCTIONS,
    ]
    return "\n".join(parts)


def cmd_build(args):
    full_fact_block = FACT_BLOCK_PATH.read_text(encoding="utf-8")
    redacted_fact_block = build_redacted_fact_block(full_fact_block)

    index_data = load_segment_index()
    segment_payload, valid_ids, text_by_id = build_segment_payload(index_data)

    prompt = build_subagent_prompt(redacted_fact_block, segment_payload)

    Path(args.prompt_out).write_text(prompt, encoding="utf-8")

    meta = {
        "question": QUESTION,
        "full_fact_block": full_fact_block,
        "redacted_fact_block": redacted_fact_block,
        "segment_payload_char_count": len(segment_payload),
        "prompt_char_count": len(prompt),
        "prompt_token_estimate_chars_div_4": round(len(prompt) / 4),
        "valid_segment_ids": valid_ids,
        "segment_text_by_id": text_by_id,
        "prediction": PREDICTION,
    }
    Path(args.meta_out).write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Wrote prompt (%d chars, ~%d tokens est.) to %s" % (len(prompt), len(prompt) / 4, args.prompt_out))
    print("Wrote meta to %s" % args.meta_out)
    print("Valid segment ids: %d" % len(valid_ids))


# ---------------------------------------------------------------------------
# Mechanical verification
# ---------------------------------------------------------------------------
PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
    "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
DIGNITY_TERMS = ["Exalted", "Debilitated", "Own Sign", "Friendly", "Neutral", "Enemy", "combust", "retrograde"]

_HOUSE_NUM_RE = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\b\s*(?:house|lord)", re.IGNORECASE)
_HOUSE_OF_RE = re.compile(r"\bhouse\s+(\d{1,2})\b", re.IGNORECASE)


def _mentioned_house_numbers(statement):
    nums = set()
    for m in _HOUSE_NUM_RE.finditer(statement):
        n = int(m.group(1))
        if 1 <= n <= 12:
            nums.add(n)
    for m in _HOUSE_OF_RE.finditer(statement):
        n = int(m.group(1))
        if 1 <= n <= 12:
            nums.add(n)
    return sorted(nums)


def _line_contains_both(lines, word_a, word_b):
    pat_a = re.compile(r"\b%s\b" % re.escape(str(word_a)), re.IGNORECASE)
    pat_b = re.compile(r"\b%s\b" % re.escape(str(word_b)), re.IGNORECASE)
    for line in lines:
        if pat_a.search(line) and pat_b.search(line):
            return True, line.strip()
    return False, None


def low_confidence_fact_scan(statement, full_fact_block):
    """Best-effort, mechanical (no LLM) scan: for each planet/house/sign/
    dignity/dasha token named in a claim's statement text, check whether
    that token co-occurs on some SINGLE LINE of the fact block with
    another token also named in the statement. This is a heuristic
    (line co-occurrence, not real semantic verification) -- every row is
    explicitly LOW-CONFIDENCE and is for a human to actually judge, not a
    pass/fail gate.
    """
    lines = full_fact_block.splitlines()
    rows = []

    mentioned_planets = [p for p in PLANETS if re.search(r"\b%s\b" % p, statement)]
    mentioned_signs = [s for s in SIGNS if re.search(r"\b%s\b" % s, statement)]
    mentioned_dignity = [d for d in DIGNITY_TERMS if re.search(r"\b%s\b" % re.escape(d), statement, re.IGNORECASE)]
    mentioned_houses = _mentioned_house_numbers(statement)
    mentions_ascendant = bool(re.search(r"\b(ascendant|lagna)\b", statement, re.IGNORECASE))
    mentions_conjunct = bool(re.search(r"\bconjunct", statement, re.IGNORECASE))
    mentions_mahadasha = bool(re.search(r"\bmahadasha\b", statement, re.IGNORECASE))
    mentions_antardasha = bool(re.search(r"\bantardasha\b", statement, re.IGNORECASE))

    for planet in mentioned_planets:
        for house in mentioned_houses:
            found, line = _line_contains_both(lines, planet, house)
            rows.append({"fact": "%s + house %d" % (planet, house), "found_in_fact_block": found, "evidence_line": line})
        for sign in mentioned_signs:
            found, line = _line_contains_both(lines, planet, sign)
            rows.append({"fact": "%s + %s" % (planet, sign), "found_in_fact_block": found, "evidence_line": line})
        for dignity in mentioned_dignity:
            found, line = _line_contains_both(lines, planet, dignity)
            rows.append({"fact": "%s + %s" % (planet, dignity), "found_in_fact_block": found, "evidence_line": line})
        if mentions_mahadasha:
            found, line = _line_contains_both(lines, planet, "Mahadasha")
            rows.append({"fact": "%s + Mahadasha" % planet, "found_in_fact_block": found, "evidence_line": line})
        if mentions_antardasha:
            found, line = _line_contains_both(lines, planet, "Antardasha")
            rows.append({"fact": "%s + Antardasha" % planet, "found_in_fact_block": found, "evidence_line": line})

    if mentions_conjunct and len(mentioned_planets) >= 2:
        for i in range(len(mentioned_planets)):
            for j in range(i + 1, len(mentioned_planets)):
                found, line = _line_contains_both(lines, mentioned_planets[i], mentioned_planets[j])
                rows.append({
                    "fact": "%s conjunct %s" % (mentioned_planets[i], mentioned_planets[j]),
                    "found_in_fact_block": found,
                    "evidence_line": line,
                })

    if mentions_ascendant:
        for sign in mentioned_signs:
            found, line = _line_contains_both(lines, "Ascendant", sign)
            rows.append({"fact": "Ascendant + %s" % sign, "found_in_fact_block": found, "evidence_line": line})

    return rows


def _strip_markdown_fence(text):
    stripped = text.strip()
    m = re.match(r"^```(?:json)?\s*\n(.*)\n```$", stripped, re.DOTALL)
    if m:
        return m.group(1)
    return stripped


def cmd_verify(args):
    meta = json.loads(Path(args.meta_in).read_text(encoding="utf-8"))
    raw_response = Path(args.response_in).read_text(encoding="utf-8")

    valid_ids = set(meta["valid_segment_ids"])
    text_by_id = meta["segment_text_by_id"]
    full_fact_block = meta["full_fact_block"]
    redacted_fact_block = meta["redacted_fact_block"]

    parse_error = None
    parsed = None
    try:
        parsed = json.loads(raw_response)
    except json.JSONDecodeError as e1:
        try:
            parsed = json.loads(_strip_markdown_fence(raw_response))
        except json.JSONDecodeError as e2:
            parse_error = "json.loads failed on raw response (%s) and on fence-stripped response (%s)" % (e1, e2)

    report = []
    report.append("# spike_career_v2.py -- latest run")
    report.append("")
    report.append(
        "Location-based citation test: the interpreter (a fresh Claude "
        "Code subagent, no prior context) is handed pre-numbered segments "
        "and cites the number; it never types a quote. This run does NOT "
        "retry -- one shot, reported as-is."
    )
    report.append("")

    report.append("## Prediction (stated before this run's subagent call)")
    report.append("")
    report.append(meta["prediction"])
    report.append("")

    report.append("## 1. Fact block, verbatim")
    report.append("")
    report.append("Full (as reused unchanged from the previous spike, for this report's own record):")
    report.append("```")
    report.append(full_fact_block)
    report.append("```")
    report.append("")
    report.append(
        "Redacted version actually sent to the subagent (name removed per "
        "the isolation requirement; birth date/time/place kept as real "
        "chart data):"
    )
    report.append("```")
    report.append(redacted_fact_block)
    report.append("```")
    report.append("")

    report.append("## 2. Payload size and verbatim proof of what the subagent received")
    report.append("")
    report.append("| measure | value |")
    report.append("|---|---|")
    report.append("| segments included | %d (all of bphs1_ch21/24/34) |" % len(valid_ids))
    report.append("| segment text chars | %d |" % meta["segment_payload_char_count"])
    report.append("| full prompt chars (fact block + segments + instructions) | %d |" % meta["prompt_char_count"])
    report.append("| estimated tokens (chars / 4, no real tokenizer available offline) | ~%d |" % meta["prompt_token_estimate_chars_div_4"])
    report.append("")
    report.append(
        "The exact prompt text below is byte-for-byte what was passed as "
        "the subagent's entire instruction -- nothing else was in its "
        "context (no session history, no file paths, no prior spike "
        "conclusions):"
    )
    report.append("")
    prompt_text = Path(args.prompt_in).read_text(encoding="utf-8") if args.prompt_in else None
    if prompt_text is not None:
        report.append("```")
        report.append(prompt_text)
        report.append("```")
    else:
        report.append("(--prompt-in not supplied to verify -- prompt text omitted from this report)")
    report.append("")

    report.append("## 3. Raw subagent response, verbatim, before parsing")
    report.append("")
    report.append("```")
    report.append(raw_response)
    report.append("```")
    report.append("")
    if parse_error:
        report.append("**PARSE FAILURE:** %s" % parse_error)
        report.append("")
        report.append("Per the task's one-shot rule, this is reported as-is; no retry was attempted.")
        report.append("")
        write_report(report)
        return

    claims = parsed.get("claims", [])
    silent_on = parsed.get("silent_on", [])
    reading = parsed.get("reading", "")

    report.append("## 4. Per-claim detail (headline -- for human judgment)")
    report.append("")
    all_cited_ids = []
    invalid_ids_found = []
    for i, claim in enumerate(claims, start=1):
        statement = claim.get("statement", "")
        seg_ids = claim.get("segment_ids", [])
        report.append("### Claim %d" % i)
        report.append("")
        report.append("Statement: %s" % statement)
        report.append("")
        report.append("Cited segment ids: %s" % (seg_ids if seg_ids else "(none)"))
        report.append("")
        for sid in seg_ids:
            all_cited_ids.append(sid)
            if sid not in valid_ids:
                invalid_ids_found.append((i, sid))
                report.append("- `%s` -- **DOES NOT EXIST IN THE INDEX (invalid citation)**" % sid)
            else:
                report.append("- `%s`:" % sid)
                report.append("  ```")
                for line in text_by_id[sid].splitlines():
                    report.append("  " + line)
                report.append("  ```")
        report.append("")
        report.append("Chart-fact scan for this statement (LOW-CONFIDENCE, line-co-occurrence heuristic, not semantic verification -- for human judgment):")
        rows = low_confidence_fact_scan(statement, full_fact_block)
        if not rows:
            report.append("- (no checkable planet/house/sign/dignity/dasha tokens detected in this statement)")
        else:
            for r in rows:
                status = "FOUND" if r["found_in_fact_block"] else "NOT FOUND"
                evidence = (" -- `%s`" % r["evidence_line"]) if r["evidence_line"] else ""
                report.append("- LOW-CONFIDENCE: %s: %s%s" % (r["fact"], status, evidence))
        report.append("")

    report.append("## 5. Invalid segment ids (the real fabrication signal)")
    report.append("")
    if invalid_ids_found:
        for i, sid in invalid_ids_found:
            report.append("- Claim %d cited `%s`, which does not exist in the 135-segment index." % (i, sid))
    else:
        report.append("None. Every cited segment_id resolved to a real, existing segment.")
    report.append("")

    report.append("## 6. Counts")
    report.append("")
    report.append("| measure | value |")
    report.append("|---|---|")
    report.append("| claims | %d |" % len(claims))
    report.append("| distinct segments cited | %d |" % len(set(all_cited_ids)))
    report.append("| total citations (incl. repeats) | %d |" % len(all_cited_ids))
    report.append("| invalid segment ids | %d |" % len(invalid_ids_found))
    report.append("")

    report.append("## 7. silent_on")
    report.append("")
    if silent_on:
        for s in silent_on:
            report.append("- %s" % s)
    else:
        report.append("(empty)")
    report.append("")

    report.append("## 8. Final reading text")
    report.append("")
    report.append(reading if reading else "(empty)")
    report.append("")

    report.append("## Production note: this interpreter path does not exist in production")
    report.append("")
    report.append(
        "Production has no way to call a Claude Code subagent -- the only "
        "available key is OpenAI's, so the real interpreter call would "
        "need to be a normal OpenAI chat completion (e.g. via the "
        "`openai` Python client) carrying this exact same payload shape "
        "(fact block + numbered segments + question + JSON-only "
        "instructions), ideally with `response_format={\"type\": "
        "\"json_object\"}` to enforce strict JSON without a fences-parsing "
        "fallback. The size measured in section 2 (~%d tokens estimated "
        "for all 135 raw segments plus the fact block and instructions) "
        "sits at or above a 30k-tokens-per-minute ceiling on its own, "
        "before accounting for the response tokens on top of it -- "
        "sending all three chapters' full segment text in one call is not "
        "viable at that ceiling, and a real integration would need to cut "
        "the segments sent per call (e.g. a retrieval or page-range "
        "pre-filter, the same shape of fix already used for palm "
        "retrieval) rather than attempting this payload whole. Caveat "
        "measured while assembling this run, not modeled: a real "
        "subword tokenizer applied to the first ~37%% of this same "
        "payload (via this session's own file-reading tool, which reports "
        "an actual token count) counted roughly 5x more tokens than the "
        "chars/4 estimate above for that slice -- Devanagari OCR text is "
        "the likely cause, since BPE-style tokenizers are not efficient on "
        "non-Latin scripts. That was a different tokenizer than OpenAI's, "
        "so the exact multiplier does not carry over, but the direction "
        "does: the true OpenAI token count for this payload is very "
        "likely well above the ~31k chars/4 figure, not at or near it, "
        "making the 30k-TPM ceiling problem worse than the headline "
        "number here suggests."
        % meta["prompt_token_estimate_chars_div_4"]
    )
    report.append("")

    write_report(report)
    print("Wrote report to %s" % DIAG_PATH)
    print("claims=%d invalid_ids=%d" % (len(claims), len(invalid_ids_found)))


def write_report(lines):
    DIAG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DIAG_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build")
    p_build.add_argument("--prompt-out", required=True)
    p_build.add_argument("--meta-out", required=True)
    p_build.set_defaults(func=cmd_build)

    p_verify = sub.add_parser("verify")
    p_verify.add_argument("--meta-in", required=True)
    p_verify.add_argument("--response-in", required=True)
    p_verify.add_argument("--prompt-in", required=False, default=None)
    p_verify.set_defaults(func=cmd_verify)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
