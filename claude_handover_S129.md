# HANDOVER -> S130 (written at end of S129, 2026-09-12)

**RECOMMENDED MODEL: Sonnet 4.6** (routine design-chat + Claude Code implementation).
Switch to Opus only for: the advisory-reader promote/hold decision, aspects+conjunctions
architecture, or debugging stuck after 2 attempts.

---

## 0. READ THESE FIRST — DO NOT ASSERT ANYTHING BEFORE YOU HAVE
1. `CLAUDE.md` lines 16-17 (**S129 lock + S129b lock**) — the S128 lock at line 17 is
   SUPERSEDED; read it for what each path IS, not for what is live.
2. `docs/ANSWER_PATHS.md` — the full two-path map. **Read this before touching
   `agent/astro/` or `agent/infra/`, and before calling either one "the pipeline".**
3. `SESSION_LOG.md` -> `## S129` (the last entry).
4. `diagnostics/KNOWN_PATTERNS.md` row **P-022**.

Rules 32/33/34 bind you: **never assert from memory or from a summary — including this
handover — when a primary source is available.** This document is a map, not authority.

---

## 1. WHERE THE PROJECT STANDS

**Path B is the product.** `frontend/app.py` answers through the five-stage pipeline
(Planner -> Calculator -> Retriever -> Interpreter -> Verifier). Path A
(`agent/infra/orchestrator`) is retained, tested, intact, and **wired to nothing** — it is
the revert target. Its known defects are unfixed BY DECISION.

**Coverage is narrow and that is accepted.** The fact block carries exactly three things:
`ascendant_sign`, `lord_house_map`, `planet_positions` (house + sign only). House-lord and
planet-placement doctrine answers. **Timing questions DECLINE** — the capability gate
(Stage 1.5, deterministic, no LLM) refuses in plain language rather than inventing a date.
AstroSage PDF stays as the covering surface until the block covers those sections.

**The user never sees jargon.** `answer_view.render_user_answer` is the surface; all
technical detail goes to `diagnostics/qa_capture/<UTC>.md`.

---

## 2. THE THREE RULES THAT WILL BITE YOU IF YOU MISS THEM

1. **FACT-BLOCK GROWTH CONTRACT** — widening `pipeline._fact_block` REQUIRES adding the
   matching key to `capability_gate.FACT_BLOCK_PROVIDES` **in the same change**. A test
   pins them together.
2. **PRATYANTAR** — unhooked on Path B. Today's safety is **ABSENCE, not a guard**: the
   block carries no dasha. Whoever adds dasha MUST add the suppression in that same change
   (±37d drift, wrong lord).
3. **LIVE RUNS COST REAL MONEY.** A live dogfood run is required ONLY when: the interpreter
   prompt changed, the fact block gained a new fact class, model/config changed, or
   something is being ratified. Everything else -> `scripts/replay_capture.py`, zero API
   cost. **The Claude sandbox is FIREWALLED from api.openai.com — live runs happen only on
   Sulabh's machine.**

---

## 3. IMMEDIATE NEXT STEPS (in order)

1. **Sulabh's stress test** on the widened fact block. This QUALIFIES as a required live
   run (planet positions are new to the model). PowerShell:
   ```
   $env:ASTRO_PALM_ENABLED=1; $env:ASTRO_DOGFOOD_CAPTURE=1; $env:PALM_RULES_ENGINE=1; streamlit run frontend/app.py
   ```
   No AstroSage upload, no palm upload — click Calculate Kundli, then ask.
2. **Promote or hold the advisory planet reader** on the measured
   `advisory_would_drop_a_kept_claim` from that capture. **Do NOT promote on intuition.**
   Non-zero = it would have dropped a claim the enforcing gate kept -> investigate before
   promoting.
3. Then, and only then, the deferred queue in §4.

---

## 4. DEFERRED / OWED (nothing here is lost; nothing here is started)

- **Aspects + conjunctions** into the fact block (Q1 option c). Both are already returned by
  `calculate_chart()` as `aspects_by_planet`, `aspected_by`, `conjunctions` — this is a
  RESTATE task in `chart_facts.py`, not a calculation task.
- **`vimshottari` / dasha** + the pratyantar hook. Blocked on the gate being able to
  range-verify a date.
- **Architect's refactor** — `pipeline._fact_block` still calls
  `payload_builder.parse_lord_house_map`; the adapter should own that.
- **MASTER BUILD PLAN** stale (~13 lines).
- **Cost-constraint re-ratification** — $0.01 ratified vs ~$0.19 / 75s measured.
- **`main` is stale at S84** -> project RAG is ~45 sessions behind. Everything since lives
  on `wip/interpretive-pilot`.

---

## 5. TRAPS — THINGS SESSIONS KEEP GETTING WRONG

- **`agent/calculations/core/chart_d1.py` is a PERMANENT, DELIBERATE stub. Never implement
  it.** Two sessions have now planned to build it. The D1 chart is in production at
  `agent/chart_calculator.py::calculate_chart()`. Recorded in 3 places: the stub docstring,
  `CLAUDE.md` line ~139, and P-022.
- **`ch34_s011` is NOT a mis-citation — it is 5/5 faithful.** Called wrong TWICE, both times
  by reading a truncated slice of a 5,396-char segment; the Raja Yoga verse sits at
  ~char 1,800. **Read the whole segment.**
- **Saturn "(R)" is RESOLVED — do not reopen.** Transcription slip in the hand-typed
  section 3e table of `sulabh.md`; census is 8/8. Proof is in the file's own raw JHora
  export. No JHora check is needed from Sulabh.
- **Enforcing-gate blind spot, fails safe, NOT a bug to fix casually:** `_CONDITION_RE`
  requires `<Nth> lord`, so "Mars, the lord of the 3rd, is in the 7th" does not match ->
  UNDETERMINED -> kept.
- **Surbhi's birth data is 11 Sep 1992, 10:30, Patna.** It has been fabricated before. Read
  `reference/oracle_fixtures/surbhi.md`.
- **`tests/fixtures/qa_captures/s129_live_gpt5_20260912T160015Z.md` is a frozen real gpt-5
  run.** It costs a live run to recreate. Do not delete or regenerate casually.
- **CRLF**: the Windows tree is CRLF. Convert anything written back, or the diff is
  whole-file.

---

## 6. WORKING PROTOCOL (Sulabh's, non-negotiable)

- Expert-to-expert. **No explanation unless asked** — usage limit is tight.
- **You do the coding.** You have full repo access. Hand over a Claude Code prompt only for
  what you genuinely cannot do yourself.
- **REVIEW before PROCEED** — flag at least one issue before approving any edit.
- **SAMPLE before SCALE. HARDEST CASE first. SURGICAL EDITS** — no full-file rewrites.
- **One prompt, one task.** Never proceed to the next step without confirmation.
- **Commits are Sulabh's**, from his tree. State the recommended model as the first line of
  every Claude Code prompt.
- Every claim about the codebase carries **branch + commit SHA**. If you can't name the SHA,
  you didn't read the code — say so.
- **"X does not exist" is never sayable alone** — only "X not found in <paths> on
  <branch>@<sha>". A contradiction from Sulabh is a **STOP** signal: re-verify the SOURCE,
  never re-run the same search harder.
