"""
tests/interpretive/test_provenance.py

Tests for agent/interpretive/provenance.py (S121 governance #1) -- the
structured-provenance parser and its G1-G8 consistency checks.

HARDEST CASE FIRST (Working Style #3): the lead test is not a synthetic
happy path, it is the REAL known-stale defect. `test_g1_catches_the_known_
stale_ft_001_binding` reconstructs FT_001/FT_009 exactly as they stand at
HEAD e982a92 -- antecedent `Depth = deep` (migrated by S121 #5A) against a
binding still naming `well_marked` (what the prose flag still says today)
-- and proves G1 fires. That is the whole point of the module, so it is
the test that must not be allowed to rot.

The companion test right below it is the one that shows why G1 is not
redundant with any gate we already have: the reachability oracle returns
status "yes" for `well_marked`, because the token IS still a legal member
of the flat `depth_values` pool. It is a WRONG token, not a DANGLING one.
No existing check in the codebase can see that; G1 can.

The module is ADDITIVE and unwired -- nothing imports it in production, no
rule file carries a `provenance` key yet, and no CI gate runs these checks.
These tests are therefore the only thing exercising it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agent.interpretive.provenance import (
    BLOCKER_KINDS,
    Provenance,
    ProvenanceError,
    ProvenanceStatus,
    TokenBinding,
    check_g1,
    check_g2,
    check_g3,
    check_g4,
    check_g5,
    check_g6,
    check_g7,
    check_g8,
    is_git_tracked,
    parse_provenance,
    validate_provenance,
    validate_rule,
)

# ─── fixtures ───────────────────────────────────────────────────────────

# A real, currently-passing shape: FT_001's two antecedents as they stand
# at HEAD e982a92, with a provenance block that correctly names the LIVE
# tokens and records the well_marked -> deep migration in `superseded`.
# Both antecedents are oracle-reachable ("yes"), so `reachability: "pass"`
# is the truthful declaration.
_VALID_RULE = {
    "rule_id": "FT_001",
    "source_page": 103,
    "source_quote": (
        "When the line of fate is strong and rises from the line of life, "
        "it denotes that success will be won by personal merit."
    ),
    "antecedents": [
        {
            "feature": "Line of Fate",
            "attribute": "Starting_Point",
            "value": None,
            "condition_type": "standard",
            "comparator": None,
            "comparator_feature": None,
            "relation_target": "Line of Life",
        },
        {
            "feature": "Line of Fate",
            "attribute": "Depth",
            "value": "deep",
            "condition_type": "standard",
            "comparator": None,
            "comparator_feature": None,
        },
    ],
    "provenance": {
        "token_bindings": [
            {
                "antecedent_index": 1,
                "bound_field": "value",
                "chosen_token": "deep",
                "attribute": "Depth",
                "binding_kind": "proxy",
                "source_phrase": "is strong",
                "authority": "S121 #5A",
                "superseded": [
                    {
                        "chosen_token": "well_marked",
                        "attribute": "Depth",
                        "authority": "S121 #5A",
                        "reason": "registry-legal but not emittable; canonical-vocab migration",
                    }
                ],
            }
        ],
        "status": {
            "fireable": True,
            "reachability": "pass",
            "reachability_authority": "S121",
            "vision_emission": "unproven",
            "vision_evidence": None,
            "blocked_on": [],
        },
        "caveats": [
            {
                "kind": "proxy_mapping",
                "note": "source says 'is strong'; no literal 'strong' token exists in any value pool",
                "human_ruling": None,
            }
        ],
        "notes": [
            "CROSS-LINE INDEX: this statement also belongs in _doctrine/cross_line_index.md"
        ],
    },
}


def _rule_with_provenance(provenance: dict) -> dict:
    """A copy of _VALID_RULE carrying a different provenance block."""
    rule = {k: v for k, v in _VALID_RULE.items() if k != "provenance"}
    rule["provenance"] = provenance
    return rule


def _binding(**overrides) -> dict:
    base = {
        "antecedent_index": 1,
        "bound_field": "value",
        "chosen_token": "deep",
        "attribute": "Depth",
        "binding_kind": "literal",
    }
    base.update(overrides)
    return base


# ─── HARDEST CASE: the real, currently-live defect ──────────────────────


def test_g1_catches_the_known_stale_ft_001_binding():
    """THE test. FT_001/FT_009 at HEAD e982a92 carry an antecedent of
    Depth=deep while their prose flag still says 'mapped to
    Depth=well_marked'. Prove G1 would have failed the moment #5A landed."""
    stale = _rule_with_provenance(
        {"token_bindings": [_binding(chosen_token="well_marked")]}
    )
    provenance = parse_provenance(stale)
    violations = check_g1(stale, provenance)

    assert len(violations) == 1, violations
    assert "G1" in violations[0]
    assert "well_marked" in violations[0]
    assert "deep" in violations[0]

    # And it surfaces through the aggregate entry point, not only the
    # individual check -- a violation that only a direct check call can
    # see would never reach a gate.
    assert any(v.startswith("G1 FT_001") for v in validate_rule(stale))


