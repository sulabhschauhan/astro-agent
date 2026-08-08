## RUN 2026-07-31T15:06:06.947177

### capture_reason
instability, silence

### Confirmed descriptions
#### LEFT
HAND SHAPE: Square palm, overall build is medium.

FINGERS: Fingers are long relative to the palm, appear straight, fingertips are rounded, spacing is moderate.

THUMB: Medium relative size, set moderately low, wide angle from the palm.

LIFE LINE: Present, deep, long, curves around the base of the thumb, no breaks, chains, forks, or islands visible.

HEAD LINE: Present, deep, long, slightly curved, no breaks, chains, forks, or islands visible.

HEART LINE: Present, deep, long, slightly curved, no breaks, chains, forks, or islands visible.

FATE LINE: Barely visible.

OTHER LINES: No other lines clearly visible.

MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.

MARKS: No marks clearly visible.
#### RIGHT
HAND SHAPE: Square palm, medium build

FINGERS: Medium length relative to palm, straight, rounded fingertips, moderate spacing

THUMB: Medium size, set moderately low, wide angle from the palm

LIFE LINE: Present, deep, long, curves around the base of the thumb, no clear breaks or forks

HEAD LINE: Present, deep, long, slightly curved, starts joined with the life line

HEART LINE: Present, deep, long, curves slightly upward, ends below the index finger

FATE LINE: Barely visible

OTHER LINES: Not clearly visible

MOUNTS: Mount of Venus appears developed, other mounts not clearly visible

MARKS: Not clearly visible

### reading_text
The line of life on your palm is long, narrow, and deep, curving gracefully around the base of your thumb without any irregularities such as breaks, chains, forks, or islands. This formation promises you longevity, accompanied by good health and vitality.

Turning to the line of head, it is present, deep, long, and slightly curved, with no breaks or other interruptions. This line speaks to your mentality, indicating intellectual strength and a clear direction and quality of talent.

Your thumb is of medium size, set moderately low, and forms a wide angle from the palm. This well-formed thumb suggests a nature that is independent yet balanced, avoiding extremes in character.

The Mount of Venus on your hand is well-developed. This indicates that you possess strong and robust health.

These features together reveal a person with a balanced character, intellectual strength, and robust health, marked by vitality and independence.

A note on what I have not interpreted: the classical texts I work from do not clearly address the following as they appear in your hands: heart line, fate line, sun line, fingers, mount of jupiter. Rather than guess, I have left these out of your reading.

For major life decisions, I recommend consulting a qualified astrologer or palm reader for a personal reading.

### READING (TAGGED)
The line of life on your palm is long, narrow, and deep, curving gracefully around the base of your thumb without any irregularities such as breaks, chains, forks, or islands. [OBS] This formation promises you longevity, accompanied by good health and vitality. [C1]

Turning to the line of head, it is present, deep, long, and slightly curved, with no breaks or other interruptions. [OBS] This line speaks to your mentality, indicating intellectual strength and a clear direction and quality of talent. [C2]

Your thumb is of medium size, set moderately low, and forms a wide angle from the palm. [OBS] This well-formed thumb suggests a nature that is independent yet balanced, avoiding extremes in character. [C3]

The Mount of Venus on your hand is well-developed. [OBS] This indicates that you possess strong and robust health. [C4]

These features together reveal a person with a balanced character, intellectual strength, and robust health, marked by vitality and independence. [FLOW]

### sources
- cheiroslanguageo00chei_1, p.134 (score: 0.5775, feature: life line)
- cheiroslanguageo00chei_1, p.145 (score: 0.5588, feature: head line)
- cheiroslanguageo00chei_1, p.87 (score: 0.5078, feature: thumb)
- cheiroslanguageo00chei_1, p.112 (score: 0.6181, feature: mount of venus)

### feature_support
supported_features: ('life line', 'head line', 'heart line', 'fate line', 'thumb', 'fingers', 'mount of venus')
unsupported_features: ('sun line', 'mount of jupiter')

### claims_inventory
C1 | life line | cheiroslanguageo00chei_1_p134_c1 | supports | False | None | None | A long, narrow, and deep line of life without irregularities promises long life, good health, and vitality.
C2 | head line | cheiroslanguageo00chei_1_p145_c0 | supports | False | None | None | The line of head relates principally to the mentality of the subject, including intellectual strength or weakness and the direction and quality of talent.
C3 | thumb | cheiroslanguageo00chei_1_p87_c0 | supports | False | None | None | A well-formed thumb that is not too close to the side or at right angles to the palm indicates a nature that is independent and not extreme, suggesting a balance in character.
C4 | mount of venus | cheiroslanguageo00chei_1_p112_c0 | supports | False | None | None | A well-developed Mount of Venus indicates strong and robust health.

### ring1_validation
passed: True
failures: ()
retry_used: True
stage1_retry_features: thumb
stage1_feature_diagnostics:
  fate line: outcome=empty_first attempt_1=validated_empty/0 (raw=0) attempt_2=not_attempted/None (raw=None)
  fingers: outcome=empty_first attempt_1=validated_empty/0 (raw=0) attempt_2=not_attempted/None (raw=None)
  head line: outcome=success_first attempt_1=validated/1 (raw=1) attempt_2=not_attempted/None (raw=None)
  heart line: outcome=empty_first attempt_1=validated_empty/0 (raw=0) attempt_2=not_attempted/None (raw=None)
  life line: outcome=success_first attempt_1=validated/1 (raw=1) attempt_2=not_attempted/None (raw=None)
  markings/other features: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of jupiter: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of venus: outcome=success_first attempt_1=validated/1 (raw=1) attempt_2=not_attempted/None (raw=None)
  sun line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  thumb: outcome=success_retry attempt_1=validation_failed/0 (raw=1) attempt_2=validated/1 (raw=1)
    attempt_1_failures: claims[0] claim_text overlap 0.31 below floor 0.4 for chunk 'cheiroslanguageo00chei_1_p88_c0'
stage2_retry_used: True
stage2_first_attempt_failures: doctrine_guard: [FLOW] sentence mentions feature-noun 'life': 'These features together paint a picture of a person with a balanced character, intellectual strength, and robust health, promising a life of vitality and independence.'
validation_failures: NONE
ring1_failures:
none

### near_miss_margin
  fate line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p165_c1, 0.6002), (2, cheiroslanguageo00chei_1_p163_c1, 0.5869), (3, cheiroslanguageo00chei_1_p165_c0, 0.5671), (4, cheiroslanguageo00chei_1_p163_c2, 0.561), (5, cheiroslanguageo00chei_1_p162_c0, 0.5515), (6, cheiroslanguageo00chei_1_p163_c0, 0.5486), (7, cheiroslanguageo00chei_1_p164_c1, 0.5336), (8, cheiroslanguageo00chei_1_p164_c2, 0.5165), (9, cheiroslanguageo00chei_1_p162_c1, 0.5081), (10, cheiroslanguageo00chei_1_p164_c0, 0.4756), (11, cheiroslanguageo00chei_1_p165_c2, 0.4595), (12, cheiroslanguageo00chei_1_p163_c3, 0.4594), (13, cheiroslanguageo00chei_1_p164_c3, 0.4225), (14, cheiroslanguageo00chei_1_p162_c2, 0.3621)]
  fingers: window=3 candidates=[(1, cheiroslanguageo00chei_1_p96_c0, 0.5164), (2, cheiroslanguageo00chei_1_p96_c2, 0.5117), (3, cheiroslanguageo00chei_1_p96_c1, 0.51), (4, cheiroslanguageo00chei_1_p95_c0, 0.4715), (5, cheiroslanguageo00chei_1_p97_c0, 0.4659), (6, cheiroslanguageo00chei_1_p96_c3, 0.4656), (7, cheiroslanguageo00chei_1_p95_c2, 0.447), (8, cheiroslanguageo00chei_1_p95_c1, 0.4451), (9, cheiroslanguageo00chei_1_p93_c0, 0.3858), (10, cheiroslanguageo00chei_1_p94_c0, 0.3716), (11, cheiroslanguageo00chei_1_p93_c1, 0.2714)]
  head line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p145_c0, 0.5588), (2, cheiroslanguageo00chei_1_p147_c1, 0.526), (3, cheiroslanguageo00chei_1_p151_c2, 0.5226), (4, cheiroslanguageo00chei_1_p147_c0, 0.5066), (5, cheiroslanguageo00chei_1_p148_c1, 0.4943), (6, cheiroslanguageo00chei_1_p148_c0, 0.4909), (7, cheiroslanguageo00chei_1_p150_c2, 0.4887), (8, cheiroslanguageo00chei_1_p147_c3, 0.4814), (9, cheiroslanguageo00chei_1_p151_c1, 0.4715), (10, cheiroslanguageo00chei_1_p149_c0, 0.4706), (11, cheiroslanguageo00chei_1_p153_c1, 0.4687), (12, cheiroslanguageo00chei_1_p150_c0, 0.4672), (13, cheiroslanguageo00chei_1_p150_c1, 0.4557), (14, cheiroslanguageo00chei_1_p146_c1, 0.4521), (15, cheiroslanguageo00chei_1_p154_c0, 0.4489), (16, cheiroslanguageo00chei_1_p148_c2, 0.4464), (17, cheiroslanguageo00chei_1_p146_c0, 0.4423), (18, cheiroslanguageo00chei_1_p146_c2, 0.4208), (19, cheiroslanguageo00chei_1_p149_c1, 0.4114), (20, cheiroslanguageo00chei_1_p153_c0, 0.4093), (21, cheiroslanguageo00chei_1_p145_c1, 0.4086), (22, cheiroslanguageo00chei_1_p147_c2, 0.3982), (23, cheiroslanguageo00chei_1_p154_c1, 0.3921), (24, cheiroslanguageo00chei_1_p155_c0, 0.3906), (25, cheiroslanguageo00chei_1_p151_c0, 0.3889), (26, cheiroslanguageo00chei_1_p152_c1, 0.3724), (27, cheiroslanguageo00chei_1_p152_c0, 0.3552), (28, cheiroslanguageo00chei_1_p155_c1, 0.3123), (29, cheiroslanguageo00chei_1_p145_c2, 0.2804), (30, cheiroslanguageo00chei_1_p153_c2, 0.1865)]
  heart line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p160_c2, 0.6427), (2, cheiroslanguageo00chei_1_p161_c0, 0.6188), (3, cheiroslanguageo00chei_1_p159_c2, 0.6061), (4, cheiroslanguageo00chei_1_p159_c3, 0.6054), (5, cheiroslanguageo00chei_1_p156_c0, 0.5884), (6, cheiroslanguageo00chei_1_p160_c1, 0.557), (7, cheiroslanguageo00chei_1_p156_c1, 0.5494), (8, cheiroslanguageo00chei_1_p160_c3, 0.5219), (9, cheiroslanguageo00chei_1_p160_c0, 0.4791), (10, cheiroslanguageo00chei_1_p159_c1, 0.4752), (11, cheiroslanguageo00chei_1_p159_c0, 0.3856), (12, cheiroslanguageo00chei_1_p156_c2, 0.3415)]
  life line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p139_c0, 0.6108), (2, cheiroslanguageo00chei_1_p134_c2, 0.5801), (3, cheiroslanguageo00chei_1_p134_c1, 0.5775), (4, cheiroslanguageo00chei_1_p135_c0, 0.5652), (5, cheiroslanguageo00chei_1_p139_c1, 0.5552), (6, cheiroslanguageo00chei_1_p138_c1, 0.5406), (7, cheiroslanguageo00chei_1_p135_c2, 0.5394), (8, cheiroslanguageo00chei_1_p136_c1, 0.5337), (9, cheiroslanguageo00chei_1_p136_c3, 0.5332), (10, cheiroslanguageo00chei_1_p134_c0, 0.5317), (11, cheiroslanguageo00chei_1_p135_c1, 0.5253), (12, cheiroslanguageo00chei_1_p137_c1, 0.5195), (13, cheiroslanguageo00chei_1_p136_c2, 0.5054), (14, cheiroslanguageo00chei_1_p137_c0, 0.5013), (15, cheiroslanguageo00chei_1_p138_c2, 0.4935), (16, cheiroslanguageo00chei_1_p138_c0, 0.466), (17, cheiroslanguageo00chei_1_p137_c3, 0.4625), (18, cheiroslanguageo00chei_1_p133_c0, 0.4477), (19, cheiroslanguageo00chei_1_p137_c2, 0.4165), (20, cheiroslanguageo00chei_1_p134_c3, 0.399), (21, cheiroslanguageo00chei_1_p136_c0, 0.3986), (22, cheiroslanguageo00chei_1_p133_c1, 0.177), (23, cheiroslanguageo00chei_1_p139_c2, 0.0862)]
  mount of venus: window=3 candidates=[(1, cheiroslanguageo00chei_1_p111_c1, 0.6521), (2, cheiroslanguageo00chei_1_p112_c0, 0.6181), (3, cheiroslanguageo00chei_1_p113_c0, 0.497), (4, cheiroslanguageo00chei_1_p111_c0, 0.4857), (5, cheiroslanguageo00chei_1_p112_c1, 0.4774), (6, cheiroslanguageo00chei_1_p113_c1, 0.4747), (7, cheiroslanguageo00chei_1_p112_c2, 0.4245)]
  thumb: window=3 candidates=[(1, cheiroslanguageo00chei_1_p88_c0, 0.5104), (2, cheiroslanguageo00chei_1_p87_c0, 0.5078), (3, cheiroslanguageo00chei_1_p88_c1, 0.5041), (4, cheiroslanguageo00chei_1_p89_c2, 0.5035), (5, cheiroslanguageo00chei_1_p89_c0, 0.4813), (6, cheiroslanguageo00chei_1_p86_c0, 0.4576), (7, cheiroslanguageo00chei_1_p85_c0, 0.4479), (8, cheiroslanguageo00chei_1_p90_c2, 0.426), (9, cheiroslanguageo00chei_1_p90_c0, 0.3723), (10, cheiroslanguageo00chei_1_p88_c2, 0.3636), (11, cheiroslanguageo00chei_1_p85_c1, 0.3588), (12, cheiroslanguageo00chei_1_p89_c1, 0.2875), (13, cheiroslanguageo00chei_1_p90_c1, 0.2682), (14, cheiroslanguageo00chei_1_p87_c1, 0.0836)]

## RUN 2026-07-31T15:13:30.702501

### capture_reason
instability, silence

### Confirmed descriptions
#### LEFT
HAND SHAPE: Square palm, overall build is medium.

FINGERS: Fingers are long relative to the palm, appear straight, fingertips are rounded, spacing is moderate.

THUMB: Medium relative size, set moderately low, wide angle from the palm.

LIFE LINE: Present, deep, long, curves around the base of the thumb, no breaks, chains, forks, or islands visible.

HEAD LINE: Present, deep, long, slightly curved, no breaks, chains, forks, or islands visible.

HEART LINE: Present, deep, long, slightly curved, no breaks, chains, forks, or islands visible.

FATE LINE: Barely visible.

OTHER LINES: No other lines clearly visible.

MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.

MARKS: No marks clearly visible.
#### RIGHT
HAND SHAPE: Square palm, medium build

FINGERS: Medium length relative to palm, straight, rounded fingertips, moderate spacing

THUMB: Medium size, set moderately low, wide angle from the palm

LIFE LINE: Present, deep, long, curves around the base of the thumb, no clear breaks or forks

HEAD LINE: Present, deep, long, slightly curved, starts joined with the life line

HEART LINE: Present, deep, long, curves slightly upward, ends below the index finger

FATE LINE: Barely visible

OTHER LINES: Not clearly visible

MOUNTS: Mount of Venus appears developed, other mounts not clearly visible

MARKS: Not clearly visible

### reading_text
The line of life on your palm is long, narrow, and deep, curving gracefully around the base of your thumb without any irregularities such as breaks, chains, forks, or islands. This formation promises you a long life, accompanied by good health and vitality.

Turning to the line of head, it is present, deep, and long, with a slight curve and no visible breaks or irregularities. This line speaks to your mentality, indicating intellectual strength and a clear direction and quality of talent.

Your thumb is of medium size, set moderately low, and forms a wide angle from the palm. Such a well-formed thumb suggests an independence of spirit and a strong character.

The Mount of Venus on your hand is well-developed. This feature indicates that you possess strong and robust health.

A note on what I have not interpreted: the classical texts I work from do not clearly address the following as they appear in your hands: heart line, fate line, sun line, fingers, mount of jupiter. Rather than guess, I have left these out of your reading.

For major life decisions, I recommend consulting a qualified astrologer or palm reader for a personal reading.

### READING (TAGGED)
The line of life on your palm is long, narrow, and deep, curving gracefully around the base of your thumb without any irregularities such as breaks, chains, forks, or islands. [OBS] This formation promises you a long life, accompanied by good health and vitality. [C1]

Turning to the line of head, it is present, deep, and long, with a slight curve and no visible breaks or irregularities. [OBS] This line speaks to your mentality, indicating intellectual strength and a clear direction and quality of talent. [C2]

Your thumb is of medium size, set moderately low, and forms a wide angle from the palm. [OBS] Such a well-formed thumb suggests an independence of spirit and a strong character. [C3]

The Mount of Venus on your hand is well-developed. [OBS] This feature indicates that you possess strong and robust health. [C4]

### sources
- cheiroslanguageo00chei_1, p.134 (score: 0.5775, feature: life line)
- cheiroslanguageo00chei_1, p.145 (score: 0.5589, feature: head line)
- cheiroslanguageo00chei_1, p.87 (score: 0.5078, feature: thumb)
- cheiroslanguageo00chei_1, p.112 (score: 0.6181, feature: mount of venus)

### feature_support
supported_features: ('life line', 'head line', 'heart line', 'fate line', 'thumb', 'fingers', 'mount of venus')
unsupported_features: ('sun line', 'mount of jupiter')

### claims_inventory
C1 | life line | cheiroslanguageo00chei_1_p134_c1 | supports | False | None | None | A long, narrow, and deep line of life without irregularities promises long life, good health, and vitality.
C2 | head line | cheiroslanguageo00chei_1_p145_c0 | supports | False | None | None | The line of head relates principally to the mentality of the subject, including intellectual strength or weakness and the direction and quality of talent.
C3 | thumb | cheiroslanguageo00chei_1_p87_c0 | supports | False | None | None | A well-formed thumb that is not too close to the palm indicates independence of spirit and strength of character.
C4 | mount of venus | cheiroslanguageo00chei_1_p112_c0 | supports | False | None | None | A well-developed Mount of Venus indicates strong and robust health.

### ring1_validation
passed: True
failures: ()
retry_used: True
stage1_retry_features: thumb
stage1_feature_diagnostics:
  fate line: outcome=empty_first attempt_1=validated_empty/0 (raw=0) attempt_2=not_attempted/None (raw=None)
  fingers: outcome=empty_first attempt_1=validated_empty/0 (raw=0) attempt_2=not_attempted/None (raw=None)
  head line: outcome=success_first attempt_1=validated/1 (raw=1) attempt_2=not_attempted/None (raw=None)
  heart line: outcome=empty_first attempt_1=validated_empty/0 (raw=0) attempt_2=not_attempted/None (raw=None)
  life line: outcome=success_first attempt_1=validated/1 (raw=1) attempt_2=not_attempted/None (raw=None)
  markings/other features: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of jupiter: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of venus: outcome=success_first attempt_1=validated/1 (raw=1) attempt_2=not_attempted/None (raw=None)
  sun line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  thumb: outcome=success_retry attempt_1=validation_failed/0 (raw=1) attempt_2=validated/1 (raw=1)
    attempt_1_failures: claims[0] claim_text overlap 0.38 below floor 0.4 for chunk 'cheiroslanguageo00chei_1_p88_c0'
stage2_retry_used: False
stage2_first_attempt_failures: NONE
validation_failures: NONE
ring1_failures:
none

### near_miss_margin
  fate line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p165_c1, 0.6001), (2, cheiroslanguageo00chei_1_p163_c1, 0.5869), (3, cheiroslanguageo00chei_1_p165_c0, 0.5671), (4, cheiroslanguageo00chei_1_p163_c2, 0.561), (5, cheiroslanguageo00chei_1_p162_c0, 0.5515), (6, cheiroslanguageo00chei_1_p163_c0, 0.5486), (7, cheiroslanguageo00chei_1_p164_c1, 0.5336), (8, cheiroslanguageo00chei_1_p164_c2, 0.5165), (9, cheiroslanguageo00chei_1_p162_c1, 0.5081), (10, cheiroslanguageo00chei_1_p164_c0, 0.4756), (11, cheiroslanguageo00chei_1_p165_c2, 0.4595), (12, cheiroslanguageo00chei_1_p163_c3, 0.4594), (13, cheiroslanguageo00chei_1_p164_c3, 0.4225), (14, cheiroslanguageo00chei_1_p162_c2, 0.3622)]
  fingers: window=3 candidates=[(1, cheiroslanguageo00chei_1_p96_c0, 0.5164), (2, cheiroslanguageo00chei_1_p96_c2, 0.5117), (3, cheiroslanguageo00chei_1_p96_c1, 0.51), (4, cheiroslanguageo00chei_1_p95_c0, 0.4715), (5, cheiroslanguageo00chei_1_p97_c0, 0.4659), (6, cheiroslanguageo00chei_1_p96_c3, 0.4656), (7, cheiroslanguageo00chei_1_p95_c2, 0.447), (8, cheiroslanguageo00chei_1_p95_c1, 0.4451), (9, cheiroslanguageo00chei_1_p93_c0, 0.3858), (10, cheiroslanguageo00chei_1_p94_c0, 0.3716), (11, cheiroslanguageo00chei_1_p93_c1, 0.2714)]
  head line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p145_c0, 0.5589), (2, cheiroslanguageo00chei_1_p147_c1, 0.526), (3, cheiroslanguageo00chei_1_p151_c2, 0.5226), (4, cheiroslanguageo00chei_1_p147_c0, 0.5066), (5, cheiroslanguageo00chei_1_p148_c1, 0.4943), (6, cheiroslanguageo00chei_1_p148_c0, 0.4909), (7, cheiroslanguageo00chei_1_p150_c2, 0.4888), (8, cheiroslanguageo00chei_1_p147_c3, 0.4814), (9, cheiroslanguageo00chei_1_p151_c1, 0.4715), (10, cheiroslanguageo00chei_1_p149_c0, 0.4706), (11, cheiroslanguageo00chei_1_p153_c1, 0.4687), (12, cheiroslanguageo00chei_1_p150_c0, 0.4672), (13, cheiroslanguageo00chei_1_p150_c1, 0.4557), (14, cheiroslanguageo00chei_1_p146_c1, 0.4521), (15, cheiroslanguageo00chei_1_p154_c0, 0.4489), (16, cheiroslanguageo00chei_1_p148_c2, 0.4464), (17, cheiroslanguageo00chei_1_p146_c0, 0.4423), (18, cheiroslanguageo00chei_1_p146_c2, 0.4209), (19, cheiroslanguageo00chei_1_p149_c1, 0.4114), (20, cheiroslanguageo00chei_1_p153_c0, 0.4093), (21, cheiroslanguageo00chei_1_p145_c1, 0.4086), (22, cheiroslanguageo00chei_1_p147_c2, 0.3982), (23, cheiroslanguageo00chei_1_p154_c1, 0.3921), (24, cheiroslanguageo00chei_1_p155_c0, 0.3907), (25, cheiroslanguageo00chei_1_p151_c0, 0.389), (26, cheiroslanguageo00chei_1_p152_c1, 0.3724), (27, cheiroslanguageo00chei_1_p152_c0, 0.3553), (28, cheiroslanguageo00chei_1_p155_c1, 0.3123), (29, cheiroslanguageo00chei_1_p145_c2, 0.2804), (30, cheiroslanguageo00chei_1_p153_c2, 0.1865)]
  heart line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p160_c2, 0.6427), (2, cheiroslanguageo00chei_1_p161_c0, 0.6188), (3, cheiroslanguageo00chei_1_p159_c2, 0.6061), (4, cheiroslanguageo00chei_1_p159_c3, 0.6054), (5, cheiroslanguageo00chei_1_p156_c0, 0.5884), (6, cheiroslanguageo00chei_1_p160_c1, 0.557), (7, cheiroslanguageo00chei_1_p156_c1, 0.5494), (8, cheiroslanguageo00chei_1_p160_c3, 0.522), (9, cheiroslanguageo00chei_1_p160_c0, 0.4791), (10, cheiroslanguageo00chei_1_p159_c1, 0.4751), (11, cheiroslanguageo00chei_1_p159_c0, 0.3856), (12, cheiroslanguageo00chei_1_p156_c2, 0.3415)]
  life line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p139_c0, 0.6108), (2, cheiroslanguageo00chei_1_p134_c2, 0.5801), (3, cheiroslanguageo00chei_1_p134_c1, 0.5775), (4, cheiroslanguageo00chei_1_p135_c0, 0.5652), (5, cheiroslanguageo00chei_1_p139_c1, 0.5552), (6, cheiroslanguageo00chei_1_p138_c1, 0.5406), (7, cheiroslanguageo00chei_1_p135_c2, 0.5394), (8, cheiroslanguageo00chei_1_p136_c1, 0.5337), (9, cheiroslanguageo00chei_1_p136_c3, 0.5332), (10, cheiroslanguageo00chei_1_p134_c0, 0.5317), (11, cheiroslanguageo00chei_1_p135_c1, 0.5253), (12, cheiroslanguageo00chei_1_p137_c1, 0.5195), (13, cheiroslanguageo00chei_1_p136_c2, 0.5054), (14, cheiroslanguageo00chei_1_p137_c0, 0.5013), (15, cheiroslanguageo00chei_1_p138_c2, 0.4935), (16, cheiroslanguageo00chei_1_p138_c0, 0.466), (17, cheiroslanguageo00chei_1_p137_c3, 0.4625), (18, cheiroslanguageo00chei_1_p133_c0, 0.4477), (19, cheiroslanguageo00chei_1_p137_c2, 0.4165), (20, cheiroslanguageo00chei_1_p134_c3, 0.399), (21, cheiroslanguageo00chei_1_p136_c0, 0.3986), (22, cheiroslanguageo00chei_1_p133_c1, 0.177), (23, cheiroslanguageo00chei_1_p139_c2, 0.0862)]
  mount of venus: window=3 candidates=[(1, cheiroslanguageo00chei_1_p111_c1, 0.652), (2, cheiroslanguageo00chei_1_p112_c0, 0.6181), (3, cheiroslanguageo00chei_1_p113_c0, 0.497), (4, cheiroslanguageo00chei_1_p111_c0, 0.4856), (5, cheiroslanguageo00chei_1_p112_c1, 0.4774), (6, cheiroslanguageo00chei_1_p113_c1, 0.4747), (7, cheiroslanguageo00chei_1_p112_c2, 0.4245)]
  thumb: window=3 candidates=[(1, cheiroslanguageo00chei_1_p88_c0, 0.5104), (2, cheiroslanguageo00chei_1_p87_c0, 0.5078), (3, cheiroslanguageo00chei_1_p88_c1, 0.5041), (4, cheiroslanguageo00chei_1_p89_c2, 0.5035), (5, cheiroslanguageo00chei_1_p89_c0, 0.4812), (6, cheiroslanguageo00chei_1_p86_c0, 0.4576), (7, cheiroslanguageo00chei_1_p85_c0, 0.4479), (8, cheiroslanguageo00chei_1_p90_c2, 0.426), (9, cheiroslanguageo00chei_1_p90_c0, 0.3723), (10, cheiroslanguageo00chei_1_p88_c2, 0.3636), (11, cheiroslanguageo00chei_1_p85_c1, 0.3588), (12, cheiroslanguageo00chei_1_p89_c1, 0.2875), (13, cheiroslanguageo00chei_1_p90_c1, 0.2682), (14, cheiroslanguageo00chei_1_p87_c1, 0.0836)]

