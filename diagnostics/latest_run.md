# Session 56: render timing_enrichment in _format_career()/_format_dasha()

One file changed: `agent/infra/result_formatter.py`. No chart_profile,
router, orchestrator, or test file touched, per scope.

## Read-first finding: extraction, as expected

`_format_av_transit()`'s envelope/sub_windows rendering (JD -> "D Mon
YYYY", sub_windows field-mapping with rank order preserved) was directly
reusable logic, not directly callable as a function (it was inlined).
**Extracted** it into a new private module-level helper,
`_render_av_timing(block: dict) -> dict`, taking the raw
`{"transit_planet", "dasha_envelope", "sub_windows"}` shape (exactly
`chart_profile._build_av_timing_block()`'s return contract, Session 56's
prior change) and returning the identical 3-key rendered dict
`_format_av_transit()` used to build inline. This is cleaner than
duplication, as expected -- confirmed by grepping the payload key set
`_format_av_transit()` used to build (`transit_planet`, `dasha_envelope`
with `mahadasha_lord`/`antardasha_lord`/`start`/`end`, `sub_windows` with
`rank`/`start`/`end`/`sign`/`bav_bindus`/`sav_bindus`/`bav_band`/
`sav_band`/`verdict`/`kakshya_lord`) against what design point 2 asks the
enrichment block to carry -- identical field-for-field.

`_format_av_transit()` now: indexes `sub_windows` directly (unchanged
never-collapse check, same `ValueError` message), then calls
`_render_av_timing(profile.payload)` for the rest. The 8-test formatter
file (`tests/infra/test_result_formatter_av_transit.py`) is the guard,
per the task -- **passed unchanged**, plus a manual real-chart check
(below) confirming the av_transit domain's own `answer_payload`/
`sources`/`demotion_reason`/`tier` are byte-identical to pre-refactor
output (no `resolution_note` leak).

## Verification of the "no live test carries the key" claim (per instructions)

`grep -rn "timing_enrichment" tests/ agent/` -- **zero hits in any test
file**, only the 3 hits already committed in `chart_profile.py` from the
prior session. Claim confirmed true; proceeded without a STOP.

(Caveat worth flagging: no *test* references the key, but
`chart_profile.py`'s builder now attempts enrichment unconditionally for
every real `career_strength`/`current_dasha` call -- so
`test_orchestrator_e2e.py`'s existing real-chart e2e tests for those two
domains DO now exercise this new render path for real on every run, they
just don't assert on the new key. Manually verified this end-to-end with
`answer_question()` for both domains against Sulabh's real chart, below --
both rendered `timing_enrichment` successfully with no exceptions.)

## Changes made

1. **`_TIMING_ENRICHMENT_RESOLUTION_NOTE`** (new module constant): fixed
   disclosure string (day-level sub-window resolution + ±37-day envelope
   drift), rendered ONLY inside a `timing_enrichment` block -- comment
   states the GOLDEN STAKE GUARD explicitly: never appended to either
   domain's top-level `demotion_reason`.
2. **`_render_av_timing(block)`** (new, private, shared): the extracted
   render logic, byte-identical to what `_format_av_transit()` built
   inline before. Returns the bare 3-key dict; callers that want the
   enrichment's 4th key (`resolution_note`) add it themselves on the
   returned dict -- this function never adds it, so `_format_av_transit()`
   calling it directly can never accidentally pick it up.
3. **`_format_career()`**: after its existing `answer_payload` assembly
   (unchanged), added an enrichment block: `profile.payload.get(
   "timing_enrichment")` (`.get()`, per design point 1 -- key legitimately
   absent on builder-side enrichment failure); if present AND its
   `sub_windows` is non-empty, renders via `_render_av_timing()`, adds
   `resolution_note`, sets `answer_payload["timing_enrichment"]`, and
   extends `sources` to `("shadbala", "bhava_bala", "ashtakavarga",
   "av_transit_scorer", "av_transit_scanner")`. If absent (or, as a
   safety net, present-but-empty), `answer_payload`/`sources` are
   untouched -- byte-identical to pre-Session-56 output. `tier`/
   `demotion_reason` (both fixed: `TIER_2_RANGE`/`None`) are completely
   unaffected either way.
4. **`_format_dasha()`**: identical pattern, `sources` base
   `("vimshottari_dasha",)` extended the same way when present.
   `tier`/`demotion_reason` (near-boundary logic, unrelated to
   enrichment) unaffected.
5. **`_format_av_transit()`**: reduced to the never-collapse check +
   `_render_av_timing(profile.payload)` call; its own `sources`/
   `demotion_reason`/`tier` construction untouched.

### GOLDEN STAKE GUARD reconciliation (flagging a wording tension, resolved)

The task's design point 3 lists `sources` among the fields that must be
"byte-identical to pre-change output," while design point 5 explicitly
instructs appending to `sources` when the block renders. Read these as
consistent, not contradictory: byte-identical holds whenever the
enrichment key is absent (every pre-existing test scenario, and any real
call where the builder's enrichment attempt failed); point 5's append
only fires in the new, additive, present case. Implemented per point 5
(the more specific instruction) with a comment on both call sites noting
this reading. No existing test asserts an exact `sources` tuple for
`career_strength`/`current_dasha` (grepped `tests/` for `.sources` before
editing -- only hit was `test_orchestrator_e2e.py`'s REFUSAL-case
`result.sources == ()` check, unrelated), so this was safe.

## Manual verification (real Sulabh chart, full `answer_question()` path)

- `career_strength` ("How is my career and job strength?"): `sources` =
  `('shadbala', 'bhava_bala', 'ashtakavarga', 'av_transit_scorer',
  'av_transit_scanner')`; `answer_payload` gained `timing_enrichment`
  (`dasha_envelope`, `resolution_note`, `sub_windows` x9, `transit_planet`);
  `demotion_reason` still the pre-existing career T2 envelope text
  (router-merged) -- no enrichment language appended.
- `current_dasha` ("What dasha period am I in right now?"): `sources` =
  `('vimshottari_dasha', 'ashtakavarga', 'av_transit_scorer',
  'av_transit_scanner')`; `answer_payload` gained `timing_enrichment`;
  `demotion_reason` still the pre-existing ±37-day dasha text -- no
  enrichment language appended.
- `av_transit` (direct `build_domain_profile`/`format_answer` call, real
  chart): `answer_payload` keys still exactly `{transit_planet,
  dasha_envelope, sub_windows}` (3, not 4 -- no `resolution_note` leak);
  `sources` still exactly the original 4-tuple; `demotion_reason`/`tier`
  unchanged.

## Suite

**2943 passed, 3 skipped, 0 failed** -- zero delta, exactly as expected.
`test_result_formatter_av_transit.py`'s all 8 tests passed unchanged
(the refactor guard). No test moved; nothing else touched.
