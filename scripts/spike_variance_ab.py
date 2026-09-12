"""
THROWAWAY SPIKE (spike_variance_ab). Separates two candidate explanations
for the v2-vs-v3 gap (13 claims/18 citations vs 5 claims/6 citations,
single run each): (A) stripping Devanagari removed verse-boundary
structure and degraded navigation, specifically hurting bphs1_ch34's
denser interleaved verses, vs (B) ordinary run-to-run variance between
two independent, non-deterministic subagent invocations. A single run
per arm cannot tell these apart; this script drives a 3-runs-per-arm,
6-total, interleaved (WITH, STRIP, WITH, STRIP, WITH, STRIP) design and
does the mechanical measurement + analysis.

Does NOT re-measure anything already settled (token counts, whether
stripping empties segments): those are taken as given per the task's
own SETTLED section. Does NOT call OpenAI or the Anthropic API -- each
of the 6 interpreter calls is a fresh Claude Code subagent with no prior
context, invoked by the orchestrating session's own Agent tool (a plain
script cannot spawn one). Does NOT touch data/segment_index_bphs_
career3.json or any book JSON.

TWO PHASES, same reason as v2/v3: "build" is pure and deterministic
(constructs the WITH and STRIP prompts -- byte-identical in construction
to spike_career_v2.py/v3.py's prompts -- and writes analysis metadata).
"analyze" is pure and deterministic (parses the 6 raw responses the
orchestrating session collected, computes the per-run measures and the
four required analyses, and writes the report). The plain-language SAFE
/ HARMFUL / STILL UNDETERMINED conclusion is a human/model judgment on
the actual data, not a mechanical rule, so it is taken as a separate
small text input (--verdict-in) rather than fabricated by the script,
same pattern as v3's quality-note input.
"""

import argparse
import json
import re
import statistics
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FACT_BLOCK_PATH = REPO_ROOT / "diagnostics" / "_spike2_fact_block.txt"
SEGMENT_INDEX_PATH = REPO_ROOT / "data" / "segment_index_bphs_career3.json"
DIAG_PATH = REPO_ROOT / "diagnostics" / "latest_run.md"

TARGET_UNIT_IDS = ["bphs1_ch21", "bphs1_ch24", "bphs1_ch34"]
QUESTION = "What does my chart say about my career?"

RAJA_YOGA_SEGMENT_ID = "bphs1_ch34#5"
SUN_SAGITTARIUS_SPECIFIC_SEGMENT_ID = "bphs1_ch34#19"  # "Mars and the Sun are auspicious" (Sagittarius-specific)
SUN_GENERAL_NATURALS_SEGMENT_ID = "bphs1_ch34#4"  # "Malefics are the Sun, Saturn and Mars" (general classification)

PREDICTION = (
    "Predicted WITH-arm claim count range: 9-15. Predicted STRIP-arm claim "
    "count range: 5-11 -- probably touching/overlapping the WITH range at "
    "n=3, because claim-count is a noisy, whole-run-level output and "
    "ordinary sampling variance (B) is a real, large effect on its own. "
    "But (A) and (B) are not treated as mutually exclusive: the specific "
    "prediction is that the RAJA YOGA CITATION RATE (whether bphs1_ch34#5 "
    "gets cited at all), not raw claim count, is where a structural, "
    "chapter-specific effect from stripping is more likely to show up, "
    "because bphs1_ch34's segments are visibly the most fragmented of the "
    "three chapters after Devanagari removal."
)

DEVANAGARI_RE = re.compile(r"[ऀ-ॿ]")


def strip_devanagari(text):
    stripped = DEVANAGARI_RE.sub("", text)
    stripped = re.sub(r"[ \t]+", " ", stripped)
    stripped = re.sub(r" *\n *", "\n", stripped)
    stripped = re.sub(r"\n{3,}", "\n\n", stripped)
    return stripped.strip()


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


