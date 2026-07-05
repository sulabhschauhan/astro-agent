# P7.0 Golden Q&A Scorecard (Session 49)

- Run evaluated_at_jd: `2461226.1340393517`
- Baseline pytest suite count (CLAUDE.md checkpoint): 1769
- Golden-set row count: 18

## Per-row results

| id | domain | expected_tier | actual | demotion_reason | category |
|---|---|---|---|---|---|
| sulabh_career_q1 | career | TIER_2_RANGE | REFUSAL | question not classifiable with confidence | KNOWN_GAP |
| sulabh_career_q2 | career | TIER_2_RANGE | REFUSAL | question not classifiable with confidence | KNOWN_GAP |
| sulabh_career_q3 | career | TIER_2_RANGE | REFUSAL | question not classifiable with confidence | KNOWN_GAP |
| sulabh_career_q4 | career | TIER_2_RANGE | REFUSAL | question not classifiable with confidence | KNOWN_GAP |
| sulabh_career_q5 | career | TIER_2_RANGE | TIER_2_RANGE | Career strength held at Tier 2 (range): residual Shadbala uncertainty envelopes (±6 Virupa Ayana Bala general; ±59 Virupa Surbhi Kala Bala chart-specific) can flip close planet rankings; rank within envelope should be treated as approximate | MATCH |
| sulabh_marriage_q6 | marriage | TIER_1_EXACT | TIER_1_EXACT |  | MATCH |
| sulabh_marriage_q7 | marriage | TIER_1_EXACT | REFUSAL | question not classifiable with confidence | KNOWN_GAP |
| sulabh_marriage_q8 | marriage | TIER_1_EXACT | REFUSAL | question not classifiable with confidence | KNOWN_GAP |
| sulabh_marriage_q9 | marriage | TIER_1_EXACT | REFUSAL | question not classifiable with confidence | KNOWN_GAP |
| sulabh_marriage_q10 | marriage | TIER_4_INTERPRETIVE | REFUSAL | question not classifiable with confidence | KNOWN_GAP |
| sulabh_dasha_q11 | dasha | TIER_2_RANGE | TIER_1_EXACT |  | KNOWN_GAP |
| sulabh_dasha_q12 | dasha | TIER_2_RANGE | TIER_1_EXACT |  | KNOWN_GAP |
| sulabh_dasha_q13 | dasha | TIER_2_RANGE | TIER_1_EXACT |  | KNOWN_GAP |
| sulabh_dasha_q14 | dasha | TIER_1_EXACT | REFUSAL | question references Sade Sati transit engine, which is not in the 3-domain whitelist (marriage_compatibility, career_strength, current_dasha) | KNOWN_GAP |
| sulabh_dasha_q15 | dasha | TIER_3_MUHURTA | REFUSAL | question not classifiable with confidence | KNOWN_GAP |
| sulabh_dasha_r4_exact_date | dasha | TIER_2_RANGE | REFUSAL | question references transit engine (gochara/sade sati), which is not in the 3-domain whitelist (marriage_compatibility, career_strength, current_dasha) | NEW_GAP |
| sulabh_refusal_boundary_probes_r1_r5 | refusal_probe | REFUSAL | N/A (batch, not executed) |  | NON_RUNNABLE_BATCH |
| sulabh_out_of_domain_probes_quest1_quest2 | refusal_probe | REFUSAL | N/A (batch, not executed) |  | NON_RUNNABLE_BATCH |

## Summary counts

- runnable: 16
- non_runnable_batch: 2
- match: 2
- known_gap: 13
- new_gap: 1
- error: 0
