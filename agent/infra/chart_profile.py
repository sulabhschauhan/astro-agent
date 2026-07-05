"""Domain-scoped input/output types for the thin-slice answer pipeline.

Covers the 3 domains locked for the pipeline checkpoint (Session 31 key
decision 3): marriage_compatibility, career_strength, current_dasha. Plus
sade_sati (Session 50/P7.2a): a TIER_1_EXACT sub-path for q14-class
questions, carrying ONLY Sade Sati fields (deterministic sign-boundary
ephemeris scan) -- never mahadasha/antardasha fields, and never touching
the general current_dasha payload/uncertainty_days, which stays at its
locked always-TIER_2_RANGE (Session 49/P7.0c "tier = payload property"
lock: current_dasha always carries dated Mahadasha/Antardasha boundaries,
which always carry the documented +/-37-day drift; sade_sati's payload
carries no such dated dasha claims, so it earns its own T1 sub-path
instead of inheriting current_dasha's demotion).
Deterministic T1/T2 output only -- NO LLM synthesis anywhere in this
pipeline (Session 23 V1 lock; any handover text mentioning "Calc Router ->
GPT-4o-mini synthesis" is stale and superseded).

SCOPE BOUNDARY: this module intentionally contains no Calc Router (question
classification -> which domain/calculation modules to call), no Result
Formatter (DomainChartProfile -> DomainAnswer rendering), and no tier-
demotion LOGIC (rank_gap vs. uncertainty_virupa comparison -- that lives in
the router). This file carries the FIELDS those two not-yet-built components
will pass between each other, plus one pure assembly function. Same
stub-with-TODO precedent as calculations/helpers/ephemeris.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

import swisseph as swe

from agent.calculations.compatibility.ashtakoot import compute_ashtakoot_compatibility
from agent.calculations.compatibility.koota_types import AshtakootResult, KootaNatalInfo
from agent.calculations.compatibility.mangal_dosha import compute_mangal_dosha
from agent.calculations.helpers import ephemeris
from agent.calculations.helpers.discrete_scan import find_state_segments
from agent.calculations.strength.bhava_bala import compute_bhava_bala_totals
from agent.calculations.strength.shadbala_totals import compute_shadbala_totals
from agent.calculations.transits.sade_sati import compute_sade_sati
from agent.chart_calculator import NAKSHATRAS, SIGNS, compute_porphyry_house_cusps

_VALID_DOMAINS = {
    "marriage_compatibility",
    "career_strength",
    "current_dasha",
    "sade_sati",
}

# career_strength's compute_bhava_bala_totals() call needs planet_lons
# (Session 53 bhava_bala.py signature change, for compute_bhava_drishti_bala) --
# title-case to match bhava_bala.py/drik_bala.py's classification helpers.
_CAREER_PLANET_SWE_IDS: dict[str, int] = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
    "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS, "Saturn": swe.SATURN,
}

# THRESHOLD DISCIPLINE (CLAUDE.md Working Style #4) -- both constants below
# size _sade_sati_adjacent_cycle_boundaries()'s find_state_segments() scan.
#
# Justification (scan width): Saturn's sidereal orbital period is ~29.4571
# years (standard astronomical value) -- a Sade Sati cycle for a fixed
# natal Moon sign recurs exactly once per Saturn orbit, so scanning
# +/-40 years from evaluated_at_jd guarantees at least one full recurrence
# in each direction with real margin, regardless of exactly where within
# the ~22y inter-cycle gap evaluated_at_jd happens to fall. Scope guard:
# assumes a human-lifetime query horizon (any live query's evaluated_at_jd
# realistically sits within a natal chart's own lifespan); NOT validated
# for a cycle boundary sought >40y from evaluated_at_jd. Revisit trigger:
# if a real query needs a boundary outside this range, widen deliberately,
# don't assume 40y is always enough.
_SADE_SATI_ADJACENT_CYCLE_SCAN_YEARS = 40

# Justification (scan step): matches sade_sati.py's own _find_segments()
# daily-resolution scan EXACTLY, for the identical state (Saturn sidereal
# sign membership in {rising, peak, setting}-from-natal-Moon) -- that
# granularity is Session 20+ validated (via Sheridan/Surbhi's real
# reference charts) as sufficient to catch retrograde double-ingress
# segments without missing a contiguous occupancy. Reusing that
# already-validated precedent rather than independently guessing a
# coarser (cheaper but unvalidated) step.
_SADE_SATI_SCAN_STEP_DAYS = 1.0


class AnswerTier(Enum):
    """Confidence-tier architecture (Session 19 lock).

    Only TIER_1_EXACT / TIER_2_RANGE are ever produced by this V1 pipeline.
    TIER_3_MUHURTA, TIER_4_INTERPRETIVE, and REFUSAL are included so the enum
    schema never needs reopening when the router later adds demotion/refusal
    handling -- they are NOT wired to anything in this file.
    """

    TIER_1_EXACT = "TIER_1_EXACT"                  # single deterministic value; no stub touches its basis
    TIER_2_RANGE = "TIER_2_RANGE"                  # deterministic value carrying an uncertainty_virupa envelope
    TIER_3_MUHURTA = "TIER_3_MUHURTA"              # personalized muhurta scoring; out of THIS pipeline's scope (marriage/career/dasha only)
    TIER_4_INTERPRETIVE = "TIER_4_INTERPRETIVE"    # LLM-generated interpretive Q&A; OUT for V1 (Session 23 lock) -- AstroSage paragraph + palm are the interpretive surface
    REFUSAL = "REFUSAL"                            # no safe deterministic answer; not produced by this pipeline in V1


@dataclass(frozen=True)
class DomainChartProfile:
    """Per-domain assembled snapshot of everything the router/formatter will need."""

    domain: str                        # "marriage_compatibility" | "career_strength" | "current_dasha"
    chart_id: str                      # primary native's birth_details.name (chart_data's own identity, not partner's)
    evaluated_at_jd: float             # JD (UT) instant this profile is evaluated as-of; caller-supplied, see build_domain_profile
    payload: dict[str, Any]            # domain-specific raw results, stored as-is (see build_domain_profile branches)
    stub_caveats: tuple[str, ...]      # every True-flagged drik/dig/drishti stub caveat, verbatim, deduped
    uncertainty_virupa: float          # max known error envelope across this domain's contributing metrics
    # Time-axis envelope, currently only the current_dasha domain -- +/-37.0
    # days documented Antardasha drift vs AstroSage (see chart_calculator.py's
    # _calc_dasha DASHA ACCURACY NOTE). Virupa and day envelopes are
    # orthogonal axes; router demotion logic must check BOTH (rank_gap vs
    # virupa; boundary proximity vs days).
    uncertainty_days: float = 0.0


@dataclass(frozen=True)
class DomainAnswer:
    """Output contract for the not-yet-built Result Formatter.

    Fixes the target shape so downstream work has something concrete to
    build against; this module does not construct DomainAnswer instances
    itself.
    """

    domain: str
    tier: AnswerTier
    answer_payload: dict[str, Any]     # deterministic values the formatter renders (scores, ranks, date ranges) -- NEVER prose
    stub_caveats: tuple[str, ...]      # carried from profile, mandatory
    uncertainty_virupa: float
    demotion_reason: str | None        # always None here; router sets it when rank_gap <= uncertainty_virupa forces T1->T2
    sources: tuple[str, ...]           # contributing module names, for audit
    # Time-axis envelope, currently only the current_dasha domain -- +/-37.0
    # days documented Antardasha drift vs AstroSage (see chart_calculator.py's
    # _calc_dasha DASHA ACCURACY NOTE). Virupa and day envelopes are
    # orthogonal axes; router demotion logic must check BOTH (rank_gap vs
    # virupa; boundary proximity vs days). Placed last, not directly after
    # uncertainty_virupa, because demotion_reason/sources (no defaults)
    # already follow uncertainty_virupa here -- a defaulted field cannot
    # precede them without breaking Python's dataclass field-ordering rule.
    uncertainty_days: float = 0.0


def _koota_natal_info_from_chart(chart_data: dict) -> KootaNatalInfo:
    """Bridge calculate_chart() output -> KootaNatalInfo.

    moon_sign / nakshatra: index lookups against chart_calculator's own
    SIGNS / NAKSHATRAS lists (0-based, matches KootaNatalInfo's documented
    ranges: moon_sign 0=Aries..11=Pisces, nakshatra 0=Ashwini..26=Revati).

    moon_longitude: calculate_chart()'s public output does NOT expose planet
    longitudes -- planetary_positions strips _calc_planets()'s internal
    "longitude" field down to house/sign/dignity/retrograde only. Recomputed
    here via helpers/ephemeris.py's sidereal_longitude() (Session 52
    migration), matching _calc_planets()'s own sidereal-Lahiri convention.
    Precision matters here: Vashya Koota's Sagittarius/Capricorn half-sign
    split (trivial.py _vashya_group) compares against an exact 15.0-degree
    boundary, which a pada-bucket (3.33-degree resolution) reconstruction
    could not resolve safely.
    """
    lagna = chart_data["lagna_chart"]
    moon_sign = SIGNS.index(lagna["rasi"])
    nakshatra = NAKSHATRAS.index(lagna["nakshatra"])

    moon_longitude = ephemeris.sidereal_longitude(chart_data["meta"]["jd_ut"], swe.MOON)

    return KootaNatalInfo(moon_sign=moon_sign, moon_longitude=moon_longitude, nakshatra=nakshatra)


def _saturn_sidereal_sign(jd_ut: float) -> int:
    """Saturn's sidereal sign (0=Aries..11=Pisces) at jd_ut.

    Direct swe.calc_ut (via helpers/ephemeris.py, Session 52 migration),
    NOT sade_sati.compute_sade_sati() -- that function runs two full
    multi-year ephemeris window scans per call (~0.8s each, measured),
    which would make the 80-year find_state_segments() scan in
    _sade_sati_adjacent_cycle_boundaries() below prohibitively slow (tens
    of seconds). This mirrors sade_sati.py's own private _saturn_sign()
    formula exactly (same //30 bucketing) -- read that function's source
    before reimplementing here rather than importing it, since it is
    module-private.
    """
    return int(ephemeris.sidereal_longitude(jd_ut, swe.SATURN) / 30.0) % 12


def _sade_sati_adjacent_cycle_boundaries(
    natal_moon_sign: int, evaluated_at_jd: float
) -> tuple[float | None, float | None]:
    """Finds (previous_cycle_end_jd, next_cycle_start_jd) via a cheap
    find_state_segments() scan over Saturn sidereal-sign membership in
    {rising, peak, setting}-from-natal-Moon (sade_sati.py's own phase
    taxonomy). Works uniformly whether or not evaluated_at_jd itself falls
    inside a currently-active cycle -- a segment containing evaluated_at_jd
    is excluded from both searches below by construction (its end_jd is
    strictly > evaluated_at_jd since find_state_segments' end_jd is
    exclusive, and its start_jd is <= evaluated_at_jd), so this correctly
    finds the ADJACENT cycles on either side, not the current one.

    Deliberately NOT implemented by calling sade_sati.compute_sade_sati()
    repeatedly at candidate anchors: that function's macro_sade_sati is
    only populated when the probed JD itself falls inside a cycle's own
    [start, end] span (not merely within its own +/-10y scan window) --
    verified empirically before choosing this approach. A period-shifted
    single-probe anchor works when currently active (the shifted JD lands
    exactly on the adjacent cycle's own boundary, by orbital periodicity)
    but is provably wrong when not active (aliases back into the same
    inter-cycle gap). This scan-based approach was cross-validated against
    that period-shift result on an active-case fixture (sub-0.1-day
    agreement) and against golden q14's verified not-active values for
    Sulabh (previous_cycle_end 24 Jan 2020, next_cycle_start 27 Jan 2041,
    both within 1 day) before being adopted as the single mechanism for
    both cases.

    Returns (None, None) components for whichever side has no adjacent
    cycle within the scan bound (see _SADE_SATI_ADJACENT_CYCLE_SCAN_YEARS).
    """
    rising_sign = (natal_moon_sign - 1) % 12
    setting_sign = (natal_moon_sign + 1) % 12
    active_signs = {rising_sign, natal_moon_sign, setting_sign}

    def _is_active_sign(jd_ut: float) -> bool:
        return _saturn_sidereal_sign(jd_ut) in active_signs

    scan_lo_jd = evaluated_at_jd - _SADE_SATI_ADJACENT_CYCLE_SCAN_YEARS * 365.25
    scan_hi_jd = evaluated_at_jd + _SADE_SATI_ADJACENT_CYCLE_SCAN_YEARS * 365.25
    segments = find_state_segments(_is_active_sign, scan_lo_jd, scan_hi_jd, _SADE_SATI_SCAN_STEP_DAYS)

    previous_cycle_end_jd: float | None = None
    next_cycle_start_jd: float | None = None
    for seg in segments:
        if not seg.state:
            continue
        if seg.end_jd <= evaluated_at_jd:
            previous_cycle_end_jd = seg.end_jd  # segments are time-ordered; last write wins
        if seg.start_jd >= evaluated_at_jd and next_cycle_start_jd is None:
            next_cycle_start_jd = seg.start_jd  # first match only

    return previous_cycle_end_jd, next_cycle_start_jd


def build_domain_profile(
    domain: str,
    chart_data: dict,
    evaluated_at_jd: float,
    *,
    partner_chart_data: dict | None = None,
    primary_role: Literal["boy", "girl"] | None = None,
) -> DomainChartProfile:
    """Pure assembly: pack pre-computed/live-called module outputs into DomainChartProfile.

    Args:
        domain: one of "marriage_compatibility", "career_strength",
            "current_dasha", "sade_sati".
        chart_data: calculate_chart() output for the primary native.
        evaluated_at_jd: JD (UT) instant this profile is evaluated as-of.
            Caller-supplied, not sampled here -- must be the SAME instant the
            caller used for the dasha lookup (chart_data["dasha"]'s current_*
            fields are computed relative to datetime.now() inside
            chart_calculator._calc_dasha() at whatever moment calculate_chart()
            was called). Reproducibility/testability requirement: this function
            never calls now() internally. For domain="sade_sati", this same
            instant is passed directly to sade_sati.compute_sade_sati() as
            transit_jd -- Sade Sati has no "as-of a different moment" concept
            of its own to reconcile against.
        partner_chart_data: calculate_chart() output for the second native.
            Required (and only accepted) for domain="marriage_compatibility" --
            Ashtakoot (compute_ashtakoot_compatibility) needs two natives.
        primary_role: "boy" or "girl" -- which role chart_data plays. Required
            for marriage_compatibility; Ashtakoot's kootas (Varna/Vashya/Tara)
            score directionally (bride vs. groom), so there is no safe default.

    Raises:
        ValueError: domain not recognised; marriage_compatibility called
            without partner_chart_data/primary_role; or partner_chart_data/
            primary_role supplied for a non-marriage domain.
        RuntimeError: a wrapped, module-named failure from any underlying
            calculation call (ashtakoot, mangal_dosha, shadbala_totals,
            compute_porphyry_house_cusps, bhava_bala_totals, sade_sati.
            compute_sade_sati, or the Moon-longitude ephemeris bridge).
    """
    if domain not in _VALID_DOMAINS:
        raise ValueError(f"domain must be one of {sorted(_VALID_DOMAINS)}, got {domain!r}")

    if domain == "marriage_compatibility":
        if partner_chart_data is None:
            raise ValueError(
                "marriage_compatibility requires partner_chart_data -- "
                "Ashtakoot needs both natives, no single-chart fallback"
            )
        if primary_role is None:
            raise ValueError(
                "marriage_compatibility requires primary_role ('boy' or 'girl') -- "
                "Ashtakoot kootas (Varna/Vashya/Tara) score directionally; "
                "there is no safe default role"
            )
    elif partner_chart_data is not None or primary_role is not None:
        raise ValueError(
            f"{domain!r} does not accept partner_chart_data/primary_role "
            f"(marriage_compatibility-only kwargs)"
        )

    if domain == "marriage_compatibility":
        primary_koota = _koota_natal_info_from_chart(chart_data)
        partner_koota = _koota_natal_info_from_chart(partner_chart_data)
        boy, girl = (
            (primary_koota, partner_koota)
            if primary_role == "boy"
            else (partner_koota, primary_koota)
        )

        try:
            ashtakoot: AshtakootResult = compute_ashtakoot_compatibility(boy, girl)
        except Exception as exc:
            raise RuntimeError(f"ashtakoot.compute_ashtakoot_compatibility failed: {exc}") from exc

        try:
            mangal_primary = compute_mangal_dosha(chart_data)
        except Exception as exc:
            raise RuntimeError(f"mangal_dosha.compute_mangal_dosha (primary) failed: {exc}") from exc
        try:
            mangal_partner = compute_mangal_dosha(partner_chart_data)
        except Exception as exc:
            raise RuntimeError(f"mangal_dosha.compute_mangal_dosha (partner) failed: {exc}") from exc

        # Role-keyed, not primary/partner-keyed: DomainChartProfile carries no
        # primary_role field, so boy/girl must be resolved here -- the Result
        # Formatter (S44.4) needs Ashtakoot-consistent boy/girl labels.
        if primary_role == "boy":
            mangal_boy, mangal_girl = mangal_primary, mangal_partner
        else:
            mangal_boy, mangal_girl = mangal_partner, mangal_primary

        payload: dict[str, Any] = {
            "ashtakoot": ashtakoot,
            "mangal_dosha_boy": mangal_boy,
            # C6 mutual-manglik is a router-level concern per mangal_dosha.py's own
            # docstring -- both single-native results are carried so the router can
            # cross-evaluate them; this file does not apply C6 itself.
            "mangal_dosha_girl": mangal_girl,
        }
        # Ashtakoot and Mangal Dosha carry no drik_is_stubbed/dig_is_stubbed/
        # drishti_is_stubbed metrics -- neither pulls from Shadbala or Bhava Bala.
        stub_caveats: tuple[str, ...] = ()
        # Mangal Dosha's excluded-from-V1 rules (C4 movable-sign, navamsa-based,
        # age-28) and deferred severity tiers (mangal_dosha.py docstring / CLAUDE.md
        # "Mangal Dosha" section) are missing RULES, not a numeric error envelope --
        # they do not contribute an uncertainty_virupa figure.
        uncertainty_virupa = 0.0
        uncertainty_days = 0.0  # no time-axis envelope for this domain

    elif domain == "career_strength":
        try:
            shadbala = compute_shadbala_totals(chart_data)
        except Exception as exc:
            raise RuntimeError(f"shadbala_totals.compute_shadbala_totals failed: {exc}") from exc

        # Canonical lowercase(shadbala_totals.py) -> Title-case(SIGN_LORDS/bhava_bala.py)
        # bridge -- single documented point per bhavadhipati_bala's own casing-contract
        # docstring (mirrors test_bhava_bala.py::test_e_live_compute_wiring_smoke).
        # Do NOT add per-callsite .capitalize() calls elsewhere; this cleanup is
        # tracked as a future pass, not re-solved ad hoc per caller.
        shadbala_titlecase = {p.capitalize(): shadbala[p]["shadbala_virupa"] for p in shadbala}

        house_signs = {entry["house"]: entry["sign"] for entry in chart_data["house_lord_mapping"]}
        jd_ut = chart_data["meta"]["jd_ut"]

        try:
            house_cusps = compute_porphyry_house_cusps(
                jd_ut,
                chart_data["birth_details"]["lat"],
                chart_data["birth_details"]["lon"],
            )
        except Exception as exc:
            raise RuntimeError(f"chart_calculator.compute_porphyry_house_cusps failed: {exc}") from exc

        # Session 53: compute_bhava_bala_totals now needs planet_lons for
        # compute_bhava_drishti_bala. Delegates to helpers/ephemeris.py
        # (Session 52 convention) rather than a new direct swe.calc_ut call.
        try:
            planet_lons = {
                name: ephemeris.sidereal_longitude(jd_ut, swe_id)
                for name, swe_id in _CAREER_PLANET_SWE_IDS.items()
            }
        except ephemeris.EphemerisError as exc:
            raise RuntimeError(
                f"helpers.ephemeris.sidereal_longitude failed (career_strength "
                f"planet_lons): {exc}"
            ) from exc

        try:
            bhava_bala = compute_bhava_bala_totals(
                house_signs, shadbala_titlecase, house_cusps, planet_lons
            )
        except Exception as exc:
            raise RuntimeError(f"bhava_bala.compute_bhava_bala_totals failed: {exc}") from exc

        if "house_lord_mapping" not in chart_data:
            raise ValueError(
                "career_strength requires chart_data['house_lord_mapping'] "
                "(set by chart_calculator.calculate_chart()) to resolve the 10th house lord"
            )
        tenth_lord_entry = next(
            (entry for entry in chart_data["house_lord_mapping"] if entry["house"] == 10),
            None,
        )
        if tenth_lord_entry is None:
            raise ValueError("career_strength: house_lord_mapping has no entry for house 10")

        payload = {
            "shadbala": shadbala,
            "bhava_bala": bhava_bala,
            "tenth_lord": tenth_lord_entry["lord"].lower(),
        }

        caveats: list[str] = []
        for row in shadbala.values():
            if row.get("caveat"):
                caveats.append(row["caveat"])
        # bhava_bala's dig_is_stubbed/drishti_is_stubbed are now BOTH always
        # False (Bhava Dig Bala real since Session 42; Bhava Drishti Bala
        # real since Session 53, AstroSage-validated 48/48 houses within
        # ±0.16 Virupa max |delta| -- see bhava_bala.py's
        # compute_bhava_drishti_bala CITATION) -- this loop is a no-op today
        # but left in place (not deleted) in case either component is ever
        # re-stubbed for a future divergence investigation.
        for row in bhava_bala.values():
            if (row.get("dig_is_stubbed") or row.get("drishti_is_stubbed")) and row.get("caveat"):
                caveats.append(row["caveat"])
        stub_caveats = tuple(dict.fromkeys(caveats))  # dedupe, preserve first-seen order

        # 2.0 = general uncertainty envelope, lowered from 6.0 Session 47.
        # Ayana Bala Kranti RESOLVED Session 47 (Sayana-longitude Kranti, fixed
        # 24 deg obliquity, Raman Art. 72-73; validated +/-0.45 vs AstroSage,
        # 28/28 cells, 4 charts) -- see CLAUDE.md "Known Source Divergences
        # (V1)" -> "Ayana Bala Kranti". Envelope basis = AstroSage parity
        # (user-perceived correctness wins per the tiebreaker principle,
        # CLAUDE.md Locked Decisions). Drik Bala no longer contributes (real
        # since Session 46, 28/28 JHora parity +/-0.5).
        # SCOPE GUARD: Chesta Bala AstroSage-parity validated Sulabh/Surbhi
        # only (Sheridan/David remain a documented divergence, see CLAUDE.md
        # "Chesta Bala cross-chart divergence") -- this 2.0 general envelope
        # does not extend Chesta parity claims beyond that validated scope.
        uncertainty_virupa = 2.0
        chart_name = chart_data.get("birth_details", {}).get("name", "").strip().lower()
        if chart_name == "surbhi":
            # SCOPE GUARD: applies to non-Surbhi charts only. Surbhi-chart-specific:
            # Kala Bala Sun/Jupiter/Saturn Abda/Masa cross-chart divergence, max
            # observed 59.0 Virupa (Saturn). See CLAUDE.md -> "Shadbala Kala Bala --
            # Sun cross-chart Abda/Masa divergence". Takes precedence over the
            # general 2.0 envelope above -- NOT a general constant, do not apply
            # elsewhere, UNCHANGED by this Session 47 update.
            uncertainty_virupa = 59.0
        # TUNING NOTE: a breach beyond 2.0 on any future chart means
        # investigate before widening back up -- do not silently re-relax.
        # Bhava Drishti Bala is real since Session 53 (AstroSage-validated,
        # 48/48 houses within ±0.16 Virupa max |delta| -- see bhava_bala.py's
        # compute_bhava_drishti_bala CITATION); drishti_is_stubbed is now
        # always False, so no caveat surfaces for it via stub_caveats above.
        # It never had its own uncertainty_virupa constant to begin with
        # (confirmed: it was never folded into the 2.0 Ayana envelope above
        # even while stubbed), so this uncertainty_virupa value is unchanged
        # by drishti going real -- not touched here (threshold discipline).
        uncertainty_days = 0.0  # no time-axis envelope for this domain

    elif domain == "current_dasha":
        dasha = chart_data["dasha"]
        payload = {
            "current_mahadasha": dasha.get("current_mahadasha"),
            "current_antardasha": dasha.get("current_antardasha"),
            "next_5_antardashas": dasha.get("next_5_antardashas"),
            "next_3_mahadashas": dasha.get("next_3_mahadashas"),
            # current_pratyantar / next_5_pratyantars deliberately excluded --
            # chart_calculator.py's own _calc_dasha() comment: "Not surfaced to
            # users -- +/-37-day drift causes wrong lord at Pratyantar granularity."
        }
        stub_caveats = ()
        uncertainty_virupa = 0.0
        # +/-37.0 days documented Antardasha drift vs AstroSage -- see
        # chart_calculator.py's _calc_dasha DASHA ACCURACY NOTE. Boundary
        # proximity (is evaluated_at_jd near a period transition?) is NOT
        # computed here -- that comparison is router logic (S44.3).
        uncertainty_days = 37.0

    else:  # sade_sati (Session 50/P7.2a) -- NO mahadasha/antardasha fields
        # here; this is a payload-property-consistent T1 sub-path, distinct
        # from current_dasha's always-T2 payload (module docstring above).
        natal_moon_sign = SIGNS.index(chart_data["lagna_chart"]["rasi"])

        try:
            current_status = compute_sade_sati(natal_moon_sign, evaluated_at_jd)
        except Exception as exc:
            raise RuntimeError(f"sade_sati.compute_sade_sati (current) failed: {exc}") from exc

        # "Current cycle" = the whole ~7.5y Sade Sati envelope
        # (macro_sade_sati), not the current sub-phase's own narrower
        # window -- consistent with "previous cycle"/"next cycle" below,
        # which are also envelope-level, not sub-phase-level.
        current_cycle_start_jd = None
        current_cycle_end_jd = None
        if current_status.active and current_status.macro_sade_sati is not None:
            current_cycle_start_jd = current_status.macro_sade_sati.overall_start_jd
            current_cycle_end_jd = current_status.macro_sade_sati.overall_end_jd

        # Previous/next cycle: compute_sade_sati()'s own macro_sade_sati only
        # ever reports the ONE envelope containing its transit_jd argument
        # (verified empirically -- see _sade_sati_adjacent_cycle_boundaries'
        # own docstring for why a compute_sade_sati()-repeated-probe design
        # was tried and rejected). Uses the cheap find_state_segments()-based
        # scan instead, uniformly for both the active and not-active cases.
        try:
            previous_cycle_end_jd, next_cycle_start_jd = _sade_sati_adjacent_cycle_boundaries(
                natal_moon_sign, evaluated_at_jd
            )
        except Exception as exc:
            raise RuntimeError(
                f"chart_profile._sade_sati_adjacent_cycle_boundaries failed: {exc}"
            ) from exc

        payload = {
            "active": current_status.active,
            "phase": current_status.phase,
            "current_cycle_start_jd": current_cycle_start_jd,
            "current_cycle_end_jd": current_cycle_end_jd,
            "previous_cycle_end_jd": previous_cycle_end_jd,
            "next_cycle_start_jd": next_cycle_start_jd,
        }
        stub_caveats = ()
        uncertainty_virupa = 0.0
        # Deterministic sign-ingress ephemeris scan (compute_sade_sati's own
        # bisection refinement, <60s precision per its own docstring) -- NO
        # documented cross-source (AstroSage/JHora) parity envelope exists
        # for Sade Sati boundary dates, unlike current_dasha's +/-37-day
        # drift. 0.0 here is "no envelope documented yet", NOT "verified
        # zero-error" -- do not conflate with current_dasha's uncertainty_days
        # semantics. Revisit if a future cross-oracle study documents one.
        uncertainty_days = 0.0

    return DomainChartProfile(
        domain=domain,
        chart_id=chart_data.get("birth_details", {}).get("name", ""),
        evaluated_at_jd=evaluated_at_jd,
        payload=payload,
        stub_caveats=stub_caveats,
        uncertainty_virupa=uncertainty_virupa,
        uncertainty_days=uncertainty_days,
    )
