"""
scripts/direction_and_position_probe.py

MEASUREMENT HARNESS ONLY -- no production file is imported for mutation, no
source commit follows this run. Report goes to diagnostics/latest_run.md
(overwrite).

Single-call probe (no menu, no second call) testing exactly two additive
edits on top of agent.palm_processor._build_description_system_prompt:

  EDIT 1 -- explicit FATE LINE DIRECTION LAW / HEAD LINE DIRECTION LAW
            sentences, mirroring the existing HEART LINE DIRECTION LAW
            verbatim in style, to see whether they stabilize ORIGIN/
            TERMINATION reporting.
  EDIT 2 -- an along-the-line CONTACT POSITION field ("at start | mid-
            course | at end") added to the free-verb CONTACTS block on
            Head/Heart/Fate only, to see whether position lets a simple
            deterministic rule separate joins_at_origin from meets from
            stopped_by WITHOUT a closed type menu.

Measurement only -- no production wiring decision is made here.
"""

from __future__ import annotations

import base64
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

# ─────────────────────────── CONFIG BLOCK ────────────────────────────────
IMAGES: dict[str, str] = {
    "fate_line": "data/test_images/Fate line.jpeg",  # richest crossings + has Head-Life join
}
HAND = "right"  # verified via thumb-side geometry in the S100/S101 probes

N = 3  # existence + rough consistency only -- escalate ONLY with explicit approval

MODEL = "gpt-4o"
TEMPERATURE = 0.0
MAX_TOKENS = 900

REPORT_PATH = _REPO_ROOT / "diagnostics" / "latest_run.md"

_FAINT_RE = re.compile(r"not clearly visible|barely visible|\bfaint\b", re.I)
_VALID_POSITIONS = ("at start", "mid-course", "at end")

_POSITION_TOKEN_RULE = {
    "at start": "joins_at_origin",
    "mid-course": "meets",
    "at end": "stopped_by",
}


def _validate_paths() -> dict[str, Path]:
    resolved = {}
    missing = []
    for key, rel in IMAGES.items():
        p = _REPO_ROOT / rel
        if not p.is_file():
            missing.append(f"{key} -> {p}")
        else:
            resolved[key] = p
    if missing:
        raise FileNotFoundError(
            "direction_and_position_probe: missing configured image(s):\n  " + "\n  ".join(missing)
        )
    return resolved


# ───────────────────────── EDIT 1: direction laws ─────────────────────────
_HEART_LAW_NEEDLE = (
    "HEART LINE DIRECTION LAW: the finger/mount end is ORIGIN and "
    "the percussion is TERMINATION (even though common convention "
    "calls the percussion the start). "
)
_FATE_LAW = (
    "FATE LINE DIRECTION LAW: the wrist / lower-palm end is ORIGIN and "
    "the finger / mount end (toward Saturn) is TERMINATION, even if "
    "the line appears to start from the top. "
)
_HEAD_LAW = (
    "HEAD LINE DIRECTION LAW: the thumb-side edge (near the Life "
    "line's start) is ORIGIN and the percussion / Luna end is "
    "TERMINATION. "
)

# ───────────────────── EDIT 2: CONTACT POSITION field ─────────────────────
_CONTACT_POSITION_FEATURES = ["Line of Head", "Line of Heart", "Line of Fate"]


def _contacts_position_field(feature: str) -> str:
    return (
        "  CONTACTS: for each other line or mount this line clearly and "
        "visibly interacts with, write \"CONTACTS: <target> | <your own "
        "short word for how they interact> | <at start | mid-course | at "
        "end> | <faint|clear>\". <target> is exactly one of "
        f"{pp._relationship_target_menu(feature)}. Position = WHERE ALONG "
        "THIS LINE (per its DIRECTION LAW) the contact happens. If this "
        "line is faint or not clearly visible, write \"CONTACTS: none\". "
        "No fixed vocabulary for the interaction word.\n"
    )


