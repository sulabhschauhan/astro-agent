# S66 Task 12 — Pass-2 pre-flight smoke probe

Live vision + generation, measure-first, NO source edits, NO content
asserts. Scratch script run then deleted; results captured here only.

## Step 0 — Fixture selection

```
data/test_images/
  Back Hand.jpeg
  Body.jpeg
  Face.jpeg
  palm_left_test.jpg
  palm_right_test.jpg
```
Used: `palm_left_test.jpg`, `palm_right_test.jpg`, `Back Hand.jpeg` (as
`hand_detail` input via `describe_hand_detail_image`). `Body.jpeg` /
`Face.jpeg` ignored — no consuming surface exists for them.

## Step 1 — Vision descriptions (3 live calls) — verbatim

### LEFT (`describe_palm_image(left_bytes, "left")`)
```
HAND SHAPE: Square palm, overall build is robust.

FINGERS: Fingers are long relative to the palm, appear straight, with rounded fingertips, moderate spacing.

THUMB: Medium size, set moderately low, wide angle from the palm.

LIFE LINE: Present, deep, long, curves around the base of the thumb, no clear breaks or forks.

HEAD LINE: Present, deep, long, slightly curved, runs across the palm, no clear breaks or forks.

HEART LINE: Present, deep, slightly curved, ends below the index finger, no clear breaks or forks.

FATE LINE: Barely visible.

OTHER LINES: No other lines clearly visible.

MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.

MARKS: No marks clearly visible.
```
`left_len = 701`

### RIGHT (`describe_palm_image(right_bytes, "right")`)
```
HAND SHAPE: Square palm, medium build

FINGERS: Medium length relative to palm, straight, rounded fingertips, moderate spacing

THUMB: Medium size, low set, wide angle from the palm

LIFE LINE: Present, deep, long, curves around the base of the thumb, no clear breaks or forks

HEAD LINE: Present, deep, long, slightly curved, no clear breaks or forks

HEART LINE: Present, deep, long, curves slightly upward, no clear breaks or forks

FATE LINE: Barely visible

OTHER LINES: Not clearly visible

MOUNTS: Mount of Venus appears developed, others unremarkable

MARKS: Not clearly visible
```
`right_len = 586`

### HAND_DETAIL (`describe_hand_detail_image`, `Back Hand.jpeg`)
```
The image shows a hand with the following observable features:

- **Hand Shape**: The hand appears broad with a relatively square palm.
- **Finger Lengths**: The fingers are of moderate length. The index finger is slightly shorter than the middle finger, and the ring finger is slightly longer than the index finger. The little finger is noticeably shorter.
- **Thumb**: The thumb is of average length with a moderate angle of flexibility, indicating it is not tightly held against the palm.
- **Visible Lines**:
  - **Life Line**: A prominent line curves around the base of the thumb.
  - **Head Line**: This line runs horizontally across the palm, starting near the life line.
  - **Heart Line**: The heart line is visible, curving across the top of the palm.
  - **Fate Line**: There is no clearly visible fate line in the image.
- **Mounts**: The mounts of Venus (base of the thumb) and Jupiter (below the index finger) appear slightly raised.
- **Markings**: There are no unusual markings or features visible on the palm.
- **Other Features**: The hand has visible hair on the back, particularly on the fingers.

These are the physical observations based on the image provided.
```
`hand_detail_len = 1182`

### Length arithmetic
| | chars |
|---|---|
| LEFT | 701 |
| RIGHT | 586 |
| Combined (left+right) | 1287 |
| `_QUERY_TRUNCATE_CHARS` | 2000 |
| Margin | 713 (fits) |

### F4 drift check (observe, don't fix)
- LEFT/RIGHT (post-F4 structured prompt): clean — no
  "indicating"/"suggesting" or interpretive language in either
  transcript, consistent with the Task 9 probe.
- HAND_DETAIL (`describe_hand_detail_image`, a DIFFERENT prompt not
  touched by F4 — still the older "Cheiro-tradition palmist... Describe
  only what you can physically observe" free-text framing): one
  borderline instance — "The thumb is... a moderate angle of
  flexibility, **indicating** it is not tightly held against the
  palm." Uses the literal word "indicating," but the claim itself
  stays physical/observational (thumb angle -> not tightly held is a
  geometric inference, not a trait/prediction claim) — flagged as a
  near-miss on the "never write 'indicating'" instruction, not a
  content violation. This prompt is out of Task 9/12's scope (F4 only
  touched `describe_palm_image`); noting for whoever scopes a future
  F-item against `describe_hand_detail_image`.

