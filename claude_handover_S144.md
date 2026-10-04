================ HANDOVER -> S144 (astro-agent, wip/interpretive-pilot) ================
RECOMMENDED MODEL: Opus for the design open (KP significator precedence/strength-ranking
sourcing -- a classically-contested rule, not a mechanical lookup); Sonnet 4.6 for the
Claude Code build + tests once that design is settled. State the model on line 1 of every
Claude Code prompt.

------------------------------- HOW TO READ THIS FILE -------------------------------
This handover is the NEWEST and LEAST AUTHORITATIVE source (Working Style #32). Read the
primary sources first; do NOT re-derive what is already decided:
  1. CLAUDE.md -> Current Session Focus (the S143 block) -- read it in full, it is dense.
  2. SESSION_LOG.md -> the S143 section (much longer, the evidentiary detail).
  3. ASTRO AGENT -- MASTER BUILD PLAN.md -> section 4 (Track A) and section 7 (V2 horizon,
     "AstroSage PDF removal in favour of in-house computation").
  4. THIS HANDOVER LAST.
Tags: [VERIFIED S143] read from tree/capture this session; [REPORTED]; [UNKNOWN] (esp.
commit SHAs -- read them from `git log`, never invent, #32).

------------------------- STAY ON TASK (why this file exists) -------------------------
S143 already did the hard diagnostic work and made (then corrected) one real mistake. Do
NOT re-litigate either of these -- they were settled this session, with evidence:
  - Whether the KP cuspal sub-lord alone can fix the marriage-timing pick -- NO, measured
    live 3 times, it is structurally incapable (a single value, fixed for the whole chart,
    cannot discriminate between two antardashas in the same mahadasha).
  - Whether "restate the printed PDF table" is an acceptable pattern for a new Track A fact
    -- NO. This was BUILT and WIRED into production this session, then REVERTED same
    session when Sulabh caught that it broke the established pattern (ephemeris-compute +
    PDF-oracle-validate-ONLY, never PDF-as-runtime-source). Read the S143 CLAUDE.md entry's
    "NEW LOCKED PRINCIPLE" paragraph before proposing anything PDF-adjacent.

================================ WHERE THINGS STAND ================================
[VERIFIED S143] KP 7th-cusp sub-lord: BUILT, oracle-validated (46/48 across 4 charts, 2
documented xfails), WIRED into the fact block, committed to device. This fact class is
DONE. It is also, by itself, PROVEN INSUFFICIENT for marriage-timing selection accuracy --
that is not a defect in it, it is a scope limit (a fixed-per-chart fact cannot carry
period-varying information).

[VERIFIED S143] KP house significators: parser (`agent/calculations/kp/significators.py`)
and its composer (`agent/astro/kp_significator_facts.py`) are BUILT and validated (100%
match, all 4 reference charts' real PDFs; Sulabh's Mercury/Rahu rows independently
cross-checked against `Output.txt`, a project doc Sulabh already validated in a prior
session). `capability_gate.py`/`pipeline.py`/`interpreter.py` all have the wiring in place
(per-antardasha `[signifies houses: ...]` tags, a standing NATAL paragraph, an
EXPERT_SYSTEM fact-type mention) -- but NONE of it is reachable in production right now,
because `frontend/app.py` and `scripts/expert_pilot.py` no longer call the composer. This
is deliberate, not an oversight -- see the S143 CLAUDE.md/SESSION_LOG entries for why.

[REPORTED -- Sulabh must confirm, this is the FIRST thing to check] Has the live GPT-5
measurement been re-run since the significator detour started? ("when would I have got
married", expert mode on, via `scripts/expert_pilot.py marriage_past` or Streamlit.) With
significators unwired, this now measures exactly the S143 fix set alone (cuspal sub-lord +
NATAL/TRANSIT rule + completeness rule) -- the last 2 live runs captured mid-session still
picked Mercury-Venus/Mercury-Saturn, not Mercury-Rahu. If a clean re-run still shows that,
it CONFIRMS the diagnosis (cuspal sub-lord genuinely cannot fix this alone) and S144's task
below is the right next step. If it has somehow shifted to Mercury-Rahu already, STOP and
report that back before building anything -- it would mean the diagnosis needs revisiting.

================================ S144 -- THE TASK ================================
Build a real ephemeris-COMPUTED KP house-significator engine (not a PDF parse) and validate
it against the oracle fixture already built, before wiring anything into production.

1. SOURCE THE PRECEDENCE/STRENGTH RULE FIRST -- DESIGN WORK, DO NOT SKIP TO CODE. The KP
   house-significator technique has (at minimum) 4 levels: (a) planets OCCUPYING a house,
   (b) the house's OWN LORD, (c) the STAR LORD (nakshatra lord) of any planet occupying the
   house, (d) the star lord of the house's own lord. Classical KP sources differ on: whether
   a 5th level (sub-lord of the above) is included; how ties are broken; and the STRENGTH
   RANKING across levels (which is what actually matters for timing precedence, not just
   flat house-membership -- this codebase's current wiring only renders the flat list,
   which is already a scope reduction worth flagging explicitly to Sulabh, not silently
   accepting). Cite the specific KP source for whichever rule set is chosen (the project's
   in-scope corpus explicitly includes "the KP system" -- check what's actually ingested/
   available before assuming a citation is unreachable). This is a genuine 9-agent-framework
   design decision (Parashara/domain agent + Validation Source agent both have standing
   here) -- invoke it silently, surface only if it conflicts.
2. BUILD ON EXISTING PRIMITIVES, do not re-derive them:
   - House occupants: `chart_facts["planet_positions"]` / `house_lord_mapping` already give
     house-by-planet.
   - House lord: `chart_facts["house_lords"]` already gives this.
   - Star lord (nakshatra lord) of a planet: [UNKNOWN -- verify whether this already exists
     anywhere, e.g. exposed as a byproduct of the dasha calculation which is itself
     nakshatra-keyed, or needs a small new 27-row lookup keyed off the same sidereal
     longitude the cuspal sub-lord table already uses at coarser (243-way) grain]. Do NOT
     rebuild `sub_lord_for_longitude` for this -- if a star-lord (27-way, not 243-way)
     lookup does not exist, it is a much smaller table than the sub-lord one, but confirm
     first rather than assuming either way.
   - Which house cusps: KP significators are conventionally read off the SAME Placidus KP
     cusps already captured in `meta["house_cusps_kp_sidereal"]` (S143) -- do not introduce
     a second house system for this.
3. VALIDATE against the oracle BEFORE wiring anything: `tests/calculations/kp/
   test_significators.py`'s pinned tables (all 4 reference charts) are the ground truth.
   Write the computed engine's own test file (do not edit `test_significators.py` itself --
   that file is now scoped to the PARSER, keep it that way) that calls the NEW computed
   function and compares against the SAME 4 charts' expected dicts. State a match-rate floor
   explicitly (mirror the cuspal sub-lord's "at least 46/48" pattern) with a justification
   for wherever it lands, before locking it.
4. ONLY AFTER (1)-(3) clear: re-wire `agent/astro/kp_significator_facts.py` to call the new
   COMPUTED function instead of `parse_kp_significators` (or add a new composer, whichever
   is the surgical edit once the actual function signature is known) -- then, and only then,
   re-add the two production call sites in `frontend/app.py` and `scripts/expert_pilot.py`
   that this session removed. `capability_gate.py`, `pipeline.py`, `interpreter.py` need NO
   changes at this point -- they already speak the right shape (a dict of planet -> houses),
   built and tested this session, sitting inert waiting for a computed source.
5. MEASURE the same way S141-S143 all did: does this actually change the GPT-5 pick on "when
   would I have got married" toward Mercury-Rahu (live run, Sulabh's machine only, sandbox is
   firewalled from api.openai.com).

-------------------------------- CLOSED -- DO NOT REOPEN --------------------------------
- Whether the cuspal sub-lord alone is sufficient -- NO, measured 3 times live, structurally
  incapable (see WHERE THINGS STAND). Do not re-propose a wording-only fix for it.
- Whether "parse the PDF live in production" is an acceptable shortcut for this fact class --
  NO, built and reverted THIS session. Read the CLAUDE.md "NEW LOCKED PRINCIPLE" paragraph
  before proposing it again in any form (including "just for now" or "as a fallback when
  ephemeris computation isn't confident").
- The PDF parser and its 4-chart fixture are NOT wasted work -- they are now the oracle for
  step 3 above. Do not delete or "clean up" `agent/calculations/kp/significators.py` or
  `tests/calculations/kp/test_significators.py`.
- Serve-time answer-guards -- REJECTED (Sulabh, S141). Completeness prevents fabrication,
  not a guard. Applies to this fact too -- feed it, don't gate on it.
- Lal Kitab -- explicitly deferred to "the end" per Sulabh's own instruction. Do not start
  it before the significator engine, and do not start it without being asked.

-------------------------------- STANDING WARNINGS --------------------------------
- COMMIT needs the literal "RATIFIED: commit authorized" (#14). Docs/diagnostics exempt --
  this handover, CLAUDE.md and SESSION_LOG.md updates were written without it, same as every
  prior handover.
- VALIDATION-FIRST (Calculation Architecture, standing): do not wire the computed
  significator engine into the fact block before it clears its own stated match-rate floor
  against the 4-chart oracle. This is the SAME discipline that gated the cuspal sub-lord in
  S143 and the one this session's significator detour skipped by accident.
- PDF-AS-ORACLE-ONLY (NEW this session, see CLAUDE.md S143 entry): never make a served
  answer's fact depend on a PDF being uploaded/present. If ephemeris computation for some
  sub-piece genuinely isn't tractable, the right move is to leave that fact UNWIRED (built,
  tested, not called by any production caller) and say so -- not to fall back to a live PDF
  parse "temporarily".
- EXPERT MODE flag: set `ASTRO_EXPERT_MODE=1` in the SHELL that launches streamlit
  (`$env:ASTRO_EXPERT_MODE="1"`); app.py has NO load_dotenv, so a `.env` entry does NOT work.
- DELIVERY (Cowork): write code INTO the tree; never deliver edits as chat files. Editing
  under /mnt/user-data/outputs auto-posts a chat card -- edit in scratch, `cp` to outputs,
  commit via device_commit_files.
- DESIGN-INTENT-FIRST (S123): trace before calling anything unbuilt/broken/gap.
- Every Claude Code prompt: model on line 1, DECISION + TOKEN CEILING, and write output to
  `latest_run.md` (truncate first).
- Cowork sandbox is firewalled from api.openai.com -- any live GPT-5 measurement needs
  Sulabh's own machine.

------------------------------ OPEN -- NEEDS SULABH ------------------------------
- Has he re-run the live GPT-5 measurement with significators unwired (see WHERE THINGS
  STAND above)? This should happen BEFORE step 1 of the S144 task, not after -- if the
  pick already shifted, the diagnosis needs revisiting before more KP work is scoped.
- Where should the precedence/strength-ranking rule (step 1) actually be sourced from --
  does he have a specific KP manual/text in mind (the project scope names "the KP system"
  generically), or should this session default to the most common documented convention
  and flag it explicitly as a to-be-confirmed choice?
- Full `pytest tests/astro/ tests/calculations/ -q` on his own machine, confirming the S143
  revert didn't regress anything beyond the sandbox-verified subset (187 passed/1 skipped/
  2 xfailed there) -- has not been run by Sulabh directly yet this session.
==========================================================================================
