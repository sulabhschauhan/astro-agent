# F-C retrieval-gap evidence probe (S68)

Diagnostics-only, throwaway, read-only (`scripts/probe_fc_retrieval.py`). Measure-first: reports observed ranks only, asserts nothing, proposes no threshold changes. No production code touched (palm_reading.py, the support gate, and production `n` are all unmodified; retrieval depth here is extended to n=10 for THIS PROBE ONLY).

Confirmed descriptions transplanted verbatim from `.claude/read_prompt.md`'s three 2026-07-18 RUN blocks, reusing `scripts/probe_pass3_chunks.py`'s own transplanted `_LEFT`/`_RIGHT`/`_HAND_DETAIL` constants directly (not retyped).

Two query variants per feature, run against two source-text scopes each (the F-D axis): **BASELINE** = current production variant-iii template (`palm_reading._build_feature_query`, unmodified) at n=10; **VARIANT-IV** = pure Python string assembly off every comma-split clause of the confirmed field text (see script docstring for the exact algorithm), also at n=10. `LR` = LEFT+RIGHT fields only (Run A/B shape); `LRH` = +HAND_DETAIL (Run C shape).

## heart line

### Query strings

| Variant | Scope | Query |
|---|---|---|
| BASELINE (variant-iii) | LR | `what does a deep heart line signify — meaning and indications of a deep heart line` |
| BASELINE (variant-iii) | LRH | `what does a deep / the heart line is visible heart line signify — meaning and indications of a deep / the heart line is visible heart line` |
| VARIANT-IV | LR | `heart line deep, long, slightly curved, no breaks, chains, forks, or islands visible, ends below the index finger` |
| VARIANT-IV | LRH | `heart line deep, long, slightly curved, no breaks, chains, forks, or islands visible, ends below the index finger, The heart line is visible, curving across the top of the palm` |

### BASELINE / LR

| rank | chunk_id | page_ref | score | vs. 0.30 floor | target flags |
|---|---|---|---|---|---|
| 1 | `cheiroslanguageo00chei_1_p160_c2` | p.160 | 0.6427 | above | -- |
| 2 | `cheiroslanguageo00chei_1_p161_c0` | p.161 | 0.6188 | above | -- |
| 3 | `cheiroslanguageo00chei_1_p159_c2` | p.159 | 0.6061 | above | -- |
| 4 | `cheiroslanguageo00chei_1_p159_c3` | p.159 | 0.6054 | above | -- |
| 5 | `cheiroslanguageo00chei_1_p156_c0` | p.156 | 0.5884 | above | -- |
| 6 | `cheiroslanguageo00chei_1_p160_c1` | p.160 | 0.5570 | above | -- |
| 7 | `cheiroslanguageo00chei_1_p156_c1` | p.156 | 0.5494 | above | -- |
| 8 | `cheiroslanguageo00chei_1_p169_c2` | p.169 | 0.5418 | above | -- |
| 9 | `cheiroslanguageo00chei_1_p139_c0` | p.139 | 0.5362 | above | -- |
| 10 | `cheiroslanguageo00chei_1_p134_c1` | p.134 | 0.5301 | above | -- |
| -- | -- | -- | (all 10 results above the 0.30 floor) | -- | -- |

### BASELINE / LRH

| rank | chunk_id | page_ref | score | vs. 0.30 floor | target flags |
|---|---|---|---|---|---|
| 1 | `cheiroslanguageo00chei_1_p159_c3` | p.159 | 0.6088 | above | -- |
| 2 | `cheiroslanguageo00chei_1_p160_c2` | p.160 | 0.6067 | above | -- |
| 3 | `cheiroslanguageo00chei_1_p161_c0` | p.161 | 0.5970 | above | -- |
| 4 | `cheiroslanguageo00chei_1_p156_c0` | p.156 | 0.5775 | above | -- |
| 5 | `cheiroslanguageo00chei_1_p159_c2` | p.159 | 0.5636 | above | -- |
| 6 | `cheiroslanguageo00chei_1_p160_c1` | p.160 | 0.5296 | above | -- |
| 7 | `cheiroslanguageo00chei_1_p123_c0` | p.123 | 0.5201 | above | -- |
| 8 | `cheiroslanguageo00chei_1_p169_c2` | p.169 | 0.5163 | above | -- |
| 9 | `cheiroslanguageo00chei_1_p134_c1` | p.134 | 0.5140 | above | -- |
| 10 | `cheiroslanguageo00chei_1_p139_c0` | p.139 | 0.5086 | above | -- |
| -- | -- | -- | (all 10 results above the 0.30 floor) | -- | -- |

