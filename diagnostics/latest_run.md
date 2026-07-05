# P7.1e — Harness reconciliation post-Stage-2

**Date:** 2026-07-05 (Session 50)
**Task source:** pasted prompt, "Session 50 — P7.1e"
**File touched:** `agent/eval/golden_harness.py` only (surgical). No
router/test changes.

## What changed

1. **Deleted 5 dead `_KNOWN_GAPS` entries**: `sulabh_career_q1/q2/q3`,
   `sulabh_marriage_q7/q8`. Verified each was MATCH in the P7.1d
   (`diagnostics/golden_scorecard_20260705_075932.md`) run before
   deleting. Deletion is behavior-neutral: `_run_runnable_row` only
   consults `_KNOWN_GAPS`/`_DESIGN_DEBT` when `actual_tier !=
   expected_tier`, so a MATCH row never reaches either dict regardless of
   whether an entry exists.
2. **Rewrote the 4 remaining `_KNOWN_GAPS` entries**
   (`sulabh_career_q4`, `sulabh_marriage_q9`, `sulabh_marriage_q10`,
   `sulabh_dasha_q15`) with updated citations reflecting the actual P7.1d
   mechanism (Stage 2 medium-confidence refusal for q4/q9/q10; Stage 2
   domain="none" high-confidence refusal for q15) instead of the stale
   Stage-1-keyword-floor citations. Each entry now leads with the exact
   required annotation: *"STAGE2_VARIABLE: outcome depends on live
   GPT-4o-mini classification; a category flip on this row across runs is
   expected variance, not automatically a regression -- check
   diagnostics/calc_router_stage2.log before treating as NEW_GAP."*
3. **q10 extra note**: if Stage 2 ever routes this to
   `marriage_compatibility` (high confidence) on a future run, that's
   BENIGN — the koota data layer still matches golden's verified claims;
   only the entry's "observed mechanism" sentence would need updating, the
   underlying KNOWN_GAP conclusion (V1 scope lock: TIER_4_INTERPRETIVE
   never produced) is unaffected.
4. **q15 extra note**: if Stage 2 ever routes this to `current_dasha`
   (high confidence) on a future run, that IS a SOFT MISROUTE (a
   Muhurta-intent question answered as a dasha question) — flag to design
   chat, do not silently accept it the way q10's case is accepted.
5. **`_DESIGN_DEBT["sulabh_dasha_q14"]`**: unchanged, as instructed.
6. **Report header**: added a `stage2_dependent_rows` line, derived from
   `tuple(_KNOWN_GAPS.keys())` (not a separately hardcoded list, so it can
   never drift out of sync with the dict itself) — lists the same 4 ids
   with a one-line explanation of the expected-variance caveat.

## Harness re-run (once, to confirm reconciliation)

```
runnable=16 non_runnable_batch=2 match=11 design_debt=1 known_gap=4 new_gap=0 error=0
report: diagnostics/golden_scorecard_20260705_080701.md
```

Matches the expected counts exactly (`match=11 design_debt=1 known_gap=4
new_gap=0`). **No STAGE2_VARIABLE flip occurred this run** — q4, q9, q10,
q15 all landed on the identical REFUSAL/KNOWN_GAP outcome as the P7.1d
run (same underlying mechanism per each row, confirmed against the new
report's per-row table). Reported as observed, not chased further per the
task's own instruction.

## Full pytest suite (safety check)

```
1786 passed, 3 skipped, 1 warning in 74.67s
```
Exactly the expected `1786/3` baseline (1770 + 16 P7.1c Stage 2 unit
tests). Stub invocation count: 5, unchanged.

## Explicitly not done (per task scope)

- No router (`calc_router.py`) or test file changes.
- No second harness re-run to see if a flip eventually happens — first
  reconciliation run's data only.
