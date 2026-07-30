# Page-range pre-filter measurement (flag OFF vs ON) — S81

`agent.interpretive.palm_reading._FEATURE_PAGE_FILTER_ENABLED` stays `False` globally in this measurement — module state is never mutated. ON figures below replicate `_search_with_page_filter`'s own filter condition over the SAME top-20 OFF candidate pool per feature (one search() call per feature, not two), so OFF vs ON differ only in the range filter, not in embedding-call jitter between separate live queries.

## Step 1 — registry keys and page-range map

`palm_reading._FEATURE_REGISTRY` (exact keys, registry order): `('life line', 'head line', 'heart line', 'fate line', 'sun line', 'thumb', 'fingers', 'mount of venus', 'mount of jupiter', 'markings/other features')`

`palm_reading._FEATURE_PAGE_RANGES` (loaded from `data/cheiro_feature_pages.json`):

| registry key | range | note |
|---|---|---|
| `life line` | 133-139 | LINE OF LIFE |
| `head line` | 145-155 | LINE OF HEAD (spans chapters VII, VIII, IX -- all head-line doctrine) |
| `heart line` | 156-161 | LINE OF HEART |
| `fate line` | 162-165 | LINE OF FATE |
| `sun line` | 166-170 | LINE OF SUN |
| `thumb` | 85-94 | THE THUMB |
| `fingers` | 95-97 | THE FINGERS |
| `mount of venus` | 111-113 | THE MOUNTS (no Venus-specific sub-range provided; the mounts chapter is a single 111-113 block covering all mounts) |
| `mount of jupiter` | 111-113 | THE MOUNTS (no Jupiter-specific sub-range provided; same 111-113 block as mount of venus) |
| `markings/other features` | null | No chapter in the S81 instructing prompt's range map corresponds to marks/crosses/stars/signs doctrine. 'GENERAL LINES' (120-132) is a distinct classical category (minor lines: Via Lascivia, girdle of Venus context, travel/influence lines etc.), not signs-and-marks doctrine -- mapping 'markings/other features' onto it would be a guess, not a verified range, and the instructing prompt explicitly says not to guess. Falls through to unfiltered retrieval at runtime (see palm_reading._search_with_page_filter). |

Mapped: 9/10. Null: ['markings/other features']

## Pre-search guard (all 10 registry features)

- **life line**: quality=`deep / a prominent line curves around the base of the thumb` — PASSED all 3 assertions
- **head line**: quality=`deep / this line runs horizontally across the palm` — PASSED all 3 assertions
- **heart line**: quality=`deep / the heart line is visible` — PASSED all 3 assertions
- **fate line**: quality=`barely visible / moderately deep / there is no clearly visible fate line in the image` — PASSED all 3 assertions
- **sun line**: quality resolved to None — SKIPPED (production would issue no query for this feature either; page-filter step never reached).
- **thumb**: quality=`medium relative size / medium size / the thumb is of moderate length and appears to have a wide angle of separation from the hand` — PASSED all 3 assertions
- **fingers**: quality=`long relative to the palm / slightly longer than the palm / the fingers are of moderate length. the index finger is slightly shorter than the middle finger` — PASSED all 3 assertions
- **mount of venus**: quality=`developed / the mounts of venus (base of the thumb) and jupiter (below the index finger) appear slightly raised` — PASSED all 3 assertions
- **mount of jupiter**: quality=`the mounts of venus (base of the thumb) and jupiter (below the index finger) appear slightly raised` — PASSED all 3 assertions
- **markings/other features**: quality resolved to None — SKIPPED (production would issue no query for this feature either; page-filter step never reached).

## Target-chunk features (fate line, head line, heart line)

| feature | chunk_id | rank OFF | rank ON | gate ON (<=3) |
|---|---|---|---|---|
| fate line | `cheiroslanguageo00chei_1_p165_c2` | 14 | 8 | FAIL |
| fate line | `cheiroslanguageo00chei_1_p163_c1` | 3 | 3 | PASS |
| head line | `cheiroslanguageo00chei_1_p145_c0` | >20 | >20 | FAIL |
| heart line | `cheiroslanguageo00chei_1_p160_c3` | >20 | >20 | FAIL |
| heart line | `cheiroslanguageo00chei_1_p159_c2` | 5 | 5 | FAIL |
| heart line | `cheiroslanguageo00chei_1_p160_c1` | 6 | 6 | FAIL |

## Other 7 features — top-3 displacement check

