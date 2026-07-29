# PATHOLOGY TRIAGE — S80 U1b — Cheiro only

Read-only, diagnostics-only. No repair, no boundary-seeder logic, no ChromaDB writes, no re-ingestion. Cohort: 14 overlap pages (A), 4 non-monotonic pages (B, confirmed subset of A), 15 lowest-coverage pages (C), 2 zero-match chunks (D), 11 empty-token chunks (E). See scripts/pathology_triage_S80.py module docstring for full reuse/method detail.

**Caught and fixed before this report was trusted:** the live ChromaDB corpus was directly probed (`collection.get(ids=[...], include=["metadatas"])` on two real chunk_ids) and confirmed to carry NO `text_sha256` metadata field at all -- `ingestion/embedder.py`'s `_to_metadata()` does write that field in the current source, but this live corpus predates it being backfilled. A first pass of this script read the (absent) metadata field for every NESTED/IDENTICAL pair below, silently compared `None == None`, and reported `byte_identical: False` for all 14 pairs -- an unverified non-finding, not a real one. Fixed by computing sha256 directly from each chunk's fetched TEXT (same hashing convention embedder.py's own `_to_metadata()` uses), not by trusting a metadata field that turned out not to exist. The `S23_DUPLICATE_RESIDUE = 0` result below is now a verified measurement.

## Self-checks

| Assertion | Expected | Observed | Status |
|---|---|---|---|
| Cheiro page count == 310 | 310 | 310 | PASS |
| Cheiro p157 native contains "Plate XVIII" | present | present | PASS |
| Cheiro p158 native char_count == 0 | 0 | 0 | PASS |
| Cheiro p156 native contains "CHAPTER X" | present | present | PASS |
| Cheiro p156 live chunk count == 3 | 3 | 3 | PASS |

---

## (a) Cohort A/B — overlap and non-monotonic pages

### page_index=13 (page_ref=14)

| chunk_id | span_start | span_end |
|---|---|---|
| cheiroslanguageo00chei_1_p14_c0 | 0 | 102 |
| cheiroslanguageo00chei_1_p14_c1 | 52 | 204 |
| cheiroslanguageo00chei_1_p14_c2 | 205 | 245 |

| chunk_a | span_a | chunk_b | span_b | relationship | sha_a | sha_b | byte_identical |
|---|---|---|---|---|---|---|---|
| cheiroslanguageo00chei_1_p14_c0 | [0, 102] | cheiroslanguageo00chei_1_p14_c1 | [52, 204] | PARTIAL | — | — | N/A (partial overlap, not checked per instruction) |

### page_index=19 (page_ref=20) **[also cohort B: non-monotonic]**

| chunk_id | span_start | span_end |
|---|---|---|
| cheiroslanguageo00chei_1_p20_c0 | 0 | 233 |
| cheiroslanguageo00chei_1_p20_c1 | 45 | 221 |
| cheiroslanguageo00chei_1_p20_c2 | 11 | 158 |
| cheiroslanguageo00chei_1_p20_c3 | 159 | 246 |
| cheiroslanguageo00chei_1_p20_c4 | None | None |

| chunk_a | span_a | chunk_b | span_b | relationship | sha_a | sha_b | byte_identical |
|---|---|---|---|---|---|---|---|
| cheiroslanguageo00chei_1_p20_c0 | [0, 233] | cheiroslanguageo00chei_1_p20_c1 | [45, 221] | NESTED | e8cc3863704183658b6f734941d25601e9b0c86f4b26515dae0667dd7388f2a1 | 28203900cc8bcc48f9e4b099fa9b82f0f257b4a33ad7b7b795686b1df70f6da1 | False |
| cheiroslanguageo00chei_1_p20_c0 | [0, 233] | cheiroslanguageo00chei_1_p20_c2 | [11, 158] | NESTED | e8cc3863704183658b6f734941d25601e9b0c86f4b26515dae0667dd7388f2a1 | cef8d655a81002812a7af3fe0f303c2fc338fd29c5e46ba29763ece19c255a8a | False |
| cheiroslanguageo00chei_1_p20_c0 | [0, 233] | cheiroslanguageo00chei_1_p20_c3 | [159, 246] | PARTIAL | — | — | N/A (partial overlap, not checked per instruction) |
| cheiroslanguageo00chei_1_p20_c1 | [45, 221] | cheiroslanguageo00chei_1_p20_c2 | [11, 158] | PARTIAL | — | — | N/A (partial overlap, not checked per instruction) |
| cheiroslanguageo00chei_1_p20_c1 | [45, 221] | cheiroslanguageo00chei_1_p20_c3 | [159, 246] | PARTIAL | — | — | N/A (partial overlap, not checked per instruction) |

### page_index=20 (page_ref=21)

| chunk_id | span_start | span_end |
|---|---|---|
| cheiroslanguageo00chei_1_p21_c0 | 0 | 77 |
| cheiroslanguageo00chei_1_p21_c1 | 7 | 85 |

| chunk_a | span_a | chunk_b | span_b | relationship | sha_a | sha_b | byte_identical |
|---|---|---|---|---|---|---|---|
| cheiroslanguageo00chei_1_p21_c0 | [0, 77] | cheiroslanguageo00chei_1_p21_c1 | [7, 85] | PARTIAL | — | — | N/A (partial overlap, not checked per instruction) |

### page_index=39 (page_ref=40) **[also cohort B: non-monotonic]**

| chunk_id | span_start | span_end |
|---|---|---|
| cheiroslanguageo00chei_1_p40_c0 | 0 | 175 |
| cheiroslanguageo00chei_1_p40_c1 | 176 | 278 |
| cheiroslanguageo00chei_1_p40_c2 | 102 | 452 |

| chunk_a | span_a | chunk_b | span_b | relationship | sha_a | sha_b | byte_identical |
|---|---|---|---|---|---|---|---|
| cheiroslanguageo00chei_1_p40_c0 | [0, 175] | cheiroslanguageo00chei_1_p40_c2 | [102, 452] | PARTIAL | — | — | N/A (partial overlap, not checked per instruction) |
| cheiroslanguageo00chei_1_p40_c1 | [176, 278] | cheiroslanguageo00chei_1_p40_c2 | [102, 452] | NESTED | 6bb927cc6489ba3a085e97fdf2d7258814da11ccb76180b5124f0128732438c9 | e91207da55f8062dbf8651acb0c1396977909823d1c313d81f17d4a804198854 | False |

### page_index=68 (page_ref=69)

| chunk_id | span_start | span_end |
|---|---|---|
| cheiroslanguageo00chei_1_p69_c0 | 0 | 326 |
| cheiroslanguageo00chei_1_p69_c1 | 61 | 61 |

| chunk_a | span_a | chunk_b | span_b | relationship | sha_a | sha_b | byte_identical |
|---|---|---|---|---|---|---|---|
| cheiroslanguageo00chei_1_p69_c0 | [0, 326] | cheiroslanguageo00chei_1_p69_c1 | [61, 61] | NESTED | 1fd9af5b205d6638f3be4870725851221f8426fc47dcf87636aefa21b72007d3 | 2041a4c8854be18e6434440fafda85e2d16c967ff8f2ddefca20217c9f45cf30 | False |

### page_index=135 (page_ref=136)

| chunk_id | span_start | span_end |
|---|---|---|
| cheiroslanguageo00chei_1_p136_c0 | 1 | 172 |
| cheiroslanguageo00chei_1_p136_c1 | 122 | 231 |
| cheiroslanguageo00chei_1_p136_c2 | 232 | 370 |
| cheiroslanguageo00chei_1_p136_c3 | 371 | 436 |

| chunk_a | span_a | chunk_b | span_b | relationship | sha_a | sha_b | byte_identical |
|---|---|---|---|---|---|---|---|
| cheiroslanguageo00chei_1_p136_c0 | [1, 172] | cheiroslanguageo00chei_1_p136_c1 | [122, 231] | PARTIAL | — | — | N/A (partial overlap, not checked per instruction) |

### page_index=146 (page_ref=147) **[also cohort B: non-monotonic]**

| chunk_id | span_start | span_end |
|---|---|---|
| cheiroslanguageo00chei_1_p147_c0 | 0 | 100 |
| cheiroslanguageo00chei_1_p147_c1 | 101 | 210 |
| cheiroslanguageo00chei_1_p147_c2 | 0 | 326 |
| cheiroslanguageo00chei_1_p147_c3 | 327 | 376 |

| chunk_a | span_a | chunk_b | span_b | relationship | sha_a | sha_b | byte_identical |
|---|---|---|---|---|---|---|---|
| cheiroslanguageo00chei_1_p147_c0 | [0, 100] | cheiroslanguageo00chei_1_p147_c2 | [0, 326] | NESTED | bd309e18252209204861f8ea6ea5e07f01157b2b0a20e75f9144bd07a59b1691 | 812bb4a6761f1b1eac79b7576ba9b85dd535d07689bd86f7e14b83e2bed07771 | False |
| cheiroslanguageo00chei_1_p147_c1 | [101, 210] | cheiroslanguageo00chei_1_p147_c2 | [0, 326] | NESTED | 60179f339ba579190b92649a892d13255be8e1172268cd7cf6ff4191310b0f2e | 812bb4a6761f1b1eac79b7576ba9b85dd535d07689bd86f7e14b83e2bed07771 | False |

### page_index=150 (page_ref=151)

| chunk_id | span_start | span_end |
|---|---|---|
| cheiroslanguageo00chei_1_p151_c0 | 0 | 111 |
| cheiroslanguageo00chei_1_p151_c1 | 0 | 369 |
| cheiroslanguageo00chei_1_p151_c2 | 0 | 405 |

| chunk_a | span_a | chunk_b | span_b | relationship | sha_a | sha_b | byte_identical |
|---|---|---|---|---|---|---|---|
| cheiroslanguageo00chei_1_p151_c0 | [0, 111] | cheiroslanguageo00chei_1_p151_c1 | [0, 369] | NESTED | fb7426dd51bf4ec219ff366baad19bda2410e49832da73aaabc153f17382a251 | 20a927a93f7e58f4cdc5f9fc42bef50f548fcc45778b4dd9f74ded9b05bf663c | False |
| cheiroslanguageo00chei_1_p151_c0 | [0, 111] | cheiroslanguageo00chei_1_p151_c2 | [0, 405] | NESTED | fb7426dd51bf4ec219ff366baad19bda2410e49832da73aaabc153f17382a251 | cfcd23e5cb808018edfd77f60ef3a0d08dc1ff5f51dfdfbdecd5c190a9c09623 | False |
| cheiroslanguageo00chei_1_p151_c1 | [0, 369] | cheiroslanguageo00chei_1_p151_c2 | [0, 405] | NESTED | 20a927a93f7e58f4cdc5f9fc42bef50f548fcc45778b4dd9f74ded9b05bf663c | cfcd23e5cb808018edfd77f60ef3a0d08dc1ff5f51dfdfbdecd5c190a9c09623 | False |

### page_index=155 (page_ref=156)

| chunk_id | span_start | span_end |
|---|---|---|
| cheiroslanguageo00chei_1_p156_c0 | 0 | 128 |
| cheiroslanguageo00chei_1_p156_c1 | 2 | 254 |
| cheiroslanguageo00chei_1_p156_c2 | 255 | 325 |

| chunk_a | span_a | chunk_b | span_b | relationship | sha_a | sha_b | byte_identical |
|---|---|---|---|---|---|---|---|
| cheiroslanguageo00chei_1_p156_c0 | [0, 128] | cheiroslanguageo00chei_1_p156_c1 | [2, 254] | PARTIAL | — | — | N/A (partial overlap, not checked per instruction) |

### page_index=187 (page_ref=188)

| chunk_id | span_start | span_end |
|---|---|---|
| cheiroslanguageo00chei_1_p188_c0 | 1 | 148 |
| cheiroslanguageo00chei_1_p188_c1 | 95 | 258 |
| cheiroslanguageo00chei_1_p188_c2 | 259 | 386 |

| chunk_a | span_a | chunk_b | span_b | relationship | sha_a | sha_b | byte_identical |
|---|---|---|---|---|---|---|---|
| cheiroslanguageo00chei_1_p188_c0 | [1, 148] | cheiroslanguageo00chei_1_p188_c1 | [95, 258] | PARTIAL | — | — | N/A (partial overlap, not checked per instruction) |

### page_index=214 (page_ref=215)

| chunk_id | span_start | span_end |
|---|---|---|
| cheiroslanguageo00chei_1_p215_c0 | 0 | 208 |
| cheiroslanguageo00chei_1_p215_c1 | 170 | 329 |
| cheiroslanguageo00chei_1_p215_c2 | 331 | 467 |

| chunk_a | span_a | chunk_b | span_b | relationship | sha_a | sha_b | byte_identical |
|---|---|---|---|---|---|---|---|
| cheiroslanguageo00chei_1_p215_c0 | [0, 208] | cheiroslanguageo00chei_1_p215_c1 | [170, 329] | PARTIAL | — | — | N/A (partial overlap, not checked per instruction) |

### page_index=216 (page_ref=217)

| chunk_id | span_start | span_end |
|---|---|---|
| cheiroslanguageo00chei_1_p217_c0 | 0 | 191 |
| cheiroslanguageo00chei_1_p217_c1 | 116 | 244 |
| cheiroslanguageo00chei_1_p217_c2 | 245 | 342 |

| chunk_a | span_a | chunk_b | span_b | relationship | sha_a | sha_b | byte_identical |
|---|---|---|---|---|---|---|---|
| cheiroslanguageo00chei_1_p217_c0 | [0, 191] | cheiroslanguageo00chei_1_p217_c1 | [116, 244] | PARTIAL | — | — | N/A (partial overlap, not checked per instruction) |

### page_index=219 (page_ref=220) **[also cohort B: non-monotonic]**

| chunk_id | span_start | span_end |
|---|---|---|
| cheiroslanguageo00chei_1_p220_c0 | 0 | 163 |
| cheiroslanguageo00chei_1_p220_c1 | 164 | 355 |
| cheiroslanguageo00chei_1_p220_c2 | 43 | 407 |

| chunk_a | span_a | chunk_b | span_b | relationship | sha_a | sha_b | byte_identical |
|---|---|---|---|---|---|---|---|
| cheiroslanguageo00chei_1_p220_c0 | [0, 163] | cheiroslanguageo00chei_1_p220_c2 | [43, 407] | PARTIAL | — | — | N/A (partial overlap, not checked per instruction) |
| cheiroslanguageo00chei_1_p220_c1 | [164, 355] | cheiroslanguageo00chei_1_p220_c2 | [43, 407] | NESTED | 482d4e2c99291ee6320941eaa95d00aa0f55fb6bbfb75fffdc1e6372c09d6a64 | f06c6fd5f1b883630121679fe73c8934e06773c32b8fbe0e49e1cec3ed30fbd4 | False |

### page_index=302 (page_ref=303)

| chunk_id | span_start | span_end |
|---|---|---|
| cheiroslanguageo00chei_1_p303_c0 | 1 | 257 |
| cheiroslanguageo00chei_1_p303_c1 | 131 | 248 |
| cheiroslanguageo00chei_1_p303_c2 | 249 | 404 |
| cheiroslanguageo00chei_1_p303_c3 | 405 | 496 |

| chunk_a | span_a | chunk_b | span_b | relationship | sha_a | sha_b | byte_identical |
|---|---|---|---|---|---|---|---|
| cheiroslanguageo00chei_1_p303_c0 | [1, 257] | cheiroslanguageo00chei_1_p303_c1 | [131, 248] | NESTED | dfc7bcd21de25df5c694dd34502c71c346aa6fa65a05d2fcb09916ff971ecbf8 | 9732d3036470280791e5dc9468524180e3bf4597531533401a90fc3e0ec76b21 | False |
| cheiroslanguageo00chei_1_p303_c0 | [1, 257] | cheiroslanguageo00chei_1_p303_c2 | [249, 404] | PARTIAL | — | — | N/A (partial overlap, not checked per instruction) |

---

## (a) Cohort C — 15 lowest-coverage pages, gap subcategory breakdown

| page_index | page_ref | coverage | ordinary_prose_word | other_unclassified_nonword_fragment | punctuation_single_char_non_alpha | roman_numeral | running_head_title_fragment |
|---|---|---|---|---|---|---|---|
| 124 | 125 | 0.2778 | 2 | 8 | 0 | 3 | 0 |
| 140 | 141 | 0.3485 | 10 | 33 | 0 | 0 | 0 |
| 100 | 101 | 0.6667 | 0 | 1 | 0 | 0 | 0 |
| 193 | 194 | 0.9709 | 1 | 1 | 0 | 1 | 0 |
| 6 | 7 | 0.9865 | 0 | 0 | 2 | 1 | 0 |
| 151 | 152 | 0.9877 | 0 | 0 | 1 | 0 | 1 |
| 226 | 227 | 0.9881 | 0 | 1 | 0 | 0 | 0 |
| 81 | 82 | 0.9903 | 0 | 1 | 0 | 0 | 0 |
| 217 | 218 | 0.9910 | 0 | 1 | 0 | 0 | 0 |
| 105 | 106 | 0.9911 | 0 | 2 | 0 | 0 | 0 |
| 299 | 300 | 0.9915 | 2 | 1 | 0 | 0 | 0 |
| 149 | 150 | 0.9916 | 0 | 1 | 1 | 0 | 1 |
| 231 | 232 | 0.9916 | 1 | 1 | 0 | 0 | 1 |
| 65 | 66 | 0.9917 | 0 | 1 | 0 | 0 | 0 |
| 133 | 134 | 0.9925 | 0 | 1 | 0 | 2 | 0 |

### page 125 (page_index=124) largest contiguous gap span, quoted

Span (native token indices): (0, 12)

> V sAt V fj'Mft ow vc V WlU CWv ft vus vtoi vT

---

## (a) Cohort D — zero-match chunks (match_ratio == 0.0)

### cheiroslanguageo00chei_1_p20_c4 (page_index=19, page_ref=20, chunk_token_count=1)

Text: `#  cD`

| Neighbor page_ref | match_ratio | span_start | span_end |
|---|---|---|---|
| 19 | 0.0000 | None | None |
| 20 | 0.0000 | None | None |
| 21 | 0.0000 | None | None |

**Classification: GARBLED_CHUNK** — no neighbor page matches meaningfully either — text does not correspond to any nearby native page

### cheiroslanguageo00chei_1_p87_c1 (page_index=86, page_ref=87, chunk_token_count=1)

Text: `e`

| Neighbor page_ref | match_ratio | span_start | span_end |
|---|---|---|---|
| 86 | 0.0000 | None | None |
| 87 | 0.0000 | None | None |
| 88 | 0.0000 | None | None |

**Classification: GARBLED_CHUNK** — no neighbor page matches meaningfully either — text does not correspond to any nearby native page

---

## (a) Cohort E — empty-token chunks (match_ratio is None)

| chunk_id | page_index | page_ref | text (repr) | is_empty | digits/punct-only |
|---|---|---|---|---|---|
| cheiroslanguageo00chei_1_p26_c2 | 25 | 26 | `'4'` | False | True |
| cheiroslanguageo00chei_1_p52_c1 | 51 | 52 | `'28'` | False | True |
| cheiroslanguageo00chei_1_p58_c2 | 57 | 58 | `'32'` | False | True |
| cheiroslanguageo00chei_1_p62_c1 | 61 | 62 | `'34'` | False | True |
| cheiroslanguageo00chei_1_p81_c1 | 80 | 81 | `'43'` | False | True |
| cheiroslanguageo00chei_1_p129_c1 | 128 | 129 | `'77'` | False | True |
| cheiroslanguageo00chei_1_p140_c2 | 139 | 140 | `'86'` | False | True |
| cheiroslanguageo00chei_1_p173_c1 | 172 | 173 | `'111'` | False | True |
| cheiroslanguageo00chei_1_p178_c1 | 177 | 178 | `'114'` | False | True |
| cheiroslanguageo00chei_1_p210_c1 | 209 | 210 | `'142'` | False | True |
| cheiroslanguageo00chei_1_p225_c2 | 224 | 225 | `'155'` | False | True |

---

## (b) Classification rollup

| Class | Count |
|---|---|
| S23_DUPLICATE_RESIDUE | 0 |
| GENUINE_BOUNDARY_ERROR | 25 |
| MISATTRIBUTED_CHUNK | 0 |
| GARBLED_CHUNK | 2 |
| F7_EMPTY_CHUNK | 11 |
| APPARATUS_GAP_BENIGN | 14 |
| UNCLASSIFIED | 0 |

<details><summary>Per-unit classification (click to expand)</summary>

| Unit | Classification |
|---|---|
| 14:cheiroslanguageo00chei_1_p14_c0<->cheiroslanguageo00chei_1_p14_c1 | GENUINE_BOUNDARY_ERROR |
| 20:cheiroslanguageo00chei_1_p20_c0<->cheiroslanguageo00chei_1_p20_c1 | GENUINE_BOUNDARY_ERROR |
| 20:cheiroslanguageo00chei_1_p20_c0<->cheiroslanguageo00chei_1_p20_c2 | GENUINE_BOUNDARY_ERROR |
| 20:cheiroslanguageo00chei_1_p20_c0<->cheiroslanguageo00chei_1_p20_c3 | GENUINE_BOUNDARY_ERROR |
| 20:cheiroslanguageo00chei_1_p20_c1<->cheiroslanguageo00chei_1_p20_c2 | GENUINE_BOUNDARY_ERROR |
| 20:cheiroslanguageo00chei_1_p20_c1<->cheiroslanguageo00chei_1_p20_c3 | GENUINE_BOUNDARY_ERROR |
| 21:cheiroslanguageo00chei_1_p21_c0<->cheiroslanguageo00chei_1_p21_c1 | GENUINE_BOUNDARY_ERROR |
| 40:cheiroslanguageo00chei_1_p40_c0<->cheiroslanguageo00chei_1_p40_c2 | GENUINE_BOUNDARY_ERROR |
| 40:cheiroslanguageo00chei_1_p40_c1<->cheiroslanguageo00chei_1_p40_c2 | GENUINE_BOUNDARY_ERROR |
| 69:cheiroslanguageo00chei_1_p69_c0<->cheiroslanguageo00chei_1_p69_c1 | GENUINE_BOUNDARY_ERROR |
| 136:cheiroslanguageo00chei_1_p136_c0<->cheiroslanguageo00chei_1_p136_c1 | GENUINE_BOUNDARY_ERROR |
| 147:cheiroslanguageo00chei_1_p147_c0<->cheiroslanguageo00chei_1_p147_c2 | GENUINE_BOUNDARY_ERROR |
| 147:cheiroslanguageo00chei_1_p147_c1<->cheiroslanguageo00chei_1_p147_c2 | GENUINE_BOUNDARY_ERROR |
| 151:cheiroslanguageo00chei_1_p151_c0<->cheiroslanguageo00chei_1_p151_c1 | GENUINE_BOUNDARY_ERROR |
| 151:cheiroslanguageo00chei_1_p151_c0<->cheiroslanguageo00chei_1_p151_c2 | GENUINE_BOUNDARY_ERROR |
| 151:cheiroslanguageo00chei_1_p151_c1<->cheiroslanguageo00chei_1_p151_c2 | GENUINE_BOUNDARY_ERROR |
| 156:cheiroslanguageo00chei_1_p156_c0<->cheiroslanguageo00chei_1_p156_c1 | GENUINE_BOUNDARY_ERROR |
| 188:cheiroslanguageo00chei_1_p188_c0<->cheiroslanguageo00chei_1_p188_c1 | GENUINE_BOUNDARY_ERROR |
| 215:cheiroslanguageo00chei_1_p215_c0<->cheiroslanguageo00chei_1_p215_c1 | GENUINE_BOUNDARY_ERROR |
| 217:cheiroslanguageo00chei_1_p217_c0<->cheiroslanguageo00chei_1_p217_c1 | GENUINE_BOUNDARY_ERROR |
| 220:cheiroslanguageo00chei_1_p220_c0<->cheiroslanguageo00chei_1_p220_c2 | GENUINE_BOUNDARY_ERROR |
| 220:cheiroslanguageo00chei_1_p220_c1<->cheiroslanguageo00chei_1_p220_c2 | GENUINE_BOUNDARY_ERROR |
| 303:cheiroslanguageo00chei_1_p303_c0<->cheiroslanguageo00chei_1_p303_c1 | GENUINE_BOUNDARY_ERROR |
| 303:cheiroslanguageo00chei_1_p303_c0<->cheiroslanguageo00chei_1_p303_c2 | GENUINE_BOUNDARY_ERROR |
| page_125_coverage_gap | APPARATUS_GAP_BENIGN |
| page_141_coverage_gap | APPARATUS_GAP_BENIGN |
| page_101_coverage_gap | APPARATUS_GAP_BENIGN |
| page_194_coverage_gap | APPARATUS_GAP_BENIGN |
| page_7_coverage_gap | APPARATUS_GAP_BENIGN |
| page_152_coverage_gap | APPARATUS_GAP_BENIGN |
| page_227_coverage_gap | APPARATUS_GAP_BENIGN |
| page_82_coverage_gap | APPARATUS_GAP_BENIGN |
| page_218_coverage_gap | APPARATUS_GAP_BENIGN |
| page_106_coverage_gap | APPARATUS_GAP_BENIGN |
| page_300_coverage_gap | GENUINE_BOUNDARY_ERROR |
| page_150_coverage_gap | APPARATUS_GAP_BENIGN |
| page_232_coverage_gap | APPARATUS_GAP_BENIGN |
| page_66_coverage_gap | APPARATUS_GAP_BENIGN |
| page_134_coverage_gap | APPARATUS_GAP_BENIGN |
| cheiroslanguageo00chei_1_p20_c4 | GARBLED_CHUNK |
| cheiroslanguageo00chei_1_p87_c1 | GARBLED_CHUNK |
| cheiroslanguageo00chei_1_p26_c2 | F7_EMPTY_CHUNK |
| cheiroslanguageo00chei_1_p52_c1 | F7_EMPTY_CHUNK |
| cheiroslanguageo00chei_1_p58_c2 | F7_EMPTY_CHUNK |
| cheiroslanguageo00chei_1_p62_c1 | F7_EMPTY_CHUNK |
| cheiroslanguageo00chei_1_p81_c1 | F7_EMPTY_CHUNK |
| cheiroslanguageo00chei_1_p129_c1 | F7_EMPTY_CHUNK |
| cheiroslanguageo00chei_1_p140_c2 | F7_EMPTY_CHUNK |
| cheiroslanguageo00chei_1_p173_c1 | F7_EMPTY_CHUNK |
| cheiroslanguageo00chei_1_p178_c1 | F7_EMPTY_CHUNK |
| cheiroslanguageo00chei_1_p210_c1 | F7_EMPTY_CHUNK |
| cheiroslanguageo00chei_1_p225_c2 | F7_EMPTY_CHUNK |

</details>

---

## (c) Consequences if a re-ingest applied NO special handling

Descriptions only — no fallback rule proposed, no seeder design. That is a design-chat ruling, made after reading this triage.

- **S23_DUPLICATE_RESIDUE**: a naive re-ingest that re-derives chunk ids from the OLD chunk list would carry the duplicate straight into the new corpus — two ids would still resolve to byte-identical text, doubling retrieval weight for that content without adding any real coverage.
- **GENUINE_BOUNDARY_ERROR**: content in the overlapping/crossing region would be re-chunked using a boundary that was already wrong once — the same words could land in two new chunks (if seeded from both old spans) or in neither cleanly-attributed chunk (if the seeder tries to split the difference).
- **MISATTRIBUTED_CHUNK**: a re-ingest trusting the OLD page_ref would keep anchoring this chunk's content to the wrong page indefinitely — any citation, test, or rubric row keyed on that page_ref would keep pointing at content that does not actually live there.
- **GARBLED_CHUNK**: with no special handling, this chunk's already-meaningless text would simply carry forward into the new corpus unchanged — occupying an embedding slot and consuming retrieval budget for content that maps to nothing readable in the source PDF.
- **F7_EMPTY_CHUNK**: an empty/near-empty chunk re-ingested unchanged contributes nothing retrievable either way — low-impact, but also a wasted embedding call if re-embedded rather than dropped.
- **APPARATUS_GAP_BENIGN**: gap content here is dominated by non-prose apparatus (running heads, plate captions, roman numerals, single-char diagram labels) — a re-ingest that never recovers this gap loses nothing of doctrinal value.
- **UNCLASSIFIED**: unknown consequence by construction — this is exactly the case a fallback rule cannot yet be written for; more evidence is needed before any seeder logic touches these units.

---

## (d) CLAUDE.md anchor cross-check

| Anchor | page_ref | Hit cohorts |
|---|---|---|
| p145_c0 | 145 | (none — page is clean in every cohort here) |
| p139_c0 | 139 | (none — page is clean in every cohort here) |
| p163_c1 | 163 | (none — page is clean in every cohort here) |
| p159_c2 | 159 | (none — page is clean in every cohort here) |

None of the four CLAUDE.md-named anchors' pages appear in this pathology cohort (overlap, non-monotonic, lowest-15-coverage, zero-match, or empty-token). U1 GATE 2's id-mappability claim for all four stands without a pathology caveat from this triage.
