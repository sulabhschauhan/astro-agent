"""
scripts/position_optional_probe.py

MEASUREMENT HARNESS ONLY -- no production file is imported for mutation, no
source commit follows this run. Report goes to diagnostics/latest_run.md
(overwrite).

Follow-up to recall_control_probe.py, which isolated the cause of thin
contact recall (1/3 on palm_left_test, both Head-Life and Fate-Head) to
the PROMPT -- specifically, the mandatory CONTACT POSITION clause added in
direction_and_position_probe.py. This probe tests one fix: make position
OPTIONAL ("unknown" allowed) and contact-first in wording, decoupling
"did a contact happen" from "where along the line did it happen" so a
shaky position judgment never suppresses a solid contact report.

EDIT 1 (direction laws) is byte-identical to direction_and_position_probe.py
-- imported directly from that script's constants, not re-typed. Only
EDIT 2 (the CONTACTS field wording) changes here.

Correctness (position->token mapping) and no-fabrication (faint-line
control) were already settled by the prior two probes -- this tests
RECALL and position-quality-given-recall only.
"""

from __future__ import annotations

import base64
import importlib.util
import re
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

import agent.palm_processor as pp  # noqa: E402  (production module, read-only use)
from openai import OpenAI  # noqa: E402

# EDIT 1 (direction laws) reused VERBATIM from direction_and_position_probe.py
# -- imported by file path, not re-typed, to guarantee byte-identity.
_DP_PATH = Path(__file__).resolve().parent / "direction_and_position_probe.py"
_dp_spec = importlib.util.spec_from_file_location("direction_and_position_probe", _DP_PATH)
dp = importlib.util.module_from_spec(_dp_spec)
_dp_spec.loader.exec_module(dp)  # module-level code only builds constants/client, no calls

# ─────────────────────────── CONFIG BLOCK ────────────────────────────────
IMAGE_KEY = "palm_left_test"
IMAGE_PATH = "data/test_images/palm_left_test.jpg"
HAND = "left"

N = 3

MODEL = "gpt-4o"
TEMPERATURE = 0.0
MAX_TOKENS = 900

REPORT_PATH = _REPO_ROOT / "diagnostics" / "latest_run.md"

# Prior-run reference rates, for the direct comparison column.
_MANDATORY_POSITION_RATES = {
    ("Line of Head", "Line of Life"): "1/3",
    ("Line of Heart", "Line of Fate"): "0/3",
    ("Line of Fate", "Line of Heart"): "0/3",
    ("Line of Fate", "Line of Head"): "1/3",
}

_CONTACT_POSITION_FEATURES = ["Line of Head", "Line of Heart", "Line of Fate"]
_VALID_REAL_POSITIONS = ("at start", "mid-course", "at end")

_POSITION_TOKEN_RULE = {
    "at start": "joins_at_origin",
    "mid-course": "meets",
    "at end": "stopped_by",
}


# ───────────────────── EDIT 2 (revised): optional position ────────────────
def _contacts_position_optional_field(feature: str) -> str:
    return (
        "  CONTACTS: list EVERY other line or mount this line clearly and "
        "visibly interacts with -- report the contact FIRST, do not "
        "withhold a contact because you are unsure where it happens. For "
        "each, write:\n"
        "     \"CONTACTS: <target> | <your own short word for how they "
        "interact> | <position> | <faint|clear>\"\n"
        f"  where <target> is exactly one of {pp._relationship_target_menu(feature)}, "
        "and <position> is one of 'at start' / 'mid-course' / 'at end' per "
        "this line's DIRECTION LAW, OR 'unknown' if you cannot tell "
        "confidently. Never drop a contact just because position is "
        "unknown. If this line itself is faint or not clearly visible, "
        "write \"CONTACTS: none\". No fixed vocabulary for the interaction "
        "word.\n"
    )


def build_probe_prompt(hand: str) -> str:
    prompt = pp._build_description_system_prompt(hand)

    if dp._HEART_LAW_NEEDLE not in prompt:
        raise RuntimeError(
            "position_optional_probe: EDIT 1 build failed -- the HEART LINE "
            "DIRECTION LAW sentence was not found verbatim in the production "
            "prompt (byte-identity assumption broken)."
        )
    prompt = prompt.replace(dp._HEART_LAW_NEEDLE, dp._HEART_LAW_NEEDLE + dp._FATE_LAW + dp._HEAD_LAW, 1)

    for feature in _CONTACT_POSITION_FEATURES:
        old = pp._relationship_field(feature)
        new = _contacts_position_optional_field(feature)
        if old not in prompt:
            raise RuntimeError(
                f"position_optional_probe: EDIT 2 build failed -- "
                f"RELATIONSHIP block for {feature!r} not found verbatim in "
                "the production prompt (byte-identity assumption broken)."
            )
        prompt = prompt.replace(old, new, 1)

    return prompt


