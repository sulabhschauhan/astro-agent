# Session 59 (cont.): arudha_lagna wired into build_domain_profile() dispatch

Scope: ONE FILE, `agent/infra/chart_profile.py` — widen `_VALID_DOMAINS` and
add the `build_domain_profile()` dispatch branch for `"arudha_lagna"`. Not
committed — user reviews diffs first.

## Pre-edit review

Read `build_domain_profile()` end-to-end and this file's own
`_VALID_DOMAINS` constant. Confirmed the Session 55 incident this task
warned about: `orchestrator.py`'s own `SENSITIVE_TO` comment documents that
`chart_profile.py`'s gate was once missed when av_transit shipped
elsewhere, leaving its builder branch dead for a full session before being
caught (fix-forward, commit 4e52e77). This prompt widens `_VALID_DOMAINS`
in the SAME change as the dispatch branch, avoiding a repeat.
`orchestrator.py`'s own `_VALID_DOMAINS` is deliberately NOT touched — a
separate, later prompt, same staged precedent.

Also checked existing tests before editing: `tests/infra/
test_chart_profile_arudha_lagna.py` only exercises `build_arudha_lagna_
profile()` directly, never `build_domain_profile()` — no test asserts
`build_domain_profile` REFUSES/raises on `"arudha_lagna"` via the old gate.
Low regression risk confirmed before editing, not just hoped.

## 4 edits applied

1. **`_VALID_DOMAINS`** += `"arudha_lagna"`, with a comment documenting
   that `build_domain_profile()`'s dispatch branch lands in the same
   change (avoiding the exact av_transit incident) and that
   `orchestrator.py`'s own `_VALID_DOMAINS` sync is a separate, later
   prompt.
2. **`build_domain_profile()`** gains an `elif domain == "arudha_lagna":`
   branch (added before the final `else: # sade_sati` catch-all, which
   otherwise would have silently absorbed `"arudha_lagna"` once it passed
   the top-of-function `_VALID_DOMAINS` check — sade_sati's branch is
   implemented as an unconditional `else`, not its own explicit `elif`,
   so a new domain MUST get its own `elif` before that `else` or it would
   be silently misrouted through the sade_sati path):
   - `payload = build_arudha_lagna_profile(chart_data)`
   - `stub_caveats = ()` — mirrors sade_sati's own no-stub convention.
   - `uncertainty_virupa = 0.0` — mirrors sade_sati.
   - `uncertainty_days = 0.0` — literal, with the exact comment text the
     task specified ("RATIFIED S59 — formatter's `_format_arudha_lagna`
     also asserts 0.0 as a hardcoded contract assertion...").
   - Comment noting `evaluated_at_jd` is accepted but genuinely unused
     (Arudha Lagna is purely natal), same precedent as av_transit's own
     unused-instant case documented just above it.
3. **Payload passthrough — reported, not decided**: `build_arudha_lagna_
   profile()`'s return dict includes `"tier"`/`"sources"` keys that
   `DomainChartProfile.payload` doesn't need (tier is domain-derived by
   the formatter, not carried on the profile; sources is a
   `result_formatter.py`-local hardcoded literal, confirmed in the prior
   session's work — `_format_arudha_lagna()` already ignores
   `payload["sources"]`). Checked every existing branch: none of them has
   ever faced this situation — marriage_compatibility/career_strength/
   current_dasha/sade_sati all assemble `payload` inline as exact-keys
   dict literals, and av_transit's `_build_av_timing_block()` helper
   already returns exactly the render-needed keys. **No existing
   "strip meta keys" convention exists.** Per the task's own fallback
   instruction, passed `build_arudha_lagna_profile(chart_data)`'s return
   value through to `payload` UNMODIFIED, with an inline comment flagging
   this explicitly (in case a future exhaustiveness test inspects
   `payload`'s key set and is surprised by the extra 2 keys).
4. **`build_arudha_lagna_profile()`'s docstring**: removed the "NOT yet
   wired into build_domain_profile()/_VALID_DOMAINS/the router or
   formatter" clause (now false — router, formatter, and this file's own
   dispatch are all wired as of Sessions 58-59). Replaced with an accurate
   statement of what's actually still pending: only
   `orchestrator.py`'s `_VALID_DOMAINS` sync, which fails closed via
   `answer_question()`'s defensive `ValueError` until it lands.

