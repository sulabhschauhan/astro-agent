"""Classify the advisory planet reader's would-drops from a QA capture.

DECISION THIS SERVES: if every would-drop is a CORRECT_CATCH then the planet
reader may be promoted to enforcing; if any is UNCAUGHT_LORDSHIP or
DEFINITIONAL then it must stay advisory until that class is handled.

WHY THIS EXISTS. `advisory_would_drop_a_kept_claim` is an integer and is not
self-interpreting. Measured on the BPHS corpus (S130, zero API cost) with the
gate's own readers:

  - 289 planet-shaped sentences vs 160 lord-shaped; 94.1% of the planet-shaped
    ones are NOT_APPLICABLE for any one chart, so a NON-ZERO metric is the
    EXPECTED result, not an alarm.
  - 9 planet-shaped sentences carry a lordship clause worded so that
    `_CONDITION_RE` misses it ("Saturn or Mercury ruling the 5th is in the
    12th", "his dispositor is conjunct", plus OCR-mangled ordinals). The
    ambiguity rule fires only when `_CONDITION_RE` ALSO matches, so these are
    judged as PLAIN planet claims on HALF their real condition. They do NOT
    fail safe -- 8 of the 9 would be dropped.
  - A second class the sweep surfaced: DEFINITIONAL sentences that state no
    precondition at all ("Jupiter and Mercury have Digbala in the ascendant").

Read-only. Makes no API call. Never raises on a malformed capture -- it
reports what it could not parse and exits non-zero.

Usage:
    python scripts/classify_advisory_drops.py diagnostics/qa_capture/<UTC>.md
    python scripts/classify_advisory_drops.py <capture> --json

Python 3.11.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CORRECT_CATCH = "CORRECT_CATCH"
UNCAUGHT_LORDSHIP = "UNCAUGHT_LORDSHIP"
DEFINITIONAL = "DEFINITIONAL"
UNCLASSIFIED = "UNCLASSIFIED"

# Lordship expressed WITHOUT the literal "<Nth> lord" that silence_gate's
# _CONDITION_RE requires -- so the ambiguity rule never fires on it.
_UNCAUGHT_LORDSHIP_RE = re.compile(
    r"\b(ruling|rules|ruler of|lord of the|owning|owner of|is the lord|"
    r"dispositor|occupies its own)\b", re.IGNORECASE)

# Doctrinal definitions, not preconditions about this chart. Dropping one is a
# WRONG drop: the sentence never claimed the placement holds for the native.
_DEFINITIONAL_RE = re.compile(
    r"\b(digbala|dig bala|directional strength|acquires? this strength|"
    r"gains? strength|is said to be strong|avastha|exalt(?:ed|ation) in|"
    r"debilitat(?:ed|ion) in|own sign|moolatrikona)\b", re.IGNORECASE)


class CaptureError(Exception):
    """The capture could not be read in the shape this script needs."""


def _json_blocks(text: str, heading: str) -> list[dict]:
    """Every ```json block that follows `heading`, one per turn."""
    out: list[dict] = []
    for chunk in text.split(heading)[1:]:
        try:
            body = chunk.split("```json", 1)[1].split("```", 1)[0]
            out.append(json.loads(body))
        except (IndexError, ValueError) as e:
            raise CaptureError(f"unreadable block after {heading!r}: {e}") from e
    return out


def classify(statement: str) -> tuple[str, str]:
    """One would-drop -> (class, why). Order matters: lordship before
    definitional, because a sentence can read as both and the lordship half is
    the one that makes the verdict unsound."""
    s = statement or ""
    if _UNCAUGHT_LORDSHIP_RE.search(s):
        return UNCAUGHT_LORDSHIP, ("carries a lordship clause the ambiguity "
                                   "rule does not see; judged on half its condition")
    if _DEFINITIONAL_RE.search(s):
        return DEFINITIONAL, ("states doctrine, not a precondition about this "
                              "chart; a drop here is a WRONG drop")
    return CORRECT_CATCH, ("plain planet-in-house precondition that is false "
                           "for this chart")


def collect(capture_path: Path) -> dict:
    try:
        text = capture_path.read_text(encoding="utf-8")
    except OSError as e:
        raise CaptureError(f"cannot read {capture_path}: {e}") from e

    gates = _json_blocks(text, "### silence gate (Stage 5a)")
    if not gates:
        raise CaptureError("no '### silence gate (Stage 5a)' section found -- "
                           "is this a qa_capture file?")

    turns, totals = [], {CORRECT_CATCH: 0, UNCAUGHT_LORDSHIP: 0,
                         DEFINITIONAL: 0, UNCLASSIFIED: 0}
    metric_total = judged_total = 0

    for i, gate in enumerate(gates, 1):
        stats = gate.get("stats") or {}
        detail = stats.get("advisory_detail")
        if detail is None:
            turns.append({"turn": i, "error": "no advisory_detail -- capture "
                                              "predates the S129b planet reader"})
            continue
        metric = stats.get("advisory_would_drop_a_kept_claim", 0)
        judged = (stats.get("advisory_applicable", 0)
                  + stats.get("advisory_not_applicable", 0))
        metric_total += metric
        judged_total += judged

        rows = []
        for a in detail:
            if (a.get("advisory_verdict") != "not_applicable"
                    or a.get("enforced_verdict") == "not_applicable"):
                continue  # not a would-drop
            cls, why = classify(a.get("statement", ""))
            totals[cls] += 1
            rows.append({"class": cls, "why": why,
                         "statement": a.get("statement", ""),
                         "reader_reason": a.get("reason", "")})
        turns.append({"turn": i, "metric": metric, "planet_claims_judged": judged,
                      "would_drops": rows})

    promote = (metric_total > 0 and totals[UNCAUGHT_LORDSHIP] == 0
               and totals[DEFINITIONAL] == 0 and totals[UNCLASSIFIED] == 0)
    if judged_total == 0:
        verdict = ("INCONCLUSIVE -- the planet reader never fired. The metric's "
                   "zero is an ABSENCE OF EVIDENCE. Re-run with questions that "
                   "elicit planet-shaped claims.")
    elif metric_total == 0:
        verdict = (f"HOLD -- the reader fired on {judged_total} claims and "
                   "disagreed with the enforcing gate ZERO times. A real zero, "
                   "not a vacuous one -- but promotion grants DROP authority and "
                   "no drop event was observed, so the behaviour promotion "
                   "actually changes remains unmeasured.")
    elif promote:
        verdict = ("PROMOTE is supported -- every would-drop is a correct "
                   "precondition catch. Still a human call.")
    else:
        verdict = ("HOLD -- at least one would-drop is a wrong-drop class. "
                   "Promotion would silence a true claim.")

    return {"capture": str(capture_path), "turns": turns, "totals": totals,
            "metric_total": metric_total, "planet_claims_judged": judged_total,
            "verdict": verdict}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("capture", type=Path)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    try:
        out = collect(args.capture)
    except CaptureError as e:
        print(f"CLASSIFY FAILED: {e}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(out, indent=2))
        return 0

    print(f"capture: {out['capture']}")
    print(f"planet claims actually judged: {out['planet_claims_judged']}")
    print(f"advisory_would_drop_a_kept_claim (all turns): {out['metric_total']}\n")
    for t in out["turns"]:
        if "error" in t:
            print(f"turn {t['turn']}: {t['error']}")
            continue
        print(f"turn {t['turn']}: metric={t['metric']} judged={t['planet_claims_judged']}")
        for r in t["would_drops"]:
            print(f"   [{r['class']}] {r['statement'][:96]}")
            print(f"        {r['why']}")
    print("\ntotals: " + ", ".join(f"{k}={v}" for k, v in out["totals"].items()))
    print(f"\nVERDICT: {out['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
