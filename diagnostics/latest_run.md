# P7.1b — Autouse OpenAI stub for calc_router Stage 2 (deterministic suite)

**Date:** 2026-07-05 (Session 50)
**Task source:** pasted prompt, "Session 50 — P7.1b"
**File touched:** `tests/conftest.py` only (no source changes)

## Patch-seam verification (done before writing any code, per the task's own instruction)

Read `agent/infra/calc_router.py::_stage2_classify` first. Confirmed: the
`from openai import OpenAI` import is INSIDE the function body (only
reached when `client is None`), not at `calc_router` module level — there
is no `calc_router.OpenAI` attribute to patch. Because that import
statement re-executes on every call, it always re-reads the *current*
`OpenAI` attribute off the real `openai` module at call time. So the
correct patch seam is `openai.OpenAI` itself (the class on the `openai`
package), not anything inside `calc_router`'s own namespace — confirmed
against the actual code, not assumed.

Also confirmed (by reading the same function): `if client is None:` means
an explicit `_stage2_client=<fake>` argument to `route_question()` always
short-circuits construction entirely — the patched `openai.OpenAI` is
never even reached in that case. So the seam parameter already takes
precedence over the autouse patch by construction; no extra plumbing was
needed to guarantee that for the next prompt's dedicated Stage 2 test file.

## What was added to `tests/conftest.py`

- `_FakeStage2OpenAI` / `_FakeStage2Chat` / `_FakeStage2Completions` /
  `_FakeStage2Response` (+ small tool-call/message/choice shims) — a
  minimal drop-in for `openai.OpenAI` whose `chat.completions.create(...)`
  returns a well-formed constrained tool-call response with
  `domain="none", confidence="high"` — reproducing today's real
  GPT-4o-mini outcome for the 5 existing zero-keyword-hit e2e refusal
  tests (`test_refusal_health/travel/lottery/gemstone`,
  `test_error_empty_question`).
- `_stage2_check(condition, message)` — asserts call shape (`model ==
  calc_router._STAGE2_MODEL`, `tool_choice` forces `classify_domain`,
  `tools[0]` names `classify_domain`, `temperature == 0`) and records any
  violation into a module-level list, in addition to raising immediately.
  The immediate raise alone would NOT surface as a pytest failure (it's
  caught by `_stage2_fallback`'s own fail-closed `except Exception` in
  production code, by design) — the recorded list is what actually makes
  a contract drift loud: `_patch_stage2_openai`'s teardown asserts the
  list stayed empty after every test, attributing any failure to the
  specific test that triggered it.
- `_patch_stage2_openai` — **function-scoped** autouse fixture (unlike the
  existing session-scoped `_patch_geocoder`, because per-test marker
  inspection for the opt-out below needs function scope). Patches
  `openai.OpenAI` via `monkeypatch.setattr` for the duration of each test,
  then asserts no new contract violations were recorded.
- **Opt-out**: tests marked `@pytest.mark.integration` (the marker already
  declared in `pytest.ini` and already used by
  `test_palm_quality.py`/`test_palm_endtoend.py` for real-GPT-call tests —
  no new marker invented) skip the patch entirely and get the real
  `openai.OpenAI`, for any future genuine live-integration test of Stage 2
  itself.
- `pytest_terminal_summary` hook — prints the stub's invocation count at
  the end of every run, for visibility without grepping
  `diagnostics/calc_router_stage2.log`.

## Suite runs

1. **Normal (real `OPENAI_API_KEY` present):**
   `1770 passed, 3 skipped, 1 warning in 79.68s` — stub invocation count: 5.
2. **`env -u OPENAI_API_KEY` (requested "keyless" run):**
   `1770 passed, 3 skipped, 1 warning in 72.32s` — identical to run 1,
   stub invocation count: 5.

Both green, identical counts, as required.

**Honesty caveat found during verification** (not asked for, but worth
flagging): `env -u OPENAI_API_KEY` does not actually keep the process
keyless. `agent/context_classifier.py` calls `load_dotenv(...)` at import
time, and `python-dotenv`'s default `override=False` only refuses to
overwrite a variable that's *already set* — it still populates a
*currently-absent* one from `.env`. Confirmed directly:
```
env -u OPENAI_API_KEY python -c "
    import os; print(before=..., 'OPENAI_API_KEY' in os.environ)  # False
    import agent.context_classifier
    print(after=..., 'OPENAI_API_KEY' in os.environ)              # True
"
```
So run 2 above did have a real key available by the time tests executed —
it did not, by itself, prove calc_router's Stage 2 is key-independent.

To get an honest proof, ran a third check (not requested, added for
rigor): **`OPENAI_API_KEY=sk-deliberately-invalid-test-key`** (a value
that would fail any real API call with an auth error):
```
6 failed, 1764 passed, 3 skipped, 1 warning in 34.10s
```
The 6 failures were exactly the pre-existing `@pytest.mark.integration`
tests (`test_palm_quality.py` x4, `test_nudge_endtoend.py` x2) that call
`OpenAI()` directly through `palm_processor.py`/`context_classifier.py` —
modules untouched by this task, already dependent on a real key before
this session, and out of scope here. **Every calc_router-Stage-2-touching
test still passed, and the stub still fired exactly 5 times** — proving
Stage 2 itself never reaches a real `OpenAI()` instance regardless of key
validity, which is the actual property this task needed to establish.
`tests/conftest.py`'s module docstring was updated to state this scoped
claim accurately rather than the broader ("keyless for the whole suite")
claim that isn't true and isn't this task's job to fix.

## Explicitly not done (per task scope)

- No changes to `agent/infra/calc_router.py` or any other source file.
- No new Stage 2 test file yet (next prompt, per the task's own framing —
  will inject fake clients via `route_question(..., _stage2_client=...)`,
  confirmed above to bypass this fixture's patch cleanly).
- Did not attempt to make the pre-existing palm/context-classifier
  integration tests key-independent — out of scope, unrelated to
  calc_router's Stage 2.
