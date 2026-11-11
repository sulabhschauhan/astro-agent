"""S157 BLIND A/B: with-corpus (Arm A) vs facts-only (Arm B) expert answers.

DECISION THIS SERVES: if Sulabh cannot tell the arms apart in a blind read, cut the
corpus payload hard; else keep the corpus and only add a token budget.

Live calls (consented): 6 planner (gpt-4o, one per question, planned ONCE and the
SAME Plan reused by both arms -- never re-planned) + 12 interpreter (gpt-5).
Arm B (corpus emptied) runs for all six FIRST; any failure/refusal there stops
the run before Arm A spends anything.

No production code is edited: the script patches `planner.plan_question` (return
the saved plan) and, for Arm B only, wraps `planner.build_from_plan` (blank the
verse segments/units). Everything else -- fact block, expert prompt, model
routing, settings -- is the production path (pipeline.answer_question,
expert=True, no history). The script judges / scores NOTHING.

    python scripts/ab_corpus_vs_facts.py
"""
from __future__ import annotations

import datetime
import json
import os
import random
import shutil
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

from expert_pilot import SULABH  # noqa: E402  (reuse the pilot's chart identity)
from agent.chart_calculator import calculate_chart  # noqa: E402
from agent.astro import capability_gate, pipeline, planner  # noqa: E402
from agent.astro.static_facts import build_static_facts  # noqa: E402

SEED = 157
QUESTIONS = [
    "What does my chart say about my inner nature and spiritual path?",
    "When will things get better for my career / money?",
    "Will I own my own house?",
    "How are my health, relationships and career looking over the next two or three years?",
    "Were the years around 2010 rough for me, and why?",
    "What does my chart say about children?",
]


def _plan_dict(p) -> dict:
    return {"domains": list(p.domains or []), "houses": list(p.houses or []),
            "time_scope": p.time_scope,
            "capabilities": list(getattr(p, "capabilities", None) or []),
            "source": p.source, "planner_fallback": p.planner_fallback}


def _run_arm(q, plan, chart, chart_facts, *, corpus: bool) -> dict:
    """One interpreter call via the production path with a fixed plan."""
    real_plan, real_build = planner.plan_question, planner.build_from_plan

    def _blank(*a, **k):
        built = real_build(*a, **k)
        pl = built.get("payload")
        if isinstance(pl, dict):
            built = dict(built, payload=dict(pl, segments=[], units=[]))
        return built

    planner.plan_question = lambda question, **k: plan  # never re-plan
    if not corpus:
        planner.build_from_plan = _blank
    t0 = time.perf_counter()
    try:
        res = pipeline.answer_question(q, chart_facts, chart=chart, history=None,
                                       expert=True)
    finally:
        planner.plan_question, planner.build_from_plan = real_plan, real_build
    secs = round(time.perf_counter() - t0, 2)
    u = res.get("usage") or {}
    return {"answer": res.get("answer") or "", "refused": bool(res.get("refused")),
            "reason": res.get("reason"), "model": res.get("model"),
            "prompt_tokens": u.get("prompt_tokens"),
            "completion_tokens": u.get("completion_tokens"), "seconds": secs,
            "payload_approx_tokens": res.get("tokens")}