Also updated (not separately numbered, but load-bearing for docstring
accuracy): `build_domain_profile()`'s own `Args`/`Raises` docstring
sections now list `"arudha_lagna"` alongside the other 5 domains, document
its `ValueError`/`RuntimeError` failure modes (propagated unmodified from
`build_arudha_lagna_profile()`), and note `evaluated_at_jd` is accepted but
unused for this domain — matching this file's existing convention of
documenting every domain's specific behavior in that shared docstring.

## Diff

```diff
--- a/agent/infra/chart_profile.py
+++ b/agent/infra/chart_profile.py
@@ -68,6 +68,16 @@ _VALID_DOMAINS = {
     # gate was widened to admit it -- fix-forward, Session 55 continued:
     # the branch was unreachable dead code until this entry was added.
     "av_transit",
+    # arudha_lagna (Session 59): this entry lands in the SAME change as
+    # build_domain_profile()'s own arudha_lagna dispatch branch below --
+    # deliberately avoiding a repeat of the exact av_transit incident
+    # documented above. orchestrator.py's own _VALID_DOMAINS does NOT yet
+    # admit "arudha_lagna" -- that sync is a separate, later prompt (same
+    # staged-rollout precedent as av_transit's router-then-orchestrator
+    # split); until it lands, a live "arudha_lagna" route fails closed via
+    # orchestrator.answer_question()'s own defensive ValueError, not a
+    # silent misroute.
+    "arudha_lagna",
 }

 # career_strength's compute_bhava_bala_totals() call needs planet_lons
@@ -438,7 +448,7 @@ def build_domain_profile(

     Args:
         domain: one of "marriage_compatibility", "career_strength",
-            "current_dasha", "sade_sati", "av_transit".
+            "current_dasha", "sade_sati", "av_transit", "arudha_lagna".
         chart_data: calculate_chart() output for the primary native.
         evaluated_at_jd: JD (UT) instant this profile is evaluated as-of.
             Caller-supplied, not sampled here -- must be the SAME instant the
@@ -453,7 +463,12 @@ def build_domain_profile(
             instant is NOT used directly (the scan window is the current
             Antardasha envelope, read from chart_data["dasha"] -- see below);
             it is accepted uniformly across all domains but genuinely unused
-            by this branch.
+            by this branch. For domain="arudha_lagna", this instant is ALSO
+            not used -- Arudha Lagna is a purely natal calculation (birth
+            longitudes only, via build_arudha_lagna_profile()) with no
+            "as-of a different moment" concept of its own, same
+            accepted-uniformly-but-unused precedent as av_transit's case
+            just above.
         partner_chart_data: calculate_chart() output for the second native.
             Required (and only accepted) for domain="marriage_compatibility" --
             Ashtakoot (compute_ashtakoot_compatibility) needs two natives.
@@ -477,12 +492,18 @@ def build_domain_profile(
             the Mahadasha envelope is never silently substituted); or
             transit_planet outside {Saturn, Jupiter, Sun, Mars} (propagated
             unwrapped from av_transit_scanner.scan_av_transit_segments()'s
-            own validation -- not duplicated here).
+            own validation -- not duplicated here); or, for arudha_lagna,
+            a non-canonical lagna_sign or a Scorpio/Aquarius D2 (both
+            co-lords resident)/D6 (exact Step-5(b) tie) fail-closed case,
+            propagated UNMODIFIED from build_arudha_lagna_profile() ->
+            compute_bhava_padas() (not caught or reinterpreted here,
+            matching that function's own documented precedent).
         RuntimeError: a wrapped, module-named failure from any underlying
             calculation call (ashtakoot, mangal_dosha, shadbala_totals,
             compute_porphyry_house_cusps, bhava_bala_totals, sade_sati.
-            compute_sade_sati, ashtakavarga natal-table assembly, or the
-            Moon-longitude ephemeris bridge).
+            compute_sade_sati, ashtakavarga natal-table assembly, the
+            Moon-longitude ephemeris bridge, or arudha_lagna's own planet-
+            longitude ephemeris bridge inside build_arudha_lagna_profile()).
     """
     if domain not in _VALID_DOMAINS:
         raise ValueError(f"domain must be one of {sorted(_VALID_DOMAINS)}, got {domain!r}")
@@ -746,6 +767,41 @@ def build_domain_profile(
         # inherits that same documented drift envelope.
         uncertainty_days = 37.0

+    elif domain == "arudha_lagna":
+        # Session 59: build_arudha_lagna_profile() is a purely natal
+        # calculation (see this function's own evaluated_at_jd Args note
+        # above) -- chart_data only, no evaluated_at_jd argument. Mirrors
+        # sade_sati's own T1, no-stub, no-virupa-envelope convention below
+        # (this domain's payload carries no dated claims, same "tier =
+        # payload property" reasoning documented in the module docstring).
+        #
+        # PAYLOAD PASSTHROUGH (flagged, not silently decided): the returned
+        # dict is assigned to `payload` UNMODIFIED, including its "tier"/
+        # "sources" keys -- keys DomainChartProfile.payload does not need
+        # (tier is decided by the router/formatter from `domain`, not
+        # carried on the profile; sources is a result_formatter.py-local
+        # hardcoded literal per _format_arudha_lagna(), which already
+        # ignores payload["sources"]). No existing branch in this file has
+        # ever faced this situation: every other domain's payload is either
+        # assembled inline as an exact-keys dict literal (marriage_
+        # compatibility/career_strength/current_dasha/sade_sati) or comes
+        # from a helper (_build_av_timing_block()) whose return contract is
+        # already exactly the render-needed keys -- so there is no existing
+        # "strip meta keys" convention to follow here. Passing the extra
+        # keys through unmodified is harmless (result_formatter.py's
+        # _format_arudha_lagna() reads only the 4 keys it needs by name,
+        # direct-indexed) but is called out here rather than silently
+        # stripped, in case a future caller ever inspects payload's key set
+        # directly (e.g. an exhaustiveness test) and is surprised by it.
+        payload = build_arudha_lagna_profile(chart_data)
+        stub_caveats = ()
+        uncertainty_virupa = 0.0
+        # RATIFIED S59 -- formatter's _format_arudha_lagna also asserts 0.0
+        # as a hardcoded contract assertion (payload structurally has no
+        # dated claims); both literals intentional, neither is the other's
+        # source.
+        uncertainty_days = 0.0
+
     else:  # sade_sati (Session 50/P7.2a) -- NO mahadasha/antardasha fields
         # here; this is a payload-property-consistent T1 sub-path, distinct
         # from current_dasha's always-T2 payload (module docstring above).
@@ -815,10 +871,15 @@ def build_arudha_lagna_profile(chart_data: dict) -> dict:
     """Bridge calculate_chart() output -> the Arudha Lagna (AL, house 1)
     entry of jaimini.padas.compute_bhava_padas()'s 12-house result.

-    Standalone builder, NOT yet wired into build_domain_profile()/
-    _VALID_DOMAINS/the router or formatter -- this function only assembles
-    the AL-specific payload; domain/router/formatter integration is a
-    separate, later prompt.
+    Wired into build_domain_profile()'s "arudha_lagna" branch and this
+    file's own _VALID_DOMAINS as of Session 59 (calc_router.py's Stage 1/
+    Stage 2/route branch already landed Session 58; result_formatter.py's
+    _format_arudha_lagna() already landed Session 59). orchestrator.py's
+    own _VALID_DOMAINS does NOT yet admit "arudha_lagna" -- that sync is a
+    separate, later prompt, same staged-rollout precedent as av_transit's
+    router-then-orchestrator split; until it lands, a live "arudha_lagna"
+    route fails closed via orchestrator.answer_question()'s own defensive
+    ValueError, not a silent misroute.

     lagna_sign comes from chart_data["lagna_chart"]["rasi"] (whole-sign
     house 1, same field _koota_natal_info_from_chart already reads for
```

