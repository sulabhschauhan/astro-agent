"""
agent/interpretive/capture_net.py

Failure-capture net (Astro Agent Task A): an append-only JSONL sink for
AI-decision events that need a durable, human-reviewable record beyond a
WARNING log line. NOT wired into any caller in this task -- deciding who
calls record()/map_fallback_audits() and when is a separate, later task.

Two public entry points:
  record(trigger, producer, payload, reading_id) -- generic, one event.
  record_dropped_rules(dropped_rule_ids, reading_id) -- S119 Step 4; one
    wrong_source event per rule that fired, survived resolve_priority,
    and then failed to produce a citable claim. DORMANT BY CONSTRUCTION
    since S119 Step 2: rules now cite themselves, so nothing can be
    dropped for citation reasons and the input list is always empty. It
    exists so that if a future change ever reintroduces a drop, the
    regression lands in this durable sink instead of scrolling past in
    stdout.
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
    # S119 Step 4: rule-claim citation failures. `rule_id` is an opaque
    # identifier ("FT_003"); `source_page` is an integer page number.
    # NEITHER carries book prose. `source_quote` is DELIBERATELY ABSENT
    # and must stay absent -- the allow-list is what keeps 19th-century
    # text out of this sink by construction, exactly as it keeps palm
    # descriptions out, and the quote is the one rule-citation field that
    # is book text.
    "rule_id", "source_page",
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


# TRIGGER CHOICE (S119 Step 4), stated rather than assumed: a rule that
# fired and survived but cannot produce a citation is a WRONG_SOURCE-class
# event -- its citation identity is broken, which is the same failure
# class as the existing "hallucination" disposition (a choice outside the
# closed vocabulary). It maps onto the existing enum cleanly, so NO new
# trigger category was invented; capture_net_digest.py's _KNOWN_TRIGGERS
# (derived from _DISPOSITION_TO_TRIGGER.values()) already contains it and
# needs no edit.
_DROPPED_RULE_DISPOSITION = "dropped_rule_no_citation"


def record_dropped_rules(dropped_rule_ids: list[str], reading_id: str) -> None:
    """One wrong_source event per dropped rule id. An empty list -- the
    only state that can occur since S119 Step 2 -- writes nothing, so a
    clean run stays silent exactly like map_fallback_audits' clean run.

    Never raises: `record` is already fail-safe, and a non-list input
    degrades to no-op rather than propagating."""
    try:
        for rule_id in dropped_rule_ids or ():
            record(
                "wrong_source",
                "palm_reading_rules_engine",
                {"rule_id": rule_id, "disposition": _DROPPED_RULE_DISPOSITION},
                reading_id,
            )
    except Exception as exc:  # noqa: BLE001 -- must never break a reading
        logger.warning(
            "capture_net.record_dropped_rules: failed to record dropped "
            "rules (reading_id=%r): %s: %s",
            reading_id, type(exc).__name__, exc,
        )
