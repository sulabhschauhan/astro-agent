# Ring 3 pass 4 evidence -- claim ledger + coverage reconstruction

**EVIDENCE PACKAGE ONLY. NOT A SCORED PASS, NOT A VERDICT.** Assembled by
Sonnet (run capture + evidence probes) per the session's own model split;
P1-P4/P7/Ring 1 spot-check scoring and the ratification verdict are
design-tier's call, not rendered here. Artifact ships with the
ratification checkbox UNCHECKED.

## Run inventory (2026-07-19 live dogfood session, all fresh uploads + human confirmations)

| Timestamp | Label | `passed` | `retry_used` | Note |
|---|---|---|---|---|
| 10:36:21 | Run A attempt 1 | False | True | `self_help_blacklist: found stability` on BOTH drafts -- fail-closed, refused, not displayed. Real P3-voice evidence: exemplar-echo/self-help register still fires live post-S67-R2. |
| 10:37:24 | Run A attempt 2 | False | True | Same failure, same word ("stability"). |
| 10:40:50 | **Run A (baseline)** | True | True | Scored below. |
| 10:41:49 | Run B attempt 1 | False | True | Same failure, same word ("stability"), same as Run A's 2 failed attempts. |
| 10:42:48 | **Run B (identical-input regenerate)** | True | True | Scored below. Confirmed identical LEFT/RIGHT to Run A (byte comparison). |
| 10:43:39 | **Run C (+HAND_DETAIL)** | True | True | Scored below. Same LEFT/RIGHT as A/B + HAND_DETAIL added. |

3/6 attempts needed a re-click after a fail-closed refusal, all 3 on the identical self-help term "stability" -- worth weighing as its own P3 finding (the register guard is doing its job, but "stability" is evidently a high-frequency GPT-4o completion for this prompt shape, costing the user a real extra click on half of today's attempts).

## Headline finding 1: ALL 3 scoreable runs carry the SAME coverage warning

Every one of Run A/B/C reconstructs to `['coverage: markings/other features supported but never cited']` (see each run's own section below). Per the S68-locked rule ("a `ValidationReport.warnings`-bearing run cannot score P4 clean"), **none of the 3 fresh runs can score P4 clean** under that rule as written. Mechanical fact, not an adjudication -- design-tier decides what this means for the ratification bar.

## Headline finding 2: F-B has a live, reproducible gap the pass-3 corpus never exercised

CLAUDE.md's F-B comparability lock states `markings/other features` "SHRINKS vs pass 3 (F-B by-design)" -- i.e. should exit to genuine-negative-absence when both hands report absence. That held for pass-3's exact captured phrasing. It does **NOT** hold here: all 3 fresh runs' vision model phrased LEFT's MARKS field as **"No crosses, stars, grilles, squares, or moles clearly visible."** -- a comma-separated list between "no" and any recognized noun. Direct proof, reproduced independently of any run parsing:

```
_is_absence('No crosses, stars, grilles, squares, or moles clearly visible.', 'markings/other features') -> False
```

Root cause found by inspecting `_ABSENCE_PATTERNS_BY_FEATURE`'s compiled pattern: the TIER-2 filler-word groups are `(?:\s+\w+){0,3}` (whitespace + word-chars only) -- a comma immediately after a filler word is not `\s`, so the pattern cannot skip past it. "No **crosses,** stars..." breaks at the comma; the pattern never reaches a recognized noun within its filler budget. This is a genuine, previously-untested gap in the F-B regex, not a regression in anything F-B was actually verified against (the pass-3 corpus's own MARKS phrasing never used this comma-list shape). Symptom is fully contained by F-A in practice -- `markings/other features` stays `supported` but is never cited in any of the 3 readings (headline finding 1), so no fabricated markings content ever reaches the user -- but the classification itself is wrong, and the near-floor junk retrieval F-B was built to eliminate (scores 0.34-0.49) is back for this phrasing. Fix candidate (not applied here, out of scope): allow `[,;]?\s+` or similar in the filler-group pattern instead of bare `\s+\w+`. Flagged for design-chat, not silently patched.

## Headline finding 3: one recurring citation worth a spot-check look

All 3 runs cite the SAME chunk (`cheiroslanguageo00chei_1_p163_c1`) for the SAME claim -- the barely-visible fate line "may not be strongly influenced by external forces or predetermined destiny... more self-directed, relying on personal choices." The cited chunk's actual content (verbatim below, each run's own section) discusses where a fate line RISES FROM and its STRENGTH determining personal-merit-vs-parental-sacrifice outcomes -- it says nothing about a faint/barely-visible line implying self-direction. This reads as the nearest-available fate-line chunk being cited for a claim it doesn't directly ground, not a verbatim-quote match. Flagged as the anchor-fidelity spot-check's first candidate row (recurs identically in all 3 runs, so one adjudication covers all 3) -- not scored here.

