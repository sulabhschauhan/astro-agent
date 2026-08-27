"""
agent/interpretive/contact_mapper.py

Deterministic verb+position -> Cheiro-token mapper (S104 Step 4). Maps one
parsed contact ({"target", "verb", "position", "clarity"}, the shape
observation_extractor.extract_relations' isolated "contacts" namespace
produces, S104 Step 3) onto the closed 8-token typed-relationship
vocabulary (joins_at_origin/meets/cuts/cut_by/touches/stopped_by/
takes_possession_of/branch_in).

NO LLM. A hardcoded verb table handles every verb whose token is
unambiguous regardless of where along the line the contact happens
("crosses" always means cuts); a SEPARATE, position-dependent split
handles the "join family" of verbs ("joins"/"merges"/"merges with"/
"starts together"/"starts from"/"meets") that are genuinely ambiguous
between joins_at_origin and meets without knowing WHERE the contact
happens -- position is the disambiguating signal there, not the verb text.
Anything that doesn't resolve (unknown verb, or a join-family verb with an
unresolvable position) returns token=None with a reason string -- the
caller quarantines it. This module NEVER guesses.

STANDALONE this step: nothing imports this module into the rules path yet
(that is Step 5) -- this module and its test exist independently, wired to
nothing.
"""

from __future__ import annotations

from agent.interpretive.observation_extractor import _RELATIONSHIP_TOKENS as _TOKEN_VOCAB

# ─── Distinct verbs -- position-independent, one verb = one token ─────────
_DISTINCT_VERB_TABLE: dict[str, str] = {
    "crosses": "cuts",
    "crossed by": "cut_by",
    "cuts": "cuts",
    "touches": "touches",
    "takes possession of": "takes_possession_of",
    "stopped by": "stopped_by",
    "barred by": "stopped_by",
    "blocked by": "stopped_by",
    "ends at": "stopped_by",
    "branch": "branch_in",
    "branch in": "branch_in",
    "branch from": "branch_in",
    "joins from": "branch_in",
}

# ─── Join family -- position-dependent; verb text alone is NOT trusted to
# distinguish joins_at_origin from meets, even when the verb is literally
# "meets" -- position is the authoritative signal for this family. ────────
_JOIN_FAMILY_VERBS: frozenset[str] = frozenset({
    "joins", "merges", "merges with", "starts together", "starts from", "meets",
})

# position -> (token, confidence). "at end" is intentionally low-confidence
# (a line meeting another at its own end reads as being stopped by it, but
# this is an inference, not a direct verb match) -- "unknown" is
# deliberately ABSENT from this table: a join-family verb with unresolvable
# position has no entry here and falls through to the UNRESOLVABLE
# quarantine path below, never a guessed token.
_POSITION_TO_JOIN_TOKEN: dict[str, tuple[str, str]] = {
    "at start": ("joins_at_origin", "high"),
    "mid-course": ("meets", "high"),
    "at end": ("stopped_by", "low"),
}

# Fail-closed sanity check at import time: every token this module's verb
# table can ever produce must be a member of the registry-derived 8-token
# vocabulary (imported directly from observation_extractor, not
# re-hardcoded here) -- catches registry/verb-table drift immediately
# rather than silently emitting an off-vocabulary token downstream.
_used_tokens: frozenset[str] = frozenset(_DISTINCT_VERB_TABLE.values()) | frozenset(
    tok for tok, _confidence in _POSITION_TO_JOIN_TOKEN.values()
)
_unknown_tokens = _used_tokens - _TOKEN_VOCAB
if _unknown_tokens:
    raise RuntimeError(
        f"contact_mapper: verb table references token(s) {sorted(_unknown_tokens)} "
        f"not in the registry-derived 8-token vocabulary {sorted(_TOKEN_VOCAB)} -- "
        "registry and verb table have diverged."
    )


def map_contact(contact: dict) -> dict:
    """Maps one parsed contact dict onto the closed 8-token vocabulary.

    Returns `{"token": <one of the 8 tokens, or None>, "confidence":
    "high"|"low"|None, "raw_verb": <verbatim, unmodified>, "target": <the
    contact's own target, passed through untouched>, "position": <the
    contact's own position, passed through untouched>, "reason": <why,
    populated whenever token is None, otherwise None>}`.

    `clarity` is NOT read, filtered on, or echoed here -- whether a faint
    contact should be dropped is a caller decision (Step 5's job, per
    instruction), not this mapper's. Callers that need it already have the
    original contact dict.

    Resolution order: (1) an exact distinct-verb match is direct and
    position-independent; (2) a join-family verb is split by position,
    'at end' at reduced confidence; (3) anything else -- an unrecognized
    verb, or a join-family verb whose position is 'unknown' or otherwise
    unresolvable -- returns token=None with a reason, never a guess.

    Never raises: a malformed `contact` (not a dict, or missing the "verb"
    key) is itself treated as unresolvable and returns token=None with a
    reason describing the malformation."""
    try:
        if not isinstance(contact, dict):
            raise TypeError(f"contact must be a dict, got {type(contact).__name__}")
        if "verb" not in contact:
            raise KeyError("verb")
        raw_verb = contact["verb"]
        target = contact.get("target")
        position = contact.get("position")
        verb_norm = str(raw_verb).strip().lower()
    except Exception as exc:  # noqa: BLE001 -- malformed input must quarantine, never raise
        return {
            "token": None,
            "confidence": None,
            "raw_verb": contact.get("verb") if isinstance(contact, dict) else None,
            "target": contact.get("target") if isinstance(contact, dict) else None,
            "position": contact.get("position") if isinstance(contact, dict) else None,
            "reason": f"malformed contact: {exc}",
        }

    if verb_norm in _DISTINCT_VERB_TABLE:
        return {
            "token": _DISTINCT_VERB_TABLE[verb_norm],
            "confidence": "high",
            "raw_verb": raw_verb,
            "target": target,
            "position": position,
            "reason": None,
        }

    if verb_norm in _JOIN_FAMILY_VERBS:
        position_norm = str(position).strip().lower() if position is not None else "unknown"
        if position_norm in _POSITION_TO_JOIN_TOKEN:
            token, confidence = _POSITION_TO_JOIN_TOKEN[position_norm]
            return {
                "token": token,
                "confidence": confidence,
                "raw_verb": raw_verb,
                "target": target,
                "position": position,
                "reason": None,
            }
        return {
            "token": None,
            "confidence": None,
            "raw_verb": raw_verb,
            "target": target,
            "position": position,
            "reason": (
                f"join-family verb {raw_verb!r} has unresolvable position "
                f"{position!r} -- cannot split joins_at_origin vs meets "
                "without a known position"
            ),
        }

    return {
        "token": None,
        "confidence": None,
        "raw_verb": raw_verb,
        "target": target,
        "position": position,
        "reason": f"unknown verb {raw_verb!r} -- not in the distinct-verb table or join family",
    }
