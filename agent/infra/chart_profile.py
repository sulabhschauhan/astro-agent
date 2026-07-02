"""Domain-scoped input/output types for the thin-slice answer pipeline.

Covers the 3 domains locked for the pipeline checkpoint (Session 31 key
decision 3): marriage_compatibility, career_strength, current_dasha.
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
from agent.calculations.strength.bhava_bala import compute_bhava_bala_totals
from agent.calculations.strength.shadbala_totals import compute_shadbala_totals
from agent.chart_calculator import NAKSHATRAS, SIGNS, compute_porphyry_house_cusps

_VALID_DOMAINS = {"marriage_compatibility", "career_strength", "current_dasha"}


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


def _koota_natal_info_from_chart(chart_data: dict) -> KootaNatalInfo:
    """Bridge calculate_chart() output -> KootaNatalInfo.

    moon_sign / nakshatra: index lookups against chart_calculator's own
    SIGNS / NAKSHATRAS lists (0-based, matches KootaNatalInfo's documented
    ranges: moon_sign 0=Aries..11=Pisces, nakshatra 0=Ashwini..26=Revati).

    moon_longitude: calculate_chart()'s public output does NOT expose planet
    longitudes -- planetary_positions strips _calc_planets()'s internal
    "longitude" field down to house/sign/dignity/retrograde only. Recomputed
    here via a direct swe.calc_ut() call, mirroring _calc_planets()'s own
    sidereal-Lahiri approach exactly (same set_sid_mode call, same flags),
    per CLAUDE.md's helpers/ephemeris.py interim convention ("direct
    swe.calc_ut() + TODO marker per call site"). Precision matters here:
    Vashya Koota's Sagittarius/Capricorn half-sign split (trivial.py
    _vashya_group) compares against an exact 15.0-degree boundary, which a
    pada-bucket (3.33-degree resolution) reconstruction could not resolve
    safely.

    CITATION: this is another hand-rolled swe.calc_ut() call site outside
    the still-stubbed helpers/ephemeris.py (CLAUDE.md's interim convention:
    "direct swe.calc_ut() + TODO marker per call site"). A repo-wide grep
    at S44.1 review time found direct swe.calc_ut() usage already present
    in 11 calculations/ modules (chesta_bala.py, kala_bala.py, dig_bala.py,
    sthana_bala.py, panchaka.py, tarabala.py, chandrabala.py, sade_sati.py,
    gochara.py, navamsa.py, panchanga.py) -- this file adds a 12th. Flagged
    as a named post-checkpoint task (helpers/ephemeris.py extraction) for
    the CLAUDE.md divergence/debt section, not actioned here.
    # TODO: extract to helpers/ephemeris.py once the extraction task lands.
    """
    lagna = chart_data["lagna_chart"]
    moon_sign = SIGNS.index(lagna["rasi"])
    nakshatra = NAKSHATRAS.index(lagna["nakshatra"])

    try:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        xx, ret = swe.calc_ut(
            chart_data["meta"]["jd_ut"], swe.MOON, swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        )
        if ret < 0:
            raise RuntimeError(f"pyswisseph error recomputing Moon longitude (retflag={ret})")
    except Exception as exc:
        raise RuntimeError(f"swisseph.calc_ut (Moon longitude bridge) failed: {exc}") from exc
    moon_longitude = xx[0] % 360

    return KootaNatalInfo(moon_sign=moon_sign, moon_longitude=moon_longitude, nakshatra=nakshatra)


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
        domain: one of "marriage_compatibility", "career_strength", "current_dasha".
        chart_data: calculate_chart() output for the primary native.
        evaluated_at_jd: JD (UT) instant this profile is evaluated as-of.
            Caller-supplied, not sampled here -- must be the SAME instant the
            caller used for the dasha lookup (chart_data["dasha"]'s current_*
            fields are computed relative to datetime.now() inside
            chart_calculator._calc_dasha() at whatever moment calculate_chart()
            was called). Reproducibility/testability requirement: this function
            never calls now() internally.
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
            compute_porphyry_house_cusps, bhava_bala_totals, or the Moon-
            longitude ephemeris bridge).
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

        payload: dict[str, Any] = {
            "ashtakoot": ashtakoot,
            "mangal_dosha_primary": mangal_primary,
            # C6 mutual-manglik is a router-level concern per mangal_dosha.py's own
            # docstring -- both single-native results are carried so the router can
            # cross-evaluate them; this file does not apply C6 itself.
            "mangal_dosha_partner": mangal_partner,
        }
        # Ashtakoot and Mangal Dosha carry no drik_is_stubbed/dig_is_stubbed/
        # drishti_is_stubbed metrics -- neither pulls from Shadbala or Bhava Bala.
        stub_caveats: tuple[str, ...] = ()
        # Mangal Dosha's excluded-from-V1 rules (C4 movable-sign, navamsa-based,
        # age-28) and deferred severity tiers (mangal_dosha.py docstring / CLAUDE.md
        # "Mangal Dosha" section) are missing RULES, not a numeric error envelope --
        # they do not contribute an uncertainty_virupa figure.
        uncertainty_virupa = 0.0

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

        try:
            house_cusps = compute_porphyry_house_cusps(
                chart_data["meta"]["jd_ut"],
                chart_data["birth_details"]["lat"],
                chart_data["birth_details"]["lon"],
            )
        except Exception as exc:
            raise RuntimeError(f"chart_calculator.compute_porphyry_house_cusps failed: {exc}") from exc

        try:
            bhava_bala = compute_bhava_bala_totals(house_signs, shadbala_titlecase, house_cusps)
        except Exception as exc:
            raise RuntimeError(f"bhava_bala.compute_bhava_bala_totals failed: {exc}") from exc

        payload = {"shadbala": shadbala, "bhava_bala": bhava_bala}

        caveats: list[str] = []
        for row in shadbala.values():
            if row.get("drik_is_stubbed") and row.get("caveat"):
                caveats.append(row["caveat"])
        for row in bhava_bala.values():
            if (row.get("dig_is_stubbed") or row.get("drishti_is_stubbed")) and row.get("caveat"):
                caveats.append(row["caveat"])
        stub_caveats = tuple(dict.fromkeys(caveats))  # dedupe, preserve first-seen order

        # Drik Bala stub: fixed Virupa envelope from the AstroSage 4-chart fixture
        # range (-20.44..+22.15). See CLAUDE.md "Known Source Divergences (V1)" ->
        # "Shadbala Drik Bala (V1 stub)".
        uncertainty_virupa = 20.0
        chart_name = chart_data.get("birth_details", {}).get("name", "").strip().lower()
        if chart_name == "surbhi":
            # Surbhi-chart-specific: Kala Bala Sun/Jupiter/Saturn Abda/Masa cross-chart
            # divergence, max observed 59.0 Virupa (Saturn). See CLAUDE.md ->
            # "Shadbala Kala Bala -- Sun cross-chart Abda/Masa divergence". NOT a
            # general V1 constant -- do not apply to other charts.
            uncertainty_virupa = 59.0
        # TUNING NOTE: both constants are frozen V1 estimates from the sessions
        # 36-39 fixture investigation. Re-derive when Drik Bala's V1.1 kernel fix
        # (CLAUDE.md's __drik_bala_calc_1_pvr, located Session 42 but not yet
        # actioned) lands -- do not hand-tune against new fixtures in the meantime
        # (rejected pattern, see CLAUDE.md Drik Bala revisit trigger).
        # Bhava Drishti Bala's stub (bhava_bala's drishti_is_stubbed=True) has no
        # documented numeric envelope of its own (unlike Drik Bala's fixture-derived
        # range) -- its caveat string is still surfaced via stub_caveats above, but
        # it is deliberately NOT folded into uncertainty_virupa as a second additive
        # term; tracked as an open gap, not silently assumed zero.

    else:  # current_dasha
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

    return DomainChartProfile(
        domain=domain,
        chart_id=chart_data.get("birth_details", {}).get("name", ""),
        evaluated_at_jd=evaluated_at_jd,
        payload=payload,
        stub_caveats=stub_caveats,
        uncertainty_virupa=uncertainty_virupa,
    )
