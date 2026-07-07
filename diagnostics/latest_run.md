# Two-Source Verification — §15.5.1 Stronger Co-Lord Cascade

**Task type:** read-only source verification + code arbitration. No code
files created or modified. Deliverable: resolve step-level semantics
before `strength.py` is designed. No interpretation, no recommendation
below — design chat decides.

**Sources:**
- PVR: `data/pdfs/Vedic Astrology_ PVR Narashimha Rao.pdf`, Ch.15
  §15.5.1, printed pp.201-203 (PDF pp.212-214, PyMuPDF 0-based page
  index, confirmed empirically below).
- PyJHora: local vendored package at `PyJHora-main/src/jhora/`.

Page-number convention (re-confirmed for this location, same
convention as the prior Ch.10 pass): "printed" = the book's own printed
page number; "PDF" = PyMuPDF's 0-based page index. Offset re-verified
locally at +11 (doc[212] prints "201" in its footer, doc[213] prints
"202", doc[214] prints "203") — same relationship as the earlier Ch.10
pass, confirmed independently rather than assumed.

Extraction tool: PyMuPDF (`fitz`), same as the prior extraction pass.
No OCR run; text-layer extraction only. All curly quotes/apostrophes
below are the PDF's own typographic characters (U+201C/U+201D/U+2019),
reproduced verbatim, not OCR artifacts.

---

## PART 1 — PVR Re-Extraction, Zero Elision

### Full verbatim text of §15.5.1 (printed pp.201-203 / PDF pp.212-214)

**Section heading and lead-in (printed p.201 / PDF p.212), immediately
following Exercise 24 and the "Importance of Sayanaadi Avasthas"
passage (different topic, included only as the boundary marker — not
part of §15.5.1):**

> "15.5 Other Simple Strengths
>
> 15.5.1
> Stronger Co-Lord
>
> When we find the arudha pada of a house falling in Scorpio or
> Aquarius, we need to find the stronger of Mars & Ketu (co-lords of
> Sc) and Saturn & Rahu (co-lords of Aq). The stronger lord acts its
> lord and decides the arudha pada. The stronger lord of Sc (or Aq) is
> also used in finding the duration of its dasa in many rasi dasas
> (e.g. Narayana dasa)."

**Basic rule and cascade framing (printed p.202 / PDF p.213):**

> "Basic rule: If one of the co-lords is in the rasi, take the other
> planet. For example, if Saturn is in Aq and Rahu is in a rasi other
> than Aq, Rahu becomes the primary lord of Aq. If not, we find the
> stronger of the 2 planets and the stronger planet becomes the
> primary lord.
>
> The stronger planet of two planets is determined using the following
> rules. We go from one rule to the next, only if we do not have a
> winner. If we have a winner in one step, we do not go through the
> remaining steps."

**Step (1) — joiner count, verbatim (printed p.202 / PDF p.213):**

> "(1) If one planet is joined by more planets than the other, it is
> stronger. Suppose Saturn is in Pi with Mars and Sun and Rahu is in Ar
> with Jupiter. Then Saturn is stronger than Rahu, because he is with
> 2 planets and Rahu is only with one planet. So Saturn becomes the
> primary lord of Aq."

**Step (2) — conjoin/aspect count, verbatim (printed p.202 / PDF
p.213):**

> "(2) We find how many of the following planets conjoin/aspect a
> planet: (1) Jupiter, (2) Mercury, and, (3) dispositor. A planet
> conjoined/aspected by more of these 3 planets is stronger. We must
> use rasi aspects here. Suppose Saturn is in Ge with Mercury, Rahu is
> in Ar, Mars is in Le, Jupiter is in Ta. Saturn is conjoined by
> Mercury and his dispositor (who is Mercury again). His count is 2.
> Rahu in Ar is aspected by Mars, his dispositor, from Le. Neither
> Jupiter nor Mercury aspects or conjoins Rahu. So Rahu's count of 1
> loses to Saturn's count of 2 and Saturn is the stronger planet. He
> becomes the lord of Aq."

**Step (3) — exaltation, verbatim (printed p.202 / PDF p.213):**

> "(3) If one planet is exalted and the other not, then the exalted
> planet is stronger. Suppose Saturn is in Li and Rahu is in Cn, with
> the same number of planets. Suppose we have a tie after step (2).
> Then we note that Saturn is exalted in Li and declare him as the
> stronger planet. He becomes the primary lord of Aq."

