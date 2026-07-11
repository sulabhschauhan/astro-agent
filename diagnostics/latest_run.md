# golden_harness.py switchover: DomainAnswer.route direct read

Closes the CLAUDE.md carry-forward's second half ("switch the harness
to read it directly") once `RouteResult.route` (agent/infra/
calc_router.py) and its orchestrator-stamped copy `DomainAnswer.route`
(agent/infra/chart_profile.py, stamped by orchestrator.py's
answer_question() on both return paths) existed and were pushed.

## Enumerated changes (agent/eval/golden_harness.py)

1. **Success-path route determination** (`_run_runnable_row()`):
   replaced the correlation -> sade_sati-fastpath-inference ->
   stage1-default block with a direct `route = result.route` read.
   Guarded: `result.route is None` raises `RuntimeError` naming the row
   id -- an un-stamped DomainAnswer reaching the harness is an upstream
   orchestrator/formatter bug, never silently defaulted.
2. **ERROR path**: kept `_used_stage2_since()` log correlation --
   `answer_question()` raised before returning any `DomainAnswer`, so
   there is no `route` field to read. Comment added explaining this is
   the correlation's sole surviving use.
3. **`_render_report()`'s deterministic-floor split**: `"pre_classification"`
   (calc_router.py's pre-scoring unbuilt-module/out-of-scope REFUSAL
   checks -- deterministic keyword matching, no LLM) now counts with
   `stage1`/`fastpath` in `deterministic_floor_ids`, not the stage2-routed
   set. `RowResult.route`'s type comment updated to list the 4th value.
4. **`_used_stage2_since()` docstring**: replaced the stale "if
   calc_router.py ever adds one (it does not today)" sentence with an
   UPDATE paragraph stating the marker now exists and this function's
   role is retired to the ERROR path only.
5. **Ride-along (`_KNOWN_GAPS` prose refresh, sanctioned CLAUDE.md
   carry-forward)**: both entries' stale "Session 50 observed mechanism"
   text updated to match currently-observed behavior --
   `sulabh_marriage_q10` now describes the actual Session 61+ mechanism
   (Stage 2 classifies high, routes marriage_compatibility, ratified
   BENIGN Session 63) instead of the superseded medium/REFUSAL
   description; `sulabh_dasha_q15` corrects "3 whitelisted domains" to
   the current 6 (`_DOMAIN_KEYWORDS`), noting the REFUSAL mechanism
   itself is unchanged.

## Pre-commit addendum: module docstring sync

Rewrote the module docstring's route paragraph (originally written
Session 55, describing route as *derived by correlating*
`calc_router_stage2.log`, and asserting "RouteResult itself... carries
no route marker of its own" -- both now false). Replaced with an UPDATE
paragraph: `route` is read directly off `DomainAnswer.route`, a
first-class orchestrator-emitted signal; the log correlation survives
only on the ERROR path. No logic changed -- docstring only.

## Verification

**pytest -q** (run twice: after the 5 enumerated changes, and again
after the docstring addendum):
- Both runs: **3134 passed, 3 skipped** -- exact match, zero delta both
  times (docstring-only change produced no test impact, as expected).

**Golden harness** (`run_golden_eval()`):
- **match=9 / match_stage2=8 / known_gap=2 / new_gap=0 / error=0** --
  exact match to frozen baseline
  `diagnostics/golden_scorecard_20260711_112836.md`.
- Row-by-row diff: `grep '^| sulabh' <old> <new>` on both scorecards
  diffs to **nothing** -- every row's `id`/`domain`/`expected_tier`/
  `actual`/`route`/`demotion_reason`/`category` is byte-identical,
  including every `route` value. **No MATCH<->MATCH_STAGE2 category
  flip occurred on any row**; correlation-derived and direct-read
  routes agreed on all 19 executed rows this run.
- New scorecard: `diagnostics/golden_scorecard_20260711_172257.md`.

## Abandoned-squash episode (recorded for the session log)

A prior prompt in this bundle asked to squash the two preceding
route-provenance commits (`7e69614` "Add RouteResult.route provenance
to DomainAnswer + Stage 2 client injection seam", `3683119` "Strengthen
Layer C full-chain tests for orchestrator route stamping") into one and
force-push over already-pushed `main` history. Before executing,
confirmation was sought given the destructive/shared-state nature of a
force-push on main; the user's next message aborted the rewrite
outright rather than answering the pending scorecard-file-inclusion
question.

Recovery: `git reset --hard 3683119` restored working tree to exactly
its pre-reset state. Verified: `git log --oneline -5` showed both
commits intact in original order; `git status` clean; `git log
origin/main..main` empty (local and origin identical). **No
force-push occurred.** Both commits remain separate, as originally
committed and pushed.
