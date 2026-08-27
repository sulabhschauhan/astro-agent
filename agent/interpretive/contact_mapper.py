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

DETERMINISTIC INFLECTION NORMALIZATION (S106, removable stage -- see the
module-level comment above `_INFLECTION_MAP`): before falling through to
token=None, an UNRECOGNIZED verb is retried once against its regular
tense/aspect siblings (joined/joining -> joins, touched/touching ->
touches, ...), generated at import time from the declared vocabulary
itself. This closes the exact gap that aborted S104 Step 5b -- live
vision reporting "joined" (past tense) where only "joins" (base form) was
declared -- without widening what counts as a resolvable verb beyond
genuine tense/aspect variants of an already-declared word. Still NO LLM,
still never guesses: a genuine synonym not derived from any declared verb
(e.g. "fuses") still falls through to token=None, same as before S106.

STANDALONE this step: nothing imports this module into the rules path yet
(that is Step 5) -- this module and its test exist independently, wired to
nothing.
"""

from __future__ import annotations

import logging

from agent.interpretive.observation_extractor import _RELATIONSHIP_TOKENS as _TOKEN_VOCAB

logger = logging.getLogger(__name__)

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


# ─── S106: deterministic inflection normalization (removable stage) ──────
# Expands every SINGLE-WORD declared verb (from _DISTINCT_VERB_TABLE keys
# and _JOIN_FAMILY_VERBS) into its regular English tense/aspect siblings
# (3rd-person -s/-es, past -ed, gerund -ing) and builds _INFLECTION_MAP:
# {generated_form: canonical_declared_form}. Multi-word entries ("crossed
# by", "merges with", "takes possession of", ...) are NOT expanded -- they
# stay exact-match only, unchanged.
#
# GENERATE-THE-FORMS, not stem-the-input: rather than trying to reduce an
# arbitrary live verb string down to some inferred lemma, this derives
# each declared verb's own stem ONCE at import (regular-suffix reversal
# only) and forward-generates its sibling surface forms -- the set of
# forms this module will ever recognize is fixed and auditable at import
# time, never computed per-call.
#
# REMOVABLE IN ONE PIECE: delete this whole section (down through
# `_INFLECTION_MAP`) and the small consult block inside map_contact that
# reads it, and the module reverts to pre-S106, exact-match-only behavior
# with zero other change.
#
# Hand-rolled regular-suffix rules only (no NLP library, no irregular-verb
# table) -- REGULAR verbs only, per the S104/S105 declared vocabulary.
# KNOWN, ACCEPTED LIMITATION: "meet" and "cut" are irregular in real
# English (met/cut, not meeted/cutted) -- this module's -ed generation
# still produces the (linguistically wrong) regular form for those two,
# since detecting irregularity would need an irregular-verb table this
# design deliberately excludes. This affects ONLY the -ed form for those
# two verbs; -ing ("meeting"/"cutting") is unaffected and correct. A live
# "met" or bare "cut" past-tense report still falls through honestly to
# token=None -- a known gap, never silently masked as a guess.
_VOWELS = frozenset("aeiou")


def _derive_stem(declared: str) -> str:
    """Reverses a declared verb's own suffix back to its bare stem, by
    regular-suffix rule only: a sibilant -es (cross/crosses, touch/
    touches) strips 2 chars; a lone trailing -s (join/joins, merge/
    merges, meet/meets, cut/cuts) strips 1; anything else is already bare
    (branch)."""
    if declared.endswith("es") and declared[:-2].endswith(("s", "x", "z", "ch", "sh")):
        return declared[:-2]
    if declared.endswith("s"):
        return declared[:-1]
    return declared


def _has_short_final_consonant(stem: str) -> bool:
    """CVC doubling check (cut -> cutting): a single final consonant, not
    in {w, x, y}, immediately preceded by exactly ONE vowel letter -- the
    letter before THAT vowel must not also be a vowel, which rules out
    digraphs like "join"/"meet" (joined/meeting, never joinned/meetting)."""
    if len(stem) < 3:
        return False
    last, second, third = stem[-1], stem[-2], stem[-3]
    if last in _VOWELS or last in ("w", "x", "y"):
        return False
    if second not in _VOWELS:
        return False
    if third in _VOWELS:
        return False
    return True


def _s_form(stem: str) -> str:
    if stem.endswith(("s", "x", "z", "ch", "sh")):
        return stem + "es"
    return stem + "s"


def _ed_form(stem: str) -> str:
    if stem.endswith("e"):
        return stem + "d"
    if _has_short_final_consonant(stem):
        return stem + stem[-1] + "ed"
    return stem + "ed"


def _ing_form(stem: str) -> str:
    if stem.endswith("e"):
        return stem[:-1] + "ing"
    if _has_short_final_consonant(stem):
        return stem + stem[-1] + "ing"
    return stem + "ing"


def _generate_inflections(declared: str) -> tuple[str, str, str] | None:
    """Returns (s_form, ed_form, ing_form) generated FROM the declared
    verb's own derived stem, or None if a self-consistency check fails
    (the regenerated s-form doesn't reproduce the declared form, meaning
    _derive_stem got this verb wrong) -- logged and skipped by the
    caller, NEVER raised, per this module's fail-open-per-verb contract
    ("if a declared verb ever fails to inflect cleanly, log it at import,
    skip it"). The self-check only applies when `declared` itself ends in
    -s (i.e. stem-derivation actually stripped something); a bare
    declared form (e.g. "branch") has nothing to self-verify against."""
    stem = _derive_stem(declared)
    s_form, ed_form, ing_form = _s_form(stem), _ed_form(stem), _ing_form(stem)
    if stem != declared and s_form != declared:
        logger.warning(
            "contact_mapper: inflection self-check failed for declared "
            "verb %r -- derived stem %r regenerates %r, not %r. Skipping "
            "inflection generation for this verb (fail-open to exact-"
            "match only, unchanged pre-S106 behavior for it).",
            declared, stem, s_form, declared,
        )
        return None
    return s_form, ed_form, ing_form


def _build_inflection_map() -> dict[str, str]:
    """Builds {generated_form: canonical_declared_form} for every SINGLE-
    WORD key in _DISTINCT_VERB_TABLE and _JOIN_FAMILY_VERBS (multi-word
    keys are skipped entirely -- exact-match only, unchanged). Two
    fail-closed guards, both RAISE at import time (never silently
    resolved): (1) a generated form that would map to two DIFFERENT
    canonical verbs -- a genuine ambiguity; (2) a generated form that
    collides with an EXISTING exact single-word table key -- silent
    shadowing of the exact tables. The declared form's own regenerated
    s-form is never added to the map (redundant -- the exact tables
    already match it directly). The bare -ed active form is suppressed
    per-verb when its passive "<-ed> by" form is itself a declared
    multi-word key -- the COLLISION GUARD: "crossed" would otherwise be
    genuinely ambiguous with the declared "crossed by" -> cut_by; an
    ambiguous bare "crossed" must stay an honest token=None, never be
    guessed as active cuts."""
    single_word_declared = [
        v for v in list(_DISTINCT_VERB_TABLE) + list(_JOIN_FAMILY_VERBS)
        if " " not in v
    ]
    exact_single_word_keys = frozenset(single_word_declared)

    inflection_map: dict[str, str] = {}
    for declared in single_word_declared:
        forms = _generate_inflections(declared)
        if forms is None:
            continue
        s_form, ed_form, ing_form = forms

        candidates = [ing_form]
        if s_form != declared:
            candidates.append(s_form)
        if f"{ed_form} by" not in _DISTINCT_VERB_TABLE:
            candidates.append(ed_form)
        else:
            logger.info(
                "contact_mapper: suppressed generated bare form %r for "
                "declared verb %r -- %r is a declared passive multi-word "
                "key; an ambiguous bare form must fall through to "
                "token=None, never be guessed active.",
                ed_form, declared, f"{ed_form} by",
            )

        for form in candidates:
            if form == declared:
                continue
            if form in exact_single_word_keys:
                raise RuntimeError(
                    f"contact_mapper: generated inflected form {form!r} "
                    f"(from declared verb {declared!r}) collides with an "
                    "EXISTING exact single-word table key -- silent "
                    "shadowing of the exact tables is not allowed."
                )
            existing = inflection_map.get(form)
            if existing is not None and existing != declared:
                raise RuntimeError(
                    f"contact_mapper: generated inflected form {form!r} "
                    f"is ambiguous between declared verbs {existing!r} "
                    f"and {declared!r} -- refusing to silently pick one."
                )
            inflection_map[form] = declared

    return inflection_map


_INFLECTION_MAP: dict[str, str] = _build_inflection_map()


def _lookup_exact(verb: str, raw_verb, target, position) -> dict | None:
    """The pre-S106 exact-match resolution body (distinct-verb table,
    then join-family + position split), extracted verbatim so
    map_contact can retry it once with an inflection-normalized verb
    without duplicating this logic. Returns None when `verb` matches
    neither table -- the ONLY behavioral difference from the pre-S106
    inline version is that this non-match is now returnable instead of
    falling straight through to the final unknown-verb dict; every
    branch's returned content is otherwise byte-identical to what
    map_contact returned inline before S106."""
    if verb in _DISTINCT_VERB_TABLE:
        return {
            "token": _DISTINCT_VERB_TABLE[verb],
            "confidence": "high",
            "raw_verb": raw_verb,
            "target": target,
            "position": position,
            "reason": None,
        }

    if verb in _JOIN_FAMILY_VERBS:
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

    return None


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
    'at end' at reduced confidence; (3) S106: ONLY if neither exact table
    matched, the verb is normalized through the generated
    `_INFLECTION_MAP` to its declared canonical form and (1)/(2) are
    retried once with that form -- so "crossed by"/"merges with" and
    every other exact (including multi-word) entry always wins verbatim
    before any inflection normalization is even attempted; (4) anything
    still unresolved -- a genuine unrecognized verb, or a join-family verb
    (exact or inflection-normalized) whose position is 'unknown' or
    otherwise unresolvable -- returns token=None with a reason, never a
    guess.

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

    exact = _lookup_exact(verb_norm, raw_verb, target, position)
    if exact is not None:
        return exact

    # S106: inflection fallback -- reached ONLY when verb_norm matched
    # neither exact table above. Maps a tense/aspect variant (e.g.
    # "joined") to its declared canonical form (e.g. "joins") and retries
    # the SAME exact lookup once with that canonical form -- never
    # invents new resolution logic, never touches position/token
    # handling, purely a verb-spelling normalization pass. Removable in
    # one piece: delete _INFLECTION_MAP (and its builder, above) and this
    # block to revert to pre-S106, exact-match-only behavior with zero
    # other change.
    canonical_verb = _INFLECTION_MAP.get(verb_norm)
    if canonical_verb is not None:
        inflected = _lookup_exact(canonical_verb, raw_verb, target, position)
        if inflected is not None:
            return inflected

    return {
        "token": None,
        "confidence": None,
        "raw_verb": raw_verb,
        "target": target,
        "position": position,
        "reason": f"unknown verb {raw_verb!r} -- not in the distinct-verb table or join family",
    }
