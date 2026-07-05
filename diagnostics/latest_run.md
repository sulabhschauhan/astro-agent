# P7.2f — Harness dead-entry cleanup

**Date:** 2026-07-05 (Session 50)
**Task source:** pasted prompt, "Session 50 — P7.2f"
**File touched:** `agent/eval/golden_harness.py` only (trivial surgical edit).

## What changed

Deleted the dead `_DESIGN_DEBT["sulabh_dasha_q14"]` entry — verified MATCH
in `diagnostics/golden_scorecard_20260705_085333.md` (P7.2d's run) before
deleting; deletion is behavior-neutral since `MATCH` is checked before
this dict is ever consulted. `_DESIGN_DEBT` is now `{}`, kept (dict +
category machinery) as the correct slot for the next genuine, un-locked
product gap, per a one-line comment.

## Harness re-run (once)

```
runnable=16 non_runnable_batch=2 match=12 design_debt=0 known_gap=4 new_gap=0 error=0
report: diagnostics/golden_scorecard_20260705_090311.md
```
Matches exactly as expected. All 4 STAGE2_VARIABLE rows
(`sulabh_career_q4`, `sulabh_marriage_q9`, `sulabh_marriage_q10`,
`sulabh_dasha_q15`) identical to the P7.2d run — **no flip this run**.

## Full suite

```
1790 passed, 3 skipped, 1 warning in 82.47s
```
Unchanged.