def load_segment_index():
    with open(SEGMENT_INDEX_PATH, encoding="utf-8") as f:
        return json.load(f)


def ordered_segments(index_data):
    segs = [s for s in index_data["segments"] if s["unit_id"] in TARGET_UNIT_IDS]
    segs.sort(key=lambda s: (TARGET_UNIT_IDS.index(s["unit_id"]), s["ordinal"]))
    return segs


def build_payload(segs, strip):
    blocks = []
    for s in segs:
        text = strip_devanagari(s["text"]) if strip else s["text"]
        blocks.append("[%s]\n%s" % (s["segment_id"], text))
    return "\n\n".join(blocks)


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


def cmd_build(args):
    full_fact_block = FACT_BLOCK_PATH.read_text(encoding="utf-8")
    redacted_fact_block = build_redacted_fact_block(full_fact_block)

    index_data = load_segment_index()
    segs = ordered_segments(index_data)

    payload_with = build_payload(segs, strip=False)
    payload_strip = build_payload(segs, strip=True)

    prompt_with = build_subagent_prompt(redacted_fact_block, payload_with)
    prompt_strip = build_subagent_prompt(redacted_fact_block, payload_strip)

    Path(args.prompt_with_out).write_text(prompt_with, encoding="utf-8")
    Path(args.prompt_strip_out).write_text(prompt_strip, encoding="utf-8")

    meta = {
        "question": QUESTION,
        "valid_segment_ids": [s["segment_id"] for s in segs],
        "segment_text_by_id_original": {s["segment_id"]: s["text"] for s in segs},
        "raja_yoga_segment_id": RAJA_YOGA_SEGMENT_ID,
        "sun_sagittarius_specific_segment_id": SUN_SAGITTARIUS_SPECIFIC_SEGMENT_ID,
        "sun_general_naturals_segment_id": SUN_GENERAL_NATURALS_SEGMENT_ID,
        "prediction": PREDICTION,
    }
    Path(args.meta_out).write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Wrote prompt_with (%d chars) to %s" % (len(prompt_with), args.prompt_with_out))
    print("Wrote prompt_strip (%d chars) to %s" % (len(prompt_strip), args.prompt_strip_out))
    print("Wrote meta to %s" % args.meta_out)


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
def _strip_markdown_fence(text):
    stripped = text.strip()
    m = re.match(r"^```(?:json)?\s*\n(.*)\n```$", stripped, re.DOTALL)
    if m:
        return m.group(1)
    return stripped


def parse_response(raw_text):
    try:
        return json.loads(raw_text), None
    except json.JSONDecodeError as e1:
        try:
            return json.loads(_strip_markdown_fence(raw_text)), None
        except json.JSONDecodeError as e2:
            return None, "json.loads failed on raw (%s) and fence-stripped (%s)" % (e1, e2)


_CITATION_BRACKET_RE = re.compile(r"\[(bphs1_ch\d+#\d+)\]")


def classify_sun_stance(claims, reading):
    """Best-effort, mechanical (no LLM) scan for how a run characterizes
    the Sun (auspicious/benefic vs malefic) for this ascendant, and which
    segment_id it leans on for that characterization. Heuristic: scan each
    claim statement (and the reading) for a sentence-level co-occurrence
    of "Sun" with a malefic/auspicious/benefic term; the FIRST such match
    wins. Spot-checked by hand against all 6 raw responses in this run's
    report -- do not trust this in isolation for a larger N.
    """
    candidates = [(c.get("statement", ""), c.get("segment_ids", [])) for c in claims]
    candidates.append((reading, None))

    for text, seg_ids in candidates:
        if not re.search(r"\bSun\b", text):
            continue
        mal = re.search(r"\bmalefic\b", text, re.IGNORECASE)
        ausp = re.search(r"\b(auspicious|benefic)\b", text, re.IGNORECASE)
        if not mal and not ausp:
            continue
        sun_pos = re.search(r"\bSun\b", text).start()
        if mal and ausp:
            stance = "malefic" if abs(mal.start() - sun_pos) < abs(ausp.start() - sun_pos) else "auspicious"
        elif mal:
            stance = "malefic"
        else:
            stance = "auspicious"
        if seg_ids is None:
            # reading text -- look for a nearby bracket citation
            window = text[max(0, sun_pos - 250):sun_pos + 250]
            found = _CITATION_BRACKET_RE.findall(window)
            seg_ids = found if found else []
        return stance, seg_ids
    return None, []


