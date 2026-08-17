"""Vocabulary reachability scan (VERIFICATION ARCHITECTURE -- fidelity-not-
truth, see data/palm_rules/README.md).

GOAL: find every validated_candidates rule that fires on a word the live
pipeline can never actually supply -- a guaranteed silent miss. Pure
Python, read-only, no LLM, no network. Writes diagnostics/latest_run.md
(truncate). Does not modify any rule, ontology, or agent file.

=== Derivation of "the emitted vocabulary" (methodology; flagged per the
task's own instruction: print what was used, since no single ready-made
list exists) ===

The task named two files as the source of truth: agent/palm_processor.py
(the vision prompt -- what the model is ASKED to describe) and
agent/interpretive/observation_extractor.py (what actually turns that
prose into structured tokens). Reading both, "the hand-state vocabulary
the pipeline actually emits" is not one flat list -- it is produced by
THREE independent code-enforced gates, and this scan checks a rule
antecedent's trigger token against whichever gate governs it:

1. LITERAL VALUE tokens (antecedent has a "value", no relation_target) --
   governed by observation_extractor._CLOSED_VOCAB /
   _values_for_attribute(): an (attribute, value) pair is only ever
   producible if (a) the antecedent's "feature" is one of the 8 ontology
   features observation_extractor._FEATURE_ALIAS actually routes vision
   prose into (Line of Life/Head/Heart/Fate/Sun, Thumb, Mount of
   Venus/Jupiter -- observation_extractor.all_aliased_features()), (b) the
   attribute is legal for that feature per ontology_registry.json's
   attribute_feature_mapping, and (c) the value is in that attribute's
   resolved legal-value pool -- its narrow attribute_value_binding set if
   the registry declares one (Slope/Slope_Magnitude/Proximity only),
   otherwise the FLAT UNION of every values-category list in the registry
   (observation_extractor.py's own module docstring point 5: an unbound
   attribute accepts any of the ~216 flattened value tokens, not just its
   "natural" category -- a deliberate, documented design choice, not a
   scan artifact). This is the code-mechanical gate the LLM-mediated
   extraction call (extract_observation) actually enforces; it is
   INDEPENDENT of whether palm_processor.py's vision prompt explicitly
   solicits that specific wording in free prose (it mostly does not, for
   Position -- see the caveat below).

2. RELATION_TARGET tokens (antecedent carries a relation_target) --
   governed by observation_extractor.extract_relational_targets():
   reachable only if the antecedent's attribute is one of
   Starting_Point/Proximity/Position/Branching (the ORIGIN/PROXIMITY/
   TERMINATION/BRANCHES_TO parse targets), the feature is one of Line of
   Head/Heart/Fate (the only 3 lines whose vision block ever carries a
   RELATIONAL sub-section), and the target landmark is a member of
   ontology_registry.json's relation_target_registry. This scan ADDITIONALLY
   cross-checks ORIGIN/TERMINATION targets (not PROXIMITY/BRANCHES_TO,
   which share one broad landmark list across all three lines per the
   prompt) against palm_processor.py's own per-line, per-field MENU --
   a real, tighter constraint the vision model is instructed to obey that
   is NOT enforced by the registry-membership code check. A target that
   passes the registry check but falls outside that menu is flagged as a
   PROMPT-MENU CAVEAT (soft; does not downgrade the yes/NO verdict, since
   the code's actual enforced gate is registry membership, not the
   prompt's declared menu -- but it is a real reason the target may never
   actually be emitted even though it would legally pass).

3. COMPARATIVE conditions (antecedent's condition_type == "comparative",
   e.g. H_010a/H_010b's Depth-of-head-vs-heart) -- always INTERPRETED-TERM.
   No raw vision field, current or hypothetical, emits "which line is
   stronger" -- it is a computed judgment over two Depth observations, the
   exact class the task's own H_010a example names.

A trigger token failing gate 1 OR 2 for a reason OTHER than nonexistent
schema (attribute/feature absent from the registry entirely, e.g. H_018's
"Hand"/"Type" or HL_015's "Presence") is reported as NO / naming-mismatch,
per the task's definition ("the rule's word simply isn't in the emitted
set and isn't interpreted"); the schema-nonexistent sub-case is called out
in the per-row detail text but still counted under the same NO / NAMING-
MISMATCH umbrella, since the task defines only two live categories (NO,
INTERPRETED-TERM) and this scan does not invent a third.

"Nearest emitted value" (report column 1, table) is a best-effort
difflib.get_close_matches() heuristic over the correct candidate pool for
that antecedent (the resolved value pool for a value mismatch, or
relation_target_registry for a relation_target mismatch) -- not a verified
recommendation. CLAUDE.md's rule_vocabulary_closure_gate.py already found
difflib nearest-token wrong on 2 of 5 flagged rules in an earlier sweep;
treat this column as a hint to manually verify, not an auto-fix.
"""
from __future__ import annotations

