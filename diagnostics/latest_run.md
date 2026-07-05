# 3-file ephemeris migration: chandrabala/tarabala/panchaka (Session 52)

**Migrated:** `_moon_sign`/`_moon_nakshatra`/`_moon_sidereal_longitude` now
delegate to `helpers.ephemeris.sidereal_longitude()`; each module's local
`EphemerisError` replaced with `EphemerisError = ephemeris.EphemerisError`
alias. TODO markers removed; docstrings updated to cite Session 52.
Existing `monkeypatch.setattr(<module>.swe, "calc_ut", ...)` tests still
pass unchanged -- `swisseph` is a shared sys.modules singleton, so
patching it via any module's `swe` name also patches ephemeris.py's calls.

## Result
Full suite (`pytest tests/`): **1841 passed, 3 skipped**, zero regressions.
10 of 13 debt call sites remain (chesta_bala, kala_bala, dig_bala,
sthana_bala, sade_sati, gochara, navamsa, panchanga, chart_profile,
combustion).
