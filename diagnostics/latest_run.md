# S121 — Vision-emittable vs rule-vocabulary mismatch: ROOT-CAUSE + OPEN DESIGN PASS

**Measured at:** `80b457b`, branch `wip/interpretive-pilot`.
**Scope:** report-only findings. No source file, rule file, registry, test or config was edited — the analysis stands unchanged from the report-only pass.
**Probe script:** `probes/vocab_mismatch_audit_S121.py`, committed as **`dbce778`** (pushed) per Working Style #16 — read-only classifier over all 4 rule files, no LLM call, no network, writes nothing unless `--dump` is passed. All numbers below re-verified against the committed copy. See Caveat C4.

---

## 0. Executive summary

FT_001 is not a token typo. It is one instance of a **three-vocabulary drift** that has never had a
contract between its layers:

| # | Vocabulary | Where it lives | Size | Who authored it |
|---|---|---|---|---|
| V1 | **Authoring / book vocabulary** | `data/ontology_registry.json` → `values` | **217 tokens** | harvested from Cheiro's own prose, wholesale, at `d723291` (2026-08-03) |
| V2 | **Vision solicitation vocabulary** | `agent/palm_processor.py::_build_description_system_prompt` | 9 closed menus + free prose for everything else | authored independently, mostly S98–S119 |
| V3 | **Extraction output vocabulary** | what `observation_extractor`'s LLM actually emits per run | a non-deterministic projection of V2 onto V1 | emergent — nobody authored it |

Rules are authored against **V1**. Rules can only fire against **V3**. Every gate in the repo checks
against **V1**. Nothing anywhere checks V1 ⊆ V3.

**Measured blast radius: 36 of 87 live rules (41%) carry at least one antecedent that cannot fire
today**, plus a further 17 antecedents that are emittable in principle but were out-competed by a
sibling token on every hand ever run. `FT_001`/`FT_009` are 2 of the 53.

The mounts file (S117–S119) is the **only** chapter with zero dead antecedents — because it is the
only one authored *vision-out*: its rules key on `_MOUNT_DEVELOPMENT_MENUS` strings
(`"well developed"`, `"present"`), which are **not in V1's value pool at all**. That is the working
pattern, and it is the basis of the recommendation below.

---

## 1. THE MISMATCH INVENTORY (all 4 rule files, all attributes)

Measured over `validated_candidates` in `palm_rules_fate_line_v1.json`,
`palm_rules_head_heart_v1.json`, `palm_rules_life_line_v1.json`, `palm_rules_mounts_v1.json`
(`needs_remodel` skipped). **127 antecedents over 87 rules.**

| Class | Count | Meaning |
|---|---|---|
| `OK-relational` | 23 | relation_target antecedent, registry-legal **and** inside the vision ORIGIN/TERMINATION menu |
| `OK-menu` | 14 | value inside a genuine closed emission menu (`attribute_value_binding` or `_MOUNT_DEVELOPMENT_MENUS`) |
| `OK-observed` | 4 | free-prose token actually observed in a live capture |
| **`D1-FEATURE-UNROUTED`** | **7** | the feature has no `_FEATURE_ALIAS` entry — no vision prose ever routes to it |
| **`D2-DIMENSION-UNSOLICITED`** | **3** | the vision prompt never asks for that dimension on that feature |
| **`D3-TOKEN-ABSENT`** | **5** | the token is not in V1's pool at all (or outside the per-line vision menu) |
| **`D4-DUAL-ENCODING`** | **30** | a relational attribute encoded as a *literal value* instead of a `relation_target` |
| `D5-SYNONYM-OR-STATE` | 17 | solicited + in pool, but every live run produced a **different** token for that (feature, attribute) |
| `D6-UNOBSERVED` | 22 | solicited + in pool, never populated in any live capture |
| `D0-COMPUTED` | 2 | comparative — no vision field emits it (known, S94) |

**Rules with ≥1 structurally-dead antecedent (D1–D4): 36 of 87.**

| file | live rules | dead rules | dead rule ids |
|---|---|---|---|
| `head_heart` | 48 | **32** | HL_001–HL_012, HL_014, HL_015, HL_018–HL_021, H_002, H_003, H_007, H_010a, H_010b, H_013, H_015, H_018–H_021, H_023–H_025 |
| `life_line` | 11 | **4** | L_004, L_005, L_018, L_022 |
| `fate_line` | 16 | 0 | — |
| `mounts` | 12 | 0 | — |

### 1.1 `D1-FEATURE-UNROUTED` (7 antecedents / 5 rules)

