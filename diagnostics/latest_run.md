# Session 58: arudha_lagna router wiring (calc_router.py, ONE FILE)

Scope: wire `arudha_lagna` into `agent/infra/calc_router.py` only. No test
file this session. Not committed — user reviews diffs first.

## Pre-edit review finding (flagged before editing, per CLAUDE.md Working
Style #1/#11)

Read `calc_router.py` end-to-end before editing. The task's original 4-edit
list registered `arudha_lagna` in `_DOMAIN_KEYWORDS` (Stage 1) and
`_STAGE2_VALID_DOMAINS` (Stage 2), but did not add a matching branch to
`_route_to_domain()`. That function's final block is an *unconditional*
fallthrough that returns a **hardcoded literal** `domain="current_dasha"`
for any domain string not explicitly branched. Net effect: an
`arudha_lagna` keyword win (e.g. "what is my public image") would have
silently been answered as `current_dasha` — wrong domain, wrong tier, wrong
content — and would have passed `orchestrator.py`'s `_VALID_DOMAINS` gate
cleanly (since `"current_dasha"` is valid), so nothing downstream would
have caught it.

Cross-checked against the av_transit precedent this task is modeled on:
when av_transit entered `_DOMAIN_KEYWORDS` (Session 55), its
`_route_to_domain` branch (lines 583-599 pre-edit) landed **in the same
change** — keyword registration alone makes a domain Stage-1-live, so the
branch is not optional.

