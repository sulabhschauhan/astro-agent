"""
scripts/recall_control_probe.py

MEASUREMENT HARNESS ONLY -- no production file is imported for mutation, no
source commit follows this run. Report goes to diagnostics/latest_run.md
(overwrite).

Cause-isolation control for the direction_and_position_probe.py result
(fate_line, N=3: Head-Life and Fate-Head contacts each appeared in only
1/3 runs). Question: was that thinness the HAND (fate_line's Fate line is
comparatively faint) or the PROMPT (the added CONTACT POSITION field
under-reports contacts in general)?

The prompt here is IDENTICAL to direction_and_position_probe.py -- same
two additive edits, same wording, byte-for-byte -- imported directly from
that script rather than re-typed, to guarantee it. ONLY the image changes,
to palm_left_test, the hand with the strongest prior recall (Head-Life
14-15/15, Heart<->Fate ~10/15 in the free_verb_capture_probe.py run).

This is NOT a re-test of correctness (position->token mapping and the
no-fabrication/faint-line control were already settled by the prior
probe) -- it isolates recall RATE only.
"""

from __future__ import annotations

import importlib.util
import sys
import time
from collections import Counter
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

# Prompt builder + parser reused VERBATIM from direction_and_position_probe.py
# (imported by file path, not re-typed) so the prompt is guaranteed
# byte-identical -- only the image/hand differ in this script.
_DP_PATH = Path(__file__).resolve().parent / "direction_and_position_probe.py"
_dp_spec = importlib.util.spec_from_file_location("direction_and_position_probe", _DP_PATH)
dp = importlib.util.module_from_spec(_dp_spec)
_dp_spec.loader.exec_module(dp)  # module-level code only builds constants/client, no calls

# ─────────────────────────── CONFIG BLOCK ────────────────────────────────
IMAGE_KEY = "palm_left_test"
IMAGE_PATH = "data/test_images/palm_left_test.jpg"
HAND = "left"  # per the S99/S100/S101 hand convention for this file

N = 3  # matches the prior probe's N -- do NOT escalate without approval

REPORT_PATH = _REPO_ROOT / "diagnostics" / "latest_run.md"


