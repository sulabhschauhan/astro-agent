# S69 F-H P3: claim_voicing.py -- Stage-2 voice pass (new file only)

**NEW FILE ONLY.** `agent/interpretive/claim_voicing.py`. `palm_reading.py`,
`app.py`, and every test file are untouched -- wiring is P5.

## Step 0 -- pooled overlap distribution (design chat's ratification input)

Copied verbatim from `diagnostics/fh_stage1_probe_S69.md`:

```
Pooled overlap distribution (all cells, all claims):
min=0.50 p25=1.00 median=1.00 p75=1.00 max=1.00 (n=73)
```

Design chat ratifies `claim_extraction._PARAPHRASE_OVERLAP_FLOOR` (0.40)
against this line. `claim_voicing.py` (this prompt) does not use that
constant at all -- Stage 2 never re-checks Stage 1's overlap floor, it
trusts Stage 1's already-validated `Claim.claim_text` as its only
interpretive-content source.

## What landed

`agent/interpretive/claim_voicing.py` -- Stage 2's closed-inventory voice
pass. Public API:

```python
voice_claims(
    claims: tuple[Claim, ...],
    texts_by_feature: dict[str, str],
    client=None,
) -> VoiceResult(reading_text_tagged, validation_failures: tuple, retry_used: bool, diagnostics: dict)
```

Never reads `Claim.chunk_id` anywhere -- no chunk text or chunk_id
appears in the prompt by construction, not merely by instruction.

