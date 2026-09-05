# ASTRO AGENT — S126 HANDOVER (written at S125 close, 2026-09-05)

> **Tombstone this file the moment S126 closes.** A stale handover is worse than
> none, because it is confidently wrong. That is why `claude_handover_S97.md`
> was reduced to a tombstone this session.

MODEL: Opus for the design decision below. Sonnet 4.6 for any Claude Code
implementation. State the model on the first line of every Claude Code prompt.

## READ THIS ORDER, THEN TRUST IT — do not re-derive

1. `CLAUDE.md` — Current Session Focus + Locked Decisions. **AUTHORITATIVE.**
2. `SESSION_LOG.md` § S125 — the evidence behind every number below.
3. `ASTRO AGENT — MASTER BUILD PLAN.md` — the map (rewritten 2026-09-05; the
   pre-2026-09-05 version was frozen at Session 42 and described a system that
   no longer exists — never cite it).

Everything in those three is settled. Re-measuring costs money and re-arguing
costs the session.

## WHERE THINGS STAND

**The POC PASSED.** The five-stage pipeline — Planner → Calculator → Retriever
→ Interpreter → Silence gate — answered real questions end to end, grounded,
cited, chart-specific, with honest refusal where material ran out. Zero ghost
citations in every run on record.

| Track | State |
|---|---|
| A — Calculation engine | Broad, but **16 modules are docstring-only stubs** |
| B — Palm rules engine | **COMPLETE for V1 scope.** Not a backlog item |
| C — BPHS text pipeline | Proven end to end. **Selection is its open blocker** |

Uncommitted, built and tested, awaiting a ratification token:
`agent/astro/planner.py`, `agent/astro/silence_gate.py`, and their 92 tests.

## CLOSED — DO NOT RE-OPEN

- **Palm is IN V1 and is DONE.** Four rule files (`head_heart`, `life_line`,
  `fate_line`, `mounts`) are the entire V1 scope. Sun / Health / Mars / Marks /
  hand-types / fingers / nails were **scoped out at S96**; Marriage lines and
  Thumb are **parked**. Reasons are in
  `data/palm_rules/unauthorable_register.json`. **Read that register before
  calling any palm chapter "remaining" — S125 did not, and was wrong.**
- **S124 open item 1 is FALSE and closed.** Domain tags are NOT title-inferred.
  Zero of 100 units. No re-read budget is needed.
- **Both S124 live bugs are closed by construction** (child-career derives the
  2nd via bhavat-bhavam; there is no substring scope guard, and a test forbids
  its return).
- **`calc_router.py` is not the planner's fallback, deliberately.** It emits
  calculation domains, a different type in a different stage.
- **Wide selection is dead** (298 of 304 segments contributed zero citations).
  **Strict is dead for timing** (14 segments is the hard ceiling at *any* house
  list). Do not re-run either probe.

## MEASURED — cite these, never re-derive

- `approx_tokens` undercounts real tokens by **1.61–1.66×**. Size payloads
  **only** from `prompt_tokens`. Never from `approx_tokens` or chars/4.
- gpt-4o **TPM cap is 30,000** at this account tier and binds long before the
  128k context window. Tier-specific; advisory, not a code problem.
- **Only 3 of 10 subjects** are workable today: career, children, health.
  Root cause: `extract_relations` reads one sentence shape, so 90–95% of verses
  are invisible to it in every domain.
- **gpt-4o-mini never cites a verse** — whole-chapter units only, every run.
  gpt-4o does, and refuses correctly where mini invents Barnum claims.

## NEXT TASK — SELECTION (ratified order: selection BEFORE calculations)

Broaden the relevance signal beyond the single "the Nth lord is in the Mth"
sentence shape. This is the one V1 blocker of its size, and it is a one-file
problem gating 7 of 10 subjects.

Calculations come **after**, not before: those 16 modules are stubs *because
those calculations were hard to get right*, each carries the 4-reference-chart
validation protocol, and doing the slow item first leaves most of the corpus
unreachable for months.

**Build this INTO the selection arc, do not defer it:** selection can only be
*measured* on the eight non-timing subjects, because `timing_dasha` cannot be
validated until `vimshottari` exists. Design the timing relevance signal
(**planet and period names, not houses**) now, ship it unmeasured, validate the
day `vimshottari` lands. Otherwise selection gets tuned on what is measurable
and reopened later.

Run the 9-agent pass before writing any selection code.

## HOW S125 WENT WRONG — the four traps, named

1. **Trusted a stale document.** The old MASTER BUILD PLAN was 80 sessions
   behind. Check a file's date against `SESSION_LOG.md` before believing it.
2. **Re-litigated a closed decision.** Called palm chapters "remaining" from a
   forward-looking S95 list, without checking that S96 had scoped them out.
   **Search the registers before declaring anything unfinished.**
3. **Put an invented expected value in a verification prompt.** Asked for
   `grep -c` and "expect 4"; the true count was 3 in *both* versions, so the
   check could never have discriminated. Working Style #16: a verification whose
   result is predicted in the prompt buys nothing.
4. **Recommended a fix before measuring it.** Proposed wiring planner houses
   into selection; measurement showed it buys 1–2%. **Measure, then recommend.**

## OPEN, SMALLER

- Planner's live house lists run thin (`[7]` for a marriage-timing question). A
  widening instruction was added to `SYSTEM_PROMPT` but its effect is
  **unmeasured** — the run that would have tested it used a stale file copy.
- **Writes to `agent/astro/planner.py` were silently reverted twice** between
  commits during S125. Cause unknown, not investigated. If a change you make
  appears to vanish, this is why — check the file's *values*, not a grep count.
- Privacy: `data/default_user/` and 5 `data/sessions/*.json` are tracked in a
  public repo against the no-storage lock. Needs a second history rewrite.
- `requirements.txt` is a one-line stub in what is now the distribution artifact.
