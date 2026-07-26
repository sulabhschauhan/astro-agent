# Drik Panchang Vimshottari Capture — David (S76)

## Source

- URL: drikpanchang.com Vimshottari Dasha calculator
- Capture method: Sulabh manual capture, pasted verbatim into
  `diagnostics/latest_run.md` (S76), lines 570-650
- Ayanamsa setting: Lahiri (Traditional / Chitrapaksha) — confirmed by
  capture site default
- Capture timestamp: 2026-07-26 (S76)

## Verbatim Drik table

```
David::

Rahu - Maha Dasha

December 7, 2019, Saturday at 18:21

December 7, 2037, Monday at 09:06

Total - 17y 11m

Left - 11y 4m

Ketu - Maha Dasha - 6y 11m

December 6, 1969, Saturday at 23:43

December 6, 1976, Monday at 17:47

❯

Shukra - Maha Dasha - 20y

December 6, 1976, Monday at 17:47

December 6, 1996, Friday at 20:50

❯

Surya - Maha Dasha - 6y

December 6, 1996, Friday at 20:50

December 7, 2002, Saturday at 09:45

❯

Chandra - Maha Dasha - 9y 11m

December 7, 2002, Saturday at 09:45

December 6, 2012, Thursday at 23:17

❯

Mangal - Maha Dasha - 7y

December 6, 2012, Thursday at 23:17

December 7, 2019, Saturday at 18:21

❯

Rahu - Maha Dasha - 17y 11m

December 7, 2019, Saturday at 18:21

December 7, 2037, Monday at 09:06

❯

Guru - Maha Dasha - 16y

December 7, 2037, Monday at 09:06

December 7, 2053, Sunday at 11:32

❯

Shani - Maha Dasha - 18y 11m

December 7, 2053, Sunday at 11:32

December 7, 2072, Wednesday at 08:26

❯

Budha - Maha Dasha - 17y

December 7, 2072, Wednesday at 08:26

December 7, 2089, Wednesday at 17:02
```

Birth: 1976-01-19 22:00 GMT, London, UK (`docs/PROJECT_FACTS.md` §1).
Row-0 lord = Ketu, 7y period — matches this codebase's own
starting-lord computation for David
(`diagnostics/vimshottari_year_length_S74.md` §7.3). Row-0 = the Ketu
MD block, end date **December 6, 1976, Monday at 17:47**.

## Row-0 MD end conversion

- Local timestamp: 1976-12-06 17:47:00. TZ confirmed GMT (UTC+0): UK
  British Summer Time (BST, UTC+1) only applies March-October; December
  6 falls in standard time, so **no DST correction applies** (per this
  task's own instruction to confirm before applying — confirmed here).
- UT conversion: `17 + 47/60 - 0.0 = 17.783333` → **1976-12-06 17:47:00 UT**
  (identical to local, since offset is zero; no day rollover)
- Julian Day: `swe.julday(1976, 12, 6, 17.783333)` = **2443119.240972**
  (verified directly via `python -c "import swisseph as swe;
  print(swe.julday(1976,12,6,17+47/60))"`)

## Residual vs production row-0

- Production row-0 (days from birth, Traditional Lahiri): **321.2793**
  (`docs/PROJECT_FACTS.md` §4 / `diagnostics/ayanamsa_mode_investigation_
  S75.md` lines 119-124)
- `birth_jd_ut = 2442797.416667` (`diagnostics/vimshottari_year_length_
  S74.md` §7.3)
- Drik row-0 (days from birth): `2443119.240972 - 2442797.416667 =
  321.824305`
- Residual (prod − drik): `321.2793 - 321.824305 = -0.5450`

**Residual: -0.5450 days** (production's Vimshottari MD1 boundary lands
~0.55 days earlier than Drik Panchang's). Within the ≤5-day flag
threshold — no STOP condition triggered.
