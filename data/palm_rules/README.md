# data/palm_rules/ -- convention

- Source of truth: `palm_rules_<chapter>_v1.json` (all rules, single + compound).
- Priority is COMPUTED by `resolve_priority()` from baseline flag + antecedent-subset
  containment (see `../priority_spec.md`). Priority is NEVER stored in a file.
- `_doctrine/doctrine_<line>.md`: the complete "when X -> means Y" inventory per line;
  the checklist of record that authoring must be complete against.
- `_audit/reconciliation_<line>.md`: book<->rules<->descriptor reconciliation; the
  three lists (authoring gaps / mismatch bugs / dead rules-tokens).
- `unauthorable_register.json`: recorded "no clean doctrine" verdicts, per line.
- Engine loads ONLY: `palm_rules_*.json`, `../ontology_registry.json`, `unauthorable_register.json`.
  Everything else here is human/authoring reference.
- Naming: `<line>` in {head, heart, life, fate, sun, health, marriage, mounts, thumb,
  fingers, nails, special_marks}. `<chapter>` for rules files matches existing
  (life_line, head_heart).
- Procedure for any new chapter: see `data/_meta/learnings_for_astrology_rules.md`
  (the reusable 6-step reconciliation procedure).

## Cross-line rules
Cross-line rules live in their PRIMARY chapter file with `is_compound: true` and
full multi-feature antecedents -- they are NOT duplicated into a separate file.
Every cross-line statement is ALSO logged in `_doctrine/cross_line_index.md`
(source_page / stated_in_chapter / features_involved / doctrine / rule_id / status),
so multi-line doctrine is never missed regardless of which chapter states it.
Authoring a chapter is incomplete until its cross-line statements are in that index.
