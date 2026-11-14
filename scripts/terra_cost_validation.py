"""Terra single-interpreter cost + depth validation harness (S159+).

DECISION THIS SERVES: does gpt-6.1-terra read the books at least as well as gpt-5
and clearly better than gpt-5.6-luna, for the minimum spend. If yes -> Terra is the
single interpreter before gpt-5 shuts down 11 Dec 2026; else test gpt-5.6-terra.

TOKEN CEILING (this script's own OpenAI spend): decided by --model/--service-tier/
--questions. LIVE SPEND CAP: $8. The paid path refuses to call without --confirm
and prints the projected cost first.

TWO MODES
  --analyze-baseline : OFFLINE, $0, no OpenAI. Rebuilds the 11 Nov payloads from the
      saved plans, prices the RECORDED 11 Nov usage AND projects Terra/flex cost from
      diagnostics/model_rates.json, and runs the depth-attribution check on the
      existing 11 Nov answers. Proves the cost column + depth check before any paid
      call. Needs the local env (swisseph, Chroma) but no API key.
  --run : PAID. Forces a chosen model + service_tier on a question subset via an
      injected interpreter_llm (flex pricing, output sum-cap, full usage capture),
      reusing the 11 Nov plans so the payload is byte-comparable. Early-stop: run
      Q1 alone first, read the result, then continue.

No production code is edited. Model forcing = patch interpreter.INTERPRETER_MODEL /
LARGE_PAYLOAD_MODEL; flex + output-cap + cached/reasoning-token capture = the
injected interpreter_llm. Both are undone in a finally.

    python scripts/terra_cost_validation.py --analyze-baseline
    python scripts/terra_cost_validation.py --run --model gpt-6.1-terra \
        --service-tier flex --questions 1 --confirm
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import shutil
import sys
import time
from typing import Optional

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)                              # import agent.* without PYTHONPATH
sys.path.insert(0, os.path.join(_ROOT, "scripts"))     # import expert_pilot (SULABH)
_RUNS = os.path.join(_ROOT, "diagnostics", "runs")
_RATES = os.path.join(_ROOT, "diagnostics", "model_rates.json")
_BASELINE_KEY = os.path.join(_RUNS, "20261111T165143Z_ab_key.json")
_BASELINE_BLIND = os.path.join(_RUNS, "20261111T165143Z_ab_blind.md")

TIER_THRESHOLD = 272_000          # > this many INPUT tokens -> long-context rate
OUTPUT_SUM_CAP = 8_000            # max_completion_tokens (reasoning + visible together)
PAYLOAD_DRIFT_TOL = 0.02          # rebuilt payload must match 11 Nov prompt_tokens +-2%

# --------------------------------------------------------------------------- #
# PURE FUNCTIONS (stdlib only -- the test suite imports these without pulling   #
# in pipeline/planner/swisseph).                                                #
# --------------------------------------------------------------------------- #


def load_rates(path: str = _RATES) -> dict:
    """Load the canonical rate card. Raises with a clear message if absent."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"rate card not found at {path}; model_rates.json must exist") from e


def _tier_for(prompt_tokens: int) -> str:
    """OpenAI reprices the WHOLE request above the threshold, not just the overflow."""
    return "long" if (prompt_tokens or 0) > TIER_THRESHOLD else "short"


