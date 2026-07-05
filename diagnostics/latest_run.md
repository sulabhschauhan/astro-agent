# Batch 3 ephemeris migration: chesta_bala/kala_bala/dig_bala (Session 52)

## Site classification
| File | Site | Flags | Verdict |
|---|---|---|---|
| chesta_bala.py | Moon/Sun lon (compute_chesta_bala) | SIDEREAL-STD | migrated |
| chesta_bala.py | Tara Grahas loop | SIDEREAL-STD | migrated |
| chesta_bala.py | swe.ECL_NUT (Sun kranti) | SIDEREAL-flag but not a planet id | NOT migrated — outside helper's SUN..MEAN_NODE contract |
| kala_bala.py | `_sun_sign` | SIDEREAL-STD | migrated |
| kala_bala.py | `_paksha_bala` Moon/Sun | SIDEREAL-STD | migrated |
| kala_bala.py | `_ayana_bala` per-planet loop | SIDEREAL-STD (flags), feeds Sayana via Python math | NOT migrated — task-flagged as sensitive; feeds Session 47 oracle-locked Kranti formula; left untouched out of caution (discrepancy vs actual flags noted) |
| kala_bala.py | `compute_kala_bala` Yuddha lon/lat loop | SIDEREAL-STD | NOT migrated — also needs xx[1] latitude, unsupported by helper |
| dig_bala.py | per-planet longitude loop | SIDEREAL-STD | migrated |

No local EphemerisError in any of the 3 files (only bare RuntimeError in
dig_bala.py); no test in any of the 3 test files monkeypatches calc_ut or
asserts on message wording (verified before migrating).

## Result
Full suite: **1843 passed, 3 skipped**, zero regressions. Smoke-tested
Sulabh's Kala/Chesta/Dig values before and after — bit-identical.