## Per-run detail

## Run A (baseline) -- `2026-07-19T10:40:50.482046`

Reconstruction fidelity gate PASSED -- reconstructed supported_features/unsupported_features exactly match the capture. Coverage warnings and chunk-text lookups below are trustworthy for this run.

**F-A coverage warnings (reconstructed)**: ['coverage: markings/other features supported but never cited']
**valid_chunk_ids count (V-2 union, reconstructed)**: 24

**F-B absence-classification check on this run's MARKS texts**:
- `_is_absence(feature='markings/other features')` = **False** for: 'No crosses, stars, grilles, squares, or moles clearly visible.'
- `_is_absence(feature='markings/other features')` = **True** for: 'Not clearly visible'

### Claim ledger (16 tagged clauses, self-declared anchors)

| # | Clause | Anchor(s) |
|---|---|---|
| 1 | The hands you present reveal a robust and grounded nature, with a square palm and well-proportioned fingers indicating a practical and methodical approach to life.[OBS] | OBS |
| 2 | The long, deep life line on both hands, curving around the base of the thumb, suggests a strong constitution and the promise of a long and healthy life.[cheiroslanguageo00chei_1_p134_c1] | cheiroslanguageo00chei_1_p134_c1 |
| 3 | This line's continuity without breaks or chains further reinforces the likelihood of enduring vitality and resilience.[cheiroslanguageo00chei_1_p134_c1] | cheiroslanguageo00chei_1_p134_c1 |
| 4 | Your head line, also long and deep, reflects a strong mental capacity and intellectual vigor.[cheiroslanguageo00chei_1_p145_c0] | cheiroslanguageo00chei_1_p145_c0 |
| 5 | Its slight curve suggests a balance between logic and creativity, allowing for both practical reasoning and imaginative thought.[cheiroslanguageo00chei_1_p145_c0] | cheiroslanguageo00chei_1_p145_c0 |
| 6 | The absence of breaks or chains in this line indicates a stable and consistent mental outlook, free from indecision or mental turmoil.[cheiroslanguageo00chei_1_p147_c1] | cheiroslanguageo00chei_1_p147_c1 |
| 7 | The heart line, deep and slightly curving upward, speaks to a warm and affectionate nature.[cheiroslanguageo00chei_1_p160_c2] | cheiroslanguageo00chei_1_p160_c2 |
| 8 | Its unbroken form suggests sincerity in emotional matters and a capacity for deep, enduring affection.[cheiroslanguageo00chei_1_p160_c2] | cheiroslanguageo00chei_1_p160_c2 |
| 9 | This line's upward curve indicates a positive and optimistic approach to relationships, with a tendency to see the best in others.[cheiroslanguageo00chei_1_p160_c2] | cheiroslanguageo00chei_1_p160_c2 |
| 10 | The barely visible fate line suggests that your life path may not be strongly influenced by external forces or predetermined destiny.[cheiroslanguageo00chei_1_p163_c1] | cheiroslanguageo00chei_1_p163_c1 |
| 11 | Instead, it implies that your course is more self-directed, relying on personal choices and actions rather than fate.[cheiroslanguageo00chei_1_p163_c1] | cheiroslanguageo00chei_1_p163_c1 |
| 12 | The Mount of Venus, well-developed on both hands, indicates a strong capacity for love and passion, as well as a robust physical health.[cheiroslanguageo00chei_1_p112_c0] | cheiroslanguageo00chei_1_p112_c0 |
| 13 | This mount suggests a benevolent and affectionate disposition, with a love for beauty and harmony in life.[cheiroslanguageo00chei_1_p112_c0] | cheiroslanguageo00chei_1_p112_c0 |
| 14 | Your thumb, medium in size and set at a wide angle, suggests a balance of will, logic, and love, indicating a well-rounded character with intellectual strength and determination.[cheiroslanguageo00chei_1_p88_c0] | cheiroslanguageo00chei_1_p88_c0 |
| 15 | The fingers, long and straight with rounded tips, further emphasize an intellectual and refined nature, capable of thoughtful and independent action.[cheiroslanguageo00chei_1_p96_c0] | cheiroslanguageo00chei_1_p96_c0 |
| 16 | In summary, your hands reveal a person of strong health, intellectual capability, and deep emotional capacity. Your life is largely self-directed, with a focus on personal growth and relationships. The developed Mount of Venus further enhances your natural inclination towards love and beauty, enriching your interactions with the world around you. | OBS |

