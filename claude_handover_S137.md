================ HANDOVER -> S137 (astro-agent, wip/interpretive-pilot) ================
RECOMMENDED MODEL: Opus for the design chat (S137 opens with a live-quality judgement
call and a doctrine ratification). Sonnet 4.6 for Claude Code implementation. State the
model as the first line of every Claude Code prompt you give Sulabh.

------------------------------- HOW TO READ THIS FILE -------------------------------
This handover is the NEWEST and LEAST AUTHORITATIVE source (P-026). Primary sources win.
It is written to be SHORT ON ASSERTIONS about the tree on purpose: the S136 handover's
predecessor carried three factually wrong tree claims (a chapter that does not exist, a
chapter title that contradicts its own body, a commit that was never made), and the first
hour of S136 went on discovering that. So below, every claim is tagged:

  [VERIFIED S136]  read directly from the file/capture named, this session
  [REPORTED]       Sulabh or Claude Code reported it; not independently checked
  [UNKNOWN]        genuinely not established -- do not guess it

READ FIRST, IN THIS ORDER. Assert nothing about the tree until you have:
  1. CLAUDE.md -> Current Session Focus (the S136 line) and Locked Decisions (the S136
     entry is FIRST). This is where the S136 reasoning actually lives.
  2. SESSION_LOG.md -> the S136 sections. Sections 10-13 are this session's close:
     10 = live verification, 11 = STANDING WARNINGS (read these before touching
     selection), 12 = the UX read of a real answer, 13 = the composer flip.
  3. diagnostics/KNOWN_PATTERNS.md -> row P-030.
  4. docs/AGENT_ROSTER.md -> who the review agents are. Do NOT count agents from any
     other file.
  5. THIS HANDOVER LAST.

