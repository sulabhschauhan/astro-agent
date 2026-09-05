"""
THROWAWAY PROBE. Not product code, not committed, not imported by anything.

DECISION THIS SERVES: does the fail-safe payload (ARM A, current shipped
path) produce a BETTER answer than a strict house-relation-filtered
payload (ARM B), or just a bigger one?
  if wide gives more grounded claims -> fail-safe justified
  if strict gives equal or more claims -> selection gets rebuilt

Builds ONE plan (live planner call, agent.astro.planner default temp=0)
and reuses it for both arms, so only the payload differs:

  ARM A (wide)   = select_units -> build_payload -> filter_segments_by_domain
                   (exactly agent.astro.planner.plan_and_build's own body).
  ARM B (strict) = ARM A's payload, then additionally drop any kept
                   segment whose stored `relations` (produced by
                   payload_builder.extract_relations at build_payload time)
                   contains NO pair touching a planned house. A segment
                   with NO extracted relation at all is ALSO dropped here
                   -- this is NOT the shipped no_relation_failsafe rule,
                   it is the opposite of it, by design of this arm.

Whole-chapter units (unsplit, no per-segment relations) are NOT touched by
ARM B's rule -- extract_relations never ran on them individually.

No new module. Force PYTHONIOENCODING=utf-8. Writes ONLY to
diagnostics/runs/<ts>_wide_vs_strict.md then copies to
diagnostics/latest_run.md. Prints a <=10 line summary only.
"""
from __future__ import annotations

import copy
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.astro import planner as P            # noqa: E402
from agent.astro import payload_builder as PB    # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS_DIR = os.path.join(ROOT, "diagnostics", "runs")
LATEST = os.path.join(ROOT, "diagnostics", "latest_run.md")

QUESTION = "When will I get married?"
EXPECTED_DOMAINS = {"marriage", "timing_dasha"}

# Sulabh's chart, same values run_planner_poc.py / spike_career_filtered.py pin.
CHART_FACTS = {
    "lord_house_map": {1: 1, 2: 2, 3: 3, 4: 4, 5: 2, 6: 6,
                       7: 12, 8: 12, 9: 9, 10: 4, 11: 5, 12: 6},
    "ascendant_sign": "Sagittarius",
}

REAL_TOKEN_THRESHOLD_FOR_4O = 30_000

# pricing, USD per 1M tokens (matches the ratio the DECISION brief already
# assumes: "cost drops 17x")
PRICES = {
    "gpt-4o-mini": {"in": 0.15, "out": 0.60},
    "gpt-4o": {"in": 2.50, "out": 10.00},
}

INTERPRETER_SYSTEM = """You are answering a question about a person's Vedic astrology chart using only the reference material supplied in the user message.

Rules, strictly enforced:
- Use ONLY the fact block and the supplied segments. Do not use outside astrological knowledge, and do not invent chart facts.
- Never state a chart fact that is not present in the fact block.
- Prefer a specific rule over a general principle where both apply.
- Cite sources by segment id or unit id only. Never quote the source text verbatim.
- Stay silent on anything the supplied text does not let you address for this chart; list such topics in "silent_on" rather than guessing.

Output STRICT JSON only, no fences, exactly:
{"claims": [{"statement": "...", "segment_ids": ["..."]}], "silent_on": ["..."], "reading": "..."}"""


def build_interpreter_prompt(question, plan, payload):
    header = payload.get("header", {})
    parts = [f"QUESTION: {question}", "",
             "CHART FACTS (the only chart facts that exist):",
             json.dumps(header, ensure_ascii=False, indent=2), "",
             f"PLANNED HOUSES (reasoned by the planner): {plan.houses}",
             f"WHOSE CHART: {plan.whose_chart}  TIME SCOPE: {plan.time_scope}",
             "", "REFERENCE MATERIAL", ""]
    for u in payload.get("units", []):
        parts.append(f"[{u['unit_id']}]\n{u['text']}\n")
    kept = sorted((s for s in payload.get("segments", []) if s.get("kept")),
                  key=lambda s: (s.get("unit_id", s.get("segment_id", "")), s.get("ordinal", 0)))
    for s in kept:
        parts.append(f"[{s['segment_id']}] {s.get('text', '')}\n")
    return "\n".join(parts)


def call_interpreter(prompt, model):
    from openai import OpenAI
    client = OpenAI()
    resp = client.chat.completions.create(
        model=model, temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": INTERPRETER_SYSTEM},
                  {"role": "user", "content": prompt}])
    content = resp.choices[0].message.content or ""
    usage = resp.usage
    return content, {
        "prompt_tokens": getattr(usage, "prompt_tokens", None),
        "completion_tokens": getattr(usage, "completion_tokens", None),
    }


