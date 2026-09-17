================ HANDOVER -> S136 (astro-agent, wip/interpretive-pilot) ================
RECOMMENDED MODEL: Opus for the design chat (Phase 2 is a doctrine-sourcing + irreversible
architecture decision). Sonnet 4.6 for implementation once the map is ratified. State the
model as the first line of every Claude Code prompt.

READ FIRST, IN THIS ORDER -- assert nothing about the tree until you have. Handovers are the
NEWEST and LEAST authoritative source (P-026); primary sources win:
  1. `ASTRO AGENT — MASTER BUILD PLAN.md`
  2. `CLAUDE.md` -> Locked Decisions: the S135 entry, then the S134 stamp on the S133 lock, then S133.
  3. `diagnostics/KNOWN_PATTERNS.md`
  4. `SESSION_LOG.md` -> `## S135` (incl. the "S135 addendum" block), `## S134`, and `## S133` §4/§5.
  5. THIS HANDOVER LAST.

TREE STATE. Branch `wip/interpretive-pilot`. Read HEAD SHA from `git log`, never a document.
  - S135 (planner ceiling -> real 272k input cap; `_calc_yogas` restated into Path B) and the
    S134 edits (yoga_facts.py `inputs` audit block; rules.py PMP docstring) are ALL present in
    the tree and committed & pushed.
  - CORRECTION (S136): there is NO separate S134 commit. The S134 edits were uncommitted and were
    folded into `6851a2d4`, whose message names only S135. The work is present; the commit is
    just mislabeled. [Certain the code is present; [Likely] it rode in 6851a2d4 -- confirm with
    `git log --stat`.] DO NOT rewrite the pushed commit message to "fix" this (Working Style #13,
    never rewrite pushed history). It is a labeling artifact, not missing work.
  - Every codebase claim you make carries branch + SHA, or say you didn't read it.

WHAT S134 + S135 DID (verify against SESSION_LOG `## S134` / `## S135`, don't take my word):
  - S134: `yoga_facts.build_yoga_facts` attaches a DIAGNOSTICS-ONLY `inputs` audit block
    (chara_karakas, ghati/hora lagna signs, planet_degrees); `pipeline._fact_block` reads only
    fired/ruled_out, so it never reaches the interpreter. Stale PMP module docstring in
    `agent/calculations/yogas/rules.py` corrected (PMP is degree-accurate; moolatrikona reachable).
  - S135 (planner.py): `HARD_CONTEXT_CEILING` 225_000 -> 150_000 approx; new `REAL_INPUT_CAP =
    272_000`; `INTERPRETER_CONTEXT_WINDOW` stays 400_000 (total window, NOT the input limit). The
    model's real input cap is ~272k (a remedy question 400'd at 299,852 real); the old ceiling let
    382,500 est-real through and the API 400'd instead of refusing. `pipeline.answer_question`
    already refuses up front on `refused` -- so correcting the ceiling IS the "remedy refusal up
    front" fix; no separate remedy path exists.
  - S135 (yoga_facts.py): `_restate_calc_yogas` folds mangal_dosha + kalsarpa_yoga from
    `chart["yogas_doshas"]` into the yoga report by RESTATEMENT (S20; no recompute) as additive
    fired/ruled_out rows. Reuses the "yogas" gate key -- no growth-contract change.

--------------------------------- S136 -- THE ONE TASK ---------------------------------
PHASE 2: fact -> chapter. The ONLY substantive work for S136. Do not start anything else (see
PARKED). This is a doctrine-sourcing + irreversible design decision: DESIGN IN THE CHAT FIRST,
Claude Code executes only, and NO source edit until the map below is ratified.

THE PROBLEM (verified S133 §4): a fired yoga produces a correct VERDICT, but the interpreter's
doctrine chapters are chosen from the QUESTION, never from the FACTS. So a fired yoga does not
pull its own doctrine chapter. Consequence is substance, not cosmetics: the verdict stays right,
but the INTERPRETATION can be ungrounded recall or sourced from the wrong chapter (live ghosts to
ch38 raja / ch35 Naabhasa). S133 §4 showed the Vipareeta chapter `bphs2_ch48` was even SELECTED
and shipped, yet its citation was thrown away by an addressing bug.

