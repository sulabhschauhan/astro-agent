# n_results coverage sweep + top-10 content dump — S81

Reuses `scripts/retrieval_rank_probe_S81.py`'s existing top-20 fetch (same queries, same guard, same production `_resolve_feature_quality`/`_build_feature_query` path as `retrieval_rank_probe_S81.md`, commit `b51049e`) — no new search() calls issued, only re-sliced at n=3/5/8/10/15/20.

## Part 1 — coverage sweep

| feature | chunk_id | n=3 | n=5 | n=8 | n=10 | n=15 | n=20 |
|---|---|---|---|---|---|---|---|
| fate line | `cheiroslanguageo00chei_1_p165_c2` | out | out | out | out | in | in |
| fate line | `cheiroslanguageo00chei_1_p163_c1` | in | in | in | in | in | in |
| head line | `cheiroslanguageo00chei_1_p145_c0` | out | out | out | out | out | out |
| heart line | `cheiroslanguageo00chei_1_p160_c3` | out | out | out | out | out | out |
| heart line | `cheiroslanguageo00chei_1_p159_c2` | out | in | in | in | in | in |
| heart line | `cheiroslanguageo00chei_1_p160_c1` | out | out | in | in | in | in |

### Per-feature target count in top n

- **fate line**: n3=1/2  n5=1/2  n8=1/2  n10=1/2  n15=2/2  n20=2/2  min_n_all=15
- **head line**: n3=0/1  n5=0/1  n8=0/1  n10=0/1  n15=0/1  n20=0/1  min_n_all=NEVER-WITHIN-20
- **heart line**: n3=0/3  n5=1/3  n8=2/3  n10=2/3  n15=2/3  n20=2/3  min_n_all=NEVER-WITHIN-20

## Part 2 — precision cost: top-10 content dump

Evidence only — no relevance label, score, or n recommendation applied below. First 200 chars of chunk text, verbatim.

### fate line

**1.** `cheiroslanguageo00chei_1_p165_c1` — score 0.5099

> A. double or sister fate-line is an excellent sign. It denotes two distinct eareers which the subject will follow. This ismuch more important if they go to different mounts.  A square on the hne of fa

**2.** `cheiroslanguageo00chei_1_p165_c0` — score 0.5056

> The Line of Fate. 105  from Venus, the subject’s destiny will sway between imagination on the one hand and love and passion on the other (m-m, Plate XXT).  When broken and irregular, the career will b

**3.** `cheiroslanguageo00chei_1_p163_c1` — score 0.4892

> The line of fate may rise from the line of hfe, the wrist, the Mount of Luna, the line of head, or even the line of heart.  If the fate-line rise from the line of life and from that poit on 18 strong,

**4.** `cheiroslanguageo00chei_1_p163_c0` — score 0.4890

> The Line of Fate. 103  square. I wish to emphasize this as so many students throw up palimistry in despair through not having this point explained at the start.  The strange and mysterious thing to no

**5.** `cheiroslanguageo00chei_1_p127_c1` — score 0.4872

> I make no comment on this strange story; I simply relate the facts as they occurred.  The above is only one example in many that could be cited to show that we rarely if ever will go by warnings, no m

**6.** `cheiroslanguageo00chei_1_p136_c3` — score 0.4761