def test_g1_catches_what_the_reachability_oracle_cannot():
    """Why G1 is not redundant. `well_marked` is still a legal member of
    the flat depth_values pool, so the existing reachability scan calls it
    reachable -- it is a WRONG token, not a DANGLING one. No pre-existing
    check in the codebase can see this class of defect."""
    from scripts.vocab_reachability_scan import classify_antecedent

    verdict = classify_antecedent("Line of Fate", "Depth", "well_marked", None)
    assert verdict["status"] == "yes", (
        "premise of this test changed: well_marked is no longer registry-legal, "
        "so the 'wrong-but-legal token' case needs a new example"
    )

    stale = _rule_with_provenance(
        {"token_bindings": [_binding(chosen_token="well_marked")]}
    )
    assert check_g1(stale, parse_provenance(stale)), (
        "G1 must catch a token the reachability oracle passes"
    )


# ─── the valid case passes every check ──────────────────────────────────


def test_valid_provenance_passes_all_of_g1_to_g8():
    provenance = parse_provenance(_VALID_RULE)
    assert provenance is not None
    assert validate_provenance(_VALID_RULE, provenance) == []


def test_valid_provenance_parses_into_typed_structures():
    provenance = parse_provenance(_VALID_RULE)

    assert isinstance(provenance, Provenance)
    assert len(provenance.token_bindings) == 1
    binding = provenance.token_bindings[0]
    assert isinstance(binding, TokenBinding)
    assert binding.antecedent_index == 1
    assert binding.bound_field == "value"
    assert binding.chosen_token == "deep"
    assert binding.binding_kind == "proxy"
    assert binding.source_phrase == "is strong"
    assert len(binding.superseded) == 1
    assert binding.superseded[0].chosen_token == "well_marked"

    assert isinstance(provenance.status, ProvenanceStatus)
    assert provenance.status.fireable is True
    assert provenance.status.reachability == "pass"
    assert provenance.status.vision_emission == "unproven"

    assert len(provenance.caveats) == 1
    assert provenance.caveats[0].kind == "proxy_mapping"
    assert len(provenance.notes) == 1


# ─── absent provenance ──────────────────────────────────────────────────


def test_absent_provenance_key_returns_none_and_no_violations():
    """41 of the 102 flag-bearing rules hold an empty schema_flags list
    today; those must migrate to an ABSENT provenance key, not a populated
    skeleton. Absence is a valid, complete state."""
    rule = {k: v for k, v in _VALID_RULE.items() if k != "provenance"}
    assert parse_provenance(rule) is None
    assert validate_rule(rule) == []


def test_explicit_null_provenance_is_also_absent():
    rule = _rule_with_provenance(None)
    assert parse_provenance(rule) is None
    assert validate_rule(rule) == []


