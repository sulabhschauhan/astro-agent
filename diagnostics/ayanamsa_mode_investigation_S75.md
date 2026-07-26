# Ayanamsa Mode Investigation — Traditional Lahiri vs True Chitrapaksha (Session 75)

**Status:** Diagnostic record. No production code touched. Not committed
pending confirmation (per instructing prompt Task 5).
**Related:** `diagnostics/vimshottari_year_length_S74.md` §11 (origin of
the 0.94 arcmin/56.13″ ayanamsa-epoch lead), `helpers/ephemeris.py`
(production `sidereal_longitude`/`sidereal_position`, hardcoded
`SIDM_LAHIRI`), `agent/chart_calculator.py:_calc_dasha()`.
**Method note:** GUI ayanamsa values under both modes (Traditional
Lahiri, True Chitrapaksha) for Sulabh and Sheridan were supplied
externally this session (paste-in evidence) and independently verified
against live `pyswisseph` calls below, not taken on faith. All
pyswisseph values in this file were computed fresh this session; none
are carried over from S74 without re-verification.

---

## 1. Origin

S74 §11 found the JHora v8 GUI's own displayed Lahiri ayanamsa for
Sulabh (`23-40-39.08` = 23.677522°, captured Session 27, Basics tab)
differs from pyswisseph's `SIDM_LAHIRI` value at the identical instant
(23.693114°) by **+0.015592° (+0.9355 arcmin, 56.13″)**. This was
flagged as a partially-located lead for the Vimshottari row-0 offset
(§7-§8 of the same file), Sulabh-only, unconfirmed on the other 3
charts due to a fixture data-quality gap (Surbhi/Sheridan/David's
Ayanamsa lines are boilerplate template text, not real per-chart GUI
captures).

## 2. S75 investigation path

This session obtained two additional real GUI captures (externally
supplied, not from any repo fixture) for **Sulabh** and **Sheridan**,
each read under **both** ayanamsa mode settings in the JHora v8 GUI:

- **Traditional Lahiri**
- **True Chitrapaksha** (Spica/Chitra fixed at 180° tropical)

This directly tests whether S27's Sulabh capture (`23-40-39.08`) was
taken under the same mode as production's hardcoded `SIDM_LAHIRI`, or
under the GUI's other Lahiri-family setting.

## 3. Evidence table (Tasks 1-2, verified against live pyswisseph)

### 3a. Traditional Lahiri (`swe.SIDM_LAHIRI`)

| Chart | pyswisseph (deg / DMS) | GUI Traditional Lahiri (deg / DMS) | Delta |
|---|---|---|---|
| Sulabh (JD 2447257.291667) | 23.693114° / 23-41-35.21 | 23.693075° / 23-41-35.07 | **+0.142″** |
| Sheridan (JD 2445847.750000) | 23.639210° / 23-38-21.16 | 23.639172° / 23-38-21.02 | **+0.137″** |

Both within the ~0.14″ expectation. This confirms production's
`SIDM_LAHIRI` matches JHora's **Traditional Lahiri** GUI setting almost
exactly, at two epochs 8 years apart (1984, 1988) — a fixed,
essentially-zero cross-implementation gap, not the 56.13″ S27 gap.

### 3b. True Chitrapaksha (`swe.SIDM_TRUE_CITRA`, mode 27)

| Chart | pyswisseph (deg / DMS) | GUI True Chitrapaksha (deg / DMS) | Delta |
|---|---|---|---|
| Sulabh | 23.683150° / 23-40-59.34 | 23.677522° / 23-40-39.08 | **+20.260″** |
| Sheridan | 23.627844° / 23-37-40.24 | 23.623658° / 23-37-25.17 | **+15.068″** |

