# Known Divergences — Accepted Gaps Register

Production maintains documented divergences from commercial Vedic
oracles (Drik Panchang, AstroSage, JHora) and classical primary sources
where either (a) sources genuinely fragment, or (b) mechanism is
unresolved but impact on V1 scope is bounded. This register consolidates
those gaps in one place, cross-referenced against the codebase and
diagnostic files where each was established.

Reopen individual gaps when: expert consultation clarifies mechanism,
or V2 scope expansion makes the gap user-visible.

---

## Category 1 — Dasha timing

### Gap D1: Vimshottari row-0 matched-mode residual

- **Symptom:** production row-0 (Mahadasha-1) end date differs from
  Drik/AstroSage/JHora by 0.3-2.8 days.
- **Measured residuals** (matched Traditional Lahiri mode, Drik as
  oracle): Sulabh -2.67d, Sheridan -1.93d, Surbhi -0.33d, David -0.54d.
  *(Provenance flag: Sulabh's number is close to but not identical to
  this session's own JHora-oracle measurement of -2.7726d/-2.7642d;
  the Sheridan/Surbhi/David figures and the Drik-Panchang comparison
  have not been independently verified against any fixture in this
  repository as of this entry — see the diagnostics `latest_run.md`
  companion to this commit for the verification trail.)*
- **Root cause hypothesis:** pyswisseph produces true apparent Moon
  (default with light-time + aberration + nutation). Drik/AstroSage/JHora
  apparently use a Moon variant with different apparent-position
  handling — likely aberration removal or a traditional
  lunar-table-derived Moon. Confirmed via `FLG_NOABERR` test: closes
  68.6% of Sulabh's gap (against the JHora oracle) but sign varies by
  birth month.
- **Amplification:** fixed offset, does NOT compound through
  Antardasha/Pratyantar (ratio math preserves durations).
- **Impact on V1:** zero for range-based answers, palm reading,
  AstroSage paragraphs, Kuta compatibility, T3 Muhurta.
- **Expert question:** what Moon variant do Drik/AstroSage use for
  dasha calculation specifically (apparent vs true, with or without
  aberration, mean vs true equinox, tradition-specific correction
  constant)?

### Gap D2: Pratyantar dasha suppressed

- **Symptom:** ±37 day drift + wrong lord assignment in prior
  implementation.
- **Root cause:** not investigated at implementation depth; suppressed
  at architecture layer.
- **Impact on V1:** none (Pratyantar Dasha not exposed in V1 scope).
- **Expert question:** is our PD lord ordering formula matching
  classical? Or is drift purely a downstream effect of Gap D1,
  amplified at PD nesting?

---

## Category 2 — Ayanamsa

### Gap A1: pyswisseph SIDM_TRUE_CITRA vs JHora True Chitrapaksha

- **Symptom:** 20.26″ (Sulabh), 15.07″ (Sheridan) delta under
  mode-matched True Chitra.
- **Root cause hypothesis:** pyswisseph's True Chitra implementation
  uses a different Spica reference longitude or nutation handling than
  JHora's.
- **Impact on V1:** NONE — production uses `SIDM_LAHIRI` (Traditional
  Lahiri), which matches JHora to 0.14″.
- **Expert question:** only relevant if we ever switch to True Chitra
  doctrine. Which authority's True Chitra is "correct" for classical
  Parashari alignment?

---

## Category 3 — Graha drishti

### Gap G1: Rahu/Ketu aspects = (5, 7, 9)

- **Symptom:** classical sources fragment on the nodes' aspects. Some
  texts: no drishti for nodes. Others: (5, 7, 9), same as Jupiter.
  Others: (3, 7, 10), Saturn-like.
- **Root cause:** genuine classical divergence, not a calculation error.
- **Ratified:** user-perceived correctness (AstroSage/Prokerala/Drik
  alignment) → (5, 7, 9) chosen.
- **Impact on V1:** affects yoga detection where nodes cast aspects.
- **Expert question:** which primary classical source (BPHS
  chapter/verse, Phaladeepika, Saravali) explicitly defines Rahu/Ketu
  drishti? Currently our tiebreaker was "match commercial oracles" — a
  classical citation would let us upgrade the documentation from
  tiebreaker-based to source-based.

---

## Category 4 — Shadbala

### Gap S1: Saptavargaja Bala — Path A (BPHS literal) vs AstroSage

- **Symptom:** AstroSage fixture values differ from BPHS-literal Path A
  implementation.
- **Root cause:** AstroSage may apply a post-BPHS correction
  (Phaladeepika, Uttarakalamrita, or modern commentary tradition).
- **Ratified:** Path A (BPHS literal); AstroSage values informational
  only, not oracle.
- **Impact on V1:** affects career-strength answers (10th lord
  Shadbala) with unknown magnitude across the 4 canonical charts.
- **Expert question:** does the tradition the user consults locally
  follow BPHS literal or a specific commentary variant? If
  commentary-based, which one?

### Gap S2: Drekkana Bala = 1 Virupa fixed constant

- **Symptom:** classical BPHS gives a formula; both AstroSage and JHora
  converge on a constant 1 Virupa for all planets.
- **Ratified:** 1 Virupa (matches both oracles).
- **Root cause hypothesis:** convergent modern simplification.
- **Impact on V1:** minor, affects total Shadbala tallies.
- **Expert question:** is the classical formula ever actually used, or
  has tradition uniformly adopted the 1-Virupa simplification?

---

## Category 5 — Nakshatra / Panchanga

### Gap N1: Nakshatra reference frame

- **Symptom:** we equal-divide from 0° sidereal Aries; some traditions
  anchor on the yoga-tara of Ashwini.
- **Root cause:** convention choice, arcsec-scale offset.
- **Impact:** not measured; likely absorbed into Gap D1.
- **Expert question:** does tradition demand yoga-tara anchoring, or is
  0° Aries anchoring canonical for Parashari?
