# Ring 3 P1 evidence — exact retrieval set for Runs A/B/C (identical query all runs; hand_detail excluded by design). Query reconstruction verified by exact score match.

Amended verification gate (Task 4b): pages/ordering exact match required;
each score within ±0.0002 of expected. Result: exact match on all 6
scores this run (0.6801, 0.6723, 0.6472, 0.6458, 0.6434, 0.6367 at pages
163, 123, 135, 120, 134, 166) — the prior run's 0.6473-vs-0.6472 on page
135 (Task 4, STOPPED under the stricter exact-match gate) reproduced here
as 0.6472 exactly, confirming that discrepancy was retrieval jitter, not
a stale expected-set or a query-construction error.

**Set-boundary margin (n=7 probe, same query):** chunk #7 = page 160,
score 0.6327. Margin between #6 (page 166, score 0.6367) and #7 = 0.0040.
**Jitter risk note:** the observed ±0.0001 jitter on individual chunk
scores is two orders of magnitude smaller than this 0.0040 margin — set
membership (which 6 chunks appear at n=6) is not at risk from that
jitter for this query; only chunk 3's own reported score value fluctuates
within tolerance.

Query reconstruction (`agent/interpretive/palm_reading.py:253`):
`" ".join(d for d in (palm_left, palm_right) if d)[:500]` — LEFT then
RIGHT, single-space join, truncated to 500 chars. Retrieval call:
`search(query_text, n_results=6, book_name="cheiroslanguageo00chei_1")`.

---

## [1] p.163 — score 0.6801

- **book_name:** cheiroslanguageo00chei_1
- **page_ref:** 163
- **score:** 0.6801
- **chunk_id:** cheiroslanguageo00chei_1_p163_c1

```
The line of fate may rise from the line of hfe, the wrist, the Mount of
Luna, the line of head, or even the line of heart.

If the fate-line rise from the line of life and from that poit on 18 strong,
suecess and riches will be won by personal merit; but if the lme be marked
low down near the wrist and tied down, as it were, by the side of the life-line,
it tells that the early portion of the subject's life will be sacrificed to the
wishes of parents or relatives (g-g, Plate XX.).

When the line of fate rises from the wrist and proceeds straight up the
hand to its destination on the Mount of Saturn, it is a sign of extreme good
fortune and success.
```

---

## [2] p.123 — score 0.6723

- **book_name:** cheiroslanguageo00chei_1
- **page_ref:** 123
- **score:** 0.6723
- **chunk_id:** cheiroslanguageo00chei_1_p123_c0

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

---

## [3] p.135 — score 0.6472

- **book_name:** cheiroslanguageo00chei_1
- **page_ref:** 135
- **score:** 0.6472
- **chunk_id:** cheiroslanguageo00chei_1_p135_c0

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

---

## [4] p.120 — score 0.6458

- **book_name:** cheiroslanguageo00chei_1
- **page_ref:** 120
- **score:** 0.6458
- **chunk_id:** cheiroslanguageo00chei_1_p120_c1

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

---

## [5] p.134 — score 0.6434

- **book_name:** cheiroslanguageo00chei_1
- **page_ref:** 134
- **score:** 0.6434
- **chunk_id:** cheiroslanguageo00chei_1_p134_c1

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

---

## [6] p.166 — score 0.6367

- **book_name:** cheiroslanguageo00chei_1
- **page_ref:** 166
- **score:** 0.6367
- **chunk_id:** cheiroslanguageo00chei_1_p166_c1

```
I prefer in my work to call this the line of sun, as this name is more
expressive and more clear in meaning. It increases the suecess given by a
good line of fate, and gives fame and distinction to the life when it is in
accordance with the work and career given by the other lines of the hand;
otherwise it merely relates to a temperament that is keenly alive to the
artistic, but unless the rest of the hand bears this out, the subject will have
the appreciation of art without the power of expression.

The line of sun may rise from the line of life, the Mount of Luna, the
Plain of Mars, the line of head, or the line of heart.
```
