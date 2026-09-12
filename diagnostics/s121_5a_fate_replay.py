"""
diagnostics/s121_5a_fate_replay.py

S121 #5A -- deterministic BEFORE/AFTER fired-set replay for the 4 Fate-file
worklist rewrites. NO vision call. Feeds the SAVED observation/targets from
diagnostics/s120_live_palm_run_raw.json into the LIVE engine path exactly as
_prepare_claims_from_rules calls it: palm_rules_table.match(observation,
magnitudes, rules, targets=targets) -> palm_rules_table.resolve_priority(fired).

magnitudes is passed as {} -- the raw captures never persisted the full
per-feature magnitudes dict (only magnitudes["_dropped"], as "dropped_tokens"),
and reconstructing it requires the live ObservationRecord from the original
LLM extraction call, which is not available offline. This is harmless for
this specific replay: the ONLY comparative antecedents anywhere in the loaded
rule set are H_010a/H_010b (palm_rules_head_heart_v1.json, both Depth
comparisons) -- confirmed by direct grep of all 4 rule files -- and
_antecedent_fires' comparative branch returns False whenever either side's
magnitudes are missing, which reproduces the ALREADY-RECORDED live outcome
(neither H_010a nor H_010b appears in s120's or s117's recorded
surviving_rule_ids). No Fate-file antecedent is comparative, so magnitudes
plays no role in this task's actual before/after comparison.

s117_live_confirmation_raw.json is NOT used for the replay: it has no
'targets' key at all (it predates that capture field), so a faithful
match()/resolve_priority() call cannot be reconstructed for it without
guessing at relation-target state that was never recorded. Its own recorded
surviving_rule_ids/fired_rule_ids are reported for context only, not replayed.
"""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from agent.interpretive import palm_rules_table

S120 = pathlib.Path("diagnostics/s120_live_palm_run_raw.json")


def replay_s120() -> dict:
    d = json.loads(S120.read_text(encoding="utf-8"))
    re = d["rules_engine"]
    observation = re["observation"]
    targets = re["targets"]

    rules = palm_rules_table.load_rule_set()
    fired = palm_rules_table.match(observation, {}, rules, targets=targets)
    survivors, suppression_log = palm_rules_table.resolve_priority(fired)

    return {
        "recorded_fired": re["fired_rule_ids"],
        "recorded_surviving": re["surviving_rule_ids"],
        "replayed_fired": sorted(r.rule_id for r in fired),
        "replayed_surviving": sorted(r.rule_id for r in survivors),
        "replayed_suppression_log": suppression_log,
    }


def main() -> None:
    result = replay_s120()
    print(json.dumps(result, indent=2))
    match_fired = sorted(result["recorded_fired"]) == result["replayed_fired"]
    match_surviving = sorted(result["recorded_surviving"]) == result["replayed_surviving"]
    print(f"fired matches recorded:     {match_fired}")
    print(f"surviving matches recorded: {match_surviving}")


if __name__ == "__main__":
    main()
