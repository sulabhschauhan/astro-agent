"""Jaimini Bhava Arudha (Arudha Pada) kernel -- P6, Master Build Plan
order.

CITATION (PVR Narasimha Rao, "Vedic Astrology: An Integrated Approach",
Ch.9 "Arudha Padas", Section 9.2 "Computation of Bhava Arudhas",
printed p.86 / PDF p.98 -- verbatim extraction, Session 57):

  "Arudha padas of all the 12 houses (bhavas) in all the divisional
  charts are defined as follows:

  (1) Take sign containing the house of interest in the divisional
  chart of interest.
  (2) Find the sign occupied by the lord of that house.
  NOTE: Aquarius is owned by Saturn and Rahu. Scorpio is owned by Mars
  and Ketu. Take the stronger lord in the case of houses falling in
  these two signs. The chapter on 'Strength of Planets and Rasis' will
  explain the rules used in comparing the strengths of planets.
  (3) Count signs from the house of interest to the sign containing its
  lord. Counting is in the zodiacal direction always. For example, if
  the house we are interested in is in Gemini and its lord Mercury is
  in Aquarius, we count signs from Gemini to Aquarius and get 9.
  (4) Count the same number of signs from the sign containing the lord
  and find the ending sign. In the above example, we count 9 signs
  from Aquarius and we end up in Libra.
  (5) Exception: If the sign found thus in step (4) is in the 1st or
  7th from the original sign in step (1), then we take the 10th sign
  from the sign found in step (4). Otherwise we don't make any change.
  (6) The resulting sign contains the arudha pada of the house of
  interest.

  Arudha pada of a house is simply called arudha or pada also. In this
  book, we will denote the arudha pada on nth house with An. For
  example, arudha pada of 4th house is A4 and arudha pada of 9th house
  is A9.

  There are two special cases: Arudha pada of lagna is denoted as AL
  (arudha lagna) and arudha pada of 12th house is denoted as UL
  (upapada lagna)."

SCOPE: this module implements the GENERAL bhava-arudha engine -- the
same 6-step procedure PVR uses for every house's arudha, AL included.
Arudha Lagna is not a separate algorithm; it is this exact procedure
applied with house_sign = the sign occupied by Lagna (house 1).
jaimini/padas.py (a later file, per the Master Build Plan's own file
split) will call compute_arudha_pada() once per house (1..12) and
attach the An/AL/UL labels from PVR's Table 18 -- that labeling layer
does not belong in this kernel.

STRONGER-LORD DEPENDENCY: step 2's own NOTE explicitly defers to "the
chapter on 'Strength of Planets and Rasis'" (PVR Ch.15 Section 15.5.1)
whenever house_sign is Scorpio (co-lords Mars/Ketu) or Aquarius
(co-lords Saturn/Rahu) -- this module calls
agent.calculations.jaimini.strength.stronger_co_lord(house_sign,
planet_longitudes, purpose="arudha") for exactly those two signs
(purpose="arudha" is the only purpose this call site ever needs, and
the only one strength.py implements). Every other sign uses its single
classical lord. stronger_co_lord's own exceptions -- design lock D2
(both co-lords resident in the contested sign) and D6 (an exact
Step-5(b) advancement tie) -- propagate UNMODIFIED out of this module:
an arudha whose house sign is Sc/Aq under one of those configurations
is simply unresolvable, the same fail-closed posture strength.py
itself takes. This module does not catch or reinterpret those errors.

COUNTING FORMULA (derived from the worked example above and
cross-checked against every one of Example 29's 12 houses, printed
p.87 / PDF p.99, before being locked in -- see the accompanying
verification, not embedded as a test file in this commit, mirroring
strength.py's kernel-first/test-suite-next rhythm from this same
session):

  Signs are indexed 0 (Aries) .. 11 (Pisces). "Count signs from X to Y,
  zodiacal direction" is an INCLUSIVE 1-based count:
  count = ((lord_idx - house_idx) % 12) + 1 -- e.g. Gemini(2) to
  Aquarius(10): ((10-2)%12)+1 = 9, matching PVR's own worked number.

  "Count `count` signs from the lord's sign" is the same inclusive
  scheme applied forward from lord_idx: ending_idx = (lord_idx +
  count - 1) % 12 -- e.g. 9 signs from Aquarius(10):
  (10+9-1)%12 = 6 = Libra, matching PVR's own worked number.

  "1st or 7th from the original sign" (step 5's exception trigger) is
  distance = (ending_idx - house_idx) % 12 being 0 (1st, i.e. the
  ending sign IS the house sign) or 6 (7th, i.e. exactly opposite).
  "The 10th sign from the sign found in step (4)" is the same
  inclusive scheme once more: final_idx = (ending_idx + 9) % 12. This
  correction is applied AT MOST ONCE -- PVR's text does not re-check
  the corrected result against the 1st/7th condition a second time,
  and no worked example in the book chains it.

Pure function, NO ephemeris calls (same pattern as karakas.py and
strength.py): the caller supplies precomputed sidereal longitudes and
the sign the house of interest falls in (whole-sign house convention,
per the chart-house-division discussion immediately preceding Ch.8 in
this same book -- this module does not itself derive house_sign from a
Lagna degree and a house number; that belongs to the caller, matching
karakas.py/strength.py's existing precedent of never doing chart
assembly inside a jaimini/ kernel).
"""

from __future__ import annotations

from dataclasses import dataclass

from agent.calculations.jaimini.strength import stronger_co_lord

_REQUIRED_PLANETS: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)

_CANONICAL_SIGNS: tuple[str, ...] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

