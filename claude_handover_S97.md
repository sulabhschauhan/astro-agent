# Claude Handover — S97 close

**Note on this file's precedent:** the instructing prompt for this handover said to
follow the structure of an existing `claude_handover_S94.md`. That file does not exist
anywhere in this repo — checked the working tree, a full-repo filename search, and
`git log --all` across every branch for any file ever named `claude_handover*`; none
found. This file therefore follows the STRUCTURE given directly in the instructing
prompt itself (which was complete and specific enough to write from), not an actual S94
precedent file. Flagging this rather than silently inventing a claim that a prior
handover file existed.

## State at handover

- Branch `wip/interpretive-pilot`, HEAD **`bd39836`** (verified via `git rev-parse HEAD`
  at write time — NOT `f9f4bbe`, which was the instructing prompt's guess; `f9f4bbe` is
  2 commits behind current HEAD, missing the SESSION_LOG consolidation + stale-comment
  fix + CLAUDE.md sync work).
- **Pull the branch first.** Then read (do NOT re-derive from scratch):
  - `CLAUDE.md` — Locked Decisions, the "Rule Authoring & Audit Architecture" section's
    Fate status line, and the "Palm Diagnostic Principles" learnings (item 7 covers the
    Ending_Point/Position bug class and its now-built CI gate).
  - `SESSION_LOG.md`'s consolidated `## S97` entry (near the file's end, right after
    `## S96`) — the single canonical account of this whole arc; the 5 fragmented
    `S97`/`S97b`/`S97c`/`S97d`/`S97e` entries that used to exist were consolidated into
    this one entry and no longer exist as separate headers.
  - `data/palm_rules/_doctrine/doctrine_fate.md` — the Fate line's full doctrine
    inventory (Step 0 of `PALM_PIPELINE.md`'s checklist), now persisted on disk.
  - `data/palm_rules/_doctrine/relation_census.md` — the relation-machinery demand
    census + sized build recommendation (see NEXT WORK below).
  - `data/palm_rules/_doctrine/PALM_PIPELINE.md` — the frozen 0-7 authoring checklist
    every line chapter follows; still the governing process document, unchanged this arc.

## DONE — do NOT re-do or re-investigate

- **Fate line v1 COMPLETE**: 15 rules LIVE + verified (FT_001-FT_015, Sulabh,
  fulltext_exact, 2026-08-22), 4 rows parked (FT_P01 generic-target, FT_P02 gender
  do_not_author, FT_P03 dual-branch, FT_P04 incoming-branch). Do not re-author, do not
  re-verify, do not re-run the fidelity-verification worksheet.
- **broken_overlapping continuity token / Plain-of-Mars ORIGIN / Saturn-finger LENGTH
  EXTENT**: all 3 wired registry→vision→rule end to end, committed. Not open work.
- **Ending_Point→Position dead-rule bug**: FIXED and CI-GATED. The suite now enforces
  zero-`UNEMITTABLE` antecedents across every `data/palm_rules/palm_rules_*.json` file
  automatically (`tests/interpretive/test_vocab_reachability_scan.py`). Do not
  reinvestigate this specific bug; if authoring NEW relation rules, the gate will catch
  this whole class automatically — treat a red `test_all_rule_files_have_zero_
  unemittable_antecedents` as the signal, not a reason to re-derive the diagnosis from
  scratch.
- **Malformed-JSON extraction crash**: FIXED (`_call_llm_and_parse()` in
  `observation_extractor.py`, bounded resample on parse failure) + 3 regression tests.
  Not open work. (Graceful-degradation-vs-crash on final exhaustion after all resamples
  fail is a DELIBERATELY left-open product decision, not a bug — see Open items below
  only if that decision ever needs revisiting.)
- **S96 mount-alias emission**: FINISHED + committed (`_FEATURE_ALIAS`, 19 keys, 17
  mapped to 15 distinct ontology features); its 2 previously-stale tests are fixed and
  green.
- **relation_census.md**: the sized build decision is ALREADY MADE (see NEXT WORK). Do
  NOT re-run the census, do NOT re-read all 9 line chapters again — the counts are
  final for this decision (caveated ±1 per the file's own provenance note, which is
  fine for a build-sizing decision, not a reason to re-derive them).

## NEXT WORK (the actual pipeline item)

Build the relation channel, highest-yield-first per `relation_census.md`'s sized
recommendation:

1. **Pattern C (convergence/joins) FIRST** — 6 cases across 4 chapters (Life, Head,
   Heart, Health), the best-DISTRIBUTED in-scope pattern of the four. Building it also
   immediately unlocks Fate's own already-parked `F025b` the moment it lands.
2. **Then Pattern A (incoming branch)** — 4 cases, 3 chapters, all in-scope; the
   narrowest conceptual fix (flip/extend `BRANCHES_TO`'s directionality), and it
   directly unblocks `FT_P04`.
3. **Pattern D (dual/multi target) LAST of the in-scope three** — 3 cases, the most
   invasive schema change (a field accepting 2+ simultaneous targets), lowest yield.
4. **Pattern B (crossed/stopped-by) is likely NEVER BUILT** — 11 raw instances, but 9
   of 11 are the ALREADY-SCOPED-OUT Hindu ray-line / Line of Influence subsystem
   (`unauthorable_register.json`'s `line_life` L_P09 entry, CLAUDE.md S96 lock); real
   in-scope demand is only ~2 (Marriage). Do not build B's machinery on the strength of
   its raw count without re-confirming this scope-out is still the standing decision.

**START with a DESIGN-IN-CHAT pass for the C convergence primitive** — a symmetric
"line A meets line B [at location L]" observation shape. This is an architecture design
decision (new observation/rule primitive touching the ontology registry, the vision
prompt, the extractor, and the rule-matching engine) — per the project's own working
laws this is an OPUS, design-in-chat-first task, NOT a paste-and-run Claude Code prompt.
Do not jump straight to authoring rules or editing `observation_extractor.py` /
`palm_processor.py` for this. The design pass should settle: what the new
attribute/relation shape looks like in the ontology registry, how the vision prompt
elicits it without drifting HEAD/HEART/LIFE/FATE's existing menus, and how
`palm_rules_table.match()`'s `targets` param (or a new param) would carry a
symmetric two-line relation rather than today's one-directional `{feature: {attribute:
landmark}}` shape.

## Open items / caveats (known, not bugs to rediscover)

- **Real-image vision reliability is unproven across all 15 Fate rules** — only ONE
  real photograph (`data/test_images/palm_right_test.jpg`) has been dogfooded against
  the live rule set (the run that caught the Ending_Point/Position bug). Every
  relation/extreme-value token added this arc (`broken_overlapping`, Plain of Mars
  origin, `cutting_into_finger_of_Saturn` extent) is synthetically validated only
  beyond that one run. Standing caveat, not a blocker, not new information to
  rediscover.
- **FT_006 carries a LOWER-CONFIDENCE flag** — Saturn-finger extent vision reliability
  specifically is untested; the flag stays alongside its UN-HELD status, unchanged.
- **FT_009's cross-line-index declaration is still absent** from
  `_doctrine/cross_line_index.md` (per that file's own README requirement for
  cross-line rules) — checked directly as of the S97 consolidation, confirmed still
  open, not touched. Small, not urgent, but real debt.
- **Throwaway diagnostics scripts are untracked scratch, safe to ignore or delete**:
  `diagnostics/validate_ending_point_fix.py`, `diagnostics/validate_fate_006_015.py`,
  `diagnostics/fate_verification_worksheet.md`, plus several untracked cheirognomy/
  soft-anchor scripts under `scripts/` from an unrelated in-progress thread — none of
  these are wired into the test suite or referenced by any committed code; they were
  one-shot proof scripts for the arc described above, not durable tooling.

## Working laws (unchanged)

Design-in-chat-first for architecture decisions; one-file-one-task discipline per
Claude Code prompt; report-first to `diagnostics/latest_run.md` (overwrite-only per
run, never append); RATIFIED-token gate before any source-code commit (docs/diagnostics
commits exempt); model routing — Sonnet for build/implementation work, Haiku for
docs+git-only tasks, Opus for architecture/multi-layer design; hardest-case-first
testing; no tolerance-widening on thresholds without evidence; the 9-agent roster stays
silent unless a genuine conflict needs `debate.md`; always verify against the repo, not
memory, before concluding a fact is still true.
