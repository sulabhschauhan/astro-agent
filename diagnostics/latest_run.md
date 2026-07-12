# S66 Task 11 — F5: dogfood capture log

Self-gated. Source file: `frontend/app.py` (+ `.gitignore` one-line
ride-along).

## Step 1 — `.gitignore`

Added:
```
# S66 F5: local dogfood capture — derived text only, never committed
# (no-storage lock ruling 2026-07-12)
diagnostics/dogfood_capture.md
```

## Step 2 — `app.py`: flag + helper

Module-level `_DOGFOOD_CAPTURE = os.environ.get("ASTRO_DOGFOOD_CAPTURE") == "1"`,
read once (re-evaluated every Streamlit script rerun, same as any other
module-level statement — no different from the rest of app.py's session-state
init pattern).

New helper `_capture_dogfood_run(palm_left, palm_right, hand_detail, reading)`
appends one markdown block to `diagnostics/dogfood_capture.md` per successful
`generate_palm_reading()` call:
```
## RUN <ISO timestamp>
### Confirmed descriptions
#### LEFT / RIGHT / HAND_DETAIL   (verbatim; omitted entirely if not confirmed for this run)
### reading_text
verbatim
### sources
- book, p.page (score: score)    (score is already round(...,4) at ingestion/query_engine.py — same value the UI renders, not reformatted)
### ring1_validation
passed: <bool>
failures: <tuple>
```
EXCLUDED by design (per the no-storage lock ruling 2026-07-12, called out
in the helper's docstring): image bytes, image hashes, `pdf_context`, any
AstroSage content.

## Step 3 — Wiring

Wired into the Generate-button success path (`frontend/app.py`, inside the
`try` block right after `generate_palm_reading()` returns), guarded by
`_DOGFOOD_CAPTURE`. Capture fires on ANY successful (non-raising)
`generate_palm_reading()` return, regardless of Ring 1 `validation.passed` —
pass/fail is itself the data the `ring1_validation` section exists to
capture, so a failed-validation run is still worth logging, not just a
displayed one.

Fail-soft: the capture call is wrapped in its own inner `try/except
Exception`, logging a warning (`logger.warning(..., exc_info=True)`) and
continuing on failure — it can never block or alter generation or display,
and sits entirely inside the outer `try` so a capture failure cannot
surface as the outer `except (ValueError, RuntimeError)` error path either.

UI: no change when the flag is off. When on and capture succeeds,
`st.caption("captured to dogfood log")` after success — no caption if
capture is skipped (flag off) or if it fails (fail-soft swallow +
warning only, no user-facing signal on capture failure by design, since
it must never intrude on the reading the user came for).

## Step 4 — AppTest smoke + full suite

New file `tests/test_app_dogfood_capture.py`, two tests via
`streamlit.testing.v1.AppTest`:
- `test_app_loads_with_dogfood_capture_flag_off` — env var unset, `at.run()`,
  assert `not at.exception`.
- `test_app_loads_with_dogfood_capture_flag_on_writes_nothing_without_generation` —
  env var `"1"` (monkeypatched), `at.run()`, assert `not at.exception`, AND
  assert the log file's (mtime, content) snapshot is unchanged from before
  the run (handles both the "file doesn't exist locally" and "a real
  dogfooding session already populated it" cases without depending on
  which is true in a given dev environment).

Neither test simulates a file upload or button click, so no real OpenAI
call is reachable in either run (`describe_palm_image` / `generate_palm_reading`
are only reachable behind file-uploader / button state this harness
doesn't drive) — confirmed by `[_patch_stage2_openai] stub invocation
count: 0` in this file's own isolated run.

```
tests/test_app_dogfood_capture.py::test_app_loads_with_dogfood_capture_flag_off PASSED
tests/test_app_dogfood_capture.py::test_app_loads_with_dogfood_capture_flag_on_writes_nothing_without_generation PASSED
2 passed, 1 warning in 1.54s
```
Confirmed post-run: `diagnostics/dogfood_capture.md` does not exist on
disk (no stray write).

### Full suite

```
3174 passed, 3 skipped, 1 warning in 109.81s (0:01:49)
```
3172 (S66 Task 9 baseline) + 2 new AppTest smoke tests = 3174. Zero
delta beyond the 2 new tests, as expected. Green -> committed.

Commit: `e1ade65` — "S66 F5: opt-in dogfood capture log (derived text
only)"

## Step 5 — This report

Diagnostics overwritten (this file). Pushed to `main`.
