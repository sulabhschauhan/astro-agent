# S70 F-E: comma-tolerant absence filler groups

**MODIFIED TWO FILES.** `agent/interpretive/palm_reading.py`
(`_build_absence_noun_pattern` only, inside the `_ABSENCE_PATTERNS_BY_
FEATURE` construction) and `tests/interpretive/test_palm_reading.py`
(new Item 18 section, appended). No other code touched --
`_ABSENCE_PHRASES` (Tier 1), `_SUPPORT_NEEDLES`, `_ABSENCE_NOUN_EXTRAS`
untouched.

## MEASURE FIRST -- exact prior pattern

```python
def _build_absence_noun_pattern(needles: tuple[str, ...]) -> re.Pattern:
    noun_alt = "|".join(re.escape(n) for n in needles)
    return re.compile(
        rf"\bno\b(?:\s+\w+){{0,3}}\s+(?:{noun_alt})s?\b(?:\s+\w+){{0,6}}\s+visible\b",
        re.IGNORECASE,
    )
```

Shape: `\bno\b` + 0-3 pre-noun filler hops (`(?:\s+\w+)`) + a mandatory
connector `\s+` + the noun (+ optional `s`, word-boundary) + 0-6
post-noun filler hops + `\s+visible\b`. Every hop and the connector
require literal whitespace immediately -- a comma anywhere in that
position breaks the match, since `,` is not `\s` and not `\w`.

## New pattern

```python
def _build_absence_noun_pattern(needles: tuple[str, ...]) -> re.Pattern:
    noun_alt = "|".join(re.escape(n) for n in needles)
    return re.compile(
        rf"\bno\b(?:[,;]?\s+\w+){{0,3}}[,;]?\s+(?:{noun_alt})s?\b[,;]?"
        rf"(?:[,;]?\s+\w+){{0,6}}\s+visible\b",
        re.IGNORECASE,
    )
```

Changes (repetition counts `{0,3}`/`{0,6}` unchanged):
1. Both filler-hop groups (pre- and post-noun) become `(?:[,;]?\s+\w+)`
   -- an optional single `[,;]` immediately before each hop's whitespace.
2. An optional `[,;]` also added immediately after the noun match
   (`s?\b[,;]?`), before the post-noun filler resumes.
3. **One deviation from the instructing prompt's stated scope, found
   necessary by direct testing, not assumed:** the mandatory connector
   `\s+` directly before the noun ALSO needed `[,;]?` tolerance. Reason:
   in the target sentence "No crosses, stars, grilles, squares, or moles
   clearly visible", `\b` cannot fire between "cross" and the following
   "es" (both `\w` characters, no boundary) -- so "crosses" is NOT a
   valid match point for the "cross" needle, contrary to my first
   (wrong) manual trace. The only needle that actually lands on a real
   word boundary in that sentence is "square" (in "squares", followed
   by a comma). Reaching it requires 3 pre-noun hops ("crosses",
   "stars", "grilles"), which leaves a comma immediately before the
   noun-connector's `\s+` -- so that connector needed the same
   tolerance as the hops, or the target case does not flip. Verified by
   running the regex directly (see below) before writing tests, not
   assumed correct from the diff alone. No other loosening was added;
   "or"/"and" still consumed as ordinary filler words within the
   unchanged hop budgets.

## Direct regex verification (pre-test, interactive)

```
markings/target (comma list):  True   (was False pre-edit)
markings/semi   (semicolon):   True   (was False pre-edit)
life/islands regression:       False  (unchanged)
head/islands regression:       False  (unchanged)
heart/islands regression:      False  (unchanged)
```

## Tests added (`tests/interpretive/test_palm_reading.py`, Item 18)

1. `test_absence_comma_list_phrasing_flips_markings_to_absent` -- target
   case, asserts `_is_absence(text, "markings/other features") is True`.
2. `test_absence_semicolon_list_phrasing_also_flips_markings_to_absent`
   -- semicolon variant of the same case.
3. `test_absence_islands_regression_guard_stays_present_for_line_
   features` (parametrized over `life line`/`head line`/`heart line`) --
   F-B's "...no breaks, chains, forks, or islands visible" case must
   stay `_is_absence(...) is False` for all three line features (per-
   feature noun anchoring: "island" is a markings needle, not a
   life/head/heart needle, so it can never be the match point there).

No existing test asserted the old pattern's literal source string, so
zero existing tests were modified.

## Test run (targeted only, per instructions -- no full suite)

```
pytest tests/interpretive/test_palm_reading.py -q
62 passed, 4 skipped (pre-existing F-H retirement skips, unchanged)
```

## Out of scope, confirmed untouched

Noun-after-"visible" phrasing ("There is no clearly visible fate
line") -- stays a V1.1 register item, not attempted here.
