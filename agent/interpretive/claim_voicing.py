"""
agent/interpretive/claim_voicing.py
S69 F-H Stage 2 -- closed-inventory voice pass over Stage 1's extracted claims.

CITATION: CLAUDE.md S69 queue's F-H entry (two-stage extract-then-voice
redesign). Stage 1 is `agent/interpretive/claim_extraction.py` (P1):
per-feature claim extraction directly from gated chunks, paraphrase-or-
nothing. THIS module is Stage 2: it never sees a retrieved chunk's text
at all -- only the CLOSED INVENTORY of `Claim` objects Stage 1 already
extracted and validated (chunk_id, valence, condition_text are all
Stage-1-owned fields; this module reads claim_id/claim_text/valence/
observation_basis only, per the module contract's explicit "NO chunk
text anywhere in the prompt" requirement). Voicing from a closed
inventory rather than free composition from raw chunks is the mechanism
this whole redesign exists for: Ring 3 pass 4 (`ring3_palm_rubric_S68_
pass4.md`) found single-call generation composes from the model's
pretraining prior first, retrieved doctrine second, making citations
decorative; a closed-inventory voice pass has no doctrine to compose
FROM except what's already in the inventory, foreclosing that failure
mode by construction (not merely discouraging it via prompt wording).

STEP 0 NOTE (per this prompt's own instruction, not re-derived here):
`diagnostics/fh_stage1_probe_S69.md`'s pooled content-word overlap
distribution (`min=0.50 p25=1.00 median=1.00 p75=1.00 max=1.00 (n=73)`)
is copied verbatim into `diagnostics/latest_run.md` for this session --
design chat ratifies `claim_extraction._PARAPHRASE_OVERLAP_FLOOR` (0.40)
against that line, not this module, which does not use that constant at
all (Stage 2 never re-checks Stage 1's overlap floor; it trusts Stage 1's
already-validated `Claim.claim_text` as its ONLY interpretive-content
source).

INPUT FILTER (Python, deterministic, before any LLM call):
  - `Claim.excluded_from_voice=True` claims are dropped entirely -- never
    reach the prompt. These are Stage 1's own E-4 fail-closed claims
    (unverified preconditions); Stage 2 has no additional information
    that could rehabilitate one, so re-litigating them here would be
    pointless at best and a second, less-informed fail-open risk at
    worst.
  - Corrective-valence claims are capped at 1 per reading (`kept first
    in claim_id order`, i.e. ascending numeric order of the module-owned
    counter Stage 1 assigned -- NOT a re-sort by any other field). Excess
    correctives land in `diagnostics["corrective_overflow"]`, never in
    the prompt. Stage 1's own docstring already flagged this as a
    deferred decision ("Stage-2 owns the one-per-reading cap -- do not
    implement it here"); implemented here now. Justification (THRESHOLD
    DISCIPLINE, CLAUDE.md Working Style #4): more than one corrective
    voiced in the same reading reads as a barrage of hedges/corrections
    rather than confident Cheiro-register assertions -- a voice/UX
    judgment call, not an empirically-measured threshold (unlike the
    0.30 support floor or the 0.40 paraphrase floor, no probe measured
    this). Scope guard: correctives only, never supports/surviving-
    conditionals (no cap on those). Revisit trigger: Ring 3 evidence that
    1 is too restrictive or not restrictive enough.

PROMPT: Cheiro voice register (the "## Voice" block below was ORIGINALLY
TRANSPLANTED near-verbatim from `palm_reading._READING_SYSTEM_PROMPT`'s
own "## Voice" section -- same forbidden self-help word list; the "must
come from" clause was adapted at that transplant, since Stage 2 has no
retrieved passages to point to, only the claim inventory. S70 F-G3:
the two verbatim exemplar sentences the block originally ALSO shared with
`palm_reading._EXEMPLAR_SENTENCES` are since DELETED, replaced with
descriptive-only voice attributes -- see the constant's own comment for
the full diff/reason) + a numbered CLOSED claim inventory (claim_id,
claim_text, valence, observation_basis) + confirmed observations. Chunk
text/chunk_id never appears anywhere in the prompt by construction (this
module never reads `Claim.chunk_id` at all).

MODEL CHOICE (3-place registration, this docstring is place 2 of 3 --
place 1 is `_VOICE_MODEL`'s own THRESHOLD DISCIPLINE comment, place 3 is
CLAUDE.md's S69 F-H close-out entry): `_VOICE_MODEL = "gpt-4o"` is an
UNTESTED design choice, unlike `claim_extraction._EXTRACTION_MODEL`'s
probe-validated `gpt-4o-mini` pick -- `fh_stage1_probe_S69.md` measured
Stage-1 extraction quality only, never Stage-2 voice/register quality. A
dedicated Stage-2 voice probe is a future candidate, not attempted here.

VALIDATORS (deterministic Python, run in order -- V-4/V-5 only evaluated
if V-3 passes, since tag POSITIONS must be trustworthy before either can
mean anything; same "whole-response rejected on any tier's violation"
philosophy as claim_extraction.py's E-1/E-2/E-3):
  - V-3 tag legality: every sentence ends in exactly one recognized tag
    ({[C<n>], [OBS], [FLOW]}); every [C<n>] resolves to an INCLUDED
    claim_id (post-filter); no other bracket token appears anywhere.
    KNOWN GAP (same class as palm_reading.py's own accepted gap (b)): an
    untagged sentence sandwiched BETWEEN two valid tags is not caught --
    only whole-text-untagged and trailing-residue are decidable from tag
    positions alone without a banned sentence-splitter.
  - V-4 claim coverage: every INCLUDED claim_id (post-filter, i.e. what
    was actually offered to Stage 2) is cited by >=1 [C<n>] tag in the
    final draft.
  - V-5 [FLOW]/[OBS] doctrine guard: reuses `palm_reading._SUPPORT_
    NEEDLES` (the per-feature trait-noun dictionary) as the SAME single
    source of truth for "does this sentence name a palm feature's own
    significance-bearing noun" -- TRANSPLANTED here (`_FEATURE_TRAIT_
    NEEDLES`, cited, not imported: importing `palm_reading` from this
    module would create a circular import once `palm_reading.py` wires
    THIS module in, the same reasoning `claim_extraction.py`'s own
    `_EXTRACTION_TIMEOUT_SECONDS` comment already documents). ANY needle
    hit in a [FLOW] or [OBS] segment fails -- deliberately coarse, by
    design, not a false-negative-optimized classifier. ACCEPTED GAP,
    3-place registration (CLAUDE.md's own convention): this module
    docstring + the validator's own code comment are places 2 and 3;
    place 1 (a CLAUDE.md Known-Source-Divergences entry) is NOT added
    here -- that is the F-H close-out prompt's job, flagged in this
    prompt's own report to diagnostics/latest_run.md.

F2c: single retry, failures fed back as a correction instruction (same
pattern as palm_reading.py's own S66 F2c retry / claim_extraction.py's
own per-feature retry), hard 2-call cap. A retry that STILL fails
validation returns a POPULATED `validation_failures` tuple rather than
raising -- fail-closed disposition is the CALLER's job (P5 wiring):
`voice_claims` itself never decides whether to display; a non-empty
`validation_failures` is the signal a caller must check and refuse
display on, mirroring `palm_reading.PalmReadingResult.validation.passed`.

ERRORS: an API exception on EITHER call (first attempt or retry) raises
RuntimeError with a module-prefixed message -- this is a single whole-
reading call, not a per-feature loop, so there is no partial-success
fallback the way claim_extraction.py has across multiple features; one
failed call here means the whole voice pass failed.

SCOPE: this module does not import palm_reading (see the V-5 comment
above) or agent.infra.calc_router/orchestrator/chart_profile, matching
the project's existing upload-triggered-artifact scope lock. No file
writes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.interpretive.claim_extraction import Claim

# ─── LLM call configuration ─────────────────────────────────────────────

# THRESHOLD DISCIPLINE (CLAUDE.md Working Style #4).
# Justification: register quality -- Stage 2's ENTIRE job is voice/tone
# fidelity in Cheiro's register, the one dimension fh_stage1_probe_S69.md
# never measured (that probe scored Stage-1 EXTRACTION quality only,
# gpt-4o vs gpt-4o-mini, and found no difference there). No probe has yet
# measured whether gpt-4o-mini reaches parity on VOICE quality
# specifically -- this is an UNTESTED design choice, not probe-validated
# like claim_extraction.py's model pick. Scope guard: this module's voice
# call site only. Revisit trigger: Ring 3 pass-5 evidence (once wiring,
# P5, lands) that gpt-4o-mini reaches voice parity, or a dedicated Stage-2
# probe analogous to fh_stage1_probe_S69.md.
_VOICE_MODEL = "gpt-4o"

# THRESHOLD DISCIPLINE (CLAUDE.md Working Style #4).
# Justification: unchanged pending pass-5 evidence. CLAUDE.md's F-G entry
# (S69 queue) found the "stability" self-help-blacklist hits in the OLD
# single-call architecture were a composition-habit, not chunk-driven,
# and explicitly folds the retry-cap/temperature question into F-H's
# design rather than resolving it standalone -- this module's Stage-2
# closed-inventory voice pass has a fundamentally different failure
# surface than the old free-composition retry (F-G's own words), so
# temperature=0 is carried over unchanged here as a starting point, not a
# re-derived value. Scope guard: this call site only. Revisit trigger:
# pass-5 evidence that temp=0 voice output is degenerate for this task
# shape (same trigger class as palm_reading._READING_TEMPERATURE's own
# comment).
_VOICE_TEMPERATURE = 0

# Same value as palm_reading._READING_TIMEOUT_SECONDS -- duplicated, NOT
# imported, to avoid a circular import (palm_reading.py will import THIS
# module once wired, P5; this module must never import palm_reading
# back). Re-sync by hand if palm_reading.py's own timeout is ever
# revisited. Same reasoning as claim_extraction._EXTRACTION_TIMEOUT_
# SECONDS's own comment.
_VOICE_TIMEOUT_SECONDS = 30.0

# THRESHOLD DISCIPLINE -- see the module docstring's INPUT FILTER section
# for full justification (voice/UX judgment, not an empirically-measured
# threshold; Ring 3 is the revisit trigger).
_CORRECTIVE_CAP = 1

_CLAIM_ID_PATTERN = re.compile(r"^C(\d+)$")


def _claim_sort_key(claim: "Claim") -> int:
    """Ascending numeric order of Stage 1's own module-owned counter
    (claim_id = "C<n>") -- NOT a lexicographic string sort, which would
    misorder "C10" before "C2". Falls back to 0 for any claim_id that
    doesn't match the expected shape (defensive only; Stage 1 always
    produces this exact shape)."""
    m = _CLAIM_ID_PATTERN.match(claim.claim_id)
    return int(m.group(1)) if m else 0


# ─── Input filter ─────────────────────────────────────────────────────────


def _filter_claims_for_voice(claims: tuple["Claim", ...]) -> tuple[list["Claim"], dict]:
    """Drops excluded_from_voice claims; caps corrective-valence claims at
    _CORRECTIVE_CAP, keeping the first in ascending claim_id order and
    moving the rest to diagnostics["corrective_overflow"]. Returns
    (included_claims sorted by claim_id, filter_diagnostics)."""
    non_excluded = [c for c in claims if not c.excluded_from_voice]
    correctives = sorted(
        (c for c in non_excluded if c.valence == "corrective"), key=_claim_sort_key
    )
    others = [c for c in non_excluded if c.valence != "corrective"]

    kept_correctives = correctives[:_CORRECTIVE_CAP]
    overflow_correctives = correctives[_CORRECTIVE_CAP:]

    included = sorted(others + kept_correctives, key=_claim_sort_key)

    filter_diagnostics = {
        "excluded_count": len(claims) - len(non_excluded),
        "corrective_overflow": [c.claim_id for c in overflow_correctives],
        "included_claim_ids": [c.claim_id for c in included],
    }
    return included, filter_diagnostics


# ─── Voice system prompt -- "## Voice" ORIGINALLY TRANSPLANTED near- ────
# verbatim from palm_reading._READING_SYSTEM_PROMPT's own "## Voice"
# block: same declarative-register description, same forbidden self-help
# word list. ONE line was ADAPTED even at the original transplant (not
# copied): the source reads "Every interpretive claim in your actual
# reading must come from the provided passages and the confirmed hand
# description(s) below" -- Stage 2 has no retrieved passages at all, only
# the claim inventory, so that clause is replaced with "must come from
# the numbered CLAIM INVENTORY below".
#
# S70 F-G3 UPDATE: the two verbatim "model sentences" this block
# originally shared with palm_reading._EXEMPLAR_SENTENCES are DELETED,
# not merely reworded -- pass-5 preflight's post-F-G re-run
# (diagnostics/pass5_preflight_S70.md, commit 908d325) found the
# exemplar text itself, present verbatim in the system prompt as a
# tone-model, created a standing echo-gravity that F-G1/F-G2's retry-feed
# wiring could detect but not eliminate at the source. Replaced with
# purely DESCRIPTIVE voice attributes (warm/measured/first-person/plain-
# language/no-canned-openings) and an explicit "compose fresh" mandate --
# zero example or model sentences of any kind remain in this prompt, by
# design (anything quotable here is a fresh echo-source risk).
# palm_reading._READING_SYSTEM_PROMPT (the OLD, now-retired single-call
# prompt) and palm_reading._EXEMPLAR_SENTENCES /
# palm_reading._check_exemplar_echo (the STILL-LIVE outer display-check
# guard) are explicitly OUT OF SCOPE for this change and remain
# byte-identical -- this module no longer shares exemplar text with
# either of them.
_VOICE_SYSTEM_PROMPT = """You are a Cheiro-tradition palmist giving a single, one-shot spoken reading. You have been given a CLOSED INVENTORY of already-extracted claims -- voice ONLY these claims, in your own words, in Cheiro's register. You have NOT seen the source texts these claims came from; do not add, infer, or invent any interpretive content beyond what a claim's own text already states.

