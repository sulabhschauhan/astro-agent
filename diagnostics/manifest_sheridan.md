# S127 — Sheridan Conflict Reconciliation Manifest (updated: S75/S76 oracle-authority ratifications applied)

Reconciles every CONFLICT row previously recorded in
`reference/oracle_fixtures/sheridan.md`. This update layers in three
oracle-authority ratifications that were made in `SESSION_LOG_ARCHIVE_
S67-S104.md` (S75/S76) but had not previously been written into
`docs/KNOWN_DIVERGENCES.md` — now landed there as Gap O1 (JHora primary
for non-dasha quantities), Gap O2 (Drik primary for dasha row-0/AD/PD
boundaries), and Gap O3 (`jhora_*.md` ayanamsa boilerplate discredited,
production `SIDM_LAHIRI` ratified as replacement). No conflict was
adjudicated by this session's own judgment — every status below quotes
its deciding line verbatim, either from the original 4-source
reconciliation pass or from the newly-landed Gap O1/O2/O3 entries.

Also fixed in the original pass: the file itself was renamed from
`reference/oracle_fixtures/Sheridan.md` to lowercase `sheridan.md`.

---

## Sheridan: 5 conflicts found, 4 fully RATIFIED-DIVERGENCE, 1 partially RATIFIED-DIVERGENCE with a 2-cell PVR-cross-check residual

### 1. Stale reused ayanamsa value (§2) — RATIFIED-DIVERGENCE (flipped this update)

- **Conflict:** `docs/PROJECT_FACTS.md`'s own "23°40'39.08"" row for
  Sheridan vs the AstroSage PDF's own printed "023-38-19".
- **Resolution:** the `23°40'39.08"` figure is discredited True-Chitra-
  mode boilerplate (Gap O3), not a genuine per-chart oracle read.
  Ratified replacement source = production `SIDM_LAHIRI`. **Numeric
  value TBD** — no `meta.ayanamsha_lahiri` capture for Sheridan exists
  anywhere in this repo (unlike David, who has
  `diagnostics/s127_chart_calculator_david_capture.py`); per the
  instructing task's explicit "do NOT guess" instruction, no number is
  invented here. Derivable on demand via the same
  `calculate_chart("Sheridan", "27 May 1984", "08:00", "Durban, South
  Africa")` method David's capture used — not a blocker, just not yet
  run.
- **Authority:** `SESSION_LOG_ARCHIVE_S67-S104.md:1636-1637` +
  `SESSION_LOG_ARCHIVE_S67-S104.md:1537-1538` ("...at both epochs tested
  (Sulabh 1988, **Sheridan 1984**)"); Gap O3 in
  `docs/KNOWN_DIVERGENCES.md`.

### 2. D1 planet longitudes, AstroSage vs JHora, every body (§3b) — RATIFIED-DIVERGENCE (flipped this update)

- **Conflict:** every planet differs 15″-77″ between the AstroSage PDF
  and the JHora v8 fixture.
- **Resolution:** S75/S76 named the AstroSage-vs-JHora pair directly for
  non-dasha quantities (D1 longitudes explicitly included): JHora
  primary, AstroSage secondary parity not expected.
- **Authority:** `SESSION_LOG_ARCHIVE_S67-S104.md:1561-1563`; Gap O1 in
  `docs/KNOWN_DIVERGENCES.md`.

### 3. Production vs Drik, MD1 boundary (§5) — RATIFIED-DIVERGENCE (unchanged this update)

- **Conflict:** production's Ketu MD1 end (1990-04-08 22:55:52) vs
  Drik Panchang's (1990-04-10 21:06:00) — a -1.9237 day residual.
- **Resolution:** production's own intentional design choice (Gap D1),
  not a bug.
- **Authority:** `docs/KNOWN_DIVERGENCES.md:37-41`. (Sheridan's file
  framed this conflict as production-vs-Drik from the start, which Gap
  D1 already covered directly — unlike David's file, which framed the
  same shape of row as AstroSage-vs-Drik and needed the new Gap O2 to
  resolve; see `manifest_david.md` item 4.)

### 4. Shadbala Drik Bala component, Sun and Moon (§7) — RATIFIED-DIVERGENCE (unchanged this update)

- **Conflict:** AstroSage's own `drik` column (Sun -16.68, Moon -2.88)
  vs JHora's Drik Bala oracle (Sun -25.36, Moon **+0.58**, a sign flip).
- **Resolution:** JHora is the sole ratified oracle for this component;
  Sheridan is specifically named in the module's own docstring as the
  chart exercising this exact Moon sign-flip edge case.
- **Authority:** `agent/calculations/strength/drik_bala.py:11-18,20-29`;
  `CLAUDE.md:249`.

### 5. Ashtakavarga BAV, Moon and Venus rows (§8b) — RATIFIED-DIVERGENCE for 2 cells, DERIVED for the printed-total row, OPEN for 2 cells (updated this pass)

- **Conflict:** JHora (checksum-verified) vs this session's raw PDF
  read disagree at Moon-Gemini, Moon-Sagittarius, Venus-Capricorn,
  Venus-Aquarius, and the printed total row.
- **Resolution (unchanged):** applying `ashtakavarga.py`'s 3 named
  Parasara/Varahamihira cell types to Sheridan's own chart: 9th-from-
  Moon = Sagittarius (matches Moon-Sagittarius) and 4th-from-Mars =
  Capricorn (matches Venus-Capricorn). JHora's value is ratified for
  these two cells.
- **Reclassified this update:** the printed-total-row mismatch is no
  longer counted as an open conflict at all — it is DERIVED (arithmetic
  sum of the 7 planet BAV rows + Lagna), not an independent value, so
  its mismatch is fully explained by the Moon/Venus row deltas already
  on this list. Removed from OPEN.
- **Still OPEN — needs PVR bindu-table hand-computation:** Moon-Gemini,
  Venus-Aquarius. Neither matches the docstring's third named type,
  2nd-from-Jupiter (which maps to Capricorn for Sheridan, not Gemini or
  Aquarius). Resolving these requires hand-computing the relevant bindu
  tables against the PVR book directly — out of scope for this
  reconciliation pass (explicitly not adjudicated per the instructing
  task's constraints).
- **Authority:** `agent/calculations/ashtakavarga/ashtakavarga.py:12-19,24-25`.

---

## Residual OPEN items — Sheridan (PVR Ashtakavarga cross-check only)

1. **Ashtakavarga Moon-Gemini** — needs PVR bindu-table hand-computation.
2. **Ashtakavarga Venus-Aquarius** — needs PVR bindu-table hand-computation.

Every other conflict previously open for Sheridan is now
RATIFIED-DIVERGENCE or reclassified DERIVED. No other OPEN item remains
for Sheridan.

---

David + Sheridan reconciliation complete pending PVR Ashtakavarga
cross-check. AWAITING HUMAN REVIEW.
