# Session: David Ashtakavarga fixture status update (doc-only)

**Changed file:** `tests/fixtures/jhora_david_ashtakavarga.md` (only file
changed besides the benign `calc_router_stage2.log` growth from running the
suite; `git status` confirms it). No table or checksum values touched.

**Edit 1:** Header `Status` line changed from `PARKED. Promotion target:
Ashtakavarga BAV/SAV module validation (hardest-case-first).` to `ACTIVE
oracle. Consumed by tests/calculations/ashtakavarga/test_ashtakavarga.py
(96/96 BAV + 12/12 SAV per-cell parity, Session 54).` — reflects that this
fixture is no longer parked; it backs the live per-cell parity suite.

**Edit 2:** End of the "D-1 positions" validation-trail paragraph — replaced
the sentence claiming cell-by-cell BAV/SAV parity "remains a distinct,
not-yet-done validation step" with a pointer to where that step was
subsequently completed (Session 54's `test_ashtakavarga.py` + module
CITATION block).

**Verification:** confirmed `tests/calculations/ashtakavarga/
test_ashtakavarga.py` actually references this fixture and runs David
per-cell BAV/SAV parity tests before writing either sentence, to avoid
overclaiming.

## Test tallies
- Full suite: `2348 passed, 3 skipped, 1 warning` — unchanged from before
  this edit (doc-only change, no logic touched).

No source or module logic changed.
