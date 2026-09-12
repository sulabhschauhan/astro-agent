"""
diagnostics/s117_live_confirmation_run.py

ONE-SHOT live confirmation that commit 3a3d625 (support-gate jurisdiction
fix) resolves the M_023/Upper-Mars voicing drop on a REAL photo -- the same
hand (David_right.jpeg) that surfaced the bug at Step 6.

NOT imported by the pipeline, NOT wired anywhere. Run once, output captured
to diagnostics/s117_live_confirmation_raw.json for evidence, findings
written to diagnostics/latest_run.md by hand after inspecting the output.

Exactly ONE palm_processor.describe_palm_image() call (the vision
description call this task is scoped to). No loop, no retry, no hand-
crafted DEVELOPMENT text -- whatever the vision model returns is what goes
into generate_palm_reading(), unedited.
"""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # repo root, for `agent.*` imports

from openai import OpenAI

from agent.interpretive import palm_reading
from agent.palm_processor import describe_palm_image

_IMAGE_PATH = Path(__file__).parent.parent / "data" / "test_images" / "David_right.jpeg"
_OUT_PATH = Path(__file__).parent / "s117_live_confirmation_raw.json"


def main() -> None:
    image_bytes = _IMAGE_PATH.read_bytes()

    # ONE real client instance, used explicitly everywhere -- client=None
    # is never passed anywhere in this script (Step-5 accidental-paid-call
    # lesson).
    client = OpenAI()

    # ── Exactly ONE vision description call ────────────────────────────
    palm_right_description = describe_palm_image(image_bytes, "right")

    # ── Production entry point, runtime toggle only ────────────────────
    original_flag = palm_reading._DETERMINISTIC_RULES_ENABLED
    palm_reading._DETERMINISTIC_RULES_ENABLED = True
    try:
        result = palm_reading.generate_palm_reading(
            palm_left=None, palm_right=palm_right_description, client=client,
        )
    finally:
        palm_reading._DETERMINISTIC_RULES_ENABLED = original_flag

    engine_diag = result.stage1_feature_diagnostics.get("_rules_engine", {})

    output = {
        "image": str(_IMAGE_PATH),
        "palm_right_description_raw": palm_right_description,
        "fired_rule_ids": engine_diag.get("fired_rule_ids"),
        "surviving_rule_ids": engine_diag.get("surviving_rule_ids"),
        "suppression_log": engine_diag.get("suppression_log"),
        "dropped_rule_ids": engine_diag.get("dropped_rule_ids"),
        "observation": engine_diag.get("observation"),
        "mount_development": engine_diag.get("mount_development"),
        "citations": engine_diag.get("citations"),
        "claims": [dataclasses.asdict(c) for c in result.claims],
        "validation_passed": result.validation.passed,
        "validation_failures": list(result.validation.failures),
        "supported_features": list(result.supported_features),
        "unsupported_features": list(result.unsupported_features),
        "reading_text_tagged": result.reading_text_tagged,
        "reading_text": result.reading_text,
        "sources": list(result.sources),
        "stage2_retry_used": result.stage2_retry_used,
        "stage2_first_attempt_failures": list(result.stage2_first_attempt_failures),
        "retry_used": result.retry_used,
    }

    _OUT_PATH.write_text(json.dumps(output, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {_OUT_PATH}")
    print("fired_rule_ids:", output["fired_rule_ids"])
    print("surviving_rule_ids:", output["surviving_rule_ids"])
    print("validation_passed:", output["validation_passed"])
    print("unsupported_features:", output["unsupported_features"])


if __name__ == "__main__":
    main()
