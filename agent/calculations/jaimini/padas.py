"""Jaimini Bhava Padas -- P6, Master Build Plan order. Orchestration
layer over arudha.py's kernel: whole-sign house assembly + PVR's An/AL/
UL labeling scheme.

CITATION (PVR Narasimha Rao, "Vedic Astrology: An Integrated Approach",
Ch.9 Section 9.2 "Computation of Bhava Arudhas", printed p.86-87 / PDF
p.98-99 -- verbatim; see arudha.py's own CITATION block for the full
6-step per-house procedure this module orchestrates):

  "Arudha pada of a house is simply called arudha or pada also. In this
  book, we will denote the arudha pada on nth house with An. For
  example, arudha pada of 4th house is A4 and arudha pada of 9th house
  is A9.

  There are two special cases: Arudha pada of lagna is denoted as AL
  (arudha lagna) and arudha pada of 12th house is denoted as UL
  (upapada lagna)."

  Table 18 (printed p.87 / PDF p.99) additionally lists each arudha's
  longer classical alternate names (e.g. A2 = "Dhanarudha, Vittarudha,
  Dhana pada, Vitta pada"). This module implements only the An/AL/UL
  numbering scheme itself -- Table 18's alternate-name list is a pure
  display-label lookup with no computational content of its own, and no
  caller has asked for it yet; not attached here.

SCOPE: this is exactly the labeling layer arudha.py's own docstring
defers to this file ("jaimini/padas.py (a later file, per the Master
Build Plan's own file split) will call compute_arudha_pada() once per
house (1..12) and attach the An/AL/UL labels from PVR's Table 18 --
that labeling layer does not belong in this kernel"). It is also the
intended home for the whole-sign house assembly arudha.py's own
docstring deliberately excludes ("this module does not itself derive
house_sign from a Lagna degree and a house number; that belongs to the
caller").

WHOLE-SIGN HOUSES: house n (1-12) falls in the sign at index
(lagna_idx + n - 1) % 12, where lagna_idx is lagna_sign's index in the
canonical 12-sign tuple and house 1 IS lagna_sign itself. This is the
only house-division convention PVR endorses anywhere in this book (Ch.7
Section 7.5 "A Controversy", printed p.77-78 / PDF p.89-90: "readers are
advised to ignore all the discussions found in other textbooks on house
division methods, 'bhaava chakra' and 'chalit chakra' ... Each rasi is a
house. The rasi containing the reference point chosen is the 1st house
and the next rasi is the 2nd house.") -- never Sripati/Porphyry cusps
for this purpose.

FAIL-CLOSED (locked decision, matching every other jaimini/ kernel in
this package): compute_arudha_pada() can raise ValueError for a given
house for several reasons, including strength.py's D2 (both co-lords
resident in Scorpio/Aquarius) and D6 (exact Step-5(b) advancement tie).
Whichever house triggers it, this module lets the exception propagate
UNMODIFIED and does not return a partial BhavaPadaSet for the other 11
houses -- a chart with even one unresolvable house has no well-defined
bhava-pada set as a whole (see the FAIL-CLOSED comment at the call site
below for the mechanical detail).

Pure function, NO ephemeris calls (same pattern as karakas.py,
strength.py, arudha.py): the caller supplies lagna_sign and precomputed
sidereal longitudes.
"""

from __future__ import annotations

from dataclasses import dataclass

from agent.calculations.jaimini.arudha import ArudhaPadaResult, compute_arudha_pada

_CANONICAL_SIGNS: tuple[str, ...] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


@dataclass(frozen=True)
class BhavaPada:
    house_num: int
    label: str  # "AL" (house 1), "UL" (house 12), else f"A{house_num}"
    result: ArudhaPadaResult


@dataclass(frozen=True)
class BhavaPadaSet:
    lagna_sign: str
    padas: tuple[BhavaPada, ...]  # len 12, ordered house 1..12 -- tuple,
    # not list/dict, so BhavaPadaSet stays hashable like its sibling
    # jaimini/ result types (ArudhaPadaResult, StrongerCoLordResult).


def _label_for(house_num: int) -> str:
    if house_num == 1:
        return "AL"
    if house_num == 12:
        return "UL"
    return f"A{house_num}"


def compute_bhava_padas(
    lagna_sign: str,
    planet_longitudes: dict[str, float],
) -> BhavaPadaSet:
    """Compute the bhava arudha pada of all 12 houses from a lagna sign,
    per PVR Ch.9 Section 9.2 (see module CITATION).

    Args:
        lagna_sign: the sign occupied by Lagna (house 1, whole-sign
            convention -- see module docstring's WHOLE-SIGN HOUSES
            section). One of the 12 canonical rasis.
        planet_longitudes: absolute sidereal longitudes in degrees, per
            compute_arudha_pada()'s own contract (Title-case keys,
            exactly the 9 required planets, [0, 360) degrees). Key-set
            and range validation happens inside compute_arudha_pada()
            itself -- not duplicated here.

    Returns:
        BhavaPadaSet, one BhavaPada per house 1-12 in order.

    Raises:
        ValueError: lagna_sign not one of the 12 canonical rasis; OR
            whatever compute_arudha_pada() itself raises for ANY of the
            12 houses (missing/extra planet key, out-of-range
            longitude, strength.py's D2/D6 co-lord failures) --
            propagated unmodified, see module docstring's FAIL-CLOSED
            section.
    """
    if lagna_sign not in _CANONICAL_SIGNS:
        raise ValueError(
            f"Unrecognized lagna_sign {lagna_sign!r}. Must be one of the "
            f"12 canonical rasis (Aries through Pisces)."
        )

    lagna_idx = _CANONICAL_SIGNS.index(lagna_sign)

    padas = []
    for house_num in range(1, 13):
        house_sign = _CANONICAL_SIGNS[(lagna_idx + house_num - 1) % 12]
        # FAIL-CLOSED (locked decision): compute_arudha_pada() validates
        # planet_longitudes' key set/range itself and can also raise for
        # strength.py's D2 (both co-lords resident) / D6 (exact
        # Step-5(b) tie) at a Scorpio/Aquarius house. Any such
        # ValueError propagates UNMODIFIED out of this loop -- caught
        # nowhere, no partial BhavaPadaSet returned -- because a chart
        # where even one house's arudha is unresolvable has no
        # well-defined bhava-pada set for the remaining 11 either.
        result = compute_arudha_pada(house_sign, planet_longitudes)
        padas.append(BhavaPada(
            house_num=house_num,
            label=_label_for(house_num),
            result=result,
        ))

    return BhavaPadaSet(lagna_sign=lagna_sign, padas=tuple(padas))
