"""Tests for S147 conversation context: the render_history leaf + the planner
and interpreter threading it. No live LLM (both stubs capture their input)."""
from __future__ import annotations

import json

from agent.astro import conversation as C
from agent.astro import planner as P
from agent.astro import interpreter as I


# ------------------------------------------------- render_history (pure) ----
def test_empty_and_whitespace_render_to_nothing():
    assert C.render_history(None) == ""
    assert C.render_history([]) == ""
    assert C.render_history([{"role": "user", "content": "   "}]) == ""


def test_renders_labelled_block_most_recent_last():
    out = C.render_history([
        {"role": "user", "content": "auspicious dates to move house"},
        {"role": "assistant", "content": "Best: Oct 6-7..."},
        {"role": "user", "content": "okay any date after 24th over weekend"},
    ])
    assert out.startswith("RECENT CONVERSATION")
    assert "- You: auspicious dates to move house" in out
    assert "- Astrologer: Best: Oct 6-7..." in out
    assert out.strip().endswith("okay any date after 24th over weekend")


def test_caps_to_last_n_messages():
    out = C.render_history([{"role": "user", "content": f"q{i}"} for i in range(8)])
    assert "q0" not in out and "q1" not in out and "q2" in out and "q7" in out


def test_truncates_long_messages():
    out = C.render_history([{"role": "user", "content": "x" * 1000}], max_chars=50)
    assert out.count("x") == 50 and out.rstrip().endswith("...")


def test_collapses_whitespace():
    out = C.render_history([{"role": "assistant", "content": "line1\nline2\n\nline3"}])
    assert "line1 line2 line3" in out


# ------------------------------------------------- planner threading --------
_PLAN_JSON = json.dumps({
    "domains": ["property"], "houses": [4], "whose_chart": "self",
    "time_scope": "none", "in_scope": True, "muhurta": True,
    "muhurta_horizon": {"mode": "count", "value": 3},
    "reasoning": "auspicious dates to move house -> property, 4th house",
})


def test_planner_feeds_history_into_the_llm_input():
    seen = {}

    def stub(arg):
        seen["arg"] = arg
        return _PLAN_JSON

    P.plan_question("okay any date after the 24th", llm=stub, log_path=None,
                    history=[{"role": "user", "content": "auspicious dates to move house"}])
    assert "RECENT CONVERSATION" in seen["arg"]
    assert "move house" in seen["arg"]
    assert "CURRENT QUESTION" in seen["arg"] and "after the 24th" in seen["arg"]


def test_planner_no_history_is_byte_identical_single_shot():
    seen = {}

    def stub(arg):
        seen["arg"] = arg
        return _PLAN_JSON

    P.plan_question("career?", llm=stub, log_path=None)
    assert seen["arg"] == "career?"          # unchanged when there is no thread


# ------------------------------------------------- interpreter threading ----
def _istub(seen):
    def stub(system, user, **kw):
        seen["user"] = user
        return ("ok", {})
    return stub


def test_interpreter_feeds_history_into_user_prompt():
    seen = {}
    I.interpret_expert("what about after the 24th", "FACTS", {},
                       llm=_istub(seen),
                       history=[{"role": "user", "content": "move house dates"}])
    assert "RECENT CONVERSATION" in seen["user"] and "move house dates" in seen["user"]
    assert "CHART FACTS" in seen["user"] and "after the 24th" in seen["user"]


def test_interpreter_no_history_omits_the_block():
    seen = {}
    I.interpret_expert("q", "FACTS", {}, llm=_istub(seen))
    assert "RECENT CONVERSATION" not in seen["user"]
    assert "CHART FACTS" in seen["user"]
