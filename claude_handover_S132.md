# HANDOVER -> S133 (written at end of S132, 2026-09-13)

**RECOMMENDED MODEL: Sonnet 4.6** for the pending items below. Opus only for
the fact-block/answer-path wiring decision, or debugging stuck after 2 attempts.

---

## 0. READ THESE FIRST, IN THIS ORDER

**The order is the point.** S132 burned most of a session because it read the
newest document first and the oldest last.

1. `ASTRO AGENT — MASTER BUILD PLAN.md` -- the module's own plan entry.
2. `CLAUDE.md` -- Locked Decisions, S132 entry first.
3. `diagnostics/KNOWN_PATTERNS.md` rows **P-026 .. P-029** (added S132).
4. `agent/calculations/yogas/rules.py` module docstring.
5. `SESSION_LOG.md` -> `## S132`, then this file.

Rules 32/33/34 bind you: never assert from memory or a summary -- including
this handover -- when a primary source is available.

---

## 1. STATE OF THE TREE

S131 was committed as three commits ending `9473c55` on `wip/interpretive-pilot`.
S132 is **UNCOMMITTED** on top of it.

| file | state |
|---|---|
| `agent/calculations/yogas/rules.py` | NEW -- all yoga calculations, one module |
| `agent/calculations/jaimini/special_lagnas.py` | NEW -- Bhava / Hora / Ghatika Lagna |
| `agent/calculations/yogas/detector.py` | `_CATALOG` now one entry, `rules.detect` |
| `agent/calculations/yogas/catalog/{raja_yogas,special,neecha_bhanga}.py` | deprecation stubs -- **DELETE THESE** |
| `reference/oracle_fixtures/sulabh.md` | 10c added -- JHora Yogas tab, 16 rows |

`tests/fixtures/jhora_sulabh.md` can now be deleted -- its 7 yoga table is
migrated to `sulabh.md` 10c. **BEFORE deleting**, re-point `SESSION_LOG.md:139`,
which cites that filename as the Pancha Mahapurusha real-chart oracle.

---

## 2. WHAT COMPLETED, AND WHAT THE ORACLE SAYS

Everything below was computed from BIRTH DETAILS ONLY
(`"Sulabh", "6 Apr 1988", "00:30", "Calcutta, India"`) and compared to
`reference/oracle_fixtures/sulabh.md` AFTERWARDS. No oracle value is an input.

### 2a. MATCHES THE ORACLE

| what | computed | oracle | delta |
|---|---|---|---|
| Bhava Lagna | Capricorn 6.9341 | Capricorn 6.9375 (3f) | 12" |
| Hora Lagna | Libra 22.1378 | Libra 22.1389 (3f) | 4" |
| Ghati Lagna | Pisces 7.7489 | Pisces 7.7429 (3f) | 21" |
| Chara Karakas | 8 of 8 | 9a | exact |
| D9 signs | 9 of 9 | 3f Navamsa column | exact |

**15 of 16 yogas in 10c fire**, giver planets matching where the oracle
prints them: Vesi, Nipuna, Sunaphaa, Adhi, Daama/Daamini, Kalpadruma,
Harsha, Raja/Dharma-Karmadhipati, Raja (AK-PiK), Yogada x4 (Su/Me/Ju/Sa),
Vipareeta 6th-8th lord link, Raja Sambandha.

### 2b. DOES **NOT** MATCH -- AND IS CORRECT NOT TO

**JHora's "Viparita Raja Yoga (Mo) -- 8th lord in 6th or 12th" does not fire
here, by design.** PVR p.145 defines Sarala as **the 8th lord in the 8th
house**. Sulabh's 8th lord (Moon) is in the 12th, so PVR's Sarala is absent.
JHora reports a DIFFERENT definition under the same family name. Per the
project's spec-source convention (PVR for the formula, JHora to check the
answer) PVR wins and the divergence is RECORDED, not reconciled -- same
disposition as the Drik Bala AstroSage-vs-JHora divergence.

**CONSEQUENCE, NOT YET DONE:** the rule id is still `sarala_yoga` but it now
computes PVR's Sarala, while the 6th-8th link it used to compute lives at
`vipareeta_6_8_link`. The id is fine; the STALE part is that S131's
`_VIPAREETA` targets were inverted (see 3 below). Rename only if it
confuses -- do not "fix" the definition back.

### 2c. NOT VERIFIED IN EITHER DIRECTION

**JHora prints only yogas it FINDS.** Every not-fired verdict is therefore
unverified: Gajakesari, Vimala, PVR-Sarala, and the six kendra-trikona pairs.
Proving a "no" needs a chart where JHora prints that yoga. **Surbhi is the
obvious second chart** -- `surbhi.md` has no Yogas tab yet; ask Sulabh to paste
it.

---

## 3. FORMULA CORRECTIONS MADE THIS SESSION (all from PVR, with pages)

S131's yoga formulas came from JHora's on-screen "Brief definition" text.
S132 re-sourced all of them from
`data/pdfs/Vedic Astrology_ PVR Narashimha Rao.pdf`. Four were wrong:

1. **THE VIPAREETA FAMILY WAS INVERTED.** PVR p.145: Harsha = 6th lord in the
   **6th**; Sarala = 8th lord in the **8th**; Vimala = 12th lord in the
   **12th**. S131 coded "the dusthana lord in one of the OTHER TWO dusthanas",
   citing Uttara Kalamrita, and locked that as a contested definition.
   **PVR is the primary spec source and says OWN HOUSE.** The S131 lock's
   framing was backwards; Harsha now fires for Sulabh, matching JHora.
2. **Raja Yoga was missing an association.** PVR p.146 names THREE:
   conjunction, graha drishti, and **parivartana (exchange)**. S131 had the
   first two. The third is now implemented -- it would have silently missed
   raja yogas on other charts.
