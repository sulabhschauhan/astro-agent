# Production-query rank probe — S81

Supersedes the VOID rank numbers in `cheiro_retrieval_baseline_S81.md` (`b1f7a79`) and `chunk_existence_vs_rank_S81.md` (`99486aa`) — both produced by an uncommitted script with an int-for-string bug (see `diagnostics/feature_query_template_S81.md`). This script is COMMITTED (`scripts/retrieval_rank_probe_S81.py`), reproducible, and guards against the same bug class before every search call.

## Step 1 — S68 input recovery

S68's probe (`scripts/probe_fc_retrieval.py`, `_FEATURES = ("heart line", "fingers", "life line")`) covered exactly 3 registry features. fate line and head line were NEVER measured at S68 — NOT IN S68. Quotes below are S68's own reported query strings for the 3 it did cover (`diagnostics/fc_retrieval_probe_S68.md`):

- heart line (BASELINE/LR): `what does a deep heart line signify — meaning and indications of a deep heart line`
- fingers (BASELINE/LR): `what does a long relative to the palm / slightly longer than the palm fingers signify — meaning and indications of a long relative to the palm / slightly longer than the palm fingers`
- life line (BASELINE/LR): `what does a deep life line signify — meaning and indications of a deep life line`
- fate line: NOT IN S68
- head line: NOT IN S68

For fate line and head line (this task's targets), the quality descriptor below is DERIVED, not recovered: it is the unmodified production `palm_reading._resolve_feature_quality()` run against the SAME confirmed LEFT/RIGHT/HAND_DETAIL texts S68 imported (`scripts/probe_pass3_chunks.py`'s `_LEFT`/`_RIGHT`/`_HAND_DETAIL`, transplanted verbatim, not retyped) — production code on S68's own input data, not an invented string.

## Step 2 — pre-search guard

- **fate line**: quality=`barely visible / moderately deep / there is no clearly visible fate line in the image` — query=`what does a barely visible / moderately deep / there is no clearly visible fate line in the image fate line signify — meaning and indications of a barely visible / moderately deep / there is no clearly visible fate line in the image fate line` — PASSED all 3 assertions
- **head line**: quality=`deep / this line runs horizontally across the palm` — query=`what does a deep / this line runs horizontally across the palm head line signify — meaning and indications of a deep / this line runs horizontally across the palm head line` — PASSED all 3 assertions
- **heart line**: quality=`deep / the heart line is visible` — query=`what does a deep / the heart line is visible heart line signify — meaning and indications of a deep / the heart line is visible heart line` — PASSED all 3 assertions

## Step 3 — measurement (top 20, production embedding model, unmodified query path)

### fate line

| rank | chunk_id | page_ref | score | is_target |
|---|---|---|---|---|
| 1 | `cheiroslanguageo00chei_1_p165_c1` | p.165 | 0.5099 |  |
| 2 | `cheiroslanguageo00chei_1_p165_c0` | p.165 | 0.5056 |  |
| 3 | `cheiroslanguageo00chei_1_p163_c1` | p.163 | 0.4892 | TARGET |
| 4 | `cheiroslanguageo00chei_1_p163_c0` | p.163 | 0.4890 |  |
| 5 | `cheiroslanguageo00chei_1_p127_c1` | p.127 | 0.4872 |  |
| 6 | `cheiroslanguageo00chei_1_p136_c3` | p.136 | 0.4761 |  |
| 7 | `cheiroslanguageo00chei_1_p160_c2` | p.160 | 0.4747 |  |
| 8 | `cheiroslanguageo00chei_1_p162_c0` | p.162 | 0.4691 |  |
| 9 | `cheiroslanguageo00chei_1_p163_c2` | p.163 | 0.4649 |  |
| 10 | `cheiroslanguageo00chei_1_p208_c1` | p.208 | 0.4641 |  |
| 11 | `cheiroslanguageo00chei_1_p169_c0` | p.169 | 0.4622 |  |
| 12 | `cheiroslanguageo00chei_1_p179_c3` | p.179 | 0.4593 |  |
| 13 | `cheiroslanguageo00chei_1_p162_c1` | p.162 | 0.4574 |  |
| 14 | `cheiroslanguageo00chei_1_p165_c2` | p.165 | 0.4569 | TARGET |
| 15 | `cheiroslanguageo00chei_1_p164_c1` | p.164 | 0.4563 |  |
| 16 | `cheiroslanguageo00chei_1_p138_c1` | p.138 | 0.4548 |  |
| 17 | `cheiroslanguageo00chei_1_p135_c1` | p.135 | 0.4537 |  |
| 18 | `cheiroslanguageo00chei_1_p139_c1` | p.139 | 0.4534 |  |
| 19 | `cheiroslanguageo00chei_1_p124_c1` | p.124 | 0.4507 |  |
| 20 | `cheiroslanguageo00chei_1_p164_c2` | p.164 | 0.4456 |  |

