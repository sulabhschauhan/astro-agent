# ASTRO AGENT — MASTER BUILD PLAN

**Rewritten 2026-09-05 (S124+).** The previous version of this file was frozen at
**Session 42–44** and described a system that no longer exists: it named V1 as
"3-domain deterministic calc Q&A", carried an S23 lock forbidding LLM-synthesised
answer text, and contained no mention of the palm rules engine or the BPHS text
pipeline — the two things ~80 sessions of work actually produced. That version is
recoverable from git history and is not reconciled here; reconciling 55 KB of
stale phase-tasks would cost more than it returns.

**Authority.** `CLAUDE.md` remains authoritative for locked decisions and standing
law. `SESSION_LOG.md` (+ two archives) remains the evidentiary record. **This file
is the map** — what exists, what ships, what is decided, what is open and what
gates each open item. Where this file and `CLAUDE.md` disagree, `CLAUDE.md` wins
and this file is wrong and should be fixed.

**Ratified scope, 2026-09-05:** palm is IN V1 and is built. The S124 five-stage
pipeline is the final answer architecture. Horizon of this document extends
through V2.

---

## 1. OBJECTIVE

Answer a person's questions about their own life the way a good astrologer would
— grounded in classical text, never fabricated, and honest about what it cannot
say.

Two evidence surfaces, one voice:

- **The chart** — computed deterministically from birth data, interpreted against
  Brihat Parashara Hora Shastra.
- **The hand** — observed from photographs, interpreted against Cheiro.

Standing doctrine, applies to every branch below: **honest silence beats
confident-wrong.** A question the material cannot answer for *this* person gets a
stated refusal, never a hedge and never a Barnum sentence.

---

## 2. WHERE WE ARE — 2026-09-05

| | |
|---|---|
| Branch | `wip/interpretive-pilot` |
| Last verified HEAD | `cbe02fe` (S123 close) |
| Test suite | **3,840 passed / 7 skipped / 0 failed** |
| Uncommitted | Planner stage (`agent/astro/planner.py`, 39 tests) — built S125, not committed |
| Corpus in scope | BPHS vol 1+2 (astrology), Cheiro (palm) |
| Corpus NOT in scope | 11 further astrology books, Hasta Samudrika |

Three tracks are live. They are at very different maturities and this is the
single most important thing to hold in mind when planning:

| Track | Maturity | Blocking issue |
|---|---|---|
| **A — Calculation engine** | Shipped, broad | 16 of 74 modules are stubs |
| **B — Palm rules engine** | **Complete for V1 scope** | none — remaining lines are scoped out, not backlog |
| **C — BPHS text pipeline** | POC, end-to-end for the first time this session | Payload economics unresolved |

---

## 3. TRACK A — DETERMINISTIC CALCULATION ENGINE

Computes chart facts. **The LLM never computes a chart fact** (locked, S124).
This track is the fact source for everything downstream.

### Built

`agent/calculations/`, ten subpackages:

| Package | Contents |
|---|---|
| `core/` | chart_d1, panchanga, aspects, dignity, friendship, combustion |
| `vargas/` | D2–D60, navamsa, vimshopaka |
| `strength/` | shadbala (all 6 components + totals), bhava_bala, ishta_kashta, dig/drik/kala/sthana/chesta |
| `dashas/` | vimshottari, yogini, chara, ashtottari, mudda |
| `yogas/` | detector + catalog (raja, dhana, pancha_mahapurusha, neecha_bhanga, special) |
| `transits/` | gochara, sade_sati, chandrabala, tarabala, panchaka, muhurta_scorer, av_transit |
| `ashtakavarga/` | compute_bav + compute_sav |
| `jaimini/` | karakas, arudha, padas, strength, rasi_aspects |
| `annual/` | varshaphal, muntha, sahams |
| `helpers/` | ephemeris (canonical), house_counting, discrete_scan |

