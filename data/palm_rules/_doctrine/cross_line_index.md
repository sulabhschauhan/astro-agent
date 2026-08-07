# Cross-Line Dependency Index (master)
Every rule/doctrine whose antecedents span MORE THAN ONE feature/line, aggregated
across all chapters, so multi-line rules are never missed regardless of which
chapter states them. Capture-now, fire-later: firing requires the V1.5 compound
engine + descriptor topology widening.

Format per entry: `| source_page | stated_in_chapter | features_involved | doctrine | rule_id (or GAP) | status |`

## Seed note (verified against source, not copied blind)
Seeded from the head<->heart items in `_audit/reconciliation_head.md`'s dead-rules
list, cross-checked against `palm_rules_head_heart_v1.json` (source of truth) before
entry. Two corrections made during verification, flagged rather than silently
papered over:
- The p148 hairlines item: `reconciliation_head.md` row 19 lists "no rule", but
  `palm_rules_head_heart_v1.json` already has `H_014` authored (compound,
  `status: parked_pending_relation_target`). That's drift between the audit doc and
  the actual rules file -- not fixed here, only noted so it isn't re-litigated as a
  fresh authoring gap.
- The requested third seed row ("head+heart meet under mount", p154) does not match
  any doctrine in the corpus -- no "mount" language appears at p154, and this exact
  phrase isn't in `reconciliation_head.md`. The real p154 cross-line item is `H_022`
  ("head line rises and takes possession of the heart line" -- criminal/murderous
  hands), verified directly in `palm_rules_head_heart_v1.json`. Substituted below.

## Index

| source_page | stated_in_chapter | features_involved | doctrine | rule_id (or GAP) | status |
|---|---|---|---|---|---|
| 147 | head_heart | Line of Head, Quadrangle, Line of Heart | High head line + narrow head-heart space, decided by comparative depth -> head rules heart (or heart rules head if the heart line is stronger) | H_010b | Rule exists (compound, comparative). DEAD: descriptor cannot produce `Line of Head.Position=high` (see `_audit/reconciliation_head.md` row 14). Capture-now, fire-later. |
| 148 | head_heart | Line of Head, Line of Heart | Little hairlines branching up from the head line to the heart line -> affections are a matter of fascination, not love | H_014 | Rule exists (compound). `status: parked_pending_relation_target` in the rules file; also descriptor-blocked (no `Branching`/`Direction=upward` token). See Seed note above re: audit drift. |
| 154 | head_heart | Line of Head, Line of Heart | In criminal/murderous hands the head line rises and takes possession of the heart line, sometimes passing beyond it | H_022 | Rule exists (compound). `status: parked_pending_relation_target` (relation_target token `reaching_Line_of_Heart` likely absent from descriptor). Capture-now, fire-later. |

## Other chapters
Not yet audited. Append here as each chapter's reconciliation pass surfaces
cross-line doctrine (per `data/palm_rules/README.md`'s Cross-line rules convention).
