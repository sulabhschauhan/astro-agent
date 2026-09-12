"""
THROWAWAY DRIVER. Not product code, not committed. Reuses ARM B
construction + interpreter-call machinery from scripts/probe_wide_vs_strict.py
unchanged (that file's build_arm_b / run_arm / load_seg_domain_map /
shipped_ids), just loops it over three questions, ARM B only, gpt-4o only.

DECISION THIS SERVES: was the career result a one-off, or does verse-level
(segment-level) retrieval work across domains?
  if >=2 of 3 questions cite a real SEGMENT id -> POC PASSES
  if 0 or 1 do -> retrieval is not earning its keep

Force PYTHONIOENCODING=utf-8. Writes ONLY to diagnostics/runs/<ts>_arm_b_
three_domains.md, then copies to diagnostics/latest_run.md.
"""
from __future__ import annotations

import dataclasses
import json
import os
import shutil
import sys
import time

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPTS_DIR)
sys.path.insert(0, ROOT)
sys.path.insert(0, SCRIPTS_DIR)

import probe_wide_vs_strict as W   # noqa: E402
from agent.astro import planner as P            # noqa: E402
from agent.astro import payload_builder as PB   # noqa: E402

RUNS_DIR = os.path.join(ROOT, "diagnostics", "runs")
LATEST = os.path.join(ROOT, "diagnostics", "latest_run.md")

QUESTIONS = [
    ("What does my chart say about my career?", [10, 1, 2, 6, 11]),
    ("What does my chart say about my children?", [5, 9, 2]),
    ("What does my chart say about my health?", [6, 8, 12, 1]),
]