import difflib
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

_RULES_PATH = _REPO_ROOT / "data" / "palm_rules" / "palm_rules_head_heart_v1.json"
_REPORT_PATH = _REPO_ROOT / "diagnostics" / "latest_run.md"

try:
    from agent.interpretive import observation_extractor as oe
except Exception as exc:  # noqa: BLE001 -- fail loud, per task's "STOP rather than invent" instruction
    raise RuntimeError(
        "vocab_reachability_scan: could not import "
        "agent.interpretive.observation_extractor -- cannot derive the "
        f"emitted vocabulary without it, refusing to guess: {exc}"
    ) from exc

# --- palm_processor.py's own per-line ORIGIN/TERMINATION menus, transcribed
# verbatim from its vision system prompt (agent/palm_processor.py,
# describe_palm_image). PROXIMITY/BRANCHES_TO deliberately excluded -- the
# prompt gives those ONE shared landmark list across all three lines
# ("PROXIMITY/BRANCHES_TO landmark names: Line of Life/Head/Heart/Fate/Sun;
# Mount of Jupiter/Saturn/the Sun/Mercury/Venus/Luna; Upper Mount of Mars;
# Lower Mount of Mars; Junction of First and Second Fingers; Wrist;
# Percussion."), not a per-line menu, so there is nothing narrower to check
# them against beyond the registry membership gate itself. Used ONLY for
# the soft prompt-menu caveat (see module docstring) -- never changes a
# yes/NO verdict.
_VISION_ORIGIN_MENU: dict[str, frozenset[str]] = {
    "Line of Head": frozenset({"Mount of Jupiter", "Line of Life", "Lower Mount of Mars"}),
    "Line of Heart": frozenset({"Mount of Jupiter", "Junction of First and Second Fingers", "Mount of Saturn"}),
    "Line of Fate": frozenset({"Line of Life", "Wrist", "Mount of Luna", "Line of Head", "Line of Heart"}),
}
_VISION_TERMINATION_MENU: dict[str, frozenset[str]] = {
    "Line of Head": frozenset({"Mount of Luna", "Percussion", "Upper Mount of Mars"}),
    "Line of Heart": frozenset({"Percussion", "Mount of Mercury"}),
    "Line of Fate": frozenset({"Mount of Saturn", "Mount of Jupiter", "Line of Heart", "Line of Head"}),
}

_RELATIONAL_ATTRS = frozenset(oe._RELATIONAL_ATTRIBUTE_MAP.values())  # Starting_Point/Proximity/Position/Branching
_RELATIONAL_FEATURES = frozenset(oe._RELATIONAL_LINE_ALIAS.values())  # Line of Head/Heart/Fate
_ALL_ONTOLOGY_FEATURE_NAMES: frozenset[str] = frozenset(
    f for category in oe._REGISTRY["features"].values() for f in category
)
_ALIASED_FEATURES: frozenset[str] = oe.all_aliased_features()

_DIFFLIB_CUTOFF = 0.4  # heuristic only -- see module docstring caveat


def _nearest(word: str, pool) -> str | None:
    matches = difflib.get_close_matches(word, list(pool), n=1, cutoff=_DIFFLIB_CUTOFF)
    return matches[0] if matches else None


def _origin_termination_menu_caveat(field: str, feature: str, target: str) -> str | None:
    """field is 'ORIGIN' or 'TERMINATION' only (PROXIMITY/BRANCHES_TO share
    one list, see module docstring). Returns a caveat string if `target` is
    registry-legal but outside palm_processor.py's declared menu for this
    (feature, field); None otherwise (including for lines/fields this
    scan has no menu data for)."""
    menu_by_feature = _VISION_ORIGIN_MENU if field == "ORIGIN" else _VISION_TERMINATION_MENU
    menu = menu_by_feature.get(feature)
    if menu is None or target in menu:
        return None
    return (
        f"PROMPT-MENU CAVEAT: {target!r} passes the registry-membership gate but is "
        f"OUTSIDE palm_processor.py's own {field} menu for {feature} ({sorted(menu)}) -- "
        "the vision model is instructed to pick only from that menu, so this target is "
        "unlikely to ever actually be emitted even though the code would accept it."
    )


