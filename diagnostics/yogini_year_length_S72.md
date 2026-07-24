# Yogini Dasha Year-Length Constant — Diagnostic (Session 72)

**Status:** Diagnostic record. No production code touched by this file.
**Related commit:** Yogini dasha module + unit tests (`agent/calculations/dashas/yogini.py`, `tests/test_yogini_dasha.py`), Session 72.

---

## 1. Observation

`compute_yogini_dasha()`'s first implementation used a birth-anchored
first period and a flat Julian year (365.25 days) for all period
durations, mirroring `chart_calculator.py`'s Vimshottari `_calc_dasha()`
convention. Running `tests/test_yogini_dasha.py::test_md_sequence_matches_jhora_fixture`
against the JHora v8 Yogini MD fixture (`tests/fixtures/jhora_sulabh.md`,
Sulabh chart) failed starting at row 11 (Sat, end 2039-07-07), with the
mismatch growing monotonically through row 23 -- not a single bad row,
but a smoothly compounding drift across the full 24-row sequence.

## 2. Drift table (Julian year, 365.25d, birth-anchored period 1)

Computed from the failing test run, before any fix. All times IST
(UT+5:30), matching `jhora_sulabh.md`'s existing convention.

| Row | Lord | Expected End (JHora fixture, IST) | Computed End (Julian 365.25, IST) | Delta (days) |
|---|---|---|---|---|
| 0 | Jup | 1988-07-06 05:11:16 | 1988-07-05 12:43:00 | -0.6863 |
| 1 | Mars | 1992-07-06 05:48:46 | 1992-07-05 12:43:00 | -0.7123 |
| 2 | Merc | 1997-07-06 12:35:37 | 1997-07-05 18:43:00 | -0.7449 |
| 3 | Sat | 2003-07-07 01:22:42 | 2003-07-06 06:43:00 | -0.7776 |
| 4 | Ven | 2010-07-06 20:30:11 | 2010-07-06 00:43:00 | -0.8244 |
| 5 | Rah | 2018-07-06 21:45:22 | 2018-07-06 00:43:00 | -0.8766 |
| 6 | Moon | 2019-07-07 03:44:13 | 2019-07-06 06:43:00 | -0.8758 |
| 7 | Sun | 2021-07-06 16:11:27 | 2021-07-05 18:43:00 | -0.8948 |
| 8 | Jup | 2024-07-06 10:34:45 | 2024-07-05 12:43:00 | -0.9109 |
| 9 | Mars | 2028-07-06 11:16:42 | 2028-07-05 12:43:00 | -0.9401 |
| 10 | Merc | 2033-07-06 17:52:12 | 2033-07-05 18:43:00 | -0.9647 |
| 11 | Sat | 2039-07-07 06:50:40 | 2039-07-06 06:43:00 | -1.0053 |
| 12 | Ven | 2046-07-07 01:45:16 | 2046-07-06 00:43:00 | -1.0432 |
| 13 | Rah | 2054-07-07 02:57:55 | 2054-07-06 00:43:00 | -1.0937 |
| 14 | Moon | 2055-07-07 09:08:31 | 2055-07-06 06:43:00 | -1.1010 |
| 15 | Sun | 2057-07-06 21:26:11 | 2057-07-05 18:43:00 | -1.1133 |
| 16 | Jup | 2060-07-06 15:57:24 | 2060-07-05 12:43:00 | -1.1350 |
| 17 | Mars | 2064-07-06 16:42:58 | 2064-07-05 12:43:00 | -1.1666 |
| 18 | Merc | 2069-07-06 23:19:56 | 2069-07-05 18:43:00 | -1.1923 |
| 19 | Sat | 2075-07-07 12:16:52 | 2075-07-06 06:43:00 | -1.2318 |
| 20 | Ven | 2082-07-07 07:07:01 | 2082-07-06 00:43:00 | -1.2667 |
| 21 | Rah | 2090-07-07 08:22:53 | 2090-07-06 00:43:00 | -1.3194 |
| 22 | Moon | 2091-07-07 14:35:59 | 2091-07-06 06:43:00 | -1.3285 |
| 23 | Sun | 2093-07-07 02:54:34 | 2093-07-05 18:43:00 | -1.3414 |

Birth inputs used: `birth_jd_ut = 2447257.291667`, natal Moon sidereal
longitude = `212.23199900092°` (Vishakha, nakshatra_number=16,
fraction_traversed=0.917400), via `calculate_chart("Sulabh", "6 Apr
1988", "00:30", "Calcutta, India")` + `ephemeris.sidereal_longitude()`.

## 3. Mechanism: compounding component

Regressing delta-from-row-0 against cumulative nominal years elapsed
gives a stable rate of approximately **-0.0064 days/year**, essentially
constant across the whole 24-row span (measured range: -0.0057 to
-0.0087 days/year, noise around a flat rate, not a trend). This value
matches, to within measurement precision:

    365.256363 (sidereal year, days) - 365.25 (Julian year, days) = 0.006363

