# Ring 3 — T4 Human-Rubric Ratification Artifact (Session 70/71) — Pass 5

**STATUS: SCORED — pass 5, verdict NOT RATIFIED (2026-07-24). Frozen
record; keep forever.**

This artifact is the REVERSAL record, not a ratification artifact. It
was opened at S71 when it was discovered that no row-level rubric
artifact for pass 5 had ever been written — the S70 close-out's "4/4"
claim (CLAUDE.md's now-superseded T4 RATIFIED-LIVE entry) stood on prose
alone, backed only by `diagnostics/pass5_preflight_S70.md` (an explicitly
labeled throwaway wiring probe on fixture images: "says nothing about
interpretive quality/citation accuracy — that is Ring 3 pass 5's job,
human-scored") and `diagnostics/dogfood_capture.md`'s raw captures,
neither of which is a row-by-row human ledger. This artifact is that
ledger, for Run A only — see the Run B/C section below for why B/C were
not scored.

Preconditions: same as the (reversed) S70 ratification — S70 P6a
(`be64da6`, F5 capture schema), P6b (`27889c1`, two-mode Stage-1
checkpoint), F-E (`84c49f1`, comma-tolerant absence filler groups), F-G1-4
(`eb2c891`/`34c7e6f`/`4b6d15a`/`f94cecb`) all live. Evidence surface:
`diagnostics/dogfood_capture.md` directly (Run A: `## RUN
2026-07-23T18:42:14.473283`) — this pass's capture schema carries a
`claims_inventory` (claim id | feature | chunk_id | valence |
excluded_from_voice | exclusion_reason | condition_text | claim_text)
produced by Stage 1 (`claim_extraction.py`) before voicing, rather than
pass-4's reconstructed-from-tagged-prose evidence file. The ledger below
verifies each `READING (TAGGED)` clause against its claims_inventory row
directly.

Rubric lineage: `ring3_palm_rubric_S68_pass4.md` — same P1-P4 rubric,
same compound-sentence split rule (observational core = D; trait/
doctrine tail = C only if literally present in the cited claims_
inventory text, else U → FAIL), same summary-row convention (a `[FLOW]`
summary restating a prior U-scored claim without new citation is itself
U → FAIL).

**Verify-before-transcribe**: every clause, chunk_id, and claims_
inventory text below was read directly from `diagnostics/
dogfood_capture.md` in this session — NOT transcribed from `.claude/
read_prompt.md`'s in-progress draft (which independently reached the
same Run A tally and rubric scores; used only as a cross-check, not as
the source of record). One correction made to the task that opened this
session and recorded here, not silently fixed: the instructing task
cited "pass-4 Run A row 8" as row 5's precedent; pass-4's own row 8 is
an unrelated heart-line/`p160_c2` row. The correct precedent is pass-4
Run A **row 4**, whose own text cites pass-3 Run A row 8 — a two-hop
citation the task conflated into one hop. Corrected before scoring.

## Run plan

- **Run A (baseline)** — both hands, no HAND_DETAIL — `## RUN
  2026-07-23T18:42:14.473283`. `retry_used: True` (`stage1_retry_
  features: thumb`, `stage2_retry_used: True`). **SCORED (this
  artifact).**
- **Run B (identical-input regenerate)** — `## RUN
  2026-07-23T18:43:13.277529`. **NOT SCORED THIS ARTIFACT** — see below.
- **Run C (+HAND_DETAIL)** — `## RUN 2026-07-23T18:44:11.215275`. **NOT
  SCORED THIS ARTIFACT** — see below.

## Confirmed descriptions (verbatim, Run A, from `dogfood_capture.md`)

**LEFT**:
```
HAND SHAPE: Square palm, overall build is medium.
FINGERS: Fingers are long relative to the palm, appear straight, with rounded fingertips, and moderate spacing.
THUMB: Medium relative size, set moderately low, wide angle from the palm.
LIFE LINE: Present, deep, long, curves around the base of the thumb, no clear breaks, chains, forks, or islands visible.
HEAD LINE: Present, deep, long, slightly curved, no clear breaks, chains, forks, or islands visible.
HEART LINE: Present, deep, long, slightly curved, no clear breaks, chains, forks, or islands visible.
FATE LINE: Barely visible.
OTHER LINES: No other lines clearly visible.
MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.
MARKS: No marks clearly visible.
```

**RIGHT**:
```
HAND SHAPE: elongated palm, medium build
FINGERS: medium length relative to palm, straight, rounded fingertips, moderate spacing
THUMB: medium size, low set, wide angle from the palm
LIFE LINE: present, deep, long, curves around the base of the thumb, no clear breaks or forks
HEAD LINE: present, deep, long, slightly curved, no clear breaks or forks
HEART LINE: present, deep, long, curves slightly upward, no clear breaks or forks
FATE LINE: not clearly visible
OTHER LINES: no other lines clearly visible
MOUNTS: mount of Venus appears developed, other mounts not clearly visible
MARKS: no marks clearly visible
```

## claims_inventory (Run A, verbatim)

```
C1 | life line | cheiroslanguageo00chei_1_p134_c1 | supports | False | None | None | A long, deep, and narrow line of life without irregularities promises long life, good health, and vitality.
C2 | life line | cheiroslanguageo00chei_1_p139_c0 | supports | False | None | None | When the line of life sweeps far out into the hand, it is a sign of good physical strength and long life.
C3 | head line | cheiroslanguageo00chei_1_p145_c0 | supports | False | None | None | The line of head relates principally to the mentality of the subject, including intellectual strength or weakness and the direction and quality of talent.
C4 | fingers | cheiroslanguageo00chei_1_p98_c1 | corrective | False | None | None | The statement that in every case the fingers must be longer than the palm is erroneous and misleading.
C5 | mount of venus | cheiroslanguageo00chei_1_p112_c0 | supports | False | None | None | A well-developed Mount of Venus indicates strong and robust health.
```

(`thumb` retried at Stage 1 — `stage1_retry_features: thumb` — and still
produced no usable claim: a legitimate per-claim decline, not a coverage-
warning firing. No C6+ claim exists for thumb.)

## Run A — claim ledger

| # | Clause | Anchor | Verified? |
|---|---|---|---|
| 1 | "The line of life on your hand is both long and deep, curving gracefully around the base of your thumb without any breaks or irregularities." | [OBS] | D — restates confirmed LIFE LINE field. |
| 2 | "This formation promises you a long life, accompanied by good health and vitality." | [C1] `p134_c1` | **C** — claims_inventory C1: "A long, deep, and narrow line of life without irregularities promises long life, good health, and vitality." Direct match (the voiced sentence drops "narrow," which is not itself asserted, so no over-claim). |
| 3 | "Furthermore, the way this line sweeps far out into your hand is a testament to your good physical strength and the likelihood of a long life." | [C2] `p139_c0` | **U → FAIL, precondition mismatch** — claims_inventory C2 states a CONDITIONAL doctrine ("When the line of life sweeps far out into the hand..."), but neither hand's LIFE LINE field confirms "sweeps far out" — both describe the line only as "curves around the base of the thumb," a different physical configuration. Stage 1 labeled this `valence="supports"` (not "conditional", `condition_text=None`) despite the claim text itself carrying an unstated precondition — same self-contradicting-label pattern as row 5's C3. The voiced sentence asserts the precondition as if directly observed. |
| 4 | "Turning to the line of head, it is also present, deep, and long, with a slight curve and no breaks." | [OBS] | D — restates confirmed HEAD LINE field. |
| 5 | "This line speaks to your mental faculties, indicating intellectual strength and the quality of your talents." | [C3] `p145_c0` | **U → FAIL** — claims_inventory C3: "The line of head relates principally to the mentality of the subject, including intellectual strength **or weakness** and the direction and quality of talent." Neutral naming/taxonomy text, no valence assigned; the voiced sentence asserts one-sided positive valence ("indicating intellectual strength"), dropping the "or weakness" hedge the cited claim text itself preserves. Identical chunk, identical defect as pass-4 Run A row 4, which itself cites pass-3 Run A row 8 as the same defect's first occurrence — third consecutive pass to hit this. Stage-1's `valence="supports"` label was weighed as a possible distinguisher (design-chat ADJ-B) and ruled NOT dispositive: the label contradicts its own claim_text, so it carries no adjudicative weight. Full three-option adjudication (ADJ-A/B/C) recorded in SESSION_LOG.md S71; ADJ-A (uphold U) was adopted. |
| 6 | "The Mount of Venus on your hand is well-developed, which is a strong indicator of robust health." | [C5] `p112_c0` | **C** — claims_inventory C5: "A well-developed Mount of Venus indicates strong and robust health." Direct match. |
| 7 | "This complements the overall vitality indicated by your hand." | [FLOW] | D-frame — pure connective, no new doctrine claim. Retry-corrected form of a first-draft sentence that failed `doctrine_guard` for naming the "life" feature-noun (`stage2_first_attempt_failures`); the retry generalized it to "your hand," removing the mention. |
| 8 | "Your fingers are long relative to your palm, but it is important to note that the belief that fingers must always be longer than the palm is a misconception." | [C4] `p98_c1` | **C** — claims_inventory C4 (valence: corrective): "The statement that in every case the fingers must be longer than the palm is erroneous and misleading." Direct match, correctly voiced as a corrective claim. |
| 9 | "This observation should not mislead you about the significance of your hand's proportions." | [FLOW] | D-frame — pure connective, extends row 8's already-C-verified claim. |
| 10 | "Overall, your hand reveals a picture of strength, vitality, and intellectual capability." | [FLOW] | **U → FAIL** — restates row 3's U-scored "physical strength" claim and row 5's U-scored "intellectual" claim with no new citation. Same summary-row convention as pass-4 (Run A row 16). |

**Run A tally: 3 C rows (2, 6, 8), 4 D/D-frame rows (1, 4, 7, 9), 3 U
rows (3, 5, 10) → P1 FAIL.** Notably fewer U-rows than pass-4's
equivalent run (pass-4 Run A: 11 U-rows; this run: 3, out of 10 tagged
clauses vs. pass-4's 16) — the two-stage extract-then-voice architecture
(F-H) produces a tighter, less elaborated claim set, but does not close
the `p145_c0` defect class it inherited unchanged from pass-3/4, and
surfaces a second instance of the same self-contradicting-valence pattern
on a different chunk (row 3/C2).

## Run A — rubric

| Signal | Score | Justification |
|---|---|---|
| P1 Grounding | **N** | 3 U-class rows: row 3 (precondition never confirmed), row 5 (recurring neutral-chunk-as-positive defect, identical to pass-3/pass-4), row 10 (summary restating both). Life line's primary claim (row 2), Mount of Venus (row 6), and the fingers corrective claim (row 8) are solidly C. |
| P2 No contradiction | **Y** | All D-basis claims (rows 1, 4) trace cleanly to confirmed fields; no direct contradictions found. Rows 3/5 are precondition-mismatch / unsupported-valence issues (P1 concerns), not stated contradictions of a confirmed field. |
| P3 Voice | **Y** | `ring1_validation`: `passed=True`, `failures=()` on the retried final draft. |
| P4 No silent clause-dropping | **Y** | `validation_failures: NONE`. Note (not a failure): `feature_support` lists `heart line`, `fate line`, `thumb` as `supported_features`, yet the final reading's decline note lists all three as not interpreted (alongside `sun line`, `mount of jupiter`, genuinely unsupported). `stage1_retry_features: thumb` shows Stage 1 retried thumb extraction and still produced no usable claim — a legitimate per-claim decline (V-4, per S69 F-H), not the old coverage-warning mechanism firing (retired this pass, superseded by Stage 2's own V-4 claim-coverage check). No fabricated content reaches the user either way. |

**Run A score: 3/4 — below the 4/4 ratification bar** (P1 alone fails
it; P2/P3/P4 all clean).

## Run A — Ring 1 spot-check

Fields reported verbatim (this pass's schema does not expose pass-4's
old per-item checklist — DISCLAIMER/jargon/dates/word-count/etc. are not
discrete fields in `dogfood_capture.md`'s new format; not reconstructed
or guessed at):
- `passed: True`
- `failures: ()`
- `retry_used: True`
- `stage1_retry_features: thumb`
- `stage2_retry_used: True`
- `stage2_first_attempt_failures: doctrine_guard: [FLOW] sentence mentions feature-noun 'life': 'This feature complements the vitality suggested by your life line.'`
- `validation_failures: NONE`
- `ring1_failures: none`

## Run B / Run C — NOT SCORED THIS ARTIFACT

Design-chat ruling (S71): Run A's P1 FAIL is dispositive on its own, per
pass-4's own precedent that a single run's P1 FAIL fails the entire pass
regardless of the other two runs' scores (pass-4 scored all 3 runs
P1=N/P4=N and still only needed one to fail the ratification bar). Run B
and Run C share BYTE-IDENTICAL LEFT/RIGHT confirmed descriptions with Run
A (per the S70 close-out's own claim, corroborated by the shared
`## RUN` blocks' HEAD LINE fields, all reading "present, deep, long,
slightly curved... no breaks"), meaning both would retrieve and cite the
identical `p145_c0` chunk for the identical head-line claim shape,
producing the same row-5-class defect. Scoring B/C could not change the
P1 FAIL verdict already reached on Run A alone. Left unscored to keep
this artifact scoped to the reversal decision; NOT a claim that B/C are
clean — that remains genuinely unknown and unscored.

## Verdict

**Ratification bar (unchanged from pass 1-4): Runs A, B, C ALL score
4/4 on P1-P4.**

| Run | P1 | P2 | P3 | P4 | Score |
|---|---|---|---|---|---|
| A | N | Y | Y | Y | 3/4 |
| B | — | — | — | — | NOT SCORED |
| C | — | — | — | — | NOT SCORED |

- [ ] RATIFIED-LIVE
- [x] NOT RATIFIED (2026-07-24, design chat)

**Run A alone fails the ratification bar.** This reverses S70's
RATIFIED-LIVE call, which asserted 4/4 across all 3 runs without any
row-level artifact to support the claim. The recurring defect (row 5,
`p145_c0`, three consecutive passes) plus a newly-surfaced second
instance of the same self-contradicting-valence pattern (row 3, `p139_
c0`) suggest this is a corpus-level or Stage-1-extraction-level issue,
not per-pass generation variance — see CLAUDE.md's new Carry-Forward
item.

**Re-open path**: Ring 3 pass 6, fresh uploads (N=3), gated by
design-chat re-litigation of the `p145_c0` recurring defect (see
CLAUDE.md Carry-Forward) before spending a fourth pass on the same
failure. S68/S69's pre-ratification pass cap (5 total) is back in
force; this reversal does not consume a cap slot (pass 5 already did),
so pass 6 is the next and, per the cap, final attempt before mandatory
design-chat re-litigation of the pass cap itself.