3. **Nipuna** -- PVR p.126 is "Sun and Mercury together (in one sign)".
   "Mutual 7ths" is JHora screen text, not in the spec. Removed.
4. **Kalpadruma** -- PVR p.140 is "quadrants, trines or exaltation signs".
   Own sign is not in the spec. Removed.

**Yogada CONFIRMED as coded** -- PVR p.179: "If a planet aspects or conjoins
or owns GL and lagna, it becomes a yogada."

**Adhi: AMBIGUOUS IN PVR, SETTLED BY THE ORACLE, do not re-litigate.** See the
docstring on `_adhi` in `rules.py` -- PVR's definition and its own worked
example disagree; JHora fires with the 8th from the Moon empty, so the loose
reading is adopted and the giver set matches planet-for-planet.

**NOT DONE: BPHS itself was never opened.** Only PVR was read. `BPHS - 1/2
RSanthanam.pdf` cross-check is outstanding for all 15.

---

## 4. PENDING, IN SUGGESTED ORDER

1. **TESTS. There are none.** `tests/calculations/yogas/` holds only
   `test_pancha_mahapurusha.py`. Nothing covers `detector.py`,
   `rules.py` or `special_lagnas.py`. The suite cannot catch a regression in
   any of it, and "suite unchanged" in S131/S132 means nothing as a result.
2. **Wire yogas to the answer path.** Nothing consumes `detect_yogas` yet.
   `pipeline._fact_block` widening REQUIRES the matching
   `capability_gate.FACT_BLOCK_PROVIDES` key in the SAME change (growth
   contract; `tests/astro/test_capability_gate.py` pins them). **The planner
   selects chapters from the QUESTION, never from the FACTS** -- so a fired
   yoga does not pull its doctrine chapter into the payload. Decide that
   before wiring, not after.
3. `pancha_mahapurusha.py` is BUILT and in no catalogue -- `_CATALOG` never
   calls it. It takes degree-level placements and its own dataclasses, which
   is why S132 did not merge it into `rules.py`. Wire or adapt deliberately.
4. Restate `chart_calculator._calc_yogas` (`mangal_dosha`, `kalsarpa_yoga`)
   into Path B by RESTATEMENT, never by importing the calculator (S20).
5. Delete the three `catalog/` stubs and `tests/fixtures/jhora_sulabh.md`
   (re-point `SESSION_LOG.md:139` first).
6. Second chart for the ruled-out direction (2c).
7. BPHS cross-check (3).
8. The wider BPHS yoga set beyond JHora's 16 -- **Sulabh's explicit
   instruction: not until the 16 are done and validated.**

---

## 5. PROCESS FAILURES OF S132 -- READ THIS, IT COST MOST OF A SESSION

Each is now a KNOWN_PATTERNS row. They are listed here because every one was
caught by Sulabh, not by me.

- **P-026 READ THE PLAN BEFORE THE HANDOVER.** S132 answered from
  `claude_handover_S131.md` repeatedly and had to retract each time as older,
  more authoritative sources surfaced. The Master Build Plan settled in one
  grep what four exchanges could not. **Order: build plan -> locks ->
  KNOWN_PATTERNS -> code -> handover.**
- **P-027 ORACLE DATA IS NEVER AN INPUT.** S132 read Ghati Lagna out of
  `sulabh.md` 3f, fed it into the yoga calculations, then "validated" the
  result against the same file and reported 16/16. Circular; the honest
  figure was 12/16. **Compute from birth details ONLY, then compare.**
- **P-028 THE FORMULA COMES FROM THE SPEC SOURCE, THE ORACLE ONLY CHECKS.**
  S131 and S132 both took yoga formulas from JHora's on-screen definition
  text, so JHora supplied the formula AND graded the answer. PVR/BPHS give
  the formula; JHora/AstroSage grade it. Same split as every other module.
- **P-029 NO DOCTRINE PROSE IN CALCULATION MODULES.** A sentence of doctrine
  in code is a FRAGMENT standing in for a whole chapter: it reads as
  authoritative, so nothing goes back for the rest, and the chapter's own
  conditions never reach the reader. It also cannot be verified by the
  silence gate. Calculation modules report placements and separations; the
  corpus says what they mean.

Two more, not worth their own rows:

- **Do not ship two contradictory results to defer a decision.** S132 emitted
  a strict Harsha AND a wide Harsha rather than resolving the conflict. That
  is not neutrality -- the answer layer would have told the user both. Read
  the spec source and pick.
- **Palm vocabulary does not belong here.** "Rule", "rule condition",
  "rules table" are the palm track's. Astrology has CALCULATIONS with
  FORMULAS from a SPEC SOURCE. The palm rules-table architecture exists
  because GPT-4o-mini could not judge hedged Cheiro prose (S71); astrology
  has a working retrieval-grounded path and needs none of it.

---

## 6. WORKING PROTOCOL (Sulabh's, unchanged)

- Expert-to-expert. **Work silently; reply very briefly, in layman terms.**
- **You do the coding.** Write files into the repo and name the path.
- **REVIEW before PROCEED. SURGICAL EDITS. One prompt, one task.**
- **Commits are Sulabh's** -- never commit source without the literal line
  `RATIFIED: commit authorized`. Docs/diagnostics commits are exempt.
- Every codebase claim carries **branch + commit SHA**, or say you did not
  read it. "X does not exist" is only sayable as "X not found in \<paths\> on
  \<branch\>@\<sha\>".
- **A contradiction from Sulabh is a STOP signal** -- re-verify the SOURCE.
  S132 hit this five times and he was right every time.
- State the recommended model as the first line of every Claude Code prompt.
