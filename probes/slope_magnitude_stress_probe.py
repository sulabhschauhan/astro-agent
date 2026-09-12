"""
probes/slope_magnitude_stress_probe.py

END-TO-END PRODUCTION STRESS TEST for the S123 arc (HEAD = 5098e90): vision
now asks SLOPE MAGNITUDE on Head/Heart/Fate, extract_flat_subfields reads
it, _merge_flat_subfields writes it policy-aware into observation, and
H_026 requires Slope_Magnitude=slight. No real vision call has ever been
made with the new field present before this probe.

PROBE ONLY -- no agent/, data/, or tests/ file is edited by this script.
Runs the FULL production path (palm_processor.describe_palm_image ->
palm_reading.generate_palm_reading) exactly as a user session would, N=5
times, on the SAME image the diagnostics/s120_live_palm_run_raw.json
baseline used (data/test_images/palm_right_test.jpg, hand=right), so the
new runs are directly comparable to that known baseline. Deterministic
rules ON via the same runtime toggle diagnostics/s120_live_palm_run.py
used (no file edit).

magnitudes (the confidence dict `palm_rules_table.match()` consumes) is
NOT exposed anywhere in the diagnostics channel `_prepare_claims_from_
rules` returns -- it is a purely local variable in that function. Rather
than reconstruct it independently (which would require a SECOND LLM
extraction call per run, diverging from what the real run actually used),
this probe captures the REAL magnitudes dict via a transient in-process
monkeypatch of `palm_rules_table.match` -- wraps the real function to
record its (observation, magnitudes, targets) arguments before calling
straight through unmodified. This changes nothing about the pipeline's
behavior or output; it only observes an argument that was already being
passed. No file on disk is touched by this.

Paid-call discipline (same posture as diagnostics/s120_live_palm_run.py):
one explicit OpenAI() client, constructed once, reused across all 5 runs.
Each run makes its own real vision call (temperature=0, no loop) plus
whatever the reading path's own Stage 2 voicing needs -- no artificial
retry loop added by this script.

Writes one JSON file per run to diagnostics/slope_magnitude_stress_run_N.json
(N=1..5), so diagnostics/latest_run.md's report can be written without
re-running.
"""
from __future__ import annotations

import json
import pathlib
import sys

# Run as `python probes/slope_magnitude_stress_probe.py` from the repo
# root: that puts probes/ on sys.path, not the root, so add the root.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from openai import OpenAI

from agent import palm_processor
from agent.interpretive import palm_reading, observation_extractor
import agent.interpretive.palm_rules_table as palm_rules_table

IMAGE = pathlib.Path("data/test_images/palm_right_test.jpg")
OUT_DIR = pathlib.Path("diagnostics")
N_RUNS = 5

# ─── transient magnitudes capture (see module docstring) ─────────────────

_real_match = palm_rules_table.match
_captured: dict = {}


def _capturing_match(observation, magnitudes, rules, targets=None):
    _captured["observation_at_match"] = observation
    _captured["magnitudes"] = magnitudes
    _captured["targets_at_match"] = targets
    return _real_match(observation, magnitudes, rules, targets=targets)


palm_rules_table.match = _capturing_match


def run_once(client: OpenAI, run_index: int) -> dict:
    _captured.clear()

    image_bytes = IMAGE.read_bytes()
    # THE one intentional vision call per run. temperature=0, no loop, no retry.
    description = palm_processor.describe_palm_image(image_bytes, "right")

    # Runtime toggle only -- no file edit, matches diagnostics/s120_live_palm_run.py.
    palm_reading._DETERMINISTIC_RULES_ENABLED = True

    # Independently capture the SAME intermediate parses the pipeline
    # itself computes internally (read-only, mirrors prepare_palm_reading's
    # own calls exactly -- does not alter its behavior since these are the
    # same pure functions called a second time on the same input text).
    parsed_fields = palm_reading._parse_fields(description)
    relations = observation_extractor.extract_relations(description)
    flat_subfields = observation_extractor.extract_flat_subfields(description)

    result = palm_reading.generate_palm_reading(
        palm_left=None,
        palm_right=description,
        client=client,
    )

    engine = dict(result.stage1_feature_diagnostics.get("_rules_engine", {}))
    engine["magnitudes_captured_at_match"] = _captured.get("magnitudes")

    decline_features = palm_reading._compute_decline_features(
        result.supported_features,
        result.unsupported_features,
        (),
        result.claims,
    )

    payload = {
        "run_index": run_index,
        "image": str(IMAGE),
        "hand": "right",
        "model": result.model,
        "vision_description_raw": description,
        "parsed_fields": dict(parsed_fields),
        "relations": relations,
        "flat_subfields": flat_subfields,
        "rules_engine": engine,
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
        "supported_features": list(result.supported_features),
        "unsupported_features": list(result.unsupported_features),
        "decline_features": list(decline_features),
        "validation_passed": result.validation.passed,
        "validation_failures": list(result.validation.failures),
        "validation_warnings": list(getattr(result.validation, "warnings", ()) or ()),
        "retry_used": result.retry_used,
        "stage2_retry_used": getattr(result, "stage2_retry_used", None),
        "stage2_first_attempt_failures": list(
            getattr(result, "stage2_first_attempt_failures", ()) or ()
        ),
        "reading_text": result.reading_text,
        "reading_text_tagged": result.reading_text_tagged,
    }
    return payload


def main() -> None:
    client = OpenAI()  # ONE explicit client, reused across all 5 runs
    try:
        for i in range(1, N_RUNS + 1):
            payload = run_once(client, i)
            out_path = OUT_DIR / f"slope_magnitude_stress_run_{i}.json"
            out_path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False, default=str),
                encoding="utf-8",
            )
            engine = payload["rules_engine"]
            print(f"RUN {i}: WROTE {out_path}")
            print(f"  fired     = {engine.get('fired_rule_ids')}")
            print(f"  surviving = {engine.get('surviving_rule_ids')}")
            print(f"  suppression_log = {engine.get('suppression_log')}")
            print(f"  claims    = {len(payload['claims'])}")
            print(f"  declines  = {len(payload['decline_features'])}")
            print(f"  validation_passed = {payload['validation_passed']}")
    finally:
        palm_rules_table.match = _real_match  # restore, good hygiene


if __name__ == "__main__":
    main()
