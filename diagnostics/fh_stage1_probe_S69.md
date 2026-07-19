# S69 F-H Stage-1 extraction probe -- diagnostics only, throwaway

Generated 2026-07-19T10:52:36.149807+00:00. Zero recommendations -- measure-first; ruling is design chat's. See `scripts/probe_fh_stage1_extraction.py` for full methodology, frozen-data provenance, and the documented gated-set-reconstruction gap.

## Reconstruction-fidelity assert

**PASSED.** All 14 transplanted chunk_ids matched live ChromaDB content exactly (collection.get by id, not a similarity query). All 12 cells ran.

## Methodology note -- gated-set reconstruction gap (documented, not silently patched)

Neither frozen artifact records chunk_id/text for gated-but-never-cited chunks from pass 4's 3 runs. This probe's per-feature gated set is therefore the RECOVERABLE subset only -- see GATED_SETS in the script for the exact (page, score) entries excluded per run/feature, and the module docstring for the A/B cross-fill justification (byte-identical LR query text -> identical retrieval, evidenced by identical (page, score) triples). 'markings/other features' and 'mount of jupiter' are excluded entirely (0 recoverable chunks / 0 gated chunks respectively in all 3 runs). Probed feature set: life line, head line, heart line, fate line, thumb, fingers, mount of venus.

## 12-cell success-criteria matrix

| Run | Model | Temp | SC-1 (no p98_c1 supports) | SC-2 (no U-row reappear) | SC-3 (chunk_id in gated set) | SC-4 (fate-line precondition) | SC-5 (JSON parse rate) |
|---|---|---|---|---|---|---|---|
| Run A | gpt-4o | 0 | PASS | PASS | PASS | FAIL | PASS |
| Run A | gpt-4o | 0.3 | PASS | PASS | PASS | FAIL | PASS |
| Run A | gpt-4o-mini | 0 | PASS | PASS | PASS | FAIL | PASS |
| Run A | gpt-4o-mini | 0.3 | PASS | PASS | PASS | FAIL | PASS |
| Run B | gpt-4o | 0 | PASS | PASS | PASS | FAIL | PASS |
| Run B | gpt-4o | 0.3 | PASS | PASS | PASS | FAIL | PASS |
| Run B | gpt-4o-mini | 0 | PASS | PASS | PASS | FAIL | PASS |
| Run B | gpt-4o-mini | 0.3 | PASS | PASS | PASS | FAIL | PASS |
| Run C | gpt-4o | 0 | PASS | PASS | PASS | FAIL | PASS |
| Run C | gpt-4o | 0.3 | PASS | PASS | PASS | FAIL | PASS |
| Run C | gpt-4o-mini | 0 | PASS | PASS | PASS | FAIL | PASS |
| Run C | gpt-4o-mini | 0.3 | PASS | PASS | PASS | FAIL | PASS |

## SC failures -- verbatim claim + chunk excerpt

### Run A / gpt-4o / temp=0 -- SC-4
- fate line: p163_c1 offered but no claim has condition_text referencing 'line of life'/'life line'. Fate-line claims extracted: []

### Run A / gpt-4o / temp=0.3 -- SC-4
- fate line: p163_c1 offered but no claim has condition_text referencing 'line of life'/'life line'. Fate-line claims extracted: []

### Run A / gpt-4o-mini / temp=0 -- SC-4
- fate line: p163_c1 offered but no claim has condition_text referencing 'line of life'/'life line'. Fate-line claims extracted: []

### Run A / gpt-4o-mini / temp=0.3 -- SC-4
- fate line: p163_c1 offered but no claim has condition_text referencing 'line of life'/'life line'. Fate-line claims extracted: []

### Run B / gpt-4o / temp=0 -- SC-4
- fate line: p163_c1 offered but no claim has condition_text referencing 'line of life'/'life line'. Fate-line claims extracted: []

### Run B / gpt-4o / temp=0.3 -- SC-4
- fate line: p163_c1 offered but no claim has condition_text referencing 'line of life'/'life line'. Fate-line claims extracted: []

