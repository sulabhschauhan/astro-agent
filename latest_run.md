# S143 -- KP 7th-cusp sub-lord (steps 1-3 of the handover: capture, build, validate)

Model: Sonnet (design discussion + build, this session, no Claude Code handoff -- done directly).

## What shipped this run (uncommitted -- RATIFIED token not given)

1. **`agent/chart_calculator.py`** (`calculate_chart()` only, ~line 722-736 and
   the `meta` dict at the return): captured the Placidus cusps tuple that was
   previously discarded (`_, ascmc = swe.houses(...)` -> `cusps_tropical, ascmc = ...`),
   and added a bracketed `swe.SIDM_KRISHNAMURTI` ayanamsha lookup (NOT a second
   `swe.houses()` call) applied to those same tropical cusps, restored to
   `SIDM_LAHIRI` immediately after so nothing downstream in the function is
   affected. New `meta` key: `house_cusps_kp_sidereal` (12 floats, KP/
   Krishnamurti-ayanamsha sidereal, house 1..12). `build_varshaphal_chart()`
   (the other swe.houses() call site) was deliberately NOT touched -- it's not
   used for natal marriage-timing KP.

2. **`agent/calculations/kp/sub_lords.py`** (new module): the 243-division
   (27 nakshatras x 9 Vimshottari-proportional sub-lords -- NOT 249; the
   handover's own arithmetic was wrong, 27x9=243, caught by
   `test_table_has_243_rows`) sub-lord table, built with `Fraction` arithmetic
   for exact boundaries, reusing `DASHA_ORDER`/`DASHA_YEARS` FROM
   `agent.chart_calculator` (the real locked 120-year table -- the handover
   pointed at `agent/calculations/dashas/`, which is the decoy stub, not
   where DASHA_ORDER/DASHA_YEARS actually live). `sub_lord_for_longitude(lon)`
   and `kp_house_sub_lord(house_cusps_kp_sidereal, house)` -- house 7 gives the
   fact this task needs, but the function takes any house 1-12.

3. **Ayanamsha decision (discussed and ratified with Sulabh before building)**:
   KP uses its own ayanamsha, not Lahiri -- `SIDM_KRISHNAMURTI` reproduces
   AstroSage's own printed "K.P. New" ayanamsha value to ~23 arcsec (vs ~49
   arcsec for `SIDM_KRISHNAMURTI_VP291`, despite AstroSage's own label reading
   "New" -- vendor ayanamsha naming is not standardized; went by which
   constant's numbers actually match). Lahiri-only was measured as the
   alternative: only 2/48 oracle cusps would flip sub-lord vs KP-ayanamsha,
   and the 7th cusp specifically never flipped across all 4 charts -- but
   Lahiri would stop being KP by KP's own definition, so KP-ayanamsha shipped.

4. **Oracle validation (S143, done BEFORE any of this was wired anywhere)**:
   found a KP oracle nobody had noticed -- all 4 AstroSage reports in
   `data/pdfs/` have a page-44 "KP System / Nakshatra Nadi" section with a
   full 12-cusp Cuspal Positions table (SUB column). Validated
   `sub_lord_for_longitude()` against it across all 4 reference charts (Sulabh,
   David, Sheridan, Surbhi) x 12 cusps = 48 data points, through the ACTUAL
   `calculate_chart()` pipeline (same geocoding fixture every other test in
   this repo uses): **46/48 exact match**. The 2 misses (David cusp 12,
   Surbhi cusp 10) are boundary-proximity artifacts of the existing geocoding-
   fixture-vs-AstroSage's-own-coordinates residual (same class
   `is_boundary_sensitive` already documents, amplified at David's 51N
   latitude) -- confirmed by re-running with AstroSage's OWN stated lat/lon
   instead of the geocoding fixture, which scores 47/48 (only David remains).
   NOT a defect in the sub-lord table's construction.

   PDF-PARSING TRAP CAUGHT EN ROUTE: a naive linear text extraction of the
   AstroSage page-44 table (pdfplumber's default reading order) interleaves
   the chart-diagram's planet-in-house labels into the middle of table rows,
   because the diagram sits in the same page region as the table and
   pdfplumber does not respect the 2-column layout. A first-pass transcription
   using that naive flow got 5 of Sulabh's 12 SUB values wrong. Fixed by
   re-extracting from word-level (x,y) bounding boxes instead. Anyone
   re-deriving oracle values from these PDFs should extract by position, not
   by `page.extract_text()`.

## Tests (all passing in an isolated sandbox re-import of the exact staged
files, with a conftest replicating tests/conftest.py's geocoding fixture --
NOT the real pytest run against the full suite; that still needs to happen
on Sulabh's machine)

- `tests/calculations/kp/test_sub_lords.py` -- 76 tests, pure table/lookup
  logic (243-row coverage, exact-boundary KP convention, every nakshatra's
  star-lord-starts-its-own-sequence invariant, Vimshottari-proportional
  segment widths, wrap-around, `kp_house_sub_lord` argument validation). One
  self-correction caught by the test itself and left in the test comments:
  a first draft asserted Revati's last segment as Mercury ("the cycle closes
  on itself") -- wrong; it's Saturn (the lord immediately before Mercury in
  the 9-lord cycle), and the test/comment now says why.
- `tests/calculations/kp/test_kp_oracle_validation.py` -- the 48-cusp sweep
  against AstroSage (46 pass, 2 `xfail(strict=False)` for the two documented
  geocoding-boundary misses), plus a `>=46/48` regression floor, a KP-cusps-
  actually-differ-from-Lahiri-ascendant sanity check, and a shape check.

Run locally (sandbox, not the repo's real suite):
`agent/chart_calculator.py` unmodified tests (`tests/test_chart_calculator.py`,
`tests/regression/test_chart_calculator_characterization_david.py`) + the new
KP tests: **151 passed, 2 xfailed, 0 failed** -- the cusp-capture edit did not
regress anything already covered.

## NOT done this run (deliberately -- per the handover's own sequencing and
what was agreed before starting)

- Steps 4/5: wiring `kp_house_sub_lord(chart['meta']['house_cusps_kp_sidereal'], 7)`
  into a `kp_facts.py` composer (mirroring `transit_facts.py`), the matching
  `FACT_BLOCK_PROVIDES` key, `pipeline._fact_block` rendering, and the live
  GPT-5 measurement. Per the standing warning ("do not wire before oracle-
  validated") validation is now done, but wiring is a second review point,
  as discussed. NOT started without a further go-ahead.
- Did NOT touch `build_varshaphal_chart()`'s cusp discard (site 2) -- not
  needed for natal marriage timing.
- Did NOT re-run `scripts/expert_pilot.py marriage_past` -- Sulabh deferred
  that until after KP, noted but not re-litigated.

## Sulabh: please run on your machine

    pytest tests/astro/ tests/calculations/ -q

to confirm against the real suite (this session's checks were an isolated
sandbox re-import, not a full-suite run) before we talk about wiring.
