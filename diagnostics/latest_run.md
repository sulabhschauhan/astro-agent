# P6 Jaimini: karakas.py input-range guard

**Task type:** surgical edit, one file (`agent/calculations/jaimini/karakas.py`).

Added an input-range validation pass to `compute_chara_karakas`, inserted
after the missing/extra-key check and before the advancement loop:

- For each of the 8 planets, rejects any longitude not satisfying
  `0.0 <= longitude < 360.0`.
- Uses the `not (0.0 <= lon < 360.0)` comparison form specifically so
  NaN is caught too (NaN relational comparisons are always False, so
  `0 <= nan < 360` is False and `not` flips it to True) — documented
  inline with a one-line comment, no separate `math.isnan()` check.
- Collects **all** out-of-range planets and reports them together in one
  `ValueError`, same style as the existing missing/extra-key message
  (not first-violation-only).
- Docstring `Raises` section updated to mention the new failure mode.

No other change: tie-break logic, karaka ordering, `CharaKarakasResult`
dataclass, and the module CITATION block are untouched.

## Manual verification (no persisted test file, per task scope)

- Lower boundary `0.0` accepted.
- Upper boundary `360.0` and a negative value (`-0.5`) both rejected in a
  single combined error, e.g.:
  `out-of-range value(s) [('Moon', -0.5), ('Sun', 360.0)]`
- `float('nan')` rejected with the same message shape.
- Re-ran the PVR Example 28 worked-example check (Ch.8 p.81, Table 14) —
  unaffected, still matches exactly.

## Test suite

```
2948 passed, 3 skipped, 0 failed
```

**Zero delta** from baseline. No deviation to report.
