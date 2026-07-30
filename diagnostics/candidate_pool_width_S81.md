# Candidate pool width fix — measurement (S81)

`palm_reading._PAGE_FILTER_CANDIDATE_N` is now `463` (was `20`, commit `d017543`). `_FEATURE_PAGE_FILTER_ENABLED` stays `False` globally in this measurement — module state is never mutated. OFF = plain unfiltered search at n=20 (continuity with prior S81 probes). ON = a SEPARATE live search at n=463 (the new production pool width), page-range-filtered, ranked in score order — this is a genuine second query per feature, not a re-slice of the OFF pool, because the pool width itself is what changed.

## Pre-search guard (all 10 registry features)

- **life line**: quality=`deep / a prominent line curves around the base of the thumb` — PASSED all 3 assertions
- **head line**: quality=`deep / this line runs horizontally across the palm` — PASSED all 3 assertions
- **heart line**: quality=`deep / the heart line is visible` — PASSED all 3 assertions
- **fate line**: quality=`barely visible / moderately deep / there is no clearly visible fate line in the image` — PASSED all 3 assertions
- **sun line**: quality resolved to None — SKIPPED.
- **thumb**: quality=`medium relative size / medium size / the thumb is of moderate length and appears to have a wide angle of separation from the hand` — PASSED all 3 assertions
- **fingers**: quality=`long relative to the palm / slightly longer than the palm / the fingers are of moderate length. the index finger is slightly shorter than the middle finger` — PASSED all 3 assertions
- **mount of venus**: quality=`developed / the mounts of venus (base of the thumb) and jupiter (below the index finger) appear slightly raised` — PASSED all 3 assertions
- **mount of jupiter**: quality=`the mounts of venus (base of the thumb) and jupiter (below the index finger) appear slightly raised` — PASSED all 3 assertions
- **markings/other features**: quality resolved to None — SKIPPED.

## Target-chunk features

| feature | chunk_id | rank OFF | rank ON | gate (<=3) |
|---|---|---|---|---|
| fate line | `cheiroslanguageo00chei_1_p165_c2` | 14 | 8 | FAIL |
| fate line | `cheiroslanguageo00chei_1_p163_c1` | 3 | 3 | PASS |
| head line | `cheiroslanguageo00chei_1_p145_c0` | >20 | 6 | FAIL |
| heart line | `cheiroslanguageo00chei_1_p160_c3` | >20 | 8 | FAIL |
| heart line | `cheiroslanguageo00chei_1_p159_c2` | 5 | 5 | FAIL |
| heart line | `cheiroslanguageo00chei_1_p160_c1` | 6 | 6 | FAIL |

## Heart line, flag ON — top 6 in-range chunks

| rank | chunk_id | score |
|---|---|---|
| 1 | `cheiroslanguageo00chei_1_p159_c3` | 0.6088 |
| 2 | `cheiroslanguageo00chei_1_p160_c2` | 0.6067 |
| 3 | `cheiroslanguageo00chei_1_p161_c0` | 0.5970 |
| 4 | `cheiroslanguageo00chei_1_p156_c0` | 0.5775 |
| 5 | `cheiroslanguageo00chei_1_p159_c2` | 0.5636 |
| 6 | `cheiroslanguageo00chei_1_p160_c1` | 0.5296 |

## Top-3 change check, all 10 features

