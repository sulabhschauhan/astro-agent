# Vimshottari Dasha Year-Length Constant — Diagnostic (Session 74)

**Status:** Diagnostic record. No production code touched by this file.
**Related:** `chart_calculator.py:_calc_dasha()` / `_add_years()` (read-only
this session). Mirrors `diagnostics/yogini_year_length_S72.md`'s method
exactly, applied to Vimshottari. Probe script used to produce this record
(`scripts/probe_vimshottari_year_length_S74.py`) was temporary and has
been deleted; not tracked in git.

---

## 1. Observation

`_calc_dasha()` uses a flat Julian year (365.25 days, via `_add_years()`)
for all Mahadasha/Antardasha/Pratyantar arithmetic. This is the same
convention the S72 Yogini diagnostic found to be measurably wrong for
the Yogini dasha system (JHora v8 uses the sidereal year, 365.256363d,
not Julian). This diagnostic reruns that same test against Vimshottari,
using the newly-appended 9-row JHora MD fixture
(`tests/fixtures/jhora_sulabh.md`, "Vimshottari Dasha (JHora v8, Sulabh)"
section).

**Flag raised before proceeding (Working Style #1):** the appended
fixture table's column headers read "Start (UT)"/"End (UT)" per the
instructing prompt. The values are byte-identical to this same file's
pre-existing (unlabeled) Section 3 "Vimsottari Maha Dasa" table. This
file's own Yogini section, and the S72 diagnostic that consumed it, both
established that JHora v8's GUI displays dasha timestamps in **local
birth-zone time (IST, UT+5:30)**, not UT. Treating the new table's values
as literal UT (rather than IST) would introduce a systematic 5.5-hour
(~0.229-day) offset into every delta measurement below. This diagnostic
therefore parses the fixture as **IST**, consistent with the rest of the
file and with S72's own convention, and flags the header text as a likely
mislabeling rather than silently complying with it. See section 4 for a
quantification of how much this choice matters to the conclusions (it
does not change the compounding-mechanism finding, but it is a
non-negligible fraction of the fixed-offset finding).

Birth inputs used (verified against `calculate_chart("Sulabh", "6 April
1988", "00:30", "Calcutta, India")`):
- `birth_jd_ut = 2447257.291667`
- `birth_local = 1988-04-06T00:30:00+05:30`
- Natal Moon sidereal longitude (independently computed via
  `helpers/ephemeris.sidereal_longitude()`): `212.23199465°`
- Nakshatra: Vishakha (index 15), lord Jupiter — matches
  `chart_calculator.calculate_chart()`'s own reported nakshatra/pada/lord
  exactly, and matches the S72 diagnostic's independently-computed value
  (212.23199900092°) to 5 decimal places.

## 2. Drift table (Julian year, 365.25d)

Row-0 (Jup) `begin_jd` is skipped per the fixture note (JHora shows the
notional full-period start for a birth-straddling MD; `_calc_dasha()`'s
period 1 is birth-anchored by design, same divergence class as Yogini's
row-0). All 9 rows' `end_jd` are compared.

| Row | Lord | Computed end_jd | JHora end_jd | Delta (days) | Elapsed yrs from birth |
|---|---|---|---|---|---|
| 0 | Jupiter | 2447740.008403 | 2447735.756910 | +4.2515 | 1.3100 |
| 1 | Saturn  | 2454679.758403 | 2454675.625405 | +4.1330 | 20.3103 |
| 2 | Mercury | 2460889.008403 | 2460884.975787 | +4.0326 | 37.3106 |
| 3 | Ketu    | 2463445.758403 | 2463441.776296 | +3.9821 | 44.3107 |
| 4 | Venus   | 2470750.758403 | 2470746.897813 | +3.8606 | 64.3110 |
| 5 | Sun     | 2472942.258403 | 2472938.429201 | +3.8292 | 70.3111 |
| 6 | Moon    | 2476594.758403 | 2476590.995799 | +3.7626 | 80.3113 |
| 7 | Mars    | 2479151.508403 | 2479147.792014 | +3.7164 | 87.3114 |
| 8 | Rahu    | 2485726.008403 | 2485722.401111 | +3.6073 | 105.3117 |

## 3. Mechanism: compounding component

Regressing delta against elapsed years from birth:

    slope = -0.006195 days/elapsed-year
    intercept = +4.259987 days

This slope matches the S72 Yogini finding's magnitude closely
(S72: ≈ -0.0064 d/yr) and its sign (delta shrinks, i.e. becomes less
positive / more negative, as elapsed time grows — same direction as
Yogini's delta growing more negative over time). It is consistent with:

    365.256363 (sidereal year, days) - 365.25 (Julian year, days) = 0.006363

**Confirmed:** the S72 hypothesis holds for Vimshottari too — JHora v8's
Vimshottari Mahadasha engine adds sidereal years, not Julian years, per
period. Using 365.25 understates each period by ~0.006-0.0064 days per
year of duration, compounding additively across the forward-chained
sequence. Same mechanism, same magnitude, as the already-fixed Yogini
case.

## 4. Row-1 fixed offset (natal Moon precision) — DOES NOT MATCH S72

Isolating the non-compounding component (row 0's delta, before any
compounding has accrued): **+4.2515 days** (Julian) / **+4.2599 days**
(sidereal, see section 5) — both hypotheses agree closely on this
baseline value, as expected (the offset originates in the balance-at-
birth calculation, before year-length choice has had time to matter).

**This does NOT match the S72 Yogini fixed offset (≈ -0.68d) in either
magnitude or sign.** The instructing prompt's expectation — "Expect the
SAME offset here, since it's an ephemeris/ayanamsa property of the natal
chart, not of the dasha system" — is **falsified** by this measurement.

Investigation into why, using the same natal Moon longitude for both
systems (confirmed identical: `agent/calculations/dashas/yogini.py`'s
`fraction_traversed = (natal_moon_lon_sidereal - nak_start_deg) /
nak_span_deg` is mathematically identical to `_calc_dasha()`'s
`elapsed_frac = (moon_lon % nak_size) / nak_size` — same Moon longitude,
same nakshatra span, same formula shape):

- **Magnitude:** Vimshottari's starting lord (Jupiter) carries a 16-year
  period; Yogini's starting lord for this chart (Dhanya/Jupiter, per
  `yogini.py`'s `_YOGINIS` table) carries a 3-year period. Since
  `balance_years = total_years * (1 - fraction_traversed)`, the SAME
  small ephemeris-driven error in `fraction_traversed` produces a
  balance-day error that scales with `total_years`. Naively scaling
  S72's -0.68d by (16/3) predicts ≈ -3.63d for Vimshottari — same order
  of magnitude as the +4.25d actually measured, but NOT a match, and
  critically:
- **Sign:** back-solving each system's `fraction_traversed` from its own
  measured offset (using each system's own `total_years` multiplier)
  shows JHora's *implied* Vimshottari fraction_traversed (≈0.91814) is
  LARGER than this codebase's computed value (0.917400) — JHora's engine
  appears to place the Moon further into Vishakha. But JHora's *implied*
  Yogini fraction_traversed, back-solved the same way from the S72 data,
  is ≈0.916773 — SMALLER than this codebase's value. Same natal Moon,
  same nominal formula, opposite-direction implied discrepancy in JHora's
  two separate dasha panels.
- **Conclusion:** the two JHora dasha engines (Vimshottari panel, Yogini
  panel) are not evidenced to share a single internally-consistent
  balance-at-birth calculation the way this codebase's two modules do.
  They are independent oracle black boxes; the "ephemeris precision is a
  natal-chart property, not a dasha-system property" framing assumes an
  implementation-sharing that has no supporting evidence here. The
  magnitude match (order-of-magnitude, ratio-scaled) is suggestive but
  the sign mismatch is not explained by ephemeris precision alone.
- **IST/UT labeling checked as an alternative explanation and ruled
  insufficient:** re-deriving row-0 delta under the (rejected, see
  section 1) literal-UT reading of the new fixture table shifts every
  JHora `end_jd` later by +0.229167d (5.5h), which would reduce the
  measured +4.2515d Julian offset to +4.0223d — still nowhere near
  -0.68d in sign or magnitude, and does not resolve the anomaly. The
  scaling argument above is the better-supported explanation, but is not
  fully dispositive.

**This is flagged as further investigation needed, per the instructing
prompt's own fallback clause, rather than asserted as a settled finding.**

## 5. Drift table (Sidereal year, 365.256363d)

| Row | Lord | Computed end_jd | JHora end_jd | Delta (days) | Elapsed yrs from birth |
|---|---|---|---|---|---|
| 0 | Jupiter | 2447740.016817 | 2447735.756910 | +4.2599 | 1.3100 |
| 1 | Saturn  | 2454679.887708 | 2454675.625405 | +4.2623 | 20.3103 |
| 2 | Mercury | 2460889.245880 | 2460884.975787 | +4.2701 | 37.3106 |
| 3 | Ketu    | 2463446.040428 | 2463441.776296 | +4.2641 | 44.3107 |
| 4 | Venus   | 2470751.167685 | 2470746.897813 | +4.2699 | 64.3110 |
| 5 | Sun     | 2472942.705856 | 2472938.429201 | +4.2767 | 70.3111 |
| 6 | Moon    | 2476595.269491 | 2476590.995799 | +4.2737 | 80.3113 |
| 7 | Mars    | 2479152.064028 | 2479147.792014 | +4.2720 | 87.3114 |
| 8 | Rahu    | 2485726.678565 | 2485722.401111 | +4.2775 | 105.3117 |

Regression: **slope = +0.000167 days/elapsed-year, intercept =
+4.260064 days**. Slope is flat within measurement noise (essentially
zero), confirming the sidereal-year swap eliminates the compounding
component here exactly as it did for Yogini. The residual +4.26d±0.02d
band across all 9 rows is the flat, non-compounding offset discussed in
section 4.

## 6. Recommendation (UNRATIFIED — for design-chat review)

- **Compounding mechanism:** the sidereal-year hypothesis is confirmed
  for Vimshottari, same as Yogini. Slope drops from -0.0062 d/yr to
  ~+0.0002 d/yr (flat) when 365.25 is swapped for 365.256363. This part
  of the finding is solid and mirrors S72's Yogini result closely.

- **Fixed offset:** does NOT match Yogini's -0.68d — it is +4.26d here,
  opposite sign, larger magnitude. Section 4's investigation found a
  plausible partial explanation (period-length scaling of a shared
  ephemeris-fraction source) but could not account for the sign flip.
  **This is the "residual has a different structure" case the
  instructing prompt itself calls out as a stop condition** — the
  residual is flat and constant (good), but its value contradicts the
  stated expectation in a way not yet fully explained.

- **Recommendation: do NOT authorize the year-length constant swap in
  `_calc_dasha`/`_add_years` in this session.** The compounding-fix case
  is as strong as Yogini's was, but shipping it alongside an
  unexplained 4.26-day fixed-offset anomaly — on a function with a much
  wider blast radius than the Yogini module (see section 7) — is
  premature. Recommend a follow-up probe specifically isolating: (a)
  whether JHora's Vimshottari and Yogini panels are known/documented to
  share an ephemeris engine internally (unlikely to be answerable
  without JHora source, but worth a literature check against PVR's
  book); (b) an independent second reference chart's Vimshottari MD1 to
  see whether the +4.26d offset's sign/magnitude is chart-specific or
  systematic.

- **If the fixed offset is eventually confirmed as a stable, chart-
  independent constant** (not yet shown here — only one chart tested),
  the ±37-day Antardasha drift envelope (CLAUDE.md Locked Decisions,
  `tests/fixtures/golden_qa_sulabh.py:391` `sulabh_dasha_q11`
  MISMATCH_ENVELOPE note) could in principle tighten to something like
  ±5-6 days at Mahadasha granularity post-fix (row-0 offset ~4.26d plus
  small residual noise) — but this number is NOT proposed as final here;
  it depends on resolving section 4's open question first, and on
  Antardasha-level testing (not run in this session — the instructing
  prompt scoped this diagnostic to the 9-row MD table only).

## 7. Carry-forward — blast radius for design chat to evaluate

**`_add_years()` call sites** (`chart_calculator.py:165`):
grep found exactly 3 call sites, all inside `_calc_dasha()` itself
(lines 524, 546, 571 — the Mahadasha loop, Antardasha loop, and
Pratyantar loop respectively). No other production module calls
`_add_years()`. One reference exists outside production code:
`tests/manual/dasha_timezone_check.py:130` (a manual/ad-hoc diagnostic
script, not part of the pytest-collected suite). **Conclusion: a
year-length change scoped to `_add_years()` itself would be naturally
narrow — it has no callers outside `_calc_dasha`'s own three loops.** No
parameterization or inlining is strictly required to avoid collateral
impact elsewhere, though design chat may still prefer inlining the
sidereal constant directly in `_calc_dasha` (matching `yogini.py`'s
module-local `_YOGINI_YEAR_DAYS` pattern) over changing the shared
helper, purely for naming/documentation clarity, not correctness.

**Downstream consumers of `_calc_dasha()`'s output** (`chart_data["dasha"]`,
i.e. `current_mahadasha`/`current_antardasha` and their `start`/`end`/
`start_jd`/`end_jd` fields) — grep-confirmed:
- `agent/infra/chart_profile.py` — builds the `current_dasha` domain
  payload (`dasha["current_mahadasha"]`/`dasha["current_antardasha"]`,
  lines ~397-406, ~816-824); also `av_transit`'s domain build requires
  `chart_data['dasha']['current_antardasha']` to be non-None (fail-closed
  guard, lines 389-406) — av_transit's own envelope arithmetic is
  Antardasha-anchored, so any Antardasha-boundary shift from a
  year-length fix propagates into av_transit's scan window too.
- `agent/infra/calc_router.py` — line 588 reads
  `(chart_data.get("dasha") or {}).get("current_antardasha")` directly
  (routing-time reference, not just payload construction).
- `agent/infra/result_formatter.py` — renders `current_dasha`'s
  mahadasha/antardasha start/end strings for display (line 522 reads
  `profile.payload["current_mahadasha"]`); carries the ±37-day drift
  language into its rendered output (multiple comments cross-referencing
  `current_dasha`'s drift framing for sade_sati/av_transit's own
  presentation, e.g. lines 575, 605, 647, 691, 748).
- `agent/interpretive/answer_renderer.py` — `_render_current_dasha()`
  (line 159) consumes the same payload for the T4 display surface.
- `agent/eval/golden_harness.py` — maps the `"dasha"` domain name to
  `"current_dasha"` (line 104); no direct date arithmetic, but the
  golden-row match/mismatch classification for `sulabh_dasha_q11`-q15
  depends on `_calc_dasha()`'s actual output values.
- **sade_sati:** no direct dependency found — `chart_profile.py`'s
  sade_sati branch (line 1051 comment: "sade_sati -- NO mahadasha/
  antardasha fields") explicitly does NOT read `_calc_dasha()`'s output;
  it has its own independent Saturn-transit calculation. Listed here to
  close the question, not because a dependency exists.
- **timing_enrichment blocks:** `_build_av_timing_block()` (referenced
  at `chart_profile.py` lines 776, 836) is the career/dasha-adjacent
  enrichment path; it is built from av_transit's own scan, not from
  `_calc_dasha()`'s timeline directly, but av_transit itself depends on
  `current_antardasha` (see av_transit bullet above) — so
  timing_enrichment inherits the dependency transitively, not directly.

**Golden fixture rows currently asserting MISMATCH_ENVELOPE under the
±37d note:** `tests/fixtures/golden_qa_sulabh.py` lines 13-18 document
the general policy ("AD-date mismatches... fall inside the documented
±37-day Antardasha cross-source drift envelope... tagged
MISMATCH_ENVELOPE, not MISMATCH"); `sulabh_dasha_q11` (line 391) is the
concrete row, with its own baseline-comparison note (lines 35-37) citing
an internally-inconsistent baseline AD calculation as a SEPARATE finding
(not affected by this diagnostic). A future constant swap would make
this row's ±37d framing stale and require it to be re-worded to whatever
tighter number design chat eventually ratifies — not done here.
