# Reconciliation Audit — Transferable Learnings (palm → astrology)

Captured so the same mistakes are not repeated when the astrology (Vedic) engine goes
through the same book↔rules↔evidence reconciliation. These are process learnings, not
palm-specific facts.

---

## 1. The "three vocabularies" drift is the root failure mode

Any citation-first interpretive engine has three separate vocabularies that must stay
aligned, and they drift silently:

- **Source doctrine** — what the classical text actually says (the meanings).
- **Rule antecedents** — the tokens a rule keys on.
- **Evidence/observation tokens** — what the extraction layer actually produces.

A reading only appears when all three align for a given configuration. When they drift,
the engine goes silent or fires the wrong thing — and **silence looks identical whether
the cause is "no doctrine exists" or "the three vocabularies disagree."** That
ambiguity is what let real coverage failures masquerade as correct honest-silence.

**Astrology parallel:** doctrine (PVR/Parashara) ↔ rule/yoga antecedents ↔ the exact
computed evidence (planet in sign/house, degrees, strengths). The evidence layer is
*exact* (no vision fuzziness), so the descriptor-coarseness problem below is smaller —
but the **rule-vs-book completeness** and **attribute-name alignment** problems are
identical and will bite the same way.

## 2. Silence is a diagnosis, never a verdict

The governing error: concluding "the book doesn't cover this / silence is correct"
**without exhaustively checking the source against the actual observed configuration.**
Twice, plain-looking features were called "unauthorable" when the book in fact spoke to
their specific structure (heart "should be deep, clear, well colored" p156; the entire
head-line **slope** doctrine p146).

**Rule:** before ruling any observation unauthorable, run the full check —
(a) enumerate every source statement touching that feature's *actual* structure,
(b) confirm no rule exists, (c) confirm no rule exists-but-mismaps. Only after all
three is "unauthorable → bare observation" a legitimate verdict. Use a critic pass to
generate structural hypotheses ("what could a downward-sloping line match?") and test
each against the source, rather than reasoning from a generic "is there a baseline."

## 3. Attribute-name mismatches are a recurring, silent bug class

Two instances found, same shape: the evidence layer and the rule layer use different
names for the same property.
- **Width vs Thickness** (line thinness) — fixed.
- **Slope vs Direction** (line angle) — open.

Each silently drops real claims. **Rule:** maintain a single canonical attribute
vocabulary, and add a reconciliation check that flags any (a) rule antecedent whose
(feature, attribute) is never produced by the evidence layer — a *dead rule*, and
(b) evidence token no rule ever consumes — a *dead token*. Both are drift signals.

**Astrology parallel:** the koota/strength/dignity tables and the yoga-rule antecedents
must use the same names and value encodings as the computed evidence (e.g. an exaltation
flag, a house number, a dignity label). The Gana-table 0-vs-1 bug was this same class —
a value-encoding mismatch between the lookup table and the source standard.

## 4. Authoring must be exhaustive against the source, tracked per-configuration

The head slope doctrine was **half-authored**: the `straight` case got a rule, the
(richer) sloping cases were dropped. Nobody noticed because nothing tracked
"every source statement → a rule or an explicit unauthorable verdict."

**Rule:** authoring is complete only when *every* "when X → means Y" statement in a
chapter maps to either a verified rule or a recorded unauthorable-gap entry. Partial
coverage with no record of what was skipped is the failure. Build the chapter's
doctrine inventory first (mechanical extraction of every conditional statement), then
author against that checklist — do not author from memory or from the "interesting"
configurations.

## 5. The extraction layer can be the bottleneck, not the rules

For the head line the descriptor was *narrower* than the rule book — ~15 rules were
un-fireable on any hand because the descriptor never reports line topology. Authoring
more such rules would have produced more dead rules.

**Rule:** before authoring rules that depend on an evidence field, confirm the evidence
layer actually produces that field. Coverage of the *rule book* is meaningless if the
*evidence* can't trigger it. Reconcile evidence-capability first.

**Astrology parallel:** less acute (the compute layer can produce almost any exact
fact), but still applies — confirm the pipeline actually surfaces a given quantity
(e.g. a specific Ashtakavarga bindu count, a specific Bhava Bala) before writing rules
that key on it.

## 6. The known-unauthorable register is mandatory, not optional

Recording "no clean doctrine exists for configuration X" is a real, first-class outcome
that must persist across sessions — otherwise every session re-litigates the same closed
question and eventually someone caves and authors the fabrication. The register is what
makes "silence is correct here" a durable, auditable decision rather than a repeated
judgment call.

## 7. Trigger for coverage work is capture-driven and corpus-existence-based, not aesthetic

Investigate a silent/bare-observation feature **only** to answer one mechanical question:
*does a valence-clean source statement for this exact configuration exist and is it
unauthored/mismapped?* Yes → author/fix. No → record unauthorable. Never "this reading
feels thin, go find something to say" — that reflex is the original fabrication trap.

---

## Reusable procedure (apply to any chapter, palm or astrology)

1. **Doctrine inventory** — mechanically extract every conditional statement from the
   chapter (the "when X → means Y" list). This is the checklist of record.
2. **Rule reconciliation** — for each statement: rule exists? mismapped? absent?
3. **Evidence reconciliation** — for each rule: can the evidence layer produce its
   antecedent tokens? Flag dead rules and dead tokens.
4. **Produce three lists** — authoring gaps · mismatch bugs · dead rules/tokens.
5. **Priority** — fix mismatches (cheapest, recovers real dropped claims) → widen
   evidence where it's the bottleneck → author gaps that are now reachable → record the
   genuinely-unauthorable in the register.
6. **Never** author a rule whose evidence token can't be produced yet.
