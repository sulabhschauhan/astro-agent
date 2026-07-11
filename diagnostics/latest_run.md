# P7 Muhurta wiring, step 7 of 7: golden rows + dead-entry deletion + baseline freeze

Session 64. TWO FILES: `tests/fixtures/golden_qa_sulabh.py` (Change A) +
`agent/eval/golden_harness.py` (Change B), sanctioned as one prompt --
the harness deletion only makes sense atomically with the rows that
replace the gap. Design chat has NOT yet ratified this row table; per
constraint, nothing is committed.

## STEP 0 -- harness domain-mapping finding (reported before any edit)

`_classify_runnability()` gates RUNNABLE purely on `row["domain"] in
_GOLDEN_DOMAIN_TO_PIPELINE_DOMAIN` (a membership check; the dict's
VALUES are never actually consulted downstream -- `_run_runnable_row()`
calls the real `answer_question()` and reads whatever domain/tier it
returns, it never forces a pipeline domain from this mapping). Since
Change A's new rows carry `domain="muhurta_window"`, that string was
NOT yet a key in `_GOLDEN_DOMAIN_TO_PIPELINE_DOMAIN` (dict had 6
entries: career/marriage/dasha/av_transit(unused)/arudha_lagna/
upapada_lagna) -- both new rows would have classified NON_RUNNABLE_BATCH
without an addition. Exact addition made (Change B item 1):

```python
"muhurta_window": "muhurta_window",
```

Identity mapping, same precedent as arudha_lagna/upapada_lagna --
confirmed by reading calc_router.py's `_route_to_domain()`: its
muhurta_window branch returns `RouteResult(domain="muhurta_window",
...)` verbatim (line 816).

## CHANGE A -- tests/fixtures/golden_qa_sulabh.py, two new rows

**`sulabh_muhurta_q1_stage1`** -- question "what is an auspicious
muhurta for me this week", the S64-ratified Stage 1 phrasing (2
`_MUHURTA_WINDOW_KEYWORDS` hits, score 0.667). Deliberately reuses
`test_orchestrator_muhurta.py`'s own `_STAGE1_CLEAN_QUESTION` sentinel
VERBATIM (not varied to dodge a collision, unlike the arudha q1/q2
precedent) -- confirmed safe post-route-field-switchover: the
`_used_stage2_since()` log-correlation fragility that collision-
avoidance discipline used to guard against now only matters on
`answer_question()`'s ERROR path, which a clean Stage-1 resolution
never reaches. `expected_tier="TIER_3_MUHURTA"`, `adjudication=
"ratified_s64"`. `baseline_answer_summary`/claims note the
wall-clock-anchoring caveat (window VALUES vary every run by design,
only domain/tier/route/structure is golden-assertable) and cite the
S64-ratified pinned-JD oracle table (11 windows, tier1_window_count=4
at the S24 anchor, from `test_orchestrator_muhurta.py`'s Sulabh full
pin) as MATCH-note CONTEXT, not a live-run assertion.

**`sulabh_muhurta_q2_stage2`** -- a below-Stage-1-floor phrasing expected
to resolve via live Stage 2. **Task's own suggested candidate REJECTED**
after verification: "when is a good time for me to start something new"
was checked programmatically against every `_DOMAIN_KEYWORDS` list and
scores 1 hit, not zero -- the bare token "when" is a literal
`_DASHA_KEYWORDS` entry:

```
Q: when is a good time for me to start something new
  domain=current_dasha hits=['when'] score=0.333
  TOTAL HITS ACROSS ALL DOMAINS: 1
```

Shipped phrasing instead: **"is this a favorable moment to begin
something new in my life"** -- verified 0 hits across all 7
`_DOMAIN_KEYWORDS` lists, `_UNBUILT_MODULE_KEYWORDS`,
`_OUT_OF_SCOPE_KEYWORDS`, `_BUILT_MODULE_FASTPATH`, and `_STEM_MAP`
(all checked programmatically, not assumed):

