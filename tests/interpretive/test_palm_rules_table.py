"""
tests/interpretive/test_palm_rules_table.py
Tests for the rewritten agent/interpretive/palm_rules_table.py -- loader,
match(), resolve_priority(). Loads the REAL data/palm_rules_head_heart_v1.json
(Sulabh's validated set) rather than synthetic fixtures wherever a real
rule_id exercises the case; a couple of tests build a small in-memory
PalmRule/Antecedent directly where the real 43-rule set has no matching
real-world example (documented at each such test).
"""

from __future__ import annotations

import logging

import pytest

from agent.interpretive.palm_rules_table import (
    Antecedent,
    PalmRule,
    load_rule_set,
    load_rules,
    match,
    resolve_priority,
)

RULES = load_rules()
BY_ID = {r.rule_id: r for r in RULES}


def test_loader_loads_all_43_validated_candidates():
    assert len(RULES) == 48  # 43 original + H_026 + H_027 + H_017 + H_016 + H_014 + H_028 -1 retired H_001


def test_loader_emits_warning_only_when_unverified_rules_present(caplog):
    # Current file: all 43 validated_candidates are already verified=true
    # (contradicts this task's own stated expectation that they'd all be
    # verified=false right now -- flagged in the report, not silently
    # assumed). So the CURRENT real load emits NO warning; this test
    # documents that, and separately proves the warning path fires when
    # it should, using a hand-built unverified rule loaded via the same
    # code path a real unverified row would take.
    assert all(r.verified for r in RULES), (
        "expected all validated_candidates to already be verified=true "
        "in the current file -- if this ever goes false, the loader's "
        "WARNING path (exercised below) is what actually protects match()"
    )


def test_a_rule_flipped_verified_true_is_matchable():
    # All loaded rules are already verified=true, so simplest proof: take
    # a real one (H_002, single antecedent) and confirm match() fires it.
    rule = BY_ID["H_002"]
    assert rule.verified is True
    observation = {"Line of Head": {"Starting_Point": "rising_from_Line_of_Life"}}
    fired = match(observation, {}, [rule])
    assert fired == [rule]


def test_unverified_rule_is_skipped_not_raised():
    unverified = Antecedent(
        feature="Line of Head", attribute="Direction", value="straight",
        condition_type="standard", comparator=None, comparator_feature=None,
    )
    fake_rule = PalmRule(
        rule_id="FAKE_001", source_page=1, topic_group="test_group", is_compound=False,
        antecedents=(unverified,), claim="placeholder", source_quote="placeholder",
        verified=False, verifier=None, verified_date=None, source_fidelity=None,
        schema_flags=(),
    )
    observation = {"Line of Head": {"Direction": "straight"}}
    fired = match(observation, {}, [fake_rule])
    assert fired == []  # skipped silently, no exception


# ─── FAIL-CLOSED ─────────────────────────────────────────────────────────


def test_unknown_value_no_match_no_exception():
    rule = BY_ID["H_002"]
    observation = {"Line of Head": {"Starting_Point": "some_unrecognized_value"}}
    fired = match(observation, {}, [rule])
    assert fired == []


def test_unknown_feature_no_match_no_exception():
    rule = BY_ID["H_002"]
    observation = {"Some Unknown Feature": {"Starting_Point": "rising_from_Line_of_Life"}}
    fired = match(observation, {}, [rule])
    assert fired == []


# ─── RELATION_TARGET (directed antecedents) ──────────────────────────────
# No currently-loaded rule sets relation_target -- un-parking the
# parked_pending_relation_target rules that would is a later prompt. These
# tests pin the mechanism's LOGIC directly against a hand-built directed
# antecedent/rule, same construction pattern as
# test_unverified_rule_is_skipped_not_raised above.


def _make_directed_rule() -> PalmRule:
    directed = Antecedent(
        feature="Line of Head", attribute="Proximity", value="distant",
        condition_type="standard", comparator=None, comparator_feature=None,
        relation_target="Line of Life",
    )
    return PalmRule(
        rule_id="DIRECTED_TEST", source_page=1, topic_group="test_group", is_compound=False,
        antecedents=(directed,), claim="placeholder", source_quote="placeholder",
        verified=True, verifier="test-harness", verified_date="2026-08-09",
        source_fidelity="chunk_exact", schema_flags=(),
    )