| rule | antecedent | why dead |
|---|---|---|
| H_010a, H_010b, HL_006, HL_021 | `Quadrangle.Breadth='narrow'` | `Quadrangle` has no `_FEATURE_ALIAS` entry — no vision prose section ever routes to it |
| H_018, H_019, H_020 | `Hand.Type='square' / 'spatulate' / 'philosophic'` | `Hand` has no alias entry; `Type` is not in `attribute_feature_mapping` at all. This is the hand-type class **formally scoped OUT at S96** |

### 1.2 `D2-DIMENSION-UNSOLICITED` (3 antecedents / 3 rules)

| rule | antecedent | why dead |
|---|---|---|
| HL_019 | `Line of Heart.Color='bright_red'` | the vision prompt asks for **no colour dimension anywhere** — LIFE/HEAD/HEART/FATE blocks list `depth, width, length, direction, breaks/chains/forks/islands`. Colour prose is never produced, so extraction can never fire |
| HL_020 | `Line of Heart.Color='pale'` | same |
| L_022 | `Mount of Venus.Fullness='full'` | mounts are asked only for `DEVELOPMENT` (closed menu) + a bare `MOUNTS:` line; `Fullness` is never solicited |

### 1.3 `D3-TOKEN-ABSENT` (5 antecedents / 4 rules)

| rule | antecedent | why dead |
|---|---|---|
| H_013 | `Line of Head.Position='terminating_on_Mount_of_Jupiter'` | not in V1's pool (pool has `terminating_at_…`, not `terminating_on_…`) |
| H_023 | `Line of Head.Position='terminating_on_Mount'` | not in V1's pool |
| H_024 | `Line of Head.Position='terminating_on_Mount_of_Moon'` | not in V1's pool (pool says `Luna`, not `Moon`) |
| HL_002 | `Line of Heart.Starting_Point='rising_from_Finger_of_Jupiter'` | not in V1's pool |
| HL_015 | `Line of Heart.Presence='faded'` | `Presence` is not in `attribute_feature_mapping` at all; `faded` not in the pool |

These five are the *only* members of the class the existing tooling could already see —
`vocab_reachability_scan.classify_antecedent()` returns `NO` for them — but see §3: `NO` is **not**
CI-enforced, only `UNEMITTABLE` is.

### 1.4 `D4-DUAL-ENCODING` (30 antecedents / 27 rules) — the largest class

A landmark relationship encoded **as a literal value token** on an attribute the extractor only ever
populates **as a relation target**.

`Starting_Point`, `Position`, `Branching`, `Proximity` are written by *two* channels:

* **target channel** — `extract_relational_targets()` parses the ORIGIN / TERMINATION / BRANCHES_TO /
  PROXIMITY vision fields into `targets[feature][attribute] = "<landmark>"`.
* **value channel** — the extraction LLM may *also* emit `observation[feature][attribute] = "<token>"`,
  because `attribute_feature_mapping` lists these attributes as legal for the lines, so they appear in
  the prompt's `VALID ATTRIBUTES FOR THIS FEATURE` line.

`palm_rules_table._antecedent_fires()` reads them from **different dicts** and never bridges:

```python
if antecedent.value is not None:
    if observation.get(f, {}).get(a) != antecedent.value:   # value channel only
        return False
if antecedent.relation_target is None:
    return antecedent.value is not None                      # never consults `targets`
```

**This is confirmed live, not theoretical.** On the S120 run
(`diagnostics/s120_live_palm_run_raw.json`, `palm_right_test.jpg`):

```
targets["Line of Heart"]["Starting_Point"] == "Mount of Jupiter"   # captured cleanly
targets["Line of Head"]["Starting_Point"]  == "Line of Life"       # captured cleanly
observation["Line of Heart"]["Starting_Point"]  -> absent
observation["Line of Head"]["Starting_Point"]   -> absent
```

`HL_001` fires on `Starting_Point='rising_from_Mount_of_Jupiter'` (literal value).
`H_002` fires on `Starting_Point='rising_from_Line_of_Life'` (literal value).
**Both doctrines were physically present on that hand and correctly captured by the pipeline; neither
rule fired.** `surviving_rule_ids` was `['H_026','H_028','L_001','M_001','M_014','M_023']`.

Full D4 list: H_002, H_003, H_007, H_010a, H_010b, H_013, H_015, H_020, H_021, H_023, H_024, H_025,
HL_001, HL_003, HL_004, HL_005 (×2), HL_006, HL_007, HL_008, HL_009, HL_010, HL_011, HL_012, HL_014,
HL_018, HL_021, L_004, L_005, L_018.

### 1.5 `D5-SYNONYM-OR-STATE` (17 antecedents) — FT_001's own class

Solicited dimension, token legal in V1, but **every live capture produced a different token for that
same (feature, attribute)**. Two genuinely different sub-causes are mixed here and must be separated
per row (see §2 for dispositions):

