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
