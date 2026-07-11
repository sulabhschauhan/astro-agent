# P7.0 Golden Q&A Scorecard -- FROZEN BASELINE (upapada_lagna live end-to-end, Session 70)

**This file supersedes `diagnostics/golden_scorecard_20260711_045928.md`
as the comparison baseline going forward.** That file was the frozen
baseline for Session 61's Stage 2 layman-intent prompt expansion; this
run is the first baseline with the Upapada Lagna (UL) domain live
end-to-end across the whole pipeline (chart_profile.py S63,
result_formatter.py S64, calc_router.py Stage 1/Stage 2 S65,
orchestrator.py S66, golden_harness.py's domain mapping S69) AND with
`sulabh_arudha_q3_refusal_probe`'s golden row itself re-ratified to
match (fixture edits S67 domain-mapping-deferred + S70 domain flip).
Golden-set row count unchanged: 21.

`sulabh_arudha_q3_refusal_probe` -- previously an unwired-construct
REFUSAL probe (pre-S63) -- now resolves **MATCH / stage1 /
TIER_1_EXACT**: Upapada Lagna = Aquarius (Ketu primary, co-lord cascade
step 2), routed via Stage 1's deterministic "upapada lagna" keyword
bigram (S65), no live Stage 2 call. Row `domain` field is now
`"upapada_lagna"` (S70; was `"arudha_lagna"` as a deliberate S67
stopgap, since `golden_harness.py`'s `_GOLDEN_DOMAIN_TO_PIPELINE_DOMAIN`
had no `"upapada_lagna"` key until S69). Row `id` stays
`sulabh_arudha_q3_refusal_probe` -- NOT renamed -- to preserve
scorecard-history correlation across every prior report this id
appears in; the "refusal_probe" suffix is now historical, not
descriptive of current behavior (see the row's own S70 NOTE comment in
`tests/fixtures/golden_qa_sulabh.py`).

`sulabh_marriage_q10` -- unaffected by any of the above. Its own,
independent routing-behavior shift (S65 Stage 2 prompt expansion
causing live routing to flip Stage-2-medium/REFUSAL ->
marriage_compatibility/TIER_1_EXACT) was ruled a correct-classification
improvement in design chat (S67: 5/5 live probe runs routed at
confidence=high) and is noted only in that row's own fixture `note` --
`expected_tier`/category (`TIER_4_INTERPRETIVE`/`KNOWN_GAP`) are
unaffected either way, since the row was always going to mismatch
`TIER_4_INTERPRETIVE` regardless of routing outcome (locked V1-scope
Tier 4 interpretive-synthesis exclusion).

**Expected steady state going forward: `match=9/match_stage2=8/
known_gap=2/new_gap=0`.**

**Errata (count-prediction history, recorded for the record, not
corrected in past entries):**
- Design chat's S67 task prompt predicted `match_stage2=9` for that
  run ("q3 joins the deterministic floor as MATCH; derive check: prior
  8+1"). This forgot that q3 had ALREADY exited the Stage-2-classified
  set one run earlier (S66): once `calc_router.py`'s S65 wiring gave
  this exact question string a Stage 1 keyword bigram match, it never
  touched Stage 2 again in any subsequent run -- `match_stage2` could
  only ever go DOWN from q3's perspective, never back up, once that
  bigram existed.
- The S67 follow-up's own diagnostics reconciliation correctly landed
  on the right number (`match_stage2=8`) but framed "prior" as the
  immediately-preceding S66 run (already-degraded to 8), describing it
  as "stays unchanged at 8". The TRUE frozen-baseline value (this
  file's predecessor, `golden_scorecard_20260711_045928.md`) was **9**,
  not 8 -- the real, permanent movement is **9 -> 8**, caused by q3
  leaving the Stage-2-classified group entirely partway through this
  saga (S65's bigram wiring), not by anything that happened in S67
  itself. Both slips are corrected here, in this baseline's own header,
  for anyone reconciling old count lines against this one.

- Run evaluated_at_jd: `2461232.977962963`
- Baseline pytest suite count (CLAUDE.md checkpoint): 1769
- Golden-set row count: 21
- deterministic_floor_rows (9, routed via Stage 1 keyword scoring or the sade_sati fastpath -- the regression floor): sulabh_career_q5, sulabh_marriage_q6, sulabh_dasha_q11, sulabh_dasha_q12, sulabh_dasha_q13, sulabh_dasha_q14, sulabh_dasha_r4_exact_date, sulabh_arudha_q1_stage1, sulabh_arudha_q3_refusal_probe
- stage2_routed_rows (10, routed via a live GPT-4o-mini Stage 2 call this run -- monitored, not asserted; a category or actual-tier flip on one of these is expected variance, not automatically a regression -- check diagnostics/calc_router_stage2.log before treating as NEW_GAP): sulabh_career_q1, sulabh_career_q2, sulabh_career_q3, sulabh_career_q4, sulabh_marriage_q7, sulabh_marriage_q8, sulabh_marriage_q9, sulabh_marriage_q10, sulabh_dasha_q15, sulabh_arudha_q2_stage2

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
| sulabh_dasha_q15 | dasha | TIER_3_MUHURTA | REFUSAL | stage2 | question not classifiable with confidence | KNOWN_GAP |
| sulabh_dasha_r4_exact_date | dasha | TIER_2_RANGE | TIER_2_RANGE | stage1 | Antardasha boundaries carry ±37-day drift vs AstroSage; the current lord itself is reliable, but any date given for its start/end should be treated as approximate | MATCH |
| sulabh_refusal_boundary_probes_r1_r5 | refusal_probe | REFUSAL | N/A (batch, not executed) | n/a |  | NON_RUNNABLE_BATCH |
| sulabh_out_of_domain_probes_quest1_quest2 | refusal_probe | REFUSAL | N/A (batch, not executed) | n/a |  | NON_RUNNABLE_BATCH |
| sulabh_arudha_q1_stage1 | arudha_lagna | TIER_1_EXACT | TIER_1_EXACT | stage1 |  | MATCH |
| sulabh_arudha_q2_stage2 | arudha_lagna | TIER_1_EXACT | TIER_1_EXACT | stage2 |  | MATCH_STAGE2 |
| sulabh_arudha_q3_refusal_probe | upapada_lagna | TIER_1_EXACT | TIER_1_EXACT | stage1 |  | MATCH |

## Summary counts

- runnable: 19
- non_runnable_batch: 2
- match: 9
- match_stage2: 8
- design_debt: 0
- known_gap: 2
- new_gap: 0
- error: 0
