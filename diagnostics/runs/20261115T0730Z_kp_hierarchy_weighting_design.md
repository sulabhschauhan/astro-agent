# Stage 1 (real): KP-hierarchy-weighted significator term — design record

Doctrine-sourced, frozen from citation. NO tuning on Sulabh's events. Built, not
proposed. This file records the sources and the 8-agent roster review.

## What changes
The timing ranker's significator term currently scores every signified target house
flat (`W_SIG × count`). KP doctrine ranks significators by HOW a planet signifies a
house. The engine already computes that rank (tier 1-4); the fact composer flattened
it away ("a v2 upgrade", kp_significator_facts.py docstring). This surfaces the tier
and weights the significator term by it.

## Doctrine (sourced — order only; the weights are an ordinal model, not a cited number)
KP four-fold significator strength, strongest→weakest (K.S. Krishnamurti, KP Reader II;
already cited in significator_engine.py):
  tier 1  star_of_occupant   — a planet in the STAR (nakshatra) of a house's occupant
  tier 2  occupant           — a planet sitting IN the house
  tier 3  star_of_owner      — a planet in the star of the house's owner
  tier 4  owner              — the house lord itself (weakest)
Corroborating legitimate sources (web, 15 Nov 2026):
  - "Planets in the star of a significator are stronger than the significator itself —
     a hallmark KP rule." (ishvaram KP, roxyapi KP guide)
  - "Level 1 Occupants (strongest) … Level 4 star-lord of the sign lord (weakest);
     higher levels always take priority." (panchangbodh KP significator)
  - "The lord of the house is the WEAKEST significator in the KP hierarchy." (roxyapi)
Node agency (Rahu/Ketu conjunction + dispositor routes) is emitted tier=None by the
engine and is doctrinally contested (KP Reader IV gives no closed ordering).

## The weight ladder (ordinal, frozen)
  tier 1 → 1.00,  tier 2 → 0.75,  tier 3 → 0.50,  tier 4 → 0.25
  tier None (node) → 0.25  (floored at the weakest classical tier)
  no tier info     → 1.00  (fail-soft: byte-identical to the pre-change flat model)
JUSTIFICATION: tier 1 anchored at 1.0 so a strongest-tier signification scores exactly
as the old flat model did — weaker tiers only scale DOWN, so nothing inflates. Equal
0.25 steps are the MINIMAL model of a known rank-order with unknown gaps (the texts
rank, they do not quantify); this is an explicit modeling choice, NOT attributed to a
page. SCOPE GUARD: multiplier ∈ [0.25, 1.0], monotonic; node floor never exceeds a real
significator. TUNING NOTE: the step spacing is the one free parameter — change it only
on a multi-chart back-test, NEVER on Sulabh's events.

## 8-agent roster review (surfacing only what was raised)
- Architect — PASS. Single source: tiers come from significator_engine via a new
  kp_significator_facts key; the ranker reads facts, never recomputes KP. Failure mode:
  tiers absent → flat (byte-identical). Does NOT touch _fact_block / FACT_BLOCK_PROVIDES
  (the tier map is consumed by the ranker, not rendered), so the growth-contract pin is
  untouched.
- Critic — PASS w/ note. Node (tier None) weight is contested → floored at 0.25, never
  dominates. Equal-step ladder flagged as a modeling choice (threshold discipline:
  justification + scope guard + tuning note above). Weights derived doctrine-first, not
  fitted to events.
- QA — PASS. Tests: descending tier → descending weight; absent tiers → byte-identical;
  facts composer carries tiers without breaking the flat tuple; strong-tier lord
  outranks weak-tier lord at equal house-count. Malformed tiers → flat fallback.
- UI/UX — PASS. Tier never enters the rendered "why"/output (no KP jargon leak); it only
  moves the SCORE. Reported sig_hits unchanged.
- Ephemeris Auditor — PASS. No new astronomical input. Tiers inherit the engine's known
  cusp-boundary sensitivity (Lahiri-vs-KP ayanamsha, already flagged via
  boundary_warnings); the weighting neither worsens nor fixes it.
- Validation Source — PASS w/ note. ORDER is cited (Reader II, in the engine). The
  NUMBERS are an explicit ordinal model, NOT a cited quantity — recorded as such, no page
  fabricated. No oracle value is a calculation input. Not validated on one chart (weights
  are doctrine-frozen, not chart-tuned).
- Business — PASS. Zero cost/latency (arithmetic over already-computed data).
- Debate — no hard conflict; Critic/Validation-Source objections satisfied by the scope
  guards + documentation above.

## Scope held
Only the AD-lord significator term is tier-weighted (the hand-trace showed this is the
discriminating signal). MD support stays boolean, transit terms unchanged — grading
those (SAV / Shadbala) is the separate, later stage. No new additive signal (handover A2
lock honoured).

## Validation status
Pure-logic weighting validated in-container (no swisseph). The real-chart effect
(does Venus-Feb2012 climb) needs a swisseph run on Sulabh's machine + a re-baseline on
the CORRECTED first-job date (Feb 2012, not the Feb-2011 row in the current baseline).
