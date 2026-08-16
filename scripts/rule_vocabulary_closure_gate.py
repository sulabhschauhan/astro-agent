"""
scripts/rule_vocabulary_closure_gate.py

Deterministic vocabulary-closure gate over the palm rule set: for every
antecedent in every loaded rule (data/palm_rules/palm_rules_*.json,
`validated_candidates` array only -- the same subset palm_rules_table.
load_rule_set() actually loads), checks whether the antecedent can EVER
fire against the live capture pipeline. An antecedent that references a
feature/attribute/value/relation_target combination the pipeline can never
produce is DEAD -- it passed human review (possibly `verified: true`) but
can never match, silently.

Three reachability rules, encoded to mirror the live pipeline exactly
(NOT re-derived independently -- verified against
agent/interpretive/observation_to_tokens.py's `_VALID_TRIPLES` and
agent/interpretive/palm_rules_table.py's `_antecedent_fires` before this
script was written):

1. condition_type == "comparative": reachable iff attribute is in
   attribute_feature_mapping (AFM), feature is in AFM[attribute], AND
   comparator_feature is in AFM[attribute] -- `_antecedent_fires`'s
   comparative branch reads magnitudes[feature][attribute] and
   magnitudes[comparator_feature][attribute]; AFM membership is the
   static-analysis proxy for "could ever be populated there".

2. value is not None: reachable iff (feature, attribute, value) is a
   valid to_tokens() triple -- attribute in AFM, feature in AFM[attribute],
   value in POOL (union of every data/ontology_registry.json `values`
   category) -- EXCEPT the P-EXCLUSIVE case: attribute == "Proximity" and
   value in {touching, medium, distant} bypasses to_tokens entirely via
   observation_extractor.extract_proximity_observations() and merges
   straight into the flat observation dict (palm_reading.py's merge
   point) -- always reachable via value, regardless of POOL/AFM.

3. relation_target is not None: reachable iff attribute is one of the
   four relational attributes {Starting_Point, Proximity, Position,
   Branching}, feature is one of the three relational-capable lines
   {Line of Head, Line of Heart, Line of Fate}, AND relation_target is in
   relation_target_registry (RTR) -- mirrors
   observation_extractor.extract_relational_targets()'s own closed
   vocabulary + `_RELATIONAL_LINE_ALIAS` scope.

An antecedent with BOTH a value and a relation_target must pass BOTH
checks (rules 2 and 3 both apply) -- value:None skips rule 2 entirely
(target-only wildcard antecedent, `_antecedent_fires`'s own value:null
convention), never a failure by itself.

Registry-level only: this gate does NOT parse agent/palm_processor.py's
vision-menu prose (a rule can be vocabulary-reachable here yet still never
observed if the vision menu never offers that token to the model --
tracked as a separate future gate, out of this script's scope).

Report-first: full findings go to diagnostics/latest_run.md (this run
ONLY -- truncate + write, never append), plus a stdout summary. Exits 1
if any DEAD antecedent is found, else 0 -- CI-callable.

No rule file, registry file, or production module is ever modified by
this script.
"""

from __future__ import annotations

import difflib
import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "data" / "ontology_registry.json"
RULES_GLOB_PATTERN = str(ROOT / "data" / "palm_rules" / "palm_rules_*.json")
REPORT_PATH = ROOT / "diagnostics" / "latest_run.md"

_PROXIMITY_EXEMPT_VALUES = frozenset({"touching", "medium", "distant"})
_TARGET_ALLOWED_ATTRIBUTES = frozenset(
    {"Starting_Point", "Proximity", "Position", "Branching"}
)
_TARGET_ALLOWED_FEATURES = frozenset(
    {"Line of Head", "Line of Heart", "Line of Fate"}
)


def load_registry(path: Path) -> dict:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(
            f"rule_vocabulary_closure_gate: failed to read registry file "
            f"{path}: {exc}"
        ) from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"rule_vocabulary_closure_gate: registry file {path} is not "
            f"valid JSON: {exc}"
        ) from exc


def build_pool(registry: dict) -> set[str]:
    try:
        values_block = registry["values"]
    except KeyError as exc:
        raise RuntimeError(
            "rule_vocabulary_closure_gate: registry has no 'values' key -- "
            "cannot build the value pool."
        ) from exc
    pool: set[str] = set()
    for category, value_list in values_block.items():
        if not isinstance(value_list, list):
            raise RuntimeError(
                f"rule_vocabulary_closure_gate: registry['values'][{category!r}] "
                f"is not a list (got {type(value_list).__name__}) -- malformed "
                "registry."
            )
        pool.update(value_list)
    return pool


