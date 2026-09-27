"""
agent/astro/house_roles.py
KP house-ROLE doctrine -> per-house weights for the timing ranker (S145).

WHY THIS EXISTS (S145, ratified in design chat):
  The planner emits a FLAT target-house list that mixes houses of different
  roles. For marriage it emits [2,7,8,11] (planner.py SYSTEM_PROMPT injects the
  8th as "mangalya"). The S144 ranker scored every target house identically, so
  a dasha lord signifying the 8th -- an obstacle house, NOT a KP marriage house
  -- earned the same marriage-timing credit as one signifying the 7th. That
  inflated runner-up windows (HANDOVER S145, Task 1).

  The clean fix is to weight each house by its ROLE in the domain: promotion
  houses score positively, obstacle/negation houses score zero (they neither
  reward nor -- yet -- penalise). This module holds that role->weight doctrine.

WHY IT IS NOT A PLANNER TABLE (the S124 lock):
  planner.py forbids a domain->house table: WHICH houses to examine is
  contextual LLM reasoning (bhavat-bhavam, widening), not a lookup. But the
  ROLE OF A HOUSE WITHIN A CHOSEN DOMAIN is FIXED CLASSICAL DOCTRINE -- 2/7/11
  always promote marriage, chart-independent -- exactly like the significator
  method hardcoded in calculations/kp/significator_engine.py. So role doctrine
  lives HERE, ranker-side, not in the planner. The planner is untouched; it
  still selects houses contextually. This module only *labels* the houses it
  already chose. The ranker itself stays domain-neutral (timing_ranker.py): it
  scores a weight map and never learns the word "marriage".

SCOPE (S145): MARRIAGE ONLY. Every other domain returns all-promotion weights,
  which makes the ranker byte-identical to its pre-S145 flat-set behaviour.
  Career/children targets are UNVALIDATED (only one ground-truth chart exists --
  Sulabh's marriage, 11 Dec 2019) and are deliberately left untouched until each
  has its own reference chart. Do NOT add a domain here without ground truth.

SOURCES (K-P-Reader-2, in data/pdfs/.../K-P-Reader-2_djvu.txt):
  - promotion {2,7,11}: "Houses 2, 7 and 11 are considered for marriage"
    (line ~12763; the significator method, lines ~13506-13518).
  - negation {1,6,10}: "12th house to any bhava is the negation of the Bhava"
    (line ~2871) applied to each promotion house -> 12th-from-2=1, 12th-from-7=6,
    12th-from-11=10.
  - obstacle {8}: mangalya / longevity-of-union (BPHS 8th = 2nd-from-7th). Absent
    from the KP marriage house-group, hence irrelevant to marriage ONSET timing.

Python 3.11.
"""
from __future__ import annotations

from typing import Iterable

# THRESHOLD DISCIPLINE (project rule: justification + scope guard + tuning note).
#   PROMOTION = 1.0  -- baseline. Equals the implicit weight every target house
#     carried in the S144 flat-set ranker, so a plan with only promotion houses
#     scores byte-identically to pre-S145.
#   OBSTACLE / NEGATION = 0.0  -- DROP semantics, NOT a penalty. A significator
#     hit on such a house contributes nothing to the marriage-timing score, which
#     removes the S144 inflation without introducing a tuning knob.
#   WHY ZERO AND NOT NEGATIVE: a negative weight is a tunable lever, and there is
#     exactly ONE marriage ground-truth chart. Tuning a lever on N=1 is forbidden
#     (SAMPLE-before-SCALE / THRESHOLD DISCIPLINE). Zero is the conservative,
#     defensible first step: it cannot change the #1 window (which scores on
#     promotion houses) and only strips spurious credit from runner-ups.
#   TUNING NOTE: negation houses (1,6,10 = loss/separation of the union) are
#     doctrinally a genuine NEGATIVE for marriage onset. Moving them below zero is
#     a real enhancement, but ONLY after >1 reference chart shows the current zero
#     under-penalising. The ranker's scoring is already weight-additive, so this
#     becomes a one-line change here plus a recorded justification -- no ranker or
#     interpreter edit. Do not make it on the marriage chart alone.
PROMOTION = 1.0
NEUTRALISED = 0.0  # obstacle + negation, "dropped" via zero weight

# domain -> {house: weight}. MARRIAGE ONLY (scope guard above).
MARRIAGE_ROLES: dict[int, float] = {
    2: PROMOTION, 7: PROMOTION, 11: PROMOTION,   # promotion (KP marriage group)
    1: NEUTRALISED, 6: NEUTRALISED, 10: NEUTRALISED,  # negation (12th-from group)
    8: NEUTRALISED,                               # obstacle (mangalya, not KP-marriage)
}

DOMAIN_ROLES: dict[str, dict[int, float]] = {
    "marriage": MARRIAGE_ROLES,
}


def weighted_targets(
    domains: Iterable[str] | None,
    houses: Iterable[int] | None,
) -> dict[int, float]:
    """Map the planner's flat target houses to role weights.

    Returns {house: weight}. The ranker consumes this dict directly.

    SCOPE GUARD: if NONE of the planned domains has a role map (i.e. anything
    other than marriage today), every house gets weight PROMOTION (1.0) and the
    ranker behaves exactly as the pre-S145 flat-set version -- no unvalidated
    domain is ever re-weighted.

    FAIL-SAFE: a house present in `houses` but not classified by any applicable
    role map keeps weight PROMOTION (1.0). We never silently zero a house the
    doctrine does not explicitly demote -- that would be narrowing.

    MULTI-DOMAIN: when several planned domains carry role maps, a house takes the
    MAX weight any of them assigns. Rationale: a house that is an obstacle for one
    domain but a promotion house for another (e.g. the 8th -- obstacle for
    marriage, promotion for longevity) must not be zeroed on account of the
    stricter domain. MAX is the widen-not-narrow choice and is forward-correct as
    more domains are added. (Moot today: marriage is the only mapped domain.)
    """
    house_list = [int(h) for h in (houses or [])]
    maps = [DOMAIN_ROLES[d] for d in (domains or []) if d in DOMAIN_ROLES]

    if not maps:  # SCOPE GUARD: unmapped domains -> pre-S145 behaviour
        return {h: PROMOTION for h in house_list}

    out: dict[int, float] = {}
    for h in house_list:
        weights = [m[h] for m in maps if h in m]
        out[h] = max(weights) if weights else PROMOTION  # FAIL-SAFE keep
    return out