### Run B / gpt-4o-mini / temp=0 -- SC-4
- fate line: p163_c1 offered but no claim has condition_text referencing 'line of life'/'life line'. Fate-line claims extracted: []

### Run B / gpt-4o-mini / temp=0.3 -- SC-4
- fate line: p163_c1 offered but no claim has condition_text referencing 'line of life'/'life line'. Fate-line claims extracted: []

### Run C / gpt-4o / temp=0 -- SC-4
- fate line: p163_c1 offered but no claim has condition_text referencing 'line of life'/'life line'. Fate-line claims extracted: []

### Run C / gpt-4o / temp=0.3 -- SC-4
- fate line: p163_c1 offered but no claim has condition_text referencing 'line of life'/'life line'. Fate-line claims extracted: []

### Run C / gpt-4o-mini / temp=0 -- SC-4
- fate line: p163_c1 offered but no claim has condition_text referencing 'line of life'/'life line'. Fate-line claims extracted: []

### Run C / gpt-4o-mini / temp=0.3 -- SC-4
- fate line: p163_c1 offered but no claim has condition_text referencing 'line of life'/'life line'. Fate-line claims extracted: []

## Full extracted inventories per cell (appendix)

<details><summary>Run A / gpt-4o / temp=0</summary>

**life line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p134_c1', 'cheiroslanguageo00chei_1_p139_c0']
- `C1` [cheiroslanguageo00chei_1_p139_c0] valence=supports cond=None
  claim_text: 'When the line of life sweeps far out into the hand, it is a sign of good physical strength and long life.'
  observation_basis: 'Present, deep, long, curves around the base of the thumb, no breaks or chains visible.'
- `C2` [cheiroslanguageo00chei_1_p134_c1] valence=supports cond=None
  claim_text: 'A long, narrow, and deep line of life without irregularities, breaks, or crosses promises long life, good health, and vitality.'
  observation_basis: 'Present, deep, long, curves around the base of the thumb, no clear breaks or forks'

**head line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p145_c0', 'cheiroslanguageo00chei_1_p147_c1']

**heart line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p160_c2']

**fate line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p163_c1']

**thumb** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p88_c0']

**fingers** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p96_c0', 'cheiroslanguageo00chei_1_p98_c1']
- `C1` [cheiroslanguageo00chei_1_p98_c1] valence=corrective cond=None
  claim_text: 'The belief that fingers must be longer than the palm to indicate an intellectual nature is erroneous and misleading.'
  observation_basis: 'Fingers are long relative to the palm'

**mount of venus** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p112_c0']
- `C1` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'A well-developed Mount of Venus indicates strong and robust health.'
  observation_basis: 'Mount of Venus appears developed'
- `C2` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'A well-developed Mount of Venus denotes affection, sympathy toward others, benevolence, a desire to please, love and worship of beauty, love of color, and melody in music, and the attraction of the one sex to the other.'
  observation_basis: 'Mount of Venus appears developed'

</details>

<details><summary>Run A / gpt-4o / temp=0.3</summary>

**life line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p134_c1', 'cheiroslanguageo00chei_1_p139_c0']
- `C1` [cheiroslanguageo00chei_1_p139_c0] valence=supports cond=None
  claim_text: 'When the line of life sweeps far out into the hand, allowing the Mount of Venus greater scope, it is a sign of good physical strength and long life.'
  observation_basis: 'Present, deep, long, curves around the base of the thumb, no breaks or chains visible.'
- `C2` [cheiroslanguageo00chei_1_p134_c1] valence=supports cond=None
  claim_text: 'A long, narrow, and deep life line without irregularities, breaks, or crosses promises long life, good health, and vitality.'
  observation_basis: 'Present, deep, long, curves around the base of the thumb, no breaks or chains visible.'

**head line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p145_c0', 'cheiroslanguageo00chei_1_p147_c1']

**heart line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p160_c2']

**fate line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p163_c1']

**thumb** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p88_c0']

**fingers** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p96_c0', 'cheiroslanguageo00chei_1_p98_c1']
- `C1` [cheiroslanguageo00chei_1_p98_c1] valence=corrective cond=None
  claim_text: 'The belief that fingers must be longer than the palm to show an intellectual nature is erroneous and misleading.'
  observation_basis: 'Fingers are long relative to the palm'

