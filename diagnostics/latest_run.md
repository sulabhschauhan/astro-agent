# P7.2e — e2e + router tests for sade_sati path

**Date:** 2026-07-05 (Session 50)
**Task source:** pasted prompt, "Session 50 — P7.2e"
**File touched:** `tests/infra/test_orchestrator_e2e.py` only (4 new
tests). No source changes.

## Item 1: conventions respected

Read the file's docstring/conventions first: import restriction (only
`answer_question`/`AnswerTier`, no `calc_router`/`chart_profile
.DomainAnswer`/`result_formatter`), the dotted-string `monkeypatch`
pattern already established by `test_dasha_boundary_reason_selection`,
and the "one test per chart, no parametrize" reference-chart template.
All 4 new tests follow these exactly — no new imports added.

## Item 2: hardest case first — `test_sade_sati_sulabh` (not-active)

Placed first in the new group, per Working Style #3. Asserts `tier ==
TIER_1_EXACT` exactly, `demotion_reason is None`,
`payload["next_cycle_start"] == "27 Jan 2041"`,
`payload["previous_cycle_end"] == "24 Jan 2020"`, `active is False`, and
**structurally** asserts `"mahadasha" not in payload` and `"antardasha"
not in payload` (plus `"current_cycle_start"/"current_cycle_end" not in
payload`, since those are active-only fields) — locks the
payload-property tier principle in code, not just prose.

## Item 3: active-case chart — verified, not guessed

Before writing the test, ran a direct check of all 4 reference charts'
current Sade Sati status:
```
Sulabh   moon_sign=Scorpio   active=False phase=NONE
Surbhi   moon_sign=Aquarius  active=True  phase=SETTING
David    moon_sign=Leo       active=False phase=NONE
Sheridan moon_sign=Aries     active=True  phase=RISING
```
**Surbhi (and Sheridan) are currently active** — the task's
historical-`evaluated_at_jd`/direct-`build_domain_profile()` fallback
(for when none of the 4 is active) was **not needed**. Used Surbhi via
the real, no-mocks `answer_question()` path instead, consistent with this
file's own convention. Verified exact values via a direct call before
writing assertions: `current_cycle_start="24 Jan 2020"`,
`current_cycle_end="23 Feb 2028"`, `next_cycle_start="20 Oct 2027"`,
`phase="SETTING"`. Also asserts `"previous_cycle_end" not in payload`
(active-case must omit it) and the same `mahadasha`/`antardasha`
structural exclusions as the not-active test.

## Item 4: determinism guard

`test_sade_sati_never_reaches_stage2` patches
`agent.infra.calc_router._stage2_fallback` (NOT `_stage2_classify`) to
raise `AssertionError` if called. Documented why in the test's own
docstring: `_stage2_classify`'s exceptions are caught by
`_stage2_fallback`'s own fail-closed `except Exception`, so patching that
function instead would be silently swallowed into an ordinary `REFUSAL`
and never surface as a visible test failure (the same trap already
documented in `tests/conftest.py`'s Stage 2 stub). `_stage2_fallback`
itself has no enclosing `try/except` in `route_question()`, so an
exception there propagates all the way up through `answer_question()`
uncaught — that's what actually proves non-invocation.

## Item 5: unbuilt-refusal regression

`test_refusal_ashtakavarga_still_unbuilt` — "What is my Ashtakavarga
strength?" still refuses via the unbuilt-module path (asserts
`"Ashtakavarga" in result.demotion_reason`), confirming
`_BUILT_MODULE_FASTPATH`'s insertion (checked AFTER
`_UNBUILT_MODULE_KEYWORDS`, per P7.2c) didn't reorder or short-circuit
the pre-existing unbuilt-refusal path.

## Item 6: wall-clock coupling notes (comments only, no machinery)

- `test_sade_sati_sulabh`: exact dates hold until Sulabh's next cycle
  begins, **27 Jan 2041**.
- `test_sade_sati_surbhi_active`: exact dates hold only until Surbhi's
  current cycle ends, **23 Feb 2028** — a materially shorter runway than
  Sulabh's, flagged explicitly in its own docstring (not asked for by
  name in item 6, but the same category of concern, so added for the
  active-case test too).

## Suite runs

1. **New file in isolation**: `21 passed in 8.06s` (17 existing + 4 new).
   Stub invocation count: 5 (unchanged — none of the new tests touch the
   autouse Stage 2 stub, matching expectation since sade_sati never
   reaches Stage 2).
2. **Full suite**: `1790 passed, 3 skipped, 1 warning in 79.08s` (1786 +
   4 new). Stub invocation count: 5, unchanged.

## Explicitly not done (per task scope)

- No source changes (calc_router.py/chart_profile.py/result_formatter.py/
  orchestrator.py untouched).
- Did not need the historical-JD `build_domain_profile()` fallback for
  the active-case test — a real reference chart was available.
