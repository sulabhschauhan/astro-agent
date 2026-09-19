# ANSWER VERIFICATION ARCHITECTURE

Design of record, S137. Supersedes the prose-matching verification described in
the S129b / S130 silence-gate entries. Read with `docs/ANSWER_PATHS.md`.

Status: **Phase 0 complete and passing.** Phases 1-3 designed, not built.

---

## 1. The objective this serves

Answer everything we correctly can. Two failure modes bound it:

- **confident-wrong** — we assert what the chart contradicts
- **silent-miss** — we hold something true and do not say it

Every rule below is judged against those two and nothing else.

## 2. The defect this replaces

Verification used to ask a claim's **English prose** whether it applied to this
chart. `silence_gate._CONDITION_RE` matches `<Nth> lord ... in the <Mth>` and
nothing else; `_PLANET_CONDITION_RE` is advisory with no drop authority.

`capability_gate.FACT_BLOCK_PROVIDES` declares **eight** fact classes. Exactly
**one** was enforceable. The other six — `house_lords`, `aspects`, `dignity`,
`navamsa`, `yogas`, `ascendant_sign` — had **no verifier at all**. Every
fact-block widening since S130 added answering power and zero verifying power,
and nothing anywhere recorded that.

It stayed invisible because UNDETERMINED **failed open**: unjudgeable claims
shipped anyway. The S136 composer flip made unjudgeability consequential for the
first time. On the first live composed run
(`diagnostics/qa_capture/20260918T193426Z.md`) **8 of 12 claims were demoted as
"unverified"**, and **five named yogas the detector had already computed as
FIRED** (`adhi`, `vesi`, `nipuna`, `kendra_trikona_1_5`, and the 1st-5th link
again). The system computed a fact, then told the user it was speculative.

**The inversion is the bug.** The chart is computed exhaustively and
deterministically. A precondition should be evaluated against the *fact block*,
never pattern-matched against its own grammar.

This is the architecture the palm side has had since S95:
`agent/interpretive/palm_select.match()` matches typed
`Antecedent(feature, attribute, value)` triples against an observed hand state,
with a vocabulary contract and a reachability CI gate. The astro half solved the
same problem with regex. This brings the mature half across.

## 3. The design

### 3.1 The typed claim contract

A claim becomes:

```json
{
  "statement": "...",
  "segment_ids": ["ch37_s002"],
  "preconditions": [{"type": "yoga_fired", "yoga_id": "adhi"}],
  "polarity": "positive|negative|mixed",
  "conditionality": "unconditional|conditional",
  "subject": "career"
}
```

The interpreter already reasons about preconditions — it writes them into the
prose and into `silent_on`. It is being asked to **declare** what it already
does, in a closed vocabulary.

### 3.2 Predicates, one family per fact class

