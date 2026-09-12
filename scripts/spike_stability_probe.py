"""
THROWAWAY SPIKE -- isolate causes of citation/claim instability across
interpreter runs on the SAME chart, question, and payload.

Builds deterministic payload text (and, for Arm D, deterministic priority
tags) from the EXISTING data/career_payload_bphs.json artifact -- does not
rebuild it, does not call any LLM. The actual A/B/C/D subagent runs are done
separately (Claude Code subagents); this script's `measure` mode does the
mechanical citation-validity check on their JSON output.

Usage:
  python scripts/spike_stability_probe.py build --out-dir <dir>
  python scripts/spike_stability_probe.py measure --arm plain|priority --json <path> --out-dir <dir>
"""
import argparse
import json
import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAYLOAD_PATH = os.path.join(REPO_ROOT, "data", "career_payload_bphs.json")
FACT_BLOCK_PATH = os.path.join(REPO_ROOT, "diagnostics", "_spike2_fact_block.txt")

QUESTION_FREEFORM = "What does my chart say about my career?"

SKELETON_POINTS = [
    "condition of the 10th house",
    "condition and placement of the 10th lord",
    "planets occupying or aspecting the 10th",
    "any career-relevant yoga present",
    "the current mahadasha/antardasha lord's bearing on career",
]

# Houses this deterministic tagger treats as structurally career-relevant:
# 10 (career itself), 6 (service/work), 2 (wealth/family support), 11 (gains).
# Chosen from the task spec verbatim, not re-derived here.
PRIMARY_HOUSES = {10, 6, 2, 11}


def load_payload():
    with open(PAYLOAD_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_fact_block():
    with open(FACT_BLOCK_PATH, "r", encoding="utf-8") as f:
        return f.read()


def priority_tag(seg):
    reason = seg["keep_reason"]
    if reason == "relation_match":
        houses = set()
        for h, t in seg["relations"]:
            houses.add(h)
            houses.add(t)
        return "PRIMARY" if houses & PRIMARY_HOUSES else "SECONDARY"
    # no_relation_failsafe, coverage_rescue, (dropped shouldn't appear -- kept-only)
    return "CONTEXT"


def kept_segments(payload):
    """Preserves the JSON array's own order, which is ordinal order by
    construction in build_career_payload.py (segments are appended in a
    single ordinal-ascending loop, regardless of keep_reason)."""
    return [s for s in payload["segments"] if s["kept"]]


def check_ordinal_sorted(segs):
    ordinals = [s["ordinal"] for s in segs]
    return ordinals == sorted(ordinals), ordinals


def units_by_id(payload):
    return {u["unit_id"]: u for u in payload["units"]}


def build_plain_payload(payload):
    units = units_by_id(payload)
    parts = [f"[ch21]\n{units['ch21']['text']}"]
    for s in kept_segments(payload):
        parts.append(f"[{s['segment_id']}]\n{s['text']}")
    parts.append(f"[ch34]\n{units['ch34']['text']}")
    return "\n\n".join(parts)


def build_priority_payload(payload):
    units = units_by_id(payload)
    # ch21 is wholly about the 10th house's effects; ch34 is wholly the
    # ascendant (Sagittarius) classification chapter -- both PRIMARY by the
    # task's own criteria (house-10 content / ascendant-scoped content).
    parts = [f"[PRIMARY] [ch21]\n{units['ch21']['text']}"]
    tag_counts = {"PRIMARY": 1, "SECONDARY": 0, "CONTEXT": 0}  # ch21 counted
    for s in kept_segments(payload):
        tag = priority_tag(s)
        tag_counts[tag] += 1
        parts.append(f"[{tag}] [{s['segment_id']}]\n{s['text']}")
    parts.append(f"[PRIMARY] [ch34]\n{units['ch34']['text']}")
    tag_counts["PRIMARY"] += 1  # ch34
    return "\n\n".join(parts), tag_counts


def cmd_build(args):
    os.makedirs(args.out_dir, exist_ok=True)
    payload = load_payload()
    segs = kept_segments(payload)

    is_sorted, ordinals = check_ordinal_sorted(segs)

    plain_text = build_plain_payload(payload)
    priority_text, tag_counts = build_priority_payload(payload)
    fact_block = load_fact_block()

    with open(os.path.join(args.out_dir, "source_plain.txt"), "w", encoding="utf-8") as f:
        f.write(plain_text)
    with open(os.path.join(args.out_dir, "source_priority.txt"), "w", encoding="utf-8") as f:
        f.write(priority_text)
    with open(os.path.join(args.out_dir, "fact_block.txt"), "w", encoding="utf-8") as f:
        f.write(fact_block)

    valid_ids = {"ch21", "ch34"} | {s["segment_id"] for s in segs}
    manifest = {
        "n_kept_segments": len(segs),
        "ordinal_sorted_by_construction": is_sorted,
        "first_10_ordinals": ordinals[:10],
        "priority_tag_counts": tag_counts,
        "valid_ids": sorted(valid_ids, key=lambda x: (x != "ch21", x != "ch34", x)),
        "plain_payload_tokens": len(plain_text.split()),
        "priority_payload_tokens": len(priority_text.split()),
    }
    with open(os.path.join(args.out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"kept segments: {len(segs)}")
    print(f"already ordinal-sorted: {is_sorted}")
    print(f"priority tag counts: {tag_counts}")
    print(f"plain payload tokens: {manifest['plain_payload_tokens']}")
    print(f"priority payload tokens: {manifest['priority_payload_tokens']}")
    print(f"wrote source_plain.txt, source_priority.txt, fact_block.txt, manifest.json to {args.out_dir}")


def _extract_ids_freeform(result):
    ids = set()
    for c in result.get("claims", []):
        ids.update(c.get("segment_ids", []))
    return ids


def _extract_ids_skeleton(result):
    ids = set()
    for p in result.get("skeleton", []):
        ids.update(p.get("segment_ids", []))
    return ids


def cmd_measure(args):
    with open(os.path.join(args.out_dir, "manifest.json"), "r", encoding="utf-8") as f:
        manifest = json.load(f)
    valid_ids = set(manifest["valid_ids"])

    with open(args.json, "r", encoding="utf-8") as f:
        raw = f.read()
    # tolerate accidental markdown fencing
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
    result = json.loads(raw)

    if "skeleton" in result:
        cited = _extract_ids_skeleton(result)
        claim_count = sum(
            1 for p in result["skeleton"] if p.get("covered") and p.get("segment_ids")
        )
        skeleton_covered = [bool(p.get("covered")) for p in result["skeleton"]]
    else:
        cited = _extract_ids_freeform(result)
        claim_count = len(result.get("claims", []))
        skeleton_covered = None  # scored manually by the orchestrator, not here

    invalid = sorted(cited - valid_ids)
    reading = result.get("reading", "")
    word_count = len(reading.split())

    report = {
        "arm_payload": args.arm,
        "claim_count": claim_count,
        "cited_segment_ids": sorted(cited),
        "invalid_ids": invalid,
        "skeleton_covered_flags": skeleton_covered,
        "reading_word_count": word_count,
    }
    out_path = os.path.join(args.out_dir, f"measure_{os.path.basename(args.json)}")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build")
    b.add_argument("--out-dir", required=True)

    m = sub.add_parser("measure")
    m.add_argument("--arm", choices=["plain", "priority"], required=True)
    m.add_argument("--json", required=True)
    m.add_argument("--out-dir", required=True)

    args = ap.parse_args()
    if args.cmd == "build":
        cmd_build(args)
    elif args.cmd == "measure":
        cmd_measure(args)


if __name__ == "__main__":
    main()
