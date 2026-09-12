# S127 — Surbhi Conflict Reconciliation Manifest

Reconciles every CONFLICT row in `reference/oracle_fixtures/surbhi.md`.
Same format/convention as `manifest_david.md`/`manifest_sulabh.md`. This
file was built fresh this session (no prior pass existed to update).

---

## Surbhi: 4 conflicts found — 3 fully RATIFIED-DIVERGENCE, 1 partial (Ashtakavarga)

### 1. Birth location coordinates (§1) — RATIFIED-DIVERGENCE

- **Conflict:** AstroSage PDF (25:36N, 85:7E) vs app geocoder
  (25.6093239, 85.1235252).
- **Resolution:** app's own Nominatim/OSM geocoder canonical for
  production. Same authority as David/Sulabh's identical-shape conflict.
- **Authority:** `docs/PROJECT_FACTS.md:18-21`.

### 2. D1 planet longitudes, AstroSage vs JHora (§3) — RATIFIED-DIVERGENCE, CLOSED at matched-mode

- **Conflict:** every body differs between AstroSage (PDF p.3) and
  JHora True-Chitra (`test_jaimini_karakas.py` `SURBHI` dict) by
  arcsecond-to-arcminute amounts.
- **Resolution:** matched-mode (Traditional Lahiri) JHora data supplied
  directly this session — §3e now carries the full residual/Camp-Y
  table. Max |Δ| = 53.82″ (Mercury), sub-90″, no FLAG (≥100″)
  triggered. Rahu/Ketu Δ≈-0.14″ confirms Mean-Node convention match
  (consistent with David's and Sulabh's own §3e tables). The external
  ask for a matched-mode capture is CLOSED — this file never carried an
  open external-ask entry to begin with, since §3e was supplied before
  the base file was written (unlike Sulabh's 2-pass history).
- **Authority:** `docs/KNOWN_DIVERGENCES.md:193-198` (Gap O1, source-
  class priority); `reference/oracle_fixtures/surbhi.md` §3e (this
  session's matched-mode residual table).

### 3. Shadbala Drik Bala (§7) — RATIFIED-DIVERGENCE

- **Conflict:** AstroSage's printed Drik Bala row vs JHora's Drik Bala
  oracle disagree on every planet, worst case Saturn (Δ3.10) and
  Jupiter (Δ3.04).
- **Resolution:** JHora is the sole ratified oracle for this component.
- **Authority:** `agent/calculations/strength/drik_bala.py:11-18`;
  `CLAUDE.md` Locked Decisions.

### 4. Ashtakavarga Moon/Venus rows (§8) — RATIFIED-DIVERGENCE for 1 cell, OPEN for 5 cells + total row

- **Conflict:** AstroSage vs JHora disagree at Moon-Cancer, Moon-Virgo,
  Moon-Libra, Moon-Aquarius, Venus-Virgo, Venus-Libra, and the total
  row.
- **Resolution:** `ashtakavarga.py`'s docstring names three
  convention-choice cell types (9th-from-Moon, 2nd-from-Jupiter,
  4th-from-Mars). For Surbhi, all three independently resolve to the
  **same cell** — Moon-Virgo (Moon in Aquarius → 9th = Virgo; Jupiter
  in Leo → 2nd = Virgo; Mars in Gemini → 4th = Virgo) — a genuine
  triple-coincidence unique to this chart's placements, not seen in
  David's or Sulabh's reconciliation. JHora's value (1) ratified over
  AstroSage's (0) for that one cell.
- **Still OPEN — needs PVR bindu-table hand-computation:** Moon-Cancer,
  Moon-Libra, Moon-Aquarius, Venus-Virgo, Venus-Libra. None match a
  named sentinel type for this chart.
- **Authority:** `agent/calculations/ashtakavarga/ashtakavarga.py:12-19,24-25`.

---

## Jaimini karaka scheme — NO conflict found (contrast with Sulabh)

Unlike Sulabh's chart (`manifest_sulabh.md` item 7, a genuine
planet-level disagreement), Surbhi's AstroSage Chara column is a pure
relabeling of JHora's 7-graha assignment under AstroSage's own role
names — full corroboration, no adjudication needed. Recorded in
`surbhi.md` §9 for completeness, not listed as a conflict here.

---

## Residual OPEN items — Surbhi

1. Ashtakavarga Moon-Cancer — needs PVR bindu-table hand-computation.
2. Ashtakavarga Moon-Libra — needs PVR bindu-table hand-computation.
3. Ashtakavarga Moon-Aquarius — needs PVR bindu-table hand-computation.
4. Ashtakavarga Venus-Virgo — needs PVR bindu-table hand-computation.
5. Ashtakavarga Venus-Libra — needs PVR bindu-table hand-computation.

## Data-flag closures (see `surbhi.md`'s own "Data-flag closures" section for full detail)

1. Moon nakshatra mislabel (S74 diagnostic said "Uttara Bhadrapada
   #24", astronomically Shatabhisha) — **RESOLVED**.
2. Combustion "Basics view shows none" — **RESOLVED** (invalidated
   S51; Mercury/Jupiter confirmed deeply combust).
3. Jupiter near the Leo/Virgo boundary (4-4.5 arcmin) — **BOUNDARY-
   SENSITIVE, flagged, not a fix** — sign stays Leo in both matched-mode
   JHora and production today.

---

Surbhi reconciliation complete except for the 5 residual Ashtakavarga
OPEN items above. AWAITING HUMAN REVIEW.
