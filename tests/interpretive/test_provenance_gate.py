"""
tests/interpretive/test_provenance_gate.py

THE SUITE-BLOCKING PROVENANCE GATE (S121 governance #2). Wires the
governance-#1 validator (agent/interpretive/provenance.py, committed at
e7660d2) into CI over every rule in every data/palm_rules/palm_rules_*.json.

=== BINDING CI DEPENDENCY (read before touching this file) ===

This gate is the ONLY mechanism that keeps rule provenance honest. It is
the direct descendant of the S119 INVARIANT 2 argument for
scripts/gate_rule_citations.py, and it carries the same condition:

    IT MUST REMAIN SUITE-ENFORCED. Never advisory, never skipped, never
    downgraded to a warning.

If it is removed or weakened, `provenance` blocks revert to unverified
assertions and the FT_001-class drift returns silently -- prose claiming a
binding the antecedent no longer carries, invisible to every other check
in the codebase. Any change that touches this file must state that
dependency explicitly.

=== THE THREE ASSERTIONS ===

1. CONSISTENCY -- every rule that HAS a `provenance` key passes G1-G8
   (validate_rule, imported and CALLED; never reimplemented here).
   A no-op today: no rule carries provenance yet. It becomes the load-
   bearing check the moment migration starts.

2. COVERAGE -- every rule with a NON-EMPTY `schema_flags` and NO
   `provenance` key must appear in the frozen baseline. This is what gives
   the gate teeth BEFORE any migration: a rule that owes provenance and is
   neither migrated nor baselined fails CI.

3. SHRINK-ONLY -- the baseline is an allowlist that may only LOSE entries.
     - a baseline entry whose rule has already gained `provenance` FAILS
       ("stale baseline entry -- remove it"), forcing the baseline to
       shrink as migration proceeds;
     - a baseline rule_id that no longer exists anywhere FAILS.

   WHY GROWTH IS PREVENTED STRUCTURALLY, and where the discipline actually
   lives: assertion 2 is the ONLY thing that reads the baseline. So a NEW
   un-migrated rule carrying schema_flags has exactly one way to make this
   gate pass -- being ADDED to the baseline. There is no mechanical bar to
   that; the bar is HUMAN REVIEW, which must reject any diff that grows
   data/provenance_baseline.json. A growing baseline is the failure mode
   this gate cannot self-detect, and it is the one thing a reviewer of
   this file's diff must look for. The failure messages below say so
   out loud, because a reviewer meets them before they meet this comment.

G9 is ADVISORY here (census §4a): it warns, it never fails. See
`g9_advisory_scan`.

=== BASELINE PROVENANCE ===

data/provenance_baseline.json was SEEDED (never hand-typed) by parsing the
rule files for rules with a non-empty `schema_flags` and no `provenance`:

    ids = {r["rule_id"] for f in glob("data/palm_rules/palm_rules_*.json")
           for section in json.load(open(f)).values() if isinstance(section, list)
           for r in section if isinstance(r, dict)
           and r.get("schema_flags") and "provenance" not in r}

61 ids, matching the S121 census exactly (fate 15, head_heart 21, life 1,
mounts 24 -- 102 rules carry the schema_flags key, 41 of them empty).
`test_baseline_matches_a_fresh_derivation` re-derives it on every run, so
the seed cannot silently drift from its own definition.
"""

from __future__ import annotations

import json
import re
import warnings
from pathlib import Path

import pytest

