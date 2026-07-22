# S70 F-G4: V-5 [OBS] carve-out + adjacent-tag prompt hardening

**MODIFIED ONE PRODUCTION FILE.** `agent/interpretive/claim_voicing.py`
(V-5 validator narrowing + `_VOICE_SYSTEM_PROMPT` hard rule) and its
direct tests (`tests/interpretive/test_claim_voicing.py`).

## Context (why)

4 consecutive dogfood runs (`.claude/read_prompt.md`, 2026-07-22,
timestamps `17:57:28`/`17:58:05`/`17:59:35` + one earlier) all
fail-closed with the identical two-stage pattern:
`stage2_first_attempt_failures` was ALWAYS `tag_legality: adjacent tags
with no sentence between them` (e.g. `'[C4]''[OBS]'`), and the FINAL
`validation_failures` (after the single retry) was ALWAYS
`doctrine_guard` on an `[OBS]` sentence that legitimately named its own
observed feature (e.g. `"The sun line is clearly present on your
palm."` `[OBS]`). Root cause, confirmed by reading `_run_validators`:
V-3 (tag legality) gates V-4/V-5, so V-5 never even ran on draft 1 --
the single retry was spent correcting tag adjacency, leaving zero
budget to also correct the V-5 hit that then failed the retry draft.
This is the module's own pre-flagged accepted gap (V-5's [OBS]
false-positive on legitimate feature-naming) manifesting as a hard
production block, compounded by a distinct prompt-clarity bug (the
system prompt never told the model tags must be sentence-separated).

## Edit 1 -- V-5 scope narrowing

`_check_flow_obs_doctrine_guard` renamed to `_check_flow_doctrine_guard`.
`[OBS]` segments are now skipped entirely (`if tag_label != "FLOW":
continue`, was `if tag_label not in ("OBS", "FLOW")`). `[FLOW]` behavior
is byte-identical to before.

### Docstring diff (validator's own comment)

**OLD:**
> V-5: any [FLOW] or [OBS] segment mentioning ANY feature's own
> trait-needle (see \_FEATURE_TRAIT_NEEDLES / module docstring) fails.
> Deliberately coarse -- a single needle hit anywhere in the segment
> fails it, regardless of whether the surrounding sentence is actually
> interpretive or just incidentally names a feature while restating an
> observation (e.g. an [OBS] sentence literally restating "the life
> line is deep and long" would ALSO trip this, since "life" is a
> needle) -- ACCEPTED GAP, not a bug: see the module docstring's V-5
> entry for the full 3-place registration note. Direction of error is
> a FALSE POSITIVE on legitimate feature-naming OBS restatement, which
> is why this is a Ring-3-backstopped accepted gap rather than a hard
> production block -- a future refinement could special-case OBS
> sentences that ALSO don't contain any non-needle trait vocabulary,
> but that reintroduces exactly the kind of heuristic-tuning this
> prompt is explicitly not scoped to attempt.

**NEW:**
> V-5 (S70 F-G4 narrowed): any [FLOW] segment mentioning ANY feature's
> own trait-needle (see \_FEATURE_TRAIT_NEEDLES / module docstring)
> fails. [OBS] segments are OUT OF SCOPE for this guard -- an [OBS]
> sentence restates a confirmed observation by definition, so naming
> that observation's own feature (e.g. "the sun line is clearly present
> on your palm") is its intended behavior, not a leak. [FLOW] segments
> are unchanged: a pure connective/opening/closing sentence naming a
> feature-noun is the closing/summary-with-feature-nouns pattern this
> guard exists to catch, and still fails.

### Module docstring diff (VALIDATORS section, V-5 entry)

**OLD** (excerpt): "V-5 [FLOW]/[OBS] doctrine guard: ... ANY needle hit
in a [FLOW] or [OBS] segment fails -- deliberately coarse, by design...
ACCEPTED GAP, 3-place registration ... place 1 (a CLAUDE.md
Known-Source-Divergences entry) is NOT added here -- that is the F-H
close-out prompt's job..."

**NEW** (excerpt): "V-5 [FLOW] doctrine guard (S70 F-G4 narrowed -- was
[FLOW]/[OBS]): ... ANY needle hit in a [FLOW] segment fails... [OBS]
segments are OUT OF SCOPE for this guard as of S70 F-G4: 4 consecutive
dogfood runs (`.claude/read_prompt.md`, 2026-07-22) showed the guard
hard-failing on [OBS] sentences that legitimately restate a confirmed
observation while naming its own feature... the old ACCEPTED GAP
framing for [OBS] is RETIRED, not merely re-scoped. [FLOW] stays an
accepted gap, 3-place registration... place 1 ... is NOT added here --
that is a future close-out prompt's job."

## Edit 2 -- adjacent-tag hard rule

`_VOICE_SYSTEM_PROMPT`'s "Output format (voice tags)" section, one new
sentence set immediately after "Tag every sentence, including the
opening and closing ones.":

> Every tag MUST be preceded by a complete sentence of visible text.
> Never place two tags back-to-back with nothing between them. Never
> emit "[X][Y]" -- always "{sentence}. [X] {next sentence}. [Y]".

No example/model sentences added (F-G3 hard constraint preserved --
the template uses brace placeholders, not real quotable prose).

## Tests (`tests/interpretive/test_claim_voicing.py`)

- (a) `test_v5_needle_in_obs_sentence_fails` -> rewritten as
  `test_v5_needle_in_obs_sentence_passes`: same fixture (needle in an
  [OBS] segment), now asserts a clean first draft, no retry, empty
  `validation_failures`.
- (b) `test_v5_needle_in_flow_sentence_fails` -- unchanged (label
  format for [FLOW] failures didn't change).
- (c) new `test_v5_failures_never_labeled_obs` -- a draft combining a
  FLOW-needle sentence (still fails) and an OBS-needle sentence (must
  not contribute) asserts the populated doctrine_guard failure list
  contains no `[OBS]`-labeled entry.
- (d) `test_v3_failure_gates_v4_and_v5` -- unchanged, V-3 still gates
  V-4/V-5.
- (e) new `test_voice_system_prompt_has_adjacent_tag_hard_rule` --
  asserts the new hard-rule sentences appear verbatim inside the
  "Output format (voice tags)" section, and that no quote-delimited run
  of >=4 real words (brace placeholders excluded) appears in that
  section -- proving the new rule didn't reintroduce quotable example
  text.
- Retired test docstring/section-header comments referencing
  "[FLOW]/[OBS]" updated to "[FLOW]" where they described V-5 scope
  (`test_v5_same_needle_inside_claim_sentence_passes`'s inline comment,
  the V-5 section header).

## Test run (targeted only, per instructions -- no full suite)

```
pytest tests/interpretive/test_claim_voicing.py -v
25 passed, 1 warning (unrelated opentelemetry deprecation warning)
```

## Flag for a future close-out prompt (not done here)

CLAUDE.md's A1 accepted-gap register and the S69 F-H close-out entry
both reference V-5's old [FLOW]/[OBS] framing -- the V-5 [OBS]
accepted-gap registration should be marked RETIRED there, and the V-5
accepted-gap language narrowed to [FLOW] only, in the next design-chat
close-out pass touching this session's decisions. Not edited in this
prompt (scope was the one production file + its direct tests only).