**Step (4) — modality (dual/fixed/movable), verbatim (printed p.202 /
PDF p.213):**

> "(4) If we have a tie after (3), we consider the natural strength of
> the rasi containing the planet. Dual rasis are stronger than fixed
> rasis and fixed rasis are stronger than movable rasis. Suppose Mars
> is in Ge and Ketu is in Aq and we have a tie between them after step
> (3). Then we declare Mars as the stronger planet and the primary
> lord of Sc, because he is in a dual rasi and Ketu is in a fixed
> rasi."

**Step (5)(a) — dasa-duration tiebreak, verbatim, spans the p.202/203
page break (PDF pp.213-214), footnote 53 included:**

> "(5) (a) When finding dasa duration: If we have a tie after (4), we
> take the planet giving a larger length for dasa. Supose [sic] Saturn
> is in Ge and Rahu is in Vi and suppose we have a tie after (4).
> Suppose we want to find the stronger lord for Narayana dasa. Rahu in
> Vi gives 5 years and Saturn in Ge gives 8 years⁵³. So Saturn is used
> instead of Rahu."
>
> Footnote 53 (printed p.202, foot of page): "We will learn the
> computation of dasa years in Narayana dasa later."

**Step (5)(b) — advancement-in-rasi tiebreak, verbatim (printed p.203 /
PDF p.214):**

> "(b) When finding the lord for arudha padas etc: If we have a tie
> after (4), we take the planet that is more advanced in its rasi. We
> measure the advancement of Rahu and Ketu from the end of the rasi.
> Suppose Mars is at 23Li17 and Ketu is at 5Cn54. Suppose we have a tie
> after (4). Advancement of Mars in Li is 23°17'. Advancement of Ketu
> from the end of Cn is 30° – 5°54' = 24°6'. Because Ketu is more
> advanced, Ketu is stronger than Mars and becomes the primary lord of
> Sc."

**Section closes (printed p.203 / PDF p.214) immediately with:**

> "Exercise 25: Find the primary lord of Aq and Sc in Chart 12 for the
> purpose of arudha padas."

followed immediately by the next section heading "15.5.2 / Stronger
Rasi" — confirming §15.5.1 ends at Exercise 25's prompt, with no
further prose. §15.5.2 is a different, related-but-distinct mechanism
(stronger of two ordinary rasis, used for graha arudha when a single
planet owns two signs) and is out of this task's scope; not quoted
here beyond this boundary marker.

This is the complete text of §15.5.1 — nothing elided. Total: lead-in
paragraph, basic rule, 5 numbered steps (step 5 has two sub-parts), one
footnote, and the Exercise 25 prompt.

---

### Item (a): Step 1 "joined by more planets" — does PVR qualify which bodies count?

**Not stated.** The rule text itself ("If one planet is joined by more
planets than the other, it is stronger") does not name which bodies
qualify as "planets" for this count. The only worked example uses
classical grahas exclusively as joiners: *"Saturn is in Pi with Mars
and Sun and Rahu is in Ar with Jupiter"* — Mars, Sun, and Jupiter are
all of the 7 classical planets; no node appears as a joiner in this
example (Rahu appears only as the planet whose strength is being
compared, occupying Aries, not as a co-joiner of Saturn). No sentence
anywhere in the quoted text restricts or extends the joiner set to
7-vs-9 bodies.

Ambiguity: **yes** — unresolved by the source text as quoted.

### Item (b): Step 2 — does PVR define "dispositor" for a planet in its own sign, or a node's dispositor?

**Not stated for the self-dispositor case.** The step-2 worked example
gives *"Saturn is conjoined by Mercury and his dispositor (who is
Mercury again)"* — Saturn occupies Gemini, so its dispositor is
Mercury, a *different* planet from Saturn; this example never puts a
planet in its own sign, so no sentence addresses what "dispositor"
means (or whether the term still applies) when planet1 or planet2 sits
in a sign it itself owns.

**A node's dispositor IS addressed, via the same example**: *"Rahu in
Ar is aspected by Mars, his dispositor, from Le"* — Rahu occupies
Aries, and PVR calls Mars (the ordinary lord of Aries) "his
[Rahu's] dispositor" without qualification or special-casing. This is
the Exercise 25 answer key's own further confirmation: *"Rahu is
aspected by Venus (his dispositor)"* (Rahu in Libra, Libra's ordinary
lord is Venus). Both instances treat a node's dispositor as the
ordinary lord of its occupied rasi, with no separate node-dispositor
rule stated.

