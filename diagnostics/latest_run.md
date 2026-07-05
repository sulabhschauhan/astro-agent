# P7.1 — Stage 2 LLM-constrained-classification fallback (calc_router.py)

**Date:** 2026-07-05
**Task source:** `.claude/read_prompt.md`
**File touched:** `agent/infra/calc_router.py` (surgical edit; no other files changed)

## Pre-implementation review (flagged before editing, per Working Style #1)

1. Verified prompt's claims against actual code: `_UNBUILT_MODULE_KEYWORDS`
   short-circuit does run before domain scoring (was true; confirmed by
   reading the file top-to-bottom before editing). `_CONFIDENCE_FLOOR=0.4`
   / `_CONFIDENCE_MARGIN=0.15` confirmed as stated.
2. Flagged a real consequence the prompt didn't address: `tests/infra/
   test_orchestrator_e2e.py` has 5 tests that currently REFUSE via the
   confidence-floor path with zero keyword hits (`test_refusal_health`,
   `test_refusal_travel`, `test_refusal_lottery`, `test_refusal_gemstone`,
   `test_error_empty_question`). Once Stage 2 fires unconditionally on that
   path, every one of these makes a live, billed OpenAI call on every
   `pytest` run — there was no OpenAI-client mock anywhere in
   `tests/conftest.py` (unlike the geocoder, which got one specifically to
   kill live calls in Session 26). Confirmed `.env` has a real
   `OPENAI_API_KEY`, so this was not hypothetical.
3. User decision (Option 2): add an injectable client seam, construct the
   real client lazily INSIDE the Stage 2 branch only (never at module
   import or `route_question()` entry), fail closed on any exception, run
   the suite once accepting the live calls this run, report outcomes, and
   defer the `conftest.py` OpenAI stub to the next prompt.

## What changed (function/line level)

- **Module docstring** (top of file) — rewritten to describe the Stage
  1/Stage 2 split; the old docstring's "No GPT/LLM classification anywhere
  in this file" claim was now false and would have been stale/incorrect
  documentation if left.
- **New imports**: `json`, `pathlib.Path`.
- **New module-level constants** (see "New constants" section below):
  `_STAGE2_MODEL`, `_STAGE2_TIMEOUT_SECONDS`, `_STAGE2_VALID_DOMAINS`,
  `_STAGE2_VALID_CONFIDENCE`, `_STAGE2_CONFIDENCE_MAP`, `_STAGE2_LOG_PATH`,
  `_STAGE2_SYSTEM_PROMPT`, `_STAGE2_TOOL_SCHEMA`.
- **New function `_stage2_classify(question, client=None)`** — the actual
  OpenAI call. Constrained tool-call output only (`tools=[...]`,
  `tool_choice` forced to `classify_domain`), `temperature=0`, receives
  ONLY the raw question text (no Stage 1 scores/keywords passed — no
  anchored judgment, rule #9). Lazily imports+constructs `OpenAI()` only
  when `client is None`, i.e. only when actually invoked. Raises on any
  failure; never itself returns a fallback value.
- **New function `_log_stage2_invocation(...)`** — appends one JSON line
  to `diagnostics/calc_router_stage2.log` per Stage 2 invocation. Logging
  failures are swallowed (`OSError`) so a diagnostics-write problem can
  never affect routing.
- **New function `_route_to_domain(domain, confidence, has_partner_data,
  chart_data)`** — extracted from `route_question()`'s previous inline
  marriage/career/dasha branches (moved verbatim, parametrized) so Stage 1
  and Stage 2 share identical downstream tier/guard logic instead of
  duplicating it. Pure refactor of existing logic; no behavior change for
  the Stage 1 path.
- **New function `_stage2_fallback(question, best_score, margin,
  has_partner_data, chart_data, client)`** — Stage 2 entry point, called
  only from the confidence-floor/margin-tie branch. Wraps
  `_stage2_classify` in `try/except Exception`; routes only if
  `stage2_domain is not None and stage2_confidence == "high"`; logs every
  invocation (fired-and-routed, fired-and-refused, and exception cases)
  before returning.
- **`route_question()`** — added keyword-only `_stage2_client: object |
  None = None` parameter (test-injection seam; not part of the stable
  public contract, `orchestrator.py` never passes it). Tail logic
  (previously ~55 lines of inline branching) replaced with two calls:
  `_stage2_fallback(...)` on the confidence-floor/margin-tie path,
  `_route_to_domain(...)` on the normal Stage-1-cleared path. No change to
  positional signature callers depend on.
- **Post-run fix**: `_stage2_fallback`'s log message for the
  "domain=none, confidence=high" case originally said `"stage2 not
  high-confidence"`, which is factually wrong when confidence *was* high.
  Caught by reading the actual log output after the test run (see below)
  and fixed to distinguish `"stage2 domain=none"` from `"stage2
  confidence=... (not high)"`.

