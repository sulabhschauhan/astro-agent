# David — Ashtakavarga (BAV/SAV) Oracle Fixture — PARKED

## Header

- **Source:** Jagannatha Hora v8 (Windows), Strengths tab → Ashtakavarga → D-1 of the Natal Chart
- **Birth data:** David — 19 Jan 1976, 22:00:00, capture location London Colney, United Kingdom (0 W 17' 00", 51 N 43' 00"), UTC+0, Lahiri ayanamsa, Whole Sign houses, Mean Node. **Location provenance note:** AstroSage's reference PDFs for David use London (0:7 W, 51:30 N), NOT London Colney — the coordinate delta is irrelevant at sign level (this fixture is sign-only) but MUST be reconciled before any degree-level David fixture is captured. JHora ayanamsa at capture: 23-30-25.61 (a known ~1 arcmin/57.77″ pyswisseph-vs-JHora Lahiri cross-implementation gap, flat across all 4 reference charts — documented in SESSION_LOG.md Session 19 and `playbook_export/decisions/ayanamsa-investigation.md`).
- **Reference sign:** Virgo (David's natal lagna). **CRITICAL provenance note:** JHora's "Select the reference" dialog states the chosen sign "will be used as lagna when finding ashtakavarga." Empirically confirmed 2026-07-06: an earlier capture with reference=Aries produced different grids, so the reference sign drives the lagna-contribution bindus. Any future capture MUST set reference = natal lagna. BAV row totals and SAV grand total (337) are lagna-position-invariant and CANNOT detect a wrong reference sign.
- **Layout note:** values read from JHora's South Indian fixed-sign grid (Pisces top-left, clockwise). Transcription validated via 21 checksums: 8 canonical row totals + 12 column sums equal to SAV + grand total 337.
- **Captured:** 2026-07-06 (Session 54)
- **Status:** PARKED. Promotion target: Ashtakavarga BAV/SAV module validation (hardest-case-first).

## BAV table

| Planet | Ar | Ta | Ge | Cn | Le | Vi | Li | Sc | Sg | Cp | Aq | Pi | Total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Sun     | 3 | 5 | 4 | 4 | 5 | 2 | 5 | 5 | 3 | 5 | 4 | 3 | 48 |
| Moon    | 3 | 4 | 5 | 5 | 4 | 4 | 5 | 4 | 2 | 4 | 4 | 5 | 49 |
| Mars    | 2 | 4 | 6 | 2 | 2 | 2 | 4 | 4 | 2 | 3 | 4 | 4 | 39 |
| Mercury | 2 | 5 | 6 | 3 | 3 | 5 | 4 | 5 | 5 | 6 | 5 | 5 | 54 |
| Jupiter | 5 | 4 | 6 | 3 | 3 | 7 | 4 | 4 | 6 | 4 | 5 | 5 | 56 |
| Venus   | 4 | 3 | 3 | 5 | 4 | 5 | 5 | 7 | 5 | 4 | 2 | 5 | 52 |
| Saturn  | 3 | 1 | 3 | 4 | 3 | 5 | 5 | 4 | 3 | 3 | 4 | 1 | 39 |
| Lagna   | 4 | 3 | 6 | 6 | 2 | 2 | 5 | 5 | 4 | 4 | 4 | 4 | 49 |

## SAV table (7 planets only — Lagna BAV excluded from SAV, per JHora)

| | Ar | Ta | Ge | Cn | Le | Vi | Li | Sc | Sg | Cp | Aq | Pi | Total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SAV | 22 | 26 | 33 | 26 | 24 | 30 | 32 | 33 | 26 | 29 | 28 | 28 | 337 |

## Checksums (verified at transcription time)

Each planet row total equals its canonical fixed total:

| Planet | Canonical total | Verified |
|---|---|---|
| Sun     | 48 | yes |
| Moon    | 49 | yes |
| Mars    | 39 | yes |
| Mercury | 54 | yes |
| Jupiter | 56 | yes |
| Venus   | 52 | yes |
| Saturn  | 39 | yes |
| Lagna   | 49 | yes |

Each sign column of the 7 planet rows (Sun..Saturn, Lagna excluded) sums to the SAV value for that sign:

| Sign | Column sum (7 planets) | SAV | Match |
|---|---|---|---|
| Ar | 22 | 22 | yes |
| Ta | 26 | 26 | yes |
| Ge | 33 | 33 | yes |
| Cn | 26 | 26 | yes |
| Le | 24 | 24 | yes |
| Vi | 30 | 30 | yes |
| Li | 32 | 32 | yes |
| Sc | 33 | 33 | yes |
| Sg | 26 | 26 | yes |
| Cp | 29 | 29 | yes |
| Aq | 28 | 28 | yes |
| Pi | 28 | 28 | yes |

SAV grand total = 337 (sum of the 12 SAV column values above) — verified.

**Transcription correction note:** the original capture had Sun-Leo transcribed as 4, which failed both the Sun row-total checksum (would sum to 47, not 48) and the Leo column-sum checksum (would sum to 23, not 24 SAV). Corrected to Sun-Leo = 5, which reconciles both checksums and the 337 grand total simultaneously. All 21 checksums pass against the corrected value above.

## D-1 positions (source-verified, JHora Basics tab, 2026-07-06)

| Contributor | Position | Retrograde |
|---|---|---|
| Lagna   | 5° Virgo 11'25"      | — |
| Sun     | 5° Capricorn 27'34"  | no |
| Moon    | 11° Leo 40'24"       | no |
| Mars    | 21° Taurus 13'34"    | yes |
| Mercury | 12° Capricorn 45'29" | yes |
| Jupiter | 23° Pisces 55'32"    | no |
| Venus   | 28° Scorpio 45'44"   | no |
| Saturn  | 6° Cancer 02'43"     | yes |

**Validation trail:** Mercury's sign (Capricorn) was first back-solved uniquely from the Sun BAV row against PVR Table 19 during design review (2026-07-06), then independently confirmed from the JHora Basics tab capture above — both checks corroborate the same sign, documented here as this fixture's independent validation trail for the one contributor not in the earlier highlight-marker cross-reference. The other 7 positions (Lagna, Sun, Moon, Mars, Jupiter, Venus, Saturn) are read directly from the Basics tab capture. This table validates the D-1 *positions* themselves; it does NOT constitute a cell-by-cell BAV/SAV parity check against the tables above — that remains a distinct, not-yet-done validation step.
