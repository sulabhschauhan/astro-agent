## Session Log

> ARCHIVES: Sessions 19-66 -> `SESSION_LOG_ARCHIVE_S19-S66.md` (split at S81); Sessions 67-104 -> `SESSION_LOG_ARCHIVE_S67-S104.md` (split at S105). This live file holds head-matter + S105 onward.

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
This live file holds: the Session 45 compression block, the locked Chunk
Metadata Schema and the Sessions 0-18 rollup (all below, NEVER archived),
then S105 onward.
Any `SESSION_LOG.md S<n>` citation with n<67 means the S19-S66 archive;
67 <= n <= 104 means the S67-S104 archive.
Note: the archive IS sequential (S19-S66, S32 restored to position at S81), but 34
of 80 sessions have no ``## `` header of their own — grep by content, not by header. Git holds every pre-split byte: \git show <hash>:SESSION_LOG.md\.
Boundary rule: never split above a session still cited by CLAUDE.md.

## S105

Pre-5b verb-form measurement sweep (6 live gpt-4o calls, 2 hands x N=3, temp=0). Confirmed temp=0 is NOT fully deterministic -- verb-form ("joins"/"joined") and even which relational lines get reported drift run-to-run on the identical image. The earlier "joined" gap (that aborted the first 5b attempt) was real but did not recur in this 6-call sample -- established that the S106 inflection fix is aimed at the right class of variance (tense/aspect), not a one-off fluke. Read-only, no commit.

## S106 (7c2cea9)

Deterministic inflection normalization shipped in `contact_mapper.py`: generate-the-forms (not stem-the-input) expansion of every declared verb into its regular tense/aspect siblings, a crossed/crossed-by collision guard (never guesses active `cuts` from an ambiguous bare "crossed"), and an import-time ambiguity guard. Fixes `joins`/`joined` and every regular tense family. **PROVISIONAL, per user directive:** on the NEXT verb-form failure (an irregular like `met`/`cut`, or a genuine new synonym), REMOVE the inflection layer entirely and replace verb->token mapping with a simple LLM call -- do not patch narrowly again. `meeted`/`cutted` are known-harmless dead keys (never produced by real English); `met`/bare `cut` are known, accepted un-covered silences.

## S107 (44e6e5b)

