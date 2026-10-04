================ HANDOVER -> S142 (astro-agent, wip/interpretive-pilot) ================
RECOMMENDED MODEL: Opus for the design open (which systems to feed, validation); Sonnet
4.6 for the Claude Code restate. State the model on line 1 of every Claude Code prompt.

------------------------------- HOW TO READ THIS FILE -------------------------------
This handover is the NEWEST and LEAST AUTHORITATIVE source (Working Style #32). Read the
primary sources first; do NOT re-derive what is already decided:
  1. CLAUDE.md -> Current Session Focus (the S141 block) + Locked Decisions (the S141
     entry: "TIMING = RESTATE NOT BUILD; COMPLETE FACTS + EXPERT-MODE, NOT GUARDS").
  2. SESSION_LOG.md -> the S141 section.
  3. THIS HANDOVER LAST.
Tags: [VERIFIED S141] read from tree/capture; [REPORTED]; [UNKNOWN] (esp. commit SHAs --
read them from `git log`, never invent, #32).

------------------------- STAY ON TASK (why this file exists) -------------------------
S141 burned many turns re-deriving architecture that was ALREADY decided. Do not repeat
that. The realignment is RATIFIED and closed (below). S142 is a NARROW RESTATE. If you
catch yourself re-arguing citation-grounding, serve-time guards, or "should we build
vimshottari" -- STOP; those are settled. Execute the restate, MEASURE, report.

================================ WHERE THINGS STAND ================================
[REPORTED -- verify with `git log --oneline -5`] The S141 changeset was committed on
`wip/interpretive-pilot` (SHA UNKNOWN here). If not committed, it is in the working tree;
`pytest tests/astro/ -q` was 447 passed.

WHAT S141 SHIPPED (all Path B):
- Dasha SURFACED into the fact block -- a RESTATE, not a build. `_calc_dasha` was always
  built + oracle-validated; S141 serialised `past_mahadashas` + the full `mahadasha_tree`
  (every MD with its 9 antardashas), restated in `chart_facts._read_dasha`, rendered in
  `pipeline._fact_block`. Pratyantar still suppressed.
- Capability gate FLIPPED: `dasha_periods` in FACT_BLOCK_PROVIDES; `dasha_timing`
  requirement retired. Timing is answerable; the gate declines nothing.
- Interpreter clause fix (a date is a chart fact, not verse text) + EXPERT MODE
  (`interpreter.interpret_expert`, flag `ASTRO_EXPERT_MODE` / `expert=`, DEFAULT OFF).
  Expert answers are free-text, facts hard-grounded, interpretation free, citations
  internal. `answer_view` passes them through citation-free.

THE REALIGNMENT (RATIFIED -- do NOT re-litigate): precompute everything, FEED the values,
let the expert LLM reason, NO serve-time answer-gating, rigor UPSTREAM (calc-validation).
Fabrication is prevented by COMPLETENESS of input, not by guards.

================================ S142 -- THE TASK ================================
Feed SADE SATI / SATURN GOCHARA (transit) into the fact block. Highest-leverage Phase-2
input. S141 proved LIVE that correct dasha math still MIS-SELECTS the marriage window: it
chose the Venus-karaka false positive (Mercury-Venus 2011-14, which Output.txt explicitly
rejects) and missed the true ~2019 window (Mercury-Rahu), because the
Saturn-transit-over-ascendant signal the benchmark used to override the Venus reading is
NOT in our facts. Accuracy is gated on INPUT SYSTEMS, not calculation.

It is a RESTATE, same pattern as dasha -- do NOT reinvent it:
- The calc is BUILT: `agent/calculations/transits/sade_sati.py`, `gochara.py`. VALIDATE
  it first on the 4 reference charts (oracle protocol) -- rigor lives upstream.
- Restate into `chart_facts` as a new fact class; add its key to
  `capability_gate.FACT_BLOCK_PROVIDES` in the SAME change (growth contract); render in
  `pipeline._fact_block`. NO new serve-time guard.
- MEASURE (the real success test, not a unit test alone): with expert mode ON, re-ask
  "when would I have got married" and check whether the Saturn-transit signal moves the
  pick toward the ~2019 window.
- CEILING: measure the payload; timing already fits (~47-109k of 150k). Adding transits
  is small but confirm.

LATER (bigger, UNBUILT, NOT S142 unless Sade Sati proves insufficient): KP 7th-cusp
sub-lord; Lal Kitab -- the other two systems Output.txt corroborated with.

-------------------------------- CLOSED -- DO NOT REOPEN --------------------------------
- "Build vimshottari" -- it is BUILT; the stub is a decoy (like chart_d1). Dasha is DONE.
- Serve-time answer-guards -- REJECTED (Sulabh). Completeness prevents fabrication.
- The citation-grounding reversal for user answers -- RATIFIED (expert mode). The
  cited-claim path stays flag-off as the revert target and keeps the suite green.
- The accuracy gap is INPUT SYSTEMS, not calculation or prompt -- do NOT chase it as a
  calc/prompt bug. Benchmark dasha math independently verified correct to +/-2 days.

-------------------------------- STANDING WARNINGS --------------------------------
- COMMIT needs the literal "RATIFIED: commit authorized" (#14). Docs/diagnostics exempt.
  Never push or rewrite `main` (#13). Never invent a SHA (#32).
- EXPERT MODE flag: set `ASTRO_EXPERT_MODE=1` in the SHELL that launches streamlit
  (`$env:ASTRO_EXPERT_MODE="1"`); app.py has NO load_dotenv, so a `.env` entry does NOT work.
- DELIVERY (Cowork): write code INTO the tree; never deliver edits as chat files. Editing
  under /mnt/user-data/outputs auto-posts a chat card -- edit in scratch, `cp` to outputs,
  commit via device_commit_files. (Repeat offense in S141 -- do not repeat.)
- DESIGN-INTENT-FIRST (S123): trace before calling anything unbuilt/broken/gap.
- Every Claude Code prompt: model on line 1, DECISION + TOKEN CEILING, and write output
  to `latest_run.md` (truncate first).

------------------------------ OPEN -- NEEDS SULABH ------------------------------
- Promote expert mode from flag to DEFAULT once selection accuracy is measured acceptable.
- Build KP cusp sub-lord + Lal Kitab? (for benchmark parity.)
- Delete `scripts/expert_pilot.py` once Sade Sati lands (superseded test rig).
==========================================================================================
