# S67 R1 probe — per-feature retrieval template fingerprint

Measure-first probe for the S67 R1 per-feature retrieval redesign. Confirmed descriptions transplanted verbatim from `diagnostics/ring3_palm_rubric_S66_pass2.md` (cited, not retyped). Query construction and feature extraction are deterministic regex over the LEFT/RIGHT labeled fields, no LLM. Retrieval via `ingestion.query_engine.search`, `book_name="cheiroslanguageo00chei_1"`, `n_results=5` — same call signature `palm_reading.py` uses.

**Scope note**: this script reports retrieval only. Whether a retrieved chunk is genuine interpretive *doctrine* vs. nomenclature/procedural text is NOT classified here — that judgment is a design-chat human call. Section 4 below reports only literal presence of the two known-doctrine pages (p.134 life-line, p.163 fate-line, per `ring3_chunks_S66_pass2.md`) in each result set.

## 1. Query strings per feature × variant

| Feature | Observed? | (i) RAW | (ii) LABEL+QUALITY | (iii) DOCTRINE-INTERROGATIVE |
|---|---|---|---|---|
| life line | yes | Present, deep, long, curves around the base of the thumb, no clear breaks or forks.; Present, deep, long, curves around the base of the thumb, no clear breaks or forks. | deep life line | what does a deep life line signify — meaning and indications of a deep life line |
| head line | yes | Present, deep, long, slightly curved, runs across the palm, no clear breaks or forks.; Present, deep, long, slightly curved, runs across the palm, no clear breaks or forks. | deep head line | what does a deep head line signify — meaning and indications of a deep head line |
| heart line | yes | Present, deep, long, slightly curved, ends below the index finger, no clear breaks or forks.; Present, deep, slightly curved, ends below the index finger, no clear breaks or forks. | deep heart line | what does a deep heart line signify — meaning and indications of a deep heart line |
| fate line | yes | Barely visible.; Present, moderately deep, runs from the base of the palm towards the middle finger, no clear breaks or forks. | barely visible / moderately deep fate line | what does a barely visible / moderately deep fate line signify — meaning and indications of a barely visible / moderately deep fate line |
| sun line | yes | Not clearly visible.; Sun line is faintly visible. | faintly visible sun line | what does a faintly visible sun line signify — meaning and indications of a faintly visible sun line |
| thumb | yes | Medium relative size, set moderately low, wide angle from the palm.; Medium size, set moderately low, wide angle from the palm. | medium relative size / medium size thumb | what does a medium relative size / medium size thumb signify — meaning and indications of a medium relative size / medium size thumb |
| fingers | yes | Fingers are long relative to the palm, appear straight, with rounded fingertips, moderate spacing.; Fingers are slightly longer than the palm, appear straight, with rounded fingertips, spaced moderately apart. | long relative to the palm / slightly longer than the palm fingers | what does a long relative to the palm / slightly longer than the palm fingers signify — meaning and indications of a long relative to the palm / slightly longer than the palm fingers |
| mount of venus | yes | Mount of Venus appears developed, other mounts are unremarkable.; Mount of Venus appears developed, other mounts are unremarkable. | developed mount of venus | what does a developed mount of venus signify — meaning and indications of a developed mount of venus |
| mount of jupiter | NOT OBSERVED | _(skipped — not observed)_ | _(skipped — not observed)_ | what does a faint mount of jupiter signify — meaning and indications of a faint mount of jupiter |
| markings/other features | yes | No clear marks visible.; No clear marks visible. | no clear marks visible markings | what does a no clear marks visible markings signify — meaning and indications of a no clear marks visible markings |

Negative control query: `steam engine boiler maintenance`

## 2. Per-query retrieval results

### life line — variant (i) RAW
Query: `Present, deep, long, curves around the base of the thumb, no clear breaks or forks.; Present, deep, long, curves around the base of the thumb, no clear breaks or forks.`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 88 | 0.5437 | When the second phalange is much longer than the first, the subject, though having all the calmness and exactitude of re |
| 2 | 89 | 0.5167 | The Thumb. 49 THE SUPPLE-JOINTED THUMB. For example, the supple-jointed thumb, bending from the hand, is the in- dicatio |
| 3 | 87 | 0.5024 | The Thumb. 47 reason goes, the thumb loses all power and drops in on the hand, but that if the reason has only faded tem |
| 4 | 89 | 0.4982 | THE SECOND PHALANGE. The next important characteristic of the thumb is the shape and make of the second or middle phalan |
| 5 | 95 | 0.4949 | When the fingers are thick and pnffy at the base, the subject considers 53 |

