"""Result Formatter -- DomainChartProfile -> DomainAnswer rendering.

S44.4, thin-slice answer pipeline checkpoint (Session 31 key decision 3 /
Session 44 sequencing). Pure deterministic template rendering: every value
in answer_payload is copied or arithmetically derived from profile.payload,
never generated. NO LLM calls anywhere in this module (Session 23 V1 lock).

SCOPE BOUNDARY: this module does not classify questions (that is the Calc
Router, calc_router.py) and does not compute tier-demotion logic beyond the
one dasha-domain boundary check already carried on the profile by the
router -- it only reads pre-assembled DomainChartProfile.payload and renders
the DomainAnswer contract fixed by chart_profile.py.
"""

from __future__ import annotations

import logging

from agent.infra.chart_profile import AnswerTier, DomainAnswer, DomainChartProfile

logger = logging.getLogger(__name__)

# Ashtakoot verdict thresholds, AstroSage-aligned (out of 36 max).
_VERDICT_HIGHLY_COMPATIBLE_MIN = 25.0
_VERDICT_COMPATIBLE_MIN = 18.0
_VERDICT_MODERATELY_COMPATIBLE_MIN = 10.0

# Shadbala ratio -> label thresholds. NOT tightened further than this because
# Drik Bala is stubbed (CLAUDE.md "Shadbala Drik Bala (V1 stub)"): the AstroSage
# fixture envelope is -20.44..+22.15 Virupa per planet, i.e. ~=0.33 Rupa of
# ratio-denominator-scale uncertainty -- a finer-grained label boundary than
# this would claim precision the underlying data does not have.
_LABEL_STRONG_MIN = 1.2
_LABEL_ADEQUATE_MIN = 0.8

# User-facing note surfaced on the DomainAnswer when the evaluated instant
# falls near a dasha period boundary.
_BOUNDARY_NOTE = (
    "Current Antardasha boundary is within +/-37 days of documented drift "
    "tolerance. The lord identification is reliable; exact transition dates "
    "should be cross-verified."
)

# Copied verbatim from calc_router._DASHA_DEMOTION_REASON (S44.3) -- not
# imported, per this module's contract: no dependency on calc_router internals.
_DASHA_DEMOTION_REASON = (
    "Antardasha boundaries carry ±37-day drift vs AstroSage; current "
    "lord is reliable except near period boundaries"
)


def format_answer(profile: DomainChartProfile) -> DomainAnswer:
    """Route to the domain-specific formatter based on profile.domain."""
    if profile.domain == "marriage_compatibility":
        return _format_marriage(profile)
    if profile.domain == "career_strength":
        return _format_career(profile)
    if profile.domain == "current_dasha":
        return _format_dasha(profile)
    raise ValueError(f"result_formatter: unknown domain {profile.domain!r}")


def _planet_label(ratio: float) -> str:
    """Shadbala ratio -> strong/adequate/weak, per the module-level thresholds."""
    if ratio >= _LABEL_STRONG_MIN:
        return "strong"
    if ratio >= _LABEL_ADEQUATE_MIN:
        return "adequate"
    return "weak"


def _format_marriage(profile: DomainChartProfile) -> DomainAnswer:
    ashtakoot = profile.payload["ashtakoot"]
    mangal_boy = profile.payload["mangal_dosha_boy"]
    mangal_girl = profile.payload["mangal_dosha_girl"]

    total_score = ashtakoot.total_score
    if total_score >= _VERDICT_HIGHLY_COMPATIBLE_MIN:
        verdict = "highly_compatible"
    elif total_score >= _VERDICT_COMPATIBLE_MIN:
        verdict = "compatible"
    elif total_score >= _VERDICT_MODERATELY_COMPATIBLE_MIN:
        verdict = "moderately_compatible"
    else:
        verdict = "incompatible"

    boy_has_dosha = mangal_boy.has_dosha
    girl_has_dosha = mangal_girl.has_dosha

    # ashtakoot.kootas is keyed by ashtakoot.py's own Title-case koota names
    # (note "GrahaMaitri"/"Bhakoot", not "graha_maitri"/"bhakoota") -- this
    # dict re-keys to the answer_payload's snake_case contract.
    kootas = ashtakoot.kootas
    koota_scores = {
        "varna": {"score": kootas["Varna"].score, "max": kootas["Varna"].max_score},
        "vashya": {"score": kootas["Vashya"].score, "max": kootas["Vashya"].max_score},
        "tara": {"score": kootas["Tara"].score, "max": kootas["Tara"].max_score},
        "yoni": {"score": kootas["Yoni"].score, "max": kootas["Yoni"].max_score},
        "graha_maitri": {
            "score": kootas["GrahaMaitri"].score,
            "max": kootas["GrahaMaitri"].max_score,
        },
        "gana": {"score": kootas["Gana"].score, "max": kootas["Gana"].max_score},
        "bhakoota": {"score": kootas["Bhakoot"].score, "max": kootas["Bhakoot"].max_score},
        "nadi": {"score": kootas["Nadi"].score, "max": kootas["Nadi"].max_score},
    }

    answer_payload = {
        "total_score": total_score,
        "max_score": 36.0,
        "koota_scores": koota_scores,
        "mangal_dosha": {
            "boy": boy_has_dosha,
            "girl": girl_has_dosha,
            "both_have": boy_has_dosha and girl_has_dosha,
        },
        "verdict": verdict,
    }

    return DomainAnswer(
        domain=profile.domain,
        tier=AnswerTier.TIER_1_EXACT,
        answer_payload=answer_payload,
        stub_caveats=profile.stub_caveats,
        uncertainty_virupa=profile.uncertainty_virupa,
        demotion_reason=None,
        sources=("ashtakoot", "mangal_dosha"),
        uncertainty_days=profile.uncertainty_days,
    )


