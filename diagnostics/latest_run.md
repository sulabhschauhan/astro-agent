# P6 Jaimini: Stronger Co-Lord Cascade -- Test Suite (PVR 15.5.1)

**Task type:** new-file test addition. One file only:
`tests/calculations/test_jaimini_strength.py`, covering the previously
test-free `agent/calculations/jaimini/strength.py` (committed 2ca52bc).
No production code touched.

## What was built

24 tests across 5 layers, mirroring `test_jaimini_karakas.py`'s
layered-oracle discipline:

- **Layer A (real-chart oracle, JHora v8 longitudes):** Sulabh-Aquarius
  (basic rule -> Saturn), Sheridan-Scorpio (basic rule -> Mars),
  Sulabh-Scorpio (cascade -> Ketu at step 2), Sheridan-Aquarius
  (cascade -> Rahu at step 1). Ketu longitudes derived as Rahu+180,
  cross-checked against `tests/fixtures/jhora_sulabh.md`'s own raw Ketu
  row (28 Le 25'02.40" = 28 Aq 25'02.40" + 180 exactly).
- **Layer B (PVR book-verbatim):** the Section 15.5.1 Step-2
  Saturn-count=2 worked example; Exercise 25 both halves (Aquarius:
  Saturn wins at step 4, dual beats movable; Scorpio: Ketu wins at
  basic rule); the Step 5(b) worked example using PVR's own two
  longitudes verbatim (Mars 23Li17, Ketu 5Cn54). Where PVR's prose
  gives only partial chart data (a few planets' signs, not a full
  9-planet set), the remaining planets were hand-placed and verified to
  be step-1/step-2/step-3/step-4-neutral so the fixture reaches the
  intended step on the book's own arithmetic, not by accident.
- **Layer C (design-lock regressions):** D2 (Saturn+Rahu both in
  Aquarius simultaneously -> fails closed, the real 2022-23 trigger),
  D3 (Mars in Aries contesting Scorpio -- self-dispositor conjoins
  trivially, isolated as the sole source of Mars's step-2 win), D4
  (Ketu placed in Capricorn -- Mars's own classical exaltation sign --
  proves a node gains nothing there), D6 (Saturn Ge15/Rahu Vi15 exact
  advancement tie after steps 1-4 all tie -> fails closed).
- **Layer D (input contract):** bad sign, both `purpose` reject paths
  (`dasa_duration` cites footnote 53; any other value lists the two
  recognized literals), missing/extra planet keys, out-of-range and
  negative longitudes, NaN (via the `not (0<=lon<360)` form).
- **Layer E (result-shape locks):** hashability, diagnostics is a
  tuple of 2-tuples, basic-rule short-circuit has empty diagnostics,
  return type check.

## Fixture verification method

Every synthetic Layer B/C fixture was hand-derived against PVR's rasi
drishti rules (`rasi_aspects.py`'s movable/fixed/dual scheme) before
being run, then cross-checked by executing `stronger_co_lord` directly
against each fixture and diffing the actual `deciding_step` /
diagnostics against the hand derivation -- all matched on the first
pass, no fixture required adjustment to match code output (which would
have defeated the purpose of an independent oracle check).

## Verify

```
tests/calculations/test_jaimini_strength.py: 24 passed
Full suite: 3074 passed, 3 skipped, 0 failed in 117.13s
```

Baseline was 3050 passed / 3 skipped (strength.py's prior no-test-file
commit). Delta is exactly +24, matching the new test count -- zero
delta elsewhere.

## Commit

Pending: `P6 Jaimini: stronger co-lord cascade test suite (PVR
15.5.1)`.
