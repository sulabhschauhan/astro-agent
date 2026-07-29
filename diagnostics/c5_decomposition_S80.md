# C5 DECOMPOSITION — S80 U0.6 — Cheiro only

Read-only, diagnostics-only. No repair logic, no new alignment design (reuses scripts/bidirectional_corruption_census_S80.py's algorithm via a position-annotated replica, fidelity-checked against its committed sidecar before this report was written). See scripts/c5_decomposition_S80.py module docstring for full subcategory-rule derivation.

- Base oracle: nltk 3.9.1, corpus 'words' (nltk.corpus.words), 234377 lowercased entries
- source_pdf_sha256: `0e3271fbd3108110bd9217e662f9064206ec2d8435a6f2768ee4786440b9ccb1`

---

## Ground-truth self-checks

| Assertion | Expected | Observed | Status |
|---|---|---|---|
| Cheiro page count == 310 | 310 | 310 | PASS |
| Cheiro p157 native contains "Plate XVIII" | present | present | PASS |
| Cheiro p158 native char_count == 0 | 0 | 0 | PASS |
| Cheiro p156 native contains "CHAPTER X" | present | present | PASS |
| Replica fidelity vs committed sidecar (C1-C5 totals) | {'C1': 832, 'C2': 210, 'C3': 343, 'C4': 276, 'C5': 2991} | (matched — see script's own AssertionError guard) | PASS |

---

## (a) C5a vs C5b totals

- **C5a (native_only, corpus lost content): 2419** (80.88% of C5)
- **C5b (corpus_only, native lost content — i.e. what a native-preferred repair would DISCARD): 572** (19.12% of C5)
- **C5a:C5b ratio = 4.229**
- Plainly: the vast majority of C5 is native tokens with no corpus counterpart, not the other way around. Whether that is meaningful depends entirely on subcategory (b) below — see the ordinary_prose_word row specifically.

---

## (b) Subcategory tables, both sides

### C5a (native_only — corpus lost this content)

| Subcategory | Count | % of C5a |
|---|---|---|
| roman_numeral | 517 | 21.37% |
| printed_folio_number_bare_digits | 0 (structurally impossible — see script docstring rule 2's note) | 0.00% |
| plate_caption_fragment | 62 | 2.56% |
| running_head_title_fragment | 258 | 10.67% |
| proper_noun | 38 | 1.57% |
| ordinary_prose_word **<- THE SIGNAL**  | 579 | 23.94% |
| punctuation_single_char_non_alpha | 657 | 27.16% |
| other_unclassified_nonword_fragment | 308 | 12.73% |

### C5b (corpus_only — native lost this content)

| Subcategory | Count | % of C5b |
|---|---|---|
| roman_numeral | 51 | 8.92% |
| printed_folio_number_bare_digits | 0 (structurally impossible — see script docstring rule 2's note) | 0.00% |
| plate_caption_fragment | 0 | 0.00% |
| running_head_title_fragment | 12 | 2.10% |
| proper_noun | 0 | 0.00% |
| ordinary_prose_word **<- THE SIGNAL**  | 146 | 25.52% |
| punctuation_single_char_non_alpha | 85 | 14.86% |
| other_unclassified_nonword_fragment | 278 | 48.60% |

**Ordinary-prose signal, isolated: C5a=579, C5b=146.** Everything else in both tables is boilerplate/structural churn by this taxonomy's own construction (roman numerals, plate captions, running heads, proper nouns, single-char diagram labels, and non-word OCR garbage).

---

## (c) Top 10 pages by ordinary-prose C5 count, both sides

### Top 10 — C5a ordinary-prose (candidate lost doctrine — corpus never captured this native content)

| Rank | page_index | page_ref | c5a_ordinary_prose | native_chars | corpus_chars |
|---|---|---|---|---|---|
| 1 | 190 | 191 | 199 | 1706 | 0 |
| 2 | 18 | 19 | 53 | 991 | 0 |
| 3 | 8 | 9 | 25 | 207 | 0 |
| 4 | 2 | 3 | 19 | 2274 | 0 |
| 5 | 15 | 16 | 16 | 1431 | 1587 |
| 6 | 214 | 215 | 12 | 2533 | 2540 |
| 7 | 308 | 309 | 12 | 1364 | 0 |
| 8 | 7 | 8 | 11 | 177 | 0 |
| 9 | 1 | 2 | 10 | 1345 | 0 |
| 10 | 307 | 308 | 7 | 1621 | 0 |

**Top 3, quoted (~15-word span around the divergent token, from NATIVE text):**

1. page_index=190, token=`CHAPTER` — "CHAPTER XIX THE CKOSS The cross is the"
2. page_index=18, token=`LIST` — "LIST OF ILLUSTRATIONS PLATE PACINO PAGE I The"
3. page_index=8, token=`DEDICATION` — "DEDICATION What do I bring Kind Life tis"

### Top 10 — C5b ordinary-prose (candidate deletion risk — what a native-preferred repair would discard)

| Rank | page_index | page_ref | c5b_ordinary_prose | native_chars | corpus_chars |
|---|---|---|---|---|---|
| 1 | 19 | 20 | 27 | 1549 | 2622 |
| 2 | 100 | 101 | 18 | 17 | 266 |
| 3 | 120 | 121 | 16 | 34 | 204 |
| 4 | 16 | 17 | 15 | 1220 | 1912 |
| 5 | 214 | 215 | 13 | 2533 | 2540 |
| 6 | 124 | 125 | 10 | 114 | 219 |
| 7 | 14 | 15 | 7 | 962 | 1447 |
| 8 | 140 | 141 | 6 | 381 | 592 |
| 9 | 15 | 16 | 5 | 1431 | 1587 |
| 10 | 13 | 14 | 4 | 1479 | 1508 |

**Top 3, quoted (~15-word span around the divergent token, from CORPUS text):**

1. page_index=19, token=`cee` — "PRINCIPAL LINES XVIII MopIrIcaATIONS OF PRINCIPAL LINES cee cee eee eee eee tees cence XIX"
2. page_index=100, token=`tien` — "tien CHIAL BRON ox PS NOCHE terrae BRONCHIAL"
3. page_index=120, token=`Re` — "Re Soy Ane S aer Bra A ALolond"

---

## (d) C5a ordinary-prose: edge-clustered or mid-page? (edge window = first/last 40 tokens)

- Edge-window occurrences: 257 (44.39%)
- Mid-page occurrences: 322 (55.61%)
- **Majority MID-PAGE.** This does NOT look like a chunk-boundary artifact (which would cluster at page edges, where chunker.py's paragraph/window splits happen); it is distributed through the body of the page — consistent with genuine content loss, not a benign boundary effect. Reported as measured, no merge-policy conclusion drawn.

---

## (e) Augmented-oracle C1/C2/C3 delta (retires the U0.5 193-position caveat)

- Roman numerals I-C added to the oracle: 92 entries (all were absent from the base wordlist).
- Task-suggested allowlist words ALREADY covered by the base nltk 'words' corpus (checked, not assumed — no-ops, added for completeness only): hepatica, luna, mensal, saturnian
- Task-suggested allowlist words genuinely NEW to the augmented oracle: cheiro, rascettes

| Class | Original count | Augmented count | Delta |
|---|---|---|---|
| C1 | 832 | 888 | +56 |
| C2 | 210 | 226 | +16 |
| C3 | 343 | 230 | -113 |
| C4 | 276 | 317 | +41 |

**C1:C2 ratio, original oracle: 3.962** (C1=832, C2=210)  
**C1:C2 ratio, augmented oracle: 3.929** (C1=888, C2=226)

Original counts are NOT replaced above — both rows are shown side by side, per instruction. Alignment (which tokens got paired at all) is IDENTICAL between the two runs; only the real-word classification of already-aligned C1-C4 pairs changed.

---

## (f) Merge policy

**No recommendation is made here.** This report is measurement only, per the instructing prompt's explicit scope. The C5a/C5b split, the subcategory tables isolating the ordinary-prose signal, the top-page examples, the edge-vs-mid-page clustering result, and the augmented-oracle delta above are the evidence; the policy ruling is a design-chat decision made after reading this census, not before.
