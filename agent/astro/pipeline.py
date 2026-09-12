"""

================================================================
PATH B / LAB TRACK -- NOT WIRED TO THE PRODUCT (S128 lock).

This module has NO non-test caller. The live answer path is
agent/infra/orchestrator.answer_question, imported by
frontend/app.py:31. Changing this file ships NOTHING to users.
Read docs/ANSWER_PATHS.md before editing or proposing work here.
================================================================

Astro Agent -- FULL ANSWER PIPELINE.

  question -> plan (Stage 1) -> unit+domain selection (Stage 2)
           -> payload build (Stage 3) -> Interpreter/GPT-5 (Stage 4)
           -> Silence gate (Stage 5a) -> answer.

The Calculator (Stage 3.5) supplies the FACT BLOCK the Interpreter reads.
Today that block is the chart's lord->house map + ascendant; when the
`chart_d1` / `vimshottari` stubs land it widens automatically and the gate's
coverage grows with it (S125 lock). The LLM never computes a chart fact.

Dependency-injected `llm` (planner) and `interpreter_llm` (interpreter) so the
whole chain is testable with stubs and never calls the API in CI.
Python 3.11.
"""
from __future__ import annotations

import time
from typing import Callable, Optional

from agent.astro import planner
from agent.astro import capability_gate
from agent.astro import interpreter as _interp
from agent.astro import silence_gate
from agent.astro import payload_builder

PIPELINE_VERSION = "pipeline-1.2"


def _fact_block(chart_facts: dict) -> str:
    """Render the chart facts the Interpreter is allowed to reason from.

    GROWTH CONTRACT: every class of fact rendered here MUST have a matching key
    in `capability_gate.FACT_BLOCK_PROVIDES`, added in the SAME change.
    `tests/astro/test_capability_gate.py` pins the two together and fails if
    they drift -- that pin is what stops the gate declining a question the
    block can now answer, or the reverse.
    """
    lord_house, asc = payload_builder.parse_lord_house_map(chart_facts)
    lines = ["CHART FACTS (the only chart facts you may use):",
             f"Ascendant sign: {asc}"]
    lines += [f"House {h}: its lord sits in house {lord_house[h]}" for h in range(1, 13)]

    # Planet positions (S129). Rendered in the classical Navagraha order that
    # chart_facts fixes, so the block is byte-stable across runs. Absent for a
    # chart_facts dict built from `fact_block_text` -- that legacy shape has no
    # planet data, and its absence is honest, not an error.
    positions = chart_facts.get("planet_positions") or {}
    if positions:
        lines.append("")
        for planet, pos in positions.items():
            lines.append(f"{planet} is in house {pos['house']} ({pos['sign']}).")
    return "\n".join(lines)


def _render(kept: list[dict], silent_on: list[str],
            declined_messages: list[str] | None = None) -> str:
    """Assemble the user-facing answer.

    `declined_messages` are the capability gate's plain-language notes about
    what could NOT be answered. They are appended, never interleaved, so the
    user always sees the limit alongside the answer rather than instead of it.
    """
    declined_messages = declined_messages or []
    if not kept:
        msg = "I can't answer this from the classical text and chart facts available."
        parts = [msg]
        if silent_on:
            parts.append("\n".join(f"- {s}" for s in silent_on))
        parts += declined_messages
        return "\n\n".join(parts)
    out = []
    for c in kept:
        cites = " ".join(f"[{i}]" for i in c.get("segment_ids", []))
        out.append(f"- {c['statement']} {cites}".rstrip())
    if silent_on:
        out.append("\nNot addressed: " + "; ".join(silent_on))
    body = "\n".join(out)
    if declined_messages:
        body += "\n\n" + "\n\n".join(declined_messages)
    return body


