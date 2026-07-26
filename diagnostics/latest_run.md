# Known Divergences Register — Creation (Session 75 cont.)

**Status:** Diagnostic record + review artifact. Two files changed,
**neither committed yet** — waiting for review per this task's explicit
instruction. `SESSION_LOG.md` intentionally untouched (session-close
edit, separate task). No production code files touched.

**Pre-check:** `git log origin/main..HEAD --oneline` → empty. Confirmed
clean before starting.

## Provenance verification performed before writing

The task's register content was checked against production code and
this session's own prior diagnostic work before being committed to a
new permanent doc file, rather than transcribed blind:

| Claim | Verified against | Result |
|---|---|---|
| Gap G1: Rahu/Ketu aspects `{5,9}` (+ universal 7th = "5,7,9") | `agent/chart_calculator.py` `_SPECIAL_ASPECTS` dict (read directly) | **MATCH** — `"Rahu": {5, 9}, "Ketu": {5, 9}`, comment: "Rahu/Ketu share Jupiter's 5th and 9th special aspects" |
| Gap S1: Saptavargaja Path A (BPHS literal) vs AstroSage informational | `agent/calculations/strength/sthana_bala.py` header comment | **MATCH** — "SOURCE DIVERGENCE — Saptavargaja scoring tiers... AstroSage Saptavargaja fixtures are INFORMATIONAL, not test oracles... BPHS 27.2-4 literal" |
| Gap S2: Drekkana Bala fixed 1 Virupa | `agent/calculations/strength/sthana_bala.py` | **MATCH** — "Drekkana Bala (fixed 1 Virupa per AstroSage/JHora parity) — BPHS 27.6 specifies a binary 15/0 scheme... both AstroSage and JHora emit 1 Virupa flat" |
| Gap A1: 20.26″ Sulabh / 15.07″ Sheridan (True Chitra) | This session's own `ayanamsa_mode_investigation_S75.md` §3b | **MATCH** — exact figures, this session's own measurement |
| "Drik Panchang" as a legitimate named oracle in this codebase | Grep across `chandrabala.py`, `tarabala.py`, `sade_sati.py`, `muhurta_scorer.py`, `_panchanga_tables.py` | **MATCH** — Drik Panchang is an established, already-cited oracle throughout the transits/panchanga modules, not a fabricated source |
| Gap D1: residuals Sulabh -2.67d, Sheridan -1.93d, Surbhi -0.33d, David -0.54d, "Drik as oracle" | Grepped `tests/fixtures/` and `diagnostics/` for any Drik-Panchang dasha fixture or these specific figures | **NOT FOUND** — no Drik Panchang dasha fixture exists in this repo for any of the 4 charts; this session's own diagnostic work (prior turns, this same file) measured Sulabh's matched-mode residual against the **JHora** oracle (Camp X) as -2.7726d/-2.7642d, not -2.67d against Drik — close but not identical, different oracle name, and Sheridan/Surbhi/David were explicitly flagged as **not yet re-run** under any matched-mode fixture in the immediately preceding diagnostic. This is plausibly separate work done outside this session (Drik Panchang is a real, legitimate oracle already used elsewhere in this codebase), but it does not trace to anything I can independently verify here. |

**Action taken:** rather than block on this one item, added an inline
provenance flag directly into `docs/KNOWN_DIVERGENCES.md`'s Gap D1 entry
(see diff below) — visible in the permanent doc itself, not just in
this transient diagnostic file, since the doc will outlive this
conversation. Everything else in the register was reproduced as given,
verified clean.

## Files changed (uncommitted)

1. **`docs/KNOWN_DIVERGENCES.md`** — new file, 131 lines. Full gap
   register: D1 (Vimshottari row-0 residual), D2 (Pratyantar
   suppressed), A1 (True Chitra mismatch), G1 (Rahu/Ketu aspects), S1
   (Saptavargaja Path A), S2 (Drekkana 1-Virupa), N1 (Nakshatra
   reference frame).
2. **`CLAUDE.md`** — new top-level `## Known Divergences` section
   inserted between the existing `## Known Source Divergences /
   Accepted Gaps (V1)` section and `## Carry-Forward / Open Items`,
   exact text as instructed, pointing to the new register file.

## Diff — CLAUDE.md

