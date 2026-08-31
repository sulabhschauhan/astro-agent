# S121 #adapter-task-1 -- COMPLETE attribute-requirement inventory

Read-only completeness scan. No file edited, no commit. HEAD `a1d5358`.

## 0. Repo state

- `git pull` -> Already up to date. **HEAD = `a1d5358`** (`feat(interpretive): emission_menus accessor -- single-source menu reader (S121 #2b-i)`).
- **Working tree is NOT clean.** `agent/palm_processor.py` carries an uncommitted +35-line diff: the
  S121 #2b-ii `build_menu_line()` helper plus 17 `build_menu_line(...)` calls injecting bound Depth/
  Width/Length/Curve/Continuity menus into the Life/Head/Heart/Fate blocks of
  `_build_description_system_prompt`. **2b-ii was NOT reverted.** No edit was made by this task (report-only);
  the delta is reported, not resolved.
- **Every map below is computed against committed HEAD**, i.e. the vision prompt WITHOUT 2b-ii. Where
  2b-ii would change a verdict it is called out inline as `[2b-ii would change this]`.
- Other working-tree noise is untracked diagnostics/probe scripts only (no source).
- `diagnostics/latest_run.md` was overwritten twice during this run: once incidentally by
  `scripts/vocab_reachability_scan.py` (invoked to corroborate the S97 UNEMITTABLE class), then by this report.

## 1. REQUIREMENT SET -- the canonical schema the adapter must cover

Union over **all 4 rule files, every bucket, every rule, every antecedent** -- no sampling.
`kind` is what the antecedent actually needs from the hand-state: a **value** token, a
**relation_target** landmark, a **location** landmark riding a typed relation, or a
**schema-flag** (`condition_type=comparative`, which reads `magnitudes`, not `observation`).
Value/meaning is read off the rule's own `source_quote`, not just the token.

### `Hand` . `Type`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `philosophic` | the philosophic hand, the line set high on the hand and straight, is critical, analytical, and cynical. | H_020 *(live)* |
| `spatulate` | The spatulate hand is the hand of action, invention, independence, and originality; when this sloping is accentuated, all these characteristics are doubled or strengthened. | H_019 *(live)* |
| `square` | The square hand with the sloping head-line would start with a practical foundation for imaginative work. | H_018 *(live)* |

### `Line of Fate` . `Branching`

kind: **relation_target**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| -> `Mount of Jupiter` | If the line of fate should at any point throw a branch in that direction, namely, toward Jupiter, it shows more than usual success at that particular stage of life. | FT_014 *(live)* |

### `Line of Fate` . `Continuity`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `broken` | V hen broken and irregular, the career will be uncertain; the ups and downs of success and failm*e full of light and shadow. | FT_011 *(live)* |
| `broken_overlapping` | When there is a break in the line, it is a sure sign of misfortune and loss; but if the second portion of the line begin before the other leaves off, it de¬ notes a complete change in life, ... | FT_012 *(live)* |
| `double` | A double or sister fate-line is an excellent sign. | FT_013 *(live)* |

### `Line of Fate` . `Depth`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `well_marked` | If the fate-line rise from the line of life and from that point on is strong, success and riches will be won by personal merit; | FT_001 *(live)* |

### `Line of Fate` . `Length`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `cutting_into_finger_of_Saturn` | When the line runs beyond the palm, cutting into the finger of Saturn, it is not a good sign, as everything will go too far. | FT_006 *(live)* |

### `Line of Fate` . `Position`

kind: **relation_target**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| -> `Mount of Jupiter` | If the line of fate ascend to the center of the Mount of Jupiter, unusual distinction and power will come into the subject’s life. | FT_005 *(live)* |
| -> `Mount of Saturn` | When the line of fate rises from the wrist and proceeds straight up the hand to its destination on the Mount of Saturn, it is a sign of extreme good fortune and success. | FT_003 *(live)* |

### `Line of Fate` . `Proximity`

kind: **relation_target, value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `touching` | but if the line be marked low down near the wrist and tied down, as it were, by the side of the life-line, it tells that the early portion of the subject’s life will be sacrificed to the wis... | FT_002 *(live)* |

### `Line of Fate` . `Slope`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `straight` | When the line of fate rises from the wrist and proceeds straight up the hand to its destination on the Mount of Saturn, it is a sign of extreme good fortune and success. | FT_003 *(live)* |

### `Line of Fate` . `Starting_Point`

kind: **relation_target**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| -> `Line of Head` | If the line of fate rise from the line of head, and that line be well marked, then success will be won late in life, after a hard struggle and through the subject’s talents. | FT_009 *(live)* |
| -> `Line of Heart` | When it rises from the line of heart extremely late in life, after a difficult struggle success will be won. | FT_010 *(live)* |
| -> `Line of Life` | If the fate-line rise from the line of life and from that point on is strong, success and riches will be won by personal merit; | FT_001 *(live)* |
| -> `Mount of Luna` | Rising from the Mount of Luna, fate and success will be more or less dependent on the fancy and caprice of other people. | FT_004 *(live)* |
| -> `Plain of Mars` | If the line of fate does not rise until late in the Plain of Mars, it denotes a very difficult, hard, and troubled life; | FT_015 *(live)* |
| -> `Wrist` | but if the line be marked low down near the wrist and tied down, as it were, by the side of the life-line, it tells that the early portion of the subject’s life will be sacrificed to the wis... | FT_002 *(live)*, FT_003 *(live)* |

### `Line of Fate` . `meets`

kind: **location, relation_target, typed-relation**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| -> `Line of Heart` @ `Mount of Jupiter` | when, however, it joins the line of heart and they together ascend Jupiter, the subject will have his or her high­est ambition gratified through the affections {h-h, Plate XIX.). | FT_016 *(live)* |

### `Line of Fate` . `stopped_by`

kind: **relation_target, typed-relation**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| -> `Line of Head` | When stopped by the line of head, it foretells that success will be thwarted by some stupidity or blunder of the head. | FT_008 *(live)* |
| -> `Line of Heart` | When the line of fate is abruptly stopped by the line of heart, success will be ruined through the affections; | FT_007 *(live)* |

### `Line of Head` . `Branching`

kind: **relation_target, value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `branched` | If the line of head sends an offshoot to or runs into a star on the Mount of Jupiter, it is a sign of wonderful success in all things attempted. | H_013 *(live)*, H_023 *(live)*, H_024 *(live)* |
| `double` | A double line of head is very rarely found, but when found it is a sure sign of brain power and mentality. | H_025 *(live)* |
| -> `Line of Heart` | When a number of little hair-lines branch upward from the line of head to that of heart, the affections will be a matter of fascination, not of love. | H_014 *(live)* |

### `Line of Head` . `Continuity`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `broken` | When broken in two under the Mount of Saturn, it tells of an early sudden death by fatality. | H_007 *(live)*, H_011 *(live)* |
| `chained` | When linked, or made up of little pieces like a chain, it denotes want of fixity of ideas, and indecision. | H_008 *(live)* |
| `clear` | When straight, clear, and even, it denotes practical common sense and a love of material things more than those of the imagination. | H_004 *(live)* |
| `islanded` | When full of little islands and hair-lines, it tells of great pain to the head and danger of brain disease. | H_009 *(live)*, H_012 *(live)* |

### `Line of Head` . `Depth`

kind: **schema-flag:comparative, value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `well_marked` | If the line of fate rise from the line of head, and that line be well marked, then success will be won late in life, after a hard struggle and through the subject’s talents. | FT_009 *(live)* |
| *(comparative: Depth > vs Line of Heart)* | When the line of head is so high on the hand that the space is extremely narrow between it and the line of heart, the head will completely rule the heart, if that line be the strongest. | H_010a *(live)* |

### `Line of Head` . `Direction`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `sloping` | The square hand with the sloping head-line would start with a practical foundation for imaginative work. | H_018 *(live)*, H_019 *(live)* |
| `straight` | When straight, clear, and even, it denotes practical common sense and a love of material things more than those of the imagination. | H_004 *(live)*, H_020 *(live)* |

### `Line of Head` . `Length`

kind: **relation_target, value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `long` | Rising from Jupiter (c-c, Plate XX.) and yet touching the line of life, it is, if a long line of head, the most powerful of all. Such a subject will have talent, energy, and daring determina... | H_001 *(retired)* |
| `long` | Rising from Jupiter (c-c, Plate XX.) and yet touching the line of life, it is, if a long line of head, the most powerful of all. Such a subject will have talent, energy, and daring determina... | H_027 *(live)* |
| `reaching_Line_of_Heart` | the line of head leaves its proper place on the hand and rises and takes possession of the line of heart, and sometimes even passes beyond it. | H_022 *(parked)* |
| `short` | When the line is short, barely reaching the middle of the hand, it tells of a nature that is thoroughly material. | H_005 *(live)*, H_006 *(live)* |

### `Line of Head` . `Position`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `high` | When the line of head is so high on the hand that the space is extremely narrow between it and the line of heart, the head will completely rule the heart, if that line be the strongest. | H_010a *(live)*, H_010b *(live)*, H_020 *(live)*, H_021 *(live)*, H_022 *(parked)* |
| `running_through_Square` | When the line of head runs into or through a square, it indicates preservation from accident or violence. | H_015 *(live)* |
| `terminating_on_Mount` | if, in its course down the hand, it sends an offshoot or branch to any particular mount, by so doing it partakes of the qualities of that mount. | H_023 *(live)* |
| `terminating_on_Mount_of_Jupiter` | If the line of head sends an offshoot to or runs into a star on the Mount of Jupiter, it is a sign of wonderful success in all things attempted. | H_013 *(live)* |
| `terminating_on_Mount_of_Moon` | Toward the Mount of Luna, imagination, mysticism. | H_024 *(live)* |
| `under_Mount_of_Saturn` | When broken in two under the Mount of Saturn, it tells of an early sudden death by fatality. | H_007 *(live)* |

### `Line of Head` . `Proximity`

kind: **relation_target, value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `distant` | When this space is extremely wide, it denotes foolhardiness, assurance, excessive effrontery, and self-confidence. | H_017 *(live)* |
| `medium` | when medium, it denotes splendid energy and self-confidence, promptness of action and readiness of thought. | H_016 *(live)* |
| `touching` | Rising from Jupiter (c-c, Plate XX.) and yet touching the line of life, it is, if a long line of head, the most powerful of all. Such a subject will have talent, energy, and daring determina... | H_027 *(live)* |
| `touching_Line_of_Life` | Rising from Jupiter and yet touching the line of life, it is, if a long line of head, the most powerful of all. | H_001 *(retired)* |

