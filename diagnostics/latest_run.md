# Session: test_av_transit_scorer.py -- score_av_transit() oracle + errors

**New file:** `tests/calculations/transits/test_av_transit_scorer.py`
(only file changed besides the benign `calc_router_stage2.log` growth from
running the suite; `git status` confirms it). No production code touched.

**Target:** `score_av_transit()` / `AvTransitScore` (added last session,
`agent/calculations/transits/av_transit_scorer.py`).

**Setup:** Sulabh's natal tables via the live pipeline -- same
`calculate_chart()` path as `test_ashtakavarga_cross_charts.py` (same
`_BIRTH_ARGS` literals, independently duplicated), then
`compute_bav`/`compute_sav`/`compute_bav_contributors`. All 8 placements
(Sun=Pisces, Moon=Scorpio, Mars=Capricorn, Mercury=Pisces, Jupiter=Aries,
Venus=Taurus, Saturn=Sagittarius, Lagna=Sagittarius) verified against the
live pipeline BEFORE writing the test file, and all 7 oracle cases'
expected field values (plus the 5 contributor sets cited in cases'
comments) were independently re-run against the live scorer and matched
exactly before being written into `_CASES` -- per this repo's
"verify task prompts against code" convention.

## Test layers (80 new tests)
- **(0) Placement sanity** (8, parametrized): pins all 8 of Sulabh's D-1
  sign placements so a placement/ephemeris wiring failure is
  distinguishable from a scorer-logic failure below.
- **(1) Oracle cases T1-T7** (63 = 7 cases x 9 fields, parametrized,
  `{case}-{field}` ids): hand-derived design-review oracle from PVR Table
  60 + Tables 19-26 against Sulabh's placements -- covers a plain
  UNFAVORABLE/UNFAVORABLE case, a plain FAVORABLE/EXCELLENT/has-rekha
  case at the last kakshya index (7=Lagna), the SAV-dominance
  DOWN-override (BAV favorable, SAV unfavorable -> verdict unfavorable),
  the SAV-dominance UP-override at the zero-degree kakshya boundary (BAV
  unfavorable, SAV favorable -> verdict favorable), Sun/Mars sign-level-
  only cases (kakshya fields None; EXCELLENT and VERY_POOR intensity
  respectively), and the NEUTRAL-BAV-to-AVERAGE-verdict mapping at the
  exact 3.75-degree half-open kakshya boundary (must land in kakshya
  index 1/Jupiter, not 0/Saturn). Each of the 9 `AvTransitScore` fields is
  asserted as its own parametrized case so a mismatch names the exact
  case+field.
- **(2) Error paths** (8): Moon/Mercury/Venus fail-closed exclusion (3,
  parametrized), degrees_in_sign boundary (30.0) and negative rejection
  (3, parametrized: 30.0, -0.0001, -5.0), unknown transit_planet (1),
  unknown transit_sign (1).
- **(3) Immutability** (1): `AvTransitScore` raises `FrozenInstanceError`
  on attribute mutation.

## Test tallies
- New file alone: `80 passed` in isolation (8 + 63 + 8 + 1 = 80, exact).
- Full suite: `2923 passed, 3 skipped, 1 warning in 87.93s` (was 2843
  passed, 3 skipped before this session; 2843 + 80 = 2923, exact).

No source or module logic changed.