def main() -> None:
    t0 = time.time()
    path = _REPO_ROOT / IMAGE_PATH
    if not path.is_file():
        raise FileNotFoundError(f"recall_control_probe: missing image -> {path}")

    image_bytes = path.read_bytes()
    mime = dp._mime_for(image_bytes)
    prompt = dp.build_probe_prompt(HAND)

    raws: list[str | None] = []
    parsed: list[dict | None] = []
    for run_idx in range(N):
        raw = dp._call_vision(prompt, image_bytes, mime, run_idx=run_idx)
        raws.append(raw)
        parsed.append(dp.parse_run(raw, run_idx=run_idx) if raw is not None else None)
        print(f"  run {run_idx + 1}/{N} -> {'OK' if raw else 'ERROR'}")

    n_errors = sum(1 for r in raws if r is None)

    # ── ORIGIN/TERMINATION consistency ──────────────────────────────
    origin_table: dict[str, list[str]] = {ln: [] for ln in dp._ORIGIN_TERMINATION_FEATURES}
    termination_table: dict[str, list[str]] = {ln: [] for ln in dp._ORIGIN_TERMINATION_FEATURES}
    for p in parsed:
        for ln in dp._ORIGIN_TERMINATION_FEATURES:
            origin_table[ln].append(p["origin"].get(ln, "-") if p else "ERROR")
            termination_table[ln].append(p["termination"].get(ln, "-") if p else "ERROR")

    def _consistent(values: list[str]) -> bool:
        real = [v for v in values if v not in ("-", "ERROR")]
        return len(set(real)) <= 1

    # ── contacts, grouped by (feature, target) ──────────────────────
    contact_groups: dict[tuple[str, str], list[dict]] = {}
    for p in parsed:
        if p is None:
            continue
        for c in p["contacts"]:
            contact_groups.setdefault((c["feature"], c["target"]), []).append(c)

    def _derive_tokens(group: list[dict]) -> list[str]:
        return [dp._POSITION_TOKEN_RULE.get(c["position"], "UNRESOLVED (bad position)") for c in group]

    # ── cleanliness ──────────────────────────────────────────────────
    total_contacts = sum(len(v) for v in contact_groups.values())
    valid_position_count = sum(1 for group in contact_groups.values() for c in group if c["position"] is not None)
    garbled_positions = [
        (c["feature"], c["target"], c["position_raw"])
        for group in contact_groups.values() for c in group if c["position"] is None
    ]
    total_malformed = sum(len(p["malformed"]) for p in parsed if p is not None)

    faint_leak: list[str] = []
    for run_idx, p in enumerate(parsed):
        if p is None:
            continue
        for c in p["contacts"]:
            if p["faint"].get(c["feature"], False):
                faint_leak.append(
                    f"run {run_idx}: {c['feature']} (faint) still emitted "
                    f"{c['target']} ({c['verb']!r}, pos={c['position_raw']!r})"
                )

    # ── report assembly ─────────────────────────────────────────────
    lines_out: list[str] = []
    lines_out.append("# Recall Control Probe -- Strong-Recall Hand (S102 follow-up)\n")
    lines_out.append(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines_out.append(f"**Model:** {dp.MODEL}, temperature={dp.TEMPERATURE}  ")
    lines_out.append(f"**Image:** {IMAGE_KEY} ({IMAGE_PATH}, hand={HAND})  ")
    lines_out.append(f"**N:** {N} (matches the prior fate_line run; NOT escalated beyond approval)  ")
    lines_out.append(
        "**Scope:** measurement harness only. No production file modified. "
        "No commit follows this run. Prompt is byte-identical to "
        "direction_and_position_probe.py (imported directly, not re-typed) "
        "-- only the image/hand changed. This is a cause-isolation control "
        "on RECALL RATE only; position->token correctness and the "
        "no-fabrication/faint-line control were already settled by the "
        "prior (fate_line) run.\n"
    )
    if n_errors:
        lines_out.append(f"*Call errors:* {n_errors}/{N}\n")

    # 1. contacts + direct comparison to fate_line's 1/3
    lines_out.append("## 1. Every contact observed [line -> target | verb | position | seen in k/N]\n")
    lines_out.append("| Line -> Target | Verb(s) seen | Position(s) seen | k/N | fate_line run (S102) |")
    lines_out.append("|---|---|---|---|---|")
    _PRIOR_RATES = {
        ("Line of Head", "Line of Life"): "1/3",
        ("Line of Fate", "Line of Head"): "1/3",
    }
    for (feature, target), group in sorted(contact_groups.items()):
        verbs = Counter(c["verb"] for c in group)
        positions = Counter(c["position_raw"] for c in group)
        verb_str = ", ".join(f"{v!r}x{n}" for v, n in verbs.most_common())
        pos_str = ", ".join(f"{v!r}x{n}" for v, n in positions.most_common())
        prior = _PRIOR_RATES.get((feature, target), "n/a (not observed on fate_line)")
        lines_out.append(f"| {feature} -> {target} | {verb_str} | {pos_str} | {len(group)}/{N} | {prior} |")
    if not contact_groups:
        lines_out.append("| (none observed) | - | - | - | - |")

    # 2. ORIGIN/TERMINATION
    lines_out.append("\n## 2. ORIGIN/TERMINATION consistency across the 3 runs\n")
    lines_out.append("| Line | Run 1 | Run 2 | Run 3 | ORIGIN consistent? | TERMINATION consistent? |")
    lines_out.append("|---|---|---|---|---|---|")
    for ln in dp._ORIGIN_TERMINATION_FEATURES:
        o = origin_table[ln]
        t = termination_table[ln]
        lines_out.append(f"| {ln} (ORIGIN) | {o[0]} | {o[1]} | {o[2]} | {_consistent(o)} | - |")
        lines_out.append(f"| {ln} (TERMINATION) | {t[0]} | {t[1]} | {t[2]} | - | {_consistent(t)} |")

    # 3. JOIN-vs-MEET
    lines_out.append("\n## 3. JOIN-vs-MEET check (at start -> joins_at_origin; mid-course -> meets; at end -> stopped_by)\n")
    lines_out.append("| Line -> Target | Derived token(s) | Notes |")
    lines_out.append("|---|---|---|")
    head_life_tokens: list[str] = []
    heart_fate_tokens: dict[tuple[str, str], list[str]] = {}
    for (feature, target), group in sorted(contact_groups.items()):
        tokens = _derive_tokens(group)
        note = ""
        if {feature, target} == {"Line of Head", "Line of Life"}:
            head_life_tokens.extend(tokens)
            note = "Head-Life check"
        elif "Line of Fate" in (feature, target) and "Line of Heart" in (feature, target):
            heart_fate_tokens.setdefault((feature, target), []).extend(tokens)
            note = "Heart/Fate crossing check"
        elif "Line of Fate" in (feature, target) or "Line of Heart" in (feature, target):
            note = "other Fate/Heart-involving contact"
        lines_out.append(f"| {feature} -> {target} | {Counter(tokens)} | {note} |")

    lines_out.append("")
    if head_life_tokens:
        lines_out.append(
            f"**Head-Life resolves to joins_at_origin:** "
            f"{all(t == 'joins_at_origin' for t in head_life_tokens)} "
            f"(observed: {Counter(head_life_tokens)})"
        )
    else:
        lines_out.append("**Head-Life resolves to joins_at_origin:** N/A -- no Head-Life contact observed in this run set.")

    if heart_fate_tokens:
        lines_out.append("\n**Heart/Fate crossing resolved:**")
        for (feature, target), toks in heart_fate_tokens.items():
            lines_out.append(f"  - {feature} -> {target}: {Counter(toks)}")
    else:
        lines_out.append("\n**Heart/Fate crossing resolved:** none observed (Heart<->Fate directly) in this run set.")

    # 4. cleanliness
    lines_out.append("\n## 4. Cleanliness\n")
    lines_out.append(f"  - Total contacts parsed: {total_contacts}")
    lines_out.append(
        f"  - Valid position value: {valid_position_count}/{total_contacts}" if total_contacts
        else "  - Valid position value: N/A (no contacts)"
    )
    if garbled_positions:
        lines_out.append(f"  - Garbled/off-vocab position values ({len(garbled_positions)}):")
        for feature, target, raw_pos in garbled_positions:
            lines_out.append(f"      - {feature} -> {target}: {raw_pos!r}")
    else:
        lines_out.append("  - Garbled/off-vocab position values: none")
    lines_out.append(f"  - Malformed CONTACTS lines (fewer than 3 pipe-fields): {total_malformed}")
    lines_out.append(
        f"  - Faint-line-still-emitted control: {'FAIL' if faint_leak else 'PASS'}"
        + (f" -- {faint_leak}" if faint_leak else " -- clean")
    )

    # 5. VERDICT -- the one question
    def _rate(feature: str, target: str) -> int:
        return len(contact_groups.get((feature, target), []))

    head_life_hits = _rate("Line of Head", "Line of Life")
    fate_head_hits = _rate("Line of Fate", "Line of Head")
    heart_fate_hits = _rate("Line of Heart", "Line of Fate") + _rate("Line of Fate", "Line of Heart")

    recall_high = (head_life_hits >= 2) or (heart_fate_hits >= 2)

    lines_out.append("\n## 5. VERDICT -- is recall now HIGH (3/3 or 2/3) on this strong hand?\n")
    lines_out.append(f"  - Line of Head <-> Line of Life: {head_life_hits}/{N}")
    lines_out.append(f"  - Line of Heart <-> Line of Fate: {heart_fate_hits}/{N}")
    lines_out.append(f"  - Line of Fate <-> Line of Head: {fate_head_hits}/{N} (not expected on this hand per the prior probe)")

    if recall_high:
        lines_out.append(
            "\n  **HIGH.** The prior 1/3 on fate_line was the HAND (its Fate "
            "line reads comparatively faint), not the prompt -- recall "
            "recovers to >=2/3 on this stronger-recall hand. The direction-"
            "law + contact-position prompt is directionally production-"
            "ready on recall grounds."
        )
        biggest_risk = (
            "N=3 per hand is still a small sample -- a genuine per-hand "
            "recall floor (not just fate_line's known faintness) hasn't "
            "been ruled out without a larger N across more hands."
        )
    else:
        lines_out.append(
            "\n  **STILL LOW.** Recall did not recover on this stronger-"
            "recall hand either -- the PROMPT (most likely the added "
            "CONTACT POSITION clause) under-reports contacts in general. "
            "A wording fix is needed before this field is wired into "
            "production."
        )
        biggest_risk = (
            "the CONTACT POSITION field itself (EDIT 2) appears to "
            "suppress emission frequency versus the plain free-verb "
            "CONTACTS field (S101 saw 11-15/15 on the equivalent pairs); "
            "the position sub-field's wording needs revision before "
            "re-testing recall."
        )
    lines_out.append(f"\n  Single biggest remaining risk: {biggest_risk}")

    report_text = "\n".join(lines_out) + "\n"
    REPORT_PATH.write_text(report_text, encoding="utf-8")

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s. Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
