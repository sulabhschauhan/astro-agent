# ANSWER PATHS -- which code actually answers a user question

**STATUS: PATH B IS THE ANSWER PATH (S129, 2026-09-12).** Supersedes the S128
version of this file, which recorded Path A as the product and Path B as
unwired. Read this before touching anything under `agent/astro/` or
`agent/infra/`, and before calling either one "the pipeline".

## PATH B -- THE PRODUCT (live as of S129)

`frontend/app.py` -- `from agent.astro.pipeline import answer_question`
and `from agent.astro.chart_facts import build_chart_facts, ChartFactsError`

```
question
  -> planner.plan_question                     Stage 1  (gpt-4o, JSON plan)
  -> capability_gate.assess                    Stage 1.5 (deterministic)
  -> planner.build_from_plan                   Stage 2+3 (chapters, verses)
       chart_facts.build_chart_facts(chart)    Stage 3.5 (the fact block)
  -> interpreter.interpret                     Stage 4  (gpt-5, cited claims)
  -> silence_gate.apply_silence_gate           Stage 5a
  -> pipeline._render                          answer + decline notes
```

This is the objective: question -> plan -> chapters -> verses -> grounded,
cited, chart-specific answer.

### What the fact block carries TODAY

**Updated S129b -- supersedes this section's ascendant+lords-only text.**
Three things, and nothing else:

  - `ascendant_sign`
  - `lord_house_map`      -- the 12 house-lord placements
  - `planet_positions`    -- per-graha {house, sign}, classical `_GRAHA_ORDER`

It is built by `chart_facts.build_chart_facts()`, which RESTATES
`calculate_chart()`'s `house_lord_mapping`, `lagna_chart.ascendant` and the
per-planet house/sign -- it computes nothing.

Planet positions are **house + sign ONLY**. NO dignity (no oracle table exists
to validate it), NO longitude (the corpus has no verse keys on a degree), NO
retrograde (retrograde-keyed verses = 10/20,426 = 0.05%). Do not "complete"
this set without a new ground.

Independently validated against the JHora oracle (S129): Sulabh's 12 lord
placements derived from `reference/oracle_fixtures/sulabh.md`'s planet signs
match the adapter's output 12/12.

NOTE ON SHAPE: `pipeline._fact_block` renders planet lines only when
`chart_facts` carries them, while `FACT_BLOCK_PROVIDES` declares them
unconditionally. That is deliberate (`tests/astro/test_capability_gate.py`
pins it) and safe ONLY because the product path always builds facts through
`build_chart_facts` (`frontend/app.py:1617`). A legacy `fact_block_text`-shaped
dict gets the declaration without the facts -- which is why a replayed zero on
a pre-S129b capture is an ABSENCE OF EVIDENCE, not evidence of safety
(`tests/astro/test_replay_capture.py`).

### The capability gate is what makes this honest

`agent/astro/capability_gate.py` runs BEFORE retrieval and before the
Interpreter. It holds one declaration -- `FACT_BLOCK_PROVIDES` -- of what the
fact block carries, and a register of requirements saying which planner
domains and time_scopes need facts beyond it.

Today exactly one requirement fires: anything planning `timing_dasha`, or
carrying `time_scope` of `future` / `specific_period`, needs dasha periods the
block does not have. That domain is dropped from the plan and the user is told
plainly. If nothing answerable remains, the question is refused outright and no
model is called at all.

This exists because the silence gate CANNOT protect a dated claim: it judges
only claims shaped "the Nth lord is in the Mth", and it fails open on
everything else. Without this gate, a timing question would reach gpt-5 with
timing doctrine and no timing facts, and anything it produced would ship
unverified -- Working Style #5.

**Growing it:** when `pipeline._fact_block` widens, add the new capability key
to `FACT_BLOCK_PROVIDES` IN THE SAME CHANGE. Widening means RESTATING more of
`calculate_chart()` (aspects and conjunctions are already returned by it, so
they are a restate task in `chart_facts.py`, not a calculation task). It does
NOT mean implementing `agent/calculations/core/chart_d1.py`, which is a
PERMANENT deliberate stub -- see KNOWN_PATTERNS P-022; two sessions have now
planned to build it.
The matching requirement goes inert automatically; nothing else is edited.
`tests/astro/test_capability_gate.py` pins the declaration against what
`_fact_block` actually renders, so the two cannot drift silently.

### Pratyantar

`calculate_chart` still returns `current_pratyantar` / `next_5_pratyantars`
(`chart_calculator.py:609-610`). The adapter never reads them, and the fact
block carries no dasha at all, so nothing pratyantar-shaped can reach the
Interpreter. THE SUPPRESSION HOOK IS STILL OWED: whoever widens the fact block
to carry dasha MUST strip pratyantar in that same change (+/-37d drift, wrong
lord). There is no hook to inherit -- the safety today is absence, not a guard.

## PATH A -- THE DETERMINISTIC ROUTER (retained, no longer wired)

`agent/infra/{orchestrator,calc_router,chart_profile,result_formatter}.py`
plus `agent/interpretive/answer_renderer.py`.

Nine routed domains, fully deterministic, answers assembled from fixed
templates. It opens no book and produces no citation, which is why it cannot
serve the objective and why S129 cut over away from it.

**It is retained, tested and intact -- do not delete it.** It is the revert
target if the cutover is reversed, and its calculation layer
(`chart_profile.build_domain_profile`) is the natural source for future fact
block widening.

Known defects found in the S129 audit, unfixed because it is no longer wired:
`answer_renderer` has no branch for `yogini_dasha` or `av_transit` (both route
and format, then raise); the career timing block renders Antardasha dates
without its own `resolution_note`; and `calc_router`'s out-of-scope guard is a
plain substring match, so a question naming the sign Cancer is refused as
medical (`calc_router.py:1077`). That last one is the S124 "live bug" CLAUDE.md
records as closed -- it was closed in the PLANNER, i.e. on Path B, never on
Path A. Path B's planner judges intent and handles it correctly.

## Rules

1. A change to product behaviour is a change to **Path B**.
2. Before proposing work on `agent/infra/`, state why it is not Path B work.
3. Do not re-wire `frontend/app.py` to `agent.infra.orchestrator` without
   re-reading this file and recording the reason.
4. The capability gate is the ONLY place that decides "we cannot answer this
   for lack of facts". Do not add a second such judgement in the interpreter
   prompt, the renderer, or the app.
