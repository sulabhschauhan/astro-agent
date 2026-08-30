"""
probes/vocab_mismatch_audit_S121.py

Vision-emittable vs rule-vocabulary mismatch audit (S121). READ-ONLY:
no LLM call, no network, no image, no write to any rule / registry /
source / test file. Reads only, prints a taxonomy to stdout. NOT
imported by the pipeline, NOT wired anywhere.

WHY THIS EXISTS: the S120 re-run found FT_001 silently never fires --
the rule needs `Line of Fate.Depth == "well_marked"` but vision only
ever emits `"deep"`. This probe measures the FULL CLASS that FT_001 is
one member of, across every live rule in all 4 palm_rules files and
every attribute, and is the evidence behind the numbers cited in the
S121 report (diagnostics/latest_run.md). Committed per CLAUDE.md
Working Style #16: any script whose numbers are cited in a decision must
be committed with its report.

=== THE THREE VOCABULARIES THIS PROBE COMPARES ===

  V1 AUTHORING/BOOK vocabulary -- data/ontology_registry.json's `values`
     block (217 tokens), harvested from Cheiro's own prose wholesale at
     commit d723291. Rule authors pick trigger tokens from it, and every
     existing gate checks against it.
  V2 VISION SOLICITATION vocabulary -- what
     palm_processor._build_description_system_prompt actually asks the
     vision model for: 9 closed menus (SLOPE / ORIGIN / TERMINATION /
     PROXIMITY / BRANCHES_TO / BREAK TYPE / LENGTH EXTENT / DEVELOPMENT /
     CONTACTS) plus FREE PROSE for every other dimension.
  V3 EXTRACTION OUTPUT vocabulary -- what observation_extractor's LLM
     actually emits per run: a non-deterministic projection of V2 onto
     V1, constrained only by the FLAT 217-token pool for the ~39
     attributes `attribute_value_binding` does not bind.

A rule can only fire against V3. Nothing anywhere checks V1 subset-of V3.
That gap is the class this probe measures.

=== TAXONOMY (the `cls` column) ===

  OK-relational  relation_target antecedent: registry-legal AND inside
                 palm_processor's per-line ORIGIN/TERMINATION menu.
  OK-menu        value inside a genuine closed emission menu
                 (attribute_value_binding, or _MOUNT_DEVELOPMENT_MENUS).
  OK-observed    free-prose token actually seen in a live capture.

  D0-COMPUTED    comparative condition -- no vision field emits a
                 "which line is stronger" judgment (known, S94).
  D1-FEATURE-UNROUTED    the feature has no observation_extractor.
                 _FEATURE_ALIAS entry, so no vision prose section ever
                 routes to it (e.g. Quadrangle, Hand).
  D2-DIMENSION-UNSOLICITED  the vision prompt never asks for that
                 dimension on that feature, so no prose about it is ever
                 produced and extraction can never fire (e.g. line Color).
  D3-TOKEN-ABSENT the token is not in V1's pool at all, or (for a
                 relation_target) outside the per-line vision menu.
  D4-DUAL-ENCODING a RELATIONAL attribute (Starting_Point / Position /
                 Branching / Proximity) encoded as a LITERAL VALUE
                 instead of a relation_target. These attributes are
                 written by two channels -- extract_relational_targets()
                 into `targets`, and the extraction LLM into
                 `observation` -- and palm_rules_table._antecedent_fires
                 reads them from different dicts and never bridges. See
                 the CAVEAT below: dead in practice, not in principle.
  D5-SYNONYM-OR-STATE  solicited + in pool, but every live capture
                 produced a DIFFERENT token for that (feature,
                 attribute). Mixes two sub-causes that must be separated
                 by hand per row: a genuine synonym split (FT_001's
                 well_marked vs deep) and a genuine state difference
                 (Length=short vs long, because the hand's line is long).
  D6-UNOBSERVED  solicited + in pool, this (feature, attribute) never
                 populated in any live capture. Mostly legitimate state
                 contingency, but also catches the ATTRIBUTE-level twin
                 of D5 (Direction vs Slope -- two attribute names for one
                 dimension, only one of them bound and therefore emitted).

"Structurally dead" = D1 | D2 | D3 | D4. D5/D6 are NOT counted as dead.

=== METHODOLOGY CAVEATS (flagged, not silently absorbed) ===

 1. EMPIRICAL BASE IS THIN. The "observed live" set is harvested from
    whatever `observation` blocks exist in diagnostics/*.json -- 2 hands
    at time of writing. D1/D2/D3/D4 verdicts are CODE-DERIVED and do not
    depend on it; D5/D6 verdicts are SUGGESTIVE ONLY and must not be
    read as proof that a token can never be emitted.
 2. THE SOLICITATION MAP IS HAND-DERIVED. `SOLICITED` below is read off
    palm_processor._build_description_system_prompt by a human, not
    extracted mechanically, so it can drift from that prompt silently.
    It should become a derived artifact if/when the registry grows a
    real `emission_menus` block.
 3. D4 IS "CANNOT FIRE IN PRACTICE", NOT "IN PRINCIPLE". The extraction
    LLM is PERMITTED to emit Starting_Point/Position/Branching as literal
    values (they are in attribute_feature_mapping, so they appear in the
    prompt's VALID ATTRIBUTES line). It never has. Rated dead on the
    mechanism plus the S120 counter-example, not on impossibility.
 4. Reaches into several observation_extractor underscore names
    (_REGISTRY, _FEATURE_ALIAS, _RELATIONAL_LINE_ALIAS,
    _MOUNT_DEVELOPMENT_MENUS, _RELATION_TARGET_REGISTRY,
    _RELATIONSHIP_TOKENS) -- a considered coupling, same posture
    scripts/vocab_reachability_scan.py already takes and for the same
    reason: that module is the single source of truth for what the
    pipeline can produce, and duplicating the derivation here would
    drift.

Usage:
    python probes/vocab_mismatch_audit_S121.py
    python probes/vocab_mismatch_audit_S121.py --dump rows.json
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

try:
    from agent.interpretive import observation_extractor as oe
except Exception as exc:  # noqa: BLE001 -- fail loud, never guess the emitted vocabulary
    raise RuntimeError(
        "vocab_mismatch_audit_S121: could not import "
        "agent.interpretive.observation_extractor -- cannot derive the emitted "
        f"vocabulary without it, refusing to guess: {exc}"
    ) from exc

REG = oe._REGISTRY
GLOBAL_POOL = set(oe._ALL_VALUES)
BINDING = oe._ATTRIBUTE_VALUE_BINDING
MOUNT_MENUS = oe._MOUNT_DEVELOPMENT_MENUS
RTREG = oe._RELATION_TARGET_REGISTRY
TYPED = oe._RELATIONSHIP_TOKENS
REL_ATTRS = oe.EMITTED_RELATION_ATTRS
REL_FEATURES = frozenset(oe._RELATIONAL_LINE_ALIAS.values())
VRM = REG["vision_relational_menus"]
ALIASED = oe.all_aliased_features()

# ontology feature name -> EVERY palm_reading._FEATURE_REGISTRY label that
# aliases onto it. A list, not a scalar: two labels can share one canonical
# feature ("mount of apollo"/"mount of the sun" -> Mount of the Sun;
# "mount of mars positive"/"upper mount of mars" -> Upper Mount of Mars),
# and _MOUNT_DEVELOPMENT_MENUS is keyed by only ONE of each pair. Taking
# the first alias would false-flag those mounts as menu-less.
FEAT_TO_LABEL: dict[str, list[str]] = {}
for _label, _canonical in oe._FEATURE_ALIAS.items():
    if _canonical:
        FEAT_TO_LABEL.setdefault(_canonical, []).append(_label)

# SOLICITATION MAP -- see METHODOLOGY CAVEAT 2. Hand-derived from
# palm_processor._build_description_system_prompt. Clause per entry:
#   lines: "presence, depth, width (narrow/thin vs broad/thick), length,
#          course, origin and end, breaks/chains/forks/islands"
#          (+ SLOPE / ORIGIN / TERMINATION / PROXIMITY / BRANCHES_TO for
#          HEAD/HEART/FATE; CONVERGENCE for LIFE)
#   sun line:  "sun/intuition lines only if clearly visible" -> presence only
#   thumb:     "relative size, how low or high it is set, angle from the palm"
#   mounts:    "which pads appear developed, flat, or unremarkable"
#              + the per-mount DEVELOPMENT closed menus
# NOTE: no COLOR dimension is solicited anywhere in the prompt.
LINE_PROSE = {"Depth", "Width", "Length", "Continuity", "Clarity"}
SOLICITED: dict[str, set[str]] = {
    "Line of Life":   LINE_PROSE | {"Curve", "Direction", "Starting_Point", "Position", "Convergence"},
    "Line of Head":   LINE_PROSE | {"Direction", "Slope", "Starting_Point", "Position", "Proximity", "Branching"},
    "Line of Heart":  LINE_PROSE | {"Direction", "Slope", "Curve", "Starting_Point", "Position", "Proximity", "Branching"},
    "Line of Fate":   LINE_PROSE | {"Direction", "Slope", "Starting_Point", "Position", "Proximity", "Branching"},
    "Line of Sun":    set(),
    "Line of Health": set(),
    "Thumb":          {"Proportion", "Setting", "Angle", "Length", "Position"},
}
for _mount in ("Mount of Venus", "Mount of Jupiter", "Mount of Saturn", "Mount of the Sun",
               "Upper Mount of Mars", "Mount of Mercury", "Lower Mount of Mars",
               "Mount of Luna", "Plain of Mars"):
    SOLICITED[_mount] = {"Development"}

_DEAD_CLASSES = ("D1-FEATURE-UNROUTED", "D2-DIMENSION-UNSOLICITED",
                 "D3-TOKEN-ABSENT", "D4-DUAL-ENCODING")


def harvest_observed(root: Path) -> dict[tuple[str, str], set[str]]:
    """(feature, attribute) -> every value ever seen in a live capture's
    `observation` block, across every diagnostics/*.json. A malformed or
    unreadable file is skipped, never fatal -- this is a best-effort
    empirical floor, not a contract (METHODOLOGY CAVEAT 1)."""
    observed: dict[tuple[str, str], set[str]] = defaultdict(set)

    def walk(node) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "observation" and isinstance(value, dict):
                    for feature, attrs in value.items():
                        if isinstance(attrs, dict):
                            for attribute, token in attrs.items():
                                if isinstance(token, str):
                                    observed[(feature, attribute)].add(token)
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    for path in glob.glob(str(root / "diagnostics" / "*.json")):
        try:
            walk(json.loads(Path(path).read_text(encoding="utf-8")))
        except Exception:  # noqa: BLE001 -- a probe must not die on one bad capture file
            continue
    return observed


def classify(feature, attribute, value, rtarget, ctype, observed) -> tuple[str, str]:
    """Returns (cls, detail). See the TAXONOMY block in the module docstring."""
    if ctype == "comparative":
        return "D0-COMPUTED", "comparative -- no vision field emits a which-is-stronger judgment"

    # --- relational channel (antecedent carries a target, or a typed token) ---
    if rtarget is not None or attribute in TYPED:
        if attribute in TYPED:
            if feature not in REL_FEATURES:
                return "D1-FEATURE-UNROUTED", f"{feature} emits no CONTACTS block"
            if rtarget not in RTREG:
                return "D3-TOKEN-ABSENT", f"target {rtarget!r} not in relation_target_registry"
            return "OK-relational", "typed relation, registry-legal + CONTACTS-derivable"
        if attribute not in REL_ATTRS:
            return "D4-DUAL-ENCODING", f"{attribute!r} has no relational parse channel"
        if attribute != "Convergence" and feature not in REL_FEATURES:
            return "D1-FEATURE-UNROUTED", f"{feature} carries no RELATIONAL block"
        if rtarget not in RTREG:
            return "D3-TOKEN-ABSENT", f"target {rtarget!r} not in relation_target_registry"
        field = oe.RELATION_ATTR_TO_FIELD.get(attribute)
        if field in ("ORIGIN", "TERMINATION"):
            menu = VRM.get(feature, {}).get(field)
            if menu is not None and rtarget not in menu:
                return "D3-TOKEN-ABSENT", f"{rtarget!r} outside vision {field} menu for {feature}: {sorted(menu)}"
        return "OK-relational", f"reachable via {field or attribute} parse"

    if value is None:
        return "D3-TOKEN-ABSENT", "malformed: neither value nor relation_target"

    # --- Development: per-mount closed menu, enforced by the extractor ---
    if attribute == "Development":
        menus = [MOUNT_MENUS[label] for label in FEAT_TO_LABEL.get(feature, []) if label in MOUNT_MENUS]
        if not menus:
            return "D2-DIMENSION-UNSOLICITED", (
                f"{feature} has no DEVELOPMENT menu (presence-only mount); extractor drops any value")
        menu = set().union(*menus)
        if value not in menu:
            return "D3-TOKEN-ABSENT", f"{value!r} outside this mount's DEVELOPMENT menu {sorted(menu)}"
        return "OK-menu", "in this mount's closed DEVELOPMENT menu"

    # --- free-prose channel ---
    if feature not in ALIASED:
        return "D1-FEATURE-UNROUTED", (
            f"{feature!r} has no _FEATURE_ALIAS entry -- no vision prose ever routes to it")
    if value not in GLOBAL_POOL:
        return "D3-TOKEN-ABSENT", f"{value!r} absent from the global value pool entirely"
    if attribute in REL_ATTRS:
        return "D4-DUAL-ENCODING", (
            f"{attribute!r} is a RELATIONAL attribute (emitted as a target via "
            f"{oe.RELATION_ATTR_TO_FIELD.get(attribute)}), but this antecedent encodes a "
            f"literal value {value!r} -- two encodings of one doctrine")
    if attribute in BINDING:
        if value not in BINDING[attribute]:
            return "D3-TOKEN-ABSENT", (
                f"{value!r} outside attribute_value_binding[{attribute!r}]={list(BINDING[attribute])}")
        return "OK-menu", f"in attribute_value_binding[{attribute!r}]"
    solicited = SOLICITED.get(feature)
    if solicited is not None and attribute not in solicited:
        return "D2-DIMENSION-UNSOLICITED", (
            f"the vision prompt never asks for {attribute!r} on {feature} -- no prose about it "
            "is ever produced, so extraction can never fire")
    seen = observed.get((feature, attribute), set())
    if value in seen:
        return "OK-observed", f"observed live: {sorted(seen)}"
    if seen:
        return "D5-SYNONYM-OR-STATE", (
            f"solicited + in pool; live runs produced only {sorted(seen)} for this (feature,attribute)")
    return "D6-UNOBSERVED", (
        "solicited + in pool; this (feature,attribute) never populated in any live capture")


def scan(root: Path) -> list[dict]:
    """One row per antecedent, over validated_candidates in every
    data/palm_rules/palm_rules_*.json (needs_remodel skipped, matching
    scripts/vocab_reachability_scan.load_scanned_rules)."""
    observed = harvest_observed(root)
    rows: list[dict] = []
    for rules_path in sorted((root / "data" / "palm_rules").glob("palm_rules_*.json")):
        try:
            data = json.loads(rules_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"vocab_mismatch_audit_S121: could not read {rules_path}: {exc}") from exc
        chapter = rules_path.name.replace("palm_rules_", "").replace("_v1.json", "")
        for rule in data.get("validated_candidates", []):
            if rule.get("needs_remodel"):
                continue
            for ant in rule.get("antecedents", []):
                cls, detail = classify(
                    ant.get("feature"), ant.get("attribute"), ant.get("value"),
                    ant.get("relation_target"), ant.get("condition_type"), observed,
                )
                rows.append({
                    "file": chapter,
                    "rule_id": rule["rule_id"],
                    "feature": ant.get("feature"),
                    "attribute": ant.get("attribute"),
                    "value": ant.get("value"),
                    "relation_target": ant.get("relation_target"),
                    "cls": cls,
                    "detail": detail,
                    "schema_flags": rule.get("schema_flags") or [],
                })
    return rows


def _token(row: dict) -> str:
    if row["value"] is not None:
        return f"{row['attribute']}={row['value']!r}"
    return f"{row['attribute']}->{row['relation_target']!r}"


def report(rows: list[dict]) -> None:
    by_rule: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        by_rule[(row["file"], row["rule_id"])].append(row)
    dead_rules = sorted(k for k, v in by_rule.items() if any(r["cls"] in _DEAD_CLASSES for r in v))

    print(f"TOTAL antecedents: {len(rows)} over {len(by_rule)} rules")
    print()
    print("## Counts by class")
    for cls, count in sorted(Counter(r["cls"] for r in rows).items()):
        print(f"  {cls:28s} {count}")
    print()
    print(f"## Rules with >=1 structurally-dead antecedent (D1|D2|D3|D4): "
          f"{len(dead_rules)} of {len(by_rule)} "
          f"({100 * len(dead_rules) / len(by_rule):.0f}%)")
    per_file_total = Counter(f for f, _ in by_rule)
    per_file_dead = Counter(f for f, _ in dead_rules)
    for chapter in sorted(per_file_total):
        print(f"  {chapter:12s} {per_file_dead.get(chapter, 0):3d} dead of {per_file_total[chapter]:3d} live")
    print()
    for chapter in sorted(per_file_total):
        ids = [rid for f, rid in dead_rules if f == chapter]
        print(f"  {chapter:12s} dead rule ids: {ids if ids else '(none)'}")
    print()
    for cls in _DEAD_CLASSES + ("D5-SYNONYM-OR-STATE", "D6-UNOBSERVED"):
        selected = [r for r in rows if r["cls"] == cls]
        print(f"### {cls}  ({len(selected)})")
        for row in selected:
            print(f"  {row['file']:10s} {row['rule_id']:8s} {row['feature']:20s} "
                  f"{_token(row):46s} | {row['detail']}")
        print()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=("Vision-emittable vs rule-vocabulary mismatch audit over every "
                     "data/palm_rules/palm_rules_*.json. Read-only; prints to stdout."))
    parser.add_argument(
        "--dump", type=Path, default=None,
        help="Optional path to write the per-antecedent rows as JSON. Omitted by default: "
             "this probe writes nothing unless asked.")
    args = parser.parse_args(argv)

    rows = scan(_REPO_ROOT)
    report(rows)

    if args.dump is not None:
        try:
            args.dump.parent.mkdir(parents=True, exist_ok=True)
            args.dump.write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
        except OSError as exc:
            raise OSError(f"vocab_mismatch_audit_S121: could not write {args.dump}: {exc}") from exc
        print(f"Wrote {len(rows)} rows to {args.dump}")


if __name__ == "__main__":
    main()
