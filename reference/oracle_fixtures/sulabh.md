# Oracle Reference — Sulabh

**Purpose:** consolidated, per-person oracle reference for Sulabh, built
READ-ONLY from repo fixtures, diagnostics, and the in-repo AstroSage PDF
(`data/pdfs/VedicReport5-24-202610-01-26PM.pdf`, confirmed by content —
page 2 prints "Sulabh" — extracted this session via `pdfplumber`; the
project-root PDF filename does not itself say "Sulabh", found by content
match, not name match; `Wife_VedicReport.pdf` is Surbhi's, confirmed the
same way and NOT used here). No value here is computed, converted, or
inferred by this session — every row is a verbatim transcription from a
cited file/page, or an existing fixture value copied verbatim. Where two
sources disagree on the same item, both are recorded in a CONFLICT row
and neither is picked, except where a prior session has already ratified
an authority (quoted verbatim, not re-adjudicated).

**Session:** S127. **PDF extraction method:** `pdfplumber` (not
`pypdf`), 56 pages, printed 5/24/2026 10:01 PM, page numbers are the
PDF's own printed footer `Page No. N`.

Status legend: `oracle-confirmed` = source is AstroSage/JHora/PVR/Drik
Panchang; `production-output` = this codebase's own calculator output
(needs oracle before trusting); `RATIFIED-DIVERGENCE` = a prior session
already named an authority for this exact conflict; `OPEN` = no
authority found, not adjudicated here; `unverified`/`DERIVED` per the
same conventions as `reference/oracle_fixtures/david.md`.

---

## 0. Mode discipline note (read this before any row below)