def main() -> int:
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = os.path.join(_ROOT, "diagnostics", "runs")
    os.makedirs(out, exist_ok=True)
    report = [f"# AB corpus-vs-facts run {ts}", ""]
    calls = {"planner": 0, "interpreter_A": 0, "interpreter_B": 0}

    def _finish(code, extra=""):
        report.append(extra)
        path = os.path.join(out, f"{ts}.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(report) + "\n")
        shutil.copyfile(path, os.path.join(_ROOT, "diagnostics", "latest_run.md"))
        return code

    chart = calculate_chart(*SULABH)
    chart_facts = build_static_facts(chart)

    # 1. Plan every question ONCE (live planner), run the deterministic gate.
    plans, runnable, skipped = {}, [], []
    for q in QUESTIONS:
        p = planner.plan_question(q)
        calls["planner"] += 1
        if p.planner_fallback or p.source not in ("llm", "llm_retry"):
            return _finish(1, f"STOP: planner fell back on {q!r}: {p.validation_errors}")
        v = capability_gate.assess(p)
        plans[q] = p
        if v.refuse_outright or not v.plan.domains:
            skipped.append(q)
        else:
            runnable.append(q)
    report.append(f"planner calls: {calls['planner']}; "
                  f"no-corpus-domain (skipped, arms would be identical): {skipped or 'none'}")

    # 2. Arm B for all runnable questions FIRST.
    arm_b = {}
    for q in runnable:
        calls["interpreter_B"] += 1
        try:
            r = _run_arm(q, plans[q], chart, chart_facts, corpus=False)
        except Exception as e:  # noqa: BLE001
            return _finish(1, f"STOP: Arm B raised on {q!r}: {type(e).__name__}: {e}")
        if r["refused"] or not r["answer"].strip():
            return _finish(1, f"STOP: Arm B refused/empty on {q!r}: {r['reason']}")
        arm_b[q] = r

    # 3. Arm A.
    arm_a = {}
    for q in runnable:
        calls["interpreter_A"] += 1
        try:
            arm_a[q] = _run_arm(q, plans[q], chart, chart_facts, corpus=True)
        except Exception as e:  # noqa: BLE001
            arm_a[q] = {"answer": "", "refused": True, "reason": f"{type(e).__name__}: {e}",
                        "prompt_tokens": None, "completion_tokens": None, "seconds": None,
                        "model": None}
            report.append(f"Arm A FAILED on {q!r}: {arm_a[q]['reason']}")

    # 4. Blind file + key (random X/Y per question, fixed seed).
    rng = random.Random(SEED)
    blind = ["# Blind A/B -- read each pair, fill in the lines. Arms are not labelled.", ""]
    key = {"seed": SEED, "questions": []}
    for i, q in enumerate(runnable, 1):
        a_is_x = rng.random() < 0.5
        x, y = (arm_a[q], arm_b[q]) if a_is_x else (arm_b[q], arm_a[q])
        blind += [f"## Q{i}. {q}", "", "### X", "", x["answer"], "", "### Y", "",
                  y["answer"], "", "**Better: X / Y / Same**", "", "**Why:**", "", "---", ""]
        key["questions"].append({
            "n": i, "question": q, "plan": _plan_dict(plans[q]),
            "X": "A_with_books" if a_is_x else "B_facts_only",
            "Y": "B_facts_only" if a_is_x else "A_with_books",
            "A_with_books": {k: arm_a[q].get(k) for k in
                             ("model", "prompt_tokens", "completion_tokens", "seconds",
                              "refused", "payload_approx_tokens")},
            "B_facts_only": {k: arm_b[q].get(k) for k in
                             ("model", "prompt_tokens", "completion_tokens", "seconds",
                              "refused", "payload_approx_tokens")}})
    key["skipped_no_corpus_domain"] = skipped
    bp = os.path.join(out, f"{ts}_ab_blind.md")
    kp = os.path.join(out, f"{ts}_ab_key.json")
    with open(bp, "w", encoding="utf-8") as f:
        f.write("\n".join(blind))
    with open(kp, "w", encoding="utf-8") as f:
        json.dump(key, f, indent=2, ensure_ascii=False)

    def _tot(arm, k):
        return sum((r.get(k) or 0) for r in arm.values())
    report += ["", f"calls made: {calls}",
               f"failures: {[q for q, r in arm_a.items() if r['refused']] or 'none'}",
               f"prompt tokens  A={_tot(arm_a, 'prompt_tokens')}  B={_tot(arm_b, 'prompt_tokens')}",
               f"seconds        A={round(_tot(arm_a, 'seconds'), 1)}  B={round(_tot(arm_b, 'seconds'), 1)}",
               f"blind: {bp}", f"key:   {kp}"]
    return _finish(0)


if __name__ == "__main__":
    sys.exit(main())
