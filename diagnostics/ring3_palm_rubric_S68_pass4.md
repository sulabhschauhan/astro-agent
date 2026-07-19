# Ring 3 — T4 Human-Rubric Ratification Artifact (Session 68) — Pass 4

**STATUS: SCORED — pass 4, verdict NOT RATIFIED (2026-07-19). Frozen
record; keep forever.**

Preconditions: S68 F-C (A1 chunk-anchor tagging + Ring 1 V-1/V-2, `73dc0a5`
et al.), F-A (supported-feature coverage check, `d54c968`/`afe6b4f`), F-B
(absence-phrase regex broadening, `d01401a`) all live. Evidence surface:
`diagnostics/ring3_evidence_S68_pass4.md` (claim ledger built from
SELF-DECLARED anchors in each run's `reading_text_tagged` — direct
positional parse, NOT a reconstruction; coverage warnings and chunk text
ARE reconstructed, gated behind a measure-first fidelity assert that
PASSED for all 3 runs).

Rubric lineage: `ring3_palm_rubric_S67_pass3.md` — same P1-P4 + P7 + Ring 1
spot-check structure, same compound-sentence split rule (observational
core = D; trait/doctrine tail = C only if literally present in the CITED
chunk, else U → FAIL). Two S68 additions, both embedded per design-chat's
prior adjudication (recorded, not re-litigated below): the anchor-fidelity
spot-check row, and the warnings-block-P4-clean rule.

**Verify-before-transcribe**: every quoted claim/chunk sentence below was
checked against `diagnostics/dogfood_capture.md` and
`diagnostics/ring3_evidence_S68_pass4.md` directly, in this session (the
evidence file's own reconstruction-fidelity gate passed for all 3 runs
before any of its chunk text was trusted). One correction made mid-session
and recorded, not silently fixed: an initial pass at scoring Run A's row 6
(head-line/chain-indecision claim) read a negation of a stated negative
("chain → indecision" implies "no chain → no indecision") as C; re-checked
against pass-3's own precedent (which explicitly required a chunk to STATE
the positive valence directly, not merely imply it via negation — see
pass-3's heart-line U-rows) and corrected to U. Documented at that row.

## Run plan (3 scored generation runs + 3 fail-closed attempts, live
OpenAI + vision, Streamlit app, 2026-07-19, fresh photo uploads)

- **Run A (baseline)** — both hands, no HAND_DETAIL — `## RUN
  2026-07-19T10:40:50.482046`. `retry_used: True`. Preceded by 2 fail-closed
  attempts (10:36:21, 10:37:24) — see Appendix.
- **Run B (identical-input regenerate)** — `## RUN
  2026-07-19T10:42:48.947566`. `retry_used: True`. Confirmed identical
  LEFT/RIGHT to Run A. Preceded by 1 fail-closed attempt (10:41:49) — see
  Appendix.
- **Run C (+HAND_DETAIL)** — `## RUN 2026-07-19T10:43:39.978164`.
  `retry_used: True`. Same LEFT/RIGHT as A/B + HAND_DETAIL added.

Unlike pass 3, **all 3 scored runs needed the F2c retry** (`retry_used:
True` across the board) — none captured a clean first draft this pass.

## Confirmed descriptions (verbatim, from `diagnostics/dogfood_capture.md`)

**LEFT** (Run A/B/C, byte-identical across all three):
```
HAND SHAPE: Square palm, overall build is robust.
FINGERS: Fingers are long relative to the palm, straight, with rounded fingertips, moderate spacing.
THUMB: Medium size, set moderately low, wide angle from the palm.
LIFE LINE: Present, deep, long, curves around the base of the thumb, no breaks or chains visible.
HEAD LINE: Present, deep, long, slightly curved, runs across the palm, no breaks or chains visible.
HEART LINE: Present, deep, long, curves slightly upward, no breaks or chains visible.
FATE LINE: Barely visible.
OTHER LINES: Sun line is not clearly visible; health and marriage lines not clearly visible.
MOUNTS: Mount of Venus appears developed; other mounts are unremarkable.
MARKS: No crosses, stars, grilles, squares, or moles clearly visible.
```

