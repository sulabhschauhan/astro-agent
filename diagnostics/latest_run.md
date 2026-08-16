# S94 heart-line ensemble-reconciliation HOLDOUT (blind, no calibration)

Reconciler mechanism reused UNCHANGED from scripts/ensemble_recon_pilot_headline.py (reconcile, member_fully_corroborates, token_condition_covered, _quotes_overlap, SHINGLE_K=6). No thresholds or matching logic edited for this run.

Rules checked (line_heart*, validated_candidates): 21
Canonical vocab tokens harvested: 22
Member A entries (diagnostics/ensemble_recon_heartline_claude.json): 28
Member B entries (diagnostics/ensemble_recon_heartline_gpt4o.json): 14
TOKEN-BEARING rules verdicted: 21
DEFERRED-RELATIONAL rules (not verdicted): 0

## Verdict table

| rule_id | verdict | A? | B? | note |
|---|---|---|---|---|
| HL_001 | AUTO-VERIFIED | True | True | A fully corroborated (Starting_Point='rising_from_Mount_of_Jupiter'); B fully corroborated (Starting_Point='rising_from_Mount_of_Jupiter') |
| HL_002 | AUTO-VERIFIED | True | True | A fully corroborated (Starting_Point='rising_from_Finger_of_Jupiter'); B fully corroborated (Starting_Point='rising_from_Finger_of_Jupiter') |
| HL_003 | AUTO-VERIFIED | True | True | A fully corroborated (Starting_Point='between_Jupiter_and_Saturn'); B fully corroborated (Starting_Point='between_Jupiter_and_Saturn') |
| HL_004 | AUTO-VERIFIED | True | True | A fully corroborated (Starting_Point='rising_from_Mount_of_Saturn'); B fully corroborated (Starting_Point='rising_from_Mount_of_Saturn') |
| HL_005 | COVERAGE-GAP | False | False | A emitted every token (Position='high', Starting_Point='rising_from_Mount_of_Saturn') but span didn't line up on this rule; B emitted every token (Position='high', Starting_Point='rising_from_Mount_of_Saturn') but span didn't line up on this rule |
| HL_006 | AMBIGUOUS | True | False | A fully corroborated (Breadth='narrow', Position='high') |
| HL_007 | AMBIGUOUS | True | False | A fully corroborated (Continuity='broken', Position='under_Mount_of_Saturn') |
| HL_008 | COVERAGE-GAP | False | False | A emitted every token (Continuity='broken', Position='under_Mount_of_Sun') but span didn't line up on this rule |
| HL_009 | COVERAGE-GAP | False | False | A emitted every token (Continuity='broken', Position='under_Mount_of_Mercury') but span didn't line up on this rule |
| HL_010 | COVERAGE-GAP | False | False | A emitted every token (Continuity='forked', Starting_Point='rising_from_Mount_of_Jupiter') but span didn't line up on this rule; B emitted every token (Continuity='forked', Starting_Point='rising_from_Mount_of_Jupiter') but span didn't line up on this rule |
| HL_011 | AMBIGUOUS | True | False | A fully corroborated (Position='high') |
| HL_012 | AMBIGUOUS | True | False | A fully corroborated (Direction='drooping', Position='low') |
| HL_013 | COVERAGE-GAP | False | False | A emitted every token (Continuity='forked', Width='wide') but span didn't line up on this rule |
| HL_014 | AMBIGUOUS | True | False | A fully corroborated (Branching='single', Width='thin') |
| HL_015 | AUTO-VERIFIED | True | True | A fully corroborated (Presence='faded'); B fully corroborated (Presence='faded') |
| HL_016 | AUTO-VERIFIED | True | True | A fully corroborated (Length='extending_across_entire_palm'); B fully corroborated (Length='extending_across_entire_palm') |
| HL_017 | AMBIGUOUS | True | False | A fully corroborated (Continuity='barred') |
| HL_018 | COVERAGE-GAP | False | False | A emitted every token (Continuity='chained', Starting_Point='rising_from_Mount_of_Saturn', Width='wide') but span didn't line up on this rule |
| HL_019 | AUTO-VERIFIED | True | True | A fully corroborated (Color='bright_red'); B fully corroborated (Color='bright_red') |
| HL_020 | AMBIGUOUS | True | False | A fully corroborated (Color='pale', Width='wide') |
| HL_021 | COVERAGE-GAP | False | False | A emitted every token (Breadth='narrow', Position='low') but span didn't line up on this rule |

## Deferred-relational (not verdicted)

(none)

## Counts per verdict

- AUTO-VERIFIED: 7
- FABRICATED-MISMODELED: 0
- COVERAGE-GAP: 7
- AMBIGUOUS: 7

## SHINGLE_K sensitivity (5 vs 6 vs 8)

(no rule's verdict changes between K=5 and K=8)

No calibration gate this run -- blind holdout on a chapter the matcher was never tuned against. Distribution above is reported as-is for review.
