# E2 Stage-1 Retry Investigation — Diagnostic Audit (thumb + fingers only)

Read-only pass. No source or test edits made. Scope: Stage-1 claim-extraction
retries for `thumb` and `fingers` body-part categories only.

## Path correction (flagged, not asked — not blocking)

The instructing prompt named `agent/palm/claim_extraction.py` and `tests/palm/`.
Neither path exists in this repo. Verified actual locations:
- `agent/interpretive/claim_extraction.py` (470 lines)
- `tests/interpretive/test_claim_extraction.py` (523 lines)

All citations below use the real paths.

---

## Step 1 — Retry trigger / cap / backoff, quoted verbatim (thumb + fingers paths)

`claim_extraction.py` has no per-feature branching — `thumb` and `fingers` run
through the exact same generic loop as every other registry feature
(`_FEATURE_REGISTRY`, `palm_reading.py:178-182`, confirms `"thumb"` and
`"fingers"` are plain registry entries, no special-casing anywhere in either
file — grep-verified, zero hits for `"thumb"` or `"finger"` as literal strings
inside `claim_extraction.py` itself).

**Per-feature call loop** — `claim_extraction.py:403-454` (`extract_claims`):

```
403	    for feature in attempted_features:
...
409	        diag["call_count"] += 1
410	        try:
411	            raw = _call_llm(client, [
412	                {"role": "system", "content": _EXTRACTION_SYSTEM_PROMPT},
413	                {"role": "user", "content": _build_user_prompt(feature, observation_text, chunks)},
414	            ])
415	        except Exception as exc:  # noqa: BLE001 -- one bad call must not crash extract_claims
416	            failed_features.append(feature)
417	            diag["status"] = "failed"
418	            diag["error"] = f"claim_extraction: API call failed for feature {feature!r}: {exc}"
419	            feature_diagnostics[feature] = diag
420	            continue
421	
422	        accepted, failures = _validate_response(raw, chunk_map)
423	
424	        if failures:
425	            diag["retry_used"] = True
426	            diag["call_count"] += 1
427	            try:
428	                raw = _call_llm(client, _build_retry_messages(feature, observation_text, chunks, raw, failures))
429	            except Exception as exc:  # noqa: BLE001
430	                failed_features.append(feature)
431	                diag["status"] = "failed"
432	                diag["error"] = f"claim_extraction: API retry failed for feature {feature!r}: {exc}"
433	                diag["first_attempt_failures"] = failures
434	                feature_diagnostics[feature] = diag
435	                continue
436	            accepted, failures = _validate_response(raw, chunk_map)
437	
438	        if failures:
439	            failed_features.append(feature)
440	            diag["status"] = "failed"
441	            diag["failures"] = failures
442	            feature_diagnostics[feature] = diag
443	            continue
```

**Retry trigger** = any non-empty `failures` list returned by `_validate_response`
(`claim_extraction.py:208-259`). Sub-triggers, quoted:

- Malformed JSON (`claim_extraction.py:214-217`):
  ```
  214	    try:
  215	        parsed = json.loads(raw)
  216	    except json.JSONDecodeError as exc:
  217	        return None, [f"malformed JSON response: {exc}"]
  ```
- Missing/wrong-typed top-level `claims` key (`claim_extraction.py:219-220`):
  ```
  219	    if not isinstance(parsed, dict) or "claims" not in parsed or not isinstance(parsed["claims"], list):
  220	        return None, ["response missing a top-level 'claims' list"]
  ```
- Per-claim not an object (`claim_extraction.py:225-227`):
  ```
  225	        if not isinstance(raw_claim, dict):
  226	            failures.append(f"claims[{i}] is not an object")
  227	            continue
  ```
- E-2 missing required keys (`claim_extraction.py:233-236`):
  ```
  233	        missing = _REQUIRED_CLAIM_KEYS - set(raw_claim)
  234	        if missing:
  235	            failures.append(f"claims[{i}] missing keys: {sorted(missing)}")
  236	            continue
  ```
- E-2 invalid valence (`claim_extraction.py:237-239`):
  ```
  237	        if raw_claim["valence"] not in _VALID_VALENCE:
  238	            failures.append(f"claims[{i}] invalid valence: {raw_claim['valence']!r}")
  239	            continue
  ```
