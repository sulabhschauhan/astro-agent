"""
PERMANENT verifier. Checks whether a claim's asserted "Nth lord is in the
Mth house" relation matches the direction stored in the cited segment's
`relations` field (data/career_payload_bphs.json), and whether the
relation matches the fact block's `lord_house_map`.

No LLM calls, no subagents, no network. Runs against three already-
captured OpenAI run JSONs (diagnostics/_spike_openai_run{1,2,3}.json).
Detects and reports only -- does not modify, drop, or silence anything.

Usage:
  PYTHONIOENCODING=utf-8 python scripts/verify_claim_direction.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_PATH = ROOT / "data" / "career_payload_bphs.json"
RUN_PATHS = [ROOT / "diagnostics" / f"_spike_openai_run{i}.json" for i in range(1, 4)]

WORD_ORDINALS = {
    "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
    "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10,
    "eleventh": 11, "twelfth": 12,
}

# an ordinal token: digit+suffix ("10th") or a spelled-out word ("tenth")
_ORDINAL_TOKEN = r"(?:\d+(?:st|nd|rd|th)|" + "|".join(WORD_ORDINALS) + r")"
_ORDINAL_RE = re.compile(_ORDINAL_TOKEN, re.IGNORECASE)

# "<ordinal> lord ... in ... <ordinal> house", tolerant of "is"/"the"/etc.
# in between, and of a comma/clause break before "house".
RELATION_RE = re.compile(
    r"(" + _ORDINAL_TOKEN + r")\s+lord\b.{0,40}?\bin\b.{0,25}?(" + _ORDINAL_TOKEN + r")\s+house",
    re.IGNORECASE,
)


def ordinal_to_int(token):
    token = token.lower()
    m = re.match(r"(\d+)", token)
    if m:
        return int(m.group(1))
    return WORD_ORDINALS[token]


def parse_relations(statement):
    """Return list of (lord_house, placed_house) int tuples asserted in the statement."""
    out = []
    for m in RELATION_RE.finditer(statement):
        n = ordinal_to_int(m.group(1))
        h = ordinal_to_int(m.group(2))
        out.append((n, h))
    return out


def load_payload():
    with open(PAYLOAD_PATH, encoding="utf-8") as f:
        return json.load(f)


def build_lookup(data):
    """Map every citable id (segment or whole-chapter unit) to
    (relations_or_None, text). relations=None means 'not a segment with
    an extracted relations field' (i.e. a whole-chapter unit) --
    structurally different from relations=[] (a segment the extractor
    ran on but found nothing in)."""
    lookup = {}
    for s in data["segments"]:
        lookup[s["segment_id"]] = {"relations": s.get("relations", []), "text": s["text"], "kind": "segment"}
    for u in data["units"]:
        lookup[u["unit_id"]] = {"relations": None, "text": u["text"], "kind": "unit"}
    return lookup


def classify(asserted, cited_ids, lookup, lord_house_map):
    """asserted = (N, M) meaning 'Nth-house lord is in Mth house'.
    Returns list of per-citation verdict dicts (one per cited id)."""
    n, m = asserted
    claim_chart_ok = lord_house_map.get(str(n)) == m

    results = []
    for cid in cited_ids:
        entry = lookup.get(cid)
        if entry is None:
            results.append({
                "cited_id": cid, "verdict": "UNKNOWN_ID",
                "chart_mismatch": not claim_chart_ok,
                "segment_relations": None, "text_excerpt": None,
            })
            continue

        rels = entry["relations"]
        text_excerpt = entry["text"].strip()[:150]

        if rels is None:
            # whole-chapter unit -- no extracted relations to compare against
            results.append({
                "cited_id": cid, "verdict": "RELATION_ABSENT_EMPTY",
                "chart_mismatch": not claim_chart_ok,
                "segment_relations": None, "text_excerpt": text_excerpt,
                "note": "citation is a whole-chapter unit, not a segment -- no relations field exists",
            })
            continue

        rels_tuples = [tuple(r) for r in rels]
        chart_mismatch = not claim_chart_ok

        if (n, m) in rels_tuples:
            verdict = "DIRECTION_OK"
        elif (m, n) in rels_tuples:
            verdict = "DIRECTION_REVERSED"
            # the segment's OWN carried relation (m, n) -- does IT hold for this chart?
            if lord_house_map.get(str(m)) != n:
                chart_mismatch = True
        else:
            verdict = "RELATION_ABSENT_EMPTY" if len(rels_tuples) == 0 else "RELATION_ABSENT_OTHER"

        results.append({
            "cited_id": cid, "verdict": verdict,
            "chart_mismatch": chart_mismatch,
            "segment_relations": rels_tuples, "text_excerpt": text_excerpt,
        })
    return results


def main():
    data = load_payload()
    lookup = build_lookup(data)
    lord_house_map = data["header"]["lord_house_map"]

    runs = []
    for p in RUN_PATHS:
        with open(p, encoding="utf-8") as f:
            runs.append(json.load(f))

    all_records = []  # flat list across all runs, for reporting
    per_run_summary = []

    for run_idx, run in enumerate(runs, start=1):
        claims = run["parsed"]["claims"]
        run_counts = {
            "DIRECTION_OK": 0, "DIRECTION_REVERSED": 0,
            "RELATION_ABSENT_EMPTY": 0, "RELATION_ABSENT_OTHER": 0,
            "NO_RELATION_CLAIMED": 0, "UNKNOWN_ID": 0,
        }
        claim_would_drop = 0

        for claim_idx, claim in enumerate(claims, start=1):
            statement = claim["statement"]
            cited_ids = claim.get("segment_ids", [])
            asserted = parse_relations(statement)

            if not asserted:
                run_counts["NO_RELATION_CLAIMED"] += 1
                all_records.append({
                    "run": run_idx, "claim_idx": claim_idx, "statement": statement,
                    "asserted": None, "cited_ids": cited_ids,
                    "verdict": "NO_RELATION_CLAIMED", "chart_mismatch": False,
                })
                continue

            claim_flagged = False
            for rel in asserted:
                results = classify(rel, cited_ids, lookup, lord_house_map)
                for r in results:
                    run_counts[r["verdict"]] = run_counts.get(r["verdict"], 0) + 1
                    if r["verdict"] in ("DIRECTION_REVERSED",) or r["chart_mismatch"]:
                        claim_flagged = True
                    all_records.append({
                        "run": run_idx, "claim_idx": claim_idx, "statement": statement,
                        "asserted": rel, "cited_ids": cited_ids,
                        "verdict": r["verdict"], "chart_mismatch": r["chart_mismatch"],
                        "cited_id": r["cited_id"], "segment_relations": r.get("segment_relations"),
                        "text_excerpt": r.get("text_excerpt"),
                    })

            if claim_flagged:
                claim_would_drop += 1

        per_run_summary.append({
            "run": run_idx, "claim_count": len(claims),
            "counts": run_counts, "claims_would_drop": claim_would_drop,
        })

    # ---- console report ----
    print("=== PER-RUN CLAIM/VERDICT COUNTS ===")
    for s in per_run_summary:
        print(f"run {s['run']}: {s['claim_count']} claims -> {s['counts']}")

    print()
    print("=== DIRECTION_REVERSED and CHART_MISMATCH records, in full ===")
    flagged = [r for r in all_records if r["verdict"] == "DIRECTION_REVERSED" or r.get("chart_mismatch")]
    if not flagged:
        print("none")
    for r in flagged:
        print(f"- run {r['run']} claim {r['claim_idx']}: verdict={r['verdict']} chart_mismatch={r['chart_mismatch']}")
        print(f"  statement: {r['statement']}")
        print(f"  cited_id: {r.get('cited_id')}  asserted={r['asserted']}  segment_relations={r.get('segment_relations')}")
        print(f"  text_excerpt: {r.get('text_excerpt')!r}")

    print()
    print("=== RELATION_ABSENT_OTHER records ===")
    other = [r for r in all_records if r["verdict"] == "RELATION_ABSENT_OTHER"]
    if not other:
        print("none")
    for r in other:
        print(f"- run {r['run']} claim {r['claim_idx']}: {r['statement']}")
        print(f"  cited_id: {r.get('cited_id')} asserted={r['asserted']} segment_relations={r.get('segment_relations')}")

    print()
    print("=== VALIDATION AGAINST THE THREE KNOWN CASES ===")
    checks = [
        ("Run 2 / ch24_s033 -> DIRECTION_REVERSED + CHART_MISMATCH", 2, "ch24_s033", "DIRECTION_REVERSED", True),
        ("Run 3 / ch24_s038 -> DIRECTION_REVERSED", 3, "ch24_s038", "DIRECTION_REVERSED", None),
        ("Run 1 / ch24_s103 -> DIRECTION_OK", 1, "ch24_s103", "DIRECTION_OK", False),
    ]
    for label, run_no, seg_id, expected_verdict, expected_mismatch in checks:
        matches = [r for r in all_records if r["run"] == run_no and r.get("cited_id") == seg_id]
        if not matches:
            print(f"{label}: NO RECORD FOUND")
            continue
        for r in matches:
            ok_verdict = r["verdict"] == expected_verdict
            ok_mismatch = (expected_mismatch is None) or (r["chart_mismatch"] == expected_mismatch)
            status = "PASS" if (ok_verdict and ok_mismatch) else "FAIL"
            print(f"{label}: {status} (actual verdict={r['verdict']}, chart_mismatch={r['chart_mismatch']})")

    print()
    print("=== DROP-RATE IF DIRECTION_REVERSED + CHART_MISMATCH WERE BLOCKING ===")
    total_claims = sum(s["claim_count"] for s in per_run_summary)
    total_drop = sum(s["claims_would_drop"] for s in per_run_summary)
    for s in per_run_summary:
        pct = 100.0 * s["claims_would_drop"] / s["claim_count"] if s["claim_count"] else 0.0
        print(f"run {s['run']}: {s['claims_would_drop']}/{s['claim_count']} claims ({pct:.1f}%)")
    pct_total = 100.0 * total_drop / total_claims if total_claims else 0.0
    print(f"overall: {total_drop}/{total_claims} claims ({pct_total:.1f}%)")


if __name__ == "__main__":
    main()
