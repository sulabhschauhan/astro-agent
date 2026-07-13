# S67 R2: exemplar rewrite + deterministic exemplar-echo validator

Implementation report for R2, closing the S67 R1→R3→R2 sequence before
Ring 3 pass 3. Two files, one commit (R1/R3 precedent).

## Files touched

- `agent/interpretive/palm_reading.py` — exemplar rewrite, new Ring 1
  validator, OCR-rationale rider comment (documentation only).
- `tests/interpretive/test_palm_reading.py` — matching Ring 2 tests.

Nothing else touched. R1 retrieval, R3 gate/ban/decline,
`generate_palm_reading`'s signature, and DISCLAIMER handling are
unchanged.

## Old vs. new exemplar block (verbatim)

**OLD** (F2c, `165484c` lineage — the doctrine-inversion vector):
```
## Voice
Write in Cheiro's declarative register: direct assertions of what the hand indicates, tied to concrete consequences -- health, success won by personal merit, travel, character, fortune. This is a palmist reading a hand, not a therapist offering affirmation.
Write in Cheiro's declarative register. Model sentences: "A deep, unbroken line of life promises long life, good health, and vitality." / "Such a fate line denotes success won by personal merit." Assert what the hand shows and what the tradition says it denotes -- concrete consequences, never affirmations about the reader's inner journey.
FORBIDDEN words and phrasings (never use these, in any form): stability, fulfillment, fulfilling, favorable, journey, navigate, navigating, empower, empowerment, and any "this suggests you are the kind of person who..." self-help framing.
```

**NEW** (S67 R2):
```
## Voice
Write in Cheiro's declarative register: direct, confident assertions in period-appropriate diction, addressed straight to the reader. This is a palmist reading a hand, not a therapist offering affirmation -- speak with the authority of someone who has read thousands of hands and states plainly what each one shows.
Model sentences (voice and cadence ONLY -- do not reuse or adapt ANY part of their wording, not even a short fragment; they contain no interpretive content of their own): "I have examined many hands in my years of practice, and each one tells its own story to those who know how to read it." / "The hand rarely lies to the palmist who reads it honestly." Every interpretive claim in your actual reading must come from the provided passages and the confirmed hand description(s) below -- these two sentences exist only to model tone, never as a source of content.
FORBIDDEN words and phrasings (never use these, in any form): stability, fulfillment, fulfilling, favorable, journey, navigate, navigating, empower, empowerment, and any "this suggests you are the kind of person who..." self-help framing.
```

Note: the OLD block's opening sentence ("...tied to concrete
consequences -- health, **success won by personal merit**, travel...")
carried the SAME risky phrase as the quoted model sentence below it,
outside of quotes — both instances are gone in the rewrite, not just
the quoted one, since either could have served as a leak source.

## Consumer/citation checks (verified, not assumed)

- **"hfe" OCR garble**: confirmed present verbatim in
  `diagnostics/ring3_chunks_S66.md` line 34 ("The line of fate may rise
  from the line of hfe, the wrist...") — cited accurately in the new
  rider comment.
- **"palimistry" OCR garble**: the task prompt asked for this as a
  second cited example. Grepped `diagnostics/` for "palimistry"
  (case-insensitive) — **zero matches**, only correctly-spelled
  "Palmistry" appears anywhere in the diagnostics corpus. This citation
  could not be verified, so it was NOT included in the rider comment —
  only the confirmed "hfe" example is cited. Flagging this rather than
  fabricating a supporting citation.

## Design-to-code mapping

| Design decision | Code |
|---|---|
| Exemplar rewrite (zero transplantable doctrine) | `_READING_SYSTEM_PROMPT`'s `## Voice` block |
| Exemplar sentences as an independent, explicit constant | `_EXEMPLAR_SENTENCES` (deliberately not parsed out of the prompt string — an editing-drift guard, same spirit as the SENSITIVE_TO convention) |
| 6-gram window, justified by the exact pass-2 leaked span length | `_EXEMPLAR_ECHO_NGRAM = 6` |
| Normalization (lowercase, strip punctuation, collapse whitespace) | `_normalize_for_echo_check` |
| Precomputed exemplar n-gram set (O(1) lookup) | `_EXEMPLAR_NGRAMS` |
| Positional (leftmost-first) n-gram scan of reading_text | `_ngrams` returns a list (not a set) — see bug note below |
| The validator itself | `_check_exemplar_echo`, folded into `_run_ring1_checks` (now "six" validators) |
| OCR-rationale asymmetry comment (chunk-side substring vs. LLM-output-side word-boundary) | `_chunk_supports_feature`'s docstring — comment only, zero logic change |

### Bug caught and fixed during implementation (not in the original design)

First draft of `_ngrams()` returned a `set`. `_check_exemplar_echo`
iterated that set looking for the first exemplar match — but set
iteration order isn't the text's left-to-right order, so the reported
`exemplar_echo: {n-gram}` string could be an ARBITRARY overlapping
window, not necessarily the first one a human reading the draft top-to-
bottom would notice. Caught by test 15a's own assertion (expected
`"each one tells its own story"`, got `"its own story to those who"` —
both genuinely overlap the exemplar, since "each one tells its own
story to those who..." has multiple valid overlapping windows).
Fixed: `_ngrams()` now returns a `list` (positional order preserved);
the precomputed exemplar side (`_EXEMPLAR_NGRAMS`) stays a `frozenset`
for O(1) membership testing, but the reading-text side is scanned
in-order and returns on the first (leftmost) match.

## Test delta

Verified BEFORE writing any new tests: all 36 pre-existing tests
(items 1–14, spanning R1/R3) pass unchanged against the rewritten
exemplars — confirms item (e) ("existing stub texts... must be
reworded") required no action this pass; nothing in the existing stub
corpus happened to echo either new exemplar sentence.

4 new tests, hardest first:

- **(15a)** `test_exemplar_echo_guard_fires_first_draft_retried_clean` —
  first draft reuses the verbatim 6-word span "each one tells its own
  story"; validator fires, retry feedback names the exact n-gram; clean
  retry passes. Derivation: *"1 observed feature (life line) -> 1
  search call; 2 LLM calls (first draft trips exemplar_echo, retry is
  clean)."*
- **(15b)** `test_exemplar_echo_boundary_5word_no_fire_6word_fires` —
  measure-first boundary pair: a 5-word overlap ("each one tells its
  own", embedded so neither adjacent real 6-gram in the exemplar
  matches) does not fire; extending by one word to complete the
  genuine 6-gram does.
- **(15c)** `test_exemplar_echo_normalization_case_punctuation_whitespace`
  — same 6-gram in mixed case, with commas/semicolons/exclamation
  marks and irregular whitespace runs, still fires.
- **(15d)** `test_exemplar_echo_does_not_fire_on_retrieved_chunk_quote`
  — a draft sharing a 6-word span with a RETRIEVED CHUNK (real
  life-line doctrine text, not an exemplar) does NOT fire — the guard's
  scope is the 2 exemplar sentences only, never the passages the
  system prompt explicitly asks the model to draw from.

## Suite count

`tests/interpretive/test_palm_reading.py` alone: **40 passed** (36
R1/R3-era + 4 new), 0 failures on final run.

Full suite: **3200 passed, 3 skipped** (was 3196/3 before this task —
net +4). Zero regressions elsewhere.
