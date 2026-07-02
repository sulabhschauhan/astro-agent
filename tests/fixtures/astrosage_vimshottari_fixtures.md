# AstroSage Vimshottari Dasha Reference Fixtures (4 charts)

**Source:** AstroSage Kundli PDF reports, `Vimshottari Dasha` table, page 3
of each report (extracted via pdfplumber's `page.extract_tables()`, not
hand-transcribed -- each Mahadasha block is its own clean table: a header
row `"<LORD> -<N> Years\n<start> - <end>"` followed by 9 Antardasha rows
`[<LORD>, <date>]`).

**Captured:** 2026-07-02 (S44.2c)

**Date format:** D/M/YY as printed (Indian convention), verbatim from the
PDFs -- not normalized/reformatted here.

## Provenance note -- Sulabh duplicate-PDF resolution (S44.2c Step 1)

Two Sulabh report files exist: `VedicReport5-24-202610-01-26PM.pdf`
(committed in `data/pdfs/`, printed 5/24/2026 10:01:25 PM) and
`VedicReport5-24-202610-01-51PM.pdf` (Downloads only, printed 5/24/2026
10:01:50 PM, generated ~25s later -- not present in this repo). The two
variants' page-3 raw text was diffed line-by-line: **identical** except for
the `Printing Date` footer timestamp (10:01:25 PM vs 10:01:50 PM) -- same
underlying chart, regenerated twice. Every Vimshottari Dasha date,
planetary position, Ashtakvarga cell, and Chalit table entry is
byte-identical between the two. The committed `...26PM.pdf` is therefore
canonical; this fixture is built from it exclusively.

| Chart | Source file | Page | Capture date |
|---|---|---|---|
| Sulabh | `data/pdfs/VedicReport5-24-202610-01-26PM.pdf` | 3 | 2026-07-02 |
| Surbhi | `data/pdfs/Wife_VedicReport.pdf` | 3 | 2026-07-02 |
| Sheridan | `data/pdfs/Sheridan Kundli.pdf` | 3 | 2026-07-02 |
| David | `data/pdfs/David Kundli.pdf` | 3 | 2026-07-02 |

---

## Sulabh

### 9-Mahadasha table

| Lord | Duration | Start | End |
|---|---|---|---|
| JUP | 16 Years | 6/ 4/88 | 4/ 8/89 |
| SAT | 19 Years | 4/ 8/89 | 4/ 8/08 |
| MER | 17 Years | 4/ 8/08 | 4/ 8/25 |
| KET | 7 Years | 4/ 8/25 | 4/ 8/32 |
| VEN | 20 Years | 4/ 8/32 | 4/ 8/52 |
| SUN | 6 Years | 4/ 8/52 | 4/ 8/58 |
| MON | 10 Years | 4/ 8/58 | 4/ 8/68 |
| MAR | 7 Years | 4/ 8/68 | 4/ 8/75 |
| RAH | 18 Years | 4/ 8/75 | 4/ 8/93 |

### Antardasha rows (9 per Mahadasha; date = AD start; `00/00/00` = AD already running at birth)

**JUP MD (6/4/88 - 4/8/89):** JUP 00/00/00, SAT 00/00/00, MER 00/00/00, KET 00/00/00, VEN 00/00/00, SUN 00/00/00, MON 00/00/00, MAR 00/00/00, RAH 4/8/89

**SAT MD (4/8/89 - 4/8/08):** SAT 7/8/92, MER 16/4/95, KET 25/5/96, VEN 25/7/99, SUN 7/7/00, MON 7/2/02, MAR 16/3/03, RAH 22/1/06, JUP 4/8/08

**MER MD (4/8/08 - 4/8/25):** MER 1/1/11, KET 28/12/11, VEN 28/10/14, SUN 4/9/15, MON 4/2/17, MAR 1/2/18, RAH 19/8/20, JUP 25/11/22, SAT 4/8/25

**KET MD (4/8/25 - 4/8/32):** KET 1/1/26, VEN 1/3/27, SUN 7/7/27, MON 7/2/28, MAR 4/7/28, RAH 22/7/29, JUP 28/6/30, SAT 7/8/31, MER 4/8/32

**VEN MD (4/8/32 - 4/8/52):** VEN 4/12/35, SUN 4/12/36, MON 4/8/38, MAR 4/10/39, RAH 4/10/42, JUP 4/6/45, SAT 4/8/48, MER 4/6/51, KET 4/8/52

