================ HANDOVER -> S141 (astro-agent, wip/interpretive-pilot) ================
RECOMMENDED MODEL: Opus for the S141 design open — vimshottari is a CALCULATION module
(formula sourcing + 4-reference-chart validation + Vedic-day-boundary edge cases, all
Opus-tier per the model-routing rule). Sonnet 4.6 for Claude Code implementation. State the
model on the first line of every Claude Code prompt.

------------------------------- HOW TO READ THIS FILE -------------------------------
This handover is the NEWEST and LEAST AUTHORITATIVE source (Working Style #32). Primary
sources win — read them and quote with the session number. Every claim is tagged:
  [VERIFIED S140] read directly from the tree/capture this session
  [REPORTED]      Sulabh or Claude Code reported it; not independently checked
  [UNKNOWN]       not established — do not guess it (esp. commit SHAs: this file names
                  NONE; read them from `git log`)

READ FIRST, IN THIS ORDER. Assert nothing about the tree until you have:
  1. CLAUDE.md -> Current Session Focus (the S140 line) + Locked Decisions (the two S140
     entries: first/second-class citation; houses-into-selection rejected) + Working
     Style #36. AUTHORITATIVE.
  2. SESSION_LOG.md -> S140 sections 1-7. Read section 7 (the proportionality reckoning)
     BEFORE touching the verifier again — it exists to stop the trap this session fell into.
  3. diagnostics/KNOWN_PATTERNS.md -> rows P-036, P-037.
  4. THIS HANDOVER LAST.

--------------------------- FRICTION POINTS, STATED UP FRONT ---------------------------
- S140 ran in Cowork with a FILE BRIDGE to the working tree (list/read/write) and a cloud
  clone for OFFLINE reproduction, but NO shell on Sulabh's machine. So it cannot read git
  SHAs; Sulabh runs pytest, streamlit, and the commit. Same split holds for S141 unless a
  shell is available.
- Everything below is on `wip/interpretive-pilot`. `main` is stale at S84 (S126 handover) —
  never build on it.

================================ WHAT S140 DID ================================
Two commits landed [REPORTED "committed"; SHAs UNKNOWN here — read `git log`]: one SOURCE
(the verifiability ledger + wiring), one DOCS.

1. KILLED houses-into-selection (Tier 1.1). [VERIFIED S140] Offline reproduction over 35
   captured turns (offline kept_segments == live capture exactly, 303==303): a fail-safe
   relation-based `plan.houses` filter cuts only 0.2-1.5% on the costly turns (payload is
   ~75% relation-less fail-safe segments + ~17% whole chapters, untouchable) AND drops 10
   cited verses — a verse is indexed by its "lord of A in B" placement, a different
   coordinate system from the question's houses, so query-houses are NOT a superset of
   citeable-verse houses (travel Q cited "11th lord in 6th -> foreign residence", relation
   {6,11}, dropped by houses {9,12}). `payload_builder.run_filter` (chart placements)
   already does the only sound chart-conditioning. Evidence: diagnostics/runs/20260920T055639Z.md.

2. RULING (Sulabh): a corpus citation is FIRST-CLASS when a typed predicate can decide it,
   SECOND-CLASS when it rests on a condition the vocabulary cannot yet check. Recorded in
   Locked Decisions. Kills the topic-tag SELECTION layer (reinforces P-034): the
   interpreter+predicate loop already verifies 92.4% of claims unaided.

3. BUILT the standing verifiability ledger. [VERIFIED green offline; REPORTED full astro
   suite green on device]
   - agent/astro/verifiability.py — leaf module, LEDGER_VERSION=1, summarize()/rollup();
     versioned + fail-safe (a pre-S137 capture without predicate_coverage reports
     second_class=None, never a silent 0).
   - pipeline.answer_question attaches result["verifiability"] = summarize(gate.stats)
     (computed in the domain layer that OWNS the gate).
   - qa_capture RENDERS result["verifiability"] as data — no import, no derived-rate
     computation in the capture layer (respects test_qa_capture's imports-nothing guard,
     which caught an initial shape that computed it inside the capture; corrected).
   - scripts/verifiability_rollup.py — standing roll-up; prefers the canonical block,
     falls back to gate-stats for pre-wiring captures.
   - tests/astro/test_verifiability.py — 7 tests.

4. AUDITED P-033 promotion and correctly did NOT flip it. [VERIFIED S140] caught_miss 2/2
   TRUE POSITIVES (ch15_s003, 5th lord Mars exalted in Capricorn, stable D1 arm). BUT a
   FALSE-JUSTIFY of the SAME doctrine surfaced (row P-037): the S139 `any_of` combinator
   works, but the interpreter's ADOPTION of it is unstable run-to-run — the same
   disjunctive verse was emitted as `any_of` in one run (caught) and as a FLAT predicate
   list in another (ANDed -> Own-Sign arm false -> whole CONTRADICTED -> silence justified).
   P-035 is only HALF closed (combinator built, adoption not). Evidence:
   diagnostics/runs/20260920T174749Z.md.

5. PROPORTIONALITY RECKONING (SESSION_LOG S140 s7 + Working Style #36). The session drilled
   from "make selection scale for dasha" down to "how the LLM wraps OR-clauses in
   precondition JSON" and pitched a CONTRACT REDESIGN for P-037 — which only blocks an
   OPTIONAL P-033 enforcing promotion. Sulabh stopped it. The redesign was DROPPED.

================================ MEASURED ================================
Verifiability ledger, 15 S139-era turns (run `python scripts/verifiability_rollup.py` to
refresh): 92.4% claims first-class; typed_share 96.9%; P-033 gate caught_miss 2/47 typed
silences (4.3%); second-class backlog 6 unevaluable claims + 23 uncheckable silences
(19.0%). Only 15 of 51 captured turns carry the full claim ledger — the S140 canonical
`verifiability` block fixes that going forward.

================================ S141 — THE TASK ================================
vimshottari / timing. The HIGHEST-LEVERAGE USER-FACING build (Working Style #36): it
unlocks every "when will I..." question and RETIRES AstroSage as a side effect. This is the
S126 NEXT, deferred through the whole S127-S140 verification arc.

It is a CALCULATION module, so it carries the full protocol (Calculation Architecture +
Working Style #2/#3):
  - Lives in agent/calculations/dashas/vimshottari.py — never a top-level file.
  - FORMULA from PVR (Vedic Astrology, PVR Narasimha Rao) + Kapoor Ch IX for the Vimshottari
    math; cite the page IN CODE (P-028/P-029: no doctrine prose in calc modules). JHora /
    AstroSage only GRADE the answer (P-027: oracle files are never calculation inputs).
  - VALIDATE across all 4 reference charts (Sulabh, Surbhi, Sheridan, David) before locking;
    zero free parameters (test alternative hypotheses, rule them out).
  - EPHEMERIS AUDITOR triggers (this is the trap): the Moon's nakshatra + the balance of the
    first dasha at birth depend on the Vedic day boundary and sidereal Moon longitude —
    S132's sunrise-boundary class. Rounded meta values are an accepted gap (S130); check the
    precision tolerance before trusting a boundary-adjacent balance.
  - HARDEST CASE first (a pre-sunrise birth like Sulabh's 00:30); SAMPLE before SCALE.
Then restate dasha facts into chart_facts so the interpreter can answer timing. CEILING is
the known constraint (S135: 150k approx / 272k real) — MEASURE the timing-question payload
before assuming it fits; the S125 flag stands (design the timing relevance signal on planet
and period NAMES, not houses).

-------------------------------- CLOSED — DO NOT REOPEN --------------------------------
  - houses-into-selection, or ANY pre-selection filter keyed on the question's houses —
    measured dead AND unsafe (S140). run_filter already does the sound chart-conditioning.
  - the topic-tag SELECTION layer — P-034 + the S140 ruling. The loop verifies 92.4% unaided.
  - the `any_of` CONTRACT REDESIGN — dropped S140 as disproportionate. P-037 is PARKED in
    recording-mode; a recorded defect in recording-mode is NOT a fire (Working Style #36).
  - the P-033 enforcing flip — blocked on P-037 (any_of adoption), itself parked. Recording
    mode stays. Do not flip enforcing.

-------------------------------- STANDING WARNINGS --------------------------------
  - WORKING STYLE #36 (verifier gravity): before ANY verifier/instrumentation work, ask if
    it changes what a USER sees or can ASK. If it only tightens an already-safe internal
    check, it is a refinement — record and move on. SESSION_LOG s7 is the worked example.
  - DO NOT NARROW the life-subject domains (S137 standing warning).
  - COMMIT needs the literal "RATIFIED: commit authorized" (#14). Never push or rewrite
    pushed history (#13). Never invent a SHA (#32).

------------------------------ OPEN — NEEDS SULABH ------------------------------
  - ch35 v8 reading; ch35 v17 (two rows or fix the source). Carried from S138.
  - (parked) P-037 any_of adoption; the P-033 enforcing promotion behind it.
==========================================================================================