### Verbatim chunk text for every cited chunk_id (not [OBS])

- `cheiroslanguageo00chei_1_p112_c0` (p.112, score 0.6181, feature=mount of venus):
  > 64 Cheiro’s Language of the Hand.

Venus be well developed, it indicates strong and robust health. A small
Mount of Venus betrays poor health and, consequently, less passion.

The Mount of Venus, abnormally large, indicates a violent passion for the
opposite sex.

This mount denotes affection, sympathy toward others, benevolence, a
desire to please, love and worship of beauty, love of color, and melody in
music, and the attraction of the one sex to the other.

THE MOUNT OF JUPITER.

This mount is the raised formation at the base of the first finger (Plate
XII.). When developed it shows ambition, pride, enthusiasm in anything
attempted, and desire for power.
- `cheiroslanguageo00chei_1_p134_c1` (p.134, score 0.5775, feature=life line):
  > The line of life should be long, narrow, and deep, without irregularities,
breaks, or crosses of any kind. Such a formation promises long life, good
health, and vitality.

When the line is linked (Fig. 10, Plate XIV.) or made up of little pieces
hkea chain, it is a sure sign of bad health, and particularly so on a soft hand.
When the line recovers its evenness and continuity, health also is regained.

When broken in the left hand and joined in the right, it threatens some
dangerous illness; but if broken in both hands it generally signifies death.
This is more decidedly confirmed when one branch turns back on the Mount
of Venus (-, Plate X 11.)
- `cheiroslanguageo00chei_1_p145_c0` (p.145, score 0.5588, feature=head line):
  > CHAPTER VII.
THE LINE OF HEAD.

“To know is power “—let us then be wise,
And use our brains with every good intent,
That at the end we come with tired eyes
And give to Nature more than what she lent.
CHEIRO.

Tue line of head (Plate NUL.) relates principally to the mentality of the
subject—to the intellectual strength or weakness, to the temperament in its
relation to talent, and to the direction and quality of the talent itself.

It is of extreme importance in connection with this line that the peculiar-
ities of the various types be borne in mind; as, for instance, a sloping line of
head on a psychic or conic hand is not of half the importance of a sloping
line on a square hand. We will, however, take general characteristics first,
and proceed to consider variations afterward.
- `cheiroslanguageo00chei_1_p147_c1` (p.147, score 0.526, feature=head line):
  > When abnormally short, it foreshadows some early death from some
mental affection.

When broken in two under the Mount of Saturn, it tells of an early
sudden death by fatality.

When linked, or made up of little pieces like a chain, it denotes want of
fixity of ideas, and indecision.

When full of little islands and hair-lines, it tells of great pain to the head
and danger of brain disease.

When the line of head is so high on the hand that the space is extremely
narrow between it and the line of heart, the head will completely rule the
heart, if that line be the strongest, and vice versd.
- `cheiroslanguageo00chei_1_p160_c2` (p.160, score 0.6427, feature=heart line):
  > When the line is quite bare of branches and thin, it tells of coldness of
heart and want of affection.

When bare and thin toward the pereussion or side of the hand, it denotes
sterility.

Fine lines rising up to the line of heart from the line of head denote
those who influence our thoughts in affairs of the heart, and by being crossed
or uncrossed denote if the affection has brought trouble or has been smooth
and fortunate.

When the lines of heart, head and hfe are very much joined together, it
is an evil sign; in all matters of affection such a subject would stick at
nothing to obtain his or her desires.
- `cheiroslanguageo00chei_1_p163_c1` (p.163, score 0.5869, feature=fate line):
  > The line of fate may rise from the line of hfe, the wrist, the Mount of
Luna, the line of head, or even the line of heart.

