# Targeted Delete Dry-Run -- X / X_c<N> Duplicate Chunks

**Generated:** 2026-06-21 12:06:05 UTC  
**Collection:** `astro_chunks` @ `data/chroma_db`  
**Read-only run** -- no `.delete()` / `.update()` / `.upsert()` / `.add()` calls made by this script. Single bulk `.get()` read, all filtering done in memory.

## 1. Pre-state

- Total chunks in collection: **11688**
- Suffix-chunks (chunk_id matches `_c\d+$`, condition 1): 11688
  (= total chunks. Expected, not a bug: the locked chunk metadata schema appends `_c{index}` to every sub-chunk unconditionally, so condition 1 alone is never discriminating -- condition 2 below is the first filter that actually narrows anything.)
- ...of which the stripped parent id also exists (conditions 1+2): 3945
- ...of which text was NOT byte-identical to the parent (condition 3 failed -- excluded outright, not a downgrade): 0
- **Candidates passing all four invariant conditions (the delete plan): 3945**
- **Candidates downgraded to human review (condition 4 failed): 0**
- Of the 3945 accepted candidates, 0 have an image_path/word_count divergence from their parent (flagged, not excluded).

No candidates were downgraded -- every suffix/parent/text match also matched on all five strict metadata fields.

## 2. Per-book candidate count

| book_name | accepted candidates |
|---|---|
| Deva-keralam | 672 |
| Muhurtha-Chinthamani | 604 |
| Prasna Marga 1 | 517 |
| Jataka Parijata with explanation of Pt. Kapileshvara Shastri and Vimala Hindi Tika of Pt. Shri Matri Prasad Shastri Series No. 10 - Kashi Sanskrit Series | 504 |
| Prasna Marga 2 | 431 |
| Sarvartha-Chintamani | 423 |
| Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan | 422 |
| uttkalamrita-kalidas-ps-sastri | 372 |

No candidates fall in the 6 clean books (BPHS - 1 RSanthanam, BPHS - 2 RSanthanam, Jyotish_Lal Kitab_B.M. Gosvami, Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri, Saravali of Kalyana Varma Santhanam R. (Astrology), cheiroslanguageo00chei_1). Consistent with the chunking-code audit's finding that only the 8 books re-chunked from already-chunked progress files are affected.

## 3. Spot-check sample (10 random accepted pairs, seed=23)

### `uttkalamrita-kalidas-ps-sastri_p176_c1`  (kept)  vs  `uttkalamrita-kalidas-ps-sastri_p176_c1_c0`  (delete candidate)

| field | parent (kept) | child (delete candidate) |
|---|---|---|
| book_name | uttkalamrita-kalidas-ps-sastri | uttkalamrita-kalidas-ps-sastri |
| page_ref | 176 | 176 |
| page_type | text | text |
| language | eng | eng |
| topic | general | general |
| image_path |  |  |
| word_count | 148 | 148 |

Parent text (first 200 chars): `Notes  This is too sweeping a statement. There are many born in Aslesha, and yet the adverse results did not appear.  We give the method accepted by the authorities on Dharma Shastra. Divide the total`  
Child text (first 200 chars): `Notes  This is too sweeping a statement. There are many born in Aslesha, and yet the adverse results did not appear.  We give the method accepted by the authorities on Dharma Shastra. Divide the total`

### `Sarvartha-Chintamani_p38_c0`  (kept)  vs  `Sarvartha-Chintamani_p38_c0_c0`  (delete candidate)

| field | parent (kept) | child (delete candidate) |
|---|---|---|
| book_name | Sarvartha-Chintamani | Sarvartha-Chintamani |
| page_ref | 38 | 38 |
| page_type | text | text |
| language | eng | eng |
| topic | general | general |
| image_path |  |  |
| word_count | 89 | 89 |

Parent text (first 200 chars): `VISVAMITRACHARITRA 17  When the (Brahmastra) weapon of Brahma was invoked, all the three worlds were struck with awe.  When the high-souled Vasishtha consumed even that most terrible Brahmanic weapon `  
Child text (first 200 chars): `VISVAMITRACHARITRA 17  When the (Brahmastra) weapon of Brahma was invoked, all the three worlds were struck with awe.  When the high-souled Vasishtha consumed even that most terrible Brahmanic weapon `

### `uttkalamrita-kalidas-ps-sastri_p225_c1`  (kept)  vs  `uttkalamrita-kalidas-ps-sastri_p225_c1_c0`  (delete candidate)

| field | parent (kept) | child (delete candidate) |
|---|---|---|
| book_name | uttkalamrita-kalidas-ps-sastri | uttkalamrita-kalidas-ps-sastri |
| page_ref | 225 | 225 |
| page_type | text | text |
| language | eng | eng |
| topic | general | general |
| image_path |  |  |
| word_count | 54 | 54 |

