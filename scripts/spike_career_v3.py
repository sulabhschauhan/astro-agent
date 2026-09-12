"""
THROWAWAY SPIKE (spike_career_v3). Controlled A/B against spike_career_v2:
same chart, same fact block, same question, same three units, same JSON
contract, same fresh-subagent isolation, same one-shot rule. The ONLY
variable is the segment payload text: v3 strips Devanagari-block
characters (U+0900-U+097F) from the payload before it is handed to the
interpreter, because (a) v2 measured Devanagari OCR text tokenizing at
roughly 5x the chars/4 estimate for a real subword tokenizer, and (b) the
interpreter cannot read Devanagari and it contributes zero interpretive
value to its answer (v2's 13 claims all cited English-derived facts).

Does NOT touch data/segment_index_bphs_career3.json or any book JSON --
the stored index keeps the full original text; stripping is
presentation-layer only, applied to a copy of the text at payload-build
time. Does NOT call OpenAI or the Anthropic API -- the interpreter is a
fresh Claude Code subagent, exactly as in v2, invoked by the orchestrating
session's own Agent tool (a plain script cannot spawn one).

TWO PHASES, same reason as v2: "build" is pure and deterministic (strips
Devanagari, measures real+estimated token counts both ways, writes the
prompt for the orchestrating session to hand to a subagent verbatim);
"verify" is pure and deterministic (checks cited segment_ids against the
real index, surfaces each cited segment's FULL ORIGINAL text -- with
Devanagari intact, read from the stored index, never the stripped copy --
and runs the same LOW-CONFIDENCE fact-scan heuristic as v2). The A/B
comparison and the qualitative quality judgment both need a human/model
read of actual content, not a mechanical rule: the script computes the
mechanical set differences (claim counts, which segments were cited by
both runs / only one), and takes the qualitative verdict as a separate
small text input rather than fabricating one.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FACT_BLOCK_PATH = REPO_ROOT / "diagnostics" / "_spike2_fact_block.txt"
SEGMENT_INDEX_PATH = REPO_ROOT / "data" / "segment_index_bphs_career3.json"
DIAG_PATH = REPO_ROOT / "diagnostics" / "latest_run.md"

TARGET_UNIT_IDS = ["bphs1_ch21", "bphs1_ch24", "bphs1_ch34"]
QUESTION = "What does my chart say about my career?"

PREDICTION = (
    "Predicted token reduction: 50-70% of the real (subword) token count. "
    "Devanagari is only ~11.9% of raw characters in these three chapters "
    "(measured directly: 14155 of 118772 chars) but a quick tiktoken "
    "sanity check on isolated Devanagari text showed it tokenizing at "
    "roughly 1 token per character, versus roughly 0.25-0.3 tokens per "
    "character for English prose -- a disproportionate share of total "
    "tokens for a disproportionately small share of characters. Predicted "
    "claim count: 10-14, similar to v2's 13. Predicted quality: HOLD -- "
    "v2's 13 claims all cited English-derived facts; nothing in v2's "
    "output drew on Devanagari content, so removing it should cost "
    "nothing."
)

DEVANAGARI_RE = re.compile(r"[ऀ-ॿ]")
ENGLISH_RUN_RE = re.compile(r"[A-Za-z]{3,}")


def strip_devanagari(text):
    stripped = DEVANAGARI_RE.sub("", text)
    stripped = re.sub(r"[ \t]+", " ", stripped)
    stripped = re.sub(r" *\n *", "\n", stripped)
    stripped = re.sub(r"\n{3,}", "\n\n", stripped)
    return stripped.strip()


# ---------------------------------------------------------------------------
# Redaction (identical to v2)
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


def ordered_segments(index_data):
    segs = [s for s in index_data["segments"] if s["unit_id"] in TARGET_UNIT_IDS]
    segs.sort(key=lambda s: (TARGET_UNIT_IDS.index(s["unit_id"]), s["ordinal"]))
    return segs


def build_payload(segs, strip):
    blocks = []
    empty_after_strip = []
    for s in segs:
        text = strip_devanagari(s["text"]) if strip else s["text"]
        if strip and not ENGLISH_RUN_RE.search(text):
            empty_after_strip.append(s["segment_id"])
            text = "(no readable English content remains after Devanagari removal)"
        blocks.append("[%s]\n%s" % (s["segment_id"], text))
    payload = "\n\n".join(blocks)
    return payload, empty_after_strip


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
    "any outside knowledge of astrology, of this specific chart, or of "
    "any other source.\n"
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


# ---------------------------------------------------------------------------
# Token measurement
# ---------------------------------------------------------------------------
def get_tiktoken_encoder():
    try:
        import tiktoken
    except ImportError:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "tiktoken"], check=True)
            import tiktoken
        except Exception as e:
            return None, "tiktoken unavailable and could not be installed (%s)" % e
    try:
        return tiktoken.get_encoding("cl100k_base"), None
    except Exception as e:
        return None, "tiktoken installed but cl100k_base encoding failed to load (%s)" % e


def cmd_build(args):
    full_fact_block = FACT_BLOCK_PATH.read_text(encoding="utf-8")
    redacted_fact_block = build_redacted_fact_block(full_fact_block)

    index_data = load_segment_index()
    segs = ordered_segments(index_data)

    payload_with_dev, _ = build_payload(segs, strip=False)
    payload_stripped, empty_after_strip = build_payload(segs, strip=True)

    prompt_with_dev = build_subagent_prompt(redacted_fact_block, payload_with_dev)
    prompt_stripped = build_subagent_prompt(redacted_fact_block, payload_stripped)

    encoder, tiktoken_error = get_tiktoken_encoder()

    def measure(text):
        m = {"chars": len(text), "chars_div_4": round(len(text) / 4)}
        if encoder is not None:
            m["real_tokens_cl100k_base"] = len(encoder.encode(text))
        else:
            m["real_tokens_cl100k_base"] = None
        return m

    measurements = {
        "payload_with_devanagari": measure(payload_with_dev),
        "payload_stripped": measure(payload_stripped),
        "full_prompt_with_devanagari": measure(prompt_with_dev),
        "full_prompt_stripped": measure(prompt_stripped),
        "tiktoken_error": tiktoken_error,
    }

    Path(args.prompt_out).write_text(prompt_stripped, encoding="utf-8")

    meta = {
        "question": QUESTION,
        "full_fact_block": full_fact_block,
        "redacted_fact_block": redacted_fact_block,
        "valid_segment_ids": [s["segment_id"] for s in segs],
        "segment_text_by_id_original": {s["segment_id"]: s["text"] for s in segs},
        "empty_after_strip": empty_after_strip,
        "measurements": measurements,
        "prediction": PREDICTION,
    }
    Path(args.meta_out).write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Wrote stripped prompt (%d chars) to %s" % (len(prompt_stripped), args.prompt_out))
    print("Wrote meta to %s" % args.meta_out)
    print("Empty-after-strip segments: %d" % len(empty_after_strip))
    print("tiktoken available: %s" % (encoder is not None))
    if measurements["full_prompt_with_devanagari"]["real_tokens_cl100k_base"]:
        wd = measurements["full_prompt_with_devanagari"]["real_tokens_cl100k_base"]
        wo = measurements["full_prompt_stripped"]["real_tokens_cl100k_base"]
        print("Real tokens: with-Devanagari=%d, stripped=%d, reduction=%.1f%%" % (wd, wo, 100 * (wd - wo) / wd))


# ---------------------------------------------------------------------------
# Mechanical verification (LOW-CONFIDENCE fact scan identical to v2)
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
    text_by_id = meta["segment_text_by_id_original"]
    full_fact_block = meta["full_fact_block"]
    redacted_fact_block = meta["redacted_fact_block"]
    measurements = meta["measurements"]
    empty_after_strip = meta["empty_after_strip"]

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
    report.append("# spike_career_v3.py -- latest run")
    report.append("")
    report.append(
        "Controlled A/B against v2: identical chart, fact block, question, "
        "units, JSON contract, fresh-subagent isolation, one-shot rule. "
        "The ONLY variable is that the SEGMENT payload has Devanagari-"
        "block characters (U+0900-U+097F) stripped before being handed to "
        "the interpreter. The stored index (`data/segment_index_bphs_"
        "career3.json`) is untouched -- stripping is presentation-layer "
        "only, and the verifier below prints each cited segment's FULL "
        "ORIGINAL text (Devanagari intact) from that stored index."
    )
    report.append("")

    report.append("## Prediction (stated before this run's subagent call)")
    report.append("")
    report.append(meta["prediction"])
    report.append("")

    report.append("## 1. Token measurement (the headline)")
    report.append("")
    if measurements["tiktoken_error"]:
        report.append("**tiktoken unavailable: %s. Real token counts NOT measured; chars/4 only below.**" % measurements["tiktoken_error"])
        report.append("")
    report.append("| measure | WITH Devanagari | stripped | reduction |")
    report.append("|---|---|---|---|")
    wd = measurements["full_prompt_with_devanagari"]
    wo = measurements["full_prompt_stripped"]
    report.append("| full prompt chars | %d | %d | %.1f%% |" % (wd["chars"], wo["chars"], 100 * (wd["chars"] - wo["chars"]) / wd["chars"]))
    report.append("| full prompt chars/4 estimate | %d | %d | %.1f%% |" % (wd["chars_div_4"], wo["chars_div_4"], 100 * (wd["chars_div_4"] - wo["chars_div_4"]) / wd["chars_div_4"]))
    if wd["real_tokens_cl100k_base"] is not None:
        report.append(
            "| **full prompt REAL tokens (tiktoken cl100k_base)** | **%d** | **%d** | **%.1f%%** |"
            % (wd["real_tokens_cl100k_base"], wo["real_tokens_cl100k_base"], 100 * (wd["real_tokens_cl100k_base"] - wo["real_tokens_cl100k_base"]) / wd["real_tokens_cl100k_base"])
        )
        multiplier = wd["real_tokens_cl100k_base"] / wo["real_tokens_cl100k_base"]
        report.append("")
        report.append(
            "Observed multiplier: the WITH-Devanagari prompt costs **%.2fx** the "
            "stripped prompt's real token count. This is the number that decides "
            "how many chapters of raw OCR text can be sent per question at a "
            "fixed token budget." % multiplier
        )
    else:
        report.append("| full prompt REAL tokens | N/A (tiktoken unavailable) | N/A | N/A |")
    report.append("")
    pwd = measurements["payload_with_devanagari"]
    pwo = measurements["payload_stripped"]
    report.append("Segment-payload-only breakdown (excludes fact block + instructions):")
    report.append("")
    report.append("| measure | WITH Devanagari | stripped |")
    report.append("|---|---|---|")
    report.append("| chars | %d | %d |" % (pwd["chars"], pwo["chars"]))
    if pwd["real_tokens_cl100k_base"] is not None:
        report.append("| real tokens | %d | %d |" % (pwd["real_tokens_cl100k_base"], pwo["real_tokens_cl100k_base"]))
    report.append("")

    report.append("## 2. Segments left empty by stripping")
    report.append("")
    report.append("Count: %d" % len(empty_after_strip))
    if empty_after_strip:
        report.append("")
        report.append("segment_ids: %s" % ", ".join(empty_after_strip))
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

    report.append("## 4. Per-claim detail (full ORIGINAL segment text, Devanagari intact)")
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

    report.append("## 9. A/B comparison against v2")
    report.append("")
    v3_cited = set(all_cited_ids)
    if args.v2_response_in:
        v2_raw = Path(args.v2_response_in).read_text(encoding="utf-8")
        try:
            v2_parsed = json.loads(v2_raw)
        except json.JSONDecodeError:
            v2_parsed = json.loads(_strip_markdown_fence(v2_raw))
        v2_claims = v2_parsed.get("claims", [])
        v2_cited = set()
        for c in v2_claims:
            v2_cited.update(c.get("segment_ids", []))

        both = sorted(v3_cited & v2_cited)
        only_v2 = sorted(v2_cited - v3_cited)
        only_v3 = sorted(v3_cited - v2_cited)

        report.append("| measure | v2 | v3 |")
        report.append("|---|---|---|")
        report.append("| claim count | %d | %d |" % (len(v2_claims), len(claims)))
        report.append("| distinct segments cited | %d | %d |" % (len(v2_cited), len(v3_cited)))
        report.append("")
        report.append("Segments cited in BOTH runs (%d): %s" % (len(both), ", ".join(both) if both else "(none)"))
        report.append("")
        report.append("Segments cited ONLY in v2 (%d): %s" % (len(only_v2), ", ".join(only_v2) if only_v2 else "(none)"))
        report.append("")
        report.append("Segments cited ONLY in v3 (%d): %s" % (len(only_v3), ", ".join(only_v3) if only_v3 else "(none)"))
        report.append("")
        if args.quality_note_in:
            quality_note = Path(args.quality_note_in).read_text(encoding="utf-8").strip()
        else:
            quality_note = "(no quality-note file supplied to verify -- honest read not recorded)"
        report.append("### Honest read on answer quality (v2 vs v3)")
        report.append("")
        report.append(quality_note)
        report.append("")
    else:
        report.append("(--v2-response-in not supplied -- A/B comparison skipped)")
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
    p_verify.add_argument("--v2-response-in", required=False, default=None)
    p_verify.add_argument("--quality-note-in", required=False, default=None)
    p_verify.set_defaults(func=cmd_verify)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