## pytest (full suite)

```
3120 passed, 3 skipped, 1 warning in 75.25s
```

Exact match — zero test flips. Confirmed low-risk before editing: no existing
test asserted `build_domain_profile()` REFUSES on `"arudha_lagna"` via the
old gate.

## Golden harness delta

```
runnable=16 non_runnable_batch=2 match=7 match_stage2=5 design_debt=0 known_gap=4 new_gap=0 error=0
report: diagnostics\golden_scorecard_20260710_170315.md
```

Baseline verification (CLAUDE.md rule #12): confirmed
`golden_scorecard_20260710_164208.md` was the most recent scorecard by
mtime before diffing.

```
$ diff diagnostics/golden_scorecard_20260710_164208.md diagnostics/golden_scorecard_20260710_170315.md
3c3
< - Run evaluated_at_jd: `2461232.1957523148`
---
> - Run evaluated_at_jd: `2461232.2104282407`
```

**Zero delta** beyond the run timestamp, as expected: the router already
routes `arudha_lagna` questions (Session 58), and `orchestrator.py`'s
`_VALID_DOMAINS` still rejects the domain — fail-closed behavior is
unchanged, no golden row's outcome moves.

## Live smoke check beyond pytest (not requested, done anyway — this is the
first point the builder->formatter chain can execute together)