## RUN 2026-07-31T15:16:23.707563

### capture_reason
instability, silence

### Confirmed descriptions
#### LEFT
HAND SHAPE: Square palm, overall build is medium.

FINGERS: Fingers are long relative to the palm, appear straight, fingertips are rounded, spacing is moderate.

THUMB: Medium relative size, set moderately low, wide angle from the palm.

LIFE LINE: Present, deep, long, curves around the base of the thumb, no breaks, chains, forks, or islands visible.

HEAD LINE: Present, deep, long, slightly curved, no breaks, chains, forks, or islands visible.

HEART LINE: Present, deep, long, slightly curved, no breaks, chains, forks, or islands visible.

FATE LINE: Barely visible.

OTHER LINES: No other lines clearly visible.

MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.

MARKS: No marks clearly visible.
#### RIGHT
HAND SHAPE: Square palm, medium build

FINGERS: Medium length relative to palm, straight, rounded fingertips, moderate spacing

THUMB: Medium size, set moderately low, wide angle from the palm

LIFE LINE: Present, deep, long, curves around the base of the thumb, no clear breaks or forks

HEAD LINE: Present, deep, long, slightly curved, starts joined with the life line

HEART LINE: Present, deep, long, curves slightly upward, ends below the index finger

FATE LINE: Barely visible

OTHER LINES: Not clearly visible

MOUNTS: Mount of Venus appears developed, other mounts not clearly visible

MARKS: Not clearly visible
#### HAND_DETAIL
The image shows a hand with the following observable features:

- **Hand Shape**: The hand appears broad with a relatively square palm.
- **Finger Lengths**: The fingers are of moderate length. The index finger is slightly shorter than the middle finger, and the ring finger is slightly longer than the index finger. The little finger is noticeably shorter than the others.
- **Thumb**: The thumb is of moderate length and appears to have a wide angle of separation from the hand, indicating flexibility.
- **Visible Lines**:
  - **Life Line**: A prominent line curves around the base of the thumb.
  - **Head Line**: This line runs horizontally across the palm, starting near the life line.
  - **Heart Line**: The heart line is visible, curving across the top of the palm.
  - **Fate Line**: There is no clearly visible fate line in the image.
- **Mounts**: The mounts of Venus (below the thumb) and Jupiter (below the index finger) appear slightly raised.
- **Markings**: There are no unusual markings or features visible on the hand.

These are the physical observations based on the image provided.

### reading_text
The life line on your palm is long, deep, and curves gracefully around the base of your thumb without any breaks or irregularities. This promises you a long life, good health, and vitality. Your thumb is of moderate length and set at a wide angle from the palm, indicating a well-formed thumb. This suggests you possess sufficient independence of spirit and force of character.

Your fingers are long relative to the palm, which indicates a love of detail in everything you do and a tendency to worry over little things. The Mount of Venus on your hand is well-developed. This is a sign of strong and robust health. Additionally, the mounts of Venus and Jupiter are slightly raised. This development indicates ambition, pride, enthusiasm in your endeavors, and a desire for power.

A note on what I have not interpreted: the classical texts I work from do not clearly address the following as they appear in your hands: head line, heart line, fate line, sun line. Rather than guess, I have left these out of your reading.

For major life decisions, I recommend consulting a qualified astrologer or palm reader for a personal reading.

### READING (TAGGED)
The life line on your palm is long, deep, and curves gracefully around the base of your thumb without any breaks or irregularities. [OBS] This promises you a long life, good health, and vitality. [C1] Your thumb is of moderate length and set at a wide angle from the palm, indicating a well-formed thumb. [OBS] This suggests you possess sufficient independence of spirit and force of character. [C2]

Your fingers are long relative to the palm, which indicates a love of detail in everything you do and a tendency to worry over little things. [C3] The Mount of Venus on your hand is well-developed. [OBS] This is a sign of strong and robust health. [C4] Additionally, the mounts of Venus and Jupiter are slightly raised. [OBS] This development indicates ambition, pride, enthusiasm in your endeavors, and a desire for power. [C5]

### sources
- cheiroslanguageo00chei_1, p.134 (score: 0.6063, feature: life line)
- cheiroslanguageo00chei_1, p.87 (score: 0.5199, feature: thumb)
- cheiroslanguageo00chei_1, p.95 (score: 0.5194, feature: fingers)
- cheiroslanguageo00chei_1, p.112 (score: 0.6725, feature: mount of venus)
- cheiroslanguageo00chei_1, p.112 (score: 0.6517, feature: mount of jupiter)

### feature_support
supported_features: ('life line', 'head line', 'heart line', 'fate line', 'thumb', 'fingers', 'mount of venus', 'mount of jupiter')
unsupported_features: ('sun line',)

### claims_inventory
C1 | life line | cheiroslanguageo00chei_1_p134_c1 | supports | False | None | None | A long, narrow, and deep line without irregularities promises long life, good health, and vitality.
C2 | thumb | cheiroslanguageo00chei_1_p87_c0 | supports | False | None | None | A thumb that is well formed and strikes a happy medium between extremes indicates sufficient independence of spirit, dignity, and force of character.
C3 | fingers | cheiroslanguageo00chei_1_p95_c0 | supports | False | None | None | Long fingers indicate a love of detail in everything and a tendency to worry over little things.
C4 | mount of venus | cheiroslanguageo00chei_1_p112_c0 | supports | False | None | None | A well-developed Mount of Venus indicates strong and robust health.
C5 | mount of jupiter | cheiroslanguageo00chei_1_p112_c0 | supports | False | None | None | When developed, it indicates ambition, pride, enthusiasm in anything attempted, and desire for power.

### ring1_validation
passed: True
failures: ()
retry_used: True
stage1_retry_features: NONE
stage1_feature_diagnostics:
  fate line: outcome=empty_first attempt_1=validated_empty/0 (raw=0) attempt_2=not_attempted/None (raw=None)
  fingers: outcome=success_first attempt_1=validated/1 (raw=1) attempt_2=not_attempted/None (raw=None)
  head line: outcome=empty_first attempt_1=validated_empty/0 (raw=0) attempt_2=not_attempted/None (raw=None)
  heart line: outcome=empty_first attempt_1=validated_empty/0 (raw=0) attempt_2=not_attempted/None (raw=None)
  life line: outcome=success_first attempt_1=validated/1 (raw=1) attempt_2=not_attempted/None (raw=None)
  markings/other features: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of jupiter: outcome=success_first attempt_1=validated/1 (raw=1) attempt_2=not_attempted/None (raw=None)
  mount of venus: outcome=success_first attempt_1=validated/1 (raw=1) attempt_2=not_attempted/None (raw=None)
  sun line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  thumb: outcome=success_first attempt_1=validated/1 (raw=1) attempt_2=not_attempted/None (raw=None)
stage2_retry_used: True
stage2_first_attempt_failures: jargon_blacklist: found dignity
validation_failures: NONE
ring1_failures:
none

### near_miss_margin
  fate line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p165_c0, 0.4942), (2, cheiroslanguageo00chei_1_p165_c1, 0.4942), (3, cheiroslanguageo00chei_1_p163_c0, 0.4729), (4, cheiroslanguageo00chei_1_p163_c1, 0.4647), (5, cheiroslanguageo00chei_1_p162_c0, 0.4627), (6, cheiroslanguageo00chei_1_p165_c2, 0.4581), (7, cheiroslanguageo00chei_1_p162_c1, 0.4441), (8, cheiroslanguageo00chei_1_p163_c2, 0.4434), (9, cheiroslanguageo00chei_1_p164_c1, 0.4393), (10, cheiroslanguageo00chei_1_p164_c2, 0.4246), (11, cheiroslanguageo00chei_1_p162_c2, 0.3781), (12, cheiroslanguageo00chei_1_p164_c0, 0.3628), (13, cheiroslanguageo00chei_1_p163_c3, 0.3584), (14, cheiroslanguageo00chei_1_p164_c3, 0.3241)]
  fingers: window=3 candidates=[(1, cheiroslanguageo00chei_1_p96_c0, 0.5251), (2, cheiroslanguageo00chei_1_p95_c0, 0.5194), (3, cheiroslanguageo00chei_1_p96_c1, 0.5125), (4, cheiroslanguageo00chei_1_p96_c2, 0.5067), (5, cheiroslanguageo00chei_1_p96_c3, 0.4959), (6, cheiroslanguageo00chei_1_p97_c0, 0.4891), (7, cheiroslanguageo00chei_1_p95_c1, 0.4731), (8, cheiroslanguageo00chei_1_p95_c2, 0.454), (9, cheiroslanguageo00chei_1_p93_c0, 0.3873), (10, cheiroslanguageo00chei_1_p94_c0, 0.3361), (11, cheiroslanguageo00chei_1_p93_c1, 0.2583)]
  head line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p151_c2, 0.5898), (2, cheiroslanguageo00chei_1_p146_c2, 0.5705), (3, cheiroslanguageo00chei_1_p147_c0, 0.5485), (4, cheiroslanguageo00chei_1_p148_c0, 0.5455), (5, cheiroslanguageo00chei_1_p147_c1, 0.5454), (6, cheiroslanguageo00chei_1_p145_c0, 0.5318), (7, cheiroslanguageo00chei_1_p150_c1, 0.5289), (8, cheiroslanguageo00chei_1_p150_c0, 0.5251), (9, cheiroslanguageo00chei_1_p150_c2, 0.5232), (10, cheiroslanguageo00chei_1_p148_c1, 0.5158), (11, cheiroslanguageo00chei_1_p151_c1, 0.4978), (12, cheiroslanguageo00chei_1_p153_c1, 0.4861), (13, cheiroslanguageo00chei_1_p146_c1, 0.4792), (14, cheiroslanguageo00chei_1_p149_c0, 0.478), (15, cheiroslanguageo00chei_1_p146_c0, 0.4774), (16, cheiroslanguageo00chei_1_p154_c1, 0.4716), (17, cheiroslanguageo00chei_1_p145_c1, 0.4464), (18, cheiroslanguageo00chei_1_p154_c0, 0.4383), (19, cheiroslanguageo00chei_1_p147_c3, 0.4375), (20, cheiroslanguageo00chei_1_p147_c2, 0.4348), (21, cheiroslanguageo00chei_1_p151_c0, 0.4336), (22, cheiroslanguageo00chei_1_p152_c0, 0.4326), (23, cheiroslanguageo00chei_1_p155_c1, 0.4169), (24, cheiroslanguageo00chei_1_p153_c0, 0.4109), (25, cheiroslanguageo00chei_1_p148_c2, 0.4016), (26, cheiroslanguageo00chei_1_p152_c1, 0.396), (27, cheiroslanguageo00chei_1_p149_c1, 0.3828), (28, cheiroslanguageo00chei_1_p155_c0, 0.3773), (29, cheiroslanguageo00chei_1_p145_c2, 0.3031), (30, cheiroslanguageo00chei_1_p153_c2, 0.2734)]
  heart line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p159_c3, 0.6088), (2, cheiroslanguageo00chei_1_p160_c2, 0.6068), (3, cheiroslanguageo00chei_1_p161_c0, 0.5971), (4, cheiroslanguageo00chei_1_p156_c0, 0.5776), (5, cheiroslanguageo00chei_1_p159_c2, 0.5636), (6, cheiroslanguageo00chei_1_p160_c1, 0.5296), (7, cheiroslanguageo00chei_1_p156_c1, 0.5056), (8, cheiroslanguageo00chei_1_p160_c3, 0.4811), (9, cheiroslanguageo00chei_1_p160_c0, 0.4394), (10, cheiroslanguageo00chei_1_p159_c1, 0.4259), (11, cheiroslanguageo00chei_1_p159_c0, 0.3718), (12, cheiroslanguageo00chei_1_p156_c2, 0.3352)]
  life line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p135_c0, 0.6131), (2, cheiroslanguageo00chei_1_p134_c1, 0.6063), (3, cheiroslanguageo00chei_1_p134_c0, 0.5725), (4, cheiroslanguageo00chei_1_p139_c0, 0.5671), (5, cheiroslanguageo00chei_1_p134_c2, 0.5658), (6, cheiroslanguageo00chei_1_p135_c2, 0.5581), (7, cheiroslanguageo00chei_1_p137_c1, 0.549), (8, cheiroslanguageo00chei_1_p139_c1, 0.5284), (9, cheiroslanguageo00chei_1_p133_c0, 0.5127), (10, cheiroslanguageo00chei_1_p136_c1, 0.5118), (11, cheiroslanguageo00chei_1_p138_c1, 0.4932), (12, cheiroslanguageo00chei_1_p135_c1, 0.491), (13, cheiroslanguageo00chei_1_p136_c3, 0.4897), (14, cheiroslanguageo00chei_1_p138_c0, 0.4893), (15, cheiroslanguageo00chei_1_p137_c0, 0.4793), (16, cheiroslanguageo00chei_1_p136_c2, 0.477), (17, cheiroslanguageo00chei_1_p138_c2, 0.4729), (18, cheiroslanguageo00chei_1_p136_c0, 0.4343), (19, cheiroslanguageo00chei_1_p137_c3, 0.4239), (20, cheiroslanguageo00chei_1_p137_c2, 0.4186), (21, cheiroslanguageo00chei_1_p134_c3, 0.3493), (22, cheiroslanguageo00chei_1_p133_c1, 0.1715), (23, cheiroslanguageo00chei_1_p139_c2, 0.1118)]
  mount of jupiter: window=3 candidates=[(1, cheiroslanguageo00chei_1_p112_c0, 0.6517), (2, cheiroslanguageo00chei_1_p111_c1, 0.6345), (3, cheiroslanguageo00chei_1_p113_c0, 0.5853), (4, cheiroslanguageo00chei_1_p111_c0, 0.5578), (5, cheiroslanguageo00chei_1_p112_c1, 0.5397), (6, cheiroslanguageo00chei_1_p112_c2, 0.536), (7, cheiroslanguageo00chei_1_p113_c1, 0.4451)]
  mount of venus: window=3 candidates=[(1, cheiroslanguageo00chei_1_p112_c0, 0.6725), (2, cheiroslanguageo00chei_1_p111_c1, 0.6631), (3, cheiroslanguageo00chei_1_p111_c0, 0.5547), (4, cheiroslanguageo00chei_1_p113_c0, 0.5524), (5, cheiroslanguageo00chei_1_p112_c1, 0.5329), (6, cheiroslanguageo00chei_1_p112_c2, 0.5076), (7, cheiroslanguageo00chei_1_p113_c1, 0.445)]
  thumb: window=3 candidates=[(1, cheiroslanguageo00chei_1_p87_c0, 0.5199), (2, cheiroslanguageo00chei_1_p88_c1, 0.516), (3, cheiroslanguageo00chei_1_p89_c2, 0.5075), (4, cheiroslanguageo00chei_1_p88_c0, 0.5039), (5, cheiroslanguageo00chei_1_p89_c0, 0.4775), (6, cheiroslanguageo00chei_1_p86_c0, 0.4433), (7, cheiroslanguageo00chei_1_p85_c0, 0.4309), (8, cheiroslanguageo00chei_1_p90_c2, 0.4224), (9, cheiroslanguageo00chei_1_p90_c0, 0.3773), (10, cheiroslanguageo00chei_1_p85_c1, 0.3652), (11, cheiroslanguageo00chei_1_p88_c2, 0.3505), (12, cheiroslanguageo00chei_1_p89_c1, 0.3043), (13, cheiroslanguageo00chei_1_p90_c1, 0.2923), (14, cheiroslanguageo00chei_1_p87_c1, 0.0929)]

## RUN 2026-08-04T09:04:25.719130

### capture_reason
instability, silence

### Confirmed descriptions
#### LEFT
HAND SHAPE: Square palm, overall build is medium.

FINGERS: Fingers are long relative to the palm, appear straight, fingertips are rounded, spacing is moderate.

THUMB: Medium relative size, set moderately low, wide angle from the palm.

LIFE LINE: Present, deep, long, curves around the base of the thumb, no breaks, chains, forks, or islands visible.

HEAD LINE: Present, deep, long, slightly curved, no breaks, chains, forks, or islands visible.

HEART LINE: Present, deep, long, slightly curved, no breaks, chains, forks, or islands visible.

FATE LINE: Barely visible.

OTHER LINES: No other lines clearly visible.

MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.

MARKS: No marks clearly visible.
#### RIGHT
HAND SHAPE: elongated palm, medium build

FINGERS: medium length relative to palm, straight, rounded fingertips, moderate spacing

THUMB: medium size, low set, wide angle from the palm

LIFE LINE: present, deep, long, curves around the base of the thumb, no clear breaks or forks

HEAD LINE: present, deep, long, slightly curved, no clear breaks or forks

HEART LINE: present, deep, long, curves slightly upward, no clear breaks or forks

FATE LINE: present, moderately deep, runs from the base towards the middle of the palm, no clear breaks or forks

OTHER LINES: not clearly visible

MOUNTS: mount of Venus appears developed, other mounts not clearly visible

MARKS: not clearly visible

### reading_text
The line of life on your palm is long, narrow, and deep, curving gracefully around the base of your thumb without any irregularities such as breaks, chains, forks, or islands. This formation promises you a long life, accompanied by good health and vitality.

Your thumb is of medium size, set moderately low, and extends at a wide angle from the palm. This indicates a nature that is independent and not easily managed or controlled by others.

The Mount of Venus on your palm is well-developed. This suggests that you possess strong and robust health.

The head line is present, deep, long, and slightly curved, with no visible breaks or forks. Similarly, the heart line is deep, long, and slightly curved, with no interruptions. The fate line, though barely visible, runs from the base towards the middle of the palm without clear breaks or forks.

Your fingers are long relative to the palm, straight, with rounded fingertips and moderate spacing. There are no other marks clearly visible on your palm.

A note on what I have not interpreted: the classical texts I work from do not clearly address the following as they appear in your hands: head line, heart line, fate line, sun line, fingers, mount of jupiter. Rather than guess, I have left these out of your reading.

For major life decisions, I recommend consulting a qualified astrologer or palm reader for a personal reading.

### READING (TAGGED)
The line of life on your palm is long, narrow, and deep, curving gracefully around the base of your thumb without any irregularities such as breaks, chains, forks, or islands. [OBS] This formation promises you a long life, accompanied by good health and vitality. [C1]

Your thumb is of medium size, set moderately low, and extends at a wide angle from the palm. [OBS] This indicates a nature that is independent and not easily managed or controlled by others. [C3]

The Mount of Venus on your palm is well-developed. [OBS] This suggests that you possess strong and robust health. [C4]

The head line is present, deep, long, and slightly curved, with no visible breaks or forks. [OBS] Similarly, the heart line is deep, long, and slightly curved, with no interruptions. [OBS] The fate line, though barely visible, runs from the base towards the middle of the palm without clear breaks or forks. [OBS]

Your fingers are long relative to the palm, straight, with rounded fingertips and moderate spacing. [OBS] There are no other marks clearly visible on your palm. [OBS]

### sources
- cheiroslanguageo00chei_1, p.134 (score: 0.5775, feature: life line)
- cheiroslanguageo00chei_1, p.87 (score: 0.5078, feature: thumb)
- cheiroslanguageo00chei_1, p.112 (score: 0.6181, feature: mount of venus)

### feature_support
supported_features: ('life line', 'head line', 'heart line', 'fate line', 'thumb', 'fingers', 'mount of venus')
unsupported_features: ('sun line', 'mount of jupiter')

### claims_inventory
C1 | life line | cheiroslanguageo00chei_1_p134_c1 | supports | False | None | None | A long, narrow, and deep line of life without irregularities promises long life, good health, and vitality.
C2 | head line | cheiroslanguageo00chei_1_p145_c0 | supports | True | disjunctive-taxonomy (S71):S1:antonym-pair | None | The line of head relates principally to the mentality of the subject, including intellectual strength or weakness and the direction and quality of talent.
C3 | thumb | cheiroslanguageo00chei_1_p87_c0 | supports | False | None | None | A well-formed thumb that is not too close to the side or at right angles to the palm indicates a nature that is independent and not easily managed or controlled.
C4 | mount of venus | cheiroslanguageo00chei_1_p112_c0 | supports | False | None | None | A well-developed Mount of Venus indicates strong and robust health.

### ring1_validation
passed: True
failures: ()
retry_used: True
stage1_retry_features: thumb
stage1_feature_diagnostics:
  fate line: outcome=empty_first attempt_1=validated_empty/0 (raw=0) attempt_2=not_attempted/None (raw=None)
  fingers: outcome=empty_first attempt_1=validated_empty/0 (raw=0) attempt_2=not_attempted/None (raw=None)
  head line: outcome=success_first attempt_1=validated/1 (raw=1) attempt_2=not_attempted/None (raw=None)
  heart line: outcome=empty_first attempt_1=validated_empty/0 (raw=0) attempt_2=not_attempted/None (raw=None)
  life line: outcome=success_first attempt_1=validated/1 (raw=1) attempt_2=not_attempted/None (raw=None)
  markings/other features: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of jupiter: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of venus: outcome=success_first attempt_1=validated/1 (raw=1) attempt_2=not_attempted/None (raw=None)
  sun line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  thumb: outcome=success_retry attempt_1=validation_failed/0 (raw=1) attempt_2=validated/1 (raw=1)
    attempt_1_failures: claims[0] claim_text overlap 0.22 below floor 0.4 for chunk 'cheiroslanguageo00chei_1_p88_c0'
stage2_retry_used: False
stage2_first_attempt_failures: NONE
validation_failures: NONE
ring1_failures:
none

