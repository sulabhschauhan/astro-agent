# S68 F-A: coverage check -- test alignment + new coverage tests

Two-commit sequence per instructing prompt's push discipline (F-C incident,
not repeating it): Commit A carries the already-correct implementation
(uncommitted from the prior prompt), Commit B carries this test-alignment
pass. Full suite verified green LOCALLY before either commit is pushed --
main is never red remotely at any point.

## Part 1 -- alignment: 1 test broke, exactly as predicted

Grepped this file for every assertion shape that would be sensitive to an
extra coverage-only retry call: `completions.calls) ==` (13 hits) and
`retry_used is False` (2 hits). Walked each hit against the actual
observed/supported-feature shape of its test:

- **Broke:** `test_exactly_one_llm_call_when_first_draft_passes`
  (line ~456). Fixture observes 2 features (life line, heart line, both
  supported via `_FakeSearch([_chunk()])`), stub is `_CLEAN_STUB_TEXT`
  (entirely `[OBS]`-tagged, cites nothing). Both features come back
  `supported but never cited` -> 2 coverage misses -> retry fires ->
  2 LLM calls, not the asserted 1.
- **Did NOT break** (11 other `== N` call-count hits, both
  `retry_used is False` hits): every one of them either (a) already
  expects >=1 failure for an unrelated reason (jargon/self-help/banned-
  mention/exemplar-echo), so the retry it triggers was already accounted
  for regardless of coverage, or (b) doesn't assert call count/retry_used
  at all -- a silent coverage-triggered second call doesn't touch what
  the test actually checks (sources, search-call count, message[0]
  content, etc.). Confirmed by inspection, not guessed: for each, traced
  which registry features are `supported` given that test's stub fixture
  and whether its stub cites them.

Fix: added a dedicated `_TWO_FEATURE_CHUNK` / `_CLEAN_TWO_FEATURE_STUB_TEXT`
pair (not a `_CLEAN_STUB_TEXT` edit -- that constant is shared by ~9 other
tests and the instructing prompt explicitly names this "dedicated variant
stub" branch to avoid perturbing them). The chunk deliberately carries
BOTH needles ("life", "heart") so the same chunk_id survives the support
gate under both observed features; the stub cites it once, satisfying
coverage for both (the shared-chunk accepted-gap mechanism doing double
duty as the fix). `test_exactly_one_llm_call_when_first_draft_passes` now
also asserts `result.validation.warnings == ()` to make the "truly clean"
claim explicit, not just implicit in the call count.

No other stub text or test file required a change.

## Part 2 -- 7 new coverage tests

Direct-function tests (`palm_reading._check_feature_coverage`, same
convention as items 3/16's direct-pattern proofs):
1. `test_coverage_supported_feature_never_cited_produces_verbatim_warning`
2. `test_coverage_obs_only_mention_of_supported_feature_still_a_miss`
   (landmark-exclusion proof)
3. `test_coverage_cited_chunk_id_marks_feature_addressed_no_warning`
4. `test_coverage_shared_chunk_id_cited_once_marks_both_features_addressed`
   (accepted false-positive boundary, documented not fixed)

`generate_palm_reading()` integration tests:
5. `test_coverage_only_retry_fires_and_clean_retry_clears_warnings` --
   zero Ring 1 failures, one coverage miss on the first draft -> retry
   fires via the existing mechanism (`retry_used=True`, no new flag);
   retry cites the chunk -> clean final pass, empty warnings.
6. `test_coverage_fail_open_final_still_missing_warning_present_reading_displays`
   -- retry draft STILL doesn't cite -> no third attempt, `passed=True`,
   warning present in `validation.warnings`, `DISCLAIMER` present in
   `reading_text` (proves display is never blocked).

Dataclass default:
7. `test_validation_report_warnings_defaults_to_empty_tuple` -- bare
   `ValidationReport(passed=True, failures=())` (the exact shape
   `tests/test_app_dogfood_capture.py` already uses) still works.

## MEASURE-FIRST demo 1: coverage-warning verbatim (supported thumb, zero citations)

Ran `_check_feature_coverage` directly (not through the full LLM-call
pipeline -- deterministic function, no live API needed) against a
synthetic supported-but-uncited `thumb`:

```python
>>> from agent.interpretive import palm_reading
>>> gated_results = {"thumb": [{"chunk_id": "cheiroslanguageo00chei_1_p200_c1", "text": "...", "score": 0.6}]}
>>> tagged_text = "The hand shows a broad, strong thumb.[OBS]"
>>> palm_reading._check_feature_coverage(tagged_text, gated_results, ("thumb",))
['coverage: thumb supported but never cited']
```

Verbatim match to the design's required warning string
(`"coverage: <feature> supported but never cited"`). Codified as
`test_coverage_supported_feature_never_cited_produces_verbatim_warning`.

## MEASURE-FIRST demo 2: shared-chunk false-positive boundary

Same function, a chunk_id gated under two DIFFERENT features (`thumb`,
`fingers`), cited once:

```python
>>> shared_chunk = {"chunk_id": "cheiroslanguageo00chei_1_p210_c3", "text": "...", "score": 0.6}
>>> gated_results = {"thumb": [shared_chunk], "fingers": [shared_chunk]}
>>> tagged_text = "The thumb is broad and strong.[cheiroslanguageo00chei_1_p210_c3]"
>>> palm_reading._check_feature_coverage(tagged_text, gated_results, ("thumb", "fingers"))
[]
```

Confirms the accepted V1 gap verbatim: citing a chunk shared by two
features marks BOTH addressed, even though the citing sentence is only
actually about `thumb` -- `fingers` gets a free pass with zero warning.
Direction of error: a real omission (fingers never really discussed) can
go un-warned; the check never produces a spurious warning for a
genuinely-cited feature. Codified as
`test_coverage_shared_chunk_id_cited_once_marks_both_features_addressed`.

## Full pytest result

`python -m pytest -q tests/interpretive/test_palm_reading.py`:
**60 passed** (was 53 before this pass; +7 new coverage tests, 0 broken,
0 skipped).

`python -m pytest -q` (full suite): **3220 passed, 3 skipped** --
baseline was 3213/3; delta is exactly the 7 new tests, 0 regressions
anywhere else in the suite. Verified LOCALLY green before either commit
of the 2-commit sequence was pushed.