**Flagged, not glossed over:** pyswisseph's `SIDM_TRUE_CITRA` does
**not** match the GUI's True Chitrapaksha reading nearly as tightly as
`SIDM_LAHIRI` matches Traditional Lahiri — 15-20″, roughly 110-140x
looser. This is consistent with the older Session 19 sweep
(`playbook_export/decisions/ayanamsa-investigation.md`), which already
found `SIDM_TRUE_CITRA` off by 9.89″ against a differently-labeled
JHora fixture — pyswisseph's True Citra implementation has never been
shown to match JHora as precisely as Traditional Lahiri does. The mode
identification below rests on the Traditional Lahiri match (3a, tight
to 0.14″), not on independently re-deriving True Chitra numerically.

## 4. Root cause of the S74 §11 misdiagnosis

S27's Sulabh capture (`23-40-39.08` = 23.677522°) is **byte-identical**
to this session's freshly-recaptured **True Chitrapaksha** GUI value
(3b table above) — not the Traditional Lahiri value. S27's capture
session did not record which ayanamsa mode the GUI was set to at
capture time; S74 §11 implicitly assumed it was Traditional Lahiri
(the mode production hardcodes) and compared it directly against
`SIDM_LAHIRI`, producing the 56.13″ gap and reading it as a
precession-model/epoch divergence between pyswisseph and JHora.

**Corrected reading:** S27 was captured under **True Chitrapaksha**
mode, then compared cross-mode against production's **Traditional
Lahiri** (`SIDM_LAHIRI`) output. The ~56″ gap is the well-known
Lahiri-vs-Chitrapaksha mode delta (both are legitimate, named,
distinct ayanamsa definitions — Chitrapaksha fixes Spica at exactly
180°, Traditional Lahiri does not), not evidence of an
implementation-level precession discrepancy between pyswisseph and
JHora. When compared **within the same mode** (3a above), pyswisseph
and JHora agree to ~0.14″ at both 1984 and 1988 epochs.

## 5. Row-0 impact table (Task 3)

Moon sidereal longitude computed via the production flag path
(`swe.FLG_SWIEPH | swe.FLG_SIDEREAL`) under each mode, for all 4
canonical charts. No nakshatra or pada boundary is crossed by the mode
switch in any of the 4 charts (starting Vimshottari lord is unchanged
in every case), so the row-0 comparison is a clean apples-to-apples
balance-day recalculation, not complicated by a lord change.

| Chart | Trad. Lahiri Moon lon | True Chitra Moon lon | Mode Δ | Nakshatra/pada |
|---|---|---|---|---|
| Sulabh | 212.23199900° (212-13-55.20) | 212.24196365° (212-14-31.07) | -35.873″ | Vishakha pada 4 (both modes) |
| Surbhi | 315.20143018° (315-12-05.15) | 315.22175675° (315-13-18.32) | -73.176″ | Shatabhisha pada 3 (both modes) |
| Sheridan | 2.15985235° (2-09-35.47) | 2.17121895° (2-10-16.39) | -40.920″ | Ashwini pada 1 (both modes) |
| David | 131.65790588° (131-39-28.46) | 131.67282979° (131-40-22.19) | -53.726″ | Magha pada 4 (both modes) |

Row-0 remaining days (`(1 - elapsed_frac) × starting_lord_years ×
365.256363`, S74-native sidereal-year formula) under each mode, and
the predicted shift a Traditional→True Chitra production switch would
produce, compared against S74 §8's already-measured sidereal row-0
offset (our code minus GUI, using production's current Traditional
Lahiri):

| Chart | Row0 days (Trad) | Row0 days (Chitra) | Predicted shift | S74 §8 observed offset | Residual after shift | % of offset closed |
|---|---|---|---|---|---|---|
| Sulabh | 482.7232 | 478.3557 | +4.3676d | +4.2599d | -0.1077d | 97.5% |
| Surbhi | 2366.1560 | 2356.1331 | +10.0230d | +11.1950d | +1.1720d | 89.5% |
| Sheridan | 2142.6221 | 2140.4425 | +2.1797d | +3.8374d | +1.6577d | 56.8% |
| David | 321.2793 | 318.4175 | +2.8618d | +1.4724d | -1.3894d | **5.6% (overshoots)** |

