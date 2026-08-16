# S94 head-line ensemble-reconciliation pilot

Rules checked (line_head*, validated_candidates): 26
Canonical vocab tokens harvested: 26
Member A entries (diagnostics/ensemble_recon_headline_claude.json): 34
Member B entries (diagnostics/ensemble_recon_headline_gpt4o.json): 21
TOKEN-BEARING rules verdicted: 20
DEFERRED-RELATIONAL rules (not verdicted): 6

## Verdict table

| rule_id | verdict | A? | B? | note |
|---|---|---|---|---|
| H_002 | AMBIGUOUS | True | False | A fully corroborated (Starting_Point='rising_from_Line_of_Life') |
| H_003 | AUTO-VERIFIED | True | True | A fully corroborated (Starting_Point='rising_from_Mount_of_Mars'); B fully corroborated (Starting_Point='rising_from_Mount_of_Mars') |
| H_004 | AMBIGUOUS | True | False | A fully corroborated (Continuity='clear', Direction='straight') |
| H_005 | AUTO-VERIFIED | True | True | A fully corroborated (Length='short'); B fully corroborated (Length='short') |
| H_006 | AUTO-VERIFIED | True | True | A fully corroborated (Length='short'); B fully corroborated (Length='short') |
| H_007 | AMBIGUOUS | True | False | A fully corroborated (Continuity='broken', Position='under_Mount_of_Saturn') |
| H_008 | AUTO-VERIFIED | True | True | A fully corroborated (Continuity='chained'); B fully corroborated (Continuity='chained') |
| H_009 | AUTO-VERIFIED | True | True | A fully corroborated (Continuity='islanded'); B fully corroborated (Continuity='islanded') |
| H_011 | AUTO-VERIFIED | True | True | A fully corroborated (Continuity='broken'); B fully corroborated (Continuity='broken') |
| H_012 | COVERAGE-GAP | False | False | A emitted every token (Continuity='islanded') but span didn't line up on this rule; B emitted every token (Continuity='islanded') but span didn't line up on this rule |
| H_013 | FABRICATED-MISMODELED | False | False | no member emitted the full compound condition, with or without span overlap |
| H_015 | AUTO-VERIFIED | True | True | A fully corroborated (Position='running_through_Square'); B fully corroborated (Position='running_through_Square') |
| H_018 | COVERAGE-GAP | False | False | A emitted every token (Direction='sloping', Type='square') but span didn't line up on this rule; B emitted every token (Direction='sloping', Type='square') but span didn't line up on this rule |
| H_019 | COVERAGE-GAP | False | False | A emitted every token (Direction='sloping', Type='spatulate') but span didn't line up on this rule; B emitted every token (Direction='sloping', Type='spatulate') but span didn't line up on this rule |
| H_020 | COVERAGE-GAP | False | False | A emitted every token (Direction='straight', Position='high', Type='philosophic') but span didn't line up on this rule; B emitted every token (Direction='straight', Position='high', Type='philosophic') but span didn't line up on this rule |
| H_021 | AMBIGUOUS | True | False | A fully corroborated (Position='high') |
| H_023 | FABRICATED-MISMODELED | False | False | no member emitted the full compound condition, with or without span overlap |
| H_024 | COVERAGE-GAP | False | False | A emitted every token (Branching='branched', Position='terminating_on_Mount_of_Moon') but span didn't line up on this rule; B emitted every token (Branching='branched', Position='terminating_on_Mount_of_Moon') but span didn't line up on this rule |
| H_025 | AUTO-VERIFIED | True | True | A fully corroborated (Branching='doubled'); B fully corroborated (Branching='doubled') |
| H_026 | FABRICATED-MISMODELED | False | False | no member emitted the full compound condition, with or without span overlap |

## Deferred-relational (not verdicted)

H_010a, H_010b, H_014, H_016, H_017, H_027

## Counts per verdict

- AUTO-VERIFIED: 8
- FABRICATED-MISMODELED: 3
- COVERAGE-GAP: 5
- AMBIGUOUS: 4

NOTE: H_026 stays FABRICATED-MISMODELED due to Direction/Slope vocab overload (its 'downward' claim likely gets tagged attribute='Direction' by members rather than the rule's 'Slope'); flagged for Phase-A vocab freeze, not fixed here.

## Anchor re-pick (single-antecedent, AUTO-VERIFIED this run)

Candidates: H_003, H_005, H_006, H_008, H_009, H_011, H_015, H_025
Anchor chosen (lowest id): H_003

## Calibration

H_013: FABRICATED-MISMODELED [expected FABRICATED-MISMODELED] OK
H_023: FABRICATED-MISMODELED [expected FABRICATED-MISMODELED] OK
H_012: COVERAGE-GAP [expected COVERAGE-GAP] OK
H_004: AMBIGUOUS [expected AMBIGUOUS] OK
H_021: AMBIGUOUS [expected AMBIGUOUS] OK
H_003: AUTO-VERIFIED [expected AUTO-VERIFIED] OK

CALIBRATION: PASS

## SHINGLE_K sensitivity (5 vs 6 vs 8)

(no rule's verdict changes between K=5 and K=8)