Atomic Step 5b cutover: `H_028`/`L_026` now fire via CONTACTS -> `contact_mapper` -> targets; the typed RELATIONSHIP emission+parse path is fully retired (shared symbols `_RELATIONSHIP_TOKENS`/`_RELATIONSHIP_LINE_HEADER`/`_RELATIONSHIP_LINE_ALIAS` + `_store_relationship` KEPT as the bridge's filing primitive). New bridge `_assemble_relational_targets` lives in `palm_reading.py`; `prepare_palm_reading` confirmed the sole rules-feeding caller. Live two-hand sanity 6/6 (N=3 x 2 hands), determinism gate byte-identical vs. the pre-cutover deterministic path.

## S108 (fb10989)

Standalone LLM synonym-resolver shipped, `contact_llm_fallback.py` -- fires ONLY on a contact `contact_mapper` already returned `token=None` for; maps the unknown raw verb to the CLOSEST KNOWN CANONICAL verb (never a token directly), then re-runs the real deterministic `map_contact` on that canonical form so token/position-split logic stays 100% deterministic. Batched (one call per reading regardless of how many contacts need rescue), fail-closed on hallucination/malformed JSON/timeout (whole batch -> unclear), returns structured audit records per contact. NOT wired into the pipeline this step.

## S109 (5ad314e)

Wired the S108 fallback into `prepare_palm_reading` via `_assemble_relational_targets_with_fallback`: exactly one batched LLM call per reading across BOTH hands, fires only on residual `token=None` contacts, degrades safely to the deterministic-only result on any unexpected error (never breaks a reading), audits logged at WARNING (amended same session to include `position_unresolved` -- visibility/measurement only, no token fired, no second call). Determinism gate stays byte-identical with the fallback client stubbed to raise if ever touched; live dormancy check confirmed 0 fallback calls on the standing test images (every verb already resolved deterministically).

## S110

David_right live probe (3 calls, first real third hand tried on the relational arc). `L_026` (Head+Heart+Life triple-join) never fired -- the Heart line reports zero contacts on this hand, an anatomy/perception limit, not a pipeline gap (H_028, the structurally identical single-antecedent sibling, fires cleanly every run). The Fate line is clearly and consistently perceived (unlike parked `FT_016`), and "Fate crosses Head" is captured cleanly end-to-end -> the `cuts` token -- but NO rule in the corpus consumes `cuts` for any feature: a real, newly-surfaced rule-coverage gap, distinct from a perception or pipeline failure. Read-only, no commit.

## S111

STOPPED before authoring: the task asked to author two new Fate stopped-by-Heart/Head rules from Cheiro p164, but `FT_007`/`FT_008` already exist, verified 2026-08-22, encoding exactly that doctrine (via the older TERMINATION-landmark antecedent) -- the census's "no such rule exists / UNCAPTURABLE" text was stale relative to the live corpus. No code touched; flagged for a design-chat call on migrate-vs-duplicate.

**Doctrine finding (from the S110/S111 arc):** a plain Head-crossing of Fate is anatomically universal and doctrinally INERT -- no Cheiro reading attaches to it; do NOT author a `cuts`-on-Head rule for the Fate line. The real doctrine at that junction is `stopped_by` (p164, negative) vs. `meets`/`FT_016` (positive, join-and-ascend). `cuts`'s own real doctrine (bar/influence lines cutting the fate line, p136) is a DIFFERENT source, part of the already-scoped-out Hindu ray-line/Line-of-Influence subsystem (S96).

## S112 (44a720f)

Migrated `FT_007`/`FT_008` IN-PLACE (same rule_ids, same claim/source_quote/doctrine_sentence_ids/verified status) from the ambiguous TERMINATION-landmark antecedent (`attribute: Position` + `relation_target`) to the typed `stopped_by` token. Closes a real, live false-positive: a bare "Fate terminates at Heart" landmark couldn't distinguish an abrupt HALT (this doctrine, bad omen) from `FT_016`'s opposite join-and-ascend good-omen doctrine at the identical endpoint. Fixture-tested only -- no live hand has ever exhibited this geometry; live `stopped_by`-verb emission stays untested until one does.

## S113 (8f36f67)

Fixed `vocab_reachability_scan.py`: typed-relationship tokens are now classified via the relation registries (`relation_target_registry` etc.), not the value-attribute map (`attribute_feature_mapping`). Root cause: the scanner's value-map existence check short-circuited BEFORE the relation branch ever ran; `joins_at_origin`/`meets` had been worked around by injecting them into the value map (2 of 8 tokens), leaving `stopped_by`/`cuts`/`cut_by`/`touches`/`takes_possession_of`/`branch_in` false-flagged unreachable. Fix mirrors the already-correct `rule_vocabulary_closure_gate.py`. Negative guard (a genuinely unknown attribute) preserved -- the gate still bites.

## S114 (9963397)

Fixed `gate_rule_citations.py`: was hardcoded to a dead legacy S84 candidate pool (zero live rule_ids) and a corpus path used inconsistently; repointed onto the live rule files + `cheiro_clean_v1.json`, replaced the source_page-vs-page_ref adjacency check with a whole-corpus anchor search (tolerates the printed-page<->page_ref offset). Report-only (never writes a rule file); added test coverage (zero prior coverage existed). Result: ALL 75 live + 13 parked rules anchor in the corpus, ZERO fabrication signal. **FINDING:** the page-numbering convention differs PER FILE, not one global offset -- Fate's `source_page` is a genuinely PRINTED page number (+60 to reach the corpus `page_ref`); Head/Heart and Life already use the corpus's own `page_ref` directly (offset ~0). Check which convention a chapter is using before assuming +60 when authoring a new file's citations.

## S115 (3f91d67)

Removed the two leftover `joins_at_origin`/`meets` keys from `attribute_feature_mapping` (the value-attribute map) -- the last remnant of the old pre-S113 scanner workaround. Prompt diff showed ONLY those two lines removed from the vision value-prompt's "VALID ATTRIBUTES" lists; relation-rule firing (`H_028`/`L_026`/`FT_016`) byte-identical; all 8 typed tokens confirmed still reachable via the relation path with ZERO of them now in the value map -- direct proof of the independence S113 established. Live sanity: a left-hand vision-API refusal occurred on this run (unrelated to the edit -- `describe_palm_image`'s own prompt was never touched), handled as honest silence; the right hand fired `H_028` normally, satisfying the check.

## S118 (27a9edd)

**Banned-mention censor: the support-gate jurisdiction principle applied GENERALLY.** S117's `3a3d625` established that a rule-fired feature is outside the retrieval support-gate's authority and applied it to the two gate TUPLES; S118 applies the SAME ratified principle to the banned-mention censor (`_check_banned_feature_mentions`, `agent/interpretive/palm_reading.py`). Claim-driven, NOT needle-driven: no Mars special-casing, no `_SUPPORT_NEEDLES` edit, no retrieval change.