If the fate-line rise from the line of life and from that poit on 18 strong,
suecess and riches will be won by personal merit; but if the lme be marked
low down near the wrist and tied down, as it were, by the side of the life-line,
it tells that the early portion of the subject’s life will be sacrificed to the
wishes of parents or relatives (g-g, Plate XX.).

When the line of fate rises from the wrist and proceeds straight up the
hand to its destination on the Mount of Saturn, it is a sign of extreme good
fortune and success.
- `cheiroslanguageo00chei_1_p88_c0` (p.88, score 0.5569, feature=thumb):
  > 45 Cheiro’s Language of the Hand.

formed thumb denotes strength of intellectual will; the short, thick thumb,
brute foree and obstinacy ; the small, weak thumb, weakness of will and want
of energy.

From time immemorial the thumb has been divided into three parts,
which are significant of the three great powers that rule the world—love,
logie, and will.

The first or nail phalange denotes will.

The second phalange, logic.

The third, which is the boundary of the Mount of Venus, love.

When the thumb is nmequally developed, as, for instance, the first pha-
lange extremely long, we find that the subject depends upon neither 1091 nor
‘reason, but simply upon will.
- `cheiroslanguageo00chei_1_p96_c0` (p.96, score 0.5165, feature=fingers):
  > ot Cheivo’s Language of the Hand.

his own comfort before that of others; he will desire luxury in eating, drink-
ing, and living. When, on the contrary, the fingers at the base are shaped
like a waist, it shows an unselfish disposition in every way, and fastidiousness
in matters of food.

When, with the fingers open, a wide space is seen between the first and
second, it indicates great independence of thought. When the space is wide
between the third and fourth, it indicates independence of action.

THE LENGTH OF THE FINGERS IN RELATION TO ONE ANOTHER.

The first finger on some hands is very short; again, on others, it is as
long as the second, and so on.

---

## Run B (identical-input regenerate) -- `2026-07-19T10:42:48.947566`

Reconstruction fidelity gate PASSED -- reconstructed supported_features/unsupported_features exactly match the capture. Coverage warnings and chunk-text lookups below are trustworthy for this run.

**F-A coverage warnings (reconstructed)**: ['coverage: markings/other features supported but never cited']
**valid_chunk_ids count (V-2 union, reconstructed)**: 24

**F-B absence-classification check on this run's MARKS texts**:
- `_is_absence(feature='markings/other features')` = **False** for: 'No crosses, stars, grilles, squares, or moles clearly visible.'
- `_is_absence(feature='markings/other features')` = **True** for: 'Not clearly visible'

### Claim ledger (17 tagged clauses, self-declared anchors)

