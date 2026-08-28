"""
tests/interpretive/test_vocab_reachability_scan.py
Regression test for scripts/vocab_reachability_scan.py's classify_antecedent()
UNEMITTABLE gate (S97): an antecedent with a non-null relation_target on an
attribute _RELATIONAL_ATTRIBUTE_MAP never emits through the relational parse
channel is registry-legal but permanently unfireable -- the Ending_Point/
Position dead-rule bug that real-hand dogfood caught live (see
diagnostics/latest_run.md S97, commit f1335c1). This gate makes that bug
class a mechanical, pre-dogfood check instead of a live-hand discovery.

Also wires the gate into the suite (this file's second half): every
data/palm_rules/palm_rules_*.json file is discovered and scanned
automatically, so a future rule authored with this exact bug shape fails
CI instead of waiting for a real-hand dogfood run to surface it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.vocab_reachability_scan import (
    _REPO_ROOT,
    classify_antecedent,
    load_scanned_rules,
    scan_rule,
)


def test_relation_target_on_non_relational_attribute_is_unemittable():
    """Ending_Point/Mount of Jupiter: the exact S97 dead-rule shape --
    registry-legal (present in attribute_feature_mapping /
    attribute_value_binding) but never emitted by any extractor path,
    since _RELATIONAL_ATTRIBUTE_MAP only ever populates Starting_Point/
    Proximity/Position/Branching from a relation_target parse."""
    result = classify_antecedent("Line of Fate", "Ending_Point", None, "Mount of Jupiter")
    assert result["status"] == "UNEMITTABLE"
    assert "Ending_Point" in result["detail"]
    assert "S97" in result["detail"]


def test_relation_target_on_the_fixed_attribute_is_not_unemittable():
    """Position/Mount of Jupiter: the S97 FIX's replacement attribute --
    same relation_target, same feature, but Position IS in
    _RELATIONAL_ATTRIBUTE_MAP's emitted set (via the TERMINATION field),
    so the gate must NOT fire here. Proves the gate discriminates on the
    actual emitted-attribute set, not merely on "has a relation_target"."""
    result = classify_antecedent("Line of Fate", "Position", None, "Mount of Jupiter")
    assert result["status"] != "UNEMITTABLE"
    assert result["status"] == "yes"


def test_scan_rule_surfaces_unemittable_from_a_fake_in_memory_rule():
    """Confirms the ACTUAL code path test_all_rule_files_have_zero_
    unemittable_antecedents (below) relies on -- scan_rule(), not
    classify_antecedent() directly -- would catch a real regression. Same
    Ending_Point/Mount of Jupiter shape as the unit tests above, but built
    as an in-memory fake rule dict, never a real rule file edit."""
    fake_rule = {
        "rule_id": "FAKE_UNEMITTABLE_PROBE",
        "antecedents": [{
            "feature": "Line of Fate",
            "attribute": "Ending_Point",
            "value": None,
            "condition_type": "standard",
            "comparator": None,
            "comparator_feature": None,
            "relation_target": "Mount of Jupiter",
        }],
    }
    rows = scan_rule(fake_rule)
    assert len(rows) == 1
    assert rows[0]["rule_id"] == "FAKE_UNEMITTABLE_PROBE"
    assert rows[0]["status"] == "UNEMITTABLE"


# ─── Suite-wide enforcement: every rule file, zero UNEMITTABLE ──────────
# Converts the S97 gate from a manual `python scripts/vocab_reachability_
# scan.py --rules ...` invocation into an enforced CI check over every
# rule file that exists, present and future.

_RULES_DIR = _REPO_ROOT / "data" / "palm_rules"
_DISCOVERED_RULE_FILES = sorted(_RULES_DIR.glob("palm_rules_*.json"))

_KNOWN_RULE_FILE_NAMES = {
    "palm_rules_fate_line_v1.json",
    "palm_rules_head_heart_v1.json",
    "palm_rules_life_line_v1.json",
}


def test_rule_file_discovery_finds_at_least_the_three_known_files():
    """Guards the glob itself: a typo'd pattern or an empty/moved
    data/palm_rules/ directory must not silently make the parametrized
    test below collect zero cases and report a false-green suite."""
    discovered_names = {p.name for p in _DISCOVERED_RULE_FILES}
    missing = _KNOWN_RULE_FILE_NAMES - discovered_names
    assert not missing, (
        f"glob {_RULES_DIR}/palm_rules_*.json found {sorted(discovered_names)}, "
        f"missing known file(s) {sorted(missing)} -- discovery is broken"
    )


@pytest.mark.parametrize(
    "rules_path",
    _DISCOVERED_RULE_FILES,
    ids=[p.name for p in _DISCOVERED_RULE_FILES],
)
def test_all_rule_files_have_zero_unemittable_antecedents(rules_path: Path):
    rules = load_scanned_rules(rules_path)
    offenders = [
        f"{rules_path.name}:{row['rule_id']} attribute={row['attribute']!r} "
        f"-- {row['detail']}"
        for rule in rules
        for row in scan_rule(rule)
        if row["status"] == "UNEMITTABLE"
    ]
    assert not offenders, (
        f"{len(offenders)} UNEMITTABLE antecedent(s) in {rules_path.name} "
        "(relation_target on a non-emitted attribute -- the Ending_Point/"
        "Position S97 bug class):\n" + "\n".join(offenders)
    )


# ═══════════════════════════════════════════════════════════════════════
# S113: typed-relationship tokens classified via the RELATION registries,
# not the value-attribute map (attribute_feature_mapping). Root cause:
# classify_antecedent's early `attribute not in oe._ATTRIBUTE_FEATURE_MAP`
# check ran BEFORE the relation branch, so any of the 8 typed tokens
# (oe._RELATIONSHIP_TOKENS) NOT also injected into attribute_feature_
# mapping false-flagged as unreachable. Only 2 of 8 (joins_at_origin,
# meets) had been worked around that way; stopped_by (S112), cuts (live
# since S110), cut_by, touches, takes_possession_of, and branch_in all
# false-flagged. Fixed by intercepting `attribute in oe._RELATIONSHIP_
# TOKENS` immediately after the feature-existence check, classifying via
# relation_target_registry membership directly -- mirrors
# rule_vocabulary_closure_gate.py's own classify_antecedent Rule 3.
# ═══════════════════════════════════════════════════════════════════════

_ALL_TYPED_RELATIONSHIP_TOKENS = (
    "joins_at_origin", "meets", "cuts", "cut_by", "touches",
    "stopped_by", "takes_possession_of", "branch_in",
)


def test_ft007_ft008_regression_now_classify_reachable_via_live_rules():
    """HARDEST CASE FIRST: the exact S112 regression this fix closes.
    FT_007 (Line of Fate, stopped_by, relation_target Line of Heart) and
    FT_008 (relation_target Line of Head) were false-flagged NO/
    unreachable before this fix (caught live in S113's own pre-flight).
    Asserted against the LIVE rules file scan_rule() actually loads --
    not just a synthetic antecedent -- so this proves the real committed
    rule, not just the mechanism in isolation."""
    fate_rules_path = _RULES_DIR / "palm_rules_fate_line_v1.json"
    rules = load_scanned_rules(fate_rules_path)
    by_id = {r["rule_id"]: r for r in rules}
    assert "FT_007" in by_id and "FT_008" in by_id

    ft007_rows = scan_rule(by_id["FT_007"])
    ft008_rows = scan_rule(by_id["FT_008"])
    assert len(ft007_rows) == 1 and len(ft008_rows) == 1
    assert ft007_rows[0]["status"] == "yes", ft007_rows[0]["detail"]
    assert ft008_rows[0]["status"] == "yes", ft008_rows[0]["detail"]
    assert ft007_rows[0]["attribute"] == "stopped_by"
    assert ft007_rows[0]["relation_target"] == "Line of Heart"
    assert ft008_rows[0]["relation_target"] == "Line of Head"


@pytest.mark.parametrize(
    "token", ("cuts", "cut_by", "touches", "stopped_by", "takes_possession_of", "branch_in"),
)
def test_previously_missing_tokens_reachable_with_valid_relation_target(token: str):
    """The 6 tokens that were NEVER worked around in attribute_feature_
    mapping (unlike joins_at_origin/meets) -- each must now classify
    reachable with a real relation_target_registry member."""
    result = classify_antecedent("Line of Fate", token, None, "Line of Head")
    assert result["status"] == "yes", result["detail"]
    assert token in result["detail"]


@pytest.mark.parametrize(
    "token", ("cuts", "cut_by", "touches", "stopped_by", "takes_possession_of", "branch_in"),
)
def test_previously_missing_tokens_unreachable_with_invalid_relation_target(token: str):
    """Proves the fix isn't blanket-permissive: the SAME 6 tokens with an
    invalid relation_target (not in relation_target_registry) must still
    classify NO, with a detail naming the registry-membership failure --
    not silently accepted just because the attribute is now recognized."""
    result = classify_antecedent("Line of Fate", token, None, "Not A Real Target")
    assert result["status"] == "NO"
    assert "relation_target_registry" in result["detail"]


@pytest.mark.parametrize("token", ("joins_at_origin", "meets"))
def test_formerly_workaround_tokens_still_reachable_via_relation_path_not_afm(token: str):
    """joins_at_origin and meets were the 2 tokens previously injected
    INTO attribute_feature_mapping as a workaround. Must still classify
    reachable after this fix -- but now via the SAME relation path as the
    other 6, proven by the detail text referencing "typed" (this
    function's own relation-branch wording), not the old
    attribute_feature_mapping-based message."""
    feature = "Line of Head" if token == "joins_at_origin" else "Line of Fate"
    target = "Line of Life" if token == "joins_at_origin" else "Line of Heart"
    result = classify_antecedent(feature, token, None, target)
    assert result["status"] == "yes", result["detail"]
    assert "typed" in result["detail"]
    assert "attribute_feature_mapping" not in result["detail"]


def test_negative_guard_genuinely_unknown_value_attribute_still_unreachable():
    """NEGATIVE GUARD: an attribute that is NOT one of the 8 typed
    relationship tokens and NOT in attribute_feature_mapping must still
    classify as unreachable (status "NO", the value-attribute-map's own
    "attribute does not exist" branch) -- proves the S113 fix's new
    early-return branch is narrowly scoped to oe._RELATIONSHIP_TOKENS
    only and does not defeat the gate for a genuinely unknown attribute."""
    result = classify_antecedent("Line of Fate", "totally_unknown_attr", "some_value", None)
    assert result["status"] == "NO"
    assert "totally_unknown_attr" in result["detail"]
    assert "attribute_feature_mapping" in result["detail"]


def test_relation_target_on_non_relational_attribute_still_hits_s97_gate_after_s113():
    """Re-confirms (post-S113) that a relation_target on an attribute
    that is NEITHER a typed-relationship token NOR an old directional
    attribute still hits the pre-existing S97 CI-gate (UNEMITTABLE) --
    the S113 fix's new branch is scoped to oe._RELATIONSHIP_TOKENS only
    and must never swallow this case. Same shape as this file's original
    S97 regression test above, re-asserted here to lock it against this
    specific fix's own placement (the new branch sits ahead of this gate
    in source order; a placement mistake could have made it swallow this
    case too -- this test exists to catch exactly that class of error)."""
    result = classify_antecedent("Line of Fate", "Ending_Point", None, "Line of Head")
    assert result["status"] == "UNEMITTABLE"
    assert "S97" in result["detail"]


def test_typed_token_with_missing_relation_target_is_unemittable():
    """Every one of the 8 typed tokens is target-bearing by construction
    -- a typed-relationship attribute with relation_target=None is a
    malformed antecedent, never fireable. Not expected on any real rule
    (all typed-relationship rules declare a relation_target), but the
    classifier must handle it explicitly rather than falling through."""
    result = classify_antecedent("Line of Fate", "stopped_by", None, None)
    assert result["status"] == "UNEMITTABLE"
    assert "relation_target" in result["detail"]


def test_old_directional_attributes_unaffected_by_s113_no_regression():
    """Position/Starting_Point (the OLD ORIGIN/TERMINATION directional
    channel) must still classify exactly as before -- the S113 fix only
    intercepts oe._RELATIONSHIP_TOKENS, never touches this path."""
    result = classify_antecedent("Line of Fate", "Position", None, "Mount of Saturn")
    assert result["status"] == "yes"
    assert "TERMINATION" in result["detail"]