**SUN MD (4/8/52 - 4/8/58):** SUN 22/11/52, MON 22/5/53, MAR 28/9/53, RAH 22/8/54, JUP 10/6/55, SAT 22/5/56, MER 28/3/57, KET 4/8/57, VEN 4/8/58

**MON MD (4/8/58 - 4/8/68):** MON 4/6/59, MAR 4/1/60, RAH 4/7/61, JUP 4/11/62, SAT 4/6/64, MER 4/11/65, KET 4/6/66, VEN 4/2/68, SUN 4/8/68

**MAR MD (4/8/68 - 4/8/75):** MAR 1/1/69, RAH 19/1/70, JUP 25/12/70, SAT 4/2/72, MER 1/2/73, KET 28/6/73, VEN 28/8/74, SUN 4/1/75, MON 4/8/75

**RAH MD (4/8/75 - 4/8/93):** RAH 16/4/78, JUP 10/9/80, SAT 16/7/83, MER 4/2/86, KET 22/2/87, VEN 22/2/90, SUN 16/1/91, MON 16/7/92, MAR 4/8/93

---

## Surbhi

### 9-Mahadasha table

| Lord | Duration | Start | End |
|---|---|---|---|
| RAH | 18 Years | 11/ 9/92 | 5/ 3/99 |
| JUP | 16 Years | 5/ 3/99 | 5/ 3/15 |
| SAT | 19 Years | 5/ 3/15 | 5/ 3/34 |
| MER | 17 Years | 5/ 3/34 | 5/ 3/51 |
| KET | 7 Years | 5/ 3/51 | 5/ 3/58 |
| VEN | 20 Years | 5/ 3/58 | 5/ 3/78 |
| SUN | 6 Years | 5/ 3/78 | 5/ 3/84 |
| MON | 10 Years | 5/ 3/84 | 5/ 3/94 |
| MAR | 7 Years | 5/ 3/94 | 5/ 3/01 |

### Antardasha rows

**RAH MD (11/9/92 - 5/3/99):** RAH 00/00/00, JUP 00/00/00, SAT 00/00/00, MER 00/00/00, KET 23/9/92, VEN 23/9/95, SUN 17/8/96, MON 17/2/98, MAR 5/3/99

**JUP MD (5/3/99 - 5/3/15):** JUP 23/4/01, SAT 5/11/03, MER 11/2/06, KET 17/1/07, VEN 17/9/09, SUN 5/7/10, MON 5/11/11, MAR 11/10/12, RAH 5/3/15

**SAT MD (5/3/15 - 5/3/34):** SAT 8/3/18, MER 17/11/20, KET 26/12/21, VEN 26/2/25, SUN 8/2/26, MON 8/9/27, MAR 17/10/28, RAH 23/8/31, JUP 5/3/34

**MER MD (5/3/34 - 5/3/51):** MER 2/8/36, KET 29/7/37, VEN 29/5/40, SUN 5/4/41, MON 5/9/42, MAR 2/9/43, RAH 20/3/46, JUP 26/6/48, SAT 5/3/51

**KET MD (5/3/51 - 5/3/58):** KET 2/8/51, VEN 2/10/52, SUN 8/2/53, MON 8/9/53, MAR 5/2/54, RAH 23/2/55, JUP 29/1/56, SAT 8/3/57, MER 5/3/58

**VEN MD (5/3/58 - 5/3/78):** VEN 5/7/61, SUN 5/7/62, MON 5/3/64, MAR 5/5/65, RAH 5/5/68, JUP 5/1/71, SAT 5/3/74, MER 5/1/77, KET 5/3/78

**SUN MD (5/3/78 - 5/3/84):** SUN 23/6/78, MON 23/12/78, MAR 29/4/79, RAH 23/3/80, JUP 11/1/81, SAT 23/12/81, MER 29/10/82, KET 5/3/83, VEN 5/3/84

**MON MD (5/3/84 - 5/3/94):** MON 5/1/85, MAR 5/8/85, RAH 5/2/87, JUP 5/6/88, SAT 5/1/90, MER 5/6/91, KET 5/1/92, VEN 5/9/93, SUN 5/3/94

