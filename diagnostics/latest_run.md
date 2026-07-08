# Session 58: P6->P7 Arudha Lagna wiring (chart_profile.py + tests)

## Status

`build_arudha_lagna_profile(chart_data) -> dict` (agent/infra/chart_profile.py)
is DONE: bridges calculate_chart() output -> jaimini.padas.compute_bhava_padas(),
extracting only the house-1 (AL) entry. Standalone -- NOT yet wired into
build_domain_profile()/_VALID_DOMAINS/calc_router.py/result_formatter.py.
Router + formatter wiring is next, pending a separate design-chat decision
on question-routing keywords for this domain.

Bug fixed en route: the first draft read `chart_data["lagna_chart"]["rasi"]`
as the Lagna sign -- that field is actually Moon-sign (Chandra Rasi), not
the Ascendant (confirmed via a REPL diagnostic: Sulabh's `rasi`=Scorpio vs
`ascendant`=Sagittarius; `_koota_natal_info_from_chart` already reads this
same field into a variable named `moon_sign`). Fixed to read
`chart_data["lagna_chart"]["ascendant"]` instead.

## 4-chart Arudha Lagna table

| Chart    | lagna_sign  | arudha_sign | lord      | co_lord_deciding_step | Ratification |
|----------|-------------|-------------|-----------|------------------------|--------------|
| Sulabh   | Sagittarius | Leo         | Jupiter   | None                   | RATIFIED (hand-verified: PVR Ch.9 counting, Sg->Ar=5, 5 from Ar=Le, no step-5 exception) |
| Surbhi   | Libra       | Leo         | Venus     | None                   | Ratified (internal-consistency only -- PVR counting engine, no independent oracle) |
| Sheridan | Taurus      | Aquarius    | Venus     | None                   | Ratified (internal-consistency only) |
| David    | Virgo       | Taurus      | Mercury   | None                   | Ratified (internal-consistency only) |

None of the 4 charts have a Scorpio/Aquarius Lagna, so `co_lord_deciding_step`
is None across the board here -- the co-lord cascade path (stronger_co_lord)
is exercised separately by test_jaimini_arudha.py's own Layer C fixtures and
by this file's Layer B (see below), not by any of these 4 reference charts'
own Lagna.

## Test suite: tests/infra/test_chart_profile_arudha_lagna.py (+9 tests)

- Layer A: Sulabh AL=Leo asserted directly (ratified). Surbhi/Sheridan/David
  measure-first (shape asserted, arudha_sign not asserted -- see table above).
- Layer B: D2 fail-closed (Saturn+Rahu both in Aquarius) propagates
  unmodified through build_arudha_lagna_profile(). Real chart_data cannot
  trigger this -- the function recomputes every planet longitude live from
  jd_ut, and no real jd_ut exists where Saturn+Rahu are both in sidereal
  Aquarius (see Known Issue below). Tested via monkeypatch on the shared
  `swisseph.calc_ut` (Saturn/Rahu forced into Aquarius, real ephemeris for
  every other planet) -- the same test seam helpers/ephemeris.py's own
  CONSTRAINT section documents.
- Layer C: missing `lagna_chart` key -> KeyError; missing `ascendant` key ->
  KeyError; invalid ascendant sign string -> ValueError (from
  compute_bhava_padas).
- Layer D: result dict has exactly 6 keys, correct types.

## Baseline

3120 passed, 3 skipped, 0 failed (3111 + 9 new, zero regressions elsewhere).

## Known issue found this session (not fixed, tracked in CLAUDE.md)

`strength.py`'s D2 docstring cites "2022-23, when Saturn and Rahu were both
transiting Aquarius" as a real, documented example. Checked directly via
swisseph: Saturn was in sidereal Aquarius through 2022-23, but Rahu (Mean
Node) was in Aries/Pisces that entire window. A 1900-2030 scan at 10-day
resolution found no real Saturn+Rahu-both-in-Aquarius overlap at all. The
D2 fail-closed mechanism itself is correct and unaffected (verified via
synthetic fixtures in test_jaimini_strength.py and via this session's own
monkeypatch test) -- only the illustrative citation in the docstring is
wrong. See CLAUDE.md Carry-Forward.

## Open items (not this session's scope)

(a) Fix strength.py's D2 docstring citation (see above) -- ride-along with
    the next file touch, not a standalone prompt.
(b) calc_router.py needs a keyword set for an "arudha_lagna" domain, plus a
    collision check against `_STEM_MAP` (existing domains' keywords) before
    wiring routing -- not started.
(c) result_formatter.py needs a render branch for arudha_lagna's
    TIER_1_EXACT payload shape (arudha_sign/lagna_sign/lord/
    co_lord_deciding_step) -- not started.

## Files touched this session

- `agent/infra/chart_profile.py` -- `build_arudha_lagna_profile()` added,
  then its lagna-key bug fixed.
- `tests/infra/test_chart_profile_arudha_lagna.py` -- new file, 9 tests.
- `CLAUDE.md` -- Carry-Forward entry for the strength.py D2 docstring issue.
- `diagnostics/latest_run.md` -- this file.
