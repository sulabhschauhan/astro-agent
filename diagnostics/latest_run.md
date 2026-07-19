# S69 F-H P1: claim_extraction.py -- Stage-1 extraction module (new file only)

**NEW FILE ONLY.** `agent/interpretive/claim_extraction.py`. `palm_reading.py`,
`app.py`, and every test file are untouched -- wiring + tests are later
prompts in this sequence. Full suite run before commit, result below.

## What landed

`agent/interpretive/claim_extraction.py` -- pure per-feature claim
extraction stage for F-H's extract-then-voice split. Public API:

```python
extract_claims(
    gated_results: dict[str, list[dict]],   # same shape palm_reading._apply_support_gate emits
    texts_by_feature: dict[str, str],       # one confirmed-observation string per feature
    client=None,                             # injection seam; OpenAI() constructed lazily inside the function if None
) -> ExtractionResult
```

`Claim` (frozen dataclass): `claim_id, feature, chunk_id, claim_text, valence,
condition_text, observation_basis, excluded_from_voice, exclusion_reason`.
`ExtractionResult` (frozen dataclass): `claims: tuple[Claim, ...],
failed_features: tuple[str, ...], diagnostics: dict`.

Model/temp locked from `diagnostics/fh_stage1_probe_S69.md`:
`gpt-4o-mini` @ temperature `0` -- the probe found no quality tradeoff vs.
gpt-4o on this task (SC-1/2/3/5 identical PASS across all 12 cells at every
model/temp combination tried).

System prompt and stopword set are **transplanted verbatim** from
`scripts/probe_fh_stage1_extraction.py` (`_EXTRACTION_SYSTEM_PROMPT` /
`_STOPWORDS` / `_WORD_PATTERN` / `_content_words` / `_overlap_ratio`) --
not redrafted, since the probe validated that exact prompt text. The F2c
retry correction-instruction shape ("Your ... failed these checks: ...;
Re-extract ... correcting ONLY these issues.") mirrors
`palm_reading.py`'s own S66 F2c retry pattern (same deterministic-
reviewer-only mechanism, CLAUDE.md Working Style #5/#9 -- not AI-
reviewing-AI).

`_EXTRACTION_TIMEOUT_SECONDS = 30.0` is a **duplicated, cited** value
(same as `palm_reading._READING_TIMEOUT_SECONDS`), not an import -- an
import would create a circular dependency once `palm_reading.py` wires
this module in (a later prompt), since this module must never import
`palm_reading` back.

## Validator inventory

Run per feature, on every raw response (first attempt and retry alike):

