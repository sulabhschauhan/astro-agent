# test_bhava_bala.py: repair + Bhava Drishti oracle parity (Session 53)

**Part 1:** deleted old Layer G stub-shape tests (obsolete by design,
noted in module docstring). Layer H (now I) aggregator tests thread
`planet_lons` (new `_planet_lons_by_chart` fixture, mirrors
`_house_cusps_by_chart`'s pattern via `ephemeris.sidereal_longitude()`)
and recompute expected totals structurally from the sub-components, not
magic numbers; `drishti_is_stubbed` assertion flipped to `False`.

**Part 2:** new Layer H — 48 parametrized AstroSage BhavBala parity
assertions (±0.5 Virupa, mirrors test_drik_bala.py's tolerance
convention), Sheridan first (hardest case, Moon malefic). Verified all
48 values against the repo's own computation before writing (max
|delta| 0.15) — all 4 birth data points match existing fixtures, no
discrepancy.

**Part 3:** new Layer G — 4 kernel structural spot-checks (Saturn/Mars/
Jupiter add-on boundaries + Venus plain-base), with a note on why
continuity assertions (unlike test_drik_bala.py) would be wrong here —
the add-on specials are intentionally discontinuous by design.

## Result
Full suite: **1895 passed, 3 skipped, 0 failed** (exceeds 1843; net new
parametrized cases from Layers G/H plus the 12-house Layer H sweep).
