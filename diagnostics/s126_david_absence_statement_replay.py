"""S126 (this task's own session): replay David's captured fate-line
"absent" text through _apply_support_gate/_build_decline_block/
_build_absence_block at current HEAD, showing the decline block and the
NEW absence block, full text, no LLM call -- same replay-not-regenerate
pattern diagnostics/s125_david_before_after_replay.py already used for the
S125 fix. Writes diagnostics/s126_david_absence_statement_replay_raw.json.
"""
import json
import sys

sys.path.insert(0, ".")
from agent.interpretive import palm_reading as pr  # noqa: E402

RAW = json.load(open("diagnostics/s124_david_e2e_raw.json", encoding="utf-8"))

left = pr._parse_fields(RAW.get("vision_description_left_raw") or "")
right = pr._parse_fields(RAW.get("vision_description_right_raw") or "")
hd = {}

raw_texts_by_feature = pr._gather_feature_texts(left, right, hd)

# per_feature_results empty everywhere (no retrieval run in this replay --
# consistent with every feature having zero surviving chunks, which is the
# relevant state for fate line either way since its text is absence-only).
per_feature_results: dict[str, list[dict]] = {}

gated, supported, unsupported, absent = pr._apply_support_gate(
    per_feature_results, raw_texts_by_feature
)

decline_features = pr._compute_decline_features(
    supported, unsupported, (), ()
)
decline_block = pr._build_decline_block(decline_features)
absence_block = pr._build_absence_block(absent)

result = {
    "fate_line_raw_texts": raw_texts_by_feature.get("fate line"),
    "fate_line_in_supported": "fate line" in supported,
    "fate_line_in_unsupported": "fate line" in unsupported,
    "fate_line_in_absent_features": "fate line" in absent,
    "absent_features": list(absent),
    "decline_features": list(decline_features),
    "decline_block_AFTER": decline_block,
    "absence_block_AFTER": absence_block,
    # BEFORE this task's change: no absent_features concept existed at
    # all -- the feature was simply invisible everywhere (S125 state,
    # already shipped at this session's HEAD before this task's edits).
    "absence_block_BEFORE": "(did not exist -- feature was silent, no sentence anywhere)",
}

print(json.dumps(result, indent=2, ensure_ascii=False))

with open("diagnostics/s126_david_absence_statement_replay_raw.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
