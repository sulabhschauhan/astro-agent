# Oracle Reference — Surbhi

**Purpose:** consolidated, per-person oracle reference for Surbhi, built
READ-ONLY from repo fixtures, diagnostics, and the in-repo AstroSage PDF
(`data/pdfs/Wife_VedicReport.pdf`, confirmed by content — page 2 prints
"Surbhi" — extracted via `pdfplumber`; `VedicReport5-24-202610-01-26PM.pdf`
is Sulabh's, confirmed the same way and NOT used here). No value here
is computed, converted, or inferred beyond DMS→decimal-degree arithmetic
and citing existing production output; every row is a verbatim
transcription with a file/page citation, or an existing fixture value
copied verbatim. Where two sources disagree and no authority exists,
both are recorded in a CONFLICT row and neither is picked.

**Session:** S127 (built in the same pass that also supplied §3e's
matched-mode data and closed the 3 data-flags below — this file was not
written in an earlier pass; no rebuild/clobber occurred). Same
conventions/status legend as `reference/oracle_fixtures/sulabh.md`.

---

## 0. Mode discipline note

- **AstroSage PDF** prints `Ayanamsa Name Lahiri`, value `023-45-16`
  (PDF p.2/p.3).
- **`tests/fixtures/jhora_surbhi.md`** states "Ayanamsa: Lahiri
  (23-40-39.08)" in its own header (line 4) — this is **byte-identical**
  to Sulabh's S27 True-Chitrapaksha capture figure. Per Gap O3 and this
  session's own instructing rule ("if Surbhi's figure equals another
  chart's, it is boilerplate — discredit it"), this is confirmed
  **boilerplate, not a genuine per-chart capture** — discredited, not
  used as any kind of oracle below.
- **`tests/calculations/test_jaimini_karakas.py`'s `SURBHI` dict** (D1
  longitudes used as the Jaimini-karaka oracle) is a **genuine
  independent JHora capture**, distinguished from the boilerplate above
  by a uniform +56.20″ offset from the matched-mode §3e table on every
  single planet (computed this session) — a fixed whole-zodiac shift is
  exactly the signature of a real ayanamsa-mode difference (True
  Chitrapaksha vs Traditional Lahiri), not a copy-paste artifact.
  Tagged **§3b, True Chitrapaksha** below.
- **§3e (matched-mode, Traditional Lahiri) is SUPPLIED directly by
  Sulabh (user) this session** — 9 grahas + Lagna, JHora v8. This is
  the working D1-longitude oracle; §3a/§3b stay recorded for provenance
  only.
- **Drik Panchang S76 capture** (`diagnostics/drik_vimshottari_S76_
  surbhi.md`) confirms its own ayanamsa setting as Traditional/
  Chitrapaksha Lahiri — matched-mode, preferred for dasha per Gap O2.

---

## 1. birth_data

| item | value | unit | source (file:line or PDF p.N) | ayanamsa/mode | status | session |
|---|---|---|---|---|---|---|
| Name | Surbhi | — | PDF p.2 | n/a | oracle-confirmed | S127 |
| Sex | Female | — | PDF p.2 | n/a | oracle-confirmed | S127 |
| Date of Birth | 11 : 9 : 1992 | D:M:Y | PDF p.2 | n/a | oracle-confirmed | S127 |
| Time of Birth | 10 : 30 : 0 | H:M:S | PDF p.2 | n/a | oracle-confirmed | S127 |
| Day of Birth | Friday | — | PDF p.2 | n/a | oracle-confirmed | S127 |
| Place of Birth | Patna | — | PDF p.2 | n/a | oracle-confirmed | S127 |
| Time Zone | 5.5 | hours | PDF p.2 | n/a | oracle-confirmed | S127 |
| Latitude | 25 : 36 : N | deg:min | PDF p.2 | n/a | oracle-confirmed | S127 |
| Longitude | 85 : 7 : E | deg:min | PDF p.2 | n/a | oracle-confirmed | S127 |
| Local Time Correction | 00.10.27 | h.m.s | PDF p.2 | n/a | oracle-confirmed | S127 |
| LMT at Birth | 10:40:28 | H:M:S | PDF p.2 | n/a | oracle-confirmed | S127 |
| GMT at Birth | 5:0:0 | H:M:S | PDF p.2 | n/a | oracle-confirmed | S127 |
| Julian Day | 2448877 | JD (AstroSage truncated display) | PDF p.2/p.3 | n/a | oracle-confirmed | S127 |
| Ishtkaal | 012-20-28 | deg-min-sec | PDF p.2 | n/a | oracle-confirmed | S127 |
| Dasa Balance (Rah) | 6 Y 5 M 24 D | Y/M/D | PDF p.2 | n/a | oracle-confirmed | S127 |
| Lagna | Libra | — | PDF p.2/p.3 | n/a | oracle-confirmed | S127 |
| Lagna Lord | Ven | — | PDF p.2 | n/a | oracle-confirmed | S127 |
| Geocoded Latitude | 25.6093239 | decimal deg | `tests/fixtures/geocoded_locations.json:55` | n/a | oracle-confirmed (Nominatim/OSM) | S127 |
| Geocoded Longitude | 85.1235252 | decimal deg | `tests/fixtures/geocoded_locations.json:56` | n/a | oracle-confirmed (Nominatim/OSM) | S127 |
| Canonical calculate_chart() input | `("Surbhi", "11 Sep 1992", "10:30", "Patna, India")` | — | `tests/calculations/strength/test_drik_bala.py:221`, `test_ishta_kashta.py:117`, `test_combustion.py:80` (byte-identical) | n/a | oracle-confirmed (unambiguous, used this session) | S127 |

**CONFLICT — birth location:** AstroSage PDF (25:36N, 85:7E =
25.6, 85.1167) vs app geocoder (25.6093239, 85.1235252). Pick nothing.

| resolution | authority | status |
|---|---|---|
| App's own Nominatim/OSM geocoder canonical for production. | `docs/PROJECT_FACTS.md:18-21` | RATIFIED-DIVERGENCE |

---

## 2. ayanamsa (+mode)