**Conventions (locked):** Python 3.11, pyswisseph, SIDM_LAHIRI, Whole Sign houses,
Mean Node. Signs 0–11 (0=Aries), nakshatras 0–26 (0=Ashwini). Attribute-style
`swe` access only — never `from swisseph import calc_ut`; tests monkeypatch the
module object.

**Validation protocol per module:** empirical validation across 4 reference charts
before locking a formula; zero free parameters; AstroSage parity where applicable,
JHora oracle where not; cross-software noise documented as discovered.

### Routed domains (hybrid router, `agent/infra/calc_router.py`)

Stage 1 keyword scoring (≥2 hits, 0.4 floor, 0.15 margin) → Stage 2 LLM
classification on Stage-1 refusals only → routes on `high` confidence, fails
closed. Built-module fastpath bypasses both.

Domains confirmed by name through S64: `current_dasha`,
`marriage_compatibility`, `career_strength`, `arudha_lagna`, `upapada_lagna`,
`muhurta_window`, `av_transit`.

> ⚠ **UNRECONCILED:** S64 records `_GENERIC_REFUSAL_MESSAGE` "re-synced to 8
> domains" but names 7 routed. Count the live `_VALID_DOMAINS` set before citing a
> figure. Do not propagate either number until verified.

**Golden harness:** 23 rows. Frozen baseline
`diagnostics/golden_scorecard_20260711_195218.md`
(match=10 / match_stage2=10 / known_gap=1 / new_gap=0).

**Tier model:** T1 exact · T2 range · T3 muhurta (the only wall-clock-anchored
domain) · T4 interpretive · REFUSAL.

### Remaining

- **16 of 74 calculation modules are stubs** (S124 open item 5) — vargas,
  vimshottari, yogas, shadbala, chart_d1 among them. *Facts gate answers as hard
  as text does:* Track C cannot answer what Track A cannot compute. **This is the
  most under-rated item in the whole plan.**
- Drik Bala stubbed at 0.0 for V1, with a mandatory caveat on every planet output.
- Router tuning backlog — dogfood-gated per the S44 lock. Tune only on Answer
  Scorecard evidence.

---

## 4. TRACK B — PALM RULES ENGINE

**Status: in V1, built, proven on real hands.**

