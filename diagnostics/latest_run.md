# S119 Step 4 — rule-claim citation failures are visible to the capture net

DECISION THIS SERVES: if the capture net can see a rule-claim citation failure,
then Defect 4 (M3) closes and the by-rule flip is observable rather than
silently trusted; else the net has a blind spot exactly where Step 2 moved the
citations. Result: closed, with one measured correction to the task's own plan.

## Verification at HEAD (46573c4/7b09398) — before editing

**`frontend/app.py` wrong_source trigger** — confirmed. It ran
`re.search(r"_p(\d+)_", claim.chunk_id)` for EVERY claim inside
`try: ... except Exception: continue`. Since Step 2 a rule claim carries
`chunk_id=None`, so that call raised TypeError straight into the `continue` —
the trigger silently stopped evaluating rule claims. Silent because the except
was there to swallow a malformed chunk_id, not an entire citation kind.

**claims_inventory render** — the task names `app.py:301`, but the identical
`{claim.chunk_id}` column appears at **four** sites: 301 and 436 (dogfood-capture
writers, `claim`) and 1333 and 1424 (Streamlit captions, `_claim`). All four
rendered a bare `None` for rule claims. Fixing only the named one would have left
three showing `None`, so all four were converted.

**`capture_net.py`** — record shape confirmed and matched, not reinvented:
`record(trigger, producer, payload, reading_id)` appends one JSON line
(`ts/reading_id/trigger/producer` + payload keys), gated by the `_PAYLOAD_KEYS`
allow-list, fail-safe (never raises). Producers follow `map_fallback_audits`'
shape: iterate, map, call `record`, silent on a clean run.

**Invocation site** — an existing one was extended, not added. `reading_id` is
already minted in `prepare_palm_reading` (`uuid.uuid4().hex`) for the S109
fallback events, in the SAME branch that calls `_prepare_deterministic_prep`, so
it is threaded through and one reading keeps one id. The S109 path is untouched.

**Trigger choice** — `wrong_source` maps cleanly; **no new category was needed
and none was invented.** A rule that fired but cannot cite has a broken citation
identity — the same failure class as the existing `hallucination` disposition (a
choice outside the closed vocabulary), which already maps to `wrong_source`.
`capture_net_digest._KNOWN_TRIGGERS` derives from `_DISPOSITION_TO_TRIGGER.values()`
and already contains it, so the digest needed no edit (asserted in a test).

## MEASURED CORRECTION to the task's plan — read this before reviewing the diff

The task says to re-key the trigger "off the by-rule source_page". Implemented
literally, that would have been a **new bug**: rule `source_page` and
`_FEATURE_PAGE_RANGES` are **different coordinate systems**.

- Rule pages anchor to `data/cheiro/cheiro_clean_v1.json` — the page-level corpus
  the authoring gate verifies against.
- `_FEATURE_PAGE_RANGES` comes from `data/cheiro_feature_pages.json`, in the
  chunk corpus' `page_ref` numbering used by the retrieval page-range gate.

Measured this session across all 99 live rules:

| topic_group | rule source_page | feature | `_FEATURE_PAGE_RANGES` | agrees? |
|---|---|---|---|---|
| line_head | 145–148 | head line | (145, 155) | yes |
| line_heart | 156–161 | heart line | (156, 161) | yes |
| line_life | 134–139 | life line | (133, 139) | yes |
| **line_fate** | **103–105** | **fate line** | **(162, 165)** | **NO — ~+59 offset** |

Range-checking rule pages would tag `wrong_source` on **all 16 fate rules on
every run that fires one** — turning the fix into a false-positive generator on
the very feature this whole arc is about. (`mount_venus`/`mount_saturn` carry
their own out-of-range outliers: M_004/M_005 p183, M_006 p222, M_007/M_008 p221,
M_015 p217.)

