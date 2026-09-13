"""
Astro Agent -- STAGE 5b: THE COMPOSER.

Stage 4 (interpreter) finds everything the verses support and cites it.
Stage 5a (silence gate) removes what this chart contradicts.
THIS stage decides what MATTERS and how to say it to a layman.

WHY A SEPARATE STAGE
--------------------
Answer SHAPE -- leading with a verdict, ranking findings, saying what was
ruled out -- cannot be a scoring function. Every question shape would need
its own lattice of weights and templates, and the thresholds would multiply
(Working Style #4). It also cannot live in the interpreter prompt: every
edit there is a live-run trigger against a 185k-token payload.

So it is a second, TINY model call whose only input is the gated claim set.
Measured on `diagnostics/qa_capture/20260913T065603Z.md`: 553 and 312
tokens of claims, against 185,297 interpreter prompt tokens on the same
turn -- roughly 0.8%. It also replays for free: `scripts/replay_capture.py`
stubs the interpreter from the stored raw response, so composer iteration
never re-runs Stage 4.

WHAT IT MAY AND MAY NOT DO
--------------------------
S129b locked `answer_view` against rewriting claim text, because rewriting
is where a gate-verified claim silently becomes unverified. This stage DOES
rewrite -- that is its job -- so the lock is replaced here by a mechanical
check rather than a prohibition:

  1. NO NEW CHART FACTS. A rewrite (or any connective text) may not contain
     a chart token -- house ordinal, graha, sign, dignity -- that is absent
     from the claim(s) it rests on. Closed vocabulary, set containment, no
     prose parsing. This is deliberately NOT the clause-reading the silence
     gate does, whose negation guard proved clause-blind (S130 §6).
  2. CONDITIONS SURVIVE -- ADVISORY, NOT ENFORCING. If the source claim is
     conditional ("when the 6th lord is strong..."), the rewrite should stay
     conditional; dropping the condition turns doctrine into a promise about
     the reader's life. This check RECORDS and does not degrade, because a
     keyword test cannot tell a genuinely unhedged rewrite from one that
     carries the condition in different words ("a strong 6th lord brings..."),
     and enforcing it would push most answers back to the jargon original --
     defeating the stage's whole purpose. Promotion to enforcing is gated on
     the measured rate in `condition_advisory`, exactly as the planet reader
     was (S129b (4)). Do not promote it on intuition.
  3. NOTHING IS SILENTLY LOST. Every input claim is either rendered or
     explicitly demoted with a reason. Same discipline as the palm side's
     coverage check.

A block failing rule 1 is REPLACED BY ITS ORIGINAL CLAIM TEXT, never
dropped: the reader still gets the claim, just not the nicer wording, and
the failure is recorded for the capture. Fail-soft, never fail-silent.

Python 3.11.
"""
from __future__ import annotations

import json
import os
import re
from typing import Callable, Optional

from agent.astro import silence_gate as SG

COMPOSER_VERSION = "composer-1.0"
COMPOSER_MODEL = os.environ.get("ASTRO_COMPOSER_MODEL", "gpt-5")
REASONING_EFFORT = "minimal"

# --------------------------------------------------------------------------
# The closed chart vocabulary. Containment against THIS is the whole safety
# argument, so it must stay exhaustive -- widen it in the same change as any
# fact block widening (the FACT_BLOCK_PROVIDES growth contract's sibling).
# --------------------------------------------------------------------------
_GRAHAS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
           "Rahu", "Ketu")
_SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
          "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
_DIGNITY = ("Exalted", "Debilitated", "Own Sign")

_ORDINAL_RE = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)\b", re.I)
_WORD_RE = re.compile(
    r"\b(" + "|".join(_GRAHAS + _SIGNS + ("Exalted", "Debilitated")) + r")\b",
    re.I)
_OWN_SIGN_RE = re.compile(r"\bown sign\b", re.I)

# A condition in the source must not vanish from the rewrite. Deliberately
# generous: this list decides only whether a rewrite must ALSO be hedged,
# never whether a claim ships.
_CONDITION_RE = re.compile(
    r"\b(if|when|unless|provided|should|whenever|as long as|in case|only)\b",
    re.I)


class ComposerError(Exception):
    """Transport/parse failure the caller must see. Never raised for a
    composition the checks rejected -- that degrades, it does not fail."""


def chart_tokens(text: str) -> set[str]:
    """Chart facts named in `text`, normalised. Houses as 'h<N>'."""
    if not text:
        return set()
    out = {f"h{int(m.group(1))}" for m in _ORDINAL_RE.finditer(text)}
    out |= {m.group(1).title() for m in _WORD_RE.finditer(text)}
    if _OWN_SIGN_RE.search(text):
        out.add("Own Sign")
    return out