def compute_cost(model: str, prompt_tokens: int, cached_tokens: int,
                 completion_tokens: int, rates: dict, service_tier: str = "standard",
                 ) -> dict:
    """USD for one call. completion_tokens already includes reasoning tokens (OpenAI
    bills them at the output rate). cache-write is NOT exposed by the usage object, so
    it is not priced here -- see module notes. Returns the breakdown + the tier used.
    """
    try:
        block = rates["models"][model]
    except KeyError as e:
        raise KeyError(f"no rate row for model {model!r} in rate card") from e
    tier = _tier_for(prompt_tokens)
    row = block.get(tier) or block.get("flat")
    if row is None:
        raise KeyError(f"model {model!r} has no {tier!r} (or flat) rate block")
    mult = rates["_meta"]["service_tier_multipliers"].get(service_tier)
    if mult is None:
        raise KeyError(f"unknown service_tier {service_tier!r} in rate card")

    cached = cached_tokens or 0
    non_cached_in = max((prompt_tokens or 0) - cached, 0)
    usd_input = non_cached_in / 1e6 * row["input"]
    usd_cached = cached / 1e6 * row["cached"]
    usd_output = (completion_tokens or 0) / 1e6 * row["output"]
    total = (usd_input + usd_cached + usd_output) * mult
    return {"model": model, "tier": tier, "service_tier": service_tier,
            "usd_input": round(usd_input * mult, 6),
            "usd_cached": round(usd_cached * mult, 6),
            "usd_output": round(usd_output * mult, 6),
            "usd_total": round(total, 6)}


_WORD = re.compile(r"[a-z][a-z'-]{3,}")   # 4+ char alpha tokens; skips short glue words
_STOP = frozenset((
    "this", "that", "with", "from", "they", "them", "then", "than", "will", "would",
    "your", "yours", "have", "which", "when", "what", "whom", "into", "onto", "over",
    "under", "about", "there", "their", "these", "those", "been", "being", "were",
    "also", "such", "both", "each", "more", "most", "some", "very", "much", "like",
    "chart", "house", "houses", "sign", "signs", "lord", "lords", "planet", "planets",
    "native", "nature", "verse", "verses", "says", "said", "indicates", "suggests",
))


def _distinctive_tokens(text: str) -> set[str]:
    """Content tokens for overlap scoring: 4+ char alpha words minus common glue and
    minus astrology boilerplate that appears in every segment (would flatten scores).
    """
    return {t for t in _WORD.findall((text or "").lower()) if t not in _STOP}


def bucket_thirds(payload: dict) -> list[tuple[str, set[str]]]:
    """Order the payload the way the interpreter sees it (_verse_block order: kept
    segments, then whole-chapter units) and split into first/middle/last third.
    Returns [(label, token_set)] for labels first/middle/last.
    """
    ordered: list[str] = []
    for s in payload.get("segments", []):
        if s.get("kept"):
            ordered.append(s.get("text", ""))
    for u in payload.get("units", []):
        ordered.append(u.get("text", ""))
    n = len(ordered)
    if n == 0:
        return [("first", set()), ("middle", set()), ("last", set())]
    c1, c2 = n // 3, (2 * n) // 3
    groups = {"first": ordered[:c1] or ordered[:1],
              "middle": ordered[c1:c2],
              "last": ordered[c2:]}
    out = []
    for label in ("first", "middle", "last"):
        toks: set[str] = set()
        for seg in groups[label]:
            toks |= _distinctive_tokens(seg)
        out.append((label, toks))
    return out


def depth_attribution(answer_text: str, thirds: list[tuple[str, set[str]]]) -> dict:
    """Where does the answer's content trace to? For each third, the fraction of the
    answer's distinctive tokens that also appear UNIQUELY in that third (a token shared
    across thirds is dropped -- only third-discriminating tokens attribute). No LLM.
    Criterion (b) reads this: luna anchored on the first third; Terra must reach
    middle+last.
    """
    ans = _distinctive_tokens(answer_text)
    sets = {label: toks for label, toks in thirds}
    unique = {label: toks - (set().union(*(sets[o] for o in sets if o != label)))
              for label, toks in sets.items()}
    denom = len(ans) or 1
    hits = {label: len(ans & unique[label]) for label in sets}
    attributed = hits["first"] + hits["middle"] + hits["last"]
    # middle_last_share: of the answer tokens that attribute to SOME third, the
    # fraction landing in middle+last. Threshold-free and comparable across models.
    # Criterion (b) is Terra's share vs luna's on the SAME question, never an absolute
    # cutoff -- and a small attributed_tokens count means the share is noisy, so read
    # it as directional triage, not a gate. (The old boolean used a >0 cutoff, which
    # any single token tripped; removed.)
    return {"answer_tokens": len(ans), "attributed_tokens": attributed,
            "first": round(hits["first"] / denom, 4),
            "middle": round(hits["middle"] / denom, 4),
            "last": round(hits["last"] / denom, 4),
            "middle_last_share": (round((hits["middle"] + hits["last"]) / attributed, 4)
                                  if attributed else 0.0)}


