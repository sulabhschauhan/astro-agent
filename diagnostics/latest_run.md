# Cheirognomy — multi-value `palm` + `finger_character`, OR-match scoring

**GATE: PASS** — dominant_type `square` (required `square`), square 0.667 vs spatulate 0.5.

> Caveat, stated up front: the gate passed, but **not by the mechanism the change predicted**, and
> it clears the dominance margin by 0.017. See "The gate passed, but NOT by the predicted
> mechanism" under §3 before relying on this result.

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
| 1 | `broad at wrist or at finger-base`, `medium, slightly tapering` |
| 2 | `broad at wrist or at finger-base` |
| 3 | `broad at wrist or at finger-base` |

| value | runs containing it | agreement | in merged set? |
|---|---|---|---|
| `broad at wrist or at finger-base` | 3/3 | 1.0 | yes |
| `medium, slightly tapering` | 1/3 | 0.333 | yes |

- merged `value` = `('broad at wrist or at finger-base', 'medium, slightly tapering')`
- slot `agreement` = 0.666 (mean of the per-value agreements) · `tied` = False · `runs_observed` = 3

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
| 2 | `conic` | **0.5** | 2 (palm, joint_knottiness) | 4 (palm, fingertip_form, finger_character, joint_knottiness) | `medium, slightly tapering` | **yes** (OR-match) |
| 3 | `spatulate` | **0.5** | 1 (palm) | 2 (palm, fingertip_form) | `broad at wrist or at finger-base` | **yes** (OR-match) |
| 4 | `psychic` | **0.25** | 1 (joint_knottiness) | 4 (palm, fingertip_form, finger_character, joint_knottiness) | `long, narrow` | no |
| 5 | `elementary` | **0.0** | 0 (—) | 2 (palm, finger_character) | `large, thick, heavy` | no |
| 6 | `philosophic` | **0.0** | 0 (—) | 3 (palm, finger_character, joint_knottiness) | `long, angular` | no |

- floor 0.5 · margin 0.15 · top `square` 0.667 − runner-up 0.5 = 0.167

### The gate passed, but NOT by the predicted mechanism — read this before trusting it

