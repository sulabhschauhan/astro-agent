# Drik Panchang Vimshottari Capture — Sulabh (S76)

## Source

- URL: drikpanchang.com Vimshottari Dasha calculator
- Capture method: Sulabh manual capture, pasted verbatim into
  `diagnostics/latest_run.md` (S76), lines 314-394
- Ayanamsa setting: Lahiri (Traditional / Chitrapaksha) — confirmed by
  capture site default
- Capture timestamp: 2026-07-26 (S76)

## Verbatim Drik table

```
Sulabh::

Ketu - Maha Dasha

August 4, 2025, Monday at 15:18

August 4, 2032, Wednesday at 10:22

Total - 6y 11m

Left - 6y

Guru - Maha Dasha - 16y

August 4, 1973, Saturday at 07:21

August 4, 1989, Friday at 09:48

❯

Shani - Maha Dasha - 18y 11m

August 4, 1989, Friday at 09:48

August 4, 2008, Monday at 06:42

❯

Budha - Maha Dasha - 17y

August 4, 2008, Monday at 06:42

August 4, 2025, Monday at 15:18

❯

Ketu - Maha Dasha - 6y 11m

August 4, 2025, Monday at 15:18

August 4, 2032, Wednesday at 10:22

❯

Shukra - Maha Dasha - 20y

August 4, 2032, Wednesday at 10:22

August 4, 2052, Sunday at 13:25

❯

Surya - Maha Dasha - 6y

August 4, 2052, Sunday at 13:25

August 5, 2058, Monday at 02:20

❯

Chandra - Maha Dasha - 9y 11m

August 5, 2058, Monday at 02:20

August 4, 2068, Saturday at 15:51

❯

Mangal - Maha Dasha - 7y

August 4, 2068, Saturday at 15:51

August 5, 2075, Monday at 10:55

❯

Rahu - Maha Dasha - 17y 11m

August 5, 2075, Monday at 10:55

August 5, 2093, Wednesday at 01:40
```

Birth: 1988-04-06 00:30 IST, Calcutta, India (`docs/PROJECT_FACTS.md` §1).
Row-0 lord = Guru (Jupiter), 16y period — matches this codebase's own
starting-lord computation for Sulabh
(`diagnostics/vimshottari_year_length_S74.md`). Row-0 = the Guru MD
block, end date **August 4, 1989, Friday at 09:48**.

## Row-0 MD end conversion

- Local timestamp: 1989-08-04 09:48:00 IST (UTC+5:30, fixed, per
  `docs/PROJECT_FACTS.md` §1)
- UT conversion: `9 + 48/60 - 5.5 = 4.300000` → **1989-08-04 04:18:00 UT**
  (no day rollover — offset subtraction keeps the same calendar day)
- Julian Day: `swe.julday(1989, 8, 4, 4.300000)` = **2447742.679167**
  (verified directly via `python -c "import swisseph as swe;
  print(swe.julday(1989,8,4,4.3))"` → `2447742.6791666667`)

## Residual vs production row-0

- Production row-0 (days from birth, Traditional Lahiri): **482.7232**
  (`docs/PROJECT_FACTS.md` §4 / `diagnostics/ayanamsa_mode_investigation_
  S75.md` lines 119-124)
- `birth_jd_ut = 2447257.291667` (`diagnostics/vimshottari_year_length_
  S74.md`)
- Drik row-0 (days from birth): `2447742.679167 - 2447257.291667 =
  485.387500`
- Residual (prod − drik): `482.7232 - 485.387500 = -2.6643`

**Residual: -2.6643 days** (production's Vimshottari MD1 boundary lands
~2.66 days earlier than Drik Panchang's). Within the ≤5-day flag
threshold — no STOP condition triggered.
