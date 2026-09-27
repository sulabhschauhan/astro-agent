"""
tests/astro/test_house_roles.py
Unit tests for agent.astro.house_roles -- the KP house-ROLE -> weight doctrine
(S145). Pure (no ephemeris, no LLM).

Covers: marriage promotion/negation/obstacle weights are sourced correctly; the
SCOPE GUARD (unmapped domains -> all-promotion, i.e. pre-S145 behaviour); the
FAIL-SAFE (unclassified house kept at 1.0); and the MULTI-DOMAIN max rule.
"""
from __future__ import annotations

from agent.astro import house_roles as hr


def test_marriage_promotion_houses_weight_one():
    w = hr.weighted_targets(["marriage"], [2, 7, 11])
    assert w == {2: 1.0, 7: 1.0, 11: 1.0}


def test_marriage_obstacle_eighth_is_zeroed():
    # The exact S145 bug: planner emits [2,7,8,11]; the 8th must drop to 0.
    w = hr.weighted_targets(["marriage"], [2, 7, 8, 11])
    assert w[8] == 0.0
    assert w[2] == w[7] == w[11] == 1.0


def test_marriage_negation_houses_zeroed():
    # 1,6,10 = 12th-from-{2,7,11} (K-P-Reader-2 line ~2871).
    w = hr.weighted_targets(["marriage"], [1, 6, 10])
    assert w == {1: 0.0, 6: 0.0, 10: 0.0}


def test_scope_guard_unmapped_domain_is_all_promotion():
    # career/children are NOT mapped -> every house weight 1.0, so the ranker is
    # byte-identical to pre-S145. This is the scope guard that protects the
    # unvalidated domains.
    for dom in ("career", "children", "wealth", "timing_dasha"):
        w = hr.weighted_targets([dom], [2, 6, 8, 10, 11])
        assert set(w.values()) == {1.0}, dom


def test_scope_guard_empty_and_none_domains():
    assert hr.weighted_targets([], [2, 7, 8, 11]) == {2: 1.0, 7: 1.0, 8: 1.0, 11: 1.0}
    assert hr.weighted_targets(None, [7, 8]) == {7: 1.0, 8: 1.0}


def test_failsafe_unclassified_house_kept():
    # House 5 (e.g. love-marriage) is not in the marriage role map -> must stay 1.0,
    # never silently zeroed (that would be narrowing).
    w = hr.weighted_targets(["marriage"], [5, 7, 8])
    assert w[5] == 1.0 and w[7] == 1.0 and w[8] == 0.0


def test_multidomain_max_rule_unzeros_shared_house():
    # If a future domain that promotes the 8th is co-planned with marriage, the 8th
    # must NOT be zeroed (max rule). Simulate by injecting a temp mapped domain.
    hr.DOMAIN_ROLES["_test_longevity"] = {8: 1.0}
    try:
        w = hr.weighted_targets(["marriage", "_test_longevity"], [7, 8])
        assert w[8] == 1.0   # max(0.0 from marriage, 1.0 from longevity)
        assert w[7] == 1.0
    finally:
        del hr.DOMAIN_ROLES["_test_longevity"]


def test_marriage_plan_emits_no_negation_houses_in_practice():
    # The planner prompt emits [2,7,8,11] for marriage (never 1/6/10), so in
    # practice only the 8th is demoted. Guards against a regression where the
    # planner starts emitting negation houses unnoticed.
    w = hr.weighted_targets(["marriage"], [2, 7, 8, 11])
    assert sorted(h for h, v in w.items() if v > 0) == [2, 7, 11]


def test_empty_houses_returns_empty():
    assert hr.weighted_targets(["marriage"], []) == {}
    assert hr.weighted_targets(["marriage"], None) == {}
