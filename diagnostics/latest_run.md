# P6 Jaimini: Rasi Drishti Oracle Tests (PVR Ch.10 §10.3 + Exercise 15)

**Task type:** new test file only.
`tests/calculations/test_jaimini_rasi_aspects.py`. One file. No other
module touched, and `agent/calculations/jaimini/rasi_aspects.py` was
NOT modified -- any oracle disagreement was to be treated as a genuine
falsification and reported, not fixed forward. None occurred.

## Oracle sources used

(a) PVR's 3 printed worked rows (Ch.10 §10.3), transcribed verbatim
    from `rasi_aspects.py`'s own CITATION block, hardcoded in the test
    (not recomputed from the rule):
    - Aries -> {Leo, Scorpio, Aquarius}
    - Taurus -> {Cancer, Libra, Capricorn}
    - Gemini -> {Virgo, Sagittarius, Pisces}

(b) PVR Exercise 15 answer key (Chart 5, printed p.110 / PDF p.121),
    all 9 rows, transcribed exactly as quoted in the CITATION block.
    Each row's occupied sign is uniquely determined by reverse lookup
    (exactly one of the 12 signs produces that row's aspected-rasis
    triplet); the parametrized test then checks the forward direction
    (occupied sign -> expected aspected set) against the module.

All 9 rows agreed with the module's computed table, including the
Ketu row (Ketu in Aquarius -> Aries/Cancer/Libra) -- confirming ordinary
zodiacal movable/fixed/dual counting, NOT the anti-zodiacal rule PVR
scopes exclusively to argala/virodhargala (§10.6). No disagreement
found; no falsification to report.

## Test layers (7)

1. 3 worked-row oracle tests (§10.3, hardcoded sets).
2. Exercise 15 oracle, parametrized over 9 rows (including the Ketu
   scope-proof row, commented).
3. Exhaustive symmetry sweep -- all 144 ordered sign pairs,
   `rasi_aspects_between(a, b) == rasi_aspects_between(b, a)`.
4. Structural locks, full 12-sign sweeps: every aspect set has exactly
   3 members; movable-only-aspects-fixed / fixed-only-aspects-movable;
   dual sets equal exactly the other 3 duals; no sign aspects an
   adjacent sign; no sign aspects itself (contract lock,
   `rasi_aspects_between(x, x) is False` for all 12 signs).
5. Return-type lock: `signs_rasi_aspected_by` returns `frozenset` for
   all 12 signs.
6. Error-path + message-content asserts: unknown sign ("Atlantis") in
   both public functions -> `ValueError` naming it; case sensitivity
   ("ARIES" rejected), consistent with `aspects.py`'s existing
   contract.
7. Cross-system guard: imports `signs_aspected_by` from
   `agent.calculations.core.aspects` and asserts Sun in Aries's graha
   drishti result ({Libra}) is disjoint from Aries's rasi drishti set
   ({Leo, Scorpio, Aquarius}) -- tripwire against future accidental
   unification of the two systems.

## Verify

Isolated run (new file only): `78 passed in 0.14s`.

Full suite, baseline `2972 passed / 3 skipped / 0 failed`:

```
3050 passed, 3 skipped, 0 failed in 96.13s
```

Delta: +78 passed (exactly the new test count), 0 lost, 0 failed.
Matches expectation -- nothing regressed.

## Commit

`P6 Jaimini: rasi drishti oracle tests (PVR Ch.10 §10.3 + Exercise 15)`
-- pushed to `main`.
