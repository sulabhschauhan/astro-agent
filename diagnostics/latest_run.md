# P7.2d — Orchestrator whitelist unblock for sade_sati

**Date:** 2026-07-05 (Session 50)
**Task source:** pasted prompt, "Session 50 — P7.2d"
**File touched:** `agent/infra/orchestrator.py` only. No other changes.

## Item 1: full read + domain-specific-branch audit

Read `orchestrator.py` fully before editing. Added `"sade_sati"` to
`_VALID_DOMAINS` (now a 4-member set). Audited `answer_question()` for
any OTHER domain-specific branching, per instruction ("report anything
found that special-cases the 3 original domains, even if it happens to
pass through safely"):

- **Marriage-only partner-data guard** (`if route_result.domain ==
  "marriage_compatibility" and partner_chart_data is None: raise
  ValueError(...)`) — special-cases ONLY `"marriage_compatibility"`;
  evaluates `False` for `sade_sati` (and always did for
  `career_strength`/`current_dasha`) — passes through unchanged.
- **`is_marriage`-gated pass-through into `build_domain_profile()`**
  (`partner_chart_data=partner_chart_data if is_marriage else None,
  primary_role=primary_role if is_marriage else None`) — `is_marriage`
  is `False` for `sade_sati`, so both args pass as `None`, which is
  exactly `build_domain_profile`'s own contract for any non-marriage
  domain (verified against `chart_profile.py`'s own `ValueError` guard
  for non-marriage domains receiving those kwargs).

No other domain-specific branch exists. Both of the above evaluate to
their safe/no-op branch for `sade_sati` — confirmed by reading, not
assumed. Documented this finding inline in `answer_question()`'s own
docstring rather than only in this report.

Also updated 2 stale `"3-domain whitelist"` string literals (the
`ValueError` message and a docstring line) to `"routable whitelist"` —
accuracy fix, not a behavior change.

## Item 2: demotion-merge safety for the T1/None-reason case

Read `_merge_router_demotion()`. For `sade_sati`, `route_result
.demotion_reason` is always `None` (calc_router.py's `sade_sati` branch
in `_route_to_domain`) and the formatter's `DomainAnswer.demotion_reason`
is also always `None` (`_format_sade_sati`). The function's very first
check is `if router_reason is None: return answer` — returns the
formatter's `DomainAnswer` completely unchanged. No `" | "`
concatenation is ever reached, no `None`-formatting risk. **Confirmed
safe by reading; nothing added, per instruction ("add nothing unless
broken").**

## Item 3: end-to-end smoke test (verbatim result)

```python
answer_question("Am I currently in Sade Sati, and when does the next cycle begin?", chart)
```
```python
DomainAnswer(
    domain='sade_sati',
    tier=<AnswerTier.TIER_1_EXACT: 'TIER_1_EXACT'>,
    answer_payload={
        'active': False,
        'phase': 'NONE',
        'next_cycle_start': '27 Jan 2041',
        'previous_cycle_end': '24 Jan 2020',
    },
    stub_caveats=(),
    uncertainty_virupa=0.0,
    demotion_reason=None,
    sources=('sade_sati',),
    uncertainty_days=0.0,
)
```
Matches the task's expected outcome exactly.

## Item 4: full suite

```
1786 passed, 3 skipped, 1 warning in 70.82s
```
Unchanged. Grepped `tests/` for any assertion on the old `"3-domain
whitelist"`/`_VALID_DOMAINS` wording — none exists, consistent with the
green run.

## Item 5: golden harness re-run (once)

```
runnable=16 non_runnable_batch=2 match=12 design_debt=0 known_gap=4 new_gap=0 error=0
report: diagnostics/golden_scorecard_20260705_085333.md
```

**`sulabh_dasha_q14` row**: `actual=TIER_1_EXACT`, `expected_tier=
TIER_1_EXACT` -> **MATCH** (was `DESIGN_DEBT` as of P7.1e). Confirms the
predicted mechanism exactly: `_run_runnable_row`'s category check tests
`MATCH` before ever consulting `_DESIGN_DEBT`, so
`golden_harness.py`'s `_DESIGN_DEBT["sulabh_dasha_q14"]` entry is now
**dead** (never reached for this row again) but is still physically
present in the file. **Not deleted this prompt, per instruction** —
flagging for a future reconciliation prompt (same pattern as P7.1e's
`_KNOWN_GAPS` cleanup).

**STAGE2_VARIABLE rows** (`sulabh_career_q4`, `sulabh_marriage_q9`,
`sulabh_marriage_q10`, `sulabh_dasha_q15`): all 4 identical to the P7.1e
run — no flip this run (all REFUSAL/KNOWN_GAP, same underlying Stage 2
mechanism as before).

## Explicitly not done (per task scope)

- No edit to `golden_harness.py`'s now-dead `_DESIGN_DEBT["sulabh_dasha_q14"]`
  entry — reported only, per instruction 5.
- No other file touched besides `orchestrator.py`.
