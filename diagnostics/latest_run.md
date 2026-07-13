# S67 R3: deterministic per-feature support gate + decline mechanism

Implementation report for the R3 support gate (`agent/interpretive/palm_reading.py`)
+ matching Ring 2 update (`tests/interpretive/test_palm_reading.py`).
Builds on R1 (commit `8c1b8ab`) as committed — R1's structure
(`_retrieve_per_feature`, `_gather_feature_texts`, `_assemble_retrieved_passages`,
registry-order per-feature map) was read first and left untouched; R3
inserts a gating layer between R1's retrieval and prompt assembly.

## Files touched

- `agent/interpretive/palm_reading.py` — production gate + decline mechanism.
- `tests/interpretive/test_palm_reading.py` — matching Ring 2 update (same commit).

Nothing else touched.

## Consumer-compatibility check (before coding)

`PalmReadingResult` gains two NEW fields (`supported_features`,
`unsupported_features`). Grepped `PalmReadingResult(` across the whole
repo before touching the dataclass: the only construction site is
`generate_palm_reading` itself (`agent/interpretive/palm_reading.py`) —
no other module constructs it directly, so adding required fields
(rather than defaulted ones) is safe; the single call site was updated
in the same edit. No consumer contradicted the instructions; nothing to
STOP and report.

## Design-decision → code mapping

| Design decision | Code |
|---|---|
| Needle registry (10 features, OCR-robust short forms) | `palm_reading._SUPPORT_NEEDLES` |
| Support gate: needle-contains AND score >= 0.30 | `_chunk_supports_feature`, `_SUPPORT_SCORE_FLOOR` |
| Gate applied to R1's map, registry order, both output tuples | `_apply_support_gate` |
| Genuine-negative-absence exemption ("no clear marks visible"-style) | `_is_genuine_negative_absence` |
| LLM-side ban (system prompt rule, no LLM-authored decline text) | New "STRICT SCOPE (S67 R3)" bullet in `_READING_SYSTEM_PROMPT`'s "## How you read" |
| Ring 1 banned-mention check (word-boundary) | `_check_banned_feature_mentions`, folded into `_run_ring1_checks` (now takes `unsupported_features`) |
| Decline block (Python-owned, fixed template) | `_DECLINE_BLOCK_TEMPLATE`, `_build_decline_block`, `_FEATURE_DISPLAY_NAMES` |
| Decline block ordering (before DISCLAIMER) | `generate_palm_reading`'s `final_text` assembly |
| Zero-support path reuses low-confidence trigger | `total_chunks` now computed from `gated_results`, not R1's raw `per_feature_results` — the SAME `if total_chunks == 0:` check now fires whenever every chunk is gated out, not just when retrieval itself was empty |
| `sources`/`context_corpus`/assembled prompt all reflect GATED chunks only | `generate_palm_reading` now threads `gated_results` (not `per_feature_results`) through all three downstream uses |
| Result surface: `supported_features`/`unsupported_features` | `PalmReadingResult` dataclass + `generate_palm_reading`'s return |
| Ring 1 / F2c retry cap / DISCLAIMER / system prompt structure | UNCHANGED except the one new STRICT SCOPE bullet |
| `generate_palm_reading` signature | UNCHANGED |

## Gate decision table — pass-2 LEFT/RIGHT/HAND_DETAIL fixture (live retrieval, R1's actual chunks)

Ran R1's real per-feature retrieval (live ChromaDB, same as the R1
rider) then applied R3's gate on top — not stubbed, since a live check
was already cheap and available; "stubbed is fine" per the prompt, this
is the stronger real-data version of the same check.

| Feature | Raw chunks | Surviving | Excluded (page, reason) |
|---|---|---|---|
| life line | 3 | 3 | — |
| head line | 3 | 3 | — |
| heart line | 3 | 3 | — |
| fate line | 3 | 3 | — |
| sun line | 3 | 3 | — |
| thumb | 3 | 3 | — |
| fingers | 3 | 3 | — |
| mount of venus | 3 | 3 | — |
| mount of jupiter | 3 | 2 | p.111 (no "jupiter" needle — it's the Mount-of-Venus chapter's opening, correctly excluded) |
| markings/other features | 3 | 2 | p.221 (no markings/hair needle — an unrelated crime-physiognomy passage, correctly excluded) |

**Result for this fixture: `supported_features` = all 10 registry
features (registry order); `unsupported_features` = () (empty);
decline block omitted entirely.** This is a real, credible example of
the gate doing its job (2 chunks excluded for lacking any real
connection to their retrieved feature) without any feature ending up
fully unsupported, since this particular fixture's per-feature queries
happened to surface at least one genuinely on-topic chunk everywhere.
The doctrine-inversion scenario the gate exists to catch (ALL 3 chunks
for a feature failing the needle check) is exercised by test 14a
instead, with synthetic non-doctrine chunks modeled directly on the
real nomenclature/procedural chunks from R1's pass-2 evidence
(`diagnostics/ring3_chunks_S66_pass2.md` — Chapter II line-listing,
"lines of head and heart", modus-operandi passages).

