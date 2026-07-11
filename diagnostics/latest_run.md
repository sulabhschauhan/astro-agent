# Session 60 closeout verification (no source edits)

Verification-only pass confirming the S60 commit landed correctly and
its post-pin expectation holds on a fresh live run. No files edited
other than this entry.

## 1. Last commit contents

```
commit 712d9cc829b36f370ce905620a34e983c01f8e7f
S60: golden set arudha_lagna coverage (3 rows), harness whitelist, q3 ratified REFUSAL, baseline superseded

 agent/eval/golden_harness.py                    |  7 +--
 diagnostics/golden_scorecard_20260710_184703.md | 68 +++++++++++++++++++++++
 diagnostics/latest_run.md                       | 71 +++++++++++++++++++++++++
 tests/fixtures/golden_qa_sulabh.py              | 51 +++++++++++++-----
 4 files changed, 181 insertions(+), 16 deletions(-)
```

Matches expectation: `golden_harness.py` whitelist wiring,
`golden_qa_sulabh.py` q3 pin, the new frozen-baseline scorecard, and the
prior diagnostics entry -- exactly the 4 files the S60 task committed.
`diagnostics/calc_router_stage2.log` NOT present -- confirmed not
committed.

## 2. calc_router_stage2.log ignore rule

```
$ git check-ignore -v diagnostics/calc_router_stage2.log
.gitignore:32:diagnostics/calc_router_stage2.log	diagnostics/calc_router_stage2.log
```

