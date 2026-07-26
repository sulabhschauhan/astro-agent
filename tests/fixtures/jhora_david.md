# JHora v8 Reference — David

Source: JHora v8 GUI, David chart, fetched Session 74.
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
`diagnostics/drik_vimshottari_S76_david.md` (independent Drik Panchang
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
| Ket  | 1976-01-19 22:00:00 | 1976-12-06 04:43:30 |
| Ven  | 1976-12-06 04:43:30 | 1996-12-06 07:46:45 |
| Sun  | 1996-12-06 07:46:45 | 2002-12-06 20:41:43 |
| Moon | 2002-12-06 20:41:43 | 2012-12-06 10:13:21 |
| Mars | 2012-12-06 10:13:21 | 2019-12-07 05:17:29 |
| Rah  | 2019-12-07 05:17:29 | 2037-12-06 20:02:25 |
| Jup  | 2037-12-06 20:02:25 | 2053-12-06 22:29:01 |
| Sat  | 2053-12-06 22:29:01 | 2072-12-06 19:23:07 |
| Merc | 2072-12-06 19:23:07 | 2089-12-07 03:58:53 |

Row-0 (Ketu) end diverges from Drik Panchang's independently captured
MD1 end (`diagnostics/drik_vimshottari_S76_david.md`: 1976-12-06 17:47
GMT) by **-0.54d** — this is the documented Gap D1 residual
(`docs/KNOWN_DIVERGENCES.md`), not a bug.

## Yogini Dasha (JHora v8, David)

### Mahadasha table (planets replacing Yoginis, JHora v8 convention)

| Lord | Start (local) | End (local) |
|---|---|---|
| Merc | 1971-09-06 05:53:21 | 1976-09-05 12:34:21 |
| Sat  | 1976-09-05 12:34:21 | 1982-09-06 01:30:53 |
| Ven  | 1982-09-06 01:30:53 | 1989-09-05 20:30:06 |
| Rah  | 1989-09-05 20:30:06 | 1997-09-05 21:45:34 |
| Moon | 1997-09-05 21:45:34 | 1998-09-06 03:49:33 |
| Sun  | 1998-09-06 03:49:33 | 2000-09-05 16:12:01 |
| Jup  | 2000-09-05 16:12:01 | 2003-09-06 10:35:50 |
| Mars | 2003-09-06 10:35:50 | 2007-09-06 11:17:23 |
| Merc | 2007-09-06 11:17:23 | 2012-09-05 18:02:59 |
| Sat  | 2012-09-05 18:02:59 | 2018-09-06 06:56:51 |
| Ven  | 2018-09-06 06:56:51 | 2025-09-06 01:49:52 |
| Rah  | 2025-09-06 01:49:52 | 2033-09-06 03:04:10 |
| Moon | 2033-09-06 03:04:10 | 2034-09-06 09:16:49 |
| Sun  | 2034-09-06 09:16:49 | 2036-09-05 21:34:01 |
| Jup  | 2036-09-05 21:34:01 | 2039-09-06 16:03:31 |
| Mars | 2039-09-06 16:03:31 | 2043-09-06 16:39:58 |
| Merc | 2043-09-06 16:39:58 | 2048-09-05 23:28:44 |
| Sat  | 2048-09-05 23:28:44 | 2054-09-06 12:13:08 |
| Ven  | 2054-09-06 12:13:08 | 2061-09-06 07:23:29 |
| Rah  | 2061-09-06 07:23:29 | 2069-09-06 08:33:01 |
| Moon | 2069-09-06 08:33:01 | 2070-09-06 14:35:11 |
| Sun  | 2070-09-06 14:35:11 | 2072-09-06 03:02:57 |
| Jup  | 2072-09-06 03:02:57 | 2075-09-06 21:29:49 |
| Mars | 2075-09-06 21:29:49 | 2079-09-06 22:02:46 |