`agent/astro/predicates.py`. Fifteen types over the eight declared fact classes,
each carrying a **gloss and a scope guard** (Working Style #35 / P-030), both
asserted by test.

| predicate | fact class |
|---|---|
| `lord_in_house` | `lord_house_map` |
| `house_lord_is` | `house_lords` |
| `planet_in_house`, `planet_in_sign`, `planet_dignity` | `planet_positions` |
| `conjunction`, `aspects_house`, `aspected_by`, `mutual_aspect` | `aspects` |
| `navamsa_sign`, `navamsa_dignity` | `navamsa` |
| `ascendant_is` | `ascendant_sign` |
| `yoga_fired`, `yoga_ruled_out` | `yogas` |
| `unfittable` | — (escape hatch) |

**`unfittable` is the S124 escape hatch.** A precondition the vocabulary cannot
express is *declared and measured*, not absorbed. Its rate is the health metric
for the vocabulary itself.

**No degree-level predicate exists, deliberately** (Ephemeris Auditor; S130
accepted gap). Exaltation tables carry signs, and `meta.jd_ut` /
`meta.asc_lon_sidereal` are rounded, so a `planet_degree(...)` predicate would
look evaluable and be false at the precision it implies. Enforced by test.

### 3.3 Three-valued outcome, one drop authority

```
SATISFIED     the fact block CONFIRMS the precondition
CONTRADICTED  the fact block REFUTES it
UNEVALUABLE   no evaluator for this type, or the fact is absent
```

**The routing law — the whole design in four lines:**

- `CONTRADICTED` → **drop.** The only drop authority in the system.
- `SATISFIED` → ship, lead with these.
- `UNEVALUABLE` → **ship, hedged, and record.** Never a drop.
- Nothing downstream may drop or demote on verification status again.

Roll-up: any predicate CONTRADICTED sinks the claim; all SATISFIED (and at least
one) is SATISFIED; anything else is UNEVALUABLE. **A claim stating no
precondition is UNEVALUABLE, never SATISFIED** — silence about a precondition is
not evidence that one holds.

This is S124's *fail safe means fail to zero, not to something wrong* carried
into verification, where it had never been applied. A filter that cannot judge
must keep.

### 3.4 The three registers collapse into one

Before: `_fact_block` computes, `FACT_BLOCK_PROVIDES` declares what we answer
from, and **nothing** declared what we can verify. That asymmetry is exactly how
six classes drifted into unverifiability unnoticed.

After: `PREDICATE_FACT_CLASS` binds every predicate to the
`FACT_BLOCK_PROVIDES` key it reads, asserted by test. Adding a fact class means
declaring its predicates in the same change. The gap becomes impossible to
create silently.

### 3.5 The composer narrows

It gets typed claims with typed verdicts and does exactly two things: **order**
and **phrase**. It is no longer the arbiter of what survives.

- Only legal demotion: `redundant_with: <claim_id>`, and that claim must have
  shipped. Mechanically checked; auto-restore on violation, reusing the coverage
  machinery that already exists.
- **Relevance becomes a rank, not a drop.**

### 3.6 The answer becomes two-tier

```
LEAD              the verdict, plain English, <= 150 words (UI/UX limit binds HERE only)
THE MAIN PICTURE  SATISFIED claims, ranked
ALSO IN YOUR CHART  UNEVALUABLE claims, honestly hedged (collapsed)
WHAT DOESN'T APPLY  ruled_out verdicts
```

The last section is free today and unused: 20 ruled-out verdicts were computed
for the live chart (Gajakesari, Sarala, all five Pancha Mahapurusha, Mangal
Dosha) and none reached the user. That is the missing counterweight recorded at
SESSION_LOG S136 §12 item 6.

## 4. Phase 0 result — MEASURED, not projected

`scripts/predicate_coverage_probe.py`, run against the twelve claims of
`20260918T193426Z.md`. No model call; costs nothing to re-run.

| metric | result |
|---|---|
| typed coverage | **95.7%** (gate was 80%) |
| claim verdicts | 9 satisfied · 2 contradicted · 1 unevaluable |
| recovered (live composer demoted, typing confirms) | **claims 3, 5, 6, 7, 10** |
| correctly dropped (chart refutes) | claims 4, 9 |
| ships hedged, never dropped | claim 8 |

Two findings beyond the gate:

- **Claim 9 was a real confident-wrong that the old gate could not see.** The
  interpreter asserted "Mercury aspects Sagittarius (the ascendant)". Mercury
  aspects house **10**, not house 1. The live composer dropped it — for the
  wrong reason, as "unverified". Typed verification drops it for the right one.
- **Claim 8 is the honest middle.** It names the *Atmakaraka*; the detector's
  `raja_sambandha_lagna` keys on the *Amatyakaraka*. Typed as `unfittable`, it
  ships hedged instead of vanishing silently.

Net on this question: **4 shipped → 9 shipped + 1 hedged + 2 correctly dropped.**

**Limit of this evidence, stated plainly.** The probe's precondition table is
hand-written from each claim's own prose; a human/agent stands in for the
interpreter. It proves the **vocabulary and evaluators are sufficient**. It does
NOT prove the interpreter will type claims correctly — that is Phase 1's
question and needs a live run. Per Working Style #5 this mapping has no human
review yet; each row carries its claim's own words so the check is quick.

## 5. Migration

| Phase | Work | Gate | Cost |
|---|---|---|---|
| **0 ✅** | registry + evaluators + probe | typed coverage >= 80% | $0 |
| 1 | interpreter emits `preconditions` alongside prose; gate uses typed when present, regex when absent | no regression vs today | 1 live run |
| 2 | composer consumes typed verdicts; closed demotion vocabulary; two-tier answer | the career question returns ~9-10 claims incl. Adhi/Vesi/Budha-Aditya | 1 live run |
| 3 | retire the regex readers; add WHAT DOESN'T APPLY | typed coverage holds | 1 live run |

Phases 1-3 are additive and individually revertible. Prose is never removed, so
a failure at any phase falls back to the current rendering.

## 6. What this amends

- **S131's "the composer decides what matters" is NARROWED.** It decides order
  and words, not what survives. A real amendment to a lock.
- **The S129b regex readers become a fallback, then retire.** The
  "promote the advisory planet reader on a measured rate" carry-forward
  dissolves — there is no advisory reader in the end state.
- **The register asymmetry is abolished**, not documented.
- **S124's never-narrow doctrine is EXTENDED to the presentation layer**, where
  it had never been applied — which is precisely how the defect shipped.

## 7. Residual risks

1. **A fabricated precondition that happens to be SATISFIED ships unchallenged.**
   A contradicted one is caught by construction; an invented-but-true one is
   not. Mitigation is the existing citation discipline plus periodic spot-audit.
   This is the honest ceiling of the design.
2. **Claims stating no precondition** are UNEVALUABLE forever. Correct: they
   ship hedged in tier 2.
3. **Dashas / timing are not in the fact block at all**, so timing questions
   remain a capability-gate decline. Unchanged by this design.
4. **Interpreter completion tokens rise.** Measurable in Phase 1; small against
   84k prompt tokens.

## 8. Roster

Architect, Critic, QA and Validation Source aligned. Ephemeris Auditor
contributed the binding no-degree-predicate constraint (§3.2).

**Conflict 1 — UI/UX vs Critic** ("150 words, no wall of bullets" vs "nothing
may be dropped"). *Resolved by surface*: the 150-word limit binds the **lead**
only; tier 2 ships collapsed. Neither overruled — they were arguing about
different things.

**Conflict 2 — Business vs Architect** ("defer, cost and latency" vs "a patch
per fact class is unbounded"). *Architect wins.* No new LLM call is introduced;
the latency objection is real but orthogonal (30s of the 44.85s is the
interpreter, untouched here). **Overruled objection, named:** Business's "defer
until after ship" — ground being that the defect is user-visible content loss on
the product's core promise.

Disclosure Auditor is proposed, not active, and was not invoked. Had it been:
typed preconditions are internal machinery and must never surface in
user-facing text or citations.