| rule | antecedent | live runs produced | sub-cause |
|---|---|---|---|
| **FT_001** | `Line of Fate.Depth='well_marked'` | `deep` | **synonym split** |
| **FT_009** | `Line of Head.Depth='well_marked'` | `deep` | **synonym split** |
| HL_016 | `Line of Heart.Length='extending_across_entire_palm'` | `long` | granularity split |
| L_023 | `Line of Life.Curve='sweeping_wide'` | `curved` | granularity split |
| L_024 | `Line of Life.Curve='close_to_Mount_of_Venus'` | `curved` | granularity split |
| FT_006 | `Line of Fate.Length='cutting_into_finger_of_Saturn'` | `long` | **dedicated `LENGTH EXTENT` vision field exists** — see §2 |
| H_005, H_006, L_025 | `Length='short'` | `long` | genuine state (hand had a long line) |
| HL_013, HL_018, HL_020 | `Width='wide'` | `narrow` | genuine state |
| HL_014 | `Width='thin'` | `narrow` | **synonym split** (`thin` and `narrow` are both `shape_values`; vision prompt literally offers "narrow/thin vs broad/thick") |
| L_002, L_005, L_017, L_018 | `Continuity='chained' / 'islanded'` | `unbroken` | genuine state |

### 1.6 `D6-UNOBSERVED` — includes an **attribute-level** twin of the same bug

22 antecedents were never populated in any capture. Most are legitimate state-contingency
(`Continuity='broken'` needs a broken line). **But 5 are the same drift one level up — two attribute
names for one dimension:**

| rule | antecedent | competing attribute actually emitted |
|---|---|---|
| H_004, H_020 | `Line of Head.Direction='straight'` | `Slope='straight'` |
| H_018, H_019 | `Line of Head.Direction='sloping'` | `Slope='downward'` |
| HL_012 | `Line of Heart.Direction='drooping'` | `Slope='downward'` |

`Direction` and `Slope` are both legal for `Line of Head` in `attribute_feature_mapping`, so both
appear in the extractor's `VALID ATTRIBUTES` line. Only `Slope` carries an
`attribute_value_binding` constraint line, so the LLM reliably picks `Slope`. `Direction` is
structurally out-competed — the D5 mechanism operating on attribute names instead of value tokens.

### 1.7 Two incidental pool defects found en route

* **Case-variant duplicate in V1:** `cutting_into_Finger_of_Saturn` (in `position_values`) and
  `cutting_into_finger_of_Saturn` (in `length_values`) are the same token with different casing. The
  vision `LENGTH EXTENT` field emits the lowercase form.
* **Naming drift between two feature lists:** `palm_reading._FEATURE_REGISTRY` carries
  `"mount of mars negative"`; `observation_extractor._FEATURE_ALIAS` carries
  `"lower mount of mars"` and has no `"mount of mars negative"` key. Latent, not currently harmful.

---

## 2. ROOT CAUSE

### 2.1 Why the registry carries both `deep` and `well_marked` — answered from history

`git log --follow data/ontology_registry.json` → the earliest revision is **`d723291`
("checkpoint: interpretive palm rule-book pilot (durability, unvalidated)", 2026-08-03)**. At that
commit:

```
depth_values = ['deep', 'shallow', 'faint', 'well_marked', 'clearly_marked',
                'indistinct', 'heavily_marked', 'heavy']
```

**Byte-identical to today.** Both tokens are original. **This is NOT a half-finished rename.**

The registry's own `meta.description` at that commit states its purpose:

> *"Closed vocabulary registry for deterministic palmistry rule extraction. All feature, attribute,
> and value tokens used in rule generation MUST exist in this registry."*

That is an **authoring-side** contract — "a rule may not invent a token" — and it says nothing about
emission. The eight depth tokens are eight of Cheiro's own English phrasings ("deep", "well marked",
"clearly marked", "heavily marked"…), harvested **book-in**. They were never a set of physically
distinguishable states. The vision prompt, authored separately and much later, asks for exactly one
thing on this axis: the bare word **`depth`**. There is no instruction anywhere telling the vision
model or the extraction LLM which of the eight to prefer, and no mechanism that could enforce one.

So the answer to the prompt's question is option **(iii)-then-(i)**: `deep` and `well_marked` are
**not two intended states vision can't distinguish** — they are two *book phrasings of one state*, and
the rule token is simply the wrong member of a synonym cluster that should never have had eight members.

**Corroborating primary source, in the repo, written at the time:**
`agent/interpretive/observation_to_tokens.py`'s module docstring, discrepancy note #3, states the flat-pool
decision explicitly and names its own tradeoff:

> *"No explicit attribute → value-category linkage exists in the registry… this adapter treats the
> FLATTENED UNION of every values-category list as the valid value pool for ANY attribute that is
> itself valid for the observed feature… A stricter per-attribute value binding would need the
> registry itself to add that linkage; not invented here."*

