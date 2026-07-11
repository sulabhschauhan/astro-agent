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

Session 59 adds a 6th domain, "arudha_lagna" -- TIER_1_EXACT only, mirroring
sade_sati's pattern (no dated claims anywhere in the payload, so no drift
language, no _format_jd calls). Same staged-rollout precedent as av_transit
above: chart_profile.py's build_arudha_lagna_profile() is a standalone
builder, not yet wired into build_domain_profile()'s dispatch, and
orchestrator.py's _VALID_DOMAINS does not yet admit "arudha_lagna" -- this
branch is dead code until that separate, later wiring lands. Deviation
flagged: the branch's original spec called for a rendered prose paragraph
inside answer_payload, but this field is documented below as "NEVER prose"
-- no other domain branch violates that, so answer_payload here stays
structured-only (arudha_sign/lagna_sign/lord/co_lord_deciding_step,
verbatim); prose rendering is deferred to a separate concern.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import swisseph as swe

from agent.infra.calc_router import RouteResult
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

# Session 56: fixed disclosure string rendered INSIDE an OPTIONAL
# "timing_enrichment" block only (career_strength/current_dasha, see
# _format_career()/_format_dasha() below) -- GOLDEN STAKE GUARD: NEVER
# appended to either domain's own top-level demotion_reason (golden rows
# q1-q5/q11-q13 assert on demotion_reason substrings and must not move).
# Same two uncertainty axes as _AV_TRANSIT_DEMOTION_REASON above (day-level
# sub-window resolution + ±37-day envelope drift), worded standalone since
# it lives inside a nested payload block, not a top-level DomainAnswer field.
_TIMING_ENRICHMENT_RESOLUTION_NOTE = (
    "This timing enrichment's sub-window boundaries are day-level "
    "resolution (daily-step scanner, no sub-day bisection), and its "
    "Antardasha envelope carries ±37-day drift vs AstroSage -- exact "
    "transition dates should be cross-verified."
)

# ─── format_refusal() support (new prompt; orchestrator delegation is a ───
# ─── separate, later prompt -- this helper is dead code until then) ──────
#
# DESIGN: RouteResult.demotion_reason is the machine contract -- calc_router.py
# fixes its exact wording/value for routing logic, golden-harness substring
# assertions, and _merge_router_demotion()'s " | " concatenation. The
# strings in _REFUSAL_USER_MESSAGES below are the presentation layer: what a
# non-technical user actually reads. Same split as the av_transit
# formatter-owns-strings precedent above (_AV_TRANSIT_DEMOTION_REASON is
# calc_router-facing machine wiring -- calc_router itself leaves
# demotion_reason=None for av_transit and lets this file own the string);
# here the two layers are simply two different strings keyed off the same
# demotion_reason, rather than one module owning both ends.
#
# Keys copied verbatim from calc_router.py's own REFUSAL-path demotion_reason
# literals (read directly from that file, not guessed/recalled) -- same
# "copied verbatim, not imported" convention as _DASHA_DEMOTION_REASON above
# (this module's contract: no dependency on calc_router.py's internal string
# constants). Only calc_router.py's two FIXED (non-interpolated) REFUSAL
# strings are keyable here:
#   - "marriage_compatibility requires partner birth data"
#       (_route_to_domain's has_partner_data hard guard)
#   - "question not classifiable with confidence"
#       (_stage2_fallback's exception path AND its low-confidence path --
#       both emit this exact same literal)
# calc_router.py's other two REFUSAL paths (_UNBUILT_MODULE_KEYWORDS and
# _OUT_OF_SCOPE_KEYWORDS) build their demotion_reason via an f-string that
# interpolates the matched keyword/module name -- there is no fixed literal
# to key on, so those fall through to the generic branch below by design,
# not by omission.
#
# Domain list in the "not classifiable" message is hand-written here (not
# imported) from calc_router.py's own _STAGE2_VALID_DOMAINS as read at the
# time this was written: {marriage_compatibility, career_strength,
# current_dasha, sade_sati, av_transit, arudha_lagna} (frozenset minus the
# "none" sentinel) -- SENSITIVE_TO that set: if a future domain is added to
# or removed from _STAGE2_VALID_DOMAINS, this message must be re-checked for
# drift, same obligation as _SADE_SATI_UNKNOWN_BOUNDARY's SENSITIVE_TO note
# above.
_REFUSAL_USER_MESSAGES: dict[str, str] = {
    "marriage_compatibility requires partner birth data": (
        "To check marriage compatibility, I also need your partner's birth "
        "details -- their date of birth, time of birth, and place of "
        "birth. Please share those and I can take a look."
    ),
    "question not classifiable with confidence": (
        "I couldn't confidently tell what you're asking. Could you try "
        "rephrasing? I can help with questions about: marriage "
        "compatibility, career strength, the life period (dasha) you're "
        "currently in, Sade Sati (Saturn's roughly 7.5-year transit around "
        "your Moon sign), how a specific planet's transit is playing out "
        "right now, and your public image/reputation."
    ),
}

