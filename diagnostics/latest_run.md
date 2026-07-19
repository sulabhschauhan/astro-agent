# S70 F-G2: display checks feed Stage-2 retry (F-G seam wiring)

**MODIFIED TWO FILES.** `agent/interpretive/palm_reading.py`
(`complete_palm_reading()` region only: new `_build_display_extra_
validators` helper + `complete_palm_reading()`'s docstring/body) and
`tests/interpretive/test_palm_reading.py`. `claim_voicing.py` untouched
(F-G1, already landed).

## MEASURE FIRST -- actual display-check inventory (verified, not assumed)

`_run_display_checks(stripped_text, context_corpus, unsupported_features)`
(unchanged by this prompt) runs, in this exact order:

```python
failures += _check_jargon(stripped_text)
failures += _check_self_help_register(stripped_text)
failures += _check_unsupported_dates(stripped_text, context_corpus)
failures += _check_length(stripped_text)
failures += _check_banned_feature_mentions(stripped_text, unsupported_features)
failures += _check_exemplar_echo(stripped_text)
```

**6 checks, not 5** -- the instructing prompt's "expected class" list
(jargon/unsupported-date/length/self-help/exemplar-echo) omitted
`_check_banned_feature_mentions` (unsupported-feature-mention). Per the
prompt's own "verify, don't assume" instruction, all 6 were wired into
the seam, not just the 5 named -- `_check_banned_feature_mentions` is
just as much a display check as the other five and there is no stated
reason to exclude it from the retry-feed fix.

Signatures (why each closure needs its own captured context):
- `_check_jargon(text)`, `_check_self_help_register(text)`,
  `_check_length(text)`, `_check_exemplar_echo(text)` -- single-arg.
- `_check_unsupported_dates(text, context_corpus)` -- needs
  `context_corpus` (built once per `complete_palm_reading()` call from
  `prep.texts_by_feature`/`prep.gated_results`).
- `_check_banned_feature_mentions(text, unsupported_features)` -- needs
  `prep.unsupported_features`.

Both extra values (`context_corpus`, `prep.unsupported_features`) were
ALREADY available from `prep` before the `voice_claims()` call -- moving
`context_corpus`'s computation a few lines earlier (unchanged value,
same two `prep` fields) was the only reordering needed.

## Edit summary

1. New helper `_build_display_extra_validators(context_corpus,
   unsupported_features) -> tuple` (placed immediately before
   `complete_palm_reading()`): 6 closures, one per check, each
   `(tagged_draft) -> list[str]` that runs `_strip_stage2_tags(tagged_
   draft)` THEN calls its one check on the stripped text. One closure per
   check (not a mega-closure) so each check's own failure string(s)
   survive distinctly into Stage 2's retry correction message.
2. Text-state parity verified: the seam's closures strip tags and run
   immediately -- no decline_block, no DISCLAIMER. The OUTER
   `_run_display_checks` call already runs on that same
   pre-decline/pre-disclaimer stripped state (`decline_block`/
   `DISCLAIMER` are only ever concatenated ONCE, after `voice_claims()`
   returns, never per-draft) -- so there was no semantic drift to
   reconcile; the seam and the outer layer check the textually IDENTICAL
   state for whichever draft is in play.
3. `complete_palm_reading()` now builds `extra_validators` from
   `context_corpus`/`prep.unsupported_features` (computed BEFORE the
   `voice_claims()` call, moved up from its old post-call position) and
   passes it as `voice_claims(..., extra_validators=extra_validators)`.
4. The outer `_run_display_checks(stripped, context_corpus, prep.
   unsupported_features)` call is UNCHANGED -- still the fail-closed
   backstop against whichever draft ships.
5. Docstring updated: "NO retry at this layer" replaced with an
   explanation of the F-G1 seam wiring, the outer layer's continued
   fail-closed/no-additional-retry role, and a pointer to the pass-5
   preflight ABORT (`diagnostics/pass5_preflight_S70.md`) this fix
   directly addresses.

## Deviations from the instructing prompt

