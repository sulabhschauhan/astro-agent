# S119 Step 2 — THE FLIP: rule claims cite by-rule (31% -> 100% citation accuracy)

DECISION THIS SERVES: if a rule can cite its own gate-verified span instead of a
re-derived chunk, then Defect 1 (13 silently dropped rules) and the 52 silent
mis-cites close outright; else they stay open. Result: closed, measured 99/99.

## Verification at HEAD (c879e45/64f038c, wip/interpretive-pilot) — before editing

**`claims_from_rules` (rule_to_claim.py:241 old)** — called
`resolve_chunk_id(rule.source_page, chunks_path)`; on `None` it appended to
`dropped`, logged a WARNING and `continue`d (the rule vanished, consuming no
claim_id). `citations[claim_id]` carried
`rule_id/chunk_id/source_page/source_quote/topic_group/evidence_confidence`.
`diagnostics = {"citations", "dropped_rule_ids"}`.

**Step-0 baseline re-measured this session** (`probes/citation_accuracy_audit_S119.py`,
unmodified): `RESOLVED_CORRECT 31 | RESOLVED_WRONG 52 | DROPPED_NONE 13 |
NO_ANCHOR_ANYWHERE 3` over 99 live rules = **31.3%**.

**E-1 — NO CHANGE NEEDED, and here is why.** E-1 lives inside
`claim_extraction._validate_and_filter`, reachable only from
`extract_claims()`. `palm_reading._prepare_claims_from_rules` (the rule path)
never calls `extract_claims` — its chain is `load_rule_set -> extract_observation
-> to_vision_payload -> to_tokens -> match/resolve_priority ->
rule_to_claim.claims_from_rules`, and that module's own docstring states the
deterministic path is a *replacement* for `extract_claims`, "deliberately NOT a
fallback". **The rule path never reaches E-1.** Step 0's evidence index was
correct. E-1 is untouched; its by-chunk behavior is pinned unchanged by a new
test.