**mount of venus** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p112_c0']
- `C1` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'A well-developed Mount of Venus indicates strong and robust health.'
  observation_basis: 'Mount of Venus appears developed'
- `C2` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'A well-developed Mount of Venus denotes affection, sympathy toward others, benevolence, a desire to please, love and worship of beauty, love of color, and melody in music, and the attraction of the one sex to the other.'
  observation_basis: 'Mount of Venus appears developed'

</details>

<details><summary>Run A / gpt-4o-mini / temp=0</summary>

**life line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p134_c1', 'cheiroslanguageo00chei_1_p139_c0']
- `C1` [cheiroslanguageo00chei_1_p139_c0] valence=supports cond=None
  claim_text: 'A line of life that sweeps far out into the hand indicates good physical strength and long life.'
  observation_basis: 'Present, deep, long, curves around the base of the thumb, no breaks or chains visible.'
- `C2` [cheiroslanguageo00chei_1_p134_c1] valence=supports cond=None
  claim_text: 'A long, narrow, and deep line of life without irregularities, breaks, or crosses promises long life, good health, and vitality.'
  observation_basis: 'Present, deep, long, curves around the base of the thumb, no clear breaks or forks.'

**head line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p145_c0', 'cheiroslanguageo00chei_1_p147_c1']
- `C1` [cheiroslanguageo00chei_1_p145_c0] valence=supports cond=None
  claim_text: 'The line of head relates principally to the mentality of the subject, including intellectual strength or weakness and the direction and quality of talent.'
  observation_basis: 'Present, deep, long, slightly curved, runs across the palm, no breaks or chains visible.'

**heart line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p160_c2']

**fate line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p163_c1']

**thumb** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p88_c0']

**fingers** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p96_c0', 'cheiroslanguageo00chei_1_p98_c1']
- `C1` [cheiroslanguageo00chei_1_p98_c1] valence=corrective cond=None
  claim_text: 'The statement that in every case the fingers must be longer than the palm is erroneous and misleading.'
  observation_basis: 'Fingers are long relative to the palm.'

**mount of venus** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p112_c0']
- `C1` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'A well-developed Mount of Venus indicates strong and robust health.'
  observation_basis: 'Mount of Venus appears developed; other mounts are unremarkable.'
- `C2` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'A well-developed Mount of Venus indicates strong and robust health.'
  observation_basis: 'Mount of Venus appears developed.'
- `C3` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'An abnormally large Mount of Venus indicates a violent passion for the opposite sex.'
  observation_basis: 'Mount of Venus appears developed.'
- `C4` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'This mount denotes affection, sympathy toward others, benevolence, a desire to please, love and worship of beauty, love of color, and melody in music, and the attraction of the one sex to the other.'
  observation_basis: 'Mount of Venus appears developed.'

</details>

<details><summary>Run A / gpt-4o-mini / temp=0.3</summary>

**life line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p134_c1', 'cheiroslanguageo00chei_1_p139_c0']
- `C1` [cheiroslanguageo00chei_1_p139_c0] valence=supports cond=None
  claim_text: 'A line of life that sweeps far out into the hand indicates good physical strength and long life.'
  observation_basis: 'Present, deep, long, curves around the base of the thumb, no breaks or chains visible.'
- `C2` [cheiroslanguageo00chei_1_p134_c1] valence=supports cond=None
  claim_text: 'A long, narrow, and deep line of life without irregularities, breaks, or crosses promises long life, good health, and vitality.'
  observation_basis: 'Present, deep, long, curves around the base of the thumb, no clear breaks or forks.'

**head line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p145_c0', 'cheiroslanguageo00chei_1_p147_c1']
- `C1` [cheiroslanguageo00chei_1_p145_c0] valence=supports cond=None
  claim_text: 'The line of head relates principally to the mentality of the subject, including intellectual strength or weakness and talent direction and quality.'
  observation_basis: 'Present, deep, long, slightly curved, runs across the palm, no breaks or chains visible.'
