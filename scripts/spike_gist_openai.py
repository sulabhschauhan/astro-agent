"""
THROWAWAY SPIKE — gist stability, OpenAI arm. Not product code, not
committed. Replaces the subagent approach (167k tokens/run overhead,
tool access could not be disabled, run 1 contaminated).

Claude Code's role here is MECHANICAL ONLY: build the payload string,
make three OpenAI API calls, dump raw results to disk for the report.
This script does not interpret the chart and does not author claims.

Usage:
  PYTHONIOENCODING=utf-8 python scripts/spike_gist_openai.py
"""
import json
import sys
import time
from pathlib import Path

import tiktoken
from openai import OpenAI, RateLimitError

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_PATH = ROOT / "data" / "career_payload_bphs.json"
OUT_DIR = ROOT / "diagnostics"
RAW_OUT_PATHS = [OUT_DIR / f"_spike_openai_run{i}.json" for i in range(1, 4)]

MODEL = "gpt-4o"
TEMPERATURE = 0
SEED = 42
QUESTION = "What does my chart say about my career?"

SYSTEM_PROMPT = """You are answering a question about a person's Vedic astrology chart using only the reference material supplied in the user message.

Rules, strictly enforced:
- Use ONLY the fact block and the supplied segments provided in the user message. Do not use any outside astrological knowledge, and do not invent chart facts.
- Never state a chart fact that is not present in the fact block.
- Where a specific rule (e.g. a Chapter 24 verse for an exact house-lord placement) and a general principle (e.g. a Chapter 21 or Chapter 34 general rule) both apply, prefer the specific rule.
- Cite sources by segment id only (e.g. "ch24_s014", or "ch21"/"ch34" for the whole-chapter units). Never quote or reproduce the source text verbatim in your claims or reading.
- Stay silent on anything the supplied text does not let you address for this chart; list such topics in "silent_on" rather than guessing.

Output STRICT JSON only, no markdown code fences, no text before or after the JSON object, in exactly this shape:
{"claims": [{"statement": "...", "segment_ids": ["..."]}], "silent_on": ["..."], "reading": "..."}

"claims": each substantive claim you draw from the material, with the segment_id(s) that support it.
"silent_on": topics about career the material does not let you address for this specific chart.
"reading": your full prose answer to the question. No required length or structure."""


def load_payload():
    with open(PAYLOAD_PATH, encoding="utf-8") as f:
        return json.load(f)


def confirm_document_order(data):
    notes = []
    units = data["units"]
    unit_ids = [u["unit_id"] for u in units]
    units_ok = unit_ids == ["ch21", "ch34"]
    notes.append(f"units order in file: {unit_ids} (expected ['ch21','ch34']) -> {units_ok}")

    kept = [s for s in data["segments"] if s.get("kept")]
    ordinals = [s["ordinal"] for s in kept]
    segs_ok = ordinals == sorted(ordinals)
    notes.append(
        f"kept ch24 segments ({len(kept)} of {len(data['segments'])}) "
        f"already ascending by ordinal in file -> {segs_ok}"
    )
    notes.append(
        "raw file is NOT one flat document-order list -- ch21/ch34 live in "
        "'units', ch24 lives separately in 'segments'. Document order "
        "(ch21 -> ch24 -> ch34) is assembled below by concatenation."
    )
    return (units_ok and segs_ok), notes


def build_payload_block(data):
    header = data["header"]
    units_by_id = {u["unit_id"]: u for u in data["units"]}
    kept = sorted(
        (s for s in data["segments"] if s.get("kept")),
        key=lambda s: s["ordinal"],
    )

    parts = []
    parts.append("=== FACT BLOCK (from payload header, verbatim) ===")
    parts.append(json.dumps(header, indent=2, ensure_ascii=False))
    parts.append("")
    parts.append("=== CHAPTER 21 (whole chapter, verbatim) ===")
    parts.append(units_by_id["ch21"]["text"])
    parts.append("")
    parts.append(
        f"=== CHAPTER 24 (selected verses, {len(kept)} of "
        f"{len(data['segments'])} total, ascending ordinal) ==="
    )
    for s in kept:
        parts.append(f"[{s['segment_id']}]")
        parts.append(s["text"])
        parts.append("")
    parts.append("=== CHAPTER 34 (whole chapter, verbatim) ===")
    parts.append(units_by_id["ch34"]["text"])

    return "\n".join(parts), [s["segment_id"] for s in kept] + ["ch21", "ch34"]