### VARIANT-IV / LR

| rank | chunk_id | page_ref | score | vs. 0.30 floor | target flags |
|---|---|---|---|---|---|
| 1 | `cheiroslanguageo00chei_1_p134_c1` | p.134 | 0.6133 | above | -- |
| 2 | `cheiroslanguageo00chei_1_p159_c2` | p.159 | 0.5683 | above | -- |
| 3 | `cheiroslanguageo00chei_1_p160_c2` | p.160 | 0.5486 | above | -- |
| 4 | `cheiroslanguageo00chei_1_p171_c1` | p.171 | 0.5484 | above | -- |
| 5 | `cheiroslanguageo00chei_1_p180_c2` | p.180 | 0.5484 | above | -- |
| 6 | `cheiroslanguageo00chei_1_p161_c0` | p.161 | 0.5459 | above | -- |
| 7 | `cheiroslanguageo00chei_1_p156_c0` | p.156 | 0.5424 | above | -- |
| 8 | `cheiroslanguageo00chei_1_p120_c0` | p.120 | 0.5248 | above | -- |
| 9 | `cheiroslanguageo00chei_1_p147_c1` | p.147 | 0.5244 | above | -- |
| 10 | `cheiroslanguageo00chei_1_p98_c1` | p.98 | 0.5159 | above | -- |
| -- | -- | -- | (all 10 results above the 0.30 floor) | -- | -- |

### VARIANT-IV / LRH

| rank | chunk_id | page_ref | score | vs. 0.30 floor | target flags |
|---|---|---|---|---|---|
| 1 | `cheiroslanguageo00chei_1_p156_c0` | p.156 | 0.6412 | above | -- |
| 2 | `cheiroslanguageo00chei_1_p159_c2` | p.159 | 0.6281 | above | -- |
| 3 | `cheiroslanguageo00chei_1_p134_c1` | p.134 | 0.6220 | above | -- |
| 4 | `cheiroslanguageo00chei_1_p160_c2` | p.160 | 0.6128 | above | -- |
| 5 | `cheiroslanguageo00chei_1_p161_c0` | p.161 | 0.6109 | above | -- |
| 6 | `cheiroslanguageo00chei_1_p171_c1` | p.171 | 0.5800 | above | -- |
| 7 | `cheiroslanguageo00chei_1_p120_c0` | p.120 | 0.5788 | above | -- |
| 8 | `cheiroslanguageo00chei_1_p160_c1` | p.160 | 0.5772 | above | -- |
| 9 | `cheiroslanguageo00chei_1_p159_c3` | p.159 | 0.5723 | above | -- |
| 10 | `cheiroslanguageo00chei_1_p123_c0` | p.123 | 0.5691 | above | -- |
| -- | -- | -- | (all 10 results above the 0.30 floor) | -- | -- |

## fingers

### Query strings

| Variant | Scope | Query |
|---|---|---|
| BASELINE (variant-iii) | LR | `what does a long relative to the palm / slightly longer than the palm fingers signify — meaning and indications of a long relative to the palm / slightly longer than the palm fingers` |
| BASELINE (variant-iii) | LRH | `what does a long relative to the palm / slightly longer than the palm / the fingers are of moderate length. the index finger is slightly shorter than the middle finger fingers signify — meaning and indications of a long relative to the palm / slightly longer than the palm / the fingers are of moderate length. the index finger is slightly shorter than the middle finger fingers` |
| VARIANT-IV | LR | `fingers Fingers are long relative to the palm, straight, with rounded fingertips, and spaced moderately apart, Fingers are slightly longer than the palm, appear straight, fingertips are rounded, spacing is moderate` |
| VARIANT-IV | LRH | `fingers Fingers are long relative to the palm, straight, with rounded fingertips, and spaced moderately apart, Fingers are slightly longer than the palm, appear straight, fingertips are rounded, spacing is moderate, The fingers are of moderate length. The index finger is slightly shorter than the middle finger, and the ring finger is slightly longer than the index finger. The little finger is noticeably shorter` |

### BASELINE / LR

