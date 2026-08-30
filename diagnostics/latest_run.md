# S119 Step 5 (completion) — mount base-meaning model applied + sources rebuilt

DECISION THIS SERVES: apply the ratified mount model, then land it with the
Part-B sources rebuild. Result: 10 rules retired, 1 graded claim enriched, live
set 99 -> 89, gate 0 NOT_FOUND, suite green.

## Verification at HEAD (17cb671) — the live base-rule set, before touching anything

The task asked me to VERIFY which base rules for Saturn / Mercury / Lower-Mars /
Luna are live, and to STOP rather than retire anything off the ratified list.

**Finding: the live set matches the ratified list exactly — no additions, no
subtractions.** `palm_rules_mounts_v1.json` held 24 validated_candidates,
3 parked_pending, 0 retired_superseded. Mercury, Lower Mars and Luna have **no
live rules at all** — their base meanings were already parked as
`M_P01` / `M_P02` / `M_P03`, every one with `reason: "ontology_gap_presence"`.

That parking note is independent corroboration of ratified decision #2, written
before it: those three mounts are *presence-only* (`palm_processor` Step 2 asks
them no Development grade question), so `extract_mount_development` never
produces a value for them and no `Presence` attribute exists to gate on.

It also explains cleanly **why the defect hit exactly the mounts it did**: a
base meaning can only be mis-keyed onto a grade where grades exist. Venus,
Saturn and Upper Mars have Development menus, so their base meanings got hung on
grades; Mercury / Lower Mars / Luna had no grades to hang them on, so the same
base meanings were correctly parked instead. One mechanism, two outcomes.

One cross-file check: `L_022` (life-line) reads `Mount of Venus.Fullness` — a
different attribute, not a base-meaning rule, untouched.

## RETIRED — 10, all on the ratified list

Moved `validated_candidates` -> `retired_superseded` (history preserved, nothing
deleted). Each carries `retired_reason`, `retired_note`, `retired_date`,
`retired_by`, plus `superseded_by` where a successor exists.

| rule | mount | antecedent | reason |
|---|---|---|---|
| M_009 | Venus | `well developed` | base_meaning_is_a_definition_not_a_claim |
| M_010 | Venus | `full and large` | base_meaning_is_a_definition_not_a_claim |
| M_011 | Venus | `abnormally large` | base_meaning_is_a_definition_not_a_claim |
| M_012 | Venus | `very high` | base_meaning_is_a_definition_not_a_claim |
| **M_013** | Venus | `not notably developed` | **base_meaning_asserted_for_an_undeveloped_mount** |
| M_017 | Saturn | `well developed` | base_meaning_is_a_definition_not_a_claim |
| M_018 | Saturn | `unusually high` | base_meaning_is_a_definition_not_a_claim |
| **M_019** | Saturn | `not notably developed` | **base_meaning_asserted_for_an_undeveloped_mount** |
| M_022 | Upper Mars | `large` | base_meaning_is_a_definition_not_a_claim (`superseded_by: M_021`) |
| **M_024** | Upper Mars | `not notably developed` | **base_meaning_asserted_for_an_undeveloped_mount** |

The three bolded rows get an additional note recording the sharper fault: they
asserted the mount's positive characteristic qualities *on the strength of the
vision layer reporting the mount is NOT developed* — not merely over-specific,
false. The retirement note also records that each `source_quote` was and remains
verbatim-correct and gate-clean, and that
`scripts/gate_rule_citations.py` verifies quote AUTHENTICITY with no notion of
antecedent-quote AGREEMENT — which is why this class survived every gate run.

## KEPT — 14 live mount rules, antecedents untouched

M_001/002/003 (Venus health/passion), M_004–M_008 (Venus, own quotes),
M_014 (Jupiter `developed`), M_015/M_016 (Saturn graded, p217/p153),
M_020 (Apollo `well developed`), M_021 (Upper Mars `large`),
**M_023 (Upper Mars `present`) — verified present and unchanged**, the one
correctly-modelled presence rule and the shape the retired rows should have had.