### `Line of Head` . `Slope`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `downward` | When the entire line has a slight slope, there is a leaning toward imag¬ inative work | H_026 *(live)* |

### `Line of Head` . `Starting_Point`

kind: **relation_target, value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `rising_from_Line_of_Life` | The line of head from the commencement of the line of life, and connected with it, indicates a sensitive and more nervous temperament; it denotes excess of caution. | H_002 *(live)* |
| `rising_from_Mount_of_Jupiter` | Rising from Jupiter and yet touching the line of life, it is, if a long line of head, the most powerful of all. | H_001 *(retired)* |
| `rising_from_Mount_of_Mars` | The line of head rising from the Mount of Mars, within the life-line, is not such a favorable sign; this indicates a fretful, worrying temperament, inconstant in thought. | H_003 *(live)* |
| -> `Mount of Jupiter` | Rising from Jupiter (c-c, Plate XX.) and yet touching the line of life, it is, if a long line of head, the most powerful of all. Such a subject will have talent, energy, and daring determina... | H_027 *(live)* |

### `Line of Head` . `joins_at_origin`

kind: **relation_target, typed-relation**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| -> `Line of Heart` | When the lines of life, head, and heart are all joined together at the commencement (a-a, Plate XVIII.), it is a very unfortunate sign, denoting that the subject, through a defect in tempera... | L_026 *(live)* |
| -> `Line of Life` | The line of head from the commencement of the line of life, and connected with it (d-d, Plate XVI.), indicates a sensitive and more nervous temperament; it denotes excess of caution; even cl... | H_028 *(live)*, L_026 *(live)* |

### `Line of Heart` . `Branching`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `single` | When the line is quite bare of branches and thin, it tells of coldness of heart and want of affection. | HL_014 *(live)* |

### `Line of Heart` . `Color`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `bright_red` | When the line of heart is bright red, it denotes great violence of passion. | HL_019 *(live)* |
| `pale` | When pale and broad, the subject is blasé and indifferent. | HL_020 *(live)* |

### `Line of Heart` . `Continuity`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `barred` | When the line of heart is much fretted by a crowd of little lines rising into it, it tells of inconstancy, flirtations, a series of amourettes, but no lasting affection. | HL_017 *(live)* |
| `broken` | Breaks in the line tell of disappointment in affection -- under Saturn, brought about by fatality. | HL_007 *(live)*, HL_008 *(live)*, HL_009 *(live)* |
| `chained` | A line of heart from Saturn, chained and broad, gives an utter contempt for the subject's opposite sex. | HL_018 *(live)* |
| `forked` | When the line of heart commences with a small fork on the Mount of Jupiter, it is an unfailing sign of a true, honest nature and enthusiasm in love. | HL_010 *(live)*, HL_013 *(live)* |

### `Line of Heart` . `Depth`

kind: **schema-flag:comparative**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| *(comparative: Depth > vs Line of Head)* | the head will completely rule the heart, if that line be the strongest, and vice versd. | H_010b *(live)* |

### `Line of Heart` . `Direction`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `drooping` | The line lying so low that it droops down toward the line of head is a sure sign of unhappiness in affections during the early portion of the life. | HL_012 *(live)* |

### `Line of Heart` . `Length`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `extending_across_entire_palm` | When the line of heart is itself in excess, namely, lying right across the hand from side to side, an excess of affection is the result, and a terrible tendency toward jealousy. | HL_016 *(live)* |

### `Line of Heart` . `Position`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `high` | The excess of this is the same kind of line rising very high on the mount, often from the very finger of Saturn. Such a subject is far more passionate and sensual than any of the others. | HL_005 *(live)*, HL_006 *(live)*, HL_011 *(live)* |
| `low` | The line lying so low that it droops down toward the line of head is a sure sign of unhappiness in affections during the early portion of the life. | HL_012 *(live)*, HL_021 *(live)* |
| `under_Mount_of_Mercury` | under Mercury, through folly and caprice. | HL_009 *(live)* |
| `under_Mount_of_Saturn` | Breaks in the line tell of disappointment in affection -- under Saturn, brought about by fatality. | HL_007 *(live)* |
| `under_Mount_of_Sun` | under the Sun, through pride. | HL_008 *(live)* |

### `Line of Heart` . `Presence`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `faded` | when, however, the line has been there, but has faded out, it is a sign that the subject has had such terrible disappointments in affection that he has become cold, heartless, and indifferen... | HL_015 *(live)* |

### `Line of Heart` . `Starting_Point`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `between_Jupiter_and_Saturn` | The line rising between the first and second fingers gives a calm but deeper nature in matters of love. | HL_003 *(live)* |
| `rising_from_Finger_of_Jupiter` | Next we will consider the line rising from the Mount of Jupiter, even from the finger itself. This denotes the excess of all the foregoing qualities. | HL_002 *(live)* |
| `rising_from_Mount_of_Jupiter` | When it rises from the center of Jupiter, it gives the highest type of love -- the pride and the worship of the heart's ideal. | HL_001 *(live)*, HL_010 *(live)* |
| `rising_from_Mount_of_Saturn` | With the line of heart rising from Saturn, the subject will have more passion in his attachments, and will be more or less selfish in satisfying his affections. | HL_004 *(live)*, HL_005 *(live)*, HL_018 *(live)* |

### `Line of Heart` . `Width`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `thin` | When the line is quite bare of branches and thin, it tells of coldness of heart and want of affection. | HL_014 *(live)* |
| `wide` | when the fork is so wide that one branch rests on Jupiter, the other on Saturn, it then denotes a very uncertain disposition. | HL_013 *(live)*, HL_018 *(live)*, HL_020 *(live)* |

### `Line of Heart` . `joins_at_origin`

kind: **relation_target, typed-relation**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| -> `Line of Life` | When the lines of life, head, and heart are all joined together at the commencement (a-a, Plate XVIII.), it is a very unfortunate sign, denoting that the subject, through a defect in tempera... | L_026 *(live)* |

### `Line of Life` . `Clarity`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `clear` | a clearly formed island at the commencement of the line of life denotes some mystery connected with the subject's birth | L_018 *(live)* |

### `Line of Life` . `Continuity`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `broken` | The line running through a square indicates preservation from death, from sudden death when the life-line running through is broken | L_020 *(retired)* |
| `chained` | When the line is linked or made up of little pieces like a chain, it is a sure sign of bad health | L_002 *(live)*, L_005 *(live)*, L_003 *(retired)* |
| `islanded` | An island on the line of life means an illness or loss of health while the island lasts | L_017 *(live)*, L_018 *(live)* |

### `Line of Life` . `Curve`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `close_to_Mount_of_Venus` | When it lies very close to the Mount of Venus, health is not so robust or the body physically so well built. | L_024 *(live)* |
| `sweeping_wide` | When the line of life sweeps far out into the hand, thus allowing the Mount of Venus a greater scope, it is in itself a sign of good physical strength and long life. | L_023 *(live)* |

### `Line of Life` . `Depth`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `deep` | The line of life should be long, narrow, and deep, without irregularities, breaks, or crosses of any kind. Such a formation promises long life, good health, and vitality. | L_001 *(live)* |

### `Line of Life` . `Length`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `long` | The line of life should be long, narrow, and deep, without irregularities, breaks, or crosses of any kind. Such a formation promises long life, good health, and vitality. | L_001 *(live)* |
| `short` | The shorter the line the shorter the life. | L_025 *(live)* |

### `Line of Life` . `Starting_Point`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `at_start` | a clearly formed island at the commencement of the line of life denotes some mystery connected with the subject's birth | L_018 *(live)* |
| `rising_from_Mount_of_Jupiter` | When the line starts from the base of the Mount of Jupiter, instead of the side of the hand, it denotes that from the earliest the life has been one of ambition. | L_004 *(live)* |
| `under_Mount_of_Jupiter` | When the line is chained at the commencement under Jupiter, bad health in early life is foreshadowed. | L_005 *(live)* |

### `Line of Life` . `Width`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `narrow` | The line of life should be long, narrow, and deep, without irregularities, breaks, or crosses of any kind. Such a formation promises long life, good health, and vitality. | L_001 *(live)* |

### `Mount of Jupiter` . `Development`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `developed` | When developed it shows ambition, pride, enthusiasm in anything attempted, and desire for power. | M_014 *(live)* |

### `Mount of Saturn` . `Development`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `not notably developed` | This is found at the base of the second finger (Plate XII.), and denotes love of solitude, quietness, prudence, earnestness in work, proneness to the study of somber things, and appreciation... | M_019 *(retired)* |
| `unusually high` | This is found at the base of the second finger (Plate XII.), and denotes love of solitude, quietness, prudence, earnestness in work, proneness to the study of somber things, and appreciation... | M_018 *(retired)*, M_016 *(retired)* |
| `well developed` | This is found at the base of the second finger (Plate XII.), and denotes love of solitude, quietness, prudence, earnestness in work, proneness to the study of somber things, and appreciation... | M_017 *(retired)*, M_015 *(retired)* |

### `Mount of Venus` . `Development`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `abnormally large` | The Mount of Venus, abnormally large, indicates a violent passion for the opposite sex. | M_003 *(live)*, M_011 *(retired)* |
| `depressed` | The Mount of Venus may be either depressed on the hand, or very high. When depressed, such a subject will commit crime simply for the sake of crime; when high, the crime will be committed mo... | M_007 *(live)* |
| `full and large` | a person with a very poor development of the Mount of Venus is not so likely at any time to have children as the person with the mount full and large | M_004 *(live)*, M_010 *(retired)* |
| `not notably developed` | This mount denotes affection, sympathy toward others, benevolence, a desire to please, love and worship of beauty, love of color, and melody in music, and the attraction of the one sex to th... | M_013 *(retired)* |
| `not well developed` | the Mount of Venus is not well developed, thus decreasing the subject's interest in all human or natural things | M_006 *(live)* |
| `small` | A small Mount of Venus betrays poor health and, consequently, less passion. | M_002 *(live)* |
| `very high` | The Mount of Venus may be either depressed on the hand, or very high. When depressed, such a subject will commit crime simply for the sake of crime; when high, the crime will be committed mo... | M_008 *(live)*, M_012 *(retired)* |
| `very poor development` | a person with a very poor development of the Mount of Venus is not so likely at any time to have children as the person with the mount full and large | M_005 *(live)* |
| `well developed` | Venus be well developed, it indicates strong and robust health. | M_001 *(live)*, M_009 *(retired)* |