TWO RISKS THE FIRST DRAFT OF THIS HANDOVER MISSED (both must shape the design):

  A. CEILING HEADROOM [Certain, S130 §6]. The planner already selects 14/16 domains, 81 units,
     185k-229k real prompt tokens on one Saturn question -- now against the S135 150k-approx /
     272k-real cap. Stacking whole yoga chapters ON TOP risks flipping currently-working answers
     into ceiling REFUSALS. LEVER: S130 §6 records "23 of 81 selected units contribute zero
     segments and are carried whole." Yoga-chapter augmentation must DISPLACE those zero-
     contribution units, NOT stack on them -- this both creates room and removes ghost-prone whole
     units.

  B. THE MAP IS INCOMPLETE. S133 §5 maps only ~7 families it happened to observe: raja/solar->
     ch38, Naabhasa->ch35, Adhi->ch36, lunar->ch37, Neecha->ch24, Vipareeta->ch48, PMP->ch75. The
     detector fires 16 JHora yogas + PMP + the 2 S135-restated (mangal_dosha, kalsarpa). UNMAPPED:
     mangal_dosha, kalsarpa, Yogada / Maha Yogada, Yogakaraka, Dharma-Karmadhipati, Raja Sambandha.
     A HALF-MAP IS NOT RATIFIABLE -- it silently pulls chapters for some fired yogas and nothing
     for others. Plus a LIVE CONFLICT to adjudicate: Harsha is a Vipareeta Raja Yoga, but S133 §5
     records it via ch36 while the S131 lock places Vipareeta at ch48 (the "BPHS titles diverge
     from content" problem in miniature). Resolve before ratifying.

PRECONDITIONS (in order; none skippable):
  (1) A COMPLETE, RATIFIED yoga->chapter map. Sulabh's doctrine call; blocks ALL code. S136's
      FIRST deliverable is the ratification-ready table, built from `detector.py` + `rules.py`:
      every fired-yoga id -> family -> proposed chapter -> provenance, with the gaps in (B) and
      the Harsha ch36/ch48 conflict flagged. Do not hand Sulabh a partial guess.
  (2) AUGMENTATION DESIGNED SEGMENT-SPLIT + DISPLACING (ADOPTED DIRECTION, Sulabh S135 close).
      Add the mapped yoga chapters SEGMENT-SPLIT (matching the dominant per-segment address
      format), NOT whole -- this sidesteps the whole-chapter citation mint entirely, removing the
      ghost-drop failure class BY CONSTRUCTION rather than live-testing around it. And it must
      DISPLACE the 23 zero-contribution units (risk A), not stack. This is what converts the old
      precondition "(3) live-verify the S130 ghost-addressing manifest on a whole yoga chapter"
      from a mandatory test into a class that no longer exists. IF whole-chapter augmentation is
      chosen instead, THEN that live-verify precondition becomes mandatory before any edit.
  (3) Only after (1) + (2): touch `build_from_plan`. Not before. REVIEW before PROCEED, one prompt
      one task, `RATIFIED: commit authorized` required for the source commit.

NOTE: the S135-restated mangal_dosha/kalsarpa inherit this same grounding gap; Phase 2 closes it
for them too, and they must appear in the map in (1).

------------------------------ PARKED -- do NOT start in S136 ------------------------------
  - WIDER BPHS yoga set beyond JHora's 16 rows -- the session AFTER Phase 2, on Sulabh's explicit go.
  - RETIRE `catalog/pancha_mahapurusha.py` -- irreversible delete; route a deletion request, never
    delete silently. Unwired/redundant since S133, harmless where it sits.
  - TOKEN CEILING -- DONE in S135. Not open. Re-open only if a NEW real 400 is observed at a
    different boundary; then re-derive from `REAL_INPUT_CAP` and the observed `prompt_tokens`,
    never from the 400k total window or chars/4.

--------------------------------- STANDING RULES ---------------------------------
- PVR/BPHS give the FORMULA (cite the page in code); JHora/AstroSage only grade the ANSWER (P-028).
  Oracle files are never calculation inputs (P-027).
- No doctrine prose in calculation modules (P-029).
- SURGICAL EDITS. Commits are Sulabh's; report every hash; NEVER rewrite pushed history (#13).
- A contradiction from Sulabh, or between this handover and the code, is a STOP signal --
  re-verify the SOURCE, don't argue.
==========================================================================================
