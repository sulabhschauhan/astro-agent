# Chunk Existence vs Rank Reconciliation — S81

## Part A: Existence (Direct ID Lookup)

| Chunk ID | Status | Char Count |
|---|---|---|
| p165_c2 | EXISTS | 355 |
| p163_c1 | EXISTS | 656 |
| p145_c0 | EXISTS | 789 |
| p160_c3 | EXISTS | 153 |
| p159_c2 | EXISTS | 602 |
| p160_c1 | EXISTS | 747 |

## Part B: Ranking (Top 20 Search Results)

| Chunk ID | Rank |
|---|---|
| p165_c2 | not-in-top-20 |
| p163_c1 | 2 |
| p145_c0 | 3 |
| p160_c3 | not-in-top-20 |
| p159_c2 | 2 |
| p160_c1 | 4 |

## Query Template Check

**Query strings produced by _build_feature_query:**
- fate_line: `what does a 3 fate line signify — meaning and indications of a 3 fate line`
- head_line: `what does a 3 head line signify — meaning and indications of a 3 head line`
- heart_line: `what does a 3 heart line signify — meaning and indications of a 3 heart line`

**Template status:** CHANGED from S68
(S68 expected simple strings like 'fate line', 'head line', 'heart line')

## Reconciliation

**Report b1f7a79 claimed:** "p165_c2 missing from corpus"
**Report 32b5125 claimed:** "chunk p165_c2 present 355 chars, under-ranked"

**MEASUREMENT:** p165_c2 EXISTS (355 chars)
**RANK:** not-in-top-20

**WRONG REPORT:** b1f7a79
**What b1f7a79 actually measured:** It searched for p165_c2 in the top 10
results of the 'fate line' query and reported it as ABSENT from the search
results. It was NOT absent from the corpus; it was absent from the top 10
query results and thus not retrieved. The report conflated 'not in top 10
search results' with 'missing from corpus', which are different things.

## p165_c2 Full Text

```
People without any sign of a line of fate are often very successful, but
taney lead more a vegetable kind of existence. They eat, drink, and sleep, but
I do not think we can really call them happy, for they cannot feel acutely,
end to feel happiness we must also feel the reverse. Sunshine and shadow,
smiles and tears comprise the sum total of our lives.
```

## Reference

**Total live Cheiro chunks:** 463 (expect 463)