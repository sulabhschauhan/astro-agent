"""

================================================================
PATH B IS THE PRODUCT (S129 cutover). THIS MODULE IS LIVE.

agent/astro/pipeline.answer_question (frontend/app.py:40) calls
interpret() at pipeline.py:332. A change here SHIPS TO USERS.
Path A (agent/infra/orchestrator) is the retained revert target,
wired to no UI. SUPERSEDES the S128 "not wired" banner, false
since S129. Read docs/ANSWER_PATHS.md before editing.
================================================================

Astro Agent -- STAGE 4: THE INTERPRETER (locked to GPT-5).

Reads the deterministic FACT BLOCK + the selected verses and emits STRUCTURED
claims -- each claim is a statement, the verse ids it rests on, and (S137) the
verse's own chart condition written as TYPED PRECONDITIONS -- so Stage 5a can
judge every claim against the computed chart by evaluation rather than by
pattern-matching the claim's English. See docs/ANSWER_VERIFICATION_ARCHITECTURE.md. Contracts this stage honours:

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

from agent.astro import predicates as PRED

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
    '{"claims": [{"statement": "<one plain-language claim>", "segment_ids": ["<id>", ...], "preconditions": [<see PRECONDITIONS below>]}], '
    '"silent_on": [{"topic": "<what you did not state>", "segment_ids": ["<id>", ...], "withheld_because": [<preconditions, see below>], "note": "<terse: verse id + missing precondition>"}], "refused": false}\n'
    "Each claim.statement must be self-contained and name the chart fact it rests on so it can be "
    "checked -- a placement (e.g. \"With the 10th lord in the 4th, ...\") or, for a timing claim, the "
    "dasha period and its dates (e.g. \"During your Venus period, around <start> to <end>, ...\"). Put "
    "NOTHING in a statement that is not supported by a cited verse OR by these chart facts.\n"
    "- Also give each claim its `preconditions`: the verse's own chart condition, written in the "
    "closed vocabulary set out under PRECONDITIONS below. The statement stays plain English for "
    "the reader; the preconditions are the same condition in a form the chart can be checked "
    "against.\n\n"
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
    "`silent_on` records each verse or point you did NOT turn into a claim because its "
    "chart condition looks unmet. For each, give `withheld_because`: the SAME closed-"
    "vocabulary preconditions you would have declared had you made the claim -- the exact "
    "condition whose failure is your reason for staying silent. These are checked against "
    "the computed chart; if a condition you call unmet actually HOLDS, that is a silent "
    "miss. State the real condition at full strength, and NEVER withhold a verse whose "
    "condition you have not checked against the facts. A condition not expressible in the "
    "vocabulary -> one `unfittable` with a note. Silent for a NON-chart reason (the verses "
    "do not address the question, or need a fact we do not compute) -> give `note` only, "
    "no `withheld_because`. Be terse; this is internal diagnostics.\n"
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
    chart_facts: Optional[dict] = None,
) -> dict:
    """Produce structured, ghost-free claims for one question.

    Returns {claims, silent_on, refused, ghost_citations, usage, model,
    interpreter_version, raw}. `claims` is ready to hand to the silence gate:
    each is {statement, segment_ids} with only real ids.
    """
    verses = _verse_block(payload)
    if not verses.strip():
        return {"claims": [], "silent_on": ["No verses were selected for this question."],
                "silences": [], "refused": True, "ghost_citations": [], "usage": {},
                "model": model, "interpreter_version": INTERPRETER_VERSION, "raw": ""}

    manifest = _id_manifest(payload)
    # The vocabulary is GENERATED from predicates.PREDICATES, never restated
    # here: one closed vocabulary, one owner (P-030). It sits in the
    # user-independent prefix so prompt caching still discounts it; it changes
    # only when the registry does, which invalidates the cache once.
    system = (_SYSTEM_HEAD
              + "\n" + PRED.vocabulary_prompt(chart_facts) + "\n"
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
    precondition_rejects: list[dict] = []
    clean_claims: list[dict] = []
    for c in (obj.get("claims") or []):
        if not isinstance(c, dict):
            continue
        stmt = str(c.get("statement", "")).strip()
        raw_ids = [str(x) for x in (c.get("segment_ids") or [])]
        real = [i for i in raw_ids if i in ids]
        ghost += [i for i in raw_ids if i not in ids]

        # PRECONDITIONS are ADDITIVE and FAIL-SAFE. An illegal one is dropped
        # and recorded; it NEVER costs the claim. A claim that arrives with
        # none is kept and simply cannot be confirmed downstream -- it reaches
        # the reader hedged, which is the S124 posture (a filter that cannot
        # judge must keep). The ghost guard above is the ONLY thing here with
        # authority to discard a claim.
        preconds: list[dict] = []
        for raw_p in (c.get("preconditions") or []):
            ok, why = PRED.validate_precondition(raw_p)
            if ok:
                preconds.append(raw_p)
            else:
                precondition_rejects.append({"statement": stmt[:120], "why": why,
                                             "precondition": raw_p})

        if stmt and real:                       # drop a claim with no surviving real id
            clean_claims.append({"statement": stmt, "segment_ids": real,
                                 "preconditions": preconds})

    # PARALLEL TYPED SILENCES (P-033). Same fail-safe posture as claims: an
    # illegal withheld_because predicate is dropped and recorded, never fatal.
    # `silent_on` stays list[str] for _render/composer; `silences` carries the
    # structured, checkable form for the silence gate.
    clean_silences: list[dict] = []
    silent_on_strings: list[str] = []
    for rs in (obj.get("silent_on") or []):
        if isinstance(rs, str):                       # legacy / degraded shape
            clean_silences.append({"topic": rs, "segment_ids": [],
                                   "withheld_because": [], "note": rs})
            silent_on_strings.append(rs)
            continue
        if not isinstance(rs, dict):
            continue
        topic = str(rs.get("topic") or "").strip()
        note = str(rs.get("note") or "").strip()
        seg = [i for i in (str(x) for x in (rs.get("segment_ids") or [])) if i in ids]
        wb: list[dict] = []
        for raw_p in (rs.get("withheld_because") or []):
            ok, why = PRED.validate_precondition(raw_p)
            if ok:
                wb.append(raw_p)
            else:
                precondition_rejects.append({"where": "silence", "topic": topic[:120],
                                             "why": why, "precondition": raw_p})
        clean_silences.append({"topic": topic, "segment_ids": seg,
                               "withheld_because": wb, "note": note})
        s = f"{topic}: {note}" if note and note != topic else (note or topic)
        if s:
            silent_on_strings.append(s)

    return {
        "claims": clean_claims,
        "silent_on": silent_on_strings,
        "silences": clean_silences,
        "silences_with_preconditions": sum(1 for s in clean_silences if s["withheld_because"]),
        "refused": bool(obj.get("refused")) or not clean_claims,
        "ghost_citations": sorted(set(ghost)),
        # Shape failures, not content failures. A climbing rate means the
        # vocabulary or its prompt is wrong -- it is the health metric for the
        # emission contract, the sibling of `unfittable`'s rate for the
        # vocabulary itself.
        "precondition_rejects": precondition_rejects,
        "claims_with_preconditions": sum(1 for c in clean_claims if c["preconditions"]),
        "usage": usage,
        "model": model,
        "interpreter_version": INTERPRETER_VERSION,
        "raw": content,
    }


# =====================================================================
# EXPERT MODE (S141) -- the realignment path.
#
# Instead of emitting verse-cited JSON claims that a downstream gate verifies
# one sentence at a time, the interpreter is given the COMPLETE computed fact
# block + the retrieved passages and asked to answer like an expert astrologer.
# FACTS stay hard-grounded (the prompt forbids stating any placement/date/yoga
# not in the block -- and the fact block is now complete, incl. the full dasha
# tree, so there is nothing left to invent). INTERPRETATION is freed. No verse
# ids reach the user; the citations that remain are internal.
#
# This is OFF by default (pipeline.answer_question's `expert` flag / the
# ASTRO_EXPERT_MODE env var). The cited-claim path is untouched and remains the
# default until expert mode is measured and promoted.
# =====================================================================

EXPERT_REASONING_EFFORT: Optional[str] = None  # gpt-5 default; a tuning knob, not minimal

EXPERT_SYSTEM = (
    "You are an expert Vedic astrologer in the Parashari tradition (Brihat Parashara "
    "Hora Shastra, Phaladeepika, Saravali), also fluent in the KP and Lal Kitab systems. "
    "You are reading ONE person's birth chart and answering their question directly, for "
    "THEM to read.\n\n"
    "You are given (1) the COMPUTED CHART FACTS for this person and (2) relevant classical "
    "passages. Work from these.\n\n"
    "HARD RULE -- facts are not yours to invent:\n"
    "- Every chart FACT you state -- a planet's house or sign, which house a lord occupies, "
    "a dignity, a yoga, a dasha/antardasha period or its dates, or a transit placement "
    "(where a planet was transiting, and relative to what, at a given time) -- MUST come "
    "from the CHART FACTS given below. Never invent, guess, or compute a placement or a "
    "date. The dasha "
    "timeline is COMPLETE (every major period and sub-period with its dates), so read the "
    "period you need; do not calculate one. If a fact you would need is genuinely not in "
    "the block, say what the given facts support and name the limit rather than filling the gap.\n"
    "- INTERPRETATION -- what a placement or period MEANS -- may draw on your expert "
    "knowledge of the classical texts and the passages provided. Never use pop astrology or "
    "unverified sources.\n\n"
    "ANSWER LIKE AN EXPERT WOULD:\n"
    "- Lead with the real answer to their question -- the bottom line first, including the "
    "uncomfortable part if there is one. No throat-clearing.\n"
    "- Be specific to THIS chart: name the actual placements and periods driving your "
    "reading. For any timing, give the real date windows from the dasha facts as "
    "month/quarter ranges (dates are approximate, +/-37 days -- say so once, not repeatedly). "
    "A retrospective question ('when would I have...') is answered with the correct PAST "
    "period, not a future one.\n"
    "- Structure however the question demands -- a timing question wants ranked windows; a "
    "'what does X mean' question wants themes, perhaps a short period-by-period read. Short "
    "paragraphs or a few grouped points, whatever reads best. Do not pad.\n"
    "- Say how sure you are in plain words -- very likely / likely / possible / uncertain -- "
    "and why, tied to the facts.\n"
    "- Plain second-person language ('you', 'your'). Translate every technical term (say "
    "'your marriage ruler', or name it once in brackets). NO citations, NO verse ids -- "
    "write as an astrologer speaking to a client, not a footnoted paper.\n"
    "- Be honest and non-fatalistic. Report difficult indications plainly, without drama, "
    "false alarm, or false reassurance."
)


def _default_llm_expert(system: str, user: str, *, model: str,
                        reasoning_effort: Optional[str]) -> tuple[str, dict]:
    """Live GPT-5 free-text call (no JSON response_format). Isolated for stubbing."""
    try:
        from openai import OpenAI
    except ImportError as e:  # pragma: no cover
        raise InterpreterError("openai package not installed; pass llm= instead") from e
    client = OpenAI()
    kwargs = dict(model=model, messages=[{"role": "system", "content": system},
                                         {"role": "user", "content": user}])
    if reasoning_effort is None:
        resp = client.chat.completions.create(**kwargs)
    else:
        try:
            resp = client.chat.completions.create(reasoning_effort=reasoning_effort, **kwargs)
        except TypeError:
            try:
                resp = client.chat.completions.create(
                    extra_body={"reasoning_effort": reasoning_effort}, **kwargs)
            except Exception:  # noqa: BLE001
                resp = client.chat.completions.create(**kwargs)
    u = resp.usage
    usage = {"prompt_tokens": getattr(u, "prompt_tokens", 0),
             "completion_tokens": getattr(u, "completion_tokens", 0),
             "reasoning_tokens": getattr(getattr(u, "completion_tokens_details", None),
                                         "reasoning_tokens", 0) or 0}
    return resp.choices[0].message.content or "", usage


def interpret_expert(
    question: str,
    fact_block: str,
    payload: dict,
    *,
    llm: Optional[Callable[..., tuple]] = None,
    model: str = INTERPRETER_MODEL,
) -> dict:
    """Free-text expert answer over the complete fact block + retrieved passages.

    Returns {answer, usage, model, interpreter_version, raw, expert_mode}. The
    `answer` is plain markdown for the reader -- no ids, no JSON. Never raises for
    an empty answer (that is a refusal the caller surfaces)."""
    verses = _verse_block(payload)
    user = (f"CHART FACTS (the only chart facts you may state):\n{fact_block}\n\n"
            f"CLASSICAL PASSAGES (for interpretation):\n{verses}\n\n"
            f"QUESTION: {question}\n\n"
            "Answer the person directly, as an expert astrologer.")
    call = llm if llm is not None else _default_llm_expert
    content, usage = call(EXPERT_SYSTEM, user, model=model,
                          reasoning_effort=EXPERT_REASONING_EFFORT)
    return {"answer": (content or "").strip(), "usage": usage, "model": model,
            "interpreter_version": INTERPRETER_VERSION, "raw": content,
            "expert_mode": True}
