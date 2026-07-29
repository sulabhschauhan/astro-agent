# CHUNK-TO-NATIVE SPAN MAPPING PROBE — S80 U1 — Cheiro only

Read-only, diagnostics-only. Gates PATH D (re-ingest, seeding new chunk boundaries from existing chunk spans). PATH C (in-place text replacement) is RETIRED -- no align_chunk_to_native() written. No ChromaDB writes, no shadow collection, no re-ingestion. See scripts/span_mapping_probe_S80.py module docstring for full reuse/method detail.

- Oracle: nltk 3.9.1, corpus 'words' (nltk.corpus.words), 234377 lowercased entries
- source_pdf_sha256: `0e3271fbd3108110bd9217e662f9064206ec2d8435a6f2768ee4786440b9ccb1`
- Mapped pages (native_char_count > 0, >=1 live chunk): 180
- Zero-live-chunk pages (native_char_count > 0, 0 chunks): 65

---

## Self-checks

| Assertion | Expected | Observed | Status |
|---|---|---|---|
| Cheiro page count == 310 | 310 | 310 | PASS |
| Cheiro p157 native contains "Plate XVIII" | present | present | PASS |
| Cheiro p158 native char_count == 0 | 0 | 0 | PASS |
| Cheiro p156 native contains "CHAPTER X" | present | present | PASS |
| Cheiro p156 live chunk count == 3 | 3 | 3 | PASS |

---

## (a) GATE 1 — Seeding viability

**CORRECTION (post-publication, docs-only, no re-run):** the figure below was
originally stated as a fraction of all 245 in-scope pages. That denominator
is wrong for a viability rate — 65 of the 245 were never span-mapped at all
(zero live chunks, section (f)), so they cannot be "monotonic AND overlap-
free" in any meaningful sense; folding them into the denominator understates
the real seeding-viable rate among pages a boundary seeder would actually
operate on. The corrected statement, verified directly against the
committed sidecar (`span_mapping_probe_S80_data.json`, no recompute from
PDFs): `mapped_page_count == 180`, confirmed equal to `len(page_records)`;
the 4 non-monotonic pages ([19, 39, 146, 219]) are confirmed a SUBSET of the
14 overlapping pages ([13, 19, 20, 39, 68, 135, 146, 150, 155, 187, 214, 216,
219, 302]) — so the underlying count of 166 seeding-viable pages itself does
not change, only which denominator it is honestly reported against.

- Pages monotonic AND overlap_token_count == 0: **166 / 180 mapped pages (92.22%)**
- Of all 245 in-scope pages, including the 65 never span-mapped: **166 / 245 (67.76%)** — the original, now-superseded-in-place figure, retained here rather than silently deleted.
- Total gap ORDINARY-PROSE tokens across all mapped pages: **33**
- That as a fraction of U0.6's C5a ordinary-prose total (579): **5.70%**

---

## (b) GATE 2 — Id mappability, CLAUDE.md-named anchors

| Anchor | Found | chunk_id | span_start | span_end | span_len | match_ratio | Disjoint from siblings |
|---|---|---|---|---|---|---|---|
| p145_c0 | yes | cheiroslanguageo00chei_1_p145_c0 | 0 | 141 | 142 | 0.9650 | True |
| p139_c0 | yes | cheiroslanguageo00chei_1_p139_c0 | 0 | 109 | 110 | 0.9818 | True |
| p163_c1 | yes | cheiroslanguageo00chei_1_p163_c1 | 145 | 279 | 135 | 0.9701 | True |
| p159_c2 | yes | cheiroslanguageo00chei_1_p159_c2 | 271 | 380 | 110 | 1.0000 | True |

A disjoint, high-match span means the anchor can be mapped to a new chunk id deterministically under Path D. Overlapping or low-match means it cannot, and the labelled set built on that anchor is at risk. No mappability ruling made here.

---

## (c) match_ratio distribution — ALL chunks

- n = 449
- min = 0.0000, p10 = 0.9342, p25 = 0.9594, median = 0.9752, p75 = 0.9877, p90 = 1.0000, max = 1.0000

| Bucket | Count |
|---|---|
| 0.00-0.05 | 4 |
| 0.05-0.10 | 1 |
| 0.10-0.15 | 1 |
| 0.15-0.20 | 1 |
| 0.20-0.25 | 0 |
| 0.25-0.30 | 0 |
| 0.30-0.35 | 1 |
| 0.35-0.40 | 0 |
| 0.40-0.45 | 1 |
| 0.45-0.50 | 0 |
| 0.50-0.55 | 1 |
| 0.55-0.60 | 2 |
| 0.60-0.65 | 0 |
| 0.65-0.70 | 2 |
| 0.70-0.75 | 4 |
| 0.75-0.80 | 1 |
| 0.80-0.85 | 2 |
| 0.85-0.90 | 3 |
| 0.90-0.95 | 49 |
| 0.95-1.00 | 376 |

