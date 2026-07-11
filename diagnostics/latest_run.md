# S72 (prompt 2 of RouteResult.route bundle): STOP -- ambiguous call
sites found before any edit made

FILE IN SCOPE: `agent/infra/calc_router.py` only (per task: orchestrator.py,
result_formatter.py, golden_harness.py explicitly out of scope this prompt).

TASK: add `route: Literal["stage1", "stage2", "fastpath"]` field to
`RouteResult`, no default, assigned per construction site by ACTUAL
resolution path (not by domain). Task instruction: "If any site's correct
route value is ambiguous, STOP and flag it here instead of guessing."

**Outcome: STOPPED. No file edited. No diff to report. No tests run
(nothing changed).**

## Step 0: full `RouteResult(` construction-site grep (12 sites)

```
608:            return RouteResult(
615:        return RouteResult(
624:        return RouteResult(
640:        return RouteResult(
658:        return RouteResult(
684:        return RouteResult(
709:        return RouteResult(
733:    return RouteResult(
775:        return RouteResult(
813:    return RouteResult(
853:            return RouteResult(
867:            return RouteResult(
```

| Line | Enclosing function | What it represents |
|---|---|---|
| 608 | `_route_to_domain()` | `marriage_compatibility`, `not has_partner_data` -> REFUSAL |
| 615 | `_route_to_domain()` | `marriage_compatibility` -> ROUTE |
| 624 | `_route_to_domain()` | `career_strength` -> ROUTE |
| 640 | `_route_to_domain()` | `sade_sati` -> ROUTE |
| 658 | `_route_to_domain()` | `av_transit` -> ROUTE |
| 684 | `_route_to_domain()` | `arudha_lagna` -> ROUTE |
| 709 | `_route_to_domain()` | `upapada_lagna` -> ROUTE |
| 733 | `_route_to_domain()` | `current_dasha` fallthrough -> ROUTE |
| 775 | `_stage2_fallback()` | `_stage2_classify` raised -> REFUSAL |
| 813 | `_stage2_fallback()` | Stage 2 returned non-high confidence -> REFUSAL |
| 853 | `route_question()` | unbuilt-module-keyword guard -> REFUSAL |
| 867 | `route_question()` | out-of-scope-keyword guard -> REFUSAL |

## Caller tracing -- the structural problem this surfaced

`_route_to_domain()` (the 8 sites at 608-733) is called from **three**
different places in `route_question()`/`_stage2_fallback()`, and has no
parameter telling it which one invoked it:

- `route_question():886` -- sade_sati fast-path (`_BUILT_MODULE_FASTPATH`
  phrase match; only ever passes `domain="sade_sati"`)
- `route_question():908` -- Stage 1 keyword-floor+margin path (any of the
  6 `_DOMAIN_KEYWORDS` domains)
- `_stage2_fallback():784` -- Stage 2 LLM path (any `_STAGE2_VALID_DOMAINS`
  member)

Cross-referencing `_DOMAIN_KEYWORDS` (6 keys: marriage_compatibility,
career_strength, current_dasha, av_transit, arudha_lagna, upapada_lagna --
**no `sade_sati`**) against `_STAGE2_VALID_DOMAINS` (adds sade_sati +
none):

- The 7 domain-branches at 608/615/624/658/684/709/733 are each reachable
  via **either** Stage 1 (908) **or** Stage 2 (784) from the identical
  source line -- a hardcoded literal at any of these lines would be
  correct only part of the time, depending on which caller's input
  actually reached it at runtime.
- Line 640 (`sade_sati`) is reachable via **either** the fast-path (886)
  **or** Stage 2 (784), since `sade_sati` is absent from
  `_DOMAIN_KEYWORDS` and therefore unreachable via Stage 1 scoring at
  all.

**Non-guessing resolution identified for these 10 sites** (mechanical,
not a judgment call): thread a `route` parameter into
`_route_to_domain()`'s signature, sourced from each of its 3 real
callers, and use that parameter (not a hardcoded per-branch literal) in
all 8 `RouteResult(...)` calls inside it:

- `route_question():886` -> `_route_to_domain(domain, 1.0, has_partner_data, chart_data, route="fastpath")`
- `route_question():908` -> `_route_to_domain(best_domain, best_score, has_partner_data, chart_data, route="stage1")`
- `_stage2_fallback():784` -> `_route_to_domain(stage2_domain, ..., route="stage2")`

Lines 775/813 (inside `_stage2_fallback` directly, not via
`_route_to_domain`) are unambiguous as-is: `route="stage2"` (Stage 2 was
attempted, either raised or returned non-high confidence).

## The genuine open ambiguity: lines 853 and 867

These two REFUSALs fire in `route_question()` **before** Stage 1 scoring,
the fast-path, or Stage 2 ever run -- pre-classification guards
(unbuilt-module keyword, out-of-scope keyword). No domain was ever
"resolved by" any of stage1/stage2/fastpath; the question was refused
before any of the three mechanisms engaged. None of the three given
values cleanly describes this. Not defaulted to `"stage1"` on the
grounds of code adjacency alone -- the module's own docstring is
deliberate that `"Stage 1"` means specifically `_score_domain`'s
floor/margin scoring, and this same prompt already established (by
carving out `"fastpath"` as its own value) that adjacency-to-Stage-1 is
not sufficient grounds to label something `"stage1"`.

Stopped here rather than partially editing: fixing the 10 unambiguous
sites while leaving 853/867 broken would leave `route_question()` unable
to construct `RouteResult` for two REFUSAL categories real tests almost
certainly exercise (yoga/transit/navamsa/etc. keyword REFUSALs,
out-of-scope REFUSALs) -- worse than not editing at all.

Two resolution options put to the user, unresolved as of this entry:

**A.** Widen the type by one value: `Literal["stage1", "stage2",
"fastpath", "pre_classification"]` (or similar), giving these guards
their own honest label.

**B.** Keep the 3-value type and treat these as `"stage1"` under a
broadened definition ("resolved without an LLM call, before or via the
deterministic keyword layer") -- accepting this reading is broader than
the module's own existing "Stage 1 = `_score_domain`" terminology.

## Verification

No source files touched. No test files touched. No test suite run
(nothing changed to verify). Once the user picks A or B above, the next
prompt should: (1) add the field, (2) thread `route` through
`_route_to_domain()`'s 3 call sites per the mapping above, (3) assign
853/867 per the chosen resolution, (4) paste every changed construction
site as a verbatim diff, (5) run only the router-specific test file(s)
and report exact pass/fail counts.

## Commit

Not committed -- no source edit made this prompt, diagnostics-only
write.