def classify_antecedent(feature: str, attribute: str, value, relation_target) -> dict:
    """Returns {"status": "yes"|"NO"|"INTERPRETED-TERM", "detail": str,
    "nearest": str|None, "caveat": str|None}. See module docstring for the
    full methodology this implements."""
    # --- feature/attribute schema existence (shared by both branches) ---
    if feature not in _ALL_ONTOLOGY_FEATURE_NAMES:
        return {
            "status": "NO",
            "detail": f"feature {feature!r} does not exist anywhere in ontology_registry.json's features registry",
            # No nearest-feature-name heuristic here: a difflib string match
            # between an absent CONCEPT (e.g. "Hand") and existing feature
            # NAMES answers a different question than "what token did the
            # rule author almost certainly mean" -- would be noise, not a hint.
            "nearest": None,
            "caveat": None,
        }
    if attribute not in oe._ATTRIBUTE_FEATURE_MAP:
        return {
            "status": "NO",
            "detail": f"attribute {attribute!r} does not exist anywhere in ontology_registry.json's attribute_feature_mapping",
            "nearest": None,  # same rationale as the feature-absent branch above
            "caveat": None,
        }
    if feature not in oe._ATTRIBUTE_FEATURE_MAP[attribute]:
        return {
            "status": "NO",
            "detail": (
                f"attribute {attribute!r} is not mapped to feature {feature!r} in "
                f"attribute_feature_mapping (mapped only to "
                f"{sorted(oe._ATTRIBUTE_FEATURE_MAP[attribute])})"
            ),
            "nearest": None,
            "caveat": None,
        }
    if feature not in _ALIASED_FEATURES:
        return {
            "status": "NO",
            "detail": (
                f"feature {feature!r} exists in the ontology but has no "
                "observation_extractor._FEATURE_ALIAS entry -- no vision prose section ever "
                "routes to it, so it can never be extracted regardless of value legality"
            ),
            "nearest": None,
            "caveat": None,
        }

    rel_result = None
    if relation_target is not None:
        if attribute not in _RELATIONAL_ATTRS:
            rel_result = {
                "status": "NO",
                "detail": (
                    f"attribute {attribute!r} has no RELATIONAL parse channel (only "
                    "Starting_Point/Proximity/Position/Branching are ever parsed as relation "
                    "targets, via ORIGIN/PROXIMITY/TERMINATION/BRANCHES_TO)"
                ),
                "nearest": None,
            }
        elif feature not in _RELATIONAL_FEATURES:
            rel_result = {
                "status": "NO",
                "detail": f"feature {feature!r} never carries a RELATIONAL block (only Line of Head/Heart/Fate do)",
                "nearest": None,
            }
        elif relation_target not in oe._RELATION_TARGET_REGISTRY:
            rel_result = {
                "status": "NO",
                "detail": f"relation_target {relation_target!r} is not a member of ontology_registry.json's relation_target_registry",
                "nearest": _nearest(relation_target, oe._RELATION_TARGET_REGISTRY),
            }
        else:
            field = {v: k for k, v in oe._RELATIONAL_ATTRIBUTE_MAP.items()}[attribute]
            caveat = _origin_termination_menu_caveat(field, feature, relation_target) if field in ("ORIGIN", "TERMINATION") else None
            rel_result = {
                "status": "yes",
                "detail": f"relation_target {relation_target!r} reachable via the {field} parse (registry-legal)",
                "nearest": None,
                "caveat": caveat,
            }

    val_result = None
    if value is not None:
        allowed = oe._values_for_attribute(attribute)
        if value in allowed:
            val_result = {"status": "yes", "detail": f"value {value!r} is in the resolved legal-value pool for attribute {attribute!r}", "nearest": None}
        else:
            val_result = {
                "status": "NO",
                "detail": f"value {value!r} is NOT in the resolved legal-value pool for attribute {attribute!r}",
                "nearest": _nearest(value, allowed),
            }

    if rel_result is None and val_result is None:
        return {"status": "NO", "detail": "malformed antecedent: neither a literal value nor a relation_target present", "nearest": None, "caveat": None}

    parts = [r for r in (rel_result, val_result) if r is not None]
    overall_status = "NO" if any(p["status"] == "NO" for p in parts) else "yes"
    detail = " | ".join(p["detail"] for p in parts)
    nearest = next((p["nearest"] for p in parts if p.get("nearest")), None)
    caveat = rel_result.get("caveat") if rel_result else None
    return {"status": overall_status, "detail": detail, "nearest": nearest, "caveat": caveat}


