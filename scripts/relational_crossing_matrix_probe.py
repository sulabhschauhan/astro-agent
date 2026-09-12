"""
scripts/relational_crossing_matrix_probe.py

MEASUREMENT HARNESS ONLY -- no production file is imported for mutation, no
source commit follows this run. Report goes to diagnostics/latest_run.md
(overwrite).

Measures the whole Head/Heart/Fate relational-crossing matrix across three
arms on real palm images:

  ARM A -- production baseline. agent.palm_processor._build_description_
           system_prompt(hand), UNMODIFIED, parsed via the live typed-
           RELATIONSHIP extractor (observation_extractor.extract_relations).
  ARM B -- oracle (ground-truth-only, ruled out as a shippable fix by S99's
           hard "no separate/direct vision calls" constraint). A local
           free-form active-trace prompt with NO closed 8-token type menu
           -- the model states the contact kind in its own words. Targets
           ARE constrained to the same SSOT target menu as A/C so results
           land in the same matrix cells (design note in the report).
  ARM C -- hypothesis. Byte-identical to ARM A's prompt EXCEPT every
           RELATIONSHIP field block (Head/Heart/Fate/Health/Marriage) is
           swapped for an active-trace variant wired through the exact
           same registry-derived menu helpers ARM A uses.

Every (emitting_line, target) pair is enumerated from the registry via
agent.palm_processor's own SSOT helpers -- never hardcoded here
(GENERALIZATION GATE).
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
from agent.interpretive.observation_extractor import extract_relations  # noqa: E402
from openai import OpenAI  # noqa: E402

# ─────────────────────────── CONFIG BLOCK ────────────────────────────────
IMAGES: dict[str, dict[str, str]] = {
    "palm_right_test": {"path": "data/test_images/palm_right_test.jpg", "hand": "right"},
    "palm_left_test":  {"path": "data/test_images/palm_left_test.jpg",  "hand": "left"},
    "athira_right":    {"path": "data/test_images/Athira Palm Right.jpeg", "hand": "right"},
    "fate_line":       {"path": "data/test_images/Fate line.jpeg", "hand": "right"},
    "back_hand_CTRL":  {"path": "data/test_images/Back Hand.jpeg", "hand": "right"},
}

N = 6                 # runs per arm per image
BOUNDARY_N = 15        # re-run count for any pair landing at 40-60% in any arm
BOUNDARY_LOW = 0.40
BOUNDARY_HIGH = 0.60

MODEL = "gpt-4o"
TEMPERATURE = 0.0
MAX_TOKENS = {"A": 600, "B": 600, "C": 900}

REPORT_PATH = _REPO_ROOT / "diagnostics" / "latest_run.md"

EMITTING_LINES = ["Line of Head", "Line of Heart", "Line of Fate"]
LIFE_PARTNERS = [ln for ln in pp._CONVERGENCE_LINES if ln != "Line of Life"]

_FAINT_RE = re.compile(r"not clearly visible|barely visible|\bfaint\b", re.I)

# ─────────────────────── path validation (fail fast) ─────────────────────
def _validate_paths() -> dict[str, Path]:
    resolved = {}
    missing = []
    for key, cfg in IMAGES.items():
        p = _REPO_ROOT / cfg["path"]
        if not p.is_file():
            missing.append(f"{key} -> {p}")
        else:
            resolved[key] = p
    if missing:
        raise FileNotFoundError(
            "relational_crossing_matrix_probe: missing configured image(s):\n  "
            + "\n  ".join(missing)
        )
    return resolved


# ─────────────────────── registry-derived target menus ───────────────────
def _target_menu_list(feature: str) -> list[str]:
    """Parses the SAME SSOT string agent.palm_processor._relationship_target_menu
    builds ("{a | b | c}") into a list -- reuses the helper, never re-lists."""
    raw = pp._relationship_target_menu(feature)
    return [t.strip() for t in raw.strip("{}").split("|")]


PAIRS: dict[str, list[str]] = {ln: _target_menu_list(ln) for ln in EMITTING_LINES}


# ───────────────────────────── ARM A prompt ───────────────────────────────
def arm_a_prompt(hand: str) -> str:
    return pp._build_description_system_prompt(hand)  # unmodified, production baseline


# ───────────────────────────── ARM C prompt ───────────────────────────────
_ARM_C_TARGET_FEATURES = [
    "Line of Head", "Line of Heart", "Line of Fate",
    "Line of Health", "Line of Marriage",
]


def _active_trace_relationship_field(feature: str) -> str:
    """Same shape as pp._relationship_field(feature) -- reuses the exact
    same registry-derived menu helpers -- but with active-trace wording
    substituted for the RELATIONSHIP instruction sentence (the ONE
    hypothesis-under-test difference from ARM A)."""
    return (
        "  RELATIONSHIP: trace this line from its origin to its end; each time "
        "it clearly touches, crosses, is crossed by, is stopped by, or merges "
        "with another line or mount, emit a separate \"RELATIONSHIP: <type> "
        "<target> [at <mount>]\" line. <type> is exactly one of "
        f"{pp._relationship_type_menu()}. <target> is exactly one of "
        f"{pp._relationship_target_menu(feature)}. Append \"at <mount>\" ONLY "
        "for cuts/cut_by/meets where the crossing mount is legible (choose "
        f"from {pp._mount_menu()}); omit it otherwise. If none clearly "
        "visible, write \"RELATIONSHIP: none\".\n"
    )


def arm_c_prompt(hand: str) -> str:
    prompt = arm_a_prompt(hand)
    for feature in _ARM_C_TARGET_FEATURES:
        old = pp._relationship_field(feature)
        new = _active_trace_relationship_field(feature)
        if old not in prompt:
            raise RuntimeError(
                f"relational_crossing_matrix_probe: ARM C build failed -- "
                f"RELATIONSHIP block for {feature!r} not found verbatim in "
                "ARM A's prompt (byte-identity assumption broken)."
            )
        prompt = prompt.replace(old, new)
    return prompt


# ───────────────────────────── ARM B prompt ───────────────────────────────
def arm_b_prompt() -> str:
    menu_lines = "\n".join(
        f"  {ln}: {{" + " | ".join(PAIRS[ln]) + "}}" for ln in EMITTING_LINES
    )
    line_menu = "{" + " | ".join(EMITTING_LINES) + "}"
    return (
        "You are a trained observer examining a palm image. For each of the "
        "Head line, Heart line, and Fate line, visually trace the line from "
        "its origin to its end. For every OTHER line or mount that line "
        "clearly touches, crosses, is crossed by, is stopped by, merges "
        "with, or takes possession of along its course, output one line in "
        "exactly this format:\n"
        "<LINE NAME>: <target> - <contact kind, in your own words, e.g. "
        "crosses / touches / is stopped by / merges with / runs alongside>\n"
        f"<LINE NAME> is exactly one of {line_menu}. <target> is exactly one "
        "of the targets listed for that line below (pick only from that "
        "line's own list, one RELATIONSHIP-style output line per "
        "interaction found):\n"
        f"{menu_lines}\n"
        "If a line has no clear interactions with anything on its list, "
        "output \"<LINE NAME>: none\" instead. If the line itself is not "
        "clearly visible, output \"<LINE NAME>: not clearly visible\" "
        "instead. Output ONLY these lines, nothing else -- no preamble, no "
        "explanation, no markdown."
    )


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
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                    ],
                },
            ],
            max_tokens=MAX_TOKENS[arm],
            temperature=TEMPERATURE,
        )
        return response.choices[0].message.content
    except Exception as exc:  # noqa: BLE001 -- one failed run must not abort the matrix
        print(
            f"  [ERROR] image={image_key!r} arm={arm} run={run_idx}: {exc}",
            file=sys.stderr,
        )
        traceback.print_exc(file=sys.stderr)
        return None


def _mime_for(image_bytes: bytes) -> str:
    return "image/png" if image_bytes[:8].startswith(b"\x89PNG") else "image/jpeg"


# ───────────────────────────── parsing: A / C ─────────────────────────────
_BLOCK_HEADER_RE = re.compile(
    r"^(HAND SHAPE|FINGERS|THUMB|LIFE LINE|HEAD LINE|HEART LINE|FATE LINE"
    r"|LINE OF HEALTH|LINE OF MARRIAGE|OTHER LINES|MOUNTS|MARKS):",
)
_FEATURE_BLOCK_LABEL = {
    "HEAD LINE": "Line of Head",
    "HEART LINE": "Line of Heart",
    "FATE LINE": "Line of Fate",
    "LINE OF HEALTH": "Line of Health",
    "LINE OF MARRIAGE": "Line of Marriage",
}


def _feature_faintness(raw_text: str) -> dict[str, bool]:
    """Per top-level relational feature block, True if the block's own text
    (any line inside it, up to the next top-level header) contains a
    not-clearly-visible/barely-visible/faint phrase. Used only for the
    fabrication controls -- the model's own self-report is the ground truth
    proxy here (no independent human read exists per-run)."""
    lines = raw_text.splitlines()
    blocks: dict[str, list[str]] = {}
    current_label = None
    for line in lines:
        stripped = line.strip()
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
    return {
        feature: bool(_FAINT_RE.search("\n".join(body)))
        for feature, body in blocks.items()
    }


def parse_arm_ac(raw_text: str) -> dict:
    """Returns {"cells": {(line, target): type_token}, "faint": {feature: bool},
    "life_partners": set[str]}."""
    parsed = extract_relations(raw_text)
    targets = parsed.get("targets", {})

    cells: dict[tuple[str, str], str] = {}
    for line in EMITTING_LINES:
        feature_targets = targets.get(line, {})
        for type_token in pp._TYPED_RELATION_TOKENS:
            val = feature_targets.get(type_token)
            if val is None:
                continue
            candidates = val if isinstance(val, set) else {val}
            for t in candidates:
                if (line, t) not in cells:
                    cells[(line, t)] = type_token
                # else: a second type_token named the same target in the
                # same run -- first-seen wins, rare collision, not logged
                # separately (documented in the report methodology note).

    life_partners: set[str] = set()
    for feature in LIFE_PARTNERS:
        conv = targets.get(feature, {}).get("Convergence")
        if conv and "Line of Life" in conv:
            life_partners.add(feature)

    return {
        "cells": cells,
        "faint": _feature_faintness(raw_text),
        "life_partners": life_partners,
    }


# ───────────────────────────── parsing: B ─────────────────────────────────
_ARM_B_LINE_RE = re.compile(
    r"^(Line of Head|Line of Heart|Line of Fate):\s*(.+)$", re.I,
)


def parse_arm_b(raw_text: str) -> dict:
    cells: dict[tuple[str, str], str] = {}
    faint: dict[str, bool] = {}
    for raw_line in raw_text.splitlines():
        stripped = raw_line.strip()
        m = _ARM_B_LINE_RE.match(stripped)
        if not m:
            continue
        line_raw, value = m.group(1), m.group(2).strip()
        # Normalize to canonical casing via the emitting-line list.
        line = next((ln for ln in EMITTING_LINES if ln.lower() == line_raw.lower()), None)
        if line is None:
            continue
        low = value.lower()
        if low in ("none", ""):
            continue
        if "not clearly visible" in low or low == "faint" or "barely visible" in low:
            faint[line] = True
            continue
        if " - " in value:
            target, kind = value.split(" - ", 1)
            target, kind = target.strip(), kind.strip()
        else:
            target, kind = value.strip(), "(unlabelled)"
        if target not in PAIRS[line]:
            # off-menu target -- log to stderr, do not silently invent a cell
            print(
                f"  [ARM B off-menu] line={line!r} target={target!r} raw={value!r}",
                file=sys.stderr,
            )
            continue
        if (line, target) not in cells:
            cells[(line, target)] = kind
    return {"cells": cells, "faint": faint}


# ───────────────────────────── run orchestration ──────────────────────────
def _run_batch(system_prompt: str, image_bytes: bytes, mime: str, *,
               arm: str, image_key: str, count: int, start_idx: int) -> list[str | None]:
    raws = []
    for i in range(count):
        run_idx = start_idx + i
        raw = _call_vision(system_prompt, image_bytes, mime, arm=arm, image_key=image_key, run_idx=run_idx)
        raws.append(raw)
        print(f"  {image_key} / arm {arm} / run {run_idx + 1} -> {'OK' if raw else 'ERROR'}")
    return raws


def _majority(values: list[str | None]) -> tuple[int, int, str]:
    """Returns (hits, n, majority_type). hits/n over the FULL run count
    (errors count as non-hits, never reduce n)."""
    hit_vals = [v for v in values if v is not None]
    n = len(values)
    if not hit_vals:
        return 0, n, "-"
    majority_type = Counter(hit_vals).most_common(1)[0][0]
    return len(hit_vals), n, majority_type


def main() -> None:
    t0 = time.time()
    resolved_paths = _validate_paths()
    print(f"Resolved {len(resolved_paths)} image path(s), config valid.")

    image_bytes_cache: dict[str, bytes] = {}
    image_mime_cache: dict[str, str] = {}
    for key, path in resolved_paths.items():
        b = path.read_bytes()
        image_bytes_cache[key] = b
        image_mime_cache[key] = _mime_for(b)

    # results[image_key][arm] = {
    #   "runs": [raw_text_or_None, ...],
    #   "parsed": [parse_dict, ...],   (aligned index to runs)
    # }
    results: dict[str, dict[str, dict]] = {}

    for image_key, cfg in IMAGES.items():
        hand = cfg["hand"]
        image_bytes = image_bytes_cache[image_key]
        mime = image_mime_cache[image_key]
        results[image_key] = {}

        prompts = {
            "A": arm_a_prompt(hand),
            "B": arm_b_prompt(),
            "C": arm_c_prompt(hand),
        }

        for arm, sys_prompt in prompts.items():
            print(f"\n=== {image_key} / ARM {arm} : {N} baseline runs ===")
            raws = _run_batch(sys_prompt, image_bytes, mime, arm=arm, image_key=image_key, count=N, start_idx=0)
            parsed = [
                (parse_arm_ac(r) if arm in ("A", "C") else parse_arm_b(r)) if r is not None else None
                for r in raws
            ]
            results[image_key][arm] = {"raws": raws, "parsed": parsed, "prompt": sys_prompt}

    # ── boundary detection + targeted re-runs ──────────────────────────
    boundary_log: list[dict] = []

    def _cell_series(image_key: str, arm: str, line: str, target: str) -> list[str | None]:
        parsed_list = results[image_key][arm]["parsed"]
        out = []
        for p in parsed_list:
            if p is None:
                out.append(None)
                continue
            out.append(p["cells"].get((line, target)))
        return out

    for image_key in IMAGES:
        for arm in ("A", "B", "C"):
            boundary_hit = False
            for line in EMITTING_LINES:
                for target in PAIRS[line]:
                    series = _cell_series(image_key, arm, line, target)
                    hits, n, _ = _majority(series)
                    rate = hits / n if n else 0.0
                    if n and BOUNDARY_LOW <= rate <= BOUNDARY_HIGH:
                        boundary_hit = True
            if boundary_hit:
                print(f"\n=== BOUNDARY re-run: {image_key} / ARM {arm} : +{BOUNDARY_N} runs ===")
                cfg = IMAGES[image_key]
                hand = cfg["hand"]
                image_bytes = image_bytes_cache[image_key]
                mime = image_mime_cache[image_key]
                sys_prompt = (
                    arm_a_prompt(hand) if arm == "A" else
                    arm_b_prompt() if arm == "B" else
                    arm_c_prompt(hand)
                )
                extra_raws = _run_batch(
                    sys_prompt, image_bytes, mime, arm=arm, image_key=image_key,
                    count=BOUNDARY_N, start_idx=N,
                )
                extra_parsed = [
                    (parse_arm_ac(r) if arm in ("A", "C") else parse_arm_b(r)) if r is not None else None
                    for r in extra_raws
                ]
                results[image_key][arm]["raws"].extend(extra_raws)
                results[image_key][arm]["parsed"].extend(extra_parsed)

                for line in EMITTING_LINES:
                    for target in PAIRS[line]:
                        pooled = _cell_series(image_key, arm, line, target)
                        pre = pooled[:N]
                        hits_pre, n_pre, _ = _majority(pre)
                        rate_pre = hits_pre / n_pre if n_pre else 0.0
                        if BOUNDARY_LOW <= rate_pre <= BOUNDARY_HIGH:
                            hits_final, n_final, type_final = _majority(pooled)
                            rate_final = hits_final / n_final if n_final else 0.0
                            boundary_log.append({
                                "image": image_key, "arm": arm, "line": line, "target": target,
                                "initial": f"{hits_pre}/{n_pre} ({rate_pre:.0%})",
                                "final": f"{hits_final}/{n_final} ({rate_final:.0%}, type={type_final})",
                            })

    # ── controls ─────────────────────────────────────────────────────
    control_rows: list[dict] = []

    # back_hand_CTRL: 0 crossings expected in every arm.
    for arm in ("A", "B", "C"):
        parsed_list = results["back_hand_CTRL"][arm]["parsed"]
        failures = []
        for run_idx, p in enumerate(parsed_list):
            if p is None:
                continue
            for (line, target), type_token in p["cells"].items():
                failures.append(f"run {run_idx}: {line} {type_token} {target}")
        control_rows.append({
            "control": "back_hand_CTRL: 0 crossings",
            "arm": arm,
            "status": "FAIL" if failures else "PASS",
            "detail": "; ".join(failures) if failures else "0 crossings in all runs",
        })

    # Health-absent + faint-line controls: arms A/C only (need the block's
    # own presence self-report, which B's prompt does not produce for
    # Health/Marriage and does not require for faintness beyond its own
    # "not clearly visible" line, handled separately below).
    for image_key in IMAGES:
        for arm in ("A", "C"):
            parsed_list = results[image_key][arm]["parsed"]
            health_fail = []
            faint_fail = []
            for run_idx, p in enumerate(parsed_list):
                if p is None:
                    continue
                faint_map = p["faint"]
                health_absent = faint_map.get("Line of Health", True)  # block missing => treated absent
                for (line, target), type_token in p["cells"].items():
                    if target == "Line of Health" and health_absent:
                        health_fail.append(f"run {run_idx}: {line} {type_token} Line of Health")
                for feature, is_faint in faint_map.items():
                    if not is_faint or feature not in EMITTING_LINES:
                        continue
                    if any(line == feature for (line, _t) in p["cells"]):
                        offenders = [f"{t}({tt})" for (l, t), tt in p["cells"].items() if l == feature]
                        faint_fail.append(f"run {run_idx}: {feature} faint but asserted {offenders}")
            control_rows.append({
                "control": "Health-absent -> no RELATIONSHIP to Line of Health",
                "arm": f"{arm}/{image_key}",
                "status": "FAIL" if health_fail else "PASS",
                "detail": "; ".join(health_fail) if health_fail else "clean",
            })
            control_rows.append({
                "control": "faint emitting line -> RELATIONSHIP: none",
                "arm": f"{arm}/{image_key}",
                "status": "FAIL" if faint_fail else "PASS",
                "detail": "; ".join(faint_fail) if faint_fail else "clean",
            })

    # Arm B faint-line control (its own "not clearly visible" self-report).
    for image_key in IMAGES:
        parsed_list = results[image_key]["B"]["parsed"]
        faint_fail = []
        for run_idx, p in enumerate(parsed_list):
            if p is None:
                continue
            for feature, is_faint in p["faint"].items():
                if is_faint and any(l == feature for (l, _t) in p["cells"]):
                    offenders = [f"{t}({k})" for (l, t), k in p["cells"].items() if l == feature]
                    faint_fail.append(f"run {run_idx}: {feature} faint but asserted {offenders}")
        control_rows.append({
            "control": "faint emitting line -> RELATIONSHIP: none",
            "arm": f"B/{image_key}",
            "status": "FAIL" if faint_fail else "PASS",
            "detail": "; ".join(faint_fail) if faint_fail else "clean",
        })

    # ── report assembly ─────────────────────────────────────────────
    lines_out: list[str] = []
    lines_out.append("# Relational-Crossing Matrix Probe (S99 follow-up)\n")
    lines_out.append(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines_out.append(f"**Model:** {MODEL}, temperature={TEMPERATURE}  ")
    lines_out.append(f"**N (baseline):** {N}, **boundary re-run N:** +{BOUNDARY_N}  ")
    lines_out.append(
        "**Scope:** measurement harness only. No production file modified. "
        "No commit follows this run.\n"
    )
    lines_out.append(
        "**Methodology note (ARM B):** ARM B's contact-kind is genuinely "
        "free text (no closed 8-token menu) -- this is the axis under test "
        "for A/C. Its TARGET is constrained to the same SSOT target menu "
        "A/C use (`agent.palm_processor._relationship_target_menu`), so "
        "results land in the same matrix cells; an off-menu target named "
        "by the model is logged to stderr and dropped, never invented as a "
        "new row.\n"
    )

    for image_key, cfg in IMAGES.items():
        lines_out.append(f"\n## Image: `{image_key}` ({cfg['path']}, hand={cfg['hand']})\n")

        any_errors = {
            arm: sum(1 for r in results[image_key][arm]["raws"] if r is None)
            for arm in ("A", "B", "C")
        }
        err_note = ", ".join(
            f"arm {a}: {c} failed call(s)" for a, c in any_errors.items() if c
        )
        if err_note:
            lines_out.append(f"*Call errors this image:* {err_note}\n")

        lines_out.append("| Line -> Target | A: k/N (type) | B: k/N (type) | C: k/N (type) |")
        lines_out.append("|---|---|---|---|")
        for line in EMITTING_LINES:
            for target in PAIRS[line]:
                cellA = _cell_series(image_key, "A", line, target)
                cellB = _cell_series(image_key, "B", line, target)
                cellC = _cell_series(image_key, "C", line, target)
                ha, na, ta = _majority(cellA)
                hb, nb, tb = _majority(cellB)
                hc, nc, tc = _majority(cellC)
                lines_out.append(
                    f"| {line} -> {target} | {ha}/{na} ({ta}) | {hb}/{nb} ({tb}) | {hc}/{nc} ({tc}) |"
                )

        lines_out.append(f"\n**Line of Life -> * (legacy CONVERGENCE channel, target-only, no type)**\n")
        lines_out.append("| Life -> Target | A: k/N | C: k/N |")
        lines_out.append("|---|---|---|")
        for target in LIFE_PARTNERS:
            def _life_series(arm: str) -> list[str | None]:
                parsed_list = results[image_key][arm]["parsed"]
                out = []
                for p in parsed_list:
                    if p is None:
                        out.append(None)
                        continue
                    out.append("hit" if target in p["life_partners"] else None)
                return out
            ha, na, _ = _majority(_life_series("A"))
            hc, nc, _ = _majority(_life_series("C"))
            lines_out.append(f"| Line of Life -> {target} | {ha}/{na} | {hc}/{nc} |")

    lines_out.append("\n## Controls\n")
    lines_out.append("| Control | Arm/Scope | Status | Detail |")
    lines_out.append("|---|---|---|---|")
    for row in control_rows:
        lines_out.append(f"| {row['control']} | {row['arm']} | {row['status']} | {row['detail']} |")

    lines_out.append("\n## Boundary log (40-60% pairs, re-run at N=15)\n")
    if boundary_log:
        lines_out.append("| Image | Arm | Line -> Target | Initial (N=6) | Final (N=21) |")
        lines_out.append("|---|---|---|---|---|")
        for row in boundary_log:
            lines_out.append(
                f"| {row['image']} | {row['arm']} | {row['line']} -> {row['target']} | "
                f"{row['initial']} | {row['final']} |"
            )
    else:
        lines_out.append("No cell landed in the 40-60% band in any arm/image at N=6 -- no re-runs triggered.")

    # ── verdict ──────────────────────────────────────────────────────
    def _arm_summary(arm: str) -> tuple[int, int]:
        """Returns (pairs_with_any_hit, total_pairs) across all non-CTRL images."""
        total = 0
        hit = 0
        for image_key in IMAGES:
            if image_key == "back_hand_CTRL":
                continue
            for line in EMITTING_LINES:
                for target in PAIRS[line]:
                    total += 1
                    series = _cell_series(image_key, arm, line, target)
                    h, n, _ = _majority(series)
                    if h > 0:
                        hit += 1
        return hit, total

    hit_a, total_a = _arm_summary("A")
    hit_c, total_c = _arm_summary("C")

    def _missed_pairs(arm: str) -> list[str]:
        missed = []
        for image_key in IMAGES:
            if image_key == "back_hand_CTRL":
                continue
            for line in EMITTING_LINES:
                for target in PAIRS[line]:
                    series = _cell_series(image_key, arm, line, target)
                    h, n, _ = _majority(series)
                    if h == 0:
                        missed.append(f"{image_key}: {line} -> {target}")
        return missed

    missed_c = _missed_pairs("C")

    lifted_tokens = set()
    for image_key in IMAGES:
        for arm in ("A", "C"):
            for p in results[image_key][arm]["parsed"]:
                if p is None:
                    continue
                for type_token in p["cells"].values():
                    if type_token in ("stopped_by", "meets"):
                        lifted_tokens.add((arm, type_token))

    lines_out.append("\n## VERDICT\n")
    lines_out.append(
        f"**(i) ARM A dead or pair-varying?** ARM A produced at least one hit on "
        f"{hit_a}/{total_a} (line,target) pairs across the non-CTRL images. "
        f"{'Pair-varying (nonzero pairs fired).' if hit_a > 0 else 'Uniformly dead -- zero pairs fired anywhere.'}\n"
    )
    lines_out.append(
        f"**(ii) Does ARM C lift crossings for ALL pairs?** ARM C fired on "
        f"{hit_c}/{total_c} pairs. "
        f"{'YES -- every pair fired at least once.' if not missed_c else 'NO -- missed pairs:'}\n"
    )
    if missed_c:
        for m in missed_c:
            lines_out.append(f"  - {m}")
        lines_out.append("")
    lines_out.append(
        "**(iii) In-scope tokens (stopped_by/meets) that became real-hand-reachable "
        "in any arm:**\n"
    )
    if lifted_tokens:
        for arm, tok in sorted(lifted_tokens):
            lines_out.append(f"  - {tok} (arm {arm})")
    else:
        lines_out.append("  - none observed in A or C on these images.")

    report_text = "\n".join(lines_out) + "\n"
    REPORT_PATH.write_text(report_text, encoding="utf-8")

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.0f}s. Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