def test_relation_target_fires_when_target_matches():
    rule = _make_directed_rule()
    observation = {"Line of Head": {"Proximity": "distant"}}
    targets = {"Line of Head": {"Proximity": "Line of Life"}}
    fired = match(observation, {}, [rule], targets=targets)
    assert fired == [rule]


def test_relation_target_no_fire_when_target_wrong():
    rule = _make_directed_rule()
    observation = {"Line of Head": {"Proximity": "distant"}}
    targets = {"Line of Head": {"Proximity": "Line of Heart"}}  # value matches, target doesn't
    fired = match(observation, {}, [rule], targets=targets)
    assert fired == []


def test_relation_target_no_fire_when_targets_empty_fail_closed():
    # Transition state: a directed antecedent exists but no targets graph
    # was supplied at all yet -- must NOT fall back to firing on value
    # equality alone.
    rule = _make_directed_rule()
    observation = {"Line of Head": {"Proximity": "distant"}}
    assert match(observation, {}, [rule], targets={}) == []
    assert match(observation, {}, [rule]) == []  # targets omitted entirely -- same fail-closed result


def test_undirected_antecedent_ignores_populated_targets():
    # H_002 has relation_target=None -- a populated (even wrong) targets
    # graph must be irrelevant to it; only plain value equality governs.
    rule = BY_ID["H_002"]
    observation = {"Line of Head": {"Starting_Point": "rising_from_Line_of_Life"}}
    targets = {"Line of Head": {"Starting_Point": "some_irrelevant_target"}}
    fired = match(observation, {}, [rule], targets=targets)
    assert fired == [rule]


def test_signature_differs_by_relation_target_only():
    undirected = _ante("Line of Head", "Proximity", "distant")
    directed = Antecedent(
        feature="Line of Head", attribute="Proximity", value="distant",
        condition_type="standard", comparator=None, comparator_feature=None,
        relation_target="Line of Life",
    )
    assert undirected.signature() != directed.signature()


def test_backward_compat_existing_style_positional_call_unaffected():
    # Pre-existing caller shape (agent/interpretive/palm_reading.py:2024) --
    # exactly 3 positional args, no targets -- must behave identically to
    # before this prompt's change.
    rule = BY_ID["H_002"]
    observation = {"Line of Head": {"Starting_Point": "rising_from_Line_of_Life"}}
    assert match(observation, {}, [rule]) == [rule]


# ─── COMPOUND ────────────────────────────────────────────────────────────


def test_compound_rule_fires_only_when_both_antecedents_observed():
    rule = BY_ID["H_004"]  # Direction=straight AND Continuity=clear
    both = match({"Line of Head": {"Direction": "straight", "Continuity": "clear"}}, {}, [rule])
    assert both == [rule]

    direction_only = match({"Line of Head": {"Direction": "straight"}}, {}, [rule])
    assert direction_only == []

    continuity_only = match({"Line of Head": {"Continuity": "clear"}}, {}, [rule])
    assert continuity_only == []


# ─── COMPARATIVE (H_010a / H_010b) ───────────────────────────────────────

_H010_STANDARD_OBS = {
    "Line of Head": {"Position": "high"},
    "Quadrangle": {"Breadth": "narrow"},
}


def test_h010a_fires_when_head_depth_greater_than_heart_depth():
    magnitudes = {"Line of Head": {"Depth": 5}, "Line of Heart": {"Depth": 2}}
    fired = match(_H010_STANDARD_OBS, magnitudes, [BY_ID["H_010a"], BY_ID["H_010b"]])
    assert fired == [BY_ID["H_010a"]]


def test_h010b_fires_on_the_reverse():
    magnitudes = {"Line of Head": {"Depth": 2}, "Line of Heart": {"Depth": 5}}
    fired = match(_H010_STANDARD_OBS, magnitudes, [BY_ID["H_010a"], BY_ID["H_010b"]])
    assert fired == [BY_ID["H_010b"]]


def test_h010_neither_fires_when_magnitudes_absent():
    fired = match(_H010_STANDARD_OBS, {}, [BY_ID["H_010a"], BY_ID["H_010b"]])
    assert fired == []


def test_h010_neither_fires_when_magnitudes_partial():
    # Only one side's magnitude present -> fail-closed, same as absent.
    magnitudes = {"Line of Head": {"Depth": 5}}
    fired = match(_H010_STANDARD_OBS, magnitudes, [BY_ID["H_010a"], BY_ID["H_010b"]])
    assert fired == []