def _is_conditional(text: str) -> bool:
    return bool(_CONDITION_RE.search(text or ""))


def _claim_rows(gate: SG.GateResult) -> list[dict]:
    """The composer's input rows: one per claim the gate KEPT, with its
    verdict attached. Ids are positional over this list and are stable for
    the life of one turn -- the claim dicts themselves carry no id.

    `gate.verdicts` is built in claim order (silence_gate.py), and kept
    claims are the non-NOT_APPLICABLE ones, so re-deriving the partition
    here keeps verdict alignment exact without touching GateResult.
    """
    rows: list[dict] = []
    for v in gate.verdicts or []:
        if v.verdict == SG.NOT_APPLICABLE:
            continue
        rows.append({
            "claim_id": len(rows),
            "statement": v.statement,
            "segment_ids": list(v.segment_ids),
            "checked": v.verdict == SG.APPLICABLE,
            "check_note": v.reason,
        })
    if rows or not (gate.kept_claims or []):
        return rows
    # Gate failed open (verdicts empty, claims kept). Ship them unchecked
    # rather than composing over nothing.
    for c in gate.kept_claims:
        rows.append({
            "claim_id": len(rows),
            "statement": str(c.get("statement", "")),
            "segment_ids": [str(i) for i in (c.get("segment_ids") or [])],
            "checked": False,
            "check_note": "gate failed open; claim not judged",
        })
    return rows


_SYSTEM = (
    "You are writing the final answer a person reads about their own birth chart. "
    "You are given CLAIMS that have already been established from classical texts and "
    "checked against this chart. Your job is ONLY to decide what matters, in what order, "
    "and to say it in plain everyday English.\n\n"
    "ABSOLUTE RULES:\n"
    "- Use ONLY the claims given. Never add an astrological fact, placement, planet, sign "
    "or house that is not already in the claim you are rewriting.\n"
    "- Never invent a yoga, combination or rule that is not in the claims.\n"
    "- If a claim is conditional (\"when X is strong...\"), your rewrite MUST stay "
    "conditional. Never turn a condition into a promise about their life.\n"
    "- `checked: true` means this chart was verified to match the rule. `checked: false` "
    "means it could not be verified either way. Weigh them accordingly and never present "
    "an unverified claim as settled.\n"
    "- Plain English only. No Sanskrit, no jargon (no kendra, trine, angle, trikona, "
    "dispositor, navamsa, exalted, debilitated) unless you gloss it in ordinary words.\n\n"
    "SHAPE: open with a short lead that answers the question directly and honestly -- "
    "including how confident the overall picture is. Then the claims that matter, "
    "strongest and best-verified first. Drop claims that repeat another or say nothing "
    "specific to this chart.\n\n"
    "Return STRICT JSON only, exactly this shape:\n"
    '{"blocks": [{"type": "lead", "text": "..."}, '
    '{"type": "claim", "claim_id": 0, "text": "<plain-English rewrite>"}, '
    '{"type": "note", "text": "..."}], '
    '"demoted": [{"claim_id": 3, "reason": "repeats claim 1"}]}\n'
    "Every claim_id you were given must appear exactly once, in `blocks` or in `demoted`."
)


def _default_llm(system: str, user: str, **kwargs):
    """OpenAI call. Mirrors interpreter._default_llm's extra_body handling:
    a TypeError on a named kwarg means the SDK SIGNATURE is old, not that the
    API refuses the parameter (KNOWN_PATTERNS P-023)."""
    from openai import OpenAI

    client = OpenAI()
    msgs = [{"role": "system", "content": system},
            {"role": "user", "content": user}]
    base = {"model": COMPOSER_MODEL, "messages": msgs,
            "response_format": {"type": "json_object"}}
    try:
        resp = client.chat.completions.create(
            reasoning_effort=REASONING_EFFORT, **base)
        path = "named_kwarg"
    except TypeError:
        resp = client.chat.completions.create(
            extra_body={"reasoning_effort": REASONING_EFFORT}, **base)
        path = "extra_body"
    u = getattr(resp, "usage", None)
    return resp.choices[0].message.content, {
        "model": COMPOSER_MODEL,
        "reasoning_effort_path": path,
        "prompt_tokens": getattr(u, "prompt_tokens", None),
        "completion_tokens": getattr(u, "completion_tokens", None),
    }


