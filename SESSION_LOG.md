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

Sessions 19-66 live in \SESSION_LOG_ARCHIVE_S19-S66.md\, split at S81.
This live file holds: the Session 45 compression block and the locked Chunk
Metadata Schema (both below, NEVER archived), then Sessions 67-80.
Any \SESSION_LOG.md S<n>\ citation with n<67 means the archive file.
Note: the archive IS sequential (S19-S66, S32 restored to position at S81), but 34
of 80 sessions have no ``## `` header of their own — grep by content, not by header. Git holds every pre-split byte: \git show <hash>:SESSION_LOG.md\.
Boundary rule: never split above a session still cited by CLAUDE.md.

## Session 67 -- S67 fix-forward queue closed: R1 per-feature retrieval -> R3 support gate/decline -> R2 exemplar rewrite/echo guard (reordered), implementation-ready for Ring 3 pass 3 (2026-07-16)

### Opening probe (`0a738c3`)
`scripts/probe_r1_retrieval.py` (throwaway) ran 29 live queries -- 10
features x 3 template variants + 1 negative control, 0 errors -- to
pick R1's retrieval design before writing any product code. Established
two things used directly in R1/R3 below: the doctrine-interrogative
template ("what does a {quality} {feature} signify...", variant iii)
reliably surfaced doctrine chunks (p.134 life, p.163 fate -- the
inversion-critical page) where RAW field-text queries mostly missed
them; and the 0.30 support-score floor (negative-control ceiling
0.2192, minimum genuine-doctrine score 0.3954 -- 0.30 sits in the empty
band between them, a noise cut only). Rider: removed unconsumed
`data/test_images/Face.jpeg`/`Body.jpeg` (no consuming surface;
Back Hand + palm fixtures untouched).

### Sequencing reorder: R1 -> R2 -> R3 (Session 66 register) became R1 -> R3 -> R2
Design-chat decision, user-confirmed, no dependency violated. R1 alone
(per-feature retrieval, ungated) measurably *increased* fabrication
surface: 28 unique chunks / ~23.7K assembled context vs. the old flat
6-chunk query, because weak features' n=3 slots were often filled by
sub-floor junk (ChromaDB always returns nearest neighbors regardless of
relevance). Gating that context (R3) was judged higher-leverage than
applying a prompt-text-only voice guard (R2) on top of an still-ungated
context, so R3 was pulled ahead of R2.

### R1 -- per-feature doctrine-interrogative retrieval (`8c1b8ab`)
Replaced the single whole-description RAG query with a 10-feature
registry (life/head/heart/fate/sun lines, thumb, fingers, mounts of
Venus/Jupiter, markings/other) and deterministic field parsing (ported
from the probe script, plus a new hand_detail bullet-format parser).
An absence rule skips the query entirely for "not clearly visible"-
style fields; unparseable fields fail OPEN (logged, not dropped -- S23
precedent). n=3/feature, justified from the probe's worst doctrine-
first-hit rank of 2 (+1 margin). Result is an ordered per-feature map
`{feature: [chunks]}`; sources now carry a `feature` tag.
**hand_detail's code-level RAG-exclusion (S66-era, never a formal
CLAUDE.md lock -- see `.claude/read_prompt.md`'s S66 note) is LIFTED**:
its rationale (unreviewed AI output feeding retrieval) died once F1
gave hand_detail a human checkpoint; hand_detail fields are now
first-class registry features. New CLAUDE.md Locked Decision records
this.
Real bug caught during implementation: `_is_absence`'s whole-string
check misfired on MOUNTS' "other mounts are unremarkable" clause,
silently dropping "developed" from mount of venus -- fixed with a
needle-scoped clause extractor, verified against the real pass-2
fixture before writing tests.
Suite: 3177 -> 3183 (+6), zero regressions.

### R3 -- deterministic per-feature support gate (`b6dee9b`)
Needle registry of OCR-robust short forms (the corpus garbles words --
e.g. p.163's "life" OCRs to "hfe"); support = needle-contains AND
score >= 0.30. Chunk-side match is deliberately plain substring, NOT
word-boundary (accepted spec deviation, surfaced via test docstring):
OCR garbling makes word-boundary matching on chunk text unreliable and
would wrongly exclude genuine doctrine -- asymmetric on purpose with
the LLM-output side below, rider comment at `_chunk_supports_feature`
cites the "hfe" example.
LLM-side: system prompt bans discussing any feature outside the
supported set; new word-boundary Ring 1 validator
(`_check_banned_feature_mentions`) catches violations, fed to the
existing F2c retry (hard 2-call cap unchanged, fail-closed). A
Python-owned deterministic decline block (fixed template, no
LLM-authored decline language) is appended before DISCLAIMER for
observed-but-unsupported features; genuine-negative-absence findings
(never observed at all) are exempted from the decline list.
`PalmReadingResult` gains `supported_features`/`unsupported_features`
(registry order); gated (not raw) chunks feed prompt/sources/
context_corpus, so the zero-support path falls out of the existing
`total_chunks == 0` check for free.
Suite: 3183 -> 3192 (+9), zero regressions.

### F5 capture schema completion (`6cce4e6`, between R3 and R2)
Added `retry_used` to the captured ring1_validation block; extended
each captured source line with its `feature` tag; added a
`feature_support` section capturing `supported_features`/
`unsupported_features` verbatim. All additive; existing captured
fields byte-identical in format (pass-2 artifact comparability
preserved). Closes the `frontend/app.py` same-file rider from
Session 66's carry-forward register.
**Correction of record**: the actual capture target is
`diagnostics/dogfood_capture.md` (gitignored, local-only, env-flag
`ASTRO_DOGFOOD_CAPTURE=1`) -- NOT `.claude/read_prompt.md` as an
earlier design-chat prompt stated; `read_prompt.md`'s past `DOGFOOD:::`
content was always the user's manual paste FROM that log, never
written by this function directly. Caught by verifying the actual call
site before editing rather than trusting the prompt's premise.
Suite: 3192 -> 3196 (+4), zero regressions.

### R2 -- exemplar rewrite + exemplar-echo guard (`ffd504f`)
F2c's old model sentences asserted transplantable quality->trait
doctrine ("Such a fate line denotes success won by personal merit" --
the exact pass-2 leak vector, present both quoted and unquoted in the
old prompt text; both instances removed). Replaced with two voice-only
meta-statements containing zero interpretive content:
  - "I have examined many hands in my years of practice, and each one
    tells its own story to those who know how to read it."
  - "The hand rarely lies to the palmist who reads it honestly."
User sign-off on this exact wording: **CONFIRMED (2026-07-16)**.
New deterministic Ring 1 validator: 6-word contiguous n-gram overlap
(normalized: lowercase, punctuation-stripped, whitespace-collapsed)
between reading_text and the exemplar sentences ONLY (never retrieved
chunks -- quoting doctrine is desired behavior). Window justified:
pass-2's confirmed leaked span was exactly 6 words ("denotes success
won by personal merit"). Fed to the same F2c retry.
Bug caught during implementation: the first `_ngrams()` draft returned
a set, so the reported leaked n-gram wasn't deterministically the
leftmost overlap -- caught by the test's own exact-string assertion,
fixed by making the reading-text scan positional (list) while keeping
the exemplar side a frozenset for lookup.
Citation note: "hfe" confirmed via grep against
`diagnostics/ring3_chunks_S66.md`; "palimistry" (also seen in the
original S67 probe report) could NOT be re-confirmed against the
current diagnostics tree -- that probe artifact has since been
overwritten per the standing diagnostics-retention convention. Not a
fabrication on either side; a citation-decay artifact of overwriting
diagnostics files across a multi-prompt sequence. Omitted from the
code comment rather than cited unverified.
Suite: 3196 -> 3200 (+4), zero regressions.

### Test baseline
3177 (S66 close) -> 3183 (R1, +6) -> 3192 (R3, +9) -> 3196 (F5 capture
schema, +4) -> 3200 (R2, +4). Zero regressions at every step. Verified
against each commit, not assumed.

### Commit hashes
Substantive: `0a738c3` (probe), `8c1b8ab` (R1), `b6dee9b` (R3),
`6cce4e6` (F5 capture schema), `ffd504f` (R2).

Docs closeout: `253d85c` ("S67 CLAUDE.md sync").

### Carry-forward resolved this session
- **S67 opening block** (Session 66 register) -- CLOSED. R1 -> R3 -> R2
  all landed and committed (reordered from the original R1 -> R2 -> R3
  register per the sequencing note above; no dependency violated).
  `palm_reading.py` is implementation-ready for Ring 3 pass 3.
- **`frontend/app.py` F5 retry_used rider** (Session 66) -- DONE, see
  F5 capture schema completion above.
- **hand_detail RAG-exclusion** (S66-era code behavior, informally
  noted, never a formal lock) -- LIFTED, see R1 above; recorded as a
  new CLAUDE.md Locked Decision.

### Carry-forward added this session
See CLAUDE.md's Carry-Forward register for the live, actionable list:
T4 status (still NOT ratified-live, exemplar sign-off now satisfied,
pass 2 remains the frozen baseline pending pass 3), Ring 3 pass 3 as
the next action (N=3, fresh uploads), and the `palm_processor.py`
same-file rider recoupled to a future coordinated two-file change
(processor prompt + palm_reading parser) rather than a safe blind
ride-along -- R1 shipped a bullet-format parser tied to
`describe_hand_detail_image`'s current output shape, so the prior
"align to F4 flat-field format" instruction would silently break R1's
hand_detail extraction if executed standalone. V1.1 register unchanged
from Session 66 -- no new items this session.

## Session 68 -- Ring 3 pass 3 pre-flight probe + live 3-run dogfood, SCORED NOT RATIFIED (P7 ratified OK; P1/P4 remain the blockers), S68 fix-forward queue opened (2026-07-18)

### Pre-flight smoke probe (`2da2819`)
`scripts/probe_pass3_preflight.py` (throwaway) ran the full pipeline once
in the Run-C shape (both palms + `Back Hand.jpeg` hand_detail fixture,
live vision + generation) against `data/test_images/`'s sanctioned probe
fixtures -- NOT a Ring 3 scoring run, a wiring smoke check ahead of
spending a live pass on it. All 3 sanity asserts passed: 10/10 registry
features supported, Ring 1 `passed=True` on the final draft, no exemplar
echo. Notable early signal: the p.163 fate-line doctrine chunk (pass 2's
missed-entirely case) surfaced and gated in on this fixture, and every
supported feature carried at least one doctrine-marker hit -- first
concrete evidence the R1/R3 landed work was doing its job before any
real dogfood data existed.

### Pass 3 live dogfood: Runs A/B/C (2026-07-18, `.claude/read_prompt.md`
F5 capture)
Fresh 3-run dogfood, mapped from the F5-captured `## RUN` timestamps:
Run A (`11:34:32`, LEFT+RIGHT only, `retry_used: True`), Run B
(`11:35:40`, identical inputs/regenerate, `retry_used: False` -- the
first clean first draft captured across pass 2 and pass 3), Run C
(`11:38:22`, +HAND_DETAIL, `retry_used: True`).

### Chunk-text evidence dump (`scripts/probe_pass3_chunks.py`, `94ffbe0`)
Read-only reconstruction of the production per-feature retrieval +
support gate against the captured confirmed descriptions, for both input
shapes (LEFT+RIGHT-only and +HAND_DETAIL). Measure-first reconstruction
gate PASSED both shapes (pages/order exact, scores within +/-0.0002 of
captured) before any chunk text was trusted as evidence. Full P1
claim-ledger evidence surface written to
`diagnostics/ring3_chunks_S67_pass3.md`, grouped by feature/registry
order with Run A/B vs. Run C delta separated, plus a deterministic
doctrine-marker lookup (not a judgment) per chunk.

### Scoring: `diagnostics/ring3_palm_rubric_S67_pass3.md` -- **SCORED NOT
RATIFIED**
Four pre-registered adjudication items scored explicitly, all with
verbatim chunk quotes:
- **(a) Run C Jupiter omission** -- CONFIRMED P4 silent-clause-drop
  (supported feature, real doctrine available, confirmed HAND_DETAIL
  observation, never addressed, no decline block since it's not in
  `unsupported_features`). Extended beyond the pre-registered scope: the
  SAME defect independently found on `thumb` in BOTH Run B and Run C
  (verified by full re-read of each `reading_text`) -- only Run A (1 of
  3 runs) actually addresses thumb despite it being `supported` with
  rich doctrine (p.87) in all three. **New failure mode**:
  "supported-but-unaddressed" -- the Python-owned decline mechanism (S67
  R3) only guarantees coverage for features that fail the support gate;
  it cannot and does not guarantee a `supported` feature with real
  evidence actually gets used by the LLM.
- **(b) Thumb wide-angle vs. p.87 doctrine** -- scored C but
  attribution-ambiguous: Run A's claim literally matches p.88's
  formation/size doctrine (the reading's own stated anchor, "well-formed"
  -- design-chat review confirmed this as a D-amplification over the
  confirmed "medium size" wording, same class as pass 1's precedent,
  noted not failed), but if attributed to the confirmed "wide angle"
  observation specifically, p.87's doctrine predicts extremity/
  unmanageability, not "balance" -- an open flag, not silently resolved.
- **(c) Right fate line vs. p.163 wrist->Saturn** -- split verdict: the
  "success" outcome is C (wrist-clause, load-bearing, all 3 runs); the
  "personal ambition/merit" self-determination framing is U (borrows a
  different clause's register without its "rises from the line of life"
  precondition being confirmed) -- a milder recurrence of pass 2's
  doctrine-inversion pattern, now on the correct (visible) line instead
  of the faint one.
- **(d) Fate-line "clearer over time" synthesis** -- scored D-frame, not
  a doctrine claim -- correctly reflects the system prompt's own
  left=innate/right=current convention; flagged as an open question for
  future rubric passes.

**P7 ratified OK** (2026-07-18, design chat) -- user reviewed all three
confirmed descriptions against the actual uploaded photos.

**Scores**:

| Run | P1 | P2 | P3 | P4 |
|---|---|---|---|---|
| A | N | Y | Y | Y |
| B | N | Y | Y | N |
| C | N | Y | Y | N |