## Voice
Write in Cheiro's declarative register: direct, confident assertions in period-appropriate diction, addressed straight to the reader. This is a palmist reading a hand, not a therapist offering affirmation -- speak with the authority of someone who has read thousands of hands and states plainly what each one shows.
Voice attributes (descriptive guidance only -- there is no template or model sentence to imitate; compose everything fresh): warm but measured in tone, a practicing palmist speaking in the first person where natural, plain unadorned language rather than ornate or archaic diction, and no canned, formulaic, or recycled opening or closing device of any kind -- every opening, transition, and closing sentence must be composed fresh for this specific hand and this specific claim inventory, never a stock phrase or boilerplate line reused across readings. Every interpretive claim in your actual reading must come from the numbered CLAIM INVENTORY below.
FORBIDDEN words and phrasings (never use these, in any form): stability, fulfillment, fulfilling, favorable, journey, navigate, navigating, empower, empowerment, and any "this suggests you are the kind of person who..." self-help framing.

## How to voice a corrective claim
A claim marked valence="corrective" REJECTS or CONTRADICTS the natural reading of the observation it's attached to. Voice it as Cheiro's own considered correction -- a direct, confident statement of what is actually true -- never as a hedge, an apology, or a "however, some might say..." qualifier.

## Output format (voice tags)
Every sentence in your reading must end with exactly one tag, placed immediately after the sentence's closing punctuation with NO space before the bracket:
- "[C<n>]" -- for a sentence voicing claim C<n> from the inventory below. Copy the number EXACTLY as given. The sentence's interpretive content must come ONLY from that claim's own text -- never blend in a second claim's content or add anything beyond what the claim states.
- "[OBS]" -- for a sentence that only restates a confirmed observation, carrying no interpretive content of its own.
- "[FLOW]" -- for a pure connective or transition sentence (an opening, a closing, or a bridge between claims) that adds no new observation or interpretive content at all.
Tag every sentence, including the opening and closing ones. Never use any other bracketed token. These tags are machine-readable annotation only -- they are stripped before display, so they are not the "citations" any scope rule below forbids.

