## Session Log

> ARCHIVES: Sessions 19-66 -> `SESSION_LOG_ARCHIVE_S19-S66.md` (split at S81); Sessions 67-104 -> `SESSION_LOG_ARCHIVE_S67-S104.md` (split at S105); Sessions 105-145 -> `SESSION_LOG_ARCHIVE_S105-S145.md` (split at S146, S151); Sessions 146-160 -> `SESSION_LOG_ARCHIVE_S146-S160.md` (split at S169). This live file holds head-matter + S161 onward.

## S170 (2026-11-22) -- PRATYANTAR CLOSED (suppression stands; the wrong reason corrected)

Pratyantar "discussion" roadmap item resolved to CLOSE -- no build. RESEARCH (session logs + legitimate external sources, no assumption): the long-standing "+/-37-day drift, wrong lord" rationale is a day-one architecture-layer precaution that `KNOWN_DIVERGENCES` D2 itself records as "not investigated at implementation depth." It is WRONG on the facts -- the only measured dasha drift is Gap D1 (0.3-2.8d across the 4 reference charts, S76; NON-compounding, "ratio math preserves durations"), not 37d; and the PD duration formula in `chart_calculator._calc_dasha` (`m_total*ad_total*DASHA_YEARS[pt]/14400`) is algebraically the standard `antardasha_years*pd_planet_years/120` (confirmed vs external worked examples). The math was never the problem. The "+/-37" was always stated only vs AstroSage (Camp X, undocumented Moon correction).

REAL reason PD stays suppressed (now the recorded one): a pratyantar is weeks-to-months long, so its dates are governed by BIRTH-TIME precision, not ephemeris drift -- external practitioner sources quantify ~6-7 weeks of whole-ladder shift per 10 min of birth-time error (ajmerastro, astromitra, shreekundli), longer than many pratyantars. The product supports approximate birth times (`birth_time_confident=False`), which cannot carry PD-level timing; AD + Saturn/Jupiter transits already answer "when" at the granularity the product surfaces, and classical practice (Sanjay Rath / K.N. Rao, per satyori) reads PD AGAINST those same transits. Net: PD = false precision for the approximate-time majority, marginal transit-duplicating value for the minute-precise minority. LOW IMPACT -> CLOSED.

EDITS this session (comments/markdown ONLY, no code logic, no pytest): `agent/chart_calculator.py` DASHA ACCURACY NOTE + 2 inline PD comments rewritten (correct reason + "PRATYANTAR SUPPRESSION -- CLOSED S170, DO NOT REOPEN"); `docs/KNOWN_DIVERGENCES.md` Gap D2 rewritten ("CLOSED S170, DO NOT REOPEN" + reopen criteria); this CLAUDE.md ROADMAP pointer updated. PD is still computed in `_calc_dasha` (`current_pratyantar`/`next_5_pratyantars`) and still not surfaced -- behaviour unchanged, only the recorded rationale.

REOPEN ONLY IF: a first-class confident/rectified birth-time path lands AND there is demonstrated demand for sub-month event timing -- then gate PD on `birth_time_confident=True`, present it with the running transit, and FIRST run the 4-chart JHora PD oracle (the one dasha level that never ran the validation protocol).

NEXT: Lal Kitab go/no-go -- the remaining AstroSage-retirement gate (itself gated on the golden-R5 rewrite + a V1-scope amendment + design-chat consensus). The palm-vision -> DeepSeek V4.1 Flash migration remains the only hard-deadline item (14 Jan 2027).

## S169 (2026-11-22) -- SESSION_LOG re-split + Terra A/B CLOSED + TAJIKA ASPECT YOGAS (Ithasala/Ishrafa) BUILT END-TO-END (engine + real-speed retrograde direction + fact-block wiring + corpus) + sahams found ALREADY DONE

HOUSEKEEPING -- RE-SPLIT: SESSION_LOG crossed 150KB; archived S146-S160 to `SESSION_LOG_ARCHIVE_S146-S160.md` (byte seam at the `## S146` header, bytes 60255..EOF). Live file now ~60KB (head + S161-S168 + this). CLAUDE.md citation-resolution rule + the one hardcoded `SESSION_LOG.md S160` filename re-pointed in the same commit (amended-boundary rule, S121). Non-monotonic naming accepted (S160 archived while S161-S162 stay live -- the file is physically newest-first).