No run reaches the 4/4 ratification bar. P1 fails on all three (fingers/
hand-shape/heart-line unsupported-claim pattern -- the fingers claim is
now actively CONTRADICTED by a retrieved chunk, p.98_c1's "erroneous and
misleading," rather than merely unsupported, a sharper finding than pass
2's plain absence). P4 fails on B and C via the thumb/Jupiter
supported-but-unaddressed pattern above.

**Progress vs. pass 2**: P3 (voice) continues to hold clean across all
three runs -- F2c's retry mechanism remains the confirmed carrier of that
fix. Life line and Mount of Venus grounding went from
unsupported/absent-doctrine (pass 2, U on all 3 runs for Venus) to
consistently load-bearing C rows in all three pass-3 runs -- concrete
evidence the R1 per-feature retrieval redesign is doing real work, not
just restructuring the failure. The remaining P1 gap has narrowed in
scope but sharpened in character (contradiction, not mere absence), and
a genuinely new failure mode (P4 supported-but-unaddressed) emerged that
neither pass 1 nor pass 2 surfaced.

Also recorded during scoring (design-chat review notes, not scoring
inputs): Run B's `retry_used: False` is a single data point, not a
trend -- do not cite it as evidence of generation-quality improvement
without a larger sample; the S66 pre-flight probe's 3/3 retry-fired
sample remains the only rate-level evidence that exists.

### Test baseline
No production code touched this session -- pre-flight probe, chunk-
evidence dump, and scoring artifact are all diagnostics-only (throwaway
scripts + committed `.md` reports). Suite unchanged from Session 67's
close: **3200 passed, 3 skipped.**

### Commit hashes
Substantive: `2da2819` (pre-flight probe), `94ffbe0` (chunk-text evidence
dump + `probe_pass3_chunks.py`), `e6ff977` (pass-3 scoring artifact,
initial DRAFT). Dogfood-capture commits (`.claude/read_prompt.md` F5
capture-log updates, not individually narrated): `d8d2f5a`, `3d390cd`,
`b2fa408`.

Docs closeout: this commit ("S68 close-out: Ring 3 pass 3 NOT RATIFIED +
S68 queue").

### Carry-forward resolved this session
- **Ring 3 pass 3** (Session 67 register) -- RESOLVED in the narrow
  sense: the pass ran (N=3, fresh uploads) and has been SCORED. T4
  remains NOT ratified-live -- an open verdict, not an open
  pass-existence gap; see CLAUDE.md's updated T4 status line.
- **F5 `retry_used` capture gap** (pass 2's Known Gap) -- RESOLVED.
  `retry_used` is now per-run hard data (captured directly in each RUN
  block), no longer inferred from a separate pre-flight sample.

### Carry-forward added this session
See CLAUDE.md's Carry-Forward register for the live, actionable list:
the S68 fix-forward queue (F-C claim-level grounding design + heart-
line/fingers retrieval gap probe, design chat first -- gates F-A, a Ring
1 supported-feature coverage validator with a landmark-exclusion rule;
F-B, a small `_ABSENCE_PHRASES` regex broadening, can land anytime; F-D,
a design debate on per-feature source scoping vs. `p134_c2`-class query
drift), and a new V1.1 register item (golden fixture rows with
`baseline_source: "astrosage_kp_2026-07"` carrying two uncorrected
capture errors -- Ketu-Sun antardasha mislabeled as Venus Mahadasha,
10th lord stated as Moon vs. computed Mercury). Not duplicated here per
the Session 62 diagnostics-retention convention -- CLAUDE.md is the
single live copy.

### S68 addendum -- AstroSage-PDF coverage audit, V2 decision gate, CLAUDE.md slim (2026-07-18)

**Coverage audit** (`diagnostics/astrosage_coverage_audit_S68.md`, via
throwaway `scripts/probe_astrosage_coverage.py`): the live 7-keyword
`astrosage_parser.py` splitter matches 6/7 of its own targets (misses
`Transit Today` on the audited PDF); a full raw-text pass surfaced the
PDF's actual taxonomy at 31 sections across 56 pages. Classified against
V1's 8 routed domains: 3 COVERED-CALC (Vimshottari Dasha, Sade Sati
table, ShadBala/BhavBala Table -- each cross-checked directly against
`chart_profile.py`, not assumed), 10 COVERED-PARTIAL, 13 NOT-COVERED, 3
OUT-OF-SCOPE-LOCKED, 2 N/A (cover pages). One correction against the
audit brief's own example categorization: Lal Kitab reclassified
OUT-OF-SCOPE-LOCKED (not NOT-COVERED as the brief's example suggested),
since CLAUDE.md's T4 lock states it is actively withheld at display
(same mechanism as Pratyantar), not merely unbuilt.

**Design-chat ruling**: AstroSage PDF stays V1 (no replacement scoped
this session). New CLAUDE.md Locked Decision, "V2 decision gate": a
future V2 interpretive template layer is scoped to the audit's
COVERED-PARTIAL sections first (calculable-but-uninterpreted content),
classical-corpus-sourced, deterministic placement-keyed, no serve-time
LLM -- design work on it pends F-C's claim-level grounding discipline
landing first (same gating logic as F-A, see the S68 fix-forward queue).

**CLAUDE.md slim**: 126 -> 117 lines (task brief cited 132 as the
pre-slim count; verified against the actual file before editing, not
transcribed). Rule followed: compress, never relocate -- Locked
Decisions, Known Source Divergences, and Working Style left untouched
(dense, precisely-worded, high risk of meaning drift if reworded; the
task's own "when in doubt, keep the original sentence" clause applied).
All reduction came from the Carry-Forward register: dropped 2
fully-resolved items with SESSION_LOG-documented resolutions (`answer_
question()` Stage 2 client injection seam, resolved Session 64 Part A;
the "S67 sequence CLOSED" bullet, redundant with the T4 status line
above it), removed one stray mid-list blank line, and merged 5 pairs/
groups of thematically-related still-open items into single bullets
(misc small ride-alongs; arudha_lagna internals; stale-prose refreshes;
router-tuning backlog; palm_reading.py S65 flags) with no fact dropped
-- every file/session/trigger citation survives, just restructured as
sub-clauses. 80 lines was not honestly reachable without rewording
protected content; reported transparently rather than forced.

**Register additions**: 3 new items folded into the consolidated V1.1
register bullet (splitter coverage broadening, naming the missed
`Transit Today` keyword; a dogfood `## RUN`-block copy-by-timestamp
script to remove Ring-3 scoring's manual paste-from-`read_prompt.md`
friction, low priority) -- both net-new this addendum, plus the
already-standing `astrosage_kp_2026-07` fixture item, all still open.

### Carry-forward resolved this session (addendum)
- `answer_question()` Stage 2 client injection seam (Session 59) --
  verified RESOLVED at Session 64 Part A ("Stage 2 client injection
  seam added"); the CLAUDE.md bullet had gone stale (never removed at
  the time) and is dropped as part of this slim.
- S67 sequence CLOSED bullet -- dropped as redundant with the T4 status
  Locked-Decision-adjacent carry-forward line, which already carries
  the current state.

### Carry-forward added this session (addendum)
See CLAUDE.md's Carry-Forward register (post-slim) for the live list --
not duplicated here per the Session 62 retention convention. Headline
new items: V2 decision gate (Locked Decisions), splitter coverage
broadening + dogfood RUN-block script (V1.1 register).

### S68 addendum -- F-C close-out: A1 chunk-anchored generation lands (2026-07-19)

**F-C arc in brief.** Two diagnostics-only probes first: a retrieval
matrix (`scripts/probe_fc_retrieval.py`, `diagnostics/fc_retrieval_probe_S68.md`,
`f25c67d`) and a heart-line corpus lookup (`scripts/probe_fc_heartline_corpus.py`,
`diagnostics/fc_heartline_corpus_S68.md`, `bfdf62f`). Findings: a
candidate variant-iv query template (pure-Python clause assembly, vs.
the production variant-iii `_build_feature_query`) REJECTED -- it
degraded both probed features' target-chunk ranks (fingers: rank 1 ->
3; life line: ranked 2/5 -> not in top 10), so the baseline template +
n=3 were retained unchanged; and a genuine corpus gap on the heart-line
chapter (p.157-158 have zero chunks; positive-configuration doctrine at
p159_c2/p160_c1 never ranks in retrieval for this feature). Both probes
are read-only, no production code touched.

With the design question answered (claim-level grounding = the tagging
contract itself, not a stricter prompt or a claim-type drop list), A1
landed across four source commits + one test-alignment commit:
`73dc0a5` (chunk-anchored generation contract + strip layer),
`30b19ed` (Ring 1 V-1/V-2 anchor validators), `7934233` (test-suite
alignment + V-1/V-2 coverage), `61088c4` (Ring 1 input-surface split --
display checks on stripped text), `91b2b25` (F5 capture extension:
tagged reading + `ring1_failures` + anchor denominator).

**One incident, logged not hidden**: `30b19ed` was pushed to main
mid-sequence with a red suite (17 tests failing -- every pre-A1
`_FakeClient` test stub predated the new tagging contract). Per
CLAUDE.md's "NEVER REWRITE PUSHED HISTORY ON MAIN" lock (Working Style
#13), this was resolved fix-forward with a NEW commit (`7934233`)
rather than amended -- the suite was red on main for the span between
those two commits, not silently rewritten away. Suite: **3200/3 ->
3213/3** (net +13, all new V-1/V-2 coverage; zero regressions once
`7934233` landed).

Close-out itself (this addendum's own commit, "S68 F-C close-out:
3-place registrations + register updates", docs/docstrings/comments
only, zero logic changes): registered 5 accepted gaps at all 3 places
(CLAUDE.md, code-site comment, module docstring) -- V-2 union-only
citation scoping (ratified final, covered by a new Ring 3 pass-4
anchor-fidelity spot-check rubric row), V-1's sandwich boundary,
the heart-line corpus gap, `CHUNK_ANCHOR_TAG_PATTERN`'s id-schema
coupling, and the F5 capture's `valid_chunk_ids_count: unavailable`
gap (pass-4's real denominator comes from a reconstruction probe
instead). F-A (Ring 1 supported-feature coverage validator,
landmark-exclusion rule) is now UNBLOCKED. Two new V1.1 register
items: corpus re-ingestion/chunk-repair (with a rider to revisit the
id-schema coupling in the same change), and promoting `valid_chunk_ids`
onto `PalmReadingResult`.

### S68 addendum -- F-A close-out: supported-feature coverage check lands (2026-07-19)

**F-A arc in brief.** Disposition prompt first: ratified the coverage
check's shape as retry-feed + fail-open, with two amendments made
explicit before implementation -- (1) coverage-only misses feed the
SAME single F2c retry a Ring 1 failure would (no new mechanism, same
2-call hard cap), and (2) the warnings surfacing on `ValidationReport`
are computed against whichever draft actually SHIPS (the final draft,
not the first draft's stale result) and gate Ring 3 pass-4 scoring
("a warning-bearing run cannot score P4 clean") without ever blocking
display.

Implementation landed clean on the first pass -- `_check_feature_
coverage` (pure chunk_id anchor-intersection against `gated_results`,
landmark-exclusion enforced BY CONSTRUCTION since `[OBS]` tags
contribute nothing to the cited set) plus the `ValidationReport.
warnings` additive field and the retry/fail-open wiring in `generate_
palm_reading()`, all correct against the design on first read.

**One behavioral test break, caught before commit, not after.** Full
suite run surfaced 1 failure: `test_exactly_one_llm_call_when_first_
draft_passes` asserted exactly 1 LLM call, but its stub (`_CLEAN_STUB_
TEXT`, entirely `[OBS]`-tagged) left both its observed features
uncited, so the new coverage-only retry correctly fired a second call
-- not a shape break (no positional `ValidationReport` construction
anywhere in the repo, confirmed by grep), a genuine behavioral
consequence of the new mechanism the stub predated. Per the
instructing prompt's own STOP branch (test alignment is explicitly the
next prompt, mirroring F-C's precedent), implementation was reported
and left uncommitted rather than silently patched inline.

**Test alignment.** Grepped every `completions.calls) ==`/`retry_used
is False` assertion in the Ring 2 file (13 + 2 hits) and traced each
one's actual supported/cited shape by hand -- only the one test broke;
every other coverage-triggered silent retry landed on a test that
either already expected a retry for an unrelated reason or never
asserted call count at all. Fixed with a dedicated `_TWO_FEATURE_CHUNK`
/ `_CLEAN_TWO_FEATURE_STUB_TEXT` pair (not an edit to the shared
`_CLEAN_STUB_TEXT`, which ~9 other tests depend on unmodified) --
deliberately exploits the shared-chunk accepted-gap mechanism as the
fix: one chunk carrying both needles, gated under both features, cited
once. Added 7 new tests: 4 direct `_check_feature_coverage` proofs
(never-cited warning verbatim, `[OBS]`-only landmark exclusion,
cited-clean, shared-chunk false-positive) + 2 `generate_palm_reading()`
integration tests (coverage-only retry fires and clears; fail-open
final still warns but displays) + 1 `ValidationReport` default-field
check. Suite: **3213/3 -> 3220/3** (net +7, zero regressions).

**Two-commit single-push discipline** (F-C incident lesson applied,
not repeated): Commit A (`d54c968`, the already-correct implementation)
and Commit B (`afe6b4f`, test alignment) both landed locally, full
suite re-verified green against the committed state, THEN one `git
push` carried both -- main was never red remotely at any point, unlike
F-C's `30b19ed` mid-sequence red-push incident.

**Close-out itself** (this addendum's own commit, "S68 F-A close-out:
gap f registration + register updates", docs/docstrings/comments only,
zero logic changes): registered a 6th accepted gap at all 3 places
(CLAUDE.md, `_check_feature_coverage`'s own docstring, module
docstring) -- the shared-chunk false-positive boundary, RATIFIED FINAL
with the same disposition as gap (a) (backstopped by the same Ring 3
pass-4 human anchor-fidelity spot-check, not a future validator).
CLAUDE.md's S68 fix-forward queue now reads F-C and F-A both COMPLETE;
F-B/F-D remain queued, unblocked, undebated; Ring 3 pass 4 is the next
gate, requiring fresh palm uploads plus a design-chat go before
scheduling.

### S68 addendum -- F-B close-out: absence-phrase regex broadening lands (2026-07-19)

**F-B arc in brief.** Small, surgical, one implementation commit
(`d01401a`, "S68 F-B: absence-phrase regex broadening"). `_is_absence()`
(`palm_reading.py`) went two-tier: TIER 1 (`_ABSENCE_PHRASES`) is the OLD
6-phrase fixed-substring list, unchanged in content, recompiled as
`re.escape`d case-insensitive regex (byte-identical matching). TIER 2
(`_ABSENCE_PATTERNS_BY_FEATURE`, new) adds per-feature `no <0-3 filler
words> <noun> <0-6 filler words> visible` patterns, sourced from
`_SUPPORT_NEEDLES` -- the SAME single source of truth already used for
chunk-relevance needles, not a second, separately-maintained noun list.

**The islands-needle near-miss, caught by per-feature anchoring, not
luck.** Before touching the fix, ran the design's own stated
false-positive risk against real captured text, not a synthetic case:
LEFT's actual LIFE/HEAD/HEART LINE fields all read "...no breaks,
chains, forks, or islands visible" -- and "islands" is a literal
`markings/other features` needle. A feature-agnostic "no...visible"
match would have wrongly flagged all three clean, PRESENT lines as
absent. Per-feature noun anchoring (checking each feature against ONLY
its own needle -- "life"/"head"/"heart", none of which appear in that
clause) correctly keeps all three unmatched, confirmed by direct
interpreter probe before running classification, not assumed from the
design alone.

**Evidence-surface catch, not assumed.** The instructing prompt pointed
at `.claude/read_prompt.md` for the RUN-block evidence. Reading the
current file found it overwritten by an unrelated later commit (a Sade
Sati question, `2bb2e44`) -- the real F5 capture data lives in
`diagnostics/dogfood_capture.md` instead (`frontend/app.py`'s
`_capture_dogfood_run()`, append-only). Used the real 3 RUN blocks
(`11:34:32`/`11:35:40`/`11:38:22`, matching Session 68's own Run A/B/C
labels) rather than stopping on the stale path -- this go-round's
close-out promotes that catch into a standing CLAUDE.md correction
(Reference Materials' new "Dogfood/diagnostic evidence surfaces" note)
so future prompts stop citing the scratch surface.

**Measure-first result: 2 expected deltas, 0 unexpected.** Classified
every field across all 3 runs, OLD vs. NEW, before writing any commit
message. Exactly the 2 predicted MARKS-class flips fired (LEFT's field-
label MARKS text, and run 3's HAND_DETAIL markings bullet -- both
previously-missed word-order variants of the SAME genuine per-hand
absence finding RIGHT's text already caught under the old list); every
LINE-quality field stayed unchanged. One narrower, differently-shaped
non-catch was observed and left open by design: HAND_DETAIL's fate-line
text ("There is no clearly visible fate line in the image.") has its
noun AFTER "visible", the reverse of F-B's target shape -- harmless in
practice (fate line resolves correctly from its other 2 sources
regardless), logged to the V1.1 register rather than expanded into
scope.

**The knock-on (pass-4 comparability).** `markings/other features` now
exits via genuine-negative-absence in all 3 reference runs -- removed
from both `supported_features` and `unsupported_features` entirely,
where it previously sat in `supported_features` via a junk near-floor
query (scores 0.348-0.365/0.41-0.41, barely above the 0.30 noise floor).
`_check_feature_coverage`'s denominator shrinks vs. pass 3 by design;
CLAUDE.md now locks this explicitly so a future pass-4 scorer doesn't
misread the shrinkage as new coverage loss.

**Tests.** Zero test-file edits needed -- the existing suite's 3 MARKS
fixtures all already used the OLD-list-matching word order ("No clear
marks visible."), so nothing in the synthetic test suite exercised the
real-world word-order gap this pass fixes. Suite ran clean FIRST,
unprompted: 3220 passed, 3 skipped, exact match to the F-A baseline. A
single commit sufficed; the two-commit-one-push discipline's commit-B
branch was never needed.

**Close-out itself** (this addendum's own commit, "S68 F-B close-out +
evidence-surface correction", docs/docstrings/comments only, zero logic
changes): CLAUDE.md gained F-B COMPLETE, the pass-4 comparability lock,
the evidence-surface correction (plus its own "Dogfood/diagnostic
evidence surfaces" note under Reference Materials), and the HAND_DETAIL
fate-line V1.1 register line. S68 fix-forward queue now reads F-C, F-A,
AND F-B all COMPLETE -- only F-D remains queued. Ring 3 pass 4's gate is
OPEN: every pre-ratification fix has landed; scheduling now needs only
fresh palm uploads plus a design-chat go.

### S68 FINAL addendum -- Ring 3 pass 4: SCORED NOT RATIFIED, architectural
ruling, S69 queue opened (2026-07-19)

**The pass-4 arc.** Pre-flight smoke probe first (`scripts/probe_pass4_
preflight.py`, ported from pass-3's script for the S68 8-validator + F-A
coverage + A1 tagged-capture pipeline) against the sanctioned
`data/test_images/` fixtures -- all 4 sanity asserts passed, a wiring
check only, never scored. Then 3 fresh live dogfood runs through the real
app, 2026-07-19, real photo uploads, human-confirmed descriptions: Run A
(baseline), Run B (identical-input regenerate), Run C (+HAND_DETAIL) --
plus 3 fail-closed attempts along the way (2 on Run A, 1 on Run B), all 3
tripping `self_help_blacklist: found stability` on BOTH the first AND
retry draft, requiring a manual re-click outside the S66 F2c in-call
retry mechanism to get a scoreable run.

**Evidence assembly** (`diagnostics/ring3_evidence_S68_pass4.md`,
Sonnet): claim ledger built from SELF-DECLARED anchors in each run's
`reading_text_tagged` -- direct positional parse, explicitly NOT a
reconstruction (that was the F-C payoff: the tagging contract means the
model's own citations are the evidence, not a re-derivation). Coverage
warnings (missing from the F5 capture -- `frontend/app.py` never writes a
`warnings:` line, a real gap caught by reading the capture function
directly) and per-chunk verbatim text WERE reconstructed, gated behind a
measure-first reconstruction-fidelity assert that PASSED for all 3 runs
before any reconstructed data was trusted.

**Scoring** (`diagnostics/ring3_palm_rubric_S68_pass4.md`, Sonnet, pass-3
lineage + 2 S68 rows): **all 3 runs scored 2/4 (P1 N, P2 Y, P3 Y, P4 N).
NOT RATIFIED.** P7 initially left PENDING (procedural F1 confirmation is
not sign-off, per pass-3's own precedent), then RATIFIED in this
close-out once the user reviewed the fresh uploads in design chat and
design chat proceeded on that basis -- same standard pass-3 used.

New findings beyond the 5 items design chat pre-adjudicated:
- **Confirmed citation inversion** (Run B, row 14) -- the model cites
  `p98_c1` for "long fingers -> intellectual nature," and that exact
  chunk states the claim is *"erroneous and misleading."* Stronger than
  pass-3's "bordering inversion" language (pass-3 never actually cited
  the rejection chunk directly against the claim; this run does).
- **Cross-run retrieval flip-flop on the identical claim type** -- Run C
  cites a DIFFERENT chunk (`p95_c0`, which genuinely supports the claim)
  for the same "long fingers" claim that inverted in Run A/B via `p98_c1`.
  Same confirmed attribute, opposite doctrine outcome, purely from which
  chunk the per-feature query happened to retrieve -- the same
  instability class pass-3's Findings #2 first identified (there, on
  head-line/life-line joining doctrine), now reconfirmed on a second,
  unrelated claim.
- **`[OBS]` doctrine leakage x3** -- Run B rows 5, 7, 9 assert real
  interpretive trait claims (row 5 echoes Cheiro's own "guided by reason
  and intelligence" phrasing near-verbatim) tagged `[OBS]` with NO anchor
  at all. A failure shape pass-3 could not have observed (it predates the
  A1 tagging contract) -- worse than a bad citation, since there is
  nothing to check.
- **F-B comma-list absence gap, live-confirmed on 3/3 runs** -- LEFT's
  MARKS field this pass read *"No crosses, stars, grilles, squares, or
  moles clearly visible"*, a comma-separated list that defeats
  `_ABSENCE_PATTERNS_BY_FEATURE`'s filler-group regex (a comma is not
  `\s`, so the pattern can't skip past it). Falsifies the F-B close-out's
  own comparability note, which stated the shrink-to-genuine-absence
  behavior as a general fact rather than the phrasing-conditional
  prediction it actually was -- a measure-first violation on the
  design-chat side, corrected in this close-out (see CLAUDE.md).

**Scorer self-correction, documented not silent**: mid-session, an initial
read of Run A's head-line/chain-indecision claim scored it C via negation
("chain -> indecision" implying "no chain -> no indecision"); re-checked
against pass-3's own precedent (which required a chunk to STATE the
positive valence directly, not merely imply it by negating a stated
negative -- see pass-3's heart-line U-rows) and corrected to U before the
artifact was finalized. Recorded in the rubric's own verify-before-
transcribe note, per this session's explicit "stop and report rather than
conform" instruction.

**Design-chat retrospective verdict**: three consecutive passes of
downstream fixes -- S67's per-feature retrieval + support gate +
exemplar-echo guard, S68's chunk-anchor grounding + coverage check +
absence-phrase broadening -- each shipped exactly what it was scoped to
fix, verified working as designed, and P1 (grounding) FAILED EVERY SINGLE
PASS regardless. Ruled architectural, not another link in the same fix
chain: single-call generation composes from GPT-4o's pretraining prior
first and retrieved doctrine second, making citations decorative rather
than load-bearing -- the `p98_c1` inversion and the `[OBS]` doctrine
leakage are direct evidence of this, not incidental defects a fourth
downstream patch would close.

**S69 queue opened, replacing the S68 fix-forward queue** (CLAUDE.md
Carry-Forward, full detail there): **F-H (PRIMARY)** -- two-stage
extract-then-voice generation redesign (Stage 1: per-feature claim
extraction from gated chunks, paraphrase-or-nothing; Stage 2:
closed-inventory voice pass over only Stage 1's output), probe-first on
the FROZEN pass-4 inputs before any production change, folding in a
temperature review and a Stage-1 model-choice question. **F-E** (small):
comma-tolerant absence-pattern fix. **F-G**: the "stability" appendix
datum (2/3 fail-closed drafts cited `p160_c2`, which lacks the word; 1/3
pure `[OBS]`) confirms the blacklist hits are composition-habit-driven,
not chunk-driven -- folded into F-H's design, retry-cap question left
open. **F-F absorbed into F-H** (the anchored-but-unfaithful citation
class IS the architecture problem, not a separate patch). **F-D**
unchanged, still queued, untouched by F-H's Stage 1 (same retrieval feeds
both). **Option S** (feature scope-down) recorded REJECTED-as-primary --
shrinks the problem's surface, not its mechanism, and pass-4's worst
findings landed on flagship high-confidence features scope-down would not
have removed; retained as a fallback only if F-H's Stage-1 probe fails.
**Pass-5 gate: CLOSED** until F-H and F-E both land; the N=5
re-ratification counter is UNSTARTED (no ratified-live baseline exists to
count failures against yet).

## Session 69 -- F-H two-stage extract-then-voice redesign landed end to end: probe -> Stage 1 -> Stage 1 tests -> Stage 2 -> Stage 2 tests -> wiring -> test alignment -> close-out (2026-07-19)

### Probe (`ef81bff`) -- pre-implementation gate, ruling: SC-4 is a criterion mis-specification, not an extraction defect
`scripts/probe_fh_stage1_extraction.py` (throwaway) measured Stage-1
extraction quality on the FROZEN pass-4 inputs (`diagnostics/
ring3_evidence_S68_pass4.md` -- the SAME 3 runs pass 4 already scored,
retrieval bypassed entirely, reconstruction-fidelity-gated against live
ChromaDB before any cell ran) across a 12-cell matrix: 3 runs x 2 models
(gpt-4o, gpt-4o-mini) x 2 temperatures (0, 0.3), 5 success criteria per
cell. Result: SC-1 (no `p98_c1` cited as `supports`, only `corrective`),
SC-2 (no pass-4 U-row claim reappears), SC-3 (citations stay in-set), and
SC-5 (100% JSON parse rate) PASSED in all 12 cells, at BOTH models and
BOTH temperatures -- the cost-discipline lesson, verbatim from the
resulting `claim_extraction.py` comment: "SC-1/2/3/5 PASS in every one of
the probe's 12 cells, identically to gpt-4o's results at the same
criteria; no quality tradeoff was observed for the cheaper/faster model
on this extraction task." gpt-4o-mini was LOCKED for Stage 1 on this
measured evidence, not assumed -- a real cost win that would have been
missed by defaulting to the expensive model out of caution.

SC-4 (a fate-line claim citing `p163_c1` must have `condition_text`
referencing the rises-from-life-line precondition) FAILED all 12 cells --
zero claims extracted the precondition at any model/temperature. Design
ruling, not silently forced: this is a MIS-SPECIFIED CRITERION, not an
extraction defect. "Barely visible" (the confirmed fate-line observation
in all 3 frozen runs) states nothing about WHERE the line rises from --
there is no textual basis for the precondition to be confirmed against,
so both models correctly, conservatively declined to force a claim. The
extractor's own downstream design (an empty `claims` list, or E-4's
`excluded_from_voice` fail-closed marking) is the CORRECT behavior this
finding predicts and validates, not a gap the implementation needed to
force past. `_PARAPHRASE_OVERLAP_FLOOR=0.40` was set from the probe's
pooled overlap distribution (min=0.50, p25=median=p75=max=1.00, n=73)
with an explicit CAVEAT carried into both the code comment and CLAUDE.md:
unlike the 0.30 support-score floor (which sits between a measured
negative-control ceiling and a measured minimum genuine score), this
probe never measured a genuinely-fabricated claim's overlap -- the floor
sits below the pooled minimum with a conservative margin, but the band is
one-sided, not proven from both directions.

### P1 (`d6b4b34`) -- `agent/interpretive/claim_extraction.py`, Stage 1
New file only. `extract_claims(gated_results, texts_by_feature, client)`
-- one extraction call per feature with gated chunks, system prompt +
stopword set TRANSPLANTED verbatim from the probe (the exact text the
probe validated, not redrafted). E-1 (per-feature-only chunk_id legality,
retiring accepted gaps (a)/(f) by construction) + E-2 (schema, re-keyed
claim_ids via a module-owned counter -- never trusting model-emitted
ids) + E-3 (paraphrase floor) run as an all-or-nothing gate per feature
response, F2c single retry (hard 2-call cap) on any violation. E-4
(conditional fail-closed: `valence=="conditional"` OR a populated
`condition_text`, EXCLUDED unless the precondition is a literal
substring of the feature's own confirmed text) marks but never drops a
claim -- kept in the inventory with `excluded_from_voice=True`,
`exclusion_reason="precondition unverified"`. `RuntimeError` only when
EVERY attempted feature fails both its tries; zero-gated-features input
returns an empty, non-raising result. Suite 3220/3 unaffected (new file,
no other file touched).

### P2 (`73959d4`) -- `tests/interpretive/test_claim_extraction.py`
New test file only, 15 tests. `_FakeClient`/`_FakeCompletions` transplanted
from `test_palm_reading.py`'s own precedent, cited not reinvented. A
SELF-CAUGHT test-design bug during this prompt (not a production bug):
four persistent-failure tests were first written with only ONE feature in
`gated_results`, so a single-feature failure IS "all features failed" by
extract_claims' own contract, tripping the wrong branch (`RuntimeError`
instead of `failed_features`) on first run. Fixed by adding a second,
always-succeeding feature alongside the one under test in all four,
isolating the intended behavior from the separate all-fail path (which
has its own dedicated test). No production bug exposed. Suite 3220/3 ->
3235/3 (+15, 0 regressions).

### P3 (`4481ff7`) -- `agent/interpretive/claim_voicing.py`, Stage 2
New file only. `voice_claims(claims, texts_by_feature, client)` -- one
whole-reading voice call over the closed inventory Stage 1 produced.
Input filter drops `excluded_from_voice` claims and caps corrective-
valence claims at `_CORRECTIVE_CAP=1` (voice/UX judgment call, not
measured -- more than one correction in a reading reads as a barrage of
hedges, Ring 3 is the revisit trigger), overflow logged not voiced. "##
Voice" system-prompt block transplanted near-verbatim from `palm_reading.
_READING_SYSTEM_PROMPT`'s own Voice section (one line adapted: "provided
passages" -> "the numbered CLAIM INVENTORY", since Stage 2 never sees a
retrieved chunk). New `{[C<n>], [OBS], [FLOW]}` tag contract, closed over
V-3 (tag legality, position-only, same accepted sandwich-gap class as
palm_reading's own V-1) + V-4 (claim coverage) + V-5 (`[FLOW]`/`[OBS]`
doctrine guard, reusing `palm_reading._SUPPORT_NEEDLES` as a TRANSPLANTED,
cited-not-imported constant to avoid a circular import -- deliberately
coarse, ANY feature-noun hit in a non-claim sentence fails, Ring-3-
backstopped ACCEPTED GAP, not a false-negative-optimized classifier).
`_VOICE_MODEL="gpt-4o"` chosen but explicitly flagged UNTESTED (the probe
never measured Stage-2 voice quality, only Stage-1 extraction). F2c
single retry, `RuntimeError` on any API exception at either call (a
single whole-reading call has no per-feature fallback to degrade to,
unlike Stage 1). Suite 3235/3 unaffected (new file only).

### P4 (`3256d90`) -- `tests/interpretive/test_claim_voicing.py`
New test file only, 17 tests, same `_FakeClient` lineage. Every test
passed on first run against P3's module as committed -- no test-design
bug this time (unlike P2), no production bug exposed. Covers the input
filter end to end (asserting on the ACTUAL sent messages, not just the
internal filter function -- excluded/overflow claims verified absent from
the prompt text itself), all four V-3 failure shapes, V-4 fail/retry/
persist, V-5 needle-in-FLOW/needle-in-OBS/same-needle-in-claim-passes,
validator-ordering proof (V-3 gates V-4/V-5), retry cap, both API-
exception variants, and both empty-included-set paths. Suite 3235/3 ->
3252/3 (+17, 0 regressions).

### P5 (`62c4a5d`) -- `agent/interpretive/palm_reading.py`, two-stage wiring
Single-call generation RETIRED: replaced by Stage 1 -> Stage 2, split at
a new `prepare_palm_reading()`/`complete_palm_reading()` seam (`generate_
palm_reading()` keeps its exact signature, now a 2-line wrapper -- no
behavior fork, built for a future P6 dogfood checkpoint on the claims
inventory). V-1/V-2/`_check_feature_coverage`/`_run_ring1_checks` calls
REMOVED, functions left DEFINED (deletion deferred to its own future
prompt). Sources rebuilt per-CLAIM (only claim_ids Stage 2 actually
CITED, deduped by chunk_id+feature, stable citation order) -- a
deliberate tightening vs. the old per-gated-chunk sources list, which
included every chunk fed to the prompt regardless of use. Decline set =
union of gate-unsupported + Stage-1 `failed_features` + supported-but-
empty/all-excluded features, "honest decline over silence."

TWO SELF-CAUGHT, SELF-CORRECTED design issues during this prompt (both
fixed before running any test, documented not silently patched): (1)
Stage 2 tags its output `{[C<n>], [OBS], [FLOW]}`, a DIFFERENT vocabulary
than the existing `CHUNK_ANCHOR_TAG_PATTERN`/`strip_generation_tags()`
recognize (`[OBS]` or a full `[<book>_p<n>_c<n>]` token) -- reusing them
as-is would have silently left Stage-2 tags in the displayed text; fixed
by adding `_STAGE2_TAG_PATTERN`/`_strip_stage2_tags` (duplicated from
`claim_voicing._VOICE_TAG_PATTERN`, cited not imported, same convention
P1/P3 used for the timeout constant). (2) A first draft assigned
`PalmReadingResult.unsupported_features=decline_features` (the broader
union), silently redefining a field whose documented meaning has always
been "registry-order tuples from the support gate" -- caught on review
before testing; reverted so the field stays gate-only, and the broader
union is used ONLY to build the decline-block text, never assigned to
the field.

Also documented, not fixed: the OLD `_LOW_CONFIDENCE_ADDENDUM` path made
exactly 1 LLM call even with zero retrieved chunks, free-composing a
generic reading. The two-stage architecture has no equivalent -- zero
gated chunks means Stage 1 has nothing to attempt and Stage 2 has nothing
to voice, so the reading becomes decline-block-plus-disclaimer only, ZERO
LLM calls anywhere. Ruled a deliberate, correct consequence of retiring
free composition (the entire point of F-H), flagged as a NOTED BEHAVIOR
CHANGE for CLAUDE.md rather than silently absorbed. Suite (this commit,
before alignment): 3213 passed, 39 EXPECTED failures (old single-call
tests), 3 skipped -- committed LOCALLY ONLY, not pushed, per the
two-commit single-push discipline (P5b's commit carries the push).

### P5b (`664b159`) -- `tests/interpretive/test_palm_reading.py`, test alignment
All 39 pre-existing failures individually verified (not inferred from
position) and grouped into 5 root-cause mechanisms, all traced to test
fixtures built for the retired architecture -- zero genuine `palm_
reading.py` bugs exposed. One shared helper (`_two_stage_setup`/
`_single_feature_client`) built once, not 34 hand-edited stubs, builds
the two-stage `responses=[...]` sequence (Stage-1 JSON per attempted
feature + one Stage-2 tagged draft) any test needs. Feature-noun mentions
moved out of `[FLOW]`/`[OBS]` content into `[C<n>]`-tagged content
throughout, since V-5 now fails a `[FLOW]`/`[OBS]` sentence naming a
feature the old single-tag stubs freely mixed in. Four tests marked
`pytest.mark.skip` (not deleted) for retired-validator invocation paths.
Three old "F2c retry on a display-check failure" tests, testing a
mechanism that no longer exists (display checks don't retry in the new
pipeline), replaced by four INTEGRATION-level tests proving the `retry_
used` OR-composition and the two new precise fields (`stage1_retry_
features`, `stage2_retry_used`) instead of re-deriving Stage 2's own
already-tested validator logic.

DISCOVERY during this alignment pass, not previously flagged in P5's own
report: `_assemble_retrieved_passages` (the old single-prompt `###
{feature}` assembler) is ALSO no longer called by the two-stage pipeline
-- its own integration test (`test_per_feature_map_ordering_and_dedupe_
for_display`) asserted on that assembly's dedupe/display-order behavior
via message content that no longer reflects it at all. Flagged in this
prompt's own report rather than silently expanded scope; the function
itself is untouched, deletion deferred with the rest of the dead-code
inventory.

ONE SELF-CAUGHT, SELF-CORRECTED assumption error during testing: a first
draft of the all-features-absent test assumed ALL 10 registry features
would be exempt from the decline block (genuine negative absence).
Running it falsified this -- of the 10, only 7 (life/head/heart/fate/
thumb/fingers/marks) are genuine negative absence (each absence-phrased
on its own mentioning source); the other 3 (sun line, mount of venus,
mount of jupiter) are sub-features NEVER NAMED at all in the fixture text
-- `_is_genuine_negative_absence` requires an actual mentioning source,
so "never mentioned" is not the same as "genuinely absent," and these 3
land in `unsupported_features`/the decline block exactly as they did
before P5's wiring. Fixed by asserting the actual, verified tuple rather
than the assumed one.

Both `62c4a5d` and `664b159` pushed together in ONE push, per the
two-commit single-push discipline. Suite progression across the whole
P1-P5b arc: **3220/3 (baseline) -> 3252/3 (P1-P4, +32 new tests, 0
regressions) -> 3213/39-EXPECTED-FAILED/3 (P5, wiring) -> 3249/0/7 (P5b,
alignment -- 4 new F-H retirement skips + 3 pre-existing unrelated
skips)**. Zero regressions across the entire arc outside the 39
EXPECTED, fully-catalogued P5 failures, all resolved by P5b.

### Close-out (docs only, this entry + CLAUDE.md updates)
CLAUDE.md's F-H Locked Decisions entry rewritten to LANDED state
(net -5 lines vs. the pre-close-out file, folding the now-resolved S69
queue/T4-status bullets rather than appending on top); A1 accepted-gap
register updated in place to mark gaps (a)/(f) RETIRED BY CONSTRUCTION
(the historical RATIFIED-gap text for the single-call architecture is
preserved, not deleted -- a retirement note is appended to each). Two
3-place registration gaps found during verification and closed with
comment-only edits (zero logic changes, suite re-run to confirm): `claim_
voicing.py`'s module docstring was missing a mention of `_VOICE_MODEL`'s
untested status (code-site comment existed, docstring didn't); both
`claim_extraction.extract_claims` and `claim_voicing.voice_claims` were
missing a code-site comment at their own empty-input early-return
(`attempted_features`/`if not included_claims:`) pointing at the NOTED
BEHAVIOR CHANGE their module docstrings already described elsewhere.
Carry-forward: P6 (app.py F5 capture wiring + human-checkpoint ruling:
dogfood=blocking inventory panel, end-user=expandable non-blocking), F-E
(still queued, small), the pass-5 gate (needs P6 + F-E + fresh uploads +
design-chat go), the Option S trigger (pass-5 P1 fail = no fourth fix
cycle), and the Ring 3 rubric pass cap (5, pre-ratification). V1.1
register gained two new items: the `test_palm_reading.py` monolith split
(1694 lines) and a prompt-drafting rule (inline fixture-builder specs for
>15-test prompts; targeted test runs during a rewrite, one full-suite run
at the end) -- both drawn directly from this arc's own practice.

## Session 70 -- Pass-5 gate closed end to end: F5 capture/checkpoint wiring -> F-E -> a probe-caught exemplar-echo regression -> the F-G fix-forward loop -> stage2 attribution -> T4 RATIFIED-LIVE (2026-07-19 through 2026-07-23)

### P6a (`be64da6`) -- `frontend/app.py`'s `_capture_dogfood_run()`, F5 capture schema
New `### claims_inventory` section (one pipe-delimited line per
`reading.claims`, `claim_id | feature | chunk_id | valence |
excluded_from_voice | exclusion_reason | condition_text | claim_text`),
new `stage1_retry_features`/`stage2_retry_used`/`validation_failures`
lines. The old `valid_chunk_ids_count: unavailable` placeholder line
(S68 F-C accepted gap (e)) is REMOVED entirely, not fixed -- superseded
by claims_inventory's per-claim `chunk_id`, which gives the real
membership directly. Targeted run only (S70 cost discipline): `pytest
tests/test_app_dogfood_capture.py` -> 13 passed (6 pre-existing + 7 new).

### P6b (`27889c1`) -- two-mode Stage-1 checkpoint (dogfood blocking / end-user expandable)
END-USER path unchanged, gains a non-blocking collapsed "Claims
inventory" expander. DOGFOOD path changed to two-phase: the generate
button now calls `prepare_palm_reading()` only, rendering a BLOCKING
claims panel (ACK-ONLY -- no edit widgets) with Ack (-> `complete_palm_
reading(prep)`, existing P6a capture fires) / Decline (-> new `_capture_
checkpoint_declined(prep)`, a `## CHECKPOINT-DECLINED` block, no voicing
call) buttons -- same AI-reviewing-AI checkpoint discipline as the S65/
S66 palm-description gate, now extended to the claims inventory. State
discipline treated as the hardest case: `palm_prep` mirrors `palm_
reading_result`'s existing clear-site pattern at all 24 sites (grepped
and verified 1:1, not assumed). One self-caught, self-corrected test-
placement bug during this prompt: 2 new AppTest tests placed at the
bottom of the test file (after many bare-import tests) tripped a
spurious `st.button() can't be used in an st.form()` failure from
polluted Streamlit widget/form state within the pytest process --
unrelated to any P6b production code (confirmed: the same test passes
in isolation), fixed by relocating both next to the pre-existing 2
AppTest tests near the top of the file. Targeted run only: `pytest
tests/test_app_dogfood_capture.py` -> 20 passed (13 P6a + 2 new AppTest
+ 5 new direct-import).

### Pass-5 pre-flight probe (`918a4d1`) -- two-stage port, first live ABORT caught
`scripts/probe_pass5_preflight.py` (throwaway, ported from the pass-4
probe to the S69 two-stage pipeline) ran the Run-C shape (both palms +
hand_detail, live vision + live two-stage generation) against `data/
test_images/` fixtures. 5 of 6 sanity asserts passed; the 6th caught a
REAL regression: `exemplar_echo: i have examined many hands in` --
Stage 2's own voice prompt was still handing the model `claim_voicing._
VOICE_SYSTEM_PROMPT`'s two R2 exemplar sentences (transplanted from
`palm_reading._EXEMPLAR_SENTENCES`) as tone models, and the model echoed
one verbatim. This single probe finding is what opened the entire F-G
fix-forward loop below -- pass-5's own gate had never been exercised
against the two-stage pipeline before this run.

### F-E (`84c49f1`) -- comma-tolerant absence filler groups
`_build_absence_noun_pattern`'s two filler-hop groups (and, found
necessary by DIRECT regex testing rather than assumed from the diff
alone, the mandatory noun-connector `\s+`) gain `[,;]?` tolerance --
fixes the S68 pass-4 finding that list-phrased MARKS fields ("No
crosses, stars, grilles, squares, or moles clearly visible") defeated
the old comma-blind pattern. One deviation from the instructing prompt's
stated scope, found necessary by testing: the connector immediately
before the noun also needed the tolerance, since `\b` cannot fire
between "cross" and "es" in "crosses" (both `\w`, no boundary), so
"square" (preceded by a comma) is the only needle that actually lands on
a real word boundary in the target sentence. 3 new tests (target case,
semicolon variant, F-B's islands-regression guard re-verified for all
3 line features). Targeted run: `pytest tests/interpretive/test_palm_
reading.py -q` -> 62 passed, 4 skipped (unchanged pre-existing skips).

### F-G1 (`eb2c891`) -- extra-validator injection seam in `voice_claims`
New keyword-only `extra_validators: tuple = ()` param + `_run_extra_
validators` helper: each `(tagged_draft) -> list[str]` callable runs
against the raw tagged draft on BOTH the first and retry drafts, merged
into the same failure list that drives the single F2c retry and the
final `validation_failures`. No `palm_reading` import (circular-import
lock preserved). Default `()` verified byte-for-byte behavior-preserving
for every pre-existing call site. Seam only -- no display validators
wired yet, that is F-G2.

### F-G2 (`34c7e6f`) -- display checks feed Stage-2 retry (seam wiring)
New `_build_display_extra_validators(context_corpus, unsupported_
features)` builds 6 closures (jargon/self-help/unsupported-dates/length/
banned-feature-mention/exemplar-echo -- MEASURE FIRST found `_run_
display_checks` actually runs 6 checks, not the 5 the instructing prompt
named; all 6 wired, not just the named 5), each stripping Stage-2 tags
before running its check, passed into `voice_claims(..., extra_
validators=...)`. The outer `_run_display_checks` post-hoc call on the
final draft is UNCHANGED, kept as the deterministic fail-closed
backstop. Re-running the pass-5 probe after this landed (`908d325`)
STILL aborted on exemplar_echo (`tells its own story to those` -- a
different fragment, same two sentences) -- the retry-feed wiring made
the echo detectable and retried, but the prompt's OWN exemplar text was
still the gravitational source pulling the model back to it; this
finding is what opened F-G3.

### F-G3 (`4b6d15a`) -- descriptive voice guidance replaces verbatim exemplars
`_VOICE_SYSTEM_PROMPT`'s "Model sentences..." line (the two R2 exemplars
transplanted from `palm_reading._EXEMPLAR_SENTENCES`) DELETED, not
reworded -- replaced with purely descriptive voice attributes (warm/
measured/first-person-where-natural/plain-language/no-canned-openings)
and an explicit "compose everything fresh" mandate. Stale prose in the
module comment/docstring claiming the two modules "share the same two
tone-only exemplar sentences" corrected in the same commit (no longer
true). New test imports `palm_reading._EXEMPLAR_SENTENCES` directly
(not pasted inline) so a future edit to either sentence can't silently
desync the two modules. Re-running the probe after this (`b4dc5a1`):
**all 6 sanity asserts PASSED** for the first time this arc.

### Stage2 first-attempt attribution (`15fe6d3`) -- `PalmReadingResult` + capture
Both preflight re-run addenda (`908d325`, `b4dc5a1`) hit the same wall:
a `stage2_retry_used=True` run gave no way to see WHAT drove the retry.
New `PalmReadingResult.stage2_first_attempt_failures: tuple[str, ...] =
()`, populated from `voice_result.diagnostics.get("first_attempt_
failures", ())` in `complete_palm_reading()`; `frontend/app.py`'s F5
capture gains one adjacent semicolon-joined line, same join-or-NONE
convention as the existing `stage1_retry_features_str`/`validation_
failures_str` lines.

### F-G4 (`f94cecb`) -- V-5 `[OBS]` carve-out + adjacent-tag prompt hardening
Separately from the probe's echo finding: 4 consecutive REAL dogfood
runs on 2026-07-22 (`.claude/read_prompt.md`) all fail-closed on the
IDENTICAL two-stage pattern -- `stage2_first_attempt_failures` always
`tag_legality: adjacent tags with no sentence between them`, and the
FINAL `validation_failures` (post-retry) always `doctrine_guard` on an
`[OBS]` sentence legitimately naming its own observed feature (e.g.
"The sun line is clearly present on your palm."). Root cause: V-3 gates
V-4/V-5 (`_run_validators`), so V-5 never even ran on draft 1 -- the
single retry was spent fixing tag adjacency, leaving no budget to also
fix the V-5 hit that then failed the retry draft too. Fix: (1) `_check_
flow_obs_doctrine_guard` renamed `_check_flow_doctrine_guard`, `[OBS]`
segments skipped entirely (this module's own pre-flagged accepted gap,
now RETIRED for `[OBS]`, narrowed to `[FLOW]` only); (2) `_VOICE_SYSTEM_
PROMPT` gains a hard rule requiring a complete sentence between any two
tags (no example sentences added -- F-G3's zero-quotable-text
constraint preserved via brace placeholders, not real prose). 25/25
targeted tests pass (`tests/interpretive/test_claim_voicing.py`), incl.
2 new: doctrine_guard failures never carry an `[OBS]` label, and the new
hard-rule text is present with no smuggled example prose.

### Pass-5 preflight re-run post-F-G4 (`5002ddf`)
All 6 sanity asserts PASSED again (`stage2_retry_used=True`, retry
cleared cleanly, `tag_legality`/`claim_coverage`/`doctrine_guard` all
`pass`) -- first clean run exercising the EXACT failure class the 4
dogfood runs above had hard-blocked on.

### Close-out (docs only, this entry + CLAUDE.md updates, 2026-07-23)
3 fresh LIVE dogfood runs through the real Streamlit app on 2026-07-23
(`diagnostics/dogfood_capture.md`: `18:42:14` Run A, `18:43:13` Run B,
`18:44:11` Run C+HAND_DETAIL -- distinct from the throwaway probe
script's fixture-based runs above) scored 4/4 on the pass-4 rubric's
P1-P4 rows, the SAME rubric pass 4 scored P1 FAIL on. Deterministic
Ring 1 corroborates all 3: `passed=True`, `validation_failures=NONE` on
every run, with each run's `stage2_first_attempt_failures` showing the
retry catching a REAL first-draft hit (a doctrine_guard/jargon/self_help
failure, one per run) and clearing it -- the F-G wiring visibly doing
its job, not merely absent because nothing tripped it. T4 status
upgrades directly from SCORED NOT RATIFIED (S68 pass 4) to
RATIFIED-LIVE on the FIFTH Ring 3 pass, satisfying the S68/S69 pass cap
exactly at its limit. N=5 post-ratification failure counter STARTED at
0 (a new, separate counter from the pre-ratification pass cap). Option
S trigger NOT FIRED -- pass-5's P1 did not fail, so the fallback is
retained only as a post-ratification-reopen contingency, unchanged.

CLAUDE.md updated: Current Session Focus rewritten to the RATIFIED-LIVE
state; new **T4 RATIFIED-LIVE** Locked Decisions entry added (full
detail + all commit refs); the F-H LANDED entry's V-5 and F-G-residual
notes updated in place (append-only, historical text preserved) to
point at the RATIFIED-LIVE entry; A1 accepted-gap (e) marked RETIRED in
place (superseded by P6a's claims_inventory, not merely fixed); three
now-resolved Carry-Forward bullets (T4 status, F-E, P6) REMOVED per this
file's own "Carry-Forward holds OPEN items only" rule, resolution
recorded here instead (see below); V1.1 register gained three new items
(parallelize Stage-1's sequential per-feature calls -- a mechanical,
~10s-latency concurrency win, not a design question; V-5's remaining
`[FLOW]` false-positive on legitimate summary-closing sentences, an
ACCEPTED gap even after the `[OBS]` carve-out; a needle-inventory audit
-- `_FEATURE_TRAIT_NEEDLES`/`_SUPPORT_NEEDLES`'s singular needles can't
match a plural-only surface form on their own, currently masked only
because both forms already happen to be listed for every feature that
needs them).

**Baseline correction (Working Style #12 applied to the instructing
prompt itself):** the close-out prompt's stated baseline of 3279/0/7 was
verified against a fresh full-suite run before writing it into either
doc, not trusted as given -- actual result: **3281 passed, 0 failed, 7
skipped**. The 2-test gap is fully accounted for: F-G4's own targeted
run reported 25 tests in `test_claim_voicing.py` including 2 new ones
added after the 3279 baseline was likely last taken, not a discrepancy
requiring further investigation.

Full-suite progression this arc: **3249/0/7 (S69 baseline) -> 3281/0/7
(S70 close-out, verified)** -- every individual S70 commit ran a
TARGETED suite only (P6a/P6b/F-E/F-G1/F-G3/F-G4 test files, `.md`
diffs above), per the session's own cost-discipline instructions; this
close-out's full-suite run is the FIRST full-suite verification taken
across the entire S70 arc.

### Carry-forward resolved this session
- **P6** (S69 register) -- RESOLVED. P6a (`be64da6`) + P6b (`27889c1`)
  both landed; F5 dogfood capture now carries the claims inventory and
  two-stage retry fields, with the blocking-checkpoint/expandable-
  display split ruled and implemented as specified.
- **F-E** (S69 queue) -- RESOLVED (`84c49f1`). Comma-tolerant absence
  filler groups landed; F-B's islands-regression guard re-verified
  unaffected.
- **T4 status / pass-5 gate** (S68/S69 register) -- RESOLVED. T4 is
  RATIFIED-LIVE as of this session's pass 5; see CLAUDE.md's new T4
  RATIFIED-LIVE entry for the full evidence chain. The Option S trigger
  and the N=5 pre-ratification pass cap are both retired as ACTIVE gates
  (the cap was satisfied, not violated); a NEW N=5 post-ratification
  failure counter takes over from here.
- **A1 accepted gap (e)** (`valid_chunk_ids_count: unavailable`) --
  RESOLVED by REMOVAL (`be64da6`), not by exposing the field as the
  gap's own V1.1 register item once proposed -- claims_inventory's
  per-claim `chunk_id` made that promotion unnecessary.

### Carry-forward added this session
See CLAUDE.md's Carry-Forward register for the live, actionable list:
F-D (unchanged, still queued/undebated), the `palm_processor.py` rider,
the `astrosage_parser.py` noise-strip touch, and three new V1.1 register
items from this session (Stage-1 call parallelization, the V-5 `[FLOW]`
residual false-positive, and the needle-inventory singular/plural audit)
-- not duplicated here per this file's own compression convention.

## Session 71 -- T4 RATIFICATION REVERSED, first row-level scoring of pass-5 produced P1 FAIL on Run A row 5 (2026-07-24)

### Trigger
S70's close-out asserted pass-5 scored "4/4 on the pass-4 rubric's P1-P4
rows" (CLAUDE.md's T4 RATIFIED-LIVE entry), but no row-level rubric
artifact existed to back it -- unlike pass-3 (`ring3_palm_rubric_S67_
pass3.md`) and pass-4 (`ring3_palm_rubric_S68_pass4.md`), no `..._pass5.md`
file was ever written; the only pass-5 artifact was `pass5_preflight_
S70.md`, an explicitly-labeled throwaway wiring probe on fixture images
("says nothing about interpretive quality/citation accuracy -- that is
Ring 3 pass 5's job, human-scored"). This gap surfaced when a design-chat
session opened the first-ever row-level adjudication of pass-5 Run A row 5
and found it did not survive scrutiny.

### Row 5 adjudication (design-chat, this session)
Row 5 -- Run A (`## RUN 2026-07-23T18:42:14.473283`, `diagnostics/
dogfood_capture.md`), `READING (TAGGED)`: "This line speaks to your
mental faculties, indicating intellectual strength and the quality of
your talents. `[C3]`". `claims_inventory` row, verbatim: `C3 | head line
| cheiroslanguageo00chei_1_p145_c0 | supports | False | None | None |
The line of head relates principally to the mentality of the subject,
including intellectual strength or weakness and the direction and
quality of talent.`

Pass-4 Run A row 4 rationale (`ring3_palm_rubric_S68_pass4.md`, verbatim):
"4 | 'head line...reflects a strong mental capacity and intellectual
vigor' | `p145_c0` | **U -> FAIL** -- chunk is the HEAD LINE chapter's
naming/intro text only ('relates principally to the mentality...to the
intellectual strength OR weakness' -- neutral framing, no valence for
deep/long). Identical chunk, identical defect as pass-3 Run A row 8."
(Note: the source precedent this row-4 text itself cites is pass-3 Run A
row 8, not pass-4 row 8 -- pass-4's own row 8 is a different, unrelated
heart-line/`p160_c2` row; the task instruction that opened this
adjudication conflated the two, corrected in design chat before scoring.)

Three candidate rulings were weighed:
- **ADJ-A (uphold U)** -- the chunk hasn't changed and neither has its
  content: `p145_c0` states strength *or* weakness, a two-sided taxonomy
  statement. Two independent prior passes (pass-3, pass-4) already ruled
  this exact chunk cannot license one-sided positive framing.
- **ADJ-B (score C)** -- Stage-1's `valence="supports"` field is real and
  explicit, produced by an independent extraction call under a documented
  rule ("if a chunk directly and positively supports the observation, use
  valence='supports'"), a structurally different evidence base than
  pass-3/4's raw single-call prose. Ruled to COLLAPSE on inspection: C3's
  own `claim_text` preserves the identical "strength or weakness"
  disjunction the label claims to have resolved positively -- the label
  contradicts its own claim text, so it carries no adjudicative weight.
- **ADJ-C (score D, tag mis-emitted)** -- would require ruling `[C3]`
  itself wrongly attached to an OBS-class restatement. Rejected: the
  clause ("indicating intellectual strength...") is a genuine interpretive
  leap with no analogue in the confirmed HEAD LINE field; the tag is
  doing exactly what it's designed to do. Not defensible.

**ADJ-A upheld.** Row 5: U -> FAIL.

### Full Run A ledger (independently re-verified against `dogfood_capture.md` this session)
Re-parsing the full `READING (TAGGED)` text (not transcribing `.claude/
read_prompt.md`'s draft, which was independently found to reach the same
numbers) surfaced two more rows beyond row 5:
- **Row 3** ("the way this line sweeps far out into your hand is a
  testament to your good physical strength" `[C2]`, `p139_c0`) --
  claims_inventory C2 states a CONDITIONAL doctrine ("When the line of
  life sweeps far out into the hand..."), but neither hand's LIFE LINE
  field confirms "sweeps far out" (both say only "curves around the base
  of the thumb"). Same class of defect as row 5: Stage-1 labeled this
  `valence="supports"` (not "conditional", condition_text=None) despite
  the claim text itself carrying an unstated precondition. **U -> FAIL.**
- **Row 10** (summary: "Overall, your hand reveals a picture of strength,
  vitality, and intellectual capability." `[FLOW]`) -- restates rows 3
  and 5's U-scored claims with no new citation, pass-4's own summary-row
  convention. **U -> FAIL.**

Run A tally: 3 C rows (2, 6, 8), 4 D/D-frame rows (1, 4, 7, 9), 3 U rows
(3, 5, 10). Rubric: P1=N (3 U-class rows), P2=Y (no direct field
contradictions -- rows 3/5 are precondition-mismatch/unsupported-valence
issues, not contradictions of a confirmed field), P3=Y (`ring1_
validation.passed=True`, `failures=()`), P4=Y (`validation_failures:
NONE` -- this pass's schema retired the old coverage-warnings mechanism,
superseded by Stage-2's V-4 claim-coverage check per S69 F-H). **Score:
3/4 -- below the 4/4 ratification bar.**

Per pass-4's own precedent (a single run's P1 FAIL fails the pass
regardless of the other runs' scores), Run A alone is dispositive. Run B
and Run C were deliberately NOT scored this session -- both share
byte-identical LEFT/RIGHT confirmed descriptions with Run A and would
encounter the same `p145_c0` chunk for the same head-line claim, so
scoring them could not change the P1 FAIL verdict already reached on Run
A; out of scope for this reversal.

### Full artifact
`diagnostics/ring3_palm_rubric_S70_pass5.md` -- new file, written this
session as the reversal record (not a ratification artifact): STATUS
SCORED / NOT RATIFIED, Run A ledger complete with row 5's ADJ-A rationale
expanded verbatim, Run B/C marked NOT SCORED THIS ARTIFACT with the
reasoning above, re-open path pointing at Ring 3 pass 6.

### CLAUDE.md updated
T4 RATIFIED-LIVE Locked Decisions entry renamed **T4 RATIFICATION
REVERSED (S71)** -- original S70 text preserved verbatim beneath a new
reversal block (append-only, not deleted). Current Session Focus
rewritten to the reversed state. N=5 post-ratification failure counter
marked RETIRED (never went live). New Carry-Forward item: Ring 3 pass 6,
gated by design-chat re-litigation of the `p145_c0` recurring defect
(THREE passes now -- pass-3 row 8, pass-4 row 4, pass-5 row 5 -- same
chunk, same defect; read as corpus-level or Stage-1-extraction-level, not
per-pass variance). No "architectural stability window" lock on
`palm_reading.py`/`claim_extraction.py`/`claim_voicing.py` existed
anywhere in CLAUDE.md to lift -- the S71 task instruction assumed one;
none was fabricated, the gap is noted in place instead.

### No production code touched this session
Docs only: CLAUDE.md, SESSION_LOG.md (this entry), `diagnostics/ring3_
palm_rubric_S70_pass5.md` (new), `diagnostics/latest_run.md` (completion
note). No RATIFIED token required (Working Style #14's docs/diagnostics
exemption).

### Carry-forward added this session
**Ring 3 pass 6** -- see CLAUDE.md's Carry-Forward register. Gated on
design-chat re-litigating the `p145_c0` recurring defect before spending
a fresh pass-6 dogfood run on the same failure a fourth time.

## S71 addendum -- V1 palm dropped (Option Z scope lock), Ring 3 arc closed (2026-07-24)

### The six-session arc (S65-S71)
- **S65**: T4 architecture landed -- AstroSage paragraph + palm reading
  as upload-triggered artifacts, `agent/interpretive/palm_reading.py`
  shipped one-shot with Cheiro RAG. Two prior scope locks made at this
  same session bear directly on today's decision: LLM-generated
  interpretive Q&A excluded from V1 (the S23 path (c) verdict), and
  kundali×palm cross-verification explicitly deferred to V1.1 (logged
  Parashara dissent -- a real capability cut, not a free choice).
- **S66-S67**: Ring 3 human-rubric passes 1-2 (SCORED NOT RATIFIED both
  times), then the R1/R2/R3 fix-forward queue (per-feature retrieval,
  exemplar rewrite, support gate).
- **S68**: Ring 3 pass 3 (SCORED NOT RATIFIED, P7 ratified OK, P1/P4
  blockers) -- fix-forward queue opened (F-A through F-H candidates).
- **S69**: F-H two-stage extract-then-voice redesign (`claim_
  extraction.py` Stage 1 + `claim_voicing.py` Stage 2) landed end to
  end, replacing the single-call generator.
- **S70**: Pass-5 gate work (P6a/P6b capture wiring, F-E, the F-G1-4
  fix-forward loop) closed out with a claimed RATIFIED-LIVE call -- but,
  as S71 discovered, that call was never backed by a row-level rubric
  artifact; only a prose summary and a throwaway wiring probe
  (`pass5_preflight_S70.md`) existed.
- **S71 (this session's earlier turns)**: first-ever row-level scoring
  of pass-5 Run A found row 5 (`p145_c0`) scores U -> FAIL under the
  SAME rubric methodology pass-3/pass-4 already applied to this
  identical chunk (pass-3 Run A row 8, pass-4 Run A row 4) -- REVERSED
  the RATIFIED-LIVE call (commit `c19ea0c`). Independent re-verification
  of the full Run A ledger surfaced a SECOND, structurally different
  self-contradicting-valence instance on `p139_c0` (a conditional claim
  labeled `valence="supports"` instead of `"conditional"`). A follow-up
  diagnostic scan (`scripts/probe_neutral_chunk_valence.py`, Phase 1,
  no commit) found 25 candidate chunks in `cheiroslanguageo00chei_1`
  sharing `p145_c0`'s neutral/disjunctive shape, AND explicitly flagged
  that `p139_c0`'s precondition-mismatch shape was NOT caught by any of
  the 5 mechanical patterns used -- a second, uncatalogued defect class.

### This turn's decision: Option Z -- drop palm reading from V1 entirely
Design chat weighed the accumulated evidence against continuing to
pursue Ring 3 pass 6 (already queued as a carry-forward item from the
reversal) and ruled: palm reading fails V1's accuracy bar, and the
failure mode is not a bug the architecture can be patched around.

**Why this is a model-fit problem, not an architecture problem**: the
F-H two-stage extract-then-voice redesign (S69) is real, shipped, and
demonstrably works as designed -- the S70 pass-5 dogfood runs showed the
F-G retry wiring visibly catching and clearing real first-draft
doctrine_guard/jargon/self_help failures, exactly as built. What it
cannot do is make Stage 1 (GPT-4o-mini, temp=0, LOCKED per the S69
`fh_stage1_probe_S69.md` extraction-quality probe) correctly judge
VALENCE on classical prose that is inherently hedged, disjunctive, and
conditional by genre convention (Cheiro's own "strength or weakness",
"either... or...", "when X, it is a sign of Y" phrasing is NORMAL for a
19th/20th-century palmistry text, not an edge case). Three consecutive
Ring 3 passes hitting the IDENTICAL chunk with the IDENTICAL defect,
plus a second defect class surfacing the moment the ledger was checked
more carefully, plus a 25-chunk candidate list for the first defect
class alone (with the second class's true prevalence still unmeasured),
together read as a structural mismatch between what Stage 1 is asked to
judge and what the corpus's prose actually supports judging -- not a
threshold to retune or a prompt tweak away.

**Why the user's stated V1 objective doesn't rescue this**: the
underlying interest (layman palm Q&A, and a combined palm+astrology
reading) is independently out of V1 scope on TWO separate prior locks,
neither opened by this decision: LLM-generated interpretive Q&A was
excluded from V1 at the S23 path (c) verdict (re-affirmed S65), and
kundali×palm cross-verification was deferred to V1.1 at S65 with a
logged Parashara dissent. Relocating palm interpretation from its
current T4 upload-time surface to a query-time Q&A surface would not
fix the Stage-1 valence defect -- it would carry the SAME defect into a
currently-unscoped, currently-unbuilt surface, compounding rather than
resolving it.

### Decision recorded (see CLAUDE.md's new V1 PALM DROPPED entry for the full text)
V1 palm-side user flow DROPPED: no palm upload UI, no T4 palm reading
generation, no palm citations in Q&A routing. All palm-side code STAYS
in the repository untouched -- `palm_processor.py`, `agent/interpretive/
palm_reading.py`, `claim_extraction.py`, `claim_voicing.py`, the Cheiro
RAG chunks in ChromaDB, the Ring 3 harness, and all palm tests are
preserved intact for V1.1, not deleted or rewritten. V1 ships T1/T2/T3
deterministic chart answers plus the AstroSage paragraph display --
chart-only.

**This is a scope decision, not a technical failure.** Recorded
explicitly because it would be easy to read five ratification attempts
and a reversal as "the team couldn't make it work" -- the two-stage
architecture DOES work, on its own terms (S69's probe evidence, S70's
retry-wiring evidence). What doesn't work is asking that architecture
to extract reliable positive/negative valence judgments from a genre of
prose that is genre-typically neutral, hedged, and conditional. That is
a task-model-fit ceiling, not an implementation defect -- no amount of
further prompt engineering on the SAME model class was demonstrated to
close it across S66-S71's five passes.

### CLAUDE.md updated this turn
Current Session Focus rewritten to the drop. `V1 scope` entry corrected
(palm removed from the interpretive-surface description -- a direct
internal-consistency conflict with the new drop decision, fixed
proactively, not requested verbatim in the instructing prompt). New
Locked Decision **V1 PALM DROPPED (S71, 2026-07-24)** added with the
full rationale, inserted immediately after the T4 RATIFICATION REVERSED
entry. That entry's own "T4 status reverts to SCORED NOT RATIFIED"
sentence updated in place to "OUT OF V1 SCOPE -- palm reading dropped,
S71", with the interim SCORED NOT RATIFIED read preserved parenthetically
for chronology rather than silently overwritten. The "pass 6 is next"
cross-reference corrected to point at this addendum instead of a
Carry-Forward item that no longer exists. Carry-Forward's **Ring 3 pass
6** item REMOVED (resolved by the drop, not superseded by new evidence
-- resolution recorded here per this file's own "Carry-Forward holds
OPEN items only" convention). Three other standalone palm-related
Carry-Forward bullets (`palm_reading.py` S65 flags, F-D retrieval
instability, `palm_processor.py` rider) MOVED into the existing V1.1
register mega-bullet, content preserved verbatim, not deleted -- all
palm-side follow-up work is now consolidated under V1.1, matching the
drop decision's own framing. V1.1 register gains one new item: revisit
palm reading with the full S65-S71 findings, considering a structured-
display fallback (verbatim Cheiro citations, no LLM valence judgment)
or a hand-curated whitelist mode as candidate remedies -- neither
designed nor decided here.

### No production code touched this session
Docs only, this turn: CLAUDE.md, SESSION_LOG.md (this entry),
`diagnostics/latest_run.md` (completion note, overwritten). No test,
config, or production module edited. Feature-flag wiring to formally
gate the palm UI path off in `frontend/app.py` is explicitly a SEPARATE
follow-up prompt, not attempted here. No RATIFIED token required
(Working Style #14's docs/diagnostics exemption).

### Carry-forward resolved this session
- **Ring 3 pass 6** (S71 reversal's own carry-forward, added earlier
  this same session) -- RESOLVED by the Option Z drop: no further Ring
  3 passes are needed once palm reading is out of V1 scope. Not a
  technical resolution of the `p145_c0`/`p139_c0` defects themselves --
  those remain open findings, now living in the V1.1 register instead
  of an active pass-cap countdown.

### Carry-forward added this session
See CLAUDE.md's V1.1 register (Carry-Forward section) for the
consolidated palm-side follow-up list: `palm_reading.py` S65 flags,
F-D retrieval instability, `palm_processor.py` rider, needle-inventory
audit, Stage-1 call parallelization, V-5 `[FLOW]` residual, and the new
"revisit palm reading" item added this session -- not duplicated here
per this file's own compression convention.

## Session 73 -- Yogini dasha P3 catch-up + P4 chart_profile/orchestrator wiring (2026-07-25)

Note: Session 72's own work (Yogini dasha calc module, JHora fixture
extension, palm UI gate S72-2a, Yogini year-constant diagnostic) never
received its own SESSION_LOG.md close-out entry -- this session's own
Carry-forward corrections item below traces directly to that gap: with
no session-log entry to check against, a carry-forward claim about S72
went unverified against the actual git history until this session
re-derived it directly from `git log`.

Two commits landed, both by direct verification against the actual
committed state (not against the instructing prompt's assumptions --
see the correction below):
- `764e910` "S72 P3 (catch-up): route yogini_dasha domain -- router
  whitelist + Stage 2 enum + unbuilt-keyword removal" --
  `agent/infra/calc_router.py` + `tests/infra/test_calc_router_stage2.py`.
  Verified in isolation (stashed the P4-scoped files, ran the full
  suite against this commit's content alone): 3286 passed, 0 failed,
  7 skipped, 3 xfailed -- exact match to the documented S72 close
  baseline. A direct `orchestrator.answer_question()` probe confirmed
  the fail-closed guard (orchestrator's own `_VALID_DOMAINS` check, not
  chart_profile.py's -- it fires one layer earlier than routing
  narrative elsewhere had assumed) raises cleanly for a yogini_dasha
  question at this commit.
- `f2d7cc4` "S73 P4: wire yogini_dasha into chart_profile builder+
  dispatch and _VALID_DOMAINS on both sides; flip orchestrator xfail
  (formatter branch lands in P5)" -- `agent/infra/chart_profile.py`,
  `agent/infra/orchestrator.py`, plus two new test files
  (`tests/test_yogini_routing.py`, `tests/infra/test_chart_profile_yogini.py`).
  Full suite after this commit: 3295 passed, 0 failed, 7 skipped,
  4 xfailed.

Neither commit pushed -- batches with Prompt 5 (result_formatter.py's
own yogini_dasha branch) per two-commit-one-push discipline, making the
eventual push 3 commits instead of the usual 2, a one-time deviation
flagged here as instructed.

### Carry-forward corrections
- S72's carry-forward stated the yogini_dasha router wiring (Prompt 3:
  `calc_router.py` keyword/dispatch/Stage-2-enum changes) was
  "committed and pushed." It was not: `git log` at the start of this
  session showed the last commit touching Yogini was `11b9284`
  (calc module + its own unit tests only) -- the router wiring sat
  uncommitted in the working tree the entire time, only landing now as
  `764e910` above. Root cause noted above (no S72 close-out entry to
  cross-check the claim against).

## S73 close -- Commit B + Commit C landed and pushed, session-close audit (2026-07-25)

This entry closes the yogini_dasha staged rollout begun above: router
(Commit A, already landed by the time this entry's own predecessor was
written) -> chart_profile builder + dispatch + both _VALID_DOMAINS
(Commit B) -> result_formatter.py's own render branch (Commit C). All
four commits (A, this file's own docs commit, B, C) pushed together in
ONE push -- a one-time deviation from the project's usual two-commit-
one-push discipline, flagged per instruction: it exists because S72's
own Prompt 3 work never got a session-close push at the time (see the
Carry-forward corrections section above), so this session's own A/B/C
sequence absorbed that backlog rather than leaving it stranded another
session.

### Three spec deviations accepted at Commit B review
Each verified against the actually-committed code before being accepted,
not against the instructing prompt's assumptions -- all three are
documented in place (chart_profile.py's own module docstring/branch
comment) as well as here:
1. **Inlined yogini_dasha branch, no standalone `build_yogini_dasha_
   profile()` helper.** Unlike arudha_lagna/upapada_lagna (which compose
   several existing calculation modules together and so justify their own
   builder function), Yogini's branch is a thin call site onto
   `agent/calculations/dashas/yogini.py`'s already-complete
   `compute_yogini_dasha()`/`current_yogini_md()` -- there is no bespoke
   composition here to justify extracting a separate helper.
2. **`uncertainty_days=0.0`, not the prompt's suggested `1.0`
   placeholder.** Matches the established `sade_sati`/`arudha_lagna`/
   `upapada_lagna` convention: `0.0` means "no envelope documented yet,"
   not "verified exact" (same semantics, not to be confused with
   `current_dasha`'s genuinely-measured `37.0`). The domain's real,
   actually-known provisional-accuracy caveat is carried entirely by
   calc_router.py's `_YOGINI_DEMOTION_REASON` (Commit A) via the
   router-side demotion_reason -- this file does not need to duplicate it
   on a fabricated day axis. Fabricating a `1.0` placeholder would itself
   have violated THRESHOLD DISCIPLINE (CLAUDE.md Working Style #4 --
   every numeric threshold needs justification; "a bit more than the one
   observed drift number" is not one).
3. **The xfail on `test_yogini_orchestrator_returns_current_md` was
   retained with a corrected reason string, not flipped to a
   `pytest.raises` assertion.** Of the two patterns the instructing
   prompt offered, this is a third, cleaner option: it needs no further
   edit when Commit C lands (which it now has) -- the same assertion
   just starts passing on its own. Confirmed safe before relying on it:
   `xfail_strict` defaults to `False` at both the global level (no
   `pyproject.toml`/`setup.cfg`/`tox.ini` in this repo; `pytest.ini` has
   neither `addopts` nor `xfail_strict`) and the decorator level (only
   `reason=` was ever passed, no explicit `strict=`) -- so Commit C's
   landing correctly produced an `XPASS`, informational only, not a
   suite break.

**xfail_strict global default = False** is hereby the documented
convention for this project (verified, not assumed, per the audit
above) -- future dasha-family staged rollouts (Ashtottari, Chara,
Kalachakra all remain unbuilt, see CLAUDE.md's P2-order lock and
`_UNBUILT_MODULE_KEYWORDS`) can rely on the same non-strict-xfail
pattern for their own "lands at router before formatter" staging window,
without re-verifying this each time.

### Test count trajectory
- 3286 (S72 close baseline, and this session's own Commit A verified in
  isolation against it -- exact match, 0 regressions from the router-only
  change).
- 3295 after Commit B (+9: two new test files, `tests/test_yogini_
  routing.py` 6 passed + 1 xfailed, `tests/infra/test_chart_profile_
  yogini.py` 3 passed).
- 3299 after Commit C (+4 from the new `tests/infra/test_result_
  formatter_yogini.py`; the routing xfail flipped to xpassed
  informationally, so passed count also absorbs that +1 while xfailed
  drops by 1 for the same reason).

**Final suite: 3299 passed / 0 failed / 7 skipped / 3 xfailed / 1
xpassed.** Re-verified directly on HEAD at session close (Working Style
#12), not carried forward from an earlier in-session number.

### CLAUDE.md updated this turn
New `## Carry-forward corrections` section added (did not exist before
this session) with the single S72-Prompt-3 correction bullet -- see that
section for the exact wording; not duplicated here. No other CLAUDE.md
edit this turn (Locked Decisions/Carry-Forward content otherwise
untouched) -- the instructing prompt's own §3 also suggested recording
the xfail_strict convention "in the Locked Decisions section," which
this entry reads as referring to this SESSION_LOG entry's own
documentation of it (immediately above), not a second CLAUDE.md Locked
Decisions bullet: the same prompt's §1 explicitly capped CLAUDE.md to
"no functional edits; add ONE bullet," and a new Locked Decisions entry
would exceed that cap. Flagged here rather than silently picking one
reading -- if a durable CLAUDE.md Locked Decisions entry for xfail_strict
is actually wanted, that's a follow-up prompt, not assumed here.

### No source code touched this session
Docs only, this turn and its predecessor: CLAUDE.md, SESSION_LOG.md.
Commits A/B/C (source + tests) were reviewed, ratified, and landed in
prior turns of this same session -- ratification tokens for those are
recorded against their own commits, not re-litigated here.

## S75 -- Vimshottari row-0 gap investigation + Ayanamsa lead closure (2026-07-26)

**Note:** no S74 close block was ever logged in this file, though commit
`2e34788` ("diagnostic: S74 pyjhora source audit -- Vimshottari
balance-at-birth mechanism") landed and is referenced elsewhere in
CLAUDE.md/diagnostics. Left open rather than backfilled here --
recorded as a carry-forward gap, not expanded into this session's scope.

- Ayanamsa lead (S74 §11 0.94 arcmin gap) FALSIFIED. Root cause: S27
  Sulabh capture was under True Chitrapaksha mode, compared against
  production SIDM_LAHIRI. Cross-mode ~56" delta misdiagnosed as
  precession divergence. pyswisseph SIDM_LAHIRI ≡ JHora Traditional
  Lahiri to 0.14" at both epochs tested (Sulabh 1988, Sheridan 1984).
- Vimshottari year_days = 365.256363 (sidereal) CONFIRMED via new
  method: JHora fixture-internal arithmetic (end-start ÷ years)
  yields 365.2558-365.2572 across all 9 rows. Ready for production
  but NOT SHIPPED this session pending V1.1 batching decision.
- Row-0 residual under matched-mode Drik oracle (Traditional Lahiri):
  Sulabh -2.67d, Sheridan -1.93d, Surbhi -0.33d, David -0.54d.
  Non-linear scaling -> falsifies both linear-reference-frame and
  fixed-angular-offset hypotheses. Seasonal pattern (spring births
  higher residual) suggests apparent-Moon convention divergence.
- Camp Y / Camp X split identified:
  Camp Y (formal math): Kapoor textbook, Prokerala, our production
  Camp X (commercial):  JHora GUI, AstroSage, Drik Panchang
- Accepted gap D1 logged (`docs/KNOWN_DIVERGENCES.md`). V1 ship
  decision: RATIFIED (range-based answers unaffected, day-precision
  predictions excluded from V1 scope).
- Kapoor book already present at `data/pdfs/[Deepak Kapoor] Astronomy
  and Mathematical Astrology_text.pdf` (not moved to a new
  `project_files/classical_references/` path -- that directory doesn't
  exist anywhere else in the repo; `data/pdfs/` is the established
  convention, same directory as the PVR book). Format: plaintext OCR
  (7385 lines). Highest priority sections: Ch IX (Vimshottari), Ch
  XVI-XIX (Shadbala/Bhava Bala), Ch IV (ayanamsa table).
- Canonical oracle reclassification: JHora primary for non-dasha
  (Ashtakavarga, karakas, D-charts, Panchanga); Drik primary for
  dasha row-0/AD boundaries going forward. AstroSage secondary parity.
- Fixtures NOT re-captured under Traditional Lahiri this session --
  tracked as S76 open item.

Ratifications:
1. Camp Y alignment as V1 position (Kapoor as anchor citation)
2. Kapoor book citation path corrected to its actual repo location
   (`data/pdfs/`), CLAUDE.md Reference Materials section updated
3. Accepted gap register (`docs/KNOWN_DIVERGENCES.md`) Gap D1 reframed
   with Camp Y/Camp X citation
4. JHora -> Drik oracle reclassification for dasha

Open items S76:
- Ship year_days = 365.256363 to production (surgical, ratified twice)
- Re-capture Traditional Lahiri Vimshottari MD tables to
  tests/fixtures/jhora_{surbhi,sheridan,david}.md (Sulabh already
  captured this session)
- Kapoor RAG indexing (extend ChromaDB corpus 14 -> 15 texts)
- Kapoor-based Shadbala refactor evaluation (may resolve S1/S2 gaps)
- Backfill or formally drop the missing S74 close block (see note above)

Carry-forward (unchanged from S74/S75 open):
- _keyword_hits word-boundary regex refactor
- .claude/read_prompt.md working-tree drift (this session's own prompt
  carried a stale prerequisite hash and a stale Kapoor file path --
  both surfaced and corrected before executing, not silently followed)
- scripts/probe_neutral_chunk_valence.py untracked
- ~0.68d Yogini row-0 offset (S72 origin) -- same class as Vimshottari
  row-0 residual, likely folds into Camp Y position

## S76 — D1 provenance closure + year_days sidereal ship + PROJECT_FACTS registry

Shipped (3 items, 2 commits, single push):

1. **Gap D1 provenance closed.** 4 Drik Panchang Vimshottari captures
   landed as committed diagnostics (diagnostics/drik_vimshottari_S76_
   {sulabh,surbhi,sheridan,david}.md). Verbatim tables + local→UT→JD
   arithmetic + residuals vs production row-0. Matched-mode residuals:
   Sulabh -2.6643d, Surbhi -0.3259d, Sheridan -1.9237d, David -0.5450d.
   Sheridan's prior -1.78d quote confirmed as transcription drift, not
   re-measurement. docs/KNOWN_DIVERGENCES.md D1 provenance flag replaced
   with S76 closure note; accepted-gap disposition unchanged.

2. **year_days = 365.256363 sidereal shipped to production.**
   agent/chart_calculator.py::_add_years() — the sole flow-through
   site. Blast radius verified empirically: sade_sati.py and
   av_transit_scanner.py 365.25 constants are independent (Saturn
   transit math + scan-window divisor, not year-length).
   golden_qa_sulabh.py ±37d envelope analytically clear of the ~0.006
   d/yr compounding drift. Fixtures tests/fixtures/jhora_{sulabh,
   surbhi,sheridan,david}.md recaptured from real production output
   (imported production functions, not hand-reimplemented); Panchanga /
   planetary-position / Yogini sections untouched. Pre/post-ship D1
   residuals agree within 0.002d — row-0 gap is fixed ephemeris/
   ayanamsa offset, not year-length. Ratified twice pre-ship (S74
   regression + S75 fixture-internal arithmetic 9 rows × 4 charts).

3. **docs/PROJECT_FACTS.md registry established.** Session-agnostic
   persistent-facts file. Sections: canonical charts, JHora fixtures,
   Drik captures (S76 landed), settled empirical findings, external-
   data-do-not-re-request register, append protocol. Hard provenance
   rule: no entry accepted unless traceable to a committed file.
   Design-chat/session-log assertions insufficient.

Test baseline: 3302 pass / 0 fail / 7 skip / 1 xpassed. Byte-identical
pre/post-ship.

Carry-forward to S77:
- PROJECT_FACTS §2 "Current MD/AD" column stale relative to recaptured
  fixtures. Refresh at next docs touch (out of S76 ratified scope).
- Surbhi/Sheridan/David natal Lagna sign/nakshatra/pada not captured
  in any fixture — jhora_{surbhi,sheridan,david}.md are MD-tables-only.
  Open capture gap, same class as the ayanamsa-boilerplate gap.
- jhora_{surbhi,sheridan,david}.md ayanamsa lines are template
  boilerplate (23-40-39.08 identical across 3 different birth epochs,
  should differ ~13-14 arcmin across 1976-1992). Open capture gap.
- S74 diagnostic file mislabels Surbhi Moon as "Uttara Bhadrapada
  nakshatra #24" — astronomically Shatabhisha. Non-blocking, fix at
  next S74 file touch.

S77 candidate tasks (agents deliberate before choosing):
D. Kapoor-anchored Shadbala refactor evaluation (Ch XVI-XIX vs
   current agent/shadbala.py). Design-chat only, no Code work. May
   close S1/S2 accepted gaps.
C. Kapoor book RAG indexing (ChromaDB 14 → 15 texts). Independent of
   chart pipeline. Chunking strategy may depend on D outcome.
E. Palm reading V1.1 queue. Needle-inventory audit or thumb/fingers
   retry investigation. Independent workstream.
F. PROJECT_FACTS §2 refresh + Surbhi/Sheridan/David Lagna capture
   (housekeeping bundle).
G. Name your own.

Recommended order: D → C → E. Housekeeping (F) opportunistic.

## S77 — Kapoor as classical citation for Shadbala S1/S2 (docs-only)

Shipped (1 commit, pushed as 886e744):
1. docs/KNOWN_DIVERGENCES.md — Gap S1 (Saptavargaja) and Gap S2
   (Drekkana) reframed with Kapoor Ch XIX p.226-227 (7-tier table)
   and Ch XVI section v p.192 citations. No code refactor. Kapoor
   confirmed as classical support, not a spec swap.

D outcome: Kapoor does NOT close S1 empirically (AstroSage uses a
third unpublished table where Adhimitra is approximately 30 -- neither
BPHS nor Kapoor tier scheme resolves cleanly). S2 Drekkana: Camp Y
unanimous classical (BPHS + Kapoor 15/0 binary) vs Camp X commercial
convergence (AstroSage + JHora 1 flat) -- camp allegiance
inconsistency vs S77 D1 Camp Y ratification, logged not fixed.
Sulabh Sun-vs-Saturn rank gap = 10.42 Virupa vs max +/-14 Virupa swap
delta; rank-flip is possible, propagation to user-visible answers
unverified. S30 1-Virupa lock preserved pending measurement.

C (Kapoor RAG indexing) deprioritized permanently. Kapoor is a
mathematical-astrology manual, not interpretive doctrine. RAG feeds
interpretive T4 answers; math-manual chunks would dilute retrieval.
Revisit only if V2 exposes a "how is X calculated" query surface.

Process finding S77: three design-chat drafting errors caught by
Code AskUserQuestion before commit -- (a) S1 citation location
Ch XVI vs actual Ch XIX; (b) S1 tolerance conflation ±40 vs actual
_TOL=0.5; (c) S2 rank-gap 30-70 Virupa fabricated, actual 10.42.
All three same failure mode: inference asserted as fact in a
persistent register. New discipline: numeric claims into
KNOWN_DIVERGENCES / PROJECT_FACTS / SESSION_LOG require per-claim
fixture/grep verification, matching the pre-prompt research
discipline already applied to Code prompts.

Test baseline unchanged: 3302 pass / 0 fail / 7 skip / 1 xpassed
(no code touched, no pytest run).

Carry-forward to S78:
- .claude/read_prompt.md working-tree drift (still shows S75 content)
- _keyword_hits word-boundary regex refactor
- scripts/probe_neutral_chunk_valence.py untracked
- ~0.68d Yogini row-0 offset (S72 origin), likely folds into Camp Y
- PROJECT_FACTS section 2 "Current MD/AD" stale
- Surbhi/Sheridan/David natal Lagna not captured in any fixture
- jhora_{surbhi,sheridan,david}.md ayanamsa boilerplate identical
  across 3 different birth epochs (real capture pending)
- S74 diagnostic file mislabels Surbhi Moon as Uttara Bhadrapada
  (astronomically Shatabhisha)

S78 candidates: E (palm V1.1 needle audit / thumb-fingers retry),
F (housekeeping bundle -- opportunistic, bundle into E close).
C dropped (see above).

## S78 close — 2026-07-29

Primary: E — Palm reading V1.1
Bundled F items: housekeeping (opportunistic)
Not done: C (Kapoor RAG — deprioritized S77)

### E scope taken: E2 (Stage-1 retry investigation for thumb/fingers)

Agents chose E2 over E1 at S78 open. Rationale: E2 had an observable
failure signal (retry flake in dogfood captures) and bounded scope;
E1 (whole-vocabulary needle-inventory audit) had no exit rubric —
"asymmetry" was never quantified at S70 flag time, so measure-first
discipline required E1 to derive its own rubric mid-investigation,
violating S77 fabrication-guard learnings.

### E2 investigation arc

1. Read-only audit (agent/interpretive/claim_extraction.py +
   frontend/app.py + tests/interpretive/). Findings landed in
   diagnostics/e2_stage1_retry_audit.md. Coverage gap surfaced:
   fingers had zero retry-path tests, thumb had partial coverage
   but no persistent-2-attempt-failure test. Capture gap: happy
   path never persisted per-feature diagnostics.

2. Instrumentation cycle (commits f16d52c, b5d51fb): Added
   attempt_1/attempt_2 status enum (validated, validated_empty,
   validation_failed, error, not_attempted, skipped_no_viable_chunks)
   and final_outcome enum (success_first, success_retry,
   failed_both, empty_first, empty_retry, failed_first_no_retry,
   failed_first_no_viable_retry) to the diag dict. Wired
   PalmReadingResult.stage1_feature_diagnostics carrier through
   happy path. Emitted parity block in both _capture_dogfood_run
   and _capture_checkpoint_declined via shared formatter. Later
   extended emit to include attempt_1_failures / attempt_2_failures
   continuation lines with truncation at 200 chars.

3. Dogfood repro identified (2026-07-27T15:04:44): thumb
   outcome=failed_both when hand_detail upload is omitted while
   both palms are uploaded. Attempt 1 attributed to p.88_c0
   (retrieval rank 1), overlap 0.08; attempt 2 same chunk,
   overlap 0.20. p.87_c0 (validatable, rank 2) sat unused.
   Heart line ALSO went empty in same run — hand_detail affects
   extraction beyond thumb/fingers. Broader observation logged;
   not chased in E2.

4. Fix menu reset. Initial (a) top-k widening, (b) query
   reinforcement, (c) template enrichment all ruled out or
   deprioritized after source audit of _build_retry_messages and
   retrieval measurement (diagnostics/e2f_retrieval_topk.md).
   p.87_c0 was already inside n_results=3 gate — retrieval was
   not the bottleneck. Root cause: retry prompt instructed LLM
   "Same chunks, same feature," causing LLM to spin on the
   E-3-failed chunk instead of switching to adjacent validatable
   chunks.

5. Fix landed as E2F commit 16f6439: parse attempt 1's E-3
   failures for chunk_ids via regex on fixed failure string
   format; exclude those chunk_ids from retry pool; skip retry
   entirely if exclusion leaves no viable chunks. Non-E-3 failures
   contribute zero chunk_ids — retry behavior unchanged. Test
   updates: renamed persistent-failure test to reflect skip-retry
   mechanism, added partial-failure test (genuine discriminator)
   and non-E-3-leaves-pool-intact test (non-regression guard).

6. Confirmation dogfood 2026-07-29T10:21:07 exposed incoherent-
   history flaw: step 1's implementation filtered retry's turn 1
   user prompt, making turn 2 (prior assistant response citing
   excluded chunk) reference a chunk turn 1 no longer showed.
   Incoherent history → LLM went safe → thumb outcome=empty_retry
   with p.87_c0 sitting unused. Fix worked mechanically (chunk
   excluded from re-citation) but not at user-visible layer
   (thumb still declined in reading).

7. E2F step 3 (commit be35a1a): preserve original chunk list in
   retry's turn 1 (matches what attempt 1 saw); enforce exclusion
   via explicit correction instruction in turn 3 that names failed
   chunk_ids and forbids re-citing. Retry pool discipline moved
   from history-rewriting to explicit instruction. Partial-failure
   test updated to check new mechanism.

8. Final confirmation dogfood 2026-07-29T11:02:48: thumb voiced
   in reading, no decline. Fix path (step 3 retry) NOT exercised
   in this run — vision variance produced "Medium relative size"
   (vs prior "Medium size") which shifted extraction enough that
   attempt 1 succeeded on p.88_c0 directly. User-visible outcome
   confirmed at production layer; step 3 code path confidence
   lives in unit tests (deterministic), not this run.

### Commits landed on origin/main during S78

- f16d52c — S78 E2: instrument Stage-1 per-feature retry diagnostics
- df3de42 — S78 E2: Stage-1 retry audit — thumb/fingers diagnostic pass
- b5d51fb — S78 E2: surface Stage-1 validation failure messages in
  per-feature diagnostics
- 16f6439 — S78 E2F: exclude E-3-failed chunks from Stage-1 retry pool
- be35a1a — S78 E2F step 3: coherent retry history for E-3 chunk
  exclusion
- 212d9c6 — S78 E2F: close out — retrieval diagnostics, gitignore
  glob, scratch prompt (single commit bundling the gitignore-glob,
  top-k measurement report, and probe-script deletion items; actual
  history landed these together, not as three separate commits as
  originally assumed)

Note: 95b0236 (docs(diagnostics): update latest_run.md — E2 2d+2e
commit/push record) also sits in this range as an interim
diagnostics-log commit; not narrated separately above.

### Carry-forward to S79

Palm Q&A architecture arc. Objective: route natural-language
questions to palm-only, chart-only, hybrid, or nudge-to-upload
responses. Cache Stage-1 output at upload time (per Sulabh S78
close input) so per-question flow is intent → feature-subset →
cache lookup → Stage-2 targeted voicing, no per-question Stage-1
re-run.

Palm quality gaps identified during E2F, in scope for S79 palm
launch prep:
- E-3 lexical rigidity: word-overlap grounding rejects legitimate
  paraphrase; vision variance (e.g. "Medium" vs "Medium relative")
  shifts retrieval and extraction unpredictably. Candidate fixes:
  embedding-similarity grounding, or LLM-quoted-anchor extraction
  with quote-only overlap check.
- Corpus completeness: heart line pages 157-158 absent from
  ChromaDB (S68 documented). Re-ingest required.
- Coverage of vision-observed variants Cheiro does not cover
  (e.g. "barely visible" fate line). Options: expand corpus, or
  graceful "not addressed by classical text" response.
- Silent declines that should be nudges-to-upload for missing
  hand_detail or missing palm photos.
- Corrective-valence surfacing bug (S71 class): Stage 2 voices
  corrective claims as supports-style — reader cannot tell claim
  is a correction of misconception vs claim about user.

Scaffolding dismantle order (S78 ruling, Sulabh): dogfood_capture,
ACK checkpoint UI, whole-reading generation button all get removed
when palm Q&A ships. Dev harness only until then, behind
ASTRO_PALM_ENABLED gate.

Non-scope for S79 (queued):
- Stage 2 doctrine_guard [FLOW] tripping on feature-noun "life"
  (pre-existing).
- Stage 2 self_help_blacklist tripping on "navigate" (pre-existing).
- E2G candidate: vision-prompt enrichment for feature detail to
  reduce hand_detail dependency at the source.

### Process learnings S78

- Investigation order matters: reading extract+retry prompt shape
  before measuring retrieval would have saved ~2 turns of misdirected
  fix menu (a)/(b)/(c). Read the code path first, measure second.
- Schema under-specification cost turns: step 2a dropped
  error_messages field as "redundant"; had to add back in step 2d.
  Every observability field should be justified against the audit
  question it answers, not against what feels non-redundant.
- Under-delegation to grep/project_knowledge_search: several turns
  asked Claude Code to audit files that could have been read
  directly from the project knowledge tree. Sulabh flagged this
  explicitly S78; corrected mid-session.
- Confirmation runs cannot guarantee fix-path traversal when the
  triggering condition depends on non-deterministic input (vision
  variance). Unit tests carry the deterministic fix-verification
  load; dogfood runs confirm production reach and non-regression.

## S79 — Corpus integrity arc opened; F1-F8 register; Path C selected (2026-07-29)

Opened as palm Q&A routing architecture. SUSPENDED at open: the routing problem is
downstream of a corpus defect. Investigation only, no production code touched.

Commits: 181965d (R1-P0 page triage — SUPERSEDED, global off-by-one page index bug;
corrected re-run OUTSTANDING, deferred), 3178fdc (native text probe). HEAD at close 3178fdc.
Diagnostics: e2g_preflight_S79.md, corpus_export_S79.md, native_text_probe_S79.md,
r1_p0_page_triage_S79.md (superseded), corpus_export_cheiro_S79.jsonl (463 Cheiro chunks,
held untracked at S79 close, landed later in 162539e).

ROOT FINDING. The ingestion pipeline discards each PDF's native embedded text layer and
re-OCRs with Tesseract. ~104 corruption tokens corpus-wide, incl. systematic line->hne and
life->hfe. These directly cause the retrieval failures seen across Ring 3 passes 3/4/5.
Verified by the user copy-pasting a suspect glyph straight out of the PDF.

TWO LONG-CARRIED FINDINGS CLOSED.
- Heart-line corpus gap CLOSED. PDF p157/p158 are Plate XVIII plus its blank verso — a
  plate spread, not missing doctrine. Carried as an accepted gap for six sessions on a
  wrong inference. Doctrine is complete.
- Fate-line "barely visible" re-diagnosed: NOT a corpus gap. p165_c2 exists; p163_c1
  (origin doctrine) simply outranks it. Query-to-chunk vocabulary mismatch.

CENSUS. 1,361 of 7,357 pages (18.5%) carry empty text. Six classical chart sources lose
26-53% of pages via a `mixed` page-type handler that was designed and never implemented.
Three books effectively blank while classified ingested: LAL KITAB-1941, Hasta Samudrika
Shastra, Jataka Parijata. Hasta Samudrika Shastra is the Indian palmistry classic — palm
readings ground exclusively on Cheiro by accident, not design.

RULINGS.
1. Vision-fill chunks are citation-ineligible until human-verified; `text_source` stamped
   in chunk metadata.
2. S79 re-scoped to corpus integrity; palm Q&A routing deferred.
3. S71 V1-palm-drop: evidence base COMPROMISED — every Ring 3 pass was scored against a
   corpus with F1-F7 active. PENDING RE-ADJUDICATION at U5. Do not reopen before U5.
4. PATH C SELECTED — freeze chunk boundaries and ids, replace only the text inside each
   chunk with the aligned native span. Chosen over full re-ingest (breaks all Ring 3 rubric
   anchors) and enumerated token repair (fixes only known corruptions). RETIRED at S80.
5. U0-U7 staged ladder designed; hard stop at U4 if A/B retrieval does not improve.
6. R2 SPLIT. R2-structural (bigram needle not bare substring, `low_visibility` third state
   in _is_absence, deterministic doctrinal lexicon expansion — not HyDE, propagate
   validate_palm_image.quality into Stage 1) runs parallel with U0-U2, text-quality-
   independent. R2-threshold (0.30 floor re-derivation, NLI calibration) waits for U4.
7. E-3 replacement queued post-U4, in order: quote-anchored extraction (Stage 1 emits
   verbatim evidence_quote, gate checks the span as a normalized substring, claim_text
   paraphrases freely — retires the "Medium" vs "Medium relative" class with no threshold
   at all), then NLI entailment WITH a polarity check. Not embedding cosine: cosine is
   topicality and would pass both p145_c0 and p139_c0.

CONVENTIONS REINFORCED. Every Code prompt: durable topic file + overwrite
diagnostics/latest_run.md + push topic file only; no RATIFIED token for diagnostics-only
commits. Every read-only probe carries four ground-truth self-check assertions and fails
loudly. diagnostics/latest_run.md is overwrite-only scratch, never a citation target. Repo
sulabhschauhan/astro-agent is PUBLIC and clonable for design-chat access — stop pasting
file contents.

## S80 — F4 confirmed dominant cause; PATH C RETIRED, PATH D LOCKED (2026-07-29)

Commits (12, all pushed): c4efca7 U0 golden fixture diagnostics + Path C census + F5
falsified on native path · b497c8d U0 fixture generator + tests · 166d8ee U0.5
bidirectional OCR-corruption census (Cheiro) · ec30ef1 U0.5 script + machine-readable
sidecar · 6fec8bf U0.6 C5 decomposition + augmented-oracle delta (Cheiro) · f2cc395 U0.6
script · 66125c6 chunk-id coupling census, repo-wide · b55933a U1 chunk-to-native span
mapping probe (Cheiro) · fb82213 U1 script · cbf6450 U1 correction + U1b pathology triage
(Cheiro) · 56ad4e3 U1b script · 6e69b73 U1c layout-based paragraph recovery probe (Cheiro).
HEAD at close d2623ff.

Suite 3304 baseline -> 3341 passed / 0 failed / 7 skipped / 1 xpassed (+37 U0 tests). The
3302-vs-3304 discrepancy is RESOLVED: 3302 was stale SESSION_LOG prose, 3304 was S78's real
commit-time count, confirmed independently as 3341 - 37.

ROOT FINDING — F4, NOT TEXT CORRUPTION. pdf_processor.py discards the OCR text for pages
classified "mixed", and classify_page() misclassifies ordinary astrology prose as "mixed"
because PLANET_MATCH_THRESHOLD over-fires on planet-dense text. Traced in source end to
end: classify_page over-fires -> page labelled "mixed" -> pdf_processor discards its OCR
text -> image_extractor refills only "diagram" pages, never "mixed" -> embedder skips empty
text -> page vanishes from the corpus. Sample false-positive rate 10/10 Lal Kitab pages
were plain narrative. Session 1's design intent was that mixed pages KEEP text AND get an
image pass; the text-retention half was never built, the image half never ran on mixed
pages. 416/416 Jyotish Lal Kitab empty pages are 100% page_type="mixed" and 100% have
native text present. Fully recoverable at zero API cost.

ARCHITECTURE RULINGS.
- PATH C RETIRED. Killed by C2=210 native-corrupt tokens (a blind "prefer native" rule
  would inject errors) and by 322 mid-page C5a prose tokens requiring INSERTION into frozen
  chunk boundaries.
- PATH D LOCKED, CHEIRO-FIRST. Re-ingest from native text, boundaries seeded from existing
  chunk spans, zero-chunk pages created fresh, F2/F4/F6/F7 fixed at source, pipeline becomes
  the reproducible source of truth. Cheiro is the pilot ONLY because it holds the sole
  labelled eval set (Ring 3). It is not the biggest win.
- OPTION C CHUNKING (user ruling): chunking strategy PLUGGABLE — paragraph-boundary vs
  fixed-window-with-overlap — decided by U4 A/B retrieval comparison, not by argument.
- SEED ACCEPTANCE FLOOR 0.90. JUSTIFICATION: Cheiro match_ratio p10=0.934, median=0.975;
  0.90 sits just below p10 so it rejects only the broken tail. Sub-floor chunks are NOT
  discarded — boundary interpolated from sibling spans. SCOPE GUARD: Cheiro only; every
  other book needs its own distribution measured. TUNING NOTE: re-derive after U4; if
  interpolation fires on >10% of a book's chunks the floor is wrong for that book's OCR
  quality, not a reason to lower it globally.
- F4 FIX IS SEPARABLE FROM PATH D — a branch fix plus targeted re-ingest of affected pages.
  Do not couple it to the Cheiro rebuild. Ship it first.

RETRACTIONS — DO NOT RE-INHERIT THE ORIGINALS.
1. "F5 falsified, U6 removed" — WRONG. Falsified for the NATIVE path only. strip_devanagari
   operates on TESSERACT output and DELETES Devanagari >=0.25 by explicit Session-2 design.
   CONFIRMED on the OCR path. U6 restored, rescoped.
2. "Tesseract language mismatch" — DEAD. OCR ran eng+hin, hin installed and verified. Never
   re-test OCR language configs.
3. "translator.py is dead code, delete it" — WRONG. It is MIS-ORDERED. Module order is
   chunker -> translator; strip_devanagari deletes at >=0.25 exactly what translator's
   >=0.25 guard was built to catch. Mutually exclusive by construction. Verified:
   original_hindi populated ZERO times in progress JSON or ChromaDB — it never translated
   anything in production. Hasta Samudrika and Jataka Parijata were declared "translated" on
   a HARDCODED language="eng" field. Working Style #5 failure that shipped.
4. GATE 1 "67.8% seeding viability" — denominator error. Corrected to 166/180 = 92.2% over
   MAPPED pages; 65 pages were never span-mapped.
5. U1c gate "42.2%" — measured PRECISION where RECALL is the meaningful quantity. Chunks
   hold multiple paragraphs, so precision was capped near 47% before the run. U1d recall
   recompute SPECIFIED BUT NEVER RUN. Deferred, low priority.

U0 FIXTURE DEVIATIONS (documented, not silently forced).
- Corpus-wide scan of all 22 PDFs found ZERO Devanagari codepoints in any native text layer
  — the LAL KITAB Devanagari-orphan defect class is falsified on the native path, not merely
  unverified. Fixture 5 became a Path-C-boundary case instead: Deva-keralam project page
  102, 0 native chars, 3760 live corpus chars across 6 chunks, entirely Tesseract-sourced
  with no native source to align a future repair against.
- Cheiro p156 native text is "rnensal", not "mensal" — a real archive.org ligature artifact.
  The corpus's Tesseract OCR got this one right.
- p90 is no longer an empty-corpus page (re-ingested since the earlier diagnostic) —
  substituted p191. PDF count corrected 19 -> 22.
- New artifact tests/fixtures/native_coverage_S80.json censuses all 22 PDFs. Of the five
  named worst-hit books, only Phaladeepika and Saravali are actually Path-C-ineligible
  (0.0); Jyotish Lal Kitab 0.9987, BPHS-1 and BPHS-2 1.0000 are highly eligible — flagged
  rather than silently reconciled.

NEW DEFECTS.
F9 MULTI-COLUMN LAYOUT UNHANDLED — Deva-keralam bimodal 5/5. Sampled only POPULATED pages =
selection bias. NOT CLEARED. Suspects: Phaladeepika, Saravali, Sarvartha-Chintamani, Jataka
Parijata (Sanskrit+commentary editions are conventionally two-column).
F10 TWO-PAGE SPREADS UNSPLIT — split_spreads=False never verified for the 9-book overnight
batch. Session 2's "all 5 confirmed single-page" covered BPHS x2, Phaladeepika, Saravali,
Cheiro only. Hasta Samudrika is a PHOTOGRAPH of an open book: two facing pages per PDF page,
spine shadow, curved lines.

RECOVERY LEDGER.
Native-recoverable at zero API cost: Jyotish Lal Kitab 416 pages (largest single win),
Cheiro 65 zero-chunk pages, BPHS-1 165 + BPHS-2 162 at 100% native eligibility.
Phaladeepika / Saravali show the same F4 pattern but 0.0 native eligibility, so recovery is
via OCR text retention, not native extraction. Two-column (F9): Deva-keralam,
Sarvartha-Chintamani + suspects. EFFECTIVELY LOST: Hasta Samudrika Shastra — photograph,
spreads, pure Devanagari, zero English; needs split + dewarp + Devanagari OCR + translate,
four unbuilt stages for one book. Likely Jataka Parijata. RECOMMENDATION: re-source English
editions or accept the loss. Cheiro carries palm for V1.1 regardless.

PROVIDER AGNOSTICISM (raised S80, deferred to V1.1). Embeddings CANNOT move off OpenAI —
Anthropic has no embedding endpoint, and changing model invalidates _SUPPORT_SCORE_FLOOR.
Movable: GPT-4o vision fill (low risk, human-gated), GPT-4o-mini translation (likely
removable entirely), calc_router Stage 2 (real risk — locked golden scorecard). Correct fix
is an LLM client abstraction + pinned model ids in config + golden set parameterised by
provider. NOT funded by the subscription extra-usage balance — that pool does not cover
API-key calls; a separate Console balance is required.

CARRY-FORWARD TO S81, gated, in order. (1) Corpus-wide page_type census, metadata only —
size F4 across all 22 books before fixing anything. (2) F4 remediation design (Opus,
9-agent): mixed-branch text retention + PLANET_MATCH_THRESHOLD re-derivation from the
measured planet-keyword density distribution across text vs genuine-diagram pages, with
scope guard and tuning note. Derived, not chosen. (3) Targeted re-ingest of F4-affected
pages, ONE BOOK AT A TIME, Lal Kitab first. (4) Path D Cheiro pilot: boundary seeder, shadow
collection, U4 A/B gate — IF RETRIEVAL DOES NOT IMPROVE AT U4, PATH D IS WRONG AND WE STOP.
(5) F9 column handling. (6) F5/translator pipeline reorder-or-remove decision. (7) F3 vision
fill.

HOUSEKEEPING OPEN AT S81. data/test_images/ holds three real hand photos, tracked, PUBLIC
repo — decide. tests/test_palm_endtoend.py test 4 makes real GPT-4o vision calls in the
suite — marker it. data/chroma_db and data/pdfs untracked, corpus unreproducible from a
fresh clone — Path D is the fix; standing top risk until then.

RESOLVED BY 162539e. Every file held untracked at S80 close is now on origin/main:
scripts/corpus_loss_attribution_S80.py, scripts/build_golden_fixtures_S80.py,
tests/test_golden_fixtures_S80.py, tests/fixtures/golden_S80.json,
tests/fixtures/native_coverage_S80.json, diagnostics/corpus_export_cheiro_S79.jsonl.

## S81 — Palm retrieval: corpus exonerated, page-range filter built, one-call contract blocks ship (2026-07-30)

HEAD at close 55d88a8. Flag _FEATURE_PAGE_FILTER_ENABLED currently False (reverted).
Commits: 947e6d8 F4 census (VOID) · b1f7a79 retrieval baseline (verdicts VOID) · 32b5125
p165_c2 root cause · 99486aa existence-vs-rank reconcile · b51049e production-query rank
probe + committed script · fa9ee8b n_results sweep · d017543 page filter v1 (post-filter) ·
55d88a8 pool=463 + thumb/fingers ranges. Docs: af39327, fc30177, b46424f, 162539e.

ROOT CAUSE, ESTABLISHED. Palm retrieval searched all 463 Cheiro chunks per feature. Score
gaps between adjacent ranks are 0.016-0.034 with no cliff, so near-miss chunks from
unrelated chapters filled the gate of 3. Measured (b51049e, deterministic): fate p163_c1=3
p165_c2=14; head p145_c0=>20; heart p159_c2=5 p160_c1=6 p160_c3=>20. Sweep (fa9ee8b):
min_n_all fate=15, head=NEVER, heart=NEVER — no value of n fixes it. Not a threshold problem.

FIX: PAGE-RANGE PRE-FILTER. Cheiro chapter map extracted from the page-level export (52
headings) and written to data/cheiro_feature_pages.json. With pool = full collection:
p145_c0 6, p165_c2 8, p160_c3 8, p163_c1 3. Head top3 p151_c2/p146_c2/p147_c0 and fate top3
p165_c1/p165_c0/p163_c1 are all in-chapter and human-verified as correct doctrine.

CORPUS EXONERATED FOR PALM — no repair warranted. 463 chunks, all 6 target chunks exist by
direct id lookup. Across the whole doctrine range p133-182, ZERO text pages are empty; all 9
empty pages are page_type='diagram' (plates). S79's p157/p158 plate-spread ruling is
CONFIRMED independently. Path D is not required for palm.

TARGET LIST WAS STALE, NOT THE SYSTEM. The S68-era "correct chunks" were never validated.
Heart top3 (p159_c3, p160_c2, p161_c0) is dense correct doctrine — breaks under
Saturn/Sun/Mercury, fork on Jupiter, high vs low origin, faded line. p145_c0 at rank 6 is
CORRECT behaviour: it is the chapter-opening page (epigraph + preamble); p146/p147 carry the
sign doctrine. Retrieval now ranks better than the rubric asked for.

BLOCKER CARRIED TO S82. The filter makes TWO search() calls per feature (widened candidate
query, then a fallback re-query). The codebase pins ONE call per feature at
_N_RESULTS_PER_FEATURE=3 — asserted independently by
test_query_template_two_hand_merged_quality_literal_shape (len(calls)==1, n_results==3),
test_search_filters_to_canonical_cheiro_book (n_results==3), and
test_one_feature_search_failure_does_not_kill_reading_other_feature_succeeds (2 features ->
2 calls, no retry). These tests encode design intent and MUST NOT be edited.
PROPOSED, NOT VERIFIED: push the range into the Chroma where clause —
search(q, n_results=3, book_name=_CHEIRO_BOOK, page_ref={"$gte":s,"$lte":e}). Requires
adding "page_ref" to query_engine.VALID_FILTER_KEYS and letting _build_where pass a
pre-built operator dict through (currently $eq-only; no existing caller passes a dict, so
the change is a no-op for them). page_ref is stored as int (confirmed by live metadata read).
UNVERIFIED: (a) this ChromaDB version's $gte/$lte support on int metadata, (b) whether
removing the fallback is safe — a zero-match range would yield empty results for that
feature; test_empty_retrieval_yields_zero_llm_calls_and_full_decline suggests the empty path
is graceful, but that was not confirmed. Verify both before committing.

RANGE MAP CORRECTIONS. thumb 85-92 (was 85-94, wrongly absorbed the Joints chapter);
fingers 93-97 (adds THE JOINTS OF THE FINGERS p93-94). p98 opens "THE PALM, AND LARGE AND
SMALL HANDS" and holds no fingers doctrine, so S68's flagging of p98_c1 as the fingers
target was WRONG and excluding it is correct. Earlier map versions omitted 6 chapters and
had 4 wrong boundaries — the 52-heading extraction is authoritative.

F4 CENSUS (947e6d8) IS VOID. data/progress/*.json covers 14 of 22 books, 5,219 of 7,357
pages, and has NO native_text_present field. The 75.9% (947/1248) figure is over an
unknown-completeness subset with a broken exclusion term; both sub-totals were zero
artifacts. The pre-registered cut (>=70% dominant / 40-70% second pass / <40% re-open) DID
NOT FIRE. F4 is unmeasured, not disproven. progress.json is an incomplete census surface —
corpus-wide sizing must read PDF page counts directly.

RETRACTIONS — do not re-inherit the originals.
1. "S79's fate-line ruling is falsified" — WITHDRAWN. S79 was right: p165_c2 exists and
   p163_c1 outranks it. Exactly as measured.
2. "The query template changed without ratification" — WITHDRAWN. Production unchanged since
   S68. The ungrammatical "a 3 {feature}" string came from an ephemeral probe script
   (_N_RESULTS_PER_FEATURE int landing in the quality slot), never from production.
3. "_N_RESULTS_PER_FEATURE=3 is unjustified" — WITHDRAWN. It is justified at
   palm_reading.py:168-175. BUT the comment OVERSTATES its evidence: it cites "worst
   doctrine-first-hit rank 2 across all 8 provable features"; S67 (0a738c3 section 4)
   measured only 2 of 10 features against their own doctrine page. Also: first-hit rank is
   not all-relevant-doctrine coverage, which is what it is now relied on for.
4. "Hasta Samudrika noise competes in palm queries" — WITHDRAWN. Every search call in
   palm_reading.py passes book_name=_CHEIRO_BOOK (lines 542, 571, 574, 583, 591).
5. b1f7a79's Q1=DATA verdict and ALL ranks in b1f7a79 / 99486aa — VOID. b1f7a79 conflated
   "absent from top 10 results" with "missing from corpus"; the ranks came from the
   int-in-query script. b51049e onward are the valid numbers.
6. "The 3 failing tests hardcode stale values" — WITHDRAWN. They pin a real contract.

BOOK MEASUREMENTS (from page-level exports, this session).
Hasta Samudrika: 449 pages, only 4 with >=50 alphabetic words, 19 with >=20, ZERO Devanagari
codepoints; typical page is OCR noise. Unusable as an artifact. S80's "effectively lost" is
confirmed. The DOCTRINAL gap is real and separate — Cheiro is Western palmistry; the Indian
tradition (mounts tied to grahas, different rekha nomenclature, linkage to Vedic houses) is
absent by accident. Fix path: re-source an English edition, or Devanagari OCR + translate.
Deva-keralam: 684 pages, 605 with substantial English, 12 empty, zero Devanagari — HEALTHY.
The F9 two-column alarm is overstated for this book.
Cheiro: 310 pages, 178 text / 127 diagram / 5 mixed; 132 empty = exactly the diagram+mixed
set. F3 vision fill produced zero entries for this book.

HEAD LINE HAS A SECOND, SEPARATE DEFECT. Retrieval now delivers correct head-line doctrine,
but the S71 Stage-1 valence defect is untouched: neutral disjunctive text ("intellectual
strength OR weakness") is labelled valence="supports". PROMPT layer, not retrieval. No
amount of retrieval work fixes it. Belongs to the S71 arc.

CARRY-FORWARD TO S82, gated, in order. (1) Resolve the one-call contract blocker; ship the
filter ON. (2) Add a fixture with an in-range page_ref — every one of the 9 first-round
failures logged "0 of N candidates in range", so no test exercises the filter's SUCCESS
path. (3) Rewrite accepted gap (c) — the "never rank" framing is obsolete. (4) Correct the
_N_RESULTS_PER_FEATURE justification comment. (5) F4 remediation, re-sized off PDF page
counts not progress.json. (6) Head-line valence (S71 arc). (7) Hasta re-sourcing decision.
Parked: Path D, F3, F9, F10, provider agnosticism, vision-citation policy.

HOUSEKEEPING STILL OPEN. Sessions 0-18 rollup remains in SESSION_LOG_ARCHIVE_S19-S66.md
under a heading that reads "NEVER archive this block" — the repair prompt was never run.
data/test_images/ holds three real hand photos, tracked, public repo. Suite baseline
3341/0/7/1xp.

## S82 — One-call contract resolved, palm page-range gate SHIPPED ON (2026-07-30)

Commits (5, all pushed): b85999e DATA range-map correction + page_ref range support in
_build_where · 5d258e2 RETRIEVAL one-call Chroma where-clause gate, post-filter/candidate
pool/fallback dropped · a69549a census script + report · 0334038 three-arm OFF/ON/WIDE probe ·
0dee13f flag ON. Suite 3354/0/7/1xp. Plus a history rewrite (force-push, no commit object).

BLOCKER CLOSED. The S81 one-call-per-feature blocker is resolved by pushing the page range into
the SAME search() call as a Chroma where-clause. Both S81 assumptions were verified in source
before any code changed, and one was WRONG.
- (a) FALSIFIED AS PROPOSED. $gte/$lte do accept int operands (chromadb 1.5.9
  api/types.py:1229-1233), but the proposed single-dict form page_ref={"$gte":s,"$lte":e} is
  rejected: an operator expression must hold EXACTLY ONE operator (api/types.py:1221-1225, and
  independently execution/expression/operator.py:155-158). A range must be TWO clauses under
  $and. Compounding it, _build_where wrapped values in {"$eq": v} unconditionally, so a
  passed-through dict would have been invalid a second time on the $eq operand type check.
- (b) CONFIRMED. Removing the unfiltered fallback is safe: per-feature empty retrieval was
  already a ratified graceful path (1 search call, ZERO LLM calls, validation.passed True,
  sources == (), feature routed to _build_decline_block) —
  tests/interpretive/test_palm_reading.py:410-432.
- The three one-call contract tests were NOT edited and pass. _FakeSearch absorbs arbitrary
  filters via **filters and the contract tests assert only the book_name and n_results KEYS, so
  an added page_ref kwarg is invisible to them. Verified before the change, not after.

DATA DEFECT CAUGHT BEFORE SHIP. data/cheiro_feature_pages.json still held the PRE-correction
split: thumb 85-94 (absorbing all of Chapter X) and fingers 95-97 (excluding it). S81 logged the
correction but never applied it to the file. Re-verified independently against the page-level
Cheiro export: p85 CHAPTER IX THE THUMB, p93 CHAPTER X THE JOINTS OF THE FINGERS, p95 CHAPTER XI
THE FINGERS, p98 CHAPTER XII THE PALM. Corrected to thumb 85-92, fingers 93-97. Under the old
post-filter a wrong boundary degraded to unfiltered search; under a hard gate with no fallback
p93-94 would have become ABSOLUTELY unreachable for fingers. Caught by checking the map before
flipping, not by a failing test.

CENSUS BEFORE MEASUREMENT (diagnostics/census_feature_page_ranges_S82.md, a69549a). page_ref
confirmed int in live metadata — a str would have made every $gte match nothing and read as a
retrieval defect. All 9 non-null ranges censused THROUGH the production _build_where against the
live DB: counts 7-30, minimum 7 against a gate of _N_RESULTS_PER_FEATURE=3, zero blocking, zero
thin, zero failures. Interior zero-chunk pages at heart 157-158 and sun 167-168 are the already-
registered plate/blank spread, not new. All 6 named chunk_ids found by DIRECT id lookup.

THREE-ARM DECISION (diagnostics/onoff_range_gate_S82.md, 0334038). OFF / ON / WIDE(n=10) over
8 of 10 features (sun line and markings resolved no quality in the LRH fixture — both UNMEASURED).
Inputs reused from scripts/probe_pass3_chunks.py via the retrieval_rank_probe_S81.py pattern,
with its three query-precondition assertions ported. 24 embedding calls, 0 failures.
- Gate is a NO-OP on 6 of 8 (ON n OFF = 3, identical sets) and CORRECTIVE on exactly 2:
  head line (2 of 3 OFF results out-of-chapter) and fingers (1 of 3).
- Head line is the deciding case. OFF rank 1 was p123_c0 at 0.6090, the highest score in any
  arm — the NOMENCLATURE table ("The Line of Life is also called the Vital..."), zero
  interpretive doctrine, outranking every real head-line passage because it names every line.
  OFF rank 3 was p135_c2, LIFE-line doctrine. ON returned three genuine head-line passages
  (p151_c2, p146_c2, p147_c0).
- "LET THE LLM CHOOSE FROM A DEEPER WINDOW" REFUTED, on text not argument. Head line's WIDE n=10
  held only 2 in-range chunks; the 8 out-of-range ones are other lines' doctrine that never names
  its own subject — "If the line leave the line of life..." (p135, life), "When the line is quite
  bare of branches..." (p160, heart). Chapter provenance is metadata; it is not recoverable from
  the text an LLM sees, and the embedding cannot recover it either, which is why they rank high.
  Also 3.3x token cost per reading.
- Earlier worry REFUTED: the gate does not exclude displaced head-line doctrine. The out-of-range
  chunks are OTHER lines' doctrine. No range widening needed.

OCR CORRUPTION — RE-DISCOVERED, NOT NEW. A fresh count of line-family corruption in the Cheiro
corpus (hne 20, lne 15, lme 4) reproduces diagnostics/bidirectional_corruption_census_S80.md
EXACTLY, and that census also carries the larger life->hfe at 34 which the fresh count missed.
S79 already established the cause (pipeline discards native text, re-OCRs with Tesseract); S80
established C1:C2 = 3.962, retiring PATH C and locking PATH D; S81's layer table already assigned
fate line to RETRIEVAL and head line to PROMPT and stated corpus repair fixes NEITHER. No new
census was written.
- NEW AND ACTIONABLE: 32 of the 51 line-family corruptions fall INSIDE ranges the gate now
  enforces, head line worst (p149 has more corrupted "line" tokens than clean; p154 is 4-and-4).
  The gate RAISES exposure to corrupted text: a corrupted in-range chunk previously had to
  outrank 460 competitors to reach the LLM, and now competes only against 7-30 chapter-mates for
  3 slots. Direction certain, MAGNITUDE UNMEASURED. Not grounds to revert — corruption cuts
  against out-of-range chunks equally and the gate's doctrine benefit is demonstrated.
- Page indexing pinned: census page_index is 0-based, page_ref = page_index + 1 (cross-checked on
  three examples). Relevant to S79's superseded off-by-one.

REPO HYGIENE. History purged of data/pdfs/ (5 PDFs, ~76 MB committed in 7277832, deleted in
5d0e0a4, blobs permanent until rewritten). git-filter-repo on a throwaway mirror, never the
working clone, so gitignored local assets (data/pdfs/, data/chroma_db/, PyJHora-main/) survived.
Pack 85.35 MiB -> 10.84 MiB, 523 commits and 405 HEAD files unchanged, force-pushed. Residual is
data/all_chunks.json revision history (11.88 + 7.20 + 3.47 MiB), a GENERATED artifact re-committed
whole on every re-ingest — the ongoing growth vector, purge candidate for a later pass along with
data/chunked_chunks.json (gitignored yet present in history). PyJHora-main/ was never committed.
No .env or secret ever committed.

CARRY-FORWARD OPENED.
- p123_c0 nomenclature attractor (DATA) — ranks 1 for head line, 7 for heart line; a table-of-
  names chunk polluting any line query not gated away from it. Now LATENT for the 9 ranged
  features, LIVE for any future feature without a range. Census structural chunks (contents,
  plate lists, running heads) before choosing between a page_type exclusion and a chunking change.
- Gate/corruption interaction above — magnitude unmeasured.
- _build_where bool hole — isinstance(v, int) accepts bool, so page_ref=(False, True) becomes a
  0-1 range silently; chromadb's own validator accepts it too. Unreachable by current callers.
  Fix: type(v) is int.
- Shipped default no longer pinned — the flip replaced test S82e's `assert
  _FEATURE_PAGE_FILTER_ENABLED is False` precondition with a monkeypatch, so nothing now asserts
  what the module ships with. Add a one-line test. Also rename
  test_page_range_gate_off_by_default_omits_page_ref_key — it is no longer "by default".
- sun line gate behaviour UNMEASURED (no quality resolved in the LRH fixture). Inferred safe from
  the a69549a census (range holds >= 3 chunks, cannot starve). Inference, not measurement.
- requirements.txt is a one-line stub (timezonefinder) with a comment saying so. The repo is
  public and is now the distribution artifact; nobody can reproduce the environment from it.
- PRIVACY, DEFERRED BY EXPLICIT DECISION: data/default_user/kundali_summary.txt (name, DOB, birth
  time, place) and 5 data/sessions/*.json remain tracked in a PUBLIC repo, against the locked
  "no PDF/palm storage, fresh upload every session" decision. data/sessions/ is gitignored but
  ignore rules do not untrack. A second history rewrite is cheap now and gets more expensive as
  commits accumulate.

S83 — Palm retrieval closed; failure-capture net shipped
- Rank sweep (validated answer key, 15 feature/quality rows, gated): 11/15 correct doctrine in
  top-3; 3 buried at ranks 4-8 (head-straight 4, heart-deep 4, heart-upward 8); the 1 "not found"
  (head-sloping) was a bad answer-key signature, NOT a retrieval failure.
- Heart-line frontend drop root-caused: RETRIEVAL, narrow — correct doctrine ranks 4-8 and the
  _N_RESULTS_PER_FEATURE=3 cutoff discards it before Stage-1. Pool not empty; Stage-1 not at fault.
- p123 attractor: pre-S82 dogfood (Jul 27) showed it firing live on head line; post-S82 gate
  (Jul 30) head sources p145 — gate fixed it live. Fully contained, no live leak (null-range
  'markings/other features' is a marks query, doesn't pull the line-name table). Content-role tag
  validated feasible (chromadb 1.5.9 metadata-only update, no re-embed) but DEFERRED to Path D /
  astrology track — no live justification.
- Vocabulary gap real in text (fate chapter uses "double/sister/branch", never "forked") but
  text-embedding-3-small bridges it (target ranks #1). Query rewording REJECTED by sweep (helps
  one row, harms others). No fix.
- Head-line valence bug (S71) still open, observed live Jul 30 (neutral "strength or weakness"
  rendered positive). PROMPT layer, untouched.
- SHIPPED: failure-only dogfood capture net (5b19f98). _run_had_failure gate in
  _capture_dogfood_run; 4 categorical threshold-free triggers (silence / all_rejected /
  wrong_source / instability) + capture_reason tag; fail-safe -> ["capture_error"]. Taxonomy
  signed off at 7 categories; v1 auto-detects the cheap categorical ones; contradictions rely on
  human eyeball of the captured block; near-miss & marginal-accept NOT captured by design.
- PARKED: rank-window widening (_N_RESULTS_PER_FEATURE 3->5) until the capture net accumulates
  real production silences — do NOT set the number from the S83 sweep sample.
- BETWEEN-SESSION ACTION: turn the dogfood capture flag ON in the deployed frontend (config, no
  code) — the net collects nothing until then.
S84 — Near-miss margin gate corrected to production-safe default; window=3 vindicated by live data
- Gated the S83 near-miss margin log's n_results=30 fetch behind ASTRO_DOGFOOD_CAPTURE
  (palm_reading.py) — Code had shipped it always-on in error, paying the capture cost in
  production too. Both _retrieve_per_feature and _search_with_page_filter now fetch 3 in
  production, 30 only under dogfood capture; full_candidates is [] when the flag is off (renders
  as NOT CAPTURED, already handled). 3 test assertions corrected to n_results==3, 1 new test locks
  the flag-on==30 path.
- Stale xfail removed: test_yogini_routing.py's yogini_dasha format_answer() dispatch confirmed
  shipped at S73/Prompt 5 (result_formatter.py's own docstring + live _format_yogini_dasha()
  branch) — xpass -> normal pass.
- Suite: 3360 passed / 7 skipped / 0 failed.
- 3 live dogfood runs (Jul 31, flag on) reviewed: near_miss_margin shows NO case of a
  correct/strong candidate buried past rank 3 for any failing feature (fate line, fingers, heart
  line, mount of jupiter all failed with top-3 scores 0.51-0.68 already in window).
  _N_RESULTS_PER_FEATURE=3 is CONFIRMED NOT the bottleneck for these misses — do not widen
  without new evidence; the S83 PARKED item stays parked.
- Recurring empty_first/unsupported pattern (fate line, heart line, mount of jupiter) across old
  AND new captures — suspect Stage-1 overlap floor (0.4, claim_extraction.py) as the real
  bottleneck, not a rank problem. thumb's one observed attempt_1 failure: overlap 0.08 vs floor
  0.4 (retry succeeded). NEXT SESSION'S REAL LEAD: investigate the 0.4 overlap floor, not the
  retrieval window.
- dogfood_capture.md (10 RUN blocks) archived verbatim to
  diagnostics/archive/dogfood_capture_2026-07-31.md (91898 bytes, 10/10 runs preserved); working
  file cleared to 0 bytes — insights already captured above.

## S84 addendum -- Palm retrieval restructured: offline-verified-extraction pilot supersedes overlap-floor lead (2026-08-01, docs-only)

Carry-forward from this session's near-miss-margin re-analysis (diagnostics/latest_run.md)
and the rule-engine-v1_5-design.md cross-chapter-conditions addendum: Cheiro/palm retrieval
is being restructured from live per-request Stage-1 extraction to an OFFLINE,
human-verified extraction pipeline into a rules table, scoped BOOK-WIDE rather than
chapter-grouped. Two root causes drove this, both now recorded in
diagnostics/KNOWN_PATTERNS.md: (P-016) Stage-1's live per-request extraction against the
0.4 overlap floor has no verified ground truth to calibrate against, producing
`empty_first`/raw=0 outcomes that vary run to run for similar inputs; (P-015) compound
conditions spanning two features (e.g. head-line + heart-line combination doctrine) are
genuinely cross-chapter and cannot be assembled by the S82 page-range gate's
chapter-scoped retrieval, however deep the window goes.

THIS SUPERSEDES, NOT ADDS TO, the previously-planned next step. S84's own "NEXT SESSION'S
REAL LEAD: investigate the 0.4 overlap floor, not the retrieval window" is superseded by
this pilot -- a future session should NOT separately pursue Stage-1 overlap-floor tuning
as its own thread. The pilot's offline/book-wide extraction approach is intended to
replace the mechanism the overlap floor was gating, not to be debugged alongside it.

Framed explicitly as a PILOT (Cheiro/palm only): validates whether offline-verified,
book-wide extraction is the right method before any astrology-book (BPHS/Phaladeepika/
Saravali-class combination rules) application is considered. Does NOT touch or partially
satisfy the V1.5 Rule Engine Foundation gates (still: not before V1 ships; still gated
behind the rule-of-three / Ashtottari as the 4th hand-coded domain) -- a single-domain
pilot proceeding is explicitly NOT the generalized multi-domain engine starting; see
playbook_export/decisions/rule-engine-v1_5-design.md's second 2026-08-01 addendum and
CLAUDE.md's V1.5 register entry for the cross-linked statement of this distinction.

Files touched this entry's session (all docs-only, additive, no RATIFIED token required
per Working Style #14's docs/diagnostics exemption): diagnostics/KNOWN_PATTERNS.md (rows
P-015, P-016 added; P-014's Status column annotated with a superseded-by pointer),
CLAUDE.md (V1.1 register bullet added; V1.5 register entry cross-link line added),
playbook_export/decisions/rule-engine-v1_5-design.md (second addendum appended), this
SESSION_LOG.md entry. No production code changed.

## S85 — Palm extraction reliability: vision-descriptor width/direction + incompleteness retry (2026-08-05 to 2026-08-06)

Commits:
- `762a12e` feat(palm): deterministic phrase-normalization layer + extractor reliability + L_023 fix
- `cf9ae2c` fix(palm): render phrase_promotions + engine diagnostic keys in dogfood capture
- `69756df` feat(palm): add line width to vision descriptor -- unblocks L_001 (p134 healthy-line rule)
- `66807d8` fix(palm): retry incomplete batched extraction with corrective re-ask
- `01a9a22` feat(palm): elicit head-line direction (straight vs sloping) in vision descriptor

Key outcomes:
- Vision-width fix unblocked L_001 (p134 healthy-line rule): a narrow-life-line hand fired
  the rule with a p134_c0 citation; a medium-width hand correctly stayed silent (no forced
  rule where doctrine doesn't clearly apply).
- L_023 / phrase-normalization sweep work deprioritized -- low ROI, since the vision
  descriptor cannot reliably discriminate the finer distinctions that sweep targeted.
- observation_extractor.py's single batched LLM call now retries on detected incompleteness
  (substantive input prose but zero tokens AND zero unmapped for a feature), up to
  ASTRO_EXTRACT_INCOMPLETE_RETRIES times, with each retry appending ONE corrective user
  message naming the specific dropped features (temperature=0 means an identical retried
  request would just reproduce the same partial response -- the correction is what lets the
  retry's output actually differ). Keeps the fewest-dropped attempt; fail-open, never raises,
  never fabricates a token. New `ObservationRecord.extraction_retries` diagnostics field.
- Head line's own descriptor line now explicitly elicits `direction` (straight across vs
  sloping toward the wrist/Mount of Luna) -- the core straight=practical/sloping=imaginative
  doctrine key that the old "same attributes [as life line]" phrasing never asked for.

Multi-hand test result (from diagnostics/dogfood_capture.md's final captured RUN block,
`2026-08-05T22:09:59.701587`): this run PREDATES both the incompleteness-retry fix
(`66807d8`, committed 2026-08-06T10:07:52+04:00) and the head-direction descriptor fix
(`01a9a22`, committed 2026-08-06T10:18:58+04:00) -- it is the problem-DEMONSTRATING run,
not a post-fix validation. It confirms: (1) the width fix already live and working --
Line of Life tokens included Width=narrow, L_001 fired citing p134_c0; (2) the exact
silent-drop failure mode that motivated the retry fix -- Line of Head and Line of Heart
both had substantive raw_prose ("deep, narrow, long, slightly curved, no clear breaks or
forks") but `tokens={}` AND `unmapped=[]`, i.e. zero extraction despite real content; (3) no
Direction token anywhere, since the head-direction descriptor change wasn't live yet either.
No dogfood run has been captured SINCE `66807d8`/`01a9a22` landed -- live recovery of
head/heart tokens and appearance of a Direction token are UNVALIDATED, pending a fresh
dogfood capture. Do not report this pair as "confirmed working" until that capture exists.

Deferred (not attempted this session):
- Left/right hand split -- architectural change, touches locked-core `palm_reading.py`;
  merge seam is `_gather_feature_texts` (`agent/interpretive/palm_reading.py:468`), which
  joins LEFT+RIGHT prose into one string per feature before extraction -- e.g. the width
  token above resolved to only "narrow" (LEFT's value) despite RIGHT independently stating
  "medium width", an ambiguity a hand-split would resolve. V1.1-scope, per CLAUDE.md's
  V1 palm-drop lock (all palm code stays intact, not touched, pending V1.1). Also deferred:
  a hand-dominance input (which hand is dominant) that a split would need to make use of.
- Gap A (clarity/ambiguity handling) -- deprioritized alongside the L_023 sweep, same
  low-ROI-given-vision-model-ceiling reasoning.
- `agent/interpretive/claim_extraction.py` (+ its test) -- an OLDER, still-uncommitted
  change from a prior session (E-5: disjunctive-taxonomy fail-closed, S71 head-line
  valence bug fix), left dirty and untouched across every task this session per explicit
  per-task staging instructions. Still uncommitted as of this entry.

## S86 — Verification architecture + head-line authoring start (2026-08-08)

- **Voicing Step-1 committed** — LLM `[OBS]` fabrication removed from claim voicing; the
  reading body now renders empty when no rule fires, rather than an LLM-composed
  observation standing in for a doctrine claim. Step-2 (deterministic bare-obs rendering,
  so an empty body doesn't read as a UX dead end) is still PENDING/blocking for UX.
- **Dominant-hand radio → Right default** — committed.
- **VERIFICATION ARCHITECTURE adopted** (fidelity-not-truth; verify the predicate
  vocabulary once rather than each rule; §6 mechanical checks; whole-chapter reasoning,
  never a retrieved chunk or single page in isolation). Locked into CLAUDE.md. Specs:
  `Prior-Art_Investigation_Deterministic_Citation.md` + `VERIFICATION_ARCHITECTURE.md`
  (project files).
- **Head-line "unauthorable" FALSIFIED** — p145's "intellectual strength or weakness"
  sentence is a chapter SCOPE sentence, not a disjunctive rule and not grounds for
  unauthorable; p146-148 carry ~27 authorable base rules in Ch VII (Cheiro), independent
  of hand-type. See `diagnostics/head_chapter_doctrine_map.md`.
- **S83 heart-line retrieval bug ELIMINATED** — retrieval itself works; the heart-line
  gap is an AUTHORING gap, not a retrieval defect. p157-158 being absent from the corpus
  is EXPECTED (they are image plates, confirmed), not a chunking failure.
- **OCR reality confirmed** — the old JSON corpus is the worst-quality source; the PDF
  text-layer and a manual paste both yield the same, cleaner OCR quality. No clean
  born-digital edition exists (Project Gutenberg's Cheiro text is a different book, not
  usable as a cleaner source). Clean page-anchored citation corpus built:
  `data/cheiro/cheiro_clean_v1.json` (SHA `644f667`), `page_ref = pdf_index + 1`
  validated, `page_type` inherited from the source. Reference full text:
  `data/cheiro/cheiro_pdf_fulltext.md`.
- **Fidelity anchor = human image-proofread of CITED sentences only** — not a bulk OCR
  re-clean. Example: the stored "Boliemianism" garble was caught and corrected to
  "Bohemianism" by eyeballing the page image for that one cited span, not by an OCR pass
  over the whole corpus.
- **H_026 authored** — Ch VII row 7 ("entire line slight slope → leaning toward
  imaginative work"), the first span-anchored extractive rule under the new
  verification architecture, §6-passing (source spans resolve, lexically grounded,
  operative not scope, `Line of Head` now has 23 rules, `Slope`/`downward` vocabulary
  already closed-registry). Live dogfood-confirmed voicing the imaginative-work claim
  before commit. Committed `be9d9b5` on `wip/interpretive-pilot`.

## S87 — Slope silence fixed via ontology binding; borderline let-be ratified (2026-08-09)
- **Slope-line silence ROOT-CAUSED to the OBSERVATION->TOKEN layer** (NOT retrieval, NOT
  authoring — both previously settled). Two parts: (a) vision emitted narrative prose
  instead of a token -> fixed with an explicit SLOPE enum in the vision prompt
  (`agent/palm_processor.py`); (b) the ontology's flat value pool let `Slope` map to
  `"sloping"` instead of `"downward"` -> fixed with `attribute_value_binding` (per-attribute
  value narrowing in `data/ontology_registry.json`), consumed GENERICALLY by
  `observation_extractor.py`'s `_values_for_attribute` — no slope-specific code added.
- **H_026** (the first head-line rule) now FIRES and VOICES live, cited to Cheiro p146.
  Committed `5ace6e8` on `wip/interpretive-pilot`.
- **RATIFIED**: `attribute_value_binding` is the standard pattern for any prose->token gap —
  the ontology is the single source of truth, consumption is generic, no hardcoded phrase
  lists. Adding a bound attribute is registry data only, no extractor/rule code change
  required.
- **RATIFIED**: borderline straight-vs-slight head slope is INHERENTLY non-deterministic.
  Measured on Athira's right hand, N=15 independent calls at temperature=0: `straight` x13,
  `downward` x2 — the vision model itself alternates its own description, not just the
  token. A follow-up explicit slope-threshold prompt edit (cheap N=6 re-test, same hand) did
  not eliminate the flip either (5 straight / 1 downward). DECISION: LET IT BE — do not
  force, sample, or stabilize the boundary; a borderline line honestly reads differently
  across calls, as different palmists would read it differently. Accept the per-call slope;
  H_026 fires or not on whatever the model sees that call.
- **Slope_Magnitude** (`slight`/`very`) attempted and DISCARDED by decision — not needed
  until rules for clearly-sloping hands (doctrine row 8, Cheiro "very sloping" ->
  Bohemianism) are authored. A deliberate deferral, not a gap. NOTE: the uncommitted
  prompt/ontology additions for this experiment (SLOPE MAGNITUDE vision lines, the slope
  threshold text, and the Slope_Magnitude ontology entries) are queued for a working-tree
  revert but NOT YET reverted as of this entry — a separate git-op task stopped on its own
  safety gate (unrelated modified tracked files: `agent/interpretive/claim_extraction.py` and
  two of its tests) before running the checkout. Committed state (`5ace6e8`) already carries
  only the SLOPE enum + `attribute_value_binding.Slope`, unaffected either way.
- **Bucket-2 hardcoding audit** (prose->token conversion done via hand-written phrase lists,
  the pattern `attribute_value_binding` replaces) recorded for later retirement:
  `phrase_normalizer.py` + `data/palm_rules/palm_phrase_lexicon_v1.json`
  (`match_any`/`must_not_match`), and `palm_reading.py`'s `_ABSENCE_PHRASES`/`_is_absence` +
  needle keyword routing (Presence should become an ontology attribute).
  `observation_extractor.py` is the GOOD constrained-extraction template going forward.
S88 ORDERING LOCK: H_001 (old-schema duplicate of H_027, same Jupiter+touching+long doctrine) MUST be retired or cross-referenced BEFORE any Starting_Point/Proximity vision-enum + attribute_value_binding is authored — both fire identically once those tokens bind, causing double-voicing. Both currently silent (tokens unbound), so latent not live.

## S89 (2026-08-09) — Relational vision block validated, enhancement rejected

GROUND TRUTH (Athira right palm, human-verified): HEAD origin=Line of Life (joins under index, touching/intertwined); slope=slight-down; ends left/lower palm edge. HEART origin=between index-middle (Jupiter); ends pinky/percussion (Mercury); medium gap to head line (quadrangle). FATE origin=Wrist; deep lower / faint upper; ends ~Saturn. No marks on any line.

ENHANCEMENT VERDICT: A/B N=10 each — REJECTED. Enhanced 13/15 vs original 14/15 GT; faint fate upper NOT surfaced (0/10 both); zero fabrication both. Revisit only for genuinely unreadable images, not as default stage.

CALIBRATION FINDINGS: (1) proximity_degree is dead — model says "medium" universally; only proximity_target carries signal; degree-based antecedents (e.g. H_027 "touching") won'''t fire → honest silence. (2) Vision cannot read intra-line depth variation (faint-upper fate read as uniformly deep 20/20).

## S90 (2026-08-09) — Relational machinery complete; Prompt 5 re-sequenced (enumeration-first). SESSION CLOSE
STATE: relation_target refactor — engine+vision+extractor WIRED and dormant; rules NOT migrated. Break here deliberately.
COMMITS: 4bc091f H_027; 740db30 S88 ordering lock; b62d1ef ontology (dropped premature binding, kept relation_target_registry); f320c24 loader count fix; d617ec1 engine consumes relation_target (fail-closed, +6 tests); 6a3053a E-5 gate (S71); 4640ad0 vision emits directed fields; 7c9cd0d docs; f920d3b extractor routes targets dict (inert).
SEQUENCING LAW (RATIFIED): attribute_value_binding bound LAST, atomically with rule+pool migration -- binding early makes the extractor drop baked values live rules need (suppression test caught it; KNOWN_PATTERNS P-017).
LLM VISION VERIFIED OK (n=1): on human-ground-truthed Athira right palm, relational vision (origins/terminations/targets/quadrangle/slope) = 14/15 MATCH/ACCEPTABLE, ZERO fabricated marks across 20 runs. Approach VALIDATED. The earlier "hallucination" alarm was partly a reviewer error -- head-heart proximity flagged as fabricated is the real Cheiro quadrangle. DO NOT re-open this.
CALIBRATION LIMITS (honest silence): (1) proximity_degree dead -- gpt-4o says "medium" universally; use proximity_target only. (2) vision can't read intra-line depth (faint-upper fate -> uniformly deep 20/20).
ENHANCEMENT: REJECTED (A/B N=10; enhanced 13/15 vs original 14/15; faint lines 0/10; zero fabrication). Revisit only for genuinely-unreadable images.
PALM SCOPE (RATIFIED): a flat photo can't show what a palmist sees by folding/pressing/tilting. Assert ONLY clearly-visible lines; faint/occluded/fold-dependent = honest silence, astrology track covers the gap. (Also why enhancement was rejected -- forcing faint lines in software is the same error.)
ORIGIN/TERMINATION ARE A CLOSED, BOOK-DERIVABLE SET PER LINE (Sulabh's call): Cheiro fixes the possible origins/terminations per line -- not open-world, limited permutations. Direction is per-line convention (head/life = index-side origin across toward percussion/wrist; heart read percussion->fingers; fate wrist->up), so origin=one fixed end, termination=other -- halves the space. Consequence: constrain vision to per-line menus (deterministic/citable), don't build general LLM origin logic. No "does origin vary across hands" test needed -- the book is authority on what's possible; if it names several, it varies.
GROUND TRUTH (Athira right): HEAD origin=Line of Life (joins under index, touching/intertwined); slight-down slope; ends left/lower palm edge. HEART origin between index-middle (Jupiter); ends pinky/percussion (Mercury); medium gap to head line (quadrangle). FATE origin=Wrist; deep lower/faint upper; ends ~Saturn. No marks.
PROCESS LESSON: run the full suite on EVERY code-consumed/source commit (H_027 commit skipped it -> 2 stale-count failures undetected until S89). ontology_registry.json is code-consumed -> NOT docs-exempt.
NEXT (new session) -- Prompt 5 RE-SEQUENCED, enumeration-first:
  5a. BOOK-ENUMERATION PASS (read-only, design-chat, FIRST): scan data/cheiro/cheiro_clean_v1.json head/heart/fate/life sections; enumerate every ORIGIN and TERMINATION landmark the text names per line, each with page citation. Report per-line CLOSED menus. Verify "small closed set" (expect ~4-6/line; flag any long tail). No code.
  5b. Constrain palm_processor vision prompt ORIGIN/TERMINATION to the per-line menus from 5a. This DISSOLVES the Mars vocab-drift -- the menu names Upper/Lower Mount of Mars from the book if present, no generic alias needed.
  5c. MIGRATION: rewrite baked antecedents -> (value + relation_target); add bare qualifiers to values pool + attribute_value_binding (bound LAST); un-park H_014/016/017/022; retire H_001 (S88 lock); migrate H_027; re-verify each antecedent vs source_quote.
  CAVEAT: a closed menu removes INVALID answers, not WRONG ones -- vision can still pick the wrong menu item; per-line reads still spot-checked vs ground truth on a few hands (accuracy != validity).

## S90 addendum — push confirmed (2026-08-09)
wip/interpretive-pilot pushed to origin: b60d3fa..98714c9. Verified post-fetch: local HEAD == origin/wip/interpretive-pilot == 98714c93036b2db35652952c40c1f28c92847172, 0 ahead/0 behind. Chain confirmed present on remote through the S90 docs commits (98714c9 patterns, 3e9e08c claude register, 2d3e8c9 session close) and Prompt-4 extractor commit f920d3b. Full verification detail: diagnostics/latest_run.md (overwritten this run).

## S91 — Relational-target inline refactor (5a → 5c-P). HEAD 71323eb (pushed to origin).

Commits this session (all pushed, wip/interpretive-pilot):
- e07d955 5a: freeze Cheiro origin/termination closed menus (doctrine, inert)
- e3ed2ed 5b-pre: add "Junction of First and Second Fingers" relation_target (meta 1.4.0)
- 554ceec 5b: constrain vision RELATIONAL menus per line + Mars split (Upper/Lower) + LAW 2
- 2e1c850 5b.5-pre: parametrize describe_palm_image temperature (default 0.0)
- 04717e6 B(i): extract_relational_targets reads inline <LINE>: format (backward-compat, _LINE_HEADER)
- ded49eb B(ii): fold ORIGIN/TERMINATION/PROXIMITY/BRANCHES inline under each line (RELATIONAL TARGETS section removed)
- 71323eb 5c-P: capture PROXIMITY degree as observation value (inert/unwired)

Findings (settled, do not re-litigate):
- LAW 2 (heart direction) finalized: finger/mount end = ORIGIN, percussion = TERMINATION. Cheiro p156/159/160 + external corroboration; modern "origin=percussion" rejected.
- Inline fold (B) fixed the ~40% RELATIONAL block-drop: measured head 8/8, heart 8/8, clear-fate 8/8; fate "drops" on faint hands are honest-silence (0/16 present-but-skipped). Canning refuted — atypical Moon-origin hand read ORIGIN "Mount of Luna" correctly.
- temp=0 is NOT deterministic on the same image (measured: 5/5 distinct). Temperature is not the lever for block-drop; inline placement was.
- Match semantics: a directed antecedent requires observation[feat][attr]==value AND targets[feat][attr]==relation_target. value:null makes the value-check no-op -> target-only match (EXECUTED, fires correctly). Proximity needs degree in observation (FLAT string) + landmark in targets.
- 5c-P captured the proximity degree {touching|medium|distant} as a nested token via new extract_proximity_observations(); inert -- not merged into match()'s observation, not bound (bind-last).

Decided-but-not-done (5c work): (a) merge+flatten P into match observation; (b) bind {touching,medium,distant} LAST; (c) extend head-TERMINATION menu + vision prompt with "Line of Heart" for H_022 (Cheiro p154); (d) retire the stale S89 "degree dead/always-medium" note.

## S92 — 5c core complete: proximity-degree relational pipeline live, H_027 migrated (2026-08-14). SESSION CLOSE

Commits this session (all pushed, wip/interpretive-pilot):
- 63b4df6 5c step 1: wire extract_proximity_observations -> flat observation (P-wins merge, post-to_tokens; touching kept P-exclusive)
- 76340f9 dogfood: surface observation/targets/proximity_observations in stage1 diagnostics
- 7589cde 5c step 1.5: isolation tests (degree reaches observation; P-wins over LLM-emitted Proximity)
- e2297ab 5c step 2.5: value:null = TRUE target-only wildcard in _antecedent_fires (ENGINE CHANGE)
- f59f04f 5c step 2: bind Proximity degree vocab {touching,medium,distant} (bind-last)
- 66b98f9 5c step 3: migrate H_027 to split-relational antecedents; retire H_001 to retired_superseded; realign count pins
- e400de2 5c step 7: retire stale S89 proximity-dead-axis comment

Findings (settled, do not re-litigate):
- CORRECTION to S91: value:null did NOT "fire correctly with no engine change." Original _antecedent_fires killed a directed antecedent whenever an observation value was present (verified by execution). 2.5 fixed it: value-equality is now enforced only when antecedent.value is not None; value:null is a true target-only wildcard. Zero regression (identical branch for all value-not-None antecedents = 100% of loaded rules).
- 'touching' is P-EXCLUSIVE by design: absent from the global value pool, so to_tokens drops any LLM-emitted 'touching'; only extract_proximity_observations supplies it. Binding it (step 2) logs an EXPECTED orphan-info. Do NOT add 'touching' to the pool — that would let the LLM inject it and break the invariant.
- retired_superseded: new top-level array = retirement convention (loader reads validated_candidates only, so moving a rule out = it never loads). H_001 lives there, superseded_by H_027.
- H_027 is the FIRST live relational rule. Fires on ORIGIN Mount of Jupiter + PROXIMITY touching to Line of Life + Length long; correctly silent on Line-of-Life-origin hands. Verified against on-disk committed files, not a report.
- Degree axis is REAL and multi-valued (touching + medium both emitted across dogfood 2026-08-12/13/14). S89 dead-axis RETIRED. RATIFIED by Sulabh: head->life = 'touching' on every sampled hand is a GENUINE homogeneous sample (all Athira, head genuinely touches life), NOT a vision bias. Do NOT re-investigate.
- Workflow adopted: push after every ratified commit (GitHub == local). New session: git pull wip/interpretive-pilot before reviewing.

Decided-but-not-done (5c steps 4-6, in order):
- Step 4: un-park H_016 (FIX contradictory distant+medium -> single Proximity=medium + target Line of Life) and H_017 (Proximity=distant + target Line of Life). Machinery proven; authorable now; will fire in sim. LIVE head->life medium/distant validation DEFERRED — no separated-origin hand sample exists (Sulabh has none). Author sim-validated; accept deferred live validation.
- Step 5: un-park H_014 (Branching value:null + target Line of Heart; DROP the unreadable "upward" antecedent). PREREQ CHECK: confirm BRANCHES_TO is parsed into targets by extract_relational_targets — NOT yet verified (dogfood only ever emitted BRANCHES_TO: none).
- Step 6: H_022 — BLOCKED on new vision capture: (a) add "Line of Heart" to head TERMINATION closed menu (data/_doctrine + palm_processor.py vision prompt, Cheiro p154); (b) capture Position:high (absent from observation today). Design task, not a migration.

Parked smells: Thumb Proximity='medium' (from "moderate angle") — Proximity attribute overloaded for non-line features; harmless (no thumb-Proximity rule), needs its own attribute if ever ruled on. Untracked probe/scratch files accumulating — gitignore/clean.

## S93 — 5c steps 4-5 complete: H_016/H_017/H_014 un-parked; all relational rules live (2026-08-14). SESSION CLOSE

Commits (all pushed, wip/interpretive-pilot):
- dc1b990 4a: un-park H_017 (Proximity=distant + target Line of Life); pins
- 51e519f 4b: fix H_016 contradictory antecedents -> single Proximity=medium + target Line of Life; un-park; pins
- 67c5cc7 5:  un-park H_014 as single Branching value:null + target Line of Heart (drop "upward"); pins

Findings (settled, do NOT re-litigate):
- H_016 was authored BROKEN: two AND-joined antecedents (distant AND medium) -> can never fire. Fixed to single Proximity=medium + target Line of Life. distant is H_017's job; no third degree-rule lost.
- H_014 redesigned: single antecedent Branching value:null + target Line of Heart. value:null (not "branched") is correct -- branch signal lives in `targets` (BRANCHES_TO landmark), never as observation VALUE (mirrors H_027). "upward" Direction antecedent DROPPED as unreadable/redundant.
- BRANCHES_TO is FULLY WIRED end-to-end (verified by execution): vision emits it for head/heart/fate (palm_processor.py ~L224/230/236, menu includes Line of Heart) AND extract_relational_targets maps BRANCHES_TO->Branching (observation_extractor.py L382). So H_014 is LIVE-capable the moment a branching hand is uploaded -- NOT deferred-live. Only a sample gap remains (Athira hands emit BRANCHES_TO: none).
- H_016/H_017 stay deferred-live: no medium/distant head-life hand exists; verified:true is sim-validated only, not a live win.
- KNOWN DEBT (proved by execution): extract_relational_targets does exact single-member registry matching, so a multi-landmark BRANCHES_TO ("Line of Heart, Mount of Saturn") is DROPPED WHOLE -> H_014 false-negative. Fix is NOT a comma-split: targets[feature][attribute] is a single str and _antecedent_fires does ==, so multi-branch needs str->set in extractor AND engine AND all relational tests (multi-layer, Opus). DEFERRED -- zero branching hands in corpus (SAMPLE-before-SCALE).
- Every commit reviewed against the DEVICE tree + engine re-executed independently before ratification. 270 passed / 4 skipped throughout. Pins realigned each commit (test_palm_rules_table.py L31 44->47, L360 57->60). All un-parks: verified:true / verifier Sulabh / verified_date 2026-08-14 / status key removed / source_fidelity null.

State: parked_pending_relation_target = [H_022] ONLY. validated_candidates = 47. retired_superseded = [H_001]. HEAD 67c5cc7.

Decided-but-not-done (next, in order):
- Housekeeping: gitignore untracked probe/scratch files (S92 smell). Trivial, Haiku.
- Step 6 (H_022) -- LAST parked rule. BLOCKED, needs design (6a, OPUS): (a) extend head-line TERMINATION closed menu to include "Line of Heart" (palm_processor.py vision prompt + data/_doctrine, Cheiro p154); (b) add Position:high capture -- SCHEMA SUBTLETY: TERMINATION already maps to the "Position" attribute as a LANDMARK (target), so H_022's Position=high is a separate VALUE axis on the same attribute name (value/target split, same pattern as Proximity). H_022 antecedents = Position=high (value) AND Length=reaching_Line_of_Heart (value + target Line of Heart). Then 6b implement vision change + re-dogfood for regression (Sonnet edit / Opus review), 6c author H_022 (Sonnet).
- DEFERRED debt: multi-branch BRANCHES_TO str->set engine change -- only when a real multi-branching hand appears (Opus, multi-layer).

Workflow unchanged: one file/one task, report-first to diagnostics/latest_run.md, RATIFIED authorizes commit, push after each commit, git pull wip/interpretive-pilot before reviewing.

## S94 — 5c step 6 ABANDONED; verification-architecture pivot; ensemble-reconciliation sweep DESIGNED (2026-08-16). SESSION CLOSE

Design-chat + one probe. NO ratified source commits. New session: git pull, confirm HEAD, TRUST this log.

Built: scripts/rule_vocabulary_closure_gate.py (registry-level vocab-closure gate) + run. [confirm commit state on pull]
Applied-but-ABANDONED (device tree, uncommitted, DO NOT SHIP): 6b placement→Position edits 1-3 (palm_processor PLACEMENT subfield + TERMINATION+Line of Heart; observation_extractor.extract_placement_observations; palm_reading merge). Edit 4 (bind Position) correctly HELD, never applied.

Findings (settled, do NOT re-litigate):
- D1 REVERSED: never add Position to attribute_value_binding — _values_for_attribute keys it by attribute-name GLOBALLY, so Position:["high"] narrows Stage-1 vocab for EVERY Position-feature -> silently kills ~14 verified rules. Verified.
- H_022 ant1 (Line of Head/Position/high) == verified H_021 (same p154 quote). Position=high is a LATENT FAMILY (H_021,H_010a,H_020; HL_005/006/011 high; HL_012/021 low), not a new axis.
- "Position" is OVERLOADED: height {high,low} AND location {under_Mount_of_X, terminating_at_X, running_through_Square, touching_Line_of_X}. Single slot/feature -> the placement->Position merge (palm_reading.py ~L2047) clobbers location tokens. Claude Code's comment "to_tokens has no route for Position" is FALSE (verified _VALID_TRIPLES routes it). This is why 6b was abandoned.
- CLOSURE GATE: 10 structurally-DEAD antecedents, ALL verified=True. 5 DRIFT (H_013 on->at Jupiter; H_023 terminating_on_Mount; H_024 Moon->Luna; HL_002 Finger->Mount Jupiter; H_025 doubled->double), 4 ATTR-UNMAPPED (H_018/019/020 Hand/Type; HL_015 heart/Presence/faded), 1 FEATURE-UNMAPPED (HL_014 heart/Branching/single).
- SOURCE REVIEW (do NOT batch-apply gate's difflib nearest-token — wrong on 2): only 2 safe normalizations (H_025, HL_002). 3 MIS-MODELED not misspelled -> normalizing fires WRONG: H_013 (source = offshoot into a STAR on Jupiter -> BRANCHES_TO Jupiter + Star), H_024 ("Toward Mount of Luna" -> BRANCHES_TO Luna; gate wrongly said Sun), H_023 ("any particular mount" -> parametric family). 5 real schema gaps.

STRATEGIC PIVOT (RATIFIED by Sulabh):
- Local per-rule fixes + parking REJECTED (doesn't scale to 600-1,200 Cheiro / 5,000-20,000 astrology rules). Root cause = MISSING normalization layer between open surface forms and a closed canonical ontology + hand-authored rules bypassing it. Fix = enforce the T-box/A-box split VERIFICATION_ARCHITECTURE §5 already specifies.
- Fidelity-at-scale = MEASURED, not exhaustive human verify (impossible at ~15k rules): (1) closure gate = pipeline fidelity [built]; (2) EXTRACTIVE rules (verbatim spans, not paraphrase); (3) verify the bounded VOCABULARY (~200-500 atoms) by hand, not every rule; (4) ENSEMBLE with disagreement-only human tickets; (5) statistical SAMPLING + fidelity disclaimer.
- Vocabulary built FROM rules (Sulabh) but VALIDATED against the cited chapter (reconciliation = his reconciliation_<line>.md convention, corpus-wide). Rules tagged by chapter (source_page present) for the later compound-precedence layer.

DESIGN LOCKED — Ensemble Reconciliation Sweep (Option 1, two-phase):
- Unit = CHAPTERequence wording, NOT char offsets (S68 line-wrap lesson).
- Roster review: no conflicts. Fold-ins: persist raw extractions committed (WS#16); calibration golden set; pin cheiro_clean_v1.json (not OCR fulltext); validate chapter boundaries first.

BLOCKERS (external): only OpenAI wired (no anthropic/google client) — full-run ensemble needs a scripted 2nd family key. No 52-chapter map (cheiro_feature_pages.json = ~10 feature ranges). Neither blocks the pilot.

NEXT (in order):
- 6-PILOT (hardest-case, head line): Step 1 = Cowork Claude blind extraction of head-line chapter -> diagnostics/ensemble_recon_headline_claude.json. Step 2 = Sonnet script: gpt-4o member B + Python reconciliation + CALIBRATION (H_013->FABRICATED-MISMODELED, H_021->AUTO-VERIFIED). PASS before scaling.
- If PASS: validated 52-chapter map -> Phase A induce+freeze -> Phase B full sweep.
- Deferred: multi-branch BRANCHES_TO str->set (Opus); H_022 authoring (subsumed); wire closure + citation + NEW extraction-reachability gates into CI; the 8 non-safe dead rules burned down BY the sweep, not hand-patched.

Workflow unchanged: one file/one task, report-first to diagnostics/latest_run.md, RATIFIED authorizes source commits, push after each commit, git pull wip/interpretive-pilot before reviewing.

## S94 -- Palm interpretation architecture pivot (RESOLVED)
DECISION: Abandon deterministic rule-MATCHING for interpretation. New architecture = code-gate + whole-sentence LLM select.
WHY: Four matcher designs (token, span-overlap, condition-decomposition, closure-gate) each failed by relocating a fidelity leak, not fixing it. Root cause: any transform of a rule BEFORE the answer loses meaning (HL_021 narrow, HL_002 "even from the finger", H_027/H_002 confusion).
VALIDATED ARCHITECTURE (all 5/5, committed):
  1. Rules stored as VERBATIM Cheiro sentences + involves-tags + page. No tokenized conditions.
  2. RETRIEVAL = deterministic set-membership on hand-state features (dumb, not semantic).
  3. Hard-fact GATE (pure Python): drop any rule whose hard prerequisite (origin/position/presence) is not satisfied by the hand-state, BEFORE the LLM sees it. Proven to make fabrication structurally impossible (H_027 Case B: 5/5, "Jupiter" cannot appear).
  4. LLM reads PRE-FILTERED whole sentences, fires all that fully apply, MERGES into one reading, quotes verbatim. Fabrication guard = output quote must substring-match stored text (held 5/5 every variant).
KEY FINDINGS:
  - Ensemble reconciliation (S94 early work) DEMOTED: it is a COVERAGE sampler + an EVAL harness, never a truth judge. Committed pilots: ensemble_recon_pilot_headline.py (calibration PASS), heartline holdout (frozen matcher generalized, 0 edits).
  - Fabrication is NOT catchable by fuzzy two-reader matching; it is caught by (a) code-gate on hard facts, (b) verbatim output-quote check. Split: hard/deterministic on structured facts, soft/LLM on prose.
  - Collision scan: 19 pairs / 23 of 47 rules need a hard-prerequisite tag; discriminators are ONLY origin/position/presence -> one repeatable gate, ~half-day authoring, not 140 bespoke tags.
COMMITS THIS SESSION (wip/interpretive-pilot): head-line reconciler validated; head-line pilot artifacts; heart-line holdout; gate-proves-no-fabrication smoke test; collision scan.
SETTLED, DO NOT RE-OPEN: matcher-based interpretation is dead; decomposition/condition-rewrite is dead (paraphrase leak); "reject on single miss" is WRONG (kills valid co-fires); the seam is code-gate + whole-sentence LLM.
NOT YET DONE: (1) author hard-prereq tags for the 23 collision rules; (2) build the eval harness (known-answer hands -- the only thing that catches coverage/precedence errors, which the fabrication guard cannot); (3) vision layer (photo -> hand-state) -- UNTESTED, deferred; precedence tie-break (head-vs-heart strongest) UNTESTED (no crowding hand yet).

## S95 -- vocabulary-contract diagnosis; architecture sharpened; NO source commits (report-only scans)
FINDINGS:
- Ontology captures hard facts: ~2 real gaps (hand-Type attribute missing; H_023 "any mount" wildcard) + 5 naming-drift. Fabrication guarantee is BOOK-WIDE via a binary partition: a rule either names a landmark (gate checks it) or doesn't (nothing to fabricate). 38% are landmark-free free-pass -- expected, safe.
- Vocab reachability scan: 33/47 reachable; 14/47 (30%) NAMING-MISMATCH (rule triggers on a word the pipeline never emits = silent miss, invisible to any fabrication guard); 2/47 INTERPRETED-TERM (H_010a/b "stronger").
- H_010a precedence miss was NOT LLM fabrication -- it was vocabulary mismatch. C2 probe: feed the rule's own word ("stronger_line":"head") and H_010a fires 1/1. The LLM was never broken.
- ARCHITECTURE SHARPEN: split gate survivors -- FULLY-HARD rules (all conditions code-computable) fire deterministically from the gate; only rules with a soft/quality component reach the LLM. H_010a died because it was re-judged by the LLM instead of fired by the gate.
GENERAL LEARNINGS (transfer to astrology):
1. Input vocab and rule vocab are ONE contract -- a rule fires only if its exact trigger word is emitted by the pipeline; mismatch = silent miss invisible to correctness checks. Make trigger-token reachability a mechanical CI gate per domain.
2. Separate NAMING-MISMATCH (align the words) from COMPUTED-TERM (compute and feed; never make the LLM infer). They look identical, fix differently.
3. Never ask the LLM to bridge two representations (deep->stronger). Compute the interpreted term deterministically.
4. A "fabrication" symptom is usually a vocabulary problem in disguise -- check words match BEFORE building gates/guards; per-case bridges (_origin_target) don't scale to thousands of rules.
QUARANTINE (needs_remodel, gate skips, re-model each as own task): H_013 (star on Jupiter), H_024 (branch-toward Luna), H_023 (any-mount wildcard), H_018/019/020 (hand Type attr), HL_002 (finger-of-Jupiter), HL_015 (faded).
BACKLOG (ordered): A vocab alignment (14 naming + 2 interpreted); B extract select->agent/interpretive/palm_select.py + split hard-fire/soft-LLM; C author eval answer key + score 3 hands; D re-model 6 quarantined; E vision layer (untested, real risk).
CARRY: eval answer key unauthored; vision untested.
