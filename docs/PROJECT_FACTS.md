# Project Facts — Persistent Captured-Data Registry

**Purpose:** session-agnostic registry of captured external data, canonical
fixtures, and settled empirical findings. Any Claude session (design chat
or Code) reads this INSTEAD of re-requesting data Sulabh has already
captured. **Append-only** — never overwrite a settled entry; add a dated
revision block with a supersession note instead.

**Provenance rule (see §6):** no entry is accepted here unless it traces
to a committed file (fixture, diagnostic, or classical reference PDF).
Design-chat/session-log assertions alone are not sufficient — land the
source file first, then cite it here.

---

## 1. Canonical Reference Charts

Birth inputs as passed to `calculate_chart(name, date, time, place)`;
lat/lon per `tests/fixtures/geocoded_locations.json` (the app's own
geocoder output — canonical for production calculation, may differ by
~0.01° from a value hand-typed into an external GUI, see Sulabh note).

| Chart | DOB | TOB | POB | Lat | Lon | TZ |
|---|---|---|---|---|---|---|
| Sulabh | 1988-04-06 | 00:30 | Calcutta, India | 22.5726459 | 88.3638953 | IST, UTC+5:30 (fixed) |
| Surbhi | 1992-09-11 | 10:30 | Patna, India | 25.6093239 | 85.1235252 | IST, UTC+5:30 (fixed) |
| Sheridan | 1984-05-27 | 08:00 | Durban, South Africa | -29.8618250 | 31.0099090 | SAST, UTC+2:00 (fixed, no DST) |
| David | 1976-01-19 | 22:00 | London, UK | 51.5074456 | -0.1277653 | GMT, UTC+0:00 on this date (London is DST-variable — BST/UTC+1 applies only in summer; `resolve_timezone_offset()` resolves this per-timestamp, not a fixed constant) |

Source: `tests/fixtures/geocoded_locations.json` (lat/lon); Surbhi/
Sheridan/David birth date-time-place strings verified canonical against
`tests/calculations/strength/test_drik_bala.py:219-222` (`_CHART_ARGS`),
byte-identical across ~12-14 other call sites per chart (per
`diagnostics/vimshottari_year_length_S74.md` §7.1-§7.3). Sulabh's
date/time/place verified against `tests/fixtures/jhora_sulabh.md`.

**Note (Sulabh coordinate divergence, informational only):**
`jhora_sulabh.md`'s header records the coordinates as manually typed into
the JHora GUI: `88°22'00"E, 22°34'00"N` (= 88.3667, 22.5667) — differs
from the app's own geocoder result above by ~0.01° (~0.3-0.4 arcmin
sub-degree, two independent geocoding sources). Not investigated further;
noted so a future reader doesn't assume a transcription error.

---

## 2. JHora Traditional Lahiri Fixtures

Per chart: ayanamsa at birth epoch, natal Moon (sign/nakshatra/pada),
natal Lagna (sign/nakshatra/pada), current MD/AD (evaluated as of
2026-07-26, this file's last-updated date — re-derive from the MD/AD
tables below if reading this much later).

| Chart | Ayanamsa at birth | Natal Moon | Natal Lagna | Current MD (/ AD) |
|---|---|---|---|---|
| Sulabh | 23°40'39.08" = 23.677522° — **independently GUI-captured** (Session 27, Basics tab) | 2° Sc 14'52.28" — Vishakha (Ju), pada 4 | 22° Sg 42'54.24" — Purva Shadha, pada 3 | Ketu MD (2025-07-28 → 2032-07-28) / Venus AD (2025-12-24 → 2027-02-21) |
| Surbhi | 23°40'39.08" — **NOT independently verified**, see caveat below | 315.20143018° — Shatabhisha, pada 3 | not captured in any repo fixture | Saturn MD (2015-02-22 → 2034-02-22); no AD table captured |
| Sheridan | 23°40'39.08" — **NOT independently verified**, see caveat below | 2.15985235° — Ashwini, pada 1 | not captured in any repo fixture | Mars MD (2026-04-05 → 2033-04-05); no AD table captured |
| David | 23°40'39.08" — **NOT independently verified**, see caveat below | 131.65790588° — Magha, pada 4 | not captured in any repo fixture | Rahu MD (2019-12-05 → 2037-12-05); no AD table captured |