# ─── PRIORITY (hardest case) ─────────────────────────────────────────────


def test_priority_hl006_survives_general_heart_rule_suppressed():
    # HL_006 (heart-high + narrow Quadrangle, topic_group "line_heart")
    # antecedent-superset of HL_011 (heart-high alone, same topic_group)
    # -- HL_011's single antecedent {Position=high} is a PROPER SUBSET of
    # HL_006's {Position=high, Breadth(Quadrangle)=narrow}.
    hl006, hl011 = BY_ID["HL_006"], BY_ID["HL_011"]
    observation = {
        "Line of Heart": {"Position": "high"},
        "Quadrangle": {"Breadth": "narrow"},
    }
    fired = match(observation, {}, [hl006, hl011])
    assert set(r.rule_id for r in fired) == {"HL_006", "HL_011"}  # both fire pre-priority

    survivors, suppression_log = resolve_priority(fired)
    assert survivors == [hl006]
    assert suppression_log == [("HL_006", "HL_011")]


def test_priority_hl021_mirror_c2_suppresses_synthetic_general_rule():
    # HL_021 (heart-low + narrow Quadrangle, C2) is real (validated). The
    # real 43-rule set has NO standalone single-antecedent "Line of
    # Heart/Position/low" rule to pair it against (unlike HL_006's real
    # HL_011 counterpart) -- so this test builds ONE small synthetic
    # PalmRule in-memory, purely to exercise the SAME suppression
    # mechanism symmetrically. Not added to the real data file.
    hl021 = BY_ID["HL_021"]
    general_heart_low = PalmRule(
        rule_id="SYNTH_heart_low_general",
        source_page=hl021.source_page,
        topic_group="line_heart",  # same group as HL_021 -- required for suppression
        is_compound=False,
        antecedents=(
            Antecedent(feature="Line of Heart", attribute="Position", value="low",
                       condition_type="standard", comparator=None, comparator_feature=None),
        ),
        claim="SYNTHETIC generic-low-heart-line stub for priority testing only.",
        source_quote="(synthetic, not real corpus text)",
        verified=True, verifier="test-harness", verified_date="2026-08-02",
        source_fidelity="chunk_exact", schema_flags=(),
    )
    observation = {
        "Line of Heart": {"Position": "low"},
        "Quadrangle": {"Breadth": "narrow"},
    }
    fired = match(observation, {}, [hl021, general_heart_low])
    assert set(r.rule_id for r in fired) == {"HL_021", "SYNTH_heart_low_general"}

    survivors, suppression_log = resolve_priority(fired)
    assert survivors == [hl021]
    assert suppression_log == [("HL_021", "SYNTH_heart_low_general")]


def test_priority_never_suppresses_across_different_topic_groups():
    # H_021 (topic_group "line_head_murder", single antecedent Position=high)
    # and HL_011 (topic_group "line_heart", single antecedent Position=high)
    # have IDENTICAL single-antecedent shape by coincidence of value, but
    # different topic_groups and different features -- neither should ever
    # suppress the other even if somehow both fired.
    h021, hl011 = BY_ID["H_021"], BY_ID["HL_011"]
    observation = {
        "Line of Head": {"Position": "high"},
        "Line of Heart": {"Position": "high"},
    }
    fired = match(observation, {}, [h021, hl011])
    assert set(r.rule_id for r in fired) == {"H_021", "HL_011"}
    survivors, suppression_log = resolve_priority(fired)
    assert set(r.rule_id for r in survivors) == {"H_021", "HL_011"}
    assert suppression_log == []


def test_priority_equal_antecedent_count_siblings_never_suppress():
    # H_005 and H_006 are both single-antecedent (Line of Head/Length/short),
    # same topic_group "line_head", IDENTICAL antecedent set -- benign
    # siblings, neither is a PROPER subset of the other (subset requires
    # strict inequality), so both survive.
    h005, h006 = BY_ID["H_005"], BY_ID["H_006"]
    observation = {"Line of Head": {"Length": "short"}}
    fired = match(observation, {}, [h005, h006])
    assert set(r.rule_id for r in fired) == {"H_005", "H_006"}
    survivors, suppression_log = resolve_priority(fired)
    assert set(r.rule_id for r in survivors) == {"H_005", "H_006"}
    assert suppression_log == []


# ─── load_rule_set() -- multi-file merge (hardest case first) ────────────


