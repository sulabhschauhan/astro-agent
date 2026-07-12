# S66 Task 13 — F2c: voice retry loop + exemplar anchoring + temp 0

Self-gated. Files: `agent/interpretive/palm_reading.py` +
`tests/interpretive/test_palm_reading.py` (atomic, per the S66 Task 8
precedent — the retry changes call-count semantics the tests pin).

## Diff summary

### Step 1 — Exemplar anchoring (additive, PREPEND)
`_READING_SYSTEM_PROMPT`'s `## Voice` block gained a new sentence
between the existing declarative-register instruction and the
(unchanged) FORBIDDEN list:
> Write in Cheiro's declarative register. Model sentences: "A deep,
> unbroken line of life promises long life, good health, and
> vitality." / "Such a fate line denotes success won by personal
> merit." Assert what the hand shows and what the tradition says it
> denotes — concrete consequences, never affirmations about the
> reader's inner journey.

Read literally as additive ("PREPEND ... above the forbidden list",
not "replace") — the original declarative-register sentence is kept,
not removed, so the block now carries both the original framing and
the new exemplar-anchored one. Flagging this interpretation explicitly
in case the intent was a replacement instead.

### Step 2 — Temperature 0.4 -> 0
`_READING_TEMPERATURE = 0`, comment updated: checkpoint-adjacent output
must be reproducible; variance probing moves to Ring 3 Run B (residual
API nondeterminism only); revisit trigger = pass-2 evidence that
temp-0 readings are degenerate.

### Step 3 — Validator-fed single retry
- New `_run_ring1_checks(text, context_corpus)` helper (DRY factor of
  the 4 validator calls, now invoked twice: first draft + retry).
