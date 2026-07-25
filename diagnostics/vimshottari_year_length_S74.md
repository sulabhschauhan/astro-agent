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

---

## §7. Multi-chart extension (S74 continuation)

Method: identical to §1-§5 above, reapplied to Surbhi/Sheridan/David.
Probe script `scripts/probe_vimshottari_multichart_S74.py` (temporary,
deleted before commit) reuses `DASHA_ORDER`/`DASHA_YEARS`/`NAKSHATRAS`/
`_NAK_LORDS`/`_nakshatra`/`resolve_timezone_offset` from
`agent/chart_calculator.py` and `sidereal_longitude` from
`helpers/ephemeris.py` — none redefined. As a self-check, the script was
first re-run against Sulabh: it reproduced the existing §2-§5 Julian/
Sidereal row-0 offsets to within 0.003d (+4.2496d vs the recorded
+4.2515d; +4.2580d vs +4.2599d) — the small residual traces to the
script's `sidereal_longitude()` call landing on a natal Moon longitude
that differs from §1's recorded value in the 5th decimal
(212.231999001° vs 212.23199465°), not a methodology divergence.
Confirms the forward-chain method itself is sound before trusting it on
new charts. Sulabh's own §1-§6 numbers are NOT overwritten by this
re-run; §8's Sulabh row below is the original, already-locked §3/§6
values, unchanged.

