# Line of Fate — Doctrine Inventory (Ch. XI, Step 0)

**Scope:** Cheiro's Language of the Hand, Ch. XI "THE LINE OF FATE."
Source: `data/cheiro/cheiro_pdf_fulltext.md`, lines 1074 (`CHAPTER XI.`) to 1117
(chapter end; line 1118 is `CHAPTER XII.` / `THE LINE OF SUN.` — unambiguous
boundary, confirmed by direct grep of both chapter headings). Read whole,
in order, from the page-level text, per `PALM_PIPELINE.md` Step 0.

**Method note:** granularity is per DOCTRINAL CLAUSE, not per orthographic
sentence — several Cheiro sentences are compound ("if A ... ; but if B ...")
and are split into `a`/`b`/`c` sub-rows so each row is the eventual
isomorphism unit Step 1 needs (one rule per source fragment). Page-furniture
(running headers/footers "102", "The Line of Fate. 103", "104 Cheiro's
Language of the Hand.", "The Line of Fate. 105") and the two structural
headings (`CHAPTER XI.` / `THE LINE OF FATE.`) are not doctrine and are not
rowed.

---

## PRE-WORK (carried from the prior turn, re-stated for this file's record)

Neither `agent/interpretive/observation_extractor.py`'s working-tree diff
(adds 7 Mount-of-* aliases, unrelated to lines/Fate) nor
`scripts/vocab_reachability_scan.py`'s diff (adds a `--rules` CLI flag,
tooling generalization only) touches Fate feature/attribute/value emission.
Clear to proceed.

---

## G1 / G2 — the two gaps closed before writing this file

**G1 — EMITTED or PARSE-ONLY?** `agent/palm_processor.py`'s
`describe_palm_image` system prompt (lines ~231-236) instructs the vision
model explicitly:

```
FATE LINE: same attributes (state plainly if absent or barely visible)
  SLOPE: exactly one of {upward | downward | straight | not clearly visible}
  ORIGIN: exactly one of {Line of Life | Wrist | Mount of Luna | Line of Head | Line of Heart} or 'none'
  TERMINATION: exactly one of {Mount of Saturn | Mount of Jupiter | Line of Heart | Line of Head} or 'none'
  PROXIMITY: <touching|medium|distant|n/a> to <landmark or none>
  BRANCHES_TO: landmark(s) any branch is directed toward, or 'none'
```

This is a direct instruction to the LLM to PRODUCE these fields for Fate —
not merely a parser standing ready in case they appear. On the parse side,
`observation_extractor.py`'s `_LINE_HEADER` regex (line ~409) includes
`FATE LINE` in its alternation, and `_RELATIONAL_LINE_ALIAS` (line ~377-381)
explicitly maps `"fate line"` alongside head/heart into the 3 features whose
RELATIONAL block `extract_relational_targets`/`extract_proximity_observations`
actually parse. **Verdict: EMITTED**, both sides, for ORIGIN, TERMINATION,
PROXIMITY, and BRANCHES_TO. (One staleness note: the comment block at
observation_extractor.py lines ~349-358 still calls the whole mechanism
"INERT on the currently-loaded rule set" — that predates S92's `H_027`,
the first *live* relational rule per CLAUDE.md's Locked Decisions; the
comment was not updated when the machinery went live. Not a functional
gap, just a stale docstring, noted for a future housekeeping pass.)

**G2 — TERMINATION landmark legality.** Checked two things in
`data/ontology_registry.json`:
- `attribute_feature_mapping`: `Position`, `Starting_Point`, `Ending_Point`,
  `Proximity`, and `Branching` **all list `"Line of Fate"`** as a valid
  feature (lines 709-801). Attribute-side legality: confirmed.