## Test delta (derivation comments quoted verbatim)

21 R1-era tests required fixture edits — NOT because the gate itself
was wrong, but because several shared stub texts (used across many
now-single-feature tests) named OTHER features for narrative flavor,
which the new banned-mention validator correctly flags once those
other features are unsupported. Per the "fix the stub, don't weaken the
gate" instruction, every fix is a text edit with a comment, not a gate
change:

```python
# S67 R3: rewritten LIFE-LINE-ONLY (was: life+heart+head+fate) -- most
# consuming tests' synthetic palm_left now observes exactly ONE feature
# (life line), so a stub draft naming heart/head/fate lines would trip
# the new banned-mention validator on those unsupported features.
_CLEAN_STUB_TEXT = (...)
```
Same pattern applied to `_JARGON_STUB_TEXT` ("mark" -> "sign"),
`_NAVIGATED_STUB_TEXT` ("head line" -> "life line"),
`_MULTI_TERM_STUB_TEXT` (heart/head/fate -> life line, self-help words
`fulfilling`/`journey` preserved unchanged), `_CHEIRO_VOICE_STUB_TEXT`
(thumb/heart/head/fate -> life line only), `test_sources_propagate_book_page_score`'s
two chunk texts (needed a "life" needle to survive the gate at all),
and item 13e's dedupe test chunk (needed BOTH "life" and "head" needles
since the same chunk is checked against 2 different features' needle
sets).

`test_empty_retrieval_proceeds_with_low_confidence_caveat` needed a
NEW genuinely feature-neutral stub (`_GENERIC_NO_FEATURE_STUB_TEXT`,
contains none of the 10 features' needles) — in this test, life line
itself ends up unsupported (search returns nothing), so EVERY registry
feature is unsupported, and the old `_CLEAN_STUB_TEXT` (which names the
life line) would have forced a retry, confounding the test's original
"exactly 1 LLM call" point.

New tests (9 functions — 14b and 14d each pair a main scenario with one
companion boundary case), hardest first:

- **(14a)** `test_doctrine_inversion_guard_fate_unsupported_first_draft_retried_clean`
  — fate line observed, all 3 chunks fail the needle check (synthetic
  nomenclature/procedural chunks) -> first draft names "the fate line"
  -> banned-mention fires -> clean retry passes (2 calls), decline
  block names it.
- **(14b)** `test_needle_collision_battery_sunday_sunny_remarkable_marked_do_not_trip`
  + companion `test_needle_collision_battery_genuine_sun_line_mention_fires`
  — "sunny"/"Sunday"/"remarkable"/"marked" never trip (word-boundary
  verified with a standalone regex check before writing the tests: all
  4 confirmed non-matching against `\b(sun|mark|...)\b`); a genuine
  standalone "sun line" mention does fire and retries clean.
- **(14c)** `test_score_floor_boundary_029_excluded_031_included` — same
  needle-passing text at 0.29 (excluded) vs. 0.31 (survives), boundary
  pair, measure-first style (mirrors R1's fabricated-year boundary
  pair convention).
- **(14d)** `test_decline_block_exact_text_two_feature_list` (exactly 2
  unsupported features via explicit-by-name absence-phrasing on every
  other field, so the exempted genuine-negative-absence features don't
  pollute the list) + companion
  `test_decline_block_absent_when_all_observed_features_supported`
  (block omitted ENTIRELY, not an empty note).
- **(14e)** `test_zero_support_path_routes_to_low_confidence_with_full_decline`
  — search returns a real (non-empty) but off-topic chunk; zero
  features survive the gate; routes to the same low-confidence path as
  a genuinely empty retrieval, full 10-feature decline block.
- **(14f)** `test_supported_unsupported_tuples_propagate_in_registry_order`
  — 3 features given in non-registry input order (fate, heart, life);
  output tuples reflect `_FEATURE_REGISTRY` order regardless.
- **(14g)** `test_f2c_cap_unchanged_banned_mention_fails_both_drafts_stays_failed`
  — banned mention on both drafts -> exactly 2 LLM calls (HARD CAP
  unchanged), fail-closed, second draft's failure reported.

## Suite count

`tests/interpretive/test_palm_reading.py` alone: **36 passed** (27
R1-era + 9 new), 0 failures on final run.

Full suite: **3192 passed, 3 skipped** (was 3183/3 before this task —
net +9). Zero regressions elsewhere.