| Validator | Checks | On failure |
|---|---|---|
| E-1 legality | `chunk_id` belongs to **that feature's own** gated set only (never a whole-reading union) | Whole-feature-response failure -> retry |
| E-2 schema | Required keys present (`chunk_id, claim_text, valence, condition_text, observation_basis`); `valence` in `{supports, corrective, conditional}`. `claim_id` NOT required/trusted -- always re-keyed by a module-owned `itertools.count` across the whole inventory | Whole-feature-response failure -> retry |
| E-3 paraphrase floor | content-word overlap (probe's stopword method) between `claim_text` and its cited chunk's text >= `_PARAPHRASE_OVERLAP_FLOOR` (0.40) | Whole-feature-response failure -> retry |
| E-4 conditional fail-closed | `valence == "conditional"` OR `condition_text is not None` (checked together, regardless of valence label -- deliberately conservative, see code comment) -> `excluded_from_voice=True, exclusion_reason="precondition unverified"` UNLESS `condition_text` is a case-insensitive substring of that feature's own `texts_by_feature` entry | Claim STAYS in the inventory, marked excluded -- not a retry trigger |

E-1/E-2/E-3 failures are **all-or-nothing per feature response** (any one
claim's violation rejects the whole response), matching
`palm_reading.py`'s own F2c precedent of retrying the whole draft rather
than patching individual sentences. Hard cap: 2 LLM calls per feature, no
exceptions. Retry-exhausted -> feature lands in `failed_features`
(fail-closed: zero claims from it survive).

`_PARAPHRASE_OVERLAP_FLOOR = 0.40` -- set from `fh_stage1_probe_S69.md`'s
pooled overlap distribution (min=0.50, p25=median=p75=max=1.00, n=73),
0.10 margin below the pooled minimum. Explicitly flagged in the code
comment as a **narrower-certainty threshold** than the 0.30 support-score
floor precedent: that floor sits between a measured negative-control
ceiling (0.2192) and a measured minimum genuine score (0.3954); this floor
has no negative-control measurement to sit above, only a
minimum-observed-genuine value to sit below. Revisit trigger: pass-5
evidence, or a future probe that measures a fabricated claim's overlap
score.

`RuntimeError` raised only when every feature that had >=1 gated chunk
failed extraction on both tries -- "nothing extractable, no reading
possible" per the Stage-1 fail-closed ruling. A `gated_results` where
every feature has zero gated chunks (nothing attempted at all) returns an
empty, non-raising `ExtractionResult` instead -- verified by manual
smoke test (see below), not by this prompt's test suite (no test file
touched per the instructing prompt).

## Manual smoke tests (not part of the committed test suite -- ad hoc, this session only)

Verified against a stub client (no real API calls) before running the
full suite:
- Clean success (supports valence, high overlap) -> claim retained,
  `excluded_from_voice=False`.
- Conditional claim, `condition_text` NOT present in the feature's
  confirmed observation text -> `excluded_from_voice=True,
  exclusion_reason="precondition unverified"`, claim still returned in
  the inventory (not dropped).
- Corrective claim -> retained, never excluded (absent a populated
  `condition_text`).
- First response cites an illegal `chunk_id` (E-1 violation) -> single
  retry fires, corrected response on retry -> feature succeeds,
  `retry_used=True`, `call_count=2`.
- Feature with zero gated chunks -> skipped entirely, never appears in
  `diagnostics["features"]`, contributes nothing to `failed_features`.
- One feature fails both tries (malformed JSON) alongside another
  feature that succeeds -> failed feature lands in `failed_features`,
  succeeding feature's claims still returned, **no exception raised**
  (not all attempted features failed).
- ALL attempted features fail both tries -> `RuntimeError` raised, as
  specified.
- All-gated-empty input (nothing attempted anywhere) -> empty,
  non-raising `ExtractionResult`.
- API exception (not just malformed JSON) on a feature's calls -> caught,
  feature marked failed with a `claim_extraction: API call failed for
  feature ...` message, never propagates out of `extract_claims` for a
  single-feature failure.
- `call_count` diagnostics reflect calls **attempted**, not just calls
  that returned content (fixed during this session -- initially only
  incremented on a successful return, undercounting a first-call API
  exception as `call_count=0`; corrected to increment before the
  try/except).

## Full suite result

```
3220 passed, 3 skipped, 1 warning in 96.10s
```

Unchanged from the pre-existing baseline (no test file touched, no
production file other than the new module touched).

## CLAUDE.md registration items to carry to F-H close-out (NOT done here)

Per this prompt's own instruction, these are flagged for the close-out
prompt, not added to CLAUDE.md now:

1. **ACCEPTED DEVIATION**: the extractor may legitimately decline a
   conditional claim upstream (empty `claims` list for a feature, or a
   claim landing with `excluded_from_voice=True` via E-4) rather than
   force an unverifiable precondition into voice. This is NOT a defect --
   it is the module's own deterministic analog of the same conservatism
   `fh_stage1_probe_S69.md`'s SC-4 finding already observed at the
   model-call level (12/12 probe cells declined to extract a fate-line
   claim referencing the rises-from-life-line precondition, since "barely
   visible" never confirms where the line rises from). Registered at 2 of
   the CLAUDE.md 3-place convention's 3 places so far (this module's own
   docstring, and the E-4 code comment) -- place 1 (a CLAUDE.md Known-
   Source-Divergences entry) is close-out's job.
2. **Accepted gaps (a) and (f) retirement candidate**: `palm_reading.py`'s
   accepted-gap register describes V-2 anchor legality as "union-only
   across all gated features" and its shared-chunk false-positive
   consequence (f). `claim_extraction.py`'s E-1 validator checks legality
   strictly per-feature (against only the chunk_id set offered to that
   feature's own extraction call), which is the module-contract-level fix
   those two gaps were deferred pending -- but they are NOT yet closeable
   in CLAUDE.md, since `palm_reading.py` doesn't call this module yet
   (wiring is a later prompt). Close-out should revisit gap (a)/(f)'s
   register text once wiring lands and Stage-2 (voice) actually consumes
   `Claim.chunk_id` attribution end to end.
3. **`_PARAPHRASE_OVERLAP_FLOOR`'s narrower-certainty status** (see above)
   is worth a CLAUDE.md THRESHOLD DISCIPLINE line of its own once F-H
   lands live, distinguishing it from the 0.30 support-gate floor's
   fuller two-sided justification.

## Verdict

New file only, as instructed. `palm_reading.py`, `app.py`, and all test
files untouched. Suite green at 3220/3, matching the pre-existing
baseline exactly. Wiring (calling `extract_claims` from `palm_reading.py`)
and the corresponding test coverage are explicitly out of scope for this
prompt -- next prompts in the F-H sequence.