# Classical (single) sign lords -- used for every house sign EXCEPT the
# two co-lorded signs, which route through stronger_co_lord() instead
# (see module docstring's STRONGER-LORD DEPENDENCY section). Scorpio and
# Aquarius are intentionally absent here; a lookup miss on either is a
# caller/logic bug, not a data gap -- see the assertion at the call site.
_CLASSICAL_SIGN_LORDS: dict[str, str] = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn",
    "Pisces": "Jupiter",
}

_CO_LORDED_SIGNS = frozenset({"Scorpio", "Aquarius"})


@dataclass(frozen=True)
class ArudhaPadaResult:
    house_sign: str
    lord: str
    lord_sign: str
    # co_lord_deciding_step is the underlying stronger_co_lord()
    # StrongerCoLordResult.deciding_step when house_sign was Scorpio or
    # Aquarius (basic_rule/step_1/../step_5b); None when house_sign had
    # a single classical lord and no cascade ran.
    co_lord_deciding_step: str | None
    count: int
    raw_ending_sign: str  # step (4)'s result, before the step (5) exception check
    exception_applied: bool  # whether step (5)'s "10th from raw_ending_sign" fired
    arudha_sign: str  # final result, step (6)


def compute_arudha_pada(
    house_sign: str,
    planet_longitudes: dict[str, float],
) -> ArudhaPadaResult:
    """Compute the arudha pada (bhava arudha) of a single house, per PVR
    Ch.9 Section 9.2 (see module CITATION).

    Args:
        house_sign: the sign occupied by the house of interest (e.g.
            Lagna's sign for AL, the 7th house's sign for A7/Dara
            Pada). One of the 12 canonical rasis.
        planet_longitudes: absolute sidereal longitudes in degrees
            ([0, 360) expected), Title-case planet-name keys. Exactly
            the 9 keys in _REQUIRED_PLANETS are required -- Sun, Moon,
            Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu -- even
            though a classical (non-co-lorded) house_sign only needs
            one planet's position; the full birth-chart contract is
            validated uniformly, matching karakas.py/strength.py.

    Returns:
        ArudhaPadaResult.

    Raises:
        ValueError: house_sign not one of the 12 canonical rasis;
            planet_longitudes missing/extra keys; any longitude not in
            [0, 360) sidereal degrees (NaN included); OR, when
            house_sign is Scorpio/Aquarius, whatever
            stronger_co_lord() itself raises (D2 both-co-lords-resident,
            D6 exact Step-5(b) tie) -- propagated unmodified, see module
            docstring's STRONGER-LORD DEPENDENCY section.
    """
    if house_sign not in _CANONICAL_SIGNS:
        raise ValueError(
            f"Unrecognized house_sign {house_sign!r}. Must be one of the "
            f"12 canonical rasis (Aries through Pisces)."
        )

    expected = set(_REQUIRED_PLANETS)
    given = set(planet_longitudes)
    missing = sorted(expected - given)
    extra = sorted(given - expected)
    if missing or extra:
        problems = []
        if missing:
            problems.append(f"missing required key(s) {missing}")
        if extra:
            problems.append(f"unexpected key(s) {extra}")
        raise ValueError(
            f"planet_longitudes must have exactly the 9 keys "
            f"{list(_REQUIRED_PLANETS)}: {'; '.join(problems)}"
        )

    # `not (0.0 <= lon < 360.0)` rather than `lon < 0.0 or lon >= 360.0`:
    # NaN compares False against every relation, so `0.0 <= nan < 360.0`
    # is False and the `not` flips it to True -- NaN is caught by this
    # form without a separate isnan() check.
    out_of_range = sorted(
        (planet, planet_longitudes[planet])
        for planet in _REQUIRED_PLANETS
        if not (0.0 <= planet_longitudes[planet] < 360.0)
    )
    if out_of_range:
        raise ValueError(
            f"planet_longitudes must be sidereal degrees in [0, 360) for "
            f"every planet: out-of-range value(s) {out_of_range}"
        )

    if house_sign in _CO_LORDED_SIGNS:
        co_lord_result = stronger_co_lord(house_sign, planet_longitudes, purpose="arudha")
        lord = co_lord_result.winner
        co_lord_deciding_step = co_lord_result.deciding_step
    else:
        lord = _CLASSICAL_SIGN_LORDS[house_sign]
        co_lord_deciding_step = None

    lord_sign = _CANONICAL_SIGNS[int(planet_longitudes[lord] // 30) % 12]

    house_idx = _CANONICAL_SIGNS.index(house_sign)
    lord_idx = _CANONICAL_SIGNS.index(lord_sign)

    # Steps (3)-(4): inclusive zodiacal counting -- see module
    # docstring's COUNTING FORMULA section for the worked derivation.
    count = ((lord_idx - house_idx) % 12) + 1
    ending_idx = (lord_idx + count - 1) % 12
    raw_ending_sign = _CANONICAL_SIGNS[ending_idx]

    # Step (5): 1st (distance 0) or 7th (distance 6) from house_sign ->
    # take the 10th sign from raw_ending_sign, applied at most once.
    distance_from_house = (ending_idx - house_idx) % 12
    exception_applied = distance_from_house in (0, 6)
    final_idx = (ending_idx + 9) % 12 if exception_applied else ending_idx
    arudha_sign = _CANONICAL_SIGNS[final_idx]

    return ArudhaPadaResult(
        house_sign=house_sign,
        lord=lord,
        lord_sign=lord_sign,
        co_lord_deciding_step=co_lord_deciding_step,
        count=count,
        raw_ending_sign=raw_ending_sign,
        exception_applied=exception_applied,
        arudha_sign=arudha_sign,
    )
