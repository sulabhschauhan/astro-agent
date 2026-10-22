## Session Log

> ARCHIVES: Sessions 19-66 -> `SESSION_LOG_ARCHIVE_S19-S66.md` (split at S81); Sessions 67-104 -> `SESSION_LOG_ARCHIVE_S67-S104.md` (split at S105); Sessions 105-145 -> `SESSION_LOG_ARCHIVE_S105-S145.md` (split at S146, S151). This live file holds head-matter + S146 onward.

## S95 -- palm interpretation CLOSED on Head+Heart; architecture frozen; pipeline spec created

OUTCOME: palm interpretation architecture is DONE and proven on Head(26)+Heart(21)=47 rules.
Remaining lines are volume, not design -- run the frozen pipeline.

BUILT:
- `agent/interpretive/palm_select.py` = canonical path: `match()` hard-fire + soft-LLM on
  verbatim sentences + vocab guard (unmatched surfaced) + subset precedence
  DEMOTE-not-DELETE (`result["suppressed"]`, never dropped). Commit `d9a8ffa`.
- `data/palm_rules/_doctrine/PALM_PIPELINE.md` = the frozen 0-7 checklist every remaining
  line MUST follow. Commit `bb20375`.
- Diagnostic scans committed: vocab reachability (`334f0e5`), hard/soft partition
  (`802fb83`), soft-feature eval harness + C2 probe (`0238cc2`).

**CORRECTION to the dictated close-out (recorded, not silently amended -- same class as the
S72 carry-forward correction):** the lambda gates are **NOT yet retired**. No script imports
`palm_select` (verified by grep at close). The repoint is BLOCKED: `smoke_test_palm_llm_select.py`
and `eval_harness_soft_v1.py` hold hand-state fixtures in a private vocabulary
(`head` / `origin: "Jupiter_touching_life"`) that `match()` cannot read; a bare import swap
gates out every rule and collapses the smoke test's A-vs-B discrimination. Translating the
fixtures to canonical ontology form (plus `magnitudes`/`targets` buckets) is a data change
needing its own ratified task. The retirement is sound in principle -- `match()` was shown to
reproduce both lambda gates (Case A -> H_027, Case B -> H_002) -- but it has not shipped.

KEY DECISIONS (do NOT re-litigate):
- `match()` (antecedent-matching) is the canonical hard engine. "Matching is dead" applies
  ONLY to claim/meaning matching (paraphrase leak), NOT antecedent matching.
- `high`/`low`/`short`/`long` = SOFT; NO anchors written even for the head line (Cheiro
  rarely defines them metrically; anchors are per-(feature,term), thin, not worth the cost).
  The LLM judges relative terms like a human reader, from the whole verbatim sentence, with
  no benchmark supplied.
- Precedence = suppress-always by strict subset, but DEMOTE not DELETE (auditable, simple,
  one check; no defeats/refines 3-way engine). Only 5 rules can ever be demoted: HL_001,
  HL_004, HL_011, H_011, H_021. Sulabh accepted the contradicting demotions (#4/#5 HL_011
  "happiest nature" vs HL_005; #7 H_021 "brutal nature").
- Fixes landed: H_025 `doubled`->`double` (`c32c850`); `Branching` -> `Line of Heart`
  ontology mapping for HL_014, approved in-session and committed separately in the S95
  close-up (`aef43de`) -- `attribute_feature_mapping["Branching"]` now includes
  `Line of Heart`, so HL_014's `Line of Heart.Branching = single` is REGISTRY-LEGAL and its
  value is in the emitted pool. **HL_014 remains PARKED regardless:** registry-legal is not
  emission-reachable, and "bare of branches" is `BRANCHES_TO: none` in the vision layer, so
  nothing emits a bare `Branching` observation for the heart line. Un-parking HL_014 is a
  vision-layer task, not a registry one.

GENERAL LEARNINGS (transfer to astrology):
1. Input-vocab and rule-vocab are ONE contract; a rule fires only if its exact trigger word
   is emitted. Mismatch = silent miss, invisible to fabrication guards. Reachability is a
   per-domain CI gate.
2. NAMING-MISMATCH (align the words) vs COMPUTED-TERM (compute and feed it, never make the
   LLM infer it, e.g. deep -> "stronger"). They look identical; they are fixed differently.
3. Never make the LLM bridge two representations.
4. A "fabrication" symptom is usually a vocabulary problem in disguise -- check the words
   before building gates and guards; per-case bridges do not scale.
5. registry-legal != emission-reachable -- two separate checks.
6. Precedence is SEMANTIC, not geometric; subset geometry cannot tell refine / reverse /
   independent apart. We chose logged suppression to stay simple without silent data loss --
   but astrology's cancellation yogas (Neecha Bhanga) will likely need authored defeat tags.
   Flag, do not auto-suppress silently.

QUARANTINE (needs_remodel, gate skips, re-model each as its own task): H_013 (star on
Jupiter), H_024 (branch-toward Luna), H_023 (any-mount wildcard), H_018/019/020 (hand Type
attr), HL_002 (finger-of-Jupiter), HL_015 (faded).

PARKED: 4 Quadrangle rules (H_010a/b, HL_006, HL_021) need the vision layer to emit
quadrangle breadth -- bundle with the vision layer. Consequence measured this session: every
cross-group precedence demotion has an unreachable primary, so corpus-wide precedence is
currently INERT in production.

REMAINING PALM (run PALM_PIPELINE.md per line): Life [file exists, UNVALIDATED -- and note
`load_rule_set()` already merges its 13 rules into a 60-rule live set, 3 antecedents fail
reachability, schema diverges: `parked_pending` vs `parked_pending_relation_target`, no
`retired_superseded`], Fate, Sun, Health, Mars, Mounts (7), Marks (cross/star/island/square),
Hand-types, fingers/thumb/nails.

STILL OPEN (not started): eval answer keys (Sulabh authors, non-delegable); VISION layer
photo -> hand-state (UNTESTED, the real risk); `palm_select.py` has NO tests; RULING 2's
corpus-wide `resolve_priority()` edit in `palm_rules_table.py` is ratified but unimplemented
(with the rename of `test_priority_never_suppresses_across_different_topic_groups`, whose
name now overclaims).

## Archived from CLAUDE.md (Session 45 compression)

Items below were moved from CLAUDE.md to reduce per-query token cost.
They remain valid decisions/findings — just not needed on every Claude
Code invocation.

### Locked Decisions (archived)

- **Hand-laterality via vision LLM** — evaluated Sessions 15-16 under 3 framings; consistently unreliable (worst case 5/6 right-bias on unlabeled images). Permanent: human confirmation at upload, no GPT laterality judgment.
- **No Chart dataclass / VargaType enum** (Session 20) — neither exists; Navamsa built as a pure `(jd_ut, asc_lon_sidereal)` function instead. Revisit only when a varga module genuinely needs shared chart-identity state.
- **Reference-chart fixture template** (Session 20) — one standalone test per chart, not `@pytest.mark.parametrize`, when expected-value structures differ; delete skip-stub parametrize blocks once empty.
- **Transit fixture anchor** (Session 21, PROVISIONAL) — 18:30 UTC (00:00 IST next day); needs second-date corroboration before treating as final.
- **Bisection-over-discrete-state range-scan** (Session 24) — locked pattern for all transit-range-scan modules, NOT fixed-step. Internal-only constants: 0.5 JD coarse step, 1e-6 JD bisection precision, max_iters=40; no caller-facing precision params. Threshold-discipline rejects tunable step params without a classical anchor; empirically, bisection vs. a naive 12h grid differs by 8-11h per Moon ingress (P2.3.2 Fixture 1 epistemic check).
- **Per-module ephemeris helpers stay duplicated** (Session 24) — `_moon_sign`/`_moon_nakshatra`/`_saturn_sign` etc. are not cross-imported between transit modules; `helpers/ephemeris.py` extraction (still a stub, Session 19+) remains the agreed future remediation.
- **Per-module bisection helper stays duplicated** (Session 24) — `_bisect_transition` is reimplemented per module (chandrabala.py, tarabala.py), not imported between them. Extract to `helpers/` once a third module carries it.
- **Sign convention split, transits** (Session 19-24) — `gochara.py` uses 1-12 (1=Aries); `sade_sati.py`/`chandrabala.py` use 0-11 (0=Aries); `tarabala.py` uses 0-26 (0=Ashwini) for nakshatras. `gochara.py` normalization remains an unscheduled backlog item.
- **Binary FAVORABLE/UNFAVORABLE across Muhurta limbs** (Session 24) — Chandrabala and Tarabala both lock binary categories; NEUTRAL classifications (2nd/5th-house Chandrabala, activity-dependent Janma Tara) are deferred jointly to V1.1.
- **PVR source-ladder asymmetry, Chandrabala vs. Tarabala** (Session 24) — Chandrabala lives in PVR's transit chapter (Ch.26 Table 63), not his Muhurta chapter; Tarabala lives directly in PVR's own Muhurta chapter (Ch.36 §36.3). Both still bind their FAVORABLE/UNFAVORABLE enums from mainstream Muhurta lineage, not derived purely from PVR.
- **Transit range-scan test layout** (Session 24) — `test_<module>.py` (instant) + `test_<module>_windows.py` (range-scan), both under `tests/calculations/transits/`.
- **Panchaka V1 = Definition B** (Session 25) — Moon sidereal longitude in [300, 360) degrees (Aquarius + Pisces). Binary IS_PANCHAK / NOT_PANCHAK only.
- **Panchaka Definition A deferred** (Session 25) — nakshatra-pada-exact start (~293°20', Dhanishtha's 3rd pada) deferred to V1.1 as a round-degree simplification; the ~6°40' gap vs. Definition B is documented in `panchaka.py`'s docstring as risk-accepted, not reconciled.
- **Panchaka named-type overlay deferred** (Session 25) — Raj/Agni/Chor/Mrityu/Rog Panchak classification by entry weekday deferred to V1.1; requires a Panchak-entry-vara backward scan plus a location/timezone dependency, out of scope for V1's binary surface.
- **Panchaka Rahita is a separate concept** (Session 25) — the Andhra/Telangana intraday Muhurta system (function of Tithi+Vara+Nakshatra+Lagna) is NOT a Panchaka extension; documented as a future standalone `panchaka_rahita.py` module, not folded into `panchaka.py`.
- **Panchaka source** (Session 25) — Definition B and the three V1.1 deferrals above sourced from Muhurtha-Chinthamani p.84-85; verified this session against the project's own RAG corpus (`data/all_chunks.json`, OCR'd from `data/pdfs/Muhurtha-Chinthamani.pdf`), not a fresh direct PDF read.
- **Design-proposal-first is not default** (Session 25) — earn a pre-implementation design-proposal pass only when (a) classical sources are genuinely ambiguous post-agent-pass, (b) the module structurally differs from existing precedent, (c) fixtures require pre-implementation ephemeris computation, or (d) the API shape is uncertain; default to a direct implementation prompt.

### Known Source Divergences (archived)

#### Shadbala Saptavargaja Bala scoring
- **Spec source:** BPHS 27.2-4 literal (Mooltrikona=45, Own=30, Pramudita=20, Shanta=15, Din=10, Duhkhita=4, Khala=2)
- **AstroSage delta:** AstroSage uses an unpublished scoring table that produces totals 10-30 Virupa higher per planet. Reverse-engineering from public data is not reliably possible — Sun fits Adhimitra=30/Sama=7.5 but Moon does not fit the same table.
- **User impact:** Near-zero in V1. Shadbala feeds Yoga detection (P3) and Trigger Naming (P7), both of which consume RANKING, not absolute values. Ranking is stable across BPHS vs AstroSage scoring tables for the dominant components (Sthana base + Kala + Chesta).
- **Revisit trigger:** Phase A user testing surfacing a ranking complaint that traces to Saptavargaja precision.

#### Shadbala Drekkana Bala
- **Spec source:** AstroSage + JHora convergence on 1 Virupa flat constant for all planets (three-tier hierarchy rule).
- **BPHS divergence:** BPHS 27.6 specifies 15/0 binary by gender×decanate. Locked at 1 Virupa per AstroSage parity.