### `Mount of Venus` . `Fullness`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `full` | the full, smooth Mount of Venus indicates that the individual is less affected by those with whom he is associated | L_022 *(live)* |

### `Mount of the Sun` . `Development`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `well developed` | When well developed it indicates an enthusiastic appreciation of all things beautiful, whether or not one follows a purely artistic calling. It denotes love of painting, poetry, literature, ... | M_020 *(live)* |

### `Palm` . `Consistency`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `soft` | it is a sure sign of bad health, and particularly so on a soft hand | L_003 *(retired)* |

### `Quadrangle` . `Breadth`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `narrow` | When the line of head is so high on the hand that the space is extremely narrow between it and the line of heart, the head will completely rule the heart, if that line be the strongest. | H_010a *(live)*, H_010b *(live)*, HL_006 *(live)*, HL_021 *(live)* |

### `Square` . `Position`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `touching_Line_of_Life` | The line running through a square indicates preservation from death, from sudden death when the life-line running through is broken | L_020 *(retired)*, L_021 *(retired)* |

### `Upper Mount of Mars` . `Development`

kind: **value**

| value / target | meaning in the cited doctrine | rules |
|---|---|---|
| `large` | This, the first, gives active courage, the martial spirit, but when large, shows a very quarrelsome, fighting disposition. | M_021 *(live)*, M_022 *(retired)* |
| `not notably developed` | This, the first, gives active courage, the martial spirit, but when large, shows a very quarrelsome, fighting disposition. | M_024 *(retired)* |
| `present` | This, the first, gives active courage, the martial spirit, but when large, shows a very quarrelsome, fighting disposition. | M_023 *(live)* |

## 2 + 3. SOLICITATION MAP and ROUTING MAP

**SOLICITED** = does `palm_processor._build_description_system_prompt` (committed HEAD) actually ask
vision for this dimension? `PARTIAL` = the dimension is touched by free prose or by an adjacent closed
field, but the specific axis the rule keys on is not asked. **NO = D2-class gap.**

**ROUTED** = does the extractor parse it into a dict the engine reads? Channels:
`A` = `extract_observation` -> `observation_to_tokens.to_tokens` (flat `observation`, gated by
`_VALID_TRIPLES`); `B` = `extract_relations` directional parse (`ORIGIN/PROXIMITY/TERMINATION/
BRANCHES_TO` -> `targets[feature][Starting_Point/Proximity/Position/Branching]`, a LANDMARK);
`B2` = PROXIMITY degree -> `observation`, merged after `to_tokens`; `C` = `CONTACTS` ->
`contact_mapper.map_contact` -> `_store_relationship` (typed tokens); `D` =
`extract_mount_development` -> `observation`, merged after `to_tokens`. **NO = D1-class gap.**

| feature | attribute | SOLICITED | evidence | ROUTED | channel / why not |
|---|---|---|---|---|---|
| `Hand` | `Type` | **PARTIAL** | HAND SHAPE line asks "palm proportions (square vs elongated), overall build" -- NOT the Cheiro 7-type classification the rules key on | **NO** | feature 'Hand' absent from ontology features registry; attribute 'Type' absent from attribute_feature_mapping AND relation_types |
| `Line of Fate` | `Branching` | **YES** | BRANCHES_TO landmark -- FT_014 wants a landmark | **YES** | B:BRANCHES_TO->targets[Line of Fate][Branching] (landmark) + A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Fate` | `Continuity` | **YES** | FATE LINE prose + closed BREAK TYPE field {broken | broken_overlapping} | **YES** | A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Fate` | `Depth` | **YES** | FATE LINE prose: "same attributes" | **YES** | A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Fate` | `Length` | **YES** | FATE LINE prose "same attributes" + the closed LENGTH EXTENT field | **YES** | A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Fate` | `Position` | **YES** | closed TERMINATION menu (landmark) -- FT_003/FT_005 both want a landmark | **YES** | B:TERMINATION->targets[Line of Fate][Position] (landmark) + A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Fate` | `Proximity` | **YES** | closed PROXIMITY field | **YES** | B:PROXIMITY->targets[Line of Fate][Proximity] (landmark) + B2:PROXIMITY degree->observation (post-to_tokens merge) + A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Fate` | `Slope` | **YES** | closed SLOPE field | **YES** | A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Fate` | `Starting_Point` | **YES** | closed ORIGIN menu (landmark) | **YES** | B:ORIGIN->targets[Line of Fate][Starting_Point] (landmark) + A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Fate` | `meets` | **YES** | CONTACTS free-verb + position "mid-course"; the "at <mount>" location rides the same field | **YES** | C:CONTACTS->contact_mapper->_store_relationship |
| `Line of Fate` | `stopped_by` | **YES** | CONTACTS free-verb ("stopped by"/"barred by"/"blocked by"/"ends at") or a join verb + "at end" | **YES** | C:CONTACTS->contact_mapper->_store_relationship |
| `Line of Head` | `Branching` | **PARTIAL** | BRANCHES_TO asks for a landmark only; nothing asks for a Branching VALUE (branched / double) | **YES** | B:BRANCHES_TO->targets[Line of Head][Branching] (landmark) + A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Head` | `Continuity` | **YES** | HEAD LINE prose: "breaks/chains/forks/islands" | **YES** | A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Head` | `Depth` | **YES** | HEAD LINE prose: "depth" | **YES** | A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Head` | `Direction` | **YES** | HEAD LINE prose: "direction (straight across vs sloping downward toward the wrist/Mount of Luna)" | **YES** | A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Head` | `Length` | **YES** | HEAD LINE prose: "length" | **SPLIT** | value antecedents: YES (A:extract_observation->to_tokens(_VALID_TRIPLES)). relation_target antecedents: NO (antecedent carries a relation_target but no relational channel emits 'Length' for 'Line of Head' (S97 UNEMITTABLE class); the flat channel cannot carry a landmark) |
| `Line of Head` | `Position` | **PARTIAL** | closed TERMINATION menu yields a LANDMARK only; nothing asks for a Position VALUE (high / under_Mount_of_X / running_through_Square) | **YES** | B:TERMINATION->targets[Line of Head][Position] (landmark) + A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Head` | `Proximity` | **YES** | closed PROXIMITY field "<touching|medium|distant|n/a> to <landmark or none>" | **YES** | B:PROXIMITY->targets[Line of Head][Proximity] (landmark) + B2:PROXIMITY degree->observation (post-to_tokens merge) + A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Head` | `Slope` | **YES** | closed SLOPE field {upward | downward | straight | not clearly visible} | **YES** | A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Head` | `Starting_Point` | **YES** | closed ORIGIN menu (landmark) | **YES** | B:ORIGIN->targets[Line of Head][Starting_Point] (landmark) + A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Head` | `joins_at_origin` | **YES** | CONTACTS free-verb field, join-family verb + position "at start" | **YES** | C:CONTACTS->contact_mapper->_store_relationship |
| `Line of Heart` | `Branching` | **PARTIAL** | BRANCHES_TO landmark only; no Branching VALUE ask (single) | **YES** | B:BRANCHES_TO->targets[Line of Heart][Branching] (landmark) + A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Heart` | `Color` | **NO** | no colour ask exists for any line in the prompt | **YES** | A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Heart` | `Continuity` | **YES** | HEART LINE prose: "breaks/chains/forks/islands" | **YES** | A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Heart` | `Depth` | **YES** | HEART LINE prose: "same attributes (depth, ...)" | **YES** | A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Heart` | `Direction` | **YES** | HEART LINE prose: "direction" | **YES** | A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Heart` | `Length` | **YES** | HEART LINE prose: "length" | **YES** | A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Heart` | `Position` | **PARTIAL** | closed TERMINATION menu yields a LANDMARK only; no Position VALUE ask (high / low / under_Mount_of_X) | **YES** | B:TERMINATION->targets[Line of Heart][Position] (landmark) + A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Heart` | `Presence` | **PARTIAL** | "presence" is inherited via "same attributes"; nothing distinguishes never-present from faded-out | **NO** | attribute 'Presence' absent from attribute_feature_mapping AND relation_types |
| `Line of Heart` | `Starting_Point` | **YES** | closed ORIGIN menu (landmark) | **YES** | B:ORIGIN->targets[Line of Heart][Starting_Point] (landmark) + A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Heart` | `Width` | **YES** | HEART LINE prose: "width" | **YES** | A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Heart` | `joins_at_origin` | **YES** | CONTACTS free-verb field, join-family verb + position "at start" | **YES** | C:CONTACTS->contact_mapper->_store_relationship |
| `Line of Life` | `Clarity` | **NO** | no prompt text asks about line clarity anywhere (registry `unbound.Clarity` agrees: n=0 emissions) | **YES** | A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Life` | `Continuity` | **YES** | LIFE LINE prose: "breaks/chains/forks/islands if visible" | **YES** | A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Life` | `Curve` | **PARTIAL** | LIFE LINE prose: "course" only -- no closed menu, no straight/curved wording, no arc-extent wording | **YES** | A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Life` | `Depth` | **YES** | LIFE LINE prose: "depth" | **YES** | A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Life` | `Length` | **YES** | LIFE LINE prose: "length" | **YES** | A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Life` | `Starting_Point` | **PARTIAL** | LIFE LINE prose: "origin and end" -- free prose only; Life has no closed ORIGIN menu | **YES** | A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Line of Life` | `Width` | **YES** | LIFE LINE prose: "width (narrow/thin vs broad/thick)" | **YES** | A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Mount of Jupiter` | `Development` | **YES** | closed DEVELOPMENT (Jupiter) menu, 3 tokens | **YES** | D:extract_mount_development->observation (post-to_tokens merge) + A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Mount of Saturn` | `Development` | **YES** | closed DEVELOPMENT (Saturn) menu, 4 tokens | **YES** | D:extract_mount_development->observation (post-to_tokens merge) + A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Mount of Venus` | `Development` | **YES** | closed DEVELOPMENT (Venus) menu, 10 tokens | **YES** | D:extract_mount_development->observation (post-to_tokens merge) + A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Mount of Venus` | `Fullness` | **PARTIAL** | MOUNTS prose "which pads appear developed, flat, or unremarkable" -- no fullness/smoothness ask; Venus DEVELOPMENT menu has no "full" token either | **YES** | A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Mount of the Sun` | `Development` | **YES** | closed DEVELOPMENT (the Sun) menu, 3 tokens | **YES** | D:extract_mount_development->observation (post-to_tokens merge) + A:extract_observation->to_tokens(_VALID_TRIPLES) |
| `Palm` | `Consistency` | **NO** | no palm-consistency ask (soft/hard/flabby/elastic) anywhere in the prompt | **NO** | feature 'Palm' absent from _FEATURE_ALIAS -- no prose ever reaches the extractor for it |
| `Quadrangle` | `Breadth` | **NO** | the Quadrangle is never named; no head-to-heart-spacing ask exists | **NO** | feature 'Quadrangle' absent from _FEATURE_ALIAS -- no prose ever reaches the extractor for it |
| `Square` | `Position` | **PARTIAL** | MARKS line asks for "squares ... only if clearly visible" but never where a square sits relative to a line | **NO** | feature 'Square' absent from _FEATURE_ALIAS -- no prose ever reaches the extractor for it |
| `Upper Mount of Mars` | `Development` | **YES** | closed DEVELOPMENT (Upper Mount of Mars) menu, 4 tokens | **YES** | D:extract_mount_development->observation (post-to_tokens merge) + A:extract_observation->to_tokens(_VALID_TRIPLES) |

