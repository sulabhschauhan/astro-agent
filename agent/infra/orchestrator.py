"""Thin-slice pipeline orchestrator -- router -> profile -> formatter -> demotion merge.

S44.5, thin-slice answer pipeline checkpoint (Session 31 key decision 3 /
Session 44 sequencing). Single entry point wiring the three pipeline stages
built in S44.3 (calc_router.py), S44.2 (chart_profile.py), and S44.4
(result_formatter.py). NO LLM calls anywhere in this module (Session 23 V1
lock) -- this is pure routing/dispatch glue, not synthesis.

chart_data OWNERSHIP CONTRACT: this module never calls calculate_chart() (or
any other calculation/ephemeris function besides swe.julday for the
evaluated_at_jd capture). chart_data/partner_chart_data arrive pre-computed
from the caller and are passed through unchanged; V1 has no caching layer,
so callers reusing the same chart across multiple questions must hold onto
their own calculate_chart() output.

DEMOTION MERGE (Option A pattern): route_question() and format_answer() are
two independent sources of tier-demotion knowledge -- the router knows about
domain-wide caveats (Drik Bala stub for career, +/-37-day dasha drift) that
exist regardless of the specific chart; the formatter knows about
per-answer conditions read off the specific profile (e.g. a near-boundary
dasha transition, once that payload field is wired up). Neither one is
allowed to overwrite the other's finding. This module ORs the two signals in
_merge_router_demotion(): if only one side demoted, its reason wins; if both
demoted, their reasons are concatenated with " | " because both are real,
independent signals worth surfacing together.
"""

from __future__ import annotations

import dataclasses
import logging
from datetime import datetime, timezone

import swisseph as swe

from agent.infra.calc_router import RouteResult, route_question
from agent.infra.chart_profile import AnswerTier, DomainAnswer, build_domain_profile
from agent.infra.result_formatter import format_answer

logger = logging.getLogger(__name__)

# "sade_sati" added Session 50/P7.2d (calc_router.py's own deterministic
# fast-path + Stage 2 support landed P7.2c; this was the only remaining
# blocker -- see diagnostics/latest_run.md P7.2c entry).
# "av_transit" added Session 55 -- chart_profile.py's builder branch and
# result_formatter.py's render branch both already exist and are
# smoke-test-verified (see diagnostics/latest_run.md, prior Session 55
# entries), but calc_router.py cannot yet emit this domain (router wiring
# is the next, separate change). Dead entry by design until then --
# mirrors the sade_sati wiring-order precedent above (formatter/builder
# landed before the router could route to it).
_VALID_DOMAINS = {
    "marriage_compatibility",
    "career_strength",
    "current_dasha",
    "sade_sati",
    "av_transit",
}

# DEMOTION LOCK (Session 55, av_transit): route_question() will set
# demotion_reason=None for this domain once router wiring lands --
# av_transit's own ±37-day-plus-day-level-resolution demotion string is
# owned entirely by result_formatter.py's _format_av_transit() branch
# (payload-property principle, same as current_dasha/sade_sati). This is
# intentional and requires NO change to _merge_router_demotion() below:
# that function already returns `answer` unchanged whenever
# router_reason is None, so the formatter's own demotion_reason is never
# overwritten. If the router ever needs to add a domain-wide av_transit
# caveat later, revisit _merge_router_demotion()'s " | " concatenation
# at that point -- do not preemptively wire it now.


