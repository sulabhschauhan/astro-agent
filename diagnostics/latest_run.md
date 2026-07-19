# S70 F-G3: descriptive voice guidance replaces verbatim exemplars

## MEASURE FIRST -- `_VOICE_SYSTEM_PROMPT`'s current "## Voice" section (verbatim, pre-edit)

```
## Voice
Write in Cheiro's declarative register: direct, confident assertions in period-appropriate diction, addressed straight to the reader. This is a palmist reading a hand, not a therapist offering affirmation -- speak with the authority of someone who has read thousands of hands and states plainly what each one shows.
Model sentences (voice and cadence ONLY -- do not reuse or adapt ANY part of their wording, not even a short fragment; they contain no interpretive content of their own): "I have examined many hands in my years of practice, and each one tells its own story to those who know how to read it." / "The hand rarely lies to the palmist who reads it honestly." Every interpretive claim in your actual reading must come from the numbered CLAIM INVENTORY below -- these two sentences exist only to model tone, never as a source of content.
FORBIDDEN words and phrasings (never use these, in any form): stability, fulfillment, fulfilling, favorable, journey, navigate, navigating, empower, empowerment, and any "this suggests you are the kind of person who..." self-help framing.
```

This is the exact block containing the two R2 exemplar sentences
(identical to `palm_reading._EXEMPLAR_SENTENCES`, transplanted per the
module's own docstring). Only line 2 (the "Model sentences..." line) is
in scope for the PROMPT STRING edit -- line 1 (register description) and
line 3 (FORBIDDEN words) stay byte-identical, as do every other section
of `_VOICE_SYSTEM_PROMPT` (How to voice a corrective claim / Output
format / Scope / Length).

## Context (why)

Pass-5 preflight's post-F-G re-run (`diagnostics/pass5_preflight_S70.md`,
commit `908d325`) still ABORTed on `exemplar_echo` even with the F-G1/F-G2
retry-feed wiring live: Stage 2's own system prompt hands the model the
two exemplar sentences verbatim as "voice and cadence" models, creating a
standing gravitational pull toward reusing/paraphrasing them regardless
of how many retries fire. F-G1/F-G2 made the ECHO DETECTABLE and
retry-fed; F-G3 removes the echo SOURCE itself from the prompt.

## Edit summary

1. `_VOICE_SYSTEM_PROMPT`'s "Model sentences..." line replaced with
   purely DESCRIPTIVE voice attributes -- warm but measured tone,
   first-person-where-natural practicing-palmist register, plain
   unadorned language over ornate/archaic diction, and an explicit ban
   on canned/formulaic/recycled openings or closings, plus a "compose
   everything fresh" mandate. Verified: zero quoted example sentences
   remain anywhere in the new prompt text (the HARD CONSTRAINT) -- the
   replacement line describes attributes only, never demonstrates one.
2. **Deviation from the pre-edit plan recorded above**: the module-level
   comment directly above `_VOICE_SYSTEM_PROMPT`, and the module
   docstring's own "PROMPT:" paragraph, both explicitly stated (in prose)
   that the block shares "the same two tone-only exemplar sentences"
   with `palm_reading._EXEMPLAR_SENTENCES` -- true before this edit,
   FALSE after it. Both were updated to describe the actual post-F-G3
   state (exemplars deleted, replaced with descriptive guidance,
   `palm_reading._EXEMPLAR_SENTENCES`/`_check_exemplar_echo` cited as
   explicitly out of scope and unchanged) rather than left as stale,
   actively-wrong documentation. This is prose/comment correction only --
   the `_VOICE_SYSTEM_PROMPT` string itself changed in exactly the one
   line described in point 1, nothing else in the prompt text moved.
3. `palm_reading.py` untouched (confirmed via `git status` before
   commit) -- `_EXEMPLAR_SENTENCES`, `_check_exemplar_echo`, the F-G1
   seam, and `voice_claims()`'s own logic are all byte-identical.

## Tests (`tests/interpretive/test_claim_voicing.py`)

1. NEW `test_voice_system_prompt_contains_no_r2_exemplar_sentences` --
   imports `palm_reading._EXEMPLAR_SENTENCES` (the canonical source, not
   pasted inline, so a future edit to either sentence can't silently
   desync the two modules undetected) and asserts neither sentence
   appears anywhere in `claim_voicing._VOICE_SYSTEM_PROMPT`.
2. No existing test asserted the old prompt text -- grepped for
   `_VOICE_SYSTEM_PROMPT`/`EXEMPLAR`/`exemplar` in the test file before
   editing; zero matches. Nothing to update.
3. All 22 pre-existing tests (including every F-G1 seam test) pass
   UNMODIFIED -- confirmed prompt-content-agnostic by design, as
   expected; no adaptation was needed or performed.

## Test run (targeted only, per instructions -- no full suite)

```
pytest tests/interpretive/test_claim_voicing.py -q
23 passed (22 pre-existing + 1 new), 0 failed
```
