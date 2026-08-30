"""
agent/interpretive/capture_net_digest.py

Read-only summarizer for the capture-net JSONL log (agent/interpretive/
capture_net.py). NEVER writes to, moves, or truncates the log -- every
function here only READS the file (or a digest already built from it).

NO automated verdicts, NO contradiction detection: this surfaces counts
and the ai_decision lane (every AI-fired token with no human check) only.
A human reads the rendered digest and decides -- this module is that
review's INPUT, never a substitute for it.

Two public entry points:
  build_digest(since=None, until=None) -> dict
  render_markdown(digest) -> str

Plus a read-only CLI (--since/--until, prints render_markdown to stdout;
never writes anything).
"""

from __future__ import annotations

import argparse
import json
import logging

from agent.interpretive import capture_net

logger = logging.getLogger(__name__)

# Derived from capture_net's own disposition->trigger map, never a
# separately hand-maintained copy -- single source of truth for the
# trigger vocabulary (silence/wrong_source/instability/ai_decision).
_KNOWN_TRIGGERS = sorted(set(capture_net._DISPOSITION_TO_TRIGGER.values()))


def _read_rows() -> list[dict]:
    """Read-only, fail-safe parse of the capture-net JSONL. Missing file
    or any read failure -> []. A malformed individual line is skipped
    (logged at WARNING) -- never fatal to the rest of the read."""
    path = capture_net._CAPTURE_NET_PATH
    try:
        if not path.exists():
            return []
        text = path.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001 -- a digest failure must never crash the caller
        logger.warning(
            "capture_net_digest: failed to read %s (%s: %s) -- returning empty digest.",
            path, type(exc).__name__, exc,
        )
        return []

    rows: list[dict] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            logger.warning(
                "capture_net_digest: skipping malformed line %d in %s (%s)",
                line_no, path, exc,
            )
    return rows


def build_digest(since: str | None = None, until: str | None = None) -> dict:
    """Counts-only digest over the capture-net log, optionally filtered
    to rows whose ts falls in [since, until] (inclusive). Comparison is
    plain string comparison -- since/until must use the same ISO-8601
    shape/offset as capture_net.record's own ts (e.g.
    "2026-08-28T13:08:56.096708+00:00"), since that shape sorts
    lexicographically the same as chronologically.

    NO verdicts, NO contradiction detection -- counts + the raw
    ai_decision rows only; a human reads and decides."""
    rows = _read_rows()
    if since is not None:
        rows = [r for r in rows if r.get("ts", "") >= since]
    if until is not None:
        rows = [r for r in rows if r.get("ts", "") <= until]

    counts_by_trigger: dict[str, int] = {t: 0 for t in _KNOWN_TRIGGERS}
    counts_by_trigger_x_feature: dict[str, dict[str, int]] = {t: {} for t in _KNOWN_TRIGGERS}
    counts_by_disposition: dict[str, int] = {}
    ai_decision_rows: list[dict] = []

    for row in rows:
        trigger = row.get("trigger", "unknown")
        counts_by_trigger[trigger] = counts_by_trigger.get(trigger, 0) + 1

        feature = row.get("feature", "unknown")
        by_feature = counts_by_trigger_x_feature.setdefault(trigger, {})
        by_feature[feature] = by_feature.get(feature, 0) + 1

        disposition = row.get("disposition", "unknown")
        counts_by_disposition[disposition] = counts_by_disposition.get(disposition, 0) + 1

        if trigger == "ai_decision":
            ai_decision_rows.append(row)

    ts_values = [r["ts"] for r in rows if "ts" in r]
    date_range_seen = {"min_ts": min(ts_values), "max_ts": max(ts_values)} if ts_values else None

    return {
        "total_rows": len(rows),
        "date_range_seen": date_range_seen,
        "counts_by_trigger": counts_by_trigger,
        "counts_by_trigger_x_feature": counts_by_trigger_x_feature,
        "counts_by_disposition": counts_by_disposition,
        "ai_decision_rows": ai_decision_rows,
    }


def render_markdown(digest: dict) -> str:
    """Plain markdown digest, suitable to paste into a monthly review.
    Never raises on an empty digest."""
    lines: list[str] = ["# Capture-Net Digest", ""]

    total = digest.get("total_rows", 0)
    date_range = digest.get("date_range_seen")
    if date_range:
        lines.append(f"**{total} row(s)**, {date_range['min_ts']} to {date_range['max_ts']}.")
    else:
        lines.append(f"**{total} row(s)** -- no rows in range.")
    lines.append("")

    lines.append("## Counts by trigger")
    lines.append("")
    lines.append("| trigger | count |")
    lines.append("|---|---|")
    for trigger, count in digest.get("counts_by_trigger", {}).items():
        lines.append(f"| {trigger} | {count} |")
    lines.append("")

    lines.append("## Counts by trigger x feature")
    lines.append("")
    lines.append("| trigger | feature | count |")
    lines.append("|---|---|---|")
    for trigger, by_feature in digest.get("counts_by_trigger_x_feature", {}).items():
        for feature, count in sorted(by_feature.items()):
            lines.append(f"| {trigger} | {feature} | {count} |")
    lines.append("")

    lines.append("## AI decisions to review")
    lines.append("")
    ai_rows = digest.get("ai_decision_rows", [])
    if not ai_rows:
        lines.append("None in range.")
    else:
        for row in ai_rows:
            raw_verb = row.get("raw_verb", "?")
            choice = row.get("llm_canonical_choice", "?")
            token = row.get("final_token", "?")
            hand = row.get("hand", "?")
            feature = row.get("feature", "?")
            lines.append(f"- `{raw_verb}` -> `{choice}` -> `{token}` ({hand}/{feature})")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Read-only capture-net digest -- prints to stdout, never writes to the log."
    )
    parser.add_argument("--since", default=None, help="ISO ts lower bound, inclusive")
    parser.add_argument("--until", default=None, help="ISO ts upper bound, inclusive")
    args = parser.parse_args()
    print(render_markdown(build_digest(since=args.since, until=args.until)))
