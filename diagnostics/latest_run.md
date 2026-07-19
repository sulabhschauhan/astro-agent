# S70 F-G1: extra-validator injection seam in voice_claims

**MODIFIED TWO FILES.** `agent/interpretive/claim_voicing.py`
(`voice_claims()` signature/body + new `_run_extra_validators` helper
only) and `tests/interpretive/test_claim_voicing.py` (5 new tests,
appended). `palm_reading.py` untouched, per this prompt's own scope lock
-- wiring the actual display validators through this seam is F-G2.

## Context (why)

`diagnostics/pass5_preflight_S70.md` (prior task) caught a live ABORT:
Stage 2 voiced a draft that verbatim-echoed both R2 exemplar sentences
(`exemplar_echo: i have examined many hands in`). The exemplar-echo check
only runs at the outer display-check layer (`palm_reading._run_display_
checks`, called once, post-Stage-2, no retry), so Stage 2's own internal
F2c retry (which DID fire, for an unrelated `thumb` extraction reason)
never saw the echo failure as a correction instruction. Pre-ratified fix
(CLAUDE.md F-G residual note): feed display validators into Stage 2's own
retry loop. This prompt is step 1 (the seam) only.

## Edit summary

1. **New keyword-only param** `extra_validators: tuple = ()` on
   `voice_claims()`. Each element: `(tagged_draft: str) -> list[str]`.
   Default `()` -- every existing call site (`palm_reading.
   complete_palm_reading()`, all pre-F-G1 tests) is byte-for-byte
   unaffected; verified directly (test (d) below).
2. **New helper** `_run_extra_validators(text, extra_validators) ->
   list[str]` -- calls each callable against the raw tagged draft (same
   text V-3/V-4/V-5 see, no stripping), concatenates failures in order.
   No import of `palm_reading` anywhere (circular-import lock preserved
   -- `claim_voicing.py` still has zero references to that module).
3. **Merge point**: after `failures = _run_validators(raw,
   included_claim_ids)` on BOTH the first-draft and retry-draft branches,
   `failures = failures + _run_extra_validators(raw, extra_validators)`.
   The combined list is what drives the single F2c retry decision (`if
   failures:`) and the final `validation_failures` -- an extra-validator-
   only failure on draft 1 now triggers the retry exactly like a V-3/V-4/
   V-5 failure would, with its string included in the correction message
   `_build_retry_messages` sends.
4. **Exception discipline**: `_run_extra_validators` has NO try/except --
   a raising callable propagates uncaught through `voice_claims` (a
   caller bug, not a voice failure; swallowing it would silently disable
   the guard). Verified directly (test (c)).
5. **Diagnostics**: `diagnostics["extra_validator_failures"]` set to the
   first-attempt extra-validator failure list, ONLY when non-empty,
   alongside the existing `first_attempt_failures` key (which now
   includes the merged V-3/V-4/V-5 + extra set). Both keys are absent
   entirely when nothing failed on the first draft (verified in test (d)).
6. Hard 2-call cap: UNCHANGED -- no new call sites added, `call_count`
   logic untouched.

## Deviations from the instructing prompt

None. All 5 numbered edit points and all 5 lettered test scenarios were
implemented as specified; no additional loosening, no palm_reading.py
touch, no re-ordering relative to V-3/V-4/V-5 beyond what was asked
("after V-3/V-4/V-5 on BOTH the first draft and the retry draft").

One judgment call not fully dictated by the prompt (documented here per
Working Style #4 discipline, though not a numeric threshold): whether
`_run_extra_validators` should be gated on V-3 passing (skipped when
`_run_validators` already failed) or run unconditionally every time. Ran
UNCONDITIONALLY -- the instruction says "after V-3/V-4/V-5" (sequential
position), not "only if V-3/V-4/V-5 pass" (conditional gating), and extra
validators are independent, caller-owned checks with no dependency on
this module's own tag-position state, so there is no correctness reason
to skip them just because a tag-legality issue also exists on the same
draft.

## Tests added (`tests/interpretive/test_claim_voicing.py`)

(a) `test_extra_validator_fails_draft1_passes_draft2_retry_fires_and_clears`
(b) `test_extra_validator_fails_both_drafts_exactly_two_calls_no_third`
(c) `test_extra_validator_raising_propagates_uncaught`
(d) `test_default_extra_validators_empty_tuple_zero_behavior_change`
(e) `test_extra_validator_failures_recorded_in_diagnostics_first_attempt_only`

All reuse the existing `_FakeClient`/`_claim` builders (transplanted from
`test_palm_reading.py`'s lineage) -- no new fixture machinery invented.

## Test run (targeted only, per instructions -- no full suite)

```
pytest tests/interpretive/test_claim_voicing.py -q
22 passed (17 pre-existing + 5 new), 0 failed
```

## Carry-forward (not this prompt's scope, flagged for F-G2)

F-G2 must: (a) build the actual display-validator callables in
`palm_reading.py` (jargon/self-help/dates/length/banned-mention/
exemplar-echo), each wrapping `_strip_stage2_tags` internally before
running its check (per this module's contract: `claim_voicing` passes
the RAW tagged draft, stripping is the caller's job); (b) wire them into
`complete_palm_reading()`'s call to `voice_claims(..., extra_validators=
(...))`; (c) decide whether `_run_display_checks`'s own post-hoc call
stays as a final belt-and-suspenders check on the LAST draft, or is fully
subsumed by the new retry-fed path -- not decided here, this prompt only
built the seam.
