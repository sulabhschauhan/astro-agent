"""
Astro Agent -- Q&A DOGFOOD CAPTURE.

PATH B. The astrology-side counterpart to frontend/app.py's palm-only
`_capture_dogfood_run()`, which never covered the chart question path.

WHAT THIS IS FOR
----------------
Every design-chat analysis of a live run so far has been done by hand-copying
the on-screen answer and then REBUILDING the payload offline to find out what
the interpreter was actually looking at. That reconstruction is where the
mistakes come from: an S129 review called a Raja Yoga citation (`ch34_s011`)
a mis-citation twice, on both occasions because the reviewer read a truncated
prefix of a 5,396-character segment instead of the whole thing. The verse was
there, ~1,800 characters in.

So this file's first duty is not metrics. It is: **write down the exact text
the model was given, in full, next to the claims it produced from that text.**
Everything else here is secondary.

FILE PER LAUNCH, NOT ONE OVERWRITTEN FILE
-----------------------------------------
`diagnostics/qa_capture/<launch-utc>.md`, appended per turn. A fresh Streamlit
process starts a new file; turns within one session accumulate in it. Rule 26
exists because overwrite-only destroyed run evidence twice; a per-launch file
keeps that protection without growing without bound. The directory is
gitignored -- these contain a real person's chart.

FAILURE POSTURE: NEVER BREAK THE ANSWER
---------------------------------------
Capture is diagnostics. Every public function swallows its own exceptions and
logs at WARNING. A disk-full or permission error must never cost the user
their answer. This is the one place in the pipeline where fail-open is
unambiguously right.

Python 3.11.
"""
from __future__ import annotations

import datetime
import json
import logging
import os
import textwrap
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

__all__ = ["QA_CAPTURE_VERSION", "capture_enabled", "session_path", "capture_turn"]

# 1.1 (S137): Stage 5b composer section added ahead of the first live composed
# run. See `_composer_block` for why a silent stage needs its own record.
QA_CAPTURE_VERSION = "qa-capture-1.2"

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CAPTURE_DIR = _REPO_ROOT / "diagnostics" / "qa_capture"

# Set ASTRO_QA_CAPTURE=0 to turn it off. ON by default: the whole point is that
# a run nobody remembered to instrument is a run we cannot review.
_DISABLED_VALUES = {"0", "false", "no", "off"}

# One path per process. Streamlit re-executes the script on every interaction,
# but the module object persists for the life of the process, so this stays put
# for the whole session and turns append to one file.
_SESSION_PATH: Optional[Path] = None


def capture_enabled() -> bool:
    return os.environ.get("ASTRO_QA_CAPTURE", "1").strip().lower() not in _DISABLED_VALUES


def session_path() -> Optional[Path]:
    """Path for this process's capture file, creating the directory on first use.

    Returns None when capture is disabled or the directory cannot be created.
    """
    global _SESSION_PATH
    if not capture_enabled():
        return None
    if _SESSION_PATH is not None:
        return _SESSION_PATH
    try:
        _CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        _SESSION_PATH = _CAPTURE_DIR / f"{stamp}.md"
        if not _SESSION_PATH.exists():
            _SESSION_PATH.write_text(
                f"# Astro Agent Q&A capture -- session {stamp}\n\n"
                f"{QA_CAPTURE_VERSION}. One block per question, appended.\n"
                "Contains a real chart; gitignored, do not commit.\n\n",
                encoding="utf-8",
            )
        return _SESSION_PATH
    except OSError as e:
        logger.warning("qa_capture: could not open a capture file: %s", e)
        return None


# ---------------------------------------------------------------- formatting

def _fence(body: str, lang: str = "") -> str:
    return f"```{lang}\n{body.rstrip()}\n```"


def _json_block(obj: Any) -> str:
    try:
        return _fence(json.dumps(obj, indent=2, default=str, ensure_ascii=False), "json")
    except (TypeError, ValueError) as e:
        return _fence(f"<unserialisable: {type(e).__name__}: {e}>")


def _plan_block(plan) -> str:
    if plan is None:
        return "_no plan (refused before planning)_"
    fields = ("domains", "houses", "whose_chart", "time_scope", "in_scope",
              "source", "planner_fallback", "validation_errors", "reasoning")
    return _json_block({f: getattr(plan, f, None) for f in fields})