## 4. CANONICAL COVERAGE

For each required value/meaning: is there a canonical token in `emission_menus` that expresses it?
`covered` = exact member of the bound menu. `MISSING` = no bound menu token expresses it -- the rule
**can never fire even with a perfect adapter**, because the attribute is UNBOUND in `emission_menus`
(so vision is never forced to say it) or the value is off-menu. `flattened-granularity` = a coarser
bound token exists but loses the distinction the rule needs.

| feature | attribute | value | coverage | detail |
|---|---|---|---|---|
| `Hand` | `Type` | `philosophic` | **MISSING** | attribute UNBOUND in emission_menus AND 'philosophic' absent from the flat registry `values` pool |
| `Hand` | `Type` | `spatulate` | **MISSING** | attribute UNBOUND in emission_menus; 'spatulate' exists only in the flat registry `values` pool |
| `Hand` | `Type` | `square` | **MISSING** | attribute UNBOUND in emission_menus; 'square' exists only in the flat registry `values` pool |
| `Line of Fate` | `Continuity` | `broken` | **covered** | exact member of emission_menus[Line of Fate][Continuity] |
| `Line of Fate` | `Continuity` | `broken_overlapping` | **MISSING** | not in emission_menus[Line of Fate][Continuity] = ['unbroken', 'broken', 'chained', 'forked', 'islanded'] |
| `Line of Fate` | `Continuity` | `double` | **MISSING** | not in emission_menus[Line of Fate][Continuity] = ['unbroken', 'broken', 'chained', 'forked', 'islanded'] |
| `Line of Fate` | `Depth` | `well_marked` | **MISSING** | not in emission_menus[Line of Fate][Depth] = ['deep', 'shallow'] |
| `Line of Fate` | `Length` | `cutting_into_finger_of_Saturn` | **MISSING** | not in emission_menus[Line of Fate][Length] = ['short', 'medium', 'long'] |
| `Line of Fate` | `Proximity` | `touching` | **covered** | exact member of emission_menus[Line of Fate][Proximity] |
| `Line of Fate` | `Slope` | `straight` | **covered** | exact member of emission_menus[Line of Fate][Slope] |
| `Line of Head` | `Branching` | `branched` | **MISSING** | attribute UNBOUND in emission_menus; 'branched' exists only in the flat registry `values` pool |
| `Line of Head` | `Branching` | `double` | **MISSING** | attribute UNBOUND in emission_menus; 'double' exists only in the flat registry `values` pool |
| `Line of Head` | `Continuity` | `broken` | **covered** | exact member of emission_menus[Line of Head][Continuity] |
| `Line of Head` | `Continuity` | `chained` | **covered** | exact member of emission_menus[Line of Head][Continuity] |
| `Line of Head` | `Continuity` | `clear` | **MISSING** | not in emission_menus[Line of Head][Continuity] = ['unbroken', 'broken', 'chained', 'forked', 'islanded'] |
| `Line of Head` | `Continuity` | `islanded` | **covered** | exact member of emission_menus[Line of Head][Continuity] |
| `Line of Head` | `Depth` | `well_marked` | **MISSING** | not in emission_menus[Line of Head][Depth] = ['deep', 'shallow'] |
| `Line of Head` | `Direction` | `sloping` | **MISSING** | attribute UNBOUND in emission_menus; 'sloping' exists only in the flat registry `values` pool |
| `Line of Head` | `Direction` | `straight` | **MISSING** | attribute UNBOUND in emission_menus; 'straight' exists only in the flat registry `values` pool |
| `Line of Head` | `Length` | `long` | **covered** | exact member of emission_menus[Line of Head][Length] |
| `Line of Head` | `Length` | `reaching_Line_of_Heart` | **MISSING** | not in emission_menus[Line of Head][Length] = ['short', 'medium', 'long'] |
| `Line of Head` | `Length` | `short` | **covered** | exact member of emission_menus[Line of Head][Length] |
| `Line of Head` | `Position` | `high` | **MISSING** | attribute UNBOUND in emission_menus; 'high' exists only in the flat registry `values` pool |
| `Line of Head` | `Position` | `running_through_Square` | **MISSING** | attribute UNBOUND in emission_menus; 'running_through_Square' exists only in the flat registry `values` pool |
| `Line of Head` | `Position` | `terminating_on_Mount` | **MISSING** | attribute UNBOUND in emission_menus AND 'terminating_on_Mount' absent from the flat registry `values` pool |
| `Line of Head` | `Position` | `terminating_on_Mount_of_Jupiter` | **MISSING** | attribute UNBOUND in emission_menus AND 'terminating_on_Mount_of_Jupiter' absent from the flat registry `values` pool |
| `Line of Head` | `Position` | `terminating_on_Mount_of_Moon` | **MISSING** | attribute UNBOUND in emission_menus AND 'terminating_on_Mount_of_Moon' absent from the flat registry `values` pool |
| `Line of Head` | `Position` | `under_Mount_of_Saturn` | **MISSING** | attribute UNBOUND in emission_menus; 'under_Mount_of_Saturn' exists only in the flat registry `values` pool |
| `Line of Head` | `Proximity` | `distant` | **covered** | exact member of emission_menus[Line of Head][Proximity] |
| `Line of Head` | `Proximity` | `medium` | **covered** | exact member of emission_menus[Line of Head][Proximity] |
| `Line of Head` | `Proximity` | `touching` | **covered** | exact member of emission_menus[Line of Head][Proximity] |
| `Line of Head` | `Proximity` | `touching_Line_of_Life` | **MISSING** | not in emission_menus[Line of Head][Proximity] = ['touching', 'medium', 'distant'] |
| `Line of Head` | `Slope` | `downward` | **covered** | exact member of emission_menus[Line of Head][Slope] |
| `Line of Head` | `Starting_Point` | `rising_from_Line_of_Life` | **MISSING** | attribute UNBOUND in emission_menus; 'rising_from_Line_of_Life' exists only in the flat registry `values` pool |
| `Line of Head` | `Starting_Point` | `rising_from_Mount_of_Jupiter` | **MISSING** | attribute UNBOUND in emission_menus; 'rising_from_Mount_of_Jupiter' exists only in the flat registry `values` pool |
| `Line of Head` | `Starting_Point` | `rising_from_Mount_of_Mars` | **MISSING** | attribute UNBOUND in emission_menus; 'rising_from_Mount_of_Mars' exists only in the flat registry `values` pool |
| `Line of Heart` | `Branching` | `single` | **MISSING** | attribute UNBOUND in emission_menus; 'single' exists only in the flat registry `values` pool |
| `Line of Heart` | `Color` | `bright_red` | **MISSING** | attribute UNBOUND in emission_menus; 'bright_red' exists only in the flat registry `values` pool |
| `Line of Heart` | `Color` | `pale` | **MISSING** | attribute UNBOUND in emission_menus; 'pale' exists only in the flat registry `values` pool |
| `Line of Heart` | `Continuity` | `barred` | **MISSING** | not in emission_menus[Line of Heart][Continuity] = ['unbroken', 'broken', 'chained', 'forked', 'islanded'] |
| `Line of Heart` | `Continuity` | `broken` | **covered** | exact member of emission_menus[Line of Heart][Continuity] |
| `Line of Heart` | `Continuity` | `chained` | **covered** | exact member of emission_menus[Line of Heart][Continuity] |
| `Line of Heart` | `Continuity` | `forked` | **covered** | exact member of emission_menus[Line of Heart][Continuity] |
| `Line of Heart` | `Direction` | `drooping` | **MISSING** | attribute UNBOUND in emission_menus; 'drooping' exists only in the flat registry `values` pool |
| `Line of Heart` | `Length` | `extending_across_entire_palm` | **flattened-granularity** | not in emission_menus[Line of Heart][Length] = ['short', 'medium', 'long'] -- a coarser bound token exists; the doctrine-specific extreme is lost |
| `Line of Heart` | `Position` | `high` | **MISSING** | attribute UNBOUND in emission_menus; 'high' exists only in the flat registry `values` pool |
| `Line of Heart` | `Position` | `low` | **MISSING** | attribute UNBOUND in emission_menus; 'low' exists only in the flat registry `values` pool |
| `Line of Heart` | `Position` | `under_Mount_of_Mercury` | **MISSING** | attribute UNBOUND in emission_menus; 'under_Mount_of_Mercury' exists only in the flat registry `values` pool |
| `Line of Heart` | `Position` | `under_Mount_of_Saturn` | **MISSING** | attribute UNBOUND in emission_menus; 'under_Mount_of_Saturn' exists only in the flat registry `values` pool |
| `Line of Heart` | `Position` | `under_Mount_of_Sun` | **MISSING** | attribute UNBOUND in emission_menus; 'under_Mount_of_Sun' exists only in the flat registry `values` pool |
| `Line of Heart` | `Presence` | `faded` | **MISSING** | attribute UNBOUND in emission_menus AND 'faded' absent from the flat registry `values` pool |
| `Line of Heart` | `Starting_Point` | `between_Jupiter_and_Saturn` | **MISSING** | attribute UNBOUND in emission_menus; 'between_Jupiter_and_Saturn' exists only in the flat registry `values` pool |
| `Line of Heart` | `Starting_Point` | `rising_from_Finger_of_Jupiter` | **MISSING** | attribute UNBOUND in emission_menus AND 'rising_from_Finger_of_Jupiter' absent from the flat registry `values` pool |
| `Line of Heart` | `Starting_Point` | `rising_from_Mount_of_Jupiter` | **MISSING** | attribute UNBOUND in emission_menus; 'rising_from_Mount_of_Jupiter' exists only in the flat registry `values` pool |
| `Line of Heart` | `Starting_Point` | `rising_from_Mount_of_Saturn` | **MISSING** | attribute UNBOUND in emission_menus; 'rising_from_Mount_of_Saturn' exists only in the flat registry `values` pool |
| `Line of Heart` | `Width` | `thin` | **MISSING** | not in emission_menus[Line of Heart][Width] = ['narrow', 'broad'] |
| `Line of Heart` | `Width` | `wide` | **MISSING** | not in emission_menus[Line of Heart][Width] = ['narrow', 'broad'] |
| `Line of Life` | `Clarity` | `clear` | **MISSING** | attribute UNBOUND in emission_menus; 'clear' exists only in the flat registry `values` pool |
| `Line of Life` | `Continuity` | `broken` | **covered** | exact member of emission_menus[Line of Life][Continuity] |
| `Line of Life` | `Continuity` | `chained` | **covered** | exact member of emission_menus[Line of Life][Continuity] |
| `Line of Life` | `Continuity` | `islanded` | **covered** | exact member of emission_menus[Line of Life][Continuity] |
| `Line of Life` | `Curve` | `close_to_Mount_of_Venus` | **flattened-granularity** | not in emission_menus[Line of Life][Curve] = ['straight', 'curved'] -- a coarser bound token exists; the doctrine-specific extreme is lost |
| `Line of Life` | `Curve` | `sweeping_wide` | **flattened-granularity** | not in emission_menus[Line of Life][Curve] = ['straight', 'curved'] -- a coarser bound token exists; the doctrine-specific extreme is lost |
| `Line of Life` | `Depth` | `deep` | **covered** | exact member of emission_menus[Line of Life][Depth] |
| `Line of Life` | `Length` | `long` | **covered** | exact member of emission_menus[Line of Life][Length] |
| `Line of Life` | `Length` | `short` | **covered** | exact member of emission_menus[Line of Life][Length] |
| `Line of Life` | `Starting_Point` | `at_start` | **MISSING** | attribute UNBOUND in emission_menus; 'at_start' exists only in the flat registry `values` pool |
| `Line of Life` | `Starting_Point` | `rising_from_Mount_of_Jupiter` | **MISSING** | attribute UNBOUND in emission_menus; 'rising_from_Mount_of_Jupiter' exists only in the flat registry `values` pool |
| `Line of Life` | `Starting_Point` | `under_Mount_of_Jupiter` | **MISSING** | attribute UNBOUND in emission_menus; 'under_Mount_of_Jupiter' exists only in the flat registry `values` pool |
| `Line of Life` | `Width` | `narrow` | **covered** | exact member of emission_menus[Line of Life][Width] |
| `Mount of Jupiter` | `Development` | `developed` | **covered** | exact member of emission_menus[Mount of Jupiter][Development] |
| `Mount of Saturn` | `Development` | `not notably developed` | **covered** | exact member of emission_menus[Mount of Saturn][Development] |
| `Mount of Saturn` | `Development` | `unusually high` | **covered** | exact member of emission_menus[Mount of Saturn][Development] |
| `Mount of Saturn` | `Development` | `well developed` | **covered** | exact member of emission_menus[Mount of Saturn][Development] |
| `Mount of Venus` | `Development` | `abnormally large` | **covered** | exact member of emission_menus[Mount of Venus][Development] |
| `Mount of Venus` | `Development` | `depressed` | **covered** | exact member of emission_menus[Mount of Venus][Development] |
| `Mount of Venus` | `Development` | `full and large` | **covered** | exact member of emission_menus[Mount of Venus][Development] |
| `Mount of Venus` | `Development` | `not notably developed` | **covered** | exact member of emission_menus[Mount of Venus][Development] |
| `Mount of Venus` | `Development` | `not well developed` | **covered** | exact member of emission_menus[Mount of Venus][Development] |
| `Mount of Venus` | `Development` | `small` | **covered** | exact member of emission_menus[Mount of Venus][Development] |
| `Mount of Venus` | `Development` | `very high` | **covered** | exact member of emission_menus[Mount of Venus][Development] |
| `Mount of Venus` | `Development` | `very poor development` | **covered** | exact member of emission_menus[Mount of Venus][Development] |
| `Mount of Venus` | `Development` | `well developed` | **covered** | exact member of emission_menus[Mount of Venus][Development] |
| `Mount of Venus` | `Fullness` | `full` | **MISSING** | attribute UNBOUND in emission_menus; 'full' exists only in the flat registry `values` pool |
| `Mount of the Sun` | `Development` | `well developed` | **covered** | exact member of emission_menus[Mount of the Sun][Development] |
| `Palm` | `Consistency` | `soft` | **MISSING** | attribute UNBOUND in emission_menus; 'soft' exists only in the flat registry `values` pool |
| `Quadrangle` | `Breadth` | `narrow` | **MISSING** | attribute UNBOUND in emission_menus; 'narrow' exists only in the flat registry `values` pool |
| `Square` | `Position` | `touching_Line_of_Life` | **MISSING** | attribute UNBOUND in emission_menus; 'touching_Line_of_Life' exists only in the flat registry `values` pool |
| `Upper Mount of Mars` | `Development` | `large` | **covered** | exact member of emission_menus[Upper Mount of Mars][Development] |
| `Upper Mount of Mars` | `Development` | `not notably developed` | **covered** | exact member of emission_menus[Upper Mount of Mars][Development] |
| `Upper Mount of Mars` | `Development` | `present` | **covered** | exact member of emission_menus[Upper Mount of Mars][Development] |

