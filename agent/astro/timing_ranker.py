"""
agent/astro/timing_ranker.py
Deterministic timing-window ranker (S144; role-weighted targets S145).

WHY: the interpreter, handed dasha + KP-significator + transit facts, ranked
them inconsistently (3 live runs -> 3 different top picks) and used
significators as post-hoc justification for whichever window it drifted to.
A timing pick must be DETERMINISTIC and derived, not narrated. This module
computes a convergence score per antardasha in Python; the interpreter's job
shrinks to EXPLAINING the top window, not choosing it.

DOMAIN-NEUTRAL: the ranker knows nothing about "marriage" / "career" /
"children". It scores each sub-period against a TARGET-HOUSE SET passed in by
the caller (the planner already emits it, e.g. [7,2,11] for marriage,
[10,6,2,11] for career). One function, every life area; a life area we never
coded works as long as the planner supplies its houses.

S145 -- ROLE-WEIGHTED TARGETS. `target_houses` may now be either:
  * a set/list of ints  -> every house weight 1.0 (UNCHANGED pre-S145 behaviour), or
  * a dict {house: weight} -> houses scored by weight, so an obstacle/negation
    house handed in at weight 0.0 contributes nothing.
The weights come from agent.astro.house_roles (marriage-only today); the ranker
stays domain-neutral and merely honours whatever weights it is given. With all
weights 1.0 the scoring is byte-identical to S144. A house at weight 0.0 is
"dropped": it is still a valid target (so a lord may still match it) but adds
nothing to the score and is not reported as a hit. The math is fully additive,
so a future negative weight (a penalising house) needs no code change here.

THE FOUR SIGNALS (all already computed elsewhere; this only scores them):
  1. significator convergence -- does the ANTARDASHA lord signify a target
     house (KP, agent.calculations.kp.significator_engine)?  [+W_SIG * weight each]
  2. mahadasha theme -- does the MD lord signify a POSITIVE-weight target house?  [+W_MD]
  3. transit corroboration -- does transiting Saturn CONTACT a positive-weight
     target house during the sub-period?  [+W_ACT]
  4. Saturn RETURN -- Saturn transiting its OWN natal house whose natal position
     contacts a positive-weight target house.  [+W_RET]

WEIGHTS (THRESHOLD DISCIPLINE -- justified independently of any chart's
"right" answer; NEVER tune these so a particular window wins):
  W_SIG 1.0  -- each target house the AD lord signifies is a first-order KP
                timing signal; count-based (now weight-scaled), so a lord
                touching two promotion houses outranks one touching a single one.
  W_MD  0.5  -- the MD sets the standing theme; corroboration, not the driver.
                Half-weight so it never overrides the AD-level signal, and it
                is constant within one MD so it cannot distort intra-MD order.
  W_ACT 1.0  -- a slow-planet transit contacting a target house is the
                classical dasha-transit cross-check; on par with one
                significator hit.
  W_RET 2.0  -- a Saturn return (own natal house) re-activating its natal
                contact on a target house is milestone-grade. W_RET > W_ACT
                because a return is categorically rarer/stronger than a passing
                aspect -- a first-principles ordering, not a fit to any answer.
                SCOPE GUARD: fires only when the natal Saturn position actually
                contacts a POSITIVE-weight target house, so it can never reward an
                astrologically irrelevant return.
  TUNING NOTE: W_RET is the pivotal weight. If more reference charts show a
  return over-/under-weighted, adjust HERE with a recorded justification -- do
  not add per-scenario logic in the interpreter prompt.

TRANSIT SCOPE: Saturn AND Jupiter. Saturn carries the 3rd/7th/10th aspects,
its Sade-Sati phase and the return bonus; Jupiter (the natural marriage/
children benefic) carries its 5th/7th/9th aspects as a positive activation
(W_JUP). Both come from build_transit_facts's per-antardasha snapshot. Other
transiting bodies are not yet scored.

Python 3.11.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

W_SIG = 1.0
W_MD = 0.5
W_ACT = 1.0
W_RET = 2.0
W_JUP = 1.0    # Jupiter transit (the natural marriage/children benefic) contacting a
               # target house -- a first-order positive activation, symmetric to
               # Saturn's W_ACT. No return concept (Jupiter's 12-yr cycle is not
               # emphasized the way a Saturn return is). SCOPE: benefic-contact only.
               #
               # S145 DECISION (Task 2b -- Jupiter-transit depth): DEFERRED, by
               # design, not oversight. Jupiter stays CONTACT-only (5th/7th/9th
               # aspects). No Jupiter return/phase bonus is added because:
               #   - classical weight: the Jupiter return (~12 yr) is not a
               #     milestone trigger the way the ~29.5-yr Saturn return is; giving
               #     it a W_RET-style bonus would overstate a common, recurring event;
               #   - discipline: a new weight is a tuning knob, and there is one
               #     marriage ground-truth chart -- adding it now would tune on N=1.
               # TUNING NOTE: revisit ONLY with >1 reference chart where a Jupiter
               # phase demonstrably improves ranking; add as a separate weight with
               # its own justification, never by inflating W_JUP.


def _normalise_targets(target_houses) -> dict[int, float]:
    """Accept a set/list of houses OR a {house: weight} dict; return {house: weight}.

    A set/list yields weight 1.0 per house -- the pre-S145 contract, byte-identical
    in scoring. A dict is taken as-is (ints, float weights). This is the ONLY place
    the two input shapes are reconciled, so every downstream calculation is
    weight-based and the set path is just "all weights are 1.0".
    """
    if isinstance(target_houses, dict):
        return {int(h): float(w) for h, w in target_houses.items()}
    return {int(h): 1.0 for h in (target_houses or ())}


def _saturn_contact_houses(house_from_lagna: int) -> set[int]:
    """Houses Saturn (at `house_from_lagna`) contacts: its own house plus its
    3rd, 7th and 10th aspects. House arithmetic is 1-based, wrapping mod 12."""
    h = ((house_from_lagna - 1) % 12) + 1
    return {h,
            ((h - 1 + 2) % 12) + 1,   # 3rd aspect
            ((h - 1 + 6) % 12) + 1,   # 7th aspect (universal)
            ((h - 1 + 9) % 12) + 1}   # 10th aspect


def _jupiter_contact_houses(house_from_lagna: int) -> set[int]:
    """Houses Jupiter (at `house_from_lagna`) contacts: its own house plus its
    5th, 7th and 9th aspects (Jupiter's special aspects)."""
    h = ((house_from_lagna - 1) % 12) + 1
    return {h,
            ((h - 1 + 4) % 12) + 1,   # 5th aspect
            ((h - 1 + 6) % 12) + 1,   # 7th aspect (universal)
            ((h - 1 + 8) % 12) + 1}   # 9th aspect


def rank_windows(
    mahadasha_tree: list[dict],
    significators: dict[str, tuple[int, ...] | list[int]],
    transit_periods: dict[str, dict],
    target_houses: set[int] | list[int] | dict[int, float],
    natal_saturn_house: int | None,
) -> list[dict]:
    """Score every antardasha by convergence toward `target_houses`.

    `target_houses` is a set/list (each house weight 1.0) or a {house: weight}
    dict (S145 role weights). Returns a list of scored windows, highest score
    first. Each item:
        {md_lord, ad_lord, start, end, phase, score,
         sig_hits: [houses], md_supports: bool, transit_hits: [houses],
         is_saturn_return: bool, jupiter_hits: [houses], why: str}
    Reported *_hits list only POSITIVE-weight houses (the ones that scored).
    Pure and deterministic; never raises for ordinary malformed rows (skips
    them). `natal_saturn_house` None disables only the return signal.
    """
    weights = _normalise_targets(target_houses)
    targets = set(weights)                       # every house is still a valid match
    positive = {h for h, w in weights.items() if w > 0}
    natal_contact = (_saturn_contact_houses(natal_saturn_house)
                     if natal_saturn_house else set())
    # A return only matters if the natal contact lands on a house that actually
    # counts (positive weight) -- a return onto a zeroed obstacle house is noise.
    natal_return_relevant = bool(natal_contact & positive)

    out: list[dict] = []
    for node in mahadasha_tree or []:
        if not isinstance(node, dict):
            continue
        md = node.get("mahadasha") or {}
        md_lord = md.get("lord")
        phase = node.get("phase")
        md_sig = {int(h) for h in (significators.get(md_lord) or ())}
        md_supports = bool(md_sig & positive)

        for ad in node.get("antardashas") or []:
            if not isinstance(ad, dict):
                continue
            ad_lord = ad.get("lord")
            start = ad.get("start")
            if not ad_lord or not start:
                continue

            sig_all = {int(h) for h in (significators.get(ad_lord) or ())} & targets
            sig_hits = sorted(h for h in sig_all if weights[h] > 0)   # reported hits
            sig_score = W_SIG * sum(weights[h] for h in sig_all)      # weight-scaled

            t = transit_periods.get(f"{ad_lord}|{start}") or {}
            hl = t.get("saturn_house_from_lagna")
            transit_hits: list[int] = []
            is_return = False
            if isinstance(hl, int):
                contact = _saturn_contact_houses(hl) & targets
                transit_hits = sorted(h for h in contact if weights[h] > 0)
                is_return = (natal_saturn_house is not None
                             and hl == natal_saturn_house
                             and natal_return_relevant)

            jl = t.get("jupiter_house_from_lagna")
            jupiter_hits: list[int] = []
            if isinstance(jl, int):
                jcontact = _jupiter_contact_houses(jl) & targets
                jupiter_hits = sorted(h for h in jcontact if weights[h] > 0)

            score = (sig_score
                     + (W_MD if md_supports else 0.0)
                     + (W_ACT if transit_hits else 0.0)
                     + (W_RET if is_return else 0.0)
                     + (W_JUP if jupiter_hits else 0.0))
            if score <= 0:
                continue  # a window with no signal toward the target is not a candidate

            why_bits = []
            if sig_hits:
                why_bits.append(f"{ad_lord} signifies {','.join(map(str, sig_hits))}")
            if md_supports:
                why_bits.append(f"under {md_lord} MD (also a significator)")
            if transit_hits:
                why_bits.append(f"Saturn transit contacts {','.join(map(str, transit_hits))}")
            if is_return:
                why_bits.append("Saturn RETURN to natal house re-firing its natal "
                                "contact on a target house [milestone]")
            if jupiter_hits:
                why_bits.append(f"Jupiter transit contacts {','.join(map(str, jupiter_hits))}")

            out.append({
                "md_lord": md_lord, "ad_lord": ad_lord,
                "start": start, "end": ad.get("end"), "phase": phase,
                "score": round(score, 2),
                "sig_hits": sig_hits, "md_supports": md_supports,
                "transit_hits": transit_hits, "is_saturn_return": is_return,
                "jupiter_hits": jupiter_hits,
                "why": "; ".join(why_bits),
            })

    out.sort(key=lambda w: (-w["score"], w["start"]))
    return out


def build_timing_ranking(
    chart_facts: dict,
    target_houses: set[int] | list[int] | dict[int, float],
) -> dict:
    """Fail-soft composer: pull the ranker's inputs out of chart_facts and rank.

    `target_houses` is a set/list (pre-S145) or a {house: weight} dict (S145).
    Returns {"target_houses": [...positive-weight houses...], "windows": [...]}
    or {} if the required facts are absent / malformed (ranking is corroboration,
    never load-bearing). The reported target_houses list shows only the houses
    that actually count toward the score (weight > 0), so the interpreter is told
    "houses 2,7,11", not the zeroed obstacle house the planner also emitted.
    """
    try:
        weights = _normalise_targets(target_houses)
        if not weights:
            return {}
        display = sorted(h for h, w in weights.items() if w > 0)
        tree = ((chart_facts.get("dasha_periods") or {}).get("mahadasha_tree")) or []
        sigs = ((chart_facts.get("kp_planet_significations") or {})
                .get("planet_significations")) or {}
        periods = ((chart_facts.get("transits") or {}).get("periods")) or {}
        if not tree or not sigs:
            return {}  # no dasha tree or no significators -> nothing to converge

        sat = ((chart_facts.get("planet_positions") or {}).get("Saturn") or {})
        natal_saturn_house = sat.get("house") if isinstance(sat.get("house"), int) else None

        windows = rank_windows(tree, sigs, periods, weights, natal_saturn_house)
        if not windows:
            return {}
        return {"target_houses": display, "windows": windows}
    except Exception as e:  # noqa: BLE001 -- ranking must never break an answer
        logger.warning("timing_ranker.build_timing_ranking failed: %s: %s",
                       type(e).__name__, e)
        return {}


def render_ranking(ranking: dict, limit: int = 6) -> str:
    """Render the ranking as a fact-block section. Empty string if no ranking."""
    windows = (ranking or {}).get("windows") or []
    if not windows:
        return ""
    targets = ranking.get("target_houses") or []
    lines = [
        "",
        f"COMPUTED TIMING RANKING (deterministic convergence for houses "
        f"{','.join(map(str, targets))} -- combines KP significators of the acting "
        f"lords with Saturn- and Jupiter-transit corroboration; higher = stronger multi-system "
        f"agreement). Treat this ranking as a computed FACT: EXPLAIN the top "
        f"window(s) in plain terms and say why the lower ones rank below -- do NOT "
        f"re-order them from your own priors. A Saturn RETURN re-firing a natal "
        f"contact is a milestone trigger, not an obstacle.",
    ]
    for i, w in enumerate(windows[:limit], 1):
        ph = f" [{w['phase']}]" if w.get("phase") else ""
        lines.append(
            f"  {i}. {w['md_lord']}-{w['ad_lord']} ({w['start']} to {w['end']})"
            f"{ph} -- score {w['score']}: {w['why']}"
        )
    return "\n".join(lines)
