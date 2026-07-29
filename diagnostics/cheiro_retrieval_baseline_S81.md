# Cheiro Retrieval Baseline — S81

## Inventory

**Divergence from S79/S80 baseline:**
- Total chunks: 463 (expected 463, delta +0)
- Folio-only chunks: 35 (expected 11, delta +24)
- Pages with zero chunks: 129 (expected 65, delta +64)

⚠ Inventory divergence detected (see deltas above)

## Baseline Rankings (U4 Anchor)

### Fate Line

| Rank | Chunk ID | Score |
|---|---|---|
| 1 | p162_c0 | 0.6724 |
| 2 | p163_c1 | 0.6720 |
| 3 | p165_c0 | 0.6676 |
| 4 | p163_c2 | 0.6432 |
| 5 | p163_c0 | 0.6340 |
| 6 | p164_c1 | 0.6339 |
| 7 | p165_c1 | 0.6247 |
| 8 | p169_c0 | 0.5801 |
| 9 | p136_c3 | 0.5677 |
| 10 | p208_c1 | 0.5647 |

**Named chunks:** `p165_c2`=ABSENT, `p163_c1`=2

### Head Line

| Rank | Chunk ID | Score |
|---|---|---|
| 1 | p145_c0 | 0.4829 |
| 2 | p150_c2 | 0.4349 |
| 3 | p151_c1 | 0.4310 |
| 4 | p164_c2 | 0.4120 |
| 5 | p147_c0 | 0.4079 |
| 6 | p150_c1 | 0.4066 |
| 7 | p151_c2 | 0.3998 |
| 8 | p137_c0 | 0.3996 |
| 9 | p16_c2 | 0.3990 |
| 10 | p147_c1 | 0.3965 |

**Named chunks:** `p145_c0`=1

### Heart Line

| Rank | Chunk ID | Score |
|---|---|---|
| 1 | p156_c0 | 0.6036 |
| 2 | p159_c2 | 0.5486 |
| 3 | p160_c2 | 0.5437 |
| 4 | p161_c0 | 0.5212 |
| 5 | p123_c0 | 0.5025 |
| 6 | p120_c0 | 0.4999 |
| 7 | p159_c3 | 0.4983 |
| 8 | p139_c0 | 0.4889 |
| 9 | p166_c1 | 0.4868 |
| 10 | p128_c0 | 0.4790 |

**Named chunks:** `p160_c3`=ABSENT, `p159_c2`=2, `p160_c1`=ABSENT

## Layer Evidence

### p165_c2
- Char count: 355
- Has OCR corruption: False
- Has mid-word newline: True

**Text (verbatim):**
```
People without any sign of a line of fate are often very successful, but
taney lead more a vegetable kind of existence. They eat, drink, and sleep, but
I do not think we can really call them happy, for they cannot feel acutely,
end to feel happiness we must also feel the reverse. Sunshine and shadow,
smiles and tears comprise the sum total of our lives.
```

### p163_c1
- Char count: 656
- Has OCR corruption: True
- Has mid-word newline: True

**Text (verbatim):**
```
The line of fate may rise from the line of hfe, the wrist, the Mount of
Luna, the line of head, or even the line of heart.

If the fate-line rise from the line of life and from that poit on 18 strong,
suecess and riches will be won by personal merit; but if the lme be marked
low down near the wrist and tied down, as it were, by the side of the life-line,
it tells that the early portion of the subject’s life will be sacrificed to the
wishes of parents or relatives (g-g, Plate XX.).

When the line of fate rises from the wrist and proceeds straight up the
hand to its destination on the Mount of Saturn, it is a sign of extreme good
fortune and success.
```

### p145_c0
- Char count: 789
- Has OCR corruption: False
- Has mid-word newline: True

**Text (verbatim):**
```
CHAPTER VII.
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
```

### p160_c3
- Char count: 153
- Has OCR corruption: False
- Has mid-word newline: True

**Text (verbatim):**
```
A subject with no line of heart, or with very little, has not the power of
feeling very deep affection. Such a person can, however, be very sensual, par-
```

### p159_c2
- Char count: 602
- Has OCR corruption: False
- Has mid-word newline: True

**Text (verbatim):**
```
When the line of heart is itself in excess, namely, lying right across the
hand from side to side, an excess of affection is the result, and a terrible
tendency toward jealousy; this is still more accentuated by a very long line
of heart rising to the outside of the hand and reaching the base of the first
finger.

When the line of heart is much fretted by a crowd of little lines rising
into it, it tells of inconstancy, flirtations, a series of amourettes, but no lasting
affection (Plate XX.).

A line of heart from Saturn, chained and broad, gives an utter contempt
for the subject’s opposite sex.
```

### p160_c1
- Char count: 747
- Has OCR corruption: False
- Has mid-word newline: True

**Text (verbatim):**
```
A very remarkable point is to notice whether the line of heart commence
high or low on the hand. ‘The first is the best, because it shows the happiest
nature.

The line lying so low that it droops down toward the line of head is a
sure sign of unhappiness in affections during the early portion of the hie.

When the line of heart forks, with one branch resting on Jupiter, the
other between the first and second fingers, it is a sign of a happy, tranquil
nature, good fortune, and happiness in affection; but when the fork is so
wide that one branch rests on Jupiter, the other on Saturn, it then denotes a
very uncertain disposition, and one that is not inclined to make the marital
relations happy, through its erratic temperament in affection.
```

## Verdicts

**Q1 (fate_line):** DATA
**Q2 (head_line):** RETRIEVAL
**Q3 (heart_line):** RETRIEVAL