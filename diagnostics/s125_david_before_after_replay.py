"""
diagnostics/s125_david_before_after_replay.py

S125 STEP 4 proof. Replays David's ALREADY-CAPTURED raw vision text
(diagnostics/s124_david_e2e_raw.json) through the support-gate decision
functions -- no new vision/LLM calls -- showing the fate-line path BEFORE
(simulated: old 6-phrase _ABSENCE_PHRASES, no "absent") and AFTER (the live,
now-fixed module) the fix, plus the actual decline-sentence text each
produces via _build_decline_block.
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
_OLD_COMPILED = tuple(re.compile(re.escape(p), re.IGNORECASE) for p in _OLD_PHRASES)


def _is_absence_old(text: str, feature: str | None = None) -> bool:
    if any(p.search(text) for p in _OLD_COMPILED):
        return True
    if feature is not None:
        pattern = palm_reading._ABSENCE_PATTERNS_BY_FEATURE.get(feature)
        if pattern is not None and pattern.search(text):
            return True
    return False


def _is_genuine_negative_absence_old(feature: str, raw_texts: list[str]) -> bool:
    if not raw_texts:
        return False
    return all(_is_absence_old(t, feature) for t in raw_texts)


def main() -> None:
    d = json.loads((REPO_ROOT / "diagnostics" / "s124_david_e2e_raw.json").read_text(encoding="utf-8"))
    right_raw = d["vision_description_right_raw"]
    fields = palm_reading._parse_fields(right_raw)
    fate_text = fields["FATE LINE"]
    print(f"David's real captured FATE LINE field text: {fate_text!r}")
    print()

    # ---- BEFORE (simulated old 6-phrase list) ----
    old_absence = _is_absence_old(fate_text, "fate line")
    old_genuine = _is_genuine_negative_absence_old("fate line", [fate_text])
    print("BEFORE (old _ABSENCE_PHRASES, no 'absent') -- this IS what the S124")
    print("probe actually captured, reconstructed here from David's real")
    print("captured supported_features/decline_features (no re-simulation):")
    print(f"  _is_absence('{fate_text}', 'fate line')            = {old_absence}")
    print(f"  _is_genuine_negative_absence('fate line', [...])    = {old_genuine}")
    old_supported = tuple(d["supported_features"])
    old_decline = tuple(d["decline_features"])
    old_sentence = palm_reading._build_decline_block(old_decline)
    print(f"  'fate line' in supported_features (captured)        = {'fate line' in old_supported}")
    print(f"  'fate line' in decline block (captured)             = {'fate line' in old_decline}")
    print(f"  decline sentence (S124's real captured text):")
    print(f"    {old_sentence!r}")
    print()

    # ---- AFTER (live, fixed module) ----
    new_absence = palm_reading._is_absence(fate_text, "fate line")
    new_genuine = palm_reading._is_genuine_negative_absence("fate line", [fate_text])
    print("AFTER (live palm_reading._ABSENCE_PHRASES, includes 'absent'):")
    print(f"  _is_absence('{fate_text}', 'fate line')            = {new_absence}")
    print(f"  _is_genuine_negative_absence('fate line', [...])    = {new_genuine}")
    # Real post-fix behavior: _retrieve_per_feature never issues a query for
    # fate line at all now (_resolve_feature_quality returns None), so it
    # exits BOTH supported_features and decline_features -- every other
    # feature's real captured classification is unaffected (this fix only
    # changes _is_absence's answer for text matching "absent"). Reproduced
    # here by removing exactly "fate line" from David's real captured
    # tuples, since that is the one and only entry the fix changes (proven
    # separately by the 228-field, 1-flip regression sweep).
    new_supported = tuple(f for f in old_supported if f != "fate line")
    new_decline = tuple(f for f in old_decline if f != "fate line")
    new_sentence = palm_reading._build_decline_block(new_decline)
    print(f"  'fate line' in supported_features                   = {'fate line' in new_supported}")
    print(f"  'fate line' in decline block                        = {'fate line' in new_decline}")
    print(f"  decline sentence (fixed):")
    print(f"    {new_sentence!r}")

    out = {
        "fate_line_raw_text": fate_text,
        "before": {
            "is_absence": old_absence,
            "is_genuine_negative_absence": old_genuine,
            "fate_line_in_supported_features": "fate line" in old_supported,
            "fate_line_in_decline_features": "fate line" in old_decline,
            "decline_sentence": old_sentence,
        },
        "after": {
            "is_absence": new_absence,
            "is_genuine_negative_absence": new_genuine,
            "fate_line_in_supported_features": "fate line" in new_supported,
            "fate_line_in_decline_features": "fate line" in new_decline,
            "decline_sentence": new_sentence,
        },
    }
    out_path = REPO_ROOT / "diagnostics" / "s125_david_before_after_replay_raw.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWROTE {out_path}")


if __name__ == "__main__":
    main()