def build_arm_b(payload_a, plan):
    """ARM A's payload, with the additional strict-relation drop applied to
    segments only. Never mutates payload_a."""
    payload_b = copy.deepcopy(payload_a)
    planned_houses = set(plan.houses)
    dropped = 0
    for seg in payload_b["segments"]:
        if not seg.get("kept"):
            continue
        rels = seg.get("relations") or []
        touches_planned = any(
            (a in planned_houses or b in planned_houses) for a, b in rels
        )
        if not rels or not touches_planned:
            seg["kept"] = False
            seg["arm_b_drop_reason"] = (
                "no_extracted_relation" if not rels else "relation_no_planned_house_touch")
            dropped += 1
    return payload_b, dropped


def shipped_ids(payload):
    units = {u["unit_id"] for u in payload.get("units", [])}
    segs = {s["segment_id"] for s in payload.get("segments", []) if s.get("kept")}
    return units | segs


def domain_bucket_for_id(payload, seg_id):
    """domain_match | failsafe | whole_chapter_unit | not_in_payload"""
    unit_ids = {u["unit_id"] for u in payload.get("units", [])}
    if seg_id in unit_ids:
        return "whole_chapter_unit"
    for s in payload.get("segments", []):
        if s["segment_id"] == seg_id:
            df = s.get("domain_filter")
            if df == "domain_match":
                return "domain_match"
            if df in ("failsafe_untagged", "failsafe_unknown_id"):
                return "failsafe"
            return f"other({df})"
    return "not_in_payload"


def zero_relation_stats(payload):
    """Of ARM A's KEPT segments, how many have zero extracted relations at
    all -- the population ARM B's rule would delete. (count, kept_total, pct)"""
    kept = [s for s in payload.get("segments", []) if s.get("kept")]
    zero = [s for s in kept if not (s.get("relations") or [])]
    pct = (100.0 * len(zero) / len(kept)) if kept else 0.0
    return len(zero), len(kept), pct


def load_seg_domain_map():
    tags = P._load_domain_tags()
    return {s["segment_id"]: set(s.get("domains") or []) for s in tags["segments"]}


def timing_bucket_for_id(payload, seg_domain_map, seg_id):
    """whole_chapter_unit | timing_dasha | career_marriage | other"""
    unit_ids = {u["unit_id"] for u in payload.get("units", [])}
    if seg_id in unit_ids:
        return "whole_chapter_unit"
    doms = seg_domain_map.get(seg_id, set())
    if "timing_dasha" in doms:
        return "timing_dasha"
    if doms & {"career", "marriage"}:
        return "career_marriage"
    return "other"


def run_arm(label, payload, plan, model, seg_domain_map=None):
    prompt = build_interpreter_prompt(QUESTION, plan, payload)
    full_text_for_estimate = INTERPRETER_SYSTEM + "\n" + prompt
    real_tokens_est = len(full_text_for_estimate) // 4
    approx_tokens_val = PB is not None and _payload_tokens(payload)

    t0 = time.time()
    error = None
    content, usage = None, {"prompt_tokens": None, "completion_tokens": None}
    try:
        content, usage = call_interpreter(prompt, model)
    except Exception as e:
        error = f"{type(e).__name__}: {e}"
    wall = round(time.time() - t0, 2)

    row = {
        "arm": label, "model": model,
        "approx_tokens": approx_tokens_val,
        "real_tokens_chars_over_4": real_tokens_est,
        "prompt_tokens_api": usage.get("prompt_tokens"),
        "completion_tokens_api": usage.get("completion_tokens"),
        "kept_segment_count": sum(1 for s in payload.get("segments", []) if s.get("kept")),
        "whole_units": len(payload.get("units", [])),
        "wall_clock_s": wall,
        "error": error,
        "claims": None, "cited_ids": [], "ghosts": [], "silent_on": [],
        "reading": None,
    }
    if error:
        row["estimated_cost_usd"] = 0.0
        return row

    price = PRICES.get(model, {"in": 0.0, "out": 0.0})
    if usage.get("prompt_tokens") is not None:
        cost = (usage["prompt_tokens"] / 1e6 * price["in"] +
                (usage.get("completion_tokens") or 0) / 1e6 * price["out"])
    else:
        cost = real_tokens_est / 1e6 * price["in"]
    row["estimated_cost_usd"] = round(cost, 4)

    try:
        parsed = json.loads(content)
    except Exception as e:
        row["error"] = f"JSON parse failed: {type(e).__name__}: {e}"
        return row

    ship = shipped_ids(payload)
    cited = sorted({i for c in parsed.get("claims", []) for i in c.get("segment_ids", [])})
    row["claims"] = len(parsed.get("claims", []))
    row["claims_detail"] = parsed.get("claims", [])
    row["cited_ids"] = cited
    row["ghosts"] = [i for i in cited if i not in ship]
    row["silent_on"] = parsed.get("silent_on", [])
    row["reading"] = parsed.get("reading", "")
    row["cited_bucket_counts"] = {}
    for cid in cited:
        b = domain_bucket_for_id(payload, cid)
        row["cited_bucket_counts"][b] = row["cited_bucket_counts"].get(b, 0) + 1
    row["cited_timing_bucket_counts"] = {}
    if seg_domain_map is not None:
        for cid in cited:
            tb = timing_bucket_for_id(payload, seg_domain_map, cid)
            row["cited_timing_bucket_counts"][tb] = row["cited_timing_bucket_counts"].get(tb, 0) + 1
    return row


