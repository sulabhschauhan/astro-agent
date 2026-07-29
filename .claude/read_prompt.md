# Read Prompt

#Paste your instructions here. Then tell Claude: Read .claude/read_prompt.md and execute

MODEL: Haiku 4.5

TASK: E2F step 3 joint commit + push covering step 3a (source) +
step 3b (test update). One source commit, one push.

RATIFIED: commit authorized

COMMIT (source + test — RATIFIED above):
Files:
  agent/interpretive/claim_extraction.py
  tests/interpretive/test_claim_extraction.py

Message:
  S78 E2F step 3: coherent retry history for E-3 chunk exclusion

  The 2026-07-29 dogfood confirmation run exposed a design flaw in
  step 1's implementation: filtering the retry's turn 1 user prompt
  made turn 2 (the prior assistant response citing the excluded
  chunk) reference a chunk that turn 1 no longer presented.
  Incoherent history — LLM returned zero claims to play safe,
  producing outcome=empty_retry with p.87_c0 (validatable, adjacent
  in the gated set) sitting unused. Fix worked mechanically (E-3
  chunk excluded from re-citation) but not at the user-visible layer
  (thumb still landed in the "not clearly address..." decline list).

  Fix: preserve the original chunk list in the retry's turn 1
  (matching what attempt 1 actually saw), enforce exclusion via an
  explicit correction instruction in turn 3 that names the failed
  chunk_id(s) and forbids re-citing them. Retry pool discipline
  moves from history-rewriting to explicit instruction — a
  coherent dialogue the LLM can act on.

  Non-E-3 retry path unchanged: empty excluded_chunk_ids still
  produces the old "Same chunks, same feature." wording. Skip-
  retry-when-all-excluded branch unchanged. Diag enum values
  unchanged.

  Test changes:
  - test_e3_partial_failure_excludes_failed_chunk_from_retry_pool:
    docstring and assertions updated to check the new mechanism
    (turn 1 preserves both chunks; turn 3 names the exclusion).
    Original invariant preserved: retry does not re-attribute to
    the failed chunk. Diagnostic assertions unchanged.

  Full suite 3304 pass / 0 fail / 7 skip / 1 xpass — matches
  baseline.

PROCEDURE:
1. git add agent/interpretive/claim_extraction.py tests/interpretive/test_claim_extraction.py
2. git status --short — verify ONLY those two files staged.
   diagnostics/latest_run.md must be unstaged.
   .gitignore, diagnostics/e2f_retrieval_topk.md,
   scripts/e2f_probe_thumb_retrieval.py — if any are modified/
   untracked, DO NOT stage. They commit separately in housekeeping.
3. git commit with the message above.
4. git log origin/main..HEAD --oneline — expect exactly 1 line.
5. git push origin main.
6. git log origin/main..HEAD --oneline — expect empty post-push.

DELIVERABLE (written to diagnostics/latest_run.md, overwriting):
- Commit hash
- git log origin/main..HEAD --oneline before and after push
- Final git status --short

If push fails, STOP and report — do not retry without design-chat
approval.