| # | Clause | Anchor(s) |
|---|---|---|
| 1 | The hands before me reveal a robust and square palm, indicating a practical and grounded nature, with a strong foundation in both innate potential and current life trajectory.[OBS] | OBS |
| 2 | The long, deep, and unbroken life line on both hands promises good health and vitality, suggesting a life of physical strength and longevity.[cheiroslanguageo00chei_1_p134_c1] | cheiroslanguageo00chei_1_p134_c1 |
| 3 | The life line's curve around the base of the thumb further emphasizes this vitality, allowing the Mount of Venus to have greater scope, which is a sign of robust health and a passionate disposition.[cheiroslanguageo00chei_1_p139_c0] | cheiroslanguageo00chei_1_p139_c0 |
| 4 | The head line, deep and slightly curved, speaks to a strong intellect and a balanced approach to life. Its unbroken nature suggests a clear and decisive mind, free from indecision or mental turmoil.[cheiroslanguageo00chei_1_p145_c0] | cheiroslanguageo00chei_1_p145_c0 |
| 5 | This line's presence in both hands indicates that your intellectual strength is both an innate trait and a current reality, guiding your actions with reason and intelligence.[OBS] | OBS |
| 6 | The heart line, also deep and long, curves slightly upward, indicating a capacity for deep affection and emotional expression. Its unbroken state suggests steadiness in emotional matters, free from the turmoil of inconstancy or fleeting passions.[cheiroslanguageo00chei_1_p160_c2] | cheiroslanguageo00chei_1_p160_c2 |
| 7 | This line's consistency across both hands suggests that your emotional depth is a fundamental aspect of your character, as well as a current strength.[OBS] | OBS |
| 8 | The barely visible fate line suggests that destiny plays a less pronounced role in your life, indicating that personal effort and choices are more significant in shaping your path.[cheiroslanguageo00chei_1_p163_c1] | cheiroslanguageo00chei_1_p163_c1 |
| 9 | This is consistent across both hands, suggesting that your life is largely self-directed, relying on personal merit rather than predetermined fate.[OBS] | OBS |
| 10 | The Mount of Venus is well-developed, indicating a strong capacity for affection, sympathy, and a love of beauty and harmony.[cheiroslanguageo00chei_1_p112_c0] | cheiroslanguageo00chei_1_p112_c0 |
| 11 | This mount's prominence in both hands suggests that these qualities are deeply ingrained in your nature and continue to influence your current life path.[OBS] | OBS |
| 12 | The medium-sized thumb, set at a wide angle, suggests a balance of willpower and logic, with a tendency towards independence and self-reliance.[cheiroslanguageo00chei_1_p88_c0] | cheiroslanguageo00chei_1_p88_c0 |
| 13 | This thumb's characteristics are consistent in both hands, indicating that these traits are both inherent and actively present in your life.[OBS] | OBS |
| 14 | The fingers, long and straight with rounded tips, suggest an intellectual nature and a refined approach to life.[cheiroslanguageo00chei_1_p98_c1] | cheiroslanguageo00chei_1_p98_c1 |
| 15 | This feature is consistent in both hands, reinforcing the intellectual and thoughtful aspects of your character.[OBS] | OBS |
| 16 | In summary, your hands reveal a life marked by health, intellectual clarity, and emotional depth, with a strong emphasis on personal agency and self-determination. The consistent features across both hands suggest that your innate potential aligns closely with your current trajectory, reinforcing the strengths and qualities that define your character.[OBS] | OBS |
| 17 | Note: Features not covered by retrieved passages include the sun line, health and marriage lines, and any specific markings such as crosses, stars, grilles, squares, or moles. | OBS |

### Verbatim chunk text for every cited chunk_id (not [OBS])

- `cheiroslanguageo00chei_1_p112_c0` (p.112, score 0.6181, feature=mount of venus):
  > 64 Cheiro’s Language of the Hand.

Venus be well developed, it indicates strong and robust health. A small
Mount of Venus betrays poor health and, consequently, less passion.

The Mount of Venus, abnormally large, indicates a violent passion for the
opposite sex.

This mount denotes affection, sympathy toward others, benevolence, a
desire to please, love and worship of beauty, love of color, and melody in
music, and the attraction of the one sex to the other.

THE MOUNT OF JUPITER.

This mount is the raised formation at the base of the first finger (Plate
XII.). When developed it shows ambition, pride, enthusiasm in anything
attempted, and desire for power.
- `cheiroslanguageo00chei_1_p134_c1` (p.134, score 0.5775, feature=life line):
  > The line of life should be long, narrow, and deep, without irregularities,
breaks, or crosses of any kind. Such a formation promises long life, good
health, and vitality.

When the line is linked (Fig. 10, Plate XIV.) or made up of little pieces
hkea chain, it is a sure sign of bad health, and particularly so on a soft hand.
When the line recovers its evenness and continuity, health also is regained.

When broken in the left hand and joined in the right, it threatens some
dangerous illness; but if broken in both hands it generally signifies death.
This is more decidedly confirmed when one branch turns back on the Mount
of Venus (-, Plate X 11.)
- `cheiroslanguageo00chei_1_p139_c0` (p.139, score 0.6107, feature=life line):
  > The Line of Life. 85

number of these lines of influence (it being remembered that only those near
the line of life are important). Numerous lines indicate a nature dependent
upon affection. Such people are what is called passionate in their disposition ;
they may have many liaisons, but in their eyes love redeems all. On the
other hand, the full, smooth Mount of Venns indicates that the individual is
less affected by those with whom he is associated.

When the line of life sweeps far out into the hand, thus allowing the
Mount of Venus a greater scope, it is in itself a sign of good physical strength
and long life.
- `cheiroslanguageo00chei_1_p145_c0` (p.145, score 0.5588, feature=head line):
  > CHAPTER VII.
THE LINE OF HEAD.

“To know is power “—let us then be wise,
And use our brains with every good intent,
That at the end we come with tired eyes
And give to Nature more than what she lent.
CHEIRO.

Tue line of head (Plate NUL.) relates principally to the mentality of the
subject—to the intellectual strength or weakness, to the temperament in its
relation to talent, and to the direction and quality of the talent itself.

