"""
diagnostics/s124_live_e2e_read_run.py

S124 PROBE ONLY -- live end-to-end palm reading run on the three standing
test palms, exactly as a user session would receive it (deterministic rule
engine ON via the documented runtime toggle -- CLAUDE.md's PALM_RULES_ENGINE
override / palm_reading._DETERMINISTIC_RULES_ENABLED, not a file edit).

Three test subjects (per data/test_images/, matching the precedent scripts'
own naming -- s120/S117/validate_step5b_*):
  1. sulabh  -- palm_left_test.jpg + palm_right_test.jpg (two-hand reading)
  2. david   -- David_right.jpeg only (single-hand reading, no palm_left)
  3. athira  -- "Athira Palm Left.jpeg" + "Athira Palm Right.jpeg" (two-hand)

N=1 per subject. Exactly the vision calls each reading needs (2 for a
two-hand subject, 1 for david) -- no loop, no re-sampling. Run-to-run
variance is NOT re-opened here (CLAUDE.md S123 ruling, out of scope).

Paid-call discipline: one explicit OpenAI() client, constructed once,
reused for every vision + Stage-1 + Stage-2 call across all three subjects.
Full capture dumped to per-subject raw JSON files so the report can be
written without re-running.
"""
from __future__ import annotations

import dataclasses
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from openai import OpenAI

from agent import palm_processor
from agent.interpretive import palm_reading, capture_net, capture_net_digest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
IMG_DIR = REPO_ROOT / "data" / "test_images"

SUBJECTS = [
    {
        "name": "sulabh",
        "left": IMG_DIR / "palm_left_test.jpg",
        "right": IMG_DIR / "palm_right_test.jpg",
    },
    {
        "name": "david",
        "left": None,
        "right": IMG_DIR / "David_right.jpeg",
    },
    {
        "name": "athira",
        "left": IMG_DIR / "Athira Palm Left.jpeg",
        "right": IMG_DIR / "Athira Palm Right.jpeg",
    },
]


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


def _claim_dict(c) -> dict:
    citation = c.citation
    citation_dict = dataclasses.asdict(citation)
    citation_dict["_kind"] = type(citation).__name__
    return {
        "claim_id": c.claim_id,
        "feature": c.feature,
        "chunk_id": c.chunk_id,
        "claim_text": c.claim_text,
        "valence": c.valence,
        "condition_text": c.condition_text,
        "observation_basis": c.observation_basis,
        "excluded_from_voice": c.excluded_from_voice,
        "exclusion_reason": c.exclusion_reason,
        "citation_ref": c.citation_ref,
        "citation": citation_dict,
    }


def run_one(subject: dict, client: OpenAI) -> dict:
    name = subject["name"]
    print(f"=== {name} ===", flush=True)

    rows_before = _rows_now()

    left_desc = None
    if subject["left"] is not None:
        left_bytes = subject["left"].read_bytes()
        left_desc = palm_processor.describe_palm_image(left_bytes, "left")
        print(f"{name}: LEFT vision call done ({len(left_desc)} chars)", flush=True)

    right_desc = None
    if subject["right"] is not None:
        right_bytes = subject["right"].read_bytes()
        right_desc = palm_processor.describe_palm_image(right_bytes, "right")
        print(f"{name}: RIGHT vision call done ({len(right_desc)} chars)", flush=True)

    # Runtime toggle only -- no file edit -- the documented A/B mechanism.
    palm_reading._DETERMINISTIC_RULES_ENABLED = True

    result = palm_reading.generate_palm_reading(
        palm_left=left_desc,
        palm_right=right_desc,
        hand_detail=None,
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
        "subject": name,
        "left_image": str(subject["left"]) if subject["left"] else None,
        "right_image": str(subject["right"]) if subject["right"] else None,
        "vision_description_left_raw": left_desc,
        "vision_description_right_raw": right_desc,
        "reading_text": result.reading_text,
        "reading_text_tagged": result.reading_text_tagged,
        "model": result.model,
        "retry_used": result.retry_used,
        "stage2_retry_used": getattr(result, "stage2_retry_used", None),
        "stage2_first_attempt_failures": list(
            getattr(result, "stage2_first_attempt_failures", ()) or ()
        ),
        "stage1_retry_features": list(getattr(result, "stage1_retry_features", ()) or ()),
        "validation_passed": result.validation.passed,
        "validation_failures": list(result.validation.failures),
        "validation_warnings": list(getattr(result.validation, "warnings", ()) or ()),
        "supported_features": list(result.supported_features),
        "unsupported_features": list(result.unsupported_features),
        "decline_features": list(decline_features),
        "claims": [_claim_dict(c) for c in result.claims],
        "sources": [dict(s) for s in result.sources],
        "rules_engine": engine,
        "stage1_feature_diagnostics": result.stage1_feature_diagnostics,
        "capture_rows_before": len(rows_before),
        "capture_rows_after": len(rows_after),
        "capture_new_rows": new_rows,
        "digest": digest,
        "digest_markdown": digest_md,
    }

    out_path = pathlib.Path(f"diagnostics/s124_{name}_e2e_raw.json")
    out_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(f"WROTE {out_path}")
    print(f"validation.passed = {result.validation.passed}")
    print(f"failures          = {list(result.validation.failures)}")
    print(f"fired             = {engine.get('fired_rule_ids')}")
    print(f"surviving         = {engine.get('surviving_rule_ids')}")
    print(f"claims            = {[c.claim_id for c in result.claims]}")
    print(f"sources           = {len(result.sources)}")
    print(f"capture rows new  = {len(new_rows)}")
    print(f"reading chars     = {len(result.reading_text)}")
    print()
    return payload


def main() -> None:
    client = OpenAI()  # ONE explicit client, reused across all 3 subjects
    results = {}
    for subject in SUBJECTS:
        results[subject["name"]] = run_one(subject, client)
    print("ALL DONE:", list(results.keys()))


if __name__ == "__main__":
    main()
