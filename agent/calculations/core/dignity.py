"""Planetary dignity states: exaltation, debilitation, own-sign, Moolatrikona.

Covers static dignity classification only (this is a per-placement lookup
against the tables in _dignity_tables.py). Friendship-based classification
(natural/tatkalika/pancha-dha maitri) is a separate, later addition — it
needs a natural-friendship table that doesn't exist yet.
"""

from agent.calculations.core._dignity_tables import (
    DEBILITATION,
    EXALTATION,
    MOOLATRIKONA,
    OWN_SIGNS,
)

_CANONICAL_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


def get_dignity_status(planet: str, sign: str, degree_in_sign: float) -> str | None:
    """Classify a planet's static dignity at a given sign + degree-in-sign.

    Returns one of "Exalted", "Debilitated", "Moolatrikona", "Own", or None
    (no special dignity applies — the common case, not an error).
    """
    if planet not in EXALTATION:
        raise ValueError(
            f"Unrecognized planet {planet!r}; expected one of {sorted(EXALTATION.keys())}"
        )
    if sign not in _CANONICAL_SIGNS:
        raise ValueError(f"Unrecognized sign {sign!r}; expected one of {_CANONICAL_SIGNS}")
    if not (0.0 <= degree_in_sign < 30.0):
        raise ValueError(
            f"degree_in_sign {degree_in_sign} out of range; expected 0.0 <= degree_in_sign < 30.0"
        )

    debil_sign, _ = DEBILITATION[planet]
    if sign == debil_sign:
        return "Debilitated"

    exalt_sign, _ = EXALTATION[planet]
    mt_sign, mt_start, mt_end = MOOLATRIKONA[planet]

    if sign == exalt_sign:
        if exalt_sign == mt_sign:
            # Moon/Mercury only: exaltation and Moolatrikona share a sign.
            # Below the MT range's start it's Exalted; at/after that degree
            # the MT (and, beyond mt_end, Own) checks below take over.
            if degree_in_sign < mt_start:
                return "Exalted"
        else:
            return "Exalted"

    if sign == mt_sign and mt_start <= degree_in_sign < mt_end:
        return "Moolatrikona"

    for own_sign, own_start, own_end in OWN_SIGNS[planet]:
        if sign == own_sign and own_start <= degree_in_sign < own_end:
            return "Own"

    return None
