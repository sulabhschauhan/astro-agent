# P7.2b — Sade Sati formatter render path

**Date:** 2026-07-05 (Session 50)
**Task source:** pasted prompt, "Session 50 — P7.2b"
**File touched:** `agent/infra/result_formatter.py` only. No
router/profile/test changes.

## Discovery before writing code

Read `result_formatter.py` first, per the contract. Found the task's
premise slightly off: the file has **no existing JD->date conversion of
its own** to mirror -- `_format_dasha()`'s mahadasha/antardasha
`start`/`end` strings arrive from `chart_profile.py` **already
pre-formatted** ("D Mon YYYY", `chart_calculator._fmt()`'s convention), so
this file never needed to convert a JD itself before P7.2a's `sade_sati`
payload (which carries raw JD floats). Resolved by treating "the file's
existing convention" as the project's established human-date STYLE ("D
Mon YYYY", day-level, no time-of-day) rather than a literal function to
reuse that doesn't exist here -- and sourcing the JD->datetime mechanics
from `panchanga.py`'s `_julian_day_ut_to_datetime` (`swe.revjul()` +
`timedelta`), this project's own existing precedent for that exact
conversion, rather than inventing a new one. New `_format_jd()` /
`_format_jd_or_unknown()` helpers added for this.

## What shipped

- `format_answer()`: added `if profile.domain == "sade_sati": return
  _format_sade_sati(profile)`, before the unknown-domain `ValueError`
  (unchanged, re-verified working).
- `_format_jd(jd_ut) -> str`: `swe.revjul()` + `timedelta` -> `"D Mon
  YYYY"`, matching `chart_calculator._fmt()`'s exact output shape.
- `_format_jd_or_unknown(jd_ut) -> str`: `None`-safe wrapper —
  `chart_profile.py`'s `sade_sati` payload uses `None` for a boundary
  genuinely not found within its ±40y scan window (not an error); renders
  the literal string `"not determinable within ±40y scan window"`
  (`_SADE_SATI_UNKNOWN_BOUNDARY`, tagged `SENSITIVE_TO
  chart_profile.py._SADE_SATI_ADJACENT_CYCLE_SCAN_YEARS`, not imported —
  same encapsulation precedent as the existing
  `_DASHA_DEMOTION_REASON` copied-verbatim comment).
- `_format_sade_sati(profile)`: always `TIER_1_EXACT`, always
  `demotion_reason=None` — no ±37-day-style drift language anywhere in
  this branch (payload carries no dated dasha claims). Renders all 4
  boundary fields through the `None`-safe helper regardless of `active`
  (chart_profile.py's own docstring says current-cycle fields are
  populated "if active" but doesn't *guarantee* it — rendering must not
  assume and must not crash if it's ever `active=True` with no macro
  envelope found). `sources=("sade_sati",)`, matching the
  `transits/sade_sati.py` module name (same style as
  `("vimshottari_dasha",)` for `current_dasha`).
  - `active=True` -> `phase` + `current_cycle_start`/`current_cycle_end`
    + `next_cycle_start`.
  - `active=False` -> `phase` ("NONE") + `previous_cycle_end` +
    `next_cycle_start`.

## Validation

End-to-end `build_domain_profile("sade_sati", ...) -> format_answer(...)`:

**Sulabh today (not active) — the actual q14 answer as it will ship:**
```python
DomainAnswer(
    domain='sade_sati',
    tier=AnswerTier.TIER_1_EXACT,
    answer_payload={
        'active': False,
        'phase': 'NONE',
        'next_cycle_start': '27 Jan 2041',
        'previous_cycle_end': '24 Jan 2020',
    },
    demotion_reason=None,
    sources=('sade_sati',),
    uncertainty_virupa=0.0,
    uncertainty_days=0.0,
)
```
Matches the golden q14 dates from P7.2a exactly.

**Active-cycle fixture** (`natal_moon_sign=0`, known-active JD): payload
correctly switches shape —
`{'active': True, 'phase': 'RISING', 'next_cycle_start': '14 May 2054',
'current_cycle_start': '29 Mar 2025', 'current_cycle_end': '30 May 2032'}`.

**Unknown-domain contract**: re-verified with a bogus `DomainChartProfile`
— still raises `ValueError: result_formatter: unknown domain 'bogus'`.

## Full suite

```
1786 passed, 3 skipped, 1 warning in 70.33s
```
Unchanged — `calc_router.py` still doesn't route to `sade_sati` (q14
still refuses via `_UNBUILT_MODULE_KEYWORDS`), so no existing test path
exercises this new branch.

## Explicitly not done (per task scope)

- No `calc_router.py`/`chart_profile.py`/test changes.
- No dedicated unit test file (not asked for this prompt; validated via
  direct smoke-test scripts, shown above).
