# Read Prompt

#Paste your instructions here. Then tell Claude: Read .claude/read_prompt.md and execute


Model: Sonnet 4.6 (multiple files, structural edits)

READ-ONLY for session log; write access for CLAUDE.md, KNOWN_DIVERGENCES.md.

Prerequisites:
- Confirm git log origin/main..HEAD --oneline empty at start
- HEAD == 2e34788

Task 1 — Update docs/KNOWN_DIVERGENCES.md (draft was prepared in previous
Code run, saved from diagnostics/latest_run.md content):
- Reframe Gap D1 with Kapoor citation: change root-cause framing from 
  "mechanism unresolved" to "Camp Y (formal mathematical astrology, 
  Kapoor Institute of Astrology textbook Ch IX pp 115-117) vs Camp X 
  (commercial software JHora/AstroSage/Drik applying undocumented Moon 
  correction). Production aligns with Camp Y. Reopen if evidence of 
  classical primary-source correction surfaces."
- Add Kapoor book reference: 
  project_files/classical_references/_Deepak_Kapoor__Astronomy_and_
  Mathematical_Astrology_text.pdf, Ch IX for Vimshottari, Ch XVI-XIX 
  for Shadbala/Bhava Bala
- All other gaps (D2 Pratyantar, A1 True Chitra, G1 Rahu/Ketu drishti, 
  S1 Saptavargaja, S2 Drekkana Bala, N1 nakshatra reference frame) 
  retain prior framing from earlier draft

Task 2 — Update CLAUDE.md:
- Under "Primary Spec Sources" section: add Kapoor book alongside PVR:
  "PVR (BPHS-tradition) and Kapoor (Institute of Astrology, Bharatiya 
  Vidya Bhavan, mathematical exposition). Kapoor for Vimshottari math, 
  Shadbala (Ch XVI-XIX), Bhava Bala, ayanamsa 1900+ table. PVR remains 
  authoritative for interpretive doctrine and yoga detection."
- Under "Known Divergences": already added in previous Code run — verify

Task 3 — Update SESSION_LOG.md with S75 close block:
  ## S75 — Vimshottari row-0 gap investigation + Ayanamsa lead closure
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
    Non-linear scaling → falsifies both linear-reference-frame and 
    fixed-angular-offset hypotheses. Seasonal pattern (spring births 
    higher residual) suggests apparent-Moon convention divergence.
  - Camp Y / Camp X split identified:
    Camp Y (formal math): Kapoor textbook, Prokerala, our production
    Camp X (commercial):  JHora GUI, AstroSage, Drik Panchang
  - Accepted gap D1 logged. V1 ship decision: RATIFIED (range-based 
    answers unaffected, day-precision predictions excluded from V1 
    scope).
  - Kapoor book added to project_files/classical_references/. Format: 
    plaintext OCR (7385 lines). Highest priority additions: Ch IX 
    (Vimshottari), Ch XVI-XIX (Shadbala/Bhava Bala), Ch IV ayanamsa 
    table.
  - Canonical oracle reclassification: JHora primary for non-dasha 
    (Ashtakavarga, karakas, D-charts, Panchanga); Drik primary for 
    dasha row-0/AD boundaries going forward. AstroSage secondary parity.
  - Fixtures NOT re-captured under Traditional Lahiri this session — 
    tracked as S76 open item.

  Ratifications:
  1. Camp Y alignment as V1 position (Kapoor as anchor citation)
  2. Kapoor book added to project_files/classical_references
  3. Accepted gap register (docs/KNOWN_DIVERGENCES.md) committed
  4. JHora → Drik oracle reclassification for dasha

  Open items S76:
  - Ship year_days = 365.256363 to production (surgical, ratified twice)
  - Re-capture Traditional Lahiri Vimshottari MD tables to 
    tests/fixtures/jhora_{surbhi,sheridan,david}.md (Sulabh already 
    captured this session)
  - Kapoor RAG indexing (extend ChromaDB corpus 14 → 15 texts)
  - Kapoor-based Shadbala refactor evaluation (may resolve S1/S2 gaps)

  Carry-forward (unchanged from S74/S75 open):
  - _keyword_hits word-boundary regex refactor
  - .claude/read_prompt.md working-tree drift
  - scripts/probe_neutral_chunk_valence.py untracked
  - ~0.68d Yogini row-0 offset (S72 origin) — same class as Vimshottari 
    row-0 residual, likely folds into Camp Y position

Task 4 — Commit sequence (three commits, ratified this session):
  1. docs(divergences): add KNOWN_DIVERGENCES.md with S75 accepted gaps
  2. docs(spec): add Kapoor book reference in CLAUDE.md, add book to 
     project_files/classical_references/
  3. docs(session): S75 close block in SESSION_LOG.md

Do NOT push. Full suite run + push happens after review.
Write full command output + git status to diagnostics/latest_run.md.