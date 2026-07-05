# P7.2c — Router flip for sade_sati domain

**Date:** 2026-07-05 (Session 50)
**Task source:** pasted prompt, "Session 50 — P7.2c"
**File touched:** `agent/infra/calc_router.py` only. No test/profile/formatter changes.

## Item 4 finding (STOP, reported, NOT fixed — per instruction)

Read `agent/infra/orchestrator.py` first, as instructed. It has its **own,
separate** domain whitelist:

```python
# orchestrator.py line 42
_VALID_DOMAINS = {"marriage_compatibility", "career_strength", "current_dasha"}
```

and enforces it defensively at line 100-105:

```python
if route_result.domain not in _VALID_DOMAINS:
    raise ValueError(
        f"answer_question: router returned unrecognized domain "
        f"{route_result.domain!r} outside the 3-domain whitelist "
        f"{sorted(_VALID_DOMAINS)}"
    )
```

**This blocks `sade_sati` end-to-end.** `route_question()` now correctly
returns `domain="sade_sati"` (verified below), but if that result were
ever passed through `answer_question()`, this line would raise
`ValueError` before `build_domain_profile()`/`format_answer()` are ever
reached — even though both of those are already `sade_sati`-ready
(P7.2a/P7.2b). Per the task's explicit instruction, this file was **not**
touched — reported only. `route_question()` itself (this session's actual
deliverable) works correctly in isolation, as the smoke checks below show;
it's only the orchestrator's own redundant whitelist that stands between
this and a working end-to-end q14 answer.

## What shipped

1. **Removed `"sade sati"` from `_UNBUILT_MODULE_KEYWORDS`** (was
   `"Sade Sati transit engine"` — this was `golden_harness.py`'s
   `_DESIGN_DEBT["sulabh_dasha_q14"]` gap, now closed at the router level).
2. **New `_BUILT_MODULE_FASTPATH` dict**: `{"sade sati", "sadesati",
   "sadhe sati"} -> "sade_sati"`, checked with the same word-boundary
   regex as the unbuilt scan, positioned after the unbuilt-module/
   out-of-scope REFUSAL checks and before domain scoring. On match, calls
   `_route_to_domain("sade_sati", 1.0, has_partner_data, chart_data)`
   (reusing the shared path rather than constructing `RouteResult` inline
   a second time — same DRY rationale the Stage 1/Stage 2 share already
   established). Deliberately bypasses `_DOMAIN_KEYWORDS`/`_score_domain`'s
   floor/margin scoring entirely — this is the flagship, zero-ambiguity
   differentiator (golden q14), so it must not depend on Stage 2/
   GPT-4o-mini being available or correct.
3. **`_route_to_domain`**: new `sade_sati` branch — `TIER_1_EXACT`,
   `demotion_reason=None`, `requires_partner=False`. Distinct from
   `current_dasha`'s ALWAYS-T2 rule: sade_sati's payload carries no dated
   mahadasha/antardasha claims, so it never inherits the ±37-day-drift
   demotion (tier-is-a-payload-property principle, Session 49/P7.0c).
4. **`_STAGE2_VALID_DOMAINS`**: added `"sade_sati"`. The tool schema's
   `enum` derives from `sorted(_STAGE2_VALID_DOMAINS)` automatically, so
   no separate schema edit was needed. **`_STAGE2_SYSTEM_PROMPT`**:
   rewritten "3 domains" -> "4 domains", added a `sade_sati` description
   paragraph.
5. Updated the unbuilt-module REFUSAL message's whitelist listing (now
   names `sade_sati` too) and the module docstring (4-domain framing,
   explains why sade_sati bypasses keyword scoring).

## Residual gap observed (not asked for, flagging for the record)

A question naming BOTH an unbuilt-keyword term and Sade Sati still refuses
via the unbuilt path first, since `_UNBUILT_MODULE_KEYWORDS` is checked
before `_BUILT_MODULE_FASTPATH` (as instructed) and `"transit"` is still
an unbuilt trigger:
```
route_question("What is my current Sade Sati transit status?")
-> REFUSAL: "question references transit engine (gochara), which is not
   in the routable whitelist..."
```
Golden q14's actual wording ("Am I currently in Sade Sati, and when does
the next cycle begin?") doesn't contain "transit", so this doesn't affect
q14 itself — reported as a dogfooding-style observation, not fixed (out
of this prompt's scope; would need either reordering the two checks or
removing "transit" as an unbuilt trigger, a separate decision).

## Smoke checks (item 6, direct `route_question()` calls)

```python
route_question("Am I currently in Sade Sati, and when does the next cycle begin?")
-> RouteResult(domain='sade_sati', tier=TIER_1_EXACT, confidence=1.0,
                demotion_reason=None, requires_partner=False)

route_question("ashtakavarga strength?")
-> RouteResult(domain=None, tier=REFUSAL, confidence=0.0,
                demotion_reason="question references Ashtakavarga (BAV/SAV), "
                "which is not in the routable whitelist (marriage_compatibility, "
                "career_strength, current_dasha, sade_sati)",
                requires_partner=False)
```
Both match the task's expected outcomes exactly.

## Full suite

```
1786 passed, 3 skipped, 1 warning in 72.12s
```
Unchanged — grepped `tests/` for any `"sade sati"`-unbuilt-refusal
assertion; none exists (all other `sade_sati` references are the
calculation module's own tests or golden fixture data, not router
assertions), consistent with the green run.

## Explicitly not done (per task scope / instruction)

- **`orchestrator.py` NOT edited** — its own `_VALID_DOMAINS` whitelist
  blocks `sade_sati` end-to-end; reported per item 4's explicit "STOP,
  do not edit a second file" instruction.
- No test/profile/formatter changes.
- Did not fix the "transit"-keyword-vs-fast-path ordering interaction
  noted above.
