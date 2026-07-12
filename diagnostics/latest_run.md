# S66 Task 7 (F2+F3) — voice hardening + query fix: RED, STOPPED (test edits out of scope)

Self-gated. ONE source file touched: `agent/interpretive/palm_reading.py`.
Its test file (`tests/interpretive/test_palm_reading.py`) is Task 8's
scope — this task ran the suite and reports the failure, but does not
touch the test file. **No commit made for the source-file change** —
STEP 5's gate is "green -> commit"; this run is red.

## Step 1 (F3) — Query cap [:500] -> [:2000]

`_QUERY_TRUNCATE_CHARS` raised from 500 to 2000. THRESHOLD DISCIPLINE
comment added citing `diagnostics/ring3_chunks_S66.md` (Ring 3 pass 1
proved the 500-char cap silently truncated the query inside the LEFT
description, dropping the RIGHT hand from retrieval entirely). Scope
guard: this call site only. Revisit trigger: a future F4 describe-prompt
change that materially alters vision-description length.

## Step 2 (F2a) — "## Voice" block added to `_READING_SYSTEM_PROMPT`

Cheiro's declarative register instruction (direct assertions tied to
concrete consequences — health, success won by personal merit, travel,
character, fortune — not therapeutic affirmation) plus an explicit
FORBIDDEN list: stability, fulfillment, fulfilling, favorable, journey,
navigate, navigating, empower, empowerment, and the "this suggests you
are the kind of person who..." self-help framing. Also added to "## How
you read": apply a retrieved passage's specific teaching where it speaks
to a described feature, rather than a generic gloss — cited to Ring 3
pass 1 (`diagnostics/ring3_palm_rubric_S66.md`: every scorable claim
across all 3 runs traced to the confirmed descriptions alone, never
uniquely to a retrieved chunk; readings ignored all 6 retrieved passages
in every run).

## Step 3 (F2b) — Ring 1 validator: `_check_self_help_register()`

New `_SELF_HELP_BLACKLIST` (9 terms: S23 R3 blacklist ["stability",
"fulfillment"] + Ring 3 pass-1 observed offenders ["fulfilling",
"favorable", "journey", "navigate", "navigating", "empower",
"empowerment"] — no speculative additions). New `_SELF_HELP_PATTERN`
(word-boundary, case-insensitive) and `_check_self_help_register()`,
same failure-string format as `_check_jargon`
(`"self_help_blacklist: found {terms}"`). Wired into `generate_palm_reading()`'s
failure-accumulation list alongside `_check_jargon`.

## Step 4 (carry-forward) — lazy OpenAI import

Module-level `from openai import OpenAI` replaced with a
`TYPE_CHECKING`-only import (annotation use only, safe under this
module's existing `from __future__ import annotations`) plus a
function-local `from openai import OpenAI` immediately before
`OpenAI()` construction in the `client is None` branch. Closes the S65-
logged carry-forward (conftest stub-defeat latency fix) on this file's
first touch since it was flagged.

## Step 5 — Full suite: RED (expected outcome per instruction)

```
1 failed, 3165 passed, 3 skipped, 1 warning in 78.67s (0:01:18)
```

**Failing test**: `tests/interpretive/test_palm_reading.py::test_jargon_injection_case_insensitive_and_word_boundary`

**Cause**: its `_JARGON_STUB_TEXT` fixture contains the phrase "a
favorable Antardasha this season" — the word "favorable" is on the new
`_SELF_HELP_BLACKLIST`, so the stubbed reading now trips both
`_check_jargon` (antardasha, lagna, yoga) and the new
`_check_self_help_register` (favorable), producing
`ValidationReport(failures=('jargon_blacklist: found antardasha, lagna, yoga', 'self_help_blacklist: found favorable'))`
— 2 failures where the test asserts exactly 1
(`assert len(result.validation.failures) == 1`).

This is evidence the new validator functions correctly against real
stub content; it is not a defect in `palm_reading.py`. Per instruction,
STOPPED here rather than editing the test — that edit belongs to Task 8.

## Step 6 — no commit for palm_reading.py

`agent/interpretive/palm_reading.py`'s F2+F3+carry-forward changes
remain **uncommitted** in the working tree (`git status`: `M
agent/interpretive/palm_reading.py`). Only this diagnostics file is
committed/pushed for Task 7. Task 8 (test file) must land before
`palm_reading.py`'s changes can be committed under STEP 5's green gate.
