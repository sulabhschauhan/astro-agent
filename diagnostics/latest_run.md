# 3 more ephemeris migrations: gochara/sade_sati/navamsa (Session 52)

**Migrated:** `_calc_transit_graha` (gochara.py) and `_calc_graha`
(navamsa.py) now delegate to `ephemeris.sidereal_position()`; sade_sati's
`_saturn_sign` to `ephemeris.sidereal_longitude()`. sade_sati's local
`EphemerisError` aliased to `ephemeris.EphemerisError` (gochara/navamsa had
none). TODO markers removed; docstrings cite Session 52.

**Bug found, incidentally fixed:** gochara.py/navamsa.py's own flags
omitted FLG_SPEED, so `is_retrograde`/`retrograde` was always False for
the 7 non-node grahas (same bug class as the Session 51 chart_calculator
fix). `sidereal_position()` always sets FLG_SPEED, so this is now
correct. No test asserted False for a real graha (only Rahu/Ketu's
hardcoded True), so no test impact — flagged, not silently changed.

## Result
Full suite: **1841 passed, 3 skipped**, zero regressions. sade_sati's
thousands-of-calls window scans: 93s full-suite wall clock, within normal
run-to-run variance (85-109s), no caching added per instructions.
7 debt call sites remain (chesta_bala, kala_bala, dig_bala, sthana_bala,
panchanga, chart_profile, combustion).
