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


# ── S157 C2b: breadth fan-out orchestration (wiring; primitives stubbed) ─────

def _stub_fanout_env(monkeypatch, *, tokens):
    """Canned plan/gate/build + stubbed C1/C2a primitives, so the test exercises
    ONLY pipeline's fan-out wiring. plan_question + capability_gate.assess are
    INJECTED (not the stub-LLM path) so _plan.domains is GUARANTEED to be two
    domains -- the real planner/gate have their own tests and must not silently
    narrow this one and mask the fan-out trigger (that masking was the C2b-RED
    root cause: the real planner reduced the plan below 2 domains, so fan-out
    never fired and the single call hit the conftest OpenAI stub)."""
    from types import SimpleNamespace
    _plan = pipeline.planner.Plan(question="q", domains=["career", "health"],
                                  houses=[], whose_chart="self", time_scope="none",
                                  in_scope=True, reasoning="broad")
    monkeypatch.setattr(pipeline.planner, "plan_question",
                        lambda q, llm=None, history=None: _plan)
    monkeypatch.setattr(pipeline.capability_gate, "assess",
                        lambda p: SimpleNamespace(
                            refuse_outright=False, plan=p, declined=[],
                            dropped_domains=[], gate_version="test", messages=[]))
    monkeypatch.setattr(pipeline.planner, "build_from_plan",
                        lambda plan, cf, **k: {
                            "plan": plan, "selection": None,
                            "payload": {"segments": [], "units": []},
                            "tokens": tokens, "over_budget": False, "refused": False})
    monkeypatch.setattr(pipeline.planner, "split_payload_by_domain",
                        lambda payload, plan, **k: {
                            "shared": {"segment_ids": [], "unit_ids": [], "tokens": 0},
                            "by_domain": {d: {"segment_ids": [], "unit_ids": [],
                                              "tokens": 0} for d in plan.domains},
                            "stats": {"shared_tokens": 0,
                                      "by_domain_tokens": {d: 0 for d in plan.domains}}})
    monkeypatch.setattr(pipeline.planner, "build_domain_subpayload",
                        lambda payload, shared, db, **k: {"segments": [], "units": []})
    monkeypatch.setattr(pipeline.planner, "payload_tokens", lambda p: 0)
    monkeypatch.setattr(pipeline, "_fact_block", lambda cf: "FACTS")
    monkeypatch.setattr(pipeline.timing_ranker, "build_timing_ranking",
                        lambda *a, **k: [])
    monkeypatch.setattr(pipeline.timing_ranker, "render_ranking", lambda *a, **k: "")
    monkeypatch.setattr(pipeline.house_roles, "weighted_targets", lambda *a, **k: {})


def test_fanout_fires_over_ceiling_and_stitches_bottom_line_plus_sections(monkeypatch):
    _stub_fanout_env(monkeypatch, tokens=999_999)  # >> 0.9 * ceiling -> fan out
    seen = []
    monkeypatch.setattr(pipeline._interp, "interpret_domain_partial",
                        lambda q, fb, sub, d, **k: (
                            seen.append(("partial", d)) or
                            {"domain": d, "answer": f"[{d}] section.",
                             "usage": {"prompt_tokens": 5}, "model": "gpt-5"}))
    monkeypatch.setattr(pipeline._interp, "synthesize_partials",
                        lambda q, parts, **k: (
                            seen.append(("synth", [p["domain"] for p in parts])) or
                            {"answer": "BOTTOM LINE.", "usage": {"prompt_tokens": 3},
                             "model": "gpt-5"}))
    res = pipeline.answer_question("How will my life go?", {"lord_house_map": {}},
                                   expert=True)
    assert res["expert_mode"] is True and res["refused"] is False
    fo = res["trace"]["fanout"]
    assert fo["triggered"] and fo["domains"] == ["career", "health"]
    assert [p["domain"] for p in fo["partials"]] == ["career", "health"]
    # bottom line leads, then the verbatim grounded sections
    assert res["answer"].startswith("BOTTOM LINE.")
    assert "[career] section." in res["answer"] and "[health] section." in res["answer"]
    # one partial per domain, then one synthesis over both
    assert seen == [("partial", "career"), ("partial", "health"),
                    ("synth", ["career", "health"])]
    # usage is summed across the sub-calls (5 + 5 + 3)
    assert res["usage"]["prompt_tokens"] == 13


def test_no_fanout_under_threshold_uses_single_call(monkeypatch):
    _stub_fanout_env(monkeypatch, tokens=1_000)  # << 0.9 * ceiling -> single call
    monkeypatch.setattr(pipeline._interp, "interpret_expert",
                        lambda q, fb, pl, **k: {"answer": "single-call answer",
                                                "usage": {}, "model": "gpt-5"})
    boom = lambda *a, **k: (_ for _ in ()).throw(
        AssertionError("fan-out must not fire under the threshold"))
    monkeypatch.setattr(pipeline._interp, "interpret_domain_partial", boom)
    res = pipeline.answer_question("narrow question", {"lord_house_map": {}},
                                   expert=True)
    assert res["answer"] == "single-call answer"
    assert "fanout" not in res["trace"]


def test_fanout_failure_falls_back_to_single_call(monkeypatch):
    _stub_fanout_env(monkeypatch, tokens=999_999)  # would fan out...
    monkeypatch.setattr(pipeline.planner, "split_payload_by_domain",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    monkeypatch.setattr(pipeline._interp, "interpret_expert",
                        lambda q, fb, pl, **k: {"answer": "fell back to single",
                                                "usage": {}, "model": "gpt-5"})
    res = pipeline.answer_question("How will my life go?", {"lord_house_map": {}},
                                   expert=True)
    # accelerant-never-a-gate: a fan-out error never costs the answer
    assert res["answer"] == "fell back to single"
    assert "fanout" not in res["trace"]
