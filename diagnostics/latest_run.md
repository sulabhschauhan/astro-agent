# Pre-flight smoke probe for Ring 3 pass 4 (S68 close-out state)

**THROWAWAY SCRIPT. NOT A SCORING PASS.** Ring 3 pass 4 itself still requires fresh uploads through the real app with live human checkpoints (CLAUDE.md T4 golden semantics / Palm human checkpoint locks). This probe uses `data/test_images/` fixtures (sanctioned for mechanical probes only) to catch a pipeline defect in the S68 F-C/F-A/F-B landed work before spending a fresh-upload pass-4 run on it. Vision descriptions below are captured verbatim but are NOT human-confirmed -- this headless script bypasses the S65/S66 F1 checkpoint UI by construction; that gate is unaffected and still applies to any real user-facing flow.

Run shape: Run-C (hardest case) -- both palm images + hand_detail, live OpenAI vision + generation.

## Fixtures

- LEFT: `C:\Users\sulab\Documents\Python Scripts\astro-agent\data\test_images\palm_left_test.jpg`
- RIGHT: `C:\Users\sulab\Documents\Python Scripts\astro-agent\data\test_images\palm_right_test.jpg`
- HAND_DETAIL: `C:\Users\sulab\Documents\Python Scripts\astro-agent\data\test_images\Back Hand.jpeg`

## Confirmed descriptions (NOT human-confirmed -- headless probe)

**LEFT** (verbatim):
```
HAND SHAPE: Square palm, overall build is medium.

FINGERS: Fingers are long relative to the palm, appear straight, fingertips are rounded, spacing is moderate.

THUMB: Medium size, set moderately low, wide angle from the palm.

LIFE LINE: Present, deep, long, curves around the base of the thumb, no clear breaks or forks visible.

HEAD LINE: Present, deep, long, slightly curved, no clear breaks or forks visible.

HEART LINE: Present, deep, long, curves slightly upwards, no clear breaks or forks visible.

FATE LINE: Barely visible.

OTHER LINES: Not clearly visible.

MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.

MARKS: No clear marks visible.
```

**RIGHT** (verbatim):
```
HAND SHAPE: Square palm, overall build is medium.

FINGERS: Fingers are slightly longer than the palm, appear straight, fingertips are rounded, spacing is moderate.

THUMB: Medium size, set moderately low, wide angle from the palm.

LIFE LINE: Present, deep, long, curves around the base of the thumb, no clear breaks or forks.

HEAD LINE: Present, deep, long, slightly curved, starts joined with the life line.

HEART LINE: Present, deep, curves slightly upward, ends below the index finger.

FATE LINE: Present, moderately deep, starts from the base of the palm and runs towards the middle finger.

OTHER LINES: Sun line is not clearly visible, health and marriage lines not clearly visible.

MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.

MARKS: No clear marks such as crosses, stars, grilles, squares, or moles visible.
```

**HAND_DETAIL** (verbatim):
```
The image shows a hand with the following observable features:

- **Hand Shape**: The hand appears broad with a relatively square palm.
- **Finger Lengths**: The fingers are of moderate length. The index finger is slightly shorter than the middle finger, and the ring finger is slightly longer than the index finger. The little finger is noticeably shorter.
- **Thumb**: The thumb is of average length with a moderate angle of flexibility, indicating it is not too rigid or too flexible.
- **Visible Lines**:
  - **Life Line**: A prominent line curves around the base of the thumb.
  - **Head Line**: Appears to be separate from the life line, running across the palm.
  - **Heart Line**: Curves across the top of the palm, below the fingers.
  - **Fate Line**: Not clearly visible in this image.
- **Mounts**: The mounts of Venus (base of the thumb) and Jupiter (below the index finger) appear slightly raised.
- **Markings**: There are no unusual markings or features that stand out.
- **Other Features**: There is visible hair on the back of the hand and fingers.

This description is based solely on the physical characteristics visible in the image.
```

## Per-feature retrieval map (raw, pre-gate, all 10 registry features)

