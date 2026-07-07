# P6 Jaimini: karakas.py four-chart oracle tests

**Task type:** new test file only (`tests/calculations/test_jaimini_karakas.py`).
`agent/calculations/jaimini/karakas.py` NOT touched — all 24 new tests
passed on first run, so no fix-forward was needed.

## Fixture provenance

JHora v8, Lahiri ayanamsa, Whole Sign, Mean Node, karaka-scheme
preference = 8. Captured Session 57 from JHora Body tables, transcribed
per the task prompt and used verbatim (not recomputed/corrected). Sign
DMS converted via a module-level `_dms_to_abs(sign, d, m, s)` helper
(bases Ar=0 ... Pi=330).

## Per-test-group summary (24 tests, 5 layers)

**Layer A — four-chart full-tuple oracle (4 tests):** David (hardest
case, tested first — Saturn/Sun/Rahu cluster spans only 48 arcmin of
advancement), Surbhi, Sheridan, Sulabh. Each asserts `result.karakas`
against the full 8-pair expected tuple, exact order, not sampled pairs.
All 4 matched the given oracle values exactly on first run.

**Layer B — PVR Ch.8 p.81 Table 14 (Example 28) numeric oracle
(2 tests):** karaka-assignment tuple (AK=Rahu … DK=Saturn, resolving the
"Venus"/"Saturn" OCR ambiguity in the printed table's last row toward
Saturn, per the task prompt) and the 8 advancement values via
`pytest.approx(abs=1/60)` — tolerance justified inline (PVR prints
arc-minute precision; scope-guarded to this test only, never smuggled
into Layer A's exact-tuple JHora asserts).

**Layer C — Rahu-reversal convention lock (4 parametrized tests, one per
chart):** asserts `result.advancement`'s Rahu entry equals the module's
own `30 - (longitude % 30)` formula on each chart's real Rahu longitude —
documented as a regression guard against a sign-flip/off-by-one bug, not
an external-oracle claim (Layer A already covers the oracle).

**Layer D — error-path contract (9 tests):** Ketu-present (message
mentions "moksha", not generic), missing key (names Saturn), extra key
(names Pluto), exact tie (Sun/Moon both forced to advancement 10.0 —
message names both and mentions "sthira"), Rahu-involved tie (Sun vs
Rahu both forced to advancement 10.0), and 4 range-guard cases from the
prior prompt's guard (negative, upper-boundary 360.0, NaN — each names
Sun; a combined two-planet case names both Sun and Moon). Tie-test
fixtures use a hand-verified `_NO_TIE_BASE` (8 distinct advancement
values, none colliding with the deliberately-forced 10.0) so only the
intended pair collides.

**Layer E — result-shape locks (5 tests):** `isinstance(result,
CharaKarakasResult)`, hashability (`hash(result)` does not raise),
`karakas` tuple length 8, karaka labels equal `("AK","AmK","BK","MK",
"PiK","PK","GK","DK")` in that exact order, and the 8 assigned planets
are a permutation of the 8 input keys.

## Test suite

```
2972 passed, 3 skipped, 0 failed
```

Baseline (pre-this-task) was 2948 passed / 3 skipped / 0 failed. Delta:
**+24 passed, 0 lost, 0 failed** — exactly the 24 new tests in this file,
zero regressions elsewhere. No deviation to report.
