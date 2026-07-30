# S82 Prompt 5 — OFF/ON/WIDE page-range gate comparison

`_FEATURE_PAGE_FILTER_ENABLED` is never flipped (stays `False` module-wide); ON calls `palm_reading._search_with_page_filter()` directly. OFF/ON query at production depth `_N_RESULTS_PER_FEATURE` = 3; WIDE queries unfiltered at `_WIDE_N` = 10 (diagnostic-only depth, never used by production). Book: `cheiroslanguageo00chei_1`. No relevance scoring — WIDE's in-range/out-of-range label is a mechanical page_ref comparison only. No comparison to the six JSON `_comment` chunk_ids.

## Pre-search guard

- **life line**: quality=`deep / a prominent line curves around the base of the thumb` — query=`what does a deep / a prominent line curves around the base of the thumb life line signify — meaning and indications of a deep / a prominent line curves around the base of the thumb life line` — PASSED all 3 assertions
- **head line**: quality=`deep / this line runs horizontally across the palm` — query=`what does a deep / this line runs horizontally across the palm head line signify — meaning and indications of a deep / this line runs horizontally across the palm head line` — PASSED all 3 assertions
- **heart line**: quality=`deep / the heart line is visible` — query=`what does a deep / the heart line is visible heart line signify — meaning and indications of a deep / the heart line is visible heart line` — PASSED all 3 assertions
- **fate line**: quality=`barely visible / moderately deep / there is no clearly visible fate line in the image` — query=`what does a barely visible / moderately deep / there is no clearly visible fate line in the image fate line signify — meaning and indications of a barely visible / moderately deep / there is no clearly visible fate line in the image fate line` — PASSED all 3 assertions
- **sun line**: quality resolved to None — SKIPPED, no search issued.
- **thumb**: quality=`medium relative size / medium size / the thumb is of moderate length and appears to have a wide angle of separation from the hand` — query=`what does a medium relative size / medium size / the thumb is of moderate length and appears to have a wide angle of separation from the hand thumb signify — meaning and indications of a medium relative size / medium size / the thumb is of moderate length and appears to have a wide angle of separation from the hand thumb` — PASSED all 3 assertions
- **fingers**: quality=`long relative to the palm / slightly longer than the palm / the fingers are of moderate length. the index finger is slightly shorter than the middle finger` — query=`what does a long relative to the palm / slightly longer than the palm / the fingers are of moderate length. the index finger is slightly shorter than the middle finger fingers signify — meaning and indications of a long relative to the palm / slightly longer than the palm / the fingers are of moderate length. the index finger is slightly shorter than the middle finger fingers` — PASSED all 3 assertions
- **mount of venus**: quality=`developed / the mounts of venus (base of the thumb) and jupiter (below the index finger) appear slightly raised` — query=`what does a developed / the mounts of venus (base of the thumb) and jupiter (below the index finger) appear slightly raised mount of venus signify — meaning and indications of a developed / the mounts of venus (base of the thumb) and jupiter (below the index finger) appear slightly raised mount of venus` — PASSED all 3 assertions
- **mount of jupiter**: quality=`the mounts of venus (base of the thumb) and jupiter (below the index finger) appear slightly raised` — query=`what does a the mounts of venus (base of the thumb) and jupiter (below the index finger) appear slightly raised mount of jupiter signify — meaning and indications of a the mounts of venus (base of the thumb) and jupiter (below the index finger) appear slightly raised mount of jupiter` — PASSED all 3 assertions
- **markings/other features**: quality resolved to None — SKIPPED, no search issued.

## The deciding table

| feature | verified range | OFF: n of 3 out-of-range | WIDE: ranks of in-range chunks | WIDE: n of 10 in-range | ON chunk_ids shared with OFF |
|---|---|---|---|---|---|
| life line | 133-139 | 0 | 1,2,3,4,5,6,9 | 7 of 10 | 3 |
| head line | 145-155 | 2 | 2,8 | 2 of 10 | 1 |
| heart line | 156-161 | 0 | 1,2,3,4,5,6 | 6 of 10 | 3 |
| fate line | 162-165 | 0 | 1,2,3,4,8,9 | 6 of 10 | 3 |
| sun line | 166-170 | 0 | (none) | 0 of 0 | 0 |
| thumb | 85-92 | 0 | 1,2,3,4,5,8 | 6 of 10 | 3 |
| fingers | 93-97 | 1 | 2,3,4,5,6,7,10 | 7 of 10 | 2 |
| mount of venus | 111-113 | 0 | 1,2,3,4,6,8 | 6 of 10 | 3 |
| mount of jupiter | 111-113 | 0 | 1,2,3,4,6,7 | 6 of 10 | 3 |
| markings/other features | null | n/a (null range) | (none) | 0 of 0 | 0 |

## Side-by-side per feature (all three arms)

### life line (range: 133-139)

**OFF:**

