# Ayanamsa / Cross-Ephemeris Discrepancy Investigation

Session 17.

## Question
calculate_solar_return showed ~10.6 min epoch drift vs AstroSage for
Sulabh's 2026 Varshaphal — root cause?

## Method
Compared AstroSage's stated Lahiri ayanamsa + degree-level Sun/Moon
positions against pyswisseph across 4 reference charts (see
reference_charts.md), spanning 1976-2026, 3 timezones (IST+5.5, Durban+2,
London+0), both hemispheres.

## Findings
- Ayanamsa: pyswisseph SIDM_LAHIRI vs AstroSage = constant ~2.2-2.7" across
  all 4 charts/epochs. SIDM_LAHIRI_ICRC slightly tighter (~1.1-1.6"), also
  flat. Ayanamsa-variant is NOT the source of the drift.
- Sun/Moon tropical longitude residuals (NOABERR/NONUT/TRUEPOS flag combos
  tested): 5-48", inconsistent in sign/magnitude across charts and between
  Sun/Moon. No flag combination resolves all cases.
- Consistent with display rounding + birth-time-to-the-second precision in
  source PDFs — irreducible noise, same class as the documented ±37-day
  Vimshottari drift.

## Decision
- Did not change global ayanamsa mode (risk to validated 9/9 D1 +
  Vimshottari, and ~1" gain from LAHIRI_ICRC is noise-level anyway).
- Added is_boundary_sensitive(degree_in_sign, threshold_deg=5.0) helper —
  flags sign-boundary-dependent results (Lagna, Muntha, etc.) within 5° of
  a boundary, based on observed worst-case ~48" residual ≈ ~5° ascendant
  motion. Reusable across Varshaphal, Muntha, and future sign-dependent
  calculations.
