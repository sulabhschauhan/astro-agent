# Session 58: arudha_lagna render branch (result_formatter.py, ONE FILE)

Scope: add the arudha_lagna render branch to
`agent/infra/result_formatter.py` only. No test file this session. Not
committed — user reviews diffs first.

## Pre-edit review

Read `result_formatter.py` end-to-end. Findings:

- **Dispatch mechanism**: `format_answer()` is an if-chain (not a dict),
  ending in `raise ValueError(f"result_formatter: unknown domain
  {profile.domain!r}")` for anything unmatched. Registered
  `"arudha_lagna"` the same way, as the last `if` before that raise.
- **sade_sati is the correct template** (confirmed by reading
  `_format_sade_sati`, not `_format_av_transit`): TIER_1_EXACT,
  `demotion_reason=None` always, no drift language anywhere in the
  branch. `_format_av_transit` is TIER_2_RANGE with a demotion reason —
  wrong shape for this domain.

## Conflict found and flagged before editing (per CLAUDE.md Working Style
#1 — flag before proceeding)

The task's original spec asked for a rendered prose paragraph to live
inside `answer_payload`. But `chart_profile.py`'s `DomainAnswer` dataclass
documents that field explicitly:

```python
answer_payload: dict[str, Any]  # deterministic values the formatter
                                 # renders (scores, ranks, date ranges)
                                 # -- NEVER prose
```

Every existing branch (`_format_marriage`, `_format_career`,
`_format_dasha`, `_format_sade_sati`, `_format_av_transit`) honors this —
none of them puts rendered sentences into `answer_payload`, only
structured values. Making arudha_lagna the first branch to violate this
locked contract was not something to decide unilaterally.

Raised this to the user. **Decision: keep answer_payload structured-only**
(`arudha_sign`/`lagna_sign`/`lord`/`co_lord_deciding_step`, verbatim from
the payload, per branch-contract item 3) — no prose key anywhere in this
file. Prose generation, if wanted, is deferred to a separate concern for
a later prompt/layer. This keeps `_format_arudha_lagna` fully consistent
with every other domain's contract.

## Other file-convention findings (per task's own flag-if-different
instructions)

- **sources**: task spec said "copied from payload." Confirmed by
  reading: every existing branch hardcodes its `sources` tuple as a
  formatter-local literal (`("sade_sati",)`, `("shadbala", "bhava_bala")`,
  etc.) — none reads `profile.payload["sources"]`. Followed file
  convention: `sources=("padas.py",)` is a hardcoded literal in the new
  branch, not read from the payload.
- **Fail-closed posture**: confirmed all existing branches use direct
  dict indexing with no try/except — a missing key raises a bare
  `KeyError`, never rewrapped as `ValueError`. Followed the same
  convention: no defensive key handling in `_format_arudha_lagna`.
- **uncertainty_virupa**: mirrors `_format_sade_sati` exactly
  (`profile.uncertainty_virupa` passthrough).
- **uncertainty_days**: per the task's explicit override, hardcoded
  `0.0` literal (not a `profile.uncertainty_days` passthrough like
  sade_sati) — this payload has zero JD/date fields at all, stronger
  than sade_sati's own T1 case.

## Diff