**Conclusion:** JHora v8's Yogini Mahadasha engine adds sidereal years
(365.256363d) per period, not Julian years (365.25d). Using 365.25 for
Yogini period durations understates each period's length by ~0.0064
days per year of duration, and this error compounds additively across
the forward-chained MD sequence -- explaining why early rows (0-10)
stay within a ±1 day band while later rows (11-23) drift past it.

## 4. Row-0 fixed offset (~0.69d): a separate cause

Even at row 0 -- before any compounding has had a chance to
accumulate -- a fixed offset of roughly -0.69 days is already present
(see table above; the delta at row 0 is -0.6863, not ~0). This is NOT
explained by the year-length mechanism in section 3, which only
predicts *growth* over elapsed time, not a *baseline* offset present
immediately.

Root cause: natal Moon longitude ephemeris precision. Comparing this
module's independently-computed sidereal Moon longitude
(212.231999°) against JHora's own quoted panchanga value for Sulabh
(`tests/fixtures/jhora_sulabh.md`, Basics tab: `2 Sc 14' 52.28"` =
212.247856°) shows a ~57 arcsecond (0.0159°) discrepancy -- consistent
with, and the same root-cause class as, the already-documented
Vimshottari divergence in CLAUDE.md: "Known drift: ±37 days at
Antardasha level vs AstroSage... due to ephemeris precision difference
in Moon longitude. Not a bug." (Ayanamsa 23-40-39.08 rounding /
pyswisseph-vs-JHora Lahiri implementation variance.)

This offset originates once, in period 0's balance-at-birth
calculation (which is directly sensitive to natal Moon longitude
precision), and then propagates unchanged through the entire
forward-chained sequence -- every subsequent period's `begin_jd` is
the previous period's `end_jd`, so the fixed offset is carried forward
additively into all 24 rows, not just row 0. This was confirmed
empirically: after fixing the year-length mechanism (section 5), the
residual per-row delta was measured to be flat at approximately -0.67
to -0.69 days across ALL 24 rows (no longer growing with elapsed
time), not isolated to row 0 alone.

## 5. Decision (S72)

- Switch `_YOGINI_YEAR_DAYS` (module-local constant in
  `agent/calculations/dashas/yogini.py`, NOT shared with Vimshottari)
  from 365.25 to **365.256363** (sidereal year). This closes the
  compounding component described in section 3. Confirmed by
  re-measurement: post-fix per-row drift no longer grows with elapsed
  time (flat within measurement noise across all 24 rows).

- **Initial tolerance proposal, superseded within this same session:**
  Row 0 ±1.0 day, rows 1-23 ±0.25 day -- based on the assumption
  (section 4, before its last paragraph's confirmation) that the
  ephemeris-precision offset was isolated to row 0 only. Running the
  test with this split immediately falsified that assumption: row 1
  failed with a 0.685-day delta, far outside ±0.25. Re-measurement
  (the flat -0.67 to -0.69 day residual noted at the end of section 4)
  showed the offset propagates to every row via the forward-chained
  `begin_jd = previous end_jd` relationship, not just row 0.

- **Final, shipped decision:** a single uniform **±1.0 day** tolerance
  for `begin_jd` and `end_jd` across ALL 24 rows (row 0's `begin_jd` is
  not compared at all -- separate, unrelated reason: JHora displays the
  conceptual full period for a birth-straddling MD, while this module's
  period-1 `begin_jd` is intentionally birth-anchored, matching
  Vimshottari's `_calc_dasha()` convention). This is what
  `tests/test_yogini_dasha.py::test_md_sequence_matches_jhora_fixture`
  actually asserts as shipped; the row-0-only ±1.0d / rows-1-23 ±0.25d
  split above did not survive contact with the data and was corrected
  in the same session before landing.

## 6. Carry-forward

`chart_calculator.py`'s Vimshottari `_calc_dasha()` uses the Julian
year (365.25d) for all Mahadasha/Antardasha arithmetic -- the same
convention this diagnostic found to be measurably wrong for Yogini.
Vimshottari's own documented "±37 days at Antardasha level" drift
envelope (CLAUDE.md Locked Decisions) is wide enough to have hidden
this same class of error at the Antardasha granularity; it is likely
present, undetected, at the Mahadasha level too. This is flagged as a
**candidate bug**, not fixed here -- Vimshottari's year-length constant
is out of scope for the Yogini module and was explicitly left
untouched in this session (`_YOGINI_YEAR_DAYS` is a Yogini-local
constant, deliberately not shared with Vimshottari, so fixing one does
not silently change the other). Revisit in a dedicated Vimshottari
audit session.
