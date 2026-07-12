# S66 Task 9 — F4: describe_palm_image hardening

Self-gated. One source file: `agent/palm_processor.py`. `palm_reading.py`
untouched (its query-cap re-derivation is a separate, measure-gated
follow-up).

## Step 1 — New system prompt

Replaced `describe_palm_image`'s system prompt (the free-text "3-5
sentences" expert-palm-reader framing) with a structured, observational
prompt: "trained observer preparing hand notes for a Cheiro-tradition
palmist... You are NOT the palmist... never write 'indicating',
'suggesting', or any interpretation." Ten labeled output fields in fixed
order: HAND SHAPE, FINGERS, THUMB, LIFE LINE, HEAD LINE, HEART LINE,
FATE LINE, OTHER LINES, MOUNTS, MARKS. Explicit instruction: "For any
attribute not clearly visible, write 'not clearly visible' — never guess
or fill in what a typical hand would show."

Root cause this closes (Ring 3 pass-1, `diagnostics/ring3_palm_rubric_S66.md`):
the old prompt's "expert palm reader... describe in detail" framing
invited interpretive language at the source, upstream of any downstream
voice/jargon filtering.

## Step 2 — Call parameters

- `temperature`: 0.3 -> 0. Comment: checkpoint reproducibility — the
  description a user confirms must be the description the run would
  regenerate.
- `max_tokens`: 400 -> 600. THRESHOLD DISCIPLINE (CLAUDE.md Working
  Style #4): derived from ~10 labeled fields x ~1-2 lines. Scope guard:
  this call site only. Revisit trigger: step-3 probe shows truncation.

## Step 3 — Measure-first probe (live vision, both repo fixtures)

Ran the new prompt once per fixture via `describe_palm_image`, using the
`test_palm_endtoend.py` integration-test precedent (real GPT-4o calls,
no asserts on content).

### LEFT (`data/test_images/palm_left_test.jpg`) — verbatim

```
HAND SHAPE: Square palm, overall build is medium.

FINGERS: Fingers are long relative to the palm, appear straight, fingertips are rounded, spacing is moderate.

THUMB: Medium relative size, set moderately low, wide angle from the palm.

LIFE LINE: Present, deep, long, curves around the base of the thumb, no breaks, chains, forks, or islands visible.

HEAD LINE: Present, deep, long, slightly curved, starts joined with the life line, no breaks, chains, forks, or islands visible.

HEART LINE: Present, deep, long, curves slightly upwards, no breaks, chains, forks, or islands visible.

FATE LINE: Barely visible.

OTHER LINES: No other lines clearly visible.

MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.

MARKS: No marks clearly visible.
```

### RIGHT (`data/test_images/palm_right_test.jpg`) — verbatim

```
HAND SHAPE: Square palm, medium build

FINGERS: Medium length relative to palm, straight, rounded fingertips, moderate spacing

THUMB: Medium size, set moderately low, wide angle from the palm

LIFE LINE: Present, deep, long, curves around the base of the thumb, no clear breaks or forks

HEAD LINE: Present, deep, long, slightly curved, starts joined with the life line

HEART LINE: Present, deep, slightly curved, ends below the middle finger

FATE LINE: Barely visible

OTHER LINES: Not clearly visible

MOUNTS: Mount of Venus appears developed, other mounts unremarkable

MARKS: Not clearly visible
```

### Length arithmetic

| | chars |
|---|---|
| LEFT description | 769 |
| RIGHT description | 602 |
| Combined | 1371 |
| `_QUERY_TRUNCATE_CHARS` (`agent/interpretive/palm_reading.py`, read not hardcoded) | 2000 |
| Margin | 629 (combined fits, no truncation) |

### Observed deviations (no asserts — observed values only, design chat ratifies)

- **Interpretation leakage**: none observed in either output. No
  "indicating"/"suggesting" or trait/prediction language in either
  transcript — all 20 field-lines (10 per hand) stay in physical-
  observation register.
- **"not clearly visible" phrasing fidelity**: RIGHT hand used the
  instructed literal phrase twice (OTHER LINES, MARKS: "Not clearly
  visible"). LEFT hand used semantically-equivalent but non-literal
  phrasing instead ("No other lines clearly visible", "No marks clearly
  visible") — the model paraphrased the required token rather than
  emitting it verbatim. Not a content problem (both correctly signal
  absence, no guessing), but the exact-string instruction was not
  followed exactly in 2/20 fields. Flagging for design-chat ratification
  per Step 3's charter, not treating as a defect requiring a code fix.
- **Fields all present, all ten labels emitted in order, both hands.**
  No truncation (both well under the 600-token budget headroom implied
  by the 769/602-char outputs).

## Step 4 — Grep for stale test coupling

Grepped `tests/` for the old prompt text and `"3-5 sentences"`: zero
matches. No atomic-landing test-update step required (unlike the S66
Task 8 precedent, where `_check_self_help_register` additions tripped an
existing stub).

## Step 5 — Full suite

```
3172 passed, 3 skipped, 1 warning in 80.34s
```
Zero delta from the expected baseline (integration-marked tests excluded
by default run). Green -> committed.

Commit: `f81809d` — "S66 F4: observational structured describe prompt,
temp 0 (Ring 3 pass-1 root-cause fix)"

## Step 6 — This report

Diagnostics overwritten (this file). Pushed to `main`.