--------------------------- A FRICTION POINT, STATED UP FRONT ---------------------------
The design chat has FILE-BRIDGE access to the repo (it can list, read and write files)
but NO SHELL. Consequences, both real, both hit in S136:
  - You CANNOT read the git HEAD SHA, git log, or git status from the design chat. So you
    cannot satisfy the CODE-READ PROVENANCE rule's "branch + SHA" in full. The honest
    form is: "read from the working tree via the file bridge, mtime <x>; branch/SHA not
    nameable from the design chat (no shell)". Say that. Do NOT invent a SHA, and do NOT
    claim you did not read the code when you did.
  - `.claude/` is NOT WRITABLE by the bridge (hard policy block, not a grantable
    permission). That is why docs/AGENT_ROSTER.md lives in docs/ and not .claude/. Do not
    "helpfully" move it back; it cannot be maintained there.
  - The design chat CAN and SHOULD read primary sources itself before asserting or before
    routing a read to Claude Code (Working Style #34).

================================ WHAT S136 ACTUALLY DID ================================
Three commits landed. [REPORTED by Sulabh: "commit done"] -- hashes are [UNKNOWN] to this
handover; read them from git log, never from a document. Whether they are PUSHED is
[UNKNOWN]; the commit prompt said do not push.

1. technique_method REMOVED from the planner's selectable domains  [VERIFIED S136]
   `planner.DOMAINS` 16 -> 15. Gone from the tuple, from SYSTEM_PROMPT section 1, and
   from `_FALLBACK_GLOSS`. All 15 remaining domains now carry a one-line gloss;
   `planetary_nature` carries an ONLY-when scope guard.

   WHY, AND THE ORDER OF THE REASONS MATTERS. The binding reason is DISCLOSURE, not cost:
   no end user asks how the system computes anything, only the system needs a formula,
   and formulas live in Python with the PVR/BPHS page cited in code (P-028/P-029).
   Shipping procedural chapters into the interpreter payload exposes how this project is
   configured, extractable one question at a time. Sulabh made that call; it is not an
   optimisation. The cost finding is SECONDARY and was what surfaced the problem:
   technique_method tagged 45 of 100 units, 148,846 of 242,571 approx-tokens (61.4% of
   corpus) = 99.2% of HARD_CONTEXT_CEILING on a SINGLE selection.

   Methodology questions now return `in_scope: false` with empty `domains`
   (SYSTEM_PROMPT section 5). The closed-vocabulary validator rejects the domain for
   free. The technique_method TAG is UNCHANGED in data/domain_tags_bphs.json -- the
   procedural chapters still exist and are still tagged; only the PLAN domain is gone.

   TWO BUGS FOUND EN ROUTE, both fixed: (a) `_FALLBACK_GLOSS["technique_method"]` led
   with the keyword "how", so the DETERMINISTIC path was pulling 61.4% of the corpus on
   "how will my career go" -- a test now forbids "how" as a keyword for any domain;
   (b) empty `domains` failed validation, so the refusal shape the new prompt asks for
   would have fallen through to `fallback_plan` and keyword-matched a question just
   declared out of scope. Empty is now legal ONLY when `in_scope` is false.

2. Composer (Stage 5b) FLIPPED ON  [VERIFIED S136]
   `pipeline.py`: default flipped, `ASTRO_COMPOSER_ENABLED=0` restores the pre-S136 path
   exactly; an explicit `compose=True/False` argument still wins over the environment.
   WHY NOW: S131 shipped it dark because composed answers were not yet trustworthy
   (ghost citations, unused facts, a payload riding the ceiling). S136 closed all three,
   so presentation was the only remaining gap -- which is this stage's entire job.

3. Two user-visible answer_view defects fixed  [VERIFIED S136]
   (a) The bare "the native" -> "you" swap shipped **"you becomes like a king"** to a
       user. Fixed by adding observed verb forms ahead of the bare rule. NOT generalised,
       deliberately: de-inflecting an English third-person-singular verb is ambiguous from
       the surface form ("rises"->rise but "passes"->pass, both end -ses; "goes"->go but
       "rises"->rise, both end -es). A lexicon does not belong in that module. New helper
       `residual_third_person_verbs(text)` reports every word the bare rule swallowed, so
       the next entry is EARNED from a capture instead of guessed.
   (b) The empty-answer path blamed the CORPUS for a question refused BY POLICY, which
       invited the retry the out-of-scope rule exists to refuse. Now branches on the
       pipeline's own `reason == "out of scope"` -- never on words in the question.

4. Agent roster consolidated  [VERIFIED S136]
   The long-standing "9 agents" was an ADDITION SLIP: S8/S9 locked 6, S19 added Ephemeris
   Auditor + Validation Source and wrote "9-agent framework"
   (SESSION_LOG_ARCHIVE_S19-S66.md:13). 6+2=8. Nothing was lost; nothing was reduced.
   Those two had been ratified for ~115 sessions with NO charter file, so they could not
   be invoked; charters were written from their already-ratified laws (P-027/P-028 for
   Validation Source; S130 precision gap, S132 sunrise boundary, P-022 for Ephemeris
   Auditor). `docs/AGENT_ROSTER.md` is now the SOLE statement of the roster and every
   other site points at it and states no count.

================================ MEASURED RESULTS, AND A TRAP ================================
Live run, diagnostics/qa_capture/20260918T183853Z.md  [VERIFIED S136, read directly]
  - Reading question ("What do the yogas in my chart say about my career and
    professional standing?"): domains ["career"], houses [1,2,6,10,11], in_scope true.
    technique_method ABSENT. Houses still widened -- the gloss narrowed the vocabulary
    WITHOUT damaging the widen mandate.
  - prompt_tokens 84,152 (against ~255,000 est-real before). ghost_citations [].
    17 claims returned, 16 shipped -- the silence gate dropped a genuine false
    precondition (ch24_s008, "ascendant lord placed in the 10th" when Jupiter is in the
    5th and only aspects it). That is the gate working, not a defect.
  - Methodology question ("How is shadbala calculated for a planet?"): in_scope false,
    empty domains, refused in 3.35s with NO model call and no payload.

  *** THE TRAP: THAT 84,152 WAS MEASURED WITH THE COMPOSER OFF. *** The flip landed
  after that capture. The composer adds a second small LLM call (S131 measured its INPUT
  at 553/312 tokens, ~0.8% of that turn's interpreter prompt) and changes the answer
  text. Do not treat 84,152 as the post-flip number, and do not treat the S136 answer
  text as what a user sees now.

================================== S137 -- THE TASK ==================================
In this order. (1) and (2) are one arc: Sulabh deferred them to "after the next module"
and said they would be checked together.

(1) FULL SUITE. The planner change was full-suite verified at 310 (tests/astro) and
    4219 (full) passed, 0 failed  [REPORTED by Claude Code, S136]. The composer flip and
    the answer_view fixes landed AFTER that run and have NOT been suite-verified --
    only the two affected test files were run, green, in an isolated sandbox
    (test_answer_view.py 28 passed, of which 6 new)  [VERIFIED S136]. So: run the full
    suite first. Three sandbox failures seen there were `source_line` tests needing
    data/chapter_index_bphs.json, which was not staged -- they MUST pass on the real tree.

(2) THE FIRST LIVE COMPOSED ANSWER, EVER. This is the real gate, and it is a QUALITY
    JUDGEMENT, not a pass/fail assertion. The composer has never produced a live answer
    on this branch: S131 measured only its input size. Its ENFORCING no-new-chart-facts
    check and its ADVISORY condition-survival check are both unexercised in production.
    Ask the same career question, then read the answer AS A LAYMAN would, against the
    nine problems recorded in SESSION_LOG S136 section 12. The composer is supposed to
    fix items 1 (no verdict/lead), 4 (conditionals reading as non-answers) and 5 (four
    bullets restating one fact) BY DESIGN.
    IF IT LOOKS WORSE THAN THE BULLETS: the revert is `ASTRO_COMPOSER_ENABLED=0`, an
    environment variable, not a code change. Flip it off and bring the capture to the
    design chat. Do not debug it live.

(3) MEASURE JARGON ON THAT CAPTURE, then stop. Section 12 item 2: "10th lord",
    "Karakamsa", "kendra", "Atmakaraka" all shipped to a user, against .claude/ui_ux.md's
    jargon-free requirement. A prompt BLOCKLIST WAS REJECTED BY SULABH AT S131 AS
    HARDCODING -- do not propose one, in any form. The fix must be a principle or a
    corpus-DERIVED lexicon. The composer's plain-English mandate may reduce it as a side
    effect, so MEASURE FIRST and design nothing until you have the number.

-------------------------- PARKED, EACH NEEDS SULABH'S GO --------------------------
  - PHASE 2 yoga->chapter map ratification. The body-verified unit+verse table is already
    written up in SESSION_LOG S136. It is a DOCTRINE call, Sulabh's, and it blocks the
    Phase-2 code. Do not write code against a half-map.
  - WIDER BPHS YOGA SET. The detector computes ~19 combinations; BPHS names hundreds. The
    live capture's own `silent_on` field is the evidence for why this matters: the
    interpreter wrote that Chamara/Sankha/Bheri/Mridanga "need exact stated conditions
    not fully verifiable from provided facts", and that most ch39-41 Raja yoga variants
    need Arudha/Karakamsa specifics -- i.e. doctrine that was retrieved, paid for, and
    unusable because nothing computes whether it fires. What it opens: answers specific
    to the native instead of generic, and the RULED-OUT half, which is the counterweight
    section 12 item 6 found missing (16 bullets of royal patronage with nothing on the
    other side). Cost: each yoga is a formula that must come from PVR/BPHS with the page
    cited in code and be validated on BOTH reference charts, and every one grows the
    payload -- which is exactly why P-030 had to land first.
  - RETIRE catalog/pancha_mahapurusha.py. Irreversible delete; unwired since S133. ROUTE
    a deletion request to Sulabh, never delete silently.
  - DISCLOSURE AUDITOR, the proposed 9th agent (docs/AGENT_ROSTER.md). Proposed, NOT
    active, NOT counted. Derived from S136's own miss: technique_method survived ~130
    sessions of full-roster review because no agent owns "does this expose how the system
    works?" -- Sulabh caught it, not the roster. `.cursorrules` requires explicit approval.

-------------------------------- CLOSED -- DO NOT REOPEN --------------------------------
  - THE "C MEASUREMENT" / ANY SELECTOR THRESHOLD. A low-contribution-unit floor was
    proposed and WITHDRAWN, and the no-threshold decision is RATIFIED. Reasons, so this
    is not re-derived: all 45 affected units are segmented, so the fail-safe segment
    filter already narrows them; the 46,263-token figure that motivated it was CHAPTER
    SIZE from the tag artifact, not tokens the payload ships; and the worst case for a
    correct answer -- a matched segment whose meaning depends on a qualifying verse
    elsewhere in the same chapter -- requires ALL segments, so no count is defensible.
    The follow-up measurement was ALSO closed (S136 close): its only purpose was to
    settle S130 section 6, the ceiling pressure that motivated displacement is gone
    (84k live against a 150k ceiling), and the adopted direction is segment-split, not
    displacement. Do not re-list it as an open item.
  - S130 SECTION 6 IS CORRECTED, NOT MERELY DOUBTED. Its "23 of 81 selected units
    contribute zero segments and are carried whole" cannot occur at unit-selection stage:
    `select_units` admits a unit only when `per_domain[d].segment_count > 0`. Re-measured
    S136: 0 such units across all 15 domains. It was cited as the Phase-2 displacement
    LEVER (risk A). Do not cite it again without re-deriving it from an instrumented run.
  - PROPOSAL B (instrument vs life-subject domain axis). Dropped. It existed to tame
    technique_method, which is gone outright; `planetary_nature` is 5 units / 31 segments.

--------------------------- STANDING WARNINGS (SESSION_LOG S136 s11) ---------------------------
  - WORST-CASE UNIT SELECTION IS STILL 135% OF THE CEILING (83 units / 202,596 approx vs
    HARD_CONTEXT_CEILING 150,000). The 84k live figure is ONE question's draw, not
    headroom. The segment filter is load-bearing and must stay FAIL-SAFE.
  - DO NOT NARROW THE LIFE-SUBJECT DOMAINS. Measured after the removal: wealth 46.1% of
    corpus, health 40.2%, career 40.2%, longevity 39.1%. A future session WILL notice
    these and propose narrowing them. That is forbidden -- S124's never-narrow doctrine,
    the planner's own widen mandate, and the fail-safe filter all point the same way.
    technique_method was removable because it was an INSTRUMENT tag naming procedural
    chapters no user question should reach: a CATEGORY distinction, not a size one.
    Do NOT generalise "we removed the widest domain" into "narrow the next widest".
  - P-030 IS A CLASS, NOT AN INCIDENT. It applies to every LLM emission vocabulary:
    `planner.DOMAINS`, `context_classifier._SYSTEM_PROMPT`'s four vocabularies (already
    compliant -- the house-style reference), the composer's claim contract, and
    `data/yoga_tags_bphs.json`, which GROWS with the wider-BPHS item above. That
    expansion is the next place this defect can recur, into the same ceiling.
  - CHAPTER TITLES ARE OCR-UNRELIABLE. `chapter_index_bphs.json`'s `title_raw` is
    mangled: bphs2_ch48's title says "Nakshatra Dasa" while its body carries the
    Vipareeta trio, and bphs1_ch38 does not exist as a unit at all. VERIFY AGAINST
    CHAPTER BODIES, never titles. This is what made the predecessor handover's map wrong.
  - ROSTER: state the roster only from docs/AGENT_ROSTER.md. Do not restate its count
    anywhere else -- scattering one fact across five files is what caused the drift, the
    same defect class as P-030 in a different medium.

--------------------------------- STANDING RULES ---------------------------------
- PVR/BPHS give the FORMULA (cite the page in code); JHora/AstroSage only grade the
  ANSWER (P-028). Oracle files are never calculation inputs (P-027).
- No doctrine prose in calculation modules (P-029).
- SURGICAL EDITS. Commits are Sulabh's; never commit source without the literal line
  `RATIFIED: commit authorized` in the instructing prompt (#14). Report every hash.
  NEVER rewrite pushed history (#13).
- One prompt, one task. REVIEW before PROCEED -- flag at least one issue before
  approving any edit. SAMPLE before SCALE. HARDEST CASE first.
- A contradiction from Sulabh, or between this handover and the code, is a STOP signal --
  re-verify the SOURCE (branch, freshness, scope), never re-run the same search harder.
==========================================================================================