def build_probe_prompt(hand: str) -> str:
    prompt = pp._build_description_system_prompt(hand)

    if _HEART_LAW_NEEDLE not in prompt:
        raise RuntimeError(
            "direction_and_position_probe: EDIT 1 build failed -- the HEART "
            "LINE DIRECTION LAW sentence was not found verbatim in the "
            "production prompt (byte-identity assumption broken)."
        )
    prompt = prompt.replace(_HEART_LAW_NEEDLE, _HEART_LAW_NEEDLE + _FATE_LAW + _HEAD_LAW, 1)

    for feature in _CONTACT_POSITION_FEATURES:
        old = pp._relationship_field(feature)
        new = _contacts_position_field(feature)
        if old not in prompt:
            raise RuntimeError(
                f"direction_and_position_probe: EDIT 2 build failed -- "
                f"RELATIONSHIP block for {feature!r} not found verbatim in "
                "the production prompt (byte-identity assumption broken)."
            )
        prompt = prompt.replace(old, new, 1)

    return prompt


# ───────────────────────────── parsing ────────────────────────────────────
_BLOCK_HEADER_RE = re.compile(
    r"^(HAND SHAPE|FINGERS|THUMB|LIFE LINE|HEAD LINE|HEART LINE|FATE LINE"
    r"|LINE OF HEALTH|LINE OF MARRIAGE|OTHER LINES|MOUNTS|MARKS):",
)
_FEATURE_BLOCK_LABEL = {
    "LIFE LINE": "Line of Life",
    "HEAD LINE": "Line of Head",
    "HEART LINE": "Line of Heart",
    "FATE LINE": "Line of Fate",
    "LINE OF HEALTH": "Line of Health",
    "LINE OF MARRIAGE": "Line of Marriage",
}
_ORIGIN_RE = re.compile(r"^ORIGIN:\s*(.*)$")
_TERMINATION_RE = re.compile(r"^TERMINATION:\s*(.*)$")
_CONTACTS_RE = re.compile(r"^CONTACTS:\s*(.*)$")

_ORIGIN_TERMINATION_FEATURES = ("Line of Head", "Line of Heart", "Line of Fate")


def _feature_faintness(raw_text: str) -> dict[str, bool]:
    blocks: dict[str, list[str]] = {}
    current_label = None
    for raw_line in raw_text.splitlines():
        stripped = raw_line.strip()
        header = _BLOCK_HEADER_RE.match(stripped)
        if header:
            label = header.group(1)
            current_label = _FEATURE_BLOCK_LABEL.get(label)
            if current_label:
                blocks.setdefault(current_label, []).append(stripped)
            else:
                current_label = None
            continue
        if current_label:
            blocks[current_label].append(stripped)
    return {feature: bool(_FAINT_RE.search("\n".join(body))) for feature, body in blocks.items()}