No target chunk is known for these 7 features. Reported: top-3 chunk_ids OFF (= production's actual gate output today) vs top-3 chunk_ids ON (= what the gate output would be if the flag were enabled), so any displacement is visible directly.

| feature | page range | top-3 OFF | top-3 ON | displaced? |
|---|---|---|---|---|
| life line | 133-139 | `cheiroslanguageo00chei_1_p135_c0`, `cheiroslanguageo00chei_1_p134_c1`, `cheiroslanguageo00chei_1_p134_c0` | `cheiroslanguageo00chei_1_p135_c0`, `cheiroslanguageo00chei_1_p134_c1`, `cheiroslanguageo00chei_1_p134_c0` | no |
| sun line | 166-170 | (none — feature skipped) | (none) | no |
| thumb | 85-94 | `cheiroslanguageo00chei_1_p87_c0`, `cheiroslanguageo00chei_1_p88_c1`, `cheiroslanguageo00chei_1_p89_c2` | `cheiroslanguageo00chei_1_p87_c0`, `cheiroslanguageo00chei_1_p88_c1`, `cheiroslanguageo00chei_1_p89_c2` | no |
| fingers | 95-97 | `cheiroslanguageo00chei_1_p98_c1`, `cheiroslanguageo00chei_1_p96_c1`, `cheiroslanguageo00chei_1_p96_c0` | `cheiroslanguageo00chei_1_p96_c1`, `cheiroslanguageo00chei_1_p96_c0`, `cheiroslanguageo00chei_1_p95_c0` | YES |
| mount of venus | 111-113 | `cheiroslanguageo00chei_1_p112_c0`, `cheiroslanguageo00chei_1_p111_c1`, `cheiroslanguageo00chei_1_p111_c0` | `cheiroslanguageo00chei_1_p112_c0`, `cheiroslanguageo00chei_1_p111_c1`, `cheiroslanguageo00chei_1_p111_c0` | no |
| mount of jupiter | 111-113 | `cheiroslanguageo00chei_1_p112_c0`, `cheiroslanguageo00chei_1_p111_c1`, `cheiroslanguageo00chei_1_p113_c0` | `cheiroslanguageo00chei_1_p112_c0`, `cheiroslanguageo00chei_1_p111_c1`, `cheiroslanguageo00chei_1_p113_c0` | no |
| markings/other features | null (no verified range) | (none — feature skipped) | (none) | no |

## Displacement summary

**DISPLACED**: fingers

**Note (evidence only, no action taken)**: the displaced chunk for `fingers` is `cheiroslanguageo00chei_1_p98_c1` — this is the SAME chunk `scripts/probe_fc_retrieval.py`'s S68 probe flagged as the fingers-feature target (pass 3's "long fingers -> intellect" contradiction chunk), and it currently ranks #1 under the unfiltered (OFF) query. It sits on page 98, one page outside the `95-97` range this task's instructing prompt specified for THE FINGERS. The range map's own accuracy claim ("the six known target chunks all reconcile correctly") was scoped to the six fate/head/heart target chunks only — `p98_c1` was never one of them, so this displacement was not covered by that verification. Reported as observed evidence; no range edited, no flag enabled.

## Live spot-check: real `_search_with_page_filter()` vs replicated logic

- feature: `fate line`
- replicated-logic top-3 ON (from cached top-20 pool): ['cheiroslanguageo00chei_1_p165_c1', 'cheiroslanguageo00chei_1_p165_c0', 'cheiroslanguageo00chei_1_p163_c1']
- real `_search_with_page_filter()` top-3 (live call, fresh embedding): ['cheiroslanguageo00chei_1_p165_c1', 'cheiroslanguageo00chei_1_p165_c0', 'cheiroslanguageo00chei_1_p163_c1']
- verdict: MATCH

## Step 4 — regression suite (flag OFF, the shipped default)

Run separately (`python -m pytest -q`), not from inside this script. Flag stays at its module default (`False`) for this run — no test, fixture, or conftest sets `_FEATURE_PAGE_FILTER_ENABLED` to `True` anywhere; the new `_search_with_page_filter` function and `_FEATURE_PAGE_RANGES` loader are reachable but never invoked by `_retrieve_per_feature` while the flag is off, so this run verifies the byte-identical-when-OFF claim, not just states it.

```
3341 passed, 7 skipped, 1 xpassed, 1 warning in 78.57s (0:01:18)
```

Baseline: 3341 passed / 0 failed. Result: MATCH — 0 failed, 0 delta from baseline; the 7 skipped / 1 xpassed are pre-existing (not introduced by this change).
