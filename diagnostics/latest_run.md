# S119 Defect 2 close — retire Saturn M_015/M_016 (head-line back-references)

## Verified at HEAD before editing
- HEAD = `5a5d7b7` (`wip/interpretive-pilot`), which already includes `7be74db` (S119 Step 5).
- M_015 (Development="well developed") and M_016 (Development="unusually high") were live
  `validated_candidates` in `data/palm_rules/palm_rules_mounts_v1.json`, both `topic_group:
  mount_saturn`.
- Each carried a pre-existing `source_fidelity` "MAJOR FIDELITY CAVEAT": the quotes back-reference
  a co-occurring Line-of-Head profile from the suicide chapter (p.217) / insanity chapter (p.153)
  respectively, not standalone Mounts-chapter Saturn grading — never resolved.
- grep of `M_015`/`M_016` across the repo found zero test/script references by rule_id; only
  incidental "Mount of Saturn"/"unusually high" occurrences unrelated to rule-firing assertions.

## Implementation
- `data/palm_rules/palm_rules_mounts_v1.json`: moved M_015 and M_016 from `validated_candidates`
  to `retired_superseded`, same structure as the 10 rows retired in `7be74db` — added
  `retired_reason: "saturn_grade_is_a_head_line_backreference_not_mount_doctrine"`,
  `retired_note`, `retired_date: "2026-08-30"`, `retired_by: "Sulabh (S119 Defect 2, ratified)"`.
  Nothing deleted; quotes/history preserved. No other rule touched.

## Verification
- `python scripts/gate_rule_citations.py` → 87 live rules, 16 parked, `NOT_FOUND_ANYWHERE: 0`.
- `python scripts/vocab_reachability_scan.py --rules data/palm_rules/palm_rules_mounts_v1.json`
  → 12 rules scanned, 12 antecedents, `Unemittable antecedents: 0`. Saturn's Development values
  now match no rule (same accepted-orphan status as "not notably developed" elsewhere).
- `pytest -q` full suite: 2 pre-existing failures surfaced (legitimate consequences of the
  retirement), both fixed and justified:
  1. `test_load_rule_set_real_data_merges_43_plus_13_with_unique_ids`
     (`tests/interpretive/test_palm_rules_table.py`) — literal live-rule-count assertion
     89 → 87; comment updated 14 → 12 mount rules, documenting the M_015/M_016 retirement.
  2. `test_enabled_features_derived_from_the_loaded_rule_set`
     (`tests/interpretive/test_palm_reading_rules_engine.py`) — dropped `"Mount of Saturn"`
     from the expected feature-derivation canary set; correct, since Saturn no longer has any
     live antecedent to derive that feature from.
  3. `test_every_live_rule_produces_a_claim_citing_its_own_gate_verified_quote`
     (`tests/interpretive/test_rule_to_claim.py`) — live rule count assertion 89 → 87.
- Final full-suite result: **3743 passed, 7 skipped, 0 failed** (was 3741 passed pre-edit; net
  +2 from no new tests, same tests re-passing after re-baseline — count difference is the 2
  fixed assertions, not new tests).

## Result
- Live rule count: **89 → 87**.
- Saturn now has NO live rule → fully silent, matching Mercury / Lower Mars / Luna.
- Commit: `7177a32` — fix(mounts): retire Saturn M_015/M_016 — head-line back-references, not
  mount doctrine (S119 Defect 2 close). Pushed to `origin/wip/interpretive-pilot`.
