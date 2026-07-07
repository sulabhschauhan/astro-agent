# Session: test_av_transit_scanner.py -- structural invariants + ingress anchors

**New file:** `tests/calculations/transits/test_av_transit_scanner.py`
(only file changed besides the benign `calc_router_stage2.log` growth
from running the suite; `git status` confirms it). No production code
touched.

**Target:** `scan_av_transit_segments()` / `AvTransitSegment` (added last
session, `agent/calculations/transits/av_transit_scanner.py`).

**Setup:** Sulabh's natal tables via the live pipeline, same path as
test_av_transit_scorer.py; JD conversion via `swisseph.julday()`, matching
test_sade_sati.py's existing convention. Transit-planet sign detection is
natal-independent (it's the transiting planet's own ephemeris position),
so Sulabh's chart is reused here purely for cross-file consistency, not
because Layer 2's anchors depend on it.

**Verified before writing:** ran an inline smoke script confirming all
structural invariants and all 4 ingress-anchor dates against the live
scanner BEFORE writing any assertion into the test file -- per this
repo's "verify task prompts against code" convention. One correction from
the raw prompt wording: the Saturn window (1 Jan 2020 -> 1 Jul 2023)
starts ~3 weeks before Saturn's actual Sagittarius->Capricorn ingress
(24 Jan 2020), so the raw collapsed-sign-run list has 5 runs (a leading
partial Sagittarius sliver, then Cp/Aq/Cp/Aq), not 4 -- the test filters
to Capricorn/Aquarius runs only before asserting "exactly 4", documented
inline as excluding a window-edge artifact, not a real ingress.

## Test layers (10 new tests)
- **(a)-(c) Saturn structural invariants** (3 tests, shared helper
  functions `_assert_contiguous_tiling` / `_assert_adjacency_legal` /
  `_assert_score_consistency` also reused by Jupiter in Layer 3): tiling
  with no gaps/overlaps and correct window-edge alignment; every state
  change is either a same-sign kakshya +/-1 step or an exact 7->0
  (direct) / 0->7 (retrograde) kakshya transition between zodiacally
  adjacent signs; every segment's score.kakshya_index/transit_sign agree
  with the segment's own fields.
- **(d) retrograde triple-pass** (1 test, hard assert): at least one
  (sign, kakshya_index) state recurs across 3+ non-consecutive segments
  in the 2020-2023 Saturn window -- confirmed 3 for (Capricorn, 1) before
  writing the assertion.
- **Layer 2 ingress anchors** (1 test): the 4 Capricorn/Aquarius maximal
  sign runs (Sagittarius edge sliver excluded) fall within +/-2 days of
  24 Jan 2020 / 29 Apr 2022 / 12 Jul 2022 / 17 Jan 2023 -- measured diffs
  were 0, 0, 0, and 1 day respectively, well inside tolerance. Provenance:
  cross-checked against mainstream Vedic transit-date sources AND this
  repo's own test_sade_sati.py, whose independently-computed
  `expected_macro_start = swe.julday(2020, 1, 24, 0.0)` pins the same
  Sagittarius->Capricorn ingress via a completely different code path
  (the rising/setting macro-envelope scan, not this scanner).
- **(e) Jupiter structural-only** (1 test, Jan-Jul 2023): same (a)-(c)
  invariants, no anchor pins.
- **(f) Sun sign-level-only** (3 tests, Feb-May 2021): kakshya_index is
  None on both segment and score for every segment; tiling; ~3-5 sign
  runs (Sun's ~30-day cadence over a 3-month window, with edge-alignment
  slack) -- measured 4.
- **(g) error path** (1 test): Moon raises ValueError via the scanner's
  delegated fail-closed exclusion check.

## Test tallies
- New file alone: `10 passed` in isolation.
- Full suite: `2933 passed, 3 skipped, 1 warning in 115.73s` (was 2923
  passed, 3 skipped before this session; 2923 + 10 = 2933, exact).

No source or module logic changed.
