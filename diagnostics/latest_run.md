# P6 Jaimini: Bhava Arudha test suite (tests/calculations/test_jaimini_arudha.py)

**Task type:** new test file only. `agent/calculations/jaimini/arudha.py`
and every other module untouched -- this run adds
`tests/calculations/test_jaimini_arudha.py` exclusively, mirroring
`tests/calculations/test_jaimini_strength.py`'s structure and
provenance discipline.

## Layer A: PVR Example 29 book oracle (Chart 1)

Chart 1 ("Rasi Arudha example", April 9, 2000, 5:55pm (4:00 West),
71W12 42N30) was reconstructed by rendering PDF page 99 (0-idx 98) of
`data/pdfs/Vedic Astrology_ PVR Narashimha Rao.pdf` via pymupdf and
reading the printed longitude table directly beneath the chart diagram
-- this is a full, unambiguous 9-planet + Asc table, not narrative
inference:

```
Asc:  10 Vi 58            Sun:  26 Pi 29 (AK)      Moon: 4 Ge 45 (GK)
Merc: 1 Pi 36 (DK)        Jup:  17 Ar 21 (PiK)      Ven:  10 Pi 01 (PK)
Mars: 19 Ar 09 (MK)       Sat:  22 Ar 41 (BK)       Rahu: 5 Cn 55 (AmK)
Ketu: 5 Cp 55  (= Rahu + 180 exactly: 5Cn55 + 180 = 5Cp55)
```

Reconstructed `CHART1` dict (absolute sidereal degrees, Aries = 0):

```python
CHART1 = {
    "Sun": 356.48333333333335,   # 26 Pi 29
    "Moon": 64.75,                # 4 Ge 45
    "Mars": 19.15,                # 19 Ar 09
    "Mercury": 331.6,             # 1 Pi 36
    "Jupiter": 17.35,             # 17 Ar 21
    "Venus": 340.01666666666665,  # 10 Pi 01
    "Saturn": 22.683333333333334, # 22 Ar 41
    "Rahu": 95.91666666666667,    # 5 Cn 55
    "Ketu": 275.9166666666667,    # 5 Cp 55
}
```

Before writing any test code, this reconstruction was ratified two
ways:
1. Every planet's sign was cross-checked against Example 29's own
   per-house narration (e.g. "Lord is Mercury and he is in Pi" ->
   Mercury at 1Pi36 is indeed Pisces; "Lord is Saturn... in Ar"
   ("with 2 other planets") -> Saturn/Mars/Jupiter all in Aries,
   confirming the joiner-count claim used to pick Saturn over Rahu
   for Aquarius and Mars over Ketu for Scorpio).
2. `compute_arudha_pada()` was run against all 12 houses and its
   `count` field was compared to the book's own narrated intermediate
   numbers (item (1) count=7, (2) count=6, (3) count=6, (4) count=5,
   (5) count=4, (6) count=3, (7) count=2, (8) count=1, (9) count=11,
   (10) count=10, (11) count=12, (12) count=8) -- all 12 matched
   exactly, confirming the longitude reconstruction is faithful.

Per this task's scope, only `arudha_sign` is asserted in Layer A
(inputs are reconstructed, not book-printed arithmetic themselves;
`count`/`raw_ending_sign`/`co_lord_deciding_step` are commented as
not-asserted-here). All 12 houses match the book's printed answer:

| House sign | Book arudha_sign | Test result |
|---|---|---|
| Virgo (AL) | Gemini | PASS |
| Libra (A2) | Leo | PASS |
| Scorpio (A3) | Virgo | PASS |
| Sagittarius (A4) | Leo | PASS |
| Capricorn (A5) | Aries | PASS |
| Aquarius (A6) | Gemini | PASS |
| Pisces (A7) | Taurus | PASS |
| Aries (A8) | Capricorn | PASS |
| Taurus (A9) | Capricorn | PASS |
| Gemini (A10) | Virgo | PASS |
| Cancer (A11) | Taurus | PASS |
| Leo (UL) | Libra | PASS |

## Layer B: step-5 exception (synthetic)

All three fixture values were independently re-derived by hand against
`arudha.py`'s own COUNTING FORMULA docstring before the test file was
written (no failures encountered, so no design-chat values needed
revision):

- B1 (1st-house trigger): Aries/Mars@10.0 -> count=1,
  raw_ending_sign=Aries, exception_applied=True,
  arudha_sign=Capricorn, lord=Mars. PASS.
- B2 (7th-house trigger): Gemini/Mercury@165.0 -> count=4,
  raw_ending_sign=Sagittarius, exception_applied=True,
  arudha_sign=Virgo, lord=Mercury. PASS.
- B3 (no exception, PVR's own inline example): Gemini/Mercury@315.0 ->
  count=9, raw_ending_sign=Libra, exception_applied=False,
  arudha_sign=Libra. PASS.

## Layer C: co-lord dependency + propagation

- C1 (SHERIDAN, Scorpio): Ketu resident -> basic_rule picks Mars.
  Routing check only (arudha_sign not asserted as oracle). PASS.
- C2 (SULABH, Aquarius): Rahu resident -> basic_rule picks Saturn.
  Routing check only. PASS.
- C3 (synthetic, Mars@210.0 + Ketu@220.0 both in Scorpio): raises
  ValueError, message matches "D2|both" (strength.py's D2
  both-resident fail-closed, propagated unmodified out of arudha.py).
  PASS.

## Layer D: input contract

Unrecognized house_sign, missing planet key, extra planet key,
out-of-range high longitude (>=360), negative longitude, NaN longitude
-- all six raise ValueError with the offending token named in the
message, mirroring `test_jaimini_strength.py`'s Layer D paths exactly.
All PASS.

## Layer E: result-shape locks

`ArudhaPadaResult` confirmed frozen (`FrozenInstanceError` on
`setattr`) and hashable (`hash(result)` succeeds); type-checked as
`ArudhaPadaResult`. All PASS.

## Full suite verification

- New file alone: 27 passed, 0 failed (0.15s).
- Baseline (pre-change, confirmed by running the full suite before
  adding this file): 3074 passed, 3 skipped, 0 failed.
- Full suite after adding the file: **3101 passed, 3 skipped, 0
  failed** (96.36s) -- exactly 3074 + 27, matching the expected total.

## Files touched

- `tests/calculations/test_jaimini_arudha.py` -- new file, 27 tests.
- No other file edited. (`diagnostics/calc_router_stage2.log` picked up
  its usual +32 lines as an incidental side effect of running the
  Stage-2 router tests inside the full suite -- not a deliberate edit,
  consistent with this repo's existing "chore: update
  calc_router_stage2.log" commit pattern.)

## Not committed

Per task instruction, nothing has been committed. This report and the
new test file are pending review.
