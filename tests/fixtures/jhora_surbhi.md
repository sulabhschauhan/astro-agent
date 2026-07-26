# JHora v8 Reference — Surbhi

Source: JHora v8 GUI, Surbhi chart, fetched Session 74.
Ayanamsa: Lahiri (23-40-39.08). All timestamps in local birth-zone
time (JHora convention), NOT UT. Balance-at-birth: JHora displays
MD 1 from notional full-period start (birth-straddling); effective
MD 1 for our calculator starts at birth with truncated balance.

**NOTE (S76):** the Vimshottari 9-Mahadasha table below was recaptured
to production's own `_calc_dasha()` output after the `year_days =
365.256363` ship (was the JHora GUI capture above, pre-S76 — see git
history for the prior values). The Yogini Dasha section further below
is UNCHANGED (already used `year_days = 365.256363` since Session 72,
unaffected by this ship). Cross-reference:
`diagnostics/drik_vimshottari_S76_surbhi.md` (independent Drik Panchang
capture) and `docs/KNOWN_DIVERGENCES.md` Gap D1 (the accepted residual
this table diverges from Drik/JHora by, documented, not a bug).

## Vimshottari Dasha (production output, post-S76 year_days ship)

### 9-Mahadasha table

Recomputed via `agent/chart_calculator.py`'s own `_add_years()`/
`DASHA_ORDER`/`DASHA_YEARS` (imported directly, not reimplemented),
birth-anchored convention (MD1 starts at birth with truncated balance,
NOT the notional full-period start JHora's GUI displays above).

| Lord | Start (local) | End (local) |
|---|---|---|
| Rah  | 1992-09-11 10:30:00 | 1999-03-05 14:11:50 |
| Jup  | 1999-03-05 14:11:50 | 2015-03-05 16:38:26 |
| Sat  | 2015-03-05 16:38:26 | 2034-03-05 13:32:32 |
| Merc | 2034-03-05 13:32:32 | 2051-03-05 22:08:18 |
| Ket  | 2051-03-05 22:08:18 | 2058-03-05 17:12:26 |
| Ven  | 2058-03-05 17:12:26 | 2078-03-05 20:15:41 |
| Sun  | 2078-03-05 20:15:41 | 2084-03-05 09:10:40 |
| Moon | 2084-03-05 09:10:40 | 2094-03-05 22:42:17 |
| Mars | 2094-03-05 22:42:17 | 2101-03-06 17:46:26 |

Row-0 (Rahu) end diverges from Drik Panchang's independently captured
MD1 end (`diagnostics/drik_vimshottari_S76_surbhi.md`: 1999-03-05
22:04 IST) by **-0.33d** — this is the documented Gap D1 residual
(`docs/KNOWN_DIVERGENCES.md`), not a bug.

## Yogini Dasha (JHora v8, Surbhi)

### Mahadasha table (planets replacing Yoginis, JHora v8 convention)

| Lord | Start (local) | End (local) |
|---|---|---|
| Jup  | 1990-10-09 20:35:40 | 1993-10-09 15:03:11 |
| Mars | 1993-10-09 15:03:11 | 1997-10-09 15:41:55 |
| Merc | 1997-10-09 15:41:55 | 2002-10-09 22:22:13 |
| Sat  | 2002-10-09 22:22:13 | 2008-10-09 11:24:00 |
| Ven  | 2008-10-09 11:24:00 | 2015-10-10 06:27:10 |
| Rah  | 2015-10-10 06:27:10 | 2023-10-10 07:40:06 |
| Moon | 2023-10-10 07:40:06 | 2024-10-09 13:46:52 |
| Sun  | 2024-10-09 13:46:52 | 2026-10-10 02:00:59 |
| Jup  | 2026-10-10 02:00:59 | 2029-10-09 20:33:36 |
| Mars | 2029-10-09 20:33:36 | 2033-10-09 21:07:35 |
| Merc | 2033-10-09 21:07:35 | 2038-10-10 03:48:21 |
| Sat  | 2038-10-10 03:48:21 | 2044-10-09 16:51:33 |
| Ven  | 2044-10-09 16:51:33 | 2051-10-10 11:50:10 |
| Rah  | 2051-10-10 11:50:10 | 2059-10-10 13:05:05 |
| Moon | 2059-10-10 13:05:05 | 2060-10-09 19:12:17 |
| Sun  | 2060-10-09 19:12:17 | 2062-10-10 07:27:07 |
| Jup  | 2062-10-10 07:27:07 | 2065-10-10 01:55:41 |
| Mars | 2065-10-10 01:55:41 | 2069-10-10 02:35:23 |
| Merc | 2069-10-10 02:35:23 | 2074-10-10 09:18:16 |
| Sat  | 2074-10-10 09:18:16 | 2080-10-09 22:22:15 |
| Ven  | 2080-10-09 22:22:15 | 2087-10-10 17:15:20 |
| Rah  | 2087-10-10 17:15:20 | 2095-10-10 18:31:33 |
| Moon | 2095-10-10 18:31:33 | 2096-10-10 00:45:05 |
| Sun  | 2096-10-10 00:45:05 | 2098-10-10 12:53:33 |