```python
chart = calculate_chart("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")
profile = build_domain_profile("arudha_lagna", chart, jd)
# profile.payload == {'arudha_sign': 'Leo', 'lagna_sign': 'Sagittarius',
#                      'lord': 'Jupiter', 'co_lord_deciding_step': None,
#                      'tier': 'TIER_1_EXACT', 'sources': ('padas.py',)}
# profile.stub_caveats == (); uncertainty_virupa == 0.0; uncertainty_days == 0.0

answer = format_answer(profile)
# answer.tier == TIER_1_EXACT; answer.answer_payload == {'arudha_sign': 'Leo',
#   'lagna_sign': 'Sagittarius', 'lord': 'Jupiter', 'co_lord_deciding_step': None}
# (the extra tier/sources keys from build_arudha_lagna_profile() are present
# on profile.payload but correctly NOT echoed into answer_payload -- confirms
# the "formatter ignores the extra keys" claim in the payload-passthrough
# comment above is actually true, not just asserted)

answer_question("what is my arudha lagna public image", chart)
# -> ValueError: "answer_question: router returned unrecognized domain
#    'arudha_lagna' outside the routable whitelist ['av_transit',
#    'career_strength', 'current_dasha', 'marriage_compatibility',
#    'sade_sati']"
# Confirms the intended end state exactly: router routes it, builder/
# formatter can now fully answer it, orchestrator still fails closed
# until its own _VALID_DOMAINS sync lands (separate, later prompt).
```

## Not touched (deliberately out of scope this session)

- `orchestrator.py`'s own `_VALID_DOMAINS` — explicitly the next, separate
  prompt per this task's own staged-rollout instruction.
- Module-level docstring at the top of `chart_profile.py` ("Covers the 3
  domains locked for the pipeline checkpoint... Plus sade_sati...") does
  not mention av_transit OR arudha_lagna — this staleness predates this
  session (av_transit was never added to that top docstring either) and
  is out of scope for a one-file, dispatch-only prompt; flagged here, not
  fixed.

Not committed — diff above for review. No test file changes this session.

## Follow-up: doc-only fixes (chart_profile.py) + commit

Two stale-docstring fixes, `agent/infra/chart_profile.py` only, no logic
changed:

1. `build_arudha_lagna_profile()`'s docstring claimed `lagna_sign` comes
   from `chart_data["lagna_chart"]["rasi"]` -- verified against the actual
   code (line 932) before writing anything: the real call reads
   `chart_data["lagna_chart"]["ascendant"]`, with an existing inline
   comment (lines 930-931) already explaining `"rasi"` holds the MOON sign
   in that dict, not the Lagna sign. Docstring corrected to match, with an
   explicit "do not regress into the Session 58 lagna-key bug" clause
   (git history: commit `83cae16`, "fix lagna key: ascendant, not rasi",
   part of the Session 58 arudha_lagna profile-builder work).
2. Module top docstring's "Covers the 3 domains..." sentence was flagged
   stale in the prior entry above (never mentioned av_transit or
   arudha_lagna at all, predating this session). Updated to state "Covers
   6 domains as of Session 59" and added a sentence each for av_transit
   and arudha_lagna, matching this file's own convention of documenting
   each domain addition.

Also added to `CLAUDE.md` Carry-Forward: arudha_lagna's payload passes
through meta keys `tier`/`sources` unreconciled -- flagged for whenever
the next Jaimini domain lands (dual tier representation risk: `payload["tier"]`
as a string literal vs. `DomainAnswer.tier`'s `AnswerTier` enum, currently
harmless only because `_format_arudha_lagna()` ignores the payload key).

pytest re-run after both doc fixes: `3120 passed, 3 skipped, 1 warning in
91.19s` -- exact match, confirms doc-only. Golden harness skipped per
instruction (no code path touched).

Commit: `S59: arudha_lagna wired into build_domain_profile dispatch +
chart_profile _VALID_DOMAINS (orchestrator sync pending)` -- hash
`2226691`.
