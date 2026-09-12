"""
THROWAWAY SPIKE — gist stability under the reframed metric (conclusion
agreement, not citation overlap). Not product code, not committed.

Modes:
  prepare  - load data/career_payload_bphs.json, confirm document order,
             build the single combined payload text block (fact block +
             ch21 unit + ch24 kept segments ascending ordinal + ch34
             unit) used verbatim and identically across all 4 subagent
             runs. Writes it to diagnostics/_spike_gist_payload_block.txt
             and prints a confirmation summary.
  analyze  - given 4 run JSON files (diagnostics/_spike_gist_run1.json
             .. run4.json, each the raw strict-JSON object returned by
             one subagent), compute the OBJECTIVE/mechanical measures
             only: claim count per run, cited segment_id set per run,
             pairwise Jaccard over those sets. Does NOT attempt the
             conclusion-agreement classification -- that is done by
             direct reading/reasoning per the task, not by this script.

Usage:
  PYTHONIOENCODING=utf-8 python scripts/spike_gist_stability.py prepare
  PYTHONIOENCODING=utf-8 python scripts/spike_gist_stability.py analyze
"""
import json
import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_PATH = ROOT / "data" / "career_payload_bphs.json"
BLOCK_OUT_PATH = ROOT / "diagnostics" / "_spike_gist_payload_block.txt"
RUN_PATHS = [ROOT / "diagnostics" / f"_spike_gist_run{i}.json" for i in range(1, 5)]


def load_payload():
    with open(PAYLOAD_PATH, encoding="utf-8") as f:
        return json.load(f)


def confirm_document_order(data):
    """Returns (is_doc_order: bool, notes: list[str])."""
    notes = []
    units = data["units"]
    unit_ids = [u["unit_id"] for u in units]
    notes.append(f"units order in file: {unit_ids}")
    expected_units = ["ch21", "ch34"]
    units_ok = unit_ids == expected_units
    notes.append(f"units already in doc order (ch21, ch34): {units_ok}")

    kept = [s for s in data["segments"] if s.get("kept")]
    ordinals = [s["ordinal"] for s in kept]
    segs_ok = ordinals == sorted(ordinals)
    notes.append(
        f"kept ch24 segments ({len(kept)} of {len(data['segments'])}) "
        f"already ascending by ordinal in file: {segs_ok}"
    )
    notes.append(
        "raw file layout is NOT one flat document-order list -- ch21/ch34 "
        "live in 'units' (whole-chapter text blocks) and ch24 lives "
        "separately in 'segments' (ordinal-addressed, kept-filtered). "
        "Document order (ch21 -> ch24 -> ch34) must be assembled by "
        "concatenation; this script does that assembly below."
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
        f"{len([s for s in data['segments']])} total, ascending ordinal) ==="
    )
    for s in kept:
        parts.append(f"[{s['segment_id']}]")
        parts.append(s["text"])
        parts.append("")
    parts.append("=== CHAPTER 34 (whole chapter, verbatim) ===")
    parts.append(units_by_id["ch34"]["text"])

    return "\n".join(parts)


def mode_prepare():
    data = load_payload()
    ok, notes = confirm_document_order(data)
    block = build_payload_block(data)
    BLOCK_OUT_PATH.write_text(block, encoding="utf-8")

    print("DOCUMENT ORDER CONFIRMATION")
    for n in notes:
        print(" -", n)
    print()
    print(f"CONCLUSION: payload was NOT already a flat document-order list; "
          f"assembled block written to {BLOCK_OUT_PATH}")
    print(f"block length: {len(block)} chars")
    approx_tokens = len(block) // 4
    print(f"approx tokens (chars/4 heuristic): {approx_tokens}")


def mode_analyze():
    runs = []
    for i, p in enumerate(RUN_PATHS, start=1):
        if not p.exists():
            print(f"MISSING: {p} -- run {i} not captured, aborting analyze")
            sys.exit(1)
        with open(p, encoding="utf-8") as f:
            runs.append(json.load(f))

    claim_counts = []
    seg_sets = []
    for i, r in enumerate(runs, start=1):
        claims = r.get("claims", [])
        claim_counts.append(len(claims))
        ids = set()
        for c in claims:
            ids.update(c.get("segment_ids", []))
        seg_sets.append(ids)
        print(f"run {i}: {len(claims)} claims, "
              f"{len(ids)} distinct cited segment_ids -> {sorted(ids)}")

    print()
    print("PAIRWISE JACCARD (cited segment_id sets, reference only):")
    for (i, a), (j, b) in combinations(enumerate(seg_sets, start=1), 2):
        union = a | b
        inter = a & b
        jac = len(inter) / len(union) if union else 1.0
        print(f"  run{i} vs run{j}: |inter|={len(inter)} |union|={len(union)} "
              f"jaccard={jac:.3f}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "prepare"
    if mode == "prepare":
        mode_prepare()
    elif mode == "analyze":
        mode_analyze()
    else:
        print(f"unknown mode: {mode}")
        sys.exit(1)
