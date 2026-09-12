"""
diagnostics/validate_step5b_live_dormancy_S109.py

S109 live dormancy check (authorized budget: N=1 per hand, 2 gpt-4o vision
calls total -- do NOT exceed).

Runs the CURRENT HEAD vision path against the two standing test hand
images, THEN calls agent.interpretive.palm_reading.
_assemble_relational_targets_with_fallback with a REAL OpenAI client
(never a stub) -- since every live verb has resolved deterministically
across S105/S107's prior sweeps, the expectation is the S109 fallback
makes ZERO synonym-resolution LLM calls (dormant): every contact should
resolve via contact_mapper alone (possibly via S106 inflection), never
needing contact_llm_fallback's own resolve_unresolved_contacts LLM call.

This script itself makes NO additional LLM call beyond the 2 vision
calls -- the fallback assembly step either makes 0 calls (dormant, the
expected/most-likely outcome) or up to 1 call (if something genuinely
needs rescuing, which is itself the "new signal" this check is designed
to surface, not silently pass or fail on).

MEASUREMENT HARNESS ONLY -- no production file is imported for mutation.
Report goes to diagnostics/latest_run.md (written by the caller, not this
script -- this script prints to stdout and writes a raw JSON dump).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from openai import OpenAI  # noqa: E402

from agent.interpretive import observation_extractor, palm_rules_table  # noqa: E402
from agent.interpretive.palm_reading import _assemble_relational_targets_with_fallback  # noqa: E402
from agent.palm_processor import describe_palm_image  # noqa: E402

LEFT_IMAGE = _REPO_ROOT / "data" / "test_images" / "palm_left_test.jpg"
RIGHT_IMAGE = _REPO_ROOT / "data" / "test_images" / "palm_right_test.jpg"

OUT_PATH = _REPO_ROOT / "diagnostics" / "validate_step5b_live_dormancy_S109_raw.json"


class _CountingClient:
    """Wraps a real OpenAI client, counting every completions.create call
    -- lets us observe exactly how many (if any) LLM calls the S109
    fallback makes, without guessing from log lines."""

    def __init__(self, real_client):
        self._real = real_client
        self.call_count = 0
        self.chat = self
        self.completions = self

    def create(self, **kwargs):
        self.call_count += 1
        return self._real.chat.completions.create(**kwargs)


def main() -> None:
    real_client = OpenAI()
    left_bytes = LEFT_IMAGE.read_bytes()
    right_bytes = RIGHT_IMAGE.read_bytes()

    print("Calling vision for LEFT hand (1 call)...")
    left_raw = describe_palm_image(left_bytes, "left", temperature=0.0)
    print("Calling vision for RIGHT hand (1 call)...")
    right_raw = describe_palm_image(right_bytes, "right", temperature=0.0)

    left_rel = observation_extractor.extract_relations(left_raw)
    right_rel = observation_extractor.extract_relations(right_raw)

    counting_client = _CountingClient(real_client)
    left_ct, right_ct, audits = _assemble_relational_targets_with_fallback(
        left_rel["contacts"], right_rel["contacts"], counting_client
    )

    rules = palm_rules_table.load_rule_set()
    from agent.interpretive.observation_extractor import merge_relational_targets
    targets = merge_relational_targets(left_ct, right_ct)
    fired = sorted(r.rule_id for r in palm_rules_table.match({}, {}, rules, targets=targets))

    head_life_left = [c for c in left_rel["contacts"].get("Line of Head", []) if c.get("target") == "Line of Life"]
    head_life_right = [c for c in right_rel["contacts"].get("Line of Head", []) if c.get("target") == "Line of Life"]

    result = {
        "left_head_life_contacts": head_life_left,
        "right_head_life_contacts": head_life_right,
        "left_ct": {k: {a: (sorted(v) if isinstance(v, set) else v) for a, v in attrs.items()} for k, attrs in left_ct.items()},
        "right_ct": {k: {a: (sorted(v) if isinstance(v, set) else v) for a, v in attrs.items()} for k, attrs in right_ct.items()},
        "fired_rule_ids": fired,
        "h028_fired": "H_028" in fired,
        "fallback_llm_call_count": counting_client.call_count,
        "audits": audits,
        "left_raw_text": left_raw,
        "right_raw_text": right_raw,
    }

    OUT_PATH.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

    print("\n--- Head->Life contacts ---")
    print("LEFT:", head_life_left)
    print("RIGHT:", head_life_right)
    print("\n--- Fallback LLM call count (expect 0 = dormant) ---")
    print(counting_client.call_count)
    print("\n--- Audits ---")
    print(audits)
    print("\n--- Fired rule ids ---")
    print(fired)
    print("\nH_028 fired:", "H_028" in fired)
    print(f"\nRaw dump written to: {OUT_PATH}")


if __name__ == "__main__":
    main()