def answer_question(
    question: str,
    chart_facts: dict,
    *,
    llm: Optional[Callable] = None,
    interpreter_llm: Optional[Callable] = None,
    token_budget: int = planner.DEFAULT_TOKEN_BUDGET,
) -> dict:
    """End-to-end. Never raises for a model/gate problem -- refuses or fails
    open with the reason on the record.

    Stage 1.5 (`capability_gate.assess`) sits between planning and retrieval:
    it narrows the plan to what the fact block can actually support, so a
    question needing facts we do not have is declined in Python rather than
    handed to the Interpreter to guess at. See capability_gate's docstring.
    """
    # Per-stage wall clock. Cheap, always on: the capture needs it and a slow
    # stage is the first thing anyone asks about after a live run.
    _t = time.perf_counter()
    timings: dict[str, float] = {}

    def _lap(stage: str) -> None:
        nonlocal _t
        now = time.perf_counter()
        timings[stage] = round(now - _t, 3)
        _t = now

    plan = planner.plan_question(question, llm=llm)
    _lap("plan")
    verdict = capability_gate.assess(plan)
    _lap("capability_gate")

    if verdict.refuse_outright:
        return {"answer": "\n\n".join(verdict.messages),
                "refused": True,
                "reason": "capability_gate: " + ", ".join(i for i, _ in verdict.declined),
                "plan": plan,
                "declined": verdict.declined,
                "dropped_domains": verdict.dropped_domains,
                "capability_gate_version": verdict.gate_version,
                "trace": {"timings": timings, "payload": {},
                          "plan_before_gate": {"domains": list(plan.domains or []),
                                               "time_scope": plan.time_scope},
                          "gate_refused_outright": True,
                          "refused_at": "capability_gate"},
                "pipeline_version": PIPELINE_VERSION}

    built = planner.build_from_plan(verdict.plan, chart_facts, token_budget=token_budget)
    _lap("select_and_build_payload")
    if built.get("refused"):
        return {"answer": f"(no answer) {built.get('refusal_reason', 'refused')}",
                "refused": True, "reason": built.get("refusal_reason"),
                "plan": built["plan"],
                "declined": verdict.declined,
                "capability_gate_version": verdict.gate_version,
                "trace": {"timings": timings, "payload": built.get("payload") or {},
                          "refused_at": "payload_ceiling"},
                "pipeline_version": PIPELINE_VERSION}

    fact_block = _fact_block(chart_facts)
    interp = _interp.interpret(question, fact_block, built["payload"], llm=interpreter_llm)
    _lap("interpreter")
    gate = silence_gate.apply_silence_gate(interp, built["payload"], chart_facts)
    _lap("silence_gate")

    selection = built.get("selection")
    trace = {
        "timings": timings,
        # The plan the PLANNER produced, before the capability gate narrowed it.
        # `result["plan"]` is the post-gate plan; without this the gate's effect
        # is invisible and a reader mistakes the narrowed plan for Stage 1's own
        # output (observed on the first live capture, S129).
        "plan_before_gate": {"domains": list(plan.domains or []),
                             "houses": list(plan.houses or []),
                             "time_scope": plan.time_scope,
                             "whose_chart": plan.whose_chart,
                             "in_scope": plan.in_scope,
                             "source": plan.source},
        "gate_refused_outright": verdict.refuse_outright,
        "payload": built["payload"],          # carries the full verse text
        "fact_block": fact_block,
        "unit_ids": getattr(selection, "unit_ids", None),
        "per_domain_units": getattr(selection, "per_domain_units", None),
        "corpus_fraction": getattr(selection, "corpus_fraction", None),
        "estimated_real_tokens": built.get("estimated_real_tokens"),
        "over_budget": built.get("over_budget"),
        "tpm_note": built.get("tpm_note"),
        "interpreter_refused": interp.get("refused"),
        "interpreter_raw": interp.get("raw"),
        "gate_error": gate.error,
    }

    return {
        "trace": trace,
        "answer": _render(gate.kept_claims, gate.silent_on, verdict.messages),
        "refused": interp["refused"] and not gate.kept_claims,
        "plan": built["plan"],
        "declined": verdict.declined,
        "dropped_domains": verdict.dropped_domains,
        "capability_gate_version": verdict.gate_version,
        "kept_claims": gate.kept_claims,
        "dropped_claims": gate.dropped_claims,       # precondition-false, removed by the gate
        "silent_on": gate.silent_on,
        "ghost_citations": interp["ghost_citations"],  # must be []
        "gate_stats": gate.stats,
        "usage": interp["usage"],
        "tokens": built["tokens"],
        "model": interp["model"],
        "pipeline_version": PIPELINE_VERSION,
    }
