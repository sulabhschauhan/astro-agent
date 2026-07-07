# PVR Source Verification — Jaimini (Chara Karakas / Arudha Padas / Co-Lordship)

**Task type:** read-only source verification. No code touched.

**Source file:** `data/pdfs/Vedic Astrology_ PVR Narashimha Rao.pdf` (515 pages).
NOTE: The Master Build Plan's cited path
(`project_files/classical_references/PVR_Vedic_Astrology_Integrated_Approach.pdf`)
does not exist in the repo — `project_files/classical_references/` is not
present at all. The actual PVR PDF lives at `data/pdfs/`. This is a path
discrepancy the design chat should reconcile in the Master Build Plan.

**Chapter citation correction:** The Master Build Plan's "Chapter 32" citation
for Jaimini/Arudha material is **wrong**. Verified actual chapters via the
book's own Contents page (PDF page 10):

| Chapter | Title | Printed page | PDF page |
|---|---|---|---|
| 8 | Karakas | 79 | 90 |
| 9 | Arudha Padas | 85 | 96 |
| 15 | Strength of Planets and Rasis | 187 | 198 |

(Chapter 32, "Impact of Birthtime Error," printed p.420, is an unrelated
Part 5 chapter — confirmed not to contain karaka/arudha content.)

Page-number convention used below: "printed" = the page number the book
itself prints in its header/footer; "PDF" = the PDF reader's absolute page
index (0-based, as returned by PyMuPDF) for the physical page carrying that
printed number. Offset is printed + 11 = PDF, confirmed at three independent
chapter boundaries (Ch.8/9/10 and Ch.15 starts).

No OCR garbling was encountered in any quoted passage below; text layer is a
clean digital extraction (occasional mis-rendered apostrophe/em-dash glyphs
in the raw PyMuPDF output, silently normalized to straight quotes here —
does not affect content).

---

## 1. Karaka scheme (7 vs 8 chara karakas, list, Rahu, Pitri Karaka)

**Verbatim (Ch.8 "Karakas," §8.1, printed p.79 / PDF p.90):**

> "There are 3 kinds of karakas:
> (1) Naisargika karakas (natural significators, 9 in number).
> (2) Chara karakas (variable significators, 8 in number), and,
> (3) Sthira karakas (fixed significators, 7 in number),"

> "Chara karakas include Rahu and the seven planets. They do not include
> Ketu, as Ketu stands for moksha (emancipation) and does not stand for any
> person who affects one's sustenance."

**Full ordered list (Table 13, §8.2, printed p.80 / PDF p.91):**

> "1 | Atma Karaka | AK | Self
> 2 | Amatya Karaka | AmK | Ministers
> 3 | Bhratri Karaka | BK | Siblings
> 4 | Matri Karaka | MK | Mother
> 5 | Pitri Karaka | PiK | Father
> 6 | Putra Karaka | PK | Children
> 7 | Jnaati Karaka | GK (JK) | Rivals
> 8 | Dara karaka | DK | Spouse"

PVR explicitly uses **8 chara karakas**, includes **Rahu**, and his scheme
**does include a Pitri Karaka** (slot 5, father) — this is the "8-karaka"
(ashta-karaka) scheme, distinct from the alternate 7-karaka scheme (which
omits a separate Pitri Karaka). Ketu is explicitly excluded from the chara
karaka set (used in naisargika and sthira sets only).

Ambiguity: **no.**

---

## 2. Degree convention for karaka degree (incl. Rahu's rule)

**Verbatim (§8.2, printed p.80 / PDF p.91):**

> "(1) Take the eight planets – Sun, Moon, Mars, Mercury, Jupiter, Venus,
> Saturn and Rahu. For each planet, find its advancement from the beginning
> of the rasi occupied by it. For Rahu, measure the advancement from the
> end of his rasi.
> (2) Arrange them in the decreasing order of advancement.
> (3) The planet with the highest advancement is Atma Karaka (significator
> of self)."

