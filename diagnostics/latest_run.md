# A1 Ring 1 anchor validators (V-1 tag completeness + V-2 anchor legality)
# -- implementation report, STOP CONDITION HIT, NOT COMMITTED

Design implemented in `agent/interpretive/palm_reading.py` only, per the
locked S68 F-C design. **Full pytest run broke 17 existing tests --
per the instructing prompt's own branch ("if any existing test hard-
codes the reading return shape... and breaks: STOP and report -- do not
edit test files"), this is a STOP condition. No test file was edited.
No commit was made. Working tree left as-is for review.**

## What was implemented
- `_check_tag_completeness()` (V-1): fails on (a) empty/whitespace text
  ("anchor contract not exercised" -- the primary guard), (b) untagged
  residue AFTER the last recognized tag in the text (the one position
  decidable from tag POSITIONS alone, with no NLP/sentence-splitter, per
  the explicit prohibition on building one). Documented KNOWN GAP: an
  untagged sentence sandwiched BETWEEN two valid tags is not caught --
  not solvable without sentence-boundary detection.
- `_check_anchor_legality()` (V-2): every `[<chunk_id>]` cited in the
  text must be a member of `valid_chunk_ids` -- the union of every
  chunk_id across ALL features in `gated_results` (single source of
  truth, no re-retrieval). **DESIGN-CHAT ESCALATION** (per the
  instructing design's own fallback clause): section boundaries are NOT
  deterministically recoverable from the generated reading's text
  format -- the "### {feature}" headings exist only in the INPUT
  passages shown to the model (`_assemble_retrieved_passages`), never in
  its free-flowing "one cohesive... not two separate paragraphs" output
  prose. Per instruction, did NOT improvise a heuristic section
  splitter; implemented UNION-only membership instead. This still kills
  fabricated and stale chunk_ids but cannot catch a real, gated
  chunk_id cited under the wrong feature's sentence -- that per-feature
  requirement needs a design-chat ruling on how (or whether) to recover
  sentence->feature attribution, e.g. requiring the model to also emit
  its own "### {feature}" markers in the output (a prompt change, out of
  this implementation-only prompt's scope).
- Both wired into `_run_ring1_checks()` (now 8 validators, V-1 before
  V-2, appended after the pre-existing 6 -- their order/logic
  untouched). `generate_palm_reading()` computes `valid_chunk_ids` once
  from `gated_results` right after the support gate, threads it into
  both `_run_ring1_checks()` call sites (first draft + F2c retry draft).
  Same failure-list disposition and retry-feedback path as every
  existing validator (S67 banned-mention precedent) -- no new
  disposition logic. Both new checks wrapped in try/except, re-raising
  RuntimeError with context on any unexpected crash (never pass
  silently).

## Synthetic examples (no live LLM calls)

**V-1 violation** (trailing untagged residue):
```
input:  'The deep life line promises long life.[cheiroslanguageo00chei_1_p134_c1] This part has no tag at all.'
output: ["anchor_completeness: sentence-final residue with no tag: 'This part has no tag at all.'"]
```
Clean pass on `'...long life.[cheiroslanguageo00chei_1_p134_c1] Your hands show a robust build.[OBS]'` -> `[]`.
Empty/whitespace text -> `['anchor_completeness: anchor contract not exercised (reading_text_tagged is empty or whitespace-only)']`.

**V-2 violation** (chunk_id not in the gated set):
```
valid_chunk_ids: {'cheiroslanguageo00chei_1_p134_c1', 'cheiroslanguageo00chei_1_p139_c0'}
input:  'The deep life line promises long life.[cheiroslanguageo00chei_1_p999_c9] Your hands show a robust build.[OBS]'
output: ['anchor_legality: unknown/malformed chunk_id(s): cheiroslanguageo00chei_1_p999_c9']
```
Clean pass on the same valid_chunk_ids with a cited id that IS a member -> `[]`.

## Full pytest result
`python -m pytest -q`: **17 failed, 3183 passed, 3 skipped** (vs. the
3200 passed / 3 skipped baseline).

## Root-cause verification (all 17 failures, single shared cause)
Every failure's `ValidationReport.failures` contains an
`anchor_completeness: sentence-final residue with no tag: ...` entry
where the quoted residue is the ENTIRE mocked `_FakeClient(content=...)`
stub text for that test (e.g. `_CLEAN_STUB_TEXT`, `_JARGON_STUB_TEXT`,
`_STABILITY_STUB_TEXT`, etc.) -- confirmed by grepping every failure's
assertion output. **Zero failures involve V-2** (`anchor_legality` never
fires in any of the 17 -- untagged text cites zero chunk_ids, so V-2 has
nothing to object to). Every one of `tests/interpretive/test_palm_
reading.py`'s ~35 `_FakeClient` stub constants is plain untagged prose,
written before the A1 tagging contract existed -- V-1 is correctly
identifying that NONE of them satisfy the new contract.

## Why this is NOT the same situation as the prior A1 prompt's break
The previous A1 implementation prompt also broke tests (a `PalmReadingResult`
dataclass-shape mismatch in `tests/test_app_dogfood_capture.py`) and was
resolved within one-file scope by giving the new field a default value --
a genuine zero-semantic-risk backward-compatibility measure that changed
nothing about any validator's behavior.

This break is different in kind: V-1 is *working exactly as designed* --
its entire purpose is to fail text that doesn't carry the required tags,
and every one of these 17 tests exercises exactly that case (untagged
mock LLM output) by construction, because they predate A1. There is no
one-file, palm_reading.py-only fix that resolves this without either
(a) weakening V-1 to not fire on untagged text -- which would defeat the
validator's stated purpose and constitutes a redesign, explicitly out of
scope for this "implement, do not redesign" prompt -- or (b) updating
the test file's stub fixtures to carry valid tags, which the instructing
prompt explicitly reserves for a later prompt ("tests are the next
prompt... do NOT edit test files").

## Status
Implementation complete and verified correct in isolation (synthetic
examples above). **Not committed, not pushed** -- `agent/interpretive/
palm_reading.py` has uncommitted changes in the working tree, left
as-is pending direction. Two things need a design-chat/user decision
before this can land:
1. How the "next prompt" should update `tests/interpretive/
   test_palm_reading.py`'s stub fixtures for the new tag contract
   (every `_FakeClient(content=...)` stub needs valid trailing tags, or
   a decision to relax V-1's HARD FAIL to a softer disposition for
   legacy-shaped test doubles specifically -- a real design choice, not
   mine to make here).
2. V-2's escalated section-attribution gap (see above) -- union-only
   membership is what's implemented; whether/how to recover per-feature
   attribution is open.

---

# S68 F-C A1: test-suite alignment + V-1/V-2 coverage -- close-out

Follow-up to the STOP-condition report above. Scope: `tests/interpretive/
test_palm_reading.py` ONLY -- no production code touched (confirmed via
`git diff` before commit: only the test file changed).
Ruling applied: validators are correct as-is; tests conform to the
contract, never vice versa.

## Part 1 -- retagged legacy stubs
All ~19 `_FakeClient` stub constants/inline literals predating A1
(`_CLEAN_STUB_TEXT`, `_JARGON_STUB_TEXT`, `_YEAR_STUB_TEXT`,
`_GENERIC_NO_FEATURE_STUB_TEXT`, `_RETRY_FIRST_DRAFT_STUB_TEXT`,
`_RETRY_SECOND_DRAFT_STILL_FAILS_STUB_TEXT`, `_STABILITY_STUB_TEXT`,
`_WORD_BOUNDARY_STUB_TEXT`, `_NAVIGATED_STUB_TEXT`,
`_MULTI_TERM_STUB_TEXT`, `_CHEIRO_VOICE_STUB_TEXT`,
`_EMPOWERMENT_STUB_TEXT`, `_FATE_MENTIONING_DRAFT`/
`_FATE_CLEAN_RETRY_DRAFT`, `_COLLISION_SAFE_DRAFT`,
`_COLLISION_TRIPPED_DRAFT`, `_EXEMPLAR_ECHO_FIRST_DRAFT`/
`_EXEMPLAR_ECHO_CLEAN_RETRY`, plus the inline `five_word_draft`/
`six_word_draft`/`weird_draft`/`draft_quoting_chunk` literals) got a
trailing `" [OBS]"` appended as their final-sentence tag -- sufficient
per V-1's documented sandwich-gap boundary (only whole-text-untagged and
trailing-residue-after-last-tag are position-decidable; mid-text
sentences stay untagged, unchanged from the stub's original prose).
**One deliberate exception**: `long_text` (the 701-word length-rail
stub in `test_length_over_700_words_fails`) was left untagged --
appending a token would make it 702 words and break the test's own
`"701" in f` assertion; that test wasn't failing anyway (it only checks
`any(f.startswith("length_guard:")...)`, indifferent to the coexisting
anchor_completeness failure).
No assertion was weakened, skipped, or xfailed. No stub required
STRIPPED-form updates to an exact-`reading_text` comparison -- verified
by grep: every existing assertion touching `reading_text` checks a
substring (DISCLAIMER, decline-block text, "fate") never the raw stub
text verbatim, so `strip_generation_tags()` removing the appended tag
changes nothing any assertion depends on.
Result: all 17 previously-failing tests pass; 0 regressions in the
other 23.

## Part 2 -- new V-1/V-2 coverage (13 new tests, synthetic text, no
live LLM/ChromaDB)
1. `test_tag_completeness_empty_string_reports_anchor_contract_not_exercised`
2. `test_tag_completeness_whitespace_only_reports_anchor_contract_not_exercised`
3. `test_tag_completeness_wholly_untagged_prose_reports_residue`
4. `test_tag_completeness_trailing_residue_after_last_tag_quoted_in_message`
5. `test_tag_completeness_clean_pass_mixed_obs_and_anchor_tags`
6. `test_tag_completeness_multi_anchor_sentence_pass`
7. `test_anchor_legality_fabricated_chunk_id_hard_fail_listed_verbatim`
8. `test_anchor_legality_stale_id_valid_shape_not_in_gated_set_fails`
9. `test_anchor_legality_cited_id_present_in_gated_set_passes`
10. `test_anchor_legality_obs_only_text_passes_nothing_cited`
11. `test_anchor_legality_empty_valid_chunk_ids_any_citation_fails`
12. `test_v1_before_v2_untagged_text_reports_completeness_without_legality_failure`
13. `test_end_to_end_tagged_draft_with_cited_chunk_validates_clean_and_strips_tags`

Items 1-11 call `palm_reading._check_tag_completeness()` /
`palm_reading._check_anchor_legality()` directly (same convention as the
pre-existing `_JARGON_PATTERN` direct-proof test) -- deterministic,
no-LLM-judgment functions, so a direct call is the more exact proof than
routing through the full `generate_palm_reading()` stack. Item 12 also
exercises `_run_ring1_checks()` end-to-end on an untagged, otherwise-
clean sentence to prove V-1 fires alone while V-2 contributes nothing.
Item 13 is the one full `generate_palm_reading()` integration test in
this batch: a tagged stub (`[OBS]` + a cited chunk_id present in the
stubbed retrieval's gated results) validates clean, and
`CHUNK_ANCHOR_TAG_PATTERN.search(result.reading_text) is None` proves no
tag token survives display (regex-negative, not hand-derived).
An informational comment block precedes item 1, documenting the
accepted sandwich-gap boundary as "place 2 of 3" in a 3-place taxonomy
(before-first-tag / between-tags / after-last-tag) -- formalizing that
taxonomy in CLAUDE.md and the module's own docstring is deferred to the
S68 F-C close-out prompt, not resolved here.

## Full pytest result
`python -m pytest -q`: **3213 passed, 3 skipped** (vs. the 3200
passed / 3 skipped baseline) -- +13, exactly the new Part 2 tests, 0
regressions.
`tests/interpretive/test_palm_reading.py` alone: 53 passed (was 23
passed / 17 failed before this close-out; +13 net new vs. the pre-A1
40-test file).
