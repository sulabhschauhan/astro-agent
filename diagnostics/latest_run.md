# S119 Step 3 — decline/jurisdiction sourced from SURVIVING RULES, not post-drop claims

DECISION THIS SERVES: if the jurisdiction set is sourced from survivors rather
than from produced claims, then a feature whose doctrine fired can never be
falsely declined as "not addressed" — regardless of what happens downstream of
resolve_priority; else the M2 side-effect can silently return. Result: sourced
from survivors, proven discriminating.

## Verification at HEAD (f9383d4/d8afa13, wip/interpretive-pilot) — before editing

**`_prepare_deterministic_prep`** — `claims, engine_diagnostics =
_prepare_claims_from_rules(...)` is the only thing it receives from the engine;
the surviving rules themselves never crossed that boundary. The set was
`features_with_surviving_rule_claims = {c.feature for c in claims}` (line 2328),
and it fed **three** consumers, all from that one assignment:
1. `supported_features` narrowing,
2. `unsupported_features` narrowing (this is the one the decline reads),
3. `PalmReadingPrep.rule_claim_features`.

**`_compute_decline_features`** — confirmed: it declines (a) everything in
`unsupported_features`, (b) extraction-failed features, (c) gate-SUPPORTED
features with zero/all-excluded claims. Join key is the plain feature string.
The jurisdiction narrowing is indeed the mechanism meant to keep rule-fired
features out — and because the narrowing removes them from BOTH tuples, a
rule-fired feature is exempt from branch (a) and branch (c) alike.

**Feature-token identity** — confirmed 1:1: survivors map through
`rule_to_claim._feature_for_topic_group` (the same `_TOPIC_GROUP_TO_FEATURE`
table, same fail-closed `ValueError`) that `Claim.feature` already goes through.
Survivor-sourced and claim-sourced tokens are the same vocabulary, not two.

## Implemented (surgical, 2 files)

The survivors live inside `_prepare_claims_from_rules` and were not exposed, so
the change is in two halves:

1. **`_prepare_claims_from_rules`** — computes `surviving_rule_features` at the
   survivors site, INSIDE fail-closed boundary 4. Deliberate: an unmapped
   `topic_group` now fails exactly the way it already did (`claims_from_rules`
   raises the same `ValueError` from the same lookup on the same rule), so this
   adds no new failure mode. Published as
   `engine_diagnostics["surviving_rule_features"]` (sorted, JSON-safe).
   Added to `_fail_closed`'s dict too, so the key is present on **every** return
   path — all 4 failure paths and the success path.
2. **`_prepare_deterministic_prep`** — `features_with_surviving_rule_claims` now
   reads that key. Indexed **directly**, not `.get()`-defaulted: a future return
   path that forgot the key would raise loudly rather than silently produce an
   empty set, which is precisely how the false decline would creep back.

Both tuple narrowings and `rule_claim_features` read that one assignment, so all
three consumers moved together by construction — no second edit site.

The comment block records the invariant it enforces: **jurisdiction belongs to a
feature whose doctrine FIRED, not to a feature that happened to survive claim
construction.** A future survivor→claim gap can cost a claim; it can no longer
turn fired doctrine into a false "not addressed."

NOT touched, per scope: needles, capture net (Step 4), sources (Step 5), the
S118 censor, resolve logic, `_apply_support_gate`'s own scoring.

## The false-decline fix, proven

Reconstructed deterministically (no live call) in the S117/S120 David-hand shape:
retrieval is fed head-line text only, so the gate has nothing for the fate line
and would classify it UNSUPPORTED → declined. A fate rule fires anyway:

```
fired_rule_ids:           ['FT_011']
surviving_rule_ids:       ['FT_011']
surviving_rule_features:  ['fate line']
fate line in unsupported_features:   False
fate line in supported_features:     False
fate line in decline_features:       False
```

Fate is the right feature to prove this on: the Step-0 audit found **every** rule
in the fate file unresolvable (source_page 103–105, no non-empty chunk on any of
them), so fate line is where the false decline was actually observed —
"the texts do not clearly address your fate line" while 13 fate rules had fired.

**The change is discriminating, not decorative — measured, not asserted.** With
the source line temporarily reverted to `{c.feature for c in claims}`, test (4)
FAILS and the other four pass; restored, all five pass. So tests 1–3 prove
behavior-preservation today, and test 4 is the one that actually pins the
robustness gain. (Temporary revert run and restored in-session; no artifact left
behind.)

## Tests — 5 added, 0 existing changed

`tests/interpretive/test_palm_reading_rules_engine.py`, diff **+212/-0**.

1. `test_fired_and_surviving_fate_rule_is_not_falsely_declined` — HARDEST CASE,
   the production shape above: fate line in neither tuple, not in the decline set.
2. `test_feature_with_no_surviving_rule_is_still_declined` — REGRESSION guard: a
   fate line contributing only an *unmapped* quality is still declined exactly as
   before, while the head line that did fire stays exempt. This step does not
   weaken honest decline.
3. `test_survivor_sourced_set_equals_claim_sourced_set_on_a_multi_feature_run` —
   INVARIANT: the two derivations agree exactly, asserted across **two** features
   (with an explicit `len(...) > 1` guard so a single-rule run cannot satisfy it
   trivially).
4. `test_survivor_with_no_claim_is_still_exempt_from_decline` — ROBUSTNESS, the
   reason this step exists. Simulates precisely what the pre-Step-2 code did for
   13 of 99 rules: rule fires, survives, produces no claim. It records the
   survivor ids that actually reached the bridge first, so the test cannot pass
   vacuously on an empty survivor list. The claim is genuinely gone
   (`prep.claims == ()`) and the feature is STILL exempt.
5. `test_engine_failure_reports_an_empty_surviving_feature_set` — the key is
   present on the fail-closed path too, and yields the same empty set the old
   code produced there.

**No existing test needed changing.** The change is behavior-preserving on every
path the suite already covered — which is the expected outcome given Step 2
guarantees survivor→claim, and is itself evidence the edit is correctly scoped.

## Verification
- `python -m pytest -q` -> **3708 passed, 7 skipped**. Step-2 baseline 3703/7;
  +5 = 3708. **Zero regressions.**
- `python scripts/gate_rule_citations.py` -> `NOT_FOUND_ANYWHERE: 0` (99 live,
  16 parked).
- Files touched: exactly 2 (`palm_reading.py` +56/-11, of which the only logic
  lines are the `surviving_rule_features` computation, its two diagnostics
  entries, and the 3-line consumer swap — the rest is comment; and
  `test_palm_reading_rules_engine.py` +212/-0). No unrelated staging.

## Note for later steps
`engine_diagnostics` gains one key (`surviving_rule_features`). It is additive
and every existing consumer is `.get()`-based (`frontend/app.py`'s diagnostics
formatter, the S83 capture net), so nothing needed a change here — but Step 4
may want to surface it alongside `surviving_rule_ids` in the dogfood capture,
since it is now the authoritative jurisdiction record.

## Commit
`46573c4` — pushed to `origin/wip/interpretive-pilot`. Staged: ONLY `agent/interpretive/palm_reading.py` and `tests/interpretive/test_palm_reading_rules_engine.py`.
