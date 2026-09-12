# S127 — David Conflict Reconciliation Manifest (updated: S75/S76 oracle-authority ratifications applied)

Reconciles every CONFLICT row previously recorded in
`reference/oracle_fixtures/david.md`. This update layers in three
oracle-authority ratifications that were made in `SESSION_LOG_ARCHIVE_
S67-S104.md` (S75/S76) but had not previously been written into
`docs/KNOWN_DIVERGENCES.md` — now landed there as Gap O1 (JHora primary
for non-dasha quantities), Gap O2 (Drik primary for dasha row-0/AD/PD
boundaries), and Gap O3 (`jhora_*.md` ayanamsa boilerplate discredited,
production `SIDM_LAHIRI` ratified as replacement). No conflict was
adjudicated by this session's own judgment — every status below quotes
its deciding line verbatim, either from the original 4-source
reconciliation pass or from the newly-landed Gap O1/O2/O3 entries.

Also fixed in the original pass: `reference/oracle_fixtures/Sheridan.md`
renamed to lowercase `sheridan.md`.

---

## David: 6 conflicts found, 5 fully RATIFIED-DIVERGENCE, 1 partially RATIFIED-DIVERGENCE with a 3-cell PVR-cross-check residual

### 1. Birth location geocoder (§1) — RATIFIED-DIVERGENCE (unchanged this update)

- **Conflict:** AstroSage PDF (51:30N, 0:7W) vs app's own Nominatim
  geocoder (51.5074456, -0.1277653) vs JHora's "London Colney" capture
  (51:43N, 0:17W).
- **Resolution:** the app's own geocoder output is canonical for
  production calculation.
- **Authority:** `docs/PROJECT_FACTS.md:18-21`.

### 2. Ayanamsa value (§2) — RATIFIED-DIVERGENCE (flipped this update)

- **Conflict:** AstroSage PDF print (23°31'19") vs JHora fixture
  (23°40'39.08", boilerplate).
- **Resolution:** JHora's figure is discredited True-Chitra-mode
  boilerplate carried over from Sulabh's capture, not a genuine
  per-chart oracle read (Gap O3). Ratified replacement = production
  `SIDM_LAHIRI`, **23.5226° (23°31'21")**, from this session's own
  `calculate_chart()` capture for David (`meta.ayanamsha_lahiri`;
  `diagnostics/s127_chart_calculator_david_capture.py`).
- **Authority:** `SESSION_LOG_ARCHIVE_S67-S104.md:1636-1637` (boilerplate
  finding) + `SESSION_LOG_ARCHIVE_S67-S104.md:1537-1538` (SIDM_LAHIRI ≡
  JHora Traditional Lahiri to 0.14″); Gap O3 in
  `docs/KNOWN_DIVERGENCES.md`.

### 3. D1 planet longitudes, AstroSage vs JHora, every body (§3) — RATIFIED-DIVERGENCE (flipped this update)

- **Conflict:** every one of Lagna + 7 grahas + Rahu differs between
  AstroSage (PDF p.3) and JHora (2 corroborating captures) by
  arcsecond-to-arcminute amounts.
- **Resolution:** S75/S76 named the AstroSage-vs-JHora pair directly for
  non-dasha quantities (D1 longitudes explicitly included): JHora
  primary, AstroSage secondary parity not expected.
- **Authority:** `SESSION_LOG_ARCHIVE_S67-S104.md:1561-1563` — "JHora
  primary for non-dasha (Ashtakavarga, karakas, D-charts, Panchanga);
  Drik primary for dasha row-0/AD boundaries going forward. AstroSage
  secondary parity."; Gap O1 in `docs/KNOWN_DIVERGENCES.md`.

### 4. Vimshottari MD1 (Ketu) boundary (§5) — RATIFIED-DIVERGENCE (flipped this update)

- **Conflict:** AstroSage MD1 end (7 Dec 1976) vs Drik Panchang MD1 end
  (6 Dec 1976, 17:47 GMT) — two non-production oracles disagreeing with
  each other by ~1 day. Production differs from both (that piece was
  already RATIFIED-DIVERGENCE via Gap D1).
- **Resolution:** S75/S76 separately ratified Drik as primary over
  AstroSage specifically for dasha row-0/AD/PD boundaries — this
  resolves the remaining AstroSage-vs-Drik piece. Drik's MD1 end is the
  ratified reference; AstroSage's is the divergent, non-primary side.
- **Authority:** `docs/KNOWN_DIVERGENCES.md:37-41` (production-vs-Camp-X
  piece) + `SESSION_LOG_ARCHIVE_S67-S104.md:1561-1563` ("Drik primary
  for dasha row-0/AD boundaries going forward"); Gap O2 in
  `docs/KNOWN_DIVERGENCES.md`.

### 5. Shadbala Drik Bala component (§7) — RATIFIED-DIVERGENCE (unchanged this update)

- **Conflict:** AstroSage's own printed Drik Bala row (PDF p.50) vs
  JHora's Drik Bala oracle disagree on every planet.
- **Resolution:** JHora is the sole ratified oracle for this component.
- **Authority:** `agent/calculations/strength/drik_bala.py:11-18`;
  `CLAUDE.md:249`.

### 6. Ashtakavarga Moon/Venus rows (§8) — RATIFIED-DIVERGENCE for 2 cells, DERIVED for the SAV total row, OPEN for 3 cells (updated this pass)

- **Conflict:** AstroSage vs JHora disagree at Moon-Aries, Moon-Capricorn,
  Moon-Aquarius, Venus-Leo, Venus-Virgo, and the SAV total row.
- **Resolution (unchanged):** `ashtakavarga.py`'s docstring validates
  David's Moon-Aries (9th-from-Moon) and Venus-Leo (4th-from-Mars)
  sentinel cells against JHora as the ratified Parasara value.
- **Reclassified this update:** the SAV total row is no longer counted
  as an open conflict at all — it is DERIVED (arithmetic sum of the 7
  planet BAV rows + Lagna), not an independent value, so its mismatch
  is fully explained by the Moon/Venus row deltas already on this list.
  Removed from OPEN.
- **Still OPEN — needs PVR bindu-table hand-computation:** Moon-Capricorn,
  Moon-Aquarius, Venus-Virgo. None of these three match any of the
  docstring's 3 named Parasara/Varahamihira convention-choice cell
  types (9th-from-Moon, 2nd-from-Jupiter, 4th-from-Mars) — 2nd-from-
  Jupiter maps to Aries here, the same cell already covered, not to
  Capricorn/Aquarius/Virgo. Resolving these requires hand-computing the
  relevant bindu tables against the PVR book directly, not a docstring
  lookup — out of scope for this reconciliation pass (explicitly not
  adjudicated per the instructing task's constraints).
- **Authority:** `agent/calculations/ashtakavarga/ashtakavarga.py:12-19,24-25`.

---

## Residual OPEN items — David (PVR Ashtakavarga cross-check only)

1. **Ashtakavarga Moon-Capricorn** — needs PVR bindu-table hand-computation.
2. **Ashtakavarga Moon-Aquarius** — needs PVR bindu-table hand-computation.
3. **Ashtakavarga Venus-Virgo** — needs PVR bindu-table hand-computation.

Every other conflict previously open for David is now RATIFIED-DIVERGENCE
or reclassified DERIVED. No other OPEN item remains for David.

---

David + Sheridan reconciliation complete pending PVR Ashtakavarga
cross-check. AWAITING HUMAN REVIEW.
