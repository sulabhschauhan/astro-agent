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
