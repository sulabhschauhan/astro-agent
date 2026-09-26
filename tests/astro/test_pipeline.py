"""End-to-end: plan -> select -> build -> interpret(stub) -> silence gate -> answer. Uses real data files + stub llm."""
import json
from agent.astro import pipeline, payload_builder as pb

def test_gate_drops_precondition_false_keeps_true_and_strips_ghost():
    chart = pb._load_real_chart_facts()
    lh, _ = pb.parse_lord_house_map(chart)
    assert lh[9] == 4 and lh[12] != 4     # fixture assumptions for this chart
    def stub(system, user, *, model, reasoning_effort):
        return json.dumps({"claims": [
            {"statement": "With the 9th lord in the 4th, houses and wealth.", "segment_ids": ["ch24_s082"]},
            {"statement": "With the 12th lord in the 4th, loss of houses.", "segment_ids": ["ch24_s111"]},
            {"statement": "Ghost.", "segment_ids": ["ch99_s999"]},
        ], "silent_on": [], "refused": False}), {"prompt_tokens": 1, "completion_tokens": 1, "reasoning_tokens": 0}
    res = pipeline.answer_question("Will I own my own house?", chart, interpreter_llm=stub)
    assert res["ghost_citations"] == ["ch99_s999"]
    assert [c["segment_ids"] for c in res["kept_claims"]] == [["ch24_s082"]]
    assert [c["segment_ids"] for c in res["dropped_claims"]] == [["ch24_s111"]]
    assert "ch24_s082" in res["answer"] and "ch24_s111" not in res["answer"]

def test_out_of_scope_refuses_without_interpreter_call():
    chart = pb._load_real_chart_facts()
    def boom(*a, **k): raise AssertionError("interpreter must not be called on refusal")
    # force an out-of-scope plan via a stub planner llm returning in_scope False
    def plan_llm(q):
        return json.dumps({"domains": [], "houses": [], "whose_chart": "self",
                           "time_scope": "none", "in_scope": False, "reasoning": "medical"})
    res = pipeline.answer_question("what medicine for fever?", chart, llm=plan_llm, interpreter_llm=boom)
    assert res["refused"] is True


def test_expert_mode_off_by_default_uses_claim_path():
    """Default (no expert flag, no env) is the unchanged cited-claim path."""
    chart = pb._load_real_chart_facts()
    def stub(system, user, *, model, reasoning_effort):
        return json.dumps({"claims": [
            {"statement": "With the 9th lord in the 4th, gains.", "segment_ids": ["ch24_s082"]}],
            "silent_on": [], "refused": False}), {"prompt_tokens": 1, "completion_tokens": 1, "reasoning_tokens": 0}
    res = pipeline.answer_question("Will I own my own house?", chart, interpreter_llm=stub)
    assert not res.get("expert_mode")
    assert "kept_claims" in res


def test_expert_mode_returns_free_text_and_view_passes_it_through():
    """expert=True: the interpreter writes the finished answer; no claim gate runs,
    and answer_view shows it verbatim with NO citation source line."""
    from agent.astro import answer_view
    chart = pb._load_real_chart_facts()
    captured = {}
    def expert_stub(system, user, *, model, reasoning_effort):
        captured["system"] = system; captured["user"] = user
        return ("You are very likely to marry during your Mercury period.",
                {"prompt_tokens": 1, "completion_tokens": 1})
    res = pipeline.answer_question("When will I get married?", chart,
                                   expert=True, interpreter_llm=expert_stub)
    # the expert prompt got the facts + the question
    assert "expert Vedic astrologer" in captured["system"]
    assert "CHART FACTS" in captured["user"] and "QUESTION:" in captured["user"]
    # result shape: expert answer, no claim machinery
    assert res["expert_mode"] is True
    assert res["kept_claims"] == [] and res["dropped_claims"] == []
    assert res["ghost_citations"] == [] and res["composed"] is None
    assert "Mercury period" in res["answer"]
    # answer_view passes it through, citation-free
    shown = answer_view.render_user_answer(res)
    assert shown == "You are very likely to marry during your Mercury period."
    assert "*Source" not in shown and "[" not in shown