Row-0 `begin_jd` is skipped for every chart (birth-straddling convention
mismatch, same rule as §2). Fixture tables sourced from the newly
created `tests/fixtures/jhora_<name>.md` files (this session's Prompt 1),
parsed directly by the probe script — not retyped by hand.

### §7.1. Surbhi

Birth inputs: `Surbhi, "11 Sep 1992", "10:30", "Patna, India"` — verified
canonical at `tests/calculations/strength/test_drik_bala.py:221`
(`_CHART_ARGS["surbhi"]`), byte-identical to ~14 other call sites (e.g.
`tests/calculations/core/test_combustion.py:80`,
`tests/infra/test_orchestrator_e2e.py:82`).

`birth_jd_ut = 2448876.708333`, geocoded `lat=25.6093, lon=85.1235`,
natal Moon sidereal longitude `315.201430°` (Uttara Bhadrapada,
nakshatra #24 per `_nakshatra()`), starting Vimshottari lord Rahu
(18y period, remaining_frac=0.3599, balance ≈6.478y).

**Julian drift table (year_days=365.25):**

| Row | Lord | Computed end_jd | JHora end_jd | Delta (days) | Elapsed yrs |
|---|---|---|---|---|---|
| 0 | Rahu    | 2451242.823131 | 2451231.669352 | +11.1538 | 6.4781 |
| 1 | Jupiter | 2457086.823131 | 2457075.771377 | +11.0518 | 22.4781 |
| 2 | Saturn  | 2464026.573131 | 2464015.644549 | +10.9286 | 41.4781 |
| 3 | Mercury | 2470235.823131 | 2470225.000000 | +10.8231 | 58.4781 |
| 4 | Ketu    | 2472792.573131 | 2472781.801528 | +10.7716 | 65.4781 |
| 5 | Venus   | 2480097.573131 | 2480086.921736 | +10.6514 | 85.4781 |
| 6 | Sun     | 2482289.073131 | 2482278.465833 | +10.6073 | 91.4781 |
| 7 | Moon    | 2485941.573131 | 2485931.029479 | +10.5437 | 101.4781 |
| 8 | Mars    | 2488498.323131 | 2488487.823125 | +10.5000 | 108.4781 |

**Sidereal drift table (year_days=365.256363):**

| Row | Lord | Computed end_jd | JHora end_jd | Delta (days) | Elapsed yrs |
|---|---|---|---|---|---|
| 0 | Rahu    | 2451242.864351 | 2451231.669352 | +11.1950 | 6.4782 |
| 1 | Jupiter | 2457086.966159 | 2457075.771377 | +11.1948 | 22.4785 |
| 2 | Saturn  | 2464026.837056 | 2464015.644549 | +11.1925 | 41.4788 |
| 3 | Mercury | 2470236.195227 | 2470225.000000 | +11.1952 | 58.4791 |
| 4 | Ketu    | 2472792.989768 | 2472781.801528 | +11.1882 | 65.4792 |
| 5 | Venus   | 2480098.117028 | 2480086.921736 | +11.1953 | 85.4796 |
| 6 | Sun     | 2482289.655206 | 2482278.465833 | +11.1894 | 91.4797 |
| 7 | Moon    | 2485942.218836 | 2485931.029479 | +11.1894 | 101.4798 |
| 8 | Mars    | 2488499.013377 | 2488487.823125 | +11.1903 | 108.4800 |

Regressions: Julian slope = -0.006412 d/yr, intercept = +11.195416 d.
Sidereal slope = -0.000049 d/yr, intercept = +11.195416 d (flat,
compounding eliminated, same as Sulabh).

Row-0 fixed offset (Julian): **+11.1538 d** (Sidereal: +11.1950 d).

### §7.2. Sheridan

Birth inputs: `Sheridan, "27 May 1984", "08:00", "Durban, South Africa"`
— verified canonical at
`tests/calculations/strength/test_drik_bala.py:219` (`_CHART_ARGS["sheridan"]`),
byte-identical to ~12 other call sites (e.g.
`tests/calculations/strength/test_ishta_kashta.py:124`).

`birth_jd_ut = 2445847.75`, geocoded `lat=-29.8618, lon=31.0099`, natal
Moon sidereal longitude `2.159852°` (Ashwini, nakshatra #1), starting
Vimshottari lord Ketu (7y period, remaining_frac=0.8380, balance
≈5.866y).

**Julian drift table (year_days=365.25):**

| Row | Lord | Computed end_jd | JHora end_jd | Delta (days) | Elapsed yrs |
|---|---|---|---|---|---|
| 0 | Ketu    | 2447990.334813 | 2447986.534780 | +3.8000 | 5.8661 |
| 1 | Venus   | 2455295.334813 | 2455291.664838 | +3.6700 | 25.8661 |
| 2 | Sun     | 2457486.834813 | 2457483.200602 | +3.6342 | 31.8661 |
| 3 | Moon    | 2461139.334813 | 2461135.770301 | +3.5645 | 41.8661 |
| 4 | Mars    | 2463696.084813 | 2463692.555359 | +3.5295 | 48.8661 |
| 5 | Rahu    | 2470270.584813 | 2470267.173264 | +3.4115 | 66.8661 |
| 6 | Jupiter | 2476114.584813 | 2476111.270914 | +3.3139 | 82.8661 |
| 7 | Saturn  | 2483054.334813 | 2483051.149016 | +3.1858 | 101.8661 |
| 8 | Mercury | 2489263.584813 | 2489260.501435 | +3.0834 | 118.8661 |

**Sidereal drift table (year_days=365.256363):**

| Row | Lord | Computed end_jd | JHora end_jd | Delta (days) | Elapsed yrs |
|---|---|---|---|---|---|
| 0 | Ketu    | 2447990.372139 | 2447986.534780 | +3.8374 | 5.8662 |
| 1 | Venus   | 2455295.499399 | 2455291.664838 | +3.8346 | 25.8665 |
| 2 | Sun     | 2457487.037577 | 2457483.200602 | +3.8370 | 31.8666 |
| 3 | Moon    | 2461139.601207 | 2461135.770301 | +3.8309 | 41.8668 |
| 4 | Mars    | 2463696.395748 | 2463692.555359 | +3.8404 | 48.8669 |
| 5 | Rahu    | 2470271.010282 | 2470267.173264 | +3.8370 | 66.8672 |
| 6 | Jupiter | 2476115.112090 | 2476111.270914 | +3.8412 | 82.8675 |
| 7 | Saturn  | 2483054.982987 | 2483051.149016 | +3.8340 | 101.8679 |
| 8 | Mercury | 2489264.341158 | 2489260.501435 | +3.8397 | 118.8681 |

Regressions: Julian slope = -0.006339 d/yr, intercept = +3.835507 d.
Sidereal slope = +0.000024 d/yr, intercept = +3.835507 d (flat).

Row-0 fixed offset (Julian): **+3.8000 d** (Sidereal: +3.8374 d).

### §7.3. David

Birth inputs: `David, "19 Jan 1976", "22:00", "London, UK"` — verified
canonical at `tests/calculations/strength/test_drik_bala.py:222`
(`_CHART_ARGS["david"]`), byte-identical to ~14 other call sites (e.g.
`tests/calculations/core/test_combustion.py:66`,
`tests/calculations/helpers/test_ephemeris.py:46`). London's UTC offset
is DST-variable (BST/GMT) unlike the other 3 charts' fixed-offset zones
— the probe script resolves each fixture timestamp's offset individually
via `resolve_timezone_offset(lat, lon, naive_dt)` (imported, not
reimplemented) rather than assuming a fixed UT+0 or UT+1, so each MD
boundary's local→UT conversion is historically DST-correct.

`birth_jd_ut = 2442797.416667`, geocoded `lat=51.5074, lon=-0.1278`,
natal Moon sidereal longitude `131.657906°` (Magha, nakshatra #10),
starting Vimshottari lord Ketu (7y period, remaining_frac=0.1256,
balance ≈0.880y).

**Julian drift table (year_days=365.25):**

| Row | Lord | Computed end_jd | JHora end_jd | Delta (days) | Elapsed yrs |
|---|---|---|---|---|---|
| 0 | Ketu    | 2443118.690352 | 2443117.223565 | +1.4668 | 0.8796 |
| 1 | Venus   | 2450423.690352 | 2450422.353785 | +1.3366 | 20.8796 |
| 2 | Sun     | 2452615.190352 | 2452613.890278 | +1.3001 | 26.8796 |
| 3 | Moon    | 2456267.690352 | 2456266.455162 | +1.2352 | 36.8796 |
| 4 | Mars    | 2458824.440352 | 2458823.250671 | +1.1897 | 43.8796 |
| 5 | Rahu    | 2465398.940352 | 2465397.865903 | +1.0744 | 61.8796 |
| 6 | Jupiter | 2471242.940352 | 2471241.966678 | +0.9737 | 77.8796 |
| 7 | Saturn  | 2478182.690352 | 2478181.841644 | +0.8487 | 96.8796 |
| 8 | Mercury | 2484391.940352 | 2484391.193762 | +0.7466 | 113.8796 |

**Sidereal drift table (year_days=365.256363):**

| Row | Lord | Computed end_jd | JHora end_jd | Delta (days) | Elapsed yrs |
|---|---|---|---|---|---|
| 0 | Ketu    | 2443118.695949 | 2443117.223565 | +1.4724 | 0.8796 |
| 1 | Venus   | 2450423.823209 | 2450422.353785 | +1.4694 | 20.8800 |
| 2 | Sun     | 2452615.361387 | 2452613.890278 | +1.4711 | 26.8801 |
| 3 | Moon    | 2456267.925017 | 2456266.455162 | +1.4699 | 36.8802 |
| 4 | Mars    | 2458824.719558 | 2458823.250671 | +1.4689 | 43.8804 |
| 5 | Rahu    | 2465399.334092 | 2465397.865903 | +1.4682 | 61.8807 |
| 6 | Jupiter | 2471243.435900 | 2471241.966678 | +1.4692 | 77.8810 |
| 7 | Saturn  | 2478183.306797 | 2478181.841644 | +1.4652 | 96.8813 |
| 8 | Mercury | 2484392.664968 | 2484391.193762 | +1.4712 | 113.8816 |

Regressions: Julian slope = -0.006390 d/yr, intercept = +1.470911 d.
Sidereal slope = -0.000027 d/yr, intercept = +1.470911 d (flat).

Row-0 fixed offset (Julian): **+1.4668 d** (Sidereal: +1.4724 d).

## §8. Multi-chart summary

| Chart    | Julian slope | Sidereal slope | Row-0 offset (Julian) | Row-0 offset (Sidereal) |
|---|---|---|---|---|
| Sulabh   | -0.0062      | +0.0002        | +4.2515               | +4.2599                 |
| Surbhi   | -0.0064      | -0.00005       | +11.1538              | +11.1950                |
| Sheridan | -0.0063      | +0.00002       | +3.8000               | +3.8374                 |
| David    | -0.0064      | -0.00003       | +1.4668               | +1.4724                 |

**Axis 1 — compounding mechanism:** Julian→Sidereal is a slope-flattening
move for ALL 4 charts, no exceptions. Julian slopes cluster tightly at
-0.0062 to -0.0064 d/yr across all 4 (the -0.006363 = 365.256363 -
365.25 signature, same as §3's finding); sidereal slopes drop to
±0.00005 d/yr or smaller (essentially measurement noise) for all 4. This
part of the S74-Prompt-1 finding generalizes cleanly — it is chart-
independent.

**Axis 2 — Row-0 fixed offset structure:** all 4 signs are POSITIVE
(uniform), ruling out the "mixed signs" half of verdict (c) on its own.
But magnitude does NOT cluster near a single band the way axis 1's
slopes do — it ranges from +1.4668d (David) to +11.1538d (Surbhi), a
~7.6x spread, so verdict (a) ("same sign and close magnitude") is
falsified by this data.

Verdict (b) ("magnitude scales with a chart property") was tested
against every candidate property available from this probe, per §4's
own scaling hypothesis (offset ∝ starting lord's `total_years`, since
`balance_years = total_years * (1 - fraction_traversed)` and the offset
is theorized to originate in a `fraction_traversed` ephemeris-precision
delta):

- **Starting lord `total_years` alone:** Sheridan and David share the
  IDENTICAL starting lord (Ketu, 7y total period) — if offset scaled
  with `total_years` alone, they should show similar offsets. They do
  not: +3.8000d vs +1.4668d, a 2.6x difference on the same total_years
  value. This single comparison falsifies "`total_years` alone" as a
  sufficient explanatory variable.
- **`balance_years` (period-0's actual duration, `total_years *
  remaining_frac`):** Sulabh 1.32y→4.25d, Surbhi 6.48y→11.15d, Sheridan
  5.87y→3.80d, David 0.88y→1.47d. Offset/balance_years ratio: 3.22,
  1.72, 0.65, 1.67 respectively — no consistent ratio.
- **`elapsed_frac` (nakshatra-fraction traversed at birth):** Sulabh
  0.917→4.25d, David 0.874→1.47d — similar `elapsed_frac`, ~2.9x
  different offset. No clean fit.
- **Birth epoch:** birth years 1976 (David, smallest offset)/1984
  (Sheridan)/1988 (Sulabh)/1992 (Surbhi, largest offset) are not
  monotonic with offset magnitude either (David earliest, smallest;
  Surbhi latest of the four, largest — but Sheridan/Sulabh don't fall
  in between in date order the way their offsets do).

None of the single-variable candidates checked here produce a clean
scaling fit. **Verdict: (c) — high variance, unresolved.** Not "mixed
signs" (all 4 are positive), but the magnitude spread and the falsified
Ketu/Ketu same-total_years comparison mean no mechanism from this
4-chart sample explains the row-0 offset's size. Per the instructing
prompt's own criterion, this is called as measured, not rationalized
toward (a) or (b) despite the uniform sign being suggestive.

## §9. Yogini formula cross-check (informational)

| Chart    | Nakshatra # | Formula (n+2)%8 | Predicted lord | JHora row-1 lord | Match? |
|---|---|---|---|---|---|
| Sulabh   | 16          | 2               | Jupiter        | Jupiter          | ✓      |
| Surbhi   | 24          | 2               | Jupiter        | Jupiter          | ✓      |
| Sheridan | 1           | 3               | Mars           | Mars             | ✓      |
| David    | 10          | 4               | Mercury        | Mercury          | ✓      |

All 4 charts PASS. Predicted lord was read directly from
`compute_yogini_dasha()`'s own `periods[0].lord` (the module's public
entry point) — not from a reimplemented formula; `nakshatra_number` and
`(n+2)%8` are reported alongside for audit-trail purposes only, derived
via the same `_nakshatra()` helper the module itself calls internally.

Per the instructing prompt: all 4 pass → the `(nakshatra_number + 2) %
8` starting-lord formula in `agent/calculations/dashas/yogini.py` is
validated across the full 4-chart reference set. The 3 xfails in
`tests/test_yogini_dasha.py` (`test_starting_lord_surbhi/sheridan/david`)
are candidates to flip in a future S74 prompt — NOT done here, per the
instructing prompt's explicit scope limit.

## §10. Revised recommendation for design-chat review

Multi-chart evidence CONFIRMS axis 1 (compounding mechanism — the
sidereal-year swap flattens drift slope from ≈-0.0064 d/yr to ≈0 for
all 4 charts, chart-independent) but does NOT resolve axis 2 (row-0
fixed offset — same sign across all 4, but magnitude varies 7.6x with
no mechanism found among the candidates tested, verdict (c)).

Per the instructing prompt's own decision framework, verdict (c) means:
**recommendation UNCHANGED from the existing §6 Recommendation above —
do NOT authorize the year-length constant swap in `_calc_dasha`/
`_add_years` yet.** (Note: the instructing prompt for this diagnostic
refers to "§5" for the prior recommendation; this file's actual
recommendation section is numbered §6 — the multi-chart evidence above
is assessed against §6's content, not a renumbering of this file.) The
compounding-fix case is now stronger (4-chart-confirmed, not
1-chart), but shipping it alongside a still-unexplained, non-constant
row-0 offset is premature — same rationale as §6, now with broader
(and more puzzling) supporting data rather than resolving evidence.

Follow-up candidates for a future dedicated session (not started here):
isolate whether the offset correlates with a property NOT tested above
(e.g. natal Moon's exact ecliptic latitude, ayanamsa-rounding behavior
specific to JHora's engine, or the interaction between `elapsed_frac`
and `total_years` as a two-variable model rather than either alone);
Antardasha-level drift was not probed for the 3 new charts (same scope
limit as §6's own note).

---

## §11. pyjhora source audit

### Path + confirmation

`PyJHora-main/` (repo root). Confirmed a real, substantial Python port
of PVR Narasimha Rao's *Vedic Astrology — An Integrated Approach* and
JHora v8.0 software — not a stub. `PyJHora-main/README.md`: "Python
package containing almost all the features described in the book...
and the free astrology software Jagannatha Hora V8.0 software by the
same author... There is a test module (`jhora.tests.pvr_tests`)
containing about 6800 tests." Vimshottari lives at
`PyJHora-main/src/jhora/horoscope/dhasa/graha/vimsottari.py`; Yogini at
`.../graha/yogini.py`. Running it required stubbing the optional
`geocoder` import (unused by this probe — no internet geocoding, lat/
lon supplied directly) via `sys.modules` injection in a temporary
scratch script; `PyQt6` (GUI-only) was never imported by the code paths
exercised. No pyjhora source file was modified.

### Mechanism side-by-side table

| Aspect | Our code (file:line) | pyjhora (file:line) | Match? |
|---|---|---|---|
| Moon longitude | `agent/chart_calculator.py:651` (`swe.set_sid_mode(swe.SIDM_LAHIRI)`) + `agent/calculations/helpers/ephemeris.py:83-102` (`sidereal_longitude`, `swe.calc_ut`) | `vimsottari.py:62-69` (`vimsottari_dasha_start_date` calls `charts.get_chart_element_longitude`) → `charts.py:2544-2553` → `drik.py:304-330` (`sidereal_longitude`, `swe.calc_ut`) | **MATCH** — same pyswisseph engine, same call shape (`FLG_SWIEPH\|FLG_SIDEREAL`-class flags) |
| Ayanamsa flag | `swe.SIDM_LAHIRI` hardcoded (`agent/chart_calculator.py:651`, `helpers/ephemeris.py:94`) | `swe.SIDM_LAHIRI`, same swisseph constant, mapped from the string key `"LAHIRI"` (`const.py:284`) via `drik.py:204-234` `set_ayanamsa_mode()` — **but pyjhora's own package-level default is `_DEFAULT_AYANAMSA_MODE = 'TRUE_PUSHYA'`, NOT Lahiri** (`const.py:296`; the vendored `README.md` itself warns "tests assume `const._DEFAULT_AYANAMSA_MODE='LAHIRI'`", i.e. callers must opt in). This audit explicitly called `drik.set_ayanamsa_mode("LAHIRI")` before every computation below to match the fixture's stated ayanamsa. | **MATCH once forced** — identical swisseph constant (`SIDM_LAHIRI`, value `1`, confirmed by direct print), but NOT the library's out-of-box behavior |
| fraction calc | `agent/chart_calculator.py:509-515` (`elapsed_frac = (moon_lon % nak_size) / nak_size`) | `vimsottari.py:70-76` (`rem = planet_long - nak*one_star; period_elapsed = rem/one_star*period`) | **MATCH** — `rem/one_star` is algebraically identical to `elapsed_frac`; nakshatra→lord mapping also verified identical (pyjhora's `vimsottari_adhipati_list = [8,5,0,1,2,7,4,6,3]` indexed by `nak % 9` with `seed_star=3` reduces to the same Ketu-first 9-cycle our `_NAK_LORDS` table encodes) |
| year constant | Fixed `365.25` (Julian), `agent/chart_calculator.py:165-166` (`_add_years`) | **NOT a fixed constant.** `drik.py:4399-4418` `dhasa_year_duration()`; default `dhasa_duration_type` is `const.dhasa_year_duration_default = DHASA_YEAR_DURATION.JHORA_DEFAULT = TRUE_SIDEREAL_YEAR` (`const.py:1640-1650`). `TRUE_SIDEREAL_YEAR` calls `true_sidereal_year(jd, place)` (`drik.py:4074-4081`): the actual measured duration between the Sun's previous and next sidereal-Aries ingress bracketing the birth `jd` — a genuinely per-chart, per-epoch COMPUTED value, not `365.25` or `365.256363`. Measured for our 4 charts: Sulabh 365.260928d, Surbhi 365.262224d, Sheridan 365.260820d, David 365.256936d (all in the 365.2569-365.2622d range — close to but NOT equal to either of §2/§5's two fixed hypotheses). | **MISMATCH** on both sides of our A/B test — pyjhora uses neither our Julian (365.25) nor our sidereal (365.256363) hypothesis; it uses a third, chart-specific, non-constant quantity |
| Yogini shares? | **NO** — `agent/chart_calculator.py`'s `_calc_dasha()` (Vimshottari) and `agent/calculations/dashas/yogini.py`'s `compute_yogini_dasha()` are independent modules with independently-chosen year constants (`_add_years`'s `365.25` vs `yogini.py:17`'s `_YOGINI_YEAR_DAYS = 365.256363`) | **YES** — `yogini.py:71-96` `_dhasa_start()` is the same formula shape as `vimsottari.py:52-78` `vimsottari_dasha_start_date()` (`rem/one_star*period` balance calc, `jd - period_elapsed` start), both call the identical `charts.get_chart_element_longitude()` for Moon longitude and the identical `drik.dhasa_year_duration()` for year length (`yogini.py:131-136` mirrors `vimsottari.py:196-201` exactly) | **REFUTES §4's "two independent black boxes" hypothesis — but only as a statement about pyjhora's own implementation choice**, not proof the actual closed-source JHora v8 GUI shares an engine internally (see next section: pyjhora's own numbers don't match the GUI fixture either, so pyjhora cannot settle what the GUI itself does) |

### Sulabh row-0 hand-computation

Computed via pyjhora's actual public entry point (`vimsottari.get_vimsottari_dhasa_bhukthi(jd_local, place, dhasa_level_index=MAHA_DHASA_ONLY)` — the same API level a GUI-equivalent caller would use), ayanamsa forced to LAHIRI, birth inputs from `tests/calculations/strength/test_drik_bala.py:220` (`_CHART_ARGS["sulabh"]`). pyjhora's own JD convention treats the supplied `jd` as "local wall-clock, not yet UT-shifted" (confirmed via `utils.julian_day_number()`'s body, `utils.py:727-738`, and `sidereal_longitude()`'s own docstring, `drik.py:304-315`: "`JD_UTC = JD - Place.TimeZoneInFloatHours`"); pyjhora's emitted `(Y,M,D,fh)` result tuples are therefore genuinely LOCAL and were converted to true `JD_UT` the same way this session's other probe scripts do (`swe.julday(...) - tz_hours/24`) before comparison.

| Source | Sulabh MD1 (Jupiter) end, JD_UT |
|---|---|
| Our code (Julian, 365.25) | 2447740.008403 |
| Our code (sidereal, 365.256363) | 2447740.016817 |
| **pyjhora** (`get_vimsottari_dhasa_bhukthi`, ayanamsa forced LAHIRI) | **2447739.906249** |
| JHora v8 GUI fixture (`tests/fixtures/jhora_sulabh.md`) | 2447735.756910 |

Deltas: pyjhora − our code (Julian) = **−0.102154 d** (≈2h27m). pyjhora −
GUI fixture = **+4.149339 d**. pyjhora's computed value is ~41x closer
to OUR code's output than to the actual JHora GUI fixture.

**This is section 4's second, "surprising" branch, not the first**:
pyjhora's computed value does NOT match the JHora GUI to within
seconds — it reproduces almost exactly our own code's answer instead
(same order of magnitude as our own code's ±minutes-to-hours internal
noise, not the GUI's multi-day gap). The same pattern holds across all
4 charts (all deltas in true JD_UT, all ayanamsa forced LAHIRI):

| Chart | pyjhora end_jd | Our code (Julian) end_jd | GUI fixture end_jd | \|pyjhora−ours\| | \|pyjhora−GUI\| |
|---|---|---|---|---|---|
| Sulabh | 2447739.906249 | 2447740.008403 | 2447735.756910 | 0.102154 | 4.149339 |
| Surbhi | 2451242.684424 | 2451242.823131 | 2451231.669352 | 0.138707 | 11.015072 |
| Sheridan | 2447990.315859 | 2447990.334813 | 2447986.534780 | 0.018954 | 3.781079 |
| David | 2443118.688018 | 2443118.690352 | 2443117.223565 | 0.002334 | 1.464453 |

Every chart: pyjhora is 27x-627x closer to our own `_calc_dasha()`
output than to the actual JHora v8 GUI fixture. **Conclusion: pyjhora
is NOT a faithful stand-in for the closed-source JHora v8 GUI's actual
Vimshottari balance-at-birth engine, at this sub-day granularity.**
Whatever the compiled GUI application does internally to produce our
fixture's numbers, this open-source port — despite matching Moon-
longitude pipeline, nakshatra-lord mapping, and balance formula SHAPE
almost exactly — does not reproduce it. The remaining gap is not
explained by algorithm shape or year-length convention (both checked
and ruled out as the dominant driver above); it must originate
somewhere neither codebase currently models.

### A candidate mechanism, partially confirmed: ayanamsa-epoch mismatch

`tests/fixtures/jhora_sulabh.md`'s own Panchanga capture (Session 27,
directly from the JHora GUI's Basics tab, not a template value) records
`Ayanamsa | 23-40-39.08` — i.e. **23.677522°** — at Sulabh's birth
moment. Our own code's independently-computed ayanamsha at the same
`jd_ut` (`agent/chart_calculator.py`'s `meta.ayanamsha_lahiri`, verified
directly: `calculate_chart("Sulabh", ...)['meta']['ayanamsha_lahiri']
== 23.6931`) — and pyjhora's `swe.get_ayanamsa_ut()` call under
`SIDM_LAHIRI` at the identical `jd_ut` — both give **23.693114°**
(same pyswisseph engine, same mode, same `jd`; this equality is
expected, not a new finding). **The JHora v8 GUI's own displayed Lahiri
ayanamsa differs from pyswisseph's `SIDM_LAHIRI` value at the same
instant by +0.015592° (+0.9355 arcminutes).**

Directional check (not just magnitude): a LARGER ayanamsa (ours) means
a SMALLER computed sidereal Moon longitude than the GUI's, which means
a SMALLER `elapsed_frac` within the natal nakshatra, which means a
LARGER `remaining_frac`/`balance_years`, which means a LATER MD1
`end_jd` than the GUI's — i.e. the sign of this hypothesized mechanism
is **+ (our code's end_jd later than the GUI's)**, matching the
observed sign of every row-0 offset measured in §7/§8 (all 4 charts
positive). Rough magnitude check for Sulabh: 0.9355 arcmin / (13.3333°
× 60) ≈ 0.001169 fractional error × 16y (Jupiter, Sulabh's MD1 lord) ×
365.256d/yr ≈ **6.8 days** — same order of magnitude as the observed
+4.25d offset (not an exact match, but the right ballpark and the right
sign, unlike every mechanism checked in §8).

**Caveat, stated plainly rather than glossed over:** this ayanamsa
comparison is independently verified for **Sulabh only**. The
Ayanamsa line in `tests/fixtures/jhora_surbhi.md` /
`jhora_sheridan.md` / `jhora_david.md` (all three read `Lahiri
(23-40-39.08)`) is copied verbatim from this session's Prompt-1
instructing-prompt template text, NOT an independently re-captured
per-chart JHora GUI value — Lahiri ayanamsa drifts ~50.3"/year with
precession, so a genuine 1976-vs-1992 capture should differ by roughly
13-14 arcminutes between David and Surbhi, not read identically. This
is a real data-quality gap in the 3 new fixtures (their Ayanamsa line
is decorative boilerplate, not measured), flagged here rather than
used to falsely claim a 4-chart-confirmed mechanism. Re-capturing each
chart's actual GUI-displayed ayanamsa (Basics tab, same as Sulabh's
Session 27 capture) is the direct next step to confirm or refute this
hypothesis generally — not done in this audit.

### Verdict

**Mechanism PARTIALLY LOCATED.** Two solid findings, one open lead:

1. **Located (with certainty):** pyjhora is not usable as ground truth
   for this specific sub-day balance-at-birth question — it reproduces
   OUR code's numbers, not the GUI's, across all 4 charts. This closes
   off "read pyjhora as an oracle" as a viable path forward; any future
   audit needs the actual JHora v8 GUI (or its source, if ever
   available) rather than this port.
2. **Located (with certainty):** algorithm shape (Moon longitude
   pipeline, nakshatra→lord mapping, elapsed-fraction formula, Yogini/
   Vimshottari sharing) is NOT the source of the row-0 gap — pyjhora
   matches our code closely on all of these, yet both diverge from the
   GUI by nearly the same multi-day margin.
3. **Partially located (Sulabh-only, unconfirmed generally):** a
   ~0.94-arcminute ayanamsa discrepancy between the GUI's own displayed
   Lahiri value and pyswisseph's `SIDM_LAHIRI` at the same instant is
   right-signed and right-order-of-magnitude to explain Sulabh's +4.25d
   offset. Not yet confirmed for Surbhi/Sheridan/David (fixture data
   gap, see caveat above) and not proven SUFFICIENT even for Sulabh
   (order-of-magnitude, not exact).

### If located: recommended fix + blast radius (NOT implemented here)

**Not proposed as a fix to implement yet** — item 3 above is a lead,
not a confirmed mechanism. IF a future session confirms the ayanamsa-
epoch hypothesis generally (re-capture Surbhi/Sheridan/David's real
GUI-displayed ayanamsa values, repeat this comparison, confirm the
sign/magnitude pattern holds), the fix would NOT be a `_calc_dasha`-
scoped change like the year-length swap this diagnostic started
investigating — it would mean **pyswisseph's `SIDM_LAHIRI` does not
match JHora v8's own Lahiri ayanamsa reference epoch/constant**, which
is a claim about ayanamsa computation itself, not dasha timing
specifically.

**Blast radius if confirmed (substantially larger than the year-length
swap's, §7):** ayanamsa is computed via `swe.set_sid_mode(swe.SIDM_LAHIRI)`
/ `swe.get_ayanamsa_ut()` at every sidereal-longitude call site in the
app — not just the 3 `_add_years()` call sites `_calc_dasha` owns. Per
CLAUDE.md's "Ephemeris consolidation" lock, this includes all 11
migrated call sites through `helpers/ephemeris.py` plus the 3
direct-by-design exceptions (`chesta_bala.py`, `kala_bala.py` ×2) —
i.e. potentially every planetary position, every varga chart, every
yoga detection, every strength calculation in the entire codebase, not
a dasha-scoped fix. Envelope-tightening is NOT a reasonable candidate
outcome of this path (unlike the year-length swap) — a confirmed
ayanamsa-epoch mismatch would be a foundational-precision question
for the whole app, warranting its own dedicated design-chat session,
not a quick fix folded into the Vimshottari dasha thread.
