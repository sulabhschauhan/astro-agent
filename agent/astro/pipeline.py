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

from typing import Callable, Optional

from agent.astro import planner
from agent.astro import interpreter as _interp
from agent.astro import silence_gate
from agent.astro import payload_builder

PIPELINE_VERSION = "pipeline-1.0"


def _fact_block(chart_facts: dict) -> str:
    lord_house, asc = payload_builder.parse_lord_house_map(chart_facts)
    lines = ["CHART FACTS (the only chart facts you may use):",
             f"Ascendant sign: {asc}"]
    lines += [f"House {h}: its lord sits in house {lord_house[h]}" for h in range(1, 13)]
    return "\n".join(lines)


def _render(kept: list[dict], silent_on: list[str]) -> str:
    if not kept:
        msg = "I can't answer this from the classical text and chart facts available."
        return msg + ("\n\n" + "\n".join(f"- {s}" for s in silent_on) if silent_on else "")
    out = []
    for c in kept:
        cites = " ".join(f"[{i}]" for i in c.get("segment_ids", []))
        out.append(f"- {c['statement']} {cites}".rstrip())
    if silent_on:
        out.append("\nNot addressed: " + "; ".join(silent_on))
    return "\n".join(out)


def answer_question(
    question: str,
    chart_facts: dict,
    *,
    llm: Optional[Callable] = None,
    interpreter_llm: Optional[Callable] = None,
    token_budget: int = planner.DEFAULT_TOKEN_BUDGET,
) -> dict:
    """End-to-end. Never raises for a model/gate problem -- refuses or fails
    open with the reason on the record."""
    built = planner.plan_and_build(question, chart_facts, llm=llm, token_budget=token_budget)
    if built.get("refused"):
        return {"answer": f"(no answer) {built.get('refusal_reason', 'refused')}",
                "refused": True, "reason": built.get("refusal_reason"),
                "plan": built["plan"], "pipeline_version": PIPELINE_VERSION}

    fact_block = _fact_block(chart_facts)
    interp = _interp.interpret(question, fact_block, built["payload"], llm=interpreter_llm)
    gate = silence_gate.apply_silence_gate(interp, built["payload"], chart_facts)

    return {
        "answer": _render(gate.kept_claims, gate.silent_on),
        "refused": interp["refused"] and not gate.kept_claims,
        "plan": built["plan"],
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
