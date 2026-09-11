"""
Planner tests. Three layers, no live LLM anywhere in CI.

  A. Structural validator -- shape only, hardest cases first.
  B. Retry / fallback / logging contract.
  C. Domain -> unit selection against the REAL domain_tags artifact.

The two live bugs the Planner exists to kill are pinned as named tests:
  - test_bug_cancer_sign_is_not_medical
  - test_bug_child_career_derives_2nd_house
Both are driven by a STUBBED planner response, so they assert the
PIPELINE handles a correct plan correctly. Whether the live LLM produces
that plan is a separate, live measurement (scripts/run_planner_poc.py),
never asserted in CI -- Stage-2 conftest-stub precedent, S50/S65.
"""
import json
import os

import pytest

from agent.astro import planner as P


def _ok_obj(**over):
    base = {
        "domains": ["career"],
        "houses": [10],
        "whose_chart": "self",
        "time_scope": "none",
        "in_scope": True,
        "reasoning": "10th house is the house of profession.",
    }
    base.update(over)
    return base


def stub(payload, *, raise_first=False):
    """Returns an llm callable emitting `payload` (str or list of str)."""
    seq = payload if isinstance(payload, list) else [payload]
    state = {"i": 0, "raised": False}

    def _call(question):
        if raise_first and not state["raised"]:
            state["raised"] = True
            raise RuntimeError("simulated transport failure")
        i = min(state["i"], len(seq) - 1)
        state["i"] += 1
        out = seq[i]
        return out if isinstance(out, str) else json.dumps(out)
    return _call


# --------------------------------------------------------------- LAYER A ----
def test_valid_object_normalises():
    fields, errs = P.validate_plan_object(_ok_obj(domains=["marriage", "career", "career"],
                                                  houses=[7, 2, 7]))
    assert errs == []
    # de-duped and put in canonical corpus order, not the LLM's order
    assert fields["domains"] == ["career", "marriage"]
    assert fields["houses"] == [2, 7]


@pytest.mark.parametrize("over,frag", [
    ({"domains": []}, "non-empty list"),
    ({"domains": ["job"]}, "closed vocabulary"),
    ({"domains": "career"}, "non-empty list"),
    ({"houses": [0]}, "outside 1-12"),
    ({"houses": [13]}, "outside 1-12"),
    ({"houses": ["10"]}, "outside 1-12"),
    ({"houses": [True]}, "outside 1-12"),          # bool is not a house
    ({"whose_chart": "child"}, "whose_chart"),
    ({"time_scope": "soon"}, "time_scope"),
    ({"in_scope": "yes"}, "must be a boolean"),    # truthy string is NOT true
    ({"reasoning": "   "}, "non-empty string"),
])
def test_structural_rejections(over, frag):
    fields, errs = P.validate_plan_object(_ok_obj(**over))
    assert fields is None
    assert any(frag in e for e in errs), errs


def test_validator_does_not_judge_doctrine():
    """A doctrinally odd but structurally legal plan MUST pass.

    Guards against someone re-adding a domain->house table here.
    """
    fields, errs = P.validate_plan_object(
        _ok_obj(domains=["marriage"], houses=[6]))
    assert errs == [] and fields["houses"] == [6]


def test_fences_and_prose_are_tolerated():
    fields, errs = P.parse_llm_plan("```json\n" + json.dumps(_ok_obj()) + "\n```")
    assert errs == [] and fields["domains"] == ["career"]


def test_non_json_is_rejected():
    fields, errs = P.parse_llm_plan("I think this is about career.")
    assert fields is None and "not valid JSON" in errs[0]


# --------------------------------------------------------------- LAYER B ----
def test_first_call_success(tmp_path):
    log = tmp_path / "d.jsonl"
    p = P.plan_question("career?", llm=stub(_ok_obj()), log_path=str(log))
    assert p.source == "llm" and p.planner_fallback is False
    assert json.loads(log.read_text(encoding="utf-8"))["source"] == "llm"


def test_retry_then_success(tmp_path):
    p = P.plan_question("career?", llm=stub(["garbage", _ok_obj()]),
                        log_path=str(tmp_path / "d.jsonl"))
    assert p.source == "llm_retry" and p.planner_fallback is False
    assert any("attempt 1" in e for e in p.validation_errors)


def test_two_failures_fall_back_and_are_stamped(tmp_path):
    p = P.plan_question("what about my career?", llm=stub("garbage"),
                        log_path=str(tmp_path / "d.jsonl"))
    assert p.planner_fallback is True and p.source == "fallback"
    assert "career" in p.domains
    assert p.houses == []          # fallback NEVER guesses houses


def test_transport_exception_is_survived(tmp_path):
    p = P.plan_question("career?", llm=stub(_ok_obj(), raise_first=True),
                        log_path=str(tmp_path / "d.jsonl"))
    assert p.source == "llm_retry"
    assert any("simulated transport failure" in e for e in p.validation_errors)


def test_fallback_with_no_keyword_refuses_rather_than_guessing(tmp_path):
    p = P.plan_question("zzzz qqqq", llm=stub("garbage"),
                        log_path=str(tmp_path / "d.jsonl"))
    assert p.planner_fallback is True
    assert p.domains == [] and p.in_scope is False