### near_miss_margin
  fate line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p165_c1, 0.5958), (2, cheiroslanguageo00chei_1_p163_c1, 0.5942), (3, cheiroslanguageo00chei_1_p165_c0, 0.5739), (4, cheiroslanguageo00chei_1_p163_c2, 0.5651), (5, cheiroslanguageo00chei_1_p163_c0, 0.5482), (6, cheiroslanguageo00chei_1_p164_c1, 0.547), (7, cheiroslanguageo00chei_1_p162_c0, 0.5379), (8, cheiroslanguageo00chei_1_p164_c2, 0.5338), (9, cheiroslanguageo00chei_1_p162_c1, 0.5168), (10, cheiroslanguageo00chei_1_p164_c0, 0.4946), (11, cheiroslanguageo00chei_1_p163_c3, 0.4767), (12, cheiroslanguageo00chei_1_p165_c2, 0.4553), (13, cheiroslanguageo00chei_1_p164_c3, 0.4512), (14, cheiroslanguageo00chei_1_p162_c2, 0.3662)]
  fingers: window=3 candidates=[(1, cheiroslanguageo00chei_1_p96_c0, 0.5164), (2, cheiroslanguageo00chei_1_p96_c2, 0.5117), (3, cheiroslanguageo00chei_1_p96_c1, 0.51), (4, cheiroslanguageo00chei_1_p95_c0, 0.4715), (5, cheiroslanguageo00chei_1_p97_c0, 0.4659), (6, cheiroslanguageo00chei_1_p96_c3, 0.4656), (7, cheiroslanguageo00chei_1_p95_c2, 0.447), (8, cheiroslanguageo00chei_1_p95_c1, 0.4451), (9, cheiroslanguageo00chei_1_p93_c0, 0.3858), (10, cheiroslanguageo00chei_1_p94_c0, 0.3716), (11, cheiroslanguageo00chei_1_p93_c1, 0.2714)]
  head line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p145_c0, 0.5589), (2, cheiroslanguageo00chei_1_p147_c1, 0.526), (3, cheiroslanguageo00chei_1_p151_c2, 0.5226), (4, cheiroslanguageo00chei_1_p147_c0, 0.5066), (5, cheiroslanguageo00chei_1_p148_c1, 0.4943), (6, cheiroslanguageo00chei_1_p148_c0, 0.4909), (7, cheiroslanguageo00chei_1_p150_c2, 0.4888), (8, cheiroslanguageo00chei_1_p147_c3, 0.4814), (9, cheiroslanguageo00chei_1_p151_c1, 0.4715), (10, cheiroslanguageo00chei_1_p149_c0, 0.4706), (11, cheiroslanguageo00chei_1_p153_c1, 0.4687), (12, cheiroslanguageo00chei_1_p150_c0, 0.4672), (13, cheiroslanguageo00chei_1_p150_c1, 0.4557), (14, cheiroslanguageo00chei_1_p146_c1, 0.4521), (15, cheiroslanguageo00chei_1_p154_c0, 0.4489), (16, cheiroslanguageo00chei_1_p148_c2, 0.4464), (17, cheiroslanguageo00chei_1_p146_c0, 0.4423), (18, cheiroslanguageo00chei_1_p146_c2, 0.4209), (19, cheiroslanguageo00chei_1_p149_c1, 0.4114), (20, cheiroslanguageo00chei_1_p153_c0, 0.4093), (21, cheiroslanguageo00chei_1_p145_c1, 0.4086), (22, cheiroslanguageo00chei_1_p147_c2, 0.3982), (23, cheiroslanguageo00chei_1_p154_c1, 0.3921), (24, cheiroslanguageo00chei_1_p155_c0, 0.3907), (25, cheiroslanguageo00chei_1_p151_c0, 0.389), (26, cheiroslanguageo00chei_1_p152_c1, 0.3724), (27, cheiroslanguageo00chei_1_p152_c0, 0.3553), (28, cheiroslanguageo00chei_1_p155_c1, 0.3123), (29, cheiroslanguageo00chei_1_p145_c2, 0.2804), (30, cheiroslanguageo00chei_1_p153_c2, 0.1865)]
  heart line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p160_c2, 0.6427), (2, cheiroslanguageo00chei_1_p161_c0, 0.6188), (3, cheiroslanguageo00chei_1_p159_c2, 0.6061), (4, cheiroslanguageo00chei_1_p159_c3, 0.6054), (5, cheiroslanguageo00chei_1_p156_c0, 0.5884), (6, cheiroslanguageo00chei_1_p160_c1, 0.557), (7, cheiroslanguageo00chei_1_p156_c1, 0.5494), (8, cheiroslanguageo00chei_1_p160_c3, 0.522), (9, cheiroslanguageo00chei_1_p160_c0, 0.4791), (10, cheiroslanguageo00chei_1_p159_c1, 0.4751), (11, cheiroslanguageo00chei_1_p159_c0, 0.3856), (12, cheiroslanguageo00chei_1_p156_c2, 0.3415)]
  life line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p139_c0, 0.6108), (2, cheiroslanguageo00chei_1_p134_c2, 0.5801), (3, cheiroslanguageo00chei_1_p134_c1, 0.5775), (4, cheiroslanguageo00chei_1_p135_c0, 0.5652), (5, cheiroslanguageo00chei_1_p139_c1, 0.5552), (6, cheiroslanguageo00chei_1_p138_c1, 0.5406), (7, cheiroslanguageo00chei_1_p135_c2, 0.5394), (8, cheiroslanguageo00chei_1_p136_c1, 0.5337), (9, cheiroslanguageo00chei_1_p136_c3, 0.5332), (10, cheiroslanguageo00chei_1_p134_c0, 0.5317), (11, cheiroslanguageo00chei_1_p135_c1, 0.5253), (12, cheiroslanguageo00chei_1_p137_c1, 0.5195), (13, cheiroslanguageo00chei_1_p136_c2, 0.5054), (14, cheiroslanguageo00chei_1_p137_c0, 0.5013), (15, cheiroslanguageo00chei_1_p138_c2, 0.4935), (16, cheiroslanguageo00chei_1_p138_c0, 0.466), (17, cheiroslanguageo00chei_1_p137_c3, 0.4625), (18, cheiroslanguageo00chei_1_p133_c0, 0.4477), (19, cheiroslanguageo00chei_1_p137_c2, 0.4165), (20, cheiroslanguageo00chei_1_p134_c3, 0.399), (21, cheiroslanguageo00chei_1_p136_c0, 0.3986), (22, cheiroslanguageo00chei_1_p133_c1, 0.177), (23, cheiroslanguageo00chei_1_p139_c2, 0.0862)]
  mount of venus: window=3 candidates=[(1, cheiroslanguageo00chei_1_p111_c1, 0.652), (2, cheiroslanguageo00chei_1_p112_c0, 0.6181), (3, cheiroslanguageo00chei_1_p113_c0, 0.497), (4, cheiroslanguageo00chei_1_p111_c0, 0.4856), (5, cheiroslanguageo00chei_1_p112_c1, 0.4774), (6, cheiroslanguageo00chei_1_p113_c1, 0.4747), (7, cheiroslanguageo00chei_1_p112_c2, 0.4245)]
  thumb: window=3 candidates=[(1, cheiroslanguageo00chei_1_p88_c0, 0.5104), (2, cheiroslanguageo00chei_1_p87_c0, 0.5078), (3, cheiroslanguageo00chei_1_p88_c1, 0.5041), (4, cheiroslanguageo00chei_1_p89_c2, 0.5035), (5, cheiroslanguageo00chei_1_p89_c0, 0.4813), (6, cheiroslanguageo00chei_1_p86_c0, 0.4576), (7, cheiroslanguageo00chei_1_p85_c0, 0.4479), (8, cheiroslanguageo00chei_1_p90_c2, 0.426), (9, cheiroslanguageo00chei_1_p90_c0, 0.3723), (10, cheiroslanguageo00chei_1_p88_c2, 0.3636), (11, cheiroslanguageo00chei_1_p85_c1, 0.3588), (12, cheiroslanguageo00chei_1_p89_c1, 0.2875), (13, cheiroslanguageo00chei_1_p90_c1, 0.2682), (14, cheiroslanguageo00chei_1_p87_c1, 0.0836)]

## RUN 2026-08-04T10:12:14.269295

### capture_reason
silence

### Confirmed descriptions
#### LEFT
HAND SHAPE: Square palm, overall build is medium.

FINGERS: Fingers are long relative to the palm, appear straight, fingertips are rounded, spacing is moderate.

THUMB: Medium size, set moderately low, wide angle from the palm.

LIFE LINE: Present, deep, long, curves around the base of the thumb, no clear breaks, chains, forks, or islands visible.

HEAD LINE: Present, deep, long, slightly curved, no clear breaks, chains, forks, or islands visible.

HEART LINE: Present, deep, long, slightly curved, no clear breaks, chains, forks, or islands visible.

FATE LINE: Barely visible.

OTHER LINES: No other lines clearly visible.

MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.

MARKS: No marks clearly visible.
#### RIGHT
HAND SHAPE: Square palm, overall build is medium.
FINGERS: Fingers are slightly longer than the palm, appear straight, with rounded fingertips, spaced moderately apart.
THUMB: Medium size, set moderately low, wide angle from the palm.
LIFE LINE: Present, deep, long, curves around the base of the thumb, no clear breaks or forks.
HEAD LINE: Present, deep, long, slightly curved, starts joined with the life line.
HEART LINE: Present, deep, curves slightly upward, ends below the index finger.
FATE LINE: Present, moderately deep, starts from the base of the palm and runs towards the middle finger.
OTHER LINES: Sun line is not clearly visible; health and marriage lines not clearly visible.
MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.
MARKS: No clear marks such as crosses, stars, grilles, squares, or moles visible.

### reading_text


A note on what I have not interpreted: the classical texts I work from do not clearly address the following as they appear in your hands: life line, head line, heart line, fate line, thumb, fingers, mount of venus, mount of jupiter. Rather than guess, I have left these out of your reading.

For major life decisions, I recommend consulting a qualified astrologer or palm reader for a personal reading.

### READING (TAGGED)


### sources

### feature_support
supported_features: ('life line', 'head line', 'heart line', 'fate line', 'thumb', 'fingers', 'mount of venus')
unsupported_features: ('mount of jupiter',)

### claims_inventory
claims_inventory: EMPTY

### ring1_validation
passed: True
failures: ()
retry_used: False
stage1_retry_features: NONE
stage1_feature_diagnostics:
  _rules_engine: outcome=rules_engine_ok attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  fate line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  fingers: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  head line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  heart line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  life line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  markings/other features: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of jupiter: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of venus: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  sun line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  thumb: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
stage2_retry_used: False
stage2_first_attempt_failures: NONE
validation_failures: NONE
ring1_failures:
none

### near_miss_margin
  fate line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p165_c1, 0.5958), (2, cheiroslanguageo00chei_1_p163_c1, 0.5942), (3, cheiroslanguageo00chei_1_p165_c0, 0.5739), (4, cheiroslanguageo00chei_1_p163_c2, 0.5651), (5, cheiroslanguageo00chei_1_p163_c0, 0.5482), (6, cheiroslanguageo00chei_1_p164_c1, 0.547), (7, cheiroslanguageo00chei_1_p162_c0, 0.5379), (8, cheiroslanguageo00chei_1_p164_c2, 0.5338), (9, cheiroslanguageo00chei_1_p162_c1, 0.5168), (10, cheiroslanguageo00chei_1_p164_c0, 0.4946), (11, cheiroslanguageo00chei_1_p163_c3, 0.4767), (12, cheiroslanguageo00chei_1_p165_c2, 0.4553), (13, cheiroslanguageo00chei_1_p164_c3, 0.4512), (14, cheiroslanguageo00chei_1_p162_c2, 0.3662)]
  fingers: window=3 candidates=[(1, cheiroslanguageo00chei_1_p96_c1, 0.5429), (2, cheiroslanguageo00chei_1_p96_c2, 0.5211), (3, cheiroslanguageo00chei_1_p96_c0, 0.5149), (4, cheiroslanguageo00chei_1_p95_c0, 0.4914), (5, cheiroslanguageo00chei_1_p96_c3, 0.4858), (6, cheiroslanguageo00chei_1_p97_c0, 0.4792), (7, cheiroslanguageo00chei_1_p95_c1, 0.4633), (8, cheiroslanguageo00chei_1_p95_c2, 0.4456), (9, cheiroslanguageo00chei_1_p93_c0, 0.3963), (10, cheiroslanguageo00chei_1_p94_c0, 0.3773), (11, cheiroslanguageo00chei_1_p93_c1, 0.285)]
  head line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p145_c0, 0.5589), (2, cheiroslanguageo00chei_1_p147_c1, 0.526), (3, cheiroslanguageo00chei_1_p151_c2, 0.5226), (4, cheiroslanguageo00chei_1_p147_c0, 0.5066), (5, cheiroslanguageo00chei_1_p148_c1, 0.4943), (6, cheiroslanguageo00chei_1_p148_c0, 0.4909), (7, cheiroslanguageo00chei_1_p150_c2, 0.4888), (8, cheiroslanguageo00chei_1_p147_c3, 0.4814), (9, cheiroslanguageo00chei_1_p151_c1, 0.4715), (10, cheiroslanguageo00chei_1_p149_c0, 0.4706), (11, cheiroslanguageo00chei_1_p153_c1, 0.4687), (12, cheiroslanguageo00chei_1_p150_c0, 0.4672), (13, cheiroslanguageo00chei_1_p150_c1, 0.4557), (14, cheiroslanguageo00chei_1_p146_c1, 0.4521), (15, cheiroslanguageo00chei_1_p154_c0, 0.4489), (16, cheiroslanguageo00chei_1_p148_c2, 0.4464), (17, cheiroslanguageo00chei_1_p146_c0, 0.4423), (18, cheiroslanguageo00chei_1_p146_c2, 0.4209), (19, cheiroslanguageo00chei_1_p149_c1, 0.4114), (20, cheiroslanguageo00chei_1_p153_c0, 0.4093), (21, cheiroslanguageo00chei_1_p145_c1, 0.4086), (22, cheiroslanguageo00chei_1_p147_c2, 0.3982), (23, cheiroslanguageo00chei_1_p154_c1, 0.3921), (24, cheiroslanguageo00chei_1_p155_c0, 0.3907), (25, cheiroslanguageo00chei_1_p151_c0, 0.389), (26, cheiroslanguageo00chei_1_p152_c1, 0.3724), (27, cheiroslanguageo00chei_1_p152_c0, 0.3553), (28, cheiroslanguageo00chei_1_p155_c1, 0.3123), (29, cheiroslanguageo00chei_1_p145_c2, 0.2804), (30, cheiroslanguageo00chei_1_p153_c2, 0.1865)]
  heart line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p160_c2, 0.6427), (2, cheiroslanguageo00chei_1_p161_c0, 0.6188), (3, cheiroslanguageo00chei_1_p159_c2, 0.6061), (4, cheiroslanguageo00chei_1_p159_c3, 0.6054), (5, cheiroslanguageo00chei_1_p156_c0, 0.5884), (6, cheiroslanguageo00chei_1_p160_c1, 0.557), (7, cheiroslanguageo00chei_1_p156_c1, 0.5494), (8, cheiroslanguageo00chei_1_p160_c3, 0.522), (9, cheiroslanguageo00chei_1_p160_c0, 0.4791), (10, cheiroslanguageo00chei_1_p159_c1, 0.4751), (11, cheiroslanguageo00chei_1_p159_c0, 0.3856), (12, cheiroslanguageo00chei_1_p156_c2, 0.3415)]
  life line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p139_c0, 0.6107), (2, cheiroslanguageo00chei_1_p134_c2, 0.58), (3, cheiroslanguageo00chei_1_p134_c1, 0.5774), (4, cheiroslanguageo00chei_1_p135_c0, 0.5651), (5, cheiroslanguageo00chei_1_p139_c1, 0.5551), (6, cheiroslanguageo00chei_1_p138_c1, 0.5405), (7, cheiroslanguageo00chei_1_p135_c2, 0.5393), (8, cheiroslanguageo00chei_1_p136_c1, 0.5336), (9, cheiroslanguageo00chei_1_p136_c3, 0.5332), (10, cheiroslanguageo00chei_1_p134_c0, 0.5316), (11, cheiroslanguageo00chei_1_p135_c1, 0.5252), (12, cheiroslanguageo00chei_1_p137_c1, 0.5194), (13, cheiroslanguageo00chei_1_p136_c2, 0.5053), (14, cheiroslanguageo00chei_1_p137_c0, 0.5012), (15, cheiroslanguageo00chei_1_p138_c2, 0.4934), (16, cheiroslanguageo00chei_1_p138_c0, 0.4659), (17, cheiroslanguageo00chei_1_p137_c3, 0.4624), (18, cheiroslanguageo00chei_1_p133_c0, 0.4477), (19, cheiroslanguageo00chei_1_p137_c2, 0.4165), (20, cheiroslanguageo00chei_1_p134_c3, 0.3989), (21, cheiroslanguageo00chei_1_p136_c0, 0.3985), (22, cheiroslanguageo00chei_1_p133_c1, 0.177), (23, cheiroslanguageo00chei_1_p139_c2, 0.0862)]
  mount of venus: window=3 candidates=[(1, cheiroslanguageo00chei_1_p111_c1, 0.652), (2, cheiroslanguageo00chei_1_p112_c0, 0.6181), (3, cheiroslanguageo00chei_1_p113_c0, 0.497), (4, cheiroslanguageo00chei_1_p111_c0, 0.4856), (5, cheiroslanguageo00chei_1_p112_c1, 0.4774), (6, cheiroslanguageo00chei_1_p113_c1, 0.4747), (7, cheiroslanguageo00chei_1_p112_c2, 0.4245)]
  thumb: window=3 candidates=[(1, cheiroslanguageo00chei_1_p88_c0, 0.5569), (2, cheiroslanguageo00chei_1_p87_c0, 0.5513), (3, cheiroslanguageo00chei_1_p88_c1, 0.5327), (4, cheiroslanguageo00chei_1_p89_c2, 0.5322), (5, cheiroslanguageo00chei_1_p89_c0, 0.5226), (6, cheiroslanguageo00chei_1_p85_c0, 0.5033), (7, cheiroslanguageo00chei_1_p86_c0, 0.4837), (8, cheiroslanguageo00chei_1_p90_c2, 0.4443), (9, cheiroslanguageo00chei_1_p85_c1, 0.4043), (10, cheiroslanguageo00chei_1_p88_c2, 0.3724), (11, cheiroslanguageo00chei_1_p90_c0, 0.3615), (12, cheiroslanguageo00chei_1_p89_c1, 0.305), (13, cheiroslanguageo00chei_1_p90_c1, 0.2905), (14, cheiroslanguageo00chei_1_p87_c1, 0.0692)]

## RUN 2026-08-04T10:12:54.721277

### capture_reason
silence

### Confirmed descriptions
#### LEFT
HAND SHAPE: Square palm, overall build is medium.

FINGERS: Fingers are long relative to the palm, appear straight, fingertips are rounded, spacing is moderate.

THUMB: Medium size, set moderately low, wide angle from the palm.

LIFE LINE: Present, deep, long, curves around the base of the thumb, no clear breaks, chains, forks, or islands visible.

HEAD LINE: Present, deep, long, slightly curved, no clear breaks, chains, forks, or islands visible.

HEART LINE: Present, deep, long, slightly curved, no clear breaks, chains, forks, or islands visible.

FATE LINE: Barely visible.

OTHER LINES: No other lines clearly visible.

MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.

MARKS: No marks clearly visible.
#### RIGHT
HAND SHAPE: Square palm, overall build is medium.
FINGERS: Fingers are slightly longer than the palm, appear straight, with rounded fingertips, spaced moderately apart.
THUMB: Medium size, set moderately low, wide angle from the palm.
LIFE LINE: Present, deep, long, curves around the base of the thumb, no clear breaks or forks.
HEAD LINE: Present, deep, long, slightly curved, starts joined with the life line.
HEART LINE: Present, deep, curves slightly upward, ends below the index finger.
FATE LINE: Present, moderately deep, starts from the base of the palm and runs towards the middle finger.
OTHER LINES: Sun line is not clearly visible; health and marriage lines not clearly visible.
MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.
MARKS: No clear marks such as crosses, stars, grilles, squares, or moles visible.

### reading_text


A note on what I have not interpreted: the classical texts I work from do not clearly address the following as they appear in your hands: life line, head line, heart line, fate line, thumb, fingers, mount of venus, mount of jupiter. Rather than guess, I have left these out of your reading.

For major life decisions, I recommend consulting a qualified astrologer or palm reader for a personal reading.

### READING (TAGGED)


### sources

### feature_support
supported_features: ('life line', 'head line', 'heart line', 'fate line', 'thumb', 'fingers', 'mount of venus')
unsupported_features: ('mount of jupiter',)

### claims_inventory
claims_inventory: EMPTY

### ring1_validation
passed: True
failures: ()
retry_used: False
stage1_retry_features: NONE
stage1_feature_diagnostics:
  _rules_engine: outcome=rules_engine_ok attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  fate line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  fingers: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  head line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  heart line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  life line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  markings/other features: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of jupiter: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of venus: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  sun line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  thumb: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
stage2_retry_used: False
stage2_first_attempt_failures: NONE
validation_failures: NONE
ring1_failures:
none

### near_miss_margin
  fate line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p165_c1, 0.5958), (2, cheiroslanguageo00chei_1_p163_c1, 0.5942), (3, cheiroslanguageo00chei_1_p165_c0, 0.5739), (4, cheiroslanguageo00chei_1_p163_c2, 0.5651), (5, cheiroslanguageo00chei_1_p163_c0, 0.5482), (6, cheiroslanguageo00chei_1_p164_c1, 0.547), (7, cheiroslanguageo00chei_1_p162_c0, 0.5379), (8, cheiroslanguageo00chei_1_p164_c2, 0.5338), (9, cheiroslanguageo00chei_1_p162_c1, 0.5168), (10, cheiroslanguageo00chei_1_p164_c0, 0.4946), (11, cheiroslanguageo00chei_1_p163_c3, 0.4767), (12, cheiroslanguageo00chei_1_p165_c2, 0.4553), (13, cheiroslanguageo00chei_1_p164_c3, 0.4512), (14, cheiroslanguageo00chei_1_p162_c2, 0.3662)]
  fingers: window=3 candidates=[(1, cheiroslanguageo00chei_1_p96_c1, 0.5429), (2, cheiroslanguageo00chei_1_p96_c2, 0.5211), (3, cheiroslanguageo00chei_1_p96_c0, 0.5149), (4, cheiroslanguageo00chei_1_p95_c0, 0.4914), (5, cheiroslanguageo00chei_1_p96_c3, 0.4858), (6, cheiroslanguageo00chei_1_p97_c0, 0.4792), (7, cheiroslanguageo00chei_1_p95_c1, 0.4633), (8, cheiroslanguageo00chei_1_p95_c2, 0.4456), (9, cheiroslanguageo00chei_1_p93_c0, 0.3963), (10, cheiroslanguageo00chei_1_p94_c0, 0.3773), (11, cheiroslanguageo00chei_1_p93_c1, 0.285)]
  head line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p145_c0, 0.5589), (2, cheiroslanguageo00chei_1_p147_c1, 0.526), (3, cheiroslanguageo00chei_1_p151_c2, 0.5226), (4, cheiroslanguageo00chei_1_p147_c0, 0.5066), (5, cheiroslanguageo00chei_1_p148_c1, 0.4943), (6, cheiroslanguageo00chei_1_p148_c0, 0.4909), (7, cheiroslanguageo00chei_1_p150_c2, 0.4888), (8, cheiroslanguageo00chei_1_p147_c3, 0.4814), (9, cheiroslanguageo00chei_1_p151_c1, 0.4715), (10, cheiroslanguageo00chei_1_p149_c0, 0.4706), (11, cheiroslanguageo00chei_1_p153_c1, 0.4687), (12, cheiroslanguageo00chei_1_p150_c0, 0.4672), (13, cheiroslanguageo00chei_1_p150_c1, 0.4557), (14, cheiroslanguageo00chei_1_p146_c1, 0.4521), (15, cheiroslanguageo00chei_1_p154_c0, 0.4489), (16, cheiroslanguageo00chei_1_p148_c2, 0.4464), (17, cheiroslanguageo00chei_1_p146_c0, 0.4423), (18, cheiroslanguageo00chei_1_p146_c2, 0.4209), (19, cheiroslanguageo00chei_1_p149_c1, 0.4114), (20, cheiroslanguageo00chei_1_p153_c0, 0.4093), (21, cheiroslanguageo00chei_1_p145_c1, 0.4086), (22, cheiroslanguageo00chei_1_p147_c2, 0.3982), (23, cheiroslanguageo00chei_1_p154_c1, 0.3921), (24, cheiroslanguageo00chei_1_p155_c0, 0.3907), (25, cheiroslanguageo00chei_1_p151_c0, 0.389), (26, cheiroslanguageo00chei_1_p152_c1, 0.3724), (27, cheiroslanguageo00chei_1_p152_c0, 0.3553), (28, cheiroslanguageo00chei_1_p155_c1, 0.3123), (29, cheiroslanguageo00chei_1_p145_c2, 0.2804), (30, cheiroslanguageo00chei_1_p153_c2, 0.1865)]
  heart line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p160_c2, 0.6427), (2, cheiroslanguageo00chei_1_p161_c0, 0.6188), (3, cheiroslanguageo00chei_1_p159_c2, 0.6061), (4, cheiroslanguageo00chei_1_p159_c3, 0.6054), (5, cheiroslanguageo00chei_1_p156_c0, 0.5884), (6, cheiroslanguageo00chei_1_p160_c1, 0.557), (7, cheiroslanguageo00chei_1_p156_c1, 0.5494), (8, cheiroslanguageo00chei_1_p160_c3, 0.522), (9, cheiroslanguageo00chei_1_p160_c0, 0.4791), (10, cheiroslanguageo00chei_1_p159_c1, 0.4751), (11, cheiroslanguageo00chei_1_p159_c0, 0.3856), (12, cheiroslanguageo00chei_1_p156_c2, 0.3415)]
  life line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p139_c0, 0.6108), (2, cheiroslanguageo00chei_1_p134_c2, 0.5801), (3, cheiroslanguageo00chei_1_p134_c1, 0.5775), (4, cheiroslanguageo00chei_1_p135_c0, 0.5652), (5, cheiroslanguageo00chei_1_p139_c1, 0.5552), (6, cheiroslanguageo00chei_1_p138_c1, 0.5406), (7, cheiroslanguageo00chei_1_p135_c2, 0.5394), (8, cheiroslanguageo00chei_1_p136_c1, 0.5337), (9, cheiroslanguageo00chei_1_p136_c3, 0.5332), (10, cheiroslanguageo00chei_1_p134_c0, 0.5317), (11, cheiroslanguageo00chei_1_p135_c1, 0.5253), (12, cheiroslanguageo00chei_1_p137_c1, 0.5195), (13, cheiroslanguageo00chei_1_p136_c2, 0.5054), (14, cheiroslanguageo00chei_1_p137_c0, 0.5013), (15, cheiroslanguageo00chei_1_p138_c2, 0.4935), (16, cheiroslanguageo00chei_1_p138_c0, 0.466), (17, cheiroslanguageo00chei_1_p137_c3, 0.4625), (18, cheiroslanguageo00chei_1_p133_c0, 0.4477), (19, cheiroslanguageo00chei_1_p137_c2, 0.4165), (20, cheiroslanguageo00chei_1_p134_c3, 0.399), (21, cheiroslanguageo00chei_1_p136_c0, 0.3986), (22, cheiroslanguageo00chei_1_p133_c1, 0.177), (23, cheiroslanguageo00chei_1_p139_c2, 0.0862)]
  mount of venus: window=3 candidates=[(1, cheiroslanguageo00chei_1_p111_c1, 0.652), (2, cheiroslanguageo00chei_1_p112_c0, 0.6181), (3, cheiroslanguageo00chei_1_p113_c0, 0.497), (4, cheiroslanguageo00chei_1_p111_c0, 0.4856), (5, cheiroslanguageo00chei_1_p112_c1, 0.4774), (6, cheiroslanguageo00chei_1_p113_c1, 0.4747), (7, cheiroslanguageo00chei_1_p112_c2, 0.4245)]
  thumb: window=3 candidates=[(1, cheiroslanguageo00chei_1_p88_c0, 0.5569), (2, cheiroslanguageo00chei_1_p87_c0, 0.5513), (3, cheiroslanguageo00chei_1_p88_c1, 0.5327), (4, cheiroslanguageo00chei_1_p89_c2, 0.5322), (5, cheiroslanguageo00chei_1_p89_c0, 0.5226), (6, cheiroslanguageo00chei_1_p85_c0, 0.5033), (7, cheiroslanguageo00chei_1_p86_c0, 0.4837), (8, cheiroslanguageo00chei_1_p90_c2, 0.4443), (9, cheiroslanguageo00chei_1_p85_c1, 0.4043), (10, cheiroslanguageo00chei_1_p88_c2, 0.3724), (11, cheiroslanguageo00chei_1_p90_c0, 0.3615), (12, cheiroslanguageo00chei_1_p89_c1, 0.305), (13, cheiroslanguageo00chei_1_p90_c1, 0.2905), (14, cheiroslanguageo00chei_1_p87_c1, 0.0692)]