- `relation_target_registry` (line 1066 on): a flat list of legal landmark
  FEATURE names — this, not `position_values`' `terminating_at_*` token
  suffixes, is what `extract_relational_targets`/`match()`'s `targets` dict
  actually checks membership against. Every landmark this chapter's
  doctrine needs is present: `Line of Life`, `Line of Head`, `Line of Heart`,
  `Mount of Saturn`, `Mount of Jupiter`, `Mount of Luna`, `Wrist`, and
  `Plain of Mars` are all members. **Verdict: REACHABLE** at the
  registry-legality level for every landmark this chapter names.

**The catch, found while applying G1/G2 per-sentence:** the vision prompt's
closed ORIGIN/TERMINATION *menus* for Fate are narrower than the registry.
ORIGIN menu = `{Line of Life, Wrist, Mount of Luna, Line of Head, Line of
Heart}` — covers every origin the chapter actually names, **except**
`Plain of Mars` (¶1106), which is `relation_target_registry`-legal but not
offered as an ORIGIN choice the vision model is ever asked to pick.
TERMINATION menu = `{Mount of Saturn, Mount of Jupiter, Line of Heart, Line
of Head}` — covers Jupiter/Saturn/Heart/Head terminations cleanly, but the
chapter's own general clause "any mount ... other than Saturn" (¶1099)
implies Sun/Mercury/Venus/Luna terminations too, none of which are
menu options. **So G1+G2 passing at the registry/channel level does not
mean every sentence's specific target is reachable** — reachability is
per-target, checked row by row below. Sentences whose target landmark is
inside both closed menus are reclassified `PARKED_RELATION` ->
`AUTHORABLE_NOW`. Sentences whose target landmark is registry-legal but
absent from the closed menu stay `PARKED_RELATION`, with the reason
recorded as a menu-gap, not a missing-channel gap — a materially different,
narrower fix (widen 2 menu strings in `palm_processor.py`, not build a new
mechanism).

`PARKED_BRANCH` rows (Branching/BRANCHES_TO) are **not** reclassified by
this pass even though G1 confirms BRANCHES_TO is also emitted for Fate:
`PALM_PIPELINE.md` Step 3 lists `Branching` (bare count vs. directed) as
one of the four **AMBIGUOUS, human-ruling-required** attribute classes —
auto-routing it here would violate that law. Flagged, not auto-promoted.

---

## SUMMARY — counts per authorability class

| class | count (rows) | sentence_ids |
|---|---|---|
| **AUTHORABLE_NOW** | **17** | F014a, F014b, F015, F016a, F016b, F021a, F021c, F023, F024a, F025a, F026, F028, F029, F031, F032a, F033, F033b |
| PARKED_RELATION | 4 | F020, F025b, F027a, F033c |
| PARKED_BRANCH | 5 | F017a, F017b, F018, F022, F030 |
| SCOPED_OUT (marks/Influence subsystem) | 5 | F034a, F034b, F035a, F035b, F035c |
| DO_NOT_AUTHOR (hand-type-conditioned) | 3 | F005, F008, F010 |
| SCHEMA_GAP (attribute not in ontology) | 1 | F036 |
| ambiguous / not extractable | 5 | F021b, F024b, F027b, F027c, F032b |
| scope | 11 | F001, F003, F004, F006, F007, F009, F011, F012, F013, F036b, F036c |
| **Total rows** | **51** | |

**Distinct base-rule claims among the 17 AUTHORABLE_NOW rows: ~13** — 4 of
the 17 (F014b→F014a's compound partner is its own claim, but F016b, F021c,
F033b are pure consequence-elaboration rows riding on F016a/F021a/F033's
antecedent, not independent claims) are modifier rows that share their base
row's antecedent and don't add a new one; F023 is flagged as a
near-duplicate of F021a (both terminate at Mount of Jupiter) to reconcile
at Step 1, not a distinct claim either.

