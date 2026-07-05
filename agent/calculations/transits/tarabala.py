"""Tarabala -- transit Moon's nakshatra position from natal nakshatra (instant primitive).

Purpose: classify the transit Moon's current nakshatra-count position (from
the native's janma nakshatra) as FAVORABLE or UNFAVORABLE for muhurta/
electional use, per the mainstream 9-tara (Tarabala) convention.

LOCKED DECISIONS (P2.3.3):
- Source ladder: PVR Ch. 36 Section 36.3 "Basics of Muhurta" (Muhurta
  chapter primary endorsement, NOT the transit chapter) names Tarabala
  as one of the limbs an astrologer checks when fixing a muhurta --
  "The nakshatra occupied by Moon at the time of a muhurta should be a
  good tara with respect to janma nakshatra." (PDF p.484, printed p.472).
  PVR does not enumerate the 9 tara names or give a favorable/unfavorable
  table anywhere in this passage; Table 79 "Muhurta guidelines" (PDF
  pp.485-486, printed pp.473-474) lists specific good Nakshatras per task
  instead of a generic tara-relative-to-janma-nakshatra column. The
  9-tara enum and its FAVORABLE/UNFAVORABLE split implemented here come
  from mainstream Muhurta lineage (AstroSage / Drik Panchang / Muhurta
  Chintamani convention), with PVR Ch.36 Section 36.3 establishing only
  that Tarabala-as-a-concept is a named, primary-chapter Muhurta limb --
  same source-ladder shape as chandrabala.py (mainstream criterion,
  PVR-corroborated existence, not a PVR-derived formula).
- 9-tara cycle, counted from janma nakshatra (nakshatra_count 1-27,
  tara_number = ((nakshatra_count - 1) % 9) + 1):
    1 Janma     -- UNFAVORABLE
    2 Sampat    -- FAVORABLE
    3 Vipat     -- UNFAVORABLE
    4 Kshema    -- FAVORABLE
    5 Pratyari  -- UNFAVORABLE
    6 Sadhaka   -- FAVORABLE
    7 Vadha     -- UNFAVORABLE
    8 Mitra     -- FAVORABLE
    9 Ati-mitra -- FAVORABLE
- Janma Tara (nakshatra_count in {1, 10, 19} -- i.e. tara_number == 1)
  is UNFAVORABLE under this binary classification. Surfaced via
  is_janma_tara: bool so the answer-pipeline can name it explicitly
  without fragmenting the enum -- same shape as chandrabala.py's
  is_janma_rashi, though there the equivalent case (transit Moon back on
  its own natal sign) is FAVORABLE, not UNFAVORABLE; the two modules
  deliberately diverge here because the classical conventions for the
  two limbs diverge (Janma Rashi auspicious, Janma Tara inauspicious).
- Binary category only: FAVORABLE / UNFAVORABLE. No NEUTRAL bucket.
  Conditional/activity-dependent refinement of Janma Tara (some lineages
  treat Janma as situationally usable) is explicitly DEFERRED to V1.1 --
  mirrors chandrabala.py's 2nd/5th-from-Moon NEUTRAL-category deferral
  precedent (see that module's docstring).
- No vedha-sthana (obstruction) analog -- Tarabala's classical
  formulation has no per-tara obstruction mechanism comparable to
  Chandrabala's vedha-sthana column in PVR Table 63, so there is nothing
  to defer here; this is a difference in classical scope between the two
  limbs, not an oversight.
- Nakshatra convention: 0-26 internally (0=Ashwini .. 26=Revati), matching
  panchanga.py's NAKSHATRA_NAMES indexing. nakshatra_count (1-27) and
  tara_number (1-9) are surfaced on the dataclass for classical display;
  internal arithmetic stays 0-indexed throughout.
- Ephemeris dependency: independent _moon_nakshatra(jd_ut) helper, NOT a
  call into chandrabala.py's _moon_sign() or any other cross-module
  dependency -- avoids cross-module coupling, same rationale as
  chandrabala.py's _moon_sign() vs gochara.compute_gochara(). swe
  convention now delegated to helpers/ephemeris.py (Session 52 migration);
  _moon_nakshatra itself remains a thin per-module wrapper.
- V1 scope: instant primitive + range-scan only, this single file, no
  Panchaka (P2.3.4) hooks and no Chandrabala+Tarabala composite/
  aggregation hooks -- deferred to the Muhurta composite phase.

Range-scan (P2.3.3 continued):
- find_tarabala_windows(natal_nakshatra, start_jd, end_jd) returns the
  contiguous (category, is_janma_tara, tara_number, nakshatra_count,
  transit_nakshatra) windows covering [start_jd, end_jd]. Same enum
  source ladder as the instant primitive above.
- Algorithm: discrete-state bisection, the same shape as
  chandrabala.py's find_chandrabala_windows (which itself mirrors
  Skyfield's almanac.find_discrete; skyfield itself is NOT a dependency).
  Reimplemented independently in this module (_bisect_transition is NOT
  imported from chandrabala.py -- same cross-module-coupling rationale
  as the ephemeris helper above). Coarse scan at a fixed, internal-only
  0.5 JD (12h) step: Moon's sidereal angular speed is ~13 deg/day, so
  13 * 0.5 = 6.5 deg < 13.333 deg (360/27, one nakshatra width) -- no
  nakshatra ingress can be skipped between two consecutive coarse
  samples (narrower margin than chandrabala.py's 30-deg sign width, but
  still safe). Each detected state change is then bisected down to
  1e-6 JD (~0.09s) precision, same constant value as chandrabala.py,
  independently justified here (precision target is domain-independent).
  Neither constant is exposed on the public surface.
- Unlike sade_sati.py's Saturn-transit scan, the Moon never retrogrades,
  so nakshatra ingress is strictly monotonic forward in time -- no
  retrograde-double-ingress handling is needed here, same as
  chandrabala.py's range-scan.
- Bisects on the (category, is_janma_tara, tara_number) triple. This is
  narrower than it looks: category and is_janma_tara are both
  deterministic functions of tara_number alone, so the triple reduces to
  "did tara_number change". tara_number = ((nakshatra_count - 1) % 9) + 1
  and nakshatra_count advances by exactly 1 at every Moon nakshatra
  ingress (no skipping, no retrograde) -- consecutive integers are never
  congruent mod 9, so tara_number changes at *every* nakshatra ingress,
  not just at tara-cycle boundaries. Detecting a tara_number change is
  therefore equivalent to detecting a nakshatra ingress directly, the
  same "bijective for fixed natal value" equivalence chandrabala.py's
  docstring notes for house_from_natal_moon vs transit_moon_sign. The
  full per-window nakshatra_count / transit_nakshatra fields are read
  from the coarse sample's own compute_tarabala() result at each
  boundary, not re-derived from the triple.
- Reuses compute_tarabala / _moon_nakshatra from the instant primitive
  above -- no duplicated ephemeris or classification logic.
"""