Parent text (first 200 chars): `In the case of Shraddha, there is no ashaucha once the cooking is completed or the food is taken up.  Likewise in a sacrifice when a Brahmana is sprinkled with the sanctified water for initiation, he `  
Child text (first 200 chars): `In the case of Shraddha, there is no ashaucha once the cooking is completed or the food is taken up.  Likewise in a sacrifice when a Brahmana is sprinkled with the sanctified water for initiation, he `

### `Jataka Parijata with explanation of Pt. Kapileshvara Shastri and Vimala Hindi Tika of Pt. Shri Matri Prasad Shastri Series No. 10 - Kashi Sanskrit Series_p115_c0`  (kept)  vs  `Jataka Parijata with explanation of Pt. Kapileshvara Shastri and Vimala Hindi Tika of Pt. Shri Matri Prasad Shastri Series No. 10 - Kashi Sanskrit Series_p115_c0_c0`  (delete candidate)

| field | parent (kept) | child (delete candidate) |
|---|---|---|
| book_name | Jataka Parijata with explanation of Pt. Kapileshvara Shastri and Vimala Hindi Tika of Pt. Shri Matri Prasad Shastri Series No. 10 - Kashi Sanskrit Series | Jataka Parijata with explanation of Pt. Kapileshvara Shastri and Vimala Hindi Tika of Pt. Shri Matri Prasad Shastri Series No. 10 - Kashi Sanskrit Series |
| page_ref | 115 | 115 |
| page_type | text | text |
| language | eng | eng |
| topic | general | general |
| image_path |  |  |
| word_count | 16 | 16 |

Parent text (first 200 chars): `wate wpa fire cart arene   Sat Ste  wa fae    nett fata  nest quit am, We  EVV`  
Child text (first 200 chars): `wate wpa fire cart arene   Sat Ste  wa fae    nett fata  nest quit am, We  EVV`

### `uttkalamrita-kalidas-ps-sastri_p68_c2`  (kept)  vs  `uttkalamrita-kalidas-ps-sastri_p68_c2_c0`  (delete candidate)

| field | parent (kept) | child (delete candidate) |
|---|---|---|
| book_name | uttkalamrita-kalidas-ps-sastri | uttkalamrita-kalidas-ps-sastri |
| page_ref | 68 | 68 |
| page_type | text | text |
| language | eng | eng |
| topic | general | general |
| image_path |  |  |
| word_count | 1 | 1 |

Parent text (first 200 chars): `1879.12.21`  
Child text (first 200 chars): `1879.12.21`

### `Sarvartha-Chintamani_p238_c0`  (kept)  vs  `Sarvartha-Chintamani_p238_c0_c0`  (delete candidate)

| field | parent (kept) | child (delete candidate) |
|---|---|---|
| book_name | Sarvartha-Chintamani | Sarvartha-Chintamani |
| page_ref | 238 | 238 |
| page_type | text | text |
| language | eng | eng |
| topic | general | general |
| image_path |  |  |
| word_count | 72 | 72 |

Parent text (first 200 chars): `bo — ~)  ' -MARKANDEYA  And revealing his humility and other good qualities, he learnt, apparently from his preceptor but really because of his inherent powers, all the several sciences  (Vidyas).  Wh`  
Child text (first 200 chars): `bo — ~)  ' -MARKANDEYA  And revealing his humility and other good qualities, he learnt, apparently from his preceptor but really because of his inherent powers, all the several sciences  (Vidyas).  Wh`

### `Deva-keralam_p146_c1`  (kept)  vs  `Deva-keralam_p146_c1_c0`  (delete candidate)

| field | parent (kept) | child (delete candidate) |
|---|---|---|
| book_name | Deva-keralam | Deva-keralam |
| page_ref | 146 | 146 |
| page_type | text | text |
| language | eng | eng |
| topic | nakshatra | nakshatra |
| image_path |  |  |
| word_count | 103 | 103 |

Parent text (first 200 chars): `473,116310, Sth and Janma Nakshatras transited by malefic planets will cause abundant difficulties, More so, the 8th star counted from birth star.  474 - 475. Only good effects and advent of wealth sh`  
Child text (first 200 chars): `473,116310, Sth and Janma Nakshatras transited by malefic planets will cause abundant difficulties, More so, the 8th star counted from birth star.  474 - 475. Only good effects and advent of wealth sh`

### `Deva-keralam_p37_c4`  (kept)  vs  `Deva-keralam_p37_c4_c0`  (delete candidate)

| field | parent (kept) | child (delete candidate) |
|---|---|---|
| book_name | Deva-keralam | Deva-keralam |
| page_ref | 37 | 37 |
| page_type | text | text |
| language | eng | eng |
| topic | planets | planets |
| image_path |  |  |
| word_count | 10 | 10 |

Parent text (first 200 chars): `Notes: Jupiter is the lord of the 9th for Cancer`  
Child text (first 200 chars): `Notes: Jupiter is the lord of the 9th for Cancer`

### `Prasna Marga 1_p98_c2`  (kept)  vs  `Prasna Marga 1_p98_c2_c0`  (delete candidate)