Source: `tests/fixtures/jhora_sulabh.md` (Sulabh's full Panchanga +
planetary-position table + MD/AD tables); `tests/fixtures/jhora_surbhi.md`
/ `jhora_sheridan.md` / `jhora_david.md` (MD tables only — no AD
breakdown, no full planetary-position table); natal Moon longitude/
nakshatra/pada for all 4 cross-verified against
`diagnostics/ayanamsa_mode_investigation_S75.md` (lines 107-110) and
`diagnostics/vimshottari_year_length_S74.md` §7.1-§7.3.

**Caveat — ayanamsa boilerplate (traced to `diagnostics/vimshottari_year_
length_S74.md` §11's own flagged finding):** `jhora_surbhi.md` /
`jhora_sheridan.md` / `jhora_david.md` all read the IDENTICAL ayanamsa
value as Sulabh's (`23-40-39.08`) — this is template boilerplate copied
into the fixture text, NOT an independently re-captured per-chart GUI
value. Lahiri ayanamsa drifts ~50.3"/year with precession, so a genuine
1976-vs-1992 capture should differ by roughly 13-14 arcminutes between
David and Surbhi, not read identically. Treat only Sulabh's ayanamsa
figure as real; the other three are an open capture gap (same class of
gap as §3 below).

**Caveat — nakshatra-name discrepancy across two diagnostic files (found
while compiling this entry, not previously reconciled):** for Surbhi's
Moon at 315.20143018°, `vimshottari_year_length_S74.md` §7.1 labels it
"Uttara Bhadrapada, nakshatra #24"; `ayanamsa_mode_investigation_S75.md`
labels the SAME longitude "Shatabhisha pada 3." Nakshatra #24 is
Shatabhisha (306°40'-320°00'); Uttara Bhadrapada is #25 — the S75 file's
label is astronomically correct, S74's is a mislabel in that earlier
file. This table uses the correct name (Shatabhisha). Not fixed at the
source file — flagged here for a future S74 file correction.

**Natal Lagna gap:** Surbhi/Sheridan/David's Lagna sign/nakshatra/pada is
NOT captured in any repo fixture found — `jhora_{surbhi,sheridan,
david}.md` contain MD/AD tables only, not the full planetary-position
table `jhora_sulabh.md` has. Do not fabricate a value; this is an open
capture gap, same disposition as the ayanamsa gap above.

---

## 3. Drik Panchang Matched-Mode Vimshottari Captures

**Status: LANDED (S76).** Sulabh manually captured all 4 charts from
drikpanchang.com's Vimshottari Dasha calculator (Lahiri/Traditional
ayanamsa, site default); each chart's verbatim table + conversion +
residual arithmetic is now committed to its own diagnostic file (see
"Required to close this gap" below) — the previous OPEN placeholder's
concern (numeric quotes with no backing file) is resolved for these 4
specific figures. All 4 residuals recomputed independently via
`swe.julday()` this session, shown inline in each file.

| Chart | Starting lord | MD1 years | Drik MD1 end (local / UT / JD) | Prod row-0 (days) | Drik row-0 (days) | Residual (prod − drik) | Source |
|---|---|---|---|---|---|---|---|
| Sulabh | Guru (Jupiter) | 16y | 1989-08-04 09:48 IST → 1989-08-04 04:18 UT → JD 2447742.679167 | 482.7232 | 485.387500 | **-2.6643d** | `diagnostics/drik_vimshottari_S76_sulabh.md` |
| Surbhi | Rahu | 18y | 1999-03-05 22:04 IST → 1999-03-05 16:34 UT → JD 2451243.190278 | 2366.1560 | 2366.481945 | **-0.3259d** | `diagnostics/drik_vimshottari_S76_surbhi.md` |
| Sheridan | Ketu | 7y | 1990-04-10 21:06 SAST → 1990-04-10 19:06 UT → JD 2447992.295833 | 2142.6221 | 2144.545833 | **-1.9237d** | `diagnostics/drik_vimshottari_S76_sheridan.md` |
| David | Ketu | 7y | 1976-12-06 17:47 GMT → 1976-12-06 17:47 UT → JD 2443119.240972 | 321.2793 | 321.824305 | **-0.5450d** | `diagnostics/drik_vimshottari_S76_david.md` |

