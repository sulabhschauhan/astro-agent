# ChromaDB Duplication Diagnostic -- astro_chunks

**Generated:** 2026-06-21 08:01:19 UTC  
**Collection:** `astro_chunks` @ `data/chroma_db`  
**Total chunks in collection:** 11688  
**Read-only run** -- no writes, deletes, or re-embeds performed by this script.

> Note: collection count (11688) is well above the ~7,281 chunks documented in CLAUDE.md's RAG corpus description. That gap is itself consistent with systematic duplicate ingestion and is worth carrying into fix-design discussion, not just the per-axis group counts below.

## Axis (a): Exact chunk_id collisions

- Total id entries returned: 11688
- Unique ids: 11688
- Colliding id groups: 0

No id stored more than once. Consistent with Chroma enforcing id uniqueness as primary key, and `embedder.py` using `.upsert()` (overwrites on existing id rather than duplicating).

## Axis (b): Byte-identical text across distinct chunk_ids

- Duplicate-text groups: 3930
- Chunks involved: 7896 (67.6% of collection)
- Group-size histogram: 3920 group(s) of size 2, 3 group(s) of size 3, 3 group(s) of size 4, 1 group(s) of size 5, 2 group(s) of size 6, 1 group(s) of size 18
- Source book distribution (duplicate-involved chunks):
  - Deva-keralam: 1344
  - Muhurtha-Chinthamani: 1208
  - Prasna Marga 1: 1034
  - Jataka Parijata with explanation of Pt. Kapileshvara Shastri and Vimala Hindi Tika of Pt. Shri Matri Prasad Shastri Series No. 10 - Kashi Sanskrit Series: 1008
  - Prasna Marga 2: 862
  - Sarvartha-Chintamani: 846
  - Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan: 844
  - uttkalamrita-kalidas-ps-sastri: 744

Representative example (largest group):

- chunk_ids: Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan_p92_c0, Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan_p264_c0, Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan_p274_c0, Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan_p294_c0, Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan_p347_c0, Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan_p373_c0, ... (+12 more)
- book_name: Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan
- page_ref: 92
- text (first 200 chars):
```
|
```

## Axis (c): Near-identical embeddings, sampled (n=500/11688, cosine > 0.99)

- Sample size: 500 (seed=22)
- Pairs above threshold: 5
- Duplicate-embedding groups (connected components): 5
- Sampled chunks involved: 10
- Group-size histogram: 5 group(s) of size 2
- Source book distribution (duplicate-involved sampled chunks):
  - Jataka Parijata with explanation of Pt. Kapileshvara Shastri and Vimala Hindi Tika of Pt. Shri Matri Prasad Shastri Series No. 10 - Kashi Sanskrit Series: 4
  - Muhurtha-Chinthamani: 2
  - Prasna Marga 1: 2
  - Prasna Marga 2: 2

Representative example (largest group):

- chunk_ids: Jataka Parijata with explanation of Pt. Kapileshvara Shastri and Vimala Hindi Tika of Pt. Shri Matri Prasad Shastri Series No. 10 - Kashi Sanskrit Series_p73_c0, Jataka Parijata with explanation of Pt. Kapileshvara Shastri and Vimala Hindi Tika of Pt. Shri Matri Prasad Shastri Series No. 10 - Kashi Sanskrit Series_p73_c0_c0
- book_name: Jataka Parijata with explanation of Pt. Kapileshvara Shastri and Vimala Hindi Tika of Pt. Shri Matri Prasad Shastri Series No. 10 - Kashi Sanskrit Series
- page_ref: 73
- text (first 200 chars):
```
SS NS  ......“.“ |  Wal: | = | =  | wea | oe, ofr eae   ————— fee a | THAT | 72: ae me | :,  me | a, ge: jute, ,  Ta:, WHat:  1 4 : a ‘oe  RET i  | +++--+---+--  r >. i We, Wx:  el. | .  |
```

## Scope notes

- Axis (c) is a 500-of-11688 random sample (seed=22), not full pairwise -- do not extrapolate its group counts linearly to the full corpus.
- Axes are independent and may overlap (e.g. a byte-identical-text pair is expected to also show near-identical embeddings if both members happen to land in the axis (c) sample).
- No fix is proposed in this report. Findings are reported as observed for Session 23 fix-design (chunk_id collision logic vs. embedder re-run vs. source page double-ingest).
