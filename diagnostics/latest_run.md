# Session 56: Ashtakavarga test file — first per-cell fixture parity

**New file:** `tests/calculations/ashtakavarga/test_ashtakavarga.py` (new
`tests/calculations/ashtakavarga/` dir, no `__init__.py` added — matches the
`tests/calculations/core/` precedent, which also has none and collects
fine). Module (`agent/calculations/ashtakavarga/ashtakavarga.py`) and every
other file left untouched (`git status` confirms only this new test dir +
the benign `calc_router_stage2.log` growth from running the suite).

**Oracle:** `tests/fixtures/jhora_david_ashtakavarga.md` (JHora v8, David,
reference=natal lagna Virgo), David's placements per the JHora Basics tab
(Sun/Mercury=Cp, Moon=Le, Mars=Ta, Jupiter=Pi, Venus=Sc, Saturn=Cn,
Lagna=Vi).

**Verified computationally before writing any hardcoded expectation**
(learned from the earlier Sun-Leo fixture typo): ran `compute_bav`/
`compute_sav` live against the fixture table first — all 96 BAV cells and
all 12 SAV cells matched exactly, zero mismatches, before the test file was
written. This is the module's first-ever cell-by-cell parity check against
this fixture (previously flagged as "not yet performed" in both the
module's CITATION block and the fixture's own D-1 positions note — this
closes that gap).

## Test layers (123 new tests)
- **Layer A** (96): full-grid parity, every (owner, sign) cell, parametrized,
  failure message names owner+sign+got/expected.
- **Layer B** (14): SAV parity (12, parametrized) + grand-total-337 (1) +
  Lagna-exclusion proof via hand-summing the 7 planet BAVs per sign and
  confirming adding Lagna's own BAV would change the total (1).
- **Layer C** (8): canonical row totals (48/49/39/54/56/52/39/49), re-derived
  from the public return value rather than trusting the module's internal
  assert.
- **Layer D** (3): ValueError on missing contributor, unknown contributor
  key, unknown sign name.
- **Layer E** (2): Parasara/Varahamihira convention sentinels — Moon-Aries
  == 3 (9th-from-Moon + 2nd-from-Jupiter, both land on Aries for David's
  placements) and Venus-Leo == 4 (4th-from-Mars) — both verified
  computationally, docstrings state a mismatch means the Varahamihira
  variant, not a bug, per the module's own CITATION block (b).

## Test tallies
- New file alone: `123 passed` in isolation.
- Full suite: `2018 passed, 3 skipped, 1 warning in 95.49s` (was 1895 passed,
  3 skipped before this session; 1895 + 123 = 2018, exact).

No source or module logic changed.
