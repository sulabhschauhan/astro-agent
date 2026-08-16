# Latest Run: palm LLM-select smoke test — deterministic gate, Case A vs Case B

Model: gpt-4o, temperature=0, runs per case=5

## Full rule corpus (pre-gate)

| id | involves | page |
|---|---|---|
| H_002 | head | 146 |
| H_026 | head | 146 |
| H_027 | head | 145 |
| HL_001 | heart | 156 |
| HL_002 | heart | 156 |
| H_005 | head | 147 |
| HL_019 | heart | 159 |

## Hard-prerequisite gate (in-file, H_027/H_002 only)

- H_027 requires head.origin includes 'Jupiter'
- H_002 requires head.origin == 'touching_life'
- All other rules have no prerequisite and always pass through.

## Case A

```json
{
  "head": {
    "origin": "Jupiter_touching_life",
    "length": "long",
    "direction": "sloping_gentle"
  },
  "heart": {
    "origin": "finger_of_Jupiter"
  },
  "gap": "moderate"
}
```

**Gate result:** dropped ['H_002']; candidate rules handed to the LLM: ['H_026', 'H_027', 'HL_001', 'HL_002', 'H_005', 'HL_019']

### Case A per-run results

| run | gate_correct | case_ok | quotes_ok | fired_ids |
|---|---|---|---|---|
| 1 | True | True | True | HL_002,H_026,H_027 |
| 2 | True | True | True | HL_002,H_026,H_027 |
| 3 | True | True | True | HL_002,H_026,H_027 |
| 4 | True | True | True | HL_002,H_026,H_027 |
| 5 | True | True | True | HL_002,H_026,H_027 |

**Case A stability: 5/5 runs fully clean on all 3 checks.**

### Case A raw per-run detail

#### Run 1
- fired_ids: ['HL_002', 'H_026', 'H_027']
- unmatched_features: ['gap']
- combined_reading: 'The hand shows a leaning toward imaginative work due to the slight slope of the head line. The head line, rising from Jupiter and touching the line of life, is long and indicates a powerful nature with talent, energy, daring determination, boundless ambition, and reason. The heart line, rising from the finger of Jupiter, denotes an excess of all the foregoing qualities.'

#### Run 2
- fired_ids: ['HL_002', 'H_026', 'H_027']
- unmatched_features: ['gap']
- combined_reading: 'The head line has a slight slope, indicating a leaning toward imaginative work. Rising from Jupiter and touching the line of life, the long head line is the most powerful of all, suggesting talent, energy, daring determination of purpose, and boundless ambition combined with reason. The heart line rising from the finger of Jupiter denotes the excess of all the foregoing qualities.'

#### Run 3
- fired_ids: ['HL_002', 'H_026', 'H_027']
- unmatched_features: ['gap']
- combined_reading: 'There is a leaning toward imaginative work. The subject will have talent, energy, and daring determination of purpose, with boundless ambition combined with reason. The excess of all the foregoing qualities is denoted.'

#### Run 4
- fired_ids: ['HL_002', 'H_026', 'H_027']
- unmatched_features: ['gap']
- combined_reading: 'There is a leaning toward imaginative work. The subject will have talent, energy, and daring determination of purpose, with boundless ambition combined with reason. The excess of all the foregoing qualities is denoted.'

#### Run 5
- fired_ids: ['HL_002', 'H_026', 'H_027']
- unmatched_features: ['gap']
- combined_reading: 'There is a leaning toward imaginative work. The head line, rising from Jupiter and touching the line of life, is long and the most powerful of all, indicating talent, energy, daring determination of purpose, and boundless ambition combined with reason. The heart line rising from the finger of Jupiter denotes the excess of all the foregoing qualities.'

## Case B

```json
{
  "head": {
    "origin": "touching_life",
    "length": "long",
    "direction": "sloping_gentle"
  },
  "heart": {
    "origin": "finger_of_Jupiter"
  },
  "gap": "moderate"
}
```