- E-1 illegal chunk_id, i.e. cites a chunk_id outside THIS feature's own gated
  set (`claim_extraction.py:243-246`):
  ```
  243	        chunk_id = raw_claim["chunk_id"]
  244	        if chunk_id not in chunk_map:
  245	            failures.append(f"claims[{i}] cites chunk_id {chunk_id!r}, not in this feature's own gated set")
  246	            continue
  ```
- E-3 paraphrase-overlap floor, `_PARAPHRASE_OVERLAP_FLOOR = 0.40`
  (`claim_extraction.py:94`, `247-254`):
  ```
  247	        overlap = _overlap_ratio(raw_claim["claim_text"], chunk_map[chunk_id])
  248	        if overlap < _PARAPHRASE_OVERLAP_FLOOR:
  249	            failures.append(
  250	                f"claims[{i}] claim_text overlap {overlap:.2f} below floor "
  251	                f"{_PARAPHRASE_OVERLAP_FLOOR} for chunk {chunk_id!r}"
  252	            )
  253	            continue
  ```

**Retry cap**: exactly one retry block exists in the loop (lines 424-436) —
no loop, no counter, no configurable max. Docstring states it explicitly
(`claim_extraction.py:364-367`):
```
364	    Hard cap: 2 LLM calls per feature, no exceptions. A feature whose
365	    retry ALSO fails validation lands in `failed_features` -- fail-closed:
366	    zero claims from it survive, and it is the caller's job (a later
367	    wiring prompt) to treat it as unsupported downstream.
```

**Backoff**: none. Grepped `claim_extraction.py` for `sleep|backoff|time\.|max_retries|for _ in range|while ` — zero matches. The retry call fires immediately after the first `_validate_response` failure, no delay.

**API-exception handling is a SEPARATE path from validation-triggered retry**:
an exception on the *first* call (line 415) fails the feature immediately,
`diag["retry_used"]` stays `False` — no retry attempt. Only a *successful*
call that fails Python-side validation triggers the retry (line 424). An
exception on the *retry* call itself (line 429) also fails closed, no third
call.

**`stage1_retry_features` attribution** (what the dogfood log actually
records) — `palm_reading.py:1646-1649`:
```
1646	    stage1_retry_features = tuple(
1647	        f for f in _FEATURE_REGISTRY
1648	        if extraction_result.diagnostics.get("features", {}).get(f, {}).get("retry_used")
1649	        )
```

---

## Step 2 — `diagnostics/dogfood_capture.md` RUN blocks touching thumb/fingers

File is 310 lines, 3 `## RUN` blocks total, all 3 include THUMB and FINGERS
in their confirmed descriptions (grep: `thumb|finger` case-insensitive, 47
matching lines across the file). 3 meets the "≥3 RUN blocks" bar — proceeding,
not stopping.

| Run timestamp | `stage1_retry_features` | Thumb final claims | Fingers final claims | Retry changed claim set? | Error/warning surfaced |
|---|---|---|---|---|---|
| `2026-07-23T18:42:14.473283` (line 1) | `thumb` | **0** (thumb absent from `claims_inventory`, line 82-87; thumb IS in `supported_features`, line 79) | 1 (C4, corrective, line 86) | Yes — thumb retried, ended with 0 claims; `feature_support` still marks it "supported" (retrieval-gate level, unaffected by extraction outcome) | No explicit error/failure text captured for thumb in this file (see gap noted in Step 6) |
| `2026-07-23T18:43:13.277529` (line 100) | `thumb` | **0** (absent, line 181-186; supported per line 178) | 1 (C4, corrective, line 185) | Same pattern as Run 1 | Same gap |
| `2026-07-23T18:44:11.215275` (line 199) | `fingers` | 1 (C2, supports, line 292 — **no retry needed for thumb this run**) | 2 (C3 supports + C4 corrective, lines 293-294) | Yes — fingers retried and *recovered*, ended with 2 claims, none `excluded_from_voice` | No explicit error/failure text captured; `stage2_first_attempt_failures` shown but that's the separate Stage-2 voicing retry, not Stage-1 |

All 3 runs' `ring1_validation` blocks show `passed: True` and
`stage1_retry_features` naming exactly one feature each — never both thumb
and fingers retrying in the same run, in this 3-run sample.

