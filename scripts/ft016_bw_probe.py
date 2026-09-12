"""
scripts/ft016_bw_probe.py

MEASUREMENT HARNESS ONLY -- no production file is imported for mutation, no
source commit follows this run. Report goes to diagnostics/latest_run.md
(overwrite).

Two questions on the SAME physical right hand, three image treatments
(black-and-white, vivid-cool filter, unfiltered colour):

  Q1 (FT_016): does the current committed pipeline detect a Fate<->Heart
     contact on the B&W image -- the touch vivid-cool and unfiltered both
     missed (0/3 each, prior probe)?
  Q2 (general): does monochrome improve overall line detection vs colour --
     more lines reported present/clear, fewer faint/not-visible verdicts?

Reuses committed production code only -- describe_palm_image,
extract_relations, map_contact -- none reimplemented.
"""

from __future__ import annotations

import re
import sys
import time
import traceback
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from agent.palm_processor import describe_palm_image  # noqa: E402
from agent.interpretive.observation_extractor import extract_relations  # noqa: E402
from agent.interpretive.contact_mapper import map_contact  # noqa: E402

REPORT_PATH = _REPO_ROOT / "diagnostics" / "latest_run.md"
_IMAGES_DIR = _REPO_ROOT / "data" / "test_images"

HAND = "right"
N = 3


def _resolve_by_stem(stem: str) -> Path:
    matches = sorted(_IMAGES_DIR.glob(f"{stem}.*"))
    if len(matches) == 0:
        raise FileNotFoundError(
            f"ft016_bw_probe: no file found for stem {stem!r} in {_IMAGES_DIR} -- "
            f"place the image as {stem}.<ext>."
        )
    if len(matches) > 1:
        raise RuntimeError(
            f"ft016_bw_probe: ambiguous -- multiple files match stem {stem!r}: "
            f"{[m.name for m in matches]}. Do not guess; resolve manually."
        )
    return matches[0]


_BLOCK_HEADER_RE = re.compile(
    r"^(HAND SHAPE|FINGERS|THUMB|LIFE LINE|HEAD LINE|HEART LINE|FATE LINE"
    r"|LINE OF HEALTH|LINE OF MARRIAGE|OTHER LINES|MOUNTS|MARKS):",
)
_FEATURE_BLOCK_LABEL = {
    "LIFE LINE": "Line of Life", "HEAD LINE": "Line of Head",
    "HEART LINE": "Line of Heart", "FATE LINE": "Line of Fate",
    "LINE OF HEALTH": "Line of Health", "LINE OF MARRIAGE": "Line of Marriage",
}
_LINE_STATUS_LABELS = ("LIFE LINE", "HEAD LINE", "HEART LINE", "FATE LINE", "LINE OF HEALTH")


def _block_text(raw_text: str, feature: str) -> str:
    lines_acc: list[str] = []
    current = None
    for line in raw_text.splitlines():
        stripped = line.strip()
        header = _BLOCK_HEADER_RE.match(stripped)
        if header:
            current = _FEATURE_BLOCK_LABEL.get(header.group(1))
            if current == feature:
                lines_acc.append(stripped)
            continue
        if current == feature:
            lines_acc.append(stripped)
    return "\n".join(lines_acc)


def classify_lines(raw_text: str) -> dict[str, str]:
    """Classifies each of Life/Head/Heart/Fate/Health as 'clear'/'faint'/
    'not_visible', based ONLY on that line's own top-level header
    description text (never an indented subfield -- a SLOPE value of
    'not clearly visible' must not count as the whole line being invisible)."""
    status: dict[str, str] = {}
    for line in raw_text.splitlines():
        stripped = line.strip()
        for label in _LINE_STATUS_LABELS:
            if stripped.startswith(label + ":"):
                desc = stripped[len(label) + 1:].strip().lower()
                if "not clearly visible" in desc:
                    status[_FEATURE_BLOCK_LABEL[label]] = "not_visible"
                elif "faint" in desc or "barely visible" in desc:
                    status[_FEATURE_BLOCK_LABEL[label]] = "faint"
                else:
                    status[_FEATURE_BLOCK_LABEL[label]] = "clear"
                break
    return status


def _fate_heart_contacts(contacts: dict) -> list[dict]:
    found = []
    for emitter, other in (("Line of Fate", "Line of Heart"), ("Line of Heart", "Line of Fate")):
        for item in contacts.get(emitter, []):
            if item.get("target") == other:
                mapped = map_contact(item)
                found.append({"emitter": emitter, "item": item, "mapped": mapped})
    return found