**Input filter** (pre-prompt, deterministic Python): `excluded_from_voice`
claims dropped entirely; corrective-valence claims capped at
`_CORRECTIVE_CAP=1` (first kept in ascending claim_id order -- numeric,
not lexicographic, so "C10" doesn't misorder before "C2"), overflow
recorded in `diagnostics["corrective_overflow"]`, never reaching the
prompt.

**Prompt**: the "## Voice" block is transplanted near-verbatim from
`palm_reading._READING_SYSTEM_PROMPT`'s own "## Voice" section -- same
declarative-register description, same two tone-only exemplar sentences,
same forbidden self-help word list. One line adapted (not copied): the
original's "must come from the provided passages and the confirmed hand
description(s)" becomes "must come from the numbered CLAIM INVENTORY
below", since Stage 2 has no retrieved passages, only the claim
inventory. New content: a 3-tag output contract (`{[C<n>], [OBS],
[FLOW]}`), a "voice a corrective as Cheiro's own correction, not a
hedge" instruction, and the numbered claim inventory + confirmed
observations blocks.

**Models/constants**: `_VOICE_MODEL="gpt-4o"` (register quality --
explicitly flagged as an UNTESTED design choice, since
`fh_stage1_probe_S69.md` only measured Stage-1 extraction quality, never
Stage-2 voice quality; no probe has compared gpt-4o vs gpt-4o-mini on
this dimension). `_VOICE_TEMPERATURE=0` (unchanged pending pass-5
evidence, per CLAUDE.md's F-G entry, which explicitly folds this question
into F-H's design rather than resolving it standalone).
`_VOICE_TIMEOUT_SECONDS=30.0` -- duplicated from
`palm_reading._READING_TIMEOUT_SECONDS`, not imported (same circular-
import avoidance as `claim_extraction._EXTRACTION_TIMEOUT_SECONDS`).

## Validator inventory

Run in order -- V-4/V-5 only evaluated if V-3 passes (tag positions must
be trustworthy first, same ordering philosophy as `claim_extraction.py`'s
E-1/E-2 before E-3):

| Validator | Checks | Known limitation |
|---|---|---|
| V-3 tag legality | Every sentence ends in exactly one recognized tag (`{[C<n>], [OBS], [FLOW]}`); every `[C<n>]` resolves to an INCLUDED claim_id; no other bracket token anywhere | Same class as `palm_reading.py`'s own accepted gap (b): an untagged sentence sandwiched between two valid tags is not caught (position-only, no sentence-splitter) |
| V-4 claim coverage | Every included claim_id is cited by >=1 `[C<n>]` tag | -- |
| V-5 `[FLOW]`/`[OBS]` doctrine guard | Reuses `palm_reading._SUPPORT_NEEDLES` (the per-feature trait-noun dictionary), TRANSPLANTED here as `_FEATURE_TRAIT_NEEDLES` (cited, not imported -- same circular-import reasoning as the timeout constant). ANY needle hit in a `[FLOW]`/`[OBS]` segment fails | Deliberately coarse: a legitimate `[OBS]` sentence restating "the life line is deep" would ALSO trip this, since "life" is a needle -- ACCEPTED GAP, not a bug, backstopped by Ring 3 human review, same disposition as `claim_extraction.py`'s gaps (a)/(f) |

F2c: single retry, failures fed back as a correction instruction, hard
2-call cap. A retry that still fails validation returns a populated
`validation_failures` tuple rather than raising -- fail-closed
disposition is explicitly the CALLER's job (P5 wiring), matching
`palm_reading.PalmReadingResult.validation.passed`'s own pattern.

`RuntimeError` (module-prefixed) on an API exception on EITHER call --
unlike `claim_extraction.py`'s per-feature partial-success design, Stage
2 is a single whole-reading call with no fallback to degrade to.

## Manual smoke tests (not part of the committed test suite -- ad hoc, this session only; formal tests are a later prompt per the instructing sequence)

Verified against a stub client before running the full suite:
- Input filter: 4 claims (1 supports, 1 excluded conditional, 2
  corrective) -> included = `[C1, C3]` (excluded dropped, only the
  first corrective kept), `corrective_overflow = [C4]`,
  `excluded_count = 1`.
- Happy path: 2 claims, clean tagged draft citing both, `[FLOW]`
  sentences free of any needle hit -> `validation_failures=()`,
  `retry_used=False`.
- V-3 (unrecognized bracket token `[XYZ]`) -> retry fires, corrected
  draft recovers.
- V-4 (claim never cited) -> persistent failure ->
  `validation_failures` contains `claim_coverage: ...`.
- V-5 (`[OBS]` sentence naming "life line") -> persistent failure ->
  `validation_failures` contains `doctrine_guard: ...`.
- Empty `claims` tuple -> `voice_claims` never calls the LLM (`.script`
  stays empty), returns an empty, non-raising `VoiceResult` with
  `diagnostics["skipped"]` set.
- API exception on the first call -> `RuntimeError` raised with the
  `claim_voicing: API call failed: ...` prefix.

## Full suite result

```
3235 passed, 3 skipped (unchanged from the P2 baseline)
```

No production file other than the new module touched; no test file
touched.

## CLAUDE.md registration items to carry to F-H close-out (NOT done here)

Per this prompt's own instruction, flagged for the close-out prompt:

1. **V-5 ACCEPTED GAP** (coarse doctrine guard -- a legitimate `[OBS]`
   sentence naming a feature trips it just as a real leak would):
   registered at 2 of the CLAUDE.md 3-place convention's 3 places so far
   (this module's own docstring, and the validator's own code comment) --
   place 1 (a CLAUDE.md Known-Source-Divergences entry) is close-out's
   job.
2. **`_VOICE_MODEL="gpt-4o"` is an untested design choice**, unlike
   `claim_extraction._EXTRACTION_MODEL`'s probe-validated pick -- worth a
   dedicated Stage-2 voice-quality probe (analogous to
   `fh_stage1_probe_S69.md`) before or during Ring 3 re-validation, not
   decided here.
3. **`_CORRECTIVE_CAP=1` is a voice/UX judgment call**, not an
   empirically-measured threshold like the 0.30/0.40 floors -- flag for a
   THRESHOLD DISCIPLINE line in CLAUDE.md once F-H lands live, and as a
   Ring 3 revisit candidate if a reading is ever found to need a second
   correction.

## Verdict

New file only, as instructed. `palm_reading.py`, `app.py`, and all test
files untouched. Suite green at 3235/3, unchanged from the P2 baseline.
Formal test coverage for `claim_voicing.py` and wiring both `claim_
extraction.py` and this module into `palm_reading.py` remain later
prompts in the F-H sequence.
