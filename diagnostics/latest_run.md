# P7 Muhurta wiring, step 4 of 6: router

Session 64. Wires `domain="muhurta_window"` into `agent/infra/calc_router.py`
(Stage 1 keywords + `_route_to_domain()` + Stage 2), plus two ride-alongs.
NOT committed -- design chat ratification pending (same posture as steps 1-3).

## Scope notes flagged before reporting the changes

1. **"ONE FILE: calc_router.py" vs. Change B's actual location.** The
   task's header names one file, but Change B (`_GENERIC_REFUSAL_MESSAGE`
   re-sync) targets constants that live in `result_formatter.py`, not
   `calc_router.py` -- confirmed by grep, no such construct exists in
   the router file. Edited `result_formatter.py` for Change B since
   that's factually where the code is; the "ONE FILE" framing is a
   inconsistency in the task text, not something I could resolve by
   picking a different file.
2. **"Three sanctioned ride-alongs" vs. two enumerated.** The task's
   intro says "Three sanctioned ride-alongs included," but only two are
   actually spelled out (Change B "ride-along 1", Change C "ride-along
   2"). Flagged, not resolved by inventing a third -- implemented
   exactly the two given.
3. **Verification 1's stated premise did not hold** -- see that section
   below; reported honestly rather than forced.

## CHANGE A: domain wiring (calc_router.py)

### A.1 -- removed from `_UNBUILT_MODULE_KEYWORDS`, verbatim

```python
"muhurta": "Muhurta scorer (module exists but is not wired to Q&A in V1)",
```

Also rewrote the block's leading comment (previously explained exactly
this entry's special-casing -- necessarily stale once removed) with a
new paragraph matching the existing "sade sati REMOVED"/"jaimini
removed" precedent style.

### A.2 -- collision check (programmatic, not just inspection)

Ran a script exercising the router's OWN `_normalize_tokens`/
`_keyword_hits` logic (not just eyeballing strings) against every
existing keyword source: `_MARRIAGE_KEYWORDS`, `_CAREER_KEYWORDS`,
`_DASHA_KEYWORDS`, `_AV_TRANSIT_KEYWORDS`, `_ARUDHA_LAGNA_KEYWORDS`,
`_UPAPADA_LAGNA_KEYWORDS`, `_STEM_MAP` (keys and values),
`_UNBUILT_MODULE_KEYWORDS` (post-muhurta-removal), `_OUT_OF_SCOPE_KEYWORDS`,
`_BUILT_MODULE_FASTPATH`, against the 5 proposed new keywords (`muhurta`,
`mahurat`, `auspicious`, `shubh`, `electional`):

```
=== Direct substring collision check (both directions, raw strings) ===
No direct substring collisions found.

=== Simulated _keyword_hits cross-check ===
normalized new-keyword tokens: ['muhurta', 'mahurat', 'auspicious', 'shubh', 'electional']
No _keyword_hits-simulated collisions found.
```

**Result: CLEAR.** Proceeded to wire.

Added:
```python
_MUHURTA_WINDOW_KEYWORDS: tuple[str, ...] = (
    "muhurta", "mahurat", "auspicious", "shubh", "electional",
)
```
and `"muhurta_window": _MUHURTA_WINDOW_KEYWORDS` to `_DOMAIN_KEYWORDS`.

### A.3 -- `_route_to_domain()` muhurta_window branch

```python
    if domain == "muhurta_window":
        return RouteResult(
            domain="muhurta_window",
            tier=AnswerTier.TIER_3_MUHURTA,
            confidence=confidence,
            demotion_reason=None,
            requires_partner=False,
            route=route,
        )
```
(Full in-file comment covers the T3 rationale, the demotion-lock
posture matching av_transit's branch, and the staged-rollout note --
longer than shown here.) Inserted directly ABOVE the `current_dasha`
branch (itself now converted from an implicit fallthrough to an
explicit `if domain == "current_dasha":` -- see Change C).

### A.4 -- Stage 2 wiring

`_STAGE2_VALID_DOMAINS` gained `"muhurta_window"` (8 entries + "none").

`_STAGE2_SYSTEM_PROMPT` gained a new gloss bullet:

```
- muhurta_window: Muhurta (electional astrology) -- finding a favorable/
auspicious time-WINDOW, in the near future, to START or DO a specific
action or event (a composite of Chandrabala, Tarabala, and Panchaka over
a short scan). Layman: picking a good/auspicious time to begin something.
Examples: "when is a good time to start something new", "what is an
auspicious muhurta for me this week", "shubh muhurat for starting my
business", "is this a good day to sign the papers". Muhurta is
ELECTIONAL -- choosing WHEN, in the near future, to DO something -- and
must NEVER be confused with NATAL-timing questions about a life period
or a transit already in progress: "when will my bad time end" or "what
phase of life am I in" is current_dasha, NOT muhurta_window; "how is
[planet]'s transit playing out right now" is av_transit, NOT
muhurta_window; and "when will I get a job" asks when a future life
EVENT will happen TO the person (current_dasha/natal-timing territory),
NOT when to ACT (muhurta_window) -- even though all of these questions
use the word "when". The deciding question: is the person asking to
PICK a moment to act (muhurta_window), or asking WHEN something already
in motion (a period, a transit, a life event) will happen or change
(current_dasha / av_transit)?
```

Also fixed the domain-count text in the same prompt block: "exactly 7
domains" -> 8, "one of these 7 things" -> 8, `_STAGE2_TOOL_SCHEMA`'s
description "7 routable domains" -> 8. Additionally corrected an
adjacent PRE-EXISTING staleness while editing the same sentence: the
confidence-instruction line said "6 domains above" even before this
change (already wrong -- there were 7) -- fixed to "8" rather than left
doubly wrong, since I was rewriting this exact sentence anyway (not a
separate ride-along; matches the "opportunistic fix while touching the
same text" precedent Session 58 already established for the tool-schema
count).

## CHANGE B: `_GENERIC_REFUSAL_MESSAGE` / `_REFUSAL_USER_MESSAGES` re-sync (result_formatter.py)

Old `_REFUSAL_USER_MESSAGES["question not classifiable with confidence"]`:
```
"I couldn't confidently tell what you're asking. Could you try
rephrasing? I can help with questions about: marriage compatibility,
career strength, the life period (dasha) you're currently in, Sade Sati
(Saturn's roughly 7.5-year transit around your Moon sign), how a
specific planet's transit is playing out right now, your public
image/reputation, and your Upapada Lagna (a marriage indicator read
from your own chart)."
```
New (added muhurta clause, replaced "and" with ", and" list continuation):
```
"... your public image/reputation, your Upapada Lagna (a marriage
indicator read from your own chart), and picking an auspicious time
(Muhurta) to start something."
```

Old `_GENERIC_REFUSAL_MESSAGE`:
```
"I'm not able to answer that confidently. Could you try rephrasing your
question, or ask about marriage compatibility, career strength, your
current dasha, Sade Sati (Saturn's roughly 7.5-year transit around your
Moon sign), transit timing, your public image, or your Upapada Lagna (a
marriage indicator read from your own chart)?"
```
New:
```
"... transit timing, your public image, your Upapada Lagna (a marriage
indicator read from your own chart), or picking an auspicious time
(Muhurta) to start something?"
```

`SENSITIVE_TO` guard comment's frozen domain-set snapshot updated:
`{marriage_compatibility, career_strength, current_dasha, sade_sati,
av_transit, arudha_lagna, upapada_lagna}` -> same set + `muhurta_window`,
with a note recording this Session 64 re-sync explicitly (matching the
comment's own precedent of recording each prior re-sync).

## CHANGE C: `_route_to_domain()` fail-closed refactor

Diff (structural; full comments in-file are longer):

```python
-    # current_dasha -- ALWAYS TIER_2_RANGE in V1 (...)
-    if chart_data is None or _near_dasha_boundary(chart_data):
-        demotion_reason = _DASHA_DEMOTION_REASON_NEAR_BOUNDARY
-    else:
-        demotion_reason = _DASHA_DEMOTION_REASON
-    return RouteResult(
-        domain="current_dasha",
-        ...
-    )
+    if domain == "current_dasha":
+        # current_dasha -- ALWAYS TIER_2_RANGE in V1 (...)
+        if chart_data is None or _near_dasha_boundary(chart_data):
+            demotion_reason = _DASHA_DEMOTION_REASON_NEAR_BOUNDARY
+        else:
+            demotion_reason = _DASHA_DEMOTION_REASON
+        return RouteResult(
+            domain="current_dasha",
+            ...
+        )
+
+    raise ValueError(f"calc_router._route_to_domain: unknown domain {domain!r}")
```

Kept this function's own established idiom (sequential `if ... return`
blocks, not literal `elif`/`else` keywords) rather than converting every
prior branch to `elif` -- functionally identical, since every earlier
branch already returns unconditionally, making the sequential-`if`
pattern and a true `elif` chain behaviorally equivalent here. The new
trailing `raise` is the only genuinely new control-flow node: any domain
string not explicitly branched now fails loudly, naming itself, instead
of silently mis-routing to `current_dasha` (the exact trap arudha_lagna's
own branch comment already flagged as a workaround, and upapada_lagna's
branch comment flagged again -- this closes the underlying pattern for
good, not just for those two).

## VERIFICATION 1: full pytest suite

```
python -m pytest -q
3134 passed, 3 skipped, 0 failed  (110.86s)
```

**The task's stated expectation ("any test asserting the 'muhurta'
unbuilt-keyword REFUSAL... will fail") did NOT hold.** Searched the full
test suite for any test asserting on the `"muhurta"` unbuilt-keyword
REFUSAL path specifically (grepped for `"Muhurta scorer"`, `"not wired to
Q&A"`, and `route_question(...muhurta...)` calls) and found none. The
`test_calc_router_stage2.py` "yogini-substitution" comment the task cited
as evidence is about a DIFFERENT, unrelated prior substitution
(`ashtakavarga` -> `yogini`, Session 55) -- its existence does not imply a
muhurta-specific test exists. Reporting this discrepancy directly rather
than manufacturing a failure to match the prediction, or silently
pretending it was correct.

## VERIFICATION 2: 12-phrasing layman reachability probe

Standing directive (CLAUDE.md): mandatory after any Stage 2 prompt
change. Located the most recent committed run of this exact probe via
`git log` (commit `c93fc44`, "S65 upapada_lagna router wiring +
reachability probe" -- the task calls this "the S63... baseline"; the
task's session-numbering and the commit-message numbering appear to have
drifted relative to each other, same class of discrepancy CLAUDE.md's
own "Session 56->57 baseline discrepancy" carry-forward already
documents. Used the most recent actual committed table regardless of the
label mismatch, since that is the correct pre-edit state to diff
against.) Re-ran the identical 12 questions, same order, same
chart_data-only-for-dasha-rows convention (rows 7-8), live OpenAI
client:

| # | question | baseline (pre-edit, committed) | this run (post-edit) | changed? |
|---|---|---|---|---|
| 1 | how do people see me in public | arudha_lagna/high/TIER_1_EXACT | arudha_lagna/high/TIER_1_EXACT | no |
| 2 | what is my public reputation | arudha_lagna/high/TIER_1_EXACT | arudha_lagna/high/TIER_1_EXACT | no |
| 3 | will I be famous | None/high/REFUSAL | None/high/REFUSAL | no |
| 4 | what impression do I make on others | arudha_lagna/high/TIER_1_EXACT | arudha_lagna/high/TIER_1_EXACT | no |
| 5 | should I change my job this year | career_strength/high/TIER_2_RANGE | career_strength/high/TIER_2_RANGE | no |
| 6 | is my career going anywhere | career_strength/high/TIER_2_RANGE | career_strength/high/TIER_2_RANGE | no |
| 7 | what phase of life am I in right now | current_dasha/high/TIER_2_RANGE | current_dasha/high/TIER_2_RANGE | no |
| 8 | when will my bad time end | current_dasha/high/TIER_2_RANGE | current_dasha/high/TIER_2_RANGE | no |
| 9 | will my marriage be happy | marriage_compatibility/high/REFUSAL (partner guard) | REFUSAL (partner guard) | no |
| 10 | are we compatible | marriage_compatibility/high/REFUSAL (partner guard) | REFUSAL (partner guard) | no |
| 11 | what do the stars say about me | None/high/REFUSAL | None/high/REFUSAL | no |
| 12 | tell me my future | None/high/REFUSAL | None/high/REFUSAL | no |

**All 12 rows unchanged.** Confirms the muhurta Stage 2 gloss addition
and keyword wiring did not perturb any other domain's classification.
Raw per-row output (this run, verbatim):

```
1 | how do people see me in public | domain=arudha_lagna tier=TIER_1_EXACT confidence=1.000 route=stage2
2 | what is my public reputation | domain=arudha_lagna tier=TIER_1_EXACT confidence=1.000 route=stage2
3 | will I be famous | domain=None tier=REFUSAL confidence=0.000 route=stage2 demotion_reason='question not classifiable with confidence'
4 | what impression do I make on others | domain=arudha_lagna tier=TIER_1_EXACT confidence=1.000 route=stage2
5 | should I change my job this year | domain=career_strength tier=TIER_2_RANGE confidence=1.000 route=stage2
6 | is my career going anywhere | domain=career_strength tier=TIER_2_RANGE confidence=1.000 route=stage2
7 | what phase of life am I in right now | domain=current_dasha tier=TIER_2_RANGE confidence=1.000 route=stage2
8 | when will my bad time end | domain=current_dasha tier=TIER_2_RANGE confidence=1.000 route=stage2
9 | will my marriage be happy | domain=None tier=REFUSAL confidence=0.000 route=stage2 demotion_reason='marriage_compatibility requires partner birth data'
10 | are we compatible | domain=None tier=REFUSAL confidence=0.000 route=stage2 demotion_reason='marriage_compatibility requires partner birth data'
11 | what do the stars say about me | domain=None tier=REFUSAL confidence=0.000 route=stage2 demotion_reason='question not classifiable with confidence'
12 | tell me my future | domain=None tier=REFUSAL confidence=0.000 route=stage2 demotion_reason='question not classifiable with confidence'
```

`diagnostics/calc_router_stage2.log` grew by 12 entries this run
(gitignored, not committed).

## VERIFICATION 3: live smoke test -- muhurta routing + fail-closed answer_question

```python
route_question("what is an auspicious muhurta for me this week",
                has_partner_data=False, chart_data=<sulabh chart>)
```
```
RouteResult:
  domain: muhurta_window
  tier: AnswerTier.TIER_3_MUHURTA
  confidence: 0.6666666666666666
  demotion_reason: None
  requires_partner: False
  route: stage1
```

Resolved entirely at **Stage 1** -- both "auspicious" and "muhurta"
match (2/3 = 0.667), clearing the 0.4 floor and the 0.15 margin without
needing Stage 2 at all.

```python
answer_question("what is an auspicious muhurta for me this week", <sulabh chart>)
```
```
ValueError: answer_question: router returned unrecognized domain
'muhurta_window' outside the routable whitelist ['arudha_lagna',
'av_transit', 'career_strength', 'current_dasha',
'marriage_compatibility', 'sade_sati', 'upapada_lagna']
```

Confirmed: fails closed exactly as expected. `orchestrator.py`'s own
`_VALID_DOMAINS` does not yet admit `"muhurta_window"` -- that sync is
step 5.

## Not committed

Per constraint: `agent/infra/calc_router.py` and
`agent/infra/result_formatter.py` (Change B) both remain uncommitted in
the working tree. Design chat ratifies before any commit -- test repairs
(if any are ultimately deemed necessary, though Verification 1 found
none required) land first per the task's own ordering.