**Rahu's rule confirmed numerically in worked Example 28 (printed p.81 /
PDF p.92):**

> "Rahu | 30° – 1°43' = 28°17' | 1 | AK"

i.e. Rahu's karaka-degree = 30° minus his longitude-within-sign (not the
mirror/reverse-motion longitude, just a straight 30°-minus-advancement
subtraction). Precision demonstrated in examples is **degrees and minutes**
(e.g. "25°18'", "17°21'"); seconds-level precision is invoked only in the
tie-break rule (Item 3 below), not shown worked in any example.

Ambiguity: **no.**

---

## 3. Tie-break for identical karaka degrees

**Verbatim (§8.2, printed pp.80–81 / PDF pp.91–92):**

> "If two planets have the same degrees, we should compare minutes. If
> minutes are same, we should compare the seconds. If two planets are
> exactly at the same longitude, then they will hold a karakatwa
> (signification) together and the next karakatwa will have no ruler. We
> should use the corresponding sthira karaka in that case. However, this
> rarely becomes necessary, as two planets are rarely at exactly the same
> longitude."

Ambiguity: **no** — rule is fully specified (degree → minute → second →
exact-tie fallback to sthira karaka), though PVR does not give a worked
numeric example of the exact-tie case.

---

## 4. Arudha pada formula (house → lord → same-distance-from-lord)

**Verbatim (§9.2 "Computation of Bhava Arudhas," printed p.86 / PDF p.97):**

> "(1) Take sign containing the house of interest in the divisional chart
> of interest.
> (2) Find the sign occupied by the lord of that house.
> ...
> (3) Count signs from the house of interest to the sign containing its
> lord. Counting is in the zodiacal direction always. For example, if the
> house we are interested in is in Gemini and its lord Mercury is in
> Aquarius, we count signs from Gemini to Aquarius and get 9.
> (4) Count the same number of signs from the sign containing the lord and
> find the ending sign. In the above example, we count 9 signs from
> Aquarius and we end up in Libra."

Counting convention is stated as "the zodiacal direction always" and the
worked example (Gemini→Aquarius = 9) is **inclusive** counting (Ge=1 ...
Aq=9, i.e. both endpoints counted) — PVR never uses the words
"inclusive"/"exclusive" himself; this is inferred only from the arithmetic
of the worked example, not from an explicit terminological statement.

The identical formula (steps 1–4, verbatim) is repeated for graha arudhas
in §9.5 (printed p.94 / PDF p.105), substituting "sign owned by the
planet" for "sign occupied by the lord."

Ambiguity: **partial** — the inclusive/exclusive counting convention is
demonstrated by example, not asserted in words.

---

## 5. Arudha exception rule (same sign / 7th from house → correction)

**Verbatim (§9.2, printed p.86 / PDF p.97):**

> "(5) Exception: If the sign found thus in step (4) is in the 1st or 7th
> from the original sign in step (1), then we take the 10th sign from the
> sign found in step (4). Otherwise we don't make any change.
> (6) The resulting sign contains the arudha pada of the house of
> interest."

Identical wording (mutatis mutandis for "planet of interest") given again
for graha arudhas, §9.5, printed p.94 / PDF p.105:

> "(5) Exception: If the sign found thus in step (4) is in the 1st or 7th
> from the original sign containing the planet, then we take the 10th sign
> from the sign found in step (4). Otherwise we don't make any change."

The prescribed correction is unambiguously **"the 10th sign from the sign
found in step (4)"** — not 4th, not 10th-from-original. Confirmed
numerically in worked Example 29 (printed p.87 / PDF p.98, house 1): "we
get Vi. However, this is in the 1st from the original sign (Vi). So we
take the 10th therefrom and get Ge. AL is in Ge." — i.e. 10th counted from
the (excepted) landing sign, not from the house/lord sign.

Ambiguity: **no.**

---

