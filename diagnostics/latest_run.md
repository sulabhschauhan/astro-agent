# P7 Muhurta wiring, step 5 of 6: orchestrator gate (LAST gate)

Session 64. Wires `domain="muhurta_window"` into
`agent/infra/orchestrator.py`'s `_VALID_DOMAINS` -- the last of the 5
staged-rollout gates (chart_profile builder -> formatter -> chart_profile
dispatch -> router -> this gate). ONE FILE, as scoped. NOT committed --
design chat ratification pending (same posture as steps 1-4).

## Change: `_VALID_DOMAINS`

```python
_VALID_DOMAINS = {
    "marriage_compatibility",
    "career_strength",
    "current_dasha",
    "sade_sati",
    "av_transit",
    "arudha_lagna",
    "upapada_lagna",
+   "muhurta_window",
}
```

## Audit: every domain-conditional branch in `answer_question()`, checked by reading

| Branch | Behavior for muhurta_window | Code change needed? |
|---|---|---|
| `partner_chart_data`/`primary_role` validation (top of function) | Unconditional -- applies to ANY domain if `partner_chart_data` is supplied at all; muhurta_window questions never supply it, so this never fires for this domain, exactly as for sade_sati/career/dasha/arudha/upapada today. | No |
| `route_result.domain not in _VALID_DOMAINS` guard | Now passes for `"muhurta_window"` (the one-line change above). | No (this IS the change) |
| `marriage_compatibility`-only partner-data guard (`if route_result.domain == "marriage_compatibility" and partner_chart_data is None`) | String-equality-gated to exactly `"marriage_compatibility"` -- evaluates False for muhurta_window, confirmed by reading, not assumed. | No |
| `evaluated_at_jd` computation (`now_utc` -> `swe.julday`) | Unconditional -- computed for every domain regardless of routing outcome, then passed to `build_domain_profile()` unconditionally. | No |
| `is_marriage`/`is_av_transit` gates -> `partner_chart_data`/`primary_role`/`transit_planet` kwargs | Both booleans evaluate False for muhurta_window (neither is `"marriage_compatibility"` nor `"av_transit"`), so `build_domain_profile()` receives `partner_chart_data=None, primary_role=None, transit_planet="Saturn"` -- exactly the same values sade_sati/arudha_lagna/upapada_lagna already receive. `build_domain_profile()`'s own muhurta_window branch (step 3) doesn't accept or consume any of these three kwargs anyway. | No |
| `route` stamping (`dataclasses.replace(format_answer(profile), route=route_result.route)`) | Unconditional -- every domain's `DomainAnswer` gets `route` stamped from the same `route_result.route`, regardless of domain. | No |
| `_merge_router_demotion()` | See dedicated section below. | No |

**Conclusion: zero code changes needed beyond the `_VALID_DOMAINS` line.**
No branch required a STOP. This matches the arudha_lagna (S59) and
upapada_lagna (S66) precedent exactly -- the ONE genuinely new wrinkle
(evaluated_at_jd being load-bearing for this domain, not merely
"accepted uniformly but unused" like av_transit/arudha_lagna/
upapada_lagna) still required no code change, because this function
already threads `evaluated_at_jd` through unconditionally for every
domain -- see step 3's own flagged departure/fix for why that threading
exists at all. Documented this explicitly in both the `_VALID_DOMAINS`
comment block and the `answer_question()` docstring's own NOTE
paragraph, following the existing per-domain-addition documentation
precedent in this file.

## `_merge_router_demotion()`: confirmed no-op by reading both sides

- `calc_router.py`'s `_route_to_domain()` muhurta_window branch (step 4):
  `demotion_reason=None`, hardcoded.
- `result_formatter.py`'s `_format_muhurta_window()` (step 2):
  `demotion_reason=None`, hardcoded.

`_merge_router_demotion()`'s own logic: `if router_reason is None: return
answer` (unchanged). Since the router's side is always `None` for this
domain, the function returns the formatter's `DomainAnswer` completely
unmodified -- a true no-op passthrough, same as arudha_lagna/
upapada_lagna/sade_sati. Verified by reading, not assumed; also verified
empirically in the live smoke test below (`demotion_reason: None` on the
final `DomainAnswer`).

## VERIFICATION 1: full pytest suite

```
python -m pytest -q
3134 passed, 3 skipped, 0 failed  (85.32s)
```

Zero delta, exactly as expected -- no test exercises the live muhurta
path yet.

## VERIFICATION 2: live e2e smoke test

```python
answer_question("what is an auspicious muhurta for me this week", <sulabh chart>)
```
```
domain: muhurta_window
tier: AnswerTier.TIER_3_MUHURTA
route: stage1
route is not None: True
sources: ('muhurta_scorer.py',)
demotion_reason: None
stub_caveats: ()
uncertainty_virupa: 0.0   uncertainty_days: 0.0
summary: {'tier1_window_count': 4, 'earliest_tier1_start': '12 Jul 2026 02:59 UTC'}
first window: {"start_jd": 2461233.3059375, "end_jd": 2461233.624569149,
  "start": "11 Jul 2026 19:20 UTC", "end": "12 Jul 2026 02:59 UTC",
  "tier": "TIER_2", "favorable_count": 1, "warnings": []}