ROOT CAUSE, confirmed at HEAD before editing and NOT a `3a3d625` regression. `3a3d625` works as designed -- per `diagnostics/s117_live_confirmation_raw.json`, `"mount of mars positive"` (the M_023 claim, C6) is in NEITHER gate tuple. The failure is entirely downstream: `"mount of mars negative"` fired no rule and retrieved no supporting chunk, so it sits honestly in `unsupported_features`, and `_SUPPORT_NEEDLES` gives BOTH Mars mounts the single shared needle `"mars"` (documented accepted imprecision -- Cheiro p113 has no single-word discriminator). The old censor asked only "did SOME needle of this unsupported feature match?" via `pattern.search`, so C6's sentence ("The Upper Mount of Mars gives you active courage and a martial spirit.") matched `"mars"` on the unclaimed sibling's behalf and failed the whole otherwise-clean reading TWICE -- once at the Stage-2 extra-validator seam, once at the fail-closed backstop.

THE PREDICATE (per-MATCHED-NEEDLE attribution, `finditer` not `search`): let `allowed_needles` = union of `_SUPPORT_NEEDLES` over every feature holding a surviving rule claim; flag an unsupported feature iff it has >=1 word-boundary match AND at least one MATCHED needle is absent from `allowed_needles`. A matched word is allowed when attributable to ANY feature that fired a rule; a genuinely unsupported feature is still flagged the moment it is named by a word no claim accounts for, so the hallucination guard is intact. Nothing in the predicate names a feature, a mount, or Mars -- it reads `_SUPPORT_NEEDLES` only to DERIVE the allowed set, so future needle edits and new shared-needle pairs are covered by construction.

REJECTED ALTERNATIVE, evaluated and NOT equivalent (the instructing prompt offered it as a "cleaner equivalent" framing): the whole-feature subset form, "skip `feature` when needles(feature) is a subset of allowed_needles". Strictly coarser and over-flags. Counterexample, now a test: with `sun line` claimed (`allowed={sun}`) and `mount of apollo` unsupported, `needles(apollo)={apollo,sun}` is NOT a subset, so a sentence about the CLAIMED sun line still fails -- even though its only matched word, `"sun"`, is fully attributable to the claim. Per-matched-needle attribution is what actually states the ratified principle; the subset form only approximates it. Recorded in the shipped docstring.

