"""
agent/interpretive/capture_net.py

Failure-capture net (Astro Agent Task A): an append-only JSONL sink for
AI-decision events that need a durable, human-reviewable record beyond a
WARNING log line. NOT wired into any caller in this task -- deciding who
calls record()/map_fallback_audits() and when is a separate, later task.

Two public entry points:
  record(trigger, producer, payload, reading_id) -- generic, one event.
  map_fallback_audits(audits, reading_id) -- palm_reading/S109-specific,
    maps each fallback_audits[i]['disposition'] onto a trigger category
    per _DISPOSITION_TO_TRIGGER and calls record() for every mapped one.
    An unmapped disposition (currently: already_resolved_no_llm_needed,
    the purely-deterministic re-resolution case) is silently ignored --
    a clean run writes nothing.

Trigger map (disposition -> trigger):
  llm_unclear, position_unresolved            -> silence
      (LLM had nothing usable to resolve the verb/position to)
  hallucination                               -> wrong_source
      (LLM's canonical choice was outside the closed vocabulary)
  batch_call_failed, batch_malformed_response -> instability
      (the LLM call or its response parsing broke, not a judgment issue)
  resolved                                    -> ai_decision
      (LLM successfully picked a canonical verb, deterministic mapper
      confirmed a token -- logged as a ratified AI decision, not a
      failure; included per explicit user approval, see instructing
      prompt)

FAIL-SAFE CONTRACT: every write is wrapped try/except. A capture-net
failure (unwritable path, disk full, permissions) NEVER raises out of
this module -- it logs a WARNING and returns. A reading must never break
because its own audit trail couldn't be written.

NO PALM TEXT/IMAGE BYTES: only a fixed, small set of keys is ever copied
from a payload into a record (see _PAYLOAD_KEYS) -- raw palm descriptions
or image data are never among them, so they cannot leak by construction,
not by post-hoc filtering.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Module-level so tests can monkeypatch it to redirect writes into tmp_path
# instead of the real diagnostics dir.
_CAPTURE_NET_PATH = Path("diagnostics/capture_net/failures.jsonl")

_DISPOSITION_TO_TRIGGER = {
    "llm_unclear": "silence",
    "position_unresolved": "silence",
    "hallucination": "wrong_source",
    "batch_call_failed": "instability",
    "batch_malformed_response": "instability",
    "resolved": "ai_decision",
}

# Fixed allow-list of payload keys ever copied into a record -- this is
# the mechanism that keeps palm text/image bytes out, not a blocklist.
_PAYLOAD_KEYS = (
    "hand", "feature", "raw_verb", "llm_canonical_choice",
    "final_token", "disposition",
)


def record(trigger: str, producer: str, payload: dict, reading_id: str) -> None:
    """Appends one JSON line to the capture-net file. Never raises --
    any failure degrades to a WARNING log and a silent return."""
    try:
        _CAPTURE_NET_PATH.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "reading_id": reading_id,
            "trigger": trigger,
            "producer": producer,
        }
        for key in _PAYLOAD_KEYS:
            if key in payload:
                entry[key] = payload[key]
        with _CAPTURE_NET_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as exc:  # noqa: BLE001 -- must never break a reading
        logger.warning(
            "capture_net.record: failed to write capture-net entry "
            "(trigger=%r producer=%r reading_id=%r): %s: %s",
            trigger, producer, reading_id, type(exc).__name__, exc,
        )


def map_fallback_audits(audits: list[dict], reading_id: str) -> None:
    """Maps palm_reading S109 fallback_audits records onto capture-net
    events via _DISPOSITION_TO_TRIGGER. An audit whose disposition isn't
    in the map is ignored -- a clean run writes nothing."""
    for audit in audits:
        trigger = _DISPOSITION_TO_TRIGGER.get(audit.get("disposition"))
        if trigger is None:
            continue
        record(trigger, "palm_reading_fallback", audit, reading_id)
