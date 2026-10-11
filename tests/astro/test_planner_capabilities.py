"""Planner capability-route tests (S150 step 2 — emit-only, behaviour-neutral).

The planner now EMITS a `capabilities` list (computed, non-corpus routes) and a
computed-only question (domains empty, capabilities set) is legal. Nothing
consumes `capabilities` yet — the dispatcher (step 3) does — so these tests
assert the planner's output shape only, not any answer behaviour.
"""
from __future__ import annotations

from agent.astro import planner
from agent.astro import capability_registry


_BASE = dict(houses=[7], whose_chart="self", time_scope="none", reasoning="r")


def test_corpus_only_defaults_capabilities_empty():
    fields, errors = planner.validate_plan_object(
        {**_BASE, "domains": ["marriage"], "in_scope": True})
    assert errors == []
    assert fields["capabilities"] == []


def test_computed_only_question_is_legal():
    # in_scope True with NO corpus domain but a capability set — the route this
    # whole arc exists for.
    fields, errors = planner.validate_plan_object(
        {**_BASE, "domains": [], "in_scope": True,
         "capabilities": ["lucky_days"]})
    assert errors == []
    assert fields["domains"] == []
    assert fields["capabilities"] == ["lucky_days"]


def test_in_scope_with_neither_domains_nor_capabilities_is_a_contradiction():
    fields, errors = planner.validate_plan_object(
        {**_BASE, "domains": [], "in_scope": True, "capabilities": []})
    assert fields is None
    assert any("non-empty list when in_scope" in e for e in errors)


def test_unknown_capability_id_rejected():
    fields, errors = planner.validate_plan_object(
        {**_BASE, "domains": ["marriage"], "in_scope": True,
         "capabilities": ["not_a_real_capability"]})
    assert fields is None
    assert any("outside closed vocabulary" in e for e in errors)


def test_capabilities_must_be_a_list():
    fields, errors = planner.validate_plan_object(
        {**_BASE, "domains": ["marriage"], "in_scope": True,
         "capabilities": "lucky_days"})
    assert fields is None
    assert any("capabilities must be a list" in e for e in errors)


def test_mixed_corpus_and_capability():
    fields, errors = planner.validate_plan_object(
        {**_BASE, "domains": ["marriage"], "in_scope": True,
         "capabilities": ["lucky_days"]})
    assert errors == []
    assert fields["domains"] == ["marriage"]
    assert fields["capabilities"] == ["lucky_days"]


def test_capabilities_deduped_in_registry_order():
    fields, errors = planner.validate_plan_object(
        {**_BASE, "domains": [], "in_scope": True,
         "capabilities": ["lucky_days", "lucky_days"]})
    assert errors == []
    assert fields["capabilities"] == ["lucky_days"]


def test_out_of_scope_empty_is_unchanged():
    fields, errors = planner.validate_plan_object(
        {**_BASE, "domains": [], "in_scope": False})
    assert errors == []
    assert fields["in_scope"] is False
    assert fields["capabilities"] == []


def test_plan_object_carries_capabilities():
    fields, _ = planner.validate_plan_object(
        {**_BASE, "domains": [], "in_scope": True,
         "capabilities": ["lucky_days"]})
    plan = planner.Plan(question="q", source="llm", planner_fallback=False,
                        validation_errors=[], raw_responses=[], **fields)
    assert plan.capabilities == ["lucky_days"]
    assert plan.to_dict()["capabilities"] == ["lucky_days"]


def test_system_prompt_carries_schema_and_registry_manifest():
    sp = planner.SYSTEM_PROMPT
    assert '"capabilities": []' in sp            # schema line
    assert "COMPUTED CAPABILITIES" in sp         # manifest header
    for cap in capability_registry.REGISTRY:     # every registered id advertised
        assert cap.id in sp


def test_pre_s150_plan_without_capabilities_key_still_constructs():
    # Backward compatibility: a Plan built without the new field defaults to [].
    plan = planner.Plan(question="q", domains=["marriage"], houses=[7],
                        whose_chart="self", time_scope="none", in_scope=True,
                        reasoning="r")
    assert plan.capabilities == []