- `C2` [cheiroslanguageo00chei_1_p145_c0] valence=supports cond=None
  claim_text: 'The line of head relates principally to the mentality of the subject, including intellectual strength or weakness and talent direction and quality.'
  observation_basis: 'Present, deep, long, slightly curved, no clear breaks or forks.'

**heart line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p160_c2']

**fate line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p163_c1']

**thumb** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p88_c0']

**fingers** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p96_c0', 'cheiroslanguageo00chei_1_p98_c1']
- `C1` [cheiroslanguageo00chei_1_p98_c1] valence=corrective cond=None
  claim_text: 'The statement that in every case the fingers must be longer than the palm is erroneous and misleading.'
  observation_basis: 'Fingers are long relative to the palm.'

**mount of venus** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p112_c0']
- `C1` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'A well-developed Mount of Venus indicates strong and robust health.'
  observation_basis: 'Mount of Venus appears developed; other mounts are unremarkable.'
- `C2` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'A well-developed Mount of Venus indicates strong and robust health.'
  observation_basis: 'Mount of Venus appears developed.'
- `C3` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'An abnormally large Mount of Venus indicates a violent passion for the opposite sex.'
  observation_basis: 'Mount of Venus appears developed.'
- `C4` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'This mount denotes affection, sympathy toward others, benevolence, a desire to please, love and worship of beauty, love of color, and melody in music, and the attraction of the one sex to the other.'
  observation_basis: 'Mount of Venus appears developed.'

</details>

<details><summary>Run B / gpt-4o / temp=0</summary>

**life line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p134_c1', 'cheiroslanguageo00chei_1_p139_c0']
- `C1` [cheiroslanguageo00chei_1_p139_c0] valence=supports cond=None
  claim_text: 'When the line of life sweeps far out into the hand, it is a sign of good physical strength and long life.'
  observation_basis: 'Present, deep, long, curves around the base of the thumb, no breaks or chains visible.'
- `C2` [cheiroslanguageo00chei_1_p134_c1] valence=supports cond=None
  claim_text: 'A long, narrow, and deep line of life without irregularities promises long life, good health, and vitality.'
  observation_basis: 'Present, deep, long, curves around the base of the thumb, no clear breaks or forks'

**head line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p145_c0', 'cheiroslanguageo00chei_1_p147_c1']

**heart line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p160_c2']

**fate line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p163_c1']

**thumb** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p88_c0']

**fingers** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p96_c0', 'cheiroslanguageo00chei_1_p98_c1']
- `C1` [cheiroslanguageo00chei_1_p98_c1] valence=corrective cond=None
  claim_text: 'The statement that fingers must be longer than the palm to show the intellectual nature is erroneous and misleading.'
  observation_basis: 'Fingers are long relative to the palm'

**mount of venus** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p112_c0']
- `C1` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'A well-developed Mount of Venus indicates strong and robust health.'
  observation_basis: 'Mount of Venus appears developed'
- `C2` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'A well-developed Mount of Venus denotes affection, sympathy toward others, benevolence, a desire to please, love and worship of beauty, love of color, and melody in music, and the attraction of the one sex to the other.'
  observation_basis: 'Mount of Venus appears developed'

</details>

<details><summary>Run B / gpt-4o / temp=0.3</summary>

**life line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p134_c1', 'cheiroslanguageo00chei_1_p139_c0']
- `C1` [cheiroslanguageo00chei_1_p139_c0] valence=supports cond=None
  claim_text: 'A life line that sweeps far out into the hand, allowing the Mount of Venus greater scope, is a sign of good physical strength and long life.'
  observation_basis: 'Present, deep, long, curves around the base of the thumb, no breaks or chains visible.'
- `C2` [cheiroslanguageo00chei_1_p134_c1] valence=supports cond=None
  claim_text: 'A long, narrow, and deep life line without irregularities, breaks, or crosses promises long life, good health, and vitality.'
  observation_basis: 'Present, deep, long, curves around the base of the thumb, no clear breaks or forks'

**head line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p145_c0', 'cheiroslanguageo00chei_1_p147_c1']

**heart line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p160_c2']

**fate line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p163_c1']

**thumb** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p88_c0']

