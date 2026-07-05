## Session Log

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

## Session 32 — P2.5.3 Kala Bala complete

### What landed
- agent/calculations/strength/kala_bala.py — all 9 Kala Bala
  sub-components: Nathonnatha, Paksha, Thribhaga, Abda, Masa,
  Vara, Hora, Ayana, Yuddha. Public API: compute_kala_bala()
  with optional sthana_result/dig_result for Yuddha cross-deps.
- tests/calculations/strength/test_kala_bala.py — 81 tests
  (Layer A structural, Layer B Sulabh all-7-planets AstroSage
  parity, Layer C Surbhi spot-checks). 81/81 passed.
- CLAUDE.md — Ayana Bala Moon/Venus divergence documented.
- ASTRO AGENT — MASTER BUILD PLAN.md — no changes this session.

### Key decisions locked (carry forward)
1. Paksha Bala classification (locked from 27/28 data points
   across 4 charts): Jupiter/Venus always benefic; Sun/Mars/Saturn
   always malefic; Moon/Mercury paksha-dependent (benefic Shukla,
   malefic Krishna). Sheridan Moon=26.9 is a fixture PDF typo
   (expected 46.56); converted to informational comment in test.
2. Ayana Bala formula: PyJHora (24.0 + adj_decl) * 1.25, Sun
   doubled. Moon/Venus diverge +5.26/+3.69 at near-max declination.
   Raman formula (23.45 * 1.2793) tested and rejected — did not
   resolve outliers. Gap accepted. DO NOT re-investigate.
3. Abda/Masa Bala: BPHS-compliant (Mesha Sankranti / new moon
   weekday lord). PyJHora's implementation uses birth weekday
   for both — confirmed placeholder, not used.
4. Yuddha Bala: explicit 1° war gate enforced per BPHS.
   No war in any of 4 reference charts (yuddha=0 all fixtures).
   Disc constants: Raman confirmed via PyJHora const.py.
5. Test tolerance tiers: ayana Moon/Venus = 6.0; ayana others
   = 2.0; all other sub-components = 0.5 Virupa.
6. One prompt = one file rule locked this session. Never bundle
   implementation + tests + docs in one Claude Code prompt.

### Bugs caught mid-session
- Paksha: Mercury initially coded always-malefic; Surbhi fixture
  (Shukla, Mercury=56.75) disproved it. Fixed to paksha-dependent.
- Yuddha test: all 7 planets at lon=90 fired 10 simultaneous wars.
  Fixed by isolating non-combatants to lon=200.
- Ayana FLG_SIDEREAL removal (attempted "fix") changed values
  by only 0.003° — confirmed declination is tropical/sidereal
  invariant. No impact.

### Test baseline
1213 passed, 3 skipped, 0 failures.

### Next task
P2.5.4 Chesta Bala (motional strength). Pre-prompt research
required: search jhora_sulabh.md for Chesta Bala values;
search shadbala_fixtures.py for chesta key; search PyJHora
strength.py for chesta_bala implementation before drafting prompt.

---

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

## Session 19 — Architecture Reset (in progress)

**Date:** [today]

**Decisions locked:**
- Confidence-Tiered Answer Architecture: T1 Exact / T2 Range / T3 Personalized Muhurta / T4 Interpretive / Refusal
- Calculation-first sequencing: complete classical surface before answer pipeline
- 9-agent framework (added Ephemeris Auditor, Validation Source)
- JHora = primary validation oracle (installed); AstroSage = secondary parity
- KP deferred to v2; edge cases (polar, pre-1900) out of scope for v1
- 7-phase calculation roadmap: P1 Foundation → P2 Charts/Strength → P3 Yogas → P4 Dashas → P5 Transits → P6 Jaimini → P7 Answer Pipeline

**Honest gap assessment:**
- Current calculation surface = ~15% of classical Vedic toolkit
- Have: D1, Vimshottari, Muntha, Mudda Dasha, Varshaphal Lagna, RAG
- Missing: vargas D9-D60, Shadbala, Ashtakavarga, aspect graph, yoga detection, Yogini/Chara dashas, Gochara, Panchanga, Jaimini karakas

**Session 19 work in progress:**
- P1.1 — Refactor `chart_calculator.py` → `calculations/` package
- Next: P1.2 Panchanga module

**Session 19 continued — P1.2b + P1.2c + ayanamsa (this entry):**

Work completed:
- P1.2b: core five Panchanga elements (tithi, vara, nakshatra, yoga, karana) + hora — validated against 4 JHora fixtures (sub-0.3% deltas).
- P1.2c: Choghadiya, Rahu Kalam, Yamaganda, Gulika Kalam, Abhijit Muhurta — validated against 4 fixtures; Sheridan (605 min day) vs David (983 min day) confirmed proportional behavior with 62% segment-length spread.
- Ayanamsa field wired (SIDM_LAHIRI), 4 tests added.
- `_pvr_spec_reference.json` created (P1-scope topics only) — 6 found in PVR (tithi, vara, nakshatra, yoga, karana, hora), 5 not in PVR (choghadiya, rahu_kalam, yamaganda, gulika_kalam, abhijit_muhurta).
- Hora comment corrected: PVR defines hora as 24 equal clock-hours from sunrise (`vara_elapsed_sec / 3600`), NOT proportional. Earlier comment claiming day_length/12 was wrong; code itself was always correct. Distinct from the Choghadiya/muhurta-family fields, which ARE proportional.
- Test count: 76 → 112.

