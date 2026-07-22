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

LIFE LINE: Present, deep, long, curves around the base of the thumb, no breaks or forks visible.

HEAD LINE: Present, deep, long, slightly curved, runs across the palm, no breaks or forks visible.

HEART LINE: Present, deep, slightly curved, ends below the index finger, no breaks or forks visible.

FATE LINE: Barely visible.

OTHER LINES: No other lines clearly visible.

MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.

MARKS: No marks clearly visible.
```

**RIGHT** (verbatim):
```
HAND SHAPE: Square palm, overall build is medium.

FINGERS: Fingers are slightly longer than the palm, appear straight, fingertips are rounded, spacing is moderate.

THUMB: Medium size, set moderately low, wide angle from the palm.

LIFE LINE: Present, deep, long, curves around the base of the thumb, no clear breaks or forks.

HEAD LINE: Present, deep, long, slightly curved, starts joined with the life line.

HEART LINE: Present, deep, long, slightly curved, ends below the index finger.

FATE LINE: Present, moderately deep, starts from the base of the palm and runs towards the middle finger.

OTHER LINES: Sun line is faintly visible, no clear health or marriage lines.

MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.

MARKS: No clear marks visible.
```

**HAND_DETAIL** (verbatim):
```
The image shows a hand with the following observable features:

- **Hand Shape**: The hand appears broad with a relatively square palm.
- **Finger Lengths**: The fingers are of moderate length. The index finger is slightly shorter than the middle finger, and the ring finger is slightly longer than the index finger. The little finger is noticeably shorter.
- **Thumb**: The thumb is of average length with a moderate angle of separation from the hand, indicating some flexibility.
- **Visible Lines**:
  - **Life Line**: A prominent line curves around the base of the thumb.
  - **Head Line**: Appears to be separate from the life line, running across the palm.
  - **Heart Line**: Curves across the top of the palm, below the fingers.
  - **Fate Line**: Not clearly visible in the image.
- **Mounts**: The mounts of Venus (base of the thumb) and Jupiter (below the index finger) appear slightly raised.
- **Markings**: There are no unusual markings or features visible.
- **Other Features**: There is a moderate amount of hair on the back of the hand and fingers.