# --------------------------------------------------------------------------- #
# BASELINE RECOVERY (offline)                                                   #
# --------------------------------------------------------------------------- #


def load_baseline() -> dict:
    """Join the 11 Nov key + blind file into {n: {question, plan, arms, answers}}."""
    with open(_BASELINE_KEY, encoding="utf-8") as f:
        key = json.load(f)
    answers = _parse_blind(_BASELINE_BLIND) if os.path.exists(_BASELINE_BLIND) else {}
    out = {}
    for q in key["questions"]:
        n = q["n"]
        xa = answers.get(n, {})
        # map X/Y answer text back to the arm it belongs to
        a_text = xa.get("X" if q["X"] == "A_with_books" else "Y", "")
        out[n] = {"question": q["question"], "plan": q["plan"],
                  "A_with_books": q["A_with_books"], "B_facts_only": q["B_facts_only"],
                  "answer_A_with_books": a_text}
    return out


def _parse_blind(path: str) -> dict:
    """Extract {n: {'X': text, 'Y': text}} from the blind markdown."""
    with open(path, encoding="utf-8") as f:
        txt = f.read()
    out: dict = {}
    for m in re.finditer(r"^## Q(\d+)\.", txt, re.M):
        n = int(m.group(1))
        block = txt[m.end():]
        nxt = re.search(r"^## Q\d+\.", block, re.M)
        block = block[:nxt.start()] if nxt else block
        parts = {}
        for lbl in ("X", "Y"):
            seg = re.search(rf"^### {lbl}\s*\n(.*?)(?=^### |\*\*Better|\Z)",
                            block, re.M | re.S)
            parts[lbl] = (seg.group(1).strip() if seg else "")
        out[n] = parts
    return out


# --------------------------------------------------------------------------- #
# PAYLOAD REBUILD (offline; lazy heavy imports)                                 #
# --------------------------------------------------------------------------- #


def _reconstruct_plan(question: str, plan_dict: dict):
    from agent.astro.planner import Plan
    return Plan(question=question, domains=list(plan_dict.get("domains") or []),
                houses=list(plan_dict.get("houses") or []), whose_chart="self",
                time_scope=plan_dict.get("time_scope", "none"), in_scope=True,
                reasoning="reused S157 plan (comparability-locked)",
                capabilities=list(plan_dict.get("capabilities") or []),
                source=plan_dict.get("source", "llm"),
                planner_fallback=bool(plan_dict.get("planner_fallback", False)))


def _build_payload(plan_dict: dict, question: str, chart_facts: dict):
    """Rebuild the exact 11 Nov payload offline (build_from_plan makes no OpenAI call)."""
    from agent.astro import planner
    plan = _reconstruct_plan(question, plan_dict)
    built = planner.build_from_plan(plan, chart_facts,
                                    token_budget=planner.DEFAULT_TOKEN_BUDGET,
                                    include_kp=True)
    return plan, built


# --------------------------------------------------------------------------- #
# INJECTED LLM for the paid run (flex + sum-cap + full usage)                   #
# --------------------------------------------------------------------------- #


