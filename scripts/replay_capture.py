"""
Replay a Q&A capture through the CURRENT code, with ZERO API cost.

WHY THIS EXISTS
---------------
A live dogfood run costs roughly $0.19 and ~75 seconds per question, and it
needs Sulabh at a keyboard. Most of what a run verifies is DOWNSTREAM of the
model call -- the silence gate, the advisory planet reader, `answer_view`, the
capture itself. None of that needs a fresh model call to test: the capture
already stores the interpreter's RAW response, and the payload rebuilds
deterministically from the `unit_ids` + `chart_facts` it also stores.

So this replays a saved run against whatever the code does today:

    payload rebuild -> [stored raw response] -> silence gate -> advisory reader
                    -> answer_view -> report

and prints what CHANGED versus what was captured. A gate, renderer, adapter or
capture edit is validated against real gpt-5 output for free.

This is the astrology-side form of a law the project already holds for palm
(CLAUDE.md S123): "Compare fired sets across a CODE change on a FIXED captured
fixture, never across two live vision calls."

WHAT IT CANNOT DO
-----------------
It cannot tell you how the model would respond DIFFERENTLY. Anything that
changes what the model sees or is told needs a real run:
  1. the interpreter prompt changed (voice, contract, output shape);
  2. the fact block gained a class of fact the model has never seen;
  3. the model or its config changed;
  4. you are ratifying something as done.
Everything else replays.

USAGE
    python -m scripts.replay_capture <capture.md> [--json]
    python -m scripts.replay_capture --latest

Python 3.11.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

CAPTURE_DIR = REPO_ROOT / "diagnostics" / "qa_capture"
REPLAY_VERSION = "replay-1.0"


class ReplayError(Exception):
    """The capture could not be parsed or replayed. Names the turn and field."""


# ---------------------------------------------------------------- parsing
# The capture is markdown written by agent/astro/qa_capture.py. These patterns
# read it back. They are deliberately anchored on that file's own section
# headings, so a heading rename breaks parsing LOUDLY here rather than silently
# producing an empty replay.
_TURN_SPLIT = re.compile(r"^## TURN ", re.M)
_SECTION = r"### {}\n```(?:json)?\n(.*?)\n```"


def _section(body: str, heading: str, turn: int, *, required: bool = True) -> Optional[str]:
    m = re.search(_SECTION.format(re.escape(heading)), body, re.S)
    if m:
        return m.group(1)
    if required:
        raise ReplayError(f"turn {turn}: no '### {heading}' section -- capture "
                          f"format changed, or this turn failed before that stage")
    return None


def _json_section(body: str, heading: str, turn: int, *, required: bool = True):
    raw = _section(body, heading, turn, required=required)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ReplayError(f"turn {turn}: '{heading}' is not valid JSON: {e}") from e


@dataclass
class CapturedTurn:
    """One turn, as the capture recorded it."""
    index: int
    question: str
    chart_facts: dict
    unit_ids: list[str]
    interpreter_raw: str
    captured_kept: list[dict] = field(default_factory=list)
    captured_dropped: list[dict] = field(default_factory=list)
    captured_stats: dict = field(default_factory=dict)
    captured_user_answer: Optional[str] = None
    # Which heading the text above came from. Captures written before S129's
    # qa_capture fix stored the PIPELINE's internal render under a heading that
    # claimed it was what the user saw. Comparing today's answer_view output
    # against that would report a difference on every single turn, for no
    # reason. So the source is recorded and only a true answer_view capture is
    # compared.
    user_answer_source: Optional[str] = None
    failed: bool = False


def parse_capture(path: Path) -> list[CapturedTurn]:
    """Every replayable turn in a capture file, in order.

    A turn with no stored raw response (a capability-gate refusal, or a run
    that crashed) is skipped -- it never reached the interpreter, so there is
    nothing downstream to replay.
    """
    text = path.read_text(encoding="utf-8")
    chunks = _TURN_SPLIT.split(text)[1:]          # [0] is the file header
    turns: list[CapturedTurn] = []
    for i, chunk in enumerate(chunks, 1):
        if chunk.lstrip().startswith(("--", "20")) and "-- FAILED" in chunk.split("\n")[0]:
            continue
        raw = _section(chunk, "interpreter raw response", i, required=False)
        if not raw or not raw.strip():
            continue
        facts = _json_section(chunk, "chart_facts", i)
        sel = _json_section(chunk, "selection + payload (Stages 2-3)", i)
        gate = _json_section(chunk, "silence gate (Stage 5a)", i, required=False) or {}
        q = _section(chunk, "question", i)
        ua = _section(chunk, "what the user actually saw (answer_view)", i, required=False)
        ua_src = "answer_view" if ua is not None else None
        if ua is None:
            # Pre-S129 capture: the heading existed but held the pipeline's own
            # render, not the user-facing one.
            ua = _section(chunk, "rendered answer (what the user saw)", i, required=False)
            ua_src = "legacy_pipeline_render" if ua is not None else None
        unit_ids = (sel or {}).get("unit_ids") or []
        if not unit_ids:
            raise ReplayError(
                f"turn {i}: no unit_ids recorded, so the payload cannot be "
                f"rebuilt. Captures written before that field existed are not "
                f"replayable.")
        turns.append(CapturedTurn(
            index=i, question=(q or "").strip(), chart_facts=facts or {},
            unit_ids=list(unit_ids), interpreter_raw=raw,
            captured_kept=gate.get("kept_claims") or [],
            captured_dropped=gate.get("dropped_claims") or [],
            captured_stats=gate.get("stats") or {},
            captured_user_answer=ua, user_answer_source=ua_src,
        ))
    return turns


# ---------------------------------------------------------------- replay
def replay_turn(turn: CapturedTurn) -> dict:
    """Run one captured turn through today's downstream code. No API call."""
    from agent.astro import payload_builder, interpreter as interp_mod
    from agent.astro import silence_gate, answer_view

    try:
        payload = payload_builder.build_payload(turn.chart_facts, unit_ids=turn.unit_ids)
    except Exception as e:
        raise ReplayError(f"turn {turn.index}: payload rebuild failed "
                          f"({type(e).__name__}: {e})") from e

    # The stored raw response stands in for the model. Same seam the tests use,
    # so the replay exercises the REAL interpret() -- ghost guard included.
    def _stub(system, user, **kwargs):
        return turn.interpreter_raw, {"replayed": True}

    interp = interp_mod.interpret(turn.question, "", payload, llm=_stub)
    gate = silence_gate.apply_silence_gate(interp, payload, turn.chart_facts)

    result = {
        "kept_claims": gate.kept_claims,
        "dropped_claims": gate.dropped_claims,
        "silent_on": gate.silent_on,
        "declined": [],
        "answer": "",
        "ghost_citations": interp["ghost_citations"],
        "gate_stats": gate.stats,
    }
    user_answer = answer_view.render_user_answer(result)

    return {
        "index": turn.index,
        "question": turn.question,
        "ghost_citations": interp["ghost_citations"],
        "kept": gate.kept_claims,
        "dropped": gate.dropped_claims,
        "stats": gate.stats,
        "gate_error": gate.error,
        "user_answer": user_answer,
        "payload_segments_kept": sum(1 for s in payload.get("segments", []) if s.get("kept")),
    }


