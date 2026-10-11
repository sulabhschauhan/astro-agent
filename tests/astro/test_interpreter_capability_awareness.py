"""Interpreter capability-awareness tests (S150 step 4).

The expert interpreter is given the capability manifest (what it can compute for
this chart + input state) and the per-capability answering directives, and the
EXPERT_SYSTEM prompt carries the standing rules: answer on-map only, decline
off-map ("I don't compute that yet"), never upsell, one clarifying question max.
These tests stub the LLM and assert what reaches the prompt -- no OpenAI call.
"""
from __future__ import annotations

from agent.astro import interpreter as I
from agent.astro import capability_registry as cr


def _capturing_stub():
    captured = {}

    def stub(system, user, *, model=None, reasoning_effort=None):
        captured["system"] = system
        captured["user"] = user
        return ("Thursday is your luckiest day.",
                {"prompt_tokens": 1, "completion_tokens": 1})

    return stub, captured


def test_manifest_and_directives_reach_the_user_prompt():
    stub, captured = _capturing_stub()
    manifest = cr.interpreter_manifest(available_fact_keys={"lucky_unlucky"})
    directives = cr.directives_for(["lucky_days"])
    I.interpret_expert(
        "which is my luckiest day?",
        "Lucky weekdays: Thursday favourable.",
        {},
        llm=stub,
        capability_manifest=manifest,
        capability_directives=directives,
    )
    user = captured["user"]
    assert "WHAT YOU CAN COMPUTE FOR THIS CHART" in user
    assert "Lucky & unlucky weekdays: available." in user
    assert "HOW TO ANSWER THE COMPUTED PART" in user
    assert "favourable_days" in user  # the lucky_days directive text


def test_absent_manifest_leaves_the_corpus_prompt_unchanged():
    # A corpus turn passes no manifest/directives; the prompt must not grow the
    # capability blocks (byte-shape identical to pre-S150 for that path).
    stub, captured = _capturing_stub()
    I.interpret_expert("what about marriage?", "CHART FACTS...", {}, llm=stub)
    user = captured["user"]
    assert "WHAT YOU CAN COMPUTE FOR THIS CHART" not in user
    assert "HOW TO ANSWER THE COMPUTED PART" not in user


def test_expert_system_carries_capability_awareness_rules():
    sp = I.EXPERT_SYSTEM
    assert "WHAT YOU CAN COMPUTE" in sp                 # the map is named
    assert "do not compute that yet" in sp              # honest decline
    assert "No upselling" in sp                         # no unrequested offers
    assert "at most ONE such question" in sp            # bounded clarification


def test_interpret_expert_still_returns_the_answer_shape():
    stub, _ = _capturing_stub()
    out = I.interpret_expert("q", "FB", {}, llm=stub,
                             capability_manifest="", capability_directives=None)
    assert out["answer"] == "Thursday is your luckiest day."
    assert out["expert_mode"] is True