**What was implemented instead, and why it is the right check:** the page-range
check exists to catch a RETRIEVAL claim citing a chunk from the wrong chapter.
That failure mode cannot occur for a rule claim, whose citation is the rule's own
authored, gate-verified span (`gate_rule_citations.py`: NOT_FOUND_ANYWHERE 0/99).
The rule-claim analogue of "wrong source" is a citation that is **missing or
unusable** — no `source_page`, or an empty `source_quote`. That is what
`_rule_claim_citation_is_broken` checks, and it matches the task's own test
spec ("wrong_source only if its citation is genuinely broken; a clean by-rule
claim is NOT falsely flagged"). Recorded at the code site, not just here.

## Implemented

1. **Trigger re-keyed per citation kind** (`frontend/app.py`). Two new helpers
   replace the inline regex: `_rule_claim_citation_is_broken` (rule claims only —
   returns False for by-chunk, no opinion) and `_retrieval_claim_page` (by-chunk
   only — byte-identical to the old regex, returns None otherwise). The
   silent-TypeError dependence is gone: each kind is now dispatched explicitly.
2. **All four claims_inventory renders** use `_citation_column(claim)` →
   `claim.citation_ref`: the chunk_id verbatim for retrieval claims (column
   unchanged for them), `rule:<rule_id>@p<page>` for rule claims. The quote is not
   part of that form, so no book prose enters any capture.
3. **`capture_net.record_dropped_rules`** — one `wrong_source` event per dropped
   rule id, producer `palm_reading_rules_engine`, disposition
   `dropped_rule_no_citation`. Wired in `_prepare_deterministic_prep`, fail-safe,
   sharing the S109 `reading_id`. **Dormant by construction**: Step 2 removed the
   only drop path, so the list is always `[]` and a real run writes nothing.
   `_PAYLOAD_KEYS` extended by exactly two keys — `rule_id` (an opaque id) and
   `source_page` (an integer). **`source_quote` was deliberately NOT added**: the
   allow-list is the containment mechanism, and the quote is the one rule-citation
   field that is book text.
4. **`surviving_rule_features` surfaced** in the capture beside
   `surviving_rule_ids` (Step 3's note) — it fits the existing line shape exactly,
   same `.get()`-defaulted style, so an older capture without the key still
   renders. This makes "which features was the support gate overruled on?"
   answerable from the capture alone.

NOT touched: needles, sources builder (Step 5), the S109 fallback path, resolve
logic, `map_fallback_audits`.

## The fix is discriminating — measured, not asserted

With the trigger temporarily reverted to the pre-fix inline regex, **4 tests
fail** — exactly the ones asserting a broken rule citation IS caught — while
every by-chunk parity test passes either way, which is itself the proof that the
retrieval path is genuinely unchanged. Restored, all pass. (Revert run and
restored in-session; no artifact left behind.)

## Tests — 22 added, 0 existing changed

`tests/test_app_dogfood_capture.py` (+257/-0) and
`tests/interpretive/test_capture_net.py` (+108/-0). Both diffs are purely
additive; the only non-test line added is a `import pytest`.

Frontend trigger:
1. `test_rule_claim_does_not_raise_and_a_clean_citation_is_not_flagged` — HARDEST
   CASE. Also pins the coordinate-system trap explicitly: asserts the claim's
   source_page (103) is OUTSIDE `_FEATURE_PAGE_RANGES["fate line"]` (162, 165) and
   that it is still not flagged.
2. `test_rule_claim_with_an_unusable_citation_is_tagged_wrong_source` ×3
   (no source_page / empty quote / whitespace quote).
3. `test_excluded_rule_claim_is_skipped_even_when_its_citation_is_broken` —
   precedence unchanged.
4. `test_by_chunk_claim_outside_its_feature_page_range_still_fires_wrong_source` —
   GUARD/PARITY. **This trigger had no test at all before this step**; the
   retrieval path is now pinned, not merely preserved.
5. `..._inside_its_feature_page_range_is_still_clean`,
   `..._with_a_malformed_chunk_id_is_still_skipped_not_flagged`,
   `..._for_a_feature_with_no_page_range_is_skipped` — the three skip paths.
6. `test_mixed_run_flags_only_the_broken_rule_claim` — both kinds in one run.

Render + diagnostics:
7. `test_claims_inventory_renders_the_by_rule_citation_form_not_none`,
   `test_claims_inventory_by_chunk_column_is_unchanged`,
   `test_no_source_quote_reaches_the_dogfood_capture`,
   `test_stage1_diagnostics_render_surviving_rule_features`,
   `test_stage1_diagnostics_tolerate_a_capture_without_the_new_key`.

Capture-net producer:
8. `test_dropped_rule_ids_producer_writes_one_wrong_source_record_per_rule`,
   `test_dropped_rule_trigger_is_already_known_to_the_digest`,
   `test_dropped_rule_producer_is_dormant_on_the_real_state` ×3 (`[]`/`None`/`()`),
   `test_dropped_rule_producer_never_raises_on_an_unwritable_path`,
   `test_no_source_quote_can_reach_a_capture_record` — feeds a payload that
   explicitly carries `source_quote`/`claim_text`/`raw_prose` and proves none
   reaches the record, because the allow-list is the mechanism.

**No existing test needed changing.**

## Verification
- `python -m pytest -q` -> **3730 passed, 7 skipped**. Step-3 baseline 3708/7;
  +22 = 3730. **Zero regressions.**
- `python scripts/gate_rule_citations.py` -> `NOT_FOUND_ANYWHERE: 0`.
- Files touched: 5 — `capture_net.py` +50/-0, `palm_reading.py` +25/-0,
  `frontend/app.py` +106/-11, and the two test files. No unrelated staging.

## Found while implementing (no action taken)
`_format_stage1_feature_diagnostics_lines` selects its engine branch on the
presence of `observation_record` in the diag dict — deliberately keyed on payload
shape rather than the `"_rules_engine"` name (its own docstring says so, to
survive a key rename). Noted because it is non-obvious to anyone writing a
fixture for it; the two new diagnostics tests carry that note inline.

## Commit
`17cb671` — pushed to `origin/wip/interpretive-pilot`. Staged: ONLY the 5 files listed above. The commit message carries the coordinate-system correction, so a reviewer reading `git log` alone still sees it.
