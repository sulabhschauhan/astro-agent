# S127 — Sulabh Conflict Reconciliation Manifest

Reconciles every CONFLICT row recorded in
`reference/oracle_fixtures/sulabh.md`. No conflict was adjudicated by
this session's own judgment where no authority exists — every
RATIFIED-DIVERGENCE status below quotes its deciding line verbatim from
an already-landed `docs/KNOWN_DIVERGENCES.md` gap or `CLAUDE.md` Locked
Decision. Same format/convention as `diagnostics/manifest_david.md`.

---

## Sulabh: 7 conflicts found — 5 fully RATIFIED-DIVERGENCE (item 3 upgraded to full closure S127 2nd pass), 2 partially RATIFIED-DIVERGENCE with residual OPEN cells (Ashtakavarga), plus 1 unresolved scheme-level disagreement (jaimini karakas)

### 1. Birth location coordinates (§1) — RATIFIED-DIVERGENCE

- **Conflict:** AstroSage PDF (22:31N, 88:25E) vs app's own Nominatim
  geocoder (22.5726459, 88.3638953) vs JHora S27 capture (22°34'N,
  88°22'E) — three different values.
- **Resolution:** the app's own geocoder output is canonical for
  production calculation. Same authority line used for David's
  identically-shaped conflict.
- **Authority:** `docs/PROJECT_FACTS.md:18-21`.

### 2. Ayanamsa value/mode (§2) — RATIFIED-DIVERGENCE (mode mislabel acknowledged; no replacement value captured)

- **Conflict:** AstroSage PDF print (23°41'33", labeled Lahiri) vs JHora
  S27 fixture (23°40'39.08", labeled Lahiri in the fixture but actually
  True Chitrapaksha per Gap O3).
- **Resolution:** Gap O3 discredits the JHora ayanamsa line as a mode
  mislabel/boilerplate-class value, not a genuine Traditional-Lahiri
  reading. Unlike David's file, this session did NOT run a production
  `calculate_chart()` capture to supply a replacement `SIDM_LAHIRI`
  figure (read-only task, no code execution beyond PDF extraction and
  existing-fixture greps) — so this conflict stays acknowledged but
  without a locked replacement number.
- **Authority:** `docs/KNOWN_DIVERGENCES.md:219-223` (Gap O3).

### 3. D1 planet longitudes, AstroSage vs JHora, every body (§3) — RATIFIED-DIVERGENCE, CLOSED at matched-mode this pass

- **Conflict:** every one of Lagna + 7 grahas + Rahu differs between
  AstroSage (PDF p.3) and JHora S27 (True Chitrapaksha) by
  arcsecond-to-arcminute amounts.
- **Resolution (1st pass):** Gap O1 names JHora primary for non-dasha
  quantities generally (source-class priority) — did not fully close
  the conflict, since S27's JHora capture is True Chitrapaksha, not
  Traditional Lahiri.
- **Resolution (S127 2nd pass, RESOLVED):** Sulabh supplied a genuine
  matched-mode (Traditional Lahiri) JHora D1 capture directly. §3e now
  carries the full residual/Camp-Y table, David/Sheridan-equivalent:
  max |Δ| = 47.92″ (Mercury), sub-90″, no FLAG (≥100″) triggered;
  Rahu/Ketu Δ≈-0.14″ confirms Mean-Node convention match. External ask
  #1 (below) is CLOSED.
- **Authority:** `docs/KNOWN_DIVERGENCES.md:193-198` (Gap O1, source-
  class priority); `reference/oracle_fixtures/sulabh.md` §3e (matched-
  mode residual table, this session).

### 4. Vimshottari MD1 (Jupiter) boundary (§5) — RATIFIED-DIVERGENCE (simpler than David's — no AstroSage-vs-Drik day-level disagreement exists here)

- **Conflict:** production MD1 end (1 Aug 1989) vs Drik/AstroSage MD1
  end (4 Aug 1989) — a ~2.66-day gap, already measured.
- **Resolution:** Gap D1 already lists Sulabh's residual explicitly
  (-2.66d) as one of its four measured, ratified figures. Unlike
  David, AstroSage and Drik agree with each other on the calendar day
  here, so there is no secondary AstroSage-vs-Drik piece to separately
  resolve via Gap O2.
- **Authority:** `docs/KNOWN_DIVERGENCES.md:17-23` (Gap D1, "Sulabh
  -2.66d" cited by name).

### 5. Shadbala Drik Bala component (§7) — RATIFIED-DIVERGENCE

- **Conflict:** AstroSage's printed Drik Bala row (PDF p.50) vs JHora's
  Drik Bala oracle disagree on every planet, worst case Saturn (10.89
  vs 17.46, Δ6.57) and Mercury (Δ10.60).
- **Resolution:** JHora is the sole ratified oracle for this component.
  Sulabh's own Saturn figures are CLAUDE.md's own named worked example
  of this exact accepted divergence.
- **Authority:** `agent/calculations/strength/drik_bala.py:11-18`;
  `CLAUDE.md` Locked Decisions (names "Sulabh Saturn 17.46 vs 10.89"
  directly).

### 6. Ashtakavarga Moon/Venus rows (§8) — RATIFIED-DIVERGENCE for 2 cells, OPEN for 4 cells + total row

- **Conflict:** AstroSage vs JHora disagree at Moon-Taurus, Moon-Cancer,
  Moon-Virgo, Moon-Pisces, Venus-Aries, Venus-Taurus, and the total row.
- **Resolution:** `ashtakavarga.py`'s docstring names three convention-
  choice cell types (9th-from-Moon, 2nd-from-Jupiter, 4th-from-Mars).
  For Sulabh: 9th-from-Moon (Moon in Scorpio) = **Cancer** — a conflict
  cell, JHora's value (4) ratified over AstroSage's (3). 2nd-from-
  Jupiter (Jupiter in Aries) = **Taurus** — also a conflict cell, on
  the Venus row; JHora's value (2) ratified over AstroSage's (3).
  4th-from-Mars (Mars in Capricorn) = Aries, on the Moon row; that
  specific cell (Moon-Aries) shows NO conflict for Sulabh (both sources
  say 3), so nothing to ratify there.
- **Still OPEN — needs PVR bindu-table hand-computation:** Moon-Taurus,
  Moon-Virgo, Moon-Pisces, Venus-Aries. None of these four match any of
  the three named convention-choice cell types for this chart's planet
  placements.
- **Authority:** `agent/calculations/ashtakavarga/ashtakavarga.py:12-19,24-25`.

### 7. Jaimini karaka scheme (§9) — NOT RATIFIED, genuinely different from David's equivalent finding

- **Conflict:** JHora's 8-karaka scheme (Rahu as Darakaraka) assigns
  Gnatikaraka to Moon; AstroSage's printed 7-karaka scheme (no Rahu
  karaka) assigns Gnati to Mars and Dara to Moon — Mars appears in
  AstroSage's karaka set where JHora's does not.
- **Why this is NOT the same as David's §9 finding:** David's two
  sources agreed on the full 7-planet karaka *set* even though naming
  conventions differed (S127 David reconciliation found zero cell-level
  disagreement). Sulabh's two sources disagree on which physical
  planets are even in the karaka set (Mars vs Rahu at one role).
- **Resolution: NONE FOUND.** Gap O1 names JHora primary for "karakas"
  as a source-class preference, but its own text is about oracle-
  precision disagreement (arcsecond/arcminute-scale), not about which
  of two different classical karaka-counting conventions (7 vs 8,
  Rahu-inclusive or not) a codebase should follow. This is a scheme-
  level question, not adjudicated by this session per its own
  constraints ("do NOT adjudicate OPEN cells").
- **Authority:** none found for the scheme question specifically;
  `docs/KNOWN_DIVERGENCES.md:193-198` (Gap O1) covers only the source-
  class priority, cited for completeness.

---

## Residual OPEN items — Sulabh

1. **Ashtakavarga Moon-Taurus** — needs PVR bindu-table hand-computation.
2. **Ashtakavarga Moon-Virgo** — needs PVR bindu-table hand-computation.
3. **Ashtakavarga Moon-Pisces** — needs PVR bindu-table hand-computation.
4. **Ashtakavarga Venus-Aries** — needs PVR bindu-table hand-computation.
5. **Jaimini karaka scheme (7 vs 8, Rahu-inclusive or not)** — needs a
   design-chat/Sulabh ruling on which classical convention this
   codebase follows; JHora's 8-karaka scheme is what
   `agent/calculations/jaimini/karakas.py` already implements (per the
   existing `test_jaimini_karakas.py` oracle), so this is a documentation
   gap about AstroSage's divergence, not a code decision pending —
   flagged so it is not silently treated as "AstroSage must be wrong"
   without a recorded reason.

---

## External data asks (matched-mode captures needed)

1. **MATCHED-MODE (Traditional Lahiri) JHora GUI D1 planetary-longitude
   capture for Sulabh.** ~~The only in-repo JHora D1 longitude data for
   Sulabh (`tests/fixtures/jhora_sulabh.md` §1-2, S27) is True
   Chitrapaksha.~~ **CLOSED, S127 2nd pass.** Sulabh supplied this
   directly (9 grahas + Lagna, Traditional Lahiri) — now
   `reference/oracle_fixtures/sulabh.md` §3e, with a full Camp-Y
   residual table run against a fresh production `calculate_chart()`
   capture. See reconciliation item #3 above.
2. **A production `SIDM_LAHIRI` `calculate_chart()` capture for
   Sulabh**, analogous to David's `diagnostics/s127_chart_calculator_
   david_capture.py` — would let the §2 ayanamsa conflict close with a
   locked replacement value the way David's did, instead of staying at
   "mode mislabel acknowledged, no replacement value." **Still OPEN**
   (this pass's `calculate_chart()` run captured `meta.ayanamsha_lahiri
   = 23.6931°` incidentally while building §3e, but §2's own ayanamsa
   conflict was not re-adjudicated this pass — flagged here rather than
   silently closed).

---

Sulabh reconciliation complete except for the 5 residual OPEN items and
2 external-data asks above. AWAITING HUMAN REVIEW.
