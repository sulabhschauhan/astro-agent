# S69 F-H P5: two-stage wiring in palm_reading.py

**MODIFIED ONE FILE.** `agent/interpretive/palm_reading.py`. No test file
touched, per this prompt's own instruction -- failures below are EXPECTED
(old single-call tests), catalogued not fixed. This commit is LOCAL ONLY,
per the two-commit single-push discipline: does not push until P5b's
test-alignment commit is also local and the suite is green, then one push
carries both.

## What landed

`palm_reading.py`'s single-call generation block (build `_READING_SYSTEM_
PROMPT` + `_LOW_CONFIDENCE_ADDENDUM`, assemble one whole-reading prompt,
one free-composition generation call with its own F2c retry) is REPLACED
by `claim_extraction.extract_claims()` (Stage 1) followed by `claim_
voicing.voice_claims()` (Stage 2). `generate_palm_reading()` keeps its
exact pre-existing signature and behavior contract -- it is now
`prepare_palm_reading()` composed with `complete_palm_reading()`, split
at that seam for a future P6 dogfood checkpoint to inspect the Stage-1
claims inventory before voicing.

**Two-phase seam**: `prepare_palm_reading(palm_left, palm_right,
hand_detail=None, client=None) -> PalmReadingPrep` runs parse -> retrieve
-> support gate -> Stage 1. `complete_palm_reading(prep, client=None) ->
PalmReadingResult` runs Stage 2 -> display checks -> decline -> DISCLAIMER
-> strip. `generate_palm_reading()` is now a 2-line wrapper: `prep =
prepare_palm_reading(...); return complete_palm_reading(prep, client=client)`
-- same client threads through both stages, no behavior fork.

**Retired, not deleted** (this prompt's own instruction -- a future
close-out prompt owns actual deletion):
- V-1 (`_check_tag_completeness`) / V-2 (`_check_anchor_legality`):
  invocation removed. Natively replaced by claim_extraction's E-1
  (per-feature chunk_id legality) and claim_voicing's own V-3 (tag
  legality on ITS OWN `{[C<n>], [OBS], [FLOW]}` vocabulary).
- `_check_feature_coverage` (F-A): invocation removed, superseded by
  claim_voicing's V-4 (claim coverage), strictly stronger.
  `ValidationReport.warnings` kept for dataclass compatibility, always
  `()` now.
- `_run_ring1_checks`: no longer called. Its six display checks (jargon,
  self-help register, unsupported dates, length, banned-feature
  mentions, exemplar echo) survive unchanged in a NEW `_run_display_
  checks()`, run on Stage 2's stripped output.

**New helpers added**: `_join_feature_texts` (Stage1/2 expect one string
per feature, `_gather_feature_texts` returns a list -- joined with `" / "`,
same separator `_resolve_feature_quality` already uses), `_STAGE2_TAG_
PATTERN`/`_strip_stage2_tags` (see CAUGHT ISSUE below), `_run_display_
checks`, `_compute_decline_features`, `_build_sources_from_claims`.

**`PalmReadingResult` additions** (additive, defaulted): `claims: tuple`
(the FULL Stage-1 inventory, not just what got voiced), `stage1_retry_
features: tuple` (registry order), `stage2_retry_used: bool`. `retry_used`
(compat) = `bool(stage1_retry_features) or stage2_retry_used`.

**Sources rebuilt per-claim**: only claim_ids Stage 2 ACTUALLY CITED (a
`[C<n>]` tag present in the final `reading_text_tagged`) contribute a
source, mapped through `gated_results` for book/page/score, deduped by
`(chunk_id, feature)`, in order of first citation. This is a deliberate
tightening vs. the OLD sources list (which included every chunk fed to
the single prompt regardless of whether it was cited).

**Decline set**: `_compute_decline_features` unions gate-unsupported +
Stage-1 `failed_features` + gate-supported features whose claims are all
`excluded_from_voice` OR simply empty ("honest decline over silence"),
registry order, deduped. Used ONLY to build the decline-block TEXT.

## CAUGHT ISSUES (self-corrected during this session, documented not silently fixed)

1. **Stage-2 tag vocabulary mismatch.** The task's own phrasing ("strip
   layer... survives") undersold a real problem: `claim_voicing.py` tags
   its output `{[C<n>], [OBS], [FLOW]}`, but the existing
   `CHUNK_ANCHOR_TAG_PATTERN`/`strip_generation_tags()` only recognize
   `[OBS]` or a full `[<book>_p<n>_c<n>]` chunk-id token -- reusing them
   as-is would have silently left `[C1]`/`[FLOW]` tokens in the displayed
   text. Caught before writing any code; fixed by adding `_STAGE2_TAG_
   PATTERN`/`_strip_stage2_tags` (duplicated from `claim_voicing._VOICE_
   TAG_PATTERN`, cited not imported -- same convention P1/P3 already used
   for the timeout constant, avoiding a reach into another module's
   private name). `CHUNK_ANCHOR_TAG_PATTERN`/`strip_generation_tags()`
   themselves are untouched (retired-but-defined).
2. **`unsupported_features` field-meaning drift.** First draft of
   `complete_palm_reading()` assigned `PalmReadingResult.unsupported_
   features=decline_features` (the broader union) instead of `prep.
   unsupported_features` (the gate-only value the field has always
   documented). Caught on review before running tests: the DECLINE BLOCK
   TEXT needs the broader union, but the FIELD's long-established meaning
   ("registry-order tuples from the support gate") should not silently
   change underneath any existing consumer. Fixed: `unsupported_features`
   stays gate-only; `decline_features` is used only to build the decline
   block text, never assigned to the field.

## NOTED BEHAVIOR CHANGE (architectural consequence, not a bug)

The old single-call flow's `_LOW_CONFIDENCE_ADDENDUM` path let the model
free-compose a generic reading from confirmed observations alone when
retrieval returned zero chunks for every feature (still making exactly 1
LLM call). The two-stage architecture has no equivalent: zero gated
chunks -> `extract_claims` has nothing to attempt (empty, non-raising) ->
`voice_claims` has nothing to voice (empty, non-raising) -> the final
reading is decline-block-plus-disclaimer only, ZERO LLM calls made. This
directly caused 4 of the 39 test failures below (tests that asserted
"exactly 1 call happens even with empty retrieval"). Judged a deliberate,
correct consequence of retiring free composition -- the entire point of
F-H -- not a regression to patch here. Flagged for close-out's CLAUDE.md
registration.

## Failing tests -- 39 failures, all in tests/interpretive/test_palm_reading.py

All 39 verified individually (`pytest -v --tb=short`, not inferred from
position). Grouped by shared root cause, since 34 of the 39 share the
identical mechanism -- one explanation per group, not 39 copies of the
same sentence.

### Group A (34 tests) -- Stage-1 JSON-parse failure -> RuntimeError

**Cause**: these tests' `_FakeClient(content=...)` supplies the OLD
single-call free-prose reading text (or a canned draft) as the fake LLM's
one answer. Stage 1 now expects THAT SAME response to be valid JSON
matching the extraction schema (`{"feature": ..., "claims": [...]}`). It
never is -- extraction fails JSON parsing on both its own first attempt
and its own retry, so `claim_extraction.extract_claims` raises
`RuntimeError` (all attempted features failed) before Stage 2, the old
Ring-1 checks, the old F2c retry, or `_check_feature_coverage` ever run.

- test_jargon_injection_case_insensitive_and_word_boundary
- test_fabricated_year_absent_from_context_fails
- test_year_supported_by_retrieved_chunk_does_not_fail
- test_happy_path_left_only
- test_exactly_one_llm_call_when_first_draft_passes
- test_retry_after_failed_first_draft_then_clean_retry_passes
- test_retry_after_failed_first_draft_still_fails_stays_failed
- test_retry_call_raises_becomes_runtime_error_no_third_call (also:
  the RuntimeError it DOES get doesn't match the test's expected
  `"GPT-4o reading-generation call failed"` regex -- same root cause,
  message just differs from the old single-call wrapper's)
- test_search_filters_to_canonical_cheiro_book
- test_sources_propagate_book_page_score
- test_self_help_case_insensitive
- test_self_help_word_boundary_excludes_substrings
- test_self_help_unlisted_conjugation_does_not_trip
- test_self_help_multi_term_single_sorted_deduped_failure
- test_self_help_clean_cheiro_register_passes
- test_self_help_integration_empowerment_fails_and_propagates
- test_fail_open_degenerate_quality_still_queries_and_logs
- test_one_feature_search_failure_does_not_kill_reading_other_feature_succeeds
- test_per_feature_map_ordering_and_dedupe_for_display
- test_sources_carry_distinct_feature_tags
- test_doctrine_inversion_guard_fate_unsupported_first_draft_retried_clean
- test_needle_collision_battery_sunday_sunny_remarkable_marked_do_not_trip
- test_needle_collision_battery_genuine_sun_line_mention_fires
- test_score_floor_boundary_029_excluded_031_included
- test_decline_block_absent_when_all_observed_features_supported
- test_supported_unsupported_tuples_propagate_in_registry_order
- test_f2c_cap_unchanged_banned_mention_fails_both_drafts_stays_failed
- test_exemplar_echo_guard_fires_first_draft_retried_clean
- test_exemplar_echo_boundary_5word_no_fire_6word_fires
- test_exemplar_echo_normalization_case_punctuation_whitespace
- test_exemplar_echo_does_not_fire_on_retrieved_chunk_quote
- test_end_to_end_tagged_draft_with_cited_chunk_validates_clean_and_strips_tags
  (exercised the OLD A1 tag contract end to end -- obsolete now that
  V-1/V-2/that tag vocabulary are retired)
- test_coverage_only_retry_fires_and_clean_retry_clears_warnings
  (exercises the retired `_check_feature_coverage` retry path)
- test_coverage_fail_open_final_still_missing_warning_present_reading_displays
  (same -- retired `_check_feature_coverage`)

### Group B (2 tests) -- IndexError, `calls[0]` on an empty call list

**Cause**: both fixtures retrieve ZERO chunks for every feature. Stage 1
has no attempted features (nothing gated) -> returns an empty result
WITHOUT calling the client at all; Stage 2 then has zero claims -> also
never calls the client. `client.completions.calls` stays `[]`, so the
test's own `calls[0]["messages"][0]["content"]` raises `IndexError`. Same
root cause as the NOTED BEHAVIOR CHANGE above.

- test_absence_rule_all_features_absent_yields_zero_search_calls_and_low_confidence
- test_zero_support_path_routes_to_low_confidence_with_full_decline

### Group C (1 test) -- assert calls==1, got 0

**Cause**: same as Group B (empty retrieval -> zero LLM calls anywhere in
the pipeline), different assertion shape (`len(calls) == 1` instead of
indexing `calls[0]`).

- test_empty_retrieval_proceeds_with_low_confidence_caveat

### Group D (1 test) -- `Failed: DID NOT RAISE <RuntimeError>`

**Cause**: the fixture's client always raises on `create()`, expecting
the OLD single always-one-call flow to trigger it and wrap it as
`RuntimeError("GPT-4o reading-generation call failed")`. With empty
retrieval, neither Stage 1 nor Stage 2 ever calls the client at all (same
root cause as Groups B/C), so the client's exception is never triggered
and nothing raises.

- test_client_raises_becomes_runtime_error_no_retry

### Group E (1 test) -- `AssertionError: assert True is False` (validation.passed)

**Cause**: the fixture's canned 701-word draft was meant to trip the OLD
length check, but with empty retrieval Stage 1/Stage 2 never run at all
(same root cause as Groups B/C/D) -- the final reading is decline-block-
plus-disclaimer only (short), so `_check_length` (now running on Stage
2's -- nonexistent -- output) never sees the long text and the reading
validates clean instead of failing.

- test_length_over_700_words_fails

## Full suite result

```
Before (P4 baseline): 3252 passed, 3 skipped
After (P5):           3213 passed, 3 skipped, 39 failed
```

3252 - 39 = 3213, confirming no OTHER regressions beyond the 39
catalogued above -- every one of the 3213 still-passing tests (including
all of `test_claim_extraction.py` and `test_claim_voicing.py`) is
unaffected.

## Close-out registration items to carry forward (NOT done here)

1. **NOTED BEHAVIOR CHANGE** (empty retrieval -> zero LLM calls, no
   generic low-confidence reading) needs a CLAUDE.md entry -- this is a
   real, user-visible product change (an all-absent hand now gets
   decline-block-only text, not a generic Cheiro-voiced paragraph), not
   silently absorbed.
2. **V-1/V-2/`_check_feature_coverage`/`_run_ring1_checks` deletion**
   deferred to close-out, per this prompt's own instruction -- currently
   dead code (defined, never called) in `palm_reading.py`.
3. **`_READING_SYSTEM_PROMPT`/`_OUTPUT_FORMAT_BLOCK`/`_LOW_CONFIDENCE_
   ADDENDUM`/`_READING_MODEL`/`_READING_TEMPERATURE`/`_READING_TIMEOUT_
   SECONDS`** (the old single-call generation's own prompt/config
   constants) are now unused by this module's own call sites but left
   defined, same retirement disposition as item 2 -- `_READING_TIMEOUT_
   SECONDS` specifically is still CITED (not imported) by both `claim_
   extraction._EXTRACTION_TIMEOUT_SECONDS` and `claim_voicing._VOICE_
   TIMEOUT_SECONDS`'s own comments, so deleting it needs those citations
   updated in the SAME change.
4. **P5b (test-alignment) is next** -- update/retire the 39 tests
   catalogued above to match the new two-stage architecture (most need a
   `_FakeClient` supplying valid Stage-1 JSON + a Stage-2 tagged draft,
   not a single old-style response); the 6 tests hitting the NOTED
   BEHAVIOR CHANGE (Groups B/C/D/E) need their own assertions rethought,
   not just a fixture swap.

## Verdict

One file modified, as instructed. No test file touched. 39 pre-existing
failures are EXPECTED and fully catalogued above with verified (not
inferred) root causes, grouped into 5 mechanisms. 3213/3252 tests still
pass -- no additional regressions beyond the 39. Committed locally only;
holding the push until P5b's test-alignment commit lands and the suite
is green, per the two-commit single-push discipline.