| rank | chunk_id | page_ref | score | vs. 0.30 floor | target flags |
|---|---|---|---|---|---|
| 1 | `cheiroslanguageo00chei_1_p98_c1` | p.98 | 0.6033 | above | IS target chunk cheiroslanguageo00chei_1_p98_c1 |
| 2 | `cheiroslanguageo00chei_1_p96_c1` | p.96 | 0.5429 | above | -- |
| 3 | `cheiroslanguageo00chei_1_p98_c0` | p.98 | 0.5284 | above | -- |
| 4 | `cheiroslanguageo00chei_1_p96_c2` | p.96 | 0.5211 | above | -- |
| 5 | `cheiroslanguageo00chei_1_p96_c0` | p.96 | 0.5149 | above | -- |
| 6 | `cheiroslanguageo00chei_1_p99_c0` | p.99 | 0.4974 | above | -- |
| 7 | `cheiroslanguageo00chei_1_p146_c2` | p.146 | 0.4969 | above | -- |
| 8 | `cheiroslanguageo00chei_1_p95_c0` | p.95 | 0.4914 | above | -- |
| 9 | `cheiroslanguageo00chei_1_p96_c3` | p.96 | 0.4858 | above | -- |
| 10 | `cheiroslanguageo00chei_1_p97_c0` | p.97 | 0.4792 | above | -- |
| -- | -- | -- | (all 10 results above the 0.30 floor) | -- | -- |

### BASELINE / LRH

| rank | chunk_id | page_ref | score | vs. 0.30 floor | target flags |
|---|---|---|---|---|---|
| 1 | `cheiroslanguageo00chei_1_p98_c1` | p.98 | 0.5885 | above | IS target chunk cheiroslanguageo00chei_1_p98_c1 |
| 2 | `cheiroslanguageo00chei_1_p96_c1` | p.96 | 0.5284 | above | -- |
| 3 | `cheiroslanguageo00chei_1_p96_c0` | p.96 | 0.5282 | above | -- |
| 4 | `cheiroslanguageo00chei_1_p95_c0` | p.95 | 0.5267 | above | -- |
| 5 | `cheiroslanguageo00chei_1_p96_c2` | p.96 | 0.5104 | above | -- |
| 6 | `cheiroslanguageo00chei_1_p96_c3` | p.96 | 0.5015 | above | -- |
| 7 | `cheiroslanguageo00chei_1_p97_c0` | p.97 | 0.4950 | above | -- |
| 8 | `cheiroslanguageo00chei_1_p98_c0` | p.98 | 0.4944 | above | -- |
| 9 | `cheiroslanguageo00chei_1_p99_c0` | p.99 | 0.4850 | above | -- |
| 10 | `cheiroslanguageo00chei_1_p95_c1` | p.95 | 0.4796 | above | -- |
| -- | -- | -- | (all 10 results above the 0.30 floor) | -- | -- |

### VARIANT-IV / LR

| rank | chunk_id | page_ref | score | vs. 0.30 floor | target flags |
|---|---|---|---|---|---|
| 1 | `cheiroslanguageo00chei_1_p95_c0` | p.95 | 0.5650 | above | -- |
| 2 | `cheiroslanguageo00chei_1_p95_c1` | p.95 | 0.5621 | above | -- |
| 3 | `cheiroslanguageo00chei_1_p98_c1` | p.98 | 0.5442 | above | IS target chunk cheiroslanguageo00chei_1_p98_c1 |
| 4 | `cheiroslanguageo00chei_1_p96_c0` | p.96 | 0.5422 | above | -- |
| 5 | `cheiroslanguageo00chei_1_p95_c2` | p.95 | 0.5286 | above | -- |
| 6 | `cheiroslanguageo00chei_1_p96_c3` | p.96 | 0.5023 | above | -- |
| 7 | `cheiroslanguageo00chei_1_p97_c0` | p.97 | 0.5008 | above | -- |
| 8 | `cheiroslanguageo00chei_1_p96_c2` | p.96 | 0.4985 | above | -- |
| 9 | `cheiroslanguageo00chei_1_p58_c0` | p.58 | 0.4954 | above | -- |
| 10 | `cheiroslanguageo00chei_1_p98_c0` | p.98 | 0.4917 | above | -- |
| -- | -- | -- | (all 10 results above the 0.30 floor) | -- | -- |

### VARIANT-IV / LRH