window count: 12
```

`route` is stamped (`"stage1"`, not `None`) -- asserted, not just
observed: `answer.route is not None` printed `True`. Full builder ->
dispatch -> router -> orchestrator -> formatter chain works end to end,
live, for the first time this staged rollout.

## VERIFICATION 3: natal identifiers, closing the step-1 verify-at-e2e obligation

```
lagna_chart["rasi"]: Scorpio -> natal_moon_sign index: 7
lagna_chart["nakshatra"]: Vishakha -> janma_nakshatra index: 15
SIGNS[7]: Scorpio   NAKSHATRAS[15]: Vishakha
```

Confirmed **(7, 15)** = Scorpio/Vishakha, matching the S27 canonical
values the task cited. Closes step 1's own verify-at-e2e obligation on
the `lagna_chart` key semantics (`"rasi"`/`"nakshatra"` hold the MOON's
sign/nakshatra, not the Ascendant's -- see `chart_profile.py`'s
`_koota_natal_info_from_chart` docstring for the original documented
precedent this reuses) -- now confirmed live, not just by reading.

## VERIFICATION 4: full golden harness run vs. frozen baseline

```
python -m agent.eval.golden_harness
runnable=19 non_runnable_batch=2 match=9 match_stage2=9 design_debt=0 known_gap=1 new_gap=0 error=0
report: diagnostics/golden_scorecard_20260711_192135.md
```

Frozen baseline (`golden_scorecard_20260711_112836.md`) expected steady
state: `match=9/match_stage2=8/known_gap=2/new_gap=0`.

**One delta found: `match_stage2` 8 -> 9 (+1), `known_gap` 2 -> 1 (-1).**
`match`, `new_gap`, `design_debt`, `error` all unchanged (9, 0, 0, 0).
`runnable`/`non_runnable_batch` (19/2) inferred unchanged -- the frozen
baseline file doesn't print an explicit count line for these two, but
the golden-set row count is unchanged (21, untouched this session) and
no row's runnability criteria were touched, so a change here would be
surprising; not independently re-derived beyond that inference.

**Identified the exact row, per CLAUDE.md's "check before treating a
flip as regression" convention (not fixed, per this task's own
instruction):**

```
baseline: | sulabh_dasha_q15 | dasha | TIER_3_MUHURTA | REFUSAL      | stage2 | question not classifiable with confidence | KNOWN_GAP    |
this run: | sulabh_dasha_q15 | dasha | TIER_3_MUHURTA | TIER_3_MUHURTA | stage2 |                                          | MATCH_STAGE2 |
```

`sulabh_marriage_q10` (the other frozen-baseline `KNOWN_GAP` row) is
UNCHANGED -- still `TIER_4_INTERPRETIVE` expected vs. `TIER_1_EXACT`
actual, `KNOWN_GAP`, exactly as the frozen baseline's own header text
predicts it should stay regardless of routing outcome (locked V1-scope
Tier 4 interpretive-synthesis exclusion).

`sulabh_dasha_q15`'s own fixture (`tests/fixtures/golden_qa_sulabh.py`
line ~541) already carries `"expected_tier": "TIER_3_MUHURTA"` and
`"expected_techniques": ["muhurta_scorer", "vimshottari"]` -- this row
was WRITTEN in anticipation of muhurta_window eventually going live, and
was tracked as `KNOWN_GAP` (actual REFUSAL, since the domain was entirely
unrouteable before this session's steps 1-5) precisely until that day
came. Now that muhurta_window is live end-to-end (this step closes the
last gate), this row's live behavior changed to actually produce
`TIER_3_MUHURTA` via Stage 2 classification, matching its long-standing
expectation exactly -- **this reads as the golden set catching up with a
newly-live domain, not a regression.** Per this task's explicit
instruction ("report, don't fix"), no fixture/harness edit was made;
whether to re-ratify this row's category (mirroring the
`sulabh_arudha_q3_refusal_probe` precedent from Session 63, which
similarly flipped `REFUSAL`->live-behavior and was re-ratified in a
LATER, separate, dedicated step) is left to design chat.

## Not committed

Per constraint: `agent/infra/orchestrator.py` remains uncommitted in the
working tree. Design chat ratifies before any commit.