All 4 residuals are negative (production's MD1 boundary lands earlier
than Drik's in every case) and all fall well under the 5-day
STOP-and-flag threshold — no TZ/JD arithmetic anomaly triggered.

**Provenance correction, caught during this landing:** Sheridan's
residual is **-1.9237d**, matching the -1.93d figure quoted two sessions
ago — NOT the -1.78d figure quoted in the immediately preceding prompt
for the "same" claim. Direct confirmation that -1.78d was a
transcription drift, not a distinct re-measurement; the now-committed
-1.9237d figure is the one to cite going forward.

**Related, already-verified data (NOT the same thing as a Drik Panchang
capture — do not conflate):** `diagnostics/ayanamsa_mode_investigation_
S75.md` (lines 119-124) has a separate, independently traceable table of
production row-0 day-counts compared against the **JHora GUI fixture**
(not Drik Panchang) under Traditional-Lahiri vs. True-Chitrapaksha
modes:

| Chart | Row0 days (Traditional Lahiri) | Row0 days (True Chitrapaksha) |
|---|---|---|
| Sulabh | 482.7232 | 478.3557 |
| Surbhi | 2366.1560 | 2356.1331 |
| Sheridan | 2142.6221 | 2140.4425 |
| David | 321.2793 | 318.4175 |

The "Row0 days (Traditional Lahiri)" column is the same "Prod row-0"
figure used in this section's table above (single source, cited
consistently) — but that file's own residual/comparison side is against
JHora's GUI oracle, not Drik Panchang, and its residual values (+1.17d,
+1.66d, etc.) are a DIFFERENT comparison than this section's Drik
residuals. Do not merge the two residual columns.

**Required to close this gap — all 4 landed:**
- ✅ `diagnostics/drik_vimshottari_S76_sulabh.md`
- ✅ `diagnostics/drik_vimshottari_S76_surbhi.md`
- ✅ `diagnostics/drik_vimshottari_S76_sheridan.md`
- ✅ `diagnostics/drik_vimshottari_S76_david.md`

See `docs/KNOWN_DIVERGENCES.md` Gap D1 for the updated provenance note
reflecting these files.

---

## 4. Settled Empirical Findings (session-durable)

Findings below are restricted to what traces directly to
`diagnostics/ayanamsa_mode_investigation_S75.md` and
`diagnostics/vimshottari_year_length_S74.md`. Chart-specific residual
numbers tracing back to the unverified §3 Drik claim have been excluded
— see §3 for why.

- pyswisseph `SIDM_LAHIRI` ≡ JHora Traditional Lahiri to **0.14 arcsec**
  at the Sulabh (1988) and Sheridan (1984) epochs
  (`ayanamsa_mode_investigation_S75.md` lines 49-50).
- pyswisseph's True Chitrapaksha implementation diverges from JHora's
  True Chitrapaksha by **20.26" (Sulabh) / 15.07" (Sheridan)**
  (`ayanamsa_mode_investigation_S75.md` lines 61-62) — production uses
  `SIDM_LAHIRI`, so this has NO V1 impact (see
  `docs/KNOWN_DIVERGENCES.md` Gap A1).
- `year_days = 365.256363` (sidereal year) CONFIRMED via JHora
  fixture-internal arithmetic (end−start ÷ elapsed years): yields
  365.2558-365.2572 across all 9 rows, 4-chart-confirmed
  (`vimshottari_year_length_S74.md` §8 — Julian→sidereal swap flattens
  drift slope from ≈-0.0064 d/yr to ≈0 for all 4 charts, chart-
  independent). **Shipped S76** — `agent/chart_calculator.py`'s
  `_add_years()` now uses `365.256363`; full suite verified clean
  (3302 passed / 0 failed / 7 skipped / 1 xpassed, identical to the
  pre-ship baseline). Confirmed the Gap D1 row-0 residual is NOT
  affected by this change (dominated by a fixed ephemeris/ayanamsa
  offset, not year-length — pre/post-ship residuals agree to within
  0.002d across all 4 charts). `tests/fixtures/jhora_{sulabh,surbhi,
  sheridan,david}.md`'s Vimshottari MD/AD tables recaptured to match
  (see §3 for the updated residuals against Drik).