## 6. Co-lordship (Scorpio / Aquarius) — stronger-lord criteria

**Verbatim, arudha-context NOTE (§9.2, printed p.86 / PDF p.97):**

> "NOTE: Aquarius is owned by Saturn and Rahu. Scorpio is owned by Mars and
> Ketu. Take the stronger lord in the case of houses falling in these two
> signs. The chapter on 'Strength of Planets and Rasis' will explain the
> rules used in comparing the strengths of planets."

**Full stronger-co-lord procedure, verbatim (Ch.15, §15.5.1 "Stronger
Co-Lord," printed pp.201–203 / PDF pp.212–214):**

> "When we find the arudha pada of a house falling in Scorpio or Aquarius,
> we need to find the stronger of Mars & Ketu (co-lords of Sc) and Saturn &
> Rahu (co-lords of Aq). The stronger lord acts its lord and decides the
> arudha pada. The stronger lord of Sc (or Aq) is also used in finding the
> duration of its dasa in many rasi dasas (e.g. Narayana dasa)."

> "Basic rule: If one of the co-lords is in the rasi, take the other
> planet. For example, if Saturn is in Aq and Rahu is in a rasi other than
> Aq, Rahu becomes the primary lord of Aq. If not, we find the stronger of
> the 2 planets and the stronger planet becomes the primary lord."

> "The stronger planet of two planets is determined using the following
> rules. We go from one rule to the next, only if we do not have a winner.
> If we have a winner in one step, we do not go through the remaining
> steps.
>
> (1) If one planet is joined by more planets than the other, it is
> stronger. ...
> (2) We find how many of the following planets conjoin/aspect a planet:
> (1) Jupiter, (2) Mercury, and, (3) dispositor. A planet
> conjoined/aspected by more of these 3 planets is stronger. We must use
> rasi aspects here. ...
> (3) If one planet is exalted and the other not, then the exalted planet
> is stronger. ...
> (4) If we have a tie after (3), we consider the natural strength of the
> rasi containing the planet. Dual rasis are stronger than fixed rasis and
> fixed rasis are stronger than movable rasis. ...
> (5) (a) When finding dasa duration: If we have a tie after (4), we take
> the planet giving a larger length for dasa. ...
> (b) When finding the lord for arudha padas etc: If we have a tie after
> (4), we take the planet that is more advanced in its rasi. We measure the
> advancement of Rahu and Ketu from the end of the rasi. ..."

Note step (5) **branches by purpose** — (5)(a) for dasa duration uses
"larger dasa length," (5)(b) for arudha padas uses "more advanced in rasi"
(same advancement convention as chara-karaka degree, Item 2). This is a
distinct, purpose-specific step 5, not a single unified rule.

Related "Stronger Rasi" procedure (§15.5.2, printed pp.203–205 / PDF
pp.214–216) is explicitly cross-referenced for graha-arudha's "stronger
sign owned by the planet" step (§9.5's NOTE), and is structurally identical
(planet count → Jupiter/Mercury/lord aspect count → exaltation → rasi
oddity-of-lord's-sign → dual/fixed/movable → lord's advancement), but is a
**different rule set** (compares two rasis, not two planets) — flagged here
because it is the rule actually invoked by §9.5's graha-arudha "stronger
sign owned" step for Mars/Mercury/Jupiter/Venus/Saturn (who each own 2
signs), as opposed to §15.5.1 which resolves Sc/Aq's two-*planet*
co-lordship.

