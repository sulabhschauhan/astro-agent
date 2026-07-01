# CLAUDE.md
<!-- TOKEN BUDGET: Keep this file under 80 lines. No session logs, no completed module designs, no book registries here. Those live in separate files loaded on demand. Before adding anything, ask: does Claude need this every single query? If not, it belongs elsewhere. -->

## Project
Astrologer AI Agent with RAG — Vedic astrology + palmistry PDFs → OCR → embed → ChromaDB → LLM Q&A agent.

## Current Session Focus
**Phase 1 CLOSED (Session 42, 2026-07-01): Bhava Bala (Bhavadhipati + Dig Bala real; Drishti Bala deliberately stubbed) + Ishta/Kashta. 1664 passed, 3 skipped, 3 xfailed. Next: thin-slice answer pipeline checkpoint per Session 31 key decisions — not superseded by this session.**
<!-- UPDATE THIS every session. One line only. -->

## Locked Decisions
- **Hand-laterality via vision LLM** — evaluated Sessions 15-16 under 3 framings; consistently unreliable (worst case 5/6 right-bias on unlabeled images). Permanent: human confirmation at upload, no GPT laterality judgment.
- **Tiebreaker principle (memory #10)** — when classical sources are genuinely fragmented, user-perceived correctness wins over single-source purity. Locked via the Rahu/Ketu graha drishti decision (Session 19); applies to all contested P2-P7 decisions, including roadmap sequencing.
- **No Chart dataclass / VargaType enum** (Session 20) — neither exists; Navamsa built as a pure `(jd_ut, asc_lon_sidereal)` function instead. Revisit only when a varga module genuinely needs shared chart-identity state.
- **Reference-chart fixture template** (Session 20) — one standalone test per chart, not `@pytest.mark.parametrize`, when expected-value structures differ; delete skip-stub parametrize blocks once empty.
- **Transit fixture anchor** (Session 21, PROVISIONAL) — 18:30 UTC (00:00 IST next day); needs second-date corroboration before treating as final.
- **P2 order** (locked Session 20, PAUSED Session 22, UNPAUSED Session 23) — Gochara → Sade Sati → Muhurta engine (Chandrabala instant primitive + range-scan shipped Session 24; Tarabala, Panchaka next — sub-step numbering needs reconciling, see SESSION_LOG) → Ashtakoot/Mangal dosha → Shadbala → D7 → D10 (demoted); P3+ deferred.
- **V1 scope** — LLM-generated interpretive Q&A is OUT (see `diagnostics/path_c_validation_20260621_173724.md`, Session 23 close 2026-06-21). AstroSage paragraph terminal; palm primary; deterministic calculation-engine output is V1's only structured Q&A surface.
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

## Windows Paths (hardcoded)
- Tesseract: `C:\Program Files\Tesseract-OCR\tesseract.exe`
- Poppler: `C:\Program Files\poppler-26.02.0\Library\bin`

## Module Order
```
pdf_processor → image_extractor → chunker → translator → embedder → ChromaDB
query_engine + chart_calculator → astrologer → session_manager
```

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

## Reference Files (load only when relevant)
| File | Load when |
|---|---|
| .claude/architect.md | new file, schema, pipeline change |
| .claude/business.md  | new file, user-facing change |
| .claude/critic.md    | new file, any code change |
| .claude/qa.md        | new file, any code change |
| .claude/ui_ux.md     | any frontend or UX change |
| .claude/debate.md    | agents conflict, multiple valid options |

## Working Style (non-negotiable)
1. **REVIEW before PROCEED** — flag at least one issue before approving any edit
2. **SAMPLE before SCALE** — propose sample validation before full dataset runs
3. **HARDEST CASE first** — test on edge cases, not simple ones
4. **THRESHOLD DISCIPLINE** — every numeric threshold needs justification + scope guard + tuning note
5. **AI reviewing AI** — flag when output has no human review; never chain AI decisions without human checkpoint
6. **SURGICAL EDITS** — no full file rewrites; Python 3.11; always `try/except` with meaningful errors
7. **AGENT INVOCATION** — auto-invoke all 6 before any design/code decision. Surface conflicts only. New agents need explicit approval.
8. **LAYER FIRST** — before any fix, state which layer owns the problem: Data, Retrieval, Prompt, or UI. A fix in the wrong layer creates narrow patches and technical debt.
9. **NO ANCHORED JUDGMENT** — never give an LLM call both a stated expectation and a request to judge against it in the same call. LLM observes independently; Python compares the observation to the expectation deterministically.

## Varshaphal House-Counting Convention (Session 18)
`resolve_house_counting_lagna()` is the canonical house-counting reference for any Varshaphal-derived bhav calculation (prefers AstroSage parsed Lagna, year-matched; else computed + boundary flag); call it rather than reading Lagna directly off `varshaphal_data`.

## Calculation Architecture (Session 19+)
Every new calculation module lives in its `calculations/` subpackage; never add calculation logic to a top-level file.

**Package structure:** `core/` (chart_d1, panchanga, aspects, dignity) · `vargas/` (D2-D60, vimshopaka) · `strength/` (shadbala, ishta_kashta, bhava_bala) · `dashas/` (vimshottari, yogini, chara, ashtottari, mudda) · `yogas/` (detector + catalog/) · `transits/` (gochara, sade_sati, chandrabala, transit_aspects) · `ashtakavarga/` (bav, sav) · `jaimini/` (karakas, arudha, padas) · `annual/` (varshaphal, muntha, sahams) · `helpers/` (house_counting, ephemeris)
**Canonical helpers:** `resolve_house_counting_lagna()` (`helpers/house_counting.py`) — canonical for ANY Varshaphal-derived bhav calc; `helpers/ephemeris.py` — planned pyswisseph wrapper, currently a stub (interim: direct `swe.calc_ut` + a `# TODO` marker per call site).
**Validation protocol** (per module, on top of Working Style #2/#3): empirical validation across 4 reference charts before locking a formula; zero free parameters (test alternative hypotheses, rule them out); AstroSage parity where applicable, JHora oracle where not; document irreducible cross-software noise as discovered.

## Reference Materials
**Calculation specifications:** `project_files/classical_references/PVR_Vedic_Astrology_Integrated_Approach.pdf` — primary reference for P1-P6; PVR authored both this book and JHora (book = formulas/justification, JHora = numerical ground truth); both consulted before implementing any new calculation module.
**Validation oracles:** AstroSage PDFs (4 reference charts) for secondary parity; JHora exports as primary parity where AstroSage doesn't expose the calculation. Sheridan (1984-05-27 08:00, Durban SA) and David (1976-01-19 22:00, London UK) are fully activated — birth data extracted from their AstroSage PDFs; geocoded in `tests/fixtures/geocoded_locations.json`.
**Interpretive RAG (separate, do not pollute):** ChromaDB ~7,281 chunks across 14 classical texts, for Tier 4 interpretive answers in Parashara's voice. Modern textbooks (incl. PVR's) are deliberately excluded from RAG to preserve classical voice and avoid single-author bias.

## Known Source Divergences — locked V1

### Shadbala Saptavargaja Bala scoring
- **Spec source:** BPHS 27.2-4 literal (Mooltrikona=45, Own=30, Pramudita=20, Shanta=15, Din=10, Duhkhita=4, Khala=2)
- **AstroSage delta:** AstroSage uses an unpublished scoring table that produces totals 10-30 Virupa higher per planet. Reverse-engineering from public data is not reliably possible — Sun fits Adhimitra=30/Sama=7.5 but Moon does not fit the same table.
- **User impact:** Near-zero in V1. Shadbala feeds Yoga detection (P3) and Trigger Naming (P7), both of which consume RANKING, not absolute values. Ranking is stable across BPHS vs AstroSage scoring tables for the dominant components (Sthana base + Kala + Chesta).
- **Revisit trigger:** Phase A user testing surfacing a ranking complaint that traces to Saptavargaja precision.

### Shadbala Drekkana Bala
- **Spec source:** AstroSage + JHora convergence on 1 Virupa flat constant for all planets (three-tier hierarchy rule).
- **BPHS divergence:** BPHS 27.6 specifies 15/0 binary by gender×decanate. Locked at 1 Virupa per AstroSage parity.

### Ayana Bala — Moon/Venus high-declination edge case (V1 accepted gap)
- **Spec source:** PyJHora `(24.0 + adj_decl) * 1.25` formula.
- **Validation oracle:** AstroSage Kundli PDFs (4 charts).
- **Pass tolerance:** ±2.0 Virupa for 5/7 planets; ±6.0 Virupa for Moon and Venus.
- **Delta magnitude:** Moon and Venus at near-maximum declination (≈23.8°) compute to ~59.7 and ~59.9 respectively; AstroSage shows 54.45 and 56.21. Other 5 planets (Sun, Mars, Mercury, Jupiter, Saturn) match within ±2.
- **User impact:** Moon Shadbala total delta ~1.1% (5.27 of 483.91). Negligible for Shadbala threshold checks (min_required=6.0 Rupa, computed ~8.07, delta does not change strong/weak classification).
- **Revisit trigger:** If user testing surfaces complaints about Moon/Venus Shadbala values being off, investigate AstroSage's exact Ayana algorithm by reverse-engineering against a chart with Moon/Venus at moderate declination (≈10°) where the formula deltas should be smaller.
- **Root cause hypothesis (not yet confirmed):** AstroSage may use a different obliquity constant or apply a soft cap below 60 Virupa for high-declination cases. PyJHora's calibrated constant (24.0) matches Sun within 0.30 but diverges for outer planets at extreme declination.

### Shadbala Drik Bala (V1 stub)
- **Spec source:** BPHS 27.26. PyJHora `__drik_bala_calc_1` kernel ported and tested as primary implementation path.
- **AstroSage/JHora delta:** Port matched AstroSage within ±5 Virupa for Surbhi (7/7 planets) but diverged on Sulabh Moon (+16.4) and Venus (+7.7), despite AstroSage and JHora agreeing closely with each other on those exact two values. Root cause unresolved after two kernel variants and two Moon benefic/malefic classification approaches tested across sessions 36-37.
- **Resolution:** Stubbed at 0.0 for all planets in V1. shadbala_totals.py (P2.5.7) exposes this via a mandatory `drik_is_stubbed: bool` and `caveat: str` field on every planet's output — not optional, not silent.
- **User impact:** Shadbala totals understated by the true Drik Bala magnitude per planet (AstroSage fixture range observed: -20.44 to +22.15 Virupa). Ratio (Rupas/minimum) may read "above minimum" when the true ratio is below. Rank order usually preserved but not guaranteed within ~20 Virupa.
- **Revisit trigger:** New source material only — AstroSage's published Drik Bala formula (not currently public) or the untested PyJHora `__drik_bala_calc_1_pvr` kernel variant. DO NOT re-attempt by fitting parameters against fixture output (rejected pattern, see session 36-37 history) — only fresh hypothesis testing.
- **Update (Session 42):** `__drik_bala_calc_1_pvr` has now been located and verbatim-extracted (`PyJHora-main/src/jhora/horoscope/chart/strength.py`, cited "per BPHS Chapter 26" in its own docstring) using this session's fingerprint-first, verbatim-extraction-only investigation method — see the Bhava Dig Bala entry above and SESSION_LOG.md Session 42. The revisit trigger above is satisfied in principle. Deliberately NOT actioned this session, per the Session 31 sequencing lock (Phase 1 scope only, this session). Next candidate for a scoped Phase 1-adjacent exception, same justification class as Bhava Dig Bala.

### Shadbala Kala Bala — Sun cross-chart Abda/Masa divergence
- **Spec source:** BPHS 27.7-13 (Abda/Masa/Vara/Hora Bala — calendar-lord assignment by solar month/day ingress).
- **AstroSage delta:** Sulabh Sun kala_total validated within ±2 Virupa, but Surbhi chart showed Jupiter +31 and Saturn -59 Virupa divergence, traced to Abda=15/Masa=0 vs computed Abda=0/Masa=0 — a solar-month ingress date disagreement between BPHS calendar-lord assignment and AstroSage's algorithm. Surfaced during P2.5.7 totals testing (test_shadbala_totals.py Layer B); kala_bala.py itself was never tested against Surbhi at this granularity.
- **User impact:** Limited to Sun kala_total cross-chart comparisons; does not affect Sulabh (the primary validated chart) or other planets.
- **Revisit trigger:** If P3 Yoga detection or P7 trigger-naming surfaces a ranking anomaly traceable to Sun kala_total on a non-Sulabh chart. Not re-opened proactively — within the 2-diagnostic-attempt budget, this is deprioritized behind Drik Bala and P3.

### Pancha Mahapurusha real-chart validation (Session 40)
- **Sulabh zero-yoga result:** Confirmed against `tests/fixtures/jhora_sulabh.md` independent JHora yoga table — no Ruchaka/Bhadra/Hamsa/Malavya/Shasha listed there.
- **Surbhi (Shasha/Saturn/house4), Sheridan (Malavya/Venus/house1), David (Hamsa/Jupiter/house7):** NOT independently cross-validated. No JHora yoga-tab screenshot or AstroSage "Yogas in your horoscope" section is captured in project fixtures for these three charts. Results were derived from `kendra_bala=60` + `ochcha_bala`/`ojayugma_bala` reverse-inference from `shadbala_fixtures.py` and confirmed by the passing test assertions, but no independent oracle cross-check exists yet.
- **Revisit trigger:** When JHora yoga-tab screenshots are captured for Surbhi/Sheridan/David (same process as `jhora_sulabh.md`), re-run the Layer I real-chart tests and add oracle citation comments to `test_pancha_mahapurusha.py` TestRealCharts.

### Sequencing lock violation (Session 40)
- **Deviation:** Session 31's locked decision (Phase 1 Bhava Bala + Ishta/Kashta, then thin-slice pipeline checkpoint, BEFORE Phase 2 vargas, BEFORE Phase 3 yogas per Master Build Plan's own "Why third: need Phases 1-2 complete") was not followed — Session 40 proceeded directly to Phase 3 Pancha Mahapurusha yoga detection with neither Phase 1 nor the Phase 2 checkpoint done.
- **Realized risk:** Low in this specific case (Pancha Mahapurusha depends only on dignity + kendra house, confirmed independent of varga/Bhava Bala data), but the deviation was unflagged and undocumented until caught retroactively.
- **Going forward:** Phase 1 (Bhava Bala + Ishta/Kashta) resumes next, per the original Session 31 lock — no further Phase 3 sessions (Raja/Dhana/Neecha Bhanga/Special yogas) until Phase 1 + the thin-slice pipeline checkpoint are complete, unless a future deviation is explicitly proposed and confirmed in design chat first, not inferred from a session handover summary.