1. **6 checks wired, not 5** -- see MEASURE FIRST above (the prompt's own
   "verify, don't assume" instruction directly anticipated this).
2. **5 existing tests updated** (all asserted the OLD no-feed/"single-
   shot, no retry" behavior, the prompt's explicit carve-out):
   - `test_jargon_injection_case_insensitive_and_word_boundary`
   - `test_self_help_case_insensitive`
   - `test_self_help_multi_term_single_sorted_deduped_failure`
   - `test_banned_mention_failure_is_single_shot_no_retry` -> renamed
     `test_banned_mention_failure_now_retries_and_stays_failed`
   - `test_exemplar_echo_guard_fires_single_shot_no_retry` -> replaced by
     3 new tests under a renamed section (see TESTS below); the OLD
     single test's exact scenario (draft echoes, single Stage-2 response
     supplied) is preserved as test (b)'s twin-echo variant, not dropped.
   All 5 failed identically for the SAME reason before the test edits:
   their single-Stage-2-response fixtures (`_single_feature_client`/
   `_two_stage_setup`) now trigger a real retry (the extra-validator
   failure on draft 1), and `_FakeCompletions` clamp-reuses the SAME
   still-failing response for the retry call -- so the failure string
   now legitimately appears TWICE and `stage2_retry_used` flips `True`.
   This is the intended behavior change, not a regression; one test NOT
   touched (`test_self_help_integration_empowerment_fails_and_propagates`,
   same fixture shape) already used containment (`any(...)`) rather than
   exact-count assertions, so it kept passing unmodified -- confirming
   the 5 above were flagged correctly as the ones actually asserting
   old-behavior specifics (counts/call-totals), not just incidentally
   broken.
3. Duplicate failure strings in `validation.failures` when the SAME
   check fails on both the seam-fed retry draft AND the outer backstop
   re-check of that same final draft: left AS-IS, not deduplicated --
   not asked for, doesn't affect `validation.passed` (any non-empty
   tuple fails closed), and the "no double-jeopardy" instruction was
   read as being about OUTCOME (corrected-by-retry XOR fails-closed
   here, never both as independent failure events), not about list
   uniqueness.

## Tests (`tests/interpretive/test_palm_reading.py`)

(a) `test_exemplar_echo_guard_fires_draft1_retries_and_clears_on_clean_draft2`
    -- draft 1 echoes, draft 2 clean -> `stage2_retry_used=True`, the
    exemplar failure string is in the retry correction message
    (`client.completions.calls[2]["messages"][-1]["content"]`), final
    `validation.passed=True`.
(b) `test_exemplar_echo_guard_fires_both_drafts_stays_failed_no_third_call`
    -- both drafts echo -> exactly 3 calls (Stage-1-once + Stage-2-twice,
    no third Stage-2 call), `validation.passed=False`, exemplar failure
    present in `validation.failures`.
(c) `test_exemplar_echo_guard_clean_draft_happy_path_no_behavior_change`
    -- clean draft -> no retry, `stage2_retry_used=False`,
    `validation.passed=True`, `validation.failures == ()`, 2 calls total
    (unchanged from pre-F-G2).

Plus the 5 updated tests above (jargon/self-help x2/banned-mention),
each now asserting the new duplicated-failure/retry-fires shape their
single-response fixtures actually produce.

## Test run (targeted only, per instructions -- no full suite)

```
pytest tests/interpretive/test_palm_reading.py -q
64 passed, 4 skipped (pre-existing F-H retirement skips, unchanged)
```
(Baseline before this prompt's edits: 62 passed, 4 skipped -- net +2
tests: -1 old single-shot exemplar test, +3 new lettered tests.)

## Carry-forward

`_run_display_checks`'s post-hoc call on the final draft (item 4, kept
unchanged as instructed) is now genuinely redundant work in the common
case where the seam's own retry already cleared everything -- left as
the deterministic fail-closed backstop per instruction 4, not optimized
away; a future prompt could reconsider whether it's still needed once
live dogfood evidence shows the seam-fed retry handles the large
majority of cases.