Raised this to the user; they approved adding a 5th edit (the
`_route_to_domain` branch) rather than shipping the gap. Tier chosen
(`TIER_1_EXACT`, no demotion) matches `chart_profile.py`'s
`build_arudha_lagna_profile()` payload docstring, which already documents
`"tier": "TIER_1_EXACT"`. Confirmed `orchestrator.py`'s own
`_VALID_DOMAINS` does NOT yet admit `"arudha_lagna"` (that sync is
explicitly deferred — `build_arudha_lagna_profile()`'s docstring: "NOT yet
wired into build_domain_profile()/_VALID_DOMAINS/the router or formatter
— domain/router/formatter integration is a separate, later prompt") — so
with the new branch in place, a live `arudha_lagna` route now fails CLOSED
via orchestrator's defensive `ValueError`, not a silent wrong answer. Same
staged-rollout precedent as av_transit's Session 55 router-then-orchestrator
split.

## 5 edits applied (4 requested + 1 approved)

1. `_ARUDHA_LAGNA_KEYWORDS` added, registered in `_DOMAIN_KEYWORDS` (mirrors
   `_AV_TRANSIT_KEYWORDS`).
2. `"arudha_lagna"` added to `_STAGE2_VALID_DOMAINS`; `_STAGE2_SYSTEM_PROMPT`
   bullet added, "5 domains" → "6 domains" (both mentions).
3. `_STAGE2_TOOL_SCHEMA` description "3 routable domains" → "6" (was already
   stale pre-edit at the true count of 5 — flagged as pre-existing,
   fixed opportunistically, inline comment added so a reviewer doesn't
   mistake it for drive-by scope creep).
4. `"jaimini"` removed from `_UNBUILT_MODULE_KEYWORDS`; comment added above
   the tuple.
5. **(approved addition)** `_route_to_domain()` gained an `arudha_lagna`
   branch: `TIER_1_EXACT`, `demotion_reason=None`, `requires_partner=False`
   — see finding above.

## Diffs

```diff
--- a/agent/infra/calc_router.py
+++ b/agent/infra/calc_router.py
@@ -82,11 +82,21 @@ _AV_TRANSIT_KEYWORDS: tuple[str, ...] = (
     "ashtakavarga", "bindu", "kakshya",
 )

+# arudha_lagna (Session 58 router wiring). Public-image/perception phrasing
+# ("public image", "public perception") alongside the literal Jaimini terms
+# ("arudha lagna", "arudha pada") -- mirrors av_transit's precedent of
+# pairing a technical term list with the layman phrasing Stage 1 can catch
+# directly, without requiring Stage 2 for the common case.
+_ARUDHA_LAGNA_KEYWORDS: tuple[str, ...] = (
+    "arudha lagna", "arudha pada", "public image", "public perception",
+)
+
 _DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
     "marriage_compatibility": _MARRIAGE_KEYWORDS,
     "career_strength": _CAREER_KEYWORDS,
     "current_dasha": _DASHA_KEYWORDS,
     "av_transit": _AV_TRANSIT_KEYWORDS,
+    "arudha_lagna": _ARUDHA_LAGNA_KEYWORDS,
 }
```

```diff
--- a/agent/infra/calc_router.py
+++ b/agent/infra/calc_router.py
@@ -244,6 +256,7 @@ _STAGE2_VALID_DOMAINS: frozenset[str] = frozenset(
         "current_dasha",
         "sade_sati",
         "av_transit",
+        "arudha_lagna",
         "none",
     }
 )
@@ -269,7 +282,7 @@ _STAGE2_LOG_PATH = Path(__file__).resolve().parents[2] / "diagnostics" / "calc_r
 _STAGE2_SYSTEM_PROMPT = """\
 You are a routing classifier for a Vedic astrology calculation Q&A pipeline.

-This pipeline can ONLY answer questions in exactly 5 domains:
+This pipeline can ONLY answer questions in exactly 6 domains:
  marriage_compatibility: Ashtakoot/Guna Milan, Mangal Dosha, spouse or \
 partner compatibility.
  career_strength: career/profession/work strength, based on Shadbala \
@@ -284,15 +297,17 @@ current, previous, or next Sade Sati cycle starts or ends.
 sub-windows, from Bindu/Kakshya strength) of a specific transiting planet \
 DURING the current Antardasha -- finer-grained timing WITHIN the current \
 dasha period, not just which lord is currently running.
+ arudha_lagna: questions about self-image, public perception, reputation, \
+how one is seen by others (Jaimini Arudha Lagna).

 Classify the question into exactly one of these domains, or "none" if it
-does not clearly ask about one of these 5 things (for example: health,
+does not clearly ask about one of these 6 things (for example: health,
 travel, gemstones, lucky numbers, or any other topic).

 Call classify_domain with:
- domain: the single best-matching domain, or "none".
- confidence: "high" ONLY if the question clearly and unambiguously asks
-  about exactly one of the 5 domains above; "medium" or "low" for any
+  about exactly one of the 6 domains above; "medium" or "low" for any
   ambiguity, a different topic, or a domain this pipeline does not cover.
 """
```

```diff
--- a/agent/infra/calc_router.py
+++ b/agent/infra/calc_router.py
@@ -300,9 +315,13 @@ _STAGE2_TOOL_SCHEMA = {
     "type": "function",
     "function": {
         "name": "classify_domain",
+        # Session 58: "3 routable domains" was already stale pre-edit
+        # (actual count had drifted to 5 with sade_sati/av_transit) --
+        # design-chat-flagged pre-existing bug, fixed opportunistically here
+        # alongside the arudha_lagna wiring, not a drive-by unrelated change.
         "description": (
             "Classify a Vedic astrology question into one of the pipeline's "
-            "3 routable domains, or none."
+            "6 routable domains, or none."
         ),
```

```diff
--- a/agent/infra/calc_router.py
+++ b/agent/infra/calc_router.py
@@ -101,6 +111,9 @@ _DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
 # built and 4-chart validated, unlike the genuinely-unbuilt modules below
 # -- refusing it here was product debt, not a locked decision). Now routed
 # via _BUILT_MODULE_FASTPATH instead.
+# Session 58: "jaimini" removed -- all jaimini/ modules exist as of
+# Session 57; unwired-Q&A refusals now go through the router's normal
+# "domain not routable" path, not this guard.
 _UNBUILT_MODULE_KEYWORDS: dict[str, str] = {
     "yoga": "yoga detection",
     "transit": "transit engine (gochara)",
@@ -110,7 +123,6 @@ _UNBUILT_MODULE_KEYWORDS: dict[str, str] = {
     "d10": "D10 divisional chart",
     "d9": "D9 (Navamsa) divisional chart",
     "varga": "divisional charts (vargas)",
-    "jaimini": "Jaimini karakas/arudha/padas",
     "chara": "Chara dasha",
     "yogini": "Yogini dasha",
     "ashtottari": "Ashtottari dasha",
```

```diff
--- a/agent/infra/calc_router.py
+++ b/agent/infra/calc_router.py
@@ -598,6 +617,32 @@ def _route_to_domain(
             requires_partner=False,
         )

+    if domain == "arudha_lagna":
+        # T1, no demotion, no partner -- mirrors sade_sati's pattern above:
+        # chart_profile.py's build_arudha_lagna_profile() payload docstring
+        # states tier="TIER_1_EXACT" (single deterministic Arudha sign/lord,
+        # no uncertainty envelope). NOTE (Session 58): this branch exists so
+        # Stage 1's fallthrough never mislabels an arudha_lagna keyword hit
+        # as current_dasha (the previous unconditional final block below
+        # returns a hardcoded "current_dasha" literal for ANY unhandled
+        # domain) -- without this branch, a keyword-scoring win here would
+        # silently produce a wrong-domain answer instead of failing safely.
+        # orchestrator.py's own _VALID_DOMAINS does NOT yet admit
+        # "arudha_lagna" (build_domain_profile()/formatter integration is a
+        # separate, later prompt per chart_profile.py's
+        # build_arudha_lagna_profile() docstring) -- until that sync lands,
+        # a question routed here will fail closed with orchestrator's
+        # defensive ValueError, same "_VALID_DOMAINS sync discipline"
+        # precedent as av_transit's Session 55 router-then-orchestrator
+        # staged rollout.
+        return RouteResult(
+            domain="arudha_lagna",
+            tier=AnswerTier.TIER_1_EXACT,
+            confidence=confidence,
+            demotion_reason=None,
+            requires_partner=False,
+        )
+
     # current_dasha -- ALWAYS TIER_2_RANGE in V1 (design-chat reversal of
```

## pytest (full suite)

```
3120 passed, 3 skipped, 1 warning in 88.62s
```

Exactly matches expected 3120/3/0.

## Golden harness delta

Ran `python -m agent.eval.golden_harness`:

```
runnable=16 non_runnable_batch=2 match=7 match_stage2=5 design_debt=0 known_gap=4 new_gap=0 error=0
report: diagnostics\golden_scorecard_20260710_161744.md
```

Baseline verification (CLAUDE.md rule #12 — baseline filenames are claims,
not facts): confirmed `golden_scorecard_20260707_112916.md` is the most
recent pre-edit scorecard file by mtime before diffing against it.

```
$ diff diagnostics/golden_scorecard_20260707_112916.md diagnostics/golden_scorecard_20260710_161744.md
3c3
< - Run evaluated_at_jd: `2461228.978414352`
---
> - Run evaluated_at_jd: `2461232.1788078705`
```

**Zero delta** beyond the run timestamp. All tallies identical
(`match=7 match_stage2=5 known_gap=4 new_gap=0 error=0`) — no golden row
touches arudha_lagna or jaimini, as expected.

## Not touched (deliberately out of scope this session)

- Module docstring's "4 routable domains as of Session 50/P7.2c" header
  comment (line 3) is now stale (true count is 6) — not touched, scope was
  ONE FILE / 5 edits only, not a full-file docstring pass.
- `_UNBUILT_MODULE_KEYWORDS` REFUSAL message body (route_question(), ~line
  744) still lists only `(marriage_compatibility, career_strength,
  current_dasha, sade_sati)` — already missing av_transit pre-edit, now
  also missing arudha_lagna. Pre-existing staleness, not introduced this
  session, not part of the scoped edits.
- `orchestrator.py`'s `_VALID_DOMAINS` and `chart_profile.py`'s
  `build_domain_profile()`/formatter wiring for arudha_lagna — explicitly
  deferred to a separate, later prompt per
  `build_arudha_lagna_profile()`'s own docstring. Until that lands, a live
  `arudha_lagna` route fails closed with `orchestrator.answer_question()`'s
  defensive `ValueError`, by design.

Not committed — diffs above for review.
