"""
diagnostics/validate_ending_point_fix.py
THROWAWAY proof script for the Ending_Point->Position reachability fix
applied to FT_003/FT_005/FT_007/FT_008. Not imported by anything, safe to
delete after this run.

THE BUG THIS PROVES FIXED: the prior dogfood run (real hand,
palm_right_test.jpg) found that agent.interpretive.observation_extractor's
_RELATIONAL_ATTRIBUTE_MAP emits the vision TERMINATION field into the
"Position" attribute -- but FT_003/FT_005/FT_007/FT_008 were keyed on
"Ending_Point", so they could never fire from real extraction output on
ANY hand, regardless of what the line actually terminates on. The prior
synthetic validation pass (validate_fate_006_015.py and earlier) never
caught this because it built `targets` dicts BY HAND using "Ending_Point"
as the key -- matching the rules' own (wrong) attribute name, not what the
real extractor actually produces. THIS script is deliberately the
opposite: it builds `targets` keyed by "Position" -- exactly what
observation_extractor.extract_relational_targets() really emits -- and
checks that the FIXED rules now fire against that.

Uses agent.interpretive.palm_rules_table.match() directly (deterministic,
NO LLM) against the real, now-patched
data/palm_rules/palm_rules_fate_line_v1.json. All 4 rules are
verified:true on disk already (Sulabh, S97) -- loaded as-is, no in-memory
override needed here (unlike FT_006/FT_015's earlier validation, which
were still verified:false at the time).
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

_RULES_PATH = _REPO_ROOT / "data" / "palm_rules" / "palm_rules_fate_line_v1.json"

_results: dict[str, object] = {}
_failures: list[str] = []


def _report(label: str, passed: bool, detail: str) -> None:
    _results[label] = {"passed": passed, "detail": detail}
    print(f"[{'PASS' if passed else 'FAIL'}] {label}: {detail}")
    if not passed:
        _failures.append(label)


def main() -> int:
    try:
        from agent.interpretive.palm_rules_table import load_rules, match
    except Exception as exc:
        print(f"[FATAL] failed to import palm_rules_table: {exc}")
        traceback.print_exc()
        return 2

    try:
        rules = load_rules(_RULES_PATH)
    except Exception as exc:
        print(f"[FATAL] failed to load {_RULES_PATH}: {exc}")
        traceback.print_exc()
        return 2

    by_id = {r.rule_id: r for r in rules}
    for needed in ("FT_003", "FT_005", "FT_007", "FT_008"):
        if needed not in by_id:
            print(f"[FATAL] {needed} not found in {_RULES_PATH}")
            return 2
        term_attr = next(
            (a.attribute for a in by_id[needed].antecedents if a.relation_target), None,
        )
        print(f"  {needed}: verified={by_id[needed].verified}, termination attribute={term_attr!r}")

    # --- FT_005: Position=Mount of Jupiter (real-extractor-shaped targets) ---
    obs = {}
    targets = {"Line of Fate": {"Position": "Mount of Jupiter"}}
    fired = {r.rule_id for r in match(obs, {}, rules, targets)}
    _report(
        "FT_005_fires_on_Position_Mount_of_Jupiter",
        "FT_005" in fired,
        f"targets={targets} -> fired={sorted(fired)} (expected FT_005 present)",
    )

    # --- FT_007: Position=Line of Heart ---
    obs = {}
    targets = {"Line of Fate": {"Position": "Line of Heart"}}
    fired = {r.rule_id for r in match(obs, {}, rules, targets)}
    _report(
        "FT_007_fires_on_Position_Line_of_Heart",
        "FT_007" in fired,
        f"targets={targets} -> fired={sorted(fired)} (expected FT_007 present)",
    )

    # --- FT_008: Position=Line of Head ---
    obs = {}
    targets = {"Line of Fate": {"Position": "Line of Head"}}
    fired = {r.rule_id for r in match(obs, {}, rules, targets)}
    _report(
        "FT_008_fires_on_Position_Line_of_Head",
        "FT_008" in fired,
        f"targets={targets} -> fired={sorted(fired)} (expected FT_008 present)",
    )

    # --- FT_003: Starting_Point=Wrist + Slope=straight + Position=Mount of Saturn (compound) ---
    obs = {"Line of Fate": {"Slope": "straight"}}
    targets = {"Line of Fate": {"Starting_Point": "Wrist", "Position": "Mount of Saturn"}}
    fired = {r.rule_id for r in match(obs, {}, rules, targets)}
    _report(
        "FT_003_fires_on_Wrist_straight_Position_Mount_of_Saturn",
        "FT_003" in fired,
        f"observation={obs}, targets={targets} -> fired={sorted(fired)} (expected FT_003 present)",
    )

    # --- Negative control: the OLD (wrong) Ending_Point-keyed targets must NOT fire these anymore ---
    # (proves the fix actually changed behavior, not that match() is permissive)
    obs = {}
    targets_old_shape = {"Line of Fate": {"Ending_Point": "Mount of Jupiter"}}
    fired = {r.rule_id for r in match(obs, {}, rules, targets_old_shape)}
    _report(
        "FT_005_no_longer_fires_on_old_Ending_Point_shape",
        "FT_005" not in fired,
        f"targets={targets_old_shape} (old wrong shape) -> fired={sorted(fired)} "
        f"(expected FT_005 ABSENT -- confirms the rule really changed attribute, not a fluke)",
    )

    print("\n=== SUMMARY ===")
    for label, r in _results.items():
        print(f"  [{'PASS' if r['passed'] else 'FAIL'}] {label}")

    if _failures:
        print(f"\n{len(_failures)} FAILED step(s): {_failures}")
        return 1

    print("\nAll steps PASSED. Ending_Point->Position fix confirmed live for FT_003/FT_005/FT_007/FT_008.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