def test_empty_provenance_object_parses_and_passes():
    rule = _rule_with_provenance({})
    provenance = parse_provenance(rule)
    assert provenance is not None
    assert provenance.token_bindings == ()
    assert provenance.status is None
    assert validate_provenance(rule, provenance) == []


# ─── G2 ─────────────────────────────────────────────────────────────────


def test_g2_flags_attribute_mismatch():
    rule = _rule_with_provenance(
        {"token_bindings": [_binding(attribute="Continuity")]}
    )
    violations = check_g2(rule, parse_provenance(rule))
    assert len(violations) == 1
    assert "Continuity" in violations[0] and "Depth" in violations[0]


def test_g2_skips_a_binding_that_declares_no_attribute():
    raw = _binding()
    del raw["attribute"]
    rule = _rule_with_provenance({"token_bindings": [raw]})
    assert check_g2(rule, parse_provenance(rule)) == []


# ─── G3 ─────────────────────────────────────────────────────────────────


def test_g3_flags_a_superseded_entry_naming_the_live_token():
    """A half-applied migration: the ledger retires the token the rule
    still fires on."""
    rule = _rule_with_provenance(
        {
            "token_bindings": [
                _binding(superseded=[{"chosen_token": "deep", "authority": "S121"}])
            ]
        }
    )
    violations = check_g3(rule, parse_provenance(rule))
    assert len(violations) == 1
    assert "half-applied migration" in violations[0]


def test_g3_accepts_a_ledger_naming_only_retired_tokens():
    assert check_g3(_VALID_RULE, parse_provenance(_VALID_RULE)) == []


# ─── G4 ─────────────────────────────────────────────────────────────────


def test_g4_flags_an_unresolvable_antecedent_index():
    rule = _rule_with_provenance({"token_bindings": [_binding(antecedent_index=7)]})
    violations = check_g4(rule, parse_provenance(rule))
    assert len(violations) == 1
    assert "does not resolve" in violations[0]


def test_g4_flags_duplicate_binding_for_same_index_and_field():
    rule = _rule_with_provenance({"token_bindings": [_binding(), _binding()]})
    violations = check_g4(rule, parse_provenance(rule))
    assert len(violations) == 1
    assert "duplicate token_binding" in violations[0]


def test_g4_allows_two_bindings_on_different_fields_of_one_antecedent():
    rule = _rule_with_provenance(
        {
            "token_bindings": [
                _binding(),
                _binding(bound_field="attribute", chosen_token="Depth"),
            ]
        }
    )
    assert check_g4(rule, parse_provenance(rule)) == []


def test_g1_skips_a_binding_g4_already_reported_as_unresolvable():
    """No double-reporting: one defect, one violation."""
    rule = _rule_with_provenance({"token_bindings": [_binding(antecedent_index=7)]})
    provenance = parse_provenance(rule)
    assert check_g1(rule, provenance) == []
    assert len(check_g4(rule, provenance)) == 1


# ─── G5 ─────────────────────────────────────────────────────────────────


def test_g5_flags_proxy_source_phrase_absent_from_source_quote():
    rule = _rule_with_provenance(
        {
            "token_bindings": [
                _binding(binding_kind="proxy", source_phrase="deeply engraved")
            ]
        }
    )
    violations = check_g5(rule, parse_provenance(rule))
    assert len(violations) == 1
    assert "does not appear in the rule's source_quote" in violations[0]


def test_g5_accepts_a_proxy_phrase_that_is_really_in_the_quote():
    assert check_g5(_VALID_RULE, parse_provenance(_VALID_RULE)) == []


def test_g5_normalization_tolerates_case_and_whitespace():
    """G5 reuses gate_rule_citations.normalize, so an authored phrase
    differing only in case or internal whitespace still matches -- the
    same tolerance that gate applies to corpus quotes."""
    rule = _rule_with_provenance(
        {
            "token_bindings": [
                _binding(binding_kind="proxy", source_phrase="IS   Strong")
            ]
        }
    )
    assert check_g5(rule, parse_provenance(rule)) == []