Relation-target and comparative antecedents need no value token (`n/a`): 21 of 149 antecedent instances.

Coverage totals over 91 distinct required values: MISSING=49, covered=39, flattened-granularity=3

## 5. MASTER GAP LEDGER

Every gap found, one row per distinct gap unit. Classes may co-occur on one antecedent (a rule can be
both unsolicited and token-absent); the row carries all of them.

| class | meaning |
|---|---|
| **D1** | unrouted -- no extractor channel produces this (feature, attribute) at all |
| **D2** | unsolicited -- the vision prompt never asks for the dimension the rule keys on |
| **D3** | token-absent -- no canonical `emission_menus` token expresses the required value |
| **D4** | literal-should-be-relation_target -- the value literal names a landmark the relational channel already carries as a target |
| **D5** | synonym -- the value is a synonym of a bound menu token; already scheduled in `emission_menus.normalization_worklist` |
| **D6** | unobserved -- routed + solicited + canonical, but the state has never been seen on a real hand |

| # | class | feature | attribute | value / target | rules | bucket | what closes it |
|---|---|---|---|---|---|---|---|
| 1 | **D1+D2+D3** | `Hand` | `Type` | `philosophic` | H_020 | live | route it: feature 'Hand' absent from ontology features registry; attribute 'Type' absent from attribute_feature_mapping AND relation_types; solicit it: HAND SHAPE line asks "palm proportions (square vs elongated), overall build" -- NOT the Cheiro 7-type classification the rules key on; no canonical token exists for 'philosophic' anywhere (menu or flat pool) -- rule can never fire |
| 2 | **D1+D2+D3** | `Hand` | `Type` | `spatulate` | H_019 | live | route it: feature 'Hand' absent from ontology features registry; attribute 'Type' absent from attribute_feature_mapping AND relation_types; solicit it: HAND SHAPE line asks "palm proportions (square vs elongated), overall build" -- NOT the Cheiro 7-type classification the rules key on; attribute 'Type' is UNBOUND in emission_menus -- 'spatulate' has no canonical menu token, only flat-pool membership |
| 3 | **D1+D2+D3** | `Hand` | `Type` | `square` | H_018 | live | route it: feature 'Hand' absent from ontology features registry; attribute 'Type' absent from attribute_feature_mapping AND relation_types; solicit it: HAND SHAPE line asks "palm proportions (square vs elongated), overall build" -- NOT the Cheiro 7-type classification the rules key on; attribute 'Type' is UNBOUND in emission_menus -- 'square' has no canonical menu token, only flat-pool membership |
| 4 | **D1+D2+D3** | `Line of Heart` | `Presence` | `faded` | HL_015 | live | route it: attribute 'Presence' absent from attribute_feature_mapping AND relation_types; solicit it: "presence" is inherited via "same attributes"; nothing distinguishes never-present from faded-out; no canonical token exists for 'faded' anywhere (menu or flat pool) -- rule can never fire |
| 5 | **D1+D2+D3** | `Palm` | `Consistency` | `soft` | L_003 | retired | route it: feature 'Palm' absent from _FEATURE_ALIAS -- no prose ever reaches the extractor for it; solicit it: no palm-consistency ask (soft/hard/flabby/elastic) anywhere in the prompt; attribute 'Consistency' is UNBOUND in emission_menus -- 'soft' has no canonical menu token, only flat-pool membership |
| 6 | **D1+D2+D3** | `Quadrangle` | `Breadth` | `narrow` | HL_006, HL_021, H_010a, H_010b | live | route it: feature 'Quadrangle' absent from _FEATURE_ALIAS -- no prose ever reaches the extractor for it; solicit it: the Quadrangle is never named; no head-to-heart-spacing ask exists; attribute 'Breadth' is UNBOUND in emission_menus -- 'narrow' has no canonical menu token, only flat-pool membership |
| 7 | **D1+D2+D3** | `Square` | `Position` | `touching_Line_of_Life` | L_020, L_021 | retired | route it: feature 'Square' absent from _FEATURE_ALIAS -- no prose ever reaches the extractor for it; solicit it: MARKS line asks for "squares ... only if clearly visible" but never where a square sits relative to a line; attribute 'Position' is UNBOUND in emission_menus -- 'touching_Line_of_Life' has no canonical menu token, only flat-pool membership |
| 8 | **D1+D3** | `Line of Head` | `Length` | `reaching_Line_of_Heart` | H_022 | parked | route it: antecedent carries a relation_target but no relational channel emits 'Length' for 'Line of Head' (S97 UNEMITTABLE class); the flat channel cannot carry a landmark; no canonical token exists for 'reaching_Line_of_Heart' anywhere (menu or flat pool) -- rule can never fire |
| 9 | **D2** | `Line of Head` | `Branching` | -> `Line of Heart` | H_014 | live | solicit it: BRANCHES_TO asks for a landmark only; nothing asks for a Branching VALUE (branched / double) |
| 10 | **D2+D3** | `Line of Head` | `Branching` | `branched` | H_013, H_023, H_024 | live | solicit it: BRANCHES_TO asks for a landmark only; nothing asks for a Branching VALUE (branched / double); attribute 'Branching' is UNBOUND in emission_menus -- 'branched' has no canonical menu token, only flat-pool membership |
| 11 | **D2+D3** | `Line of Head` | `Branching` | `double` | H_025 | live | solicit it: BRANCHES_TO asks for a landmark only; nothing asks for a Branching VALUE (branched / double); attribute 'Branching' is UNBOUND in emission_menus -- 'double' has no canonical menu token, only flat-pool membership |
| 12 | **D2+D3** | `Line of Head` | `Position` | `high` | H_010a, H_010b, H_020, H_021, H_022 | live/parked | solicit it: closed TERMINATION menu yields a LANDMARK only; nothing asks for a Position VALUE (high / under_Mount_of_X / running_through_Square); attribute 'Position' is UNBOUND in emission_menus -- 'high' has no canonical menu token, only flat-pool membership |
| 13 | **D2+D3** | `Line of Heart` | `Branching` | `single` | HL_014 | live | solicit it: BRANCHES_TO landmark only; no Branching VALUE ask (single); attribute 'Branching' is UNBOUND in emission_menus -- 'single' has no canonical menu token, only flat-pool membership |
| 14 | **D2+D3** | `Line of Heart` | `Color` | `bright_red` | HL_019 | live | solicit it: no colour ask exists for any line in the prompt; attribute 'Color' is UNBOUND in emission_menus -- 'bright_red' has no canonical menu token, only flat-pool membership |
| 15 | **D2+D3** | `Line of Heart` | `Color` | `pale` | HL_020 | live | solicit it: no colour ask exists for any line in the prompt; attribute 'Color' is UNBOUND in emission_menus -- 'pale' has no canonical menu token, only flat-pool membership |
| 16 | **D2+D3** | `Line of Heart` | `Position` | `high` | HL_005, HL_006, HL_011 | live | solicit it: closed TERMINATION menu yields a LANDMARK only; no Position VALUE ask (high / low / under_Mount_of_X); attribute 'Position' is UNBOUND in emission_menus -- 'high' has no canonical menu token, only flat-pool membership |
| 17 | **D2+D3** | `Line of Heart` | `Position` | `low` | HL_012, HL_021 | live | solicit it: closed TERMINATION menu yields a LANDMARK only; no Position VALUE ask (high / low / under_Mount_of_X); attribute 'Position' is UNBOUND in emission_menus -- 'low' has no canonical menu token, only flat-pool membership |
| 18 | **D2+D3** | `Line of Life` | `Clarity` | `clear` | L_018 | live | solicit it: no prompt text asks about line clarity anywhere (registry `unbound.Clarity` agrees: n=0 emissions); attribute 'Clarity' is UNBOUND in emission_menus -- 'clear' has no canonical menu token, only flat-pool membership |
| 19 | **D2+D3** | `Line of Life` | `Curve` | `close_to_Mount_of_Venus` | L_024 | live | solicit it: LIFE LINE prose: "course" only -- no closed menu, no straight/curved wording, no arc-extent wording; 'close_to_Mount_of_Venus' absent from emission_menus[Line of Life][Curve]=['straight', 'curved'] |
| 20 | **D2+D3** | `Line of Life` | `Curve` | `sweeping_wide` | L_023 | live | solicit it: LIFE LINE prose: "course" only -- no closed menu, no straight/curved wording, no arc-extent wording; 'sweeping_wide' absent from emission_menus[Line of Life][Curve]=['straight', 'curved'] |
| 21 | **D2+D3** | `Line of Life` | `Starting_Point` | `at_start` | L_018 | live | solicit it: LIFE LINE prose: "origin and end" -- free prose only; Life has no closed ORIGIN menu; attribute 'Starting_Point' is UNBOUND in emission_menus -- 'at_start' has no canonical menu token, only flat-pool membership |
| 22 | **D2+D3** | `Line of Life` | `Starting_Point` | `rising_from_Mount_of_Jupiter` | L_004 | live | solicit it: LIFE LINE prose: "origin and end" -- free prose only; Life has no closed ORIGIN menu; attribute 'Starting_Point' is UNBOUND in emission_menus -- 'rising_from_Mount_of_Jupiter' has no canonical menu token, only flat-pool membership |
| 23 | **D2+D3** | `Line of Life` | `Starting_Point` | `under_Mount_of_Jupiter` | L_005 | live | solicit it: LIFE LINE prose: "origin and end" -- free prose only; Life has no closed ORIGIN menu; attribute 'Starting_Point' is UNBOUND in emission_menus -- 'under_Mount_of_Jupiter' has no canonical menu token, only flat-pool membership |
| 24 | **D2+D3** | `Mount of Venus` | `Fullness` | `full` | L_022 | live | solicit it: MOUNTS prose "which pads appear developed, flat, or unremarkable" -- no fullness/smoothness ask; Venus DEVELOPMENT menu has no "full" token either; attribute 'Fullness' is UNBOUND in emission_menus -- 'full' has no canonical menu token, only flat-pool membership |
| 25 | **D2+D3+D4** | `Line of Head` | `Position` | `running_through_Square` | H_015 | live | solicit it: closed TERMINATION menu yields a LANDMARK only; nothing asks for a Position VALUE (high / under_Mount_of_X / running_through_Square); attribute 'Position' is UNBOUND in emission_menus -- 'running_through_Square' has no canonical menu token, only flat-pool membership; literal 'running_through_Square' names a landmark already carried on the relational channel as targets[Line of Head][Position] |
| 26 | **D2+D3+D4** | `Line of Head` | `Position` | `terminating_on_Mount` | H_023 | live | solicit it: closed TERMINATION menu yields a LANDMARK only; nothing asks for a Position VALUE (high / under_Mount_of_X / running_through_Square); no canonical token exists for 'terminating_on_Mount' anywhere (menu or flat pool) -- rule can never fire; literal 'terminating_on_Mount' names a landmark already carried on the relational channel as targets[Line of Head][Position] |
| 27 | **D2+D3+D4** | `Line of Head` | `Position` | `terminating_on_Mount_of_Jupiter` | H_013 | live | solicit it: closed TERMINATION menu yields a LANDMARK only; nothing asks for a Position VALUE (high / under_Mount_of_X / running_through_Square); no canonical token exists for 'terminating_on_Mount_of_Jupiter' anywhere (menu or flat pool) -- rule can never fire; literal 'terminating_on_Mount_of_Jupiter' names a landmark already carried on the relational channel as targets[Line of Head][Position] |
| 28 | **D2+D3+D4** | `Line of Head` | `Position` | `terminating_on_Mount_of_Moon` | H_024 | live | solicit it: closed TERMINATION menu yields a LANDMARK only; nothing asks for a Position VALUE (high / under_Mount_of_X / running_through_Square); no canonical token exists for 'terminating_on_Mount_of_Moon' anywhere (menu or flat pool) -- rule can never fire; literal 'terminating_on_Mount_of_Moon' names a landmark already carried on the relational channel as targets[Line of Head][Position] |
| 29 | **D2+D3+D4** | `Line of Head` | `Position` | `under_Mount_of_Saturn` | H_007 | live | solicit it: closed TERMINATION menu yields a LANDMARK only; nothing asks for a Position VALUE (high / under_Mount_of_X / running_through_Square); attribute 'Position' is UNBOUND in emission_menus -- 'under_Mount_of_Saturn' has no canonical menu token, only flat-pool membership; literal 'under_Mount_of_Saturn' names a landmark already carried on the relational channel as targets[Line of Head][Position] |
| 30 | **D2+D3+D4** | `Line of Heart` | `Position` | `under_Mount_of_Mercury` | HL_009 | live | solicit it: closed TERMINATION menu yields a LANDMARK only; no Position VALUE ask (high / low / under_Mount_of_X); attribute 'Position' is UNBOUND in emission_menus -- 'under_Mount_of_Mercury' has no canonical menu token, only flat-pool membership; literal 'under_Mount_of_Mercury' names a landmark already carried on the relational channel as targets[Line of Heart][Position] |
| 31 | **D2+D3+D4** | `Line of Heart` | `Position` | `under_Mount_of_Saturn` | HL_007 | live | solicit it: closed TERMINATION menu yields a LANDMARK only; no Position VALUE ask (high / low / under_Mount_of_X); attribute 'Position' is UNBOUND in emission_menus -- 'under_Mount_of_Saturn' has no canonical menu token, only flat-pool membership; literal 'under_Mount_of_Saturn' names a landmark already carried on the relational channel as targets[Line of Heart][Position] |
| 32 | **D2+D3+D4** | `Line of Heart` | `Position` | `under_Mount_of_Sun` | HL_008 | live | solicit it: closed TERMINATION menu yields a LANDMARK only; no Position VALUE ask (high / low / under_Mount_of_X); attribute 'Position' is UNBOUND in emission_menus -- 'under_Mount_of_Sun' has no canonical menu token, only flat-pool membership; literal 'under_Mount_of_Sun' names a landmark already carried on the relational channel as targets[Line of Heart][Position] |
| 33 | **D3** | `Line of Fate` | `Continuity` | `broken_overlapping` | FT_012 | live | normalization_worklist rekey: Line of Fate.Continuity -> Break_Type |
| 34 | **D3** | `Line of Fate` | `Continuity` | `double` | FT_013 | live | 'double' absent from emission_menus[Line of Fate][Continuity]=['unbroken', 'broken', 'chained', 'forked', 'islanded'] |
| 35 | **D3** | `Line of Fate` | `Length` | `cutting_into_finger_of_Saturn` | FT_006 | live | normalization_worklist rekey: Line of Fate.Length -> Length_Extent |
| 36 | **D3** | `Line of Head` | `Direction` | `straight` | H_004, H_020 | live | normalization_worklist: attribute_migration |
| 37 | **D3** | `Line of Heart` | `Continuity` | `barred` | HL_017 | live | 'barred' absent from emission_menus[Line of Heart][Continuity]=['unbroken', 'broken', 'chained', 'forked', 'islanded'] |
| 38 | **D3** | `Line of Heart` | `Length` | `extending_across_entire_palm` | HL_016 | live | 'extending_across_entire_palm' absent from emission_menus[Line of Heart][Length]=['short', 'medium', 'long'] |
| 39 | **D3+D4** | `Line of Head` | `Proximity` | `touching_Line_of_Life` | H_001 | retired | 'touching_Line_of_Life' absent from emission_menus[Line of Head][Proximity]=['touching', 'medium', 'distant']; literal 'touching_Line_of_Life' names a landmark already carried on the relational channel as targets[Line of Head][Proximity] |
| 40 | **D3+D4** | `Line of Head` | `Starting_Point` | `rising_from_Line_of_Life` | H_002 | live | attribute 'Starting_Point' is UNBOUND in emission_menus -- 'rising_from_Line_of_Life' has no canonical menu token, only flat-pool membership; literal 'rising_from_Line_of_Life' names a landmark already carried on the relational channel as targets[Line of Head][Starting_Point] |
| 41 | **D3+D4** | `Line of Head` | `Starting_Point` | `rising_from_Mount_of_Jupiter` | H_001 | retired | attribute 'Starting_Point' is UNBOUND in emission_menus -- 'rising_from_Mount_of_Jupiter' has no canonical menu token, only flat-pool membership; literal 'rising_from_Mount_of_Jupiter' names a landmark already carried on the relational channel as targets[Line of Head][Starting_Point] |
| 42 | **D3+D4** | `Line of Head` | `Starting_Point` | `rising_from_Mount_of_Mars` | H_003 | live | attribute 'Starting_Point' is UNBOUND in emission_menus -- 'rising_from_Mount_of_Mars' has no canonical menu token, only flat-pool membership; literal 'rising_from_Mount_of_Mars' names a landmark already carried on the relational channel as targets[Line of Head][Starting_Point] |
| 43 | **D3+D4** | `Line of Heart` | `Starting_Point` | `between_Jupiter_and_Saturn` | HL_003 | live | attribute 'Starting_Point' is UNBOUND in emission_menus -- 'between_Jupiter_and_Saturn' has no canonical menu token, only flat-pool membership; literal 'between_Jupiter_and_Saturn' names a landmark already carried on the relational channel as targets[Line of Heart][Starting_Point] |
| 44 | **D3+D4** | `Line of Heart` | `Starting_Point` | `rising_from_Finger_of_Jupiter` | HL_002 | live | no canonical token exists for 'rising_from_Finger_of_Jupiter' anywhere (menu or flat pool) -- rule can never fire; literal 'rising_from_Finger_of_Jupiter' names a landmark already carried on the relational channel as targets[Line of Heart][Starting_Point] |
| 45 | **D3+D4** | `Line of Heart` | `Starting_Point` | `rising_from_Mount_of_Jupiter` | HL_001, HL_010 | live | attribute 'Starting_Point' is UNBOUND in emission_menus -- 'rising_from_Mount_of_Jupiter' has no canonical menu token, only flat-pool membership; literal 'rising_from_Mount_of_Jupiter' names a landmark already carried on the relational channel as targets[Line of Heart][Starting_Point] |
| 46 | **D3+D4** | `Line of Heart` | `Starting_Point` | `rising_from_Mount_of_Saturn` | HL_004, HL_005, HL_018 | live | attribute 'Starting_Point' is UNBOUND in emission_menus -- 'rising_from_Mount_of_Saturn' has no canonical menu token, only flat-pool membership; literal 'rising_from_Mount_of_Saturn' names a landmark already carried on the relational channel as targets[Line of Heart][Starting_Point] |
| 47 | **D5** | `Line of Fate` | `Depth` | `well_marked` | FT_001 | live | normalization_worklist: well_marked -> deep |
| 48 | **D5** | `Line of Head` | `Continuity` | `clear` | H_004 | live | normalization_worklist: clear -> unbroken |
| 49 | **D5** | `Line of Head` | `Depth` | `well_marked` | FT_009 | live | normalization_worklist: well_marked -> deep |
| 50 | **D5** | `Line of Head` | `Direction` | `sloping` | H_018, H_019 | live | normalization_worklist: value_normalization+attribute_migration |
| 51 | **D5** | `Line of Heart` | `Direction` | `drooping` | HL_012 | live | normalization_worklist: value_normalization+attribute_migration |
| 52 | **D5** | `Line of Heart` | `Width` | `thin` | HL_014 | live | normalization_worklist: thin -> narrow |
| 53 | **D5** | `Line of Heart` | `Width` | `wide` | HL_013, HL_018, HL_020 | live | normalization_worklist: wide -> broad |
| 54 | **D6** | `Line of Fate` | `Continuity` | `broken` | FT_011 | live | CHANNEL-SILENT: solicited YES + routed YES, yet the n=1 live capture (s117) produced no Continuity value for Line of Fate at all -- plausibly honest absence on that hand, but unproven; needs a second capture to separate honest-absence from a dead channel |
| 55 | **D6** | `Line of Fate` | `meets` | -> `Line of Heart` | FT_016 | live | CLAUDE.md S104: parked model-perception-limited |
| 56 | **D6** | `Line of Fate` | `stopped_by` | -> `Line of Heart` | FT_007 | live | CLAUDE.md S115: PARKED PERMANENTLY -- no live stopped_by hand sourced (fixture-only since S112) |
| 57 | **D6** | `Line of Fate` | `stopped_by` | -> `Line of Head` | FT_008 | live | CLAUDE.md S115: PARKED PERMANENTLY -- no live stopped_by hand sourced (fixture-only since S112) |
| 58 | **D6** | `Line of Head` | `Continuity` | `broken` | H_007, H_011 | live | CHANNEL-SILENT: solicited YES + routed YES, yet the n=1 live capture (s117) produced no Continuity value for Line of Head at all -- plausibly honest absence on that hand, but unproven; needs a second capture to separate honest-absence from a dead channel |
| 59 | **D6** | `Line of Head` | `Continuity` | `chained` | H_008 | live | CHANNEL-SILENT: solicited YES + routed YES, yet the n=1 live capture (s117) produced no Continuity value for Line of Head at all -- plausibly honest absence on that hand, but unproven; needs a second capture to separate honest-absence from a dead channel |
| 60 | **D6** | `Line of Head` | `Continuity` | `islanded` | H_009, H_012 | live | CHANNEL-SILENT: solicited YES + routed YES, yet the n=1 live capture (s117) produced no Continuity value for Line of Head at all -- plausibly honest absence on that hand, but unproven; needs a second capture to separate honest-absence from a dead channel |
| 61 | **D6** | `Line of Head` | `Proximity` | `distant` | H_017 | live | CLAUDE.md S93: deferred-live -- no distant-proximity head/life hand |
| 62 | **D6** | `Line of Head` | `Proximity` | `medium` | H_016 | live | CLAUDE.md S93: deferred-live -- no medium-proximity head/life hand |
| 63 | **D6** | `Line of Head` | `joins_at_origin` | -> `Line of Heart` | L_026 | live | CLAUDE.md S115: PARKED PERMANENTLY -- triple-join never fires; the Heart line has reported no contacts on any hand tried (anatomy/perception limit) |
| 64 | **D6** | `Line of Head` | `joins_at_origin` | -> `Line of Life` | L_026 | live | CLAUDE.md S115: PARKED PERMANENTLY -- triple-join never fires; the Heart line has reported no contacts on any hand tried (anatomy/perception limit) |
| 65 | **D6** | `Line of Heart` | `Continuity` | `broken` | HL_007, HL_008, HL_009 | live | CHANNEL-SILENT: solicited YES + routed YES, yet the n=1 live capture (s117) produced no Continuity value for Line of Heart at all -- plausibly honest absence on that hand, but unproven; needs a second capture to separate honest-absence from a dead channel |
| 66 | **D6** | `Line of Heart` | `Continuity` | `chained` | HL_018 | live | CHANNEL-SILENT: solicited YES + routed YES, yet the n=1 live capture (s117) produced no Continuity value for Line of Heart at all -- plausibly honest absence on that hand, but unproven; needs a second capture to separate honest-absence from a dead channel |
| 67 | **D6** | `Line of Heart` | `Continuity` | `forked` | HL_010, HL_013 | live | CHANNEL-SILENT: solicited YES + routed YES, yet the n=1 live capture (s117) produced no Continuity value for Line of Heart at all -- plausibly honest absence on that hand, but unproven; needs a second capture to separate honest-absence from a dead channel |
| 68 | **D6** | `Line of Heart` | `joins_at_origin` | -> `Line of Life` | L_026 | live | CLAUDE.md S115: PARKED PERMANENTLY -- triple-join never fires; the Heart line has reported no contacts on any hand tried (anatomy/perception limit) |
| 69 | **D6** | `Line of Life` | `Continuity` | `chained` | L_002, L_005 | live | CHANNEL-SILENT: solicited YES + routed YES, yet the n=1 live capture (s117) produced no Continuity value for Line of Life at all -- plausibly honest absence on that hand, but unproven; needs a second capture to separate honest-absence from a dead channel |
| 70 | **D6** | `Line of Life` | `Continuity` | `islanded` | L_017, L_018 | live | CHANNEL-SILENT: solicited YES + routed YES, yet the n=1 live capture (s117) produced no Continuity value for Line of Life at all -- plausibly honest absence on that hand, but unproven; needs a second capture to separate honest-absence from a dead channel |

