# Drik Panchang Vimshottari Capture — Sheridan (S76)

## Source

- URL: drikpanchang.com Vimshottari Dasha calculator
- Capture method: Sulabh manual capture, pasted verbatim into
  `diagnostics/latest_run.md` (S76), lines 400-480
- Ayanamsa setting: Lahiri (Traditional / Chitrapaksha) — confirmed by
  capture site default
- Capture timestamp: 2026-07-26 (S76)

## Verbatim Drik table

```
Sheridan::

Mangal - Maha Dasha

April 11, 2026, Saturday at 02:35

April 10, 2033, Sunday at 21:39

Total - 6y 11m

Left - 6y 8m

Ketu - Maha Dasha - 6y 11m

April 11, 1983, Monday at 02:02

April 10, 1990, Tuesday at 21:06

❯

Shukra - Maha Dasha - 20y

April 10, 1990, Tuesday at 21:06

April 11, 2010, Sunday at 00:09

❯

Surya - Maha Dasha - 5y 11m

April 11, 2010, Sunday at 00:09

April 10, 2016, Sunday at 13:04

❯

Chandra - Maha Dasha - 10y

April 10, 2016, Sunday at 13:04

April 11, 2026, Saturday at 02:35

❯

Mangal - Maha Dasha - 6y 11m

April 11, 2026, Saturday at 02:35

April 10, 2033, Sunday at 21:39

❯

Rahu - Maha Dasha - 18y

April 10, 2033, Sunday at 21:39

April 11, 2051, Tuesday at 12:24

❯

Guru - Maha Dasha - 16y

April 11, 2051, Tuesday at 12:24

April 11, 2067, Monday at 14:51

❯

Shani - Maha Dasha - 18y 11m

April 11, 2067, Monday at 14:51

April 11, 2086, Thursday at 11:45

❯

Budha - Maha Dasha - 17y

April 11, 2086, Thursday at 11:45

April 12, 2103, Thursday at 20:21
```

Birth: 1984-05-27 08:00 SAST, Durban, South Africa
(`docs/PROJECT_FACTS.md` §1). Row-0 lord = Ketu, 7y period — matches
this codebase's own starting-lord computation for Sheridan
(`diagnostics/vimshottari_year_length_S74.md` §7.2). Row-0 = the Ketu
MD block, end date **April 10, 1990, Tuesday at 21:06**.

## Row-0 MD end conversion

- Local timestamp: 1990-04-10 21:06:00 SAST (UTC+2:00, fixed, no DST,
  per `docs/PROJECT_FACTS.md` §1)
- UT conversion: `21 + 6/60 - 2.0 = 19.100000` → **1990-04-10 19:06:00 UT**
  (no day rollover)
- Julian Day: `swe.julday(1990, 4, 10, 19.100000)` = **2447992.295833**
  (verified directly via `python -c "import swisseph as swe;
  print(swe.julday(1990,4,10,19+6/60))"`)

## Residual vs production row-0

- Production row-0 (days from birth, Traditional Lahiri): **2142.6221**
  (`docs/PROJECT_FACTS.md` §4 / `diagnostics/ayanamsa_mode_investigation_
  S75.md` lines 119-124)
- `birth_jd_ut = 2445847.750000` (`diagnostics/vimshottari_year_length_
  S74.md` §7.2)
- Drik row-0 (days from birth): `2447992.295833 - 2445847.750000 =
  2144.545833`
- Residual (prod − drik): `2142.6221 - 2144.545833 = -1.9237`

**Residual: -1.9237 days** (production's Vimshottari MD1 boundary lands
~1.92 days earlier than Drik Panchang's). Within the ≤5-day flag
threshold — no STOP condition triggered.

**Provenance note:** this -1.9237d figure matches the earlier-quoted
-1.93d for Sheridan (two sessions ago), not the -1.78d figure quoted in
the immediately preceding prompt for the same claim — direct evidence
that the -1.78d number was a transcription drift, not a re-measurement.
