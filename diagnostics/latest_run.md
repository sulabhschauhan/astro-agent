# chart_calculator.py retrograde-flag fix (Session 51)

**Bug:** `_calc_planets()` omitted `swe.FLG_SPEED`, so `xx[3]` was hardcoded
0.0 and `retrograde` was always `False` for every planet, every chart.
**Fix:** added `swe.FLG_SPEED` to that call's flags (1-line, longitude-neutral).

## Retrograde map (before: all False everywhere)
- sulabh:   all direct.
- surbhi:   Saturn retro; rest direct.
- sheridan: Mars, Jupiter, Saturn retro; rest direct.
- david:    Mercury, Mars, Saturn retro; rest direct.

## Regression gate
`pytest tests/`: **1790 passed, 3 skipped** — identical to pre-fix baseline.
No test encoded the buggy always-False behavior.
