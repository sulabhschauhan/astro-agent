# S69 F-H P5b: test alignment to two-stage pipeline

**MODIFIED ONE FILE.** `tests/interpretive/test_palm_reading.py`. No
production code changed. Alignment exposed no genuine `palm_reading.py`
bug -- every failure traced to a test fixture built for the retired
single-call architecture, not a defect in the new pipeline. Full suite
green; both this commit and P5's commit are pushed together in ONE push,
per the two-commit single-push discipline.

## Shared helper (built once, per the instructing prompt)

`_two_stage_setup(feature_chunks, voice_text_builder)` builds the
`responses=[...]` sequence a `_FakeClient` needs to answer BOTH stages:
one valid Stage-1 JSON extraction response per feature (registry order,
one claim per chunk, `claim_text` defaulting to the chunk's own text so
the E-3 paraphrase floor is trivially satisfied), then one Stage-2
tagged-voice-text response. `_single_feature_client(feature, chunk,
voice_text)` is a convenience for the common single-feature/single-chunk
case (claim_id is always deterministically "C1"). Every rewritten test
below uses one of these two, with per-test deviations (custom claim
content, multi-feature setups, deliberately-broken Stage-1/Stage-2
responses for retry/exception tests) staying local to that test.

## Alignment by P5's 5 root-cause groups

- **Group A (Stage-1 JSON-parse, 34 originally failing)**: fixtures
  rewritten to the two-stage shape via the shared helper. Feature-noun
  mentions ("life line", "sun line", etc.) were moved OUT of `[FLOW]`/
  `[OBS]`-tagged content and INTO `[C<n>]`-tagged content throughout --
  claim_voicing's own V-5 doctrine guard fails any `[FLOW]`/`[OBS]`
  sentence naming a palm-feature noun, which the OLD single-tag stubs
  (e.g. the original `_CLEAN_STUB_TEXT`, one `[OBS]` tag over a whole
  paragraph mentioning "life line") would now trip on their own, before
  ever reaching palm_reading.py's display checks.
- **Group B/C (empty-retrieval, 3 originally failing)**: rewritten to the
  NEW ratified contract -- zero LLM calls, `validation.passed=True`,
  `sources == ()`, DISCLAIMER present, decline block reflecting whichever
  features actually land in `unsupported_features` (verified precisely,
  not assumed -- see the CAUGHT ISSUE below).
