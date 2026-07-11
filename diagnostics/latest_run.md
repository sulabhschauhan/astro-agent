# P7 Muhurta wiring, step 6 of 7: test_orchestrator_muhurta.py

Session 64. New file `tests/infra/test_orchestrator_muhurta.py` -- the
3-layer router-provenance/oracle/full-chain test for muhurta_window,
adapting the arudha_lagna/upapada_lagna precedent for wall-clock
coupling. NEW TEST FILE ONLY, no source edits. NOT committed -- design
chat ratifies the Layer B measured values (below) before they become
asserts next prompt. (Plan renumbered per the task: this is step 6 of 7;
step 7 = golden rows + dead `_KNOWN_GAPS` deletion + baseline freeze.)

## MEASURE-FIRST (per CLAUDE.md Working Style #2/#3): ran once, before writing any assertion

### Layer A -- router provenance (deterministic)

```
CLEAN "what is an auspicious muhurta for me this week"
  domain=muhurta_window tier=TIER_3_MUHURTA confidence=0.6666666666666666 (2/3)
  route=stage1 demotion=None requires_partner=False   sentinel_calls=0

MISS "muhurta"
  domain=None tier=REFUSAL confidence=0.0 route=stage2   _stage2_fallback_calls=1
```

CLEAN scores 2 keyword hits ("auspicious" + "muhurta") -> min(2,3)/3 =
0.667, clears the 0.4 floor and 0.15 margin, resolves at Stage 1 with the
recording sentinel NEVER invoked. MISS scores 1 hit -> 0.333, below floor
-> `route_question()` enters the `_stage2_fallback` path.

### Layer B -- 4-chart structural, PINNED JD (S24 anchor, 2026-06-20 18:30 UTC)

```
Sulabh:   natal=(7,15)  [Scorpio/Vishakha]      count=11 span=7.0 contiguous=True tiers={T1,T2,T3} tier1_count=4
David:    natal=(4,9)   [Leo/Magha]             count=11 span=7.0 contiguous=True tiers={T1,T2,T3} tier1_count=2
Surbhi:   natal=(10,23) [Aquarius/Shatabhisha]  count=11 span=7.0 contiguous=True tiers={T1,T2,T3} tier1_count=3
Sheridan: natal=(0,0)   [Aries/Ashwini]         count=11 span=7.0 contiguous=True tiers={T1,T2,T3} tier1_count=2
```

All 4 charts: 11 windows, span exactly 7.0, fully contiguous, all three
tier values present. (Every chart landing on count=11 at this particular
anchor is a coincidence of this week's transit boundary structure, not an
invariant -- the count is chart+JD-specific, which is exactly why it is a
DEFERRED value-assert, see below.)

### Sulabh full window table @ _PINNED_JD -- the ratified-run candidate (NOT yet asserted)

```
domain=muhurta_window tier=TIER_3_MUHURTA sources=('muhurta_scorer.py',)
stub_caveats=() demotion=None uncertainty_virupa=0.0 uncertainty_days=0.0
summary={'tier1_window_count': 4, 'earliest_tier1_start': '21 Jun 2026 04:01 UTC'}
window_count=11

idx | start (UTC)          | end (UTC)            | tier   | fav | warnings
 0  | 20 Jun 2026 18:30     | 21 Jun 2026 04:01    | TIER_2 |  1  | ()
 1  | 21 Jun 2026 04:01     | 21 Jun 2026 10:10    | TIER_1 |  2  | ()
 2  | 21 Jun 2026 10:10     | 22 Jun 2026 04:52    | TIER_1 |  2  | ()
 3  | 22 Jun 2026 04:52     | 23 Jun 2026 06:24    | TIER_2 |  1  | ()
 4  | 23 Jun 2026 06:24     | 23 Jun 2026 19:23    | TIER_1 |  2  | ()
 5  | 23 Jun 2026 19:23     | 24 Jun 2026 08:29    | TIER_2 |  1  | ()
 6  | 24 Jun 2026 08:29     | 25 Jun 2026 10:59    | TIER_2 |  1  | ()
 7  | 25 Jun 2026 10:59     | 26 Jun 2026 07:03    | TIER_3 |  0  | ('Janma Tara',)
 8  | 26 Jun 2026 07:03     | 26 Jun 2026 13:46    | TIER_2 |  1  | ('Janma Tara', 'Janma Rashi')
 9  | 26 Jun 2026 13:46     | 27 Jun 2026 16:41    | TIER_1 |  2  | ('Janma Rashi',)
10  | 27 Jun 2026 16:41     | 27 Jun 2026 18:30    | TIER_2 |  1  | ('Janma Rashi',)
```

