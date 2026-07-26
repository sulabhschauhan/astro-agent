# S76 — year_days ship + fixture recapture (post-commit report)

**Commit:** `fd9c20b` ("docs: land Drik Panchang Vimshottari captures
S76, close D1 provenance gap"). This file holds only this run's
output, per convention — historical Code output lives in
commit-anchored diagnostic files (`diagnostics/drik_vimshottari_S76_
{sulabh,surbhi,sheridan,david}.md`), not in this rolling file. Prior
runs' content (PROJECT_FACTS.md creation trail, the raw verbatim Drik
Panchang paste, the interim "awaiting ratification" report) has been
truncated from here — all of it is durably preserved elsewhere: the 4
diagnostic files above (verbatim Drik captures), `docs/PROJECT_FACTS.md`
(§3), `docs/KNOWN_DIVERGENCES.md` (Gap D1), and `SESSION_LOG.md`'s S76
close block.

**Blocking check surfaced before any edit:** this task's premise
("fixtures reflect production output post-ship") assumed
`agent/chart_calculator.py`'s `_add_years()` already used
`365.256363` — verified via `Grep` that it still read `365.25`
(Julian). Asked via `AskUserQuestion` whether to ship the constant now
or leave it untouched (in which case the fixture request couldn't be
honored as literally stated). User chose to ship it now and supplied
"RATIFIED: commit authorized" plus a fully detailed 5-point scope.

## Blast-radius verification (before editing)

`git grep 365` across `agent/` found exactly 4 files with a hardcoded
`365.25`-family constant:

| File | Constant | Verdict |
|---|---|---|
| `agent/chart_calculator.py:166` | `365.25` (`_add_years`) | **Changed** to `365.256363` — this is the target |
| `agent/infra/chart_profile.py:348-349` | `365.25` (`_SADE_SATI_ADJACENT_CYCLE_SCAN_YEARS` scan window) | **Unrelated** — sade_sati's own independent Saturn-transit calc, confirmed no `_add_years`/dasha dependency (CLAUDE.md's own note: "sade_sati -- NO mahadasha/antardasha fields") |
| `agent/calculations/transits/sade_sati.py:62` | `_YEAR_DAYS = 365.25` | **Unrelated** — same independent Saturn-transit calc |
| `agent/calculations/transits/av_transit_scanner.py:96` | `_YEAR_DAYS = 365.25` | **Unrelated** — read the actual usage (line 225): `window_years = (end_jd - start_jd) / _YEAR_DAYS`, a scan-window SANITY-CHECK CAP divisor only; `start_jd`/`end_jd` themselves already come from `_add_years()`'s (now-updated) output, so this constant never re-derives a dasha period length |

`calc_router.py`, `result_formatter.py`, `answer_renderer.py`: zero
`365`-family hits — grep-confirmed, they only consume `_calc_dasha()`'s
output fields. **Conclusion: only `agent/chart_calculator.py:166`
needed to change**, exactly matching `vimshottari_year_length_S74.md`
§7's own blast-radius inventory (3 call sites, all inside
`_calc_dasha()`).

`golden_qa_sulabh.py`'s ±37-day Antardasha envelope: checked
analytically, not tightened (per instruction). The constant swap adds a
compounding drift of ≈0.006d per elapsed year; even at Sulabh's ~38
elapsed years that's ~0.23d — nowhere near stressing a 37-DAY envelope.
No fixture/assertion change needed there.

## Code change

```diff
diff --git a/agent/chart_calculator.py b/agent/chart_calculator.py
index 8b0577f..eb3293f 100644
--- a/agent/chart_calculator.py
+++ b/agent/chart_calculator.py
@@ -163,7 +163,9 @@ def _dignity(planet: str, sign: str) -> str:
 
 
 def _add_years(dt: datetime, years: float) -> datetime:
-    return dt + timedelta(days=years * 365.25)
+    # sidereal year. Ratified S74 (regression), S75 (JHora fixture-internal
+    # arithmetic, 9 rows x 4 charts). Was 365.25 Julian pre-S76. Kapoor Ch IX.
+    return dt + timedelta(days=years * 365.256363)
 
 
 def _fmt(dt: datetime) -> str:
```

## Test results

Targeted affected-module run (dasha/chart_profile/calc_router/
orchestrator/answer_renderer/av_transit/yogini, 13 files): **123 passed,
1 xpassed** — same known xpass as baseline, zero failures.

Full suite, run twice (once before any edit to confirm the stated
baseline, once after all edits including the fixture recapture):