> ✅ **RESOLVED 2026-09-05.** Both `CLAUDE.md` defects are now marked in place
> (supersede-don't-delete, entries retained). The S71 "V1 PALM DROPPED" lock is
> stamped SUPERSEDED — palm is in V1. The duplicate S72 palm-UI-gate entry is
> stamped STALE: verified by grep, `_PALM_ENABLED` **exists** at
> `frontend/app.py:47` and gates 4 UI render blocks (868, 889, 1259, 1440). The
> gate is implemented; V1.1 re-enable is `ASTRO_PALM_ENABLED=1`, a config flip.

### The pipeline (frozen, S95)

`data/palm_rules/_doctrine/PALM_PIPELINE.md` is the frozen 0–7 checklist every
remaining line must follow. Remaining lines are **volume, not design.**

```
photo → palm_processor (vision, structured fields)
      → HUMAN CHECKPOINT (display + confirm, mandatory)
      → observation_extractor → contact_mapper (deterministic)
                              → contact_llm_fallback (synonym rescue only)
      → palm_select.match()  hard-fire + soft-LLM + subset precedence
      → claim_extraction (Stage 1, gpt-4o-mini, temp 0)
      → claim_voicing    (Stage 2, gpt-4o) + display validators in the retry loop
      → reading
```

### Locked mechanisms

- **Self-grounding (S119).** A rule-sourced claim cites its OWN authored,
  gate-verified `source_page` + `source_quote`. No retrieval chunk is resolved for
  it. Citation accuracy **31% → 100%**, gate-verified. Rule claims bypass the
  retrieval support gate by construction.
- **Human checkpoint (S65/S66).** Every vision-derived description entering
  generation must be displayed and user-confirmed. Programmatic auto-confirm is an
  AI-reviewing-AI violation and was removed.
- **Page-range gate ON (S82).** Exactly one `search()` per feature carrying
  `page_ref=(start,end)` from `data/cheiro_feature_pages.json`, as two Chroma
  `$and` clauses. An empty range routes to the decline block — the unfiltered
  fallback is gone by design.
- **One-call-per-feature contract (S81).** Asserted by three independent tests.
  Any filter acts *inside* the query, never widen-then-post-filter.
- **Precedence = demote, never delete.** Suppressed rules stay in
  `result["suppressed"]`, auditable.
- **Definite absence is stated, can't-tell stays silent (S123 `9ce9028`).**
  "absent" earns a plain sentence; "not clearly visible" / "unremarkable" stay
  silent. Proven: exactly one new sentence across 9 captured hands.
- **Vision run-to-run variance on an identical photo is BY DESIGN** — borderline
  anatomical judgements a human palmist would also disagree on. A changed fired
  set on a re-run is never a regression.

### Coverage

| | |
|---|---|
| Live rules | 87 (was 99 before S119 retirements) |
| Parked rules | 16 |
| Citation gate | `NOT_FOUND_ANYWHERE = 0` across all live + parked |
| Chapters authored | Head, Heart, Life, Fate, Mounts — 4 rule files, the complete V1 set |
| Chapters NOT authored | **Scoped out or parked with recorded reasons, not backlog** |
| Corpus | Cheiro, 579 chunks — the only book with a labelled eval set (Ring 3) |

**Fired on real hands, before → after the S123 arc:** 6 of 87, with love and
destiny at zero → love (HL_001/HL_003), destiny (FT_003) and head (H_002) all
populated, confirmed end-to-end on 3 real subjects with claims == fired 1:1 and
zero silent drops.

**PALM IS DONE FOR V1 — correction, 2026-09-05.** An earlier draft of this file
listed Sun / Health / Mars / Marks / hand-types / fingers / thumb / nails as
"remaining chapters". That was read off S95's forward-looking list and is WRONG
as of today. **S96 formally scoped those out**, with per-configuration reasons
recorded in `data/palm_rules/unauthorable_register.json` (marks and signs,
hand-type family, two-hand laterality, and the whole p136-139 Influence-ray
subsystem — all "not emission-reachable" or outside the Cheiro-Western core).
Marriage lines are PARKED (no vision emitter block exists, so they are
architecturally unmeasurable). Thumb is PARKED (same relative-judgement class as
the dead `proximity_degree` axis). The four live rule files — `head_heart`,
`life_line`, `fate_line`, `mounts` — ARE the V1 palm scope, and it is complete.
Do not re-open any of these without new evidence; the register exists precisely
so closed questions are not re-litigated.

### Known gaps, deliberate

- **The Indian tradition is absent.** Palm grounds on Cheiro (Western) only. Hasta
  Samudrika is 449 pages of OCR noise — 4 pages with ≥50 alphabetic words, zero
  Devanagari. **Do not ingest or repair it.** Fix path is re-sourcing an English
  edition or Devanagari OCR + translate. Real doctrinal gap, recorded not hidden.
- **Absence doctrine parked on yield, not risk** — only 2 cleanly authorable
  absence rules across all 579 chunks. Revisit triggers recorded in `CLAUDE.md`.
- **~15 tests in `test_palm_rules_table.py` are pinned to live doctrine rule ids.**
  A legitimate rule edit can break a test that was never about that rule. Filed at
  `diagnostics/KNOWN_PATTERNS.md` P-021. Rule for whoever hits the next one:
  rebuild synthetically through the real `PalmRule`/`Antecedent` path — never
  re-point at a different real rule, which only relocates the landmine.
- Quadrangle rules (H_010a/b, HL_006, HL_021) parked pending a vision emitter for
  quadrangle breadth.

---

## 5. TRACK C — BPHS TEXT ANSWERING PIPELINE

**The final answer architecture** (ratified 2026-09-05). Five stages.

```
question → PLANNER → CALCULATOR → RETRIEVER → INTERPRETER → VERIFIER → answer
```

| Stage | State | Owner artifact |
|---|---|---|
| 1. Planner | **BUILT S125**, uncommitted, live-verified once | `agent/astro/planner.py` |
| 2. Calculator | Partial — 16 of 74 modules stubbed | Track A |
| 3. Retriever | Done | `chapter_index_bphs.json`, `domain_tags_bphs.json`, `payload_builder.py` |
| 4. Interpreter | Done, zero fabrications measured | one LLM call, cites location |
| 5. Verifier | Detect-only. **Silence gate does not exist** | — |

### Locked decisions (S124 — do not revisit)

- **Rule authoring is DEAD for astrology.** No hand-authored doctrine rules.
  Fidelity moves from build time to run time. *(Note the asymmetry with Track B,
  which is rule-authored. This is deliberate: Cheiro is small and has a labelled
  eval set; BPHS is not and does not.)*
- Retrieval **is** in the citation path. The prior constraint forbidding this is
  retired.
- Retrieval unit = **chapter**. Notes and commentary stay attached to their verse.
- Addressing = **ordinal** position (`ch24_s001`…), contiguous, no gaps. Printed
  verse numbers are metadata only — 35 of ch24's 144 are missing to OCR, so they
  cannot be addresses. Printed page numbers dropped entirely; `page_ref` is the
  internal key.
- Citations are **internal only**, for debug logs. Never shown to the user.
- Devanagari stripped from payloads, retained in storage. 37% token cut, no quality
  loss (6-run A/B).
- Interpreter **never quotes** — it cites a location and the system fetches text.
- **Filter fails SAFE** — unparsed or untagged content is KEPT, never dropped.
- No answer skeletons, no priority/ranking tags, no relevance-ordered payloads.
  Ranking cannot be defined domain-free.
- Router **reasons** about houses, including derived / bhavat-bhavam. No fixed
  domain-to-house table.
- **16-domain closed vocabulary, locked:** career, marriage, wealth, children,
  health, education, longevity, travel, property, parents, siblings, spirituality,
  enemies_conflict, timing_dasha, technique_method, planetary_nature.

### Artifacts

| Artifact | Content | Validation |
|---|---|---|
| `chapter_index_bphs.json` | 100 units | 7/7 checks pass, zero character loss. Canary: `bphs1_ch24` starts at `page_ref` 188 |
| `domain_tags_bphs.json` | 1,129 segments, 100 units | Unfittable rate 0.09% — the vocabulary holds at scale. Re-tag reproducibility 8/8 blind |
| `segment_index_bphs_career3.json` | 135 segments | ordinals + `text_sha256` drift protection |
| `career_payload_bphs.json` | filtered career payload | 31.6% within-chapter cut |
| `agent/astro/payload_builder.py` | generic payload builder | — |

### The Planner (built S125)

One LLM call. Emits `{domains, houses, whose_chart, time_scope, in_scope,
reasoning}`. Python validates **shape only** — house ∈ 1–12, domain ∈ the closed
16, `whose_chart` ∈ {self, other}. It never checks whether the doctrine is right;
that would reintroduce the table this architecture removed.

- Malformed output → **one retry** → deterministic keyword fallback stamped
  `planner_fallback: true`. Every decision logged to
  `diagnostics/planner_decisions.jsonl`. The fallback never guesses houses and
  refuses outright when nothing matches.
- `calc_router.py` was **deliberately not** used as the fallback: it emits
  calculation domains, a different type in a different stage, and mapping it onto
  the 16 text domains would be a fresh hardcoded table. It is untouched and
  continues to serve Track A.
- Other people's charts resolve onto the native's own chart via bhavat-bhavam.
  **The system never needs a second birth record.**
- Hard context ceiling: **72,000** approx-tokens (recalibrated from real
  `prompt_tokens`; ratio 1.70 with headroom). Over it the pipeline **refuses and
  says why** — it never truncates, because silently dropping doctrine is the
  confident-wrong failure this architecture exists to prevent. A CI test asserts
  ceiling × ratio stays inside the model window, so raising one without the other
  fails. Separately, `INTERPRETER_TPM_LIMIT = 30,000` warns but never refuses —
  it is account-tier specific and an upgrade changes it without a code change.

**Both S124 live bugs are closed by construction:**

| Bug | Was | Now |
|---|---|---|
| "will my child succeed in his career" returned the USER's Shadbala | no whose-chart concept | `whose_chart: other`, houses `[5, 2, 10]` — the 2nd being the 10th-from-the-5th |
| any question naming the sign "Cancer" refused as medical | substring out-of-scope guard | no substring guard exists; a test asserts one cannot be re-added |

### Measured facts (do not re-derive)

- **S124 open item 1 is CLOSED and was FALSE.** The tags are not title-inferred.
  Zero of 100 units. Every unit was tagged from real corpus text at one of three
  read depths. No re-read budget is needed.
- Zero genuine fabrications across all interpreter runs. Location-based citation
  was never beaten.
- **Three separate times a "fabrication" was called and was wrong** — the tool or
  the diagnostic was at fault. *Check the tool before blaming the model.*
- The relation filter cuts 31.6% within selected chapters but only 4.6% across the
  whole book. **It is a within-chapter tool, not a selector.**
- `approx_tokens` is a WORD COUNT and undercounts the real tokeniser by
  **1.61–1.66×**, measured against real OpenAI `prompt_tokens` (48,589 → 80,882;
  12,864 → 20,736). A chars/4 estimate is itself ~17% low on this corpus, because
  Devanagari-stripped OCR text fragments badly. **Never size a payload from
  `approx_tokens` or chars/4 — only from `prompt_tokens`.**
- Temperature 0 + fixed seed did **not** produce identical OpenAI output. Some
  nondeterminism is inherent to the serving stack.
- Reading corpus text costs ~9× source tokens due to Devanagari fragments.

### Payload economics — the open problem (S125)

Selection cost, measured, as a share of the 242,571-approx-token corpus:

| Question | whole chapters | + relation filter | + domain filter (shipped) |
|---|---|---|---|
| "my career?" | 97,480 (40%) | 90,653 (37%) | **48,589 (20%)** |
| "my child's career?" | 122,531 (51%) | 111,640 (46%) | **64,967 (27%)** |
| "when will I marry?" | 127,931 (53%) | 117,402 (48%) | **91,418 (38%)** |

Two hard constraints discovered on the first live end-to-end run:

1. **gpt-4o is unusable at this payload size on the current tier.** TPM cap is
   30,000; a 68,342-token request is rejected outright (429, pre-billing). Not a
   quality signal — but it closes the "stay on gpt-4o" path until the payload
   shrinks or the tier is raised.
2. **The payload may be too large for the model to actually read.** gpt-4o-mini
   was sent 304 verses and returned **one claim**, citing one whole-chapter unit
   (`bphs2_ch48`, a dasha chapter) in answer to a career question — and the claim
   was conditional ("*if* the lord of the 10th is well placed"), never resolving
   against the fact block that was supplied.

### RESOLVED 2026-09-05 — wide vs strict, measured

The wide-vs-strict probe ran. **The fail-safe assumption is falsified for
house-shaped questions.**

| Arm | Model | Segments | Cost | Claims | Cited |
|---|---|---|---|---|---|
| A (wide) | gpt-4o-mini | 304 | $0.0122 | 1 | `bphs2_ch48` |
| B (strict) | gpt-4o-mini | **6** | $0.0032 | 1 | `bphs2_ch48` — identical |
| B (strict) | **gpt-4o** | 6 | $0.0547 | **2** | `bphs2_ch48`, `ch24_s106` |

Dropping 298 of 304 segments changed mini's citation set by nothing. And the
smaller payload cleared the TPM cap, which made **gpt-4o available for the first
time** — and gpt-4o produced the better answer: two claims, a real verse citation,
and a specific reading naming the placement and putting the claim on a dasha.

**Second finding, unanticipated:** in BOTH mini arms the single citation came from
a *whole-chapter unit* — `domain_match` count zero. Mini never cited one of the
304 verses at all. gpt-4o is the only run that cited a real verse. Every earlier
mini-only result is therefore a weaker signal than it appeared.

**Scope limit, stated:** N=1, one question, one chart, and `career` is the
friendliest case — house-10 relations are densely written in ch24. A timing
question ("when will I marry") names periods, not houses, so `extract_relations`
finds nothing and strict would likely empty the payload. **Strict is proven for
relation-shaped questions and unproven for timing ones. It cannot ship as-is.**

---

## 6. V1 — WHAT SHIPS

**Definition.** One chart, one hand, one voice. A user supplies birth data and
optionally palm photographs, and asks questions in plain language. The system
answers from computed chart facts + BPHS text, and from confirmed palm
observations + Cheiro, or states plainly that it cannot.

### Ships

- Track A deterministic answers across the routed domains, with the tier model and
  the refusal tier.
- Track B palm reading — upload-triggered, human-checkpointed, self-grounded.
- Track C text answering over BPHS 1+2 via the five-stage pipeline.
- AstroSage paragraph displayed verbatim from parser output (no RAG, no LLM
  synthesis). Pratyantar and Lal Kitab sections extracted but withheld at the
  display layer.
- Streamlit as the sole frontend surface (locked S72, through V1 **and** V1.1).

### Does not ship

- Remedies of any kind — including gemstones. Out of V1 scope entirely.
- Pratyantar dasha (±37-day drift, wrong lord).
- Kundali × palm cross-verification (deferred V1.1, Parashara dissent logged as a
  real capability cut).
- Prokerala API — designed, not built, backup only.
- Any book beyond BPHS 1+2 and Cheiro.

### Remaining to ship, ordered

| # | Item | Gate |
|---|---|---|
| 1 | **Resolve payload economics** | Wide-vs-strict probe (§8.1) |
| 2 | **Silence gate** | Needs #1 — the gate must know what was asked before deciding what is missing |
| 3 | **Commit the Planner** | Ratification token; live run across all 4 POC questions |
| 4 | **Close the 16 stubbed calculation modules** | Prioritise by which domains they gate |
| 5 | **Finish the palm chapters** | Run `PALM_PIPELINE.md` per line — volume, not design |
| 6 | **Resolve the palm UI gate contradiction** | One grep |
| 7 | **Privacy: purge tracked user data from the public repo** | `data/default_user/`, 5 `data/sessions/*.json` — violates the no-storage lock. Needs a second history rewrite |
| 8 | **`requirements.txt` is a one-line stub** in what is now the distribution artifact | — |

Items 7 and 8 are small and have been open a long time. 7 is the one that matters.

---

## 7. BEYOND V1

### V1.1

- **Palm revisit** — kundali × palm cross-verification, gated on a lock-compliant
  deterministic chart-summary export.
- Yogini and Ashtottari dashas wired.
- D10 and D7.
- Stage-1 parallelisation.
- Contrast preprocessing before vision description (photo-lighting delta measured
  at Ring 3 pass 2).
- Layman progressive disclosure — surface interpretive depth gradually rather than
  one dense paragraph.
- Plain-language field glosses at the human checkpoint (a layperson confirming
  "FATE LINE: barely visible" may not know what a fate line signifies).
- `AppTest`-in-CI for Streamlit.
- `ask()` / `prompt_builder` / `context_classifier` quarantine residue in
  `app.py` — inventory and retirement decision.
- `astrosage_parser.py` noise-strip + public `SECTION_NAMES` alias; splitter
  coverage broadening (live splitter captures 6/7 of its own target sections and
  misses `Transit Today`; the PDF's real taxonomy has 31 sections).

### V1.5 — Rule Engine Foundation

**PROPOSED, UNRATIFIED.** Design at
`playbook_export/decisions/rule-engine-v1_5-design.md`. Generalises the
domain-assembler pattern before V2 scales it 10×.

**Four prerequisites, all must be green before V1.5.1 opens:**

1. V1 shipped, including the palm UI gate
2. Ashtottari wired
3. D10 + D7 built
4. Palm revisit decided

Plus the **rule-of-three**: a 4th hand-coded domain before generalising. A
single-domain Cheiro pilot running does not satisfy this. Do not conflate "pilot
running" with "gates lifted." Premature start is the path-(c) failure mode class.

### V2

- **Corpus expansion** — the 11 untouched astrology books. Sizing must read PDF
  page counts directly; `data/progress/*.json` covers 14 of 22 books and has no
  `native_text_present` field, so the 75.9% figure is unusable.
- **Interpretive template layer** — scoped to the AstroSage COVERED-PARTIAL
  sections first (audit: 13 NOT-COVERED, 10 COVERED-PARTIAL), classical-corpus
  sourced, deterministic placement-keyed, **no serve-time LLM**.
- **Cross-chapter doctrine linking** — compound conditional doctrine is genuinely
  cross-chapter; a future extraction pass needs a linking step.
- **AstroSage PDF removal** in favour of in-house computation, plus ingest-time
  content-role tagging for the classical corpus. Recorded at S115 as "the large
  unbuilt half, not started."
- **Lal Kitab remedy tier** — post-V1 design gate. Requires, before *any* wiring: a
  rewrite of golden row R5, a V1-scope amendment in `CLAUDE.md`, and design-chat
  consensus. Scoped RAG-grounded and cited, never prescriptive.

---

## 8. OPEN DECISIONS AND THEIR GATES

Each of these blocks something. None should be decided without its gate.

### 8.1 Wide vs strict payload — **HALF ANSWERED**

RUN 2026-09-05, result in §5. Wide is dead for house-shaped questions: 298 of 304
segments contributed zero citations, and the strict payload let gpt-4o run and
answer better. **What remains open is whether strict generalises to
`timing_dasha`**, where verses name periods rather than houses and the filter will
likely keep nothing. Gate: re-run the same probe on "When will I get married?"
before any selection rewrite. If strict empties there — the expected outcome —
`timing_dasha` needs a relevance signal of its own (planet and period names), and
that is a design decision, not another probe.

### 8.2 Interpreter model

gpt-4o is blocked by the TPM cap at the current payload size. gpt-4o-mini is 17×
cheaper and runs, but S71 dropped palm reading precisely because mini could not
reliably judge hedged classical prose. **That was Stage-1 extraction from Cheiro,
a different job** from reading a fact block and citing verse ids — so S71 is not
automatically dispositive here, but it is not nothing. Gated on 8.1, because a
smaller payload changes the answer.

### 8.3 Silence gate

Does not exist. The Verifier detects only. The gate needs to know what was asked
before it can decide what is missing — so it is gated on the Planner's output
being trusted, which is gated on 8.1.

### 8.4 Palm UI gate — ~~contradiction~~ **CLOSED 2026-09-05**

`_PALM_ENABLED` exists at `frontend/app.py:47`, gating 4 render blocks. The gate is
implemented. The stale `CLAUDE.md` entry is marked in place. No further action.

### 8.5 Houses are reasoned but unconsumed

The Planner emits `houses`, and nothing downstream reads them. Wiring them into
selection was measured and buys **1–2%** with the fail-safe on — so this is *not*
the cost lever it looked like. It may still be the right relevance signal for the
silence gate. Gated on 8.1 and 8.3.

### 8.6 Roster count

`CLAUDE.md` Working Style #7 says the agent roster is 9; 8 are documented
(architect, business, critic, qa, ui_ux, debate, Ephemeris Auditor, Validation
Source). **Name the 9th or drop the count.** Do not cite "9 agents" as settled.

---

## 9. DEAD — DO NOT REBUILD

Recorded so a later session does not re-propose them as fresh ideas.

| Rejected | Why |
|---|---|
| Hand-authored doctrine rules for astrology | S124 lock. Fidelity moved to run time |
| Entity-level tagging (houses/planets as flat lists) | Kept 122/135 — a 4% cut. Only the RELATIONSHIP identifies the matching cell |
| Priority / ranking tags | Measured *worse* citation agreement than free-form (0.60 vs 0.625 Jaccard) |
| Strict verbatim quoting | 73% failure, almost all cosmetic — case, curly quotes, models silently correcting OCR typos |
| TOC-based chapter detection | OCR-damaged. Sequential walk works |
| Subagents as interpreters | Tool access cannot be disabled in Claude Code, so context isolation is impossible and repo contamination is live. 167k per run. Use OpenAI |
| Parallel / multi-agent fan-out | 300k+ overruns. Sequential only |
| Hasta Samudrika as-is | 449 pages, 4 usable. Re-source or re-OCR; do not repair |
| Pratyantar dasha | ±37-day drift, wrong lord |
| Per-rule fixes and parking as a strategy | Treadmill. Does not survive 600–1,200 Cheiro rules |
| Query-template variant-iv (pure-Python clause assembly) | Degraded both probed features' target-chunk ranks |
| Deeper unfiltered palm retrieval | Chapter provenance is metadata, unrecoverable from chunk text |
| `pypdf` | Use `pdfplumber` |

---

## 10. STANDING LAW

Full text in `CLAUDE.md`. The ones that most often get violated:

1. **REVIEW before PROCEED** — flag at least one issue before approving any edit.
2. **SAMPLE before SCALE** · **HARDEST CASE first**.
3. **THRESHOLD DISCIPLINE** — every numeric threshold needs justification, scope
   guard and tuning note.
4. **AI reviewing AI** — never chain AI decisions without a human checkpoint.
5. **LAYER FIRST** — name the owning layer (Data / Retrieval / Prompt / UI) before
   any fix.
6. **NO ANCHORED JUDGMENT** — never give an LLM both a stated expectation and a
   request to judge against it. The LLM observes; Python compares.
7. **DESIGN-INTENT-FIRST (S123)** — everything present or absent is by design until
   the record proves otherwise. Nothing is a bug without a history search and an
   explicit verdict label.
8. **Data-property is not a live symptom (S83)** — measure the live path before
   calling anything a leak.
9. **EXISTENCE vs RANK (S81)** — "absent from top N" is not "missing from corpus".
   Establish existence by direct id lookup, never by search output. Conflating
   these produced a false verdict and three sessions of wrong direction.
10. **COMMIT RATIFICATION TOKEN** — never commit a source edit without the literal
    line `RATIFIED: commit authorized`.
11. **NEVER REWRITE PUSHED HISTORY ON MAIN.**
12. **Diagnostic output → `diagnostics/latest_run.md`**, archived to
    `diagnostics/runs/<timestamp>.md`. Chat gets ≤10 lines.

---

## 11. MAINTENANCE OF THIS FILE

Update at session close **only** when a track's state changes — not per commit.
If this file and `CLAUDE.md` disagree, `CLAUDE.md` wins. If this file grows past
~20 KB it has started duplicating the session log and should be cut back to the
map, not the record.

**Dead files retired alongside this rewrite (2026-09-05):** `SESSION_5_PLAN.md`,
`claude_handover_S97.md`, and the project-side `claude/handover_S94.md`. All three
described a superseded current state — a stale handover is worse than none,
because it is confidently wrong.