def call_openai(client, user_message, run_idx):
    backoff = 2
    for attempt in range(1, 4):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                temperature=TEMPERATURE,
                seed=SEED,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
            )
            return resp
        except RateLimitError as e:
            if attempt == 3:
                raise
            print(f"run {run_idx}: rate limited (attempt {attempt}), backing off {backoff}s")
            time.sleep(backoff)
            backoff *= 2
    raise RuntimeError("unreachable")


def main():
    data = load_payload()
    ok, order_notes = confirm_document_order(data)
    block, valid_segment_ids = build_payload_block(data)
    valid_segment_ids_set = set(valid_segment_ids)

    enc = tiktoken.get_encoding("cl100k_base")
    payload_tokens = len(enc.encode(block))
    system_tokens = len(enc.encode(SYSTEM_PROMPT))
    question_tokens = len(enc.encode(QUESTION))

    print("DOCUMENT ORDER CONFIRMATION")
    for n in order_notes:
        print(" -", n)
    print()
    print(f"payload block tiktoken(cl100k_base) count: {payload_tokens}")
    print(f"system prompt tiktoken count: {system_tokens}")
    print(f"question tiktoken count: {question_tokens}")
    print(f"estimated total input tokens per call: {payload_tokens + system_tokens + question_tokens}")
    print()

    user_message = block + "\n\n=== QUESTION ===\n" + QUESTION

    client = OpenAI()
    results = []
    for i in range(1, 4):
        print(f"--- calling OpenAI, run {i}/3 ---")
        try:
            resp = call_openai(client, user_message, i)
        except Exception as e:
            print(f"run {i}: NON-RATE-LIMIT ERROR, STOPPING: {type(e).__name__}: {e}")
            sys.exit(1)

        raw_text = resp.choices[0].message.content
        fingerprint = resp.system_fingerprint
        usage = resp.usage

        try:
            parsed = json.loads(raw_text)
            parse_error = None
        except json.JSONDecodeError as e:
            parsed = None
            parse_error = str(e)

        invalid_ids = []
        if parsed is not None:
            cited = set()
            for c in parsed.get("claims", []):
                cited.update(c.get("segment_ids", []))
            invalid_ids = sorted(cited - valid_segment_ids_set)

        record = {
            "run": i,
            "model": MODEL,
            "temperature": TEMPERATURE,
            "seed": SEED,
            "system_fingerprint": fingerprint,
            "usage": {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
            },
            "raw_text": raw_text,
            "parsed": parsed,
            "parse_error": parse_error,
            "invalid_segment_ids": invalid_ids,
        }
        results.append(record)
        with open(RAW_OUT_PATHS[i - 1], "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=False)

        print(f"run {i}: fingerprint={fingerprint} "
              f"in={usage.prompt_tokens} out={usage.completion_tokens} "
              f"invalid_segment_ids={invalid_ids} parse_error={parse_error}")

    fingerprints = {r["system_fingerprint"] for r in results}
    print()
    print(f"distinct system_fingerprints across 3 runs: {fingerprints}")

    raw_texts = [r["raw_text"] for r in results]
    identical_all = len(set(raw_texts)) == 1
    print(f"all three raw outputs byte-identical: {identical_all}")

    print()
    print("Raw run files written:")
    for p in RAW_OUT_PATHS:
        print(" -", p)


if __name__ == "__main__":
    main()