#### Ayana Bala — Moon/Venus high-declination edge case (V1 accepted gap)
- **Spec source:** PyJHora `(24.0 + adj_decl) * 1.25` formula.
- **Validation oracle:** AstroSage Kundli PDFs (4 charts).
- **Pass tolerance:** ±2.0 Virupa for 5/7 planets; ±6.0 Virupa for Moon and Venus.
- **Delta magnitude:** Moon and Venus at near-maximum declination (≈23.8°) compute to ~59.7 and ~59.9 respectively; AstroSage shows 54.45 and 56.21. Other 5 planets (Sun, Mars, Mercury, Jupiter, Saturn) match within ±2.
- **User impact:** Moon Shadbala total delta ~1.1% (5.27 of 483.91). Negligible for Shadbala threshold checks (min_required=6.0 Rupa, computed ~8.07, delta does not change strong/weak classification).
- **Revisit trigger:** If user testing surfaces complaints about Moon/Venus Shadbala values being off, investigate AstroSage's exact Ayana algorithm by reverse-engineering against a chart with Moon/Venus at moderate declination (≈10°) where the formula deltas should be smaller.
- **Root cause hypothesis (not yet confirmed):** AstroSage may use a different obliquity constant or apply a soft cap below 60 Virupa for high-declination cases. PyJHora's calibrated constant (24.0) matches Sun within 0.30 but diverges for outer planets at extreme declination.

#### Shadbala Kala Bala — Sun cross-chart Abda/Masa divergence
- **Spec source:** BPHS 27.7-13 (Abda/Masa/Vara/Hora Bala — calendar-lord assignment by solar month/day ingress).
- **AstroSage delta:** Sulabh Sun kala_total validated within ±2 Virupa, but Surbhi chart showed Jupiter +31 and Saturn -59 Virupa divergence, traced to Abda=15/Masa=0 vs computed Abda=0/Masa=0 — a solar-month ingress date disagreement between BPHS calendar-lord assignment and AstroSage's algorithm. Surfaced during P2.5.7 totals testing (test_shadbala_totals.py Layer B); kala_bala.py itself was never tested against Surbhi at this granularity.
- **User impact:** Limited to Sun kala_total cross-chart comparisons; does not affect Sulabh (the primary validated chart) or other planets.
- **Revisit trigger:** If P3 Yoga detection or P7 trigger-naming surfaces a ranking anomaly traceable to Sun kala_total on a non-Sulabh chart. Not re-opened proactively — within the 2-diagnostic-attempt budget, this is deprioritized behind Drik Bala and P3.

#### Pancha Mahapurusha real-chart validation (Session 40)
- **Sulabh zero-yoga result:** Confirmed against `tests/fixtures/jhora_sulabh.md` independent JHora yoga table — no Ruchaka/Bhadra/Hamsa/Malavya/Shasha listed there.
- **Surbhi (Shasha/Saturn/house4), Sheridan (Malavya/Venus/house1), David (Hamsa/Jupiter/house7):** NOT independently cross-validated. No JHora yoga-tab screenshot or AstroSage "Yogas in your horoscope" section is captured in project fixtures for these three charts. Results were derived from `kendra_bala=60` + `ochcha_bala`/`ojayugma_bala` reverse-inference from `shadbala_fixtures.py` and confirmed by the passing test assertions, but no independent oracle cross-check exists yet.
- **Revisit trigger:** When JHora yoga-tab screenshots are captured for Surbhi/Sheridan/David (same process as `jhora_sulabh.md`), re-run the Layer I real-chart tests and add oracle citation comments to `test_pancha_mahapurusha.py` TestRealCharts.

#### Sequencing lock violation (Session 40)
- **Deviation:** Session 31's locked decision (Phase 1 Bhava Bala + Ishta/Kashta, then thin-slice pipeline checkpoint, BEFORE Phase 2 vargas, BEFORE Phase 3 yogas per Master Build Plan's own "Why third: need Phases 1-2 complete") was not followed — Session 40 proceeded directly to Phase 3 Pancha Mahapurusha yoga detection with neither Phase 1 nor the Phase 2 checkpoint done.
- **Realized risk:** Low in this specific case (Pancha Mahapurusha depends only on dignity + kendra house, confirmed independent of varga/Bhava Bala data), but the deviation was unflagged and undocumented until caught retroactively.
- **Going forward:** Phase 1 (Bhava Bala + Ishta/Kashta) resumes next, per the original Session 31 lock — no further Phase 3 sessions (Raja/Dhana/Neecha Bhanga/Special yogas) until Phase 1 + the thin-slice pipeline checkpoint are complete, unless a future deviation is explicitly proposed and confirmed in design chat first, not inferred from a session handover summary.