It is of extreme importance in connection with this line that the peculiar-
ities of the various types be borne in mind; as, for instance, a sloping line of
head on a psychic or conic hand is not of half the importance of a sloping
line on a square hand. We will, however, take general characteristics first,
and proceed to consider variations afterward.
- `cheiroslanguageo00chei_1_p160_c2` (p.160, score 0.6427, feature=heart line):
  > When the line is quite bare of branches and thin, it tells of coldness of
heart and want of affection.

When bare and thin toward the pereussion or side of the hand, it denotes
sterility.

Fine lines rising up to the line of heart from the line of head denote
those who influence our thoughts in affairs of the heart, and by being crossed
or uncrossed denote if the affection has brought trouble or has been smooth
and fortunate.

When the lines of heart, head and hfe are very much joined together, it
is an evil sign; in all matters of affection such a subject would stick at
nothing to obtain his or her desires.
- `cheiroslanguageo00chei_1_p163_c1` (p.163, score 0.5869, feature=fate line):
  > The line of fate may rise from the line of hfe, the wrist, the Mount of
Luna, the line of head, or even the line of heart.

If the fate-line rise from the line of life and from that poit on 18 strong,
suecess and riches will be won by personal merit; but if the lme be marked
low down near the wrist and tied down, as it were, by the side of the life-line,
it tells that the early portion of the subject’s life will be sacrificed to the
wishes of parents or relatives (g-g, Plate XX.).

When the line of fate rises from the wrist and proceeds straight up the
hand to its destination on the Mount of Saturn, it is a sign of extreme good
fortune and success.
- `cheiroslanguageo00chei_1_p88_c0` (p.88, score 0.557, feature=thumb):
  > 45 Cheiro’s Language of the Hand.

formed thumb denotes strength of intellectual will; the short, thick thumb,
brute foree and obstinacy ; the small, weak thumb, weakness of will and want
of energy.

From time immemorial the thumb has been divided into three parts,
which are significant of the three great powers that rule the world—love,
logie, and will.

The first or nail phalange denotes will.

The second phalange, logic.

The third, which is the boundary of the Mount of Venus, love.

When the thumb is nmequally developed, as, for instance, the first pha-
lange extremely long, we find that the subject depends upon neither 1091 nor
‘reason, but simply upon will.
- `cheiroslanguageo00chei_1_p98_c1` (p.98, score 0.5882, feature=fingers):
  > If it inclines to the line of life, it promises disappointment and trouble in
domestic affairs, and if the rest of the hand denotes ill-health, it is an added
sign of delicacy and trouble.

When the hollow comes under the line of fate, it indicates misfortune in
business, money, and worldly affairs.

When under the Ine of heart it tells of disappoimtment in the closest
affections.

Ido not hold with other works on the subject, that the fingers must be
longer than the palm to show the intellectual nature. The palm of the hand is
never, properly speaking, exceeded in length by the fingers. How ean we ex-
pect this to be the case with the square, spatulate, and philosophic types?
The statement that in every case the fingers must be longer than the palm is
erroneous and misleading.

---

## Run C (+HAND_DETAIL) -- `2026-07-19T10:43:39.978164`

Reconstruction fidelity gate PASSED -- reconstructed supported_features/unsupported_features exactly match the capture. Coverage warnings and chunk-text lookups below are trustworthy for this run.

**F-A coverage warnings (reconstructed)**: ['coverage: markings/other features supported but never cited']
**valid_chunk_ids count (V-2 union, reconstructed)**: 22

**F-B absence-classification check on this run's MARKS texts**:
- `_is_absence(feature='markings/other features')` = **False** for: 'No crosses, stars, grilles, squares, or moles clearly visible.'
- `_is_absence(feature='markings/other features')` = **True** for: 'Not clearly visible'
- `_is_absence(feature='markings/other features')` = **True** for: 'There are no unusual markings or features visible.'
- `_is_absence(feature='markings/other features')` = **False** for: 'There is a presence of hair on the back of the hand and fingers.'

### Claim ledger (17 tagged clauses, self-declared anchors)

