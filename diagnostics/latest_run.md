# S70: stage2 first-attempt failure attribution on result + capture

**MODIFIED THREE FILES.** `agent/interpretive/palm_reading.py`
(`PalmReadingResult` new field + `complete_palm_reading()` population
only), `frontend/app.py` (`_capture_dogfood_run()`, one new adjacent
capture line -- the explicit coordinated rider per the prompt), and
their direct tests (`tests/interpretive/test_palm_reading.py`,
`tests/test_app_dogfood_capture.py`).

## Context (why)

Both pass-5 preflight re-run addenda (`diagnostics/pass5_preflight_
S70.md`, commits `908d325` and `b4dc5a1`) hit the same wall: a run with
`stage2_retry_used=True` gave no way to tell WHAT drove the retry --
`voice_result.diagnostics["first_attempt_failures"]` exists inside
`claim_voicing.voice_claims()` but was never propagated onto
`PalmReadingResult`. This closes that gap directly.

## Edit summary

1. `PalmReadingResult` gains `stage2_first_attempt_failures: tuple[str,
   ...] = ()` -- additive, defaulted, same convention as `reading_text_
   tagged`/`claims`/`stage1_retry_features`/`stage2_retry_used` before
   it. Comment block extended to explain it's distinct from `validation.
   failures` (the FINAL verdict) -- this field answers "what was wrong
   on attempt 1" even when the retry fully cleared it.
2. `complete_palm_reading()`: one new line, `stage2_first_attempt_
   failures = tuple(voice_result.diagnostics.get("first_attempt_
   failures", ()))`, passed into the `PalmReadingResult(...)`
   construction. `.get(..., ())` naturally covers both non-retry paths
   (the key is simply absent from `voice_result.diagnostics` whenever no
   retry fired, including the empty-claims early-return case) --
   verified by reading `claim_voicing.voice_claims()`'s own source
   (the key is set ONLY inside the `if failures:` retry-triggering
   branch).
3. `frontend/app.py`'s `_capture_dogfood_run()`: one new line adjacent to
   `stage2_retry_used`, semicolon-joining `reading.stage2_first_attempt_
   failures` (or `"NONE"` when empty) -- same join-or-NONE convention
   `stage1_retry_features_str`/`validation_failures_str` already use in
   this same function.

No other logic touched -- `validation`/`decline_features`/`sources`
computation, the F-G1 seam, and F-G2's `_build_display_extra_validators`
are all untouched.

## Tests

`tests/interpretive/test_palm_reading.py` (new section, "S70:
stage2_first_attempt_failures -- retry attribution"):
- (a) `test_stage2_first_attempt_failures_carries_first_draft_failure_
  verbatim` -- reuses `test_exemplar_echo_guard_fires_draft1_retries_
  and_clears_on_clean_draft2`'s exact fixture shape (draft 1 echoes,
  draft 2 clean) -- asserts `result.stage2_first_attempt_failures ==
  ("exemplar_echo: each one tells its own story",)` even though the
  final `validation.passed is True`.
- (b) `test_stage2_first_attempt_failures_empty_when_no_retry` -- a
  clean first draft (no retry) -> `stage2_first_attempt_failures == ()`.

`tests/test_app_dogfood_capture.py`:
- `_synthetic_reading()` extended with `stage2_first_attempt_failures=
  ("exemplar_echo: tells its own story to those", "jargon_blacklist:
  found antardasha")` -- 2 DISTINCT strings (not 1) specifically so the
  new capture test exercises the semicolon-JOIN behavior, not merely the
  line's presence. Docstring updated to flag the one deliberately
  unrealistic bit (`stage2_retry_used=False` alongside a non-empty
  `stage2_first_attempt_failures` -- a combination real `complete_palm_
  reading()` output would never produce, but irrelevant to what this
  fixture needs to prove: that the capture line reads whatever tuple is
  on the object, not a hardcoded value).
- (c) new `test_capture_dogfood_run_writes_stage2_first_attempt_
  failures_line` -- asserts the exact joined line `"stage2_first_
  attempt_failures: exemplar_echo: tells its own story to those;
  jargon_blacklist: found antardasha"` appears in the captured log
  content.

## Test run (targeted only, per instructions -- no full suite)

```
pytest tests/interpretive/test_palm_reading.py tests/test_app_dogfood_capture.py -q
87 passed, 4 skipped (pre-existing F-H retirement skips, unchanged)
```