The flat 217-token pool is therefore a **known, documented, deliberately deferred** design decision —
not an oversight. S95's `attribute_value_binding` block was the start of the fix and reached exactly
**3 of ~42 attributes** (`Slope`, `Slope_Magnitude`, `Proximity`). The remaining ~39 still fall through
to the flat pool.

### 2.2 The FT_001 flag was raised at authoring time and never cleared

`palm_rules_fate_line_v1.json` FT_001 carries its own `schema_flags` entry, verbatim:

> *"NAMING-MISMATCH: source says 'is strong' (no literal 'strong' token in any value pool) -- mapped
> to Depth=well_marked as the nearest closed-vocab match. **Verify live-phrasing at Step 2 before
> treating as fireable**; raise for Sulabh if a dedicated 'strong' token is preferred instead."*

The author flagged the exact risk, named the exact verification step, and the rule was nonetheless
marked `verified: true` / `source_fidelity: fulltext_exact` on 2026-08-22. **`schema_flags` is a
free-text field that nothing reads.** No loader, gate, test or scan inspects it. A correctly-raised
hazard was recorded into a channel with no consumer.

### 2.3 The decisive A/B, on one hand, one attribute

| rule | antecedent | fired on S120 hand? |
|---|---|---|
| `L_001` | `Line of Life.Depth = 'deep'` | **YES** |
| `FT_001` | `Line of Fate.Depth = 'well_marked'` | no |
| `FT_009` | `Line of Head.Depth = 'well_marked'` | no |

Corpus-wide `Depth` usage: `well_marked` × 2, `deep` × 1. **The single rule that happened to pick the
emitted synonym is the only `Depth` rule that has ever fired.** Which member of the cluster an author
picked was a coin flip, and the coin decided whether the rule exists in production.

### 2.4 Per-mismatch disposition — (i) rule-token correction / (ii) vision-menu widening / (iii) park

| class | rules | disposition | reasoning |
|---|---|---|---|
| **D5 synonym split** — FT_001, FT_009, HL_014 | 3 | **(i)** rule-token correction, *plus* collapse the cluster in V1 | `deep`/`narrow` are the emitted members; the other cluster members must be removed from the pool in the same change or the next author repeats the coin flip |
| **D5 granularity split** — HL_016, L_023, L_024 | 3 | **(ii)** vision-menu widening | these are real distinctions Cheiro draws (a life line *sweeping wide* vs merely *curved* is doctrine); vision is capable of the call if asked. Gate on a measurement probe first per Working Style #19 |
| **FT_006** `cutting_into_finger_of_Saturn` | 1 | **already (ii); token-casing fix only** | the `LENGTH EXTENT` vision field *literally emits this string*. It has never fired only because no hand had it. Fix the `Finger`/`finger` case-variant duplicate (§1.7) so the two pool entries cannot diverge |
| **D5 genuine state** — H_005, H_006, L_025, HL_013, HL_018, HL_020, L_002, L_005, L_017, L_018 | 10 | **no action** | correct behaviour; needs a hand that exhibits the state. Same disposition as the S115 `L_026` / `FT_007` permanent-park entries |
| **D6 attribute twin** — H_004, H_018, H_019, H_020, HL_012 | 5 | **(i)** migrate `Direction` → `Slope` | `Slope` is bound and deterministically emitted; `Direction` is the unbound twin. Same shape as the S97 `Ending_Point` → `Position` migration, already precedented |
| **D6 state-contingent** — remaining 17 | 17 | **no action** | legitimate |
| **D4 dual-encoding** | 27 | **(i)** migrate literal-value → `relation_target`, *and* delete the duplicated landmark tokens from `position_values` | precedented twice (S97 `Ending_Point`→`Position`, S112 `FT_007/8`→`stopped_by`). Highest yield in the report: HL_001 and H_002 would have fired on the S120 hand |
| **D3 token-absent** | 4 | **(i)** correction, mechanical | `terminating_on_` → `terminating_at_`; `Moon` → `Luna`; HL_002/HL_015 need a modelling decision, not a rename |
| **D2 colour** — HL_019, HL_020 | 2 | **(iii) park** | line colour under uncontrolled phone lighting/white-balance is not measurable. Same disposition class as S119's mount-LEANING park — gate any future work on a vision-measurement proof first |
| **D2 Fullness** — L_022 | 1 | **(ii)** *or* (i) | `Mount of Venus` already has a 10-member `DEVELOPMENT` menu including `full and large`; `Fullness='full'` is most likely a mis-modelled `Development` |
| **D1 Hand.Type** — H_018, H_019, H_020 | 3 | **(iii) park — already scoped out** | S96 formally scoped hand-type OUT. These 3 rules should be moved to `unauthorable_register.json`, not left as live-but-dead |
| **D1 Quadrangle** — H_010a, H_010b, HL_006, HL_021 | 4 | **(iii) park** | the quadrangle is not an emitted feature and has no vision block. Needs a new feature + emission field before any of these can live |