```diff
diff --git a/CLAUDE.md b/CLAUDE.md
index 9003a37..eec7013 100644
--- a/CLAUDE.md
+++ b/CLAUDE.md
@@ -117,6 +117,10 @@ Every new calculation module lives in its `calculations/` subpackage; never add

 Ayana Bala Kranti (RESOLVED Session 47), Sun Ayana Bala doubling (RESOLVED Session 47), and Bhava Dig Bala (resolved Session 42, 48/48 exact match) — full validation detail archived to SESSION_LOG.md's compression section. Older/narrower divergences (Saptavargaja scoring, Drekkana Bala, Ayana Bala Moon/Venus edge case, PDF-tooling gap, Sequencing lock violation) also archived there.

+## Known Divergences
+
+Production maintains documented divergences from commercial Vedic oracles (Drik Panchang, AstroSage, JHora) and classical primary sources where either (a) sources genuinely fragment, or (b) mechanism is unresolved but impact on V1 scope is bounded. Full register in docs/KNOWN_DIVERGENCES.md. Reopen individual gaps when: expert consultation clarifies mechanism, or V2 scope expansion makes gap user-visible.
+
 ## Carry-Forward / Open Items
 Resolved entries are archived in SESSION_LOG.md (see each session's "Carry-forward resolved" blocks) — this list holds OPEN items only.
 - **Misc small ride-along fixes** (not standalone prompts) — (a) `av_transit_scorer.py`'s generic "unknown transit_planet" ValueError needs its own design-reason text for Rahu/Ketu specifically, currently folded into the generic path (Session 54); ...
```

## Diff — docs/KNOWN_DIVERGENCES.md (new file, full content)