def load_scanned_rules() -> list[dict]:
    try:
        with open(_RULES_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except OSError as exc:
        raise OSError(f"vocab_reachability_scan: could not read {_RULES_PATH}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"vocab_reachability_scan: {_RULES_PATH} is not valid JSON: {exc}") from exc
    return [r for r in data.get("validated_candidates", []) if not r.get("needs_remodel")]


def scan_rule(rule: dict) -> list[dict]:
    """One row per antecedent. condition_type == 'comparative' short-circuits
    straight to INTERPRETED-TERM regardless of value/relation_target."""
    rows = []
    for ant in rule.get("antecedents", []):
        feature = ant.get("feature")
        attribute = ant.get("attribute")
        value = ant.get("value")
        relation_target = ant.get("relation_target")
        if ant.get("condition_type") == "comparative":
            classification = {
                "status": "INTERPRETED-TERM",
                "detail": (
                    f"comparative condition ({attribute} vs {ant.get('comparator_feature')}, "
                    f"comparator {ant.get('comparator')!r}) -- requires a computed 'which is "
                    "stronger' judgment; no raw vision field ever emits this directly (the "
                    "H_010a class per task spec)"
                ),
                "nearest": None,
                "caveat": None,
            }
        else:
            classification = classify_antecedent(feature, attribute, value, relation_target)
        rows.append({
            "rule_id": rule["rule_id"],
            "feature": feature,
            "attribute": attribute,
            "value": value,
            "relation_target": relation_target,
            **classification,
        })
    return rows


def _trigger_token_str(row: dict) -> str:
    parts = [f"{row['attribute']}"]
    if row["value"] is not None:
        parts.append(f"={row['value']!r}")
    if row["relation_target"] is not None:
        parts.append(f"->{row['relation_target']!r}")
    return "".join(parts) + f" (on {row['feature']})"


def _format_report(all_rows: list[dict], rule_ids_scanned: list[str]) -> str:
    lines = ["# Latest Run: vocabulary reachability scan (validated_candidates, needs_remodel skipped)\n"]
    lines.append(f"Rules scanned: {len(rule_ids_scanned)}. Read-only, no LLM, no network. See module docstring in scripts/vocab_reachability_scan.py for the full three-gate methodology.\n")

    lines.append("## 1. Per-antecedent trigger-token table\n")
    lines.append("| rule_id | trigger token | status | nearest emitted value if NO | detail |")
    lines.append("|---|---|---|---|---|")
    for row in all_rows:
        nearest = row["nearest"] if row["nearest"] else ("-" if row["status"] != "NO" else "(no close match)")
        detail = row["detail"].replace("|", "/")
        status_display = "yes" if row["status"] == "yes" else row["status"]
        lines.append(f"| {row['rule_id']} | {_trigger_token_str(row)} | {status_display} | {nearest} | {detail} |")
        if row.get("caveat"):
            lines.append(f"| {row['rule_id']} |  | *(caveat)* |  | {row['caveat']} |")
    lines.append("")

    by_rule: dict[str, list[dict]] = {}
    for row in all_rows:
        by_rule.setdefault(row["rule_id"], []).append(row)

    total = len(rule_ids_scanned)
    fully_reachable = [rid for rid in rule_ids_scanned if all(r["status"] == "yes" for r in by_rule.get(rid, []))]
    has_no = [rid for rid in rule_ids_scanned if any(r["status"] == "NO" for r in by_rule.get(rid, []))]
    has_interpreted = [rid for rid in rule_ids_scanned if any(r["status"] == "INTERPRETED-TERM" for r in by_rule.get(rid, []))]

    def pct(n: int) -> str:
        return f"{n}/{total} ({100 * n / total:.1f}%)" if total else f"{n}/0 (n/a)"

    lines.append("## 2. Summary counts\n")
    lines.append(f"- Rules fully-reachable (every antecedent yes): {pct(len(fully_reachable))}")
    lines.append(f"- Rules with >=1 NO (naming-mismatch): {pct(len(has_no))}")
    lines.append(f"- Rules with >=1 INTERPRETED-TERM: {pct(len(has_interpreted))}")
    lines.append("")

    lines.append("## 3a. FLAG: NAMING-MISMATCH rules (>=1 antecedent NO)\n")
    if has_no:
        for rid in has_no:
            bad = [r for r in by_rule[rid] if r["status"] == "NO"]
            for r in bad:
                lines.append(f"- {rid}: {_trigger_token_str(r)} -- {r['detail']}")
    else:
        lines.append("(none)")
    lines.append("")

    lines.append("## 3b. FLAG: INTERPRETED-TERM rules (compute-and-feed candidates)\n")
    if has_interpreted:
        for rid in has_interpreted:
            bad = [r for r in by_rule[rid] if r["status"] == "INTERPRETED-TERM"]
            for r in bad:
                lines.append(f"- {rid}: {_trigger_token_str(r)} -- {r['detail']}")
    else:
        lines.append("(none)")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    rules = load_scanned_rules()
    rule_ids = [r["rule_id"] for r in rules]
    all_rows: list[dict] = []
    for rule in rules:
        all_rows.extend(scan_rule(rule))

    report = _format_report(all_rows, rule_ids)
    try:
        _REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_REPORT_PATH, "w", encoding="utf-8") as f:
            f.write(report)
    except OSError as exc:
        raise OSError(f"vocab_reachability_scan: could not write report to {_REPORT_PATH}: {exc}") from exc

    print(f"Scanned {len(rule_ids)} rules, {len(all_rows)} antecedents.")
    print(f"Wrote report to {_REPORT_PATH}")


if __name__ == "__main__":
    main()