**Important correction to an initial mis-read**: the reading-text sentence
"the classical texts I work from do not clearly address the following ...
thumb" (present in Run 1 and Run 2, `dogfood_capture.md:56,155`) is **not**
proof that Stage-1 extraction failed for thumb. That sentence is built by
`_build_decline_block` (`palm_reading.py:719-735`), fed by
`_compute_decline_features` (`palm_reading.py:1404-1442`), whose decline set
is the union of three genuinely different causes:
```
1410	    """S69 F-H P5: decline set = union of (a) gate-unsupported features,
1411	    (b) features Stage 1 (extract_claims) failed to extract at all after
1412	    its own retry, and (c) gate-supported features whose Stage-1 claims
1413	    are ALL excluded_from_voice OR whose claims list is simply empty ...
```
Run 1/2's `feature_support` block explicitly lists `thumb` under
`supported_features`, not `unsupported_features` (cause (a) ruled out). Since
`PalmReadingResult.claims` carries the FULL Stage-1 inventory verbatim
including `excluded_from_voice=True` claims (`palm_reading.py:1796`,
`claims=prep.claims`), and Run 1/2's `claims_inventory` has **zero** rows of
any kind for `thumb`, cause (c) ("all excluded_from_voice") is also ruled
out — an excluded claim would still appear as a row. That leaves only cause
(b): either (b-i) both Stage-1 attempts for thumb failed validation
(`failed_features`), or (b-ii) the retried attempt validated cleanly but
returned a legitimately empty `claims` list (which itself never retries
further — see `test_empty_claims_list_is_legitimate_not_a_failure`). **The
dogfood capture file cannot distinguish (b-i) from (b-ii)** — see Step 6.

---

## Step 3 — Existing test coverage, `tests/interpretive/test_claim_extraction.py`

All 15 tests, feature-by-feature, retry-branch vs. happy-path:

| Test | Feature(s) used | Branch exercised |
|---|---|---|
| `test_happy_path_two_features_claims_rekeyed_and_diagnostics_populated` (L136) | life line, **thumb** | Happy path only, both features — no retry |
| `test_e1_illegal_chunk_id_retry_fed_failure_text_persistent_failure` (L192) | life line (fails+retries+fails), thumb (rides along, happy) | Retry branch — E-1, subject = **life line**, not thumb |
| `test_e2_invalid_valence_triggers_retry_then_recovers` (L229) | life line only | Retry branch — E-2 valence, recovers |
| `test_e2_missing_required_field_triggers_retry_persistent_failure` (L256) | life line (fails), **thumb** (rides along, happy) | Retry branch — E-2 missing keys, subject = life line |
| `test_e3_overlap_below_floor_triggers_retry_persistent_failure` (L282) | life line (fails), **thumb** (rides along, happy) | Retry branch — E-3, subject = life line |
| `test_e3_overlap_at_or_above_floor_passes` (L301) | life line only | Happy path, no retry |
| `test_e4_conditional_excluded_unless_condition_text_matches_confirmed_observation` (L320) | fate line only | Happy path (E-4 logic, no retry) |
| `test_e4_corrective_claim_retained_not_excluded` (L358) | **fingers only** | Happy path — **the only fingers test in the file**, single clean call, no retry |
| `test_retry_cap_exactly_two_calls_never_three` (L380) | life line (fails, capped at 2), **thumb** (rides along, happy) | Retry branch — cap enforcement, subject = life line |
| `test_api_exception_on_first_call_marks_feature_failed_others_succeed_no_raise` (L406) | life line (happy), **thumb** (exception on call 1) | Exception path, **not** the validation-retry path (exception on first call skips retry per code) |
| `test_api_exception_on_retry_call_marks_feature_failed_no_raise` (L434) | life line (happy), **thumb** (E-1 fails on call 1 → retry fires → call 2 raises exception) | **Retry DOES fire for thumb here** — first-attempt E-1 trigger with thumb as subject — but the retry's own outcome is an API exception, not a second validation check |
| `test_all_features_fail_raises_runtime_error` (L462) | life line AND **thumb**, both fail both calls (malformed JSON) | Retry branch, both features, ends in `RuntimeError` |
| `test_empty_claims_list_is_legitimate_not_a_failure` (L481) | fate line only | Happy path, empty claims, no retry |
| `test_feature_with_empty_gated_chunks_is_skipped_entirely` (L497) | life line (happy), heart line (0 chunks, skipped) | No call for heart line at all |
| `test_all_gated_empty_returns_empty_result_no_raise` (L510) | life line, **thumb**, neither called | No call at all |

---

## Step 4 — Coverage matrix (trigger × subject feature)

"Subject" = the feature whose response actually drives the trigger/retry
(not a happy-path ride-along feature in the same test).

