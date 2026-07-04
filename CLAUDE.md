# CLAUDE.md
<!-- TOKEN BUDGET: Keep this file under 80 lines. No session logs, no completed module designs, no book registries here. Those live in separate files loaded on demand. Before adding anything, ask: does Claude need this every single query? If not, it belongs elsewhere. -->

## Project
Astrologer AI Agent with RAG — Vedic astrology + palmistry PDFs → OCR → embed → ChromaDB → LLM Q&A agent.

## Current Session Focus
**Thin-slice answer pipeline CHECKPOINT CLOSED (Session 45, 2026-07-03): orchestrator.py wires router→profile→formatter→merge. 16 e2e tests (4 career + 4 dasha + 1 marriage + 5 refusal + 2 error). Dasha conditional demotion bug fixed. 1766 passed, 3 skipped, 3 xfailed. Next: POST-CHECKPOINT PHASE ORDER per Master Build Plan (Drik extraction → ephemeris consolidation → timing block).**
<!-- UPDATE THIS every session. One line only. -->

## Locked Decisions
- **Tiebreaker principle** (memory #10) — when classical sources are genuinely fragmented, user-perceived correctness wins over single-source purity; applies to all contested decisions.
- **V1 scope** — LLM-generated interpretive Q&A is OUT; AstroSage paragraph + palm are the interpretive surface; deterministic calculation-engine output is V1's only structured Q&A surface.
- **P2 order** (locked) — Gochara → Sade Sati → Muhurta engine → Ashtakoot/Mangal dosha → Shadbala → D7 → D10 (demoted); P3+ deferred.
- **Ephemeris consolidation debt** (Session 44 flag) — 12 independent `swe.calc_ut()` call sites across chesta_bala, kala_bala, dig_bala, sthana_bala, panchaka, tarabala, chandrabala, sade_sati, gochara, navamsa, panchanga, chart_profile bridge. Extract to `helpers/ephemeris.py` per existing TODO markers. Mechanical, bounded, no investigation risk. Scheduled as post-checkpoint item (b) in Master Build Plan.
- **Router refuse-heavy posture** (Session 44 lock) — calc_router.py requires >=2 keyword hits to route any domain (0.4 floor, 0.15 margin). Single-keyword questions are REFUSED BY DESIGN. Dogfood-observed misses ("career potential" → 1 hit, refused; "Are we compatible?" → tie, refused) are scorecard data for future `_STEM_MAP` tuning, not bugs. Tune only with Answer Scorecard evidence, not preemptive guesses.

Older superseded/shipped-feature decisions (Sessions 15-25) archived to SESSION_LOG.md's compression section — not needed per-query once a module ships and its convention lives in the code/tests themselves.

## Windows Paths (hardcoded)
- Tesseract: `C:\Program Files\Tesseract-OCR\tesseract.exe`
- Poppler: `C:\Program Files\poppler-26.02.0\Library\bin`

## Module Order
```
pdf_processor → image_extractor → chunker → translator → embedder → ChromaDB
query_engine + chart_calculator → astrologer → session_manager
```

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

## Known Source Divergences — locked V1 (affects every Shadbala/Bhava Bala query)
- **Shadbala Drik Bala** — REAL since Session 46. 28/28 JHora v8 parity (4 charts, ±0.5 Virupa). Formula: BPHS Ch.28 Sphuta Drishti kernel + B.V. Raman Art.109-120 aggregation (Pinda/4) + smooth-taper corrections at 3 BPHS segment boundaries (documented in drik_bala.py docstring). Moon classification: benefic when 90<=elongation<270 (Ashtami-to-Ashtami), NOT paksha; Mercury: same-rasi association count, Moon included. OPEN: Mars 180-210 plateau (S=60) continuity-derived, zero data coverage across all 4 charts — revisit trigger: any chart with a Mars aspect landing in that arc. AstroSage parity NOT expected on this component (JHora-vs-AstroSage genuine divergence, e.g. Sulabh Saturn 17.46 vs 10.89); JHora primary.
- **Bhava Drishti Bala** — stubbed at 0.0 V1 (same formula family as Drik Bala, applied to Bhava Madhya instead of planet longitude; Drik Bala's own stub is now resolved — see above). Fix: port the resolved Drik Bala kernel to Bhava Madhya inputs.
- **Ayana Bala Kranti** — RESOLVED Session 47. Root cause: true equatorial declination (latitude-contaminated) instead of Sayana-longitude Kranti. Fix: kranti = asin(sin(24°) × sin(sayana_lon)), fixed 24° obliquity per Raman Art. 72-73. Validated ±0.45 vs AstroSage, 28/28 cells, 4 charts. Test tolerance single-tier 0.75 (was 6.0/2.0). david-sun ishta JHora-oracle split resolved per tiebreaker principle, `_A_TOL` sun=1.75.
- **Sun Ayana Bala doubling** — OPEN. `_ayana_bala()`'s Sun `*2.0` doubling is now oracle-validated 4/4 vs AstroSage Ayana column; remaining issue is the doubled value flowing into Chesta Bala (BPHS 27.18) — AstroSage fixture shows Sun Chesta ≈ Ayana/2. Undoubled-into-Chesta is the V1.1 candidate fix; investigate on the post-K24 baseline. 3 Ishta/Kashta Sun xfails unchanged.
- **Chesta Bala cross-chart divergence** — Sheridan/David show wider kala_total/chesta spread than Surbhi's documented divergence (same elongation-formula root cause); AstroSage parity tests scoped to Sulabh+Surbhi only. Fix: revisit only if a future phase needs Sheridan/David precision.
- **Planet key casing** — shadbala_totals.py keys are lowercase (`"sun"`); bhava_bala.py/SIGN_LORDS use Title-case (`"Sun"`). `chart_profile.py`'s `shadbala_titlecase` bridge is the single conversion point — do not add ad-hoc `.capitalize()` calls elsewhere.
- **Kala Bala Sun cross-chart (Surbhi)** — ±59 Virupa uncertainty envelope (Jupiter/Saturn Abda/Masa divergence), vs. the general ±6 Virupa Ayana Bala envelope used for other charts (Surbhi's 59.0 is unchanged, chart-specific, and takes precedence). Full detail archived in SESSION_LOG.md.
- **Pancha Mahapurusha real-chart validation** — 3/4 charts unvalidated — see SESSION_LOG Session 40.
- **Bhava Dig Bala** — resolved Session 42, 48/48 exact match. Methodology archived in SESSION_LOG.

Older/narrower divergences (Saptavargaja scoring, Drekkana Bala, Ayana Bala Moon/Venus edge case, PDF-tooling gap, Sequencing lock violation) archived to SESSION_LOG.md's compression section.