TERRA A/B -- CLOSED on cost (ratified by Sulabh). Reaffirms the S160 luna-on-cost lock; the rate card confirms Terra is 10x in/out, 5x cached. Finding (not re-litigated): the handover framed "10x cost" as a scale argument, but at ~zero production volume the absolute cost is also ~zero -- so the real driver was never revenue, it was the palm-vision deadline. DECISION: no A/B run; luna stays; `scripts/terra_cost_validation.py` harness delta cancelled. PALM VISION: the gpt-4o retirement (14 Jan 2027) still forces a migration; Terra ruled out on cost -> candidate is **DeepSeek V4.1 Flash** (cheaper, Sulabh's pick), decided at END OF DEV. CAVEATS carried: DeepSeek is non-OpenAI (new client/base-URL path, not a model-string swap); "similar performance" is a GENERAL-benchmark claim -- the palm live smoke-test gate must pass on DeepSeek before trust (palm reading is narrow morphology, not general VQA); hard deadline 14 Jan 2027 regardless of when dev finishes. LIVE FINDING #1 orphaned-consequence noted: the S168 Charak carry-forward was gated on "Terra tried on live longevity AND protection still under-weighted" -- Terra is now closed, so trigger (a) can never fire; re-base onto luna-under-weighting if ever pursued.

SAHAMS -- FOUND ALREADY DONE (handover + CLAUDE.md roadmap were STALE). The "11 pending sahams" item is CLOSED: `agent/calculations/annual/sahams.py` has 36 sahams, ALL status=CONFIRMED (the 11 were promoted across S163-S165; `include_pending` is now a dead switch), emitted by `varshaphal_facts`, rendered by `pipeline._fact_block` (loops all, no cap), and oracle-validated in `test_sahams.py` (all 36 x 4 charts, day+night, <0.5deg vs JHora). Nothing to build. Stale text remains in the CLAUDE.md S162 locked decision ("11 QUARANTINED... not wired") -- corrected in the roadmap this session; the S162 lock body left as-is (history).

TAJIKA ASPECT YOGAS (sub-engine D) -- BUILT END-TO-END, the big handover open item. Three steps, each validated:
 1. ENGINE: new `agent/calculations/annual/tajaka_aspects.py` -- Ithasala (applying) / Ishrafa (separating) per classical pair with valence (benefic/malefic/neutral) + type (varthamaana/poorna/bhavishya), plus companion yogas (Kamboola, Nakta, Yamaya, Manahu, Ishkavala, Induvara). FAITHFUL PORT of PyJHora `tajaka.py`/`tajaka_yoga.py` (deeptamsa orbs 15/12/8/7/9/7/9; Tajika sign-aspect 2/3/4/5/7/9/10/11/12). PyJHora is LOOKUP-ONLY (ruled): no runtime dependency, no cross-check that executes it -- validation is 5 HAND-VERIFIED anchors on the 2027 chart (Ithasala needs no JHora oracle: it is deterministic geometry, not a contested formula like the sahams). `test_tajaka_aspects.py` 13 passed.
 2. REAL-SPEED RETROGRADE DIRECTION: applying/separating computed from ACTUAL SIGNED VELOCITY (gap closing=Ithasala, opening=Ishrafa), not a faster/slower rule -- best practice from the Tajika/horary literature (Ernst Wilhelm Tajika Prashna; Tajika Neelakanthi "Khalasara"; Gomes/Saptarishis), researched + agent-reviewed. Subsumes faster-only vs either-planet (no special case); Khalasara (false Ithasala) emerges automatically. Plumbed via new `ephemeris.sidereal_position_true` (true-sidereal longitude + FLG_SPEED, longitude byte-identical) -> `varsha_pravesh` returns `planet_speeds` + `retrograde`. `test_varsha_pravesh.py` +3 (Jupiter-2027 reads retrograde from real speed; oracle longitude tests unchanged -> FLG_SPEED shifted nothing). LIVE-CONFIRMED: Jupiter-Saturn flips Ithasala->Ishrafa under real speed (the retrograde correction working end-to-end).
 3. WIRING + CORPUS: `varshaphal_facts` builds pts+speeds and calls the engine (fail-soft, nested under `varshaphal` -> no FACT_BLOCK_PROVIDES change); `pipeline._fact_block` renders Ithasala/Ishrafa + companions with a plain-language frame. Full suite 870 passed (astro+annual), no regression, direction_provisional absent (real speeds reached the engine). CORPUS: new `data/tajika_aspects_corpus.txt` (8 segments, verbatim-English B.V. Raman Varshaphal Ch.VII §57-63 -- Ithasala/Ishrafa/Ishkavala/Induvara/Khallasara/Radda + general deeptamsa/framework; NO verification gate, already-English) + `scripts/ingest_tajaka_yogas_corpus.py` (mirrors the sahams ingest, life-area-wide tags, FIXES the indent=None minified-JSON bug -> indent=2 per the S166 lock, .bak_S169). Dry-run + apply + idempotency validated in-container (device JSONs pristine; Sulabh runs --apply). DEFERRED (recorded): Kamboola/Nakta/Yamaya/Manahu RESULT-doctrine (Raman §57 only names them; the Nilakanthi passage is Devanagari -> verification gate -> later ingest); Radda QUALITY layer (retrograde/combust spoils an Ithasala -> "final success after much trouble", source-grounded in Raman §63 -- the engine computes direction, not yet the Radda spoil); radda/duhphali/gairi-kamboola/khallasara engine yogas (need dignity+combustion+PV-bala or are unimplemented upstream).

RETROGRADE DOCTRINE (ruling, do not re-litigate): applying/separating = signed relative velocity. A SEPARATE quality layer (Radda) says a retrograde/combust planet ALSO weakens an Ithasala -- deferred, source = Raman §63.

PROCESS NOTE: the sahams ingest script (`scripts/ingest_sahams_corpus.py`) writes `indent=None` (minified) -- a latent regression against the S166 pretty-print lock; the live JSONs are currently pretty (so it was caught/restored before), but a re-run would re-minify. Not fixed this session (out of scope); flagged for a one-line fix when that script is next touched.

## S168 (2026-11-22) -- Longevity extension EVALUATED then DROPPED (three-pairs + eighth-lord + Charak flags) + FOUR items CLOSED (planner validation / palm-temperature / LIVE FINDING #1 / longevity) + palm TEXT path migrated to gpt-6-luna (committed + tested) + palm<->astrology confirmed NOT integrated

DESIGN + RESEARCH + ONE MIGRATION. The longevity answer is UNCHANGED (frozen at S167). One code change shipped: palm TEXT -> gpt-6-luna.

### 1. Longevity range methods -- PROTOTYPED, DROPPED (not deferred)
Prototype `longevity_range_facts.py` built in the DESIGN-CHAT CONTAINER ONLY (NOT in the repo; dies with the session). Source-faithful from the PVR PDF (data/pdfs/Vedic Astrology_ PVR Narashimha Rao.pdf, Ch.14), extracted verbatim, never from memory:
 - Table 32 (Shiva-motion 8th): Ar->Sc Ta->Ge Ge->Cp Cn->Sg Le->Cn Vi->Aq Li->Ta Sc->Sg Sg->Cn Cp->Ge Aq->Cp Pi->Le.
 - Table 33 (modality pair -> category): MM->long, FF->short, DD->middle, movable+fixed->middle, movable+dual->short, fixed+dual->long.
 - §14.4 combine: all-same->that; 2-agree->those dominate; all-differ->prefer pair3 (Lagna/HoraLagna) UNLESS Moon in lagna/7th -> prefer pair2 (Moon/Saturn). Pairs: (1) lagna-lord + special-8th-lord [Table 32], (2) Moon+Saturn, (3) Lagna+HoraLagna.
 - §14.5 eighth-lord method: 8th lord from the stronger of lagna/7th; quadrant->long, panaphara->middle, apoklima->short.
 - Charak (Elements of Vedic Astrology, Balarishta & Arishta-bhanga ch., combined-ed. pp.355-369) structural flags: Moon-in-dusthana Balarishta, kendra/trikona malefic-benefic census, Vargottama lagna/lord, trik & tri-shadaya occupants, Saturn-in-8th exception. Coded as emitted flags ONLY (Option-3, book-as-spec); NO Charak prose in the corpus (modern-author exclusion lock STANDS).
VALIDATION: engine matches PVR's OWN worked examples -- Example 47 -> long, Exercise 23 -> middle; zero free parameters. NOT oracle-validated vs JHora (that would have been the ship gate).
RUN ON SULABH (deterministic, HL via compute_special_lagnas): pair-1 (Jupiter Aries / Moon Scorpio) = Middle; pair-2 (Moon Scorpio / Saturn Sagittarius) = Long -- ALREADY SPLIT, so pair-3 (Lagna Sagittarius dual + Hora Lagna) ALONE decides, and swings the combined across ALL THREE: HL movable->Short, dual->Middle, fixed->Long. Eighth-lord likewise swings Short (ref=lagna, Moon apoklima) <-> Long (ref=7th, Saturn quadrant). The handover's "Short 0-36" is ONE of three equally-valid outputs. THE INSTABILITY IS THE FINDING.
DECISION (ratified by Sulabh):
 - THREE-PAIRS = DROPPED (not deferred): provably unstable on this chart; research consensus that longevity is the least-reliable judgement ("a bracket of several decades is worth very little"); a surfaced band is charter-forbidden; the number-refusal is already doctrinally backed by the S167 caveat; building it costs a JHora 4-chart validation + fact-block growth (feeds LIVE FINDING #2 ceiling) + model-leak risk, for a ~worthless signal.
 - EIGHTH-LORD METHOD = REJECTED: emitting both lagna- and 7th-references = the S132 "ship two results to defer a decision" violation (Validation Source). PVR himself flags it unreliable ("did not work here").
 - CHARAK BOOK = ASSESSED, NOT INGESTED. It DOES fill the S167 Arishtabhanga gap (dedicated Balarishta & Arishta-bhanga chapter + longevity-bands chapter). Modern-author corpus-exclusion lock STANDS. Its structural factors are classical consensus (not Charak-unique) -> if ever used, FLAGS ONLY (Option-3). Charak Ch.XXIII number-methods (Pindayu class) stay excluded by the no-number lock.
 - Longevity FROZEN AT S167 (maraka_facts + maraka_strength + protective_facts, live-confirmed). No regression, no wrong-answer gap -- only a thin spot (no explicit Balarishta/Vargottama flag), whose correct FIRST fix is a MODEL lever (Terra), not code (reaffirms S167: the corpus HAS the protective doctrine; gpt-6-luna under-weights it).
CARRY-FORWARD (single trigger): revisit Charak structural flags ONLY after (a) Terra is tried on a live longevity/health answer AND (b) protection is STILL under-weighted. Then build FLAGS ONLY (Moon-balarishta, kendra/trikona census, Vargottama, tri-shadaya, Saturn-8th), parameters-only, nest under maraka, + pytest. Three-pairs stays dropped. Prototype + extracted PVR tables recorded above so nothing is re-derived.

### 2. Four items CLOSED
 - Planner plan-diff validation (gpt-6-luna) -> CLOSED: verified via good live answers across many questions (the real target is answer quality, not plan-byte-match vs gpt-4o). Residual (silent domain-narrowing on edge cases) is academic while live answers stay comprehensive.
 - Palm temperature reproducibility -> CLOSED (won't-fix): GPT-6 models forbid temperature control and no alternative model offers it -> nothing in hand; accept the variance.
 - LIVE FINDING #1 (a follow-up inherits the prior turn's narrow domains via the S147 conversation-context feed; a cold broad question fans out correctly) -> CLOSED (won't-fix, by design): a planner scope-detector is the patchwork S140/S161 rejected, with its own false-re-broaden failure mode. Escape hatch if it ever bites: a ONE-LINE interpreter nudge ("this covers career -- ask about health/finances/relationships for the rest"), NOT planner logic. [LIVE FINDING #2 -- all-13-domain overflow false-silence -- stays parked.]
 - Longevity extension -> dropped/parked (section 1).

### 3. Palm TEXT path migrated to gpt-6-luna (SHIPPED, committed + tested)
Migrated the 4 palm TEXT modules off gpt-4o/gpt-4o-mini -> gpt-6-luna, matching interpreter._default_llm's shape: drop `temperature` (GPT-6 rejects it), add `reasoning_effort="minimal"` with a TypeError fallback (never crashes on an SDK build that rejects the kwarg). Files: claim_extraction.py (_EXTRACTION_MODEL), claim_voicing.py (_VOICE_MODEL), contact_llm_fallback.py (_FALLBACK_MODEL), palm_reading.py (_READING_MODEL -- vestigial/unused constant, migrated for provenance). New test tests/interpretive/test_palm_gpt6_migration.py (model / reasoning_effort / no-temperature / fallback branch). PYTEST: test_palm_gpt6_migration 8 passed; tests/interpretive 592 passed, 4 skipped; no stale assertions needed updating.
LOOSE ENDS (flagged, not fixed -- surgical diff): _EXTRACTION/_VOICE/_FALLBACK_TEMPERATURE are now dead constants; the probe-locked gpt-4o-mini justification comments are stale.
STILL ON gpt-4o (OUT of scope this session, by Sulabh's decision): palm VISION -- palm_processor.py (3 calls) + cheirognomy/vlm_arm.py. The vision model choice (gpt-6.1-terra vs luna) is DEFERRED to the regular-astrology Terra A/B: if Terra is selected there, move palm vision to Terra too; else to luna. gpt-4o retires 14 JAN 2027 -> the Terra A/B is now the HARD-DEADLINE gate for palm vision. (Luna image-input support unverified -- do NOT blind-swap vision to luna.)

### 4. Palm <-> astrology integration: confirmed NOT built
Traced in frontend/app.py (not memory): answer_question(prompt, chart_facts, chart=, history=, expert=, ...) NEVER receives palm data; generate_palm_reading() NEVER receives the chart. Two parallel independent surfaces. Matches the S65 lock (kundali x palm cross-verification deferred V1.1, gated on a lock-compliant deterministic chart-summary export). A user uploading palms + birth details gets TWO separate readings, not one integrated answer. Fusing them is a real V1.1 build (merging a fidelity artifact with a cited/computed one), not a wiring tweak.

### 5. Agent roster (8)
Architect/Business/UI-UX approved the longevity-prototype shape; QA conditioned on a pytest (delivered for the palm migration); Ephemeris Auditor confirmed HL correctly handles Sulabh's pre-sunrise 00:30 Vedic-day boundary via compute_special_lagnas, flagged meta.local_datetime tz-awareness (self-neutralising -- a naive datetime fail-softs pair-3 to pending, never a wrong HL); Critic + Validation Source rejected the eighth-lord dual-reference; Debate ruled drop eighth-lord + drop three-pairs as a surfaced band.

NOTE: per Sulabh, NO CLAUDE.md Locked-Decision entry for S168 (head-matter weight) -- the drop/park record lives here only. Resurrection risk (a future session re-proposing three-pairs) is accepted against that weight. SESSION_LOG now ~150KB -> at the re-split trigger; next session should re-split per the boundary rule.


## S167 (2026-11-22) -- Longevity-tag flood fix (corpus precision) + LONGEVITY BUILD (maraka-strength + arishta-bhanga/protective + window role-kinds + render), built + tested + live-confirmed; three-pairs + arishta-bhanga ingest deferred to next session

Commits: `be28c0d` (tag flood fix: build_kp_units.py + regenerated domain_tags/chapter_index), `772742e` (longevity build: maraka_facts + protective_facts + static_facts + pipeline + 3 tests), `67ece91` (app.py refresh fix). Not pushed. Suite 5441 passed / 9 skipped / 2 xfailed.

PART A -- LONGEVITY-TAG FLOOD FIX. The shallow longevity answer traced to corpus SELECTION, not the engine. On the committed `domain_tags_bphs.json`: 1694 `longevity`-tagged segments, 93.5% from KP, the single largest contributor `kp_friendship_love_marriage` ("Astrological Secrets of Friendship, Love and Marriage") with 404 longevity segments vs only 64 longevity keyword hits in 530K chars. Root cause: `scripts/build_kp_units.py`'s `HOUSE_TO_DOMAIN` mapped houses {8,12,2,7,3} -> longevity by BARE HOUSE NUMBER, but 2/7 are maraka (dual-signification wealth/marriage), 3 is siblings (8th-from-8th), 12 is loss -- so every marriage/wealth/sibling verse naming those houses got stamped `longevity`. The fix `HOUSE_TO_DOMAIN={8:longevity,6:health}` (2/3/7/12 reach longevity ONLY via the lexical maraka/ayush/mrityu net) was ALREADY AUTHORED (commented "S167", uncommitted since 330662e / S145) but never regenerated, so the committed artifact still carried the old flood. Regenerated (idempotent: strips `kp_` then rebuilds; nila_sahams + BPHS byte-identical; segment_count 5229 unchanged): KP longevity 1584->835; marriage book 404->103 (residual lexically-grounded, acceptable); the two real longevity books preserved (186->185). Live-validated: "how does my longevity look?" selects domains=["longevity"] on the planner's own reasoning (no prompt change) and no longer pulls the marriage book. A PLANNER gloss nudge was authored then REVERTED -- Sulabh: an "also select health when X" clause is per-scenario hardcoding that does not scale; the planner's widen doctrine decides routing.

PART B -- LONGEVITY BUILD (parameters-only; the S166 lock implemented). The engine knew maraka LORDS + dasha windows only (zero strength, zero protection), so the interpreter could only recite textbook, never read the chart. Built: (1) `maraka_facts.build_maraka_strength_facts(facts)` -- an ENRICHMENT pass (runs in static_facts AFTER shadbala, because build_maraka_facts runs inside build_chart_facts BEFORE shadbala exists) emitting per maraka planet: lord-role flags, `natural_malefic` (fixed {Sun,Mars,Saturn,Rahu,Ketu}; Mercury/Moon UNCLASSIFIED -> corpus decides), a REAL shadbala read-through (None for nodes), `afflicts_2/7`, `benefic_save_present`. (2) risk_windows carry definitional `kinds` (maraka/randhra/ayushkaraka) via `_kinds_of` -- the engine already distinguished 2/7-lord vs 8th-lord vs Ayushkaraka in `roles`; this normalises it. (3) new `protective_facts.build_protective_facts(facts)` -- Ayushkaraka strength, lagna + lagna-lord strength & benefic aspects, 3rd/8th lord strength. Both NEST under the existing `maraka` key (no FACT_BLOCK_PROVIDES change). (4) `pipeline._fact_block` renders strength + protective + per-window kind + a WHOLISTIC/NO-NUMBER frame; the maraka caveat corrected so [randhra] windows are no longer lumped as "elevated risk". NO invented weight/score/verdict anywhere -- importance is corpus doctrine applied by the interpreter.

WINDOW-KIND VALIDATION (deterministic dump, no model). Sulabh's Jul2027-Feb2028 window = Ketu MD / Moon AD, flagged by the maraka engine under the "8th lord (longevity/randhra)" role -> kinds=[randhra], phase=current -- NOT maraka, and Sade Sati=NONE then (Saturn in Pisces, 4th), so not a transit-affliction window either. Confirmed Sulabh's instinct ("a health date, not malefic maraka"): the engine already drew the distinction; the bug was flattening it into one "elevated risk" bucket. Fix = surface the existing role-kind, zero new classification code.

LIVE RESULT (qa_capture 20261122T081354Z, gpt-6-luna). Markedly better than the pre-build answer: reads Jul2027 as "the Moon, linked with transitions and health attention... not forecasts of a fatal event"; grounds Jupiter in "meets the stated minimum strength" (real shadbala, no textbook filler); qualitative, no number, interpreter_refused=null. Residual: the synthesis UNDER-WEIGHTS the protective side (never names the weak Mercury maraka; reads strong lagna-Saturn as "strain") -- model conservatism (gpt-6-luna), not an engine gap; the corpus HAS the doctrine (whole-corpus scan: arishta/maraka/weak-strong present; alpa/madhya/poorna bands present).

PART C -- app.py refresh bug (reported live). Calculate Kundali recomputed the chart but never cleared `st.session_state.messages`, so a new person's chart loaded under the previous person's answers AND the old thread was fed to the planner/interpreter (S147). Fix: reset messages + SessionManager when `(name,dob,tob,place)` changes; a same-details re-calc (marital toggle) keeps the chat.

DECISIONS (Sulabh). (i) NO-NUMBER STANDS but RATIONALE RE-BASED off "it falsified on Sulabh's chart" (symptom of single-factor reading) onto principle: PVR rejects the number-methods + no oracle for a lifespan number. A classical band (alpa/madhya/purna) may be named ONLY as attribution to the tradition with its uncertainty, never as a prediction; concreteness comes from the specific caution windows, not a year-range. (ii) three-pairs is BUILD-NEXT-SESSION not dropped -- a single-factor method falsifies BECAUSE it ignores strength/protection, so feed it as ONE structural input (category-only) among many; source-faithful from the PVR Ch.14 PDF, do NOT fabricate the sign-modality->category table. (iii) arishta-bhanga depth: whole-corpus scan found NO dedicated Balarishta/Arishtabhanga chapter (ch43 already longevity-tagged; ~5 incidental mentions) -- NOT a re-tagging gap; ingest a classical source next session. (iv) under-weighting = model lever (Terra = quality revert target), not code.

NEXT SESSION: three-pairs source-faithful build (PVR Ch.14 PDF, category-only) + arishta-bhanga classical ingest + consider Terra for longevity-class synthesis. Carried: 11 pending Tajika sahams + Varshaphal D aspects; Pratyantar; Lal Kitab; LIVE FINDINGS #1/#2; planner plan-diff validation on gpt-6-luna; PALM gpt-6 migration (deadline 14 Jan 2027).

## S166 (2026-11-22) -- Longevity decline root-caused (env, not code) + qa_capture fact-block stamp + sahams/maraka engine committed (SCHEMA 5->6) + longevity architecture finalized (design only) + RAG/ChromaDB drift guardrail

**COWORK/DESIGN-CHAT SESSION (no Claude Code except git). Opened from a handover chasing a 3-cycle "longevity question declines" loop.**

**1. Root cause -- environmental, NOT a pipeline bug.** The handover's gate command (`python -c` schema/maraka probe) returned working-tree / SCHEMA_VERSION 6 / `build_maraka_facts in build_chart_facts.__globals__ == True`. The handover framed `maraka absent + saham refs: 0` as ONE symptom with one cause (stale interpreter). It is TWO different paths: (a) maraka is baked into `chart_facts` (`chart_facts.py:89-91`), which `fact_store` caches under SCHEMA_VERSION -> a stale schema-5 cache/process serves a maraka-less dict (the REAL signal); (b) sahams are computed at ANSWER time and merged into a fresh copy (`pipeline.answer_question` ~L1182 `chart_facts = {**chart_facts, "varshaphal": _vp}`), bypassing `fact_store` entirely -> a stale cache CANNOT suppress them; `saham refs: 0` was a MEASUREMENT ARTIFACT (grepping the captured `chart_facts` dict, where sahams never live). The three cycles partly chased a ghost.

**2. The actual capture gap + fix (commit `2807af1`).** `qa_capture.py` recorded the `chart_facts` dict but NOT the assembled fact-block TEXT the interpreter reads -- and `trace["fact_block"]` was ALREADY produced by the pipeline (both return paths, `pipeline.py:1314`/`:1374`), just never rendered. One-file surgical add to `capture_turn`: a "### fact block -- EXACT text the interpreter received" section. No new imports, guarded fallback on refusal-before-assembly. Tests: 31 passed (`-k qa_capture`). "Did maraka/sahams reach the model?" is now a one-read answer, never inference again.

**3. Engine was uncommitted despite the handover saying "committed" (commit `7c0a751`).** `git status` showed the sahams/maraka engine sitting in the working tree: `capability_gate`, `capability_registry`, `chart_facts`, `fact_store` (SCHEMA 5->6), `pipeline`, `varshaphal_facts`, `maraka_facts` (new, S165), `sahams.py` + 3 tests. Exactly the S157 process-loss failure mode. Committed engine-only (explicit paths, NOT `git add -A`); suite 5427 passed. HEAD now carries schema 6 -> the ghost is dead.

**4. Data-file triage (I was wrong, the halt was right).** Two data files (`domain_tags_bphs.json`, `chapter_index_bphs.json`) showed the 1-add/65k-delete minification shape. I called them "whitespace-only, restore from HEAD" -- WRONG (I trusted the stale internal `generated_at: 2026-09-27`). Claude Code's pre-restore parse caught that they are semantically DIFFERENT: +42 real segments (5187->5229) and a NEW `nila_sahams` unit under book "Tajika-Nilakanthi" (the roadmap-#1 sahams corpus-domain, pulled from `data/pdfs/tajika_nilakanthi_hindi_djvu.txt` -> `data/tajika_sahams_corpus.txt`). Restoring would have deleted 42 segments. Lesson re-confirmed: never infer "reformat" from an internal timestamp; diff against HEAD. These files got MINIFIED by their build script -- regression; keep them pretty-printed (indent=2).

**5. Live re-test -- RESOLVED.** After restart, "how does my longevity look" ANSWERED (capture `20261121T183846Z.md`): fact block carries both the Maraka/longevity framework lines AND the full Tajaka Sahams block; `interpreter_refused: null`; output = qualitative, no death date, future windows **July 2027-Feb 2028 + June 2030-Aug 2032**, honest confidence caveat. Confirmed NOT a gpt-6-luna refusal -- the model answered once the data reached it. The handover's "add an interpreter longevity clause" watch-item is UNNECESSARY.

**6. Longevity research (PVR Ch.14, read this session) + architecture (FINALIZED, DESIGN ONLY).** NO ayurdaya/longevity-span engine exists; `maraka_facts.py` emits only maraka LORDS + dasha windows (zero strength, zero protective side). PVR's real range method = "Method of Three Pairs" (he REJECTS Pindayu/Amshayu/Nisargayu as unreliable). Computed on Sulabh (Lagna Sg; pair1 Jupiter-Aries/Moon-Scorpio=Middle; pair2 Moon-Scorpio/Saturn-Sg=Long; pair3 Lagna-Sg/HL-Libra=Short -> all-different -> prefer pair3 -> "Short life 0-36") = FALSIFIED (alive, 40s). This is the PROOF that a raw longevity NUMBER is unsafe. Sulabh's chart: Saturn (Ayushkaraka) in 1st (+ Lal Kitab "long life") and Jupiter in 5th throwing its 9th aspect on Lagna = Arishta-bhanga -- the protective factors `maraka_facts` never emits. RULINGS (Sulabh): (i) NEVER surface a longevity number/paramaayush -- qualitative band + windows only. (ii) WEIGHTS: calcs emit PARAMETERS ONLY (structural flags + real computed shadbala); NO invented importance weights in code; importance = CORPUS doctrine applied by the interpreter (extends S161). (iii) BUILD LIST (not started, gated on ratification): maraka-strength params (is_2nd/7th_lord, is_malefic, shadbala, afflicts_2/7, benefic_save_present) + Arishta-bhanga/protective facts (Ayushkaraka placement+strength, benefic aspects to lagna/lagna-lord, 3rd/8th strength); three-pairs category optional, structural-only, never the number. (iv) ITERATIVE-INTERPRETER LOOP (interpreter requests more calcs mid-answer) PARKED -- all calcs upfront => single pass suffices; the loop is only a breadth/ceiling fix (LIVE FINDING #2), do not refile as a longevity need. (v) CORPUS: longevity doctrine = BPHS 43-44 + `kp_longevity_hariharan`, NOT the Tajika sahams corpus (that is ANNUAL). TODO: proper `longevity`-domain tagging (incl. the Tajika corpus) in the pipeline before build.

**7. RAG/ChromaDB drift guardrail (CLAUDE.md).** Clarified (Sulabh): the astrology answer path is NOT vector RAG/ChromaDB -- it is deterministic tagged-segment selection over `chapter_index_bphs.json` + `domain_tags_bphs.json`. Fixed the misleading head-matter "## Project" line and the "Interpretive RAG" reference line; added a loud locked decision so no future session drifts back to the parked ChromaDB methodology.

**COMMITS:** `2807af1` (qa_capture stamp), `7c0a751` (engine, schema 6), + corpus commit + this docs commit (S166 close). Not pushed.

## S162 (2026-11-15) -- Ephemeris split (.se1 everywhere) + Tajaka Sahams engine (21/30 validated, 11 quarantined)

PART A -- EPHEMERIS SPLIT (committed + validated).
- Root cause: every calc requested `FLG_SWIEPH`, but only `varsha_pravesh` ever called `swe.set_ephe_path` (process-global), so every other call silently fell back to Moshier. Researched first (per Sulabh): no genuine reason for Moshier -- it was an accident, not a choice.
- New leaf `agent/calculations/helpers/ephemeris_config.py`: single `EPHE_PATH` (-> `PyJHora-main/src/jhora/data/ephe`), `swe.set_ephe_path(EPHE_PATH)` at import. Imported (noqa F401) by `ephemeris.py` + `chart_calculator.py` -- the keystone, since conftest imports chart_calculator so the whole suite flips to .se1. Removed `varsha_pravesh`'s local `set_ephe_path` + try/finally restore dance.
- Impact: sub-arcsecond (Moshier ~0.025" vs .se1). Re-baselined 6 David characterization GOLDEN_LONGITUDES to .se1 values (Sun/Moon/Mars/Mercury/Jupiter/Venus; Saturn/Rahu/Ketu unchanged); all 25 David tests green. A Moshier/.se1 delta on any other chart's goldens is a re-baseline, NOT a regression.
- `varsha_pravesh` validated post-split: annual chart matches JHora to 0.14" (planets) / 4' (Lagna = 0.066deg, under the 0.5deg tol) -- rules varsha_pravesh out as any saham-error source.

PART B -- TAJAKA SAHAMS ENGINE (committed; 21 emitted, 11 quarantined; NOT yet wired to fact block).
- New `agent/calculations/annual/sahams.py`. Spec source (P-028): B.V. Raman *Varshaphal* Ch.VII pp.34-36 + Tajika Nilakanthi (`data/tajika_nilakanthi_hindi_djvu.txt`) Saham adhyaya. JHora v8 section 9 (`tests/fixtures/jhora_sulabh.md`, 4 Sulabh annual charts: 2024/25 day, 2026/27 night) GRADES ONLY.
- TWO rules validated across ALL 4 charts (not fitted): (1) 3-term sahams apply the +30deg rule to (A-B) then close with the THIRD point instead of the Lagna; (2) NIGHT reverses A,B for EVERY saham -- JHora's measured reverse-all convention (16 night mismatches vs 26 under Raman's selective reversal; confirmed concretely -- JHora night Bhratru = its Jeeva, the exact swap).
- METHOD CORRECTION (Sulabh rebuke, logged): the first cut brute-forced A-B pairs to fit 2024 ALONE, then cited the book post-hoc -- the exact Validation-Source "oracle grades its own homework" failure. The 4-chart run caught it (2025:7, 2026:16, 2027:17 mismatches); several pairs were only coincidentally right on 2024 (Samartha==Kali, Roga==Sraddha, Vyapara==Satru). Re-derivation from source + 4-chart validation is now the standard.
- RESULT: 21 CONFIRMED (Punya, Vidya, Yasas, Mitra, Pitru, Rajya, Putra, Jeeva, Karma, Vivaha, Satru, Mahatmya, Asha, Matru, Sraddha, Kali, Bandhu, Paradara, Vanik, Bandhana, Jadya) reproduce JHora on all 4 charts to <0.5deg -- emitted. 11 PENDING (Gaurava, Vyapara, Samartha, Bhratru, Roga, Sastra, Karyasiddhi, Artha, Labha, Santapa, Preeti, Jalapatana) QUARANTINED: `compute_sahams(..., include_pending=False)` by default, not emitted, not asserted -- each awaits its Nilakantha shloka re-derivation + a 4-chart pass before promotion.
- Deterministic test `tests/calculations/annual/test_sahams.py`: embeds the 4 annual charts (engine `varsha_pravesh` output) + the section-9 oracle, asserts the 21 CONFIRMED across both day and night branches + a pending-not-emitted guard + a missing-longitude error path = 6 passed (replaces the old all-31 `test_sahams_four_year_oracle`, which is removed). Doctrine: `docs/sahams_reconciliation_S162.md`.
- NEXT: wire the 21 into `varshaphal_facts` -> `_fact_block` -> `FACT_BLOCK_PROVIDES`; build a trimmed translated Nilakantha sahams results-corpus (txt) as a corpus domain; then derive the 11 pending.

## S161 (2026-11-15) -- T1 ties + T2 summary-to-top + D1 fact-block completeness + KP-hierarchy significator weighting (fidelity, not a ranking fix) + negation-stays-in-corpus ruling + live gpt-6-luna validation

DELIVERED (committed 35a8381: T1+T2+D1; KP batch committed + all PUSHED this session):
- T1 (ties): `timing_ranker` returns `five_year_windows` + `lifetime_peaks` LISTS (every top-scoring window), `render_ranking` flags a tie and names every co-equal window. Singular `five_year_window`/`lifetime_peak` kept = chronologically-earliest, byte-identical to pre-change (`_peak_windows(c)[0] == _peak_window(c)`). 6 new tests.
- T2: `interpreter.EXPERT_SYSTEM` moved the plain-language `In simple terms:` summary from END to the OPEN (prompt-only). Live-confirmed: every answer opens with it.
- D1: `tests/astro/test_fact_block_completeness.py` -- real `calculate_chart(Sulabh)` -> `build_static_facts` + `build_varshaphal_facts`, asserts 18 MUST sections non-empty. `masa` dropped to MAY (planner-gated dated fact, not in the static+varshaphal assembly). Closes the S157 class where varshaphal was silently empty while the suite stayed green (existing varshaphal tests all monkeypatch the ephemeris). Needs swisseph (runs on Sulabh's machine).

KP-HIERARCHY SIGNIFICATOR WEIGHTING (the real Stage 1; reprioritised from SAV-grading after the first-job hand-trace):
- `significator_engine` already computes a KP tier per (planet,house): 1 star_of_occupant (strongest) .. 4 owner (weakest), node-agency=None; cited to KP Reader II. `kp_significator_facts` previously FLATTENED it ("v2 upgrade" per its docstring).
- `kp_significator_facts` now ALSO emits `planet_signification_tiers` {planet:{house:tier}}; flat `planet_significations` byte-identical -> `_fact_block`/`capability_gate`/growth-contract untouched; no FACT_BLOCK_PROVIDES change (tiers consumed by the ranker, not rendered).
- `timing_ranker` weights the significator term by tier: `_TIER_WEIGHT` {1:1.0, 2:0.75, 3:0.5, 4:0.25}, node None floored 0.25, absent tier -> 1.0 (flat, byte-identical). `rank_windows` gains `signator_tiers` (keyword-only, default None); `build_timing_ranking` reads `kp.planet_signification_tiers`. ORDINAL model: order sourced to Reader II, equal-step numbers an explicit modelling choice (not a cited quantity), tier-1 anchored at 1.0 so nothing inflates, NEVER fitted to events. 8 new ranker tests; 40 tests green.
- 8-agent roster run; all pass with two documented notes (node weight contested -> floored; equal-step ladder is a modelling choice). Design record: `diagnostics/runs/20261115T0730Z_kp_hierarchy_weighting_design.md`.

BACK-TEST (`probe_timing_backtest_baseline.py` updated to dual-rank flat-vs-tiered + in-horizon + first-job date CORRECTED to Feb 2012):
- First-job "failure" was a WRONG DATE: the baseline used Feb-2011 Mercury-Ketu, which signifies no career house. Corrected to Feb-2012 Mercury-Venus, the FLAT model already ranks it 1/4 in-horizon.
- Tiering shrinks ties and is doctrinally cleaner but does NOT improve in-horizon rank for any clean event and REGRESSED Pashmina (3/7 -> 6/7). KEPT as a FIDELITY improvement per Sulabh (fidelity-not-truth charter), NOT an accuracy win. Do not re-litigate as a ranking fix.

ARCHITECTURE RULING (Sulabh): negation / promise / nullifiers (denial houses, cuspal-sub-lord promise, combustion, delay) are DOCTRINE and stay in the CORPUS, applied by the interpreter -- NEVER coded as per-scenario ranker rules (patchwork, won't generalise). Fact-block audit: NO plumbing gap -- full significations incl. denial houses, cusp sub-lords, combustion, debilitation, aspects all already rendered in `_fact_block`; the only friction is the promise two-step join (cusp sub-lord -> its significations), to watch in live validation, not a rule. The realistic metric is TOP-N HIT-RATE (event in one of the surfaced windows, ~75-90% = KP's own claim), NOT rank-1. Validation cases pinned: `diagnostics/llm_corpus_negation_validation_cases.md`.

LIVE VALIDATION (gpt-6-luna, `diagnostics/qa_capture/20261115T084124Z.md`, 3 Qs):
- gpt-6-luna serving (570k/250k/441k prompt tokens); T2 summary-on-top OK; T1 ties presented as equal OK; layman/no-jargon OK; future-lead/time-direction OK ("best period already passed" effectively resolved).
- Career (Q2): corpus applied -- Mercury debilitation + cancellation + Venus/Mars strengths. PASS.
- Marriage (Q1): windows + tie CORRECT (true window Jan2018-Aug2020 in the top-2 tie; the other tied window Aug2008-Dec2010 is, from live significations, the STRONGER promise on paper -- Mercury the 7th-lord signifying 2 & 7 -- so NO negation down-ranks it; the earlier "prune 2008" was an age-bias error, retracted). No window-level negation was applicable; nothing wrongly omitted.
- Top-N hit metric: events land in surfaced windows for both marriage and career.

OPEN / NEXT (only these four continue): Ephemeris split (.se1 vs Moshier); Varshaphal Tajika aspects + Sahams (retires AstroSage); Pratyantar (+/-37d, suppressed) discussion; Lal Kitab start-or-not. Owed but NOT continued now: planner plan-diff on gpt-6-luna (`planner_decisions.jsonl` captured this run); palm GPT-6 migration (deadline 14 Jan 2027); D3 per-user spend alarm (needs user identity + pricing + accumulator -- parked until multi-user; threshold 10 AED captured).

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

