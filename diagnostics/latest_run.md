# S69 F-H P2: claim_extraction test suite (new test file only)

**NEW FILE ONLY.** `tests/interpretive/test_claim_extraction.py`. No
production code changed -- `agent/interpretive/claim_extraction.py` (P1)
is untouched. No bug was exposed in it by this suite; nothing to STOP
and report.

## What landed

15 tests covering the checklist minimum plus a couple of cheap
belt-and-suspenders extras. Fake OpenAI client classes
(`_FakeMessage`/`_FakeChoice`/`_FakeResponse`/`_FakeCompletions`/
`_FakeClient`) are transplanted verbatim from
`tests/interpretive/test_palm_reading.py` (same shapes, same
`responses=[(content, exception), ...]` call-order convention) -- cited
in the file's own module docstring, not reinvented.

| Test | Covers |
|---|---|
| `test_happy_path_two_features_claims_rekeyed_and_diagnostics_populated` | Happy path, 2 features, both raw responses reuse model-emitted `claim_id="C1"` -> proves re-keying (`C1`, `C2` in the final result), diagnostics populated (`call_count`, `retry_used`, `status`, `claim_count`, `overlap_scores`) |
| `test_e1_illegal_chunk_id_retry_fed_failure_text_persistent_failure` | E-1: out-of-set `chunk_id` on both tries -> retry message contains the failure text (`chunk_id`, "not in this feature's own gated set") -> persistent -> `failed_features` |
| `test_e2_invalid_valence_triggers_retry_then_recovers` | E-2: invalid `valence` -> retry fed "invalid valence" -> corrected response recovers, feature succeeds |
| `test_e2_missing_required_field_triggers_retry_persistent_failure` | E-2: `condition_text`/`observation_basis` missing -> retry fed "missing keys" -> persistent -> `failed_features` |
| `test_e3_overlap_below_floor_triggers_retry_persistent_failure` | E-3: hand-computed overlap 0.20 (below the 0.40 floor) -> retry -> persistent -> `failed_features` |
| `test_e3_overlap_at_or_above_floor_passes` | E-3: hand-computed overlap 0.60 (at/above floor) -> passes first try, no retry, overlap recorded in diagnostics |
| `test_e4_conditional_excluded_unless_condition_text_matches_confirmed_observation` | E-4: `condition_text` substring-matched in `texts_by_feature` -> not excluded; NOT matched -> `excluded_from_voice=True, exclusion_reason="precondition unverified"`, claim retained in inventory + exclusion ledger |
| `test_e4_corrective_claim_retained_not_excluded` | Corrective valence, no `condition_text` -> retained, never excluded |
| `test_retry_cap_exactly_two_calls_never_three` | Persistent failure -> exactly 2 calls, proven by asserting `.calls` length (not relying on a crash past the fake's clamped-index behavior) |
| `test_api_exception_on_first_call_marks_feature_failed_others_succeed_no_raise` | API exception on the very first call for one feature -> `failed_features`, no retry attempted, another feature's claims still returned, no raise |
| `test_api_exception_on_retry_call_marks_feature_failed_no_raise` | API exception specifically during the retry call (after a validation failure) -> `failed_features`, `first_attempt_failures` logged, no raise |
| `test_all_features_fail_raises_runtime_error` | Every attempted feature fails both tries -> `RuntimeError` |
| `test_empty_claims_list_is_legitimate_not_a_failure` | Model returns `"claims": []` -> `status="ok"`, `claim_count=0`, no retry |
| `test_feature_with_empty_gated_chunks_is_skipped_entirely` (extra) | A feature with zero gated chunks never appears in diagnostics or `failed_features`, no LLM call made for it |
| `test_all_gated_empty_returns_empty_result_no_raise` (extra) | Every feature has zero gated chunks -> empty, non-raising `ExtractionResult`, zero LLM calls (belt-and-suspenders, same convention as `test_palm_reading.py`'s `_explosive_client`) |

## A test-design bug caught and fixed during this session (not a production bug)

Four persistent-failure tests (E-1, E-2 missing-field, E-3, retry-cap)
were initially written with only ONE feature in `gated_results`. Since
`extract_claims`'s `RuntimeError` fires whenever *every* attempted
feature fails, a single-feature persistent failure IS "all features
failed" by construction -- these 4 tests raised `RuntimeError`
unexpectedly on first run, not because of a production defect, but
because the test fixtures didn't account for that interaction. Fixed by
adding a second, always-succeeding feature ("thumb") alongside the
feature under test in each of the 4 cases, isolating the intended
single-feature behavior from the separate all-fail path (which has its
own dedicated test, `test_all_features_fail_raises_runtime_error`).

## E-3 overlap fixture -- hand-computed math (also commented in the test file)

Chunk text content words (8, none are stopwords): `alpha, bravo, charlie,
delta, echo, foxtrot, golf, hotel`.
- PASS claim: `alpha, bravo, charlie, xray, yankee` (5 words). Shared =
  `{alpha, bravo, charlie}` = 3. `overlap = 3 / min(5, 8) = 0.60` -- above
  the 0.40 floor.
- FAIL claim: `alpha, xray, yankee, zulu, whiskey` (5 words). Shared =
  `{alpha}` = 1. `overlap = 1 / min(5, 8) = 0.20` -- below the 0.40 floor.

## Full suite result

```
Before (P1 baseline): 3220 passed, 3 skipped
After (P2):            3235 passed, 3 skipped
Delta: +15 passed, 0 skipped delta, 0 failed, 0 regressions
```

## Verdict

New test file only, as instructed. `agent/interpretive/claim_extraction.py`
untouched -- no bug exposed, nothing to STOP and report. Suite green at
3235/3, a clean +15 over the P1 baseline. Wiring `extract_claims` into
`palm_reading.py` remains the next prompt in the F-H sequence.
