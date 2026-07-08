# P6 Jaimini: Bhava Padas test suite (tests/calculations/test_jaimini_padas.py)

**Task type:** new test file only. `agent/calculations/jaimini/padas.py`
and every other module untouched -- this run adds
`tests/calculations/test_jaimini_padas.py` exclusively, mirroring
`test_jaimini_arudha.py`'s structure, provenance discipline, and
CHART1 fixture (copied verbatim).

## Layer A: PVR Example 29 labeled book oracle

Single test (`test_all_12_houses_match_book`) calls
`compute_bhava_padas("Virgo", CHART1)` once and asserts against the
book-printed (label, arudha_sign) table for all 12 houses:

| House | Label (book) | arudha_sign (book) | Match |
|---|---|---|---|
| 1 | AL | Gemini | PASS |
| 2 | A2 | Leo | PASS |
| 3 | A3 | Virgo | PASS |
| 4 | A4 | Leo | PASS |
| 5 | A5 | Aries | PASS |
| 6 | A6 | Gemini | PASS |
| 7 | A7 | Taurus | PASS |
| 8 | A8 | Capricorn | PASS |
| 9 | A9 | Capricorn | PASS |
| 10 | A10 | Virgo | PASS |
| 11 | A11 | Taurus | PASS |
| 12 | UL | Libra | PASS |

Also asserted in this same test: `len(bps.padas) == 12` and
`house_num` runs 1..12 in order. Only `label` + `arudha_sign` are
book-printed per house -- `house_sign`/`lord`/`count`/etc. on
`BhavaPada.result` are already covered by test_jaimini_arudha.py's own
Layer A and deliberately not re-asserted here.

## Layer B: fail-closed D2 propagation through the full loop

This closes the specific gap test_jaimini_arudha.py's own C3 left
open: C3 called `compute_arudha_pada()` directly (single house), never
`compute_bhava_padas()`'s own 12-house loop. Here, `lagna_sign="Scorpio"`
makes house 1 itself Scorpio -- the synthetic chart (Mars@210.0 +
Ketu@220.0 both resident in Scorpio) triggers strength.py's D2
fail-closed on the very first loop iteration.
`pytest.raises(ValueError, match="D2|both")` around
`compute_bhava_padas("Scorpio", ...)`: PASS. Confirms the exception
propagates UNMODIFIED out of the whole-loop orchestration, not just
out of the single-house kernel.

## Layer C: input contract

- Unrecognized `lagna_sign` ("Xyz") raises ValueError naming it, before
  any pada is computed (checked ahead of the loop). PASS.
- Missing planet key (Ketu deleted from a CHART1 copy) raises
  ValueError naming it -- confirms the validation split documented in
  padas.py's own docstring: `lagna_sign` is checked locally,
  `planet_longitudes` validation is delegated entirely to
  `compute_arudha_pada()`, not duplicated in padas.py. PASS.

## Layer D: result-shape locks

- `BhavaPadaSet` confirmed frozen (`FrozenInstanceError` on `setattr`)
  and hashable (`hash(bps)` succeeds). PASS.
- `BhavaPada` confirmed frozen (`FrozenInstanceError` on a pada's own
  `label` setattr). PASS.
- Type-checks: `BhavaPadaSet` and every element of `.padas` is a
  `BhavaPada`. PASS.
- Label scheme: house 1 == "AL", house 12 == "UL", houses 2-11 ==
  `f"A{n}"`. PASS.

## Full suite verification

- New file alone: **9 passed**, 0 failed (0.20s).
- Baseline (pre-change, confirmed by running the full suite before
  adding this file): 3102 passed, 3 skipped, 0 failed.
- Full suite after adding the file: **3111 passed, 3 skipped, 0
  failed** (104.30s) -- exactly 3102 + 9, matching the expected total.

## Files touched

- `tests/calculations/test_jaimini_padas.py` -- new file, 9 tests.
- No other file edited.

## Not committed

Per task instruction, nothing has been committed. This report and the
new test file are pending review.