**fingers** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p96_c0', 'cheiroslanguageo00chei_1_p98_c1']

**mount of venus** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p112_c0']
- `C1` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'A well-developed Mount of Venus indicates strong and robust health.'
  observation_basis: 'Mount of Venus appears developed'
- `C2` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'A well-developed Mount of Venus denotes affection, sympathy toward others, benevolence, a desire to please, love and worship of beauty, love of color, and melody in music, and the attraction of the one sex to the other.'
  observation_basis: 'Mount of Venus appears developed'

</details>

<details><summary>Run B / gpt-4o-mini / temp=0</summary>

**life line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p134_c1', 'cheiroslanguageo00chei_1_p139_c0']
- `C1` [cheiroslanguageo00chei_1_p139_c0] valence=supports cond=None
  claim_text: 'A line of life that sweeps far out into the hand indicates good physical strength and long life.'
  observation_basis: 'Present, deep, long, curves around the base of the thumb, no breaks or chains visible.'
- `C2` [cheiroslanguageo00chei_1_p134_c1] valence=supports cond=None
  claim_text: 'A long, narrow, and deep line of life without irregularities, breaks, or crosses promises long life, good health, and vitality.'
  observation_basis: 'Present, deep, long, curves around the base of the thumb, no clear breaks or forks.'

**head line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p145_c0', 'cheiroslanguageo00chei_1_p147_c1']
- `C1` [cheiroslanguageo00chei_1_p145_c0] valence=supports cond=None
  claim_text: 'The line of head relates principally to the mentality of the subject, including intellectual strength or weakness and the direction and quality of talent.'
  observation_basis: 'Present, deep, long, slightly curved, runs across the palm, no breaks or chains visible.'

**heart line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p160_c2']

**fate line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p163_c1']

**thumb** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p88_c0']

**fingers** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p96_c0', 'cheiroslanguageo00chei_1_p98_c1']
- `C1` [cheiroslanguageo00chei_1_p98_c1] valence=corrective cond=None
  claim_text: 'The statement that in every case the fingers must be longer than the palm is erroneous and misleading.'
  observation_basis: 'Fingers are long relative to the palm.'

**mount of venus** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p112_c0']
- `C1` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'A well-developed Mount of Venus indicates strong and robust health.'
  observation_basis: 'Mount of Venus appears developed; other mounts are unremarkable.'
- `C2` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'A well-developed Mount of Venus indicates strong and robust health.'
  observation_basis: 'Mount of Venus appears developed.'
- `C3` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'An abnormally large Mount of Venus indicates a violent passion for the opposite sex.'
  observation_basis: 'Mount of Venus appears developed.'
- `C4` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'This mount denotes affection, sympathy toward others, benevolence, a desire to please, love and worship of beauty, love of color, and melody in music, and the attraction of the one sex to the other.'
  observation_basis: 'Mount of Venus appears developed.'

</details>

<details><summary>Run B / gpt-4o-mini / temp=0.3</summary>

**life line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p134_c1', 'cheiroslanguageo00chei_1_p139_c0']
- `C1` [cheiroslanguageo00chei_1_p139_c0] valence=supports cond=None
  claim_text: 'A line of life that sweeps far out into the hand indicates good physical strength and long life.'
  observation_basis: 'Present, deep, long, curves around the base of the thumb, no breaks or chains visible.'
- `C2` [cheiroslanguageo00chei_1_p134_c1] valence=supports cond=None
  claim_text: 'A long, narrow, and deep line of life without irregularities, breaks, or crosses promises long life, good health, and vitality.'
  observation_basis: 'Present, deep, long, curves around the base of the thumb, no clear breaks or forks.'

**head line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p145_c0', 'cheiroslanguageo00chei_1_p147_c1']
- `C1` [cheiroslanguageo00chei_1_p145_c0] valence=supports cond=None
  claim_text: 'The line of head relates principally to the mentality of the subject, including intellectual strength or weakness and the quality of talent.'
  observation_basis: 'Present, deep, long, slightly curved, runs across the palm, no breaks or chains visible.'

**heart line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p160_c2']

**fate line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p163_c1']