def _run_batch(image_bytes: bytes, hand: str, count: int, *, tag: str) -> list[dict | None]:
    results = []
    for run_idx in range(count):
        try:
            raw = describe_palm_image(image_bytes, hand)
        except Exception as exc:  # noqa: BLE001 -- one failed run must not abort the probe
            print(f"  [ERROR] {tag} run={run_idx}: {exc}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            results.append(None)
            print(f"  {tag} run {run_idx + 1}/{count} -> ERROR")
            continue
        parsed = extract_relations(raw)
        results.append({"raw": raw, "parsed": parsed, "line_status": classify_lines(raw)})
        print(f"  {tag} run {run_idx + 1}/{count} -> OK")
    return results


def main() -> None:
    t0 = time.time()

    bw_path = _resolve_by_stem("palm_right_black_white")
    vivid_path = _resolve_by_stem("palm_right_vivid_cool")
    unfiltered_path = _resolve_by_stem("palm_right_test")
    print(f"Resolved: B&W={bw_path.name}, vivid-cool={vivid_path.name}, unfiltered={unfiltered_path.name}")

    IMAGES = {
        "black_white": bw_path,
        "vivid_cool": vivid_path,
        "unfiltered": unfiltered_path,
    }

    all_runs: dict[str, list[dict | None]] = {}
    for key, path in IMAGES.items():
        print(f"\n=== {key.upper()}: {path.name} ===")
        image_bytes = path.read_bytes()
        all_runs[key] = _run_batch(image_bytes, HAND, N, tag=key)

    lines_out: list[str] = []
    lines_out.append("# FT_016 B&W Probe + Line-Detection A/B/C (S104 Step 5a follow-up)\n")
    lines_out.append(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines_out.append(f"**Resolved files:** black_white={bw_path.name}, vivid_cool={vivid_path.name}, unfiltered={unfiltered_path.name}  ")
    lines_out.append(f"**N:** {N} per image (9 calls total), hand={HAND}, SAME physical hand across all three  ")
    lines_out.append(
        "**Scope:** measurement harness only. No production file modified. No "
        "commit follows this run. Reuses committed `describe_palm_image` / "
        "`extract_relations` / `map_contact` directly, none reimplemented.\n"
    )

    for key in IMAGES:
        n_err = sum(1 for r in all_runs[key] if r is None)
        if n_err:
            lines_out.append(f"*Call errors, {key}:* {n_err}/{N}")
    lines_out.append("")

    # 1. FT_016 FOCUS (B&W)
    lines_out.append("## 1. FT_016 FOCUS -- Fate<->Heart contacts (B&W image)\n")
    bw_meets_hits = 0
    bw_any_hits = 0
    for run_idx, r in enumerate(all_runs["black_white"]):
        lines_out.append(f"**Run {run_idx}:**")
        if r is None:
            lines_out.append("  ERROR\n")
            continue
        fh = _fate_heart_contacts(r["parsed"]["contacts"])
        if not fh:
            lines_out.append("  (no Fate<->Heart contact in either direction)")
        for entry in fh:
            item, mapped = entry["item"], entry["mapped"]
            lines_out.append(
                f"  - {entry['emitter']} -> {item['target']} | verb={item['verb']!r} | "
                f"position={item['position']!r} | clarity={item['clarity']!r} | "
                f"mapped_token={mapped['token']} | confidence={mapped['confidence']} | reason={mapped['reason']}"
            )
            if mapped["token"] == "meets":
                bw_meets_hits += 1
            if mapped["token"] is not None:
                bw_any_hits += 1
        fate_block = _block_text(r["raw"], "Line of Fate")
        heart_block = _block_text(r["raw"], "Line of Heart")
        mount_mentioned = "Mount of Jupiter" in fate_block or "Mount of Jupiter" in heart_block
        lines_out.append(f"  'Mount of Jupiter' substring present in Fate/Heart block text: {mount_mentioned} (NOTE: this can be a false positive -- e.g. Heart's own routine ORIGIN field; verify context before treating as location evidence)")
        lines_out.append("")
    lines_out.append(f"**Resolves to `meets`:** {bw_meets_hits}/{N}")
    lines_out.append(f"**Any Fate<->Heart contact (any token):** {bw_any_hits}/{N}\n")

    # 2. FT_016 three-way
    lines_out.append("## 2. FT_016 three-way comparison\n")
    rates = {}
    for key in IMAGES:
        hits = 0
        meets_hits = 0
        for r in all_runs[key]:
            if r is None:
                continue
            fh = _fate_heart_contacts(r["parsed"]["contacts"])
            if any(e["mapped"]["token"] is not None for e in fh):
                hits += 1
            if any(e["mapped"]["token"] == "meets" for e in fh):
                meets_hits += 1
        rates[key] = (hits, meets_hits)
    lines_out.append("| Image | Any Fate<->Heart contact (k/3) | Resolves to `meets` (k/3) |")
    lines_out.append("|---|---|---|")
    for key in IMAGES:
        hits, meets_hits = rates[key]
        lines_out.append(f"| {key} | {hits}/{N} | {meets_hits}/{N} |")
    newly_surfaced = rates["black_white"][0] > 0 and rates["vivid_cool"][0] == 0 and rates["unfiltered"][0] == 0
    lines_out.append(f"\n**Does B&W newly surface the contact (vs both other treatments at 0)?** {newly_surfaced}\n")

    # 3. LINE-DETECTION A/B/C
    lines_out.append("## 3. LINE-DETECTION A/B/C\n")
    feature_order = ("Line of Life", "Line of Head", "Line of Heart", "Line of Fate", "Line of Health")
    lines_out.append("| Image | clear | faint | not_visible | total lines counted | total contacts captured |")
    lines_out.append("|---|---|---|---|---|---|")
    detection_summary = {}
    for key in IMAGES:
        clear_c = faint_c = notvis_c = 0
        total_contacts = 0
        for r in all_runs[key]:
            if r is None:
                continue
            for feature in feature_order:
                status = r["line_status"].get(feature)
                if status == "clear":
                    clear_c += 1
                elif status == "faint":
                    faint_c += 1
                elif status == "not_visible":
                    notvis_c += 1
            for items in r["parsed"]["contacts"].values():
                total_contacts += len(items)
        total_counted = clear_c + faint_c + notvis_c
        detection_summary[key] = {"clear": clear_c, "faint": faint_c, "not_visible": notvis_c, "contacts": total_contacts}
        lines_out.append(f"| {key} | {clear_c} | {faint_c} | {notvis_c} | {total_counted} | {total_contacts} |")

    lines_out.append(
        "\n(Counts are totals across all 3 runs x 5 lines = up to 15 line-"
        "instances per image; a missing header in a given run -- rare, would "
        "show as fewer than 15 total counted -- is possible if the model ever "
        "omits a header line entirely.)\n"
    )

    # 4. Fate-line clarity specifically
    lines_out.append("## 4. Fate-line clarity, per image (the line that matters for FT_016)\n")
    for key in IMAGES:
        statuses = [r["line_status"].get("Line of Fate", "MISSING") if r else "ERROR" for r in all_runs[key]]
        lines_out.append(f"  - {key}: {statuses}")
    lines_out.append("")

    # 5. VERDICT
    lines_out.append("## 5. VERDICT\n")
    bw_detected = bw_any_hits > 0
    lines_out.append(f"**(i) FT_016 detected on B&W?** {'YES' if bw_detected else 'NO'}, at {bw_any_hits}/{N} (resolves to `meets`: {bw_meets_hits}/{N}).")
    if bw_detected:
        lines_out.append(
            "\n**PRODUCTION CAVEAT (restated explicitly):** this is B&W-image "
            "detection under a deliberate, user-applied filter -- NOT evidence "
            "about fresh-unfiltered-upload production behavior, per the locked "
            "architecture (production receives whatever a real user's camera "
            "captures; B&W conversion is not part of that pipeline). Do not "
            "treat this as resolving FT_016's migration blocker on its own."
        )
    else:
        lines_out.append("\nB&W did not change the FT_016 outcome in this sample -- still 0 across all three treatments.")

    # (ii) line-detection comparison
    bw_summary = detection_summary["black_white"]
    unfiltered_summary = detection_summary["unfiltered"]
    bw_clear_rate = bw_summary["clear"]
    unfiltered_clear_rate = unfiltered_summary["clear"]
    improves = bw_clear_rate > unfiltered_clear_rate and bw_summary["not_visible"] <= unfiltered_summary["not_visible"]

    lines_out.append(f"\n**(ii) Does B&W measurably improve line detection over colour on this hand?** {'YES' if improves else 'NO'}")
    lines_out.append(
        f"  - B&W: clear={bw_summary['clear']}, faint={bw_summary['faint']}, "
        f"not_visible={bw_summary['not_visible']}, contacts={bw_summary['contacts']}"
    )
    lines_out.append(
        f"  - Unfiltered: clear={unfiltered_summary['clear']}, faint={unfiltered_summary['faint']}, "
        f"not_visible={unfiltered_summary['not_visible']}, contacts={unfiltered_summary['contacts']}"
    )
    vivid_summary = detection_summary["vivid_cool"]
    lines_out.append(
        f"  - Vivid-cool (for reference): clear={vivid_summary['clear']}, faint={vivid_summary['faint']}, "
        f"not_visible={vivid_summary['not_visible']}, contacts={vivid_summary['contacts']}"
    )
    lines_out.append(
        "\n  **This is N=3 on ONE hand -- a signal, not a conclusion.** A real B&W-"
        "adoption decision would need a wider A/B across multiple hands, and "
        "should be reconciled against whatever prior enhancement-preprocessing "
        "rejection is on record (a contrast/preprocessing proposal was raised "
        "and not adopted per this project's own V1.1 register -- this result "
        "does not itself overturn that, it's one more data point for whoever "
        "revisits it)."
    )

    report_text = "\n".join(lines_out) + "\n"
    REPORT_PATH.write_text(report_text, encoding="utf-8")

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s. Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
