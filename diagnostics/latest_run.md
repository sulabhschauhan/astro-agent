# P7.2a — Sade Sati sub-path payload in chart_profile.py

**Date:** 2026-07-05 (Session 50)
**Task source:** pasted prompt, "Session 50 — P7.2a"
**File touched:** `agent/infra/chart_profile.py` only. No router/formatter/test changes.

## Design discovery during implementation (flagged and resolved with you mid-task)

Read `chart_profile.py` and `agent/calculations/transits/sade_sati.py` first,
per the contract. `compute_sade_sati()`'s public surface
(`SadeSatiStatus.macro_sade_sati`) only reports an envelope when the
*probed* JD itself falls inside that cycle's own `[start, end]` span — not
merely within its internal ±10y scan window. Verified empirically. This
breaks a naive "shift `evaluated_at_jd` by one Saturn period" approach for
finding the previous/next cycle whenever the chart is **not currently in
an active cycle** (confirmed always returns `None`, not just imprecise —
period-shifting a between-cycle point aliases back into the same gap).
Flagged this to you rather than shipping either a silently-broken
not-active fallback or an unvalidated invented scan. You directed a cheap
`find_state_segments()`-based scan reusing `helpers/discrete_scan.py`,
reimplementing Saturn's sign classifier directly (not calling
`compute_sade_sati()` per probe, which is ~0.8s/call and would make a
scan prohibitively slow).

## What shipped

- **`_VALID_DOMAINS`**: added `"sade_sati"`.
- **`_saturn_sidereal_sign(jd_ut)`** (new private helper): one
  `swe.calc_ut` call (~0.05ms), mirrors `sade_sati.py`'s private
  `_saturn_sign()` formula exactly (verified against its source before
  reimplementing — it's module-private, so not imported).
- **`_sade_sati_adjacent_cycle_boundaries(natal_moon_sign, evaluated_at_jd)`**
  (new private helper): scans Saturn sidereal-sign membership in
  `{rising, peak, setting}`-from-natal-Moon via
  `find_state_segments()` (imported from `agent.calculations.helpers.discrete_scan`)
  over `evaluated_at_jd ± 40 years`, 1-day step. Returns
  `(previous_cycle_end_jd, next_cycle_start_jd)`, each `None` if no
  adjacent cycle is found in range. Works uniformly whether or not
  `evaluated_at_jd` itself falls inside a currently-active cycle (a
  segment containing it is excluded from both searches by construction,
  since `find_state_segments`' `end_jd` is exclusive).
  - **Scan width (40y)**: justified by Saturn's ~29.4571y sidereal
    orbital period — guarantees >=1 full recurrence each direction with
    margin, regardless of where in the ~22y inter-cycle gap
    `evaluated_at_jd` falls. Scope guard: human-lifetime query horizon
    only. Revisit trigger: a real query needing a boundary >40y away.
  - **Scan step (1 day)**: matches `sade_sati.py`'s own `_find_segments()`
    daily-resolution precedent exactly (same state — Saturn sign
    membership), Session 20+ validated via Sheridan/Surbhi's real
    retrograde-double-ingress fixtures. Reused, not re-derived.
- **`build_domain_profile()`**: new `sade_sati` branch (replacing the
  final bare `else`, which is now `elif domain == "current_dasha"`).
  Calls `compute_sade_sati(natal_moon_sign, evaluated_at_jd)` once for
  `active`/`phase`/current-cycle boundaries (only populated when
  `active`), then `_sade_sati_adjacent_cycle_boundaries()` once for
  previous/next. `natal_moon_sign` resolved via
  `SIGNS.index(chart_data["lagna_chart"]["rasi"])` (same pattern already
  used by `_koota_natal_info_from_chart` above it, confirmed correct
  against a real chart: Sulabh -> Scorpio -> index 7, matching
  `test_muhurta_windows.py`'s own assertion).
- **Payload fields shipped** (exact names, for the formatter prompt):
  ```
  active: bool
  phase: str                        # "RISING" | "PEAK" | "SETTING" | "NONE"
  current_cycle_start_jd: float | None   # None unless active
  current_cycle_end_jd: float | None     # None unless active
  previous_cycle_end_jd: float | None
  next_cycle_start_jd: float | None
  ```
  NO mahadasha/antardasha fields anywhere in this payload.
- `uncertainty_virupa = 0.0`, `uncertainty_days = 0.0`, both with inline
  citation comments distinguishing "no envelope documented yet" from
  current_dasha's "verified +/-37-day drift" semantics — not conflated.
- `stub_caveats = ()` (no drik/dig/drishti stub involved in this domain).
- Docstrings updated: module header, `build_domain_profile`'s `Args`/
  `Raises` sections now mention `sade_sati` and its
  `compute_sade_sati` failure mode.
- Unknown-domain `ValueError` contract preserved and re-verified with the
  4th domain now in the sorted list.
- `try/except` wraps every new external call
  (`compute_sade_sati` x1, `_sade_sati_adjacent_cycle_boundaries` x1),
  each re-raising `RuntimeError` with a module-qualified message, matching
  this file's existing convention.

## Validation (hardest case first, per your instruction)

1. **Sulabh today, not active** (real chart via `calculate_chart`):
   `previous_cycle_end_jd` -> 24 Jan 2020 (04:27 UT), `next_cycle_start_jd`
   -> 27 Jan 2041 (21:42 UT) — both match your stated golden q14 verified
   values within ~1 day (well within, actually within hours).
2. **Active-cycle chart** (`natal_moon_sign=0`, the known-active fixture
   JD from `test_sade_sati.py`): scan-based previous/next matched the
   earlier (rejected) period-shift-anchor result to within ~0.02 days —
   cross-validated, then the period-shift path was dropped entirely per
   your "your call after measuring both" — single unified mechanism now
   used for both active and not-active cases.
3. **Wall-clock time**: ~2.2-2.5s end-to-end through
   `build_domain_profile()` (includes one `compute_sade_sati()` call
   ~0.8s + the ±40y/1-day scan ~1.4-1.5s). Not "well under 1s" as hoped,
   but the scan itself is ~1.45s in isolation — reported as measured, not
   adjusted after the fact.

## Full suite

```
1786 passed, 3 skipped, 1 warning in 74.56s
```
Unchanged from the P7.1c/P7.1e baseline — nothing routes to `sade_sati`
yet (calc_router.py untouched this session), so no existing test path
exercises this new branch.

## Explicitly not done (per task scope)

- No `calc_router.py`/formatter/test changes — this domain is not yet
  reachable from any question (q14 still refuses via
  `_UNBUILT_MODULE_KEYWORDS`, unchanged).
- No dedicated unit test file for the new branch (not asked for this
  prompt; validated via direct smoke-test scripts instead, documented
  above).
