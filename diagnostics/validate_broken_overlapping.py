"""
diagnostics/validate_broken_overlapping.py
THROWAWAY synthetic validation script -- proves WIRING only, does NOT
license verified:true on FT_011/FT_012 (real-image vision reliability
stays unproven; see Level B's own caveat below). Not imported by anything,
not part of the test suite, safe to delete after this run.

LEVEL A (deterministic, NO LLM): constructs observation dicts by hand and
runs them through the REAL agent/interpretive/palm_rules_table.match()
engine (the deterministic equality-matching function palm_select.py's hard
gate calls internally), loading the real
data/palm_rules/palm_rules_fate_line_v1.json. FT_011/FT_012 are both
Continuity-only, single-antecedent rules -- per PALM_PIPELINE.md's
hard/soft partition doctrine, "broken"/"chained" are named SOFT-class
terms, meaning palm_select.py's FULL select() pipeline would ordinarily
route them to an LLM soft-judgment call. Level A deliberately bypasses
select() and drives palm_rules_table.match() directly instead -- that
function's antecedent-equality logic is hard/soft-agnostic (it treats
Continuity=broken as a plain equality check, same as any other attribute),
so calling it directly is a legitimate, LLM-free way to isolate and prove
the ANTECEDENT-DISCRIMINATION wiring this task is about, without
contradicting the "NO LLM" constraint.

IMPORTANT: FT_011 and FT_012 are both `"verified": false` in the source
file (correctly -- no self-certification per this project's convention).
match() fail-closed-skips any rule where verified is not True. To exercise
the REAL antecedent-matching logic despite that, this script loads the
real rules via load_rules() (proving the file parses/loads correctly) and
then builds IN-MEMORY copies with verified overridden to True via
dataclasses.replace() -- the source JSON file is never touched, opened for
writing, or otherwise modified by this script. This override exists solely
so Level A can observe match()'s real firing behavior; it has no bearing
on ratification.

LEVEL B (uses the real gpt-4o-mini extraction call, agent/interpretive/
observation_extractor.extract_observation): feeds synthetic raw FATE-LINE
vision text (as palm_processor.describe_palm_image would produce it, now
carrying the new BREAK TYPE field from Step 2) through the real extraction
LLM call and inspects the emitted Continuity token. B1 is a clean-signal
case (assertable). B2 is the hardest case -- a signal collision between the
new structured BREAK TYPE field and the pre-existing inherited free-text
break wording -- and is a MEASURE step only, no assertion, by design: we do
not yet know which signal should win, so this script reports the outcome
for a human to ratify, not "pass"/"fail" it.
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


def _report(label: str, passed: bool | None, detail: str) -> None:
    """passed=True/False -> asserted step; passed=None -> MEASURE step (no
    pass/fail verdict recorded, per Level B2's explicit design)."""
    _results[label] = {"passed": passed, "detail": detail}
    tag = "MEASURE" if passed is None else ("PASS" if passed else "FAIL")
    print(f"[{tag}] {label}: {detail}")
    if passed is False:
        _failures.append(label)


def level_a() -> None:
    print("\n=== LEVEL A: engine firing (deterministic, NO LLM) ===")
    try:
        from agent.interpretive.palm_rules_table import load_rules, match
    except Exception as exc:
        raise RuntimeError(
            f"validate_broken_overlapping: failed to import palm_rules_table: {exc}"
        ) from exc

    try:
        rules = load_rules(_RULES_PATH)
    except Exception as exc:
        raise RuntimeError(
            f"validate_broken_overlapping: failed to load {_RULES_PATH}: {exc}"
        ) from exc

    by_id = {r.rule_id: r for r in rules}
    for needed in ("FT_011", "FT_012"):
        if needed not in by_id:
            raise RuntimeError(
                f"validate_broken_overlapping: {needed} not found in {_RULES_PATH} "
                f"-- cannot run Level A. Rule ids present: {sorted(by_id)}"
            )

    # IN-MEMORY ONLY override -- see module docstring. Source file untouched.
    ft011 = replace(by_id["FT_011"], verified=True)
    ft012 = replace(by_id["FT_012"], verified=True)
    print(
        f"  Loaded FT_011 (source verified={by_id['FT_011'].verified}) and "
        f"FT_012 (source verified={by_id['FT_012'].verified}) from disk; "
        "test copies verified=True IN-MEMORY ONLY for this script's match() calls."
    )
    print(f"  FT_011 antecedent: {ft011.antecedents[0].feature}/{ft011.antecedents[0].attribute}={ft011.antecedents[0].value}")
    print(f"  FT_012 antecedent: {ft012.antecedents[0].feature}/{ft012.antecedents[0].attribute}={ft012.antecedents[0].value}")

    test_rules = [ft011, ft012]

    # --- A1: broken_overlapping -> FT_012 fires, FT_011 does not ---
    obs_a1 = {"Line of Fate": {"Continuity": "broken_overlapping"}}
    fired_a1 = match(obs_a1, {}, test_rules)
    fired_ids_a1 = {r.rule_id for r in fired_a1}
    a1_pass = fired_ids_a1 == {"FT_012"}
    _report(
        "A1_broken_overlapping_fires_FT012_only",
        a1_pass,
        f"observation={obs_a1} -> fired={sorted(fired_ids_a1)} (expected {{'FT_012'}})",
    )

    # --- A2: broken -> FT_011 fires, FT_012 does not ---
    obs_a2 = {"Line of Fate": {"Continuity": "broken"}}
    fired_a2 = match(obs_a2, {}, test_rules)
    fired_ids_a2 = {r.rule_id for r in fired_a2}
    a2_pass = fired_ids_a2 == {"FT_011"}
    _report(
        "A2_broken_fires_FT011_only",
        a2_pass,
        f"observation={obs_a2} -> fired={sorted(fired_ids_a2)} (expected {{'FT_011'}})",
    )

    # --- A3: mutual exclusion -- single-valued attribute, structurally ---
    # A plain dict key can hold exactly one value; demonstrate this directly
    # rather than merely asserting it, then confirm match() against the
    # resulting single-valued observation still fires exactly one rule.
    obs_a3: dict[str, dict[str, str]] = {}
    obs_a3.setdefault("Line of Fate", {})["Continuity"] = "broken"
    obs_a3["Line of Fate"]["Continuity"] = "broken_overlapping"  # overwrites -- cannot coexist
    single_value_ok = (
        obs_a3["Line of Fate"]["Continuity"] == "broken_overlapping"
        and len(obs_a3["Line of Fate"]) == 1
    )
    fired_a3 = match(obs_a3, {}, test_rules)
    fired_ids_a3 = {r.rule_id for r in fired_a3}
    a3_pass = single_value_ok and fired_ids_a3 == {"FT_012"}
    _report(
        "A3_mutual_exclusion_single_valued_attribute",
        a3_pass,
        f"dict overwrite left Continuity={obs_a3['Line of Fate']['Continuity']!r} "
        f"(only one value can ever occupy the key); match() on that single "
        f"observation fired={sorted(fired_ids_a3)} (expected {{'FT_012'}}, never both)",
    )


def level_b() -> None:
    print("\n=== LEVEL B: extractor routing + two-signal collision (REAL gpt-4o-mini call) ===")
    try:
        from agent.interpretive.observation_extractor import extract_observation
    except Exception as exc:
        raise RuntimeError(
            f"validate_broken_overlapping: failed to import observation_extractor: {exc}"
        ) from exc

    try:
        from openai import OpenAI
        client = OpenAI()
    except Exception as exc:
        raise RuntimeError(
            f"validate_broken_overlapping: failed to construct a live OpenAI client "
            f"(is OPENAI_API_KEY set?): {exc}"
        ) from exc

    # --- B1: clean signal, no conflicting free text ---
    b1_text = (
        "FATE LINE: present, moderately deep, no other breaks visible.\n"
        "  SLOPE: straight\n"
        "  ORIGIN: Wrist\n"
        "  TERMINATION: Mount of Saturn\n"
        "  PROXIMITY: n/a to none\n"
        "  BRANCHES_TO: none\n"
        "  BREAK TYPE: broken_overlapping"
    )
    try:
        record_b1 = extract_observation(
            {"fate line": [b1_text]}, client=client, model="gpt-4o-mini",
        )
    except Exception as exc:
        raise RuntimeError(
            f"validate_broken_overlapping: B1 extract_observation call failed: {exc}"
        ) from exc

    fobs_b1 = record_b1.features.get("Line of Fate")
    token_b1 = fobs_b1.tokens.get("Continuity") if fobs_b1 else None
    value_b1 = token_b1.get("value") if token_b1 else None
    b1_pass = value_b1 == "broken_overlapping"
    _report(
        "B1_clean_signal_emits_broken_overlapping",
        b1_pass,
        f"input text BREAK TYPE line = 'broken_overlapping', no conflicting free text -> "
        f"emitted Continuity token = {value_b1!r} "
        f"(unmapped for Line of Fate: {fobs_b1.unmapped if fobs_b1 else 'N/A (feature missing)'})",
    )

    # --- B2: HARDEST CASE -- structured signal vs. conflicting free text ---
    b2_text = (
        "FATE LINE: present, moderately deep, but the line breaks partway across "
        "the palm before continuing.\n"
        "  SLOPE: straight\n"
        "  ORIGIN: Wrist\n"
        "  TERMINATION: Mount of Saturn\n"
        "  PROXIMITY: n/a to none\n"
        "  BRANCHES_TO: none\n"
        "  BREAK TYPE: broken_overlapping"
    )
    try:
        record_b2 = extract_observation(
            {"fate line": [b2_text]}, client=client, model="gpt-4o-mini",
        )
    except Exception as exc:
        raise RuntimeError(
            f"validate_broken_overlapping: B2 extract_observation call failed: {exc}"
        ) from exc

    fobs_b2 = record_b2.features.get("Line of Fate")
    token_b2 = fobs_b2.tokens.get("Continuity") if fobs_b2 else None
    value_b2 = token_b2.get("value") if token_b2 else None
    unmapped_b2 = fobs_b2.unmapped if fobs_b2 else None
    _report(
        "B2_collision_measure_only_no_verdict",
        None,  # MEASURE step -- deliberately no pass/fail, per task instructions
        f"input has BOTH free text 'the line breaks partway ...' (implies plain "
        f"'broken') AND structured 'BREAK TYPE: broken_overlapping' -> emitted "
        f"Continuity token = {value_b2!r}; unmapped for Line of Fate = {unmapped_b2!r}; "
        f"raw_prose stored = {(fobs_b2.raw_prose if fobs_b2 else 'N/A')!r}",
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
        tag = "MEASURE" if r["passed"] is None else ("PASS" if r["passed"] else "FAIL")
        print(f"  [{tag}] {label}")

    if _failures:
        print(f"\n{len(_failures)} FAILED step(s): {_failures}")
        return 1

    print("\nAll asserted steps PASSED (B2 is a MEASURE step, not asserted, by design).")
    print("REMINDER: this proves WIRING only. FT_012 stays verified:false. Whether")
    print("real vision (GPT-4o on an actual photo) can distinguish an overlapping")
    print("break from a clean break remains UNPROVEN.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
