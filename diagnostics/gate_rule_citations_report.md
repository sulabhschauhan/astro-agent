# S114 rule-citation gate report (scripts/gate_rule_citations.py)

Run date: 2026-09-13. Corpus: `C:\Users\sulab\Documents\Python Scripts\astro-agent\data\cheiro\cheiro_clean_v1.json`. Rule files scanned: 4 (palm_rules_fate_line_v1.json, palm_rules_head_heart_v1.json, palm_rules_life_line_v1.json, palm_rules_mounts_v1.json).

**REPORT-ONLY**: this run writes nothing except this report -- no data/palm_rules/ file is read-and-rewritten. Whole-corpus anchor search (not a source_page-vs-page_ref comparison): a quote is CLEAN if it anchors on ANY page or in the full-corpus concatenation, regardless of which page_ref that is -- printed source_page and the corpus's own page_ref are different numbering schemes with a non-trivial (roughly-constant per book) offset.

## Per-file citation-status counts

| file | bucket | CLEAN | NOT_FOUND_ANYWHERE | UNCITED | GENERATOR_PLACEHOLDER | total |
|---|---|---|---|---|---|---|
| palm_rules_fate_line_v1.json | validated_candidates (LIVE) | 16 | 0 | 0 | 0 | 16 |
| palm_rules_fate_line_v1.json | parked_* (PARKED) | 0 | 0 | 4 | 0 | 4 |
| palm_rules_head_heart_v1.json | validated_candidates (LIVE) | 48 | 0 | 0 | 0 | 48 |
| palm_rules_head_heart_v1.json | parked_* (PARKED) | 1 | 0 | 0 | 0 | 1 |
| palm_rules_life_line_v1.json | validated_candidates (LIVE) | 11 | 0 | 0 | 0 | 11 |
| palm_rules_life_line_v1.json | parked_* (PARKED) | 0 | 0 | 8 | 0 | 8 |
| palm_rules_mounts_v1.json | validated_candidates (LIVE) | 12 | 0 | 0 | 0 | 12 |
| palm_rules_mounts_v1.json | parked_* (PARKED) | 0 | 0 | 3 | 0 | 3 |

## NOT_FOUND_ANYWHERE -- every one, for human review (never auto-fixed)

**None. Every cited rule (live and parked) anchors somewhere in the corpus.**

## Implied-offset distribution (found page_ref - source_page), CLEAN rules only

n=106 offset data points (a rule matching multiple pages contributes one point per matched page).

- min: -34
- p25: 0
- median: 0
- p75: 1
- max: 84

Most common offset values: 0 (x71), 60 (x16), 1 (x3), -13 (x2), -1 (x2)

**IMPORTANT per-file finding, not a single global offset**: the combined distribution above blends together what are actually TWO distinct, each internally-tight, per-file conventions -- see the breakdown below. A future rule-authoring session should know which convention its own chapter's `source_page` field is already using before assuming a fixed +60.

### Per-file dominant offset

| file | n | dominant offset | count at dominant | other offsets seen |
|---|---|---|---|---|
| palm_rules_fate_line_v1.json | 19 | +60 | 16/19 | 66 (x1), 31 (x1), 84 (x1) |
| palm_rules_head_heart_v1.json | 61 | +0 | 49/61 | -13 (x2), 1 (x2), -12 (x1), 12 (x1), 13 (x1), 45 (x1), -34 (x1), -1 (x1), 44 (x1), 53 (x1) |
| palm_rules_life_line_v1.json | 13 | +0 | 10/13 | 13 (x1), 44 (x1), 1 (x1) |
| palm_rules_mounts_v1.json | 13 | +0 | 12/13 | -1 (x1) |

## Spot-check: FT_007 / FT_008 / H_028 / L_026

| rule_id | file | bucket | status | matched_pages | implied_offsets |
|---|---|---|---|---|---|
| FT_007 | palm_rules_fate_line_v1.json | live | CLEAN | [164] | [60] |
| FT_008 | palm_rules_fate_line_v1.json | live | CLEAN | [164] | [60] |
| H_028 | palm_rules_head_heart_v1.json | live | CLEAN | [146] | [0] |
| L_026 | palm_rules_life_line_v1.json | live | CLEAN | [135] | [1] |