- `PalmReadingResult` gains `retry_used: bool` (additive field).
- `generate_palm_reading()`: first draft always generated and
  validated as before. If `failures` is non-empty, ONE retry fires:
  same `messages` + an assistant turn (the failed draft, verbatim) +
  a user turn ("Your draft failed these checks: `<failures joined with
  "; ">`. Rewrite the reading correcting ONLY these issues. Same facts,
  same structure."). The retry draft's validation result is final —
  fail-closed, no further retries. HARD CAP: max 2 LLM calls ever,
  documented inline citing S23 + the S66 pre-flight probe
  (`f906f3e` — 3/3 live runs tripped `self_help_blacklist` pre-F2c) and
  CLAUDE.md Working Style #5/#9 (the reviewer is a regex, not an LLM —
  not AI-reviewing-AI). Revisit trigger: pass-2 shows the retry ALSO
  failing routinely -> prompt/validator redesign signal, never a cap
  increase.
- **app.py NOT touched.** Step 3's conditional ("capture log in app.py
  picks it up ONLY if trivially additive there") was evaluated: adding
  a `retry_used` line to `_capture_dogfood_run`'s markdown block would
  in fact be a one-line, non-breaking addition. Left undone anyway
  because this task's own top-line scope declaration ("Self-gated.
  Files: `agent/interpretive/palm_reading.py` +
  `tests/interpretive/test_palm_reading.py`") and the STEP 5 commit
  message ("atomic with tests") both name exactly two files — treated
  that explicit scope as authoritative over Step 3's conditional, to
  keep the ratified commit strictly atomic to the stated pair. Noted
  here as the required "otherwise ... note it" follow-up: a trivial
  one-line pickup in `frontend/app.py`'s `_capture_dogfood_run`
  (`### ring1_validation` section) is available whenever app.py is
  next in scope.

## Step 4 — Test updates

`tests/interpretive/test_palm_reading.py`:
- `_FakeCompletions`/`_FakeClient` gained an optional `responses: list[
  (content, exception)]` param — consumed one tuple per `.create()`
  call in order (clamped to the last entry past the list length,
  though no test relies on that clamp firing). `content`/`exception`
  single-shot construction stays supported unchanged for every
  pre-existing test.
- Item 9 renamed `test_exactly_one_llm_call_when_first_draft_passes`,
  now also asserts `validation.passed is True` and `retry_used is
  False`.
- Item 9b (3 new tests):
  - (a) `test_retry_after_failed_first_draft_then_clean_retry_passes`
    — first draft trips (`stability`), retry is clean -> 2 calls,
    `passed=True`, `retry_used=True`; also asserts the retry message
    structure directly (`[system, user, assistant(draft), user
    (feedback)]`, 4 messages) and that the feedback turn contains the
    literal failure string `"self_help_blacklist: found stability"`.
  - (b) `test_retry_after_failed_first_draft_still_fails_stays_failed`
    — both drafts trip (`stability` then `empowerment`) -> exactly 2
    calls, `passed=False`, `retry_used=True`, and the SECOND draft's
    failure (`empowerment`) is what's reported, not the first's
    (`stability`) — proves the retry result is what's final, not a
    merge of both attempts.
  - (c) `test_retry_call_raises_becomes_runtime_error_no_third_call` —
    first draft trips, retry call itself raises `ConnectionError` ->
    `RuntimeError` propagates (same message pattern as item 8), exactly
    2 calls recorded (proves no third call was attempted).

Isolated file run: **21 passed** (18 pre-existing + 3 new), 0 failed.

## Step 5 — Full suite

```
3177 passed, 3 skipped, 1 warning in 79.81s (0:01:19)
```
3174 (S66 Task 11 baseline) + 3 new retry tests = 3177. Zero delta
beyond the 3 new tests. Green -> committed.

Commit: `165484c` — "S66 F2c: Cheiro exemplar anchoring + temp 0 +
validator-fed single retry (atomic with tests)"

## Step 6 — Pass-2 pre-flight probe RE-RUN (live, post-F2c)

Same 3 fixture images as Task 12
(`palm_left_test.jpg`/`palm_right_test.jpg`/`Back Hand.jpeg`), same 3
run shapes (A: left+right, B: identical repeat, C: +hand_detail). No
asserts — measure only.

### RUN A
```
Your hands reveal a robust and grounded nature, with a strong potential for health and vitality. The square shape of your palms, combined with the long, straight fingers and rounded fingertips, suggests a practical and methodical approach to life. This is further emphasized by the deep and unbroken lines of life, head, and heart on both hands, indicating a stable and consistent character.

The deep and long life line on both hands, curving around the base of the thumb without any breaks or irregularities, promises a long life filled with good health and vitality. This is a strong indicator of your innate potential for resilience and physical well-being. The developed Mount of Venus on both hands supports this, suggesting a robust constitution and a passionate nature. This mount also indicates a strong capacity for affection and a love for beauty and harmony in life.

Your head line, deep and slightly curved, reflects a clear and logical mind, capable of making sound decisions. The consistency of this line across both hands suggests that your mental faculties are both a natural strength and a current asset. The heart line, also deep and slightly curved, indicates a warm and sincere emotional nature. Its slight upward curve in the right hand suggests that your current trajectory involves a focus on emotional connections and relationships.

The barely visible fate line on both hands suggests that your life path is not heavily influenced by external forces or destiny. Instead, your life is shaped by your own choices and actions. This aligns with the practical and self-reliant nature indicated by your hand shape and lines.

Overall, your hands reveal a person who is grounded, practical, and capable of achieving a balanced and rewarding life through personal effort and clear decision-making. Your strong health and emotional warmth are key assets in your current life path.

For major life decisions, I recommend consulting a qualified astrologer or palm reader for a personal reading.
```
`validation.passed = True` / `validation.failures = ()` / **`retry_used = True`**

### RUN B (identical repeat)
```
Your hands reveal a robust and grounded nature, with a strong potential for health and vitality. The square shape of your palms, combined with the long, straight fingers, suggests a practical and methodical approach to life. This is further supported by the deep and unbroken lines of life, head, and heart on both hands, indicating a stable and consistent character.

The deep and long life line, curving around the base of the thumb, promises a life of good health and vitality. This line, free from breaks or forks, suggests a life path that is steady and free from major disruptions. The developed Mount of Venus on both hands indicates a strong capacity for affection, sympathy, and a love for beauty and harmony. This mount also suggests robust health, as it is associated with the vitality of the blood vessels in the hand.

Your head line, deep and slightly curved, points to a clear and logical mind, capable of making sound decisions. The lack of breaks or forks in this line suggests a focused and unwavering mental approach. The heart line, also deep and slightly curved, indicates a warm and sincere nature in matters of the heart, with a capacity for deep emotional connections.

The barely visible fate line suggests that your life path may not be strongly influenced by external forces or destiny. Instead, your direction is likely shaped by your own actions and decisions. This aligns with the practical and self-reliant nature indicated by your hand shape and lines.

Overall, your hands reveal a person who is grounded, practical, and capable of maintaining a steady course in life. Your innate potential for health and vitality is mirrored in your current life trajectory, suggesting that you are on a path that aligns well with your natural strengths and inclinations.

For major life decisions, I recommend consulting a qualified astrologer or palm reader for a personal reading.
```
`validation.passed = True` / `validation.failures = ()` / **`retry_used = True`**

### RUN C (+ hand_detail)
```
Your hands reveal a robust and grounded nature, with a strong potential for vitality and health. The square shape of your palms, combined with the long, straight fingers, suggests a practical and methodical approach to life. This is further supported by the deep, unbroken lines of life, head, and heart on both hands, indicating a stable and consistent character.

The deep and long life line on both hands promises good health and vitality. Its unbroken nature suggests a life free from major health crises, allowing you to pursue your ambitions with vigor. The developed Mount of Venus on both hands indicates a strong capacity for affection and a love for beauty and harmony. This mount also suggests a robust physical constitution, which aligns with the promise of good health seen in your life line.

Your head line, deep and slightly curved, points to a clear and logical mind, capable of both practical reasoning and creative thought. This line's consistency across both hands suggests that your innate intellectual potential is being realized in your current life path. The heart line, also deep and slightly curved, indicates a warm and sincere nature in matters of the heart, with a capacity for deep emotional connections.

The barely visible fate line suggests that your life path may not be strongly influenced by external forces or destiny. Instead, your direction is likely shaped by your own decisions and efforts. This aligns with the practical and self-reliant nature indicated by your hand shape and lines.

The Mount of Jupiter, slightly raised, suggests ambition and a desire for achievement, though it is not overly pronounced, indicating a balanced approach to power and leadership. The moderate spacing of your fingers and the medium-sized thumb set at a wide angle suggest a balance between flexibility and determination, allowing you to adapt to circumstances while maintaining your goals.

Overall, your hands reveal a person of strong health, practical intelligence, and emotional depth, with a life path shaped largely by personal effort and decisions rather than fate.

For major life decisions, I recommend consulting a qualified astrologer or palm reader for a personal reading.
```
`validation.passed = True` / `validation.failures = ()` / **`retry_used = True`**

### Reading of the result

Zero exceptions across all 6 generation calls (2 per run x 3 runs) plus
the 3 vision calls. **All 3 final readings now pass Ring 1 validation**
— a reversal of the Task 12 pre-flight result (3/3 failed there). BUT
**all 3 runs required the retry** (`retry_used=True` in every case):
the FIRST draft still tripped the self-help blacklist in every run,
same as pre-F2c behavior — the exemplar anchoring + temp 0 change did
NOT measurably reduce the first-draft failure rate in this 3-run
sample. What changed the observed outcome is the retry mechanism
itself: the validator-fed correction turn successfully produced a
passing second draft in 3/3 attempts. This matches the HARD CAP
comment's own stated premise ("prompt-only voice control fails ~100%
for this task shape") rather than contradicting it — the retry is
carrying the fix, as designed, not the prompt change. Whether the
first-draft failure rate itself should be a future target (vs.
accepting "always needs one retry" as the steady state) is a call for
whoever scores pass-2, not decided here (measure-first, no asserts,
per this task's charter).

No source files edited in this step (probe only, scratch script +
output file deleted after capture).

## Commits
- `165484c` — source: F2c (exemplar anchoring + temp 0 + retry loop),
  atomic with tests
- diagnostics (this file) — pushed separately, hash reported after
  commit below
