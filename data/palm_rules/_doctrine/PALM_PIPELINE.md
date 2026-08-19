# PALM_PIPELINE.md — the frozen, repeatable pipeline for every Cheiro line-chapter

**Status: FROZEN as of S95.** Head + Heart are complete and are the reference
implementation (47 rules, all `verified: true`). Every remaining line/chapter MUST run
through the ordered checklist below, end to end, in order. This document is the spec; it is
not a summary of what was done once.

**Governing doctrine:** `VERIFICATION_ARCHITECTURE.md` (fidelity-not-truth) and
`Prior-Art_Investigation_Deterministic_Citation.md`. Read both before authoring. The
guarantee is that a claim is **faithful to the cited source text**, never that it is
doctrinally correct — no palmistry expert is in the loop.

**Storage convention:** authoritative in `data/palm_rules/README.md`. Not restated here.

---

## The ordered checklist

### 0. SCOPE — name the chapter, read it WHOLE

State the line and chapter explicitly (e.g. *Line of Fate, Ch. XI*). Then read the
**entire chapter in order**, from the page-level text — **never** from retrieved chunks and
never from a single page.

> **LAW — a scope sentence is not a rule.** Cheiro opens most chapters with a framing
> sentence that names the topic ("the line of head relates principally to the mentality of
> the subject — to the intellectual strength or weakness…"). Read in isolation, such a
> sentence looks like a disjunctive rule and is the single largest source of BOTH fabricated
> rules and false "no rule exists" verdicts. It is topic-setting prose. Sentence roles are
> `scope` / `base_rule` / `modifier` / `ambiguous`; **no rule may cite a span tagged
> `scope`.**

Deliverable: `data/palm_rules/_doctrine/doctrine_<line>.md` — the doctrine inventory.

---

### 1. AUTHOR rules — extractive only

Write to `data/palm_rules/palm_rules_<line>_v1.json`.

- **Extractive, not paraphrase.** Condition and consequence are real character-spans of the
  source. `source_quote` holds the verbatim Cheiro sentence; `source_page` its page.
- **Isomorphism:** one rule ↔ one source fragment.
- Antecedents carry `feature` / `attribute` / `value` / `condition_type` / `comparator` /
  `comparator_feature` / `relation_target`.
- Retired rules move to the top-level **`retired_superseded[]`** array. The loader reads
  **`validated_candidates` only** — nothing else is ever matched against.
- Every doctrine statement from step 0 must end up as either a verified rule OR an entry in
  `unauthorable_register.json`. **No doctrine statement may go unaccounted for.**

Deliverable: the rules file + `_audit/reconciliation_<line>.md`.

---

### 2. VOCAB REACHABILITY scan — `scripts/vocab_reachability_scan.py`

Every rule trigger token MUST exist in the vocabulary the pipeline actually **emits**.

Classify each token: **reachable** / **NAMING-MISMATCH** / **INTERPRETED-TERM**.

- **NAMING-MISMATCH** → fix at source (the rule's token, or the emitting prompt). Example:
  H_025 triggered on `doubled` while the pipeline emits `double` — a permanent silent miss
  until corrected.
- **INTERPRETED-TERM** (e.g. "which line is stronger") → **compute it and feed it**. Never
  ask the LLM to bridge a representation gap.

> **LAW — registry-legal ≠ emission-reachable. Check BOTH.** A feature can be perfectly
> legal in `ontology_registry.json` and still be unreachable because
> `observation_extractor._FEATURE_ALIAS` never routes vision prose into it. `Quadrangle` and
> `Hand` are exactly this: registry-legal, never emitted, so every rule keyed on them is a
> guaranteed silent miss. Check membership in `all_aliased_features()` **and** attribute
> legality **and** value-pool membership.

**Caveat to carry:** most attributes are *unbound* in the registry, so their legal pool is
the flat union of ~216 tokens. Value-membership checking is therefore weak for unbound
attributes — its real teeth are feature reachability and out-of-union tokens.

Mismatches are **surfaced in `unmatched`**, never silently dropped, never sent onward as a
fake fire (CLAUDE.md law #22).

---

### 3. HARD/SOFT PARTITION — `scripts/hard_soft_partition_scan.py`

Classify **per ANTECEDENT, by attribute-class — never per rule.** A per-rule label can be
tuned until a target comes out right; an attribute-class map cannot.

**HARD** → decided by `match()`:
- `Starting_Point` / `Ending_Point` (origin), `Presence`
- `Position` with a **LANDMARK-shaped** value (`under_`, `terminating_on_`,
  `running_through_`)
- any antecedent carrying a `relation_target`
- any `condition_type == "comparative"` (code-computed from `magnitudes`)

**SOFT** → sent to the LLM as the **whole verbatim sentence**:
- quality / texture / relative reads: `high`, `low`, `short`, `long`, `sloping`, `chained`,
  `broken`, `clear`, `forked`, `curved`, `straight`, `wide`, `deep`…
- **NO anchors, NO benchmarks, NO thresholds.** The model reads the sentence the way a
  human reader would and judges the relative term itself. Do not decompose the sentence, do
  not supply a reference measurement.

**AMBIGUOUS** → **FLAG for Sulabh. Do not auto-route.**
`Position` (height-vs-landmark), `Branching` (bare count vs directed), `Breadth`, `Length`,
`Type`, and the value `Presence=faded`. Forcing these into a bucket to make percentages look
clean is precisely what this step forbids.

A rule is FULLY-HARD / FULLY-SOFT / MIXED / CONTAINS-AMBIGUOUS. **CONTAINS-AMBIGUOUS takes
precedence** — a rule with any unruled antecedent cannot honestly be called either.

---

### 4. HARD-SIDE PROOF — must pass before wiring

For every rule with ≥1 hard antecedent: build a synthetic hand-state in the rules' own
vocabulary, assert `match()` **fires** it, then delete exactly ONE hard fact and assert it
**no longer fires** (fail-closed).

Also measure **co-fire**: `match()` runs over the whole corpus, so a state built for one
rule may satisfy others. Co-firing is not automatically a defect — step 5's precedence
arbitrates it — but it must be measured, not left invisible.

A rule that cannot be fired by any synthetic hand-state cannot be fired by a real one
either. Such rules are **FLAGGED, never smoothed over**.

---

### 5. WIRE via `agent/interpretive/palm_select.py` — canonical, already built

Do **not** write a new gate, a new lambda map, or a new matcher. `palm_select.select()` is
the single interpretation path:

```
select(hand_state, rules, *, model, temperature, client=None, unruled_policy="hard")
  -> {fired_ids, quotes, combined_reading, gated_out, unmatched, suppressed}
```

1. **Hard gate** — each rule is projected onto its hard antecedents
   (`dataclasses.replace`) and handed to the **real production `match()`**, never a
   reimplementation. Fail-closed.
   - **An EMPTY hard projection is a VACUOUS PASS, never a gate-out.** `match()` reads
     `if rule.antecedents and all(...)`, so an antecedent-less projection returns "not
     fired" — treating that as a gate-out would silently kill every FULLY-SOFT rule.
2. **FULLY-HARD rules fire from the gate and never reach the LLM.** Only soft-containing
   rules go onward (CLAUDE.md law #23).
3. **Vocabulary guard** runs before the LLM call; unreachable tokens land in `unmatched`.
4. **Soft select** — one LLM call, whole verbatim sentences, then a verbatim-quote guard
   (a quote that is not a literal substring of the rule's own `source_quote` is a
   fabrication and is dropped).
5. **Precedence — subset DEMOTE, never DELETE.** When rule X's antecedent set is a strict
   proper subset of rule Y's and both fire, Y is primary. X does **not** vanish: it lands in
   `result["suppressed"]` as `{suppressed_id, by, claim, quote}`, carrying its own claim and
   verbatim sentence. `fired_ids` / `quotes` / `combined_reading` hold primaries only.
   Equal or identical antecedent sets never suppress — siblings survive.

---

### 6. EVAL — known-answer hands

Add known-answer hand-states for the line and assert **`fired` / `suppressed` /
`unmatched`** (all three, not just fired). Include at minimum: a positive case, a
single-field-flip phantom-fire control, and a precedence case.

> **The answer key is authored by Sulabh and is NON-DELEGABLE.** An AI-generated answer key
> scored by an AI is an AI-reviewing-AI violation (Working Style #5).

Hand-state fixtures must be written in the **canonical ontology vocabulary**
(`Line of Head`, `Starting_Point`, plus `magnitudes` / `targets` buckets where needed), not
a script-local shorthand. The S95 caller-repoint stalled precisely because the existing
harness fixtures use a private vocabulary that `match()` cannot read.

---

### 7. QUARANTINE — anything needing remodelling

Mark `needs_remodel`; the gate skips it. **Re-model each quarantined rule as its own
one-file task** — never batch-fix, and never let a nearest-token suggestion be applied
automatically (the closure gate's `difflib` nearest-token guess was measured WRONG on 2 of
5 cases).

---

## HUMAN RULINGS — per line, cannot be delegated

Four decisions per chapter. An AI may prepare evidence and options; only Sulabh rules.

| # | ruling | default |
|---|---|---|
| 1 | Which soft terms have a genuine Cheiro **anchor** (a reference the term is measured against) | **none** — LLM judges relative terms like a human reader |
| 2 | **Ambiguous-attribute routing** (Position height-vs-landmark, Branching, Breadth, Length, Type, `faded`) | none — must be ruled explicitly |
| 3 | **Precedence / defeat pairs** — sanity-check the demotion list; confirm no demoted claim deserved promotion | mechanical subset check proposes; human confirms |
| 4 | **Eval answer key** (step 6) | none — non-delegable |

Ruling 1's evidence is produced by `scripts/soft_anchor_by_line.py` (per-line, per-term
scan: anchor-candidate / ambiguous-subject / pure-relative). It **flags**; it never assigns
which line a term describes when more than one is named.

---

## WORKING LAWS (restated — these bind every step)

1. **Design in chat first.** No code before the approach is agreed.
2. **One file, one task.** A prompt that touches two files needs that called out explicitly.
3. **Report-first to `diagnostics/latest_run.md`** (overwrite-only, never append). Chat gets
   a ≤10-line summary.
4. **`RATIFIED: commit authorized` before any source commit.** Docs/diagnostics are exempt.
   No token → STOP and surface.
5. **Model routing:** Sonnet builds · Haiku docs + git · Opus irreversible/high-stakes.
6. **Hardest case first.** Test the edge, not the happy path. Every defect found in the S95
   `palm_select` build was found by running the awkward fixture, not the clean one.
7. **No widening tolerances.** Never loosen a threshold to make a result pass. Every numeric
   threshold needs justification + scope guard + tuning note.
8. **Measure before claiming.** A prompt's constants are a claim, not a fact — verify against
   the code first. A prediction stated as a measurement is a reportable incident.
9. **Layer first.** Name the owning layer (Data / Retrieval / Prompt / UI) before fixing.
10. **Check `diagnostics/KNOWN_PATTERNS.md`** before starting a diagnosis; add a row before
    closing one.

---

## Reference implementation + remaining work

**Head + Heart — COMPLETE (S95).** `palm_rules_head_heart_v1.json`, 47 validated rules, all
`verified: true`. Reconciliation audit done for head (`_audit/reconciliation_head.md`).
This is the worked example for every step above.

| line / chapter | status |
|---|---|
| Head, Heart | **COMPLETE** — reference implementation |
| **Life** | **file exists, NOT vetted** — 13 rules. ⚠ See warning below. |
| Fate | not started |
| Sun | not started |
| Health | not started |
| Mars | not started |
| Mounts | not started |
| Marks / signs | not started |
| Hand types | not started — blocked: `Hand` is not emission-reachable (step 2) |

> ⚠ **LIFE LINE WARNING — live but unvetted.** `load_rule_set()` globs every top-level
> `*.json` in `data/palm_rules/`, so the 13 life-line rules are **already merged into the
> live rule set** (60 rules total vs. the 47 that `load_rules()` returns by default). They
> have never been through steps 2–4: a reachability check finds **3 antecedents that fail**,
> and the file's schema diverges from head/heart (`parked_pending` instead of
> `parked_pending_relation_target`, and no `retired_superseded` array). Life must be run
> through this pipeline before it can be trusted, and the schema divergence reconciled.

---

## Known structural gaps that outlive S95

- **`Quadrangle` and `Hand` are not emission-reachable.** Rules keyed on them
  (H_010a, H_010b, HL_006, HL_021, H_018, H_019, H_020) cannot fire from a real hand.
- **Cross-group precedence is currently inert** — every cross-group demotion has an
  unreachable primary, so it changes nothing until the above is fixed.
- **The Indian tradition is absent.** Palm grounds on Cheiro (Western) only; Hasta
  Samudrika is OCR-unusable (449 pages, 4 with ≥50 alphabetic words). The doctrinal gap is
  real; the fix is re-sourcing, not repair.