| Feature | Chunks (page_ref, score, chunk_id) |
|---|---|
| life line | (p.135, 0.6131, cheiroslanguageo00chei_1_p135_c0); (p.134, 0.6063, cheiroslanguageo00chei_1_p134_c1); (p.134, 0.5725, cheiroslanguageo00chei_1_p134_c0) |
| head line | (p.134, 0.5581, cheiroslanguageo00chei_1_p134_c2); (p.147, 0.5525, cheiroslanguageo00chei_1_p147_c1); (p.139, 0.5422, cheiroslanguageo00chei_1_p139_c1) |
| heart line | (p.160, 0.5735, cheiroslanguageo00chei_1_p160_c2); (p.160, 0.5706, cheiroslanguageo00chei_1_p160_c1); (p.159, 0.5534, cheiroslanguageo00chei_1_p159_c2) |
| fate line | (p.165, 0.5958, cheiroslanguageo00chei_1_p165_c1); (p.163, 0.5942, cheiroslanguageo00chei_1_p163_c1); (p.165, 0.5739, cheiroslanguageo00chei_1_p165_c0) |
| sun line | _(none -- skipped or retrieval failed)_ |
| thumb | (p.88, 0.5514, cheiroslanguageo00chei_1_p88_c1); (p.87, 0.5489, cheiroslanguageo00chei_1_p87_c0); (p.89, 0.5339, cheiroslanguageo00chei_1_p89_c0) |
| fingers | (p.98, 0.5885, cheiroslanguageo00chei_1_p98_c1); (p.96, 0.5284, cheiroslanguageo00chei_1_p96_c1); (p.96, 0.5282, cheiroslanguageo00chei_1_p96_c0) |
| mount of venus | (p.112, 0.6824, cheiroslanguageo00chei_1_p112_c0); (p.111, 0.6698, cheiroslanguageo00chei_1_p111_c1); (p.111, 0.5591, cheiroslanguageo00chei_1_p111_c0) |
| mount of jupiter | (p.112, 0.6630, cheiroslanguageo00chei_1_p112_c0); (p.111, 0.6457, cheiroslanguageo00chei_1_p111_c1); (p.113, 0.5894, cheiroslanguageo00chei_1_p113_c0) |
| markings/other features | (p.221, 0.4764, cheiroslanguageo00chei_1_p221_c1); (p.107, 0.4382, cheiroslanguageo00chei_1_p107_c0); (p.172, 0.4305, cheiroslanguageo00chei_1_p172_c1) |

## Support gate verdicts

- **supported_features** (registry order): ['life line', 'head line', 'heart line', 'fate line', 'thumb', 'fingers', 'mount of venus', 'mount of jupiter', 'markings/other features']
- **unsupported_features** (registry order): []
- **genuine negative-absence** (in neither tuple -- nothing to support, nothing to decline): ['sun line']
- **valid_chunk_ids** (V-2 union, count=24): ['cheiroslanguageo00chei_1_p107_c0', 'cheiroslanguageo00chei_1_p111_c0', 'cheiroslanguageo00chei_1_p111_c1', 'cheiroslanguageo00chei_1_p112_c0', 'cheiroslanguageo00chei_1_p113_c0', 'cheiroslanguageo00chei_1_p134_c0', 'cheiroslanguageo00chei_1_p134_c1', 'cheiroslanguageo00chei_1_p134_c2', 'cheiroslanguageo00chei_1_p135_c0', 'cheiroslanguageo00chei_1_p139_c1', 'cheiroslanguageo00chei_1_p147_c1', 'cheiroslanguageo00chei_1_p159_c2', 'cheiroslanguageo00chei_1_p160_c1', 'cheiroslanguageo00chei_1_p160_c2', 'cheiroslanguageo00chei_1_p163_c1', 'cheiroslanguageo00chei_1_p165_c0', 'cheiroslanguageo00chei_1_p165_c1', 'cheiroslanguageo00chei_1_p172_c1', 'cheiroslanguageo00chei_1_p87_c0', 'cheiroslanguageo00chei_1_p88_c1', 'cheiroslanguageo00chei_1_p89_c0', 'cheiroslanguageo00chei_1_p96_c0', 'cheiroslanguageo00chei_1_p96_c1', 'cheiroslanguageo00chei_1_p98_c1']

## Python decline block

Not appended (unsupported_features is empty).

## LLM call count

2 chat.completions.create() call(s) captured (hard cap 2).

## retry_used + first-draft Ring 1 failures / coverage misses

`retry_used`: **True**