Ignore rule exists, `.gitignore` line 32, exact-path match. Confirms the
Session 59 carry-forward item ("closed: added to .gitignore and
un-tracked from git") still holds -- no drift.

## 3. Post-pin golden harness run

```
runnable=19 non_runnable_batch=2 match=8 match_stage2=7 design_debt=0 known_gap=4 new_gap=0 error=0
report: diagnostics/golden_scorecard_20260711_043812.md
```

**Exact match to the S60 task's stated expectation**
(`match=8/match_stage2=7/known_gap=4/new_gap=0`) -- zero deviation.
`sulabh_arudha_q3_refusal_probe` now resolves `MATCH_STAGE2` (ratified
`REFUSAL` == observed `REFUSAL`, routed via Stage 2), no longer
`NEW_GAP`. No per-row deviation to investigate against
`calc_router_stage2.log`; skipped that check since there was nothing to
explain.

No commit made -- verification-only task, per instruction.

---

# Session 60: pin q3 ratified REFUSAL + commit both sessions' staged arudha_lagna work

Scope: `tests/fixtures/golden_qa_sulabh.py` (surgical, row
`sulabh_arudha_q3_refusal_probe` only) + a supersession header on
`diagnostics/golden_scorecard_20260710_184703.md` + this diagnostics
entry. No other code file touched.

## Edit 1 -- golden_qa_sulabh.py, `sulabh_arudha_q3_refusal_probe`

- `expected_tier`: `"MEASURE_FIRST_PENDING_RATIFICATION"` ->
  `"REFUSAL"`, ratified from the S59(cont.7) live run's observed actual
  tier (`diagnostics/golden_scorecard_20260710_184703.md`).
- Claim verdict `"PENDING"` -> `"MATCH"`; note rewritten to record: the
  REFUSAL is produced by the Stage 2 low-confidence fallback ("question
  not classifiable with confidence"), NOT deterministic Stage 1 --
  category posture is MATCH_STAGE2, monitored not asserted, same as the
  ledger's other Stage-2-routed rows. Documented a MONITORED RISK: a
  future run where Stage 2 instead classifies this question as
  marriage_compatibility at high confidence is expected variance by
  construction, but a SUBSTANTIVE answer from that flip would be a
  product-quality signal (Upapada Lagna != Ashtakoot marriage
  compatibility) -- escalate to design chat if ever observed, don't
  silently reclassify or fold into `_KNOWN_GAPS`/`_DESIGN_DEBT`.

## Edit 2 -- supersession header, golden_scorecard_20260710_184703.md

Prepended a header mirroring `golden_scorecard_20260707_091459_
post_av_transit.md`'s own convention: declares this file the new frozen
comparison baseline (21-row ledger, first run to execute the 3 arudha
rows), and notes `sulabh_arudha_q3_refusal_probe`'s `NEW_GAP` categorization
in this specific run's own per-row table is a run-time artifact (row
executed before ratification, still carrying the placeholder) rather than
a live gap -- with the post-pin expectation for any future re-run:
`match=8, match_stage2=7, known_gap=4, new_gap=0`.

## Verification

Fixture import:
```
total rows: 21
q3 expected_tier: REFUSAL
q3 claim verdict: MATCH
IMPORT_OK
```

Grep for `MEASURE_FIRST_PENDING_RATIFICATION`: zero hits in `tests/` or
`agent/` (confirmed by directory-scoped greps). 5 remaining hits are all
in `diagnostics/` -- historical run logs (`latest_run.md`'s own prior
entries) and this scorecard's per-row table, which accurately records
what the placeholder value WAS at the moment that run executed, before
ratification. These are historical record, not live references, and were
deliberately left unscrubbed -- rewriting a past run's own recorded
output would misrepresent history, not fix a bug.

## Commit

Both this session's fixture pin and the prior session's staged
`golden_harness.py` whitelist wiring committed together, per task
instruction, as one commit:

`S60: golden set arudha_lagna coverage (3 rows), harness whitelist, q3
ratified REFUSAL, baseline superseded`

Files: `agent/eval/golden_harness.py`, `tests/fixtures/golden_qa_sulabh.py`,
`diagnostics/golden_scorecard_20260710_184703.md` (new), this
`diagnostics/latest_run.md` entry. `diagnostics/calc_router_stage2.log`
remains uncommitted/gitignored -- unchanged, still an open carry-forward
per CLAUDE.md.

---

# Session 59 (cont. 7): wire arudha_lagna into golden_harness.py

ONE FILE: `agent/eval/golden_harness.py`. Not committed — q3's ratification
and the scorecard baseline-supersession decision happen in design chat
first, per task instruction.

## Edits applied (2, surgical)

1. `_GOLDEN_DOMAIN_TO_PIPELINE_DOMAIN` += `"arudha_lagna": "arudha_lagna"`
   (golden row `domain` value and pipeline `domain` value are identical
   strings for this domain, unlike career/marriage/dasha's renamed
   mappings — confirmed by reading `chart_profile.py`'s `_VALID_DOMAINS`
   and `calc_router.py`'s routing target before adding the entry). This
   single entry makes all 3 new `golden_qa_sulabh.py` rows RUNNABLE (all
   use `chart="sulabh"` + `domain="arudha_lagna"`, matching
   `_classify_runnability()`'s existing chart+domain-membership check
   unchanged).
2. Module docstring's runnability sentence: "three pipeline-whitelisted
   domains (career/marriage/dasha)" -> "four pipeline-whitelisted domains
   (career/marriage/dasha/arudha_lagna)".

Neither `_KNOWN_GAPS` nor `_DESIGN_DEBT` touched. Route-determination
logic (`_run_runnable_row`'s stage1/stage2/fastpath branching) untouched
— arudha_lagna needs no fastpath branch (routes via Stage 1 keyword
scoring like career/marriage/dasha; only sade_sati has a fastpath).

## Live harness run

```
runnable=19 non_runnable_batch=2 match=8 match_stage2=6 design_debt=0 known_gap=4 new_gap=1 error=0
report: diagnostics/golden_scorecard_20260710_184703.md
```

19 runnable = 16 prior + 3 new arudha rows, as expected.

### Per-row results, 3 new arudha rows (verbatim from the report)

| id | expected_tier | actual | route | category |
|---|---|---|---|---|
| sulabh_arudha_q1_stage1 | TIER_1_EXACT | TIER_1_EXACT | stage1 | MATCH |
| sulabh_arudha_q2_stage2 | TIER_1_EXACT | TIER_1_EXACT | stage2 | MATCH_STAGE2 |
| sulabh_arudha_q3_refusal_probe | MEASURE_FIRST_PENDING_RATIFICATION | **REFUSAL** | stage2 | NEW_GAP |

- `q1_stage1` -> exactly as predicted: `TIER_1_EXACT`/`stage1`/`MATCH`.
- `q2_stage2` -> exactly as predicted: routed via `stage2`,
  `MATCH_STAGE2` (monitored, not asserted — a live GPT-4o-mini call
  resolved it correctly this run).
- `q3_refusal_probe` -> `NEW_GAP` by construction (placeholder
  `expected_tier` never matches any real tier), as predicted. **Observed
  actual tier: `REFUSAL`**, `demotion_reason="question not classifiable
  with confidence"`, routed via `stage2` (upapada lagna hits zero
  `_ARUDHA_LAGNA_KEYWORDS` and no other domain's keywords strongly
  enough to clear Stage 1, so it falls through to Stage 2, which itself
  returned a non-"high"-confidence/unclassifiable result and REFUSED).
  This is the value for design chat to ratify against
  `MEASURE_FIRST_PENDING_RATIFICATION`.

### Deviation from the task's stated call-count expectation (reporting exactly, not rounding up)

Task text predicted "10 live Stage 2 calls this run, up from 9" (9 prior
+ 1 for q2 alone). The report's own computed `stage2_routed_rows` list is
**11**, not 10:
`sulabh_career_q1, sulabh_career_q2, sulabh_career_q3, sulabh_career_q4,
sulabh_marriage_q7, sulabh_marriage_q8, sulabh_marriage_q9,
sulabh_marriage_q10, sulabh_dasha_q15, sulabh_arudha_q2_stage2,
sulabh_arudha_q3_refusal_probe` (9 pre-existing + q2 + q3). The task's
prediction only accounted for q2 needing Stage 2; q3 also required a live
Stage 2 call (it isn't Stage-1-clean either, for the keyword-miss reason
above) — an 11th call, not anticipated in the task's own count. Flagging
this rather than silently reporting "10 as expected."

## Diff: 18 pre-existing rows vs. baseline `golden_scorecard_20260707_091459_post_av_transit.md`

Compared `actual` tier and `route` (baseline's "routed via" column,
Stage 1 vs Stage 2 vs fastpath) for all 18 pre-existing row IDs against
this run's report. **Zero `actual`-tier changes; zero route changes.**
Every row that was `TIER_2_RANGE`/`TIER_1_EXACT`/`REFUSAL` in the
baseline is the identical tier this run; every row's Stage
1/Stage 2/fastpath route is unchanged.

The only differences are `category` LABEL naming, and they are 100%
explained by the two reports using different classification schemes
(documented in the baseline file's own header, not a real divergence):
- `sulabh_career_q1/q2/q3`, `sulabh_marriage_q7/q8`: baseline labels
  `STAGE2_VARIABLE` (its own stricter "any Stage-2-routed row" scheme);
  this run labels `MATCH_STAGE2` (`golden_harness.py`'s native
  scheme for "Stage 2 routed AND tier matched"). Same underlying
  outcome, different label vocabulary.
- `sulabh_career_q4`, `sulabh_marriage_q9/q10`, `sulabh_dasha_q15`:
  baseline labels `STAGE2_VARIABLE`; this run labels `KNOWN_GAP`
  (these 4 IDs are exactly `_KNOWN_GAPS`'s existing seeded entries,
  unmodified by this task). Same underlying REFUSAL outcome both runs.
- All 7 true Stage-1/fastpath `MATCH` rows and both `NON_RUNNABLE_BATCH`
  rows: identical label in both reports.

**Conclusion: zero deviations outside expected/documented Stage-2
variance semantics.** No row's actual behavior changed; only the
comparison report's independent labeling scheme differs, as that file's
own header already anticipated.

## Full pytest suite

```
3127 passed, 3 skipped, 1 warning in 90.32s
```

Exact match to the expected 3127/3/0 — zero delta, confirms
`golden_harness.py` is not imported by the pytest suite (as expected;
this module is a standalone `diagnostics/`-writing script, never
`test_*`-collected).

## Not committed

Per task instruction: q3's `MEASURE_FIRST_PENDING_RATIFICATION` ->
observed-`REFUSAL` ratification, AND the baseline-scorecard-supersession
decision (does `golden_scorecard_20260710_184703.md` become the new
frozen comparison baseline, given it's the first run where arudha_lagna
rows execute) both happen in design chat before any commit. Nothing in
`agent/eval/golden_harness.py`, `tests/fixtures/golden_qa_sulabh.py`, or
`calc_router.py` committed this task.

---

# Session 59 (cont. 5): fix sulabh_arudha_q2_stage2 question collision with sentinel test

ONE FILE: `tests/fixtures/golden_qa_sulabh.py`. Row `sulabh_arudha_q2_stage2`
only. Not committed — awaiting review.

## Why

`sulabh_arudha_q2_stage2`'s question `"what is my arudha lagna"` was a
verbatim collision with `tests/infra/test_orchestrator_arudha_lagna.py`'s
`_STAGE1_MISS_QUESTION` (same literal string, used in
`test_a2_single_keyword_phrasing_attempts_stage2_and_refuses`).
`golden_harness._used_stage2_since()` correlates
`diagnostics/calc_router_stage2.log` entries to golden rows by exact
question text; `_log_stage2_invocation` logs unconditionally, including
sentinel/pytest-fixture runs — so any pytest run of the sentinel test
would pollute this golden row's Stage-2-log correlation, violating the
harness docstring's stated uniqueness invariant.

## Edit applied

`question` changed from `"what is my arudha lagna"` to
`"tell me my arudha lagna"` — still exactly one `_ARUDHA_LAGNA_KEYWORDS`
hit (`"arudha lagna"`), so `_score_domain` still returns `1/3 = 0.333 <
0.4` floor, preserving the row's Stage-2-dependent design intent
unchanged. `baseline_answer_summary` appended with a sentence explaining
the rephrase and citing the collision it avoids.

## Verification

**1. New string uniqueness** — grepped `"tell me my arudha lagna"`
across `tests/`: exactly 1 hit, `tests/fixtures/golden_qa_sulabh.py:673`
(the edited row itself). Zero collisions.

**2. Collision-class check on the other 2 new rows (report only, no fix)**:
- `"what is my arudha lagna and public image"`
  (`sulabh_arudha_q1_stage1`) — **COLLIDES**. Same string as
  `test_orchestrator_arudha_lagna.py`'s `_STAGE1_CLEAN_QUESTION`
  (lines 21, 33, 66). This row is Stage-1-clean by design (score 0.667,
  never reaches Stage 2), so the harness's Stage-2-log correlation isn't
  triggered by this collision the way it was for q2 — but the literal
  question-text duplication across files still exists and violates the
  same invariant in spirit. Not fixed — awaiting ratification, since the
  task prompt scoped this run to `sulabh_arudha_q2_stage2` only.
- `"what does my upapada lagna say about my marriage"`
  (`sulabh_arudha_q3_refusal_probe`) — grepped `"upapada lagna"`
  (case-insensitive) across `tests/`: only 2 hits, both inside
  `golden_qa_sulabh.py` itself (the question string and the
  `baseline_answer_summary` prose that also mentions "Upapada Lagna").
  No collision with any other test file.

**Net: 1 of 3 new rows (q1_stage1) still has an unresolved collision.**
Flagging for a follow-up ratification/fix decision, not fixing
preemptively.

## Fixture import check

```
total rows: 21
duplicate questions within ledger: NONE
IMPORT_OK
```

No commit made — review pending.

---

# Session 59 (cont. 6): fix sulabh_arudha_q1_stage1 question collision with sentinel test

ONE FILE: `tests/fixtures/golden_qa_sulabh.py`. Row `sulabh_arudha_q1_stage1`
only. Not committed — awaiting review.

## Edit applied

`question` changed from `"what is my arudha lagna and public image"` to
`"what is my arudha pada and public perception"` — a verbatim collision
with `test_orchestrator_arudha_lagna.py`'s `_STAGE1_CLEAN_QUESTION`
constant. Inert today (Stage-1-clean phrasings never log to
`calc_router_stage2.log`, so no live misattribution currently occurs) but
violated the harness docstring's absolute uniqueness invariant and was a
live risk if future keyword tuning ever shifted this phrasing's routing.
Replacement was already measured in the same S59 sentinel run recorded in
that test file's own module docstring: 2 keyword hits (`"arudha pada"` +
`"public perception"`), score 0.667, Stage 1 clean, sentinel calls=0,
`TIER_1_EXACT` — equally ratified, no re-measurement needed.
`baseline_answer_summary` appended with a sentence explaining the
rephrase and citing the collision avoided.

## Verification

**1. New string grep across `tests/`** — NOT a clean zero-outside-row
result; flagging precisely rather than rounding up:

```
tests\infra\test_orchestrator_arudha_lagna.py:25:    "what is my arudha pada and public perception" -> score 0.667, sentinel
tests\fixtures\golden_qa_sulabh.py:648:        "question": "what is my arudha pada and public perception",
```

Line 25 is inside that file's MODULE DOCSTRING (lines 1-50) — part of
the prose table documenting all 5 candidate phrasings measured against
`route_question()` before any test was written (see that file's own
"MEASURE-FIRST FINDING" section). It is never assigned to a variable and
never passed to `route_question()`/any test call — the only LIVE
constant in that file is `_STAGE1_CLEAN_QUESTION = "what is my arudha "
"lagna and public image"` (line 66, unchanged, still distinct from the
new golden-row string). So this is inert docstring prose, not an
executable-string collision of the kind that broke q2 — but it is still
a literal text duplication across files. Not fixed (out of scope for a
golden-fixture-only edit; would require touching the test file).

**2. Fixture import + ledger-wide uniqueness**:

```
total rows: 21
duplicate questions within ledger: NONE
unique: True
IMPORT_OK
```

No commit made — review pending, including on the docstring-prose
duplication noted above.

---

# Session 59 (cont. 4): ratify David/Sheridan/Surbhi lord/co_lord_deciding_step + docs

Uncommented and pinned the 3 previously-print-only RATIFY assertion blocks
in `tests/infra/test_orchestrator_arudha_lagna.py`:

```
David:    lord="Mercury", co_lord_deciding_step=None
Sheridan: lord="Venus",   co_lord_deciding_step=None
Surbhi:   lord="Venus",   co_lord_deciding_step=None
```

Each pinned with an inline comment: "RATIFIED S59 (design-chat sign-off,
2026-07-10) -- derived live, cross-checked against S57 PVR counting
ratification." `_print_ratify_line()` helper removed (nothing else used
it once all 3 call sites became live assertions); the David test's own
docstring updated to drop its now-stale "print-only pending ratification"
line.

## CLAUDE.md updates

1. Added a carry-forward item: the arudha_lagna co-lord cascade
   (`strength.py`'s `stronger_co_lord()`) has zero real-chart coverage --
   none of the 4 canonical charts has a Scorpio/Aquarius Lagna. Flagged
   Session 57 in `test_chart_profile_arudha_lagna.py`'s DEVIATIONS #2;
   reconfirmed Session 59 at the orchestrator/e2e layer via this file's
   own 4-chart Layer B row (Sulabh=Sagittarius, Surbhi=Libra,
   Sheridan=Taurus, David=Virgo -- none co-lorded). Still deferred, no
   new reference chart being added; bundle unchanged.

   **Discrepancy flagged**: the task prompt asked to update a carry-forward
   item labeled "C4" for this gap. Grepped CLAUDE.md and SESSION_LOG.md for
   "C4" -- no existing item by that label exists (the only "C4" hit in
   either file is `mangal_dosha.py`'s unrelated cancellation-rule C4,
   "movable sign," excluded from V1 -- a different C4 entirely). Added the
   co-lord-cascade item fresh instead of guessing which existing line was
   meant, with a note in CLAUDE.md itself.

2. Added a second carry-forward item: `answer_question()` has no Stage 2
   client injection seam (unlike `route_question()`'s own `_stage2_client`
   kwarg) -- `test_orchestrator_arudha_lagna.py`'s Layer C test had to
   monkeypatch `calc_router._stage2_classify` directly instead. Bundled
   with the existing `RouteResult.route` marker carry-forward for a future
   joint decision.

## pytest full suite

`3127 passed, 3 skipped, 1 warning in 72.50s` -- exact match to the
expected 3127/3/0 with the 3 ratified assertions now live (no delta from
the prior print-only run).

Golden harness skipped per instruction (no source file touched, docs +
test-file assertions only).

Commit: `S59: orchestrator e2e test suite for arudha_lagna (7 tests,
4-chart ratified oracle; Stage-1-unreachable behavior pinned)` -- hash
`b4be25a`. Pushed to `main`.

---

# Session 59 (cont. 3): new test file test_orchestrator_arudha_lagna.py — router-provenance + e2e oracle

ONE FILE (new): `tests/infra/test_orchestrator_arudha_lagna.py`. No source
files touched. Not committed — user reviews + ratifies first.

## Pre-edit step 1: exact `_score_domain` formula (read, not assumed)

`agent/infra/calc_router.py:415-422`:

```python
def _score_domain(question_tokens: list[str], keywords: tuple[str, ...]) -> float:
    """Saturating score: min(matched_keywords, 3) / 3. ..."""
    matched = sum(1 for kw in keywords if _keyword_hits(kw, question_tokens))
    return min(matched, 3) / 3
```

Confirmed: the denominator is a FIXED 3 (saturating cap), NOT
`len(keywords)`. `arudha_lagna`'s own `_ARUDHA_LAGNA_KEYWORDS` has 4
entries (`"arudha lagna"`, `"arudha pada"`, `"public image"`,
`"public perception"`) — a single-keyword hit always scores `1/3 = 0.333`
regardless of that list's length, matching the log's observed 0.333
exactly. `_CONFIDENCE_FLOOR = 0.4` — so 1 match never clears Stage 1; 2
matches score `2/3 = 0.667`, clearing both the floor and the
`_CONFIDENCE_MARGIN = 0.15` gap against every other domain's 0.0 for these
phrasings.

## Pre-edit step 2: MEASURE-FIRST candidate phrasings (recording sentinel)

Ran `route_question()` directly against a recording sentinel client
(records the call in `.calls`, then raises `RuntimeError` — never returns a
canned response) for 5 candidate phrasings, BEFORE writing any test:

```
Q: 'what is my arudha lagna and public image'
  all scores: {'marriage_compatibility': 0.0, 'career_strength': 0.0, 'current_dasha': 0.0, 'av_transit': 0.0, 'arudha_lagna': 0.6667}
  best=arudha_lagna score=0.6667 second=0.0000 margin=0.6667
  sentinel invoked: False (calls=0)
  route_question result: domain=arudha_lagna tier=AnswerTier.TIER_1_EXACT

Q: 'arudha lagna public image'
  all scores: {..., 'arudha_lagna': 0.6667}
  sentinel invoked: False (calls=0)
  route_question result: domain=arudha_lagna tier=AnswerTier.TIER_1_EXACT

Q: 'what is my arudha lagna'
  all scores: {..., 'arudha_lagna': 0.3333}
  sentinel invoked: True (calls=1)
  route_question result: domain=None tier=AnswerTier.REFUSAL

Q: 'how do people see me in public'
  all scores: {..., 'arudha_lagna': 0.0}  (best=marriage_compatibility, all 0.0)
  sentinel invoked: True (calls=1)
  route_question result: domain=None tier=AnswerTier.REFUSAL

Q: 'what is my arudha pada and public perception'
  all scores: {..., 'arudha_lagna': 0.6667}
  sentinel invoked: False (calls=0)
  route_question result: domain=arudha_lagna tier=AnswerTier.TIER_1_EXACT
```

3 of 5 phrasings clear Stage 1 alone (2 keyword hits each); the other 2
score 0.333/0.0 and fall through to a Stage-2 attempt that fails closed
(sentinel raises, `_stage2_fallback`'s `except Exception` converts it to
REFUSAL). Full `RouteResult` for the chosen Stage-1-clean phrasing
(`"what is my arudha lagna and public image"`):

```
RouteResult(domain='arudha_lagna', tier=<AnswerTier.TIER_1_EXACT: 'TIER_1_EXACT'>, confidence=0.6666666666666666, demotion_reason=None, requires_partner=False)
calls: []
```

Selected this phrasing (over the shorter `"arudha lagna public image"`)
because it reads as an actual question, matching
`test_orchestrator_e2e.py`'s existing full-question convention.

## Pre-edit step 3: `route_question` signature confirmation

`agent/infra/calc_router.py:751-757`:

```python
def route_question(
    question: str,
    has_partner_data: bool = False,
    *,
    chart_data: dict | None = None,
    _stage2_client: object | None = None,
) -> RouteResult:
```

Confirmed the injection kwarg is `_stage2_client`, threaded into
`_stage2_classify(question, client=client)` only inside `_stage2_fallback`
— matches `tests/infra/test_calc_router_stage2.py`'s own usage.

IMPORTANT divergence caught before writing Layer C: `agent/infra/
orchestrator.py`'s `answer_question()` signature does NOT accept or thread
a `_stage2_client` kwarg through to `route_question()` at all. So Layer C's
"recording sentinel" cannot use that seam — the correct seam (confirmed by
reading, not assumed) is monkeypatching `calc_router._stage2_classify`
itself, the module-level function `_stage2_fallback` calls internally. Used
that instead for Layer C only; Layer A (direct `route_question()` calls)
uses the real `_stage2_client` kwarg.

## Pre-edit step 4: fixture/prompt-verification conventions

Read `tests/infra/test_orchestrator_e2e.py` (module-scoped
`calculate_chart()` fixture per reference chart, standalone test function
per chart) and `tests/infra/test_chart_profile_arudha_lagna.py` (measure-
first ratify pattern: print `"RATIFY BEFORE COMMIT -- {chart}: ..."`,
assert only what's independently verified, leave the rest commented).
Mirrored both in the new file.

Also verified the task prompt's claimed ratified `arudha_sign` values
against a live run of `build_arudha_lagna_profile()` BEFORE writing any
assertion (per CLAUDE.md's "verify task prompts against code" memory) --
all 3 confirmed exact:

```
Sulabh   {'arudha_sign': 'Leo', 'lagna_sign': 'Sagittarius', 'lord': 'Jupiter', 'co_lord_deciding_step': None, ...}
Surbhi   {'arudha_sign': 'Leo', 'lagna_sign': 'Libra', 'lord': 'Venus', 'co_lord_deciding_step': None, ...}
Sheridan {'arudha_sign': 'Aquarius', 'lagna_sign': 'Taurus', 'lord': 'Venus', 'co_lord_deciding_step': None, ...}
David    {'arudha_sign': 'Taurus', 'lagna_sign': 'Virgo', 'lord': 'Mercury', 'co_lord_deciding_step': None, ...}
```

David=Taurus, Sheridan=Aquarius, Surbhi=Leo all matched the prompt exactly
-- no correction needed.

## New file: `tests/infra/test_orchestrator_arudha_lagna.py` (7 tests)

**Layer A (router provenance, `route_question()` in isolation):**
- `test_a1_stage1_clean_phrasing_never_touches_stage2` — Stage-1-clean
  phrasing + recording sentinel -> `domain=arudha_lagna`,
  `TIER_1_EXACT`, `demotion_reason=None`, `requires_partner=False`,
  sentinel `.calls == []`.
- `test_a2_single_keyword_phrasing_attempts_stage2_and_refuses` —
  `"what is my arudha lagna"` + recording sentinel -> sentinel invoked
  (`len(calls) == 1`), `domain=None`, `tier=REFUSAL`. Docstring explicitly
  states this pins CURRENT behavior (CLAUDE.md carry-forward, 2026-07-10),
  not desired behavior, and that a future scorecard-gated tuning should
  flip it deliberately.

**Layer B (chart_profile.build_domain_profile -> result_formatter.
format_answer, router bypassed, no LLM):**
- Sulabh: FULL assert — exact `answer_payload` dict match, exact 4-key
  set (pins no tier/sources meta-key leakage from chart_profile.py's
  documented payload passthrough), `TIER_1_EXACT`, `demotion_reason=None`,
  `uncertainty_days=0.0`, `sources=("padas.py",)`.
- David (hardest case, tested first among the 3 partial rows): assert
  `arudha_sign="Taurus"` only; `lord`/`co_lord_deciding_step` printed via
  `RATIFY BEFORE COMMIT` line, assertions commented out.
- Sheridan: assert `arudha_sign="Aquarius"` only, same RATIFY treatment.
- Surbhi: assert `arudha_sign="Leo"` only, same RATIFY treatment.

**Layer C (full chain, `answer_question()`, Sulabh, Stage-1-clean
phrasing):**
- `test_sulabh_full_chain_matches_layer_b` — monkeypatches
  `calc_router._stage2_classify` with a spy that records + raises;
  asserts it's never called, then asserts the full `DomainAnswer` is
  `==` to Layer B's independently-built Sulabh row byte-for-byte —
  pins `_merge_router_demotion`'s no-op passthrough for this domain.

## Test run (`-s`) output

```
tests/infra/test_orchestrator_arudha_lagna.py::TestLayerARouterProvenance::test_a1_stage1_clean_phrasing_never_touches_stage2 PASSED
tests/infra/test_orchestrator_arudha_lagna.py::TestLayerARouterProvenance::test_a2_single_keyword_phrasing_attempts_stage2_and_refuses PASSED
tests/infra/test_orchestrator_arudha_lagna.py::TestLayerBRealChartOracle::test_sulabh_full_assert PASSED
tests/infra/test_orchestrator_arudha_lagna.py::TestLayerBRealChartOracle::test_david_arudha_sign_ratified RATIFY BEFORE COMMIT -- David: lord='Mercury' co_lord_deciding_step=None
PASSED
tests/infra/test_orchestrator_arudha_lagna.py::TestLayerBRealChartOracle::test_sheridan_arudha_sign_ratified RATIFY BEFORE COMMIT -- Sheridan: lord='Venus' co_lord_deciding_step=None
PASSED
tests/infra/test_orchestrator_arudha_lagna.py::TestLayerBRealChartOracle::test_surbhi_arudha_sign_ratified RATIFY BEFORE COMMIT -- Surbhi: lord='Venus' co_lord_deciding_step=None
PASSED
tests/infra/test_orchestrator_arudha_lagna.py::TestLayerCFullChain::test_sulabh_full_chain_matches_layer_b PASSED

[_patch_stage2_openai] stub invocation count: 0
7 passed in 1.03s
```

Stub invocation count 0 confirms no test in this file reaches the real
(stubbed) Stage 2 path -- consistent with Layer A/C's own sentinel
evidence.

**RATIFY BEFORE COMMIT lines, for your review:**
- David: `lord='Mercury'`, `co_lord_deciding_step=None`
- Sheridan: `lord='Venus'`, `co_lord_deciding_step=None`
- Surbhi: `lord='Venus'`, `co_lord_deciding_step=None`

## pytest full suite

`3127 passed, 3 skipped, 1 warning in 75.67s` — exactly the expected
3120 + 7 new, 3 skipped, 0 failed.

## Golden harness

`runnable=16 non_runnable_batch=2 match=7 match_stage2=5 design_debt=0
known_gap=4 new_gap=0 error=0` — new report
`diagnostics/golden_scorecard_20260710_181527.md`. Diffed against the
immediately-prior scorecard
(`diagnostics/golden_scorecard_20260710_175732.md`): only the
`evaluated_at_jd` timestamp differs. Zero rows moved.

Not committed — new test file only, no source files touched; awaiting
ratification of the 3 RATIFY lines above before any commit.

---

# Session 59 (cont. 2): arudha_lagna admitted into orchestrator._VALID_DOMAINS — last gate

Scope: ONE FILE, `agent/infra/orchestrator.py` — admit `"arudha_lagna"` into
`_VALID_DOMAINS`. Not committed — user reviews diffs first. This closes the
arudha_lagna staged rollout: router (S58) + formatter (S59) + chart_profile
dispatch/`_VALID_DOMAINS` (S59) were already live; this was the last gate.

## Pre-edit review

Read `orchestrator.py` end-to-end. Located `_VALID_DOMAINS` and its
`SENSITIVE_TO` comment block documenting the Session 55 av_transit incident
(chart_profile.py's own gate was missed for a full session after
orchestrator.py's gate shipped). Grepped `tests/` for any test asserting
`answer_question()` raises on `"arudha_lagna"`, asserting `_VALID_DOMAINS`'
exact contents/length, or asserting the "unrecognized domain" ValueError
message listing exactly 5 domains — no matches found (only
`test_chart_profile_arudha_lagna.py`, which exercises
`build_arudha_lagna_profile()` directly, never the orchestrator). Clear to
proceed.

## Edit applied (single)

`_VALID_DOMAINS` += `"arudha_lagna"`, with a comment stating: added S59,
closes the av_transit-precedent staged rollout (router S58 -> formatter S59
-> chart_profile S59 -> this gate); SENSITIVE_TO chart_profile.py's own
`_VALID_DOMAINS` (both now list the same 6 domains — keep in sync by hand,
per the existing incident note above); and that `_merge_router_demotion()`
needs NO change (calc_router.py emits `demotion_reason=None` for
arudha_lagna and the formatter's `_format_arudha_lagna()` branch also sets
`None`, so the merge is a no-op passthrough — confirmed by reading, not
preemptively wired).

```diff
 _VALID_DOMAINS = {
     "marriage_compatibility",
     "career_strength",
     "current_dasha",
     "sade_sati",
     "av_transit",
+    "arudha_lagna",
 }
+# "arudha_lagna" added Session 59 -- closes the av_transit-precedent staged
+# rollout (router S58 -> formatter S59 -> chart_profile.py's own dispatch/
+# _VALID_DOMAINS S59 -> this gate, the last one). SENSITIVE_TO
+# chart_profile.py's own _VALID_DOMAINS constant (see incident note above):
+# both now list the same 6 domains -- keep in sync by hand.
+#
+# _merge_router_demotion() needs NO change for this domain: calc_router.py
+# emits demotion_reason=None for arudha_lagna and result_formatter.py's
+# _format_arudha_lagna() branch also sets demotion_reason=None (payload-
+# property principle, same as current_dasha/sade_sati/av_transit), so the
+# merge below is a no-op passthrough -- not preemptively wiring anything.
```

No other lines in the file touched (the older "DEMOTION LOCK (Session 55,
av_transit)" comment block further down and the `transit_planet` docstring
prose still read as av_transit-specific — left alone, out of scope for a
one-edit prompt).

## Live E2E smoke (first reachable execution of the full chain)

Ran directly against `agent.infra.orchestrator.answer_question()` with the
real Sulabh chart (6 Apr 1988, 00:30, Calcutta) — no mocks.

> **CORRECTION (post-review):** the original version of this section
> claimed both (a) and (b) resolved via Stage 1 keyword scoring. That
> claim was **wrong** and is corrected below after reading
> `diagnostics/calc_router_stage2.log` directly. Both questions actually
> routed through **Stage 2** (the GPT-4o-mini LLM classifier), not Stage
> 1. Verbatim log lines, `diagnostics/calc_router_stage2.log`:
>
> ```
> {"timestamp": "2026-07-10T17:55:44.464274+00:00", "question": "what is my arudha lagna", "stage1_best_score": 0.3333333333333333, "stage1_margin": 0.3333333333333333, "stage2_domain": "arudha_lagna", "stage2_confidence": "high", "outcome": "ROUTED:arudha_lagna"}
> {"timestamp": "2026-07-10T17:55:45.598533+00:00", "question": "how do people see me in public", "stage1_best_score": 0.0, "stage1_margin": 0.0, "stage2_domain": "arudha_lagna", "stage2_confidence": "high", "outcome": "ROUTED:arudha_lagna"}
> ```

**(a) `"what is my arudha lagna"`** — result payload matches expectation
exactly, but the ROUTE was via Stage 2, not Stage 1: `stage1_best_score`
0.333 (a single keyword hit — the literal domain name still falls below
calc_router.py's 0.4 confidence floor per the S44 refuse-heavy posture),
`stage2_domain="arudha_lagna"`, `stage2_confidence="high"` ->
`ROUTED:arudha_lagna`.
- `domain`: `arudha_lagna`
- `tier`: `AnswerTier.TIER_1_EXACT`
- `answer_payload`: `{'arudha_sign': 'Leo', 'lagna_sign': 'Sagittarius', 'lord': 'Jupiter', 'co_lord_deciding_step': None}`
- `demotion_reason`: `None`
- (also observed: `stub_caveats=()`, `uncertainty_virupa=0.0`, `uncertainty_days=0.0`, `sources=('padas.py',)`)

**(b) `"how do people see me in public"`** — reported verbatim, NOT tuned:
this scored `stage1_best_score=0.0` (a complete Stage 1 miss, zero keyword
hits — not a Stage 1 match as originally misreported), fell through to
Stage 2, and the LLM classifier resolved it to
`stage2_domain="arudha_lagna"` at `stage2_confidence="high"` ->
`ROUTED:arudha_lagna`, same payload as (a), `demotion_reason=None`. Router
posture (refuse-heavy, S44 lock) not touched; this is a report only, no
keyword/threshold changes made — but see the new CLAUDE.md carry-forward
below: for arudha_lagna specifically, Stage 1 is currently unreachable even
on the best-case single-keyword question, so *every* live route to this
domain is a Stage 2 LLM call.

**(c) `"what is my current dasha"`** — zero behavior change confirmed:
`domain=current_dasha`, `tier=AnswerTier.TIER_2_RANGE` (router-demoted for
the ±37-day Antardasha-drift caveat, pre-existing behavior, unrelated to
this edit), full mahadasha/antardasha/timing_enrichment payload present,
`demotion_reason="Antardasha boundaries carry ±37-day drift vs AstroSage;
the current lord itself is reliable, but any date given for its start/end
should be treated as approximate"` — identical shape/content to what this
domain has always returned; `_VALID_DOMAINS` widening does not perturb any
other domain's dispatch.

## pytest full suite

`3120 passed, 3 skipped, 1 warning in 74.59s` — exact match to the expected
3120/3/0, no flips.

## Golden harness

Ran `python -m agent.eval.golden_harness`:
`runnable=16 non_runnable_batch=2 match=7 match_stage2=5 design_debt=0
known_gap=4 new_gap=0 error=0` — new report
`diagnostics/golden_scorecard_20260710_175732.md`.

Diffed against the immediately-prior scorecard
(`diagnostics/golden_scorecard_20260710_170315.md`, generated during the
earlier S59 chart_profile-dispatch task this session): the ONLY diff line
is the `evaluated_at_jd` run timestamp. Zero rows moved category —
confirms the S58-observed "no golden row routes to arudha_lagna" holds
after this gate opened too.

Commit: `S59: orchestrator _VALID_DOMAINS admits arudha_lagna -- domain
live e2e; smoke provenance corrected (both routes were Stage 2)` -- hash
`919eb4a`. Pushed to `main`.

---

# Session 59 (cont.): arudha_lagna wired into build_domain_profile() dispatch

Scope: ONE FILE, `agent/infra/chart_profile.py` — widen `_VALID_DOMAINS` and
add the `build_domain_profile()` dispatch branch for `"arudha_lagna"`. Not
committed — user reviews diffs first.

## Pre-edit review

Read `build_domain_profile()` end-to-end and this file's own
`_VALID_DOMAINS` constant. Confirmed the Session 55 incident this task
warned about: `orchestrator.py`'s own `SENSITIVE_TO` comment documents that
`chart_profile.py`'s gate was once missed when av_transit shipped
elsewhere, leaving its builder branch dead for a full session before being
caught (fix-forward, commit 4e52e77). This prompt widens `_VALID_DOMAINS`
in the SAME change as the dispatch branch, avoiding a repeat.
`orchestrator.py`'s own `_VALID_DOMAINS` is deliberately NOT touched — a
separate, later prompt, same staged precedent.

Also checked existing tests before editing: `tests/infra/
test_chart_profile_arudha_lagna.py` only exercises `build_arudha_lagna_
profile()` directly, never `build_domain_profile()` — no test asserts
`build_domain_profile` REFUSES/raises on `"arudha_lagna"` via the old gate.
Low regression risk confirmed before editing, not just hoped.

## 4 edits applied

1. **`_VALID_DOMAINS`** += `"arudha_lagna"`, with a comment documenting
   that `build_domain_profile()`'s dispatch branch lands in the same
   change (avoiding the exact av_transit incident) and that
   `orchestrator.py`'s own `_VALID_DOMAINS` sync is a separate, later
   prompt.
2. **`build_domain_profile()`** gains an `elif domain == "arudha_lagna":`
   branch (added before the final `else: # sade_sati` catch-all, which
   otherwise would have silently absorbed `"arudha_lagna"` once it passed
   the top-of-function `_VALID_DOMAINS` check — sade_sati's branch is
   implemented as an unconditional `else`, not its own explicit `elif`,
   so a new domain MUST get its own `elif` before that `else` or it would
   be silently misrouted through the sade_sati path):
   - `payload = build_arudha_lagna_profile(chart_data)`
   - `stub_caveats = ()` — mirrors sade_sati's own no-stub convention.
   - `uncertainty_virupa = 0.0` — mirrors sade_sati.
   - `uncertainty_days = 0.0` — literal, with the exact comment text the
     task specified ("RATIFIED S59 — formatter's `_format_arudha_lagna`
     also asserts 0.0 as a hardcoded contract assertion...").
   - Comment noting `evaluated_at_jd` is accepted but genuinely unused
     (Arudha Lagna is purely natal), same precedent as av_transit's own
     unused-instant case documented just above it.
3. **Payload passthrough — reported, not decided**: `build_arudha_lagna_
   profile()`'s return dict includes `"tier"`/`"sources"` keys that
   `DomainChartProfile.payload` doesn't need (tier is domain-derived by
   the formatter, not carried on the profile; sources is a
   `result_formatter.py`-local hardcoded literal, confirmed in the prior
   session's work — `_format_arudha_lagna()` already ignores
   `payload["sources"]`). Checked every existing branch: none of them has
   ever faced this situation — marriage_compatibility/career_strength/
   current_dasha/sade_sati all assemble `payload` inline as exact-keys
   dict literals, and av_transit's `_build_av_timing_block()` helper
   already returns exactly the render-needed keys. **No existing
   "strip meta keys" convention exists.** Per the task's own fallback
   instruction, passed `build_arudha_lagna_profile(chart_data)`'s return
   value through to `payload` UNMODIFIED, with an inline comment flagging
   this explicitly (in case a future exhaustiveness test inspects
   `payload`'s key set and is surprised by the extra 2 keys).
4. **`build_arudha_lagna_profile()`'s docstring**: removed the "NOT yet
   wired into build_domain_profile()/_VALID_DOMAINS/the router or
   formatter" clause (now false — router, formatter, and this file's own
   dispatch are all wired as of Sessions 58-59). Replaced with an accurate
   statement of what's actually still pending: only
   `orchestrator.py`'s `_VALID_DOMAINS` sync, which fails closed via
   `answer_question()`'s defensive `ValueError` until it lands.

Also updated (not separately numbered, but load-bearing for docstring
accuracy): `build_domain_profile()`'s own `Args`/`Raises` docstring
sections now list `"arudha_lagna"` alongside the other 5 domains, document
its `ValueError`/`RuntimeError` failure modes (propagated unmodified from
`build_arudha_lagna_profile()`), and note `evaluated_at_jd` is accepted but
unused for this domain — matching this file's existing convention of
documenting every domain's specific behavior in that shared docstring.

## Diff

```diff
--- a/agent/infra/chart_profile.py
+++ b/agent/infra/chart_profile.py
@@ -68,6 +68,16 @@ _VALID_DOMAINS = {
     # gate was widened to admit it -- fix-forward, Session 55 continued:
     # the branch was unreachable dead code until this entry was added.
     "av_transit",
+    # arudha_lagna (Session 59): this entry lands in the SAME change as
+    # build_domain_profile()'s own arudha_lagna dispatch branch below --
+    # deliberately avoiding a repeat of the exact av_transit incident
+    # documented above. orchestrator.py's own _VALID_DOMAINS does NOT yet
+    # admit "arudha_lagna" -- that sync is a separate, later prompt (same
+    # staged-rollout precedent as av_transit's router-then-orchestrator
+    # split); until it lands, a live "arudha_lagna" route fails closed via
+    # orchestrator.answer_question()'s own defensive ValueError, not a
+    # silent misroute.
+    "arudha_lagna",
 }

 # career_strength's compute_bhava_bala_totals() call needs planet_lons
@@ -438,7 +448,7 @@ def build_domain_profile(

     Args:
         domain: one of "marriage_compatibility", "career_strength",
-            "current_dasha", "sade_sati", "av_transit".
+            "current_dasha", "sade_sati", "av_transit", "arudha_lagna".
         chart_data: calculate_chart() output for the primary native.
         evaluated_at_jd: JD (UT) instant this profile is evaluated as-of.
             Caller-supplied, not sampled here -- must be the SAME instant the
@@ -453,7 +463,12 @@ def build_domain_profile(
             instant is NOT used directly (the scan window is the current
             Antardasha envelope, read from chart_data["dasha"] -- see below);
             it is accepted uniformly across all domains but genuinely unused
-            by this branch.
+            by this branch. For domain="arudha_lagna", this instant is ALSO
+            not used -- Arudha Lagna is a purely natal calculation (birth
+            longitudes only, via build_arudha_lagna_profile()) with no
+            "as-of a different moment" concept of its own, same
+            accepted-uniformly-but-unused precedent as av_transit's case
+            just above.
         partner_chart_data: calculate_chart() output for the second native.
             Required (and only accepted) for domain="marriage_compatibility" --
             Ashtakoot (compute_ashtakoot_compatibility) needs two natives.
@@ -477,12 +492,18 @@ def build_domain_profile(
             the Mahadasha envelope is never silently substituted); or
             transit_planet outside {Saturn, Jupiter, Sun, Mars} (propagated
             unwrapped from av_transit_scanner.scan_av_transit_segments()'s
-            own validation -- not duplicated here).
+            own validation -- not duplicated here); or, for arudha_lagna,
+            a non-canonical lagna_sign or a Scorpio/Aquarius D2 (both
+            co-lords resident)/D6 (exact Step-5(b) tie) fail-closed case,
+            propagated UNMODIFIED from build_arudha_lagna_profile() ->
+            compute_bhava_padas() (not caught or reinterpreted here,
+            matching that function's own documented precedent).
         RuntimeError: a wrapped, module-named failure from any underlying
             calculation call (ashtakoot, mangal_dosha, shadbala_totals,
             compute_porphyry_house_cusps, bhava_bala_totals, sade_sati.
-            compute_sade_sati, ashtakavarga natal-table assembly, or the
-            Moon-longitude ephemeris bridge).
+            compute_sade_sati, ashtakavarga natal-table assembly, the
+            Moon-longitude ephemeris bridge, or arudha_lagna's own planet-
+            longitude ephemeris bridge inside build_arudha_lagna_profile()).
     """
     if domain not in _VALID_DOMAINS:
         raise ValueError(f"domain must be one of {sorted(_VALID_DOMAINS)}, got {domain!r}")
@@ -746,6 +767,41 @@ def build_domain_profile(
         # inherits that same documented drift envelope.
         uncertainty_days = 37.0

+    elif domain == "arudha_lagna":
+        # Session 59: build_arudha_lagna_profile() is a purely natal
+        # calculation (see this function's own evaluated_at_jd Args note
+        # above) -- chart_data only, no evaluated_at_jd argument. Mirrors
+        # sade_sati's own T1, no-stub, no-virupa-envelope convention below
+        # (this domain's payload carries no dated claims, same "tier =
+        # payload property" reasoning documented in the module docstring).
+        #
+        # PAYLOAD PASSTHROUGH (flagged, not silently decided): the returned
+        # dict is assigned to `payload` UNMODIFIED, including its "tier"/
+        # "sources" keys -- keys DomainChartProfile.payload does not need
+        # (tier is decided by the router/formatter from `domain`, not
+        # carried on the profile; sources is a result_formatter.py-local
+        # hardcoded literal per _format_arudha_lagna(), which already
+        # ignores payload["sources"]). No existing branch in this file has
+        # ever faced this situation: every other domain's payload is either
+        # assembled inline as an exact-keys dict literal (marriage_
+        # compatibility/career_strength/current_dasha/sade_sati) or comes
+        # from a helper (_build_av_timing_block()) whose return contract is
+        # already exactly the render-needed keys -- so there is no existing
+        # "strip meta keys" convention to follow here. Passing the extra
+        # keys through unmodified is harmless (result_formatter.py's
+        # _format_arudha_lagna() reads only the 4 keys it needs by name,
+        # direct-indexed) but is called out here rather than silently
+        # stripped, in case a future caller ever inspects payload's key set
+        # directly (e.g. an exhaustiveness test) and is surprised by it.
+        payload = build_arudha_lagna_profile(chart_data)
+        stub_caveats = ()
+        uncertainty_virupa = 0.0
+        # RATIFIED S59 -- formatter's _format_arudha_lagna also asserts 0.0
+        # as a hardcoded contract assertion (payload structurally has no
+        # dated claims); both literals intentional, neither is the other's
+        # source.
+        uncertainty_days = 0.0
+
     else:  # sade_sati (Session 50/P7.2a) -- NO mahadasha/antardasha fields
         # here; this is a payload-property-consistent T1 sub-path, distinct
         # from current_dasha's always-T2 payload (module docstring above).
@@ -815,10 +871,15 @@ def build_arudha_lagna_profile(chart_data: dict) -> dict:
     """Bridge calculate_chart() output -> the Arudha Lagna (AL, house 1)
     entry of jaimini.padas.compute_bhava_padas()'s 12-house result.

-    Standalone builder, NOT yet wired into build_domain_profile()/
-    _VALID_DOMAINS/the router or formatter -- this function only assembles
-    the AL-specific payload; domain/router/formatter integration is a
-    separate, later prompt.
+    Wired into build_domain_profile()'s "arudha_lagna" branch and this
+    file's own _VALID_DOMAINS as of Session 59 (calc_router.py's Stage 1/
+    Stage 2/route branch already landed Session 58; result_formatter.py's
+    _format_arudha_lagna() already landed Session 59). orchestrator.py's
+    own _VALID_DOMAINS does NOT yet admit "arudha_lagna" -- that sync is a
+    separate, later prompt, same staged-rollout precedent as av_transit's
+    router-then-orchestrator split; until it lands, a live "arudha_lagna"
+    route fails closed via orchestrator.answer_question()'s own defensive
+    ValueError, not a silent misroute.

     lagna_sign comes from chart_data["lagna_chart"]["rasi"] (whole-sign
     house 1, same field _koota_natal_info_from_chart already reads for
```

## pytest (full suite)

```
3120 passed, 3 skipped, 1 warning in 75.25s
```

Exact match — zero test flips. Confirmed low-risk before editing: no existing
test asserted `build_domain_profile()` REFUSES on `"arudha_lagna"` via the
old gate.

## Golden harness delta

```
runnable=16 non_runnable_batch=2 match=7 match_stage2=5 design_debt=0 known_gap=4 new_gap=0 error=0
report: diagnostics\golden_scorecard_20260710_170315.md
```

Baseline verification (CLAUDE.md rule #12): confirmed
`golden_scorecard_20260710_164208.md` was the most recent scorecard by
mtime before diffing.

```
$ diff diagnostics/golden_scorecard_20260710_164208.md diagnostics/golden_scorecard_20260710_170315.md
3c3
< - Run evaluated_at_jd: `2461232.1957523148`
---
> - Run evaluated_at_jd: `2461232.2104282407`
```

**Zero delta** beyond the run timestamp, as expected: the router already
routes `arudha_lagna` questions (Session 58), and `orchestrator.py`'s
`_VALID_DOMAINS` still rejects the domain — fail-closed behavior is
unchanged, no golden row's outcome moves.

## Live smoke check beyond pytest (not requested, done anyway — this is the
first point the builder->formatter chain can execute together)

```python
chart = calculate_chart("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")
profile = build_domain_profile("arudha_lagna", chart, jd)
# profile.payload == {'arudha_sign': 'Leo', 'lagna_sign': 'Sagittarius',
#                      'lord': 'Jupiter', 'co_lord_deciding_step': None,
#                      'tier': 'TIER_1_EXACT', 'sources': ('padas.py',)}
# profile.stub_caveats == (); uncertainty_virupa == 0.0; uncertainty_days == 0.0

answer = format_answer(profile)
# answer.tier == TIER_1_EXACT; answer.answer_payload == {'arudha_sign': 'Leo',
#   'lagna_sign': 'Sagittarius', 'lord': 'Jupiter', 'co_lord_deciding_step': None}
# (the extra tier/sources keys from build_arudha_lagna_profile() are present
# on profile.payload but correctly NOT echoed into answer_payload -- confirms
# the "formatter ignores the extra keys" claim in the payload-passthrough
# comment above is actually true, not just asserted)

answer_question("what is my arudha lagna public image", chart)
# -> ValueError: "answer_question: router returned unrecognized domain
#    'arudha_lagna' outside the routable whitelist ['av_transit',
#    'career_strength', 'current_dasha', 'marriage_compatibility',
#    'sade_sati']"
# Confirms the intended end state exactly: router routes it, builder/
# formatter can now fully answer it, orchestrator still fails closed
# until its own _VALID_DOMAINS sync lands (separate, later prompt).
```

## Not touched (deliberately out of scope this session)

- `orchestrator.py`'s own `_VALID_DOMAINS` — explicitly the next, separate
  prompt per this task's own staged-rollout instruction.
- Module-level docstring at the top of `chart_profile.py` ("Covers the 3
  domains locked for the pipeline checkpoint... Plus sade_sati...") does
  not mention av_transit OR arudha_lagna — this staleness predates this
  session (av_transit was never added to that top docstring either) and
  is out of scope for a one-file, dispatch-only prompt; flagged here, not
  fixed.

Not committed — diff above for review. No test file changes this session.

## Follow-up: doc-only fixes (chart_profile.py) + commit

Two stale-docstring fixes, `agent/infra/chart_profile.py` only, no logic
changed:

1. `build_arudha_lagna_profile()`'s docstring claimed `lagna_sign` comes
   from `chart_data["lagna_chart"]["rasi"]` -- verified against the actual
   code (line 932) before writing anything: the real call reads
   `chart_data["lagna_chart"]["ascendant"]`, with an existing inline
   comment (lines 930-931) already explaining `"rasi"` holds the MOON sign
   in that dict, not the Lagna sign. Docstring corrected to match, with an
   explicit "do not regress into the Session 58 lagna-key bug" clause
   (git history: commit `83cae16`, "fix lagna key: ascendant, not rasi",
   part of the Session 58 arudha_lagna profile-builder work).
2. Module top docstring's "Covers the 3 domains..." sentence was flagged
   stale in the prior entry above (never mentioned av_transit or
   arudha_lagna at all, predating this session). Updated to state "Covers
   6 domains as of Session 59" and added a sentence each for av_transit
   and arudha_lagna, matching this file's own convention of documenting
   each domain addition.

Also added to `CLAUDE.md` Carry-Forward: arudha_lagna's payload passes
through meta keys `tier`/`sources` unreconciled -- flagged for whenever
the next Jaimini domain lands (dual tier representation risk: `payload["tier"]`
as a string literal vs. `DomainAnswer.tier`'s `AnswerTier` enum, currently
harmless only because `_format_arudha_lagna()` ignores the payload key).

pytest re-run after both doc fixes: `3120 passed, 3 skipped, 1 warning in
91.19s` -- exact match, confirms doc-only. Golden harness skipped per
instruction (no code path touched).

Commit: `S59: arudha_lagna wired into build_domain_profile dispatch +
chart_profile _VALID_DOMAINS (orchestrator sync pending)` -- hash
`2226691`.
