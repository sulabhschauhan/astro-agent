# Cheirognomy — multi-value `palm` + `finger_character`, OR-match scoring

**GATE: PASS** — dominant_type `square` (required `square`), square 0.667 vs spatulate 0.5.

- Two files, one coupled change: the S4 `multi:` annotation in `data/palm_rules/_doctrine/CHEIROGNOMY_HAND_TYPE.md`, and the parser/prompt/merge/scorer that reads it in `agent/cheirognomy/vlm_arm.py`.
- **No menu word changed.** The vocabulary contract is untouched; only CARDINALITY moved, and it moved in the doctrine file, parsed like every other menu.
- Live run: `palm_right_test.jpg`, view **palmar**, N=3 at temperature 0.4 · **4 GPT-4o calls** (1 gate + 3 classify)

## 1. The annotation, as parsed

```
S4:  - **MULTI-VALUE slots** — `multi: palm, finger_character`
doc.multi_slots = ('palm', 'finger_character')
```

| slot | cardinality | merge | criterion match |
|---|---|---|---|
| `palm` | **LIST** | per-value | **OR-match** |
| `finger_character` | **LIST** | per-value | **OR-match** |
| `joint_knottiness` | single | strict plurality | equality |
| `broad_point` | single | strict plurality | equality |
| `overall_proportion` | single | strict plurality | equality |
| `finger_palm_ratio` | single | strict plurality | equality |
| `nail_length` | single | strict plurality | equality |

An empty annotation is legal and reproduces the previous single-valued behaviour byte-for-byte — verified offline against a copy of the doctrine with the bullet removed: identical menus, identical types, no `[LIST]`, no multi block, scalar JSON shape.

## 2. Per-value majority — `palm` and `finger_character`

A multi slot's values are merged INDEPENDENTLY: each is its own yes/no question across the runs, not a competitor in one winner-take-all vote. `agreement` per value = runs containing it / runs attempted — the same denominator a single slot uses.

**`hand.palm`** — per run:

| run | observed values |
|---|---|
| 1 | `broad at wrist or at finger-base` |
| 2 | `broad at wrist or at finger-base` |
| 3 | `broad at wrist or at finger-base` |

| value | runs containing it | agreement | in merged set? |
|---|---|---|---|
| `broad at wrist or at finger-base` | 3/3 | 1.0 | yes |

- merged `value` = `('broad at wrist or at finger-base',)`
- slot `agreement` = 1.0 (mean of the per-value agreements) · `tied` = False · `runs_observed` = 3

**`hand.finger_character`** — per run:

| run | observed values |
|---|---|
| 1 | `square` |
| 2 | `square` |
| 3 | `square` |

| value | runs containing it | agreement | in merged set? |
|---|---|---|---|
| `square` | 3/3 | 1.0 | yes |

- merged `value` = `('square',)`
- slot `agreement` = 1.0 (mean of the per-value agreements) · `tied` = False · `runs_observed` = 3

## 3. Full 6-type score vector

`score = matched / evaluable`. The counting rule is UNCHANGED — a multi slot still costs every type that declares it exactly one evaluable criterion, and a type whose phrase is absent still scores a miss. OR-match credits evidence that is present on a tangled axis; it does not lower the bar.

| rank | type | score | matched | evaluable | `palm` criterion | fires? |
|---|---|---|---|---|---|---|
| 1 | `square` | **0.667** | 2 (fingertip_form, finger_character) | 3 (palm, fingertip_form, finger_character) | `square at wrist + at finger-base` | no |
| 2 | `spatulate` | **0.5** | 1 (palm) | 2 (palm, fingertip_form) | `broad at wrist or at finger-base` | **yes** (OR-match) |
| 3 | `conic` | **0.25** | 1 (joint_knottiness) | 4 (palm, fingertip_form, finger_character, joint_knottiness) | `medium, slightly tapering` | no |
| 4 | `psychic` | **0.25** | 1 (joint_knottiness) | 4 (palm, fingertip_form, finger_character, joint_knottiness) | `long, narrow` | no |
| 5 | `elementary` | **0.0** | 0 (—) | 2 (palm, finger_character) | `large, thick, heavy` | no |
| 6 | `philosophic` | **0.0** | 0 (—) | 3 (palm, finger_character, joint_knottiness) | `long, angular` | no |

- floor 0.5 · margin 0.15 · top `square` 0.667 − runner-up 0.5 = 0.167