def _statements(claims) -> list[str]:
    return [str(c.get("statement", "")) for c in (claims or [])]


def diff_turn(turn: CapturedTurn, now: dict) -> list[str]:
    """Human-readable differences between the capture and today's code."""
    out: list[str] = []
    was_k, now_k = _statements(turn.captured_kept), _statements(now["kept"])
    if was_k != now_k:
        out.append(f"KEPT CLAIMS CHANGED: {len(was_k)} -> {len(now_k)}")
        for s in set(was_k) - set(now_k):
            out.append(f"    no longer kept: {s[:100]}")
        for s in set(now_k) - set(was_k):
            out.append(f"    newly kept:     {s[:100]}")

    was_d, now_d = _statements(turn.captured_dropped), _statements(now["dropped"])
    if was_d != now_d:
        out.append(f"DROPPED CLAIMS CHANGED: {len(was_d)} -> {len(now_d)}")
        for s in set(now_d) - set(was_d):
            out.append(f"    newly dropped:  {s[:100]}")

    for key in ("applicable", "not_applicable", "undetermined", "ungated_pct"):
        a, b = turn.captured_stats.get(key), now["stats"].get(key)
        if a != b:
            out.append(f"stat {key}: {a} -> {b}")

    new_keys = sorted(set(now["stats"]) - set(turn.captured_stats))
    if new_keys:
        out.append(f"NEW stats keys: {', '.join(k for k in new_keys if k != 'advisory_detail')}")

    if turn.user_answer_source == "answer_view":
        if (turn.captured_user_answer or "").strip() != now["user_answer"].strip():
            out.append("USER-FACING ANSWER CHANGED (see --json for both)")
    elif turn.user_answer_source == "legacy_pipeline_render":
        out.append("user answer NOT COMPARED: this capture predates the "
                   "answer_view split and stored the pipeline's internal render")
    return out


