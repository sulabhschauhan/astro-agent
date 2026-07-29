# BIDIRECTIONAL CORRUPTION CENSUS — S80 U0.5 — Cheiro only

Read-only, diagnostics-only. No repair logic, no alignment/merge function meant for production use. Scope: cheiroslanguageo00chei_1, pages with native_char_count > 0 only. See scripts/bidirectional_corruption_census_S80.py module docstring for full method.

- Oracle: nltk 3.9.1, corpus 'words' (nltk.corpus.words), 234377 lowercased entries
- source_pdf_sha256: `0e3271fbd3108110bd9217e662f9064206ec2d8435a6f2768ee4786440b9ccb1`
- In-scope pages (native_char_count > 0): 245

---

## (d) Mandatory self-checks

| Assertion | Expected | Observed | Status |
|---|---|---|---|
| Cheiro page count == 310 | 310 | 310 | PASS |
| Cheiro p157 native contains "Plate XVIII" | present | present | PASS |
| Cheiro p158 native char_count == 0 | 0 | 0 | PASS |
| Cheiro p156 native contains "CHAPTER X" | present | present | PASS |

---

## (a) Aggregate counts, C1–C5, across all in-scope pages

| Class | Count | % of classified pairs (C1-C4) or all tokens (C5) |
|---|---|---|
| C1 corpus_corrupt_native_clean | 832 | 17.88% |
| C2 native_corrupt_corpus_clean | 210 | 4.51% |
| C3 both_corrupt | 343 | 7.37% |
| C4 both_valid_divergent | 276 | 5.93% |
| C5 unalignable | 2991 | 64.29% |
| **Total non-matching token positions** | **4652** | 100% |

**C1:C2 ratio = 3.962** (C1=832, C2=210)