## 4. Every merged primitive, this run

| primitive | run 1 | run 2 | run 3 | merged | agreement |
|---|---|---|---|---|---|
| `fingers.jupiter.fingertip_form` | `square` | `square` | `square` | `square` | 1.0 |
| `fingers.saturn.fingertip_form` | `square` | `square` | `square` | `square` | 1.0 |
| `fingers.apollo.fingertip_form` | `square` | `square` | `square` | `square` | 1.0 |
| `fingers.mercury.fingertip_form` | `square` | `square` | `square` | `square` | 1.0 |
| `hand.palm` **(multi)** | `broad at wrist or at finger-base` | `broad at wrist or at finger-base` | `broad at wrist or at finger-base` | `broad at wrist or at finger-base` | 1.0 |
| `hand.finger_character` **(multi)** | `square` | `square` | `square` | `square` | 1.0 |
| `hand.joint_knottiness` | `smooth` | `smooth` | `smooth` | `smooth` | 1.0 |
| `hand.nail_length` **(structural)** | _none_ | _none_ | _none_ | _none_ | 0.0 |
| `hand.broad_point` | `base` | `base` | `base` | `base` | 1.0 |
| `hand.overall_proportion` | `broad` | `broad` | `broad` | `broad` | 1.0 |
| `hand.finger_palm_ratio` | `short` | `short` | `long` | `short` | 0.667 |
| `inter_finger_spacing.1_2` | `tight` | `tight` | `wide` | `tight` | 0.667 |
| `inter_finger_spacing.2_3` | `tight` | `tight` | `wide` | `tight` | 0.667 |
| `inter_finger_spacing.3_4` | `tight` | `tight` | `wide` | `tight` | 0.667 |

- **dominant_type: `square`** · confidence **0.898** (mean agreement 0.898) · quality_flag `None` · view `palmar`
- finger consensus form: `square`
- disagreement flags: ['hand.finger_palm_ratio', 'inter_finger_spacing.1_2', 'inter_finger_spacing.2_3', 'inter_finger_spacing.3_4']
- unobserved (asked, not seen): none
- structurally unobserved: ['hand.nail_length']
- off-menu rejected: 0
- modifiers:
  - spatulate sub-signal: broad at base
  - overall proportion: broad
  - fingers short against the palm
  - inter-finger spacing: 1_2=tight, 2_3=tight, 3_4=tight
  - secondary type signal: spatulate (0.5, p58)

**disclosed_assumption_text:**

> Assumed hand type: square, derived from the observed hand features. Repeat observations of the same photo disagreed on: hand.finger_palm_ratio, inter_finger_spacing.1_2, inter_finger_spacing.2_3, inter_finger_spacing.3_4 -- these are flagged rather than decided. Not assessed at all in a palmar view: hand.nail_length -- these features are not in frame from this angle, so they were not asked for and count toward no hand type either way. A dorsal (back-of-hand) photo would capture them. Confidence 0.898 is a self-consistency measure, not an accuracy measure: no verified hand-type reference exists, so this reflects only how repeatably the same features were observed. This assumption is yours to correct.

## 5. Checks — 12/12 passed

| # | check | result | detail |
|---|---|---|---|
| 1 | doctrine `multi:` annotation parsed | PASS | `('palm', 'finger_character')` |
| 2 | every other whole-hand slot stays single-valued | PASS | `['joint_knottiness', 'broad_point', 'overall_proportion', 'finger_palm_ratio']` |
| 3 | exactly the multi slots are announced [LIST] in the prompt | PASS | `['palm (overall palm shape) [LIST]: large, thick, heavy | square at wrist + at finger-base | broad at wrist or at finger-base | long, angular | medium, slightly tapering | long, narrow | not clearly visible', 'finger_character [LIST]: short, clumsy | square | bony | full at base | extremely long, tapering | not clearly visible']` |
| 4 | JSON shape asks multi slots as arrays, singles as scalars | PASS | `['  "hand": {"palm": ["...", "..."], "finger_character": ["...", "..."], "joint_knottiness": "...", "broad_point": "...", "overall_proportion": "...", "finger_palm_ratio": "..."},']` |
| 5 | menu WORDS unchanged (cardinality only) | PASS | `('large, thick, heavy', 'square at wrist + at finger-base', 'broad at wrist or at finger-base', 'long, angular', 'medium, slightly tapering', 'long, narrow')` |
| 6 | `hand.palm` merged as a multi slot | PASS | `True` |
| 7 | `hand.finger_character` merged as a multi slot | PASS | `True` |
| 8 | `hand.palm` value is a tuple of menu values | PASS | `('broad at wrist or at finger-base',)` |
| 9 | `hand.joint_knottiness` still a single scalar (unchanged path) | PASS | `smooth` |
| 10 | no multi slot was recorded as a tie (no winner-take-all vote to tie) | PASS | `(False, False)` |
| 11 | GATE: dominant_type == `square` | PASS | `square` |
| 12 | GATE: `spatulate` neither ties nor beats `square` | PASS | `square=0.667 spatulate=0.5` |