- The **AstroSage PDF** (this session's fresh capture) prints
  `Ayanamsa Name Lahiri`, value `023-41-33` (PDF p.2/p.3).
- The **`tests/fixtures/jhora_sulabh.md` S27 capture** (Panchanga +
  Planetary Positions, its own §1-2) prints ayanamsa `23-40-39.08` —
  this is the exact value `docs/KNOWN_DIVERGENCES.md` Gap O3 discusses.
  Per the instructing task and Gap O3's own text, this value is **True
  Chitrapaksha**, not Traditional Lahiri, for all 4 charts including
  Sulabh — Gap O3's "Only Sulabh's figure is treated as a real
  independent GUI capture" language (quoted in `CLAUDE.md`) means the
  *capture itself* is genuine (not copy-pasted boilerplate the way the
  other 3 charts' identical figures are), **not** that its *mode* is
  Traditional Lahiri. It is tagged **True Chitrapaksha** throughout this
  file and is **not used as the matched-mode D1 longitude oracle**.
- The **S76 Vimshottari recapture** (`diagnostics/drik_vimshottari_S76_
  sulabh.md`, Drik Panchang) explicitly confirms its own ayanamsa
  setting as "Lahiri (Traditional / Chitrapaksha)" — this **is**
  matched-mode, and is preferred for dasha per Gap O2.
- **UPDATE, S127 2nd pass:** a Traditional-Lahiri-mode JHora D1
  planetary-longitude table for Sulabh was not found in the repo during
  the first pass of this file, and was recorded as an external ask.
  Sulabh (user) has since supplied one directly (9 grahas + Lagna) —
  see §3e, which now closes that gap with a real matched-mode Camp-Y
  residual table, David/Sheridan-equivalent.

---

## 1. birth_data

| item | value | unit | source (file:line or PDF p.N) | ayanamsa/mode | status | session |
|---|---|---|---|---|---|---|
| Name | Sulabh | — | PDF p.2 | n/a | oracle-confirmed | S127 |
| Sex | Male | — | PDF p.2 | n/a | oracle-confirmed | S127 |
| Date of Birth | 6 : 4 : 1988 | D:M:Y | PDF p.2 | n/a | oracle-confirmed | S127 |
| Time of Birth | 0 : 30 : 0 | H:M:S | PDF p.2 | n/a | oracle-confirmed | S127 |
| Day of Birth | Wednesday | — | PDF p.2 | n/a | oracle-confirmed | S127 |
| Place of Birth | Calcutta | — | PDF p.2 | n/a | oracle-confirmed | S127 |
| Time Zone | 5.5 | hours | PDF p.2 | n/a | oracle-confirmed | S127 |
| Latitude | 22 : 31 : N | deg:min | PDF p.2 | n/a | oracle-confirmed | S127 |
| Longitude | 88 : 25 : E | deg:min | PDF p.2 | n/a | oracle-confirmed | S127 |
| Local Time Correction | 00.23.40 | h.m.s | PDF p.2 | n/a | oracle-confirmed | S127 |
| War Time Correction | 00.00.00 | h.m.s | PDF p.2 | n/a | oracle-confirmed | S127 |
| LMT at Birth | 0:53:40 | H:M:S | PDF p.2 | n/a | oracle-confirmed | S127 |
| GMT at Birth | 19:0:0 | H:M:S | PDF p.2 | n/a | oracle-confirmed | S127 |
| Julian Day | 2447258 | JD (integer, AstroSage's own truncated display) | PDF p.2/p.3 | n/a | oracle-confirmed | S127 |
| Ishtkaal | 047-44-41 | deg-min-sec | PDF p.2 | n/a | oracle-confirmed | S127 |
| Dasa Balance (Jup) | 1 Y 3 M 28 D | Y/M/D | PDF p.2 | n/a | oracle-confirmed | S127 |
| Lagna | Sagittarius | — | PDF p.2/p.3 | n/a | oracle-confirmed | S127 |
| Lagna Lord | Jup | — | PDF p.2 | n/a | oracle-confirmed | S127 |
| Geocoded Latitude | 22.5726459 | decimal deg | `tests/fixtures/geocoded_locations.json:3` ("Calcutta, India" → "Kolkata...") | n/a | oracle-confirmed (Nominatim/OSM, distinct geocoder from AstroSage's own 22:31N) | S127 |
| Geocoded Longitude | 88.3638953 | decimal deg | `tests/fixtures/geocoded_locations.json:4` | n/a | oracle-confirmed (Nominatim/OSM) | S127 |
| Canonical calculate_chart() input | `("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")` | — | `tests/calculations/strength/test_drik_bala.py:220`, `tests/calculations/strength/test_ishta_kashta.py:110`, `tests/calculations/core/test_combustion.py:73` (byte-identical across all 3 call sites) | n/a | oracle-confirmed (canonical fixture, cross-verified) | S74-era, re-confirmed S127 |

**CONFLICT — birth location coordinates:**
- AstroSage PDF (p.2): `22:31:N, 88:25:E` (= 22.5167, 88.4167).
- App's own geocoder (Nominatim/OSM, `geocoded_locations.json`):
  `22.5726459, 88.3638953`.
- JHora S27 capture (`tests/fixtures/jhora_sulabh.md:31`): "88°22'00\"E,
  22°34'00\"N" — a **third** value, close to but not identical to
  either of the above.
- Pick nothing; same class of divergence already recorded for David/
  Sheridan.

| resolution | authority (file:line) | status |
|---|---|---|
| For production calculation purposes, the app's own Nominatim/OSM geocoder output is canonical. | `docs/PROJECT_FACTS.md:18-21` (same citation used for David's identical-shape conflict) | RATIFIED-DIVERGENCE |

---

## 2. ayanamsa (+mode)

| item | value | unit | source (file:line or PDF p.N) | ayanamsa/mode | status | session |
|---|---|---|---|---|---|---|
| Ayanamsa (degrees, AstroSage) | 023-41-33 | deg-min-sec | PDF p.2 ("Ayanamsa 023-41-33") | Lahiri (PDF p.2/p.3: "Ayanamsa Name Lahiri" / "Ayan Type Lahiri") | oracle-confirmed | S127 |
| Obliquity | 023-26-27 | deg-min-sec | PDF p.2 | n/a | oracle-confirmed | S127 |
| Sidereal Time | 13.50.48 | h.m.s | PDF p.2 | n/a | oracle-confirmed | S127 |
| Ayanamsa (JHora fixture, Sulabh, S27) | 23-40-39.08 | deg-min-sec | `tests/fixtures/jhora_sulabh.md:48` | **True Chitrapaksha** (per Gap O3 / task instructions; genuine capture, wrong mode for the matched-mode comparison) | unverified for matched-mode purposes — see §0 above | S27 |

**CONFLICT — Ayanamsa value for Sulabh (both readings under a nominally
"Lahiri"-labeled setting, arcsecond-scale gap):**
- AstroSage PDF (p.2, Lahiri): **23°41'33"**.
- JHora S27 capture (labeled Lahiri in the fixture, actually True
  Chitrapaksha per Gap O3): **23°40'39.08"**.
- Delta: ~54 arcsec. Pick nothing — the two captures are not even the
  same ayanamsa mode once Gap O3 is applied, so this is not a clean
  same-mode oracle disagreement to adjudicate.

| resolution | authority (file:line) | status |
|---|---|---|
| Gap O3 discredits the JHora fixture's ayanamsa line as True-Chitra-mode boilerplate/mislabel, not a genuine Traditional-Lahiri reading — same disposition as David's identical conflict. No production `SIDM_LAHIRI` capture for Sulabh was run this session (out of scope — read-only task), so unlike David's file this entry does not carry a replacement production figure. | `docs/KNOWN_DIVERGENCES.md:219-223` (Gap O3) | RATIFIED-DIVERGENCE (mode mislabel acknowledged); no matched-mode replacement value captured this session — see manifest external asks |

---

## 3. D1_planet_longitudes

### 3a. AstroSage PDF p.3 — Planetary Positions table (verbatim; column header printed "Latitude" but values are degree-minute-second position-in-sign, not ecliptic latitude — captured as printed, same caveat as David's file)

| Planet | Sign | "Latitude" column (deg-min-sec in sign) | Nakshatra | Pada | Retrograde |
|---|---|---|---|---|---|
| ASC (Lagna) | Sagittarius | 22-46-07 | Purvashadha | 3 | — |
| Sun | Pisces | 22-31-13 | Revati | 2 | — |
| Moon | Scorpion | 02-13-44 | Vishakha | 4 | — |
| Mars | Capricorn | 05-34-32 | Uttarashadha | 3 | — |
| Mercury | Pisces | 07-52-34 | Uttarabhadra | 2 | — |
| Jupiter | Aries | 12-33-39 | Ashvini | 4 | — |
| Venus | Taurus | 08-19-40 | Krittika | 4 | — |
| Saturn | Sagittarius | 08-50-36 | Mula | 3 | — |
| Rahu | Aquarius | 28-23-54 | Purvabhadra | 3 | [R] |
| Ketu | Leo | 28-23-54 | Uttaraphal | 1 | [R] |

Source: PDF p.3. Status: oracle-confirmed. Session: S127. (No explicit
per-planet retrograde column printed on this page other than the `[R]`
tag on Rahu/Ketu; the PDF's Avkahada/basics page does not restate
retrograde flags for the other 7 bodies the way David's fixture did —
not fabricated here.)

### 3b. JHora S27 capture — True Chitrapaksha mode (genuine GUI capture, wrong mode for matched comparison — see §0)

| Body | Position | Nakshatra | Pada | Rasi | Navamsa |
|---|---|---|---|---|---|
| Lagna | 22 Sg 42' 54.24" | PSha | 3 | Sg | Li |
| Sun | 22 Pi 31' 52.53" | Reva | 2 | Pi | Cp |
| Moon | 2 Sc 14' 52.28" | Visa | 4 | Sc | Cn |
| Mars | 5 Cp 34' 38.75" | USha | 3 | Cp | Aq |
| Mercury | 7 Pi 53' 19.62" | UBha | 2 | Pi | Vi |
| Jupiter | 12 Ar 34' 25.28" | Aswi | 4 | Ar | Cn |
| Venus | 8 Ta 20' 35.31" | Krit | 4 | Ta | Pi |
| Saturn | 8 Sg 51' 10.60" | Mool | 3 | Sg | Ge |
| Rahu | 28 Aq 25' 02.40" | PBha | 3 | Aq | Ge |
| Ketu | 28 Le 25' 02.40" | UPha | 1 | Le | Sg |

Source: `tests/fixtures/jhora_sulabh.md:57-66`. Status: oracle-confirmed
(genuine JHora GUI capture, per Gap O3's own text), **True Chitrapaksha
mode**. Session: S27.

### 3e. JHora v8 Traditional Lahiri (matched-mode) — RATIFIED D1 oracle (Gap O1)

**Update, S127 (2nd pass):** supplied directly by Sulabh (user), not
extracted from any repo file — a genuine matched-mode JHora GUI capture,
9 grahas + Lagna (upagrahas/sphutas not requested). Closes the "no
matched-mode JHora D1 table" gap flagged in the first pass of this file
and in `diagnostics/manifest_sulabh.md`'s external ask #1.

| Body | JHora Trad-Lahiri (DMS) | abs° | Production abs° | Δ arcsec | Status |
|---|---|---|---|---|---|
| Lagna | Sg 22°40'59.06" | 262.683072 | 262.693800 | 38.62 | matched-mode residual |
| Sun | Pi 22°30'56.53" | 352.515703 | 352.509971 | -20.63 | matched-mode residual (aberration-scale, consistent with David's -20.94″) |
| Moon | Sc 2°13'56.28" | 212.232300 | 212.231995 | -1.10 | matched-mode residual |
| Mars | Cp 5°33'42.75" | 275.561875 | 275.556634 | -18.87 | matched-mode residual |
| Mercury | Pi 7°52'23.63" | 337.873231 | 337.859921 | -47.92 | matched-mode residual (max) |
| Jupiter | Ar 12°33'29.29" | 12.558136 | 12.550179 | -28.64 | matched-mode residual |
| Venus | Ta 8°19'39.31" | 38.327586 | 38.323702 | -13.98 | matched-mode residual |
| Saturn | Sg 8°50'14.60" | 248.837389 | 248.836890 | -1.79 | matched-mode residual; **(R) REMOVED S129 — see correction note below** |
| Rahu | Aq 28°24'06.40" | 328.401778 | 328.401740 | -0.14 | node-convention match (~0) |
| Ketu | Le 28°24'06.40" | 148.401778 | 148.401740 | -0.14 | node-convention match (~0) |

Production values from a fresh `calculate_chart("Sulabh", "6 Apr 1988",
"00:30", "Calcutta, India")` run this session (canonical tuple per
`tests/calculations/strength/test_drik_bala.py:220` and 2 other call
sites, unambiguous); `planetary_positions[<planet>]["longitude"]` for
grahas, `meta.asc_lon_sidereal` (262.6938°) for Lagna. Matched-mode
residual = documented Camp-Y apparent-position gap (production geometric
vs JHora apparent; Gap A1 family). Max |Δ| = 47.92″ (Mercury) — sub-90″,
no FLAG condition (≥100″) triggered. Rahu/Ketu Δ ≈ -0.14″ confirms
Mean-Node convention match between production and this JHora capture
(byte-identical to David's own Rahu/Ketu residual, §3e of that file —
corroborating, not coincidental: both captures share the same JHora
Mean-Node setting).

**CORRECTION (S129, 2026-09-12).** The struck sentence below was wrong on
both halves and is retained per the supersede-don't-delete convention:

  ~~"Saturn's retrograde flag (R) in this capture matches
  production/AstroSage."~~

(a) THERE IS NO (R) IN THE CAPTURE. This file's own raw JHora export prints
    `Saturn - BK              8 Sg 50' 14.60" Mool      3    Sg   Ge`
    with no retrograde marker — and 8 Sg 50'14.60" is exactly the §3e value,
    so that line IS the source of this row. For contrast, the same export
    format in the other three fixtures marks a retrograde Saturn explicitly:
    david `Saturn (R) - PK  6 Cn 01' 47.43"`, sheridan `Saturn (R) - MK
    17 Li 44' 27.51"`, surbhi `Saturn (R) - PK  19 Cp 01' 47.26"`.
    The "(R)" in the §3e row above was introduced when the table was
    hand-built from the export. It is a transcription slip, now removed.
(b) IT DID NOT MATCH PRODUCTION EITHER. Production computes Saturn DIRECT
    for this chart and is correct: recomputed against pyswisseph
    (SIDM_LAHIRI, FLG_SPEED, jd_ut 2447257.291667) Saturn's motion is
    +0.008719 deg/day — direct, and ~1/100 of mean speed. It stations
    retrograde at jd 2447262.5614 = 1988-04-11 01:47 UT, 5.27 days AFTER
    birth. So JHora, production and the astronomy all agree; only the
    hand-built table disagreed.

CROSS-CHART CENSUS supporting this (S129, 4 charts x 7 grahas): JHora marks
8 bodies (R) across the four fixtures. 7 agree with production exactly —
surbhi/Saturn -0.052846, david/Mars -0.012495, david/Mercury -1.024148,
david/Saturn -0.082362, sheridan/Mars -0.298606, sheridan/Jupiter -0.081194,
sheridan/Saturn -0.064846 deg/day. The single disagreement was this row.
With the slip removed the census is 8/8. Note david/Mars at -0.0125 deg/day
is nearly as slow as this Saturn and still flags correctly, so JHora is NOT
applying a near-station convention — the marker tracks the sign of motion.

### 3f. JHora v8 Traditional Lahiri (matched-mode) — FULL body table incl. Navamsa, upagrahas and sphutas (S130)

**Supplied directly by Sulabh (user), 2026-09-13, via JHora's own
"Copy to clipboard" — NOT hand-typed.** Same mode and same underlying
capture as §3e (all 9 grahas byte-identical to it), but this one carries
three things §3e does not: the **Navamsa column**, the **upagrahas**, and
the **sphutas** — §3e's own note records "upagrahas/sphutas not requested".
Ayanamsa mode confirmed by the user as **Traditional Lahiri**.

```
Body                    Longitude        Nakshatra Pada Rasi Navamsa
Lagna                   22 Sg 41' 58.24" PSha      3    Sg   Li
Sun - AK                22 Pi 30' 56.53" Reva      2    Pi   Cp
Moon - GK                2 Sc 13' 56.28" Visa      4    Sc   Cn
Mars - PK                5 Cp 33' 42.75" USha      3    Cp   Aq
Mercury - PiK            7 Pi 52' 23.63" UBha      2    Pi   Vi
Jupiter - AmK           12 Ar 33' 29.29" Aswi      4    Ar   Cn
Venus - MK               8 Ta 19' 39.31" Krit      4    Ta   Pi
Saturn - BK              8 Sg 50' 14.60" Mool      3    Sg   Ge
Rahu - DK               28 Aq 24' 06.40" PBha      3    Aq   Ge
Ketu                    28 Le 24' 06.40" UPha      1    Le   Sg
Maandi                   2 Li 13' 37.09" Chit      3    Li   Li
Gulika                  22 Vi 14' 24.34" Hast      4    Vi   Cn
Bhava Lagna              6 Cp 56' 15.01" USha      4    Cp   Pi
Hora Lagna              22 Li 08' 19.90" Visa      1    Li   Ar
Ghati Lagna              7 Pi 44' 34.57" UBha      2    Pi   Vi
Vighati Lagna           25 Cp 45' 47.92" Dhan      1    Cp   Le
Varnada Lagna           22 Cn 41' 58.24" Asre      2    Cn   Sc
Sree Lagna              22 Sc 58' 17.75" Jye       2    Sc   Cp
Pranapada Lagna         26 Ta 32' 34.32" Mrig      1    Ta   Le
Indu Lagna               2 Le 13' 56.28" Magh      1    Le   Ar
Bhrigu Bindu             0 Cn 19' 01.34" Puna      4    Cn   Cn
Dhooma                   5 Le 50' 56.53" Magh      2    Le   Ta
Vyatipata               24 Sc 09' 03.47" Jye       3    Sc   Aq
Parivesha               24 Ta 09' 03.47" Mrig      1    Ta   Le
Indra Chapa              5 Aq 50' 56.53" Dhan      4    Aq   Sc
Upaketu                 22 Aq 30' 56.53" PBha      1    Aq   Ar
Kaala                   11 Sc 03' 49.13" Anu       3    Sc   Li
Mrityu                  20 Sg 52' 57.66" PSha      3    Sg   Li
Artha Prahara           13 Cp 38' 12.72" Srav      2    Cp   Ta
Yama Ghantaka            9 Aq 38' 52.78" Sata      1    Aq   Sg
Prana Sphuta            15 Ta 44' 15.53" Rohi      2    Ta   Ta
Deha Sphuta             10 Ge 05' 54.56" Ardr      2    Ge   Cp
Mrityu Sphuta           28 Cn 11' 46.88" Asre      4    Cn   Pi
Sookshma TriSphuta      24 Sc 01' 56.97" Jye       3    Sc   Aq
Tithi Sphuta             9 Sc 42' 59.75" Anu       2    Sc   Vi
Yoga Sphuta (Sun-Moon)  24 Li 44' 52.81" Visa      2    Li   Ta
Rahu Tithi Sphuta        5 Pi 53' 09.87" UBha      1    Pi   Le
Kshetra Sphuta          20 Le 21' 08.31" PPha      3    Le   Li
Beeja Sphuta            13 Ta 24' 05.12" Rohi      2    Ta   Ta
TriSphuta               17 Cp 10' 18.85" Srav      3    Cp   Ge
ChatusSphuta             9 Cp 41' 15.38" USha      4    Cp   Pi
PanchaSphuta             8 Sg 05' 21.78" Mool      3    Sg   Ge
V2                      22 Le 41' 58.24" PPha      3    Le   Sg
V3                      22 Sc 41' 58.24" Jye       2    Sc   Pi
V4                      22 Sg 41' 58.24" PSha      3    Sg   Ar
V5                      22 Pi 41' 58.24" Reva      2    Pi   Cn
V6                      22 Ar 41' 58.24" Bhar      3    Ar   Le
V7                      22 Cn 41' 58.24" Asre      2    Cn   Sc
V8                      22 Le 41' 58.24" PPha      3    Le   Sg
V9                      22 Sc 41' 58.24" Jye       2    Sc   Pi
V10                     22 Sg 41' 58.24" PSha      3    Sg   Ar
V11                     22 Pi 41' 58.24" Reva      2    Pi   Cn
V12                     22 Ar 41' 58.24" Bhar      3    Ar   Le
Kunda                    8 Ta 39' 37.30" Krit      4    Ta   Pi
Yoga Sphuta             28 Cp 04' 52.81" Dhan      2    Cp   Vi
Avayoga Sphuta           4 Le 44' 52.81" Magh      2    Le   Ta
```

**D9 (Navamsa) — this is now the matched-mode D9 oracle for Sulabh.**
The Navamsa column here is byte-identical to §3b's Navamsa column, which is
a **True Chitrapaksha** capture — so for this chart the D9 signs are stable
across the two ayanamsa modes even though the D1 longitudes are not. Two
independent modes, one identical D9 column.

| Body | D9 sign |
|---|---|
| Lagna | Libra |
| Sun | Capricorn |
| Moon | Cancer |
| Mars | Aquarius |
| Mercury | **Virgo (exaltation)** |
| Jupiter | **Cancer (exaltation)** |
| Venus | **Pisces (exaltation)** |
| Saturn | Gemini |
| Rahu | Gemini |
| Ketu | Sagittarius |

**PRODUCTION AGREEMENT: 10/10.** `agent/calculations/vargas/navamsa.py`'s
`compute_navamsa()`, as composed by `frontend/app.py` and restated by
`chart_facts._read_navamsa`, produces exactly these ten values — captured
live in `diagnostics/qa_capture/20260913T065603Z.md`. This **closes the S130
accepted precision gap**: that composition feeds `compute_navamsa` the
ROUNDED `meta.jd_ut` (6dp) and `meta.asc_lon_sidereal` (4dp), worth ~0.2
arc-seconds against a 3°20' pada, and the concern was that a boundary case
could flip a pada. On this chart none does — all ten land exactly where
JHora puts them. The gap remains a documented theoretical limit; it is now
MEASURED HARMLESS for Sulabh. Do NOT "fix" it by exposing unrounded values
from `chart_calculator` — that is the S20 lock.

**Mercury exalted in D9 is load-bearing.** It is the remaining Neecha Bhanga
route for the debilitated Mercury that participates in this chart's
Dharma-Karmadhipati yoga (9th lord Sun + 10th lord Mercury conjunct in the
4th). The other two standard routes fail — Jupiter, Mercury's dispositor, is
neither exalted nor in a kendra from Lagna or Moon — so this row is what
decides whether that yoga fires at full strength.

**Upagrahas and sphutas: transcribed verbatim, NOT independently validated.**
No production code reads them today and no second oracle exists for them in
this repo. They are recorded because the capture was free and they close the
"upagrahas/sphutas not requested" gap; treat them as a single-source capture
until something cross-checks them.

Source: JHora v8 GUI, Basics tab -> Longitudes & Basic Info, clipboard copy.
Status: oracle-confirmed (matched-mode) for the graha + Navamsa rows;
single-source-captured for the upagraha/sphuta rows. Session: S130.

### CONFLICT — §3e's Lagna disagrees with §3f's, and §3f is very probably right

§3e and §3f are the SAME capture in the SAME mode: all nine grahas are
byte-identical between them. Only the Lagna differs.

| | Lagna | abs° | vs production | 
|---|---|---|---|
| §3e (hand-built table) | Sg 22°40'59.06" | 262.683072 | **+38.62″** |
| §3f (clipboard, this session) | Sg 22°41'58.24" | 262.699511 | **−20.56″** |

Production `meta.asc_lon_sidereal` = 262.693800.

**Why §3f is probably correct.** §3e's Lagna residual of +38.62″ is the ONLY
positive value in that entire table — every other row sits between −0.14″
and −47.91″, the documented Camp-Y apparent-vs-geometric aberration band.
§3f's Lagna gives −20.56″, which lands beside Sun's −20.63″. Correcting it
makes all ten residuals negative and internally coherent; leaving it makes
one row an unexplained sign flip. The two values also differ as a plausible
digit-order slip: 40'59 vs 41'58. Nobody caught it because +38.62″ passes
the ≥100″ FLAG threshold, and §3e's own text reports "Max |Δ| = 47.92″
(Mercury)" — still true either way.

This is the SAME failure class as the Saturn "(R)" slip resolved above in
this very file: a hand-built table disagreeing with its own clipboard source.

**NOT auto-corrected.** §3e is the RATIFIED D1 oracle (Gap O1) and
`meta.asc_lon_sidereal` feeds `compute_navamsa`. Changing a ratified oracle
row is Sulabh's call, not a session's. Recorded here per the
supersede-don't-delete convention; §3e's row is left exactly as it stands
until adjudicated. NOTE: adjudicating it does NOT change the D9 result
above — production computes its own ascendant and already matches JHora
10/10 on Navamsa.

### CONFLICT — AstroSage vs JHora S27 (True Chitrapaksha) D1 longitudes for Sulabh (arcminute-scale, both nominally "Lahiri"/"Lahiri-labeled" but see §0 mode caveat)

| Body | AstroSage (§3a) | JHora S27 (§3b) | Approx delta |
|---|---|---|---|
| Lagna | Sagittarius 22-46-07 | Sagittarius 22°42'54" | ~3.2' |
| Sun | Pisces 22-31-13 | Pisces 22°31'53" | ~40" |
| Moon | Scorpion 02-13-44 | Scorpio 2°14'52" | ~68" |
| Mars | Capricorn 05-34-32 | Capricorn 5°34'39" | ~7" |
| Mercury | Pisces 07-52-34 | Pisces 7°53'20" | ~46" |
| Jupiter | Aries 12-33-39 | Aries 12°34'25" | ~46" |
| Venus | Taurus 08-19-40 | Taurus 8°20'35" | ~55" |
| Saturn | Sagittarius 08-50-36 | Sagittarius 8°51'11" | ~35" |
| Rahu | Aquarius 28-23-54 | Aquarius 28°25'02" | ~68" |

Pick nothing directly cell-by-cell. Per Gap O1, JHora is the ratified
non-dasha primary oracle over AstroSage — but per §0, this specific
JHora capture is True Chitrapaksha, not Traditional Lahiri, so it is
**not** a clean matched-mode replacement the way David's §3e table was.

| resolution | authority (file:line) | status |
|---|---|---|
| Gap O1 names JHora primary for non-dasha quantities including D1 longitudes, generally. This §3b-vs-§3a conflict (True-Chitra JHora vs AstroSage) is now superseded as the operative D1 oracle by §3e (matched-mode Traditional Lahiri), supplied this pass — §3b/§3a stay recorded for provenance but are no longer the live comparison. | `docs/KNOWN_DIVERGENCES.md:193-198` (Gap O1) | RATIFIED-DIVERGENCE for source-class priority; **superseded as the working D1 oracle by §3e** |

**S127 (2nd pass) RESOLVED:** Step 4 (Node + Camp-Y checks) is now RUN
— see §3e above. The arcminute-scale AstroSage-vs-JHora-S27 gap in the
CONFLICT table above is mode contamination (§3b is True Chitrapaksha)
compounded with the Camp-Y apparent-position gap; matched-mode
(Trad-Lahiri, §3e) residual is ≤47.92″ (Mercury), well under the 100″
flag threshold, and Rahu/Ketu confirm Mean-Node convention agreement.
Not an open conflict at the matched-mode level. The external ask in
`diagnostics/manifest_sulabh.md` ("MATCHED-MODE JHORA D1 LONGITUDE
CAPTURE NEEDED") is CLOSED by §3e.

---

## 4. D1_sign_house_dignity

**No independent oracle table found in the repo for per-planet dignity**
(Exalted/Own/Friendly/Neutral/Inimical/Debilitated) for Sulabh — same
gap as David's file. AstroSage's own Lagna-chart diagram (PDF p.3) is a
graphic (North-Indian box chart) that pdfplumber renders as unreadable
interleaved glyph fragments (e.g. "Me / Ma Mo 8 6 / 10 8 Ke 9 5 Ne..."),
not reliably parseable without inference — not transcribed here per the
read-only/no-inference constraint.

| item | value | source | status |
|---|---|---|---|
| Chalit Table (whole-sign bhava boundaries, Bhav Begin / Sign Mid Bhav) | Bhav 1=Sagittarius 09.59.19→Sagittarius 22.46.06; Bhav 2=Capricorn 09.59.19→Capricorn 27.12.32; Bhav 3=Aquarius 14.25.45→Pisces 01.38.58; Bhav 4=Pisces 18.52.11→Aries 06.05.23; Bhav 5=Aries 18.52.11→Taurus 01.38.58; Bhav 6=Taurus 14.25.45→Taurus 27.12.32; Bhav 7=Gemini 09.59.19→Gemini 22.46.06; Bhav 8=Cancer 09.59.19→Cancer 27.12.32; Bhav 9=Leo 14.25.45→Virgo 01.38.58; Bhav 10=Virgo 18.52.11→Libra 06.05.23; Bhav 11=Libra 18.52.11→Scorpion 01.38.58; Bhav 12=Scorpion 14.25.45→Scorpion 27.12.32 | PDF p.3, "Chalit Table" | oracle-confirmed |
| Sign-level dignity | NOT FOUND IN REPO as a printed oracle column | — | — |

**DERIVED dignity (S130) — not an oracle row, recorded as a derivation.**
No source in this repo PRINTS a dignity column. But exaltation, debilitation
and own-sign are a fixed lookup on the sign, and the signs ARE oracle-confirmed
(§3e/§3f). Applying `chart_calculator.py`'s `EXALTATION`/`DEBILITATION`/
`_OWN_SIGNS` constants — locked S21 from PVR Table 6, uncontested — to JHora's
own Rasi column gives, and production agrees 7/7:

| Planet | Rasi (§3f) | derived standing |
|---|---|---|
| Sun | Pisces | (none — friendship tier, deliberately not stated) |
| Moon | Scorpio | **Debilitated** |
| Mars | Capricorn | **Exalted** |
| Mercury | Pisces | **Debilitated** |
| Jupiter | Aries | (none) |
| Venus | Taurus | **Own Sign** |
| Saturn | Sagittarius | (none) |

SCOPE: only these three tiers are restated into the Path B fact block
(S130 lock). Friendly/Inimical/Neutral stay out — that is the contested
tail. Exaltation DEGREES are absent from the tables, so deep-exaltation and
degree-keyed Neecha Bhanga variants remain unreachable. This block is a
DERIVATION from oracle-confirmed signs, NOT a transcribed oracle table — the
§4 no-inference constraint above still applies to anything JHora/AstroSage
does not print.

---

## 5. vimshottari_MD_AD

### 5a. AstroSage PDF p.3 — 9-Mahadasha table

| Lord | Start | End |
|---|---|---|
| JUP | 6/4/88 | 4/8/89 |
| SAT | 4/8/89 | 4/8/08 |
| MER | 4/8/08 | 4/8/25 |
| KET | 4/8/25 | 4/8/32 |
| VEN | 4/8/32 | 4/8/52 |
| SUN | 4/8/52 | 4/8/58 |
| MON | 4/8/58 | 4/8/68 |
| MAR | 4/8/68 | 4/8/75 |
| RAH | 4/8/75 | 4/8/93 |

Source: PDF p.3 (verbatim, D/M/YY as printed). Status: oracle-confirmed.
Session: S127. (Duration figures also printed per-block, e.g. "JUP -16
Years", "SAT -19 Years" etc. — verbatim, not reproduced cell-by-cell
here.)

### 5b. Drik Panchang — Vimshottari MD table (independent oracle, Traditional Lahiri, site default)

| Lord | Start (local) | End (local) |
|---|---|---|
| Guru (Jupiter) | 1973-08-04 07:21 | 1989-08-04 09:48 |
| Shani (Saturn) | 1989-08-04 09:48 | 2008-08-04 06:42 |
| Budha (Mercury) | 2008-08-04 06:42 | 2025-08-04 15:18 |
| Ketu | 2025-08-04 15:18 | 2032-08-04 10:22 |
| Shukra (Venus) | 2032-08-04 10:22 | 2052-08-04 13:25 |
| Surya (Sun) | 2052-08-04 13:25 | 2058-08-05 02:20 |
| Chandra (Moon) | 2058-08-05 02:20 | 2068-08-04 15:51 |
| Mangal (Mars) | 2068-08-04 15:51 | 2075-08-05 10:55 |
| Rahu | 2075-08-05 10:55 | 2093-08-05 01:40 |

Source: `diagnostics/drik_vimshottari_S76_sulabh.md:15-96` (Sulabh
manual capture from drikpanchang.com, 2026-07-26; ayanamsa confirmed
Traditional/Chitrapaksha Lahiri by the capture site's own default).
Status: oracle-confirmed. Session: S76.

### 5c. JHora S27 — Yogini Dasha (True Chitrapaksha mode)

First 3 of 24 rows (full table at `tests/fixtures/jhora_sulabh.md:174-197`):

| Lord | Start | End |
|---|---|---|
| Jup | 1985-07-06 10:46:59 | 1988-07-06 05:11:16 |
| Mars | 1988-07-06 05:11:16 | 1992-07-06 05:48:46 |
| Merc | 1992-07-06 05:48:46 | 1997-07-06 12:35:37 |

Source: `tests/fixtures/jhora_sulabh.md:174-176`. Status: oracle-confirmed
(JHora v8, True Chitrapaksha ayanamsa per that file's own header). Session: S27.

### 5d. JHora v8 GUI — Vimshottari MD (True Chitrapaksha, S74 capture; notional full-period display convention, MD1 begins before birth)

| Lord | Start (IST) | End (IST) |
|---|---|---|
| Jup | 1973-07-28 09:15:03 | 1989-07-28 11:39:57 |
| Sat | 1989-07-28 11:39:57 | 2008-07-28 08:30:35 |
| Merc | 2008-07-28 08:30:35 | 2025-07-28 16:55:08 |
| Ket | 2025-07-28 16:55:08 | 2032-07-28 12:07:52 |
| Ven | 2032-07-28 12:07:52 | 2052-07-28 15:02:51 |
| Sun | 2052-07-28 15:02:51 | 2058-07-29 03:48:03 |
| Moon | 2058-07-29 03:48:03 | 2068-07-28 17:23:57 |
| Mars | 2068-07-28 17:23:57 | 2075-07-29 12:30:30 |
| Rah | 2075-07-29 12:30:30 | 2093-07-29 03:07:36 |

Source: `tests/fixtures/jhora_sulabh.md:323-331`. Status:
oracle-confirmed (JHora v8 GUI, True Chitrapaksha, ayanamsa
23-40-39.08 per that section's own header). Session: S74. **Note:**
row-1 (Jup) begins before birth — JHora notional-full-period display
convention, same as David's equivalent table; row-1 `end` is the only
directly comparable boundary.

### 5e. Production output (post-S76 year_days=365.256363 ship, recomputed via `agent/chart_calculator.py`'s own `_add_years()`)

| Lord | Start | End |
|---|---|---|
| Jup | 1988-04-06 (00:30:00) | 1989-08-01 (17:54:13) |
| Sat | 1989-08-01 (17:54:13) | 2008-08-01 (14:48:18) |
| Merc | 2008-08-01 (14:48:18) | 2025-08-01 (23:24:04) |
| Ket | 2025-08-01 (23:24:04) | 2032-08-01 (18:28:13) |
| Ven | 2032-08-01 (18:28:13) | 2052-08-01 (21:31:28) |
| Sun | 2052-08-01 (21:31:28) | 2058-08-02 (10:26:26) |
| Moon | 2058-08-02 (10:26:26) | 2068-08-01 (23:58:04) |
| Mars | 2068-08-01 (23:58:04) | 2075-08-02 (19:02:12) |
| Rah | 2075-08-02 (19:02:12) | 2093-08-02 (09:47:08) |

Source: `tests/fixtures/jhora_sulabh.md:123-133`. Status:
**production-output** — needs oracle before trusting on its own, but is
the input to the already-ratified Gap D1 residual below. Session: S76.

### Gap D1 residual (already measured and ratified — restated, not re-derived)

Production row-0 (Jup MD) end vs Drik row-0 (Jup MD) end: **-2.6643
days** (production lands ~2.66 days earlier). Full arithmetic:
`diagnostics/drik_vimshottari_S76_sulabh.md:104-127`. This is the
Sulabh figure already cited in `docs/KNOWN_DIVERGENCES.md` Gap D1's
measured-residuals list ("Sulabh -2.66d").

### CONFLICT — MD1 (Jupiter) boundary: AstroSage vs Drik Panchang vs JHora disagree

- AstroSage (§5a): Jup MD ends **4 Aug 1989** (date only).
- Drik Panchang (§5b): Jup MD ends **4 Aug 1989, 09:48 IST**.
- JHora S27 True-Chitra Yogini/§5c cross-check and §5d: not directly the
  same dasha system boundary at row-0 (Yogini ≠ Vimshottari), so not
  compared cell-for-cell here.
- AstroSage's date (4 Aug 1989) and Drik's date (4 Aug 1989) **agree on
  the calendar day** — unlike David's ~1-day AstroSage-vs-Drik gap, no
  cross-oracle day-level disagreement exists for Sulabh's MD1 boundary.
  Only production (§5e, 1 Aug 1989) diverges from both, by the
  already-ratified Gap D1 amount.

| resolution | authority (file:line) | status |
|---|---|---|
| Gap D1 ratifies production's intentional divergence from the Drik/AstroSage/JHora camp (Camp Y vs Camp X). No AstroSage-vs-Drik adjudication is needed here (unlike David) since the two already agree on the calendar day for this boundary. | `docs/KNOWN_DIVERGENCES.md:17-23` (Gap D1, Sulabh -2.66d cited directly) | RATIFIED-DIVERGENCE (production vs Camp X); no open AstroSage-vs-Drik conflict for this boundary |

---

## 6. combustion

Test-fixture oracle values (hand-derived from real longitudes, same
convention as David's file), from `tests/calculations/core/
test_combustion.py`.

| Planet | Separation from Sun (deg) | Combust? | Orb used (deg) | Retrograde | Source |
|---|---|---|---|---|---|
| Moon | 140.291 | False | 12.0 | False | `tests/calculations/core/test_combustion.py:116` |
| Mercury | 14.644 | False | 14.0 | False | `tests/calculations/core/test_combustion.py:117-118` — flagged "near_miss_guard": True (must stay NOT combust with separation strictly above its orb) |
| Jupiter | 20.041 | False | 11.0 | False | `tests/calculations/core/test_combustion.py:119` |

Status: oracle-confirmed (test's own header states these values are
real-chart parity data, cross-checked against a hand-falsified AstroSage
longitude oracle — same provenance class as David's §6). Session:
not stamped in-file for Sulabh's specific rows; file predates S127.
**Note:** Mars/Venus/Saturn rows are not present for Sulabh in this
test file (only Moon/Mercury/Jupiter are asserted for this chart) —
NOT a gap in this reference, just this file's own per-chart row
selection (David/Sheridan carry the full 6-row set; Sulabh/Surbhi carry
a 3-row subset per the file's own "18 rows: David (6) first, then
Sulabh (3), Surbhi (3), Sheridan (6)" comment).

---

## 7. shadbala_components (sthana/kala/etc)

### 7a. AstroSage PDF p.50 — full ShadBala table (verbatim; independently cross-verified byte-identical against `tests/fixtures/shadbala_fixtures.py:13-209` this session)

| Component | Sun | Moon | Mars | Mercury | Jupiter | Venus | Saturn |
|---|---|---|---|---|---|---|---|
| Ochcha Bala | 54.17 | 0.26 | 52.53 | 2.37 | 32.52 | 46.22 | 43.72 |
| Saptavargaja Bala | 120 | 112.5 | 120 | 114.38 | 120 | 136.88 | 101.25 |
| Ojayugmarasyamsa Bala | 0 | 30 | 15 | 0 | 15 | 30 | 30 |
| Kendra Bala | 60 | 15 | 30 | 60 | 30 | 15 | 60 |
| Drekkana Bala | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| **Total Sthan Bala** | **234.17** | **157.76** | **232.53** | **176.75** | **197.52** | **228.1** | **234.97** |
| Total Dig Bala | 4.52 | 8.71 | 30.17 | 34.96 | 23.4 | 49.25 | 4.64 |
| Nathonnatha Bala | 4.27 | 55.73 | 55.73 | 60 | 4.27 | 4.27 | 55.73 |
| Paksha Bala | 13.24 | 13.24 | 13.24 | 13.24 | 46.76 | 46.76 | 13.24 |
| Thribhaga Bala | 0 | 0 | 0 | 0 | 60 | 60 | 0 |
| Abda Bala | 0 | 0 | 15 | 0 | 0 | 0 | 0 |
| Masa Bala | 0 | 30 | 0 | 0 | 0 | 0 | 0 |
| Vara Bala | 0 | 0 | 45 | 0 | 0 | 0 | 0 |
| Hora Bala | 0 | 60 | 0 | 0 | 0 | 0 | 0 |
| Ayana Bala | 76.23 | 54.45 | 4.06 | 30.79 | 47.24 | 56.21 | 59.82 |
| Yuddha Bala | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **Total Kala Bala** | **93.74** | **213.42** | **133.02** | **104.02** | **158.28** | **167.25** | **128.78** |
| **Total Chesta Bala** | **35.4** | **46.76** | **30.32** | **3.37** | **7.85** | **20.02** | **35.3** |
| **Total Naisargika Bala** | **60** | **51.42** | **17.16** | **25.74** | **34.26** | **42.84** | **8.58** |
| **Total Drik Bala (AstroSage)** | **-15.1** | **5.83** | **22.15** | **-20.44** | **-16.12** | **1.46** | **10.89** |
| **Total Shad Bala** | **412.74** | **483.91** | **465.35** | **324.41** | **405.2** | **508.91** | **423.16** |
| Shadbala In Rupas | 6.88 | 8.07 | 7.76 | 5.41 | 6.75 | 8.48 | 7.05 |
| Minimum Requirements | 5 | 6 | 5 | 7 | 6.5 | 5.5 | 5 |
| Ratio | 1.38 | 1.34 | 1.55 | 0.77 | 1.04 | 1.54 | 1.41 |
| Relative Rank | 4 | 5 | 1 | 7 | 6 | 2 | 3 |

Source: PDF p.50, cross-verified verbatim against
`tests/fixtures/shadbala_fixtures.py` (`source: "AstroSage Kundli PDF"`).
Status: oracle-confirmed. Session: S127 (PDF extraction) / prior session
(fixture transcription, undated in-file).

### 7b. AstroSage PDF p.50 — BhavBala table

| Component | H1 | H2 | H3 | H4 | H5 | H6 | H7 | H8 | H9 | H10 | H11 | H12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Bhavadhipati Bala | 405.2 | 423.16 | 423.16 | 405.2 | 465.35 | 508.91 | 324.41 | 483.91 | 412.74 | 324.41 | 508.91 | 465.35 |
| Bhavdig Bala | 30 | 40 | 50 | 0 | 10 | 20 | 0 | 20 | 20 | 30 | 20 | 10 |
| Bhavdrishti Bala | 55.64 | 20.52 | -15.55 | -20.85 | -11.86 | -31.33 | -34.93 | 12.28 | -19.18 | -26.86 | 18.4 | 23.07 |
| Total Bhav Bala | 490.83 | 483.68 | 457.61 | 384.35 | 463.49 | 497.59 | 289.47 | 516.18 | 413.56 | 327.55 | 547.32 | 498.42 |
| Total Bhav In Rupas | 8.18 | 8.06 | 7.63 | 6.41 | 7.72 | 8.29 | 4.82 | 8.6 | 6.89 | 5.46 | 9.12 | 8.31 |
| Relative Rank | 5 | 6 | 8 | 10 | 7 | 4 | 12 | 2 | 9 | 11 | 1 | 3 |

Source: PDF p.50. Status: oracle-confirmed. Session: S127. The
"Bhavdig Bala" row is independently cross-verified at
`tests/fixtures/bhava_dig_bala_astrosage.py:18-21` (direct transcription,
Session 42) — byte-identical: `1:30, 2:40, 3:50, 4:0, 5:10, 6:20, 7:0,
8:20, 9:20, 10:30, 11:20, 12:10`.

### 7c. JHora v8 Drik Bala oracle (separate oracle from 7a's AstroSage Drik Bala row — CONFLICT below)

| Planet | Drik Bala (JHora v8) |
|---|---|
| Sun | -17.22 |
| Moon | 5.84 |
| Mars | 16.39 |
| Mercury | -9.84 |
| Jupiter | -15.24 |
| Venus | 1.46 |
| Saturn | 17.46 |

Source: `tests/calculations/strength/test_drik_bala.py:204-207`
(`_JHORA_DRIK["sulabh"]`). Status: oracle-confirmed. Session: not
stamped in-file (predates S127; file's own comment block references
"Session 46"-era work). Note: this file's own header comment explicitly
calls out Sulabh Saturn (AstroSage 10.89 vs JHora 17.46, delta +6.57) as
the worked example of the AstroSage-vs-JHora Drik Bala divergence.

### 7d. JHora v8 Ishta/Kashta Bala oracle (separate module, own oracle capture)

| Planet | Ishta Phala | Kashta Phala |
|---|---|---|
| Sun | 43.66 | 12.02 |
| Moon | 3.42 | 28.12 |
| Mars | 39.92 | 14.89 |
| Mercury | 2.75 | 57.22 |
| Jupiter | 15.93 | 37.87 |
| Venus | 31.04 | 23.23 |
| Saturn | 39.30 | 20.04 |

Source: `tests/calculations/strength/test_ishta_kashta.py:57-59`
(`_ORACLE["sulabh"]`, byte-identical to the AstroSage PDF's own
IshtaPhala/KashtaPhala columns — `tests/fixtures/jhora_sulabh.md:203-211`
also reprints these same 7 pairs under its own "Shadbala (Strengths
tab)" section, corroborating). Status: oracle-confirmed.

### CONFLICT — Drik Bala for Sulabh: AstroSage (§7a) vs JHora (§7c) disagree on every planet, beyond tolerance

| Planet | AstroSage Drik Bala | JHora Drik Bala | Delta |
|---|---|---|---|
| Sun | -15.1 | -17.22 | 2.12 |
| Moon | 5.83 | 5.84 | 0.01 |
| Mars | 22.15 | 16.39 | 5.76 |
| Mercury | -20.44 | -9.84 | 10.60 |
| Jupiter | -16.12 | -15.24 | 0.88 |
| Venus | 1.46 | 1.46 | 0.00 |
| Saturn | 10.89 | 17.46 | 6.57 |

Pick nothing between the two raw values.

| resolution | authority (file:line or docstring) | status |
|---|---|---|
| JHora is the ratified sole oracle for Drik Bala; AstroSage parity on this component explicitly not expected. This exact Sulabh Saturn pair (10.89 vs 17.46) is CLAUDE.md's own worked example of the accepted divergence. | `agent/calculations/strength/drik_bala.py:11-18`; `CLAUDE.md` Locked Decisions ("AstroSage parity NOT expected on this component ... e.g. Sulabh Saturn 17.46 vs 10.89 ... JHora primary") | RATIFIED-DIVERGENCE |

---

## 8. ashtakavarga_BAV_SAV

### 8a. JHora v8 (reference sign = Sagittarius = natal lagna, Session 54, checksum-validated) — BAV

| Planet | Ar | Ta | Ge | Cn | Le | Vi | Li | Sc | Sg | Cp | Aq | Pi | Total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Sun | 4 | 2 | 2 | 3 | 5 | 6 | 5 | 5 | 4 | 5 | 4 | 3 | 48 |
| Moon | 3 | 7 | 2 | 4 | 3 | 5 | 6 | 4 | 2 | 5 | 5 | 3 | 49 |
| Mars | 3 | 3 | 1 | 4 | 4 | 4 | 4 | 1 | 4 | 5 | 3 | 3 | 39 |
| Mercury | 2 | 3 | 3 | 6 | 6 | 6 | 3 | 4 | 5 | 6 | 5 | 5 | 54 |
| Jupiter | 6 | 5 | 5 | 4 | 3 | 4 | 5 | 5 | 4 | 6 | 4 | 5 | 56 |
| Venus | 3 | 2 | 3 | 5 | 5 | 4 | 4 | 4 | 5 | 6 | 6 | 5 | 52 |
| Saturn | 4 | 3 | 2 | 0 | 2 | 4 | 6 | 2 | 4 | 3 | 4 | 5 | 39 |
| Lagna | 3 | 5 | 4 | 2 | 5 | 5 | 6 | 1 | 5 | 6 | 4 | 3 | 49 |

### JHora SAV (7 planets, Lagna excluded)

| Ar | Ta | Ge | Cn | Le | Vi | Li | Sc | Sg | Cp | Aq | Pi | Total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 25 | 25 | 18 | 26 | 28 | 33 | 33 | 25 | 28 | 36 | 31 | 29 | 337 |

Source: `tests/fixtures/jhora_ashtakavarga_cross_charts.md:27-48`. Status:
oracle-confirmed (reference-sign confirmed, transcription-note fixed a
Saturn-Cancer mis-transcription per that file's own note; all 21
checksums verified). Session: S54. **This supersedes the older §8 grid
in `tests/fixtures/jhora_sulabh.md:254-277`, which that file's own note
flags as SUPERSEDED (undocumented reference sign) — not used here.**

### 8b. AstroSage PDF p.3 (also byte-identically re-printed p.54, not independently checked this session) — Ashtakvarga Table

| Planet | Ar | Ta | Ge | Cn | Le | Vi | Li | Sc | Sg | Cp | Aq | Pi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Sun | 4 | 2 | 2 | 3 | 5 | 6 | 5 | 5 | 4 | 5 | 4 | 3 |
| Moon | 3 | 6 | 2 | 3 | 3 | 6 | 6 | 4 | 2 | 5 | 5 | 4 |
| Mars | 3 | 3 | 1 | 4 | 4 | 4 | 4 | 1 | 4 | 5 | 3 | 3 |
| Mercury | 2 | 3 | 3 | 6 | 6 | 6 | 3 | 4 | 5 | 6 | 5 | 5 |
| Jupiter | 6 | 5 | 5 | 4 | 3 | 4 | 5 | 5 | 4 | 6 | 4 | 5 |
| Venus | 2 | 3 | 3 | 5 | 5 | 4 | 4 | 4 | 5 | 6 | 6 | 5 |
| Saturn | 4 | 3 | 2 | 0 | 2 | 4 | 6 | 2 | 4 | 3 | 4 | 5 |
| **Total (printed)** | 24 | 25 | 18 | 25 | 28 | 34 | 33 | 25 | 28 | 36 | 31 | 30 |

Source: PDF p.3. Status: oracle-confirmed (self-consistent, not
independently re-checked against p.54 this session). Session: S127.

### CONFLICT — Ashtakavarga: AstroSage vs JHora disagree on Moon and Venus rows (Sun/Mars/Mercury/Jupiter/Saturn match exactly)

| Row | AstroSage (8b) | JHora (8a) | Match? |
|---|---|---|---|
| Sun | 4,2,2,3,5,6,5,5,4,5,4,3 | 4,2,2,3,5,6,5,5,4,5,4,3 | yes |
| Moon | 3,6,2,3,3,6,6,4,2,5,5,4 | 3,7,2,4,3,5,6,4,2,5,5,3 | **no** (Ta: 6 vs 7; Cn: 3 vs 4; Vi: 6 vs 5; Pi: 4 vs 3) |
| Mars | 3,3,1,4,4,4,4,1,4,5,3,3 | 3,3,1,4,4,4,4,1,4,5,3,3 | yes |
| Mercury | 2,3,3,6,6,6,3,4,5,6,5,5 | 2,3,3,6,6,6,3,4,5,6,5,5 | yes |
| Jupiter | 6,5,5,4,3,4,5,5,4,6,4,5 | 6,5,5,4,3,4,5,5,4,6,4,5 | yes |
| Venus | 2,3,3,5,5,4,4,4,5,6,6,5 | 3,2,3,5,5,4,4,4,5,6,6,5 | **no** (Ar: 2 vs 3; Ta: 3 vs 2) |
| Saturn | 4,3,2,0,2,4,6,2,4,3,4,5 | 4,3,2,0,2,4,6,2,4,3,4,5 | yes |
| Total row | 24,25,18,25,28,34,33,25,28,36,31,30 | 25,25,18,26,28,33,33,25,28,36,31,29 | **no** (Ar, Cn, Vi, Pi columns differ, consistent with Moon/Venus row deltas) |

Pick nothing for Moon and Venus. Grand total differs by 1 (337 JHora
vs 336 AstroSage-printed-sum) — not independently re-summed this
session, flagged as observed only.

| resolution | authority (file:line or docstring) | status |
|---|---|---|
| `ashtakavarga.py`'s docstring names the 9th-from-Moon and 4th-from-Mars sentinel cells for the Parasara/Varahamihira convention choice. **Sulabh's Moon is in Scorpio; 9th-from-Scorpio = Cancer** (the Cn cell above — AstroSage=3, JHora=4). **Sulabh's Mars is in Capricorn; 4th-from-Capricorn = Aries** — this lands on the Moon row's Ar cell (AstroSage=3, JHora=3, no conflict there) not the Venus row; the Venus-row conflict cells (Ar, Ta) do not match "4th-from-Mars" mapped onto Venus, nor "2nd-from-Jupiter" (Sulabh's Jupiter is in Aries; 2nd-from-Aries = Taurus — this **does** land on the Venus-Taurus conflict cell, AstroSage=3, JHora=2). So: Moon-Cancer (9th-from-Moon) and Venus-Taurus (2nd-from-Jupiter) are the two docstring-named sentinel cells present in this chart's conflict set; JHora's value is ratified for both. The remaining conflict cells (Moon-Ta/Vi/Pi, Venus-Ar, and the total row) are **not** named by the docstring and are left OPEN. | `agent/calculations/ashtakavarga/ashtakavarga.py:12-19,24-25` (same docstring cited in David's file) | RATIFIED-DIVERGENCE for Moon-Cancer and Venus-Taurus; DERIVED (not independent) for the total-row mismatch; **OPEN — needs PVR bindu-table hand-computation** for Moon-Taurus, Moon-Virgo, Moon-Pisces, Venus-Aries |

---

## 9. jaimini_karakas

### 9a. JHora v8 — Chara Karakas (oracle used by `tests/calculations/test_jaimini_karakas.py`)

| Karaka | Planet |
|---|---|
| AK (Atmakaraka) | Sun |
| AmK (Amatyakaraka) | Jupiter |
| BK (Bhratrukaraka) | Saturn |
| MK (Matrukaraka) | Venus |
| PiK (Putrikaraka) | Mercury |
| PK (Pitrukaraka) | Mars |
| GK (Gnatikaraka) | Moon |
| DK (Darakaraka) | Rahu |

Source: `tests/calculations/test_jaimini_karakas.py:90-102`
(`SULABH`/`SULABH_EXPECTED`). Status: oracle-confirmed (JHora v8).

### 9b. AstroSage PDF p.23 — "Karak Avastha" table (Sthir/Chara columns; header row garbled in extraction — same structural caveat as David's file: "Karak Sthir Chara Planets Jagrat Baladi Deeptadi" straddles this table and the adjacent Avastha table)

| Karaka name (AstroSage) | Sthir (fixed classical) | Chara (this chart) |
|---|---|---|
| Atma | Sun | Sun |
| Amatya | Merc | Jupt |
| Bhratru | Mars | Satn |
| Matrua | Moon | Venu |
| Putra | Jupt | Merc |
| Gnati | Satn | Mars |
| Dara | Venu | Moon |

Source: PDF p.23. Status: oracle-confirmed. Session: S127. Same header
garbling caveat as David's §9b: planet values read directly from
row/column position, header wording lightly inferred.

### CONFLICT — Jaimini karaka assignment: AstroSage's 7-karaka scheme vs JHora's 8-karaka scheme disagree on 2 planets, not just naming

Aligning by karaka role (AstroSage Chara column → JHora equivalent):

| Role | JHora (9a) | AstroSage Chara (9b) | Match? |
|---|---|---|---|
| AK / Atma | Sun | Sun | yes |
| AmK / Amatya | Jupiter | Jupt | yes |
| BK / Bhratru | Saturn | Satn | yes |
| MK / Matrua | Venus | Venu | yes |
| PiK / Putra | Mercury | Merc | yes |
| GK / Gnati | Moon | **Mars** | **no** |
| DK / Dara | Rahu | **Moon** (no Rahu in AstroSage's 7-karaka scheme) | **no** (different scheme, not directly comparable) |

This is a genuine 2-role disagreement, not a header-labeling artifact:
JHora's 8-karaka scheme assigns Gnatikaraka to Moon and Darakaraka to
Rahu; AstroSage's printed 7-karaka scheme (no Rahu karaka at all)
assigns Gnati to Mars and Dara to Moon. Unlike David's file (where the
karaka *planet set* matched exactly across both sources, S127 David
§9b), Sulabh's two sources do **not** agree on the full planet set —
Mars appears in AstroSage's karaka list where JHora's does not (JHora's
set is {Sun, Jupiter, Saturn, Venus, Mercury, Moon, Rahu}; AstroSage's
Chara set is {Sun, Jupiter, Saturn, Venus, Mercury, Mars, Moon} — Mars
replaces Rahu). No prior-session authority naming JHora vs AstroSage for
this specific 8-karaka-vs-7-karaka scheme choice was found in
`docs/KNOWN_DIVERGENCES.md` or `CLAUDE.md`. Pick nothing.

| resolution | authority (file:line) | status |
|---|---|---|
| None found. Gap O1 names JHora primary for "karakas" generally as a source-class preference, which would favor 9a — but that ratification's own text does not address the underlying 7-karaka-vs-8-karaka (Rahu-as-karaka) scheme question, which is a different kind of disagreement than an oracle-precision gap. | `docs/KNOWN_DIVERGENCES.md:193-198` (Gap O1, source-class only) | RATIFIED-DIVERGENCE for source-class priority (JHora over AstroSage, per Gap O1); **OPEN** for the underlying 7-vs-8-karaka scheme question itself — not adjudicated here |

---

## 10. Any other validated fixture

### 10a. `tests/fixtures/astrosage_sulabh_surbhi_kundli_milan.md` — Ashtakoot/Guna Milan compatibility fixture (Sulabh+Surbhi pair, not a solo-chart oracle for any of the 9 required categories — not transcribed here; cite that file directly if compatibility data is needed).

### 10b. `tests/fixtures/golden_qa_sulabh.py` — golden-harness Q&A rows (routing/answer-tier fixtures, not raw chart-fact oracle data — out of scope for this reference file's 9 categories, not transcribed).

---

### 10c. JHora v8 — Yogas (Strengths tab) — MIGRATED FROM `tests/fixtures/jhora_sulabh.md` (S132)

Transcribed VERBATIM from the retiring `tests/fixtures/jhora_sulabh.md` §7,
which was the ONLY yoga oracle in the repo for any chart. Copied here so the
old fixture can be removed without losing it. Mode/capture provenance is that
file's, unrestated — treat the mode as UNCONFIRMED for this table until it is
re-captured in matched mode (see §0).

WHAT THIS IS THE ORACLE FOR. Scope (which yogas JHora reports at all) and
per-yoga fired/not-fired for this chart. JHora prints ONLY fired yogas — an
absent name means "not reported by JHora", which is weaker than "ruled out".

THREE THINGS TO READ BEFORE USING IT:
  1. **Harsha — oracle and code DISAGREE.** JHora fires Harsha on "the 6th
     lord in the 6th house". `agent/calculations/yogas/` rules Harsha OUT for
     this chart, applying the narrow reading (6th lord must be in the 8th or
     12th, not its own house). A definition conflict, not an arithmetic one.
     UNRESOLVED — Sulabh's call (S131 lock).
  2. **Pancha Mahapurusha.** None of Ruchaka / Bhadra / Hamsa / Malavya /
     Sasa appears below. That absence is the evidence
     `test_pancha_mahapurusha.py`'s real-chart test rests on
     (SESSION_LOG.md:139), and that citation points at the retiring filename
     — re-point it here.
  3. **Neecha Bhanga is absent entirely.** JHora does not report it, so this
     table corroborates nothing either way for the Moon/Mercury cancellations.

| Yoga | Varga | Yoga givers | Results ascribed to yoga | Brief definition of yoga |
|---|---|---|---|---|
| Vesi | D-1 | Ju | Balanced, truthful and happy | Planets other than Moon in 2nd from Sun |
| Nipuna (Budha-Aditya) | D-1 | Su, Me | Skillful, expert, well-known and respected | Sun and Mercury together or in mutual 7ths |
| Sunaphaa | D-1 | Sa | Intelligent, wealthy and famous | Planets other than Sun in 2nd from Moon |
| Adhi yoga | D-1 | Ju, Ve | King, minister or an army chief | Benefics in 6th, 7th and 8th from Moon |
| Daama/Daamini | D-1 | Naabhasa yoga - throughout life | Rich, famous, helpful, many children | Seven planets in 6 rasis |
| Kalpadruma/Parijata | D-1 | Ju, Ma, Sa, Sa | King, principled, warrior, prosperous, strong, kind | Lagna lord, his disposior, latter's rasi & navamsa dispositors are all in own/exaltation sign or kendra/kona |
| Harsha | D-1 | Ve | Happy, strong, good-natured, invincible | The 6th lord in the 6th house |
| Raja/Dharma-Karmadhipati | D-1 | Me, Su | Dutiful and high achiever | Conjunction, aspect or exchange of 9th/10th lords |
| Raja (AK-PiK) | D-1 | Su, Me | Power and favors from authorities | Atma karaka and pitru karaka together or in 1st/5th |
| Yogada (GL) | D-1 | Su | Power and authority | Associated with lagna and GL (by aspect, conjunction or ownership) |
| Yogada (GL) | D-1 | Me | Power and authority | Associated with lagna and GL (by aspect, conjunction or ownership) |
| Yogada (GL) | D-1 | Ju | Power and authority | Associated with lagna and GL (by aspect, conjunction or ownership) |
| Yogada (GL) | D-1 | Sa | Power and authority | Associated with lagna and GL (by aspect, conjunction or ownership) |
| Viparita Raja Yoga | D-1 | Mo | Success after pressures or someone else's losses | 8th lord in 6th or 12th |
| Viparita Raja Yoga | D-1 | Ve, Mo | Success after pressures or someone else's losses | The 6th and 8th lords in conjunction or samasaptaka |
| Raja Sambandha | D-1 | Ju | A famous minister | Amatya karaka in a kona |

---

## Categories explicitly NOT FOUND IN REPO for Sulabh

- Per-planet sign-based dignity table (Exalted/Own/Friendly/Neutral/
  Inimical/Debilitated) **printed by** any oracle source — still absent;
  same gap as David's file. **PARTIALLY ADDRESSED S130:** the three
  fixed-table tiers (Exalted/Debilitated/Own Sign) are now DERIVED from
  §3f's oracle-confirmed Rasi column and recorded at §4, 7/7 agreeing with
  production. The contested friendship tiers remain both unprinted and
  unused.
- ~~A matched-mode D9/Navamsa reference for Sulabh~~ — **CLOSED S130, §3f**
  (Traditional Lahiri clipboard capture, 10/10 against production, and
  byte-identical to §3b's True Chitrapaksha Navamsa column).
- A matched-mode (Traditional Lahiri) JHora GUI capture of D1 planetary
  longitudes — the only JHora D1 longitude captures in-repo for Sulabh
  (S27, S74-restated) are True Chitrapaksha. See manifest external asks.
- A combustion table printed directly by AstroSage (§6 values are test-
  fixture hand-derived, not read off an AstroSage-labeled column).
- Any Ashtottari, D2-D60 varga chart reference values, or Mangal Dosha /
  Kalsarpa Yoga oracle-confirmed determination for Sulabh specifically
  (beyond the Ashtakoot pair fixture noted at §10a). **PARTIALLY ADDRESSED
  S132:** a JHora Yogas-tab capture now sits at §10c — it does NOT print
  Mangal Dosha or Kalsarpa, so those two stay unoracled; the named yogas it
  does print are now available.



<!-- S130: loose paste, retained as-is. Labelled True Chitrapaksha by the
     user; its Lagna (22 Sg 41' 55.06") differs from BOTH §3e and §3f, which
     is consistent with it being a third, different-mode capture. Not used
     as an oracle anywhere. Structured captures live at §3b/§3e/§3f. -->
Sulabh::
true lahiri/chitrapaksha:
Body                    Longitude        Nakshatra Pada Rasi Navamsa

Lagna                   22 Sg 41' 55.06" PSha      3    Sg   Li
Sun - AK                22 Pi 31' 52.53" Reva      2    Pi   Cp
Moon - GK                2 Sc 14' 52.28" Visa      4    Sc   Cn
Mars - PK                5 Cp 34' 38.75" USha      3    Cp   Aq
Mercury - PiK            7 Pi 53' 19.62" UBha      2    Pi   Vi
Jupiter - AmK           12 Ar 34' 25.28" Aswi      4    Ar   Cn
Venus - MK               8 Ta 20' 35.31" Krit      4    Ta   Pi
Saturn - BK              8 Sg 51' 10.60" Mool      3    Sg   Ge
Rahu - DK               28 Aq 25' 02.40" PBha      3    Aq   Ge
Ketu                    28 Le 25' 02.40" UPha      1    Le   Sg
Maandi                   2 Li 14' 33.36" Chit      3    Li   Li
Gulika                  22 Vi 15' 20.62" Hast      4    Vi   Cn
Bhava Lagna              6 Cp 56' 11.23" USha      4    Cp   Pi
Hora Lagna              22 Li 07' 16.18" Visa      1    Li   Ar
Ghati Lagna              7 Pi 40' 31.01" UBha      2    Pi   Vi
Vighati Lagna           25 Cp 26' 45.20" Dhan      1    Cp   Le
Varnada Lagna           22 Cn 41' 55.06" Asre      2    Cn   Sc
Sree Lagna              23 Sc 23' 26.52" Jye       3    Sc   Aq
Pranapada Lagna         26 Ta 13' 31.44" Mrig      1    Ta   Le
Indu Lagna               2 Le 14' 52.28" Magh      1    Le   Ar
Bhrigu Bindu             0 Cn 19' 57.34" Puna      4    Cn   Cn
Dhooma                   5 Le 51' 52.53" Magh      2    Le   Ta
Vyatipata               24 Sc 08' 07.47" Jye       3    Sc   Aq
Parivesha               24 Ta 08' 07.47" Mrig      1    Ta   Le
Indra Chapa              5 Aq 51' 52.53" Dhan      4    Aq   Sc
Upaketu                 22 Aq 31' 52.53" PBha      1    Aq   Ar
Kaala                   11 Sc 04' 45.35" Anu       3    Sc   Li
Mrityu                  20 Sg 53' 53.85" PSha      3    Sg   Li
Artha Prahara           13 Cp 39' 08.91" Srav      2    Cp   Ta
Yama Ghantaka            9 Aq 39' 48.96" Sata      1    Aq   Sg
Prana Sphuta            15 Ta 44' 55.93" Rohi      2    Ta   Ta
Deha Sphuta             10 Ge 14' 18.83" Ardr      2    Ge   Cp
Mrityu Sphuta           28 Cn 19' 16.89" Asre      4    Cn   Pi
Sookshma TriSphuta      24 Sc 18' 31.65" Jye       3    Sc   Aq
Tithi Sphuta             9 Sc 42' 59.75" Anu       2    Sc   Vi
Yoga Sphuta (Sun-Moon)  24 Li 46' 44.80" Visa      2    Li   Ta
Rahu Tithi Sphuta        5 Pi 53' 09.87" UBha      1    Pi   Le
Kshetra Sphuta          20 Le 23' 56.31" PPha      3    Le   Li
Beeja Sphuta            13 Ta 26' 53.12" Rohi      2    Ta   Ta
TriSphuta               17 Cp 12' 07.96" Srav      3    Cp   Ge
ChatusSphuta             9 Cp 44' 00.49" USha      4    Cp   Pi
PanchaSphuta             8 Sg 09' 02.89" Mool      3    Sg   Ge
V2                      22 Le 41' 55.06" PPha      3    Le   Sg
V3                      22 Sc 41' 55.06" Jye       2    Sc   Pi
V4                      22 Sg 41' 55.06" PSha      3    Sg   Ar
V5                      22 Pi 41' 55.06" Reva      2    Pi   Cn
V6                      22 Ar 41' 55.06" Bhar      3    Ar   Le
V7                      22 Cn 41' 55.06" Asre      2    Cn   Sc
V8                      22 Le 41' 55.06" PPha      3    Le   Sg
V9                      22 Sc 41' 55.06" Jye       2    Sc   Pi
V10                     22 Sg 41' 55.06" PSha      3    Sg   Ar
V11                     22 Pi 41' 55.06" Reva      2    Pi   Cn
V12                     22 Ar 41' 55.06" Bhar      3    Ar   Le
Kunda                    8 Ta 35' 20.03" Krit      4    Ta   Pi
Yoga Sphuta             28 Cp 06' 44.80" Dhan      2    Cp   Vi
Avayoga Sphuta           4 Le 46' 44.80" Magh      2    Le   Ta



traditional lahiri:
Body                    Longitude        Nakshatra Pada Rasi Navamsa

Lagna                   22 Sg 40' 59.06" PSha      3    Sg   Li
Sun - AK                22 Pi 30' 56.53" Reva      2    Pi   Cp
Moon - GK                2 Sc 13' 56.28" Visa      4    Sc   Cn
Mars - PK                5 Cp 33' 42.75" USha      3    Cp   Aq
Mercury - PiK            7 Pi 52' 23.63" UBha      2    Pi   Vi
Jupiter - AmK           12 Ar 33' 29.29" Aswi      4    Ar   Cn
Venus - MK               8 Ta 19' 39.31" Krit      4    Ta   Pi
Saturn - BK              8 Sg 50' 14.60" Mool      3    Sg   Ge
Rahu - DK               28 Aq 24' 06.40" PBha      3    Aq   Ge
Ketu                    28 Le 24' 06.40" UPha      1    Le   Sg
Maandi                   2 Li 13' 37.36" Chit      3    Li   Li
Gulika                  22 Vi 14' 24.62" Hast      4    Vi   Cn
Bhava Lagna              6 Cp 55' 15.23" USha      4    Cp   Pi
Hora Lagna              22 Li 06' 20.18" Visa      1    Li   Ar
Ghati Lagna              7 Pi 39' 35.02" UBha      2    Pi   Vi
Vighati Lagna           25 Cp 25' 49.20" Dhan      1    Cp   Le
Varnada Lagna           22 Cn 40' 59.06" Asre      2    Cn   Sc
Sree Lagna              22 Sc 57' 18.58" Jye       2    Sc   Cp
Pranapada Lagna         26 Ta 12' 35.44" Mrig      1    Ta   Le
Indu Lagna               2 Le 13' 56.28" Magh      1    Le   Ar
Bhrigu Bindu             0 Cn 19' 01.34" Puna      4    Cn   Cn
Dhooma                   5 Le 50' 56.53" Magh      2    Le   Ta
Vyatipata               24 Sc 09' 03.47" Jye       3    Sc   Aq
Parivesha               24 Ta 09' 03.47" Mrig      1    Ta   Le
Indra Chapa              5 Aq 50' 56.53" Dhan      4    Aq   Sc
Upaketu                 22 Aq 30' 56.53" PBha      1    Aq   Ar
Kaala                   11 Sc 03' 49.35" Anu       3    Sc   Li
Mrityu                  20 Sg 52' 57.85" PSha      3    Sg   Li
Artha Prahara           13 Cp 38' 12.92" Srav      2    Cp   Ta
Yama Ghantaka            9 Aq 38' 52.96" Sata      1    Aq   Sg
Prana Sphuta            15 Ta 39' 19.94" Rohi      2    Ta   Ta
Deha Sphuta             10 Ge 05' 54.85" Ardr      2    Ge   Cp
Mrityu Sphuta           28 Cn 11' 48.90" Asre      4    Cn   Pi
Sookshma TriSphuta      23 Sc 57' 03.70" Jye       3    Sc   Aq
Tithi Sphuta             9 Sc 42' 59.75" Anu       2    Sc   Vi
Yoga Sphuta (Sun-Moon)  24 Li 44' 52.81" Visa      2    Li   Ta
Rahu Tithi Sphuta        5 Pi 53' 09.87" UBha      1    Pi   Le
Kshetra Sphuta          20 Le 21' 08.31" PPha      3    Le   Li
Beeja Sphuta            13 Ta 24' 05.12" Rohi      2    Ta   Ta
TriSphuta               17 Cp 09' 19.97" Srav      3    Cp   Ge
ChatusSphuta             9 Cp 40' 16.49" USha      4    Cp   Pi
PanchaSphuta             8 Sg 04' 22.90" Mool      3    Sg   Ge
V2                      22 Le 40' 59.06" PPha      3    Le   Sg
V3                      22 Sc 40' 59.06" Jye       2    Sc   Pi
V4                      22 Sg 40' 59.06" PSha      3    Sg   Ar
V5                      22 Pi 40' 59.06" Reva      2    Pi   Cn
V6                      22 Ar 40' 59.06" Bhar      3    Ar   Le
V7                      22 Cn 40' 59.06" Asre      2    Cn   Sc
V8                      22 Le 40' 59.06" PPha      3    Le   Sg
V9                      22 Sc 40' 59.06" Jye       2    Sc   Pi
V10                     22 Sg 40' 59.06" PSha      3    Sg   Ar
V11                     22 Pi 40' 59.06" Reva      2    Pi   Cn
V12                     22 Ar 40' 59.06" Bhar      3    Ar   Le
Kunda                    7 Ta 19' 44.19" Krit      4    Ta   Pi
Yoga Sphuta             28 Cp 04' 52.81" Dhan      2    Cp   Vi
Avayoga Sphuta           4 Le 44' 52.81" Magh      2    Le   Ta