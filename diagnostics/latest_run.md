# Session 55: av_transit builder in chart_profile.py -- STOPPED at read-first gate

**No code changed.** `chart_profile.py` was NOT touched. Per the task's
explicit instruction ("If AD start/end are available ONLY as formatted
'D Mon YYYY' strings and no JD form exists anywhere in chart_data /
chart_calculator output, STOP and report -- do not parse dates back to
JDs"), the first read-first check hit that exact condition.

## Read-first finding 1 (BLOCKER): current_dasha's AD boundaries are string-only

`build_domain_profile`'s existing `current_dasha` branch
(`chart_profile.py:470-487`) reads:
```
dasha = chart_data["dasha"]
payload = {
    "current_mahadasha": dasha.get("current_mahadasha"),
    "current_antardasha": dasha.get("current_antardasha"),
    ...
}
```
Each of `current_mahadasha`/`current_antardasha` is
`{"lord": str, "start": str, "end": str}`.

Traced the producer: `chart_calculator._calc_dasha()`
(`chart_calculator.py:458-578`) builds its Antardasha timeline (`ad_list`,
lines 516-523) using real `datetime` objects for `start`/`end`. But the
function's own `_ser()` helper (lines 568-569):
```
def _ser(d: dict) -> dict:
    return {"lord": d["lord"], "start": _fmt(d["start"]), "end": _fmt(d["end"])}
```
converts those `datetime` objects to `_fmt()`-formatted "D Mon YYYY"
strings and returns ONLY the string form (`current_antardasha":
_ser(current_ad)`, line 573) -- the underlying `datetime` objects are not
retained anywhere in the returned dict, and `chart_data` (the only thing
`build_domain_profile` receives) carries no other trace of them.

Also checked whether a JD-aware dasha implementation exists elsewhere in
the calculations package that could be called instead of reading
`chart_data["dasha"]`: `agent/calculations/dashas/vimshottari.py` is an
empty stub (docstring only, no code) -- confirmed via direct read.

**Conclusion: there is no JD float form of Antardasha start/end anywhere
in chart_data or any calculation module's output.** Design item 2
("payload['dasha_envelope'] = {..., start_jd, end_jd} as floats") cannot
be built from what currently exists without either:
(a) reworking `chart_calculator._calc_dasha()` to also expose JDs --
    a different file, outside this task's "ONE FILE ONLY" scope, or
(b) reimplementing the Vimshottari Antardasha timeline independently
    inside `chart_profile.py` -- a much larger, unsanctioned deviation
    from "add a branch that assembles existing outputs," and duplicate
    logic with `_calc_dasha()`'s own timeline builder (drift risk if the
    two diverge).
Neither is "add the av_transit branch to build_domain_profile()." Per
task instructions, stopping here rather than guessing or parsing the
date string back to a JD.

## Read-first finding 2: scan_av_transit_segments() signature + segment contents

```
scan_av_transit_segments(
    transit_planet: str,
    natal_bav: dict[str, dict[str, int]],
    natal_sav: dict[str, int],
    natal_contributors: dict[str, dict[str, frozenset[str]]],
    start_jd: float,
    end_jd: float,
) -> list[AvTransitSegment]
```
(`av_transit_scanner.py:184-191`). Each returned `AvTransitSegment`
(`av_transit_scanner.py:106-112`) already carries a full `score:
AvTransitScore` -- the scanner calls `score_av_transit()` internally per
segment (lines 247-249). **No separate score_av_transit() pass is needed
by the builder** -- segments are scored on return.

Bonus (not a blocker, noted for whoever unblocks this): the scorer's
actual `AvTransitScore` field names are `bav_rekhas`/`sav_value`
(`av_transit_scorer.py:151,154`), not `bav_bindus`/`sav_bindus` as named
in the frozen render contract -- the eventual builder will need to bridge
those names into the payload dict (same pattern as this file's existing
`shadbala_titlecase` bridge for career_strength), not itself a blocker.

## Changed files
None. `chart_profile.py` untouched. `diagnostics/latest_run.md` (this
file) and `diagnostics/calc_router_stage2.log` (none -- no tests run this
session, no log growth) are the only diagnostics touched.

## Suite count
Not run -- no code change to verify. Baseline remains 2943 passed / 3
skipped from the prior session.

## Needed to unblock
A design-chat decision on how current_dasha's Antardasha boundaries
become JD-available: extend `_calc_dasha()`'s return contract (adds a
`chart_calculator.py` change to the batch), or a different envelope
source entirely. Flagging back rather than proceeding on a guess.
