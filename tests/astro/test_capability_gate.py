"""Tests for agent/astro/capability_gate.py -- the Stage 1.5 honest-refusal gate.

HARDEST CASE FIRST: the tests that matter are the mixed-domain ones, where a
question is partly answerable and partly not. Pure "when will I marry" is easy;
"what does my chart say about marriage and when will it happen" is the case
that decides whether the product is honest or fabricates.
"""
from __future__ import annotations

import pytest

from agent.astro import capability_gate as CG
from agent.astro.planner import Plan


def _plan(domains, time_scope="none", in_scope=True):
    return Plan(
        question="q", domains=list(domains), houses=[1],
        whose_chart="self", time_scope=time_scope,
        in_scope=in_scope, reasoning="r",
    )


# ── the declaration must match reality ─────────────────────────────────────

def test_fact_block_provides_matches_what_pipeline_actually_renders():
    """FACT_BLOCK_PROVIDES is a promise about pipeline._fact_block. If the two
    drift, the gate stops protecting anything -- so pin them together."""
    from agent.astro import pipeline
    facts = {"lord_house_map": {h: 1 for h in range(1, 13)},
             "ascendant_sign": "Leo"}
    block = pipeline._fact_block(facts)

    assert "Ascendant sign:" in block, "ascendant_sign capability claimed but not rendered"
    assert block.count("its lord sits in house") == 12, \
        "lord_house_map capability claimed but 12 placements not rendered"
    # planet_positions: claimed since S129, so the block must render them when
    # the facts carry them -- and must NOT invent a line when they are absent.
    assert "is in house" not in block, "no planet facts supplied, yet planets rendered"
    with_planets = pipeline._fact_block(dict(facts, planet_positions={
        "Sun": {"house": 4, "sign": "Pisces"}, "Ketu": {"house": 9, "sign": "Leo"}}))
    assert "Sun is in house 4 (Pisces)." in with_planets
    assert "Ketu is in house 9 (Leo)." in with_planets
    # Nothing else is in the block. If a future edit adds dasha lines here,
    # this assertion fires and the author must add the capability key too.
    assert "dasha" not in block.lower(), (
        "the fact block now mentions dasha -- add the matching key to "
        "FACT_BLOCK_PROVIDES in the same change, or the gate will keep "
        "declining questions it could now answer"
    )
    assert CG.FACT_BLOCK_PROVIDES == frozenset(
        {"ascendant_sign", "lord_house_map", "planet_positions"})


def test_every_requirement_names_a_capability_the_block_does_not_yet_have():
    for req in CG.REQUIREMENTS:
        assert req.needs not in CG.FACT_BLOCK_PROVIDES, (
            f"requirement {req.id} guards {req.needs!r}, which the fact block "
            "already provides -- it can never fire; delete it or fix the key"
        )
        assert req.domains or req.time_scopes, f"{req.id} can never trigger"
        assert req.user_message.strip(), f"{req.id} has no user message"


# ── the answerable case: gate must stay out of the way ─────────────────────

@pytest.mark.parametrize("domains", [
    ["career"], ["marriage"], ["health", "longevity"],
    ["wealth", "property", "children"], ["planetary_nature"],
])
def test_non_timing_questions_pass_through_untouched(domains):
    plan = _plan(domains)
    v = CG.assess(plan)
    assert v.refuse_outright is False
    assert v.declined == []
    assert v.dropped_domains == []
    assert v.plan is plan, "an unaffected plan must be passed through, not copied"


# ── the hard cases: mixed answerable / unanswerable ────────────────────────

def test_marriage_plus_timing_answers_marriage_and_declines_the_timing():
    """'What does my chart say about marriage, and when?' -- the honest middle."""
    plan = _plan(["marriage", "timing_dasha"], time_scope="future")
    v = CG.assess(plan)

    assert v.refuse_outright is False
    assert v.dropped_domains == ["timing_dasha"]
    assert v.plan.domains == ["marriage"]
    assert len(v.messages) == 1
    assert "when" in v.messages[0].lower()
    # the original plan is untouched -- the decision log must stay truthful
    assert plan.domains == ["marriage", "timing_dasha"]


def test_timing_only_question_refuses_outright():
    """'When will I marry?' planned as timing alone -- nothing left to answer."""
    plan = _plan(["timing_dasha"], time_scope="future")
    v = CG.assess(plan)

    assert v.refuse_outright is True
    assert v.dropped_domains == ["timing_dasha"]
    assert v.plan.domains == []
    assert len(v.messages) == 1


def test_future_time_scope_alone_triggers_even_without_the_timing_domain():
    """'How will my career go next year?' may plan only `career` -- but it is
    still asking for a date, and we have no dates."""
    plan = _plan(["career"], time_scope="future")
    v = CG.assess(plan)

    assert v.declined, "a future-scoped question must be told we cannot date it"
    # career itself survives -- the doctrine is still answerable
    assert v.refuse_outright is False
    assert v.plan.domains == ["career"]
    assert v.dropped_domains == []


def test_specific_period_time_scope_also_triggers():
    v = CG.assess(_plan(["wealth"], time_scope="specific_period"))
    assert v.declined
    assert v.refuse_outright is False


@pytest.mark.parametrize("scope", ["none", "past", "present"])
def test_non_forward_time_scopes_do_not_trigger(scope):
    v = CG.assess(_plan(["career"], time_scope=scope))
    assert v.declined == []
    assert v.refuse_outright is False


# ── growth path: a widened fact block silences the gate automatically ──────

def test_widened_fact_block_makes_the_timing_requirement_inert():
    """When vimshottari lands and the block carries dasha_periods, the same
    question must sail through with NO code change beyond the capability key."""
    widened = CG.FACT_BLOCK_PROVIDES | {"dasha_periods"}
    plan = _plan(["marriage", "timing_dasha"], time_scope="future")

    v = CG.assess(plan, provides=widened)

    assert v.declined == []
    assert v.refuse_outright is False
    assert v.plan is plan
    assert v.plan.domains == ["marriage", "timing_dasha"]


# ── structural guards ──────────────────────────────────────────────────────

def test_empty_domains_with_forward_scope_refuses_rather_than_proceeding():
    v = CG.assess(_plan([], time_scope="future"))
    assert v.refuse_outright is True


def test_non_plan_input_raises_loudly():
    with pytest.raises(TypeError, match="planner.Plan"):
        CG.assess({"domains": ["career"], "time_scope": "none"})


def test_verdict_carries_gate_version():
    v = CG.assess(_plan(["career"]))
    assert v.gate_version == CG.CAPABILITY_GATE_VERSION


def test_requirement_ids_are_unique():
    ids = [r.id for r in CG.REQUIREMENTS]
    assert len(ids) == len(set(ids))


def test_gate_makes_no_llm_call():
    """Deterministic by construction -- no transport import anywhere."""
    import ast
    import inspect
    tree = ast.parse(inspect.getsource(CG))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names.append(node.module or "")
    for n in names:
        assert "openai" not in n.lower(), "the capability gate must never call a model"
