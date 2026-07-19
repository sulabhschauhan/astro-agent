# S70 P6b: two-mode Stage-1 checkpoint (dogfood blocking / end-user expandable)

**MODIFIED THREE FILES.** `frontend/app.py` (palm-generation button block +
new checkpoint block only), `tests/test_app_dogfood_capture.py` (same
task), and one explicit rider: `agent/interpretive/palm_reading.py`'s
`complete_palm_reading()` docstring wording ("inspects/edits `prep.claims`"
-> "inspects/acks (ACK-ONLY -- claims are never edited; S70 ruling)").
No other `palm_reading.py` changes. P6a's capture-schema lines (be64da6)
untouched.

## Design implemented (as locked, not redesigned)

- **END-USER path** (`_DOGFOOD_CAPTURE` off): unchanged behavior --
  button calls `generate_palm_reading()` synchronously. Added one
  collapsed `st.expander("Claims inventory")` below the "Classical
  sources" expander in the shared reading-display block (renders for
  both paths once a `PalmReadingResult` exists -- harmless/still useful
  on the dogfood path post-ack, and keeps the display logic in one
  place rather than duplicated per path). Non-blocking, display-only,
  never gates the reading.
- **DOGFOOD path** (`_DOGFOOD_CAPTURE` on): button calls
  `prepare_palm_reading()` only, stores the `PalmReadingPrep` in
  `st.session_state.palm_prep`, clears `palm_reading_result`, reruns.
  A new main-area block (`if palm_prep is not None and
  palm_reading_result is None`) renders the BLOCKING claims panel:
  full `prep.claims` (incl. excluded, same `claim_id | feature |
  chunk_id | valence | included/excluded(reason)` fields), plus
  `stage1_retry_features`/`stage1_failed_features` from
  `prep.diagnostics`. Two buttons:
  - **Ack** -> `complete_palm_reading(prep)`, sets
    `palm_reading_result`, clears `palm_prep`, then fires the existing
    P6a `_capture_dogfood_run()` capture unchanged (recomputes the
    confirmed-description args from current session state -- safe
    because every site that mutates those descriptions also clears
    `palm_prep`, so prep and the confirmed strings can never diverge
    while a checkpoint is pending).
  - **Decline** -> new module-level helper `_capture_checkpoint_declined
    (prep)` appends a `## CHECKPOINT-DECLINED <iso-timestamp>` block
    (claims_inventory in the P6a pipe format + stage1_retry_features +
    stage1_failed_features, NO reading fields), fail-soft try/except at
    the call site (same pattern as `_capture_dogfood_run`'s call site,
    not baked into the helper itself), then clears `palm_prep`. No
    voicing call.
  - ACK-ONLY: the panel renders claims via `st.caption()` only -- no
    edit widgets of any kind.

## Errors

- `prepare_palm_reading` (`ValueError`/`RuntimeError`) -> existing
  try/except `st.error()` pattern, in the button handler.
- `complete_palm_reading` (`RuntimeError`) -> same `st.error()` handling
  in the Ack button handler; on exception `palm_prep` is deliberately
  NOT cleared (no `st.session_state.palm_prep = None` inside that
  except branch) -- retained so the user can retry Ack or Decline.

## State discipline (S65 4a precedent -- treated as hardest case)

`st.session_state.palm_prep = None` added to the session-state defaults
block alongside `palm_reading_result`. **Grepped every
`palm_reading_result = None` assignment and mirrored it 1:1** with an
adjacent `palm_prep = None` at matching indentation.

**24 clear sites found, all 24 edited** (verified post-edit by grepping
every `palm_reading_result = None` line and checking the very next
source line is the matching `palm_prep = None`, at the correct
indentation, for all 24): left-palm hard-reject / same-image-uploaded /
describe-RuntimeError / reupload-clear (4); left-hand swap-regen success
x2 + failure x2 + no-partner-to-swap-with (5); left-desc discard (1);
right-palm hard-reject / same-image-uploaded / describe-RuntimeError /
reupload-clear (4); right-hand swap-regen success x2 + failure x2 +
no-partner-to-swap-with (5); right-desc discard (1); hand-detail
analyse-success / analyse-ValueError / reupload-clear (3); hand-detail
discard (1). Total 4+5+1+4+5+1+3+1 = 24, matches the grep count exactly.

A new "Generate Palm Reading" click while a checkpoint is already
pending simply overwrites `palm_prep` with the fresh
`prepare_palm_reading()` result (plain reassignment, no extra guard
needed).

## Structure

`_capture_checkpoint_declined(prep)` is a module-level helper (same
placement/style as `_capture_dogfood_run`, immediately after it),
direct-import testable.

## Tests (`tests/test_app_dogfood_capture.py`)

1. **AppTest load smoke** (flag on/off): 2 new tests confirming the
   `palm_prep` default and the new checkpoint-panel `if` don't break
   module-level execution or write to the log without a real
   generation/checkpoint. **CAUGHT ISSUE, self-corrected before
   reporting**: placing these next to the OTHER new P6b tests (bottom
   of file, after the file's many bare `import frontend.app as app`
   direct-import tests) caused a spurious `st.button() can't be used in
   an st.form()` failure -- confirmed unrelated to any P6b production
   code (the same test passes in isolation; the pre-existing 2 AppTest
   tests at the top of the file never hit this because they run before
   any bare import pollutes Streamlit's widget/form state within the
   pytest process). Fixed by relocating both new AppTest tests directly
   alongside the original 2 AppTest tests near the top of the file,
   documented inline (both in the module docstring and an inline
   comment) so a future edit doesn't silently move them back into the
   failure-prone position.
2. **Direct-import tests for `_capture_checkpoint_declined`** with a
   synthetic `PalmReadingPrep` (`_synthetic_prep()`, 2 claims -- one
   clean, one `excluded_from_voice` with a `condition_text` and an
   embedded newline in `claim_text` to exercise the flatten-to-space
   rule, same claims as P6a's `_synthetic_reading()` for consistency):
   claims_inventory lines present (both claims, all 8 fields, newline
   flattened), stage1_retry_features/stage1_failed_features lines
   present, NO reading_text/READING (TAGGED)/sources/ring1_validation/
   feature_support lines, empty-claims case writes `claims_inventory:
   EMPTY`, and append-not-truncate across two calls.

AppTest **cannot** drive a file upload or button state deep enough to
reach the palm-generation button, the checkpoint panel, or Ack/Decline
-- true end-to-end checkpoint simulation is NOT attempted here (same
limitation the pre-existing S67 note already documents for
`generate_palm_reading()`). This is a genuine coverage limit, not an
oversight.

## Result

**Targeted run only** (S70 cost discipline, no full-suite run):
`pytest tests/test_app_dogfood_capture.py` -> **20 passed** (13
pre-existing/P6a + 2 new AppTest load-smoke + 5 new direct-import), 0
failures, 0 deviations from the instructing prompt beyond the
self-corrected test-placement issue above.

Full-suite run deferred to session end per instructions.