- `FLG_NOABERR` closes 68.6% of Sulabh's row-0 gap (against the JHora
  GUI oracle) but the sign of the residual varies by birth month across
  the 4-chart set — ruled DO NOT SHIP on this basis
  (`vimshottari_year_length_S74.md` §4, `ayanamsa_mode_investigation_
  S75.md`'s own follow-on).
- Row-0 fixed-offset magnitude does NOT scale linearly with any single
  chart property tested (starting-lord `total_years` alone, `balance_
  years`, `elapsed_frac`, birth epoch) — reference-frame linear-scaling
  hypothesis and fixed-angular-offset hypothesis both FALSIFIED
  (`vimshottari_year_length_S74.md` §8, "Verdict: (c) — high variance,
  unresolved").
- A ~0.94-arcminute (+0.015592°) ayanamsa discrepancy exists between
  JHora v8 GUI's own displayed Lahiri value and pyswisseph's
  `SIDM_LAHIRI` at the same Sulabh birth instant — right-signed,
  right-order-of-magnitude candidate for part of the row-0 offset, but
  **verified for Sulabh only**; the other 3 charts' ayanamsa fixture
  lines are boilerplate, not independently captured (see §2 caveat)
  (`vimshottari_year_length_S74.md` §11).
- pyjhora (open-source PyJHora port) is NOT a faithful stand-in for the
  closed-source JHora v8 GUI's Vimshottari balance-at-birth engine at
  sub-day granularity — across all 4 charts, pyjhora's computed MD1 end
  is 27x-627x closer to THIS codebase's own output than to the actual
  GUI fixture (`vimshottari_year_length_S74.md` §11).
- Gana table `Manushya × Rakshasa = 0` (classical), NOT 1 — learned
  pre-Session-46 (source predates the diagnostics convention; carried
  forward as an established convention, not re-derived here).
- Rahu/Ketu graha drishti = `(5, 7, 9)` per user-perceived-correctness
  tiebreaker (CLAUDE.md Locked Decisions / `docs/KNOWN_DIVERGENCES.md`
  Gap G1) — genuine classical fragmentation, not a calculation error.

---

## 5. External Data Already Captured — Do Not Re-Request

- JHora v8 Vimshottari + Yogini MD tables, all 4 charts:
  `tests/fixtures/jhora_sulabh.md` (full Panchanga + planetary
  positions + MD/AD), `tests/fixtures/jhora_surbhi.md`,
  `tests/fixtures/jhora_sheridan.md`, `tests/fixtures/jhora_david.md`
  (MD tables only, Session 74).
- JHora Ashtakavarga cross-chart data:
  `tests/fixtures/jhora_ashtakavarga_cross_charts.md`,
  `tests/fixtures/jhora_david_ashtakavarga.md`.
- AstroSage PDF Vimshottari fixtures:
  `tests/fixtures/astrosage_vimshottari_fixtures.md`.
- Geocoded lat/lon for all 4 charts' birthplaces:
  `tests/fixtures/geocoded_locations.json`.
- Kapoor book, plaintext OCR (7385 lines): `data/pdfs/[Deepak Kapoor]
  Astronomy and Mathematical Astrology_text.pdf` — **not**
  `project_files/classical_references/...`, which does not exist
  anywhere in this repo (confirmed both S57, per CLAUDE.md's Reference
  Materials section, and again this session).
- PVR Narasimha Rao, *Vedic Astrology: An Integrated Approach*:
  `data/pdfs/Vedic Astrology_ PVR Narashimha Rao.pdf` (same directory,
  same correction applies).
- Reference chart source PDFs (verified filenames, exact case/spacing):
  `data/pdfs/VedicReport5-24-202610-01-26PM.pdf` (Sulabh),
  `data/pdfs/Wife_VedicReport.pdf` (Surbhi),
  `data/pdfs/Sheridan Kundli.pdf`,
  `data/pdfs/David Kundli.pdf`.
- Classical RAG corpus (14 texts, ~7,281 chunks, ChromaDB) — see
  CLAUDE.md's Reference Materials section for the full list; not
  duplicated here since it's a corpus, not a discrete capture.

---

## 6. Append Protocol

Any session that receives new external data (Drik, AstroSage, JHora,
Prokerala, book citations) MUST append to this file in the session-close
commit.

**No entry is accepted into this file unless it is traceable to a
committed file** (fixture, diagnostic, or classical reference). A
design-chat or session-log assertion alone is not sufficient provenance
— land the source file first (as a fixture or diagnostic), then cite it
here. (This rule exists because of §3 above: the same unwritten "S75
Drik capture" was quoted three different ways across three different
prompts, with no file anyone could check it against.)

Entry format:

```
<Sxx> — <topic>
Source: <file path — fixture / diagnostic / classical reference PDF>
Data: <verbatim or table>
Supersedes: <prior entry ref if any>
```
