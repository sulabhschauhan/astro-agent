# Palm Rule Priority Specification (drives `resolve_priority()`)

Status: DESIGN — awaiting Sulabh validation. Not yet implemented in engine.
Scope: deterministic palm rules table (`palm_rules_*.json` → `palm_rules_table.py`).

## Core invariant
Suppression happens **only within a single `topic_group`**. Rules in different
topic_groups NEVER suppress each other — they all voice. (A life-line reading and
a head-line reading coexist.)

## Three tiers (within a topic_group)

### Tier 0 — Baseline / ideal  (`baseline: true`)
The "healthy / ideal" reading, e.g. L_001 "long, narrow, deep → long life, good health".
Rule: **suppressed by ANY co-firing non-baseline rule in the same topic_group.**
Rationale: if a defect or a more specific reading is present, the ideal reading is
contradicted and must not be voiced alongside it.
If a baseline rule is the ONLY rule firing in its topic_group, it voices normally.

### Tier 1 — General  (single-antecedent, non-baseline)
Mid priority. Voices unless suppressed by a Tier-2 refinement (see below).

### Tier 2 — Specific / compound  (most-specific-wins)
**Suppression is by antecedent-SUBSET containment, NOT by raw antecedent count.**
Rule R_spec suppresses R_gen iff, within the same topic_group:
    antecedents(R_gen) ⊂ antecedents(R_spec)   (proper subset, same feature+attribute+value tuples)
i.e. R_spec is a strict refinement of R_gen. Example:
    L_017 [islanded]                       (general)
    L_018 [islanded, at_start, clear]      (refinement) → suppresses L_017.
Two compounds that do NOT subsume each other BOTH fire:
    L_003 [chained, Palm soft]  and  L_005 [chained, under_Jupiter]
    → neither is a subset of the other → BOTH voice.

## Comparative rules  (`condition_type: comparative`)
Evaluated independently. They neither suppress nor are suppressed by Tier 0/1/2,
because their antecedent set is a cross-feature comparison (`>`,`<`,`=`) and is not
subset-comparable to standard antecedents. They always voice when their comparison holds.

## Resolution order (per topic_group)
1. Collect all fired rules.
2. Partition: {comparative} | {baseline} | {non-baseline standard}.
3. Within non-baseline standard: drop any rule that is a proper antecedent-subset
   of another fired rule in the group (most-specific-wins).
4. If any non-baseline rule survives, drop ALL baseline rules in the group.
5. Emit: surviving non-baseline standard + surviving baseline (if step 4 didn't fire)
   + all comparative.

## Known engine-alignment risk (verify before coding)
The current `resolve_priority()` implements "most_specific_wins" — it MUST be
confirmed to use subset-containment, not raw count. If it uses raw count, equal- or
higher-count unrelated compounds (L_003 vs L_005) will wrongly suppress. Align engine
to §Tier-2 semantics under a RATIFIED code prompt before this spec is considered live.

## Schema addition required
Add `"baseline": <bool>` to the rule schema (already present in
`palm_rules_life_line_v1.json`; backfill `head_heart_v1` with `baseline:false`
except its ideal rules).
