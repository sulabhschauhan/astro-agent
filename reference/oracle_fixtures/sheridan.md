# Oracle Reference — Sheridan

Built S127. READ-ONLY compilation of every validated value tied to
Sheridan already present in the repo (fixtures, JHora captures, the
AstroSage PDF, and diagnostic files). No values computed, converted, or
invented here — every row traces to a specific file/line or PDF page.
Row schema: `| item | value | unit | source | ayanamsa/mode | status | session |`.

Status legend: **oracle-confirmed** = sourced from AstroSage PDF / JHora
GUI / Drik Panchang / PVR book (not our own code); **production-output**
= our own `chart_calculator.py`/module output, needs independent oracle
before trusting; **unverified** = present in repo but flagged by its own
source file as not independently checked; **retracted** = superseded by
a later session's correction.

---

## 1. birth_data

| item | value | unit | source | ayanamsa/mode | status | session |
|---|---|---|---|---|---|---|
| Date of Birth | 27 May 1984 | date | `data/pdfs/Sheridan Kundli.pdf` p.2 ("Date of Birth 27 : 5 : 1984") | n/a | oracle-confirmed | S44.2c / S127 |
| Time of Birth | 08:00:00 | local clock time | `data/pdfs/Sheridan Kundli.pdf` p.2 ("Time of Birth 8 : 0 : 0") | n/a | oracle-confirmed | S127 |
| Place of Birth | Durban, South Africa | — | `data/pdfs/Sheridan Kundli.pdf` p.2 ("Place of Birth Durban") | n/a | oracle-confirmed | S127 |
| Latitude | 29:51:S (-29.8618250 decimal per geocode fixture) | deg:min:dir | PDF p.2 "Latitude 29 : 51 : S"; decimal cross-ref `tests/fixtures/geocoded_locations.json` via `docs/PROJECT_FACTS.md:27` | n/a | oracle-confirmed | S127 |
| Longitude | 31:1:E (31.0099090 decimal per geocode fixture) | deg:min:dir | PDF p.2 "Longitude 31 : 1 : E"; decimal cross-ref `tests/fixtures/geocoded_locations.json` via `docs/PROJECT_FACTS.md:27` | n/a | oracle-confirmed | S127 |
| Time Zone | 2.0 (SAST, UTC+2:00, fixed, no DST) | hours | PDF p.2 "Time Zone 2.0"; confirmed `docs/PROJECT_FACTS.md:27` | n/a | oracle-confirmed | S127 |
| Local Time Correction | 00:04:03 | h:m:s | `data/pdfs/Sheridan Kundli.pdf` p.2 | n/a | oracle-confirmed | S127 |
| LMT at Birth | 8:4:4 | h:m:s | `data/pdfs/Sheridan Kundli.pdf` p.2 | n/a | oracle-confirmed | S127 |
| GMT at Birth | 6:0:0 | h:m:s | `data/pdfs/Sheridan Kundli.pdf` p.2 | n/a | oracle-confirmed | S127 |
| Julian Day | 2445848 | JD (integer, AstroSage's own rounded display) | `data/pdfs/Sheridan Kundli.pdf` p.2 and p.3 | n/a | oracle-confirmed | S127 |
| `birth_jd_ut` (precise) | 2445847.750000 | JD UT | `diagnostics/vimshottari_year_length_S74.md` §7.2, via `diagnostics/drik_vimshottari_S76_sheridan.md:119` | n/a | production-output | S74/S76 |
| Sex | Male | — | PDF p.2 | n/a | oracle-confirmed | S127 |
| Day of Birth | Sunday | — | PDF p.2 | n/a | oracle-confirmed | S127 |
| Dasa Balance at birth | Ketu, 5Y 10M 13D | — | PDF p.2/p.3 | n/a | oracle-confirmed | S127 |

**Note on lat/lon rounding:** `tests/fixtures/shadbala_fixtures.py:417-418` and
`tests/calculations/strength/test_bhava_bala.py`-style call sites use a
slightly different rounding (`lat: -29.85, lon: 31.0167`) than the
geocoded-locations fixture (`-29.8618250 / 31.0099090`). Both are
sub-arcminute apart and neither contradicts the PDF's `29:51:S / 31:1:E`
— not raised as a CONFLICT, just noted as two independently-rounded
decimal renderings of the same DMS source.

---

## 2. ayanamsa (+ mode)

| item | value | unit | source | ayanamsa/mode | status | session |
|---|---|---|---|---|---|---|
| Ayanamsa (AstroSage PDF, printed) | 023-38-19 = 23.638611° | DMS / decimal | `data/pdfs/Sheridan Kundli.pdf` p.2 ("Ayanamsa 023-38-19", "Ayanamsa Name Lahiri") and p.3 ("Ayan 023-38-19", "Ayan Type Lahiri") | Lahiri | oracle-confirmed | S127 |
| Ayanamsa (`reference_charts.md`) | 23-38-19 = 23.63861° | DMS / decimal | `playbook_export/reference/reference_charts.md:26` | Lahiri (AstroSage) | oracle-confirmed | (undated, pre-S75) |
| Ayanamsa, Traditional Lahiri, JHora GUI capture | 23.639172° = 23-38-21.02 | decimal / DMS | `diagnostics/ayanamsa_mode_investigation_S75.md:50` (JD 2445847.750000) | Traditional Lahiri | oracle-confirmed | S75 |
| Ayanamsa, Traditional Lahiri, pyswisseph (`SIDM_LAHIRI`) | 23.639210° = 23-38-21.16 | decimal / DMS | `diagnostics/ayanamsa_mode_investigation_S75.md:50` | Traditional Lahiri (`SIDM_LAHIRI`) | production-output (verified to 0.137″ of the JHora GUI row above) | S75 |
| Ayanamsa, True Chitrapaksha, JHora GUI capture | 23.623658° = 23-37-25.17 | decimal / DMS | `diagnostics/ayanamsa_mode_investigation_S75.md:62` | True Chitrapaksha | oracle-confirmed | S75 |
| Ayanamsa, True Chitrapaksha, pyswisseph (`SIDM_TRUE_CITRA`) | 23.627844° = 23-37-40.24 | decimal / DMS | `diagnostics/ayanamsa_mode_investigation_S75.md:62` | True Chitrapaksha (`SIDM_TRUE_CITRA`) | production-output (diverges +15.068″ from the JHora GUI row above — documented Gap A1) | S75 |

**CONFLICT — stale reused ayanamsa value:** `docs/PROJECT_FACTS.md:57`
lists Sheridan's "Ayanamsa at birth" as `23°40'39.08" = 23.677522°` but
explicitly flags it **"NOT independently verified, see caveat below"**
— that file's own §3/§4 text (lines 76-88, echoed at `PROJECT_FACTS.md`
prose) establishes this figure is Sulabh's Session-27 GUI capture,
later shown at S75 to have been taken under **True Chitrapaksha at
Sulabh's 1988 epoch**, reused as boilerplate across all four charts
without a per-chart recapture. **Do not use this value for Sheridan.**
The S75 GUI-verified Sheridan-specific values (Traditional Lahiri
23.639172°, True Chitra 23.623658°, both above) supersede it, and the
AstroSage PDF's own printed `023-38-19` independently agrees with the
Traditional Lahiri row to ~2 arcsec.