### head line

| rank | chunk_id | page_ref | score | is_target |
|---|---|---|---|---|
| 1 | `cheiroslanguageo00chei_1_p123_c0` | p.123 | 0.6090 |  |
| 2 | `cheiroslanguageo00chei_1_p151_c2` | p.151 | 0.5897 |  |
| 3 | `cheiroslanguageo00chei_1_p135_c2` | p.135 | 0.5865 |  |
| 4 | `cheiroslanguageo00chei_1_p124_c1` | p.124 | 0.5802 |  |
| 5 | `cheiroslanguageo00chei_1_p134_c1` | p.134 | 0.5744 |  |
| 6 | `cheiroslanguageo00chei_1_p135_c0` | p.135 | 0.5729 |  |
| 7 | `cheiroslanguageo00chei_1_p160_c2` | p.160 | 0.5728 |  |
| 8 | `cheiroslanguageo00chei_1_p146_c2` | p.146 | 0.5704 |  |
| 9 | `cheiroslanguageo00chei_1_p140_c1` | p.140 | 0.5688 |  |
| 10 | `cheiroslanguageo00chei_1_p171_c1` | p.171 | 0.5686 |  |
| 11 | `cheiroslanguageo00chei_1_p134_c0` | p.134 | 0.5606 |  |
| 12 | `cheiroslanguageo00chei_1_p180_c2` | p.180 | 0.5576 |  |
| 13 | `cheiroslanguageo00chei_1_p193_c1` | p.193 | 0.5564 |  |
| 14 | `cheiroslanguageo00chei_1_p137_c1` | p.137 | 0.5550 |  |
| 15 | `cheiroslanguageo00chei_1_p197_c1` | p.197 | 0.5548 |  |
| 16 | `cheiroslanguageo00chei_1_p134_c2` | p.134 | 0.5542 |  |
| 17 | `cheiroslanguageo00chei_1_p181_c0` | p.181 | 0.5488 |  |
| 18 | `cheiroslanguageo00chei_1_p147_c0` | p.147 | 0.5484 |  |
| 19 | `cheiroslanguageo00chei_1_p148_c0` | p.148 | 0.5455 |  |
| 20 | `cheiroslanguageo00chei_1_p147_c1` | p.147 | 0.5454 |  |

### heart line

