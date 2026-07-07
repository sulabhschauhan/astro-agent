# Session 55: test coverage for result_formatter.py's av_transit branch

**File-discovery check (per task instructions, done before writing):**
- `tests/infra/test_result_formatter.py` -- does not exist.
- Grepped `tests/` for `format_answer` -- only hit is
  `tests/infra/test_orchestrator_e2e.py`, which is an explicit **no-mocks,
  real-chart** end-to-end suite per its own module docstring (exercises
  the full `answer_question() -> route_question() -> build_domain_profile()
  -> format_answer()` path against real `calculate_chart()` output). Not a
  home for synthetic-payload unit tests of a single render branch.
- Conclusion: no dedicated formatter test file exists -> **created**
  `tests/infra/test_result_formatter_av_transit.py`.

**Changed files:** `tests/infra/test_result_formatter_av_transit.py` (new,
8 tests) only, plus the benign `diagnostics/calc_router_stage2.log` growth
from running the suite. `result_formatter.py` and all other production
files untouched, as required.

**Test design:** all profiles are synthetic `DomainChartProfile` instances
built directly (frozen dataclass, `domain="av_transit"`,
`uncertainty_days=37.0`) -- no chart computation, no ephemeris calls.
`format_answer()` is called directly (the av_transit branch is not
reachable via any live router/orchestrator path yet -- Session 54
Conflict A: formatter lands before convergence wiring and router).

8 tests, hardest case first:
1. `test_empty_sub_windows_raises_never_collapse_value_error` -- empty
   `sub_windows` -> `ValueError` containing both "Session 54" and
   "never-collapse".
2. `test_rank_order_preserved_not_resorted` -- designed-adversarial case:
   rank 1 has LOWER `bav_bindus` than rank 2; asserts output order tracks
   input rank order, not score. Catches an accidental re-sort.
3. `test_retrograde_reentry_same_sign_not_deduplicated` -- two windows,
   identical sign, different date ranges -> both survive as distinct
   entries.
4. `test_kakshya_lord_none_for_sign_level_planet` -- `transit_planet="Sun"`,
   `kakshya_lord=None` -> rendered as `None`, key present, not dropped or
   stringified.
5. `test_jd_rendering_epoch_anchor` -- `start_jd=2451545.0` (J2000) ->
   `"1 Jan 2000"`, hand-verifiable against `swe.revjul()`.
6. `test_tier_always_tier_2_range_and_demotion_reason_fixed` -- tier is
   always `TIER_2_RANGE`; `demotion_reason` contains both "37-day" and
   "day-level" substrings (the two orthogonal uncertainty axes).
7. `test_sources_tuple_exact` -- `sources` tuple matches the 4 modules in
   order exactly.
8. `test_missing_payload_key_raises_key_error` -- payload without
   `"dasha_envelope"` -> `KeyError` (fail-closed convention, no partial
   render).

No ride-along fixes; no other file touched.

## Test tallies
- New file alone: `8 passed` (isolated run, confirmed before full suite).
- Full suite: `2943 passed, 3 skipped, 1 warning` -- matches the expected
  2935 + 8 = 2943 derivation exactly. No delta to flag.

No production/calculation module logic changed.