def _significator_block(shadbala_row: dict) -> dict:
    return {
        "planet": shadbala_row["_planet_name"],
        "rupa": shadbala_row["shadbala_rupa"],
        "ratio": shadbala_row["ratio"],
        "rank": shadbala_row["rank"],
        "label": _planet_label(shadbala_row["ratio"]),
        "above_min": shadbala_row["ratio"] >= 1.0,
    }


def _format_career(profile: DomainChartProfile) -> DomainAnswer:
    shadbala = profile.payload["shadbala"]
    bhava_bala = profile.payload["bhava_bala"]
    tenth_lord_name = profile.payload["tenth_lord"]

    tenth_lord_row = {**shadbala[tenth_lord_name], "_planet_name": tenth_lord_name}
    sun_row = {**shadbala["sun"], "_planet_name": "sun"}
    saturn_row = {**shadbala["saturn"], "_planet_name": "saturn"}

    strongest_planet = next(p for p, row in shadbala.items() if row["rank"] == 1)
    weakest_planet = next(p for p, row in shadbala.items() if row["rank"] == 7)

    answer_payload = {
        "career_significators": {
            "tenth_lord": _significator_block(tenth_lord_row),
            "sun": _significator_block(sun_row),
            "saturn": _significator_block(saturn_row),
        },
        "strongest_planet": strongest_planet,
        "weakest_planet": weakest_planet,
        "bhava_10_rupa": bhava_bala[10]["total_rupa"],
    }

    return DomainAnswer(
        domain=profile.domain,
        tier=AnswerTier.TIER_2_RANGE,
        answer_payload=answer_payload,
        stub_caveats=profile.stub_caveats,
        uncertainty_virupa=profile.uncertainty_virupa,
        demotion_reason=None,
        sources=("shadbala", "bhava_bala"),
        uncertainty_days=profile.uncertainty_days,
    )


def _format_dasha(profile: DomainChartProfile) -> DomainAnswer:
    mahadasha = profile.payload["current_mahadasha"]
    antardasha = profile.payload["current_antardasha"]
    near_boundary = profile.payload.get("near_boundary", False)

    boundary_note = None
    tier = AnswerTier.TIER_1_EXACT
    demotion_reason = None
    if near_boundary:
        boundary_note = _BOUNDARY_NOTE
        tier = AnswerTier.TIER_2_RANGE
        demotion_reason = _DASHA_DEMOTION_REASON

    answer_payload = {
        "mahadasha": {
            "lord": mahadasha["lord"],
            "start": mahadasha["start"],
            "end": mahadasha["end"],
        },
        "antardasha": {
            "lord": antardasha["lord"],
            "start": antardasha["start"],
            "end": antardasha["end"],
        },
        "near_boundary": near_boundary,
        "boundary_note": boundary_note,
    }

    return DomainAnswer(
        domain=profile.domain,
        tier=tier,
        answer_payload=answer_payload,
        stub_caveats=profile.stub_caveats,
        uncertainty_virupa=profile.uncertainty_virupa,
        demotion_reason=demotion_reason,
        sources=("vimshottari_dasha",),
        uncertainty_days=profile.uncertainty_days,
    )
