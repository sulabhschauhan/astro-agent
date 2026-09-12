# ANSWER PATHS -- which code actually answers a user question

**STATUS: LOCKED S128 (2026-09-12).** Read this before touching anything under
`agent/astro/` or `agent/infra/`, and before calling either one "the pipeline".

There are TWO answer paths in this repo. Only ONE is wired to the product.

## PATH A -- THE PRODUCT (live)

`frontend/app.py:31` -- `from agent.infra.orchestrator import answer_question`
`frontend/app.py:1600` -- calls it with `(prompt, st.session_state.chart)`

```
question
  -> agent/infra/calc_router.route_question        (Stage 1 keywords + Stage 2 LLM)
  -> agent/infra/chart_profile.build_domain_profile
  -> agent/infra/result_formatter.format_answer / format_refusal
  -> agent/interpretive/answer_renderer.render_answer   (frontend/app.py:1601)
```

- Deterministic. No LLM writes answer prose (S23 lock).
- Chart comes from `agent/chart_calculator.calculate_chart` (`frontend/app.py:767`).
- Pratyantar is stripped HERE, at `agent/infra/chart_profile.py:817`.
- Every V1 behaviour, golden row, scorecard and `_KNOWN_GAPS` entry describes
  THIS path.

## PATH B -- THE LAB TRACK (not wired, by design as of S128)

`agent/astro/{planner,payload_builder,interpreter,silence_gate,pipeline}.py`

```
question -> plan -> select -> payload -> Interpreter (gpt-5) -> silence gate -> answer
```

- **NO non-test caller exists anywhere in the repo.** Verified 2026-09-12 on
  `wip/interpretive-pilot @ 2bf850a` by grepping `agent.astro` / `agent/astro`
  across the whole tree. The only importers are `tests/astro/*` and
  `scripts/{run_planner_poc, validate_model, probe_wide_vs_strict,
  spike_option2_timing, build_domain_tags}.py`. `frontend/` and `agent/infra/`
  import it NOWHERE.
- **It cannot be wired as it stands.** Nothing converts `calculate_chart()`'s
  `house_lord_mapping` (list of dicts, `chart_calculator.py:697-707`) into the
  `lord_house_map` that `payload_builder.parse_lord_house_map` demands
  (`payload_builder.py:282-306`). That adapter does not exist. Path B runs today
  only on a hand-built dict (`scripts/run_planner_poc.py:44`) or the frozen
  header of `data/career_payload_bphs.json`.
- **Pratyantar has no suppression hook on this path.** The fact block
  (`pipeline.py:29-34`) carries no dasha data at all, so there is nothing to
  strip. The S125 "pratyantar suppressed downstream" lock is satisfied by
  PATH A only. Any widening of the fact block to include dasha MUST add the
  hook in the same change.

## What "S126: ANSWER PIPELINE COMPLETE END-TO-END" actually means

It means Path B is complete end-to-end **within itself** -- `plan -> answer`,
given a `chart_facts` dict someone hands it. It does NOT mean Path B is
reachable from the app. That single sentence is what misled S127 and S128 into
planning product work against dead code.

## Rules

1. A change to **product behaviour** is a change to **Path A**. A change to
   `agent/astro/` ships nothing to users.
2. Every prompt or design note proposing work on `agent/astro/` must state
   which path it serves, in its first line.
3. Path B does not become the product by being improved. It becomes the product
   only when all three land:
   a. the `calculate_chart() -> chart_facts` adapter is built and tested;
   b. `frontend/app.py:31` is repointed at it;
   c. a pratyantar suppression hook exists on the fact-block path.
   Until all three land, **Path A is the product.**
4. Do not delete Path B. It is the ratified target architecture (S125) and its
   suite is green. It is dormant, not dead.