> When they cut the line of life only (6-0. Plate NVIL.). they denote the interference of relatives—generally in the home life.  When they cross the life-line and attack the line of fate (e-e, Plate AVI

**7.** `cheiroslanguageo00chei_1_p160_c2` — score 0.4747

> When the line is quite bare of branches and thin, it tells of coldness of heart and want of affection.  When bare and thin toward the pereussion or side of the hand, it denotes sterility.  Fine lines 

**8.** `cheiroslanguageo00chei_1_p162_c0` — score 0.4691

> CHAPTER XI. THE LINE OF FATE.  And what is fate?  A perfect law that shapes all things for good; And thus, that men may have a just reward For doing what is right, not caring should No earthly crown b

**9.** `cheiroslanguageo00chei_1_p163_c2` — score 0.4649

> Rising from the Mount of Luna, fate and success will be more or less dependent on the fancy and eaprice of other people. This 1s very often found in the case of public favorites.  Tf the line of fate 

**10.** `cheiroslanguageo00chei_1_p208_c1` — score 0.4641

> When they enter the line of fate and ascend with it, they denote travels that will materially benefit the subject.  When the end of any of these horizontal lines droop or curve downward toward the wri

### head line

**1.** `cheiroslanguageo00chei_1_p123_c0` — score 0.6090

> The Lines of the Hand. 73  The main lines are known by other names, as follows:  The Line of Life is also called the Vital.  The Line of Head, the Natural or Cerebral.  The Line of Heart, the Mensal. 

**2.** `cheiroslanguageo00chei_1_p151_c2` — score 0.5898

> THE LINE OF HEAD IN RELATION TO THE PSYCHIC HAND.  The natural position for the line of head on this hand is extremely sloping, giving all the visionary, dreamy qualities in accordance with this type.

**3.** `cheiroslanguageo00chei_1_p135_c2` — score 0.5866

> If the line leave the line of life and ascend to the Mount of the Sun, it denotes distinction according to the class of hand.  If it leave the line of life and cross to Mercury, it promises great succ

**4.** `cheiroslanguageo00chei_1_p124_c1` — score 0.5803

> Lines very dark in color, almost. black, tell of a melancholy, grave tem- perament, and also indicate a haughty, distant nature, one usually very revengeful and unforgiving.  Lines may appear, diminis

**5.** `cheiroslanguageo00chei_1_p134_c1` — score 0.5744

> The line of life should be long, narrow, and deep, without irregularities, breaks, or crosses of any kind. Such a formation promises long life, good health, and vitality.  When the line is linked (Fig

**6.** `cheiroslanguageo00chei_1_p135_c0` — score 0.5730

> The Line of Life. 81  mencement (a-a, Plate XVIII), it is a very unfortunate sign, denoting that the subject, through a defect in temperament, rushes blindly into danger and catastrophe. This mark, as

**7.** `cheiroslanguageo00chei_1_p160_c2` — score 0.5728

> When the line is quite bare of branches and thin, it tells of coldness of heart and want of affection.  When bare and thin toward the pereussion or side of the hand, it denotes sterility.  Fine lines 

**8.** `cheiroslanguageo00chei_1_p146_c2` — score 0.5705

> When extremely long and straight, and going directly to the side of the hand (the percussion), it usually denotes that the subject has more than ordinary intellectual power, but is inclined to be self

**9.** `cheiroslanguageo00chei_1_p140_c1` — score 0.5688

> When a branch shoots from this line out to the Mount of Luna (b-8, Plate XX.), it tells that there is a terrible tendeney toward intemperance of every kind, through the very robustness of the nature, 

**10.** `cheiroslanguageo00chei_1_p171_c1` — score 0.5686

> The hepatica (Plate XIII.) should he straight down the hand—the straighter the better.  It is an excellent sign to be without this line. Such absence denotes an extremely robust, healthy constitution.

### heart line

**1.** `cheiroslanguageo00chei_1_p159_c3` — score 0.6088

> When the line of heart is bright red, it denotes great violence of passion.  When pale and broad, the subject is blasé and indifferent.  When low down on the hand and thus close to the line of head, t

**2.** `cheiroslanguageo00chei_1_p160_c2` — score 0.6067

> When the line is quite bare of branches and thin, it tells of coldness of heart and want of affection.  When bare and thin toward the pereussion or side of the hand, it denotes sterility.  Fine lines 

**3.** `cheiroslanguageo00chei_1_p161_c0` — score 0.5970

> The Line of Heart. 101  ticnlarly if the hand is soft. Ona hard hand such a mark will affect the subject less—he may not be sensual, but he will never feel very deep affection.  When, however, the lin

**4.** `cheiroslanguageo00chei_1_p156_c0` — score 0.5775

> CHAPTER X. THE LINE OF HEART.  Keep still, my heart, Nor ask for peace, when care may suit thee best, Nor ask for love, nor joy, nor even rest, But be content to love, whate’er betide, And maybe love 

**5.** `cheiroslanguageo00chei_1_p159_c2` — score 0.5636

> When the line of heart is itself in excess, namely, lying right across the hand from side to side, an excess of affection is the result, and a terrible tendency toward jealousy; this is still more acc

**6.** `cheiroslanguageo00chei_1_p160_c1` — score 0.5296

> A very remarkable point is to notice whether the line of heart commence high or low on the hand. ‘The first is the best, because it shows the happiest nature.  The line lying so low that it droops dow

**7.** `cheiroslanguageo00chei_1_p123_c0` — score 0.5201

> The Lines of the Hand. 73  The main lines are known by other names, as follows:  The Line of Life is also called the Vital.  The Line of Head, the Natural or Cerebral.  The Line of Heart, the Mensal. 

**8.** `cheiroslanguageo00chei_1_p169_c2` — score 0.5163

> Rising from the line of heart it merely denotes a great taste for art and artistic things, and looking at it from the purely practical standpoint it denotes more distinction and influence in the world

**9.** `cheiroslanguageo00chei_1_p134_c1` — score 0.5140

> The line of life should be long, narrow, and deep, without irregularities, breaks, or crosses of any kind. Such a formation promises long life, good health, and vitality.  When the line is linked (Fig

**10.** `cheiroslanguageo00chei_1_p139_c0` — score 0.5086

> The Line of Life. 85  number of these lines of influence (it being remembered that only those near the line of life are important). Numerous lines indicate a nature dependent upon affection. Such peop

## Part 3 — threshold provenance

Verbatim, `agent/interpretive/palm_reading.py:168-175`:

```python
# THRESHOLD DISCIPLINE (CLAUDE.md Working Style #4).
# Justification: S67 probe (diagnostics/latest_run.md, commit 0a738c3)
# measured the worst doctrine-first-hit rank at 2 across all 8 provable
# features under the ratified variant (iii) template -- +1 margin. Scope
# guard: this module's per-feature call sites only -- does not alter
# query_engine.DEFAULT_N_RESULTS or any other caller. Revisit trigger:
# pass-3 claim ledgers showing support routinely landing at rank 3 -- go
# to 4 before blaming the template.
```

Verbatim, commit `0a738c3`'s `diagnostics/latest_run.md`, section 4 ("Summary — p.134 / p.163 literal presence by feature x variant") — this table is the ENTIRE evidentiary basis for the "worst rank 2" figure quoted above:

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

**Metric identification (not softened): the S67 probe's own script (`scripts/probe_r1_retrieval.py:335-338`) hardcodes exactly two page numbers — 134 and 163 — and checks EVERY feature's result set for literal presence of THOSE two pages only, regardless of which feature is being queried. It is a FIRST-HIT rank of a single pre-identified page per feature (page 134 tagged to life line, page 163 tagged to fate line), never a check for that feature's own full relevant-doctrine set, and never a coverage measure at all for the other 8 registry features (head line, heart line, sun line, thumb, fingers, mount of venus, mount of jupiter, markings/other features) — their "none" result is a check against the WRONG feature's page markers, not a demonstrated doctrine-retrieval failure for their own content. The "worst rank 2" figure is therefore computed from exactly 2 data points (life line's p.134 hit, fate line's p.163 hit) out of the registry's 10 features, not from '8 provable features' each independently measured for their own doctrine coverage — the comment's phrasing overstates what section 4 of the cited probe actually measured.

s67_metric: FIRST_HIT — a single hardcoded page's first-occurrence rank, checked against only 2 of 10 features' own content; not ALL-RELEVANT-DOCTRINE coverage for any feature.

## Part 4 — score geometry

### fate line — top 20 scores in order

0.5099, 0.5056, 0.4892, 0.4890, 0.4872, 0.4761, 0.4747, 0.4691, 0.4649, 0.4641, 0.4622, 0.4593, 0.4574, 0.4569, 0.4563, 0.4548, 0.4537, 0.4534, 0.4507, 0.4456

### head line — top 20 scores in order

0.6090, 0.5898, 0.5866, 0.5803, 0.5744, 0.5730, 0.5728, 0.5705, 0.5688, 0.5686, 0.5606, 0.5576, 0.5564, 0.5550, 0.5548, 0.5542, 0.5488, 0.5485, 0.5455, 0.5454

### heart line — top 20 scores in order

0.6088, 0.6067, 0.5970, 0.5775, 0.5636, 0.5296, 0.5201, 0.5163, 0.5140, 0.5086, 0.5057, 0.5055, 0.5045, 0.4975, 0.4927, 0.4919, 0.4913, 0.4876, 0.4861, 0.4847

### Largest consecutive-score gap per feature

| feature | largest consecutive gap | at rank (i -> i+1) |
|---|---|---|
| fate line | 0.0164 | rank 2 -> 3 |
| head line | 0.0192 | rank 1 -> 2 |
| heart line | 0.0340 | rank 5 -> 6 |
