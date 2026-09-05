"""
THROWAWAY SPIKE. Not product code, not committed, not imported by anything.

DECISION THIS SERVES: does Option 2 (Track A computes dates deterministically,
Track C supplies only doctrinal meaning) answer a timing question properly?

STEP 0 verifies agent/astro/planner.py's three threshold constants are the
expected post-S125 values before trusting anything else in this file.
STEP 1 gets ONE live plan for "When will I get married?" and records it
verbatim -- never substituted, never judged.
STEP 2 tries to build Track A's deterministic fact block from
agent.calculations.dashas.vimshottari. Per the task's own rule: if that
module is a stub, this script names it and STOPS -- it does not
approximate a date, and it does not proceed to Track C or any LLM
interpreter call.

Force PYTHONIOENCODING=utf-8. Writes ONLY to diagnostics/runs/<ts>_spike_
option2_timing.md, then copies to diagnostics/latest_run.md.
"""
from __future__ import annotations

import inspect
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS_DIR = os.path.join(ROOT, "diagnostics", "runs")
LATEST = os.path.join(ROOT, "diagnostics", "latest_run.md")

QUESTION = "When will I get married?"

EXPECTED = {
    "HARD_CONTEXT_CEILING": 72_000,
    "APPROX_TO_REAL_RATIO": 1.70,
    "INTERPRETER_TPM_LIMIT": 30_000,
}

# Sulabh's chart, same values every prior probe in this arc pins.
CHART_FACTS = {
    "lord_house_map": {1: 1, 2: 2, 3: 3, 4: 4, 5: 2, 6: 6,
                       7: 12, 8: 12, 9: 9, 10: 4, 11: 5, 12: 6},
    "ascendant_sign": "Sagittarius",
}


