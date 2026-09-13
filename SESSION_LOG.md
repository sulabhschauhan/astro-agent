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


## S122 — vocab-contract / provenance arc — REVERTED to 048fe97
Outcome: all code reverted to session start; work archived in branch/tag `archive/S122-vocab-provenance-arc` (recoverable, off the active branch).
What we did (archived, not on branch): emission_menus mapper, vocab_adapter (unwired), provenance validator + suite-blocking gate + baseline, retired-rule cleanup (16 dead rules), FT_001/FT_009 well_marked→deep, FT_001 provenance migration, Heart HL_001/003/004 relation_target rewire (uncommitted).
PROVEN SAFE: before/after replay on the s120 real hand showed IDENTICAL firing at 048fe97 vs 2ae5f87 (same 6 rules) — the arc broke nothing; it was inert to the reading.
Why reverted: the arc was citation-integrity work, not richness work, and rested on an incompletely-traced diagnosis.
KEY LEARNINGS:
1. TWO extraction channels exist for line origins — flat-value (extract_observation tokenizes prose vs the registry's closed value pool; rising_from_X ARE legal Starting_Point values) AND structured (extract_relational_targets → targets, via ORIGIN/TERMINATION menus). A rule reachable via one may be dead via the other. Trace BOTH before calling any rule dead. This session twice overclaimed "provably unfireable"/"CI blind spot" by tracing only the structured channel.
2. Line-origin dual-encoding (flat value vs relation_target) is the REAL open question — resolve which channel real vision actually uses BEFORE rewiring. (s120 evidence: real vision emitted origin via the structured ORIGIN menu, not as a flat value — but not fully verified.)
3. Reading is thin on real hands (6/87 fired on s120) — a REACHABILITY + BREADTH problem (Heart/Fate fire ~0; Thumb/Sun/Marriage/Health unauthored), NOT a provenance problem. Thinness is pre-existing (6/87 at session start), partly by-design honest silence.
4. PROCESS: fully trace plumbing (all channels + consumers) and confirm on a real hand BEFORE designing a fix. Do not act on a diagnostic whose channel-tracing is incomplete.

## S123 (97bbd01)

**METHOD CORRECTION OPENED THE SESSION.** The S122 arc (reverted at session start, `7bc0735`) had judged which rules were "dead" by tracing only the CODE side -- the vocabulary-mismatch probe (`dbce778`) and its report (`048fe97`) classified antecedents against the emitted vocabulary without first asking what the RULES actually required, and reached wrong verdicts twice as a result (S122's own KEY LEARNINGS above). This session opened by correcting the method rather than the symptom: `290435b` adds the DESIGN-INTENT-FIRST standing law to CLAUDE.md -- everything present or absent is BY DESIGN until the record proves otherwise, and nothing may be called a bug without a history search and an explicit verdict label (BY DESIGN / PARKED / SCOPED OUT / KNOWN TRADE-OFF / UNRECORDED / GENUINE DEFECT). The ontology and vision prompt were derived FROM rule requirements, not the other way around, so judging the pipeline from the code's side alone is backwards by construction. The same commit closes the S123 audit of known-intentional items (Position overload, Hand/Type, Quadrangle, `most_specific_wins`, comparative/magnitudes) and flags two genuine findings for the arc that follows: the Line of Life ORIGIN/TERMINATION menu is NOT REQUIRED (no live rule needs it), and the SLOPE field ships half-connected.

**THE VISION_FLAT_SUBFIELDS ARC** closes that second finding. SLOPE (Head/Heart/Fate) and BREAK TYPE/LENGTH EXTENT (Fate) were emitted by vision on every hand as indented closed sub-fields that matched neither `_gather_feature_texts`'s flat-label lookup nor `_RELATIONAL_SUBFIELD`'s regex -- read by nothing, leaving H_026/FT_003/FT_006/FT_012 blind to signals vision was already sending. Four commits, each inert until the last: `dc50132` declares each field's attribute, closed menu and escape value in the registry, with a `write_policy` DERIVED (never hand-asserted) from whether the menu equals the attribute's full legal range (`authoritative`, overwrites on collision) or is a proper subset (`fill_only`, writes only into an empty slot) -- `fill_only` exists specifically because BREAK TYPE=broken would otherwise clobber a plain-sentence Continuity=double and kill FT_013 while fixing FT_012. `5e4771d` adds `extract_flat_subfields`, fully registry-driven, unwired. `53ecd0a` adds the SLOPE MAGNITUDE vision-prompt field itself (conditional, `n/a` whenever the degree isn't clearly judgeable -- S87 had already measured this boundary as genuinely unstable). `fff4301` wires the reader into the reading pipeline via a new `_merge_flat_subfields`, policy-aware, proven on the real s120 hand: the observation genuinely changes (Fate gains Slope=upward) while the fired set stays byte-identical to the pre-arc baseline.

**H_026 RE-POINTED, THE SLOPE DEFECT CLOSED.** `5098e90` adds the second antecedent H_026 was always missing -- Line of Head Slope_Magnitude=slight -- because Cheiro p146 states two distinct consequents (slight slope -> imaginative work; very sloping -> romance/idealism/Bohemianism) and the old single-antecedent H_026 asserted the slight-slope claim on any downward slope, accentuated included. Fired set on s120 drops 6 -> 5, losing only H_026 (that capture predates the SLOPE MAGNITUDE field and carries no magnitude at all) -- correct honest silence, not a regression. A live N=5 stress probe on a real hand then confirmed the whole arc end to end: SLOPE/SLOPE MAGNITUDE labels byte-exact across all five draws, the parser clean, and **FT_003 firing on a real hand for the first time**. `884068b`/`05d7b8c` close the defect in CLAUDE.md, additionally ruling that vision run-to-run variance on an identical photograph is BY DESIGN (borderline anatomical judgements a human palmist would also disagree on -- never treat a changed fired set on a re-run as a regression), parking Thumb (same relative-judgement class as the already-dead `proximity_degree` axis), and opening the Heart audit that the next two commits act on.

**HEART MIGRATION (`b23f0a7`), the first rules moved under DESIGN-INTENT-FIRST.** The Heart chapter fired ZERO on every real hand: its `Starting_Point` antecedents keyed the flat channel, but for Head/Heart/Fate the vision prompt emits origin only through the structured ORIGIN menu, and `_parse_fields` discards it from the flat path. Audit found no recorded rationale anywhere -- these six rules (HL_001, HL_003, HL_004, HL_005, HL_010, HL_018) were authored 11 days BEFORE the structured channel existed and were never revisited. Ruled an authoring-order artifact, migrated by CONNECTED SUBSET COMPONENT, never partially: `{HL_001, HL_010}` and `{HL_004, HL_005, HL_018}` each moved whole, because partial migration is exactly what broke `archive/S122-heart-rewire-wip` -- `resolve_priority` compares whole antecedent tuples, so a migrated rule silently stops being a subset of an unmigrated sibling. Verified, not assumed: the pairwise subset graph was recomputed via the real loader and the real `Antecedent.signature()` across all 87 rules, same-group and cross-group, before and after -- byte-identical. Proven on three real captured hands: Heart's ORIGIN is Mount of Jupiter or Junction of First and Second Fingers on every draw on record, so HL_001 or HL_003 now fires on every hand -- **the first love claims this pipeline has ever produced.**

**THE ABSENCE-DETECTION FIX (`29ff43f`, tagged S125 in the commit but landing inside this session's arc).** Found live on David's hand: he has no fate line, vision correctly wrote "FATE LINE: absent", but `_ABSENCE_PHRASES` had no bare "absent", so `_is_genuine_negative_absence` returned False, the feature stayed in the retrieval pool, cleared the score floor, produced zero claims, and the reader was told the classical texts do not clearly address fate lines -- false, since FT_003 fires for two other subjects in the same probe. A genuine defect, not a design choice: the vision prompt itself invites "state plainly if absent or barely visible", so the prompt invited vocabulary the detector could not recognise. Fixed additively (bare "absent" added to tier 1, every existing phrase byte-identical) and closed generically rather than by patching one word -- a single-source list of the prompt's invited absence vocabulary is now cross-checked against the detector in both directions, so a future prompt edit that invites a new absence term fails CI until the detector is taught it. "Barely visible" deliberately NOT added -- a faint line is a real observation, and treating it as absence would suppress a genuine finding. Not fixed, investigated and reported inert: the extractor maps bare "absent" into `Branching=absent` because no Presence attribute exists and Branching has no closed-value binding, so Stage-1 improvised into the one unconstrained slot; confirmed no live rule keys it.

**HEAD MIGRATION (`97bbd01`), the same fix applied to the same-shaped Head backlog.** Seven rules were diagnosed dead on 2026-08-07 in `_audit/reconciliation_head.md` ("the descriptor is the bottleneck, not the rule book"); the structured channel that fixes them arrived at S92-S93 scoped narrowly to proximity and branching, and the dead list was never revisited -- a backlog gap, not a design decision. Migrates H_002/H_003 (mechanical `Starting_Point` swap to Line of Life / Lower Mount of Mars) and RESHAPES H_013/H_024, collapsing two antecedents (`Branching=branched` AND `Position=terminating_on_Mount_of_X`) into one branch relation to Mount of Jupiter / Mount of Luna -- following H_014's shipped S93 precedent, since keeping both channels would require vision to supply the branch twice at once, which it never does. Excluded with reasons: H_007 (no structured equivalent), H_015 (Marks/Square, scoped out S96), H_023 (names no specific mount, unresolvable, not guessed), H_010a/b/H_020/H_021 (Position=high, permanently parked). Proven on three real hands: **H_002 joins the fired set on all three -- Head's ORIGIN reads Line of Life on 6 of 6 draws on record, the strongest reachability found in this whole arc** -- while H_003/H_013/H_024 stay honest silence (their values never observed on any hand yet captured). Subset graph byte-identical before/after; H_011 < H_007 intact; H_028 unaffected. The same commit unpins three generic engine tests in `test_palm_rules_table.py` that had borrowed `BY_ID["H_002"]` as a stand-in for "an undirected single-antecedent rule" -- coupling engine mechanics to live doctrine so a legitimate rule edit broke tests about something else entirely. Rebuilt on synthetic rules through the real `PalmRule`/`Antecedent` construction path, proven decoupled by running them against both the pre- and post-migration rule files with identical results; re-pointing at a different real rule was rejected as relocating the landmine, not removing it. Roughly fifteen further tests in the same file carry the identical fragility, catalogued and deliberately deferred.

**END-TO-END READ, three real subjects** (`diagnostics/s124_live_e2e_read_run.py`, sulabh/david/athira, deterministic rules engine on, N=1 per subject, no re-sampling). Confirmed every fired rule reaches the tagged prose: fired/surviving rule count and claim count matched 1:1 for all three subjects (sulabh 7/7, athira 7/7, david 6/6) with zero silent drops -- the direct proof that the S119 self-grounding consolidation and this session's migrations compose correctly end to end, not just at the engine layer. This run is what surfaced David's fate-line absence bug live, closed by `29ff43f` above.

**BEFORE / AFTER, stated plainly.** Session start (S122's own close-out figure, reconfirmed by this session's own pre-migration replays): **6 of 87 rules** fired on a real hand -- H_026, H_028 (Head), L_001 (Life), M_001/M_014/M_023 (Mounts) -- with **love (Heart) and destiny (Fate) at zero**, and Heart/Fate each honestly silent on every subject tried. Current HEAD: love, destiny AND head are all populated on real hands -- HL_001/HL_003 (Heart) fire on every draw on record, FT_003 (Fate) fires live, and H_002 joins Head's fired set on 6 of 6 draws, alongside the pre-existing H_026/H_028. Full suite at close: **3830 passed / 7 skipped / 0 failed** (`97bbd01`).

**THE ABSENCE-DOCTRINE FEASIBILITY STUDY, FEASIBLE BUT NOT WORTH IT.** Sulabh asked whether a genuinely-absent feature (David's missing fate line, going silent since the S125 fix above) should become a rule-authorable doctrine surface -- a Presence attribute, absence rules sourced from Cheiro. Traced first, not designed first: the feared pipeline blocker does not exist -- S119 self-grounding means a rule-sourced claim bypasses the retrieval support gate by construction, so nothing there needed to change. Parked anyway, on YIELD not RISK: an exhaustive sweep of all 579 Cheiro corpus chunks found only TWO cleanly authorable absence rules (Heart p160 "no line of heart -> not capable of deep affection"; Fate p165), against one conditional (Sun p170, gated on "an otherwise talented and artistic hand"), one already-parked feature (Health p171), and one inside the already-scoped-out palm-region-shape subsystem (Health/Triangle p204). Worse, only the Fate line has any live evidence vision can detect absence at all -- across 11 captured hands the Heart line was reported present every single time. One deliverable rule plus one speculative one does not justify a new registered attribute, a binding, and a regression-risky edit to the Fate line's already-shipped vision field. Two claims made in-session while scoping the fix turned out WRONG and are corrected on the record: registering a Presence attribute does NOT close HL_015 for free (it needs value "faded", which does not exist in the registry either, and Heart has never been reported faded on any captured hand), and does NOT resolve the Branching=absent mis-mapping automatically either (Branching would still legally accept "absent" globally unless separately bound). Both stay open, unchanged, as their own items. Revisit triggers, recorded not just implied: (a) a doctrine sweep across the other 21 corpus books surfaces enough further absence rules to amortise the infrastructure cost; (b) a live hand is ever captured showing a genuine Heart-line absence, making the second rule non-speculative.

**VERSION A SHIPPED (`9ce9028`): STATE A DEFINITE ABSENCE, STAY SILENT ON A CAN'T-TELL.** Sulabh's revised ruling did not reopen the parked doctrine question -- it separated it from a narrower, cheaper one: David's reading should say his fate line was not found, plainly, as an observation, with no doctrinal content and no hedging about photographs. The load-bearing scope rule is what makes this safe rather than noisy: "absent" is an unhedged, positive determination and gets a sentence; "not clearly visible", "not observed", "none", "unremarkable", "no clear marks" and "not visible" are can't-tell/visibility-hedged and stay silent exactly as before -- a flat photograph cannot show what a palmist would find by folding and tilting the hand, so uncertainty is honest silence, not a finding. Without that split the change would have appended a "markings/other features: not detected" sentence to essentially every reading produced -- that feature, not the fate line, is the one flagged genuinely-absent on 9 of the 9 captured hands available; the fate line is the rare case, one of nine. Rendered as a Python-templated paragraph appended after `_run_display_checks`, exactly the way the existing decline block already is, deliberately never routed through `claim_voicing` -- its own display guard is keyed on `unsupported_features`, which a genuinely-absent feature is never a member of, so it would have offered zero protection against the model embellishing an absence into doctrine. The same jurisdiction principle S119 already established for the two existing gate tuples was extended to this third one, so a feature can never be both stated absent and voiced by a firing rule claim in the same reading. Proven on all 9 captured runs, not assumed: exactly one statement produced, David's fate line; zero for markings/other features on any hand; the other 8 readings are a no-op by construction. 10 new tests, suite 3830 -> 3840.

**FILED, NOT FIXED: ABSENCE VOCABULARY LIVES IN THREE PLACES (`cbe02fe`).** Closing this arc surfaced the same drift shape that produced the SLOPE half-connected defect earlier in this session: the vision prompt's own English (`agent/palm_processor.py`), the runtime `_ABSENCE_VOCABULARY` tuple (`agent/interpretive/palm_reading.py`), and the test module's `_PROMPT_INVITED_ABSENCE_PHRASES` list are three separate places carrying the same vocabulary, inconsistent with `vision_flat_subfields`, which the SLOPE arc put in the registry for exactly this reason. Nothing is currently broken -- the S125 two-way sync test bridges the prompt and the test list, and the two runtime lists derive from one tuple -- so this was deliberately NOT moved to `ontology_registry.json` mid-arc: the feature is working, tested and guarded, and relocating vocabulary now is risk for zero behaviour change. Filed as CLAUDE.md's S123 open item (f) specifically so it is not discovered a third time and mistaken for a new finding.

**SESSION CLOSE, UPDATED.** Full suite at final close: **3840 passed / 7 skipped / 0 failed** (`cbe02fe`).

## S124

SESSION: ASTROLOGY RETRIEVAL ARCHITECTURE

DECISIONS RATIFIED (locked, do not revisit)
- Rule authoring is DEAD. No hand-authored doctrine rules. Fidelity moves from build time to run time.
- Retrieval IS in the citation path. The prior constraint forbidding this is formally retired.
- Retrieval unit = CHAPTER. Median 3,336 tokens. Notes/commentary stay attached to their verse.
- Citations are INTERNAL ONLY, for debug logs. Never shown to the user.
- Addressing = ORDINAL position (ch24_s001..sNNN), contiguous, no gaps. Printed verse numbers are metadata only: 35 of ch24's 144 are missing due to OCR, so they cannot be addresses.
- Printed PDF page numbers dropped entirely. page_ref is the internal key.
- Devanagari stripped from payloads, retained in storage. 37% real token cut, no quality loss (6-run A/B).
- Interpreter never quotes. It cites a location; the system fetches text.
- LLM never computes chart facts. One chart, one source, always.
- Filter fails SAFE: unparsed or untagged content is KEPT, never dropped.
- No answer skeletons, no priority/ranking tags, no relevance-ordered payloads. Ranking cannot be defined domain-free.
- Router will REASON about houses (including derived/bhavat-bhavam), not use a fixed domain-to-house table.
- 16-domain closed vocabulary is correct and locked: career, marriage, wealth, children, health, education, longevity, travel, property, parents, siblings, spirituality, enemies_conflict, timing_dasha, technique_method, planetary_nature.

ARTIFACTS BUILT
- data/chapter_index_bphs.json - 100 units, all 7 validation checks pass, zero character loss. Canary: bphs1_ch24 starts at page_ref 188.
- data/segment_index_bphs_career3.json v2 - 135 segments, ordinals, text_sha256 drift protection.
- data/career_payload_bphs.json - filtered career payload, 31.6% cut.
- data/domain_tags_bphs.json - 1129 segments, 100 units. SEE CAVEAT.
- agent/astro/payload_builder.py - generic payload builder (component).
- scripts/verify_claim_direction.py - direction-checking verifier.

MEASURED FACTS
- Zero genuine fabrications across all interpreter runs. Location-based citation was never beaten.
- Three separate times a "fabrication" was called and was WRONG - the tool or the diagnostic was at fault (Raja Yoga verse, 5th-lord-in-2nd, ch24_v25/v41). Check the tool before blaming the model.
- Relation filter cuts 31.6% within selected chapters, but only 4.6% across the whole book (242,571 -> 231,470). 46 of 69 splittable chapters yield ZERO lord-house relations; 76.3% of kept tokens arrive via fail-safe. It is a WITHIN-CHAPTER tool, not a selector.
- Domain tagging is reproducible: 8/8 probe units re-tagged blind returned identical domain sets.
- Unfittable rate 0.09% - the 16-domain vocabulary holds at scale.
- Temperature 0 + fixed seed did NOT produce identical OpenAI output. Some nondeterminism is inherent to the serving stack.
- Zero CONTRADICT findings across 3 clean OpenAI runs, but only ONE conclusion appeared in all three. Gist is directionally stable, thin on consistency.
- Reading corpus text costs ~9x source tokens due to Devanagari fragments. This constrains any future full re-read.

REJECTED APPROACHES (do not retry)
- Entity-level tagging (houses/planets as flat lists): kept 122/135, a 4% cut. Cannot narrow a placement census, because a chart matches exactly 12 of 144 cells and only the RELATIONSHIP identifies which.
- Priority/ranking tags: measured WORSE citation agreement than plain free-form (0.60 vs 0.625 Jaccard).
- Strict verbatim quoting: 73% failure, almost all cosmetic (case, curly quotes, model silently correcting OCR typos).
- TOC-based chapter detection: OCR-damaged; sequential walk works.
- Subagents as interpreters: tool access CANNOT be disabled in Claude Code, so context isolation is impossible and repo contamination is live. Cost 167k per run. Use OpenAI for interpreter runs.
- Parallel/multi-agent fan-out: 300k+ overruns. Sequential only.

OPEN ITEMS
1. data/domain_tags_bphs.json is PARTLY TITLE-INFERRED, not text-derived. Reading stopped after ~70 units. 61.9% of tags are low confidence (vs 14% when text was actually read). Career selection pulls 21.2% of the corpus (51,454 tokens) versus 4% on the properly-read subset. High-confidence tags are trustworthy; the rest need a text re-read before the router depends on them.
2. Router does not exist. Must output: domains (from the closed 16), houses (reasoned, including derived), whose-chart (self/other), and time scope. Must widen when uncertain, never narrow. Log every decision.
3. Silence gate does not exist. Verifier currently detects only.
4. Direction verifier catches reversed citations only where a relation was extracted. Partial coverage by design; do not chase the gap.
5. 16 of 74 calculation modules are stubs (vargas, vimshottari, yogas, shadbala, chart_d1 and others). Facts gate rules as hard as text does.
6. Two live bugs unfixed: "will my child succeed in his career" returns the USER's Shadbala; the out-of-scope guard matches by substring so any question naming the sign Cancer is refused as medical.
7. Only BPHS 1+2 is in scope. 11 other books untouched.
8. diagnostics/latest_run.md was overwrite-only and destroyed evidence twice. Now archived to diagnostics/runs/<timestamp>.md with a copy.


## S125 — Planner + Silence Gate built; five-stage pipeline PROVEN end to end; palm scope corrected; V1 order re-ratified (2026-09-05)

**POC VERDICT: PASSED.** The S124 five-stage architecture answered real questions end to end for the first time, without a hand-picked chapter list. Question -> plan -> chapters -> verses -> grounded, cited, chart-specific answer, with honest refusal where material runs out. Zero ghost citations in every run on record.

### BUILT (both uncommitted at session close — no ratification token was given)
- `agent/astro/planner.py` (`planner-1.0`) — the missing Stage 1. One LLM call emitting `{domains, houses, whose_chart, time_scope, in_scope, reasoning}`. Python validates SHAPE ONLY (house 1-12, domain in the closed 16, whose_chart/time_scope in their sets); it never judges doctrine, deliberately, so the domain->house table this architecture removed cannot creep back. Malformed -> ONE retry -> deterministic keyword fallback stamped `planner_fallback: true`, every decision appended to `diagnostics/planner_decisions.jsonl`. Fallback never guesses houses and refuses outright when nothing matches. `plan_and_build()` runs plan -> select_units -> build_payload -> filter_segments_by_domain.
- `agent/astro/silence_gate.py` (`silence-gate-1.0`) — Stage 5a. Deterministic, no LLM (Working Style #9). Drops a claim ONLY when the CLAIM'S OWN text states a lord-in-house condition that is readable, unambiguous, and positively false for the chart. Fail-open everywhere; any internal error ships the answer unmodified with the failure recorded.
- Tests: `tests/astro/test_planner.py` (41) + `tests/astro/test_silence_gate.py` (51) = **92 passing, 0 failed**. These are ADDITIVE to the 3,840-test suite, which was not re-run this session.

### BOTH S124 LIVE BUGS ARE CLOSED BY CONSTRUCTION
- "will my child succeed in his career" -> `whose_chart: other`, houses `[5, 2, 10]`, the 2nd being the 10th-from-the-5th. No second birth record needed, ever.
- the "Cancer = medical" substring guard -> **there is no substring guard anywhere**. `in_scope` is the planner's judgement; Python only checks it is a boolean. A test asserts the constructs `_OUT_OF_SCOPE` / `OUT_OF_SCOPE_KEYWORDS` / `_MEDICAL` cannot be reintroduced.

### MEASURED — do not re-derive
1. **S124 open item 1 was FALSE and is CLOSED.** `domain_tags_bphs.json` is NOT partly title-inferred. ZERO of 100 units. Every unit was tagged from real corpus text at one of three read depths. No re-read budget is needed; the audit that proved it is `diagnostics/runs/20260905T101738Z_audit_tag_coverage.md`.
2. **`approx_tokens` undercounts the real tokeniser by 1.61-1.66x**, measured against real OpenAI `prompt_tokens` (48,589 -> 80,882; 12,864 -> 20,736; 91,418 -> 152,542). A chars/4 estimate is itself ~17% low on this corpus. NEVER size a payload from `approx_tokens` or chars/4 again — only from `prompt_tokens`.
3. **gpt-4o TPM cap is 30,000 at this account tier.** A 68,342-token request was rejected 429 pre-billing. The cap binds long before the 128k context window does. Tier-specific; a tier upgrade changes it with no code change.
4. **Unit-level selection ships 37-48% of the corpus**; stacking the per-segment domain tags cuts a further 22-46% (career 90,653 -> 48,589 approx-tokens). Segment ids in `domain_tags_bphs.json` and `payload_builder` resolve 1,129/1,129 — one id scheme, no bridging needed.
5. **WIDE IS DEAD for house-shaped questions.** Career, ARM A vs ARM B: dropping 298 of 304 segments changed gpt-4o-mini's citation set by NOTHING, and the smaller payload cleared the TPM cap so gpt-4o could run at all — producing the better answer (2 claims, a real verse citation, a specific reading). The fail-safe segments contributed ZERO citations.
6. **STRICT IS DEAD for timing questions.** "When will I get married": 336 of 350 kept segments (96%) have zero extractable relations. **14 is the hard ceiling** on what a house-keyed filter can EVER keep, at ANY house list — measured across `[7]`, `[7,2,11]`, `[7,2,11,8]` and all 12 houses (2 / 9 / 9 / 14 segments). The planner's thin `[7]` cost 7 segments; the filter's design costs 336. Off by a factor of 48.
7. **Only 3 of 10 subjects land in a workable band today** (>=6 segments, under the TPM cap): career, children, health. Over TPM: wealth, marriage — both fixed by a tier upgrade, not by code. Too thin: education, property, siblings, travel, spirituality. ROOT CAUSE: `extract_relations` recognises essentially one sentence shape, so 90-95% of verses are invisible to it in every domain.
8. **gpt-4o-mini never cites a verse.** Across every mini arm on record it cited only whole-chapter units; `domain_match` count zero. gpt-4o is the only model that cited real segments. Every mini-only result is a weaker signal than it appeared.
9. **gpt-4o refuses correctly where mini invents.** Given 2 thin segments on a timing question, gpt-4o produced 0 claims and said the material could not answer it; mini produced 3 Barnum claims from the same input. More claims was never the goal.
10. **The precondition-mismatch defect, quantified.** 3 of 12 shipped claims in the live three-domain run recite doctrine whose "if" clause is false for this chart ("if the 12th lord is in the ascendant" — chart has 12th->6th; "5th lord in the 5th"/"in the 6th" — chart has 5th->2nd). Correctly cited, correctly quoted, not about this person. SAME defect class as the `p139_c0` finding that reversed the T4 palm ratification at S71.
11. **The silence gate, replayed on those 12 real claims: 3 dropped, 9 kept, zero false drops.** Coverage varies hard by question — health 100% judged, career 50%, children 38%. The gate REPORTS its own `ungated_pct` on every answer so a human always knows how much was actually checked.

### THE SILENCE GATE'S OWN NEAR-MISS — recorded because the lesson generalises
`silence-gate-1.0`'s first implementation reused `payload_builder.extract_relations`. An adversarial review pass reproduced **six classes of WRONG DROP** on ordinary interpreter prose: negation ("NOT in the 5th" read as "in the 5th"), cross-sentence bridging (the 200-char DOTALL window inventing a relation from two unrelated sentences), missed disjunctions ("in the 9th or the 2nd" reading only the first), foreign reference frames ("from the Moon", navamsa, D-10, Arudha, transits all judged against the ascendant map), indirect attribution ("aspected by Jupiter in the 9th" — the 9th belongs to Jupiter), and bare numerals ("the 2 charts examined" read as the 2nd house).

**ROOT CAUSE, and it is a doctrine mismatch rather than a bug:** `extract_relations` is a RETRIEVAL filter, deliberately permissive because over-matching there merely keeps extra text (fail-safe). As a precision judge, an over-match SILENCES A TRUE CLAIM — invisible in production. **A permissive matcher can never be a precision judge.** Fixed by replacing it with a purpose-built strict reader that works one sentence at a time and refuses to judge at the first sign of negation, alternatives, another reference frame, indirect attribution, dasha phrasing, or a compound condition. All six are now locked regression tests.

### DECISIONS RATIFIED (do not re-litigate)
- **PALM IS IN V1 and is BUILT.** Reverses the S71 "V1 PALM DROPPED" Option-Z lock, which is now stamped SUPERSEDED in CLAUDE.md (entry preserved; its technical content about GPT-4o-mini's limits on hedged classical prose remains valid and is what the two-stage extract-then-voice architecture answers).
- **The S124 five-stage pipeline is the FINAL answer architecture.** The old S23 "no LLM-synthesised answer text" lock does not survive it; the deterministic calc domains become the fact block the Interpreter reads.
- **V1 ORDER, re-ratified by Sulabh at session close: SELECTION FIRST, calculations after.** The 16 calculation stubs are stubs *because those calculations were hard to get right* — each carries the 4-reference-chart validation protocol and will take a long time. Selection is a one-file problem gating 7 of 10 subjects today. Doing the slow item first leaves most of the corpus unreachable for months.
- **`calc_router.py` was deliberately NOT used as the planner's fallback.** It emits CALCULATION domains (`current_dasha`, `muhurta_window`...), a different output type in a different stage; mapping it onto the 16 TEXT domains would be a fresh hardcoded table — exactly what this architecture removed. It is untouched and continues to serve Track A.

### CORRECTIONS MADE ON THE RECORD
- **PALM IS COMPLETE FOR V1 SCOPE — an in-session claim to the contrary was WRONG and is retracted.** Sun / Health / Mars / Marks / hand-types / fingers / thumb / nails were read off S95's forward-looking list and called "remaining chapters". **S96 formally scoped them out**, per-configuration reasons recorded in `data/palm_rules/unauthorable_register.json` (marks and signs, hand-type family, two-hand laterality, and the whole p136-139 Influence-ray subsystem — "not emission-reachable" or outside the Cheiro-Western core). Marriage lines PARKED (no vision emitter block exists — architecturally unmeasurable). Thumb PARKED (S123, same relative-judgement class as the dead `proximity_degree` axis). The four live rule files — `head_heart`, `life_line`, `fate_line`, `mounts` — ARE the V1 palm scope. **The register exists precisely so closed questions are not re-litigated. This session re-litigated one.**
- **CLAUDE.md's duplicate S72 palm-UI-gate entry resolved by grep, not argument.** `_PALM_ENABLED` EXISTS at `frontend/app.py:47` and gates 4 UI render blocks (868, 889, 1259, 1440). The "PLANNED, NOT YET IMPLEMENTED" twin is stamped STALE in place (supersede-don't-delete).
- **`ASTRO AGENT — MASTER BUILD PLAN.md` REWRITTEN.** The prior version was frozen at **Session 42-44** — it named V1 as "3-domain deterministic calc Q&A", carried the S23 no-LLM-text lock, and contained no mention of the palm rules engine or the BPHS text pipeline. It described a system that no longer exists. Replaced with a three-track map (calculations / palm / BPHS text) through V2, with every open decision carrying its gate. `SESSION_5_PLAN.md` and `claude_handover_S97.md` reduced to one-paragraph tombstones — a stale handover is worse than none, because it is confidently wrong.
- **A verification whose expected value was invented buys nothing (Working Style #16, violated in-session).** A prompt asked Claude Code to `grep -c HARD_CONTEXT_CEILING` and "expect 4". The true count is 3, in BOTH the old and new versions of the file — so the check could never have discriminated. The value, not the count, is the discriminating grep. Chasing it did surface a real problem: repeated writes to `agent/astro/planner.py` were reverted between commits (twice observed). **Cause unknown, not investigated — flag for the next session if it recurs.**

### CARRY-FORWARD, OPEN
1. **SELECTION is the next arc and the only V1 blocker of its size.** Broaden the relevance signal beyond the single lord-in-house sentence shape. **FLAG, recorded not buried:** selection can only be MEASURED on the eight non-timing subjects, because `timing_dasha` material cannot be validated until `vimshottari` exists. MITIGATION, to be built INTO the selection arc rather than deferred — design the timing relevance signal (planet and period names, NOT houses) now, ship it unmeasured, validate the day `vimshottari` lands. Do NOT leave `timing_dasha` out of the selection design because it cannot yet be tested.
2. **Planner + silence gate are UNCOMMITTED.** Both built, both tested, awaiting a ratification token.
3. **The silence gate is a scalpel, not a net.** It judges only the plain "the Nth lord is in the Mth" sentence. Dasha, conjunction and aspect claims pass through unjudged — not because the gate is weak, but because the fact block holds only 12 lord placements and an ascendant. Each calculation stub closed widens gate coverage with NO new gate code.
4. **16 calculation stubs, 1,087 bytes total, all docstring-only** — `vimshottari` (gates every "when" question), `chart_d1` (gates the fact block), `yogas/detector` + 4 catalogs, `shadbala` roll-up, `vargas/divisional`, `vimshopaka`, 3 more dashas, `varshaphal`/`muntha`/`sahams`. **Closing these retires AstroSage as a side effect** — the PDF exists only because the engine cannot compute these yet.
5. The planner's live house lists run thin (`[7]` for a marriage-timing question). A widening instruction was added to `SYSTEM_PROMPT`; its effect is UNMEASURED — the first run that would have tested it used a stale copy of the file.
6. Repeated silent reverts of `agent/astro/planner.py` between writes — see the correction above.


## S126 — Answer pipeline complete end-to-end; interpreter locked to gpt-5; selection reconciled to the locked 16 domains; Fix1 timing-tag cleanup (2026-09-11)

DESIGN-CHAT session (Cowork). Executed directly against the working tree via the device bridge; the GPT validation ran on Sulabh's machine (the Cowork sandbox is firewalled from api.openai.com by egress policy). Suite after the session's commit: **3938 passed, 7 skipped, 0 failed** (`diagnostics/latest_run.md`).

### BUILT + COMMITTED (S126)
- `agent/astro/interpreter.py` (`interpreter-1.0`) — Stage 4. Emits STRUCTURED claims `{statement, segment_ids}` (so the silence gate can judge each claim's precondition), corpus-first prompt (verse block leads the system message = cacheable prefix), GHOST GUARD (any cited id not in the payload is stripped; a claim left with no real id is dropped, so the gate never sees a ghost id), `reasoning_effort=minimal`, dependency-injected `llm` for stub tests. Model locked `gpt-5`.
- `agent/astro/pipeline.py` (`pipeline-1.0`) — `answer_question`: plan → select_units → build_payload → filter_segments_by_domain → interpret → apply_silence_gate → rendered answer. Builds the FACT BLOCK from the chart's lord→house map + ascendant. Fails open / refuses with the reason on record; never raises for a model/gate problem.
- `tests/astro/test_interpreter.py` (6) + `tests/astro/test_pipeline.py` (2) — stub-llm, no API. End-to-end proof: a true-precondition claim kept, a false-precondition claim dropped by the gate, a ghost id stripped.
- `agent/astro/planner.py` config: `INTERPRETER_CONTEXT_WINDOW` 128_000→400_000, `HARD_CONTEXT_CEILING` 72_000→225_000 (= (400k real − ~15k output/reasoning reserve) / 1.70 approx-ratio).
- `data/domain_tags_bphs.json` — Fix 1 (below).
- planner.py + silence_gate.py (built S125, previously uncommitted) landed in the same commit under a ratification token.

### FIX 1 — timing-tag pollution removed (data-only; the ONE tagging fix that survived)
`timing_dasha` was wrongly co-tagged on machinery and out-of-scope material. Dropped it from: `bphs2_ch46` (the dasha COMPUTATION manual → now `technique_method` only) and `bphs2_ch61/62/63` (Effects of Pratyantar/Sookshma/Prana dashas — the SUPPRESSED sub-dasha levels, ±37-day drift lock). Result: `timing_dasha` 252→38 segs (−36% of the domain was pollution); the "when will I marry" payload fell 158k→113k real tokens with ZERO doctrine dropped, because every removed segment was computation or a suppressed level. All 1,129 segments preserved; unit `per_domain` rollups recomputed.

### MODEL — gpt-4o → gpt-5 (VALIDATED on real calls, do not re-derive)
Validation (`scripts/validate_model.py`, run on Sulabh's machine 2026-09-10, real gpt-5): 4 real questions + 1 out-of-scope.
- **0 ghost citations on every question** — every cited id exists in the payload. (career 6 real cites, wealth 7, property 4.)
- **Honest refusal on "when will I marry"** — gpt-5 walked the marriage-timing yogas, ruled out the ones that don't fit the chart, and refused to give an age because the FACT BLOCK lacks planet positions (only lord→house today). This is the correct behaviour AND the concrete proof that timing needs `vimshottari`/`chart_d1`.
- **Recall held at 99k–105k prompt tokens** (no degradation). The account cleared 105k with **no 429**, so gpt-5's TPM headroom is far above gpt-4o's 30k — the TPM wall is effectively gone on gpt-5.
- **Cost ~$0.16 per big question** at `reasoning_effort=minimal` (reasoning ran ~2k–5.7k tokens, higher than the "~0.6k" estimate, but the payload is input-dominated ~82k:1.2k so it stays cheaper than gpt-4o's $0.22 and far cheaper cached).
- gpt-5 fits EVERY question (max wealth_timing ~149k real) in ONE 400k-window call — no split, no narrowing, no doctrine dropped.

Model comparison (live 2026 pricing, third-party, [Likely]): gpt-4o $2.50/$10, 128k, FAILS big+timing (over window); **gpt-5 $1.25/$10 cached $0.125, 400k — chosen**; GPT-5.6 Terra $2.50/$15, 1M, 89.6% recall (safety net, unused); GPT-5.6 Luna/mini **REJECTED — 41.3% long-context recall = cites wrong verses (the S125 mini-trap, benchmark-confirmed)**. Caching is automatic, ~24h TTL, 90% off the repeated prefix — keep the user-independent verse block as the prompt PREFIX.

### DECISIONS RATIFIED (do not re-litigate)
- **Interpreter model = gpt-5** (config in planner.py). `reasoning_effort=minimal`, corpus-first prompt.
- **Selection speaks ONLY the locked 16-domain vocabulary** (S124). No topic/rule_type/facet axis was adopted. The planner emits `domains` (which it already did) + the `time_scope` it already emits; selection is `filter_segments_by_domain` + the within-chapter relation funnel (demoting the funnel was TESTED and REJECTED — it only enlarges payloads).
- **Standing cost/correctness doctrine: never narrow, never fail-open to silence doctrine.** Window overflow is solved by the 400k model (lossless); TPM by account tier (money). Sub-tagging / a per-query LLM filter were considered and rejected as narrowing judges (a wrong drop silences a true claim).

### CORRECTIONS ON THE RECORD (mistakes made and reversed this session — read before repeating)
- **Anchored the whole first design on a REJECTED artifact.** Built a topic + `rule_type` tag layer on top of `segment_tags_bphs_career3.json` (segtag-2.0), and invented a `property_home` topic. Both wrong: S124 locks the 16 domains as the vocabulary (`property` is already in it), and S124 REJECTED entity-level (houses/planets) tagging. Sulabh caught it ("why segtag/property_home as external?… we decided not to design based on rule… read the log"). Retracted; `topic_select.py` and the topic-tag experiment are NOT part of the design. **Lesson: check the locked vocabulary and the REJECTED-APPROACHES list before proposing a new tagging axis.**
- **`rule_type` (single or multi-valued) was scope creep** on the axis we agreed to keep backstage. The timing-vs-machinery distinction it was meant to carry is already carried by the 16 domains (`technique_method` = machinery, `timing_dasha` = timing). Dropped.

### CARRY-FORWARD / NEXT (see claude_handover_S126.md)
1. **`vimshottari` + `chart_d1` calc stubs** — the immediate next work. They widen the FACT BLOCK beyond lord→house (planet positions + running dasha), which is exactly what gpt-5's honest timing-refusal proved is missing. Unlocks all "when" questions and retires AstroSage. Each carries the 4-reference-chart validation protocol.
2. **Vision / palm track** — Sulabh flagged starting the vision work in the next session (palm is already COMPLETE for V1 scope per S125; this is new vision work, scope to be defined next session).
3. The silence gate stays a scalpel (judges only plain lord-in-house claims) until the fact block grows; each calc stub widens its coverage with no new gate code.
4. **`parked_cost_reduction` SUPERSEDED + removed from the project (S126).** Its top lever (gpt-4o-mini interpreter) is REJECTED by the model validation (41.3% long-context recall); its prompt-caching idea is ADOPTED (gpt-5 auto 90% cache); the cost it targeted is already ~$0.16/big-Q (~$0.03 cached), nothing refuses over ceiling. Only unbuilt remnant: cache the interpreter ANSWER for chart-independent questions — LOW priority, not gating anything.

### S126 close addendum — branch hygiene + sync (2026-09-12)
- **`main` is stale at S84; `wip/interpretive-pilot` is the trunk** (deliberate since the ~S90 pivot; workflow = commit/push/pull on wip). Verified: wip is 214 commits ahead, main 0 ahead, FF-safe (main is an ancestor). DO NOT build on main — it starts from S84 and silently drops the whole pipeline. Confirm `git branch --show-current` == wip/interpretive-pilot before any work.
- **a0569b0 (pushed) — tracked 12 accidentally-untracked LOAD-BEARING files** the committed pipeline imports/reads: `agent/astro/payload_builder.py`, `agent/astro/__init__.py`, `tests/astro/__init__.py`, `data/chapter_index_bphs.json`, `data/career_payload_bphs.json`, + 7 build/validate scripts. Before this, committed code imported an untracked module → a clean clone would ImportError; the 3938-pass suite only worked on local working-tree files. `wip` now clones clean (3938 pass). The S90 "untracked = only diagnostics/scripts/probes" invariant had silently broken; restored. `segment_index/tags_career3.json` stay untracked (no committed code reads them).
- **OPEN — RAG/sync staleness (Sulabh action, project settings):** the project's GitHub sync points at `main`, so the project RAG serves S84-era content. FIX: repoint the sync branch `main` → `wip/interpretive-pilot`. Until then, a new session's RAG is 42 sessions stale — trust CLAUDE.md + SESSION_LOG + the handover over RAG hits. A `main`→`wip` FF-merge was considered and REJECTED: wip is the deliberate trunk, repointing the sync is the root-cause fix; merging would re-diverge on the next wip commit.

### S126 → S127 build-guidance CORRECTION (2026-09-12, verified vs archives; supersedes optimistic handover phrasing)
A fresh session (Output.txt) read `main`/S84 and correctly refused to build on unverifiable state. Its stub findings are VERIFIED here and correct three overclaims:
- **`vimshottari` unlocks RANGE-level "when", NOT day-precise dates.** Gap D1 (S75/S76, `docs/KNOWN_DIVERGENCES.md`): row-0 (MD-1 end) residual vs Drik −0.33 to −2.66d, non-linear/seasonal → apparent-Moon convention divergence. RATIFIED accepted gap: range answers unaffected, day-precision EXCLUDED from V1. MD/AD logic already lives in `agent/chart_calculator.py` (S44 "import the real logic, do not touch the stub"); building the stub = extract/wire WITH regression coverage first, not greenfield.
- **`chart_d1` stub is DELIBERATE** (P1.1/P1.4 Chart-dataclass refactor aborted S22/S24 — consumers take primitives). `chart_calculator.calculate_chart()` is the production D1 path with ZERO regression coverage; computes per-planet sidereal longitudes internally but its public dict exposes sign/house/dignity/retrograde, NOT raw longitudes. To surface positions: add regression tests to the production path FIRST (HARDEST-CASE-FIRST), then expose longitudes — do NOT rewrite the stub.
- **AstroSage STAYS in V1.** Ratified S68 ("AstroSage PDF stays V1, no replacement scoped"). The S125 "retire AstroSage as a side effect" was an ASPIRATION, not a ratified decision — corrected. Removal contingent on the engine demonstrably covering AstroSage outputs.
- **For any session that can't see S126:** the S126 code is on `wip/interpretive-pilot` @ `a0569b0` (pushed), NOT `main` (stale S84). Reconcile against `wip`, never `main`.

## S127 — chart_d1 longitude surfacing + 4-chart oracle reconciliation + verification-gate rules

**Shipped (committed):**
- 1a `53b90f3`: David characterization regression test for calculate_chart() public D1 fields (sign/house/dignity/retrograde + lagna, 16 fields). Drift-guard, NOT an oracle. CAVEAT: per-planet dignity has no oracle table -- characterization only.
- 1b `a65cb4c`: surfaced per-planet sidereal `longitude` in calculate_chart() public output (additive; value was computed internally and discarded -- no new ephemeris call). Extended the David test with 9 longitude asserts (1e-6 deg drift tol). Suite 3954->3963.
- oracle `25dd869`: reference/oracle_fixtures/{david,sheridan,sulabh,surbhi}.md -- matched-mode section 3e (JHora Traditional Lahiri) as ratified D1 oracle.

**Key findings:**
- Prior JHora D1 captures (3b/3c) were **True-Chitrapaksha mode, not Traditional Lahiri** -- mode contamination, same class as the ayanamsa boilerplate bug. Corrected; True-Chitra tables tagged, retained for provenance.
- Matched-mode residual (production vs JHora Trad-Lahiri) = documented **Camp-Y apparent-position gap** (Gap A1): max ~54" (Surbhi Mercury), 30.7" David, 44.2" Sheridan. Sun ~ -20" on all four = annual aberration signature. Rahu/Ketu ~ -0.14" = Mean-node match, no flip. NOT drift.
- Ratifications propagated (corrected: **S75**, not S72): Gap O1/O2/O3.
- Data-flag closures: Surbhi Moon = **Shatabhisha** (S74 "U-Bhadrapada #24" mislabel corrected); Surbhi Mercury(~3.6 deg)+Jupiter(~4.98 deg) **combust** (S51 "none" Basics-view invalidated); Surbhi Jupiter 29 deg 56' Leo **boundary-sensitive** flagged. Surbhi Ashtakavarga sentinel cells collapse to one (Moon-Virgo).

**Process (CLAUDE.md rules 32-34 added):** root-caused this session's own misdirections -- calling the dasha/chart_d1 stubs a "stalled refactor," an already-documented Parasara/Varahamihira divergence a "new finding," mislabeling S75 as S72, reinventing rule-26's run-archive as per-person manifests. Single cause: **asserting from memory/summary before reading an available primary source.** Rules 32 (summaries!=authority), 33 (DESIGN-INTENT-FIRST binds the design chat), 34 (design chat reads what it can) added.

**Recon (mapped, not built):** fact-block flow = pipeline._fact_block() renders ONLY lord_house_map + ascendant. Silence-gate **fails open** (non-relation claims -> UNDETERMINED -> kept). Widening with dasha/longitude is NOT gate-blocked but ships UNVERIFIED. chart_facts construction point NOT yet located.

**NEXT:** fact-block widening -- chart_d1 position FIRST (restate-don't-compute, low risk), dasha DEFERRED until the gate can range-verify. Start with the S127 recon prompt (locate chart_facts construction; confirm gate fail-open on live tree; propose longitude wiring). Parked: PVR Ashtakavarga hand-computation cells (David/Sheridan).

## S129 — Path B cutover: app.py rewired, capability gate, fact block widened to planet positions, QA capture + user-facing answer view, advisory planet reader, replay harness, Saturn oracle slip resolved (2026-09-12)

> NOTE ON THE GAP: this file jumps S127 -> S129. **S128 was never logged here.** S128's
> work is recorded only in `claude_handover_S126.md`-style handover text and in the
> S128 lock at `CLAUDE.md:17` (now stamped SUPERSEDED). Do not infer S128 content from
> this entry — it is not a summary of S128.

OUTCOME: the Streamlit app now answers through the five-stage Path B pipeline. Coverage is
narrow and DELIBERATELY so — what the fact block cannot support, the app declines in plain
language instead of inventing. AstroSage PDF stays as the covering surface (S125 V1 order).

**BRANCH:** `wip/interpretive-pilot`. Written to disk uncommitted; SHA assigned at Sulabh's
commit — this entry names no SHA because none existed when it was written (CODE-READ
PROVENANCE).

**THE CUTOVER (the decision):**
Two answer paths had been derailing sessions. Path A (`agent/infra/orchestrator`) assembles
fixed templates and opens no book — it can never produce the objective's grounded, cited,
chart-specific answer. Path B (`agent/astro/*`) is Planner -> Calculator -> Retriever ->
Interpreter -> Verifier. Sulabh ratified **everything to B**. `frontend/app.py` now imports
`answer_question` from `agent.astro.pipeline`, `build_chart_facts` from
`agent.astro.chart_facts`, `render_user_answer` from `agent.astro.answer_view`, and
`agent.astro.qa_capture`. Path A is RETAINED, tested, intact as the revert target, and wired
to nothing. Its known defects are left unfixed BY DECISION.

**BUILT (new modules):**
- `agent/astro/chart_facts.py` — the adapter that did not exist. Restates
  `calculate_chart()` output into `{lord_house_map, ascendant_sign, planet_positions}`.
  **Computes nothing. Fails closed on any partial map.** Emits house + sign ONLY —
  no dignity (no oracle table to validate it), no longitude (no verse keys on a degree),
  no retrograde (three recorded grounds). `_GRAHA_ORDER` is classical, for byte-stable
  rendering. 12/12 against the JHora oracle for Sulabh.
- `agent/astro/capability_gate.py` — Stage 1.5, deterministic, NO LLM, sits between
  planning and retrieval. Declines any question needing facts the block does not carry.
  `FACT_BLOCK_PROVIDES = {ascendant_sign, lord_house_map, planet_positions}`. ONE
  requirement today: `dasha_timing` (domain `timing_dasha` OR `time_scope in
  {future, specific_period}`). **This is what makes a narrow fact block SAFE rather than
  merely narrow** — the silence gate only judges "Nth lord in the Mth" and FAILS OPEN, so
  a dated claim would otherwise ship unverified (Working Style #5).
- `agent/astro/qa_capture.py` — per-launch `diagnostics/qa_capture/<UTC>.md`, appended per
  turn. Records question, chart_facts, BOTH plans (pre- and post-gate), gate verdict,
  selection + payload, interpreter usage + ghost ids, silence-gate stats, **full
  untruncated cited verse text with char counts**, per-stage timings, the user answer AND
  the pipeline render separately, raw interpreter JSON. Never raises. Gitignored (holds a
  real chart).
- `agent/astro/answer_view.py` — the user surface. Strips `[ids]`, drops `silent_on`,
  swaps "the native" -> "you", appends a chapter-level source line. **Deliberately does
  NOT rewrite claim text** — rewriting is where a verified claim becomes an unverified one.
  Title guard at 60 chars / sentence punctuation because 20 of 100 chapter `title_raw`
  values are OCR run-on sentences.
- `scripts/replay_capture.py` — zero-API-cost replay: payload rebuild -> stored raw
  response -> silence gate -> advisory -> answer_view -> diff. `CapturedTurn.user_answer_source`
  distinguishes `answer_view` from `legacy_pipeline_render` so old captures are not
  spuriously diffed.

**MODIFIED:**
- `pipeline.py` v1.0 -> v1.2: gate wired in, `_lap()` per-stage timings, `trace` dict
  (`plan_before_gate`, `gate_refused_outright`, `payload`, `interpreter_raw`, `gate_error`),
  `_fact_block` renders planet positions.
- `planner.py`: `plan_and_build` split into `plan_question` + `build_from_plan(...)`.
  Behaviour-neutral; `plan_and_build` unchanged for every existing caller.
- `interpreter.py`: VOICE block in `_SYSTEM_HEAD` — address the user directly, NEVER write
  "the native", ban kendra/trikona/dispositor/Navamsa/Atmakaraka etc., `silent_on` labelled
  INTERNAL. Added `reasoning_effort_requested`/`_applied` to usage so the `except TypeError`
  fallback cannot silently drop the param.
- `silence_gate.py`: new **ADVISORY** planet reader (`read_planet_condition`,
  `judge_planet_claim`). Records verdicts, **has no drop authority**. A sentence matching
  both readers returns `None` (ambiguity rule). New stats incl. the promotion metric
  `advisory_would_drop_a_kept_claim`.
- `agent/calculations/core/chart_d1.py`: docstring rewritten to open
  "THIS STUB IS DELIBERATE AND PERMANENT. DO NOT IMPLEMENT IT" with the verbatim S22/S24
  abort quote.
- `docs/ANSWER_PATHS.md`: rewritten — records the cutover, the gate, the pratyantar debt,
  Path A's retained-but-unwired status and its known defects.
- `CLAUDE.md`: S129 Path B lock added; S128 lock stamped SUPERSEDED; chart_d1 added to the
  DESIGN-INTENT-FIRST known-intentional list.
- `diagnostics/KNOWN_PATTERNS.md`: row **P-022** for the chart_d1 confusion.

**FACT-BLOCK GROWTH CONTRACT (enforced by test):** widening `pipeline._fact_block` REQUIRES
adding the matching key to `capability_gate.FACT_BLOCK_PROVIDES` in the SAME change.

**PRATYANTAR:** still unhooked on Path B. The fact block carries no dasha, so today's safety
is **ABSENCE, not a guard**. Whoever adds dasha to the block MUST add the suppression in
that same change (±37d drift, wrong lord).

**MEASURED BEFORE BUILDING:** 344 planet-in-house vs 176 lord-in-house corpus sentences,
94.5% judgeable. Retrograde-keyed verses = 10/20,426 (0.05%) — the ground for omitting
retrograde from the fact block.

**SATURN "(R)" ORACLE CONFLICT — RESOLVED from primary sources.**
Cross-chart retrograde census (4 charts x 7 grahas): 8 `(R)` marks, 7 agreed with recomputed
pyswisseph speeds. Only `sulabh` Saturn disagreed — production says direct at
**+0.008719 deg/day**. Decisive evidence is inside `sulabh.md` itself: its raw JHora
Traditional-Lahiri export prints `Saturn - BK   8 Sg 50' 14.60"  Mool  3  Sg  Ge` with **no
(R)**, and that value is EXACTLY the section-3e row's value — so that line is provably the
row's source. The other three fixtures print retrograde Saturns as `Saturn (R) - PK ...` in
the identical format, so the marker is not being dropped by the export. VERDICT: a
**transcription slip** when the 3e table was hand-typed. Not a JHora convention, not a
pyswisseph bug. Near-station is ruled out — `david` Mars at -0.012495 deg/day is nearly as
slow as Sulabh's Saturn and flags correctly. `sulabh.md` corrected (`(R)` removed, marked,
correction note retaining the superseded sentence); `docs/PROJECT_FACTS.md` RESOLVED entry
supersedes the UNRESOLVED one. **Census is now 8/8. No JHora check is needed from Sulabh.**

**COST DISCIPLINE (new, at Sulabh's instruction):** live dogfood runs burn real OpenAI
credit. A live run is now required ONLY when (1) the interpreter prompt changed, (2) the
fact block gained a new fact class, (3) model/config changed, (4) something is being
ratified. Everything else replays through `scripts/replay_capture.py` at zero API cost.
**The sandbox is FIREWALLED from api.openai.com — live runs happen only on Sulabh's machine.**

**FROZEN FIXTURE:** `tests/fixtures/qa_captures/s129_live_gpt5_20260912T160015Z.md` — the
real 2026-09-12 gpt-5 run. Costs a live run to recreate; do not delete.

**VERIFIED:** 4 reference charts x 7 question shapes x 2 interpreter modes = 56/56 no
exception, real retrieval, 21k-67k approx-token payloads. Suite 3939 -> 3982 passed, same 9
pre-existing key/corpus-dependent failures. Post-Saturn: 123 passed across `tests/astro` +
`tests/regression`.

**MY OWN ERRORS THIS SESSION (root-caused, not just listed):**
- Called `ch34_s011` a mis-citation — **for the second time across sessions**. Cause: printed
  `s["text"][:460]` of a 5,396-char segment; the Raja Yoga verse sits at ~char 1,800. It is
  5/5 faithful. FIX: `qa_capture` now stores full untruncated verse text with char counts,
  so truncation can no longer masquerade as a mis-citation.
- Fabricated Surbhi's birth data ("14 Oct 1992, Delhi"). Real: **11 Sep 1992, 10:30, Patna**.
  Caught by oracle mismatch. Corrected and re-run.
- Handed Sulabh a Claude Code prompt instead of doing the work myself. Corrected — I have
  the access; I do the coding.
- Asked Sulabh to check JHora when the answer was inside `sulabh.md`. Corrected by running
  the census myself. **Same root cause as rules 32-34: reaching for a human before reading
  an available primary source.**

**NEXT:**
1. Sulabh's stress test with the widened fact block (qualifies as a REQUIRED live run —
   planet positions are new to the model).
2. Promote or hold the advisory planet reader on `advisory_would_drop_a_kept_claim` from
   that run. Do NOT promote on intuition.
3. Deferred/owed: aspects + conjunctions (Q1 option c); `vimshottari` + pratyantar hook;
   architect's refactor (`pipeline._fact_block` still calls `payload_builder.parse_lord_house_map`);
   stale MASTER BUILD PLAN (~13 lines); cost-constraint re-ratification ($0.01 ratified vs
   measured ~$0.19 / 75s); **`main` is stale at S84, so project RAG is ~45 sessions behind.**


## S130 — reasoning_effort was never reaching the API; fact block widened 4 ways (house_lords, aspects, dignity head, navamsa); ghost citations root-caused (2026-09-13)

**BRANCH:** `wip/interpretive-pilot`, on top of `c0d6c70`. Written to disk UNCOMMITTED;
SHA assigned at Sulabh's commit — this entry names none because none existed when it was
written (CODE-READ PROVENANCE).

**HEADLINE:** three things this project believed were missing or blocked turned out to be
already built and merely unwired, and the reason each was 'blocked' did not survive being
checked against its own cited source. Rows P-024 and P-025 exist so this stops recurring.

### 1. `reasoning_effort` NEVER REACHED THE API (P-023, FIXED)
`interpreter._default_llm` passed `reasoning_effort` as a NAMED kwarg and, on `TypeError`,
retried WITHOUT the parameter. On an SDK whose `chat.completions.create` signature predates
that kwarg, the drop path ran on EVERY call. Measured 7/7 turns in
`diagnostics/qa_capture/20260913T040439Z.md`: `reasoning_effort_applied=false`, 3,328-8,384
reasoning tokens, 50-58s interpreter stages. FIX: the TypeError path now retries via
`extra_body={"reasoning_effort": ...}`, which reaches the API on any SDK version; only an
API-side refusal drops it, and `usage.reasoning_effort_path` records which of the three
paths ran. MEASURED AFTER (`20260913T051158Z.md`, same Saturn question):
`path=extra_body`, reasoning_tokens **8384 -> 0**, interpreter **50.51s -> 21.07s**,
total **55.51s -> 24.37s**. STANDING LESSON: a TypeError on a named kwarg means the SDK
SIGNATURE is old, NOT that the API rejects the parameter. Never conflate the two.

### 2. FACT BLOCK WIDENED FOUR WAYS — all pure restatement
Every key below was ALREADY produced by `calculate_chart()` and simply not restated by the
adapter. No calculation was added anywhere; `chart_calculator.py` is untouched.
- **`house_lords`** — `house_lord_mapping` rows carry `house/sign/lord/lord_in_house`; the
  adapter read two and DISCARDED the lord's planet name and the sign. So the block could
  not say "the 9th lord is Sun", and lord co-location was a 12-line inference. Now
  restated, plus two pure regroupings: lords sharing a house, and planets ruling two houses.
- **`aspects`** — `conjunctions` / `aspects_by_planet` / `aspected_by` restated verbatim,
  plus a MUTUAL grouping (a one-way aspect and a mutual one carry different doctrinal
  weight; a benchmark answer for this chart rated a one-way aspect as a certain raja yoga
  precisely by not distinguishing them).
- **`dignity`, HEAD ONLY** — Exalted / Debilitated / Own Sign restated; Friendly / Inimical
  / Neutral NOT. See §3.
- **`navamsa`** — D9 restated from a caller-supplied chart. See §4.
Growth contract honoured on all four; `tests/astro/test_capability_gate.py` pins each, and
a further test pins that a pre-S130 `chart_facts` dict still renders BYTE-IDENTICALLY so
replaying an old capture reports no false diff. Suite 217 -> 228.

**WHY IT MATTERS (measured against a Claude-desktop benchmark answer for the same chart).**
Before: the Interpreter emitted "the 9th lord in the 4th" and "the 10th lord in the 4th" as
two UNRELATED claims and never noticed they name one house — which is the
Dharma-Karmadhipati yoga. After (`20260913T065603Z.md`): "With the 9th lord (Sun) conjoined
the 10th lord (Mercury) in the 4th, an angle, you have an angle-trine lords' union." It also
found Venus ruling BOTH the 6th and 11th, which the benchmark answer missed entirely.
This is Working Style #23 in practice: feed the computed term, never ask the model to bridge
two representations.

### 3. THE S129b DIGNITY EXCLUSION WAS UNRATIFIED AND ITS STATED GROUND WAS FALSE
`chart_facts.py` excluded ALL dignity because "no oracle table exists to validate it" and
because "docs/KNOWN_DIVERGENCES.md records the dignity vocabulary fragmenting three ways".
CHECKED: **KNOWN_DIVERGENCES.md contains no dignity entry at all.** Its only three-way
fragmentation is Gap S1, Saptavargaja Bala, which is about VIRUPA TIER WEIGHTS in Shadbala
(Mooltrikona=45 / Own=30 / Pramudita=20 vs Kapoor 45/30/22.5/15) — how much STRENGTH a tier
scores, never which sign a planet is exalted in. A full design-chat history search (run by
Sulabh, pasted to `diagnostics/latest_run.md`) found NO session where the exclusion was
agreed; the last locatable fact-block session is S127, which had not yet even found the
`chart_facts` construction point. Treat the old comment as written by Claude Code and never
ratified.
`_dignity()` (chart_calculator.py:147-162) tests EXALTATION, then DEBILITATION, then
`_OWN_SIGNS` — all fixed constants locked S21 from PVR Table 6, uncontested and never
revisited — and only THEN falls through to `_FRIENDS`, which is the genuinely contested
part. So the S129b reasoning correctly blocks the tail and incorrectly blocks the head.
S21 named the consumer at the time: "most raja/dhana yogas and Neecha Bhanga literally
require knowing exaltation/debilitation/own-sign status".
**STILL OUT, deliberately:** friendship tiers, and exaltation DEGREES — the tables carry
signs only, so deep-exaltation and degree-keyed Neecha Bhanga variants stay unreachable.
Do not synthesise either.

### 4. NAVAMSA (D9) WAS BUILT ALL ALONG — WIRED AT LAST
`agent/calculations/vargas/navamsa.py` has been built and oracle-clean since **S20**:
`compute_navamsa(jd_ut, asc_lon_sidereal)`, 4/4 reference charts passing (David tested
FIRST specifically for pada-boundary sensitivity), commit `2a70f1a`. It was wired to
NOTHING for ~110 sessions because S20 locked *"Don't touch chart_calculator. Don't retrofit
D1"* — an ARCHITECTURAL lock. Nobody ever decided D9 should stay away from users; S20's own
V1 scope table marks D9 REQUIRED for the two highest-value marriage questions. The unwired
state was DRIFT, not policy.
That lock is HONOURED, not worked around: `calculate_chart()` already returns
`meta.jd_ut` + `meta.asc_lon_sidereal`, which are exactly `compute_navamsa`'s two arguments.
So `frontend/app.py` composes D9 and `chart_facts._read_navamsa` only RESTATES it —
calculator untouched, adapter still importing no calculator, P-022 respected. FAIL-SOFT: a
D9 failure costs the Neecha Bhanga check, never the answer.
**ACCEPTED PRECISION GAP:** those meta values are rounded (jd_ut 6dp, asc_lon 4dp), worth
~0.2 arc-seconds against a 3d20' pada. Resolving it means exposing unrounded values from
chart_calculator, i.e. the S20 lock. Recorded, not resolved.
**FIRST LIVE RESULT:** `Mercury: Virgo, D9 house 12, Exalted` — which ANSWERS the exact
question the benchmark answer had to leave open ("the remaining route is Mercury being
exalted in Navamsa… I haven't been asked to read it"). Jupiter and Venus are also exalted
in D9, Moon in own sign.

### 5. GHOST CITATIONS ROOT-CAUSED (fix landed, NOT yet live-verified)
Every ghost in the 2026-09-13 runs came from the prompt carrying **two address formats at
once**: split chapters render as `[ch34_s003]` (book prefix stripped, per-segment) while
whole chapters render as `[bphs2_ch57]` (full unit id, NO sub-ids). The model normalises to
the dominant per-segment format and mints sub-ids for the whole ones. 9 of 10 ghosts in one
turn were `ch57_s001..s016` against `bphs2_ch57` "Effects of the Antardasas in the Dasa of
Saturn" — a chapter genuinely present, genuinely on-topic, carried WHOLE. The remaining two
were ordinal overruns: `ch34_s013` where ch34 ends at s012, `ch17_s012` where ch17 ends at
s004. Measured: 23 of 81 selected units contribute zero segments and are carried whole.
NOT fabrication — an ADDRESSING failure, and an expensive one, because the ghost guard drops
the CLAIM along with the id (the Saturn turn shed 10 ids and shipped 2 claims).
FIX: `interpreter._id_manifest()` renders a complete CITABLE IDS list ahead of the verses,
whole chapters flagged as having no sub-ids, plus an inline marker on each whole chapter.
4 tests, incl. one asserting the manifest actually reaches the system prompt.
This is S124's own law reappearing: an id space the model cannot enumerate produces
addresses that cannot resolve.

### 6. OPEN, FOUND THIS SESSION, NOT FIXED
- **A false-precondition claim shipped.** Saturn turn: "…as the 10th lord in the 8th gives
  obstructions…" — this chart's 10th lord is in the 4th. The enforcing silence gate did NOT
  judge it: `read_condition` returned `None` with "condition is negated or exclusionary",
  because the word "unless" appears in a DIFFERENT clause of the same sentence. Fails safe,
  so it was kept — and shipped. The negation guard is clause-blind.
- **`ungated_pct` hit 100%** on two turns: the enforcing gate judged nothing at all.
- **The planner selects almost everything.** 14 of 16 domains for "What does Saturn's
  placement mean"; 81 units; prompt_tokens 185k-229k against the ~80k the $0.19/question
  estimate was built on. `cached_tokens` 0 on six of seven turns — the corpus-first cache is
  not hitting.
- **`planetary_nature` is a glossary domain.** All five chapters are reference material
  (ch2 Great Incarnations, ch3 Planetary Characters, ch4 Zodiacal Signs, ch76 Five Elements,
  ch77 Satwa Guna). The planner picked it ALONE for "What do Mars and Venus say about me?"
  and gpt-5 correctly recited definitions — "Venus is a female planet" — with a true
  placement prefix. Faithful, cited, gate-clean, worthless to a reader. Proposed one-line
  planner gloss is in `diagnostics/planet_reader_evidence_S130.md` §2, NOT applied: a planner
  prompt change alters planning for every question and cannot be verified without live
  gpt-4o calls, which the sandbox cannot make.
- **Answer SHAPE is now the biggest gap to the benchmark.** The facts are no longer the
  constraint — Sarala VRY (8th lord in 12th) and the Moon's Neecha Bhanga both sit in the
  block and went unused, and D9 was never mentioned. The benchmark leads with a verdict,
  ranks by reliability, and states what it rules out; ours emits a flat list of whichever
  verses matched, and still leaks banned jargon ("angle-trine lords' union").
  This is an interpreter-prompt + `answer_view` job.

### 7. ADVISORY PLANET READER — HOLD (unchanged)
`20260913T040439Z.md`: 21 planet claims judged, `advisory_would_drop_a_kept_claim` = **0**.
A REAL zero, not the vacuous one S129 feared — but gpt-5 wrote every claim as "With <planet>
in the <TRUE house>, <doctrine>", so the reader validated a true prefix 21 times and was
never given the chance to refuse. Promotion grants DROP authority; no drop event has been
observed, so the behaviour promotion actually changes is still unmeasured. `HOLD`.
`scripts/classify_advisory_drops.py` sorts would-drops into CORRECT_CATCH /
UNCAUGHT_LORDSHIP / DEFINITIONAL and now has a branch for "fired but never disagreed".

### 8. MY OWN ERRORS THIS SESSION (root-caused)
- Called `silence_gate.py:525-527` a GENUINE DEFECT (`claim in kept` membership). It is not:
  `judge_claim` is a pure function of the claim dict, so value-equal claims get equal
  verdicts and land in the same bucket — the false positive is unreachable BY CONSTRUCTION.
  Proven with a 2,800-case exhaustive differential harness, 0 mismatches. I asserted a defect
  without proving reachability (rule 28) and overruled the Architect on a false premise.
- Asserted the capture lacked a judged-count denominator for the promotion metric. It does
  not — `advisory_applicable`/`_not_applicable`/`_undetermined` have always been in
  `gate_stats`. I asserted from the handover instead of the code (rules 32-34).
- Twice claimed a live-run question set would work without checking what the model actually
  cites; corrected only after measuring 96 planet-shaped sentences sitting unused in the
  career payload.
- Delivered source files as chat file-cards instead of just writing them to the repo.

**NEXT:** see `claude_handover_S130.md`.


## S131 — Stage 5b composer (answer shape becomes an LLM decision); yoga detector built, ruling-out becomes a calculation (2026-09-13)

**BRANCH:** `wip/interpretive-pilot`, on top of **`b6bcc54`** — the S130 commit.
Written to disk UNCOMMITTED. Suite **4123 passed, 7 skipped, 5 deselected**,
unchanged before and after every edit this session.

**CORRECTION TO THE RECORD, FOUND FIRST THING.** Sulabh opened the session saying
S130 was uncommitted; `CLAUDE.md:8` and SESSION_LOG §S130 say the same. Both are
stale by ~70 seconds: `.git/logs/HEAD` records
`c0d6c70 -> b6bcc5447728339ec3e96323a604893cc8798662` at 1789289494, message
"S130: reasoning_effort never reached the API…". S130 IS committed. The two
documents were written just before the commit and never updated.

### 1. THE SCORER WAS DESIGNED, THEN REJECTED — RECORDED SO IT IS NOT REBUILT
S131 first proposed answer shape as: an extended claim schema carrying
fact-reference `mechanism` / `degraders` / `unresolved`, a deterministic
reliability+ceiling scorer, and verdict templates selected by the topology of the
scored set. **Sulabh rejected it:** "scoring logic will change as per scenarios and
same for topology… we will get into mesh of all these setting and thresholds".
He was right — it is precisely the threshold proliferation Working Style #4 exists
to stop, and it would need a new lattice branch per question shape. REPLACED by an
LLM composer. **Do not re-propose the scorer.**

### 2. STAGE 5b — THE COMPOSER (`agent/astro/composer.py`, NEW)
A second, tiny gpt-5 call whose ONLY input is the gated claim set: question, the
kept claims with each claim's ENFORCED gate verdict, dropped claims, `silent_on`.
It decides salience and order and writes plain English.

**Why a separate stage and not the interpreter prompt.** Every `_SYSTEM_HEAD` edit
is a live-run trigger against a 185k-token payload. The composer takes shape work
off it entirely and **the interpreter prompt was not touched this session.**

**Cost, measured not assumed** (`diagnostics/qa_capture/20260913T065603Z.md`):
composer input 553 and 312 tokens against the SAME turn's **185,297** interpreter
prompt tokens — ~0.8%. Live: `prompt_tokens` 1176 / 766, `completion_tokens`
537 / 313, `reasoning_effort_path=extra_body`.

**THE S129b NO-REWRITE RULE IS REPLACED BY MECHANISM, NOT RELAXED.** S129b barred
`answer_view` from rewriting AND re-ordering because rewriting is where a
gate-verified claim silently becomes unverified. The composer does both, so
`composer._verify` substitutes:
- **ENFORCING — no new chart facts.** A rewrite may not contain a chart token
  (house ordinal / graha / sign / dignity) absent from the claim it rests on.
  Closed vocabulary, set containment, NO prose parsing — deliberately not the
  clause-reading whose negation guard proved clause-blind (S130 §6). A failing
  block DEGRADES to the original claim text; it is never dropped.
- **ADVISORY — conditions survive.** Recorded in `condition_advisory`, NOT
  enforced. A keyword test cannot distinguish a genuinely unhedged rewrite from
  one carrying the condition in other words ("a strong 6th lord brings…"), and
  enforcing it would push most answers back to the jargon original — defeating the
  stage. Promotion is gated on the measured rate, exactly as the planet reader was
  (S129b (4)). **Do not promote on intuition.**
- **COVERAGE.** Every input claim is rendered or explicitly demoted with a reason;
  anything unaccounted for is auto-restored (`unaccounted_restored`).

**OFF BY DEFAULT.** `compose=False` (or `ASTRO_COMPOSER_ENABLED` unset) means the
branch does not run and the result is byte-identical to pre-S131. The composer
never raises and never replaces `answer`.

**VERIFIED BEFORE BUILDING (no assumptions):** `GateResult.verdicts` carries a
per-claim `ClaimVerdict`, built in claim order — but `answer_question`'s return
dict does NOT carry it (repo-wide grep: only `silence_gate.py:108` and `:580`
touch `.verdicts`). It is reachable in-process at the gate call, which is where
Stage 5b sits. Claims carry NO id anywhere, so `composer._claim_rows` assigns
positional ids by re-deriving the kept partition from `gate.verdicts` — no change
to `GateResult` was needed.

**LIVE RESULT (real gpt-5, both turns, via `replay_capture --compose`).** Stage 4
replayed from the stored raw response, so only the composer call was live.
**0 invented facts across two independent calls.** Both answers opened with a
verdict ("Yes—you do have clear angle–trine combinations…" / "the picture is
cautious because both key points are unverified"), both flagged verified vs
unverified per claim, both closed with what was not assessed. Turn 1's ordering
roughly tracked `checked` status. Full before/after text in
`diagnostics/latest_run.md`, archived under `diagnostics/runs/`.
gpt-5 at `reasoning_effort=minimal` is NOT deterministic call to call — the two
calls differed in wording and in whether the advisory fired. Expected, not a defect
(the S123 run-to-run-variance law applies to text composition too).

### 3. THE YOGA DETECTOR (`agent/calculations/yogas/`)
Four Phase-0 stubs FILLED: `detector.py`, `catalog/raja_yogas.py`,
`catalog/special.py`. Pure arithmetic over the already-computed fact block — no
ephemeris, no `chart_calculator` import, no chart fact computed (S124 + S20 hold
by construction). Catalogue modules are plain `detect(facts) -> list[dict]`, so
nothing in `catalog/` imports `detector`; there is no cycle. NEVER RAISES.

**EVERY RULE RETURNS A NOT-FIRED REASON.** That is the deliverable, not a nicety:
"you do not have Gajakesari, because your Moon and Jupiter are six houses apart"
is the half of an answer this pipeline has never been able to produce.

**PRE-FLIGHT DONE (P-024), before writing anything:** `pancha_mahapurusha.py` was
already BUILT (3,322 bytes, uses `calculations.core.dignity.get_dignity_status`)
and wired to nothing; `detector` / `raja_yogas` / `neecha_bhanga` / `dhana_yogas`
/ `special` were docstring-only stubs; `chart_calculator._calc_yogas` returns ONLY
`mangal_dosha` and `kalsarpa_yoga` — there was no raja-yoga logic to restate.

**VALIDATED 6/6 against `Output.txt`** (the Claude-desktop benchmark for this same
chart; identity confirmed from the capture's own `chart_facts` — Sagittarius
lagna, Moon debilitated in Scorpio 12th, Mars exalted in Capricorn, Mercury
debilitated in Pisces 4th, Venus own sign 6th). `scripts/probe_yoga_detector_S131.py`
-> RESULT: PASS.

| rule | expected | got |
|---|---|---|
| Dharma-Karmadhipati | FIRED | FIRED |
| Sarala (VRY) | FIRED | FIRED |
| kendra_trikona_4_5 (Mars aspects Jupiter) | FIRED | FIRED |
| Harsha (VRY) | RULED OUT | RULED OUT |
| Vimala (VRY) | RULED OUT | RULED OUT |
| Gajakesari | RULED OUT | RULED OUT |

**CONTESTED, DELIBERATELY UNRESOLVED.** Vipareeta rules carry `contested=True` +
`contested_note`: Uttara Kalamrita requires the dusthana lord in one of the OTHER
two dusthanas; later compilations also count its own. The module takes the UK
reading — the same one the benchmark used to rule out Harsha. Do NOT widen the
condition; that is the Tiebreaker-principle call and it is Sulabh's.

**DUPLICATE-LOOKING HITS: RULED, NO ACTION.** 7 fired rows include
`kendra_trikona_7_9` and `kendra_trikona_10_9`, both resting on the same physical
Sun+Mercury conjunction; both are genuinely distinct lordship links. Sulabh:
"Our composer will automatically merge them we need not to do anything."

### 4. MY PREMISE WAS FALSE AND SULABH CAUGHT IT
S131 asserted the ruled-out set could not be produced because the desktop
benchmark ruled out Gajakesari and Harsha using training knowledge, which S124
bars. Sulabh asked where that knowledge came from. VERIFIED in
`data/chapter_index_bphs.json`: **Gajakesari is in `bphs1_ch36` ("Many Other
Yogas"), the Vipareeta trio in `bphs2_ch48`, Neecha in `bphs1_ch24`.** Worse —
all four chapters were ALREADY SELECTED and shipped in the 065603Z turn (46 units
selected). The doctrine was in front of gpt-5 and went unused, and `ch48_s001`
sits in that turn's `ghost_citations`: the model reached for the Vipareeta chapter
and the addressing bug threw the citation away. Ruling-out was never an
outside-knowledge problem. This is rule 33/34 again — I asserted a limit without
searching the primary source I could already read.

### 5. OPEN, FOUND THIS SESSION, NOT FIXED
- **Jargon survives the rewrite.** "angle–trine" appeared unglossed in 5 of 6
  claim blocks plus the lead. A prompt blocklist was **rejected by Sulabh as
  hardcoding** ("we cant harcode block for each of these kinds of issues"). Two
  general routes, neither chosen: reframe the rule from a banned-word list to a
  principle plus self-check, or DERIVE a jargon lexicon from the corpus (frequent
  in BPHS, rare in ordinary English) — the same SSOT reasoning as
  `feature_needles.py` and `ontology_registry.json`.
- **One condition drop observed.** Turn 1 claim 0: source "especially WHEN that
  1st lord also rules the 4th…" → rewrite stated it settled. Logged by the
  advisory check, not blocked. Sulabh: "lets keep this in mind, no action as of
  now."
- **`ungated_pct` measured 66.7% and 100%** on the two turns. On the Saturn turn
  the composer has NO verification signal to rank by, because every claim is
  UNDETERMINED. The clause-blind negation guard therefore now blocks composer
  quality and has risen in priority.
- **The fact block is NOT yet widened with yogas.** Whoever does it MUST add the
  key to `capability_gate.FACT_BLOCK_PROVIDES` in the SAME change.
- **`interpreter.py`'s module docstring is still stale** — "PATH B / LAB TRACK —
  NOT WIRED TO THE PRODUCT (S128 lock)", false since S129.

### 6. MY OWN ERRORS THIS SESSION
- Asserted the ruled-out set needed outside knowledge without grepping the chapter
  index I could already read (§4). Rules 33/34.
- Proposed a scorer + topology templates that would have become a threshold mesh;
  Sulabh's rejection was correct on the merits, not a preference.
- Overstated composer iteration as "free". Stage 4 replays free; the composer call
  is live at ~1.5k tokens. Corrected in-session.
- Delivered source as chat file-cards once, against a standing instruction.
  `device_commit_files` takes a staged path directly; no card is needed.

**NEXT:** see `claude_handover_S131.md`. First task is Neecha Bhanga.