def test_fallback_never_silent_in_log(tmp_path):
    log = tmp_path / "d.jsonl"
    P.plan_question("my job?", llm=stub("garbage"), log_path=str(log))
    rec = json.loads(log.read_text(encoding="utf-8"))
    assert rec["planner_fallback"] is True
    assert rec["validation_errors"]        # never an empty explanation


def test_log_failure_does_not_kill_the_answer(tmp_path):
    bad = str(tmp_path / "nope") + "\x00/x.jsonl"
    p = P.plan_question("career?", llm=stub(_ok_obj()), log_path=bad)
    assert p.source == "llm"   # answered anyway


def test_empty_question_raises():
    with pytest.raises(P.PlannerError):
        P.plan_question("   ", llm=stub(_ok_obj()))


# --------------------------------------------------------------- LAYER C ----
def test_selection_against_real_artifact():
    p = P.plan_question("career?", llm=stub(_ok_obj()), log_path=None)
    sel = P.select_units(p)
    assert sel.unit_ids, "career must select at least one unit"
    assert len(set(sel.unit_ids)) == len(sel.unit_ids), "no duplicates"
    assert sel.approx_tokens == sum(sel.per_unit_tokens.values())


def test_selection_is_a_union_not_an_intersection():
    one = P.select_units(P.plan_question(
        "q", llm=stub(_ok_obj(domains=["siblings"])), log_path=None))
    two = P.select_units(P.plan_question(
        "q", llm=stub(_ok_obj(domains=["siblings", "travel"])), log_path=None))
    assert set(one.unit_ids).issubset(set(two.unit_ids))
    assert two.approx_tokens >= one.approx_tokens


def test_over_budget_reports_but_never_drops():
    p = P.plan_question("q", llm=stub(_ok_obj(domains=["career"])), log_path=None)
    tight = P.select_units(p, token_budget=1)
    loose = P.select_units(p, token_budget=10**9)
    assert tight.over_budget is True and loose.over_budget is False
    assert tight.unit_ids == loose.unit_ids      # budget is advisory ONLY


def test_empty_domains_select_nothing():
    p = P.Plan(question="q", domains=[], houses=[], whose_chart="self",
               time_scope="none", in_scope=False, reasoning="x")
    assert P.select_units(p).unit_ids == []


# ------------------------------------------------ THE TWO LIVE BUGS ---------
def test_bug_cancer_sign_is_not_medical():
    """S124 open item 6b: the substring guard refused any question naming
    'Cancer'. There is no substring guard now -- in_scope is the LLM's
    judgement and Python only checks it is a bool.
    """
    q = "My ascendant is Cancer. What does that say about my nature?"
    p = P.plan_question(q, llm=stub(_ok_obj(
        domains=["planetary_nature", "health"], houses=[1],
        reasoning="Cancer here names a sign, not a disease.")), log_path=None)
    assert p.in_scope is True
    assert P.select_units(p).unit_ids
    # and Python owns NO scope judgement: in_scope passes through the
    # validator untouched, and no keyword blocklist construct exists.
    fields, errs = P.validate_plan_object(_ok_obj(in_scope=False))
    assert errs == [] and fields["in_scope"] is False
    src = open(P.__file__, encoding="utf-8").read()
    for banned in ("_OUT_OF_SCOPE", "OUT_OF_SCOPE_KEYWORDS", "_MEDICAL"):
        assert banned not in src, f"substring scope guard reintroduced: {banned}"


def test_bug_child_career_derives_2nd_house():
    """S124 open item 6a: 'will my child succeed in his career' returned
    the USER's Shadbala. The plan must carry whose_chart='other' AND the
    derived house (10th from the 5th = 2nd), on the native's own chart.
    """
    q = "Will my child succeed in his career?"
    p = P.plan_question(q, llm=stub(_ok_obj(
        domains=["children", "career"], houses=[5, 2, 10],
        whose_chart="other", time_scope="future",
        reasoning="Child = 5th. His 10th = 10th from the 5th = the 2nd of "
                  "the native's chart. 10th kept as the base karma house.")),
        log_path=None)
    assert p.whose_chart == "other"
    assert 2 in p.houses, "derived bhavat-bhavam house missing"
    sel = P.select_units(p)
    assert set(sel.per_domain_units) == {"children", "career"}
    assert sel.unit_ids


# ------------------------------------------- LAYER D: segment filter --------
def _fake_payload():
    return {
        "units": [{"unit_id": "ch21", "tokens": 100}],
        "segments": [
            {"segment_id": "ch24_s001", "tokens": 10, "kept": True},
            {"segment_id": "ch24_s002", "tokens": 20, "kept": True},
            {"segment_id": "NOT_IN_TAGS_s999", "tokens": 5, "kept": True},
            {"segment_id": "ch24_s003", "tokens": 7, "kept": False},
        ],
    }


def _tags_stub(tmp_path, segments):
    p = tmp_path / "tags.json"
    p.write_text(json.dumps({"segments": segments, "units": [],
                             "domain_vocabulary": list(P.DOMAINS)}),
                 encoding="utf-8")
    P._TAGS_CACHE.pop(str(p), None)
    return str(p)