## 6. COMPLETENESS GUARDS

### Guard 1 -- every rule id in every file is accounted for

| file | bucket | rules |
|---|---|---|
| `palm_rules_fate_line_v1.json` | live | 16 |
| `palm_rules_fate_line_v1.json` | parked | 4 |
| `palm_rules_head_heart_v1.json` | live | 48 |
| `palm_rules_head_heart_v1.json` | parked | 1 |
| `palm_rules_head_heart_v1.json` | retired | 1 |
| `palm_rules_life_line_v1.json` | live | 11 |
| `palm_rules_life_line_v1.json` | parked | 8 |
| `palm_rules_life_line_v1.json` | retired | 3 |
| `palm_rules_mounts_v1.json` | live | 12 |
| `palm_rules_mounts_v1.json` | parked | 3 |
| `palm_rules_mounts_v1.json` | retired | 12 |
| **total** | | **119** |

- Rules **IN**: 119 (across 4 files x 3 bucket kinds; `retired_superseded` in the fate file is empty).
- Rules carrying >=1 antecedent: **104**. Rules classified **OUT** into the requirement set: **104**. **MATCH: YES**
- The remaining **15** carry ZERO antecedents and are therefore classifiable only as stubs -- all 15 are
  `parked_pending` doctrine placeholders with a `disposition` field and no `antecedents` key content:
  `FT_P01`, `FT_P02`, `FT_P03`, `FT_P04`, `L_P03`, `L_P04`, `L_P05`, `L_P06`, `L_P07`, `L_P08`, `L_P10`, `L_P11`, `M_P01`, `M_P02`, `M_P03`.
  They contribute no (feature, attribute) requirement and are excluded from every count below **by construction,**
  not by sampling. Their dispositions: do_not_author, future_branch, future_presence_signal, future_relation_target.