| resolution | authority (file:line) | status |
|---|---|---|
| **S127 update:** the stale `docs/PROJECT_FACTS.md` figure (`23°40'39.08"`) is not a genuine second oracle for Sheridan — it is discredited True-Chitra-mode boilerplate reused across charts. Ratified replacement value = **production `SIDM_LAHIRI`, 23.639210° (23°38'21.16")**, per this same §2's own S75 rows above — verified to 0.137″ against the JHora GUI Traditional Lahiri capture (23.639172° = 23°38'21.02") at Sheridan's own JD 2445847.750000. No longer TBD: the S75 rows already present in this file were the answer, not a separate capture that still needed running. | `SESSION_LOG_ARCHIVE_S67-S104.md:1636-1637` ("jhora_{surbhi,sheridan,david}.md ayanamsa lines are template boilerplate (23-40-39.08 identical across 3 different birth epochs...). Open capture gap.") + `SESSION_LOG_ARCHIVE_S67-S104.md:1537-1538` ("pyswisseph SIDM_LAHIRI ≡ JHora Traditional Lahiri to 0.14\" at both epochs tested (Sulabh 1988, **Sheridan 1984**)"); consolidated as Gap O3 in `docs/KNOWN_DIVERGENCES.md`. | RATIFIED-DIVERGENCE (boilerplate discredited, replacement value = 23.639210°, verified) |

---

## 3. D1_planet_longitudes

### 3a. AstroSage PDF (`data/pdfs/Sheridan Kundli.pdf` p.3, "Planetary Positions" table) — oracle-confirmed, Lahiri

| Planet | Sign | Deg-Min-Sec in sign | Nakshatra | Pada |
|---|---|---|---|---|
| ASC | Taurus | 28-46-17 | Mrigasira | 2 |
| Sun | Taurus | 12-30-06 | Rohini | 1 |
| Moon | Aries | 02-09-16 | Ashvini | 1 |
| Mars [R] | Libra | 21-46-53 | Vishakha | 1 |
| Mercury | Aries | 18-29-54 | Bharani | 2 |
| Jupiter [R] | Sagittarius | 18-12-13 | Purvashadha | 2 |
| Venus | Taurus | 07-09-49 | Krittika | 4 |
| Saturn [R] | Libra | 17-44-51 | Swati | 4 |
| Rahu [R] | Taurus | 13-05-34 | Rohini | 1 |
| Ketu [R] | Scorpio | 13-05-34 | Anuradha | 3 |

(Uranus/Neptune/Pluto also printed on the same page but out of scope —
this project's calculation modules are BPHS/classical, 9-graha only.)

### 3b. JHora v8 fixture (`tests/calculations/test_jaimini_karakas.py:75-84`, Session 57) — oracle-confirmed, Lahiri, Mean Node — NOTE: MODE = True Chitrapaksha (confirmed by the appended True-Chitra table matching these values); superseded as matched-mode oracle by §3e.

| Planet | Sign | Deg-Min-Sec in sign |
|---|---|---|
| Sun | Taurus | 12-30-48.88 |
| Moon | Aries | 02-10-33.00 |
| Mars | Libra | 21-46-06.71 |
| Mercury | Aries | 18-30-40.55 |
| Jupiter | Sagittarius | 18-11-23.34 |
| Venus | Taurus | 07-10-42.19 |
| Saturn | Libra | 17-44-27.51 |
| Rahu | Taurus | 13-06-42.33 |

**CONFLICT — AstroSage PDF vs JHora v8 fixture, every planet:**
the two per-planet longitudes above differ by roughly 15″-70″ each
(e.g. Sun 12-30-06 PDF vs 12-30-48.88 JHora = +42.88″; Moon 02-09-16 PDF
vs 02-10-33.00 JHora = +77″; Rahu 13-05-34 PDF vs 13-06-42.33 JHora =
+68.33″). Sign placements agree exactly; nakshatra/pada boundaries are
unaffected at either source's precision (per `ayanamsa_mode_investigation_
S75.md` §5, no pada boundary is crossed by comparable sub-arcminute
ayanamsa shifts for this chart). Root cause not diagnosed here — could
be JHora vs AstroSage ephemeris/epoch differences, True Node vs Mean
Node convention (the JHora fixture states Mean Node explicitly; the PDF
does not state its Rahu/Ketu node convention), or independent rounding.
**Pick neither as canonical without further investigation** — recorded
as a CONFLICT per the instructing prompt, not resolved.

| resolution | authority (file:line) | status |
|---|---|---|
| **S127 update:** the AstroSage-vs-JHora pair IS now named directly. S75/S76 ratified a canonical oracle split for non-dasha quantities — D1 longitudes explicitly included — naming JHora primary and AstroSage secondary parity not expected. This resolves the D1 longitude class for Sheridan: JHora's §3b values are the ratified reference; AstroSage's §3a print is the divergent, non-oracle-primary side. | `SESSION_LOG_ARCHIVE_S67-S104.md:1561-1563` — "Canonical oracle reclassification: JHora primary for non-dasha (Ashtakavarga, karakas, D-charts, Panchanga); Drik primary for dasha row-0/AD boundaries going forward. AstroSage secondary parity."; consolidated as Gap O1 in `docs/KNOWN_DIVERGENCES.md`. | RATIFIED-DIVERGENCE |

**S127 RESOLVED:** the arcminute-scale gap was mode contamination (§3b
captured under True Chitrapaksha) + the Camp-Y apparent-position gap.
Matched-mode (Trad-Lahiri, §3e) residual ≤ 44.20″. Not an open
conflict.

### 3c. Sun/Moon sidereal longitude, pyswisseph production path (`diagnostics/ayanamsa_mode_investigation_S75.md:109`)

| item | value | unit | source | ayanamsa/mode | status | session |
|---|---|---|---|---|---|---|
| Moon sidereal longitude (Traditional Lahiri) | 2.15985235° = 2-09-35.47 (Aries) | decimal / DMS | `diagnostics/ayanamsa_mode_investigation_S75.md:109` | Traditional Lahiri (`SIDM_LAHIRI`) | production-output | S75 |
| Moon sidereal longitude (True Chitrapaksha) | 2.17121895° = 2-10-16.39 (Aries) | decimal / DMS | `diagnostics/ayanamsa_mode_investigation_S75.md:109` | True Chitrapaksha (`SIDM_TRUE_CITRA`) | production-output | S75 |

This is a *third* independent value for Moon longitude (2-09-35.47 or
2-10-16.39 depending on mode), close to but not identical to either
3a (02-09-16) or 3b (02-10-33.00) — adds to the CONFLICT above rather
than resolving it; both modes agree the nakshatra/pada stays Ashwini
pada 1.

### 3e. JHora v8 Traditional Lahiri (matched-mode) — RATIFIED D1 oracle (Gap O1)

Source: user-appended raw JHora v8 export at the end of this file
("Sheridan::" / "Traditional Lahiri:" block) — Sulabh-supplied, mode
explicitly labeled by the export itself, distinct from the
True-Chitrapaksha-mode §3b capture above (that block's own "true
Lahiri/Chitrapaksha" heading in the same appended export corroborates
§3b's Sun value, 12 Ta 30'48.88", exactly).

| Body | JHora Trad-Lahiri (DMS) | abs° | Production abs° | Δ arcsec | Status |
|---|---|---|---|---|---|
| Sun | Ta 12°29'53.04" | 42.498067 | 42.492407 | -20.37 | matched-mode residual |
| Moon | Ar 2°09'37.15" | 2.160319 | 2.159852 | -1.68 | matched-mode residual |
| Mars | Li 21°45'10.86" | 201.753017 | 201.753783 | 2.76 | matched-mode residual |
| Mercury | Ar 18°29'44.71" | 18.495753 | 18.488463 | -26.24 | matched-mode residual |
| Jupiter | Sg 18°10'27.50" | 258.174306 | 258.176373 | 7.44 | matched-mode residual |
| Venus | Ta 7°09'46.34" | 37.162872 | 37.150595 | -44.20 | matched-mode residual (max) |
| Saturn | Li 17°43'31.67" | 197.725464 | 197.728729 | 11.75 | matched-mode residual |
| Rahu | Ta 13°05'46.49" | 43.096247 | 43.096207 | -0.14 | node-convention match (~0) |
| Ketu | Sc 13°05'46.49" | 223.096247 | 223.096207 | -0.14 | node-convention match (~0) |

Matched-mode residual = documented Camp-Y apparent-position gap
(production geometric vs JHora apparent; S75/Gap A1). Max |Δ| = 44.20″
(Venus). NOT drift. Production values are NOT currently drift-guarded
by a Sheridan regression test (only David has one, at
`tests/regression/test_chart_calculator_characterization_david.py`) —
noted as a gap, not fixed here (out of this task's scope). Rahu/Ketu
Δ ≈ -0.14″ confirms Mean-Node convention matches between production and
this JHora capture (no Mean/True node mismatch to flag).

---

## 4. D1_sign_house_dignity

Source: `data/pdfs/Sheridan Kundli.pdf`, "Planet Consideration in
Astrology" section, pp.35-39 (per-planet dignity/lordship/house
narrative pages) — oracle-confirmed, whole-sign houses from Taurus
Lagna. Also cross-referenced against `tests/calculations/strength/
test_bhava_bala.py:100-104`'s hardcoded whole-sign house-to-sign map
for Sheridan (production-output test fixture, matches PDF exactly).

| Planet | Sign | Dignity (AstroSage term) | House lordship | Situated in house | Source (PDF page) |
|---|---|---|---|---|---|
| Sun | Taurus | Enemy sign | 4th | 1st | p.35 |
| Moon | Aries | Friendly sign | 3rd | 12th | p.35 |
| Mars | Libra | Neutral sign | 12th, 7th | 6th | p.36 |
| Mercury | Aries | Neutral sign | 2nd, 5th | 12th | p.36 |
| Jupiter | Sagittarius | Own sign | 8th, 11th | 8th | p.37 |
| Venus | Taurus | Own sign | 1st, 6th | 1st | p.37 |
| Saturn | Libra | **Exalted sign** | 9th, 10th | 6th | p.38 |
| Rahu | Taurus | (AstroSage prints "-", no dignity term) | (none printed) | 1st | p.38 |
| Ketu | Scorpio | (AstroSage prints "-", no dignity term) | (none printed) | 7th | p.39 |

### Lagna / Rasi

| item | value | source | status | session |
|---|---|---|---|---|
| Lagna sign | Taurus | PDF p.2/p.3; `reference_charts.md:27` | oracle-confirmed | S127 |
| Lagna longitude in sign | 28-46-17 | PDF p.3 table (§3a above) | oracle-confirmed | S127 |
| Lagna Lord | Venus | PDF p.2 ("Lagna Lord Ven") | oracle-confirmed | S127 |
| Lagna nakshatra/pada | Mrigasira, pada 2 | PDF p.3 table | oracle-confirmed | S127 |
| Rasi (Moon) sign | Aries | PDF p.2 ("Rasi Aries") | oracle-confirmed | S127 |
| Rasi Lord | Mars | PDF p.2 ("Rasi Lord Mar") | oracle-confirmed | S127 |

`docs/PROJECT_FACTS.md:89-93` flags Sheridan's Lagna nakshatra/pada as
"NOT captured in any repo fixture found" — that statement is now
**superseded by this session's direct PDF read** (p.3 table gives ASC
Mrigasira pada 2 explicitly); recorded here as NOT FOUND IN prior repo
fixtures but IS FOUND IN the source PDF itself.

### Chalit (house-cusp) table — AstroSage PDF p.3, distinct from whole-sign Bhava

| Bhav | Sign | Bhav Begin | Sign Mid | Bhav (Sign Mid) |
|---|---|---|---|---|
| 1 | Taurus | 16.07.26 | Taurus | 28.46.17 |
| 2 | Gemini | 16.07.26 | Cancer | 03.28.36 |
| 3 | Cancer | 20.49.45 | Leo | 08.10.55 |
| 4 | Leo | 25.32.05 | Virgo | 12.53.14 |
| 5 | Virgo | 25.32.05 | Libra | 08.10.55 |
| 6 | Libra | 20.49.45 | Scorpio | 03.28.36 |
| 7 | Scorpio | 16.07.26 | Scorpio | 28.46.17 |
| 8 | Sagittarius | 16.07.26 | Capricorn | 03.28.36 |
| 9 | Capricorn | 20.49.45 | Aquarius | 08.10.55 |
| 10 | Aquarius | 25.32.05 | Pisces | 12.53.14 |
| 11 | Pisces | 25.32.05 | Aries | 08.10.55 |
| 12 | Aries | 20.49.45 | Taurus | 03.28.36 |

Source: `data/pdfs/Sheridan Kundli.pdf` p.3, oracle-confirmed. Note this
is a Sripati/Porphyry-style Chalit table (unequal cusps), **not** the
whole-sign Bhava scheme `test_bhava_bala.py` and the dignity narrative
above use — the two are different house-division conventions present
in the same PDF and are not in conflict, just different systems (see
`docs/KNOWN_DIVERGENCES.md`'s Bhava Drishti Bala entry: "Sripati/
Porphyry Bhava Madhya").

---

## 5. vimshottari_MD_AD

### 5a. AstroSage PDF / fixture (`tests/fixtures/astrosage_vimshottari_fixtures.md:112-140`, Session 44.2c) — oracle-confirmed

| Lord | Duration | Start | End |
|---|---|---|---|
| KET | 7 Years | 27/5/84 | 10/4/90 |
| VEN | 20 Years | 10/4/90 | 10/4/10 |
| SUN | 6 Years | 10/4/10 | 10/4/16 |
| MON | 10 Years | 10/4/16 | 10/4/26 |
| MAR | 7 Years | 10/4/26 | 10/4/33 |
| RAH | 18 Years | 10/4/33 | 10/4/51 |
| JUP | 16 Years | 10/4/51 | 10/4/67 |
| SAT | 19 Years | 10/4/67 | 10/4/86 |
| MER | 17 Years | 10/4/86 | 10/4/03 |

(Full Antardasha rows for KET/VEN/SUN/MON/MAR/RAH MDs are in the source
file at the cited lines; not fully reproduced here — see source.)

### 5b. Drik Panchang capture (`diagnostics/drik_vimshottari_S76_sheridan.md`, S76) — oracle-confirmed

Row-0 (Ketu MD) end: **April 10, 1990, Tuesday at 21:06 SAST** →
JD 2447992.295833. Full 9-MD table (Ketu→Venus→Sun→Moon→Mars→Rahu→
Guru→Shani→Budha) is in the source file, matching 5a's lord sequence
and durations to the day (both round-trip the same 7/20/6/10/7/18/16/
19/17-year sequence); AstroSage prints D/M/YY dates without HH:MM,
Drik prints full local timestamps.

### 5c. Production output (`tests/fixtures/jhora_sheridan.md:29-39`, recomputed post-S76 `year_days` ship) — production-output, NOT oracle

| Lord | Start (local) | End (local) |
|---|---|---|
| Ket | 1984-05-27 08:00:00 | 1990-04-08 22:55:52 |
| Ven | 1990-04-08 22:55:52 | 2010-04-09 01:59:08 |
| Sun | 2010-04-09 01:59:08 | 2016-04-08 14:54:06 |
| Moon | 2016-04-08 14:54:06 | 2026-04-09 04:25:44 |
| Mars | 2026-04-09 04:25:44 | 2033-04-08 23:29:52 |
| Rah | 2033-04-08 23:29:52 | 2051-04-09 14:14:48 |
| Jup | 2051-04-09 14:14:48 | 2067-04-09 16:41:24 |
| Sat | 2067-04-09 16:41:24 | 2086-04-09 13:35:30 |
| Merc | 2086-04-09 13:35:30 | 2103-04-10 22:11:16 |

**IMPORTANT — this table is NOT a JHora GUI capture despite living in a
file named `jhora_sheridan.md`.** The file's own header note (lines 9-18)
states this table was recaptured to production's own `_calc_dasha()`
output after the S76 `year_days = 365.256363` ship, replacing an earlier
JHora GUI capture that this session did not recover (the file directs
readers to git history for the pre-S76 JHora values). **Status is
production-output, not oracle-confirmed**, despite the filename.

**CONFLICT / documented residual — production vs Drik (Gap D1,
`docs/KNOWN_DIVERGENCES.md:17-33`):** row-0 (Ketu MD) end date: 5c gives
1990-04-08 22:55:52 local; 5b (Drik) gives 1990-04-10 21:06:00 local —
a **-1.9237 day** residual (production lands earlier). This is a
**documented, accepted, non-bug divergence** (Gap D1), not an open
question — cited here only because both values are genuinely different
numbers for the same item and the task instructions require flagging
any such pair.

| resolution | authority (file:line) | status |
|---|---|---|
| Production's divergence from Drik (and the wider commercial/panchang camp) is an intentional, ratified design choice, not a bug: production follows a different root-cause camp on purpose. | `docs/KNOWN_DIVERGENCES.md:37-41`: "Root cause: Camp Y (formal mathematical astrology, Kapoor Institute of Astrology textbook Ch IX pp 115-117) vs Camp X (commercial software JHora/AstroSage/Drik applying an undocumented Moon correction). **Production aligns with Camp Y.** Reopen if evidence of classical primary-source correction surfaces." | RATIFIED-DIVERGENCE |

### 5d. Yogini Dasha (`tests/fixtures/jhora_sheridan.md:46-75`, JHora v8) — oracle-confirmed, unaffected by the S76 year_days ship

24-row Mahadasha table (Mars/Merc/Sat/Ven/Rah/Moon/Sun/Jup cycling,
1983-10-05 through 2091-10-05) — see source file for full table, not
reproduced here in full since it is 24 rows; first row: Mars
1983-10-05 00:39:49 → 1987-10-05 01:11:48.

---

## 6. combustion

Source: `tests/calculations/core/test_combustion.py:125-130`, "hand-falsified
AstroSage-longitude oracle", 6 rows for Sheridan — **oracle-confirmed**
(hand arithmetic derived from AstroSage longitudes, asserted against
production Swiss Ephemeris separation/retrograde output).

| Planet | Separation from Sun (deg) | Combust | Orb used (deg) | Retrograde |
|---|---|---|---|---|
| Moon | 40.347 | False | 12.0 | False |
| Mars | 159.280 | False | 17.0 | True |
| Mercury | 24.003 | False | 14.0 | False |
| Jupiter | 144.298 | False | 11.0 | True |
| Venus | 5.338 | **True** | 10.0 | False |
| Saturn | 155.246 | False | 15.0 | True |

(Sun has no self-row; combustion is Sun-relative only.)

---

## 7. shadbala_components (sthana/kala/etc.)

Source: `tests/fixtures/shadbala_fixtures.py:411-610`, "Source: AstroSage
Kundli PDF reports" — **oracle-confirmed**, all 7 planets, full
Sthana-Bala and Kala-Bala sub-component breakdown.

| Planet | ochcha | saptavargaja | ojayugma | kendra | drekkana | sthan_total | dig | nathonnatha | paksha | thribhaga | abda | masa | vara | hora | ayana | yuddha | kala_total | chesta | naisargika | drik | shadbala_virupa | shadbala_rupa | min_required | ratio | rank |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Sun | 49.17 | 58.12 | 15 | 60 | 1 | 182.29 | 40.13 | 40.58 | 46.55 | 0 | 0 | 0 | 45 | 60 | 114.14 | 0 | 306.27 | 52.05 | 60 | -16.68 | 624.06 | 10.40 | 5.0 | 2.08 | 1 |
| Moon | 49.72 | 45 | 0 | 15 | 1 | 109.72 | 6.42 | 19.42 | 26.90 | 0 | 0 | 0 | 0 | 0 | 17.35 | 0 | 63.67 | 13.45 | 51.42 | -2.88 | 241.79 | 4.03 | 6.0 | 0.67 | 7 |
| Mars | 27.93 | 50.62 | 30 | 15 | 1 | 123.55 | 12.96 | 19.42 | 46.55 | 0 | 0 | 0 | 0 | 0 | 8.99 | 0 | 74.96 | 57.39 | 17.16 | -24.47 | 261.56 | 4.36 | 5.0 | 0.87 | 6 |
| Mercury | 11.17 | 99.38 | 15 | 15 | 1 | 155.54 | 46.58 | 60 | 46.55 | 60 | 0 | 0 | 0 | 0 | 49.69 | 0 | 216.24 | 21.53 | 25.74 | -13.34 | 452.28 | 7.54 | 7.0 | 1.08 | 4 |
| Jupiter | 5.6 | 108.75 | 15 | 30 | 1 | 159.35 | 6.48 | 40.58 | 13.45 | 60 | 15 | 0 | 0 | 0 | 0.86 | 0 | 129.88 | 47.60 | 34.26 | -32.11 | 345.45 | 5.76 | 6.5 | 0.89 | 5 |
| Venus | 46.61 | 120 | 30 | 60 | 1 | 256.61 | 18.09 | 40.58 | 13.45 | 0 | 0 | 30 | 0 | 0 | 55.96 | 0 | 139.99 | 1.13 | 42.84 | -16.02 | 442.65 | 7.38 | 5.5 | 1.34 | 3 |
| Saturn | 59.25 | 106.88 | 15 | 15 | 1 | 211.12 | 46.33 | 19.42 | 46.55 | 0 | 0 | 0 | 0 | 0 | 49.37 | 0 | 115.35 | 51.46 | 8.58 | -24.95 | 407.88 | 6.80 | 5.0 | 1.36 | 2 |

**CONFLICT — this table's `drik` column vs the JHora Drik Bala oracle
below (§7a).** They mostly agree closely (e.g. Mars -24.47 vs -24.48,
Mercury -13.34 vs -13.44) but Sun and Moon diverge sharply — Sun -16.68
(AstroSage) vs -25.36 (JHora); Moon **-2.88 (AstroSage, malefic) vs
+0.58 (JHora, benefic) — a sign flip.** This is the project's own
**documented, locked** divergence (CLAUDE.md "Shadbala Drik Bala":
"AstroSage parity NOT expected on this component ... Moon classification
benefic when 90<=elongation<270 ... JHora primary"), and Sheridan is
named there as the specific chart that flips Moon's classification.
Not a new finding — recorded here only because the task requires
flagging value pairs that differ for the same item.

| resolution | authority (file:line or docstring) | status |
|---|---|---|
| JHora is the ratified sole oracle for Drik Bala; AstroSage parity on this specific component is explicitly not expected/not checked. Sheridan is the specific chart the module docstring itself cites for the Moon sign-flip edge case. | `agent/calculations/strength/drik_bala.py:11-18` (module docstring, PROVENANCE CAVEAT): "**AstroSage parity has NOT been checked against this version. Treat as JHora-parity-only.**"; same file's "SHERIDAN EDGE CASE" comment at lines 20-29 names Sheridan by name for this exact Moon/Mercury classification behavior. Corroborated by `CLAUDE.md:249`: "**AstroSage parity NOT expected on this component** ... **JHora primary**." | RATIFIED-DIVERGENCE |

### 7a. JHora v8 Drik Bala (`tests/calculations/strength/test_drik_bala.py:200-203`) — oracle-confirmed, JHora primary per the lock above

| Planet | Drik Bala (Virupa) |
|---|---|
| Sun | -25.36 |
| Moon | +0.58 |
| Mars | -24.48 |
| Mercury | -13.44 |
| Jupiter | -31.95 |
| Venus | -22.69 |
| Saturn | -24.95 |

### 7b. Bhava Dig Bala, AstroSage (`tests/fixtures/bhava_dig_bala_astrosage.py:26-29`) — oracle-confirmed

| House | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Virupa | 30.0 | 40.0 | 10.0 | 30.0 | 20.0 | 50.0 | 60.0 | 40.0 | 20.0 | 0.0 | 50.0 | 40.0 |

### 7c. Bhava Drishti Bala, AstroSage (`tests/calculations/strength/test_bhava_bala.py:436-437`) — oracle-confirmed

| House | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Virupa | -11.33 | 0.40 | -19.33 | 35.35 | -49.17 | -60.93 | -50.71 | -52.37 | -17.48 | 36.25 | 16.59 | 17.99 |

Test file comment flags Sheridan as "the only chart in this set where
Moon classifies malefic" — consistent with the §7 CONFLICT note above.

---

## 8. ashtakavarga_BAV_SAV

### 8a. JHora v8 (`tests/fixtures/jhora_ashtakavarga_cross_charts.md:133-172`, Session 54) — oracle-confirmed, checksum-verified

| Planet | Ar | Ta | Ge | Cn | Le | Vi | Li | Sc | Sg | Cp | Aq | Pi | Total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Sun | 5 | 4 | 5 | 3 | 6 | 2 | 5 | 4 | 2 | 5 | 4 | 3 | 48 |
| Moon | 2 | 0 | 3 | 6 | 4 | 3 | 5 | 4 | 5 | 4 | 7 | 6 | 49 |
| Mars | 3 | 4 | 3 | 4 | 3 | 4 | 6 | 2 | 1 | 2 | 4 | 3 | 39 |
| Mercury | 4 | 6 | 5 | 5 | 5 | 4 | 5 | 4 | 3 | 6 | 3 | 4 | 54 |
| Jupiter | 2 | 5 | 4 | 4 | 5 | 5 | 5 | 3 | 5 | 6 | 7 | 5 | 56 |
| Venus | 3 | 4 | 6 | 5 | 7 | 5 | 1 | 1 | 7 | 4 | 4 | 5 | 52 |
| Saturn | 2 | 3 | 2 | 2 | 4 | 3 | 3 | 3 | 4 | 1 | 6 | 6 | 39 |
| Lagna | 3 | 3 | 3 | 6 | 5 | 4 | 5 | 1 | 4 | 5 | 4 | 6 | 49 |
| **SAV** | 21 | 26 | 28 | 29 | 34 | 26 | 30 | 21 | 27 | 28 | 35 | 32 | **337** |

All 8 row checksums and 12 column checksums verified at transcription
time (source file lines 153-172); reference = Taurus (Sheridan's real
natal Lagna), independently cross-checked against an invalid
Aries-reference capture per the source file's header note.

### 8b. AstroSage PDF (`data/pdfs/Sheridan Kundli.pdf` p.3, "Ashtakvarga Table") — this session's own pdfplumber extraction, **unverified**

| Planet | Ar | Ta | Ge | Cn | Le | Vi | Li | Sc | Sg | Cp | Aq | Pi | Total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Sun | 5 | 4 | 5 | 3 | 6 | 2 | 5 | 4 | 2 | 5 | 4 | 3 | — |
| Moon | 2 | 0 | 4 | 6 | 4 | 3 | 5 | 5 | 4 | 3 | 7 | 6 | — |
| Mars | 3 | 4 | 3 | 4 | 3 | 4 | 6 | 2 | 1 | 2 | 4 | 3 | — |
| Mercury | 4 | 6 | 5 | 5 | 5 | 4 | 5 | 4 | 3 | 6 | 3 | 4 | — |
| Jupiter | 2 | 5 | 4 | 4 | 5 | 5 | 5 | 3 | 5 | 6 | 7 | 5 | — |
| Venus | 3 | 4 | 6 | 5 | 7 | 5 | 1 | 1 | 7 | 3 | 5 | 5 | — |
| Saturn | 2 | 3 | 2 | 2 | 4 | 3 | 3 | 3 | 4 | 1 | 6 | 6 | — |
| **Total (as printed)** | 21 | 26 | 29 | 29 | 34 | 26 | 30 | 22 | 26 | 26 | 36 | 32 | 337 |

**CONFLICT — 8a (JHora, checksummed) vs 8b (this session's raw
pdfplumber read of the AstroSage PDF):** Moon's row differs at
Gemini (4 vs 3) and Sagittarius (4 vs 5); Venus's row differs at
Capricorn (3 vs 4) and Aquarius (5 vs 4); the printed PDF "Total" row
also differs from 8a's SAV row at 5 signs (Cn, Sc, Sg, Cp, Aq) despite
both grand-totaling 337. Given 8a is independently checksum-verified
(row + column + grand total, per its own source file) and this
session's PDF table extraction is raw/unverified pdfplumber text with
no cross-check performed, **8a should be treated as the more reliable
value** — but both are recorded per the task's CONFLICT instruction
rather than silently preferring one. Possible cause: the PDF's own
"Total" row may already be a genuine 8-source SAV (7 planets + Lagna)
while its displayed per-planet rows are BAV-only, making a literal
column-sum-vs-printed-total mismatch expected rather than a
transcription error — not confirmed here.

| resolution | authority (file:line or docstring) | status |
|---|---|---|
| Parasara convention locked, JHora oracle. `ashtakavarga.py`'s module docstring names exactly three known Parasara/Varahamihira convention-choice cells. Applied to Sheridan's own chart (Moon in Aries, Mars in Libra, Jupiter in Sagittarius): **9th-from-Moon** = 9th-from-Aries = **Sagittarius** — matches the Moon-Sagittarius discrepancy in this block. **4th-from-Mars** = 4th-from-Libra = **Capricorn** — matches the Venus-Capricorn discrepancy in this block. For these two cells, JHora's value (8a) is the ratified Parasara-convention value; the raw PDF read's differing value is the divergent one. **Coverage caveat:** the docstring's third named type, 2nd-from-Jupiter (Jupiter in Sagittarius → 2nd-from-Sagittarius = Capricorn), does not match either of the block's other two discrepancies (Moon-Gemini, Venus-Aquarius) — those two remain unaddressed by this docstring and are not adjudicated here. **S127 reclassification:** the printed-total-row mismatch is removed from this OPEN list — it is not an independent value at all, it is DERIVED (arithmetic sum of the 7 planet BAV rows + Lagna), so its mismatch is fully explained by, and does not add to, the Moon/Venus row mismatches already accounted for above; it carries no separate adjudication need. | `agent/calculations/ashtakavarga/ashtakavarga.py:12-19` (named conflict-cell list) and `:24-25` ("Parasara convention confirmed end-to-end") | RATIFIED-DIVERGENCE for Moon-Sagittarius and Venus-Capricorn; DERIVED (sum of BAV rows, not independent) for the printed-total-row mismatch, removed from OPEN; OPEN — needs PVR bindu-table hand-computation — for Moon-Gemini and Venus-Aquarius |

---

## 9. jaimini_karakas

Source: `tests/calculations/test_jaimini_karakas.py:75-88`, Layer A
JHora v8 real-chart oracle, Session 57 — **oracle-confirmed**.

| Karaka | Planet |
|---|---|
| AK (Atma Karaka) | Mars |
| AmK (Amatya Karaka) | Mercury |
| BK (Bhratri Karaka) | Jupiter |
| MK (Matri Karaka) | Saturn |
| PiK (Pitri Karaka) | Rahu |
| PK (Putra Karaka) | Sun |
| GK (Gnati Karaka) | Venus |
| DK (Dara Karaka) | Moon |

Test name for this row: `test_sheridan_rahu_mid_rank` — flags Rahu's
karaka rank as the specific edge condition this fixture exercises.
Underlying longitudes used to derive this ranking are §3b above
(the JHora fixture longitudes, same source file).

---

## 10. Any other validated fixture

### 10a. Retrograde flags (planet-level, cross-referenced from combustion §6 + PDF §3a)

| Planet | Retrograde | Source |
|---|---|---|
| Mars | True | `test_combustion.py:126` (oracle) + PDF "[R]" marker p.3 |
| Jupiter | True | `test_combustion.py:128` (oracle) + PDF "[R]" marker p.3 |
| Saturn | True | `test_combustion.py:130` (oracle) + PDF "[R]" marker p.3 |
| Rahu | (nodes always retrograde by convention) | PDF "[R]" marker p.3 |
| Ketu | (nodes always retrograde by convention) | PDF "[R]" marker p.3 |
| Moon, Mercury, Venus | False | `test_combustion.py:125,127,129` (oracle) |

### 10b. Session-45-era memory file note (out-of-band, cross-check only)

`C:\Users\sulab\.claude\projects\...\memory\project_retrograde_flag_fix_
session51.md` (this assistant's own persistent memory, NOT a repo file)
records that the retrograde flag was "always False (missing FLG_SPEED),
now fixed" as of Session 51, with "real retro map for the 4 canonical
charts" — consistent with §10a's non-trivial Mars/Jupiter/Saturn=True
values existing at all (a broken flag would show all-False). Cited for
completeness per the instructing prompt's "diagnostics that recorded a
ratified value" search scope; this is a memory file, not a repo
fixture, so not assigned its own status row.

---

## 4-Chart PDF Table Coverage Note

`tests/fixtures/astrosage_vimshottari_fixtures.md:27-32` confirms all
4 canonical charts (Sulabh, Surbhi, Sheridan, David) have a committed
AstroSage PDF in `data/pdfs/`, captured/extracted 2026-07-02 (Sheridan:
`data/pdfs/Sheridan Kundli.pdf`, 56 pages). This session additionally
opened the Sheridan PDF directly (pdfplumber) for the D1 positions,
dignity narrative, Chalit table, and raw Ashtakavarga table sections
that are NOT captured in any existing `.md` fixture — those are the
"this session's own pdfplumber extraction" rows above (§4 dignity
table, §4 Chalit table, §8b).

## Categories confirmed NOT FOUND in any repo fixture for Sheridan

- **Full Shadbala Rupa totals with graha ranking narrative text** — the
  numeric components exist (§7) but no fixture captures AstroSage's own
  prose ranking commentary; PDF page 50 has a Shadbala section not read
  in full this session (budget — flagged, not fabricated).
- **Ishta/Kashta Phala per planet** — no Sheridan-specific numeric
  fixture found (module and tests reference Sheridan by name for
  parametrization but no discrete oracle table was located in the time
  available this session).
- **Varshaphal/Muntha/Sahams for Sheridan** — `playbook_export/reference/
  reference_charts.md:28-31` gives the 2026 Varshaphal epoch/ayanamsa/
  Lagna/Rasi/Muntha only; no full Varshaphal chart table found.
- **D2-D60 varga chart full tables** — the PDF's Shodashvarga Table
  (p.40) exists but was not transcribed into this reference file
  (out of the 10 requested categories; noted for a future pass if
  needed).






Sheridan::

true Lahiri/Chitrapaksha

Body                    Longitude        Nakshatra Pada Rasi Navamsa

Lagna                   28 Ta 47' 15.66" Mrig      2    Ta   Vi
Sun - PK                12 Ta 30' 48.88" Rohi      1    Ta   Ar
Moon - DK                2 Ar 10' 33.00" Aswi      1    Ar   Ar
Mars (R) - AK           21 Li 46' 06.71" Visa      1    Li   Ar
Mercury - AmK           18 Ar 30' 40.55" Bhar      2    Ar   Vi
Jupiter (R) - BK        18 Sg 11' 23.34" PSha      2    Sg   Vi
Venus - GK               7 Ta 10' 42.19" Krit      4    Ta   Pi
Saturn (R) - MK         17 Li 44' 27.51" Swat      4    Li   Pi
Rahu - PiK              13 Ta 06' 42.33" Rohi      1    Ta   Ar
Ketu                    13 Sc 06' 42.33" Anu       3    Sc   Li
Maandi                   8 Li 19' 01.53" Swat      1    Li   Sg
Gulika                  25 Vi 04' 16.83" Chit      1    Vi   Le
Bhava Lagna              1 Ge 15' 21.33" Mrig      3    Ge   Li
Hora Lagna              20 Ge 02' 54.17" Puna      1    Ge   Ar
Ghati Lagna             16 Le 25' 32.70" PPha      1    Le   Le
Vighati Lagna           28 Ta 18' 45.36" Mrig      2    Ta   Vi
Varnada Lagna           28 Le 47' 15.66" UPha      1    Le   Li
Sree Lagna              27 Cn 32' 06.54" Asre      4    Cn   Pi
Pranapada Lagna         28 Cp 21' 45.76" Dhan      2    Cp   Vi
Indu Lagna               2 Aq 10' 33.00" Dhan      3    Aq   Li
Bhrigu Bindu            22 Li 38' 37.66" Visa      1    Li   Ar
Dhooma                  25 Vi 50' 48.88" Chit      1    Vi   Le
Vyatipata                4 Li 09' 11.12" Chit      4    Li   Sc
Parivesha                4 Ar 09' 11.12" Aswi      2    Ar   Ta
Indra Chapa             25 Pi 50' 48.88" Reva      3    Pi   Aq
Upaketu                 12 Ar 30' 48.88" Aswi      4    Ar   Cn
Kaala                   20 Ta 44' 28.94" Rohi      4    Ta   Cn
Mrityu                  26 Ge 48' 23.23" Puna      3    Ge   Ge
Artha Prahara           18 Cn 25' 56.08" Asre      1    Cn   Sg
Yama Ghantaka           13 Le 34' 46.43" PPha      1    Le   Le
Prana Sphuta            19 Cn 00' 35.12" Asre      1    Cn   Sg
Deha Sphuta             12 Li 28' 40.79" Swat      2    Li   Cp
Mrityu Sphuta            8 Li 00' 46.66" Swat      1    Li   Sg
Sookshma TriSphuta       9 Le 30' 02.57" Magh      3    Le   Ge
Tithi Sphuta            19 Aq 39' 44.11" Sata      4    Aq   Pi
Yoga Sphuta (Sun-Moon)  14 Ta 41' 21.88" Rohi      2    Ta   Ta
Rahu Tithi Sphuta        0 Ar 35' 53.45" Aswi      1    Ar   Ar
Kshetra Sphuta          12 Cn 08' 03.05" Push      3    Cn   Li
Beeja Sphuta             7 Pi 52' 54.41" UBha      2    Pi   Vi
TriSphuta               26 Sc 02' 05.48" Jye       3    Sc   Aq
ChatusSphuta             8 Cp 32' 54.36" USha      4    Cp   Pi
PanchaSphuta            21 Aq 39' 36.69" PBha      1    Aq   Ar
V2                      28 Vi 47' 15.66" Chit      2    Vi   Cn
V3                      28 Sg 47' 15.66" USha      1    Sg   Aq
V4                      28 Ta 47' 15.66" Mrig      2    Ta   Pi
V5                      28 Ar 47' 15.66" Krit      1    Ar   Aq
V6                      28 Ta 47' 15.66" Mrig      2    Ta   Cn
V7                      28 Sg 47' 15.66" USha      1    Sg   Li
V8                      28 Vi 47' 15.66" Chit      2    Vi   Cn
V9                      28 Le 47' 15.66" UPha      1    Le   Aq
V10                     28 Cp 47' 15.66" Dhan      2    Cp   Pi
V11                     28 Ar 47' 15.66" Krit      1    Ar   Aq
V12                     28 Cp 47' 15.66" Dhan      2    Cp   Cn
Kunda                   21 Ge 48' 08.43" Puna      1    Ge   Ar
Yoga Sphuta             18 Le 01' 21.88" PPha      2    Le   Vi
Avayoga Sphuta          24 Aq 41' 21.88" PBha      2    Aq   Ta



Traditional Lahiri:

Body                    Longitude        Nakshatra Pada Rasi Navamsa

Lagna                   28 Ta 46' 19.82" Mrig      2    Ta   Vi
Sun - PK                12 Ta 29' 53.04" Rohi      1    Ta   Ar
Moon - DK                2 Ar 09' 37.15" Aswi      1    Ar   Ar
Mars (R) - AK           21 Li 45' 10.86" Visa      1    Li   Ar
Mercury - AmK           18 Ar 29' 44.71" Bhar      2    Ar   Vi
Jupiter (R) - BK        18 Sg 10' 27.50" PSha      2    Sg   Vi
Venus - GK               7 Ta 09' 46.34" Krit      4    Ta   Pi
Saturn (R) - MK         17 Li 43' 31.67" Swat      4    Li   Pi
Rahu - PiK              13 Ta 05' 46.49" Rohi      1    Ta   Ar
Ketu                    13 Sc 05' 46.49" Anu       3    Sc   Li
Maandi                   8 Li 18' 05.69" Swat      1    Li   Sg
Gulika                  25 Vi 03' 20.98" Chit      1    Vi   Le
Bhava Lagna              1 Ge 14' 25.48" Mrig      3    Ge   Li
Hora Lagna              20 Ge 01' 58.33" Puna      1    Ge   Ar
Ghati Lagna             16 Le 24' 36.86" PPha      1    Le   Le
Vighati Lagna           28 Ta 17' 49.51" Mrig      2    Ta   Vi
Varnada Lagna           28 Le 46' 19.82" UPha      1    Le   Li
Sree Lagna              27 Cn 06' 02.90" Asre      4    Cn   Pi
Pranapada Lagna         28 Cp 20' 49.91" Dhan      2    Cp   Vi
Indu Lagna               2 Aq 09' 37.15" Dhan      3    Aq   Li
Bhrigu Bindu            22 Li 37' 41.82" Visa      1    Li   Ar
Dhooma                  25 Vi 49' 53.04" Chit      1    Vi   Le
Vyatipata                4 Li 10' 06.96" Chit      4    Li   Sc
Parivesha                4 Ar 10' 06.96" Aswi      2    Ar   Ta
Indra Chapa             25 Pi 49' 53.04" Reva      3    Pi   Aq
Upaketu                 12 Ar 29' 53.04" Aswi      4    Ar   Cn
Kaala                   20 Ta 43' 33.09" Rohi      4    Ta   Cn
Mrityu                  26 Ge 47' 27.38" Puna      3    Ge   Ge
Artha Prahara           18 Cn 25' 00.24" Asre      1    Cn   Sg
Yama Ghantaka           13 Le 33' 50.58" PPha      1    Le   Le
Prana Sphuta            18 Cn 55' 00.06" Asre      1    Cn   Sg
Deha Sphuta             12 Li 20' 18.19" Swat      2    Li   Cp
Mrityu Sphuta            7 Li 53' 19.90" Swat      1    Li   Sg
Sookshma TriSphuta       9 Le 08' 38.15" Magh      3    Le   Ge
Tithi Sphuta            19 Aq 39' 44.11" Sata      4    Aq   Pi
Yoga Sphuta (Sun-Moon)  14 Ta 39' 30.19" Rohi      2    Ta   Ta
Rahu Tithi Sphuta        0 Ar 35' 53.45" Aswi      1    Ar   Ar
Kshetra Sphuta          12 Cn 05' 15.51" Push      3    Cn   Li
Beeja Sphuta             7 Pi 50' 06.88" UBha      2    Pi   Vi
TriSphuta               25 Sc 59' 17.95" Jye       3    Sc   Aq
ChatusSphuta             8 Cp 29' 10.98" USha      4    Cp   Pi
PanchaSphuta            21 Aq 34' 57.47" PBha      1    Aq   Ar
V2                      28 Vi 46' 19.82" Chit      2    Vi   Cn
V3                      28 Sg 46' 19.82" USha      1    Sg   Aq
V4                      28 Ta 46' 19.82" Mrig      2    Ta   Pi
V5                      28 Ar 46' 19.82" Krit      1    Ar   Aq
V6                      28 Ta 46' 19.82" Mrig      2    Ta   Cn
V7                      28 Sg 46' 19.82" USha      1    Sg   Li
V8                      28 Vi 46' 19.82" Chit      2    Vi   Cn
V9                      28 Le 46' 19.82" UPha      1    Le   Aq
V10                     28 Cp 46' 19.82" Dhan      2    Cp   Pi
V11                     28 Ar 46' 19.82" Krit      1    Ar   Aq
V12                     28 Cp 46' 19.82" Dhan      2    Cp   Cn
Kunda                   20 Ge 32' 45.04" Puna      1    Ge   Ar
Yoga Sphuta             17 Le 59' 30.19" PPha      2    Le   Vi
Avayoga Sphuta          24 Aq 39' 30.19" PBha      2    Aq   Ta

