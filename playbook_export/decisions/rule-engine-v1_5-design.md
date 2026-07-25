# V1.5 Rule Engine Foundation — Design Proposal (Speculative, Unratified)

**Recorded:** 2026-07-25, docs-only, drafted this session
**Status:** PROPOSAL ONLY — NOT a ratified design-chat decision. No
corroborating session exists in SESSION_LOG.md or CLAUDE.md as of this
writing; this content was authored now, not transcribed from a prior
"S73-adjacent" design chat. Treat everything below as a candidate
architecture to be reviewed and ratified (or rejected) in an actual
future design-chat session, not as locked history.
**Trigger to open V1.5 (proposed):** all four prerequisites green (see
below) — proposed gating criteria, not yet agreed.

## Purpose
Generalize the per-domain assembler pattern before V2 scales it 10x.
Prevents second-system syndrome by deriving schema from N shipped
hand-coded domains, not designing top-down.

## Prerequisites (proposed — ALL would need to be green before V1.5.1 begins)
1. V1 shipped end-to-end (palm UI gate implemented per S72 planned
   spec; all 8 routable domains stable in production)
2. Ashtottari dasha wired (4th post-lock hand-coded domain data point;
   Yogini was 3rd at S73)
3. D10 + D7 divisional chart modules built (unblocks multi-chart
   ChartContext axis)
4. Palm revisit outcome decided (shapes T4-interpretive tier that rule
   engine must accommodate)

## Candidate Design Decisions (proposed, not locked)

### D1 — Two-tier engine, not one
Tier A = YAML-driven, for linearly decomposable domains (progeny
gender, dasha lookups, koota tables, house-lord-sign classifications).
Tier B = Python composite, for graph/pattern/multi-chart domains (yoga
detection, argala, Jaimini karaka schemes, cross-varga references).
Shared contract: both consume DomainChartProfile, emit DomainAnswer +
structured trace, cite PVR page + JHora fixture per step.
Rationale: linear step-chains cover ~30% of V2 domains; forcing yogas/
argala/karaka schemes into YAML would explode the op registry until
it's Python written in YAML.

### D2 — Confidence: ordinal tier derived from structured signals
No fabricated numerics. Four deterministic signals:
- source_count: 1 | 2 | 3+ classical sources
- oracle_agreement: none | jhora_only | jhora+astrosage
- exception_depth: 0 | 1 | 2
- signal_axis_coverage: subset of {houses, lords, karakas, dasha, vargas}
Tier derivation table (engine-level, not per-rule):
- T1: source_count>=2 AND jhora+astrosage AND exception_depth=0 AND
  >=2 axes converge
- T2: source_count>=1 AND jhora_only AND exception_depth<=1
- T3: everything below
User-facing surface (2-3 lines): counts + names only, no percentages.
Full detail lives in debug trace.
Rationale: classical "eka/dvi/trini pramana" (one/two/three
testimonies) framework — reinvent not invent.

### D3 — Multi-chart ChartContext v2 with signal-axis discipline
Add vargas axis to ChartContext: {D1: existing, D9: NavamsaChart, D7:
pending, D10: pending, jaimini: {karakas, arudhas}, panchanga,
dashas}. Lazy-computed, not eager.
Kernel signatures gain chart_ref: dignity_of(planet, chart='D1'),
house_from(chart, point, n), lord_of_house(chart, n).
YAML rule steps declare signal axis (houses/lords/karakas/dasha/
cross-varga). Engine trace validator warns when a rule claims N
independent signals but >=2 steps share the same axis (prevents
axis-collapse fabrication — three views of the same underlying
condition presented as three signals).

### D4 — Rule ratification bar
Max bar for V1.5 flagship domains (progeny, longevity, wealth): PVR
page + JHora fixture + AstroSage parity + validation against 4
reference charts. ~3-4 hours per rule.
Std bar for supporting rules: PVR page + JHora fixture. ~1 hour per
rule.
Min bar (PVR page only) NEVER — that's the AstroSage-only trap.

### D5 — Sequencing: rule of three (retrospective derivation)
Do NOT design engine top-down. Sequence:
1. V1 ships + Ashtottari wired (4th hand-coded domain post-S19 lock)
2. Retrospective analysis of 4-8 shipped domain assemblers (what
   genuinely repeats vs incidentally similar)
3. Tier A engine + schema derived from observation
4. Retrofit-test schema against all shipped domains before touching V2
5. Migrate marriage_compat first (hardest — has documented PVR/
   AstroSage divergence, forces citation-block design early)
6. Tier B contract designed in parallel; not urgent since V2
7. Populate V2 rules via YAML

## Rejected Alternatives (candidate reasoning, not a ratified record)
- Single-schema linear YAML for all domains — ~70% of V2 domains
  resist linear decomposition; would force op registry explosion.
- Numeric confidence percentages (base + boost/penalty) — fabrication
  risk, path (c) failure mode class (S22-S23 lock).
- Building engine now, before V1 ships — premature abstraction, same
  class as path (c). Rule-of-three violated at N=3 hand-coded domains.

## V1.5 Sub-Phase Estimate (rough, proposed)
- V1.5.1: Retrospective analysis of shipped domain assemblers (1-2 sessions)
- V1.5.2: Two-tier engine contract design (2-3 sessions)
- V1.5.3: Multi-chart ChartContext v2 + signal-axis validator (1-2 sessions)
- V1.5.4: Ordinal confidence derivation module (1 session)
- V1.5.5: Retrofit migration of marriage_compat (1-2 sessions)
- V1.5.6: First V2 domain via YAML — progeny_gender (1-2 sessions)
Total: 7-12 sessions.

## Agent Review Note (corrected roster)
This project's standing agent roster is 6 (CLAUDE.md Working Style
#7 / Reference Files table): Architect, Business, Critic, QA, UI/UX,
Debate (`.claude/architect.md`, `business.md`, `critic.md`, `qa.md`,
`ui_ux.md`, `debate.md`). This proposal has **not** been run through
that 6-agent pass yet — doing so is a prerequisite before any of the
above moves from "candidate" to "locked." An earlier draft of this
document claimed a "9-agent pass" including "Parashara agent,"
"Ephemeris/Calc Auditor," and "Validation Source" — none of those are
agents that exist in this project (a single "Parashara dissent" is
logged once, in SESSION_LOG.md's S65 entry, on an unrelated palm/
kundali cross-verification decision — it is not a standing reviewer).
That claim has been removed rather than repeated here.
