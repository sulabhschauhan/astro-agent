# P7.0 Golden Q&A Scorecard -- FROZEN BASELINE (muhurta_window live end-to-end, Session 64)

**This file supersedes `diagnostics/golden_scorecard_20260711_112836.md`
as the comparison baseline going forward.** That file was the frozen
baseline for Session 70's Upapada Lagna live end-to-end landing; this
run is the first baseline with the muhurta_window (Muhurta electional
astrology) domain live end-to-end across the whole pipeline --
chart_profile.py's build_muhurta_profile() (step 1), result_formatter.py's
_format_muhurta_window() (step 2), calc_router.py's Stage 1 keyword list
+ Stage 2 gloss (step 4), orchestrator.py's _VALID_DOMAINS gate (step 5),
tests/infra/test_orchestrator_muhurta.py's 3-layer router-provenance/
oracle/full-chain suite (step 6/6b), and this session's own
golden_harness.py domain-mapping addition + `sulabh_dasha_q15`
KNOWN_GAP deletion (step 7) -- all Session 64. Golden-set row count:
21 -> 23 (two new muhurta rows added).

`sulabh_dasha_q15` ("Which month this year is astrologically best for
me to make a major move?") -- previously KNOWN_GAP under the CLAUDE.md
P2-order lock ("Muhurta engine exists but is not wired to Q&A in V1")
-- now resolves **MATCH_STAGE2 / stage2 / TIER_3_MUHURTA**: that lock's
"not wired" clause is retired for Muhurta specifically as of this
session's wiring; Stage 2 classifies this question muhurta_window at
high confidence (verified in the step 5 run per
`golden_harness.py`'s own deletion-comment citation, reconfirmed in
this run). The `_KNOWN_GAPS["sulabh_dasha_q15"]` entry is deleted
(S50 P7.2f precedent) -- deletion is behavior-neutral, since
`_run_runnable_row` only consults `_KNOWN_GAPS` on a tier mismatch and
this row now matches.

Two new rows: `sulabh_muhurta_q1_stage1` (the S64-ratified Stage 1
phrasing, 2 keyword hits, resolves via stage1, MATCH) and
`sulabh_muhurta_q2_stage2` (a fresh below-floor phrasing -- the task's
own suggested candidate was checked and rejected, since it scores 1
Stage 1 hit against `_DASHA_KEYWORDS` via the bare token "when", not
the required zero; the shipped phrasing scores zero hits across all 7
domain keyword lists, verified programmatically, and was live-probed
4/4 stable at domain=muhurta_window/confidence=high/route=stage2
before shipping -- resolves MATCH_STAGE2).

`sulabh_marriage_q10` -- unaffected by any of the above; remains the
sole `KNOWN_GAP` row, its own independent locked V1-scope Tier 4
interpretive-synthesis exclusion.

**Expected steady state going forward: `match=10/match_stage2=10/
known_gap=1/new_gap=0`** (runnable=21, non_runnable_batch=2,
golden_row_count=23).

- Run evaluated_at_jd: `2461233.327766204`
- Baseline pytest suite count (CLAUDE.md checkpoint): 1769
- Golden-set row count: 23
- deterministic_floor_rows (10, routed via Stage 1 keyword scoring or the sade_sati fastpath -- the regression floor): sulabh_career_q5, sulabh_marriage_q6, sulabh_dasha_q11, sulabh_dasha_q12, sulabh_dasha_q13, sulabh_dasha_q14, sulabh_dasha_r4_exact_date, sulabh_arudha_q1_stage1, sulabh_arudha_q3_refusal_probe, sulabh_muhurta_q1_stage1
- stage2_routed_rows (11, routed via a live GPT-4o-mini Stage 2 call this run -- monitored, not asserted; a category or actual-tier flip on one of these is expected variance, not automatically a regression -- check diagnostics/calc_router_stage2.log before treating as NEW_GAP): sulabh_career_q1, sulabh_career_q2, sulabh_career_q3, sulabh_career_q4, sulabh_marriage_q7, sulabh_marriage_q8, sulabh_marriage_q9, sulabh_marriage_q10, sulabh_dasha_q15, sulabh_arudha_q2_stage2, sulabh_muhurta_q2_stage2

## Per-row results

| id | domain | expected_tier | actual | route | demotion_reason | category |
|---|---|---|---|---|---|---|
| sulabh_career_q1 | career | TIER_2_RANGE | TIER_2_RANGE | stage2 | Career strength held at Tier 2 (range): residual Shadbala uncertainty envelopes (±6 Virupa Ayana Bala general; ±59 Virupa Surbhi Kala Bala chart-specific) can flip close planet rankings; rank within envelope should be treated as approximate | MATCH_STAGE2 |
| sulabh_career_q2 | career | TIER_2_RANGE | TIER_2_RANGE | stage2 | Career strength held at Tier 2 (range): residual Shadbala uncertainty envelopes (±6 Virupa Ayana Bala general; ±59 Virupa Surbhi Kala Bala chart-specific) can flip close planet rankings; rank within envelope should be treated as approximate | MATCH_STAGE2 |
| sulabh_career_q3 | career | TIER_2_RANGE | TIER_2_RANGE | stage2 | Career strength held at Tier 2 (range): residual Shadbala uncertainty envelopes (±6 Virupa Ayana Bala general; ±59 Virupa Surbhi Kala Bala chart-specific) can flip close planet rankings; rank within envelope should be treated as approximate | MATCH_STAGE2 |
| sulabh_career_q4 | career | TIER_2_RANGE | TIER_2_RANGE | stage2 | Career strength held at Tier 2 (range): residual Shadbala uncertainty envelopes (±6 Virupa Ayana Bala general; ±59 Virupa Surbhi Kala Bala chart-specific) can flip close planet rankings; rank within envelope should be treated as approximate | MATCH_STAGE2 |
| sulabh_career_q5 | career | TIER_2_RANGE | TIER_2_RANGE | stage1 | Career strength held at Tier 2 (range): residual Shadbala uncertainty envelopes (±6 Virupa Ayana Bala general; ±59 Virupa Surbhi Kala Bala chart-specific) can flip close planet rankings; rank within envelope should be treated as approximate | MATCH |
| sulabh_marriage_q6 | marriage | TIER_1_EXACT | TIER_1_EXACT | stage1 |  | MATCH |
| sulabh_marriage_q7 | marriage | TIER_1_EXACT | TIER_1_EXACT | stage2 |  | MATCH_STAGE2 |
| sulabh_marriage_q8 | marriage | TIER_1_EXACT | TIER_1_EXACT | stage2 |  | MATCH_STAGE2 |
| sulabh_marriage_q9 | marriage | TIER_1_EXACT | TIER_1_EXACT | stage2 |  | MATCH_STAGE2 |
| sulabh_marriage_q10 | marriage | TIER_4_INTERPRETIVE | TIER_1_EXACT | stage2 |  | KNOWN_GAP |
| sulabh_dasha_q11 | dasha | TIER_2_RANGE | TIER_2_RANGE | stage1 | Antardasha boundaries carry ±37-day drift vs AstroSage; the current lord itself is reliable, but any date given for its start/end should be treated as approximate | MATCH |
| sulabh_dasha_q12 | dasha | TIER_2_RANGE | TIER_2_RANGE | stage1 | Antardasha boundaries carry ±37-day drift vs AstroSage; the current lord itself is reliable, but any date given for its start/end should be treated as approximate | MATCH |
| sulabh_dasha_q13 | dasha | TIER_2_RANGE | TIER_2_RANGE | stage1 | Antardasha boundaries carry ±37-day drift vs AstroSage; the current lord itself is reliable, but any date given for its start/end should be treated as approximate | MATCH |
| sulabh_dasha_q14 | dasha | TIER_1_EXACT | TIER_1_EXACT | fastpath |  | MATCH |
| sulabh_dasha_q15 | dasha | TIER_3_MUHURTA | TIER_3_MUHURTA | stage2 |  | MATCH_STAGE2 |
| sulabh_dasha_r4_exact_date | dasha | TIER_2_RANGE | TIER_2_RANGE | stage1 | Antardasha boundaries carry ±37-day drift vs AstroSage; the current lord itself is reliable, but any date given for its start/end should be treated as approximate | MATCH |
| sulabh_refusal_boundary_probes_r1_r5 | refusal_probe | REFUSAL | N/A (batch, not executed) | n/a |  | NON_RUNNABLE_BATCH |
| sulabh_out_of_domain_probes_quest1_quest2 | refusal_probe | REFUSAL | N/A (batch, not executed) | n/a |  | NON_RUNNABLE_BATCH |
| sulabh_arudha_q1_stage1 | arudha_lagna | TIER_1_EXACT | TIER_1_EXACT | stage1 |  | MATCH |
| sulabh_arudha_q2_stage2 | arudha_lagna | TIER_1_EXACT | TIER_1_EXACT | stage2 |  | MATCH_STAGE2 |
| sulabh_arudha_q3_refusal_probe | upapada_lagna | TIER_1_EXACT | TIER_1_EXACT | stage1 |  | MATCH |
| sulabh_muhurta_q1_stage1 | muhurta_window | TIER_3_MUHURTA | TIER_3_MUHURTA | stage1 |  | MATCH |
| sulabh_muhurta_q2_stage2 | muhurta_window | TIER_3_MUHURTA | TIER_3_MUHURTA | stage2 |  | MATCH_STAGE2 |

## Summary counts

- runnable: 21
- non_runnable_batch: 2
- match: 10
- match_stage2: 10
- design_debt: 0
- known_gap: 1
- new_gap: 0
- error: 0
