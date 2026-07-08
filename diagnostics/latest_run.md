# P6 Jaimini: Bhava Arudha Kernel (PVR Ch.9 Section 9.2)

**Task type:** new-file implementation. One file only:
`agent/calculations/jaimini/arudha.py`. No test file, no other module
touched, nothing imports this module yet.

## What was built

`compute_arudha_pada(house_sign, planet_longitudes) -> ArudhaPadaResult`
-- implements PVR Ch.9 Section 9.2's general Bhava Arudha procedure
(steps 1-6). This is the SAME algorithm for every house, AL (Arudha
Lagna, house 1) included -- AL is not a separate calculation, just this
procedure with `house_sign` = Lagna's sign. `jaimini/padas.py` (a later
file, per the Master Build Plan's own file split) will call this kernel
once per house (1-12) and attach the An/AL/UL labels from PVR's Table
18; that labeling layer deliberately does not live here.

Step 2's own text ("Take the stronger lord... The chapter on 'Strength
of Planets and Rasis' will explain the rules") is a direct, explicit
cross-reference to Ch.15 Section 15.5.1 -- confirming
`strength.stronger_co_lord()` (built and tested earlier this session)
is the PVR-mandated dependency for Scorpio/Aquarius house signs, not an
inferred one. Every other house sign uses its single classical lord.
`stronger_co_lord`'s own exceptions (D2 both-co-lords-resident, D6
exact Step-5(b) tie) propagate unmodified -- this module does not catch
or reinterpret them.

Counting formula (steps 3-5) was derived from PVR's own inline worked
numbers (Gemini->Aquarius = 9, 9 signs from Aquarius = Libra) as an
inclusive 1-based zodiacal count, with the "1st or 7th from the
original sign" exception check expressed as distance 0 or 6 (mod 12),
applied at most once (no worked example in the book chains the
correction).

Input contract mirrors karakas.py/strength.py: all 9 Title-case planet
keys required and range-validated ([0,360), NaN-safe form) even though
a classical (non-co-lorded) house sign only needs one planet's
position -- uniform full-birth-chart contract, same as the sibling
kernels.

`ArudhaPadaResult` is a frozen dataclass with explicit named fields
(house_sign, lord, lord_sign, co_lord_deciding_step, count,
raw_ending_sign, exception_applied, arudha_sign) -- flat-field style
like `CharaKarakasResult`, not a diagnostics tuple like
`StrongerCoLordResult`, because every arudha computation runs the same
fixed sequence of steps with no step-dependent early return.

## Oracle verification (no test file, per this task's scope)

PVR's own Example 29 (Chart 1, printed p.87 / PDF p.99) gives a FULL
12-house worked answer key -- every house's lord, sign, count, and
final arudha sign, including both co-lord cases (House 3 = Scorpio ->
Mars, House 6 = Aquarius -> Saturn, both resolved at step 1 per the
book's own "with 2 other planets" phrasing). Chart 1's planet-to-sign
placements were reconstructed from Example 29 + the companion Example
30 (Graha Arudha, same chart) and cross-checked for internal
consistency (e.g. Moon's sign independently confirmed from both
examples) before use.

All 12 houses matched exactly on the first run, including the two
co-lord cases resolving at `deciding_step="step_1"` as the book
narrates:

```
House  1 (Virgo)       -> Gemini      [AL]  OK
House  2 (Libra)       -> Leo               OK
House  3 (Scorpio)     -> Virgo   (Mars, step_1)  OK
House  4 (Sagittarius) -> Leo               OK
House  5 (Capricorn)   -> Aries             OK
House  6 (Aquarius)    -> Gemini  (Saturn, step_1) OK
House  7 (Pisces)      -> Taurus            OK
House  8 (Aries)       -> Capricorn         OK
House  9 (Taurus)      -> Capricorn         OK
House 10 (Gemini)      -> Virgo             OK
House 11 (Cancer)      -> Taurus            OK
House 12 (Leo)         -> Libra       [UL]  OK
```

Error paths spot-checked by hand: bad house_sign, missing planet key --
both raised as designed.

## Verify

Full suite, zero delta expected (nothing imports the new module yet):

```
3074 passed, 3 skipped, 0 failed in 97.00s
```

Matches the expected baseline exactly (unchanged from the prior
strength.py test-suite commit).

## Commit

Pending: `P6 Jaimini: bhava arudha kernel (PVR Ch.9 Section 9.2)`.
