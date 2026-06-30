"""Bhava Bala — Bhavadhipati Bala sub-component (first of three).

Source: BPHS 27.26-31; B.V. Raman "Graha and Bhava Balas".
Bhavadhipati Bala = the Shadbala total (Virupa) of the planet that rules
the sign occupying a given house (the house's "lord"). The lord is
determined by whole-sign house assignment; Shadbala totals are taken
from compute_shadbala_totals() — not recomputed here.

NOT IMPLEMENTED HERE: Bhava Dig Bala, Bhava Drishti Bala, Total Bhava
Bala aggregate — those are separate follow-up modules/prompts.
"""

from __future__ import annotations

from agent.chart_calculator import SIGN_LORDS

_EXPECTED_HOUSES = frozenset(range(1, 13))


def compute_bhavadhipati_bala(
    house_signs: dict[int, str],
    shadbala_totals: dict[str, float],
) -> dict[int, float]:
    """Return Bhavadhipati Bala (Virupa) for each of the 12 houses.

    For each house, looks up its sign's ruling planet via SIGN_LORDS and
    returns that planet's Shadbala virupa total.

    Args:
        house_signs: {1: "Sagittarius", 2: "Capricorn", ...} — exactly 12
            entries with integer keys 1-12, whole-sign house assignment.
        shadbala_totals: planet name → virupa total, as returned by
            compute_shadbala_totals(). Must include the lord of every sign
            present in house_signs.

    Returns:
        {1: 405.2, 2: 423.16, ...} — house number → Bhavadhipati Bala.

    Raises:
        ValueError: if house_signs does not have exactly 12 entries with keys
            1-12, contains an unrecognised sign, or shadbala_totals is missing
            the lord for any house's sign.
    """
    if set(house_signs.keys()) != _EXPECTED_HOUSES:
        missing = _EXPECTED_HOUSES - set(house_signs.keys())
        extra = set(house_signs.keys()) - _EXPECTED_HOUSES
        raise ValueError(
            f"house_signs must have exactly keys 1-12; "
            f"missing={sorted(missing)}, extra={sorted(extra)}"
        )

    result: dict[int, float] = {}
    for house, sign in house_signs.items():
        if sign not in SIGN_LORDS:
            raise ValueError(
                f"House {house}: sign {sign!r} not recognised — "
                f"expected one of {sorted(SIGN_LORDS)}"
            )
        lord = SIGN_LORDS[sign]
        if lord not in shadbala_totals:
            raise ValueError(
                f"House {house}: sign {sign!r} is ruled by {lord!r}, "
                f"but {lord!r} is missing from shadbala_totals "
                f"(keys present: {sorted(shadbala_totals)})"
            )
        result[house] = shadbala_totals[lord]

    return result
