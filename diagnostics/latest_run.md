# test_ephemeris.py sid_mode leak fix (Session 52)

**Fixed:** `test_sidereal_longitude_ignores_prior_global_sid_mode` set
SIDM_RAMAN and never restored Lahiri, risking a silent ayanamsa leak into
legacy modules' tests (panchaka.py, chandrabala.py, tarabala.py, etc. rely
on ambient Lahiri state pending ephemeris-wrapper migration). Wrapped in
try/finally restoring SIDM_LAHIRI unconditionally.

## Result
Full suite (`pytest tests/`): **1841 passed, 3 skipped**, no regressions.