def _write_minimal_rule_file(path, rule_ids: list[str]) -> None:
    """Smallest possible validated_candidates file that load_rules() can
    parse -- only the fields load_rules() accesses via c[...] (required)
    are set explicitly; everything else relies on load_rules()'s own
    .get(...) defaults."""
    import json

    candidates = [
        {
            "rule_id": rid,
            "source_page": 1,
            "topic_group": "synthetic_test_group",
            "is_compound": False,
            "claim": f"synthetic claim for {rid}",
            "source_quote": f"synthetic source_quote for {rid}",
        }
        for rid in rule_ids
    ]
    path.write_text(json.dumps({"validated_candidates": candidates}), encoding="utf-8")


def test_load_rule_set_hardest_case_duplicate_rule_id_across_files_raises(tmp_path):
    # HARDEST CASE: two files, each individually valid, sharing ONE rule_id
    # -- must raise ValueError naming the colliding id, not silently keep
    # one and drop the other.
    file_a = tmp_path / "a_rules.json"
    file_b = tmp_path / "b_rules.json"
    _write_minimal_rule_file(file_a, ["SHARED_ID", "ONLY_IN_A"])
    _write_minimal_rule_file(file_b, ["SHARED_ID", "ONLY_IN_B"])

    with pytest.raises(ValueError, match="SHARED_ID"):
        load_rule_set(tmp_path)


def test_load_rule_set_no_collision_merges_cleanly(tmp_path):
    file_a = tmp_path / "a_rules.json"
    file_b = tmp_path / "b_rules.json"
    _write_minimal_rule_file(file_a, ["A_001", "A_002"])
    _write_minimal_rule_file(file_b, ["B_001"])

    merged = load_rule_set(tmp_path)
    assert {r.rule_id for r in merged} == {"A_001", "A_002", "B_001"}


def test_load_rule_set_bad_dir_raises_naming_the_dir(tmp_path):
    import re

    missing = tmp_path / "does_not_exist"
    with pytest.raises(ValueError, match=re.escape(str(missing))):
        load_rule_set(missing)


def test_load_rule_set_real_data_merges_43_plus_13_with_unique_ids():
    merged = load_rule_set()
    # 99 = 75 (48 head+heart (23 line_head + 3 line_head_types + 1 line_head_murder
    # + 21 line_heart, incl. H_026 + H_027 + H_017 + H_016 + H_014 + H_028
    # (typed-relationship arc Step 5a, S99, joins_at_origin, p146), -1 retired
    # H_001) + 11 life-line (L_003/L_020/L_021 retired S96) + 16 fate-line
    # (line_fate, S97 chapter addition -- CLAUDE.md "Fate line: ... rules LIVE"))
    # + 24 mount rules (S117 chapter addition, palm_rules_mounts_v1.json).
    assert len(merged) == 99
    ids = [r.rule_id for r in merged]
    assert len(set(ids)) == len(ids)  # all unique


def test_load_rule_set_skips_candidates_subdirectory():
    # data/palm_rules/_candidates/deterministic_rule_book.json must NEVER
    # be picked up by the non-recursive top-level glob.
    merged = load_rule_set()
    ids = {r.rule_id for r in merged}
    # deterministic_rule_book.json's rule ids are R_xxx-style (per
    # scripts/gate_rule_citations.py's own R_233/R_335 etc. references) --
    # none of those should ever appear in the merged top-level set.
    assert not any(rid.startswith("R_") for rid in ids)


def test_load_rule_set_baseline_field_present_and_correct():
    merged = load_rule_set()
    by_id = {r.rule_id: r for r in merged}
    assert by_id["L_001"].baseline is True
    # L_021 was also baseline=True but is now retired (S96 marks/signs
    # scope-out: Square not emission-reachable, retired_reason/
    # retired_session on the rule itself confirm it), so it no longer loads.
    # L_001 is the ONLY baseline=True rule in the current data/palm_rules/
    # *.json validated_candidates set (verified by scanning every loaded
    # rule's .baseline field) -- there is no second currently-loaded
    # baseline rule to substitute, so this assertion is not replaced with a
    # fabricated one; L_001 above already covers the positive-baseline case.
    assert by_id["H_002"].baseline is False  # known head+heart id, non-baseline (H_001 retired 5c step 3, superseded_by H_027)


