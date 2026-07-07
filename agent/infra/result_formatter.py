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

Session 50/P7.2b adds a 4th domain, "sade_sati" -- a TIER_1_EXACT-only
render (no ±37-day-style drift language anywhere in that branch: the
payload carries no dated dasha claims, per the "tier = payload property"
lock, chart_profile.py's own P7.2a docstring). It is also this file's
first JD->human-date conversion: current_dasha's mahadasha/antardasha
date strings arrive from chart_profile.py already formatted (chart_
calculator._fmt()'s "D Mon YYYY", day-level, no time-of-day), so this file
never needed its own JD conversion before. _format_jd() below mirrors that
exact "D Mon YYYY" output convention, sourced via panchanga.py's
swe.revjul()-based conversion pattern (this project's own existing
JD->datetime precedent) -- not a second, independently-invented
conversion path.

Session 55 adds a 5th domain, "av_transit" -- always TIER_2_RANGE (payload-
property principle, P7.0c precedent: this payload carries dated Antardasha
envelope + sub-window claims, so it always carries the drift language, same
reasoning as current_dasha, opposite of sade_sati). Its raw JD fields
(dasha_envelope start/end, each sub-window's start/end) are converted with
this file's own _format_jd(), same as sade_sati's boundary fields. The
upstream convergence layer that assembles this payload does not exist yet
as of this branch landing (Session 54 Conflict A: formatter lands first,
convergence wiring and router are later, separate changes) -- the payload
shape is frozen by design-chat ahead of that layer's construction, so this
branch is unreachable via any live router path until that wiring lands.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import swisseph as swe

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

# av_transit demotion reason (Session 55). Covers BOTH uncertainty axes on
# this payload: the ±37-day Antardasha envelope drift (same axis as
# _DASHA_DEMOTION_REASON above) AND the day-level resolution of sub-window
# boundaries (av_transit_scanner steps day-by-day, no sub-day bisection) --
# these are orthogonal sources of imprecision and both must be disclosed.
_AV_TRANSIT_DEMOTION_REASON = (
    "Antardasha envelope carries ±37-day drift vs AstroSage; sub-window "
    "boundaries are day-level resolution (daily-step scanner, no sub-day "
    "bisection) -- exact transition dates should be cross-verified"
)

# SENSITIVE_TO chart_profile.py's _SADE_SATI_ADJACENT_CYCLE_SCAN_YEARS (=40):
# this literal must stay in sync with that constant if it's ever changed --
# not imported (this module's contract: no dependency on chart_profile.py
# internals, only its public DomainChartProfile/AnswerTier/DomainAnswer
# contract), same encapsulation as _DASHA_DEMOTION_REASON above.
_SADE_SATI_UNKNOWN_BOUNDARY = "not determinable within ±40y scan window"


def format_answer(profile: DomainChartProfile) -> DomainAnswer:
    """Route to the domain-specific formatter based on profile.domain."""
    if profile.domain == "marriage_compatibility":
        return _format_marriage(profile)
    if profile.domain == "career_strength":
        return _format_career(profile)
    if profile.domain == "current_dasha":
        return _format_dasha(profile)
    if profile.domain == "sade_sati":
        return _format_sade_sati(profile)
    if profile.domain == "av_transit":
        return _format_av_transit(profile)
    raise ValueError(f"result_formatter: unknown domain {profile.domain!r}")


def _format_jd(jd_ut: float) -> str:
    """JD (UT) -> "D Mon YYYY" string -- matches chart_calculator._fmt()'s
    exact output convention (day-level precision, no time-of-day; the only
    human-date format used anywhere in this pipeline's payloads so far --
    current_dasha's mahadasha/antardasha start/end strings arrive already
    formatted this way from chart_profile.py, see module docstring).
    Conversion mechanics (swe.revjul() + timedelta) mirror panchanga.py's
    _julian_day_ut_to_datetime -- this project's own existing JD->datetime
    precedent -- rather than inventing a second one.
    """
    y, mo, dy, hr = swe.revjul(jd_ut)
    dt = datetime(y, mo, dy, tzinfo=timezone.utc) + timedelta(hours=hr)
    return f"{dt.day} {dt.strftime('%b')} {dt.year}"


def _format_jd_or_unknown(jd_ut: float | None) -> str:
    """None-safe wrapper: chart_profile.py's sade_sati payload uses None for
    a boundary genuinely not found within its +/-40y scan window (not an
    error) -- must not crash, must not fabricate a date."""
    if jd_ut is None:
        return _SADE_SATI_UNKNOWN_BOUNDARY
    return _format_jd(jd_ut)


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


def _format_sade_sati(profile: DomainChartProfile) -> DomainAnswer:
    """Always TIER_1_EXACT, always demotion_reason=None -- no ±37-day-style
    drift language anywhere in this branch (design lock: tier is a payload
    property, and this payload carries no dated dasha claims, unlike
    current_dasha's). All 4 boundary fields are rendered None-safely via
    _format_jd_or_unknown() regardless of `active` (chart_profile.py's own
    P7.2a docstring notes current_cycle_start/end are populated "if
    active", but does not guarantee active=True always implies a found
    macro envelope -- rendering must not assume it and must not crash).
    """
    active = profile.payload["active"]
    phase = profile.payload["phase"]

    # Rendering rule (P7.2b contract): active -> phase + current cycle span
    # + next cycle start; not active -> not-active + previous cycle end +
    # next cycle start. Both branches always report next_cycle_start.
    answer_payload: dict = {
        "active": active,
        "phase": phase,
        "next_cycle_start": _format_jd_or_unknown(profile.payload["next_cycle_start_jd"]),
    }
    if active:
        answer_payload["current_cycle_start"] = _format_jd_or_unknown(
            profile.payload["current_cycle_start_jd"]
        )
        answer_payload["current_cycle_end"] = _format_jd_or_unknown(
            profile.payload["current_cycle_end_jd"]
        )
    else:
        answer_payload["previous_cycle_end"] = _format_jd_or_unknown(
            profile.payload["previous_cycle_end_jd"]
        )

    return DomainAnswer(
        domain=profile.domain,
        tier=AnswerTier.TIER_1_EXACT,
        answer_payload=answer_payload,
        stub_caveats=profile.stub_caveats,
        uncertainty_virupa=profile.uncertainty_virupa,
        demotion_reason=None,
        sources=("sade_sati",),
        uncertainty_days=profile.uncertainty_days,
    )


def _format_av_transit(profile: DomainChartProfile) -> DomainAnswer:
    """Always TIER_2_RANGE -- payload-property principle, P7.0c precedent:
    this payload carries dated Antardasha-envelope + sub-window claims, so
    it always carries the drift language (same reasoning as current_dasha,
    opposite of sade_sati's T1-only branch above).

    Missing/malformed payload keys are NOT defended against here (existing
    module convention, see _format_marriage/_format_dasha above): direct
    dict indexing raises KeyError with the offending key name, never a
    partial render.

    NEVER-COLLAPSE GUARD (Session 54 locked decision 2): an empty
    sub_windows list is a designed fail-closed path, not a defensive
    padding case -- a dasha envelope with no ranked sub-windows underneath
    it is not a renderable Tier 2 AV-transit answer.
    """
    transit_planet = profile.payload["transit_planet"]
    envelope = profile.payload["dasha_envelope"]
    sub_windows = profile.payload["sub_windows"]

    if not sub_windows:
        raise ValueError(
            "result_formatter: av_transit payload has an empty sub_windows "
            "list -- Session 54 locked decision 2 (never-collapse guard) "
            "forbids rendering a dasha envelope without ranked sub-windows"
        )

    rendered_windows = [
        {
            "rank": window["rank"],
            "start": _format_jd(window["start_jd"]),
            "end": _format_jd(window["end_jd"]),
            "sign": window["sign"],
            "bav_bindus": window["bav_bindus"],
            "sav_bindus": window["sav_bindus"],
            "bav_band": window["bav_band"],
            "sav_band": window["sav_band"],
            "verdict": window["verdict"],
            "kakshya_lord": window["kakshya_lord"],
        }
        # Preserve rank order as given -- the convergence layer owns
        # ranking, this file never re-sorts.
        for window in sub_windows
    ]

    answer_payload = {
        "transit_planet": transit_planet,
        "dasha_envelope": {
            "mahadasha_lord": envelope["mahadasha_lord"],
            "antardasha_lord": envelope["antardasha_lord"],
            "start": _format_jd(envelope["start_jd"]),
            "end": _format_jd(envelope["end_jd"]),
        },
        "sub_windows": rendered_windows,
    }

    return DomainAnswer(
        domain=profile.domain,
        tier=AnswerTier.TIER_2_RANGE,
        answer_payload=answer_payload,
        stub_caveats=profile.stub_caveats,
        uncertainty_virupa=profile.uncertainty_virupa,
        demotion_reason=_AV_TRANSIT_DEMOTION_REASON,
        sources=(
            "ashtakavarga",
            "av_transit_scorer",
            "av_transit_scanner",
            "vimshottari_dasha",
        ),
        uncertainty_days=profile.uncertainty_days,
    )