| # | Clause | Anchor(s) |
|---|---|---|
| 1 | The hands you present reveal a robust and grounded nature, with a square palm and well-formed lines indicating a strong foundation in both innate potential and current life trajectory.[OBS] | OBS |
| 2 | The life line, deep and unbroken in both hands, promises long life, good health, and vitality.[cheiroslanguageo00chei_1_p134_c1] | cheiroslanguageo00chei_1_p134_c1 |
| 3 | This continuity from potential to present suggests a stable and enduring constitution, free from the interruptions that might otherwise signal health challenges or significant life disruptions.[cheiroslanguageo00chei_1_p134_c1] | cheiroslanguageo00chei_1_p134_c1 |
| 4 | The head line, also deep and slightly curved, indicates a natural balance between intellect and emotion, with a tendency towards practical and clear thinking.[cheiroslanguageo00chei_1_p123_c0] | cheiroslanguageo00chei_1_p123_c0 |
| 5 | This line's consistency across both hands suggests that your mental faculties have been well-developed from potential to present, allowing you to handle life's complexities with a steady mind.[cheiroslanguageo00chei_1_p123_c0] | cheiroslanguageo00chei_1_p123_c0 |
| 6 | Your heart line, deep and curving slightly upward, speaks to a capacity for deep affection and emotional engagement.[cheiroslanguageo00chei_1_p159_c3] | cheiroslanguageo00chei_1_p159_c3 |
| 7 | The absence of breaks or forks in this line suggests that your emotional life is stable and sincere, with a straightforward approach to relationships.[cheiroslanguageo00chei_1_p159_c3] | cheiroslanguageo00chei_1_p159_c3 |
| 8 | The fate line, barely visible, indicates that your life path may not be strongly influenced by external forces or destiny.[cheiroslanguageo00chei_1_p163_c1] | cheiroslanguageo00chei_1_p163_c1 |
| 9 | This suggests a life more shaped by personal choices and internal motivations than by fate or circumstance.[cheiroslanguageo00chei_1_p163_c1] | cheiroslanguageo00chei_1_p163_c1 |
| 10 | The Mount of Venus, well-developed in both hands, indicates a strong capacity for love, affection, and a zest for life.[cheiroslanguageo00chei_1_p112_c0] | cheiroslanguageo00chei_1_p112_c0 |
| 11 | This mount's prominence suggests a robust health and a passionate nature, with a love for beauty and harmony in your surroundings.[cheiroslanguageo00chei_1_p112_c0] | cheiroslanguageo00chei_1_p112_c0 |
| 12 | Your thumb, medium in size and set at a wide angle, reflects a balanced will and reason, with enough flexibility to adapt to circumstances without losing your sense of self.[cheiroslanguageo00chei_1_p88_c1] | cheiroslanguageo00chei_1_p88_c1 |
| 13 | This thumb position suggests a person who is neither overly rigid nor excessively yielding, capable of making decisions with both strength and consideration.[cheiroslanguageo00chei_1_p88_c1] | cheiroslanguageo00chei_1_p88_c1 |
| 14 | The fingers, long and straight with rounded tips, indicate a love of detail and precision in your endeavors.[cheiroslanguageo00chei_1_p95_c0] | cheiroslanguageo00chei_1_p95_c0 |
| 15 | This trait suggests an ability to focus on the finer points of any task, whether in personal or professional life.[cheiroslanguageo00chei_1_p95_c0] | cheiroslanguageo00chei_1_p95_c0 |
| 16 | Overall, your hands reveal a life marked by steadiness, health, and a balanced approach to both thought and emotion. The absence of significant markings or disruptions in the lines further underscores a life path that is steady and self-directed, with a strong foundation in both personal and emotional realms.[OBS] | OBS |
| 17 | Note: Features not covered by retrieved passages include the specific length and spacing of fingers, the presence of hair on the back of the hand, and the detailed shape of the mounts other than Venus. | OBS |

### Verbatim chunk text for every cited chunk_id (not [OBS])

- `cheiroslanguageo00chei_1_p112_c0` (p.112, score 0.6181, feature=mount of venus):
  > 64 Cheiro’s Language of the Hand.

Venus be well developed, it indicates strong and robust health. A small
Mount of Venus betrays poor health and, consequently, less passion.

The Mount of Venus, abnormally large, indicates a violent passion for the
opposite sex.

This mount denotes affection, sympathy toward others, benevolence, a
desire to please, love and worship of beauty, love of color, and melody in
music, and the attraction of the one sex to the other.

THE MOUNT OF JUPITER.

