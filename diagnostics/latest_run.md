# Session: test_ashtakavarga_contributors.py -- compute_bav_contributors()

**New file:** `tests/calculations/ashtakavarga/test_ashtakavarga_contributors.py`
(only file changed besides the benign `calc_router_stage2.log` growth from
running the suite; `git status` confirms it). No production code touched.

**Target:** `compute_bav_contributors()` (added last session for future
Prastaara Ashtakavarga kakshya scoring, CITATION (e)) -- not
`compute_bav`/`compute_sav`/`AV_TABLES`, which stay locked per the two
existing ashtakavarga test files.

## Test layers (495 new tests)
- **(A) Cardinality invariant, via public API:** 4 charts (David hardcoded,
  Sulabh/Surbhi/Sheridan derived live via `calculate_chart()`, reusing the
  exact placement paths from `test_ashtakavarga.py` and
  `test_ashtakavarga_cross_charts.py`) x 8 owners x 12 signs = 384,
  parametrized. Re-derives `len(contributors[owner][sign]) ==
  compute_bav(...)[owner][sign]` from both functions' public return values
  -- does NOT trust `compute_bav_contributors`'s own internal assert.
- **(B) Membership oracle:** David's complete Sun-BAV contributor sets (12
  signs, parametrized), hand-derived in design review 2026-07-06 from PVR
  Table 19, provided in the prompt and independently re-verified against
  the live `compute_bav_contributors()` output before being written into
  the test (all 12 sets matched exactly). Catches what cardinality alone
  cannot -- two cells swapping a contributor while matching in count.
  Failure message names the sign and the symmetric difference.
- **(C) Type/immutability + error paths:** 96 `isinstance(..., frozenset)`
  checks (David, all 8 owners x 12 signs) + 3 `ValueError` tests mirroring
  `compute_bav`'s exactly (missing contributor, unknown contributor key,
  unknown sign), since `compute_bav_contributors` delegates validation to
  `compute_bav`.

## Test tallies
- New file alone: `495 passed` in isolation (384 + 12 + 96 + 3 = 495, exact).
- Full suite: `2843 passed, 3 skipped, 1 warning in 101.87s` (was 2348
  passed, 3 skipped before this session; 2348 + 495 = 2843, exact).

No source or module logic changed.