## CONSEQUENT-CONTEXT ENRICHMENT — exactly one: M_021

Cheiro p113 writes base and graded meaning in a **single sentence**:

> "This, the first, **gives active courage, the martial spirit**, but **when
> large**, shows a very quarrelsome, fighting disposition."

M_021's own `source_quote` is that whole sentence. With M_022 retired, a large
Upper Mars would have kept only the "quarrelsome" half — dropping the concessive
the source actually writes. Enrichment licensed by M_021's **own unchanged
citation**; no new or different quote introduced.

- before: `A large Upper Mount of Mars shows a very quarrelsome, fighting disposition.`
- after: `The Upper Mount of Mars gives active courage and the martial spirit; when large, it shows a very quarrelsome, fighting disposition.`

**No other rule was enriched.** Checked every kept graded rule and none is
licensed: Venus's base meaning is a *separate* p112 sentence from M_001/002/003's
own quotes; M_004–M_008 cite p183/p221/p222 entirely; M_015/M_016 cite p217/p153;
M_020's quote already contains its own "It denotes love of painting, poetry..."
continuation and its claim already carries it; Jupiter has no separate base
*meaning*, only an anatomical location sentence. Per the instruction, where
enrichment would have needed a different citation I did nothing.

Two `meta` keys added recording the model and the parked leaning track
(`mount_base_meaning_model`, `mount_leaning_track` — p113 "THE LEANING OF THE
MOUNTS TOWARD ONE ANOTHER" is real doctrine and the only route by which
Saturn/Mercury/Lower-Mars/Luna could ever produce a discriminating claim; no
vision signal measures inter-mount lean, so it is parked, not built).

## ONE DISCREPANCY TO FLAG (no action taken — both instructions followed literally)

Ratified decision #2 says Saturn "fires NOTHING (honest silence)". The ratified
KEEP list says keep **M_015/M_016** (Saturn graded, p217/p153) and "do NOT touch
their antecedents". I followed the KEEP list, so **Saturn is not fully silent**:
it still fires on `well developed` (M_015) and `unusually high` (M_016). Mercury,
Lower Mars and Luna *are* fully silent, as decision #2 describes.

Worth knowing before you reconcile the two: both rules already carry a
pre-existing **"MAJOR FIDELITY CAVEAT ... flagged prominently for Sulabh's
explicit decision"** in their own `source_fidelity` field. M_015's quote opens
"*The same indications* being found in connection with a well-developed Mount of
Saturn" and M_016's opens "*The same development of the line of head*, with an
unusually high Mount of Saturn" — both are back-references to a Line-of-Head
profile in the preceding paragraph, and both come from Part III chapters
(suicidal tendency / insanity), not the Mounts chapter. Each was authored as a
Saturn-only single-antecedent rule under an earlier instruction, with four
remediation options recorded and never chosen. If decision #2's intent was that
Saturn falls silent, retiring or re-scoping these two is the outstanding step —
but that is a separate ratified authoring call and I did not take it.

## Reachability scan — `python scripts/vocab_reachability_scan.py --rules data/palm_rules/palm_rules_mounts_v1.json`

- **UNEMITTABLE: 0** — this is the CI-enforced gate
  (`tests/interpretive/test_vocab_reachability_scan.py` asserts it across every
  `palm_rules_*.json`), and it is clean.
- **Orphaned by the retirements — exactly one value, as expected and desired:**
  `not notably developed` now fires nothing on Venus, Saturn and Upper Mars (it
  was already inert on Jupiter and Apollo). That value is still emitted by the
  vision layer and simply matches no rule — which *is* the ratified model:
  "the mount is not notably developed" is not grounds for a claim.

  | mount | values that still fire | orphaned |
  |---|---|---|
  | venus | well developed, small, abnormally large, full and large, very poor development, not well developed, depressed, very high | not notably developed |
  | saturn | well developed, unusually high | not notably developed |
  | jupiter | developed | not notably developed |
  | apollo | well developed | not notably developed |
  | mars positive | large, present | not notably developed |