These are the physical observations based on the image provided.
```

## Per-feature retrieval map (raw, pre-gate, all 10 registry features)

| Feature | Chunks (page_ref, score, chunk_id) |
|---|---|
| life line | (p.135, 0.6131, cheiroslanguageo00chei_1_p135_c0); (p.134, 0.6063, cheiroslanguageo00chei_1_p134_c1); (p.134, 0.5725, cheiroslanguageo00chei_1_p134_c0) |
| head line | (p.134, 0.5581, cheiroslanguageo00chei_1_p134_c2); (p.147, 0.5525, cheiroslanguageo00chei_1_p147_c1); (p.139, 0.5422, cheiroslanguageo00chei_1_p139_c1) |
| heart line | (p.160, 0.5735, cheiroslanguageo00chei_1_p160_c2); (p.160, 0.5706, cheiroslanguageo00chei_1_p160_c1); (p.159, 0.5534, cheiroslanguageo00chei_1_p159_c2) |
| fate line | (p.165, 0.5958, cheiroslanguageo00chei_1_p165_c1); (p.163, 0.5942, cheiroslanguageo00chei_1_p163_c1); (p.165, 0.5739, cheiroslanguageo00chei_1_p165_c0) |
| sun line | (p.166, 0.5206, cheiroslanguageo00chei_1_p166_c1); (p.166, 0.5176, cheiroslanguageo00chei_1_p166_c0); (p.169, 0.5064, cheiroslanguageo00chei_1_p169_c0) |
| thumb | (p.87, 0.5395, cheiroslanguageo00chei_1_p87_c0); (p.88, 0.5126, cheiroslanguageo00chei_1_p88_c1); (p.89, 0.5071, cheiroslanguageo00chei_1_p89_c2) |
| fingers | (p.98, 0.5886, cheiroslanguageo00chei_1_p98_c1); (p.96, 0.5284, cheiroslanguageo00chei_1_p96_c1); (p.96, 0.5282, cheiroslanguageo00chei_1_p96_c0) |
| mount of venus | (p.112, 0.6824, cheiroslanguageo00chei_1_p112_c0); (p.111, 0.6698, cheiroslanguageo00chei_1_p111_c1); (p.111, 0.5591, cheiroslanguageo00chei_1_p111_c0) |
| mount of jupiter | (p.112, 0.6630, cheiroslanguageo00chei_1_p112_c0); (p.111, 0.6457, cheiroslanguageo00chei_1_p111_c1); (p.113, 0.5894, cheiroslanguageo00chei_1_p113_c0) |
| markings/other features | (p.107, 0.4890, cheiroslanguageo00chei_1_p107_c0); (p.225, 0.4648, cheiroslanguageo00chei_1_p225_c1); (p.202, 0.4623, cheiroslanguageo00chei_1_p202_c1) |

## Support gate verdicts

- **supported_features** (registry order): ['life line', 'head line', 'heart line', 'fate line', 'sun line', 'thumb', 'fingers', 'mount of venus', 'mount of jupiter', 'markings/other features']
- **unsupported_features** (registry order): []
- **genuine negative-absence** (in neither tuple -- nothing to support, nothing to decline): []
- **valid_chunk_ids** (union, count=27): ['cheiroslanguageo00chei_1_p107_c0', 'cheiroslanguageo00chei_1_p111_c0', 'cheiroslanguageo00chei_1_p111_c1', 'cheiroslanguageo00chei_1_p112_c0', 'cheiroslanguageo00chei_1_p113_c0', 'cheiroslanguageo00chei_1_p134_c0', 'cheiroslanguageo00chei_1_p134_c1', 'cheiroslanguageo00chei_1_p134_c2', 'cheiroslanguageo00chei_1_p135_c0', 'cheiroslanguageo00chei_1_p139_c1', 'cheiroslanguageo00chei_1_p147_c1', 'cheiroslanguageo00chei_1_p159_c2', 'cheiroslanguageo00chei_1_p160_c1', 'cheiroslanguageo00chei_1_p160_c2', 'cheiroslanguageo00chei_1_p163_c1', 'cheiroslanguageo00chei_1_p165_c0', 'cheiroslanguageo00chei_1_p165_c1', 'cheiroslanguageo00chei_1_p166_c0', 'cheiroslanguageo00chei_1_p166_c1', 'cheiroslanguageo00chei_1_p169_c0', 'cheiroslanguageo00chei_1_p225_c1', 'cheiroslanguageo00chei_1_p87_c0', 'cheiroslanguageo00chei_1_p88_c1', 'cheiroslanguageo00chei_1_p89_c2', 'cheiroslanguageo00chei_1_p96_c0', 'cheiroslanguageo00chei_1_p96_c1', 'cheiroslanguageo00chei_1_p98_c1']

## Python decline block (pre-Stage-1 estimate, from the gate alone)

Not appended (unsupported_features is empty).

(Note: the FINAL decline block generate_palm_reading() builds can differ from this -- `_compute_decline_features` also folds in Stage-1 extraction failures and gate-supported-but-zero-claims features; see the final Ring 1 result section below for the authoritative reading.)

## LLM call count

12 chat.completions.create() call(s) captured total across BOTH stages (Stage 1: up to 2 calls PER attempted feature, own F2c retry; Stage 2: up to 2 calls, own whole-reading F2c retry -- no single global cap, unlike the old single-call architecture's flat 2-call ceiling).

## Stage1/Stage2 retry fields (data, NOT asserted -- single run, no rate claim)

- `stage1_retry_features`: NONE
- `stage2_retry_used`: True
- `retry_used` (COMPAT, true if either stage retried): True

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
| tag_legality | pass | -- |
| claim_coverage | pass | -- |
| doctrine_guard | pass | -- |

`validation.warnings` (F-A retired, superseded by Stage 2's own V-4 claim-coverage check -- always `()` now): none

## Full claims inventory (P6a pipe format, PalmReadingResult.claims verbatim)

claim_id | feature | chunk_id | valence | excluded_from_voice | exclusion_reason | condition_text | claim_text
C1 | life line | cheiroslanguageo00chei_1_p134_c1 | supports | False | None | None | A long, deep, and uninterrupted line of life indicates long life, good health, and vitality.
C2 | thumb | cheiroslanguageo00chei_1_p87_c0 | supports | False | None | None | A well-formed thumb that strikes a happy medium indicates sufficient independence of spirit, dignity, and force of character.
C3 | fingers | cheiroslanguageo00chei_1_p98_c1 | corrective | False | None | None | The statement that in every case the fingers must be longer than the palm is erroneous and misleading.
C4 | mount of venus | cheiroslanguageo00chei_1_p112_c0 | supports | False | None | None | A well-developed Mount of Venus indicates strong and robust health.
C5 | mount of venus | cheiroslanguageo00chei_1_p112_c0 | supports | False | None | None | The Mount of Venus denotes affection, sympathy toward others, benevolence, a desire to please, love and worship of beauty, love of color, and melody in music, and the attraction of the one sex to the other.
C6 | mount of venus | cheiroslanguageo00chei_1_p111_c1 | conditional | True | precondition unverified | if not abnormally large | The Mount of Venus is a favorable sign on the hand of man or woman when not abnormally large.
C7 | mount of jupiter | cheiroslanguageo00chei_1_p112_c0 | supports | False | None | None | When well developed, the Mount of Jupiter indicates ambition, pride, enthusiasm in endeavors, and a desire for power.

## reading_text (verbatim, final -- includes decline block + disclaimer, tags STRIPPED)

```
The line of life on your palm is long, deep, and uninterrupted, curving gracefully around the base of your thumb. This indicates a long life, good health, and vitality. Your thumb is of average length with a moderate angle of separation from the hand, suggesting a balance of independence and force of character.

