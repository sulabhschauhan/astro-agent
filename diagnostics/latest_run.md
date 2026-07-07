# Session 56: OPTIONAL AV timing enrichment for career_strength/current_dasha

One file changed: `agent/infra/chart_profile.py`. No formatter, router,
orchestrator, or test file touched, per scope.

## Read-first finding: extraction vs. direct callable

The av_transit domain branch's envelope/scan/rank logic was NOT directly
callable as-is -- it was inlined directly in `build_domain_profile()`'s
`elif domain == "av_transit":` block (assembling `envelope`, natal
BAV/SAV tables, calling `scan_av_transit_segments()`, the tiling-contract
asserts, ranking, and the `sub_windows` render-contract mapping), all
using local variables scoped to that one branch. **Extracted** it
verbatim into a new private module-level helper,
`_build_av_timing_block(chart_data, transit_planet) -> dict`, returning
exactly `{"transit_planet", "dasha_envelope", "sub_windows"}` -- the
same dict the av_transit branch used to build inline. No logic changed,
only relocated; every comment/docstring note from the original block
moved with it (CURRENT-Antardasha-not-Mahadasha rationale, fail-closed
`ValueError`, the ashtakavarga assembly `RuntimeError` wrap, the
scanner's own unwrapped `ValueError` for bad `transit_planet`, the
tiling-contract asserts, the Session 55 ranking-key product-decision
note, and the render-contract field-mapping note).

The av_transit domain branch now reads:
```python
payload = _build_av_timing_block(chart_data, transit_planet)
stub_caveats = ()
uncertainty_virupa = 0.0
uncertainty_days = 37.0
```
-- i.e. it calls the extracted helper directly and keeps its own
`stub_caveats`/`uncertainty_virupa`/`uncertainty_days` assignment exactly
as before (those are DomainChartProfile-level fields, not part of the
returned dict, so they stay outside the helper).

## Changes made

1. **`_build_av_timing_block(chart_data, transit_planet)`** (new,
   private, module-level, placed just above `build_domain_profile`):
   the extracted av_transit logic, verbatim. Docstring records its own
   FAIL-CLOSED posture (`ValueError`/`RuntimeError`/`AssertionError`
   propagate unwrapped) and a NOTE that this is caller's-choice --
   career_strength/current_dasha wrap it in try/except to degrade,
   av_transit's own domain branch lets it propagate.
2. **`career_strength` branch**: after its existing `stub_caveats`
   assembly, added:
   ```python
   try:
       payload["timing_enrichment"] = _build_av_timing_block(chart_data, "Saturn")
   except Exception as exc:
       stub_caveats = stub_caveats + (
           f"timing enrichment unavailable: {type(exc).__name__}: {exc}",
       )
   ```
   `uncertainty_virupa`/`uncertainty_days` assignments below this are
   completely untouched (still 2.0/59.0 Surbhi-override and 0.0
   respectively).
3. **`current_dasha` branch**: identical pattern, placed right after
   `stub_caveats = ()`. `uncertainty_days = 37.0` (current_dasha's own
   dasha-drift envelope) is unchanged and unrelated to the enrichment's
   own day-level resolution (which lives inside the
   `timing_enrichment` block itself, per the design -- not surfaced
   here, that's a formatter-step concern for later).
4. **`av_transit` domain branch**: reduced to a 4-line call into the
   shared helper (see above) plus a cross-reference comment pointing at
   the career_strength/current_dasha enrichment blocks' opposite
   (degrade, not fail-closed) posture.
5. Comment added on the av_transit branch and mirrored on both
   enrichment call sites, per the task's "cross-reference comment on
   both" instruction (Session 56 locked decision 2: degradation, not
   fail-closed, for the two enrichment call sites; fail-closed,
   unchanged, for the standalone domain).

`transit_planet` is hardcoded to `"Saturn"` at both enrichment call
sites (design point 1) -- independent of `build_domain_profile`'s own
`transit_planet` kwarg, which still only ever affects the `av_transit`
domain branch.

No formatter change: `timing_enrichment` is a new dict key that
`result_formatter.py` never reads (grepped every `profile.payload[...]`
site in that file before editing -- confirmed each formatter branch
indexes only its own known keys, never iterates or asserts on the
payload's full key set), so the key is inert for career_strength/
current_dasha until a future formatter step reads it, per design point 4.

## Manual verification (in-memory, no test file added)

Ran `build_domain_profile()` directly for Sulabh's real chart across all
3 relevant domains:
- `career_strength`: payload gained `timing_enrichment` (9 ranked
  sub_windows, `transit_planet="Saturn"`); `stub_caveats` unchanged
  (still just the pre-existing Ayana Bala Moon/Venus note);
  `uncertainty_virupa=2.0`, `uncertainty_days=0.0` -- both unchanged.
- `current_dasha`: payload gained `timing_enrichment`;
  `uncertainty_days=37.0` unchanged.
- `av_transit`: payload keys still exactly
  `{"transit_planet", "dasha_envelope", "sub_windows"}` -- no
  `timing_enrichment` key on this domain itself (design point 1: the
  key is added to career_strength/current_dasha only), same 9
  sub_windows as before the refactor.

## Suite

**2943 passed, 3 skipped, 0 failed** -- zero delta, exactly as expected.
`test_orchestrator_e2e.py::test_ashtakavarga_routes_to_av_transit_tier2`
(the av_transit e2e guard) passed unchanged, confirming the extraction
produced a byte-identical av_transit payload. No test moved; nothing
else touched.