**Delta vs. the S96 in-chat baseline (~6-7 reachable of 33 operative
statements):** this pass finds roughly **13 distinct reachable claims**
(17 counting elaboration rows) against **51** total doctrinal clauses (a
finer split than S96's 33, since compound sentences are here broken into
their `a`/`b`/`c` conditional clauses). That is a delta of **+6 to +7
distinct claims**, entirely attributable to the G1/G2 finding: the
Starting_Point/Ending_Point relation channel that S96 evidently assumed
was not live for Fate (consistent with the `PARKED_RELATION` category's
own parenthetical, "needs relation channel") **is in fact already wired
and emitting** for Fate line specifically (`_RELATIONAL_LINE_ALIAS`
includes `"fate line"`, confirmed above). Once that channel is credited,
7 origin/termination rows (F014a, F014b, F015, F016a/b, F025a, F026, F028,
F029) that a channel-blind read would file under `PARKED_RELATION` move to
`AUTHORABLE_NOW`. The remaining `PARKED_RELATION` rows (F020, F025b,
F027a, F033c) stay parked for menu-completeness or compound-condition
reasons distinct from "no channel exists."

---

## Full table

| id | verbatim span | pg | role | antecedents (feature/attribute/value or relation_target) | authorability |
|---|---|---|---|---|---|
| F001 | *". . . And what is fate ? / A perfect law that shapes all things for good; ... / . . . And such is fate. — Cheiro." (epigraph poem)* | 101 | scope | — (poetic epigraph, non-analyzable) | n/a |
| F003 | "The line of fate (Plate XIII.), otherwise called the line of destiny, or the Saturnian, is the center upright line on the palm of the hand." | 101 | scope | — (naming/definition) | n/a |
| F004 | "In the consideration of this line the type of hand plays an important part; for instance, the line of fate, even in the most successful hands, is less marked on the elementary, the square, and the spatulate, than on the philosophic, the conic, or the psychic." | 101-102 | scope | — (hand-type framing, sets up F005/F008) | n/a |
| F005 | "These upright lines are more in keeping with the latter hands, and are therefore less important on them; consequently if one sees, as one often will, an apparently very strong line of fate on a conic hand, one must remember that it has not half the importance of a similiar line on a square type as far as worldly success is concerned." | 102 | modifier | Line of Fate / (Depth or Clarity, soft "strong") — modulated by Hand Type | **DO_NOT_AUTHOR** (hand-type-conditioned) |
| F006 | "This point, I am sorry to say, has been completely overlooked by other writers, though it is one of the most significant in this study." | 102 | scope | — (author's meta-aside) | n/a |
| F007 | "It is useless to simply give a map of the hand without clearly explaining this point." | 102 | scope | — (meta) | n/a |
| F008 | "The bewildered student sees this long line of fate marked as a sign of great fortune and success, and naturally concludes that a small line on the square hand means nothing, and that a long one on the conic or psychic means success, fame, and fortune, whereas it has not one quarter the importance of the small line shown on the square." | 102-103 | modifier | Line of Fate / Length=long or short — modulated by Hand Type | **DO_NOT_AUTHOR** (hand-type-conditioned) |
| F009 | "I wish to emphasize this as so many students throw up palmistry in despair through not having this point explained at the start." | 103 | scope | — (meta) | n/a |
| F010 | "The strange and mysterious thing to note is that the possessors of the philosophic, conic, and psychic hands which bear these heavily marked lines are more or less believers in fate, whereas the possessors of the square and spatulate rarely if ever believe in fate at all." | 103 | ambiguous | Hand Type / belief-correlation — not a fortune-reading claim about the subject's life at all | **DO_NOT_AUTHOR** (hand-type-conditioned; also borderline out-of-scope as a belief-correlation aside rather than a reading claim) |
| F011 | "Before the student goes farther I would recommend him, once and for all, to settle this doctrine of fate, either for or against." | 103 | scope | — (author's aside to the reader) | n/a |
| F012 | "The line of fate, properly speaking, relates to all worldly affairs, to our success or failure, to the people who influence our career, whether such influ­ences be beneficial or otherwise, to the barriers and obstacles in our way, and to the ultimate result of our career." | 103 | **scope** | — (chapter topic-framing sentence — LAW: not a rule, exact same class as the Head-line "relates principally to mentality" sentence PALM_PIPELINE.md names by example) | n/a |
| F013 | "The line of fate may rise from the line of life, the wrist, the Mount of Luna, the line of head, or even the line of heart." | 103 | scope | — (origin-menu-setting sentence; no distinct consequence of its own, elaborated by F014a/F014b/F016a/F028/F029) | n/a |
| F014a | "If the fate-line rise from the line of life and from that point on is strong, success and riches will be won by personal merit;" | 103 | base_rule | Line of Fate / Starting_Point / relation_target=Line of Life; + Line of Fate / Depth or Clarity, soft "strong" (whole-sentence LLM judgment) | **AUTHORABLE_NOW** — Starting_Point EMITTED+REACHABLE (G1/G2, ORIGIN menu includes Line of Life); "strong" is an existing soft quality primitive |
| F014b | "but if the line be marked low down near the wrist and tied down, as it were, by the side of the life-line, it tells that the early portion of the subject's life will be sacrificed to the wishes of parents or relatives (g-g, Plate XX.)." | 103 | base_rule | Line of Fate / Starting_Point / relation_target=Wrist; + Line of Fate / Proximity / relation_target=Line of Life, degree=touching or medium | **AUTHORABLE_NOW** — Wrist is an ORIGIN menu option; Proximity to Line of Life is emitted (PROXIMITY subfield) |
| F015 | "When the line of fate rises from the wrist and proceeds straight up the hand to its destination on the Mount of Saturn, it is a sign of extreme good fortune and success." | 103 | base_rule | Line of Fate / Starting_Point / relation_target=Wrist; + Line of Fate / Slope=straight (closed 4-choice SLOPE field, not free text); + Line of Fate / Ending_Point / relation_target=Mount of Saturn | **AUTHORABLE_NOW** — all three antecedents individually reachable (Wrist in ORIGIN menu, straight in the closed SLOPE menu, Mount of Saturn in TERMINATION menu) |
| F016a | "Rising from the Mount of Luna, fate and success will be more or less dependent on the fancy and caprice of other people." | 103 | base_rule | Line of Fate / Starting_Point / relation_target=Mount of Luna | **AUTHORABLE_NOW** — Mount of Luna is an ORIGIN menu option |
| F016b | "This is very often found in the case of public favorites." | 103 | modifier | (same antecedent as F016a, consequence elaboration only) | **AUTHORABLE_NOW** (tied to F016a — not an independent claim) |
| F017a | "If the line of fate be straight and a branch run in and join it from the Mount of Luna, it is somewhat similar in its meaning—it signifies that the strong influence of some other person out of fancy or caprice will assist the subject in his or her career." | 103 | base_rule | Line of Fate / Slope=straight; + Line of Fate / Branching / relation_target=Mount of Luna | **PARKED_BRANCH** (Branching antecedent — human ruling required per PALM_PIPELINE Step 3's AMBIGUOUS class; not auto-reclassified despite BRANCHES_TO being confirmed EMITTED under G1) |
| F017b | "On a woman's hand, if this ray-line from Luna travel on afterward by the side of the line of fate, it denotes a wealthy marriage or influence which accompanies and assists her (h—h, Plate XX.)." | 103 | base_rule | Line of Fate / Branching / relation_target=Mount of Luna; + Line of Fate / Proximity / relation_target=self (running parallel) | **PARKED_BRANCH** — plus a SECOND, independent blocker: no sex/gender-of-subject attribute exists anywhere in the ontology ("on a woman's hand" is unrepresentable regardless of the Branching ruling) |
| F018 | "If the line of fate in its course to the Mount of Saturn send offshoots to any other mount, it denotes that the qualities of that particular mount will dominate the life." | 104 | base_rule | Line of Fate / Branching / relation_target=(wildcard, any mount) | **PARKED_BRANCH** — additionally the target is an unbound wildcard ("any other mount"), not a single named landmark, a second-order authoring complexity once Branching itself is unparked |
| F020 | "If the line of fate itself should go to any mount or portion of the hand other than the Mount of Saturn, it foretells great success in that particular direction, according to the characteristics of the mount." | 104 | base_rule | Line of Fate / Ending_Point / relation_target=(wildcard: any mount except Saturn) | **PARKED_RELATION** — NOT a missing-channel gap (channel is live, G1/G2 pass); it is a **closed-menu-completeness gap**: the FATE LINE TERMINATION menu in `palm_processor.py` only offers `{Mount of Saturn, Mount of Jupiter, Line of Heart, Line of Head}` — Sun/Mercury/Venus/Luna terminations, which this general clause needs, are not menu options even though those mounts are `relation_target_registry`-legal |
| F021a | "If the line of fate ascend to the center of the Mount of Jupiter, unusual distinction and power will come into the subject's life." | 104 | base_rule | Line of Fate / Ending_Point / relation_target=Mount of Jupiter | **AUTHORABLE_NOW** — Mount of Jupiter is inside the closed TERMINATION menu |
| F021b | "It also relates to character." | 104 | ambiguous | — (too vague; no extractable antecedent or consequence) | n/a — not authorable, no claim to extract |
| F021c | "Such people are born to climb up higher than their fellows through their enormous energy, ambition, and determination." | 104 | modifier | (same antecedent as F021a, consequence elaboration only) | **AUTHORABLE_NOW** (tied to F021a) |
| F022 | "If the line of fate should at any point throw a branch in that direction, namely, toward Jupiter, it shows more than usual success at that particular stage of life." | 104 | base_rule | Line of Fate / Branching / relation_target=Mount of Jupiter | **PARKED_BRANCH** |
| F023 | "If the line of fate terminate by crossing its own mount and reaching Jupiter, success will be so great in the end that it will go far toward satisfy­ing even the ambition of such a subject." | 104 | base_rule | Line of Fate / Ending_Point / relation_target=Mount of Jupiter (the "crossing its own mount" clause first is not separately encodable — no compound/two-hop Position value exists) | **AUTHORABLE_NOW**, flagged **near-duplicate of F021a** — same Jupiter-termination primitive; the "crossing its own mount" nuance would be dropped or folded into `claim` prose only, reconcile the two at Step 1 rather than double-author |
| F024a | "When the line runs beyond the palm, cutting into the finger of Saturn, it is not a good sign, as everything will go too far." | 104 | base_rule | Line of Fate / Length=cutting_into_finger_of_Saturn (registry token exists verbatim in `length_values`; Length is unbound so the flat pool applies, and Length is attribute-legal for Line of Fate) | **AUTHORABLE_NOW**, **lower confidence flag**: the FATE LINE prompt block only asks for "same attributes" generic free text (depth/width/length/direction/breaks-chains-forks-islands), never explicitly solicits this specific extreme-length phrasing — registry-legal and attribute-legal, but live-phrasing match is unverified; recommend confirming at Step 2 (`vocab_reachability_scan.py`) before authoring, not assumed here |
| F024b | "For instance, if such an in­dividual be a leader, his subjects will some day go beyond his wishes and power, and will most probably turn and attack their commander." | 104 | ambiguous | — (nested hypothetical illustration, no hand-observable antecedent) | n/a — not authorable |
| F025a | "When the line of fate is abruptly stopped by the line of heart, success will be ruined through the affections;" | 104 | base_rule | Line of Fate / Ending_Point / relation_target=Line of Heart | **AUTHORABLE_NOW** — Line of Heart is inside the closed TERMINATION menu |
| F025b | "when, however, it joins the line of heart and they together ascend Jupiter, the subject will have his or her high­est ambition gratified through the affections {h-h, Plate XIX.)." | 104 | base_rule | Line of Fate / Ending_Point / relation_target=Line of Heart, AND both lines continue to Mount of Jupiter (compound cross-line convergence) | **PARKED_RELATION** — each individual landmark (Line of Heart, Mount of Jupiter) is reachable, but the JOINT "two lines converge and continue together to a third landmark" claim exceeds a single antecedent; needs a comparator_feature/multi-hop relation shape not in the current schema |
| F026 | "When stopped by the line of head, it foretells that success will be thwarted by some stupidity or blunder of the head." | 104 | base_rule | Line of Fate / Ending_Point / relation_target=Line of Head | **AUTHORABLE_NOW** — Line of Head is inside the closed TERMINATION menu |
| F027a | "If the line of fate does not rise until late in the Plain of Mars, it denotes a very difficult, hard, and troubled life;" | 104 | base_rule | Line of Fate / Starting_Point / relation_target=Plain of Mars | **PARKED_RELATION** — `Plain of Mars` IS `relation_target_registry`-legal, but is **absent from the FATE LINE ORIGIN closed menu** (`{Line of Life, Wrist, Mount of Luna, Line of Head, Line of Heart}`) — same menu-completeness gap class as F020, on the origin side instead of termination |
| F027b | "but if it goes on well up the hand, all difficulties will be surmounted, and once over the first half of the life all the rest will be smooth." | 104 | ambiguous | Line of Fate / Position (height-vs-timing) | **AMBIGUOUS** — `Position` height-vs-landmark is one of PALM_PIPELINE Step 3's named ambiguous-routing items; flag for Human Ruling #2, do not auto-route |
| F027c | "Such success comes from the subject's own energy, per­severance, and determination." | 104 | modifier | (tied to F027b) | ambiguous (tied) |
| F028 | "If the line of fate rise from the line of head, and that line be well marked, then success will be won late in life, after a hard struggle and through the subject's talents." | 104 | base_rule | Line of Fate / Starting_Point / relation_target=Line of Head; + comparator_feature: Line of Head / Depth or Clarity, soft "well marked" | **AUTHORABLE_NOW** (mixed: hard Starting_Point relation on Fate + comparator_feature soft quality on Head, schema supports `comparator_feature`) |
| F029 | "When it rises from the line of heart extremely late in life, after a difficult struggle success will be won." | 104-105 | base_rule | Line of Fate / Starting_Point / relation_target=Line of Heart | **AUTHORABLE_NOW** — Line of Heart is an ORIGIN menu option; "extremely late in life" timing folds into claim prose, not a separate blocking antecedent |
| F030 | "When the line rises with one branch from the base of Luna, the other from Venus, the subject's destiny will sway between imagination on the one hand and love and passion on the other (m-m, Plate XXI.)." | 105 | base_rule | Line of Fate / Branching / relation_target=Mount of Luna AND Mount of Venus (dual-branch split) | **PARKED_BRANCH** — dual-target branching, same multi-value need as the S96 cheirognomy OR-match work; flag as a candidate for that mechanism once Branching is unparked |
| F031 | "When broken and irregular, the career will be uncertain; the ups and downs of success and failm*e full of light and shadow." *(OCR: "failm*e" = "failure")* | 105 | base_rule | Line of Fate / Continuity=broken (+ irregular) | **AUTHORABLE_NOW** — single feature/attribute/value, no relation_target, Continuity is unbound (flat pool includes "broken"/"irregular") and attribute-legal for Line of Fate; same primitive already fireable for Head/Heart per `reconciliation_head.md` |
| F032a | "When there is a break in the line, it is a sure sign of misfortune and loss;" | 105 | base_rule | Line of Fate / Continuity=broken | **AUTHORABLE_NOW**, flagged **near-duplicate of F031** (both key Continuity=broken with a different consequence gloss) — reconcile at Step 1 |
| F032b | "but if the second portion of the line begin before the other leaves off, it de­notes a complete change in life, and if very decided it will mean a change more in accordance with the subject's own wishes in the way of position and success (a-a, Plate XXI.)." | 105 | ambiguous | Line of Fate / Continuity (finer break-subtype: overlapping resumption vs. plain gap) | **AMBIGUOUS — value-granularity gap**, same class as the Head-line "very sloping" gap in `reconciliation_head.md` row 4: no `continuity_value` token distinguishes an overlapping-resumption break from a plain gap-break |
| F033 | "A double or sister fate-line is an excellent sign." | 105 | base_rule | Line of Fate / Continuity=double | **AUTHORABLE_NOW** — single feature/attribute/value, "double" is a legal `continuity_value`, no relation_target |
| F033b | "It denotes two distinct careers which the subject will follow." | 105 | modifier | (tied to F033) | **AUTHORABLE_NOW** (tied to F033) |
| F033c | "This is much more important if they go to different mounts." | 105 | modifier | Line of Fate / Ending_Point / relation_target=(two distinct mounts, one per branch) | **PARKED_RELATION** — upgrades F033's base claim with a dual-termination compound condition (each of the two sister-lines terminating on a *different* mount), exceeding a single antecedent |
| F034a | "A square on the line of fate protects the subject from loss through money, business, or financial matters." | 105 | base_rule | Square (mark) | **SCOPED_OUT** — marks/signs, per S96 chapter scope-out (already covered by `unauthorable_register.json`'s marks-family decision) |
| F034b | "A square touching the line in the Plain of Mars (h, Plate XXI.) foretells danger from accident in relation to home life if on the side of the fate-line next the line of life; from accident in travel if on the side of the fate-line next the Mount of Luna." | 105 | base_rule | Square (mark) | **SCOPED_OUT** — marks/signs |
| F035a | "A cross is a sign of trouble and follows the same rules as the square," | 105 | base_rule | Cross (mark) | **SCOPED_OUT** — marks/signs |
| F035b | "but an island in the line of fate is a mark of misfortune, loss, and adversity (d, Plate XXI.)." | 105 | base_rule | Island (mark) | **SCOPED_OUT** — marks/signs |
| F035c | "It is sometimes marked with the line of influence from Luna, and in such a case means loss and misfortune caused by the influence, be it marriage or otherwise, which affects the life at that date (c, Plate XXI.)." | 105 | base_rule | Line of Influence (subsystem) | **SCOPED_OUT** — whole Line of Influence / Hindu ray subsystem, per S96's p136-139 chapter-wide scope-out (`unauthorable_register.json`'s `line_life` entry frames it as "entire ... subsystem", applied here too) |
| F036 | "People without any sign of a line of fate are often very successful, but they lead more a vegetable kind of existence." | 105 | base_rule | Line of Fate / Presence=absent | **SCHEMA_GAP** — `Presence` is used by `palm_select.py`'s `_HARD_ATTRS` and by `HL_015` (`schema_flags: ["PRESENCE: new attribute ... not in current ontology"]`), but is **not present** in `ontology_registry.json`'s `line_attributes` list at all; same unresolved gap as `HL_015`, not specific to Fate |
| F036b | "They eat, drink, and sleep, but I do not think we can really call them happy, for they cannot feel acutely, and to feel happiness we must also feel the reverse." | 105 | scope | — (rhetorical elaboration on F036, no new antecedent) | n/a |
| F036c | "Sunshine and shadow, smiles and tears comprise the sum total of our lives." | 105 | scope | — (poetic closing) | n/a |

**LAW check:** no `base_rule`/`modifier` row above cites a `scope`-tagged
span; F012/F013 (the chapter's own topic-framing and origin-menu-setting
sentences) carry no antecedents and are not cited by any authorability
row. Every clause in the chapter (excluding page furniture and the two
structural headings) is accounted for in one of the 51 rows above.
