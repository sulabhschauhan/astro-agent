# Wide (fail-safe) vs strict house-filtered payload -- ARM A vs ARM B

Generated: 2026-09-05T12:15:45Z
Question: What does my chart say about my career?
Plan built once, live planner call, temp=0, 3.6s. Reused unchanged for both arms.

## Prediction (stated before running)

ARM B cites FEWER distinct ids but a HIGHER fraction of what it was sent. If ARM B produces MORE claims than ARM A, that inverts the fail-safe assumption -- flag loudly.

## Plan (shared by both arms)

```json
{
  "question": "What does my chart say about my career?",
  "domains": [
    "career"
  ],
  "houses": [
    10
  ],
  "whose_chart": "self",
  "time_scope": "present",
  "in_scope": true,
  "reasoning": "The 10th house is the primary house related to career in a person's chart. The question is about the native's own career, so it pertains to the native's chart. The time scope is present as the question asks about the current state of the career.",
  "source": "llm",
  "planner_fallback": false,
  "validation_errors": [],
  "raw_responses": [
    "{\"domains\": [\"career\"], \"houses\": [10], \"whose_chart\": \"self\", \"time_scope\": \"present\", \"in_scope\": true, \"reasoning\": \"The 10th house is the primary house related to career in a person's chart. The question is about the native's own career, so it pertains to the native's chart. The time scope is present as the question asks about the current state of the career.\"}"
  ],
  "planner_version": "planner-1.0"
}
```

## ARM B construction note

ARM B additionally dropped 298 segment(s) that ARM A kept, because either they had NO extracted relation at all, or their relation(s) touched no planned house [10]. This is NOT the shipped `no_relation_failsafe` rule -- it is its inverse, unique to this probe. Whole-chapter units (6) are untouched by ARM B's rule in both arms, since extract_relations never ran on them individually.

## ARM B -> gpt-4o gate

ARM B real tokens (chars/4 estimate) = 18340. Threshold = 30000. Under threshold -- ALSO sent to gpt-4o (row 3 below).

## 1. Cost / size per arm

| arm | model | approx tokens (payload) | real tokens (chars/4 est.) | API prompt_tokens | API completion_tokens | kept segments | whole units | wall-clock s | est. cost USD | error |
|---|---|---|---|---|---|---|---|---|---|---|
| A (wide) | gpt-4o-mini | 48589 | 67513 | 80882 | 120 | 304 | 6 | 5.72 | 0.0122 |  |
| B (strict) | gpt-4o-mini | 12864 | 18340 | 20736 | 123 | 6 | 6 | 2.29 | 0.0032 |  |
| B (strict) | gpt-4o | 12864 | 18340 | 20736 | 283 | 6 | 6 | 4.15 | 0.0547 |  |

## 2. Claims / citations per arm

| arm | model | claims | cited ids | ghost count | ghosts |
|---|---|---|---|---|---|
| A (wide) | gpt-4o-mini | 1 | bphs2_ch48 | 0 | (none) |
| B (strict) | gpt-4o-mini | 1 | bphs2_ch48 | 0 | (none) |
| B (strict) | gpt-4o | 2 | bphs2_ch48, ch24_s106 | 0 | (none) |

## 3. Citation set difference (both mini)

### A (wide, gpt-4o-mini) vs B (strict) (gpt-4o-mini)

- cited by A but NOT this arm: (none)
- cited by this arm but NOT A: (none)

### A (wide, gpt-4o-mini) vs B (strict) (gpt-4o)

- cited by A but NOT this arm: (none)
- cited by this arm but NOT A: ['ch24_s106']

## 4. Cited-id origin: domain_match vs fail-safe (the decision number)

| arm | model | domain_match | failsafe (untagged/unknown_id) | whole_chapter_unit | other |
|---|---|---|---|---|---|
| A (wide) | gpt-4o-mini | 0 | 0 | 1 | 0 |
| B (strict) | gpt-4o-mini | 0 | 0 | 1 | 0 |
| B (strict) | gpt-4o | 1 | 0 | 1 | 0 |

## 5. Readings, verbatim, side by side

### A (wide) -- gpt-4o-mini

Your career prospects appear favorable due to the placement of the lord of the 10th house in the 4th house, suggesting potential recognition and rewards from the government.

silent_on: ['specific career paths', 'current career status', 'personal ambitions', 'challenges in career']

### B (strict) -- gpt-4o-mini

The placement of the lord of the 10th house in the 4th house suggests that there may be favorable outcomes in your career, particularly in terms of recognition and awards from the government.

silent_on: ['specific career details', 'current career status', 'career challenges', 'career opportunities']

### B (strict) -- gpt-4o

The chart suggests a career that may involve public welfare, education, or real estate, with potential recognition from authorities. The presence of the 11th lord in the 10th house indicates a focus on public welfare and creating a lasting impact. Recognition and awards from the government are possible during the Dasa of the 10th lord.

silent_on: ['specific planetary positions', 'nakshatras', 'aspects', 'dignities', 'yogas not mentioned', 'transits', 'divisional charts', 'current Dasa or Antardasa']

## Deviation from prediction

ARM B claims (1) <= ARM A claims (1) -- consistent with the stated prediction's direction on claim count. See tables 2-4 above for the citation-fraction comparison (fewer distinct ids / higher fraction) the prediction also made.