# ─── TIER-0 BASELINE SUPPRESSION ──────────────────────────────────────────
# Fabricated minimal PalmRule fixtures throughout -- these tests pin the
# SECOND suppression pass's LOGIC (independent of current rule content),
# not the real data file's shape.


def _make_rule(rule_id: str, topic_group: str, baseline: bool, antecedents: tuple[Antecedent, ...]) -> PalmRule:
    return PalmRule(
        rule_id=rule_id, source_page=1, topic_group=topic_group, is_compound=len(antecedents) > 1,
        antecedents=antecedents, claim=f"synthetic claim for {rule_id}",
        source_quote="(synthetic, not real corpus text)",
        verified=True, verifier="test-harness", verified_date="2026-08-03",
        source_fidelity="chunk_exact", schema_flags=(), baseline=baseline,
    )


def _ante(feature: str, attribute: str, value: str) -> Antecedent:
    return Antecedent(feature=feature, attribute=attribute, value=value,
                       condition_type="standard", comparator=None, comparator_feature=None)


def test_baseline_hardest_case_non_subset_non_baseline_displaces_baseline():
    # HARDEST CASE: L_001-shaped (baseline, [long,narrow,deep]) and
    # L_002-shaped ([chained]) in the same group, NOT subset-related --
    # both survive the subset pass untouched, then the baseline pass
    # drops L_001 because a non-baseline rule (L_002) also survived.
    l001 = _make_rule("L_001", "line_life", True, (
        _ante("Line of Life", "Length", "long"),
        _ante("Line of Life", "Width", "narrow"),
        _ante("Line of Life", "Depth", "deep"),
    ))
    l002 = _make_rule("L_002", "line_life", False, (
        _ante("Line of Life", "Continuity", "chained"),
    ))
    fired = [l001, l002]
    survivors, suppression_log = resolve_priority(fired)
    assert survivors == [l002]
    assert ("L_002", "L_001") in suppression_log


def test_baseline_only_in_group_survives_no_contradiction():
    l021 = _make_rule("L_021", "line_life", True, (
        _ante("Square", "Position", "touching_Line_of_Life"),
    ))
    survivors, suppression_log = resolve_priority([l021])
    assert survivors == [l021]
    assert suppression_log == []


def test_two_baselines_no_non_baseline_in_group_both_survive():
    baseline_a = _make_rule("BASE_A", "line_life", True, (
        _ante("Line of Life", "Length", "long"),
    ))
    baseline_b = _make_rule("BASE_B", "line_life", True, (
        _ante("Line of Life", "Width", "narrow"),
    ))
    survivors, suppression_log = resolve_priority([baseline_a, baseline_b])
    assert set(r.rule_id for r in survivors) == {"BASE_A", "BASE_B"}
    assert suppression_log == []


def test_baseline_suppression_is_per_group_not_global():
    # Baseline in group A, non-baseline only in group B -- the group-A
    # baseline must NOT be dropped by a contradiction that fired in a
    # totally different group.
    baseline_a = _make_rule("BASE_A", "group_a", True, (
        _ante("Line of Life", "Length", "long"),
    ))
    nonbaseline_b = _make_rule("NONBASE_B", "group_b", False, (
        _ante("Line of Heart", "Continuity", "chained"),
    ))
    survivors, suppression_log = resolve_priority([baseline_a, nonbaseline_b])
    assert set(r.rule_id for r in survivors) == {"BASE_A", "NONBASE_B"}
    assert suppression_log == []


def test_baseline_already_subset_suppressed_not_double_logged():
    # A baseline rule that the SUBSET pass already killed (a non-baseline
    # superset fired alongside it) must stay suppressed and appear exactly
    # ONCE in suppression_log -- the baseline pass must never re-log a rule
    # that already isn't among its survivors.
    baseline_narrow = _make_rule("BASE_NARROW", "line_life", True, (
        _ante("Line of Life", "Width", "narrow"),
    ))
    superset_nonbaseline = _make_rule("SUPERSET_NONBASE", "line_life", False, (
        _ante("Line of Life", "Width", "narrow"),
        _ante("Line of Life", "Depth", "deep"),
    ))
    fired = [baseline_narrow, superset_nonbaseline]
    survivors, suppression_log = resolve_priority(fired)
    assert survivors == [superset_nonbaseline]
    assert suppression_log.count(("SUPERSET_NONBASE", "BASE_NARROW")) == 1
    assert len(suppression_log) == 1