**MAR MD (5/3/94 - 5/3/01):** MAR 2/8/94, RAH 20/8/95, JUP 26/7/96, SAT 5/9/97, MER 2/9/98, KET 29/1/99, VEN 29/3/00, SUN 5/8/00, MON 5/3/01

---

## Sheridan

### 9-Mahadasha table

| Lord | Duration | Start | End |
|---|---|---|---|
| KET | 7 Years | 27/ 5/84 | 10/ 4/90 |
| VEN | 20 Years | 10/ 4/90 | 10/ 4/10 |
| SUN | 6 Years | 10/ 4/10 | 10/ 4/16 |
| MON | 10 Years | 10/ 4/16 | 10/ 4/26 |
| MAR | 7 Years | 10/ 4/26 | 10/ 4/33 |
| RAH | 18 Years | 10/ 4/33 | 10/ 4/51 |
| JUP | 16 Years | 10/ 4/51 | 10/ 4/67 |
| SAT | 19 Years | 10/ 4/67 | 10/ 4/86 |
| MER | 17 Years | 10/ 4/86 | 10/ 4/03 |

### Antardasha rows

**KET MD (27/5/84 - 10/4/90):** KET 00/00/00, VEN 7/11/84, SUN 13/3/85, MON 13/10/85, MAR 10/3/86, RAH 28/3/87, JUP 4/3/88, SAT 13/4/89, MER 10/4/90

**VEN MD (10/4/90 - 10/4/10):** VEN 10/8/93, SUN 10/8/94, MON 10/4/96, MAR 10/6/97, RAH 10/6/00, JUP 10/2/03, SAT 10/4/06, MER 10/2/09, KET 10/4/10

**SUN MD (10/4/10 - 10/4/16):** SUN 28/7/10, MON 28/1/11, MAR 4/6/11, RAH 28/4/12, JUP 16/2/13, SAT 28/1/14, MER 4/12/14, KET 10/4/15, VEN 10/4/16

**MON MD (10/4/16 - 10/4/26):** MON 10/2/17, MAR 10/9/17, RAH 10/3/19, JUP 10/7/20, SAT 10/2/22, MER 10/7/23, KET 10/2/24, VEN 10/10/25, SUN 10/4/26

**MAR MD (10/4/26 - 10/4/33):** MAR 7/9/26, RAH 25/9/27, JUP 1/9/28, SAT 10/10/29, MER 7/10/30, KET 4/3/31, VEN 4/5/32, SUN 10/9/32, MON 10/4/33

**RAH MD (10/4/33 - 10/4/51):** RAH 22/12/35, JUP 16/5/38, SAT 22/3/41, MER 10/10/43, KET 28/10/44, VEN 28/10/47, SUN 22/9/48, MON 22/3/50, MAR 10/4/51

**JUP MD (10/4/51 - 10/4/67):** JUP 28/5/53, SAT 10/12/55, MER 16/3/58, KET 22/2/59, VEN 22/10/61, SUN 10/8/62, MON 10/12/63, MAR 16/11/64, RAH 10/4/67

**SAT MD (10/4/67 - 10/4/86):** SAT 13/4/70, MER 22/12/72, KET 1/2/74, VEN 1/4/77, SUN 13/3/78, MON 13/10/79, MAR 22/11/80, RAH 28/9/83, JUP 10/4/86

**MER MD (10/4/86 - 10/4/03):** MER 7/9/88, KET 4/9/89, VEN 4/7/92, SUN 10/5/93, MON 10/10/94, MAR 7/10/95, RAH 25/4/98, JUP 1/8/00, SAT 10/4/03

---

## David

### 9-Mahadasha table

| Lord | Duration | Start | End |
|---|---|---|---|
| KET | 7 Years | 19/ 1/76 | 7/12/76 |
| VEN | 20 Years | 7/12/76 | 7/12/96 |
| SUN | 6 Years | 7/12/96 | 7/12/02 |
| MON | 10 Years | 7/12/02 | 7/12/12 |
| MAR | 7 Years | 7/12/12 | 7/12/19 |
| RAH | 18 Years | 7/12/19 | 7/12/37 |
| JUP | 16 Years | 7/12/37 | 7/12/53 |
| SAT | 19 Years | 7/12/53 | 7/12/72 |
| MER | 17 Years | 7/12/72 | 7/12/89 |

### Antardasha rows

