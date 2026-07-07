# Session 55: av_transit builder in build_domain_profile() (chart_profile.py)

**Changed file:** `agent/infra/chart_profile.py` only, plus the benign
`diagnostics/calc_router_stage2.log` growth from running the suite. No
other file touched (calc_router.py, orchestrator.py, result_formatter.py,
chart_calculator.py, scanner/scorer/ashtakavarga modules, and all test
files untouched, as required). `_VALID_DOMAINS` deliberately NOT extended
with "av_transit" -- per task instructions, that's router-wiring's job,
a later step. This means the new branch is currently unreachable through
the function's own domain gate (verified in-memory below, not by editing
the file).

## AvTransitSegment / AvTransitScore field mapping (as found)

`AvTransitSegment` (`av_transit_scanner.py:106-112`): `start_jd`,
`end_jd`, `sign`, `kakshya_index` (redundant with `score.kakshya_index`,
unused here), `score: AvTransitScore`.

`AvTransitScore` (`av_transit_scorer.py:147-159`): `transit_planet`,
`transit_sign`, `bav_rekhas`, `bav_band` (`BavBand` enum), `bav_intensity`,
`sav_value`, `sav_band` (`AvVerdictBand` enum), `verdict` (`AvVerdictBand`
enum), `kakshya_index`, `kakshya_lord`, `kakshya_has_rekha`.

Mapping applied to the frozen render-contract keys:
| render-contract key | source |
|---|---|
| `bav_bindus` | `seg.score.bav_rekhas` |
| `sav_bindus` | `seg.score.sav_value` |
| `bav_band` | `seg.score.bav_band.value` (Enum -> str) |
| `sav_band` | `seg.score.sav_band.value` (Enum -> str) |
| `verdict` | `seg.score.verdict.value` (Enum -> str) |
| `kakshya_lord` | `seg.score.kakshya_lord` (verbatim, already `None` for Sun/Mars) |
| `sign` | `seg.sign` |
| `start_jd`/`end_jd` | `seg.start_jd`/`seg.end_jd` |

## Tiling-contract confirmation

`scan_av_transit_segments()`'s own docstring (`av_transit_scanner.py:207-211`,
Returns clause) states segments are "contiguously tiling [start_jd, end_jd]
with no gaps or overlaps." Confirmed by reading `_daily_state_segments()`
(lines 148-181): the first day's segment starts at `start_jd` and the loop's
final segment's end is set to the window's own `end_jd` (line 179:
`seg_end = days[run_end + 1] if run_end + 1 < n else end_jd`). No clipping
logic was added -- instead, two `assert` statements pin this contract at
the call site (first segment start == envelope start_jd, last segment end
== envelope end_jd), so a future scanner-contract change fails loudly
here rather than silently mis-scoping the envelope. Both asserts passed in
the smoke test below.

## transit_planet validation

Confirmed via read + smoke test: `scan_av_transit_segments()` calls
`_validate_transit_planet()`, which delegates to `score_av_transit()`'s own
planet-identity/exclusion check. No duplicate validation was added in
`chart_profile.py` -- the `ValueError` propagates unwrapped (not
re-wrapped into `RuntimeError`), per design item 8.

## Change summary

1. New imports: `compute_bav`/`compute_bav_contributors`/`compute_sav`
   from `agent.calculations.ashtakavarga.ashtakavarga`;
   `scan_av_transit_segments` from
   `agent.calculations.transits.av_transit_scanner`.
2. New module constant `_AV_TRANSIT_NATAL_PLANETS` (7 classical planets,
   same set/order as `test_av_transit_scanner.py`'s own `_PLANETS`,
   independently duplicated per this project's convention).
3. `build_domain_profile()` signature gains `transit_planet: str =
   "Saturn"` (keyword-only, same domain-scoped-kwarg precedent as
   `partner_chart_data`/`primary_role`) -- docstring updated (Args,
   Raises, domain list).
4. New `elif domain == "av_transit":` branch, inserted between
   `current_dasha` and the `else:  # sade_sati` fallback:
   - Envelope = current Antardasha read directly from
     `chart_data["dasha"]` (JD keys from commit 394ad29). Fail-closed
     `ValueError` when `current_antardasha` is `None` -- verified by
     smoke test (message names the fail-closed reasoning, never
     substitutes the Mahadasha envelope).
   - Natal AV tables assembled via the `sulabh_natal_tables` fixture
     pattern (Lagna + 7 planets' signs -> `compute_bav` -> `compute_sav`
     -> `compute_bav_contributors`), wrapped in `try/except` ->
     `RuntimeError` (this file's existing convention for natal-table
     computation failures).
   - `scan_av_transit_segments()` called unwrapped (no try/except) so its
     `ValueError`s (bad `transit_planet`, bad window) and `EphemerisError`
     propagate as-is.
   - `sub_windows` = ALL returned segments, no favorability filtering
     (locked rider).
   - Ranking: `sorted(segments, key=lambda seg: (-seg.score.sav_value,
     -seg.score.bav_rekhas, seg.start_jd))`, `rank` assigned 1..n via
     `enumerate(..., start=1)`. Comment explicitly attributes the sort
     key to a Session 55 product decision extending the Session 54
     SAV-dominance lock, NOT to PVR (PVR ch.25 is cited only for the
     band thresholds already applied inside `score_av_transit()`).
   - `uncertainty_virupa = 0.0` (BAV/SAV are integer bindu counts, no
     virupa axis), `uncertainty_days = 37.0` (same axis as
     `current_dasha`'s Antardasha drift -- this domain's window IS the
     current Antardasha). `stub_caveats = ()`.

## Smoke test (ad hoc, in-memory `_VALID_DOMAINS` patch only -- file NOT edited)

Ran `build_domain_profile("av_transit", <Sulabh chart>, ..., transit_planet="Saturn")`
directly (bypassing only the module-level domain gate in-process, to
verify the new branch without touching the file):
- Envelope: `{'mahadasha_lord': 'Ketu', 'antardasha_lord': 'Venus',
  'start_jd': 2461038.15..., 'end_jd': 2461464.28...}`.
- 9 sub_windows returned, ranks 1..9, `sav_bindus` strictly non-increasing
  by rank (dominance-ranking confirmed).
- Both tiling asserts passed (first segment start == envelope start,
  last segment end == envelope end).
- Fail-closed path (`current_antardasha=None`) raised the expected
  `ValueError`.
- `transit_planet="Mercury"` raised the scorer's own exclusion
  `ValueError`, unwrapped, propagated through unchanged.

## Suite count

Full suite: `2943 passed, 3 skipped, 1 warning` -- **identical** to the
pre-change baseline. Zero delta, exactly as expected (branch unreachable
via any live call path until router wiring adds "av_transit" to
`_VALID_DOMAINS`).

## Sequencing status

Formatter (done) -> convergence wiring / builder (this session, done) ->
router (next). All three payload-producing/consuming pieces
(`result_formatter.py`'s render branch, `chart_profile.py`'s builder
branch, `av_transit_scanner.py`/`av_transit_scorer.py`) now exist and are
smoke-test-verified to compose correctly end-to-end; only the router's
domain classification and `_VALID_DOMAINS` gate remain to make this
domain live.