| item | value | source | mode | status |
|---|---|---|---|---|
| Ayanamsa (AstroSage) | 023-45-16 | PDF p.2 ("Ayanamsa Name Lahiri") | Lahiri | oracle-confirmed |
| Obliquity | 023-26-25 | PDF p.2 | n/a | oracle-confirmed |
| Sidereal Time | 10.02.18 | PDF p.2 | n/a | oracle-confirmed |
| Ayanamsa (`jhora_surbhi.md` header) | 23-40-39.08 | `tests/fixtures/jhora_surbhi.md:4` | **boilerplate, discredited** (identical to Sulabh's figure) | see §0 |
| Production `ayanamsha_lahiri` | 23.755° | this session's `calculate_chart()` run (§3e) | Traditional Lahiri | production-output |

No conflict adjudicated between AstroSage's 023-45-16 and production's
23.755° — both nominally "Lahiri", not cross-checked cell-by-cell here
(out of this pass's scope; §3e's per-planet residual table is the
operative matched-mode comparison instead).

---

## 3. D1_planet_longitudes

### 3a. AstroSage PDF p.3 — Planetary Positions

| Planet | Sign | Position (deg-min-sec in sign) | Nakshatra | Pada | Retro |
|---|---|---|---|---|---|
| ASC | Libra | 29-52-55 | Vishakha | 3 | — |
| Sun | Leo | 24-57-43 | Purvaphalgini | 4 | — |
| Moon | Aquarius | 15-11-52 | Satabhisa | 3 | — |
| Mars | Gemini | 05-37-19 | Mrigasira | 4 | — |
| Mercury | Leo | 21-21-53 | Purvaphalgini | 3 | — |
| Jupiter | Leo | 29-54-13 | Uttaraphal | 1 | — |
| Venus | Virgo | 19-10-59 | Hasta | 3 | — |
| Saturn | Capricorn | 19-00-59 | Sravana | 3 | [R] |
| Rahu | Sagittarius | 02-34-55 | Mula | 1 | [R] |
| Ketu | Gemini | 02-34-55 | Mrigasira | 3 | [R] |

Source: PDF p.3. Status: oracle-confirmed. Session: S127.

### 3b. JHora v8 — True Chitrapaksha (genuine capture; distinguished from `jhora_surbhi.md`'s boilerplate ayanamsa line by a uniform +56.20″ whole-zodiac offset from §3e, computed this session — see §0)

| Planet | Sign, deg, min, sec | Source |
|---|---|---|
| Sun | Le 24°58'21.89" | `tests/calculations/test_jaimini_karakas.py:61` |
| Moon | Aq 15°13'3.07" | `tests/calculations/test_jaimini_karakas.py:62` |
| Mars | Ge 5°39'41.10" | `tests/calculations/test_jaimini_karakas.py:63` |
| Mercury | Le 21°22'48.83" | `tests/calculations/test_jaimini_karakas.py:64` |
| Jupiter | Le 29°56'56.35" | `tests/calculations/test_jaimini_karakas.py:65` |
| Venus | Vi 19°11'44.29" | `tests/calculations/test_jaimini_karakas.py:66` |
| Saturn | Cp 19°2'43.46" | `tests/calculations/test_jaimini_karakas.py:67` |
| Rahu | Sg 2°36'4.41" | `tests/calculations/test_jaimini_karakas.py:68` |

Status: oracle-confirmed (JHora v8, True Chitrapaksha mode, per §0's
offset-signature reasoning). Session: not stamped in-file.

### 3e. JHora v8 Traditional Lahiri (matched-mode) — RATIFIED D1 oracle (Gap O1)

Supplied directly by Sulabh (user) this session — 9 grahas + Lagna,
Mean-Node convention (confirmed by the Rahu Δ below).

| Body | JHora Trad-Lahiri (DMS) | abs° | Production abs° | Δ arcsec | Status |
|---|---|---|---|---|---|
| Lagna | Li 29°53'26.41" | 209.890669 | 209.893200 | 9.11 | matched-mode residual |
| Sun | Le 24°57'25.70" | 144.957139 | 144.951449 | -20.48 | matched-mode residual (aberration-scale) |
| Moon | Aq 15°12'06.88" | 315.201911 | 315.201434 | -1.72 | matched-mode residual |
| Mars | Ge 5°38'44.90" | 65.645806 | 65.641602 | -15.13 | matched-mode residual |
| Mercury | Le 21°21'52.63" | 141.364619 | 141.349668 | -53.82 | matched-mode residual (max) |
| Jupiter | Le 29°56'00.15" | 149.933375 | 149.925294 | -29.09 | matched-mode residual |
| Venus | Vi 19°10'48.09" | 169.180025 | 169.169293 | -38.64 | matched-mode residual |
| Saturn | Cp 19°01'47.26" (R) | 289.029794 | 289.032574 | 10.01 | matched-mode residual |
| Rahu | Sg 2°35'08.22" | 242.585617 | 242.585578 | -0.14 | node-convention match (~0) |
| Ketu | Ge 2°35'08.22" | 62.585617 | 62.585578 | -0.14 | node-convention match (~0) |

Production from a fresh `calculate_chart("Surbhi", "11 Sep 1992",
"10:30", "Patna, India")` run this session (canonical tuple, confirmed
unambiguous, 3 byte-identical call sites). `planetary_positions[<planet
>]["longitude"]` for grahas; `meta.asc_lon_sidereal` (209.8932°) for
Lagna. All residuals sub-90″ (max 53.82″, Mercury) — no FLAG (≥100″)
triggered. Rahu/Ketu Δ≈-0.14″ confirms Mean-Node convention match
(byte-identical to David's and Sulabh's own Rahu/Ketu residual — same
JHora Mean-Node setting across all three captures, corroborating).
Recorded as Camp-Y (Gap A1 family), not drift. Saturn's (R) flag
matches AstroSage §3a and production (see §6 note on the S51 FLG_SPEED
fix).

### CONFLICT — AstroSage (§3a) vs JHora True-Chitra (§3b), arcminute-scale, mode-contaminated

Not tabulated cell-by-cell here (same shape as Sulabh's equivalent
conflict) — §3b is True Chitrapaksha, §3a is AstroSage's own Lahiri
print; both are superseded as the working D1 oracle by §3e.

| resolution | authority | status |
|---|---|---|
| §3e (matched-mode Traditional Lahiri) is the ratified working D1 oracle; §3a/§3b are provenance-only. | `docs/KNOWN_DIVERGENCES.md:193-198` (Gap O1) | RATIFIED-DIVERGENCE — resolved at matched-mode by §3e |

---

## 4. D1_sign_house_dignity

**No per-planet dignity table found** (same gap as David/Sulabh).
AstroSage's Lagna-chart diagram (PDF p.3) is an unreadable glyph-fragment
graphic — not transcribed per the no-inference constraint.

| item | value | source | status |
|---|---|---|---|
| Chalit Table | Bhav 1=Libra 15.40.44→Libra 29.52.54; Bhav 2=Scorpion 15.40.44→Sagittarius 01.28.34; Bhav 3=Sagittarius 17.16.23→Capricorn 03.04.13; Bhav 4=Capricorn 18.52.02→Aquarius 04.39.52; Bhav 5=Aquarius 18.52.02→Pisces 03.04.13; Bhav 6=Pisces 17.16.23→Aries 01.28.34; Bhav 7=Aries 15.40.44→Aries 29.52.54; Bhav 8=Taurus 15.40.44→Gemini 01.28.34; Bhav 9=Gemini 17.16.23→Cancer 03.04.13; Bhav 10=Cancer 18.52.02→Leo 04.39.52; Bhav 11=Leo 18.52.02→Virgo 03.04.13; Bhav 12=Virgo 17.16.23→Libra 01.28.34 | PDF p.3 | oracle-confirmed |
| Sign-level dignity | NOT FOUND IN REPO | — | — |

---

## 5. vimshottari_MD_AD

### 5a. AstroSage PDF p.3 — 9-Mahadasha table

| Lord | Start | End |
|---|---|---|
| RAH | 11/9/92 | 5/3/99 |
| JUP | 5/3/99 | 5/3/15 |
| SAT | 5/3/15 | 5/3/34 |
| MER | 5/3/34 | 5/3/51 |
| KET | 5/3/51 | 5/3/58 |
| VEN | 5/3/58 | 5/3/78 |
| SUN | 5/3/78 | 5/3/84 |
| MON | 5/3/84 | 5/3/94 |
| MAR | 5/3/94 | 5/3/01 |

Source: PDF p.3. Status: oracle-confirmed. Session: S127.

### 5b. Drik Panchang — matched-mode oracle

| Lord | Start (local) | End (local) |
|---|---|---|
| Rahu | 1981-03-05 07:19 | 1999-03-05 22:04 |
| Guru (Jupiter) | 1999-03-05 22:04 | 2015-03-06 00:31 |
| Shani (Saturn) | 2015-03-06 00:31 | 2034-03-05 21:25 |
| Budha (Mercury) | 2034-03-05 21:25 | 2051-03-06 06:00 |
| Ketu | 2051-03-06 06:00 | 2058-03-06 01:05 |
| Shukra (Venus) | 2058-03-06 01:05 | 2078-03-06 04:08 |
| Surya (Sun) | 2078-03-06 04:08 | 2084-03-05 17:03 |
| Chandra (Moon) | 2084-03-05 17:03 | 2094-03-06 06:34 |
| Mangal (Mars) | 2094-03-06 06:34 | 2101-03-07 01:38 |

Source: `diagnostics/drik_vimshottari_S76_surbhi.md:15-96`. Status:
oracle-confirmed (Traditional/Chitrapaksha Lahiri, site default).
Session: S76.

### 5c. Production output (post-S76 year_days ship)

| Lord | Start | End |
|---|---|---|
| Rah | 1992-09-11 10:30:00 | 1999-03-05 14:11:50 |
| Jup | 1999-03-05 14:11:50 | 2015-03-05 16:38:26 |
| Sat | 2015-03-05 16:38:26 | 2034-03-05 13:32:32 |
| Merc | 2034-03-05 13:32:32 | 2051-03-05 22:08:18 |
| Ket | 2051-03-05 22:08:18 | 2058-03-05 17:12:26 |
| Ven | 2058-03-05 17:12:26 | 2078-03-05 20:15:41 |
| Sun | 2078-03-05 20:15:41 | 2084-03-05 09:10:40 |
| Moon | 2084-03-05 09:10:40 | 2094-03-05 22:42:17 |
| Mars | 2094-03-05 22:42:17 | 2101-03-06 17:46:26 |

Source: `tests/fixtures/jhora_surbhi.md:28-38`. Status:
production-output. Session: S76. Gap D1 residual (row-0 Rahu end,
production vs Drik): **-0.3259 days** (`diagnostics/drik_vimshottari_
S76_surbhi.md:114-127`), matching `docs/KNOWN_DIVERGENCES.md`'s
Gap D1 measured-residuals list ("Surbhi -0.33d"). RATIFIED-DIVERGENCE
(Camp Y vs Camp X), `docs/KNOWN_DIVERGENCES.md:17-23`.

### 5d. JHora v8 — Yogini Dasha (True Chitrapaksha)

First 3 of 24 rows (full table `tests/fixtures/jhora_surbhi.md:49-74`):

| Lord | Start | End |
|---|---|---|
| Jup | 1990-10-09 20:35:40 | 1993-10-09 15:03:11 |
| Mars | 1993-10-09 15:03:11 | 1997-10-09 15:41:55 |
| Merc | 1997-10-09 15:41:55 | 2002-10-09 22:22:13 |

Status: oracle-confirmed (JHora v8, True Chitrapaksha). Session: S72.

---

## 6. combustion — RESOLVED (flag b closed)

| Planet | Separation from Sun (deg) | Combust? | Orb (deg) | Retro | Source |
|---|---|---|---|---|---|
| Moon | 170.236 | False | 12.0 | False | `tests/calculations/core/test_combustion.py:121` |
| Mercury | 3.597 | **True** | 14.0 | False | `tests/calculations/core/test_combustion.py:122` |
| Jupiter | 4.942 | **True** | 11.0 | False | `tests/calculations/core/test_combustion.py:123` |

**RESOLVED, S127:** Mercury and Jupiter are deeply combust (~3.6° and
~4.97° from Sun respectively) — confirmed independently this session by
a fresh production run: `Sun=144.951449°`, `Mercury=141.349668°` (sep
3.6018°), `Jupiter=149.925294°` (sep 4.9738°), corroborating the test
fixture's oracle-basis figures. The earlier JHora "Basics view shows
none combust" reading was **INVALIDATED at Session 51** — that view
displays no combustion flags at all, so its absence is not evidence of
non-combustion; a wrong-chart JHora screenshot mixup (Surbhi's date at
Sulabh's 00:30) was also caught in the same design-chat pass. Oracle
basis for this module is hand-falsified arithmetic on AstroSage p.3
longitudes (separations are ayanamsa-invariant), not the JHora Basics
view. Citation: `SESSION_LOG_ARCHIVE_S19-S66.md:1134-1138` ("a false
'none combust' read from JHora Basics view ... Basics-view absence is
not evidence"); corroborated in-file at
`tests/calculations/core/test_combustion.py:17-22` ("Surbhi PDF p.23
shows Mercury=Muditha at 3.6 deg from Sun").

**Note on Saturn retrograde (not a flag in this pass, recorded for
completeness):** AstroSage PDF p.3 shows Saturn `[R]`; this session's
production run shows Saturn's longitude consistent with the matched-
mode §3e oracle. The retrograde flag only became reliably True post the
Session 51 `FLG_SPEED` fix (this assistant's own persistent memory,
`project_retrograde_flag_fix_session51.md`, not a repo file — cited for
completeness, same convention as `sheridan.md:490-496`) — any
pre-fix-era retrograde reading elsewhere in the repo should not be
treated as oracle for Surbhi's Saturn.

---

## 7. shadbala_components

### 7a. AstroSage PDF p.50 — ShadBala

| Component | Sun | Moon | Mars | Mercury | Jupiter | Venus | Saturn |
|---|---|---|---|---|---|---|---|
| Ochcha Bala | 15.01 | 34.07 | 17.46 | 52.12 | 41.7 | 2.61 | 30.33 |
| Saptavargaja Bala | 110.62 | 82.5 | 101.25 | 95.62 | 86.25 | 91.88 | 69.38 |
| Ojayugmarasyamsa Bala | 15 | 0 | 15 | 30 | 30 | 15 | 15 |
| Kendra Bala | 30 | 30 | 15 | 30 | 30 | 15 | 60 |
| Drekkana Bala | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| **Total Sthan Bala** | **170.64** | **146.57** | **163.71** | **207.75** | **187.95** | **124.48** | **189.7** |
| Total Dig Bala | 53.23 | 56.49 | 40.32 | 37.16 | 40.01 | 14.84 | 26.38 |
| Nathonnatha Bala | 53.66 | 6.34 | 6.34 | 60 | 53.66 | 53.66 | 6.34 |
| Paksha Bala | 3.25 | 56.75 | 3.25 | 56.75 | 56.75 | 56.75 | 3.25 |
| Thribhaga Bala | 60 | 0 | 0 | 0 | 60 | 0 | 0 |
| Abda Bala | 15 | 0 | 0 | 0 | 0 | 0 | 0 |
| Masa Bala | 0 | 0 | 0 | 0 | 30 | 0 | 0 |
| Vara Bala | 0 | 0 | 0 | 0 | 0 | 45 | 0 |
| Hora Bala | 0 | 0 | 0 | 0 | 0 | 0 | 60 |
| Ayana Bala | 71.35 | 40.41 | 59.95 | 37.48 | 33.19 | 23.5 | 51.61 |
| Yuddha Bala | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **Total Kala Bala** | **203.26** | **103.5** | **69.55** | **154.23** | **233.59** | **178.9** | **121.2** |
| **Total Chesta Bala** | **33.76** | **56.75** | **35.19** | **11.19** | **2.08** | **15.94** | **49.36** |
| **Total Naisargika Bala** | **60** | **51.42** | **17.16** | **25.74** | **34.26** | **42.84** | **8.58** |
| **Total Drik Bala (AstroSage)** | **-5.31** | **4.14** | **13.38** | **-4.41** | **-6.55** | **-10.03** | **3.52** |
| **Total Shad Bala** | **515.58** | **418.85** | **339.31** | **431.65** | **491.34** | **366.96** | **398.74** |
| Shadbala In Rupas | 8.59 | 6.98 | 5.66 | 7.19 | 8.19 | 6.12 | 6.65 |
| Minimum Requirements | 5 | 6 | 5 | 7 | 6.5 | 5.5 | 5 |
| Ratio | 1.72 | 1.16 | 1.13 | 1.03 | 1.26 | 1.11 | 1.33 |
| Relative Rank | 1 | 4 | 5 | 7 | 3 | 6 | 2 |

Source: PDF p.50. Status: oracle-confirmed. Session: S127.

### 7b. AstroSage PDF p.50 — BhavBala

| Component | H1 | H2 | H3 | H4 | H5 | H6 | H7 | H8 | H9 | H10 | H11 | H12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Bhavadhipati Bala | 366.96 | 339.31 | 491.34 | 398.74 | 398.74 | 491.34 | 339.31 | 366.96 | 431.65 | 418.85 | 515.58 | 431.65 |
| Bhavdig Bala | 60 | 50 | 10 | 30 | 50 | 20 | 30 | 10 | 10 | 60 | 40 | 50 |
| Bhavdrishti Bala | 25.45 | 69.33 | 67.6 | 23.53 | 99.7 | 70.59 | 56.31 | 32.02 | -1.98 | -6.94 | -7.34 | -3.47 |
| Total Bhav Bala | 452.41 | 458.65 | 568.94 | 452.27 | 548.44 | 581.93 | 425.62 | 408.98 | 439.67 | 471.91 | 548.24 | 478.18 |

Source: PDF p.50. Status: oracle-confirmed. Session: S127. Bhavdig Bala
row cross-verified byte-identical against
`tests/fixtures/bhava_dig_bala_astrosage.py:22-25` (Session 42).

### 7c. JHora v8 Drik Bala oracle

| Planet | Drik Bala (JHora) |
|---|---|
| Sun | -7.72 |
| Moon | 4.12 |
| Mars | 13.38 |
| Mercury | -6.37 |
| Jupiter | -9.59 |
| Venus | -8.40 |
| Saturn | 0.42 |

Source: `tests/calculations/strength/test_drik_bala.py:208-211`
(`_JHORA_DRIK["surbhi"]`). Status: oracle-confirmed.

### 7d. JHora v8 Ishta/Kashta Bala oracle

| Planet | Ishta Phala | Kashta Phala |
|---|---|---|
| Sun | 22.59 | 34.20 |
| Moon | 43.97 | 9.18 |
| Mars | 25.04 | 32.01 |
| Mercury | 19.63 | 20.35 |
| Jupiter | 6.74 | 32.85 |
| Venus | 6.49 | 50.16 |
| Saturn | 38.29 | 18.59 |

Source: `tests/calculations/strength/test_ishta_kashta.py:60-62`
(`_ORACLE["surbhi"]`). Status: oracle-confirmed.

### CONFLICT — Drik Bala: AstroSage (§7a) vs JHora (§7c) disagree on every planet

| Planet | AstroSage | JHora | Delta |
|---|---|---|---|
| Sun | -5.31 | -7.72 | 2.41 |
| Moon | 4.14 | 4.12 | 0.02 |
| Mars | 13.38 | 13.38 | 0.00 |
| Mercury | -4.41 | -6.37 | 1.96 |
| Jupiter | -6.55 | -9.59 | 3.04 |
| Venus | -10.03 | -8.40 | 1.63 |
| Saturn | 3.52 | 0.42 | 3.10 |

| resolution | authority | status |
|---|---|---|
| JHora sole ratified oracle for Drik Bala; AstroSage parity not expected. | `agent/calculations/strength/drik_bala.py:11-18`; `CLAUDE.md` Locked Decisions | RATIFIED-DIVERGENCE |

---

## 8. ashtakavarga_BAV_SAV

### 8a. JHora v8 (reference = Libra = natal lagna, checksum-validated)

| Planet | Ar | Ta | Ge | Cn | Le | Vi | Li | Sc | Sg | Cp | Aq | Pi | Total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Sun | 6 | 2 | 4 | 5 | 4 | 4 | 2 | 3 | 5 | 5 | 4 | 4 | 48 |
| Moon | 2 | 5 | 5 | 4 | 5 | 1 | 4 | 6 | 4 | 2 | 4 | 7 | 49 |
| Mars | 4 | 2 | 4 | 6 | 3 | 2 | 4 | 1 | 5 | 5 | 1 | 2 | 39 |
| Mercury | 5 | 4 | 4 | 8 | 3 | 4 | 4 | 4 | 5 | 7 | 2 | 4 | 54 |
| Jupiter | 4 | 5 | 8 | 3 | 5 | 4 | 5 | 4 | 4 | 4 | 4 | 6 | 56 |
| Venus | 6 | 6 | 6 | 2 | 3 | 4 | 5 | 4 | 5 | 4 | 3 | 4 | 52 |
| Saturn | 3 | 4 | 4 | 5 | 4 | 1 | 2 | 3 | 3 | 3 | 2 | 5 | 39 |
| Lagna | 5 | 4 | 5 | 3 | 4 | 3 | 3 | 7 | 4 | 6 | 1 | 4 | 49 |

SAV (7 planets): Ar30 Ta28 Ge35 Cn33 Le27 Vi20 Li26 Sc25 Sg31 Cp30
Aq20 Pi32 = 337.

Source: `tests/fixtures/jhora_ashtakavarga_cross_charts.md:82-99`.
Status: oracle-confirmed (checksum-validated, "zero transcription
corrections"). Session: S54.

### 8b. AstroSage PDF p.3 — Ashtakvarga

| Planet | Ar | Ta | Ge | Cn | Le | Vi | Li | Sc | Sg | Cp | Aq | Pi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Sun | 6 | 2 | 4 | 5 | 4 | 4 | 2 | 3 | 5 | 5 | 4 | 4 |
| Moon | 2 | 5 | 5 | 5 | 5 | 0 | 3 | 6 | 4 | 2 | 5 | 7 |
| Mars | 4 | 2 | 4 | 6 | 3 | 2 | 4 | 1 | 5 | 5 | 1 | 2 |
| Mercury | 5 | 4 | 4 | 8 | 3 | 4 | 4 | 4 | 5 | 7 | 2 | 4 |
| Jupiter | 4 | 5 | 8 | 3 | 5 | 4 | 5 | 4 | 4 | 4 | 4 | 6 |
| Venus | 6 | 6 | 6 | 2 | 3 | 3 | 6 | 4 | 5 | 4 | 3 | 4 |
| Saturn | 3 | 4 | 4 | 5 | 4 | 1 | 2 | 3 | 3 | 3 | 2 | 5 |
| **Total (printed)** | 30 | 28 | 35 | 34 | 27 | 18 | 26 | 25 | 31 | 30 | 21 | 32 |

Source: PDF p.3. Status: oracle-confirmed. Session: S127.

### CONFLICT — Moon row + total row disagree (Sun/Mars/Mercury/Jupiter/Saturn match exactly; Venus matches too except one cell)

| Row | AstroSage (8b) | JHora (8a) | Match? |
|---|---|---|---|
| Moon | 2,5,5,5,5,0,3,6,4,2,5,7 | 2,5,5,4,5,1,4,6,4,2,4,7 | **no** (Cn: 5 vs 4; Vi: 0 vs 1; Li: 3 vs 4; Aq: 5 vs 4) |
| Venus | 6,6,6,2,3,3,6,4,5,4,3,4 | 6,6,6,2,3,4,5,4,5,4,3,4 | **no** (Vi: 3 vs 4; Li: 6 vs 5) |
| Total row | 30,28,35,34,27,18,26,25,31,30,21,32 | 30,28,35,33,27,20,26,25,31,30,20,32 | **no** (Cn, Vi, Aq columns differ, consistent with Moon/Venus deltas) |

| resolution | authority | status |
|---|---|---|
| `ashtakavarga.py`'s docstring names 9th-from-Moon and 4th-from-Mars as sentinel cells. Surbhi's Moon is in Aquarius; 9th-from-Aquarius = Virgo (Vi cell, AstroSage=0, JHora=1 — a conflict cell). Surbhi's Mars is in Gemini; 4th-from-Gemini = Virgo — same cell, both conventions point to Virgo here. Surbhi's Jupiter is in Leo; 2nd-from-Leo = Virgo — again the same Vi cell. All three named convention-choice types converge on Moon-Virgo for this chart; JHora's value (1) is ratified over AstroSage's (0). | `agent/calculations/ashtakavarga/ashtakavarga.py:12-19,24-25` | RATIFIED-DIVERGENCE for Moon-Virgo; **OPEN — needs PVR bindu-table hand-computation** for Moon-Cancer, Moon-Libra, Moon-Aquarius, Venus-Virgo, Venus-Libra (not matched by any named sentinel type); total-row mismatch is DERIVED, not independently adjudicated |

---

## 9. jaimini_karakas

### 9a. JHora v8 — Chara Karakas

| Karaka | Planet |
|---|---|
| AK | Jupiter |
| AmK | Rahu |
| BK | Sun |
| MK | Mercury |
| PiK | Venus |
| PK | Saturn |
| GK | Moon |
| DK | Mars |

Source: `tests/calculations/test_jaimini_karakas.py:70-73`
(`SURBHI_EXPECTED`). Status: oracle-confirmed.

### 9b. AstroSage PDF p.23 — Karak Avastha (Sthir/Chara columns; same header-garbling caveat as David/Sulabh files)

| Karaka name | Sthir | Chara |
|---|---|---|
| Atma | Sun | Jupt |
| Amatya | Merc | Sun |
| Bhratru | Mars | Merc |
| Matrua | Moon | Venu |
| Putra | Jupt | Satn |
| Gnati | Satn | Moon |
| Dara | Venu | Mars |

Source: PDF p.23. Status: oracle-confirmed. Session: S127.

### Comparison — full agreement, JHora's 8-karaka Rahu-inclusive naming aside

| Role | JHora (9a) | AstroSage Chara (9b) | Match? |
|---|---|---|---|
| AK | Jupiter | Jupt | yes |
| BK | Sun | Sun (Amatya row) | role-name differs, planet matches AK↔Amatya crosswalk — see note |
| MK | Mercury | Merc (Bhratru row) | see note |
| PiK | Venus | Venu (Matrua row) | see note |
| PK | Saturn | Satn (Putra row) | see note |
| GK | Moon | Moon (Gnati row) | see note |
| DK | Mars | Mars (Dara row) | see note |

**Note:** unlike Sulabh's chart, AstroSage's Chara column here is a
**pure relabeling** of JHora's assignment under AstroSage's own
Sthir-role names, not a different planet set — the planet SET
{Jupiter, Sun, Mercury, Venus, Saturn, Moon, Mars} matches JHora's
7-graha set exactly (Rahu is absent from AstroSage's 7-karaka scheme
here too, same structural difference as Sulabh's file, but for Surbhi
it does not produce a planet-level disagreement — Rahu simply has no
AstroSage-side counterpart to compare). No CONFLICT declared — full
corroboration. (Contrast with `manifest_sulabh.md` item 7, where the
same scheme difference DID produce a genuine planet-level mismatch for
that chart.)

---

## Data-flag closures (S127, this pass)

1. **Moon nakshatra mislabel — RESOLVED.** `diagnostics/
   vimshottari_year_length_S74.md:309-310` labels Surbhi's Moon
   (longitude 315.201430°) "Uttara Bhadrapada, nakshatra #24" — index
   #24 in the standard 27-nakshatra list is **Shatabhisha**, not Uttara
   Bhadrapada (#26). Confirmed independently three ways this session:
   AstroSage PDF p.2/p.3 prints "Satabhisa" directly; JHora §3b/§3e
   both fall in the Satabhisha span; this session's own fresh
   `calculate_chart()` run returns `nakshatra: 'Shatabhisha'` in
   `lagna_chart`. The S74 diagnostic's label is the error; its own
   longitude and nakshatra-index number are correct, only the printed
   name is wrong.
2. **Combustion — RESOLVED.** See §6 above. Mercury/Jupiter deep
   combustion confirmed by production-longitude arithmetic; the
   "Basics view shows none combust" reading is INVALIDATED (S51,
   `SESSION_LOG_ARCHIVE_S19-S66.md:1134-1138`), not used as evidence.
3. **Jupiter near-boundary — BOUNDARY-SENSITIVE, flagged not resolved.**
   Jupiter sits `29°56'00.15"` in Leo per §3e (Trad-Lahiri) — **0.0666°
   (4.0 arcmin) from the Virgo boundary** — and `29.9253°` per
   production (0.0747°/4.48 arcmin from the boundary). Sign stays Leo
   in both the matched-mode JHora capture and production (they agree),
   so no sign-placement error exists today — but this placement is
   close enough that any future ayanamsa/ephemeris refinement could
   flip it to Virgo. Flagged for awareness in any downstream
   Jupiter-sign-dependent logic (dignity, yogas, dasha lord), not
   fixed — no code change indicated by a still-stable sign.

---

## Categories explicitly NOT FOUND IN REPO for Surbhi

- Per-planet sign-based dignity table — only the Chalit table (§4)
  exists.
- A combustion table printed directly by AstroSage (§6 is test-fixture
  hand-derived).
- Any Ashtottari, D2-D60 varga reference values, or Mangal Dosha /
  Kalsarpa Yoga oracle determination for Surbhi specifically (beyond
  the Sulabh+Surbhi Ashtakoot pair fixture,
  `tests/fixtures/astrosage_sulabh_surbhi_kundli_milan.md`, not
  transcribed here — compatibility data, not a solo-chart oracle).


Surbhi::
traditional lahiri:

Body                    Longitude        Nakshatra Pada Rasi Navamsa

Lagna                   29 Li 53' 26.41" Visa      3    Li   Ge
Sun - BK                24 Le 57' 25.70" PPha      4    Le   Sc
Moon - GK               15 Aq 12' 06.88" Sata      3    Aq   Aq
Mars - DK                5 Ge 38' 44.90" Mrig      4    Ge   Sc
Mercury - MK            21 Le 21' 52.63" PPha      3    Le   Li
Jupiter - AK            29 Le 56' 00.15" UPha      1    Le   Sg
Venus - PiK             19 Vi 10' 48.09" Hast      3    Vi   Ge
Saturn (R) - PK         19 Cp 01' 47.26" Srav      3    Cp   Ge
Rahu - AmK               2 Sg 35' 08.22" Mool      1    Sg   Ar
Ketu                     2 Ge 35' 08.22" Mrig      3    Ge   Li
Maandi                  25 Vi 56' 39.42" Chit      1    Vi   Le
Gulika                  15 Vi 35' 04.21" Hast      2    Vi   Ta
Bhava Lagna              7 Sc 52' 47.89" Anu       2    Sc   Vi
Hora Lagna              21 Cp 00' 01.00" Srav      4    Cp   Cn
Ghati Lagna              0 Vi 21' 40.31" UPha      2    Vi   Cp
Vighati Lagna           17 Vi 09' 56.89" Hast      3    Vi   Ge
Varnada Lagna           29 Cn 53' 26.41" Asre      4    Cn   Vi
Sree Lagna              20 Ge 20' 32.16" Puna      1    Ge   Ar
Pranapada Lagna         17 Ta 21' 47.80" Rohi      3    Ta   Ge
Indu Lagna              15 Vi 12' 06.88" Hast      2    Vi   Ta
Bhrigu Bindu             8 Cp 53' 37.55" USha      4    Cp   Pi
Dhooma                   8 Cp 17' 25.70" USha      4    Cp   Pi
Vyatipata               21 Ge 42' 34.30" Puna      1    Ge   Ar
Parivesha               21 Sg 42' 34.30" PSha      3    Sg   Li
Indra Chapa              8 Cn 17' 25.70" Push      2    Cn   Vi
Upaketu                 24 Cn 57' 25.70" Asre      3    Cn   Aq
Kaala                    6 Sc 21' 49.74" Anu       1    Sc   Le
Mrityu                  17 Sg 48' 06.38" PSha      2    Sg   Vi
Artha Prahara           11 Cp 48' 06.01" Srav      1    Cp   Ar
Yama Ghantaka            9 Aq 49' 56.85" Sata      1    Aq   Sg
Prana Sphuta            15 Le 02' 16.24" PPha      1    Le   Le
Deha Sphuta             17 Vi 11' 59.24" Hast      3    Vi   Ge
Mrityu Sphuta           14 Sc 02' 55.14" Anu       4    Sc   Sc
Sookshma TriSphuta      16 Vi 17' 10.63" Hast      2    Vi   Ta
Tithi Sphuta            20 Vi 14' 41.18" Hast      4    Vi   Cn
Yoga Sphuta (Sun-Moon)  10 Cn 09' 32.58" Push      3    Cn   Li
Rahu Tithi Sphuta        7 Cn 37' 42.52" Push      2    Cn   Vi
Kshetra Sphuta          20 Vi 46' 51.94" Hast      4    Vi   Cn
Beeja Sphuta            14 Cn 04' 13.95" Push      4    Cn   Sc
TriSphuta                0 Pi 40' 37.49" PBha      4    Pi   Cn
ChatusSphuta            25 Cn 38' 03.19" Asre      3    Cn   Aq
PanchaSphuta            28 Pi 13' 11.41" Reva      4    Pi   Pi
V2                      29 Li 53' 26.41" Visa      3    Li   Sg
V3                      29 Sc 53' 26.41" Jye       4    Sc   Ta
V4                      29 Aq 53' 26.41" PBha      3    Aq   Ar
V5                      29 Pi 53' 26.41" Reva      4    Pi   Ta
V6                      29 Aq 53' 26.41" PBha      3    Aq   Sg
V7                      29 Sc 53' 26.41" Jye       4    Sc   Vi
V8                      29 Li 53' 26.41" Visa      3    Li   Le
V9                      29 Cn 53' 26.41" Asre      4    Cn   Cp
V10                     29 Aq 53' 26.41" PBha      3    Aq   Ar
V11                     29 Pi 53' 26.41" Reva      4    Pi   Cp
V12                     29 Aq 53' 26.41" PBha      3    Aq   Le
Kunda                   21 Ge 08' 39.02" Puna      1    Ge   Ar
Yoga Sphuta             13 Li 29' 32.58" Swat      3    Li   Aq
Avayoga Sphuta          20 Ar 09' 32.58" Bhar      3    Ar   Li

true lahiri/chitrapaksha:
Body                    Longitude        Nakshatra Pada Rasi Navamsa

Lagna                   29 Li 54' 22.60" Visa      3    Li   Ge
Sun - BK                24 Le 58' 21.89" PPha      4    Le   Sc
Moon - GK               15 Aq 13' 03.07" Sata      3    Aq   Aq
Mars - DK                5 Ge 39' 41.10" Mrig      4    Ge   Sc
Mercury - MK            21 Le 22' 48.83" PPha      3    Le   Li
Jupiter - AK            29 Le 56' 56.35" UPha      1    Le   Sg
Venus - PiK             19 Vi 11' 44.29" Hast      3    Vi   Ge
Saturn (R) - PK         19 Cp 02' 43.46" Srav      3    Cp   Ge
Rahu - AmK               2 Sg 36' 04.41" Mool      1    Sg   Ar
Ketu                     2 Ge 36' 04.41" Mrig      3    Ge   Li
Maandi                  25 Vi 57' 35.61" Chit      1    Vi   Le
Gulika                  15 Vi 36' 00.40" Hast      2    Vi   Ta
Bhava Lagna              7 Sc 53' 44.09" Anu       2    Sc   Vi
Hora Lagna              21 Cp 00' 57.19" Srav      4    Cp   Cn
Ghati Lagna              0 Vi 22' 36.51" UPha      2    Vi   Cp
Vighati Lagna           17 Vi 10' 53.08" Hast      3    Vi   Ge
Varnada Lagna           29 Cn 54' 22.60" Asre      4    Cn   Vi
Sree Lagna              20 Ge 46' 45.63" Puna      1    Ge   Ar
Pranapada Lagna         17 Ta 22' 44.00" Rohi      3    Ta   Ge
Indu Lagna              15 Vi 13' 03.07" Hast      2    Vi   Ta
Bhrigu Bindu             8 Cp 54' 33.74" USha      4    Cp   Pi
Dhooma                   8 Cp 18' 21.89" USha      4    Cp   Pi
Vyatipata               21 Ge 41' 38.11" Puna      1    Ge   Ar
Parivesha               21 Sg 41' 38.11" PSha      3    Sg   Li
Indra Chapa              8 Cn 18' 21.89" Push      2    Cn   Vi
Upaketu                 24 Cn 58' 21.89" Asre      3    Cn   Aq
Kaala                    6 Sc 22' 45.94" Anu       1    Sc   Le
Mrityu                  17 Sg 49' 02.57" PSha      2    Sg   Vi
Artha Prahara           11 Cp 49' 02.20" Srav      1    Cp   Ar
Yama Ghantaka            9 Aq 50' 53.04" Sata      1    Aq   Sg
Prana Sphuta            15 Le 07' 53.42" PPha      1    Le   Le
Deha Sphuta             17 Vi 20' 25.00" Hast      3    Vi   Ge
Mrityu Sphuta           14 Sc 10' 24.70" Anu       4    Sc   Sc
Sookshma TriSphuta      16 Vi 38' 43.12" Hast      2    Vi   Ta
Tithi Sphuta            20 Vi 14' 41.18" Hast      4    Vi   Cn
Yoga Sphuta (Sun-Moon)  10 Cn 11' 24.97" Push      3    Cn   Li
Rahu Tithi Sphuta        7 Cn 37' 42.52" Push      2    Cn   Vi
Kshetra Sphuta          20 Vi 49' 40.52" Hast      4    Vi   Cn
Beeja Sphuta            14 Cn 07' 02.53" Push      4    Cn   Sc
TriSphuta                0 Pi 43' 26.08" PBha      4    Pi   Cn
ChatusSphuta            25 Cn 41' 47.97" Asre      3    Cn   Aq
PanchaSphuta            28 Pi 17' 52.39" Reva      4    Pi   Pi
V2                      29 Li 54' 22.60" Visa      3    Li   Sg
V3                      29 Sc 54' 22.60" Jye       4    Sc   Ta
V4                      29 Aq 54' 22.60" PBha      3    Aq   Ar
V5                      29 Pi 54' 22.60" Reva      4    Pi   Ta
V6                      29 Aq 54' 22.60" PBha      3    Aq   Sg
V7                      29 Sc 54' 22.60" Jye       4    Sc   Vi
V8                      29 Li 54' 22.60" Visa      3    Li   Le
V9                      29 Cn 54' 22.60" Asre      4    Cn   Cp
V10                     29 Aq 54' 22.60" PBha      3    Aq   Ar
V11                     29 Pi 54' 22.60" Reva      4    Pi   Cp
V12                     29 Aq 54' 22.60" PBha      3    Aq   Le
Kunda                   22 Ge 24' 30.83" Puna      1    Ge   Ar
Yoga Sphuta             13 Li 31' 24.97" Swat      3    Li   Aq
Avayoga Sphuta          20 Ar 11' 24.97" Bhar      3    Ar   Li



Surbhi Yogas:

Yoga                     Varga Yoga givers                     Results ascribed to yoga                         Brief definition of yoga

Sasa                     D-1   Sa                              Wandering leader of free spirit                  Saturn in a kendra in moolatrikona or own or exaltation sign
Vesi                     D-1   Ve                              Balanced, truthful and happy                     Planets other than Moon in 2nd from Sun
Nipuna (Budha-Aditya)    D-1   Su, Me                          Skillful, expert, well-known and respected       Sun and Mercury together or in mutual 7ths
Anaphaa                  D-1   Sa                              Comforts, good looks and character               Planets other than Sun in 12th from Moon
Gaja-Kesari              D-1   Mo, Ju                          Famous and virtuous                              Moon and Jupiter in mutual kendras
Adhi yoga                D-1   Me, Ju, Ve                      King, minister or an army chief                  Benefics in 6th, 7th and 8th from Moon
Paasa                    D-1   Naabhasa yoga - throughout life Talkative, characterless, may be imprisoned      Seven planets in 5 rasis
Raja/Dharma-Karmadhipati D-1   Mo, Me                          Dutiful and high achiever                        Conjunction, aspect or exchange of 9th/10th lords
Yogakaraka               D-1   Sa                              Success and achievements                         Same planet owns a kendra and a kona
Yogada (HL)              D-1   Su                              Wealth and prosperity                            Associated with lagna and HL (by aspect, conjunction or ownership)
Maha Yogada              D-1   Me                              Power, authority and wealth                      Associated with lagna, GL and HL (by aspect, conjunction or ownership)
Yogada (HL)              D-1   Ju                              Wealth and prosperity                            Associated with lagna and HL (by aspect, conjunction or ownership)
Yogada (GL)              D-1   Ve                              Power and authority                              Associated with lagna and GL (by aspect, conjunction or ownership)
Viparita Raja Yoga       D-1   Ve                              Success after pressures or someone else's losses 8th lord in 6th or 12th
Viparita Raja Yoga       D-1   Ju, Me                          Success after pressures or someone else's losses The 6th and 12th lords in conjunction or samasaptaka
Raja Sambandha           D-1   Ju, Ra                          An associate liked by a king                     Amatya karaka in a kendra/kona from atma karaka





Vimsopaka Dasa Varga (10) Shodasa Varga (16) Sapta Varga (7) Shad Varga (6)

Sun       12.10  (60.50%) 12.03  (60.13%)    13.40  (67.00%) 14.45  (72.25%)
Moon      15.98  (79.88%) 14.38  (71.88%)    15.13  (75.63%) 13.90  (69.50%)
Mars      11.57  (57.88%) 12.32  (61.63%)    13.95  (69.75%) 13.55  (67.75%)
Mercury   13.28  (66.38%) 12.20  (61.00%)    11.82  (59.13%) 11.70  (58.50%)
Jupiter   13.95  (69.75%) 13.98  (69.88%)    14.50  (72.50%) 15.15  (75.75%)
Venus     10.53  (52.63%) 11.53  (57.63%)    11.02  (55.12%) 11.95  (59.75%)
Saturn    11.28  (56.38%) 11.68  (58.38%)    11.95  (59.75%) 12.85  (64.25%)
Rahu      9.32  (46.63%)  8.95  (44.75%)     7.92  (39.63%)  6.75  (33.75%)
Ketu      10.25  (51.25%) 10.50  (52.50%)    11.35  (56.75%) 12.00  (60.00%)





Planet  Shadbala In rupas % Strength IshtaPhala KashtaPhala

Sun     455.94   7.60     151.98     22.60      34.19
Moon    404.63   6.74     112.40     43.97      9.18
Mars    343.58   5.73     114.53     25.04      32.00
Mercury 428.09   7.13     101.93     19.63      20.36
Jupiter 541.93   9.03     138.96     6.73       32.84
Venus   368.80   6.15     111.76     6.49       50.15
Saturn  327.51   5.46     109.17     38.29      18.59




Planet  Shadbala Rupas Sthana Bala Kala Bala DigBala Cheshta Bala DrigBala Naisargika Bala

Sun     7.60           150.01      202.01    51.64   34.01        -7.72    60.00
Moon    6.74           131.57      162.61    54.90   56.75        4.12     51.43
Mars    5.73           163.70      71.51     41.92   35.93        13.38    17.14
Mercury 7.13           209.62      154.59    37.16   7.39         -6.37    25.70
Jupiter 9.03           184.19      291.95    40.01   1.09         -9.59    34.28
Venus   6.15           124.48      177.27    16.43   16.17        -8.40    42.85
Saturn  5.46           180.32      63.46     26.38   48.36        0.42     8.57




Planet  Sthana Bala In rupas Uchcha Saptavargaja Oja Yugma Kendra Drekkana

Sun     150.01      2.50     15.01  90.00        15.00     30.00  0.00
Moon    131.57      2.19     34.07  67.50        0.00      30.00  0.00
Mars    163.70      2.73     17.45  101.25       15.00     15.00  15.00
Mercury 209.62      3.49     52.12  97.50        30.00     30.00  0.00
Jupiter 184.19      3.07     41.69  82.50        30.00     30.00  0.00
Venus   124.48      2.07     2.61   91.88        15.00     15.00  0.00
Saturn  180.32      3.01     30.32  60.00        15.00     60.00  15.00





