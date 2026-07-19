# S70 P6a: F5 dogfood-capture schema update for the two-stage pipeline

**MODIFIED TWO FILES.** `frontend/app.py` (`_capture_dogfood_run()` only)
and its direct test file `tests/test_app_dogfood_capture.py`. No other
app.py block touched (generate button handler / checkpoint flow are P6b,
out of scope here).

## Edits to `_capture_dogfood_run()`

1. New `### claims_inventory` section: one line per `reading.claims`
   entry (tuple order), format `claim_id | feature | chunk_id | valence |
   excluded_from_voice | exclusion_reason | condition_text | claim_text`
   (claim_text's internal newlines flattened to a single space). Excluded
   claims included. Empty case writes `claims_inventory: EMPTY` under the
   section header.
2. New `stage1_retry_features: <comma-joined or NONE>` and
   `stage2_retry_used: <bool>` lines, adjacent to the existing
   `retry_used:` (COMPAT) line in `### ring1_validation`.
3. New `validation_failures: <semicolon-joined or NONE>` line, verbatim
   from `reading.validation.failures`.
4. Removed the `valid_chunk_ids_count: unavailable` line and its
   S68 F-C comment block (accepted gap (e)) -- retired, since
   claims_inventory's per-claim `chunk_id` now captures anchor
   membership directly. **Flag for a future close-out prompt**: update
   CLAUDE.md's "Known Source Divergences / Accepted Gaps (V1)" register
   (item (e)) and `palm_reading.py`'s own gap-register comment to mark
   gap (e) retired -- not done in this prompt (explicitly out of scope:
   "do not edit CLAUDE.md").
5. No warnings line added (F-A coverage retired, `ValidationReport.
   warnings` is always `()` under the current architecture) -- per
   instructions, confirmed no other change needed here.
6. Updated the `### READING (TAGGED)` section's comment: now documents
   Stage 2's `{[C<n>], [OBS], [FLOW]}` tag vocabulary in place of the
   retired single-call architecture's `{[OBS], [<chunk_id>]}`, and points
   at claims_inventory as the way to resolve a `[C<n>]` tag back to its
   `chunk_id`/`feature`.

## Test file

`_synthetic_reading()` extended with 2 claims (`C1` clean, `C2`
`excluded_from_voice=True` / `exclusion_reason="precondition
unverified"` / with a `condition_text` and an embedded `\n` in
`claim_text` to exercise the flatten-to-space rule) plus
`stage1_retry_features=("life line",)` and `stage2_retry_used=False`.

7 new tests added:
- `test_capture_dogfood_run_writes_claims_inventory` -- both claim lines
  present verbatim (all 8 fields), newline flattened.
- `test_capture_dogfood_run_claims_inventory_empty` -- `claims=()` writes
  `claims_inventory: EMPTY`.
- `test_capture_dogfood_run_writes_two_stage_retry_fields` -- both new
  fields reflect actual values.
- `test_capture_dogfood_run_stage1_retry_features_none_when_empty` --
  empty tuple writes `NONE`.
- `test_capture_dogfood_run_writes_validation_failures_line` --
  semicolon-joined, multi-failure case.
- `test_capture_dogfood_run_validation_failures_none_when_empty` --
  empty tuple writes `NONE`.
- `test_capture_dogfood_run_no_longer_writes_valid_chunk_ids_count` --
  removed line's substring absent from output.

No pre-existing test asserted the removed `valid_chunk_ids_count` line
(confirmed via grep before editing), so no existing test needed updating
beyond the new module-docstring note.

## Result

**Targeted run only** (S70 cost discipline, no full-suite run):
`pytest tests/test_app_dogfood_capture.py` -> **13 passed** (6
pre-existing + 7 new), 0 failures, 0 deviations from the instructing
prompt.

Full-suite run deferred to session end per instructions.