def answer_question(
    question: str,
    chart_data: dict,
    partner_chart_data: dict | None = None,
    primary_role: str | None = None,
    *,
    transit_planet: str = "Saturn",
) -> DomainAnswer:
    """Route `question`, assemble its DomainChartProfile, and format a DomainAnswer.

    Args:
        question: user's natural-language question string.
        chart_data: pre-computed calculate_chart() output for the primary
            native. Never recomputed here.
        partner_chart_data: pre-computed calculate_chart() output for the
            second native. Only meaningful for marriage_compatibility;
            required together with primary_role whenever supplied.
        primary_role: "boy" or "girl" -- required when partner_chart_data is
            given, regardless of which domain the question ultimately routes
            to (an orchestrator-level input contract, not a router concern).
        transit_planet: one of "Saturn", "Jupiter", "Sun", "Mars". Only
            meaningful for domain="av_transit" -- passed through to
            build_domain_profile() ONLY when route_result.domain ==
            "av_transit" (same conditional-kwarg pattern as
            partner_chart_data/primary_role's is_marriage gating below).
            calc_router.py cannot yet route any question to "av_transit"
            (router wiring is a separate, later change), so this parameter
            is currently unreachable via any live question string --
            present now so build_domain_profile()'s call site is already
            correct once routing lands.

    Returns:
        DomainAnswer -- always, including AnswerTier.REFUSAL cases.

    Raises:
        ValueError: partner_chart_data given without primary_role;
            router routed to marriage_compatibility without partner
            data (defensive -- route_question's own has_partner_data
            guard should already prevent this); router returned a
            domain outside the routable whitelist (defensive).
        RuntimeError: propagated, uncaught, from build_domain_profile()
            or format_answer() on any underlying calculation failure.

    NOTE (Session 50/P7.2d, item 1 verification; updated Session 55): the
    marriage-only partner-data guard (below) and the is_marriage-gated
    partner_chart_data/primary_role pass-through into build_domain_profile()
    remain special-cased ONLY to "marriage_compatibility" and evaluate to
    their False/None branch for every other domain -- confirmed by reading,
    not assumed -- so "sade_sati"/"career_strength"/"current_dasha" pass
    through them unchanged, exactly as before. Session 55 adds a second,
    parallel domain-specific branch (is_av_transit-gated transit_planet
    pass-through) that follows the identical pattern for "av_transit" --
    the two conditionals are independent and mutually exclusive (a
    question can only ever route to one domain), not a chain of
    special cases growing more entangled over time.
    """
    if partner_chart_data is not None and primary_role is None:
        raise ValueError(
            "answer_question: primary_role ('boy' or 'girl') is required "
            "whenever partner_chart_data is supplied"
        )

    route_result: RouteResult = route_question(
        question,
        has_partner_data=partner_chart_data is not None,
        chart_data=chart_data,
    )

    if route_result.tier == AnswerTier.REFUSAL:
        return DomainAnswer(
            domain=route_result.domain,
            tier=AnswerTier.REFUSAL,
            answer_payload={},
            stub_caveats=(),
            uncertainty_virupa=0.0,
            demotion_reason=route_result.demotion_reason,
            sources=(),
            uncertainty_days=0.0,
        )

    if route_result.domain not in _VALID_DOMAINS:
        raise ValueError(
            f"answer_question: router returned unrecognized domain "
            f"{route_result.domain!r} outside the routable whitelist "
            f"{sorted(_VALID_DOMAINS)}"
        )

    if route_result.domain == "marriage_compatibility" and partner_chart_data is None:
        raise ValueError(
            "answer_question: router selected marriage_compatibility but no "
            "partner_chart_data was supplied -- route_question's "
            "has_partner_data guard should have already forced a REFUSAL"
        )

    now_utc = datetime.now(timezone.utc)
    hour_decimal = now_utc.hour + now_utc.minute / 60.0 + now_utc.second / 3600.0
    evaluated_at_jd = swe.julday(now_utc.year, now_utc.month, now_utc.day, hour_decimal)

    is_marriage = route_result.domain == "marriage_compatibility"
    is_av_transit = route_result.domain == "av_transit"
    profile = build_domain_profile(
        route_result.domain,
        chart_data,
        evaluated_at_jd,
        partner_chart_data=partner_chart_data if is_marriage else None,
        primary_role=primary_role if is_marriage else None,
        transit_planet=transit_planet if is_av_transit else "Saturn",
    )

    formatted = format_answer(profile)

    return _merge_router_demotion(formatted, route_result)


def _merge_router_demotion(answer: DomainAnswer, route_result: RouteResult) -> DomainAnswer:
    """Overlay the router's demotion signal onto the formatter's, per Option A.

    Router-only demotion: formatter's None is replaced with the router's
    reason, and TIER_1_EXACT is bumped to TIER_2_RANGE. Both-demoted: reasons
    are concatenated (" | "), tier stays/becomes TIER_2_RANGE. Formatter-only
    demotion (router's reason is None): answer is returned unchanged.
    """
    router_reason = route_result.demotion_reason
    if router_reason is None:
        return answer

    if answer.demotion_reason is None:
        merged_reason = router_reason
    else:
        merged_reason = f"{answer.demotion_reason} | {router_reason}"

    merged_tier = (
        AnswerTier.TIER_2_RANGE if answer.tier == AnswerTier.TIER_1_EXACT else answer.tier
    )

    return dataclasses.replace(answer, tier=merged_tier, demotion_reason=merged_reason)