| field | parent (kept) | child (delete candidate) |
|---|---|---|
| book_name | Prasna Marga 1 | Prasna Marga 1 |
| page_ref | 98 | 98 |
| page_type | text | text |
| language | eng | eng |
| topic | bhava | bhava |
| image_path |  |  |
| word_count | 92 | 92 |

Parent text (first 200 chars): `quarrels with relatives, loss of house, great mental affliction, fear of suicide or death.  ANIMAL SYMBOLS  Stanza 23. — If the middle and unit digits are represented by serpent and Garuda, or mouse a`  
Child text (first 200 chars): `quarrels with relatives, loss of house, great mental affliction, fear of suicide or death.  ANIMAL SYMBOLS  Stanza 23. — If the middle and unit digits are represented by serpent and Garuda, or mouse a`

### `Jataka Parijata with explanation of Pt. Kapileshvara Shastri and Vimala Hindi Tika of Pt. Shri Matri Prasad Shastri Series No. 10 - Kashi Sanskrit Series_p190_c0`  (kept)  vs  `Jataka Parijata with explanation of Pt. Kapileshvara Shastri and Vimala Hindi Tika of Pt. Shri Matri Prasad Shastri Series No. 10 - Kashi Sanskrit Series_p190_c0_c0`  (delete candidate)

| field | parent (kept) | child (delete candidate) |
|---|---|---|
| book_name | Jataka Parijata with explanation of Pt. Kapileshvara Shastri and Vimala Hindi Tika of Pt. Shri Matri Prasad Shastri Series No. 10 - Kashi Sanskrit Series | Jataka Parijata with explanation of Pt. Kapileshvara Shastri and Vimala Hindi Tika of Pt. Shri Matri Prasad Shastri Series No. 10 - Kashi Sanskrit Series |
| page_ref | 190 | 190 |
| page_type | text | text |
| language | eng | eng |
| topic | general | general |
| image_path |  |  |
| word_count | 7 | 7 |

Parent text (first 200 chars): `ee ae) eee  (go te  Dua CSS`  
Child text (first 200 chars): `ee ae) eee  (go te  Dua CSS`

## 4. Expected post-state

- Current total: 11688
- Accepted delete-plan size: 3945
- **Expected post-delete total: 7743**
- Target band: 8650-8950 (centered on the task's ~8,800 estimate) -- OUTSIDE band.

**Reconciliation (not a script defect -- traced to a stale upstream estimate):** the task's ~2,892/~8,800 figures trace to `diagnostics/chunking_code_audit_20260621_092249.md` line 6 ("2,892 duplicate-text groups, 100% of which match a chunk_id X / X_c<N> pair"). That figure does not itself reconcile against its own cited source, `chromadb_dup_report_20260621_080119.md`'s axis (b) histogram (3,930 groups / 7,896 chunks total). Redoing that arithmetic directly: excluding the one 18-member OCR-garbage group (cross-page, not a suffix chain -- see Section 6) leaves 3,929 groups / 7,878 chunks; if each remaining group is one kept parent plus (size-1) deletable children, that predicts 7,878 - 3,929 = **3,949** deletions -- within 4 of this run's exact, schema-verified count of 3945. The small residual is consistent with a handful of groups whose members aren't a clean single-parent chain. This run's count is the ground truth (computed directly against the live collection per the stated invariant); the task's ~2,892/~8,800 figures were an upstream approximation that undercounted sub-chunk-level pairs within affected pages (e.g. one re-chunked page can contribute several independent X/X_c<N> pairs, not just one -- see the Deva-keralam p8 example in `embedder_hardening_proposal_20260621_100850.md`).

## 5. Snapshot sanity check

- Snapshot file: `targeted_delete_snapshot_20260621_120557.jsonl`
- Snapshot size: 127,907,942 bytes (121.98 MB)
- Snapshot record count: 3945
- Delete-plan record count: 3945
- **Sanity check (snapshot count == plan count): PASS**

## 6. Out-of-scope (documented, not touched by this plan)

- **OCR-garbage groups.** `diagnostics/chromadb_dup_report_20260621_080119.md` axis (b) found 3,930 byte-identical-text groups total (7,896 chunks), including a single 18-member group in `Hasta Samudrika Shastra...` whose entire text is the literal character `|`, spanning unrelated page_refs (p92, p264, p274, ...). This invariant excludes that group by construction: stripping `_c0` from e.g. `..._p264_c0` yields `..._p264`, which is never itself a stored chunk_id under the locked schema, so condition 2 fails and the pair is never even evaluated as a candidate. Left untouched, as instructed.
- **Near-identical-embedding pairs outside the suffix invariant.** The same source report's axis (c) sampled 500/11688 chunks and found 5 pairs at cosine > 0.99 (one of which is itself an X/X_c<N> pair already covered above). This script does not re-run or extend that embedding-similarity scan -- any near-identical-but-non-suffix-matching pairs remain out of scope for this pass and are not in the delete plan.

