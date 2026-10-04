# Agent Roster — THE SINGLE SOURCE OF TRUTH

Every other file that mentions the roster POINTS HERE and states no count of its
own. Written S136 (2026-09-18) to end a count that had drifted across five files.

**WHY ONE FILE.** The roster count was stated independently in `CLAUDE.md`
Working Style #7, `.cursorrules`, the master build plan §8.6 and two session
logs, and they disagreed (6, 8, 9). That is the same defect as
`diagnostics/KNOWN_PATTERNS.md` P-030 in a different medium: a fact restated in
many places drifts, and no single statement is wrong enough to notice. Adding or
retiring an agent is now a ONE-FILE edit. Do not reintroduce a number elsewhere.

---

## THE ARITHMETIC, RESOLVED

The "9" was an addition slip, not a missing file.

| When | Event | Reviewers | Resolvers | Files |
|---|---|---|---|---|
| Session 8 (2026-05-28) | 6-agent framework established (ui_ux + debate added) | 5 | 1 | 6 |
| Session 9 (2026-05-28) | 6-agent invocation rule LOCKED | 5 | 1 | 6 |
| Session 19 | "9-agent framework (added Ephemeris Auditor, Validation Source)" — `SESSION_LOG_ARCHIVE_S19-S66.md:13` | 7 | 1 | 8 |

6 + 2 = **8**. S19 wrote 9. Every later "9 agents" traces to that one line; no
ninth agent was ever named, chartered or invoked. **The count was wrong, not the
roster** — nothing was lost, and nothing should be dropped to "fix" it.

`.cursorrules` was never updated after S19 and still described the S8 six. Fixed
S136.

---

## ACTIVE ROSTER — 8

Auto-invoke the full roster before any design decision or code change. Do not
wait to be asked. Surface only conflicts or the final recommendation; paste full
agent output only when a genuine conflict needs `debate.md` resolution.

### Reviewers (7) — each holds one perspective and may object

| Agent | Charter | Owns | Trigger |
|---|---|---|---|
| Architect | `.claude/architect.md` | interface contracts, single responsibility, dependency direction, failure modes | new file, schema, pipeline change |
| Business | `.claude/business.md` | user value, cost per query, time-to-value | new file, user-facing change |
| Critic | `.claude/critic.md` | unvalidated assumptions, thresholds without empirical backing, edge cases, AI-reviewing-AI | any code change |
| QA | `.claude/qa.md` | minimum viable tests, crash scenarios, idempotency, fallbacks | any code change |
| UI/UX | `.claude/ui_ux.md` | user-facing output, loading states, jargon, error wording | any frontend or UX change |
| Ephemeris Auditor | `.claude/ephemeris_auditor.md` | astronomical inputs — ayanamsa, timezone, Vedic day boundary, Julian day, precision | any calculation touching time, place or longitude |
| Validation Source | `.claude/validation_source.md` | spec-source vs oracle separation (P-027, P-028) | any formula, any claimed oracle match |

### Resolver (1) — holds no perspective, adjudicates the reviewers

| Agent | Charter | Owns | Trigger |
|---|---|---|---|
| Debate | `.claude/debate.md` | picks ONE winner per conflict, names the overruled objection | reviewers conflict |

Ephemeris Auditor and Validation Source were ratified at S19 but had no charter
file for ~115 sessions, so they could not actually be invoked — they were run
from their titles, when at all. Their charters were written S136 and are
assembled from the laws already ratified for their subject matter (P-022,
P-027, P-028, the S130 precision gap, the S132 sunrise-boundary trap), not
invented.

---

## PROPOSED — NOT ACTIVE, AWAITING SULABH'S EXPLICIT APPROVAL

Per `.cursorrules`: new agent proposals require explicit user approval before
adding. This one is proposed, not added. Do not invoke it and do not count it.

### Disclosure Auditor

**The gap it would close, with evidence from the session that found it.** In
S136 the `technique_method` domain — which shipped the corpus's procedural
chapters into the interpreter payload, exposing how this project computes what
it computes — survived ~130 sessions of full-roster review. It survived because
no agent on the roster owns that question:

- Architect asked whether data flows one way. It did.
- Critic asked whether the threshold was empirically backed. There was no threshold.
- QA asked whether it was tested. It was.
- Business asked whether cost per query was acceptable. It was, until the ceiling.
- UI/UX asked what the user sees. Nothing amiss.

**Sulabh caught it, not the roster.** That is the signal that a perspective is
missing, and it is the same signal that produced Ephemeris Auditor and
Validation Source at S19 — each was added after a real miss exposed a blind
spot. Proposing this one follows that precedent rather than inventing a slot to
make a number come out right.

**What it would own.** Whether an output, payload or prompt exposes how the
system works rather than what it found: internal methodology reaching the
interpreter or the user; procedural doctrine, formulas or thresholds in
user-facing text; a vocabulary offering the model terms only the system needs;
and file/citation paths that map the internals.

**Questions it would always ask.**
- Would answering this question describe the person's life, or the machinery?
- Does this payload contain anything a competitor could reassemble the design from?
- Is this term in the model's vocabulary because a USER needs it, or because the SYSTEM does?
- Could this be extracted one question at a time?
- Does this error message, citation or refusal name an internal path, module or threshold?

**Red flags it would catch.** Procedural corpus regions reachable from a user
question (S136, `technique_method`); a formula or page citation surfaced in
user-facing prose; an internal module or file path in a user-visible error;
a closed vocabulary offering system-only terms (P-030).

**If approved:** write `.claude/disclosure_auditor.md`, add the row to the
Reviewers table above, bump the active count in this file, and add a
`debate.md` precedence line — proposed as: *Disclosure Auditor vs Business:
Disclosure Auditor wins; a cost or shipping argument never overrides an
exposure finding.* Nothing outside this file needs editing.
