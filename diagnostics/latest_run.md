# Read-prompt execution — Gap D1 Kapoor reframe, CLAUDE.md spec source, S75 close block

**Status:** Executed and committed (3 docs commits), NOT pushed per
task instruction ("Do NOT push. Full suite run + push happens after
review.").

## Prerequisite check — FAILED as literally stated, surfaced before proceeding

`.claude/read_prompt.md` instructed:
- "Confirm git log origin/main..HEAD --oneline empty at start" — TRUE.
- "HEAD == 2e34788" — **FALSE**. Actual HEAD at start: `f4505d4`, four
  commits ahead of `2e34788` (`8cd07f8`, `bcbaa37`, `ac8bf64`,
  `f4505d4`), all already pushed to `origin/main` (hence the empty
  `origin/main..HEAD` diff above — that check alone doesn't catch a
  stale baseline hash).

This means Task 1's target file (`docs/KNOWN_DIVERGENCES.md`) already
existed (created by `bcbaa37`, prior session), and CLAUDE.md already
had a "Known Divergences" pointer section (`ac8bf64`) — both predating
this prompt's draft text. Consistent with CLAUDE.md's own documented
behavior for this file: ".claude/read_prompt.md is a MANUAL-PASTE
SCRATCH SURFACE... routinely overwritten" and the standing carry-
forward item "`.claude/read_prompt.md` working-tree drift."

## Additional drift found and surfaced (not silently patched)

1. **Kapoor book path wrong.** Prompt cited
   `project_files/classical_references/_Deepak_Kapoor__...pdf` — that
   directory does not exist anywhere in the repo. Actual file:
   `data/pdfs/[Deepak Kapoor] Astronomy and Mathematical
   Astrology_text.pdf` (verified via repo-wide filename search),
   matching the existing convention (PVR book lives in the same
   directory; CLAUDE.md's Reference Materials section already notes
   `project_files/classical_references/...` "does not exist in this
   repo" from a prior Session-57 correction of the identical mistake).
2. **CLAUDE.md has no "Primary Spec Sources" section.** Closest analog
   is the existing "Reference Materials" section (already carries the
   PVR citation).
3. **SESSION_LOG.md is missing an entire S74 close block**, not just
   S75 — commit `2e34788` ("S74 pyjhora source audit") landed with no
   corresponding session-log entry.

All three surfaced via `AskUserQuestion` before any edit. User
decisions: (1) proceed from current HEAD, (2) cite the real
`data/pdfs/` path rather than moving the file, (3) add Kapoor into the
existing Reference Materials section rather than inventing a new
heading, (4) leave the S74 gap as a flagged carry-forward item, not
backfilled in this pass.

## Edits made

- `docs/KNOWN_DIVERGENCES.md` — Gap D1 root-cause reframed to Camp Y
  (Kapoor Ch IX pp 115-117) vs Camp X (JHora/AstroSage/Drik
  undocumented Moon correction); prior FLG_NOABERR hypothesis preserved
  inline, not deleted. Reference line added citing the corrected
  `data/pdfs/` path.
- `CLAUDE.md` — Reference Materials section: Kapoor book added as
  second primary spec source alongside PVR (Vimshottari Ch IX,
  Shadbala/Bhava Bala Ch XVI-XIX, ayanamsa table Ch IV; PVR stays
  authoritative for interpretive doctrine/yoga detection). "Known
  Divergences" section verified already correct from a prior commit —
  no change needed there.
- `SESSION_LOG.md` — S75 close block appended (full content: Ayanamsa
  lead falsification, year_days=365.256363 confirmation, Camp Y/Camp X
  split, oracle reclassification, S76 open items, carry-forward). Note
  added flagging the missing S74 block rather than backfilling it.

## Commits made (docs-only, exempt from RATIFIED-token rule per
CLAUDE.md Working Style #14)

1. `68251e3` — docs(divergences): reframe Gap D1 with Kapoor Camp
   Y/Camp X citation
2. `753fcff` — docs(spec): add Kapoor book as second primary spec
   source
3. `63ce795` — docs(session): S75 close block — Vimshottari row-0
   investigation + Kapoor citation

## Final `git status --porcelain`

```
 M .claude/read_prompt.md
```

(Pre-existing dirty state from before this task started — this file
was not touched by this run; left as-is, not part of this task's
scope.)

## Not done (per task's own instruction)

- No `git push` — explicitly deferred to post-review.
- No full test suite run — explicitly deferred to post-review ("Full
  suite run + push happens after review").