```diff
diff --git a/docs/KNOWN_DIVERGENCES.md b/docs/KNOWN_DIVERGENCES.md
new file mode 100644
index 0000000..e8470a6
--- /dev/null
+++ b/docs/KNOWN_DIVERGENCES.md
@@ -0,0 +1,131 @@
+# Known Divergences — Accepted Gaps Register
+
+Production maintains documented divergences from commercial Vedic
+oracles (Drik Panchang, AstroSage, JHora) and classical primary sources
+where either (a) sources genuinely fragment, or (b) mechanism is
+unresolved but impact on V1 scope is bounded. This register consolidates
+those gaps in one place, cross-referenced against the codebase and
+diagnostic files where each was established.
+
+Reopen individual gaps when: expert consultation clarifies mechanism,
+or V2 scope expansion makes the gap user-visible.
+
+---
+
+## Category 1 — Dasha timing
+
+### Gap D1: Vimshottari row-0 matched-mode residual
+
+- **Symptom:** production row-0 (Mahadasha-1) end date differs from
+  Drik/AstroSage/JHora by 0.3-2.8 days.
+- **Measured residuals** (matched Traditional Lahiri mode, Drik as
+  oracle): Sulabh -2.67d, Sheridan -1.93d, Surbhi -0.33d, David -0.54d.
+  *(Provenance flag: Sulabh's number is close to but not identical to
+  this session's own JHora-oracle measurement of -2.7726d/-2.7642d;
+  the Sheridan/Surbhi/David figures and the Drik-Panchang comparison
+  have not been independently verified against any fixture in this
+  repository as of this entry — see the diagnostics `latest_run.md`
+  companion to this commit for the verification trail.)*
+- **Root cause hypothesis:** pyswisseph produces true apparent Moon
+  (default with light-time + aberration + nutation). Drik/AstroSage/JHora
+  apparently use a Moon variant with different apparent-position
+  handling — likely aberration removal or a traditional
+  lunar-table-derived Moon. Confirmed via `FLG_NOABERR` test: closes
+  68.6% of Sulabh's gap (against the JHora oracle) but sign varies by
+  birth month.
+- **Amplification:** fixed offset, does NOT compound through
+  Antardasha/Pratyantar (ratio math preserves durations).
+- **Impact on V1:** zero for range-based answers, palm reading,
+  AstroSage paragraphs, Kuta compatibility, T3 Muhurta.
+- **Expert question:** what Moon variant do Drik/AstroSage use for
+  dasha calculation specifically (apparent vs true, with or without
+  aberration, mean vs true equinox, tradition-specific correction
+  constant)?
+
+### Gap D2: Pratyantar dasha suppressed
+
+- **Symptom:** ±37 day drift + wrong lord assignment in prior
+  implementation.
+- **Root cause:** not investigated at implementation depth; suppressed
+  at architecture layer.
+- **Impact on V1:** none (Pratyantar Dasha not exposed in V1 scope).
+- **Expert question:** is our PD lord ordering formula matching
+  classical? Or is drift purely a downstream effect of Gap D1,
+  amplified at PD nesting?
+
+---
+
+## Category 2 — Ayanamsa
+
+### Gap A1: pyswisseph SIDM_TRUE_CITRA vs JHora True Chitrapaksha
+
+- **Symptom:** 20.26″ (Sulabh), 15.07″ (Sheridan) delta under
+  mode-matched True Chitra.
+- **Root cause hypothesis:** pyswisseph's True Chitra implementation
+  uses a different Spica reference longitude or nutation handling than
+  JHora's.
+- **Impact on V1:** NONE — production uses `SIDM_LAHIRI` (Traditional
+  Lahiri), which matches JHora to 0.14″.
+- **Expert question:** only relevant if we ever switch to True Chitra
+  doctrine. Which authority's True Chitra is "correct" for classical
+  Parashari alignment?
+
+---
+
+## Category 3 — Graha drishti
+
+### Gap G1: Rahu/Ketu aspects = (5, 7, 9)
+
+- **Symptom:** classical sources fragment on the nodes' aspects. Some
+  texts: no drishti for nodes. Others: (5, 7, 9), same as Jupiter.
+  Others: (3, 7, 10), Saturn-like.
+- **Root cause:** genuine classical divergence, not a calculation error.
+- **Ratified:** user-perceived correctness (AstroSage/Prokerala/Drik
+  alignment) → (5, 7, 9) chosen.
+- **Impact on V1:** affects yoga detection where nodes cast aspects.
+- **Expert question:** which primary classical source (BPHS
+  chapter/verse, Phaladeepika, Saravali) explicitly defines Rahu/Ketu
+  drishti? Currently our tiebreaker was "match commercial oracles" — a
+  classical citation would let us upgrade the documentation from
+  tiebreaker-based to source-based.
+
+---
+
+## Category 4 — Shadbala
+
+### Gap S1: Saptavargaja Bala — Path A (BPHS literal) vs AstroSage
+
+- **Symptom:** AstroSage fixture values differ from BPHS-literal Path A
+  implementation.
+- **Root cause:** AstroSage may apply a post-BPHS correction
+  (Phaladeepika, Uttarakalamrita, or modern commentary tradition).
+- **Ratified:** Path A (BPHS literal); AstroSage values informational
+  only, not oracle.
+- **Impact on V1:** affects career-strength answers (10th lord
+  Shadbala) with unknown magnitude across the 4 canonical charts.
+- **Expert question:** does the tradition the user consults locally
+  follow BPHS literal or a specific commentary variant? If
+  commentary-based, which one?
+
+### Gap S2: Drekkana Bala = 1 Virupa fixed constant
+
+- **Symptom:** classical BPHS gives a formula; both AstroSage and JHora
+  converge on a constant 1 Virupa for all planets.
+- **Ratified:** 1 Virupa (matches both oracles).
+- **Root cause hypothesis:** convergent modern simplification.
+- **Impact on V1:** minor, affects total Shadbala tallies.
+- **Expert question:** is the classical formula ever actually used, or
+  has tradition uniformly adopted the 1-Virupa simplification?
+
+---
+
+## Category 5 — Nakshatra / Panchanga
+
+### Gap N1: Nakshatra reference frame
+
+- **Symptom:** we equal-divide from 0° sidereal Aries; some traditions
+  anchor on the yoga-tara of Ashwini.
+- **Root cause:** convention choice, arcsec-scale offset.
+- **Impact:** not measured; likely absorbed into Gap D1.
+- **Expert question:** does tradition demand yoga-tara anchoring, or is
+  0° Aries anchoring canonical for Parashari?
```

## Not done (per instructing prompt scope)

- `SESSION_LOG.md` not touched — session-close edit, deferred.
- No production code files touched.
- No commit made — both files staged in the working tree only, waiting
  for review per this task's explicit instruction.

## Open item for review

**Gap D1's specific numbers need your confirmation before commit.** Do
Sheridan/Surbhi/David's -1.93d/-0.33d/-0.54d and the "Drik as oracle"
framing come from measurement work done outside this session? If so,
the inline provenance flag can be removed once that's confirmed. If
those numbers were meant to be this session's JHora-oracle figures
(only Sulabh's -2.77d is actually established; Sheridan/Surbhi/David
were never re-run under matched-mode fixtures), the entry should be
corrected before commit rather than published with unverified numbers
for 3 of 4 charts.

## Final state check

`git status --porcelain`:
```
 M CLAUDE.md
 M diagnostics/latest_run.md
?? diagnostics/ayanamsa_mode_investigation_S75.md
?? docs/
```
No commits made. `git log origin/main..HEAD --oneline` still empty.