Key findings/decisions:
- Gulika Kalam slot table corroborated by PVR §4.3 (Gulika Upagraha Saturn's-part-of-day table) — positive cross-validation of `GULIKA_KALAM_SLOT` for all 7 weekdays. Upgrades Gulika Kalam from "formula-only" to "PVR-corroborated-via-related-upagraha" validation tier.
- Abhijit Muhurta: PVR does not cover it. Implementation uses the Muhurtha-Chinthamani definition (day_length/15, 8th of 15 daytime muhurtas). Validated geometrically only — center = local noon to 0.0s on all 4 fixtures. No JHora numeric oracle available in current basic exports.
- Validation tier (lower than full-oracle): Rahu Kalam, Yamaganda, Gulika Kalam, Abhijit Muhurta — all validated by formula correctness + geometric/structural checks, NOT by independent JHora numeric cross-check (basic JHora exports don't expose these windows). Deferred: bundle JHora muhurta-menu extraction into the planned `jhora_parser.py` (Phase 0.6) scope.
- Ayanamsa: pyswisseph SIDM_LAHIRI kept (consistent with all prior P1 work). Cross-implementation gap vs JHora's Lahiri = 57.77″, perfectly flat across all 4 fixtures (structural formula difference, not a bug). Working tolerance set to 60″ for ayanamsa tests specifically. Full investigation in `playbook_export/decisions/ayanamsa-investigation.md`.

Next planned work: P1.3 — Dignity + Aspects (Graha Drishti per classical rules: 7th-from-self for all planets, plus special aspects for Mars 4th/8th, Jupiter 5th/9th, Saturn 3rd/10th). Refer to the PVR spec reference once extracted for P1.3 topics in a future `_pvr_spec_reference.json` extension.

**Session 19 continued — P1.3 Aspects, CLOSED (this entry):**

**Date:** 2026-06-20
**Phase tag:** P1.3 Aspects — CLOSED

Completed P1.3 Aspects sub-phase. Nine-planet graha drishti table, three public aspect functions, 73 new tests. Final test baseline: 593 passed, 3 skipped.

Decisions locked this session:
- Rahu/Ketu graha drishti = (5,7,9) Jupiter-pattern, both nodes symmetric. Anchored to AstroSage 4-PDF parity + Sanjay Rath + modern web consensus. PyJHora const.py L508 (7,)-only and JHora-UI 2,5,7,9-asymmetric explicitly rejected and cited as alternatives.
- Tiebreaker principle established (now memory #10): when classical sources are genuinely fragmented, user-perceived correctness wins over single-source-code purity. Applies to all future P2-P7 contested decisions.
- SENSITIVE_TO tag convention introduced: downstream consumers of contested locks must reference the lock by name in their docstrings so future revisions trigger targeted regression sweeps.

Files shipped:
- `agent/calculations/core/_aspects_tables.py` — 9-planet table + full citation block (data table: commit de9debe; comment-only citation rewrite: commit 23efe58)
- `agent/calculations/core/aspects.py` — 3 public functions (`signs_aspected_by`, `does_planet_aspect_sign`, `aspects_between`) + `ASPECTING_PLANETS` constant (commit aee45ed)
- `tests/calculations/test__aspects_tables.py` — 54 tests (commit de910eb)
- `tests/calculations/test_aspects.py` — 19 tests (commit 23efe58)

Investigation trail: PyJHora source code investigation surfaced (7,)-only for both nodes, contradicting the original (5,7,9) lock. Multi-source landscape mapped across 8 sources. After agent debate, lock reverted to (5,7,9) on user-perceived-correctness grounds — PyJHora is an outlier vs. every major user-facing site. Decision trade-off documented explicitly in the table's citation block so the next dev sees the reasoning, not just the value.

Next session entry point: P2.1 Navamsa (D9) — first divisional chart. Hardest-case target: David's chart for boundary signs. Open questions pre-listed in the P2.1 handoff.

## Session 20 — P2.1 Navamsa (D9)

**Date:** 2026-06-20
**Phase tag:** P2.1 Navamsa (D9) — CLOSED

Decisions locked this session:
- Chart/VargaType prep task aborted before any code was written: grep confirmed no Chart dataclass exists anywhere in the codebase, and `calculations/core/panchanga.py`'s functions take raw `(datetime, latitude, longitude)` primitives directly, not a chart object — wiring the requested guard-rail pattern would have required adding a new parameter to ~9 function signatures, which the task explicitly forbade. Paused and re-scoped with Sulabh rather than inventing infrastructure nothing consumes.
- P2.1 Navamsa (D9) re-scoped to a pure function over birth-time primitives instead: `compute_navamsa(jd_ut, asc_lon_sidereal) -> NavamsaChart`. No Chart dataclass, no VargaType enum — explicitly deferred until a future varga module actually needs shared chart-identity state (P2.5-boundary note left in navamsa.py's docstring).
- Pada formula: exact `30.0/9.0` arithmetic (not a rounded 3.333 constant), with a defensive clamp to 8. Verified pada-boundary floats numerically before locking the 5 edge-case test expectations rather than assuming them — e.g. 3°20'00" lands bit-identically on the pada-1 boundary (`3 + 20/60` and `30.0/9.0` are bit-identical floats), 26°40'00" lands bit-identically on pada-8.
- D9 starting-sign table hardcoded per PVR Ch.7/BPHS Ch.6 movable/fixed/dual convention; confirmed it reduces to "each triplicity starts from its own movable sign" (fire to Aries, earth to Capricorn, air to Libra, water to Cancer) and cross-checked against 3 locked test values (Aries to Aries, Taurus to Capricorn, Gemini to Libra) before writing the table.

Files shipped:
- `agent/calculations/vargas/navamsa.py` — `NavamsaPlacement`/`NavamsaChart` (frozen dataclasses), `compute_navamsa()` (commit 2a70f1a; one-line Ketu-comment closeout in 16036ec)
- `tests/calculations/vargas/test_navamsa.py` — Layer A (8 structural/input-validation tests, no ephemeris), Layer B (4 reference-chart parity tests, skipped pending manual fixture extraction), Layer C (4 internal-consistency tests) (commit 2a70f1a)
- `tests/calculations/vargas/__init__.py`

Test baseline: 593 passed / 3 skipped (Session 19 close) -> 614 passed / 7 skipped (21 new passing tests + 4 new skips, zero regressions). `chart_calculator.py` and `calculations/core/panchanga.py` untouched throughout.

Next session entry point: David fixture extraction (Navamsa parity) — manually extract David's AstroSage Shodashvarga (D9) page values (lagna sign + each of the 9 planets' d9_sign/d9_house), cross-check against JHora, and populate `tests/calculations/vargas/test_navamsa.py` Layer B for David first (hardest case), then Sulabh, Surbhi, Sheridan. After fixtures land: P2.2 Dasamsa (D10).

## Session 20 continued — P2 reorder + P2.1 Navamsa fully closed (this entry)

**Date:** 2026-06-20
**Phase tag:** P2.1 Navamsa (D9) — fully CLOSED; P2 roadmap reordered

Deliverables:
1. Scope-calibration exercise: 20 V1 layman questions classified against the calculation surface, leverage ranking established per module.
2. P2 sequence reordered (see locked order below) — supersedes the flat "P2 Charts/Strength" placeholder from the Session 19 roadmap.
3. P2.1 Navamsa final closeout: 4/4 reference charts (David, Sulabh, Surbhi, Sheridan) now PASSED, no skips — David activated first (hardest case), then Sulabh/Surbhi/Sheridan in one pass, each verified independently against the project's own `calculate_chart()` primitives before being locked into the test file.
4. Test baseline: 618 passed, 3 skipped (Panchanga-related skips remain; unrelated to this session's work).

Decisions locked this session:
- Reference-chart fixture template: one standalone test function per chart (not a shared `@pytest.mark.parametrize`) when each chart's expected-value structure differs (named dict of 9 planets here); the skip-stub parametrize block is deleted once its backing list is empty, not left as dead scaffolding.
- ASC citation honesty: do not fabricate a degree-level AstroSage value when the source material is sign-only (Sulabh's `reference_charts.md` entry omits a natal ASC degree) — the gap is noted explicitly in the citation comment rather than papered over.
- Tiebreaker principle (memory #10) extends beyond contested calculation values to roadmap sequencing — user value beats classical pedagogical ordering wherever no classical source mandates a specific build order.

Locked P2 order (supersedes the Session 19 placeholder):
- P2.2 Gochara (transits) — was D10
- P2.3 Muhurta answer-engine
- P2.4 Ashtakoot + Mangal dosha
- P2.5 Shadbala
- P2.6 D7 Saptamsa
- P2.7 D10 Dasamsa (demoted)
- P3+ Yogas / Jaimini / Arudha — deferred for V1

Rationale: scope-calibration against the 20 V1 layman questions showed Gochara answers 13/17 high-value rows; D10 Dasamsa answers 0/17 — the original D9→D10 divisional-chart-family ordering optimized for classical pedagogy, not user-facing leverage.

Next session entry point: P2.2 Gochara (transits).

## Session 21 — P2.2.1 Gochara (transits)

**Date:** 2026-06-21
**Phase tag:** P2.2.1 Gochara — first implementation GREEN; transit anchor convention provisionally locked

Deliverables:
1. Scope-calibration exercise — 20 V1 layman questions classified; leverage ranking established.
2. P2 sequence reordered (V1-user-value over classical pedagogy) — see the Session 20 continued entry for the full locked order.
3. P2.1 Navamsa fully closed: 4/4 reference charts (David, Sulabh, Surbhi, Sheridan) PASSED.
4. `agent/calculations/transits/` package scaffolded with locked design docstrings + `NotImplementedError` stubs (gochara.py, sade_sati.py, transit_aspects.py).
5. P2.2.1 `compute_gochara()` implemented; 2 reference fixtures (Surbhi, Sheridan) PASSED.
6. Anchor convention diagnostic: 5 candidate JDs tested; 18:30 UTC (00:00 IST next-day rollover) is the only anchor matching all 9 planets simultaneously.

Decisions locked this session:
- P2 reordering: P2.2 Gochara, P2.3 Muhurta answer-engine, P2.4 Ashtakoot + Mangal dosha, P2.5 Shadbala, P2.6 D7, P2.7 D10 (demoted), P3+ Yogas/Jaimini/Arudha (deferred for V1).
- Calculation subpackage `__init__.py` convention: empty (no re-exports). Callers use direct module imports — `transits/__init__.py` was normalized back to this shape after briefly deviating.
- Reference-chart fixture template: standalone test per chart with real assertions; no parametrize when assertions differ; skip-stub deleted when its list empties.
- ASC citation honesty: do not fabricate degree-level AstroSage values when source is sign-only; note the gap in the citation comment.
- Mean Node for transit Rahu (deliberate divergence from JHora; matches AstroSage + Indian astrologer mainstream).
- Sade Sati boundaries from natal Moon SIGN (Janma Rashi), not nakshatra — universal app/astrologer consensus.
- Tiebreaker principle extends to roadmap sequencing — user-perceived value beats classical-text pedagogy where no source forbids.
- Transit fixture canonical moment 18:30 UTC = 00:00 IST next-day rollover (PROVISIONAL — strong lead, sub-arcsecond margin on the Mars boundary, needs second-date corroboration).

Test baseline: 618 passed / 3 skipped (Session 20 close) -> 620 passed / 3 skipped (+2 from the new Surbhi/Sheridan transit fixtures).

Open items carried forward:
- Interpretive-text feasibility spike (30-min RAG+GPT-4o experiment vs AstroSage paragraph quality) — execute after P2.2 closes.
- AstroSage anchor convention corroboration on second date.
- CLAUDE.md trim pass (currently 119 lines vs ~80 budget; flagged by Claude Code Session 21).
- Retrograde-double-ingress handling for sade_sati.py design (Sheridan rows 13-19, Surbhi rows 15-17 confirm this is not edge-case but mainline).
- Sulabh and David transit fixtures (only Surbhi/Sheridan currently active).
- `helpers/ephemeris.py` extraction (still stub; convention is direct `swe.calc_ut` with a TODO marker per call site).

Next session entry point: P2.2.2 Sade Sati.

## Session 22 — P2.2.2 Sade Sati closed; Interpretive-text spike returned FAIL; calculation roadmap paused

**Date:** 2026-06-21
**Phase tag:** P2.2.2 Sade Sati — CLOSED; P2.2.3+ PAUSED pending architectural rethink

Work completed:
1. P2.2.2 `sade_sati.py` implemented and validated against AstroSage Sade Sati reports for Sheridan + Surbhi. 623 passed / 3 skipped.
2. `macro_sade_sati` field added to `SadeSatiStatus` dataclass on Claude Code's initiative during implementation — accepted retroactively (genuinely useful, semantically distinct from `current_phase_window`). Flag for awareness: was not in the locked Session 20 scaffolding contract.
3. Gating contract locked: `macro_sade_sati` populated whenever `transit_jd` ∈ `[overall_start_jd, overall_end_jd]`, independent of instantaneous phase. `current_phase_window` gated on `phase != NONE`. Surbhi's June-October 2027 Aries gap (Saturn outside her envelope mid-Sade-Sati) validated as the canonical test case in Test 3.
4. Macro envelope bug found and fixed during implementation: old 3-sign envelope continuity logic broke on retrograde dips into non-envelope signs (Surbhi-specific failure mode; silent on Sheridan because her envelope happened to contain the dip target). Replaced with independent rising/setting sign scans (earliest rising ingress + latest setting egress).
5. Interpretive-text feasibility spike (backlog #1) executed. Single throwaway harness, Sheridan Saturn-in-11th-from-Lagna (retargeted from 6th after verification). Three-way comparison produced. Rubric score: 0/4 Yes. Decision: FAIL.

Spike findings (structural, not just rubric):
- RAG retrieval is broken at corpus level: 3 of 8 chunks were exact duplicates (ChromaDB indexing bug); off-topic dominates (12th-house content, 5th-10th content cutting off before 11th, a TOC heading); corpus itself documents a gap on Saturn-in-11th-from-ascendant (Deva-keralam p.59 chunk explicitly flags the missing lines).
- Layering prompt is independently broken: adding AstroSage to the RAG+LLM context (Output C vs B) LOST named citations B had, contradicted AstroSage on 3+ themes despite "do not contradict" instruction, and degraded voice from astrological to corporate/therapeutic register. Even with perfect RAG, this prompt structure would fail.
- Personalization is tokenistic: "Aries Moon native" name-dropped once, never integrated. No use of natal Saturn placement, dignity, dasha context.

Decisions locked this session:
- `macro_sade_sati` gating contract (see point 3 above).
- P2.2.3 transit_aspects PAUSED. Aspects calculations are useless until the interpretive layer architecture is settled.
- Calculation roadmap on hold pending architectural rethink.
- RAG corpus rebuild queued as a parallel workstream regardless of architectural path chosen.

Test baseline: 620 -> 623 passed (+3 from Sade Sati tests).

Calendar/JD clarification: confirmed Gregorian calendar setting in both JHora and pyswisseph (gregflag=1) is correct for all modern chart dates; "Julian Date" (continuous day count) is unrelated to "Julian Calendar" (pre-1582 system).

Open items carried forward:
- Architectural rethink for interpretive layer. Three candidate paths to debate Session 23:
  (a) Extract-then-annotate two-stage pipeline
  (b) Template-bound generation (AstroSage as fixed scaffold)
  (c) Scope cut — AstroSage terminal, RAG/LLM reserved for follow-up Q&A only
- RAG corpus rebuild: dedup, chunking strategy review, plug Deva-keralam gap on 11th-house-from-ascendant content.
- Sade Sati systematic delta pattern: ingress consistently -0.3d, exits consistently +0.5-0.9d vs AstroSage day-only dates. Likely cause: AstroSage uses IST sunrise rollover rather than UT midnight for date assignment. Worth a 5-min investigation when a time-stamped oracle is available (also closes backlog item #2 anchor corroboration in the same pass).
- AstroSage anchor convention corroboration on second date (open since Session 21).
- CLAUDE.md trim pass (handled in Part B of this prompt).
- Sulabh and David transit fixtures (only Surbhi/Sheridan currently active for P2.2.x work).
- `helpers/ephemeris.py` extraction (still stub).
- `SadeSatiWindow` range-scan API (P2.2.2b, deferred).

Next session entry point: Session 23 — interpretive layer architectural debate. Full 9-agent framework. Three candidate paths above. No code until architecture is locked.

## Session 23 — Architectural debate closed; corpus dedup executed; Path (c) validation FAILED; V1 scope locked

**Date:** 2026-06-21
**Phase tag:** Interpretive-layer architecture — LOCKED (path (c) selected, then invalidated by its own validation run); calculation roadmap UNPAUSED

Work completed:
1. Architectural rethink: 9-agent debate walked the three Session 22 candidate paths — (a) extract-then-annotate two-stage pipeline, (b) template-bound generation (AstroSage as fixed scaffold), (c) scope cut (AstroSage terminal, RAG/LLM reserved for follow-up Q&A only). (b) eliminated for AstroSage prose-shape instability (no stable structural anchor to template against). (c) selected pending validation, as the smallest, most testable change. (a) deferred as a V1.1 candidate pending corpus rebuild + natal-context redesign — not ruled out, just not V1-critical-path.
2. Corpus dedup: `chromadb_dup_diagnostic.py` surfaced 3,930 byte-identical duplicate-text groups (~25% of the 11,688-chunk collection). Root cause traced via the chunking-code audit + provenance audit to a 2026-05-27 mystery write into `data/progress/*.json` (writer never identified — PowerShell history had no record covering that window) compounded by `run_single_book.py`'s 2026-05-30 re-merge re-chunking content that was already chunked. `embedder.py` hardened with `text_sha256` idempotency (prompt #5) to prevent recurrence. Targeted delete removed 3,945 X/X_c<N> duplicate children: 11,688 -> 7,743. Full-fidelity snapshot retained at `diagnostics/targeted_delete_snapshot_20260621_120557.jsonl` (122 MB, includes embeddings) for reversibility.
3. Post-delete verification: dedup mechanics landed clean — axis (b) duplicate-text groups 3,930 -> 10 (all OCR-garbage residuals, e.g. the 18-member literal `|` group), axis (c) near-identical-embedding pairs 5 -> 0. Saturn-11th retrieval is now 8/8 distinct (no within-result duplicates), but relevance is unchanged from pre-delete: still only 2/8 on-topic, and the 3 freed slots surfaced comparably off-topic Deva-keralam content rather than better content. None of the 6 clean books (BPHS, Phaladeepika, Saravali, Cheiro, Lal Kitab) surface for Saturn-11th queries. Confirms retrieval relevance is a separate workstream from dedup, not fixed by it.
4. Path (c) validation: 4 Q&A queries against Sheridan's Saturn-11th AstroSage paragraph (Q1 definitional, Q2 mechanism, Q3 cross-placement, Q4 compound stress case probing the documented Deva-keralam 11th/12th-from-ascendant corpus gap). Primary-signal results: Q1 clean 3/3; Q3 nominally 3/3 but the citation is factually mis-paginated (verified against the actual retrieved chunks); Q2 failed on voice degradation (self-help register); Q4 failed on voice AND silently dropped the Moon-in-Aries clause instead of giving the honest-gap answer the stress test was designed to elicit. Honest primary-signal pass rate: 1/4. All three failure modes (voice drift, confident mis-citation, silent sub-clause omission) are LLM-behavior-layer, independent of retrieval quality. Path (c) does not ship as designed. Verdict locked.
5. V1 scope decision: LLM-generated interpretive Q&A is OUT for V1. AstroSage paragraph is terminal; palm reading is primary; the deterministic calculation engine (Mahadasha lookups, Chandrabala, Tarabala, etc.) is V1's only structured Q&A surface — no LLM synthesis in that path.

Decisions locked this session:
- Path (b) eliminated (AstroSage prose-shape instability).
- Path (c) selected for testing, then invalidated by its own validation run (1/4 honest primary-signal pass rate against the locked rubric).
- Path (a) deferred to V1.1, pending corpus rebuild + natal-context redesign.
- V1 scope: LLM-generated interpretive Q&A OUT; AstroSage terminal; palm primary; calculation engine is the only structured V1 Q&A surface.
- Calculation roadmap UNPAUSED. P2.2.3 transit_aspects remains paused (no architectural need for it under the V1 scope decision); next session resumes at P2.3 Muhurta per the existing locked P2 order.

Test baseline: 623 passed / 3 skipped (Session 22 close) -> 626 passed / 3 skipped (+3 new embedder hardening tests, `tests/test_embedder.py`). Zero regressions.

Open items carried forward:
- Path (a) extract-then-annotate one-shot test with full natal context — research question, not V1 critical path.
- Deterministic Q&A on structured calculation data — possible V1.1 addition once Muhurta and Gochara ship.
- Deterministic template-fill (no LLM in interpretive layer) — V2 destination, multi-month corpus engineering.
- Path (c) prompt iteration — open option but not recommended given confident-incorrectness failure modes; extends V1 timeline materially.
- Rubric hardening for any future Q&A test — citation-content-accuracy verification required, not just presence. Q3's result is the textbook case.
- `run_single_book.py` re-merge input validation (scrapped from Session 23 as off critical path).
- `run_overnight.py` twin gap (same vulnerability, different script).
- OCR garbage cleanup (single-char chunks, the `|` group of 18).
- Corpus gap inventory on 11th/12th-from-ascendant and similar holes — flagged by the path (c) retrieval result.
- Enable PowerShell command-line history persistence (`Set-PSReadLineOption -HistorySaveStyle SaveIncrementally`) so the next incident is forensically reachable.
- AstroSage anchor convention corroboration on a second date (open since Session 21).
- Sade Sati systematic delta pattern investigation (5-min when a time-stamped oracle is available).
- `helpers/ephemeris.py` extraction (still stub).
- `SadeSatiWindow` range-scan API (P2.2.2b).
- Sulabh and David transit fixtures (Surbhi/Sheridan only currently active).

Next session entry point: P2.3 Muhurta answer-engine (highest user-value-per-session ratio per the Session 20 scope-calibration exercise; directly validates the post-(c) product thesis as deterministic structured-data Q&A).

## Session 24 — P2.3.1 + P2.3.2 Chandrabala (in progress)

**Date:** 2026-06-21/2026-06-22
**Phase tag:** P2.3.1 Chandrabala (instant primitive) — CLOSED; P2.3.2 Chandrabala (range-scan) — CLOSED. Session not yet closed.

Work completed:
1. P2.3.1 design proposal executed (read-only, no code) — investigated `calculations/` package structure, `gochara.py`/`sade_sati.py` conventions, the PVR PDF, and the test-fixture pattern. Headline finding: PVR's book contains **no section named "Chandrabala"** anywhere (zero hits across 515 pages). The functionally equivalent favorable-house data exists under Ch.26 §26.3 "Rasi Gochara Vedha" Table 63's Moon row (general transit theory), NOT in PVR's own dedicated Muhurta chapter (Ch.36), which names only Tarabala as a muhurta limb. Surfaced 7 open questions for Sulabh plus one Architect-vs-Critic conflict (import `gochara.compute_gochara()` vs. an independent minimal helper), resolved in favor of the independent-helper precedent.
2. P2.3.1 `compute_chandrabala()` implemented in `agent/calculations/transits/chandrabala.py`: binary FAVORABLE/UNFAVORABLE classification, enum {1,3,6,7,10,11} locked from PVR Table 63's Moon row, Janma-Rashi (house 1) folded into FAVORABLE and surfaced via `is_janma_rashi`, sign convention 0-11 (matches `sade_sati.py`, deliberately not `gochara.py`'s 1-12), independent `_moon_sign()` helper (no cross-module dependency on `gochara.compute_gochara()`), vedha-sthana mechanism explicitly deferred to V1.1 (P2.3.1b) mirroring `sade_sati.py`'s Small Panoti precedent. 9 tests, 3 fixtures (Sulabh canonical anchor, Sulabh Janma-Rashi, David cross-chart), all computed programmatically.
3. `transits/__init__.py` conflict caught and resolved: the implementation prompt asked to add re-exports to `transits/__init__.py`, directly contradicting the Session 21 locked convention (empty `__init__.py`, no re-exports, "normalized back to this shape after briefly deviating") — re-verified all 11 `calculations/` subpackages are currently empty. Flagged via a question rather than silently complying or silently skipping; Sulabh confirmed keeping `__init__.py` empty. Callers use direct module imports throughout.
4. P2.3.2 `find_chandrabala_windows()` range-scan implemented in the same file: bisection-based discrete-state window detection (Skyfield `almanac.find_discrete` pattern, reimplemented locally against pyswisseph — skyfield itself is not a dependency); two internal-only constants (`_COARSE_STEP_JD`=0.5 JD/12h, justified by Moon's ~13°/day speed vs. 30° sign width; `_BISECT_TOL_JD`=1e-6 JD/~0.09s); no caller-facing step/precision parameters; bisects on the full (category, is_janma_rashi, house_from_natal_moon) triple (mathematically equivalent to bisecting on Moon sign ingress alone, since house_from_natal_moon is a bijective function of transit sign for fixed natal sign); no retrograde-double-ingress handling needed — the Moon never retrogrades, unlike Saturn in `sade_sati.py`. 11 tests: 3 fixtures (Sulabh 7-day, Sulabh 30-day spanning a Janma-Rashi entry, David 7-day cross-chart) plus contiguity/coverage/frozen-dataclass/bisection-convergence unit tests.
5. Epistemic check on Fixture 1: all 3 detected boundaries differ from a naive fixed-step (0.5 JD grid) estimate by 8.3-11.4 hours — confirms the bisection is load-bearing, not cosmetic.
6. Committed and pushed: commit `7d4ec2e` (`44cb935..7d4ec2e` on `origin/main`), 3 files, 726 insertions.

Decisions locked this session:
- Favorable-house enum {1,3,6,7,10,11} sourced from PVR Ch.26 §26.3 Table 63 Moon row — corroborates but is NOT the same source as PVR's own Muhurta methodology (Ch.36), which names only Tarabala. Chandrabala implemented as the mainstream Muhurta-lineage criterion (AstroSage/Drik Panchang/Muhurta Chintamani convention), with PVR Table 63 as independent corroboration.
- Janma-Rashi (house 1) is part of the FAVORABLE bucket, surfaced via `is_janma_rashi: bool`, not a separate category.
- Binary category only (FAVORABLE/UNFAVORABLE); NEUTRAL explicitly deferred to V1.1 — applies to both the instant primitive and the range-scan.
- Vedha-sthana (obstruction) mechanism deferred to V1.1 (P2.3.1b), both instant primitive and range-scan.
- Sign convention split acknowledged and accepted: `chandrabala.py` uses 0-11 (`sade_sati.py` convention); `gochara.py`'s 1-12 convention untouched, not refactored.
- `transits/__init__.py` stays empty (no re-exports) — re-confirmed the Session 21 lock after a conflicting instruction was caught and Sulabh confirmed keeping it empty.
- `_bisect_transition` takes an explicit `classify` callable parameter (beyond the literal signature given in the P2.3.2 prompt) to make it independently unit-testable; mirrors `sade_sati.py`'s existing `_refine_boundary(jd_a, jd_b, in_target: Callable)` precedent.

Files shipped:
- `agent/calculations/transits/chandrabala.py` — `compute_chandrabala()`, `ChandrabalaStatus`, `ChandrabalaCategory`, `find_chandrabala_windows()`, `ChandrabalaWindow`, `_moon_sign()`, `_bisect_transition()` (commit `7d4ec2e`)
- `tests/calculations/transits/test_chandrabala.py` — 9 tests (commit `7d4ec2e`)
- `tests/calculations/transits/test_chandrabala_windows.py` — 11 tests (commit `7d4ec2e`)

Test baseline: 626 passed/3 skipped (Session 23 close) -> 646 passed/3 skipped (+20: 9 instant-primitive + 11 range-scan; zero regressions).

Open items carried forward:
- P2.3.1b vedha-sthana mechanism (deferred V1.1, both instant primitive and range-scan).
- NEUTRAL category for 2nd/5th houses (deferred V1.1, per the P2.3.2 prompt's own locked-decisions list).
- **P2.3 sub-sequence numbering collision**: "P2.3.2" was used for two different things across this conversation — Tarabala (per the original P2.3.1→P2.3.2→P2.3.3 Chandrabala→Tarabala→Panchaka sub-sequence, quoted as already-locked context in the design-proposal prompt) and Chandrabala's own range-scan (per this session's actual implementation prompt, titled "P2.3.2 Chandrabala range-scan"). Needs reconciling before Tarabala work starts — flag for Sulabh.
- Test file location precedent: `tests/calculations/transits/test_chandrabala.py` was placed nested (mirroring `test_gochara.py`/`test_sade_sati.py`) rather than at the flat `tests/test_chandrabala.py` path one prompt's literal text specified; flagged in that turn's report, not separately re-confirmed by Sulabh.
- All Session 23 carried-forward items (Path (a) interpretive-pipeline research question, RAG corpus gap inventory on 11th/12th-from-ascendant content, ephemeris helper extraction, Sulabh/David transit fixtures for Gochara/Sade Sati specifically, Sade Sati systematic delta-pattern investigation, AstroSage anchor-convention corroboration on a second date, OCR garbage cleanup, PowerShell history persistence) remain untouched.

## Session 24 continued — Muhurta phase P2.3.1, P2.3.2, P2.3.3 shipped; session CLOSED

**Date:** 2026-06-22
**Phase tag:** P2.3.1 Chandrabala instant — CLOSED; P2.3.2 Chandrabala range-scan — CLOSED; P2.3.3 Tarabala instant + range-scan — CLOSED. Session 24 CLOSED. Next: P2.3.4 Panchaka.

Work completed (continuing from the in-progress entry above):
1. P2.3.3 Tarabala implemented in `agent/calculations/transits/tarabala.py`: `compute_tarabala()` instant primitive + `find_tarabala_windows()` range-scan, shipped as a single combined unit since the bisection design pattern was already locked from P2.3.2. 9-tara cycle (Janma/Sampat/Vipat/Kshema/Pratyari/Sadhaka/Vadha/Mitra/Ati-mitra), binary FAVORABLE/UNFAVORABLE, Janma Tara (nakshatra_count in {1,10,19}) UNFAVORABLE. Independent `_moon_nakshatra()` and `_bisect_transition()` (not imported from chandrabala.py). 18 tests across two files (test_tarabala.py instant: 9, test_tarabala_windows.py range: 9), 3 fixtures each (Sulabh canonical anchor, Sulabh Janma-Tara, David cross-chart), all computed programmatically.
2. PVR Ch.36 §36.3 "Basics of Muhurta" (PDF p.484, printed p.472) extracted verbatim: "The nakshatra occupied by Moon at the time of a muhurta should be a good tara with respect to janma nakshatra." Cleaner source-ladder than Chandrabala — Tarabala is endorsed directly in PVR's own Muhurta chapter, not borrowed from a different chapter. Table 79 (PDF pp.485-486) checked for a tara column: none present; it lists task-specific good Nakshatras instead. No classical sub-classification of Janma Tara as activity-dependent found in this passage — binary classification proceeds as locked, no STOP triggered.
3. Internal consistency cross-check: Tarabala windows over the same 7-day Sulabh scan are markedly more granular than Chandrabala's (8 windows vs. 4, since nakshatra divisions (27) cycle faster than rashi divisions (12) over the same ~27.3-day Moon cycle) — confirms the two limbs' relative time-resolution behaves as classically expected.
4. Suite run: 646 passed/3 skipped (P2.3.2 close) -> 664 passed/3 skipped (+18 new, 0 failed, 0 regressions).

Documentation correction found during Session 24 close review: the P2.3.3 implementation report (and a code comment inside `tests/calculations/transits/test_tarabala.py`'s `test_sulabh_canonical_anchor_unfavorable`) mislabeled nakshatra index 10 as "Uttara Phalguni" — per `agent/calculations/core/_panchanga_tables.py`'s `NAKSHATRA_NAMES`, index 10 is **Purva Phalguni** (Uttara Phalguni is index 11). Confirmed by direct table lookup, not left as a "likely typo" guess. Doc/comment-only error — the test asserts on the integer index (10), not the name string, so no test logic is affected. Not fixed in this prompt (doc-only scope this entry); tracked as a backlog item below.

Decisions locked this session (continued, Tarabala-specific — supplements the P2.3.1/P2.3.2 locks already recorded in the entry above):
- Tarabala source ladder: PVR Ch.36 §36.3 directly endorses Tarabala as a Muhurta limb (cleaner than Chandrabala's borrowed-chapter sourcing), but the 9-tara enum and FAVORABLE/UNFAVORABLE split are still mainstream-lineage, not PVR-derived — PVR's text never enumerates the 9 tara names.
- Janma Tara (nakshatra_count in {1,10,19}) is UNFAVORABLE — deliberately the opposite auspiciousness convention from Chandrabala's Janma Rashi (FAVORABLE), reflecting genuinely divergent classical treatment of the two "back on your own natal point" cases, not an inconsistency to reconcile.
- No vedha-sthana analog for Tarabala — Tarabala's classical formulation has no per-tara obstruction column comparable to Chandrabala's PVR Table 63 vedha-sthana column, so nothing is deferred there (a scope difference between the two limbs, not an oversight).
- `_bisect_transition` and `_moon_nakshatra` reimplemented independently in tarabala.py, not imported from chandrabala.py — cross-module-coupling avoidance, same rationale as chandrabala.py's own independent `_moon_sign()` vs. `gochara.compute_gochara()`.
- Generic `discrete_scan` helper extraction explicitly NOT done — two modules (chandrabala.py, tarabala.py) now carry near-identical bisection scaffolding; extraction threshold set at three modules (see CLAUDE.md Locked Decisions).
- `transits/__init__.py` stays empty — untouched this session, re-confirming the Session 21 lock a second time.

Files shipped (Tarabala, this entry):
- `agent/calculations/transits/tarabala.py` — `compute_tarabala()`, `TarabalaStatus`, `TaraName`, `TarabalaCategory`, `find_tarabala_windows()`, `TarabalaWindow`, `_moon_nakshatra()`, `_bisect_transition()`
- `tests/calculations/transits/test_tarabala.py` — 9 tests
- `tests/calculations/transits/test_tarabala_windows.py` — 9 tests

Test baseline: 646 passed/3 skipped (P2.3.2 close, this same session) -> 664 passed/3 skipped (+18: 9 instant-primitive + 9 range-scan; zero regressions).

P2.3 sub-sequence numbering reconciled (resolves the collision flagged in this session's first entry above): P2.3.1 = Chandrabala instant primitive, P2.3.2 = Chandrabala range-scan, P2.3.3 = Tarabala instant + range-scan (combined), P2.3.4 = Panchaka (next). The pre-renumbering sequence quoted in this session's own design-proposal prompt (P2.3.1→P2.3.2→P2.3.3 mapping to Chandrabala→Tarabala→Panchaka, i.e. Tarabala as P2.3.2) is superseded going forward; not retroactively edited in this log's earlier entries, per the standing instruction against rewriting historical entries.

Backlog items retired this session:
- The "Uttara Phalguni" → "Purva Phalguni" mislabel in test_tarabala.py's test_sulabh_canonical_anchor_unfavorable comment (flagged in this same entry above) — fixed immediately after this entry was written; doc-comment-only change, 664 passed/3 skipped/0 failed reconfirmed after the fix.
- Otherwise none confirmed against the written backlog record. (A draft closing brief for this entry proposed retiring the "Sulabh and David transit fixtures" item as covered by Chandrabala/Tarabala's own David fixtures — checked against this log's actual backlog wording (lines recorded at Sessions 21/22/23 close) and found that item is explicitly scoped to Gochara/Sade Sati ("P2.2.x work"), not Chandrabala/Tarabala. Chandrabala and Tarabala shipped with their own Sulabh+David fixtures from their initial design this session — not a retirement of a pre-existing gap. The Gochara/Sade Sati Sulabh+David fixture gap remains OPEN, untouched by this session's work.)

Backlog items added this session:
- Parity infrastructure (PRIORITY): `jhora_parser.py` construction (Phase 0.6, never built); `astrosage_parser.py` extension for Chandra Bala / Tara Bala; manual JHora Chandra Bala parity on the Sulabh canonical fixture (needs UI investigation — transit-time selector independent of birth time); manual JHora Tara Bala parity on the Sulabh canonical fixture.
- V1.1 refinement candidates: ternary enum for 2nd/5th-house NEUTRAL Chandrabala; activity-dependent/conditional Janma Tara classification; vedha-sthana obstruction layer for Chandrabala.
- Test-coverage gaps: frozen-dataclass enforcement test backfill for sade_sati.py and gochara.py (chandrabala.py and tarabala.py already have it). (The "Uttara Phalguni" → "Purva Phalguni" mislabel noted above was fixed same-session, not carried forward — see Backlog items retired.)
- Reference-data hygiene: backfill Sulabh's natal Moon sign/degree + janma nakshatra into `playbook_export/reference/reference_charts.md` (currently only David's chart has a natal Moon entry there; Sulabh's nakshatra was sourced from `kundali_summary.txt` instead during P2.3.1/P2.3.3).
- Generic `discrete_scan` helper extraction once a third range-scan module ships.
- CLAUDE.md trim pass (now 92 lines vs ~80 budget — was already 85 before this session's Locked Decisions additions; flagged by Claude Code Session 24, same pattern as the Session 21 item that was handled in Session 22).

Session close: not committed. Sulabh runs git commands directly per locked working pattern (see the Claude Code report for this entry for the staged commands).

## Session 25 — P2.3.4 Panchaka (CLOSED)

**Date:** 2026-06-22
**Phase tag:** P2.3.4 Panchaka — CLOSED.

Work completed:
1. `agent/calculations/transits/panchaka.py` (303 lines) implemented: `compute_panchaka(jd_ut) -> PanchakaStatus`, `find_panchaka_windows(start_jd, end_jd) -> list[PanchakaWindow]`, binary `PanchakaCategory` enum, frozen dataclasses, local `_bisect_transition` (third module carrying this duplicated helper, after chandrabala.py and tarabala.py). No natal parameter anywhere on the public surface -- Panchaka is not natal-relative, unlike Chandrabala/Tarabala.
2. `tests/calculations/transits/test_panchaka.py` (113 lines, 7 tests) and `tests/calculations/transits/test_panchaka_windows.py` (147 lines, 9 tests) shipped.
3. Suite run: 664 passed/3 skipped (Session 24 close) -> 680 passed/3 skipped (+16 new, 0 failed, 0 regressions).

Decisions locked this session:
- Panchaka V1 = Definition B (Moon sidereal longitude in [300, 360) degrees, Aquarius + Pisces). Binary IS_PANCHAK / NOT_PANCHAK only.
- Source: Muhurtha-Chinthamani p.84-85. Verified this session against the project's own RAG corpus (`data/all_chunks.json`, chunks `Muhurtha-Chinthamani_p84_c2` / `p85_c0` / `p309_c1` / `p309_c2` / `p310_c0` -- OCR'd from `data/pdfs/Muhurtha-Chinthamani.pdf`), not a fresh direct PDF read; flagged here per the project's citation-honesty convention rather than overstating the verification method.
- Threshold note: the passage gives both the round-sign framing ("Moon in the Ascendants of Aquarius and Pisces" = [300, 360) degrees, Definition B, implemented) and the nakshatra-pada-exact framing (Dhanishtha's 3rd pada, ~293°20', through end of Revati, Definition A, NOT implemented) in the same breath, treating them as equivalent glosses rather than competing definitions. The ~6°40' gap between the two is acknowledged, not reconciled, and documented in `panchaka.py`'s module docstring as a risk-accepted V1 simplification.
- Three V1.1 deferrals documented: named-type overlay (Raj/Agni/Chor/Mrityu/Rog Panchak by entry weekday), Panchaka Rahita as a wholly separate future module, and Definition A's round-degree refinement.
- Methodology lock: design-proposal-first is NOT the default going forward -- earned only when (a) classical sources are genuinely ambiguous post-agent-pass, (b) the module structurally differs from existing precedent, (c) fixtures require pre-implementation ephemeris computation, or (d) the API shape is uncertain (full criteria recorded in CLAUDE.md's Locked Decisions). Default is a direct implementation prompt -- this session went straight to implementation with no separate design-proposal pass, the first P2.3.x module to do so.

Files shipped:
- `agent/calculations/transits/panchaka.py`
- `tests/calculations/transits/test_panchaka.py` -- 7 tests
- `tests/calculations/transits/test_panchaka_windows.py` -- 9 tests

Test baseline: 664 passed/3 skipped (Session 24 close) -> 680 passed/3 skipped (+16: 7 instant-primitive + 9 range-scan; zero regressions).

Backlog items retired this session:
- Generic `discrete_scan` helper extraction is now the ACTIVE next task, not backlog -- `panchaka.py` is the third module carrying a duplicated `_bisect_transition` (chandrabala.py, tarabala.py, panchaka.py), crossing the Session 24-locked extraction threshold.

Backlog items added this session:
- `helpers/discrete_scan.py` extraction (NOW DUE -- next task): refactor chandrabala.py / tarabala.py / panchaka.py to import a shared bisection helper.
- Named-type Panchak overlay (V1.1): Raj/Agni/Chor/Mrityu/Rog classification requires a Panchak-entry-vara backward scan plus a location/timezone parameter.
- Panchaka Rahita module (V1.1+): separate file `transits/panchaka_rahita.py`; function of (Tithi, Vara, Nakshatra, Udaya Lagna); Andhra/Telangana intraday classifier; oracle drikpanchang.com/muhurat/panchaka-rahita-muhurat.html. Do NOT conflate with `panchaka.py`.

Next session entry point: Session 26 -- `helpers/discrete_scan.py` extraction (refactor chandrabala.py / tarabala.py / panchaka.py to import the shared helper). Then P2.3.5 Muhurta composite scorer.

Session close: committed and pushed as commit `23f0c31` on `origin/main` (`89cd330..23f0c31`).

## Session 26 — helpers/discrete_scan.py extraction + deterministic geocoder fixture

**Date:** 2026-06-22
**Phase tag:** helpers/discrete_scan.py — CLOSED; conftest geocoder monkeypatch — ADDED

Work completed:
1. `helpers/discrete_scan.py` extracted: generic `StateSegment[T]` + `find_state_segments()` bisection range-scan helper, after a caller audit confirmed all three transit modules' `_bisect_transition` implementations match on boundary semantics, constant-state behavior, near-boundary transitions, inverted/empty windows, and exception propagation. 10 new structural/synthetic-state tests in `tests/calculations/helpers/test_discrete_scan.py`. Callers migrated as three follow-up commits (Tasks C/D/E): chandrabala.py, tarabala.py, panchaka.py all refactored to import `find_state_segments` and delete local `_bisect_transition`. `_BISECT_TOL_JD` removed from all three callers (absorbed into the helper); `_COARSE_STEP_JD` retained per-caller since step size is caller-specific.
2. Deterministic geocoder fixture added: session-scoped autouse `_patch_geocoder` in `tests/conftest.py`, backed by `_FakeNominatim` reading from `tests/fixtures/geocoded_locations.json`. Eliminates live Nominatim calls during pytest (was ~26 HTTP calls/run; triggering HTTP 429s on repeated full-suite runs). No agent/ edits; no fall-through to live geocoding on a fixture miss (KeyError on cache miss). Verified 3x back-to-back byte-identical.

Decisions locked this session:
- `find_state_segments()` is the public surface; `StateSegment[T]` (frozen dataclass) is the return element. The `classify` callable is `Callable[[float], T]`. Boundary semantics: bisects until `|jd_b - jd_a| < tol`; tolerance absorbed into the helper, not exposed to callers.
- All three transit modules now delegate to the shared helper — the Session 24-locked "extract at third module" threshold was met and acted on promptly.
- `tests/conftest.py` monkeypatch is session-scoped autouse; no individual test needs an explicit fixture argument.

Files shipped:
- `agent/calculations/helpers/discrete_scan.py` — `StateSegment`, `find_state_segments()`
- `tests/calculations/helpers/__init__.py`
- `tests/calculations/helpers/test_discrete_scan.py` — 10 tests
- `tests/conftest.py` — `_patch_geocoder` autouse fixture, `_FakeNominatim`
- `tests/fixtures/geocoded_locations.json` — 4 birthplace geocode cache entries
- `agent/calculations/transits/chandrabala.py`, `tarabala.py`, `panchaka.py` — refactored (no new tests; 689/3 confirmed after each migration)

Test baseline: 680 passed/3 skipped (Session 25 close) → 689 passed/3 skipped (+9 net: 10 new discrete_scan unit tests, minus 1 net change from refactor verification; zero regressions).

Session close: committed and pushed across 5 commits (`f1facd5`…`d6d43ba`) on `origin/main`.

## Session 27 — P2.3.5 Muhurta composite scorer

**Date:** 2026-06-23
**Phase tag:** P2.3.5 Muhurta composite scorer (instant + range-scan) — CLOSED. P2.3 Muhurta engine CLOSED.

Work completed:
1. `agent/calculations/transits/muhurta_scorer.py` implemented: `compute_muhurta_score(jd_ut, natal_moon_sign, natal_nakshatra) -> MuhurtaScore` composes Chandrabala, Tarabala, and Panchaka into a four-tier classification (TIER_1 through TIER_3 + PANCHAKA_VETO). Tier logic: Panchaka IS_PANCHAK overrides to TIER_3 unconditionally (veto); otherwise Chandrabala + Tarabala favorable-count drives TIER_1/TIER_2/TIER_3. 16 tests in `tests/calculations/transits/test_muhurta_scorer.py` (structural, Sulabh + David fixtures, tier boundary isolation). 705 passed/3 skipped after instant scorer.
2. `find_muhurta_windows(start_jd, end_jd, natal_moon_sign, natal_nakshatra) -> list[MuhurtaWindow]` added to same file: uses interval algebra over the three sibling limb finders (union of their window boundaries, midpoint-scored via `compute_muhurta_score`) rather than a new ephemeris scan. 13 new tests in `tests/calculations/transits/test_muhurta_windows.py` (Sulabh/Surbhi/David fixtures + mechanical unit tests). 718 passed/3 skipped after range-scan addition.
3. JHora v8 reference data for Sulabh's canonical chart parked (commit `1ff9fc1`) for future parity validation of the composite scorer.

Decisions locked this session:
- Interval algebra over sibling finders (not a new ephemeris scan) is the locked composition pattern for `find_muhurta_windows()` — avoids duplicating the Moon's position computation and guarantees the composite window boundaries are exactly the union of the limb boundaries.
- Panchaka IS_PANCHAK is a hard veto (always TIER_3), not a soft modifier — preserves the classical "avoid entirely" semantics.
- `MuhurtaScore` and `MuhurtaWindow` are frozen dataclasses; tier enum is `MuhurtaTier`.

Files shipped:
- `agent/calculations/transits/muhurta_scorer.py` — `compute_muhurta_score()`, `find_muhurta_windows()`, `MuhurtaScore`, `MuhurtaWindow`, `MuhurtaTier`
- `tests/calculations/transits/test_muhurta_scorer.py` — 16 tests
- `tests/calculations/transits/test_muhurta_windows.py` — 13 tests

Test baseline: 689 passed/3 skipped (Session 26 close) → 718 passed/3 skipped (+29; zero regressions).

Session close: committed and pushed as commits `8a31271`, `1ff9fc1`, `cd2e685` on `origin/main`.

## Session 28 — P2.4.0 through P2.4.2 Ashtakoot 8-koota compatibility engine

**Date:** 2026-06-23/2026-06-24
**Phase tag:** P2.4.0 Ashtakoot tables — CLOSED; P2.4.1a/b/c koota calculators — CLOSED; P2.4.2 composite scorer — CLOSED.

Work completed:
1. P2.4.0 `_ashtakoot_tables.py` (498 lines): all lookup tables for 8 kootas (Varna, Vashya, Tara, Yoni, GrahaMaitri, Gana, Bhakoot, Nadi) + `KOOTA_SCORE_WEIGHTS`. Structural invariants tests in `test__ashtakoot_tables.py` (360 lines). `compatibility/__init__.py` and `tests/calculations/compatibility/__init__.py` created.
2. P2.4.1a `trivial.py` (200 lines): Varna, Vashya, Tara, Gana calculators (pure table lookup over nakshatra/moon_sign inputs). `KootaNatalInfo` + `KootaResult` frozen dataclasses in `koota_types.py`. `test_trivial.py` (319 lines) + AstroSage reference fixture file `tests/fixtures/astrosage_sulabh_surbhi_kundli_milan.md`.
3. P2.4.1b `sign_lord.py` (269 lines): Graha Maitri and Bhakoot calculators. Bhakoot cancellation matrix locked: 6/8 pair cancels when both signs share a lord (Aries/Scorpio via Mars, Taurus/Libra via Venus, Gemini/Virgo via Mercury, Capricorn/Aquarius via Saturn); 2/12 pair cancels when lords are mutual friends. Navamsa-based cancellation pathway deferred to V1.1. `test_sign_lord.py` (324 lines).
4. P2.4.1c `matrix.py` (47 lines): Yoni and Nadi calculators. Nadi V1 = table lookup only (AstroSage parity confirmed on all 4 reference pairs); classical cancellation rules for Nadi (same gotra, same nakshatra exceptions) deferred to V1.1 pending AstroSage ground-truth on which rule set they apply. `test_matrix.py` (146 lines). Delhi geocode entry added to `tests/fixtures/geocoded_locations.json`.
5. P2.4.2 `ashtakoot.py` (134 lines): `compute_ashtakoot_compatibility(boy, girl) -> AshtakootResult` composite scorer over all 8 kootas. Dosha detection (Nadi_Dosha, Bhakoot_*_Dosha). Interpretation bands: ≥26 Excellent, ≥18 Preferable, ≥12 Marginal, <12 Not Preferable. `AshtakootResult` frozen dataclass added to `koota_types.py`. `test_ashtakoot.py` (223 lines): AC-1 Sulabh×Surbhi AstroSage full-parity (27.5/36, Preferable, all 8 per-koota scores locked), AC-2/AC-3 Nadi+Bhakoot dosha fixtures, AC-4 cancellation case, AC-5 Marginal band, structural invariant tests.

Decisions locked this session:
- Sign convention 0-11 (0=Aries) throughout compatibility package.
- Frozen dataclasses for all result types (FrozenInstanceError on mutation).
- `calculate_chart()` key structure: `["planetary_positions"][planet]["sign"]` → sign string; `["lagna_chart"]["ascendant"]` → Lagna sign string (confirmed by reading chart_calculator.py).
- Three-tier source hierarchy: AstroSage parity > PyJHora > classical anchor; AstroSage wins on contested cells.
- AC-3 Pair 3 total provisionally logged as 5/36 (AstroSage oracle); at time of writing, the code produced 6/36 — noted as a possible transcription slip, pending root-cause investigation (carried forward as a known discrepancy, not resolved this session).

Files shipped:
- `agent/calculations/compatibility/_ashtakoot_tables.py`, `koota_types.py`, `trivial.py`, `sign_lord.py`, `matrix.py`, `ashtakoot.py`
- `tests/calculations/compatibility/test__ashtakoot_tables.py`, `test_trivial.py`, `test_sign_lord.py`, `test_matrix.py`, `test_ashtakoot.py`
- `tests/fixtures/astrosage_sulabh_surbhi_kundli_milan.md`, `tests/fixtures/geocoded_locations.json` (Delhi entry added)

Test baseline: 718 passed/3 skipped (Session 27 close) → ~991 passed/3 skipped (293 new tests across 5 test files; zero regressions).

Session close: committed and pushed across 7 commits (`5a342fa`…`2d8878d`) on `origin/main`.

## Session 29 — P2.4.3 Gana table fix (AstroSage parity) + P2.4.5 Mangal Dosha

**Date:** 2026-06-27
**Phase tag:** P2.4.3 GANA_SCORE fix — CLOSED; P2.4.5 Mangal Dosha — CLOSED.

Work completed:
1. Diagnostic investigation (scratchpad-only, no file changes): confirmed Pair 3 (6 Mar 1995 × 19 Feb 1995, Delhi 12:00 IST) is a Manushya×Rakshasa cell; raw `GANA_SCORE[("Manushya","Rakshasa")]` was 1; AstroSage oracle gives 5/36 total only if that cell is 0. Classical majority (AstroVed, AstroBix) gives 1; AstroSage gives 0. Per the locked three-tier source hierarchy (AstroSage > classical majority), the table value was wrong.
2. TASK 0 (test-first): `test_gana_score_full_matrix_astrosage_parity_locked()` added to `test_trivial.py` — exhaustiveness test over all 9 GANA_SCORE cells, collects all mismatches into a dict for one-shot failure reporting. Confirmed exactly 2 failures before the fix (Manushya×Rakshasa and Rakshasa×Manushya), zero after.
3. TASK 1 (table fix): `GANA_SCORE[("Manushya","Rakshasa")]` and `[("Rakshasa","Manushya")]` changed from 1 to 0 in `_ashtakoot_tables.py`. Gana section docstring rewritten: removed the prior incorrect AstroSage-agrees-with-1 claim; added empirical evidence from Pair 3; documented the classical-majority vs. AstroSage divergence; noted Manushya-Rakshasa=0 now tied with Deva-Rakshasa=0, consistent with "death ≥ quarrel."
4. TASK 2 (AC-3 fixture): test renamed `test_ac3_pair3_bhakoot_and_nadi_dosha_verified_total_5_of_36`; assertion changed `total_score 6.0 → 5.0`; `result.kootas["Gana"].score == 0.0` assertion added; module docstring "AC-3 NOTE" rewritten — retracted prior "transcription slip" conclusion, documented root cause as a genuine table defect now corrected.
5. TASK 3 (regression): full suite 1011 passed/3 skipped — Sulabh×Surbhi total still 27.5, all previously passing tests pass.
6. P2.4.5 `agent/calculations/compatibility/mangal_dosha.py` (187 lines): `compute_mangal_dosha(chart_data) -> MangalDoshaResult`. Mars in {1,2,4,7,8,12} from any of Lagna/Moon/Venus (whole-sign house arithmetic). V1 cancellation rules: C1 (Mars own sign: Aries/Scorpio), C2 (exalted: Capricorn), C3 (debilitated: Cancer), C5 (Jupiter conjunct or 5th/7th/9th Whole Sign aspect), C7 (Lagna Cancer or Leo, Yogakaraka). Excluded from V1: C4 (movable sign — fragmented sources), C6 (mutual Manglik — two-chart concern, caller-level only), navamsa-based rules, age-28 rule. `MangalDoshaResult` frozen dataclass (has_dosha, dosha_triggers, cancellations, is_cancelled, details, warnings).
7. `tests/calculations/compatibility/test_mangal_dosha.py` (222 lines): 20 tests across 4 layers — A (structural/constant/house-arithmetic, no ephemeris), B (AstroSage parity via `calculate_chart()`: Sulabh no-dosha, Surbhi no-dosha, Pair1-boy has-dosha "Low Mangal Dosha", Pair1-girl no-dosha), C (cancellation isolation: C1/C2/C3/C5-conjunction/C5-aspect/C7-cancer/C7-leo/no-cancellation-fires), D (no-dosha cases). All 20 passing.

Decisions locked this session:
- GANA_SCORE Manushya×Rakshasa = 0, locked to AstroSage parity (over AstroVed/AstroBix classical majority of 1). Root-cause evidence from Pair 3 AstroSage oracle.
- Mangal Dosha Whole Sign house arithmetic: `_house_from(mars_sign, ref_sign) = ((mars_sign - ref_sign) % 12) + 1`.
- C5 Jupiter aspect formula: `((jupiter_sign - mars_sign) % 12) + 1 in {5, 7, 9}` (equivalent to asking whether Jupiter's 5th/7th/9th Whole Sign aspect lands on Mars).
- C6 mutual Manglik is a two-chart concern; `MANGAL_CANCELLATION_C6_MUTUAL_MANGLIK` sentinel exported for callers (future ashtakoot.py integration point).
- V1 severity classification (Low/Medium/High) deferred to V1.1 — `is_cancelled` (boolean) only in V1.
- `_SIGN_TO_IDX` dict within mangal_dosha.py for string→int conversion; no shared sign-conversion helper imported cross-module.
- Test-first discipline applied: gana exhaustiveness test written and confirmed failing before the table fix, then confirmed passing after.

Files shipped:
- `agent/calculations/compatibility/_ashtakoot_tables.py` — GANA_SCORE fix + docstring
- `tests/calculations/compatibility/test_trivial.py` — exhaustiveness test added
- `tests/calculations/compatibility/test_ashtakoot.py` — AC-3 fixture updated
- `agent/calculations/compatibility/mangal_dosha.py` — P2.4.5 (new)
- `tests/calculations/compatibility/test_mangal_dosha.py` — 20 tests (new)

Test baseline: ~991 passed/3 skipped (Session 28 close) → 1011 passed/3 skipped (+20 Mangal Dosha tests +1 Gana exhaustiveness test −1 AC-3 was not deleted just renamed; net +21 but some previously failing AC-3 assertion is now corrected; zero regressions on Sulabh×Surbhi total 27.5).

Session close: committed and pushed as commit `cbabe76` on `origin/main` (`2d8878d..cbabe76`).

## Session 30 — P2.5 Shadbala: Fixture + Sthana Bala

### What landed
- P2.5.0: tests/fixtures/shadbala_fixtures.py — 4 charts × 7 planets,
  32 smoke tests, virupa/rupa consistency verified across all 28 cells.
- P2.5.1: agent/calculations/strength/sthana_bala.py — all 5 Sthana Bala
  sub-components (Ochcha, Saptavargaja, Ojayugmarasyamsa, Kendra, Drekkana).
  D2/D3/D7/D12/D30 varga calculators built inline as private functions
  tagged # TODO: extract to calculations/vargas/ once ≥2 consumers exist.
- CLAUDE.md: "Known Source Divergences (V1)" section added — Saptavargaja
  and Drekkana Bala gaps documented with spec source, delta, user impact,
  revisit trigger.

### Key decisions (locked, carry forward)
1. Saptavargaja scoring: BPHS 27.2-4 literal (Mooltrikona=45, Own=30,
   Pramudita=20, Shanta=15, Din=10, Duhkhita=4, Khala=2). AstroSage
   Saptavargaja fixture values are INFORMATIONAL — AstroSage uses an
   unpublished table not reverse-engineerable from public data. All 7
   planets' AstroSage Saptavargaja assertions collapsed to informational
   comments; sthan_total tolerance widened to abs=40.
2. Drekkana Bala: 1 Virupa flat constant (AstroSage+JHora convergence wins
   over BPHS 27.6 binary 15/0).
3. Acceptable gap protocol (locked this session): every accepted divergence
   must be written to CLAUDE.md + test file comment + module docstring
   CITATION block before session closes. SESSION_LOG.md alone is
   insufficient — Claude Code cannot read it at prompt time.
4. Pre-prompt research discipline (locked this session): design chat must
   project_knowledge_search existing repo before drafting any Claude Code
   prompt. Duplicate friendship table in P2.5.1 first draft cost ~75k
   tokens — avoidable with one search.

### Test baseline
1119 passed, 3 skipped, 0 failures.

### Next task
P2.5.2 Dig Bala — directional strength. AstroSage fixture values are
primary oracle (published, no source divergence expected).

## Session 31 — P2.5.2 Dig Bala + Master Plan Reconciliation

### What landed
- P2.5.2: agent/calculations/strength/dig_bala.py — Directional strength
  for all 7 classical planets. True sidereal MC via swe.houses_ex (not
  Lagna+270°); documented in module docstring. Locked: Sun/Mars → MC,
  Mercury/Jupiter → ASC, Moon/Venus → IC, Saturn → DSC.
- tests/calculations/strength/test_dig_bala.py — 13 tests (Layer A
  structural formula, Layer B Sulabh all-7-planets AstroSage parity,
  Layer C Surbhi Sun spot-check). 13/13 passed.
- "ASTRO AGENT — MASTER BUILD PLAN.md" — 6 surgical edits:
  (1) ACTUAL STATE block (1119 baseline, all completed phases);
  (2) Phase 0 dissolved with locked rationale;
  (3) Phase 0.6 JHora Parser tracked;
  (4) CHECKPOINT thin-slice pipeline block after Phase 1;
  (5) Validation cadence + 75-80 session revised estimate added to
      dependency graph;
  (6) Closing sentence updated.

### Key decisions (locked, carry forward)
1. Dig Bala uses true sidereal MC from swe.houses_ex, NOT Lagna+270°.
   At non-equatorial latitudes the approximation breaks Sun parity
   (verified on Sulabh, Calcutta 22.5°N). Documented in module docstring
   and now in SESSION_LOG.
2. saturn dig fixture = 4.64 (confirmed correct). The spec inline doc
   had a copy-paste error (56.49 = surbhi.moon.dig). Test reads fixture
   directly — was never wrong.
3. Thin-slice answer pipeline checkpoint: after P2.5 Shadbala completes
   and Phase 1 (Bhava Bala + Ishta/Kashta) completes, build a 3-domain
   router (marriage/career/dasha) BEFORE starting Phase 2 vargas.
   Locked in Master Plan.
4. chart_profile schema build deferred to just-in-time before Calc
   Router (Phase 10 prep), not Phase 0.

### Test baseline
1132 passed, 3 skipped, 0 failures.

### Next task
P2.5.3 Kala Bala (temporal strength) — most complex Shadbala component:
Nathonnatha, Paksha, Thribhaga, Abda, Masa, Vara, Hora, Ayana, Yuddha.
JHora fixture in tests/fixtures/jhora_sulabh.md; AstroSage fixture in
tests/fixtures/shadbala_fixtures.py. Pre-prompt research required:
search jhora_sulabh.md for Kala Bala values before drafting.

## Session 38 — P2.5.6 Drik Bala (investigation closed) + P2.5.7 shadbala_totals (2026-06-30)

### What landed
- P2.5.6: agent/calculations/strength/drik_bala.py — investigation closed.
  PyJHora `__drik_bala_calc_1` kernel ported and validated sessions 36-37:
  7/7 on Surbhi, 4/7 on Sulabh. Moon (+16.4) and Venus (+7.7) diverged from
  both AstroSage and JHora despite those two oracles agreeing closely —
  confirmed real formula gap, not classical ambiguity. Two kernel variants and
  two Moon benefic/malefic classification approaches tried and rejected. Stub
  locked at 0.0 all planets for V1.
- P2.5.7: agent/calculations/strength/shadbala_totals.py — full aggregator.
  Sums Sthana, Dig, Kala, Chesta, Naisargika, Drik (0.0 stub) per planet;
  converts to Rupas; ratio against BPHS minimum requirements; rank 1-7 by
  virupa descending (stable sort, _PLANETS iteration order tie-break).
  Mandatory `drik_is_stubbed: bool` and `caveat: str` on every planet output
  — not optional, not silent.
- tests/calculations/strength/test_shadbala_totals.py — 153 tests, all
  passed. Layers A-F: NAISARGIKA_BALA constant (BPHS 60/7 series), component
  pass-through tolerance (sthan_total ±40, dig ±0.5, kala_total Sulabh-only
  ±2/6, chesta per-planet ±1–41), aggregator arithmetic correctness (virupa =
  sum of own components, not fixture totals which include real Drik Bala),
  rank validity (complete permutation + Sulabh closest-pair tie-gap check),
  caveat/stub integrity, error propagation.
- CLAUDE.md: "Known Source Divergences (V1)" updated — Drik Bala entry
  expanded with investigation closure and V1.1 path; new Kala Bala
  cross-chart Abda/Masa divergence entry added (Jupiter/Saturn Surbhi ±31/±59
  Virupa cross-chart gap surfaced during totals Layer B testing).

### Key decisions (locked, carry forward)
1. Drik Bala stubbed at 0.0 V1. DO NOT re-attempt kernel port without new
   source material (AstroSage formula or untested `__drik_bala_calc_1_pvr`).
   Fitting parameters against fixture output is a rejected pattern.
2. shadbala_totals.py Layer C arithmetic test uses the aggregator's own
   computed component fields (not fixture shadbala_virupa), because the
   fixture includes real Drik Bala which our stub cannot match. This is the
   only correct way to test aggregator arithmetic without re-solving Drik Bala.
3. Sheridan/David remain excluded from cross-chart assertions (birth data
   "unknown" precedent, same as test_chesta_bala.py and test_sthana_bala.py).
   NOTE: David_Kundli.pdf actually contains full birth details (19 Jan 1976,
   22:00, London) — flagged for review, not yet activated as a test chart.
4. Surbhi kala_total for Jupiter/Saturn diverges ±31/±59 Virupa from
   AstroSage fixture (Hora/Masa Bala day-specific differences not validated
   by test_kala_bala.py cross-chart). Documented in CLAUDE.md §Kala Bala
   cross-chart entry. Not re-opened proactively.

### Test baseline
1380 passed, 4 skipped, 0 failures.

### Next task
Phase 1: Bhava Bala + Ishta/Kashta Bala. After both complete, build the
thin-slice answer pipeline (3-domain router: marriage/career/dasha) before
starting Phase 2 vargas — locked in Session 31 key decision 3.

## Session 39 — Sheridan/David birth data activation (2026-06-30)

### What landed
- tests/fixtures/shadbala_fixtures.py: Sheridan and David meta blocks
  updated from "unknown" placeholders to real birth data, extracted
  directly from their AstroSage PDF "Basic Details" pages:
    Sheridan: 1984-05-27, 08:00, Durban, South Africa
    David: 1976-01-19, 22:00, London, UK
- Both place strings confirmed already present in
  tests/fixtures/geocoded_locations.json — no new live geocoding needed.
- test_chesta_bala.py: activated test_c2_david_moon_krishna_chesta;
  replaced skip stub with real david_chesta module fixture. Delta 0.003
  vs fixture, within ±1.0 tolerance.
- test_shadbala_totals.py: added sheridan_totals/david_totals/all_totals
  module fixtures; expanded _ALL_CHART_KEYS constant; promoted Layers
  C/D/E from 2-chart to 4-chart parametrize; added 14 sheridan/david
  rows to test_c_min_required_exact.
- CLAUDE.md: Current Session Focus updated to 1461 total; new "Shadbala
  Chesta Bala — Layer B cross-chart scope" entry added to Known Source
  Divergences; Validation oracles note updated with Sheridan/David status.
- SESSION_LOG.md and Master Build Plan updated (this entry).
- Test baseline: 1380 → 1461 passed (+81), 3 skipped, 0 failures.

### Key decisions (locked, carry forward)
1. test_chesta_bala.py Layer B (tight AstroSage-parity tolerance) stays
   Sulabh + Surbhi only — Sheridan/David activated at Layers C/D/E
   (structural/rank/caveat) only. STOP documented as diagnostic attempt #1
   in CLAUDE.md Known Source Divergences; not pursued further.
   Specific deltas that triggered the STOP:
     Sheridan Sun:     computed 113.33, fixture  52.05, delta +61.28 (tol ±41)
     Sheridan Mercury: computed   8.00, fixture  21.53, delta −13.53 (tol ±10)
     David Mercury:    computed   2.44, fixture  55.64, delta −53.20 (tol ±10)
     David Venus:      computed  12.23, fixture  22.43, delta −10.20 (tol ±10)
2. Precedent confirmed: meta "unknown" placeholders in shadbala_fixtures.py
   should be checked against source PDFs before being treated as a
   permanent data gap. Session 38 key decision 3 flagged David's real data
   as activatable; Session 39 executed that activation for both charts.

### Test baseline
1461 passed, 3 skipped, 0 failures.

### Next task
P3 Yoga detection engine — Pancha Mahapurusha yogas first.

## Session 42 — Phase 1 CLOSED: Bhava Dig Bala stub → real (2026-07-01)

### What landed
- Bhava Dig Bala moved from V1 stub to real implementation, across a
  3-prompt sequence:
  1. Implementation prompt — `compute_bhava_dig_bala` rewritten against
     PyJHora's `strength.py::_bhava_dig_bala` (rasi-animal-group discrete
     taper on Porphyry/Sripati cusps, NOT the Session 41 equal-house
     hypothesis that was tested and rejected). Blocked mid-prompt on a
     signature conflict (real Dig Bala needs jd_ut/lat/lon-derived cusps;
     the stub's `house_signs`-only signature can't carry them) — resolved
     via a design-chat decision to add `compute_porphyry_house_cusps()`
     to `chart_calculator.py` and thread a `house_cusps` param through
     `compute_bhava_dig_bala`/`compute_bhava_bala_totals`, deliberately
     leaving the 7 (actually 8, corrected on recount) now-broken test call
     sites unfixed for the next prompt.
  2. (Folded into prompt 1's design-chat, not a separate prompt): verbatim
     re-extraction of the exact rasi-group longitude boundary constants
     from PyJHora's `const.py`, after an earlier investigation report had
     paraphrased/summarized them and corrupted a value — caught before
     implementation, not after.
  3. Fixture + test rewrite prompt — blocked once more: the prompt asked
     for an "AstroSage-sourced" fixture file, but no such source data
     existed anywhere in the repo and the PDF-read path was non-functional
     (see new CLAUDE.md entry, "PDF-read tooling gap"). Resolved via a
     design-chat decision: user transcribed the 4 charts' AstroSage
     Bhavdig Bala tables directly into chat. `tests/fixtures/
     bhava_dig_bala_astrosage.py` created citing that provenance;
     `test_bhava_bala.py` Layer F/H rewritten against the new signature
     (8 broken call sites fixed, not the originally-estimated 6); new
     48-case exact-match parametrize sweep (4 charts × 12 houses) plus a
     dedicated hardest-case-first test for Sulabh's two AstroSage zeros
     (houses 4 and 7) ahead of the general sweep.
- Result: 48/48 exact match, all 4 charts, first run, no tolerance band
  needed (rasi-group taper only produces clean multiples of 10).
  `multi_match_houses` (a new field surfacing an upstream PyJHora
  last-write-wins quirk) returned empty on all 4 charts — untested by
  real data, flagged in CLAUDE.md rather than assumed safe.
- CLAUDE.md: Bhava Dig Bala entry marked RESOLVED; Drik Bala and Bhava
  Drishti Bala entries updated (stub status unchanged, but their shared
  revisit-trigger kernel `__drik_bala_calc_1_pvr` is now located and
  extractable — deliberately not actioned, per the Session 31 sequencing
  lock); new PDF-read tooling gap entry added.
- Master Build Plan: Phase 1 (Bhava Bala + Ishta/Kashta) marked CLOSED,
  with Bhava Drishti Bala noted as a deliberate, documented stub within
  the closed phase — not an open item blocking closure.

### Methodology note — fingerprint-first investigation (template for future stuck sessions)
When a formula is genuinely unknown and a prior direct-port attempt has
stalled (as Drik Bala did, sessions 36-37), this session's 4-step sequence
resolved Bhava Dig Bala where the Session 41 direct-hypothesis approach
had failed:
  1. **Fingerprint the target output BEFORE reading source code.** AstroSage's
     Bhavdig Bala values were all clean multiples of 10 across all 4 charts
     — this alone ruled out a continuous-arc formula and pointed at a
     discrete/tiered one, before any PyJHora code was opened.
  2. **Verbatim-extraction-only, never paraphrase-and-summarize.** A first
     investigation pass summarized PyJHora's formula in prose and silently
     corrupted a boundary constant, producing a false negative on House 1.
     A dedicated re-extraction prompt requesting exact literal source lines
     (not a re-summarization) caught and fixed this before implementation.
  3. **Hand-verify 1-2 points before implementing at scale**, per Working
     Style #2 (SAMPLE before SCALE) — Sulabh's houses 4 and 7 (the two
     AstroSage zeros) were checked by hand against the extracted formula
     before writing the full 12-house/4-chart implementation.
  4. **Implement, then validate exhaustively** — 48/48 exact match, not a
     sampled subset, once the formula was locked.
Reference this session as the template for any future Drik Bala /
Bhava Drishti Bala V1.1 attempt, or any other stalled-investigation module.

### Test baseline
1495 → 1664 passed (+169: +120 in test_bhava_bala.py's full run, remainder
from suite-wide re-collection with the new fixture import), 3 skipped,
3 xfailed (unchanged — the 3 known Ishta/Kashta Sun cases).

### Next task
Thin-slice answer pipeline checkpoint (3-domain router: marriage/career/
dasha) — per Session 31 key decision 3 and the Session 42 handover.
Pre-prompt research required before drafting the implementation prompt
(unchanged scope from prior handovers; not superseded by this session's
Bhava Dig Bala work, which was itself the last blocking item ahead of it
per the Session 31 lock).

## Session 45 — Thin-slice answer pipeline CHECKPOINT CLOSED (2026-07-03)

### What landed
- `agent/infra/result_formatter.py` (S44.4) — pure deterministic
  DomainChartProfile -> DomainAnswer formatter for the 3 pipeline
  domains (marriage/career/dasha). No LLM calls.
- `agent/infra/orchestrator.py` (S44.5) — single entry point
  `answer_question()` wiring route_question() -> build_domain_profile()
  -> format_answer() -> Option A demotion merge (router and formatter
  demotion signals overlaid, concatenated with " | " when both fire).
- `tests/infra/test_orchestrator_e2e.py` — 16 real-chart integration
  tests, no mocks (4 career + 4 dasha + 1 marriage + 5 refusal + 2
  error handling). Uncovered and fixed 3 spec-vs-code mismatches along
  the way (Ashtakoot koota dict keys are Title-case not snake_case;
  MangalDoshaResult is a dataclass with `has_dosha`, not a dict; the
  Surbhi fixture birth data given in the task prompt didn't match the
  canonical Surbhi used everywhere else in the repo and didn't
  reproduce the task's own hardcoded total_score==27.5 assertion).
- `chart_profile.py` patched — marriage payload keys renamed
  `mangal_dosha_primary`/`mangal_dosha_partner` -> `mangal_dosha_boy`/
  `mangal_dosha_girl` (role-resolved via `primary_role`, since
  DomainChartProfile carries no primary_role field of its own); career
  payload gained a `tenth_lord` key (resolved by matching
  `house_lord_mapping`'s `"house" == 10` entry, not by list-indexing —
  `house_lord_mapping` is a list of 12 dicts, not a dict keyed 1-12).
- `calc_router.py` bug fixed — `current_dasha` was demoting every
  answer to TIER_2_RANGE unconditionally; now demotes only when
  `_near_dasha_boundary()` is True (or chart_data is absent), matching
  the ±37-day AD drift's actual scope (mid-period lord ID has zero
  ambiguity). Caught via the e2e suite's diagnostic prints (all 4
  reference charts showed identical TIER_2_RANGE regardless of
  boundary proximity).
- CLAUDE.md compressed 175 -> 76 lines across two passes: Locked
  Decisions cut from 22 bullets to 5 + a pointer line; Known Source
  Divergences cut from 12 entries to 8 one-liners; Chunk Metadata
  Schema section moved out entirely. Archive section created at the
  top of this file (see "Archived from CLAUDE.md" above) preserving
  every moved item verbatim — nothing deleted.
- Item C spot-check closed — Saturn AD (7/8/92) visually confirmed
  against JHora desktop; the 324-point dasha fixture is oracle-grade.

### Dogfood scorecard (2 entries captured this session)
- "How strong is my career potential?" -> refused (1 keyword hit,
  below calc_router.py's 0.4 confidence floor).
- "Are we compatible?" -> refused (marriage_compatibility/
  career_strength tie at 0.333 each, below the 0.15 margin).
Per the Router refuse-heavy posture lock (CLAUDE.md): scorecard data
for future `_STEM_MAP`/threshold tuning, not treated as bugs. Tune
only once enough scorecard evidence accumulates.

### Test baseline
1664 -> 1680 passed (+16, exactly the new e2e suite), 3 skipped, 3
xfailed (unchanged — the 3 known Ishta/Kashta Sun cases).

### Next task
Session 46 entry point: POST-CHECKPOINT PHASE ORDER item (a) — Drik
Bala extraction. Pre-gate: hand-verify Sulabh Moon + Venus Drik Bala
values from JHora desktop before any implementation prompt is drafted.
Abort gate: 2 attempts max; 7/7 planets within ±0.5 Virupa on BOTH
Sulabh AND Surbhi, or the stub stays at 0.0.

## Session 46 — Drik Bala SOLVED: stub → real, 28/28 JHora parity (2026-07-04)

### What landed
- drik_bala.py: real implementation. BPHS Ch.28 Sphuta Drishti kernel
  (triangulated: Scribd DRISTI doc + B.V. Raman Art.114 + PyJHora) +
  Raman Art.120 aggregation (Drishti Pinda/4) + smooth-taper corrections
  at 3 BPHS segment boundaries (Saturn 60-90: 90-D/2; Jupiter 120-150:
  2*(150-D); Jupiter 210-270: D/2-60 then 420-3D/2), each back-computed
  from a single divergent JHora pair then cross-validated.
- Classification: Moon benefic iff 90<=elongation<270 (Ashtami-to-
  Ashtami, classical — not paksha; Session 32/38 paksha attempts were
  the actual root cause of prior failures). Mercury: same-rasi count
  INCLUDING Moon. Sheridan was the exposing edge case (elongation
  319.67, Mercury sharing Moon's rasi) — initial ship was 2/7 there.
- test_drik_bala.py: 86 tests (kernel boundary continuity, 28-point
  JHora parity all 4 charts, error contract).
- Stale-stub cleanup chain: shadbala_totals.py (drik_is_stubbed=False,
  Ayana-envelope caveat), test Layer E, chart_profile.py (20.0→6.0
  general envelope + caveat-gate fix), calc_router.py (envelope-driven
  career demotion reason), test_orchestrator_e2e.py (6.0 + sentinel).
- CLAUDE.md: Drik Bala divergence entry replaced; Ayana Bala
  re-investigation lock LIFTED with pre-gate; baseline bumped. 77 lines.

### Key decisions locked
1. Career stays TIER_2 despite real Drik Bala — residual envelopes
   (±6 Ayana general, ±59 Surbhi Kala) still make exact ranks dishonest.
   Revisit T1 after Ayana investigation.
2. uncertainty_virupa 6.0 = Ayana Moon/Venus envelope only; honest-scope
   tuning note in chart_profile.py.
3. AstroSage parity NOT expected on Drik Bala — genuine JHora-vs-
   AstroSage divergence (Sulabh Saturn 17.46 vs 10.89). JHora primary.
4. Mars 180-210 plateau: continuity-derived, zero data coverage, open.
5. Methodology validated: back-solve single divergent pairs against
   oracle, one principle (boundary continuity), zero free parameters —
   distinct from the rejected parameter-fitting pattern.

### Bugs caught mid-session
- Shipped v1 Mercury classification excluded Moon from same-rasi count
  AND hardcoded Moon always-benefic — 2/7 on Sheridan. Both fixed via
  4-combination back-solve before any speculation committed.
- Prompt 3e fallout miscounted (3 expected, 4 actual — Surbhi shares
  the chart-agnostic demotion string).

### Test baseline
1766 passed, 3 skipped, 3 xfailed.

### Next task
Ayana Bala investigation, Drik-style. Pre-gate: read-only convergence
diagnostic — JHora fixture kala_bala_breakdown Ayana vs AstroSage
fixture Ayana vs computed, all 7 planets, Sulabh (+ Surbhi if breakdown
exists). Sun doubling/inversion (~40 Virupa via Sun Chesta) primary
target; Moon/Venus ±5-6 secondary. Multi-source validation planned
(user will supply sources Claude cannot access).

## Session 49 — P7.0 golden-set eval harness + router findings (2026-07-05)

### What landed
- **P7.0a** — `agent/eval/golden_harness.py` + `agent/eval/__init__.py`:
  drives every RUNNABLE row of `tests/fixtures/golden_qa_sulabh.py`'s
  GOLDEN_QA through the real `answer_question()` pipeline, writes a
  markdown scorecard to `diagnostics/`. No LLM calls, read-only golden
  data.
- **P7.0b** — `calc_router.py`'s `_UNBUILT_MODULE_KEYWORDS` scan switched
  from plain substring containment to word-boundary regex
  (`\b{keyword}s?\b`) — golden row `sulabh_dasha_r4_exact_date` exposed
  "transition"/"transitional" false-positiving on keyword "transit".
  Full suite unaffected (1769 passed, 0 failed both before/after).
- **P7.0c** — design-chat reversal of the Session 45 conditional-demotion
  behavior: `current_dasha` now ALWAYS resolves TIER_2_RANGE (was
  TIER_1_EXACT mid-period, TIER_2_RANGE only within the ±37-day boundary
  window). Rationale: the payload always carries Mahadasha/Antardasha
  boundary DATES, which always carry the documented ±37-day drift
  regardless of evaluated_at position — tier is a property of the
  answer's claims, not the evaluation moment. `_near_dasha_boundary()` /
  `_DASHA_BOUNDARY_WINDOW_DAYS` kept, repurposed to select between two
  demotion_reason wordings (dates-only vs identity-also-uncertain) rather
  than whether to demote at all. Golden rows q11/q12/q13/r4 flipped
  TIER_1_EXACT → TIER_2_RANGE (all MATCH now).
- **P7.0d** — `test_orchestrator_e2e.py`: tightened
  `_assert_dasha_answer_shape`'s `tier in {T1, T2}` set-membership check
  (which would have silently passed a T1 regression) to
  `tier == TIER_2_RANGE` + a `"37-day"` demotion_reason substring check.
  Added `test_dasha_boundary_reason_selection` (+1 test, monkeypatches
  `calc_router._near_dasha_boundary` to lock both reason-wording branches
  without coupling to wall-clock boundary proximity). 1770 passed net.
- **P7.0e** — `_KNOWN_GAPS` reconciliation: deleted 3 dead entries
  (q11/q12/q13, made dead by P7.0c). Added a 5th row category,
  DESIGN_DEBT (checked after MATCH, before KNOWN_GAP), seeded with
  exactly one entry (`sulabh_dasha_q14` — Sade Sati refused via
  `_UNBUILT_MODULE_KEYWORDS` despite `sade_sati.py` being built and
  4-chart validated; this is product debt, not a locked decision, unlike
  q15/Muhurta which is genuinely unwired).
- **P7.0f** — read-only router-tuning evidence dump,
  `diagnostics/router_tuning_evidence_20260705_041121.md`: verbatim
  keyword lists/thresholds/scoring formula, per-row keyword-hit trace for
  all 10 refused golden rows, q14 Sade-Sati hypothetical. No code changed.

### Key findings for next session (verbatim)
(a) 9/10 golden refusals are single-hit confidence-floor, 0 margin-ties.
(b) "job" keyword is dead code — `_STEM_MAP` key collision routes it into
    the phrase-match branch, never matches (only "job" is affected; it's
    the sole `_STEM_MAP` key that's also a literal `_DOMAIN_KEYWORDS`
    entry).
(c) q14 unblocking requires: keyword removal (drop "sade sati" from
    `_UNBUILT_MODULE_KEYWORDS`) + dasha-domain sade-sati terms (so it
    scores confidently) + `chart_profile.py` payload fields (Sade Sati
    status/dates) + a formatter render path + a T1 sub-path
    (payload-property-consistent with the P7.0c dasha-tier principle —
    i.e. tier still keyed to what the payload actually claims).
(d) q10 (TIER_4_INTERPRETIVE) and q15 (TIER_3_MUHURTA) are unreachable by
    design — this pipeline never produces those two tiers at all; golden
    `expected_tier` records design intent, not a gap to close by tuning.

### Test baseline
1770 passed, 3 skipped, 0 xfailed, 0 failed.

### Next task
Hybrid router design session (keyword fast-path + GPT-4o-mini
constrained-classification fallback) — DESIGN IN CHAT FIRST, no
implementation until locked. Combustion thin-slice (PVR orb table)
queued behind router work.