def test_g5_flags_a_proxy_binding_with_no_source_phrase():
    rule = _rule_with_provenance({"token_bindings": [_binding(binding_kind="proxy")]})
    violations = check_g5(rule, parse_provenance(rule))
    assert len(violations) == 1
    assert "no source_phrase" in violations[0]


def test_g5_ignores_non_proxy_bindings():
    rule = _rule_with_provenance(
        {
            "token_bindings": [
                _binding(binding_kind="literal", source_phrase="not in the quote at all")
            ]
        }
    )
    assert check_g5(rule, parse_provenance(rule)) == []


# ─── G6 ─────────────────────────────────────────────────────────────────


def test_g6_flags_fireable_true_with_reachability_fail():
    """The declared self-consistency half: a rule cannot claim to be
    fireable while declaring its own vocabulary unreachable."""
    rule = _rule_with_provenance(
        {
            "token_bindings": [],
            "status": {"fireable": True, "reachability": "fail"},
        }
    )
    violations = check_g6(rule, parse_provenance(rule))
    assert any(
        "fireable is true but status.reachability is 'fail'" in v for v in violations
    ), violations


def test_g6_flags_fireable_true_with_reachability_unemittable():
    rule = _rule_with_provenance(
        {"status": {"fireable": True, "reachability": "unemittable"}}
    )
    violations = check_g6(rule, parse_provenance(rule))
    assert any("unemittable" in v for v in violations), violations


def test_g6_flags_a_declared_pass_the_oracle_contradicts():
    """The oracle-agreement half. Without it, the declared check is prose
    checking prose -- a rule could declare 'pass' forever while its tokens
    were unreachable. Oracle injected so the check logic is proven in
    isolation from the scan's own verdicts."""

    def unreachable_oracle(feature, attribute, value, relation_target):
        return {"status": "UNEMITTABLE", "detail": "stub: relation attr not emitted"}

    rule = _rule_with_provenance(
        {"status": {"fireable": True, "reachability": "pass"}}
    )
    violations = check_g6(rule, parse_provenance(rule), oracle=unreachable_oracle)
    assert len(violations) == 1
    assert "oracle says 'unemittable'" in violations[0]


def test_g6_accepts_a_declared_pass_the_real_oracle_agrees_with():
    """Oracle-backed, no stub: both of FT_001's real antecedents classify
    'yes' against the live scan, so 'pass' is truthful."""
    assert check_g6(_VALID_RULE, parse_provenance(_VALID_RULE)) == []


def test_g6_skips_the_oracle_when_reachability_is_unchecked():
    def exploding_oracle(*_args):
        raise AssertionError("oracle must not be called for reachability='unchecked'")

    rule = _rule_with_provenance(
        {"status": {"fireable": False, "reachability": "unchecked"}}
    )
    assert check_g6(rule, parse_provenance(rule), oracle=exploding_oracle) == []


def test_g6_reports_an_oracle_failure_rather_than_passing():
    """An oracle that raises must not read as a clean pass."""

    def broken_oracle(*_args):
        raise RuntimeError("registry unavailable")

    rule = _rule_with_provenance(
        {"status": {"fireable": True, "reachability": "pass"}}
    )
    violations = check_g6(rule, parse_provenance(rule), oracle=broken_oracle)
    assert len(violations) == 1
    assert "oracle raised" in violations[0]


def test_g6_is_a_no_op_without_a_status_block():
    rule = _rule_with_provenance({"token_bindings": [_binding()]})
    assert check_g6(rule, parse_provenance(rule)) == []


# ─── G7 ─────────────────────────────────────────────────────────────────


