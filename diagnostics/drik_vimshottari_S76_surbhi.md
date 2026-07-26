# Drik Panchang Vimshottari Capture — Surbhi (S76)

## Source

- URL: drikpanchang.com Vimshottari Dasha calculator
- Capture method: Sulabh manual capture, pasted verbatim into
  `diagnostics/latest_run.md` (S76), lines 486-566
- Ayanamsa setting: Lahiri (Traditional / Chitrapaksha) — confirmed by
  capture site default
- Capture timestamp: 2026-07-26 (S76)

## Verbatim Drik table

```
Surbhi::

Shani - Maha Dasha

March 6, 2015, Friday at 00:31

March 5, 2034, Sunday at 21:25

Total - 18y 11m

Left - 7y 7m

Rahu - Maha Dasha - 18y

March 5, 1981, Thursday at 07:19

March 5, 1999, Friday at 22:04

❯

Guru - Maha Dasha - 16y

March 5, 1999, Friday at 22:04

March 6, 2015, Friday at 00:31

❯

Shani - Maha Dasha - 18y 11m

March 6, 2015, Friday at 00:31

March 5, 2034, Sunday at 21:25

❯

Budha - Maha Dasha - 17y

March 5, 2034, Sunday at 21:25

March 6, 2051, Monday at 06:00

❯

Ketu - Maha Dasha - 6y 11m

March 6, 2051, Monday at 06:00

March 6, 2058, Wednesday at 01:05

❯

Shukra - Maha Dasha - 20y

March 6, 2058, Wednesday at 01:05

March 6, 2078, Sunday at 04:08

❯

Surya - Maha Dasha - 5y 11m

March 6, 2078, Sunday at 04:08

March 5, 2084, Sunday at 17:03

❯

Chandra - Maha Dasha - 10y

March 5, 2084, Sunday at 17:03

March 6, 2094, Saturday at 06:34

❯

Mangal - Maha Dasha - 7y

March 6, 2094, Saturday at 06:34

March 7, 2101, Monday at 01:38
```

Birth: 1992-09-11 10:30 IST, Patna, India (`docs/PROJECT_FACTS.md` §1).
Row-0 lord = Rahu, 18y period — matches this codebase's own
starting-lord computation for Surbhi
(`diagnostics/vimshottari_year_length_S74.md` §7.1). Row-0 = the Rahu
MD block, end date **March 5, 1999, Friday at 22:04**.

## Row-0 MD end conversion

- Local timestamp: 1999-03-05 22:04:00 IST (UTC+5:30, fixed, per
  `docs/PROJECT_FACTS.md` §1)
- UT conversion: `22 + 4/60 - 5.5 = 16.566667` → **1999-03-05 16:34:00 UT**
  (no day rollover)
- Julian Day: `swe.julday(1999, 3, 5, 16.566667)` = **2451243.190278**
  (verified directly via `python -c "import swisseph as swe;
  print(swe.julday(1999,3,5,16+34/60))"`)

## Residual vs production row-0

- Production row-0 (days from birth, Traditional Lahiri): **2366.1560**
  (`docs/PROJECT_FACTS.md` §4 / `diagnostics/ayanamsa_mode_investigation_
  S75.md` lines 119-124)
- `birth_jd_ut = 2448876.708333` (`diagnostics/vimshottari_year_length_
  S74.md` §7.1)
- Drik row-0 (days from birth): `2451243.190278 - 2448876.708333 =
  2366.481945`
- Residual (prod − drik): `2366.1560 - 2366.481945 = -0.3259`

**Residual: -0.3259 days** (production's Vimshottari MD1 boundary lands
~0.33 days earlier than Drik Panchang's). Within the ≤5-day flag
threshold — no STOP condition triggered.