## Scope
Voice EVERY claim in the inventory below at least once. Do not mention, allude to, or interpret any palm feature that has no claim in the inventory. Do not cite book names, page numbers, or any source material -- you were never shown any.

## Length
Keep the reading focused -- do not pad with repeated restatements of the same claim."""


def _build_user_prompt(included_claims: list["Claim"], texts_by_feature: dict[str, str]) -> str:
    claim_lines = [
        f'{c.claim_id}: (valence: {c.valence}) "{c.claim_text}" -- observation: "{c.observation_basis}"'
        for c in included_claims
    ]
    claim_block = "\n".join(claim_lines) if claim_lines else "(none)"

    obs_lines = [f"- {feature}: {text}" for feature, text in texts_by_feature.items() if text]
    obs_block = "\n".join(obs_lines) if obs_lines else "(none recorded)"

    return (
        f"CLAIM INVENTORY (voice ONLY these, cite by claim_id in your [C<n>] tags):\n{claim_block}\n\n"
        f"CONFIRMED OBSERVATIONS (for [OBS] sentences):\n{obs_block}\n\n"
        f"Write the reading per your instructions."
    )


# F2c retry correction-instruction pattern, same shape as
# palm_reading.py's own S66 F2c retry and claim_extraction.py's own
# per-feature retry.
def _build_retry_messages(user_prompt: str, prior_raw: str, failures: list[str]) -> list[dict]:
    return [
        {"role": "system", "content": _VOICE_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
        {"role": "assistant", "content": prior_raw},
        {
            "role": "user",
            "content": (
                "Your draft failed these checks: " + "; ".join(failures) + ". "
                "Rewrite the reading correcting ONLY these issues. Same "
                "claims, same tags contract."
            ),
        },
    ]


def _call_llm(client, messages: list[dict]) -> str:
    """Single try/except boundary around one API call -- the caller owns
    whether an exception here becomes a RuntimeError (it always does in
    this module, per the ERRORS section of the module docstring)."""
    response = client.chat.completions.create(
        model=_VOICE_MODEL,
        messages=messages,
        temperature=_VOICE_TEMPERATURE,
        timeout=_VOICE_TIMEOUT_SECONDS,
    )
    return response.choices[0].message.content


# ─── V-5: transplanted trait-needle machinery ───────────────────────────
# TRANSPLANTED from palm_reading._SUPPORT_NEEDLES (verbatim dict), cited
# not imported -- see the module docstring's V-5 entry for the circular-
# import reasoning. Same single-word, OCR-robustness-motivated needle
# choices as the original (irrelevant to THIS use, since V-5 only ever
# scans the MODEL's own fluent English output, never OCR'd corpus text --
# kept identical anyway so the two dictionaries never drift apart for no
# reason).
_FEATURE_TRAIT_NEEDLES: dict[str, tuple[str, ...]] = {
    "life line": ("life",),
    "head line": ("head",),
    "heart line": ("heart",),
    "fate line": ("fate",),
    "sun line": ("sun",),
    "thumb": ("thumb",),
    "fingers": ("finger",),
    "mount of venus": ("venus",),
    "mount of jupiter": ("jupiter",),
    "markings/other features": (
        "mark", "star", "cross", "island", "square", "circle", "hair",
    ),
}

_ALL_NEEDLES: tuple[str, ...] = tuple(
    sorted({n for needles in _FEATURE_TRAIT_NEEDLES.values() for n in needles})
)
_ANY_FEATURE_NEEDLE_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(n) for n in _ALL_NEEDLES) + r")\b", re.IGNORECASE
)


# ─── Validators (V-3/V-4/V-5) ────────────────────────────────────────────

_VOICE_TAG_PATTERN = re.compile(r"\[(?:C\d+|OBS|FLOW)\]")
_BRACKET_TOKEN_PATTERN = re.compile(r"\[[^\]]*\]")


def _check_tag_legality(text: str, included_claim_ids: set[str]) -> list[str]:
    """V-3: every sentence ends in exactly one recognized tag; every
    [C<n>] resolves to an INCLUDED claim_id; no other bracket token
    appears anywhere. Position-only, no sentence-splitter (same
    convention as palm_reading._check_tag_completeness) -- see the
    module docstring's KNOWN GAP note for the one class of error this
    can't catch (an untagged sentence sandwiched between two valid
    tags)."""
    if not text or not text.strip():
        return ["tag_legality: reading_text_tagged is empty or whitespace-only"]

    failures: list[str] = []

    for m in _BRACKET_TOKEN_PATTERN.finditer(text):
        if not _VOICE_TAG_PATTERN.fullmatch(m.group(0)):
            failures.append(f"tag_legality: unrecognized bracket token {m.group(0)!r}")

    valid_tags = list(_VOICE_TAG_PATTERN.finditer(text))
    if not valid_tags:
        failures.append("tag_legality: no recognized tag found in text")
        return failures

    trailing = text[valid_tags[-1].end():].strip()
    if trailing:
        failures.append(f"tag_legality: untagged residue after last tag: {trailing!r}")

    for prev, curr in zip(valid_tags, valid_tags[1:]):
        between = text[prev.end():curr.start()]
        if not between.strip():
            failures.append(
                "tag_legality: adjacent tags with no sentence between them: "
                f"{prev.group(0)!r}{curr.group(0)!r}"
            )

    for m in valid_tags:
        tag_text = m.group(0)
        if tag_text.startswith("[C"):
            claim_id = tag_text[1:-1]
            if claim_id not in included_claim_ids:
                failures.append(f"tag_legality: {tag_text} does not resolve to an included claim_id")

    return failures


def _check_claim_coverage(text: str, included_claim_ids: set[str]) -> list[str]:
    """V-4: every INCLUDED claim_id (post-filter) is cited by >=1 [C<n>]
    tag in the final draft."""
    cited = {
        m.group(0)[1:-1]
        for m in _VOICE_TAG_PATTERN.finditer(text)
        if m.group(0).startswith("[C")
    }
    missing = included_claim_ids - cited
    if missing:
        return [f"claim_coverage: claim_id(s) never cited: {sorted(missing)}"]
    return []


def _segment_by_tag(text: str) -> list[tuple[str, str]]:
    """[(sentence_text, tag_label), ...] using ONLY tag positions -- no
    sentence-splitter NLP, same position-only philosophy as everywhere
    else in this module. tag_label is "OBS", "FLOW", or a claim_id like
    "C3". Any untagged residue is not represented here -- V-3 already
    reports it separately, and V-4/V-5 only ever run once V-3 is clean."""
    segments: list[tuple[str, str]] = []
    prev_end = 0
    for m in _VOICE_TAG_PATTERN.finditer(text):
        sentence = text[prev_end:m.start()]
        tag_label = m.group(0)[1:-1]
        segments.append((sentence, tag_label))
        prev_end = m.end()
    return segments


def _check_flow_obs_doctrine_guard(text: str) -> list[str]:
    """V-5: any [FLOW] or [OBS] segment mentioning ANY feature's own
    trait-needle (see _FEATURE_TRAIT_NEEDLES / module docstring) fails.
    Deliberately coarse -- a single needle hit anywhere in the segment
    fails it, regardless of whether the surrounding sentence is actually
    interpretive or just incidentally names a feature while restating an
    observation (e.g. an [OBS] sentence literally restating "the life
    line is deep and long" would ALSO trip this, since "life" is a
    needle) -- ACCEPTED GAP, not a bug: see the module docstring's V-5
    entry for the full 3-place registration note. Direction of error is
    a FALSE POSITIVE on legitimate feature-naming OBS restatement, which
    is why this is a Ring-3-backstopped accepted gap rather than a hard
    production block -- a future refinement could special-case OBS
    sentences that ALSO don't contain any non-needle trait vocabulary,
    but that reintroduces exactly the kind of heuristic-tuning this
    prompt is explicitly not scoped to attempt."""
    failures: list[str] = []
    for sentence, tag_label in _segment_by_tag(text):
        if tag_label not in ("OBS", "FLOW"):
            continue
        hit = _ANY_FEATURE_NEEDLE_PATTERN.search(sentence)
        if hit:
            failures.append(
                f"doctrine_guard: [{tag_label}] sentence mentions feature-noun "
                f"{hit.group(0)!r}: {sentence.strip()!r}"
            )
    return failures


def _run_validators(text: str, included_claim_ids: set[str]) -> list[str]:
    """V-4/V-5 only evaluated once V-3 passes -- tag positions must be
    trustworthy before either downstream check means anything, same
    "whole-response rejected on any tier's violation" ordering as
    claim_extraction.py's E-1/E-2 before E-3."""
    failures = _check_tag_legality(text, included_claim_ids)
    if failures:
        return failures
    failures.extend(_check_claim_coverage(text, included_claim_ids))
    failures.extend(_check_flow_obs_doctrine_guard(text))
    return failures


