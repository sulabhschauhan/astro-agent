"""
diagnostics/validate_fate_006_015.py
THROWAWAY synthetic firing + routing test for FT_006 (Length=
cutting_into_finger_of_Saturn) and FT_015 (Starting_Point relation_target=
Plain of Mars), the two Fate rules whose vision-emission menus were widened
in the immediately preceding arc. Proves WIRING only -- does NOT license
verified:true on either rule (both stay verified:false in the source file;
this script never writes to it). Not imported by anything, safe to delete.

LEVEL A (deterministic, NO LLM): hand-built observation dicts run through
the REAL agent/interpretive/palm_rules_table.match() engine, loading the
real data/palm_rules/palm_rules_fate_line_v1.json. FT_006/FT_015 are both
verified:false on disk (correct -- no self-certification); to exercise
match()'s real firing logic this script builds IN-MEMORY-ONLY copies with
verified overridden to True via dataclasses.replace() -- the source file
is never opened for writing.

LEVEL B (uses the real extraction machinery, two DIFFERENT code paths):
  B1 -- FT_006's Length token rides observation_extractor.extract_observation,
        the LLM-mediated (gpt-4o-mini) SOFT free-text path.
  B2 -- FT_015's Starting_Point/Plain-of-Mars token rides
        observation_extractor.extract_relational_targets, a pure
        deterministic STRING PARSE of the vision model's own structured
        ORIGIN field -- no LLM call in this half at all.
B2 proves the PARSE accepts the new landmark; it says nothing about
whether GPT-4o's vision call would ever actually write "ORIGIN: Plain of
Mars" for a real photographed hand -- that stays UNPROVEN, same posture as
B1's clean-signal result for BREAK TYPE/broken_overlapping in the prior arc.
"""

from __future__ import annotations

import sys
import traceback
from dataclasses import replace
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


def level_a() -> None:
    print("\n=== LEVEL A: engine firing (deterministic, NO LLM) ===")
    try:
        from agent.interpretive.palm_rules_table import load_rules, match
    except Exception as exc:
        raise RuntimeError(
            f"validate_fate_006_015: failed to import palm_rules_table: {exc}"
        ) from exc

    try:
        rules = load_rules(_RULES_PATH)
    except Exception as exc:
        raise RuntimeError(
            f"validate_fate_006_015: failed to load {_RULES_PATH}: {exc}"
        ) from exc

    by_id = {r.rule_id: r for r in rules}
    for needed in ("FT_006", "FT_015"):
        if needed not in by_id:
            raise RuntimeError(
                f"validate_fate_006_015: {needed} not found in {_RULES_PATH} "
                f"-- cannot run Level A. Rule ids present: {sorted(by_id)}"
            )

    ft006 = replace(by_id["FT_006"], verified=True)
    ft015 = replace(by_id["FT_015"], verified=True)
    print(
        f"  Loaded FT_006 (source verified={by_id['FT_006'].verified}) and "
        f"FT_015 (source verified={by_id['FT_015'].verified}) from disk; "
        "test copies verified=True IN-MEMORY ONLY for this script's match() calls."
    )
    print(f"  FT_006 antecedent: {ft006.antecedents[0].feature}/{ft006.antecedents[0].attribute}={ft006.antecedents[0].value}")
    print(f"  FT_015 antecedent: {ft015.antecedents[0].feature}/{ft015.antecedents[0].attribute} relation_target={ft015.antecedents[0].relation_target}")

    test_rules = [ft006, ft015]

    # --- A1: FT_006's own observation fires FT_006 ---
    obs_a1 = {"Line of Fate": {"Length": "cutting_into_finger_of_Saturn"}}
    fired_a1 = {r.rule_id for r in match(obs_a1, {}, test_rules)}
    _report(
        "A1_FT006_fires_on_own_observation",
        "FT_006" in fired_a1,
        f"observation={obs_a1} -> fired={sorted(fired_a1)} (expected FT_006 present)",
    )

    # --- A2: FT_015's own observation fires FT_015 (relation_target via targets dict) ---
    obs_a2: dict[str, dict[str, str]] = {}
    targets_a2 = {"Line of Fate": {"Starting_Point": "Plain of Mars"}}
    fired_a2 = {r.rule_id for r in match(obs_a2, {}, test_rules, targets_a2)}
    _report(
        "A2_FT015_fires_on_own_observation",
        "FT_015" in fired_a2,
        f"observation={obs_a2}, targets={targets_a2} -> fired={sorted(fired_a2)} (expected FT_015 present)",
    )

    # --- A3: cross-fire guard -- neither observation should fire the OTHER rule ---
    a3_1_ok = "FT_015" not in fired_a1
    a3_2_ok = "FT_006" not in fired_a2
    _report(
        "A3_cross_fire_guard",
        a3_1_ok and a3_2_ok,
        f"A1's observation fired FT_015? {'FT_015' in fired_a1} (expected False); "
        f"A2's observation fired FT_006? {'FT_006' in fired_a2} (expected False)",
    )


