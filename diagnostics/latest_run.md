# chart_profile.py wired to Bhava Drishti Bala (Session 53 follow-up)

**Wired:** career_strength's `compute_bhava_bala_totals` call now builds
`planet_lons` via `ephemeris.sidereal_longitude()` (7 classical planets,
new `_CAREER_PLANET_SWE_IDS` const) — no new direct `swe.calc_ut` call.
Stale drishti-stub comments (gating loop + TUNING NOTE) updated to note
Bhava Drishti Bala is real since Session 53.

**Threshold discipline:** no numeric `uncertainty_virupa` envelope exists
or ever existed specifically for the drishti stub (confirmed via the
pre-existing comment: it was never folded into the 2.0 Ayana envelope)
— nothing changed here. Note: this prompt said "48/48 ±0.2 Virupa"; the
repo's actual validated figure (bhava_bala.py CITATION) is ±0.16 Virupa
max |delta| — used the verified figure in the updated comments.

## Result
Full suite: **1835 passed, 3 skipped, 8 failed** — exact target. The 4
`test_orchestrator_e2e.py` career failures recovered; only the 8
`test_bhava_bala.py` failures remain (next prompt, unchanged).
