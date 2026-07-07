# PVR Source Verification — Rasi Drishti (Sign Aspects)

**Task type:** read-only source verification. No code touched.

**Source file:** `data/pdfs/Vedic Astrology_ PVR Narashimha Rao.pdf` (515 pages).

**Location:** Ch.10 "Aspects and Argalas", §10.1–10.4, printed pp.100–104
(PDF pp.111–115), plus the Exercise 15 answer key, printed p.110
(PDF p.121). Confirmed NOT in Ch.8/Ch.9/§15.5 (already extracted in the
prior source-verification pass) — a whole-PDF term search for "rasi
drishti" / "sign aspect" turned up this chapter as the sole definitional
cluster; three later incidental mentions (PDF pp.141, 181, 225, 226) are
passing cross-references in unrelated Yoga/Dasa chapters, not additional
definition or table content (checked and excluded — see Item 2).

Page-number convention: "printed" = the book's own printed page number;
"PDF" = PyMuPDF's absolute page index. Offset confirmed at this chapter's
own boundary (PDF p.111 prints "100" in its header) — same printed+11=PDF
relationship established in the prior extraction pass.

No OCR garbling encountered in any quoted passage below.

---

## 1. Complete rasi drishti rule (movable/fixed/dual scheme + adjacency exclusion)

**Verbatim, framing (§10.1, printed p.100 / PDF p.111):**

> "There are 2 kinds of aspects: (1) graha drishti and (2) rasi drishti.
> Drishti means aspect. Each planet aspects certain houses from it with
> graha drishti (planetary aspect). The houses aspected are fixed based
> on the planet. In addition, rasis aspect each other and a planet
> aspects the rasis aspected by the rasi occupied by it. This is called
> rasi drishti (sign aspect)."

**Verbatim, the rule itself (§10.3, printed p.102 / PDF p.113):**

> "Rasis aspect other rasis based on the following rules:
> • A movable rasi aspects all fixed rasis except the one adjacent to it.
> • A fixed rasi aspects all movable rasis except the one adjacent to it.
> • A dual rasi aspects all other dual rasis."

This is the complete rule as PVR states it — three bullet points, no
further qualification attached to the rule statement itself. Note dual
signs get no adjacency exclusion (dual aspects ALL other dual signs,
3 of them, unconditionally) — only movable↔fixed pairs carry the
adjacency exception.

Ambiguity: **no.**

---

## 2. Worked example / table

**No full 12x12 (or per-sign, all-12-signs) table exists anywhere in the
book** — checked the definitional chapter (Ch.10) in full and the three
later incidental mentions (pp.141, 181, 225–226 PDF), none contain a
sign-aspect table. PVR gives:

**(a) Three worked per-sign examples, verbatim (§10.3, printed p.102 /
PDF p.113), one per rasi type:**

> "For example, Ar is a movable sign. It aspects all the fixed signs
> except the one adjacent to it, i.e. Ta. So Ar aspects Le, Sc and Aq.
>
> Ta is a fixed sign. It aspects all the movable signs except the one
> adjacent to it, i.e. Ar. So Ta aspects Cn, Li and Cp.
>
> Ge is a dual sign. It aspects all other dual signs. So Ge aspects Vi,
> Sg and Pi."

