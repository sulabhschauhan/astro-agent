"""
tests/interpretive/test_vocab_reachability_scan.py
Regression test for scripts/vocab_reachability_scan.py's classify_antecedent()
UNEMITTABLE gate (S97): an antecedent with a non-null relation_target on an
attribute _RELATIONAL_ATTRIBUTE_MAP never emits through the relational parse
channel is registry-legal but permanently unfireable -- the Ending_Point/
Position dead-rule bug that real-hand dogfood caught live (see
diagnostics/latest_run.md S97, commit f1335c1). This gate makes that bug
class a mechanical, pre-dogfood check instead of a live-hand discovery.
"""

from __future__ import annotations

from scripts.vocab_reachability_scan import classify_antecedent


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