First-draft Ring 1 failures (best-effort recomputation against this probe's own locally-computed unsupported_features/context_corpus/valid_chunk_ids -- see caveat above; this is what triggered the retry, combined with any coverage miss below):

| Validator | Result | Detail |
|---|---|---|
| jargon_blacklist | pass | -- |
| self_help_blacklist | FAIL | self_help_blacklist: found fulfillment, navigate, stability |
| unsupported_dates | pass | -- |
| length_guard | pass | -- |
| banned_feature_mention | pass | -- |
| exemplar_echo | pass | -- |
| anchor_completeness | FAIL | anchor_completeness: sentence-final residue with no tag: 'Note: The retrieved passages did not cover the specific features of the fingers, mounts other than Venus, or any markings beyond those mentioned.' |
| anchor_legality | pass | -- |

First-draft coverage misses (F-A, best-effort recomputation): ['coverage: fingers supported but never cited', 'coverage: markings/other features supported but never cited']

## Final Ring 1 result (authoritative, from PalmReadingResult.validation)

`passed`: **True**

| Validator | Result | Detail |
|---|---|---|
| jargon_blacklist | pass | -- |
| self_help_blacklist | pass | -- |
| unsupported_dates | pass | -- |
| length_guard | pass | -- |
| banned_feature_mention | pass | -- |
| exemplar_echo | pass | -- |
| anchor_completeness | pass | -- |
| anchor_legality | pass | -- |

**F-A coverage warnings** (`validation.warnings`, fail-open, never blocks display, per the S68 close-out lock a warning-bearing run cannot score P4 clean): ['coverage: markings/other features supported but never cited']

## reading_text (verbatim, final -- includes decline block + disclaimer, tags STRIPPED)

```
Your hands reveal a life of robust health and vitality, as indicated by the deep and unbroken life line on both hands. This line promises a long life, free from significant health issues or interruptions. The life line's consistent depth and length in both hands suggest a strong foundation of energy and resilience, which is a notable aspect of your character and life path.

The head line, deep and slightly curved, shows a mind guided by reason and intelligence. In your right hand, it begins joined with the life line, indicating that your life is currently guided by a balance of reason and personal sensitivity. This connection suggests a cautious approach to personal endeavors, with a strong reliance on intellect to face life's challenges. The slight curve of the head line also points to a creative and adaptable mind, capable of adjusting to new ideas and circumstances.

Your heart line, deep and curving slightly upwards, reflects a nature capable of deep affection and emotional engagement. In the right hand, it ends below the index finger, suggesting a focus on personal happiness and success in relationships. This line's upward curve indicates a positive outlook on emotional matters, with a tendency towards optimism in love and affection.

The fate line, more visible in your right hand, suggests a current trajectory marked by a developing sense of purpose and direction. Its presence indicates that you are in a phase of life where career and personal ambitions are becoming more defined. The line's path towards the middle finger, or Mount of Saturn, suggests a focus on responsibility in your endeavors.

The Mount of Venus, well-developed in both hands, signifies a strong capacity for love, affection, and a desire to connect with others. This mount's prominence indicates a robust physical constitution and a passionate nature, with a love for beauty and harmony in your surroundings.

Your thumb, medium in size and set at a wide angle, reflects a balanced character with a blend of willpower and adaptability. This positioning suggests a person who is neither overly rigid nor excessively flexible, capable of making decisions with both strength and consideration.

The fingers, being long and straight, suggest an intellectual nature, with a tendency towards independence of thought and action. This is further supported by the moderate spacing, which indicates a balanced approach to life.

Overall, your hands reveal a life path characterized by health, reason, emotional depth, and a developing sense of purpose. The features of your hands suggest a person who is well-equipped to face life's challenges with resilience and intelligence.

Note: The retrieved passages did not cover the specific features of the mounts other than Venus, or any markings beyond those mentioned.

For major life decisions, I recommend consulting a qualified astrologer or palm reader for a personal reading.
```

## reading_text_tagged (verbatim, A1 raw tagged draft -- anchors intact)

```
Your hands reveal a life of robust health and vitality, as indicated by the deep and unbroken life line on both hands. This line promises a long life, free from significant health issues or interruptions.[cheiroslanguageo00chei_1_p134_c1] The life line's consistent depth and length in both hands suggest a strong foundation of energy and resilience, which is a notable aspect of your character and life path.[OBS]

The head line, deep and slightly curved, shows a mind guided by reason and intelligence. In your right hand, it begins joined with the life line, indicating that your life is currently guided by a balance of reason and personal sensitivity. This connection suggests a cautious approach to personal endeavors, with a strong reliance on intellect to face life's challenges.[cheiroslanguageo00chei_1_p134_c2] The slight curve of the head line also points to a creative and adaptable mind, capable of adjusting to new ideas and circumstances.[OBS]

Your heart line, deep and curving slightly upwards, reflects a nature capable of deep affection and emotional engagement. In the right hand, it ends below the index finger, suggesting a focus on personal happiness and success in relationships. This line's upward curve indicates a positive outlook on emotional matters, with a tendency towards optimism in love and affection.[cheiroslanguageo00chei_1_p160_c1]

The fate line, more visible in your right hand, suggests a current trajectory marked by a developing sense of purpose and direction. Its presence indicates that you are in a phase of life where career and personal ambitions are becoming more defined. The line's path towards the middle finger, or Mount of Saturn, suggests a focus on responsibility in your endeavors.[cheiroslanguageo00chei_1_p163_c1]

The Mount of Venus, well-developed in both hands, signifies a strong capacity for love, affection, and a desire to connect with others. This mount's prominence indicates a robust physical constitution and a passionate nature, with a love for beauty and harmony in your surroundings.[cheiroslanguageo00chei_1_p112_c0]

Your thumb, medium in size and set at a wide angle, reflects a balanced character with a blend of willpower and adaptability. This positioning suggests a person who is neither overly rigid nor excessively flexible, capable of making decisions with both strength and consideration.[cheiroslanguageo00chei_1_p88_c1]

The fingers, being long and straight, suggest an intellectual nature, with a tendency towards independence of thought and action. This is further supported by the moderate spacing, which indicates a balanced approach to life.[cheiroslanguageo00chei_1_p96_c0]

Overall, your hands reveal a life path characterized by health, reason, emotional depth, and a developing sense of purpose. The features of your hands suggest a person who is well-equipped to face life's challenges with resilience and intelligence.[OBS]

Note: The retrieved passages did not cover the specific features of the mounts other than Venus, or any markings beyond those mentioned.[OBS]
```

## sources (from PalmReadingResult, post-gate)

- cheiroslanguageo00chei_1, p.135 (score: 0.6127) -- feature: life line
- cheiroslanguageo00chei_1, p.134 (score: 0.6054) -- feature: life line
- cheiroslanguageo00chei_1, p.134 (score: 0.5721) -- feature: life line
- cheiroslanguageo00chei_1, p.134 (score: 0.5581) -- feature: head line
- cheiroslanguageo00chei_1, p.147 (score: 0.5525) -- feature: head line
- cheiroslanguageo00chei_1, p.139 (score: 0.5422) -- feature: head line
- cheiroslanguageo00chei_1, p.160 (score: 0.5735) -- feature: heart line
- cheiroslanguageo00chei_1, p.160 (score: 0.5706) -- feature: heart line
- cheiroslanguageo00chei_1, p.159 (score: 0.5534) -- feature: heart line
- cheiroslanguageo00chei_1, p.165 (score: 0.5958) -- feature: fate line
- cheiroslanguageo00chei_1, p.163 (score: 0.5942) -- feature: fate line
- cheiroslanguageo00chei_1, p.165 (score: 0.5739) -- feature: fate line
- cheiroslanguageo00chei_1, p.88 (score: 0.5514) -- feature: thumb
- cheiroslanguageo00chei_1, p.87 (score: 0.5489) -- feature: thumb
- cheiroslanguageo00chei_1, p.89 (score: 0.5339) -- feature: thumb
- cheiroslanguageo00chei_1, p.98 (score: 0.5885) -- feature: fingers
- cheiroslanguageo00chei_1, p.96 (score: 0.5284) -- feature: fingers
- cheiroslanguageo00chei_1, p.96 (score: 0.5282) -- feature: fingers
- cheiroslanguageo00chei_1, p.112 (score: 0.6824) -- feature: mount of venus
- cheiroslanguageo00chei_1, p.111 (score: 0.6698) -- feature: mount of venus
- cheiroslanguageo00chei_1, p.111 (score: 0.5591) -- feature: mount of venus
- cheiroslanguageo00chei_1, p.112 (score: 0.663) -- feature: mount of jupiter
- cheiroslanguageo00chei_1, p.113 (score: 0.5894) -- feature: mount of jupiter
- cheiroslanguageo00chei_1, p.107 (score: 0.4382) -- feature: markings/other features
- cheiroslanguageo00chei_1, p.172 (score: 0.4304) -- feature: markings/other features

## Sanity asserts

- [x] At least 1 feature supported -- got 9: ['life line', 'head line', 'heart line', 'fate line', 'thumb', 'fingers', 'mount of venus', 'mount of jupiter', 'markings/other features']
- [x] Ring 1 `passed=True` on the final draft
- [x] No 6-gram exemplar echo in `reading_text`
- [x] `reading_text_tagged` is populated and contains a recognized anchor tag

## Verdict

All 4 sanity asserts PASSED. This is a wiring smoke check only -- it says nothing about interpretive quality/citation accuracy (that is Ring 3 pass 4's job, on fresh uploads, human-scored). No product code was touched or fixed by this script.