### life line — variant (ii) LABEL+QUALITY
Query: `deep life line`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 139 | 0.5254 | The Line of Life. 85 number of these lines of influence (it being remembered that only those near the line of life are i |
| 2 | 134 | 0.4850 | The line of life should be long, narrow, and deep, without irregularities, breaks, or crosses of any kind. Such a format |
| 3 | 139 | 0.4810 | When, on the contrary, it lies very close to the Mount of Venus, health is not so robust or the body physically so well  |
| 4 | 136 | 0.4682 | When they cut the line of life only (6-0. Plate NVIL.). they denote the interference of relatives—generally in the home  |
| 5 | 137 | 0.4676 | The Line of Life. 63 When they reach the lne of head (#-f, Plate XVI.), they indicate persons who will influence our tho |

### life line — variant (iii) DOCTRINE-INTERROGATIVE
Query: `what does a deep life line signify — meaning and indications of a deep life line`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 139 | 0.6108 | The Line of Life. 85 number of these lines of influence (it being remembered that only those near the line of life are i |
| 2 | 134 | 0.5801 | When the line starts from the base of the Mount of Jupiter, instead of the side of the hand, it denotes that from the ea |
| 3 | 134 | 0.5775 | The line of life should be long, narrow, and deep, without irregularities, breaks, or crosses of any kind. Such a format |
| 4 | 135 | 0.5652 | The Line of Life. 81 mencement (a-a, Plate XVIII), it is a very unfortunate sign, denoting that the subject, through a d |
| 5 | 139 | 0.5552 | When, on the contrary, it lies very close to the Mount of Venus, health is not so robust or the body physically so well  |

### head line — variant (i) RAW
Query: `Present, deep, long, slightly curved, runs across the palm, no clear breaks or forks.; Present, deep, long, slightly curved, runs across the palm, no clear breaks or forks.`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 98 | 0.5418 | CHAPTER NIL THE PALM, AND LARGE AND SMALL HANDS. A rut, hard, dry palm indicates timidity, and a nervous, worrying, trou |
| 2 | 146 | 0.4975 | When extremely long and straight, and going directly to the side of the hand (the percussion), it usually denotes that t |
| 3 | 202 | 0.4849 | SMOOTH HANDS. Very smooth hands with few lines belong to people calm in temperament and even in disposition. They seldom |
| 4 | 98 | 0.4787 | If it inclines to the line of life, it promises disappointment and trouble in domestic affairs, and if the rest of the h |
| 5 | 225 | 0.4748 | On all iniportant points, such as Ulness, death, loss of fortune, marriage, and so forth, see what the left promises bef |

### head line — variant (ii) LABEL+QUALITY
Query: `deep head line`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 145 | 0.5057 | CHAPTER VII. THE LINE OF HEAD. “To know is power “—let us then be wise, And use our brains with every good intent, That  |
| 2 | 151 | 0.5052 | THE LINE OF HEAD IN RELATION TO THE PSYCHIC HAND. The natural position for the line of head on this hand is extremely sl |
| 3 | 150 | 0.4810 | THE LINE OF HEAD IN RELATION TO THE PHILOSOPHIC HAND. The philosophic hand (Part L, Chapter V.) is thoughtful, earnest i |
| 4 | 150 | 0.4749 | THE LINE OF HEAD IN RELATION TO THE SPATULATE HAND. The spatulate hand (Part 1., Chapter IV.) is the hand of action, inv |
| 5 | 151 | 0.4560 | THE LINE OF HEAD IN REFERENCE TO THE CONIC HAND. The conic hand (Part 1., Chapter VI.) belongs to the artistic, impulsiv |

### head line — variant (iii) DOCTRINE-INTERROGATIVE
Query: `what does a deep head line signify — meaning and indications of a deep head line`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 145 | 0.5588 | CHAPTER VII. THE LINE OF HEAD. “To know is power “—let us then be wise, And use our brains with every good intent, That  |
| 2 | 147 | 0.5260 | When abnormally short, it foreshadows some early death from some mental affection. When broken in two under the Mount of |
| 3 | 151 | 0.5226 | THE LINE OF HEAD IN RELATION TO THE PSYCHIC HAND. The natural position for the line of head on this hand is extremely sl |
| 4 | 160 | 0.5184 | When the line is quite bare of branches and thin, it tells of coldness of heart and want of affection. When bare and thi |
| 5 | 159 | 0.5083 | When the line of heart is bright red, it denotes great violence of passion. When pale and broad, the subject is blasé an |

### heart line — variant (i) RAW
Query: `Present, deep, long, slightly curved, ends below the index finger, no clear breaks or forks.; Present, deep, slightly curved, ends below the index finger, no clear breaks or forks.`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 95 | 0.5018 | Fingers thick and clumsy, as well as short, are more or less cruel and selfish. When the fingers are stiff and curved in |
| 2 | 96 | 0.4860 | When the fourth, or little finger, is well-shaped and long, it acts as a kind |
| 3 | 95 | 0.4837 | When the fingers are thick and pnffy at the base, the subject considers 53 |
| 4 | 146 | 0.4591 | When extremely long and straight, and going directly to the side of the hand (the percussion), it usually denotes that t |
| 5 | 65 | 0.4566 | With these hands, therefore, it must be borne im mind that the developed joints are the peculiar characteristic of thoug |

### heart line — variant (ii) LABEL+QUALITY
Query: `deep heart line`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 161 | 0.6437 | The Line of Heart. 101 ticnlarly if the hand is soft. Ona hard hand such a mark will affect the subject less—he may not  |
| 2 | 156 | 0.6389 | CHAPTER X. THE LINE OF HEART. Keep still, my heart, Nor ask for peace, when care may suit thee best, Nor ask for love, n |
| 3 | 159 | 0.6261 | When the line of heart is itself in excess, namely, lying right across the hand from side to side, an excess of affectio |
| 4 | 160 | 0.6180 | When the line is quite bare of branches and thin, it tells of coldness of heart and want of affection. When bare and thi |
| 5 | 159 | 0.5621 | When the line of heart is bright red, it denotes great violence of passion. When pale and broad, the subject is blasé an |

### heart line — variant (iii) DOCTRINE-INTERROGATIVE
Query: `what does a deep heart line signify — meaning and indications of a deep heart line`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 160 | 0.6427 | When the line is quite bare of branches and thin, it tells of coldness of heart and want of affection. When bare and thi |
| 2 | 161 | 0.6188 | The Line of Heart. 101 ticnlarly if the hand is soft. Ona hard hand such a mark will affect the subject less—he may not  |
| 3 | 159 | 0.6061 | When the line of heart is itself in excess, namely, lying right across the hand from side to side, an excess of affectio |
| 4 | 159 | 0.6054 | When the line of heart is bright red, it denotes great violence of passion. When pale and broad, the subject is blasé an |
| 5 | 156 | 0.5884 | CHAPTER X. THE LINE OF HEART. Keep still, my heart, Nor ask for peace, when care may suit thee best, Nor ask for love, n |

### fate line — variant (i) RAW
Query: `Barely visible.; Present, moderately deep, runs from the base of the palm towards the middle finger, no clear breaks or forks.`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 95 | 0.4806 | When the fingers are thick and pnffy at the base, the subject considers 53 |
| 2 | 98 | 0.4714 | CHAPTER NIL THE PALM, AND LARGE AND SMALL HANDS. A rut, hard, dry palm indicates timidity, and a nervous, worrying, trou |
| 3 | 225 | 0.4443 | On all iniportant points, such as Ulness, death, loss of fortune, marriage, and so forth, see what the left promises bef |
| 4 | 221 | 0.4440 | It is the hand of the subtlest nature in regard to crime. There will be nothing abnormal in connection with the hand its |
| 5 | 134 | 0.4356 | The line of life should be long, narrow, and deep, without irregularities, breaks, or crosses of any kind. Such a format |

### fate line — variant (ii) LABEL+QUALITY
Query: `barely visible / moderately deep fate line`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 179 | 0.5221 | A wealthy union is shown by a strong, well-marked line from the side of the line of fate next Luna (h-h, Plate XX.), run |
| 2 | 163 | 0.5164 | The line of fate may rise from the line of hfe, the wrist, the Mount of Luna, the line of head, or even the line of hear |
| 3 | 165 | 0.5113 | The Line of Fate. 105 from Venus, the subject’s destiny will sway between imagination on the one hand and love and passi |
| 4 | 165 | 0.4913 | A. double or sister fate-line is an excellent sign. It denotes two distinct eareers which the subject will follow. This  |
| 5 | 163 | 0.4879 | Rising from the Mount of Luna, fate and success will be more or less dependent on the fancy and eaprice of other people. |

### fate line — variant (iii) DOCTRINE-INTERROGATIVE
Query: `what does a barely visible / moderately deep fate line signify — meaning and indications of a barely visible / moderately deep fate line`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 165 | 0.5958 | A. double or sister fate-line is an excellent sign. It denotes two distinct eareers which the subject will follow. This  |
| 2 | 163 | 0.5942 | The line of fate may rise from the line of hfe, the wrist, the Mount of Luna, the line of head, or even the line of hear |
| 3 | 165 | 0.5739 | The Line of Fate. 105 from Venus, the subject’s destiny will sway between imagination on the one hand and love and passi |
| 4 | 163 | 0.5651 | Rising from the Mount of Luna, fate and success will be more or less dependent on the fancy and eaprice of other people. |
| 5 | 163 | 0.5482 | The Line of Fate. 103 square. I wish to emphasize this as so many students throw up palimistry in despair through not ha |

### sun line — variant (i) RAW
Query: `Not clearly visible.; Sun line is faintly visible.`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 166 | 0.4638 | CHAPTER XIL. THE LINE OF SUN. And there are some who have success in wealth, And some in war, and some again in peace, A |
| 2 | 120 | 0.4390 | The Line of Sun, which rises generally on the Plain of Mars and ascends the hand tothe Mount of the Sun. The Line of Fat |
| 3 | 179 | 0.4241 | A wealthy union is shown by a strong, well-marked line from the side of the line of fate next Luna (h-h, Plate XX.), run |
| 4 | 166 | 0.4159 | I prefer in my work to call this the line of sun, as this name is more expressive and more clear in meaning. It increase |
| 5 | 169 | 0.3954 | The Line of Sun. 107 Rising from the line of fate, it increases the success promised by the line of fate, and gives more |

### sun line — variant (ii) LABEL+QUALITY
Query: `faintly visible sun line`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 166 | 0.4868 | CHAPTER XIL. THE LINE OF SUN. And there are some who have success in wealth, And some in war, and some again in peace, A |
| 2 | 166 | 0.4474 | I prefer in my work to call this the line of sun, as this name is more expressive and more clear in meaning. It increase |
| 3 | 120 | 0.4410 | The Line of Sun, which rises generally on the Plain of Mars and ascends the hand tothe Mount of the Sun. The Line of Fat |
| 4 | 169 | 0.4337 | The Line of Sun. 107 Rising from the line of fate, it increases the success promised by the line of fate, and gives more |
| 5 | 181 | 0.4235 | The Line of Marriage. 117 and into the line of sun, it tells that its possessor will marry some one of dis- tinction, an |

### sun line — variant (iii) DOCTRINE-INTERROGATIVE
Query: `what does a faintly visible sun line signify — meaning and indications of a faintly visible sun line`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 166 | 0.5206 | I prefer in my work to call this the line of sun, as this name is more expressive and more clear in meaning. It increase |
| 2 | 166 | 0.5176 | CHAPTER XIL. THE LINE OF SUN. And there are some who have success in wealth, And some in war, and some again in peace, A |
| 3 | 169 | 0.5064 | The Line of Sun. 107 Rising from the line of fate, it increases the success promised by the line of fate, and gives more |
| 4 | 160 | 0.4804 | When the line is quite bare of branches and thin, it tells of coldness of heart and want of affection. When bare and thi |
| 5 | 169 | 0.4780 | Rising from the line of heart it merely denotes a great taste for art and artistic things, and looking at it from the pu |

### thumb — variant (i) RAW
Query: `Medium relative size, set moderately low, wide angle from the palm.; Medium size, set moderately low, wide angle from the palm.`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 99 | 0.4678 | The Palm, and Large and Small Hands. en =) LARGE AND SMALL HANDS. It is a thing well worth remarking, that, generally sp |
| 2 | 98 | 0.4011 | CHAPTER NIL THE PALM, AND LARGE AND SMALL HANDS. A rut, hard, dry palm indicates timidity, and a nervous, worrying, trou |
| 3 | 99 | 0.3956 | Small hands, on the contrary, prefer to carry out large ideas, and, as a rule, make plans far too large for their power  |
| 4 | 51 | 0.3690 | CHAPTER II. THE ELEMENTARY, OR LOWEST TYPE. Tuts hand naturally belongs to the lowest type of mentality. In appear- ance |
| 5 | 95 | 0.3642 | When the fingers are thick and pnffy at the base, the subject considers 53 |

### thumb — variant (ii) LABEL+QUALITY
Query: `medium relative size / medium size thumb`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 87 | 0.4850 | The Thumb. 47 reason goes, the thumb loses all power and drops in on the hand, but that if the reason has only faded tem |
| 2 | 89 | 0.4839 | THE SECOND PHALANGE. The next important characteristic of the thumb is the shape and make of the second or middle phalan |
| 3 | 88 | 0.4582 | When the second phalange is much longer than the first, the subject, though having all the calmness and exactitude of re |
| 4 | 88 | 0.4562 | 45 Cheiro’s Language of the Hand. formed thumb denotes strength of intellectual will; the short, thick thumb, brute fore |
| 5 | 89 | 0.4540 | The Thumb. 49 THE SUPPLE-JOINTED THUMB. For example, the supple-jointed thumb, bending from the hand, is the in- dicatio |

### thumb — variant (iii) DOCTRINE-INTERROGATIVE
Query: `what does a medium relative size / medium size thumb signify — meaning and indications of a medium relative size / medium size thumb`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 88 | 0.5104 | 45 Cheiro’s Language of the Hand. formed thumb denotes strength of intellectual will; the short, thick thumb, brute fore |
| 2 | 87 | 0.5078 | The Thumb. 47 reason goes, the thumb loses all power and drops in on the hand, but that if the reason has only faded tem |
| 3 | 88 | 0.5041 | When the second phalange is much longer than the first, the subject, though having all the calmness and exactitude of re |
| 4 | 89 | 0.5035 | THE SECOND PHALANGE. The next important characteristic of the thumb is the shape and make of the second or middle phalan |
| 5 | 89 | 0.4813 | The Thumb. 49 THE SUPPLE-JOINTED THUMB. For example, the supple-jointed thumb, bending from the hand, is the in- dicatio |

### fingers — variant (i) RAW
Query: `Fingers are long relative to the palm, appear straight, with rounded fingertips, moderate spacing.; Fingers are slightly longer than the palm, appear straight, with rounded fingertips, spaced moderately apart.`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 95 | 0.5733 | Fingers thick and clumsy, as well as short, are more or less cruel and selfish. When the fingers are stiff and curved in |
| 2 | 95 | 0.5555 | CHAPTER XI. THE FINGERS. Frncers are either long or short, irrespective of the length of the palm to which they belong.  |
| 3 | 98 | 0.5513 | If it inclines to the line of life, it promises disappointment and trouble in domestic affairs, and if the rest of the h |
| 4 | 96 | 0.5422 | ot Cheivo’s Language of the Hand. his own comfort before that of others; he will desire luxury in eating, drink- ing, an |
| 5 | 95 | 0.5315 | When the fingers are thick and pnffy at the base, the subject considers 53 |

### fingers — variant (ii) LABEL+QUALITY
Query: `long relative to the palm / slightly longer than the palm fingers`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 98 | 0.5725 | If it inclines to the line of life, it promises disappointment and trouble in domestic affairs, and if the rest of the h |
| 2 | 99 | 0.5240 | The Palm, and Large and Small Hands. en =) LARGE AND SMALL HANDS. It is a thing well worth remarking, that, generally sp |
| 3 | 98 | 0.5232 | CHAPTER NIL THE PALM, AND LARGE AND SMALL HANDS. A rut, hard, dry palm indicates timidity, and a nervous, worrying, trou |
| 4 | 96 | 0.5153 | ot Cheivo’s Language of the Hand. his own comfort before that of others; he will desire luxury in eating, drink- ing, an |
| 5 | 96 | 0.5094 | When the fourth, or little finger, is well-shaped and long, it acts as a kind |

### fingers — variant (iii) DOCTRINE-INTERROGATIVE
Query: `what does a long relative to the palm / slightly longer than the palm fingers signify — meaning and indications of a long relative to the palm / slightly longer than the palm fingers`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 98 | 0.6033 | If it inclines to the line of life, it promises disappointment and trouble in domestic affairs, and if the rest of the h |
| 2 | 96 | 0.5429 | When the first, or index finger, is excessively long, it denotes great pride, and a tendeney to rule and domineer. It is |
| 3 | 98 | 0.5284 | CHAPTER NIL THE PALM, AND LARGE AND SMALL HANDS. A rut, hard, dry palm indicates timidity, and a nervous, worrying, trou |
| 4 | 96 | 0.5211 | When pointed, the reverse—callousness and frivolity. When the third finger (the finger of the Sun) is nearly of the same |
| 5 | 96 | 0.5149 | ot Cheivo’s Language of the Hand. his own comfort before that of others; he will desire luxury in eating, drink- ing, an |

### mount of venus — variant (i) RAW
Query: `Mount of Venus appears developed, other mounts are unremarkable.; Mount of Venus appears developed, other mounts are unremarkable.`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 111 | 0.6326 | THE MOUNT OF VENUS. The Mount of Venus is the develoyeout found at the base of the thu ~b (Plate XII.). Wher not abnorin |
| 2 | 112 | 0.5850 | 64 Cheiro’s Language of the Hand. Venus be well developed, it indicates strong and robust health. A small Mount of Venus |
| 3 | 113 | 0.5748 | Lhe Mounts, their Position and their Meanings. 69 THE MOUNT OF MARS. There are two mounts of this name; the first beneat |
| 4 | 111 | 0.5397 | CHAPTER XY. THE MOUNTS, THEIR POSITION AND THEIR MEANINGS. Ix my work I abways class the mounts of the hand (Plate XIJ.) |
| 5 | 189 | 0.5331 | THE STAR ON THE MOUNT OF VENUS. In the center or highest point of the Mount of Venus (J, Plate XVIIL) the star is once m |

### mount of venus — variant (ii) LABEL+QUALITY
Query: `developed mount of venus`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 111 | 0.6558 | THE MOUNT OF VENUS. The Mount of Venus is the develoyeout found at the base of the thu ~b (Plate XII.). Wher not abnorin |
| 2 | 112 | 0.5737 | 64 Cheiro’s Language of the Hand. Venus be well developed, it indicates strong and robust health. A small Mount of Venus |
| 3 | 189 | 0.5370 | THE STAR ON THE MOUNT OF VENUS. In the center or highest point of the Mount of Venus (J, Plate XVIIL) the star is once m |
| 4 | 111 | 0.4915 | CHAPTER XY. THE MOUNTS, THEIR POSITION AND THEIR MEANINGS. Ix my work I abways class the mounts of the hand (Plate XIJ.) |
| 5 | 112 | 0.4783 | THE MOUNT OF SATURN. This is found at the base of the second finger (Plate XII.), and denotes love of solitude, quietnes |

### mount of venus — variant (iii) DOCTRINE-INTERROGATIVE
Query: `what does a developed mount of venus signify — meaning and indications of a developed mount of venus`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 111 | 0.6520 | THE MOUNT OF VENUS. The Mount of Venus is the develoyeout found at the base of the thu ~b (Plate XII.). Wher not abnorin |
| 2 | 112 | 0.6181 | 64 Cheiro’s Language of the Hand. Venus be well developed, it indicates strong and robust health. A small Mount of Venus |
| 3 | 189 | 0.5676 | THE STAR ON THE MOUNT OF VENUS. In the center or highest point of the Mount of Venus (J, Plate XVIIL) the star is once m |
| 4 | 113 | 0.4970 | Lhe Mounts, their Position and their Meanings. 69 THE MOUNT OF MARS. There are two mounts of this name; the first beneat |
| 5 | 111 | 0.4856 | CHAPTER XY. THE MOUNTS, THEIR POSITION AND THEIR MEANINGS. Ix my work I abways class the mounts of the hand (Plate XIJ.) |

### mount of jupiter — variant (iii) DOCTRINE-INTERROGATIVE
Query: `what does a faint mount of jupiter signify — meaning and indications of a faint mount of jupiter`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 112 | 0.5735 | 64 Cheiro’s Language of the Hand. Venus be well developed, it indicates strong and robust health. A small Mount of Venus |
| 2 | 199 | 0.5246 | On the Mount of Mercury it denotes an unstable and rather unprincipled person. On the Mount of Luna it foretells restles |
| 3 | 113 | 0.5233 | Lhe Mounts, their Position and their Meanings. 69 THE MOUNT OF MARS. There are two mounts of this name; the first beneat |
| 4 | 198 | 0.5036 | 130 Cheiro’s Language of the Hand. An island on any of the mounts injures the qualities of the mount on which it is foun |
| 5 | 187 | 0.4906 | With a strong fate, head, and sun line, there is almost no step in the ladder of human greatness that the subject will n |

### markings/other features — variant (i) RAW
Query: `No clear marks visible.; No clear marks visible.`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 202 | 0.4040 | yet even where there is manual work this can still be observed by the ridges 134 |
| 2 | 172 | 0.3667 | When formed in httle straight pieces, bad digestion (i-7, Plate XIX.). In little islands, with long, filbert nails, dang |
| 3 | 171 | 0.3293 | The hepatica (Plate XIII.) should he straight down the hand—the straighter the better. It is an excellent sign to be wit |
| 4 | 220 | 0.3278 | In the seeond elass none of these points will be abnormal; the most striking peeuharity will be the 116 of head, which w |
| 5 | 161 | 0.3245 | The Line of Heart. 101 ticnlarly if the hand is soft. Ona hard hand such a mark will affect the subject less—he may not  |

### markings/other features — variant (ii) LABEL+QUALITY
Query: `no clear marks visible markings`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 202 | 0.4660 | yet even where there is manual work this can still be observed by the ridges 134 |
| 2 | 183 | 0.3557 | The lines relating to children are the fine upright limes from the end of the line of marriage. Sometimes these are so f |
| 3 | 172 | 0.3539 | When formed in httle straight pieces, bad digestion (i-7, Plate XIX.). In little islands, with long, filbert nails, dang |
| 4 | 162 | 0.3487 | whereas it has not one quarter the importance of the small line shown on the 102 |
| 5 | 152 | 0.3372 | By such illustrations the student will understand how to make every other modification in accordance with the type of ha |

### markings/other features — variant (iii) DOCTRINE-INTERROGATIVE
Query: `what does a no clear marks visible markings signify — meaning and indications of a no clear marks visible markings`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 155 | 0.3609 | [NotE.—I do not use or pay attention to such signs as the red cross on Mars or the black spot on Saturn as indications o |
| 2 | 187 | 0.3575 | 1 THE STAR ON THE MOUNT OF SATURN. On the center of the Mount of Saturn it is a sign of some terrible fatality (0, Plate |
| 3 | 198 | 0.3502 | THE CIRCLE. If found on the Mount of the Sun, the circle is a favorable mark. This is the only position in which it is f |
| 4 | 124 | 0.3429 | CHAPTER ITI. IN RELATION TO THE LINES. THE rules in relation to the lines are, in the first place, that they should be c |
| 5 | 172 | 0.3424 | When formed in httle straight pieces, bad digestion (i-7, Plate XIX.). In little islands, with long, filbert nails, dang |

## 3. Negative control

Query: `steam engine boiler maintenance`

| rank | page_ref | score | first 120 chars |
|---|---|---|---|
| 1 | 230 | 0.2192 | Among the many interestmg experiments made from time to time by the mventor and myself, there is one that has been quote |
| 2 | 228 | 0.1993 | This little machine was in its infancy then, and although scientists mar- veled at it in those days, yet there were few. |
| 3 | 129 | 0.1949 | 77 |
| 4 | 202 | 0.1888 | yet even where there is manual work this can still be observed by the ridges 134 |
| 5 | 231 | 0.1862 | One of the most extraordinary conditions of the machine is that there is no physical contact whatever required (see Pall |

## 4. Summary — p.134 / p.163 literal presence by feature × variant

Report only — no doctrine-vs-nomenclature classification performed here.

| Feature | p.134/p.163 hits |
|---|---|
| life line | (ii) rank 2, p.134; (iii) rank 2, p.134; (iii) rank 3, p.134 |
| head line | none |
| heart line | none |
| fate line | (i) rank 5, p.134; (ii) rank 2, p.163; (ii) rank 5, p.163; (iii) rank 2, p.163; (iii) rank 4, p.163; (iii) rank 5, p.163 |
| sun line | none |
| thumb | none |
| fingers | none |
| mount of venus | none |
| mount of jupiter | none |
| markings/other features | none |

## 5. Rider — unconsumed face/body test images removed

`git rm` on `data/test_images/` files whose filename contains "face" or "body" (case-insensitive) and have no consuming test/production surface. Palm fixture images (`palm_left_test.jpg`, `palm_right_test.jpg`) and `Back Hand.jpeg` (filename matches neither criterion) untouched.

- `data/test_images/Face.jpeg` — removed
- `data/test_images/Body.jpeg` — removed