```diff
--- a/agent/infra/result_formatter.py
+++ b/agent/infra/result_formatter.py
@@ -35,6 +35,19 @@ as of this branch landing (Session 54 Conflict A: formatter lands first,
 convergence wiring and router are later, separate changes) -- the payload
 shape is frozen by design-chat ahead of that layer's construction, so this
 branch is unreachable via any live router path until that wiring lands.
+
+Session 58 adds a 6th domain, "arudha_lagna" -- TIER_1_EXACT only, mirroring
+sade_sati's pattern (no dated claims anywhere in the payload, so no drift
+language, no _format_jd calls). Same staged-rollout precedent as av_transit
+above: chart_profile.py's build_arudha_lagna_profile() is a standalone
+builder, not yet wired into build_domain_profile()'s dispatch, and
+orchestrator.py's _VALID_DOMAINS does not yet admit "arudha_lagna" -- this
+branch is dead code until that separate, later wiring lands. Deviation
+flagged: the branch's original spec called for a rendered prose paragraph
+inside answer_payload, but this field is documented below as "NEVER prose"
+-- no other domain branch violates that, so answer_payload here stays
+structured-only (arudha_sign/lagna_sign/lord/co_lord_deciding_step,
+verbatim); prose rendering is deferred to a separate concern.
 """

 from __future__ import annotations
@@ -122,6 +135,8 @@ def format_answer(profile: DomainChartProfile) -> DomainAnswer:
         return _format_sade_sati(profile)
     if profile.domain == "av_transit":
         return _format_av_transit(profile)
+    if profile.domain == "arudha_lagna":
+        return _format_arudha_lagna(profile)
     raise ValueError(f"result_formatter: unknown domain {profile.domain!r}")


@@ -496,3 +511,57 @@ def _format_av_transit(profile: DomainChartProfile) -> DomainAnswer:
         ),
         uncertainty_days=profile.uncertainty_days,
     )
+
+
+def _format_arudha_lagna(profile: DomainChartProfile) -> DomainAnswer:
+    """Always TIER_1_EXACT, always demotion_reason=None -- mirrors
+    _format_sade_sati()'s pattern above: this payload carries no dated
+    claims at all (no JD fields anywhere in
+    chart_profile.py's build_arudha_lagna_profile() contract), so it never
+    inherits current_dasha's/av_transit's drift-language demotion, and this
+    branch makes no _format_jd() calls.
+
+    UNREACHABLE VIA ANY LIVE ROUTER PATH as of this branch landing:
+    build_arudha_lagna_profile() is a standalone builder, not yet wired
+    into build_domain_profile()'s own dispatch, and orchestrator.py's
+    _VALID_DOMAINS does not yet admit "arudha_lagna" -- same staged-rollout
+    precedent as _format_av_transit()'s Session 55 landing above: this
+    branch is dead code until that separate, later wiring lands.
+
+    DEVIATION FLAGGED (Session 58, design-chat decision): the original
+    branch spec called for a rendered prose paragraph inside
+    answer_payload, but DomainAnswer.answer_payload is documented
+    (chart_profile.py) as "deterministic values the formatter renders
+    (scores, ranks, date ranges) -- NEVER prose" -- no other branch in
+    this file violates that contract. Resolved by keeping answer_payload
+    structured-only, verbatim from the payload; a prose rendering, if
+    wanted, is a separate concern for a later prompt/layer.
+
+    sources=("padas.py",) is hardcoded here, NOT read from
+    profile.payload["sources"] -- matches this file's existing convention
+    (every other branch's sources tuple is a formatter-local literal, never
+    copied from the payload; see _format_sade_sati/_format_av_transit
+    above).
+
+    Missing payload keys are NOT defended against here (existing module
+    convention, see _format_marriage/_format_dasha/_format_sade_sati
+    above): direct dict indexing raises KeyError with the offending key
+    name, never a partial render.
+    """
+    answer_payload = {
+        "arudha_sign": profile.payload["arudha_sign"],
+        "lagna_sign": profile.payload["lagna_sign"],
+        "lord": profile.payload["lord"],
+        "co_lord_deciding_step": profile.payload["co_lord_deciding_step"],
+    }
+
+    return DomainAnswer(
+        domain=profile.domain,
+        tier=AnswerTier.TIER_1_EXACT,
+        answer_payload=answer_payload,
+        stub_caveats=profile.stub_caveats,
+        uncertainty_virupa=profile.uncertainty_virupa,
+        demotion_reason=None,
+        sources=("padas.py",),
+        uncertainty_days=0.0,
+    )
```

## Smoke test (print-only, hand-assembled DomainChartProfile, no test file
this session)

Two variants exercised through the real `format_answer()` dispatch (not a
mock). Prose blocks below are rendered by a throwaway script's own
`render_prose()` helper (kept OUT of result_formatter.py per the
structured-only decision above) — it consumes the branch's real
`answer_payload` output and renders the spec's template text purely for
wording ratification, not as a shipped code path.

### Variant A — Sulabh values (arudha_sign=Leo, lagna_sign=Sagittarius,
lord=Jupiter, co_lord_deciding_step=None)

