# Oracle Reference — David

**Purpose:** consolidated, per-person oracle reference for David, built
READ-ONLY from repo fixtures, diagnostics, and the in-repo AstroSage PDF
(`data/pdfs/David Kundli.pdf`, extracted this session via `pdfplumber`).
No value here is computed, converted, or inferred by this session — every
row is a verbatim transcription from a cited file/page, or an existing
fixture value copied verbatim. Where two sources disagree on the same
item, both are recorded in a CONFLICT row and neither is picked.

**Session:** S127. **PDF extraction method:** `pdfplumber` (not `pypdf`),
56 pages, full-text dump to a scratch file, greps against the dump for
each section below (page numbers are the PDF's own printed footer
`Page No. N`, matching pdfplumber's page index).

Status legend: `oracle-confirmed` = source is AstroSage/JHora/PVR/Drik
Panchang; `production-output` = this codebase's own calculator output
(needs oracle before trusting); `retracted` = a value later corrected/
superseded in its own source file; `unverified` = flagged by the
project's own prior session as not independently confirmed.

---

## 1. birth_data

| item | value | unit | source (file:line or PDF p.N) | ayanamsa/mode | status | session |
|---|---|---|---|---|---|---|
| Name | David | — | PDF p.2 ("Name David") | n/a | oracle-confirmed | S44.2c/S127 |
| Sex | Male | — | PDF p.2 | n/a | oracle-confirmed | S127 |
| Date of Birth | 19 : 1 : 1976 | D:M:Y | PDF p.2 | n/a | oracle-confirmed | S127 |
| Time of Birth | 22 : 0 : 0 | H:M:S | PDF p.2 | n/a | oracle-confirmed | S127 |
| Day of Birth | Monday | — | PDF p.2 | n/a | oracle-confirmed | S127 |
| Place of Birth | London | — | PDF p.2 | n/a | oracle-confirmed | S127 |
| Time Zone | 0.0 | hours | PDF p.2 | n/a | oracle-confirmed | S127 |
| Latitude | 51 : 30 : N | deg:min | PDF p.2 | n/a | oracle-confirmed | S127 |
| Longitude | 0 : 7 : W | deg:min | PDF p.2 | n/a | oracle-confirmed | S127 |
| Local Time Correction | 00.00.28 | h.m.s | PDF p.2 | n/a | oracle-confirmed | S127 |
| War Time Correction | 00.00.00 | h.m.s | PDF p.2 | n/a | oracle-confirmed | S127 |
| LMT at Birth | 21:59:32 | H:M:S | PDF p.2 | n/a | oracle-confirmed | S127 |
| GMT at Birth | 22:0:0 | H:M:S | PDF p.2 | n/a | oracle-confirmed | S127 |
| Julian Day | 2442797 | JD (integer, AstroSage's own truncated display) | PDF p.2 | n/a | oracle-confirmed | S127 |
| Ishtkaal | 035-09-15 | deg-min-sec | PDF p.2 | n/a | oracle-confirmed | S127 |
| Dasa Balance (Ketu) | 0 Y 10 M 17 D | Y/M/D | PDF p.2 | n/a | oracle-confirmed | S127 |
| Geocoded Latitude | 51.5074456 | decimal deg | `tests/fixtures/geocoded_locations.json:29` ("London, UK") | n/a | oracle-confirmed (Nominatim/OSM, distinct geocoder from AstroSage's own 51:30N) | S44.2c |
| Geocoded Longitude | -0.1277653 | decimal deg | `tests/fixtures/geocoded_locations.json:30` | n/a | oracle-confirmed (Nominatim/OSM) | S44.2c |
| Canonical calculate_chart() input | `("David", "19 Jan 1976", "22:00", "London, UK")` | — | `tests/calculations/strength/test_drik_bala.py:222` (`_CHART_ARGS["david"]`), byte-identical at ~14+ other call sites per `diagnostics/vimshottari_year_length_S74.md` §7.3 | n/a | oracle-confirmed (canonical fixture, cross-verified) | S74 |

**CONFLICT — birth location geocoder used for lat/lon:**
- AstroSage PDF (p.2): `51:30:N, 0:7:W` (= 51.5, -0.1167).
- App's own geocoder (Nominatim/OSM, `geocoded_locations.json`): `51.5074456, -0.1277653`.
- JHora Ashtakavarga capture (`tests/fixtures/jhora_david_ashtakavarga.md`, header) used yet a **third** location: "London Colney, United Kingdom (0 W 17' 00", 51 N 43' 00")" — NOT London itself. That fixture's own header already flags this as unreconciled.
- Pick nothing; all three are recorded above/below with their own citation.

| resolution | authority (file:line) | status |
|---|---|---|
| For production calculation purposes, the app's own Nominatim/OSM geocoder output is canonical — not AstroSage's or JHora's hand-typed/differently-geocoded coordinates. This resolves WHICH lat/lon `calculate_chart()` uses; it does not declare AstroSage's or JHora's own report/capture coordinates "wrong" for their own purposes. | `docs/PROJECT_FACTS.md:18-21`: "lat/lon per `tests/fixtures/geocoded_locations.json` (the app's own geocoder output — **canonical for production calculation**, may differ by ~0.01° from a value hand-typed into an external GUI, see Sulabh note)." | RATIFIED-DIVERGENCE |

---

## 2. ayanamsa (+mode)

| item | value | unit | source (file:line or PDF p.N) | ayanamsa/mode | status | session |
|---|---|---|---|---|---|---|
| Ayanamsa (degrees, AstroSage) | 023-31-19 | deg-min-sec | PDF p.2 ("Ayanamsa 023-31-19") | Lahiri (PDF p.2: "Ayanamsa Name Lahiri") | oracle-confirmed | S127 |
| Obliquity | 023-26-33 | deg-min-sec | PDF p.2 | n/a | oracle-confirmed | S127 |
| Sidereal Time | 05.53.13 | h.m.s | PDF p.2 | n/a | oracle-confirmed | S127 |
| Ayanamsa (JHora fixture, David) | 23-40-39.08 | deg-min-sec | `tests/fixtures/jhora_david.md:4` | Lahiri | **unverified — flagged boilerplate**, per `docs/PROJECT_FACTS.md` §2 caveat: this exact value is byte-identical across all 4 charts' JHora fixtures despite ~50.3"/yr Lahiri precession meaning a genuine 1976-vs-1992 (David vs Surbhi) capture should differ by ~13-14 arcmin. Only Sulabh's figure is treated as a real independent GUI capture. | S74/S75 |
| Ayanamsa cross-implementation note (pyswisseph SIDM_LAHIRI vs JHora) | ~1 arcmin / 57.77″ flat gap across all 4 reference charts | arcsec | `tests/fixtures/jhora_david_ashtakavarga.md:6` | Lahiri | oracle-confirmed (documented cross-implementation constant, SESSION_LOG Session 19 / `playbook_export/decisions/ayanamsa-investigation.md`) | S19/S54 |

**CONFLICT — Ayanamsa value for David:**
- AstroSage PDF (p.2, chart-specific print): **23°31'19"**.
- JHora fixture (`jhora_david.md:4`): **23°40'39.08"** — but this codebase's own `docs/PROJECT_FACTS.md` §2 already flags this specific value as suspect boilerplate (identical across all 4 charts), not a genuine independent JHora capture for David.
- Pick nothing. Note the JHora figure's own credibility is already in question per the project's own prior finding — do not treat it as a clean "second oracle" without re-capturing.

| resolution | authority (file:line) | status |
|---|---|---|
| **S127 update:** the JHora fixture's `23°40'39.08"` is not a genuine second oracle for David — it is discredited True-Chitra-mode boilerplate reused across charts. Ratified replacement value = **production `SIDM_LAHIRI`, 23.5226° (23°31'21")**, captured from this session's own `calculate_chart()` run for David (`meta.ayanamsha_lahiri`; see `diagnostics/s127_chart_calculator_david_capture.py`, whose output landed in a since-overwritten `diagnostics/latest_run.md` pass this same session). This value is production-output, not a third-party oracle read — recorded here because it is the ratified reference going forward, not because it independently confirms AstroSage's print. | `SESSION_LOG_ARCHIVE_S67-S104.md:1636-1637` ("jhora_{surbhi,sheridan,david}.md ayanamsa lines are template boilerplate (23-40-39.08 identical across 3 different birth epochs...). Open capture gap.") + `SESSION_LOG_ARCHIVE_S67-S104.md:1537-1538` ("pyswisseph SIDM_LAHIRI ≡ JHora Traditional Lahiri to 0.14\" at both epochs tested"); consolidated as Gap O3 in `docs/KNOWN_DIVERGENCES.md`. | RATIFIED-DIVERGENCE |

---

## 3. D1_planet_longitudes

### 3a. AstroSage PDF p.3 — Planetary Positions table (verbatim; column header printed "Latitude" but values are clearly degree-minute-second position-in-sign, not ecliptic latitude — captured as printed, not relabeled)

| Planet | Sign | "Latitude" column (deg-min-sec in sign) | Nakshatra | Pada | Retrograde |
|---|---|---|---|---|---|
| ASC (Lagna) | Virgo | 05-16-57 | Uttaraphal(guni) | 3 | — |
| Sun | Capricorn | 05-26-58 | Uttarashadha | 3 | no |
| Moon | Leo | 11-39-21 | Magha | 4 | no |
| Mars | Taurus | 21-11-31 | Rohini | 4 | [R] yes |
| Mercury | Capricorn | 12-45-23 | Sravana | 1 | [R] yes |
| Jupiter | Pisces | 23-53-47 | Revati | 3 | no |
| Venus | Scorpio | 28-45-03 | Jyeshtha | 4 | no |
| Saturn | Cancer | 06-08-03 | Pashyami | 1 | [R] yes |
| Rahu | Libra | 24-44-12 | Vishakha | 2 | [R] yes |
| Ketu | Aries | 24-44-12 | Bharani | 4 | [R] yes |

Source: PDF p.3. Status: oracle-confirmed. Session: S127. (Byte-identical
table also re-printed at PDF p.54, self-consistency confirmed.)

### 3b. JHora v8 — D-1 positions (Basics tab capture, Session 54; location = "London Colney", not London — see §1 CONFLICT) — NOTE: MODE = True Chitrapaksha (confirmed by the appended True-Chitra table matching these values); superseded as matched-mode oracle by §3e.

| Planet | Position (deg° sign min'sec") | Retrograde | Source |
|---|---|---|---|
| Lagna | 5° Virgo 11'25" | — | `tests/fixtures/jhora_david_ashtakavarga.md:71` |
| Sun | 5° Capricorn 27'34" | no | `tests/fixtures/jhora_david_ashtakavarga.md:72` |
| Moon | 11° Leo 40'24" | no | `tests/fixtures/jhora_david_ashtakavarga.md:73` |
| Mars | 21° Taurus 13'34" | yes | `tests/fixtures/jhora_david_ashtakavarga.md:74` |
| Mercury | 12° Capricorn 45'29" | yes | `tests/fixtures/jhora_david_ashtakavarga.md:75` |
| Jupiter | 23° Pisces 55'32" | no | `tests/fixtures/jhora_david_ashtakavarga.md:76` |
| Venus | 28° Scorpio 45'44" | no | `tests/fixtures/jhora_david_ashtakavarga.md:77` |
| Saturn | 6° Cancer 02'43" | yes | `tests/fixtures/jhora_david_ashtakavarga.md:78` |

Status: oracle-confirmed. Session: S54.

### 3c. JHora v8 — same longitudes, absolute-degree form used by the Jaimini karaka oracle (corroborates 3b to sub-arcsecond precision, same underlying JHora capture, NOT a second independent source) — NOTE: MODE = True Chitrapaksha (confirmed by the appended True-Chitra table matching these values); superseded as matched-mode oracle by §3e.

| Planet | Sign, deg, min, sec | Source |
|---|---|---|
| Sun | Cp 5°27'33.96" | `tests/calculations/test_jaimini_karakas.py:46` (`DAVID` dict) |
| Moon | Le 11°40'24.23" | `tests/calculations/test_jaimini_karakas.py:47` |
| Mars | Ta 21°13'33.95" | `tests/calculations/test_jaimini_karakas.py:48` |
| Mercury | Cp 12°45'29.37" | `tests/calculations/test_jaimini_karakas.py:49` |
| Jupiter | Pi 23°55'32.12" | `tests/calculations/test_jaimini_karakas.py:50` |
| Venus | Sc 28°45'43.93" | `tests/calculations/test_jaimini_karakas.py:51` |
| Saturn | Cn 6°2'42.90" | `tests/calculations/test_jaimini_karakas.py:52` |
| Rahu | Li 24°45'18.05" | `tests/calculations/test_jaimini_karakas.py:53` |

Status: oracle-confirmed (JHora v8, per file header comment "Layer A:
four-chart full-tuple oracle asserts (JHora)"). Session: not stamped in
file; header says "hardest case first" re David's tight Sun/Saturn/Rahu
cluster.

### 3d. Natal Moon longitude (production-computed, cross-checked against nakshatra boundary only — NOT an independent oracle)

| item | value | unit | source | status |
|---|---|---|---|---|
| Moon sidereal longitude (Traditional Lahiri, production flag path) | 131.65790588° (131-39-28.46) | deg | `diagnostics/ayanamsa_mode_investigation_S75.md:110` | production-output |
| Moon sidereal longitude (True Chitrapaksha, production flag path) | 131.67282979° (131-40-22.19) | deg | `diagnostics/ayanamsa_mode_investigation_S75.md:110` | production-output |
| Nakshatra/pada (both modes) | Magha, pada 4 | — | `diagnostics/ayanamsa_mode_investigation_S75.md:110` | production-output (both modes agree on nakshatra/pada) |

### 3e. JHora v8 Traditional Lahiri (matched-mode) — RATIFIED D1 oracle (Gap O1)

Source: user-appended raw JHora v8 export at the end of this file
("David::" / "Traditional Lahiri::" block) — Sulabh-supplied, mode
explicitly labeled by the export itself, distinct from the
True-Chitrapaksha-mode §3b/3c captures above.

| Body | JHora Trad-Lahiri (DMS) | abs° | Production abs° | Δ arcsec | Status |
|---|---|---|---|---|---|
| Sun | Cp 5°26'38.49" | 275.444025 | 275.438209 | -20.94 | matched-mode residual |
| Moon | Le 11°39'28.76" | 131.657989 | 131.657901 | -0.32 | matched-mode residual |
| Mars | Ta 21°12'38.48" | 51.210689 | 51.210714 | 0.09 | matched-mode residual |
| Mercury | Cp 12°44'33.90" | 282.742750 | 282.746830 | 14.69 | matched-mode residual |
| Jupiter | Pi 23°54'36.65" | 353.910181 | 353.906423 | -13.53 | matched-mode residual |
| Venus | Sc 28°44'48.46" | 238.746794 | 238.738271 | -30.69 | matched-mode residual (max) |
| Saturn | Cn 6°01'47.43" | 96.029842 | 96.033649 | 13.71 | matched-mode residual |
| Rahu | Li 24°44'22.58" | 204.739606 | 204.739568 | -0.14 | node-convention match (~0) |
| Ketu | Ar 24°44'22.58" | 24.739606 | 24.739568 | -0.14 | node-convention match (~0) |

Matched-mode residual = documented Camp-Y apparent-position gap
(production geometric vs JHora apparent; S75/Gap A1). Max |Δ| = 30.69″
(Venus). NOT drift. Production values drift-guarded in
`tests/regression/test_chart_calculator_characterization_david.py`.
Rahu/Ketu Δ ≈ -0.14″ confirms Mean-Node convention matches between
production and this JHora capture (no Mean/True node mismatch to flag).

### CONFLICT — every AstroSage vs JHora D1 longitude for David disagrees at arcminute scale

| Body | AstroSage (§3a) | JHora (§3b/3c) | Approx delta |
|---|---|---|---|
| Lagna | Virgo 05-16-57 | Virgo 5°11'25" | ~5.5' |
| Sun | Capricorn 05-26-58 | Capricorn 5°27'34" | ~36" |
| Moon | Leo 11-39-21 | Leo 11°40'24" | ~63" |
| Mars | Taurus 21-11-31 | Taurus 21°13'34" | ~123" |
| Mercury | Capricorn 12-45-23 | Capricorn 12°45'29" | ~6" |
| Jupiter | Pisces 23-53-47 | Pisces 23°55'32" | ~105" |
| Venus | Scorpio 28-45-03 | Scorpio 28°45'44" | ~41" |
| Saturn | Cancer 06-08-03 | Cancer 6°02'43" | ~320" (~5.3') |
| Rahu | Libra 24-44-12 | Libra 24°45'18" | ~66" |

Pick nothing. Contributing factors already flagged in-repo (not
re-derived here): the two captures used **different geocoded locations**
(London vs "London Colney", §1 CONFLICT) and a documented ~1 arcmin
pyswisseph-vs-JHora Lahiri cross-implementation gap
(`jhora_david_ashtakavarga.md:6`). Saturn's much larger ~5.3' delta is
not explained by either factor alone and is left unresolved here.

| resolution | authority (file:line) | status |
|---|---|---|
| **S127 update:** the AstroSage-vs-JHora pair IS now named directly. S75/S76 ratified a canonical oracle split for non-dasha quantities — D1 longitudes explicitly included — naming JHora primary and AstroSage secondary parity not expected. This resolves the D1 longitude class for David: JHora's §3b/3c values are the ratified reference; AstroSage's §3a print is the divergent, non-oracle-primary side. | `SESSION_LOG_ARCHIVE_S67-S104.md:1561-1563` — "Canonical oracle reclassification: JHora primary for non-dasha (Ashtakavarga, karakas, D-charts, Panchanga); Drik primary for dasha row-0/AD boundaries going forward. AstroSage secondary parity."; consolidated as Gap O1 in `docs/KNOWN_DIVERGENCES.md`. | RATIFIED-DIVERGENCE |

**S127 RESOLVED:** the arcminute-scale gap was mode contamination
(§3b/3c captured under True Chitrapaksha) + the Camp-Y apparent-position
gap. Matched-mode (Trad-Lahiri, §3e) residual ≤ 30.69″. Not an open
conflict.

---

## 4. D1_sign_house_dignity

**No independent oracle table found in the repo for per-planet dignity
(Exalted/Own/Friendly/Neutral/Inimical/Debilitated) or whole-sign house
placement for David.** AstroSage's own Lagna-chart diagram (PDF p.3) is a
graphic (North-Indian style box chart) that pdfplumber's text extraction
renders as unreadable interleaved glyph fragments (e.g. "Ur Ve / Ra Mo 12
10 / 7 5 Me 1 Su 9 Ne ...") — not reliably parseable without inference,
so NOT transcribed here per the read-only/no-inference constraint.

| item | value | source | status |
|---|---|---|---|
| Sign + house + dignity + retrograde, all 9 bodies | (full dict) | `diagnostics/latest_run.md` (S127, prior task this session — `calculate_chart()` capture for David) | production-output — **needs oracle before trusting** |
| House-cusp / Chalit table (whole-sign bhava boundaries) | Bhav 1=Leo 20.13.21→Virgo 05.16.56; Bhav 2=Virgo 20.13.21→Libra 05.09.45; Bhav 3=Libra 20.06.09→Scorpio 05.02.34; Bhav 4=Scorpio 19.58.58→Sagittarius 04.55.22; Bhav 5=Sagittarius 19.58.58→Capricorn 05.02.34; Bhav 6=Capricorn 20.06.09→Aquarius 05.09.45; Bhav 7=Aquarius 20.13.21→Pisces 05.16.56; Bhav 8=Pisces 20.13.21→Aries 05.09.45; Bhav 9=Aries 20.06.09→Taurus 05.02.34; Bhav 10=Taurus 19.58.58→Gemini 04.55.22; Bhav 11=Gemini 19.58.58→Cancer 05.02.34; Bhav 12=Cancer 20.06.09→Leo 05.09.45 | PDF p.3, "Chalit Table" | oracle-confirmed |
| Sign-level dignity | NOT FOUND IN REPO | — | — |
| Five-fold/Natural/Temporal Friendship tables (chart-invariant classical doctrine, printed per-report by AstroSage; usable to cross-check `chart_calculator.py`'s `_FRIENDS` dict, NOT chart-specific to David) | Permanent Friendship: Sun{Friend:Moon,Mars,Jup; Enemy:Venus,Sat; Neutral:Mercury}, Moon{Friend:Sun,Mercury; Neutral:Mars,Jup,Venus,Sat}, Mars{Friend:Sun,Moon,Jup; Enemy:Mercury; Neutral:Venus,Sat}, Mercury{Friend:Sun,Venus; Enemy:Moon; Neutral:Mars,Jup,Sat}, Jupiter{Friend:Sun,Moon,Mars; Enemy:Mercury,Venus; Neutral:Sat}, Venus{Friend:Mercury,Sat; Enemy:Sun,Moon; Neutral:Mars,Jup}, Saturn{Friend:Mercury,Venus; Enemy:Sun,Moon,Mars; Neutral:Jup} | PDF p.49, "Permanent Friendship" table | oracle-confirmed (classical/static, not David-specific — matches `agent/chart_calculator.py`'s own `_FRIENDS` dict at a glance, not diffed cell-by-cell here) |

---

## 5. vimshottari_MD_AD

### 5a. AstroSage PDF p.3 — 9-Mahadasha table + Antardashas (also independently re-captured as a fixture)

| Lord | Duration | Start | End |
|---|---|---|---|
| KET | 7 Years | 19/1/76 | 7/12/76 |
| VEN | 20 Years | 7/12/76 | 7/12/96 |
| SUN | 6 Years | 7/12/96 | 7/12/02 |
| MON | 10 Years | 7/12/02 | 7/12/12 |
| MAR | 7 Years | 7/12/12 | 7/12/19 |
| RAH | 18 Years | 7/12/19 | 7/12/37 |
| JUP | 16 Years | 7/12/37 | 7/12/53 |
| SAT | 19 Years | 7/12/53 | 7/12/72 |
| MER | 17 Years | 7/12/72 | 7/12/89 |

Source: PDF p.3 (verbatim, D/M/YY) and `tests/fixtures/astrosage_vimshottari_fixtures.md:154-164`
(pdfplumber `extract_tables()` capture, not hand-transcribed). Status:
oracle-confirmed. Session: S44.2c.

Full antardasha rows (all 9 MDs × 9 ADs) also captured verbatim at
`tests/fixtures/astrosage_vimshottari_fixtures.md:168-184` — not
reproduced cell-by-cell here; cite that file directly.

### 5b. Drik Panchang — Vimshottari MD table (independent oracle, Traditional Lahiri, site default)

| Lord | Start (local) | End (local) |
|---|---|---|
| Ketu | 1969-12-06 23:43 | 1976-12-06 17:47 |
| Shukra (Venus) | 1976-12-06 17:47 | 1996-12-06 20:50 |
| Surya (Sun) | 1996-12-06 20:50 | 2002-12-07 09:45 |
| Chandra (Moon) | 2002-12-07 09:45 | 2012-12-06 23:17 |
| Mangal (Mars) | 2012-12-06 23:17 | 2019-12-07 18:21 |
| Rahu | 2019-12-07 18:21 | 2037-12-07 09:06 |
| Guru (Jupiter) | 2037-12-07 09:06 | 2053-12-07 11:32 |
| Shani (Saturn) | 2053-12-07 11:32 | 2072-12-07 08:26 |
| Budha (Mercury) | 2072-12-07 08:26 | 2089-12-07 17:02 |

Source: `diagnostics/drik_vimshottari_S76_david.md:15-96` (Sulabh manual
capture from drikpanchang.com, 2026-07-26). Status: oracle-confirmed.
Session: S76.

### 5c. JHora v8 GUI — original pre-S76 Vimshottari MD end-JD capture (Session 74; `tests/fixtures/jhora_david.md` itself no longer shows these — it was overwritten with production-recomputed values post-S76, per that file's own note)

| Row | Lord | JHora end_jd |
|---|---|---|
| 0 | Ketu | 2443117.223565 |
| 1 | Venus | 2450422.353785 |
| 2 | Sun | 2452613.890278 |
| 3 | Moon | 2456266.455162 |
| 4 | Mars | 2458823.250671 |
| 5 | Rahu | 2465397.865903 |
| 6 | Jupiter | 2471241.966678 |
| 7 | Saturn | 2478181.841644 |
| 8 | Mercury | 2484391.193762 |

Source: `diagnostics/vimshottari_year_length_S74.md:413-423`. Status:
oracle-confirmed (JHora v8 GUI). Session: S74.

### 5d. JHora v8 — Yogini Dasha (planets-replacing-Yoginis convention)

First 3 rows (24-row full cycle table at `tests/fixtures/jhora_david.md:49-74`, not reproduced in full here):

| Lord | Start (local) | End (local) |
|---|---|---|
| Merc | 1971-09-06 05:53:21 | 1976-09-05 12:34:21 |
| Sat | 1976-09-05 12:34:21 | 1982-09-06 01:30:53 |
| Ven | 1982-09-06 01:30:53 | 1989-09-05 20:30:06 |

Source: `tests/fixtures/jhora_david.md:49-74`. Status: oracle-confirmed
(JHora v8). Session: S72 (per the file's own note that this section
predates and is unaffected by the S76 year_days ship).

### 5e. Yogini starting-lord formula cross-check

| item | value | source | status |
|---|---|---|---|
| Nakshatra # | 10 (Magha) | `diagnostics/vimshottari_year_length_S74.md:509` | oracle-confirmed (nakshatra index, cross-checked) |
| Formula (n+2)%8 | 4 | `diagnostics/vimshottari_year_length_S74.md:509` | production-output (formula application) |
| Predicted lord | Mercury | `diagnostics/vimshottari_year_length_S74.md:509` | production-output |
| JHora row-1 lord | Mercury | `diagnostics/vimshottari_year_length_S74.md:509` | oracle-confirmed — **matches predicted lord** |

### 5f. Production output (this codebase, post-S76 `year_days=365.256363` ship)

| Lord | Start (local) | End (local) |
|---|---|---|
| Ket | 1976-01-19 22:00:00 | 1976-12-06 04:43:30 |
| Ven | 1976-12-06 04:43:30 | 1996-12-06 07:46:45 |
| Sun | 1996-12-06 07:46:45 | 2002-12-06 20:41:43 |
| Moon | 2002-12-06 20:41:43 | 2012-12-06 10:13:21 |
| Mars | 2012-12-06 10:13:21 | 2019-12-07 05:17:29 |
| Rah | 2019-12-07 05:17:29 | 2037-12-06 20:02:25 |
| Jup | 2037-12-06 20:02:25 | 2053-12-06 22:29:01 |
| Sat | 2053-12-06 22:29:01 | 2072-12-06 19:23:07 |
| Merc | 2072-12-06 19:23:07 | 2089-12-07 03:58:53 |

Source: `tests/fixtures/jhora_david.md:28-38`. Status: **production-output**
(explicitly labeled "recomputed via `agent/chart_calculator.py`'s own
`_add_years()`" in that file's own header, S76) — needs oracle before
trusting.

### CONFLICT — MD1 (Ketu) boundary: AstroSage vs Drik Panchang disagree by ~1 day

- AstroSage (§5a): Ketu MD ends **7 Dec 1976** (date only, no time in this fixture).
- Drik Panchang (§5b): Ketu MD ends **6 Dec 1976, 17:47 GMT**.
- Production (§5f): Ketu MD ends **6 Dec 1976, 04:43:30**.
- JHora GUI original (§5c, JD 2443117.223565): does not itself convert to a calendar date in this file (not computed here per no-inference constraint), but is documented (`docs/KNOWN_DIVERGENCES.md` Gap D1) as the basis for the already-measured **-0.545 day** residual between production and Drik for this exact boundary.
- Pick nothing. This exact three/four-way disagreement is the subject of the already-documented, already-accepted `docs/KNOWN_DIVERGENCES.md` Gap D1 — not a new finding, restated here only because two DIFFERENT oracle sources (AstroSage, Drik) disagree with each other by ~1 calendar day, which is larger than Gap D1's own stated ±0.3-2.8 day residual band framing (that framing compares production vs one oracle at a time, not oracle vs oracle).

| resolution | authority (file:line) | status |
|---|---|---|
| Gap D1 explicitly ratifies **production's** intentional divergence from the commercial/panchang camp as a group ("Camp X": JHora/AstroSage/Drik) in favor of "Camp Y" (Kapoor Ch IX) — that piece was already RATIFIED-DIVERGENCE. **S127 update, the remaining AstroSage-vs-Drik piece:** S75/S76 separately ratified Drik as primary over AstroSage specifically for dasha row-0/AD/PD boundaries. Applied here: Drik's MD1 end (§5b) is the ratified reference; AstroSage's MD1 end (§5a) is the divergent, non-primary side. | `docs/KNOWN_DIVERGENCES.md:37-41` (production-vs-Camp-X piece) plus `SESSION_LOG_ARCHIVE_S67-S104.md:1561-1563` — "Drik primary for dasha row-0/AD boundaries going forward" (AstroSage-vs-Drik piece); consolidated as Gap O2 in `docs/KNOWN_DIVERGENCES.md`. | RATIFIED-DIVERGENCE |

---

## 6. combustion

Hand-derived (not code-computed) from AstroSage PDF page-3 planetary
longitudes (§3a above), Session 51 design chat. Separations are
ayanamsa-invariant (difference of two same-frame longitudes).

| Planet | Separation from Sun (deg) | Combust? | Orb used (deg) | Retrograde | Source |
|---|---|---|---|---|---|
| Moon | 143.794 | False | 12.0 | False | `tests/calculations/core/test_combustion.py:108` |
| Mars | 135.742 | False | 17.0 | True | `tests/calculations/core/test_combustion.py:109` |
| Mercury | 7.307 | **True** | 12.0 | True | `tests/calculations/core/test_combustion.py:110` |
| Jupiter | 78.447 | False | 11.0 | False | `tests/calculations/core/test_combustion.py:111` |
| Venus | 36.699 | False | 10.0 | False | `tests/calculations/core/test_combustion.py:112` |
| Saturn | 179.315 | False | 15.0 | True | `tests/calculations/core/test_combustion.py:113-114` — flagged as a "max-separation edge" case: hand arithmetic and Swiss Ephemeris diverge beyond the usual noise band this close to 180°; test asserts `179.0 < sep <= 180.0` rather than a tight numeric match. |

Status: oracle-confirmed (hand-derived directly from AstroSage's own
printed longitudes — not this codebase's own longitude computation).
Session: S51.

---

## 7. shadbala_components (sthana/kala/etc)

### 7a. AstroSage PDF p.50 — full ShadBala table (verbatim; also independently transcribed at `tests/fixtures/shadbala_fixtures.py:613-814`, byte-identical to the PDF as re-checked this session)

| Component | Sun | Moon | Mars | Mercury | Jupiter | Venus | Saturn |
|---|---|---|---|---|---|---|---|
| Ochcha Bala | 28.48 | 27.11 | 22.27 | 20.75 | 26.3 | 20.58 | 25.38 |
| Saptavargaja Bala | 69.38 | 71.25 | 82.5 | 91.88 | 131.25 | 60 | 69.38 |
| Ojayugmarasyamsa Bala | 15 | 15 | 0 | 15 | 15 | 30 | 15 |
| Kendra Bala | 30 | 15 | 15 | 30 | 60 | 15 | 30 |
| Drekkana Bala | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| **Total Sthan Bala** | **157.86** | **128.36** | **119.77** | **172.62** | **232.55** | **140.58** | **139.75** |
| Total Dig Bala | 10.18 | 22.24 | 55.42 | 17.51 | 6.2 | 57.94 | 19.72 |
| Nathonnatha Bala | 10.92 | 49.08 | 49.08 | 60 | 10.92 | 10.92 | 49.08 |
| Paksha Bala | 12.07 | 12.07 | 12.07 | 12.07 | 47.93 | 47.93 | 12.07 |
| Thribhaga Bala | 0 | 0 | 0 | 0 | 60 | 60 | 0 |
| Abda Bala | 0 | 0 | 0 | 0 | 0 | 15 | 0 |
| Masa Bala | 0 | 0 | 0 | 0 | 30 | 0 | 0 |
| Vara Bala | 0 | 45 | 0 | 0 | 0 | 0 | 0 |
| Hora Bala | 0 | 0 | 0 | 0 | 60 | 0 | 0 |
| Ayana Bala | 7.99 | 17.81 | 58.86 | 53.73 | 38.69 | 0.56 | 4.14 |
| Yuddha Bala | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **Total Kala Bala** | **30.98** | **123.96** | **120.01** | **125.8** | **247.54** | **134.41** | **65.29** |
| **Total Chesta Bala** | **9.66** | **47.93** | **47.8** | **55.64** | **32.04** | **22.43** | **59.36** |
| **Total Naisargika Bala** | **60** | **51.42** | **17.16** | **25.74** | **34.26** | **42.84** | **8.58** |
| **Total Drik Bala (AstroSage)** | **-23.18** | **-14.97** | **8.24** | **-22.78** | **-2.35** | **7.61** | **-8.42** |
| **Total Shad Bala** | **245.49** | **358.95** | **368.4** | **374.53** | **550.24** | **405.81** | **284.27** |
| Shadbala In Rupas | 4.09 | 5.98 | 6.14 | 6.24 | 9.17 | 6.76 | 4.74 |
| Minimum Requirements | 5 | 6 | 5 | 7 | 6.5 | 5.5 | 5 |
| Ratio | 0.82 | 1 | 1.23 | 0.89 | 1.41 | 1.23 | 0.95 |
| Relative Rank | 7 | 4 | 3 | 6 | 1 | 2 | 5 |

Source: PDF p.50, cross-verified verbatim against
`tests/fixtures/shadbala_fixtures.py:613-814` (`source: "AstroSage Kundli
PDF (David_Kundli.pdf)"`). Status: oracle-confirmed. Session: S127 (PDF
extraction) / prior session (fixture transcription, undated in-file).

### 7b. AstroSage PDF p.50 — BhavBala table

| Component | H1 | H2 | H3 | H4 | H5 | H6 | H7 | H8 | H9 | H10 | H11 | H12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Bhavadhipati Bala | 374.53 | 405.81 | 368.4 | 550.24 | 284.27 | 284.27 | 550.24 | 368.4 | 405.81 | 374.53 | 358.95 | 245.49 |
| Bhavdig Bala | 60 | 50 | 20 | 30 | 10 | 10 | 30 | 40 | 50 | 30 | 10 | 40 |
| Bhavdrishti Bala | -32.43 | 8.46 | 30.55 | 49.24 | -15.86 | -0.02 | -2.11 | -38.25 | -39.5 | 33.13 | -11.21 | -11.89 |
| Total Bhav Bala | 402.1 | 464.26 | 418.95 | 629.48 | 278.41 | 294.25 | 578.13 | 370.15 | 416.31 | 437.67 | 357.73 | 273.59 |
| Total Bhav In Rupas | 6.7 | 7.74 | 6.98 | 10.49 | 4.64 | 4.9 | 9.64 | 6.17 | 6.94 | 7.29 | 5.96 | 4.56 |
| Relative Rank | 7 | 3 | 5 | 1 | 11 | 10 | 2 | 8 | 6 | 4 | 9 | 12 |

Source: PDF p.50. Status: oracle-confirmed. Session: S127. The
"Bhavdig Bala" row is independently cross-verified at
`tests/fixtures/bhava_dig_bala_astrosage.py:30-33` (direct transcription,
Session 42) — byte-identical.

### 7c. JHora v8 Drik Bala oracle (separate oracle from 7a's AstroSage Drik Bala row — SEE CONFLICT below)

| Planet | Drik Bala (JHora v8) |
|---|---|
| Sun | -21.45 |
| Moon | -24.08 |
| Mars | 8.26 |
| Mercury | -20.09 |
| Jupiter | -9.06 |
| Venus | 5.48 |
| Saturn | -5.32 |

Source: `tests/calculations/strength/test_drik_bala.py:212-215`
(`_JHORA_DRIK["david"]`, hand-transcribed Session 46). Status:
oracle-confirmed. Session: S46. Note: CLAUDE.md's own Locked Decisions
already ratify JHora as the sole Drik Bala oracle for production parity
("AstroSage parity NOT expected on this component ... JHora primary") —
so this is a documented, accepted divergence class, not a fresh finding.

### 7d. JHora v8 Ishta/Kashta Bala oracle (separate module, own oracle capture)

| Planet | Ishta Phala | Kashta Phala |
|---|---|---|
| Sun | 16.44 | 39.90 |
| Moon | 36.05 | 19.93 |
| Mars | 32.68 | 21.30 |
| Mercury | 33.75 | 14.15 |
| Jupiter | 28.94 | 30.80 |
| Venus | 21.96 | 37.97 |
| Saturn | 38.86 | 3.90 |

Source: `tests/calculations/strength/test_ishta_kashta.py:66-68`
(`JHORA_ISHTA_KASHTA["david"]`, "JHora v8 Strengths tab, transcribed
directly from the desktop app"). Status: oracle-confirmed.

### CONFLICT — Drik Bala for David: AstroSage (§7a) vs JHora (§7c) disagree on every planet, beyond tolerance

| Planet | AstroSage Drik Bala | JHora Drik Bala | Delta |
|---|---|---|---|
| Sun | -23.18 | -21.45 | 1.73 |
| Moon | -14.97 | -24.08 | 9.11 |
| Mars | 8.24 | 8.26 | 0.02 |
| Mercury | -22.78 | -20.09 | 2.69 |
| Jupiter | -2.35 | -9.06 | 6.71 |
| Venus | 7.61 | 5.48 | 2.13 |
| Saturn | -8.42 | -5.32 | 3.10 |

Pick nothing between the two raw values. As noted in 7c, this codebase's
own Locked Decisions already resolve which one production follows
(JHora) — this row exists only to satisfy this file's own "record both,
pick neither" contract for the raw oracle data, not to relitigate the
production ratification.

| resolution | authority (file:line or docstring) | status |
|---|---|---|
| JHora is the ratified sole oracle for Drik Bala; AstroSage parity on this specific component is explicitly not expected/not checked. | `agent/calculations/strength/drik_bala.py:11-18` (module docstring, PROVENANCE CAVEAT): "This is narrower than this project's usual protocol (AstroSage parity checked); **AstroSage parity has NOT been checked against this version. Treat as JHora-parity-only.**" Corroborated by `CLAUDE.md:249`: "**AstroSage parity NOT expected on this component** (JHora-vs-AstroSage genuine divergence, e.g. Sulabh Saturn 17.46 vs 10.89); **JHora primary**." | RATIFIED-DIVERGENCE |

---

## 8. ashtakavarga_BAV_SAV

### 8a. JHora v8 (Strengths tab → Ashtakavarga → D-1, reference sign = Virgo = natal lagna, Session 54) — BAV

| Planet | Ar | Ta | Ge | Cn | Le | Vi | Li | Sc | Sg | Cp | Aq | Pi | Total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Sun | 3 | 5 | 4 | 4 | 5 | 2 | 5 | 5 | 3 | 5 | 4 | 3 | 48 |
| Moon | 3 | 4 | 5 | 5 | 4 | 4 | 5 | 4 | 2 | 4 | 4 | 5 | 49 |
| Mars | 2 | 4 | 6 | 2 | 2 | 2 | 4 | 4 | 2 | 3 | 4 | 4 | 39 |
| Mercury | 2 | 5 | 6 | 3 | 3 | 5 | 4 | 5 | 5 | 6 | 5 | 5 | 54 |
| Jupiter | 5 | 4 | 6 | 3 | 3 | 7 | 4 | 4 | 6 | 4 | 5 | 5 | 56 |
| Venus | 4 | 3 | 3 | 5 | 4 | 5 | 5 | 7 | 5 | 4 | 2 | 5 | 52 |
| Saturn | 3 | 1 | 3 | 4 | 3 | 5 | 5 | 4 | 3 | 3 | 4 | 1 | 39 |
| Lagna | 4 | 3 | 6 | 6 | 2 | 2 | 5 | 5 | 4 | 4 | 4 | 4 | 49 |

### JHora SAV (7 planets, Lagna excluded per JHora)

| Ar | Ta | Ge | Cn | Le | Vi | Li | Sc | Sg | Cp | Aq | Pi | Total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 22 | 26 | 33 | 26 | 24 | 30 | 32 | 33 | 26 | 29 | 28 | 28 | 337 |

Source: `tests/fixtures/jhora_david_ashtakavarga.md:14-29`. Status:
oracle-confirmed. Session: S54. All 21 internal checksums (row totals +
column sums + grand total) independently verified in that file — see
its own "Checksums" section.

### 8b. AstroSage PDF p.3/p.54 — Ashtakvarga Table (byte-identical between the two pages within the PDF)

| Planet | Ar | Ta | Ge | Cn | Le | Vi | Li | Sc | Sg | Cp | Aq | Pi | Total (SAV row as printed) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Sun | 3 | 5 | 4 | 4 | 5 | 2 | 5 | 5 | 3 | 5 | 4 | 3 | — |
| Moon | 1 | 4 | 5 | 5 | 4 | 4 | 5 | 4 | 2 | 5 | 5 | 5 | — |
| Mars | 2 | 4 | 6 | 2 | 2 | 2 | 4 | 4 | 2 | 3 | 4 | 4 | — |
| Mercury | 2 | 5 | 6 | 3 | 3 | 5 | 4 | 5 | 5 | 6 | 5 | 5 | — |
| Jupiter | 5 | 4 | 6 | 3 | 3 | 7 | 4 | 4 | 6 | 4 | 5 | 5 | — |
| Venus | 4 | 3 | 3 | 5 | 3 | 6 | 5 | 7 | 5 | 4 | 2 | 5 | — |
| Saturn | 3 | 1 | 3 | 4 | 3 | 5 | 5 | 4 | 3 | 3 | 4 | 1 | — |
| **SAV Total (printed)** | 20 | 26 | 33 | 26 | 23 | 31 | 32 | 33 | 26 | 30 | 29 | 28 | — |

Source: PDF p.3 (lines 94-106 of the extracted text) and p.54 (byte-identical re-print). Status: oracle-confirmed (self-consistent across both pages of the same PDF). Session: S127.

### CONFLICT — Ashtakavarga: AstroSage vs JHora disagree on Moon and Venus rows (Sun/Mars/Mercury/Jupiter/Saturn rows match exactly)

| Row | AstroSage (8b) | JHora (8a) | Match? |
|---|---|---|---|
| Sun | 3,5,4,4,5,2,5,5,3,5,4,3 | 3,5,4,4,5,2,5,5,3,5,4,3 | yes |
| Moon | 1,4,5,5,4,4,5,4,2,5,5,5 | 3,4,5,5,4,4,5,4,2,4,4,5 | **no** (Ar: 1 vs 3; Cp: 5 vs 4; Aq: 5 vs 4) |
| Mars | 2,4,6,2,2,2,4,4,2,3,4,4 | 2,4,6,2,2,2,4,4,2,3,4,4 | yes |
| Mercury | 2,5,6,3,3,5,4,5,5,6,5,5 | 2,5,6,3,3,5,4,5,5,6,5,5 | yes |
| Jupiter | 5,4,6,3,3,7,4,4,6,4,5,5 | 5,4,6,3,3,7,4,4,6,4,5,5 | yes |
| Venus | 4,3,3,5,3,6,5,7,5,4,2,5 | 4,3,3,5,4,5,5,7,5,4,2,5 | **no** (Le: 3 vs 4; Vi: 6 vs 5) |
| Saturn | 3,1,3,4,3,5,5,4,3,3,4,1 | 3,1,3,4,3,5,5,4,3,3,4,1 | yes |
| SAV total row | 20,26,33,26,23,31,32,33,26,30,29,28 | 22,26,33,26,24,30,32,33,26,29,28,28 | **no** (Ar, Le, Vi, Cp, Aq columns differ, consistent with the Moon/Venus row deltas above) |

Pick nothing for Moon and Venus. Sun/Mars/Mercury/Jupiter/Saturn rows and
the grand total (337, both sources) match exactly, so this is not a
wholesale corpus problem — it is isolated to 2 of 7 planet rows. Not
previously flagged anywhere else in the repo found during this session's
search.

| resolution | authority (file:line or docstring) | status |
|---|---|---|
| Parasara convention locked, JHora oracle. `ashtakavarga.py`'s own module docstring names exactly three known Parasara/Varahamihira convention-choice cells and explicitly validates two of David's sentinel cells against JHora: **Moon-Aries** (David's Moon is in Leo; 9th-from-Leo = Aries — this is the "9th-from-Moon" cell) and **Venus-Leo** (David's Mars is in Taurus; 4th-from-Taurus = Leo — this is the "4th-from-Mars" cell). For these two specific cells, JHora's value (Moon-Ar=3, per §8a; Venus-Le=4, per §8a) is the ratified Parasara-convention value; AstroSage's differing print (Moon-Ar=1, Venus-Le=3) is the divergent one. **Coverage caveat:** the docstring names only 3 conflict-cell types total (9th-from-Moon, 2nd-from-Jupiter, 4th-from-Mars). David's block also shows discrepancies at Moon-Capricorn, Moon-Aquarius, and Venus-Virgo — none of these match "2nd-from-Jupiter" (David's Jupiter is in Pisces; 2nd-from-Pisces = Aries, i.e. the same Moon-Aries cell already covered) or any of the other two named types. Those three cells are **not** addressed by this docstring and remain unadjudicated. **S127 reclassification:** the SAV total row is removed from this OPEN list — it is not an independent value at all, it is DERIVED (arithmetic sum of the 7 planet BAV rows + Lagna), so its mismatch is fully explained by, and does not add to, the Moon/Venus row mismatches already accounted for above; it carries no separate adjudication need. | `agent/calculations/ashtakavarga/ashtakavarga.py:12-19` (named conflict-cell list) and `:24-25` ("incl. both Parasara/Varahamihira sentinel cells (Moon-Ar=3, Venus-Le=4) — Parasara convention confirmed end-to-end") | RATIFIED-DIVERGENCE for the Moon-Aries and Venus-Leo cells; DERIVED (sum of BAV rows, not independent) for the SAV total row, removed from OPEN; OPEN — needs PVR bindu-table hand-computation — for Moon-Capricorn, Moon-Aquarius, and Venus-Virgo |

---

## 9. jaimini_karakas

### 9a. JHora v8 — Chara Karakas (rank order, from tightest-margin longitudes)

| Karaka | Planet |
|---|---|
| AK (Atmakaraka) | Venus |
| AmK (Amatyakaraka) | Jupiter |
| BK (Bhratrukaraka) | Mars |
| MK (Matrukaraka) | Mercury |
| PiK (Putrikaraka) | Moon |
| PK (Pitrukaraka) | Saturn |
| GK (Gnatikaraka) | Sun |
| DK (Darakaraka) | Rahu |

Source: `tests/calculations/test_jaimini_karakas.py:55-58`
(`DAVID_EXPECTED`). Status: oracle-confirmed (JHora v8). Session: not
stamped in file; header flags David as the hardest of the 4 charts
(Saturn/Sun/Rahu cluster within 48 arcmin of advancement).

### 9b. AstroSage PDF p.23 — "Karak" table (Sthir + Chara columns; column headers are garbled in pdfplumber's text extraction — captured as printed, structure inferred from row shape only, NOT the cell values)

| Karaka name (AstroSage) | Sthir (fixed classical) | Chara (this chart) |
|---|---|---|
| Atma | Sun | Venus |
| Amatya | Mercury | Jupiter |
| Bhratru | Mars | Mars |
| Matrua | Moon | Mercury |
| Putra | Jupiter | Moon |
| Gnati | Saturn | Saturn |
| Dara | Venus | Sun |

Source: PDF p.23. Status: oracle-confirmed. Session: S127. **Caveat:**
the PDF's own column headers extracted as a garbled fragment ("Karak
Sthir Chara Planets Jagrat Baladi Deeptadi") straddling this table and an
adjacent Avastha table — the "Sthir"/"Chara" column labels above are
inferred from the row/column shape of the extracted text, not read
cleanly from a header cell. The planet values themselves are read
directly from their row/column position and are not in question; only
the exact header wording is a light structural inference. Not verified
name-for-name against JHora's AK/AmK/BK/MK/PiK/PK/GK abbreviation
scheme (AstroSage's karaka names Atma/Amatya/Bhratru/Matrua/Putra/Gnati/
Dara are a different naming convention) — but the SET of chara-karaka
planets matches exactly: {Venus, Jupiter, Mars, Mercury, Moon, Saturn,
Sun} in both 9a and 9b, in the same row order. No CONFLICT declared
since no cell-level disagreement was found — this is corroboration
across two independent JHora/AstroSage sources for David's Jaimini
chara-karaka planet set.

---

## 10. Any other validated fixture

### 10a. Jaimini Chara Dasha — AstroSage PDF p.24, Chara Maha Dasha header table (first 6 of 12 rows; full antardasha breakdown at PDF p.24-25, not transcribed here for brevity)

| Sign | Duration | Start | End |
|---|---|---|---|
| VIR | 08 Year | 19/1/76 | 19/1/84 |
| LIB | 01 Year | 19/1/84 | 19/1/85 |
| SCO | 06 Year | 19/1/85 | 19/1/91 |
| PIS | 12 Year | 19/1/04* | 19/1/16* |
| ARI | 01 Year | 19/1/16 | 19/1/17 |
| TAU | 06 Year | 19/1/17 | 19/1/23 |

(*PIS row's start/end dates as printed in the PDF's two-column layout
appear out of chronological sequence relative to the SCO row above it —
captured verbatim as extracted; not reordered or corrected here.)

Source: PDF p.24. Status: oracle-confirmed. Session: S127.

### 10b. Yogini Dasha starting-lord cross-check — see §5e above (not repeated).

### 10c. Natural/Temporal/Five-fold Friendship tables — see §4 above (not repeated; chart-invariant classical doctrine, not David-specific).

### 10d. Production `calculate_chart()` full output for David — prior task this session

Full return dict (`birth_details`, `lagna_chart`, `planetary_positions`,
`conjunctions`, `house_lord_mapping`, `yogas_doshas`, `aspects_by_planet`,
`aspected_by`, `dasha`, `meta`) captured verbatim to `diagnostics/latest_run.md`
(this session, prior task). Status: **production-output — needs oracle
before trusting**. Not reproduced here; see that file directly (note it
is OVERWRITE-ONLY per CLAUDE.md convention — a later session's run will
have replaced it).

---

## Categories explicitly NOT FOUND IN REPO for David

- Per-planet sign-based dignity table (Exalted/Own/Friendly/Neutral/
  Inimical/Debilitated) from any oracle source (AstroSage/JHora/PVR).
  Only this codebase's own production computation exists (§4).
- Natal Lagna sign/nakshatra/pada from an independently-verified JHora
  GUI capture — `docs/PROJECT_FACTS.md` §2 explicitly flags this as an
  open capture gap for David (and Surbhi/Sheridan).
- A combustion table printed directly by AstroSage (the combustion
  values in §6 are hand-derived from AstroSage's raw longitudes, not
  read off an AstroSage-labeled "combustion" column).
- Any Ashtottari, Chara/Jaimini-based sub-dasha, D2-D60 varga chart
  reference values, or Mangal Dosha / Kalsarpa Yoga oracle-confirmed
  determination for David specifically.




David::

Traditional Lahiri::

Body                    Longitude        Nakshatra Pada Rasi Navamsa

Lagna                    5 Vi 17' 20.27" UPha      3    Vi   Aq
Sun - GK                 5 Cp 26' 38.49" USha      3    Cp   Aq
Moon - PiK              11 Le 39' 28.76" Magh      4    Le   Cn
Mars (R) - BK           21 Ta 12' 38.48" Rohi      4    Ta   Cn
Mercury (R) - MK        12 Cp 44' 33.90" Srav      1    Cp   Ar
Jupiter - AmK           23 Pi 54' 36.65" Reva      3    Pi   Aq
Venus - AK              28 Sc 44' 48.46" Jye       4    Sc   Pi
Saturn (R) - PK          6 Cn 01' 47.43" Push      1    Cn   Le
Rahu - DK               24 Li 44' 22.58" Visa      2    Li   Ta
Ketu                    24 Ar 44' 22.58" Bhar      4    Ar   Sc
Maandi                   6 Le 26' 27.86" Magh      2    Le   Ta
Gulika                  26 Cn 07' 40.66" Asre      3    Cn   Aq
Bhava Lagna              4 Le 05' 02.67" Magh      2    Le   Ta
Hora Lagna               3 Pi 18' 55.97" PBha      4    Pi   Cn
Ghati Lagna              1 Sg 00' 35.86" Mool      1    Sg   Ar
Vighati Lagna           19 Le 28' 55.32" PPha      2    Le   Vi
Varnada Lagna            5 Le 17' 20.27" Magh      2    Le   Ta
Sree Lagna              20 Cn 03' 16.83" Asre      2    Cn   Cp
Pranapada Lagna         20 Le 04' 24.43" PPha      3    Le   Li
Indu Lagna              11 Cp 39' 28.76" Srav      1    Cp   Ar
Bhrigu Bindu            18 Pi 11' 55.67" Reva      1    Pi   Sg
Dhooma                  18 Ta 46' 38.49" Rohi      3    Ta   Ge
Vyatipata               11 Aq 13' 21.51" Sata      2    Aq   Cp
Parivesha               11 Le 13' 21.51" Magh      4    Le   Cn
Indra Chapa             18 Sc 46' 38.49" Jye       1    Sc   Sg
Upaketu                  5 Sg 26' 38.49" Mool      2    Sg   Ta
Kaala                   17 Vi 59' 10.42" Hast      3    Vi   Ge
Mrityu                  29 Li 23' 39.02" Visa      3    Li   Ge
Artha Prahara           21 Sc 12' 45.87" Jye       2    Sc   Cp
Yama Ghantaka           17 Sg 46' 36.62" PSha      2    Sg   Vi
Prana Sphuta            22 Vi 34' 21.99" Hast      4    Vi   Cn
Deha Sphuta             29 Ge 23' 30.75" Puna      3    Ge   Ge
Mrityu Sphuta            8 Ar 20' 23.12" Aswi      3    Ar   Ge
Sookshma TriSphuta       0 Cp 18' 15.87" USha      2    Cp   Cp
Tithi Sphuta             6 Sc 12' 50.27" Anu       1    Sc   Le
Yoga Sphuta (Sun-Moon)  17 Ta 06' 07.25" Rohi      3    Ta   Ge
Rahu Tithi Sphuta       19 Cp 17' 44.09" Srav      3    Cp   Ge
Kshetra Sphuta          26 Vi 46' 43.89" Chit      2    Vi   Vi
Beeja Sphuta            28 Le 06' 03.60" UPha      1    Le   Sg
TriSphuta               13 Ta 04' 29.69" Rohi      1    Ta   Ar
ChatusSphuta            18 Aq 31' 08.18" Sata      4    Aq   Pi
PanchaSphuta            13 Vi 15' 30.76" Hast      1    Vi   Ar
V2                       5 Sc 17' 20.27" Anu       1    Sc   Sg
V3                       5 Sg 17' 20.27" Mool      2    Sg   Vi
V4                       5 Pi 17' 20.27" UBha      1    Pi   Sg
V5                       5 Ar 17' 20.27" Aswi      2    Ar   Ta
V6                       5 Cn 17' 20.27" Push      1    Cn   Ar
V7                       5 Le 17' 20.27" Magh      2    Le   Ta
V8                       5 Sc 17' 20.27" Anu       1    Sc   Sg
V9                       5 Sg 17' 20.27" Mool      2    Sg   Vi
V10                      5 Pi 17' 20.27" UBha      1    Pi   Sg
V11                      5 Ar 17' 20.27" Aswi      2    Ar   Ta
V12                      5 Cn 17' 20.27" Push      1    Cn   Ar
Kunda                    8 Pi 24' 21.60" UBha      2    Pi   Vi
Yoga Sphuta             20 Le 26' 07.25" PPha      3    Le   Li
Avayoga Sphuta          27 Aq 06' 07.25" PBha      3    Aq   Ge



True lahiri/chitrapaksha::

Body                    Longitude        Nakshatra Pada Rasi Navamsa

Lagna                    5 Vi 18' 15.74" UPha      3    Vi   Aq
Sun - GK                 5 Cp 27' 33.96" USha      3    Cp   Aq
Moon - PiK              11 Le 40' 24.23" Magh      4    Le   Cn
Mars (R) - BK           21 Ta 13' 33.95" Rohi      4    Ta   Cn
Mercury (R) - MK        12 Cp 45' 29.37" Srav      1    Cp   Ar
Jupiter - AmK           23 Pi 55' 32.12" Reva      3    Pi   Aq
Venus - AK              28 Sc 45' 43.93" Jye       4    Sc   Pi
Saturn (R) - PK          6 Cn 02' 42.90" Push      1    Cn   Le
Rahu - DK               24 Li 45' 18.05" Visa      2    Li   Ta
Ketu                    24 Ar 45' 18.05" Bhar      4    Ar   Sc
Maandi                   6 Le 27' 23.33" Magh      2    Le   Ta
Gulika                  26 Cn 08' 36.13" Asre      3    Cn   Aq
Bhava Lagna              4 Le 05' 58.14" Magh      2    Le   Ta
Hora Lagna               3 Pi 19' 51.44" PBha      4    Pi   Cn
Ghati Lagna              1 Sg 01' 31.33" Mool      1    Sg   Ar
Vighati Lagna           19 Le 29' 50.79" PPha      2    Le   Vi
Varnada Lagna            5 Le 18' 15.74" Magh      2    Le   Ta
Sree Lagna              20 Cn 29' 09.96" Asre      2    Cn   Cp
Pranapada Lagna         20 Le 05' 19.90" PPha      3    Le   Li
Indu Lagna              11 Cp 40' 24.23" Srav      1    Cp   Ar
Bhrigu Bindu            18 Pi 12' 51.14" Reva      1    Pi   Sg
Dhooma                  18 Ta 47' 33.96" Rohi      3    Ta   Ge
Vyatipata               11 Aq 12' 26.04" Sata      2    Aq   Cp
Parivesha               11 Le 12' 26.04" Magh      4    Le   Cn
Indra Chapa             18 Sc 47' 33.96" Jye       1    Sc   Sg
Upaketu                  5 Sg 27' 33.96" Mool      2    Sg   Ta
Kaala                   18 Vi 00' 05.89" Hast      3    Vi   Ge
Mrityu                  29 Li 24' 34.49" Visa      3    Li   Ge
Artha Prahara           21 Sc 13' 41.34" Jye       2    Sc   Cp
Yama Ghantaka           17 Sg 47' 32.09" PSha      2    Sg   Vi
Prana Sphuta            22 Vi 39' 54.81" Hast      4    Vi   Cn
Deha Sphuta             29 Ge 31' 49.97" Puna      3    Ge   Ge
Mrityu Sphuta            8 Ar 27' 46.87" Aswi      3    Ar   Ge
Sookshma TriSphuta       0 Cp 39' 31.65" USha      2    Cp   Cp
Tithi Sphuta             6 Sc 12' 50.27" Anu       1    Sc   Le
Yoga Sphuta (Sun-Moon)  17 Ta 07' 58.19" Rohi      3    Ta   Ge
Rahu Tithi Sphuta       19 Cp 17' 44.09" Srav      3    Cp   Ge
Kshetra Sphuta          26 Vi 49' 30.30" Chit      2    Vi   Vi
Beeja Sphuta            28 Le 08' 50.01" UPha      1    Le   Sg
TriSphuta               13 Ta 07' 16.10" Rohi      1    Ta   Ar
ChatusSphuta            18 Aq 34' 50.05" Sata      4    Aq   Pi
PanchaSphuta            13 Vi 20' 08.11" Hast      2    Vi   Ta
V2                       5 Sc 18' 15.74" Anu       1    Sc   Sg
V3                       5 Sg 18' 15.74" Mool      2    Sg   Vi
V4                       5 Pi 18' 15.74" UBha      1    Pi   Sg
V5                       5 Ar 18' 15.74" Aswi      2    Ar   Ta
V6                       5 Cn 18' 15.74" Push      1    Cn   Ar
V7                       5 Le 18' 15.74" Magh      2    Le   Ta
V8                       5 Sc 18' 15.74" Anu       1    Sc   Sg
V9                       5 Sg 18' 15.74" Mool      2    Sg   Vi
V10                      5 Pi 18' 15.74" UBha      1    Pi   Sg
V11                      5 Ar 18' 15.74" Aswi      2    Ar   Ta
V12                      5 Cn 18' 15.74" Push      1    Cn   Ar
Kunda                    9 Pi 39' 14.58" UBha      2    Pi   Vi
Yoga Sphuta             20 Le 27' 58.19" PPha      3    Le   Li
Avayoga Sphuta          27 Aq 07' 58.19" PBha      3    Aq   Ge