"""
END-TO-END POC RUNNER -- Planner -> Selector -> Payload -> Interpreter.

DECISION THIS SERVES: does the five-stage pipeline answer a real question
end to end without a hand-picked chapter list?
  if yes -> POC closed, next work is the silence gate (S124 open item 3)
  if no  -> the failing stage is named in the report, nothing else changes

TOKEN CEILING: ~60k payload + one interpreter call per question.

Usage
  # no LLM calls at all -- proves the plumbing, uses a canned plan
  PYTHONIOENCODING=utf-8 python scripts/run_planner_poc.py --dry-run

  # live planner only (1 cheap call), no interpreter
  PYTHONIOENCODING=utf-8 python scripts/run_planner_poc.py --plan-only

  # full end to end (planner call + interpreter call)
  PYTHONIOENCODING=utf-8 python scripts/run_planner_poc.py \
      -q "Will my child succeed in his career?"

Writes diagnostics/runs/<timestamp>_planner_poc.md and copies it to
diagnostics/latest_run.md (per the S124 overwrite-only fix).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.astro import planner as P  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS_DIR = os.path.join(ROOT, "diagnostics", "runs")
LATEST = os.path.join(ROOT, "diagnostics", "latest_run.md")

# Sulabh's chart, same values scripts/spike_career_filtered.py pins.
CHART_FACTS = {
    "lord_house_map": {1: 1, 2: 2, 3: 3, 4: 4, 5: 2, 6: 6,
                       7: 12, 8: 12, 9: 9, 10: 4, 11: 5, 12: 6},
    "ascendant_sign": "Sagittarius",
}

DEFAULT_QUESTIONS = [
    "What does my chart say about my career?",
    "Will my child succeed in his career?",
    "My ascendant is Cancer. What does that say about my nature?",
    "When will I get married?",
]

# Canned plans for --dry-run ONLY. These are what a correct planner
# SHOULD emit; they are never used in a live run and never asserted as
# the live planner's output.
_CANNED = {
    "What does my chart say about my career?": {
        "domains": ["career"], "houses": [1, 10], "whose_chart": "self",
        "time_scope": "none", "in_scope": True,
        "reasoning": "10th house of karma, 1st for the native's own capacity."},
    "Will my child succeed in his career?": {
        "domains": ["children", "career"], "houses": [5, 2, 10],
        "whose_chart": "other", "time_scope": "future", "in_scope": True,
        "reasoning": "Child is the 5th. His 10th is the 10th from the 5th, "
                     "i.e. the 2nd of the native's own chart."},
    "My ascendant is Cancer. What does that say about my nature?": {
        "domains": ["planetary_nature", "health"], "houses": [1],
        "whose_chart": "self", "time_scope": "none", "in_scope": True,
        "reasoning": "Cancer here names a rasi, not a disease."},
    "When will I get married?": {
        "domains": ["marriage", "timing_dasha"], "houses": [7, 2, 11],
        "whose_chart": "self", "time_scope": "future", "in_scope": True,
        "reasoning": "7th for the spouse, 2nd for family, 11th for fulfilment; "
                     "'when' makes the dasha material mandatory."},
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


def canned_llm(question):
    obj = _CANNED.get(question)
    if obj is None:
        raise P.PlannerError(
            f"--dry-run has no canned plan for {question!r}; "
            f"add one or drop --dry-run")
    return json.dumps(obj)


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
                  key=lambda s: (s.get("unit_id", ""), s.get("ordinal", 0)))
    for s in kept:
        parts.append(f"[{s['segment_id']}] {s.get('text', '')}\n")
    return "\n".join(parts)


def call_interpreter(prompt, model="gpt-4o"):
    from openai import OpenAI
    client = OpenAI()
    resp = client.chat.completions.create(
        model=model, temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": INTERPRETER_SYSTEM},
                  {"role": "user", "content": prompt}])
    return resp.choices[0].message.content or ""


def run_one(question, *, dry_run, plan_only, budget, model="gpt-4o"):
    llm = canned_llm if dry_run else None
    row = {"question": question}
    t0 = time.time()
    try:
        res = P.plan_and_build(question, CHART_FACTS, llm=llm,
                               token_budget=budget)
    except Exception as e:
        row["error"] = f"{type(e).__name__}: {e}"
        return row
    plan = res["plan"]
    row.update({
        "domains": plan.domains, "houses": plan.houses,
        "whose_chart": plan.whose_chart, "time_scope": plan.time_scope,
        "in_scope": plan.in_scope, "source": plan.source,
        "planner_fallback": plan.planner_fallback,
        "reasoning": plan.reasoning,
        "validation_errors": plan.validation_errors,
        "refused": res["refused"],
        "plan_seconds": round(time.time() - t0, 2),
    })
    row["estimated_real_tokens"] = res.get("estimated_real_tokens", 0)
    row["exceeds_context"] = res.get("exceeds_context", False)
    if res["refused"]:
        row["refusal_reason"] = res.get("refusal_reason")
        # a refused row NEVER makes an interpreter call -- that is the whole
        # point of the ceiling: no oversized request is ever sent.
        return row
    sel, pay = res["selection"], res["payload"]
    row.update({
        "units": len(sel.unit_ids),
        "kept_segments": sum(1 for s in pay["segments"] if s.get("kept")),
        "tokens": res["tokens"],
        "corpus_pct": round(100 * res["tokens"] / sel.corpus_tokens, 1),
        "over_budget": res["over_budget"],
        "domain_filter": pay["domain_filter"]["counts"],
        "segment_cut_pct": pay["domain_filter"]["segment_cut_pct"],
    })
    if dry_run or plan_only:
        return row
    prompt = build_interpreter_prompt(question, plan, pay)
    t1 = time.time()
    try:
        raw = call_interpreter(prompt, model=model)
        parsed = json.loads(raw)
        row["claims"] = len(parsed.get("claims", []))
        row["silent_on"] = parsed.get("silent_on", [])
        row["reading"] = parsed.get("reading", "")
        row["cited_ids"] = sorted({i for c in parsed.get("claims", [])
                                   for i in c.get("segment_ids", [])})
        # every cited id must exist in what we actually shipped
        shipped = ({u["unit_id"] for u in pay["units"]} |
                   {s["segment_id"] for s in pay["segments"] if s.get("kept")})
        row["uncited_ghosts"] = [i for i in row["cited_ids"] if i not in shipped]
    except Exception as e:
        row["interpreter_error"] = f"{type(e).__name__}: {e}"
    row["interpret_seconds"] = round(time.time() - t1, 2)
    return row


def write_report(rows, mode):
    os.makedirs(RUNS_DIR, exist_ok=True)
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    path = os.path.join(RUNS_DIR, f"{ts}_planner_poc.md")
    L = [f"# Planner POC end-to-end run ({mode})", "",
         f"Generated: {ts}", f"Planner version: {P.PLANNER_VERSION}", "",
         "## Summary", "",
         "| question | src | fb | domains | houses | whose | units | segs | tokens | %corp | budget |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        if "error" in r:
            L.append(f"| {r['question'][:40]} | ERROR | | | | | | | | | {r['error']} |")
            continue
        L.append(
            f"| {r['question'][:40]} | {r.get('source','')} | "
            f"{'YES' if r.get('planner_fallback') else '-'} | "
            f"{','.join(r.get('domains', []))} | {r.get('houses')} | "
            f"{r.get('whose_chart','')} | {r.get('units','-')} | "
            f"{r.get('kept_segments','-')} | {r.get('tokens','-'):,} | "
            f"{r.get('corpus_pct','-')}% | "
            f"{'OVER' if r.get('over_budget') else 'ok'} |"
            if isinstance(r.get('tokens'), int) else
            f"| {r['question'][:40]} | {r.get('source','')} | "
            f"{'YES' if r.get('planner_fallback') else '-'} | REFUSED | | | | | | | |")
    L += ["", "## Per-question detail", ""]
    for r in rows:
        L += [f"### {r['question']}", "", "```json",
              json.dumps({k: v for k, v in r.items() if k != "reading"},
                         ensure_ascii=False, indent=2), "```", ""]
        if r.get("reading"):
            L += ["**Reading:**", "", r["reading"], ""]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    shutil.copyfile(path, LATEST)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-q", "--question", action="append",
                    help="question (repeatable); default = the 4 POC cases")
    ap.add_argument("--dry-run", action="store_true",
                    help="no LLM calls anywhere; canned plans")
    ap.add_argument("--plan-only", action="store_true",
                    help="live planner call, no interpreter call")
    ap.add_argument("--budget", type=int, default=P.DEFAULT_TOKEN_BUDGET)
    ap.add_argument("--model", default="gpt-4o",
                    help="interpreter model, passed through to call_interpreter()")
    args = ap.parse_args()

    questions = args.question or DEFAULT_QUESTIONS
    mode = ("dry-run" if args.dry_run
            else "plan-only" if args.plan_only else "full end-to-end")
    rows = [run_one(q, dry_run=args.dry_run, plan_only=args.plan_only,
                    budget=args.budget, model=args.model) for q in questions]
    path = write_report(rows, mode)

    print(f"mode={mode}  questions={len(rows)}")
    for r in rows:
        if "error" in r:
            print(f"  ERROR  {r['question'][:50]}  {r['error']}")
        elif r.get("refused"):
            print(f"  REFUSE {r['question'][:50]}  {r.get('refusal_reason')}")
        else:
            print(f"  ok     {r['question'][:50]}  "
                  f"{r['tokens']:,} tok ({r['corpus_pct']}%)"
                  f"{'  OVER BUDGET' if r['over_budget'] else ''}"
                  f"{'  FALLBACK' if r['planner_fallback'] else ''}"
                  + (f"  ghosts={r['uncited_ghosts']}"
                     if r.get("uncited_ghosts") else ""))
    print(f"report -> {path}")
    print(f"      -> {LATEST}")


if __name__ == "__main__":
    main()