def _plan(domains):
    return P.Plan(question="q", domains=domains, houses=[], whose_chart="self",
                  time_scope="none", in_scope=True, reasoning="x")


def test_domain_filter_drops_only_positive_misses(tmp_path):
    tags = _tags_stub(tmp_path, [
        {"segment_id": "ch24_s001", "domains": ["career"], "unfittable": False},
        {"segment_id": "ch24_s002", "domains": ["marriage"], "unfittable": False},
    ])
    out = P.filter_segments_by_domain(_fake_payload(), _plan(["career"]),
                                      tags_path=tags)
    by = {s["segment_id"]: s for s in out["segments"]}
    assert by["ch24_s001"]["kept"] is True       # domain match
    assert by["ch24_s002"]["kept"] is False      # positive miss -> dropped
    assert by["NOT_IN_TAGS_s999"]["kept"] is True  # FAIL SAFE, unknown id
    assert by["ch24_s003"]["kept"] is False      # was already dropped upstream
    assert out["domain_filter"]["counts"]["dropped_domain_miss"] == 1
    assert out["domain_filter"]["counts"]["kept_failsafe_unknown_id"] == 1


def test_untagged_and_unfittable_are_kept_failsafe(tmp_path):
    tags = _tags_stub(tmp_path, [
        {"segment_id": "ch24_s001", "domains": [], "unfittable": False},
        {"segment_id": "ch24_s002", "domains": ["marriage"], "unfittable": True},
    ])
    out = P.filter_segments_by_domain(_fake_payload(), _plan(["career"]),
                                      tags_path=tags)
    assert all(s["kept"] for s in out["segments"]
               if s["segment_id"] in ("ch24_s001", "ch24_s002"))
    assert out["domain_filter"]["counts"]["kept_failsafe_untagged"] == 2


def test_domain_filter_never_mutates_input(tmp_path):
    tags = _tags_stub(tmp_path, [
        {"segment_id": "ch24_s002", "domains": ["marriage"], "unfittable": False}])
    src = _fake_payload()
    before = json.dumps(src, sort_keys=True)
    P.filter_segments_by_domain(src, _plan(["career"]), tags_path=tags)
    assert json.dumps(src, sort_keys=True) == before


def test_domain_filter_is_a_noop_with_no_domains(tmp_path):
    src = _fake_payload()
    assert P.filter_segments_by_domain(src, _plan([]),
                                       tags_path=_tags_stub(tmp_path, [])) is src


def test_every_drop_carries_a_reason(tmp_path):
    tags = _tags_stub(tmp_path, [
        {"segment_id": "ch24_s002", "domains": ["marriage"], "unfittable": False}])
    out = P.filter_segments_by_domain(_fake_payload(), _plan(["career"]),
                                      tags_path=tags)
    dropped = [s for s in out["segments"]
               if s.get("domain_filter") == "dropped_domain_miss"]
    assert dropped and all("domain_drop_reason" in s for s in dropped)


def test_payload_tokens_counts_units_and_kept_segments_only():
    assert P.payload_tokens(_fake_payload()) == 100 + 10 + 20 + 5


def test_out_of_scope_refuses_before_touching_the_corpus():
    obj = {"domains": ["health"], "houses": [6], "whose_chart": "self",
           "time_scope": "none", "in_scope": False, "reasoning": "medical"}
    res = P.plan_and_build("diagnose my rash", {"lord_house_map": {}},
                           llm=stub(obj), log_path=None)
    assert res["refused"] is True and res["payload"] is None


# ----------------------------------------- LAYER E: hard context ceiling ----
def test_ceiling_refuses_rather_than_truncating(monkeypatch):
    """Over the context ceiling the pipeline must REFUSE, and must NOT
    have dropped a single unit or segment on the way there."""
    monkeypatch.setattr(P, "HARD_CONTEXT_CEILING", 1)
    obj = _ok_obj(domains=["career"])
    chart = {"lord_house_map": {i: i for i in range(1, 13)},
             "ascendant_sign": "Sagittarius"}
    res = P.plan_and_build("career?", chart, llm=stub(obj), log_path=None)
    assert res["refused"] is True and res["exceeds_context"] is True
    assert "NOT truncated" in res["refusal_reason"]
    # the payload is still fully intact -- refusal is a gate, not a trim
    assert res["payload"] is not None and res["tokens"] > 1


def test_under_ceiling_does_not_refuse():
    obj = _ok_obj(domains=["travel"])
    chart = {"lord_house_map": {i: i for i in range(1, 13)},
             "ascendant_sign": "Sagittarius"}
    res = P.plan_and_build("travel?", chart, llm=stub(obj), log_path=None)
    assert res["refused"] is False and res["refusal_reason"] is None
    assert res["estimated_real_tokens"] > res["tokens"]


def test_ceiling_is_below_the_model_window():
    assert P.HARD_CONTEXT_CEILING * P.APPROX_TO_REAL_RATIO < P.INTERPRETER_CONTEXT_WINDOW
