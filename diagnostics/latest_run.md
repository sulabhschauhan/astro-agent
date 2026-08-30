# S119 Step 1 — citation sum type (by-chunk | by-rule), additive carrier

DECISION THIS SERVES: if a citation carrier can represent a rule's own
(source_page + source_quote) alongside a retrieval chunk_id, then Step 2 can
stop fabricating chunk_ids for rule-sourced claims; else Step 2 stays blocked
on Claim's shape. Result: carrier landed, additive, nothing switched to it.

## Verification at HEAD (e7eec28, wip/interpretive-pilot) — before editing

`Claim` (agent/interpretive/claim_extraction.py:310-319) = frozen dataclass,
9 fields, ALL required, no defaults; `chunk_id: str` was the 3rd positional.

Every `Claim(...)` construction site in the repo (grep `Claim(` over *.py):

| # | Site | Kind |
|---|---|---|
| 1 | `claim_extraction.py:425` (`_apply_e4`, retrieval path) | production |
| 2 | `rule_to_claim.py:253` (`claims_from_rules`, rule path) | production |
| 3 | `tests/interpretive/test_claim_voicing.py:153` (`_claim` builder) | test |
| 4-8 | `tests/test_app_dogfood_capture.py:163,174,650,661,794` (inline fixtures) | test |

All 8 are keyword-only, all nine fields, none positional.

`.chunk_id` READERS (unchanged this step): `claim_extraction.py:439,635`
(exclusion ledger + overlap diagnostics), `palm_reading.py:1753,1756`
(`_build_sources_from_claims`), `frontend/app.py:195,301,436,1333,1424`
(F5 capture), `scripts/probe_pass5_preflight.py:231,530,536`.
- E-1 (`claim_extraction.py:284-289`) reads `raw_claim["chunk_id"]` against
  the feature's own gated `chunk_map` — CONFIRMED unchanged.
- A1 V-2 (`palm_reading._check_anchor_legality`, :1482) reads chunk_ids off
  the tagged text against `valid_chunk_ids` — CONFIRMED unchanged.
- `claim_voicing` — CONFIRMED never reads `chunk_id`: it reads exactly
  `claim_id` / `claim_text` / `valence` / `observation_basis` (:281 prompt
  line, :196/:210/:577 elsewhere). No `source_quote` field exists on Claim.

## Approach chosen, and why

The sum type is two frozen dataclasses + a union alias:
`CitationByChunk(chunk_id)` | `CitationByRule(rule_id, source_page, source_quote)`.

The carrier is stored as an INSTANCE ATTRIBUTE (`_citation`), **not** as a
tenth dataclass field, and by-chunk is DERIVED (no storage at all).

WHY NOT a real field: `tests/interpretive/test_palm_reading_rules_engine.py:453-458`
pins `{f.name for f in dataclasses.fields(result.claims[0])}` to the exact
9-name set. A tenth field breaks it — i.e. it would have made this step
non-additive, tripping the prompt's own STOP condition. The chosen shape keeps
`__init__`/`__eq__`/`__repr__`/`fields()` byte-for-byte identical, so **no
existing test needed changing.**

Also added (all additive):
- `Claim.citation` property — defaults to `CitationByChunk(chunk_id)`, so the
  plain constructor (all 8 sites above) stays by-chunk exactly as before.
  Raises `ValueError` if a claim has neither a chunk_id nor a rule citation
  (fail-closed, never guesses).
- `Claim.citation_ref` — the single citation-identity accessor. by-chunk
  returns the chunk_id verbatim (identical to `.chunk_id`, so a future
  consumer can swap one for the other with no behavior change); by-rule
  returns `rule:<rule_id>@p<source_page>` — **the quote is deliberately
  excluded from this rendering** so even a consumer that logs the accessor
  cannot leak it.
- `Claim.by_chunk` / `Claim.by_rule` classmethod constructors.
- `chunk_id: str` -> `chunk_id: str | None` — ANNOTATION ONLY (still a
  required positional field, no default); by-rule claims have no chunk_id.
- Sites 1 and 2 migrated to `Claim.by_chunk(...)` (internal only, byte-identical
  result — it makes the branch legible and reduces Step 2 to a one-call flip).
  Test call sites left untouched on the plain constructor.

NO consumer produces or reads the by-rule branch. `resolve_chunk_id`,
`claims_from_rules` drop behavior, E-1, V-2, sources, needles and the capture
net are all untouched.

### Accepted consequences, registered at the code site (not left to be found)
1. `dataclasses.replace(claim, ...)` would DROP a by-rule citation. Verified:
   no caller anywhere in the repo calls `replace()` on a `Claim` (the 7 hits
   are on `DomainAnswer` and `PalmRule`). Step 2 must route through
   `Claim.by_rule`, never `replace`.
2. `__eq__` ignores the citation — two claims identical in all 9 fields but
   citing different rules compare equal. Unreachable in practice: `claim_id`
   is unique within a reading.

### FLAG FOR STEP 2 (drift, not a failure)
`test_palm_reading_rules_engine.py:451-458`'s comment reads "the Claim objects
themselves carry no quote-bearing field". That assertion still PASSES (the
field set is unchanged), but once Step 2 puts the rule path on `by_rule`, the
comment's claim becomes true only of the by-chunk branch — a `CitationByRule`
does carry the quote, off-field. Step 2 should re-word that comment and pin
the containment property directly instead (the new
`test_source_quote_never_reaches_any_voicer_facing_field` already does).

## Tests added (8, all in tests/interpretive/test_claim_extraction.py)
1. `test_existing_style_construction_is_a_by_chunk_citation_with_identical_chunk_id`
2. `test_by_chunk_classmethod_is_indistinguishable_from_the_plain_constructor`
3. `test_claim_dataclass_field_set_is_unchanged_by_the_citation_carrier`
4. `test_by_rule_carries_rule_id_source_page_and_source_quote`
5. `test_by_rule_citation_ref_returns_a_rule_form_without_the_quote`
6. `test_claim_with_no_chunk_id_and_no_rule_citation_raises_rather_than_guessing`
7. `test_source_quote_never_reaches_any_voicer_facing_field` (builds the real
   `claim_voicing._build_user_prompt` and asserts the quote is absent)
8. `test_every_existing_construction_site_shape_still_builds_a_valid_claim`
   (parametrizes the 4 distinct shapes the 8 enumerated sites use)

## Verification
- `python -m pytest -q` -> **3695 passed, 7 skipped** = baseline 3687/7 plus
  exactly the 8 new tests. 0 regressions.
- **NO existing test file was edited.** Only the 8 new tests were appended to
  `test_claim_extraction.py` (plus its import line).
- `python scripts/gate_rule_citations.py` -> `NOT_FOUND_ANYWHERE: 0`
  (4 rule files, 99 live rules, 16 parked).
- Diff is +172/-2 in `claim_extraction.py` (the -2: the `chunk_id` annotation
  line and the `Claim(` -> `Claim.by_chunk(` line) and +5/-1 in
  `rule_to_claim.py`.

## Commit
`c879e45` — pushed to `origin/wip/interpretive-pilot`. Staged files: ONLY `agent/interpretive/claim_extraction.py` (+172/-2), `agent/interpretive/rule_to_claim.py` (+5/-1), `tests/interpretive/test_claim_extraction.py` (+174/-0). CONFIRMED: no existing test changed.
