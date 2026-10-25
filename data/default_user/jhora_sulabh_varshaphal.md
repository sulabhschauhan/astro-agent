# JHora Varshaphal (Tajaka Annual) Oracle — Sulabh

Source: Jagannatha Hora desktop (Sulabh.jhd). Pulled 2026-10-24 (S156).
Pull method: Tajaka tab → set Year → "Find Tajaka Chart" → read D-1 of the Tajaka annual position table.

## Provenance / no-curve-fit audit (S156)

Every value here traces to a PRIMARY source or the JHora desktop oracle. Nothing is tuned to hit a number.
- **A (pravesh + cast):** conventions (SIDM_LAHIRI, FLG_TRUEPOS, true-ayanamsa, true sidereal return) were each *derived empirically then confirmed* against the 3 held-out JHora instants (planets <0.2", Muntha exact). The only numeric threshold (boundary ε=2°) is justified from ±8-min birth-time uncertainty, independent of the test charts.
- **B (Muntha):** pure arithmetic (natal Lagna lon + whole signs). Exact.
- **C1 (Pancha-vargeeya):** = literal Raman §32-37 tier values (30/15/7.5 …); NOT fitted. 17/21 exact. The Moon/Merc-neutral residual is left HONESTLY UNFITTED — the fits that would close it (neutral→friend, 4-tier, positional, compound) were all tested and REJECTED because they broke other planets; forcing Moon would be curve-fitting, so it is documented instead.
- **C2 (year-lord):** selection rules are Raman / shankerstudy Upload 38 text, not invented.
HONEST CAVEAT: "everything matches" is true for A/B and 17/21 of C1; it is NOT true to the last decimal for Moon/Merc in C1. That gap is real, bounded, non-impactful on the year-lord, and deliberately not papered over.

## Fixed inputs

- **Ayanamsa:** Traditional Lahiri, no correction (Subtract 0-0-0). swe equivalent to CONFIRM = `SIDM_LAHIRI`.
- **Natal:** 1988-04-06 00:30:00 IST (+5:30), Calcutta Bara Bazar 88E21'00", 22N34'00". Natal ayanamsa 23-41-35.07.
- **Pravesh cast place = BIRTHPLACE (Calcutta)**, NOT residence (Dubai). JHora default. [DOCTRINE FORK — engine default = birthplace to match oracle; residence as config option; Sulabh to ratify product behaviour.]
- **Return method = TRUE sidereal solar return** (root-find Sun sidereal longitude back to natal). Evidence: uneven ~6h/yr drift + identical Sun longitude across years. DO NOT reuse the Ashtottari mean-sidereal-year helper.

## Sulabh natal chart (D1) — reference (JHora desktop, Lahiri)

Birth: **1988-04-06, 00:30:00 IST (+5:30)**, Calcutta Bara Bazar (88E21'00", 22N34'00"). Ayanamsa 23-41-35.07. **Lagna Sagittarius 22°40'59.06"**; **birth nakshatra Visakha** (Moon, pada 4); Sun/Moon lord of... (see below). Janma Ghatis 47.5308; Vedic weekday Tuesday (Ma).

```
Body    Longitude          Nak    Pada Rasi Nav  (Karaka)
Lagna   22 Sg 40'59.06"    PSha   3    Sg   Li
Sun     22 Pi 30'56.53"    Reva   2    Pi   Cp   (AK)   <- annual-return anchor
Moon     2 Sc 13'56.28"    Visa   4    Sc   Cn   (GK)   <- birth nakshatra Visakha
Mars     5 Cp 33'42.75"    USha   3    Cp   Aq   (PK)
Mercury  7 Pi 52'23.63"    UBha   2    Pi   Vi   (PiK)
Jupiter 12 Ar 33'29.29"    Aswi   4    Ar   Cn   (AmK)
Venus    8 Ta 19'39.31"    Krit   4    Ta   Pi   (MK)
Saturn   8 Sg 50'14.60"    Mool   3    Sg   Ge   (BK)
Rahu    28 Aq 24'06.40"    PBha   3    Aq   Ge   (DK)
Ketu    28 Le 24'06.40"    UPha   1    Le   Sg
Maandi   2 Li 13'37.36"    Chit   3    Li   Li
Gulika  22 Vi 14'24.62"    Hast   4    Vi   Cn
```
Derived & used downstream: Lagna lord = Jupiter (Sg); Muntha degree = natal Lagna degree 22°40'59.06" (B); birth-nakshatra no. Visakha = 16 (Mudda seed formula needs a +2 calibration vs oracle — pin in E). Natal D1 also lives in data/default_user (dashas oracle); duplicated here so this file is self-contained.

## Validation anchors (the gates)

- **Sun return longitude (sub-engine A convergence target):** 22 Pi 30' 56.53" sidereal (Lahiri), identical in all three annual charts = natal sidereal Sun. Root-finder tolerance <0.01".
- **Ayanamsa precession check:** 50.29"/yr (2025→26), 50.30"/yr (2026→27); natal→2025 back-checks 50.29"/yr over 37yr. Consistent with Lahiri. ✓
- **Muntha rule (sub-engine B — PINNED):** constant degree 22°40'59.06" across all years; sign advances exactly one per year (Cp→Aq→Pi). Muntha = natal_Lagna_lon + whole-sign steps, degree preserved.
- **Boundary case:** 2026 annual Lagna 1°21' Libra (~1.4° past Vi/Li cusp) = hardest-case boundary_flag test.

## Varsha Pravesh instants (sub-engine A)

| Year | Date | Time (IST +5:30) | Ayanamsa at instant | Sidereal Time |
|------|------|------------------|---------------------|---------------|
| 2025 | 2025-04-06 | 12:14:10 | 24-12-35.82 | 1:36:49 |
| 2026 | 2026-04-06 | 18:28:46 | 24-13-26.11 | 7:51:29 |
| 2027 | 2027-04-07 | 00:26:57 | 24-14-16.41 | 13:49:43 |

Place for all: 88 E 21' 00", 22 N 34' 00" (Calcutta). Annual Moon (Mudda seed): 2025 Pushya p2 (Sa) · 2026 Anuradha p3 (Sa) · 2027 Revati p2 (Me).

## Annual D-1 position tables (verbatim)

### 2025 (Lagna 6 Cn 29' 08.46", Pushya p1)
```
Body                    Longitude        Nak   Pada Rasi Nav
Lagna                    6 Cn 29' 08.46" Push  1    Cn   Le
Sun - BK                22 Pi 30' 56.53" Reva  2    Pi   Cp
Moon - MK                6 Cn 57' 40.18" Push  2    Cn   Vi
Mars - GK                1 Cn 12' 02.84" Puna  4    Cn   Cn
Mercury (R) - PiK        2 Pi 40' 46.39" PBha  4    Pi   Cn
Jupiter - AmK           22 Ta 37' 03.83" Rohi  4    Ta   Cn
Venus (R) - PK           1 Pi 20' 28.40" PBha  4    Pi   Cn
Saturn - DK              0 Pi 54' 53.63" PBha  4    Pi   Cn
Rahu - AK                2 Pi 14' 30.85" PBha  4    Pi   Cn
Ketu                     2 Vi 14' 30.85" UPha  2    Vi   Cp
Maandi                  20 Le 37' 24.28" PPha  3    Le   Li
Gulika                  10 Le 00' 54.38" Magh  4    Le   Cn
Muntha                  22 Cp 40' 59.06" Srav  4    Cp   Cn
```
Special pts: Bhava Lagna 3Cn42 · Hora Lagna 15Li10 · Ghati Lagna 19Le34 · Sree Lagna 14Li26 · Indu 6Aq57 · Bhrigu Bindu 4Ta36. (Full upagraha/sphuta list in session transcript.)

### 2026 (Lagna 1 Li 21' 44.24", Chitra p3)
```
Body                    Longitude        Nak   Pada Rasi Nav
Lagna                    1 Li 21' 44.24" Chit  3    Li   Li
Sun - AmK               22 Pi 30' 56.53" Reva  2    Pi   Cp
Moon - PK               12 Sc 28' 06.96" Anu   3    Sc   Li
Mars - DK                3 Pi 13' 52.70" PBha  4    Pi   Cn
Mercury - AK            24 Aq 55' 00.40" PBha  2    Aq   Ta
Jupiter - BK            21 Ge 57' 43.90" Puna  1    Ge   Ar
Venus - PiK             14 Ar 14' 21.24" Bhar  1    Ar   Le
Saturn - GK             12 Pi 01' 00.12" UBha  3    Pi   Li
Rahu - MK               12 Aq 53' 09.75" Sata  2    Aq   Cp
Ketu                    12 Le 53' 09.75" Magh  4    Le   Cn
Maandi                  22 Li 01' 02.22" Visa  1    Li   Ar
Gulika                  12 Li 17' 50.65" Swat  2    Li   Cp
Muntha                  22 Aq 40' 59.06" PBha  1    Aq   Ar
```
Special pts: Bhava Lagna 7Li02 · Hora Lagna 22Ar06 · Ghati Lagna 7Sg17 · Sree Lagna 8Ge00 · Indu 12Li28 · Bhrigu Bindu 27Ge40.

### 2027 (Lagna 21 Sg 55' 51.25", P.Ashadha p3)
```
Body                    Longitude        Nak   Pada Rasi Nav
Lagna                   21 Sg 55' 51.25" PSha  3    Sg   Li
Sun - MK                22 Pi 30' 56.53" Reva  2    Pi   Cp
Moon - PiK              20 Pi 00' 07.68" Reva  2    Pi   Cp
Mars - AK               26 Cn 50' 54.84" Asre  4    Cn   Pi
Mercury - DK             2 Pi 09' 59.52" PBha  4    Pi   Cn
Jupiter (R) - BK        22 Cn 49' 01.30" Asre  2    Cn   Cp
Venus - PK              19 Aq 34' 47.56" Sata  4    Aq   Pi
Saturn - AmK            23 Pi 18' 59.91" Reva  2    Pi   Cp
Rahu - GK               23 Cp 31' 50.82" Dhan  1    Cp   Le
Ketu                    23 Cn 31' 50.82" Asre  3    Cn   Aq
Maandi                   2 Li 12' 57.09" Chit  3    Li   Li
Gulika                  22 Vi 14' 41.16" Hast  4    Vi   Cn
Muntha                  22 Pi 40' 59.06" Reva  2    Pi   Cp
```
Special pts: Bhava Lagna 6Cp17 · Hora Lagna 20Li50 · Ghati Lagna 4Pi29 · Sree Lagna 21Pi59 · Indu 20Aq00 · Bhrigu Bindu 21Aq45.

## Panchanga (verbatim, per pravesh)

**2025:** Lunar Yr-Mo Viswa-vasu / Chaitra · Tithi Sukla Navami (Su) 29.62% left · Wkdy Sunday (Mo:Su) · Nak Pushyami (Sa) 72.79% left · Yoga Sukarman (Ma) · Karana Kaulava (Ma) · Hora Lord Mars · Kaala Lord Venus · Sunrise 5:28:18 · Sunset 17:50:03 · Janma Ghatis 16.9113.

**2026:** Lunar Yr-Mo Parabhava / Chaitra · Tithi Krishna Panchami (Ju) 83.73% left · Wkdy Monday (Mo) · Nak Anuraadha (Sa) 31.49% left · Yoga Vyatipata (Ra) · Karana Kaulava (Ma) · Hora Lord Mercury · Kaala Lord Jupiter · Sunrise 5:28:30 · Sunset 17:49:57 · Janma Ghatis 32.5106.

**2027:** Lunar Yr-Mo Parabhava / Phalguna · Tithi Amavasya (Ra) 20.95% left · Wkdy Tuesday (Ma) · Nak Revati (Me) 74.98% left · Yoga Indra (Ra) · Karana Naga (Me) · Hora Lord Moon · Kaala Lord Mars · Sunrise 5:28:45 · Sunset 17:49:54 · Janma Ghatis 47.4252.

## Pancha-vargeeya Bala (sub-engine C1 oracle)

Classification bands (classical Tajika, NOT tuned): ≥15 Very Strong · 10–15 Powerful · 5–10 Ordinary · <5 weak.
ANCHOR: Sun = 11.70 identical all 3 yrs (same longitude every return → constant varga strength). Sun's cross-year CONSTANCY also PROVES the relationship basis is NATURAL (naisargika), not positional/temporal — a positional model would vary Sun's Kshetra yearly as other planets move.

CORRECTED 2025 (S156 re-pull, Year-set-first): the earlier 2025 column was the NATAL chart (mini-charts were labelled "Natal Chart"). True 2025 ANNUAL below.

| Planet | 2025 | 2026 | 2027 |
|--------|------|------|------|
| Sun | 11.70 Powerful | 11.70 Powerful | 11.70 Powerful |
| Moon | 15.41 Very Strong | 6.51 Ord | 10.99 Powerful |
| Mars | 10.12 Powerful | 10.58 Powerful | 6.59 Ord |
| Mercury | 5.03 Ord | 7.12 Ord | 5.04 Ord |
| Jupiter | 7.89 Ord | 9.64 Ord | 14.82 Powerful |
| Venus | 10.85 Powerful | 9.21 Ord | 10.21 Powerful |
| Saturn | 6.05 Ord | 5.12 Ord | 5.43 Ord |

### C1 method status (S156) — SOLVED (Model A, Raman), avg 0.358, 17/21 exact
SOURCE: B.V. Raman "Varshaphala or The Hindu Progressed Horoscope" (data/pdfs/..._djvu.txt, §32–37).
MODEL (production): per planet, relationship to the DIVISION LORD (NOT dignity), **natural (naisargika) friendship**, **3-tier**: own→max, friend→max/2, **neutral & enemy both → max/4 (inimical)** [Raman has only Mitra/Swa/Satru — no Sama tier].
- Kshetra (D1 sign lord): 30 / 15 / 7.5
- Hadda (Egyptian-terms lord, D1): 15 / 7.5 / 3.75
- Drekkana (D3 sign lord): 10 / 5 / 2.5
- Navamsa (D9 sign lord): 5 / 2.5 / 1.25
- Uchcha: circular |lon − (deep-exalt+180)| capped ≤180, ÷9 (= pd/180×20). Exalt lons [10,33,298,165,95,357,200].
- total = ΣΣ ÷ 4; bands ≥15 VeryStrong / 10–15 Powerful / 5–10 Ordinary / <5 weak.
PROVEN: natural (not positional) by Sun's cross-year constancy. Sun/Mars/Merc(25,27)/Jup/Ven/Sat all EXACT ×3.
KNOWN RESIDUAL (bounded, documented): Moon all 3 yrs (−0.62/−1.56/−3.44) + Mercury 2026 (−1.87) under-predicted — Moon's NEUTRAL relationships score higher in JHora than "inimical," but neutral→friend breaks Venus, and compound/4-tier/positional models are all worse (tested: Model A 0.358 < compound 1.16 < own/half 1.46 < 4-tier 2.66 < positional 3.26). NOT curve-fitted (Model A = literal Raman). Refine later if a Moon-dominant chart needs it.
NOT LOAD-BEARING after all: residual does NOT change the year-lord — Moon still wins 2025 decisively (14.79 vs 10.85). Model A → correct YL Moon/Jupiter/Jupiter.

## Harsha Bala + Dwadasa-vargeeya (2026)

Harsha: Sun 5 Little · Moon 10 Average · Mars 10 Average · Mercury 5 Little · Jupiter 0 Nil · Venus 10 Average · Saturn 5 Little.
Dwadasa-vargeeya (/12): Sun 4 · Moon 7 · Mars 7 · Mercury 7 · Jupiter 4 · Venus 1 · Saturn 3.

## Mudda / Varsha-Vimshottari Dasa (sub-engine E)

SEED (VALIDATED S156, 3/3 yrs): **R = (completed_years + birth_nakshatra_no) mod 9; starting lord = Vimshottari_seq[(R-1) mod 9]** where seq=[Ket,Ven,Sun,Moon,Mars,Rah,Jup,Sat,Merc]. Birth nak Visakha=16 → 2025 Sat / 2026 Merc / 2027 Ket (exact). The shankerstudy "(…−2)/9" is OCR-wrong (+2 off); the "×3 / 30-day-month" period rule is ALSO wrong. CAVEAT: validated on 1 chart × 3 yrs — confirm on a 2nd chart before locking (coincidental cancellation possible).
PERIOD model (VALIDATED): cycle = ACTUAL solar year (pravesh→next pravesh ≈ 365.25d), NOT 360d; periods ≈ Vimshottari-proportional (7/20/6/10/7/18/16/19/17 /120 × cycle). Most MDs <0.5d; Ven +1.7d / Sat −1.7d deviate → a sub-division nuance to pin in the build (not pure proportional). Naive annual-Moon-nakshatra-lord rule does NOT reproduce JHora. These 3 sequences are the spec.

```
2025 (MD start times):
Sat  2025-02-13 03:04:59   Merc 2025-04-11 07:12:52   Ket 2025-06-02 23:01:19
Ven  2025-06-24 22:27:39   Sun  2025-08-26 15:29:03   Moon 2025-09-14 05:15:16
Mars 2025-10-14 18:24:14   Rah  2025-11-04 20:09:45   Jup 2025-12-28 04:12:35  (→ 2026-02-13 09:17:32)

2026 (MD start times):
Merc 2026-02-18 20:04:00   Ket  2026-04-11 01:19:32   Ven 2026-05-02 13:44:33
Sun  2026-07-04 02:41:35   Moon 2026-07-22 23:30:35   Mars 2026-08-23 06:38:57
Rah  2026-09-13 23:08:43   Jup  2026-11-07 14:18:22   Sat 2026-12-25 00:03:49  (→ 2027-02-19 02:07:27)

2027 (MD start times):
Ket  2027-03-18 13:10:38   Ven  2027-04-08 18:44:46   Sun 2027-06-09 18:22:50
Moon 2027-06-28 14:57:04   Mars 2027-07-30 01:37:10   Rah 2027-08-20 23:11:52
Jup  2027-10-15 07:24:30   Sat  2027-12-02 03:53:16   Merc 2028-01-27 04:06:47  (→ 2028-03-17 19:26:02)
```

## Patyayini Dasa (sub-engine E)

MECHANIC (VALIDATED S156, order exact 2025+2026): bodies = 7 planets + Lagna (Asc); nodes EXCLUDED. (1) ORDER = ascending degree-within-sign ("reject the signs", Raman §49). (2) Patyamsha(body) = its degree-in-sign − previous body's degree-in-sign (first body = its own degree); these telescope to max_degree. (3) PERIOD(days) = cycle_days × Patyamsha / max_degree_in_sign; runs in sorted order from pravesh. Verified: every 2025 period back-solves exactly (Sat 0.91→14.8d … Sun gap 15.55→249d; sum=cycle). Durations vary widely; Asc is a dasa lord. Oracle:

```
2025 (MD start times):
Sat  2025-04-06 12:14:10   Mars 2025-04-21 08:57:56   Ven 2025-04-26 00:59:21
Merc 2025-04-28 08:06:24   Asc  2025-05-20 08:44:17   Moon 2025-07-22 17:52:56
Sun  2025-07-30 15:54:39   Jup  2026-04-05 02:52:55   Sat 2026-04-06 18:28:46  (→ 2026-04-21 15:03:08)

2026 (MD start times):
Asc  2026-04-06 18:28:46   Mars 2026-04-26 21:08:47   Sat 2026-05-24 19:33:00
Moon 2026-10-03 19:03:41   Ven  2026-10-10 09:55:30   Jup 2026-11-05 02:55:18
Sun  2027-02-23 03:47:55   Merc 2027-03-03 02:45:53   Asc 2027-04-07 00:26:57  (→ 2027-04-27 03:13:42)

2027 (MD start times):
Merc 2027-04-07 00:26:57   Ven  2027-05-06 18:46:40   Moon 2028-01-06 00:30:16
Asc  2028-01-31 10:17:48   Sun  2028-02-08 03:50:18   Jup 2028-02-12 03:39:22
Sat  2028-02-18 18:48:42   Mars 2028-04-06 06:36:04   Merc 2028-05-06 00:56:51
```

## Year-lord / Varshesvara (sub-engine C2) — DERIVED, NOT ORACLE

JHora does NOT declare a Varshesvara → NO desktop oracle. Winners below are HAND-COMPUTED from the book Panchadhikari rule applied to JHora oracle inputs (positions + PV bala). Engine↔this agreement proves correct book-rule TRANSCRIPTION (fidelity), NOT doctrinal truth or JHora concurrence. Provenance = DERIVED. Do not treat as oracle.

Byproduct (cross-check): Muntha triangulation ⇒ natal Lagna = Sagittarius ~22°40'59" (lord Jupiter). CONFIRMED against JHora natal chart 2026-10-24 (natal Lagna 22 Sg 40'59.06", PSha p3; natal Sun 22 Pi 30'56.53" AK = return anchor). Candidate derivation validated.

RULE (sourced, B.V. Raman *Varshaphal* / Tajika Neelakanthi; corrected S156 2026-10-24):
Five office-bearers = lords of:
1. Janma Lagna (natal asc) = Jupiter (Sag) [fixed]
2. Varsha Lagna (annual asc sign lord)
3. Muntha sign lord
4. Dinaratri-pati: DAY → lord of the SUN's sign · NIGHT → lord of the MOON's sign (dispositor, NOT Sun/Moon itself — earlier draft was wrong)
5. Trirasi-pati: triplicity lord of the Varsha Lagna sign, by day/night (Fire d=Sun/n=Jup · Earth d=Ven/n=Moon · Air d=Sat/n=Merc · Water d=Ven/n=Mars)
Day/night by pravesh vs sunrise/sunset: 2025 day · 2026 night · 2027 night.
SELECTION (CONSENSUS, research-ratified S156 — Raman + shankerstudy + vedastro + cosmicinsights):
1. BENEFIC Tajika aspect on Varsha Lagna = office-bearer in house **3/5/9/11** from Lagna (trine 5/9 + sextile 3/11). Malefic = 4/10 (square) + 7 (opposition); conjunction (1st) = inimical per Raman.
2. Among candidates with a BENEFIC aspect on the Lagna → **strongest by PV bala** wins.
3. If none benefic-aspects → among malefic/any-aspecting, strongest; then **Munthesh (Muntha lord) default** (also if the strongest aspecting <5 VB, or all equal).
Whole-sign, no orb-based Ithasala (D) needed. REJECTED: PyJHora's `_get_the_lord_of_tajaka_chart` takes max PV over ALL candidates when >1 benefic-aspect — a code shortcut that ignores the filter (gives Moon'25/Mars'26); handover warns PyJHora diverges. Design per S155: SURFACE all five candidates + PV + aspect-status + winner, interpreter-weighted, NOT a hard gate.

| Year | Varshesvara | Basis (consensus rule) | Confidence |
|------|-------------|------------------------|------------|
| 2025 | **Venus** | Benefic-aspecting set = Venus(Pi, 9th, PV 10.85), Jupiter(Ta, 11th, 7.89), Saturn(Pi, 9th, 6.05). Moon strongest overall (15.41) but CONJUNCT Lagna (1st=inimical) → excluded. Strongest benefic = **Venus**. | Likely |
| 2026 | **Jupiter** | Benefic set = Jupiter(Ge, 9th, 9.64), Mercury(Aq, 5th, 7.12). Mars strongest (10.58) but 6th = no benefic aspect → excluded. Strongest benefic = **Jupiter**. | Likely |
| 2027 | **Jupiter** | All five offices = Jupiter; Jupiter in Cancer = 8th (inimical) so no benefic-aspecter → Munthesh default = Jupiter (Muntha-lord) anyway. | Likely (strong) |

HISTORY: this value oscillated Venus→Moon→Venus across S156 as (a) corrected PV data arrived and (b) the benefic-aspect-filter rule was researched. Final = **Venus/Jupiter/Jupiter** under the sourced consensus. PyJHora code would give Moon/Mars/Jupiter — documented deviation, not adopted.

LOCKED DECISIONS (S156): cast=birthplace default + residence config (Raman); year-lord as above (surface-not-gate, Tajika sign-aspect eligibility, no D dependency); boundary ε=2° Lagna from ±8min birth-time band (tuning note: widen for larger rectification uncertainty).

## Sub-engine A/B — VALIDATED CONVENTIONS + REFERENCE (S156, in-container Moshier proof)

LOCKED CONVENTIONS (empirically proven vs JHora, not assumed):
- Ayanamsa model = swe.SIDM_LAHIRI (matches JHora "Traditional Lahiri" to 0.14").
- Positions = FLG_TRUEPOS (true/geometric; JHora reports true, NOT apparent — apparent was 19" low on Sun).
- Ayanamsa value = TRUE ayanamsa WITH nutation = get_ayanamsa_ex_ut(jd, FLG_SWIEPH)[1]. NOT get_ayanamsa_ut() (returns MEAN/no-nut → drifts up to -209s by 2027).
- Return = Newton root-find on sidereal Sun = natal sidereal Sun; cast at BIRTHPLACE.
- Muntha = (natal_sidereal_Lagna + completed_years*30) % 360; degree preserved.

VALIDATION (Moshier in-container; repo Swiss .se1 files close the residual):
- Annual planets (Moon/Jup) 0.1-1.2" all 3 yrs; pravesh +9/+12/+14s flat (=Moshier, →~1-2s on Swiss files); annual Lagna +2'-3' (= the pravesh-time residual × 15"/s, →sub-arcmin on Swiss files); Muntha EXACT; natal Lagna 0.13", natal Sun +1.3".

REFERENCE CORE (validated — adapt into repo, do not re-derive):
```python
swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
FL = swe.FLG_SWIEPH | swe.FLG_TRUEPOS
def aya(jd):            return swe.get_ayanamsa_ex_ut(jd, swe.FLG_SWIEPH)[1]   # nutation ON
def sid(body, jd):      return (swe.calc_ut(jd, body, FL)[0][0] - aya(jd)) % 360
def sid_asc(jd,lat,lon):return (swe.houses_ex(jd, lat, lon, b'P')[1][0] - aya(jd)) % 360
lam0 = sid(swe.SUN, natal_jd_ut)                 # natal sidereal Sun
# pravesh: anchor at (Y,4,6,0h UT), Newton on wrap(sid(SUN,jd)-lam0), step f/0.9856091
# cast at (pravesh_jd, birth_lat, birth_lon); muntha = (sid_asc(natal)+completed_yrs*30)%360
```

### ΔT DIVERGENCE vs JHora (DIAGNOSED + CLOSED S156) — engine is CORRECT

Repo Swiss-file run showed pravesh +10-14s vs JHora (drift +2.3s/yr), Lagna +2'-3'. ROOT CAUSE (isolated, not theorised):
- Planets match JHora to <0.2" at OUR instant → same physical (TT) moment.
- JHora's printed ST is self-consistent with its own printed UT (<1s) → JHora is internally fine.
- Our ΔT = 68.8-69.0s (flat, CORRECT — actual ΔT ~69s since ~2020). JHora's IMPLIED ΔT = 78→81→83s, RISING ~2s/yr = an OLD build's upward ΔT extrapolation (pre-2020 model).
- Same physical instant, ΔT labels ~10-14s apart → only UT-dependent quantities shift: Lagna + special lagnas + Gulika/Maandi by 2'-3'. Planets unaffected.

RULING: OUR Lagna is MORE accurate. DO NOT match JHora's ΔT (would degrade accuracy + replicate stale data + violate no-curation). Document as KNOWN DIVERGENCE (docs/KNOWN_DIVERGENCES.md), bounded 2'-3', NEVER flips a sign (≪ 2° boundary band), negligible for dasha dates. boundary_flag computed on OUR Lagna.

CORRECTED VALIDATION GATE (supersedes Lagna<1' vs JHora): planets (Sun/Moon/Jup...) <5" vs JHora [strict]; pravesh physical instant via planet match [strict]; Lagna/time accepted within the ΔT-explained band (pravesh ΔT-offset × 15"/s, ~2'-3') and cross-checked that |our_ΔT - actual| is small, NOT against JHora's ΔT. Sub-engine A = VALIDATED.

## STATUS

PINNED (oracle): A (pravesh instant + D1 cast) — VALIDATED on repo Swiss files: planets <0.2", pravesh physical instant correct; 2'-3' Lagna gap = JHora stale-ΔT (KNOWN DIVERGENCE, ours more accurate, closed S156). B (Muntha) — EXACT. C1 (Pancha-vargeeya Bala). E (Mudda + Patyayini sequences; seed to reverse-engineer in build).
SOLVED: C1 (Pancha-vargeeya Bala) — Model A (Raman §32-37), avg 0.358, 17/21 exact, correct year-lords. Known bounded Moon/Merc-neutral residual (non-impactful on YL).
C2 (year-lord: 2025 Moon, 2026 Jupiter, 2027 Jupiter) — now backed by solved C1; full selection rules captured from Raman/shankerstudy Upload 38 (Munthesh default, Moon/Rahu-Ketu edge cases, isthala tie-break). Still SURFACE-not-gate.

## INTEGRATION LANDED (S156, 2026-10-25) — spine wired, full suite green

Varshaphal spine wired into the fact-block pipeline. Verified on-device: full suite **5366 passed / 0 failed**, 9 skipped, 2 xfailed.
- `agent/astro/varshaphal_facts.build_varshaphal_facts` — fail-soft composer over A→B→C1→C2→E; cast at birthplace; YEAR-FIXED (defaults to the solar year containing `as_of`); dashas as dated ISO intervals. Returns {} on any missing input/engine failure, never raises.
- Hooked in `static_facts` (after ashtottari); `"varshaphal"` pinned in `capability_gate.FACT_BLOCK_PROVIDES`; render block in `pipeline._fact_block` (annual Lagna, Muntha, year-lord+rule, annual positions, PV-bala, the 3 dashas with phase resolved at answer time).
- Tests: `tests/astro/test_varshaphal_facts.py` (monkeypatched composer — year-lord Venus, Muntha Capricorn, dasha seeds Sat/Merc/Sat, fail-soft, target-year default) + `test_varshaphal_capability_is_rendered_with_phase` in `test_capability_gate.py` (frozenset pin updated).

### EPHEMERIS-PATH LEAK FIX (S156, 2026-10-25) — A, code change, NOT curve-fitting
`varsha_pravesh.compute_varsha_pravesh` called `swe.set_ephe_path(EPHE_PATH)` (bundled Swiss `.se1`, needed to match the JHora oracle) and never restored it. `set_ephe_path` is PROCESS-GLOBAL; the rest of the engine (`chart_calculator`, `helpers/ephemeris`) never sets a path → runs on the **Moshier** fallback. The leak shifted every later `FLG_SWIEPH` call by ~7e-6° → 6 David longitude characterization tests failed, but ONLY when run after `test_varsha_pravesh` (test-order leak, not a calc error). FIX: compute body wrapped in `try/finally`; `finally` calls `swe.set_ephe_path(None)` to restore the Moshier baseline. Returned pravesh instant + longitudes unchanged (restore runs after the result is built). A's oracle match intact; +6 tests recovered (5360→5366).

### OPEN (deferred — NOT small, start fresh)
- [ ] **Staleness re-anchor** — `varshaphal` sits in the chart-fixed cached static block but defaults to the current solar year; a cached chart serves last year's Varsha after the next pravesh until invalidated. Real fix = dated layer (`timeline_store`, keyed on the pravesh span, decision #2). Interim contract: callers that cache MUST key/invalidate on the result's `"year"` stamp.
- [ ] **Ephemeris split decision** — A on Swiss `.se1`, the rest on Moshier (~0.025 arcsec). Coherence gap, not a bug. Option 1 = keep (A isolates `.se1` to its own cast). Option 2 = standardize engine on `.se1` at startup → re-baselines every Moshier-captured characterization test. Not adopted; Sulabh's call.

## PENDING — next JHora pull (second pass, non-blocking)

- [ ] **Sahams** — Punya, Vidya, Yasas (degrees), 2026. [separate view — NOT the upagraha table]
- [ ] **Tajika yogas/aspects** — Ithasala/Esahphala/Muthashila, 2026, if JHora exposes. (sub-engine D)
