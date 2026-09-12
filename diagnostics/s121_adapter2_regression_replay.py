"""S121 adapter #2 -- STEP 2 regression proof. Deterministic, no vision cost.

Replays the REAL relational parse (extract_relations/extract_mount_development,
both pure regex, no LLM) directly from each capture's own raw vision text, and
reconstructs the value-only vision_payload from that capture's own already-
captured `observation` dict (excluding Proximity/Development, which never go
through to_tokens -- they merge in afterward in palm_reading.py, unaffected by
this task's edit). Runs palm_rules_table.match() BEFORE (old flat-pool-only
gate, reimplemented inline against the untouched _is_valid_triple) vs AFTER
(current to_tokens(), with the new BOUND-attribute vocab_adapter routing) and
diffs the fired-rule-id sets.
"""
import json
import sys

sys.path.insert(0, ".")

from agent.interpretive import observation_extractor as oe
from agent.interpretive import observation_to_tokens as ott
from agent.interpretive import palm_rules_table

_MERGE_ONLY_ATTRS = {"Proximity", "Development"}


def _old_to_tokens(vision_payload: dict) -> dict:
    """Exact reimplementation of to_tokens()'s PRE-edit gate: unconditional
    _is_valid_triple, no menu_for/vocab_adapter branch at all -- the code as
    it existed before this task's edit (verified against the diff)."""
    observation: dict[str, dict[str, str]] = {}
    for feature, attributes in vision_payload.items():
        for attribute, entry in attributes.items():
            value = entry["value"]
            if ott._is_valid_triple(feature, attribute, value):
                observation.setdefault(feature, {})[attribute] = value
    return observation


def replay(raw_text_path_key: str, capture: dict, capture_name: str) -> dict:
    raw_text = capture[raw_text_path_key]
    captured_observation = capture.get("observation") or (capture.get("rules_engine") or {}).get("observation") or {}

    rel = oe.extract_relations(raw_text)
    from agent.interpretive.palm_reading import _assemble_relational_targets
    contacts_targets = _assemble_relational_targets(rel["contacts"])
    targets = oe.merge_relational_targets(rel["targets"], contacts_targets)
    # _flatten_proximity_degrees lives in palm_reading.py; reproduce its one-line
    # job inline (drop the {value,confidence} wrapper -> bare degree string) to
    # avoid importing palm_reading.py (heavier, client-dependent module) for a
    # pure-parse replay.
    proximity_flat = {
        feat: {"Proximity": attrs["Proximity"]["value"]}
        for feat, attrs in rel["proximity"].items()
    }

    mount_dev_raw = oe.extract_mount_development(raw_text)
    mount_dev = oe.translate_mount_development(mount_dev_raw)

    vision_payload = {}
    for feature, attrs in captured_observation.items():
        for attribute, value in attrs.items():
            if attribute in _MERGE_ONLY_ATTRS:
                continue
            vision_payload.setdefault(feature, {})[attribute] = {"value": value, "confidence": 1.0}

    observation_before = _old_to_tokens(vision_payload)
    observation_after, _magnitudes = ott.to_tokens(vision_payload)

    for merged in (observation_before, observation_after):
        for feature, attrs in proximity_flat.items():
            merged.setdefault(feature, {})["Proximity"] = attrs["Proximity"]
        for feature, attrs in mount_dev.items():
            merged.setdefault(feature, {})["Development"] = attrs["Development"]

    magnitudes = {feature: {attr: 1.0 for attr in attrs} for feature, attrs in captured_observation.items()}

    rules = palm_rules_table.load_rule_set()
    fired_before = sorted(r.rule_id for r in palm_rules_table.match(observation_before, magnitudes, rules, targets=targets))
    fired_after = sorted(r.rule_id for r in palm_rules_table.match(observation_after, magnitudes, rules, targets=targets))

    obs_diff = {}
    for feature in set(observation_before) | set(observation_after):
        b = observation_before.get(feature, {})
        a = observation_after.get(feature, {})
        if b != a:
            obs_diff[feature] = {"before": b, "after": a}

    return {
        "capture": capture_name,
        "captured_observation": captured_observation,
        "vision_payload_reconstructed": vision_payload,
        "observation_before": observation_before,
        "observation_after": observation_after,
        "observation_diff": obs_diff,
        "fired_before": fired_before,
        "fired_after": fired_after,
        "fired_diff": {
            "only_before": sorted(set(fired_before) - set(fired_after)),
            "only_after": sorted(set(fired_after) - set(fired_before)),
        },
        "capture_reported_fired_or_surviving": capture.get("fired_rule_ids") or capture.get("surviving_rule_ids")
        or (capture.get("rules_engine") or {}).get("fired_rule_ids"),
    }


results = []
s117 = json.load(open("diagnostics/s117_live_confirmation_raw.json", encoding="utf-8"))
results.append(replay("palm_right_description_raw", s117, "s117_live_confirmation"))

s120 = json.load(open("diagnostics/s120_live_palm_run_raw.json", encoding="utf-8"))
results.append(replay("vision_description_raw", s120, "s120_live_palm_run"))

json.dump(results, open("diagnostics/s121_adapter2_regression_replay_raw.json", "w", encoding="utf-8"), indent=1)

for r in results:
    print("===", r["capture"])
    print("  observation_diff:", r["observation_diff"] or "NONE")
    print("  fired_before:", r["fired_before"])
    print("  fired_after: ", r["fired_after"])
    print("  fired_diff:  ", r["fired_diff"])
    print("  capture's own reported fired/surviving ids:", r["capture_reported_fired_or_surviving"])
    print()
