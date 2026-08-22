"""
Pattern C relation primitive, STEP 1 of 3: additive ontology_registry.json schema edit.

Adds two pure-relation line_attributes ("Convergence", "Convergence_Location")
to data/ontology_registry.json. Registry-legal only -- not wired to any
extractor, vision prompt, or rule file (that is STEP 2/3, separate prompts).

Idempotent: re-running after a successful apply will fail the preconditions
(the attributes already exist) rather than double-applying.
"""
import json
import sys
from pathlib import Path

REGISTRY_PATH = Path(__file__).resolve().parent.parent / "data" / "ontology_registry.json"

NEW_ATTRS = ["Convergence", "Convergence_Location"]
OWNER_FEATURES = ["Line of Fate", "Line of Head", "Line of Health", "Line of Heart"]
REQUIRED_RELATION_TARGETS = [
    "Line of Life",
    "Line of Head",
    "Line of Heart",
    "Line of Fate",
    "Line of Health",
    "Mount of Jupiter",
]


def load_registry(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise RuntimeError(f"registry not found at {path}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"registry at {path} is not valid JSON: {e}") from e


def assert_preconditions(reg: dict) -> None:
    line_attrs = reg["attributes"]["line_attributes"]
    afm = reg["attribute_feature_mapping"]
    avb = reg["attribute_value_binding"]
    rtr = reg["relation_target_registry"]

    if "Convergence" in line_attrs:
        raise RuntimeError("precondition failed: 'Convergence' already in attributes.line_attributes")
    if "Convergence_Location" in line_attrs:
        raise RuntimeError("precondition failed: 'Convergence_Location' already in attributes.line_attributes")
    if "Convergence" in afm or "Convergence_Location" in afm:
        raise RuntimeError("precondition failed: Convergence/Convergence_Location already in attribute_feature_mapping")
    if "Convergence" in avb or "Convergence_Location" in avb:
        raise RuntimeError("precondition failed: Convergence/Convergence_Location already in attribute_value_binding")

    missing_targets = [t for t in REQUIRED_RELATION_TARGETS if t not in rtr]
    if missing_targets:
        raise RuntimeError(f"precondition failed: relation_target_registry missing required targets: {missing_targets}")


def apply_mutations(reg: dict) -> dict:
    avb_keys_before = set(reg["attribute_value_binding"].keys())

    for attr in NEW_ATTRS:
        reg["attributes"]["line_attributes"].append(attr)

    for attr in NEW_ATTRS:
        reg["attribute_feature_mapping"][attr] = list(OWNER_FEATURES)

    reg["change_log"].append(
        {
            "version": "1.6.0",
            "date": "2026-08-22",
            "author": "chat, awaiting Sulabh validation",
            "change": (
                "Add relation attributes 'Convergence' and 'Convergence_Location' (Pattern C, "
                "symmetric two-line convergence). Pure relation attributes: value=null, relation_target "
                "drawn from relation_target_registry, matched via palm_rules_table match()'s existing "
                "targets channel. Symmetry handled by CANONICALIZATION at extraction time (owner = "
                "alphabetically-first feature of the pair, target = the other). Convergence = 'line A "
                "meets line B'; Convergence_Location (single generic slot) = a third landmark associated "
                "with that convergence (either the meeting point or a shared continuation landmark, e.g. "
                "F025b fate+heart ascend Jupiter) -- disambiguated in claim prose, NOT structurally split, "
                "because vision (gpt-4o) reliability on meet-at vs continue-to is below floor; all "
                "location-gated C rules carry a LOWER-CONFIDENCE flag. Registry-legal only -- NOT yet in "
                "any vision-prompt menu, extractor label map, or rule file; unreachable until STEP 2 "
                "(extractor) and STEP 3 (vision) wiring. attribute_value_binding deliberately UNTOUCHED."
            ),
            "canonical_owner_rule": (
                "For any convergence pair {A, B}, owner = min(A, B) by string sort, relation_target = the "
                "other. In-scope owners: Line of Fate, Line of Head, Line of Health, Line of Heart. Line of "
                "Life is never an owner among in-scope pairs."
            ),
            "unlocks": "Fate F025b (PARKED_RELATION) becomes authorable once STEP 3 lands.",
        }
    )

    reg["meta"]["version"] = "1.6.0"
    reg["meta"]["total_attributes"] = reg["meta"]["total_attributes"] + 2

    avb_keys_after = set(reg["attribute_value_binding"].keys())
    if avb_keys_after != avb_keys_before:
        raise RuntimeError(
            f"post-mutation invariant violated: attribute_value_binding keys changed "
            f"({avb_keys_before} -> {avb_keys_after})"
        )

    return reg


def assert_postconditions(reg: dict) -> None:
    line_attrs = reg["attributes"]["line_attributes"]
    afm = reg["attribute_feature_mapping"]

    for attr in NEW_ATTRS:
        if attr not in line_attrs:
            raise RuntimeError(f"postcondition failed: '{attr}' missing from attributes.line_attributes")
        if attr not in afm:
            raise RuntimeError(f"postcondition failed: '{attr}' missing from attribute_feature_mapping")
        if afm[attr] != OWNER_FEATURES:
            raise RuntimeError(f"postcondition failed: attribute_feature_mapping['{attr}'] != {OWNER_FEATURES}")

    if reg["meta"]["total_attributes"] != 44:
        raise RuntimeError(f"postcondition failed: meta.total_attributes == {reg['meta']['total_attributes']}, expected 44")

    if reg["meta"]["version"] != "1.6.0":
        raise RuntimeError(f"postcondition failed: meta.version == {reg['meta']['version']}, expected 1.6.0")


def main() -> None:
    raw_before = REGISTRY_PATH.read_text(encoding="utf-8")
    reg_before = load_registry(REGISTRY_PATH)

    old_line_attrs_count = len(reg_before["attributes"]["line_attributes"])
    old_afm_keys_count = len(reg_before["attribute_feature_mapping"])
    old_total_attributes = reg_before["meta"]["total_attributes"]
    avb_keys_before = sorted(reg_before["attribute_value_binding"].keys())

    assert_preconditions(reg_before)

    reg = apply_mutations(reg_before)

    assert_postconditions(reg)

    new_text = json.dumps(reg, indent=2, ensure_ascii=False) + "\n"

    try:
        reloaded = json.loads(new_text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"serialized output failed to reload as JSON: {e}") from e

    assert_postconditions(reloaded)

    REGISTRY_PATH.write_text(new_text, encoding="utf-8")

    # Reload from disk to confirm the write landed correctly.
    reg_after = load_registry(REGISTRY_PATH)
    assert_postconditions(reg_after)

    avb_keys_after = sorted(reg_after["attribute_value_binding"].keys())
    if avb_keys_after != avb_keys_before:
        raise RuntimeError(
            f"FATAL post-write check: attribute_value_binding keys changed on disk "
            f"({avb_keys_before} -> {avb_keys_after})"
        )

    new_line_attrs_count = len(reg_after["attributes"]["line_attributes"])
    new_afm_keys_count = len(reg_after["attribute_feature_mapping"])
    new_total_attributes = reg_after["meta"]["total_attributes"]

    print("=== Pattern C relation primitive -- STEP 1 (ontology_registry.json) ===")
    print()
    print(f"line_attributes count:            {old_line_attrs_count} -> {new_line_attrs_count}")
    print(f"attribute_feature_mapping keys:    {old_afm_keys_count} -> {new_afm_keys_count}")
    print(f"meta.total_attributes:             {old_total_attributes} -> {new_total_attributes}")
    print()
    for attr in NEW_ATTRS:
        print(f"  attribute_feature_mapping['{attr}'] = {OWNER_FEATURES}")
    print()
    print(f"attribute_value_binding: UNCHANGED ({len(avb_keys_after)} keys)")
    print()
    print("relation targets required by Pattern C -- all already registry-legal, none added:")
    for t in REQUIRED_RELATION_TARGETS:
        print(f"  - {t}")
    print()
    print("Nothing written outside data/ontology_registry.json. No git commit made.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ABORTED, no changes applied (or applied only in-memory): {e}", file=sys.stderr)
        sys.exit(1)