Ambiguity: **yes** for the self-dispositor case (no example exists
either way); **no** for the node-dispositor case (two independent
confirming instances, both ordinary-rule).

### Item (c): Step 2 "conjoin/aspect" — confirm rasi aspects, and self-aspect example

**Confirmed, verbatim:** *"We must use rasi aspects here."* — stated
explicitly, immediately following the rule-2 statement, with no
qualification distinguishing it from any other aspect mechanism in the
book.

**Self-aspect / own-sign example:** **not addressed.** No example in
the quoted text shows a planet's dispositor coinciding with the planet
itself (see Item b), and no example shows a planet's own occupied sign
casting rasi drishti back onto its own house (which the prior Session
57 rasi-drishti source-verification pass already established is
structurally impossible under the movable/fixed/dual rule — a sign
never rasi-aspects itself). No sentence in this section discusses that
case one way or the other; it is simply never raised.

Ambiguity: **no** for the aspect mechanism itself (explicitly "rasi
aspects"); **yes/not applicable** for a self-aspecting scenario — no
worked example exists to confirm or deny, and it may be structurally
unreachable given the rasi-drishti primitive's own no-self-aspect
property (a separate module, not re-derived here).

### Item (d): Step 3 exaltation — does PVR treat Rahu/Ketu exaltation signs here?

**Not stated.** The step-3 worked example is *"Saturn is in Li and
Rahu is in Cn, with the same number of planets. Suppose we have a tie
after step (2). Then we note that Saturn is exalted in Li and declare
him as the stronger planet."* — this example resolves the tie via
Saturn's (a classical planet's) exaltation in Libra; it says nothing
about whether Rahu is or is not exalted in Cancer, and does not name
Rahu/Ketu's own exaltation sign(s) anywhere in this section. No
sentence in §15.5.1 itself assigns Rahu or Ketu an exaltation rasi.
(Whether such an assignment exists elsewhere in the book, e.g. a
dignity chapter, is outside this task's scope — the task asks what
§15.5.1 itself says, and it is silent.)

Ambiguity: **yes** — unresolved by the source text as quoted.

### Item (e): Worked example in or near §15.5.1 beyond Exercise 25

No additional worked example exists beyond the rule-embedded examples
already quoted in full above and Exercise 25 itself. The immediately
surrounding exercises (Exercise 24, printed p.201, and Exercise 26,
printed p.205) belong to different sections (avasthas, and §15.5.2
Stronger Rasi, respectively) — confirmed by reading their full prompts
and answer keys, neither one touches the Sc/Aq stronger-co-lord
mechanism.

**Exercise 25 prompt (printed p.203 / PDF p.214), quoted above.**

