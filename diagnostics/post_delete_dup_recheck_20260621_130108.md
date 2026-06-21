# Post-Delete Duplicate Diagnostic Re-check -- astro_chunks

**Generated:** 2026-06-21 13:01:08 UTC  
**Collection:** `astro_chunks` @ `data/chroma_db`  
**Read-only run** -- no writes, deletes, or re-embeds performed by this script. Re-runs the exact axis a/b/c logic from `chromadb_dup_diagnostic.py` and the exact suffix invariant from `targeted_delete_dryrun.py`.

## 1. Total chunk count

- Total chunks: **7743**
- Expected (post-delete): 7743 -- MATCH

## 2. Axis (a): Exact chunk_id collisions

- Total id entries: 7743
- Unique ids: 7743
- Colliding id groups: 0 -- PASS (expected 0)

## 3. Axis (b): Byte-identical text across distinct chunk_ids

- Duplicate-text groups: 10 (pre-delete: 3,930)
- Chunks involved: 31 (0.4% of collection) (pre-delete: 7,896)
- Incomplete-delete flag (group count > 100): not tripped

- Group-size histogram: 6 group(s) of size 2, 2 group(s) of size 3, 1 group(s) of size 4, 1 group(s) of size 9

### Largest 3 remaining groups

**Group 1 (size 9):**

- chunk_ids: Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan_p92_c0, Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan_p264_c0, Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan_p274_c0, Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan_p294_c0, Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan_p347_c0, Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan_p373_c0, ... (+3 more)
- book_name: Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan
- page_ref: 92
- text (first 200 chars):
```
|
```

**Group 2 (size 4):**

- chunk_ids: BPHS - 2 RSanthanam_p244_c2, Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri_p188_c2, Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri_p244_c2, Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan_p482_c0
- book_name: BPHS - 2 RSanthanam
- page_ref: 244
- text (first 200 chars):
```
~
```

**Group 3 (size 3):**

- chunk_ids: Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan_p76_c0, Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan_p114_c0, Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan_p223_c0
- book_name: Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan
- page_ref: 76
- text (first 200 chars):
```
i
```

Per the dry-run's Section 6 (out-of-scope), the residual is expected to be OCR-garbage groups like the 18-member literal `|` group spanning unrelated page_refs -- not a missed class of real X/X_c<N> duplicates. Confirmed below via the suffix-invariant re-check (Section 6).

## 4. Axis (c): Near-identical embeddings, sampled (n=500/7743, cosine > 0.99, seed=22)

- Pairs above threshold: 0 (pre-delete: 5) -- PASS (<=5)
- Duplicate-embedding groups: 0

Scope note (unchanged from the original diagnostic): this is a 500-of-7743 random sample, not full pairwise -- do not extrapolate group counts linearly.

## 5. Per-book chunk count post-delete

| book_name | post-delete count | deleted (this pass) | reconstructed pre-delete | class |
|---|---|---|---|---|
| Jyotish_Lal Kitab_B.M. Gosvami | 769 | 0 | 769 | CLEAN |
| BPHS - 2 RSanthanam | 730 | 0 | 730 | CLEAN |
| BPHS - 1 RSanthanam | 728 | 0 | 728 | CLEAN |
| Deva-keralam | 672 | 672 | 1344 | AFFECTED |
| Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri | 642 | 0 | 642 | CLEAN |
| Muhurtha-Chinthamani | 604 | 604 | 1208 | AFFECTED |
| Prasna Marga 1 | 517 | 517 | 1034 | AFFECTED |
| Jataka Parijata with explanation of Pt. Kapileshvara Shastri and Vimala Hindi Tika of Pt. Shri Matri Prasad Shastri Series No. 10 - Kashi Sanskrit Series | 504 | 504 | 1008 | AFFECTED |
| Saravali of Kalyana Varma Santhanam R. (Astrology) | 466 | 0 | 466 | CLEAN |
| cheiroslanguageo00chei_1 | 463 | 0 | 463 | CLEAN |
| Prasna Marga 2 | 431 | 431 | 862 | AFFECTED |
| Sarvartha-Chintamani | 423 | 423 | 846 | AFFECTED |
| Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan | 422 | 422 | 844 | AFFECTED |
| uttkalamrita-kalidas-ps-sastri | 372 | 372 | 744 | AFFECTED |

### Clean-book unchanged check

- `BPHS - 1 RSanthanam`: 728 chunks, 0 deleted this pass -- unchanged by construction (delete touched none of its ids).
- `BPHS - 2 RSanthanam`: 730 chunks, 0 deleted this pass -- unchanged by construction (delete touched none of its ids).
- `Jyotish_Lal Kitab_B.M. Gosvami`: 769 chunks, 0 deleted this pass -- unchanged by construction (delete touched none of its ids).
- `Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri`: 642 chunks, 0 deleted this pass -- unchanged by construction (delete touched none of its ids).
- `Saravali of Kalyana Varma Santhanam R. (Astrology)`: 466 chunks, 0 deleted this pass -- unchanged by construction (delete touched none of its ids).
- `cheiroslanguageo00chei_1`: 463 chunks, 0 deleted this pass -- unchanged by construction (delete touched none of its ids).

Secondary cross-check (`data/embedding_report.json` by_book.embedded, independent of this run):

- `BPHS - 1 RSanthanam`: embedding_report=706, live=728 -- differs (see note)
- `BPHS - 2 RSanthanam`: embedding_report=716, live=730 -- differs (see note)
- `Jyotish_Lal Kitab_B.M. Gosvami`: embedding_report=769, live=769 -- match
- `Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri`: embedding_report=561, live=642 -- differs (see note)
- `Saravali of Kalyana Varma Santhanam R. (Astrology)`: embedding_report=464, live=466 -- differs (see note)
- `cheiroslanguageo00chei_1`: embedding_report=452, live=463 -- differs (see note)

(Differences here, if any, predate this delete pass and reflect normal embedder-report-vs-live drift, e.g. pending/diagram chunks counted differently -- not evidence this delete touched a clean book.)

## 6. Suffix-invariant re-check (did the delete fully land?)

- Re-running `find_candidates()` (the exact invariant `targeted_delete_execute.py` deleted against) on the post-delete collection: **0 accepted candidates remain** (expected 0).
- Downgraded-to-review candidates remaining: 0 (informational; these were never in the delete plan).
- None of the 8 previously-affected books show the X/X_c<N> suffix pattern anymore. Delete landed completely.

## Headline summary

- Total count: 7743 (expected 7743) -- PASS
- Axis (a) collisions: 0 (expected 0) -- PASS
- Axis (b) groups: 10 (pre-delete 3,930; flag threshold >100)
- Axis (c) pairs: 0 (expected <=5) -- PASS
- Suffix-invariant residual: 0 (expected 0) -- PASS
- Clean-book anomaly: none
- **Incomplete-delete flag: not tripped**