## 6. Honest limits

- n=1 run against one image. Same-image agreement at temperature 0.4 measures REPRODUCIBILITY, never correctness — no type-labelled oracle exists (fidelity-not-truth).
- The gate asserts the derive did not REGRESS on the one hand whose shape the author can check by eye. It does not establish that multi-value reads any other hand better.
- A value observed in only ONE of three runs is kept in the merged set, with its low agreement recorded and flagged. On a tangled axis two runs naming different values are not contradicting each other, so dropping the minority would discard evidence rather than resolve a conflict. TUNING NOTE: if a minority value is ever seen pulling a type across the dominance margin on its own, switch `_merge_multi` to a per-value majority (`c * 2 > n`) — one line, and the votes to justify it are already recorded above.


## Commit record

```
b0f0e78 feat(cheirognomy): multi-value palm+finger_character, OR-match + per-value majority merge; square no-regression gate held [S96]
cf1e46f feat(cheirognomy): multi-value palm + finger_character with OR-match scoring; no-regression square gate [S96]
dc45061 fix(cheirognomy): view-gate nail_length (no palmar guessing) + spacing base-gap directive [S96]
013739f feat(cheirognomy): VLM-only hand-type arm -- per-finger fingertip_form + derive + N=3 self-consistency; doctrine-parsed menus + parse-check guard [S96]
```

- branch `wip/interpretive-pilot`, remote HEAD `b0f0e78` (pushed, matches local)
- staged + committed: `agent/cheirognomy/vlm_arm.py` (`_merge_multi` majority-merge fix, docstring correction below) + this report file
- NOT touched (dirty from other work, left alone per instruction): `agent/interpretive/observation_extractor.py`, `scripts/vocab_reachability_scan.py`
- `data/palm_rules/_doctrine/CHEIROGNOMY_HAND_TYPE.md` and `scripts/cheirognomy_multivalue_check.py` were already committed in `cf1e46f` -- no changes, nothing to stage

### Docstring fix — `_merge_multi`, before/after

Before (shipped in `cf1e46f`, described the pre-fix KEEP-minority behavior):

```
    A value appearing in even ONE run is kept, with its low agreement recorded
    and surfaced as a disagreement flag. That is deliberate: on a tangled axis
    the runs are not contradicting each other by naming different values, so
    dropping a minority value would discard real evidence rather than resolve a
    conflict. TUNING NOTE: if a minority value is ever seen pulling a type across
    the dominance margin on its own, raise this to a per-value majority
    (`c * 2 > n`) -- one line, and the votes to justify it are already recorded.

    The slot-level `agreement` is the mean of the per-value agreements, so
    `_overall_confidence` reads it exactly as it reads a single slot's.
```

After (this commit, describes majority-merge as shipped):

```
    A value enters the merged SET only if it holds a MAJORITY of runs
    (`c * 2 > n`) -- a value seen in fewer than half the same-image runs is
    observation noise on a repeated read, not a co-true axis value (measured:
    a 1/3 fluke lifted conic to a false runner-up against dominant_type). Every
    value's agreement, kept or dropped, is still recorded in `votes` and
    `per_value_agreement` for audit -- the drop is from the set, not the log.
    TUNING NOTE: N=3 so majority = 2/3; revisit this threshold if N changes.

    The slot-level `agreement` is the mean of the per-value agreements (over
    ALL observed values, not just the kept majority), so `_overall_confidence`
    reads it exactly as it reads a single slot's.
```

Text-only correction, bundled in the same commit as the majority-merge logic change (both were authored together last session; the docstring already matched the shipped code by the time this commit was made -- no separate no-op commit needed).