## RUN 2026-08-04T15:37:43.891617

### capture_reason
silence

### Confirmed descriptions
#### LEFT
HAND SHAPE: Square palm, overall build is medium.

FINGERS: Fingers are long relative to the palm, appear straight, fingertips are rounded, spacing is moderate.

THUMB: Medium size, set moderately low, wide angle from the palm.

LIFE LINE: Present, deep, long, curves around the base of the thumb, no clear breaks, chains, forks, or islands visible.

HEAD LINE: Present, deep, long, slightly curved, no clear breaks, chains, forks, or islands visible.

HEART LINE: Present, deep, long, slightly curved, no clear breaks, chains, forks, or islands visible.

FATE LINE: Barely visible.

OTHER LINES: No other lines clearly visible.

MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.

MARKS: No marks clearly visible.
#### RIGHT
HAND SHAPE: Square palm, overall build is medium.

FINGERS: Fingers are slightly longer than the palm, appear straight, with rounded fingertips, moderate spacing.

THUMB: Medium size, set moderately low, wide angle from the palm.

LIFE LINE: Present, deep, long, curves around the base of the thumb, no clear breaks or forks.

HEAD LINE: Present, deep, long, slightly curved, no clear breaks or forks.

HEART LINE: Present, moderately deep, curves slightly upwards, no clear breaks or forks.

FATE LINE: Barely visible.

OTHER LINES: No other lines clearly visible.

MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.

MARKS: No marks clearly visible.

### reading_text


A note on what I have not interpreted: the classical texts I work from do not clearly address the following as they appear in your hands: life line, head line, heart line, fate line, sun line, thumb, fingers, mount of venus, mount of jupiter. Rather than guess, I have left these out of your reading.

For major life decisions, I recommend consulting a qualified astrologer or palm reader for a personal reading.

### READING (TAGGED)


### sources

### feature_support
supported_features: ('life line', 'head line', 'heart line', 'fate line', 'thumb', 'fingers', 'mount of venus')
unsupported_features: ('sun line', 'mount of jupiter')

### claims_inventory
claims_inventory: EMPTY

### ring1_validation
passed: True
failures: ()
retry_used: False
stage1_retry_features: NONE
stage1_feature_diagnostics:
  _rules_engine: outcome=rules_engine_ok attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  fate line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  fingers: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  head line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  heart line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  life line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  markings/other features: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of jupiter: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of venus: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  sun line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  thumb: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
stage2_retry_used: False
stage2_first_attempt_failures: NONE
validation_failures: NONE
ring1_failures:
none

### near_miss_margin
  fate line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p165_c1, 0.6001), (2, cheiroslanguageo00chei_1_p163_c1, 0.5869), (3, cheiroslanguageo00chei_1_p165_c0, 0.5671), (4, cheiroslanguageo00chei_1_p163_c2, 0.561), (5, cheiroslanguageo00chei_1_p162_c0, 0.5515), (6, cheiroslanguageo00chei_1_p163_c0, 0.5486), (7, cheiroslanguageo00chei_1_p164_c1, 0.5336), (8, cheiroslanguageo00chei_1_p164_c2, 0.5165), (9, cheiroslanguageo00chei_1_p162_c1, 0.5081), (10, cheiroslanguageo00chei_1_p164_c0, 0.4756), (11, cheiroslanguageo00chei_1_p165_c2, 0.4595), (12, cheiroslanguageo00chei_1_p163_c3, 0.4594), (13, cheiroslanguageo00chei_1_p164_c3, 0.4225), (14, cheiroslanguageo00chei_1_p162_c2, 0.3622)]
  fingers: window=3 candidates=[(1, cheiroslanguageo00chei_1_p96_c1, 0.5429), (2, cheiroslanguageo00chei_1_p96_c2, 0.5211), (3, cheiroslanguageo00chei_1_p96_c0, 0.5149), (4, cheiroslanguageo00chei_1_p95_c0, 0.4914), (5, cheiroslanguageo00chei_1_p96_c3, 0.4858), (6, cheiroslanguageo00chei_1_p97_c0, 0.4792), (7, cheiroslanguageo00chei_1_p95_c1, 0.4633), (8, cheiroslanguageo00chei_1_p95_c2, 0.4456), (9, cheiroslanguageo00chei_1_p93_c0, 0.3963), (10, cheiroslanguageo00chei_1_p94_c0, 0.3773), (11, cheiroslanguageo00chei_1_p93_c1, 0.285)]
  head line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p145_c0, 0.5589), (2, cheiroslanguageo00chei_1_p147_c1, 0.526), (3, cheiroslanguageo00chei_1_p151_c2, 0.5226), (4, cheiroslanguageo00chei_1_p147_c0, 0.5066), (5, cheiroslanguageo00chei_1_p148_c1, 0.4943), (6, cheiroslanguageo00chei_1_p148_c0, 0.4909), (7, cheiroslanguageo00chei_1_p150_c2, 0.4888), (8, cheiroslanguageo00chei_1_p147_c3, 0.4814), (9, cheiroslanguageo00chei_1_p151_c1, 0.4715), (10, cheiroslanguageo00chei_1_p149_c0, 0.4706), (11, cheiroslanguageo00chei_1_p153_c1, 0.4687), (12, cheiroslanguageo00chei_1_p150_c0, 0.4672), (13, cheiroslanguageo00chei_1_p150_c1, 0.4557), (14, cheiroslanguageo00chei_1_p146_c1, 0.4521), (15, cheiroslanguageo00chei_1_p154_c0, 0.4489), (16, cheiroslanguageo00chei_1_p148_c2, 0.4464), (17, cheiroslanguageo00chei_1_p146_c0, 0.4423), (18, cheiroslanguageo00chei_1_p146_c2, 0.4209), (19, cheiroslanguageo00chei_1_p149_c1, 0.4114), (20, cheiroslanguageo00chei_1_p153_c0, 0.4093), (21, cheiroslanguageo00chei_1_p145_c1, 0.4086), (22, cheiroslanguageo00chei_1_p147_c2, 0.3982), (23, cheiroslanguageo00chei_1_p154_c1, 0.3921), (24, cheiroslanguageo00chei_1_p155_c0, 0.3907), (25, cheiroslanguageo00chei_1_p151_c0, 0.389), (26, cheiroslanguageo00chei_1_p152_c1, 0.3724), (27, cheiroslanguageo00chei_1_p152_c0, 0.3553), (28, cheiroslanguageo00chei_1_p155_c1, 0.3123), (29, cheiroslanguageo00chei_1_p145_c2, 0.2804), (30, cheiroslanguageo00chei_1_p153_c2, 0.1865)]
  heart line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p160_c2, 0.6271), (2, cheiroslanguageo00chei_1_p159_c3, 0.6102), (3, cheiroslanguageo00chei_1_p161_c0, 0.6089), (4, cheiroslanguageo00chei_1_p159_c2, 0.584), (5, cheiroslanguageo00chei_1_p156_c0, 0.5798), (6, cheiroslanguageo00chei_1_p160_c1, 0.5508), (7, cheiroslanguageo00chei_1_p156_c1, 0.5382), (8, cheiroslanguageo00chei_1_p160_c3, 0.5246), (9, cheiroslanguageo00chei_1_p159_c1, 0.4773), (10, cheiroslanguageo00chei_1_p160_c0, 0.4426), (11, cheiroslanguageo00chei_1_p159_c0, 0.3762), (12, cheiroslanguageo00chei_1_p156_c2, 0.3282)]
  life line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p139_c0, 0.6108), (2, cheiroslanguageo00chei_1_p134_c2, 0.5801), (3, cheiroslanguageo00chei_1_p134_c1, 0.5775), (4, cheiroslanguageo00chei_1_p135_c0, 0.5652), (5, cheiroslanguageo00chei_1_p139_c1, 0.5552), (6, cheiroslanguageo00chei_1_p138_c1, 0.5406), (7, cheiroslanguageo00chei_1_p135_c2, 0.5394), (8, cheiroslanguageo00chei_1_p136_c1, 0.5337), (9, cheiroslanguageo00chei_1_p136_c3, 0.5332), (10, cheiroslanguageo00chei_1_p134_c0, 0.5317), (11, cheiroslanguageo00chei_1_p135_c1, 0.5253), (12, cheiroslanguageo00chei_1_p137_c1, 0.5195), (13, cheiroslanguageo00chei_1_p136_c2, 0.5054), (14, cheiroslanguageo00chei_1_p137_c0, 0.5013), (15, cheiroslanguageo00chei_1_p138_c2, 0.4935), (16, cheiroslanguageo00chei_1_p138_c0, 0.466), (17, cheiroslanguageo00chei_1_p137_c3, 0.4625), (18, cheiroslanguageo00chei_1_p133_c0, 0.4477), (19, cheiroslanguageo00chei_1_p137_c2, 0.4165), (20, cheiroslanguageo00chei_1_p134_c3, 0.399), (21, cheiroslanguageo00chei_1_p136_c0, 0.3986), (22, cheiroslanguageo00chei_1_p133_c1, 0.177), (23, cheiroslanguageo00chei_1_p139_c2, 0.0862)]
  mount of venus: window=3 candidates=[(1, cheiroslanguageo00chei_1_p111_c1, 0.652), (2, cheiroslanguageo00chei_1_p112_c0, 0.6181), (3, cheiroslanguageo00chei_1_p113_c0, 0.497), (4, cheiroslanguageo00chei_1_p111_c0, 0.4856), (5, cheiroslanguageo00chei_1_p112_c1, 0.4774), (6, cheiroslanguageo00chei_1_p113_c1, 0.4747), (7, cheiroslanguageo00chei_1_p112_c2, 0.4245)]
  thumb: window=3 candidates=[(1, cheiroslanguageo00chei_1_p88_c0, 0.5569), (2, cheiroslanguageo00chei_1_p87_c0, 0.5513), (3, cheiroslanguageo00chei_1_p88_c1, 0.5327), (4, cheiroslanguageo00chei_1_p89_c2, 0.5322), (5, cheiroslanguageo00chei_1_p89_c0, 0.5226), (6, cheiroslanguageo00chei_1_p85_c0, 0.5033), (7, cheiroslanguageo00chei_1_p86_c0, 0.4837), (8, cheiroslanguageo00chei_1_p90_c2, 0.4443), (9, cheiroslanguageo00chei_1_p85_c1, 0.4043), (10, cheiroslanguageo00chei_1_p88_c2, 0.3724), (11, cheiroslanguageo00chei_1_p90_c0, 0.3615), (12, cheiroslanguageo00chei_1_p89_c1, 0.305), (13, cheiroslanguageo00chei_1_p90_c1, 0.2905), (14, cheiroslanguageo00chei_1_p87_c1, 0.0692)]

## RUN 2026-08-04T15:40:39.808120

### capture_reason
silence

### Confirmed descriptions
#### LEFT
HAND SHAPE: Square palm, overall build is sturdy.

FINGERS: Fingers are of medium length relative to the palm, appear straight, with rounded fingertips, and moderate spacing.

THUMB: Medium size, set moderately low, with a wide angle from the palm.

LIFE LINE: Present, deep, long, curves around the base of the thumb, no visible breaks or forks.

HEAD LINE: Present, deep, long, slightly curved, no visible breaks or forks.

HEART LINE: Present, deep, long, curves slightly upwards, no visible breaks or forks.

FATE LINE: Present, moderately deep, runs vertically towards the middle finger, no visible breaks or forks.

OTHER LINES: Sun line is faintly visible, no clear health or marriage lines.

MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.

MARKS: No clear marks visible.
#### RIGHT
HAND SHAPE: Square palm, overall build is robust.

FINGERS: Fingers are slightly longer than the palm, appear straight, fingertips are rounded, spacing is moderate.

THUMB: Medium relative size, set moderately low, wide angle from the palm.

LIFE LINE: Present, deep, long, curves around the base of the thumb, no breaks or chains visible.

HEAD LINE: Present, deep, long, slightly curved, runs across the palm, no breaks or chains visible.

HEART LINE: Present, deep, long, curves slightly upwards, no breaks or chains visible.

FATE LINE: Barely visible.

OTHER LINES: Not clearly visible.

MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.

MARKS: No marks clearly visible.

### reading_text


A note on what I have not interpreted: the classical texts I work from do not clearly address the following as they appear in your hands: life line, head line, heart line, fate line, sun line, thumb, fingers, mount of venus, mount of jupiter. Rather than guess, I have left these out of your reading.

For major life decisions, I recommend consulting a qualified astrologer or palm reader for a personal reading.

### READING (TAGGED)


### sources

### feature_support
supported_features: ('life line', 'head line', 'heart line', 'fate line', 'sun line', 'thumb', 'fingers', 'mount of venus')
unsupported_features: ('mount of jupiter',)

### claims_inventory
claims_inventory: EMPTY

### ring1_validation
passed: True
failures: ()
retry_used: False
stage1_retry_features: NONE
stage1_feature_diagnostics:
  _rules_engine: outcome=rules_engine_ok attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  fate line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  fingers: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  head line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  heart line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  life line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  markings/other features: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of jupiter: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of venus: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  sun line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  thumb: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
stage2_retry_used: False
stage2_first_attempt_failures: NONE
validation_failures: NONE
ring1_failures:
none

### near_miss_margin
  fate line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p165_c1, 0.5711), (2, cheiroslanguageo00chei_1_p163_c1, 0.5633), (3, cheiroslanguageo00chei_1_p165_c0, 0.5533), (4, cheiroslanguageo00chei_1_p163_c2, 0.5377), (5, cheiroslanguageo00chei_1_p163_c0, 0.5251), (6, cheiroslanguageo00chei_1_p164_c1, 0.5196), (7, cheiroslanguageo00chei_1_p162_c0, 0.5166), (8, cheiroslanguageo00chei_1_p164_c2, 0.5115), (9, cheiroslanguageo00chei_1_p162_c1, 0.4896), (10, cheiroslanguageo00chei_1_p164_c0, 0.4588), (11, cheiroslanguageo00chei_1_p163_c3, 0.445), (12, cheiroslanguageo00chei_1_p165_c2, 0.4335), (13, cheiroslanguageo00chei_1_p164_c3, 0.4188), (14, cheiroslanguageo00chei_1_p162_c2, 0.3676)]
  fingers: window=3 candidates=[(1, cheiroslanguageo00chei_1_p96_c0, 0.5108), (2, cheiroslanguageo00chei_1_p96_c2, 0.5084), (3, cheiroslanguageo00chei_1_p97_c0, 0.4926), (4, cheiroslanguageo00chei_1_p96_c1, 0.4862), (5, cheiroslanguageo00chei_1_p96_c3, 0.4839), (6, cheiroslanguageo00chei_1_p95_c0, 0.4692), (7, cheiroslanguageo00chei_1_p95_c2, 0.4585), (8, cheiroslanguageo00chei_1_p95_c1, 0.4489), (9, cheiroslanguageo00chei_1_p93_c0, 0.3823), (10, cheiroslanguageo00chei_1_p94_c0, 0.3685), (11, cheiroslanguageo00chei_1_p93_c1, 0.2336)]
  head line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p145_c0, 0.5589), (2, cheiroslanguageo00chei_1_p147_c1, 0.526), (3, cheiroslanguageo00chei_1_p151_c2, 0.5226), (4, cheiroslanguageo00chei_1_p147_c0, 0.5066), (5, cheiroslanguageo00chei_1_p148_c1, 0.4943), (6, cheiroslanguageo00chei_1_p148_c0, 0.4909), (7, cheiroslanguageo00chei_1_p150_c2, 0.4888), (8, cheiroslanguageo00chei_1_p147_c3, 0.4814), (9, cheiroslanguageo00chei_1_p151_c1, 0.4715), (10, cheiroslanguageo00chei_1_p149_c0, 0.4706), (11, cheiroslanguageo00chei_1_p153_c1, 0.4687), (12, cheiroslanguageo00chei_1_p150_c0, 0.4672), (13, cheiroslanguageo00chei_1_p150_c1, 0.4557), (14, cheiroslanguageo00chei_1_p146_c1, 0.4521), (15, cheiroslanguageo00chei_1_p154_c0, 0.4489), (16, cheiroslanguageo00chei_1_p148_c2, 0.4464), (17, cheiroslanguageo00chei_1_p146_c0, 0.4423), (18, cheiroslanguageo00chei_1_p146_c2, 0.4209), (19, cheiroslanguageo00chei_1_p149_c1, 0.4114), (20, cheiroslanguageo00chei_1_p153_c0, 0.4093), (21, cheiroslanguageo00chei_1_p145_c1, 0.4086), (22, cheiroslanguageo00chei_1_p147_c2, 0.3982), (23, cheiroslanguageo00chei_1_p154_c1, 0.3921), (24, cheiroslanguageo00chei_1_p155_c0, 0.3907), (25, cheiroslanguageo00chei_1_p151_c0, 0.389), (26, cheiroslanguageo00chei_1_p152_c1, 0.3724), (27, cheiroslanguageo00chei_1_p152_c0, 0.3553), (28, cheiroslanguageo00chei_1_p155_c1, 0.3123), (29, cheiroslanguageo00chei_1_p145_c2, 0.2804), (30, cheiroslanguageo00chei_1_p153_c2, 0.1865)]
  heart line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p160_c2, 0.6427), (2, cheiroslanguageo00chei_1_p161_c0, 0.6188), (3, cheiroslanguageo00chei_1_p159_c2, 0.6061), (4, cheiroslanguageo00chei_1_p159_c3, 0.6054), (5, cheiroslanguageo00chei_1_p156_c0, 0.5884), (6, cheiroslanguageo00chei_1_p160_c1, 0.557), (7, cheiroslanguageo00chei_1_p156_c1, 0.5494), (8, cheiroslanguageo00chei_1_p160_c3, 0.522), (9, cheiroslanguageo00chei_1_p160_c0, 0.4791), (10, cheiroslanguageo00chei_1_p159_c1, 0.4751), (11, cheiroslanguageo00chei_1_p159_c0, 0.3856), (12, cheiroslanguageo00chei_1_p156_c2, 0.3415)]
  life line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p139_c0, 0.6108), (2, cheiroslanguageo00chei_1_p134_c2, 0.5801), (3, cheiroslanguageo00chei_1_p134_c1, 0.5775), (4, cheiroslanguageo00chei_1_p135_c0, 0.5652), (5, cheiroslanguageo00chei_1_p139_c1, 0.5552), (6, cheiroslanguageo00chei_1_p138_c1, 0.5406), (7, cheiroslanguageo00chei_1_p135_c2, 0.5394), (8, cheiroslanguageo00chei_1_p136_c1, 0.5337), (9, cheiroslanguageo00chei_1_p136_c3, 0.5332), (10, cheiroslanguageo00chei_1_p134_c0, 0.5317), (11, cheiroslanguageo00chei_1_p135_c1, 0.5253), (12, cheiroslanguageo00chei_1_p137_c1, 0.5195), (13, cheiroslanguageo00chei_1_p136_c2, 0.5054), (14, cheiroslanguageo00chei_1_p137_c0, 0.5013), (15, cheiroslanguageo00chei_1_p138_c2, 0.4935), (16, cheiroslanguageo00chei_1_p138_c0, 0.466), (17, cheiroslanguageo00chei_1_p137_c3, 0.4625), (18, cheiroslanguageo00chei_1_p133_c0, 0.4477), (19, cheiroslanguageo00chei_1_p137_c2, 0.4165), (20, cheiroslanguageo00chei_1_p134_c3, 0.399), (21, cheiroslanguageo00chei_1_p136_c0, 0.3986), (22, cheiroslanguageo00chei_1_p133_c1, 0.177), (23, cheiroslanguageo00chei_1_p139_c2, 0.0862)]
  mount of venus: window=3 candidates=[(1, cheiroslanguageo00chei_1_p111_c1, 0.652), (2, cheiroslanguageo00chei_1_p112_c0, 0.6181), (3, cheiroslanguageo00chei_1_p113_c0, 0.497), (4, cheiroslanguageo00chei_1_p111_c0, 0.4856), (5, cheiroslanguageo00chei_1_p112_c1, 0.4774), (6, cheiroslanguageo00chei_1_p113_c1, 0.4747), (7, cheiroslanguageo00chei_1_p112_c2, 0.4245)]
  sun line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p166_c1, 0.5206), (2, cheiroslanguageo00chei_1_p166_c0, 0.5176), (3, cheiroslanguageo00chei_1_p169_c0, 0.5064), (4, cheiroslanguageo00chei_1_p169_c2, 0.478), (5, cheiroslanguageo00chei_1_p170_c0, 0.4632), (6, cheiroslanguageo00chei_1_p169_c1, 0.3619), (7, cheiroslanguageo00chei_1_p169_c3, 0.3531), (8, cheiroslanguageo00chei_1_p166_c2, 0.3499)]
  thumb: window=3 candidates=[(1, cheiroslanguageo00chei_1_p88_c0, 0.5159), (2, cheiroslanguageo00chei_1_p87_c0, 0.5151), (3, cheiroslanguageo00chei_1_p89_c2, 0.5107), (4, cheiroslanguageo00chei_1_p88_c1, 0.5084), (5, cheiroslanguageo00chei_1_p89_c0, 0.49), (6, cheiroslanguageo00chei_1_p86_c0, 0.4525), (7, cheiroslanguageo00chei_1_p85_c0, 0.451), (8, cheiroslanguageo00chei_1_p90_c2, 0.4245), (9, cheiroslanguageo00chei_1_p90_c0, 0.372), (10, cheiroslanguageo00chei_1_p88_c2, 0.3704), (11, cheiroslanguageo00chei_1_p85_c1, 0.3696), (12, cheiroslanguageo00chei_1_p89_c1, 0.2948), (13, cheiroslanguageo00chei_1_p90_c1, 0.2705), (14, cheiroslanguageo00chei_1_p87_c1, 0.0831)]

## RUN 2026-08-04T15:43:09.833068

### capture_reason
silence

### Confirmed descriptions
#### LEFT
HAND SHAPE: Square palm, overall build is average.

FINGERS: Fingers are slightly longer than the palm, appear straight, fingertips are rounded, spacing is average.

THUMB: Medium relative size, set moderately low, wide angle from the palm.

LIFE LINE: Present, moderately deep, curves around the base of the thumb, no clear breaks, chains, forks, or islands visible.

HEAD LINE: Present, moderately deep, straight, runs across the palm, no clear breaks, chains, forks, or islands visible.

HEART LINE: Present, moderately deep, curves slightly upwards, no clear breaks, chains, forks, or islands visible.

FATE LINE: Barely visible.

OTHER LINES: No other lines clearly visible.

MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.

MARKS: No marks such as crosses, stars, grilles, squares, or moles clearly visible.
#### RIGHT
HAND SHAPE: Elongated palm, overall build is slender.

FINGERS: Long relative to palm, straight, rounded fingertips, moderate spacing.

THUMB: Medium size, set moderately low, wide angle from the palm.

LIFE LINE: Present, deep, long, curves around the base of the thumb, no clear breaks or forks.

HEAD LINE: Present, deep, long, slightly curved, no clear breaks or forks.