def measure_run(raw_text, valid_ids):
    parsed, err = parse_response(raw_text)
    if err:
        return {"parse_error": err}
    claims = parsed.get("claims", [])
    reading = parsed.get("reading", "")
    all_cited = []
    for c in claims:
        all_cited.extend(c.get("segment_ids", []))
    distinct = sorted(set(all_cited))
    invalid = sorted({sid for sid in all_cited if sid not in valid_ids})
    cites_raja_yoga = RAJA_YOGA_SEGMENT_ID in distinct
    sun_stance, sun_evidence = classify_sun_stance(claims, reading)
    return {
        "parse_error": None,
        "claim_count": len(claims),
        "distinct_segments": distinct,
        "invalid_ids": invalid,
        "cites_raja_yoga": cites_raja_yoga,
        "sun_stance": sun_stance,
        "sun_evidence_segment_ids": sun_evidence,
        "reading_word_count": len(reading.split()),
        "parsed": parsed,
        "raw_text": raw_text,
    }


def cmd_analyze(args):
    meta = json.loads(Path(args.meta_in).read_text(encoding="utf-8"))
    valid_ids = set(meta["valid_segment_ids"])

    run_paths = {
        "WITH": [args.with1, args.with2, args.with3],
        "STRIP": [args.strip1, args.strip2, args.strip3],
    }
    runs = {"WITH": [], "STRIP": []}
    for arm, paths in run_paths.items():
        for p in paths:
            raw = Path(p).read_text(encoding="utf-8")
            m = measure_run(raw, valid_ids)
            m["path"] = p
            runs[arm].append(m)

    report = []
    report.append("# spike_variance_ab.py -- latest run")
    report.append("")
    report.append(
        "3 runs per arm, 6 total, interleaved order (WITH, STRIP, WITH, "
        "STRIP, WITH, STRIP), each a fresh Claude Code subagent with no "
        "prior context and no knowledge of the other runs or of this "
        "diagnostic's purpose. Arms differ ONLY in whether the segment "
        "payload has Devanagari-block characters stripped -- same chart, "
        "fact block, question, units, JSON contract, instructions across "
        "all 6. No prompt tuning between runs."
    )
    report.append("")
    report.append("## Prediction (stated before running)")
    report.append("")
    report.append(meta["prediction"])
    report.append("")

    report.append("## 1. Per-run table")
    report.append("")
    report.append("| arm | run | claims | distinct segments | invalid ids | cites Raja Yoga (ch34#5) | Sun stance | Sun evidence | reading words |")
    report.append("|---|---|---|---|---|---|---|---|---|")
    for arm in ("WITH", "STRIP"):
        for i, m in enumerate(runs[arm], start=1):
            if m["parse_error"]:
                report.append("| %s | %d | PARSE ERROR: %s | | | | | | |" % (arm, i, m["parse_error"]))
                continue
            report.append(
                "| %s | %d | %d | %d | %d | %s | %s | %s | %d |"
                % (
                    arm, i, m["claim_count"], len(m["distinct_segments"]), len(m["invalid_ids"]),
                    "YES" if m["cites_raja_yoga"] else "no",
                    m["sun_stance"] or "(not stated)",
                    ", ".join(m["sun_evidence_segment_ids"]) if m["sun_evidence_segment_ids"] else "-",
                    m["reading_word_count"],
                )
            )
    report.append("")

    def claim_counts(arm):
        return [m["claim_count"] for m in runs[arm] if not m["parse_error"]]

    with_counts = claim_counts("WITH")
    strip_counts = claim_counts("STRIP")

    report.append("## 2. Analysis 1 -- claim count range overlap")
    report.append("")
    report.append("| arm | min | median | max |")
    report.append("|---|---|---|---|")
    if with_counts:
        report.append("| WITH | %d | %.1f | %d |" % (min(with_counts), statistics.median(with_counts), max(with_counts)))
    if strip_counts:
        report.append("| STRIP | %d | %.1f | %d |" % (min(strip_counts), statistics.median(strip_counts), max(strip_counts)))
    report.append("")
    if with_counts and strip_counts:
        overlap = max(min(with_counts), min(strip_counts)) <= min(max(with_counts), max(strip_counts))
        if overlap:
            verdict1 = "OVERLAP: the WITH and STRIP claim-count ranges overlap -- variance explains the range, the strip is NOT implicated by claim count alone."
        else:
            verdict1 = "NO OVERLAP: the WITH and STRIP claim-count ranges are cleanly separated -- the strip IS implicated by claim count."
    else:
        verdict1 = "Cannot assess -- a parse error in one or both arms leaves too few data points."
    report.append("**Verdict: %s**" % verdict1)
    report.append("")

    report.append("## 3. Analysis 2 -- within-arm spread vs between-arm gap")
    report.append("")
    if with_counts and strip_counts:
        with_spread = max(with_counts) - min(with_counts)
        strip_spread = max(strip_counts) - min(strip_counts)
        between_gap = abs(statistics.median(with_counts) - statistics.median(strip_counts))
        report.append("| measure | value |")
        report.append("|---|---|")
        report.append("| WITH within-arm spread (max-min) | %d |" % with_spread)
        report.append("| STRIP within-arm spread (max-min) | %d |" % strip_spread)
        report.append("| between-arm gap (median difference) | %.1f |" % between_gap)
        report.append("")
        max_spread = max(with_spread, strip_spread)
        if max_spread >= between_gap:
            verdict2 = "Within-arm spread (%d) is AS LARGE AS OR LARGER THAN the between-arm gap (%.1f) -- the v2-vs-v3 single-run result is consistent with ordinary noise; it cannot be distinguished from variance at this sample size." % (max_spread, between_gap)
        else:
            verdict2 = "Within-arm spread (%d) is SMALLER than the between-arm gap (%.1f) -- the gap is larger than what run-to-run variance alone produced in this sample." % (max_spread, between_gap)
    else:
        verdict2 = "Cannot assess -- insufficient data due to a parse error."
    report.append("**Verdict: %s**" % verdict2)
    report.append("")

    report.append("## 4. Analysis 3 -- segment citation stability per arm")
    report.append("")
    for arm in ("WITH", "STRIP"):
        valid_runs = [m for m in runs[arm] if not m["parse_error"]]
        counts = {}
        for m in valid_runs:
            for sid in m["distinct_segments"]:
                counts[sid] = counts.get(sid, 0) + 1
        n = len(valid_runs)
        stable = sorted(sid for sid, c in counts.items() if c == n)
        unstable = sorted(sid for sid, c in counts.items() if c == 1)
        report.append("### %s arm (n=%d valid runs)" % (arm, n))
        report.append("")
        report.append("Cited by ALL %d runs (stable): %s" % (n, ", ".join(stable) if stable else "(none)"))
        report.append("")
        report.append("Cited by exactly 1 run (unstable): %s" % (", ".join(unstable) if unstable else "(none)"))
        report.append("")

    report.append("## 5. Analysis 4 -- Sun malefic/auspicious correctness signal")
    report.append("")
    report.append(
        "v2's original single run treated the Sun as AUSPICIOUS for this "
        "Sagittarius ascendant (the specific rule, `%s`, over the general "
        "naturals classification, `%s` -- per the instructions' own "
        "specific-over-general preference)."
        % (SUN_SAGITTARIUS_SPECIFIC_SEGMENT_ID, SUN_GENERAL_NATURALS_SEGMENT_ID)
    )
    report.append("")
    report.append("| arm | auspicious | malefic | not stated |")
    report.append("|---|---|---|---|")
    for arm in ("WITH", "STRIP"):
        valid_runs = [m for m in runs[arm] if not m["parse_error"]]
        n_ausp = sum(1 for m in valid_runs if m["sun_stance"] == "auspicious")
        n_mal = sum(1 for m in valid_runs if m["sun_stance"] == "malefic")
        n_none = sum(1 for m in valid_runs if m["sun_stance"] is None)
        report.append("| %s | %d | %d | %d |" % (arm, n_ausp, n_mal, n_none))
    report.append("")
    report.append(
        "This is a CORRECTNESS signal, not a volume signal: getting the "
        "Sun's classification right requires applying the specific-over-"
        "general instruction correctly regardless of how many claims a "
        "run makes."
    )
    report.append("")

    report.append("## 6. Conclusion")
    report.append("")
    if args.verdict_in:
        report.append(Path(args.verdict_in).read_text(encoding="utf-8").strip())
    else:
        report.append("(--verdict-in not supplied -- plain-language SAFE/HARMFUL/UNDETERMINED conclusion not recorded)")
    report.append("")

    report.append("## 7. Full raw JSON: best and worst run per arm")
    report.append("")

    def score(m):
        if m["parse_error"]:
            return -999
        return m["claim_count"] + 5 * int(m["cites_raja_yoga"]) + 5 * int(m["sun_stance"] == "auspicious")

    report.append(
        "Selection rule (mechanical, stated so it can be checked): "
        "score = claim_count + 5*(cites Raja Yoga) + 5*(Sun classified "
        "auspicious). Best = max score, worst = min score, per arm."
    )
    report.append("")
    for arm in ("WITH", "STRIP"):
        scored = [(score(m), i, m) for i, m in enumerate(runs[arm], start=1)]
        scored.sort(key=lambda t: t[0])
        worst_score, worst_i, worst_m = scored[0]
        best_score, best_i, best_m = scored[-1]
        report.append("### %s arm -- BEST (run %d, score %d)" % (arm, best_i, best_score))
        report.append("")
        report.append("```json")
        report.append(json.dumps(best_m.get("parsed", {"parse_error": best_m.get("parse_error")}), ensure_ascii=False, indent=2))
        report.append("```")
        report.append("")
        report.append("### %s arm -- WORST (run %d, score %d)" % (arm, worst_i, worst_score))
        report.append("")
        report.append("```json")
        report.append(json.dumps(worst_m.get("parsed", {"parse_error": worst_m.get("parse_error")}), ensure_ascii=False, indent=2))
        report.append("```")
        report.append("")

    write_report(report)
    print("Wrote report to %s" % DIAG_PATH)


def write_report(lines):
    DIAG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DIAG_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build")
    p_build.add_argument("--prompt-with-out", required=True)
    p_build.add_argument("--prompt-strip-out", required=True)
    p_build.add_argument("--meta-out", required=True)
    p_build.set_defaults(func=cmd_build)

    p_analyze = sub.add_parser("analyze")
    p_analyze.add_argument("--meta-in", required=True)
    p_analyze.add_argument("--with1", required=True)
    p_analyze.add_argument("--with2", required=True)
    p_analyze.add_argument("--with3", required=True)
    p_analyze.add_argument("--strip1", required=True)
    p_analyze.add_argument("--strip2", required=True)
    p_analyze.add_argument("--strip3", required=True)
    p_analyze.add_argument("--verdict-in", required=False, default=None)
    p_analyze.set_defaults(func=cmd_analyze)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
