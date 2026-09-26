================ HANDOVER -> S143 (astro-agent, wip/interpretive-pilot) ================
RECOMMENDED MODEL: Opus for the design open (Placidus cusp capture + sub-lord table
design, oracle-source choice); Sonnet 4.6 for the Claude Code build + tests. State the
model on line 1 of every Claude Code prompt.

------------------------------- HOW TO READ THIS FILE -------------------------------
This handover is the NEWEST and LEAST AUTHORITATIVE source (Working Style #32). Read the
primary sources first; do NOT re-derive what is already decided:
  1. CLAUDE.md -> Current Session Focus (the S142 block) + the S141 Locked Decision
     ("TIMING = RESTATE NOT BUILD; COMPLETE FACTS + EXPERT-MODE, NOT GUARDS").
  2. SESSION_LOG.md -> the S142 section.
  3. THIS HANDOVER LAST.
Tags: [VERIFIED S142] read from tree/capture this session; [REPORTED]; [UNKNOWN] (esp.
commit SHAs -- read them from `git log`, never invent, #32).

------------------------- STAY ON TASK (why this file exists) -------------------------
S142 scoped this task carefully so S143 does not have to re-derive it. Do not re-run the
"is this simple or complex" question -- it was already answered THIS session (complex,
that's why it's a new session): KP 7th-cusp sub-lord is a genuine NEW BUILD, not a
restate like Sade Sati was. Read section "WHAT S143 MUST BUILD" below and execute it;
don't re-scope from scratch.

================================ WHERE THINGS STAND ================================
[REPORTED -- verify with `git log --oneline -5`] The S142 changeset (Sade Sati/gochara
restate + Sulabh oracle validation) is UNCOMMITTED on `wip/interpretive-pilot` (no
"RATIFIED: commit authorized" token was given). Sandbox-run (Cowork; conftest bypassed,
agent.infra/openai not staged there): test_sade_sati.py 37/37, test_transit_facts.py
10/10, test_capability_gate.py 29/29, all passing. Sulabh has NOT yet run the full
`pytest tests/astro/ tests/calculations/ -q` on his own machine -- do that FIRST, before
touching anything new, to confirm S142 didn't regress the 447-ish baseline.

WHAT S142 SHIPPED (all Path B, all restates, no new guard):
- Sade Sati / Saturn gochara fed into the fact block via a new composer module
  `agent/astro/transit_facts.py` (`build_transit_facts`), wired the same way as
  `yoga_facts.py`/D9. `pipeline._fact_block` now tags antardasha lines with
  `[Saturn: <sign>, house H from lagna, house H from Moon, Sade Sati <PHASE>]`.
- NEW: Sulabh is now a THIRD oracle-validated reference chart for Sade Sati (was only
  Sheridan/Surbhi) -- checked against his own AstroSage report
  (data/pdfs/VedicReport5-24-202610-01-26PM.pdf), 24/24 rows match, folded into
  tests/calculations/transits/test_sade_sati.py permanently.
- The true ~2019 marriage window (Mercury-Rahu) sits in AstroSage's own
  Sagittarius/Setting Sade Sati row; the false-positive window (Mercury-Venus,
  2011-14) sits in its Libra/Rising row -- independent confirmation of the S141
  hypothesis from a commercial source, not just our own ephemeris.
- NOT YET DONE: the actual live GPT-5 re-ask ("when would I have got married" with
  expert mode on) -- Cowork sandbox is firewalled from api.openai.com. ASK SULABH
  WHETHER HE HAS RUN THIS YET before building KP -- if Saturn transit alone already
  fixes the selection, KP/Lal Kitab may not be needed. If he hasn't run it, that is
  arguably a higher-priority first step than starting the KP build.

================================ S143 -- THE TASK ================================
Build KP (Krishnamurti Paddhati) 7th-cusp sub-lord and feed it into the fact block, same
end goal as Sade Sati (another corroborating input system for marriage-timing selection
accuracy) but a DIFFERENT shape of work -- a BUILD, not a restate.

WHAT S143 MUST BUILD (scoped S142, verified against the actual tree):
1. CAPTURE THE PLACIDUS CUSPS (cheap -- restate-shaped). `chart_calculator.py` already
   calls `swe.houses(jd_ut, lat, lon_geo, b"P")` (Placidus, sidereal via the existing
   ayanamsha subtraction pattern) at two sites -- `calculate_chart()` (~line 723) and
   `build_varshaphal_chart()` (~line 1057) -- but discards the returned cusps tuple
   (`_, ascmc = swe.houses(...)`), keeping only `ascmc[0]`. Capturing all 12 cusps costs
   nothing new ephemeris-wise; just stop throwing them away. Do NOT reuse
   `compute_porphyry_house_cusps()` -- that is a DIFFERENT house system (Porphyry/
   Sripati, hsys='O', built for Bhava Dig Bala) and is not KP-valid. KP requires
   Placidus specifically.
2. BUILD THE KP SUB-LORD TABLE (genuinely new -- this is the real work). Each of the 27
   nakshatras (13d20' each) is subdivided into 9 segments in Vimshottari dasha
   proportion (Ketu 7yr/120, Venus 20/120, Sun 6/120, Moon 10/120, Mars 7/120, Rahu
   18/120, Jupiter 16/120, Saturn 19/120, Mercury 17/120 -- same 120-year cycle already
   locked in `agent/calculations/dashas` for mahadasha proportions, just applied at a
   finer grain here). 27 x 9 = 249 sub-divisions of the full 360d zodiac. This table does
   NOT exist anywhere in the codebase (confirmed S142 by a full recursive listing of
   agent/calculations/ -- no kp/ subpackage, no sub-lord references). It is mechanical
   and deterministic (no cross-source fragmentation the way some yoga definitions had),
   but still needs: a clean data structure (probably a sorted list of (start_deg,
   sub_lord) tuples per nakshatra, or a flat 249-row table), a lookup function
   `sub_lord_for_longitude(sidereal_lon: float) -> str`, unit tests on boundary cases,
   and -- per the Calculation Architecture's own validation protocol -- EMPIRICAL
   VALIDATION against an oracle before locking. Likely oracle: an AstroSage KP-specific
   report (check if one exists for Sulabh/Sheridan/Surbhi/David, same way the Sadesati
   report was found this session) or a JHora KP export. VALIDATE FIRST, across at least
   2 reference charts, before wiring anything downstream -- same discipline as every
   other calculation module (see CLAUDE.md's Calculation Architecture / Validation
   protocol section).
3. GET THE 7TH CUSP'S SUB-LORD. Once (1) and (2) exist: house 7's Placidus cusp longitude
   -> sub_lord_for_longitude() -> one planet name. That IS the "KP 7th-cusp sub-lord".
4. RESTATE + WIRE (same pattern as Sade Sati, S142; only do this AFTER 1-3 are validated):
   a new fact ("kp_7th_cusp_sub_lord" or similar) added to chart_facts via a composer
   module (mirror transit_facts.py's shape -- caller composes, chart_facts.py stays
   untouched); the matching key added to `capability_gate.FACT_BLOCK_PROVIDES` in the
   SAME change (growth contract); rendered in `pipeline._fact_block`; a short addition to
   `interpreter.py`'s EXPERT_SYSTEM fact-type list if the wording needs it (probably
   already covered by S142's "a placement" language, check before editing). NO new
   serve-time guard -- same locked doctrine as everything else on this path.
5. MEASURE the same way S142 did: does adding this signal change the GPT-5 pick on "when
   would I have got married" (live run, Sulabh's machine only, sandbox is firewalled).

-------------------------------- CLOSED -- DO NOT REOPEN --------------------------------
- Whether Sade Sati is a restate -- YES, it was, and it shipped S142. Do not re-litigate.
- Whether KP is "simple and quick" -- NO, scoped and settled S142 (see above). It is a
  build with an oracle-validation step, same as any other new calculation module.
- Serve-time answer-guards -- REJECTED (Sulabh, S141). Completeness prevents fabrication,
  not a guard. This applies to the KP fact too -- feed it, don't gate on it.
- The citation-grounding reversal for user answers -- RATIFIED (expert mode, S141).
- Reusing compute_porphyry_house_cusps() for KP -- WRONG, it's a different house system
  (Porphyry, not Placidus). Do not "simplify" by reusing it.

-------------------------------- STANDING WARNINGS --------------------------------
- COMMIT needs the literal "RATIFIED: commit authorized" (#14). Docs/diagnostics exempt.
  Never push or rewrite `main` (#13). Never invent a SHA (#32).
- VALIDATION-FIRST (Calculation Architecture, standing): do not wire the KP sub-lord into
  the fact block before it is oracle-validated. Sade Sati was already-validated; KP is
  not, and skipping that step would violate the same discipline every other calc module
  in this codebase follows.
- EXPERT MODE flag: set `ASTRO_EXPERT_MODE=1` in the SHELL that launches streamlit
  (`$env:ASTRO_EXPERT_MODE="1"`); app.py has NO load_dotenv, so a `.env` entry does NOT
  work.
- DELIVERY (Cowork): write code INTO the tree; never deliver edits as chat files. Editing
  under /mnt/user-data/outputs auto-posts a chat card -- edit in scratch, `cp` to outputs,
  commit via device_commit_files.
- DESIGN-INTENT-FIRST (S123): trace before calling anything unbuilt/broken/gap. (This
  handover already did that trace for the Placidus-cusp-discard finding -- don't redo it,
  just verify the line numbers still match if chart_calculator.py has moved since.)
- Every Claude Code prompt: model on line 1, DECISION + TOKEN CEILING, and write output
  to `latest_run.md` (truncate first).
- Cowork sandbox is firewalled from api.openai.com -- any live GPT-5 measurement, and any
  live AstroSage/JHora KP-report lookup that needs a live web fetch, may need to happen on
  Sulabh's own machine. A KP report PDF, if one exists on disk already (check data/pdfs/
  the same way the Sadesati one was found), can be read from Cowork same as this session
  did -- only LIVE network calls are blocked.

------------------------------ OPEN -- NEEDS SULABH ------------------------------
- Has he run `scripts/expert_pilot.py marriage_past` (or Streamlit expert mode) since
  S142 shipped? If Saturn transit alone already fixes the selection, re-confirm KP is
  still wanted before building it.
- Where is the KP oracle coming from -- does an AstroSage KP-specific report exist for
  Sulabh (check data/pdfs/ for a KP-named export), or does this need a fresh pull /
  a different source (JHora)?
- Lal Kitab remains explicitly deferred to "the end" per his own instruction -- do not
  start it before KP, and do not start it without being asked.
==========================================================================================