**This ratio IS the finding.** A C1:C2 ratio far above 1 would mean corpus-side corruption dominates and native-side corruption is comparatively rare (consistent with U0's original one-directional evidence). A ratio near 1 or below means native-side corruption is NOT rare — blind replacement (always prefer native) would systematically reintroduce errors on the C2 pages. No policy conclusion is drawn here; see closing note.

**Oracle-noise flag:** 193 of the 4652 classified C1/C2/C3 token positions involve a Roman numeral (e.g. "XVIII") or the proper noun "Cheiro" on at least one side — both absent from a general-English wordlist by construction, and will misclassify as "not a real word" regardless of whether the OCR actually corrupted anything. Not corrected for above; reported as a measured caveat on the C1/C2/C3 totals, per the oracle limitation noted in the script docstring.

---

## (b) Top 40 token pairs by frequency — C1 and C2 separately

### C1 (corpus_corrupt_native_clean) — top 40

| # | native | corpus | count | example page_index (0-based) |
|---|---|---|---|---|
| 1 | life | hfe | 34 | 31 |
| 2 | in | im | 22 | 12 |
| 3 | line | hne | 20 | 39 |
| 4 | line | lne | 15 | 134 |
| 5 | success | suecess | 14 | 43 |
| 6 | Hand | Hanp | 13 | 19 |
| 7 | Mercury | Mereury | 10 | 119 |
| 8 | and | aud | 9 | 28 |
| 9 | little | httle | 8 | 39 |
| 10 | conic | conie | 8 | 55 |
| 11 | lias | has | 7 | 22 |
| 12 | distinct | distinet | 6 | 10 |
| 13 | like | hke | 6 | 30 |
| 14 | his | Ins | 5 | 41 |
| 15 | brilliancy | brillianey | 5 | 69 |
| 16 | believe | beheve | 4 | 10 |
| 17 | Philosophic | Philosophie | 4 | 15 |
| 18 | If | Tf | 4 | 34 |
| 19 | artistic | artistie | 4 | 55 |
| 20 | slightly | shghtly | 4 | 68 |
| 21 | f | Af | 4 | 135 |
| 22 | line | lme | 4 | 144 |
| 23 | you | vou | 4 | 224 |
| 24 | Lady | Lapy | 3 | 13 |
| 25 | like | lke | 3 | 28 |
| 26 | palmistry | palnistry | 3 | 29 |
| 27 | I | Iam | 3 | 31 |
| 28 | convince | convinee | 3 | 33 |
| 29 | psychic | psychie | 3 | 47 |
| 30 | once | onee | 3 | 55 |
| 31 | it | itis | 3 | 60 |
| 32 | The | Lhe | 3 | 64 |
| 33 | palm | pahn | 3 | 86 |
| 34 | force | foree | 3 | 87 |
| 35 | tendency | tendeney | 3 | 89 |
| 36 | It | Itis | 3 | 186 |
| 37 | Cheiromancy | Cheiromaney | 2 | 10 |
| 38 | In | Jn | 2 | 10 |
| 39 | John | Joun | 2 | 13 |
| 40 | Conic | Conie | 2 | 15 |

### C2 (native_corrupt_corpus_clean) — top 40

| # | native | corpus | count | example page_index (0-based) |
|---|---|---|---|---|
| 1 | XVII | X | 5 | 127 |
| 2 | tlie | the | 4 | 85 |
| 3 | liue | line | 4 | 135 |
| 4 | op | OF | 3 | 16 |
| 5 | lines | limes | 3 | 39 |
| 6 | bv | by | 3 | 136 |
| 7 | XX | X | 3 | 162 |
| 8 | liis | his | 2 | 36 |
| 9 | tlieir | their | 2 | 60 |
| 10 | mancy | maney | 2 | 84 |
| 11 | XVIII | X | 2 | 134 |
| 12 | monev | money | 2 | 135 |
| 13 | XXI | X | 2 | 164 |
| 14 | STAE | STAR | 2 | 187 |
| 15 | tbe | the | 1 | 6 |
| 16 | tbc | the | 1 | 6 |
| 17 | powrer | power | 1 | 10 |
| 18 | mucli | much | 1 | 12 |
| 19 | TV | W | 1 | 13 |
| 20 | XY | Contents | 1 | 15 |
| 21 | Yenus | Venus | 1 | 15 |
| 22 | IV | ce | 1 | 15 |
| 23 | XIII | i | 1 | 15 |
| 24 | XIV | cee | 1 | 15 |
| 25 | op | oF | 1 | 16 |
| 26 | XXII | cee | 1 | 19 |
| 27 | XXXIII | ce | 1 | 19 |
| 28 | XLYI | Lolo | 1 | 20 |
| 29 | e'en | e | 1 | 22 |
| 30 | wTish | wish | 1 | 23 |
| 31 | cheA | cheir | 1 | 25 |
| 32 | remaik | remark | 1 | 26 |
| 33 | histoiy | history | 1 | 26 |
| 34 | Falmistiy | Palmistry | 1 | 26 |
| 35 | theiefoie | therefore | 1 | 26 |
| 36 | wdio | who | 1 | 28 |
| 37 | whicli | which | 1 | 29 |
| 38 | jwobably | probably | 1 | 29 |
| 39 | iii | i | 1 | 29 |
| 40 | ei | very | 1 | 30 |

---

## Discovered ligature/substitution patterns (C1+C2+C3 pooled), top 40

| # | native_substr → corpus_substr | frequency |
|---|---|---|
| 1 | c → e | 248 |
| 2 | li → h | 189 |
| 3 | i → Ø | 46 |
| 4 | u → n | 45 |
| 5 | n → m | 43 |
| 6 | n → u | 35 |
| 7 | in → m | 33 |
| 8 | i → l | 31 |
| 9 | Ø → e | 26 |
| 10 | d → p | 23 |
| 11 | Ø → a | 22 |
| 12 | v → y | 22 |
| 13 | 's → Ø | 22 |
| 14 | y → v | 19 |
| 15 | c → Ø | 17 |
| 16 | i → t | 16 |
| 17 | m → n | 12 |
| 18 | r → v | 12 |
| 19 | i → r | 12 |
| 20 | l → i | 12 |
| 21 | e → r | 11 |
| 22 | l → Ø | 10 |
| 23 | n → Ø | 10 |
| 24 | r → Ø | 9 |
| 25 | x → n | 9 |
| 26 | Ø → n | 9 |
| 27 | ri → n | 8 |
| 28 | f → t | 8 |
| 29 | i → h | 7 |
| 30 | h → Ø | 7 |
| 31 | h → u | 6 |
| 32 | Ø → i | 6 |
| 33 | m → in | 6 |
| 34 | o → e | 6 |
| 35 | Ø → y | 6 |
| 36 | Ø → is | 6 |
| 37 | vii → Ø | 6 |
| 38 | x → Ø | 5 |
| 39 | a → Ø | 5 |
| 40 | h → l | 5 |

---

## (c) Per-page table (all in-scope pages) + top 10 by C2 count

### Top 10 pages by C2 count — the pages Path C (native-preferred replacement) would damage

| Rank | page_index | page_ref | native_chars | corpus_chars | C1 | C2 | C3 | C4 | C5 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 140 | 141 | 381 | 592 | 11 | 24 | 25 | 5 | 33 |
| 2 | 135 | 136 | 2404 | 2408 | 5 | 10 | 8 | 4 | 8 |
| 3 | 15 | 16 | 1431 | 1587 | 7 | 5 | 3 | 2 | 75 |
| 4 | 112 | 113 | 1374 | 1379 | 4 | 5 | 1 | 0 | 1 |
| 5 | 16 | 17 | 1220 | 1912 | 1 | 4 | 5 | 1 | 70 |
| 6 | 26 | 27 | 2473 | 2473 | 1 | 4 | 4 | 0 | 2 |
| 7 | 126 | 127 | 2347 | 2337 | 2 | 4 | 0 | 1 | 4 |
| 8 | 29 | 30 | 2307 | 2305 | 4 | 3 | 2 | 1 | 1 |
| 9 | 30 | 31 | 2393 | 2390 | 8 | 3 | 2 | 1 | 3 |
| 10 | 34 | 35 | 2391 | 2389 | 10 | 3 | 1 | 3 | 0 |

### Full per-page table (all in-scope pages)

| page_index | page_ref | native_chars | corpus_chars | chunk_count | C1 | C2 | C3 | C4 | C5 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 2 | 1345 | 0 | 0 | 0 | 0 | 0 | 0 | 225 |
| 2 | 3 | 2274 | 0 | 0 | 0 | 0 | 0 | 0 | 376 |
| 6 | 7 | 1370 | 1410 | 2 | 4 | 2 | 3 | 2 | 13 |
| 7 | 8 | 177 | 0 | 0 | 0 | 0 | 0 | 0 | 22 |
| 8 | 9 | 207 | 0 | 0 | 0 | 0 | 0 | 0 | 38 |
| 10 | 11 | 1882 | 1879 | 3 | 10 | 1 | 1 | 0 | 1 |
| 11 | 12 | 2461 | 2461 | 4 | 1 | 0 | 0 | 0 | 2 |
| 12 | 13 | 2217 | 2224 | 3 | 1 | 1 | 2 | 0 | 0 |
| 13 | 14 | 1479 | 1508 | 3 | 8 | 1 | 5 | 1 | 7 |
| 14 | 15 | 962 | 1447 | 2 | 8 | 0 | 3 | 0 | 50 |
| 15 | 16 | 1431 | 1587 | 3 | 7 | 5 | 3 | 2 | 75 |
| 16 | 17 | 1220 | 1912 | 3 | 1 | 4 | 5 | 1 | 70 |
| 18 | 19 | 991 | 0 | 0 | 0 | 0 | 0 | 0 | 142 |
| 19 | 20 | 1549 | 2622 | 5 | 11 | 2 | 11 | 9 | 130 |
| 20 | 21 | 493 | 737 | 2 | 12 | 1 | 5 | 5 | 24 |
| 22 | 23 | 1678 | 1680 | 3 | 1 | 1 | 1 | 1 | 3 |
| 23 | 24 | 2537 | 2532 | 3 | 3 | 1 | 1 | 0 | 3 |
| 24 | 25 | 2374 | 2374 | 2 | 2 | 0 | 3 | 0 | 0 |
| 25 | 26 | 2452 | 2458 | 3 | 3 | 1 | 1 | 0 | 0 |
| 26 | 27 | 2473 | 2473 | 2 | 1 | 4 | 4 | 0 | 2 |
| 27 | 28 | 2451 | 2446 | 3 | 4 | 0 | 0 | 0 | 3 |
| 28 | 29 | 2472 | 2470 | 1 | 7 | 1 | 4 | 2 | 0 |
| 29 | 30 | 2307 | 2305 | 2 | 4 | 3 | 2 | 1 | 1 |
| 30 | 31 | 2393 | 2390 | 3 | 8 | 3 | 2 | 1 | 3 |
| 31 | 32 | 2416 | 2411 | 3 | 7 | 1 | 3 | 4 | 5 |
| 32 | 33 | 2796 | 2799 | 4 | 7 | 1 | 2 | 2 | 4 |
| 33 | 34 | 3154 | 3159 | 3 | 6 | 0 | 4 | 0 | 2 |
| 34 | 35 | 2391 | 2389 | 3 | 10 | 3 | 1 | 3 | 0 |
| 35 | 36 | 2407 | 2406 | 2 | 2 | 1 | 2 | 0 | 1 |
| 36 | 37 | 2535 | 2528 | 3 | 7 | 1 | 1 | 3 | 0 |
| 37 | 38 | 2410 | 2405 | 3 | 8 | 0 | 1 | 1 | 7 |
| 38 | 39 | 2430 | 2426 | 2 | 7 | 1 | 3 | 4 | 5 |
| 39 | 40 | 2490 | 2479 | 3 | 5 | 1 | 5 | 2 | 2 |
| 40 | 41 | 2618 | 2612 | 1 | 6 | 2 | 2 | 2 | 0 |
| 41 | 42 | 2558 | 2553 | 3 | 11 | 1 | 1 | 0 | 2 |
| 42 | 43 | 2464 | 2463 | 4 | 6 | 0 | 1 | 2 | 3 |
| 43 | 44 | 2502 | 2497 | 3 | 8 | 3 | 1 | 4 | 4 |
| 44 | 45 | 1145 | 1142 | 1 | 2 | 0 | 0 | 1 | 1 |
| 46 | 47 | 1404 | 1409 | 2 | 3 | 2 | 1 | 4 | 1 |
| 47 | 48 | 1797 | 1803 | 2 | 4 | 1 | 1 | 1 | 3 |
| 49 | 50 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| 50 | 51 | 1961 | 1960 | 2 | 4 | 1 | 1 | 4 | 0 |
| 51 | 52 | 1808 | 1808 | 2 | 4 | 0 | 2 | 0 | 1 |
| 52 | 53 | 37 | 0 | 0 | 0 | 0 | 0 | 0 | 6 |
| 54 | 55 | 1992 | 1996 | 3 | 5 | 1 | 3 | 1 | 3 |
| 55 | 56 | 2431 | 2427 | 2 | 13 | 1 | 3 | 4 | 4 |
| 56 | 57 | 1959 | 1963 | 3 | 0 | 0 | 0 | 1 | 1 |
| 57 | 58 | 1958 | 1957 | 3 | 4 | 0 | 2 | 1 | 0 |
| 58 | 59 | 41 | 0 | 0 | 0 | 0 | 0 | 0 | 7 |
| 60 | 61 | 1867 | 1863 | 2 | 2 | 2 | 1 | 0 | 3 |
| 61 | 62 | 2013 | 2005 | 2 | 5 | 0 | 1 | 0 | 2 |
| 62 | 63 | 42 | 0 | 0 | 0 | 0 | 0 | 0 | 7 |
| 64 | 65 | 2565 | 2564 | 2 | 6 | 2 | 0 | 3 | 3 |
| 65 | 66 | 703 | 705 | 1 | 0 | 2 | 1 | 0 | 1 |
| 67 | 68 | 37 | 0 | 0 | 0 | 0 | 0 | 0 | 7 |
| 68 | 69 | 1922 | 1925 | 2 | 9 | 0 | 1 | 1 | 1 |
| 69 | 70 | 2557 | 2559 | 3 | 6 | 0 | 2 | 3 | 1 |
| 70 | 71 | 1607 | 1600 | 2 | 4 | 0 | 0 | 2 | 1 |
| 71 | 72 | 1952 | 1948 | 2 | 7 | 1 | 3 | 0 | 3 |
| 74 | 75 | 2522 | 2521 | 3 | 7 | 0 | 1 | 0 | 0 |
| 75 | 76 | 1721 | 1715 | 1 | 2 | 0 | 4 | 0 | 1 |
| 77 | 78 | 26 | 0 | 0 | 0 | 0 | 0 | 0 | 5 |
| 78 | 79 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 80 | 81 | 1870 | 1868 | 2 | 11 | 1 | 4 | 4 | 0 |
| 81 | 82 | 616 | 616 | 1 | 1 | 1 | 1 | 0 | 1 |
| 83 | 84 | 64 | 0 | 0 | 0 | 0 | 0 | 0 | 11 |
| 84 | 85 | 1939 | 1938 | 2 | 3 | 2 | 0 | 2 | 1 |
| 85 | 86 | 2571 | 2568 | 1 | 5 | 1 | 4 | 1 | 3 |
| 86 | 87 | 2578 | 2571 | 2 | 13 | 1 | 0 | 6 | 2 |
| 87 | 88 | 2117 | 2117 | 3 | 6 | 2 | 1 | 3 | 3 |
| 88 | 89 | 2203 | 2205 | 3 | 6 | 0 | 1 | 3 | 3 |
| 89 | 90 | 2450 | 2448 | 3 | 10 | 0 | 4 | 2 | 4 |
| 91 | 92 | 82 | 0 | 0 | 0 | 0 | 0 | 0 | 12 |
| 92 | 93 | 1953 | 1950 | 2 | 3 | 2 | 3 | 1 | 4 |
| 93 | 94 | 1870 | 1869 | 1 | 6 | 2 | 1 | 2 | 5 |
| 94 | 95 | 1609 | 1616 | 3 | 6 | 1 | 3 | 1 | 3 |
| 95 | 96 | 2116 | 2120 | 4 | 3 | 0 | 1 | 1 | 2 |
| 96 | 97 | 605 | 604 | 1 | 0 | 1 | 0 | 0 | 1 |
| 97 | 98 | 1586 | 1582 | 2 | 6 | 3 | 1 | 3 | 2 |
| 98 | 99 | 960 | 964 | 2 | 3 | 1 | 0 | 3 | 1 |
| 99 | 100 | 1647 | 1648 | 3 | 5 | 1 | 3 | 1 | 1 |
| 100 | 101 | 17 | 266 | 1 | 0 | 0 | 1 | 0 | 42 |
| 103 | 104 | 21 | 0 | 0 | 0 | 0 | 0 | 0 | 5 |
| 104 | 105 | 1754 | 1763 | 3 | 3 | 1 | 0 | 0 | 1 |
| 105 | 106 | 1295 | 1299 | 2 | 0 | 1 | 1 | 0 | 0 |
| 106 | 107 | 1817 | 1820 | 3 | 3 | 0 | 0 | 1 | 2 |
| 107 | 108 | 2249 | 2243 | 3 | 3 | 1 | 1 | 5 | 1 |
| 109 | 110 | 33 | 0 | 0 | 0 | 0 | 0 | 0 | 7 |
| 110 | 111 | 1830 | 1884 | 2 | 10 | 3 | 5 | 3 | 7 |
| 111 | 112 | 1675 | 1675 | 3 | 2 | 1 | 4 | 4 | 4 |
| 112 | 113 | 1374 | 1379 | 2 | 4 | 5 | 1 | 0 | 1 |
| 113 | 114 | 1610 | 1608 | 3 | 3 | 0 | 1 | 1 | 0 |
| 114 | 115 | 2020 | 2026 | 3 | 0 | 0 | 0 | 0 | 0 |
| 115 | 116 | 2351 | 2353 | 2 | 1 | 0 | 1 | 0 | 0 |
| 116 | 117 | 1689 | 1698 | 2 | 8 | 0 | 0 | 2 | 1 |
| 117 | 118 | 2458 | 2453 | 3 | 9 | 1 | 3 | 2 | 2 |
| 118 | 119 | 1010 | 1013 | 2 | 1 | 1 | 0 | 0 | 1 |
| 119 | 120 | 1189 | 1195 | 3 | 7 | 0 | 9 | 2 | 4 |
| 120 | 121 | 34 | 204 | 1 | 0 | 0 | 0 | 0 | 38 |
| 122 | 123 | 1100 | 1108 | 1 | 3 | 0 | 1 | 0 | 0 |
| 123 | 124 | 1847 | 1855 | 3 | 1 | 1 | 1 | 0 | 0 |
| 124 | 125 | 114 | 219 | 1 | 4 | 1 | 0 | 1 | 38 |
| 126 | 127 | 2347 | 2337 | 3 | 2 | 4 | 0 | 1 | 4 |
| 127 | 128 | 1737 | 1740 | 3 | 1 | 1 | 3 | 3 | 10 |
| 128 | 129 | 1885 | 1890 | 2 | 2 | 2 | 0 | 2 | 1 |
| 129 | 130 | 962 | 964 | 1 | 0 | 0 | 2 | 0 | 1 |
| 131 | 132 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| 132 | 133 | 1785 | 1784 | 2 | 2 | 2 | 0 | 1 | 1 |
| 133 | 134 | 2197 | 2197 | 4 | 6 | 3 | 0 | 1 | 7 |
| 134 | 135 | 2400 | 2395 | 3 | 4 | 1 | 2 | 3 | 5 |
| 135 | 136 | 2404 | 2408 | 4 | 5 | 10 | 8 | 4 | 8 |
| 136 | 137 | 2156 | 2148 | 4 | 11 | 2 | 4 | 0 | 8 |
| 137 | 138 | 2260 | 2260 | 3 | 6 | 1 | 2 | 3 | 5 |
| 138 | 139 | 2238 | 2239 | 3 | 5 | 1 | 1 | 0 | 0 |
| 139 | 140 | 1562 | 1565 | 3 | 1 | 1 | 1 | 0 | 2 |
| 140 | 141 | 381 | 592 | 1 | 11 | 24 | 25 | 5 | 33 |
| 143 | 144 | 11 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| 144 | 145 | 1698 | 1699 | 3 | 2 | 2 | 0 | 3 | 2 |
| 145 | 146 | 2307 | 2311 | 3 | 6 | 3 | 1 | 1 | 7 |
| 146 | 147 | 2075 | 2092 | 4 | 5 | 0 | 2 | 0 | 2 |
| 147 | 148 | 1639 | 1648 | 3 | 4 | 1 | 2 | 3 | 3 |
| 148 | 149 | 1785 | 1779 | 2 | 9 | 1 | 2 | 1 | 2 |
| 149 | 150 | 2078 | 2080 | 3 | 6 | 1 | 2 | 4 | 4 |
| 150 | 151 | 2289 | 2290 | 3 | 2 | 2 | 0 | 0 | 2 |
| 151 | 152 | 903 | 902 | 2 | 2 | 0 | 1 | 0 | 2 |
| 152 | 153 | 1823 | 1818 | 3 | 4 | 1 | 2 | 1 | 5 |
| 153 | 154 | 2266 | 2260 | 2 | 10 | 0 | 2 | 2 | 3 |
| 154 | 155 | 1051 | 1050 | 2 | 1 | 0 | 4 | 2 | 0 |
| 155 | 156 | 1719 | 1710 | 3 | 3 | 2 | 0 | 0 | 2 |
| 156 | 157 | 12 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| 158 | 159 | 2312 | 2316 | 4 | 2 | 0 | 0 | 1 | 3 |
| 159 | 160 | 2130 | 2136 | 4 | 4 | 0 | 1 | 1 | 1 |
| 160 | 161 | 369 | 370 | 1 | 0 | 0 | 1 | 1 | 1 |
| 161 | 162 | 1757 | 1745 | 3 | 12 | 2 | 0 | 4 | 1 |
| 162 | 163 | 2293 | 2298 | 4 | 9 | 1 | 0 | 1 | 3 |
| 163 | 164 | 2281 | 2284 | 4 | 9 | 0 | 2 | 1 | 1 |
| 164 | 165 | 1885 | 1886 | 3 | 4 | 2 | 3 | 3 | 8 |
| 165 | 166 | 1652 | 1657 | 3 | 3 | 1 | 2 | 0 | 0 |
| 166 | 167 | 48 | 0 | 0 | 0 | 0 | 0 | 0 | 7 |
| 167 | 168 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 168 | 169 | 2157 | 2166 | 4 | 0 | 0 | 1 | 0 | 0 |
| 169 | 170 | 895 | 899 | 1 | 3 | 0 | 0 | 0 | 1 |
| 170 | 171 | 1725 | 1736 | 2 | 5 | 1 | 2 | 2 | 6 |
| 171 | 172 | 1536 | 1535 | 2 | 8 | 0 | 2 | 1 | 4 |
| 172 | 173 | 1178 | 1181 | 2 | 1 | 1 | 2 | 1 | 2 |
| 173 | 174 | 1744 | 1745 | 3 | 1 | 0 | 0 | 3 | 3 |
| 174 | 175 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| 176 | 177 | 1718 | 1716 | 2 | 1 | 1 | 0 | 2 | 2 |
| 177 | 178 | 1771 | 1775 | 2 | 6 | 0 | 2 | 2 | 1 |
| 178 | 179 | 2285 | 2286 | 4 | 2 | 2 | 0 | 1 | 2 |
| 179 | 180 | 2032 | 2049 | 4 | 2 | 1 | 0 | 2 | 6 |
| 180 | 181 | 2436 | 2436 | 2 | 2 | 1 | 3 | 4 | 3 |
| 181 | 182 | 1345 | 1344 | 2 | 2 | 0 | 0 | 1 | 0 |
| 182 | 183 | 1654 | 1653 | 3 | 2 | 2 | 0 | 1 | 0 |
| 183 | 184 | 1202 | 1212 | 2 | 0 | 1 | 1 | 0 | 1 |
| 185 | 186 | 47 | 0 | 0 | 0 | 0 | 0 | 0 | 7 |
| 186 | 187 | 1741 | 1738 | 3 | 3 | 0 | 2 | 2 | 8 |
| 187 | 188 | 2071 | 2074 | 3 | 4 | 1 | 2 | 1 | 3 |
| 188 | 189 | 1775 | 1777 | 2 | 3 | 0 | 1 | 2 | 7 |
| 189 | 190 | 934 | 938 | 1 | 1 | 1 | 2 | 0 | 1 |
| 190 | 191 | 1706 | 0 | 0 | 0 | 0 | 0 | 0 | 315 |
| 191 | 192 | 722 | 725 | 2 | 2 | 0 | 0 | 0 | 0 |
| 192 | 193 | 1759 | 1767 | 3 | 1 | 1 | 3 | 0 | 2 |
| 193 | 194 | 584 | 590 | 1 | 1 | 0 | 0 | 1 | 1 |
| 195 | 196 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| 196 | 197 | 1695 | 1698 | 3 | 0 | 2 | 2 | 1 | 1 |
| 197 | 198 | 1445 | 1461 | 3 | 2 | 1 | 1 | 0 | 3 |
| 198 | 199 | 1339 | 1348 | 3 | 1 | 0 | 0 | 0 | 1 |
| 199 | 200 | 1900 | 1906 | 3 | 1 | 2 | 2 | 2 | 1 |
| 200 | 201 | 711 | 716 | 1 | 2 | 0 | 1 | 2 | 1 |
| 201 | 202 | 1543 | 1544 | 3 | 3 | 1 | 1 | 0 | 1 |
| 202 | 203 | 1721 | 1723 | 2 | 7 | 0 | 2 | 1 | 1 |
| 203 | 204 | 1818 | 1818 | 3 | 3 | 1 | 1 | 1 | 4 |
| 204 | 205 | 1720 | 1729 | 3 | 2 | 2 | 2 | 0 | 1 |
| 205 | 206 | 1763 | 1764 | 3 | 4 | 0 | 1 | 0 | 3 |
| 206 | 207 | 1707 | 1705 | 2 | 3 | 0 | 3 | 2 | 3 |
| 207 | 208 | 1917 | 1923 | 3 | 3 | 0 | 1 | 0 | 8 |
| 208 | 209 | 889 | 892 | 1 | 2 | 0 | 0 | 0 | 0 |
| 209 | 210 | 1977 | 1974 | 2 | 2 | 1 | 0 | 1 | 1 |
| 210 | 211 | 38 | 0 | 0 | 0 | 0 | 0 | 0 | 7 |
| 212 | 213 | 1705 | 1704 | 2 | 5 | 0 | 3 | 3 | 1 |
| 213 | 214 | 1733 | 1729 | 3 | 1 | 1 | 4 | 2 | 2 |
| 214 | 215 | 2533 | 2540 | 3 | 6 | 0 | 3 | 3 | 28 |
| 215 | 216 | 1667 | 1654 | 2 | 9 | 1 | 1 | 2 | 3 |
| 216 | 217 | 1969 | 1968 | 3 | 9 | 3 | 5 | 4 | 1 |
| 217 | 218 | 606 | 605 | 1 | 1 | 1 | 1 | 0 | 2 |
| 218 | 219 | 1892 | 1888 | 2 | 3 | 1 | 1 | 1 | 2 |
| 219 | 220 | 2303 | 2300 | 3 | 5 | 2 | 6 | 2 | 1 |
| 220 | 221 | 2141 | 2138 | 4 | 6 | 1 | 3 | 1 | 0 |
| 221 | 222 | 1482 | 1484 | 2 | 5 | 0 | 1 | 4 | 0 |
| 222 | 223 | 2258 | 2266 | 2 | 14 | 1 | 5 | 0 | 5 |
| 223 | 224 | 1272 | 1275 | 2 | 5 | 0 | 0 | 2 | 0 |
| 224 | 225 | 1854 | 1855 | 3 | 14 | 1 | 2 | 4 | 0 |
| 225 | 226 | 2495 | 2490 | 4 | 12 | 1 | 0 | 2 | 3 |
| 226 | 227 | 434 | 435 | 1 | 0 | 0 | 1 | 0 | 1 |
| 227 | 228 | 1605 | 1606 | 2 | 2 | 0 | 0 | 2 | 3 |
| 228 | 229 | 2117 | 2114 | 4 | 2 | 1 | 2 | 3 | 3 |
| 229 | 230 | 2222 | 2219 | 4 | 5 | 0 | 2 | 4 | 3 |
| 230 | 231 | 2088 | 2086 | 3 | 4 | 1 | 2 | 3 | 2 |
| 231 | 232 | 1944 | 1956 | 3 | 3 | 1 | 3 | 4 | 3 |
| 234 | 235 | 71 | 0 | 0 | 0 | 0 | 0 | 0 | 12 |
| 236 | 237 | 36 | 0 | 0 | 0 | 0 | 0 | 0 | 8 |
| 238 | 239 | 26 | 0 | 0 | 0 | 0 | 0 | 0 | 5 |
| 240 | 241 | 44 | 0 | 0 | 0 | 0 | 0 | 0 | 7 |
| 242 | 243 | 40 | 0 | 0 | 0 | 0 | 0 | 0 | 8 |
| 244 | 245 | 44 | 0 | 0 | 0 | 0 | 0 | 0 | 9 |
| 245 | 246 | 7 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| 246 | 247 | 82 | 0 | 0 | 0 | 0 | 0 | 0 | 15 |
| 248 | 249 | 49 | 0 | 0 | 0 | 0 | 0 | 0 | 9 |
| 249 | 250 | 12 | 0 | 0 | 0 | 0 | 0 | 0 | 4 |
| 250 | 251 | 85 | 0 | 0 | 0 | 0 | 0 | 0 | 15 |
| 252 | 253 | 64 | 0 | 0 | 0 | 0 | 0 | 0 | 15 |
| 254 | 255 | 49 | 0 | 0 | 0 | 0 | 0 | 0 | 11 |
| 256 | 257 | 93 | 0 | 0 | 0 | 0 | 0 | 0 | 15 |
| 258 | 259 | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 4 |
| 260 | 261 | 43 | 0 | 0 | 0 | 0 | 0 | 0 | 9 |
| 261 | 262 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 262 | 263 | 53 | 0 | 0 | 0 | 0 | 0 | 0 | 13 |
| 264 | 265 | 40 | 0 | 0 | 0 | 0 | 0 | 0 | 8 |
| 266 | 267 | 49 | 0 | 0 | 0 | 0 | 0 | 0 | 9 |
| 267 | 268 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 268 | 269 | 49 | 0 | 0 | 0 | 0 | 0 | 0 | 9 |
| 270 | 271 | 73 | 0 | 0 | 0 | 0 | 0 | 0 | 14 |
| 272 | 273 | 42 | 0 | 0 | 0 | 0 | 0 | 0 | 8 |
| 274 | 275 | 48 | 0 | 0 | 0 | 0 | 0 | 0 | 8 |
| 276 | 277 | 39 | 0 | 0 | 0 | 0 | 0 | 0 | 8 |
| 278 | 279 | 37 | 0 | 0 | 0 | 0 | 0 | 0 | 8 |
| 280 | 281 | 63 | 0 | 0 | 0 | 0 | 0 | 0 | 12 |
| 281 | 282 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 282 | 283 | 132 | 0 | 0 | 0 | 0 | 0 | 0 | 21 |
| 284 | 285 | 43 | 0 | 0 | 0 | 0 | 0 | 0 | 8 |
| 286 | 287 | 86 | 0 | 0 | 0 | 0 | 0 | 0 | 16 |
| 288 | 289 | 51 | 0 | 0 | 0 | 0 | 0 | 0 | 9 |
| 290 | 291 | 54 | 0 | 0 | 0 | 0 | 0 | 0 | 13 |
| 292 | 293 | 39 | 0 | 0 | 0 | 0 | 0 | 0 | 8 |
| 294 | 295 | 51 | 0 | 0 | 0 | 0 | 0 | 0 | 11 |
| 296 | 297 | 45 | 0 | 0 | 0 | 0 | 0 | 0 | 9 |
| 298 | 299 | 1156 | 1168 | 2 | 2 | 0 | 4 | 1 | 3 |
| 299 | 300 | 1961 | 1969 | 3 | 14 | 2 | 5 | 2 | 4 |
| 302 | 303 | 2842 | 2842 | 4 | 24 | 2 | 3 | 3 | 4 |
| 303 | 304 | 2528 | 2538 | 4 | 5 | 1 | 3 | 1 | 1 |
| 304 | 305 | 2703 | 2713 | 4 | 7 | 1 | 0 | 2 | 7 |
| 305 | 306 | 2366 | 2370 | 3 | 9 | 0 | 2 | 1 | 2 |
| 307 | 308 | 1621 | 0 | 0 | 0 | 0 | 0 | 0 | 266 |
| 308 | 309 | 1364 | 0 | 0 | 0 | 0 | 0 | 0 | 234 |

---

## (e) Is p156_c0's rnensal/mensal pair isolated, or representative of a class?

- The exact pair (native="rnensal", corpus="mensal") occurs 1 time(s) on page 156 (the only page it can occur on, by construction of this specific word).
- Its underlying character-level hunk, `rn → m`, was independently discovered (not looked up) by the SAME character-diff mechanism applied to every C1/C2/C3 pair census-wide, and occurs **1** time(s) in total across all 245 in-scope pages (including this one instance).
- **Verdict at the EXACT hunk level: ISOLATED.** The precise `rn → m` two-character hunk does not recur elsewhere in this book's in-scope pages beyond this single p156 instance.
- **However, at a broader level, the underlying failure mode IS a recurring class.** `rn → m` is one specific case of a much larger, independently-discovered cluster of narrow-vertical-stroke ("minim") confusions — m, n, u, rn, ri, and in mutually substituting for one another (the classic OCR minim-ambiguity problem). This broader family accounts for **189** hunk occurrences census-wide (see the table below), dwarfing the single `rn → m` instance. This family grouping is named here for prose ONLY, after seeing which hunks actually recurred in the discovered-pattern table above — it was never fed back into classification.

| native_substr → corpus_substr | frequency |
|---|---|
| u → n | 45 |
| n → m | 43 |
| n → u | 35 |
| in → m | 33 |
| m → n | 12 |
| ri → n | 8 |
| m → in | 6 |
| ri → m | 4 |
| rn → m | 1 |
| m → u | 1 |
| u → m | 1 |

- **Net call: the p156 rnensal/mensal pair's EXACT spelling is a singleton, but the CLASS of error it belongs to (minim/narrow-stroke confusion) is common and recurring in this book's native text layer** — consistent with the C1:C2 ratio above already showing native-side corruption (C2) is far from negligible (4.51% of classified pairs).

---

## (f) Merge policy

**No recommendation is made here.** This report is measurement only, per the instructing prompt's explicit scope. The C1:C2 ratio, the top-40 pair tables, the discovered ligature patterns, and the per-page C2 hotspot table above are the evidence; the policy ruling (whether Path C is a blind native-preferred replacement, a token-level adjudicated merge, or something else) is a design-chat decision made after reading this census, not before.