def make_interpreter_llm(service_tier: str, output_cap: int = OUTPUT_SUM_CAP):
    """Build an interpreter_llm callable (system, user, *, model, reasoning_effort)
    -> (content, usage). Forces service_tier + max_completion_tokens and captures all
    four token counts. Degrades safely: an SDK/API that rejects service_tier or the
    reasoning knob falls back and records which path ran, rather than crashing a paid
    run mid-flight.
    """
    def _llm(system: str, user: str, *, model: str,
             reasoning_effort: Optional[str]) -> tuple[str, dict]:
        from openai import OpenAI
        client = OpenAI()
        kwargs = dict(model=model, max_completion_tokens=output_cap,
                      messages=[{"role": "system", "content": system},
                                {"role": "user", "content": user}])
        tier_applied = service_tier
        # service_tier first; drop to standard if the SDK/API refuses it.
        try:
            resp = _create_with_effort(client, reasoning_effort,
                                       service_tier=service_tier, **kwargs)
        except Exception:  # noqa: BLE001 -- service_tier refused -> standard
            tier_applied = "standard"
            resp = _create_with_effort(client, reasoning_effort, **kwargs)
        u = resp.usage
        usage = {"prompt_tokens": getattr(u, "prompt_tokens", 0),
                 "completion_tokens": getattr(u, "completion_tokens", 0),
                 "reasoning_tokens": getattr(getattr(u, "completion_tokens_details",
                                                      None), "reasoning_tokens", 0) or 0,
                 "cached_tokens": getattr(getattr(u, "prompt_tokens_details", None),
                                          "cached_tokens", 0) or 0,
                 "service_tier_requested": service_tier,
                 "service_tier_applied": tier_applied}
        return resp.choices[0].message.content or "", usage
    return _llm


def _create_with_effort(client, reasoning_effort, **kwargs):
    """reasoning_effort via named kwarg, then extra_body, then dropped (the S130 path)."""
    if reasoning_effort is None:
        return client.chat.completions.create(**kwargs)
    try:
        return client.chat.completions.create(reasoning_effort=reasoning_effort, **kwargs)
    except TypeError:
        return client.chat.completions.create(
            extra_body={"reasoning_effort": reasoning_effort}, **kwargs)


# --------------------------------------------------------------------------- #
# MODES                                                                         #
# --------------------------------------------------------------------------- #


def _chart_and_facts():
    from expert_pilot import SULABH
    from agent.chart_calculator import calculate_chart
    from agent.astro.static_facts import build_static_facts
    chart = calculate_chart(*SULABH)
    return chart, build_static_facts(chart)


def analyze_baseline() -> int:
    """OFFLINE. Price the 11 Nov run + project Terra/flex, and depth-check the answers."""
    rates = load_rates()
    base = load_baseline()
    chart, chart_facts = _chart_and_facts()
    rows, body = [], ["# Terra validation -- OFFLINE baseline analysis", ""]
    for n in sorted(base):
        rec = base[n]
        a = rec["A_with_books"]
        pt, ct, comp = a.get("prompt_tokens"), None, a.get("completion_tokens")
        plan, built = _build_payload(rec["plan"], rec["question"], chart_facts)
        rebuilt_tokens = built.get("tokens")
        # comparability guard: the rebuilt payload must reproduce the 11 Nov size
        # (approx-token proxy; exact prompt_tokens is only known after an API call).
        drift = None
        if a.get("payload_approx_tokens"):
            drift = abs((rebuilt_tokens or 0) - a["payload_approx_tokens"]) / \
                a["payload_approx_tokens"]
        depth = depth_attribution(rec["answer_A_with_books"], bucket_thirds(built["payload"]))
        old_cost = compute_cost(_norm_model(a.get("model")), pt or 0,
                                a.get("cached_tokens") or 0, comp or 0, rates, "standard")
        terra_std = compute_cost("gpt-6.1-terra", pt or 0, 0, comp or 0, rates, "standard")
        terra_flex = compute_cost("gpt-6.1-terra", pt or 0, 0, comp or 0, rates, "flex")
        rows.append({"n": n, "old_model": a.get("model"), "prompt_tokens": pt,
                     "rebuilt_approx": rebuilt_tokens, "drift": drift,
                     "old_usd": old_cost["usd_total"], "terra_std": terra_std["usd_total"],
                     "terra_flex": terra_flex["usd_total"], "tier": terra_std["tier"],
                     "depth": depth})
        body += [f"## Q{n}. {rec['question']}",
                 f"- old model / prompt_tokens: {a.get('model')} / {pt}",
                 f"- rebuilt payload approx tokens: {rebuilt_tokens} "
                 f"(drift vs 11 Nov approx: {None if drift is None else round(drift,4)})",
                 f"- Terra cost @ this payload: standard ${terra_std['usd_total']}  "
                 f"flex ${terra_flex['usd_total']}  (tier={terra_std['tier']})",
                 f"- depth attribution: first={depth['first']} middle={depth['middle']} "
                 f"last={depth['last']}  middle_last_share={depth['middle_last_share']} "
                 f"(attributed_tokens={depth['attributed_tokens']})",
                 ""]
    terra_std_total = round(sum(r["terra_std"] for r in rows), 4)
    terra_flex_total = round(sum(r["terra_flex"] for r in rows), 4)
    decisive = [r for r in rows if r["n"] in (1, 4, 5)]
    body += ["---", "",
             f"PROJECTED Terra cost, ALL {len(rows)} Qs: standard ${terra_std_total}  "
             f"flex ${terra_flex_total}",
             f"PROJECTED Terra cost, decisive subset Q1/Q4/Q5: "
             f"standard ${round(sum(r['terra_std'] for r in decisive),4)}  "
             f"flex ${round(sum(r['terra_flex'] for r in decisive),4)}",
             f"payload drift max: {max((r['drift'] or 0) for r in rows):.4f} "
             f"(tolerance {PAYLOAD_DRIFT_TOL}; above it = payload did NOT reproduce, STOP)"]
    _write_run("offline_baseline", body)
    print(f"[offline] Terra all-6 flex ${terra_flex_total} | "
          f"decisive Q1/Q4/Q5 flex "
          f"${round(sum(r['terra_flex'] for r in decisive),4)} | see latest_run.md")
    return 0