## New constants, tuning-note comments (verbatim from the file)

```
_STAGE2_MODEL = "gpt-4o-mini"
```
> Justification: gpt-4o-mini matches the model already used at this
> codebase's other LLM classification call site (context_classifier.py's
> Layer 1 gate) -- consistent cost/latency profile, cheap enough to run
> per-REFUSAL at V1's expected query volume. Scope guard: governs ONLY this
> file's Stage 2 fallback call -- each LLM call site in this codebase owns
> its own model constant (no shared "the model" constant exists); do not
> import this into other modules. Revisit trigger: if dogfooding shows
> Stage 2 misclassifying at a rate that matters, evaluate gpt-4o (full)
> before touching the confidence thresholds below.

```
_STAGE2_TIMEOUT_SECONDS = 8.0
```
> Justification: keeps Stage 2 well under a synchronous request-response
> UX budget (Session 3's SSE-streaming fix was itself a response to
> 6-11s latency complaints elsewhere in this codebase) while leaving
> several seconds of margin over GPT-4o-mini's typical sub-2s
> single-tool-call latency. Scope guard: a per-call timeout on the OpenAI
> SDK request only -- no retry/backoff/circuit-breaker; a single timeout
> is a hard failure -> REFUSAL (never retried in-request). Revisit
> trigger: if diagnostics/calc_router_stage2.log shows repeated timeout
> outcomes at this value, investigate root cause before raising it
> blindly.

```
_STAGE2_CONFIDENCE_MAP: dict[str, float] = {"high": 1.0, "medium": 0.5, "low": 0.0}
```
> Justification: RouteResult.confidence is a float (Stage 1's continuous
> [0, 1] saturating score); Stage 2 only ever returns a coarse
> high/medium/low enum, and only "high" ever routes (item 3 of the
> Stage 2 spec) -- this map exists purely so a routed RouteResult carries
> a well-defined, documented float instead of a magic literal at the call
> site. Scope guard: 1.0/0.5/0.0 are sentinels, NOT calibrated
> probabilities or measured precision/recall figures. Revisit trigger: if
> a future prompt ever allows medium/low to route, this map must be
> re-justified against real accuracy data per domain, not hand-picked,
> before it's trusted for anything beyond a REFUSAL-vs-ROUTE decision.

## Test suite confirmation

Ran once (per the agreed plan — accept the live Stage 2 calls this single
run):

```
python -m pytest tests -q
...
1770 passed, 3 skipped, 1 warning in 76.24s
```

Identical to the pre-change baseline (1770 passed / 3 skipped / 0 xfailed
/ 0 failed) — **zero regressions, no test outcome changed.**

`diagnostics/calc_router_stage2.log` confirms Stage 2 fired exactly 5
times this run — `test_refusal_health`, `test_refusal_travel`,
`test_refusal_lottery`, `test_refusal_gemstone`, `test_error_empty_question`
— all 5 correctly classified `domain=none, confidence=high` by GPT-4o-mini
and REFUSED, matching what Stage 1 alone already produced for these rows.
No refusal test's outcome flipped to a ROUTE.

## Explicitly not done (per prompt scope + user's follow-up plan)

- No new test file for Stage 2 itself (next prompt, per the task's own
  "no test file" scope line).
- No `conftest.py` OpenAion client stub yet — user's stated next step is a
  dedicated prompt to add an autouse OpenAI stub (mirroring the Session 26
  geocoder fixture) to restore a deterministic/free suite. Until that
  lands, `tests/infra/test_orchestrator_e2e.py`'s 5 refusal tests above
  will keep making live OpenAI calls on every run.
- No changes to `_UNBUILT_MODULE_KEYWORDS`, `_DOMAIN_KEYWORDS`,
  `_STEM_MAP`, the "job" dead-keyword bug, Sade Sati/q14, or
  `golden_harness.py`/`golden_qa_sulabh.py` — all explicitly out of scope,
  untouched.
