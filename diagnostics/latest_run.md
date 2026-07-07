# Session 55: result_formatter.py -- av_transit render branch (formatter step of Session 54 sequencing lock)

**Changed files:** `agent/infra/result_formatter.py` only, plus the benign
`diagnostics/calc_router_stage2.log` growth from running the suite. No
other file touched (chart_profile.py, calc_router.py, orchestrator.py,
and all test files untouched, as required).

**What changed:** added a 5th domain render branch, `"av_transit"`, to
`format_answer()`'s dispatcher, plus its own `_format_av_transit()`
function and `_AV_TRANSIT_DEMOTION_REASON` constant. This branch is
currently **unreachable in any live path** -- no router keyword, no
`chart_profile.py` builder, and no `_VALID_DOMAINS` entry exist yet
(Session 54 Conflict A resolution: formatter lands first, convergence
wiring and router are separate later changes). It renders the frozen
payload contract (`transit_planet`, `dasha_envelope`, ranked
`sub_windows`) against a synthetic profile only, once that convergence
layer exists.

**Design decisions carried through, per the frozen contract:**
- Tier is hardcoded `AnswerTier.TIER_2_RANGE`, unconditionally -- payload-
  property principle (P7.0c precedent), same reasoning as `current_dasha`
  (dated envelope + sub-window claims always carry drift language),
  opposite of `sade_sati`'s T1-only branch.
- `demotion_reason` is a fixed string covering both uncertainty axes: the
  existing ±37-day Antardasha envelope drift (same axis as
  `_DASHA_DEMOTION_REASON`) AND the day-level resolution of sub-window
  boundaries (daily-step scanner, no sub-day bisection) -- these are
  orthogonal and both are disclosed in one string, modeled on the
  existing `_BOUNDARY_NOTE`/`_DASHA_DEMOTION_REASON` register.
- All JD fields (`dasha_envelope.start_jd`/`end_jd`, each sub-window's
  `start_jd`/`end_jd`) go through the existing `_format_jd()` -- no new
  conversion path.
- Sub-window rank order is preserved verbatim (no re-sort) -- the
  convergence layer owns ranking, this file only re-renders dates and
  carries all scoring fields (`bav_bindus`, `sav_bindus`, `bav_band`,
  `sav_band`, `verdict`, `kakshya_lord`) through unchanged.
- **Never-collapse guard** (Session 54 locked decision 2): an empty
  `sub_windows` list raises `ValueError` citing the locked decision by
  name, rather than rendering a dasha envelope with nothing underneath
  it -- a designed fail-closed path, not defensive padding.
- Missing/malformed payload keys are not defended against -- direct dict
  indexing raises `KeyError`/`ValueError` with the offending key,
  matching the existing convention in `_format_marriage`/`_format_dasha`
  (never a partial render).
- `sources` tuple: `("ashtakavarga", "av_transit_scorer",
  "av_transit_scanner", "vimshottari_dasha")` -- the three AV-transit
  modules plus the existing dasha-provenance source used by
  `_format_dasha`.

**Not done (explicitly out of scope, per prompt):** no router keywords,
no `orchestrator._VALID_DOMAINS` entry, no `chart_profile.py` builder, no
test file writes or edits, no ride-along fixes elsewhere in the file
(the Rahu/Ketu unknown-planet message carry-forward in
`av_transit_scorer.py` was left untouched, as instructed).

## Test tallies
- Full suite: `2935 passed, 3 skipped, 1 warning` -- **identical** to the
  pre-change baseline (2935 passed / 3 skipped). Zero test-count delta,
  exactly as expected for a branch with no test coverage yet and no live
  router path reaching it.

No production/calculation module logic changed; this is additive,
currently-dead render code only.