def _verify(blocks: list[dict], rows: dict[int, dict]
            ) -> tuple[list[dict], list[dict], list[dict]]:
    """Apply the checks. Returns (safe_blocks, violations, condition_advisory).

    ENFORCING: invented chart facts. A failing CLAIM block degrades to the
    original statement; a failing LEAD/NOTE block is dropped, since connective
    text is never load-bearing.
    ADVISORY: a dropped condition is RECORDED only -- see the module docstring
    for why it does not degrade, and what would justify promoting it.
    """
    advisory: list[dict] = []
    allowed_all: set[str] = set()
    for r in rows.values():
        allowed_all |= chart_tokens(r["statement"])

    safe: list[dict] = []
    bad: list[dict] = []
    for b in blocks:
        btype = str(b.get("type", ""))
        text = str(b.get("text", "") or "")
        if btype == "claim":
            try:
                cid = int(b.get("claim_id"))
            except (TypeError, ValueError):
                bad.append({"block": b, "why": "claim_id not an integer"})
                continue
            row = rows.get(cid)
            if row is None:
                bad.append({"block": b, "why": f"claim_id {cid} was not supplied"})
                continue
            invented = chart_tokens(text) - chart_tokens(row["statement"])
            if _is_conditional(row["statement"]) and not _is_conditional(text):
                advisory.append({"claim_id": cid, "text": text,
                                 "why": "no condition keyword in a rewrite of a "
                                        "conditional claim (advisory, not enforced)"})
            if invented or not text.strip():
                bad.append({"claim_id": cid, "text": text,
                            "why": ("invented chart facts: " + ", ".join(sorted(invented))
                                    if invented else "empty rewrite")})
                text = row["statement"]          # degrade, never drop
            safe.append({"type": "claim", "claim_id": cid, "text": text,
                         "segment_ids": row["segment_ids"],
                         "checked": row["checked"]})
        elif btype in ("lead", "note"):
            invented = chart_tokens(text) - allowed_all
            if invented:
                bad.append({"block": btype, "text": text,
                            "why": "invented chart facts: " + ", ".join(sorted(invented))})
                continue
            if text.strip():
                safe.append({"type": btype, "text": text})
        else:
            bad.append({"block": b, "why": f"unknown block type {btype!r}"})
    return safe, bad, advisory


def compose(question: str, gate: SG.GateResult, *,
            llm: Optional[Callable] = None) -> dict:
    """Compose the final answer. NEVER raises for a model or check problem --
    on any failure it returns `composed=False` and the caller falls back to
    the existing renderer, so this stage can never cost the user an answer.
    """
    rows_list = _claim_rows(gate)
    rows = {r["claim_id"]: r for r in rows_list}
    if not rows:
        return {"composed": False, "reason": "no claims to compose",
                "blocks": [], "violations": [], "condition_advisory": [], "demoted": [],
                "composer_version": COMPOSER_VERSION}

    user = json.dumps({
        "question": question,
        "claims": [{k: r[k] for k in
                    ("claim_id", "statement", "checked", "check_note")}
                   for r in rows_list],
        "not_addressed": list(gate.silent_on or []),
    }, ensure_ascii=False, indent=2)

    try:
        raw, usage = (llm or _default_llm)(_SYSTEM, user)
        parsed = json.loads(raw)
        blocks = parsed.get("blocks") or []
        demoted = parsed.get("demoted") or []
        if not isinstance(blocks, list):
            raise ComposerError("blocks is not a list")
    except Exception as e:
        return {"composed": False, "reason": f"{type(e).__name__}: {e}",
                "blocks": [], "violations": [], "condition_advisory": [], "demoted": [],
                "composer_version": COMPOSER_VERSION}

    safe, violations, condition_advisory = _verify(blocks, rows)

    # Coverage: nothing may vanish without a recorded reason.
    seen = {b["claim_id"] for b in safe if b["type"] == "claim"}
    seen |= {int(d.get("claim_id")) for d in demoted
             if isinstance(d, dict) and str(d.get("claim_id", "")).isdigit()}
    unaccounted = sorted(set(rows) - seen)
    for cid in unaccounted:
        safe.append({"type": "claim", "claim_id": cid,
                     "text": rows[cid]["statement"],
                     "segment_ids": rows[cid]["segment_ids"],
                     "checked": rows[cid]["checked"]})

    return {
        "composed": True,
        "blocks": safe,
        "demoted": demoted,
        "violations": violations,
        "condition_advisory": condition_advisory,
        "unaccounted_restored": unaccounted,
        "claims_in": len(rows),
        "claims_rendered": sum(1 for b in safe if b["type"] == "claim"),
        "usage": usage,
        "composer_version": COMPOSER_VERSION,
    }


def render(composed: dict) -> str:
    """Blocks -> the text the user sees. Deterministic; adds nothing."""
    if not composed.get("composed"):
        return ""
    out: list[str] = []
    for b in composed["blocks"]:
        if b["type"] == "lead":
            out.append(b["text"])
        elif b["type"] == "claim":
            out.append(f"- {b['text']}")
        else:
            out.append(b["text"])
    return "\n\n".join(out)