| Run | Result |
|---|---|
| Before this task's edits | 3302 passed, 7 skipped, 1 xpassed, 0 failed |
| After `_add_years` change + fixture recapture | 3302 passed, 7 skipped, 1 xpassed, 0 failed |

**Byte-identical — zero regressions.**

## Fixture recapture — per-chart date-shift table

Recomputed via a temporary script (`scripts/_probe_fixture_recapture_
S76.py`, deleted after use, not tracked in git — same convention as
prior S72/S74 probes) that imports `agent/chart_calculator.py`'s own
`_add_years()`/`DASHA_ORDER`/`DASHA_YEARS`/`_nakshatra`/`geocode_place`/
`to_julian_day`/`_local_datetime`/`_calc_planets` directly — not
reimplemented — so the fixture now reflects the literal function that
ships, not a hand-derived approximation.

| Chart | Row-0 lord | Old fixture MD1 end (JHora GUI, pre-S76) | New fixture MD1 end (production, post-S76) | Residual vs. Drik (`diagnostics/drik_vimshottari_S76_<chart>.md`) |
|---|---|---|---|---|
| Sulabh | Jupiter | 1989-07-28 (11:39:57) | 1989-08-01 (17:54:13) | -2.66d |
| Surbhi | Rahu | 1999-02-22 09:33:52 | 1999-03-05 14:11:50 | -0.33d |
| Sheridan | Ketu | 1990-04-05 02:50:05 | 1990-04-08 22:55:52 | -1.92d |
| David | Ketu | 1976-12-04 17:21:56 | 1976-12-06 04:43:30 | -0.54d |

Note the large jump between "old fixture" and "new fixture" columns for
most charts (e.g. Surbhi: Feb 22 → Mar 5) — this is NOT the year_days
effect (which is sub-day at row-0); it's the pre-existing convention
mismatch between JHora's GUI (full notional period, birth-straddling)
and production's own birth-anchored MD1 (starts at actual birth with
truncated balance) — already documented in
`vimshottari_year_length_S74.md` §2 ("Row-0 `begin_jd` is skipped per
the fixture note"). The residual column (vs. Drik, matched convention)
is the actually-meaningful D1 comparison, and confirms pre-ship ≈
post-ship (sub-0.003d difference) — see the cross-check below.

**Pre-ship vs. post-ship residual cross-check** (confirms year_days
does NOT move Gap D1):

| Chart | Residual pre-ship (365.25) | Residual post-ship (365.256363) | Difference |
|---|---|---|---|
| Sulabh | -2.6643d | -2.6623d | 0.0020d |
| Surbhi | -0.3259d | -0.3279d | 0.0020d |
| Sheridan | -1.9237d | -1.9237d | 0.0000d |
| David | -0.5450d | -0.5441d | 0.0009d |

## Files changed, full diffstat (commit `fd9c20b`)

```
 SESSION_LOG.md                   | 137 ++++++++++++++++++++++++++++++++++++++-
 agent/chart_calculator.py        |   4 +-
 docs/KNOWN_DIVERGENCES.md        |  22 +++++--
 docs/PROJECT_FACTS.md            |  91 +++++++++++++++-----------
 tests/fixtures/jhora_david.md    |  40 +++++++++---
 tests/fixtures/jhora_sheridan.md |  41 +++++++++---
 tests/fixtures/jhora_sulabh.md   |  65 +++++++++++++------
 tests/fixtures/jhora_surbhi.md   |  40 +++++++++---
 8 files changed, 345 insertions(+), 95 deletions(-)
```

Plus 4 new files in the same commit:
`diagnostics/drik_vimshottari_S76_{sulabh,surbhi,sheridan,david}.md`
(the verbatim Drik Panchang captures — see those files directly for
content, not re-duplicated here).

## Known staleness flagged, not fixed (out of ratified scope)

`docs/PROJECT_FACTS.md` §2's "Current MD (/ AD)" column is now stale
relative to the recaptured fixtures (sourced from the old JHora-GUI
dates). Not corrected here — the ratified file list for this commit did
not include §2. Logged in `SESSION_LOG.md`'s S76 close block and in
`CLAUDE.md`'s Carry-Forward as a follow-up.

## Commit history this session (S76)

| Commit | Content |
|---|---|
| `b125297` | `docs/PROJECT_FACTS.md` created |
| `76a82a1` | `docs/PROJECT_FACTS.md` verification trail (diagnostic) |
| `fd9c20b` | Drik captures + D1 provenance closure + year_days ship + fixture recapture (this report) |

All 3 were unpushed as of this report; push status is tracked in this
same file's next update, not here (per the "current run only"
convention this entry itself establishes).