**thumb** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p88_c0']

**fingers** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p96_c0', 'cheiroslanguageo00chei_1_p98_c1']
- `C1` [cheiroslanguageo00chei_1_p98_c1] valence=corrective cond=None
  claim_text: 'The statement that in every case the fingers must be longer than the palm is erroneous and misleading.'
  observation_basis: 'Fingers are long relative to the palm, straight, with rounded fingertips, moderate spacing.'

**mount of venus** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p112_c0']
- `C1` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'A well-developed Mount of Venus indicates strong and robust health.'
  observation_basis: 'Mount of Venus appears developed; other mounts are unremarkable.'
- `C2` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'A well-developed Mount of Venus indicates strong and robust health.'
  observation_basis: 'Mount of Venus appears developed.'
- `C3` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'An abnormally large Mount of Venus indicates a violent passion for the opposite sex.'
  observation_basis: 'Mount of Venus appears developed.'
- `C4` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'The Mount of Venus denotes affection, sympathy, benevolence, and a desire to please.'
  observation_basis: 'Mount of Venus appears developed.'

</details>

<details><summary>Run C / gpt-4o / temp=0</summary>

**life line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p134_c1']
- `C1` [cheiroslanguageo00chei_1_p134_c1] valence=supports cond=None
  claim_text: 'A long, narrow, and deep life line without irregularities, breaks, or crosses promises long life, good health, and vitality.'
  observation_basis: 'Present, deep, long, curves around the base of the thumb, no breaks or chains visible.'

**head line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p123_c0']

**heart line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p159_c3']

**fate line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p163_c1']

**thumb** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p88_c1']

**fingers** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p95_c0']
- `C1` [cheiroslanguageo00chei_1_p95_c0] valence=supports cond=None
  claim_text: 'Long fingers indicate a love of detail in everything, such as decoration, management, and noticing small attentions.'
  observation_basis: 'Fingers are long relative to the palm, straight, with rounded fingertips, moderate spacing.'

**mount of venus** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p112_c0']
- `C1` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'A well-developed Mount of Venus indicates strong and robust health.'
  observation_basis: 'Mount of Venus appears developed'
- `C2` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'A well-developed Mount of Venus denotes affection, sympathy toward others, benevolence, a desire to please, love and worship of beauty, love of color, and melody in music, and the attraction of the one sex to the other.'
  observation_basis: 'Mount of Venus appears developed'

</details>

<details><summary>Run C / gpt-4o / temp=0.3</summary>

**life line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p134_c1']
- `C1` [cheiroslanguageo00chei_1_p134_c1] valence=supports cond=None
  claim_text: 'A long, narrow, and deep life line without irregularities, breaks, or crosses promises long life, good health, and vitality.'
  observation_basis: 'Present, deep, long, curves around the base of the thumb, no breaks or chains visible.'

**head line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p123_c0']

**heart line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p159_c3']

**fate line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p163_c1']

**thumb** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p88_c1']

**fingers** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p95_c0']
- `C1` [cheiroslanguageo00chei_1_p95_c0] valence=supports cond=None
  claim_text: 'Long fingers indicate a love of detail in everything, such as decoration, treatment of others, and management.'
  observation_basis: 'Fingers are long relative to the palm, straight, with rounded fingertips, moderate spacing.'

**mount of venus** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p112_c0']
- `C1` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'A well-developed Mount of Venus indicates strong and robust health.'
  observation_basis: 'Mount of Venus appears developed'
- `C2` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'A well-developed Mount of Venus denotes affection, sympathy toward others, benevolence, a desire to please, love and worship of beauty, love of color, and melody in music, and the attraction of the one sex to the other.'
  observation_basis: 'Mount of Venus appears developed'

</details>

<details><summary>Run C / gpt-4o-mini / temp=0</summary>

**life line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p134_c1']
- `C1` [cheiroslanguageo00chei_1_p134_c1] valence=supports cond=None
  claim_text: 'A long, deep, and uninterrupted life line indicates long life, good health, and vitality.'
  observation_basis: 'Present, deep, long, curves around the base of the thumb, no breaks or chains visible.'

**head line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p123_c0']

