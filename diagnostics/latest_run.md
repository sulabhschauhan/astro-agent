# Pre-flight smoke probe for Ring 3 pass 3 (S67 close-out)

**THROWAWAY SCRIPT. NOT A SCORING PASS.** Ring 3 pass 3 itself still requires fresh uploads through the real app with live human checkpoints (CLAUDE.md T4 golden semantics / Palm human checkpoint locks). This probe uses `data/test_images/` fixtures (sanctioned for mechanical probes only) to catch a pipeline defect in the S67 R1->R3->R2 landed work before spending a fresh-upload pass-3 run on it. Vision descriptions below are captured verbatim but are NOT human-confirmed -- this headless script bypasses the S65/S66 F1 checkpoint UI by construction; that gate is unaffected and still applies to any real user-facing flow.

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

LIFE LINE: Present, deep, long, curves around the base of the thumb, no clear breaks or forks.

HEAD LINE: Present, deep, long, slightly curved, runs across the palm, no clear breaks or forks.

HEART LINE: Present, deep, slightly curved, ends below the index finger, no clear breaks or forks.

FATE LINE: Barely visible.

OTHER LINES: No other lines clearly visible.

MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.

MARKS: No marks clearly visible.
```

**RIGHT** (verbatim):
```
HAND SHAPE: Square palm, overall build is robust.

FINGERS: Fingers are slightly longer than the palm, appear straight, fingertips are rounded, spacing is moderate.

THUMB: Medium relative size, set moderately low, wide angle from the palm.

LIFE LINE: Present, deep, long, curves around the base of the thumb, no clear breaks or forks.

HEAD LINE: Present, deep, long, slightly curved, runs across the palm, no clear breaks or forks.

HEART LINE: Present, deep, long, curves slightly upwards, no clear breaks or forks.

FATE LINE: Present, moderately deep, runs vertically towards the middle finger, no clear breaks or forks.

OTHER LINES: Sun line is faintly visible, no clear health or marriage lines.

MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.

MARKS: No clear marks such as crosses, stars, grilles, squares, or moles.
```

**HAND_DETAIL** (verbatim):
```
The image shows a hand with the following observable features:

- **Hand Shape**: The hand appears broad with a relatively square palm.
- **Finger Lengths**: The fingers are of moderate length. The index finger is slightly shorter than the middle finger, and the ring finger is slightly longer than the index finger. The little finger is noticeably shorter.
- **Thumb**: The thumb is of average length with a moderate angle of flexibility, indicating it is not tightly held against the palm.
- **Visible Lines**:
  - **Life Line**: A prominent line curves around the base of the thumb.
  - **Head Line**: Appears to be separate from the life line, running across the palm.
  - **Heart Line**: Starts under the little finger and curves towards the index finger.
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
| heart line | (p.160, 0.5831, cheiroslanguageo00chei_1_p160_c1); (p.160, 0.5562, cheiroslanguageo00chei_1_p160_c2); (p.180, 0.5372, cheiroslanguageo00chei_1_p180_c1) |
| fate line | (p.165, 0.5958, cheiroslanguageo00chei_1_p165_c1); (p.163, 0.5942, cheiroslanguageo00chei_1_p163_c1); (p.165, 0.5739, cheiroslanguageo00chei_1_p165_c0) |
| sun line | (p.166, 0.5206, cheiroslanguageo00chei_1_p166_c1); (p.166, 0.5176, cheiroslanguageo00chei_1_p166_c0); (p.169, 0.5064, cheiroslanguageo00chei_1_p169_c0) |
| thumb | (p.88, 0.5261, cheiroslanguageo00chei_1_p88_c1); (p.87, 0.5235, cheiroslanguageo00chei_1_p87_c0); (p.89, 0.5100, cheiroslanguageo00chei_1_p89_c0) |
| fingers | (p.98, 0.5886, cheiroslanguageo00chei_1_p98_c1); (p.96, 0.5284, cheiroslanguageo00chei_1_p96_c1); (p.96, 0.5282, cheiroslanguageo00chei_1_p96_c0) |
| mount of venus | (p.112, 0.6824, cheiroslanguageo00chei_1_p112_c0); (p.111, 0.6698, cheiroslanguageo00chei_1_p111_c1); (p.111, 0.5591, cheiroslanguageo00chei_1_p111_c0) |
| mount of jupiter | (p.112, 0.6630, cheiroslanguageo00chei_1_p112_c0); (p.111, 0.6456, cheiroslanguageo00chei_1_p111_c1); (p.113, 0.5893, cheiroslanguageo00chei_1_p113_c0) |
| markings/other features | (p.172, 0.4387, cheiroslanguageo00chei_1_p172_c1); (p.221, 0.4258, cheiroslanguageo00chei_1_p221_c1); (p.202, 0.4112, cheiroslanguageo00chei_1_p202_c1) |

## Support gate verdicts

- **supported_features** (registry order): ['life line', 'head line', 'heart line', 'fate line', 'sun line', 'thumb', 'fingers', 'mount of venus', 'mount of jupiter', 'markings/other features']
- **unsupported_features** (registry order): []
- **genuine negative-absence** (in neither tuple -- nothing to support, nothing to decline): []

## Python decline block

Not appended (unsupported_features is empty).

## LLM call count

2 chat.completions.create() call(s) captured (hard cap 2).

## retry_used + first-draft Ring 1 failures

