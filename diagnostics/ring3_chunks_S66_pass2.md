# Ring 3 pass-2 chunk-text evidence (Session 66)

**Measure-first pass-2 evidence. Supersedes nothing — the pass-1 dump
(`diagnostics/ring3_chunks_S66.md`) stays as the pass-1 record.**

## Literal presence checks (lookups, not judgments)

Retrieved corpus checked: the live n=6 set below, extended to n=7 for
the boundary probe. Each item is a literal string/doctrine-presence
check against the ACTUAL retrieved chunk text — not an assessment of
whether the generated reading's claims are justified.

- **(a) Fate-line interpretive doctrine**: **ABSENT.** Two chunks name
  the fate line ("The Line of Fate, the Line of Destiny, or the
  Saturnian" — p.123; "The Line of Fate, which oceupies the center of
  the hand, from the wrist to the Mount of Saturn" — p.120c1), but
  neither states what the fate line *denotes* — naming and location
  only, no doctrine sentence of the "such a fate line denotes X" shape
  anywhere in the n=6 or n=7 set.
- **(b) Sun-line doctrine**: **ABSENT.** Same pattern — two chunks name
  the sun line ("The Line of Sun, the Line of Brillianey, or Apollo" —
  p.123; "The Line of Sun, which rises generally on the Plain of Mars
  and ascends the hand tothe Mount of the Sun" — p.120c1), naming and
  origin/course only, no doctrine about what it signifies (no "success,"
  "recognition," "fame," or equivalent claim present anywhere in the
  retrieved text).
- **(c) Thumb/willpower doctrine**: **ABSENT.** The word "thumb" does
  not appear anywhere in any of the 7 retrieved chunks (n=6 + the
  boundary chunk).
- **(d) Heart-line/affection doctrine**: **ABSENT.** Two chunks name
  the heart line ("The Line of Heart, the Mensal" — p.123; "The Line of
  Heart, which runs parallel to that of the head, at the base of the
  fingers" — p.120c0), naming and location only, no doctrine about
  affection, warmth, or emotional character anywhere in the retrieved
  text.

**Contrast — what IS present**: p.134's chunk carries genuine
interpretive life-line doctrine verbatim: *"The line of life should be
long, narrow, and deep, without irregularities, breaks, or crosses of
any kind. Such a formation promises long life, good health, and
vitality."* This directly grounds the life-line claims appearing in
all 3 captured dogfood readings ("promises good health, vitality, and
a long life"). No equivalent doctrine chunk was retrieved for fate,
sun, thumb, or heart — the readings' claims about those four features
(sun line "recognition/success," heart line "warmth and affection,"
fate line "personal choices shaping destiny," thumb "balance of
willpower") are not traceable to any retrieved passage's content, only
to the vision-model's own description text or the LLM's own synthesis.

---

## Step 1 — `.claude/read_prompt.md` enumeration

Three `## RUN` blocks found (all under the `DOGFOOD:::` section; the
later `MANUAL:::` section's "RUN A/B/C" text is differently formatted
— no `## RUN` header — and is NOT counted here per the literal `## RUN`
scope).

| Run (timestamp) | Confirmed-description subsections | Sources (page, score) | ring1_validation |
|---|---|---|---|
| `2026-07-12T21:52:13.042523` | LEFT, RIGHT | p.123 (0.6285), p.120 (0.6285), p.120 (0.6238), p.135 (0.6119), p.226 (0.5975), p.134 (0.5928) | passed=True, failures=() |
| `2026-07-12T21:52:49.170382` | LEFT, RIGHT | p.123 (0.6287), p.120 (0.6285), p.120 (0.6239), p.135 (0.6121), p.226 (0.5977), p.134 (0.593) | passed=True, failures=() |
| `2026-07-12T21:53:55.163731` | LEFT, RIGHT, **HAND_DETAIL** | p.123 (0.6285), p.120 (0.6285), p.120 (0.6238), p.135 (0.6119), p.226 (0.5975), p.134 (0.5928) | passed=True, failures=() |

**A Run C exists**: the third block (`21:53:55.163731`) carries a
HAND_DETAIL confirmed-description subsection alongside LEFT/RIGHT —
the pass-2 Run C shape. Its sources are identical (to 4dp) to Run 1's,
confirming (again) that hand_detail does not alter the RAG query,
consistent with `palm_reading.py`'s design (query built from
`palm_left`/`palm_right` only) and the Task 12 finding.

## Step 2 — Query reconstruction + gate check

`palm_reading.py`'s current construction (read directly, not assumed):
```python
query_text = " ".join(d for d in (palm_left, palm_right) if d)[:_QUERY_TRUNCATE_CHARS]
raw_sources = search(query_text, n_results=_N_RESULTS, book_name=_CHEIRO_BOOK)
# _QUERY_TRUNCATE_CHARS = 2000, _N_RESULTS = 6, _CHEIRO_BOOK = "cheiroslanguageo00chei_1"
```
Reconstructed verbatim from Run 1's LEFT (703 chars) + RIGHT (792
chars) confirmed descriptions -> `query_text` = 1496 chars (well under
the 2000-char cap).

Live n=6 retrieval: `p.123 (0.6287), p.120 (0.6285), p.120 (0.6239),
p.135 (0.6121), p.226 (0.5977), p.134 (0.593)`.

**GATE**: page ordering matches all 3 captured runs exactly (same 6
pages, same order, every run). Score comparison against each captured
run's sources (±0.0002):
- vs. Run 2 (`21:52:49`): **exact match**, 0.0000 diff on all 6.
- vs. Run 1 (`21:52:13`) and Run 3 (`21:53:55`): every diff is exactly
  0.0002 or less — within tolerance, consistent with the cited jitter
  precedent (Task 4b + observed A/B 4th-decimal drift). One raw
  floating-point comparison of the live API float against a literal
  (`0.6287 - 0.6285`) initially printed as a hair over the tolerance
  due to double-precision representation noise below the 4th decimal;
  re-verified with decimal-safe comparison and confirmed genuinely at
  or under 0.0002, not a real mismatch.

**GATE RESULT: PASS** (matches "a captured run's sources" exactly per
the gate's own wording — Run 2 — and is within tolerance of the other
two).

## Step 3 — Full chunk text (n=6) + n=7 boundary probe

### [1] p.123 (score 0.6287, `cheiroslanguageo00chei_1_p123_c0`)
```
The Lines of the Hand. 73

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
```

### [2] p.120 (score 0.6285, `cheiroslanguageo00chei_1_p120_c1`)
```
The Line of Sun, which rises generally on the Plain of Mars and
ascends the hand tothe Mount of the Sun.

The Line of Fate, which oceupies the center of the hand, from the
wrist to the Mount of Saturn.

The seven lesser lines on the hand are as follows:

The Line of Mars, which rises on the Mount of Mars and lies within
the Line of Life (Plate XIIL).

The Via Lasciva, which lies parallel to the hne of health (Plate XIII).

The Line of Intuition, which extends like a semicirele from Mereury
to Luna (Plate XIL.).

The Line of Marriage, the horizontal ne on the Mount of Mereury
(Plate XTII.), and
```

### [3] p.120 (score 0.6239, `cheiroslanguageo00chei_1_p120_c0`)
```
CHAPTER IL.
THE LINES OF THE HAND.

THERE are seven important lines on the hand, and seven lesser lines
(Piate XIII). The important hnes are as follows:

The Line of Life. which embraces the Mount of Venus.

The Line of Head, which erosses the center of the hand.

The Line of Heart, which runs parallel to that of the head, at the
base of the fingers.

The Girdle of Venus, found above the 116 of heart and generally
eneireling the Mounts of Saturn and the Sun.

The Line of Health, which runs from the Mount of Mereury down
the hand.
```

### [4] p.135 (score 0.6121, `cheiroslanguageo00chei_1_p135_c0`)
```
The Line of Life. 81

mencement (a-a, Plate XVIII), it is a very unfortunate sign, denoting that
the subject, through a defect in temperament, rushes blindly into danger and
catastrophe. This mark, as far as temperament is concerned, indicates the
subject's want of perception, both in personal dangers and in those arising
from dealmgs with other people.

When the line of life divides at about the center of the hand, and one
branch shoots across to the base of the Mount of Luna (-6, Plate X VIII.), it
indicates on a firm, well-made hand a restless life, a great desire for travel,
and the ultimate satisfaction of that desire. When such a mark is found on
a flabby, soft hand, with a sloping line of head, it again denotes the restless
nature, craving for excitement, but i this case the craving will be gratified
in vice or intemperance of some kind. This statement, as will be seen, can
be logically and easily reasoned out: the line crossing to the Mount of Luna
denotes the restless nature craving for change, but, the hand being soft and
flabby, the subject will be too lazy and indolent to satisfy this craving by
travel, and the sloping line of head in this case showing a weak nature, the
reason for this statement is apparent.
```

### [5] p.226 (score 0.5977, `cheiroslanguageo00chei_1_p226_c0`)
```
156 Modus Operandi.

I would next advise that you remark the fingers—their proportion to the
palm, whether long or short, thick or thin; class them as a whole, according
to the type they represent, or if they be mixed, class each individual finger.
Then notice the nails for their bearing on temper, disposition, and health.
Finally, after carefully examining the entire hand, turn your attention to the
mounts: see which mount or mounts have the greatest prominence; and then
proceed to the lines. There is no fixed rule as to the line to examine first ;
the best plan, however, is to start with the lines of life and health combimed,
then proceed to the line of head, the lne of destiny, the line of heart, and
80 on.
```

### [6] p.134 (score 0.593, `cheiroslanguageo00chei_1_p134_c1`)
```
The line of life should be long, narrow, and deep, without irregularities,
breaks, or crosses of any kind. Such a formation promises long life, good
health, and vitality.

When the line is linked (Fig. 10, Plate XIV.) or made up of little pieces
hkea chain, it is a sure sign of bad health, and particularly so on a soft hand.
When the line recovers its evenness and continuity, health also is regained.

When broken in the left hand and joined in the right, it threatens some
dangerous illness; but if broken in both hands it generally signifies death.
This is more decidedly confirmed when one branch turns back on the Mount
of Venus (-, Plate X 11.)
```

### n=7 boundary probe: [7] p.111 (score 0.5888, `cheiroslanguageo00chei_1_p111_c0`)
Margin below the 6th chunk (p.134, 0.593): **0.0042**.
```
CHAPTER XY.
THE MOUNTS, THEIR POSITION AND THEIR MEANINGS.

Ix my work I abways class the mounts of the hand (Plate XIJ.) with the
hand itself, and therefore I treat of them in the section of this work devoted
to cheirognomy. Again, in the consideration of this point, I must state that,
although manual labor will have the effect of coating the hand with a rougher
and thicker development of skin, vet it does not depress or decrease what are
known as the mounts, and which, again, in their turn, show constitutional
characteristics, which are doubtless caused by the hereditary laws which
govern and control the intermingling of races. As regards the use by
eheiromants of the old-time names, such as the Mount of Venus, Mars, ete.,
I must here state that I do not use these names in any sense in relation to
what is known as Astrological Palmistry. I do not for one moment deny that
there may be a connection—and a very great one—between the two; but 1
do not think it necessary to consider it in conjunction with this study of the
hand, which study I hold to be in every way complete in itself. Consequently,
I use such names as Venus, Mars, Saturn, etc., simply as a quicker way of
giving the student an idea of the qualities I wish to describe. These qualities
have been associated so long with such names in our minds as Mars, the
martial natwre, and so on, that their mere mention recalls them, ena the em-
ployment of these terms will, therefore, simplify matters meh more than if
I were to call the mounts by numbers, as first, second, third, and so forth.
```
(OCR artifacts such as "oceupies," "hnes," "eneireling," "eheiromants"
reproduced verbatim from the source corpus — not transcription errors
introduced here.)

No source files edited. Scratch reconstruction script + chunk-dump
output file deleted after capture.