HEART LINE: Present, deep, long, slightly curved, no clear breaks or forks.

FATE LINE: Barely visible.

OTHER LINES: Sun line visible, no clear health or marriage lines.

MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.

MARKS: No clear marks visible.

### reading_text


A note on what I have not interpreted: the classical texts I work from do not clearly address the following as they appear in your hands: life line, head line, heart line, fate line, sun line, thumb, fingers, mount of venus, mount of jupiter, markings and other features. Rather than guess, I have left these out of your reading.

For major life decisions, I recommend consulting a qualified astrologer or palm reader for a personal reading.

### READING (TAGGED)


### sources

### feature_support
supported_features: ('life line', 'head line', 'heart line', 'fate line', 'sun line', 'thumb', 'fingers', 'mount of venus', 'markings/other features')
unsupported_features: ('mount of jupiter',)

### claims_inventory
claims_inventory: EMPTY

### ring1_validation
passed: True
failures: ()
retry_used: False
stage1_retry_features: NONE
stage1_feature_diagnostics:
  _rules_engine: outcome=rules_engine_ok attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  fate line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  fingers: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  head line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  heart line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  life line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  markings/other features: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of jupiter: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of venus: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  sun line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  thumb: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
stage2_retry_used: False
stage2_first_attempt_failures: NONE
validation_failures: NONE
ring1_failures:
none

### near_miss_margin
  fate line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p165_c1, 0.6001), (2, cheiroslanguageo00chei_1_p163_c1, 0.5869), (3, cheiroslanguageo00chei_1_p165_c0, 0.5671), (4, cheiroslanguageo00chei_1_p163_c2, 0.561), (5, cheiroslanguageo00chei_1_p162_c0, 0.5515), (6, cheiroslanguageo00chei_1_p163_c0, 0.5486), (7, cheiroslanguageo00chei_1_p164_c1, 0.5336), (8, cheiroslanguageo00chei_1_p164_c2, 0.5165), (9, cheiroslanguageo00chei_1_p162_c1, 0.5081), (10, cheiroslanguageo00chei_1_p164_c0, 0.4756), (11, cheiroslanguageo00chei_1_p165_c2, 0.4595), (12, cheiroslanguageo00chei_1_p163_c3, 0.4594), (13, cheiroslanguageo00chei_1_p164_c3, 0.4225), (14, cheiroslanguageo00chei_1_p162_c2, 0.3622)]
  fingers: window=3 candidates=[(1, cheiroslanguageo00chei_1_p96_c1, 0.5379), (2, cheiroslanguageo00chei_1_p96_c2, 0.5162), (3, cheiroslanguageo00chei_1_p96_c0, 0.5106), (4, cheiroslanguageo00chei_1_p95_c0, 0.4933), (5, cheiroslanguageo00chei_1_p96_c3, 0.4858), (6, cheiroslanguageo00chei_1_p97_c0, 0.4754), (7, cheiroslanguageo00chei_1_p95_c1, 0.4714), (8, cheiroslanguageo00chei_1_p95_c2, 0.4553), (9, cheiroslanguageo00chei_1_p93_c0, 0.4023), (10, cheiroslanguageo00chei_1_p94_c0, 0.3766), (11, cheiroslanguageo00chei_1_p93_c1, 0.2809)]
  head line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p145_c0, 0.5352), (2, cheiroslanguageo00chei_1_p151_c2, 0.4947), (3, cheiroslanguageo00chei_1_p148_c1, 0.4907), (4, cheiroslanguageo00chei_1_p147_c0, 0.4853), (5, cheiroslanguageo00chei_1_p150_c2, 0.4825), (6, cheiroslanguageo00chei_1_p147_c1, 0.4792), (7, cheiroslanguageo00chei_1_p147_c3, 0.4681), (8, cheiroslanguageo00chei_1_p149_c0, 0.457), (9, cheiroslanguageo00chei_1_p146_c1, 0.4565), (10, cheiroslanguageo00chei_1_p151_c1, 0.4551), (11, cheiroslanguageo00chei_1_p150_c1, 0.4474), (12, cheiroslanguageo00chei_1_p153_c1, 0.4448), (13, cheiroslanguageo00chei_1_p150_c0, 0.4389), (14, cheiroslanguageo00chei_1_p148_c2, 0.4349), (15, cheiroslanguageo00chei_1_p148_c0, 0.433), (16, cheiroslanguageo00chei_1_p154_c0, 0.4236), (17, cheiroslanguageo00chei_1_p146_c0, 0.4105), (18, cheiroslanguageo00chei_1_p146_c2, 0.4103), (19, cheiroslanguageo00chei_1_p145_c1, 0.3923), (20, cheiroslanguageo00chei_1_p149_c1, 0.3861), (21, cheiroslanguageo00chei_1_p153_c0, 0.3839), (22, cheiroslanguageo00chei_1_p155_c0, 0.3686), (23, cheiroslanguageo00chei_1_p151_c0, 0.3644), (24, cheiroslanguageo00chei_1_p152_c1, 0.3607), (25, cheiroslanguageo00chei_1_p147_c2, 0.3591), (26, cheiroslanguageo00chei_1_p154_c1, 0.3552), (27, cheiroslanguageo00chei_1_p152_c0, 0.3322), (28, cheiroslanguageo00chei_1_p145_c2, 0.3084), (29, cheiroslanguageo00chei_1_p155_c1, 0.2733), (30, cheiroslanguageo00chei_1_p153_c2, 0.1935)]
  heart line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p160_c2, 0.6157), (2, cheiroslanguageo00chei_1_p159_c3, 0.6059), (3, cheiroslanguageo00chei_1_p161_c0, 0.6012), (4, cheiroslanguageo00chei_1_p159_c2, 0.5802), (5, cheiroslanguageo00chei_1_p156_c0, 0.5735), (6, cheiroslanguageo00chei_1_p160_c1, 0.5444), (7, cheiroslanguageo00chei_1_p156_c1, 0.5387), (8, cheiroslanguageo00chei_1_p160_c3, 0.5188), (9, cheiroslanguageo00chei_1_p159_c1, 0.476), (10, cheiroslanguageo00chei_1_p160_c0, 0.4395), (11, cheiroslanguageo00chei_1_p159_c0, 0.3666), (12, cheiroslanguageo00chei_1_p156_c2, 0.3276)]
  life line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p139_c0, 0.6295), (2, cheiroslanguageo00chei_1_p134_c2, 0.5872), (3, cheiroslanguageo00chei_1_p135_c0, 0.5835), (4, cheiroslanguageo00chei_1_p139_c1, 0.5774), (5, cheiroslanguageo00chei_1_p134_c1, 0.5748), (6, cheiroslanguageo00chei_1_p135_c2, 0.5418), (7, cheiroslanguageo00chei_1_p136_c2, 0.5333), (8, cheiroslanguageo00chei_1_p136_c1, 0.529), (9, cheiroslanguageo00chei_1_p136_c3, 0.5265), (10, cheiroslanguageo00chei_1_p134_c0, 0.5208), (11, cheiroslanguageo00chei_1_p137_c0, 0.5156), (12, cheiroslanguageo00chei_1_p138_c1, 0.5148), (13, cheiroslanguageo00chei_1_p135_c1, 0.5111), (14, cheiroslanguageo00chei_1_p138_c2, 0.5024), (15, cheiroslanguageo00chei_1_p137_c1, 0.5023), (16, cheiroslanguageo00chei_1_p137_c3, 0.4751), (17, cheiroslanguageo00chei_1_p133_c0, 0.4698), (18, cheiroslanguageo00chei_1_p138_c0, 0.4589), (19, cheiroslanguageo00chei_1_p134_c3, 0.4215), (20, cheiroslanguageo00chei_1_p137_c2, 0.4139), (21, cheiroslanguageo00chei_1_p136_c0, 0.3948), (22, cheiroslanguageo00chei_1_p133_c1, 0.1769), (23, cheiroslanguageo00chei_1_p139_c2, 0.1115)]
  markings/other features: window=3 candidates=[(1, cheiroslanguageo00chei_1_p155_c1, 0.4323), (2, cheiroslanguageo00chei_1_p180_c2, 0.4175), (3, cheiroslanguageo00chei_1_p200_c1, 0.4097), (4, cheiroslanguageo00chei_1_p127_c1, 0.396), (5, cheiroslanguageo00chei_1_p160_c2, 0.3924), (6, cheiroslanguageo00chei_1_p207_c1, 0.3825), (7, cheiroslanguageo00chei_1_p172_c1, 0.3815), (8, cheiroslanguageo00chei_1_p148_c1, 0.3789), (9, cheiroslanguageo00chei_1_p187_c2, 0.3772), (10, cheiroslanguageo00chei_1_p137_c1, 0.3765), (11, cheiroslanguageo00chei_1_p198_c1, 0.3672), (12, cheiroslanguageo00chei_1_p152_c1, 0.3652), (13, cheiroslanguageo00chei_1_p208_c1, 0.3592), (14, cheiroslanguageo00chei_1_p197_c0, 0.3565), (15, cheiroslanguageo00chei_1_p161_c0, 0.3534), (16, cheiroslanguageo00chei_1_p170_c0, 0.3448), (17, cheiroslanguageo00chei_1_p209_c0, 0.3418), (18, cheiroslanguageo00chei_1_p128_c1, 0.3417), (19, cheiroslanguageo00chei_1_p124_c0, 0.3392), (20, cheiroslanguageo00chei_1_p165_c1, 0.3371), (21, cheiroslanguageo00chei_1_p20_c0, 0.3368), (22, cheiroslanguageo00chei_1_p179_c1, 0.3364), (23, cheiroslanguageo00chei_1_p183_c2, 0.336), (24, cheiroslanguageo00chei_1_p159_c3, 0.3339), (25, cheiroslanguageo00chei_1_p198_c2, 0.333), (26, cheiroslanguageo00chei_1_p192_c0, 0.3322), (27, cheiroslanguageo00chei_1_p135_c0, 0.3317), (28, cheiroslanguageo00chei_1_p34_c0, 0.3296), (29, cheiroslanguageo00chei_1_p128_c0, 0.3279), (30, cheiroslanguageo00chei_1_p184_c0, 0.3274)]
  mount of venus: window=3 candidates=[(1, cheiroslanguageo00chei_1_p111_c1, 0.652), (2, cheiroslanguageo00chei_1_p112_c0, 0.6181), (3, cheiroslanguageo00chei_1_p113_c0, 0.497), (4, cheiroslanguageo00chei_1_p111_c0, 0.4856), (5, cheiroslanguageo00chei_1_p112_c1, 0.4774), (6, cheiroslanguageo00chei_1_p113_c1, 0.4747), (7, cheiroslanguageo00chei_1_p112_c2, 0.4245)]
  sun line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p166_c1, 0.5583), (2, cheiroslanguageo00chei_1_p166_c0, 0.5557), (3, cheiroslanguageo00chei_1_p169_c0, 0.5301), (4, cheiroslanguageo00chei_1_p170_c0, 0.5049), (5, cheiroslanguageo00chei_1_p169_c2, 0.4894), (6, cheiroslanguageo00chei_1_p166_c2, 0.3792), (7, cheiroslanguageo00chei_1_p169_c1, 0.3665), (8, cheiroslanguageo00chei_1_p169_c3, 0.3546)]
  thumb: window=3 candidates=[(1, cheiroslanguageo00chei_1_p88_c0, 0.5104), (2, cheiroslanguageo00chei_1_p87_c0, 0.5078), (3, cheiroslanguageo00chei_1_p88_c1, 0.5041), (4, cheiroslanguageo00chei_1_p89_c2, 0.5035), (5, cheiroslanguageo00chei_1_p89_c0, 0.4813), (6, cheiroslanguageo00chei_1_p86_c0, 0.4576), (7, cheiroslanguageo00chei_1_p85_c0, 0.4479), (8, cheiroslanguageo00chei_1_p90_c2, 0.426), (9, cheiroslanguageo00chei_1_p90_c0, 0.3723), (10, cheiroslanguageo00chei_1_p88_c2, 0.3636), (11, cheiroslanguageo00chei_1_p85_c1, 0.3588), (12, cheiroslanguageo00chei_1_p89_c1, 0.2875), (13, cheiroslanguageo00chei_1_p90_c1, 0.2682), (14, cheiroslanguageo00chei_1_p87_c1, 0.0836)]

## RUN 2026-08-05T14:22:31.824001

### capture_reason
silence

### Confirmed descriptions
#### LEFT
HAND SHAPE: Square palm, overall build is robust.

FINGERS: Fingers are long relative to the palm, appear straight, with rounded fingertips, moderate spacing between them.

THUMB: Medium size, set moderately low, wide angle from the palm.

LIFE LINE: Present, deep, long, curves around the base of the thumb, no breaks visible.

HEAD LINE: Present, deep, long, slightly curved, runs across the palm, no breaks visible.

HEART LINE: Present, deep, long, curves slightly upwards, no breaks visible.

FATE LINE: Barely visible.

OTHER LINES: No other lines clearly visible.

MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.

MARKS: No marks clearly visible.
#### RIGHT
HAND SHAPE: Square palm, overall build is medium.
FINGERS: Fingers are slightly longer than the palm, straight, with rounded fingertips, spaced moderately apart.
THUMB: Medium size, set moderately low, wide angle from the palm.
LIFE LINE: Present, deep, long, curves around the base of the thumb, no clear breaks or forks.
HEAD LINE: Present, deep, long, slightly curved, starts joined with the life line.
HEART LINE: Present, deep, long, slightly curved, ends below the index finger.
FATE LINE: Present, moderately deep, starts from the base of the palm and runs towards the middle finger.
OTHER LINES: Sun line is faintly visible.
MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.
MARKS: No clear marks visible.

### reading_text


A note on what I have not interpreted: the classical texts I work from do not clearly address the following as they appear in your hands: life line, head line, heart line, fate line, sun line, thumb, fingers, mount of venus, mount of jupiter. Rather than guess, I have left these out of your reading.

For major life decisions, I recommend consulting a qualified astrologer or palm reader for a personal reading.

### READING (TAGGED)


### sources

### feature_support
supported_features: ('life line', 'head line', 'heart line', 'fate line', 'sun line', 'thumb', 'fingers', 'mount of venus')
unsupported_features: ('mount of jupiter',)

### claims_inventory
claims_inventory: EMPTY

### ring1_validation
passed: True
failures: ()
retry_used: False
stage1_retry_features: NONE
stage1_feature_diagnostics:
  _rules_engine: outcome=rules_engine_ok failed=False
    enabled_features: ['Line of Fate', 'Line of Head', 'Line of Heart', 'Line of Life', 'Line of Sun', 'Mount of Jupiter', 'Mount of Venus', 'Thumb']
    fired_rule_ids: []
    surviving_rule_ids: []
    suppression_log: []
    dropped_tokens: []
    observation_record:
      Line of Fate: tokens={'Clarity': {'value': 'absent', 'confidence': 0.6}, 'Starting_Point': {'value': 'at_base', 'confidence': 0.6}} unmapped=[{'quality': 'moderately_deep', 'attribute_guess': 'Depth'}, {'quality': 'towards_middle_finger', 'attribute_guess': 'Position'}] raw_prose="Barely visible. Present, moderately deep, starts from the base of the palm and runs towards the middle finger."
      Line of Head: tokens={'Depth': {'value': 'deep', 'confidence': 0.6}, 'Length': {'value': 'long', 'confidence': 0.6}, 'Curve': {'value': 'curved', 'confidence': 0.6}, 'Continuity': {'value': 'unbroken', 'confidence': 0.6}} unmapped=[{'quality': 'joined', 'attribute_guess': 'Starting_Point'}, {'quality': 'across', 'attribute_guess': 'Position'}] raw_prose="Present, deep, long, slightly curved, runs across the palm, no breaks visible. Present, deep, long, slightly curved, starts joined with the life line."
      Line of Heart: tokens={'Depth': {'value': 'deep', 'confidence': 0.6}, 'Length': {'value': 'long', 'confidence': 0.6}, 'Curve': {'value': 'curved', 'confidence': 0.6}, 'Continuity': {'value': 'unbroken', 'confidence': 0.6}} unmapped=[{'quality': 'below_index_finger', 'attribute_guess': 'Ending_Point'}] raw_prose="Present, deep, long, curves slightly upwards, no breaks visible. Present, deep, long, slightly curved, ends below the index finger."
      Line of Life: tokens={'Depth': {'value': 'deep', 'confidence': 1.0}, 'Length': {'value': 'long', 'confidence': 1.0}, 'Curve': {'value': 'curved', 'confidence': 1.0}, 'Continuity': {'value': 'unbroken', 'confidence': 1.0}} unmapped=[] raw_prose="Present, deep, long, curves around the base of the thumb, no breaks visible. Present, deep, long, curves around the base of the thumb, no clear breaks or forks."
      Line of Sun: tokens={'Clarity': {'value': 'absent', 'confidence': 0.6}} unmapped=[] raw_prose="Sun line is faintly visible."
      Mount of Venus: tokens={'Development': {'value': 'developed', 'confidence': 1.0}} unmapped=[] raw_prose="Mount of Venus appears developed Mount of Venus appears developed"
      Thumb: tokens={'Length': {'value': 'medium', 'confidence': 1.0}, 'Angle': {'value': 'wide', 'confidence': 1.0}} unmapped=[{'quality': 'moderately_low', 'attribute_guess': 'Setting'}] raw_prose="Medium size, set moderately low, wide angle from the palm. Medium size, set moderately low, wide angle from the palm."
  fate line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  fingers: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  head line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  heart line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  life line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  markings/other features: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of jupiter: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of venus: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  sun line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  thumb: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
stage2_retry_used: False
stage2_first_attempt_failures: NONE
validation_failures: NONE
ring1_failures:
none

### near_miss_margin
  fate line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p165_c1, 0.5958), (2, cheiroslanguageo00chei_1_p163_c1, 0.5942), (3, cheiroslanguageo00chei_1_p165_c0, 0.5739), (4, cheiroslanguageo00chei_1_p163_c2, 0.5651), (5, cheiroslanguageo00chei_1_p163_c0, 0.5482), (6, cheiroslanguageo00chei_1_p164_c1, 0.547), (7, cheiroslanguageo00chei_1_p162_c0, 0.5379), (8, cheiroslanguageo00chei_1_p164_c2, 0.5338), (9, cheiroslanguageo00chei_1_p162_c1, 0.5168), (10, cheiroslanguageo00chei_1_p164_c0, 0.4946), (11, cheiroslanguageo00chei_1_p163_c3, 0.4767), (12, cheiroslanguageo00chei_1_p165_c2, 0.4553), (13, cheiroslanguageo00chei_1_p164_c3, 0.4512), (14, cheiroslanguageo00chei_1_p162_c2, 0.3662)]
  fingers: window=3 candidates=[(1, cheiroslanguageo00chei_1_p96_c1, 0.5429), (2, cheiroslanguageo00chei_1_p96_c2, 0.5211), (3, cheiroslanguageo00chei_1_p96_c0, 0.5149), (4, cheiroslanguageo00chei_1_p95_c0, 0.4914), (5, cheiroslanguageo00chei_1_p96_c3, 0.4858), (6, cheiroslanguageo00chei_1_p97_c0, 0.4792), (7, cheiroslanguageo00chei_1_p95_c1, 0.4633), (8, cheiroslanguageo00chei_1_p95_c2, 0.4456), (9, cheiroslanguageo00chei_1_p93_c0, 0.3963), (10, cheiroslanguageo00chei_1_p94_c0, 0.3773), (11, cheiroslanguageo00chei_1_p93_c1, 0.285)]
  head line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p145_c0, 0.5589), (2, cheiroslanguageo00chei_1_p147_c1, 0.526), (3, cheiroslanguageo00chei_1_p151_c2, 0.5226), (4, cheiroslanguageo00chei_1_p147_c0, 0.5066), (5, cheiroslanguageo00chei_1_p148_c1, 0.4943), (6, cheiroslanguageo00chei_1_p148_c0, 0.4909), (7, cheiroslanguageo00chei_1_p150_c2, 0.4888), (8, cheiroslanguageo00chei_1_p147_c3, 0.4814), (9, cheiroslanguageo00chei_1_p151_c1, 0.4715), (10, cheiroslanguageo00chei_1_p149_c0, 0.4706), (11, cheiroslanguageo00chei_1_p153_c1, 0.4687), (12, cheiroslanguageo00chei_1_p150_c0, 0.4672), (13, cheiroslanguageo00chei_1_p150_c1, 0.4557), (14, cheiroslanguageo00chei_1_p146_c1, 0.4521), (15, cheiroslanguageo00chei_1_p154_c0, 0.4489), (16, cheiroslanguageo00chei_1_p148_c2, 0.4464), (17, cheiroslanguageo00chei_1_p146_c0, 0.4423), (18, cheiroslanguageo00chei_1_p146_c2, 0.4209), (19, cheiroslanguageo00chei_1_p149_c1, 0.4114), (20, cheiroslanguageo00chei_1_p153_c0, 0.4093), (21, cheiroslanguageo00chei_1_p145_c1, 0.4086), (22, cheiroslanguageo00chei_1_p147_c2, 0.3982), (23, cheiroslanguageo00chei_1_p154_c1, 0.3921), (24, cheiroslanguageo00chei_1_p155_c0, 0.3907), (25, cheiroslanguageo00chei_1_p151_c0, 0.389), (26, cheiroslanguageo00chei_1_p152_c1, 0.3724), (27, cheiroslanguageo00chei_1_p152_c0, 0.3553), (28, cheiroslanguageo00chei_1_p155_c1, 0.3123), (29, cheiroslanguageo00chei_1_p145_c2, 0.2804), (30, cheiroslanguageo00chei_1_p153_c2, 0.1865)]
  heart line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p160_c2, 0.6427), (2, cheiroslanguageo00chei_1_p161_c0, 0.6188), (3, cheiroslanguageo00chei_1_p159_c2, 0.6061), (4, cheiroslanguageo00chei_1_p159_c3, 0.6054), (5, cheiroslanguageo00chei_1_p156_c0, 0.5884), (6, cheiroslanguageo00chei_1_p160_c1, 0.557), (7, cheiroslanguageo00chei_1_p156_c1, 0.5494), (8, cheiroslanguageo00chei_1_p160_c3, 0.522), (9, cheiroslanguageo00chei_1_p160_c0, 0.4791), (10, cheiroslanguageo00chei_1_p159_c1, 0.4751), (11, cheiroslanguageo00chei_1_p159_c0, 0.3856), (12, cheiroslanguageo00chei_1_p156_c2, 0.3415)]
  life line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p139_c0, 0.6108), (2, cheiroslanguageo00chei_1_p134_c2, 0.5801), (3, cheiroslanguageo00chei_1_p134_c1, 0.5775), (4, cheiroslanguageo00chei_1_p135_c0, 0.5652), (5, cheiroslanguageo00chei_1_p139_c1, 0.5552), (6, cheiroslanguageo00chei_1_p138_c1, 0.5406), (7, cheiroslanguageo00chei_1_p135_c2, 0.5394), (8, cheiroslanguageo00chei_1_p136_c1, 0.5337), (9, cheiroslanguageo00chei_1_p136_c3, 0.5332), (10, cheiroslanguageo00chei_1_p134_c0, 0.5317), (11, cheiroslanguageo00chei_1_p135_c1, 0.5253), (12, cheiroslanguageo00chei_1_p137_c1, 0.5195), (13, cheiroslanguageo00chei_1_p136_c2, 0.5054), (14, cheiroslanguageo00chei_1_p137_c0, 0.5013), (15, cheiroslanguageo00chei_1_p138_c2, 0.4935), (16, cheiroslanguageo00chei_1_p138_c0, 0.466), (17, cheiroslanguageo00chei_1_p137_c3, 0.4625), (18, cheiroslanguageo00chei_1_p133_c0, 0.4477), (19, cheiroslanguageo00chei_1_p137_c2, 0.4165), (20, cheiroslanguageo00chei_1_p134_c3, 0.399), (21, cheiroslanguageo00chei_1_p136_c0, 0.3986), (22, cheiroslanguageo00chei_1_p133_c1, 0.177), (23, cheiroslanguageo00chei_1_p139_c2, 0.0862)]
  mount of venus: window=3 candidates=[(1, cheiroslanguageo00chei_1_p111_c1, 0.652), (2, cheiroslanguageo00chei_1_p112_c0, 0.6181), (3, cheiroslanguageo00chei_1_p113_c0, 0.497), (4, cheiroslanguageo00chei_1_p111_c0, 0.4856), (5, cheiroslanguageo00chei_1_p112_c1, 0.4774), (6, cheiroslanguageo00chei_1_p113_c1, 0.4747), (7, cheiroslanguageo00chei_1_p112_c2, 0.4245)]
  sun line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p166_c1, 0.5206), (2, cheiroslanguageo00chei_1_p166_c0, 0.5176), (3, cheiroslanguageo00chei_1_p169_c0, 0.5064), (4, cheiroslanguageo00chei_1_p169_c2, 0.478), (5, cheiroslanguageo00chei_1_p170_c0, 0.4632), (6, cheiroslanguageo00chei_1_p169_c1, 0.3619), (7, cheiroslanguageo00chei_1_p169_c3, 0.3531), (8, cheiroslanguageo00chei_1_p166_c2, 0.3499)]
  thumb: window=3 candidates=[(1, cheiroslanguageo00chei_1_p88_c0, 0.5569), (2, cheiroslanguageo00chei_1_p87_c0, 0.5513), (3, cheiroslanguageo00chei_1_p88_c1, 0.5327), (4, cheiroslanguageo00chei_1_p89_c2, 0.5322), (5, cheiroslanguageo00chei_1_p89_c0, 0.5226), (6, cheiroslanguageo00chei_1_p85_c0, 0.5033), (7, cheiroslanguageo00chei_1_p86_c0, 0.4837), (8, cheiroslanguageo00chei_1_p90_c2, 0.4443), (9, cheiroslanguageo00chei_1_p85_c1, 0.4043), (10, cheiroslanguageo00chei_1_p88_c2, 0.3724), (11, cheiroslanguageo00chei_1_p90_c0, 0.3615), (12, cheiroslanguageo00chei_1_p89_c1, 0.305), (13, cheiroslanguageo00chei_1_p90_c1, 0.2905), (14, cheiroslanguageo00chei_1_p87_c1, 0.0692)]