## Step 2 — Generation runs (3 live calls) — verbatim

### RUN A: `generate_palm_reading(left, right)`
```
Your hands reveal a strong foundation of health and vitality, both in your innate potential and your current life path. The deep, long Life Line on both hands, curving smoothly around the base of the thumb without breaks, indicates robust health and a long life. This is reinforced by the developed Mount of Venus, which suggests a passion for life, affection, and a strong constitution.

The Head Line, deep and slightly curved in both hands, shows a clear and balanced mind. This line's continuity and depth suggest a strong mental capacity and a practical approach to life's challenges. The slight curve indicates a degree of creativity and flexibility in thinking, allowing you to adapt and thrive in various situations.

Your Heart Line, deep and slightly curved, ending below the index finger, points to a sincere and straightforward approach to relationships. It suggests you value honesty and directness in emotional matters. The upward curve in your right hand indicates that your current emotional life is fulfilling and that you are open to love and affection.

The barely visible Fate Line in both hands suggests that your life path is more influenced by your own decisions and actions rather than external forces or destiny. This indicates a life where personal choices and efforts play a significant role in shaping your future.

The square shape of your palm, combined with the robust build, points to a practical, grounded nature. You are likely someone who values stability and reliability, with a strong sense of responsibility.

The medium-length fingers with rounded tips suggest a balance between practicality and sensitivity. You can approach tasks with both efficiency and empathy, making you well-suited to roles that require both skill and understanding.

Overall, your hands depict a life of health, mental acuity, and emotional sincerity, with a strong emphasis on personal agency and choice in crafting your life's journey.

For major life decisions, I recommend consulting a qualified astrologer or palm reader for a personal reading.
```
- `validation.passed = False`
- `validation.failures = ('self_help_blacklist: found fulfilling, journey, stability',)`
- sources:
  - cheiroslanguageo00chei_1, p.120 (score: 0.5983)
  - cheiroslanguageo00chei_1, p.123 (score: 0.5965)
  - cheiroslanguageo00chei_1, p.135 (score: 0.5947)
  - cheiroslanguageo00chei_1, p.120 (score: 0.5888)
  - cheiroslanguageo00chei_1, p.112 (score: 0.5846)
  - cheiroslanguageo00chei_1, p.134 (score: 0.5771)
- word_count = 328 (cap=700, fits)

### RUN B: identical repeat (variance probe)
```
Your hands reveal a strong and consistent character, with a robust potential and a steady current life trajectory. The square shape of your palms, combined with the long, straight fingers, suggests a practical and methodical nature. You are likely someone who values structure and order, and this is reflected in both your innate potential and your current path.

The deep, long life line on both hands, curving around the base of the thumb without breaks or forks, indicates a life of good health and vitality. This is further supported by the developed Mount of Venus, which suggests strong health and a passionate nature. Your capacity for affection and sympathy towards others is notable, and you likely have a strong appreciation for beauty and harmony.

Your head line, which is deep and slightly curved, shows a clear and focused mind. This line's consistency across both hands indicates that your intellectual potential is being realized in your current life. You have a strong sense of logic and reasoning, which helps you navigate challenges with clarity and determination.

The heart line, ending below the index finger on the left hand and curving slightly upward on the right, suggests a balance between idealism and practicality in matters of the heart. While you have a capacity for deep emotions, you approach relationships with a sense of realism and understanding.

The barely visible fate line suggests that destiny plays a lesser role in your life compared to your own actions and decisions. You are likely someone who believes in shaping your own path rather than relying on fate.

Overall, your hands indicate a life driven by personal effort and a strong, consistent character. You possess the potential for a rich and fulfilling life, marked by health, passion, and a keen intellect.

For major life decisions, I recommend consulting a qualified astrologer or palm reader for a personal reading.
```
- `validation.passed = False`
- `validation.failures = ('self_help_blacklist: found fulfilling, navigate',)`
- sources:
  - cheiroslanguageo00chei_1, p.120 (score: 0.598)
  - cheiroslanguageo00chei_1, p.123 (score: 0.596)
  - cheiroslanguageo00chei_1, p.135 (score: 0.5945)
  - cheiroslanguageo00chei_1, p.120 (score: 0.5887)
  - cheiroslanguageo00chei_1, p.112 (score: 0.5854)
  - cheiroslanguageo00chei_1, p.134 (score: 0.5768)