def run_paid(model: str, service_tier: str, question_ns: list[int], confirm: bool,
             reasoning_effort: Optional[str]) -> int:
    """PAID. Force model+tier on the chosen 11 Nov questions, reusing their plans."""
    rates = load_rates()
    base = load_baseline()
    ns = [n for n in question_ns if n in base]
    projected = sum(compute_cost(model, base[n]["A_with_books"].get("prompt_tokens") or 0,
                                 0, base[n]["A_with_books"].get("completion_tokens") or 0,
                                 rates, service_tier)["usd_total"] for n in ns)
    print(f"[paid] model={model} tier={service_tier} questions={ns} "
          f"PROJECTED ${round(projected,4)} (output est from 11 Nov; reasoning may add)")
    if not confirm:
        print("[paid] dry run -- pass --confirm to actually call OpenAI. Nothing spent.")
        return 0

    from agent.astro import interpreter as _interp, pipeline
    from agent.astro.answer_view import render_user_answer
    chart, chart_facts = _chart_and_facts()
    llm = make_interpreter_llm(service_tier)
    saved = (_interp.INTERPRETER_MODEL, _interp.LARGE_PAYLOAD_MODEL)
    _interp.INTERPRETER_MODEL = _interp.LARGE_PAYLOAD_MODEL = model   # force, both routes
    body, rows, spent = ["# Terra validation -- PAID run", ""], [], 0.0
    try:
        for n in ns:
            rec = base[n]
            plan = _reconstruct_plan(rec["question"], rec["plan"])
            import agent.astro.planner as _pl
            real = _pl.plan_question
            _pl.plan_question = lambda question, **k: plan   # reuse the 11 Nov plan
            t0 = time.perf_counter()
            try:
                res = pipeline.answer_question(rec["question"], chart_facts, chart=chart,
                                               history=None, expert=True,
                                               interpreter_llm=llm)
            finally:
                _pl.plan_question = real
            secs = round(time.perf_counter() - t0, 2)
            u = res.get("usage") or {}
            cost = compute_cost(model, u.get("prompt_tokens") or 0,
                                u.get("cached_tokens") or 0,
                                u.get("completion_tokens") or 0, rates, service_tier)
            spent += cost["usd_total"]
            # Rebuild the payload once (offline) and attribute BOTH answers against the
            # same thirds, so criterion (b)'s paired read -- Terra vs the 11 Nov baseline
            # -- sits in one file, with the directional share next to each answer.
            thirds = bucket_thirds(_build_payload(rec["plan"], rec["question"],
                                                  chart_facts)[1]["payload"])
            depth = depth_attribution(res.get("answer") or "", thirds)
            base_depth = depth_attribution(rec["answer_A_with_books"], thirds)
            base_model = rec["A_with_books"].get("model")
            rows.append({"n": n, "usage": u, "cost": cost, "secs": secs,
                         "depth": depth, "base_depth": base_depth})
            body += [f"## Q{n}. {rec['question']}",
                     f"- model/tier: {res.get('model')} / {u.get('service_tier_applied')}",
                     f"- prompt={u.get('prompt_tokens')} cached={u.get('cached_tokens')} "
                     f"completion={u.get('completion_tokens')} "
                     f"reasoning={u.get('reasoning_tokens')} secs={secs}",
                     f"- cost: ${cost['usd_total']} (tier={cost['tier']})  "
                     f"RUNNING TOTAL ${round(spent,4)}",
                     f"- depth middle_last_share: Terra={depth['middle_last_share']} "
                     f"(attr={depth['attributed_tokens']})  vs  {base_model}="
                     f"{base_depth['middle_last_share']} (attr={base_depth['attributed_tokens']})",
                     "", "### Terra answer", "", render_user_answer(res), "",
                     f"### Baseline answer ({base_model}, 11 Nov)", "",
                     rec["answer_A_with_books"] or "(not recovered from blind file)",
                     "", "---", ""]
            if spent > 8:
                body.append("STOP: live spend exceeded $8 cap.")
                break
    finally:
        _interp.INTERPRETER_MODEL, _interp.LARGE_PAYLOAD_MODEL = saved
    body.append(f"TOTAL SPENT this run: ${round(spent,4)}")
    _write_run("paid_run", body)
    print(f"[paid] spent ${round(spent,4)} across {len(rows)} Qs -- see latest_run.md")
    return 0