# ───────────────────────────── parsing ────────────────────────────────────
def _classify_position(raw: str) -> str:
    """Returns 'real', 'unknown', or 'garbled'."""
    norm = raw.strip().lower()
    if norm in _VALID_REAL_POSITIONS:
        return "real"
    if norm == "unknown":
        return "unknown"
    return "garbled"


def parse_run(raw_text: str, *, run_idx: int) -> dict:
    origin: dict[str, str] = {}
    termination: dict[str, str] = {}
    contacts: list[dict] = []
    malformed: list[tuple[str, str]] = []
    current_feature: str | None = None

    for raw_line in raw_text.splitlines():
        stripped = raw_line.strip()
        header = dp._BLOCK_HEADER_RE.match(stripped)
        if header:
            label = header.group(1)
            current_feature = dp._FEATURE_BLOCK_LABEL.get(label)
            continue
        if current_feature is None:
            continue

        m = dp._ORIGIN_RE.match(stripped)
        if m and current_feature in dp._ORIGIN_TERMINATION_FEATURES:
            origin[current_feature] = m.group(1).strip()
            continue
        m = dp._TERMINATION_RE.match(stripped)
        if m and current_feature in dp._ORIGIN_TERMINATION_FEATURES:
            termination[current_feature] = m.group(1).strip()
            continue
        m = dp._CONTACTS_RE.match(stripped)
        if m:
            raw_value = m.group(1).strip()
            if not raw_value or raw_value.lower() in ("none", "n/a"):
                continue
            parts = [p.strip() for p in raw_value.split("|")]
            if len(parts) < 3:
                malformed.append((current_feature, stripped))
                print(f"  [run {run_idx}] malformed CONTACTS line (feature={current_feature!r}): {stripped!r}", file=sys.stderr)
                continue
            target = parts[0]
            verb = parts[1]
            position_raw = parts[2]
            clarity = parts[3] if len(parts) >= 4 else "clear"
            position_class = _classify_position(position_raw)
            position_norm = position_raw.strip().lower() if position_class == "real" else None
            if position_class == "garbled":
                print(f"  [run {run_idx}] garbled/off-vocab position (feature={current_feature!r}): {position_raw!r} in line {stripped!r}", file=sys.stderr)
            contacts.append({
                "feature": current_feature, "target": target, "verb": verb,
                "position_raw": position_raw, "position": position_norm,
                "position_class": position_class, "clarity": clarity,
            })

    return {
        "origin": origin, "termination": termination,
        "contacts": contacts, "malformed": malformed,
        "faint": dp._feature_faintness(raw_text),
    }


# ───────────────────────────── API call wrapper ───────────────────────────
_client = OpenAI()