- Duplicate rule ids across all files: **0**.
- Antecedent instances extracted: **149** (= 104 rules x their own antecedent counts).

### Guard 2 -- every attribute in `emission_menus` is required-by-a-rule or flagged dead

`emission_menus` binds **39** (feature, attribute) menus over 9 features.

| feature | attribute | verdict | menu tokens no rule keys on |
|---|---|---|---|
| `Line of Fate` | `Break_Type` | **DEAD MENU ENTRY** | `broken`, `broken_overlapping`, `n/a` |
| `Line of Fate` | `Continuity` | REQUIRED | `unbroken`, `chained`, `forked`, `islanded` |
| `Line of Fate` | `Depth` | REQUIRED | `deep`, `shallow` |
| `Line of Fate` | `Length` | REQUIRED | `short`, `medium`, `long` |
| `Line of Fate` | `Length_Extent` | **DEAD MENU ENTRY** | `cutting_into_finger_of_Saturn`, `n/a` |
| `Line of Fate` | `ORIGIN` | **DEAD MENU ENTRY** | `Line of Life`, `Wrist`, `Mount of Luna`, `Line of Head`, `Line of Heart`, `Plain of Mars` |
| `Line of Fate` | `Proximity` | REQUIRED | `medium`, `distant` |
| `Line of Fate` | `Slope` | REQUIRED | `upward`, `downward` |
| `Line of Fate` | `Slope_Magnitude` | **DEAD MENU ENTRY** | `slight`, `very` |
| `Line of Fate` | `TERMINATION` | **DEAD MENU ENTRY** | `Mount of Saturn`, `Mount of Jupiter`, `Line of Heart`, `Line of Head` |
| `Line of Fate` | `Width` | **DEAD MENU ENTRY** | `narrow`, `broad` |
| `Line of Head` | `Continuity` | REQUIRED | `unbroken`, `forked` |
| `Line of Head` | `Depth` | REQUIRED | `deep`, `shallow` |
| `Line of Head` | `Length` | REQUIRED | `medium` |
| `Line of Head` | `ORIGIN` | **DEAD MENU ENTRY** | `Mount of Jupiter`, `Line of Life`, `Lower Mount of Mars` |
| `Line of Head` | `Proximity` | REQUIRED | *(none -- all used)* |
| `Line of Head` | `Slope` | REQUIRED | `upward`, `straight` |
| `Line of Head` | `Slope_Magnitude` | **DEAD MENU ENTRY** | `slight`, `very` |
| `Line of Head` | `TERMINATION` | **DEAD MENU ENTRY** | `Mount of Luna`, `Percussion`, `Upper Mount of Mars` |
| `Line of Head` | `Width` | **DEAD MENU ENTRY** | `narrow`, `broad` |
| `Line of Heart` | `Continuity` | REQUIRED | `unbroken`, `islanded` |
| `Line of Heart` | `Depth` | REQUIRED | `deep`, `shallow` |
| `Line of Heart` | `Length` | REQUIRED | `short`, `medium`, `long` |
| `Line of Heart` | `ORIGIN` | **DEAD MENU ENTRY** | `Mount of Jupiter`, `Junction of First and Second Fingers`, `Mount of Saturn` |
| `Line of Heart` | `Proximity` | **DEAD MENU ENTRY** | `touching`, `medium`, `distant` |
| `Line of Heart` | `Slope` | **DEAD MENU ENTRY** | `upward`, `downward`, `straight` |
| `Line of Heart` | `Slope_Magnitude` | **DEAD MENU ENTRY** | `slight`, `very` |
| `Line of Heart` | `TERMINATION` | **DEAD MENU ENTRY** | `Percussion`, `Mount of Mercury` |
| `Line of Heart` | `Width` | REQUIRED | `narrow`, `broad` |
| `Line of Life` | `Continuity` | REQUIRED | `unbroken`, `forked` |
| `Line of Life` | `Curve` | REQUIRED | `straight`, `curved` |
| `Line of Life` | `Depth` | REQUIRED | `shallow` |
| `Line of Life` | `Length` | REQUIRED | `medium` |
| `Line of Life` | `Width` | REQUIRED | `broad` |
| `Mount of Jupiter` | `Development` | REQUIRED | `not notably developed`, `cannot-tell` |
| `Mount of Saturn` | `Development` | REQUIRED | `cannot-tell` |
| `Mount of Venus` | `Development` | REQUIRED | `cannot-tell` |
| `Mount of the Sun` | `Development` | REQUIRED | `not notably developed`, `cannot-tell` |
| `Upper Mount of Mars` | `Development` | REQUIRED | `cannot-tell` |