def _cited_segment_texts(payload: dict, cited_ids: list[str]) -> str:
    """THE IMPORTANT PART: full, untruncated text of every cited segment.

    A BPHS segment runs to several thousand characters and covers many verses.
    Truncating here would recreate the exact review error this file exists to
    prevent, so nothing is trimmed -- if that makes the file large, the file is
    allowed to be large.
    """
    if not cited_ids:
        return "_no citations_"
    by_id: dict[str, dict] = {}
    for s in (payload or {}).get("segments", []) or []:
        by_id[s.get("segment_id")] = s
    for u in (payload or {}).get("units", []) or []:
        by_id[u.get("unit_id")] = u

    out: list[str] = []
    for cid in cited_ids:
        node = by_id.get(cid)
        if node is None:
            out.append(f"#### `{cid}` -- NOT IN PAYLOAD "
                       "(ghost, or a real corpus id outside this selection)\n")
            continue
        text = node.get("text") or ""
        out.append(
            f"#### `{cid}`  ({len(text):,} chars, kept={node.get('kept', 'n/a')})\n"
            + _fence(text)
        )
    return "\n\n".join(out)


def _composer_block(composed: Any) -> str:
    """Stage 5b's own record. Added S137, BEFORE the first live composed run.

    WHY THIS EXISTS. `composer.compose()` never raises: on a transport, parse
    or check failure it returns `composed=False` and the caller falls back to
    the bullet rendering. And its ENFORCING no-new-chart-facts check DEGRADES a
    failing block back to the original claim text rather than dropping it. Both
    postures are right, and both are SILENT -- so "the composed answer reads
    much like the bullets did" has three different causes that cannot be told
    apart from the answer text alone:

        (a) the composer never ran (flag off, or no claims to compose),
        (b) it ran and returned composed=False (model or parse failure),
        (c) it ran and `_verify` degraded most blocks back to their originals.

    The first live composed run is a QUALITY JUDGEMENT and it costs a real API
    call on Sulabh's machine (S129b: the sandbox is firewalled from OpenAI), so
    an uninterpretable capture means paying for it twice. Everything below is
    read straight off the composer's return value; nothing is recomputed.

    NOT COMPUTED HERE, DELIBERATELY. The advisory condition-survival RATE needs
    a denominator (how many source claims were conditional), which means
    `composer._CONDITION_RE`. This module imports nothing from `agent.astro`
    and stays that way: a second copy of a closed vocabulary drifting from its
    owner is KNOWN_PATTERNS P-030 in a different medium, and the same defect as
    the S119 needle-table transplant. Derive the rate offline from the
    `### silence gate` section's `kept_claims`, which this same capture already
    records in full, using the composer's own regex.
    """
    if composed is None:
        return ("_composer did not run -- `result['composed']` is absent or None. "
                "Either `compose=False` / `ASTRO_COMPOSER_ENABLED=0`, or the "
                "pipeline returned before Stage 5b._")
    if not isinstance(composed, dict):
        return _fence(f"<unexpected composed payload: {type(composed).__name__}>")

    if not composed.get("composed"):
        # A refusal is a result, not an absence. Record it as loudly as a success.
        return _json_block({
            "composed": False,
            "reason": composed.get("reason"),
            "composer_version": composed.get("composer_version"),
        })

    blocks = composed.get("blocks") or []
    violations = composed.get("violations") or []
    advisory = composed.get("condition_advisory") or []
    restored = composed.get("unaccounted_restored") or []

    # A claim whose rewrite was rejected still SHIPS -- as its original jargon
    # text. That is the failure most likely to be misread as "the composer made
    # no difference", so name the ids outright rather than leaving them to be
    # inferred from the violations list.
    degraded = sorted({int(v["claim_id"]) for v in violations
                       if isinstance(v, dict) and str(v.get("claim_id", "")).isdigit()})

    summary = {
        "composed": True,
        "composer_version": composed.get("composer_version"),
        "usage": composed.get("usage"),
        "claims_in": composed.get("claims_in"),
        "claims_rendered": composed.get("claims_rendered"),
        "demoted_count": len(composed.get("demoted") or []),
        # Did it actually produce a LEAD? SESSION_LOG S136 section 12 item 1 --
        # "no answer, just evidence" -- is the single thing this stage was
        # flipped on to fix, and the block sequence answers it at a glance.
        "block_sequence": [str(b.get("type")) for b in blocks],
        "has_lead": any(str(b.get("type")) == "lead" for b in blocks),
        "enforcing_violations": len(violations),
        "claims_degraded_to_original": degraded,
        "condition_advisory_count": len(advisory),
        "unaccounted_restored": restored,
    }

    # The evidence itself, untruncated, on the same doctrine as the cited source
    # text above: a trimmed record is how a review reaches a wrong verdict.
    return "\n\n".join([
        _json_block(summary),
        "#### enforcing violations (rewrite rejected, claim degraded to original)\n"
        + (_json_block(violations) if violations else "_none_"),
        "#### condition-survival advisory (RECORDED, not enforced)\n"
        + (_json_block(advisory) if advisory else "_none_"),
        "#### demoted by the composer (with its stated reason)\n"
        + (_json_block(composed.get("demoted")) if composed.get("demoted") else "_none_"),
    ])


