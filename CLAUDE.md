# CLAUDE.md
<!-- TOKEN BUDGET: Keep this file under 80 lines. No session logs, no completed module designs, no book registries here. Those live in separate files loaded on demand. Before adding anything, ask: does Claude need this every single query? If not, it belongs elsewhere. -->

## Project
Astrologer AI Agent with RAG — Vedic astrology + palmistry PDFs → OCR → embed → ChromaDB → LLM Q&A agent.

## Current Session Focus
**Session 56: P6 Jaimini (Arudha/Padas) per Master Build Plan order, OR the P7 convergence step if design chat overrides with justification.**
<!-- UPDATE THIS every session. One line only. -->

## Locked Decisions
- **Tiebreaker principle** (memory #10) — when classical sources are genuinely fragmented, user-perceived correctness wins over single-source purity; applies to all contested decisions.
- **V1 scope** — LLM-generated interpretive Q&A is OUT; AstroSage paragraph + palm are the interpretive surface; deterministic calculation-engine output is V1's only structured Q&A surface.
- **P2 order** (locked) — Gochara → Sade Sati → Muhurta engine → Ashtakoot/Mangal dosha → Shadbala → D7 → D10 (demoted); P3+ deferred.
- **Ephemeris consolidation** (Session 44 flagged, Session 52 CLOSED) — `helpers/ephemeris.py` (`sidereal_longitude`/`sidereal_position`/`EphemerisError`) is canonical for sidereal-standard `swe.calc_ut()` calls; attribute-style `swe` access (`import swisseph as swe`, never `from swisseph import calc_ut`) is a hard constraint — several tests monkeypatch the shared `swisseph` module object and rely on late attribute lookup. 11/13 originally-catalogued files fully migrated; 3 call sites stay direct-by-design (not debt): chesta_bala.py's `swe.ECL_NUT` call (not a planet id, outside the helper's contract), kala_bala.py's Ayana Bala loop (flags are actually sidereal-standard, but it feeds the Session 47 oracle-locked Kranti formula — too fragile to touch), and kala_bala.py's Yuddha-Bala loop (needs ecliptic latitude, unexposed by the helper — this gap does NOT justify extending the helper's API). combustion.py deliberately re-wraps `EphemerisError` as its own `RuntimeError` to preserve the planet NAME in the message (Layer C test asserts `match="Sun"`) — do not normalize this to bare unwrapped propagation.
- **Router refuse-heavy posture** (Session 44 lock) — calc_router.py requires >=2 keyword hits to route any domain (0.4 floor, 0.15 margin). Single-keyword questions are REFUSED BY DESIGN. Dogfood-observed misses ("career potential" → 1 hit, refused; "Are we compatible?" → tie, refused) are scorecard data for future `_STEM_MAP` tuning, not bugs. Tune only with Answer Scorecard evidence, not preemptive guesses.
- **Dasha tier = payload property** (Session 49) — current_dasha always TIER_2_RANGE in V1; boundary window selects reason wording only. Tier attaches to answer claims, not evaluation moment.
- **Hybrid router** (Session 50) — Stage 2 LLM classification fires only on Stage-1 confidence-floor/margin refusals; routes only on high; fails closed; built-module fastpath bypasses both stages for flagship deterministic domains.
- **Golden harness STAGE2_VARIABLE tag** (Session 50) — rows tagged STAGE2_VARIABLE carry expected cross-run variance; check calc_router_stage2.log before treating a flip as regression.

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
10. **DIAGNOSTIC OUTPUT ROUTING** (Session 49) — full diagnostic output goes to `diagnostics/latest_run.md` and is committed to git; chat gets a ≤10-line summary with test counts only.
11. **SMOKE-TEST SCOPE HONESTY** (Session 55) — an in-memory smoke test that verifies builder logic directly can mask a pending wiring step (e.g. a module-level whitelist gate never widened); if a feature needs a real end-to-end call to be reachable, verify with one before calling a branch done.
12. **BASELINE FILES ARE ORACLE DATA** (Session 55) — a baseline filename named in a prompt is a claim, not a fact; verify it's still the most recent matching file before diffing against it.

## Varshaphal House-Counting Convention (Session 18)
`resolve_house_counting_lagna()` is the canonical house-counting reference for any Varshaphal-derived bhav calculation (prefers AstroSage parsed Lagna, year-matched; else computed + boundary flag); call it rather than reading Lagna directly off `varshaphal_data`.

## Calculation Architecture (Session 19+)
Every new calculation module lives in its `calculations/` subpackage; never add calculation logic to a top-level file.

**Package structure:** `core/` (chart_d1, panchanga, aspects, dignity) · `vargas/` (D2-D60, vimshopaka) · `strength/` (shadbala, ishta_kashta, bhava_bala) · `dashas/` (vimshottari, yogini, chara, ashtottari, mudda) · `yogas/` (detector + catalog/) · `transits/` (gochara, sade_sati, chandrabala, transit_aspects) · `ashtakavarga/` (single module: compute_bav + compute_sav; bav.py/sav.py stubs superseded and removed, Session 54) · `jaimini/` (karakas, arudha, padas) · `annual/` (varshaphal, muntha, sahams) · `helpers/` (house_counting, ephemeris)
**Canonical helpers:** `resolve_house_counting_lagna()` (`helpers/house_counting.py`) — canonical for ANY Varshaphal-derived bhav calc; `helpers/ephemeris.py` (`sidereal_longitude`/`sidereal_position`/`EphemerisError`, Session 52) — canonical for sidereal-standard `swe.calc_ut()` calls; see Locked Decisions for the 3 direct-by-design exceptions.
**Validation protocol** (per module, on top of Working Style #2/#3): empirical validation across 4 reference charts before locking a formula; zero free parameters (test alternative hypotheses, rule them out); AstroSage parity where applicable, JHora oracle where not; document irreducible cross-software noise as discovered.

## Reference Materials
**Calculation specifications:** `project_files/classical_references/PVR_Vedic_Astrology_Integrated_Approach.pdf` — primary reference for P1-P6; PVR authored both this book and JHora (book = formulas/justification, JHora = numerical ground truth); both consulted before implementing any new calculation module.
**Validation oracles:** AstroSage PDFs (4 reference charts) for secondary parity; JHora exports as primary parity where AstroSage doesn't expose the calculation. Sheridan (1984-05-27 08:00, Durban SA) and David (1976-01-19 22:00, London UK) are fully activated — birth data extracted from their AstroSage PDFs; geocoded in `tests/fixtures/geocoded_locations.json`.
**Interpretive RAG (separate, do not pollute):** ChromaDB ~7,281 chunks across 14 classical texts, for Tier 4 interpretive answers in Parashara's voice. Modern textbooks (incl. PVR's) are deliberately excluded from RAG to preserve classical voice and avoid single-author bias.
## Known Source Divergences — locked V1 (affects every Shadbala/Bhava Bala query)
- **Shadbala Drik Bala** — REAL since Session 46. 28/28 JHora v8 parity (4 charts, ±0.5 Virupa). Formula: BPHS Ch.28 Sphuta Drishti kernel + B.V. Raman Art.109-120 aggregation (Pinda/4) + smooth-taper corrections at 3 BPHS segment boundaries (documented in drik_bala.py docstring). Moon classification: benefic when 90<=elongation<270 (Ashtami-to-Ashtami), NOT paksha; Mercury: same-rasi association count, Moon included. OPEN: Mars 180-210 plateau (S=60) continuity-derived, zero data coverage across all 4 charts — revisit trigger: any chart with a Mars aspect landing in that arc. AstroSage parity NOT expected on this component (JHora-vs-AstroSage genuine divergence, e.g. Sulabh Saturn 17.46 vs 10.89); JHora primary.
- **Bhava Drishti Bala** — REAL since Session 53. Kernel = raw PyJHora `__bhava_drik_bala_calc_1` piecewise with ADD-ON specials (Saturn/Mars/Jupiter) — intentionally DIFFERENT from drik_bala.py's smooth-taper graha kernel; both independently oracle-validated; do NOT unify them. Quarter rule (all planets ×0.25 except Mercury/Jupiter, which get full value), signed sum (no /4), no drishti-house gating, Sripati/Porphyry Bhava Madhya, classification reuses drik_bala.py's dynamic Session 46 rules (a fixed benefic list was empirically ruled out — Sulabh/David Mercury flips malefic). PyJHora's own aggregation NOT ported (row/col indexing bug + fixed benefic list). Oracle = AstroSage BhavBala table, 48/48 houses ±0.5 (measured max 0.15); JHora bhava-level parity unchecked. combustion.py-style exception re-wrap does NOT apply here (bhava_bala.py has no local EphemerisError to preserve).
- **Chesta Bala cross-chart divergence** — Sheridan/David show wider kala_total/chesta spread than Surbhi's documented divergence (same elongation-formula root cause); AstroSage parity tests scoped to Sulabh+Surbhi only. Fix: revisit only if a future phase needs Sheridan/David precision.
- **Planet key casing** — shadbala_totals.py keys are lowercase (`"sun"`); bhava_bala.py/SIGN_LORDS use Title-case (`"Sun"`). `chart_profile.py`'s `shadbala_titlecase` bridge is the single conversion point — do not add ad-hoc `.capitalize()` calls elsewhere.
- **Kala Bala Sun cross-chart (Surbhi)** — `uncertainty_virupa` general = 2.0 (AstroSage-parity basis), vs. Surbhi's ±59 Virupa override (Jupiter/Saturn Abda/Masa divergence) — unchanged, chart-specific, takes precedence. Full detail archived in SESSION_LOG.md.
- **Pancha Mahapurusha real-chart validation** — 3/4 charts unvalidated (SESSION_LOG Session 40).
- **Combustion orbs** (Session 51) — PVR book SILENT (p.114 qualitative only, no degrees, no retro rule) — spec falls to Surya Siddhanta convention (Mo12/Ma17/Me14[12R]/Ju11/Ve10[8R]/Sa15). PyJHora const.py:608-609 diverges (Ju/Ve swapped: 10/11; non-classical retro Ma8/Sa16) — we follow classical; outcome-sensitive only 10-11deg from Sun. AstroSage exposes NO combustion surface: Deeptadi avastha is dignity-only, never assigns Vikala (verified Surbhi p.23, Mercury=Muditha at 3.6deg). Oracle = hand-falsified arithmetic on AstroSage p.3 longitudes. No deep/casual sub-threshold in V1 (no classical source quantifies one).
Ayana Bala Kranti (RESOLVED Session 47), Sun Ayana Bala doubling (RESOLVED Session 47), and Bhava Dig Bala (resolved Session 42, 48/48 exact match) — full validation detail archived to SESSION_LOG.md's compression section. Older/narrower divergences (Saptavargaja scoring, Drekkana Bala, Ayana Bala Moon/Venus edge case, PDF-tooling gap, Sequencing lock violation) also archived there.

## Carry-Forward / Open Items
- **Rahu/Ketu unknown-planet message** (Session 54) — `av_transit_scorer.py`'s generic "unknown transit_planet" ValueError needs its own design-reason text for Rahu/Ketu specifically (currently folded into the generic unknown-planet path); ride-along with the next file touch, not a standalone prompt.
- **RouteResult route marker** (Session 55) — `calc_router.py`'s `RouteResult` carries no field identifying which path (Stage 1 / Stage 2 / fastpath) resolved a question; `golden_harness.py` currently reconstructs this by fragile question-text/timestamp correlation against `calc_router_stage2.log`. Add a router-emitted `route` field next time `calc_router.py` is touched, and switch the harness to read it directly.
- **`_VALID_DOMAINS` sync discipline** (Session 55) — `chart_profile.py` and `orchestrator.py` each carry their OWN independent domain whitelist (neither imports the other's); `chart_profile.py`'s copy was missed for a full session after av_transit shipped elsewhere. Add `SENSITIVE_TO`-style cross-reference comments on both constants at the next touch of either.
- **`golden_harness.py` stale `_KNOWN_GAPS` prose** (Session 55) — 5 entries' "Session 50 observed mechanism" text describes pre-Session-55 routing behavior (now superseded by the `route`-field split, MATCH vs MATCH_STAGE2); refresh opportunistically, not a standalone prompt.
