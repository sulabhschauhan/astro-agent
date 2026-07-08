# P6 Jaimini: Bhava Padas kernel (agent/calculations/jaimini/padas.py)

**Task type:** new-file implementation. One file only:
`agent/calculations/jaimini/padas.py` (replacing its 1-line stub). No
test file, no other module touched, nothing imports this module yet
(kernel-then-test-suite rhythm, matching arudha.py/strength.py this
session).

## What was built

`compute_bhava_padas(lagna_sign, planet_longitudes) -> BhavaPadaSet` --
the orchestration + labeling layer arudha.py's own docstring explicitly
defers here: calls `compute_arudha_pada()` once per house (1-12) and
attaches PVR's An/AL/UL labels (Ch.9 Section 9.2, Table 18 printed
p.87).

- **Whole-sign house assembly**: house n falls in the sign at
  `(lagna_idx + n - 1) % 12`; house 1 IS lagna_sign. This is the only
  house-division convention arudha.py's docstring left for a caller to
  supply, and the only one PVR endorses anywhere in the book (Ch.7
  Section 7.5 "A Controversy" explicitly rejects Sripati/equal-house
  cusps for this purpose).
- **Labels**: house 1 -> "AL", house 12 -> "UL", else `f"A{n}"` --
  PVR's own verbatim naming (Ch.9 Section 9.2).
- **Validation split**: `lagna_sign` membership in the 12 canonical
  rasis is checked BEFORE the loop, raising ValueError naming the bad
  value. `planet_longitudes`' key-set/range validation is delegated
  entirely to `compute_arudha_pada()` -- not duplicated here (one-line
  comment at the docstring and call site say so explicitly).
- **Fail-closed (locked decision)**: any ValueError `compute_arudha_pada()`
  raises for any of the 12 houses -- including strength.py's D2
  (both co-lords resident) and D6 (exact Step-5(b) tie), for a
  Scorpio/Aquarius house -- propagates UNMODIFIED. No catch, no partial
  `BhavaPadaSet`: a chart with even one unresolvable house has no
  well-defined bhava-pada set as a whole. Commented at the call site
  with this rationale, per task instruction.

## Result shape

- `BhavaPada` (frozen dataclass): `house_num: int`, `label: str`,
  `result: ArudhaPadaResult`.
- `BhavaPadaSet` (frozen dataclass): `lagna_sign: str`,
  `padas: tuple[BhavaPada, ...]` (length 12, ordered house 1-12) -- a
  tuple, not list/dict, so the whole set stays hashable like its
  sibling jaimini/ result types (`ArudhaPadaResult`,
  `StrongerCoLordResult`).
- `_CANONICAL_SIGNS` is a local copy (not imported from arudha.py/
  strength.py) -- matches this session's own locked precedent that
  each jaimini/ kernel module carries its own copy rather than sharing
  one (see SESSION_LOG.md Session 57, Key Decision 1).

## Hand verification (no test file, per this task's scope)

Ran `compute_bhava_padas("Virgo", CHART1)` against PVR's own Example 29
(Chart 1, the same fixture reconstructed for arudha.py's test suite)
before considering this done. All 12 houses matched the book's printed
answer key exactly, both label AND arudha_sign:

| House | Label | House sign | arudha_sign (book) | Match |
|---|---|---|---|---|
| 1 | AL | Virgo | Gemini | OK |
| 2 | A2 | Libra | Leo | OK |
| 3 | A3 | Scorpio | Virgo | OK |
| 4 | A4 | Sagittarius | Leo | OK |
| 5 | A5 | Capricorn | Aries | OK |
| 6 | A6 | Aquarius | Gemini | OK |
| 7 | A7 | Pisces | Taurus | OK |
| 8 | A8 | Aries | Capricorn | OK |
| 9 | A9 | Taurus | Capricorn | OK |
| 10 | A10 | Gemini | Virgo | OK |
| 11 | A11 | Cancer | Taurus | OK |
| 12 | UL | Leo | Libra | OK |

Also confirmed directly:
- `BhavaPadaSet` is frozen (`FrozenInstanceError` on `setattr`) and
  hashable (`hash(bps)` succeeds).
- Bad `lagna_sign` ("Xyz") raises ValueError naming it, before the
  loop runs.
- A chart missing a required planet key (`Ketu` deleted) raises
  ValueError naming it -- confirming validation genuinely delegates to
  `compute_arudha_pada()` rather than silently passing through.

## Full suite verification

**3102 passed, 3 skipped, 0 failed** (91.84s) -- identical to the
committed baseline after the arudha.py test-suite close-out. Zero
delta, as expected: nothing imports `padas.py` yet.

## Files touched

- `agent/calculations/jaimini/padas.py` -- full kernel, replacing the
  1-line stub. No other file edited.

## Not committed

Per task instruction, nothing has been committed. This report and the
new module are pending review.
