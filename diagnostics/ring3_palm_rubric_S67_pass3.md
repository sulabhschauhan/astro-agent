# Ring 3 — T4 Human-Rubric Ratification Artifact (Session 67) — Pass 3

**STATUS: DRAFT (2026-07-18). Verdict checkbox left UNCHECKED — ratification
happens in design chat, not here.** This artifact is scoring evidence
prepared for user review; it is not itself the ratification decision.

Preconditions: S67 R1 (per-feature retrieval, `0a738c3`), R3 (support gate +
Python-owned decline, `b6dee9b`), R2 (exemplar rewrite + echo guard,
`ffd504f`) all live. Chunk-text evidence surface:
`diagnostics/ring3_chunks_S67_pass3.md` (reconstruction gate PASSED both
input shapes — pages/order exact, scores within +/-0.0002 of captured).

Rubric lineage: `ring3_palm_rubric_S66_pass2.md` — same P1-P4 + P7 + Ring 1
spot-check structure, same sharpened P1 compound-sentence split rule
(observational core = D; trait/doctrine tail = C only if literally present
in a gated chunk for that feature, else U -> FAIL). This pass applies the
split rule MORE strictly than pass 2's own execution in one place: pass 2
left "square shape...practical and grounded nature" as an unsplit D row
even though the trait tail has no possible chunk support (hand shape is
not a `_FEATURE_REGISTRY` entry, so it can never be C by construction).
Pass 3 splits these consistently — see ledgers below. This is a stricter
reading than pass 2's own precedent, not a laxer one; flagged explicitly
rather than silently diverging.

**Verify-before-transcribe**: every quoted claim and chunk sentence below
was checked against the committed `.claude/read_prompt.md` RUN blocks and
`diagnostics/ring3_chunks_S67_pass3.md` directly in this session (re-read
in full, not recalled from memory) before entering a ledger. No brief-vs-
data mismatches found this pass.

## Run plan (3 generation runs, live OpenAI + vision, Streamlit app,
2026-07-18)
- **Run A** — both hands, no HAND_DETAIL (baseline) — `## RUN
  2026-07-18T11:34:32.542544`. `retry_used: True`.
- **Run B** — identical inputs, regenerate (variance probe) — `## RUN
  2026-07-18T11:35:40.844356`. `retry_used: False` — **the first run this
  pass (and across both pass 2 and pass 3) to capture a clean first draft**
  (pass 2's Known Gap flagged `retry_used` as uncaptured data; it is now
  per-run hard data via the F5 schema completion, and this is the first
  actual `False` observed).
- **Run C** — + HAND_DETAIL (stress probe) — `## RUN
  2026-07-18T11:38:22.023802`. `retry_used: True`.

## Confirmed descriptions (verbatim, transplanted from `.claude/read_prompt.md`)

**LEFT** (Run A/B/C, byte-identical across all three):
```
HAND SHAPE: Square palm, overall build is robust.
FINGERS: Fingers are long relative to the palm, straight, with rounded fingertips, and spaced moderately apart.
THUMB: Medium relative size, set moderately low, wide angle from the palm.
LIFE LINE: Present, deep, long, curves around the base of the thumb, no breaks, chains, forks, or islands visible.
HEAD LINE: Present, deep, long, slightly curved, no breaks, chains, forks, or islands visible.
HEART LINE: Present, deep, long, slightly curved, no breaks, chains, forks, or islands visible.
FATE LINE: Barely visible.
OTHER LINES: No other lines clearly visible.
MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.
MARKS: No marks clearly visible.
```

**RIGHT** (Run A/B/C, byte-identical across all three):
```
HAND SHAPE: Square palm, overall build is medium.
FINGERS: Fingers are slightly longer than the palm, appear straight, fingertips are rounded, spacing is moderate.
THUMB: Medium size, set moderately low, wide angle from the palm.
LIFE LINE: Present, deep, long, curves around the base of the thumb, no clear breaks or forks.
HEAD LINE: Present, deep, long, slightly curved, starts joined with the life line.
HEART LINE: Present, deep, slightly curved, ends below the index finger.
FATE LINE: Present, moderately deep, starts from the base of the palm and runs towards the middle finger.
OTHER LINES: Sun line is not clearly visible, health and marriage lines not clearly visible.
MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.
MARKS: No clear marks such as crosses, stars, grilles, squares, or moles visible.
```