from agent.interpretive.provenance import (
    ProvenanceError,
    parse_provenance,
    validate_rule,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_RULES_DIR = _REPO_ROOT / "data" / "palm_rules"
_RULES_GLOB = "palm_rules_*.json"
_BASELINE_PATH = _REPO_ROOT / "data" / "provenance_baseline.json"
_REGISTRY_PATH = _REPO_ROOT / "data" / "ontology_registry.json"

# Shown verbatim in every coverage/shrink failure. A reviewer hits this
# text before they ever open this file's docstring.
_DISCIPLINE = (
    "\n    DISCIPLINE: the baseline is SHRINK-ONLY. Adding an id to "
    "data/provenance_baseline.json\n    to make this gate pass is NOT the fix and "
    "must be rejected in review -- migrate the\n    rule to a structured `provenance` "
    "block instead."
)


# ─── loading ────────────────────────────────────────────────────────────


def _load_all_rules() -> list[tuple[str, str, dict]]:
    """Every rule in every rule file, as (filename, section, rule).

    ALL sections -- validated_candidates, parked_pending,
    parked_pending_relation_target, retired_superseded. A retired or parked
    rule still carries schema_flags and still owes provenance; scoping the
    gate to validated_candidates only would silently exempt 32 of the 119
    rules, including 15 of the 61 the baseline covers."""
    out: list[tuple[str, str, dict]] = []
    paths = sorted(_RULES_DIR.glob(_RULES_GLOB))
    assert paths, f"no rule files matched {_RULES_DIR / _RULES_GLOB}"
    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - corrupt repo
            pytest.fail(f"{path.name} is not valid JSON: {exc}")
        for section, entries in data.items():
            if not isinstance(entries, list):
                continue
            for rule in entries:
                if isinstance(rule, dict) and "rule_id" in rule:
                    out.append((path.name, section, rule))
    return out


def _load_baseline() -> list[str]:
    try:
        raw = json.loads(_BASELINE_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:  # pragma: no cover - repo integrity
        pytest.fail(f"frozen baseline missing at {_BASELINE_PATH}")
    except json.JSONDecodeError as exc:  # pragma: no cover
        pytest.fail(f"{_BASELINE_PATH.name} is not valid JSON: {exc}")
    assert isinstance(raw, list), (
        f"{_BASELINE_PATH.name} must be a JSON array of rule_ids, got {type(raw).__name__}"
    )
    for i, entry in enumerate(raw):
        assert isinstance(entry, str) and entry, (
            f"{_BASELINE_PATH.name}[{i}] must be a non-empty string, got {entry!r}"
        )
    return raw


_ALL_RULES = _load_all_rules()
_BASELINE = _load_baseline()


def _owes_provenance(rule: dict) -> bool:
    """A rule owes provenance when it carries a NON-EMPTY schema_flags and
    has not yet been migrated. An empty `schema_flags: []` owes nothing --
    those 41 rules migrate to an ABSENT provenance key, never a skeleton."""
    return bool(rule.get("schema_flags")) and "provenance" not in rule


# ─── ASSERTION 1: CONSISTENCY (hard fail) ───────────────────────────────


def test_assertion_1_every_provenance_bearing_rule_passes_g1_to_g8():
    """Every rule with a `provenance` key satisfies G1-G8.

    A no-op today (no rule carries provenance). It becomes load-bearing at
    the first migration -- and it is what would have caught FT_001 the
    instant e982a92 landed."""
    failures: list[str] = []
    checked = 0
    for filename, section, rule in _ALL_RULES:
        if "provenance" not in rule:
            continue
        checked += 1
        where = f"{filename}:{section}:{rule['rule_id']}"
        try:
            violations = validate_rule(rule)
        except ProvenanceError as exc:
            # A malformed block is a different failure from an inconsistent
            # one; report it as a clear gate failure rather than letting a
            # raw traceback escape.
            failures.append(f"{where}: MALFORMED provenance -- {exc}")
            continue
        failures.extend(f"{where}: {v}" for v in violations)

    assert not failures, (
        f"{len(failures)} provenance consistency violation(s) across "
        f"{checked} provenance-bearing rule(s):\n  " + "\n  ".join(failures)
    )


# ─── ASSERTION 2: COVERAGE (hard fail) ──────────────────────────────────


def test_assertion_2_every_rule_owing_provenance_is_migrated_or_baselined():
    """A rule with non-empty schema_flags and no provenance must be in the
    frozen baseline. Neither migrated nor baselined = FAIL.

    This is the assertion that gives the gate teeth today, before any
    migration exists."""
    baseline = set(_BASELINE)
    unaccounted = [
        f"{filename}:{section}:{rule['rule_id']}"
        for filename, section, rule in _ALL_RULES
        if _owes_provenance(rule) and rule["rule_id"] not in baseline
    ]
    assert not unaccounted, (
        f"{len(unaccounted)} rule(s) carry a non-empty `schema_flags` but have neither a "
        f"structured `provenance` block nor a baseline entry:\n  "
        + "\n  ".join(unaccounted)
        + _DISCIPLINE
    )


# ─── ASSERTION 3: SHRINK-ONLY (hard fail) ───────────────────────────────


def test_assertion_3a_no_stale_baseline_entry_for_a_migrated_rule():
    """A baselined rule that has ALREADY gained `provenance` must be
    removed from the baseline. This is the mechanism that forces the
    baseline to shrink as migration proceeds -- without it, a fully
    migrated corpus could still carry all 61 original entries."""
    by_id = {rule["rule_id"]: rule for _f, _s, rule in _ALL_RULES}
    stale = [
        rule_id
        for rule_id in _BASELINE
        if rule_id in by_id and "provenance" in by_id[rule_id]
    ]
    assert not stale, (
        f"{len(stale)} stale baseline entr(ies) -- these rules now carry a structured "
        f"`provenance` block, so they must be REMOVED from "
        f"{_BASELINE_PATH.name}:\n  " + "\n  ".join(sorted(stale))
    )


def test_assertion_3b_every_baseline_id_still_exists():
    """A baseline id naming a rule that no longer exists anywhere is dead
    weight that would silently mask a re-added rule later."""
    known = {rule["rule_id"] for _f, _s, rule in _ALL_RULES}
    missing = [rule_id for rule_id in _BASELINE if rule_id not in known]
    assert not missing, (
        f"{len(missing)} baseline entr(ies) name rule_ids that exist in no rule file "
        f"-- remove them from {_BASELINE_PATH.name}:\n  " + "\n  ".join(sorted(missing))
    )


def test_assertion_3c_baseline_has_no_duplicates():
    """A duplicated id would let one removal look like progress while the
    rule stayed allowlisted."""
    seen: set[str] = set()
    dupes = sorted({r for r in _BASELINE if r in seen or seen.add(r)})  # type: ignore[func-returns-value]
    assert not dupes, f"duplicate baseline entries: {dupes}"


# ─── baseline integrity ─────────────────────────────────────────────────


def test_baseline_matches_a_fresh_derivation():
    """The seed cannot silently drift from its own definition: re-derive
    the owes-provenance set and compare. Any legitimate divergence means a
    migration landed, and then assertion 3a is the check that fires."""
    derived = {
        rule["rule_id"] for _f, _s, rule in _ALL_RULES if _owes_provenance(rule)
    }
    baseline = set(_BASELINE)
    only_derived = sorted(derived - baseline)
    only_baseline = sorted(baseline - derived)
    assert not only_derived, (
        f"rules owe provenance but are absent from the baseline: {only_derived}"
        + _DISCIPLINE
    )
    assert not only_baseline, (
        f"baseline entries no longer owe provenance (migrated, or schema_flags emptied) "
        f"-- remove them: {only_baseline}"
    )


def test_baseline_is_sorted_and_deterministic():
    """Sorted on disk so a diff shows a real change, never a reordering."""
    assert _BASELINE == sorted(_BASELINE), (
        f"{_BASELINE_PATH.name} must be sorted -- run sorted() over it"
    )


def test_rule_ids_are_globally_unique():
    """The baseline is a flat array of bare rule_ids, which is only
    unambiguous while ids are unique across every file and section.
    Verified at authoring time (119 rules, 0 duplicates); pinned here
    because a future duplicate would silently make baseline entries
    ambiguous rather than failing."""
    seen: dict[str, str] = {}
    collisions: list[str] = []
    for filename, section, rule in _ALL_RULES:
        rid = rule["rule_id"]
        where = f"{filename}:{section}"
        if rid in seen:
            collisions.append(f"{rid} in both {seen[rid]} and {where}")
        seen[rid] = where
    assert not collisions, (
        "rule_ids are no longer globally unique, so a flat-array baseline is ambiguous:\n  "
        + "\n  ".join(collisions)
    )


# ─── G9: ADVISORY ONLY (warns, never fails) ─────────────────────────────


def _registry_tokens() -> set[str]:
    registry = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    attributes = {a for group in registry["attributes"].values() for a in group}
    values = {v for pool in registry["values"].values() for v in pool}
    return attributes | values


def g9_advisory_scan(rules: list[tuple[str, str, dict]]) -> list[str]:
    """G9 (census §4a): flag any `provenance.notes` string containing a
    registry attribute name or value-pool member -- class-D prose silently
    re-acquiring token coupling.

    ADVISORY BY DESIGN, and it must stay that way until measured: 88 of the
    217 value-pool tokens are ordinary English words ('clear', 'deep',
    'full', 'long', 'low', 'close', 'even', 'light'), so a perfectly
    legitimate prose note will match one. Promoting this to a hard failure
    without first measuring the false-positive rate over real migrated
    notes would block honest prose. Word-boundary matched to keep the noise
    down; underscored tokens are matched literally.

    If G9 is ever promoted to hard, it belongs in provenance.py alongside
    G1-G8, not here."""
    tokens = _registry_tokens()
    patterns = [
        (tok, re.compile(rf"\b{re.escape(tok)}\b", re.IGNORECASE)) for tok in tokens
    ]
    advisories: list[str] = []
    for filename, section, rule in rules:
        try:
            provenance = parse_provenance(rule)
        except ProvenanceError:
            continue  # assertion 1 owns malformed blocks
        if provenance is None:
            continue
        for i, note in enumerate(provenance.notes):
            hits = sorted({tok for tok, pat in patterns if pat.search(note)})
            if hits:
                advisories.append(
                    f"{filename}:{section}:{rule['rule_id']} notes[{i}] contains "
                    f"registry token(s) {hits}: {note[:120]!r}"
                )
    return advisories


def test_g9_advisory_never_fails_the_suite():
    """G9 warns; it does not assert. Empty today -- no rule carries a
    `provenance` block, so there are no notes to scan. The check is
    exercised against synthetic input below so it is not merely vacuous."""
    advisories = g9_advisory_scan(_ALL_RULES)
    if advisories:
        warnings.warn(
            "G9 ADVISORY (not a failure) -- class-D notes contain registry tokens:\n  "
            + "\n  ".join(advisories),
            UserWarning,
            stacklevel=2,
        )
    # Deliberately no assertion on `advisories`: this check is advisory.
    assert isinstance(advisories, list)


def test_g9_detects_a_token_bearing_note_on_synthetic_input():
    """Proves G9 works, since the live corpus gives it nothing to find."""
    rule = {
        "rule_id": "SYNTHETIC_G9",
        "antecedents": [],
        "provenance": {
            "notes": ["MODIFIER-FOLD: the Depth reading is folded into claim prose"]
        },
    }
    advisories = g9_advisory_scan([("synthetic.json", "validated_candidates", rule)])
    assert len(advisories) == 1
    assert "Depth" in advisories[0]


def test_g9_ignores_a_note_with_no_registry_token():
    rule = {
        "rule_id": "SYNTHETIC_G9_CLEAN",
        "antecedents": [],
        "provenance": {
            "notes": ["CROSS-LINE INDEX: this statement belongs in cross_line_index.md"]
        },
    }
    assert g9_advisory_scan([("synthetic.json", "validated_candidates", rule)]) == []


# ─── the gate's own teeth (proves each assertion can actually fail) ─────
#
# A gate nobody has seen fail is a gate nobody knows works. Each of these
# drives the assertion's own predicate over a synthetic corpus.


def test_coverage_predicate_catches_an_unaccounted_rule():
    rogue = {"rule_id": "ROGUE_001", "schema_flags": ["some prose"], "antecedents": []}
    baseline: set[str] = set()
    unaccounted = [
        r["rule_id"]
        for _f, _s, r in [("x.json", "validated_candidates", rogue)]
        if _owes_provenance(r) and r["rule_id"] not in baseline
    ]
    assert unaccounted == ["ROGUE_001"]


def test_coverage_predicate_exempts_empty_schema_flags():
    """The 41 empty-list rules owe nothing."""
    empty = {"rule_id": "EMPTY_001", "schema_flags": [], "antecedents": []}
    assert not _owes_provenance(empty)


def test_coverage_predicate_exempts_a_migrated_rule():
    migrated = {
        "rule_id": "MIGRATED_001",
        "schema_flags": ["old prose"],
        "provenance": {"notes": []},
        "antecedents": [],
    }
    assert not _owes_provenance(migrated)


def test_consistency_predicate_catches_a_real_g1_violation():
    """The gate's assertion-1 body, driven over the known-stale FT_001
    shape: antecedent Depth=deep against a binding still naming
    well_marked."""
    stale = {
        "rule_id": "FT_001_SYNTHETIC",
        "source_quote": "when the line of fate is strong",
        "antecedents": [{"feature": "Line of Fate", "attribute": "Depth", "value": "deep"}],
        "provenance": {
            "token_bindings": [
                {
                    "antecedent_index": 0,
                    "bound_field": "value",
                    "chosen_token": "well_marked",
                    "attribute": "Depth",
                }
            ]
        },
    }
    violations = validate_rule(stale)
    assert any(v.startswith("G1 ") for v in violations), violations


def test_shrink_only_predicate_catches_a_stale_baseline_entry():
    migrated = {
        "rule_id": "MIGRATED_002",
        "schema_flags": ["old prose"],
        "provenance": {"notes": []},
        "antecedents": [],
    }
    by_id = {migrated["rule_id"]: migrated}
    stale = [rid for rid in ["MIGRATED_002"] if rid in by_id and "provenance" in by_id[rid]]
    assert stale == ["MIGRATED_002"]


# ─── governance-#1 additive-only guard stays true ───────────────────────


def test_no_rule_carries_provenance_yet():
    """Mirrors the governance-#1 guard. This task wires the GATE; it does
    not migrate anything. When migration begins, this test and its twin in
    test_provenance.py are updated together, deliberately."""
    carriers = [
        f"{filename}:{rule['rule_id']}"
        for filename, _section, rule in _ALL_RULES
        if "provenance" in rule
    ]
    assert carriers == [], (
        f"rules now carry `provenance` -- governance #2 was gate-only: {carriers}"
    )


def test_gate_covers_every_rule_file():
    """Guards against the gate silently scanning nothing (a glob typo, a
    renamed directory) and reporting green for it."""
    files = {filename for filename, _s, _r in _ALL_RULES}
    assert len(files) == 4, f"expected 4 rule files, gate scanned: {sorted(files)}"
    assert len(_ALL_RULES) > 100, f"gate scanned only {len(_ALL_RULES)} rules"
