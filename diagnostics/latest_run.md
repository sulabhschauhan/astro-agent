# P7 Muhurta wiring, step 6b of 7: promote ratified Layer B values to asserts

Session 64. `tests/infra/test_orchestrator_muhurta.py` -- promotes the S64
design-chat-ratified Layer B table (previously measured, reported, and
left unasserted in step 6) to hard value asserts. ONE FILE, test-only, no
source edits. STILL NOT committed per this prompt's own constraint --
design chat must ratify before the commit lands.

## What changed vs. step 6

**Sulabh (`test_sulabh_structural_and_natal_ids`)** -- full pin (hardest
case: both Janma Tara and Janma Rashi warning paths fire in-window):
- window count == 11
- per-window tier SEQUENCE: `[T2,T1,T1,T2,T1,T2,T2,T3,T2,T1,T2]`
- per-window favorable_count SEQUENCE: `[1,2,2,1,2,1,1,0,1,2,1]`
- per-window warnings bands: idx 7 == `("Janma Tara",)`, idx 8 ==
  `("Janma Tara", "Janma Rashi")`, idx 9 and 10 == `("Janma Rashi",)`, all
  other indices == `()`
- summary == `{"tier1_window_count": 4, "earliest_tier1_start": "21 Jun
  2026 04:01 UTC"}`

Comment in the test file cites the ratification source: table ratified S64
design chat (the MEASURE-FIRST block reported in this file's step-6
version); the Janma Tara band boundaries (idx 7-8) are independently
corroborated by S24's own Vishakha occupancy scan -- verbatim minute
match, not a fresh unverified observation.

**David/Surbhi/Sheridan (`_assert_chart_structural`)** -- light pins added:
- natal-id value asserts: David `(4, 9)`, Surbhi `(10, 23)`, Sheridan
  `(0, 0)` (was: range-only checks `0<=sign<=11`, `0<=nakshatra<=26`)
- per-chart `tier1_window_count` asserts: David 2, Surbhi 3, Sheridan 2
- window COUNT is deliberately NOT asserted for these 3 -- a code comment
  on `_assert_chart_structural` explains why: all 4 charts landing on
  count==11 at this particular pinned anchor is a coincidence of this
  week's transit boundary structure, not an invariant. Only Sulabh (the
  full-table pin) asserts count==11, and only because it's paired with the
  exact sequence that produced it, not as a standalone claim.
- Full per-window tier/favorable_count/warnings sequences stay unasserted
  for these 3 (sample-before-scale: one full pin, three light pins).

## Warnings comparison type -- verified by reading, not assumed

Traced the full passthrough chain:
- `agent/calculations/transits/muhurta_scorer.py`: `MuhurtaWindowScore`
  dataclass field `warnings: tuple[str, ...]`, constructed via
  `warnings=tuple(warnings)` (line 146) from a `list[str]` built during
  scoring -- so it's a genuine tuple at the source, not a list dressed as
  one.
- `agent/infra/chart_profile.py` `build_muhurta_profile()` (line 1266):
  `"warnings": w.warnings` -- direct dataclass-attribute passthrough, no
  `list()` cast.
- `agent/infra/result_formatter.py` `_format_muhurta_window()` (line 857):
  `"warnings": w["warnings"]` -- dict-key passthrough, again no cast.

Conclusion: **tuple end to end**, confirmed at all 3 layers by reading the
source, not inferred from the diagnostic table's `repr()` output alone.
The new asserts compare against tuple literals (`("Janma Tara",)`, etc.),
matching the payload's actual runtime type.

## Test run

New file in isolation:
```
7 passed in 1.02s   ([_patch_stage2_openai] stub invocation count: 0)
```

Full suite:
```
python -m pytest -q
3141 passed, 3 skipped, 0 failed  (100.23s)
```

Same counts as step 6's baseline (3141/3/0) -- same 7 tests, now with
strengthened (value, not just structural) asserts on 4 of them. Zero
regressions, zero new/removed tests. The
`[_patch_stage2_openai] stub invocation count: 5` on the full run is the
same pre-existing count from other Stage-2 tests in the suite, unchanged
by this file.

## Not committed

Per constraint: `tests/infra/test_orchestrator_muhurta.py` remains
uncommitted in the working tree. Design chat ratifies this step's changes
before they're committed; step 7 (golden rows + dead `_KNOWN_GAPS`
deletion + baseline freeze) is still open.