**HAND_DETAIL** (Run C only):
```
The image shows a hand with the following observable features:
- Hand Shape: The hand appears broad with a relatively square palm.
- Finger Lengths: The fingers are of moderate length. The index finger is slightly shorter than the middle finger, and the ring finger is slightly longer than the index finger. The little finger is noticeably shorter.
- Thumb: The thumb is of moderate length and appears to have a wide angle of separation from the hand, indicating flexibility.
- Visible Lines: Life Line — a prominent line curves around the base of the thumb. Head Line — runs horizontally across the palm, starting near the life line. Heart Line — visible, curving across the top of the palm. Fate Line — not clearly visible.
- Mounts: The mounts of Venus (base of the thumb) and Jupiter (below the index finger) appear slightly raised.
- Markings: There are no unusual markings or features visible on the hand.
```

---

## Pre-registered adjudication items (scored explicitly)

### (a) Run C Jupiter omission — P4 silent-clause-drop
`mount of jupiter` is in Run C's `supported_features` (not declined — the
Python decline block is empty for Run C, `unsupported_features: ()`).
Gated chunks for it are real doctrine, not noise:
> p.112: *"THE MOUNT OF JUPITER. This mount is the raised formation at the
> base of the first finger... When developed it shows ambition, pride,
> enthusiasm in anything attempted, and desire for power."*

HAND_DETAIL confirms an affirmative, non-absent observation: *"The mounts
of Venus (base of the thumb) and Jupiter (below the index finger) appear
slightly raised."* Run C's `reading_text` (verified by direct re-read,
full text above) never mentions Jupiter, ambition, or ANY interpretation
of this mount. **Verdict: P4 silent-clause-drop, CONFIRMED.** Unlike a
genuinely absent field (which the rubric permits skipping silently), this
is a supported feature with real available doctrine AND a confirmed
non-absent observation that the reading simply never addresses, and the
decline mechanism does not cover it (decline only fires for
`unsupported_features`, which is empty here).

**Additional, non-pre-registered finding surfaced during ledger
construction**: the SAME defect recurs for `thumb` in Run C — `thumb` is
supported (p.87/p.88/p.89 gated in with real angle/phalange doctrine,
quoted under item (b) below) and HAND_DETAIL confirms *"The thumb is of
moderate length and appears to have a wide angle of separation from the
hand, indicating flexibility"* — yet Run C's `reading_text` never
addresses the thumb as its own interpreted feature (`"base of the thumb"`
appears once, but only as a life-line landmark reference, not a thumb
claim). **Run C has TWO silent-clause-drops (Jupiter, thumb), not one.**
Verified by direct re-read of the full `reading_text` string, paragraph by
paragraph — no thumb-trait sentence exists anywhere in it.

**Further finding**: `thumb` is also silently dropped in **Run B**
(regenerate of the SAME inputs as Run A, which DID address thumb — see
item (b)). Run B's full `reading_text` was re-read paragraph by paragraph;
no thumb-trait sentence exists there either (only "curves...around the
base of the thumb" as a life-line landmark, same non-claim pattern as Run
C). This means only Run A (1 of 3 runs) actually addresses a feature that
is `supported` with real, content-rich doctrine (p.87's long angle/
character passage) in ALL THREE runs. See Findings section below —
this is a cross-run addressing-instability pattern, not a one-off.

### (b) Thumb wide-angle claims vs. p.87's wide-angle doctrine valence
Confirmed THUMB fields (both hands): *"...wide angle from the palm."*
Only **Run A** makes a thumb trait claim (Runs B/C omit thumb entirely,
per item (a) above): *"This is further supported by the well-formed
thumb, which indicates a balance of willpower and logic, allowing you to
approach challenges with both determination and reason."*

Run A's gated thumb set contains p.87's angle-specific doctrine, verified
verbatim:
> *"It should have a slope toward the fingers, and yet not lie down on
> them. When it stands off the hand, at right angles to it, the [nature]
> will fly to extremes, from sheer independence of spirit. It will be
> [im]possible to manage or control such natures; they will brook no
> opposition, and they will be inclined to the aggressive in their manner
> and bearing. When the thumb is well formed, but lying down, cramped
> toward the fingers, it indicates the utter want of independence of
> spirit... nervous, timorous, but cautious..."*