#### Bhava Dig Bala — RESOLVED (Session 41 investigation → Session 42 implementation)
- **Spec source:** PyJHora `strength.py::_bhava_dig_bala` — Porphyry/Sripati house cusps (NOT equal-house from Lagna, the Session 41 hypothesis tested and rejected), rasi-animal-group discrete taper `abs(60 - abs(h)*10)` gating each house's own cusp longitude against 4 classical rasi-animal groups (Nara/Jalachara/Chatushpada/Keeta, anchored at houses 1/4/7/10 respectively). A different formula family from the originally-attempted continuous BPHS 27.26-29 degree-arc/3 formula — not a refinement of it.
- **Discovery method (two-stage, template for future stuck investigations):** (a) formula family identified via OUTPUT FINGERPRINTING before any source code was read — AstroSage's Bhavdig Bala values across all 4 charts are all clean multiples of 10, which ruled out a continuous-arc formula on its face; (b) exact rasi-group longitude boundary constants required a dedicated VERBATIM RE-EXTRACTION prompt after an earlier investigation report paraphrased/summarized the boundary tuples and corrupted a value, producing a false negative on House 1 during validation.
- **Validation:** 48/48 exact match (4 charts × 12 houses: Sulabh, Surbhi, Sheridan, David) against AstroSage's BhavBala Table Bhavdig Bala row. Cusps via new `compute_porphyry_house_cusps()` (`agent/chart_calculator.py`, pyswisseph `hsys=b'O'`) — deliberately a separate cusp system from the whole-sign houses used elsewhere.
- **multi_match_houses — untested by real data:** `compute_bhava_dig_bala` exposes a `multi_match_houses: list[int]` field surfacing an upstream PyJHora quirk (its h-loop spans 14 offsets over a 12-house cycle, double-visiting 2 houses per rasi-group anchor — last-write-wins in PyJHora's own hash-order-dependent aggregation). Algebraically the two candidate values are always equal for any real longitude (verified this session), so the field is currently harmless — but all 4 reference charts returned `[]` empty, so this has never been observed populated. If a 5th chart ever returns a non-empty `multi_match_houses`, treat it as new territory requiring fresh validation — do not assume it's safe purely on the existing algebraic argument.
- **Resolution:** Real implementation. `compute_bhava_dig_bala` in `bhava_bala.py`; `dig_is_stubbed` now always `False`. `compute_bhava_drishti_bala` / `drishti_is_stubbed` unaffected — remains stubbed.

#### PDF-read tooling gap (Session 42)
- **Issue:** The poppler/`pdftoppm` path referenced under "Windows Paths (hardcoded)" (`C:\Program Files\poppler-26.02.0\Library\bin`) is not currently wired up on PATH in the Claude Code environment, despite being hardcoded there — the Read tool's PDF-render path fails with "pdftoppm is not installed" when pointed at a PDF.
- **Impact this session:** Could not directly OCR/read AstroSage PDF chart reports to extract Bhava Dig Bala reference values from source; required a manual chat-transcription relay (user pasted the values from the PDFs directly) instead of direct Claude Code extraction — see `tests/fixtures/bhava_dig_bala_astrosage.py` docstring for the resulting provenance note.
- **Status:** Flagged for a future fix, not blocking. Revisit when a task next needs direct PDF-sourced fixture extraction (e.g. Bhava Drishti Bala's eventual validation).

### Chunk Metadata Schema (archived)

## Chunk Metadata Schema (locked — do not alter)
```python
{
  "chunk_id": str,       # "{book_name}_p{page_num}_c{index}"
  "text": str,
  "topic": str,
  "language": "eng|hin|mixed",
  "page_ref": int,
  "image_path": "str|null",
  "book_name": str,
  "page_type": "text|diagram|mixed",
  "word_count": int,
  "text_sha256": str,    # SHA-256 hex digest of `text`; embedder-computed, ChromaDB-metadata-only (not chunker-emitted)
}
```
Sub-chunks always have `_c{index}` appended to `chunk_id`.
Schema lock permits additive fields with safe defaults; renames and removals require explicit sign-off. `text_sha256` added per `diagnostics/embedder_hardening_proposal_20260621_100850.md`.

## Sessions 0-18 — completion rollup (no per-session blocks exist)

Promoted out of the Session 32 block at S81, verbatim. This is the ONLY record of
Sessions 0-18 and is ACTIVE EVIDENCE, not dormant history: the Session 2 bullet
(classify_page mixed detection) is F2/F4's provenance and the Session 4 bullet
(translator.py) is F5's. NEVER archive this block.
INCOMPLETE: Sessions 5, 6, 7, 15 and 17 are absent — do not cite as a full record.

- Session 0 (2026-05-25): Repo created, folder structure, `.cursorrules`, `CLAUDE.md` — COMPLETE
- Session 1 (2026-05-25): `pdf_processor.py` complete + validated on BPHS Vol 1 (482 pages, 155 diagram); fixed kundali misclassification via number density + planetary keyword checks; `image_extractor.py` complete; `chunker.py` complete — COMPLETE
- Session 2 (2026-05-26): `embedder.py` written; `classify_page()` extended with mixed detection (5 patterns: number density, planetary keywords, structural grids, illustration markers, diagram override for word_count > 250); `strip_devanagari()` added to `chunker.py`; split_page() added to `pdf_processor.py` with `split_spreads=False` default; all 5 books confirmed as single-page portrait scans — COMPLETE
- Session 3 (2026-05-26): four-agent review system (qa.md added); query_engine.py complete, all QA passed; astrologer.py complete, 13/15 QA passed — 2 failures: response time 6-11s (fix: SSE streaming in FastAPI layer); prompt_builder.py complete 12/12 tests passed; astrologer.py migrated atomically 7/7 regression passed; session_manager.py complete — get_recent_history (sliding 6-turn window), MAX_HISTORY_SAVE=100 trim logic, atomic JSON persist, 24/24 QA passed; astrologer.py session wiring complete — history prepend, introduce suppression, failed-call guard, all crashes fixed — COMPLETE
- Session 4 (2026-05-26): `translator.py` complete — GPT-4o-mini translation for Hindi books; partial book-name matching (case-insensitive contains on HINDI_BOOKS stems); Devanagari fraction guard ≥0.25 (matches chunker.py); idempotency via `original_hindi` field; atomic save + incremental progress every 50 chunks; actual token-based cost tracking; BPHS safety confirmed (0/2169 current chunks triggered); 8/8 QA passed — COMPLETE
- Session 8 (2026-05-28): 6-agent framework established (ui_ux + debate agents), palm nudge redesigned Option C, fixed U-1 U-2 U-3 ISSUE-2 ISSUE-3 ISSUE-6, 3 unit tests passing, data artifacts removed from git — COMPLETE
- Session 9 (2026-05-28): Token optimisation — CLAUDE.md 78→57 lines, removed stack/sessions/token-hygiene sections, fixed cursorrules duplicate agent heading, 6-agent invocation rule locked — COMPLETE
- Session 10 (2026-05-28): context_order routing (context_router.py + prompt_builder.py + astrologer.py + app.py wired end-to-end); left/right dual-palm split — palm_processor.py (validate_palm_image, GPT-4o vision, hard_reject/warn/reject_message), app.py two uploaders with duplicate-hash guard + swap UI, ask()/build_prompts() signature updated to palm_left/palm_right; STRICT RULE added to system prompt; left/right palm synthesis confirmed end-to-end; test_palm_quality.py — 4 integration tests, hallucination regression + quality validation passing; 25 tests total passing — COMPLETE. Known debt carried forward: _PALM_TOPICS keyword audit pending.
- Session 11 (2026-05-29): prompt_builder.py — CQ behaviour block added (missing context → ask one clarifying question); needs_disclaimer() guard added (suppress on CQ responses, <80 words + ends with ?); cross-verification block added (mandatory kundali × palm synthesis when both present); query_engine.py — multi_source_search() added (2 chunks × 5 books, dedup by chunk_id, score-sorted, per-book try/except); astrologer.py — multi_source param wired to ask(); test_palm_quality.py — test_no_context_no_hallucination updated with CQ guard; SYSTEM_PROMPT ~580-600 words; 40/40 tests passing — COMPLETE. Known debt: _PALM_TOPICS keyword audit still pending.
- Session 12 (2026-05-29): multi_source_search() validated — root cause was 2 book_name mismatches (Cheiro, Phaladeepika) + 9 books missing from hardcoded list; fixed to 14-book flat list using exact ChromaDB strings; 7,281 chunks now reachable; palm-only query (broken fate line) improved from top score 0.39 irrelevant Vedic → 0.63 Cheiro on-topic; 14/14 books returning results, 0 silent misses; context_classifier.py (new) — LLM Phase 1 gate before RAG/GPT, intent/gate separation (GPT classifies topic only, Python applies has_palm/has_pdf gating), principle-based system prompt (no keyword lists), fail-open; context_router.py stripped to context_order only (nudge/needs_pdf/needs_palm removed); astrologer.py — Phase 1 gate wired, gated key added to all return paths; app.py — pending_question state, gated warning display, "✋ Generate My Reading" button, old nudge block removed; test_nudge_endtoend.py replaced (5 classify_context integration tests); 4/4 integration tests pass, 40/40 suite passing — COMPLETE. Known debt: Hasta p71 OCR noise (data layer, low priority).
- Session 13 (2026-05-30): Lal Kitab (Jyotish_Lal Kitab_B.M. Gosvami) validated — 769 chunks embedded, ranks 1&2 on remedy queries at 0.66+; LAL KITAB-1941 re-purged + progress file deleted (root cause: progress file survived Session 12 purge); progress file orphan audit clean; query_engine.py updated (LAL KITAB-1941 → new book string, 14 books clean); KeyError gated fixed — variable name collision in app.py (result reused for parse_astrosage_pdf + ask() output, renamed to _pdf_parse_result); 40/40 passing. Architecture redesign approved for Session 14: ContextBundle dataclass, single GPT-4o-mini classifier replacing context_classifier.py + context_router.py, intent-driven retrieval profiles, tiered gating (required/enriching), spouse PDF + hand detail inputs. Known debt: left/right palm misclassification (Priority 3), _PALM_TOPICS keyword audit.
- Session 14 (2026-05-30): COMPLETE — ContextBundle dataclass; single GPT-4o-mini classifier replacing context_classifier.py + context_router.py; describe_hand_detail_image() added; matches_slot palm misclassification detection; spouse_pdf + hand_detail + individual palm slots in prompt_builder.py; PALM_TOPICS removed; MULTI-PART QUESTIONS rule added as named block in SYSTEM_PROMPT; LLM query rewriter replacing REWRITE_MAP; app.py spouse PDF + hand detail uploaders, nudge display, confidence score UI removed; dead code purged (context_router.py, config.py REWRITE_MAP); 37/37 passing. No debt carried forward.
- Session 16 (2026-06-14): COMPLETE — palm geometry fields (quality/issues/palm_facing/finger_direction) consolidated into validate_palm_image()'s single GPT-4o call as geometry_tips (briefly a 2nd call via detect_palm_geometry across Tasks 1-2, merged into the existing call in Task 4); hand/matches_slot fields removed entirely (unreliable, see CLAUDE.md Locked Decisions); app.py hand-confirm/swap UI rebuilt around geometry_tips — thumbnail preview + geometry_tips captions + Yes/No (swap) self-confirmation (Task 5); swap regenerates both palm descriptions via describe_palm_image() with corrected hand framing, falling back to the swapped (pre-regen) string with a warning on RuntimeError (Task 6); chat UI fixes — st.write_stream → st.markdown for correct markdown rendering of answers (Task A), and the question bubble now renders before the spinner/ask() call instead of after, eliminating the disappear/reappear flash (Task B; known minor UX item: gated questions now flash a bubble before the warning but don't persist to history — gating logic unchanged); removed stale Session 15-16 hand-laterality diagnostics (tests/manual/slot_bias_check.py, real_photo_check.py, letter_ground_truth_check.py — referenced removed hand/matches_slot fields); 35/35 non-integration passing, 5 integration tests deselected. No debt carried forward.
- Session 18 (2026-06-15/16): COMPLETE — calculate_mudda_dasha() implemented: starting-lord formula (natal_1st_mahadasha_lord_index + age) % 9 validated 36/36 lords, 36/36 bhavs across all 4 reference charts. Two alternative hypotheses (Varsha-Lagna nakshatra, Varsha-Moon nakshatra) tested and ruled out (0/4 each) before the correct formula was found — David was the hardest case, breaking the naive rashi-lord theory that worked 3/4. Residual ±1-day cumulative-rounding deltas (9/36, all delta_bhav=0) documented as irreducible cross-ephemeris noise, same class as the ±37-day Vimshottari drift note — not a defect, not tuned against. resolve_house_counting_lagna() added: shared helper, prefers AstroSage's parsed Varshaphal Lagna when present and year-matched to target_year, else falls back to computed Lagna + boundary_sensitive flag; year-mismatch guard explicitly tested (rejects stale-year AstroSage data). extract_varshaphal_lagna_year() added to astrosage_parser.py, fail-soft. calculate_muntha() retrofitted onto the same helper: added resolved_bhav/bhav_source/bhav_boundary_sensitive (additive only, legacy bhav_primary/bhav_alternate/ambiguous untouched), 4/4 match vs AstroSage. Note: Surbhi's case (no AstroSage data, boundary-sensitive=True) had bhav_primary == resolved_bhav by coincidence of her specific degree — boundary-sensitive cases without AstroSage data remain flagged, not resolved. pytest: 41/41 passing (37 at Session 17 close, +4 this session: lord-sequence, bhav, year-mismatch guard, Muntha new+legacy fields).

## Archive pointer — READ THIS BEFORE CONCLUDING A RECORD IS MISSING

Sessions 19-66 live in `SESSION_LOG_ARCHIVE_S19-S66.md`, split at S81.
Sessions 67-104 live in `SESSION_LOG_ARCHIVE_S67-S104.md`, split at S105 (S121).
Sessions 105-145 live in `SESSION_LOG_ARCHIVE_S105-S145.md`, split at S146 (S151).
This live file holds: the Session 45 compression block, the locked Chunk
Metadata Schema and the Sessions 0-18 rollup (all below, NEVER archived),
then S105 onward.
Any `SESSION_LOG.md S<n>` citation with n<67 means the S19-S66 archive;
67 <= n <= 104 means the S67-S104 archive.
Note: the archive IS sequential (S19-S66, S32 restored to position at S81), but 34
of 80 sessions have no ``## `` header of their own — grep by content, not by header. Git holds every pre-split byte: \git show <hash>:SESSION_LOG.md\.
Boundary rule: never split above a session still cited by CLAUDE.md.

## S146 — Stub cleanup + Points 1/2/3A (built-but-blind calcs wired, divisional charts D2–D60, panchanga-muhurta) + layman summary + ceiling re-derive + timing-ranking/payload diagnostic probe (2026-10-03)

DESIGN-CHAT session (Cowork). Executed directly against the working tree via the device bridge (no git commit — RATIFIED pending, commit at session end). Pure-logic work validated in-sandbox; anything touching swisseph / calculate_chart / the LLM / Streamlit is Sulabh's machine. Last green suite reported by Sulabh during the points work: **3960 passed, 3 skipped**. The S146 probe added below is diagnostics-only (no new tests) and awaits Sulabh's next `pytest` + live Streamlit run.

STANDING RULE established this session (applies to ALL future Claude Code prompts): **no Claude Code prompt may depend on the OpenAI LLM without Sulabh's explicit consent.** Every CC prompt states `LLM: none` on its own line, or flags the live-LLM dependency and waits for approval. (pytest does NOT call OpenAI — the interpreter LLM is stubbed in tests; confirmed.)

### PART 0 — STUB CLEANUP (the docstring-only decoys)
14 docstring-only stub files removed so a future session cannot mistake them for pending work. The deletion was initially BLOCKED on `dashas/vimshottari.py` (a live importer, `scripts/spike_option2_timing.py`, still referenced it); resolved, then deleted. Removed: `vargas/divisional.py` (OLD stub), `vargas/vimshopaka.py`, `dashas/vimshottari.py`, `dashas/ashtottari.py`, `dashas/chara.py`, `dashas/mudda.py`, `annual/muntha.py`, `annual/sahams.py`, `annual/varshaphal.py`, `strength/shadbala.py`, `yogas/catalog/dhana_yogas.py`, `yogas/catalog/raja_yogas.py`, `yogas/catalog/special.py`, `yogas/catalog/neecha_bhanga.py`. **KEPT on purpose:** `core/chart_d1.py` (self-documenting guard rail) and `yogas/catalog/pancha_mahapurusha.py` (real, populated). The "whatever is left from these we will build" plan then drove Points 1–2 below (the deleted `strength/shadbala.py` and `vargas/divisional.py` stubs were replaced by the REAL `strength/shadbala_totals.py` wiring and a NEW `vargas/divisional.py` engine).

### PART 1 — WIRE THE BUILT-BUT-BLIND CALCS INTO THE PATH-B FACT BLOCK
Shadbala, Ashtakavarga and Jaimini were computed by existing calc modules but never reached the live interpreter (Path B = `agent/astro/pipeline.answer_question`). Wired each as a fail-soft composer following the compose→render→gate pattern:
- NEW `agent/astro/shadbala_facts.py` — `compute_shadbala_totals(chart)` → per-planet {rupa, ratio, rank, meets_minimum}; `meets_minimum = ratio>=1.0` (the only sourced cut); fail-soft `{}`.
- NEW `agent/astro/ashtakavarga_facts.py` — `compute_bav`/`compute_sav`; SAV sign→house (whole-sign 1:1); `average_per_house=28.08`.
- NEW `agent/astro/jaimini_facts.py` — `compute_chara_karakas` (8-karaka incl. Rahu: AK,AmK,BK,MK,PiK,PK,GK,DK) + `compute_arudha_pada` (AL/UL); per-part fail-soft (Arudha co-lord cascade can raise → karakas still survive).
- `pipeline.py` render blocks (with role glosses) inserted before the DASHA/TIMING section; `capability_gate.py` FACT_BLOCK_PROVIDES gained keys `shadbala`, `ashtakavarga`, `jaimini` (growth contract, pinned by `test_capability_gate.py`); `interpreter.py` EXPERT_SYSTEM recognized-facts list extended; `frontend/app.py` + `scripts/expert_pilot.py` compose the facts before `answer_question`. These are `unfittable` concepts (numeric/different-frame) → no S137 predicate, no Requirement, by design.
- Tests: `tests/astro/test_{shadbala,ashtakavarga,jaimini}_facts.py`.

### PART 2 — DIVISIONAL (VARGA) CHARTS D2–D60
- NEW `agent/calculations/vargas/divisional.py` — generic engine. `VARGA_RULES` for D2 (Hora), D3, D4, D7, D10, D12, D16, D20, D24, D27, D30 (Trimsamsa special), D40, D45, D60; `varga_sign_index(longitude, varga)` pure; `compute_varga(jd_ut, asc_lon_sidereal, varga)→VargaChart`. swisseph used ONLY for longitudes. D9 stays in `navamsa.py` (oracle-clean, untouched).
- NEW `agent/astro/divisional_facts.py` — surfaces D10(career), D7(children), D2(wealth), D30(health), D12(parents), D3(siblings), D24(education); reads `chart["meta"]["jd_ut"]`/`["asc_lon_sidereal"]`; per-varga fail-soft. `pipeline` render (one line per varga) + `capability_gate` key `divisional` + interpreter recognition.
- VALIDATION (AstroSage Shodashvarga table p39 as oracle, no swisseph needed): 555/558 across 4 charts. D27 regression fixed (start-sign map → fire=Aries/earth=Cancer/air=Libra/water=Capricorn → 10/10). D7 "divergence" (Sulabh Saturn Aquarius vs AstroSage Capricorn) resolved by Sulabh's JHora D-7 = Aquarius → AstroSage reclassified as the outlier; the rule was NOT tuned.
- Tests: `tests/calculations/vargas/test_divisional.py` (4-chart oracle; Layer A pure + Layer B live), `tests/astro/test_divisional_facts.py`.

### PART 3A — MUHURTA (PANCHANGA-LIMB SUITABILITY)
- NEW `agent/calculations/transits/panchanga_muhurta.py` — `score_panchanga_muhurta(jd_ut)` + classification: `INAUSPICIOUS_YOGAS` (9), Rikta tithis + Amavasya = avoid, Vishti karana = avoid, Sakuni/Chatushpada/Naga = caution. STANDALONE — does NOT touch `muhurta_scorer`.
- Test: `tests/calculations/transits/test_panchanga_muhurta.py`.
- NOTE: this is the panchanga-limb Tier A only. Making muhurta USABLE live (a deterministic "Muhurta Finder" panel, option A, 30-day default, reusing the Path-A scan + composing these limbs at the scan layer, no `muhurta_scorer` change, LLM:none) is DEFERRED to a fresh session — see CARRY-FORWARD.

### PART 4 — LAYMAN SUMMARY
`interpreter.py` EXPERT_SYSTEM now ends every answer with an **"In simple terms:"** section — 2–4 sentences, practical bottom line in everyday English, NO astrology terms (no planet/sign/house/lord/yoga/dasha/varga/karaka/Sanskrit, no jargon-dressed dates). A non-astrologer must understand the whole answer from that section alone.

### PART 5 — CONTEXT-CEILING RE-DERIVE (in-code tagged S147 by Sulabh)
`GPT5_SAFE_APPROX` recalibrated **200_000 → 150_000**. Cause: at 200k, ~340k-real payloads (200k×1.70) routed to gpt-5, whose REAL input cap is **272,000** → live 400 "Input tokens exceed 272000 (resulted in 274282)". New derivation `(272000 − overhead)/1.70 ≈ 150k` routes those to gpt-5.6-luna instead. Sulabh applied the fix before I finished deriving it; it matched. Other live constants unchanged and CONFIRMED this session: `REAL_INPUT_CAP=950_000`, `HARD_CONTEXT_CEILING=500_000` (approx; absolute refuse bound), `INTERPRETER_CONTEXT_WINDOW=1_050_000`, `APPROX_TO_REAL_RATIO=1.70`, `DEFAULT_TOKEN_BUDGET=60_000`, `INTERPRETER_TPM_LIMIT=30_000`.

### PART 6 — DIAGNOSTIC PROBE (timing-ranking + payload tagging) — LLM: none
Motivated by two Sulabh doubts on the live run (`diagnostics/qa_capture/20261003T175900Z.md`): (a) marriage answer led to 2045+ with an apparent empty 2026–2045 window; (b) whether the 244k–564k payload is legitimate/reducible. Root cause of why neither could be answered from the capture: the ranker's FULL scored list was discarded (only `render_ranking(limit=6)` text reached the interpreter; `build_timing_ranking`'s full `windows` was thrown away), and the per-segment domain-filter keep/drop breakdown lived in the payload but was never surfaced in the capture. Fix (surgical, diagnostics-only, answer UNCHANGED):
- `pipeline.py` — retain the full `build_timing_ranking(...)` result in `_timing_ranking`; add it to BOTH trace dicts (the expert-mode return AND the normal return — the live path IS expert mode, so omitting the expert branch would blind the probe exactly where it is needed). Interpreter still receives only the rendered top-6 text.
- `qa_capture.py` — NEW `### computed timing ranking` section (full scored list, per-signal breakdown); `domain_filter` added to the `### selection + payload` block (kept_domain_match vs kept_failsafe_untagged/unknown_id vs dropped_domain_miss + segment_cut_pct = the tagging-coverage signal).
- Tests checked, not run here: all `test_qa_capture.py` capture_turn assertions are positive-presence (additive sections, `.get()`-guarded → render `null` harmlessly if absent); no new imports (imports-nothing guard intact); `test_replay_capture.py` replays a frozen fixture so it never sees the new keys. Sulabh to confirm via `pytest`.