**A1 V-2 (`_check_anchor_legality`) — NO CODE CHANGE NEEDED, verified twice over.**
1. It is RETIRED-NOT-DELETED (palm_reading.py's own docstring): grep shows zero
   production call sites — only `test_palm_reading.py:1773` (which asserts its
   retired behavior) and two archived probe scripts. The LIVE analog is
   `claim_voicing._check_tag_legality` (V-3), which keys on `claim_id` only and
   is blind to the citation branch entirely.
2. Even if it were live, a by-rule anchor is **out of its jurisdiction by
   construction**: `CHUNK_ANCHOR_TAG_PATTERN` accepts only `[OBS]` or
   `[<word>_p<digits>_c<digits>]`, so `[rule:FT_003@p103]` (the `citation_ref`
   form) never enters `cited` and can never be reported unknown/malformed.
   This is now written into V-2's docstring and pinned by two tests — one
   proving a by-rule anchor passes against an EMPTY legal set (strictest input),
   one proving a fabricated by-chunk anchor still fails (guard intact).

**Display anchor — already citation-agnostic.** The live per-claim display anchor
is Stage 2's `[C<n>]` claim_id tag (`_STAGE2_TAG_PATTERN`), identical for both
citation kinds; chunk_ids appear in no Stage-2 output. The by-rule anchor *form*
is `Claim.citation_ref` -> `rule:<rule_id>@p<page>` (quote excluded by design),
landed in Step 1 and now exercised. No emitter change was required.

## Implemented

1. **`claims_from_rules` — the flip.** `resolve_chunk_id` call and the None-drop
   branch DELETED. Every surfaced rule now builds `Claim.by_rule(rule_id,
   source_page, source_quote, ...)`. `chunks_path` retained for signature
   stability, now unused. `citations[...]["chunk_id"]` is now always `None`
   (key kept for diagnostics shape stability).
2. **`dropped_rule_ids` — retired tripwire.** Still in the diagnostics dict,
   ALWAYS `[]`, with a comment that a non-empty value now signals a real
   regression rather than a data condition.
3. **`resolve_chunk_id` — left defined**, docstring updated to record that it is
   off the citation path and is now only exercised by the Step-0 baseline probe.
4. **V-2 docstring** — records the by-rule jurisdiction fact above.
5. **Rules-engine test comment** — reworded per Step 1's flag (below).

NOT touched, per scope: needles, capture net (Step 4), sources builder (Step 5),
jurisdiction/decline set (Step 3), `resolve_chunk_id`'s definition.

## THE FIX, MEASURED

| | OLD (re-derived chunk) | NEW (by-rule) |
|---|---|---|
| live rules | 99 | 99 |
| claims produced | 86 | **99** |
| dropped | **13** | **0** |
| citation correct | **31 (31.3%)** | **99 (100.0%)** |
| mis-cited | 52 RESOLVED_WRONG + 3 NO_ANCHOR | **0** |

100% is not asserted by construction — every one of the 99 claims' citations is
independently re-verified in-test through `scripts/gate_rule_citations.py`'s own
`classify_rule_citation` (page-level corpus + the same overlap primitive):
**99/99 CLEAN**. `python scripts/gate_rule_citations.py` -> `NOT_FOUND_ANYWHERE: 0`.

`probes/citation_accuracy_audit_S119.py` measures the OLD resolve path and is now
a **baseline artifact** — left untouched deliberately: it is the before-picture
this step is measured against.

## Tests

**8 added** (`tests/interpretive/test_rule_to_claim.py`):
1. `test_every_live_rule_produces_a_claim_citing_its_own_gate_verified_quote` —
   HARDEST CASE, all 99 live rules: 0 dropped, contiguous C1..C99, every citation
   equals its rule's own source_page+source_quote AND passes the authoring gate.
2. `test_the_fate_offset_rules_no_longer_mis_cite` — the +60 offset is now inert.
3. `test_ft003_extreme_good_fortune_survives_to_voicing_citing_by_rule` — the
   original live failure, end to end. Asserts the killing precondition is STILL
   true of the corpus (`resolve_chunk_id(103) is None`), so the rule is saved by
   not consulting the chunk data, not by the data changing; then voices it.
4. `test_dropped_rule_ids_is_empty_on_rules_that_previously_dropped` — all 13.
5. `test_by_rule_anchor_is_out_of_v2_jurisdiction_not_flagged_fabricated`.
6. `test_v2_still_kills_a_fabricated_by_chunk_anchor` — guard intact.
7. `test_by_chunk_retrieval_claims_are_unchanged_through_e1_and_v2`.
8. `test_source_quote_reaches_no_voicer_facing_field_on_the_by_rule_path` —
   all 99 claims + the real `_build_user_prompt` output.

### CHANGED existing tests — 4, each justified

| test | before | after | why the new behavior is correct |
|---|---|---|---|
| `test_unresolvable_page_rule_is_dropped_not_crashed` -> renamed `..._is_no_longer_dropped_it_cites_itself` (`test_rule_to_claim.py`) | `claims == ()`, `dropped_rule_ids == ["BOGUS_PAGE"]` | 1 claim, `dropped_rule_ids == []`, by-rule citation | This test asserted **the defect itself**. "Unresolvable page" only ever meant the CHUNK corpus has no non-empty chunk on that page number — a property of `chunked_chunks.json`, unrelated to whether the rule's own quote is genuine. Dropping discarded a gate-verified claim. |
| `test_claim_id_ordering_stable_across_multi_rule_set_no_gaps` (`test_rule_to_claim.py`) | 4 rules -> `C1,C2,C3` (BOGUS_PAGE dropped without consuming a number) | 4 rules -> `C1..C4` | The property this test exists to pin — **contiguity, no gaps** — is unchanged and still asserted. Only the count moved, because the drop it was compensating for is gone. |
| `test_hl006_claim_object_fields` (`test_rule_to_claim.py`) | `chunk_id == "cheiroslanguageo00chei_1_p160_c0"` | `chunk_id is None`, citation `== CitationByRule("HL_006", 160, <quote>)`, `citation_ref == "rule:HL_006@p160"` | HL_006 is one of the 31 whose page DID resolve correctly, so the old value was not wrong — but it pinned the **re-derivation mechanism**, which is exactly what this step removes. |
| `test_fired_rules_become_claims_and_reach_stage_two` (`test_palm_reading_rules_engine.py`) | `all(c.chunk_id.startswith("cheiroslanguageo00chei_1_p147"))` | `all(c.chunk_id is None)` + `citation_ref == ["rule:H_005@p147", "rule:H_006@p147"]` | Same reason: it pinned the mechanism, not the provenance. The provenance (p147) is now asserted **directly off the rule**, which is strictly stronger. |

Every one of the four is explained by the intended flip. No other test changed.

**Also reworded (Step 1's flagged drift, not a behavior change):**
`test_palm_reading_rules_engine.py`'s "the Claim objects themselves carry no
quote-bearing field" comment. The dataclass FIELD set is still unchanged and still
asserted; the comment now says so accurately, and the property that actually
matters — **containment** — is asserted directly (the quote IS reachable via the
citation, and is absent from all four voicer-facing attributes).

## Verification
- `python -m pytest -q` -> **3703 passed, 7 skipped**. Step-1 baseline was
  3695/7; +8 = 3703. **Zero regressions.**
- `python scripts/gate_rule_citations.py` -> `NOT_FOUND_ANYWHERE: 0` (99 live,
  16 parked).
- Files touched: exactly 4 (`rule_to_claim.py` +66/-29, `palm_reading.py` +18/-0
  docstring only, `test_rule_to_claim.py` +272/-8, `test_palm_reading_rules_engine.py`
  +28/-3). No unrelated staging.

## Flagged for later steps (found, not fixed here — out of this step's scope)
- **Step 4 (capture net):** `frontend/app.py:195`'s `wrong_source` trigger does
  `re.search(r"_p(\d+)_", claim.chunk_id)`. With `chunk_id=None` this raises
  TypeError inside the existing `try/except Exception: continue` — **no crash**,
  but the trigger now silently never fires for rule claims. It should key on the
  by-rule `source_page` instead. `app.py:301`'s claims_inventory line likewise
  renders `None` in the chunk_id column.
- **Step 5 (sources):** `_build_sources_from_claims` looks up
  `chunk_lookup[(feature, claim.chunk_id)]` against this run's `gated_results`;
  a by-rule claim misses and is skipped (no crash — `key=(None, feature)` is a
  valid tuple). Bounded honestly: before this step at most the 31
  RESOLVED_CORRECT rules could ever have produced a source, and only when that
  chunk was ALSO in that run's gated set; now none do. Step 5 owns rebuilding
  sources from the by-rule citation.
- `scripts/probe_pass5_preflight.py:530` would classify by-rule claims as
  "orphaned" (`c.chunk_id not in valid_chunk_ids`). Probe script, not production,
  not run by the suite.

## Commit
`f9383d4` — pushed to `origin/wip/interpretive-pilot`. Staged: ONLY the 4 files listed above.
