# Read Prompt

#Paste your instructions here. Then tell Claude: "Read .claude/read_prompt.md and execute"

TASK: Add Stage 2 (LLM-constrained-classification fallback) to calc_router.py — ROUTING ONLY.

FILE: agent/infra/calc_router.py (surgical edit, not a rewrite)

CONTEXT
Stage 1 (existing keyword scorer) stays untouched except confirm it still
runs first and _UNBUILT_MODULE_KEYWORDS check still short-circuits BEFORE
any domain scoring, as it does today. Do not touch _UNBUILT_MODULE_KEYWORDS,
_DOMAIN_KEYWORDS, _STEM_MAP, or the "job" dead-keyword bug in this prompt —
those are separate, already-scoped tasks. Do not touch anything related to
Sade Sati / q14 — that is explicitly out of scope for this prompt.

BEHAVIORAL CONTRACT

1. Stage 2 fires ONLY when Stage 1 returns REFUSAL via the confidence-floor
   path or the margin-tie path (best_score < 0.4, or margin < 0.15). It
   must NOT fire when Stage 1 refused via the unbuilt-module-keyword path.

2. Stage 2 calls GPT-4o-mini with:
   - temperature 0
   - constrained/tool-call output only — no free text parsing, no regex
     extraction of a JSON blob from prose
   - output schema: domain (enum: marriage_compatibility | career_strength
     | current_dasha | none), confidence (enum: high | medium | low)
   - input: the raw question text ONLY. Do NOT pass Stage 1's scores,
     matched keywords, or any expectation into the prompt — the model
     must classify independently (no anchored judgment, rule #9).

3. Routing decision from Stage 2: route ONLY if confidence == "high".
   confidence == "medium" or "low" -> REFUSAL, same message contract as
   today's confidence-floor refusal.

4. Failure handling: any exception from the API call (timeout, auth error,
   malformed/unparseable structured output, schema validation failure) ->
   catch explicitly, log the exception type/message, and return REFUSAL.
   Never fall through to Stage 1's sub-floor result. Never let an
   exception propagate to the caller uncaught.

5. Logging: every Stage 2 invocation (fired or skipped-then-fired) must
   log to diagnostics/ (not chat) — question text, Stage 1's best_score
   and margin, Stage 2's returned domain+confidence, and final routing
   outcome. One line per invocation, append-only, do not overwrite prior
   runs.

6. New constants (confidence enum mapping, model name, timeout value) must
   each carry an inline comment stating: justification, scope guard
   (what this does NOT cover), and revisit trigger — same discipline as
   the existing 0.4 floor / 0.15 margin constants.

7. No changes to the public function signature(s) that orchestrator.py or
   any other caller depends on — Stage 2 is an internal fallback inside
   the existing routing function, transparent to callers.

EXPLICITLY OUT OF SCOPE FOR THIS PROMPT
- No test file (separate prompt, next).
- No q14 / Sade Sati keyword or payload work.
- No "job" stem-map bug fix.
- No caching layer.
- No changes to golden_harness.py or golden_qa_sulabh.py.

DELIVERABLE
Patched calc_router.py only. write full below output to diagnostics/latest_run.md and push to git.
Report back: what changed (function/line
level), new constants added with their tuning-note comments verbatim,
and confirm full test suite still green before this prompt's own tests
(next prompt) are even written.