---

## 3. WHY NO GATE CAUGHT IT — both claims confirmed, and a third found

### 3.1 `_check_vocabulary` checks the flat pool — CONFIRMED

`agent/interpretive/palm_select.py:346`:

```python
legal = vocab.get(ant.feature, {}).get(ant.attribute)   # vocab = oe._CLOSED_VOCAB
if ant.value is not None and ant.value not in legal:
    misses.append({... "reason": "value_not_in_emitted_pool" ...})
```

`oe._CLOSED_VOCAB[feature][attribute]` is built by `_values_for_attribute()`, which returns the
narrow `attribute_value_binding` tuple **only for the 3 bound attributes** and the flat 217-token
`_ALL_VALUES` for every other. `well_marked` is in `depth_values`, therefore in `_ALL_VALUES`,
therefore passes. Confirmed.

### 3.2 `vocab_reachability_scan.py` CLI defaults to head/heart only — CONFIRMED, with a nuance

* CLI default (`scripts/vocab_reachability_scan.py:_RULES_PATH`) is
  `data/palm_rules/palm_rules_head_heart_v1.json`; `--rules` must be passed per-file.
* **However**, `tests/interpretive/test_vocab_reachability_scan.py` *does* glob
  `data/palm_rules/palm_rules_*.json` and run all 4 files in CI.
* **The nuance that matters:** that CI test asserts **only** `status == "UNEMITTABLE"` is empty.
  It does **not** assert `status == "NO"` is empty. So the 5 `D3-TOKEN-ABSENT` antecedents the scan
  *already* classifies `NO` pass CI silently today.
* Its `_KNOWN_RULE_FILE_NAMES` discovery guard still lists only 3 files —
  `palm_rules_mounts_v1.json` is discovered by the glob but is not protected against a discovery
  regression.
* And the scan's own value check is `oe._values_for_attribute(attribute)` — the **same** flat pool as
  §3.1. So even promoting `NO` to a hard failure would not catch `FT_001`.

### 3.3 THIRD FINDING (not in the prompt): the vocabulary guard is not on the live path at all

`palm_select.select()` — which owns `_check_vocabulary`, `hard_side_misses`, and the entire
`unmatched` silent-miss surface described in CLAUDE.md as *"the silent-miss surface (CLAUDE.md law #22)"* —
**is never called by production code.**

```
$ grep -rn "palm_select" --include=*.py .   (excluding palm_select.py itself)
./diagnostics/validate_broken_overlapping.py:10:   (comment only)
./diagnostics/validate_broken_overlapping.py:15:   (comment only)
```

The live path is `agent/interpretive/palm_reading.py::_run_rules_engine` →
`palm_rules_table.match()` + `resolve_priority()` **directly** (`palm_reading.py:2246-2247`). It never
constructs the vocabulary guard, never computes `hard_side_misses`, never surfaces `unmatched`.

This contradicts CLAUDE.md's S95 lock — *"`agent/interpretive/palm_select.py` is the CANONICAL
interpretation path"*. Whatever the intent was, the module is currently dead code with respect to
production. **Flagged, not fixed** — deciding whether `palm_select` should be wired in or its guard
relocated into `_run_rules_engine` is a design ruling, and it materially changes where the gate in §4
should live.

### 3.4 What a correct reachability gate must check

Not `value ∈ global_pool`. It must check:

```
value ∈ EMISSION_MENU[feature][attribute]
```

where `EMISSION_MENU` is the **per-feature, per-attribute closed token set the vision prompt actually
solicits and the extractor actually enforces**. Three such menus already exist and already work —
`attribute_value_binding` (3 attributes), `_MOUNT_DEVELOPMENT_MENUS` (5 mounts), and
`vision_relational_menus` (per-line ORIGIN/TERMINATION). They are three separate, hand-maintained
tables in three different files. The gate needs one union of them, and the ~39 unbound attributes need
their menus authored.

---

## 4. THE CAPTURE-NET BLIND SPOT — CONFIRMED

`agent/interpretive/capture_net.py` has exactly 4 trigger categories, all derived from one map:

```python
_DISPOSITION_TO_TRIGGER = {
    "llm_unclear": "silence",  "position_unresolved": "silence",
    "hallucination": "wrong_source",
    "batch_call_failed": "instability", "batch_malformed_response": "instability",
    "resolved": "ai_decision",
}
```

`capture_net_digest._KNOWN_TRIGGERS` is literally `sorted(set(_DISPOSITION_TO_TRIGGER.values()))`.