## RUN 2026-08-05T22:08:44.302441

### capture_reason
silence

### Confirmed descriptions
#### LEFT
HAND SHAPE: Elongated palm, overall build is medium.

FINGERS: Fingers are long relative to the palm, appear straight, with rounded fingertips, moderate spacing.

THUMB: Medium relative size, set moderately low, wide angle from the palm.

LIFE LINE: Present, deep, medium width, long, curves around the base of the thumb, no visible breaks, chains, forks, or islands.

HEAD LINE: Present, deep, medium width, long, slightly curved, no visible breaks, chains, forks, or islands.

HEART LINE: Present, deep, medium width, long, curves slightly upwards, no visible breaks, chains, forks, or islands.

FATE LINE: Barely visible.

OTHER LINES: No other lines clearly visible.

MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.

MARKS: No marks clearly visible.
#### RIGHT
HAND SHAPE: Square palm proportions, medium build.

FINGERS: Medium length relative to palm, straight, rounded fingertips, moderate spacing.

THUMB: Medium size, set moderately low, wide angle from the palm.

LIFE LINE: Present, deep, medium width, long, curves around the base of the thumb, no breaks/chains/forks/islands visible.

HEAD LINE: Present, deep, medium width, long, slightly curved, no breaks/chains/forks/islands visible.

HEART LINE: Present, deep, medium width, long, slightly curved, no breaks/chains/forks/islands visible.

FATE LINE: Barely visible.

OTHER LINES: Sun line visible, no health or marriage lines clearly visible.

MOUNTS: Mount of Venus appears developed, other mounts not clearly visible.

MARKS: No crosses, stars, grilles, squares, or moles clearly visible.

### reading_text


A note on what I have not interpreted: the classical texts I work from do not clearly address the following as they appear in your hands: life line, head line, heart line, fate line, sun line, thumb, fingers, mount of venus, mount of jupiter. Rather than guess, I have left these out of your reading.

For major life decisions, I recommend consulting a qualified astrologer or palm reader for a personal reading.

### READING (TAGGED)


### sources

### feature_support
supported_features: ('life line', 'head line', 'heart line', 'fate line', 'sun line', 'thumb', 'fingers', 'mount of venus')
unsupported_features: ('mount of jupiter',)

### claims_inventory
claims_inventory: EMPTY

### ring1_validation
passed: True
failures: ()
retry_used: False
stage1_retry_features: NONE
stage1_feature_diagnostics:
  _rules_engine: outcome=rules_engine_ok failed=False
    enabled_features: ['Line of Fate', 'Line of Head', 'Line of Heart', 'Line of Life', 'Line of Sun', 'Mount of Jupiter', 'Mount of Venus', 'Thumb']
    fired_rule_ids: []
    surviving_rule_ids: []
    suppression_log: []
    dropped_tokens: []
    phrase_promotions: []
    citations: {}
    dropped_rule_ids: []
    claim_features_outside_registry: []
    observation_record:
      Line of Fate: tokens={'Clarity': {'value': 'absent', 'confidence': 0.6}} unmapped=[] raw_prose="Barely visible. Barely visible."
      Line of Head: tokens={'Depth': {'value': 'deep', 'confidence': 0.6}, 'Width': {'value': 'medium', 'confidence': 0.6}, 'Length': {'value': 'long', 'confidence': 0.6}, 'Curve': {'value': 'curved', 'confidence': 0.6}, 'Continuity': {'value': 'unbroken', 'confidence': 0.6}} unmapped=[] raw_prose="Present, deep, medium width, long, slightly curved, no visible breaks, chains, forks, or islands. Present, deep, medium width, long, slightly curved, no breaks/chains/forks/islands visible."
      Line of Heart: tokens={'Depth': {'value': 'deep', 'confidence': 0.6}, 'Width': {'value': 'medium', 'confidence': 0.6}, 'Length': {'value': 'long', 'confidence': 0.6}, 'Curve': {'value': 'curved', 'confidence': 0.6}, 'Continuity': {'value': 'unbroken', 'confidence': 0.6}} unmapped=[] raw_prose="Present, deep, medium width, long, curves slightly upwards, no visible breaks, chains, forks, or islands. Present, deep, medium width, long, slightly curved, no breaks/chains/forks/islands visible."
      Line of Life: tokens={'Depth': {'value': 'deep', 'confidence': 1.0}, 'Width': {'value': 'medium', 'confidence': 1.0}, 'Length': {'value': 'long', 'confidence': 1.0}, 'Curve': {'value': 'curved', 'confidence': 1.0}, 'Continuity': {'value': 'unbroken', 'confidence': 1.0}} unmapped=[] raw_prose="Present, deep, medium width, long, curves around the base of the thumb, no visible breaks, chains, forks, or islands. Present, deep, medium width, long, curves around the base of the thumb, no breaks/..."
      Line of Sun: tokens={} unmapped=[{'quality': 'present', 'attribute_guess': 'Clarity'}] raw_prose="Sun line visible"
      Mount of Venus: tokens={'Development': {'value': 'developed', 'confidence': 1.0}} unmapped=[] raw_prose="Mount of Venus appears developed Mount of Venus appears developed"
      Thumb: tokens={'Setting': {'value': 'moderate', 'confidence': 1.0}, 'Angle': {'value': 'wide', 'confidence': 1.0}} unmapped=[{'quality': 'medium', 'attribute_guess': 'Size'}] raw_prose="Medium relative size, set moderately low, wide angle from the palm. Medium size, set moderately low, wide angle from the palm."
  fate line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  fingers: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  head line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  heart line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  life line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  markings/other features: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of jupiter: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of venus: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  sun line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  thumb: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
stage2_retry_used: False
stage2_first_attempt_failures: NONE
validation_failures: NONE
ring1_failures:
none

### near_miss_margin
  fate line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p165_c1, 0.6001), (2, cheiroslanguageo00chei_1_p163_c1, 0.5869), (3, cheiroslanguageo00chei_1_p165_c0, 0.5671), (4, cheiroslanguageo00chei_1_p163_c2, 0.561), (5, cheiroslanguageo00chei_1_p162_c0, 0.5515), (6, cheiroslanguageo00chei_1_p163_c0, 0.5486), (7, cheiroslanguageo00chei_1_p164_c1, 0.5336), (8, cheiroslanguageo00chei_1_p164_c2, 0.5165), (9, cheiroslanguageo00chei_1_p162_c1, 0.5081), (10, cheiroslanguageo00chei_1_p164_c0, 0.4756), (11, cheiroslanguageo00chei_1_p165_c2, 0.4595), (12, cheiroslanguageo00chei_1_p163_c3, 0.4594), (13, cheiroslanguageo00chei_1_p164_c3, 0.4225), (14, cheiroslanguageo00chei_1_p162_c2, 0.3622)]
  fingers: window=3 candidates=[(1, cheiroslanguageo00chei_1_p96_c0, 0.5164), (2, cheiroslanguageo00chei_1_p96_c2, 0.5117), (3, cheiroslanguageo00chei_1_p96_c1, 0.51), (4, cheiroslanguageo00chei_1_p95_c0, 0.4715), (5, cheiroslanguageo00chei_1_p97_c0, 0.4659), (6, cheiroslanguageo00chei_1_p96_c3, 0.4656), (7, cheiroslanguageo00chei_1_p95_c2, 0.447), (8, cheiroslanguageo00chei_1_p95_c1, 0.4451), (9, cheiroslanguageo00chei_1_p93_c0, 0.3858), (10, cheiroslanguageo00chei_1_p94_c0, 0.3716), (11, cheiroslanguageo00chei_1_p93_c1, 0.2714)]
  head line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p145_c0, 0.5589), (2, cheiroslanguageo00chei_1_p147_c1, 0.526), (3, cheiroslanguageo00chei_1_p151_c2, 0.5226), (4, cheiroslanguageo00chei_1_p147_c0, 0.5066), (5, cheiroslanguageo00chei_1_p148_c1, 0.4943), (6, cheiroslanguageo00chei_1_p148_c0, 0.4909), (7, cheiroslanguageo00chei_1_p150_c2, 0.4888), (8, cheiroslanguageo00chei_1_p147_c3, 0.4814), (9, cheiroslanguageo00chei_1_p151_c1, 0.4715), (10, cheiroslanguageo00chei_1_p149_c0, 0.4706), (11, cheiroslanguageo00chei_1_p153_c1, 0.4687), (12, cheiroslanguageo00chei_1_p150_c0, 0.4672), (13, cheiroslanguageo00chei_1_p150_c1, 0.4557), (14, cheiroslanguageo00chei_1_p146_c1, 0.4521), (15, cheiroslanguageo00chei_1_p154_c0, 0.4489), (16, cheiroslanguageo00chei_1_p148_c2, 0.4464), (17, cheiroslanguageo00chei_1_p146_c0, 0.4423), (18, cheiroslanguageo00chei_1_p146_c2, 0.4209), (19, cheiroslanguageo00chei_1_p149_c1, 0.4114), (20, cheiroslanguageo00chei_1_p153_c0, 0.4093), (21, cheiroslanguageo00chei_1_p145_c1, 0.4086), (22, cheiroslanguageo00chei_1_p147_c2, 0.3982), (23, cheiroslanguageo00chei_1_p154_c1, 0.3921), (24, cheiroslanguageo00chei_1_p155_c0, 0.3907), (25, cheiroslanguageo00chei_1_p151_c0, 0.389), (26, cheiroslanguageo00chei_1_p152_c1, 0.3724), (27, cheiroslanguageo00chei_1_p152_c0, 0.3553), (28, cheiroslanguageo00chei_1_p155_c1, 0.3123), (29, cheiroslanguageo00chei_1_p145_c2, 0.2804), (30, cheiroslanguageo00chei_1_p153_c2, 0.1865)]
  heart line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p160_c2, 0.6427), (2, cheiroslanguageo00chei_1_p161_c0, 0.6188), (3, cheiroslanguageo00chei_1_p159_c2, 0.6061), (4, cheiroslanguageo00chei_1_p159_c3, 0.6054), (5, cheiroslanguageo00chei_1_p156_c0, 0.5884), (6, cheiroslanguageo00chei_1_p160_c1, 0.557), (7, cheiroslanguageo00chei_1_p156_c1, 0.5494), (8, cheiroslanguageo00chei_1_p160_c3, 0.522), (9, cheiroslanguageo00chei_1_p160_c0, 0.4791), (10, cheiroslanguageo00chei_1_p159_c1, 0.4751), (11, cheiroslanguageo00chei_1_p159_c0, 0.3856), (12, cheiroslanguageo00chei_1_p156_c2, 0.3415)]
  life line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p139_c0, 0.6108), (2, cheiroslanguageo00chei_1_p134_c2, 0.5801), (3, cheiroslanguageo00chei_1_p134_c1, 0.5775), (4, cheiroslanguageo00chei_1_p135_c0, 0.5652), (5, cheiroslanguageo00chei_1_p139_c1, 0.5552), (6, cheiroslanguageo00chei_1_p138_c1, 0.5406), (7, cheiroslanguageo00chei_1_p135_c2, 0.5394), (8, cheiroslanguageo00chei_1_p136_c1, 0.5337), (9, cheiroslanguageo00chei_1_p136_c3, 0.5332), (10, cheiroslanguageo00chei_1_p134_c0, 0.5317), (11, cheiroslanguageo00chei_1_p135_c1, 0.5253), (12, cheiroslanguageo00chei_1_p137_c1, 0.5195), (13, cheiroslanguageo00chei_1_p136_c2, 0.5054), (14, cheiroslanguageo00chei_1_p137_c0, 0.5013), (15, cheiroslanguageo00chei_1_p138_c2, 0.4935), (16, cheiroslanguageo00chei_1_p138_c0, 0.466), (17, cheiroslanguageo00chei_1_p137_c3, 0.4625), (18, cheiroslanguageo00chei_1_p133_c0, 0.4477), (19, cheiroslanguageo00chei_1_p137_c2, 0.4165), (20, cheiroslanguageo00chei_1_p134_c3, 0.399), (21, cheiroslanguageo00chei_1_p136_c0, 0.3986), (22, cheiroslanguageo00chei_1_p133_c1, 0.177), (23, cheiroslanguageo00chei_1_p139_c2, 0.0862)]
  mount of venus: window=3 candidates=[(1, cheiroslanguageo00chei_1_p111_c1, 0.652), (2, cheiroslanguageo00chei_1_p112_c0, 0.6181), (3, cheiroslanguageo00chei_1_p113_c0, 0.497), (4, cheiroslanguageo00chei_1_p111_c0, 0.4856), (5, cheiroslanguageo00chei_1_p112_c1, 0.4774), (6, cheiroslanguageo00chei_1_p113_c1, 0.4747), (7, cheiroslanguageo00chei_1_p112_c2, 0.4245)]
  sun line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p166_c1, 0.5583), (2, cheiroslanguageo00chei_1_p166_c0, 0.5557), (3, cheiroslanguageo00chei_1_p169_c0, 0.5301), (4, cheiroslanguageo00chei_1_p170_c0, 0.5049), (5, cheiroslanguageo00chei_1_p169_c2, 0.4894), (6, cheiroslanguageo00chei_1_p166_c2, 0.3792), (7, cheiroslanguageo00chei_1_p169_c1, 0.3665), (8, cheiroslanguageo00chei_1_p169_c3, 0.3546)]
  thumb: window=3 candidates=[(1, cheiroslanguageo00chei_1_p88_c0, 0.5104), (2, cheiroslanguageo00chei_1_p87_c0, 0.5078), (3, cheiroslanguageo00chei_1_p88_c1, 0.5041), (4, cheiroslanguageo00chei_1_p89_c2, 0.5035), (5, cheiroslanguageo00chei_1_p89_c0, 0.4813), (6, cheiroslanguageo00chei_1_p86_c0, 0.4576), (7, cheiroslanguageo00chei_1_p85_c0, 0.4479), (8, cheiroslanguageo00chei_1_p90_c2, 0.426), (9, cheiroslanguageo00chei_1_p90_c0, 0.3723), (10, cheiroslanguageo00chei_1_p88_c2, 0.3636), (11, cheiroslanguageo00chei_1_p85_c1, 0.3588), (12, cheiroslanguageo00chei_1_p89_c1, 0.2875), (13, cheiroslanguageo00chei_1_p90_c1, 0.2682), (14, cheiroslanguageo00chei_1_p87_c1, 0.0836)]

## RUN 2026-08-05T22:09:59.701587

### capture_reason
silence

### Confirmed descriptions
#### LEFT
HAND SHAPE: Elongated palm, overall build is slender.

FINGERS: Long relative to palm, straight, rounded fingertips, moderate spacing.

THUMB: Medium size, set moderately low, wide angle from the palm.

LIFE LINE: Present, deep, narrow, long, curves around the base of the thumb, no clear breaks or forks.

HEAD LINE: Present, deep, narrow, long, slightly curved, no clear breaks or forks.

HEART LINE: Present, deep, narrow, long, slightly curved, no clear breaks or forks.

FATE LINE: Barely visible.

OTHER LINES: Not clearly visible.

MOUNTS: Mount of Venus appears developed, other mounts not clearly visible.

MARKS: Not clearly visible.
#### RIGHT
HAND SHAPE: Elongated palm, medium build

FINGERS: Medium length relative to palm, straight, rounded fingertips, moderate spacing

THUMB: Medium size, set moderately low, moderate angle from the palm

LIFE LINE: Present, moderately deep, medium width, long, curves around the base of the thumb, no clear breaks or forks

HEAD LINE: Present, moderately deep, medium width, long, slightly curved, no clear breaks or forks

HEART LINE: Present, moderately deep, medium width, long, slightly curved, no clear breaks or forks

FATE LINE: Barely visible

OTHER LINES: Not clearly visible

MOUNTS: Mount of Venus appears developed, others not clearly visible

MARKS: Not clearly visible

### reading_text
The life line on your palm is long, narrow, and deep, curving gracefully around the base of your thumb without any breaks or forks. This particular formation of the life line promises you a long life, accompanied by good health and vitality.

A note on what I have not interpreted: the classical texts I work from do not clearly address the following as they appear in your hands: head line, heart line, fate line, sun line, thumb, fingers, mount of venus, mount of jupiter. Rather than guess, I have left these out of your reading.

For major life decisions, I recommend consulting a qualified astrologer or palm reader for a personal reading.

### READING (TAGGED)
The life line on your palm is long, narrow, and deep, curving gracefully around the base of your thumb without any breaks or forks. [OBS] This particular formation of the life line promises you a long life, accompanied by good health and vitality. [C1]

### sources

### feature_support
supported_features: ('life line', 'head line', 'heart line', 'fate line', 'thumb', 'fingers', 'mount of venus')
unsupported_features: ('sun line', 'mount of jupiter')

### claims_inventory
C1 | life line | cheiroslanguageo00chei_1_p134_c0 | supports | False | None | None | A long, narrow, deep life line without irregularities promises long life, good health, and vitality.

### ring1_validation
passed: True
failures: ()
retry_used: False
stage1_retry_features: NONE
stage1_feature_diagnostics:
  _rules_engine: outcome=rules_engine_ok failed=False
    enabled_features: ['Line of Fate', 'Line of Head', 'Line of Heart', 'Line of Life', 'Line of Sun', 'Mount of Jupiter', 'Mount of Venus', 'Thumb']
    fired_rule_ids: ['L_001']
    surviving_rule_ids: ['L_001']
    suppression_log: []
    dropped_tokens: []
    phrase_promotions: []
    citations: {'C1': {'rule_id': 'L_001', 'chunk_id': 'cheiroslanguageo00chei_1_p134_c0', 'source_page': 134, 'source_quote': 'The line of life should be long, narrow, and deep, without irregularities, breaks, or crosses of any kind. Such a formation promises long life, good health, and vitality.', 'topic_group': 'line_life'}}
    dropped_rule_ids: []
    claim_features_outside_registry: []
    observation_record:
      Line of Fate: tokens={} unmapped=[] raw_prose="Barely visible. Barely visible"
      Line of Head: tokens={} unmapped=[] raw_prose="Present, deep, narrow, long, slightly curved, no clear breaks or forks. Present, moderately deep, medium width, long, slightly curved, no clear breaks or forks"
      Line of Heart: tokens={} unmapped=[] raw_prose="Present, deep, narrow, long, slightly curved, no clear breaks or forks. Present, moderately deep, medium width, long, slightly curved, no clear breaks or forks"
      Line of Life: tokens={'Depth': {'value': 'deep', 'confidence': 1.0}, 'Width': {'value': 'narrow', 'confidence': 1.0}, 'Length': {'value': 'long', 'confidence': 1.0}, 'Curve': {'value': 'curved', 'confidence': 1.0}, 'Continuity': {'value': 'unbroken', 'confidence': 1.0}} unmapped=[] raw_prose="Present, deep, narrow, long, curves around the base of the thumb, no clear breaks or forks. Present, moderately deep, medium width, long, curves around the base of the thumb, no clear breaks or forks"
      Mount of Venus: tokens={} unmapped=[] raw_prose="Mount of Venus appears developed Mount of Venus appears developed"
      Thumb: tokens={} unmapped=[] raw_prose="Medium size, set moderately low, wide angle from the palm. Medium size, set moderately low, moderate angle from the palm"
  fate line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  fingers: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  head line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  heart line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  life line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  markings/other features: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of jupiter: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of venus: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  sun line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  thumb: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
stage2_retry_used: False
stage2_first_attempt_failures: NONE
validation_failures: NONE
ring1_failures:
none

### near_miss_margin
  fate line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p165_c1, 0.6001), (2, cheiroslanguageo00chei_1_p163_c1, 0.5869), (3, cheiroslanguageo00chei_1_p165_c0, 0.5671), (4, cheiroslanguageo00chei_1_p163_c2, 0.561), (5, cheiroslanguageo00chei_1_p162_c0, 0.5515), (6, cheiroslanguageo00chei_1_p163_c0, 0.5486), (7, cheiroslanguageo00chei_1_p164_c1, 0.5336), (8, cheiroslanguageo00chei_1_p164_c2, 0.5165), (9, cheiroslanguageo00chei_1_p162_c1, 0.5081), (10, cheiroslanguageo00chei_1_p164_c0, 0.4756), (11, cheiroslanguageo00chei_1_p165_c2, 0.4595), (12, cheiroslanguageo00chei_1_p163_c3, 0.4594), (13, cheiroslanguageo00chei_1_p164_c3, 0.4225), (14, cheiroslanguageo00chei_1_p162_c2, 0.3622)]
  fingers: window=3 candidates=[(1, cheiroslanguageo00chei_1_p96_c0, 0.5206), (2, cheiroslanguageo00chei_1_p96_c1, 0.5129), (3, cheiroslanguageo00chei_1_p96_c2, 0.5115), (4, cheiroslanguageo00chei_1_p95_c0, 0.471), (5, cheiroslanguageo00chei_1_p96_c3, 0.4667), (6, cheiroslanguageo00chei_1_p97_c0, 0.4656), (7, cheiroslanguageo00chei_1_p95_c2, 0.4517), (8, cheiroslanguageo00chei_1_p95_c1, 0.4509), (9, cheiroslanguageo00chei_1_p93_c0, 0.3888), (10, cheiroslanguageo00chei_1_p94_c0, 0.375), (11, cheiroslanguageo00chei_1_p93_c1, 0.2712)]
  head line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p145_c0, 0.5464), (2, cheiroslanguageo00chei_1_p151_c2, 0.4992), (3, cheiroslanguageo00chei_1_p148_c1, 0.4934), (4, cheiroslanguageo00chei_1_p147_c1, 0.4889), (5, cheiroslanguageo00chei_1_p150_c2, 0.4877), (6, cheiroslanguageo00chei_1_p147_c0, 0.4838), (7, cheiroslanguageo00chei_1_p147_c3, 0.4693), (8, cheiroslanguageo00chei_1_p149_c0, 0.4688), (9, cheiroslanguageo00chei_1_p151_c1, 0.4628), (10, cheiroslanguageo00chei_1_p146_c1, 0.4554), (11, cheiroslanguageo00chei_1_p153_c1, 0.4476), (12, cheiroslanguageo00chei_1_p150_c1, 0.4472), (13, cheiroslanguageo00chei_1_p148_c0, 0.4452), (14, cheiroslanguageo00chei_1_p150_c0, 0.4437), (15, cheiroslanguageo00chei_1_p148_c2, 0.441), (16, cheiroslanguageo00chei_1_p154_c0, 0.4247), (17, cheiroslanguageo00chei_1_p146_c0, 0.4178), (18, cheiroslanguageo00chei_1_p146_c2, 0.4018), (19, cheiroslanguageo00chei_1_p153_c0, 0.3958), (20, cheiroslanguageo00chei_1_p145_c1, 0.3952), (21, cheiroslanguageo00chei_1_p149_c1, 0.3942), (22, cheiroslanguageo00chei_1_p155_c0, 0.3745), (23, cheiroslanguageo00chei_1_p151_c0, 0.3721), (24, cheiroslanguageo00chei_1_p147_c2, 0.371), (25, cheiroslanguageo00chei_1_p154_c1, 0.3645), (26, cheiroslanguageo00chei_1_p152_c1, 0.3601), (27, cheiroslanguageo00chei_1_p152_c0, 0.3346), (28, cheiroslanguageo00chei_1_p145_c2, 0.2988), (29, cheiroslanguageo00chei_1_p155_c1, 0.2786), (30, cheiroslanguageo00chei_1_p153_c2, 0.1997)]
  heart line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p160_c2, 0.6271), (2, cheiroslanguageo00chei_1_p159_c3, 0.6102), (3, cheiroslanguageo00chei_1_p161_c0, 0.6089), (4, cheiroslanguageo00chei_1_p159_c2, 0.584), (5, cheiroslanguageo00chei_1_p156_c0, 0.5798), (6, cheiroslanguageo00chei_1_p160_c1, 0.5508), (7, cheiroslanguageo00chei_1_p156_c1, 0.5382), (8, cheiroslanguageo00chei_1_p160_c3, 0.5246), (9, cheiroslanguageo00chei_1_p159_c1, 0.4773), (10, cheiroslanguageo00chei_1_p160_c0, 0.4426), (11, cheiroslanguageo00chei_1_p159_c0, 0.3762), (12, cheiroslanguageo00chei_1_p156_c2, 0.3282)]
  life line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p139_c0, 0.634), (2, cheiroslanguageo00chei_1_p134_c2, 0.5939), (3, cheiroslanguageo00chei_1_p135_c0, 0.583), (4, cheiroslanguageo00chei_1_p134_c1, 0.5803), (5, cheiroslanguageo00chei_1_p139_c1, 0.5788), (6, cheiroslanguageo00chei_1_p135_c2, 0.5465), (7, cheiroslanguageo00chei_1_p136_c3, 0.5359), (8, cheiroslanguageo00chei_1_p136_c1, 0.5353), (9, cheiroslanguageo00chei_1_p138_c1, 0.5301), (10, cheiroslanguageo00chei_1_p136_c2, 0.5288), (11, cheiroslanguageo00chei_1_p135_c1, 0.5212), (12, cheiroslanguageo00chei_1_p137_c0, 0.5198), (13, cheiroslanguageo00chei_1_p134_c0, 0.5192), (14, cheiroslanguageo00chei_1_p137_c1, 0.5164), (15, cheiroslanguageo00chei_1_p138_c2, 0.5108), (16, cheiroslanguageo00chei_1_p137_c3, 0.4764), (17, cheiroslanguageo00chei_1_p133_c0, 0.4655), (18, cheiroslanguageo00chei_1_p138_c0, 0.4597), (19, cheiroslanguageo00chei_1_p134_c3, 0.4161), (20, cheiroslanguageo00chei_1_p137_c2, 0.4113), (21, cheiroslanguageo00chei_1_p136_c0, 0.395), (22, cheiroslanguageo00chei_1_p133_c1, 0.1764), (23, cheiroslanguageo00chei_1_p139_c2, 0.1073)]
  mount of venus: window=3 candidates=[(1, cheiroslanguageo00chei_1_p111_c1, 0.652), (2, cheiroslanguageo00chei_1_p112_c0, 0.6181), (3, cheiroslanguageo00chei_1_p113_c0, 0.497), (4, cheiroslanguageo00chei_1_p111_c0, 0.4856), (5, cheiroslanguageo00chei_1_p112_c1, 0.4774), (6, cheiroslanguageo00chei_1_p113_c1, 0.4747), (7, cheiroslanguageo00chei_1_p112_c2, 0.4245)]
  thumb: window=3 candidates=[(1, cheiroslanguageo00chei_1_p88_c0, 0.5569), (2, cheiroslanguageo00chei_1_p87_c0, 0.5513), (3, cheiroslanguageo00chei_1_p88_c1, 0.5327), (4, cheiroslanguageo00chei_1_p89_c2, 0.5322), (5, cheiroslanguageo00chei_1_p89_c0, 0.5226), (6, cheiroslanguageo00chei_1_p85_c0, 0.5033), (7, cheiroslanguageo00chei_1_p86_c0, 0.4837), (8, cheiroslanguageo00chei_1_p90_c2, 0.4443), (9, cheiroslanguageo00chei_1_p85_c1, 0.4043), (10, cheiroslanguageo00chei_1_p88_c2, 0.3724), (11, cheiroslanguageo00chei_1_p90_c0, 0.3615), (12, cheiroslanguageo00chei_1_p89_c1, 0.305), (13, cheiroslanguageo00chei_1_p90_c1, 0.2905), (14, cheiroslanguageo00chei_1_p87_c1, 0.0692)]

