# Batch 4 ephemeris migration: sthana_bala/panchanga/chart_profile/combustion (Session 52)

## Site classification
| File | Site | Flags | Verdict |
|---|---|---|---|
| sthana_bala.py | per-planet longitude loop | SIDEREAL-STD | migrated → sidereal_longitude() |
| panchanga.py | Moon + Sun (calculate_panchanga) | SIDEREAL-STD + FLG_SPEED | migrated → sidereal_position() (both lon+speed used) |
| panchanga.py | calculate_sunrise/sunset (swe.rise_trans) | different API, not calc_ut | out of scope, untouched |
| chart_profile.py | `_koota_natal_info_from_chart` (Moon) | SIDEREAL-STD | migrated → sidereal_longitude() |
| chart_profile.py | `_saturn_sidereal_sign` | SIDEREAL-STD | migrated → sidereal_longitude() |
| combustion.py | per-planet longitude loop (incl. Sun) | SIDEREAL-STD, longitude-only | migrated → sidereal_longitude() — task described this as needing sidereal_position() for retro overrides, but retrograde is actually read from chart_data, never from this call (only xx[0] used); used sidereal_longitude() to match actual usage, confirmed numerically identical |

No local EphemerisError in any of the 4 files. No test asserts message
wording EXCEPT test_combustion.py's `test_c_calc_ut_raising_surfaces_
runtimeerror` (`pytest.raises(RuntimeError, match="Sun")`) — migrating
naively would have replaced the planet name with ephemeris.py's numeric
swe id, breaking it. Kept a thin except-wrapper there that re-raises
`ephemeris.EphemerisError` as this module's own RuntimeError, preserving
"Sun" in the message; verified directly (see smoke test) and via full
suite. No test file exists for chart_profile.py directly (covered via
test_orchestrator_e2e.py / test_calc_router_stage2.py, no message asserts).

## Result
Full suite: **1843 passed, 3 skipped**, zero regressions. All 13
original Session 44 debt call sites now migrated or explicitly deferred
with inline rationale (Batches 1-4 complete).