Every producer is either `palm_reading`'s S109 relational-verb LLM fallback (`map_fallback_audits`) or
S119's `record_dropped_rules` (dormant by construction). **Nothing routes a rule-gating outcome into
the net.** `_PAYLOAD_KEYS` has no slot for `attribute`, `value`, or a gate reason.

Consequence, measured: the S120 run's capture-net digest reads **`0 row(s)`** on a hand where at least
two doctrinally-correct rules (HL_001, H_002) silently failed to fire on data the pipeline had already
captured. The run looks perfectly clean. Confirmed: **a real silent miss with zero instrumentation.**

---

## 5. AGENT PASS

Run against the roster documented in this repo: **architect, business, critic, qa, ui_ux, debate,
Ephemeris Auditor, Validation Source**. Per CLAUDE.md Working Style #7 the roster count is
UNRESOLVED — 8 are documented, the 9th is documented nowhere — so this is reported as an **8-agent
documented pass**, not "9 agents". Ephemeris Auditor returns NO FINDINGS (no ephemeris/calculation
surface touched). Only genuine disagreements are surfaced below; agreements are compressed.

### 5.1 Where all agents agree (no debate needed)

1. Renaming `well_marked` → `deep` alone is **rejected** — it fixes 2 of 53 antecedents and leaves the
   generator of the class intact.
2. The **root defect is that V1 was authored book-in and never reconciled against V2/V3**, and the
   mounts chapter proves vision-out authoring works.
3. **D4 is the highest-yield fix** in the report — 27 rules, precedented migration, two of them
   verifiably would have fired on an existing hand.
4. `schema_flags` must gain a consumer or be deleted; a hazard channel nobody reads is worse than none.
5. The three existing emission menus (`attribute_value_binding`, `_MOUNT_DEVELOPMENT_MENUS`,
   `vision_relational_menus`) must become **one** source, per the S98 registry-is-the-single-source lock.

### 5.2 CONFLICT 1 — the structural fix (a)

```
CONFLICT: Do we complete per-attribute emission binding for all ~42 attributes now,
          or bind only the attributes live rules actually use?
ARCHITECT says: Complete the binding. A registry block `emission_menus[feature][attribute]`
          becomes the ONE source; palm_processor derives its prompt menus from it (byte-identical-
          proven, exactly as S98 did for vision_relational_menus), observation_extractor derives
          both its VALUE CONSTRAINTS prompt lines and its Python guard from it, and the rule
          loader/CI gate checks against it. Partial binding leaves the flat-pool fallback alive,
          which IS the bug; a half-closed vocabulary is the S119 feature_needles drift shape.
BUSINESS says: ~42 attributes x ~15 features is a large authoring job with no user-visible
          output. Bind the 11 attributes live rules actually key on (Depth, Length, Width,
          Continuity, Curve, Direction, Slope, Clarity, Proximity, Development, Fullness) and
          ship. V1 palm is DROPPED from scope (S71) — this is V1.1 work competing with
          the astrology track, which is the actual revenue surface.
RESOLUTION: BUSINESS, scoped — bind the attributes live rules use, but the mechanism Architect
          specifies (single registry block, derived prompt, derived guard, derived gate) is
          built in full at the same time. Debate rule: "Business wins if fix is genuinely low
          effort; Critic wins if issue causes failure." The mechanism is what prevents recurrence;
          the coverage is what costs time. Build the mechanism, phase the coverage.
OVERRULED: ARCHITECT — the flat-pool fallback survives for unbound attributes. Acknowledged and
          contained: an unbound attribute must be an explicit, listed exception with a
          `# UNBOUND:` marker, not a silent default, so the residue is visible and countable.
UNIFIED ACTION: add `emission_menus` to ontology_registry.json covering the 11 in-use attributes;
          derive palm_processor's prompt menus and observation_extractor's guard + constraint
          lines from it; keep the flat pool ONLY for explicitly-listed unbound attributes.
```

### 5.3 CONFLICT 2 — should the reachability gate be a mandatory suite test over ALL rule files? (b)

```
CONFLICT: Hard-fail CI on every non-emittable antecedent, or ratchet on new rules only?
QA says: Hard fail, all 4 files, all statuses (NO + UNEMITTABLE + the new NOT-IN-EMISSION-MENU).
          Working Style #22 already calls reachability "a CI gate, per domain". A gate that
          exempts the existing corpus is a gate that never fires — 36 of 87 rules are already
          broken and the suite is green.
CRITIC agrees with QA on principle and adds: the current test asserting only UNEMITTABLE is
          precisely how 5 already-detectable D3 rows stayed invisible.
ARCHITECT says: Hard-failing today turns the suite red on 36 rules that a human ratified as
          doctrinally correct. That is not a code defect, it is an unmigrated corpus. Red-on-
          arrival gates get skipped or xfailed, and then they are worse than absent.