| Trigger (Step 1 code ref) | Tested, subject = life line/fate line/heart line | Tested, subject = **thumb** | Tested, subject = **fingers** |
|---|---|---|---|
| Malformed JSON (214-217) | Covered (`test_all_features_fail...`, jointly w/ thumb) | Covered — jointly with life line in `test_all_features_fail_raises_runtime_error` (both fail on malformed JSON) | **Uncovered** |
| Missing top-level `claims` key (219-220) | **Uncovered** | **Uncovered** | **Uncovered** |
| Per-claim not an object (225-227) | **Uncovered** | **Uncovered** | **Uncovered** |
| E-2 missing required keys (233-236) | Covered (`test_e2_missing_required_field...`, subject = life line) | **Uncovered** as subject | **Uncovered** |
| E-2 invalid valence (237-239) | Covered (`test_e2_invalid_valence...`, subject = life line) | **Uncovered** as subject | **Uncovered** |
| E-1 illegal chunk_id — first-attempt trigger (243-246) | Covered (`test_e1_illegal_chunk_id...`, subject = life line) | **Covered** — `test_api_exception_on_retry_call_marks_feature_failed_no_raise`, thumb's call 1 is E-1-illegal, retry fires | **Uncovered** |
| E-1 illegal chunk_id — persistent failure across both attempts | Covered (`test_e1_illegal_chunk_id...`, `test_retry_cap...`) | **Uncovered** (thumb's retry-outcome test uses an exception, not a 2nd validation failure) | **Uncovered** |
| E-3 overlap floor (247-254) | Covered (`test_e3_overlap_below_floor...`, subject = life line) | **Uncovered** as subject | **Uncovered** |
| Retry-then-recover (any trigger clears on attempt 2) | Covered (`test_e2_invalid_valence_triggers_retry_then_recovers`, subject = life line) | **Uncovered** as subject | **Uncovered** — this is exactly the pattern Run 3 shows in production (fingers retries, recovers, 2 claims) and it has zero test coverage for fingers |
| API exception, first call (415-420) | Covered (thumb tests use life line as the happy-path partner) | Covered (`test_api_exception_on_first_call...`, subject = thumb) | **Uncovered** |
| API exception, retry call (429-435) | n/a | Covered (`test_api_exception_on_retry_call...`, subject = thumb) | **Uncovered** |
| Retry cap = exactly 2 calls, never 3 (structural) | Covered (`test_retry_cap_exactly_two_calls_never_three`, subject = life line) | **Uncovered** as subject (thumb only rides along happy-path in this test) | **Uncovered** |
| All-attempted-features-fail → `RuntimeError` (456-461) | Covered jointly (life line + thumb) | Covered jointly | **Uncovered** |
| E-4 conditional exclusion (290-342, not itself a retry trigger but produces the same "0 voiced claims despite a claim existing" symptom) | Covered (`test_e4_conditional_excluded...`, subject = fate line) | **Uncovered** | **Uncovered** |

**Net finding**: `fingers` has **zero** retry-path test coverage of any kind
— the single fingers test in the suite is a one-call happy path. `thumb` has
partial coverage (API-exception paths, and one E-1-first-attempt-trigger
case), but **no test exercises thumb undergoing a persistent E-1/E-2/E-3
validation failure across both attempts**, and **no test exercises thumb (or
fingers) retrying and recovering via a second validation-clean call** —
despite Run 3 showing exactly that recovery pattern for fingers in production.

---

## Step 5 — Hypotheses (cause of retry flakiness), tagged

**[Certain]** The retry mechanism itself is feature-agnostic — `thumb` and
`fingers` run through byte-identical code to every other feature. Grep of
`claim_extraction.py` for the literal strings `thumb`/`finger` returns zero
hits; nothing in this module special-cases either feature.

**[Certain]** There is no backoff/delay between attempt 1 and the retry, and
the cap is hard-coded at 2 calls with no configurability (verified: no
`sleep`/`backoff`/loop-counter construct anywhere in the file; structural
single-retry-block shape; `test_retry_cap_exactly_two_calls_never_three`
proves no 3rd call fires even when still failing).

**[Certain]** `dogfood_capture.md`'s `## RUN` capture path
(`frontend/app.py`'s `_capture_dogfood_run`) does not write
`stage1_failed_features` or any per-feature Stage-1 diagnostic (call_count,
failure list, error text) — only the aggregate `stage1_retry_features` tuple.
By contrast, `_capture_checkpoint_declined` (same file) *does* write
`stage1_failed_features`, but that path only fires when a user declines the
Stage-1 checkpoint, which none of the 3 captured RUN blocks did. This is a
capture-completeness gap, not a bug in the retry logic itself.

**[Likely]** Given a retry fired for thumb in Run 1/2, the cause was a
genuine E-1/E-2/E-3 (or malformed-JSON/schema) validation failure on
attempt 1 — not an API exception, since exceptions on the first call skip
retry entirely per the code (line 415-420) and are architecturally distinct
from the validation-triggered retry path (line 424).

**[Likely]** Thumb's inconsistent behavior across near-identical input text
(THUMB confirmed-description text is materially the same across all 3 runs:
"Medium relative size, set moderately low, wide angle from the palm" /
"medium size, low set, wide angle from the palm") — retrying-and-failing in
Run 1/2, succeeding cleanly with zero retry in Run 3 — is consistent with
either (a) genuine LLM output nondeterminism at temperature=0, or (b)
different retrieved chunks silently entering the per-feature user prompt
between runs (retrieval-level variance upstream of `claim_extraction.py`).
This module's own deterministic validators (E-1/E-2/E-3) behave identically
given identical input; the variance has to originate either in the LLM call
or in what gets retrieved and handed to it — this audit's scope (Step 1) does
not cover retrieval, so this cannot be narrowed further here.

**[Likely]** Fingers' one retry-and-recover instance (Run 3) is consistent
with an ordinary, successfully-self-corrected E-1/E-2/E-3 failure — nothing
in the evidence suggests a fingers-specific defect distinct from the generic
mechanism.

**[Guessing]** `gpt-4o-mini` at `temperature=0` (`claim_extraction.py:68-69`)
may not be perfectly deterministic across separate API calls even with
identical prompts — a commonly-reported general characteristic of the
underlying API, not something this module or its tests could control or
detect. Unverified in this codebase; would require an external, dedicated
determinism probe.

**[Guessing]** The 0.40 paraphrase-overlap floor (E-3) might reject
thumb/fingers claims more often than life-line claims if Cheiro's
thumb/finger doctrine passages (p.87, p.95, p.96, p.98 per the dogfood
`sources` sections) structurally produce lower-overlap paraphrases than
life-line passages do. Not measured in this pass — would require reading the
actual chunk texts and computing `_overlap_ratio` by hand, out of this
audit's scope (Step 1 only, source file only).

---

## Step 6 — Open questions (not resolvable from Steps 1-4 evidence alone)

1. For Run 1 and Run 2's thumb retry: did the retry ultimately land in
   `failed_features` (both attempts invalid) or succeed with a legitimately
   empty `claims` list? Not distinguishable from `dogfood_capture.md` as
   currently captured — needs either a fresh dogfood run with the
   Stage-1-prep checkpoint inspected before Stage 2 fires (the
   `PalmReadingPrep.diagnostics["stage1"]["features"]["thumb"]` dict, which
   `prepare_palm_reading()` computes but the `## RUN` capture path never
   writes to disk), or a capture-code change to persist it.

2. What was the exact first-attempt validation failure text for thumb in
   Run 1/2 (which specific trigger from Step 1's list fired)? Not captured
   anywhere in the current file.

3. Was the actual *set* of gated chunks retrieved for `thumb` identical
   across Run 1, 2, and 3? The `### sources` section is evidently a partial
   list (5 lines in Run 1/2, 7 in Run 3) and does not reliably show a
   `feature: thumb` line even when `feature_support` marks thumb
   "supported" — so this file cannot confirm or rule out retrieval-level
   variance between runs.

4. Is the observed thumb/fingers variance driven by LLM-side nondeterminism,
   retrieval-side variance, or both? Not separable from the current evidence
   — would need prompt-level logging on a fresh run (i.e., capturing the
   exact `_build_user_prompt` content sent to the model each time).

5. `diagnostics/archive/dogfood_capture_pre_S70_pass5.md` contains 6 further
   `stage1_retry_features: thumb` occurrences and zero `fingers`
   occurrences (grep-verified count only — content not read, and this file
   was explicitly out of this audit's step-2 scope, which named
   `diagnostics/dogfood_capture.md` only). If design chat wants a larger
   sample, that file exists, but its alignment with the *current*
   `claim_extraction.py`/`palm_reading.py` architecture has not been
   checked here and should not be assumed.

---

## Stop condition

Report written to `diagnostics/e2_stage1_retry_audit.md`. No source or test
files touched. No commit made.
