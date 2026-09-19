# What the detector is for — the admission contract

**Status: DECISION OF RECORD, S138. Full roster invoked (7 reviewers + Debate).
Items 1–4 below are ADOPTED. Items 5–8 are ADOPTED BUT NOT YET BUILT. The
retirement of redundant rows is BLOCKED by QA until its test set passes.**

Evidence base: `diagnostics/qa_capture/20260919T122618Z.md` (4 questions, 1
chart), `data/sloka_registry.json`, and the S138 roster review.

---

## The question this answers

BPHS has ~97 chapters and many are enumerative tables — ch24 alone is a 12×12
grid of "the Nth lord in the Mth house". If the detector needs a row per
applicable verse, then every chapter brings its own selection question (which
cells, chosen how, tagged where) and a third tagging hierarchy appears
alongside `domain_tags_bphs.json` and `yoga_tags_bphs.json` that has to stay
consistent with both. Forever.

Sulabh raised this against a proposed local fix (re-index the ch24 rows by
chart instead of by topic). The roster rejected that fix as a pattern. This
document is what replaced it.

## 1. The boundary rule — ADOPTED

> **The detector exists to cover the predicate vocabulary's blind spots, not to
> mirror the corpus.**

For a single-placement rule the pipeline already has three independent
mechanisms: the **fact block** states the placement, the **corpus** states the
effect, and a **typed predicate** verifies any claim asserting it. A detector
row is a fourth copy carrying no new information, and it costs ceiling.

This is measured, not asserted. In the S138 capture the interpreter found and
cited 8+ correct ch24 cells unaided, and the predicates then CONTRADICTED and
dropped 4 wrong claims. The detector contributed one of those cells.

The rule is per-**condition**, not per-**chapter**, so no chapter ever needs a
tagging decision and nothing new has to stay consistent with anything.

## 2. Gate order — ADOPTED

**SOURCE-NAMED first. Predicate-redundancy second.**

A predicate-redundancy test alone is defective on its own terms: it filters on
decidability, not provenance. Run against the tree it would **retain all 47
unsourced rows and retire 19 correctly-cited ones** — including every
kendra-trikona raja link, all five Pancha Mahapurusha, all seven Neecha Bhanga
and all three Vipareeta links. It inverts the charter it is meant to serve.

So: a row must name its source before its redundancy is even considered.

## 3. Admission clauses — ADOPTED

A rule is admitted only if **all four** hold.

| # | Clause | Owner |
|---|---|---|
| 1 | Names its source — a sloka id, or an explicitly flagged spec source | Validation Source |
| 2 | Compound, or needs a frame the fact block does not state directly (from-the-Moon, from-the-Sun, navamsa lordship, karaka, set-confinement) | Architect |
| 3 | No combination of existing predicates could decide a claim asserting it — declared as `subsumed_by: [predicate_type, ...]`, empty meaning admitted | Architect |
| 4 | Carries a plain-language `user_text`, authored separately from the diagnostic `reason` | UI/UX |

Clause 3 is **data, not prose**: CI asserts that any row with a non-empty
`subsumed_by` is absent from the emitted fact block, and fails when a newly
added predicate subsumes a live row that was not retired. That is the mechanical
decision procedure Critic required — without it the clause is unfalsifiable.

Clause 4 makes this the enforcement point for translation. No detector `reason`
string reaches `answer_view`; the live capture shipped "11th ruler placed in the
6th" to a user.

## 4. Retirement, not deletion — ADOPTED

A redundant row moves to `retired=True`: **still computed, excluded from the
prompt and its token count, logged to the trace, tests retained.**

QA blocked deletion on three untested failure paths, and the charter is explicit
that QA blocks HIGH items with untested failure paths without exception:

- **Subsumption is asserted, never proven.** A predicate adjudicates only claims
  that *exist*. If the interpreter never emits a claim, silence is not a
  decision, and deleting the row turns a FIRED detection into nothing, silently.
- **The evidence is one chart.** "All ch19/ch15 rows ruled out" is evidence this
  nativity lacks those combinations — the rules *working*. Deleting a longevity
  rule because the developer is not short-lived is selection on the dependent
  variable.
- **The 400-chart zero-regression diff proves that ADDING changed nothing.** The
  deletion diff is a different experiment and has not been run.

Retirement delivers the entire token saving without the irreversible step, and
is the easier fix to revert.

### The deletion gate

Deletion is unblocked only when all of the following pass:

1. Per retired row, on the exact chart that FIRED it in its unit test: the
   predicate vocabulary returns SATISFIED or CONTRADICTED — never UNEVALUABLE.
2. Per retired row, on that chart: the interpreter actually *emits* such a
   claim. No emission → no decision → the row stays.
3. Shadow-mode regression over 400 randomised charts: zero charts where a
   retired row fires and the predicate path produces no claim.
4. The admission test applied to the survivors retains all of them. If it
   retires any, the test is miscalibrated.
5. A stratified sample of 20–30 charts, chosen to FIRE each retired rule at
   least twice, across 3 question types, scored on whether the unaided
   interpreter recovers the same claim.

## 5. The registry — BUILT, NOT WIRED

`data/sloka_registry.json`. The detector had become an **undocumented divergence
registry**: every sloka id, translation divergence, commentary expansion and
editorial reading lived in exactly one place — an evidence string on a row.
Retiring rows would have deleted the disagreements while the disagreements
persisted.

The live proof is ch15 v3. The English reads "the 5th lord"; the Sanskrit reads
*sukha-sthaana-adhipa*, the 4th. The detector resolved to the Sanskrit. In the
capture the interpreter read the retrieved **English** and wrote "not met here"
— while the 5th lord, Mars, is **Exalted**, so under its own reading the
condition *was* met. Detector and corpus disagree in production, and the
interpreter follows the corpus.

**Proposed and not active:** where the registry records a ruling, the ruling
binds over the retrieved translation. Nothing carries a ruling into the prompt
yet, so today the English wins.

## 6. Resolution contract — ADOPTED, NOT BUILT

Clause 2 admits on frame *novelty*. Ephemeris Auditor's unopposed HIGH is that
this is not frame *fidelity*, and the two are not the same precision class:
from-the-Moon and from-the-Sun are sign counting, exact once the sign is right.
Navamsa lordship partitions each sign into 3°20′ cells — a 1° ayanamsa or
birth-time discrepancy flips the cell roughly one time in three. ch19 v5 fires
on a cell-boundary coin flip and reports it with sign-level confidence.

Required: each row declares SIGN / NAVAMSA-CELL / DEGREE resolution; the fact
block gains `ayanamsa_name`, `birth_time_precision` and a per-planet
`boundary_flag`; and **`fired` becomes three-valued — TRUE / FALSE /
UNDECIDABLE-AT-THIS-RESOLUTION.** A binary `fired=false` is lossy: set-confinement
and unreachable-condition rules produce clean negatives that are artifacts of
the coordinate system, and the Silence Gate reads them as refutations.

## 7. Ruled-out transmission — OPEN, deliberately not shipped

Business proposed dropping ruled-out rows from the prompt (~620 tokens, zero
appearances across four answers). **Not done.** The evidence is n=4, and S131
put them there deliberately as "the what-I-am-ruling-out half of an answer the
pipeline could not produce before" — dropping them wholesale removes the ability
to say "you do not have Gajakesari". Business's own refinement is the right
shape: admit a ruled-out row only when the question's domain tags touch it. That
needs a yoga↔domain mapping, which does not exist.

## 8. Outstanding debts

| Debt | Severity | Note |
|---|---|---|
| 47 of 144 rows cite no sloka | HIGH | `sloka_registry.json` → `debts.unsourced_rows` |
| `_adhi` resolved a spec ambiguity from the JHora oracle | HIGH | P-027 breach. Recording it made it auditable, not cured. Re-derive from BPHS ch37 v5, which is in the corpus, or demote. |
| Silences are never typed | HIGH | P-033. Roster's #1 uncontested item. |
| ch35 v8, ch35 v17 readings | OPEN | Need Sulabh's ruling; see the registry. |
| Turn 1 payload: 124,925 tokens, 39.2s, 49 whole chapters | HIGH | Routing, not the detector (which is 0.8% of that turn). |

## What was rejected, and why

**Design A — re-index the ch24 rows by chart.** Rejected as a pattern: it
invents a second indexing scheme alongside the first and every enumerative
chapter then needs a bespoke index, which is precisely the sprawl this document
exists to prevent. Critic's counter — that unaided interpreter recall was
observed *once*, on one model version, and a deterministic floor is cheap — was
overruled but preserved: a golden-chart CI assertion pins unaided ch24 recall to
its observed baseline, and if it ever regresses, chart-indexed emission is
reopened for ch24 only.