BUSINESS says: a red suite blocks the astrology track for work on a V1-dropped surface.
RESOLUTION: QA, with Architect's mechanism. QA blocks HIGH items with untested failure paths —
          no exceptions — but the block is satisfied by a FROZEN BASELINE ratchet, not by a
          blanket exemption: the test asserts the non-emittable set is EXACTLY a pinned,
          committed list of the 36 known rule ids. Any NEW offender fails CI immediately; any
          FIXED offender also fails CI until removed from the list, so the list can only shrink.
OVERRULED: ARCHITECT — a baseline list is a form of exemption. Acknowledged: it is a shrink-only
          exemption with a named owner per row, which is the difference between a ratchet and an
          amnesty.
UNIFIED ACTION: promote the reachability scan to a mandatory suite test over ALL palm_rules_*.json;
          assert the offender set == a committed frozen baseline (36 ids); add palm_rules_mounts_v1.json
          to _KNOWN_RULE_FILE_NAMES; extend the scan's value check from the flat pool to emission_menus.
```

### 5.4 CONFLICT 3 — a new capture-net trigger? (c)

```
CONFLICT: Is a capture trigger for silent rule-vocab misses worth it, or over-engineering?
CRITIC says: Worth it. §4 proves the S120 run reported "0 rows" while two correct rules silently
          failed. That is the exact undiagnosable-silence class the net exists for.
BUSINESS says: Over-engineering. A CI gate is STATIC and catches this class before any hand is
          ever photographed. A runtime trigger duplicates the CI gate's job at runtime cost, on
          a dropped surface.
QA says: Neither covers the DYNAMIC half. CI cannot see D5: `FT_001`'s token is legal in every
          static sense; only a live run reveals that the hand emitted a SIBLING token from the
          same menu. That near-miss is invisible to any static gate.
RESOLUTION: QA — split the responsibility. STATIC classes (D1/D2/D3/D4) go to the CI gate and get
          NO runtime trigger; the DYNAMIC class (D5 sibling-token near-miss) gets ONE new
          trigger. Business's objection is correct for 4 of the 5 classes and wrong for the one
          that actually produced this session.
OVERRULED: BUSINESS on the D5 half — acknowledged: it is one trigger, one _PAYLOAD_KEYS extension,
          fires only on a real near-miss, and inherits capture_net's existing never-raises contract.
UNIFIED ACTION: add trigger `vocab_near_miss` (NOT a reuse of `silence` — `silence` means the LLM
          had nothing usable; this means the pipeline had something usable and the rule asked for
          its synonym). Fires when a rule gate-failed on (feature, attribute) that the run DID
          observe with a different token from the same emission menu. Extend _PAYLOAD_KEYS with
          `attribute`, `rule_value`, `observed_value`. NOTE: requires §3.3 to be resolved first —
          today's live path has no gate-reason surface to hang this on.