from dataclasses import dataclass
from enum import Enum

import swisseph as swe

from agent.calculations.helpers import ephemeris
from agent.calculations.helpers.discrete_scan import find_state_segments

_NAK_SPAN = 360.0 / 27.0

_JANMA_TARA_COUNTS = frozenset({1, 10, 19})
_FAVORABLE_TARA_NUMBERS = frozenset({2, 4, 6, 8, 9})


class TaraName(Enum):
    JANMA = "JANMA"
    SAMPAT = "SAMPAT"
    VIPAT = "VIPAT"
    KSHEMA = "KSHEMA"
    PRATYARI = "PRATYARI"
    SADHAKA = "SADHAKA"
    VADHA = "VADHA"
    MITRA = "MITRA"
    ATI_MITRA = "ATI_MITRA"


# Index 0 = tara_number 1 .. index 8 = tara_number 9.
_TARA_NAMES_BY_NUMBER: tuple[TaraName, ...] = (
    TaraName.JANMA,
    TaraName.SAMPAT,
    TaraName.VIPAT,
    TaraName.KSHEMA,
    TaraName.PRATYARI,
    TaraName.SADHAKA,
    TaraName.VADHA,
    TaraName.MITRA,
    TaraName.ATI_MITRA,
)


class TarabalaCategory(Enum):
    FAVORABLE = "FAVORABLE"
    UNFAVORABLE = "UNFAVORABLE"


# Session 52 migration: delegates to helpers/ephemeris.py's canonical
# EphemerisError rather than keeping a module-local copy.
EphemerisError = ephemeris.EphemerisError


@dataclass(frozen=True)
class TarabalaStatus:
    natal_nakshatra: int            # 0=Ashwini..26=Revati
    transit_nakshatra: int          # 0=Ashwini..26=Revati
    nakshatra_count: int            # 1-27, ((transit - natal) % 27) + 1
    tara_number: int                # 1-9, ((count - 1) % 9) + 1
    tara_name: TaraName
    category: TarabalaCategory
    is_janma_tara: bool             # nakshatra_count in {1, 10, 19}


def _moon_nakshatra(jd_ut: float) -> int:
    """Moon's sidereal nakshatra (0=Ashwini..26=Revati) at jd_ut.

    Delegates to helpers/ephemeris.py's sidereal_longitude() (Session 52
    migration) for the underlying swe.calc_ut convention.
    """
    return int(ephemeris.sidereal_longitude(jd_ut, swe.MOON) / _NAK_SPAN) % 27


