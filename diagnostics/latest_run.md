# Session 55: av_transit wiring in orchestrator.py

**Changed file:** `agent/infra/orchestrator.py` only, plus the benign
`diagnostics/calc_router_stage2.log` growth from running the suite. No
other file touched (`calc_router.py`, `chart_profile.py`,
`result_formatter.py`, and all test files untouched, as required).

## Read-first: transit_planet-key confirmation

Grepped `chart_profile.py`'s av_transit branch for its payload assembly.
Confirmed (`chart_profile.py:631-635`):
```python
payload = {
    "transit_planet": transit_planet,
    "dasha_envelope": envelope,
    "sub_windows": sub_windows,
}
```
The `"transit_planet"` key IS present -- `result_formatter.py`'s
`_format_av_transit()` indexing `profile.payload["transit_planet"]` will
resolve correctly once the router can emit this domain. No STOP needed;
proceeded with the wiring change.

## Change summary

1. `_VALID_DOMAINS`: added `"av_transit"`, with a Session 55 comment
   explaining it's a dead entry by design until `calc_router.py`'s own
   wiring lands (mirrors the `sade_sati` wiring-order precedent already
   documented on the set).
2. `answer_question()` gains `transit_planet: str = "Saturn"`
   (keyword-only, added after a new `*`). It is passed to
   `build_domain_profile()` via a new `is_av_transit` flag, following the
   existing `is_marriage` conditional-kwarg pattern exactly:
   ```python
   is_marriage = route_result.domain == "marriage_compatibility"
   is_av_transit = route_result.domain == "av_transit"
   profile = build_domain_profile(
       route_result.domain, chart_data, evaluated_at_jd,
       partner_chart_data=partner_chart_data if is_marriage else None,
       primary_role=primary_role if is_marriage else None,
       transit_planet=transit_planet if is_av_transit else "Saturn",
   )
   ```
   Docstring updated: new `transit_planet` Args entry, and the existing
   Session 50/P7.2d NOTE amended to acknowledge the second, parallel
   `is_av_transit` conditional (still mutually exclusive with
   `is_marriage` -- a question routes to exactly one domain) rather than
   leaving a now-inaccurate "the only domain-specific branch" claim in
   place.
3. Demotion merge (`_merge_router_demotion()`) left completely untouched,
   per the design lock -- documented with a new comment block directly
   above `_VALID_DOMAINS`'s av_transit entry: once router wiring lands,
   `route_question()` will set `demotion_reason=None` for this domain,
   so `_merge_router_demotion()`'s existing `if router_reason is None:
   return answer` early-return already does the right thing without any
   code change -- av_transit's ±37-day-plus-day-level-resolution
   demotion string stays formatter-owned, with no " | " duplication risk.

## Verification

- `python -c "import agent.infra.orchestrator"` -- clean import.
- Confirmed in-process: `"av_transit" in orchestrator._VALID_DOMAINS` ->
  `True`; `inspect.signature(answer_question)` shows
  `transit_planet: str = 'Saturn'` correctly keyword-only.
- Grepped `tests/` for `_VALID_DOMAINS` / "routable whitelist" -- no test
  references this set directly, so widening it carries no assertion risk.
- `calc_router.route_question()` still cannot emit `"av_transit"` (no
  router keywords wired) -- confirmed no behavior change is reachable via
  any live question string; the new kwarg and whitelist entry are
  dead-by-design until the next, separate router-wiring change.

## Suite count

Full suite: `2943 passed, 3 skipped, 1 warning` -- **identical** to the
pre-change baseline. Zero delta, exactly as expected (router still
cannot emit this domain).

## Sequencing status

Formatter -> convergence wiring (chart_profile.py builder) -> orchestrator
wiring (this session) are all done. Only `calc_router.py`'s own domain
classification (keywords, confidence floor/margin, `_UNBUILT_MODULE_KEYWORDS`
removal for av_transit, and the CLAUDE.md carry-forward item updating
`test_refusal_ashtakavarga_still_unbuilt`) remains to make this domain
live end-to-end.
