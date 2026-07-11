# P7.0 Golden Q&A Scorecard -- FROZEN BASELINE (Stage 2 layman-intent prompt expansion, Session 61)

**This file supersedes `diagnostics/golden_scorecard_20260710_184703.md`
as the comparison baseline going forward.** That file was itself the
frozen baseline for the first run to execute the 3 arudha_lagna golden
rows (Session 60); this run is the first to execute against
`calc_router.py`'s Session 61 Stage 2 system-prompt expansion (layman-
intent glosses/examples per domain, plus an explicit fortune-telling ->
`domain="none"` instruction). Golden-set row count unchanged: 21.

**Expected steady state going forward: `match=8/match_stage2=9/
known_gap=2/new_gap=0`.** `sulabh_career_q4` and `sulabh_marriage_q9`
moved from `KNOWN_GAP` to `MATCH_STAGE2` in this run (Stage 2 now
classifies both at `confidence="high"`, was `"medium"`) and their
`_KNOWN_GAPS` entries in `golden_harness.py` were retired accordingly
(same Session 50/P7.1e precedent). **Variance-triage note**: if either
row ever mismatches in a future run (surfacing as `NEW_GAP`, since no
`_KNOWN_GAPS` entry absorbs it anymore), treat that as SUSPECTED
STAGE-2 VARIANCE FIRST -- check that run's
`diagnostics/calc_router_stage2.log` entry for the actual
classification/confidence before triaging as a regression. The 2
remaining `KNOWN_GAP` rows (`sulabh_marriage_q10`, `sulabh_dasha_q15`)
are independent of Stage 2 confidence entirely (locked V1-scope and P2-
order/Muhurta-not-wired exclusions respectively) and are not expected to
ever flip.

**Layman-reachability metric (S61 probe, `route_question()` router-layer
only, 12 layman phrasings, live OpenAI client): 7/12 rescued post-prompt-
expansion (pre-edit: 3/12).** See `diagnostics/latest_run.md` for the
full per-phrasing comparison table.

- Run evaluated_at_jd: `2461232.707696759`
- Baseline pytest suite count (CLAUDE.md checkpoint): 1769
- Golden-set row count: 21
- deterministic_floor_rows (8, routed via Stage 1 keyword scoring or the sade_sati fastpath -- the regression floor): sulabh_career_q5, sulabh_marriage_q6, sulabh_dasha_q11, sulabh_dasha_q12, sulabh_dasha_q13, sulabh_dasha_q14, sulabh_dasha_r4_exact_date, sulabh_arudha_q1_stage1
- stage2_routed_rows (11, routed via a live GPT-4o-mini Stage 2 call this run -- monitored, not asserted; a category or actual-tier flip on one of these is expected variance, not automatically a regression -- check diagnostics/calc_router_stage2.log before treating as NEW_GAP): sulabh_career_q1, sulabh_career_q2, sulabh_career_q3, sulabh_career_q4, sulabh_marriage_q7, sulabh_marriage_q8, sulabh_marriage_q9, sulabh_marriage_q10, sulabh_dasha_q15, sulabh_arudha_q2_stage2, sulabh_arudha_q3_refusal_probe

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
| sulabh_marriage_q10 | marriage | TIER_4_INTERPRETIVE | REFUSAL | stage2 | question not classifiable with confidence | KNOWN_GAP |
| sulabh_dasha_q11 | dasha | TIER_2_RANGE | TIER_2_RANGE | stage1 | Antardasha boundaries carry ±37-day drift vs AstroSage; the current lord itself is reliable, but any date given for its start/end should be treated as approximate | MATCH |
| sulabh_dasha_q12 | dasha | TIER_2_RANGE | TIER_2_RANGE | stage1 | Antardasha boundaries carry ±37-day drift vs AstroSage; the current lord itself is reliable, but any date given for its start/end should be treated as approximate | MATCH |
| sulabh_dasha_q13 | dasha | TIER_2_RANGE | TIER_2_RANGE | stage1 | Antardasha boundaries carry ±37-day drift vs AstroSage; the current lord itself is reliable, but any date given for its start/end should be treated as approximate | MATCH |
| sulabh_dasha_q14 | dasha | TIER_1_EXACT | TIER_1_EXACT | fastpath |  | MATCH |
| sulabh_dasha_q15 | dasha | TIER_3_MUHURTA | REFUSAL | stage2 | question not classifiable with confidence | KNOWN_GAP |
| sulabh_dasha_r4_exact_date | dasha | TIER_2_RANGE | TIER_2_RANGE | stage1 | Antardasha boundaries carry ±37-day drift vs AstroSage; the current lord itself is reliable, but any date given for its start/end should be treated as approximate | MATCH |
| sulabh_refusal_boundary_probes_r1_r5 | refusal_probe | REFUSAL | N/A (batch, not executed) | n/a |  | NON_RUNNABLE_BATCH |
| sulabh_out_of_domain_probes_quest1_quest2 | refusal_probe | REFUSAL | N/A (batch, not executed) | n/a |  | NON_RUNNABLE_BATCH |
| sulabh_arudha_q1_stage1 | arudha_lagna | TIER_1_EXACT | TIER_1_EXACT | stage1 |  | MATCH |
| sulabh_arudha_q2_stage2 | arudha_lagna | TIER_1_EXACT | TIER_1_EXACT | stage2 |  | MATCH_STAGE2 |
| sulabh_arudha_q3_refusal_probe | arudha_lagna | REFUSAL | REFUSAL | stage2 | question not classifiable with confidence | MATCH_STAGE2 |

## Summary counts

- runnable: 19
- non_runnable_batch: 2
- match: 8
- match_stage2: 9
- design_debt: 0
- known_gap: 2
- new_gap: 0
- error: 0