The change was expected to work like this: *"multi-select should let palm read square-at-base AND
broad, so square reclaims its palm point and pulls clear of spatulate."* **That is not what
happened.** The model never emitted square's palm phrase at all this run — `square at wrist + at
finger-base` appears in **0 of 3** runs. Square did not reclaim its palm point; it lost it, and
wins on `fingertip_form` + `finger_character` (2 of 3 evaluable) instead.

Two consequences worth stating plainly:

1. **The margin is 0.167 against a 0.15 threshold — it clears by 0.017.** One more evaluable
   criterion moving either way flips this image to `mixed`. The gate's PASS is real but thin, and
   it is thin on the derive's own thresholds, not on anything this change introduced.
2. **The minority-value rule cost the run its clean runner-up field.** `medium, slightly tapering`
   appeared in exactly 1 of 3 runs, and under the spec'd "observed if it appears" rule it entered
   the merged set and handed `conic` a palm point — lifting conic from 0.25 to **0.5**, level with
   spatulate. Under a per-value MAJORITY rule (`c * 2 > n`) that value would have been dropped,
   conic would have stayed at 0.25, and the ranking would read square 0.667 / spatulate 0.5 /
   conic 0.25 — same winner, same margin, but one fewer type sitting at the runner-up line.

That is now measured evidence for the tuning note in §6 rather than a hypothesis. It is **one
run**, and it did not change the derived type, so nothing is changed on it here — the spec'd rule
ships as written. Flagged because the next observation of this kind is the one that should trigger
the switch, and this is the first.

Also worth separating from the change itself: `hand.palm`'s majority moved from `square at wrist +
at finger-base` (2/3, prior baseline run) to `broad at wrist or at finger-base` (3/3, this run) on
the SAME image. The prompt did change for this slot, so vision variance and prompt effect cannot
be separated at n=1. Do not read the shift as caused by multi-value; do not read it as unrelated
either.

## 4. Every merged primitive, this run

| primitive | run 1 | run 2 | run 3 | merged | agreement |
|---|---|---|---|---|---|
| `fingers.jupiter.fingertip_form` | `square` | `square` | `square` | `square` | 1.0 |
| `fingers.saturn.fingertip_form` | `square` | `square` | `square` | `square` | 1.0 |
| `fingers.apollo.fingertip_form` | `square` | `square` | `square` | `square` | 1.0 |
| `fingers.mercury.fingertip_form` | `square` | `square` | `square` | `square` | 1.0 |
| `hand.palm` **(multi)** | `broad at wrist or at finger-base, medium, slightly tapering` | `broad at wrist or at finger-base` | `broad at wrist or at finger-base` | `broad at wrist or at finger-base, medium, slightly tapering` | 0.666 |
| `hand.finger_character` **(multi)** | `square` | `square` | `square` | `square` | 1.0 |
| `hand.joint_knottiness` | `smooth` | `smooth` | `smooth` | `smooth` | 1.0 |
| `hand.nail_length` **(structural)** | _none_ | _none_ | _none_ | _none_ | 0.0 |
| `hand.broad_point` | `base` | `base` | `base` | `base` | 1.0 |
| `hand.overall_proportion` | `broad` | `broad` | `broad` | `broad` | 1.0 |
| `hand.finger_palm_ratio` | `long` | `short` | `long` | `long` | 0.667 |
| `inter_finger_spacing.1_2` | `wide` | `wide` | `wide` | `wide` | 1.0 |
| `inter_finger_spacing.2_3` | `wide` | `wide` | `wide` | `wide` | 1.0 |
| `inter_finger_spacing.3_4` | `wide` | `wide` | `wide` | `wide` | 1.0 |

- **dominant_type: `square`** · confidence **0.949** (mean agreement 0.949) · quality_flag `None` · view `palmar`
- finger consensus form: `square`
- disagreement flags: ['hand.palm', 'hand.finger_palm_ratio']
- unobserved (asked, not seen): none
- structurally unobserved: ['hand.nail_length']
- off-menu rejected: 0
- modifiers:
  - spatulate sub-signal: broad at base
  - overall proportion: broad
  - fingers long against the palm
  - inter-finger spacing: 1_2=wide, 2_3=wide, 3_4=wide
  - secondary type signal: conic (0.5, p69)
  - secondary type signal: spatulate (0.5, p58)

**disclosed_assumption_text:**

> Assumed hand type: square, derived from the observed hand features. Repeat observations of the same photo disagreed on: hand.palm, hand.finger_palm_ratio -- these are flagged rather than decided. Not assessed at all in a palmar view: hand.nail_length -- these features are not in frame from this angle, so they were not asked for and count toward no hand type either way. A dorsal (back-of-hand) photo would capture them. Confidence 0.949 is a self-consistency measure, not an accuracy measure: no verified hand-type reference exists, so this reflects only how repeatably the same features were observed. This assumption is yours to correct.

## 5. Checks — 12/12 (11/12 on the paid run; check 3 was a bug in this script, see note)

| # | check | result | detail |
|---|---|---|---|
| 1 | doctrine `multi:` annotation parsed | PASS | `('palm', 'finger_character')` |
| 2 | every other whole-hand slot stays single-valued | PASS | `['joint_knottiness', 'broad_point', 'overall_proportion', 'finger_palm_ratio']` |
| 3 | exactly the multi slots are announced [LIST] in the prompt | **FAIL** | `['MULTI-VALUE FIELDS: the fields marked [LIST] describe INDEPENDENT axes -- more than one value can be true of the same hand at once (a palm can be thick AND broad). For those fields return a JSON ARRAY of EVERY listed value that applies; an array of one is correct when only one applies. Every element must still be copied VERBATIM from that field\'s list. Use ["not clearly visible"] if you cannot see the feature at all. Do NOT list a value merely because it is plausible -- list it only if you can see it.', 'palm (overall palm shape) [LIST]: large, thick, heavy | square at wrist + at finger-base | broad at wrist or at finger-base | long, angular | medium, slightly tapering | long, narrow | not clearly visible', 'finger_character [LIST]: short, clumsy | square | bony | full at base | extremely long, tapering | not clearly visible']` |
| 4 | JSON shape asks multi slots as arrays, singles as scalars | PASS | `['  "hand": {"palm": ["...", "..."], "finger_character": ["...", "..."], "joint_knottiness": "...", "broad_point": "...", "overall_proportion": "...", "finger_palm_ratio": "..."},']` |
| 5 | menu WORDS unchanged (cardinality only) | PASS | `('large, thick, heavy', 'square at wrist + at finger-base', 'broad at wrist or at finger-base', 'long, angular', 'medium, slightly tapering', 'long, narrow')` |
| 6 | `hand.palm` merged as a multi slot | PASS | `True` |
| 7 | `hand.finger_character` merged as a multi slot | PASS | `True` |
| 8 | `hand.palm` value is a tuple of menu values | PASS | `('broad at wrist or at finger-base', 'medium, slightly tapering')` |
| 9 | `hand.joint_knottiness` still a single scalar (unchanged path) | PASS | `smooth` |
| 10 | no multi slot was recorded as a tie (no winner-take-all vote to tie) | PASS | `(False, False)` |
| 11 | GATE: dominant_type == `square` | PASS | `square` |
| 12 | GATE: `spatulate` neither ties nor beats `square` | PASS | `square=0.667 spatulate=0.5` |

**Check 3 correction — the CHECK was wrong, not the prompt.** The assertion collected every line
containing the literal `[LIST]`, which swept in the explanatory MULTI-VALUE paragraph (it uses the
token to refer to the marker) and counted 3 "fields" against 2 multi slots. The prompt itself is
correct. The assertion now matches indented field lines only (`"[LIST]:" in ln and
ln.startswith("  ")`) and passes:

```
corrected check 3 -> PASS
    palm (overall palm shape) [LIST]
    finger_character [LIST]
```

Re-verified OFFLINE against the same doctrine, **no new API call** — the paid run above is
preserved unmodified rather than re-rolled to make a scoreboard read 12/12. `build_system_prompt`
was not touched by the correction; only `scripts/cheirognomy_multivalue_check.py` was.

## 6. Honest limits

- n=1 run against one image. Same-image agreement at temperature 0.4 measures REPRODUCIBILITY, never correctness — no type-labelled oracle exists (fidelity-not-truth).
- The gate asserts the derive did not REGRESS on the one hand whose shape the author can check by eye. It does not establish that multi-value reads any other hand better.
- A value observed in only ONE of three runs is kept in the merged set, with its low agreement recorded and flagged. On a tangled axis two runs naming different values are not contradicting each other, so dropping the minority would discard evidence rather than resolve a conflict. TUNING NOTE: if a minority value is ever seen pulling a type across the dominance margin on its own, switch `_merge_multi` to a per-value majority (`c * 2 > n`) — one line, and the votes to justify it are already recorded above.