## RUN 2026-08-06T10:34:47.828365

### capture_reason
silence

### Confirmed descriptions
#### LEFT
HAND SHAPE: Square palm, overall build is robust.

FINGERS: Fingers are long relative to the palm, appear straight, with rounded fingertips, and moderate spacing.

THUMB: Medium relative size, set moderately low, wide angle from the palm.

LIFE LINE: Present, deep, narrow, long, curves around the base of the thumb, no breaks, chains, forks, or islands visible.

HEAD LINE: Present, deep, narrow, long, slightly sloping downward toward the wrist, no breaks, chains, forks, or islands visible.

HEART LINE: Present, deep, narrow, long, curves slightly upward, no breaks, chains, forks, or islands visible.

FATE LINE: Barely visible.

OTHER LINES: No other lines clearly visible.

MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.

MARKS: No marks clearly visible.
#### RIGHT
HAND SHAPE: Square palm proportions, medium build.

FINGERS: Fingers are of medium length relative to the palm, appear straight, with rounded fingertips, and moderate spacing.

THUMB: Medium relative size, set moderately low, wide angle from the palm.

LIFE LINE: Present, deep, medium width, long, curves around the base of the thumb, no clear breaks, chains, forks, or islands visible.

HEAD LINE: Present, deep, medium width, long, slightly sloping downward toward the wrist, no clear breaks, chains, forks, or islands visible.

HEART LINE: Present, deep, medium width, long, curves slightly upward, no clear breaks, chains, forks, or islands visible.

FATE LINE: Barely visible.

OTHER LINES: No other lines clearly visible.

MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.

MARKS: No marks such as crosses, stars, grilles, squares, or moles clearly visible.

### reading_text
The life line on your palm is long, narrow, and deep, curving gracefully around the base of your thumb without any breaks, chains, forks, or islands. This line promises you a long life, accompanied by good health and vitality.

Your head line is also present, deep, and long, with a slight slope downward toward the wrist. It is free of any breaks, chains, forks, or islands. The heart line mirrors this pattern, being deep, narrow, and long, with a gentle upward curve and no visible irregularities.

The fate line, however, is barely visible. Your thumb is of medium size, set moderately low, and opens at a wide angle from the palm. Your fingers are long relative to the palm, straight, with rounded fingertips and moderate spacing.

The Mount of Venus appears developed, indicating a capacity for warmth and affection. There are no marks such as crosses, stars, grilles, squares, or moles clearly visible on your palm.

A note on what I have not interpreted: the classical texts I work from do not clearly address the following as they appear in your hands: head line, heart line, fate line, sun line, thumb, fingers, mount of venus, mount of jupiter, markings and other features. Rather than guess, I have left these out of your reading.

For major life decisions, I recommend consulting a qualified astrologer or palm reader for a personal reading.

### READING (TAGGED)
The life line on your palm is long, narrow, and deep, curving gracefully around the base of your thumb without any breaks, chains, forks, or islands. [OBS] This line promises you a long life, accompanied by good health and vitality. [C1]

Your head line is also present, deep, and long, with a slight slope downward toward the wrist. It is free of any breaks, chains, forks, or islands. [OBS] The heart line mirrors this pattern, being deep, narrow, and long, with a gentle upward curve and no visible irregularities. [OBS]

The fate line, however, is barely visible. [OBS] Your thumb is of medium size, set moderately low, and opens at a wide angle from the palm. [OBS] Your fingers are long relative to the palm, straight, with rounded fingertips and moderate spacing. [OBS]

The Mount of Venus appears developed, indicating a capacity for warmth and affection. [OBS] There are no marks such as crosses, stars, grilles, squares, or moles clearly visible on your palm. [OBS]

### sources

### feature_support
supported_features: ('life line', 'head line', 'heart line', 'fate line', 'thumb', 'fingers', 'mount of venus', 'markings/other features')
unsupported_features: ('sun line', 'mount of jupiter')

### claims_inventory
C1 | life line | cheiroslanguageo00chei_1_p134_c0 | supports | False | None | None | A long, narrow, deep life line without irregularities promises long life, good health, and vitality.

### ring1_validation
passed: True
failures: ()
retry_used: False
stage1_retry_features: NONE
stage1_feature_diagnostics:
  _rules_engine: outcome=rules_engine_ok failed=False
    enabled_features: ['Line of Fate', 'Line of Head', 'Line of Heart', 'Line of Life', 'Line of Sun', 'Mount of Jupiter', 'Mount of Venus', 'Thumb']
    fired_rule_ids: ['L_001']
    surviving_rule_ids: ['L_001']
    suppression_log: []
    dropped_tokens: []
    phrase_promotions: []
    citations: {'C1': {'rule_id': 'L_001', 'chunk_id': 'cheiroslanguageo00chei_1_p134_c0', 'source_page': 134, 'source_quote': 'The line of life should be long, narrow, and deep, without irregularities, breaks, or crosses of any kind. Such a formation promises long life, good health, and vitality.', 'topic_group': 'line_life'}}
    dropped_rule_ids: []
    claim_features_outside_registry: []
    observation_record:
      Line of Fate: tokens={} unmapped=[{'quality': 'Barely visible', 'attribute_guess': 'Clarity'}] raw_prose="Barely visible. Barely visible."
      Line of Head: tokens={'Depth': {'value': 'deep', 'confidence': 0.6}, 'Width': {'value': 'narrow', 'confidence': 0.6}, 'Length': {'value': 'long', 'confidence': 0.6}, 'Slope': {'value': 'downward', 'confidence': 0.6}, 'Continuity': {'value': 'unbroken', 'confidence': 0.6}} unmapped=[{'quality': 'no breaks, chains, forks, or islands visible', 'attribute_guess': 'Continuity'}, {'quality': 'no clear breaks, chains, forks, or islands visible', 'attribute_guess': 'Continuity'}] raw_prose="Present, deep, narrow, long, slightly sloping downward toward the wrist, no breaks, chains, forks, or islands visible. Present, deep, medium width, long, slightly sloping downward toward the wrist, no..."
      Line of Heart: tokens={'Depth': {'value': 'deep', 'confidence': 0.6}, 'Width': {'value': 'narrow', 'confidence': 0.6}, 'Length': {'value': 'long', 'confidence': 0.6}, 'Curve': {'value': 'curved', 'confidence': 0.6}, 'Continuity': {'value': 'unbroken', 'confidence': 0.6}} unmapped=[{'quality': 'no breaks, chains, forks, or islands visible', 'attribute_guess': 'Continuity'}, {'quality': 'no clear breaks, chains, forks, or islands visible', 'attribute_guess': 'Continuity'}] raw_prose="Present, deep, narrow, long, curves slightly upward, no breaks, chains, forks, or islands visible. Present, deep, medium width, long, curves slightly upward, no clear breaks, chains, forks, or islands..."
      Line of Life: tokens={'Depth': {'value': 'deep', 'confidence': 1.0}, 'Width': {'value': 'narrow', 'confidence': 1.0}, 'Length': {'value': 'long', 'confidence': 1.0}, 'Curve': {'value': 'curved', 'confidence': 1.0}, 'Continuity': {'value': 'unbroken', 'confidence': 1.0}} unmapped=[{'quality': 'no breaks, chains, forks, or islands visible', 'attribute_guess': 'Continuity'}, {'quality': 'no clear breaks, chains, forks, or islands visible', 'attribute_guess': 'Continuity'}] raw_prose="Present, deep, narrow, long, curves around the base of the thumb, no breaks, chains, forks, or islands visible. Present, deep, medium width, long, curves around the base of the thumb, no clear breaks,..."
      Mount of Venus: tokens={'Development': {'value': 'developed', 'confidence': 1.0}} unmapped=[{'quality': 'Mount of Venus appears developed', 'attribute_guess': 'Development'}] raw_prose="Mount of Venus appears developed Mount of Venus appears developed"
      Thumb: tokens={'Angle': {'value': 'wide', 'confidence': 1.0}} unmapped=[{'quality': 'medium', 'attribute_guess': 'Size'}, {'quality': 'moderately low', 'attribute_guess': 'Setting'}, {'quality': 'wide angle from the palm', 'attribute_guess': 'Angle'}] raw_prose="Medium relative size, set moderately low, wide angle from the palm. Medium relative size, set moderately low, wide angle from the palm."
  fate line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  fingers: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  head line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  heart line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  life line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  markings/other features: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of jupiter: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of venus: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  sun line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  thumb: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
stage2_retry_used: False
stage2_first_attempt_failures: NONE
validation_failures: NONE
ring1_failures:
none

### near_miss_margin
  fate line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p165_c1, 0.6001), (2, cheiroslanguageo00chei_1_p163_c1, 0.5869), (3, cheiroslanguageo00chei_1_p165_c0, 0.5671), (4, cheiroslanguageo00chei_1_p163_c2, 0.561), (5, cheiroslanguageo00chei_1_p162_c0, 0.5515), (6, cheiroslanguageo00chei_1_p163_c0, 0.5486), (7, cheiroslanguageo00chei_1_p164_c1, 0.5336), (8, cheiroslanguageo00chei_1_p164_c2, 0.5165), (9, cheiroslanguageo00chei_1_p162_c1, 0.5081), (10, cheiroslanguageo00chei_1_p164_c0, 0.4756), (11, cheiroslanguageo00chei_1_p165_c2, 0.4595), (12, cheiroslanguageo00chei_1_p163_c3, 0.4594), (13, cheiroslanguageo00chei_1_p164_c3, 0.4225), (14, cheiroslanguageo00chei_1_p162_c2, 0.3622)]
  fingers: window=3 candidates=[(1, cheiroslanguageo00chei_1_p96_c0, 0.5318), (2, cheiroslanguageo00chei_1_p96_c1, 0.5234), (3, cheiroslanguageo00chei_1_p96_c2, 0.5208), (4, cheiroslanguageo00chei_1_p97_c0, 0.4866), (5, cheiroslanguageo00chei_1_p95_c0, 0.4847), (6, cheiroslanguageo00chei_1_p96_c3, 0.4781), (7, cheiroslanguageo00chei_1_p95_c1, 0.4629), (8, cheiroslanguageo00chei_1_p95_c2, 0.4584), (9, cheiroslanguageo00chei_1_p93_c0, 0.4036), (10, cheiroslanguageo00chei_1_p94_c0, 0.3903), (11, cheiroslanguageo00chei_1_p93_c1, 0.291)]
  head line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p145_c0, 0.5589), (2, cheiroslanguageo00chei_1_p147_c1, 0.526), (3, cheiroslanguageo00chei_1_p151_c2, 0.5226), (4, cheiroslanguageo00chei_1_p147_c0, 0.5066), (5, cheiroslanguageo00chei_1_p148_c1, 0.4943), (6, cheiroslanguageo00chei_1_p148_c0, 0.4909), (7, cheiroslanguageo00chei_1_p150_c2, 0.4888), (8, cheiroslanguageo00chei_1_p147_c3, 0.4814), (9, cheiroslanguageo00chei_1_p151_c1, 0.4715), (10, cheiroslanguageo00chei_1_p149_c0, 0.4706), (11, cheiroslanguageo00chei_1_p153_c1, 0.4687), (12, cheiroslanguageo00chei_1_p150_c0, 0.4672), (13, cheiroslanguageo00chei_1_p150_c1, 0.4557), (14, cheiroslanguageo00chei_1_p146_c1, 0.4521), (15, cheiroslanguageo00chei_1_p154_c0, 0.4489), (16, cheiroslanguageo00chei_1_p148_c2, 0.4464), (17, cheiroslanguageo00chei_1_p146_c0, 0.4423), (18, cheiroslanguageo00chei_1_p146_c2, 0.4209), (19, cheiroslanguageo00chei_1_p149_c1, 0.4114), (20, cheiroslanguageo00chei_1_p153_c0, 0.4093), (21, cheiroslanguageo00chei_1_p145_c1, 0.4086), (22, cheiroslanguageo00chei_1_p147_c2, 0.3982), (23, cheiroslanguageo00chei_1_p154_c1, 0.3921), (24, cheiroslanguageo00chei_1_p155_c0, 0.3907), (25, cheiroslanguageo00chei_1_p151_c0, 0.389), (26, cheiroslanguageo00chei_1_p152_c1, 0.3724), (27, cheiroslanguageo00chei_1_p152_c0, 0.3553), (28, cheiroslanguageo00chei_1_p155_c1, 0.3123), (29, cheiroslanguageo00chei_1_p145_c2, 0.2804), (30, cheiroslanguageo00chei_1_p153_c2, 0.1865)]
  heart line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p160_c2, 0.6427), (2, cheiroslanguageo00chei_1_p161_c0, 0.6188), (3, cheiroslanguageo00chei_1_p159_c2, 0.6061), (4, cheiroslanguageo00chei_1_p159_c3, 0.6054), (5, cheiroslanguageo00chei_1_p156_c0, 0.5884), (6, cheiroslanguageo00chei_1_p160_c1, 0.557), (7, cheiroslanguageo00chei_1_p156_c1, 0.5494), (8, cheiroslanguageo00chei_1_p160_c3, 0.522), (9, cheiroslanguageo00chei_1_p160_c0, 0.4791), (10, cheiroslanguageo00chei_1_p159_c1, 0.4751), (11, cheiroslanguageo00chei_1_p159_c0, 0.3856), (12, cheiroslanguageo00chei_1_p156_c2, 0.3415)]
  life line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p139_c0, 0.6108), (2, cheiroslanguageo00chei_1_p134_c2, 0.5801), (3, cheiroslanguageo00chei_1_p134_c1, 0.5775), (4, cheiroslanguageo00chei_1_p135_c0, 0.5652), (5, cheiroslanguageo00chei_1_p139_c1, 0.5552), (6, cheiroslanguageo00chei_1_p138_c1, 0.5406), (7, cheiroslanguageo00chei_1_p135_c2, 0.5394), (8, cheiroslanguageo00chei_1_p136_c1, 0.5337), (9, cheiroslanguageo00chei_1_p136_c3, 0.5332), (10, cheiroslanguageo00chei_1_p134_c0, 0.5317), (11, cheiroslanguageo00chei_1_p135_c1, 0.5253), (12, cheiroslanguageo00chei_1_p137_c1, 0.5195), (13, cheiroslanguageo00chei_1_p136_c2, 0.5054), (14, cheiroslanguageo00chei_1_p137_c0, 0.5013), (15, cheiroslanguageo00chei_1_p138_c2, 0.4935), (16, cheiroslanguageo00chei_1_p138_c0, 0.466), (17, cheiroslanguageo00chei_1_p137_c3, 0.4625), (18, cheiroslanguageo00chei_1_p133_c0, 0.4477), (19, cheiroslanguageo00chei_1_p137_c2, 0.4165), (20, cheiroslanguageo00chei_1_p134_c3, 0.399), (21, cheiroslanguageo00chei_1_p136_c0, 0.3986), (22, cheiroslanguageo00chei_1_p133_c1, 0.177), (23, cheiroslanguageo00chei_1_p139_c2, 0.0862)]
  markings/other features: window=3 candidates=[(1, cheiroslanguageo00chei_1_p155_c1, 0.4323), (2, cheiroslanguageo00chei_1_p180_c2, 0.4175), (3, cheiroslanguageo00chei_1_p200_c1, 0.4097), (4, cheiroslanguageo00chei_1_p127_c1, 0.396), (5, cheiroslanguageo00chei_1_p160_c2, 0.3924), (6, cheiroslanguageo00chei_1_p207_c1, 0.3825), (7, cheiroslanguageo00chei_1_p172_c1, 0.3815), (8, cheiroslanguageo00chei_1_p148_c1, 0.3789), (9, cheiroslanguageo00chei_1_p187_c2, 0.3772), (10, cheiroslanguageo00chei_1_p137_c1, 0.3765), (11, cheiroslanguageo00chei_1_p198_c1, 0.3672), (12, cheiroslanguageo00chei_1_p152_c1, 0.3652), (13, cheiroslanguageo00chei_1_p208_c1, 0.3592), (14, cheiroslanguageo00chei_1_p197_c0, 0.3565), (15, cheiroslanguageo00chei_1_p161_c0, 0.3534), (16, cheiroslanguageo00chei_1_p170_c0, 0.3448), (17, cheiroslanguageo00chei_1_p209_c0, 0.3418), (18, cheiroslanguageo00chei_1_p128_c1, 0.3417), (19, cheiroslanguageo00chei_1_p124_c0, 0.3392), (20, cheiroslanguageo00chei_1_p165_c1, 0.3371), (21, cheiroslanguageo00chei_1_p20_c0, 0.3368), (22, cheiroslanguageo00chei_1_p179_c1, 0.3364), (23, cheiroslanguageo00chei_1_p183_c2, 0.336), (24, cheiroslanguageo00chei_1_p159_c3, 0.3339), (25, cheiroslanguageo00chei_1_p198_c2, 0.333), (26, cheiroslanguageo00chei_1_p192_c0, 0.3322), (27, cheiroslanguageo00chei_1_p135_c0, 0.3317), (28, cheiroslanguageo00chei_1_p34_c0, 0.3296), (29, cheiroslanguageo00chei_1_p128_c0, 0.3279), (30, cheiroslanguageo00chei_1_p184_c0, 0.3274)]
  mount of venus: window=3 candidates=[(1, cheiroslanguageo00chei_1_p111_c1, 0.652), (2, cheiroslanguageo00chei_1_p112_c0, 0.6181), (3, cheiroslanguageo00chei_1_p113_c0, 0.497), (4, cheiroslanguageo00chei_1_p111_c0, 0.4856), (5, cheiroslanguageo00chei_1_p112_c1, 0.4774), (6, cheiroslanguageo00chei_1_p113_c1, 0.4747), (7, cheiroslanguageo00chei_1_p112_c2, 0.4245)]
  thumb: window=3 candidates=[(1, cheiroslanguageo00chei_1_p87_c0, 0.5493), (2, cheiroslanguageo00chei_1_p88_c0, 0.5466), (3, cheiroslanguageo00chei_1_p88_c1, 0.5414), (4, cheiroslanguageo00chei_1_p89_c2, 0.5381), (5, cheiroslanguageo00chei_1_p89_c0, 0.5179), (6, cheiroslanguageo00chei_1_p86_c0, 0.5049), (7, cheiroslanguageo00chei_1_p85_c0, 0.5001), (8, cheiroslanguageo00chei_1_p90_c2, 0.465), (9, cheiroslanguageo00chei_1_p85_c1, 0.3976), (10, cheiroslanguageo00chei_1_p90_c0, 0.3941), (11, cheiroslanguageo00chei_1_p88_c2, 0.3907), (12, cheiroslanguageo00chei_1_p89_c1, 0.3073), (13, cheiroslanguageo00chei_1_p90_c1, 0.2914), (14, cheiroslanguageo00chei_1_p87_c1, 0.0875)]

## RUN 2026-08-06T10:35:51.326824

### capture_reason
silence

### Confirmed descriptions
#### LEFT
HAND SHAPE: Elongated palm, medium build.

FINGERS: Long relative to palm, straight, rounded fingertips, moderate spacing.

THUMB: Medium size, set moderately low, wide angle from the palm.

LIFE LINE: Present, deep, narrow, long, curves around the base of the thumb, no clear breaks or forks.

HEAD LINE: Present, deep, narrow, medium length, slightly sloping downward, originates close to the life line, no clear breaks or forks.

HEART LINE: Present, deep, narrow, long, curves slightly upward, no clear breaks or forks.

FATE LINE: Barely visible.

OTHER LINES: Not clearly visible.

MOUNTS: Mount of Venus appears developed, other mounts not clearly visible.

MARKS: Not clearly visible.
#### RIGHT
HAND SHAPE: elongated palm, slender build

FINGERS: long relative to palm, straight, rounded fingertips, moderate spacing

THUMB: medium size, low set, moderate angle from the palm

LIFE LINE: present, deep, narrow, long, curves around the base of the thumb, no breaks/chains/forks/islands clearly visible

HEAD LINE: present, deep, narrow, long, slightly sloping downward, originates close to the life line, no breaks/chains/forks/islands clearly visible

HEART LINE: present, deep, narrow, long, curves slightly upward, ends under the index finger, no breaks/chains/forks/islands clearly visible

FATE LINE: not clearly visible

OTHER LINES: no other lines clearly visible

MOUNTS: Mount of Venus appears developed, other mounts unremarkable

MARKS: no marks clearly visible

### reading_text
The life line on your palm is long, narrow, and deep, curving gracefully around the base of your thumb without any breaks or irregularities. This configuration promises you a long life, accompanied by good health and vitality.

Your head line is also present, deep, and narrow, with a medium length and a slight downward slope. It originates close to the life line and remains unbroken.

The heart line is similarly deep, narrow, and long, curving slightly upward and ending under the index finger without any visible breaks.

The fate line, however, is barely visible on your palm.

Your thumb is of medium size, set moderately low, and extends at a wide angle from the palm. Your fingers are long relative to your palm, straight, with rounded fingertips and moderate spacing between them.

Lastly, the Mount of Venus on your palm appears developed.

A note on what I have not interpreted: the classical texts I work from do not clearly address the following as they appear in your hands: head line, heart line, fate line, sun line, thumb, fingers, mount of venus, mount of jupiter. Rather than guess, I have left these out of your reading.

For major life decisions, I recommend consulting a qualified astrologer or palm reader for a personal reading.

### READING (TAGGED)
The life line on your palm is long, narrow, and deep, curving gracefully around the base of your thumb without any breaks or irregularities. [OBS] This configuration promises you a long life, accompanied by good health and vitality. [C1]

Your head line is also present, deep, and narrow, with a medium length and a slight downward slope. It originates close to the life line and remains unbroken. [OBS] 

The heart line is similarly deep, narrow, and long, curving slightly upward and ending under the index finger without any visible breaks. [OBS]

The fate line, however, is barely visible on your palm. [OBS]

Your thumb is of medium size, set moderately low, and extends at a wide angle from the palm. [OBS] Your fingers are long relative to your palm, straight, with rounded fingertips and moderate spacing between them. [OBS]

Lastly, the Mount of Venus on your palm appears developed. [OBS]

### sources

### feature_support
supported_features: ('life line', 'head line', 'heart line', 'fate line', 'thumb', 'fingers', 'mount of venus')
unsupported_features: ('sun line', 'mount of jupiter')

### claims_inventory
C1 | life line | cheiroslanguageo00chei_1_p134_c0 | supports | False | None | None | A long, narrow, deep life line without irregularities promises long life, good health, and vitality.