def _timings_table(timings: dict) -> str:
    if not timings:
        return "_not recorded_"
    rows = ["| stage | seconds |", "|---|---|"]
    total = 0.0
    for k, v in timings.items():
        try:
            total += float(v)
        except (TypeError, ValueError):
            pass
        rows.append(f"| {k} | {v:.2f} |" if isinstance(v, (int, float)) else f"| {k} | {v} |")
    rows.append(f"| **total** | **{total:.2f}** |")
    return "\n".join(rows)


# ------------------------------------------------------------------- capture

def capture_turn(question: str, result: dict, chart_facts: dict | None = None,
                 user_answer: str | None = None) -> Optional[Path]:
    """Append one turn's full trace. Never raises.

    Args:
        question: the user's question, verbatim.
        result: the dict returned by pipeline.answer_question (which carries a
            `trace` key when capture is on).
        chart_facts: the fact dict the answer was built from.
        user_answer: the text the app ACTUALLY displayed -- i.e.
            `answer_view.render_user_answer(result)`. Pass it: `result["answer"]`
            is the pipeline's internal render (verse ids + the silent_on wall)
            and is NOT what the reader sees. The first live capture labelled the
            internal one "what the user saw" and it was wrong (S129).

    Returns:
        The capture file path, or None if nothing was written.
    """
    try:
        path = session_path()
        if path is None:
            return None

        trace = (result or {}).get("trace") or {}
        payload = trace.get("payload") or {}
        plan = (result or {}).get("plan")

        kept = result.get("kept_claims") or []
        dropped = result.get("dropped_claims") or []
        cited: list[str] = []
        for c in list(kept) + list(dropped):
            for sid in (c.get("segment_ids") or []):
                if sid not in cited:
                    cited.append(sid)

        segs = payload.get("segments") or []
        kept_segs = [s for s in segs if s.get("kept")]
        now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")

        parts = [
            f"\n---\n\n## TURN {now}",
            f"### question\n{_fence(question)}",
            f"### chart_facts\n{_json_block(chart_facts)}",
            # BOTH plans: the planner's own output, and what survived the gate.
            # Showing only the post-gate plan hides the gate's effect entirely
            # (S129: a capture showed domains=["marriage"] while dropped_domains
            # said timing_dasha had been removed -- unreadable without this).
            "### plan (Stage 1, as the PLANNER produced it)\n"
            + _json_block(trace.get("plan_before_gate")),
            f"### plan AFTER the capability gate narrowed it\n{_plan_block(plan)}",
            "### capability gate (Stage 1.5)\n" + _json_block({
                "declined": result.get("declined"),
                "dropped_domains": result.get("dropped_domains"),
                # The GATE's own verdict, straight from GateVerdict.refuse_outright.
                # Distinct from `answer_is_empty` below: the gate refusing before
                # any model call, and the interpreter finding nothing in the
                # verses, are different events and must never share one field.
                "gate_refused_outright": trace.get("gate_refused_outright"),
                "answer_is_empty": bool(result.get("refused")) and not kept,
                "gate_version": result.get("capability_gate_version"),
            }),
            "### selection + payload (Stages 2-3)\n" + _json_block({
                "unit_ids": trace.get("unit_ids"),
                "per_domain_units": trace.get("per_domain_units"),
                "segments_total": len(segs),
                "segments_kept": len(kept_segs),
                "whole_units": len(payload.get("units") or []),
                "approx_tokens": result.get("tokens"),
                "estimated_real_tokens": trace.get("estimated_real_tokens"),
                "corpus_fraction": trace.get("corpus_fraction"),
                "over_budget": trace.get("over_budget"),
                # S146: the per-segment keep/drop breakdown from
                # filter_segments_by_domain. THIS is the tagging-coverage signal:
                # kept_domain_match = earned its place; kept_failsafe_untagged /
                # kept_failsafe_unknown_id = rode the fail-safe (a high share here
                # means UNDER-TAGGING, not legitimate breadth); dropped_domain_miss
                # = correctly excluded. segment_cut_pct is how much the segment
                # filter removed. Already in the payload; surfaced so "did we miss
                # tagging / are we shipping off-domain text" is answerable per run.
                "domain_filter": payload.get("domain_filter"),
            }),
            # S146: the FULL deterministic timing ranking -- every antardasha that
            # scored > 0, sorted, with its per-signal breakdown. render_ranking
            # shows the interpreter only the top 6, so a "why is <window> absent"
            # question (e.g. the 2026-2045 marriage gap) cannot be answered from
            # the fact block alone. This is the whole scored list it was ranked
            # against. Absent/None when the question had no timing target.
            "### computed timing ranking (S146 -- FULL list, not the top-6 the model sees)\n"
            + _json_block(trace.get("timing_ranking")),
            "### interpreter (Stage 4)\n" + _json_block({
                "model": result.get("model"),
                "usage": result.get("usage"),
                "claims_returned": len(kept) + len(dropped),
                "ghost_citations": result.get("ghost_citations"),
                "interpreter_refused": trace.get("interpreter_refused"),
                # S137 emission contract. `precondition_rejects` is the SHAPE
                # failure rate for the typed-precondition contract -- a climbing
                # one means the vocabulary prompt is wrong. Both were invisible
                # on the first live Phase-1 run (20260919T072700Z).
                "claims_with_preconditions": result.get("claims_with_preconditions"),
                "precondition_rejects": result.get("precondition_rejects"),
            }),
            "### silence gate (Stage 5a)\n" + _json_block({
                "kept_claims": kept,
                "dropped_claims": dropped,
                "silent_on": result.get("silent_on"),
                "stats": result.get("gate_stats"),
                # S137 amendment: chart tokens a STATEMENT asserted that its
                # preconditions never tested. ADVISORY -- nothing was dropped
                # for it. A non-empty list is the under-coverage rate a human
                # reads before this is ever promoted to enforcing.
                "error": trace.get("gate_error"),
            }),
            # S140: the canonical first/second-class ledger, COMPUTED UPSTREAM in
            # pipeline.answer_question and rendered here as pure data (no import,
            # no derived-rate computation in the capture layer -- test_qa_capture
            # imports-nothing guard). Future roll-ups read THIS block.
            # MEASUREMENT ONLY; `caught_miss_rate_pct` is the P-033 promotion gate.
            "### verifiability (S140)\n" + _json_block(result.get("verifiability")),
            # Stage 5b sits between the gate and what the reader sees, so it is
            # recorded between them. It is the ONLY record of whether the answer
            # below was composed, fell back, or was quietly degraded.
            "### composer (Stage 5b)\n" + _composer_block((result or {}).get("composed")),
            "### CITED SOURCE TEXT (full, untruncated)\n"
            + _cited_segment_texts(payload, cited),
            f"### timings\n{_timings_table(trace.get('timings') or {})}",
            "### what the user actually saw (answer_view)\n"
            + (_fence(user_answer) if user_answer is not None
               else "_not supplied by the caller -- pass user_answer=_ to capture_turn_"),
            f"### pipeline internal render (NOT shown to the user)\n{_fence(result.get('answer') or '')}",
        ]

        raw = trace.get("interpreter_raw")
        if raw:
            parts.append("### interpreter raw response\n" + _fence(str(raw)))

        with path.open("a", encoding="utf-8") as fh:
            fh.write("\n\n".join(parts) + "\n")
        return path

    except Exception as e:  # noqa: BLE001 -- diagnostics must never break an answer
        logger.warning("qa_capture.capture_turn failed: %s: %s", type(e).__name__, e)
        return None


def capture_error(question: str, exc: BaseException) -> Optional[Path]:
    """Record a turn that raised. A crashed turn is the most interesting run
    there is, and it is exactly the one the happy path would never write."""
    try:
        path = session_path()
        if path is None:
            return None
        now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        import traceback
        body = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        with path.open("a", encoding="utf-8") as fh:
            fh.write(
                f"\n---\n\n## TURN {now} -- FAILED\n\n"
                f"### question\n{_fence(question)}\n\n"
                f"### exception\n{_fence(textwrap.shorten(body, 8000, placeholder=' ...[truncated]'))}\n"
            )
        return path
    except Exception as e:  # noqa: BLE001
        logger.warning("qa_capture.capture_error failed: %s: %s", type(e).__name__, e)
        return None