def test_g7_flags_confirmed_emission_backed_by_an_untracked_file(tmp_path):
    """M_001's exact situation: venus_grade_probe_S119_raw.json shows 6/6
    confirmed Venus emission, but the file is untracked, so per Working
    Style #16 it cannot yet close the flag."""
    evidence = tmp_path / "untracked_probe_raw.json"
    evidence.write_text("{}", encoding="utf-8")

    rule = _rule_with_provenance(
        {
            "status": {
                "vision_emission": "confirmed",
                "vision_evidence": evidence.name,
            }
        }
    )
    violations = check_g7(
        rule,
        parse_provenance(rule),
        is_tracked=lambda _p: False,
        repo_root=tmp_path,
    )
    assert len(violations) == 1
    assert "NOT git-tracked" in violations[0]


def test_g7_flags_confirmed_emission_with_a_missing_file(tmp_path):
    rule = _rule_with_provenance(
        {
            "status": {
                "vision_emission": "confirmed",
                "vision_evidence": "diagnostics/does_not_exist.json",
            }
        }
    )
    violations = check_g7(
        rule, parse_provenance(rule), is_tracked=lambda _p: True, repo_root=tmp_path
    )
    assert len(violations) == 1
    assert "does not exist" in violations[0]


def test_g7_flags_confirmed_emission_with_no_evidence_path():
    rule = _rule_with_provenance({"status": {"vision_emission": "confirmed"}})
    violations = check_g7(rule, parse_provenance(rule))
    assert len(violations) == 1
    assert "no vision_evidence path" in violations[0]


def test_g7_accepts_confirmed_emission_backed_by_a_tracked_file():
    """Oracle-backed with the REAL git check, against a file that is
    genuinely tracked at HEAD."""
    rule = _rule_with_provenance(
        {
            "status": {
                "vision_emission": "confirmed",
                "vision_evidence": "data/ontology_registry.json",
            }
        }
    )
    assert check_g7(rule, parse_provenance(rule)) == []


def test_g7_is_a_no_op_for_unproven_emission():
    assert check_g7(_VALID_RULE, parse_provenance(_VALID_RULE)) == []


def test_is_git_tracked_agrees_with_git_on_a_known_tracked_file():
    assert is_git_tracked("data/ontology_registry.json") is True
    assert is_git_tracked("diagnostics/no_such_file_anywhere.json") is False


# ─── G8 ─────────────────────────────────────────────────────────────────


def test_g8_accepts_a_blocker_naming_a_genuinely_absent_token():
    """H_011's real blocker: `hand_side` is genuinely absent from the
    attributes registry."""
    rule = _rule_with_provenance(
        {"status": {"blocked_on": ["ontology:attribute:hand_side"]}}
    )
    assert check_g8(rule, parse_provenance(rule)) == []


def test_g8_flags_a_stale_blocker_whose_token_now_exists():
    """The self-clearing property: once the ontology gains the token, the
    blocker fails loudly instead of sitting there stale forever."""
    rule = _rule_with_provenance(
        {"status": {"blocked_on": ["ontology:attribute:Depth"]}}
    )
    violations = check_g8(rule, parse_provenance(rule))
    assert len(violations) == 1
    assert "blocker is stale" in violations[0]


def test_g8_flags_an_unparseable_blocker():
    rule = _rule_with_provenance({"status": {"blocked_on": ["Presence is missing"]}})
    violations = check_g8(rule, parse_provenance(rule))
    assert len(violations) == 1
    assert "does not parse" in violations[0]


def test_g8_flags_an_unknown_blocker_kind():
    rule = _rule_with_provenance({"status": {"blocked_on": ["ontology:widget:foo"]}})
    violations = check_g8(rule, parse_provenance(rule))
    assert len(violations) == 1
    assert "unknown kind" in violations[0]


@pytest.mark.parametrize("kind", sorted(BLOCKER_KINDS))
def test_g8_every_blocker_kind_is_registry_backed(kind):
    """No unfalsifiable blocker kinds: each must resolve against a real
    registry collection, so a nonsense token reads as absent (valid) and a
    real one reads as stale."""
    rule = _rule_with_provenance(
        {"status": {"blocked_on": [f"ontology:{kind}:__definitely_not_a_real_token__"]}}
    )
    assert check_g8(rule, parse_provenance(rule)) == []


