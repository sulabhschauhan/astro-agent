"""
scripts/free_verb_capture_probe.py

MEASUREMENT HARNESS ONLY -- no production file is imported for mutation, no
source commit follows this run. Report goes to diagnostics/latest_run.md
(overwrite).

Measures whether a SINGLE-CALL free-verb crossing capture (ARM G -- the
production describe_palm_image prompt with its RELATIONSHIP block swapped
for a free-verb CONTACTS block) matches the working second-call free-form
reference (ARM F, reused UNCHANGED from S100's
crossing_pass_second_call_probe.py), across every doctrinally-live line
pair -- with a deterministic, post-hoc, text-only mapping from free verbs
onto the closed 8-token vocabulary.

LOGICAL ELIMINATION (not re-tested here): menu-constrained emission is
already dead both single-call (S99/S100) and second-call (S100 ARM E,
0/750). This probe tests exactly two arms, neither of them menu-
constrained.

  ARM G (single-call, free-verb) -- agent.palm_processor.
         _build_description_system_prompt, UNMODIFIED, with ONLY the
         RELATIONSHIP field block (on each of the 5 lines that carry one:
         Head/Heart/Fate/Health/Marriage) replaced by a free-verb CONTACTS
         block. Everything else byte-identical to production.
  ARM F (second-call free-form reference) -- imported and called VERBATIM
         from scripts/crossing_pass_second_call_probe.py (S100). Not
         reimplemented here.

Every (emitting_line, target) pair enumerated for the full per-image
matrix comes from the registry via agent.palm_processor's own SSOT
helpers -- never hardcoded (GENERALIZATION GATE). The DOCTRINALLY-LIVE
evaluation subset (LIVE_LINE_PAIRS / LIVE_LINE_MOUNT_PAIRS) is supplied
verbatim by the instructing prompt (derived externally from
relation_census.md + authored rules) and is NOT derived here.
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

# ARM F is reused VERBATIM from the S100 probe -- imported by file path so
# this script has zero dependency on scripts/ being an importable package.
_S100_PATH = Path(__file__).resolve().parent / "crossing_pass_second_call_probe.py"
_s100_spec = importlib.util.spec_from_file_location("crossing_pass_second_call_probe", _S100_PATH)
s100 = importlib.util.module_from_spec(_s100_spec)
_s100_spec.loader.exec_module(s100)  # module-level code only defines constants/client, no calls

# ─────────────────────────── CONFIG BLOCK ────────────────────────────────
IMAGES: dict[str, str] = {
    "palm_left_test":  "data/test_images/palm_left_test.jpg",
    "athira":          "data/test_images/Athira Palm Right.jpeg",
    "fate_line":       "data/test_images/Fate line.jpeg",
    "palm_right_test": "data/test_images/palm_right_test.jpg",
    "back_hand_CTRL":  "data/test_images/Back Hand.jpeg",
}
HANDS: dict[str, str] = {
    "palm_left_test":  "left",
    "athira":          "right",
    "fate_line":       "right",
    "palm_right_test": "right",
    "back_hand_CTRL":  "right",  # dorsal shot, hand label has no semantic effect
}

N = 15

MODEL = "gpt-4o"
TEMPERATURE = 0.0
MAX_TOKENS = {"G": 900, "F": 800}

REPORT_PATH = _REPO_ROOT / "diagnostics" / "latest_run.md"

STABLE_THRESHOLD = 12 / 15  # 80%
UNSTABLE_LOW = 0.40

_FAINT_RE = re.compile(r"not clearly visible|barely visible|\bfaint\b", re.I)

# DOCTRINALLY-LIVE evaluation set -- supplied verbatim by the instructing
# prompt, NOT derived from the registry. Do not edit.
LIVE_LINE_PAIRS: list[tuple[str, str]] = [
    ("Line of Head", "Line of Life"), ("Line of Head", "Line of Heart"),
    ("Line of Heart", "Line of Fate"), ("Line of Head", "Line of Fate"),
    ("Line of Health", "Line of Life"), ("Line of Health", "Line of Heart"),
    ("Line of Health", "Line of Head"),
]  # 3-way Life+Head+Heart scored as its 3 constituent pairs co-firing
LIVE_LINE_MOUNT_PAIRS: list[tuple[str, str]] = [
    ("Line of Fate", "Mount of Jupiter"), ("Line of Heart", "Mount of Jupiter"),
    ("Line of Heart", "Mount of Saturn"), ("Line of Fate", "Mount of Luna"),
]

# ─────────────────────── path validation (fail fast) ─────────────────────
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
            "free_verb_capture_probe: missing configured image(s):\n  " + "\n  ".join(missing)
        )
    return resolved


# ───────────────────── registry-derived lines + target menus ─────────────
# Full matrix reporting spans every line that carries either a RELATIONSHIP/
# CONTACTS field (Head/Heart/Fate/Health/Marriage) or the legacy CONVERGENCE
# field (Life) -- the union of what either arm can possibly emit.
ALL_LINES: list[str] = list(pp._CONVERGENCE_LINES) + ["Line of Marriage"]


def _target_menu_list(feature: str) -> list[str]:
    raw = pp._relationship_target_menu(feature)
    return [t.strip() for t in raw.strip("{}").split("|")]


PAIRS: dict[str, list[str]] = {ln: _target_menu_list(ln) for ln in ALL_LINES}

# The 5 lines whose RELATIONSHIP field production actually builds -- verified
# directly against agent.palm_processor._build_description_system_prompt's
# source (same 5 S100's ARM C used for the identical byte-identical-swap
# technique).
_ARM_G_TARGET_FEATURES = [
    "Line of Head", "Line of Heart", "Line of Fate",
    "Line of Health", "Line of Marriage",
]


# ───────────────────────────── ARM G prompt ───────────────────────────────
def _contacts_field(feature: str) -> str:
    return (
        "  CONTACTS: for each other line or mount this line clearly and "
        "visibly interacts with, write \"CONTACTS: <target> | <your own "
        "short word for how they interact> | <faint|clear>\". <target> is "
        f"exactly one of {pp._relationship_target_menu(feature)}. If this "
        "line is faint or not clearly visible, write \"CONTACTS: none\". "
        "Describe the interaction in your own words -- no fixed list.\n"
    )


def arm_g_prompt(hand: str) -> str:
    prompt = pp._build_description_system_prompt(hand)
    for feature in _ARM_G_TARGET_FEATURES:
        old = pp._relationship_field(feature)
        new = _contacts_field(feature)
        if old not in prompt:
            raise RuntimeError(
                f"free_verb_capture_probe: ARM G build failed -- RELATIONSHIP "
                f"block for {feature!r} not found verbatim in the production "
                "prompt (byte-identity assumption broken)."
            )
        prompt = prompt.replace(old, new)
    return prompt


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
_CONTACTS_RE = re.compile(r"^CONTACTS:\s*(.*)$")


def _feature_faintness(raw_text: str) -> dict[str, bool]:
    """Per top-level relational feature block, True if the block's own text
    contains a not-clearly-visible/barely-visible/faint phrase. Same
    methodology as the S99/S100 probes: the model's own self-report is the
    ground-truth proxy, no independent human read exists per-run."""
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


def parse_arm_g(raw_text: str, *, image_key: str, run_idx: int) -> dict:
    cells: dict[tuple[str, str], str] = {}
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
        m = _CONTACTS_RE.match(stripped)
        if not m:
            continue
        raw_value = m.group(1).strip()
        if not raw_value or raw_value.lower() in ("none", "n/a"):
            continue
        parts = [p.strip() for p in raw_value.split("|")]
        if len(parts) < 2:
            print(
                f"  [ARM G off-format] image={image_key!r} run={run_idx} "
                f"line={current_feature!r} raw={stripped!r}",
                file=sys.stderr,
            )
            continue
        target, verb = parts[0], parts[1]
        if target not in PAIRS.get(current_feature, []):
            print(
                f"  [ARM G off-menu TARGET] image={image_key!r} run={run_idx} "
                f"line={current_feature!r} target={target!r} raw={stripped!r}",
                file=sys.stderr,
            )
            continue
        if (current_feature, target) not in cells:
            cells[(current_feature, target)] = verb
    return {"cells": cells, "faint": _feature_faintness(raw_text)}


# ───────────────────────── post-hoc verb -> token mapping ─────────────────
# Deterministic, text-only, NO vision call. Ordered most-specific-first so a
# multi-word phrase (e.g. "crossed by") is not pre-empted by a shorter
# generic substring (e.g. "cross") checked later.
_VERB_MAP_RULES: list[tuple[str, str]] = [
    ("crossed by", "cut_by"),
    ("branch", "branch_in"),
    ("joins from", "branch_in"),
    ("stopped by", "stopped_by"),
    ("barred by", "stopped_by"),
    ("ends at", "stopped_by"),
    ("takes possession", "takes_possession_of"),
    ("merges", "joins_at_origin"),
    ("starts from", "joins_at_origin"),
    ("joins", "joins_at_origin"),
    ("touches", "touches"),
    ("meets", "meets"),
    ("cross", "cuts"),
]


def map_verb(verb: str) -> str | None:
    low = verb.lower()
    for pattern, token in _VERB_MAP_RULES:
        if pattern in low:
            return token
    return None  # UNMAPPED (e.g. "runs alongside") -- never guessed


# ───────────────────────────── API call wrapper ───────────────────────────
_client = OpenAI()


def _call_vision(system_prompt: str, image_bytes: bytes, mime: str, *,
                  arm: str, image_key: str, run_idx: int) -> str | None:
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
            max_tokens=MAX_TOKENS[arm],
            temperature=TEMPERATURE,
        )
        return response.choices[0].message.content
    except Exception as exc:  # noqa: BLE001 -- one failed run must not abort the matrix
        print(f"  [ERROR] image={image_key!r} arm={arm} run={run_idx}: {exc}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return None


def _mime_for(image_bytes: bytes) -> str:
    return "image/png" if image_bytes[:8].startswith(b"\x89PNG") else "image/jpeg"


def _run_batch(system_prompt: str, image_bytes: bytes, mime: str, *,
               arm: str, image_key: str, count: int) -> list[str | None]:
    raws = []
    for run_idx in range(count):
        raw = _call_vision(system_prompt, image_bytes, mime, arm=arm, image_key=image_key, run_idx=run_idx)
        raws.append(raw)
        print(f"  {image_key} / arm {arm} / run {run_idx + 1}/{count} -> {'OK' if raw else 'ERROR'}")
    return raws


def _majority(values: list[str | None]) -> tuple[int, int, str]:
    hit_vals = [v for v in values if v is not None]
    n = len(values)
    if not hit_vals:
        return 0, n, "-"
    return len(hit_vals), n, Counter(hit_vals).most_common(1)[0][0]


def main() -> None:
    t0 = time.time()
    resolved_paths = _validate_paths()
    print(f"Resolved {len(resolved_paths)} image path(s), config valid.")

    prompt_f = s100.arm_f_prompt()

    # results[image_key][arm] = {"raws": [...], "parsed": [...]}
    results: dict[str, dict[str, dict]] = {}

    for image_key, path in resolved_paths.items():
        image_bytes = path.read_bytes()
        mime = _mime_for(image_bytes)
        hand = HANDS[image_key]
        results[image_key] = {}

        prompt_g = arm_g_prompt(hand)

        for arm, sys_prompt in (("G", prompt_g), ("F", prompt_f)):
            print(f"\n=== {image_key} / ARM {arm} : {N} runs ===")
            raws = _run_batch(sys_prompt, image_bytes, mime, arm=arm, image_key=image_key, count=N)
            parsed = []
            for run_idx, raw in enumerate(raws):
                if raw is None:
                    parsed.append(None)
                elif arm == "G":
                    parsed.append(parse_arm_g(raw, image_key=image_key, run_idx=run_idx))
                else:
                    parsed.append(s100.parse_arm_f(raw, image_key=image_key, run_idx=run_idx))
            results[image_key][arm] = {"raws": raws, "parsed": parsed}

    # ── raw (ungated) per-cell series ───────────────────────────────────
    def _raw_cell_series(image_key: str, arm: str, line: str, target: str) -> list[str | None]:
        parsed_list = results[image_key][arm]["parsed"]
        out = []
        for p in parsed_list:
            out.append(None if p is None else p["cells"].get((line, target)))
        return out

    # ── faintness-gated per-cell series (drops a cell if its EMITTING line
    # self-reported faint in that same run) ─────────────────────────────
    def _gated_cell_series(image_key: str, arm: str, line: str, target: str) -> tuple[list[str | None], int]:
        parsed_list = results[image_key][arm]["parsed"]
        out = []
        dropped = 0
        for p in parsed_list:
            if p is None:
                out.append(None)
                continue
            val = p["cells"].get((line, target))
            if val is not None and p["faint"].get(line, False):
                dropped += 1
                out.append(None)
            else:
                out.append(val)
        return out, dropped

    def _gated_undirected_series(image_key: str, arm: str, a: str, b: str, *, is_mount: bool) -> tuple[list[str | None], int]:
        series_ab, drop_ab = _gated_cell_series(image_key, arm, a, b)
        if is_mount:
            return series_ab, drop_ab
        series_ba, drop_ba = _gated_cell_series(image_key, arm, b, a)
        out = []
        for i in range(len(series_ab)):
            va = series_ab[i] if i < len(series_ab) else None
            vb = series_ba[i] if i < len(series_ba) else None
            out.append(va if va is not None else vb)
        return out, drop_ab + drop_ba

    def _image_line_faint(image_key: str, arm: str, line: str) -> bool:
        parsed_list = results[image_key][arm]["parsed"]
        votes = sum(1 for p in parsed_list if p is not None and p["faint"].get(line, False))
        seen = sum(1 for p in parsed_list if p is not None)
        return seen > 0 and votes > seen / 2

    # ── controls ─────────────────────────────────────────────────────
    control_rows: list[dict] = []

    for arm in ("G", "F"):
        parsed_list = results["back_hand_CTRL"][arm]["parsed"]
        failures = []
        for run_idx, p in enumerate(parsed_list):
            if p is None:
                continue
            for (line, target), verb in p["cells"].items():
                failures.append(f"run {run_idx}: {line} {verb!r} {target}")
        control_rows.append({
            "control": "back_hand_CTRL: 0 crossings", "image": "back_hand_CTRL", "arm": arm,
            "status": "FAIL" if failures else "PASS",
            "detail": "; ".join(failures) if failures else "0 crossings in all runs",
        })

    live_line_set = sorted({x for pair in LIVE_LINE_PAIRS for x in pair} | {p[0] for p in LIVE_LINE_MOUNT_PAIRS})
    for image_key in IMAGES:
        for arm in ("G", "F"):
            total_dropped = 0
            for line in ALL_LINES:
                for target in PAIRS[line]:
                    _, dropped = _gated_cell_series(image_key, arm, line, target)
                    total_dropped += dropped
            control_rows.append({
                "control": "faintness removals", "image": image_key, "arm": arm,
                "status": "PASS",
                "detail": f"{total_dropped} cell-run(s) removed (faint emitting line still reported a contact pre-gate)"
                          if total_dropped else "0 removed (clean)",
            })

        health_absent = _image_line_faint(image_key, "F", "Line of Health")
        for arm in ("G", "F"):
            parsed_list = results[image_key][arm]["parsed"]
            health_fail = []
            for run_idx, p in enumerate(parsed_list):
                if p is None:
                    continue
                for (line, target), verb in p["cells"].items():
                    if target == "Line of Health" and health_absent:
                        health_fail.append(f"run {run_idx}: {line} {verb!r} Line of Health")
            control_rows.append({
                "control": "absent Health -> silent", "image": image_key, "arm": arm,
                "status": "FAIL" if health_fail else "PASS",
                "detail": "; ".join(health_fail) if health_fail else (
                    "clean (Health judged absent)" if health_absent else "n/a (Health judged present)"
                ),
            })

    # ── report assembly: header + matrices ──────────────────────────
    lines_out: list[str] = []
    lines_out.append("# Free-Verb Capture Probe, All-Line Evaluation (S100 follow-up)\n")
    lines_out.append(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines_out.append(f"**Model:** {MODEL}, temperature={TEMPERATURE}  ")
    lines_out.append(f"**N:** {N}  ")
    lines_out.append(
        "**Scope:** measurement harness only. No production file modified. "
        "No commit follows this run.\n"
    )
    lines_out.append(
        "**Methodology note:** ARM G is the production single-call "
        "describe_palm_image prompt with ONLY its RELATIONSHIP field "
        "blocks (Head/Heart/Fate/Health/Marriage) swapped for a free-verb "
        "CONTACTS block; Line of Life keeps its legacy CONVERGENCE field "
        "unchanged (Life never emits a CONTACTS line in ARM G by "
        "construction -- a Life-involving pair can still register via the "
        "OTHER line's CONTACTS output, since scoring is undirected). ARM F "
        "is reused UNCHANGED from crossing_pass_second_call_probe.py "
        "(S100) -- not reimplemented here. Verb->token mapping is "
        "deterministic substring matching, most-specific pattern first, "
        "never a vision call. The raw per-image matrix below is UNGATED "
        "(shows everything either model actually said); the faintness gate "
        "(drop a cell whose emitting line self-reported faint in that same "
        "run) is applied only in the Controls 'faintness removals' count "
        "and in the EVALUATION section's LIVE-set scoring.\n"
    )

    for image_key in IMAGES:
        lines_out.append(f"\n## Image: `{image_key}` ({IMAGES[image_key]}, hand={HANDS[image_key]})\n")
        err_g = sum(1 for r in results[image_key]["G"]["raws"] if r is None)
        err_f = sum(1 for r in results[image_key]["F"]["raws"] if r is None)
        if err_g or err_f:
            lines_out.append(f"*Call errors this image:* arm G: {err_g}, arm F: {err_f}\n")

        live_undirected_marks: set[tuple[str, str]] = set()
        for a, b in LIVE_LINE_PAIRS:
            live_undirected_marks.add((a, b))
            live_undirected_marks.add((b, a))
        for a, b in LIVE_LINE_MOUNT_PAIRS:
            live_undirected_marks.add((a, b))

        lines_out.append("| Line -> Target | LIVE? | G: k/N (verb -> token) | F: k/N (verb) |")
        lines_out.append("|---|---|---|---|")
        for line in ALL_LINES:
            for target in PAIRS[line]:
                raw_g = _raw_cell_series(image_key, "G", line, target)
                raw_f = _raw_cell_series(image_key, "F", line, target)
                hg, ng, tg = _majority(raw_g)
                hf, nf, tf = _majority(raw_f)
                mapped_g = map_verb(tg) if tg != "-" else "-"
                is_live = "LIVE" if (line, target) in live_undirected_marks else ""
                lines_out.append(
                    f"| {line} -> {target} | {is_live} | {hg}/{ng} ({tg} -> {mapped_g}) | {hf}/{nf} ({tf}) |"
                )

    # ── controls table ───────────────────────────────────────────────
    lines_out.append("\n## Controls\n")
    lines_out.append("| Control | Image | Arm | Status | Detail |")
    lines_out.append("|---|---|---|---|---|")
    for row in control_rows:
        lines_out.append(f"| {row['control']} | {row['image']} | {row['arm']} | {row['status']} | {row['detail']} |")

    # ── BLIND-SPOT REPORT ────────────────────────────────────────────
    lines_out.append("\n## BLIND-SPOT REPORT\n")
    lines_out.append("**ARCHITECTURALLY UNMEASURABLE (prompt-independent):**\n")
    lines_out.append(
        "  - Line of Marriage as an emitter -- ARM F's traced-line set "
        "(reused unchanged from S100) is Life/Head/Heart/Fate/Health only; "
        "it never traces Marriage, so no Marriage-emitted crossing can "
        "ever be cross-arm-compared regardless of what ARM G reports. Not "
        "in LIVE_LINE_PAIRS/LIVE_LINE_MOUNT_PAIRS, so excluded from "
        "EVALUATION below by construction, not by a special-case filter."
    )
    lines_out.append(
        "  - No other non-emittable target identified -- every target in "
        "PAIRS is registry-legal and reachable by at least one emitting "
        "line's own field in both arms' traced-line sets (outside "
        "Marriage)."
    )

    non_ctrl_images = [k for k in IMAGES if k != "back_hand_CTRL"]
    image_limited: list[tuple[str, str, bool]] = []  # (a, b, is_mount)
    for a, b in LIVE_LINE_PAIRS:
        all_zero = True
        for image_key in non_ctrl_images:
            sg, _ = _gated_undirected_series(image_key, "G", a, b, is_mount=False)
            sf, _ = _gated_undirected_series(image_key, "F", a, b, is_mount=False)
            hg, ng, _ = _majority(sg)
            hf, nf, _ = _majority(sf)
            if hg > 0 or hf > 0:
                all_zero = False
                break
        if all_zero:
            image_limited.append((a, b, False))
    for a, b in LIVE_LINE_MOUNT_PAIRS:
        all_zero = True
        for image_key in non_ctrl_images:
            sg, _ = _gated_undirected_series(image_key, "G", a, b, is_mount=True)
            sf, _ = _gated_undirected_series(image_key, "F", a, b, is_mount=True)
            hg, ng, _ = _majority(sg)
            hf, nf, _ = _majority(sf)
            if hg > 0 or hf > 0:
                all_zero = False
                break
        if all_zero:
            image_limited.append((a, b, True))

    lines_out.append("\n**IMAGE-LIMITED (both G and F are 0/15 on every hand -- inconclusive, needs a hand exhibiting it, NOT a failure):**\n")
    if image_limited:
        for a, b, is_mount in image_limited:
            lines_out.append(f"  - {a} <-> {b}")
    else:
        lines_out.append("  - None -- every LIVE pair fired at least once (in G or F) on at least one hand.")

    # ── EVALUATION ───────────────────────────────────────────────────
    lines_out.append("\n## EVALUATION (LIVE set only, excluding architecturally-unmeasurable)\n")

    image_limited_set = {(a, b) for a, b, _m in image_limited}

    # (i) MATCH
    matches, misses = [], []
    for a, b in LIVE_LINE_PAIRS:
        if (a, b) in image_limited_set:
            continue
        for image_key in non_ctrl_images:
            sf, _ = _gated_undirected_series(image_key, "F", a, b, is_mount=False)
            hf, nf, tf = _majority(sf)
            if hf / nf >= STABLE_THRESHOLD if nf else False:
                sg, _ = _gated_undirected_series(image_key, "G", a, b, is_mount=False)
                hg, ng, tg = _majority(sg)
                rate_g = hg / ng if ng else 0.0
                entry = f"{image_key}: {a} <-> {b} | F={hf}/{nf} ({tf}) | G={hg}/{ng} ({tg})"
                (matches if rate_g >= STABLE_THRESHOLD else misses).append(entry)
    for a, b in LIVE_LINE_MOUNT_PAIRS:
        if (a, b) in image_limited_set:
            continue
        for image_key in non_ctrl_images:
            sf, _ = _gated_undirected_series(image_key, "F", a, b, is_mount=True)
            hf, nf, tf = _majority(sf)
            if hf / nf >= STABLE_THRESHOLD if nf else False:
                sg, _ = _gated_undirected_series(image_key, "G", a, b, is_mount=True)
                hg, ng, tg = _majority(sg)
                rate_g = hg / ng if ng else 0.0
                entry = f"{image_key}: {a} -> {b} | F={hf}/{nf} ({tf}) | G={hg}/{ng} ({tg})"
                (matches if rate_g >= STABLE_THRESHOLD else misses).append(entry)

    lines_out.append("**(i) MATCH** -- per LIVE cell where F >= 12/15, does G also fire >= 12/15?\n")
    lines_out.append(f"MATCHES ({len(matches)}):")
    for m in matches:
        lines_out.append(f"  - {m}")
    lines_out.append(f"\nMISSES ({len(misses)}):")
    for m in misses:
        lines_out.append(f"  - {m}")
    lines_out.append("")

    # (ii) COVERAGE
    covered_lines: set[str] = set()
    for a, b in LIVE_LINE_PAIRS:
        for image_key in non_ctrl_images:
            sg, _ = _gated_undirected_series(image_key, "G", a, b, is_mount=False)
            hg, ng, _ = _majority(sg)
            if hg > 0:
                covered_lines.add(a)
                covered_lines.add(b)
    for a, b in LIVE_LINE_MOUNT_PAIRS:
        for image_key in non_ctrl_images:
            sg, _ = _gated_undirected_series(image_key, "G", a, b, is_mount=True)
            hg, ng, _ = _majority(sg)
            if hg > 0:
                covered_lines.add(a)
    target_lines = {"Line of Head", "Line of Heart", "Line of Fate", "Line of Life", "Line of Health"}
    zero_lines = sorted(target_lines - covered_lines)
    lines_out.append("**(ii) COVERAGE** -- distinct emitting/participating lines G fired on within the LIVE set:\n")
    lines_out.append(f"  - Covered: {sorted(covered_lines)}")
    lines_out.append(f"  - Zero G emission: {zero_lines if zero_lines else 'none -- all 5 lines covered'}")
    lines_out.append("")

    # (iii) MAPPING FIDELITY -- over ALL of G's parsed verbs (full matrix, not just LIVE set)
    all_verbs: list[str] = []
    for image_key in IMAGES:
        for p in results[image_key]["G"]["parsed"]:
            if p is None:
                continue
            all_verbs.extend(p["cells"].values())
    mapped = [v for v in all_verbs if map_verb(v) is not None]
    unmapped = [v for v in all_verbs if map_verb(v) is None]
    pct = (len(mapped) / len(all_verbs) * 100) if all_verbs else 0.0
    lines_out.append(f"**(iii) MAPPING FIDELITY** -- over all {len(all_verbs)} G verb occurrence(s) (full matrix, not just LIVE set):\n")
    lines_out.append(f"  - Mapped: {len(mapped)}/{len(all_verbs)} ({pct:.0f}%)")
    if unmapped:
        lines_out.append(f"  - UNMAPPED occurrences ({len(unmapped)}): {sorted(set(unmapped))}")
    else:
        lines_out.append("  - UNMAPPED occurrences: none")
    lines_out.append("")

    # (iv) STABILITY
    unstable_cells, stable_cells, dead_cells = [], [], []
    for a, b in LIVE_LINE_PAIRS:
        for image_key in non_ctrl_images:
            sg, _ = _gated_undirected_series(image_key, "G", a, b, is_mount=False)
            hg, ng, tg = _majority(sg)
            rate = hg / ng if ng else 0.0
            label = f"{image_key}: {a} <-> {b} ({hg}/{ng}, {tg})"
            if rate >= STABLE_THRESHOLD:
                stable_cells.append(label)
            elif rate >= UNSTABLE_LOW:
                unstable_cells.append(label)
            else:
                dead_cells.append(label)
    for a, b in LIVE_LINE_MOUNT_PAIRS:
        for image_key in non_ctrl_images:
            sg, _ = _gated_undirected_series(image_key, "G", a, b, is_mount=True)
            hg, ng, tg = _majority(sg)
            rate = hg / ng if ng else 0.0
            label = f"{image_key}: {a} -> {b} ({hg}/{ng}, {tg})"
            if rate >= STABLE_THRESHOLD:
                stable_cells.append(label)
            elif rate >= UNSTABLE_LOW:
                unstable_cells.append(label)
            else:
                dead_cells.append(label)
    lines_out.append("**(iv) STABILITY** -- G LIVE cells binned <40% / 40-79% / >=80%:\n")
    lines_out.append(f"  - <40%: {len(dead_cells)}")
    lines_out.append(f"  - 40-79% (unstable): {len(unstable_cells)}")
    for c in unstable_cells:
        lines_out.append(f"      - {c}")
    lines_out.append(f"  - >=80% (stable): {len(stable_cells)}")
    for c in stable_cells:
        lines_out.append(f"      - {c}")
    lines_out.append("")

    # (v) FAINTNESS GATE
    lines_out.append("**(v) FAINTNESS GATE** -- did it stop the athira leak (S100: Line of Fate self-reported faint yet still emitted a Heart crossing)?\n")
    for arm in ("G", "F"):
        raw_leak = []
        for run_idx, p in enumerate(results["athira"][arm]["parsed"]):
            if p is None:
                continue
            if p["faint"].get("Line of Fate", False):
                for (line, target), verb in p["cells"].items():
                    if line == "Line of Fate":
                        raw_leak.append(f"run {run_idx}: Fate(faint) -> {target} ({verb!r})")
        gated_g, _ = _gated_undirected_series("athira", arm, "Line of Heart", "Line of Fate", is_mount=False)
        post_gate_leak = any(
            v is not None and results["athira"][arm]["parsed"][i] is not None
            and results["athira"][arm]["parsed"][i]["faint"].get("Line of Fate", False)
            for i, v in enumerate(gated_g)
        )
        lines_out.append(
            f"  - ARM {arm}: pre-gate leak instances = {len(raw_leak)}"
            + (f" ({raw_leak})" if raw_leak else "")
            + f"; post-gate leak present = {post_gate_leak}"
        )
    lines_out.append("")

    # (vi) VERDICT
    controls_clean = all(r["status"] == "PASS" for r in control_rows)
    match_clean = not misses
    coverage_clean = not zero_lines
    bar_clear = match_clean and coverage_clean and controls_clean

    failure_modes = []
    if not match_clean:
        failure_modes.append(f"MATCH: {len(misses)} live cell(s) where F is reliable (>=80%) but G misses.")
    if not coverage_clean:
        failure_modes.append(f"COVERAGE: G never fired for {zero_lines} within the LIVE set.")
    if not controls_clean:
        failed = [f"{r['control']} ({r['image']}/{r['arm']})" for r in control_rows if r["status"] == "FAIL"]
        failure_modes.append(f"CONTROLS: {failed}")

    lines_out.append("**(vi) VERDICT** -- can single-call free-verb (G) replace second-call F across the MEASURABLE live set?\n")
    lines_out.append(f"  - Controls clean: {controls_clean}")
    lines_out.append(f"  - Match clean (every F>=80% live cell matched by G>=80%): {match_clean}")
    lines_out.append(f"  - Coverage clean (G fires on all 5 lines within the LIVE set): {coverage_clean}")
    lines_out.append(f"\n  **{'YES' if bar_clear else 'NO'}**\n")
    if not bar_clear:
        biggest = max(failure_modes, key=len) if failure_modes else "unknown"
        lines_out.append(f"  Single biggest gap: {biggest}")
        if len(failure_modes) > 1:
            lines_out.append("  (other failure modes also present, listed above)")
    lines_out.append(
        f"\n  Live pairs untestable for lack of a suitable hand ({len(image_limited)}):"
    )
    if image_limited:
        for a, b, _m in image_limited:
            lines_out.append(f"    - {a} <-> {b}")
    else:
        lines_out.append("    - none")

    report_text = "\n".join(lines_out) + "\n"
    REPORT_PATH.write_text(report_text, encoding="utf-8")

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.0f}s. Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