**Gate result:** dropped ['H_027']; candidate rules handed to the LLM: ['H_002', 'H_026', 'HL_001', 'HL_002', 'H_005', 'HL_019']

### Case B per-run results

| run | gate_correct | case_ok | quotes_ok | jupiter_absent | fired_ids |
|---|---|---|---|---|---|
| 1 | True | True | True | True | HL_002,H_002,H_026 |
| 2 | True | True | True | True | HL_002,H_002,H_026 |
| 3 | True | True | True | True | HL_002,H_002,H_026 |
| 4 | True | True | True | True | HL_002,H_002,H_026 |
| 5 | True | True | True | True | HL_002,H_002,H_026 |

**Case B stability: 5/5 runs fully clean on all 4 checks.**

### Case B Jupiter flag (loud)

'jupiter_literal_present' is EXPECTED true (heart.origin is still finger_of_Jupiter, so HL_002 legitimately mentions Jupiter, and H_027 was gated out so it never reaches the model at all). 'jupiter_absent' (graded above) is scoped to HEAD-tagged content only: no fired quote from a head-tagged rule contains 'jupiter', and no sentence in combined_reading ties 'head' and 'jupiter' together. Since H_027 is not even a candidate this run, any head-Jupiter claim here would be a pure hallucination, not a misapplied-but-real citation.

| run | jupiter_literal_present | head_jupiter_claim (FABRICATION) |
|---|---|---|
| 1 | True | False |
| 2 | True | False |
| 3 | True | False |
| 4 | True | False |
| 5 | True | False |

No Case B run asserted a head-line Jupiter-origin claim.

### Case B raw per-run detail

#### Run 1
- fired_ids: ['HL_002', 'H_002', 'H_026']
- unmatched_features: ['gap']
- combined_reading: 'The line of head from the commencement of the line of life, and connected with it, indicates a sensitive and more nervous temperament; it denotes excess of caution. When the entire line has a slight slope, there is a leaning toward imaginative work. Next we will consider the line rising from the Mount of Jupiter, even from the finger itself. This denotes the excess of all the foregoing qualities.'

#### Run 2
- fired_ids: ['HL_002', 'H_002', 'H_026']
- unmatched_features: ['gap']
- combined_reading: 'The line of head from the commencement of the line of life, and connected with it, indicates a sensitive and more nervous temperament; it denotes excess of caution. When the entire line has a slight slope, there is a leaning toward imaginative work. Next we will consider the line rising from the Mount of Jupiter, even from the finger itself. This denotes the excess of all the foregoing qualities.'

#### Run 3
- fired_ids: ['HL_002', 'H_002', 'H_026']
- unmatched_features: ['gap']
- combined_reading: 'The line of head from the commencement of the line of life, and connected with it, indicates a sensitive and more nervous temperament; it denotes excess of caution. When the entire line has a slight slope, there is a leaning toward imaginative work. Next we will consider the line rising from the Mount of Jupiter, even from the finger itself. This denotes the excess of all the foregoing qualities.'

#### Run 4
- fired_ids: ['HL_002', 'H_002', 'H_026']
- unmatched_features: ['gap']
- combined_reading: 'The line of head from the commencement of the line of life, and connected with it, indicates a sensitive and more nervous temperament; it denotes excess of caution. When the entire line has a slight slope, there is a leaning toward imaginative work. Next we will consider the line rising from the Mount of Jupiter, even from the finger itself. This denotes the excess of all the foregoing qualities.'

#### Run 5
- fired_ids: ['HL_002', 'H_002', 'H_026']
- unmatched_features: ['gap']
- combined_reading: 'The line of head from the commencement of the line of life, and connected with it, indicates a sensitive and more nervous temperament; it denotes excess of caution. When the entire line has a slight slope, there is a leaning toward imaginative work. Next we will consider the line rising from the Mount of Jupiter, even from the finger itself. This denotes the excess of all the foregoing qualities.'