THREADING (compute once, pass down -- no recomputation): `features_with_surviving_rule_claims` was already computed once in `_prepare_deterministic_prep` (the same expression that narrows both gate tuples) but was NOT in scope at either censor call site. Carried on a new defaulted `PalmReadingPrep.rule_claim_features` field; `allowed_needles` derived ONCE in `complete_palm_reading` and fed to BOTH live call sites (`_build_display_extra_validators`'s `_banned` closure = Stage-2 retry seam; `_run_display_checks` = fail-closed backstop), so the two can never disagree. The retired `_run_ring1_checks` path keeps the empty default and is byte-identical.

BLAST RADIUS, stated precisely: because `3a3d625` already removes a claimed feature from `unsupported_features`, the censor could never flag a claimed feature for naming ITSELF -- so the only outcomes S118 can flip are ones where a genuinely unsupported feature SHARES or OVERLAPS the matched needle with a claimed one. Today `_SUPPORT_NEEDLES` holds exactly two such collisions, `{mars positive, mars negative}` on `"mars"` and `{mount of apollo, sun line}` on `"sun"`; both are tested in both directions. Every other reading, and the ENTIRE LLM Stage-1 path (its claims are retrieval-sourced, hence squarely inside the gate's jurisdiction -- pinned by a dataclass-default test), is byte-identical.

TESTS: 13 new in `tests/interpretive/test_palm_reading_rules_engine.py` (+263), covering generality/non-Mars, the Mars live failure, guard-intact, decline-unchanged, and no-claims. The primary generality proof is the `sun line` <-> `mount of apollo` overlap run in BOTH directions; the stronger direction has the claim held by the SUN LINE (a line, not a mount) with the unsupported apollo carrying a strict SUPERSET of its needles -- that is simultaneously the anti-mount-patch proof and the case that fails under the rejected subset framing, so it pins the predicate's SHAPE, not just its outcome. A rule-fired sun line cannot be built end-to-end today (no sun-line rules exist in any of the 4 live rule files), so that pair is exercised at the censor's own boundary with the allowed set still derived by the production helper. The Mars case IS end-to-end and deterministic (no live call): `MOUNTS: DEVELOPMENT (Upper Mount of Mars): present` -> M_023 -> one claim, retrieval stubbed to unrelated life-line text so the sibling is honestly unsupported; asserts the verbatim live C6 sentence reaches `reading_text`, `validation.failures == ()`, and EXACTLY 2 LLM calls (2 means the seam saw no failure and Stage 2 never retried). Its pre-fix counterpart is not hypothetical -- the no-claims parametrised row asserts the SAME sentence + SAME unsupported feature + empty allowed set still yields the old failure string.

FIXTURE CORRECTION made en route, flagged not silent: the guard test originally used "the markings on the palm are many" expecting `markings/other features` to flag. It does not -- `"markings"` does not word-boundary-match the `"mark"` needle. That is PRE-EXISTING, DELIBERATE behavior (the S67 R2 rider: word boundaries so `"remarkable"` never fires `"mark"`), unrelated to S118 and unchanged by it; the test was corrected to `"a star"`. Same singular-noun needle limitation already registered in CLAUDE.md's Carry-Forward ("needle-inventory audit", S70 F-E). No needle was edited.

VERIFICATION: deterministic C6 recheck replaying the LIVE capture (real `reading_text_tagged`, real `unsupported_features`, real claim set from `s117_live_confirmation_raw.json`; no live call made) -> BEFORE `['unsupported feature mentioned: mount of mars negative']`, AFTER `[]`. `scripts/gate_rule_citations.py` -> NOT_FOUND_ANYWHERE 0. Full suite **3687 passed / 7 skipped / 0 failed**. Four lines' rule/reading files re-run explicitly -> 270 passed. Registry-wide sweep: 15 flags with no claims, 0 flags with every feature claimed -- guard fully live at one extreme, fully deferential at the other, nothing hardcoded between.

**Capture-net digest tool committed (`dee8007`).** S116-era artifact, built and tested in an earlier session but never committed; landed here unchanged. `agent/interpretive/capture_net_digest.py` (170 lines) is a READ-ONLY summarizer over the capture-net JSONL -- groups by trigger / trigger x feature / disposition and surfaces the `ai_decision` lane for the monthly human review, with `build_digest`/`render_markdown` plus a `--since/--until` CLI. Never writes, moves, or truncates the log (verified against source: `read_text` only, no write path anywhere); `_KNOWN_TRIGGERS` derives from `capture_net._DISPOSITION_TO_TRIGGER` rather than duplicating the vocabulary. NO auto-verdicts and NO contradiction detection by design -- it is the review's INPUT, never a substitute for it (Working Style #5). Companion to the capture-net writer + wiring committed at S116 `3866997`. 7 tests, already collected by the suite before the commit (pytest collects from the filesystem, not the git index -- which is why the suite count did NOT rise on commit; verified separately at 7 passed).

BRANCH CLOSE-OUT: `wip/interpretive-pilot` fully pushed, head `1d18fa2`, no tracked file modified, `git log origin/wip..HEAD` empty. 47 untracked paths remain, ALL classified keep-untracked session artifacts (28 `diagnostics/*`, 18 one-off `scripts/*` probes, 1 `probes/`); zero sit outside those directories. Working Style #16 audit RUN rather than assumed: every untracked probe basename grepped against committed `CLAUDE.md`/`SESSION_LOG.md`/`diagnostics/` -> zero citations, so none backs a recorded decision and leaving them untracked opens no audit gap. Ready for the astrology pivot.

CARRIED DEBT, unchanged and still open: `claim_voicing._FEATURE_TRAIT_NEEDLES` is a drifted verbatim copy of `_SUPPORT_NEEDLES` (10 vs 16 features), and the DUAL USE of `_SUPPORT_NEEDLES` for both corpus retrieval and output censoring is the deeper structural cause -- Direction B, deferred to its own session, out of S118's scope.

LOG GAP NOTED, not silently papered over: this file has NO S116 and NO S117 entry (first S116/S117 mention anywhere in it is this line). Both sessions shipped real work -- S116 the capture-net writer + wiring (`3866997`), S117 the mounts arc (mount-development emission/extractor, the 24-rule Mounts chapter, live wiring, and the support-gate jurisdiction fix `3a3d625`). Backfilling them from commit history is a separate task and was deliberately NOT attempted here, to avoid reconstructing sessions from commit messages alone into a durable record.

## S119 (37d88e8)

**THE SELF-GROUNDING CONSOLIDATION.** A rule-sourced claim now cites its OWN authored, gate-verified `source_page`+`source_quote` and no retrieval chunk is resolved for it at all. Nine commits, measured start to finish: citation accuracy **31% -> 100%** (gate-verified), live rule count **99 -> 87**, suite **3794 passed / 7 skipped**. This is the fourth and final member of the "a retrieval-era mechanism must not gate a rule claim" family, after S117 `3a3d625` (support-gate tuples) and S118 `27a9edd` (banned-mention censor) -- and unlike those two, which exempted rule claims from a gate, this one removes the retrieval dependency itself.

MEASURED FIRST, NOT ASSUMED (`e7eec28`, Step 0). The consolidation opened with an audit probe over all 99 live rules rather than a design argument: **31 correct / 52 wrong / 13 dropped** -- 69% of live rules carried a wrong or missing citation. Two independent root causes, both mechanical. (1) A rule's authored `source_page` is not the corpus `page_ref` -- the fate-line file is offset by a constant +60, so every fate rule resolved into the wrong chapter entirely. (2) `resolve_chunk_id` always selected `_c0` regardless of which chunk on the page actually carried the quote. The 13 "dropped" rules were worse than wrong: a rule whose chunk could not be resolved was silently DROPPED from the claim set, so `FT_003` fired correctly and then vanished before the reading. The probe is committed with its numbers per Working Style #16 -- an uncommitted probe cannot be audited when its numbers turn out wrong.

THE FLIP (`c879e45` Step 1 additive, `f9383d4` Step 2 the cutover). Step 1 added a citation sum type to `Claim` (`by-chunk | by-rule`) as a pure carrier, changing no behavior -- so the type could land and be tested before anything depended on it. Step 2 flipped rule claims onto the `by-rule` arm and DELETED both the chunk-resolution path and the silent-drop branch. The safety argument is not "the new citations look right": it is that `scripts/gate_rule_citations.py` already verifies every authored quote against the real corpus text, so a by-rule citation is authentic by the same check that authored it. `FT_003` un-dropped as a direct consequence. Accuracy went 31% -> 100% because the question changed -- there is no longer a resolution step that can be wrong, only an authored quote that the gate has already verified.

DOWNSTREAM CONSEQUENCES, each its own commit rather than folded into the flip. `46573c4` (Step 3): the decline/jurisdiction set was being computed from POST-DROP claims, so a dropped rule made the reading actively lie -- "the classical texts I work from do not clearly address your fate line" while `FT_003` had in fact fired on it. Re-sourced from SURVIVING RULES, killing the false decline. `17cb671` (Step 4): the capture net was keyed off the old chunk-resolution failure mode and therefore saw nothing at all after the flip; re-keyed off `by-rule` `source_page`. The dropped-rule tripwire is retained but now DORMANT BY CONSTRUCTION -- see the invariant below.

MOUNT BASE MEANINGS ARE DEFINITIONS, NOT CLAIMS (`7be74db`, Step 5). The mounts chapter authored a "base meaning" rule per mount that fired on mere presence and produced a standalone claim. Read back as delivered prose, these are Barnum statements -- true of everyone, discriminating nobody. Reclassified as DEFINITIONS that supply consequent context to GRADED rules and never stand alone; 10 rules retired. `sources` was rebuilt from by-rule citations in the same commit, which closed the S120 "2 of 6" sources gap as a side effect rather than as a separate fix. Consequence accepted deliberately, not worked around: mounts with only a base meaning and no graded rule (Saturn, Mercury, Lower Mars, Luna) are now HONESTLY SILENT. Silence is the correct product behavior here (Palm Diagnostic Principle #2), not a coverage regression to paper over.

DEFECT 2, found by reading the source rather than the code (`7177a32`). Saturn's `M_015`/`M_016` survived Step 5 as graded rules, so Saturn was not yet silent. Checked against the PDF: both quotes are HEAD-LINE back-references that merely mention Saturn in passing -- they are not mount doctrine at all. Retired; Saturn is now fully silent. This exposed a gate limitation worth stating plainly: `gate_rule_citations.py` verifies that a quote is AUTHENTIC (it exists in the corpus at the cited page), never that the quote AGREES with the antecedent it was attached to. Defect 2 is one instance of that class; the rest of the corpus is unaudited against it (parked track below).

THE NEEDLE-TABLE SPLIT (`92230fa` Step 6, `37d88e8` Step 7) -- closing the CARRIED DEBT S118 logged verbatim. Step 6 was a PURE RENAME: `_SUPPORT_NEEDLES` served two jobs with genuinely different requirements -- corpus support-gate matching (permissive substring against OCR'd book text) and output-feature identification (word-boundary against the model's own fluent English) -- so it split into `_RETRIEVAL_NEEDLES` and `_OUTPUT_FEATURE_IDENTIFIERS` with IDENTICAL values, each consumer repointed to its own job's table, pinned by an equality test against an independently transcribed pre-split oracle so a future divergence must be a conscious, tested edit. Step 7 then deleted `claim_voicing._FEATURE_TRAIT_NEEDLES`, the verbatim copy commented "kept identical anyway so the two dictionaries never drift apart for no reason" -- which had drifted regardless to **10 features against the real 16**, missing every mount added at S117. The copy existed only because `palm_reading` imports `claim_voicing` at module level, so the reverse import would close a cycle; the fix is the leaf module `agent/interpretive/feature_needles.py`, which imports nothing from `agent.interpretive` and can therefore be read from both sides. Both modules now hold the SAME objects, not equal copies.

V-5 BEHAVIOR-CHANGE ANALYSIS, reported BEFORE relying on tests (Step 7 was dogfood-gated for exactly this reason). V-5 flattens the needle table into a UNION of words and never uses the per-feature structure, so the delta is 16 -> 22 words: `apollo`/`luna`/`mars`/`mercury`/`moon`/`saturn` ("sun" was already present via `sun line`). `_check_flow_doctrine_guard` skips every segment whose tag is not `FLOW`, so the change is precisely: an UNANCHORED `[FLOW]` connective naming a mount noun now fails where it silently passed. Anchored `[C<n>]`/`[OBS]` mount sentences were never in V-5's jurisdiction -- already pinned pre-Step-7 by two existing tests -- so the widening cannot reject a legitimate mount sentence. No scoping sub-decision was needed: the 6 new words are proper nouns, and the union already carried far more collision-prone ordinary English (`life`, `head`, `cross`, `star`, `mark`, `sun`).

DOGFOOD GATE (Step 7, required before commit -- a green suite was explicitly NOT sufficient). One live run, `data/test_images/palm_right_test.jpg`, rules ON, one explicit `OpenAI()` client, N=1, never `client=None`. The hand is the right gate because it produces mount claims whose nouns are among the 6 newly-added needles. Result: `validation_passed=True`, `validation_failures=[]`, `stage2_retry_used=False`, `stage2_first_attempt_failures=[]`. The Venus, Jupiter and Upper-Mars claim sentences all reached the delivered reading; the only new-needle occurrence in the entire draft was "Mars" inside the anchored `[C6]` segment. Guard proven LIVE rather than merely silent by a counterfactual on the SAME real text -- moving "Mount of Mars" out of `[C6]` into the closing `[FLOW]` sentence fires `doctrine_guard` on the exact new needle, a sentence that would have passed silently before Step 7. So it is the `[FLOW]`-only scoping, not blindness, that keeps the real draft clean.

SELF-CAUGHT CORRECTIONS, flagged not silent. (1) Step 7's "no second needle literal" scan was first written as "any dict keyed by feature names" and flagged three LEGITIMATE dicts (`observation_extractor`'s feature->registry and feature->display-name maps, `palm_reading`'s feature->field-label map). Tightened to the needle table's actual signature -- each line feature maps to a tuple CONTAINING its own bare noun. Kept structural rather than name-based deliberately: the deleted copy escaped notice for sessions precisely BECAUSE it was named `_FEATURE_TRAIT_NEEDLES` and not `_SUPPORT_NEEDLES`, so a name-only grep would miss the next re-transplant too. (2) `data/palm_rules/palm_rules_mounts_v1.json`'s shared-needle note cited `observation_extractor._SUPPORT_NEEDLES` -- a module that never held that symbol; corrected to `feature_needles.RETRIEVAL_NEEDLES` with the rename history recorded.

VERIFICATION across the arc: `scripts/gate_rule_citations.py` -> `NOT_FOUND_ANYWHERE 0` at every step (87 live, 16 parked rules, 4 files). Reachability scan 27 passed. Suite progression through Steps 6-7: 3743 -> 3758 (+15, Step 6) -> 3794 (+36, Step 7), 7 skipped throughout, **zero existing tests changed behavior at either step** -- each delta is exactly the new tests, which is the specific claim a pure-rename/pure-move refactor has to be able to make.
