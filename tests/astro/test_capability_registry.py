"""Tests for agent.astro.capability_registry (S150 dispatcher foundation).

Pure: the registry + manifest renderers are stdlib-only. The one cross-module
test pins the growth contract -- every capability's fact_key must be a member
of capability_gate.FACT_BLOCK_PROVIDES, so a capability can never route to a
fact the block does not carry.
"""
from __future__ import annotations

import dataclasses

import pytest

from agent.astro import capability_registry as cr


def test_registry_non_empty_and_ids_unique():
    assert cr.REGISTRY, "registry must seed at least the pilot capability"
    ids = [c.id for c in cr.REGISTRY]
    assert len(ids) == len(set(ids)), "capability ids must be unique"
    assert cr.CAPABILITY_IDS == frozenset(ids)


def test_lucky_days_pilot_present():
    lucky = cr.get("lucky_days")
    assert lucky is not None
    assert lucky.fact_key == "lucky_unlucky"
    assert lucky.dated is False
    assert lucky.interpreter_directive, "a capability must carry a directive"


def test_get_unknown_returns_none():
    assert cr.get("does_not_exist") is None


def test_fact_keys_match_registry():
    assert cr.fact_keys() == frozenset(c.fact_key for c in cr.REGISTRY)


def test_every_fact_key_is_declared_in_the_block_growth_contract():
    # The binding contract: a computed capability may only route to a fact the
    # block actually provides. Importing capability_gate here is deliberate --
    # the two registers must not drift (P-030 class).
    from agent.astro.capability_gate import FACT_BLOCK_PROVIDES
    missing = cr.fact_keys() - set(FACT_BLOCK_PROVIDES)
    assert not missing, (
        f"capabilities route to fact keys absent from FACT_BLOCK_PROVIDES: "
        f"{sorted(missing)}"
    )


def test_directives_for_filters_and_orders():
    d = cr.directives_for(["lucky_days", "unknown_id"])
    assert len(d) == 1
    assert "favourable_days" in d[0]
    assert cr.directives_for([]) == []
    assert cr.directives_for(None) == []


def test_planner_manifest_lists_every_id_and_gloss():
    m = cr.planner_manifest()
    for c in cr.REGISTRY:
        assert c.id in m
        assert c.intent_gloss in m
    assert "closed list" in m.lower()


def test_interpreter_manifest_marks_available_when_fact_present():
    m = cr.interpreter_manifest(available_fact_keys={"lucky_unlucky"})
    assert "Lucky & unlucky weekdays: available." in m


def test_interpreter_manifest_marks_unavailable_when_fact_absent():
    m = cr.interpreter_manifest(available_fact_keys=set())
    assert "not available for this chart." in m


def test_interpreter_manifest_names_missing_required_input():
    # A synthetic capability with a required input exercises the ask-for-input
    # branch without coupling the test to a specific real input.
    demo = dataclasses.replace(
        cr.get("lucky_days"), id="demo", fact_key="demo_key",
        label="Demo", requires_input=("exact_birth_time",),
    )
    saved = cr.REGISTRY
    cr.REGISTRY = cr.REGISTRY + (demo,)
    try:
        m = cr.interpreter_manifest(available_fact_keys=set(), inputs_present=())
        assert "Demo: not computed -- needs exact_birth_time." in m
    finally:
        cr.REGISTRY = saved


def test_interpreter_manifest_forbids_upsell_and_improvisation():
    m = cr.interpreter_manifest(available_fact_keys={"lucky_unlucky"})
    low = m.lower()
    assert "do not offer" in low and "not ask for" in low  # no upsell
    assert "do not compute that yet" in low                # honest decline