### KEY DIAGNOSES (design findings — see CARRY-FORWARD for the open decisions)
- **Marriage 2026–2045 "gap" = a ranker-DESIGN artifact, not a calc bug** [Certain on mechanism, from reading `timing_ranker.py`]. The ranker scores purely on KP significators + Saturn/Jupiter transits + Saturn return: `score = W_SIG×(AD-lord sig of target houses) + 0.5·(MD-lord signifies) + W_ACT + W_RET + W_JUP`. There is **no karaka logic** — Venus being the kalatra karaka contributes nothing unless Venus is a KP significator of {2,7,11}; `W_MD=0.5` is flat across the whole MD and by design "cannot distort intra-MD order". So within Venus MD (2032–2052, itself the marriage dasha) the winner is whichever SUB-lord best signifies 2/7/11 + catches transits → Venus-Saturn 2045, Venus-Mercury 2048; early Venus sub-periods (2032–2045) score lower. `render_ranking(limit=6)` then truncates to the significator cluster → the apparent empty 19 years. Defensible ranking by its own rules, but the rules under-weight karaka-driven dashas (marriage=Venus, children=Jupiter) — the exact signal a classical reading leans on. The S146 probe will print the actual 2032–2045 scores.
- **Children NUMBER and SEX = NOT a missing input; DROPPED as a feature** [Certain]. The birth chart already contains everything the classical progeny methods use. The agent is silent because (1) no calc computes count or sex, and (2) both are classically low-reliability — count was era-calibrated and counted conceptions/pregnancies not surviving births; sex has no validated method. Sulabh's decision: if the astrologers themselves can't do it reliably, building it only manufactures false precision — **do not build.** (Birth-time-to-the-minute does gate D7-lagna quality (~1 saptamsa / ~17 min); Sulabh runs "Exact", so the input side is covered regardless.)
- **Payload over-inclusion = the LOCKED S124 design, not a tagging slip** [Certain]. Two-stage selection: `select_units` pulls WHOLE chapters if ANY planned-domain segment is present; `filter_segments_by_domain` drops a segment ONLY if it is positively tagged for other domains — untagged / unknown-id / `unfittable` segments are KEPT by fail-safe. So everything not provably off-domain ships, by design. Whether that is a tagging MISS vs legitimate breadth is exactly what the newly-surfaced `domain_filter` counts measure: fail-safe ≫ domain_match ⇒ under-tagging (tag those segments, shrink payload with zero quality loss); domain_match dominates ⇒ payload legitimately that size and luna is the right route. Could NOT be answered from existing captures (counts never recorded) — hence the probe, not a code read alone.

### FILES TOUCHED THIS SESSION (device, no git commit — RATIFIED pending)
NEW: `agent/astro/shadbala_facts.py`, `agent/astro/ashtakavarga_facts.py`, `agent/astro/jaimini_facts.py`, `agent/astro/divisional_facts.py`, `agent/calculations/vargas/divisional.py`, `agent/calculations/transits/panchanga_muhurta.py`, and their tests. EDITED: `agent/astro/pipeline.py`, `agent/astro/capability_gate.py`, `agent/astro/interpreter.py`, `agent/astro/qa_capture.py`, `agent/astro/planner.py` (GPT5_SAFE_APPROX), `frontend/app.py`, `scripts/expert_pilot.py`, `tests/astro/test_capability_gate.py`. DELETED: the 14 stubs in PART 0. (`diagnostics/qa_capture/*` is gitignored — local only.)

