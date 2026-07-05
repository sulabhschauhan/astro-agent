# P7.1c — Dedicated Stage 2 unit test file (calc_router.py)

**Date:** 2026-07-05 (Session 50)
**Task source:** pasted prompt, "Session 50 — P7.1c"
**File added:** `tests/infra/test_calc_router_stage2.py` (16 tests). No
source changes, no `conftest.py` changes.

## Design

All tests inject fake clients via `route_question(..., _stage2_client=...)`.
Confirmed by reading `_stage2_classify` first: its `if client is None:`
check short-circuits real-client construction entirely when a client is
passed, so every test here bypasses both the real network AND the
`conftest.py` autouse OpenAI stub (Session 50/P7.1b) — no network, no
`OPENAI_API_KEY`, no `@pytest.mark.integration` needed.

Fakes: `_FakeClient`/`_FakeCompletions`/`_FakeResponse` etc. — minimal
stand-ins for `openai.OpenAI`'s response shape, with `.completions.calls`
tracking every invocation (the actual proof used by the "Stage 2 never
fires" tests, not just exception-raising, since an `AssertionError` raised
inside a fake's `create()` would otherwise be silently swallowed by
`_stage2_fallback`'s own fail-closed `except Exception` — same trap
documented in the P7.1b conftest stub).

File order: Group A (fail-closed battery, item 4) placed first per
"hardest case first" — a fail-closed regression is the highest-severity
failure mode for this fallback.

## Two corrections vs. the task prompt's wording (verified against code, not guessed)

- Items 2 and 3 asked to assert that `demotion_reason` "names the
  not-high confidence" / "the domain=none wording." Reading
  `_stage2_fallback` shows `RouteResult.demotion_reason` is the SAME
  generic `"question not classifiable with confidence"` string for every
  Stage 2 REFUSAL cause (medium, low, domain=none, or any exception) — the
  richer distinction (`"stage2 domain=none"` vs `"stage2 confidence=...
  (not high)"`) exists ONLY in `diagnostics/calc_router_stage2.log`'s
  `outcome` field. Tests assert this accurately: Group C/Group F check
  the generic `RouteResult.demotion_reason`; Group D's two tests
  (`test_domain_none_high_confidence_refuses_and_logs_distinctly`,
  `test_non_high_confidence_logs_distinctly_from_domain_none`)
  monkeypatch `_STAGE2_LOG_PATH` to `tmp_path` and assert the actual log
  distinction there instead.

## Test groups (16 tests)

- **Group A** (6, parametrized) — fail-closed battery: network exception,
  timeout, no tool_calls, malformed JSON arguments, schema-invalid domain,
  schema-invalid confidence. All assert REFUSAL / domain=None /
  confidence=0.0 / generic demotion_reason — mirrors
  `_stage2_fallback`'s `except Exception` contract exactly.
- **Group B** (1) — routes on `confidence="high"`: career_strength ->
  TIER_2_RANGE, confidence == `_STAGE2_CONFIDENCE_MAP["high"]` (1.0),
  `_CAREER_DEMOTION_REASON`.
- **Group C** (2, parametrized medium/low) — REFUSAL, generic
  demotion_reason (see correction above).
- **Group D** (2) — domain=none vs. non-high-confidence: asserts the
  diagnostics log's `outcome` field distinguishes `"stage2 domain=none"`
  from `"stage2 confidence='medium' (not high)"`.
- **Group E** (2) — Stage 2 never fires: keyword-rich marriage question
  (Stage 1 routes directly) and an `"ashtakavarga"` unbuilt-module
  refusal, both asserting `client.completions.calls == []`.
- **Group F** (2) — Stage-2-resolved `marriage_compatibility` respects
  `has_partner_data` identically to Stage 1 (via the shared
  `_route_to_domain` path): REFUSAL without partner data, TIER_1_EXACT
  with it.
- **Group G** (1) — log side-effect: 3 invocations (routed / refused /
  exception) via a `tmp_path`-monkeypatched log path, asserting exactly 3
  JSONL lines with distinguishing `outcome` prefixes
  (`"ROUTED:career_strength"`, `"... not high ..."`, `"...
  ConnectionError..."`).

## Suite runs

1. **New file in isolation:** `16 passed in 0.26s`. Stub invocation count: 0
   (confirms no test in this file touches the autouse patch).
2. **Full suite:** `1786 passed, 3 skipped, 1 warning in 87.17s` (1770
   baseline + 16 new). Stub invocation count: **5**, unchanged from the
   P7.1b baseline — confirms none of the 16 new tests leaked onto the
   autouse OpenAI stub path.

## Explicitly not done (per task scope)

- No changes to `agent/infra/calc_router.py` or `tests/conftest.py`.
- No new integration-marked (real-call) Stage 2 test — all 16 tests are
  pure unit tests against fake clients.
