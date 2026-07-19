# S69 F-H P4: claim_voicing test suite (new test file only)

**NEW FILE ONLY.** `tests/interpretive/test_claim_voicing.py`. No
production code changed -- `agent/interpretive/claim_voicing.py` (P3) is
untouched. No bug was exposed in it by this suite; nothing to STOP and
report.

## What landed

17 tests covering the checklist minimum. Fake OpenAI client classes
(`_FakeMessage`/`_FakeChoice`/`_FakeResponse`/`_FakeCompletions`/
`_FakeClient`) are transplanted verbatim from
`tests/interpretive/test_palm_reading.py` (same lineage
`tests/interpretive/test_claim_extraction.py` already transplanted them
from) -- cited in the file's own module docstring, not reinvented.
`_explosive_client()` (a client whose `create()` raises `AssertionError`
if invoked at all) is also transplanted from the same source, for the
"must not call the LLM" proofs.

| Test | Covers |
|---|---|
| `test_input_filter_excluded_dropped_corrective_capped_overflow_in_diagnostics_and_absent_from_prompt` | 4 claims (1 supports, 1 excluded, 2 corrective) -> `diagnostics["included_claim_ids"] == ["C1", "C3"]`, `corrective_overflow == ["C4"]`; asserts on the ACTUAL messages sent to the fake client -- the excluded and overflow claims' text never appears anywhere in the prompt |
| `test_prompt_never_contains_chunk_id` | A distinctive `chunk_id` value never appears in any sent message -- `Claim.chunk_id` is never read by this module at all |
| `test_v3_untagged_text_fails_and_retry_fed_failure_text` | Whole-text-untagged draft -> `"no recognized tag found"` -> retry message contains it -> corrected draft recovers |
| `test_v3_unknown_claim_id_tag_fails_persistent` | `[C99]` (not an included claim_id) -> persistent failure, `"C99"` present in both the failure list and the retry correction message |
| `test_v3_adjacent_double_tag_fails_persistent` | `[C1][OBS]` with nothing between them -> `"adjacent tags with no sentence between them"` |
| `test_v3_stray_bracket_token_fails_persistent` | `[NOTATAG]` -> `"unrecognized bracket token"` containing `"NOTATAG"` |
| `test_v4_claim_never_cited_fails_then_clean_retry_clears` | C1 never cited -> `"claim_coverage: claim_id(s) never cited: ['C1']"` recorded in `diagnostics["first_attempt_failures"]` -> clean retry clears, `validation_failures == ()` |
| `test_v4_persistent_failure_populates_validation_failures` | Same failure persists both tries -> `validation_failures` populated, no raise |
| `test_v5_needle_in_flow_sentence_fails` | `"life"` needle inside a `[FLOW]` sentence -> `"doctrine_guard: [FLOW]..."` |
| `test_v5_needle_in_obs_sentence_fails` | `"life"` needle inside an `[OBS]` sentence -> `"doctrine_guard: [OBS]..."` |
| `test_v5_same_needle_inside_claim_sentence_passes` | The SAME needle (`"life"`, twice) appearing only inside a `[C1]`-tagged sentence -> passes (V-5 only scans `[FLOW]`/`[OBS]` segments) |
| `test_v3_failure_gates_v4_and_v5` | A draft with a simultaneous V-3 violation (`[C99]`), a would-be V-4 violation (C1 never cited), and a would-be V-5 violation (needle in `[OBS]`) -> `validation_failures` contains ONLY `tag_legality`-class entries, proving V-4/V-5 never ran |
| `test_retry_cap_exactly_two_calls_never_three_no_raise` | Persistent failure -> exactly 2 calls (asserted via call-count, not crash-reliance past the fake's clamped-index behavior), `validation_failures` populated, no exception |
| `test_api_exception_on_first_call_raises_runtime_error_with_module_prefix` | First call raises -> `RuntimeError` matching `"claim_voicing: API call failed: network down"` |
| `test_api_exception_on_retry_call_raises_runtime_error_with_module_prefix` | Retry call raises -> `RuntimeError` matching `"claim_voicing: API retry call failed: timeout"` |
| `test_empty_claims_tuple_skips_llm_call` | Empty `claims` tuple -> LLM never called, `diagnostics["skipped"] == "no included claims to voice"`, `call_count == 0` |
| `test_all_claims_excluded_from_voice_skips_llm_call` | Every claim `excluded_from_voice=True` -> same skip behavior as the empty-tuple case |

## Full suite result

```
Before (P3 baseline): 3235 passed, 3 skipped
After (P4):            3252 passed, 3 skipped
Delta: +17 passed, 0 skipped delta, 0 failed, 0 regressions
```

No bug surfaced in `claim_voicing.py` -- every test passed on first run
against the module as committed in P3 (no test-design bugs needed
fixing this time either, unlike P2's single-feature/all-fail
interaction).

## Verdict

New test file only, as instructed. `agent/interpretive/claim_voicing.py`,
`palm_reading.py`, `app.py`, and all other test files untouched. Suite
green at 3252/3, a clean +17 over the P3 baseline. Wiring both
`claim_extraction.py` and `claim_voicing.py` into `palm_reading.py`
remains the next prompt in the F-H sequence (P5).
