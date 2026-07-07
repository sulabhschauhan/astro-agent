# P6 Jaimini: Rasi Drishti Primitive (PVR Ch.10 §10.3)

**Task type:** new-file implementation. One file only:
`agent/calculations/jaimini/rasi_aspects.py`. No test file, no other
module touched, nothing imports this module yet.

## What was built

- `signs_rasi_aspected_by(sign: str) -> frozenset[str]`
- `rasi_aspects_between(sign_a: str, sign_b: str) -> bool`

Canonical Title-case sign vocabulary, identical to
`agent/calculations/core/aspects.py`. Unknown sign raises `ValueError`
naming it. Pure functions, no ephemeris calls, no import from
`aspects.py` (rasi drishti and graha drishti are different classical
mechanisms and must never be conflated -- see the module's own LOUD
docstring warning).

## Design

The 12-sign aspect table is derived programmatically at module import
from the movable/fixed/dual classification plus adjacency (PVR states
the rule + 3 worked single-sign examples, not a full 12x12 table --
per source verification, no such table exists anywhere in the book).
For each sign:

- Dual signs aspect all 3 other dual signs unconditionally (no
  adjacency exclusion, per PVR's own rule wording).
- Movable/fixed signs aspect all 3 signs of the opposite class, except
  whichever one of their two zodiacal neighbors happens to be of that
  opposite class (the other neighbor is always dual, by construction
  of the movable-fixed-dual repeating cycle around the zodiac).

Two machine-checked invariants run at import time (not just citation
prose):

1. **Symmetry** -- every derived aspect relation is asserted symmetric,
   matching PVR's explicit statement ("sign Y will aspect sign X if
   sign X aspects sign Y", §10.3).
2. **Cross-check against PVR's own worked examples** -- the derived
   sets for Aries/Taurus/Gemini are asserted equal to PVR's 3 printed
   worked rows verbatim.

## Independent verification against the Exercise 15 answer key

Beyond the 3 worked examples asserted in-module, all 9 rows of PVR's
Exercise 15 answer key (Chart 5, printed p.110 / PDF p.121) were
checked against the derived table by reverse lookup: for each
planet's expected aspected-rasis triplet, find which of the 12 signs
produces exactly that aspect set under `signs_rasi_aspected_by`.

| Planet | Expected aspected rasis (PVR) | Unique sign match |
|---|---|---|
| Sun | Cn, Li, Cp | Taurus |
| Moon | Le, Sc, Aq | Aries |
| Mars | Cp, Ar, Cn | Scorpio |
| Mercury | Pi, Ge, Vi | Sagittarius |
| Jupiter | Sg, Pi, Ge | Virgo |
| Venus | Ta, Le, Sc | Capricorn |
| Saturn | Cp, Ar, Cn | Scorpio |
| Rahu | Li, Cp, Ar | Leo |
| Ketu | Ar, Cn, Li | Aquarius |

All 9 rows resolved to exactly one matching sign each -- full
agreement with the derived table, no ambiguity, no mismatch. Notably
Ketu resolves uniquely to Aquarius (a fixed sign), confirming the
source-verification pass's inference and empirically reconfirming
that Ketu's rasi drishti follows ordinary zodiacal movable/fixed/dual
counting, NOT the anti-zodiacal rule that PVR scopes exclusively to
argala/virodhargala (§10.6) -- that scope note is quoted in the
module's own CITATION block with its scope flag.

## Verify

Full suite, zero delta expected (nothing imports the new module yet):

```
2972 passed, 3 skipped, 0 failed in 84.81s
```

Matches the expected baseline exactly.

## Commit

`P6 Jaimini: rasi drishti primitive (PVR Ch.10 §10.3)` -- pushed to
`main`.
