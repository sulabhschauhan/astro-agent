# P7 Muhurta wiring, step 2 of 5: result_formatter.py branch

Session 64. Adds `_format_muhurta_window(payload)` to
`agent/infra/result_formatter.py`, registered in `format_answer()`'s
dispatch, plus a new `_jd_to_utc_str()` helper. ONE FILE, as scoped. NOT
committed -- design chat ratification pending per the prompt's own
constraint (same posture as step 1).

## Registration diff (format_answer dispatch)

```python
     if profile.domain == "upapada_lagna":
         return _format_upapada(profile)
+    if profile.domain == "muhurta_window":
+        return _format_muhurta_window(profile.payload)
     raise ValueError(f"result_formatter: unknown domain {profile.domain!r}")
```

Note the call passes `profile.payload`, not `profile` -- see the
signature-deviation section below.

## JD -> human-readable string: reuse check, then a new helper

Checked for an existing reusable JD->datetime helper before writing one,
per the prompt's instruction. Found `_format_jd()` already in this file
(day-level only, "D Mon YYYY", no time-of-day -- explicitly documented as
this file's "only human-date format used anywhere in this pipeline's
payloads so far"). Unsuitable here: a Muhurta window's whole purpose is
pinpointing an hour-range within a day (Chandrabala ~2.27d/sign,
Tarabala ~1d/nakshatra -- window boundaries do not align to day
boundaries), so day-level rendering would silently collapse distinct
window boundaries onto the same date string.

Checked siblings too: `panchanga.py`'s `_julian_day_ut_to_datetime` and
`kala_bala.py`'s `_jd_to_utc_datetime` implement the identical
`swe.revjul()` + `timedelta` mechanics, but both are module-private --
this project's own documented "per-module duplication convention"
(chart_profile.py comment), not an importable cross-module utility.
No existing helper anywhere returns a full datetime string with
time-of-day and an explicit UTC label.

Added `_jd_to_utc_str(jd_ut) -> str`: reuses the identical
`swe.revjul()` + `timedelta` conversion mechanics `_format_jd()` already
uses (not a second, independently-invented conversion path -- only the
string-formatting layer is new), returns `"D Mon YYYY HH:MM UTC"`
(minute-level). Docstring carries the locked line verbatim: *"V1 renders
UTC with explicit UTC labels -- chart_data carries birth place, not the
user's current location; local-timezone rendering deferred to V1.1."*

## `_format_muhurta_window(payload)`: two deliberate departures from
## `_format_arudha_lagna`/`_format_upapada` precedent, both flagged in-code

1. **Signature: `payload: dict`, not `profile: DomainChartProfile`.**
   Every DomainAnswer field this branch sets is either a hardcoded
   literal (`stub_caveats=()`, `uncertainty_virupa=0.0`,
   `uncertainty_days=0.0` -- step 1's recommended values) or read
   straight off the payload dict (`sources`) -- nothing in this branch
   ever needs `profile.domain`/`profile.stub_caveats`/
   `profile.uncertainty_virupa`/`profile.uncertainty_days`, so there's
   no reason to thread the full `DomainChartProfile` through. The task
   prompt's own literal signature (`_format_muhurta_window(payload)`)
   matches this reasoning exactly, so it was followed as-is rather than
   forced into the sibling `profile`-argument shape.
2. **`sources` read from `payload["sources"]`, not hardcoded.** Sibling
   branches document hardcoding sources locally and explicitly ignoring
   `profile.payload["sources"]` (arudha/upapada's own docstrings say so
   verbatim). Muhurta departs on the prompt's own explicit instruction
   ("sources from payload") -- justified because
   `chart_profile.build_muhurta_profile()` is the one place that knows
   which module actually produced the payload
   (`muhurta_scorer.py`, itself composing chandrabala/tarabala/panchaka
   internally); duplicating that literal here would just be a second,
   driftable copy of a fact the builder already computed once. `tier` is
   NOT read the same way -- always `AnswerTier.TIER_3_MUHURTA` by
   construction, same payload-property principle as every other
   single-domain branch.

Both departures are documented in the function's own docstring, matching
this file's existing convention of flagging intentional deviations
in-line (see `_format_arudha_lagna`'s own "DEVIATION FLAGGED" precedent).

## Two distinct "tier" fields -- documented, not conflated

Per-window `"tier"` in `answer_payload["windows"][i]` is
`muhurta_scorer.MuhurtaTier`'s value string (`"TIER_1"`/`"TIER_2"`/
`"TIER_3"`, per-window Muhurta *quality*). The `DomainAnswer.tier` field
itself is the pipeline's `AnswerTier.TIER_3_MUHURTA` (always, for this
domain) -- a structurally distinct enum. Comment placed directly at the
per-window tier-rendering line, as the prompt asked, plus a
cross-reference in the function docstring.

## answer_payload shape

```python
{
    "windows": [
        {
            "start_jd": float, "end_jd": float,          # raw, machine-readable
            "start": str, "end": str,                     # "D Mon YYYY HH:MM UTC"
            "tier": str,                                   # MuhurtaTier value
            "favorable_count": int,                         # 0-2
            "warnings": tuple[str, ...],
        },
        ...
    ],
    "summary": {
        "tier1_window_count": int,
        "earliest_tier1_start": str,   # rendered UTC string, or the
                                        # explicit "none in the 7-day scan"
                                        # marker -- key never omitted
    },
}
```

Design call made here, not specified by the prompt: `summary` is a
nested sub-dict rather than two flattened top-level keys alongside
`windows`. Chosen for self-documentation and to avoid any future key
collision; flagged here as a judgment call in case a later step assumed
flattened keys instead.

## Ordering: asserted, not re-sorted

Iterates consecutive window pairs and raises `ValueError` (naming
`"muhurta_window"` and the offending JD pair) if `end_jd > next start_jd`
-- per chart_profile.build_muhurta_profile()'s (and beneath it,
`find_muhurta_windows()`'s) own documented ascending/contiguous
guarantee. No re-sort logic added.

## Error handling

`payload["windows"]` / `payload["sources"]` / any per-window key access
wrapped in `try/except KeyError`, re-raised as
`ValueError(f"result_formatter: muhurta_window payload missing key {exc}")`
-- domain name present in every message, per the prompt's instruction.
This is a deliberate departure from this file's usual bare-KeyError
convention (documented explicitly in-code as such), since the prompt
specifically asked for wrapped, meaningful errors on this branch.

Verified by direct invocation (not yet covered by any test, per this
step's constraints):
- Missing `"windows"` key -> `ValueError: result_formatter: muhurta_window
  payload missing key 'windows'`.
- Out-of-order/non-contiguous windows -> `ValueError: ...windows are not
  ascending/contiguous... (10.0 > 1.0)`.
- Empty `windows` list -> no error; `summary` renders
  `{"tier1_window_count": 0, "earliest_tier1_start": "none in the 7-day
  scan"}`.
- **Edge case flagged, not fixed**: a per-window `start_jd` far outside
  any real chart's range (synthetic test value `1.0`, i.e. ~4713 BCE)
  raises a bare `ValueError` from `_jd_to_utc_str()`'s own
  `datetime()` construction (Python's `datetime` min year is 1), NOT
  wrapped with the domain name -- it isn't a missing/malformed *key*, so
  the `except KeyError` clause doesn't catch it. This can never occur
  from real `chart_profile.build_muhurta_profile()` output (JDs are
  always ~2.46 million for any real date, evaluated_at_jd to
  evaluated_at_jd+7.0) -- not adding speculative handling for a
  scenario the real pipeline cannot produce.

## End-to-end smoke test (not part of the automated suite)

Ran `build_muhurta_profile()` -> `_format_muhurta_window()` directly
against Sulabh's real chart (`calculate_chart("Sulabh", "6 Apr 1988",
"00:30", "Calcutta, India")`):

```
windows found: 11
domain: muhurta_window   tier: AnswerTier.TIER_3_MUHURTA
sources: ('muhurta_scorer.py',)
stub_caveats: ()   uncertainty_virupa: 0.0   uncertainty_days: 0.0
first window: {"start_jd": 2461233.25, "end_jd": 2461233.62,
  "start": "11 Jul 2026 18:00 UTC", "end": "12 Jul 2026 02:59 UTC",
  "tier": "TIER_2", "favorable_count": 1, "warnings": []}
summary: {'tier1_window_count': 3,
  'earliest_tier1_start': '12 Jul 2026 02:59 UTC'}
```

Confirms the full chain (step 1 builder -> step 2 formatter) actually
produces a correct, renderable `DomainAnswer` end to end, ahead of any
router/orchestrator wiring.

## Not wired

No edit to `build_domain_profile()`'s dispatch, `_VALID_DOMAINS`,
`calc_router.py`, or `orchestrator.py` -- `format_answer()`'s new branch
is reachable only if a caller hand-builds a
`DomainChartProfile(domain="muhurta_window", ...)` itself (as the smoke
test did indirectly, by calling `_format_muhurta_window()` on the raw
payload dict directly rather than through `format_answer()`). Via any
live/router path it remains dead code.

## Test run

```
python -m pytest -q
3134 passed, 3 skipped, 0 failed  (83.95s)
```

Matches the expected 3134/3/0 baseline exactly -- confirms the new
dispatch branch is unreachable via the existing suite, as expected until
`build_domain_profile()` wires the domain in a later step.

## Status

Not committed. Awaiting design-chat ratification per the prompt's own
constraint before any commit. `agent/infra/chart_profile.py` (step 1,
already reported previously) also remains uncommitted, unchanged since
the last report.