`retry_used`: **True**

First-draft failures (best-effort recomputation against this probe's own locally-computed unsupported_features/context_corpus -- see caveat above; this is what triggered the retry):

| Validator | Result | Detail |
|---|---|---|
| jargon_blacklist | pass | -- |
| self_help_blacklist | FAIL | self_help_blacklist: found fulfillment, stability |
| unsupported_dates | pass | -- |
| length_guard | pass | -- |
| banned_feature_mention | pass | -- |
| exemplar_echo | pass | -- |

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

## reading_text (verbatim, final -- includes decline block + disclaimer)

```
Your hands reveal a life of robust health and vitality, with a strong potential for success in your endeavors. The deep and unbroken life line on both hands indicates a life marked by good health and vitality. This line's continuity suggests that you are likely to enjoy a long and healthy life, free from major health disruptions.

The head line, also deep and unbroken, signifies a clear and focused mind. Its slight curve suggests a balance between logic and creativity, allowing you to approach problems with both reason and imagination. This line's separation from the life line indicates a degree of independence in thought and action, suggesting that you are not easily swayed by others and prefer to chart your own course.

The heart line, ending below the index finger on the left hand and curving slightly upwards on the right, suggests a nature that is both affectionate and discerning. You are likely to experience happiness in your relationships, as this line's depth and clarity indicate sincerity and depth of feeling. The upward curve on the right hand suggests a current trajectory towards emotional satisfaction in personal relationships.

The fate line, more visible on the right hand, suggests that your current life path is one of increasing direction. Its presence indicates that you are likely to experience a period of success and recognition in your career or personal endeavors. The absence of breaks or forks in this line suggests a steady progression without major disruptions.

The developed Mount of Venus on both hands indicates a strong capacity for love and affection, as well as a robust physical constitution. This mount's prominence suggests a life enriched by beauty, art, and harmonious relationships.

Overall, your hands reveal a life of potential and current trajectory marked by health, success, and emotional satisfaction. Your innate qualities and current path suggest a harmonious balance between personal desires and external achievements.

For major life decisions, I recommend consulting a qualified astrologer or palm reader for a personal reading.
```

## sources (from PalmReadingResult, post-gate)

- cheiroslanguageo00chei_1, p.135 (score: 0.6127) -- feature: life line
- cheiroslanguageo00chei_1, p.134 (score: 0.6054) -- feature: life line
- cheiroslanguageo00chei_1, p.134 (score: 0.5721) -- feature: life line
- cheiroslanguageo00chei_1, p.134 (score: 0.5581) -- feature: head line
- cheiroslanguageo00chei_1, p.147 (score: 0.5525) -- feature: head line
- cheiroslanguageo00chei_1, p.139 (score: 0.5422) -- feature: head line
- cheiroslanguageo00chei_1, p.160 (score: 0.583) -- feature: heart line
- cheiroslanguageo00chei_1, p.160 (score: 0.5561) -- feature: heart line
- cheiroslanguageo00chei_1, p.180 (score: 0.5372) -- feature: heart line
- cheiroslanguageo00chei_1, p.165 (score: 0.5958) -- feature: fate line
- cheiroslanguageo00chei_1, p.163 (score: 0.5942) -- feature: fate line
- cheiroslanguageo00chei_1, p.165 (score: 0.5739) -- feature: fate line
- cheiroslanguageo00chei_1, p.166 (score: 0.5206) -- feature: sun line
- cheiroslanguageo00chei_1, p.166 (score: 0.5176) -- feature: sun line
- cheiroslanguageo00chei_1, p.169 (score: 0.5064) -- feature: sun line
- cheiroslanguageo00chei_1, p.88 (score: 0.5261) -- feature: thumb
- cheiroslanguageo00chei_1, p.87 (score: 0.5235) -- feature: thumb
- cheiroslanguageo00chei_1, p.89 (score: 0.51) -- feature: thumb
- cheiroslanguageo00chei_1, p.98 (score: 0.5886) -- feature: fingers
- cheiroslanguageo00chei_1, p.96 (score: 0.5284) -- feature: fingers
- cheiroslanguageo00chei_1, p.96 (score: 0.5282) -- feature: fingers
- cheiroslanguageo00chei_1, p.112 (score: 0.6824) -- feature: mount of venus
- cheiroslanguageo00chei_1, p.111 (score: 0.6698) -- feature: mount of venus
- cheiroslanguageo00chei_1, p.111 (score: 0.5591) -- feature: mount of venus
- cheiroslanguageo00chei_1, p.112 (score: 0.663) -- feature: mount of jupiter
- cheiroslanguageo00chei_1, p.113 (score: 0.5894) -- feature: mount of jupiter
- cheiroslanguageo00chei_1, p.172 (score: 0.4387) -- feature: markings/other features

## Sanity asserts

- [x] At least 1 feature supported -- got 10: ['life line', 'head line', 'heart line', 'fate line', 'sun line', 'thumb', 'fingers', 'mount of venus', 'mount of jupiter', 'markings/other features']
- [x] Ring 1 `passed=True` on the final draft
- [x] No 6-gram exemplar echo in `reading_text`

## Verdict

All 3 sanity asserts PASSED. This is a wiring smoke check only -- it says nothing about interpretive quality/citation accuracy (that is Ring 3 pass 3's job, on fresh uploads, human-scored). No product code was touched or fixed by this script.