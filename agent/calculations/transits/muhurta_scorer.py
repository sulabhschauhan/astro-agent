"""Muhurta composite scorer -- P2.3.5 instant primitive (no range-scan).

Purpose: compose Chandrabala, Tarabala, and Panchaka into a single
MuhurtaScore for a given transit moment and natal pair (natal_moon_sign,
janma_nakshatra). This is the composition point for the three P2.3.1-4
Muhurta limbs -- callers pass natal identifiers and a transit JD;
compute_muhurta_score() calls compute_chandrabala(), compute_tarabala(),
and compute_panchaka() internally, in that order, and does not accept
pre-constructed status objects (it is the aggregator, not a passthrough
wrapper).

LOCKED DECISIONS (P2.3.5):
- Tier mapping rationale -- veto vs. vote asymmetry: Chandrabala and
  Tarabala are both classical Muhurta *limbs*, scored as a vote (PVR
  Ch.36 Section 36.3 names both as criteria an astrologer checks when
  fixing an electional moment; see chandrabala.py / tarabala.py module
  docstrings for the full source ladder on each). Panchaka, by contrast,
  is a taboo/avoidance condition (Muhurtha Chinthamani p.84-85;
  AstroSage / Drik Panchang mainstream convention) -- a window to avoid
  outright, not a positively-named limb contributing a favorable/
  unfavorable vote alongside the other two. This is why Panchaka
  overrides to TIER_3 unconditionally regardless of how favorable
  Chandrabala/Tarabala are, while Chandrabala/Tarabala combine by simple
  favorable-count.
- favorable_count excludes Panchaka by design, not by oversight: it
  counts only Chandrabala + Tarabala FAVORABLE classifications (range
  0-2). It is deliberately NOT decremented when Panchaka vetoes the
  tier to TIER_3 -- the field answers "how many of the two scored limbs
  were favorable", while tier answers "what is the veto-aware composite
  verdict". Keeping them orthogonal lets a downstream LLM reasoning
  trail state "both limbs were favorable but Panchaka blocked this
  muhurta" without re-deriving that fact from the raw sub-statuses.
- warnings is fully deterministic, derived only from the three
  sub-primitives' own boolean/category fields at construction time --
  no free-form text, no LLM involvement anywhere in this module. Fixed
  order: Janma Tara, then Janma Rashi, then Panchaka (see
  compute_muhurta_score's body for the derivation).
- No new deferrals introduced here. Vedha-sthana, aspect overrides,
  NEUTRAL categories (2nd/5th-house Chandrabala, activity-dependent
  Janma Tara), and Panchaka's named-type/Rahita layers all remain
  deferred to V1.1 exactly as locked in chandrabala.py / tarabala.py /
  panchaka.py's own module docstrings -- this module surfaces no new
  deferrals of its own.
- Range-scan composition (scoring all three limbs simultaneously across
  a time window, the Muhurta analog of find_chandrabala_windows /
  find_tarabala_windows / find_panchaka_windows) is explicitly OUT OF
  SCOPE for this module -- a separate follow-up phase. This file ships
  the instant primitive only.
"""

from dataclasses import dataclass
from enum import Enum

from agent.calculations.transits.chandrabala import ChandrabalaCategory, compute_chandrabala
from agent.calculations.transits.panchaka import PanchakaCategory, compute_panchaka
from agent.calculations.transits.tarabala import TarabalaCategory, compute_tarabala


class MuhurtaTier(Enum):
    TIER_1 = "TIER_1"
    TIER_2 = "TIER_2"
    TIER_3 = "TIER_3"


@dataclass(frozen=True)
class MuhurtaScore:
    chandrabala: ChandrabalaCategory
    tarabala: TarabalaCategory
    panchaka: PanchakaCategory
    is_janma_rashi: bool
    is_janma_tara: bool
    tier: MuhurtaTier
    favorable_count: int             # 0-2, Chandrabala + Tarabala only (excludes Panchaka by design)
    warnings: tuple[str, ...]        # derived deterministically, see compute_muhurta_score


def compute_muhurta_score(
    jd_ut: float, natal_moon_sign: int, janma_nakshatra: int
) -> MuhurtaScore:
    """
    Composes Chandrabala, Tarabala, and Panchaka for a single transit
    moment into one MuhurtaScore. Calls compute_chandrabala(),
    compute_tarabala(), compute_panchaka() internally, in that order --
    does not accept pre-constructed status objects (see module
    docstring).

    Args:
        jd_ut: Julian Day (UT) of the moment being evaluated.
        natal_moon_sign: Natal Moon's sidereal sign, 0=Aries..11=Pisces
            (chandrabala.py convention).
        janma_nakshatra: Natal Moon's sidereal nakshatra, 0=Ashwini..
            26=Revati (tarabala.py convention).

    Returns:
        MuhurtaScore with the three sub-limb categories, the two janma
        flags, the veto-aware tier, favorable_count (Chandrabala +
        Tarabala only), and the deterministic warnings tuple.

    Raises:
        ValueError: natal_moon_sign not in 0..11, or janma_nakshatra not
            in 0..26 (raised by compute_chandrabala / compute_tarabala).
        EphemerisError: a pyswisseph calculation failed for the Moon
            (raised by one of the three sub-primitives).
    """
    chandrabala_status = compute_chandrabala(natal_moon_sign, jd_ut)
    tarabala_status = compute_tarabala(janma_nakshatra, jd_ut)
    panchaka_status = compute_panchaka(jd_ut)

    chandrabala_favorable = chandrabala_status.category == ChandrabalaCategory.FAVORABLE
    tarabala_favorable = tarabala_status.category == TarabalaCategory.FAVORABLE
    is_panchak = panchaka_status.category == PanchakaCategory.PANCHAK

    favorable_count = int(chandrabala_favorable) + int(tarabala_favorable)

    if is_panchak:
        tier = MuhurtaTier.TIER_3
    elif favorable_count == 2:
        tier = MuhurtaTier.TIER_1
    elif favorable_count == 1:
        tier = MuhurtaTier.TIER_2
    else:
        tier = MuhurtaTier.TIER_3

    warnings: list[str] = []
    if tarabala_status.is_janma_tara:
        warnings.append("Janma Tara")
    if chandrabala_status.is_janma_rashi:
        warnings.append("Janma Rashi")
    if is_panchak:
        warnings.append("Panchaka")

    return MuhurtaScore(
        chandrabala=chandrabala_status.category,
        tarabala=tarabala_status.category,
        panchaka=panchaka_status.category,
        is_janma_rashi=chandrabala_status.is_janma_rashi,
        is_janma_tara=tarabala_status.is_janma_tara,
        tier=tier,
        favorable_count=favorable_count,
        warnings=tuple(warnings),
    )
