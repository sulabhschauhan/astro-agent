# Session: Ashtakavarga cross-chart e2e pipeline test

**New file:** `tests/calculations/ashtakavarga/test_ashtakavarga_cross_charts.py`
(only file changed besides the benign `calc_router_stage2.log` growth from
running the suite; `git status` confirms it).

**Design:** unlike `test_ashtakavarga.py` (hardcoded David placements,
kernel-only), this file derives each chart's D-1 sign placements live via
`agent.chart_calculator.calculate_chart()` — validating
ephemeris -> sign-extraction -> BAV wiring end-to-end, not just the
AV_TABLES kernel (already cell-locked on David).

**Birth data:** verified against `tests/calculations/strength/
test_bhava_bala.py`'s existing `_BIRTH_ARGS` before writing — same
literals (`"6 Apr 1988", "00:30", "Calcutta, India"` etc.), independently
duplicated per this repo's per-module duplication convention.

**Verified computationally before writing any hardcoded expectation:** ran
`calculate_chart()` for all 3 charts via a throwaway script (deleted before
finalizing), fed the derived placements through `compute_bav`/`compute_sav`,
and diffed against `tests/fixtures/jhora_ashtakavarga_cross_charts.md` —
zero mismatches across all 3 charts before any test assertion was written.
Confirmed lagna signs: Sulabh=Sagittarius, Surbhi=Libra, Sheridan=Taurus
(all match the task's expected pins). Sheridan's sidereal Moon longitude:
2.16 degrees into Aries — comfortably clear of the ~1-arcmin ayanamsa-gap
boundary risk documented in the module docstring's KNOWN-RISK comment (not
currently triggered, but the comment + failure-message longitude-print stay
in place for future charts/runs).

## Test layers (330 new tests)
- **(a)** Full-grid parity: 3 charts x 8 owners x 12 signs = 288, parametrized,
  failure message names chart+owner+sign+got/expected; Sheridan-Moon
  mismatches additionally print the live computed Moon longitude.
- **(b)** SAV parity: 3 charts x 12 signs = 36, parametrized, plus 3
  grand-total-337 assertions.
- **(c)** Placement-sanity: 3 tests pinning each chart's derived lagna sign,
  so a placement/ephemeris wiring failure is distinguishable from a kernel
  failure.

## Test tallies
- New file alone: `330 passed` in isolation.
- Full suite: `2348 passed, 3 skipped, 1 warning in 115.06s` (was 2018
  passed, 3 skipped before this session; 2018 + 330 = 2348, exact).

No source or module logic changed.
