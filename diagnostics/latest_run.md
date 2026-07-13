# S67 R1: per-feature doctrine-interrogative retrieval in palm_reading

Implementation report for the R1 per-feature retrieval redesign
(`agent/interpretive/palm_reading.py`) + matching Ring 2 update
(`tests/interpretive/test_palm_reading.py`). Design ratified in design
chat from `diagnostics/latest_run.md` as committed by
`scripts/probe_r1_retrieval.py` (commit `0a738c3`) — this report
overwrites that probe report per the standing diagnostic-output
convention (probe evidence stays available via git history at that
commit).

## Files touched

- `agent/interpretive/palm_reading.py` — production redesign.
- `tests/interpretive/test_palm_reading.py` — matching Ring 2 update
  (same commit, per the F2+F3 precedent for atomic module+suite
  landings).

Nothing else touched (scope discipline per the prompt).

## Consumer-compatibility check (before coding, not after)

`PalmReadingResult.sources` gains a new `"feature"` key per source
dict. Grepped every consumer:
- `frontend/app.py` lines 75/839 — both access `src['book']`/
  `src['page']`/`src['score']` by name only, never iterate/assert the
  full key set. Additive-safe, no change needed, no STOP triggered.
- `tests/test_app_dogfood_capture.py` — no reference to `.sources` at
  all.
- `tests/test_palm_endtoend.py` — exercises `prompt_builder.build_prompts`
  (the quarantined `ask()` path), never calls `generate_palm_reading`.

No consumer contradicted the instructions; nothing to STOP and report.

## Design-decision → code mapping

