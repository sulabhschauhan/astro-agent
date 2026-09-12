"""
diagnostics/s120_live_palm_run.py

ONE live end-to-end palmistry run on data/test_images/palm_right_test.jpg,
as a front-end user would get it. Deterministic rules ON (runtime toggle,
not a file edit). Exactly ONE intentional vision call; the reading path's
own internal calls are whatever it makes.

Paid-call discipline: an explicit OpenAI() client is constructed once and
passed in. client=None is never used. Everything is dumped to
s120_live_palm_run_raw.json so the report can be written without re-running.
"""
from __future__ import annotations

import json
import pathlib
import sys

# Run as `python diagnostics/s120_live_palm_run.py` from the repo root:
# that puts diagnostics/ on sys.path, not the root, so add the root.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from openai import OpenAI

from agent import palm_processor
from agent.interpretive import palm_reading, capture_net, capture_net_digest

IMAGE = pathlib.Path("data/test_images/palm_right_test.jpg")
OUT = pathlib.Path("diagnostics/s120_live_palm_run_raw.json")


def _rows_now() -> list[dict]:
    p = capture_net._CAPTURE_NET_PATH
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def main() -> None:
    client = OpenAI()  # ONE explicit client, reused

    rows_before = _rows_now()

    image_bytes = IMAGE.read_bytes()
    # THE one intentional vision call. temperature=0, no loop, no retry.
    description = palm_processor.describe_palm_image(image_bytes, "right")

    # Runtime toggle only -- no file edit.
    palm_reading._DETERMINISTIC_RULES_ENABLED = True

    result = palm_reading.generate_palm_reading(
        palm_left=None,
        palm_right=description,
        client=client,
    )

    rows_after = _rows_now()
    new_rows = rows_after[len(rows_before):]

    digest = capture_net_digest.build_digest()
    digest_md = capture_net_digest.render_markdown(digest)

    engine = result.stage1_feature_diagnostics.get("_rules_engine", {})

    decline_features = palm_reading._compute_decline_features(
        result.supported_features,
        result.unsupported_features,
        (),
        result.claims,
    )

    payload = {
        "image": str(IMAGE),
        "hand": "right",
        "vision_description_raw": description,
        "reading_text": result.reading_text,
        "reading_text_tagged": result.reading_text_tagged,
        "model": result.model,
        "retry_used": result.retry_used,
        "stage2_retry_used": getattr(result, "stage2_retry_used", None),
        "stage2_first_attempt_failures": list(
            getattr(result, "stage2_first_attempt_failures", ()) or ()
        ),
        "validation_passed": result.validation.passed,
        "validation_failures": list(result.validation.failures),
        "validation_warnings": list(getattr(result.validation, "warnings", ()) or ()),
        "supported_features": list(result.supported_features),
        "unsupported_features": list(result.unsupported_features),
        "decline_features": list(decline_features),
        "claims": [
            {
                "claim_id": c.claim_id,
                "feature": c.feature,
                "chunk_id": c.chunk_id,
                "claim_text": c.claim_text,
                "valence": c.valence,
                "condition_text": c.condition_text,
                "observation_basis": c.observation_basis,
                "excluded_from_voice": c.excluded_from_voice,
                "exclusion_reason": c.exclusion_reason,
            }
            for c in result.claims
        ],
        "sources": [dict(s) for s in result.sources],
        "rules_engine": engine,
        "capture_rows_before": len(rows_before),
        "capture_rows_after": len(rows_after),
        "capture_new_rows": new_rows,
        "digest": digest,
        "digest_markdown": digest_md,
    }

    OUT.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(f"WROTE {OUT}")
    print(f"validation.passed = {result.validation.passed}")
    print(f"failures          = {list(result.validation.failures)}")
    print(f"fired             = {engine.get('fired_rule_ids')}")
    print(f"surviving         = {engine.get('surviving_rule_ids')}")
    print(f"claims            = {[c.claim_id for c in result.claims]}")
    print(f"capture rows new  = {len(new_rows)}")
    print(f"reading chars     = {len(result.reading_text)}")


if __name__ == "__main__":
    main()
