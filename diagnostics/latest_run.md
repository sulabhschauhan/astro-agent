# P7 Muhurta wiring, step 3 of 6: chart_profile dispatch

Session 64. Wires `domain="muhurta_window"` into
`build_domain_profile()`'s dispatch and `_VALID_DOMAINS`, in
`agent/infra/chart_profile.py`. ONE FILE, as scoped. NOT committed --
design chat ratification pending (same posture as steps 1-2).

## Step 0: dispatch structure + _VALID_DOMAINS before editing

`_VALID_DOMAINS` (7 entries before this change): `marriage_compatibility,
career_strength, current_dasha, sade_sati, av_transit, arudha_lagna,
upapada_lagna`.

`build_domain_profile()`'s dispatch was an `if`/`elif` chain:
`marriage_compatibility -> career_strength -> current_dasha ->
av_transit -> arudha_lagna -> upapada_lagna -> else: # sade_sati`
(sade_sati is the fallback branch, not an explicit `elif` -- confirmed by
reading the source directly rather than assuming). Every branch other
than sade_sati sets `payload`, `stub_caveats`, `uncertainty_virupa`,
`uncertainty_days` then falls through to one shared
`return DomainChartProfile(...)` at the function's end.

`upapada_lagna`'s own branch (the direct precedent to mirror) does NOT
thread `evaluated_at_jd` to `build_upapada_profile(chart_data)` -- purely
natal, no as-of-instant concept, "accepted uniformly but unused" per the
function's own Args docstring.

## Departure from the prompt's literal call signature -- flagged and resolved by inspection, not guessed

The prompt describes the call as `build_muhurta_profile(chart_data)`
(mirroring upapada_lagna's no-evaluated_at_jd shape). Checked this
against `build_domain_profile()`'s own docstring instead of complying
literally: *"Reproducibility/testability requirement: this function
never calls now() internally."* `build_muhurta_profile()` (step 1)
defaults `evaluated_at_jd=None` -> internal `datetime.now(timezone.utc)`
when not supplied. Calling it as `build_muhurta_profile(chart_data)`
(omitting the argument) would make `build_domain_profile()` indirectly
violate its own stated contract: the DomainChartProfile's own
`evaluated_at_jd` field (caller-supplied) and the actual muhurta scan
window's start (a second, independently-sampled, slightly later `now()`
inside the helper) would silently diverge -- unlike av_transit/
arudha_lagna/upapada_lagna, where `evaluated_at_jd` is genuinely unused
by the domain, muhurta's scan window IS anchored to this instant.

Resolved by threading it through: `build_muhurta_profile(chart_data,
evaluated_at_jd)`. Verified empirically in the smoke test below --
`profile.evaluated_at_jd` and the first rendered window's `start_jd`
match exactly.

Both the `_VALID_DOMAINS` entry and the dispatch branch's own comments
flag this departure explicitly, per this file's existing convention of
calling out intentional deviations in-line (matching
`_format_arudha_lagna`'s "DEVIATION FLAGGED" precedent in the sibling
file).

## Diff (dispatch branch, `_VALID_DOMAINS` entries only summarized -- full comments in-file)

```python
_VALID_DOMAINS = {
    ...
    "upapada_lagna",
+   "muhurta_window",
}
```

```python
     elif domain == "upapada_lagna":
         ...
         uncertainty_days = 0.0

+    elif domain == "muhurta_window":
+        payload = build_muhurta_profile(chart_data, evaluated_at_jd)
+        stub_caveats = ()
+        uncertainty_virupa = 0.0
+        uncertainty_days = 0.0
+
     else:  # sade_sati (Session 50/P7.2a) ...
```

(Full in-file comments -- reproducibility rationale, PAYLOAD PASSTHROUGH
flag, uncertainty_days rationale -- are longer than shown here; see the
actual diff for complete text.)

## Meta values: matches step 1's ratified recommendation exactly

