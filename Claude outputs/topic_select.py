"""
Astro Agent -- Stage-1.5: TOPIC + SCOPE SEGMENT SELECTION.

The fine selection layer that sits on payload_builder's output, AFTER
filter_segments_by_domain. Mirrors that function's shape and its S124
fail-safe law exactly; the only differences are the tag artifact it reads
(topic + rule_type, not the 16 domains) and the time_scope gate.

DOCTRINE (design chat, S126):
  - The PLANNER speaks question-space only: `topics` (this module's closed
    vocab) + `time_scope` (already emitted). It NEVER emits a rule_type --
    rule_type is a property of the VERSE, resolved here in code.
  - rule_type is bucketed into three selection roles:
        machinery  -> dropped from EVERY answer (computation/narration/defn)
        timing     -> kept ONLY for a "when" question (future/specific_period)
        placement  -> kept for a "what/how" question
  - FAIL-SAFE (S124): a segment whose id is unknown to the tag artifact, or
    that carries no topic, is KEPT, never dropped. Only a segment POSITIVELY
    tagged off-topic, or machinery, or wrong-scope, is dropped. `counts`
    surfaces every disposition; `failsafe_untagged` is the tag-completeness
    meter and should trend to 0 as tagging completes.

This module NEVER mutates its input payload and NEVER calls an LLM.
Python 3.11.
"""
from __future__ import annotations

import json
import os
from typing import Optional

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOPIC_TAGS_PATH = os.path.join(REPO_ROOT, "data", "segment_topic_tags_bphs.json")

TOPIC_SELECT_VERSION = "topic-select-0.1"

# --- closed rule_type -> selection-bucket map (backstage; planner never sees it) ---
_MACHINERY = frozenset({"computation_method", "narrative", "definitional", "unusable"})
_TIMING = frozenset({"dasha_effect", "timing_event"})
# everything else authored is placement-class answer content
_TIMING_SCOPES = frozenset({"future", "specific_period"})


class TopicSelectError(Exception):
    """Raised only for an unreadable/malformed tag artifact -- never for a
    tagging gap, which fails safe."""


_TAGS_CACHE: dict[str, dict] = {}


def _load_topic_tags(path: str = TOPIC_TAGS_PATH) -> dict[str, dict]:
    """Return {segment_id: {"topics": [...], "rule_type": "..."}}.

    Accepts either a bare mapping or a {"segments":[{segment_id,...}]} doc,
    so it reads the same artifact shape as domain_tags_bphs.json.
    """
    if path in _TAGS_CACHE:
        return _TAGS_CACHE[path]
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except OSError as e:
        raise TopicSelectError(f"cannot read topic tags at {path}: {e}") from e
    except json.JSONDecodeError as e:
        raise TopicSelectError(f"topic tags at {path} are not valid JSON: {e}") from e
    if isinstance(raw, dict) and "segments" in raw:
        tags = {s["segment_id"]: {"topics": s.get("topics") or [],
                                  "rule_type": s.get("rule_type")}
                for s in raw["segments"]}
    elif isinstance(raw, dict):
        tags = raw
    else:
        raise TopicSelectError("topic tags artifact must be an object")
    _TAGS_CACHE[path] = tags
    return tags


def _bucket(rule_type: Optional[str]) -> str:
    if rule_type in _MACHINERY:
        return "machinery"
    if rule_type in _TIMING:
        return "timing"
    return "placement"


def filter_segments_by_topic_scope(
    payload: dict,
    topics: list[str],
    time_scope: str,
    *,
    tags_path: str = TOPIC_TAGS_PATH,
    tags: Optional[dict] = None,
) -> dict:
    """Return a NEW payload with `kept` narrowed to the planned topics and
    the question's time scope. Never mutates input; adds `topic_filter`
    stats and a per-segment `topic_filter` disposition for audit.

    An empty `topics` (e.g. a fallback plan with none) is a no-op, by the
    widen-when-unsure law -- do not narrow on an absent signal.
    """
    if not topics:
        return payload

    try:
        table = tags if tags is not None else _load_topic_tags(tags_path)
    except TopicSelectError:
        # A missing/unreadable tag artifact must NOT take down an answer:
        # fail open, keep the payload exactly as received.
        return payload

    want = set(topics)
    timing_q = time_scope in _TIMING_SCOPES

    counts = {"topic_match": 0, "failsafe_untagged": 0, "drop_topic_miss": 0,
              "drop_machinery": 0, "drop_scope_miss": 0, "already_dropped": 0}
    tokens_before = tokens_after = 0
    new_segments: list[dict] = []

    for seg in payload.get("segments", []):
        s = dict(seg)
        if not s.get("kept"):
            counts["already_dropped"] += 1
            new_segments.append(s)
            continue
        tokens_before += s.get("tokens", 0)

        entry = table.get(s["segment_id"])
        if entry is None or not entry.get("topics"):
            counts["failsafe_untagged"] += 1
            s["topic_filter"] = "failsafe_untagged"
        elif not (set(entry["topics"]) & want):
            s["kept"] = False
            s["topic_filter"] = "drop_topic_miss"
            counts["drop_topic_miss"] += 1
            new_segments.append(s)
            continue
        else:
            bucket = _bucket(entry.get("rule_type"))
            if bucket == "machinery":
                s["kept"] = False
                s["topic_filter"] = "drop_machinery"
                counts["drop_machinery"] += 1
                new_segments.append(s)
                continue
            if timing_q and bucket != "timing":
                s["kept"] = False
                s["topic_filter"] = "drop_scope_miss"
                counts["drop_scope_miss"] += 1
                new_segments.append(s)
                continue
            if (not timing_q) and bucket == "timing":
                s["kept"] = False
                s["topic_filter"] = "drop_scope_miss"
                counts["drop_scope_miss"] += 1
                new_segments.append(s)
                continue
            counts["topic_match"] += 1
            s["topic_filter"] = "topic_match"

        tokens_after += s.get("tokens", 0)
        new_segments.append(s)

    out = dict(payload)
    out["segments"] = new_segments
    out["topic_filter"] = {
        "topics": list(topics),
        "time_scope": time_scope,
        "counts": counts,
        "segment_tokens_before": tokens_before,
        "segment_tokens_after": tokens_after,
        "segment_cut_pct": (round(100 * (1 - tokens_after / tokens_before), 2)
                            if tokens_before else 0.0),
        "topic_select_version": TOPIC_SELECT_VERSION,
    }
    return out