# Generic fallback for any demotion_reason not in _REFUSAL_USER_MESSAGES
# above (None, or one of calc_router.py's interpolated unbuilt-module/
# out-of-scope strings) -- fail-closed, must never KeyError.
_GENERIC_REFUSAL_MESSAGE = (
    "I'm not able to answer that confidently. Could you try rephrasing "
    "your question, or ask about marriage compatibility, career strength, "
    "your current dasha, Sade Sati (Saturn's roughly 7.5-year transit "
    "around your Moon sign), transit timing, or your public image?"
)


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
    if profile.domain == "arudha_lagna":
        return _format_arudha_lagna(profile)
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


def _render_av_timing(block: dict) -> dict:
    """Formats a raw av_transit-shaped block -- {"transit_planet",
    "dasha_envelope", "sub_windows"}, exactly chart_profile.py's
    _build_av_timing_block()'s return contract -- into its rendered form:
    JD floats -> "D Mon YYYY" strings via _format_jd(), sub_windows
    field-mapped with rank order preserved (the convergence/builder layer
    owns ranking; this file never re-sorts).

    Extracted Session 56 (helper-extraction finding, see diagnostics/
    latest_run.md): _format_av_transit()'s own answer_payload assembly
    and _format_career()/_format_dasha()'s OPTIONAL "timing_enrichment"
    key both consume this identical raw shape, so this is shared rather
    than duplicated. Returns the bare 3-key rendered dict every time --
    _format_av_transit() uses it AS this domain's answer_payload verbatim
    (byte-identical output, GOLDEN STAKE GUARD); the enrichment call sites
    add a 4th key ("resolution_note") on top of this function's return
    value themselves -- this function never adds it, so av_transit's own
    output is never at risk of picking it up by accident.

    Callers own empty-sub_windows handling (av_transit fail-closes before
    ever calling this; the enrichment call sites silently drop the whole
    block instead) -- this function does not inspect sub_windows length
    itself, so it must never be called with an empty list.
    """
    transit_planet = block["transit_planet"]
    envelope = block["dasha_envelope"]
    sub_windows = block["sub_windows"]

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
        for window in sub_windows
    ]

    return {
        "transit_planet": transit_planet,
        "dasha_envelope": {
            "mahadasha_lord": envelope["mahadasha_lord"],
            "antardasha_lord": envelope["antardasha_lord"],
            "start": _format_jd(envelope["start_jd"]),
            "end": _format_jd(envelope["end_jd"]),
        },
        "sub_windows": rendered_windows,
    }


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

    # OPTIONAL AV timing enrichment (Session 56). GOLDEN STAKE GUARD: every
    # key/value above this point, plus tier/demotion_reason below, are
    # byte-identical to pre-Session-56 output regardless of whether this
    # block renders -- enrichment is purely additive, never mutates the
    # base answer. Do NOT append enrichment language to demotion_reason.
    # .get(), never indexing -- chart_profile.py's own Session 56
    # degradation lock: the key is legitimately absent whenever the
    # builder's own enrichment attempt failed; the resulting caveat is
    # already carried in profile.stub_caveats by that point, nothing to
    # redo here. NEVER-COLLAPSE GUARD (S54 lock 2, see
    # _format_av_transit()) does NOT apply here -- the builder guarantees
    # sub_windows is non-empty whenever the block itself is present -- but
    # if it somehow arrives empty anyway, this drops the whole block
    # silently (in the S54 guard's own spirit: an envelope with no ranked
    # sub-windows is not renderable) rather than raising, since raising
    # here would defeat the "base answer never blocked" point of this key.
    sources = ("shadbala", "bhava_bala")
    enrichment_block = profile.payload.get("timing_enrichment")
    if enrichment_block is not None and enrichment_block["sub_windows"]:
        rendered_enrichment = _render_av_timing(enrichment_block)
        rendered_enrichment["resolution_note"] = _TIMING_ENRICHMENT_RESOLUTION_NOTE
        answer_payload["timing_enrichment"] = rendered_enrichment
        # sources ONLY grows when the block actually renders (design
        # point 5) -- unchanged from the pre-Session-56 tuple otherwise.
        sources = sources + ("ashtakavarga", "av_transit_scorer", "av_transit_scanner")

    return DomainAnswer(
        domain=profile.domain,
        tier=AnswerTier.TIER_2_RANGE,
        answer_payload=answer_payload,
        stub_caveats=profile.stub_caveats,
        uncertainty_virupa=profile.uncertainty_virupa,
        demotion_reason=None,
        sources=sources,
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

    # OPTIONAL AV timing enrichment (Session 56) -- see _format_career()'s
    # identical block, immediately above, for the full rationale (GOLDEN
    # STAKE GUARD, the .get() degradation-lock convention, and why the
    # never-collapse guard does not apply here); not repeated verbatim.
    sources = ("vimshottari_dasha",)
    enrichment_block = profile.payload.get("timing_enrichment")
    if enrichment_block is not None and enrichment_block["sub_windows"]:
        rendered_enrichment = _render_av_timing(enrichment_block)
        rendered_enrichment["resolution_note"] = _TIMING_ENRICHMENT_RESOLUTION_NOTE
        answer_payload["timing_enrichment"] = rendered_enrichment
        sources = sources + ("ashtakavarga", "av_transit_scorer", "av_transit_scanner")

    return DomainAnswer(
        domain=profile.domain,
        tier=tier,
        answer_payload=answer_payload,
        stub_caveats=profile.stub_caveats,
        uncertainty_virupa=profile.uncertainty_virupa,
        demotion_reason=demotion_reason,
        sources=sources,
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
    it is not a renderable Tier 2 AV-transit answer. Session 56 note:
    this fail-closed guard is intentionally NOT reused by the OPTIONAL
    "timing_enrichment" render in _format_career()/_format_dasha() -- see
    those functions' own comments for why an empty enrichment block is
    silently dropped there instead of raising (this domain is required
    and explicitly requested; enrichment is an optional add-on to a
    different domain's already-valid answer).

    Session 56: envelope/sub_windows rendering itself is now shared with
    the enrichment render path via _render_av_timing() (above) -- this
    function's own output is unchanged (byte-identical, verified by this
    file's own 8-test guard, tests/infra/test_result_formatter_av_transit.py).
    """
    sub_windows = profile.payload["sub_windows"]

    if not sub_windows:
        raise ValueError(
            "result_formatter: av_transit payload has an empty sub_windows "
            "list -- Session 54 locked decision 2 (never-collapse guard) "
            "forbids rendering a dasha envelope without ranked sub-windows"
        )

    answer_payload = _render_av_timing(profile.payload)

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


def _format_arudha_lagna(profile: DomainChartProfile) -> DomainAnswer:
    """Always TIER_1_EXACT, always demotion_reason=None -- mirrors
    _format_sade_sati()'s pattern above: this payload carries no dated
    claims at all (no JD fields anywhere in
    chart_profile.py's build_arudha_lagna_profile() contract), so it never
    inherits current_dasha's/av_transit's drift-language demotion, and this
    branch makes no _format_jd() calls.

    UNREACHABLE VIA ANY LIVE ROUTER PATH as of this branch landing:
    build_arudha_lagna_profile() is a standalone builder, not yet wired
    into build_domain_profile()'s own dispatch, and orchestrator.py's
    _VALID_DOMAINS does not yet admit "arudha_lagna" -- same staged-rollout
    precedent as _format_av_transit()'s Session 55 landing above: this
    branch is dead code until that separate, later wiring lands.

    DEVIATION FLAGGED (Session 59, design-chat decision): the original
    branch spec called for a rendered prose paragraph inside
    answer_payload, but DomainAnswer.answer_payload is documented
    (chart_profile.py) as "deterministic values the formatter renders
    (scores, ranks, date ranges) -- NEVER prose" -- no other branch in
    this file violates that contract. Resolved by keeping answer_payload
    structured-only, verbatim from the payload; a prose rendering, if
    wanted, is a separate concern for a later prompt/layer.

    sources=("padas.py",) is hardcoded here, NOT read from
    profile.payload["sources"] -- matches this file's existing convention
    (every other branch's sources tuple is a formatter-local literal, never
    copied from the payload; see _format_sade_sati/_format_av_transit
    above).

    Missing payload keys are NOT defended against here (existing module
    convention, see _format_marriage/_format_dasha/_format_sade_sati
    above): direct dict indexing raises KeyError with the offending key
    name, never a partial render.
    """
    answer_payload = {
        "arudha_sign": profile.payload["arudha_sign"],
        "lagna_sign": profile.payload["lagna_sign"],
        "lord": profile.payload["lord"],
        "co_lord_deciding_step": profile.payload["co_lord_deciding_step"],
    }

    return DomainAnswer(
        domain=profile.domain,
        tier=AnswerTier.TIER_1_EXACT,
        answer_payload=answer_payload,
        stub_caveats=profile.stub_caveats,
        uncertainty_virupa=profile.uncertainty_virupa,
        demotion_reason=None,
        sources=("padas.py",),
        uncertainty_days=0.0,
    )


def format_refusal(route_result: RouteResult) -> DomainAnswer:
    """Build the user-facing DomainAnswer for a REFUSAL RouteResult.

    Dead code until a later prompt wires orchestrator.answer_question()'s
    REFUSAL branch to call this instead of constructing the DomainAnswer
    inline (see orchestrator.py's current inline REFUSAL construction,
    which this mirrors field-for-field except for the new
    answer_payload["user_message"] key).

    demotion_reason is copied VERBATIM from route_result -- never rewritten,
    never re-worded -- because it is the machine contract downstream code
    (golden-harness substring assertions, _merge_router_demotion's " | "
    concatenation) depends on. answer_payload["user_message"] is a SEPARATE,
    new string: the presentation layer a real user reads. See the
    _REFUSAL_USER_MESSAGES module comment above for the full
    machine-contract-vs-presentation-layer design note (same split as the
    av_transit formatter-owns-strings precedent).

    _REFUSAL_USER_MESSAGES.get(...) with a generic-message default is the
    ONLY defensive/fallback branch in this module, and deliberately so:
    every other function here trusts its payload dict via direct KeyError-
    raising indexing (existing module convention, see _format_marriage/
    _format_dasha/_format_arudha_lagna above) because that payload is an
    internal contract this pipeline's own code assembles end to end. A
    REFUSAL's demotion_reason is different in kind -- it originates from a
    different layer (calc_router.py's classification logic, including two
    REFUSAL paths that interpolate arbitrary keyword/module-name text into
    the string, so no exhaustive fixed key set can ever cover it) and is
    not a payload this module's own contract controls. Falling through to
    a generic safe message here is fail-closed correctness, not a
    convention violation.
    """
    user_message = _REFUSAL_USER_MESSAGES.get(
        route_result.demotion_reason, _GENERIC_REFUSAL_MESSAGE
    )

    return DomainAnswer(
        domain=route_result.domain,
        tier=AnswerTier.REFUSAL,
        answer_payload={"user_message": user_message},
        stub_caveats=(),
        uncertainty_virupa=0.0,
        demotion_reason=route_result.demotion_reason,
        sources=(),
        uncertainty_days=0.0,
    )