- **DEAD (feature, attribute) menu entries: 15.** Every one is a menu authored ahead of demand, not drift:
  the 3 `ORIGIN`/`TERMINATION` pairs per line are the LANDMARK menus consumed by channel B (their
  antecedents are keyed as `Starting_Point`/`Position`, which ARE required -- so `ORIGIN`/`TERMINATION`
  are menu-side spellings of a live requirement, dead only in name); `Slope_Magnitude` x3, `Line of Fate`
  `Break_Type` / `Length_Extent`, `Line of Head`/`Line of Fate` `Width`, and `Line of Heart`
  `Slope`/`Proximity` are genuinely unclaimed. **`Break_Type` and `Length_Extent` are not dead in intent**
  -- `normalization_worklist` schedules `FT_012` and `FT_006` to be re-keyed onto exactly them (ledger
  rows 33 and 35), which converts both from dead to required.
- **Menu tokens no rule keys on: 85.** Expected and not a defect: menus are closed emission vocabularies
  (they must offer `cannot-tell`, `not notably developed`, `unbroken`, `n/a` etc. so vision can decline),
  whereas rules only key on the states that carry doctrine.

### Guard 3 -- every required attribute is either covered or in the gap ledger

- Required (feature, attribute) pairs: **48**.
- Pairs with >=1 gapped antecedent (present in the ledger): **33**.
- Pairs fully clean -- every antecedent solicited, routed, and canonically covered: **15**.
  - `Line of Fate` . `Branching`
  - `Line of Fate` . `Position`
  - `Line of Fate` . `Proximity`
  - `Line of Fate` . `Slope`
  - `Line of Fate` . `Starting_Point`
  - `Line of Head` . `Slope`
  - `Line of Heart` . `Depth`
  - `Line of Life` . `Depth`
  - `Line of Life` . `Length`
  - `Line of Life` . `Width`
  - `Mount of Jupiter` . `Development`
  - `Mount of Saturn` . `Development`
  - `Mount of Venus` . `Development`
  - `Mount of the Sun` . `Development`
  - `Upper Mount of Mars` . `Development`
- **33 + 15 = 48 = the required-pair total. No attribute is unclassified.**

At the antecedent-instance level: **149** instances total; **97** carry >=1 gap; **52** are clean.

## 7. Findings worth carrying into the downstream tasks

1. **`Position` and `Starting_Point` are DUAL-CHANNEL, and 17 live antecedents are on the wrong one (D4).**
   `extract_relations` files a LANDMARK into `targets[feature]['Starting_Point'|'Position']`, while
   `palm_rules_table._antecedent_fires` checks a VALUE literal against `observation[feature][attribute]`
   -- two different dicts. Rules that encode the landmark as a value literal
   (`rising_from_Mount_of_Saturn`, `under_Mount_of_Sun`, `terminating_on_Mount_of_Jupiter`, ...) therefore
   depend on the free-prose LLM channel emitting that exact pool token, which the n=1 live capture shows
   it never does -- the capture's `observation` carries no `Starting_Point` or `Position` key for any line,
   while its `targets` carried all six. 4 of these literals (`terminating_on_Mount`,
   `terminating_on_Mount_of_Jupiter`, `terminating_on_Mount_of_Moon`, `rising_from_Finger_of_Jupiter`) are
   not even in the flat value pool, so `to_tokens` would drop them regardless. **This is the single largest
   coherent block in the ledger and the highest-value adapter target.**

2. **4 features the rules require do not exist on the extractor's feature axis at all (D1).**
   `Hand` (H_018/H_019/H_020), `Quadrangle` (H_010a/H_010b/HL_006/HL_021), `Palm` (L_003, retired),
   `Square` (L_020/L_021, retired). `Hand`/`Type` and `Line of Heart`/`Presence` additionally name
   attributes absent from `attribute_feature_mapping` AND `relation_types`. 8 LIVE rules are affected.
   `observation_to_tokens.py`'s own module docstring point 5 already records the `Hand`/`Type` half;
   **`Quadrangle`.`Breadth` (4 live rules) and `Line of Heart`.`Presence` (1 live rule) are not recorded
   anywhere and are new findings from this pass.**

3. **`normalization_worklist` covers 14 of the 65 LIVE token-gap instances.** 10 are `D5` value
   normalizations (`well_marked`->`deep`, `thin`->`narrow`, `wide`->`broad`, `clear`->`unbroken`,
   `sloping`/`drooping`->`downward`) and 4 are `D3` attribute re-keys (`FT_006`->`Length_Extent`,
   `FT_012`->`Break_Type`, `H_004`/`H_020` `Direction`->`Slope`). It is a real head start but it is NOT the
   full worklist: **51 LIVE token-absent instances sit outside both it and `out_of_scope_untouched`.**
   Do not treat the worklist as the adapter's requirement list.

4. **`Continuity` is the one channel-silence worth a second capture.** It is solicited
   (`breaks/chains/forks/islands`) and routed on all four lines, keys 20 live antecedents, and yet the
   n=1 capture produced no `Continuity` token for any line -- the Life line's prose said
   `no breaks/chains/forks/islands visible` (a genuine negative) but Head/Heart/Fate said nothing at all.
   Honest absence and a dead channel are indistinguishable at n=1. **[2b-ii would change this]** --
   the uncommitted diff forces a closed `CONTINUITY:` menu onto all four lines, which is exactly the
   intervention that would separate the two; that is evidence for landing 2b-ii, not against it.

5. **n=1 is the evidence floor for every live-emission claim here.** All channel-level statements come
   from `diagnostics/s117_live_confirmation_raw.json`, one right hand. `emission_menus._meta` itself
   flags the same limit (n=2, both right-hand). Treat D6 rows as suggestive, never settled.

---

**TOTALS -- rules: 119 (104 with antecedents, 15 antecedent-less parked stubs) | required (feature, attribute) pairs: 48 | antecedent instances: 149 | gap units: 70 | gaps by class (antecedent instances, classes co-occur): D1=12 D2=44 D3=62 D4=19 D5=10 D6=24**