**RIGHT** (Run A/B/C, byte-identical across all three):
```
HAND SHAPE: Square palm, medium build
FINGERS: Medium length relative to palm, straight, rounded fingertips, moderate spacing
THUMB: Medium size, low set, wide angle from the palm
LIFE LINE: Present, deep, long, curves around the base of the thumb, no clear breaks or forks
HEAD LINE: Present, deep, long, slightly curved, no clear breaks or forks
HEART LINE: Present, deep, long, curves slightly upward, no clear breaks or forks
FATE LINE: Barely visible
OTHER LINES: Not clearly visible
MOUNTS: Mount of Venus appears developed, other mounts not clearly visible
MARKS: Not clearly visible
```

**HAND_DETAIL** (Run C only):
```
- Hand Shape: broad, relatively square palm.
- Finger Lengths: moderate length; index shorter than middle; ring slightly longer than index; little finger noticeably shorter.
- Thumb: average length, moderate angle of flexibility.
- Visible Lines: Life Line — prominent, curves around base of thumb. Head Line — runs horizontally, starting near life line. Heart Line — visible, starting under little finger, curving toward index finger. Fate Line — a faint line running vertically up the center of the palm.
- Mounts: mounts under the fingers appear moderately developed.
- Markings: no unusual markings or features visible.
- Other Features: hair present on back of hand and fingers.
```

---

## Design-chat adjudications embedded (recorded, not re-litigated)

### 1. P4 all runs: NOT CLEAN, mechanical cascade from a real F-B gap
Rule applied as written: `ValidationReport.warnings` non-empty ⇒ P4 cannot
score clean, for all 3 runs. Root cause, for pass-5 comparability, not
exculpation: all 3 runs' LEFT hand phrased MARKS as *"No crosses, stars,
grilles, squares, or moles clearly visible"* — a comma-separated list that
defeats `_ABSENCE_PATTERNS_BY_FEATURE`'s `(?:\s+\w+){0,3}` filler-group
regex (a comma is not `\s`, so the pattern cannot skip past it). This holds
`markings/other features` in `supported_features` via near-floor junk
retrieval (scores 0.34–0.49) instead of exiting to genuine-negative-absence.
The model correctly cited NONE of that junk in any of the 3 readings — the
coverage warning is the mechanism catching exactly the case it was built to
catch (a supported-but-uncited feature), firing correctly on a classification
that is itself wrong upstream. **The rule is not at fault; F-B's regex is
the fixable layer.** Not fixed here (out of scope, no production code
change this session).

### 2. Anchor-fidelity row: FAIL
`cheiroslanguageo00chei_1_p163_c1` cited in all 3 runs for a barely-visible-
fate-line / self-direction claim. Chunk content (verbatim, all 3 runs'
own sections in the evidence file): discusses where a fate line **rises
from** and its **strength** determining personal-merit-vs-parental-sacrifice
outcomes — nothing about faintness/visibility implying self-direction.
**FAIL, confirmed** — 1 of ~16–17 clauses per run, consistent across all 3.
Recorded as the first live gaming-rate data point for F-C's accepted gap
(a) (V-2 anchor legality is union-only, backstopped by this exact human
spot-check, not a future mechanical validator) — the citation IS legally
valid (the chunk really is gated for `fate line`, so V-2 correctly does not
flag it), the defect is purely in WHETHER the cited content supports the
SPECIFIC claim, which is exactly the class of thing gap (a) says this
spot-check — not a mechanical check — exists to catch.