### Bhava Dig Bala — RESOLVED (Session 41 investigation → Session 42 implementation)
- **Spec source:** PyJHora `strength.py::_bhava_dig_bala` — Porphyry/Sripati house cusps (NOT equal-house from Lagna, the Session 41 hypothesis tested and rejected), rasi-animal-group discrete taper `abs(60 - abs(h)*10)` gating each house's own cusp longitude against 4 classical rasi-animal groups (Nara/Jalachara/Chatushpada/Keeta, anchored at houses 1/4/7/10 respectively). A different formula family from the originally-attempted continuous BPHS 27.26-29 degree-arc/3 formula — not a refinement of it.
- **Discovery method (two-stage, template for future stuck investigations — see SESSION_LOG.md Session 42):** (a) formula family identified via OUTPUT FINGERPRINTING before any source code was read — AstroSage's Bhavdig Bala values across all 4 charts are all clean multiples of 10, which ruled out a continuous-arc formula on its face; (b) exact rasi-group longitude boundary constants required a dedicated VERBATIM RE-EXTRACTION prompt after an earlier investigation report paraphrased/summarized the boundary tuples and corrupted a value, producing a false negative on House 1 during validation.
- **Validation:** 48/48 exact match (4 charts × 12 houses: Sulabh, Surbhi, Sheridan, David) against AstroSage's BhavBala Table Bhavdig Bala row. Cusps via new `compute_porphyry_house_cusps()` (`agent/chart_calculator.py`, pyswisseph `hsys=b'O'`) — deliberately a separate cusp system from the whole-sign houses used elsewhere.
- **multi_match_houses — untested by real data:** `compute_bhava_dig_bala` exposes a `multi_match_houses: list[int]` field surfacing an upstream PyJHora quirk (its h-loop spans 14 offsets over a 12-house cycle, double-visiting 2 houses per rasi-group anchor — last-write-wins in PyJHora's own hash-order-dependent aggregation). Algebraically the two candidate values are always equal for any real longitude (verified this session), so the field is currently harmless — but all 4 reference charts returned `[]` empty, so this has never been observed populated. If a 5th chart ever returns a non-empty `multi_match_houses`, treat it as new territory requiring fresh validation — do not assume it's safe purely on the existing algebraic argument.
- **Resolution:** Real implementation. `compute_bhava_dig_bala` in `bhava_bala.py`; `dig_is_stubbed` now always `False`. `compute_bhava_drishti_bala` / `drishti_is_stubbed` unaffected — remains stubbed, see entry below.

### Bhava Drishti Bala (Session 41, not implemented V1, no fresh investigation run)
- **Spec source:** BPHS-derived Drishti Kendra piecewise taper, Vishesha drishti for Mars/Jupiter/Saturn, full-value for Jupiter/Mercury, quarter-value for others, benefic/malefic algebraic signing — structurally the SAME aspect-strength kernel already implemented and stubbed for Drik Bala (`agent/calculations/strength/drik_bala.py`). Bhava Drishti Bala applies it to a Bhava Madhya point as the aspected target instead of a planet's longitude.
- **Rationale for no fresh investigation:** Drik Bala's port of this exact kernel already diverges from AstroSage on Sulabh (Moon +16.4, Venus +7.7 Virupa, despite JHora and AstroSage agreeing with each other on those values — root cause unresolved after two kernel variants). No reason to expect re-deriving the same kernel against a different target point resolves the underlying formula gap.
- **Resolution:** Stubbed at 0.0 V1 without a fresh per-chart investigation — direct extension of the Drik Bala finding, not a new diagnostic attempt. `compute_bhava_drishti_bala` in bhava_bala.py.
- **Revisit trigger:** SAME as Drik Bala — new source material only (AstroSage's published formula, or the untested `__drik_bala_calc_1_pvr` kernel variant). If/when Drik Bala's V1.1 is resolved, re-attempt Bhava Drishti Bala using whatever kernel fix resolves Drik Bala first — same root cause.
- **Update (Session 42):** Same status as the Drik Bala update above — `__drik_bala_calc_1_pvr` is now located and verbatim-extractable via the proven fingerprint → verbatim-extraction → hand-verify → implement method. Revisit trigger satisfied in principle; deliberately not actioned this session per the Session 31 sequencing lock. Should be attempted together with (or immediately after) Drik Bala's V1.1 fix, since both stubs share the exact same underlying kernel.

### PDF-read tooling gap (Session 42)
- **Issue:** The poppler/`pdftoppm` path referenced under "Windows Paths (hardcoded)" (`C:\Program Files\poppler-26.02.0\Library\bin`) is not currently wired up on PATH in the Claude Code environment, despite being hardcoded there — the Read tool's PDF-render path fails with "pdftoppm is not installed" when pointed at a PDF.
- **Impact this session:** Could not directly OCR/read AstroSage PDF chart reports to extract Bhava Dig Bala reference values from source; required a manual chat-transcription relay (user pasted the values from the PDFs directly) instead of direct Claude Code extraction — see `tests/fixtures/bhava_dig_bala_astrosage.py` docstring for the resulting provenance note.
- **Status:** Flagged for a future fix, not blocking. Revisit when a task next needs direct PDF-sourced fixture extraction (e.g. Bhava Drishti Bala's eventual validation).

### Shadbala Chesta Bala — Layer B cross-chart scope (Sheridan/David excluded)
- **Decision:** test_chesta_bala.py Layer B (tight-tolerance AstroSage parity spot-checks) remains scoped to Sulabh + Surbhi only. Sheridan and David are exercised at Layers C/D/E (structural, rank validity, caveat integrity) but not added to Layer B's tight-tolerance assertions.
- **Reason:** Investigated once (diagnostic attempt #1, within the 2-attempt budget) during the Sheridan/David activation session (Session 39). Sheridan shows wider kala_total/chesta cross-chart spread than Surbhi's already-documented divergence — same elongation-formula root cause, larger magnitude on these charts. Not re-investigated further per session budget; deprioritized behind P3.
- **Revisit trigger:** Only if a future phase (P3 yoga potency, P7 trigger naming) specifically needs Sheridan/David chesta_bala precision. Not proactively revisited.

### Ishta/Kashta Phala — Sun Ayana Bala doubling range violation (Session 41)
- **Root cause:** kala_bala.py's `_ayana_bala()` applies the Sun `*2.0` special-case with no upper clamp (line ~370-372), producing values up to ~118 Virupa instead of the documented 0-60 Virupa range. This propagates unchanged through chesta_bala.py's Sun path (which passes `ayana_result['Sun']` directly as Sun's Chesta Bala with no clamp) and into `compute_ishta_kashta()`'s sqrt inputs, causing `sqrt((60-uchcha)*(60-chesta))` to receive a negative second factor for 3 of 4 reference charts (Sulabh Sun chesta=75.93, Surbhi Sun chesta=71.17, Sheridan Sun chesta=113.33; David Sun chesta=9.08 is below 60 due to near-zero solar declination at that chart's birth date).
- **Not a wiring bug:** confirmed both call paths (via shadbala_totals.py and via ishta_kashta.py) produce byte-identical chesta values, ruling out the wiring hypothesis (diagnostic attempt #1, Session 41).
- **Pre-existing and silent** before ishta_kashta.py surfaced it: TestA3Range in test_chesta_bala.py only asserts the 0-60 invariant on a synthetic ayana_val=30.0 fixture, not on real ephemeris output.
- **V1 resolution:** `max(0, ...)` guard in `compute_ishta_kashta` prevents a sqrt of negative, capping Kashta Phala to 0.0 when chesta > 60. ishta_kashta.py test Layer A marks the 3 affected Sun cases as xfail with explicit reason.
- **NOT fixed in kala_bala.py in V1:** capping `_ayana_bala` at 60 would break existing AstroSage-parity tests that already accept and validate Sun Ayana values over 60 (e.g. Sheridan AstroSage fixture = 114.14, currently green).
- **V1.1 fix path:** requires a deliberate cross-module scoping decision — does the cap belong in `_ayana_bala` itself, in chesta_bala's Sun path only, or in a dedicated Ishta/Kashta pre-processing step? Also requires re-checking whether AstroSage and JHora agree on capped vs uncapped for Sun Ishta/Kashta specifically (they may use a different Chesta source for Sun in this context than they use for the Shadbala total). DO NOT attempt V1.1 fix without that cross-oracle check first.
- **Revisit trigger:** This is diagnostic attempt #1 of the 2-attempt budget for this issue.