| rank | chunk_id | page_ref | score | vs. 0.30 floor | target flags |
|---|---|---|---|---|---|
| 1 | `cheiroslanguageo00chei_1_p95_c0` | p.95 | 0.6000 | above | -- |
| 2 | `cheiroslanguageo00chei_1_p95_c1` | p.95 | 0.5844 | above | -- |
| 3 | `cheiroslanguageo00chei_1_p98_c1` | p.98 | 0.5674 | above | IS target chunk cheiroslanguageo00chei_1_p98_c1 |
| 4 | `cheiroslanguageo00chei_1_p96_c0` | p.96 | 0.5623 | above | -- |
| 5 | `cheiroslanguageo00chei_1_p96_c3` | p.96 | 0.5526 | above | -- |
| 6 | `cheiroslanguageo00chei_1_p96_c2` | p.96 | 0.5264 | above | -- |
| 7 | `cheiroslanguageo00chei_1_p97_c0` | p.97 | 0.5244 | above | -- |
| 8 | `cheiroslanguageo00chei_1_p96_c1` | p.96 | 0.5199 | above | -- |
| 9 | `cheiroslanguageo00chei_1_p95_c2` | p.95 | 0.5034 | above | -- |
| 10 | `cheiroslanguageo00chei_1_p88_c1` | p.88 | 0.4840 | above | -- |
| -- | -- | -- | (all 10 results above the 0.30 floor) | -- | -- |

## life line

### Query strings

| Variant | Scope | Query |
|---|---|---|
| BASELINE (variant-iii) | LR | `what does a deep life line signify — meaning and indications of a deep life line` |
| BASELINE (variant-iii) | LRH | `what does a deep / a prominent line curves around the base of the thumb life line signify — meaning and indications of a deep / a prominent line curves around the base of the thumb life line` |
| VARIANT-IV | LR | `life line deep, long, curves around the base of the thumb, no breaks, chains, forks, or islands visible, no clear breaks or forks` |
| VARIANT-IV | LRH | `life line deep, long, curves around the base of the thumb, no breaks, chains, forks, or islands visible, no clear breaks or forks, A prominent line curves around the base of the thumb` |

### BASELINE / LR

| rank | chunk_id | page_ref | score | vs. 0.30 floor | target flags |
|---|---|---|---|---|---|
| 1 | `cheiroslanguageo00chei_1_p139_c0` | p.139 | 0.6108 | above | -- |
| 2 | `cheiroslanguageo00chei_1_p134_c2` | p.134 | 0.5801 | above | IS target chunk cheiroslanguageo00chei_1_p134_c2 |
| 3 | `cheiroslanguageo00chei_1_p134_c1` | p.134 | 0.5775 | above | -- |
| 4 | `cheiroslanguageo00chei_1_p135_c0` | p.135 | 0.5652 | above | -- |
| 5 | `cheiroslanguageo00chei_1_p139_c1` | p.139 | 0.5552 | above | -- |
| 6 | `cheiroslanguageo00chei_1_p193_c2` | p.193 | 0.5420 | above | -- |
| 7 | `cheiroslanguageo00chei_1_p138_c1` | p.138 | 0.5406 | above | -- |
| 8 | `cheiroslanguageo00chei_1_p135_c2` | p.135 | 0.5394 | above | -- |
| 9 | `cheiroslanguageo00chei_1_p166_c2` | p.166 | 0.5347 | above | -- |
| 10 | `cheiroslanguageo00chei_1_p136_c1` | p.136 | 0.5337 | above | -- |
| -- | -- | -- | (all 10 results above the 0.30 floor) | -- | -- |

### BASELINE / LRH

| rank | chunk_id | page_ref | score | vs. 0.30 floor | target flags |
|---|---|---|---|---|---|
| 1 | `cheiroslanguageo00chei_1_p135_c0` | p.135 | 0.6127 | above | -- |
| 2 | `cheiroslanguageo00chei_1_p134_c1` | p.134 | 0.6054 | above | -- |
| 3 | `cheiroslanguageo00chei_1_p134_c0` | p.134 | 0.5721 | above | -- |
| 4 | `cheiroslanguageo00chei_1_p139_c0` | p.139 | 0.5668 | above | -- |
| 5 | `cheiroslanguageo00chei_1_p134_c2` | p.134 | 0.5654 | above | IS target chunk cheiroslanguageo00chei_1_p134_c2 |
| 6 | `cheiroslanguageo00chei_1_p135_c2` | p.135 | 0.5576 | above | -- |
| 7 | `cheiroslanguageo00chei_1_p140_c1` | p.140 | 0.5570 | above | -- |
| 8 | `cheiroslanguageo00chei_1_p180_c1` | p.180 | 0.5534 | above | -- |
| 9 | `cheiroslanguageo00chei_1_p137_c1` | p.137 | 0.5481 | above | -- |
| 10 | `cheiroslanguageo00chei_1_p181_c0` | p.181 | 0.5467 | above | -- |
| -- | -- | -- | (all 10 results above the 0.30 floor) | -- | -- |