**heart line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p159_c3']

**fate line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p163_c1']

**thumb** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p88_c1']

**fingers** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p95_c0']
- `C1` [cheiroslanguageo00chei_1_p95_c0] valence=supports cond=None
  claim_text: 'Long fingers indicate a love of detail in various aspects of life, such as decoration and management.'
  observation_basis: 'Fingers are long relative to the palm.'

**mount of venus** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p112_c0']
- `C1` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'A well-developed Mount of Venus indicates strong and robust health.'
  observation_basis: 'Mount of Venus appears developed; other mounts are unremarkable.'
- `C2` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'A well-developed Mount of Venus indicates strong and robust health.'
  observation_basis: 'Mount of Venus appears developed.'
- `C3` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'An abnormally large Mount of Venus indicates a violent passion for the opposite sex.'
  observation_basis: 'Mount of Venus appears developed.'
- `C4` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'This mount denotes affection, sympathy toward others, and a desire to please.'
  observation_basis: 'Mount of Venus appears developed.'

</details>

<details><summary>Run C / gpt-4o-mini / temp=0.3</summary>

**life line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p134_c1']
- `C1` [cheiroslanguageo00chei_1_p134_c1] valence=supports cond=None
  claim_text: 'A long, deep, and narrow life line without irregularities, breaks, or crosses indicates long life, good health, and vitality.'
  observation_basis: 'Present, deep, long, curves around the base of the thumb, no breaks or chains visible.'

**head line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p123_c0']

**heart line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p159_c3']

**fate line** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p163_c1']

**thumb** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p88_c1']
- `C1` [cheiroslanguageo00chei_1_p88_c1] valence=supports cond=None
  claim_text: "The thumb's flexibility relates significantly to character, with a supple thumb indicating a different nature than a stiff one."
  observation_basis: 'The thumb is of average length and appears to have a moderate angle of flexibility from the palm.'

**fingers** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p95_c0']
- `C1` [cheiroslanguageo00chei_1_p95_c0] valence=supports cond=None
  claim_text: 'Long fingers indicate a love of detail in various aspects of life, including decoration and management.'
  observation_basis: 'Fingers are long relative to the palm.'

**mount of venus** -- status=ok
gated chunks offered: ['cheiroslanguageo00chei_1_p112_c0']
- `C1` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'A well-developed Mount of Venus indicates strong and robust health.'
  observation_basis: 'Mount of Venus appears developed; other mounts are unremarkable.'
- `C2` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'A well-developed Mount of Venus indicates strong and robust health.'
  observation_basis: 'Mount of Venus appears developed.'
- `C3` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'An abnormally large Mount of Venus indicates a violent passion for the opposite sex.'
  observation_basis: 'Mount of Venus appears developed.'
- `C4` [cheiroslanguageo00chei_1_p112_c0] valence=supports cond=None
  claim_text: 'This mount denotes affection, sympathy toward others, benevolence, a desire to please, love and worship of beauty, love of color, and melody in music, and the attraction of the one sex to the other.'
  observation_basis: 'Mount of Venus appears developed.'

</details>

## Comparative metrics (report only, no pass/fail, no proposed floor)

Content-word overlap: lowercase alpha tokens minus stopword set (['a', 'also', 'an', 'and', 'are', 'as', 'at', 'be', 'been', 'being', 'but', 'by', 'for', 'from', 'he', 'her', 'his', 'if', 'in', 'indicate', 'indicates', 'into', 'is', 'it', 'its', 'may', 'might', 'no', 'not', 'of', 'on', 'or', 'she', 'so', 'such', 'suggest', 'suggests', 'than', 'that', 'the', 'their', 'then', 'these', 'they', 'this', 'those', 'to', 'was', 'were', 'when', 'which', 'while', 'who', 'whom', 'with', 'you', 'your']), overlap_ratio = |shared| / min(|claim_tokens|, |chunk_tokens|).

