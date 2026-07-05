# P7.1d — Golden harness re-run with live Stage 2 (read-only)

**Date:** 2026-07-05 (Session 50)
**Task source:** pasted prompt, "Session 50 — P7.1d (HARNESS RE-RUN, READ-ONLY)"
**Files touched:** none (no source/test/harness edits). Harness run once,
producing `diagnostics/golden_scorecard_20260705_075932.md` (new artifact,
committed alongside this report per existing precedent — 3 prior
`golden_scorecard_*.md` files from Session 49 are already committed).

## Run command

```
python -m agent.eval.golden_harness
```
Output: `runnable=16 non_runnable_batch=2 match=11 design_debt=1 known_gap=4 new_gap=0 error=0`

Run once, as instructed — no re-run to chase a better outcome.

## Per-row table (verbatim from the generated scorecard)

| id | domain | expected_tier | actual | demotion_reason | category |
|---|---|---|---|---|---|
| sulabh_career_q1 | career | TIER_2_RANGE | TIER_2_RANGE | Career strength held at Tier 2 (range): residual Shadbala uncertainty envelopes (±6 Virupa Ayana Bala general; ±59 Virupa Surbhi Kala Bala chart-specific) can flip close planet rankings; rank within envelope should be treated as approximate | MATCH |
| sulabh_career_q2 | career | TIER_2_RANGE | TIER_2_RANGE | (same career demotion reason) | MATCH |
| sulabh_career_q3 | career | TIER_2_RANGE | TIER_2_RANGE | (same career demotion reason) | MATCH |
| sulabh_career_q4 | career | TIER_2_RANGE | REFUSAL | question not classifiable with confidence | KNOWN_GAP |
| sulabh_career_q5 | career | TIER_2_RANGE | TIER_2_RANGE | (same career demotion reason) | MATCH |
| sulabh_marriage_q6 | marriage | TIER_1_EXACT | TIER_1_EXACT | (blank) | MATCH |
| sulabh_marriage_q7 | marriage | TIER_1_EXACT | TIER_1_EXACT | (blank) | MATCH |
| sulabh_marriage_q8 | marriage | TIER_1_EXACT | TIER_1_EXACT | (blank) | MATCH |
| sulabh_marriage_q9 | marriage | TIER_1_EXACT | REFUSAL | question not classifiable with confidence | KNOWN_GAP |
| sulabh_marriage_q10 | marriage | TIER_4_INTERPRETIVE | REFUSAL | question not classifiable with confidence | KNOWN_GAP |
| sulabh_dasha_q11 | dasha | TIER_2_RANGE | TIER_2_RANGE | (dasha ±37-day demotion reason) | MATCH |
| sulabh_dasha_q12 | dasha | TIER_2_RANGE | TIER_2_RANGE | (dasha ±37-day demotion reason) | MATCH |
| sulabh_dasha_q13 | dasha | TIER_2_RANGE | TIER_2_RANGE | (dasha ±37-day demotion reason) | MATCH |
| sulabh_dasha_q14 | dasha | TIER_1_EXACT | REFUSAL | question references Sade Sati transit engine, which is not in the 3-domain whitelist | DESIGN_DEBT |
| sulabh_dasha_q15 | dasha | TIER_3_MUHURTA | REFUSAL | question not classifiable with confidence | KNOWN_GAP |
| sulabh_dasha_r4_exact_date | dasha | TIER_2_RANGE | TIER_2_RANGE | (dasha ±37-day demotion reason) | MATCH |
| sulabh_refusal_boundary_probes_r1_r5 | refusal_probe | REFUSAL | N/A (batch, not executed) | | NON_RUNNABLE_BATCH |
| sulabh_out_of_domain_probes_quest1_quest2 | refusal_probe | REFUSAL | N/A (batch, not executed) | | NON_RUNNABLE_BATCH |

## Summary counts

