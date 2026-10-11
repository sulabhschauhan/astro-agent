"""Pipeline dispatch tests (S150 step 3 -- the computed-only route).

A computed-only plan (capabilities set, NO corpus domain) must be answered from
its computed fact classes alone: build_from_plan is skipped (no corpus to
retrieve, no no-domains refusal) and the answer is rendered in expert mode (no
verses to cite).

SCOPE: these tests cover the DISPATCH DECISION only. They monkeypatch
build_from_plan to RAISE (so a computed-only turn that ever reached corpus
retrieval fails loudly), and stub `_fact_block` (fact-block assembly has its own
tests and needs a full 12-house lord map the dispatch decision does not care
about -- the real pipeline always hands it a complete static block). Both LLMs
are stubbed; no OpenAI call.
"""
from __future__ import annotations

import json

import pytest

from agent.astro import pipeline


_LUCKY_PLAN = {
    "domains": [],
    "houses": [],
    "whose_chart": "self",
    "time_scope": "none",
    "in_scope": True,
    "capabilities": ["lucky_days"],
    "muhurta": False,
    "muhurta_horizon": None,
    "reasoning": "Asks for the lucky weekday -- a computed capability, no corpus.",
}

# Thin on purpose: the dispatch decision reads plan.capabilities / plan.domains,
# not the chart. _fact_block is stubbed in the fixture, so this never has to be a
# complete chart.
_CHART_FACTS = {"lucky_unlucky": {"favourable_days": [{"day": "Thursday"}]}}

_CANNED_FACT_BLOCK = "Lucky weekdays: Thursday favourable; Friday to be avoided."


def _planner_llm(_prompt):
    # plan_question calls the planner llm with one positional arg, parses JSON.
    return json.dumps(_LUCKY_PLAN)


def _interp_llm(_system, _user, *, model=None, reasoning_effort=None):
    # interpret_expert calls (system, user, model=, reasoning_effort=) -> (content, usage).
    # Prove the fact block reached the interpreter.
    assert "Thursday" in _user
    return ("Thursday is your most favourable day; avoid Friday.",
            {"prompt_tokens": 10, "completion_tokens": 8})


def _boom(*_a, **_k):
    raise AssertionError("build_from_plan must NOT run for a computed-only plan")


@pytest.fixture
def _dispatch_env(monkeypatch):
    # build_from_plan must never be reached on the computed-only route.
    monkeypatch.setattr(pipeline.planner, "build_from_plan", _boom)
    # Scope the test to dispatch: stub fact-block assembly (own tests elsewhere)
    # and isolate the timing ranker / house roles, which expect a full static
    # fact block the computed-only route does not depend on.
    monkeypatch.setattr(pipeline, "_fact_block", lambda cf: _CANNED_FACT_BLOCK)
    monkeypatch.setattr(pipeline.timing_ranker, "build_timing_ranking",
                        lambda *a, **k: [])
    monkeypatch.setattr(pipeline.timing_ranker, "render_ranking",
                        lambda *a, **k: "")
    monkeypatch.setattr(pipeline.house_roles, "weighted_targets",
                        lambda *a, **k: {})
    return monkeypatch


def test_computed_only_plan_answers_without_corpus(_dispatch_env):
    result = pipeline.answer_question(
        "which is my luckiest day of the week?",
        _CHART_FACTS,
        llm=_planner_llm,
        interpreter_llm=_interp_llm,
    )
    assert result["refused"] is False
    assert result["expert_mode"] is True
    assert "Thursday" in result["answer"]


def test_computed_only_forces_expert_even_when_expert_false(_dispatch_env):
    # A caller (or ASTRO_EXPERT_MODE=0) asking for the cited-claim path must be
    # overridden for a computed-only plan -- there are no verses to cite.
    result = pipeline.answer_question(
        "what days should I avoid?",
        _CHART_FACTS,
        llm=_planner_llm,
        interpreter_llm=_interp_llm,
        expert=False,
    )
    assert result["expert_mode"] is True
    assert result["refused"] is False
