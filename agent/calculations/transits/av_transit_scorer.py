"""Ashtakavarga transit scorer -- Master Build Plan Session 55.

Purpose: score a transiting planet's effect on a natal chart using its
BAV/SAV/contributor-set inputs (agent.calculations.ashtakavarga.
ashtakavarga's compute_bav / compute_sav / compute_bav_contributors),
plus PVR ch. 25.5.2's Prastaara kakshya method for Saturn/Jupiter.

Pure function, NO ephemeris calls: score_av_transit() takes precomputed
transit position + precomputed natal Ashtakavarga tables. Callers own
sourcing transit_sign/degrees_in_sign (from whatever ephemeris call they
already made) and natal_bav/natal_sav/natal_contributors (from the
ashtakavarga module).

USAGE CONSTRAINT (PVR verbatim, ch. 25.5.2) -- the kakshya method "can
only be used to fine-tune a prediction to a few days" and is never used
in a vacuum. This module scores a single instant; it is the CONSUMER's
responsibility (the future convergence layer) to nest this score inside a
dasha envelope, never to substitute for one. Nothing here checks or
enforces that nesting -- it cannot, from a pure per-instant function.

PLANET SCOPE (locked design, V1):
  - Saturn, Jupiter: full scoring, including kakshya_index/kakshya_lord/
    kakshya_has_rekha (PVR Table 60 lord order applies to these two
    because they are the slow-moving planets whose kakshya residence is
    stable enough to matter for day-scale predictions).
  - Sun, Mars: sign-level scoring only (bav_rekhas/bav_band/bav_intensity/
    sav_value/sav_band/verdict) -- kakshya_index/kakshya_lord/
    kakshya_has_rekha are None. Sun and Mars are fast enough that a
    kakshya (3d45') residence is single-digit-hours, well below "fine-tune
    to a few days" -- scoring a kakshya for them would overstate the
    method's own stated precision floor.
  - Moon, Mercury, Venus: excluded from V1 transit scoring entirely
    (ValueError, fail closed -- see _EXCLUDED_PLANETS). Moon is faster
    still than Sun/Mars (~2.25 days/sign) and belongs to the Muhurta
    layer (chandrabala.py/tarabala.py), not this slower-cadence Gochara
    scorer. Mercury and Venus are excluded alongside it for the same
    too-fast-to-constrain-an-event-window reason; PVR ch. 25.5 does not
    itself carve out a separate exclusion list, so this is a project-side
    V1 scope decision, not a classical rule -- revisit if a future phase
    needs sub-week transit resolution for these three.

CITATION / THRESHOLD DISCIPLINE (each numeric threshold below has its own
justification + scope guard + tuning note; see also individual field
comments in AvTransitScore):
  (a) bav_band thresholds (>=5 FAVORABLE, ==4 NEUTRAL, <=3 UNFAVORABLE):
      PVR ch. 25.5 states benefic-transit results when a planet transits
      a rasi where it holds bindus w.r.t. 5 or more reference points,
      malefic results at 3 or fewer; 4 is prose-unclassified. Scope
      guard: applies only to the 0-8 BAV range (8 contributors). Tuning
      note: NEUTRAL-at-4 is a deliberate "unclassified middle" choice,
      not a rounding of FAVORABLE or UNFAVORABLE -- do not collapse it
      into either without a source that actually classifies 4.
  (b) bav_intensity (EXCELLENT for 6/7/8, VERY_POOR for 0/1, else None):
      PVR ch. 25.5 states "6 or 7 rekhas invariably excellent" and "1 or
      0 invariably very poor" verbatim; 8 is folded into EXCELLENT here
      by monotonicity (a strictly-better score than the cited 7 cannot be
      worse than "excellent") -- PVR's prose does not itself mention 8,
      so this one value is an interpolation, not a direct citation.
      Scope guard: 2-5 rekhas intentionally yield None (PVR does not
      claim an intensity label for the middle of the range). Tuning
      note: if a future oracle disagrees on the 8 case specifically,
      revisit only that folding, not the 6/7/0/1 citations.
  (c) sav_band thresholds (>=30 FAVORABLE, 25-29 AVERAGE, <=24
      UNFAVORABLE): PVR ch. 25.5.1's prose gives ">30 good, <25 bad",
      leaving the boundary value 30 itself ambiguous (neither ">30" nor
      "<25" resolves it). PVR's own worked example (Vajpayee's chart)
      counts a Pisces SAV of exactly 30 as "very strong" -- resolved here
      to >=30 FAVORABLE on that worked-example precedent, not from the
      prose alone. Scope guard: SAV range is 0-56 (7 planet contributors
      x max 8). Tuning note: if a future oracle chart's SAV=30 disagrees
      with the worked example's classification, that is a genuine source
      conflict to escalate via the tiebreaker principle, not a silent
      threshold change.
  (d) verdict / SAV-dominance rule: PVR states SAV "will dominate over
      the BAVs if it has too many or too few rekhas" -- i.e. only when
      sav_band is NOT the middle band. Implemented as: verdict = sav_band
      when sav_band != AVERAGE, else verdict = bav_band (with NEUTRAL
      mapped to AVERAGE, since verdict shares sav_band's 3-way type and
      PVR's own "average" framing for the non-dominant case is the
      natural fit for an unclassified BAV middle). No numeric weighting
      or composite score of any kind is computed -- PVR provides no
      formula combining SAV and BAV numerically, and none is invented
      here.
  (e) kakshya boundaries (3d45' = 3.75 degrees per division, half-open
      [start, end)): PVR Table 60 gives the lord order and the 3d45'
      division width but does not state, in the source prose consulted,
      which side of an exact 3d45' multiple a boundary transit falls on.
      Chosen convention here: half-open [start, end), so a transit sitting
      at exactly 3d45'00" belongs to the SECOND kakshya (Jupiter, index
      1), not the first (Saturn, index 0). This is a documented
      convention, not a citation -- revisit only if a future oracle
      fixture pins the opposite convention at an exact boundary degree.

Lord order (PVR Table 60, fixed, does NOT rotate with transit_planet or
sign): Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon, Lagna.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from agent.chart_calculator import SIGNS

_EXCLUDED_PLANETS: tuple[str, ...] = ("Moon", "Mercury", "Venus")
_KAKSHYA_PLANETS: tuple[str, ...] = ("Saturn", "Jupiter")
_ALL_KNOWN_TRANSIT_PLANETS: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
)

# PVR Table 60 kakshya lord order, fixed -- see module CITATION (e).
_KAKSHYA_LORDS: tuple[str, ...] = (
    "Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon", "Lagna",
)
_KAKSHYA_WIDTH_DEG = 3.75  # 3 degrees 45 minutes


class BavBand(Enum):
    FAVORABLE = "FAVORABLE"
    NEUTRAL = "NEUTRAL"
    UNFAVORABLE = "UNFAVORABLE"


class AvVerdictBand(Enum):
    """Shared 3-way band for sav_band and verdict (see CITATION (c)/(d) --
    this is a distinct type from BavBand because BAV's unclassified
    middle is named NEUTRAL while SAV's/verdict's is named AVERAGE,
    matching PVR's own terminology for each.
    """
    FAVORABLE = "FAVORABLE"
    AVERAGE = "AVERAGE"
    UNFAVORABLE = "UNFAVORABLE"


class BavIntensity(Enum):
    EXCELLENT = "EXCELLENT"
    VERY_POOR = "VERY_POOR"


_BAV_BAND_TO_VERDICT: dict[BavBand, AvVerdictBand] = {
    BavBand.FAVORABLE: AvVerdictBand.FAVORABLE,
    BavBand.NEUTRAL: AvVerdictBand.AVERAGE,
    BavBand.UNFAVORABLE: AvVerdictBand.UNFAVORABLE,
}


@dataclass(frozen=True)
class AvTransitScore:
    transit_planet: str
    transit_sign: str
    bav_rekhas: int                      # natal_bav[transit_planet][transit_sign], 0-8
    bav_band: BavBand                    # CITATION (a)
    bav_intensity: BavIntensity | None    # CITATION (b); None for 2-5 rekhas
    sav_value: int                       # natal_sav[transit_sign], 0-56
    sav_band: AvVerdictBand              # CITATION (c)
    verdict: AvVerdictBand               # CITATION (d), SAV-dominance rule
    kakshya_index: int | None            # 0-7, Saturn/Jupiter only; else None
    kakshya_lord: str | None             # PVR Table 60 lord; Saturn/Jupiter only
    kakshya_has_rekha: bool | None       # Saturn/Jupiter only; else None


def score_av_transit(
    transit_planet: str,
    transit_sign: str,
    degrees_in_sign: float,
    natal_bav: dict[str, dict[str, int]],
    natal_sav: dict[str, int],
    natal_contributors: dict[str, dict[str, frozenset[str]]],
) -> AvTransitScore:
    """Score transit_planet's transit of transit_sign against a natal
    chart's precomputed Ashtakavarga tables. See module docstring for the
    USAGE CONSTRAINT, PLANET SCOPE, and per-threshold CITATION notes.

    Args:
        transit_planet: one of "Sun","Moon","Mars","Mercury","Jupiter",
            "Venus","Saturn" (title case, agent.chart_calculator
            convention). Moon/Mercury/Venus raise ValueError by design
            (see PLANET SCOPE) -- fail closed, never silently scored.
        transit_sign: one of the 12 title-case sign names in
            agent.chart_calculator.SIGNS.
        degrees_in_sign: transiting planet's position within transit_sign,
            [0, 30) degrees. Only consulted for Saturn/Jupiter kakshya
            placement; still validated for all scorable planets so a bad
            caller input fails the same way regardless of planet.
        natal_bav: compute_bav()'s return value (or same shape) --
            validated shallowly (transit_planet/transit_sign keys
            present), NOT recomputed from placements here.
        natal_sav: compute_sav()'s return value (or same shape) --
            validated shallowly (transit_sign key present).
        natal_contributors: compute_bav_contributors()'s return value (or
            same shape) -- validated shallowly, and only when needed
            (Saturn/Jupiter kakshya scoring); unused/unvalidated for
            Sun/Mars since they have no kakshya fields to derive.

    Returns:
        AvTransitScore.

    Raises:
        ValueError: transit_planet not one of the 7 classical grahas;
            transit_planet is Moon/Mercury/Venus (excluded from V1
            transit scoring by design); transit_sign not a recognized
            sign; degrees_in_sign outside [0, 30); or a required key is
            missing from natal_bav/natal_sav/natal_contributors.
    """
    if transit_planet not in _ALL_KNOWN_TRANSIT_PLANETS:
        raise ValueError(
            f"unknown transit_planet {transit_planet!r}; expected one of "
            f"{_ALL_KNOWN_TRANSIT_PLANETS}"
        )
    if transit_planet in _EXCLUDED_PLANETS:
        raise ValueError(
            f"{transit_planet} is excluded from V1 Ashtakavarga transit "
            f"scoring by design: it moves too fast to constrain an event "
            f"window at this method's day-scale precision (Moon belongs "
            f"to the Muhurta layer -- see chandrabala.py/tarabala.py -- "
            f"not this Gochara-cadence scorer). This is a V1 scope "
            f"decision, not a classical rule; fails closed rather than "
            f"silently scoring."
        )
    if transit_sign not in SIGNS:
        raise ValueError(
            f"unrecognized transit_sign {transit_sign!r}; expected one of {SIGNS}"
        )
    if not (0 <= degrees_in_sign < 30):
        raise ValueError(
            f"degrees_in_sign must be in [0, 30), got {degrees_in_sign!r}"
        )

    if transit_planet not in natal_bav or transit_sign not in natal_bav[transit_planet]:
        raise ValueError(
            f"natal_bav missing entry for transit_planet={transit_planet!r} "
            f"sign={transit_sign!r}"
        )
    if transit_sign not in natal_sav:
        raise ValueError(f"natal_sav missing entry for sign={transit_sign!r}")

    bav_rekhas = natal_bav[transit_planet][transit_sign]
    sav_value = natal_sav[transit_sign]

    # CITATION (a).
    if bav_rekhas >= 5:
        bav_band = BavBand.FAVORABLE
    elif bav_rekhas == 4:
        bav_band = BavBand.NEUTRAL
    else:
        bav_band = BavBand.UNFAVORABLE

    # CITATION (b).
    if bav_rekhas in (6, 7, 8):
        bav_intensity: BavIntensity | None = BavIntensity.EXCELLENT
    elif bav_rekhas in (0, 1):
        bav_intensity = BavIntensity.VERY_POOR
    else:
        bav_intensity = None

    # CITATION (c).
    if sav_value >= 30:
        sav_band = AvVerdictBand.FAVORABLE
    elif sav_value >= 25:
        sav_band = AvVerdictBand.AVERAGE
    else:
        sav_band = AvVerdictBand.UNFAVORABLE

    # CITATION (d): SAV-dominance rule -- no numeric weighting/composite.
    if sav_band != AvVerdictBand.AVERAGE:
        verdict = sav_band
    else:
        verdict = _BAV_BAND_TO_VERDICT[bav_band]

    kakshya_index: int | None = None
    kakshya_lord: str | None = None
    kakshya_has_rekha: bool | None = None

    if transit_planet in _KAKSHYA_PLANETS:
        if transit_planet not in natal_contributors or transit_sign not in natal_contributors[transit_planet]:
            raise ValueError(
                f"natal_contributors missing entry for "
                f"transit_planet={transit_planet!r} sign={transit_sign!r} "
                f"(required for {transit_planet}'s kakshya scoring)"
            )
        # CITATION (e): half-open [start, end) division, 3.75 degrees wide.
        # min(...,7) is a float-precision guard only (degrees_in_sign is
        # already validated < 30 = 8 * 3.75), not a new boundary rule.
        kakshya_index = min(int(degrees_in_sign // _KAKSHYA_WIDTH_DEG), 7)
        kakshya_lord = _KAKSHYA_LORDS[kakshya_index]
        kakshya_has_rekha = kakshya_lord in natal_contributors[transit_planet][transit_sign]

    return AvTransitScore(
        transit_planet=transit_planet,
        transit_sign=transit_sign,
        bav_rekhas=bav_rekhas,
        bav_band=bav_band,
        bav_intensity=bav_intensity,
        sav_value=sav_value,
        sav_band=sav_band,
        verdict=verdict,
        kakshya_index=kakshya_index,
        kakshya_lord=kakshya_lord,
        kakshya_has_rekha=kakshya_has_rekha,
    )
