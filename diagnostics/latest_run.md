# Bhava Drishti Bala real implementation (Session 53)

**Shipped:** `compute_bhava_drishti_bala(house_cusps, planet_lons)` —
bhava-level Sphuta Drishti (raw PyJHora piecewise + Saturn/Mars/Jupiter
additive add-ons, quarter rule except Mercury/Jupiter, dynamic benefic/
malefic classification reused from `drik_bala.py`'s `_classify_moon`/
`_classify_mercury`, no clamp). `compute_bhava_bala_totals` gains a
required `planet_lons` param; `drishti_is_stubbed` now `False`; caveat
rewritten.

## Validation checkpoint (Sulabh, printed not tested)
All 12 houses within ±0.5 Virupa of the expected oracle array (max
|delta| 0.15, house 9): 55.63/20.54/-15.52/-20.88/-11.88/-31.27/-35.01/
12.22/-19.03/-26.95/18.37/23.07. **ALL OK.**

## Expected breakage (not patched, per instructions)
Full suite: **1831 passed, 3 skipped, 12 failed.** 8 in
`test_bhava_bala.py` (Layer G stub-shape tests, Layer H aggregator calls
missing `planet_lons`) — direct signature-change fallout. 4 in
`test_orchestrator_e2e.py` (`test_career_{david,sheridan,surbhi,sulabh}`)
— `chart_profile.py:372` calls `compute_bhava_bala_totals` with the old
3-arg signature; out of scope for this bhava_bala.py-only prompt.
