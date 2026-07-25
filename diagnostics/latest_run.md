# S74 Vimshottari Year-Length Audit — Full Report

**Report type:** Read-only diagnostic (no production code touched).
**Related commit:** `60d054b` — "fixture: append JHora Vimshottari Sulabh
MDs (S74) / diagnostic: S74 Vimshottari year-length probe" (2 files:
`tests/fixtures/jhora_sulabh.md` append, `diagnostics/
vimshottari_year_length_S74.md` new). Not yet pushed to origin.
**Full detail:** `diagnostics/vimshottari_year_length_S74.md` (this file
is the chat-facing report; that file is the durable diagnostic record).
**Probe script:** `scripts/probe_vimshottari_year_length_S74.py` —
temporary, deleted before commit, never tracked in git.

---

## 0. What this audit did

Mirrored `diagnostics/yogini_year_length_S72.md`'s method exactly,
applied to `chart_calculator.py`'s Vimshottari `_calc_dasha()` /
`_add_years()` (both read-only this session; no source file edited).
Appended a 9-row JHora v8 Vimshottari Mahadasha fixture for Sulabh to
`tests/fixtures/jhora_sulabh.md`, wrote a temporary probe script that
reimplements `_calc_dasha()`'s balance-at-birth + forward-chain MD
arithmetic locally with `year_days` as a parameter (Julian 365.25 vs
sidereal 365.256363), compared against the fixture, and recorded the
result.

