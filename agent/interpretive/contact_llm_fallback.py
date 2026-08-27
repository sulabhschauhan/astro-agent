"""
agent/interpretive/contact_llm_fallback.py

S108: standalone LLM synonym-resolver for contact verbs that the
deterministic contact_mapper (S104 Step 4 + S106 inflection) leaves
unresolved (token=None). NOT wired into the pipeline in this task -- see
the "STANDALONE this step" note at the end of this docstring; wiring is a
separate later task (S109).

WHY THIS EXISTS: contact_mapper resolves every DECLARED verb (the exact
tables) and every regular tense/aspect variant of one (S106's inflection
map). A genuine SYNONYM not derived from any declared verb -- "fuses",
"runs into", "converges" -- still returns token=None and is silently
dropped. This module is the rescue path for exactly that residual class,
firing only on contacts contact_mapper genuinely could not resolve.

INDIRECTION, NOT DIRECT-TO-TOKEN (the core design decision): the LLM's
ONLY job is picking the CLOSEST KNOWN CANONICAL VERB from a closed set,
or "unclear". It never sees position, never chooses a token, never does
the join-vs-meet position split -- those stay entirely in contact_mapper's
deterministic tables. After the LLM answers, this module re-runs
contact_mapper.map_contact() on the SAME contact with raw_verb replaced by
the LLM's canonical choice -- token/cardinality/position-split logic is
therefore 100% deterministic and re-validated by the existing tables,
never trusted directly from the LLM. A hallucinated "canonical" verb
outside the closed set can never produce an off-vocabulary token: the
tables are the only path to a token, ever, on either the deterministic or
the fallback path.

DEFENSIVE RE-VALIDATION: even though this module's intended contract is
"only ever receives contacts contact_mapper already returned token=None
for" (S109's bridge is the intended caller), resolve_unresolved_contacts()
does NOT trust that blindly -- it re-runs map_contact() on every input
contact FIRST. Any contact that resolves right there (a caller passed
something contact_mapper could already handle, including trivially an
S106-inflected form) is returned directly, with ZERO LLM involvement for
it. The LLM batch contains ONLY contacts still token=None after this
re-check -- so an all-already-resolved input list makes zero LLM calls,
same as an empty list, and this module can never spend a call rescuing
something the deterministic layer already had.

BATCHED: resolve_unresolved_contacts() takes a LIST and makes AT MOST ONE
LLM call for the whole batch (zero if nothing in it is genuinely
unresolved), so a caller spends at most +1 call per reading regardless of
how many contacts need rescue.

FAIL-CLOSED EVERYWHERE (the AI-over-AI safety surface, CLAUDE.md Working
Style #5/#9 -- an LLM's raw answer is never trusted without a deterministic
re-check): a hallucinated canonical verb outside the closed set, malformed
or unparseable JSON, a wrong-length response list, or the client itself
raising/timing out -- ALL resolve the affected contact(s) to "unclear"
(token stays None), logged, NEVER raised to the caller. A structural
batch-level failure (bad JSON, wrong-length list, API error) fails the
WHOLE batch to unclear; a single hallucinated or genuinely-"unclear" item
inside an otherwise well-formed batch fails ONLY that item. "unclear" is
this module's own honest-silence outcome, never a failure to recover
from -- same posture as contact_mapper's own "never guesses" contract.

OUTPUT CONTRACT: resolve_unresolved_contacts(contacts, client) returns
(results, audits) -- two lists, same length and order as `contacts`.
`results[i]` is a dict of the SAME shape contact_mapper.map_contact()
returns ({token, confidence, raw_verb, target, position, reason});
raw_verb is ALWAYS the caller's original verbatim verb, never the LLM's
canonical substitute. `audits[i]` is a structured record ({raw_verb,
target, position, llm_canonical_choice, final_token, disposition}) --
this is what a future S109 wiring feeds into a failure-capture/human-
review log; this module returns it, it does not log it anywhere itself.

REMOVABLE / FUTURE-PRIMARY: resolve_unresolved_contacts() is a pure
function of (contacts, client) with no entanglement to any bridge or
pipeline state -- it can be deleted outright, or later promoted to the
PRIMARY mapper if the deterministic layer is ever retired (per the user's
standing provisional-mapping note on the S106 commit message). That
promotion is NOT built here -- this module only proves the rescue path
works correctly in isolation.

STANDALONE this step: nothing imports this module into the rules path yet
(no S109 wiring) -- this module and its test exist independently, wired
to nothing. It imports contact_mapper (for map_contact and the two
declared-verb tables) but nothing imports it back.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from agent.interpretive.contact_mapper import (
    _DISTINCT_VERB_TABLE,
    _JOIN_FAMILY_VERBS,
    map_contact,
)

if TYPE_CHECKING:
    from openai import OpenAI

logger = logging.getLogger(__name__)

# ─── LLM call configuration ──────────────────────────────────────────────
# THRESHOLD DISCIPLINE (CLAUDE.md Working Style #4).
# Starting pick, matching claim_extraction.py's _EXTRACTION_MODEL choice
# for a similarly-constrained classification task -- but UNVALIDATED for
# THIS task specifically: claim_extraction's choice was probe-confirmed
# for claim extraction (fh_stage1_probe_S69.md), not for closed-set verb
# classification. One-line tunable. Revisit trigger: a dedicated probe
# before S109 wiring, or the first live dogfood miss/quality complaint.
_FALLBACK_MODEL = "gpt-4o-mini"
_FALLBACK_TEMPERATURE = 0

# Same value as claim_extraction._EXTRACTION_TIMEOUT_SECONDS -- duplicated,
# NOT imported, same avoid-circular-import reasoning that module documents
# for its own duplication of palm_reading's timeout constant.
_FALLBACK_TIMEOUT_SECONDS = 30.0

_UNCLEAR = "unclear"


# ─── Closed choice set -- DERIVED, never hardcoded ───────────────────────
def _derive_closed_choice_set() -> tuple[str, ...]:
    """Every declared canonical verb contact_mapper can ever resolve --
    the exact union of _DISTINCT_VERB_TABLE's keys and
    _JOIN_FAMILY_VERBS's members, sorted for a stable, reproducible prompt
    string. Never hardcoded here: a verb added to (or removed from)
    either table in contact_mapper.py is picked up automatically the next
    time this module is imported, no edit needed here."""
    return tuple(sorted(set(_DISTINCT_VERB_TABLE) | set(_JOIN_FAMILY_VERBS)))


_CLOSED_CHOICE_SET: tuple[str, ...] = _derive_closed_choice_set()


# ─── Physical (NOT doctrinal) glosses -- one per declared verb ───────────
# Deliberately geometric/physical only ("what shape does this describe"),
# NEVER Cheiro's interpretive/doctrinal meaning of that shape -- honest
# silence: the LLM's job here is spelling/synonym resolution, not doctrine
# inference. A verb's doctrinal weight lives entirely in the rule engine
# (data/palm_rules/*.json), never surfaced to this module or its prompt.
_VERB_GLOSSES: dict[str, str] = {
    "crosses": "passes over or through the other line, continuing on its own path afterward",
    "crossed by": "the other line passes over or through this one (the passive direction of 'crosses')",
    "cuts": "passes across the other line, interrupting its continuity",
    "touches": "comes into contact at a single point, without crossing through or ending there",
    "takes possession of": "this line's ending is absorbed into the other line's path",
    "stopped by": "this line's course ends where it meets the other line",
    "barred by": "this line is blocked from continuing by the other line (same physical shape as 'stopped by')",
    "blocked by": "this line is prevented from continuing by the other line (same physical shape as 'stopped by')",
    "ends at": "this line terminates exactly at the other line or landmark",
    "branch": "a smaller offshoot line splits off from this line toward the other line or landmark",
    "branch in": "an offshoot line runs into the other line or landmark (same physical shape as 'branch')",
    "branch from": "an offshoot originates FROM the other line, running toward this one",
    "joins from": "an offshoot comes in from the other line and joins this one",
    "joins": "the two lines' paths come together and continue as one, or meet at a shared point",
    "merges": "the two lines blend together into one path (same physical shape as 'joins')",
    "merges with": "the two lines blend together into one path (same physical shape as 'joins', explicit partner)",
    "starts together": "both lines begin from the same point of origin",
    "starts from": "this line's own origin point is at the other line or landmark",
    "meets": "the two lines come together at a point, not necessarily at either one's start",
}

# Fail-closed sanity check at import time (mirrors contact_mapper.py's own
# _unknown_tokens guard): every verb in the derived closed choice set MUST
# have a gloss, and every gloss MUST correspond to a still-declared verb --
# a future verb added to (or removed from) contact_mapper's tables without
# a matching update here must block import, not silently ship a stale or
# incomplete choice set to the LLM.
_missing_glosses = [v for v in _CLOSED_CHOICE_SET if v not in _VERB_GLOSSES]
if _missing_glosses:
    raise RuntimeError(
        f"contact_llm_fallback: closed choice set verb(s) {sorted(_missing_glosses)} "
        "have no entry in _VERB_GLOSSES -- add a short, physical (non-doctrinal) "
        "gloss for each before this module can be imported."
    )
_stale_glosses = [v for v in _VERB_GLOSSES if v not in _CLOSED_CHOICE_SET]
if _stale_glosses:
    raise RuntimeError(
        f"contact_llm_fallback: _VERB_GLOSSES has entry/entries {sorted(_stale_glosses)} "
        "no longer present in the derived closed choice set -- contact_mapper's "
        "tables have diverged from this module's gloss dict; remove the stale "
        "gloss(es) or reconcile the drift."
    )


def _build_system_prompt() -> str:
    """Builds the fixed system-prompt text (identical every call -- no
    per-batch content lives here, only the closed choice set + glosses,
    which are import-time constants). Kept as a function rather than a
    module-level string purely so the choice-set/gloss substitution stays
    provably in sync with _CLOSED_CHOICE_SET at call time (mirrors this
    project's existing precedent, e.g. palm_processor._build_description_
    system_prompt, for the same reason: a substituted constant is
    trivially unit-tested for drift, a static literal is not)."""
    glossed_lines = "\n".join(
        f'- "{verb}": {_VERB_GLOSSES[verb]}' for verb in _CLOSED_CHOICE_SET
    )
    return (
        "You are matching unfamiliar verbs from hand-observation notes to "
        "the closest term in a FIXED list of physical relationship "
        "descriptions. This is a pure vocabulary-matching task, not "
        "palmistry interpretation -- you are choosing which listed term "
        "describes the SAME PHYSICAL SHAPE as the given verb, nothing "
        "more.\n\n"
        "Below is the complete list of terms you may choose from, each "
        "with a short physical description of what it means "
        "geometrically (NOT what it means in palmistry):\n\n"
        f"{glossed_lines}\n\n"
        "For each numbered verb in the user message, respond with EXACTLY "
        "ONE of the terms above, written verbatim exactly as shown "
        "(including any spaces), or the word \"unclear\" if none of them "
        "clearly describes the same physical relationship.\n\n"
        "Rules:\n"
        "- Choose ONLY from the list above -- never invent a new term or "
        "modify one.\n"
        "- If you are not confident, answer \"unclear\" rather than "
        "guessing.\n"
        "- Do not consider palmistry meaning, fortune, or doctrine -- "
        "only the physical shape of the relationship the verb describes.\n\n"
        "Respond with ONLY a JSON object of this exact shape:\n"
        '{"resolutions": ["<term-or-unclear>", "<term-or-unclear>", ...]}\n'
        "The list must have EXACTLY as many entries as there are numbered "
        "verbs in the user message, in the same order."
    )


def _build_user_prompt(batch_contacts: list[dict]) -> str:
    """Builds the per-batch user-prompt text: one numbered line per
    contact, showing ONLY its raw verb -- deliberately no target, no
    position, no clarity. The LLM's ONLY job is verb-to-verb synonym
    matching (see the module docstring's INDIRECTION note); withholding
    target/position keeps the task maximally narrow and prevents any
    temptation to infer a relationship's meaning from context it was
    never asked to judge."""
    lines = "\n".join(
        f'{i}. "{c.get("verb")}"' for i, c in enumerate(batch_contacts, start=1)
    )
    return f"Match each of the following {len(batch_contacts)} verb(s):\n\n{lines}"


def _call_llm(client, messages: list[dict]) -> str:
    """Mirrors claim_extraction._call_llm's shape exactly (same call
    signature, same response_format contract) -- single try/except
    boundary around one API call, raises the underlying exception to the
    caller, which owns the fail-closed decision."""
    response = client.chat.completions.create(
        model=_FALLBACK_MODEL,
        messages=messages,
        temperature=_FALLBACK_TEMPERATURE,
        timeout=_FALLBACK_TIMEOUT_SECONDS,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


def _already_resolved_result(pre: dict) -> dict:
    return dict(pre)


def _already_resolved_audit(pre: dict) -> dict:
    return {
        "raw_verb": pre["raw_verb"],
        "target": pre["target"],
        "position": pre["position"],
        "llm_canonical_choice": None,
        "final_token": pre["token"],
        "disposition": "already_resolved_no_llm_needed",
    }


def _batch_failure_result(contact: dict, reason: str) -> dict:
    return {
        "token": None,
        "confidence": None,
        "raw_verb": contact.get("verb") if isinstance(contact, dict) else None,
        "target": contact.get("target") if isinstance(contact, dict) else None,
        "position": contact.get("position") if isinstance(contact, dict) else None,
        "reason": reason,
    }


def _batch_failure_audit(contact: dict, disposition: str) -> dict:
    return {
        "raw_verb": contact.get("verb") if isinstance(contact, dict) else None,
        "target": contact.get("target") if isinstance(contact, dict) else None,
        "position": contact.get("position") if isinstance(contact, dict) else None,
        "llm_canonical_choice": None,
        "final_token": None,
        "disposition": disposition,
    }


def resolve_unresolved_contacts(
    contacts: list[dict], client: "OpenAI"
) -> tuple[list[dict], list[dict]]:
    """Batched LLM synonym-resolution rescue path -- see the module
    docstring for the full design (INDIRECTION, DEFENSIVE RE-VALIDATION,
    BATCHED, FAIL-CLOSED, OUTPUT CONTRACT).

    Returns (results, audits), each the same length and order as
    `contacts`. Never raises: every failure mode (API error, malformed
    JSON, hallucinated choice, "unclear") resolves to a token=None result
    with a traceable reason, never propagates an exception to the
    caller."""
    if not contacts:
        return [], []

    results: list[dict | None] = [None] * len(contacts)
    audits: list[dict | None] = [None] * len(contacts)
    still_unresolved_idx: list[int] = []

    for i, contact in enumerate(contacts):
        pre = map_contact(contact)
        if pre["token"] is not None:
            results[i] = _already_resolved_result(pre)
            audits[i] = _already_resolved_audit(pre)
        else:
            still_unresolved_idx.append(i)

    if not still_unresolved_idx:
        return results, audits  # type: ignore[return-value]  -- every slot filled above

    batch_contacts = [contacts[i] for i in still_unresolved_idx]

    try:
        raw = _call_llm(client, [
            {"role": "system", "content": _build_system_prompt()},
            {"role": "user", "content": _build_user_prompt(batch_contacts)},
        ])
    except Exception as exc:  # noqa: BLE001 -- one bad call must not crash a reading; whole batch -> unclear
        logger.error(
            "contact_llm_fallback: API call failed for a %d-contact batch "
            "(%s: %s) -- whole batch resolved to unclear.",
            len(batch_contacts), type(exc).__name__, exc,
        )
        reason = f"llm_fallback: batch API call failed ({type(exc).__name__}: {exc})"
        for idx in still_unresolved_idx:
            results[idx] = _batch_failure_result(contacts[idx], reason)
            audits[idx] = _batch_failure_audit(contacts[idx], "batch_call_failed")
        return results, audits  # type: ignore[return-value]

    try:
        parsed = json.loads(raw)
        resolutions = parsed["resolutions"]
        if not isinstance(resolutions, list) or len(resolutions) != len(batch_contacts):
            raise ValueError(
                f"expected a list of exactly {len(batch_contacts)} resolutions, "
                f"got {resolutions!r}"
            )
    except Exception as exc:  # noqa: BLE001 -- malformed response must not crash; whole batch -> unclear
        logger.error(
            "contact_llm_fallback: malformed response for a %d-contact "
            "batch (%s: %s) -- whole batch resolved to unclear. raw=%r",
            len(batch_contacts), type(exc).__name__, exc, raw,
        )
        reason = f"llm_fallback: malformed batch response ({type(exc).__name__}: {exc})"
        for idx in still_unresolved_idx:
            results[idx] = _batch_failure_result(contacts[idx], reason)
            audits[idx] = _batch_failure_audit(contacts[idx], "batch_malformed_response")
        return results, audits  # type: ignore[return-value]

    for idx, contact, choice in zip(still_unresolved_idx, batch_contacts, resolutions):
        canonical = choice.strip() if isinstance(choice, str) else None

        if canonical is None or canonical.lower() == _UNCLEAR:
            results[idx] = _batch_failure_result(
                contact,
                f"llm_fallback: {contact.get('verb')!r} -> unclear "
                "(LLM found no matching known synonym)",
            )
            audits[idx] = {
                "raw_verb": contact.get("verb"), "target": contact.get("target"),
                "position": contact.get("position"),
                "llm_canonical_choice": choice if isinstance(choice, str) else None,
                "final_token": None, "disposition": "llm_unclear",
            }
            continue

        if canonical not in _CLOSED_CHOICE_SET:
            logger.warning(
                "contact_llm_fallback: LLM returned %r for raw_verb=%r -- "
                "not in the closed choice set, treated as a hallucination "
                "(unclear).",
                canonical, contact.get("verb"),
            )
            results[idx] = _batch_failure_result(
                contact,
                f"llm_fallback: {contact.get('verb')!r} -> hallucinated "
                f"canonical {canonical!r} not in closed choice set -- "
                "treated as unclear",
            )
            audits[idx] = {
                "raw_verb": contact.get("verb"), "target": contact.get("target"),
                "position": contact.get("position"),
                "llm_canonical_choice": canonical,
                "final_token": None, "disposition": "hallucination",
            }
            continue

        # Re-run the DETERMINISTIC mapper with raw_verb swapped to the
        # LLM's canonical choice -- token/cardinality/position-split stay
        # 100% deterministic, re-validated by the same tables every other
        # contact goes through.
        re_contact = dict(contact)
        re_contact["verb"] = canonical
        mapped = map_contact(re_contact)
        mapped["raw_verb"] = contact.get("verb")  # ALWAYS the original, verbatim

        if mapped["token"] is not None:
            mapped["reason"] = (
                f"llm_fallback: {contact.get('verb')!r} -> {canonical!r} -> "
                f"{mapped['token']}"
            )
            disposition = "resolved"
        else:
            mapped["reason"] = (
                f"llm_fallback: {contact.get('verb')!r} -> {canonical!r}, "
                f"but position-split still unresolved: {mapped['reason']}"
            )
            disposition = "position_unresolved"

        results[idx] = mapped
        audits[idx] = {
            "raw_verb": contact.get("verb"), "target": contact.get("target"),
            "position": contact.get("position"),
            "llm_canonical_choice": canonical,
            "final_token": mapped["token"], "disposition": disposition,
        }

    return results, audits  # type: ignore[return-value]