| chunk_id | page_ref | score | text (first 200 chars) |
|---|---|---|---|
| `cheiroslanguageo00chei_1_p135_c0` | 135 | 0.6131 | The Line of Life. 81  mencement (a-a, Plate XVIII), it is a very unfortunate sign, denoting that the subject, through a defect in temperament, rushes blindly into danger and catastrophe. This mark, as |
| `cheiroslanguageo00chei_1_p134_c1` | 134 | 0.6063 | The line of life should be long, narrow, and deep, without irregularities, breaks, or crosses of any kind. Such a formation promises long life, good health, and vitality.  When the line is linked (Fig |
| `cheiroslanguageo00chei_1_p134_c0` | 134 | 0.5725 | SO Cheiro’s Language of the Hand.  development or non-development of this line or that mark is the palmist able to say that a certain disease at a certain time will cause illmess with such and such a  |

**ON:**

| chunk_id | page_ref | score | text (first 200 chars) |
|---|---|---|---|
| `cheiroslanguageo00chei_1_p135_c0` | 135 | 0.6124 | The Line of Life. 81  mencement (a-a, Plate XVIII), it is a very unfortunate sign, denoting that the subject, through a defect in temperament, rushes blindly into danger and catastrophe. This mark, as |
| `cheiroslanguageo00chei_1_p134_c1` | 134 | 0.6052 | The line of life should be long, narrow, and deep, without irregularities, breaks, or crosses of any kind. Such a formation promises long life, good health, and vitality.  When the line is linked (Fig |
| `cheiroslanguageo00chei_1_p134_c0` | 134 | 0.5717 | SO Cheiro’s Language of the Hand.  development or non-development of this line or that mark is the palmist able to say that a certain disease at a certain time will cause illmess with such and such a  |

**WIDE (n=10, in-range marked by mechanical page_ref check only):**

| rank | chunk_id | page_ref | in-range? | score | text (first 200 chars) |
|---|---|---|---|---|---|
| 1 | `cheiroslanguageo00chei_1_p135_c0` | 135 | in-range | 0.6131 | The Line of Life. 81  mencement (a-a, Plate XVIII), it is a very unfortunate sign, denoting that the subject, through a defect in temperament, rushes blindly into danger and catastrophe. This mark, as |
| 2 | `cheiroslanguageo00chei_1_p134_c1` | 134 | in-range | 0.6063 | The line of life should be long, narrow, and deep, without irregularities, breaks, or crosses of any kind. Such a formation promises long life, good health, and vitality.  When the line is linked (Fig |
| 3 | `cheiroslanguageo00chei_1_p134_c0` | 134 | in-range | 0.5725 | SO Cheiro’s Language of the Hand.  development or non-development of this line or that mark is the palmist able to say that a certain disease at a certain time will cause illmess with such and such a  |
| 4 | `cheiroslanguageo00chei_1_p139_c0` | 139 | in-range | 0.5671 | The Line of Life. 85  number of these lines of influence (it being remembered that only those near the line of life are important). Numerous lines indicate a nature dependent upon affection. Such peop |
| 5 | `cheiroslanguageo00chei_1_p134_c2` | 134 | in-range | 0.5658 | When the line starts from the base of the Mount of Jupiter, instead of the side of the hand, it denotes that from the earliest the life has been one of ambition.  When the line is chained at the comme |
| 6 | `cheiroslanguageo00chei_1_p135_c2` | 135 | in-range | 0.5581 | If the line leave the line of life and ascend to the Mount of the Sun, it denotes distinction according to the class of hand.  If it leave the line of life and cross to Mercury, it promises great succ |
| 7 | `cheiroslanguageo00chei_1_p140_c1` | 140 | out-of-range | 0.5579 | When a branch shoots from this line out to the Mount of Luna (b-8, Plate XX.), it tells that there is a terrible tendeney toward intemperance of every kind, through the very robustness of the nature,  |
| 8 | `cheiroslanguageo00chei_1_p180_c1` | 180 | out-of-range | 0.5546 | When it curves or drops downward toward the line of heart, it foretells that the person with whom the subject is married will die first (7, Plate X_X.).  When the line curves upward, the possessor is  |
| 9 | `cheiroslanguageo00chei_1_p137_c1` | 137 | in-range | 0.5490 | When the line crosses the hand and touches the line of marriage (h-h, Plate XVII.), it signifies divorce, and will oceur to the person on whose hand it appears.  When this crossing-line has in itself  |
| 10 | `cheiroslanguageo00chei_1_p181_c0` | 181 | out-of-range | 0.5472 | The Line of Marriage. 117  and into the line of sun, it tells that its possessor will marry some one of dis- tinction, and generally a person in some way famous.  When, on the contrary, it goes down t |

### head line (range: 145-155)

**OFF:**

| chunk_id | page_ref | score | text (first 200 chars) |
|---|---|---|---|
| `cheiroslanguageo00chei_1_p123_c0` | 123 | 0.6090 | The Lines of the Hand. 73  The main lines are known by other names, as follows:  The Line of Life is also called the Vital.  The Line of Head, the Natural or Cerebral.  The Line of Heart, the Mensal.  |
| `cheiroslanguageo00chei_1_p151_c2` | 151 | 0.5898 | THE LINE OF HEAD IN RELATION TO THE PSYCHIC HAND.  The natural position for the line of head on this hand is extremely sloping, giving all the visionary, dreamy qualities in accordance with this type. |
| `cheiroslanguageo00chei_1_p135_c2` | 135 | 0.5866 | If the line leave the line of life and ascend to the Mount of the Sun, it denotes distinction according to the class of hand.  If it leave the line of life and cross to Mercury, it promises great succ |

**ON:**

| chunk_id | page_ref | score | text (first 200 chars) |
|---|---|---|---|
| `cheiroslanguageo00chei_1_p151_c2` | 151 | 0.5898 | THE LINE OF HEAD IN RELATION TO THE PSYCHIC HAND.  The natural position for the line of head on this hand is extremely sloping, giving all the visionary, dreamy qualities in accordance with this type. |
| `cheiroslanguageo00chei_1_p146_c2` | 146 | 0.5705 | When extremely long and straight, and going directly to the side of the hand (the percussion), it usually denotes that the subject has more than ordinary intellectual power, but is inclined to be self |
| `cheiroslanguageo00chei_1_p147_c0` | 147 | 0.5485 | The Line of Head. 89  on Mars (g-g, Plate XIX.), the subject will win unusual success in a business life; such a man will have a keen sense of the value of money—it will accunu- late rapidly in his ha |

**WIDE (n=10, in-range marked by mechanical page_ref check only):**

| rank | chunk_id | page_ref | in-range? | score | text (first 200 chars) |
|---|---|---|---|---|---|
| 1 | `cheiroslanguageo00chei_1_p123_c0` | 123 | out-of-range | 0.6090 | The Lines of the Hand. 73  The main lines are known by other names, as follows:  The Line of Life is also called the Vital.  The Line of Head, the Natural or Cerebral.  The Line of Heart, the Mensal.  |
| 2 | `cheiroslanguageo00chei_1_p151_c2` | 151 | in-range | 0.5897 | THE LINE OF HEAD IN RELATION TO THE PSYCHIC HAND.  The natural position for the line of head on this hand is extremely sloping, giving all the visionary, dreamy qualities in accordance with this type. |
| 3 | `cheiroslanguageo00chei_1_p135_c2` | 135 | out-of-range | 0.5865 | If the line leave the line of life and ascend to the Mount of the Sun, it denotes distinction according to the class of hand.  If it leave the line of life and cross to Mercury, it promises great succ |
| 4 | `cheiroslanguageo00chei_1_p124_c1` | 124 | out-of-range | 0.5802 | Lines very dark in color, almost. black, tell of a melancholy, grave tem- perament, and also indicate a haughty, distant nature, one usually very revengeful and unforgiving.  Lines may appear, diminis |
| 5 | `cheiroslanguageo00chei_1_p134_c1` | 134 | out-of-range | 0.5744 | The line of life should be long, narrow, and deep, without irregularities, breaks, or crosses of any kind. Such a formation promises long life, good health, and vitality.  When the line is linked (Fig |
| 6 | `cheiroslanguageo00chei_1_p135_c0` | 135 | out-of-range | 0.5729 | The Line of Life. 81  mencement (a-a, Plate XVIII), it is a very unfortunate sign, denoting that the subject, through a defect in temperament, rushes blindly into danger and catastrophe. This mark, as |
| 7 | `cheiroslanguageo00chei_1_p160_c2` | 160 | out-of-range | 0.5728 | When the line is quite bare of branches and thin, it tells of coldness of heart and want of affection.  When bare and thin toward the pereussion or side of the hand, it denotes sterility.  Fine lines  |
| 8 | `cheiroslanguageo00chei_1_p146_c2` | 146 | in-range | 0.5704 | When extremely long and straight, and going directly to the side of the hand (the percussion), it usually denotes that the subject has more than ordinary intellectual power, but is inclined to be self |
| 9 | `cheiroslanguageo00chei_1_p140_c1` | 140 | out-of-range | 0.5688 | When a branch shoots from this line out to the Mount of Luna (b-8, Plate XX.), it tells that there is a terrible tendeney toward intemperance of every kind, through the very robustness of the nature,  |
| 10 | `cheiroslanguageo00chei_1_p171_c1` | 171 | out-of-range | 0.5686 | The hepatica (Plate XIII.) should he straight down the hand—the straighter the better.  It is an excellent sign to be without this line. Such absence denotes an extremely robust, healthy constitution. |

### heart line (range: 156-161)

**OFF:**

| chunk_id | page_ref | score | text (first 200 chars) |
|---|---|---|---|
| `cheiroslanguageo00chei_1_p159_c3` | 159 | 0.6088 | When the line of heart is bright red, it denotes great violence of passion.  When pale and broad, the subject is blasé and indifferent.  When low down on the hand and thus close to the line of head, t |
| `cheiroslanguageo00chei_1_p160_c2` | 160 | 0.6067 | When the line is quite bare of branches and thin, it tells of coldness of heart and want of affection.  When bare and thin toward the pereussion or side of the hand, it denotes sterility.  Fine lines  |
| `cheiroslanguageo00chei_1_p161_c0` | 161 | 0.5970 | The Line of Heart. 101  ticnlarly if the hand is soft. Ona hard hand such a mark will affect the subject less—he may not be sensual, but he will never feel very deep affection.  When, however, the lin |

**ON:**

| chunk_id | page_ref | score | text (first 200 chars) |
|---|---|---|---|
| `cheiroslanguageo00chei_1_p159_c3` | 159 | 0.6088 | When the line of heart is bright red, it denotes great violence of passion.  When pale and broad, the subject is blasé and indifferent.  When low down on the hand and thus close to the line of head, t |
| `cheiroslanguageo00chei_1_p160_c2` | 160 | 0.6067 | When the line is quite bare of branches and thin, it tells of coldness of heart and want of affection.  When bare and thin toward the pereussion or side of the hand, it denotes sterility.  Fine lines  |
| `cheiroslanguageo00chei_1_p161_c0` | 161 | 0.5970 | The Line of Heart. 101  ticnlarly if the hand is soft. Ona hard hand such a mark will affect the subject less—he may not be sensual, but he will never feel very deep affection.  When, however, the lin |

**WIDE (n=10, in-range marked by mechanical page_ref check only):**

| rank | chunk_id | page_ref | in-range? | score | text (first 200 chars) |
|---|---|---|---|---|---|
| 1 | `cheiroslanguageo00chei_1_p159_c3` | 159 | in-range | 0.6088 | When the line of heart is bright red, it denotes great violence of passion.  When pale and broad, the subject is blasé and indifferent.  When low down on the hand and thus close to the line of head, t |
| 2 | `cheiroslanguageo00chei_1_p160_c2` | 160 | in-range | 0.6068 | When the line is quite bare of branches and thin, it tells of coldness of heart and want of affection.  When bare and thin toward the pereussion or side of the hand, it denotes sterility.  Fine lines  |
| 3 | `cheiroslanguageo00chei_1_p161_c0` | 161 | in-range | 0.5971 | The Line of Heart. 101  ticnlarly if the hand is soft. Ona hard hand such a mark will affect the subject less—he may not be sensual, but he will never feel very deep affection.  When, however, the lin |
| 4 | `cheiroslanguageo00chei_1_p156_c0` | 156 | in-range | 0.5776 | CHAPTER X. THE LINE OF HEART.  Keep still, my heart, Nor ask for peace, when care may suit thee best, Nor ask for love, nor joy, nor even rest, But be content to love, whate’er betide, And maybe love  |
| 5 | `cheiroslanguageo00chei_1_p159_c2` | 159 | in-range | 0.5636 | When the line of heart is itself in excess, namely, lying right across the hand from side to side, an excess of affection is the result, and a terrible tendency toward jealousy; this is still more acc |
| 6 | `cheiroslanguageo00chei_1_p160_c1` | 160 | in-range | 0.5296 | A very remarkable point is to notice whether the line of heart commence high or low on the hand. ‘The first is the best, because it shows the happiest nature.  The line lying so low that it droops dow |
| 7 | `cheiroslanguageo00chei_1_p123_c0` | 123 | out-of-range | 0.5201 | The Lines of the Hand. 73  The main lines are known by other names, as follows:  The Line of Life is also called the Vital.  The Line of Head, the Natural or Cerebral.  The Line of Heart, the Mensal.  |
| 8 | `cheiroslanguageo00chei_1_p169_c2` | 169 | out-of-range | 0.5163 | Rising from the line of heart it merely denotes a great taste for art and artistic things, and looking at it from the purely practical standpoint it denotes more distinction and influence in the world |
| 9 | `cheiroslanguageo00chei_1_p134_c1` | 134 | out-of-range | 0.5140 | The line of life should be long, narrow, and deep, without irregularities, breaks, or crosses of any kind. Such a formation promises long life, good health, and vitality.  When the line is linked (Fig |
| 10 | `cheiroslanguageo00chei_1_p139_c0` | 139 | out-of-range | 0.5086 | The Line of Life. 85  number of these lines of influence (it being remembered that only those near the line of life are important). Numerous lines indicate a nature dependent upon affection. Such peop |

### fate line (range: 162-165)

**OFF:**

| chunk_id | page_ref | score | text (first 200 chars) |
|---|---|---|---|
| `cheiroslanguageo00chei_1_p165_c1` | 165 | 0.5099 | A. double or sister fate-line is an excellent sign. It denotes two distinct eareers which the subject will follow. This ismuch more important if they go to different mounts.  A square on the hne of fa |
| `cheiroslanguageo00chei_1_p165_c0` | 165 | 0.5056 | The Line of Fate. 105  from Venus, the subject’s destiny will sway between imagination on the one hand and love and passion on the other (m-m, Plate XXT).  When broken and irregular, the career will b |
| `cheiroslanguageo00chei_1_p163_c1` | 163 | 0.4892 | The line of fate may rise from the line of hfe, the wrist, the Mount of Luna, the line of head, or even the line of heart.  If the fate-line rise from the line of life and from that poit on 18 strong, |

**ON:**

| chunk_id | page_ref | score | text (first 200 chars) |
|---|---|---|---|
| `cheiroslanguageo00chei_1_p165_c1` | 165 | 0.5099 | A. double or sister fate-line is an excellent sign. It denotes two distinct eareers which the subject will follow. This ismuch more important if they go to different mounts.  A square on the hne of fa |
| `cheiroslanguageo00chei_1_p165_c0` | 165 | 0.5056 | The Line of Fate. 105  from Venus, the subject’s destiny will sway between imagination on the one hand and love and passion on the other (m-m, Plate XXT).  When broken and irregular, the career will b |
| `cheiroslanguageo00chei_1_p163_c1` | 163 | 0.4892 | The line of fate may rise from the line of hfe, the wrist, the Mount of Luna, the line of head, or even the line of heart.  If the fate-line rise from the line of life and from that poit on 18 strong, |

**WIDE (n=10, in-range marked by mechanical page_ref check only):**

| rank | chunk_id | page_ref | in-range? | score | text (first 200 chars) |
|---|---|---|---|---|---|
| 1 | `cheiroslanguageo00chei_1_p165_c1` | 165 | in-range | 0.5099 | A. double or sister fate-line is an excellent sign. It denotes two distinct eareers which the subject will follow. This ismuch more important if they go to different mounts.  A square on the hne of fa |
| 2 | `cheiroslanguageo00chei_1_p165_c0` | 165 | in-range | 0.5056 | The Line of Fate. 105  from Venus, the subject’s destiny will sway between imagination on the one hand and love and passion on the other (m-m, Plate XXT).  When broken and irregular, the career will b |
| 3 | `cheiroslanguageo00chei_1_p163_c1` | 163 | in-range | 0.4892 | The line of fate may rise from the line of hfe, the wrist, the Mount of Luna, the line of head, or even the line of heart.  If the fate-line rise from the line of life and from that poit on 18 strong, |
| 4 | `cheiroslanguageo00chei_1_p163_c0` | 163 | in-range | 0.4890 | The Line of Fate. 103  square. I wish to emphasize this as so many students throw up palimistry in despair through not having this point explained at the start.  The strange and mysterious thing to no |
| 5 | `cheiroslanguageo00chei_1_p127_c1` | 127 | out-of-range | 0.4872 | I make no comment on this strange story; I simply relate the facts as they occurred.  The above is only one example in many that could be cited to show that we rarely if ever will go by warnings, no m |
| 6 | `cheiroslanguageo00chei_1_p136_c3` | 136 | out-of-range | 0.4761 | When they cut the line of life only (6-0. Plate NVIL.). they denote the interference of relatives—generally in the home life.  When they cross the life-line and attack the line of fate (e-e, Plate AVI |
| 7 | `cheiroslanguageo00chei_1_p160_c2` | 160 | out-of-range | 0.4747 | When the line is quite bare of branches and thin, it tells of coldness of heart and want of affection.  When bare and thin toward the pereussion or side of the hand, it denotes sterility.  Fine lines  |
| 8 | `cheiroslanguageo00chei_1_p162_c0` | 162 | in-range | 0.4691 | CHAPTER XI. THE LINE OF FATE.  And what is fate?  A perfect law that shapes all things for good; And thus, that men may have a just reward For doing what is right, not caring should No earthly crown b |
| 9 | `cheiroslanguageo00chei_1_p163_c2` | 163 | in-range | 0.4649 | Rising from the Mount of Luna, fate and success will be more or less dependent on the fancy and eaprice of other people. This 1s very often found in the case of public favorites.  Tf the line of fate  |
| 10 | `cheiroslanguageo00chei_1_p208_c1` | 208 | out-of-range | 0.4641 | When they enter the line of fate and ascend with it, they denote travels that will materially benefit the subject.  When the end of any of these horizontal lines droop or curve downward toward the wri |

### sun line (range: 166-170)

**OFF:**

(no results)

**ON:**

(no results)

**WIDE (n=10, in-range marked by mechanical page_ref check only):**

(no results)

### thumb (range: 85-92)

**OFF:**

| chunk_id | page_ref | score | text (first 200 chars) |
|---|---|---|---|
| `cheiroslanguageo00chei_1_p87_c0` | 87 | 0.5199 | The Thumb. 47  reason goes, the thumb loses all power and drops in on the hand, but that if the reason has only faded temporarily the thumb still retains its power and there is every hope of life. It  |
| `cheiroslanguageo00chei_1_p88_c1` | 88 | 0.5160 | When the second phalange is much longer than the first, the subject, though having all the calmness and exactitude of reason, vet has not sufficient will and determination to carry out Ins ideas.  Whe |
| `cheiroslanguageo00chei_1_p89_c2` | 89 | 0.5075 | THE SECOND PHALANGE.  The next important characteristic of the thumb is the shape and make of the second or middle phalange. It will be found that this varies greatly and is a decided indicator of tem |

**ON:**

| chunk_id | page_ref | score | text (first 200 chars) |
|---|---|---|---|
| `cheiroslanguageo00chei_1_p87_c0` | 87 | 0.5199 | The Thumb. 47  reason goes, the thumb loses all power and drops in on the hand, but that if the reason has only faded temporarily the thumb still retains its power and there is every hope of life. It  |
| `cheiroslanguageo00chei_1_p88_c1` | 88 | 0.5160 | When the second phalange is much longer than the first, the subject, though having all the calmness and exactitude of reason, vet has not sufficient will and determination to carry out Ins ideas.  Whe |
| `cheiroslanguageo00chei_1_p89_c2` | 89 | 0.5075 | THE SECOND PHALANGE.  The next important characteristic of the thumb is the shape and make of the second or middle phalange. It will be found that this varies greatly and is a decided indicator of tem |

**WIDE (n=10, in-range marked by mechanical page_ref check only):**

| rank | chunk_id | page_ref | in-range? | score | text (first 200 chars) |
|---|---|---|---|---|---|
| 1 | `cheiroslanguageo00chei_1_p87_c0` | 87 | in-range | 0.5199 | The Thumb. 47  reason goes, the thumb loses all power and drops in on the hand, but that if the reason has only faded temporarily the thumb still retains its power and there is every hope of life. It  |
| 2 | `cheiroslanguageo00chei_1_p88_c1` | 88 | in-range | 0.5160 | When the second phalange is much longer than the first, the subject, though having all the calmness and exactitude of reason, vet has not sufficient will and determination to carry out Ins ideas.  Whe |
| 3 | `cheiroslanguageo00chei_1_p89_c2` | 89 | in-range | 0.5075 | THE SECOND PHALANGE.  The next important characteristic of the thumb is the shape and make of the second or middle phalange. It will be found that this varies greatly and is a decided indicator of tem |
| 4 | `cheiroslanguageo00chei_1_p88_c0` | 88 | in-range | 0.5039 | 45 Cheiro’s Language of the Hand.  formed thumb denotes strength of intellectual will; the short, thick thumb, brute foree and obstinacy ; the small, weak thumb, weakness of will and want of energy.   |
| 5 | `cheiroslanguageo00chei_1_p89_c0` | 89 | in-range | 0.4775 | The Thumb. 49  THE SUPPLE-JOINTED THUMB.  For example, the supple-jointed thumb, bending from the hand, is the in- dication of the extravagant person, not only in matters of monev, but in thought ; th |
| 6 | `cheiroslanguageo00chei_1_p97_c0` | 97 | out-of-range | 0.4474 | The Fingers. Dd  of balance in the hand to the thumb, and indicates the power of the subject to influence others. When very long—almost reaching to the nail of the third— it shows great power of expre |
| 7 | `cheiroslanguageo00chei_1_p96_c2` | 96 | out-of-range | 0.4448 | When pointed, the reverse—callousness and frivolity.  When the third finger (the finger of the Sun) is nearly of the same length as the first, it denotes ambition for wealth and honor through its arti |
| 8 | `cheiroslanguageo00chei_1_p86_c0` | 86 | in-range | 0.4433 | 46 Cheiro’s Language of the Hand.  Trinity; the ordinary priest has to use the whole hand. And, again, in the old ritual of the English church, we find that in baptism the cross must be made by the th |
| 9 | `cheiroslanguageo00chei_1_p96_c0` | 96 | out-of-range | 0.4416 | ot Cheivo’s Language of the Hand.  his own comfort before that of others; he will desire luxury in eating, drink- ing, and living. When, on the contrary, the fingers at the base are shaped like a wais |
| 10 | `cheiroslanguageo00chei_1_p99_c0` | 99 | out-of-range | 0.4399 | The Palm, and Large and Small Hands.  en =)  LARGE AND SMALL HANDS.  It is a thing well worth remarking, that, generally speaking, people with large hands do very fine work and love great detail in wo |

### fingers (range: 93-97)

**OFF:**

| chunk_id | page_ref | score | text (first 200 chars) |
|---|---|---|---|
| `cheiroslanguageo00chei_1_p98_c1` | 98 | 0.5885 | If it inclines to the line of life, it promises disappointment and trouble in domestic affairs, and if the rest of the hand denotes ill-health, it is an added sign of delicacy and trouble.  When the h |
| `cheiroslanguageo00chei_1_p96_c1` | 96 | 0.5284 | When the first, or index finger, is excessively long, it denotes great pride, and a tendeney to rule and domineer. It is to be found in the hands of priests as well as politicians. Such a man, literal |
| `cheiroslanguageo00chei_1_p96_c0` | 96 | 0.5282 | ot Cheivo’s Language of the Hand.  his own comfort before that of others; he will desire luxury in eating, drink- ing, and living. When, on the contrary, the fingers at the base are shaped like a wais |

**ON:**

| chunk_id | page_ref | score | text (first 200 chars) |
|---|---|---|---|
| `cheiroslanguageo00chei_1_p96_c1` | 96 | 0.5284 | When the first, or index finger, is excessively long, it denotes great pride, and a tendeney to rule and domineer. It is to be found in the hands of priests as well as politicians. Such a man, literal |
| `cheiroslanguageo00chei_1_p96_c0` | 96 | 0.5282 | ot Cheivo’s Language of the Hand.  his own comfort before that of others; he will desire luxury in eating, drink- ing, and living. When, on the contrary, the fingers at the base are shaped like a wais |
| `cheiroslanguageo00chei_1_p95_c0` | 95 | 0.5267 | CHAPTER XI. THE FINGERS.  Frncers are either long or short, irrespective of the length of the palm to which they belong.  Long fingers give love of detail in everything—in the decoration of a room, in |

**WIDE (n=10, in-range marked by mechanical page_ref check only):**

| rank | chunk_id | page_ref | in-range? | score | text (first 200 chars) |
|---|---|---|---|---|---|
| 1 | `cheiroslanguageo00chei_1_p98_c1` | 98 | out-of-range | 0.5886 | If it inclines to the line of life, it promises disappointment and trouble in domestic affairs, and if the rest of the hand denotes ill-health, it is an added sign of delicacy and trouble.  When the h |
| 2 | `cheiroslanguageo00chei_1_p96_c1` | 96 | in-range | 0.5284 | When the first, or index finger, is excessively long, it denotes great pride, and a tendeney to rule and domineer. It is to be found in the hands of priests as well as politicians. Such a man, literal |
| 3 | `cheiroslanguageo00chei_1_p96_c0` | 96 | in-range | 0.5282 | ot Cheivo’s Language of the Hand.  his own comfort before that of others; he will desire luxury in eating, drink- ing, and living. When, on the contrary, the fingers at the base are shaped like a wais |
| 4 | `cheiroslanguageo00chei_1_p95_c0` | 95 | in-range | 0.5267 | CHAPTER XI. THE FINGERS.  Frncers are either long or short, irrespective of the length of the palm to which they belong.  Long fingers give love of detail in everything—in the decoration of a room, in |
| 5 | `cheiroslanguageo00chei_1_p96_c2` | 96 | in-range | 0.5104 | When pointed, the reverse—callousness and frivolity.  When the third finger (the finger of the Sun) is nearly of the same length as the first, it denotes ambition for wealth and honor through its arti |
| 6 | `cheiroslanguageo00chei_1_p96_c3` | 96 | in-range | 0.5016 | When the fourth, or little finger, is well-shaped and long, it acts as a kind |
| 7 | `cheiroslanguageo00chei_1_p97_c0` | 97 | in-range | 0.4950 | The Fingers. Dd  of balance in the hand to the thumb, and indicates the power of the subject to influence others. When very long—almost reaching to the nail of the third— it shows great power of expre |
| 8 | `cheiroslanguageo00chei_1_p98_c0` | 98 | out-of-range | 0.4945 | CHAPTER NIL THE PALM, AND LARGE AND SMALL HANDS.  A rut, hard, dry palm indicates timidity, and a nervous, worrying, troubled nature.  A very thick palm, full and soft, shows sensuality of disposition |
| 9 | `cheiroslanguageo00chei_1_p99_c0` | 99 | out-of-range | 0.4850 | The Palm, and Large and Small Hands.  en =)  LARGE AND SMALL HANDS.  It is a thing well worth remarking, that, generally speaking, people with large hands do very fine work and love great detail in wo |
| 10 | `cheiroslanguageo00chei_1_p95_c1` | 95 | in-range | 0.4797 | Fingers thick and clumsy, as well as short, are more or less cruel and selfish.  When the fingers are stiff and curved inward, or naturally contracted, they denote an excess of caution and reserve, an |

### mount of venus (range: 111-113)

**OFF:**

| chunk_id | page_ref | score | text (first 200 chars) |
|---|---|---|---|
| `cheiroslanguageo00chei_1_p112_c0` | 112 | 0.6824 | 64 Cheiro’s Language of the Hand.  Venus be well developed, it indicates strong and robust health. A small Mount of Venus betrays poor health and, consequently, less passion.  The Mount of Venus, abno |
| `cheiroslanguageo00chei_1_p111_c1` | 111 | 0.6698 | THE MOUNT OF VENUS.  The Mount of Venus is the develoyeout found at the base of the thu ~b (Plate XII.). Wher not abnorinally iavee it is a favorable sign en the hand  of man or woman./ This mouut cov |
| `cheiroslanguageo00chei_1_p111_c0` | 111 | 0.5591 | CHAPTER XY. THE MOUNTS, THEIR POSITION AND THEIR MEANINGS.  Ix my work I abways class the mounts of the hand (Plate XIJ.) with the hand itself, and therefore I treat of them in the section of this wor |

**ON:**

| chunk_id | page_ref | score | text (first 200 chars) |
|---|---|---|---|
| `cheiroslanguageo00chei_1_p112_c0` | 112 | 0.6824 | 64 Cheiro’s Language of the Hand.  Venus be well developed, it indicates strong and robust health. A small Mount of Venus betrays poor health and, consequently, less passion.  The Mount of Venus, abno |
| `cheiroslanguageo00chei_1_p111_c1` | 111 | 0.6698 | THE MOUNT OF VENUS.  The Mount of Venus is the develoyeout found at the base of the thu ~b (Plate XII.). Wher not abnorinally iavee it is a favorable sign en the hand  of man or woman./ This mouut cov |
| `cheiroslanguageo00chei_1_p111_c0` | 111 | 0.5591 | CHAPTER XY. THE MOUNTS, THEIR POSITION AND THEIR MEANINGS.  Ix my work I abways class the mounts of the hand (Plate XIJ.) with the hand itself, and therefore I treat of them in the section of this wor |

**WIDE (n=10, in-range marked by mechanical page_ref check only):**

| rank | chunk_id | page_ref | in-range? | score | text (first 200 chars) |
|---|---|---|---|---|---|
| 1 | `cheiroslanguageo00chei_1_p112_c0` | 112 | in-range | 0.6824 | 64 Cheiro’s Language of the Hand.  Venus be well developed, it indicates strong and robust health. A small Mount of Venus betrays poor health and, consequently, less passion.  The Mount of Venus, abno |
| 2 | `cheiroslanguageo00chei_1_p111_c1` | 111 | in-range | 0.6698 | THE MOUNT OF VENUS.  The Mount of Venus is the develoyeout found at the base of the thu ~b (Plate XII.). Wher not abnorinally iavee it is a favorable sign en the hand  of man or woman./ This mouut cov |
| 3 | `cheiroslanguageo00chei_1_p111_c0` | 111 | in-range | 0.5591 | CHAPTER XY. THE MOUNTS, THEIR POSITION AND THEIR MEANINGS.  Ix my work I abways class the mounts of the hand (Plate XIJ.) with the hand itself, and therefore I treat of them in the section of this wor |
| 4 | `cheiroslanguageo00chei_1_p113_c0` | 113 | in-range | 0.5501 | Lhe Mounts, their Position and their Meanings. 69  THE MOUNT OF MARS.  There are two mounts of this name; the first beneath the Mount of Jupiter, but inside the line of iife, lying next to the Mount o |
| 5 | `cheiroslanguageo00chei_1_p189_c1` | 189 | out-of-range | 0.5406 | THE STAR ON THE MOUNT OF VENUS.  In the center or highest point of the Mount of Venus (J, Plate XVIIL) the star is once more successful and favorable, but this timein relation to the affections and pa |
| 6 | `cheiroslanguageo00chei_1_p112_c1` | 112 | in-range | 0.5381 | THE MOUNT OF SATURN.  This is found at the base of the second finger (Plate XII.), and denotes love of solitude, quietness, prudence, earnestness in work, proneness to the study of somber things, and  |
| 7 | `cheiroslanguageo00chei_1_p187_c1` | 187 | out-of-range | 0.5347 | With a strong fate, head, and sun line, there is almost no step in the ladder of human greatness that the subject will not reach. Itis usually found on the hand of avery ambitious man or woman, and in |
| 8 | `cheiroslanguageo00chei_1_p112_c2` | 112 | in-range | 0.5113 | THE MOUNT OF MERCURY.  The mount of this name is found at the base of the fourth finger (Plate » 1"). {t denotes all the mercurial qualities of life—love of change, travel, excitement, wit, quickness  |
| 9 | `cheiroslanguageo00chei_1_p183_c1` | 183 | out-of-range | 0.4834 | Owing to the accuracy with which I have been credited on this point, I have been largely requested, in writing this book, to give as many details as permissible. I shall endeavor to do so in as clear  |
| 10 | `cheiroslanguageo00chei_1_p156_c2` | 156 | out-of-range | 0.4728 | Next we will consider the line rising from the Mount of Jupiter, even from the finger itself (e-e, Plate XX.). This denotes the excess of all the fore- going qualities; it gives the blind enthusiast,  |

### mount of jupiter (range: 111-113)

**OFF:**

| chunk_id | page_ref | score | text (first 200 chars) |
|---|---|---|---|
| `cheiroslanguageo00chei_1_p112_c0` | 112 | 0.6630 | 64 Cheiro’s Language of the Hand.  Venus be well developed, it indicates strong and robust health. A small Mount of Venus betrays poor health and, consequently, less passion.  The Mount of Venus, abno |
| `cheiroslanguageo00chei_1_p111_c1` | 111 | 0.6456 | THE MOUNT OF VENUS.  The Mount of Venus is the develoyeout found at the base of the thu ~b (Plate XII.). Wher not abnorinally iavee it is a favorable sign en the hand  of man or woman./ This mouut cov |
| `cheiroslanguageo00chei_1_p113_c0` | 113 | 0.5893 | Lhe Mounts, their Position and their Meanings. 69  THE MOUNT OF MARS.  There are two mounts of this name; the first beneath the Mount of Jupiter, but inside the line of iife, lying next to the Mount o |

**ON:**

| chunk_id | page_ref | score | text (first 200 chars) |
|---|---|---|---|
| `cheiroslanguageo00chei_1_p112_c0` | 112 | 0.6630 | 64 Cheiro’s Language of the Hand.  Venus be well developed, it indicates strong and robust health. A small Mount of Venus betrays poor health and, consequently, less passion.  The Mount of Venus, abno |
| `cheiroslanguageo00chei_1_p111_c1` | 111 | 0.6456 | THE MOUNT OF VENUS.  The Mount of Venus is the develoyeout found at the base of the thu ~b (Plate XII.). Wher not abnorinally iavee it is a favorable sign en the hand  of man or woman./ This mouut cov |
| `cheiroslanguageo00chei_1_p113_c0` | 113 | 0.5893 | Lhe Mounts, their Position and their Meanings. 69  THE MOUNT OF MARS.  There are two mounts of this name; the first beneath the Mount of Jupiter, but inside the line of iife, lying next to the Mount o |

**WIDE (n=10, in-range marked by mechanical page_ref check only):**

| rank | chunk_id | page_ref | in-range? | score | text (first 200 chars) |
|---|---|---|---|---|---|
| 1 | `cheiroslanguageo00chei_1_p112_c0` | 112 | in-range | 0.6630 | 64 Cheiro’s Language of the Hand.  Venus be well developed, it indicates strong and robust health. A small Mount of Venus betrays poor health and, consequently, less passion.  The Mount of Venus, abno |
| 2 | `cheiroslanguageo00chei_1_p111_c1` | 111 | in-range | 0.6456 | THE MOUNT OF VENUS.  The Mount of Venus is the develoyeout found at the base of the thu ~b (Plate XII.). Wher not abnorinally iavee it is a favorable sign en the hand  of man or woman./ This mouut cov |
| 3 | `cheiroslanguageo00chei_1_p113_c0` | 113 | in-range | 0.5893 | Lhe Mounts, their Position and their Meanings. 69  THE MOUNT OF MARS.  There are two mounts of this name; the first beneath the Mount of Jupiter, but inside the line of iife, lying next to the Mount o |
| 4 | `cheiroslanguageo00chei_1_p111_c0` | 111 | in-range | 0.5636 | CHAPTER XY. THE MOUNTS, THEIR POSITION AND THEIR MEANINGS.  Ix my work I abways class the mounts of the hand (Plate XIJ.) with the hand itself, and therefore I treat of them in the section of this wor |
| 5 | `cheiroslanguageo00chei_1_p189_c1` | 189 | out-of-range | 0.5546 | THE STAR ON THE MOUNT OF VENUS.  In the center or highest point of the Mount of Venus (J, Plate XVIIL) the star is once more successful and favorable, but this timein relation to the affections and pa |
| 6 | `cheiroslanguageo00chei_1_p112_c1` | 112 | in-range | 0.5526 | THE MOUNT OF SATURN.  This is found at the base of the second finger (Plate XII.), and denotes love of solitude, quietness, prudence, earnestness in work, proneness to the study of somber things, and  |
| 7 | `cheiroslanguageo00chei_1_p112_c2` | 112 | in-range | 0.5490 | THE MOUNT OF MERCURY.  The mount of this name is found at the base of the fourth finger (Plate » 1"). {t denotes all the mercurial qualities of life—love of change, travel, excitement, wit, quickness  |
| 8 | `cheiroslanguageo00chei_1_p187_c1` | 187 | out-of-range | 0.5469 | With a strong fate, head, and sun line, there is almost no step in the ladder of human greatness that the subject will not reach. Itis usually found on the hand of avery ambitious man or woman, and in |
| 9 | `cheiroslanguageo00chei_1_p199_c1` | 199 | out-of-range | 0.4981 | On the Mount of Mercury it denotes an unstable and rather unprincipled person.  On the Mount of Luna it foretells restlessness, discontent, and dis- qnietude.  On the Mount of Venus, caprice 11 passio |
| 10 | `cheiroslanguageo00chei_1_p187_c0` | 187 | out-of-range | 0.4952 | CHAPTER XVIIL THE STAR.  THE star is a sign of very great importance, wherever it makes 18 appear- ance on the hand. Ido not at all hold that it is generally a danger, and one from which there is no e |

### markings/other features (range: null)

**OFF:**

(no results)

**ON:**

(no results)

**WIDE (n=10, in-range marked by mechanical page_ref check only):**

(no results)

## markings/other features — null-range identity check

- OFF chunk_ids (order-sensitive): []
- ON chunk_ids (order-sensitive): []
- WIDE result count: 0 (all count as in-range by definition, null range)
- **IDENTICAL — correct: null range means ON and OFF are the same call.**

## Embedding calls made

Total: **24**

## Failures

- OFF arm failures: **0**
- ON arm failures: **0**
- WIDE arm failures: **0**
- Total: **0**