**KET MD (19/1/76 - 7/12/76):** KET 00/00/00, VEN 00/00/00, SUN 00/00/00, MON 00/00/00, MAR 00/00/00, RAH 00/00/00, JUP 00/00/00, SAT 10/12/75, MER 7/12/76

**VEN MD (7/12/76 - 7/12/96):** VEN 7/4/80, SUN 7/4/81, MON 7/12/82, MAR 7/2/84, RAH 7/2/87, JUP 7/10/89, SAT 7/12/92, MER 7/10/95, KET 7/12/96

**SUN MD (7/12/96 - 7/12/02):** SUN 25/3/97, MON 25/9/97, MAR 1/2/98, RAH 25/12/98, JUP 13/10/99, SAT 25/9/00, MER 1/8/01, KET 7/12/01, VEN 7/12/02

**MON MD (7/12/02 - 7/12/12):** MON 7/10/03, MAR 7/5/04, RAH 7/11/05, JUP 7/3/07, SAT 7/10/08, MER 7/3/10, KET 7/10/10, VEN 7/6/12, SUN 7/12/12

**MAR MD (7/12/12 - 7/12/19):** MAR 4/5/13, RAH 22/5/14, JUP 28/4/15, SAT 7/6/16, MER 4/6/17, KET 1/11/17, VEN 1/1/19, SUN 7/5/19, MON 7/12/19

**RAH MD (7/12/19 - 7/12/37):** RAH 19/8/22, JUP 13/1/25, SAT 19/11/27, MER 7/6/30, KET 25/6/31, VEN 25/6/34, SUN 19/5/35, MON 19/11/36, MAR 7/12/37

**JUP MD (7/12/37 - 7/12/53):** JUP 25/1/40, SAT 7/8/42, MER 13/11/44, KET 19/10/45, VEN 19/6/48, SUN 7/4/49, MON 7/8/50, MAR 13/7/51, RAH 7/12/53

**SAT MD (7/12/53 - 7/12/72):** SAT 10/12/56, MER 19/8/59, KET 28/9/60, VEN 28/11/63, SUN 10/11/64, MON 10/6/66, MAR 19/7/67, RAH 25/5/70, JUP 7/12/72

**MER MD (7/12/72 - 7/12/89):** MER 4/5/75, KET 1/5/76, VEN 1/3/79, SUN 7/1/80, MON 7/6/81, MAR 4/6/82, RAH 22/12/84, JUP 28/3/87, SAT 7/12/89

---

## Cross-oracle notes

### Sulabh -- AstroSage vs JHora (Mercury -> Ketu transition)

- AstroSage (this fixture): MER MD ends / KET MD starts on **4/8/25** (4 Aug 2025).
- JHora (`tests/fixtures/jhora_sulabh.md` line 112): `Ket | 2025-07-28 (16:55:08) | 2032-07-28 (12:07:52)` -- Ketu MD starts **2025-07-28** (28 Jul 2025).
- **Delta: 7 days.** Same documented drift class as the ±37-day Antardasha
  drift already noted in `chart_calculator.py`'s `_calc_dasha` DASHA
  ACCURACY NOTE -- not a new divergence, not investigated further here.

### David -- AstroSage vs existing project oracle (Ketu -> Venus transition)

- AstroSage (this fixture): KET MD ends / VEN MD starts on **7/12/76** (7 Dec 1976).
- `tests/manual/dasha_timezone_check.py` line 103:
  `EXPECTED_TRANSITION = date(1976, 12, 7)  # AstroSage: Ketu balance 0Y 10M 17D`.
- **Exact match** -- this fixture's AstroSage-sourced KET->VEN transition
  date corroborates `dasha_timezone_check.py`'s existing oracle precisely
  (not just within its documented ±1-day tolerance).

### Pratyantar tables -- present, not included here

All 4 PDFs also carry a separately-titled `Vimshottari Dasha - Pratyantar`
section (3-level MD->AD->Pratyantar date breakdown) at later pages --
Sulabh: pages 45-46 (verified this session); other charts at equivalent
pages given the identical 56-page report layout. Parked as a candidate V1.1
oracle for unlocking the currently-suppressed Pratyantar granularity (see
`chart_calculator.py`'s `_calc_dasha` DASHA ACCURACY NOTE: "Pratyantar
dates computed but suppressed from output -- wrong lord at this
granularity due to drift"). Not extracted or included in this fixture --
out of scope for S44.2c.
