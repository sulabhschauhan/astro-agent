## Session Log

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