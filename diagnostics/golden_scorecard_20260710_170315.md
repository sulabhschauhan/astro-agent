# P7.0 Golden Q&A Scorecard (Session 49)

- Run evaluated_at_jd: `2461232.2104282407`
- Baseline pytest suite count (CLAUDE.md checkpoint): 1769
- Golden-set row count: 18
- deterministic_floor_rows (7, routed via Stage 1 keyword scoring or the sade_sati fastpath -- the regression floor): sulabh_career_q5, sulabh_marriage_q6, sulabh_dasha_q11, sulabh_dasha_q12, sulabh_dasha_q13, sulabh_dasha_q14, sulabh_dasha_r4_exact_date
- stage2_routed_rows (9, routed via a live GPT-4o-mini Stage 2 call this run -- monitored, not asserted; a category or actual-tier flip on one of these is expected variance, not automatically a regression -- check diagnostics/calc_router_stage2.log before treating as NEW_GAP): sulabh_career_q1, sulabh_career_q2, sulabh_career_q3, sulabh_career_q4, sulabh_marriage_q7, sulabh_marriage_q8, sulabh_marriage_q9, sulabh_marriage_q10, sulabh_dasha_q15

## Per-row results

| id | domain | expected_tier | actual | route | demotion_reason | category |
|---|---|---|---|---|---|---|
| sulabh_career_q1 | career | TIER_2_RANGE | TIER_2_RANGE | stage2 | Career strength held at Tier 2 (range): residual Shadbala uncertainty envelopes (±6 Virupa Ayana Bala general; ±59 Virupa Surbhi Kala Bala chart-specific) can flip close planet rankings; rank within envelope should be treated as approximate | MATCH_STAGE2 |
| sulabh_career_q2 | career | TIER_2_RANGE | TIER_2_RANGE | stage2 | Career strength held at Tier 2 (range): residual Shadbala uncertainty envelopes (±6 Virupa Ayana Bala general; ±59 Virupa Surbhi Kala Bala chart-specific) can flip close planet rankings; rank within envelope should be treated as approximate | MATCH_STAGE2 |
| sulabh_career_q3 | career | TIER_2_RANGE | TIER_2_RANGE | stage2 | Career strength held at Tier 2 (range): residual Shadbala uncertainty envelopes (±6 Virupa Ayana Bala general; ±59 Virupa Surbhi Kala Bala chart-specific) can flip close planet rankings; rank within envelope should be treated as approximate | MATCH_STAGE2 |
| sulabh_career_q4 | career | TIER_2_RANGE | REFUSAL | stage2 | question not classifiable with confidence | KNOWN_GAP |
| sulabh_career_q5 | career | TIER_2_RANGE | TIER_2_RANGE | stage1 | Career strength held at Tier 2 (range): residual Shadbala uncertainty envelopes (±6 Virupa Ayana Bala general; ±59 Virupa Surbhi Kala Bala chart-specific) can flip close planet rankings; rank within envelope should be treated as approximate | MATCH |
| sulabh_marriage_q6 | marriage | TIER_1_EXACT | TIER_1_EXACT | stage1 |  | MATCH |
| sulabh_marriage_q7 | marriage | TIER_1_EXACT | TIER_1_EXACT | stage2 |  | MATCH_STAGE2 |
| sulabh_marriage_q8 | marriage | TIER_1_EXACT | TIER_1_EXACT | stage2 |  | MATCH_STAGE2 |
| sulabh_marriage_q9 | marriage | TIER_1_EXACT | REFUSAL | stage2 | question not classifiable with confidence | KNOWN_GAP |
| sulabh_marriage_q10 | marriage | TIER_4_INTERPRETIVE | REFUSAL | stage2 | question not classifiable with confidence | KNOWN_GAP |
| sulabh_dasha_q11 | dasha | TIER_2_RANGE | TIER_2_RANGE | stage1 | Antardasha boundaries carry ±37-day drift vs AstroSage; the current lord itself is reliable, but any date given for its start/end should be treated as approximate | MATCH |
| sulabh_dasha_q12 | dasha | TIER_2_RANGE | TIER_2_RANGE | stage1 | Antardasha boundaries carry ±37-day drift vs AstroSage; the current lord itself is reliable, but any date given for its start/end should be treated as approximate | MATCH |
| sulabh_dasha_q13 | dasha | TIER_2_RANGE | TIER_2_RANGE | stage1 | Antardasha boundaries carry ±37-day drift vs AstroSage; the current lord itself is reliable, but any date given for its start/end should be treated as approximate | MATCH |
| sulabh_dasha_q14 | dasha | TIER_1_EXACT | TIER_1_EXACT | fastpath |  | MATCH |
| sulabh_dasha_q15 | dasha | TIER_3_MUHURTA | REFUSAL | stage2 | question not classifiable with confidence | KNOWN_GAP |
| sulabh_dasha_r4_exact_date | dasha | TIER_2_RANGE | TIER_2_RANGE | stage1 | Antardasha boundaries carry ±37-day drift vs AstroSage; the current lord itself is reliable, but any date given for its start/end should be treated as approximate | MATCH |
| sulabh_refusal_boundary_probes_r1_r5 | refusal_probe | REFUSAL | N/A (batch, not executed) | n/a |  | NON_RUNNABLE_BATCH |
| sulabh_out_of_domain_probes_quest1_quest2 | refusal_probe | REFUSAL | N/A (batch, not executed) | n/a |  | NON_RUNNABLE_BATCH |

## Summary counts

- runnable: 16
- non_runnable_batch: 2
- match: 7
- match_stage2: 5
- design_debt: 0
- known_gap: 4
- new_gap: 0
- error: 0