**Flag raised before proceeding (Working Style #1):** the appended
fixture table's column headers read "Start (UT)"/"End (UT)" per the
instructing prompt, but the values are byte-identical to this same
file's pre-existing (unlabeled) Section 3 "Vimsottari Maha Dasa" table.
This file's own Yogini section, and the S72 diagnostic that consumed
it, both established that JHora v8's GUI displays dasha timestamps in
**local birth-zone time (IST, UT+5:30)**, not UT. Treating the new
table's values as literal UT would introduce a systematic 5.5-hour
(~0.229-day) offset into every delta measurement. This audit parsed the
fixture as **IST**, consistent with the rest of the file, and flags the
header text as a likely mislabeling rather than silently complying with
it — quantified in section 4 below (does not change the compounding
finding; is a non-negligible fraction of the fixed-offset finding).

Birth inputs used (verified against `calculate_chart("Sulabh", "6 April
1988", "00:30", "Calcutta, India")`):
- `birth_jd_ut = 2447257.291667`
- `birth_local = 1988-04-06T00:30:00+05:30`
- Natal Moon sidereal longitude (independently computed via
  `helpers/ephemeris.sidereal_longitude()`): `212.23199465°` — matches
  the S72 diagnostic's independently-computed value
  (212.23199900092°) to 5 decimal places.
- Nakshatra: Vishakha (index 15), lord Jupiter — matches
  `chart_calculator.calculate_chart()`'s own reported nakshatra/pada/lord.

## 1. Drift table — Julian year (365.25d)

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

## 2. Drift table — Sidereal year (365.256363d)

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

## 3. Regressions (delta vs elapsed years from birth)

- **Julian (365.25d):** slope = **-0.006195 days/elapsed-year**,
  intercept = **+4.259987 days**.
- **Sidereal (365.256363d):** slope = **+0.000167 days/elapsed-year**
  (flat), intercept = **+4.260064 days**.

**Compounding mechanism CONFIRMED:** the Julian slope matches, in both
magnitude and sign-of-effect, S72's Yogini finding (≈ -0.0064 d/yr), and
is explained by the same arithmetic identity:

    365.256363 (sidereal year, days) - 365.25 (Julian year, days) = 0.006363

Switching to the sidereal year drops the slope to ~zero (flat), exactly
as it did for Yogini. **JHora v8's Vimshottari Mahadasha engine adds
sidereal years, not Julian years, per period — same mechanism, same
magnitude, as the already-fixed Yogini case.**

## 4. Row-1 fixed offset (natal Moon precision) — DOES NOT MATCH S72

Isolating the non-compounding component (row 0's delta, before any
compounding has accrued): **+4.2515 days** (Julian) / **+4.2599 days**
(sidereal) — both hypotheses agree closely on this baseline, as
expected (the offset originates in the balance-at-birth calculation,
before year-length choice has had time to matter).

**This does NOT match the S72 Yogini fixed offset (≈ -0.68d) in either
magnitude or sign.** The instructing prompt's stated expectation —
"Expect the SAME offset here, since it's an ephemeris/ayanamsa property
of the natal chart, not of the dasha system" — is **falsified** by this
measurement.

Investigation, using the same natal Moon longitude for both systems
(confirmed identical formula shape: `agent/calculations/dashas/
yogini.py`'s `fraction_traversed = (natal_moon_lon_sidereal -
nak_start_deg) / nak_span_deg` is mathematically identical to
`_calc_dasha()`'s `elapsed_frac = (moon_lon % nak_size) / nak_size`):

- **Magnitude:** Vimshottari's starting lord (Jupiter) carries a
  16-year period; Yogini's starting lord for this chart (Dhanya/
  Jupiter, per `yogini.py`'s `_YOGINIS` table) carries a 3-year period.
  Since `balance_years = total_years * (1 - fraction_traversed)`, the
  same small ephemeris-driven error in `fraction_traversed` produces a
  balance-day error that scales with `total_years`. Naively scaling
  S72's -0.68d by (16/3) predicts ≈ -3.63d — same order of magnitude as
  the +4.25d actually measured, but NOT a match.
- **Sign:** back-solving each system's `fraction_traversed` from its
  own measured offset shows JHora's *implied* Vimshottari fraction
  (≈0.91814) is LARGER than this codebase's computed value (0.917400).
  JHora's *implied* Yogini fraction, back-solved the same way from the
  S72 data, is ≈0.916773 — SMALLER than this codebase's value. Same
  natal Moon, same nominal formula, opposite-direction implied
  discrepancy in JHora's two separate dasha panels.
- **Conclusion:** the two JHora dasha engines (Vimshottari panel,
  Yogini panel) are not evidenced to share a single internally-
  consistent balance-at-birth calculation the way this codebase's two
  modules do. They are independent oracle black boxes; the "ephemeris
  precision is a natal-chart property, not a dasha-system property"
  framing assumes implementation-sharing that has no supporting
  evidence here.
- **IST/UT labeling checked and ruled insufficient as the explanation:**
  re-deriving row-0 delta under the (rejected) literal-UT reading of
  the fixture shifts every JHora `end_jd` later by +0.229167d (5.5h),
  reducing the measured +4.2515d Julian offset to +4.0223d — still
  nowhere near -0.68d in sign or magnitude.

**This is flagged as further investigation needed, per the instructing
prompt's own fallback clause, rather than asserted as a settled finding.**

## 5. Recommendation (UNRATIFIED — for design-chat review)

- **Compounding mechanism:** confirmed for Vimshottari, same as Yogini.
  Slope drops from -0.0062 d/yr to ~+0.0002 d/yr (flat) when 365.25 is
  swapped for 365.256363. Solid finding.
- **Fixed offset:** does NOT match Yogini's -0.68d — it is +4.26d here,
  opposite sign, larger magnitude, and only partially explained (period-
  length scaling predicts the right order of magnitude but the wrong
  sign). This is the "residual has a different structure" stop
  condition the instructing prompt itself calls out.
- **Recommendation: do NOT authorize the year-length constant swap in
  `_calc_dasha`/`_add_years` in this session.** The compounding-fix case
  is as strong as Yogini's was, but shipping it alongside an
  unexplained 4.26-day fixed-offset anomaly — on a function with a much
  wider blast radius than the Yogini module (section 6) — is premature.
  Recommend a follow-up probe: (a) check whether JHora's Vimshottari/
  Yogini panels are documented to share an ephemeris engine internally;
  (b) test a second reference chart's Vimshottari MD1 to see whether
  the +4.26d offset's sign/magnitude is chart-specific or systematic.
- **If** the fixed offset is eventually confirmed as a stable, chart-
  independent constant (not shown here — only one chart tested), the
  ±37-day Antardasha drift envelope (CLAUDE.md Locked Decisions,
  `tests/fixtures/golden_qa_sulabh.py:391` `sulabh_dasha_q11`
  MISMATCH_ENVELOPE note) could in principle tighten to roughly ±5-6
  days at Mahadasha granularity post-fix — not proposed as final; depends
  on resolving the sign anomaly first, and on Antardasha-level testing
  (out of scope this session — only the 9-row MD table was audited).

## 6. Carry-forward — blast radius for design chat to evaluate

**`_add_years()` call sites** (`chart_calculator.py:165`): exactly 3,
all inside `_calc_dasha()` itself (lines 524/546/571 — MD, AD, and
Pratyantar loops). No other production module calls it. One reference
outside production code: `tests/manual/dasha_timezone_check.py:130`
(manual script, not pytest-collected). **A year-length change scoped to
`_add_years()` would be naturally narrow** — no collateral callers.

**Downstream consumers of `_calc_dasha()`'s output**
(`chart_data["dasha"]`):
- `agent/infra/chart_profile.py` — builds the `current_dasha` domain
  payload; `av_transit`'s domain build fail-closed-requires
  `chart_data['dasha']['current_antardasha']` non-None, so Antardasha-
  boundary shifts propagate into av_transit's scan window.
- `agent/infra/calc_router.py:588` — reads
  `(chart_data.get("dasha") or {}).get("current_antardasha")` directly
  at routing time.
- `agent/infra/result_formatter.py` — renders current_dasha's
  mahadasha/antardasha strings; carries ±37-day drift language into
  sade_sati/av_transit's own presentation via cross-references.
- `agent/interpretive/answer_renderer.py:_render_current_dasha()` —
  T4 display surface.
- `agent/eval/golden_harness.py` — maps `"dasha"` domain name to
  `"current_dasha"`; `sulabh_dasha_q11`-q15's match/mismatch
  classification depends on `_calc_dasha()`'s actual output values.
- **sade_sati:** confirmed NO dependency (`chart_profile.py` line 1051
  comment: "sade_sati -- NO mahadasha/antardasha fields"; independent
  Saturn-transit calculation).
- **timing_enrichment:** inherits the dependency only transitively, via
  av_transit's own `current_antardasha` requirement, not directly.

**Golden fixture rows currently asserting MISMATCH_ENVELOPE under the
±37d note:** `sulabh_dasha_q11` (`tests/fixtures/golden_qa_sulabh.py:391`,
general policy at lines 13-18). Would go stale if the envelope tightens
in a future session — not edited here.

---
*Test suite:* not re-run — no source/test file touched this session
(read-only diagnostic; fixture append + new diagnostics file only).
