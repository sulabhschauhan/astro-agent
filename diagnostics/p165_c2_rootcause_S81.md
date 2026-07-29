# p165_c2 Absence Root Cause — S81

## Page Mapping

**Page mapping:** Chunk id p165 refers to `page_ref=165` (1-indexed)
PDF page index: 165 (pdfplumber uses 1-indexed)
Mapping confidence: HIGH (chunk id page_ref is the direct source)

## Part 1: Live Chunks

**Result:** 3 chunks for p165:
- p165_c0: 614 chars
- p165_c1: 915 chars
- p165_c2: 355 chars
**c2 status:** PRESENT

## Part 2: Page Classification

**Progress record found:**
```
{
  "chunk_id": "cheiroslanguageo00chei_1_p165",
  "text": "The Line of Fate. 105\n\nfrom Venus, the subject\u2019s destiny will sway between imagination on the one\nhand and love and passion on the other (m-m, Plate XXT).\n\nWhen broken and irregular, the career will be uncertain; the ups and\ndowns of success and failure full of light and shadow.\n\nWhen there is a break in the line, it is a sure sign of misfortune and loss;\nbut if the second portion of the line begin before the other leaves off, it de-\nnotes a complete change in life, and if very decided it will mean a change\nmore in accordance with the subject\u2019s own wishes in the way of position and\nsuccess (6-6, Plate XXL).\n\nA. double or sister fate-line is an excellent sign. It denotes two distinct\neareers which the subject will follow. This ismuch more important if they go\nto different mounts.\n\nA square on the hne of fate protects the subject from loss through\nmoney, business, or financial matters. A square touching the line in the\nPlain of Mars (b, Plate XXI.) foretells danger from accident in relation to\nhome life if on the side of the fate-line next the line of hfe; from accident\nin travel if on the side of the fate-line next the Mount of Luna.\n\nA cross 18 a sign of trouble and follows the same rules as the square, but\nan island in the line of fate is a mark of misfortune, loss, and adversity\n(6, Plate XXI.). It is sometimes marked with the line of influence from Luna,\nand in such a case means loss and misfortune caused by the influence, be it\nmarriage or otherwise, which affects the life at that date (c, Plate X-XT).\n\nPeople without any sign of a line of fate are often very successful, but\ntaney lead more a vegetable kind of existence. They eat, drink, and sleep, but\nI do not think we can really call them happy, for they cannot feel acutely,\nend to feel happiness we must also feel the reverse. Sunshine and shadow,\nsmiles and tears comprise the sum total of our lives.",
  "topic": "",
  "language": "eng",
  "page_ref": 165,
  "image_path": null,
  "book_name": "cheiroslanguageo00chei_1",
  "page_type": "text"
}
```

## Part 3: Native Text Layer

**Native text extracted:** 1885 chars
```
The Line of Fate. 105
from Venus, the subject’s destiny will sway between imagination on the one
hand and love and passion on the other (m-m, Plate XXI.).
V hen broken and irregular, the career will be uncertain; the ups and
downs of success and failm*e full of light and shadow.
When there is a break in the line, it is a sure sign of misfortune and loss;
but if the second portion of the line begin before the other leaves off, it de¬
notes a complete change in life, and if very decided it will mean a change
more in accordance with the subject’s own wishes in the way of position and
success (a-a, Plate XXI.).
A double or sister fate-line is an excellent sign. It denotes two distinct
careers which the subject will follow. This is much more important if they go
to different mounts.
A square on the line of fate protects the subject from loss through
money, business, or financial matters. A square touching the line in the
Plain of Mars (h, Plate XXI.) foretells danger from accident in relation to
home life if on the side of the fate-line next the line of life; from accident
in travel if on the side of the fate-line next the Mount of Luna.
A cross is a sign of trouble and follows the same rules as the square, but
an island in the line of fate is a mark of misfortune, loss, and adversity
(d, Plate XXI.). It is sometimes marked with the line of influence from Luna,
and in such a case means loss and misfortune caused by the influence, be it
marriage or otherwise, which affects the life at that date (c, Plate XXI.).
People without any sign of a line of fate are often very successful, but
they lead more a vegetable kind of existence. They eat, drink, and sleep, but
I do not think we can really call them happy, for they cannot feel acutely,
and to feel happiness we must also feel the reverse. Sunshine and shadow,
smiles and tears comprise the sum total of our lives.
```

## Part 4: Mechanism Analysis

**F4 (mixed page text discard):** does not fire
  page_type = 'text' (from progress.json)

**F7 (embed filter non-empty only):** potentially fires
  Native text present: True (1885 chars)

**F6 (no whitespace normalization):** FIRES
  Native text contains 27 newlines

**DISPOSITIVE:** RETRIEVAL (chunk present, under-ranked)
  The chunk p165_c2 exists in the corpus (355 chars) but is not in the top 10
  results for the 'fate line' query. This is a retrieval ranking issue.

## Part 5: Fate-Line Doctrine Check

**Fate-line doctrine found:** YES
  1. "The Line of Fate"
  2. "A double or sister fate-line is an excellent sign"

## Part 6: Blast Radius

**Blast radius NOT APPLICABLE:** RETRIEVAL issues require per-query analysis
The ranking of p165_c2 in other queries (head-line, heart-line, etc.) would need
to be checked separately. This is query-specific, not a corpus-wide mechanism.