- **The scan also flags 10 surviving rules NAMING-MISMATCH — PRE-EXISTING, not
  caused by this change, and a scan blind spot rather than a real defect.** It
  compares against `ontology_registry.json`'s *global* `Development` value pool,
  but mount Development values come from `observation_extractor.
  _MOUNT_DEVELOPMENT_MENUS` (S117), which by design bypasses that global gate —
  `palm_reading` merges mount Development into the flat observation *after*
  `to_tokens` for exactly this reason. I verified all 10 flagged values
  (`well developed`, `abnormally large`, `full and large`, `very poor
  development`, `not well developed`, `very high`, `unusually high`, `present`)
  are present in their own mount's menu, so every one is genuinely emittable.
  Recorded as a finding; teaching the scan about the per-mount menus is a
  separate change and was not made here.

## Live rule count: **99 -> 89** (24 mount rules -> 14)

## Tests — 4 existing changed, every one caused by a ratified retirement

| test | change | why |
|---|---|---|
| `test_load_rule_set_real_data_merges_43_plus_13_with_unique_ids` | `99` -> `89`, arithmetic comment updated (24 mount -> 14) | pure count baseline; 10 rules retired |
| `test_every_live_rule_produces_a_claim_citing_its_own_gate_verified_quote` (my S119 Step-2 test) | `99` -> `89` | its own guard message said "live rule count moved -- re-baseline this test". It measures CITATION ACCURACY, unaffected by the live set shrinking: it still re-verifies **all** live rules through the authoring gate, now 89/89 CLEAN |
| `test_mount_development_fires_end_to_end_definition_of_done` | dropped the `M_009` co-fire + `("M_001","M_009")` suppression assertions; docstring rewritten | M_009 no longer exists to co-fire. **The definition-of-done is untouched and still fully asserted** — a DEVELOPMENT line still flows end to end and M_001 still fires, survives alone and supplies the voiced claim. The user-visible outcome is identical; only the suppressed row is gone. Its old docstring praised the very behavior the ratification removes ("the GENERIC Venus-trait claim only ever surfaces when NO graded rule also fires") — that is the Barnum case, surfacing precisely when nothing discriminating was observed. `resolve_priority`'s baseline-suppression mechanism is untouched and still covered by the Life-line baseline tests |
| `test_mount_development_deficiency_gates_off_base_meaning_live` | docstring note only, **no assertion changed** (it still passes) | its disjointness assertion now holds trivially rather than by OFF-set gating. Kept — "small fires M_002 and nothing else" is still real — but the prose would otherwise describe a mechanism that no longer exists |

No test change is unexplained by a ratified retirement.

## PART B — sources rebuild: still present, still green after the rule edits

Re-verified in place: `_build_sources_from_claims` derives a by-rule source from
the claim's own citation (page + gate-verified quote, `score=None`), by-chunk
retrieval sources unchanged with their real score; both renderers share
`_format_source_line`, which omits the score clause when None; the UI shows the
quote beneath the citation. All 13 Part-B tests pass, including the S120
"2 of 6 sources" closure and the containment test proving the quote reaches the
sources panel but never the voicer prompt.

## Verification
- `python -m pytest -q` -> **3743 passed, 7 skipped**. Step-4 baseline 3730/7;
  +13 Part-B tests = 3743, with 4 existing tests re-baselined (the retirements
  remove rules, not tests). Zero unexplained failures.
- `python scripts/gate_rule_citations.py` -> **`NOT_FOUND_ANYWHERE: 0`**
  (89 live, 16 parked).
- `python scripts/vocab_reachability_scan.py --rules .../palm_rules_mounts_v1.json`
  -> **UNEMITTABLE: 0**.
- Files staged: 8 — the mounts rule file, `palm_reading.py`, `frontend/app.py`,
  and 5 test files. No unrelated staging.

## Commit
`7be74db` — pushed to `origin/wip/interpretive-pilot`. Staged: ONLY the 8 files listed above.