Ambiguity: **no** — procedure is fully specified and exemplified (Exercise
25 answer, printed p.202 / PDF p.213: "Mars is in Sc and Ketu is elsewhere
(in Ar). So we don't even have to go through the rules... We use the
'basic rule' and declare Ketu as the primary lord of Sc.").

---

## 7. Upapada (UL)

**Verbatim, definition (§9.2, printed p.86 / PDF p.97):**

> "There are two special cases: Arudha pada of lagna is denoted as AL
> (arudha lagna) and arudha pada of 12th house is denoted as UL (upapada
> lagna)."

**Verbatim, usage (§9.4 "Use of Bhava Arudhas," printed p.90 / PDF p.101):**

> "One important arudha pada used in Jyotish is upapada lagna (UL) – the
> arudha pada of the 12th house. This shows one's marriage and spouse."

> "The 8th house from UL shows the longevity of marriage and the 2nd and
> 7th houses from UL show the end of marriage. Malefics like Mars, Saturn
> and nodes in these houses from UL can result in troubles for the
> marriage and even a divorce."

PVR defines UL strictly as **the arudha pada of the 12th house**, computed
by the identical general bhava-arudha procedure (Item 4/5 above) applied
with house-of-interest = 12th (lord of 12th, count house→lord, same count
from lord, apply the 1st/7th exception). No alternate definition (e.g. "UL
= arudha of 7th," "UL computed from a different lord") appears anywhere in
Ch.9. No UL-specific exception rule beyond the general bhava-arudha
exception (Item 5) is stated — the 8th/2nd/7th-from-UL rules quoted above
are interpretive/results rules, not computation-exception rules.

Ambiguity: **no** for the definition; **not found** for any UL-specific
computational exception distinct from the general bhava-arudha rule.

---

## 8. Explicit school-divergence statements

Searched Ch.8 (Karakas), Ch.9 (Arudha Padas), and Ch.15 §15.5 (Stronger
Co-Lord / Stronger Rasi) in full for footnoted or in-text alternate-school
statements. Result: **no divergence statement exists for the chara-karaka
scheme (7-vs-8), the arudha formula, the arudha exception rule, the
co-lordship stronger-lord procedure, or the UL definition.** PVR states
those as single, undisputed procedures throughout Ch.9 and Ch.15 §15.5.

The only explicit alternate-school statements found in this page range are
**footnoted and scoped to the sthira-karaka (fixed significator) list**,
not the chara-karaka scheme item 1 asked about:

**Verbatim, main text (§8.3, printed p.82 / PDF p.93):**

> "For example, some astrologers use the 7th from Jupiter instead of the
> 7th from Venus to predict marriage. However, Venus is the natural
> significator of marriage and the 7th from Venus should be used for
> predicting marriage, both in male and female charts."

**Verbatim, footnote 26 (printed p.82 / PDF p.93):**

> "Some people opine that Sun should be taken as the fixed significator of
> father for daytime births and Venus for nighttime births. Similarly,
> Moon is taken as the fixed significator of mother for nighttime births
> and Mars for daytime births."

**Verbatim, footnote 27 (printed p.82 / PDF p.93):**

> "Some scholars give Saturn as the sthira karaka for children instead of
> elder siblings."

**Verbatim, footnote 28 (printed p.82 / PDF p.93):**

> "Some scholars take Jupiter as the sthira karaka of spouse in male charts
> also."

These four are the complete set of alternate-tradition footnotes in the
Karakas/Arudha/co-lordship material. All four concern **sthira karakas**
(death-timing significators), which is out of scope for the current P6
Jaimini build (Arudha/Padas) — flagged here only because the prompt asked
to surface any school-divergence statement PVR makes "on the above," and
these are the only ones present in the searched chapters.

Ambiguity: **no** — divergence statements themselves are unambiguous;
their absence for items 1 and 4–7 is a confirmed "not found," not an
extraction gap (full chapter text was read, not sampled).

---

## Scope note

This task covered Ch.8, Ch.9, and Ch.15 §§15.4–15.6 only (the chapters
containing the Karaka/Arudha/co-lordship material). No other chapter was
searched. `helpers/house_counting.py`'s counting convention and
`_pvr_spec_reference.json` (found at
`agent/calculations/core/_pvr_spec_reference.json` during this search) were
not opened or cross-checked against this material — that reconciliation, if
needed, is a separate task.
