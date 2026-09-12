"""
scripts/crossing_pass_second_call_probe.py

MEASUREMENT HARNESS ONLY -- no production file is imported for mutation, no
source commit follows this run. Report goes to diagnostics/latest_run.md
(overwrite).

Measures whether ONE dedicated SECOND vision call (image only, NOT the
production describe_palm_image prompt) reliably captures relational
crossings across ALL five convergence-participating lines (Head/Heart/
Fate/Life/Health), to justify -- or kill -- reopening the S99 "no separate/
direct vision calls outside the single unified describe_palm_image prompt"
constraint.

  ARM E (engineered) -- closed 8-token type menu + registry target menu,
           same vocabulary agent.palm_processor already uses for the
           production RELATIONSHIP field, but issued as its OWN, second,
           dedicated call.
  ARM F (free-form oracle, unchanged in design from the S100 probe's
           ARM B) -- free-text contact-kind, target constrained to the
           same SSOT menu so results land in the same matrix cells.
           Ground-truth reference only.

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
from agent.interpretive.observation_extractor import _parse_relationship_value  # noqa: E402
from openai import OpenAI  # noqa: E402

# ─────────────────────────── CONFIG BLOCK ────────────────────────────────
IMAGES: dict[str, str] = {
    "palm_right_test": "data/test_images/palm_right_test.jpg",
    "palm_left_test":  "data/test_images/palm_left_test.jpg",
    "athira":          "data/test_images/Athira Palm Right.jpeg",
    "fate_line":       "data/test_images/Fate line.jpeg",
    "back_hand_CTRL":  "data/test_images/Back Hand.jpeg",
}

N = 15  # stability is the whole question -- reuses the slope-boundary N standard

MODEL = "gpt-4o"
TEMPERATURE = 0.0
MAX_TOKENS = {"E": 900, "F": 800}

REPORT_PATH = _REPO_ROOT / "diagnostics" / "latest_run.md"

STABLE_THRESHOLD = 12 / 15   # 80% -- "his slope-boundary standard"
UNSTABLE_LOW = 0.40
UNSTABLE_HIGH_EXCL = STABLE_THRESHOLD  # [0.40, 0.80) is the unstable band

_FAINT_RE = re.compile(r"not clearly visible|barely visible|\bfaint\b", re.I)

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
            "crossing_pass_second_call_probe: missing configured image(s):\n  "
            + "\n  ".join(missing)
        )
    return resolved


# ───────────────────── registry-derived lines + target menus ─────────────
EMITTING_LINES: list[str] = list(pp._CONVERGENCE_LINES)  # Life/Head/Heart/Fate/Health, SSOT


def _target_menu_list(feature: str) -> list[str]:
    """Parses the SAME SSOT string agent.palm_processor._relationship_target_menu
    builds ("{a | b | c}") into a list -- reuses the helper, never re-lists."""
    raw = pp._relationship_target_menu(feature)
    return [t.strip() for t in raw.strip("{}").split("|")]


PAIRS: dict[str, list[str]] = {ln: _target_menu_list(ln) for ln in EMITTING_LINES}


# ───────────────────────────── ARM E prompt ───────────────────────────────
def arm_e_prompt() -> str:
    line_menu = "{" + " | ".join(EMITTING_LINES) + "}"
    menu_lines = "\n".join(
        f"  {ln}: {{" + " | ".join(PAIRS[ln]) + "}}" for ln in EMITTING_LINES
    )
    return (
        "You are tracing palm lines for contacts only. For EACH of "
        f"{line_menu} present in the image, trace it from origin to end. "
        "Each time it clearly touches, crosses, is crossed by, meets, is "
        "stopped by, merges at origin with, takes possession of, or "
        "receives a branch from another line or mount, output one line: "
        "\"RELATIONSHIP: <line> -> <type> <target> [at <mount>]\". <type> "
        f"is exactly one of {pp._relationship_type_menu()}. <target> is "
        "exactly one of the targets listed for that line below (pick only "
        "from that line's own list):\n"
        f"{menu_lines}\n"
        "Append \"at <mount>\" ONLY for cuts/cut_by/meets where the "
        f"crossing mount is legible (choose from {pp._mount_menu()}); omit "
        "it otherwise. If a line is faint or not clearly visible, output "
        "nothing for it. If NO line in the image has any contacts at all, "
        "output exactly \"NONE\" and nothing else. Output ONLY "
        "\"RELATIONSHIP: ...\" lines (or the single word NONE), nothing "
        "else -- no preamble, no explanation, no markdown."
    )


_ARM_E_LINE_RE = re.compile(r"^RELATIONSHIP:\s*(Line of \w+)\s*->\s*(.+)$", re.I)


def parse_arm_e(raw_text: str, *, image_key: str, run_idx: int) -> dict[tuple[str, str], str]:
    cells: dict[tuple[str, str], str] = {}
    for raw_line in raw_text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.upper() == "NONE":
            continue
        m = _ARM_E_LINE_RE.match(stripped)
        if not m:
            continue
        line_raw, rest = m.group(1), m.group(2)
        line = next((ln for ln in EMITTING_LINES if ln.lower() == line_raw.strip().lower()), None)
        if line is None:
            print(
                f"  [ARM E off-menu LINE] image={image_key!r} run={run_idx} "
                f"line={line_raw!r} raw={stripped!r}",
                file=sys.stderr,
            )
            continue
        try:
            parsed = _parse_relationship_value(rest)
        except Exception as exc:  # noqa: BLE001 -- malformed line must not kill the rest of the block
            print(
                f"  [ARM E parse error] image={image_key!r} run={run_idx} "
                f"line={line!r} raw={stripped!r}: {exc}",
                file=sys.stderr,
            )
            continue
        if parsed is None:
            continue
        type_token, target, _mount = parsed
        if type_token not in pp._TYPED_RELATION_TOKENS:
            print(
                f"  [ARM E off-menu TYPE] image={image_key!r} run={run_idx} "
                f"line={line!r} type={type_token!r} raw={stripped!r}",
                file=sys.stderr,
            )
            continue
        if target not in PAIRS[line]:
            print(
                f"  [ARM E off-menu TARGET] image={image_key!r} run={run_idx} "
                f"line={line!r} target={target!r} raw={stripped!r}",
                file=sys.stderr,
            )
            continue
        if (line, target) not in cells:
            cells[(line, target)] = type_token
    return cells


# ───────────────────────────── ARM F prompt ───────────────────────────────
def arm_f_prompt() -> str:
    line_menu = "{" + " | ".join(EMITTING_LINES) + "}"
    menu_lines = "\n".join(
        f"  {ln}: {{" + " | ".join(PAIRS[ln]) + "}}" for ln in EMITTING_LINES
    )
    return (
        "You are a trained observer examining a palm image. For each of "
        f"{line_menu}, visually trace the line from its origin to its end. "
        "For every OTHER line or mount that line clearly touches, crosses, "
        "is crossed by, is stopped by, merges with, or takes possession of "
        "along its course, output one line in exactly this format:\n"
        "<LINE NAME>: <target> - <contact kind, in your own words, e.g. "
        "crosses / touches / is stopped by / merges with / runs alongside>\n"
        f"<LINE NAME> is exactly one of {line_menu}. <target> is exactly "
        "one of the targets listed for that line below (pick only from "
        "that line's own list, one output line per interaction found):\n"
        f"{menu_lines}\n"
        "If a line has no clear interactions with anything on its list, "
        "output \"<LINE NAME>: none\" instead. If the line itself is not "
        "clearly visible, output \"<LINE NAME>: not clearly visible\" "
        "instead. Output ONLY these lines, nothing else -- no preamble, no "
        "explanation, no markdown."
    )


def _arm_f_line_re() -> re.Pattern:
    alt = "|".join(re.escape(ln) for ln in EMITTING_LINES)
    return re.compile(rf"^({alt}):\s*(.+)$", re.I)


_ARM_F_LINE_RE = _arm_f_line_re()


def parse_arm_f(raw_text: str, *, image_key: str, run_idx: int) -> dict:
    cells: dict[tuple[str, str], str] = {}
    faint: dict[str, bool] = {}
    for raw_line in raw_text.splitlines():
        stripped = raw_line.strip()
        m = _ARM_F_LINE_RE.match(stripped)
        if not m:
            continue
        line_raw, value = m.group(1), m.group(2).strip()
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
            print(
                f"  [ARM F off-menu TARGET] image={image_key!r} run={run_idx} "
                f"line={line!r} target={target!r} raw={stripped!r}",
                file=sys.stderr,
            )
            continue
        if (line, target) not in cells:
            cells[(line, target)] = kind
    return {"cells": cells, "faint": faint}


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


# ───────────────────────────── run orchestration ──────────────────────────
def _run_batch(system_prompt: str, image_bytes: bytes, mime: str, *,
               arm: str, image_key: str, count: int) -> list[str | None]:
    raws = []
    for run_idx in range(count):
        raw = _call_vision(system_prompt, image_bytes, mime, arm=arm, image_key=image_key, run_idx=run_idx)
        raws.append(raw)
        print(f"  {image_key} / arm {arm} / run {run_idx + 1}/{count} -> {'OK' if raw else 'ERROR'}")
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

    prompt_e = arm_e_prompt()
    prompt_f = arm_f_prompt()

    # results[image_key][arm] = {"raws": [...], "parsed": [...] }
    #   E parsed entries: dict[(line,target) -> type_token]
    #   F parsed entries: {"cells": {...}, "faint": {...}}
    results: dict[str, dict[str, dict]] = {}

    for image_key, path in resolved_paths.items():
        image_bytes = path.read_bytes()
        mime = _mime_for(image_bytes)
        results[image_key] = {}

        for arm, sys_prompt in (("E", prompt_e), ("F", prompt_f)):
            print(f"\n=== {image_key} / ARM {arm} : {N} runs ===")
            raws = _run_batch(sys_prompt, image_bytes, mime, arm=arm, image_key=image_key, count=N)
            parsed = []
            for run_idx, raw in enumerate(raws):
                if raw is None:
                    parsed.append(None)
                elif arm == "E":
                    parsed.append(parse_arm_e(raw, image_key=image_key, run_idx=run_idx))
                else:
                    parsed.append(parse_arm_f(raw, image_key=image_key, run_idx=run_idx))
            results[image_key][arm] = {"raws": raws, "parsed": parsed}

    # ── helpers over the collected results ──────────────────────────────
    def _cell_series(image_key: str, arm: str, line: str, target: str) -> list[str | None]:
        parsed_list = results[image_key][arm]["parsed"]
        out = []
        for p in parsed_list:
            if p is None:
                out.append(None)
                continue
            cells = p if arm == "E" else p["cells"]
            out.append(cells.get((line, target)))
        return out

    def _image_line_faint(image_key: str, line: str) -> bool:
        """Ground truth for 'this line is faint on this image', derived from
        ARM F's own self-report (majority vote across its N runs) -- ARM E's
        prompt has no faintness marker of its own (it is told to silently
        omit a faint line, not to state it), so F is the shared reference
        both arms' faint-line control is checked against. Documented in the
        report as a deliberate methodology choice."""
        parsed_list = results[image_key]["F"]["parsed"]
        faint_votes = sum(
            1 for p in parsed_list if p is not None and p["faint"].get(line, False)
        )
        seen_votes = sum(1 for p in parsed_list if p is not None)
        return seen_votes > 0 and faint_votes > seen_votes / 2

    # ── controls ─────────────────────────────────────────────────────
    control_rows: list[dict] = []

    for arm in ("E", "F"):
        parsed_list = results["back_hand_CTRL"][arm]["parsed"]
        failures = []
        for run_idx, p in enumerate(parsed_list):
            if p is None:
                continue
            cells = p if arm == "E" else p["cells"]
            for (line, target), type_token in cells.items():
                failures.append(f"run {run_idx}: {line} {type_token} {target}")
        control_rows.append({
            "control": "back_hand_CTRL: 0 crossings",
            "image": "back_hand_CTRL",
            "arm": arm,
            "status": "FAIL" if failures else "PASS",
            "detail": "; ".join(failures) if failures else "0 crossings in all runs",
        })

    for image_key in IMAGES:
        line_faint = {ln: _image_line_faint(image_key, ln) for ln in EMITTING_LINES}
        health_absent = line_faint["Line of Health"]
        for arm in ("E", "F"):
            parsed_list = results[image_key][arm]["parsed"]
            health_fail = []
            faint_fail = []
            for run_idx, p in enumerate(parsed_list):
                if p is None:
                    continue
                cells = p if arm == "E" else p["cells"]
                for (line, target), type_token in cells.items():
                    if target == "Line of Health" and health_absent:
                        health_fail.append(f"run {run_idx}: {line} {type_token} Line of Health")
                    if line_faint.get(line, False):
                        faint_fail.append(f"run {run_idx}: {line} (faint) still emitted {target}({type_token})")
            control_rows.append({
                "control": "absent Health -> no Health-target emission",
                "image": image_key,
                "arm": arm,
                "status": "FAIL" if health_fail else "PASS",
                "detail": "; ".join(health_fail) if health_fail else (
                    "clean (Health judged absent)" if health_absent else "n/a (Health judged present)"
                ),
            })
            control_rows.append({
                "control": "faint line -> no emission",
                "image": image_key,
                "arm": arm,
                "status": "FAIL" if faint_fail else "PASS",
                "detail": "; ".join(faint_fail) if faint_fail else (
                    "clean" if any(line_faint.values()) else "n/a (no line judged faint)"
                ),
            })

    # ── report assembly: matrices ───────────────────────────────────
    lines_out: list[str] = []
    lines_out.append("# Crossing-Pass Second-Call Probe (S100 follow-up)\n")
    lines_out.append(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines_out.append(f"**Model:** {MODEL}, temperature={TEMPERATURE}  ")
    lines_out.append(f"**N:** {N}  ")
    lines_out.append(
        "**Scope:** measurement harness only. No production file modified. "
        "No commit follows this run.\n"
    )
    lines_out.append(
        "**Methodology note:** both arms are a dedicated SECOND vision call "
        "(image only), completely separate from agent.palm_processor."
        "describe_palm_image -- neither arm is the production prompt. ARM E "
        "reuses the production 8-token type menu / target menu / mount menu "
        "helpers verbatim. ARM F's contact-kind is free text (ground-truth "
        "reference only); its target is constrained to the same SSOT menu "
        "so results land in the same matrix cells. ARM E's prompt has no "
        "explicit faintness marker (it is told to silently omit a faint "
        "line) -- both arms' faint-line and absent-Health controls are "
        "therefore checked against a SHARED ground truth derived from ARM "
        "F's own per-image majority faintness self-report; this is a "
        "deliberate methodology choice, flagged here rather than silently "
        "assumed.\n"
    )

    all_cells: list[tuple[str, str, str]] = []  # (image, line, target) for non-CTRL images
    for image_key in IMAGES:
        lines_out.append(f"\n## Image: `{image_key}` ({IMAGES[image_key]})\n")

        err_e = sum(1 for r in results[image_key]["E"]["raws"] if r is None)
        err_f = sum(1 for r in results[image_key]["F"]["raws"] if r is None)
        if err_e or err_f:
            lines_out.append(f"*Call errors this image:* arm E: {err_e}, arm F: {err_f}\n")

        lines_out.append("| Line -> Target | E: k/N (type) | F: k/N (type) |")
        lines_out.append("|---|---|---|")
        for line in EMITTING_LINES:
            for target in PAIRS[line]:
                cellE = _cell_series(image_key, "E", line, target)
                cellF = _cell_series(image_key, "F", line, target)
                he, ne, te = _majority(cellE)
                hf, nf, tf = _majority(cellF)
                lines_out.append(
                    f"| {line} -> {target} | {he}/{ne} ({te}) | {hf}/{nf} ({tf}) |"
                )
                if image_key != "back_hand_CTRL":
                    all_cells.append((image_key, line, target))

    # ── controls table ───────────────────────────────────────────────
    lines_out.append("\n## Controls\n")
    lines_out.append("| Control | Image | Arm | Status | Detail |")
    lines_out.append("|---|---|---|---|---|")
    for row in control_rows:
        lines_out.append(
            f"| {row['control']} | {row['image']} | {row['arm']} | {row['status']} | {row['detail']} |"
        )

    # ── BAR EVALUATION ───────────────────────────────────────────────
    lines_out.append("\n## BAR EVALUATION\n")

    # (i) COMPLETENESS
    completeness_misses = []
    for image_key, line, target in all_cells:
        cellF = _cell_series(image_key, "F", line, target)
        hf, nf, tf = _majority(cellF)
        rate_f = hf / nf if nf else 0.0
        if rate_f >= STABLE_THRESHOLD:
            cellE = _cell_series(image_key, "E", line, target)
            he, ne, te = _majority(cellE)
            rate_e = he / ne if ne else 0.0
            if rate_e < STABLE_THRESHOLD or te != tf:
                completeness_misses.append(
                    f"{image_key}: {line} -> {target} | F={hf}/{nf} ({tf}) | "
                    f"E={he}/{ne} ({te})"
                )
    lines_out.append("**(i) COMPLETENESS** -- every cell where F >= 12/15, checked for E >= 12/15 SAME type:\n")
    if completeness_misses:
        lines_out.append(f"MISSED/DISAGREED ({len(completeness_misses)}):\n")
        for m in completeness_misses:
            lines_out.append(f"  - {m}")
    else:
        lines_out.append("None -- every F>=80% cell is matched by E>=80% at the same majority type.")
    lines_out.append("")

    # (ii) COVERAGE
    coverage_beyond_fate: dict[str, list[str]] = {ln: [] for ln in EMITTING_LINES if ln != "Line of Fate"}
    for image_key, line, target in all_cells:
        if line == "Line of Fate":
            continue
        he, ne, te = _majority(_cell_series(image_key, "E", line, target))
        if he > 0:
            coverage_beyond_fate[line].append(f"{image_key}: {line} -> {target} ({he}/{ne}, {te})")
    lines_out.append("**(ii) COVERAGE** -- does E fire on pairs beyond Fate (Head/Heart/Life/Health)?\n")
    any_beyond_fate = any(coverage_beyond_fate.values())
    if any_beyond_fate:
        for ln, hits in coverage_beyond_fate.items():
            lines_out.append(f"  - {ln}: {len(hits)} hit(s)")
            for h in hits:
                lines_out.append(f"      - {h}")
    else:
        lines_out.append("  - NO -- E fired on zero pairs outside Line of Fate as emitter.")
    lines_out.append("")

    # (iii) STABILITY
    unstable_cells = []
    stable_cells = []
    for image_key, line, target in all_cells:
        he, ne, te = _majority(_cell_series(image_key, "E", line, target))
        rate = he / ne if ne else 0.0
        if UNSTABLE_LOW <= rate < UNSTABLE_HIGH_EXCL:
            unstable_cells.append(f"{image_key}: {line} -> {target} ({he}/{ne}, {te})")
        elif rate >= STABLE_THRESHOLD:
            stable_cells.append(f"{image_key}: {line} -> {target} ({he}/{ne}, {te})")
    lines_out.append(
        f"**(iii) STABILITY** -- E cells in the 40-79% band (unstable) vs >=80% (stable):\n"
    )
    lines_out.append(f"  - Unstable (40-79%): {len(unstable_cells)}")
    for c in unstable_cells:
        lines_out.append(f"      - {c}")
    lines_out.append(f"  - Stable (>=80%): {len(stable_cells)}")
    for c in stable_cells:
        lines_out.append(f"      - {c}")
    lines_out.append("")

    # (iv) DISAGREEMENT (bug detector) -- any-hit presence compared, deliberately
    # inclusive (rate>0, not majority) so this list catches every discrepancy for
    # human sign-off rather than only majority-level ones.
    disagreements = []
    for image_key, line, target in all_cells:
        he, ne, te = _majority(_cell_series(image_key, "E", line, target))
        hf, nf, tf = _majority(_cell_series(image_key, "F", line, target))
        present_e, present_f = he > 0, hf > 0
        if present_e != present_f:
            disagreements.append(
                f"{image_key}: {line} -> {target} | PRESENCE differs -- "
                f"E={he}/{ne} ({te}) vs F={hf}/{nf} ({tf})"
            )
        elif present_e and present_f and te != tf:
            disagreements.append(
                f"{image_key}: {line} -> {target} | TYPE differs -- "
                f"E={he}/{ne} ({te}) vs F={hf}/{nf} ({tf})"
            )
    lines_out.append("**(iv) DISAGREEMENT (bug detector)** -- E vs F differ on presence or type, flagged for human visual sign-off:\n")
    if disagreements:
        for d in disagreements:
            lines_out.append(f"  - {d}")
    else:
        lines_out.append("  - None -- E and F agree (presence and type) on every cell.")
    lines_out.append("")

    # (v) VERDICT
    controls_clean = all(row["status"] == "PASS" for row in control_rows)
    completeness_clean = not completeness_misses
    coverage_clean = all(len(hits) > 0 for hits in coverage_beyond_fate.values())
    bar_clear = completeness_clean and coverage_clean and controls_clean

    failure_modes = []
    if not completeness_clean:
        failure_modes.append(
            f"COMPLETENESS: {len(completeness_misses)} cell(s) where F is reliable (>=80%) "
            "but E misses or disagrees on type."
        )
    if not coverage_clean:
        missing_lines = [ln for ln, hits in coverage_beyond_fate.items() if not hits]
        failure_modes.append(
            f"COVERAGE: E never fired for {missing_lines} as emitter -- "
            "coverage does not span all pairs."
        )
    if not controls_clean:
        failed = [f"{r['control']} ({r['image']}/{r['arm']})" for r in control_rows if r["status"] == "FAIL"]
        failure_modes.append(f"CONTROLS: {failed}")

    lines_out.append("**(v) VERDICT** -- does E clear the bar?\n")
    lines_out.append(f"  - Controls clean: {controls_clean}")
    lines_out.append(f"  - Completeness clean (every F>=80% matched by E>=80% same type): {completeness_clean}")
    lines_out.append(f"  - Coverage spans all pairs (E fires beyond Fate on every other line): {coverage_clean}")
    lines_out.append(f"\n  **{'YES' if bar_clear else 'NO'}**\n")
    if not bar_clear:
        biggest = max(failure_modes, key=len) if failure_modes else "unknown"
        lines_out.append(f"  Single biggest failure mode: {biggest}")
        if len(failure_modes) > 1:
            lines_out.append("  (other failure modes also present, listed above)")

    report_text = "\n".join(lines_out) + "\n"
    REPORT_PATH.write_text(report_text, encoding="utf-8")

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.0f}s. Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