```

### 5.5 Single-agent findings, uncontested

* **CRITIC:** `_check_vocabulary`'s `hard_side_misses` is `blocking: False` — advisory by design. Even
  if `palm_select` were wired in, an unreachable-token gate-out would not stop a reading. Any fix
  must decide `blocking` explicitly rather than inheriting the current default.
* **QA:** the S120 evidence base is **2 hands**. Every "never observed" verdict in §1.5/§1.6 is
  therefore weak evidence *individually* — but the D1/D2/D3/D4 verdicts are structural (code-derived)
  and do not depend on it. Do not let a strong structural finding be diluted by a thin empirical one.
* **UI/UX:** user-visible consequence — the S120 hand produced a reading that silently omitted its
  heart-line origin doctrine and its head-line origin doctrine. Per Palm Diagnostic Principle #2 the
  product's silence must be *honest*; here it was silence caused by a token mismatch and presented
  identically to genuine doctrinal silence. That is the actual product harm, and it argues for
  surfacing `unmatched` somewhere a human sees it.
* **VALIDATION SOURCE:** every FT_001-class token in §1.5 traces to real Cheiro phrasing —
  `well marked` appears verbatim on the very page FT_009 cites (p103/p104,
  *"If the line of fate rise from the line of head, and that line be well marked…"*). Collapsing the
  synonym cluster must therefore be recorded as a **vocabulary** decision, not a source-fidelity one;
  `source_quote` must stay verbatim while the trigger token normalizes. This is exactly the
  "three vocabularies drift" mistake class `data/_meta/learnings_for_astrology_rules.md` exists to prevent.
* **ARCHITECT:** the D4 fix has a hidden prerequisite — deleting `rising_from_*` / `under_Mount_of_*` /
  `terminating_at_*` from `position_values` will break any *other* consumer of the flat pool. Sequence
  the pool edit AFTER the rule migration, never before.
* **EPHEMERIS AUDITOR:** no findings — no ephemeris, chart, or calculation surface is touched.

---

## 6. RECOMMENDED PLAN (ranked, for ratification — nothing executed)

| # | Action | Class fixed | Resolves |
|---|---|---|---|
| 1 | **Resolve §3.3 first:** rule on whether `palm_select.select()` is wired into `_run_rules_engine` or its vocabulary guard is relocated there. Everything below hangs off this. | — | non-delegable human ruling |
| 2 | Add `emission_menus[feature][attribute]` to `ontology_registry.json` for the 11 in-use attributes; derive palm_processor's prompt menus + observation_extractor's guard/constraint lines from it (byte-identical proof, S98 pattern). Unbound attributes become an explicit listed exception. | mechanism for all | Conflict 1 |
| 3 | Promote the reachability scan to a mandatory suite test over ALL 4 rule files, checking `emission_menus` not the flat pool, asserting a **frozen shrink-only baseline of 36 offender ids**. Add `palm_rules_mounts_v1.json` to `_KNOWN_RULE_FILE_NAMES`. | D1–D4 detection | Conflict 2 |
| 4 | **D4 migration** (27 rules): literal landmark value → `relation_target`. Highest yield. Verify HL_001 + H_002 fire on the existing S120 image before/after. | D4 | agreed |
| 5 | **D5/D6 token + attribute corrections**: FT_001/FT_009 `well_marked`→`deep`; HL_014 `thin`→`narrow`; H_004/H_018/H_019/H_020/HL_012 `Direction`→`Slope`; D3 renames; then collapse the `depth_values` synonym cluster **in the same commit**. | D3, D5-synonym, D6-twin | agreed |
| 6 | Move H_018/H_019/H_020 (hand-type, S96-scoped-out) and the 4 Quadrangle rules to `unauthorable_register.json`. | D1 | agreed |
| 7 | Give `schema_flags` a consumer: any `verified: true` rule carrying an unresolved `NAMING-MISMATCH:` flag fails the same CI gate. | root cause 2.2 | agreed |
| 8 | Add capture trigger `vocab_near_miss` + `_PAYLOAD_KEYS` extension (`attribute`, `rule_value`, `observed_value`). **After #1.** | D5 dynamic | Conflict 3 |
| 9 | Park with a vision-measurement gate: line `Color` (HL_019/HL_020), `Quadrangle` as a feature. Record alongside the S119 mount-LEANING park. | D2 | agreed |
| 10 | Ride-alongs: fix the `cutting_into_Finger_of_Saturn` case-variant duplicate; reconcile `_FEATURE_REGISTRY`'s `"mount of mars negative"` against `_FEATURE_ALIAS`'s `"lower mount of mars"`. | §1.7 | agreed |

---

## 7. CAVEATS

* **C1 — empirical base is 2 hands.** Every "never observed / only ever produced X" statement rests on
  the live captures present in `diagnostics/*.json` (principally `s120_live_palm_run_raw.json` and
  `s117_live_confirmation_raw.json`). D1/D2/D3/D4 verdicts are code-derived and independent of this;
  D5/D6 verdicts are **suggestive, not proven**.
* **C2 — the solicitation map is hand-derived.** §1.2's "the vision prompt never asks for X" is read
  off `agent/palm_processor.py::_build_description_system_prompt` by a human, not extracted
  mechanically. It should become a derived artifact under plan item #2.
* **C3 — D4 is "cannot fire in practice", not "cannot fire in principle".** The extraction LLM is
  *permitted* to emit `Starting_Point` as a literal value (the attribute is in
  `attribute_feature_mapping`, so it appears in the prompt's VALID ATTRIBUTES line). It never has.
  Rated dead on the strength of the mechanism plus the S120 counter-example, not on impossibility.
* **C4 — RESOLVED. The probe is committed:** `probes/vocab_mismatch_audit_S121.py`, commit
  **`dbce778`** (pushed to `wip/interpretive-pilot`). Every number in this report was re-verified
  against the committed copy and reproduces exactly: 127 antecedents / 87 rules, 36 dead (41%),
  per-class counts D1=7 D2=3 D3=5 D4=30 D5=17 D6=22 D0=2, and the per-file dead-rule id lists in
  §1. Working Style #16 satisfied. Two deltas from the scratchpad original, logic untouched:
  paths are now repo-relative (derived from `__file__`, not hardcoded temp paths, which is what
  makes it reproducible at all), and the per-antecedent JSON dump moved behind an opt-in `--dump`
  flag so the probe writes nothing by default. Suite at commit time: 3794 passed, 7 skipped, 0
  failed.
* **C5 — roster count.** Reported as an 8-agent documented pass. CLAUDE.md Working Style #7 records
  the count as UNRESOLVED and forbids citing "9 agents" as settled; not invented here.
