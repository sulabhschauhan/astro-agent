# test_gochara.py: pin Session 52 FLG_SPEED fix (Session 52)

**Added:** 2 tests — Mercury retrograde=True at David's natal JD (reused
from test_combustion.py/test_ephemeris.py's known real-chart case) and
Sun retrograde=False at Sulabh's natal JD (inverse-failure guard). Both
verified against gochara output before writing (is_retrograde field
confirmed present). Pins the Session 52 migration's incidental FLG_SPEED
fix against silent regression; no prior test covered a real graha's
retrograde flag (only Rahu/Ketu's hardcoded True was tested).

## Result
New tests alone: 2 passed (4 total in file).
Full suite: **1843 passed, 3 skipped** (1841 + 2 new), zero regressions.