def build_afm(registry: dict) -> dict[str, set[str]]:
    try:
        raw_afm = registry["attribute_feature_mapping"]
    except KeyError as exc:
        raise RuntimeError(
            "rule_vocabulary_closure_gate: registry has no "
            "'attribute_feature_mapping' key."
        ) from exc
    return {attribute: set(features) for attribute, features in raw_afm.items()}


def build_rtr(registry: dict) -> set[str]:
    try:
        return set(registry["relation_target_registry"])
    except KeyError as exc:
        raise RuntimeError(
            "rule_vocabulary_closure_gate: registry has no "
            "'relation_target_registry' key."
        ) from exc


def load_rule_files(pattern: str) -> list[tuple[Path, dict]]:
    matched = sorted(Path(p) for p in glob.glob(pattern))
    if not matched:
        raise RuntimeError(
            f"rule_vocabulary_closure_gate: no rule files matched pattern "
            f"{pattern!r} -- nothing to check."
        )
    files: list[tuple[Path, dict]] = []
    for path in matched:
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise RuntimeError(
                f"rule_vocabulary_closure_gate: failed to read rule file "
                f"{path}: {exc}"
            ) from exc
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"rule_vocabulary_closure_gate: rule file {path} is not "
                f"valid JSON: {exc}"
            ) from exc
        files.append((path, data))
    return files


def classify_antecedent(
    antecedent: dict, afm: dict[str, set[str]], pool: set[str], rtr: set[str]
) -> tuple[str, str] | None:
    """Returns None if the antecedent is reachable, else
    (dead_class, reason_detail)."""
    feature = antecedent.get("feature")
    attribute = antecedent.get("attribute")
    value = antecedent.get("value")
    relation_target = antecedent.get("relation_target")
    condition_type = antecedent.get("condition_type")
    comparator_feature = antecedent.get("comparator_feature")

    # Rule 1: comparative antecedents are checked entirely separately --
    # value/relation_target are irrelevant to a comparative condition
    # (Antecedent.value is always None for these in the live schema).
    if condition_type == "comparative":
        if attribute not in afm:
            return ("DEAD-COMPARATIVE", "attribute not in AFM")
        if feature not in afm.get(attribute, set()):
            return ("DEAD-COMPARATIVE", "feature not in AFM[attribute]")
        if comparator_feature not in afm.get(attribute, set()):
            return ("DEAD-COMPARATIVE", "comparator_feature not in AFM[attribute]")
        return None

    # Rule 2: value check. value is None => wildcard, target-only
    # antecedent -- skip this check entirely (never a failure on its own).
    if value is not None:
        if attribute == "Proximity" and value in _PROXIMITY_EXEMPT_VALUES:
            pass  # P-EXCLUSIVE: bypasses to_tokens/POOL, always reachable via value.
        else:
            if attribute not in afm:
                return ("DEAD-ATTR-UNMAPPED", "attribute not in AFM")
            if feature not in afm.get(attribute, set()):
                return ("DEAD-FEATURE-UNMAPPED", "feature not in AFM[attribute]")
            if value not in pool:
                return ("DEAD-VALUE-DRIFT", "value not in POOL")

    # Rule 3: relation_target check. Independent of rule 2 -- an
    # antecedent with both value and relation_target must pass both.
    if relation_target is not None:
        if attribute not in _TARGET_ALLOWED_ATTRIBUTES:
            return (
                "DEAD-TARGET-UNREACHABLE",
                "attribute not in {Starting_Point,Proximity,Position,Branching}",
            )
        if feature not in _TARGET_ALLOWED_FEATURES:
            return (
                "DEAD-TARGET-UNREACHABLE",
                "feature not in {Line of Head,Line of Heart,Line of Fate}",
            )
        if relation_target not in rtr:
            return ("DEAD-TARGET-UNREACHABLE", "relation_target not in RTR")

    return None


def nearest_pool_token(value: object, pool: set[str]) -> str:
    if not isinstance(value, str) or not pool:
        return ""
    matches = difflib.get_close_matches(value, pool, n=1)
    return matches[0] if matches else ""


def value_or_target_display(antecedent: dict) -> str:
    value = antecedent.get("value")
    relation_target = antecedent.get("relation_target")
    parts = []
    if value is not None:
        parts.append(f"value={value!r}")
    if relation_target is not None:
        parts.append(f"target={relation_target!r}")
    return "; ".join(parts) if parts else "(none)"


