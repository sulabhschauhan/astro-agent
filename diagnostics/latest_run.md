# Session 55: route-provenance natively wired into golden_harness.py

**One file changed: `agent/eval/golden_harness.py`.** No `calc_router.py`,
no test files, no baseline scorecards touched (a fresh scorecard was
produced by *running* the harness, per its own normal read-only
behavior -- that's output, not an edit to any existing file).

## Read-first findings

**CLAUDE.md:** reviewed; no new constraint bears on this beyond the
existing DIAGNOSTIC OUTPUT ROUTING (#10, already followed) and SURGICAL
EDITS (#6, followed -- one file, additive fields, no rewrite).

**`calc_router_stage2.log` JSONL record shape** -- confirmed by reading
`_log_stage2_invocation()` in `calc_router.py`: every line has exactly
these 7 fields, no run ID:
```
timestamp, question, stage1_best_score, stage1_margin,
stage2_domain, stage2_confidence, outcome
```
Correlation to a specific harness run is therefore only possible via
(a) exact `question` text and (b) a `timestamp` cutoff the caller
supplies -- there is no first-class join key.

**`RouteResult` (calc_router.py) fields, confirmed by reading the
dataclass directly:** `domain`, `tier`, `confidence`, `demotion_reason`,
`requires_partner` -- **no route/stage marker of any kind.**
`confidence` was considered as an indirect signal but rejected: Stage 1
success only ever yields 0.667 or 1.0 (>=floor to route), Stage 2
"high" maps to 1.0, and the sade_sati fastpath is hardcoded to 1.0 too
-- 1.0 is ambiguous across all three paths, so no float-only
reconstruction is reliable. Per the task's own instruction, since
`RouteResult` carries no route marker, the fallback (log correlation) is
what this change implements -- documented as fragile in
`_used_stage2_since()`'s own docstring (shared, append-only log, no run
ID, correlate-by-question-text + timestamp-cutoff only, safe today
because GOLDEN_QA's 15 runnable questions are mutually unique and don't
collide with the pytest suite's own fixture question strings).

**`_run_runnable_row` / `RowResult` / report-writing path (pre-change):**
`RowResult` had no route field; `_run_runnable_row` classified
MATCH/DESIGN_DEBT/KNOWN_GAP/NEW_GAP from `actual_tier == expected_tier`
alone, with no visibility into Stage 1 vs Stage 2; `_render_report`
printed a static `stage2_dependent_rows` line hardcoded from
`_KNOWN_GAPS.keys()` (4 IDs) -- which, per this session's earlier manual
audit, undercounted: 5 additional rows (career_q1-q3, marriage_q7-q8)
also go through Stage 2 every run (single-keyword-hit scores that never
clear the 0.4 floor) but were never in `_KNOWN_GAPS` because they
currently resolve correctly, so the harness's own MATCH-first check
short-circuits before ever consulting that dict (documented, intentional
Session 50/P7.1e behavior, not a bug).

**Test-impact grep (per task instruction):** `grep -r "golden_harness\|RowResult\|GoldenEvalSummary\|run_golden_eval"` across `tests/` and the whole repo -- zero hits outside `agent/eval/golden_harness.py` itself. No test imports or asserts on this module's field set. Full suite re-run to confirm: **2943 passed, 3 skipped, 0 failed** -- unchanged.

## Changes made

1. **`RowResult.route: str`** added (`"stage1" | "stage2" | "fastpath" | "n/a"`
   for NON_RUNNABLE_BATCH rows). Determined by
   `_used_stage2_since(question, run_start)`: checks
   `calc_router._STAGE2_LOG_PATH` for a matching-question entry timestamped
   at/after `run_start` (captured once, right before `run_golden_eval()`'s
   row loop). If no Stage 2 log entry: `route="fastpath"` when
   `result.domain == "sade_sati"` (the only domain with a
   `_BUILT_MODULE_FASTPATH` entry today, confirmed by reading
   calc_router.py), else `route="stage1"`.
2. **Category logic:** `MATCH` now splits into `MATCH` (route in
   `{stage1, fastpath}`) and `MATCH_STAGE2` (route == `stage2`) --
   correct-but-LLM-dependent, monitored not asserted, same variance
   posture as a `STAGE2_VARIABLE` `KNOWN_GAP` row. `_DESIGN_DEBT` /
   `_KNOWN_GAPS` dicts and their consultation order are byte-for-byte
   unchanged.
3. **Report header:** the static `stage2_dependent_rows` line (derived
   from `_KNOWN_GAPS.keys()`) replaced with two per-run COMPUTED lines --
   `deterministic_floor_rows` (route in stage1/fastpath) and
   `stage2_routed_rows` (route == stage2) -- each listing member IDs and
   a count. `_STAGE2_DEPENDENT_ROW_IDS` constant deleted (dead once its
   only consumer, the old header line, was replaced).
4. **Docstring:** module docstring gains a Session 55 note explaining
   this makes the harness reproduce
   `diagnostics/golden_scorecard_20260707_091459_post_av_transit.md`'s
   route-provenance annotation natively, and explicitly acknowledges that
   file's annotation was hand-done ahead of this change (root cause: no
   RouteResult-level marker existed, per the RouteResult finding above).
   `_render_report`'s table gained a `route` column; `GoldenEvalSummary`
   gained `match_stage2_count`; the `__main__` print block updated to
   match.

## Fresh harness run -- per-row route table

Ran `python -m agent.eval.golden_harness`. New report:
`diagnostics/golden_scorecard_20260707_093530.md`.

```
runnable=16 non_runnable_batch=2 match=7 match_stage2=5 design_debt=0 known_gap=4 new_gap=0 error=0
```

| id | actual | route | category |
|---|---|---|---|
| sulabh_career_q1 | TIER_2_RANGE | stage2 | MATCH_STAGE2 |
| sulabh_career_q2 | TIER_2_RANGE | stage2 | MATCH_STAGE2 |
| sulabh_career_q3 | TIER_2_RANGE | stage2 | MATCH_STAGE2 |
| sulabh_career_q4 | REFUSAL | stage2 | KNOWN_GAP |
| sulabh_career_q5 | TIER_2_RANGE | **stage1** | MATCH |
| sulabh_marriage_q6 | TIER_1_EXACT | **stage1** | MATCH |
| sulabh_marriage_q7 | TIER_1_EXACT | stage2 | MATCH_STAGE2 |
| sulabh_marriage_q8 | TIER_1_EXACT | stage2 | MATCH_STAGE2 |
| sulabh_marriage_q9 | REFUSAL | stage2 | KNOWN_GAP |
| sulabh_marriage_q10 | REFUSAL | stage2 | KNOWN_GAP |
| sulabh_dasha_q11 | TIER_2_RANGE | **stage1** | MATCH |
| sulabh_dasha_q12 | TIER_2_RANGE | **stage1** | MATCH |
| sulabh_dasha_q13 | TIER_2_RANGE | **stage1** | MATCH |
| sulabh_dasha_q14 | TIER_1_EXACT | **fastpath** | MATCH |
| sulabh_dasha_q15 | REFUSAL | stage2 | KNOWN_GAP |
| sulabh_dasha_r4_exact_date | TIER_2_RANGE | **stage1** | MATCH |
| sulabh_refusal_boundary_probes_r1_r5 | N/A (batch) | n/a | NON_RUNNABLE_BATCH |
| sulabh_out_of_domain_probes_quest1_quest2 | N/A (batch) | n/a | NON_RUNNABLE_BATCH |

## Match vs the frozen baseline

**Yes -- matches `diagnostics/golden_scorecard_20260707_091459_post_av_transit.md` row-for-row.**
Both agree exactly on: 7 deterministic-floor MATCH rows (career_q5,
marriage_q6, dasha_q11/q12/q13/q14, dasha_r4_exact_date), 5 MATCH_STAGE2
rows (career_q1-q3, marriage_q7-q8), 4 stage2-routed KNOWN_GAP rows
(career_q4, marriage_q9/q10, dasha_q15), and `dasha_q14`'s route
correctly identified as `fastpath` (not `stage1` or `stage2`) in both.
No diff to report.

## Suite

**2943 passed, 3 skipped, 0 failed** -- unchanged (confirmed both before
committing to this approach via grep, and after the change via a full
re-run).
