# P7.0 Golden Q&A Scorecard -- FROZEN BASELINE (post-av_transit router wiring)

**This file supersedes BOTH prior scorecards used as comparison baselines:**
- `diagnostics/golden_scorecard_20260704_185911.md` (Session 49-era; pinned
  in error by a prior task's design chat -- match=6/design_debt=1/
  known_gap=9, a materially staler router/career-scoring state than the
  current codebase; superseded, do not diff against it going forward).
- `diagnostics/golden_scorecard_20260705_090311.md` (the correct,
  most-recent post-Session-50 scorecard prior to this run -- match=12/
  design_debt=0/known_gap=4; used as THIS report's comparison baseline
  below, and now itself superseded by this file for any future diff).

**av_transit domain is live as of this run** (calc_router.py router
wiring + chart_profile.py `_VALID_DOMAINS` gate fix-forward, both shipped
since the `20260705_090311` baseline). No golden_qa_sulabh.py row
currently exercises av_transit (all 18 rows predate that domain), so this
run cannot yet demonstrate an av_transit MATCH/mismatch -- noted for a
future golden-set row addition, not actioned here (fixture changes are
out of scope for this task).

**Categorization scheme, revised from golden_harness.py's own built-in
category machinery:** the harness's `_KNOWN_GAPS`-based classifier
labels a row MATCH whenever `actual_tier == expected_tier`, regardless of
whether Stage 1 (deterministic keyword scoring) or Stage 2 (live
GPT-4o-mini fallback, invoked outside pytest with no conftest stub)
produced that result -- see golden_harness.py's own Session 50/P7.1e
comment: "q1/q2/q3/q7/q8 deleted from `_KNOWN_GAPS` ... Stage 2 now
classifies all 5 at confidence='high' ... Deletion is behavior-neutral:
MATCH is checked before this dict." This report applies a STRICTER split
for baseline-freezing purposes only (no change to golden_harness.py
itself):
- **MATCH** -- actual_tier == expected_tier AND resolved entirely by
  Stage 1 (keyword score or the sade_sati fast-path). Deterministic;
  this is the regression floor asserted going forward.
- **STAGE2_VARIABLE** -- ANY row whose routing invoked a live Stage 2
  GPT-4o-mini call, whether or not the resulting tier happened to match
  expected_tier this run. Monitored, never asserted as a fixed
  regression floor -- a category or actual-tier flip on one of these
  rows across runs is expected variance by construction, not
  automatically a regression.

"Routed via" column determined by cross-referencing each row's exact
question text against `diagnostics/calc_router_stage2.log`'s
per-invocation JSONL records for this run's timestamp window
(2026-07-07T08:38:20 - 08:38:34 UTC) -- not inferred from the scorecard's
actual/category columns alone, since Stage 1 and Stage 2 can independently
produce the identical final RouteResult for a given domain (both funnel
through `_route_to_domain()`).

- Run evaluated_at_jd: `2461228.8599074073`
- Baseline pytest suite count (CLAUDE.md checkpoint): 1769 (full-suite
  re-run optional for this read-only task; not re-run here -- last known
  count 2943 passed / 3 skipped / 0 failed)
- Golden-set row count: 18

## Per-row results