### ring1_validation
passed: True
failures: ()
retry_used: False
stage1_retry_features: NONE
stage1_feature_diagnostics:
  _rules_engine: outcome=rules_engine_ok failed=False
    enabled_features: ['Line of Fate', 'Line of Head', 'Line of Heart', 'Line of Life', 'Line of Sun', 'Mount of Jupiter', 'Mount of Venus', 'Thumb']
    fired_rule_ids: ['L_001']
    surviving_rule_ids: ['L_001']
    suppression_log: []
    dropped_tokens: []
    phrase_promotions: []
    citations: {'C1': {'rule_id': 'L_001', 'chunk_id': 'cheiroslanguageo00chei_1_p134_c0', 'source_page': 134, 'source_quote': 'The line of life should be long, narrow, and deep, without irregularities, breaks, or crosses of any kind. Such a formation promises long life, good health, and vitality.', 'topic_group': 'line_life'}}
    dropped_rule_ids: []
    claim_features_outside_registry: []
    observation_record:
      Line of Fate: tokens={} unmapped=[{'quality': 'Barely visible.', 'attribute_guess': 'Clarity'}] raw_prose="Barely visible. not clearly visible"
      Line of Head: tokens={'Depth': {'value': 'deep', 'confidence': 0.6}, 'Length': {'value': 'medium', 'confidence': 0.6}, 'Curve': {'value': 'sloping', 'confidence': 0.6}, 'Clarity': {'value': 'clear', 'confidence': 0.6}, 'Thickness': {'value': 'narrow', 'confidence': 0.6}, 'Continuity': {'value': 'unbroken', 'confidence': 0.6}, 'Position': {'value': 'close', 'confidence': 0.6}, 'Slope': {'value': 'downward', 'confidence': 0.6}} unmapped=[] raw_prose="Present, deep, narrow, medium length, slightly sloping downward, originates close to the life line, no clear breaks or forks. present, deep, narrow, long, slightly sloping downward, originates close t..."
      Line of Heart: tokens={'Depth': {'value': 'deep', 'confidence': 0.6}, 'Length': {'value': 'long', 'confidence': 0.6}, 'Curve': {'value': 'curved', 'confidence': 0.6}, 'Clarity': {'value': 'clear', 'confidence': 0.6}, 'Thickness': {'value': 'narrow', 'confidence': 0.6}, 'Continuity': {'value': 'unbroken', 'confidence': 0.6}} unmapped=[{'quality': 'under_index_finger', 'attribute_guess': 'Ending_Point'}] raw_prose="Present, deep, narrow, long, curves slightly upward, no clear breaks or forks. present, deep, narrow, long, curves slightly upward, ends under the index finger, no breaks/chains/forks/islands clearly ..."
      Line of Life: tokens={'Depth': {'value': 'deep', 'confidence': 1.0}, 'Length': {'value': 'long', 'confidence': 1.0}, 'Curve': {'value': 'curved', 'confidence': 1.0}, 'Clarity': {'value': 'clear', 'confidence': 1.0}, 'Thickness': {'value': 'narrow', 'confidence': 1.0}, 'Continuity': {'value': 'unbroken', 'confidence': 1.0}, 'Width': {'value': 'narrow', 'confidence': 1.0}} unmapped=[] raw_prose="Present, deep, narrow, long, curves around the base of the thumb, no clear breaks or forks. present, deep, narrow, long, curves around the base of the thumb, no breaks/chains/forks/islands clearly vis..."
      Mount of Venus: tokens={'Development': {'value': 'developed', 'confidence': 1.0}} unmapped=[] raw_prose="Mount of Venus appears developed Mount of Venus appears developed"
      Thumb: tokens={'Length': {'value': 'medium', 'confidence': 1.0}, 'Setting': {'value': 'low', 'confidence': 1.0}, 'Angle': {'value': 'moderate', 'confidence': 1.0}} unmapped=[] raw_prose="Medium size, set moderately low, wide angle from the palm. medium size, low set, moderate angle from the palm"
  fate line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  fingers: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  head line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  heart line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  life line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  markings/other features: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of jupiter: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of venus: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  sun line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  thumb: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
stage2_retry_used: False
stage2_first_attempt_failures: NONE
validation_failures: NONE
ring1_failures:
none

### near_miss_margin
  fate line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p165_c1, 0.6001), (2, cheiroslanguageo00chei_1_p163_c1, 0.5869), (3, cheiroslanguageo00chei_1_p165_c0, 0.5671), (4, cheiroslanguageo00chei_1_p163_c2, 0.561), (5, cheiroslanguageo00chei_1_p162_c0, 0.5515), (6, cheiroslanguageo00chei_1_p163_c0, 0.5486), (7, cheiroslanguageo00chei_1_p164_c1, 0.5336), (8, cheiroslanguageo00chei_1_p164_c2, 0.5165), (9, cheiroslanguageo00chei_1_p162_c1, 0.5081), (10, cheiroslanguageo00chei_1_p164_c0, 0.4756), (11, cheiroslanguageo00chei_1_p165_c2, 0.4595), (12, cheiroslanguageo00chei_1_p163_c3, 0.4594), (13, cheiroslanguageo00chei_1_p164_c3, 0.4225), (14, cheiroslanguageo00chei_1_p162_c2, 0.3622)]
  fingers: window=3 candidates=[(1, cheiroslanguageo00chei_1_p96_c1, 0.5511), (2, cheiroslanguageo00chei_1_p96_c2, 0.5341), (3, cheiroslanguageo00chei_1_p96_c0, 0.533), (4, cheiroslanguageo00chei_1_p96_c3, 0.4912), (5, cheiroslanguageo00chei_1_p97_c0, 0.4911), (6, cheiroslanguageo00chei_1_p95_c0, 0.488), (7, cheiroslanguageo00chei_1_p95_c1, 0.4763), (8, cheiroslanguageo00chei_1_p95_c2, 0.4624), (9, cheiroslanguageo00chei_1_p93_c0, 0.4169), (10, cheiroslanguageo00chei_1_p94_c0, 0.3788), (11, cheiroslanguageo00chei_1_p93_c1, 0.2772)]
  head line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p145_c0, 0.5589), (2, cheiroslanguageo00chei_1_p147_c1, 0.526), (3, cheiroslanguageo00chei_1_p151_c2, 0.5226), (4, cheiroslanguageo00chei_1_p147_c0, 0.5066), (5, cheiroslanguageo00chei_1_p148_c1, 0.4943), (6, cheiroslanguageo00chei_1_p148_c0, 0.4909), (7, cheiroslanguageo00chei_1_p150_c2, 0.4888), (8, cheiroslanguageo00chei_1_p147_c3, 0.4814), (9, cheiroslanguageo00chei_1_p151_c1, 0.4715), (10, cheiroslanguageo00chei_1_p149_c0, 0.4706), (11, cheiroslanguageo00chei_1_p153_c1, 0.4687), (12, cheiroslanguageo00chei_1_p150_c0, 0.4672), (13, cheiroslanguageo00chei_1_p150_c1, 0.4557), (14, cheiroslanguageo00chei_1_p146_c1, 0.4521), (15, cheiroslanguageo00chei_1_p154_c0, 0.4489), (16, cheiroslanguageo00chei_1_p148_c2, 0.4464), (17, cheiroslanguageo00chei_1_p146_c0, 0.4423), (18, cheiroslanguageo00chei_1_p146_c2, 0.4209), (19, cheiroslanguageo00chei_1_p149_c1, 0.4114), (20, cheiroslanguageo00chei_1_p153_c0, 0.4093), (21, cheiroslanguageo00chei_1_p145_c1, 0.4086), (22, cheiroslanguageo00chei_1_p147_c2, 0.3982), (23, cheiroslanguageo00chei_1_p154_c1, 0.3921), (24, cheiroslanguageo00chei_1_p155_c0, 0.3907), (25, cheiroslanguageo00chei_1_p151_c0, 0.389), (26, cheiroslanguageo00chei_1_p152_c1, 0.3724), (27, cheiroslanguageo00chei_1_p152_c0, 0.3553), (28, cheiroslanguageo00chei_1_p155_c1, 0.3123), (29, cheiroslanguageo00chei_1_p145_c2, 0.2804), (30, cheiroslanguageo00chei_1_p153_c2, 0.1865)]
  heart line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p160_c2, 0.6427), (2, cheiroslanguageo00chei_1_p161_c0, 0.6188), (3, cheiroslanguageo00chei_1_p159_c2, 0.6061), (4, cheiroslanguageo00chei_1_p159_c3, 0.6054), (5, cheiroslanguageo00chei_1_p156_c0, 0.5884), (6, cheiroslanguageo00chei_1_p160_c1, 0.557), (7, cheiroslanguageo00chei_1_p156_c1, 0.5494), (8, cheiroslanguageo00chei_1_p160_c3, 0.522), (9, cheiroslanguageo00chei_1_p160_c0, 0.4791), (10, cheiroslanguageo00chei_1_p159_c1, 0.4751), (11, cheiroslanguageo00chei_1_p159_c0, 0.3856), (12, cheiroslanguageo00chei_1_p156_c2, 0.3415)]
  life line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p139_c0, 0.6108), (2, cheiroslanguageo00chei_1_p134_c2, 0.5801), (3, cheiroslanguageo00chei_1_p134_c1, 0.5775), (4, cheiroslanguageo00chei_1_p135_c0, 0.5652), (5, cheiroslanguageo00chei_1_p139_c1, 0.5552), (6, cheiroslanguageo00chei_1_p138_c1, 0.5406), (7, cheiroslanguageo00chei_1_p135_c2, 0.5394), (8, cheiroslanguageo00chei_1_p136_c1, 0.5337), (9, cheiroslanguageo00chei_1_p136_c3, 0.5332), (10, cheiroslanguageo00chei_1_p134_c0, 0.5317), (11, cheiroslanguageo00chei_1_p135_c1, 0.5253), (12, cheiroslanguageo00chei_1_p137_c1, 0.5195), (13, cheiroslanguageo00chei_1_p136_c2, 0.5054), (14, cheiroslanguageo00chei_1_p137_c0, 0.5013), (15, cheiroslanguageo00chei_1_p138_c2, 0.4935), (16, cheiroslanguageo00chei_1_p138_c0, 0.466), (17, cheiroslanguageo00chei_1_p137_c3, 0.4625), (18, cheiroslanguageo00chei_1_p133_c0, 0.4477), (19, cheiroslanguageo00chei_1_p137_c2, 0.4165), (20, cheiroslanguageo00chei_1_p134_c3, 0.399), (21, cheiroslanguageo00chei_1_p136_c0, 0.3986), (22, cheiroslanguageo00chei_1_p133_c1, 0.177), (23, cheiroslanguageo00chei_1_p139_c2, 0.0862)]
  mount of venus: window=3 candidates=[(1, cheiroslanguageo00chei_1_p111_c1, 0.652), (2, cheiroslanguageo00chei_1_p112_c0, 0.6181), (3, cheiroslanguageo00chei_1_p113_c0, 0.497), (4, cheiroslanguageo00chei_1_p111_c0, 0.4856), (5, cheiroslanguageo00chei_1_p112_c1, 0.4774), (6, cheiroslanguageo00chei_1_p113_c1, 0.4747), (7, cheiroslanguageo00chei_1_p112_c2, 0.4245)]
  thumb: window=3 candidates=[(1, cheiroslanguageo00chei_1_p88_c0, 0.5569), (2, cheiroslanguageo00chei_1_p87_c0, 0.5513), (3, cheiroslanguageo00chei_1_p88_c1, 0.5327), (4, cheiroslanguageo00chei_1_p89_c2, 0.5322), (5, cheiroslanguageo00chei_1_p89_c0, 0.5226), (6, cheiroslanguageo00chei_1_p85_c0, 0.5033), (7, cheiroslanguageo00chei_1_p86_c0, 0.4837), (8, cheiroslanguageo00chei_1_p90_c2, 0.4443), (9, cheiroslanguageo00chei_1_p85_c1, 0.4043), (10, cheiroslanguageo00chei_1_p88_c2, 0.3724), (11, cheiroslanguageo00chei_1_p90_c0, 0.3615), (12, cheiroslanguageo00chei_1_p89_c1, 0.305), (13, cheiroslanguageo00chei_1_p90_c1, 0.2905), (14, cheiroslanguageo00chei_1_p87_c1, 0.0692)]

## RUN 2026-08-06T14:20:24.307832

### capture_reason
silence

### Confirmed descriptions
#### LEFT
HAND SHAPE: Elongated palm, overall slender build.

FINGERS: Long relative to palm, straight, rounded fingertips, slight spacing between fingers.

THUMB: Medium size, set moderately low, wide angle from the palm.

LIFE LINE: Present, deep, narrow, long, curves around the base of the thumb, no clear breaks or forks.

HEAD LINE: Present, deep, narrow, medium length, slightly sloping downward, no clear breaks or forks.

HEART LINE: Present, deep, narrow, long, curves slightly upward, no clear breaks or forks.

FATE LINE: Barely visible.

OTHER LINES: Not clearly visible.

MOUNTS: Mount of Venus appears developed, other mounts not clearly visible.

MARKS: No clear marks visible.
#### RIGHT
HAND SHAPE: Elongated palm, overall build is slender.

FINGERS: Long relative to palm, straight, rounded fingertips, moderate spacing.

THUMB: Medium size, set moderately low, wide angle from the palm.

LIFE LINE: Present, deep, narrow, long, curves around the base of the thumb, no clear breaks or forks.

HEAD LINE: Present, deep, narrow, medium length, slightly sloping downward, no clear breaks or forks.

HEART LINE: Present, deep, narrow, long, curves slightly upward, no clear breaks or forks.

FATE LINE: Barely visible.

OTHER LINES: Not clearly visible.

MOUNTS: Mount of Venus appears developed, other mounts unremarkable.

MARKS: Not clearly visible.

### reading_text


A note on what I have not interpreted: the classical texts I work from do not clearly address the following as they appear in your hands: life line, head line, heart line, fate line, sun line, thumb, fingers, mount of venus, mount of jupiter. Rather than guess, I have left these out of your reading.

For major life decisions, I recommend consulting a qualified astrologer or palm reader for a personal reading.

### READING (TAGGED)


### sources

### feature_support
supported_features: ('life line', 'head line', 'heart line', 'fate line', 'thumb', 'fingers', 'mount of venus')
unsupported_features: ('sun line', 'mount of jupiter')

### claims_inventory
claims_inventory: EMPTY

### ring1_validation
passed: True
failures: ()
retry_used: False
stage1_retry_features: NONE
stage1_feature_diagnostics:
  _rules_engine: outcome=rules_engine_ok failed=False
    enabled_features: ['Line of Fate', 'Line of Head', 'Line of Heart', 'Line of Life', 'Line of Sun', 'Mount of Jupiter', 'Mount of Venus', 'Thumb']
    fired_rule_ids: []
    surviving_rule_ids: []
    suppression_log: []
    dropped_tokens: []
    phrase_promotions: []
    citations: {}
    dropped_rule_ids: []
    claim_features_outside_registry: []
    observation_record:
      Line of Fate: tokens={} unmapped=[{'quality': 'Barely visible.', 'attribute_guess': 'Clarity'}] raw_prose="Barely visible."
      Line of Head: tokens={'Depth': {'value': 'deep', 'confidence': 0.6}, 'Thickness': {'value': 'narrow', 'confidence': 0.6}, 'Length': {'value': 'medium', 'confidence': 0.6}, 'Slope': {'value': 'downward', 'confidence': 0.6}, 'Continuity': {'value': 'unbroken', 'confidence': 0.6}} unmapped=[] raw_prose="Present, deep, narrow, medium length, slightly sloping downward, no clear breaks or forks."
      Line of Heart: tokens={'Depth': {'value': 'deep', 'confidence': 0.6}, 'Thickness': {'value': 'narrow', 'confidence': 0.6}, 'Length': {'value': 'long', 'confidence': 0.6}, 'Curve': {'value': 'curved', 'confidence': 0.6}, 'Continuity': {'value': 'unbroken', 'confidence': 0.6}} unmapped=[] raw_prose="Present, deep, narrow, long, curves slightly upward, no clear breaks or forks."
      Line of Life: tokens={'Depth': {'value': 'deep', 'confidence': 1.0}, 'Thickness': {'value': 'narrow', 'confidence': 1.0}, 'Length': {'value': 'long', 'confidence': 1.0}, 'Curve': {'value': 'curved', 'confidence': 1.0}, 'Continuity': {'value': 'unbroken', 'confidence': 1.0}} unmapped=[] raw_prose="Present, deep, narrow, long, curves around the base of the thumb, no clear breaks or forks."
      Mount of Venus: tokens={'Development': {'value': 'developed', 'confidence': 1.0}} unmapped=[] raw_prose="Mount of Venus appears developed"
      Thumb: tokens={'Length': {'value': 'medium', 'confidence': 1.0}, 'Setting': {'value': 'moderate', 'confidence': 1.0}, 'Angle': {'value': 'wide', 'confidence': 1.0}} unmapped=[] raw_prose="Medium size, set moderately low, wide angle from the palm."
  fate line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  fingers: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  head line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  heart line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  life line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  markings/other features: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of jupiter: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  mount of venus: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  sun line: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
  thumb: outcome=unknown attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)
stage2_retry_used: False
stage2_first_attempt_failures: NONE
validation_failures: NONE
ring1_failures:
none

### near_miss_margin
  fate line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p165_c1, 0.6001), (2, cheiroslanguageo00chei_1_p163_c1, 0.5869), (3, cheiroslanguageo00chei_1_p165_c0, 0.5671), (4, cheiroslanguageo00chei_1_p163_c2, 0.561), (5, cheiroslanguageo00chei_1_p162_c0, 0.5515), (6, cheiroslanguageo00chei_1_p163_c0, 0.5486), (7, cheiroslanguageo00chei_1_p164_c1, 0.5336), (8, cheiroslanguageo00chei_1_p164_c2, 0.5165), (9, cheiroslanguageo00chei_1_p162_c1, 0.5081), (10, cheiroslanguageo00chei_1_p164_c0, 0.4756), (11, cheiroslanguageo00chei_1_p165_c2, 0.4595), (12, cheiroslanguageo00chei_1_p163_c3, 0.4594), (13, cheiroslanguageo00chei_1_p164_c3, 0.4225), (14, cheiroslanguageo00chei_1_p162_c2, 0.3622)]
  fingers: window=3 candidates=[(1, cheiroslanguageo00chei_1_p96_c1, 0.5511), (2, cheiroslanguageo00chei_1_p96_c2, 0.5341), (3, cheiroslanguageo00chei_1_p96_c0, 0.533), (4, cheiroslanguageo00chei_1_p96_c3, 0.4912), (5, cheiroslanguageo00chei_1_p97_c0, 0.4911), (6, cheiroslanguageo00chei_1_p95_c0, 0.488), (7, cheiroslanguageo00chei_1_p95_c1, 0.4763), (8, cheiroslanguageo00chei_1_p95_c2, 0.4624), (9, cheiroslanguageo00chei_1_p93_c0, 0.4169), (10, cheiroslanguageo00chei_1_p94_c0, 0.3788), (11, cheiroslanguageo00chei_1_p93_c1, 0.2772)]
  head line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p145_c0, 0.5589), (2, cheiroslanguageo00chei_1_p147_c1, 0.526), (3, cheiroslanguageo00chei_1_p151_c2, 0.5226), (4, cheiroslanguageo00chei_1_p147_c0, 0.5066), (5, cheiroslanguageo00chei_1_p148_c1, 0.4943), (6, cheiroslanguageo00chei_1_p148_c0, 0.4909), (7, cheiroslanguageo00chei_1_p150_c2, 0.4888), (8, cheiroslanguageo00chei_1_p147_c3, 0.4814), (9, cheiroslanguageo00chei_1_p151_c1, 0.4715), (10, cheiroslanguageo00chei_1_p149_c0, 0.4706), (11, cheiroslanguageo00chei_1_p153_c1, 0.4687), (12, cheiroslanguageo00chei_1_p150_c0, 0.4672), (13, cheiroslanguageo00chei_1_p150_c1, 0.4557), (14, cheiroslanguageo00chei_1_p146_c1, 0.4521), (15, cheiroslanguageo00chei_1_p154_c0, 0.4489), (16, cheiroslanguageo00chei_1_p148_c2, 0.4464), (17, cheiroslanguageo00chei_1_p146_c0, 0.4423), (18, cheiroslanguageo00chei_1_p146_c2, 0.4209), (19, cheiroslanguageo00chei_1_p149_c1, 0.4114), (20, cheiroslanguageo00chei_1_p153_c0, 0.4093), (21, cheiroslanguageo00chei_1_p145_c1, 0.4086), (22, cheiroslanguageo00chei_1_p147_c2, 0.3982), (23, cheiroslanguageo00chei_1_p154_c1, 0.3921), (24, cheiroslanguageo00chei_1_p155_c0, 0.3907), (25, cheiroslanguageo00chei_1_p151_c0, 0.389), (26, cheiroslanguageo00chei_1_p152_c1, 0.3724), (27, cheiroslanguageo00chei_1_p152_c0, 0.3553), (28, cheiroslanguageo00chei_1_p155_c1, 0.3123), (29, cheiroslanguageo00chei_1_p145_c2, 0.2804), (30, cheiroslanguageo00chei_1_p153_c2, 0.1865)]
  heart line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p160_c2, 0.6427), (2, cheiroslanguageo00chei_1_p161_c0, 0.6188), (3, cheiroslanguageo00chei_1_p159_c2, 0.6061), (4, cheiroslanguageo00chei_1_p159_c3, 0.6054), (5, cheiroslanguageo00chei_1_p156_c0, 0.5884), (6, cheiroslanguageo00chei_1_p160_c1, 0.557), (7, cheiroslanguageo00chei_1_p156_c1, 0.5494), (8, cheiroslanguageo00chei_1_p160_c3, 0.522), (9, cheiroslanguageo00chei_1_p160_c0, 0.4791), (10, cheiroslanguageo00chei_1_p159_c1, 0.4751), (11, cheiroslanguageo00chei_1_p159_c0, 0.3856), (12, cheiroslanguageo00chei_1_p156_c2, 0.3415)]
  life line: window=3 candidates=[(1, cheiroslanguageo00chei_1_p139_c0, 0.6108), (2, cheiroslanguageo00chei_1_p134_c2, 0.5801), (3, cheiroslanguageo00chei_1_p134_c1, 0.5775), (4, cheiroslanguageo00chei_1_p135_c0, 0.5652), (5, cheiroslanguageo00chei_1_p139_c1, 0.5552), (6, cheiroslanguageo00chei_1_p138_c1, 0.5406), (7, cheiroslanguageo00chei_1_p135_c2, 0.5394), (8, cheiroslanguageo00chei_1_p136_c1, 0.5337), (9, cheiroslanguageo00chei_1_p136_c3, 0.5332), (10, cheiroslanguageo00chei_1_p134_c0, 0.5317), (11, cheiroslanguageo00chei_1_p135_c1, 0.5253), (12, cheiroslanguageo00chei_1_p137_c1, 0.5195), (13, cheiroslanguageo00chei_1_p136_c2, 0.5054), (14, cheiroslanguageo00chei_1_p137_c0, 0.5013), (15, cheiroslanguageo00chei_1_p138_c2, 0.4935), (16, cheiroslanguageo00chei_1_p138_c0, 0.466), (17, cheiroslanguageo00chei_1_p137_c3, 0.4625), (18, cheiroslanguageo00chei_1_p133_c0, 0.4477), (19, cheiroslanguageo00chei_1_p137_c2, 0.4165), (20, cheiroslanguageo00chei_1_p134_c3, 0.399), (21, cheiroslanguageo00chei_1_p136_c0, 0.3986), (22, cheiroslanguageo00chei_1_p133_c1, 0.177), (23, cheiroslanguageo00chei_1_p139_c2, 0.0862)]
  mount of venus: window=3 candidates=[(1, cheiroslanguageo00chei_1_p111_c1, 0.652), (2, cheiroslanguageo00chei_1_p112_c0, 0.6181), (3, cheiroslanguageo00chei_1_p113_c0, 0.497), (4, cheiroslanguageo00chei_1_p111_c0, 0.4856), (5, cheiroslanguageo00chei_1_p112_c1, 0.4774), (6, cheiroslanguageo00chei_1_p113_c1, 0.4747), (7, cheiroslanguageo00chei_1_p112_c2, 0.4245)]
  thumb: window=3 candidates=[(1, cheiroslanguageo00chei_1_p88_c0, 0.5569), (2, cheiroslanguageo00chei_1_p87_c0, 0.5513), (3, cheiroslanguageo00chei_1_p88_c1, 0.5327), (4, cheiroslanguageo00chei_1_p89_c2, 0.5322), (5, cheiroslanguageo00chei_1_p89_c0, 0.5226), (6, cheiroslanguageo00chei_1_p85_c0, 0.5033), (7, cheiroslanguageo00chei_1_p86_c0, 0.4837), (8, cheiroslanguageo00chei_1_p90_c2, 0.4443), (9, cheiroslanguageo00chei_1_p85_c1, 0.4043), (10, cheiroslanguageo00chei_1_p88_c2, 0.3724), (11, cheiroslanguageo00chei_1_p90_c0, 0.3615), (12, cheiroslanguageo00chei_1_p89_c1, 0.305), (13, cheiroslanguageo00chei_1_p90_c1, 0.2905), (14, cheiroslanguageo00chei_1_p87_c1, 0.0692)]

