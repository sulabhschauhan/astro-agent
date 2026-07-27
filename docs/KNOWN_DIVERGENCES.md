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
  oracle): Sulabh -2.66d, Sheridan -1.92d, Surbhi -0.33d, David -0.55d.
  *(Provenance closed, S76: all 4 figures independently recomputed via
  `swe.julday()` from Sulabh's verbatim drikpanchang.com capture and
  committed as diagnostic files — `diagnostics/drik_vimshottari_S76_
  {sulabh,surbhi,sheridan,david}.md`, cross-referenced from
  `docs/PROJECT_FACTS.md` §3. Prior provenance flag on this entry — "the
  Sheridan/Surbhi/David figures and the Drik-Panchang comparison have not
  been independently verified against any fixture in this repository" —
  is RESOLVED for these 4 numbers. En route, a stale intermediate quote
  of Sheridan's residual as -1.78d (one prompt prior) was traced and
  ruled a transcription drift, not a re-measurement; -1.92d is the
  verified figure. Sulabh's number remains close to but not identical to
  an earlier same-session JHora-oracle measurement of -2.7726d/-2.7642d
  — expected, since that comparison is against JHora's GUI, a different
  oracle than Drik Panchang; the two are not required to match.)*
- **Root cause:** Camp Y (formal mathematical astrology, Kapoor
  Institute of Astrology textbook Ch IX pp 115-117) vs Camp X
  (commercial software JHora/AstroSage/Drik applying an undocumented
  Moon correction). Production aligns with Camp Y. Reopen if evidence
  of classical primary-source correction surfaces.
  *(Prior working hypothesis, preserved for its diagnostic value:
  pyswisseph produces true apparent Moon — default with light-time +
  aberration + nutation — while Drik/AstroSage/JHora apparently apply a
  different apparent-position handling, likely aberration removal or a
  traditional lunar-table-derived Moon. Confirmed via `FLG_NOABERR`
  test: closes 68.6% of Sulabh's gap against the JHora oracle, but sign
  varies by birth month — consistent with Camp X applying a correction
  not derivable from a single flag toggle.)*
- **Reference:** `data/pdfs/[Deepak Kapoor] Astronomy and Mathematical
  Astrology_text.pdf`, Ch IX (Vimshottari).
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
- **Root cause:** Three-way tier divergence across classical + commercial
  sources. BPHS 27.2-4 literal (production): Mooltrikona=45 / Own=30 /
  Pramudita=20 / Shanta=15 / Din=10 / Duhkhita=4 / Khala=2. Kapoor Ch XIX
  p.226-227 ready reckoner (Raman-scaled variant, Camp Y classical):
  Mooltrikona=45 / Own=30 / Adhi mitra=22.5 / Mitra=15 / Neutral=7.5 /
  Shatru=3.75 / Adhi shatru=1.875. AstroSage (unpublished):
  reverse-engineering fails — Sun fits Adhimitra≈30/Sama≈7.5 but Moon does
  not fit the same table across 4 canonical charts (S30 finding).
- **Ratified:** BPHS literal (production); Kapoor Ch XIX cited as named
  classical support for the Raman-scaled variant existing in Camp Y
  literature; AstroSage values informational only, not oracle. No
  empirical AstroSage-vs-Kapoor delta measurement performed S77 — open
  work item if S1 is ever reopened.
- **Impact on V1:** Expected low, not empirically measured S77. Shadbala
  feeds Yoga detection (P3) and Trigger Naming (P7), both of which consume
  RANKING, not absolute Virupa (see test_sthana_bala.py:263 informational
  comment). Whether ranking is stable across BPHS / Kapoor / AstroSage tier
  schemes for the 4 canonical charts is unverified — logged as open work
  item, not asserted here. Suite is green under current BPHS-literal
  scoring; no tier-swap regression has been run.
- **Reference:** `data/pdfs/[Deepak Kapoor] Astronomy and Mathematical
  Astrology_text.pdf`, Ch XIX p.226-227 (Graha Bala ready reckoner,
  "Unit of strength" 7-tier table).
- **Expert question:** does the tradition the user consults locally
  follow BPHS literal or a specific commentary variant? If
  commentary-based, which one?

### Gap S2: Drekkana Bala = 1 Virupa fixed constant

- **Symptom:** Camp Y unanimous classical (BPHS 27.6 + Kapoor Ch XVI §v +
  Ch XIX p 227) specifies binary 15/0 by planet-gender × decanate. Camp X
  commercial (AstroSage + JHora) converges on 1 Virupa flat for all
  planets. Camp allegiance inconsistency with S77's Camp Y ratification
  for Vimshottari (Gap D1) — production sides Camp X on this component.
- **Ratified:** 1 Virupa (matches Camp X commercial oracles). Not
  re-ratified S77; the S30 lock stands because the impact analysis below
  shows no user-answer effect. Camp allegiance inconsistency logged, not
  fixed.
- **Root cause hypothesis:** Convergent modern simplification in commercial
  software; classical binary scheme preserved in both BPHS and Kapoor
  (mathematical-astrology tradition).
- **Impact on V1:** Not empirically measured S77. Max delta if switched to
  Camp Y binary: ±14 Virupa on a single planet's Sthana total. Sulabh
  Sun-vs-Saturn Shadbala gap is 10.4 Virupa (Sun=412.74, Saturn=423.16
  from shadbala_fixtures.py) — a swap CAN flip that adjacent-rank pair.
  Whether the flip propagates to a user-visible answer change through
  Yoga detection / Trigger Naming consumers is unverified. Logged as open
  work item; the S30 1-Virupa lock is preserved pending measurement, not
  ratified as user-answer-safe.
- **Reference:** `data/pdfs/[Deepak Kapoor] Astronomy and Mathematical
  Astrology_text.pdf`, Ch XVI §v p 192 (Dreshkon bala definition), Ch XIX
  p 227 (ready reckoner).
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