- **Group D (client-raises, 1)**: renamed `test_stage1_client_raises_
  becomes_runtime_error` -- the OLD "GPT-4o reading-generation call
  failed" message no longer exists; this is `claim_extraction.extract_
  claims`'s own message now, and no Stage-1 retry is attempted on a
  first-call API exception.
- **Group E (length-check false-pass under empty retrieval, 1)**: folded
  into `test_length_over_700_words_fails`'s ordinary rewrite (a real,
  non-empty retrieval fixture that reaches the length check directly,
  rather than one that accidentally hit the empty-retrieval path).

## `retry_used` OR-composition (4 tests replace/extend 4 old ones)

The OLD "F2c retry on a self-help/jargon/date/length failure" tests
(`test_retry_after_failed_first_draft_then_clean_retry_passes`,
`_still_fails_stays_failed`, `test_retry_call_raises_becomes_runtime_
error_no_third_call`) tested a mechanism that no longer exists: display
checks do NOT retry in the new pipeline (P5's own "NO retry at this
layer" rule). Re-testing Stage 2's own V-3/V-4/V-5 retry logic here would
also be redundant with `tests/interpretive/test_claim_voicing.py`'s own
exhaustive coverage. Replaced with 4 INTEGRATION-level tests proving
`palm_reading.py` correctly surfaces the retry_used OR-composition and
the two new precise fields:
- `test_retry_used_true_when_stage1_retries` -- Stage-1-only retry ->
  `stage1_retry_features=("life line",)`, `stage2_retry_used=False`,
  `retry_used=True`.
- `test_retry_used_true_when_stage2_retries` -- Stage-2-only retry ->
  `stage1_retry_features=()`, `stage2_retry_used=True`, `retry_used=True`.
- `test_stage2_persistent_failure_stays_failed_no_third_stage2_call` --
  both Stage-2 attempts fail -> `validation.passed=False`, no raise, no
  3rd call.
- `test_stage2_retry_call_raises_becomes_runtime_error` -- Stage-2's
  retry call itself raising -> `claim_voicing`'s own RuntimeError message,
  propagated uncaught.

`test_exactly_one_llm_call_when_first_draft_passes` renamed `test_
exactly_n_plus_one_llm_calls_when_first_draft_passes` -- the invariant
itself changed (N Stage-1 calls + 1 Stage-2 call, not "exactly 1").

## Display-check "retry-then-clean" tests become single-shot

Every test that previously proved "first draft trips a display check,
retry is clean" (self-help x1 originally, exemplar-echo x1, banned-
mention x1, doctrine-inversion x1) is now a single-shot pass/fail --
display checks don't retry, so there is no retry-then-clean scenario left
to prove at this layer. Renamed where the old name implied a retry
(`test_exemplar_echo_guard_fires_first_draft_retried_clean` ->
`test_exemplar_echo_guard_fires_single_shot_no_retry`, etc.).

## Retired-validator tests: skipped, not deleted (4, per instruction)

| Test | Reason |
|---|---|
| `test_end_to_end_tagged_draft_with_cited_chunk_validates_clean_and_strips_tags` | V-1/V-2 no longer invoked; this test exercised them end-to-end through `generate_palm_reading` |
| `test_coverage_only_retry_fires_and_clean_retry_clears_warnings` | `_check_feature_coverage`'s retry-feed wiring no longer exists |
| `test_coverage_fail_open_final_still_missing_warning_present_reading_displays` | same -- `_check_feature_coverage` retired |
| `test_per_feature_map_ordering_and_dedupe_for_display` | **Discovered during this alignment pass, not previously flagged in P5's own report**: `_assemble_retrieved_passages` (the old single-prompt `### {feature}` assembler) is ALSO no longer called by the two-stage pipeline -- this test asserted on that assembly's dedupe/display-order behavior via the (no-longer-representative) `client.completions.calls[0]` message content. Flagged here, not silently expanded scope; `_assemble_retrieved_passages` itself is untouched and could get a direct unit test (same convention as V-1/V-2/coverage's own direct tests) if its logic is still wanted -- not done in this prompt. |

All 4 direct-unit-test groups (V-1/V-2 functions, `_check_feature_
coverage` function, `ValidationReport` defaults) that call the retired
functions DIRECTLY (not through `generate_palm_reading`) stay passing,
unmodified.

## CAUGHT ISSUE (self-corrected during this session, documented not silently fixed)

First draft of `test_absence_rule_all_features_absent_yields_zero_
search_and_llm_calls` assumed ALL 10 registry features would be exempt
from the decline block (genuine negative absence). Running the test
falsified this: of the 10, only 7 (life/head/heart/fate/thumb/fingers/
marks) are genuine negative absence (each is absence-phrased on its own
mentioning source); the other 3 (sun line, mount of venus, mount of
jupiter) are sub-features NEVER NAMED at all in the fixture text (OTHER
LINES/MOUNTS present but say neither "sun" nor "venus"/"jupiter") --
`_is_genuine_negative_absence` requires an actual mentioning source, so
"never mentioned" is NOT the same as "genuinely absent" and these 3 land
in `unsupported_features`/the decline block, exactly as they did before
P5's wiring. Fixed by asserting the actual (verified, not assumed)
`unsupported_features` tuple and the corresponding decline text, per the
module's own `_build_decline_block`.

## Full suite result

```
Before (P5, pre-alignment): 3213 passed, 39 failed, 3 skipped
After (P5b):                3249 passed,  0 failed, 7 skipped
```

Skip inventory (7 total): 3 pre-existing, unrelated to F-H (`tests/
calculations/test_dignity.py` -- Moon/Rahu/Ketu "MT spans the full sign"
out-of-domain edge cases) + 4 new F-H retirement skips (table above).

## Verdict

One test file modified, as instructed. No production code touched, no
genuine bug exposed. Full suite green: 3249 passed, 0 failed, 7 skipped
(4 new + 3 pre-existing). Both this commit and P5's `62c4a5d` are pushed
together in one push, closing out the two-commit single-push discipline
for the P5/P5b pair. Next in the F-H sequence: close-out (CLAUDE.md
registration of the NOTED BEHAVIOR CHANGE, the V-5/gap-(a)/(f) items from
P1-P4, the accepted-deviation entries, and the newly-discovered
`_assemble_retrieved_passages` retirement).