```
Q: is this a favorable moment to begin something new in my life
  TOTAL HITS ACROSS ALL DOMAINS: 0
  unbuilt-module hits: []   out-of-scope hits: []
  fastpath hits: []         stem-map hits: []
```

Live-probed 4/4 stable before shipping (`route_question()`, real
GPT-4o-mini calls):

```
domain=muhurta_window tier=TIER_3_MUHURTA confidence=1.0 route=stage2  (x4)
```

Also confirmed end-to-end via `answer_question()` against the real
Sulabh chart (domain=muhurta_window, tier=TIER_3_MUHURTA, route=stage2,
demotion=None). No verbatim collision with any existing test/golden
question string (grepped before shipping -- zero matches).
`expected_tier="TIER_3_MUHURTA"`, `adjudication="ratified_s64"`,
MATCH_STAGE2 posture (monitored via calc_router_stage2.log, not
asserted), mirroring `sulabh_arudha_q2_stage2`'s style.

## CHANGE B -- agent/eval/golden_harness.py

1. Added `"muhurta_window": "muhurta_window"` to
   `_GOLDEN_DOMAIN_TO_PIPELINE_DOMAIN` (Step 0 finding above).
2. Deleted the dead `_KNOWN_GAPS["sulabh_dasha_q15"]` entry (S50 P7.2f
   precedent). MATCH_STAGE2 verified in the step 5 run (per
   `golden_harness.py`'s own deletion-comment citation of that report)
   before deletion; reconfirmed in this step's own full harness run
   below. Deletion is behavior-neutral: `_run_runnable_row` only
   consults `_KNOWN_GAPS` when `actual_tier != expected_tier`, so a
   MATCH/MATCH_STAGE2 row never reaches it.
3. Ride-along (CLAUDE.md carry-forward item, sanctioned by this file
   touch): fixed `_classify_runnability()`'s stale "3-domain whitelist"
   docstring -> "6-domain whitelist" (career/marriage/dasha/
   arudha_lagna/upapada_lagna/muhurta_window). Also fixed the module
   top-level docstring's twin "five pipeline-whitelisted domains" ->
   "six" for the same reason (same staleness class the CLAUDE.md item
   already named for both spots; leaving one fixed and one stale would
   immediately reintroduce the inconsistency).

**Observed but NOT touched** (out of this prompt's scope, flagged for a
future ride-along): `_GOLDEN_DOMAIN_TO_PIPELINE_DOMAIN`'s own
`"upapada_lagna"` comment still says "Dead entry as of this session: no
GOLDEN_QA row's `domain` field is `upapada_lagna` yet" and cites
`sulabh_arudha_q3_refusal_probe` as still carrying
`domain="arudha_lagna"` -- but that row's domain field was already
flipped to `"upapada_lagna"` per its own S70 NOTE comment in
`golden_qa_sulabh.py`. This comment predates my touch and is unrelated
to Change B's own edits; not fixed here to stay surgical.

## VERIFICATION 1 -- full pytest suite

```
python -m pytest -q
3141 passed, 3 skipped, 0 failed  (84.02s)
```

Same counts as the step 6b baseline -- no test pins `_KNOWN_GAPS`
contents.

## VERIFICATION 2 -- full golden harness run

```
python -m agent.eval.golden_harness
runnable=21 non_runnable_batch=2 match=10 match_stage2=10 design_debt=0 known_gap=1 new_gap=0 error=0
report: diagnostics/golden_scorecard_20260711_195218.md
```

Exactly as expected: both new rows land (q1 MATCH via stage1, q2
MATCH_STAGE2 via live stage2), `sulabh_dasha_q15` stays MATCH_STAGE2,
known_gap count drops 2 -> 1 (only `sulabh_marriage_q10` remains),
new_gap=0.

Full per-row table:

| id | domain | expected_tier | actual | route | category |
|---|---|---|---|---|---|
| sulabh_career_q1 | career | TIER_2_RANGE | TIER_2_RANGE | stage2 | MATCH_STAGE2 |
| sulabh_career_q2 | career | TIER_2_RANGE | TIER_2_RANGE | stage2 | MATCH_STAGE2 |
| sulabh_career_q3 | career | TIER_2_RANGE | TIER_2_RANGE | stage2 | MATCH_STAGE2 |
| sulabh_career_q4 | career | TIER_2_RANGE | TIER_2_RANGE | stage2 | MATCH_STAGE2 |
| sulabh_career_q5 | career | TIER_2_RANGE | TIER_2_RANGE | stage1 | MATCH |
| sulabh_marriage_q6 | marriage | TIER_1_EXACT | TIER_1_EXACT | stage1 | MATCH |
| sulabh_marriage_q7 | marriage | TIER_1_EXACT | TIER_1_EXACT | stage2 | MATCH_STAGE2 |
| sulabh_marriage_q8 | marriage | TIER_1_EXACT | TIER_1_EXACT | stage2 | MATCH_STAGE2 |
| sulabh_marriage_q9 | marriage | TIER_1_EXACT | TIER_1_EXACT | stage2 | MATCH_STAGE2 |
| sulabh_marriage_q10 | marriage | TIER_4_INTERPRETIVE | TIER_1_EXACT | stage2 | KNOWN_GAP |
| sulabh_dasha_q11 | dasha | TIER_2_RANGE | TIER_2_RANGE | stage1 | MATCH |
| sulabh_dasha_q12 | dasha | TIER_2_RANGE | TIER_2_RANGE | stage1 | MATCH |
| sulabh_dasha_q13 | dasha | TIER_2_RANGE | TIER_2_RANGE | stage1 | MATCH |
| sulabh_dasha_q14 | dasha | TIER_1_EXACT | TIER_1_EXACT | fastpath | MATCH |
| sulabh_dasha_q15 | dasha | TIER_3_MUHURTA | TIER_3_MUHURTA | stage2 | MATCH_STAGE2 |
| sulabh_dasha_r4_exact_date | dasha | TIER_2_RANGE | TIER_2_RANGE | stage1 | MATCH |
| sulabh_refusal_boundary_probes_r1_r5 | refusal_probe | REFUSAL | N/A (batch) | n/a | NON_RUNNABLE_BATCH |
| sulabh_out_of_domain_probes_quest1_quest2 | refusal_probe | REFUSAL | N/A (batch) | n/a | NON_RUNNABLE_BATCH |
| sulabh_arudha_q1_stage1 | arudha_lagna | TIER_1_EXACT | TIER_1_EXACT | stage1 | MATCH |
| sulabh_arudha_q2_stage2 | arudha_lagna | TIER_1_EXACT | TIER_1_EXACT | stage2 | MATCH_STAGE2 |
| sulabh_arudha_q3_refusal_probe | upapada_lagna | TIER_1_EXACT | TIER_1_EXACT | stage1 | MATCH |
| sulabh_muhurta_q1_stage1 | muhurta_window | TIER_3_MUHURTA | TIER_3_MUHURTA | stage1 | MATCH |
| sulabh_muhurta_q2_stage2 | muhurta_window | TIER_3_MUHURTA | TIER_3_MUHURTA | stage2 | MATCH_STAGE2 |

Summary counts: runnable=21, non_runnable_batch=2, match=10,
match_stage2=10, design_debt=0, known_gap=1, new_gap=0, error=0.

## VERIFICATION 3 -- new frozen baseline

`diagnostics/golden_scorecard_20260711_195218.md` is now the NEW FROZEN
BASELINE, superseding `golden_scorecard_20260711_112836.md`. Supersession
header written into the scorecard itself (predecessor citation, the S64
muhurta landing across all 7 steps, the q15 flip rationale, the two new
rows, expected steady state `match=10/match_stage2=10/known_gap=1/
new_gap=0`).

## Not committed

Per constraint: `tests/fixtures/golden_qa_sulabh.py` and
`agent/eval/golden_harness.py` remain uncommitted in the working tree.
`diagnostics/golden_scorecard_20260711_195218.md` (the new frozen
baseline) is also new/untracked. Design chat ratifies the row table
before any of these land.
