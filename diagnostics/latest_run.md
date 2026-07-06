# Session: av_transit_scanner.py -- Ashtakavarga transit segment scanner

**New file:** `agent/calculations/transits/av_transit_scanner.py` (only
file changed besides the benign `calc_router_stage2.log` growth from
running the suite; `git status` confirms it). No other file touched.

**Function:** `scan_av_transit_segments(transit_planet, natal_bav,
natal_sav, natal_contributors, start_jd, end_jd) -> list[AvTransitSegment]`
-- the ephemeris layer sitting on top of last session's pure
`score_av_transit()`. Walks a date window, groups it into contiguous
(sign, kakshya_index) segments, and scores each once at its midpoint.

**Design -- reuse over duplication:**
- Delegates the planet-identity/exclusion check to `score_av_transit()`
  itself (`_validate_transit_planet` calls it with placeholder
  sign="Aries"/degrees=0.0, discarding the result) -- same reuse pattern
  as `compute_bav_contributors` delegating to `compute_bav`. No planet
  list or ValueError wording duplicated.
- Imports `score_av_transit()`'s `_KAKSHYA_PLANETS` and
  `_KAKSHYA_WIDTH_DEG` constants directly so the scanner's own daily
  state-detection loop can never drift from the scorer's CITATION (e)
  boundary convention.
- Sidereal longitudes come only from `helpers/ephemeris.py`'s
  `sidereal_longitude()` -- no raw `swe.calc_ut()` call in this module
  (CLAUDE.md ephemeris-consolidation lock).
- Segmentation adapts sade_sati.py's `_find_segments` daily-scan pattern
  (`_daily_state_segments`) but deliberately DROPS its sub-day bisection
  refinement -- day-level boundaries are sufficient here (kakshya dwell
  floors: Jupiter ~45d, Saturn ~112d; a 1-day edge error is noise against
  the ~20y mahadasha envelope this nests inside).
- Each segment's score comes from exactly one `score_av_transit()` call
  at the segment's midpoint JD -- band/verdict/intensity logic is never
  reimplemented here.

**Retrograde re-entries are NOT merged or deduplicated** -- confirmed by
smoke test (see below): Saturn's real 2020-2023 Capricorn/Aquarius
retrograde oscillation produced repeated non-adjacent (sign,
kakshya_index) states as separate segments, exactly as designed.

**Validation:** `end_jd > start_jd`; window capped at 40 years (scope
guard: V1 dasha envelopes never exceed a single ~20y mahadasha; tuning
note: raise only if a future phase needs multi-dasha scans in one call).

**Manual verification (no test file this prompt, per instructions) --**
ran an inline smoke script against David's oracle-locked BAV/SAV/
contributor tables:
- Saturn over 2020-01-01..2023-01-01 (a real historical
  Capricorn/Aquarius retrograde window): 21 segments, contiguous tiling
  confirmed (each segment's end_jd == next segment's start_jd), first
  segment start == window start, last segment end == window end, and
  repeated non-adjacent (sign, kakshya_index) states present (retrograde
  evidence).
- Sun and Mars: all segments have `kakshya_index=None`, as designed.
- Moon/Mercury/Venus/unknown-planet: all raise `ValueError` via the
  delegated check.
- Reversed window (`end_jd < start_jd`): raises `ValueError`.
- 41-year window: raises `ValueError`; 40-year window (the boundary):
  succeeds (279 segments).
Script was not committed.

**Suite-warning triage (requested in design review):** the single
`DeprecationWarning` in the pytest tail
(`opentelemetry\util\_importlib_metadata.py:32: ... SelectableGroups dict
interface is deprecated. Use select.`) originates from
`opentelemetry-api` 1.42.1, a transitive dependency of `chromadb` (our
RAG vector store) -- confirmed via `pip show opentelemetry-api`
(`Required-by: chromadb, opentelemetry-exporter-otlp-proto-grpc,
opentelemetry-sdk, ...`) and a repo-wide grep showing zero direct
`import opentelemetry` in `agent/` or `tests/`. It fires from
opentelemetry's own internal code when something (transitively,
chromadb's client init) touches its entry-points metadata shim -- it is
third-party noise, not actionable in this codebase, and not something
this session's change introduced or could fix.

## Test tallies
- Full suite: `2923 passed, 3 skipped, 1 warning` -- unchanged (pure
  addition, no test file this prompt; existing suite stays green).

No existing file's logic changed.