def _payload_tokens(payload):
    whole = sum(u.get("tokens", 0) for u in payload.get("units", []))
    kept = sum(s.get("tokens", 0) for s in payload.get("segments", []) if s.get("kept"))
    return whole + kept


def main():
    print(f"PREDICTION (stated before running): ARM B will keep FEWER THAN "
          f"10 segments and may keep zero, because dasha doctrine names "
          f"periods, not houses. If ARM B keeps a healthy segment count, "
          f"that inverts this prediction -- flagged loudly below if it "
          f"happens.")

    t_plan0 = time.time()
    plan = P.plan_question(QUESTION)
    plan_seconds = round(time.time() - t_plan0, 2)

    lines = []
    p = lines.append
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())

    p("# Wide (fail-safe) vs strict house-filtered payload -- ARM A vs ARM B")
    p("")
    p(f"Generated: {now}")
    p(f"Question: {QUESTION}")
    p(f"Plan built once, live planner call, temp=0, {plan_seconds}s. "
      f"Reused unchanged for both arms.")
    p("")
    p("## Prediction (stated before running)")
    p("")
    p("ARM B will keep FEWER THAN 10 segments and may keep zero, because "
      "dasha doctrine names periods, not houses. If ARM B keeps a healthy "
      "segment count, that inverts this prediction -- flag loudly.")
    p("")
    p("## Plan (shared by both arms)")
    p("")
    p("```json")
    p(json.dumps(plan.to_dict(), ensure_ascii=False, indent=2))
    p("```")
    p("")

    if not plan.in_scope or not plan.domains:
        p("PLAN REFUSED / no domains -- cannot build either arm. Stopping.")
        report_text = "\n".join(lines) + "\n"
        _write(report_text, ts)
        print("Plan refused or produced no domains -- see diagnostics/latest_run.md")
        return

    if set(plan.domains) != EXPECTED_DOMAINS:
        p(f"## STOP -- planner domains do not match expectation")
        p("")
        p(f"Expected domains = {sorted(EXPECTED_DOMAINS)}. Live planner "
          f"returned domains = {sorted(plan.domains)}. Per instruction, "
          f"reporting the plan (above) and stopping -- NOT substituting a "
          f"canned plan.")
        p("")
        report_text = "\n".join(lines) + "\n"
        _write(report_text, ts)
        print(f"STOP: planner domains {sorted(plan.domains)} != expected "
              f"{sorted(EXPECTED_DOMAINS)} -- see diagnostics/latest_run.md")
        return

    selection = P.select_units(plan, token_budget=P.DEFAULT_TOKEN_BUDGET)
    payload_a = PB.build_payload(CHART_FACTS, unit_ids=selection.unit_ids)
    payload_a = P.filter_segments_by_domain(payload_a, plan)
    payload_b, n_dropped_by_arm_b = build_arm_b(payload_a, plan)
    seg_domain_map = load_seg_domain_map()

    zero_rel_count, kept_a_total, zero_rel_pct = zero_relation_stats(payload_a)
    p("## Zero-extracted-relation population in ARM A's kept segments")
    p("")
    p(f"Of ARM A's {kept_a_total} kept segments, {zero_rel_count} "
      f"({zero_rel_pct:.1f}%) have ZERO extracted relations at all -- this "
      f"is the population ARM B's rule deletes outright, in addition to any "
      f"non-empty-relation segments whose pair(s) don't touch a planned "
      f"house.")
    p("")

    arm_b_kept = sum(1 for s in payload_b.get("segments", []) if s.get("kept"))
    p("## ARM B segment count (headline)")
    p("")
    p(f"ARM B kept segments: {arm_b_kept} "
      f"(+ {len(payload_b.get('units', []))} whole-chapter units, untouched "
      f"by ARM B's rule).")
    p("")

    p("## ARM B construction note")
    p("")
    p(f"ARM B additionally dropped {n_dropped_by_arm_b} segment(s) that ARM A "
      f"kept, because either they had NO extracted relation at all, or their "
      f"relation(s) touched no planned house {sorted(set(plan.houses))}. "
      f"This is NOT the shipped `no_relation_failsafe` rule -- it is its "
      f"inverse, unique to this probe. Whole-chapter units "
      f"({len(payload_a.get('units', []))}) are untouched by ARM B's rule "
      f"in both arms, since extract_relations never ran on them "
      f"individually.")
    p("")

    rows = []
    rows.append(run_arm("A (wide)", payload_a, plan, "gpt-4o-mini", seg_domain_map))

    arm_b_skipped = (arm_b_kept == 0)
    ran_b_on_4o = False
    if arm_b_skipped:
        p("## ARM B -> gpt-4o gate")
        p("")
        p("SKIPPED -- ARM B kept 0 segments. Both ARM B model calls "
          "(gpt-4o-mini and the gpt-4o gate) were skipped rather than "
          "sending a vacuous request. $0 spent on ARM B.")
        p("")
        rows.append({
            "arm": "B (strict)", "model": "N/A (skipped, 0 kept segments)",
            "approx_tokens": _payload_tokens(payload_b),
            "real_tokens_chars_over_4": None,
            "prompt_tokens_api": None, "completion_tokens_api": None,
            "kept_segment_count": 0, "whole_units": len(payload_b.get("units", [])),
            "wall_clock_s": 0.0,
            "error": "skipped: ARM B has 0 kept segments",
            "claims": None, "cited_ids": [], "ghosts": [], "silent_on": [],
            "reading": None, "estimated_cost_usd": 0.0,
            "cited_bucket_counts": {}, "cited_timing_bucket_counts": {},
        })
    else:
        rows.append(run_arm("B (strict)", payload_b, plan, "gpt-4o-mini", seg_domain_map))
        b_real_tokens = rows[1]["real_tokens_chars_over_4"]
        if not rows[1]["error"] and b_real_tokens < REAL_TOKEN_THRESHOLD_FOR_4O:
            rows.append(run_arm("B (strict)", payload_b, plan, "gpt-4o", seg_domain_map))
            ran_b_on_4o = True
        p("## ARM B -> gpt-4o gate")
        p("")
        p(f"ARM B real tokens (chars/4 estimate) = {b_real_tokens}. Threshold = "
          f"{REAL_TOKEN_THRESHOLD_FOR_4O}. "
          f"{'Under threshold -- ALSO sent to gpt-4o (row 3 below).' if ran_b_on_4o else 'At or over threshold -- gpt-4o NOT attempted for ARM B.'}")
        p("")

    # ---- Table 1 ----
    p("## 1. Cost / size per arm")
    p("")
    p("| arm | model | approx tokens (payload) | real tokens (chars/4 est.) | "
      "API prompt_tokens | API completion_tokens | kept segments | whole units | "
      "wall-clock s | est. cost USD | error |")
    p("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        p(f"| {r['arm']} | {r['model']} | {r['approx_tokens']} | "
          f"{r['real_tokens_chars_over_4']} | {r['prompt_tokens_api']} | "
          f"{r['completion_tokens_api']} | {r['kept_segment_count']} | "
          f"{r['whole_units']} | {r['wall_clock_s']} | {r['estimated_cost_usd']} | "
          f"{r['error'] or ''} |")
    p("")

    # ---- Table 2 ----
    p("## 2. Claims / citations per arm")
    p("")
    p("| arm | model | claims | cited ids | ghost count | ghosts |")
    p("|---|---|---|---|---|---|")
    for r in rows:
        p(f"| {r['arm']} | {r['model']} | {r['claims']} | "
          f"{', '.join(r['cited_ids']) or '(none)'} | {len(r['ghosts'])} | "
          f"{', '.join(r['ghosts']) or '(none)'} |")
    p("")

    a_row = rows[0]
    b_rows = [r for r in rows[1:]]
    a_ids = set(a_row["cited_ids"] or [])
    p("## 3. Citation set difference (both mini)")
    p("")
    for r in b_rows:
        b_ids = set(r["cited_ids"] or [])
        only_a = sorted(a_ids - b_ids)
        only_b = sorted(b_ids - a_ids)
        p(f"### A (wide, gpt-4o-mini) vs {r['arm']} ({r['model']})")
        p("")
        p(f"- cited by A but NOT this arm: {only_a or '(none)'}")
        p(f"- cited by this arm but NOT A: {only_b or '(none)'}")
        p("")

    # ---- Table 4 ----
    p("## 4. Cited-id origin: domain_match vs fail-safe (the decision number)")
    p("")
    p("| arm | model | domain_match | failsafe (untagged/unknown_id) | "
      "whole_chapter_unit | other |")
    p("|---|---|---|---|---|---|")
    for r in rows:
        counts = r.get("cited_bucket_counts", {})
        other = sum(v for k, v in counts.items() if k not in
                    ("domain_match", "failsafe", "whole_chapter_unit"))
        p(f"| {r['arm']} | {r['model']} | {counts.get('domain_match', 0)} | "
          f"{counts.get('failsafe', 0)} | {counts.get('whole_chapter_unit', 0)} | "
          f"{other} |")
    p("")

    # ---- Table 5 ----
    p("## 5. Cited-id origin: timing_dasha vs career/marriage vs whole-chapter")
    p("")
    p("| arm | model | timing_dasha | career/marriage | whole_chapter_unit | other |")
    p("|---|---|---|---|---|---|")
    for r in rows:
        tcounts = r.get("cited_timing_bucket_counts", {})
        p(f"| {r['arm']} | {r['model']} | {tcounts.get('timing_dasha', 0)} | "
          f"{tcounts.get('career_marriage', 0)} | "
          f"{tcounts.get('whole_chapter_unit', 0)} | {tcounts.get('other', 0)} |")
    p("")

    # ---- Section 6 ----
    p("## 6. Readings, verbatim, side by side")
    p("")
    for r in rows:
        p(f"### {r['arm']} -- {r['model']}")
        p("")
        p(r["reading"] or f"(no reading -- error: {r['error']})")
        p("")
        p(f"silent_on: {r['silent_on']}")
        p("")

    # ---- Deviation check ----
    p("## Deviation from prediction")
    p("")
    if arm_b_kept >= 10:
        p(f"**LOUD FLAG: ARM B kept a HEALTHY segment count ({arm_b_kept} "
          f">= 10). This INVERTS the stated prediction (fewer than 10, "
          f"possibly zero).**")
    elif arm_b_kept == 0:
        p(f"ARM B kept 0 segments -- consistent with the stated prediction's "
          f"\"may keep zero\" branch. Strict is house-shaped only for this "
          f"timing question; both ARM B model calls were skipped.")
    else:
        p(f"ARM B kept {arm_b_kept} segments (< 10) -- consistent with the "
          f"stated prediction's direction.")
    p("")
    a_claims = a_row["claims"] or 0
    b_mini_row = rows[1] if len(rows) > 1 else None
    b_claims = (b_mini_row["claims"] or 0) if b_mini_row else 0
    if b_mini_row is not None and not arm_b_skipped and b_claims > a_claims:
        p(f"**LOUD FLAG: ARM B (strict, gpt-4o-mini) produced MORE claims "
          f"({b_claims}) than ARM A (wide, gpt-4o-mini) ({a_claims}). This "
          f"inverts the fail-safe-justification assumption from the prior "
          f"career-question probe.**")
    elif not arm_b_skipped:
        p(f"ARM B claims ({b_claims}) <= ARM A claims ({a_claims}).")
    p("")

    report_text = "\n".join(lines) + "\n"
    path = _write(report_text, ts)

    print(f"plan_seconds={plan_seconds}  arms_run={len(rows)}  "
          f"ran_B_on_4o={ran_b_on_4o}")
    for r in rows:
        print(f"  {r['arm']:12s} {r['model']:14s} claims={r['claims']} "
              f"cited={len(r['cited_ids'])} ghosts={len(r['ghosts'])} "
              f"cost=${r['estimated_cost_usd']} err={r['error']}")
    print(f"report -> {path}")
    print(f"      -> {LATEST}")


def _write(report_text, ts):
    os.makedirs(RUNS_DIR, exist_ok=True)
    path = os.path.join(RUNS_DIR, f"{ts}_wide_vs_strict.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(report_text)
    shutil.copyfile(path, LATEST)
    return path


if __name__ == "__main__":
    main()
