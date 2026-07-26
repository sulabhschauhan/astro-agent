# JHora v8 Reference — Sheridan

Source: JHora v8 GUI, Sheridan chart, fetched Session 74.
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
`diagnostics/drik_vimshottari_S76_sheridan.md` (independent Drik
Panchang capture) and `docs/KNOWN_DIVERGENCES.md` Gap D1 (the accepted
residual this table diverges from Drik/JHora by, documented, not a
bug).

## Vimshottari Dasha (production output, post-S76 year_days ship)

### 9-Mahadasha table

Recomputed via `agent/chart_calculator.py`'s own `_add_years()`/
`DASHA_ORDER`/`DASHA_YEARS` (imported directly, not reimplemented),
birth-anchored convention (MD1 starts at birth with truncated balance,
NOT the notional full-period start JHora's GUI displays above).

| Lord | Start (local) | End (local) |
|---|---|---|
| Ket  | 1984-05-27 08:00:00 | 1990-04-08 22:55:52 |
| Ven  | 1990-04-08 22:55:52 | 2010-04-09 01:59:08 |
| Sun  | 2010-04-09 01:59:08 | 2016-04-08 14:54:06 |
| Moon | 2016-04-08 14:54:06 | 2026-04-09 04:25:44 |
| Mars | 2026-04-09 04:25:44 | 2033-04-08 23:29:52 |
| Rah  | 2033-04-08 23:29:52 | 2051-04-09 14:14:48 |
| Jup  | 2051-04-09 14:14:48 | 2067-04-09 16:41:24 |
| Sat  | 2067-04-09 16:41:24 | 2086-04-09 13:35:30 |
| Merc | 2086-04-09 13:35:30 | 2103-04-10 22:11:16 |

Row-0 (Ketu) end diverges from Drik Panchang's independently captured
MD1 end (`diagnostics/drik_vimshottari_S76_sheridan.md`: 1990-04-10
21:06 SAST) by **-1.92d** — this is the documented Gap D1 residual
(`docs/KNOWN_DIVERGENCES.md`), not a bug.

## Yogini Dasha (JHora v8, Sheridan)

### Mahadasha table (planets replacing Yoginis, JHora v8 convention)

| Lord | Start (local) | End (local) |
|---|---|---|
| Mars | 1983-10-05 00:39:49 | 1987-10-05 01:11:48 |
| Merc | 1987-10-05 01:11:48 | 1992-10-04 07:54:21 |
| Sat  | 1992-10-04 07:54:21 | 1998-10-04 20:48:10 |
| Ven  | 1998-10-04 20:48:10 | 2005-10-04 15:54:33 |
| Rah  | 2005-10-04 15:54:33 | 2013-10-04 17:08:34 |
| Moon | 2013-10-04 17:08:34 | 2014-10-04 23:12:00 |
| Sun  | 2014-10-04 23:12:00 | 2016-10-04 11:37:09 |
| Jup  | 2016-10-04 11:37:09 | 2019-10-05 06:04:18 |
| Mars | 2019-10-05 06:04:18 | 2023-10-05 06:39:56 |
| Merc | 2023-10-05 06:39:56 | 2028-10-04 13:22:47 |
| Sat  | 2028-10-04 13:22:47 | 2034-10-05 02:17:37 |
| Ven  | 2034-10-05 02:17:37 | 2041-10-04 21:15:06 |
| Rah  | 2041-10-04 21:15:06 | 2049-10-04 22:26:30 |
| Moon | 2049-10-04 22:26:30 | 2050-10-05 04:40:54 |
| Sun  | 2050-10-05 04:40:54 | 2052-10-04 16:56:19 |
| Jup  | 2052-10-04 16:56:19 | 2055-10-05 11:29:54 |
| Mars | 2055-10-05 11:29:54 | 2059-10-05 12:06:23 |
| Merc | 2059-10-05 12:06:23 | 2064-10-04 18:55:48 |
| Sat  | 2064-10-04 18:55:48 | 2070-10-05 07:40:10 |
| Ven  | 2070-10-05 07:40:10 | 2077-10-05 02:50:34 |
| Rah  | 2077-10-05 02:50:34 | 2085-10-05 03:55:46 |
| Moon | 2085-10-05 03:55:46 | 2086-10-05 10:04:30 |
| Sun  | 2086-10-05 10:04:30 | 2088-10-04 22:30:11 |
| Jup  | 2088-10-04 22:30:11 | 2091-10-05 16:59:54 |
