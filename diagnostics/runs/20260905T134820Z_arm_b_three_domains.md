# ARM B (strict), gpt-4o only, across 3 domains -- career/children/health

Generated: 2026-09-05T13:48:20Z
ARM A skipped entirely per instruction (wide already ruled out). gpt-4o-mini skipped -- gpt-4o only.

## Prediction (stated before running)

At least 2 of 3 will cite >=1 real segment id. If all three cite only whole-chapter units, that is the headline: the segment machinery is not being used at all and the POC's central claim is unproven.

## 1. Plan / payload / cost per question

| # | question | planner houses | fallback used | effective houses | strict kept segments | approx tokens | API prompt_tokens | ratio | est. cost USD |
|---|---|---|---|---|---|---|---|---|---|
| 1 | What does my chart say about my career? | [1, 2, 6, 10, 11] | no | [1, 2, 6, 10, 11] | 14 | 15367 | 24604 | 1.601 | 0.0636 |
| 2 | What does my chart say about my children? | [5] | YES | [5, 9, 2] | 8 | 17338 | 27380 | 1.579 | 0.0753 |
| 3 | What does my chart say about my health? | [1, 6, 8] | no | [1, 6, 8] | 8 | 10340 | 17036 | 1.648 | 0.045 |

Rows using the fallback house list: [2]

## 2. Claims, per-claim segment_ids arrays

### Q1 -- What does my chart say about my career?

claims = 2

| claim # | statement | segment_ids |
|---|---|---|
| 1 | The 10th lord is in the 4th house. | ['bphs2_ch48'] |
| 2 | Recognition from and awards by Government are indicated in the Dasa of the lord of the 10th. | ['bphs2_ch48'] |

### Q2 -- What does my chart say about my children?

claims = 8

| claim # | statement | segment_ids |
|---|---|---|
| 1 | During the Dasa of the rasi owned or occupied by the Moon, there will be gain of wealth and clothes, name and fame, and birth of children. | ['bphs2_ch49'] |
| 2 | In the Dasa of the rasi owned or occupied by Mercury, there will be acquisition of wealth and birth of children. | ['bphs2_ch49'] |
| 3 | In the Dasa of the rasi owned or occupied by Jupiter, there will be an increase in the number of children, acquisition of wealth, and enjoyment. | ['bphs2_ch49'] |
| 4 | If the 5th lord is exalted or in the 2nd, 5th, or 9th from the ascendant or conjunct or aspected by Jupiter, obtainment of children will be there. | ['ch16_s013'] |
| 5 | If the 5th lord is in the 2nd, the native will have many sons and wealth, be a pater familias, be honorable, be attached to his spouse, and be famous in the world. | ['ch24_s036'] |
| 6 | If the 5th lord is in the 5th, the native will have progeny if related to a benefic; there will be no issues if a malefic is related to the said 5th lord placed in the 5th. | ['ch24_s039'] |
| 7 | If the 5th lord is in the 6th, the native will obtain such sons who will be equal to his enemies or will lose them, or will acquire an adopted or purchased son. | ['ch24_s039'] |
| 8 | If Saturn, the Moon, and Mercury are together in the 9th from one of the said places, there will be no son at all while the Sun, Jupiter, and Rahu so placed will give a number of sons. | ['ch30_s001'] |

### Q3 -- What does my chart say about my health?

claims = 2

| claim # | statement | segment_ids |
|---|---|---|
| 1 | The native's health may be affected by phlegmatic disorders, such as breathing troubles or lung disorders, if the 12th lord is in the ascendant. | ['ch24_s108'] |
| 2 | If the 6th lord is in the 6th house, the native will be free from diseases and enjoy happiness of conveyances. | ['ch24_s053'] |

## 3. THE DECISION COLUMN -- cited segment ids vs whole-chapter unit ids

| # | question | segment ids cited (contain `_s`) | whole-chapter unit ids cited | segment id list | unit id list |
|---|---|---|---|---|---|
| 1 | What does my chart say about my career? | 0 | 1 | [] | ['bphs2_ch48'] |
| 2 | What does my chart say about my children? | 4 | 1 | ['ch16_s013', 'ch24_s036', 'ch24_s039', 'ch30_s001'] | ['bphs2_ch49'] |
| 3 | What does my chart say about my health? | 2 | 0 | ['ch24_s053', 'ch24_s108'] | [] |

Questions citing >=1 real segment id: 2 / 3

## 4. Ghost count per question

| # | question | ghost count | ghosts |
|---|---|---|---|
| 1 | What does my chart say about my career? | 0 | (none) |
| 2 | What does my chart say about my children? | 0 | (none) |
| 3 | What does my chart say about my health? | 0 | (none) |

## 5. Readings, verbatim

### Q1 -- What does my chart say about my career?

The chart indicates that the 10th lord is placed in the 4th house. According to the reference material, this placement suggests recognition from and awards by the government during the Dasa of the 10th lord. This could imply a favorable period for career advancement or public recognition. However, without additional information on the specific planets involved or their aspects, further details about the career cannot be provided.

silent_on: ['nakshatras', 'planets in signs', 'aspects', 'yogas', 'dasa periods', 'transits', 'specific career fields', 'career changes', 'career success or failure', 'career timing']

### Q2 -- What does my chart say about my children?

The chart suggests potential for children during certain Dasa periods, particularly those associated with the Moon, Mercury, and Jupiter, which are linked to the birth of children and an increase in their number. The placement and condition of the 5th lord are crucial in determining progeny. If the 5th lord is exalted or well-placed, it indicates the likelihood of having children. Conversely, if the 5th lord is afflicted or in a challenging position, it may indicate difficulties or loss related to children. The presence of benefic influences on the 5th house or its lord generally supports progeny, while malefic influences may hinder it. Additionally, specific planetary combinations in the 9th house can influence the number of children, with certain combinations indicating no children and others suggesting many.

silent_on: ['specific planetary positions', 'aspects', 'nakshatras', 'detailed Dasa periods', 'specific yogas', 'remedial measures', 'Upapada and its effects', 'specific house placements', 'specific sign placements', 'specific conjunctions', 'specific aspects', 'specific Navamsa positions']

### Q3 -- What does my chart say about my health?

The chart suggests that the native may experience phlegmatic disorders if the 12th lord is in the ascendant, which could manifest as breathing troubles or lung disorders. However, if the 6th lord is in the 6th house, the native is likely to be free from diseases and enjoy happiness related to conveyances. Overall, the chart indicates a mixed influence on health, with potential for both health challenges and resilience.

silent_on: ['specific diseases related to planets or signs not mentioned in the chart facts', 'effects of specific planetary positions not mentioned in the chart facts', 'remedial measures for health issues', 'timing of health issues', 'effects of specific dasas on health']

## Deviation from prediction

2/3 questions cited >=1 real segment id -- consistent with the stated prediction (>=2 of 3). POC PASSES per the decision rule.

Total OpenAI spend this run: ~$0.1839