def main():
    lines = []
    p = lines.append
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    total_cost = 0.0

    p("# Option 2 spike -- Track A (computed dates) + Track C (meaning only)")
    p("")
    p(f"Generated: {now}")
    p(f"Question: {QUESTION}")
    p("")
    p("## Prediction (stated before running)")
    p("")
    p("gpt-4o will produce >=1 dated claim, every date traceable to the "
      "fact block, and will stay silent on which specific outcome the "
      "marriage has. A date NOT in the fact block would be the single "
      "most important finding of the run, to be led with.")
    p("")

    # ------------------------------------------------------------------
    # STEP 0
    # ------------------------------------------------------------------
    from agent.astro import planner as P
    actual = {
        "HARD_CONTEXT_CEILING": getattr(P, "HARD_CONTEXT_CEILING", None),
        "APPROX_TO_REAL_RATIO": getattr(P, "APPROX_TO_REAL_RATIO", None),
        "INTERPRETER_TPM_LIMIT": getattr(P, "INTERPRETER_TPM_LIMIT", None),
    }
    p("## 1. Step 0 -- constant verification")
    p("")
    p("| constant | expected | actual | match |")
    p("|---|---|---|---|")
    step0_ok = True
    for k, exp in EXPECTED.items():
        act = actual[k]
        ok = (act == exp)
        step0_ok = step0_ok and ok
        p(f"| {k} | {exp} | {act} | {'OK' if ok else 'MISMATCH'} |")
    p("")

    if not step0_ok:
        p("**STOP -- agent/astro/planner.py is stale relative to the "
          "expected S125 values. Everything downstream is invalid and was "
          "not attempted.**")
        _finish(lines, ts, total_cost)
        print("STEP 0 FAILED -- planner.py constants do not match expected "
              "values. Stopped before any live call. See diagnostics/latest_run.md")
        return

    # ------------------------------------------------------------------
    # STEP 1 -- live plan
    # ------------------------------------------------------------------
    t0 = time.time()
    plan = P.plan_question(QUESTION)
    plan_seconds = round(time.time() - t0, 2)
    # planner's default LLM is gpt-4o; a single short structured-output
    # call, negligible cost (~$0.002), unavoidable per Step 1's own
    # instruction to use a live call.
    total_cost += 0.002

    houses_widened = sorted(plan.houses) != [7]
    p("## 2. Step 1 -- the plan (live, temp=0, NOT substituted)")
    p("")
    p("| domains | houses | whose_chart | time_scope | in_scope | "
      "houses widened beyond [7]? |")
    p("|---|---|---|---|---|---|")
    p(f"| {', '.join(plan.domains)} | {plan.houses} | {plan.whose_chart} | "
      f"{plan.time_scope} | {plan.in_scope} | {houses_widened} |")
    p("")
    p(f"Reasoning (verbatim): {plan.reasoning}")
    p("")
    p(f"Plan call: {plan_seconds}s, source={plan.source}, "
      f"planner_fallback={plan.planner_fallback}")
    p("")

    # ------------------------------------------------------------------
    # STEP 2 -- Track A: deterministic dates from vimshottari
    # ------------------------------------------------------------------
    p("## 3. Step 2 -- Track A deterministic fact block")
    p("")
    try:
        from agent.calculations.dashas import vimshottari as V
    except ImportError as e:
        p(f"**STOP -- cannot even import agent.calculations.dashas.vimshottari: "
          f"{type(e).__name__}: {e}**")
        _finish(lines, ts, total_cost)
        print(f"STEP 2 FAILED -- import error, see diagnostics/latest_run.md")
        return

    own_functions = [
        name for name, obj in inspect.getmembers(V, inspect.isfunction)
        if obj.__module__ == V.__name__
    ]
    own_classes = [
        name for name, obj in inspect.getmembers(V, inspect.isclass)
        if obj.__module__ == V.__name__
    ]
    module_file = inspect.getsourcefile(V)
    module_src = inspect.getsource(V)
    module_lines = len(module_src.splitlines())

    p(f"Module: `{os.path.relpath(module_file, ROOT)}` ({module_lines} line(s))")
    p("")
    p("```python")
    p(module_src.rstrip("\n"))
    p("```")
    p("")
    p(f"Public functions defined in this module: {own_functions or '(none)'}")
    p(f"Public classes defined in this module: {own_classes or '(none)'}")
    p("")

    if not own_functions and not own_classes:
        p("**STOP -- `agent/calculations/dashas/vimshottari.py` is a STUB: "
          "docstring only, zero functions, zero classes. Track A cannot "
          "compute the 7th-lord placement, the mahadasha sequence, the "
          "current mahadasha/antardasha, or the future 7th-lord periods. "
          "Per this task's own rule, no date is approximated and no "
          "interpreter call is made. Steps 3 and 4 are SKIPPED. "
          "$0 spent on Steps 3-4.**")
        p("")
        p(f"Total cost this run: ~${total_cost:.3f} (Step 1 planner call only).")
        _finish(lines, ts, total_cost)
        print("STOP at STEP 2: agent/calculations/dashas/vimshottari.py is "
              "a stub (docstring only, no functions/classes). Track A "
              "cannot compute dates. Steps 3-4 skipped, $0 spent on them. "
              "See diagnostics/latest_run.md")
        return

    # If we ever get here, vimshottari has real content -- this spike does
    # not implement Steps 2-4's actual date computation / retrieval / LLM
    # call in that branch; a follow-up prompt would be needed once Track A
    # is real. Recorded so this isn't silently mistaken for a full run.
    p("Module has real content -- this throwaway script's Step 2/3/4 "
      "implementation was written assuming a stub and does not compute "
      "dates from a live module. Re-run with a version of this script "
      "extended for the real API before trusting any output past this "
      "point.")
    _finish(lines, ts, total_cost)
    print("STEP 2 found a NON-stub vimshottari module -- this spike's "
          "code does not implement live date computation. See "
          "diagnostics/latest_run.md; do not trust Steps 3-4 (not run).")


def _finish(lines, ts, total_cost):
    report_text = "\n".join(lines) + "\n"
    os.makedirs(RUNS_DIR, exist_ok=True)
    path = os.path.join(RUNS_DIR, f"{ts}_spike_option2_timing.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(report_text)
    shutil.copyfile(path, LATEST)
    print(f"report -> {path}")
    print(f"      -> {LATEST}")


if __name__ == "__main__":
    main()