### VARIANT-IV / LR

| rank | chunk_id | page_ref | score | vs. 0.30 floor | target flags |
|---|---|---|---|---|---|
| 1 | `cheiroslanguageo00chei_1_p134_c1` | p.134 | 0.5868 | above | -- |
| 2 | `cheiroslanguageo00chei_1_p128_c1` | p.128 | 0.5024 | above | -- |
| 3 | `cheiroslanguageo00chei_1_p171_c1` | p.171 | 0.5011 | above | -- |
| 4 | `cheiroslanguageo00chei_1_p180_c2` | p.180 | 0.5004 | above | -- |
| 5 | `cheiroslanguageo00chei_1_p135_c0` | p.135 | 0.4804 | above | -- |
| 6 | `cheiroslanguageo00chei_1_p147_c1` | p.147 | 0.4790 | above | -- |
| 7 | `cheiroslanguageo00chei_1_p140_c1` | p.140 | 0.4500 | above | -- |
| 8 | `cheiroslanguageo00chei_1_p137_c3` | p.137 | 0.4465 | above | -- |
| 9 | `cheiroslanguageo00chei_1_p139_c0` | p.139 | 0.4445 | above | -- |
| 10 | `cheiroslanguageo00chei_1_p120_c0` | p.120 | 0.4434 | above | -- |
| -- | -- | -- | (all 10 results above the 0.30 floor) | -- | -- |

### VARIANT-IV / LRH

| rank | chunk_id | page_ref | score | vs. 0.30 floor | target flags |
|---|---|---|---|---|---|
| 1 | `cheiroslanguageo00chei_1_p134_c1` | p.134 | 0.5843 | above | -- |
| 2 | `cheiroslanguageo00chei_1_p171_c1` | p.171 | 0.5202 | above | -- |
| 3 | `cheiroslanguageo00chei_1_p180_c2` | p.180 | 0.5094 | above | -- |
| 4 | `cheiroslanguageo00chei_1_p135_c0` | p.135 | 0.5040 | above | -- |
| 5 | `cheiroslanguageo00chei_1_p128_c1` | p.128 | 0.4891 | above | -- |
| 6 | `cheiroslanguageo00chei_1_p89_c0` | p.89 | 0.4870 | above | -- |
| 7 | `cheiroslanguageo00chei_1_p88_c1` | p.88 | 0.4814 | above | -- |
| 8 | `cheiroslanguageo00chei_1_p147_c1` | p.147 | 0.4807 | above | -- |
| 9 | `cheiroslanguageo00chei_1_p89_c2` | p.89 | 0.4789 | above | -- |
| 10 | `cheiroslanguageo00chei_1_p87_c0` | p.87 | 0.4771 | above | -- |
| -- | -- | -- | (all 10 results above the 0.30 floor) | -- | -- |

## Raw counts (measure-first summary, no interpretation)

| Feature | Variant/Scope | Target-flag hits in top-10 | Rank of first target-flag hit |
|---|---|---|---|
| heart line | BASELINE / LR | 0 | none in top-10 |
| heart line | BASELINE / LRH | 0 | none in top-10 |
| heart line | VARIANT-IV / LR | 0 | none in top-10 |
| heart line | VARIANT-IV / LRH | 0 | none in top-10 |
| fingers | BASELINE / LR | 1 | 1 |
| fingers | BASELINE / LRH | 1 | 1 |
| fingers | VARIANT-IV / LR | 1 | 3 |
| fingers | VARIANT-IV / LRH | 1 | 3 |
| life line | BASELINE / LR | 1 | 2 |
| life line | BASELINE / LRH | 1 | 5 |
| life line | VARIANT-IV / LR | 0 | none in top-10 |
| life line | VARIANT-IV / LRH | 0 | none in top-10 |