```
DomainAnswer.tier: AnswerTier.TIER_1_EXACT
DomainAnswer.demotion_reason: None
DomainAnswer.uncertainty_days: 0.0
DomainAnswer.uncertainty_virupa: 0.0
DomainAnswer.sources: ('padas.py',)
DomainAnswer.answer_payload: {'arudha_sign': 'Leo', 'lagna_sign': 'Sagittarius', 'lord': 'Jupiter', 'co_lord_deciding_step': None}
```

Rendered prose:
> Your Arudha Lagna (AL) is Leo. The Arudha Lagna is the Jaimini indicator
> of your public image — how the world perceives you, as distinct from
> your Ascendant (Sagittarius), which shows who you are. It is computed
> from your Ascendant Sagittarius through its lord, Jupiter.

### Variant B — synthetic co-lord case (NOT a real chart; lagna_sign=Scorpio,
lord=Ketu, co_lord_deciding_step="Step 5(b): stronger co-lord by
&lt;criterion&gt;", arudha_sign=Leo)

```
DomainAnswer.tier: AnswerTier.TIER_1_EXACT
DomainAnswer.demotion_reason: None
DomainAnswer.uncertainty_days: 0.0
DomainAnswer.uncertainty_virupa: 0.0
DomainAnswer.sources: ('padas.py',)
DomainAnswer.answer_payload: {'arudha_sign': 'Leo', 'lagna_sign': 'Scorpio', 'lord': 'Ketu', 'co_lord_deciding_step': 'Step 5(b): stronger co-lord by <criterion>'}
```

Rendered prose:
> Your Arudha Lagna (AL) is Leo. The Arudha Lagna is the Jaimini indicator
> of your public image — how the world perceives you, as distinct from
> your Ascendant (Scorpio), which shows who you are. It is computed from
> your Ascendant Scorpio through its stronger co-lord, Ketu.

Both variants: TIER_1_EXACT, demotion_reason=None, uncertainty_days=0.0,
sources=("padas.py",) — matches BRANCH CONTRACT item 1 exactly. The
`co_lord_deciding_step` value passes through into `answer_payload`
unchanged (machine-readable diagnostic) but is never surfaced in the
prose sentence, matching spec item 2's "do NOT include the deciding-step
text in prose."

## pytest (full suite)

```
3120 passed, 3 skipped, 1 warning in 77.47s
```

Exactly matches expected 3120/3/0 — this branch is dead code (unreachable
via any live router path), so zero delta was the only correct outcome.

## Golden harness delta

```
runnable=16 non_runnable_batch=2 match=7 match_stage2=5 design_debt=0 known_gap=4 new_gap=0 error=0
report: diagnostics\golden_scorecard_20260710_164208.md
```

Baseline verification (CLAUDE.md rule #12): confirmed
`golden_scorecard_20260710_161744.md` (post-router-wiring, pre-this-edit)
was the most recent scorecard by mtime before diffing.

```
$ diff diagnostics/golden_scorecard_20260710_161744.md diagnostics/golden_scorecard_20260710_164208.md
3c3
< - Run evaluated_at_jd: `2461232.1788078705`
---
> - Run evaluated_at_jd: `2461232.1957523148`
```

**Zero delta** beyond the run timestamp, as expected — no golden row
routes to arudha_lagna (S58 router-wiring session already confirmed this).

## Not touched (deliberately out of scope this session)

- `chart_profile.py`'s `build_domain_profile()` dispatch and
  `orchestrator.py`'s `_VALID_DOMAINS` — arudha_lagna remains unreachable
  via any live path until those separate, later prompts land (same
  staged-rollout precedent as av_transit's Session 55 formatter-then-wiring
  split).
- Prose rendering — deliberately kept out of `result_formatter.py`
  entirely, per the flagged contract conflict above. If prose generation
  is wanted downstream, that's a distinct design decision for wherever
  DomainAnswer eventually gets surfaced to the user (this pipeline's V1
  scope lock: deterministic engine output is the Q&A surface, no LLM
  synthesis anywhere — CLAUDE.md V1 scope).

Not committed — diff above for review. No test file this session (tests
are the next prompt, per task instruction).
