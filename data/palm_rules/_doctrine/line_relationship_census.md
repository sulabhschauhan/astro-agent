# Line-Relationship Requirement Census (all 9 line chapters + mounts)

**Status: REQUIREMENTS ONLY.** No code, rule, prompt, or registry change accompanies this document. Goal: enumerate every distinct line-to-line (and line-to-mount) RELATIONSHIP TYPE the doctrine across the whole book actually demands, as design input for a future vision-capture redesign — not just "convergence" (the one type Pattern D built).

**Method:** built on top of `_doctrine/relation_census.md` (a prior A/B/C/D pattern-tag scan of the same 9 chapters), re-read against the raw corpus (`data/cheiro/cheiro_clean_v1.json`, 310 chunks) with a different organizing axis — RELATIONSHIP TYPE/VERB, not A/B/C/D pattern code — and extended with direct verification of every quote reused here (spot-checks below found zero transcription errors in `relation_census.md`; a handful of exact `page_ref` values it left as book-page citations only are resolved to corpus `page_ref` here). Doctrine already fully authored (Fate: `doctrine_fate.md` / `palm_rules_fate_line_v1.json`) is cross-referenced, not re-derived from scratch. All page numbers below are the corpus's own `page_ref` field (verified directly against `cheiro_clean_v1.json`), NOT the book's printed page number (noted in parens where relevant, per the two-numbering-scheme confusion already documented in this project's S98 session history).

**Current-capture baseline used throughout:** `data/ontology_registry.json`'s `relation_types` (`Starting_Point`/`Position`/`Branching` = directional, `Proximity` = proximity, `Convergence`/`Convergence_Location` = symmetric), `relation_cardinality` (`Convergence` = multi, everything else single), `convergence_lines` (`Life, Head, Heart, Fate, Health`); `agent/palm_processor.py`'s live prompt, which gives LIFE/HEAD/HEART/FATE their own labeled blocks (LIFE: CONVERGENCE only; HEAD/HEART: SLOPE/ORIGIN/TERMINATION/PROXIMITY/BRANCHES_TO/CONVERGENCE; FATE: same plus BREAK TYPE/LENGTH EXTENT/CONVERGENCE_LOCATION) — Sun/Health/Marriage collapse into one free-text `OTHER LINES:` line with zero structured fields; Mars and Intuition/Via Lasciva are not mentioned in the prompt at all.

---

## Relationship types

### 1. JOIN / MEET (symmetric convergence)

**Definition:** two or more lines' courses come together at a shared point ("joined together," "meet," "unite"). The corpus treats this as reciprocal — "A and B meet" carries no privileged actor, unlike CUT (§4) or STOPPED-BY (§2), where one line acts on another.

**Instances** (all independently spot-verified against the corpus this session):

| # | Chapter | page_ref (book p.) | Verbatim | Lines/mounts |
|---|---|---|---|---|
| 1 | Life | 134→135 (80-81) | "When the lines of life, head, and heart are all joined together at the commencement (a-a, Plate XVIII.), it is a very unfortunate sign, denoting that the subject, through a defect in temperament, rushes blindly into danger and catastrophe." | Life+Head+Heart (3-way) |
| 2 | Heart | 160 (100) | "When the lines of heart, head and life are very much joined together, it is an evil sign; in all matters of affection such a subject would stick at nothing to obtain his or her desires." | Heart+Head+Life (3-way; same doctrine as #1, restated) |
| 3 | Head | 154 (96) | "In such cases the line of head leaves its proper place on the hand and rises and **takes possession of** the line of heart... If the head and heart **meet** under Saturn, it will occur before he is twenty-five; between Saturn and the Sun, before thirty-five; under the Mount of the Sun, before forty-five." | Head+Heart, location-gated (see §6) |
| 4 | Health | 171 (109) | "...if the hepatica is as strongly marked as the line of life itself, their meeting at any point will be the point of death." | Health+Life (2-way; restates Life ch.'s own p.139 forward-reference) |
| 5 | Life | 139 (85) | "...when it is of equal strength with that of life, where these lines meet will be the point of death, even though it be years in advance..." | Life+Health (same doctrine as #4, Life ch.'s own statement, forward-referencing the Health chapter) |
| 6 | Fate | 164 (104) | "...when, however, it joins the line of heart and they together ascend Jupiter, the subject will have his or her highest ambition gratified through the affections" | Fate+Heart (already authored: `FT_016`/F025b) |

**Directionality:** symmetric (confirmed by "joined together," "meet," "meeting" — no actor/recipient asymmetry in the verb itself). #3's "takes possession of" is a DIFFERENT, directional verb describing the SAME event from a dominance angle — see §3.

**Cardinality:** YES, n-way — #1/#2 are a genuine 3-way join (life+head+heart), independently stated in two chapters. This is the doctrine `L_026` was authored against (Pattern D, `palm_rules_life_line_v1.json`).

**Location sensitivity:** YES for #3 (the SPECIFIC mount the join happens under changes the predicted age: Saturn <25, Saturn-Sun 25-35, Sun <45) and for #6 (Fate+Heart joining AND ascending to Jupiter specifically gates the "highest ambition" claim — `Convergence_Location`). NOT explicitly location-gated for #1/#2/#4/#5 (only "at the commencement" / "at any point" — timing-flavored, not mount-flavored).

**Current capture:** `Convergence` (symmetric, multi-cardinality) — this is the ONE relationship type Pattern D fully built (registry → engine → extractor → prompt → `L_026` authored and fires end-to-end on synthetic input, per S98's Aug 2026 arc). #6 (`Convergence_Location`) is captured too, but ONLY as a single scalar (F025b-shaped); #1/#2's 3-way case has no location component to lose. #3's location-gated 3-tier mount claim (Saturn/Saturn-Sun/Sun) is **UNCAPTURED** — `Convergence_Location`'s menu is `{Mount of Jupiter}` only (Fate-specific), not the 3-mount set Head's doctrine needs, and Head has no `CONVERGENCE_LOCATION` field at all in the prompt.

**Emitter gap:** Health has no vision block (§ below, all types) — #4/#5's doctrine literally cannot be reported from Health's own "side," only inferred if some OTHER line's block happens to name Health as a convergence partner (which the current prompt does support, since `convergence_lines` includes Health as a target).

---

### 2. STOPPED-BY (directional halt, negative-outcome framing)

**Definition:** line A's forward course is abruptly terminated/blocked AT line B — narrated from A's own perspective as an obstruction, always paired with a negative-outcome claim, and used in the SAME breath as JOIN (§1) to draw a positive/negative contrast at the identical physical location.

**Instances:**

| # | Chapter | page_ref (book p.) | Verbatim | Lines |
|---|---|---|---|---|
| 1 | Fate | 164 (104) | "When the line of fate is abruptly **stopped by** the line of heart, success will be ruined through the affections; when, however, it joins the line of heart and they together ascend Jupiter, the subject will have his or her highest ambition gratified through the affections." | Fate stopped-by Heart (negative) vs Fate joins Heart (positive, §1#6) |
| 2 | Fate | 164 (104) | "When **stopped by** the line of head, it foretells that success will be thwarted by some stupidity or blunder of the head." | Fate stopped-by Head |

**Directionality:** directional — the ACTOR (line being stopped) is grammatically distinct from the OBSTACLE (the line doing the stopping); "Fate stopped by Heart" is not interchangeable with "Heart stopped by Fate."

**Cardinality:** no n-way instance found; always one line stopped by one other line.

**Location sensitivity:** the doctrine's CLAIM is gated by WHICH line does the stopping (Heart → ruined affections; Head → thwarted by stupidity), not by a third-party mount location — so location-sensitivity here is really "which line," captured by the `relation_target` slot on the typed `stopped_by` antecedent (see below).

**Current capture: AUTHORED-AND-MIGRATED-TO-TYPED (S112).** `FT_007` (instance #1, Fate stopped-by Heart, doctrine_sentence_ids `F025a`) and `FT_008` (instance #2, Fate stopped-by Head, `F026`) both exist in `palm_rules_fate_line_v1.json`, `verified: true`. **CORRECTION to this file's own prior text** (this paragraph previously said "UNCAPTURED... no such rule exists" — that was stale/wrong: FT_007/FT_008 were already authored, at S97, before this census was written, via the OLD scalar `Position`/`TERMINATION` landmark antecedent — the exact doctrinally-ambiguous shape this paragraph correctly warned against (a `TERMINATION → Line of Heart` report is ambiguous between "stopped" (bad, this doctrine) and "joined and continued" (good, `FT_016`)). S111 caught this contradiction between the census text and the live corpus and stopped rather than silently duplicating coverage; S112 resolved it by MIGRATING FT_007/FT_008 in place (same rule_ids, same claims/source_quotes/doctrine_sentence_ids/verified status) onto the typed `stopped_by` verb token (via free-verb CONTACTS + `contact_mapper`, the same disambiguating mechanism `FT_016` itself uses for its own antecedent) instead of retiring and replacing them. A bare landmark report with no `stopped_by` verb now leaves both rules honestly silent — the false-positive this paragraph flagged is closed. See each rule's own `S112 MIGRATION` schema_flag for the full mechanics. LOWER-CONFIDENCE, unchanged from before: live `stopped_by`-verb emission on a real halted-fate-line hand is still untested (no test hand exhibits this geometry) -- fixture-verified only.

**Emitter gap:** none specific to this type (Fate/Head/Heart all have blocks) — the gap is purely in the RELATIONSHIP-TYPE vocabulary, not in which lines can speak.

---

### 3. TAKES POSSESSION OF / OVERTAKES (directional dominance)

**Definition:** one line physically invades and displaces another's normal territory ("leaves its proper place... and rises and takes possession of... and sometimes even passes beyond it") — stronger than a simple join; implies A subsuming/overpowering B, not a neutral meeting of equals.

**Instance:**

| # | Chapter | page_ref (book p.) | Verbatim | Lines |
|---|---|---|---|---|
| 1 | Head | 154 (96) | "In such cases the line of head leaves its proper place on the hand and rises and **takes possession of** the line of heart, and sometimes even passes beyond it." | Head overtakes Heart |

Same sentence continues into §1#3's location-gated "meet" framing — this is the SAME doctrine instance narrated with two different verbs in two consecutive sentences (overtake, then meet-at-location), an internal ambiguity worth flagging on its own (see Open Questions).

**Directionality:** strongly directional — Head is the actor, Heart is passive/displaced. Not found elsewhere in the corpus (a one-off, but a doctrinally rich one: it's the basis of the book's own "murderous propensities" chapter section).

**Cardinality:** 2-way only, no n-way instance.

**Location sensitivity:** the CONTINUATION into location-gated "meet under Saturn/Sun" (§1#3) makes the compound doctrine location-sensitive, but "takes possession of" itself, read alone, is not.

**Current capture: UNCAPTURED.** No relational attribute distinguishes "overtook/displaced" from a neutral join or a plain termination; even if wired as a `Convergence` instance, it would lose the dominance/displacement semantics entirely — a directional flag or a distinct value, not the existing symmetric attribute, would be needed.

**Emitter gap:** none (Head and Heart both have blocks).

---

### 4. CUT / CROSS (directional, full intersection — location-bearing)

**Definition:** line A's course physically intersects and severs line B's course. The corpus's OWN explicit distinction (p.137/book p.83, quoted in full below) establishes CUT as the load-bearing, LOCATION-GIVING event, contrasted against mere TOUCH (§5).

**The anchor passage** (page_ref 137, book p.83) — the exact text the task named:
> "When they reach and cut the line of heart (g-g, Plate XVI.), they denote interference in our closest affections, and here **the date of such interference is given where the line cuts the life-line, and not where it touches the line of heart.**"

This single sentence is the corpus's OWN statement of the CUT-vs-TOUCH distinction: even when a foreign ray-line touches TWO lines (life AND heart) in the same clause, only the CUT location (against the ray-line's home reference, the life-line) is doctrinally load-bearing for timing; the TOUCH location (against heart) is not.

**Instances** (all page_ref 136-138, book pp.82-84 — the Hindu ray-line/Line of Influence subsystem, Life chapter; scoped OUT of this project's build per `unauthorable_register.json`'s `line_life` entry and CLAUDE.md's S96 lock, but catalogued here in full per this census's own "enumerate every relationship type, in-scope or not" mandate):

| # | page_ref | Verbatim | Lines |
|---|---|---|---|
| 1 | 136 (82) | "a little line **cutting** the life-line rises from the Plain of Mars" | (unnamed ray-line) cuts Life |
| 2 | 136 (82) | "all those rising in the opposite direction and **cutting** the life-line show worries and obstacles caused by the opposition and interference of others" | ray-line cuts Life |
| 3 | 136 (82) | "When they **cut** the l[i]ne of life only... they denote the interference of relatives" | ray-line cuts Life (Life only) |
| 4 | 136-137 (82-83) | "When they **cross** the life-line and **attack** the l[i]ne of fate... where they **cut** the fate-line the point of junction gives the date" | ray-line cuts/crosses Life AND Fate (dual-target, see §7) |
| 5 | 137 (83) | anchor passage above — ray-line **cuts** Heart (location-bearing) vs **touches** Heart is explicitly NOT the anchor passage's own framing; re-reading precisely: it **reaches and cuts** the Heart line itself, with the DATE keyed to where it cuts the LIFE-line, not where it touches Heart | ray-line cuts Heart; date keyed to Life |
| 6 | 137 (83) | "When they **cut and break** the l[i]ne of sun... they denote that others will interfere and spoil our position in life... the mischief will be caused by scandal or disgrace at the point of junction" | ray-line cuts Sun (location-bearing: "at the point of junction") |

**Also in-scope (Marriage chapter, NOT the Hindu subsystem — genuinely unbuilt, not scoped out):**

| # | page_ref (book p.) | Verbatim | Lines |
|---|---|---|---|
| 7 | 181 (117) | "When, on the contrary, it goes down toward and **cuts** the line of sun, the person on whose hand it appears will lose position through marriage." | Marriage line cuts Sun |
| 8 | 181 (117) | "When a deep line from the top of the mount grows downward and **cuts** the line of marriage, there will be a great obstacle and opposition to such marriage." | (unnamed mount-line) cuts Marriage |

**Directionality:** strongly directional — grammatically, one line always does the cutting, the other is cut. "X cuts Y" ≠ "Y cuts X" (no instance found where this is treated symmetrically).

**Cardinality:** instance #4 shows a SINGLE ray-line cutting/crossing TWO named lines (Life then Fate) — n-way capable in the sense of one actor against multiple targets (see also §7, dual-target).

**Location sensitivity:** YES, explicitly and repeatedly — instance #5 (the anchor) states outright that WHERE the cut happens (against the home line) gives the date, and instance #6 says "at the point of junction" gives the scandal's location. This is the single clearest location-sensitive relationship type in the whole corpus.

**Current capture: UNCAPTURED entirely.** No relational attribute in `relation_types` supports a "line A cuts line B [at location L]" shape. `Position`/`Starting_Point` capture ORIGIN/TERMINATION only (the line's own two endpoints), not a mid-course intersection point with a foreign line. Instances #7/#8 (Marriage, genuinely in-scope, NOT part of the scoped-out Hindu subsystem) are real, currently-unbuildable doctrine.

**Emitter gap:** Marriage has no vision block at all (folded into the free-text `OTHER LINES:` line) — instances #7/#8 are doubly uncapturable: no relationship-type field exists, AND the emitting line (Marriage) can't structurally report anything about itself even if one did.

---

### 5. TOUCH / REACH (directional, weaker contact — non-location-bearing in the anchor passage)

**Definition:** a lesser form of contact than CUT — approach or graze without a full severing intersection. The anchor passage (§4) explicitly marks TOUCH as the non-load-bearing member of the CUT/TOUCH pair for timing purposes. REACH appears as an even milder variant, explicitly flagged as ambiguous by `relation_census.md`'s own prior pass.

**Instances:**

| # | page_ref (book p.) | Verbatim | Lines |
|---|---|---|---|
| 1 | 137 (83) | "...and not where it **touches** the line of heart" (anchor passage, §4) | ray-line touches Heart (non-bearing) |
| 2 | 137 (83) | "When the line crosses the hand and **touches** the line of marriage... it signifies divorce" | ray-line touches Marriage (HERE touch IS the primary, load-bearing verb for a real claim — divorce) |
| 3 | 137-138 (83-84) | "if the ray-line rise on the Mount of Mars... and lower down **touch or attack** the life-line in any way, it denotes... some unfavorable attachment" | ray-line touches/attacks Life |
| 4 | 136 (82) | "When they **reach** the line of head... they indicate persons who will influence our thoughts and interfere with our ideas" | ray-line reaches Head (`relation_census.md`'s own flag: "ambiguous... could read as plain TERMINATION") |
| 5 | 179 (115, Marriage) | "When there is a fine line running parallel with and almost **touching** the [line]..." | (context cut off at page boundary in my read — PROXIMITY-flavored, not catalogued further here) |

**Directionality:** directional, same actor/recipient asymmetry as CUT.

**Cardinality:** no clean n-way instance; #3 shows one verb pair (touch-or-attack) applied to one target.

**Location sensitivity:** explicitly NO for instance #1 (the anchor passage's whole point). YES for instance #2 (touching Marriage's line at all is itself the full claim — divorce — regardless of where; so "location" here collapses to "which line is touched," already true of every relationship type). Ambiguous for #4.

**Current capture: partially, indirectly, and imprecisely.** `Proximity`'s `touching` degree value exists in today's schema — but it is defined and scoped for the THREE in-scope lines' (Head/Heart/Fate) relationship to a landmark from THEIR OWN vision block (e.g. `PROXIMITY: touching to Line of Life`), not for an arbitrary foreign line "touching" another in the sense these doctrine instances use. The vocabulary word coincidentally matches, but the doctrine (a Hindu ray-line touching Marriage/Life/Head) is a structurally different relationship (an unnamed, unmodeled third line acting on a named one) that today's `Proximity` schema was never built to represent.

**Emitter gap:** Marriage (instance #2) has no vision block; the "ray-line" itself (instances #1/#3/#4) is not a feature this project's ontology models at all (scoped out per S96) — it cannot emit its OWN observations regardless of relationship-type machinery.

---

### 6. BRANCH-IN / INCOMING (directional, reverse of BRANCHES_TO)

**Definition:** a branch line arrives INTO the line being described, originating FROM another named line or mount — the mirror image of `BRANCHES_TO` (which only models a branch leaving the described line and heading TO a target).

**Instances:**

| # | Chapter | page_ref (book p.) | Verbatim | Direction |
|---|---|---|---|---|
| 1 | Heart | 160 (100) | "Fine lines rising up to the line of heart **from** the line of head denote those who influence our thoughts in affairs of the heart" | Head → Heart (incoming, told from Heart's chapter) |
| 2 | Fate | 163 (103) | "If the line of fate be straight and a branch run in and join it **from** the Mount of Luna, it is somewhat similar in its meaning — it signifies that the strong influence of some other person..." | Luna → Fate (incoming; this is `FT_P04`/F017a, already parked) |
| 3 | Marriage | 179 (115) | "A wealthy union is shown by a strong, well-marked line **from** the side of the line of fate next Luna... running up and joining the line of fate..." | Luna-adjacent → Fate (incoming, told from Marriage's chapter — same underlying doctrine as #2, restated) |
| 4 | Marriage | 180 (116) | "When... the line of influence rises first straight on the Mount of Luna and then runs up and into the fate-line, the marriage will be more the capricious fancy than real affection." | Luna → Fate (incoming, third restatement, different consequence) |

**Directionality:** always directional, arrival-into framing (source line/mount → described line). `relation_census.md`'s own note on instance #1: "the reverse of the head-line's own BRANCHES_TO framing of essentially the same doctrine" (Head chapter states the identical fact as an outgoing branch — see cross-reference below).

**Cardinality:** 2-way (one source, one destination) in every instance found; no n-way incoming case.

**Location sensitivity:** no — the doctrine's claim depends on WHICH source line/mount the branch comes from, not on a separate location gate.

**Current capture: UNCAPTURED — the clearest structural mis-route in this census.** `Branching`/`BRANCHES_TO` is declared `directional` and `single`-cardinality in the registry, and the vision prompt's own wording is explicitly outgoing-only: *"BRANCHES_TO: landmark(s) any branch is directed toward, or 'none'"* — there is no vision field, registry attribute, or prompt instruction for an INCOMING branch at all. This is exactly the gap `relation_census.md`'s own build-sizing section flagged as "the narrowest fix conceptually — it only requires flipping BRANCHES_TO's directionality... or adding an inverse field" and noted it blocks `FT_P04` specifically. Instance #1 is a doubly interesting case: the SAME physical doctrine is stated ONCE as an outgoing branch (Head's own chapter, EXPRESSIBLE today via `BRANCHES_TO`) and ONCE as an incoming branch (Heart's chapter, restating identically but from the receiving line's vantage) — meaning the doctrine IS capturable today, but only if the emitting line happens to be the SOURCE, never the destination; a vision call that only sees the Heart-line block and never asks Head about its branches would miss it entirely under the current per-line framing.

**Emitter gap:** none for #1/#2 (Head, Heart, Fate all have blocks); #3/#4 restate the SAME Fate-ward doctrine from Marriage's perspective, and Marriage has no block at all — moot here since #2 already captures the doctrine from Fate's side (once BRANCH-IN exists).

---

### 7. DUAL-TARGET BRANCH (one line forks to 2+ simultaneous named targets)

**Definition:** a single branching event splits into two (or more) distinct named destinations at once, each named target independently gating a different claim — distinct from BRANCHES_TO's current single-scalar-target shape.

**Instances:**

| # | Chapter | page_ref (book p.) | Verbatim | Targets |
|---|---|---|---|---|
| 1 | Heart | 160 (100) | "When the line of heart forks, with one branch resting on Jupiter, the other between the first and second fingers, it is a sign of a happy, tranquil nature... but when the fork is so wide that one branch rests on Jupiter, the other on Saturn, it then denotes a very uncertain disposition." | Jupiter + (Junction of First/Second Fingers) → happy/tranquil; Jupiter + Saturn → uncertain (two variants) |
| 2 | Fate | 164-165 (104-105) | "When the line rises with one branch from the base of Luna, the other from Venus, the subject's destiny will sway between imagination on the one hand and love and passion on the other." | Luna + Venus (this is `FT_P03`/F030, already parked; note this is dual-ORIGIN, see §8, not dual-BRANCH — a fork happening at the START of the line, not partway along it) |
| 3 | Health | ~172 (110) | "When heavily marked, joining the lines of heart and head, and not found elsewhere, it threatens brain-fever." | Heart + Head simultaneously (one line, hepatica, joining BOTH at once — a dual-target JOIN, not a branch/fork; a genuinely different verb (join) applied to the dual-target shape) |

**Directionality:** the FORKING line is the actor in all 3 instances; the two named targets are passive destinations. Instance #3 is technically a dual-target JOIN (§1) rather than a dual-target BRANCH — flagged here as a cross-cutting case since the CARDINALITY question (can 2 targets matter simultaneously) is identical regardless of which verb (fork vs join) carries it.

**Cardinality:** definitionally n-way (2 simultaneous targets in every instance; no 3+ target instance found for this specific fork/branch shape, though §1's own JOIN type already has a proven 3-way case).

**Location sensitivity:** YES, centrally — instance #1's whole doctrine IS which pair of targets (Jupiter+finger-junction vs Jupiter+Saturn) that determines happy-vs-uncertain; instance #2 similarly keys the ENTIRE claim on the specific pair (Luna+Venus).

**Current capture: UNCAPTURED.** `Branching` is `single`-cardinality in the registry (unlike `Convergence`, which Pattern D made `multi`) — a fork to 2 simultaneous targets cannot be represented; only one target landmark can ever be stored per feature today. This is the SAME shape-of-fix Pattern D already solved for `Convergence` (single → multi, set-valued, accumulate-don't-overwrite), just not yet extended to `Branching`.

**Emitter gap:** none for #1/#2 (Heart, Fate have blocks); #3 involves Health, which has no block (moot until dual-target machinery exists anyway).

---

### 8. DUAL-ORIGIN (2+ simultaneous origin branches)

**Definition:** the line's own STARTING point splits into two simultaneous branches from different named sources — a fork at the origin, not partway along the line's course (contrast with §7).

**Instance:**

| # | Chapter | page_ref (book p.) | Verbatim | Origins |
|---|---|---|---|---|
| 1 | Fate | 164-165 (104-105) | "When the line rises with one branch from the base of Luna, the other from Venus, the subject's destiny will sway between imagination on the one hand and love and passion on the other." | Luna + Venus simultaneously (`FT_P03`/F030) |

**Directionality:** the two sources are both "feeding into" the line's origin — arguably closer to BRANCH-IN (§6) run twice simultaneously than to a true fork, but distinct enough (it's the line's OWN origin event, described once, not two separate incoming-branch sentences) to warrant its own entry per the corpus's own single-sentence framing.

**Cardinality:** n-way by definition (2 sources here; no 3+ instance found).

**Location sensitivity:** YES — the doctrine's entire claim (imagination vs love/passion) depends on which TWO sources are named.

**Current capture: UNCAPTURED.** `Starting_Point` is `single`-cardinality, scalar, directional — cannot hold two simultaneous origin sources. Same fix-shape as §7 (single → multi), applied to `Starting_Point` instead of `Branching`.

**Emitter gap:** none (Fate has a block).

---

### 9. PARALLEL / ALONGSIDE (co-location without crossing)

**Definition:** two lines run near or beside each other without intersecting — an ongoing spatial relationship, not a single-point event. Already well-modeled by today's schema.

**Representative instances** (not exhaustively catalogued — this type is the ONE already fully expressible and was extensively rowed by `relation_census.md`'s own PROXIMITY counts per chapter: Life 13, Head 7, Heart 2, Fate — see `doctrine_fate.md`, Health 1, Intuition 1): e.g. Life ch. p.138 "if the ray-line should rise by the side of the line of life and travel by the side of it... it shows... that she will strongly influence him"; Marriage ch. p.181 "a fine line running parallel with and almost touching the [marriage line]."

**Directionality:** symmetric in spatial sense (A parallel to B = B parallel to A), though the corpus usually narrates it from one line's vantage.

**Cardinality:** 2-way in all instances found.

**Location sensitivity:** the DEGREE of closeness (touching/medium/distant) is itself the claim-gating variable — already the exact shape `Proximity`'s `<touching|medium|distant|n/a>` scale captures.

**Current capture: FULLY CAPTURED.** `Proximity` (directional-ish but effectively symmetric in practice, `single`-cardinality, registry `relation_types`: `"proximity"`) is exactly this relationship type, already live across Head/Heart/Fate.

**Emitter gap:** none for the in-scope lines.

---

### 10. COMPARATIVE STRENGTH (line A stronger/weaker than line B)

**Definition:** a claim gated by comparing two lines' relative depth/strength/marking, not their spatial relationship at all — a magnitude comparison, structurally distinct from every relationship type above.

**Instances:**

| # | Chapter | page_ref (book p.) | Verbatim | Lines |
|---|---|---|---|---|
| 1 | Life/Health (cross-chapter) | 139 (85) / 171 (109) | "...when it is of equal strength with that of life..." / "...if the hepatica is as strongly marked as the line of life itself..." | Health vs Life strength — this is the intended antecedent behind the still-PARKED `L_P10` (blocked on Health emitting its own Depth/strength signal at all, per that parked entry's own note) |
| 2 | Marriage | 180 (116) | "When the line of influence is stronger than the subject's line of fate, then the person the subject marries will have greater power and more individuality than the subject." | Line of influence vs Fate strength |

**Directionality:** the comparison itself is symmetric (A vs B), but the CONSEQUENCE is directional/asymmetric (which one is stronger determines who dominates).

**Cardinality:** 2-way only.

**Location sensitivity:** no — a pure magnitude comparison, no spatial location involved.

**Current capture: schema exists, wiring doesn't (for these specific instances).** `condition_type: "comparative"` + `comparator`/`comparator_feature` is an ALREADY-LIVE schema shape (used elsewhere in this project, e.g. Head-line H_010a/H_010b Depth-of-head-vs-heart rules) — the MECHANISM is not a gap. Instance #1's specific blocker is `L_P10`'s own documented one: Health has no vision block, so its `Depth` can never be observed to compare against Life's. Instance #2 is additionally uncapturable because "line of influence" is not a modeled feature at all (S96 scope-out).

**Emitter gap:** Health (instance #1) — the SAME gap already on record for `L_P10`. "Line of influence" (instance #2) is not a feature this project's ontology recognizes at all (deeper than an emitter gap — a whole-doctrine scope-out).

---

## Emitter-gap summary (which lines/mounts cannot report their OWN relationships today)

| Line/feature | Has a vision block? | Appears as a relationship TARGET today? | Doctrine instances above blocked by this |
|---|---|---|---|
| Line of Health | NO | Yes (`convergence_lines` includes it as a target) | §1#4/#5 (can't confirm from Health's own observation), §10#1 (`L_P10`, can't compare its own Depth) |
| Line of Marriage | NO | No (not in `convergence_lines`, no relation_target menu) | §4#7/#8 (cuts), §5#2 (touches), §6#3/#4 (incoming branch restatement — moot, §6#2 already covers it from Fate's side) |
| Line of Sun | NO | No | §4#6 (Hindu subsystem, scoped out anyway), §4#7 (Marriage cuts Sun — genuinely in-scope, blocked) |
| Line of Mars | NO (not mentioned in the prompt at all) | No | none found needing Mars specifically as an emitter in this census (Mars ch. per `relation_census.md`: "short, simple chapter, no crossing/joining/dual-target doctrine found") |
| Line of Intuition / Via Lasciva | NO (not mentioned in the prompt at all) | No | none found (per `relation_census.md`: "shortest chapter... essentially just an origin/termination menu-setter") |
| "Line of Influence" (Hindu ray-line subsystem) | Not a modeled feature at all (S96 scope-out) | No | §4 (most instances), §5 (most instances), §10#2 — entire subsystem out of scope by decision, not oversight |

---

## Master table

| Relationship type | Instance count | Chapters | Directional? | N-way capable? | Location-sensitive? | Current field | Gap/misroute |
|---|---|---|---|---|---|---|---|
| JOIN / MEET | 6 | Life, Head, Heart, Fate, Health | Symmetric (verb) | **YES** (proven 3-way) | Mixed — YES for §1#3/#6, NO for §1#1/#2/#4/#5 | `Convergence` (+`Convergence_Location` for §1#6 only) | §1#3's 3-tier mount-gated claim uncaptured (Fate-only `CONVERGENCE_LOCATION` menu, Head has none) |
| STOPPED-BY | 2 | Fate | Directional | No instance found | No (which-line-gated, not mount-gated) | **UNCAPTURED** | Ambiguous with plain `TERMINATION`/`Position` — same physical endpoint as a positive `Convergence` instance, opposite valence, no field distinguishes them |
| TAKES POSSESSION OF / OVERTAKES | 1 | Head | Directional | No | Partially (via its own §1#3 continuation) | **UNCAPTURED** | No directional-dominance value exists; would collapse into a neutral `Convergence` if ever forced through it |
| CUT / CROSS | 8 | Life (6, Hindu subsystem, scoped out), Marriage (2, in-scope) | Directional | Yes (§4#4, one cutter, two targets) | **YES, explicitly** (the corpus's own anchor passage) | **UNCAPTURED** | The clearest location-bearing gap in the whole census; Marriage's 2 instances are real, in-scope, unbuildable today |
| TOUCH / REACH | 5 | Life (Hindu subsystem, scoped out), Marriage (1, in-scope) | Directional | No | Mostly NO (anchor passage's own point); YES for the divorce instance | Nominally overlaps `Proximity`'s wording, but structurally a different relationship (unmodeled foreign line, not an in-scope line's own PROXIMITY read) | Vocabulary collision risk: reusing "touching" for this would blur two different doctrine classes |
| BRANCH-IN / INCOMING | 4 | Heart, Fate, Marriage (x2, restating Fate's) | Directional (reverse of BRANCHES_TO) | No | No | **UNCAPTURED** | `relation_census.md`'s own #1 fix priority; blocks `FT_P04`; `BRANCHES_TO` is outgoing-only by explicit prompt wording |
| DUAL-TARGET BRANCH | 3 | Heart, Fate, Health | Directional (forking line is actor) | **YES** (2 targets each) | **YES**, centrally | **UNCAPTURED** | `Branching` is single-cardinality; same fix-shape Pattern D already solved for `Convergence`, not yet extended |
| DUAL-ORIGIN | 1 | Fate | Directional (2 sources feeding in) | **YES** (2 sources) | **YES** | **UNCAPTURED** | `Starting_Point` is single-cardinality, scalar |
| PARALLEL / ALONGSIDE | many (13+7+2+1+1 per `relation_census.md`'s prior PROXIMITY counts) | Life, Head, Heart, Fate, Health, Intuition | Symmetric in practice | No | YES (degree scale) | `Proximity` | **FULLY CAPTURED** — no gap |
| COMPARATIVE STRENGTH | 2 | Life/Health (cross-chapter, 1 doctrine), Marriage | Symmetric comparison, directional consequence | No | No | `condition_type: "comparative"` schema exists and is used elsewhere (mechanism not a gap) | Blocked per-instance by emitter gaps (Health has no Depth signal; "line of influence" not a modeled feature), not by the comparative mechanism itself |

---

## Doctrines that MIS-FIRE or are UNCAPTURABLE under today's fields

1. **Fate "stopped by" Heart/Head** (§2, page_ref 164) — **RESOLVED (S112).** Originally listed here as UNCAPTURABLE ("no field distinguishes a negative halt-termination from the positive `Convergence` reading of the exact same endpoint... this is why no such rule exists") — that framing was stale/incorrect: `FT_007`/`FT_008` already existed (S97) on the ambiguous plain-`TERMINATION` shape this entry warned against. S112 migrated both in place onto the typed `stopped_by` verb token (same mechanism `FT_016` already used for its own antecedent), closing the exact ambiguity this entry describes. See §2's own capture note above for the full account.
2. **Head "takes possession of" Heart** (§3, page_ref 154) — UNCAPTURABLE: forcing this through `Convergence` would silently discard the dominance/displacement semantics that make the doctrine's actual claim (murderous propensity) meaningful; a plain "they converged" reading loses the directionality entirely.
3. **Marriage line cuts Sun / mount-line cuts Marriage** (§4#7/#8, page_ref 181) — UNCAPTURABLE on two independent axes: no CUT relationship type exists in the schema, AND Marriage has no vision emitter block at all.
4. **The 8 Hindu ray-line CUT/TOUCH/CROSS/ATTACK/REACH instances** (§4#1-6, §5#1/#3/#4, page_ref 136-138) — deliberately OUT OF SCOPE per S96, catalogued here for completeness only; would be UNCAPTURABLE even if the CUT relationship type were built, since "line of influence" is not a modeled feature.
5. **Heart-line incoming branch from Head** (§6#1, page_ref 160) — technically capturable TODAY only if the SAME doctrine is authored from Head's own `BRANCHES_TO` field (its outgoing form); if a rule were authored keying on Heart's own vision block to detect "a branch arrived from Head," it would MIS-FIRE (silently never trigger) since no incoming-branch field exists on Heart's side.
6. **Fate incoming branch from Marriage-line-near-Luna** (§6#3/#4, page_ref 179-180) — UNCAPTURABLE: Marriage has no emitter block; even once BRANCH-IN exists generically, these two Marriage-chapter restatements of Fate's own already-parked `FT_P04` doctrine add nothing new to build against (the Fate-side statement, §6#2, already covers the same underlying doctrine).
7. **Heart-line dual-fork to Jupiter+finger-junction vs Jupiter+Saturn** (§7#1, page_ref 160) — UNCAPTURABLE: `Branching` is single-cardinality; a real dual-target fork would have its second target silently overwritten or dropped depending on extraction order, exactly the class of bug Pattern D's `Convergence` accumulation fix was built to prevent (not yet extended here).
8. **Fate dual-origin from Luna+Venus** (§8#1 = `FT_P03`, page_ref 164-165) — UNCAPTURABLE for the same single-cardinality reason as #7, applied to `Starting_Point` instead of `Branching`; already on record as parked.
9. **Health-line dual-target join with Heart+Head simultaneously** (§7#3, page_ref ~172) — UNCAPTURABLE on two independent axes: dual-target JOIN cardinality (same class as #7) AND Health has no emitter block.
10. **Life/Health comparative-strength point-of-death doctrine** (§10#1 = `L_P10`, page_ref 139/171) — already on record as parked; the comparative-mechanism itself works, but Health's missing Depth signal blocks it structurally.
11. **Marriage line-of-influence vs Fate comparative strength** (§10#2, page_ref 180) — UNCAPTURABLE: "line of influence" is not a modeled feature; deeper than an emitter gap.

---

## Recommendations / Open Design Questions

This is a requirements document — the following are OPEN QUESTIONS for a future design pass, not proposed answers:

1. Should CUT/CROSS become its own new relational attribute (parallel to `Convergence`), or is it better modeled as a variant/qualifier on an existing attribute? The corpus's own location-sensitivity (the anchor passage) suggests it needs its OWN location-companion field the way `Convergence`/`Convergence_Location` pairs today — should that pairing pattern be reused verbatim, or does CUT's directionality (unlike symmetric `Convergence`) demand a different shape entirely?
2. Is STOPPED-BY a genuinely distinct relationship type from CUT, or is it the SAME physical event (a line's course being interrupted by another) narrated from the interrupted line's own perspective vs. the interrupting line's perspective? If the latter, should ONE bidirectional-narration-aware attribute cover both CUT and STOPPED-BY, or are they doctrinally different enough (STOPPED-BY always negative-outcome, CUT sometimes neutral/positive per instance) to warrant separate treatment?
3. Should BRANCHES_TO be given a companion "incoming" field (a real inverse), or should it become bidirectional in a single field (accepting both "this line branches TO X" and "a branch arrived FROM X" as two values of one relational shape)? `relation_census.md`'s own build-sizing section already flagged this as conceptually the cheapest fix of the historically-scanned patterns — does that assessment still hold once TAKES-POSSESSION-OF and CUT/TOUCH/STOPPED-BY are added to the requirement surface?
4. Dual-target BRANCH (§7) and dual-origin (§8) both need the same single→multi cardinality upgrade Pattern D already built for `Convergence`. Should this be a GENERIC mechanism applied uniformly to `Branching`/`Starting_Point` (and any future relational attribute), or does each attribute's own doctrine shape (branch-out vs origin-in vs converge-symmetric) warrant bespoke multi-cardinality semantics per attribute, the way `Convergence`'s accumulate-into-a-set behavior was specifically designed around its own symmetric-canonicalization logic?
5. Is it worth building a Line-of-Health (and/or Line-of-Marriage) vision emitter block at all, given V1's scope decisions already dropped palm reading from the user-facing V1 surface (per CLAUDE.md's "V1 PALM DROPPED" lock) and this whole line of work is explicitly V1.1-scoped? Should THIS census itself gate on that same V1.1 boundary, or does building out the relationship-type vocabulary now (independent of whether Health/Marriage ever get emitter blocks) still have standalone value for the in-scope lines (Life/Head/Heart/Fate)?
6. TAKES-POSSESSION-OF (§3) is a single instance in the whole corpus. Does a one-off doctrine instance justify its own relational-attribute machinery, or should it be captured some other way (e.g., a soft/LLM-judged claim rather than a hard-gated deterministic antecedent, per this project's own hard/soft partition discipline)?
7. The "line of influence" / Hindu ray-line subsystem (S96 scope-out) reappears as the blocker behind roughly a third of the relationship-type instances catalogued here (CUT, TOUCH, one COMPARATIVE-STRENGTH instance). Does cataloguing these as "requirements" here create pressure to reopen the S96 decision, or should this document explicitly reaffirm that scope-out stands regardless of how many relationship-type instances trace back to it?
8. TOUCH/REACH's vocabulary collision risk with the EXISTING `Proximity` field's "touching" degree value (§5) — should a future CUT/TOUCH build deliberately rename its own vocabulary to avoid confusion with `Proximity`'s unrelated "touching" meaning, or is the collision harmless because the two live in structurally different parts of the schema (a foreign-line relationship type vs. an in-scope line's landmark-proximity read)?