def compute_tarabala(natal_nakshatra: int, transit_jd: float) -> TarabalaStatus:
    """
    Tarabala: transit Moon's nakshatra-count position counted from natal
    nakshatra (Janma Nakshatra), classified FAVORABLE/UNFAVORABLE per the
    9-tara cycle (see module docstring for sourcing and the
    activity-dependent-Janma deferral).

    Args:
        natal_nakshatra: Natal Moon's sidereal nakshatra, 0=Ashwini..26=Revati.
        transit_jd: Julian Day (UT) of the moment being evaluated. Trusted,
            not validated (matches chandrabala.py / sade_sati.py precedent).

    Returns:
        TarabalaStatus with both nakshatras, the classical 1-27
        nakshatra_count, the 1-9 tara_number, tara_name, category, and
        is_janma_tara.

    Raises:
        ValueError: natal_nakshatra not in 0..26.
        EphemerisError: a pyswisseph calculation failed for the Moon.
    """
    if not (0 <= natal_nakshatra <= 26):
        raise ValueError(f"natal_nakshatra must be in 0..26, got {natal_nakshatra}")

    swe.set_sid_mode(swe.SIDM_LAHIRI)

    transit_nakshatra = _moon_nakshatra(transit_jd)
    nakshatra_count = ((transit_nakshatra - natal_nakshatra) % 27) + 1
    tara_number = ((nakshatra_count - 1) % 9) + 1
    tara_name = _TARA_NAMES_BY_NUMBER[tara_number - 1]
    category = (
        TarabalaCategory.FAVORABLE
        if tara_number in _FAVORABLE_TARA_NUMBERS
        else TarabalaCategory.UNFAVORABLE
    )

    return TarabalaStatus(
        natal_nakshatra=natal_nakshatra,
        transit_nakshatra=transit_nakshatra,
        nakshatra_count=nakshatra_count,
        tara_number=tara_number,
        tara_name=tara_name,
        category=category,
        is_janma_tara=(nakshatra_count in _JANMA_TARA_COUNTS),
    )


# Coarse-scan step, internal only -- 12 hours. Moon's sidereal angular speed
# is ~13 deg/day; 13 * 0.5 = 6.5 deg < 13.333 deg (360/27, one nakshatra
# width), so a nakshatra ingress cannot be skipped between two consecutive
# coarse samples. Same value as chandrabala.py's _COARSE_STEP_JD, justified
# independently against the narrower nakshatra width. Not a function
# parameter -- see module docstring's Range-scan section.
_COARSE_STEP_JD = 0.5


@dataclass(frozen=True)
class TarabalaWindow:
    start_jd: float                 # inclusive
    end_jd: float                   # exclusive
    tara_name: TaraName
    category: TarabalaCategory
    is_janma_tara: bool
    nakshatra_count: int
    transit_nakshatra: int


def find_tarabala_windows(
    natal_nakshatra: int, start_jd: float, end_jd: float
) -> list[TarabalaWindow]:
    """
    Scans [start_jd, end_jd] for contiguous Tarabala windows -- spans
    where (category, is_janma_tara, tara_number) all stay constant
    (equivalently, spans of a single nakshatra-count value -- see module
    docstring's Range-scan section for why these coincide). Boundaries are
    bisected via agent.calculations.helpers.discrete_scan.find_state_segments,
    to its default tol_jd precision (1e-6 JD).

    Args:
        natal_nakshatra: Natal Moon's sidereal nakshatra, 0=Ashwini..26=Revati.
        start_jd: Julian Day (UT), inclusive lower bound of the scan.
        end_jd: Julian Day (UT), exclusive upper bound of the scan.

    Returns:
        List of TarabalaWindow, ordered by time, contiguous and gap-free
        over [start_jd, end_jd] (windows[0].start_jd == start_jd,
        windows[-1].end_jd == end_jd, windows[i].end_jd ==
        windows[i+1].start_jd). Empty list if start_jd == end_jd.

    Raises:
        ValueError: natal_nakshatra not in 0..26, or start_jd > end_jd.
        EphemerisError: a pyswisseph calculation failed for the Moon.
    """
    if not (0 <= natal_nakshatra <= 26):
        raise ValueError(f"natal_nakshatra must be in 0..26, got {natal_nakshatra}")
    if start_jd > end_jd:
        raise ValueError(f"start_jd ({start_jd}) must be <= end_jd ({end_jd})")
    if start_jd == end_jd:
        return []

    def _classify(jd: float) -> tuple:
        # Widened beyond the (category, is_janma_tara, tara_number)
        # change-detection triple to also carry tara_name/nakshatra_count/
        # transit_nakshatra -- tara_number changes at every nakshatra
        # ingress (see module docstring's Range-scan section), so this
        # produces the identical boundary set while letting each
        # StateSegment.state be unpacked directly into a TarabalaWindow.
        status = compute_tarabala(natal_nakshatra, jd)
        return (
            status.tara_name,
            status.category,
            status.is_janma_tara,
            status.nakshatra_count,
            status.transit_nakshatra,
        )

    segments = find_state_segments(_classify, start_jd, end_jd, _COARSE_STEP_JD)

    return [
        TarabalaWindow(
            start_jd=segment.start_jd,
            end_jd=segment.end_jd,
            tara_name=segment.state[0],
            category=segment.state[1],
            is_janma_tara=segment.state[2],
            nakshatra_count=segment.state[3],
            transit_nakshatra=segment.state[4],
        )
        for segment in segments
    ]
