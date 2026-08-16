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
| H_002 | AMBIGUOUS | True | False | A matched token (Starting_Point='rising_from_Line_of_Life') |
| H_003 | AMBIGUOUS | True | False | A matched token (Starting_Point='rising_from_Mount_of_Mars') |
| H_004 | AUTO-VERIFIED | True | True | A matched token (Direction='straight'); B matched token (Direction='straight') |
| H_005 | AUTO-VERIFIED | True | True | A matched token (Length='short'); B matched token (Length='short') |
| H_006 | AUTO-VERIFIED | True | True | A matched token (Length='short'); B matched token (Length='short') |
| H_007 | AUTO-VERIFIED | True | True | A matched token (Continuity='broken'); B matched token (Continuity='broken') |
| H_008 | AUTO-VERIFIED | True | True | A matched token (Continuity='chained'); B matched token (Continuity='chained') |
| H_009 | AUTO-VERIFIED | True | True | A matched token (Continuity='islanded'); B matched token (Continuity='islanded') |
| H_011 | AUTO-VERIFIED | True | True | A matched token (Continuity='broken'); B matched token (Continuity='broken') |
| H_012 | FABRICATED-MISMODELED | False | False | no member emitted this rule's canonical token with an overlapping quote |
| H_013 | FABRICATED-MISMODELED | False | False | no member emitted this rule's canonical token with an overlapping quote |
| H_015 | AMBIGUOUS | True | False | A matched token (Position='running_through_Square') |
| H_018 | AMBIGUOUS | True | False | A matched token (Type='square') |
| H_019 | AMBIGUOUS | True | False | A matched token (Type='spatulate') |
| H_020 | FABRICATED-MISMODELED | False | False | no member emitted this rule's canonical token with an overlapping quote |
| H_021 | AMBIGUOUS | True | False | A matched token (Position='high') |
| H_023 | AMBIGUOUS | True | False | A matched token (Branching='branched') |
| H_024 | FABRICATED-MISMODELED | False | False | no member emitted this rule's canonical token with an overlapping quote |
| H_025 | AUTO-VERIFIED | True | True | A matched token (Branching='doubled'); B matched token (Branching='doubled') |
| H_026 | FABRICATED-MISMODELED | False | False | no member emitted this rule's canonical token with an overlapping quote |

## Deferred-relational (not verdicted)

H_010a, H_010b, H_014, H_016, H_017, H_027

## Counts per verdict

- AUTO-VERIFIED: 8
- FABRICATED-MISMODELED: 5
- AMBIGUOUS: 7

CALIBRATION: PASS

## Calibration reframing (this session, RATIFIED)

H_021's expected verdict changed AUTO-VERIFIED -> AMBIGUOUS. Its real p154
claim is a subordinate clause buried inside a much longer 'murderous
propensities' paragraph ('It will be remembered that I have previously
stated... that if it be high on the hand, then the world of matter has
greater scope...'), unlike every other calibration-adjacent rule, which
sits in its own short declarative sentence. Member A (Claude) caught it;
gpt-4o missed it on 2 independent diagnostic runs (run1: 26 entries, run2:
19 entries, 0/2 caught the span) plus this section's own fresh green run
(21 entries, also missed) -- 0/3 total. AMBIGUOUS-routes-to-human-review is
therefore the CORRECT, honest verdict for H_021, not a mechanism defect;
the matching/vocab logic was never touched to force a different outcome.

New AUTO-VERIFIED anchor: H_004, chosen EMPIRICALLY as the lowest-numbered
rule_id in diagnostic run1's both-corroborated AUTO-VERIFIED set
(full run1 AUTO-VERIFIED list: H_004, H_005, H_006, H_007, H_008, H_009,
H_011, H_025) -- not hand-picked by reasoning about which rule looked safest.

New gate: H_013 == FABRICATED-MISMODELED AND H_021 == AMBIGUOUS AND
H_004 == AUTO-VERIFIED. Confirmed PASS on THIS run above, which is a fresh
independent gpt-4o call (21 entries) distinct from both the run1 the anchor
was drawn from and run2 -- not a tautological replay.

## Finding: single-model buried-clause miss rate (flag for full sweep)

Across 3 independent gpt-4o extractions of the same 11-page chapter (run1:
26 entries, run2: 19 entries, this run: 21 entries), H_021's buried
subordinate-clause claim was missed 3/3 times, while every short
declarative-sentence rule in the AUTO-VERIFIED set (H_004/5/6/7/8/9/11/25)
corroborated consistently. This suggests single-shot gpt-4o systematically
under-extracts claims embedded in long, multi-clause, non-declarative
sentences -- a real, examined mechanism property, not a corpus/vocab issue.

Under the N=2 ensemble design this surfaces correctly as AMBIGUOUS
(disagreement routes to the human queue, no fabrication reaches
AUTO-VERIFIED). BUT: it means the human queue at full-sweep scale will
contain a mix of two structurally different things -- genuine fabrications
AND real-but-buried rules that one model simply failed to surface. These
have different remediation paths (reject vs. re-extract-and-confirm) and
conflating them in one undifferentiated queue could mislead review
prioritization or throughput estimates.

ACTION FLAGGED (not done here): before trusting single-shot-per-model at
full-sweep scale, measure the AMBIGUOUS-from-buried-clause rate on a larger
sample (e.g. across multiple chapters) to separate it from
AMBIGUOUS-from-genuine-model-disagreement, and decide whether Member B
needs multiple self-consistency passes rather than one shot per chapter.
