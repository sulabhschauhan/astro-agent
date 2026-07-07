# Session 56 acceptance gate: golden harness re-run vs frozen baseline

**READ-ONLY task — no code, no tests, no fixtures, no baseline edits.**
Only new output: `diagnostics/golden_scorecard_20260707_112916.md` (this
run's scorecard) and this report. The frozen baseline
(`diagnostics/golden_scorecard_20260707_093530.md`) was NOT superseded
-- that remains a closeout decision for design chat, per instructions.

## Verdict: **PASS** against expectations (a)-(c)

All three pre-registered expectations held. No deviation to report; no
tuning performed.

## Step 1-2: harness run + row-for-row diff

Ran `agent.eval.golden_harness.run_golden_eval()` directly. New
scorecard: `diagnostics/golden_scorecard_20260707_112916.md`.

```
runnable=16 non_runnable_batch=2 match=7 match_stage2=5 design_debt=0 known_gap=4 new_gap=0 error=0
```

`diff` against the frozen baseline
(`golden_scorecard_20260707_093530.md`):

```
3c3
< - Run evaluated_at_jd: `2461228.8994444446`
---
> - Run evaluated_at_jd: `2461228.978414352`
```

**Zero row-level differences.** Every `id`/`domain`/`expected_tier`/
`actual`/`route`/`demotion_reason`/`category` cell is byte-identical
across both runs; only the header's `evaluated_at_jd` timestamp differs
(expected -- each run records its own wall-clock moment).

### Per-row diff table

| id | baseline category | this-run category | route | changed? |
|---|---|---|---|---|
| sulabh_career_q1 | MATCH_STAGE2 | MATCH_STAGE2 | stage2 | no |
| sulabh_career_q2 | MATCH_STAGE2 | MATCH_STAGE2 | stage2 | no |
| sulabh_career_q3 | MATCH_STAGE2 | MATCH_STAGE2 | stage2 | no |
| sulabh_career_q4 | KNOWN_GAP | KNOWN_GAP | stage2 | no |
| sulabh_career_q5 | MATCH | MATCH | stage1 | no |
| sulabh_marriage_q6 | MATCH | MATCH | stage1 | no |
| sulabh_marriage_q7 | MATCH_STAGE2 | MATCH_STAGE2 | stage2 | no |
| sulabh_marriage_q8 | MATCH_STAGE2 | MATCH_STAGE2 | stage2 | no |
| sulabh_marriage_q9 | KNOWN_GAP | KNOWN_GAP | stage2 | no |
| sulabh_marriage_q10 | KNOWN_GAP | KNOWN_GAP | stage2 | no |
| sulabh_dasha_q11 | MATCH | MATCH | stage1 | no |
| sulabh_dasha_q12 | MATCH | MATCH | stage1 | no |
| sulabh_dasha_q13 | MATCH | MATCH | stage1 | no |
| sulabh_dasha_q14 | MATCH | MATCH | fastpath | no |
| sulabh_dasha_q15 | KNOWN_GAP | KNOWN_GAP | stage2 | no |
| sulabh_dasha_r4_exact_date | MATCH | MATCH | stage1 | no |
| sulabh_refusal_boundary_probes_r1_r5 | NON_RUNNABLE_BATCH | NON_RUNNABLE_BATCH | n/a | no |
| sulabh_out_of_domain_probes_quest1_quest2 | NON_RUNNABLE_BATCH | NON_RUNNABLE_BATCH | n/a | no |

## Step 3a: deterministic-floor rows -- PASS

All 7 deterministic-floor rows (`sulabh_career_q5`, `sulabh_marriage_q6`,
`sulabh_dasha_q11`, `sulabh_dasha_q12`, `sulabh_dasha_q13`,
`sulabh_dasha_q14`, `sulabh_dasha_r4_exact_date`) show **zero category
changes** -- confirmed above.

## Step 3b: MATCH_STAGE2/known_gap rows -- no variance observed this run

All 9 stage2-routed rows (`sulabh_career_q1-q4`, `sulabh_marriage_q7-q10`,
`sulabh_dasha_q15`) resolved identically to the frozen baseline this
run -- no flip to log or investigate. Per the STAGE2_VARIABLE
convention, this is not a requirement (a flip would have been acceptable
variance, not a gate failure) -- simply reporting that none occurred.
`diagnostics/calc_router_stage2.log` grew by one full run's worth of
entries during this harness invocation (append-only, as always); not
inspected further since there was nothing to explain.

## Step 3c: timing_enrichment presence check (q5, q11-q13)

The scorecard table itself only carries tier/route/demotion_reason/
category -- `timing_enrichment` is payload-level and invisible there, as
expected (design point c). Verified directly by calling
`answer_question()` for each row's exact question text (from
`tests/fixtures/golden_qa_sulabh.py`) against the real Sulabh chart:

| id | domain | tier | timing_enrichment present | sub_windows | resolution_note |
|---|---|---|---|---|---|
| sulabh_career_q5 | career_strength | TIER_2_RANGE | yes | 9 (non-empty) | present, non-empty |
| sulabh_dasha_q11 | current_dasha | TIER_2_RANGE | yes | 9 (non-empty) | present, non-empty |
| sulabh_dasha_q12 | current_dasha | TIER_2_RANGE | yes | 9 (non-empty) | present, non-empty |
| sulabh_dasha_q13 | current_dasha | TIER_2_RANGE | yes | 9 (non-empty) | present, non-empty |

All 4 confirmed: `timing_enrichment` block present, `sub_windows`
non-empty (9 ranked windows each), `resolution_note` present and
non-empty. Scorecard's own tier/category columns for these 4 rows are
unchanged from baseline, confirming enrichment is additive/invisible at
the tier-decision level, as designed.

## Step 3d: wall-clock runtime

**This run: 22.85 seconds** (measured via `time.perf_counter()` around
`run_golden_eval()` directly, excluding Python interpreter startup).

**No prior comparable figure exists to diff against.** Searched
`diagnostics/latest_run.md`'s git history (`git log -p --follow`) for
"elapsed"/"runtime"/"seconds"/"wall-clock" -- no prior golden-harness-
specific timing was ever recorded in this repo (the only wall-clock
figure on file anywhere is an unrelated "93s full-suite pytest wall
clock" note from a different session). Every career/dasha row that
actually routes to its domain now runs a Saturn AV scan over the current
Antardasha (per Session 56's enrichment change) -- this run's 22.85s
covers 16 runnable rows plus 2 real `calculate_chart()` builds (Sulabh +
Surbhi), several of which hit live Stage 2 GPT-4o-mini calls (network-
bound) on top of the new enrichment scans. Flagging this measurement as
the new reference point for future runs to diff against, since none
existed before; not treating its absolute value as a pass/fail signal
per instructions ("a noticeable increase is expected and acceptable,
just quantify it").

## Baseline status

Frozen baseline (`golden_scorecard_20260707_093530.md`) **left
untouched, not superseded** -- per instructions, that decision is
design chat's to make, contingent on this report's PASS verdict.