## 6. Status: partial explanation only — measured, not the pre-stated estimate

**Correction to the instructing prompt's framing:** the prompt's own
working estimate for this section ("mode switch closes ~40% of row-0
spread; residual ~6d spread remains") does not match what was actually
measured here. Reporting the real numbers rather than the estimate,
per this project's standing measure-first discipline (CLAUDE.md
Working Style #12, and the same principle S74 §8 itself applied when
it called its own verdict "(c) — high variance, unresolved" rather
than forcing a scaling fit):

- **Mean % of offset closed across the 4 charts: ~62.35%**, not ~40%
  — but the per-chart spread (5.6% to 97.5%) is far too wide for a
  single summary percentage to be meaningful on its own.
- **Residual spread after the mode switch: ~3.05d** (range -1.39d to
  +1.66d), not ~6d.
- **The residual is not single-signed.** Sulabh and David residuals
  are negative (mode switch already fully or over-explains their
  offset); Surbhi and Sheridan residuals are positive (mode switch
  under-explains). A clean, chart-independent second cause (e.g. a
  fixed year-length-constant correction, S74's own open item) would be
  expected to produce a residual of consistent sign and comparable
  magnitude across charts — this data does not show that. David in
  particular is a outlier: the mode-switch shift (+2.86d) is nearly
  **double** its actual observed offset (+1.47d), i.e. switching modes
  would move David's prediction in the right direction but past the
  target, not toward a clean ~40-60% partial correction.

**Conclusion:** the Traditional-vs-True-Chitrapaksha mode
identification (§4) is solid and resolves the S74 §11 misdiagnosis
cleanly — that finding stands on its own, verified to 0.14″/0.137″ at
two independent epochs. But mode choice, applied uniformly as a
production ayanamsa swap, is **not** shown here to be a sufficient or
even a consistently-signed explanation for the remaining Vimshottari
row-0 spread across all 4 charts. Whatever secondary mechanism S74's
year-length open item (or another untested variable) contributes, it
does not appear to combine additively with the mode-switch shift in a
simple way — at least not one visible from a 4-chart sample.

## 7. Decision required at session close

Mode choice (Traditional Lahiri vs True Chitrapaksha) is a
**doctrinal** question, not a numerical bug — both are legitimate,
named ayanamsa definitions in real use, and production's current
`SIDM_LAHIRI` choice matches its own named GUI counterpart (Traditional
Lahiri) to <1″ at two epochs 8 years apart. Nothing in this diagnostic
is evidence that Traditional Lahiri is "wrong" or that True
Chitrapaksha is "right" — switching is a doctrinal choice about which
classical reference this app should follow, not a precision fix.

**Before any production ayanamsa change is proposed:**
1. A PVR book quote check — does *Vedic Astrology: An Integrated
   Approach* state a preference between Traditional Lahiri and True
   Chitrapaksha for the calculation conventions this app already
   follows elsewhere?
2. An AstroSage parity check on natal longitudes — AstroSage is this
   app's other validation oracle (see CLAUDE.md's Ephemeris
   consolidation lock); confirm which mode AstroSage's own published
   longitudes are closer to, using the existing 4-chart reference set,
   before treating either mode as preferred.
3. The residual analysis in §6 needs its own follow-up — the
   mode-switch mechanism alone does not close the row-0 gap uniformly;
   a second mechanism (year-length constant, or something untested)
   is still required and its interaction with the mode choice is
   unknown.

**Not decided here.** Logged as an **S76 candidate task**: resolve (1)
and (2) above before any `helpers/ephemeris.py` / `chart_calculator.py`
ayanamsa mode change is authorized. No production code touched by this
session (Task 5 constraint honored — mode identified and quantified,
not implemented).