| Design decision | Code |
|---|---|
| Canonical feature registry (10 features) | `palm_reading._FEATURE_REGISTRY` |
| Feature extraction over palm_left/palm_right (F4 flat fields) | `palm_reading._parse_fields` (ported from `scripts/probe_r1_retrieval.py`, blank-line-reset added) |
| Feature extraction over hand_detail (LOCK LIFTED, S67 Conflict A (b)) | `palm_reading._parse_bullet_fields` (new — hand_detail's markdown bullet format, not in the probe) |
| Plain-feature field map + MOUNTS/OTHER LINES sub-feature needles | `_PLAIN_FEATURE_FIELDS`, `_SUB_FEATURES`, `_gather_feature_texts` |
| Absence rule (6 phrases, all-mentioning-sources gate) | `_ABSENCE_PHRASES`, `_is_absence`, `_resolve_feature_quality` |
| Fail-open (degenerate quality -> raw text + warning) | `_resolve_feature_quality`'s `if not q or q == "present":` branch |
| Quality merge (" / ", per-hand) | `_resolve_feature_quality`'s dedupe-preserving-order join |
| Variant-iii query template | `_build_feature_query` |
| n=3/feature retrieval, try/except per feature | `_retrieve_per_feature` |
| Ordered per-feature map + display dedupe | `_assemble_retrieved_passages` |
| Sources gain `feature` tag | `generate_palm_reading`'s `sources = tuple(...)` construction |
| All-queries-fail -> low-confidence path preserved | `total_chunks == 0` gate (was `not raw_sources`) |
| Ring 1 / F2c retry / DISCLAIMER / system prompt | UNCHANGED |
| `generate_palm_reading` signature | UNCHANGED |

### Bug caught and fixed during implementation (not in the original design)

`_is_absence` is a whole-string substring check. LEFT/RIGHT's MOUNTS
field reads "Mount of Venus appears developed, **other mounts are
unremarkable**." — the word "unremarkable" (an absence phrase) is about
the OTHER mounts, not Venus, but a naive whole-text check flagged the
entire field absent and silently dropped "developed" for `mount of
venus`. Fixed with `_extract_needle_clause`: for MOUNTS/OTHER LINES
sub-features, only the comma-separated clause(s) actually naming the
needle ("venus"/"jupiter"/"sun") are used for the absence check and
quality extraction. Verified via a dry run against the real pass-2
fixture before writing tests (see rider below) — `mount of venus`
correctly resolves to `developed / ...` after the fix, not just the
hand_detail sentence.

## Test delta (derivation comments quoted verbatim from the file)

Kept all 21 original tests (scenarios unchanged: fail-closed ValueError
battery, jargon, year, length, empty retrieval, happy path, client
failure, F2c retry a/b/c, book filter, sources propagation, 6 self-help
register tests). Every synthetic `palm_left`/`palm_right` fixture that
was free prose (e.g. `"A long life line with a gentle curve."`) is now
F4-structured field text (e.g. `"LIFE LINE: A long life line with a
gentle curve."`) since that is what feature-extraction actually parses
— free prose observes zero features and would call `search()` zero
times, which is not what those tests are testing.

No "truncation" test existed to delete — grepped both
`tests/interpretive/test_palm_reading.py` and
`tests/test_palm_endtoend.py` for `truncat` (case-insensitive) before
touching anything; zero matches. The old `_QUERY_TRUNCATE_CHARS`
constant it would have covered is deleted from production with no
orphaned test.

The "exactly-one-call invariant" (item 9,
`test_exactly_one_llm_call_when_first_draft_passes`) is about the LLM
call count (F2c retry mechanism), which R1 does not touch — NOT the old
implicit "exactly one `search()` call" assumption baked into items 6,
10, and 11's fixtures, which R1 makes false by design. Rather than
delete item 9, its fixture was changed to deliberately observe 2
features (life line + heart line) to prove the LLM-call invariant holds
even when 2 `search()` calls now happen:

```python
# 2 observed features (life line from palm_left, heart line from
# palm_right) -> 2 search calls; this test asserts the SEPARATE LLM
# call count only (unaffected by how many search() calls occurred).
fake_search = _FakeSearch([_chunk()])
...
assert len(fake_search.calls) == 2
assert len(client.completions.calls) == 1
```

Derivation comments on every updated expected-call-count assertion:

```python
# test_empty_retrieval_proceeds_with_low_confidence_caveat
# search WAS called (not refused) and returned an empty list.
# 1 observed feature (life line) -> 1 search call.
assert len(fake_search.calls) == 1
```
```python
# test_search_filters_to_canonical_cheiro_book
# 1 observed feature (life line) -> 1 search call.
assert len(fake_search.calls) == 1
assert fake_search.calls[0]["book_name"] == palm_reading._CHEIRO_BOOK
# S67 R1 threshold: n_results is now per-feature (3), not the old
# whole-description 6.
assert fake_search.calls[0]["n_results"] == palm_reading._N_RESULTS_PER_FEATURE == 3
```
```python
# test_sources_propagate_book_page_score
# 1 observed feature (life line) -> 1 search call, returning 2 chunks.
```

New tests (6), hardest first, `_FakeSearch` extended with an optional
`raise_for` predicate for (c):

- **(13a)** `test_absence_rule_all_features_absent_yields_zero_search_calls_and_low_confidence`
  — all 10 registry features resolve to "no query" (7 plain fields
  absence-phrased, sun/venus/jupiter never named) -> 0 search calls,
  low-confidence path fires.
- **(13b)** `test_fail_open_degenerate_quality_still_queries_and_logs` —
  `"LIFE LINE: Present."` degenerates to quality `"present"` -> fail
  open, queries with raw text, logs a warning containing "fail-open".
- **(13c)** `test_one_feature_search_failure_does_not_kill_reading_other_feature_succeeds`
  — life-line query raises, heart-line query succeeds -> reading
  proceeds, sources contain only the heart-line chunk, failure logged.
- **(13d)** `test_query_template_two_hand_merged_quality_literal_shape` —
  exact query string assertion for the real pass-2 fate-line pair
  (`"barely visible"` / `"moderately deep"`), plus `n_results == 3`.
- **(13e)** `test_per_feature_map_ordering_and_dedupe_for_display` — same
  chunk_id returned for 2 features -> shown once in the assembled
  prompt (registry order, first-feature-wins), but `sources` carries
  both assignments.
- **(13f)** `test_sources_carry_distinct_feature_tags` — 2 features, 2
  distinct chunks -> each source dict tagged with the feature that
  actually produced it.

## Suite count

`tests/interpretive/test_palm_reading.py` alone: **27 passed** (21
original + 6 new), 0 failures on first run.

Full suite: **3183 passed, 3 skipped** (was 3177/3 before this task —
net +6, all in this file). Zero regressions elsewhere.

## Rider tables (throwaway script, not committed — production functions exercised directly)

### Part A — mount of jupiter / markings+hair, real HAND_DETAIL qualities, n=3

**mount of jupiter**
Quality: `the mounts of venus (base of the thumb) and jupiter (below the index finger) appear slightly raised`

| rank | page_ref | score | chunk_id | first 120 chars |
|---|---|---|---|---|
| 1 | 112 | 0.6630 | cheiroslanguageo00chei_1_p112_c0 | 64 Cheiro's Language of the Hand. Venus be well developed, it indicates strong and robust health. A small Mount of Venus |
| 2 | 111 | 0.6456 | cheiroslanguageo00chei_1_p111_c1 | THE MOUNT OF VENUS. The Mount of Venus is the develoyeout found at the base of the thu ~b (Plate XII.). Wher not abnorin |
| 3 | 113 | 0.5893 | cheiroslanguageo00chei_1_p113_c0 | Lhe Mounts, their Position and their Meanings. 69 THE MOUNT OF MARS. There are two mounts of this name; the first beneat |

**markings/other features**
Quality: `there are no unusual markings or features visible / there is a moderate amount of hair on the back of the hand and fingers`

| rank | page_ref | score | chunk_id | first 120 chars |
|---|---|---|---|---|
| 1 | 221 | 0.4729 | cheiroslanguageo00chei_1_p221_c1 | It is the hand of the subtlest nature in regard to crime. There will be nothing abnormal in connection with the hand its |
| 2 | 107 | 0.4371 | cheiroslanguageo00chei_1_p107_c0 | CHAPTER XIV. THE HAIR ON THE HANDS, A Suggestive Theory. Ir the exponent of palmistry has to read hands through a curtai |
| 3 | 172 | 0.4345 | cheiroslanguageo00chei_1_p172_c1 | When formed in httle straight pieces, bad digestion (i-7, Plate XIX.). In little islands, with long, filbert nails, dang |

Notable: rank-2 for `markings/other features` (p.107, "THE HAIR ON THE
HANDS") is genuinely on-topic — the "hair" clause of hand_detail's
"Other Features" bullet is doing real retrieval work here, not just
decorative junk. Same pattern for `mount of jupiter`'s rank-1/2 hits
(p.111/p.112, the actual Mount of Venus chapter) — a real, if imperfect
(mount of jupiter's own quality string is actually the Venus+Jupiter
sentence undivided, see the Verified-open item below), doctrine hit.

### Part B — full pipeline over the pass-2 LEFT+RIGHT+HAND_DETAIL fixture

**Observed features (10 of 10 — every registry feature had at least one non-absent source):**
life line, head line, heart line, fate line, sun line, thumb, fingers,
mount of venus, mount of jupiter, markings/other features.

**Every query string:**

| Feature | Query |
|---|---|
| life line | `what does a deep / a prominent line curves around the base of the thumb life line signify — meaning and indications of a deep / a prominent line curves around the base of the thumb life line` |
| head line | `what does a deep / to be separate from the life line head line signify — meaning and indications of a deep / to be separate from the life line head line` |
| heart line | `what does a deep / curves across the top of the palm heart line signify — meaning and indications of a deep / curves across the top of the palm heart line` |
| fate line | `what does a barely visible / moderately deep fate line signify — meaning and indications of a barely visible / moderately deep fate line` |
| sun line | `what does a faintly visible sun line signify — meaning and indications of a faintly visible sun line` |
| thumb | `what does a medium relative size / medium size / the thumb is of average length with a moderate angle of separation from the hand thumb signify — meaning and indications of a medium relative size / medium size / the thumb is of average length with a moderate angle of separation from the hand thumb` |
| fingers | `what does a long relative to the palm / slightly longer than the palm / the fingers are of moderate length. the index finger is slightly shorter than the middle finger fingers signify — meaning and indications of a long relative to the palm / slightly longer than the palm / the fingers are of moderate length. the index finger is slightly shorter than the middle finger fingers` |
| mount of venus | `what does a developed / the mounts of venus (base of the thumb) and jupiter (below the index finger) appear slightly raised mount of venus signify — meaning and indications of a developed / the mounts of venus (base of the thumb) and jupiter (below the index finger) appear slightly raised mount of venus` |
| mount of jupiter | `what does a the mounts of venus (base of the thumb) and jupiter (below the index finger) appear slightly raised mount of jupiter signify — meaning and indications of a the mounts of venus (base of the thumb) and jupiter (below the index finger) appear slightly raised mount of jupiter` |
| markings/other features | `what does a there are no unusual markings or features visible / there is a moderate amount of hair on the back of the hand and fingers markings signify — meaning and indications of a there are no unusual markings or features visible / there is a moderate amount of hair on the back of the hand and fingers markings` |

**Totals:** 10 queries fired, 0 failed. 30 total chunk assignments (3 x 10),
**28 unique chunk_ids** (2 cross-feature repeats). Assembled context
(the `### {feature}` grouped, display-deduped passages block that goes
into the user message): **23,655 chars**.

**Verified-open item (not fixed here, out of scope — R1 only)**: `thumb`,
`fingers`, `mount of jupiter`, and `markings/other features`'s merged
qualities are long/awkward run-on sentences (visible in the table
above) because their source text has no comma to split on (HAND_DETAIL's
prose-style bullets) or the needle-clause split still leaves a long
single clause (MOUNTS' Venus+Jupiter sentence is one clause, so `mount
of venus` and `mount of jupiter` currently get an IDENTICAL long
fallback quality from hand_detail — only the LEFT/RIGHT-sourced
`developed` half is genuinely Venus-specific). This is a real, known
quality-of-query limitation, not a defect against this prompt's
ratified design (which specifies the extraction/merge rule verbatim,
not a requirement to further split same-clause multi-entity sentences)
— flagged here as a candidate refinement for R2/R3 or a future R1.x,
not fixed in this commit.