def parse_run(raw_text: str, *, run_idx: int) -> dict:
    origin: dict[str, str] = {}
    termination: dict[str, str] = {}
    contacts: list[dict] = []
    malformed: list[tuple[str, str]] = []
    current_feature: str | None = None

    for raw_line in raw_text.splitlines():
        stripped = raw_line.strip()
        header = _BLOCK_HEADER_RE.match(stripped)
        if header:
            label = header.group(1)
            current_feature = _FEATURE_BLOCK_LABEL.get(label)
            continue
        if current_feature is None:
            continue

        m = _ORIGIN_RE.match(stripped)
        if m and current_feature in _ORIGIN_TERMINATION_FEATURES:
            origin[current_feature] = m.group(1).strip()
            continue
        m = _TERMINATION_RE.match(stripped)
        if m and current_feature in _ORIGIN_TERMINATION_FEATURES:
            termination[current_feature] = m.group(1).strip()
            continue
        m = _CONTACTS_RE.match(stripped)
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
            position_norm = position_raw.strip().lower()
            valid_position = position_norm if position_norm in _VALID_POSITIONS else None
            if valid_position is None:
                print(f"  [run {run_idx}] garbled/off-vocab position (feature={current_feature!r}): {position_raw!r} in line {stripped!r}", file=sys.stderr)
            contacts.append({
                "feature": current_feature, "target": target, "verb": verb,
                "position_raw": position_raw, "position": valid_position, "clarity": clarity,
            })

    return {
        "origin": origin, "termination": termination,
        "contacts": contacts, "malformed": malformed,
        "faint": _feature_faintness(raw_text),
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


def _mime_for(image_bytes: bytes) -> str:
    return "image/png" if image_bytes[:8].startswith(b"\x89PNG") else "image/jpeg"


def main() -> None:
    t0 = time.time()
    resolved_paths = _validate_paths()
    image_key = "fate_line"
    path = resolved_paths[image_key]
    image_bytes = path.read_bytes()
    mime = _mime_for(image_bytes)

    prompt = build_probe_prompt(HAND)

    raws: list[str | None] = []
    parsed: list[dict | None] = []
    for run_idx in range(N):
        raw = _call_vision(prompt, image_bytes, mime, run_idx=run_idx)
        raws.append(raw)
        if raw is None:
            parsed.append(None)
        else:
            parsed.append(parse_run(raw, run_idx=run_idx))
        print(f"  run {run_idx + 1}/{N} -> {'OK' if raw else 'ERROR'}")

    n_errors = sum(1 for r in raws if r is None)

    # ── 1. ORIGIN/TERMINATION consistency ──────────────────────────────
    origin_table: dict[str, list[str]] = {ln: [] for ln in _ORIGIN_TERMINATION_FEATURES}
    termination_table: dict[str, list[str]] = {ln: [] for ln in _ORIGIN_TERMINATION_FEATURES}
    for p in parsed:
        for ln in _ORIGIN_TERMINATION_FEATURES:
            origin_table[ln].append(p["origin"].get(ln, "-") if p else "ERROR")
            termination_table[ln].append(p["termination"].get(ln, "-") if p else "ERROR")

    def _consistent(values: list[str]) -> bool:
        real = [v for v in values if v not in ("-", "ERROR")]
        return len(set(real)) <= 1

    # ── 2. contacts across runs, grouped by (feature, target) ──────────
    contact_groups: dict[tuple[str, str], list[dict]] = {}
    for p in parsed:
        if p is None:
            continue
        for c in p["contacts"]:
            contact_groups.setdefault((c["feature"], c["target"]), []).append(c)

    # ── 3. JOIN-vs-MEET check ──────────────────────────────────────────
    def _derive_tokens(group: list[dict]) -> list[str]:
        return [_POSITION_TOKEN_RULE.get(c["position"], "UNRESOLVED (bad position)") for c in group]

    # ── 4. cleanliness ──────────────────────────────────────────────────
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
                faint_leak.append(f"run {run_idx}: {c['feature']} (faint) still emitted {c['target']} ({c['verb']!r}, pos={c['position_raw']!r})")

    # ── report assembly ─────────────────────────────────────────────
    lines_out: list[str] = []
    lines_out.append("# Direction-Law + Contact-Position Probe (S100/S101 follow-up)\n")
    lines_out.append(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines_out.append(f"**Model:** {MODEL}, temperature={TEMPERATURE}  ")
    lines_out.append(f"**Image:** {image_key} ({IMAGES[image_key]}, hand={HAND})  ")
    lines_out.append(f"**N:** {N} (existence + rough consistency only; NOT escalated beyond approval)  ")
    lines_out.append(
        "**Scope:** measurement harness only. No production file modified. "
        "No commit follows this run. Single call per run -- no menu, no "
        "second call.\n"
    )
    if n_errors:
        lines_out.append(f"*Call errors:* {n_errors}/{N}\n")

    # 1. ORIGIN/TERMINATION
    lines_out.append("## 1. ORIGIN/TERMINATION consistency across the 3 runs\n")
    lines_out.append("| Line | Run 1 | Run 2 | Run 3 | ORIGIN consistent? | TERMINATION consistent? |")
    lines_out.append("|---|---|---|---|---|---|")
    for ln in _ORIGIN_TERMINATION_FEATURES:
        o = origin_table[ln]
        t = termination_table[ln]
        lines_out.append(
            f"| {ln} (ORIGIN) | {o[0]} | {o[1]} | {o[2]} | {_consistent(o)} | - |"
        )
        lines_out.append(
            f"| {ln} (TERMINATION) | {t[0]} | {t[1]} | {t[2]} | - | {_consistent(t)} |"
        )

    # 2. contacts
    lines_out.append("\n## 2. Every contact observed [line -> target | verb | position | seen in k/N]\n")
    lines_out.append("| Line -> Target | Verb(s) seen | Position(s) seen | k/N |")
    lines_out.append("|---|---|---|---|")
    for (feature, target), group in sorted(contact_groups.items()):
        verbs = Counter(c["verb"] for c in group)
        positions = Counter(c["position_raw"] for c in group)
        verb_str = ", ".join(f"{v!r}x{n}" for v, n in verbs.most_common())
        pos_str = ", ".join(f"{v!r}x{n}" for v, n in positions.most_common())
        lines_out.append(f"| {feature} -> {target} | {verb_str} | {pos_str} | {len(group)}/{N} |")
    if not contact_groups:
        lines_out.append("| (none observed) | - | - | - |")

    # 3. JOIN-vs-MEET check
    lines_out.append("\n## 3. JOIN-vs-MEET check (at start -> joins_at_origin; mid-course -> meets; at end -> stopped_by)\n")
    lines_out.append("| Line -> Target | Derived token(s) | Notes |")
    lines_out.append("|---|---|---|")
    head_life_tokens: list[str] = []
    other_crossing_tokens: dict[tuple[str, str], list[str]] = {}
    for (feature, target), group in sorted(contact_groups.items()):
        tokens = _derive_tokens(group)
        note = ""
        if (feature, target) == ("Line of Head", "Line of Life") or (feature, target) == ("Line of Life", "Line of Head"):
            head_life_tokens.extend(tokens)
            note = "Head-Life check"
        elif "Line of Fate" in (feature, target) or "Line of Heart" in (feature, target):
            other_crossing_tokens.setdefault((feature, target), []).extend(tokens)
            note = "Fate/Heart crossing"
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

    if other_crossing_tokens:
        lines_out.append("\n**Fate/Heart crossings resolved:**")
        for (feature, target), toks in other_crossing_tokens.items():
            lines_out.append(f"  - {feature} -> {target}: {Counter(toks)}")
    else:
        lines_out.append("\n**Fate/Heart crossings resolved:** none observed.")

    # 4. cleanliness
    lines_out.append("\n## 4. Cleanliness\n")
    lines_out.append(f"  - Total contacts parsed: {total_contacts}")
    lines_out.append(f"  - Valid position value: {valid_position_count}/{total_contacts}" if total_contacts else "  - Valid position value: N/A (no contacts)")
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

    # 5. VERDICT
    origin_stable = all(_consistent(origin_table[ln]) for ln in _ORIGIN_TERMINATION_FEATURES)
    termination_stable = all(_consistent(termination_table[ln]) for ln in _ORIGIN_TERMINATION_FEATURES)
    position_clean_rate = (valid_position_count / total_contacts) if total_contacts else 0.0
    head_life_clean = bool(head_life_tokens) and all(t == "joins_at_origin" for t in head_life_tokens)

    lines_out.append("\n## 5. VERDICT\n")
    lines_out.append(f"  - (i) Direction laws stabilized ORIGIN/TERMINATION? ORIGIN consistent for all 3 lines: {origin_stable}; TERMINATION consistent for all 3 lines: {termination_stable}.")
    lines_out.append(
        f"  - (ii) Does position cleanly separate join from meet? Head-Life resolves to "
        f"joins_at_origin every time: {head_life_clean}. Position field validity rate: "
        f"{valid_position_count}/{total_contacts} ({position_clean_rate:.0%})." if total_contacts else
        "  - (ii) Does position cleanly separate join from meet? N/A -- no contacts observed to test against."
    )

    issues = []
    if not origin_stable or not termination_stable:
        issues.append("ORIGIN/TERMINATION still flips across runs despite the added direction laws.")
    if garbled_positions:
        issues.append(f"{len(garbled_positions)} contact(s) returned a position value outside the 3-way vocabulary.")
    if total_malformed:
        issues.append(f"{total_malformed} CONTACTS line(s) omitted the position field entirely (fewer than 3 pipe-fields).")
    if faint_leak:
        issues.append("a faint-reported line still emitted a contact (control FAIL).")
    if not head_life_tokens:
        issues.append("Head-Life contact was not observed at all in this run set -- cannot validate the join case.")

    usable = not issues
    lines_out.append(f"\n  - (iii) Field usable as-is: {usable}.")
    if issues:
        biggest = max(issues, key=len)
        lines_out.append(f"    Single biggest issue: {biggest}")
        if len(issues) > 1:
            lines_out.append(f"    (other issues also present: {issues})")
    else:
        lines_out.append("    No issues found in this 3-run sample.")

    report_text = "\n".join(lines_out) + "\n"
    REPORT_PATH.write_text(report_text, encoding="utf-8")

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s. Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