def _call_vision(system_prompt: str, image_bytes: bytes, mime: str, *, run_idx: int) -> str | None:
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    try:
        response = _client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                ]},
            ],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )
        return response.choices[0].message.content
    except Exception as exc:  # noqa: BLE001 -- one failed run must not abort the probe
        print(f"  [ERROR] run={run_idx}: {exc}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return None


def main() -> None:
    t0 = time.time()
    path = _REPO_ROOT / IMAGE_PATH
    if not path.is_file():
        raise FileNotFoundError(f"position_optional_probe: missing image -> {path}")

    image_bytes = path.read_bytes()
    mime = dp._mime_for(image_bytes)
    prompt = build_probe_prompt(HAND)

    raws: list[str | None] = []
    parsed: list[dict | None] = []
    for run_idx in range(N):
        raw = _call_vision(prompt, image_bytes, mime, run_idx=run_idx)
        raws.append(raw)
        parsed.append(parse_run(raw, run_idx=run_idx) if raw is not None else None)
        print(f"  run {run_idx + 1}/{N} -> {'OK' if raw else 'ERROR'}")

    n_errors = sum(1 for r in raws if r is None)

    # ── contacts grouped ─────────────────────────────────────────────
    contact_groups: dict[tuple[str, str], list[dict]] = {}
    for p in parsed:
        if p is None:
            continue
        for c in p["contacts"]:
            contact_groups.setdefault((c["feature"], c["target"]), []).append(c)

    # ── ORIGIN/TERMINATION consistency (sanity check, laws unchanged) ──
    origin_table: dict[str, list[str]] = {ln: [] for ln in dp._ORIGIN_TERMINATION_FEATURES}
    termination_table: dict[str, list[str]] = {ln: [] for ln in dp._ORIGIN_TERMINATION_FEATURES}
    for p in parsed:
        for ln in dp._ORIGIN_TERMINATION_FEATURES:
            origin_table[ln].append(p["origin"].get(ln, "-") if p else "ERROR")
            termination_table[ln].append(p["termination"].get(ln, "-") if p else "ERROR")

    def _consistent(values: list[str]) -> bool:
        real = [v for v in values if v not in ("-", "ERROR")]
        return len(set(real)) <= 1

    # ── cleanliness ──────────────────────────────────────────────────
    total_contacts = sum(len(v) for v in contact_groups.values())
    real_position_count = sum(1 for g in contact_groups.values() for c in g if c["position_class"] == "real")
    unknown_position_count = sum(1 for g in contact_groups.values() for c in g if c["position_class"] == "unknown")
    garbled_position_count = sum(1 for g in contact_groups.values() for c in g if c["position_class"] == "garbled")
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
    lines_out.append("# Position-Optional Recall-Recovery Probe (S103 follow-up)\n")
    lines_out.append(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines_out.append(f"**Model:** {MODEL}, temperature={TEMPERATURE}  ")
    lines_out.append(f"**Image:** {IMAGE_KEY} ({IMAGE_PATH}, hand={HAND})  ")
    lines_out.append(f"**N:** {N}  ")
    lines_out.append(
        "**Scope:** measurement harness only. No production file modified. "
        "No commit follows this run. EDIT 1 (direction laws) is byte-"
        "identical to direction_and_position_probe.py (imported directly). "
        "Only EDIT 2 (CONTACTS wording) changed: position is now optional "
        "('unknown' allowed) and the contact itself is asked for first. "
        "Correctness (position->token) and no-fabrication were already "
        "settled by the prior two probes -- this tests RECALL and "
        "position-quality-given-recall only.\n"
    )
    if n_errors:
        lines_out.append(f"*Call errors:* {n_errors}/{N}\n")

    # 1. contacts + comparison
    lines_out.append("## 1. Every contact observed [line -> target | verb | position | seen in k/N]\n")
    lines_out.append("| Line -> Target | Verb(s) seen | Position(s) seen | k/N | mandatory-position run (S102) |")
    lines_out.append("|---|---|---|---|---|")
    for (feature, target), group in sorted(contact_groups.items()):
        verbs = Counter(c["verb"] for c in group)
        positions = Counter(c["position_raw"] for c in group)
        verb_str = ", ".join(f"{v!r}x{n}" for v, n in verbs.most_common())
        pos_str = ", ".join(f"{v!r}x{n}" for v, n in positions.most_common())
        prior = _MANDATORY_POSITION_RATES.get((feature, target), "n/a (not observed prior)")
        lines_out.append(f"| {feature} -> {target} | {verb_str} | {pos_str} | {len(group)}/{N} | {prior} |")
    if not contact_groups:
        lines_out.append("| (none observed) | - | - | - | - |")

    # 2. RECALL VERDICT
    def _rate(feature: str, target: str) -> int:
        return len(contact_groups.get((feature, target), []))

    head_life_hits = _rate("Line of Head", "Line of Life")
    heart_fate_hits = _rate("Line of Heart", "Line of Fate") + _rate("Line of Fate", "Line of Heart")

    recall_recovered = (head_life_hits >= 2) and (heart_fate_hits >= 2)
    recall_partial = (head_life_hits >= 2) != (heart_fate_hits >= 2)  # exactly one recovered

    lines_out.append("\n## 2. RECALL VERDICT\n")
    lines_out.append(f"  - Line of Head <-> Line of Life: {head_life_hits}/{N} (mandatory-position run: 1/3)")
    lines_out.append(f"  - Line of Heart <-> Line of Fate: {heart_fate_hits}/{N} (mandatory-position run: 0/3)")
    if recall_recovered:
        lines_out.append("\n  **YES** -- both pairs recovered to >=2/3. The optional-position wording fixed the recall suppression.")
    elif recall_partial:
        lines_out.append("\n  **PARTIAL** -- one of the two pairs recovered to >=2/3, the other did not. Mixed result, not a clean YES.")
    else:
        lines_out.append("\n  **NO** -- neither pair recovered to >=2/3. Making position optional did not fix recall; a deeper issue with the CONTACTS field (or this specific wording) remains.")

    # 3. POSITION QUALITY
    lines_out.append("\n## 3. POSITION QUALITY (of contacts actually reported)\n")
    if total_contacts:
        lines_out.append(f"  - Real position (at start / mid-course / at end): {real_position_count}/{total_contacts} ({real_position_count/total_contacts:.0%})")
        lines_out.append(f"  - 'unknown': {unknown_position_count}/{total_contacts} ({unknown_position_count/total_contacts:.0%})")
        lines_out.append(f"  - Garbled/off-vocab: {garbled_position_count}/{total_contacts} ({garbled_position_count/total_contacts:.0%})")
    else:
        lines_out.append("  - N/A -- no contacts reported.")

    # 4. JOIN-vs-MEET on real-position contacts
    lines_out.append("\n## 4. JOIN-vs-MEET check (on contacts with a real position only)\n")
    lines_out.append("| Line -> Target | Derived token(s) | Real-position count |")
    lines_out.append("|---|---|---|")
    head_life_tokens: list[str] = []
    any_real = False
    for (feature, target), group in sorted(contact_groups.items()):
        real_group = [c for c in group if c["position_class"] == "real"]
        if not real_group:
            continue
        any_real = True
        tokens = [_POSITION_TOKEN_RULE[c["position"]] for c in real_group]
        if {feature, target} == {"Line of Head", "Line of Life"}:
            head_life_tokens.extend(tokens)
        lines_out.append(f"| {feature} -> {target} | {Counter(tokens)} | {len(real_group)} |")
    if not any_real:
        lines_out.append("| (no contact carried a real position value) | - | - |")
    lines_out.append("")
    if head_life_tokens:
        lines_out.append(
            f"**Head-Life resolves to joins_at_origin (on real-position instances):** "
            f"{all(t == 'joins_at_origin' for t in head_life_tokens)} (observed: {Counter(head_life_tokens)})"
        )
    else:
        lines_out.append("**Head-Life resolves to joins_at_origin:** N/A -- no real-position Head-Life contact observed.")

    # 5. Cleanliness
    lines_out.append("\n## 5. Cleanliness\n")
    lines_out.append(f"  - Total contacts parsed: {total_contacts}")
    lines_out.append(f"  - Malformed CONTACTS lines (fewer than 3 pipe-fields): {total_malformed}")
    lines_out.append(
        f"  - Faint-line-still-emitted control: {'FAIL' if faint_leak else 'PASS'}"
        + (f" -- {faint_leak}" if faint_leak else " -- clean")
    )
    origin_stable = all(_consistent(origin_table[ln]) for ln in dp._ORIGIN_TERMINATION_FEATURES)
    termination_stable = all(_consistent(termination_table[ln]) for ln in dp._ORIGIN_TERMINATION_FEATURES)
    lines_out.append(f"  - ORIGIN/TERMINATION still consistent across runs (direction laws unaffected by EDIT 2 change): ORIGIN={origin_stable}, TERMINATION={termination_stable}")

    # 6. single biggest remaining risk
    lines_out.append("\n## 6. Single biggest remaining risk\n")
    if recall_recovered:
        if unknown_position_count > real_position_count:
            risk = (
                "recall is fixed, but most recovered contacts carry "
                "'unknown' rather than a real position -- the model may be "
                "defaulting to 'unknown' rather than actually judging "
                "position, which would make the join/meets/stopped_by "
                "discrimination unusable in practice even though recall "
                "itself is healthy. Needs a larger-N check of real-vs-"
                "unknown ratio before wiring."
            )
        else:
            risk = (
                "N=3 is still a small sample for a production wiring "
                "decision -- recall recovery and position quality both look "
                "good here, but neither has been confirmed at scale or "
                "across multiple hands yet."
            )
    elif recall_partial:
        risk = (
            "the fix worked for one pair but not the other -- the "
            "remaining suppression may be pair-specific (e.g. weaker "
            "Heart<->Fate visibility on this hand) rather than a uniform "
            "prompt effect, which the N=3 sample can't distinguish from "
            "genuine wording insufficiency."
        )
    else:
        risk = (
            "making position optional did not restore recall -- the "
            "suppression may be coming from elsewhere in the CONTACTS "
            "block's wording (e.g. the multi-line/quoted format itself), "
            "not specifically the position sub-field; a more targeted "
            "diff against the S101 wording (which recalled well) is needed "
            "before another wording iteration."
        )
    lines_out.append(f"  {risk}")

    report_text = "\n".join(lines_out) + "\n"
    REPORT_PATH.write_text(report_text, encoding="utf-8")

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s. Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