def replay_file(path: Path) -> dict:
    turns = parse_capture(path)
    results, diffs = [], {}
    for t in turns:
        now = replay_turn(t)
        results.append(now)
        d = diff_turn(t, now)
        if d:
            diffs[t.index] = d
    return {"capture": str(path), "replay_version": REPLAY_VERSION,
            "turns_replayed": len(results), "results": results, "diffs": diffs}


def _advisory_rollup(results: list[dict]) -> dict:
    """The promotion metric, aggregated over real claims.

    `advisory_would_drop_a_kept_claim` is what decides whether the planet
    reader may be promoted from advisory to enforcing. Every non-zero entry
    needs a HUMAN to say whether that drop would have been correct -- this
    function only counts them, it never judges.
    """
    roll = {"claims": 0, "advisory_applicable": 0, "advisory_not_applicable": 0,
            "advisory_undetermined": 0, "would_drop_a_kept_claim": 0,
            "disagreements": []}
    for r in results:
        st = r.get("stats") or {}
        for k in ("advisory_applicable", "advisory_not_applicable", "advisory_undetermined"):
            roll[k] += st.get(k, 0)
        roll["would_drop_a_kept_claim"] += st.get("advisory_would_drop_a_kept_claim", 0)
        for d in st.get("advisory_detail") or []:
            roll["claims"] += 1
            if d.get("advisory_verdict") == "not_applicable":
                roll["disagreements"].append(
                    {"turn": r["index"], "statement": d.get("statement"),
                     "advisory_reason": d.get("reason"),
                     "enforced_verdict": d.get("enforced_verdict")})
    return roll


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("capture", nargs="?", help="path to a qa_capture markdown file")
    ap.add_argument("--latest", action="store_true", help="use the newest capture")
    ap.add_argument("--json", action="store_true", help="dump the full result as JSON")
    a = ap.parse_args(argv)

    if a.latest or not a.capture:
        files = sorted(CAPTURE_DIR.glob("*.md"))
        if not files:
            print(f"no captures in {CAPTURE_DIR}", file=sys.stderr)
            return 2
        path = files[-1]
    else:
        path = Path(a.capture)
    if not path.exists():
        print(f"no such capture: {path}", file=sys.stderr)
        return 2

    try:
        out = replay_file(path)
    except ReplayError as e:
        print(f"REPLAY FAILED: {e}", file=sys.stderr)
        return 1

    if a.json:
        print(json.dumps(out, indent=2, default=str))
        return 0

    print(f"# Replay of {path.name}  ({out['replay_version']}, no API calls)")
    print(f"turns replayed: {out['turns_replayed']}\n")
    for r in out["results"]:
        print(f"-- turn {r['index']}: {r['question'][:70]}")
        print(f"   kept {len(r['kept'])} | dropped {len(r['dropped'])} | "
              f"ghosts {len(r['ghost_citations'])} | segments {r['payload_segments_kept']}")
        if r["gate_error"]:
            print(f"   GATE ERROR: {r['gate_error']}")
    print("\n## Differences vs the capture")
    if not out["diffs"]:
        print("  none -- today's code reproduces the captured run exactly.")
    for idx, lines in out["diffs"].items():
        print(f"  turn {idx}:")
        for line in lines:
            print(f"    {line}")

    roll = _advisory_rollup(out["results"])
    print("\n## Advisory planet reader, on REAL claims")
    print(f"  claims seen            : {roll['claims']}")
    print(f"  advisory applicable    : {roll['advisory_applicable']}")
    print(f"  advisory not-applicable: {roll['advisory_not_applicable']}")
    print(f"  advisory undetermined  : {roll['advisory_undetermined']}")
    print(f"  WOULD DROP A KEPT CLAIM: {roll['would_drop_a_kept_claim']}"
          "   <- promotion metric; every one needs a human ruling")
    for d in roll["disagreements"]:
        print(f"    turn {d['turn']}: {str(d['statement'])[:90]}")
        print(f"      advisory says: {d['advisory_reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