**(b) "Figure 2: Rasi Aspects" (printed p.102 / PDF p.113)** — an
embedded diagram ("A line is drawn between every pair of signs that
aspect each other"), i.e. a graph/visual, not text-extractable by this
pass (PyMuPDF text layer only; no OCR run on the embedded image). Its
informational content is the same movable/fixed/dual rule rendered
visually, per PVR's own caption sentence quoted in Item 3 below — not
independently verified pixel-by-pixel against the verbal rule.

**(c) Exercise 15 answer key — a partial worked table, per-planet (not
per-sign), 9 planets/nodes from "Chart 5" (printed p.110 / PDF p.121):**

> "Planet | Aspected Rasis | Aspected Houses | Aspected Planets
> Sun | Cn, Li, Cp | 9th, 12th, 3rd | Venus
> Moon | Le, Sc, Aq | 10th, 1st, 4th | Rahu, Mars, Saturn, Ketu
> Mars | Cp, Ar, Cn | 3rd, 6th, 9th | Venus, Moon
> Mercury | Pi, Ge, Vi | 5th, 8th, 11th | Jupiter
> Jupiter | Sg, Pi, Ge | 2nd, 5th, 8th | Mercury
> Venus | Ta, Le, Sc | 7th, 10th, 1st | Sun, Rahu, Mars, Saturn
> Saturn | Cp, Ar, Cn | 3rd, 6th, 9th | Venus, Moon
> Rahu | Li, Cp, Ar | 12th, 3rd, 6th | Venus, Moon
> Ketu | Ar, Cn, Li | 6th, 9th, 12th | Moon"

This confirms Rahu and Ketu ARE assigned rasi drishti by the ordinary
movable/fixed/dual rule from whatever sign each occupies in Chart 5 (not
shown in this extraction — Chart 5's own planetary positions were not
re-derived, only the answer table was captured verbatim). Cross-check:
Ketu's row (Ar, Cn, Li) is consistent with Ketu occupying a fixed sign
(Aq, inferred from the aspected-houses column's "own-house" logic used
elsewhere in the chapter) aspecting movable signs Ar/Cn/Li while
excluding its adjacent movable sign Cp — i.e. ordinary rule application,
not a reversed/anti-zodiacal count (see Item 4 on the unrelated Ketu
argala-reversal note).

Ambiguity: **no** for the rule itself; **partial/not found** for a
canonical full 12-sign table — none exists in the source, only 3
single-sign worked examples plus a 9-row per-planet exercise answer
covering (at most) 9 of the 12 signs as source-sign.

---

## 3. Symmetry statement

**Verbatim (§10.3, printed p.102 / PDF p.113):**

> "It may be noted that sign Y will aspect sign X if sign X aspects sign
> Y. A visual representation of rasi aspects is given in Figure 2. A
> line is drawn between every pair of signs that aspect each other."

PVR states the symmetry explicitly and in so many words ("sign Y will
aspect sign X if sign X aspects sign Y"), and the Figure 2 caption
("every pair of signs that aspect each other," undirected line, not an
arrow) corroborates it as an undirected/symmetric relation.

Ambiguity: **no.**

---

## 4. Exceptions / special cases / school-divergence footnotes on rasi drishti itself

**None found** in §10.1–10.4 (the rasi drishti definition and its
surrounding discussion). No footnote, alternate-tradition statement, or
special-case carve-out is attached to the movable/fixed/dual rule or its
adjacency exclusion.

**Flag — a DIFFERENT, unrelated rule exists nearby that a reader could
mistakenly import into rasi drishti:** §10.6 "Virodhargala" (printed
pp.105–106 / PDF pp.116–117) states, for the separate ARGALA concept
(not rasi drishti):

> "NOTE: If a sign contains Ketu, argalas and virodhargalas on it are
> counted anti-zodiacally. For example, let us say Ketu is in Vi. Then
> Le, Ge, Sc and Ta are the 2nd, 4th, 11th and 5th from Vi (counted
> anti-zodiacally) and planets in those signs cause argala on Vi and on
> the planets in Vi. Virodhargala is also counted similarly."

This anti-zodiacal counting is explicitly scoped by PVR to "argalas and
virodhargalas" only — it is never stated to apply to rasi drishti. The
Exercise 15 answer table (Item 2c above) empirically confirms this
scoping: Ketu's own rasi-drishti row follows ordinary zodiacal
movable/fixed/dual counting, not a reversed count. Reported here only as
a disambiguation flag, not as an exception to the rasi drishti rule
itself.

Ambiguity: **no** — absence is confirmed by a full read of §10.1–10.4,
not a sampling gap.

---

## 5. Do planets IN an aspected sign receive/cast the sign's aspect?

**Verbatim (§10.1, printed p.100 / PDF p.111):**

> "In addition, rasis aspect each other and a planet aspects the rasis
> aspected by the rasi occupied by it."

**Verbatim, restated with the receiving side made explicit (§10.3,
printed p.102–103 / PDF pp.113–114):**

> "A planet aspects the signs aspected by the sign it occupies. It also
> aspects the houses and planets in those signs. This aspect is called
> rasi drishti (sign aspect). For example, a planet in Libra will aspect
> the houses and planets in Aq, Ta and Le."

**Verbatim, casting side made explicit — ALL occupants of a sign cast the
same rasi drishti (§10.4, printed p.103 / PDF p.114):**

> "All planets in a sign will have rasi drishti on the same signs, just
> as people living in the same house see the same neighbors everyday and
> exert some influence over the same neighbors."

Both directions are explicit and unambiguous: (a) every planet occupying
a sign casts that sign's rasi drishti (casting side — all co-occupants
cast identically), and (b) any planet sitting in an aspected sign is
itself aspected (receiving side — "aspects the houses and planets in
those signs"). This directly supports §15.5.1 step 2's "conjoin/aspect a
planet" wording (from the prior extraction pass) — a planet in a
rasi-drishti-aspected sign counts as "aspected" for that step's
Jupiter/Mercury/dispositor count, on this chapter's own terms.

Ambiguity: **no.**

---

## Scope note

This task covered Ch.10 §§10.1–10.4 (rasi drishti definition) and the
Exercise 15 answer key only. §§10.5–10.8 (Argala/Virodhargala) were
skimmed only far enough to confirm the Ketu anti-zodiacal note's scope
(Item 4) and were not otherwise extracted — that is a separate topic from
rasi drishti and out of this task's scope.