| feature | top-3 OFF | top-3 ON | changed? |
|---|---|---|---|
| life line | `cheiroslanguageo00chei_1_p135_c0`, `cheiroslanguageo00chei_1_p134_c1`, `cheiroslanguageo00chei_1_p134_c0` | `cheiroslanguageo00chei_1_p135_c0`, `cheiroslanguageo00chei_1_p134_c1`, `cheiroslanguageo00chei_1_p134_c0` | no |
| head line | `cheiroslanguageo00chei_1_p123_c0`, `cheiroslanguageo00chei_1_p151_c2`, `cheiroslanguageo00chei_1_p135_c2` | `cheiroslanguageo00chei_1_p151_c2`, `cheiroslanguageo00chei_1_p146_c2`, `cheiroslanguageo00chei_1_p147_c0` | YES |
| heart line | `cheiroslanguageo00chei_1_p159_c3`, `cheiroslanguageo00chei_1_p160_c2`, `cheiroslanguageo00chei_1_p161_c0` | `cheiroslanguageo00chei_1_p159_c3`, `cheiroslanguageo00chei_1_p160_c2`, `cheiroslanguageo00chei_1_p161_c0` | no |
| fate line | `cheiroslanguageo00chei_1_p165_c1`, `cheiroslanguageo00chei_1_p165_c0`, `cheiroslanguageo00chei_1_p163_c1` | `cheiroslanguageo00chei_1_p165_c1`, `cheiroslanguageo00chei_1_p165_c0`, `cheiroslanguageo00chei_1_p163_c1` | no |
| sun line | (none — skipped) | (none) | no |
| thumb | `cheiroslanguageo00chei_1_p87_c0`, `cheiroslanguageo00chei_1_p88_c1`, `cheiroslanguageo00chei_1_p89_c2` | `cheiroslanguageo00chei_1_p87_c0`, `cheiroslanguageo00chei_1_p88_c1`, `cheiroslanguageo00chei_1_p89_c2` | no |
| fingers | `cheiroslanguageo00chei_1_p98_c1`, `cheiroslanguageo00chei_1_p96_c1`, `cheiroslanguageo00chei_1_p96_c0` | `cheiroslanguageo00chei_1_p96_c1`, `cheiroslanguageo00chei_1_p96_c0`, `cheiroslanguageo00chei_1_p95_c0` | YES |
| mount of venus | `cheiroslanguageo00chei_1_p112_c0`, `cheiroslanguageo00chei_1_p111_c1`, `cheiroslanguageo00chei_1_p111_c0` | `cheiroslanguageo00chei_1_p112_c0`, `cheiroslanguageo00chei_1_p111_c1`, `cheiroslanguageo00chei_1_p111_c0` | no |
| mount of jupiter | `cheiroslanguageo00chei_1_p112_c0`, `cheiroslanguageo00chei_1_p111_c1`, `cheiroslanguageo00chei_1_p113_c0` | `cheiroslanguageo00chei_1_p112_c0`, `cheiroslanguageo00chei_1_p111_c1`, `cheiroslanguageo00chei_1_p113_c0` | no |
| markings/other features | (none — skipped) | (none) | no |

**CHANGED**: head line, fingers
- `fingers` change is EXPECTED, not a defect: its `95-97` page range is known wrong (excludes page 98, where the S68-flagged target chunk `p98_c1` lives) — already logged in `diagnostics/feature_page_filter_S81.md` (commit `d017543`) and explicitly out of scope for this task (fingers range fix is separate).
- `head line` change is the filter working as designed, not a range error: OFF's top-3 (`p123_c0`, `p151_c2`, `p135_c2`) includes two chunks outside the `145-155` head chapter (p.123, p.135); ON correctly excludes them and surfaces `p151_c2`/`p146_c2`/`p147_c0`, all within range. This is the intended precision gain from widening the pool -- previously (pool=20) `p145_c0` was unreachable at any rank; now it surfaces at rank 6 within the correct chapter.

## Live spot-check: real `_search_with_page_filter()` vs measurement

- feature: `fate line`
- measurement top-3 ON: ['cheiroslanguageo00chei_1_p165_c1', 'cheiroslanguageo00chei_1_p165_c0', 'cheiroslanguageo00chei_1_p163_c1']
- real `_search_with_page_filter()` top-3 (fresh live call): ['cheiroslanguageo00chei_1_p165_c1', 'cheiroslanguageo00chei_1_p165_c0', 'cheiroslanguageo00chei_1_p163_c1']
- verdict: MATCH

## Regression suite (flag OFF, the shipped default)

Run separately (`python -m pytest -q`). Flag stays at its module default (`False`); `_retrieve_per_feature` never calls `_search_with_page_filter` while OFF, so the pool-width change is unreachable in this run — verifies byte-identical-when-OFF, not just states it.

```
3341 passed, 7 skipped, 1 xpassed, 1 warning in 74.04s (0:01:14)
```

Baseline: 3341 passed / 0 failed / 7 skipped / 1 xpassed. Result: MATCH — 0 delta.