def run() -> int:
    registry = load_registry(REGISTRY_PATH)
    pool = build_pool(registry)
    afm = build_afm(registry)
    rtr = build_rtr(registry)

    rule_files = load_rule_files(RULES_GLOB_PATTERN)

    dead_rows: list[dict] = []
    class_counts: dict[str, int] = {}
    total_antecedents = 0
    total_rules = 0

    for path, data in rule_files:
        candidates = data.get("validated_candidates", [])
        for rule in candidates:
            total_rules += 1
            rule_id = rule.get("rule_id", "<no rule_id>")
            verified = rule.get("verified")
            for antecedent in rule.get("antecedents", []):
                total_antecedents += 1
                result = classify_antecedent(antecedent, afm, pool, rtr)
                if result is None:
                    continue
                dead_class, reason = result
                class_counts[dead_class] = class_counts.get(dead_class, 0) + 1
                value = antecedent.get("value")
                nearest = (
                    nearest_pool_token(value, pool)
                    if dead_class == "DEAD-VALUE-DRIFT"
                    else ""
                )
                dead_rows.append({
                    "rule_id": rule_id,
                    "file": path.name,
                    "feature": antecedent.get("feature"),
                    "attribute": antecedent.get("attribute"),
                    "value_or_target": value_or_target_display(antecedent),
                    "class": f"{dead_class} ({reason})",
                    "nearest": nearest,
                    "verified": verified,
                })

    verified_dead = [r for r in dead_rows if r["verified"] is True]

    write_report(
        rule_files, total_rules, total_antecedents, dead_rows, class_counts,
        verified_dead,
    )
    print_summary(total_rules, total_antecedents, dead_rows, class_counts, verified_dead)

    return 1 if dead_rows else 0


def write_report(
    rule_files, total_rules, total_antecedents, dead_rows, class_counts,
    verified_dead,
) -> None:
    lines: list[str] = []
    lines.append("# Rule vocabulary-closure gate\n")
    lines.append(
        f"Files checked: {', '.join(p.name for p, _ in rule_files)}\n"
    )
    lines.append(f"Rules checked (validated_candidates): {total_rules}\n")
    lines.append(f"Antecedents checked: {total_antecedents}\n")
    lines.append(f"DEAD antecedents found: {len(dead_rows)}\n")

    lines.append("\n## Dead antecedents\n")
    if dead_rows:
        lines.append(
            "| rule_id | file | feature | attribute | value/target | class | nearest valid token |"
        )
        lines.append("|---|---|---|---|---|---|---|")
        for row in dead_rows:
            lines.append(
                f"| {row['rule_id']} | {row['file']} | {row['feature']} | "
                f"{row['attribute']} | {row['value_or_target']} | {row['class']} | "
                f"{row['nearest']} |"
            )
    else:
        lines.append("(none -- vocabulary closure holds)")

    lines.append("\n## Counts per class\n")
    if class_counts:
        for cls in sorted(class_counts):
            lines.append(f"- {cls}: {class_counts[cls]}")
    else:
        lines.append("(none)")

    lines.append(
        f"\n## verified=True but DEAD: {len(verified_dead)}\n"
    )
    lines.append(
        "These passed human review yet cannot fire against the live "
        "pipeline -- the dangerous subset.\n"
    )
    if verified_dead:
        lines.append("| rule_id | file | feature | attribute | value/target | class |")
        lines.append("|---|---|---|---|---|---|")
        for row in verified_dead:
            lines.append(
                f"| {row['rule_id']} | {row['file']} | {row['feature']} | "
                f"{row['attribute']} | {row['value_or_target']} | {row['class']} |"
            )
    else:
        lines.append("(none)")

    lines.append("")

    try:
        REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(
            f"rule_vocabulary_closure_gate: failed to write report to "
            f"{REPORT_PATH}: {exc}"
        ) from exc


def print_summary(total_rules, total_antecedents, dead_rows, class_counts, verified_dead) -> None:
    print("rule_vocabulary_closure_gate summary")
    print(f"  rules checked: {total_rules}")
    print(f"  antecedents checked: {total_antecedents}")
    print(f"  DEAD antecedents: {len(dead_rows)}")
    for cls in sorted(class_counts):
        print(f"    {cls}: {class_counts[cls]}")
    print(f"  verified=True but DEAD: {len(verified_dead)}")


if __name__ == "__main__":
    try:
        sys.exit(run())
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
