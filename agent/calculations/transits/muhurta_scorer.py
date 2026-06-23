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
- Range-scan composition: find_muhurta_windows() (P2.3.5) now lives in
  this module. Algorithm class: interval algebra over the three sibling
  window-finders (find_chandrabala_windows / find_tarabala_windows /
  find_panchaka_windows) -- NOT a new ephemeris scan. Boundaries are the
  union of the three input window lists' start_jd/end_jd values; each
  resulting sub-interval is scored by calling compute_muhurta_score() at
  its midpoint, reusing the same tier/favorable_count/warnings logic as
  the instant primitive above.
"""

from dataclasses import dataclass
from enum import Enum

from agent.calculations.transits.chandrabala import ChandrabalaCategory, compute_chandrabala
from agent.calculations.transits.panchaka import PanchakaCategory, compute_panchaka
from agent.calculations.transits.tarabala import TarabalaCategory, compute_tarabala
from agent.calculations.transits.chandrabala import find_chandrabala_windows
from agent.calculations.transits.tarabala import find_tarabala_windows
from agent.calculations.transits.panchaka import find_panchaka_windows


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


@dataclass(frozen=True)
class MuhurtaWindow:
    """
    A contiguous time interval with a fixed MuhurtaTier and sub-limb
    statuses. Fields mirror MuhurtaScore inline (not by composition) for
    flat downstream access. Produced by find_muhurta_windows().

    Invariants:
    - start_jd < end_jd always (empty intervals are never emitted)
    - tier, chandrabala, tarabala, panchaka, favorable_count, warnings
      are derived from compute_muhurta_score(midpoint, ...) where
      midpoint = (start_jd + end_jd) / 2.0 -- guaranteed interior to the
      interval, never on a boundary.
    """
    start_jd: float
    end_jd: float
    tier: MuhurtaTier
    chandrabala: ChandrabalaCategory
    tarabala: TarabalaCategory
    panchaka: PanchakaCategory
    is_janma_rashi: bool
    is_janma_tara: bool
    favorable_count: int          # 0-2, Chandrabala + Tarabala only
    warnings: tuple[str, ...]


def find_muhurta_windows(
    natal_moon_sign: int,
    janma_nakshatra: int,
    start_jd: float,
    end_jd: float,
) -> list[MuhurtaWindow]:
    """
    Compose the three Muhurta limb window-finders into a single list of
    MuhurtaWindow objects covering [start_jd, end_jd] exactly, with each
    interval scored via the same tier logic as compute_muhurta_score().

    Algorithm -- interval algebra (not a new ephemeris scan):
    1. Call find_chandrabala_windows(), find_tarabala_windows(),
       find_panchaka_windows() on the same [start_jd, end_jd].
    2. Collect all boundary JDs from all three window lists into a sorted,
       deduplicated set, including start_jd and end_jd themselves.
    3. Iterate consecutive pairs (b0, b1) in the sorted boundary list.
       For each sub-interval:
         midpoint = (b0 + b1) / 2.0
         score = compute_muhurta_score(midpoint, natal_moon_sign,
                                       janma_nakshatra)
         emit MuhurtaWindow(start_jd=b0, end_jd=b1, tier=score.tier,
                            chandrabala=score.chandrabala, ...)
    4. Return the list in ascending time order.

    Guarantees (mirrors sibling finders):
    - windows[0].start_jd == start_jd
    - windows[-1].end_jd == end_jd
    - windows[i].end_jd == windows[i+1].start_jd (contiguous, no gaps)
    - Every window has start_jd < end_jd (no zero-width intervals)
    - Empty list iff start_jd == end_jd

    Args:
        natal_moon_sign:  0=Aries..11=Pisces (chandrabala.py convention).
        janma_nakshatra:  0=Ashwini..26=Revati (tarabala.py convention).
        start_jd:         Julian Day (UT), inclusive lower bound.
        end_jd:           Julian Day (UT), exclusive upper bound.

    Returns:
        List[MuhurtaWindow], ordered ascending by start_jd.

    Raises:
        ValueError: natal_moon_sign not in 0..11, janma_nakshatra not in
            0..26, or start_jd > end_jd.
        EphemerisError: a pyswisseph calculation failed for the Moon
            (propagated from the three sub-finders or compute_muhurta_score).
    """
    # -- input validation (mirrors sibling finders) --
    if not (0 <= natal_moon_sign <= 11):
        raise ValueError(f"natal_moon_sign must be 0..11, got {natal_moon_sign}")
    if not (0 <= janma_nakshatra <= 26):
        raise ValueError(f"janma_nakshatra must be 0..26, got {janma_nakshatra}")
    if start_jd > end_jd:
        raise ValueError(f"start_jd ({start_jd}) > end_jd ({end_jd})")
    if start_jd == end_jd:
        return []

    # -- step 1: collect windows from all three limb finders --
    cb_windows = find_chandrabala_windows(natal_moon_sign, start_jd, end_jd)
    tb_windows = find_tarabala_windows(janma_nakshatra, start_jd, end_jd)
    pk_windows = find_panchaka_windows(start_jd, end_jd)

    # -- step 2: common refinement boundary set --
    boundaries: set[float] = {start_jd, end_jd}
    for w in cb_windows:
        boundaries.add(w.start_jd)
        boundaries.add(w.end_jd)
    for w in tb_windows:
        boundaries.add(w.start_jd)
        boundaries.add(w.end_jd)
    for w in pk_windows:
        boundaries.add(w.start_jd)
        boundaries.add(w.end_jd)
    sorted_boundaries = sorted(boundaries)

    # -- step 3: score each sub-interval at its midpoint --
    result: list[MuhurtaWindow] = []
    for b0, b1 in zip(sorted_boundaries, sorted_boundaries[1:]):
        if b1 <= b0:
            continue  # deduplicate float-equal boundaries defensively
        midpoint = (b0 + b1) / 2.0
        score = compute_muhurta_score(midpoint, natal_moon_sign, janma_nakshatra)
        result.append(
            MuhurtaWindow(
                start_jd=b0,
                end_jd=b1,
                tier=score.tier,
                chandrabala=score.chandrabala,
                tarabala=score.tarabala,
                panchaka=score.panchaka,
                is_janma_rashi=score.is_janma_rashi,
                is_janma_tara=score.is_janma_tara,
                favorable_count=score.favorable_count,
                warnings=score.warnings,
            )
        )

    return result