### 3. Ledger scoring rule (methodology, applied below)
C requires the cited chunk to literally carry the claim's doctrine
(pass-3's compound-split rule, unchanged). `[OBS]` rows = D unless the
clause asserts doctrine-shaped interpretive content with no anchor at all
(then U → FAIL — a mistagged-as-observation trait claim is worse than an
absent one, not exempt from scoring). Applied consistently below; see the
Verify-before-transcribe note above for the one mid-session self-correction.

### 4. Appendix required check
Per-draft, verbatim: for each of the 3 fail-closed attempts, was the
"stability" sentence anchored, and does its cited chunk contain
"stability"? See Appendix below — done.

### 5. P7 section
**RATIFIED (2026-07-19, design chat).** Procedural F1 confirmation (the
human-checkpoint UI exercised live for all 3 runs' descriptions) is NOT
itself the same as artifact sign-off, per pass-3's own precedent (which
required a SEPARATE design-chat visual re-verification step before
marking P7 OK) — that separate step happened here: the user reviewed the
fresh 2026-07-19 uploads and confirmed the descriptions against them in
design chat, and design chat proceeding to close-out on that basis is
the sign-off itself, same standard pass-3 applied. See the P7 section
below for the final wording.

---

## Run A — claim ledger

`retry_used: True`.

| # | Clause | Anchor | Verified? |
|---|---|---|---|
| 1a | "square palm and well-proportioned fingers" | [OBS] | D — restates confirmed HAND SHAPE + FINGERS. |
| 1b | "...indicating a practical and methodical approach to life" | [OBS] | **U → FAIL** — hand shape has no `_FEATURE_REGISTRY` entry; doctrine-shaped claim, no anchor at all (mistagged observation). Same class as pass-3's row 2. |
| 2 | "long, deep life line...suggests a strong constitution and the promise of a long and healthy life" | `p134_c1` | **C** — chunk states directly: "long, narrow, deep, without irregularities...promises long life, good health, and vitality." |
| 3 | "continuity without breaks or chains further reinforces...enduring vitality and resilience" | `p134_c1` | **C** — same chunk states the positive valence DIRECTLY ("without...breaks...promises...vitality"), not via inference. |
| 4 | "head line...reflects a strong mental capacity and intellectual vigor" | `p145_c0` | **U → FAIL** — chunk is the HEAD LINE chapter's naming/intro text only ("relates principally to the mentality...to the intellectual strength OR weakness" — neutral framing, no valence for deep/long). Identical chunk, identical defect as pass-3 Run A row 8. |
| 5 | "slight curve suggests a balance between logic and creativity" | `p145_c0` | **U → FAIL** — same chunk, no support. |
| 6 | "absence of breaks or chains...indicates a stable and consistent mental outlook, free from indecision" | `p147_c1` | **U → FAIL (corrected during scoring — see note above)** — chunk ONLY states the negative conditional ("when linked...chain...denotes want of fixity...indecision"); never states the positive ("when clean, stable outlook"). Applying pass-3's own precedent (heart-line rows), an unstated negation-inference does not count as C. |
| 7 | "heart line...speaks to a warm and affectionate nature" | `p160_c2` | **U → FAIL** — chunk covers ONLY abnormal configs (bare/thin=coldness, joined=evil sign); no positive-valence statement for a normal deep/curved line. Identical defect to pass-3. |
| 8 | "unbroken form suggests sincerity...capacity for deep, enduring affection" | `p160_c2` | **U → FAIL** — same chunk, same issue. |
| 9 | "upward curve indicates a positive and optimistic approach to relationships" | `p160_c2` | **U → FAIL** — same chunk, same issue. |
| 10 | "barely visible fate line suggests...may not be strongly influenced by external forces or predetermined destiny" | `p163_c1` | **U → FAIL** — anchor-fidelity FAIL, adjudication #2. |
| 11 | "more self-directed, relying on personal choices and actions rather than fate" | `p163_c1` | **U → FAIL** — same chunk, continues the unsupported claim. |
| 12 | "Mount of Venus, well-developed...strong capacity for love and passion...robust physical health" | `p112_c0` | **C** — chunk: "well developed...strong and robust health...denotes affection...love and worship of beauty." |
| 13 | "benevolent and affectionate disposition, with a love for beauty and harmony" | `p112_c0` | **C** — same chunk, direct match. |
| 14 | "thumb, medium in size and set at a wide angle, suggests a balance of will, logic, and love...well-rounded character" | `p88_c0` | **C, attribution-ambiguous** (pass-3 precedent) — chunk's "love, logic, and will" framing matches the claim's own attribution to formation/size, not the (uncited) angle-doctrine at p.87 which would predict a different valence for a wide angle. Flagged, not failed, matching pass-3's item (b) disposition. |
| 15 | "fingers, long and straight with rounded tips, further emphasize an intellectual and refined nature...thoughtful and independent action" | `p96_c0` | **U → FAIL** — chunk's "independence of thought/action" doctrine is tied to WIDE finger SPACING; confirmed field states "moderate" spacing, not wide — precondition unmet, same class as pass-3 item (c)'s precondition-mismatch reasoning. "Intellectual and refined" has no support at all in this chunk. |
| 16 | Summary: "strong health, intellectual capability, and deep emotional capacity...largely self-directed..." | [OBS] | **U → FAIL** — restates specific prior U-scored claims (intellectual capability, self-directed) without new citation. |

**Run A tally: 4 clean C rows (2, 3, 12, 13), 1 attribution-ambiguous C row
(14), 1 D-only partial row (1a), 11 U rows (1b, 4, 5, 6, 7, 8, 9, 10, 11,
15, 16) → P1 FAIL, more U-rows than pass-3's equivalent run (pass-3 Run A:
4 U rows; this run: 11).**