def _run_extra_validators(text: str, extra_validators: tuple) -> list[str]:
    """S70 F-G1: runs each caller-supplied `(tagged_draft: str) -> list[str]`
    callable against the raw tagged draft (same text V-3/V-4/V-5 see,
    BEFORE any stripping) and concatenates their failure lists, in the
    order given. Deliberately NOT wrapped in try/except -- a validator
    that raises is a caller bug (a malformed callable), not a voice
    failure; swallowing it here would silently disable that guard, the
    opposite of what F-G1 exists to add. Runs unconditionally (not gated
    on V-3 passing) -- these are independent, caller-owned checks with no
    dependency on this module's own tag-position validators."""
    failures: list[str] = []
    for validator in extra_validators:
        failures.extend(validator(text))
    return failures


# ─── Dataclass ───────────────────────────────────────────────────────────


@dataclass(frozen=True)
class VoiceResult:
    reading_text_tagged: str
    validation_failures: tuple[str, ...]
    retry_used: bool
    diagnostics: dict = field(default_factory=dict)


# ─── Public API ─────────────────────────────────────────────────────────


def voice_claims(
    claims: tuple["Claim", ...],
    texts_by_feature: dict[str, str],
    client=None,
    *,
    extra_validators: tuple = (),
) -> VoiceResult:
    """One whole-reading voice call over the closed inventory of `claims`
    (after the input filter drops excluded_from_voice claims and caps
    correctives at _CORRECTIVE_CAP). If nothing survives the filter (an
    empty or all-excluded `claims` tuple), the LLM is never called -- an
    empty, non-raising VoiceResult is returned instead (there is nothing
    to voice, same "nothing attempted" convention as
    claim_extraction.extract_claims's all-gated-empty case).

    F2c semantics: an E-quivalent V-3/V-4/V-5 validation failure on the
    first draft triggers exactly ONE retry, with the failure list fed
    back as a correction instruction. Hard cap: 2 LLM calls, no
    exceptions. A retry that STILL fails validation does NOT raise --
    `validation_failures` comes back populated, and it is the CALLER's
    job (a later wiring prompt, P5) to refuse display on a non-empty
    tuple, mirroring `palm_reading.PalmReadingResult.validation.passed`.

    client: injection seam for tests -- if None, a real OpenAI() client
    is constructed lazily INSIDE this function (never at module import
    time; same S65 flag (b) precedent claim_extraction.py already
    documents).

    extra_validators (S70 F-G1, keyword-only): tuple of caller-owned
    `(tagged_draft: str) -> list[str]` callables, run after V-3/V-4/V-5
    on BOTH the first draft and the retry draft (see `_run_extra_
    validators`). Their failures are merged into the SAME list that
    drives the single F2c retry and the returned `validation_failures` --
    a first-draft failure from an extra validator alone triggers the
    retry, identical semantics to a V-3/V-4/V-5 failure. This is the seam
    pass-5 preflight's exemplar-echo ABORT (`diagnostics/pass5_preflight_
    S70.md`) needs: that check currently runs only at the outer display-
    check layer, which has no retry, so Stage 2's own internal retry
    never sees an echo failure as a correction. Wiring the actual display
    validators through this seam (palm_reading.py, tag-stripped first) is
    F-G2's job, NOT done here -- this module still never imports
    palm_reading (circular-import lock) and never strips tags itself;
    strip-wrapping is the caller's responsibility. An extra_validator
    that raises propagates UNCAUGHT (a caller bug, not a voice failure --
    see `_run_extra_validators`'s own docstring). Default `()` preserves
    every pre-F-G1 call site's behavior byte-for-byte -- no wiring here
    yet, this prompt is the seam only.

    Raises:
        RuntimeError: an API exception on EITHER call (first attempt or
                      retry) -- this is a single whole-reading call, not
                      a per-feature loop, so there is no partial-success
                      fallback the way claim_extraction.py has across
                      multiple features.
    """
    included_claims, filter_diagnostics = _filter_claims_for_voice(claims)

    # Empty `claims` (Stage 1 had nothing to attempt or extracted
    # nothing) -> zero LLM calls here too. Same NOTED BEHAVIOR CHANGE
    # this early-return pairs with in claim_extraction.extract_claims'
    # own `attempted_features` comment -- together these two empty-cases
    # are why an all-absent hand now yields a decline-only reading with
    # NO LLM call anywhere, not the old single-call low-confidence
    # fallback (S69 F-H close-out, CLAUDE.md).
    if not included_claims:
        return VoiceResult(
            reading_text_tagged="",
            validation_failures=(),
            retry_used=False,
            diagnostics={**filter_diagnostics, "call_count": 0, "skipped": "no included claims to voice"},
        )

    if client is None:
        from openai import OpenAI  # lazy import -- see docstring
        client = OpenAI()

    included_claim_ids = {c.claim_id for c in included_claims}
    user_prompt = _build_user_prompt(included_claims, texts_by_feature)

    call_count = 0
    try:
        call_count += 1
        raw = _call_llm(client, [
            {"role": "system", "content": _VOICE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ])
    except Exception as exc:  # noqa: BLE001 -- re-raised as a module-prefixed RuntimeError
        raise RuntimeError(f"claim_voicing: API call failed: {exc}") from exc

    failures = _run_validators(raw, included_claim_ids)
    extra_failures = _run_extra_validators(raw, extra_validators)
    failures = failures + extra_failures
    retry_used = False
    diagnostics: dict = dict(filter_diagnostics)

    if failures:
        retry_used = True
        diagnostics["first_attempt_failures"] = failures
        if extra_failures:
            diagnostics["extra_validator_failures"] = extra_failures
        try:
            call_count += 1
            raw = _call_llm(client, _build_retry_messages(user_prompt, raw, failures))
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"claim_voicing: API retry call failed: {exc}") from exc
        failures = _run_validators(raw, included_claim_ids)
        failures = failures + _run_extra_validators(raw, extra_validators)

    diagnostics["call_count"] = call_count

    return VoiceResult(
        reading_text_tagged=raw,
        validation_failures=tuple(failures),
        retry_used=retry_used,
        diagnostics=diagnostics,
    )