### CARRY-FORWARD / NEXT (fresh session)
1. **Validate the S146 probe** — run `pytest`, then one marriage + one career question in Streamlit expert mode (`$env:ASTRO_EXPERT_MODE=1`); read the new `### computed timing ranking` (actual 2032–2045 scores) and the `domain_filter` block (tagging ratio). Decide (a) whether a `W_KARAKA` weight is warranted — an N>1 design decision, NEVER tuned on Sulabh's one chart; and (b) whether under-tagging is shrinking-worthy.
2. **Muhurta-live "Muhurta Finder" panel** — deterministic, option A, 30-day default, reusing the Path-A scan + composing `panchanga_muhurta` limbs at the scan layer; no `muhurta_scorer` change; LLM:none.
3. **Interpreter prompt (small, optional):** always surface the single top-ranked timing window even if past, before leading with upcoming — the system cannot know an event already occurred (Sulabh's marriage 11 Dec 2019 IS in the fact block via Mercury-Rahu, but S145 framing led future-only).


## S150 (2026-10-11) -- RUNTIME-DISPATCHER FOUNDATION: capability registry + computed-only answer route (lucky-days pilot)

OUTCOME: the architecture that lets a question be answered from a COMPUTED fact class with no corpus domain is built, tested, and live-validated. Branch `wip/interpretive-pilot`. COMMITTED as `beaf0b1` on top of S149 `19c8c59`. Full suite 5062 passed / 7 skipped / 2 xfailed / 0 failed (28 new across 4 test files). Design-chat session (Cowork) executed against the working tree via the device bridge; every step was sandbox- or pytest-validated and one live Streamlit run gated the pilot.

### THE PROBLEM THIS SOLVES
"Which is my luckiest day" was UNANSWERABLE. Not a missing fact -- `lucky_unlucky` is computed (S147) -- but a ROUTING gap: `planner.DOMAINS` is a closed corpus-domain vocabulary with no lucky entry, and `build_from_plan` (planner.py:911) refuses any domain-less question. lucky_unlucky (like muhurta) has NO BPHS chapters, so it had no route. Sulabh's ruling: do NOT build a per-feature route (lucky colour, do's/don'ts, remedies would each need one) -- build ONE uber-level mechanism. This is the runtime dispatcher the S147/S149 carry-forwards named.

### THE ARCHITECTURE (ratified via the full roster; 3 conflicts resolved by Sulabh)
A self-describing CAPABILITY REGISTRY is the single source for computed, non-corpus answer routes, rendered into BOTH the planner and interpreter prompts so each LLM has full capability awareness (incl. follow-ups) -- the P-030 drift guard: one list, two renders.
- NEW `agent/astro/capability_registry.py` (LEAF, stdlib only). `Capability` dataclass {id, intent_gloss, fact_key, label, dated, needs_chart, requires_input, interpreter_directive}. `REGISTRY` seeded with the pilot row `lucky_days` -> fact_key `lucky_unlucky`. `planner_manifest()` (id->gloss, closed vocab for the planner), `interpreter_manifest(available_fact_keys, inputs_present)` (what is available for THIS chart + input state), `directives_for(ids)`, `fact_keys()`. SOURCED BY CONSTRUCTION: a row points at a fact class already computed from a cited rule, so there is no unsourced capability to advertise (Sulabh dissolved the "sourcing gate" as structural, not an enforced check).
- STEP 1 (also landed the S147 wiring that NEVER reached app.py -- a doc drift corrected here): `frontend/app.py` now composes the static block via `fact_store.load_or_build(_fact_key, lambda: build_static_facts(_chart), identity=...)`, replacing ~115 lines of inline composition. This ACTIVATES `lucky_unlucky` (the inline block silently omitted it) + per-chart caching + one source of truth. Verified against the inline block: identical composer order, + lucky.
- STEP 2 (`planner.py`, emit-only/behaviour-neutral): `Plan` gains `capabilities: list[str]`; SYSTEM_PROMPT carries a `capabilities` schema field + the registry manifest appended; `validate_plan_object` validates capabilities against the registry and a computed-only plan (domains [], capabilities set, in_scope true) is now legal. `:911` refusal NOT touched in this step.
- STEP 3 (`pipeline.py`, the dispatcher -- behaviour change): a computed-only plan (capabilities and NO domain) skips `build_from_plan` entirely (no retrieval, no no-domains refusal), stands in an empty payload, and is forced into EXPERT mode (no verses to cite). Corpus and mixed plans unchanged; a plan with neither domains nor capabilities still hits the honest refusal.
- STEP 4 (`pipeline.py`+`interpreter.py`, capability awareness): the interpreter is handed the interpreter_manifest + the fired capabilities' directives; EXPERT_SYSTEM gains the standing rules -- answer on-map only, decline off-map ("I don't compute that yet", never improvise), NO upsell, at most ONE grounded clarification. The planner already refuses off-manifest as out-of-scope, so this is awareness/defence-in-depth, not the sole guard.

### ROSTER RULINGS (Sulabh)
- CONFLICT 1 (no upsell): the answering LLM must NOT offer unrequested capabilities ("would you like your lucky colour?"). Answer the question asked and stop. A clarifying question is allowed ONLY when the answer is impossible without a missing detail.
- CONFLICT 2 (dissolved): registration is self-sourcing -- a capability exists only if it has a backing computed/cited fact class, so there is nothing unsourced to advertise. The only live rule is on the ANSWER side: answer strictly on-map; "I don't compute that yet" for anything off it. do's/don'ts + remedies appear automatically once Lal Kitab is ingested + tagged -- one registry row each, no new routing.

### PILOT VALIDATED LIVE (Streamlit, expert mode, Sulabh's chart)
- "which is my luckiest day of the week?" -> ANSWERS ("Thursday is your luckiest day"), in_scope true. (Was refused before this session.)
- "what does my chart say about marriage" -> unchanged full corpus answer.
- "what's my lucky colour" -> cleanly REFUSED as out of scope (in_scope false), NOT freelanced -- the honesty boundary holds at the planner.

### KNOWN BUG, FOUND IN THE LIVE RUN, DEFERRED BY SULABH (tracked)
`fact_store` caches via `json.dump`, which serialises INTEGER dict keys to STRINGS. `ashtakavarga_facts.sav_by_house` is int-keyed and `strongest_house` is an int, so on a cache HIT `_fact_block` (pipeline.py:302) does an unguarded `sav_h[_sh]` -> KeyError. The live run crashed on the first (cache-hit) turns and "worked" later only because a fresh (int-keyed) build is a cache MISS. The guarded loop above (297-299, `if _h in sav_h`) would also silently render ZERO SAV lines on a cached read. PROVEN from the cache file (`data/fact_cache/fecfe1a48656e908.json`: keys '5','6','7'...; strongest_house 2 int; sav[2] -> KeyError). SCOPE: every int-keyed dict in the fact block; `timeline_store` shares the same JSON atomic-write pattern, so the dated-engine arc inherits the same landmine. FIX (next session, before the dated engines): switch `fact_store`+`timeline_store` serialisation to key-type-preserving (pickle recommended -- cached read == fresh build byte-for-byte, zero reader changes) OR JSON-normalise digit keys on load; plus a defensive guard at `_fact_block:302`.

### DOC DRIFTS CORRECTED THIS SESSION
(1) S147 log/lock claimed `app.py` used `fact_store`/`build_static_facts`; on disk it did not until STEP 1 this session (it still composed inline and omitted lucky_unlucky). (2) S148 (`70b2a55`) and S149 (`19c8c59`) were both already COMMITTED despite focus text saying "git commit PENDING" -- superseded.

### FILES (committed in beaf0b1)
NEW: `agent/astro/capability_registry.py`, `tests/astro/{test_capability_registry,test_planner_capabilities,test_pipeline_dispatch,test_interpreter_capability_awareness}.py`. EDITED: `frontend/app.py`, `agent/astro/{planner,pipeline,interpreter}.py`.

### CARRY-FORWARD / NEXT (the dated-engine arc)
1. **Caching int-key fix** (above) -- quick, surgical, and load-bearing for everything below; do it FIRST because `timeline_store` shares the pattern.
2. **Migrate muhurta onto the registry** as the first `dated` capability -- retire its bespoke S147 planner flag; needs the dated-compose mechanism (compose at answer time with the planner horizon). 4-file refactor; not a quick win.
3. **Plug in the dark dated engines as capabilities**: combustion (S147), ingress / "when does Saturn enter my 7th" (S148), masa (S148), the two-tier timeline (S149). Each = one registry row + the dated-compose hook + a fact composer + a `_fact_block` render. This is the runtime-dispatcher dated path (date inside window -> stored intervals via `timeline_store`; beyond -> live compute).
4. **Masa naming** still OPEN (no corpus source; AstroSage carries no panchanga section to grade it).
5. Deferred from S146 (still open): timing-ranking W_KARAKA probe (N>1, never tuned on one chart); interpreter "surface the top-ranked window even if past".

## S149 (2026-10-07) -- THE PRECOMPUTED DATED FILE: TWO-TIER TIMELINE (shared sky + per-chart projection)

OUTCOME: the "one file with everything pre-calculated, time-based, for the next year" is built, measured and tested. Branch `wip/interpretive-pilot`, on top of `70b2a55` (S148). Nothing committed. 32 new tests; 91 green in the S149 sandbox tree, full suite expected 5034.

### PART 0 -- A COURSE CORRECTION, RECORDED
Sulabh corrected the S146 marriage-gap re-read: the 2026-2045 range came from the QUESTION ("when WILL I get married" -- future-facing), not from a ranker defect. The ranker is built, tested and SETTLED; do not reopen it. The S148-close proposal to refactor `transit_facts._snapshot` is WITHDRAWN -- it was scope drift away from the agreed path (engines -> precomputed timeline -> dispatcher).
What survives is a NOTE, not a work item: `transit_facts._snapshot` takes `mid_jd = (start_jd + end_jd)/2` and reads one `compute_gochara` snapshot, so the transit term's hit rate is flat at 1/12 regardless of antardasha length (measured over 2026-2053: Jupiter 8.3% midpoint vs 39.9% true overlap on a 3.33-year window). Logged for whenever transit depth is revisited on its own merits. NOT a diagnosis of anything shipped.

### PART 1 -- THE STORAGE SPLIT, RESOLVED (S147 carry-forward 3)
S147 deferred "shared chart-independent ephemeris cache vs per-chart copy" to timeline-assembly time. Assembly is now, and the engines answered it: combustion is a Sun-planet separation, an ingress is a graha crossing a cusp, a lunar month is a new moon. NONE reads a natal chart, so all three are byte-identical for every chart ever built.
- TIER A, NEW `agent/astro/ephemeris_cache.py` -- `shared_window_key(as_of, horizon_days, ayanamsa)` (human-readable `2026-10-07_365_LAHIRI`; nothing to obscure because nothing personal is in it), `build_shared_ephemeris`, `load_or_build_shared`. Per-ENGINE try/except so one failing scan costs its own fact class, surfaced in `errors` and never silent. `SHARED_SCHEMA_VERSION` independent of the other two stores. Atomic tmp+os.replace; a corrupt or unwritable cache falls back to building in memory and NEVER blocks an answer.
- TIER B, NEW `agent/astro/build_timeline.py` -- `project_events` joins the blob onto one chart: every graha event gains `from/to_house_from_lagna` and `from/to_house_from_moon` (whole-sign, exactly `gochara.compute_gochara`'s S20-locked dual-reference rule). NO ephemeris call. `timeline_builder_for(chart)` returns the `builder(as_of)` callable `timeline_store.load_or_refresh` already expects, so the store stays ignorant of charts and calculators as its leaf docstring requires. `load_timeline_for_chart(key, chart)` is the app seam, keyed by the SAME identity key `fact_store` uses.
- THE LINE: "depends on the sky" (Tier A, shared) vs "depends on your chart" (Tier B, per-chart). Every engine lands cleanly on one side. A test walks EVERY key of the Tier-A blob and fails if a chart field or a house ever leaks in.

### PART 2 -- WHAT build_timeline DELIBERATELY DOES NOT DO
- NO FILTERING. Every event is projected and none is dropped. WHICH event matters for a question is the planner's and the interpreter's business; a relevance rule here would be use-case logic inside the fact layer.
- NO SADE SATI. `transits/sade_sati.py` owns it and is oracle-validated; Saturn's ingress events carry `house_from_moon`, which is the INPUT that module wants. Re-deriving the phase would be a second source of truth.
- NO TITHI. `core/panchanga.py` stays sole source (S148 lock). The lunations here are month boundaries.
- NO NAMING of the intercalary month -- the S148 doctrine stop carries through Tier B unchanged.
- NO "now" VALUE -- intervals and events only, resolved against today at answer time (S147 lock).

### PART 3 -- MEASURED
Window 2026-10-07 .. 2027-10-07, Sagittarius lagna / Cancer Moon:
  TIER A build 0.435 s | cached read 0.0004 s | file 24.9 KB | errors {}
    209 ingress events, 10 combustion intervals, 14 masa months (all complete)
  TIER B projection 0.23 ms
A worked example the old point-sample could not express at all: Jupiter enters the 9th from lagna on 2026-10-31, RETROGRADES BACK into the 8th on 2027-01-24, and re-enters on 2027-06-25. The interval form carries the whole sequence; a midpoint snapshot carries one coin flip.

### PART 4 -- A LIVE PRIVACY GAP, FOUND AND CLOSED
`data/timeline_cache/` was NEVER in `.gitignore`. The S147 session log lists ".gitignore (data/timeline_cache/)" under EDITED and the S147 Locked Decision states "Real birth data is NEVER git-committed (`data/fact_cache/`, `data/timeline_cache/` gitignored)" -- both describe an edit that did not land. Found by grep while adding the S149 entry. The per-chart dated store has shipped since S147 with its birth-derived output committable. Added now, alongside `data/ephemeris_cache/` (ignored as a DERIVED ARTIFACT, explicitly not for privacy -- it holds no birth data, which is what makes it shareable).

### PART 5 -- RULE OF THREE, MET AND NOT ACTED ON
The ~15-line atomic-write / fail-soft-read core is now in THREE stores (`fact_store`, `timeline_store`, `ephemeris_cache`). S147 declined extraction at two, citing the rule of three; three is the same threshold that triggered the `helpers/discrete_scan.py` extraction at S26. NOT extracted here: it would mean editing two committed green modules inside a feature commit, against the surgical-edit rule, and the three differ in invalidation semantics (schema version / forward-reach re-anchor / content-addressed key). RECORDED as its own task in the module docstring and here -- not silently skipped, not bundled.

### VALIDATION / TESTS
- `tests/astro/test_build_timeline.py` (25, PURE -- hand-built Tier-A blob, injected builders, no ephemeris): projection into both frames, retrograde backward house move, nothing filtered, masa unprojected and unnamed, malformed event costs itself, all four unusable-chart shapes keep the sky and flag the failure, shared-loader failure does not raise, builder matches the store contract, store round-trip caches, empty key builds in memory, key is content-addressed, two charts share one file, a different ayanamsa never reuses, stale schema rebuilds, corrupt file and unwritable dir never block an answer.
- `tests/astro/test_build_timeline_ephemeris.py` (7, REAL ephemeris, no skips): every fact class populated, NO birth data in the shared blob (key walk), one scan serves two charts with different houses and writes ONE file, houses in 1-12, retrograde Jupiter shows as a backward house move, horizon reach exact, cached read at least 5x faster than cold.

### FILES (device; git commit PENDING, RATIFIED awaited)
NEW: `agent/astro/{ephemeris_cache,build_timeline}.py`, `tests/astro/{test_build_timeline,test_build_timeline_ephemeris}.py`. EDITED: `.gitignore`, `CLAUDE.md`, `SESSION_LOG.md`. No existing module touched -- `timeline_store.py` is consumed through its published contract, unmodified.

### CARRY-FORWARD / NEXT
1. **RATIFIED git commit** of S149 on top of `70b2a55`.
2. **THE RUNTIME DISPATCHER** -- the last piece of the S147 plan: planner emits parametrised calc-requests; a date inside the window resolves against these stored intervals, a date beyond it computes live. Muhurta is the first registered calc.
3. **WIRE THE TIMELINE INTO `frontend/app.py`** alongside the existing `fact_store.load_or_build` call, and render the dated facts in `pipeline._fact_block`. Needs a live Streamlit run to validate.
4. **Extract the shared store core** (Part 5), as its own task.
5. **The masa naming question stays OPEN** (S148 Part 4): AstroSage carries no panchanga section, so it cannot grade masa.
6. **Deferred from S146** (still open): timing-ranking probe validation; interpreter "surface top-ranked window even if past".

## S148 (2026-10-07) -- UNIVERSAL CROSSING PRIMITIVE; GENERAL INGRESS ENGINE; MASA CALENDAR (placement facts only)

OUTCOME: the two engines the S147 carry-forward asked for are built, tested and ratified against the real ephemeris -- but NOT in the order asked, and the masa engine deliberately stops short of naming the intercalary month. Branch `wip/interpretive-pilot`, on top of `5702d2f`. Nothing committed. Full suite 5002 passed / 7 skipped / 2 xfailed / 0 failed (59 new, suite +4s).

### PART 0 -- STATE VERIFICATION AND A DOC DRIFT
`.git/HEAD` -> `ref: refs/heads/wip/interpretive-pilot`; reflog tail `9a64311` -> `5702d2f` "S147: muhurta on Path B + conversation context + V1.5 fact layer". The S147 stack WAS committed; CLAUDE.md and this log still said "git commit PENDING" in four places, written pre-commit. Corrected in this pass. (No `device_bash` in the S148 session, so cleanliness of the working tree was verified by Sulabh's own `git status`, not asserted here.)

### PART 1 -- THE CARRY-FORWARD PREMISE WAS WRONG (repo-search, anti-phantom)
S147 recorded masa as "smaller lift than transit-ingress because core/panchanga.py already exists". It is not. `core/panchanga.py` exports tithi, vara, nakshatra+pada, yoga, karana, hora, choghadiya, rahu/yamaganda/gulika, abhijit, sunrise/sunset -- and NO masa, NO sankranti, NO amanta/purnimanta, NO adhika/kshaya. Zero hits for `masa|sankranti|adhika|shuddhi|kshaya|amanta|purnimanta|malamasa` across `agent/calculations/**`, `agent/astro/**`, CLAUDE.md and this log (the only matches are the unrelated Kala Bala "Abda/Masa" Virupa note). Panchanga supplies the TITHI half for free; the other half of masa is solar sign ingress -- i.e. the transit-ingress engine queued second. ORDER INVERTED: the general engine was built first, so masa composes over it instead of carrying a private sankranti scan that the ingress engine would then duplicate (the second-source-of-truth seam `combustion_scan.py` avoided by importing `core/combustion`'s orbs).

### PART 2 -- THE OBVIOUS REUSE WAS UNSOUND (full roster, before any code)
The proposed L0 -- `state_fn = floor(angle*n/360)` fed to `find_state_segments` -- was attacked independently by Architect (HIGH-1), Critic (HIGH-1), QA (HIGH-3) and Ephemeris Auditor (MED-3). `find_state_segments` compares CONSECUTIVE COARSE SAMPLES and bisects each bracket ASSUMING ONE transition. Both halves fail for quantised angles: (a) a body crossing a cusp and crossing BACK inside one step leaves both samples in the same band -> ZERO crossings, silently -- precisely the retrograde-station-near-a-cusp case; (b) a 3-state bracket (k, k-1, k) converges on an arbitrary point labelled with the two ENDPOINT states -- a crossing that never happened. `combustion_scan.py` is safe from (a) only because its episodes are days-to-weeks wide, which its own docstring states as a scope guard.
NO FINER STEP FIXES IT -- the dither window shrinks faster than any constant rate, so `samples_per_band` was a guessed number wearing the costume of a calculation. REPLACED BY A PROOF: a crossing at tc in [a,b] requires tc-a >= d(a)/R and b-tc >= d(b)/R, hence b-a >= (d(a)+d(b))/R; contrapositive prunes. Correctness now rests on R (measured), NOT on step size; `initial_step_jd` is a performance knob only.
FALSIFIER (in the test suite): a 0.05-deg parabolic excursion over the 30-deg cusp lasting 0.316 d inside a 3.4 d stride. Adaptive scanner returns both roots at 100 -+ sqrt(0.05/2) exactly; `find_state_segments` returns states [11, 0, 11] and misses them entirely. Both assertions live in the same test so the contrast is the test, not a comment.

### PART 3 -- WHAT SHIPPED
- `helpers/discrete_scan.py` EDITED, APPEND-ONLY -- verified byte-identical through line 175; `find_state_segments` untouched. Adds `Crossing`, `scan_quantised_crossings`, `default_initial_step`, `_division_index` (modulo load-bearing: angle 360.0 would otherwise index n), and `max_evaluations` -- a guard, not a knob, for the degenerate angle-exactly-ON-a-boundary input whose distance to a boundary is zero so the prune can never fire (found by RUNNING the tests: 51s before the guard, 0.11s after; loud RuntimeError now).
- NEW `transits/ingress_scan.py` -- `scan_divisional_ingresses(body, ..., n_divisions=12)` and `scan_ingress_table(...)`. PER-BODY ERROR ISOLATION (one bad body must not discard six good ones; the one place that swallows an EphemerisError, and it records what it swallowed). Records `ayanamsa`/`nirayana` on every result. Unknown body REFUSES rather than defaulting a rate.
- NEW `core/masa.py` (PURE, stdlib only) + `core/_masa_tables.py` (label table, `_panchanga_tables.py` precedent) + `transits/masa_scan.py` (driver: over-scan by one synodic month + 1 day, then trim; `resolve_local_dates`).
- NEW `scripts/measure_ephemeris_rates.py` -- re-derives the correctness constants, exits non-zero if any stored bound is below the measured maximum.
- CUT after roster adjudication: `scan_retrograde_segments` (not a crossing primitive, no caller); `purnimanta` scheme (presentation transform, and shipping both = two contradictory answers to defer a decision); `kshaya` naming (next occurrence ~2124, untestable branch); the claim that the primitive "subsumes" tithi/karana/yoga (`core/panchanga.py` stays the SOLE tithi source -- a second path would disagree at the ~0.09 s tolerance).

### PART 4 -- THE DOCTRINE STOP (Validation Source, upheld)
The adhika/kshaya naming rule is NOT in this project's corpus. Searched: the only BPHS masa material is ch.27's Masa LORD (Ahargana / 30 -- a mean 30-day month, no sankranti, no intercalation; it feeds Kala Bala, not a calendar). The no-sankranti rule is siddhantic doctrine from a text we do not hold. Taking it from PyJHora/DrikPanchang and then grading against DrikPanchang is the S131/S132 failure verbatim.
RULING APPLIED: the engine reports `sankranti_count` and `contained_sankranti_rashis` as PLACEMENT FACTS and sets `masa_index`/`name_sa` to None when the count is not 1. No `adhika` flag, no `kshaya` flag, no `source` string on returned data (P-029). Naming belongs in a doctrine layer above `core/masa.py`.
SULABH RULED "no need to cite; if values match the AstroSage PDF, proceed". RE-VERIFIED THE SOURCE RATHER THAN ARGUING: that gate CANNOT BE RUN. `astrosage_parser._PRIORITY_ORDER` = [Varshaphal, Pratyantar, Muntha, Sade Sati, Favourable Points, Transit Today, Lal Kitab]; `grep -i "masa|month|tithi|paksha|panchang"` over the parser returns NOTHING. The AstroSage natal report carries no panchanga section, so there is no masa value in it to match. Recorded OPEN; naming stays withheld until a source or a different oracle is chosen.

### PART 5 -- MEASURED, THEN FROZEN
max |d(sidereal longitude)/dt| deg/day, 2010-01-01..2040-01-01, sampled 0.25 d (Sun/Moon) / 0.5-1.0 d:
  sun 1.0197  moon 15.3851  mercury 2.2024  venus 1.2588  mars 0.7913  jupiter 0.2420  saturn 0.1305
  elongation(moon-sun) 14.3885  <- the COMPOSED angle masa scans; NOT the Moon's own, which the first draft would have passed.
Stored bounds are these rounded UP. IDENTICAL TO 4 dp on the sandbox Moshier fallback and on Sulabh's real SE1 files, so the frozen test bands are backend-independent -- which is what the containment/band house style was meant to buy.
REGRESSION CHECK: re-running `combustion_scan` in the sandbox reproduced S147's ratified windows exactly (Venus retro 10-19..10-29, Mercury retro 10-30..11-10, Mercury direct 12-06..01-23).

### PART 6 -- RATIFICATION (hardest case first; real ephemeris, no skips)
2026 was chosen as the window because it CONTAINS the hard case, not because it is convenient.
- Sun: exactly 12 sign ingresses; Mesha sankranti 2026-04-14, Makara 2026-01-14 (day-level containment).
- Mercury: 14 crossings including a BACKWARD cusp crossing (2026-07-07, 3->2) and the re-entry (2026-08-05, 2->3) -- the case the whole L0 redesign exists for. Saturn makes NO sign ingress in 2026 (~2.5 yr/sign); its absence is asserted, not ignored.
- NAMING RULE CORRECTED BY MEASUREMENT: the month [2026-03-19 .. 2026-04-17] contains the Mesha ingress and IS Chaitra, so masa index = the contained rashi. The design brief said rashi+1, which would have named every month after its successor. The ephemeris caught it, not a recollection. Pinned.
- THE INTERCALARY MONTH: [2026-05-16 20:01 .. 2026-06-15 02:54 UT] contains ZERO sankrantis. Its status is AYANAMSA-DEPENDENT BY 0.184 DEG: the Mithuna ingress falls 4.48 HOURS after the new moon that opens the next month. Lahiri vs Raman differ ~0.9 deg (~22 h of solar motion), which would move the ingress across the new moon and dissolve the intercalary month. The margin itself is pinned in a test so a frame change fails loudly instead of quietly renaming a month. THIS IS ALSO THE TEMPTATION TO REFUSE: when an oracle disagrees here, the only change that "works" is adjusting the ayanamsa until it agrees -- that is sourcing, and it is forbidden.
- VEDIC DAY BOUNDARY (Ephemeris Auditor HIGH-1, confirmed live): the 2026-10-10 15:50 UT new moon tz-localises to Oct 10 in Dubai but the first sunrise after it is Oct 11. `resolve_local_dates` uses `panchanga.calculate_sunrise` and REQUIRES tz/lat/lon with no defaults. Dubai and Delhi legitimately disagree on some month start dates; the instants do not.
- Cost: full 2026 masa calendar + 7-body ingress table = 0.42 s, 209 events, 0 errors. The Business agent's cost concern is closed empirically.

### DECISIONS / FINDINGS
- Roster conflicts resolved toward LESS, again: four cuts, one primitive, no new astronomy.
- "Hardest case first" paid differently than in S147: there the value was confirming reuse; here it was DISPROVING a reuse that looked obvious and would have failed silently in production.
- Two defects in this session were found by RUNNING, not reasoning: the naming off-by-one (ephemeris) and the boundary-degenerate hang (test suite).
- NOT WIRED TO PATH B, deliberately (Business HIGH: masa changes no answer without a consumer). Wiring touches planner + capability_gate + pipeline + a facts composer -- four files, a separate task, and the masa half depends on the naming question above.

### FILES (device; git commit PENDING, RATIFIED awaited)
NEW: `agent/calculations/core/{masa,_masa_tables}.py`, `agent/calculations/transits/{ingress_scan,masa_scan}.py`, `scripts/measure_ephemeris_rates.py`, `tests/calculations/core/test_masa.py`, `tests/calculations/helpers/test_discrete_scan_crossings.py`, `tests/calculations/transits/{test_ingress_scan_ephemeris,test_masa_scan_ephemeris}.py`. EDITED: `agent/calculations/helpers/discrete_scan.py` (append-only), `CLAUDE.md`, `SESSION_LOG.md`.

### CARRY-FORWARD / NEXT
1. **RATIFIED git commit** of the S148 engine layer (Sulabh's choice: commit engine first, wiring separate).
2. **THE NAMING QUESTION IS OPEN** -- AstroSage cannot grade masa (Part 4). Options: supply a Surya Siddhanta text; pre-register a 1900-2100 zero-sankranti list and grade against TWO independent panchangas; or leave naming withheld and record it alongside the 47 unsourced detector rows.
3. **Wire to Path B** -- ingress first (no doctrine to ratify; unlocks "when does Saturn enter my 7th", which `compute_gochara` cannot answer because it is a snapshot). Masa second, once (2) resolves.
4. **build_timeline + dispatcher** + the shared-vs-per-chart storage split (S147 carry-forward 3) -- all three engines (combustion, ingress, masa) are chart-INDEPENDENT, which argues for one shared ephemeris cache; still not pre-built.
5. **Deferred from S146** (still open): validate the timing-ranking probe (W_KARAKA N>1 decision); interpreter "surface top-ranked window even if past".

## S147 (2026-10-07) -- MUHURTA LIVE ON PATH B; CONVERSATION CONTEXT (standing); V1.5 FACT LAYER (fact_store + timeline_store + combustion engine + calculated lucky/unlucky)

OUTCOME: the dated/interpretive fact layer that Path B was missing is now built, tested, and (combustion) externally ratified. Branch `wip/interpretive-pilot`. COMMITTED as `5702d2f` ("S147: muhurta on Path B + conversation context + V1.5 fact layer (fact_store, timeline_store, combustion)"); verified at S148 open against `.git/HEAD` + reflog. The "commit PENDING" wording below was written pre-commit and is superseded. Full suite at close: 4943 passed, 7 skipped, 2 xfailed, 0 failed.

### PART 1 -- MUHURTA INTEGRATED INTO PATH B (not a separate panel)
S146 carried muhurta forward as an option-A standalone "Muhurta Finder" panel; Sulabh re-scoped it INTO the answer pipeline so one LLM reads intent and the same facts path serves it.
- NEW `agent/astro/muhurta_facts.py` -- `build_muhurta_facts(chart, start_jd, *, horizon_days, want_count, max_days=730, top_n=8)`. Reuses `muhurta_scorer.find_muhurta_windows` UNCHANGED (Chandrabala+Tarabala+Panchaka) and overlays `panchanga_muhurta.score_panchanga_muhurta` (tithi/yoga/karana) at each window midpoint. Pure ranking (`_rank_and_select`, string-tier keyed); returns {searched, windows, best, earliest_good, none_found}. MAX_SCAN_DAYS=730.
- `planner.py`: Plan gains `muhurta: bool` + `muhurta_horizon: Optional[dict]`; SYSTEM_PROMPT section 6 (MUHURTA = electional "when should I DO X", NOT prediction) + section 7 (MUHURTA_HORIZON from the user's own words); validator for both. muhurta is a PLANNER FLAG, never a corpus domain (no BPHS chapters).
- `capability_gate.py`: `muhurta` added to FACT_BLOCK_PROVIDES; the earlier "ask for horizon" clause + MUHURTA_CLARIFICATION REMOVED (default-not-ask).
- `pipeline.answer_question(..., chart, history)`: composes muhurta when `plan.muhurta` and chart present; default horizon `{"mode":"days","value":730}` (2 years from now); `_fact_block` renders the windows (TIER_1/TIER_2, best + earliest_good, panchanga limbs, cautions); "none found in 2 years" rendered honestly.
- `interpreter.py`: EXPERT_SYSTEM muhurta block (explain the computed windows, do NOT re-rank or invent dates; electional uses muhurta NOT dasha).
DEFAULT HORIZON DECISION (Sulabh): 2 years from current date, real-time calculation beyond; people asking "over 2 years" never mean every muhurta -- rank and give the best + earliest, don't enumerate.

### PART 2 -- CONVERSATION CONTEXT "B" (standing requirement)
Follow-ups like "okay any auspicious date after 24th October" were refused because the planner saw a single-shot question with no thread. Sulabh: "conversation context is a must throughout our project ... which can provide personalized answers."
- NEW `agent/astro/conversation.py` -- `render_history(messages, *, max_messages=6, max_chars=600)`, leaf, stdlib only.
- Fed to BOTH `planner.plan_question(..., history)` (follow-up resolution: pronouns, omitted subject, carry the life area/person/constraints; never carry a domain/house/muhurta flag unless the current question continues it) AND `interpreter.interpret_expert(..., history)`.

### PART 3 -- V1.5 FACT ARCHITECTURE (no-storage lock reversed)
Sulabh reversed the S65 no-storage lock for multi-user rollout: "store it per file for each name, place and date-time of birth combination." Compute-once-per-chart, read thereafter.
- NEW `agent/astro/fact_store.py` -- SCHEMA_VERSION (now 2), `chart_identity_key(jd_ut, asc_lon_sidereal, *, exact)` (16-hex, "" if unavailable), `load_or_build(key, builder, *, cache_dir, identity)`; atomic tmp+os.replace, schema-version invalidation, fail-soft (a bad cache never blocks an answer), empty-key -> build-in-memory. `DEFAULT_CACHE_DIR=data/fact_cache` (gitignored).
- NEW `agent/astro/static_facts.py` -- `build_static_facts(chart)` centralises the composition app.py ran inline (navamsa -> build_chart_facts -> yogas/transits/kp/kp_significators/shadbala/ashtakavarga/jaimini/divisional + now lucky_unlucky), fail-soft per composer.
- `frontend/app.py`: computes `_fact_key` from chart meta, `chart_facts = fact_store.load_or_build(_fact_key, lambda: build_static_facts(_chart), identity=...)`; passes `chart=_chart, history=st.session_state.messages` to answer_question.
- NEW `agent/astro/timeline_store.py` -- the SECOND store, for DATED facts. `TIMELINE_SCHEMA_VERSION`, `WINDOW_DAYS=365`, `REANCHOR_TAIL_DAYS=90`, `needs_reanchor(blob, today)`, `load_or_refresh(key, builder, today, *, cache_dir, identity)`. Key insight: dated facts are stored as INTERVALS (ingresses/combust spans/masa calendar), not point "now"-values, and resolved against the current date at answer time -- so a stored 1-yr window survives the day turning over. SINGLE re-anchor threshold (9-agent decision): rebuild when `horizon_end - today < 90d` (intervals are exact, so an aging as_of costs no accuracy; only the forward reach can go stale). `data/timeline_cache/` gitignored. fact_store I/O NOT shared (9-agent: rule-of-three; the two stores have different semantics).

### PART 4 -- LUCKY / UNLUCKY (calculated, not parsed)
Sulabh: "lucky days etc. we should calculate not pull from Astrosage pdf."
- NEW `agent/astro/lucky_facts.py` -- `build_lucky_facts(chart_facts)` pure over `chart_facts["house_lords"]`. Classical functional-nature rule (BPHS): weekday ruled by a TRIKONA lord (1/5/9) = favourable; by a DUSTHANA-only lord (6/8/12) = avoid; TRIKONA DOMINATES a shared dusthana. Reproduces Sulabh's Sagittarius-lagna oracle (Thu/Tue/Sun favourable, Mon/Fri avoid). Wired: static_facts composes `lucky_unlucky`; FACT_BLOCK_PROVIDES += `lucky_unlucky`; `pipeline._fact_block` renders favourable/avoid with ruling planet + houses (grounded, not asserted); fact_store SCHEMA_VERSION 1->2 (every cached chart rebuilds). v1 first-order rule; maraka 2/7 + kendradhipati-dosha refinements recorded as deferred.

### PART 5 -- COMBUSTION WINDOW ENGINE (hardest case first; ~80% reuse)
Anti-phantom repo search found `core/combustion.py` (natal, point-wise), `helpers/ephemeris.py` (`sidereal_position` returns signed speed), `helpers/discrete_scan.py` (`find_state_segments`, oracle-validated, used by 3 transit modules) ALL already built.
- NEW `agent/calculations/transits/combustion_scan.py` -- `scan_combustion_windows(start_jd, end_jd, *, coarse_step_jd=0.5, planets=5 taragrahas)`. ASSEMBLY: reuses core/combustion `_ORB_DIRECT`/`_ORB_RETRO`/`_min_separation` (single source of truth for the Surya-Siddhanta orbs), ephemeris speed, and find_state_segments. ONLY new logic = `_is_combust_at` (transit-mode retrograde read LIVE from speed<0, not from natal chart_data). MOON EXCLUDED (amavasya, already in panchanga/tithi; combustion.py's own double-penalize warning) -- also removes the fastest-flipping body, making coarse_step=0.5 JD safe (narrowest remaining episode is Mercury's, days-to-weeks). CHART-INDEPENDENT (depends only on Sun-planet separation) -- flagged: the per-chart timeline may want a shared ephemeris cache at assembly time. Bug caught+fixed: orb tables are Capitalized-keyed while output is lowercase -> `_orb_for` capitalizes to index.
- RATIFIED measure-first (120-day sample from 2026-10-04, Moshier): Venus retro [10-19..10-29], Mercury retro [10-30..11-10], Mercury direct [12-06..01-23] 47.75d. Verified against external ephemeris -- Venus inferior conj 24 Oct 04:39, Mercury inferior 4 Nov 14:20 (both dead-center); Mercury superior ~30 Dec geometrically pinned (greatest elong W 20 Nov 19.6deg sits in the scan GAP; exit 23 Jan rules out a Jan conjunction). The 47.75d is Mercury loitering near aphelion (24 Dec). No slow-graha combustion in the sample (correct). VARSHAPHAL DEFERRED -- no Tajika engine; not bundled.

### VALIDATION / TESTS (all green on device)
- Logic tests runnable in sandbox: test_lucky_facts (10), test_timeline_store (14), test_combustion_scan (6, synthetic ephemeris), test_fact_store, test_conversation, test_muhurta_facts; test_capability_gate FACT_BLOCK_PROVIDES pin + lucky render.
- Real-ephemeris ratification (house style, no skip -- swisseph is a hard dependency, 28 calls in chart_calculator): NEW `tests/calculations/transits/test_combustion_scan_ephemeris.py` (5) -- conjunction-CONTAINMENT + retro flag + duration BAND (not exact boundaries, which shift by backend). 5/5 PASS, no band needed widening.
- Full suite: 4943 passed / 7 skipped / 2 xfailed / 0 failed (the 7 skipped are real-GPT-call tests, not swisseph).

### DECISIONS / FINDINGS
- 9-agent conflicts resolved toward LESS: single re-anchor threshold (dropped the redundant 30d front-edge); fact_store I/O NOT extracted (rule-of-three, keeps committed green code untouched).
- "Hardest case first" (combustion) turned out ~80% pre-built -- the value was confirming reuse, not new astronomy.
- Combustion/transit/masa are all chart-INDEPENDENT ephemeris facts; only their interpretation is chart-relative -- a shared-cache vs per-chart-copy decision deferred to timeline assembly.
- SESSION HYGIENE: CLAUDE.md "Current Session Focus" trimmed to S147 + S146 only (S145->S130 narrative lives here in SESSION_LOG); 4 new Locked Decisions added (no-storage reversal, conversation-context standing, muhurta-as-planner-flag, dated-facts-calculated).

### FILES (committed in 5702d2f)
NEW: `agent/astro/{muhurta_facts,conversation,fact_store,static_facts,timeline_store,lucky_facts}.py`, `agent/calculations/transits/combustion_scan.py`, `tests/astro/{test_muhurta_facts,test_conversation,test_fact_store,test_timeline_store,test_lucky_facts}.py`, `tests/calculations/transits/test_combustion_scan_ephemeris.py`. EDITED: `agent/astro/{planner,capability_gate,pipeline,interpreter,static_facts,fact_store}.py`, `frontend/app.py`, `tests/astro/test_capability_gate.py`, `.gitignore` (data/timeline_cache/), `CLAUDE.md`, `SESSION_LOG.md`.

### CARRY-FORWARD / NEXT (fresh session)
1. ~~RATIFIED git commit of the S147 stack~~ -- DONE, `5702d2f`. Verified at S148 open.
2. **Timeline engines still to build**: masa composer (on existing `core/panchanga.py`, same find_state_segments pattern) and the transit INGRESS table (widen the existing Saturn-only gochara into a general per-graha ingress/station table). Then wire `build_timeline` + the runtime dispatcher (planner emits parametrised calc-requests; muhurta becomes the first registered calc; beyond-1yr-horizon = live-compute). Combustion is the first ratified engine of this set.
3. **Storage split decision** at timeline-assembly time: shared chart-independent ephemeris cache vs per-chart copy (combustion/transit/masa intervals are identical across charts).
4. **Deferred from S146** (still open): validate the timing-ranking probe (W_KARAKA N>1 decision); interpreter "surface top-ranked window even if past".


---

## S151 (2026-10-11) — store int-key fix (DONE) + muhurta→registry migration (Option A, DONE — b84d3b4 + 50ff1ea, pushed)

Design-chat + direct execution on the device tree (Cowork-with-device model per the S151 handover). No git commit this session unless a `RATIFIED: commit authorized` token is given; tree left modified for review.

### Point 1 — caching int-key fix: DONE — committed b84d3b4, pushed
Root cause: JSON coerces int dict keys to strings, so a cache HIT returned `lord_house_map` / `house_lords` / `ashtakavarga.sav_by_house` with keys "1".."12" where readers expect 1..12. Six read sites already hand-patched this with `.get(h) or .get(str(h))` (pipeline ×3, predicates ×2, lucky_facts ×1) and silence_gate coerces `int(k)`; the ONE unpatched reader (`pipeline._fact_block` sav_by_house) both silently dropped the per-house lines (`if _h in sav_h` false on str keys) AND KeyError'd (`sav_h[_sh]`).
Fix: `_decode_int_keys` at the STORE load boundary (fact_store.load_or_build cache-hit return; timeline_store.load_or_refresh fresh-window return) — digit-string keys coerced to int recursively, non-digit (planet-name) keyed dicts untouched. Copied into both stores (S147 no-share lock), NOT shared. Makes keys consistently int store-wide; the six hand-patches are now redundant (left in place — cleanup is a later task). NO SCHEMA_VERSION bump (old files decode correctly on read); NO runtime shape-assert in the stores (they stay calculator-agnostic — the house-survival coverage check lives in the two new round-trip tests instead).
Proven in-sandbox on the REAL cached chart `fecfe1a48656e908.json`: BEFORE decode = per-house 0/12 + KeyError; AFTER = 12/12 + OK. Sulabh ran pytest: store tests 26 passed; full suite 5064 passed / 7 skipped / 2 xfailed / 0 failed (+2 = the two new round-trip tests, uncommitted working-tree changes).
Files: agent/astro/fact_store.py, agent/astro/timeline_store.py, tests/astro/test_fact_store.py, tests/astro/test_timeline_store.py.

### Point 2 — muhurta → capability registry: Option A DONE — committed 50ff1ea, pushed (suite 5064/0; live gate capture-confirmed diagnostics/qa_capture/20261011T141736Z.md)
Decision (Sulabh, ratified in chat): migrate muhurta from the bespoke `plan.muhurta` flag onto a `capability_registry` row (dated=True), KEEPING muhurta's compose muhurta-shaped for now — do NOT build a generic registry-driven dated-compose dispatcher yet.
Resolved by reading (not a question): muhurta stays LIVE-composed at answer time, NOT stored in timeline_store. Its horizon is question-parametrised (2yr default / "next N days" / "next N dates"); timeline_store holds fixed-window, sky-shared facts only (combustion/ingress/masa, S149).

### LOCKED DECISION — the generic "dated-compose socket" is deferred to Point 3 (do not build a second one-off cable)
The question "how generic to build the dated-compose mechanism" is answered: muhurta is the ONLY dated capability today, so a generic dispatcher built now would be generalising from one example (rule-of-three violation). Point 3 brings the 2nd–4th dated engines (combustion, graha ingress "when does Saturn enter my 7th", masa) AND a second unresolved question — CAPABILITY PARAMETERS: muhurta needs `{horizon}`, ingress needs `{planet, house}`; right now `muhurta_horizon` hangs on `Plan` as a one-off.
THEREFORE (Sulabh's instruction, this entry is the durable record): when the Point 3 engines land, DESIGN THE GENERIC DATED-COMPOSE MECHANISM + THE CAPABILITY-PARAM MECHANISM TOGETHER, with 2–4 real consumers in hand — a compose-callable per dated capability dispatched generically, and a typed param-carrying shape on the capability/plan. Do NOT add another bespoke per-engine compose cable the way muhurta's is. The muhurta Option-A compose is the concrete seed that mechanism generalises from; migrating muhurta onto the generic socket is part of that Point 3 arc.
TRIGGER: the first Point 3 dated engine (combustion or ingress) reaching the dispatcher.

---

## S152 (2026-10-17) — Dated-compose socket; friendship + Yogini fact classes; palm re-enabled

Branch wip/interpretive-pilot. Design-in-chat + direct-tree execution; Sulabh ran pytest/oracle/commit. Commits incl. `68736f3` (local_datetime). Suite green (~5040+ passed, friendship/yogini/gate tests added; pre-existing palm app-test fixed).

**1. Dated-compose socket (Point 3).** Added `Capability.kind` to `capability_registry` (`"chart"` | `"live"` | `"timeline"`). Design finding (ratified): the S151 "generic socket, muhurta is the seed" framing was half-wrong — muhurta is the OUTLIER. The timeline trio (ingress/combustion/masa) share ONE `build_timeline` scan and need NO typed planner param; selection is the interpreter's job, exactly like every other fact class. New `agent/astro/dated_facts.py` (`build_timeline_facts`): one scan at the max per-cap horizon (ingress 1100d, combustion/masa 400d), each cap trims its slice (next ingress per graha; near-term combustion ≤180d; current+2 masa). `pipeline.answer_question` dispatches live caps (muhurta, unchanged) + timeline caps; `_fact_block` renders all three (guarded, legacy-dict byte-identical). `FACT_BLOCK_PROVIDES` += ingress/combustion/masa. muhurta migrated to `kind="live"` (no S151 store reversal — storage is an internal builder detail). Engines (ingress/combustion S147/S148, masa S148) were built + ephemeris-ratified; this is wiring only.

**2. Friendship (pancha-dha maitri) fact class.** `agent/astro/friendship_facts.build_friendship_facts` restates the PVR engine `core/friendship.py` (natural + tatkalika → five-fold compound; 7 classical planets, nodes excluded by doctrine). Wired via `static_facts`, rendered in `_fact_block`, `FACT_BLOCK_PROVIDES` += friendship, `fact_store` schema 2→3. Supersedes S130's deliberate "friendship is contested, leave it out." **Oracle: validated 42/42 cells × 4 charts (Sulabh/Surbhi/Sheridan/David) vs AstroSage Five-fold Friendship table, 0 mismatches.**

**3. Yogini Mahadasha fact class.** `agent/astro/yogini_facts.build_yogini_facts` restates `dashas/yogini.py` (MD only — no AD engine). Rendered birth-local via `meta.local_datetime` (newly exposed in `calculate_chart`, mirroring `calculate_solar_return`), matching the Vimshottari `_calc_dasha` convention. `fact_store` schema 3→5. **Oracle (4 charts): starting-index formula `(nak+2)%8`, lord sequence, and year length (365.256363, verified identical to JHora) all match.** Remaining ≤2-day MD-END gaps investigated to root: NOT display (the local-render fix moved only the MD1 start anchor), NOT year-length. Measured on Sulabh with JHora's OWN stated Moon (212.2479°, 8.14% left): our PVR balance formula gives 89.21d, JHora's balance is 91.20d — a +1.99d / ~1.45-arcmin balance-at-birth divergence. This is the documented **Gap D1** (ephemeris/ayanamsa balance-at-birth residual; `docs/KNOWN_DIVERGENCES.md`, `jhora_sulabh.md` lines 138-142), inherited from the shared nakshatra-fraction input exactly as Vimshottari inherits it (Vimshottari MD1 −2.66d, Yogini +1.99d — same root, different year-multiplier). Our formula follows the classical PVR spec; the gap is oracle-vs-spec, ≤2 days, day-granular, deferred to the ayanamsa audit. NOT a Yogini bug.

**4. Palm re-enabled.** `_PALM_ENABLED` default flipped `"0"→"1"` in `frontend/app.py` (env kept as kill-switch); S72's default-off reason (Option Z drop) was void since S125 put palm back in V1. Default-on surfaced a latent bug — `palm_dominant_side` was read before init (the widget was its only setter) → KeyError in `test_app_dogfood_capture` once palm rendered. Fixed by seeding it in the session-state init block (default "Right hand"), the sibling pattern.

**5. Record hygiene.** Corrected the stale `capability_gate` KP-significators comment (said "parsed from PDF / requires a PDF" — false since S144's `compute_kp_significators`). Rewrote CLAUDE.md S141 clause (e) + added the TIMING-FUTURE-DATES lock to stop every session re-opening the already-closed-and-tested marriage-window item; the future-default is already live in `EXPERT_SYSTEM`.

**Still open / deferred:** Gap-D1 ayanamsa audit (shared Vimshottari+Yogini balance precision); AstroSage retirement (needs Varshaphal + Char/Ashtottari dashas built — `annual/` is empty, no chara/ashtottari files); Lal Kitab ingestion; the 6 redundant int-key `.get` hand-patches (S151).

## Session 153 (2026-10-22) — Jaimini/KP/varga surfacing, dasha engines, Narayana shipped
Suite 5177 passed / 0 failed at close. Branch wip/interpretive-pilot. All via the device bridge (direct tree edits), committed here.
- FRIENDSHIP RENDER FIDELITY FIX: _fact_block renders all 5 pancha-dha maitri tiers incl. empties ("friend: none"). Closes the live-run mis-binning where the interpreter back-filled a missing "friend" slot from NEUTRAL planets; root cause was the render OMITTING empty tiers (a vacuum), not the fact. (pipeline.py, test_friendship_facts, test_capability_gate.)
- KP ALL-12 CUSP SUB-LORDS: kp_facts surfaces cusp_sub_lords{1..12} (was 7th only); engine already 47/48 oracle-validated (S143). FACT_BLOCK_PROVIDES += kp_cusp_sub_lords.
- EXTRA SHODASHVARGA: divisional_facts surfaces the finer 6 vargas (D16/D20/D27/D40/D45/D60) — all 14 already 4-chart validated; render de-duplicated to iterate the dict (P-030).
- BHAVA ARUDHAS ALL-12: jaimini_facts surfaces bhava_padas{1..12} via compute_bhava_padas (PVR Example 29-validated), separate fail-soft block so AL/UL stay robust.
- KARAKAMSA: jaimini_facts surfaces karakamsa (AK's navamsa sign, PVR Ch.7). "Swamsa" deliberately NOT surfaced — not a PVR term.
- PYTEST FAILURE LOG: conftest.pytest_terminal_summary overwrites diagnostics/latest_pytest.log each run with failed nodeids + tracebacks.
- STRONGER_RASI (§15.5.2): NEW in jaimini/strength.py — 6-rule stronger-rasi cascade (Narayana seed selector). Validated vs PVR Exercise 26 (Chart 12 D-10, 6 pairs, answer key p.217).
- NARAYANA DASA: NEW agent/calculations/dashas/narayana.py (Jaimini rasi dasa, PVR Ch.18). Progression COMPUTED from the Brahma/Shiva/Vishnu movement rules (NOT a transcribed table); cross-validated 36/36 vs PVR Table 40. Lengths §18.2.2 (count/direction/dignity/own-sign/2nd-cycle). Validated: Table 40 + Example 66 (book) + JHora v8 END-TO-END on Sulabh — exact, every edge incl. the Sc co-lord resolving to Ketu. Wired via narayana_facts.py (yogini-style dated intervals), static_facts, _fact_block render, FACT_BLOCK_PROVIDES += narayana.
- D5 SOLVED: stronger_co_lord(purpose="dasa_duration") stays LOCKED (do not reopen). Narayana's length fn applies PVR Step-5a (larger-length co-lord) ITSELF, reusing stronger_co_lord's purpose-independent steps 1-4. Sc=9 (Ketu) on Sulabh is the proof.
- data/default_user/jhora_sulabh_dashas.md saved (JHora v8 oracle tables for Sulabh).
OPEN, deferred by Sulabh until more greenfield modules land: (1) live Streamlit Narayana "when" check; (2) Narayana end-to-end on David/Sheridan/Surbhi. Parked: Narayana antardasas (§18.3); special_lagnas surfacing (no oracle yet).