| Run | Model | Temp | Total claims | Per-feature yield | Overlap min/p25/median/p75/max | Prompt tok | Completion tok | Total latency (s) |
|---|---|---|---|---|---|---|---|---|
| Run A | gpt-4o | 0 | 5 | {'life line': 2, 'head line': 0, 'heart line': 0, 'fate line': 0, 'thumb': 0, 'fingers': 1, 'mount of venus': 2} | 0.89/1.00/1.00/1.00/1.00 | 5258 | 549 | 9.15 |
| Run A | gpt-4o | 0.3 | 5 | {'life line': 2, 'head line': 0, 'heart line': 0, 'fate line': 0, 'thumb': 0, 'fingers': 1, 'mount of venus': 2} | 0.90/1.00/1.00/1.00/1.00 | 5258 | 557 | 8.88 |
| Run A | gpt-4o-mini | 0 | 8 | {'life line': 2, 'head line': 1, 'heart line': 0, 'fate line': 0, 'thumb': 0, 'fingers': 1, 'mount of venus': 4} | 0.92/1.00/1.00/1.00/1.00 | 5258 | 771 | 11.72 |
| Run A | gpt-4o-mini | 0.3 | 9 | {'life line': 2, 'head line': 2, 'heart line': 0, 'fate line': 0, 'thumb': 0, 'fingers': 1, 'mount of venus': 4} | 0.92/1.00/1.00/1.00/1.00 | 5258 | 859 | 11.53 |
| Run B | gpt-4o | 0 | 5 | {'life line': 2, 'head line': 0, 'heart line': 0, 'fate line': 0, 'thumb': 0, 'fingers': 1, 'mount of venus': 2} | 1.00/1.00/1.00/1.00/1.00 | 5258 | 544 | 8.41 |
| Run B | gpt-4o | 0.3 | 4 | {'life line': 2, 'head line': 0, 'heart line': 0, 'fate line': 0, 'thumb': 0, 'fingers': 0, 'mount of venus': 2} | 1.00/1.00/1.00/1.00/1.00 | 5258 | 483 | 9.19 |
| Run B | gpt-4o-mini | 0 | 8 | {'life line': 2, 'head line': 1, 'heart line': 0, 'fate line': 0, 'thumb': 0, 'fingers': 1, 'mount of venus': 4} | 0.92/1.00/1.00/1.00/1.00 | 5258 | 771 | 10.94 |
| Run B | gpt-4o-mini | 0.3 | 8 | {'life line': 2, 'head line': 1, 'heart line': 0, 'fate line': 0, 'thumb': 0, 'fingers': 1, 'mount of venus': 4} | 0.92/1.00/1.00/1.00/1.00 | 5258 | 753 | 10.87 |
| Run C | gpt-4o | 0 | 4 | {'life line': 1, 'head line': 0, 'heart line': 0, 'fate line': 0, 'thumb': 0, 'fingers': 1, 'mount of venus': 2} | 0.90/1.00/1.00/1.00/1.00 | 4911 | 462 | 8.70 |
| Run C | gpt-4o | 0.3 | 4 | {'life line': 1, 'head line': 0, 'heart line': 0, 'fate line': 0, 'thumb': 0, 'fingers': 1, 'mount of venus': 2} | 0.89/1.00/1.00/1.00/1.00 | 4911 | 476 | 8.51 |
| Run C | gpt-4o-mini | 0 | 6 | {'life line': 1, 'head line': 0, 'heart line': 0, 'fate line': 0, 'thumb': 0, 'fingers': 1, 'mount of venus': 4} | 0.67/0.88/1.00/1.00/1.00 | 4911 | 544 | 9.30 |
| Run C | gpt-4o-mini | 0.3 | 7 | {'life line': 1, 'head line': 0, 'heart line': 0, 'fate line': 0, 'thumb': 1, 'fingers': 1, 'mount of venus': 4} | 0.50/1.00/1.00/1.00/1.00 | 4911 | 672 | 10.33 |

Pooled overlap distribution (all cells, all claims):
min=0.50 p25=1.00 median=1.00 p75=1.00 max=1.00 (n=73)

Token-cost note: raw prompt/completion token counts reported above, directly from each API response's `usage` field. No dollar-cost conversion performed -- this script has no verified current OpenAI pricing to cite as of this run; converting would risk reporting a fabricated rate as fact.