**Verdict: AMBIGUOUS ATTRIBUTION, scored C but flagged, not a clean pass.**
The reading's actual wording ("well-formed thumb... balance of willpower
and logic... determination and reason") attributes the trait to
**formation/size** ("well-formed"), which literally matches a DIFFERENT
gated chunk, p.88: *"...formed thumb denotes strength of intellectual
will... three great powers that rule the world—love, logic, and will. The
first or nail phalange denotes will. The second phalange, logic."* — a
strong, literal C match on that attribution. **If instead the "wide angle"
observation specifically is read as the trait's anchor** (it is the only
angle-related confirmed field, and the reading never explicitly says
"angle"), p.87's doctrine for a wide/right-angle thumb predicts
**extremity and unmanageability** ("fly to extremes... brook no
opposition... aggressive"), not "balance" — which would be a genuine
valence mismatch bordering on inversion. The reading's own text does not
disambiguate which physical attribute it is drawing from, so this is
scored as **C (via p.88's formation/size doctrine, the reading's own
stated anchor)** with the angle-doctrine mismatch recorded as an open
adjudication flag, not silently resolved either way.

### (c) Right fate line (base of palm -> middle finger) vs. p.163's
wrist->Saturn sentence
Confirmed RIGHT FATE LINE: *"Present, moderately deep, starts from the
base of the palm and runs towards the middle finger."* Gated in all three
runs (identical fate-line chunk set: p165_c1, p165_c0, p163_c1). p.163
verbatim:
> *"When the line of fate rises from the wrist and proceeds straight up
> the hand to its destination on the Mount of Saturn, it is a sign of
> extreme good fortune and success."*

The Mount of Saturn sits at the base of the middle finger in Cheiro's own
naming convention (confirmed elsewhere in the gated set, p.123: *"The
Line of Fate, the Line of Destiny, or the Saturnian"*), and "base of the
palm" is the same origin region as "wrist." **Origin/destination match is
literal and load-bearing.** Each run's fate-line paragraph asserts a
"success" outcome for the right hand (Run A: *"a desire for success"*; Run
B: *"career and personal achievements"*; Run C: *"potential for success in
your chosen endeavors"*). **Verdict: C, content-verified, on the SUCCESS
outcome specifically** — quote p.163's wrist-clause above.

**However**, all three runs frame this success as **self-driven**
("personal ambition," "driven by... ambition," "actively pursuing your
goals" — Run A most explicitly). That self-determination register belongs
to p.163's OTHER clause: *"If the fate-line rise from the line of life and
from that po[i]nt on [i]s strong, success and riches will be won by
personal merit..."* — which requires the line to rise **from the line of
life**, a precondition the confirmed field does not state (it says "base
of the palm," matching the wrist-clause's origin, not the life-line
clause's). **This half of the claim is U** — the "personal
ambition"/"personal merit" register is borrowed from a clause whose
precondition isn't confirmed present, the same exemplar-adjacent
leakage pattern pass 2 found (there, misapplied to the faint LEFT line;
here, applied to the correct — more visible — RIGHT line, but still
citing the wrong clause's precondition). Milder than pass 2's inversion
(the outcome polarity is at least correct this time — success, not
failure), but not a clean C either.

### (d) Fate-line left/right synthesis ("clearer over time")
Run B: *"...indicates a life path that has become clearer over time."*
Run C: *"...suggests that your life path is becoming clearer and more
defined as you progress."* (Run A phrases it differently — "more
pronounced... current life is aligned with your ambitions" — without the
explicit "over time" framing.)

No gated fate-line chunk (p.165_c1, p.165_c0, p.163_c1, in any run)
states or implies a left-to-right progression / clarity-over-time
narrative — verified by re-reading all three chunks' full text above.
**Verdict: D-FRAME, not a doctrine claim.** This is the system prompt's
OWN structural convention, applied correctly: *"When BOTH hands are
present: the left hand reveals innate potential and character, the right
hand reveals the native's current life trajectory -- synthesize both into
a single unified reading."* Left=barely-visible, right=moderately-deep is
accurately reframed as "becoming clearer" under that sanctioned
convention. **Not scored as U** (it doesn't purport to be Cheiro content,
it's the reading's own stated generation mechanism), but flagged: if a
future rubric pass treats "becoming clearer" as an implicit trait claim
about the fate line's real-world trajectory rather than pure narrative
framing, it would fail for lack of chunk support. Recorded as an open
question, not resolved either way.

---

## Run A — claim ledger

`retry_used: True` (first draft failed Ring 1; passed on the S66 F2c
retry — see Ring 1 spot-check below for which validator).

| # | Claim (short quote) | Basis | Verified? |
|---|---|---|---|
| 1 | "square shape of your palms... long, straight fingers" | D (LEFT/RIGHT HAND SHAPE + FINGERS) | — |
| 2 | "...suggests a practical and methodical nature, with a strong inclination towards intellectual pursuits" | **U -> FAIL** | Hand shape has no `_FEATURE_REGISTRY` entry (structurally unverifiable). Fingers' own gated chunk p.98_c1 explicitly REJECTS the finger-length-implies-intellect claim this echoes: *"I do not hold with other works on the subject, that the fingers must be longer than the palm to show the intellectual nature... erroneous and misleading."* Borderline INVERSION, not mere absence. |
| 3 | "well-formed thumb, which indicates a balance of willpower and logic... determination and reason" | **C (attribution-ambiguous, see adjudication (b))** | p.88: *"formed thumb denotes strength of intellectual will... love, logic, and will. The first or nail phalange denotes will. The second phalange, logic."* |
| 4 | "life line on both hands is long, deep, curves around base of thumb" | D (LEFT/RIGHT LIFE LINE) | — |
| 5 | "...indicating good physical strength and vitality... unbroken... free from major health crises, with a strong constitution" | **C, content-verified, load-bearing (dual source)** | p.134_c1: *"The line of life should be long, narrow, and deep, without irregularities, breaks, or crosses of any kind. Such a formation promises long life, good health, and vitality."* + p.139_c0: *"When the line of life sweeps far out into the hand... it is in itself a sign of good physical strength and long life."* |
| 6 | "developed Mount of Venus on both hands... robust health and a passionate nature... capacity for affection and a love for beauty" | **C, content-verified** | p.112: *"if Venus be well developed, it indicates strong and robust health... This mount denotes affection, sympathy toward others, benevolence... love and worship of beauty."* **Delta vs. pass 2**: pass 2 scored this row U (Venus doctrine was absent from that run's whole-description retrieval); R1's per-feature retrieval now surfaces it. |
| 7 | "head line, deep and slightly curved... starts joined with the life line [right hand]" | D (LEFT/RIGHT HEAD LINE, verbatim match on the joining clause) | — |
| 8 | "...reflects a keen intellect and a mind that is both analytical and imaginative" | **U -> FAIL** | Gated head-line chunks (p.145_c0 naming/positional, p.147_c1 abnormal-configuration doctrine only, p.151_c2 psychic-hand-type only) give no support for a deep/curved line's positive intellect valence. |
| 9 | "...indicating that your decisions are guided by reason and intelligence... cautious approach to new ventures, ensuring plans are well thought out" (re: head-line/life-line joining) | **C, content-verified (cross-feature citation)** | p.134_c2 (gated under "life line" heading, not "head line"): *"When the line is closely connected with that of the head, life is guided by reason and intelligence, but the subject is extremely sensitive about everything which affects self, and more or less cautious in enterprises for self."* Near-verbatim. Flagged: citation lives under a DIFFERENT feature heading than the claim's surface attribution — see Findings. |
| 10 | "heart line, deep and slightly curved, ending below the index finger" | D (LEFT/RIGHT HEART LINE) | — |
| 11 | "...reveals a capacity for deep affection and a sincere approach to relationships... consistency... loyalty and sincerity" | **U -> FAIL** | Gated heart-line chunks (p.160_c2, p.161_c0, p.159_c2) cover only ABNORMAL configurations (bare/thin=coldness, joined-with-head-and-life=evil sign, faded=cold/heartless, excess=jealousy) — none states a present/deep/unbroken line's positive affection valence. Same absence pattern as pass 2's Task 14 flag (d), reconfirmed under the new retrieval mechanism. |
| 12 | "fate line, more pronounced in your right hand... indicates a current path... origin from base of palm, progression towards middle finger" | D (LEFT/RIGHT FATE LINE) | — |
| 13 | "...suggests a life path driven by personal ambition and a desire for success... actively pursuing your goals" | **SPLIT, see adjudication (c)**: "desire for success" = C (p.163 wrist-clause); "driven by personal ambition... actively pursuing" = U (borrows the life-line-clause's register without its precondition) | — |
| 14 | Jupiter decline block: *"...do not clearly address... mount of jupiter... left these out"* | Correct, matches `unsupported_features: ('mount of jupiter',)` exactly | P4-clean for this feature |

**Run A tally: 4 D-only rows, 3 clean C rows (5, 6, 9), 1 split C/U row
(13), 1 attribution-ambiguous C row (3), 4 clean U rows (2, 8, 11, and
13's second half) -> P1 FAIL (multiple unsupported/contradicted trait
claims survive).**

## Run A — rubric

| Signal | Score | Justification |
|---|---|---|
| P1 Grounding | **N** | 4 U-class findings (fingers/intellect — bordering INVERSION against p.98_c1; head-line/intellect; heart-line/affection; fate-line self-determination half). Real improvement vs. pass 2: life line and Mount of Venus are now genuinely load-bearing C rows (pass 2 had only life line). |
| P2 No contradiction of confirmed descriptions | **Y** | All D-basis claims trace cleanly; no claim asserts the opposite of a confirmed field. |
| P3 Voice | **Y** | `ring1_validation`: `passed=True`, `failures=()`. No self-help-blacklist or jargon hits on the final (retried) draft. |
| P4 No silent clause-dropping | **Y** | Thumb addressed (see item b); Jupiter explicitly declined via the Python-owned block, matching `unsupported_features` exactly; markings genuinely near-absent everywhere (see Findings), silently skipping is permitted. |

## Run A — Ring 1 spot-check
- `passed: True` / `failures: ()` / **`retry_used: True`** (captured
  directly, not inferred).
- [x] DISCLAIMER present  - [x] no jargon-blacklist terms
- [x] no unsupported dates  - [x] <=700 words
- [x] no unsupported-feature mentions (banned-feature-mention validator)
- [x] no exemplar echo (6-gram guard)

---

## Run B — claim ledger

`retry_used: False` — **first clean first draft captured across pass 2
and pass 3.**

| # | Claim (short quote) | Basis | Verified? |
|---|---|---|---|
| 1 | "square shape of your palms... long, straight fingers" | D (LEFT/RIGHT HAND SHAPE + FINGERS) | — |
| 2 | "...suggests a practical and methodical nature... hand that values structure and order, with a mind inclined towards logical reasoning" | **U -> FAIL** | Same as Run A row 2 — p.98_c1 explicitly rejects the underlying claim. |
| 3 | *(thumb — no claim; see item (a) addendum, silent-clause-drop)* | -- | **P4 concern**, not a ledger row |
| 4 | "life line on both hands is long, deep, curves gracefully around base of thumb" | D (LEFT/RIGHT LIFE LINE) | — |
| 5 | "...indicating a strong constitution and vitality... free from major health crises, with a natural resilience" | **C, content-verified** | p.134_c1 (same as Run A row 5). |
| 6 | "life line's sweep allows the Mount of Venus ample space, further emphasizing your physical strength and potential for a long life" | **C, content-verified, near-verbatim** | p.139_c0: *"When the line of life sweeps far out into the hand, thus allowing the Mount of Venus a greater scope, it is in itself a sign of good physical strength and long life."* Closest paraphrase of any run this pass. |
| 7 | "head line, also long and deep... slight curve and initial connection with the life line indicate a life guided by reason and intelligence" | **C, content-verified (cross-feature citation, same as Run A row 9)** | p.134_c2 — Run B shares Run A's exact gated set (both are the LEFT+RIGHT-only shape). |
| 8 | "...This connection suggests a cautious approach to new ventures, with decisions made after careful consideration" | Same citation as row 7 | — |
| 9 | "heart line, deep and slightly curved, ending below the index finger" | D (LEFT/RIGHT HEART LINE) | — |
| 10 | "...reveals a capacity for deep affection and emotional depth... straightforward approach to relationships, with a heart that is sincere and true" | **U -> FAIL** | Same absence as Run A row 11. |
| 11 | "fate line, barely visible in the left hand but more pronounced in the right... running towards the middle finger" | D (LEFT/RIGHT FATE LINE) | — |
| 12 | "...indicates a life path that has become clearer over time... suggests a current trajectory focused on career and personal achievements" | **"clearer over time" = D-frame, see adjudication (d); "career and personal achievements" = C via p.163 wrist-clause success outcome, see adjudication (c)** | — |
| 13 | "Mount of Venus is well-developed in both hands, indicating a warm and affectionate nature... love for beauty, music, and the arts, as well as a strong capacity for love and passion" | **C, content-verified, near-verbatim** | p.112: *"This mount denotes affection, sympathy toward others, benevolence, a desire to please, love and worship of beauty, love of color, and melody in music..."* — "music" appears literally in both. |
| 14 | Jupiter decline block, identical wording to Run A | Matches `unsupported_features` exactly | P4-clean for this feature |

**Run B tally: 4 D-only rows, 4 clean C rows (5, 6, 7/8, 13), 1 D-frame +
partial-C row (12), 1 clean U row (2, 10 — two rows) -> P1 FAIL. P4 FAIL
separately, on the thumb omission (item a addendum) — not reflected in
this ledger since it's an absence, not a claim.**

## Run B — rubric

| Signal | Score | Justification |
|---|---|---|
| P1 Grounding | **N** | Same fingers/intellect + heart-line/affection U pattern as Run A. Notably the STRONGEST C-coverage of the three runs (life line doubly-sourced, head line via cross-citation, Mount of Venus near-verbatim) — the regenerate variance did not degrade grounding relative to Run A. |
| P2 No contradiction | **Y** | Clean. |
| P3 Voice | **Y** | `ring1_validation`: `passed=True`, `failures=()`, on the FIRST draft — no retry needed. |
| P4 No silent clause-dropping | **N** | Thumb is `supported` (real p.87/p.88/p.89 doctrine available, same set as Run A) with a confirmed non-absent observation ("wide angle from the palm," both hands) and is never addressed or declined anywhere in `reading_text` — verified by full re-read. Same defect class as Run C's item (a), one occurrence instead of two. |

## Run B — Ring 1 spot-check
- `passed: True` / `failures: ()` / **`retry_used: False`**.
- [x] DISCLAIMER present  - [x] no jargon-blacklist terms
- [x] no unsupported dates  - [x] <=700 words
- [x] no unsupported-feature mentions  - [x] no exemplar echo

---

## Run C — claim ledger

`retry_used: True`. HAND_DETAIL checkpoint in effect (per S65/S66 F1
lock) — this is the stress-probe shape.

| # | Claim (short quote) | Basis | Verified? |
|---|---|---|---|
| 1 | "square shape of your palms... robust build of your left hand" | D (LEFT HAND SHAPE) | — |
| 2 | "...suggests a practical and grounded nature" | **U -> FAIL** | Hand shape, no registry entry, same as Run A/B row 2 pattern. |
| 3 | "long, straight fingers with rounded tips" | D (LEFT FINGERS; RIGHT + HAND_DETAIL corroborate) | — |
| 4 | "...indicating a balance between intellectual pursuits and a pragmatic approach to life" | **U -> FAIL, bordering INVERSION** | Run C's own gated fingers set still includes p.98_c1 (same rejection of the length-implies-intellect claim: *"erroneous and misleading"*). |
| 5 | *(thumb — no claim; see item (a), silent-clause-drop, second occurrence)* | -- | **P4 concern** |
| 6 | "life line on both hands is long, deep, curves gracefully around base of thumb" | D (LEFT/RIGHT LIFE LINE) | — |
| 7 | "...which is a strong indicator of vitality and a robust constitution" | **C, content-verified** | p.134_c1 (CONFIRMED present in Run C's own gated set at score 0.6054, chunk_id `p134_c1` — re-verified directly via script re-run, not assumed from delta-diff report): *"Such a formation promises long life, good health, and vitality."* |
| 8 | "...absence of breaks or chains in this line suggests a life free from major health crises or disruptions" | Same citation as row 7 | — |
| 9 | "deep and slightly curved head line, starting joined with the life line on your right hand" | D (RIGHT HEAD LINE, verbatim "starts joined with the life line") | — |
| 10 | "...indicates a thoughtful and deliberate approach to decision-making, with a tendency to weigh options carefully before proceeding" | **U -> FAIL, NOT the same as Run A/B** | Re-verified directly: Run C's gated LIFE LINE set is `{p135_c0, p134_c1, p134_c0}` — **p134_c2 (the "guided by reason and intelligence... cautious" chunk that supported this exact claim in Run A/B) is NOT present in Run C's set.** Run C's HEAD LINE set (`p123_c0` naming, `p151_c2` psychic-hand-type — irrelevant, this hand isn't sloping/psychic) gives no alternative support either. **Cross-run instability: same claim, same confirmed observation, C in Run A/B -> U in Run C**, purely from retrieval-query drift (HAND_DETAIL's added text changes the life-line query enough to drop this chunk). See Findings. |
| 11 | "heart line, deep and slightly curved, ending below the index finger" | D (LEFT/RIGHT HEART LINE) | — |
| 12 | "...suggests a capacity for deep affection and emotional expression... emotions are well-integrated with your intellectual faculties" | **U -> FAIL** | Same heart-line absence as Run A/B; "well-integrated with intellectual faculties" is additionally novel content with no analog in any gated chunk (heart OR head line). |
| 13 | "fate line, barely visible on your left hand but more pronounced on your right" | D (LEFT/RIGHT FATE LINE) | — |
| 14 | "...suggests that your life path is becoming clearer and more defined as you progress... potential for success in your chosen endeavors" | **"clearer/more defined" = D-frame, adjudication (d); "success" = C via p.163 wrist-clause, adjudication (c)** | Run C's fate-line gated set is identical to Run A/B (`p165_c1, p165_c0, p163_c1` — confirmed, "Run C: identical chunk set" per the evidence dump). |
| 15 | "developed Mount of Venus on both hands... strong capacity for love, affection, and a desire to connect with others... love for beauty and harmony" | **C, content-verified** | p.112 (present in Run C's gated set, score 0.6824): *"This mount denotes affection, sympathy toward others, benevolence, a desire to please, love and worship of beauty..."* |
| 16 | *(mount of jupiter — no claim; see item (a), primary pre-registered finding)* | -- | **P4 FAIL** |

**Run C tally: 4 D-only rows, 3 clean C rows (7/8, 15, half of 14), 1
D-frame+partial-C row (14), 3 clean U rows (2, 4, 12), 1 cross-run-
unstable U row (10) -> P1 FAIL. P4 FAIL, doubly (thumb + Jupiter, both
supported features with confirmed observations, both silently dropped).**

## Run C — rubric

| Signal | Score | Justification |
|---|---|---|
| P1 Grounding | **N** | Same core U pattern as A/B (fingers, hand-shape, heart-line), PLUS a newly-lost C row relative to A/B (head-line/life-line joining, now U due to retrieval instability). Life line and Mount of Venus remain solidly C. |
| P2 No contradiction | **Y** | All D-basis claims (including HAND_DETAIL-sourced ones) trace cleanly; no contradictions found. |
| P3 Voice | **Y** | `ring1_validation`: `passed=True`, `failures=()` on the retried draft. |
| P4 No silent clause-dropping | **N** | Two silent drops: mount of jupiter (pre-registered item a) and thumb (surfaced during ledger construction, same defect class). Both are `supported` features with real gated doctrine and confirmed non-absent HAND_DETAIL observations. Worse than pass 2's single-omission Run C finding (Jupiter/Markings/hair, that pass's HAND_DETAIL had an extra "Other Features" hair field this run's capture lacks) — this pass's omissions are on features with STRONGER, more content-rich doctrine available (p.87's full angle-and-character passage; p.112's explicit "shows ambition, pride, enthusiasm... desire for power" for Jupiter) than pass 2's, making the drop more consequential, not less. |

## Run C — Ring 1 spot-check
- `passed: True` / `failures: ()` / **`retry_used: True`**.
- [x] DISCLAIMER present  - [x] no jargon-blacklist terms
- [x] no unsupported dates  - [x] <=700 words
- [x] no unsupported-feature mentions  - [x] no exemplar echo

---

## Findings (non-failing, fix-forward candidates)

1. **`markings/other features` supported on all-absence fields at
   near-floor scores (0.348-0.365 in Run A/B; 0.4078-0.4115 in Run C) —
   pre-registered finding, root cause identified.** LEFT's MARKS field
   reads *"No marks clearly visible"* — this does NOT literally match any
   `_ABSENCE_PHRASES` entry (`"not clearly visible"` requires the word
   "not"; LEFT's phrasing is "No marks... visible", word order defeats
   the substring check). RIGHT's MARKS field (*"No clear marks such as
   crosses..."*) DOES match (`"no clear marks"` is a listed phrase). Since
   `_is_genuine_negative_absence` requires ALL mentioning sources to be
   absence-phrased, LEFT's near-miss alone is enough to route the feature
   through the "real, non-absent quality" fail-open path instead of the
   genuine-negative-absence path — triggering a real query that returns
   low-relevance junk (star-on-Saturn, black-spot warnings, sister-line
   doctrine) which still clears the 0.30 floor + a needle match. **Not a
   P4 failure this pass** (the reading never mentions markings in any of
   the three runs, which is the CORRECT behavior for a genuinely absent
   feature) — but it is a latent risk: a future hand with a different
   "no X visible" phrasing could similarly evade the absence-phrase list
   and have the LLM actually USE junk-scored content. Fix-forward
   candidate: broaden `_ABSENCE_PHRASES` to catch `"no marks"` /
   `"no clear marks"` in more word orders, or match a regex pattern
   (`no\s+\w*\s*marks?\s+.*visible`) instead of fixed substrings.
2. **Cross-run addressing instability on `supported` features.** Thumb is
   `supported` with real, rich doctrine (p.87) in ALL THREE runs but is
   only actually addressed in 1 of 3 (Run A). Head-line/life-line joining
   doctrine (p.134_c2) is present in Run A/B's gated set but absent from
   Run C's (retrieval-query drift from HAND_DETAIL's added text). The
   Python-owned decline mechanism (S67 R3) only guarantees coverage for
   features that fail the SUPPORT GATE (zero surviving chunks) — it does
   not and cannot guarantee that a `supported` feature with real evidence
   actually gets used by the LLM, or that the SAME feature stays
   consistently supported across regenerations/input-shape changes. This
   is a genuine gap between "supported" (deterministic, Python-owned) and
   "addressed" (LLM discretion, not deterministically enforced) that R3
   did not close and wasn't designed to close — worth a design-chat
   conversation about whether a "supported-but-unaddressed" check
   belongs in Ring 1 (would need to be a soft warning, not a hard fail,
   since some silent omission of a low-relevance supported feature may be
   legitimate editorial judgment, same as the STRICT SCOPE prompt
   permits ignoring low-relevance retrieved passages).
3. **p.163 fate-line valence chunk is now reliably retrieved (a real
   improvement, not a new problem)** — present in ALL SIX runs across
   pass 2 and pass 3's fate-line gated sets... correction: pass 2's whole-
   description query never retrieved it at all (pass-2 finding: "p.163 is
   NOT in this run's retrieved n=6/n=7 set"); it is present in all THREE
   pass-3 runs. The polarity risk pass 2 flagged (misapplying the
   "personal merit" clause to a faint line) is REDUCED but not eliminated
   this pass — see adjudication (c): this pass applies the self-
   determination register to the correct (more visible) line, but still
   borrows a clause whose stated precondition ("rise from the line of
   life") isn't literally confirmed.

## P7 — Vision fidelity

**PENDING USER RATIFICATION.** This pass's descriptions were captured
live during an actual 2026-07-18 app session (not a headless probe) —
the S65/S66 F1 human-checkpoint UI was exercised procedurally (palm_left,
palm_right, and hand_detail were each displayed and confirmed before
generation, per the app's wiring). That procedural confirmation is NOT
the same as this artifact's own P7 sign-off, which requires the user to
visually re-verify the confirmed field text against the actual uploaded
images (as was done for pass 2's annotated fate-line corridor check).
**No P7 score is asserted here** — final P7 sign-off, and by extension
this artifact's overall ratification, happens when the user reviews this
draft in design chat.

## Verdict

**Ratification bar (unchanged from pass 1/pass 2): Runs A, B, C ALL score
4/4 on P1-P4, P7 OK/minor. Literal scoring only.**

| Run | P1 | P2 | P3 | P4 | Score |
|---|---|---|---|---|---|
| A | N | Y | Y | Y | 3/4 |
| B | N | Y | Y | N | 2/4 |
| C | N | Y | Y | N | 2/4 |

- [ ] NOT RATIFIED
- [ ] RATIFIED-LIVE

**Pending design-chat review + user ratification.** Neither box is
checked in this draft — the itemized table above is the evidence; the
decision is the user's to make. As scored, no run currently reaches 4/4
(P1 fails on all three via the fingers/hand-shape/heart-line U-pattern;
P4 additionally fails on B and C via the thumb/Jupiter omission pattern
in Findings #2) — presented here as data for that review, not as a
pre-committed verdict.

**Progress vs. pass 2** (for context, not a scoring input): P3 (voice)
remains fully fixed, consistent with pass 2. Life line and Mount of Venus
grounding went from unsupported/absent-doctrine (pass 2) to consistently
load-bearing C rows (pass 3, all three runs) — the R1 per-feature
retrieval fix is doing real work. The remaining P1 gap has shifted in
character: pass 2's gap was "doctrine mostly absent from retrieval at
all"; pass 3's gap is narrower but sharper — specific claims (finger-
length-intellect) are now actively CONTRADICTED by retrieved content
rather than merely unsupported, and a new failure mode (P4
supported-but-unaddressed, Findings #2) emerged that pass 2's own
findings didn't surface (pass 2's only P4 finding was about a
non-absent-but-never-supported field, a different mechanism).

**Re-open condition** (unchanged): any post-ratification live T4 failure
reopens Ring 3 at N=5 runs.