| rank | chunk_id | page_ref | score | is_target |
|---|---|---|---|---|
| 1 | `cheiroslanguageo00chei_1_p159_c3` | p.159 | 0.6088 |  |
| 2 | `cheiroslanguageo00chei_1_p160_c2` | p.160 | 0.6067 |  |
| 3 | `cheiroslanguageo00chei_1_p161_c0` | p.161 | 0.5970 |  |
| 4 | `cheiroslanguageo00chei_1_p156_c0` | p.156 | 0.5775 |  |
| 5 | `cheiroslanguageo00chei_1_p159_c2` | p.159 | 0.5636 | TARGET |
| 6 | `cheiroslanguageo00chei_1_p160_c1` | p.160 | 0.5296 | TARGET |
| 7 | `cheiroslanguageo00chei_1_p123_c0` | p.123 | 0.5201 |  |
| 8 | `cheiroslanguageo00chei_1_p169_c2` | p.169 | 0.5163 |  |
| 9 | `cheiroslanguageo00chei_1_p134_c1` | p.134 | 0.5140 |  |
| 10 | `cheiroslanguageo00chei_1_p139_c0` | p.139 | 0.5086 |  |
| 11 | `cheiroslanguageo00chei_1_p193_c1` | p.193 | 0.5057 |  |
| 12 | `cheiroslanguageo00chei_1_p156_c1` | p.156 | 0.5055 |  |
| 13 | `cheiroslanguageo00chei_1_p181_c0` | p.181 | 0.5045 |  |
| 14 | `cheiroslanguageo00chei_1_p135_c2` | p.135 | 0.4975 |  |
| 15 | `cheiroslanguageo00chei_1_p171_c1` | p.171 | 0.4927 |  |
| 16 | `cheiroslanguageo00chei_1_p197_c1` | p.197 | 0.4919 |  |
| 17 | `cheiroslanguageo00chei_1_p166_c1` | p.166 | 0.4913 |  |
| 18 | `cheiroslanguageo00chei_1_p139_c1` | p.139 | 0.4876 |  |
| 19 | `cheiroslanguageo00chei_1_p180_c1` | p.180 | 0.4861 |  |
| 20 | `cheiroslanguageo00chei_1_p138_c1` | p.138 | 0.4847 |  |

## Step 4 — per-target-chunk rank + gate

Production gate: `_N_RESULTS_PER_FEATURE` = 3 (a chunk clears the gate iff rank <= 3).

| feature | chunk_id | rank | gate (<= 3) |
|---|---|---|---|
| fate line | `cheiroslanguageo00chei_1_p165_c2` | 14 | FAIL |
| fate line | `cheiroslanguageo00chei_1_p163_c1` | 3 | PASS |
| head line | `cheiroslanguageo00chei_1_p145_c0` | >20 | FAIL |
| heart line | `cheiroslanguageo00chei_1_p160_c3` | >20 | FAIL |
| heart line | `cheiroslanguageo00chei_1_p159_c2` | 5 | FAIL |
| heart line | `cheiroslanguageo00chei_1_p160_c1` | 6 | FAIL |

## Step 5 — comparison to S68

heart line target chunks (p160_c3, p159_c2, p160_c1) were not S68's own "target flags" (S68 tracked "below the first finger"/"mount of jupiter" needle hits for heart line, not these specific chunk ids) — but these chunk ids DO appear organically in S68's printed BASELINE/LR and BASELINE/LRH heart-line tables, quoted verbatim below for direct rank comparison. fate line and head line have no S68 figures at all — NOT IN S68 for every one of their target chunks.

- S68 BASELINE/LR heart line: rank 3 = `p159_c2` (0.6061), rank 6 = `p160_c1` (0.5570), `p160_c3` not in top 10
- S68 BASELINE/LRH heart line: rank 5 = `p159_c2` (0.5636), rank 6 = `p160_c1` (0.5296), `p160_c3` not in top 10
- S68 fate line: NOT IN S68 (feature never probed)
- S68 head line: NOT IN S68 (feature never probed)

- `cheiroslanguageo00chei_1_p165_c2` (fate line): this probe rank=14
- `cheiroslanguageo00chei_1_p163_c1` (fate line): this probe rank=3
- `cheiroslanguageo00chei_1_p145_c0` (head line): this probe rank=>20
- `cheiroslanguageo00chei_1_p160_c3` (heart line): this probe rank=>20
- `cheiroslanguageo00chei_1_p159_c2` (heart line): this probe rank=5
- `cheiroslanguageo00chei_1_p160_c1` (heart line): this probe rank=6

### Per-feature verdict vs. S68

- fate line: NOT IN S68 (feature never probed at S68 — no comparison possible)
- head line: NOT IN S68 (feature never probed at S68 — no comparison possible)
- heart line: MATCH — `p159_c2` rank 5 (0.5636) and `p160_c1` rank 6 (0.5296) are IDENTICAL to S68's own BASELINE/LRH figures for the same scope (verbatim quote above); `p160_c3` stays not-in-top-20 here exactly as it was not-in-top-10 at S68 — neither improved nor regressed, same outcome at greater depth.