def test_g8_flags_stale_blockers_across_every_kind():
    rule = _rule_with_provenance(
        {
            "status": {
                "blocked_on": [
                    "ontology:feature:Line of Fate",
                    "ontology:attribute:Depth",
                    "ontology:value:deep",
                    "ontology:relation_target:Line of Life",
                ]
            }
        }
    )
    violations = check_g8(rule, parse_provenance(rule))
    assert len(violations) == 4, violations
    assert all("blocker is stale" in v for v in violations)


# ─── malformed provenance raises, never silently passes ─────────────────


@pytest.mark.parametrize(
    "provenance, fragment",
    [
        ({"token_bindings": "not a list"}, "must be an array"),
        ({"token_bindings": [{"bound_field": "value", "chosen_token": "deep"}]}, "antecedent_index"),
        ({"token_bindings": [_binding(antecedent_index=True)]}, "antecedent_index"),
        ({"token_bindings": [_binding(bound_field="colour")]}, "bound_field"),
        ({"token_bindings": [_binding(binding_kind="guess")]}, "binding_kind"),
        ({"token_bindings": [_binding(chosen_token="")]}, "chosen_token"),
        ({"status": {"reachability": "maybe"}}, "reachability"),
        ({"status": {"vision_emission": "probably"}}, "vision_emission"),
        ({"status": {"fireable": "yes"}}, "fireable"),
        ({"status": {"blocked_on": "ontology:attribute:x"}}, "blocked_on"),
        ({"caveats": [{"kind": "vibes", "note": "n"}]}, "kind"),
        ({"caveats": [{"kind": "proxy_mapping"}]}, "note"),
        ({"notes": [42]}, "notes"),
        ({"status": []}, "must be an object"),
    ],
)
def test_malformed_provenance_raises_provenance_error(provenance, fragment):
    rule = _rule_with_provenance(provenance)
    with pytest.raises(ProvenanceError) as exc:
        parse_provenance(rule)
    assert fragment in str(exc.value)


def test_violation_and_malformed_are_different_channels():
    """A violation is returned as a string; a malformed block raises. The
    two failures are not collapsed into one channel."""
    stale = _rule_with_provenance(
        {"token_bindings": [_binding(chosen_token="well_marked")]}
    )
    assert validate_rule(stale)  # returns, does not raise

    with pytest.raises(ProvenanceError):
        validate_rule(_rule_with_provenance({"token_bindings": [{"bogus": 1}]}))


# ─── additive-only guard ────────────────────────────────────────────────


def test_module_is_not_yet_wired_into_any_rule_file():
    """This task is additive: no rule file carries a `provenance` key yet.
    When migration begins this test is the one to update deliberately --
    it must not be allowed to fail silently in between."""
    import json

    rules_dir = Path(__file__).resolve().parents[2] / "data" / "palm_rules"
    carriers = []
    for path in sorted(rules_dir.glob("palm_rules_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for section in data.values():
            if not isinstance(section, list):
                continue
            for rule in section:
                if isinstance(rule, dict) and "provenance" in rule:
                    carriers.append(f"{path.name}:{rule.get('rule_id')}")
    assert carriers == [], (
        "rules now carry a `provenance` key -- governance #1 was additive-only; "
        f"update this test alongside the migration step: {carriers}"
    )


def test_every_rule_file_still_parses_as_no_provenance():
    """Corollary: validate_rule over every live rule is a clean no-op
    today, so wiring the gate cannot fail on day one for a reason
    unrelated to a real defect."""
    import json

    rules_dir = Path(__file__).resolve().parents[2] / "data" / "palm_rules"
    checked = 0
    for path in sorted(rules_dir.glob("palm_rules_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for section in data.values():
            if not isinstance(section, list):
                continue
            for rule in section:
                if not isinstance(rule, dict) or "rule_id" not in rule:
                    continue
                assert parse_provenance(rule) is None
                assert validate_rule(rule) == []
                checked += 1
    assert checked > 100, f"expected the full rule population, scanned only {checked}"
