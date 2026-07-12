# S66 Task 6 (F1) — hand_detail human checkpoint

Self-gated. Source: `frontend/app.py` (+ CLAUDE.md lock-wording
ride-along, docs). Closes the Ring 3 pass-1 finding
(`diagnostics/ring3_palm_rubric_S66.md`, Verdict failure #2): the
`hand_detail` vision output entered `generate_palm_reading()` with no
display or user confirmation, unlike palm_left/palm_right.

## Step 1 — Audit (pre-edit)

- **Describe call timing**: already fired at upload-time (pre-edit
  line 653-667, guarded by the `_hand_detail_image_name` name-change
  check) — same trigger pattern as the palms. No move-to-upload-time
  needed.
- **Session keys held (pre-edit)**: `hand_detail_str` (description
  text), `_hand_detail_image_name` (image-name guard). Missing,
  relative to the palms' discipline: `hand_detail_hash`,
  `hand_detail_bytes`, `hand_detail_confirmed`.
- **Path to generation (pre-edit)**: `hand_detail=st.session_state.get("hand_detail_str")`
  passed unconditionally at the "Generate Palm Reading" button — no
  display, no confirm/discard gate. Confirmed zero checkpoint existed.

## Step 2 — Fix applied

Mirrors the palms' review/confirm/discard checkpoint pattern (NOT the
palms' hand-identity/swap logic — that's left/right-ambiguity-specific
and doesn't apply to the single hand_detail slot):

- New session-state keys: `hand_detail_hash`, `hand_detail_bytes`,
  `hand_detail_confirmed` (default `False`), added alongside the
  existing `hand_detail_str`/`_hand_detail_image_name` defaults.
- Upload block now stores bytes + hash (mirrors `palm_left_hash`/
  `palm_left_bytes`), sets `hand_detail_confirmed = False` on every
  new upload, and clears `palm_reading_result` on upload, describe
  failure, and file removal — same as the palm blocks.
- New review block (`st.container()` + bold `st.markdown` label, per
  the S66 Task 3 nested-expander lesson — never `st.expander` inside
  the upload expander): unconfirmed state shows "Review hand detail
  description" + "Looks right — use this description" /
  "Discard — re-upload" buttons; confirmed state shows a caption +
  "Hand detail description" read-only.
- Discard clears `hand_detail_str`/`hash`/`bytes`/`confirmed`/
  `_hand_detail_image_name`/`palm_reading_result` — same clear-set as
  the palms' discard buttons.
- Generate button now computes `_confirmed_hand_detail =
  st.session_state.hand_detail_str if st.session_state.hand_detail_confirmed
  else None` and passes that (not the raw `hand_detail_str`) to
  `generate_palm_reading()`.
- Comment above the generation block updated: "only confirmed
  vision-derived descriptions are ever passed through (palm_left,
  palm_right, hand_detail alike, CLAUDE.md 'Palm human checkpoint'
  lock)".

## Step 3 — CLAUDE.md lock extended

"Palm human checkpoint" (Session 65) reworded to: "ALL vision-derived
descriptions entering reading generation (palm_left, palm_right,
hand_detail) must be displayed and USER-CONFIRMED first", with an S66
Ring 3 pass-1 provenance note citing
`diagnostics/ring3_palm_rubric_S66.md` as the source of this finding.

## Step 4 — Verify

AppTest smoke (Task 3 pattern — fresh run, then inject real
`pdf_context` with `[Varshaphal]`/`[Sade Sati]` sections, rerun):
```
PASS: no exception (hand_detail checkpoint edits, pdf_context path)
```

Full suite:
```
3166 passed, 3 skipped, 1 warning in 87.48s (0:01:27)
```
Matches expected baseline exactly — zero delta.

## Step 5 — Commit

Green -> single commit:
`2d4a42f` — "S66 F1: hand_detail human checkpoint — Ring 3 pass-1 gap
closed"
(RATIFIED: commit authorized)