**Exercise 25 answer key, verbatim, in full (§15.6 "Answers to
Exercises", printed pp.205-206 / PDF pp.216-217):**

> "Exercise 25:
>
> Rahu is alone and Saturn is alone. We have a tie after rule (1).
> Saturn is aspected by Mercury and not aspected/conjoined by Jupiter
> and his dispositor (Jupiter again). Rahu is aspected by Venus (his
> dispositor) and not aspected by Mercury and Jupiter. Both have a
> count of one and we have a tie after rule (2). Neither Saturn nor
> Rahu is exalted after rule (3). Now we use rule (4). Saturn is in a
> dual rasi and Rahu is in a movable rasi. So Saturn is stronger and he
> becomes the primary lord of Aq.
>
> Mars is in Sc and Ketu is elsewhere (in Ar). So we don't even have to
> go through the rules to find the stronger planet. We use the "basic
> rule" and declare Ketu as the primary lord of Sc."

This answer key is itself a second confirming instance of Item (b)'s
node-dispositor finding (Rahu's dispositor = Venus, ordinary rule) and
demonstrates the Basic Rule short-circuit (Mars occupies its own sign
Scorpio, so Ketu wins immediately without entering the numbered
cascade at all) alongside a full run through rules (1)-(4) for the
Aq pair (Saturn vs. Rahu).

Ambiguity: **no** — confirmed no example exists beyond what is quoted
above; both halves (prompt + answer) reproduced in full.

---

## PART 2 — PyJHora Source Arbitration

**Scope discipline:** grepped only for the specified terms
("stronger", "co_lord", "colord", "stronger_planet", "stronger_rasi")
within the vendored `PyJHora-main/src/jhora/` tree; did not browse
beyond call sites needed to identify the direct §15.5.1 entry point.

**Direct entry point** — `PyJHora-main/src/jhora/horoscope/chart/house.py:939-951`:

```python
def house_owner_from_planet_positions(planet_positions,sign,check_during_dhasa=False):
    """ If house owner for Sc/Aq is forced - use that """ 
    if sign==const.SCORPIO and const.scorpio_owner_for_dhasa_calculations in [const.MARS_ID,const.KETU_ID]:
        return const.scorpio_owner_for_dhasa_calculations
    elif sign==const.AQUARIUS and const.aquarius_owner_for_dhasa_calculations in [const.SATURN_ID,const.RAHU_ID]: 
        return const.aquarius_owner_for_dhasa_calculations
    h_to_p = utils.get_house_planet_list_from_planet_positions(planet_positions)
    lord_of_sign = house_owner(h_to_p, sign)
    if sign == const.SCORPIO:
        lord_of_sign = stronger_planet_from_planet_positions(planet_positions, const.MARS_ID, const.KETU_ID, check_during_dhasa=check_during_dhasa)
    elif sign == const.AQUARIUS:
        lord_of_sign = stronger_planet_from_planet_positions(planet_positions, const.SATURN_ID, const.RAHU_ID, check_during_dhasa=check_during_dhasa)
    return lord_of_sign
```

Note the module-level config override (`scorpio_owner_for_dhasa_calculations`,
`aquarius_owner_for_dhasa_calculations`) that can force a fixed co-lord
and skip the cascade entirely — this knob has no counterpart anywhere
in the PVR text quoted in Part 1; PVR always runs the Basic Rule +
cascade, with no "force a fixed lord" concept stated.

**Core cascade implementation** —
`PyJHora-main/src/jhora/horoscope/chart/house.py:454-576`
(`_stronger_planet_new`, called from `stronger_planet_from_planet_positions`
at line 424; this is the "planet_positions"-based variant, the one the
NOTE at line 580 says to prefer: *"NOTE: To check all rules of
strength use stronger_planet_from_planet_positions()"*):

```python
def _stronger_planet_new(house_to_planet_dict,planet1=None,planet2=None):
    if planet1 is None: planet1 = const.SATURN_ID
    if planet2 is None: planet2 = const.RAHU_ID
    _debug_print = False
    if _debug_print: print('stronger_planet_new: finding stronger co lords ',planet_list[planet1],planet_list[planet2])
    if planet1==planet2:
        return planet1
    p_to_h = utils.get_planet_to_house_dict_from_chart(house_to_planet_dict)
    if _debug_print: print('p_to_h',p_to_h)
    RAHU_OR_KETU = [const.RAHU_ID,const.KETU_ID]
    planet1_house = p_to_h[planet1]
    planet2_house = p_to_h[planet2]
    if planet1 in RAHU_OR_KETU:
        lord_house_of_planets = const.houses_of_rahu_kethu[planet1]
    elif planet2 in RAHU_OR_KETU:
        lord_house_of_planets = const.houses_of_rahu_kethu[planet2]
    """ Basic Rule - If Planet1/Saturn/Mars in Aq/Sc and Planet2/Rahu/Ketu elsewhere then Planet2/Rahu/Ketu is stronger """
    if ((planet2 in RAHU_OR_KETU  or planet1 in RAHU_OR_KETU) and planet1_house==lord_house_of_planets and planet2_house != lord_house_of_planets):
        return planet2
    if ((planet2 in RAHU_OR_KETU  or planet1 in RAHU_OR_KETU) and planet2_house==lord_house_of_planets and planet1_house != lord_house_of_planets):
        return planet1
    """ Rule-1: If one planet is joined by more planets than the other, it is stronger. """
    planet1_co_planet_count = sum(value==planet1_house for value in p_to_h.values()) - 1 # Exclude planet itsef
    planet2_co_planet_count = sum(value==planet2_house for value in p_to_h.values()) - 1 # Exclude planet itself
    if planet1_co_planet_count > planet2_co_planet_count:
        return planet1
    elif planet2_co_planet_count > planet1_co_planet_count:
        return planet2
    """ Rule-2: how many of the following planets conjoin/aspect a planet: (1) Jupiter,(2) Mercury, and, (3) dispositor. """
    dispositor_of_planet1_house = const.house_owners[planet1_house]
    planet1_co_planet_count = 0
    planet1_co_planet_count += [p_to_h[const.MERCURY_ID],p_to_h[const.JUPITER_ID],dispositor_of_planet1_house].count(planet1_house)
    planet1_aspects = aspected_planets_of_the_raasi(house_to_planet_dict, planet1_house)
    planet1_co_planet_count += sum(p1 in planet1_aspects for p1 in [const.MERCURY_ID,const.JUPITER_ID,dispositor_of_planet1_house])

    planet2_co_planet_count = 0
    dispositor_of_planet2_house = const.house_owners[planet2_house]
    planet2_co_planet_count += [p_to_h[const.MERCURY_ID],p_to_h[const.JUPITER_ID],dispositor_of_planet2_house].count(planet2_house)
    planet2_aspects = aspected_planets_of_the_raasi(house_to_planet_dict, planet2_house)
    planet2_co_planet_count += sum(p2 in planet2_aspects for p2 in [const.MERCURY_ID,const.JUPITER_ID,dispositor_of_planet2_house])
    if planet1_co_planet_count > planet2_co_planet_count:
        return planet1
    elif planet2_co_planet_count > planet1_co_planet_count:
        return planet2
    """ Rule-3: If one planet is exalted and the other not, then the exalted planet is stronger. """
    if const.house_strengths_of_planets[planet1][planet1_house] == const._EXALTED_UCCHAM and \
        (const.house_strengths_of_planets[planet1][planet1_house] > const.house_strengths_of_planets[planet2][planet2_house]):
        return planet1
    if const.house_strengths_of_planets[planet2][planet2_house] == const._EXALTED_UCCHAM and \
        (const.house_strengths_of_planets[planet2][planet2_house] > const.house_strengths_of_planets[planet2][planet2_house]):
        return planet2
    """ Rule - 4: natural strength of the rasi containing the planet. 
        Dual rasis are stronger than fixed rasis and fixed rasis are stronger than movable rasis.
    """
    def _mod_rank(sign_idx):
        if sign_idx in const.dual_signs:
            return 3  # Dual
        elif sign_idx in const.fixed_signs:
            return 2  # Fixed
        else:
            return 1  # Movable
    m1 = _mod_rank(planet1_house)
    m2 = _mod_rank(planet2_house)
    if m1 > m2:
        return planet1
    elif m2 > m1:
        return planet2
    else:
        return None
```

`stronger_planet_from_planet_positions` (lines 386-453) calls the
above, and if it returns `None` (Rule-4 tie), falls through to its own
Rule-5(a)/(b) — dhasa-duration comparison if `check_during_dhasa=True`
(`house.py:432-444`, calls into `narayana._dhasa_duration`), else
advancement-in-rasi comparison (`house.py:446-453`, `planet1_longitude
> planet2_longitude` on the raw sidereal longitude — not explicitly
re-deriving "advancement from end of rasi" for nodes as a separate
step; see deviation flag below).

There is also a second, near-duplicate implementation, `stronger_planet`
(house.py:577-721, not shown in full here — structurally identical
rule-1-through-4 cascade, operating on `house_to_planet_dict` instead
of `planet_positions`, with the same Rule-2 conjoin-count construction
at lines 636-637 and 648). The docstring at line 580 explicitly flags
`stronger_planet_from_planet_positions` as the preferred/complete
entry point; `stronger_planet` reads as an older/parallel variant.

`aspected_planets_of_the_raasi` (house.py:349-355) — the function
Rule-2 calls to determine step-2's aspect count — is implemented via
`raasi_drishti_from_chart` (house.py:290-321), which iterates
`for p,_ in enumerate(planet_list[:9])`, i.e. all 9 chart points
including Rahu/Ketu, with no anti-zodiacal special-casing for nodes'
own rasi-drishti casting. This is **rasi-level** (sign) aspect, not
graha-level (planetary) aspect — confirmed by contrast with the
separate `graha_drishti_from_chart`/`aspected_planets_of_the_planet`
functions (house.py:324-332) that PyJHora keeps as a distinct code
path for planetary aspect.

### Item (a): Does its step-1 joiner count include Rahu/Ketu?

**Yes, by code inspection.** Rule-1's `planet1_co_planet_count = sum(value==planet1_house for value in p_to_h.values()) - 1`
iterates every value in `p_to_h` (the full planet-to-house dictionary,
which — per `utils.get_planet_to_house_dict_from_chart` — is built
over all planets in the chart, Sun through Ketu, not a 7-planet
subset). No filtering excludes Rahu/Ketu from the joiner count. This
answers Part 1 Item (a)'s "not stated" gap in the PVR text on the code
side: PyJHora includes nodes as qualifying joiners.

### Item (b): How does it handle self-dispositor?

**No special-casing found.** `dispositor_of_planet1_house =
const.house_owners[planet1_house]` unconditionally looks up the
ordinary lord of planet1's occupied rasi. If planet1 occupies its own
sign, `dispositor_of_planet1_house` simply equals `planet1` itself —
this value then flows into both the (see deviation flag below) conjoin
check and the aspect check with no exclusion or special path. This
mirrors Part 1 Item (b)'s finding that PVR's own text is silent on the
self-dispositor case — the code doesn't add a rule the text doesn't
have.

### Item (c): Which aspect function does it call for step 2?

**Sign-level (rasi drishti), not planet-level (graha drishti).**
`planet1_aspects = aspected_planets_of_the_raasi(house_to_planet_dict, planet1_house)`
resolves via `raasi_drishti_from_chart`, confirmed above. This matches
PVR's own explicit instruction in Part 1 Item (c): *"We must use rasi
aspects here."*

### Deviation flag (known-bugs caveat, per the bhava-bala-indexing precedent)

**Rule-2's "conjoin" (co-located) count has an apparent type mismatch,
found by direct code inspection — flagged as arbitration evidence, not
fixed, not filed as a bug report:**

```python
dispositor_of_planet1_house = const.house_owners[planet1_house]   # a PLANET id
planet1_co_planet_count += [p_to_h[const.MERCURY_ID],p_to_h[const.JUPITER_ID],dispositor_of_planet1_house].count(planet1_house)
```

`p_to_h[const.MERCURY_ID]` and `p_to_h[const.JUPITER_ID]` are HOUSE ids
(the rasi Mercury/Jupiter occupy) — correctly comparable to
`planet1_house` via `.count(...)`. But `dispositor_of_planet1_house`
is a PLANET id (e.g. `6` for Saturn), not the dispositor's occupied
house — the list mixes two different id spaces and then tests all
three against `planet1_house` (a rasi index 0-11). The parallel branch
a few lines below, for the *aspect* half of the same rule, does not
have this problem:

```python
planet1_co_planet_count += sum(p1 in planet1_aspects for p1 in [const.MERCURY_ID,const.JUPITER_ID,dispositor_of_planet1_house])
```

here `planet1_aspects` is itself a list of planet ids (per
`aspected_planets_of_the_raasi`'s return contract), so comparing
`dispositor_of_planet1_house` (a planet id) against it is type-
consistent. Only the *conjoin* half appears to compare mismatched id
spaces. This is a candidate implementation defect in PyJHora's Rule-2
"conjoin" sub-check — noted here as arbitration evidence per the
known-bugs caveat (bhava bala indexing precedent), not confirmed
against a numeric oracle, not fixed, and out of this task's read-only
scope. The identical pattern is present in both `_stronger_planet_new`
(house.py:505) and `stronger_planet` (house.py:637).

### Other deviations from the PVR text (Part 1) noted during arbitration

- **Config override knob** (`scorpio_owner_for_dhasa_calculations`,
  `aquarius_owner_for_dhasa_calculations`) — no counterpart in PVR's
  text; PyJHora-specific.
- **Modality rank (Rule-4)** — PyJHora's `_mod_rank` returns `None` on
  a tie (deferring to Rule-5) rather than PVR's phrasing, which treats
  steps as a strict ordered sequence with no explicit "return no
  winner, fall through" mechanism named — functionally equivalent, not
  a substantive deviation, noted for completeness only.
- **Step 5(b) advancement-from-end-of-rasi for nodes** — PVR's text
  explicitly measures Rahu/Ketu's advancement "from the end of the
  rasi" (worked example: *"Advancement of Ketu from the end of Cn is
  30° – 5°54' = 24°6'"*). `stronger_planet_from_planet_positions`'s own
  Rule-5(b) (house.py:446-453) compares `planet1_longitude >
  planet2_longitude` directly on the raw sidereal longitude passed in,
  with no visible from-end-of-rasi transform applied for Rahu/Ketu at
  that comparison site — whether that transform happens upstream
  (before `planet_positions` is constructed) was not traced, as doing
  so would exceed this task's "do NOT browse beyond this" scope guard.
  Flagged, not resolved.

---

## Scope note

Per the task's explicit instruction, this file is a two-source
verification only. No recommendation is made on any of the flagged
ambiguities or deviations; `strength.py`'s step-level semantics are a
design-chat decision informed by, not settled by, this document.
