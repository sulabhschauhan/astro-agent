# Pre-flight smoke probe for Ring 3 pass 5 (S69 F-H two-stage pipeline)

**THROWAWAY SCRIPT. NOT A SCORING PASS.** Ring 3 pass 5 itself still requires fresh uploads through the real app with live human checkpoints (CLAUDE.md T4 golden semantics / Palm human checkpoint locks, extended by S70 P6b's own claims-ack checkpoint). This probe uses `data/test_images/` fixtures (sanctioned for mechanical probes only) to catch a wiring defect in the landed S69 F-H two-stage pipeline before spending a fresh-upload pass-5 run on it. Vision descriptions and the claims inventory below are captured verbatim but are NOT human-confirmed/acked -- this headless script bypasses BOTH the S65/S66 F1 palm-description checkpoint UI and S70 P6b's claims-ack checkpoint by construction (it calls generate_palm_reading() directly, the prepare/complete seam un-checkpointed); both gates are unaffected and still apply to any real user-facing flow.

Run shape: Run-C (hardest case) -- both palm images + hand_detail, live OpenAI vision + live two-stage generation.

## Fixtures

- LEFT: `C:\Users\sulab\Documents\Python Scripts\astro-agent\data\test_images\palm_left_test.jpg`
- RIGHT: `C:\Users\sulab\Documents\Python Scripts\astro-agent\data\test_images\palm_right_test.jpg`
- HAND_DETAIL: `C:\Users\sulab\Documents\Python Scripts\astro-agent\data\test_images\Back Hand.jpeg`

## Confirmed descriptions (NOT human-confirmed -- headless probe)

**LEFT** (verbatim):
```
HAND SHAPE: Square palm, overall build is robust.

FINGERS: Fingers are long relative to the palm, appear straight, with rounded fingertips, and moderate spacing.

THUMB: Medium size, set moderately low, wide angle from the palm.

LIFE LINE: Present, deep, long, curves around the base of the thumb, no breaks visible.

HEAD LINE: Present, deep, long, slightly curved, runs across the palm, no breaks visible.

HEART LINE: Present, deep, slightly curved, ends below the index finger, no breaks visible.

FATE LINE: Barely visible.

OTHER LINES: No other lines clearly visible.

MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.

MARKS: No marks clearly visible.
```

**RIGHT** (verbatim):
```
HAND SHAPE: Square palm, medium build

FINGERS: Medium length relative to palm, straight, rounded fingertips, moderate spacing

THUMB: Medium size, set moderately low, wide angle from the palm

LIFE LINE: Present, deep, long, curves around the base of the thumb, no clear breaks or forks

HEAD LINE: Present, deep, long, slightly curved, starts joined with the life line

HEART LINE: Present, deep, long, curves slightly upward, ends below the index finger

FATE LINE: Barely visible

OTHER LINES: Not clearly visible

MOUNTS: Mount of Venus appears developed, other mounts unremarkable

MARKS: Not clearly visible
```

**HAND_DETAIL** (verbatim):
```
The image shows a hand with the following observable features:

- **Hand Shape**: The hand appears broad with a relatively square palm.
- **Finger Lengths**: The fingers are of moderate length. The index finger is slightly shorter than the middle finger, and the ring finger is slightly longer than the index finger. The little finger is noticeably shorter.
- **Thumb**: The thumb is of average length and appears to have a moderate angle of flexibility from the palm.
- **Visible Lines**:
  - **Life Line**: A prominent line curves around the base of the thumb.
  - **Head Line**: This line runs horizontally across the palm, starting near the life line.
  - **Heart Line**: The heart line is visible, starting under the little finger and curving towards the index finger.
  - **Fate Line**: There is no clearly visible fate line in the image.
- **Mounts**: The mounts of Venus (base of the thumb) and Jupiter (below the index finger) appear slightly raised.
- **Markings**: There are no unusual markings or features visible.
- **Other Features**: The hand has visible hair on the back, particularly on the fingers.

This description is based solely on the physical characteristics visible in the image.
```

## Per-feature retrieval map (raw, pre-gate, all 10 registry features)

| Feature | Chunks (page_ref, score, chunk_id) |
|---|---|
| life line | (p.135, 0.6127, cheiroslanguageo00chei_1_p135_c0); (p.134, 0.6054, cheiroslanguageo00chei_1_p134_c1); (p.134, 0.5721, cheiroslanguageo00chei_1_p134_c0) |
| head line | (p.123, 0.6090, cheiroslanguageo00chei_1_p123_c0); (p.151, 0.5898, cheiroslanguageo00chei_1_p151_c2); (p.135, 0.5866, cheiroslanguageo00chei_1_p135_c2) |
| heart line | (p.159, 0.6088, cheiroslanguageo00chei_1_p159_c3); (p.160, 0.6068, cheiroslanguageo00chei_1_p160_c2); (p.161, 0.5971, cheiroslanguageo00chei_1_p161_c0) |
| fate line | (p.165, 0.4943, cheiroslanguageo00chei_1_p165_c1); (p.165, 0.4942, cheiroslanguageo00chei_1_p165_c0); (p.127, 0.4762, cheiroslanguageo00chei_1_p127_c1) |
| sun line | _(none -- skipped or retrieval failed)_ |
| thumb | (p.88, 0.5588, cheiroslanguageo00chei_1_p88_c1); (p.87, 0.5581, cheiroslanguageo00chei_1_p87_c0); (p.89, 0.5331, cheiroslanguageo00chei_1_p89_c0) |
| fingers | (p.98, 0.5694, cheiroslanguageo00chei_1_p98_c1); (p.96, 0.5251, cheiroslanguageo00chei_1_p96_c0); (p.95, 0.5194, cheiroslanguageo00chei_1_p95_c0) |
| mount of venus | (p.112, 0.6824, cheiroslanguageo00chei_1_p112_c0); (p.111, 0.6698, cheiroslanguageo00chei_1_p111_c1); (p.111, 0.5591, cheiroslanguageo00chei_1_p111_c0) |
| mount of jupiter | (p.112, 0.6630, cheiroslanguageo00chei_1_p112_c0); (p.111, 0.6457, cheiroslanguageo00chei_1_p111_c1); (p.113, 0.5894, cheiroslanguageo00chei_1_p113_c0) |
| markings/other features | (p.107, 0.4734, cheiroslanguageo00chei_1_p107_c0); (p.172, 0.4597, cheiroslanguageo00chei_1_p172_c1); (p.225, 0.4313, cheiroslanguageo00chei_1_p225_c1) |

## Support gate verdicts

- **supported_features** (registry order): ['life line', 'head line', 'heart line', 'fate line', 'thumb', 'fingers', 'mount of venus', 'mount of jupiter', 'markings/other features']
- **unsupported_features** (registry order): ['sun line']
- **genuine negative-absence** (in neither tuple -- nothing to support, nothing to decline): []
- **valid_chunk_ids** (union, count=23): ['cheiroslanguageo00chei_1_p107_c0', 'cheiroslanguageo00chei_1_p111_c0', 'cheiroslanguageo00chei_1_p111_c1', 'cheiroslanguageo00chei_1_p112_c0', 'cheiroslanguageo00chei_1_p113_c0', 'cheiroslanguageo00chei_1_p123_c0', 'cheiroslanguageo00chei_1_p134_c0', 'cheiroslanguageo00chei_1_p134_c1', 'cheiroslanguageo00chei_1_p135_c0', 'cheiroslanguageo00chei_1_p151_c2', 'cheiroslanguageo00chei_1_p159_c3', 'cheiroslanguageo00chei_1_p160_c2', 'cheiroslanguageo00chei_1_p161_c0', 'cheiroslanguageo00chei_1_p165_c0', 'cheiroslanguageo00chei_1_p165_c1', 'cheiroslanguageo00chei_1_p172_c1', 'cheiroslanguageo00chei_1_p225_c1', 'cheiroslanguageo00chei_1_p87_c0', 'cheiroslanguageo00chei_1_p88_c1', 'cheiroslanguageo00chei_1_p89_c0', 'cheiroslanguageo00chei_1_p95_c0', 'cheiroslanguageo00chei_1_p96_c0', 'cheiroslanguageo00chei_1_p98_c1']

## Python decline block (pre-Stage-1 estimate, from the gate alone)

Appended for: ['sun line']

```
A note on what I have not interpreted: the classical texts I work from do not clearly address the following as they appear in your hands: sun line. Rather than guess, I have left these out of your reading.
```

(Note: the FINAL decline block generate_palm_reading() builds can differ from this -- `_compute_decline_features` also folds in Stage-1 extraction failures and gate-supported-but-zero-claims features; see the final Ring 1 result section below for the authoritative reading.)

## LLM call count

12 chat.completions.create() call(s) captured total across BOTH stages (Stage 1: up to 2 calls PER attempted feature, own F2c retry; Stage 2: up to 2 calls, own whole-reading F2c retry -- no single global cap, unlike the old single-call architecture's flat 2-call ceiling).

## Stage1/Stage2 retry fields (data, NOT asserted -- single run, no rate claim)

- `stage1_retry_features`: ['thumb']
- `stage2_retry_used`: True
- `retry_used` (COMPAT, true if either stage retried): True

## Final Ring 1 result (authoritative, from PalmReadingResult.validation)

`passed`: **False**

| Validator | Result | Detail |
|---|---|---|
| jargon_blacklist | pass | -- |
| self_help_blacklist | pass | -- |
| unsupported_dates | pass | -- |
| length_guard | pass | -- |
| banned_feature_mention | pass | -- |
| exemplar_echo | FAIL | exemplar_echo: i have examined many hands in |
| tag_legality | pass | -- |
| claim_coverage | pass | -- |
| doctrine_guard | pass | -- |

`validation.warnings` (F-A retired, superseded by Stage 2's own V-4 claim-coverage check -- always `()` now): none

## Full claims inventory (P6a pipe format, PalmReadingResult.claims verbatim)

claim_id | feature | chunk_id | valence | excluded_from_voice | exclusion_reason | condition_text | claim_text
C1 | life line | cheiroslanguageo00chei_1_p134_c1 | supports | False | None | None | A long, deep, and uninterrupted line of life indicates long life, good health, and vitality.
C2 | fingers | cheiroslanguageo00chei_1_p95_c0 | supports | False | None | None | Long fingers indicate a love of detail in everything and a tendency to worry over little things.
C3 | fingers | cheiroslanguageo00chei_1_p96_c0 | supports | False | None | None | The first finger can be very short or as long as the second, indicating variability in finger length.
C4 | fingers | cheiroslanguageo00chei_1_p98_c1 | corrective | False | None | None | The statement that in every case the fingers must be longer than the palm is erroneous and misleading.
C5 | mount of venus | cheiroslanguageo00chei_1_p112_c0 | supports | False | None | None | A well-developed Mount of Venus indicates strong and robust health.
C6 | mount of venus | cheiroslanguageo00chei_1_p112_c0 | supports | False | None | None | The Mount of Venus denotes affection, sympathy toward others, benevolence, a desire to please, love and worship of beauty, love of color, and melody in music, and the attraction of the one sex to the other.
C7 | mount of jupiter | cheiroslanguageo00chei_1_p112_c0 | supports | False | None | None | When developed, it indicates ambition, pride, enthusiasm in anything attempted, and desire for power.

## reading_text (verbatim, final -- includes decline block + disclaimer, tags STRIPPED)

```
I have examined many hands in my years of practice, and each one tells its own story to those who know how to read it. The life line on your palm is long, deep, and uninterrupted, curving gracefully around the base of the thumb. This indicates a long life, good health, and vitality.

Your fingers are long relative to the palm, which suggests a love of detail in all things and a tendency to worry over minor matters. It is important to note that the belief that fingers must always be longer than the palm is a misconception. The index finger is slightly shorter than the middle finger, which is a common variation in finger length.

The Mount of Venus on your hand is well-developed, signifying strong and robust health. This mount also denotes affection, sympathy toward others, benevolence, a desire to please, and a love of beauty, color, and melody in music. It also indicates an attraction between the sexes. Additionally, the slightly raised mounts of Venus and Jupiter suggest ambition, pride, enthusiasm in your endeavors, and a desire for power.

The lines and features of your hand reveal a person of vitality, attention to detail, and a strong capacity for affection and ambition. The hand rarely lies to the palmist who reads it honestly.

A note on what I have not interpreted: the classical texts I work from do not clearly address the following as they appear in your hands: head line, heart line, fate line, sun line, thumb, markings and other features. Rather than guess, I have left these out of your reading.

For major life decisions, I recommend consulting a qualified astrologer or palm reader for a personal reading.
```

## reading_text_tagged (verbatim, Stage 2 raw voiced draft -- [C<n>]/[OBS]/[FLOW] tags intact)

```
I have examined many hands in my years of practice, and each one tells its own story to those who know how to read it. [FLOW] The life line on your palm is long, deep, and uninterrupted, curving gracefully around the base of the thumb. This indicates a long life, good health, and vitality. [C1] 

Your fingers are long relative to the palm, which suggests a love of detail in all things and a tendency to worry over minor matters. [C2] It is important to note that the belief that fingers must always be longer than the palm is a misconception. [C4] The index finger is slightly shorter than the middle finger, which is a common variation in finger length. [C3]

The Mount of Venus on your hand is well-developed, signifying strong and robust health. [C5] This mount also denotes affection, sympathy toward others, benevolence, a desire to please, and a love of beauty, color, and melody in music. It also indicates an attraction between the sexes. [C6] Additionally, the slightly raised mounts of Venus and Jupiter suggest ambition, pride, enthusiasm in your endeavors, and a desire for power. [C7]

The lines and features of your hand reveal a person of vitality, attention to detail, and a strong capacity for affection and ambition. [FLOW] The hand rarely lies to the palmist who reads it honestly. [FLOW]
```

## sources (from PalmReadingResult, per-claim-cited only)

- cheiroslanguageo00chei_1, p.134 (score: 0.6054) -- feature: life line
- cheiroslanguageo00chei_1, p.95 (score: 0.5194) -- feature: fingers
- cheiroslanguageo00chei_1, p.98 (score: 0.5694) -- feature: fingers
- cheiroslanguageo00chei_1, p.96 (score: 0.5251) -- feature: fingers
- cheiroslanguageo00chei_1, p.112 (score: 0.6824) -- feature: mount of venus
- cheiroslanguageo00chei_1, p.112 (score: 0.663) -- feature: mount of jupiter

## Sanity asserts

- [x] At least 1 feature supported -- got 9: ['life line', 'head line', 'heart line', 'fate line', 'thumb', 'fingers', 'mount of venus', 'mount of jupiter', 'markings/other features']
- [x] `reading_text_tagged` is populated and contains >=1 `[C<n>]` tag
- [x] `result.claims` is non-empty -- got 7 claim(s)
- [x] Every non-excluded claim's chunk_id is a member of the gated chunk-id union -- checked 7 non-excluded claim(s) against 23 valid id(s)
- [x] Every `[C<n>]` tag cited in `reading_text_tagged` resolves to a member of the non-excluded claim id set -- cited ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7'] against ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7']

## ABORT -- sanity assert(s) failed

- ASSERT FAILED: Ring 1 passed=True on the final draft -- got False. Failures: ['exemplar_echo: i have examined many hands in']. Both Stage 1 and Stage 2 already own their own hard-capped F2c retry internally -- a failing final draft is a real, reportable defect, not something this probe can retry past.
- ASSERT FAILED: no 6-gram exemplar echo in reading_text -- got: ['exemplar_echo: i have examined many hands in']
