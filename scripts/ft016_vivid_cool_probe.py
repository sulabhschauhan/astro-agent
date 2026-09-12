"""
scripts/ft016_vivid_cool_probe.py

MEASUREMENT HARNESS ONLY -- no production file is imported for mutation, no
source commit follows this run. Report goes to diagnostics/latest_run.md
(overwrite). Pure evidence check: does the CURRENT committed pipeline
(production describe_palm_image -> observation_extractor.extract_relations
'contacts' -> contact_mapper.map_contact) detect a Fate<->Heart contact on
the vivid-cool-filtered image -- the crossing FT_016's cutover-equivalence
gate (S104 Step 5a) found no unfiltered hand has ever surfaced. Decides
nothing on its own.

Reuses committed production code directly -- describe_palm_image,
extract_relations, map_contact -- none of it reimplemented here.
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

IMAGE_PATH = _REPO_ROOT / "data" / "test_images" / "palm_right_vivid_cool.jpeg"
UNFILTERED_IMAGE_PATH = _REPO_ROOT / "data" / "test_images" / "palm_right_test.jpg"
HAND = "right"
N = 3

_BLOCK_HEADER_RE = re.compile(
    r"^(HAND SHAPE|FINGERS|THUMB|LIFE LINE|HEAD LINE|HEART LINE|FATE LINE"
    r"|LINE OF HEALTH|LINE OF MARRIAGE|OTHER LINES|MOUNTS|MARKS):",
)
_FEATURE_BLOCK_LABEL = {
    "LIFE LINE": "Line of Life", "HEAD LINE": "Line of Head",
    "HEART LINE": "Line of Heart", "FATE LINE": "Line of Fate",
    "LINE OF HEALTH": "Line of Health", "LINE OF MARRIAGE": "Line of Marriage",
}


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
        results.append({"raw": raw, "parsed": parsed})
        print(f"  {tag} run {run_idx + 1}/{count} -> OK")
    return results


def _fate_heart_contacts(contacts: dict) -> list[dict]:
    """Every contact between Line of Fate and Line of Heart, either
    direction, with its mapped token."""
    found = []
    for emitter, other in (("Line of Fate", "Line of Heart"), ("Line of Heart", "Line of Fate")):
        for item in contacts.get(emitter, []):
            if item.get("target") == other:
                mapped = map_contact(item)
                found.append({"emitter": emitter, "item": item, "mapped": mapped})
    return found


def main() -> None:
    t0 = time.time()
    if not IMAGE_PATH.is_file():
        raise FileNotFoundError(f"ft016_vivid_cool_probe: missing image -> {IMAGE_PATH}")

    image_bytes = IMAGE_PATH.read_bytes()

    print(f"=== FILTERED: {IMAGE_PATH.name} ===")
    filtered_runs = _run_batch(image_bytes, HAND, N, tag="filtered")

    print(f"\n=== UNFILTERED (re-run for apples-to-apples comparison under the CURRENT committed prompt): {UNFILTERED_IMAGE_PATH.name} ===")
    unfiltered_image_bytes = UNFILTERED_IMAGE_PATH.read_bytes()
    unfiltered_runs = _run_batch(unfiltered_image_bytes, HAND, N, tag="unfiltered")

    lines_out: list[str] = []
    lines_out.append("# FT_016 Evidence Probe -- vivid-cool-filtered image (S104 Step 5a follow-up)\n")
    lines_out.append(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines_out.append(f"**Image:** {IMAGE_PATH.relative_to(_REPO_ROOT)} (hand={HAND})  ")
    lines_out.append(f"**N:** {N}  ")
    lines_out.append(
        "**Scope:** measurement harness only. No production file modified. No "
        "commit follows this run. Pure evidence check -- decides nothing on its "
        "own. Reuses committed `describe_palm_image` / `extract_relations` / "
        "`map_contact` directly, none reimplemented.\n"
    )
    lines_out.append(
        "**Comparison-image note:** prior probes measured palm_right_test's "
        "Fate<->Heart contact under an EARLIER, pre-commit CONTACTS wording "
        "(mandatory position, not the final position-optional form Step 2 "
        "actually committed) -- not a clean match for \"does the CURRENT "
        "committed pipeline show this.\" Re-ran palm_right_test N=3 here, "
        "under the exact current committed prompt, for a valid apples-to-"
        "apples comparison (3 extra calls, noted per instruction).\n"
    )

    n_errors_filtered = sum(1 for r in filtered_runs if r is None)
    n_errors_unfiltered = sum(1 for r in unfiltered_runs if r is None)
    if n_errors_filtered or n_errors_unfiltered:
        lines_out.append(f"*Call errors:* filtered: {n_errors_filtered}/{N}, unfiltered: {n_errors_unfiltered}/{N}\n")

    # 1. Per-run full contacts dict (filtered image)
    lines_out.append("## 1. Per-run parsed `contacts` (filtered image)\n")
    for run_idx, r in enumerate(filtered_runs):
        lines_out.append(f"**Run {run_idx}:**")
        if r is None:
            lines_out.append("  ERROR -- call failed, see stderr log.\n")
            continue
        contacts = r["parsed"]["contacts"]
        if not contacts:
            lines_out.append("  (empty -- no CONTACTS line seen for any feature)\n")
        for feature, items in contacts.items():
            if not items:
                lines_out.append(f"  - {feature}: [] (declared-none or nothing valid parsed)")
            for item in items:
                lines_out.append(f"  - {feature} -> {item['target']!r} | verb={item['verb']!r} | position={item['position']!r} | clarity={item['clarity']!r}")
        lines_out.append("")

    # 2. FT_016 FOCUS
    lines_out.append("## 2. FT_016 FOCUS -- Fate<->Heart contacts (filtered image)\n")
    filtered_ft016_hits = 0
    filtered_meets_hits = 0
    for run_idx, r in enumerate(filtered_runs):
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
                filtered_meets_hits += 1
            if mapped["token"] is not None:
                filtered_ft016_hits += 1

        fate_block = _block_text(r["raw"], "Line of Fate")
        heart_block = _block_text(r["raw"], "Line of Heart")
        mount_mentioned = "Mount of Jupiter" in fate_block or "Mount of Jupiter" in heart_block
        lines_out.append(f"  Mount of Jupiter mentioned anywhere in Fate/Heart block text: {mount_mentioned}")
        lines_out.append("")

    lines_out.append(f"**Resolves to `meets` (FT_016's required token):** {filtered_meets_hits}/{N} runs")
    lines_out.append(f"**Any Fate<->Heart contact (any token) present:** {filtered_ft016_hits}/{N} runs\n")

    # 3. Direct comparison: unfiltered
    lines_out.append("## 3. Direct comparison -- unfiltered palm_right_test (re-run, current committed prompt)\n")
    unfiltered_ft016_hits = 0
    for run_idx, r in enumerate(unfiltered_runs):
        lines_out.append(f"**Run {run_idx}:**")
        if r is None:
            lines_out.append("  ERROR")
            continue
        fh = _fate_heart_contacts(r["parsed"]["contacts"])
        if not fh:
            lines_out.append("  (no Fate<->Heart contact in either direction)")
        else:
            for entry in fh:
                item, mapped = entry["item"], entry["mapped"]
                lines_out.append(
                    f"  - {entry['emitter']} -> {item['target']} | verb={item['verb']!r} | "
                    f"position={item['position']!r} | mapped_token={mapped['token']}"
                )
                if mapped["token"] is not None:
                    unfiltered_ft016_hits += 1

    if filtered_ft016_hits > 0 and unfiltered_ft016_hits > 0:
        comparison_verdict = "BOTH -- filtered and unfiltered both show a Fate<->Heart contact."
    elif filtered_ft016_hits > 0 and unfiltered_ft016_hits == 0:
        comparison_verdict = "FILTERED-ONLY -- the filtered image shows a contact the unfiltered image (under the current prompt) does not."
    elif filtered_ft016_hits == 0 and unfiltered_ft016_hits > 0:
        comparison_verdict = "UNFILTERED-ONLY -- unexpected; unfiltered shows a contact the filtered image does not."
    else:
        comparison_verdict = "NEITHER -- no Fate<->Heart contact detected on either image."
    lines_out.append(f"\n**Comparison verdict: {comparison_verdict}**\n")

    # 4. Faintness
    lines_out.append("## 4. Faintness self-report\n")
    for run_idx, r in enumerate(filtered_runs):
        if r is None:
            continue
        fate_faint = bool(re.search(r"not clearly visible|barely visible|\bfaint\b", _block_text(r["raw"], "Line of Fate"), re.I))
        fh = _fate_heart_contacts(r["parsed"]["contacts"])
        contact_clarities = [entry["item"]["clarity"] for entry in fh]
        lines_out.append(
            f"  - Run {run_idx}: Fate line self-reported faint (block text): {fate_faint}; "
            f"Fate<->Heart contact clarity field(s): {contact_clarities if contact_clarities else 'n/a (no contact)'}"
        )

    # 5. VERDICT
    lines_out.append("\n## 5. VERDICT\n")
    detected = filtered_ft016_hits > 0
    lines_out.append(f"**Fate<->Heart contact detected on the filtered image: {'YES' if detected else 'NO'}**, at {filtered_ft016_hits}/{N}.")
    if detected:
        tokens_seen = set()
        for r in filtered_runs:
            if r is None:
                continue
            for entry in _fate_heart_contacts(r["parsed"]["contacts"]):
                tokens_seen.add(entry["mapped"]["token"])
        lines_out.append(f"Mapped token(s) observed: {sorted(t for t in tokens_seen if t is not None)}")
        lines_out.append(
            "\n**PRODUCTION CAVEAT (restated explicitly):** this is filtered-image "
            "detection, not unfiltered-production detection. The vivid-cool filter "
            "is a deliberate, user-applied image transformation -- it is NOT what "
            "production receives from a real user's camera capture. A hit here is "
            "evidence the crossing CAN be seen under altered contrast/color "
            "conditions, not evidence that production's real input distribution "
            "will ever reliably surface it. Do not treat this as resolving FT_016's "
            "migration blocker on its own."
        )
    else:
        lines_out.append("No token to report -- the filtered image did not change the outcome in this sample.")

    report_text = "\n".join(lines_out) + "\n"
    REPORT_PATH.write_text(report_text, encoding="utf-8")

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s. Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
