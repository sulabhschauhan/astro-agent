# Session 55: _calc_dasha() -- additive start_jd/end_jd keys (unblocks av_transit builder)

**Changed file:** `agent/chart_calculator.py` only, plus the benign
`diagnostics/calc_router_stage2.log` growth from running the suite. No
other file touched.

## Read-first: grep for exact key-set assertions on dasha dicts

Grepped `tests/` for `current_mahadasha|current_antardasha|
next_5_antardashas|next_3_mahadashas|current_pratyantar|
next_5_pratyantars` -- one hit: `tests/manual/dasha_timezone_check.py`.
Inspected it: it's a **standalone, non-pytest script** (filename doesn't
match pytest's `test_*.py`/`*_test.py` collection pattern, confirmed
against `pytest.ini`'s default `python_files` -- not collected by the
2943-test suite). Its only dasha-dict comparisons are `dasha_old ==
dasha_new` and `sulabh["dasha"] == dasha_new`, both sides produced by the
SAME `_ser()` code path -- adding two keys to both sides equally does not
break either comparison.

Also grepped for generic exact-key-set patterns (`set(...keys()) ==`,
literal-dict equality) across all of `tests/` -- none target the dasha
period dicts (`lord`/`start`/`end`). Full hit list reviewed; all are
unrelated modules (ashtakoot tables, shadbala, bhava_bala, combustion,
etc.).

**Conclusion: no test asserts an exact key set on `_calc_dasha()`'s
serialized period dicts.** Safe to add keys additively.

## Change

1. New private helper `_to_jd(d: datetime) -> float`, next to `_fmt()`:
   converts to UTC first (`d.astimezone(timezone.utc)`), then
   `swe.julday(y, m, day, hour + min/60 + sec/3600)` -- same
   datetime->JD path as `orchestrator.py`'s `evaluated_at_jd` capture
   (verified by reading that code: `datetime.now(timezone.utc)` ->
   hour-decimal -> `swe.julday()`), not a new conversion convention.
2. `_ser()` (inside `_calc_dasha()`) extended with two additive keys:
   `"start_jd": _to_jd(d["start"])`, `"end_jd": _to_jd(d["end"])`.
   Existing `"lord"`/`"start"`/`"end"` string keys unchanged,
   byte-for-byte (confirmed via smoke check below).
3. `_ser()` is unchanged in every other respect -- it already applies
   uniformly to mahadasha, antardasha, next-N lists, and pratyantars, so
   all of those now carry `start_jd`/`end_jd` too, as intended (nothing
   else needed to change).
4. `_calc_dasha()` docstring extended with a Session 55 note: JD keys
   added for the av_transit convergence layer (chart_profile.py needs a
   float envelope; the string form is render-only), and the documented
   ±37-day drift note applies identically to the JD keys (same
   underlying timeline).

**Manual smoke check** (ad hoc, not a test file) on Sulabh's live chart:
```
current_antardasha = {'lord': 'Venus', 'start': '28 Dec 2025', 'end': '28 Feb 2027',
                       'start_jd': 2461038.15..., 'end_jd': 2461464.27...}
```
`swe.revjul()` round-trip on both JDs lands on the correct dates (UT-day
vs. local-day boundary shift observed is expected given the +5:30 IST
offset, consistent with `_to_jd()`'s UTC-first conversion).

## Suite count

Full suite: `2943 passed, 3 skipped, 1 warning` -- **identical** to the
pre-change baseline. Zero delta, exactly as expected for a purely
additive change.

## Unblocks

This clears the Session 55 STOP from the previous task (`chart_profile.py`
av_transit builder): `current_dasha`'s Antardasha now has a JD float form
(`chart_data["dasha"]["current_antardasha"]["start_jd"/"end_jd"]`)
available for `build_domain_profile()` to read directly -- no parsing
dates back to JDs, no duplicate timeline computation needed.
