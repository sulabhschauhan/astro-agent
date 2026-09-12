"""
diagnostics/s125_absence_regression_check.py

S125 STEP 3 regression check -- runs OLD vs NEW _is_absence() classification
across every captured raw vision text this repo has, per feature, per hand,
reporting any flip. Read-only: does not import the live (edited) module in a
way that mutates it, just calls _is_absence with two different phrase tuples
(OLD verbatim, NEW = OLD + "absent") to isolate the effect of exactly one
addition.

Files scanned (every raw capture named in the S125 task):
  diagnostics/s120_live_palm_run_raw.json
  diagnostics/slope_magnitude_stress_run_1.json .. _5.json
  diagnostics/s124_sulabh_e2e_raw.json
  diagnostics/s124_david_e2e_raw.json
  diagnostics/s124_athira_e2e_raw.json

Not a test -- a one-off diagnostic run, output captured to
diagnostics/s125_absence_regression_check_raw.json and summarized in
diagnostics/latest_run.md.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from agent.interpretive import palm_reading

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

_OLD_PHRASES = (
    "not clearly visible", "no clear marks", "unremarkable",
    "not observed", "not visible", "none",
)
_NEW_PHRASES = _OLD_PHRASES + ("absent",)


def _compile(phrases):
    return tuple(re.compile(re.escape(p), re.IGNORECASE) for p in phrases)


_OLD_COMPILED = _compile(_OLD_PHRASES)
_NEW_COMPILED = _compile(_NEW_PHRASES)


def _is_absence_with(compiled_tier1, text, feature):
    if any(p.search(text) for p in compiled_tier1):
        return True
    if feature is not None:
        pattern = palm_reading._ABSENCE_PATTERNS_BY_FEATURE.get(feature)
        if pattern is not None and pattern.search(text):
            return True
    return False


FILES = [
    "diagnostics/s120_live_palm_run_raw.json",
    "diagnostics/slope_magnitude_stress_run_1.json",
    "diagnostics/slope_magnitude_stress_run_2.json",
    "diagnostics/slope_magnitude_stress_run_3.json",
    "diagnostics/slope_magnitude_stress_run_4.json",
    "diagnostics/slope_magnitude_stress_run_5.json",
    "diagnostics/s124_sulabh_e2e_raw.json",
    "diagnostics/s124_david_e2e_raw.json",
    "diagnostics/s124_athira_e2e_raw.json",
]


def _raw_texts_for_file(path: pathlib.Path) -> list[tuple[str, str, str]]:
    """Returns [(hand_label, feature, field_text), ...] for one capture file."""
    d = json.loads(path.read_text(encoding="utf-8"))
    out = []

    def _add_block(hand_label, block_text):
        if not block_text:
            return
        fields = palm_reading._parse_fields(block_text)
        for label, text in fields.items():
            feature = label.strip().lower()
            out.append((hand_label, feature, text))

    if "vision_description_raw" in d:
        _add_block(f"{path.name}::{d.get('hand', 'unknown')}", d["vision_description_raw"])
    else:
        _add_block(f"{path.name}::left", d.get("vision_description_left_raw"))
        _add_block(f"{path.name}::right", d.get("vision_description_right_raw"))

    return out


def main() -> None:
    all_rows = []
    flips = []
    for rel in FILES:
        path = REPO_ROOT / rel
        for hand_label, feature, text in _raw_texts_for_file(path):
            # Map raw field labels (e.g. "fate line", "development (venus)")
            # onto the _FEATURE_REGISTRY names _is_absence's tier-2 lookup
            # actually keys on, where obvious; else feature=None (tier-1 only,
            # matching how _is_absence(text) is called with no feature arg
            # in the one pre-F-B call site still in use).
            reg_feature = feature if feature in palm_reading._FEATURE_REGISTRY else None

            old = _is_absence_with(_OLD_COMPILED, text, reg_feature)
            new = _is_absence_with(_NEW_COMPILED, text, reg_feature)
            row = {
                "file": hand_label,
                "feature_label": feature,
                "registry_feature": reg_feature,
                "text": text,
                "old": old,
                "new": new,
            }
            all_rows.append(row)
            if old != new:
                flips.append(row)

    out = {
        "total_fields_checked": len(all_rows),
        "flip_count": len(flips),
        "flips": flips,
        "all_rows": all_rows,
    }
    out_path = REPO_ROOT / "diagnostics" / "s125_absence_regression_check_raw.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"total fields checked: {len(all_rows)}")
    print(f"flips: {len(flips)}")
    for row in flips:
        print(f"  FLIP file={row['file']!r} feature_label={row['feature_label']!r} "
              f"registry_feature={row['registry_feature']!r} old={row['old']} new={row['new']} "
              f"text={row['text']!r}")
    print(f"WROTE {out_path}")


if __name__ == "__main__":
    main()