- runnable: 16
- non_runnable_batch: 2
- match: **11** (was 6 at Session 49 close — +5)
- design_debt: 1 (unchanged — q14, Sade Sati, correctly never reaches
  Stage 2 at all: `_UNBUILT_MODULE_KEYWORDS` refuses before domain
  classification)
- known_gap: **4** (was 9 at Session 49 close — -5: q1/q2/q3/q7/q8 flipped
  to MATCH via Stage 2)
- new_gap: 0
- error: 0

`_KNOWN_GAPS`/`_DESIGN_DEBT` dict entries for q1/q2/q3/q7/q8 are now stale
(their prose still says "REFUSED BY DESIGN") but this is harmless: the
harness's own categorization checks `actual_tier == expected_tier` (MATCH)
BEFORE ever consulting either dict, so the stale prose is dead text, not a
miscategorization. Left untouched per instructions — reconciliation is a
design-chat decision, not this run's job.

## This run's Stage 2 log slice (9 invocations; `diagnostics/calc_router_stage2.log`, lines 48-56)

| question (row) | stage2_domain | stage2_confidence | outcome |
|---|---|---|---|
| "How strong is my career potential?" (q1) | career_strength | high | ROUTED:career_strength |
| "Which planet most supports my profession?" (q2) | career_strength | high | ROUTED:career_strength |
| "Is my 10th house strong enough for leadership roles?" (q3) | career_strength | high | ROUTED:career_strength |
| "Will a job change in the next 12 months favor me?" (q4) | career_strength | medium | REFUSAL (confidence='medium' not high) |
| "Does either of us have Mangal Dosha (Kuja Dosha)?" (q7) | marriage_compatibility | high | ROUTED:marriage_compatibility |
| "Is there a Nadi dosha between us?" (q8) | marriage_compatibility | high | ROUTED:marriage_compatibility |
| "Where is the weakest link in our compatibility?" (q9) | marriage_compatibility | medium | REFUSAL (confidence='medium' not high) |
| "What does our overall compatibility mean for us as a couple?" (q10) | marriage_compatibility | medium | REFUSAL (confidence='medium' not high) |
| "Which month this year is astrologically best for me to make a major move?" (q15) | none | high | REFUSAL (stage2 domain=none) |

Routed/refused split: **5 routed, 4 refused** (of 9 Stage-2-touching rows).
9 rows never reached Stage 2 at all (q5, q6, q11-q13, r4 cleared Stage 1
alone; q14 refused via the unbuilt-module-keyword path, which returns
before Stage 2 is reachable — confirmed by its log absence above).

## Flags requested by the task

**(a) Wrong-domain routes:** none. Every ROUTED row this run (q1, q2, q3,
q7, q8) matched the golden row's own `domain` field exactly
(career questions -> career_strength, marriage questions ->
marriage_compatibility).

**(b) Routed-but-wrong-tier:** none. All 5 ROUTED rows landed on their
golden `expected_tier` exactly (q1/q2/q3 -> TIER_2_RANGE, q7/q8 ->
TIER_1_EXACT), all via the same shared `_route_to_domain` path Stage 1
uses.

**(c) q10 / q15 misroute-by-design-intent check:** neither routed this
run. q10 got `confidence="medium"` (stayed REFUSAL); q15 got
`domain="none"` (stayed REFUSAL). Flagging for the record per the task's
own framing: this is LLM output at `temperature=0`, not a hard guarantee —
a future run COULD return `confidence="high"` for one of these, which
would then satisfy `_route_to_domain` and produce a tier other than
TIER_4_INTERPRETIVE/TIER_3_MUHURTA (both genuinely unreachable by this
pipeline's design). That would be a design-intent misroute if it ever
happens, per the task's own framing — did not occur this run, reported
as observed, not fixed.

## Explicitly not done (per task scope)

- No edits to `_KNOWN_GAPS` or `_DESIGN_DEBT` in `agent/eval/golden_harness.py`
  — reconciliation is design-chat first, per the task.
- No second harness run to see if results differ — first-run data only.
- No source/test/harness changes of any kind.