def level_b() -> None:
    print("\n=== LEVEL B: extractor routing (2 different code paths) ===")

    # --- B1: soft/LLM path -- FT_006's Length token via extract_observation ---
    try:
        from agent.interpretive.observation_extractor import extract_observation
    except Exception as exc:
        raise RuntimeError(
            f"validate_fate_006_015: failed to import observation_extractor: {exc}"
        ) from exc

    try:
        from openai import OpenAI
        client = OpenAI()
    except Exception as exc:
        raise RuntimeError(
            f"validate_fate_006_015: failed to construct a live OpenAI client "
            f"(is OPENAI_API_KEY set?): {exc}"
        ) from exc

    b1_text = (
        "FATE LINE: present, moderately deep.\n"
        "  SLOPE: straight\n"
        "  ORIGIN: Wrist\n"
        "  TERMINATION: Mount of Saturn\n"
        "  PROXIMITY: n/a to none\n"
        "  BRANCHES_TO: none\n"
        "  BREAK TYPE: n/a\n"
        "  LENGTH EXTENT: cutting_into_finger_of_Saturn"
    )
    try:
        record_b1 = extract_observation(
            {"fate line": [b1_text]}, client=client, model="gpt-4o-mini",
        )
    except Exception as exc:
        raise RuntimeError(
            f"validate_fate_006_015: B1 extract_observation call failed: {exc}"
        ) from exc

    fobs_b1 = record_b1.features.get("Line of Fate")
    token_b1 = fobs_b1.tokens.get("Length") if fobs_b1 else None
    value_b1 = token_b1.get("value") if token_b1 else None
    _report(
        "B1_extract_observation_routes_Length_token",
        value_b1 == "cutting_into_finger_of_Saturn",
        f"input LENGTH EXTENT line = 'cutting_into_finger_of_Saturn' -> emitted Length token = "
        f"{value_b1!r} (unmapped for Line of Fate: {fobs_b1.unmapped if fobs_b1 else 'N/A (feature missing)'})",
    )

    # --- B2: pure deterministic parse -- FT_015's relation_target via extract_relational_targets ---
    try:
        from agent.interpretive.observation_extractor import extract_relational_targets
    except Exception as exc:
        raise RuntimeError(
            f"validate_fate_006_015: failed to import extract_relational_targets: {exc}"
        ) from exc

    b2_text = (
        "FATE LINE: present, moderately deep\n"
        "  ORIGIN: Plain of Mars\n"
        "  TERMINATION: Mount of Saturn\n"
        "  PROXIMITY: n/a to none\n"
        "  BRANCHES_TO: none\n"
    )
    try:
        targets_b2 = extract_relational_targets(b2_text)
    except Exception as exc:
        raise RuntimeError(
            f"validate_fate_006_015: B2 extract_relational_targets call failed: {exc}"
        ) from exc

    origin_b2 = targets_b2.get("Line of Fate", {}).get("Starting_Point")
    _report(
        "B2_extract_relational_targets_routes_Plain_of_Mars",
        origin_b2 == "Plain of Mars",
        f"input 'ORIGIN: Plain of Mars' -> extract_relational_targets returned "
        f"targets['Line of Fate']['Starting_Point'] = {origin_b2!r}. NO LLM call in this "
        f"half -- pure deterministic parse. Proves the PARSE accepts the new landmark; does "
        f"NOT prove GPT-4o's vision call would ever actually write this for a real photo.",
    )


def main() -> int:
    try:
        level_a()
    except Exception as exc:
        print(f"\n[FATAL] Level A raised: {exc}")
        traceback.print_exc()
        return 2

    try:
        level_b()
    except Exception as exc:
        print(f"\n[FATAL] Level B raised: {exc}")
        traceback.print_exc()
        return 2

    print("\n=== SUMMARY ===")
    for label, r in _results.items():
        print(f"  [{'PASS' if r['passed'] else 'FAIL'}] {label}")

    if _failures:
        print(f"\n{len(_failures)} FAILED step(s): {_failures}")
        return 1

    print("\nAll steps PASSED.")
    print("REMINDER: this proves WIRING only. FT_006 and FT_015 stay verified:false.")
    print("Whether real vision (GPT-4o on an actual photo) can distinguish a Saturn-finger")
    print("extension or a Plain-of-Mars origin from their neighboring configurations")
    print("remains completely UNPROVEN.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