def main():
    lines = []
    p = lines.append
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())

    p("# ARM B (strict), gpt-4o only, across 3 domains -- career/children/health")
    p("")
    p(f"Generated: {now}")
    p("ARM A skipped entirely per instruction (wide already ruled out). "
      "gpt-4o-mini skipped -- gpt-4o only.")
    p("")
    p("## Prediction (stated before running)")
    p("")
    p("At least 2 of 3 will cite >=1 real segment id. If all three cite "
      "only whole-chapter units, that is the headline: the segment "
      "machinery is not being used at all and the POC's central claim is "
      "unproven.")
    p("")

    seg_domain_map = W.load_seg_domain_map()
    rows = []
    total_cost = 0.0

    for i, (question, fallback_houses) in enumerate(QUESTIONS, start=1):
        t0 = time.time()
        plan = P.plan_question(question)
        plan_seconds = round(time.time() - t0, 2)

        used_fallback = len(plan.houses) < 3
        effective_houses = fallback_houses if used_fallback else plan.houses
        effective_plan = (dataclasses.replace(plan, houses=effective_houses)
                          if used_fallback else plan)

        selection = P.select_units(plan, token_budget=P.DEFAULT_TOKEN_BUDGET)
        payload_a = PB.build_payload(W.CHART_FACTS, unit_ids=selection.unit_ids)
        payload_a = P.filter_segments_by_domain(payload_a, plan)
        payload_b, n_dropped = W.build_arm_b(payload_a, effective_plan)

        # BUG GUARD: probe_wide_vs_strict.run_arm() builds its interpreter
        # prompt from the MODULE-LEVEL `W.QUESTION` global, not a per-call
        # argument (it was written for a single fixed question). This
        # driver loops 3 different questions, so the global must be
        # updated before every call or every arm answers whatever
        # question was last left in that module (caught live: readings
        # all discussed "marriage timing" regardless of the loop's actual
        # question -- W.QUESTION was still "When will I get married?"
        # from a prior task).
        W.QUESTION = question

        arm_b_kept = sum(1 for s in payload_b.get("segments", []) if s.get("kept"))

        row_meta = {
            "idx": i, "question": question,
            "planner_houses": plan.houses,
            "fallback_used": used_fallback,
            "effective_houses": effective_houses,
            "domains": plan.domains,
            "plan_seconds": plan_seconds,
            "arm_b_kept_segments": arm_b_kept,
            "arm_b_whole_units": len(payload_b.get("units", [])),
            "n_dropped_by_arm_b": n_dropped,
        }

        if arm_b_kept == 0 and row_meta["arm_b_whole_units"] == 0:
            call_row = {
                "arm": f"Q{i} strict", "model": "N/A (skipped, empty payload)",
                "approx_tokens": 0, "real_tokens_chars_over_4": 0,
                "prompt_tokens_api": None, "completion_tokens_api": None,
                "kept_segment_count": 0, "whole_units": 0, "wall_clock_s": 0.0,
                "error": "skipped: ARM B payload is entirely empty",
                "claims": None, "claims_detail": [], "cited_ids": [], "ghosts": [],
                "silent_on": [], "reading": None, "estimated_cost_usd": 0.0,
            }
        else:
            call_row = W.run_arm(f"Q{i} strict", payload_b, effective_plan,
                                 "gpt-4o", seg_domain_map)
            total_cost += call_row.get("estimated_cost_usd") or 0.0

        rows.append({**row_meta, **call_row})

    # ---- Table 1 ----
    p("## 1. Plan / payload / cost per question")
    p("")
    p("| # | question | planner houses | fallback used | effective houses | "
      "strict kept segments | approx tokens | API prompt_tokens | ratio | "
      "est. cost USD |")
    p("|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        pt = r.get("prompt_tokens_api")
        at = r.get("approx_tokens")
        ratio = round(pt / at, 3) if (pt and at) else "n/a"
        p(f"| {r['idx']} | {r['question']} | {r['planner_houses']} | "
          f"{'YES' if r['fallback_used'] else 'no'} | {r['effective_houses']} | "
          f"{r['arm_b_kept_segments']} | {at} | {pt} | {ratio} | "
          f"{r.get('estimated_cost_usd')} |")
    p("")
    fallback_rows = [r['idx'] for r in rows if r['fallback_used']]
    p(f"Rows using the fallback house list: {fallback_rows or '(none)'}")
    p("")

    # ---- Table 2 ----
    p("## 2. Claims, per-claim segment_ids arrays")
    p("")
    for r in rows:
        p(f"### Q{r['idx']} -- {r['question']}")
        p("")
        p(f"claims = {r['claims']}")
        p("")
        detail = r.get("claims_detail") or []
        if not detail:
            p("(no claims / no response)")
        else:
            p("| claim # | statement | segment_ids |")
            p("|---|---|---|")
            for j, c in enumerate(detail, start=1):
                stmt = (c.get("statement", "") or "").replace("|", "/")
                p(f"| {j} | {stmt} | {c.get('segment_ids', [])} |")
        p("")

    # ---- Table 3 (the decision column) ----
    p("## 3. THE DECISION COLUMN -- cited segment ids vs whole-chapter unit ids")
    p("")
    p("| # | question | segment ids cited (contain `_s`) | whole-chapter "
      "unit ids cited | segment id list | unit id list |")
    p("|---|---|---|---|---|---|")
    pass_count = 0
    for r in rows:
        cited = r.get("cited_ids") or []
        seg_ids = [c for c in cited if "_s" in c]
        unit_ids = [c for c in cited if "_s" not in c]
        if seg_ids:
            pass_count += 1
        p(f"| {r['idx']} | {r['question']} | {len(seg_ids)} | {len(unit_ids)} | "
          f"{seg_ids} | {unit_ids} |")
        r["_seg_ids_cited"] = seg_ids
        r["_unit_ids_cited"] = unit_ids
    p("")
    p(f"Questions citing >=1 real segment id: {pass_count} / 3")
    p("")

    # ---- Table 4 ----
    p("## 4. Ghost count per question")
    p("")
    p("| # | question | ghost count | ghosts |")
    p("|---|---|---|---|")
    for r in rows:
        ghosts = r.get("ghosts") or []
        p(f"| {r['idx']} | {r['question']} | {len(ghosts)} | {ghosts or '(none)'} |")
    p("")

    # ---- Section 5 ----
    p("## 5. Readings, verbatim")
    p("")
    for r in rows:
        p(f"### Q{r['idx']} -- {r['question']}")
        p("")
        p(r.get("reading") or f"(no reading -- error: {r.get('error')})")
        p("")
        p(f"silent_on: {r.get('silent_on')}")
        p("")

    # ---- Deviation check ----
    p("## Deviation from prediction")
    p("")
    if pass_count == 0:
        p("**LOUD FLAG: ALL THREE questions cited ONLY whole-chapter units, "
          "zero real segment ids. The segment machinery is not being used "
          "at all -- the POC's central claim is UNPROVEN. This inverts the "
          "stated prediction (>=2 of 3).**")
    elif pass_count >= 2:
        p(f"{pass_count}/3 questions cited >=1 real segment id -- consistent "
          f"with the stated prediction (>=2 of 3). POC PASSES per the "
          f"decision rule.")
    else:
        p(f"Only {pass_count}/3 questions cited a real segment id -- below "
          f"the stated prediction (>=2 of 3) and below the pass threshold. "
          f"Flagged as a deviation.")
    p("")
    p(f"Total OpenAI spend this run: ~${total_cost:.4f}")
    p("")

    report_text = "\n".join(lines) + "\n"
    os.makedirs(RUNS_DIR, exist_ok=True)
    path = os.path.join(RUNS_DIR, f"{ts}_arm_b_three_domains.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(report_text)
    shutil.copyfile(path, LATEST)

    print(f"pass_count={pass_count}/3  total_cost=${total_cost:.4f}")
    for r in rows:
        print(f"  Q{r['idx']} segs_cited={len(r.get('_seg_ids_cited', []))} "
              f"units_cited={len(r.get('_unit_ids_cited', []))} "
              f"ghosts={len(r.get('ghosts') or [])} err={r.get('error')}")
    print(f"report -> {path}")
    print(f"      -> {LATEST}")


if __name__ == "__main__":
    main()
