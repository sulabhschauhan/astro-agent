"""

================================================================
PATH B / LAB TRACK -- NOT WIRED TO THE PRODUCT (S128 lock).

This module has NO non-test caller. The live answer path is
agent/infra/orchestrator.answer_question, imported by
frontend/app.py:31. Changing this file ships NOTHING to users.
Read docs/ANSWER_PATHS.md before editing or proposing work here.
================================================================

Astro Agent -- STAGE 4: THE INTERPRETER (locked to GPT-5).

Reads the deterministic FACT BLOCK + the selected verses and emits STRUCTURED
claims -- each claim is a statement plus the verse ids it rests on -- so
Stage 5a (the silence gate) can judge every claim's precondition against the
chart. Contracts this stage honours:

  - NEVER computes a chart fact (S124 lock). It reasons over supplied facts.
  - Cites LOCATION ids only, never quotes verse text (S124 lock).
  - Grounds ONLY in the supplied verses; refuses honestly when they cannot
    answer (validated 2026-09-10: gpt-5 refused the timing question cleanly,
    0 ghost citations across every question, recall held at 105k tokens).
  - CORPUS-FIRST prompt: the user-independent verse block leads the prompt so
    OpenAI prompt-caching (90% off) discounts it across questions.
  - GHOST GUARD: any cited id not present in the payload is stripped here; a
    claim left with no real id is dropped. The gate never sees a ghost id.
  - reasoning_effort=minimal (measured sufficient; keeps hidden reasoning
    tokens, billed at output rate, down).
  - Dependency-injected llm so tests run with a stub and never call the API.

Python 3.11.
"""
from __future__ import annotations

import json
import os
import re
from typing import Callable, Optional

INTERPRETER_VERSION = "interpreter-1.0"
INTERPRETER_MODEL = "gpt-5"          # locked S126; override per-call for A/B only
REASONING_EFFORT = "minimal"

_SYSTEM_HEAD = (
    "You are a Vedic astrologer grounded ONLY in the numbered verses given below, from "
    "Brihat Parashara Hora Shastra. Absolute rules:\n"
    "- Use ONLY these verses. Never use outside knowledge, never invent doctrine.\n"
    "- A claim is valid ONLY if the cited verse's condition matches the CHART FACTS.\n"
    "- Cite the verse id(s) each claim rests on. Never quote verse text.\n"
    "- If the verses cannot answer the question, refuse plainly. Honest silence beats a guess.\n\n"
    "Return STRICT JSON only, no prose outside it, exactly this shape:\n"
    '{"claims": [{"statement": "<one plain-language claim>", "segment_ids": ["<id>", ...]}], '
    '"silent_on": ["<what you could not address and why>"], "refused": false}\n'
    "Each claim.statement must be self-contained and name the placement it relies on so it can be "
    "checked (e.g. \"With the 10th lord in the 4th, ...\"). Put NOTHING in a statement that is not "
    "supported by a cited verse.\n"
)


class InterpreterError(Exception):
    """Raised only for a transport/parse failure the caller must see; never for
    an honest refusal (that is a normal, structured result)."""


def _payload_ids(payload: dict) -> set[str]:
    ids = {s["segment_id"] for s in payload.get("segments", []) if s.get("kept")}
    ids |= {u["unit_id"] for u in payload.get("units", [])}
    return ids


def _verse_block(payload: dict) -> str:
    parts = [f"[{s['segment_id']}] {s['text'].strip()}"
             for s in payload.get("segments", []) if s.get("kept")]
    parts += [f"[{u['unit_id']}] {u['text'].strip()}" for u in payload.get("units", [])]
    return "\n\n".join(parts)


def _default_llm(system: str, user: str, *, model: str, reasoning_effort: str) -> tuple[str, dict]:
    """Live GPT-5 call. Returns (content, usage_dict). Isolated for stubbing."""
    try:
        from openai import OpenAI
    except ImportError as e:  # pragma: no cover
        raise InterpreterError("openai package not installed; pass llm= instead") from e
    client = OpenAI()
    kwargs = dict(model=model, response_format={"type": "json_object"},
                  messages=[{"role": "system", "content": system},
                            {"role": "user", "content": user}])
    try:
        resp = client.chat.completions.create(reasoning_effort=reasoning_effort, **kwargs)
    except TypeError:
        resp = client.chat.completions.create(**kwargs)  # SDK/model without the param
    u = resp.usage
    usage = {
        "prompt_tokens": getattr(u, "prompt_tokens", 0),
        "completion_tokens": getattr(u, "completion_tokens", 0),
        "reasoning_tokens": getattr(getattr(u, "completion_tokens_details", None),
                                    "reasoning_tokens", 0) or 0,
        "cached_tokens": getattr(getattr(u, "prompt_tokens_details", None),
                                 "cached_tokens", 0) or 0,
    }
    return resp.choices[0].message.content or "", usage


def interpret(
    question: str,
    fact_block: str,
    payload: dict,
    *,
    llm: Optional[Callable[..., tuple]] = None,
    model: str = INTERPRETER_MODEL,
) -> dict:
    """Produce structured, ghost-free claims for one question.

    Returns {claims, silent_on, refused, ghost_citations, usage, model,
    interpreter_version, raw}. `claims` is ready to hand to the silence gate:
    each is {statement, segment_ids} with only real ids.
    """
    verses = _verse_block(payload)
    if not verses.strip():
        return {"claims": [], "silent_on": ["No verses were selected for this question."],
                "refused": True, "ghost_citations": [], "usage": {}, "model": model,
                "interpreter_version": INTERPRETER_VERSION, "raw": ""}

    system = _SYSTEM_HEAD + "\nVERSES:\n" + verses           # corpus-first (cacheable prefix)
    user = (fact_block + f"\n\nQUESTION: {question}\n"
            "Answer using only the verses above, as JSON claims citing ids.")

    call = llm if llm is not None else _default_llm
    content, usage = call(system, user, model=model, reasoning_effort=REASONING_EFFORT)

    try:
        obj = json.loads(content)
    except (json.JSONDecodeError, TypeError) as e:
        raise InterpreterError(f"interpreter did not return valid JSON: {e}") from e

    ids = _payload_ids(payload)
    ghost: list[str] = []
    clean_claims: list[dict] = []
    for c in (obj.get("claims") or []):
        if not isinstance(c, dict):
            continue
        stmt = str(c.get("statement", "")).strip()
        raw_ids = [str(x) for x in (c.get("segment_ids") or [])]
        real = [i for i in raw_ids if i in ids]
        ghost += [i for i in raw_ids if i not in ids]
        if stmt and real:                       # drop a claim with no surviving real id
            clean_claims.append({"statement": stmt, "segment_ids": real})

    return {
        "claims": clean_claims,
        "silent_on": list(obj.get("silent_on") or []),
        "refused": bool(obj.get("refused")) or not clean_claims,
        "ghost_citations": sorted(set(ghost)),
        "usage": usage,
        "model": model,
        "interpreter_version": INTERPRETER_VERSION,
        "raw": content,
    }