`stub_caveats=()`, `uncertainty_virupa=0.0`, `uncertainty_days=0.0` --
byte-identical to the values `diagnostics/latest_run.md` recommended
after step 1 landed. No invented value was needed for any field; the
only field with a genuinely new consideration was `evaluated_at_jd`
(see above), which is not one of the three meta values the prompt asked
about but a structural argument-threading question.

## PAYLOAD PASSTHROUGH -- same posture as arudha_lagna/upapada_lagna

`build_muhurta_profile()`'s return dict (`{"windows": [...], "tier":
"TIER_3_MUHURTA", "sources": (...)}`) is assigned to `payload`
unmodified, including its "tier"/"sources" meta keys that
`DomainChartProfile.payload` doesn't strictly need -- same flagged,
harmless-but-noted convention as the two sibling domains before it (see
arudha_lagna's own comment, referenced rather than duplicated).

## Docstring updates (ride-along, both files' pre-existing staleness noted)

Updated `build_domain_profile()`'s Args (domain list + evaluated_at_jd
paragraph) and Raises sections to cover muhurta_window. While there,
found the SAME pre-existing gap already flagged in
`result_formatter.py`'s module docstring (previous step's report):
neither this function's own Args `domain:` list nor the module-level
docstring's "Covers 6 domains as of Session 59" line was ever updated
for upapada_lagna's Session 62 landing. Flagged in-line at both sites,
not backfilled beyond adding accurate text for this step's own addition
-- ride-along candidate, not a standalone prompt.

## End-to-end smoke test: build_domain_profile -> format_answer

```
chart_data = calculate_chart("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")
evaluated_at_jd = swe.julday(...)   # now-UTC, orchestrator's own pattern
profile = build_domain_profile("muhurta_window", chart_data, evaluated_at_jd)
answer = format_answer(profile)
```

```
profile.domain: muhurta_window
profile.evaluated_at_jd: 2461233.2581018517
profile.stub_caveats: ()
profile.uncertainty_virupa: 0.0
profile.uncertainty_days: 0.0
profile.payload windows count: 11

answer.domain: muhurta_window   tier: AnswerTier.TIER_3_MUHURTA
answer.sources: ('muhurta_scorer.py',)
answer.stub_caveats: ()
answer.uncertainty_virupa: 0.0   uncertainty_days: 0.0
answer.demotion_reason: None
answer.route: None
summary: {'tier1_window_count': 3, 'earliest_tier1_start': '12 Jul 2026 02:59 UTC'}
first window: {"start_jd": 2461233.2581018517, "end_jd": 2461233.6245698044,
  "start": "11 Jul 2026 18:11 UTC", "end": "12 Jul 2026 02:59 UTC",
  "tier": "TIER_2", "favorable_count": 1, "warnings": []}
```

Confirms the full builder -> dispatch -> formatter chain produces a
correct, renderable `DomainAnswer` end to end, ahead of any router/
orchestrator wiring. `answer.route` is `None`, correctly un-stamped
(orchestrator-only field, per `DomainAnswer`'s own contract) --
verified, not just assumed. First window's `start_jd`
(`2461233.2581018517`) matches `profile.evaluated_at_jd` exactly,
confirming the evaluated_at_jd-threading fix above actually closes the
reproducibility gap it was written to close.

## Not wired

No edit to `calc_router.py` or `orchestrator.py`. The router still
refuses "muhurta" questions via `_UNBUILT_MODULE_KEYWORDS` (unchanged --
verified by scope, not re-tested here since router edits are out of
scope this prompt); `orchestrator.py`'s own `_VALID_DOMAINS` does not
admit `"muhurta_window"` either. A live "muhurta_window" route still
fails closed, same staged-rollout precedent as every prior new-domain
landing.

## Test run

```
python -m pytest -q
3134 passed, 3 skipped, 0 failed  (90.19s)
```

Matches the expected 3134/3/0 baseline exactly -- confirms no live path
reaches the new dispatch branch via the existing suite.

## Status

Not committed. Awaiting design-chat ratification per the prompt's own
constraint before any commit.
