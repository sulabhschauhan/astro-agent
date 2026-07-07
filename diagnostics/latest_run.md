# P6 Jaimini: Stronger Co-Lord Cascade (PVR 15.5.1)

**Task type:** new-file implementation. One file only:
`agent/calculations/jaimini/strength.py`. No test file, no other
module touched, nothing imports this module yet.

## What was built

`stronger_co_lord(sign, planet_longitudes, purpose="arudha") ->
StrongerCoLordResult` -- implements PVR Ch.15 Section 15.5.1's
"Stronger Co-Lord" cascade for Scorpio (Mars/Ketu) and Aquarius
(Saturn/Rahu) ONLY. Full text transferred verbatim into the module's
own CITATION block from the immediately preceding two-source
verification pass (this file's prior content), before this run
overwrote it -- basic rule, steps (1)-(5b), footnote 53, and Exercise
25 with its full answer key.

Input contract mirrors `karakas.py`'s guard style exactly: exactly the
9 Title-case planet keys required, missing/extra collected into one
`ValueError`, longitude range validated via the `not (0.0 <= lon <
360.0)` NaN-safe form, all range violations collected into one error.
`purpose="dasa_duration"` and any value other than `"arudha"` both
raise (design lock D5).

`StrongerCoLordResult` is a frozen dataclass (tuple fields only, same
shape discipline as `CharaKarakasResult`): `sign`, `winner`, `loser`,
`deciding_step`, and a `diagnostics` tuple of `(label, value)` pairs
recording every step actually evaluated (steps after the deciding one
are absent).

## Design locks (D1-D6)

All six resolve a gap the immediately preceding two-source
verification pass (PVR + PyJHora) found genuinely unresolved by the
source text itself:

- **D1** -- Step 1 joiner count uses 9-graha scope (Rahu/Ketu count as
  joiners). PVR's own example never tests this; PyJHora-lineage
  precedent adopted.
- **D2** -- both co-lord candidates occupying the contested sign
  simultaneously (e.g. Saturn+Rahu both in Aquarius, a real
  configuration -- 2022-23) raises `ValueError`. PVR's Basic Rule text
  only covers the one-resident case; Step 2's dispositor lookup is
  circular in the both-resident case. Known V1 gap, fails closed.
- **D3** -- dispositor = ordinary classical lord of the candidate's
  occupied sign (PVR-confirmed twice for nodes: Rahu's dispositor is
  always the ordinary lord, never a special node rule). Scorpio/
  Aquarius map to their classical lord (Mars/Saturn) for dispositor
  lookups only, never re-entering this cascade. Self-dispositor
  conjoins trivially (+1), falling out of the general formula with no
  special-cased code.
- **D4** -- Rahu/Ketu are never exalted for Step 3's purposes. PVR's
  own example never exalts a node; school-divergent alternatives
  exist but PVR doesn't adopt any of them in this section.
- **D5** -- `purpose="dasa_duration"` (PVR's Step 5(a)) is out of V1
  scope: footnote 53 itself defers the computation to a later chapter,
  so implementing it now would be oracle-free code.
- **D6** -- an exact Step-5(b) advancement tie fails closed with
  `ValueError`, same posture as `karakas.py`'s sibling tie handling.

## Manual oracle verification (no test file, per this task's scope)

Every numbered step was independently exercised against PVR's own
worked in-rule examples (constructing full 9-planet longitude
scenarios by hand, placing non-participating planets in signs proven
via `rasi_aspects.py` to be neutral -- neither conjunct nor
rasi-aspecting either candidate's sign, so earlier steps genuinely tie
through to the step under test):

| Step | PVR scenario | Expected winner | Result |
|---|---|---|---|
| Basic Rule | Saturn in Aq, Rahu elsewhere | Rahu (the other planet) | MATCH, `deciding_step="basic_rule"`, empty diagnostics |
| Step 1 | Saturn in Pi w/ Mars+Sun (2 joiners), Rahu in Ar w/ Jupiter (1 joiner) | Saturn | MATCH, joiners (2, 1) |
| Step 2 | Saturn in Ge w/ Mercury (dispositor=Mercury, count 2), Rahu in Ar (dispositor=Mars aspects, count 1) | Saturn | MATCH, counts (2, 1) -- confirms PER-ROLE counting (Mercury-as-listed-planet and Mercury-as-dispositor both score) |
| Step 3 | Saturn in Li (exalted), Rahu in Cn | Saturn | MATCH, exalted (True, False) |
| Step 4 | Mars in Ge (dual), Ketu in Aq (fixed) | Mars | MATCH, modality rank (3, 2) |
| Step 5(b) | Mars at 23Li17 (adv. 23.283), Ketu at 5Cn54 (adv. 30-5.9=24.1, measured from end of sign) | Ketu | MATCH, advancement (23.2833..., 24.0999...) -- exact arithmetic match to PVR's own worked numbers |

Error paths also verified by hand: D2 (both-resident ValueError), D5
(`purpose="dasa_duration"` ValueError), D6 (exact-tie ValueError,
constructed a genuine tie surviving steps 1-4), bad sign, bad purpose,
missing/extra planet keys, out-of-range longitude including NaN --
all raised as designed.

## Verify

Full suite, zero delta expected (nothing imports the new module yet):

```
3050 passed, 3 skipped, 0 failed in 88.56s
```

Matches the expected baseline exactly.

## Commit

`P6 Jaimini: stronger co-lord cascade (PVR 15.5.1)` -- pushed to
`main`.