| id | domain | expected_tier | actual | routed via | demotion_reason | category |
|---|---|---|---|---|---|---|
| sulabh_career_q1 | career | TIER_2_RANGE | TIER_2_RANGE | Stage 2 (career_strength, high) | Career strength held at Tier 2 (range): residual Shadbala uncertainty envelopes (±6 Virupa Ayana Bala general; ±59 Virupa Surbhi Kala Bala chart-specific) can flip close planet rankings; rank within envelope should be treated as approximate | STAGE2_VARIABLE |
| sulabh_career_q2 | career | TIER_2_RANGE | TIER_2_RANGE | Stage 2 (career_strength, high) | Career strength held at Tier 2 (range): residual Shadbala uncertainty envelopes (±6 Virupa Ayana Bala general; ±59 Virupa Surbhi Kala Bala chart-specific) can flip close planet rankings; rank within envelope should be treated as approximate | STAGE2_VARIABLE |
| sulabh_career_q3 | career | TIER_2_RANGE | TIER_2_RANGE | Stage 2 (career_strength, high) | Career strength held at Tier 2 (range): residual Shadbala uncertainty envelopes (±6 Virupa Ayana Bala general; ±59 Virupa Surbhi Kala Bala chart-specific) can flip close planet rankings; rank within envelope should be treated as approximate | STAGE2_VARIABLE |
| sulabh_career_q4 | career | TIER_2_RANGE | REFUSAL | Stage 2 (domain=none, high) | question not classifiable with confidence | STAGE2_VARIABLE |
| sulabh_career_q5 | career | TIER_2_RANGE | TIER_2_RANGE | Stage 1 (keyword score) | Career strength held at Tier 2 (range): residual Shadbala uncertainty envelopes (±6 Virupa Ayana Bala general; ±59 Virupa Surbhi Kala Bala chart-specific) can flip close planet rankings; rank within envelope should be treated as approximate | **MATCH** |
| sulabh_marriage_q6 | marriage | TIER_1_EXACT | TIER_1_EXACT | Stage 1 (keyword score) |  | **MATCH** |
| sulabh_marriage_q7 | marriage | TIER_1_EXACT | TIER_1_EXACT | Stage 2 (marriage_compatibility, high) |  | STAGE2_VARIABLE |
| sulabh_marriage_q8 | marriage | TIER_1_EXACT | TIER_1_EXACT | Stage 2 (marriage_compatibility, high) |  | STAGE2_VARIABLE |
| sulabh_marriage_q9 | marriage | TIER_1_EXACT | REFUSAL | Stage 2 (marriage_compatibility, medium -- not high) | question not classifiable with confidence | STAGE2_VARIABLE |
| sulabh_marriage_q10 | marriage | TIER_4_INTERPRETIVE | REFUSAL | Stage 2 (marriage_compatibility, medium -- not high) | question not classifiable with confidence | STAGE2_VARIABLE |
| sulabh_dasha_q11 | dasha | TIER_2_RANGE | TIER_2_RANGE | Stage 1 (keyword score) | Antardasha boundaries carry ±37-day drift vs AstroSage; the current lord itself is reliable, but any date given for its start/end should be treated as approximate | **MATCH** |
| sulabh_dasha_q12 | dasha | TIER_2_RANGE | TIER_2_RANGE | Stage 1 (keyword score) | Antardasha boundaries carry ±37-day drift vs AstroSage; the current lord itself is reliable, but any date given for its start/end should be treated as approximate | **MATCH** |
| sulabh_dasha_q13 | dasha | TIER_2_RANGE | TIER_2_RANGE | Stage 1 (keyword score) | Antardasha boundaries carry ±37-day drift vs AstroSage; the current lord itself is reliable, but any date given for its start/end should be treated as approximate | **MATCH** |
| sulabh_dasha_q14 | dasha | TIER_1_EXACT | TIER_1_EXACT | Stage 1 (sade_sati fast-path, `_BUILT_MODULE_FASTPATH`) |  | **MATCH** |
| sulabh_dasha_q15 | dasha | TIER_3_MUHURTA | REFUSAL | Stage 2 (domain=none, high) | question not classifiable with confidence | STAGE2_VARIABLE |
| sulabh_dasha_r4_exact_date | dasha | TIER_2_RANGE | TIER_2_RANGE | Stage 1 (keyword score) | Antardasha boundaries carry ±37-day drift vs AstroSage; the current lord itself is reliable, but any date given for its start/end should be treated as approximate | **MATCH** |
| sulabh_refusal_boundary_probes_r1_r5 | refusal_probe | REFUSAL | N/A (batch, not executed) | N/A |  | NON_RUNNABLE_BATCH |
| sulabh_out_of_domain_probes_quest1_quest2 | refusal_probe | REFUSAL | N/A (batch, not executed) | N/A |  | NON_RUNNABLE_BATCH |

## Summary counts

- runnable: 16
- non_runnable_batch: 2
- **match (Stage-1-deterministic, regression floor): 7**
  (sulabh_career_q5, sulabh_marriage_q6, sulabh_dasha_q11,
  sulabh_dasha_q12, sulabh_dasha_q13, sulabh_dasha_q14,
  sulabh_dasha_r4_exact_date)
- **stage2_variable (monitored, not asserted): 9**
  (sulabh_career_q1, sulabh_career_q2, sulabh_career_q3,
  sulabh_career_q4, sulabh_marriage_q7, sulabh_marriage_q8,
  sulabh_marriage_q9, sulabh_marriage_q10, sulabh_dasha_q15)
- design_debt: 0
- new_gap: 0
- error: 0

(golden_harness.py's own native summary line for this same run, for
cross-reference: match=12, design_debt=0, known_gap=4, new_gap=0,
error=0 -- the 12 = this file's 7 true-MATCH + 5 of the 9
STAGE2_VARIABLE rows that happened to resolve correctly this run
[q1, q2, q3, q7, q8]; the 4 = the remaining STAGE2_VARIABLE rows that
mismatched this run [q4, q9, q10, q15].)