def _norm_model(m: Optional[str]) -> str:
    """Baseline model -> a rate-card key that actually PRICES. gpt-5 is being
    decommissioned and its card row is intentionally null (short/long both None), so
    a present-but-unusable row must still fall back to luna -- not only a missing one.
    The old_usd column for gpt-5 questions is therefore luna-approximate; it never
    feeds the Terra projection.
    """
    models = load_rates().get("models", {})
    blk = models.get(m or "")
    if blk and (blk.get("short") or blk.get("long") or blk.get("flat")):
        return m  # has a usable block
    return "gpt-5.6-luna"


def _write_run(tag: str, body: list[str]) -> None:
    os.makedirs(_RUNS, exist_ok=True)
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(_RUNS, f"{ts}_{tag}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(body) + "\n")
    shutil.copyfile(path, os.path.join(_ROOT, "diagnostics", "latest_run.md"))


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Terra cost + depth validation harness")
    ap.add_argument("--analyze-baseline", action="store_true",
                    help="OFFLINE: cost column + depth check on the 11 Nov data, $0")
    ap.add_argument("--run", action="store_true", help="PAID: force model on a subset")
    ap.add_argument("--model", default="gpt-6.1-terra")
    ap.add_argument("--service-tier", default="flex", choices=["flex", "standard"])
    ap.add_argument("--questions", default="1,4,5",
                    help="comma list of 11 Nov question numbers (default decisive 1,4,5)")
    ap.add_argument("--reasoning-effort", default="minimal")
    ap.add_argument("--confirm", action="store_true", help="actually spend on --run")
    a = ap.parse_args(argv)
    if a.analyze_baseline:
        return analyze_baseline()
    if a.run:
        ns = [int(x) for x in a.questions.split(",") if x.strip()]
        return run_paid(a.model, a.service_tier, ns, a.confirm, a.reasoning_effort)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
