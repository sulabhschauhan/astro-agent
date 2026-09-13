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
    "supported by a cited verse.\n\n"
    "VOICE -- the reader has never studied astrology and is reading about their own life:\n"
    "- Address them directly: \"you\", \"your\". NEVER write \"the native\", \"the subject\", "
    "\"one will\". The classical texts use the third person; you must not.\n"
    "- KEEP the opening placement clause exactly as specified above -- it is machine-checked -- "
    "but write the RESULT of that placement in everyday English.\n"
    "- No untranslated technical terms in a statement: kendra, trikona, trine, angle, angular, "
    "dispositor, Navamsa, varga, divisional, Atmakaraka, Amatyakaraka, Karakamsa, Arudha, "
    "Moolatrikona, exalted, debilitated. If such an idea is load-bearing, put it in plain words "
    "and add the Sanskrit once in brackets -- e.g. \"a strong supporting house (kendra)\".\n"
    "- Where a verse is unfavourable, report it plainly and without drama, as what the text says, "
    "not as a prediction about their life. No fatalism, no alarm, no reassurance either.\n"
    "- One or two sentences per claim. No preamble, no summary claim restating the others.\n\n"
    "`silent_on` is INTERNAL DIAGNOSTICS and is never shown to the user, so be terse and "
    "technical there: name the verse ids and the missing precondition, nothing more.\n"
)


class InterpreterError(Exception):
    """Raised only for a transport/parse failure the caller must see; never for
    an honest refusal (that is a normal, structured result)."""


def _payload_ids(payload: dict) -> set[str]:
    ids = {s["segment_id"] for s in payload.get("segments", []) if s.get("kept")}
    ids |= {u["unit_id"] for u in payload.get("units", [])}
    return ids


def _id_manifest(payload: dict) -> str:
    """The exact, complete list of citable ids, rendered ahead of the verses.

    WHY (S130, measured). Every ghost citation in the 2026-09-13 live runs came
    from the prompt carrying TWO address formats at once: split chapters appear
    as [ch34_s003] (book prefix stripped, per-segment) while whole chapters
    appear as [bphs2_ch57] (full unit id, no sub-ids at all). The model
    normalises to the dominant per-segment format and mints sub-ids for the
    whole ones -- 9 of 10 ghosts in one turn were ch57_s001..s016 against
    bphs2_ch57 "Effects of the Antardasas in the Dasa of Saturn", a chapter
    genuinely present and genuinely on-topic, carried WHOLE. The other ghosts
    were ordinal overruns: ch34_s013 where ch34 ends at s012, ch17_s012 where
    ch17 ends at s004.

    Both are addressing failures, not fabrication -- the ghost guard then drops
    the CLAIM along with the id, so real answers are lost (the Saturn turn shed
    10 ids and shipped 2 claims). This is S124's own law reappearing: an id
    space the model cannot enumerate produces addresses that cannot resolve.
    Stating the space removes the guesswork.
    """
    seg_ids = [s["segment_id"] for s in payload.get("segments", []) if s.get("kept")]
    unit_ids = [u["unit_id"] for u in payload.get("units", [])]
    lines = []
    if seg_ids:
        lines.append("Verse ids (cite the exact id): " + ", ".join(seg_ids))
    if unit_ids:
        lines.append("Whole-chapter ids -- these have NO sub-ids; cite the id "
                     "exactly as written and never append _s001 or similar: "
                     + ", ".join(unit_ids))
    if not lines:
        return ""
    return ("CITABLE IDS -- this list is COMPLETE. Cite ONLY ids that appear "
            "here, character for character. An id you do not see here does not "
            "exist, and a claim citing one is discarded whole.\n"
            + "\n".join(lines))


def _verse_block(payload: dict) -> str:
    parts = [f"[{s['segment_id']}] {s['text'].strip()}"
             for s in payload.get("segments", []) if s.get("kept")]
    # Whole chapters are marked inline as well as in the manifest: the model
    # reads the verses far more closely than any preamble.
    parts += [f"[{u['unit_id']}] (whole chapter -- no sub-ids) {u['text'].strip()}"
              for u in payload.get("units", [])]
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
    # The fallback below silently drops reasoning_effort on an SDK/model that
    # does not accept it. That is correct behaviour but it was INVISIBLE: a live
    # run showed 8,640 reasoning tokens on "minimal" with no way to tell whether
    # the setting had been applied or quietly discarded. Record which path ran.
    # S130: the bare `except TypeError -> drop it` below was firing on EVERY live
    # call. Measured in diagnostics/qa_capture/20260913T040439Z.md: 7 of 7 turns
    # reported reasoning_effort_applied=False with 3,328-8,384 reasoning tokens
    # and 50-58s interpreter stages. Cause: older SDKs do not accept
    # `reasoning_effort` as a NAMED kwarg on chat.completions.create, so the
    # TypeError path ran every time and the setting never reached the API.
    # `extra_body` puts it in the request payload on ANY SDK version, so the
    # named-kwarg TypeError is no longer a reason to give up on the setting.
    # Only a rejection BY THE API is.
    effort_applied = True
    effort_path = "named_kwarg"
    try:
        resp = client.chat.completions.create(reasoning_effort=reasoning_effort, **kwargs)
    except TypeError:
        # Old SDK signature. Send it in the body instead of abandoning it.
        try:
            resp = client.chat.completions.create(
                extra_body={"reasoning_effort": reasoning_effort}, **kwargs)
            effort_path = "extra_body"
        except Exception as e:  # noqa: BLE001 -- the API itself refused the param
            effort_applied = False
            effort_path = f"dropped ({type(e).__name__})"
            resp = client.chat.completions.create(**kwargs)
    u = resp.usage
    usage = {
        "prompt_tokens": getattr(u, "prompt_tokens", 0),
        "completion_tokens": getattr(u, "completion_tokens", 0),
        "reasoning_tokens": getattr(getattr(u, "completion_tokens_details", None),
                                    "reasoning_tokens", 0) or 0,
        "cached_tokens": getattr(getattr(u, "prompt_tokens_details", None),
                                 "cached_tokens", 0) or 0,
        "reasoning_effort_requested": reasoning_effort,
        "reasoning_effort_applied": effort_applied,
        # WHICH path delivered it. "dropped (...)" names the API's own refusal --
        # without this, a False above cannot be told from an old SDK signature.
        "reasoning_effort_path": effort_path,
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

    manifest = _id_manifest(payload)
    system = (_SYSTEM_HEAD
              + ("\n" + manifest + "\n" if manifest else "")
              + "\nVERSES:\n" + verses)          # corpus-first (cacheable prefix)
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