## Run A — rubric

| Signal | Score | Justification |
|---|---|---|
| P1 Grounding | **N** | 11 U-class rows. Heart line and head-line-interpretive fully unsupported (same as pass-3); fate line now ENTIRELY unsupported (pass-3 had a partial C via a different clause in the same chunk — this run's actual sentence never touches the wrist/success clause at all); fingers newly U on a precondition mismatch. Life line and Mount of Venus remain solidly C (consistent with pass-3). |
| P2 No contradiction | **Y** | All D-basis claims trace cleanly to confirmed fields; no direct contradictions found. |
| P3 Voice | **Y** | `ring1_validation`: `passed=True`, `failures=()` on the (retried) final draft. |
| P4 No silent clause-dropping | **N** | Coverage warning present (`markings/other features supported but never cited`) — NOT CLEAN per adjudication #1. Mount of Jupiter correctly declined (`unsupported_features: ('mount of jupiter',)`, decline block names it); thumb IS addressed (row 14) — no ADDITIONAL silent-drop beyond the coverage-warning mechanism. |

## Run A — Ring 1 spot-check
- `passed: True` / `failures: ()` / **`retry_used: True`**.
- [x] DISCLAIMER present · [x] no jargon-blacklist terms
- [x] no unsupported dates · [x] ≤700 words
- [x] no unsupported-feature mentions · [x] no exemplar echo
- [x] `reading_text_tagged` populated, real anchor tags present (A1, new this pass)
- [ ] **coverage warnings clean** — FAILS: `['coverage: markings/other features supported but never cited']`

---

## Run B — claim ledger

`retry_used: True`.

| # | Clause | Anchor | Verified? |
|---|---|---|---|
| 1a | "robust and square palm" | [OBS] | D — restates confirmed field. |
| 1b | "...indicating a practical and grounded nature, with a strong foundation..." | [OBS] | **U → FAIL** — same hand-shape pattern as Run A row 1b. |
| 2 | "long, deep, and unbroken life line...promises good health and vitality" | `p134_c1` | **C** — same direct-statement chunk as Run A. |
| 3 | "life line's curve...allowing the Mount of Venus to have greater scope...robust health and a passionate disposition" | `p139_c0` | **C, near-verbatim** — chunk: "sweeps far out into the hand, thus allowing the Mount of Venus a greater scope, it is in itself a sign of good physical strength" — AND the same chunk separately states "passionate in their disposition" (both halves of this claim are literally present in the one cited chunk). |
| 4 | "head line, deep and slightly curved...strong intellect and a balanced approach...clear and decisive mind, free from indecision" | `p145_c0` | **U → FAIL** — same naming/intro chunk, no valence support. |
| 5 | "intellectual strength is both an innate trait and a current reality, guiding your actions with reason and intelligence" | [OBS] | **U → FAIL** — doctrine-shaped claim (echoes Cheiro's own well-known "guided by reason and intelligence" phrasing), NO anchor at all. Worse than a mismatched citation — no citation to check. |
| 6 | "heart line...capacity for deep affection and emotional expression...unbroken state suggests steadiness...free from turmoil" | `p160_c2` | **U → FAIL** — same abnormal-only chunk as Run A. |
| 7 | "emotional depth is a fundamental aspect of your character, as well as a current strength" | [OBS] | **U → FAIL** — restates row 6's unsupported claim, no anchor. |
| 8 | "barely visible fate line suggests...destiny plays a less pronounced role...personal effort and choices are more significant" | `p163_c1` | **U → FAIL** — anchor-fidelity FAIL, adjudication #2. |
| 9 | "life is largely self-directed, relying on personal merit rather than predetermined fate" | [OBS] | **U → FAIL** — "personal merit" is literally borrowed from p163_c1's OTHER clause (requires the line to rise "from the line of life" — a precondition never confirmed), same leakage pattern as pass-3 item (c), and here presented with NO anchor at all. |
| 10 | "Mount of Venus is well-developed...strong capacity for affection, sympathy, and a love of beauty and harmony" | `p112_c0` | **C, near-verbatim** — "denotes affection, sympathy toward others, benevolence...love and worship of beauty." |
| 11 | "mount's prominence...these qualities are deeply ingrained...continue to influence your current life path" | [OBS] | **D-frame** (pass-3 adjudication (d) convention) — extends row 10's already-C-verified claim temporally; introduces no NEW unsupported trait content. |
| 12 | "medium-sized thumb, set at a wide angle, suggests a balance of willpower and logic...independence and self-reliance" | `p88_c0` | **C, attribution-ambiguous** — same disposition as Run A row 14. |
| 13 | "thumb's characteristics are consistent in both hands...inherent and actively present" | [OBS] | **D-frame** — same reasoning as row 11. |
| 14 | "fingers, long and straight with rounded tips, suggest an intellectual nature and a refined approach to life" | `p98_c1` | **U → FAIL, CONFIRMED INVERSION** — chunk states: *"I do not hold with other works on the subject, that the fingers must be longer than the palm to show the intellectual nature...erroneous and misleading."* The cited chunk directly REJECTS the exact claim it is attached to. Stronger than pass-3's "bordering inversion" language (pass-3 never actually cited this rejection chunk directly against the claim; this run does). |
| 15 | "feature is consistent in both hands, reinforcing the intellectual and thoughtful aspects of your character" | [OBS] | **U → FAIL** — restates and compounds row 14's inverted claim. |
| 16 | Summary: "...intellectual clarity...emphasis on personal agency and self-determination..." | [OBS] | **U → FAIL** — restates specific prior U/inverted claims. |
| 17 | "Note: Features not covered by retrieved passages include the sun line, health and marriage lines, and any specific markings..." | [OBS] | **D** — meta-commentary on retrieval coverage, not a trait claim; accurate (sun line genuinely absent, markings genuinely never cited). |

**Run B tally: 4 C rows (2, 3, 10, 12), 2 D-frame rows (11, 13), 2 D-only
rows (1a, 17), 10 U rows (1b, 4, 5, 6, 7, 8, 9, 14 [CONFIRMED INVERSION],
15, 16) → P1 FAIL, including a direct citation-content self-contradiction
(row 14), the most serious single defect found across all 3 runs.**

## Run B — rubric

| Signal | Score | Justification |
|---|---|---|
| P1 Grounding | **N** | Worst of the three runs on defect severity: a CONFIRMED inversion (row 14, cited chunk directly rejects its own claim), plus 3 doctrine-shaped `[OBS]` rows with no anchor at all (5, 7, 9) — a new failure shape not seen in pass 3 (pass 3's U-rows were all mis-supported citations, not un-anchored assertions). Life line and Mount of Venus remain the strongest C-coverage. |
| P2 No contradiction | **Y** | D-basis claims trace cleanly. |
| P3 Voice | **Y** | `ring1_validation`: `passed=True`, `failures=()` on the retried final draft. |
| P4 No silent clause-dropping | **N** | Coverage warning present — NOT CLEAN per adjudication #1. Jupiter correctly declined; thumb addressed (rows 12/13) — no additional silent-drop. |

## Run B — Ring 1 spot-check
- `passed: True` / `failures: ()` / **`retry_used: True`**.
- [x] DISCLAIMER present · [x] no jargon-blacklist terms
- [x] no unsupported dates · [x] ≤700 words
- [x] no unsupported-feature mentions · [x] no exemplar echo
- [x] `reading_text_tagged` populated, real anchor tags present
- [ ] **coverage warnings clean** — FAILS: `['coverage: markings/other features supported but never cited']`

---

## Run C — claim ledger

`retry_used: True`. HAND_DETAIL checkpoint in effect.

| # | Clause | Anchor | Verified? |
|---|---|---|---|
| 1a | "square palm and well-formed lines" | [OBS] | D — restates confirmed field. |
| 1b | "...indicating a strong foundation in both innate potential and current life trajectory" | [OBS] | **U → FAIL** — hand-shape/lines trait framing, no registry backing. |
| 2 | "life line, deep and unbroken...promises long life, good health, and vitality" | `p134_c1` | **C** — direct statement, same chunk as A/B. |
| 3 | "continuity from potential to present suggests a stable and enduring constitution, free from...health challenges" | `p134_c1` | **C** — same chunk states the positive valence directly (as in Run A row 3's reasoning). |
| 4 | "head line...indicates a natural balance between intellect and emotion...practical and clear thinking" | `p123_c0` | **U → FAIL** — chunk is a pure NAMING/taxonomy passage (alternate line names + hemisphere framing); no valence content at all for a deep/curved line. |
| 5 | "mental faculties have been well-developed from potential to present...handle life's complexities with a steady mind" | `p123_c0` | **U → FAIL** — same chunk, same issue. |
| 6 | "heart line, deep and curving slightly upward...capacity for deep affection and emotional engagement" | `p159_c3` | **U → FAIL** — chunk covers only abnormal configs (bright red=violence, pale/broad=indifference, low-set=interference); no positive-valence statement. |
| 7 | "absence of breaks or forks...emotional life is stable and sincere, straightforward approach to relationships" | `p159_c3` | **U → FAIL** — same chunk, same issue. Also: "breaks or forks" was never actually a confirmed HEART LINE attribute in either hand's field text this run (LEFT says "no breaks or chains"; the field never mentions "forks" for heart line) — a minor D-basis slippage on top of the U doctrine gap. |
| 8 | "fate line, barely visible...may not be strongly influenced by external forces or destiny" | `p163_c1` | **U → FAIL** — anchor-fidelity FAIL, adjudication #2. |
| 9 | "life more shaped by personal choices and internal motivations than by fate or circumstance" | `p163_c1` | **U → FAIL** — same chunk, continues the claim. |
| 10 | "Mount of Venus, well-developed...strong capacity for love, affection, and a zest for life" | `p112_c0` | **C** — chunk matches directly. |
| 11 | "mount's prominence suggests a robust health and a passionate nature, love for beauty and harmony" | `p112_c0` | **C** — direct match. |
| 12 | "thumb, medium in size and set at a wide angle, reflects a balanced will and reason...flexibility to adapt" | `p88_c1` | **U → FAIL** — DIFFERENT chunk than A/B's p88_c0. This chunk discusses PHALANGE-LENGTH RATIOS and JOINT SUPPLENESS, not size or angle at all — the cited content does not address either confirmed attribute (medium size, wide angle). Worse than A/B's attribution-ambiguous case: here the citation is about a different physical dimension entirely. |
| 13 | "neither overly rigid nor excessively yielding, capable of making decisions with both strength and consideration" | `p88_c1` | **U → FAIL** — the chunk's actual "supple vs. stiff" framing could map to "yielding vs. rigid," but NO joint-suppleness observation was confirmed anywhere in this run's descriptions or HAND_DETAIL — precondition unmet. |
| 14 | "fingers, long and straight with rounded tips, indicate a love of detail and precision in your endeavors" | `p95_c0` | **C, strong/near-verbatim** — chunk states directly: "Long fingers give love of detail in everything...exact in matters of dress." A DIFFERENT, genuinely supportive chunk than the rejection chunk (p98_c1) A/B's near-identical claim cited — real cross-run retrieval instability on the SAME underlying claim type, opposite outcomes. |
| 15 | "ability to focus on the finer points of any task, whether in personal or professional life" | `p95_c0` | **C** — same chunk, reasonable extension. |
| 16 | Summary: "...steady health...absence of significant markings or disruptions...self-directed..." | [OBS] | **U → FAIL** — restates prior U claims (self-directed, balanced thought/emotion). |
| 17 | "Note: Features not covered by retrieved passages include the specific length and spacing of fingers, the presence of hair..., and the detailed shape of the mounts other than Venus" | [OBS] | **D** — accurate meta-commentary. |

**Run C tally: 6 C rows (2, 3, 10, 11, 14, 15 — the strongest C-coverage of
the three runs), 2 D-only rows (1a, 17), 10 U rows (1b, 4, 5, 6, 7, 8, 9,
12, 13, 16) → P1 FAIL.**

## Run C — rubric

| Signal | Score | Justification |
|---|---|---|
| P1 Grounding | **N** | Best C-coverage (life line doubly-sourced, Mount of Venus, AND fingers now genuinely supported via a different chunk than A/B) but the thumb citation (p88_c1) is a genuine off-topic mismatch (wrong physical dimension), and head/heart line remain fully unsupported. |
| P2 No contradiction | **Y** | All D-basis claims (including HAND_DETAIL-sourced ones) trace cleanly. |
| P3 Voice | **Y** | `ring1_validation`: `passed=True`, `failures=()` on the retried final draft. |
| P4 No silent clause-dropping | **N** | Coverage warning present — NOT CLEAN per adjudication #1. Jupiter correctly declined (`unsupported_features: ('mount of jupiter',)`); thumb addressed (rows 12/13, even though content-poor) — no additional silent-drop. |

## Run C — Ring 1 spot-check
- `passed: True` / `failures: ()` / **`retry_used: True`**.
- [x] DISCLAIMER present · [x] no jargon-blacklist terms
- [x] no unsupported dates · [x] ≤700 words
- [x] no unsupported-feature mentions · [x] no exemplar echo
- [x] `reading_text_tagged` populated, real anchor tags present
- [ ] **coverage warnings clean** — FAILS: `['coverage: markings/other features supported but never cited']`

---

## Findings (non-failing, fix-forward candidates)

1. **F-B comma-list gap, live-confirmed on 3/3 runs** — see adjudication
   #1 for root cause. Fix candidate (not applied): allow `[,;]?\s+` in
   `_ABSENCE_PATTERNS_BY_FEATURE`'s filler-group pattern instead of bare
   `\s+\w+`.
2. **Cross-run retrieval instability, same claim type, opposite
   outcomes.** The "long fingers → intellectual/refined nature" claim
   appears in all 3 runs; Run A/B cite `p98_c1` (which REJECTS the claim,
   producing a confirmed inversion in Run B) while Run C cites `p95_c0`
   (which SUPPORTS the claim directly). Same underlying confirmed
   attribute (long, straight, rounded-tip fingers), same claim shape,
   opposite doctrine outcome purely from which chunk the per-feature query
   happened to retrieve. This is the SAME class of instability pass-3's
   Findings #2 identified for head-line/life-line joining doctrine —
   confirms it is a recurring pattern, not a one-off.
3. **Un-anchored doctrine-shaped `[OBS]` rows — a failure shape not seen
   in pass 3.** Run B rows 5, 7, 9 assert interpretive trait claims
   (echoing real Cheiro phrasing in row 5's case) with NO citation at all,
   tagged `[OBS]` despite not being pure observation. Pass 3 predates the
   A1 tagging contract, so this specific shape (mistagged sourcing) could
   not have been observed there — worth tracking whether this is
   idiosyncratic to this session's drafts or a recurring generation habit.
4. **Confirmed inversion (Run B row 14) is the single most serious defect
   found across pass 3 and pass 4 combined.** Pass 3's closest analog
   (Run A row 2, "bordering inversion") never actually cited the rejection
   chunk against the claim — it was scored as unsupported/contradicted by
   a DIFFERENT gated chunk in the same feature's set, not the cited one.
   Here, the model cites `p98_c1` directly for a claim `p98_c1` itself
   rejects. Recommend this be flagged explicitly for the S69 design
   conversation the Appendix's stability-anchor data also feeds.
5. **Markings/other features` never once gets cited or discussed across
   all 3 runs** despite sitting in `supported_features` throughout (per
   Finding 1/F-B gap) — confirms F-A's coverage mechanism, not F-B's
   classification, is what's actually protecting users from fabricated
   markings content right now. The classification bug (Finding 1) and the
   safety outcome (no fabrication reaches the user) are two separate
   facts; only the first is still open.

## Appendix — fail-closed attempts (2026-07-19)

Three attempts hit the S66 F2c hard cap with BOTH drafts failing
`self_help_blacklist: found stability`, requiring a manual re-click (not
an in-app auto-retry — `retry_used: True` on these refers to the
IN-CALL first-draft→retry mechanism inside `generate_palm_reading()`,
which fired and still failed; the user's re-click is a SEPARATE, manual,
outside-the-call regeneration, a different concept from `retry_used`).

| Timestamp | Mapped to | "stability" sentence | Anchor | Cited chunk contains "stability"? |
|---|---|---|---|---|
| 10:36:21 | Run A attempt 1 | *"Overall, your hands reveal a life characterized by strength, stability, and a balanced approach to both intellectual and emotional pursuits."* | `[OBS]` — no chunk cited | N/A — no chunk to check; pure free composition. |
| 10:37:24 | Run A attempt 2 | *"...indicates a capacity for deep affection and emotional stability. Its slight curve suggests a balance between emotional expression and control, without the excesses of jealousy or coldness."* | `cheiroslanguageo00chei_1_p160_c2` (SHARED trailing tag with the following sentence — a V-1 sandwich-gap instance, accepted gap (b)) | **No.** Verified: `p160_c2`'s full text (quoted in the evidence file) never contains "stability" or any synonym. |
| 10:41:49 | Run B attempt 1 | *"...indicates a capacity for deep affection and emotional stability, with a slight upward curve suggesting warmth and a positive outlook in matters of the heart."* | `cheiroslanguageo00chei_1_p160_c2` (own dedicated tag) | **No.** Same chunk, same verified absence. |

**Datum for S69**: in 2 of 3 fail-closed attempts, "stability" is cited to
the SAME heart-line chunk (`p160_c2`) that never contains it — the term is
model-generated summary vocabulary, not drawn from retrieved doctrine, in
every single occurrence across all 3 failed attempts AND (per Run A/B/C's
own final "stable"/"steady" word choices in the scored ledgers above) a
recurring generation habit for this prompt shape generally. Since the
blacklist hit is not chunk-driven, a fresh regeneration (not a
retrieval change) is what resolves it — consistent with the observed
behavior (manual re-click succeeded both times). Routes an S69 question:
should the F2c retry feedback explicitly name the SPECIFIC offending
word(s) more prominently, or is a 3rd attempt (raising the hard cap)
worth considering given this evidence that the failure mode is
composition-habit-driven, not retrieval-driven? Not decided here.

## P7 — Vision fidelity

**RATIFIED (2026-07-19, design chat).** The S65/S66 F1 human-checkpoint UI
was exercised procedurally for all 3 runs (LEFT, RIGHT, and Run C's
HAND_DETAIL each displayed and confirmed before generation) on FRESH
2026-07-19 uploads — and, per adjudication #5's own standard (procedural
confirmation alone is not sign-off), the user reviewed those same fresh
uploads and confirmed the descriptions against them in design chat, with
design chat proceeding to this close-out on that basis. Same standard as
pass-3's own P7 ratification (user review + design-chat proceed = sign-off,
not the F1 UI pass alone). **P7: OK.**

## Verdict

**Ratification bar (unchanged from pass 1-3): Runs A, B, C ALL score 4/4
on P1-P4, P7 OK/minor. Literal scoring only.**

| Run | P1 | P2 | P3 | P4 | Score |
|---|---|---|---|---|---|
| A | N | Y | Y | N | 2/4 |
| B | N | Y | Y | N | 2/4 |
| C | N | Y | Y | N | 2/4 |

- [ ] RATIFIED-LIVE
- [x] NOT RATIFIED (2026-07-19, design chat)

**No run reaches 4/4.** P4 fails on all 3 runs via the NEW S68 warnings-
block-P4-clean mechanical rule (adjudication #1) — this is a rule
consequence, not new evidence of worse behavior on its own (the user is
never shown fabricated markings content in any run). P1 fails on all 3
runs via a substantive, evidence-heavy U-pattern that is, on the numbers,
WORSE than pass 3 (pass-3 Run A: 4 U-rows; this pass: 11/10/10 U-rows for
A/B/C respectively) — driven by a genuinely new failure shape (un-anchored
doctrine
`[OBS]` rows, Finding 3) and a CONFIRMED inversion (Finding 4, Run B row
14) neither of which pass 3 observed in this exact form. P7 is RATIFIED
(OK) — the P1/P4 gaps are the sole blockers on the ratification bar, same
framing pass-3 used.

**Progress vs. pass 3** (context, not a scoring input): life line and
Mount of Venus remain solidly load-bearing C rows in all 3 runs, same as
pass 3. Fingers is newly, genuinely C-supported in Run C (a real
improvement over pass 3, where fingers had no positive citation in any
run) — but the SAME claim type inverts in Run A/B via a different cited
chunk (Finding 2), so this is not an unambiguous net gain. The A1 tagging
contract itself performed exactly as designed across all 6 captured
attempts (3 scored + 3 fail-closed) — every sentence tagged, every anchor
resolvable, the coverage mechanism firing correctly on the one genuinely
supported-but-uncited feature in all 3 runs.

**Re-open condition** (unchanged): any post-ratification live T4 failure
reopens Ring 3 at N=5.