This distribution is the DERIVED input for a future seeding acceptance threshold. **No threshold is proposed here** — that is a design-chat ruling, with its own scope guard and tuning note, per instruction.

---

## (d) Coverage distribution per page

- min = 0.2778, median = 1.0000, max = 1.0000

### 15 lowest-coverage pages

| Rank | page_index | page_ref | coverage | gap_ordinary_prose_count | chunk_count |
|---|---|---|---|---|---|
| 1 | 124 | 125 | 0.2778 | 2 | 1 |
| 2 | 140 | 141 | 0.3485 | 10 | 1 |
| 3 | 100 | 101 | 0.6667 | 0 | 1 |
| 4 | 193 | 194 | 0.9709 | 1 | 1 |
| 5 | 6 | 7 | 0.9865 | 0 | 2 |
| 6 | 151 | 152 | 0.9877 | 0 | 2 |
| 7 | 226 | 227 | 0.9881 | 0 | 1 |
| 8 | 81 | 82 | 0.9903 | 0 | 1 |
| 9 | 217 | 218 | 0.9910 | 0 | 1 |
| 10 | 105 | 106 | 0.9911 | 0 | 2 |
| 11 | 299 | 300 | 0.9915 | 2 | 3 |
| 12 | 149 | 150 | 0.9916 | 0 | 3 |
| 13 | 231 | 232 | 0.9916 | 1 | 3 |
| 14 | 65 | 66 | 0.9917 | 0 | 1 |
| 15 | 133 | 134 | 0.9925 | 0 | 4 |

---

## (e) Monotonicity / overlap detail

- Non-monotonic pages: **4 / 180**
- Pages with any overlap (overlap_token_count > 0): **14 / 180**

### 3 worst non-monotonic pages

**page_index=19 (page_ref=20)**, 1 adjacent-pair violation(s):

| chunk_id | span_start | span_end |
|---|---|---|
| cheiroslanguageo00chei_1_p20_c0 | 0 | 233 |
| cheiroslanguageo00chei_1_p20_c1 | 45 | 221 |
| cheiroslanguageo00chei_1_p20_c2 | 11 | 158 |
| cheiroslanguageo00chei_1_p20_c3 | 159 | 246 |
| cheiroslanguageo00chei_1_p20_c4 | None | None |

**page_index=39 (page_ref=40)**, 1 adjacent-pair violation(s):

| chunk_id | span_start | span_end |
|---|---|---|
| cheiroslanguageo00chei_1_p40_c0 | 0 | 175 |
| cheiroslanguageo00chei_1_p40_c1 | 176 | 278 |
| cheiroslanguageo00chei_1_p40_c2 | 102 | 452 |

**page_index=146 (page_ref=147)**, 1 adjacent-pair violation(s):

| chunk_id | span_start | span_end |
|---|---|---|
| cheiroslanguageo00chei_1_p147_c0 | 0 | 100 |
| cheiroslanguageo00chei_1_p147_c1 | 101 | 210 |
| cheiroslanguageo00chei_1_p147_c2 | 0 | 326 |
| cheiroslanguageo00chei_1_p147_c3 | 327 | 376 |

### 3 worst overlap pages

**page_index=150 (page_ref=151)**, overlap_token_count=370:

| chunk_id | span_start | span_end |
|---|---|---|
| cheiroslanguageo00chei_1_p151_c0 | 0 | 111 |
| cheiroslanguageo00chei_1_p151_c1 | 0 | 369 |
| cheiroslanguageo00chei_1_p151_c2 | 0 | 405 |

**page_index=219 (page_ref=220)**, overlap_token_count=313:

| chunk_id | span_start | span_end |
|---|---|---|
| cheiroslanguageo00chei_1_p220_c0 | 0 | 163 |
| cheiroslanguageo00chei_1_p220_c1 | 164 | 355 |
| cheiroslanguageo00chei_1_p220_c2 | 43 | 407 |

**page_index=19 (page_ref=20)**, overlap_token_count=223:

| chunk_id | span_start | span_end |
|---|---|---|
| cheiroslanguageo00chei_1_p20_c0 | 0 | 233 |
| cheiroslanguageo00chei_1_p20_c1 | 45 | 221 |
| cheiroslanguageo00chei_1_p20_c2 | 11 | 158 |
| cheiroslanguageo00chei_1_p20_c3 | 159 | 246 |
| cheiroslanguageo00chei_1_p20_c4 | None | None |

---

## (f) Zero-live-chunk pages (NOT span-mapped — recoverable under Path D)

| page_index | page_ref | native_char_count | ordinary_prose_token_count |
|---|---|---|---|
| 1 | 2 | 1345 | 10 |
| 2 | 3 | 2274 | 19 |
| 7 | 8 | 177 | 11 |
| 8 | 9 | 207 | 25 |
| 18 | 19 | 991 | 53 |
| 49 | 50 | 16 | 1 |
| 52 | 53 | 37 | 2 |
| 58 | 59 | 41 | 3 |
| 62 | 63 | 42 | 3 |
| 67 | 68 | 37 | 3 |
| 77 | 78 | 26 | 1 |
| 78 | 79 | 1 | 0 |
| 83 | 84 | 64 | 4 |
| 91 | 92 | 82 | 6 |
| 103 | 104 | 21 | 0 |
| 109 | 110 | 33 | 0 |
| 131 | 132 | 10 | 0 |
| 143 | 144 | 11 | 0 |
| 156 | 157 | 12 | 0 |
| 166 | 167 | 48 | 1 |
| 167 | 168 | 2 | 0 |
| 174 | 175 | 9 | 0 |
| 185 | 186 | 47 | 1 |
| 190 | 191 | 1706 | 199 |
| 195 | 196 | 10 | 0 |
| 210 | 211 | 38 | 3 |
| 234 | 235 | 71 | 3 |
| 236 | 237 | 36 | 1 |
| 238 | 239 | 26 | 0 |
| 240 | 241 | 44 | 1 |
| 242 | 243 | 40 | 1 |
| 244 | 245 | 44 | 1 |
| 245 | 246 | 7 | 0 |
| 246 | 247 | 82 | 5 |
| 248 | 249 | 49 | 2 |
| 249 | 250 | 12 | 0 |
| 250 | 251 | 85 | 4 |
| 252 | 253 | 64 | 3 |
| 254 | 255 | 49 | 2 |
| 256 | 257 | 93 | 4 |
| 258 | 259 | 20 | 1 |
| 260 | 261 | 43 | 0 |
| 261 | 262 | 1 | 0 |
| 262 | 263 | 53 | 1 |
| 264 | 265 | 40 | 1 |
| 266 | 267 | 49 | 2 |
| 267 | 268 | 2 | 0 |
| 268 | 269 | 49 | 2 |
| 270 | 271 | 73 | 4 |
| 272 | 273 | 42 | 1 |
| 274 | 275 | 48 | 2 |
| 276 | 277 | 39 | 2 |
| 278 | 279 | 37 | 0 |
| 280 | 281 | 63 | 2 |
| 281 | 282 | 1 | 0 |
| 282 | 283 | 132 | 5 |
| 284 | 285 | 43 | 2 |
| 286 | 287 | 86 | 5 |
| 288 | 289 | 51 | 1 |
| 290 | 291 | 54 | 2 |
| 292 | 293 | 39 | 2 |
| 294 | 295 | 51 | 2 |
| 296 | 297 | 45 | 1 |
| 307 | 308 | 1621 | 7 |
| 308 | 309 | 1364 | 12 |

Under Path C these pages were permanently empty (no corpus text to align against). Under Path D, a fresh re-ingest would create new chunks for these pages from scratch -- recoverable, not gated on span-mapping at all.

---

## (g) C5b ordinary-prose re-check (retires the U0.6 146-token caveat)

- Regenerated total: **146** (matches U0.6's already-reported 146 — fidelity-checked before this section was trusted)
- Sits inside a span-mapped chunk (the token's own chunk has a valid, non-None span on this probe): **146 / 146**
- OCR-garbage-like by the stated heuristic (repeated-char/short-unit run, or a 3+ run of same vowel/consonant class): **4 / 146**

These two counts are NOT a partition — a token can be both (garbage sitting inside an otherwise well-mapped chunk), either, or neither. Both are reported as independent measurements, per instruction.

---

## (h) Recommendation

**None made.** No ruling on seeding viability, match_ratio acceptance thresholds, or Path D itself — report only, per instruction. The gate 1/2 numbers, the match_ratio and coverage distributions, the monotonicity/overlap detail, the zero-chunk-page list, and the C5b recheck above are the evidence for that ruling.