The fingers on your hand are long relative to the palm. It is important to note that the belief that fingers must always be longer than the palm is misleading.

The Mount of Venus on your palm is well-developed. This signifies strong and robust health. Additionally, it denotes affection, sympathy toward others, benevolence, and a love for beauty, color, and melody in music.

The Mount of Jupiter is also slightly raised. This indicates ambition, pride, enthusiasm in your endeavors, and a desire for power.

Your head line is present, deep, and long, slightly curved as it runs across the palm. The heart line is similarly deep and slightly curved, ending below the index finger. The fate line is barely visible, and the sun line is faintly visible. There are no unusual markings or features visible on your palm.

A note on what I have not interpreted: the classical texts I work from do not clearly address the following as they appear in your hands: head line, heart line, fate line, sun line, markings and other features. Rather than guess, I have left these out of your reading.

For major life decisions, I recommend consulting a qualified astrologer or palm reader for a personal reading.
```

## reading_text_tagged (verbatim, Stage 2 raw voiced draft -- [C<n>]/[OBS]/[FLOW] tags intact)

```
The line of life on your palm is long, deep, and uninterrupted, curving gracefully around the base of your thumb. [OBS] This indicates a long life, good health, and vitality. [C1] Your thumb is of average length with a moderate angle of separation from the hand, suggesting a balance of independence and force of character. [C2] 

The fingers on your hand are long relative to the palm. [OBS] It is important to note that the belief that fingers must always be longer than the palm is misleading. [C3] 

The Mount of Venus on your palm is well-developed. [OBS] This signifies strong and robust health. [C4] Additionally, it denotes affection, sympathy toward others, benevolence, and a love for beauty, color, and melody in music. [C5] 

The Mount of Jupiter is also slightly raised. [OBS] This indicates ambition, pride, enthusiasm in your endeavors, and a desire for power. [C7] 

Your head line is present, deep, and long, slightly curved as it runs across the palm. [OBS] The heart line is similarly deep and slightly curved, ending below the index finger. [OBS] The fate line is barely visible, and the sun line is faintly visible. [OBS] There are no unusual markings or features visible on your palm. [OBS]
```

## sources (from PalmReadingResult, per-claim-cited only)

- cheiroslanguageo00chei_1, p.134 (score: 0.6054) -- feature: life line
- cheiroslanguageo00chei_1, p.87 (score: 0.5395) -- feature: thumb
- cheiroslanguageo00chei_1, p.98 (score: 0.5886) -- feature: fingers
- cheiroslanguageo00chei_1, p.112 (score: 0.6824) -- feature: mount of venus
- cheiroslanguageo00chei_1, p.112 (score: 0.663) -- feature: mount of jupiter

## Sanity asserts

- [x] At least 1 feature supported -- got 10: ['life line', 'head line', 'heart line', 'fate line', 'sun line', 'thumb', 'fingers', 'mount of venus', 'mount of jupiter', 'markings/other features']
- [x] Ring 1 `passed=True` on the final draft
- [x] No 6-gram exemplar echo in `reading_text`
- [x] `reading_text_tagged` is populated and contains >=1 `[C<n>]` tag
- [x] `result.claims` is non-empty -- got 7 claim(s)
- [x] Every non-excluded claim's chunk_id is a member of the gated chunk-id union -- checked 6 non-excluded claim(s) against 27 valid id(s)
- [x] Every `[C<n>]` tag cited in `reading_text_tagged` resolves to a member of the non-excluded claim id set -- cited ['C1', 'C2', 'C3', 'C4', 'C5', 'C7'] against ['C1', 'C2', 'C3', 'C4', 'C5', 'C7']

## Verdict

All 6 sanity asserts PASSED. This is a wiring smoke check only -- it says nothing about interpretive quality/citation accuracy (that is Ring 3 pass 5's job, on fresh uploads, human-scored, with both checkpoints live). No product code was touched or fixed by this script.