- word_count = 312 (cap=700, fits)

### RUN C: `generate_palm_reading(left, right, hand_detail=detail)`
```
Your hands reveal a robust and grounded nature, both in potential and in your current life path. The square palm and long fingers suggest a practical and methodical approach to life, with a strong foundation in logic and reason. The deep, long lines of life, head, and heart in both hands indicate a life path characterized by vitality, mental clarity, and emotional depth.

The life line, which is deep and curves around the base of the thumb without breaks, promises good health and a strong life force. This is consistent across both hands, suggesting that your innate potential for vitality is being realized in your current life. The deep head line, slightly curved and unbroken, indicates a clear and focused mind, capable of both analytical thought and creativity. This mental strength is a constant in your life, guiding you through challenges with clarity and insight.

The heart line, ending below the index finger and slightly curved, speaks to a capacity for deep emotional connections and a strong sense of empathy. This emotional depth is a core aspect of your character and continues to influence your relationships positively.

The Mount of Venus, being well-developed, suggests a passionate nature with a strong appreciation for beauty and affection. This mount indicates a life rich in personal connections and a desire to engage deeply with those around you. Your thumb's moderate size and flexibility reflect a balanced willpower and adaptability, allowing you to pursue your goals with determination while remaining open to change.

The barely visible fate line suggests that your life path is not heavily influenced by destiny or external forces; rather, it is shaped by your own choices and actions. This lack of a strong fate line emphasizes the importance of personal agency in your life journey.

Overall, your hands reveal a life that is grounded in personal strength, mental clarity, and emotional richness. Your path is one of self-determined progress, supported by a robust constitution and a deep connection to those around you.

For major life decisions, I recommend consulting a qualified astrologer or palm reader for a personal reading.
```
- `validation.passed = False`
- `validation.failures = ('self_help_blacklist: found journey',)`
- sources:
  - cheiroslanguageo00chei_1, p.120 (score: 0.5983)
  - cheiroslanguageo00chei_1, p.123 (score: 0.5965)
  - cheiroslanguageo00chei_1, p.135 (score: 0.5947)
  - cheiroslanguageo00chei_1, p.120 (score: 0.5888)
  - cheiroslanguageo00chei_1, p.112 (score: 0.5846)
  - cheiroslanguageo00chei_1, p.134 (score: 0.5771)
- word_count = 349 (cap=700, fits)

Note: Run C's sources are byte-identical to Run A's (same scores) —
consistent with the pass-1 finding that `hand_detail` is excluded from
the RAG query by design (`palm_reading.py`'s query is built from
`palm_left`/`palm_right` only); no new evidence needed here, this is
expected mechanical behavior, not a bug.

## Step 3 — Result

Zero exceptions across all 6 live calls. **All 3 generation runs failed
Ring 1 validation** on `self_help_blacklist`:
- Run A: `fulfilling, journey, stability`
- Run B: `fulfilling, navigate`
- Run C: `journey`

This means that under the current app.py display path
(`if not _reading.validation.passed: st.error(...)`), a live user
running any of these 3 shapes today would see a validation-failure
error, not a reading — Ring 1's self-help blacklist (S66 F2+F3) is
firing reliably on gpt-4o's generation output at the current
temperature/prompt, independent of the F4 vision-description change.
This is measure-first data for whoever scores pass-2's P3 (voice) rows
next — it's stronger signal than pass-1 had (pass-1's Ring 1 spot-check
showed no jargon-blacklist trips; this probe shows self-help-blacklist
trips on 3/3 runs), and is a fact to reconcile before pass-2 scoring,
not an action taken here (no source edits, no asserts, per this task's
charter).

No source files edited. Scratch script + stray output file deleted
after capture.

## Commit
Diagnostics-only commit, pushed to `main`.
