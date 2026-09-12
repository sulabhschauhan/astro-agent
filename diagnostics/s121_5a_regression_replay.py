"""S121 #5A -- STEP 2 regression proof. Compares palm_rules_table.match()
fired-sets using the OLD (pre-migration, well_marked literal) vs NEW
(migrated, deep literal) palm_rules_fate_line_v1.json, holding every other
rule file and the observation/targets constant -- isolates the migration's
effect from everything else. Deterministic, no vision cost: relational
targets are replayed via extract_relations/_assemble_relational_targets
(pure regex, no LLM) directly from each capture's own raw vision text; the
value-only observation is reconstructed from that capture's own already-
captured `observation` dict (unaffected by this task -- the adapter-#2 wire
is reverted, so to_tokens' flat-pool gate is exactly as it was pre-S121
adapter work)."""
import json
import sys

sys.path.insert(0, ".")

from pathlib import Path

from agent.interpretive import observation_extractor as oe
from agent.interpretive import palm_rules_table
from agent.interpretive.palm_reading import _assemble_relational_targets

RULES_DIR = Path("data/palm_rules")
OLD_FATE_PATH = Path(
    "C:/Users/sulab/AppData/Local/Temp/claude/C--Users-sulab-Documents-Python-Scripts-astro-agent/"
    "64b56063-7481-4a8c-bd8e-b7493bc480b8/scratchpad/palm_rules_fate_line_v1_OLD.json"
)
CURRENT_FATE_PATH = RULES_DIR / "palm_rules_fate_line_v1.json"


def build_rule_set(fate_path: Path) -> tuple:
    new_rules = palm_rules_table.load_rule_set(RULES_DIR)
    current_fate_ids = {r.rule_id for r in palm_rules_table.load_rules(CURRENT_FATE_PATH)}
    substitute_fate_rules = palm_rules_table.load_rules(fate_path)
    kept = [r for r in new_rules if r.rule_id not in current_fate_ids]
    return tuple(kept) + substitute_fate_rules


old_rules = build_rule_set(OLD_FATE_PATH)
new_rules = build_rule_set(CURRENT_FATE_PATH)

# Sanity: same rule_id universe, only the two literals differ.
assert {r.rule_id for r in old_rules} == {r.rule_id for r in new_rules}
old_ft001 = next(r for r in old_rules if r.rule_id == "FT_001")
new_ft001 = next(r for r in new_rules if r.rule_id == "FT_001")
old_ft009 = next(r for r in old_rules if r.rule_id == "FT_009")
new_ft009 = next(r for r in new_rules if r.rule_id == "FT_009")
print("FT_001 Depth antecedent OLD value:", [a.value for a in old_ft001.antecedents if a.attribute == "Depth"])
print("FT_001 Depth antecedent NEW value:", [a.value for a in new_ft001.antecedents if a.attribute == "Depth"])
print("FT_009 Depth antecedent OLD value:", [a.value for a in old_ft009.antecedents if a.attribute == "Depth"])
print("FT_009 Depth antecedent NEW value:", [a.value for a in new_ft009.antecedents if a.attribute == "Depth"])
print()


def replay(raw_text_path_key: str, capture: dict, capture_name: str) -> dict:
    raw_text = capture[raw_text_path_key]
    captured_observation = capture.get("observation") or (capture.get("rules_engine") or {}).get("observation") or {}

    rel = oe.extract_relations(raw_text)
    contacts_targets = _assemble_relational_targets(rel["contacts"])
    targets = oe.merge_relational_targets(rel["targets"], contacts_targets)

    proximity_flat = {feat: {"Proximity": attrs["Proximity"]["value"]} for feat, attrs in rel["proximity"].items()}
    mount_dev = oe.translate_mount_development(oe.extract_mount_development(raw_text))

    observation = {}
    for feature, attrs in captured_observation.items():
        for attribute, value in attrs.items():
            observation.setdefault(feature, {})[attribute] = value
    for feature, attrs in proximity_flat.items():
        observation.setdefault(feature, {})["Proximity"] = attrs["Proximity"]
    for feature, attrs in mount_dev.items():
        observation.setdefault(feature, {})["Development"] = attrs["Development"]

    magnitudes = {feature: {attr: 1.0 for attr in attrs} for feature, attrs in observation.items()}

    fired_old = sorted(r.rule_id for r in palm_rules_table.match(observation, magnitudes, old_rules, targets=targets))
    fired_new = sorted(r.rule_id for r in palm_rules_table.match(observation, magnitudes, new_rules, targets=targets))

    return {
        "capture": capture_name,
        "targets": targets,
        "observation": observation,
        "fired_old": fired_old,
        "fired_new": fired_new,
        "fired_diff": {
            "only_old": sorted(set(fired_old) - set(fired_new)),
            "only_new": sorted(set(fired_new) - set(fired_old)),
        },
        "capture_reported_fired_or_surviving": capture.get("fired_rule_ids") or capture.get("surviving_rule_ids")
        or (capture.get("rules_engine") or {}).get("fired_rule_ids"),
    }


results = []
s117 = json.load(open("diagnostics/s117_live_confirmation_raw.json", encoding="utf-8"))
results.append(replay("palm_right_description_raw", s117, "s117_live_confirmation"))

s120 = json.load(open("diagnostics/s120_live_palm_run_raw.json", encoding="utf-8"))
results.append(replay("vision_description_raw", s120, "s120_live_palm_run"))

json.dump(results, open("diagnostics/s121_5a_regression_replay_raw.json", "w", encoding="utf-8"), indent=1, default=str)

for r in results:
    print("===", r["capture"])
    print("  Fate Starting_Point target:", r["targets"].get("Line of Fate", {}).get("Starting_Point"))
    print("  fired_old:", r["fired_old"])
    print("  fired_new:", r["fired_new"])
    print("  fired_diff:", r["fired_diff"])
    print("  capture's own reported fired/surviving ids:", r["capture_reported_fired_or_surviving"])
    print()