This table is the candidate for the next prompt's value-asserts (window
count == 11, per-window tier sequence, summary tier1_window_count == 4,
the Janma Tara / Janma Rashi warning bands). **Design chat ratifies these
before they become asserts** -- this prompt ships STRUCTURAL asserts only.
Note both natal-warning paths fire in Sulabh's table (Janma Tara at
idx 7-8, Janma Rashi at idx 8-10), which is why Sulabh is the
hardest-case-first row: its Scorpio Moon-sign and Vishakha nakshatra both
recur inside this particular 7-day window.

## What the file asserts THIS prompt (structural only)

**Layer A (`TestLayerARouterProvenance`)** -- fully asserted (deterministic):
- `test_a1`: CLEAN -> Stage 1, domain=muhurta_window, tier=TIER_3_MUHURTA,
  confidence == approx(2/3), route=="stage1", demotion None,
  requires_partner False, recording sentinel `.calls == []`.
- `test_a2`: MISS -> monkeypatches `_stage2_fallback` ITSELF (a canned
  REFUSAL, never delegates), asserts it was called once, that
  `route_question` returned that result, and that the recorded `best_score`
  was below `_CONFIDENCE_FLOOR`. This is the DELIBERATE departure from
  arudha/upapada's a2 (which pass a `_RecordingClient` and rely on the
  record landing before `_stage2_classify`'s fail-closed swallow) -- per
  the task's own S50 P7.2e note ("do NOT patch `_stage2_classify`; its
  fail-closed swallows the signal"). No real OpenAI call is made.

**Layer B (`TestLayerBRealChartOracle`, PINNED JD)** -- structural only:
- `test_sulabh_structural_and_natal_ids`: natal ids **asserted == (7, 15)**
  (closes step 1's verify-at-e2e obligation), domain/tier/sources/
  stub_caveats/uncertainty fields, plus the shared window-structure
  asserter (non-empty; `windows[0].start_jd == _PINNED_JD`;
  `windows[-1].end_jd == _PINNED_JD + 7.0`; contiguity; each window
  non-zero-width and ascending; every per-window tier in
  {"TIER_1","TIER_2","TIER_3"}; total span == 7.0 EXACT; summary key-set).
- `test_david/surbhi/sheridan_structural`: natal ids derived in valid
  range (0..11 sign, 0..26 nakshatra), domain/tier, same window-structure
  asserter. David first per HARDEST-CASE-first.
- DEFERRED (value-asserts, next prompt after ratification): window
  count == 11, the per-window tier sequence, summary
  `tier1_window_count`, the warning bands. The observed table above is the
  ratification candidate; none of its chart-specific literals are asserted
  yet.

**Layer C (`TestLayerCFullChain`)** -- STRUCTURAL, not byte-equal:
- `test_sulabh_full_chain_structural`: full `answer_question()` chain.
  domain, tier==TIER_3_MUHURTA, route=="stage1", demotion None, sources,
  stub_caveats==(), uncertainty 0.0/0.0, plus the shared window-structure
  asserter with `expected_start_jd=None` and `exact_span=False` (span
  7.0 +/- 1e-6). Byte-equality vs Layer B is impossible BY DESIGN --
  `answer_question()` samples its own `datetime.now(timezone.utc)` for
  evaluated_at_jd (muhurta_window is the first wall-clock-anchored domain),
  so its window boundaries start at "now", not at `_PINNED_JD`. This is
  the documented departure from arudha/upapada's Layer C, which asserts
  full `result == expected` byte-equality (safe there because those
  domains are purely natal and evaluated_at_jd is genuinely unused).
  Monkeypatches `_stage2_classify` to raise -- proves Stage 2 never fires
  AND guarantees no accidental live OpenAI call.

## Test run

New file in isolation:
```
7 passed in 1.23s   ([_patch_stage2_openai] stub invocation count: 0 -- no live OpenAI call)
```

Full suite:
```
python -m pytest -q
3141 passed, 3 skipped, 0 failed  (81.31s)
```

Exactly 3134 (prior baseline) + 7 new tests, zero regressions. The
`[_patch_stage2_openai] stub invocation count: 5` on the full run is the
pre-existing count from OTHER Stage-2 tests in the suite -- unchanged by
this file (whose own isolated run showed count 0, confirming these 7
tests make no Stage 2 calls of their own).

## Not committed

Per constraint: `tests/infra/test_orchestrator_muhurta.py` remains
uncommitted in the working tree. Design chat ratifies the Layer B
measured values (the Sulabh table above) before the deferred value-asserts
land next prompt.