This mount is the raised formation at the base of the first finger (Plate
XII.). When developed it shows ambition, pride, enthusiasm in anything
attempted, and desire for power.
- `cheiroslanguageo00chei_1_p123_c0` (p.123, score 0.609, feature=head line):
  > The Lines of the Hand. 73

The main lines are known by other names, as follows:

The Line of Life is also called the Vital.

The Line of Head, the Natural or Cerebral.

The Line of Heart, the Mensal.

The Line of Fate, the Line of Destiny, or the Saturnian.
The Line of Sun, the Line of Brillianey, or Apollo.

The Line of Health, the Hepatica, or the Liver Line.

The hand is divided into two parts or hemispheres by the line of head.

The upper hemisphere, containing the fingers and Mounts of Jupiter,
Saturn, the Sun, Mereury, and Mars, represents mind, and the lower, con-
taining the base of the hand, represents the material. It will thus be seen
that with this clear point as a guide the student will gain an insight at once
into the character of the subject under examination. This division has
hitherto been ignored, but it is almost infallible in its accuracy; as, for
example, when the predisposition is toward crime the line of head rises into
the abnormal position shown by Plate XXIV., which, taken from life, is-one
instance jn the thousands that can be had of the accuracy of this statement.
- `cheiroslanguageo00chei_1_p134_c1` (p.134, score 0.6054, feature=life line):
  > The line of life should be long, narrow, and deep, without irregularities,
breaks, or crosses of any kind. Such a formation promises long life, good
health, and vitality.

When the line is linked (Fig. 10, Plate XIV.) or made up of little pieces
hkea chain, it is a sure sign of bad health, and particularly so on a soft hand.
When the line recovers its evenness and continuity, health also is regained.

When broken in the left hand and joined in the right, it threatens some
dangerous illness; but if broken in both hands it generally signifies death.
This is more decidedly confirmed when one branch turns back on the Mount
of Venus (-, Plate X 11.)
- `cheiroslanguageo00chei_1_p159_c3` (p.159, score 0.6088, feature=heart line):
  > When the line of heart is bright red, it denotes great violence of passion.

When pale and broad, the subject is blasé and indifferent.

When low down on the hand and thus close to the line of head, the heart
will always interfere with the affairs of the head.
- `cheiroslanguageo00chei_1_p163_c1` (p.163, score 0.6248, feature=fate line):
  > The line of fate may rise from the line of hfe, the wrist, the Mount of
Luna, the line of head, or even the line of heart.

If the fate-line rise from the line of life and from that poit on 18 strong,
suecess and riches will be won by personal merit; but if the lme be marked
low down near the wrist and tied down, as it were, by the side of the life-line,
it tells that the early portion of the subject’s life will be sacrificed to the
wishes of parents or relatives (g-g, Plate XX.).

When the line of fate rises from the wrist and proceeds straight up the
hand to its destination on the Mount of Saturn, it is a sign of extreme good
fortune and success.
- `cheiroslanguageo00chei_1_p88_c1` (p.88, score 0.5588, feature=thumb):
  > When the second phalange is much longer than the first, the subject,
though having all the calmness and exactitude of reason, vet has not sufficient
will and determination to carry out Ins ideas.

When the third phalange is long and the thumb small, the man or woman
is a prey to the more passionate or sensual side of the nature.

One of the most interesting things in the study of the thumb is to notice
whether the first jot is supple or stiff. When supple, the first phalange is
allowed to bend back, and forms the thumb into an arch; when, on the con-
trary, the thumb is stiff, the first phalange cannot be bent back, even by
pressure ; and these two opposite peculiarities bear the greatest possible rela-
tion to character.
- `cheiroslanguageo00chei_1_p95_c0` (p.95, score 0.5194, feature=fingers):
  > CHAPTER XI.
THE FINGERS.

Frncers are either long or short, irrespective of the length of the palm to
which they belong.

Long fingers give love of detail in everything—in the decoration of a
room, in the treatment of servants, in the management of nations, or in the
painting of a picture. Long-fingered people are exact in matters of dress,
quick to notice small attentions; they worry themselves over little things,
and have oceasionally a leaning toward affectation.

Short fingers are quick and impulsive. They cannot be troubled about
little things; they take everything ex masse; they generally jwnp at con-
elusions too hastily. They do not care so much about appearances, or for the
conventionalities of society; they are quick in thought, and hasty and out-
spoken 11 speech.

---
