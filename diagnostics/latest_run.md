# tests/calculations/helpers/test_ephemeris.py added (Session 52)

**Added:** 20 tests for `agent/calculations/helpers/ephemeris.py` — local
swe.calc_ut reference parity (Moon/MeanNode/Saturn, 1e-9), sidereal_position
speed sign (David Mercury retrograde <0, Sulabh Sun >0), longitude
normalization across all 11 bodies SUN..MEAN_NODE, sid_mode independence
(prior SIDM_RAMAN doesn't leak), chained EphemerisError on invalid planet
99999, and sidereal_position/sidereal_longitude longitude consistency.
jd_ut values derived via calculate_chart(), not hardcoded, reusing
test_combustion.py's known David-Mercury-retrograde fixture.

## Result
New file alone: 20 passed.
Full suite (`pytest tests/`): **1841 passed, 3 skipped** (1821 + 20 new,
delta exact, no regressions).
