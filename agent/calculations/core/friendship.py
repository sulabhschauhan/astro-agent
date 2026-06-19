"""Friendship-based dignity classification: natural and tatkalika (temporary).

Covers two of the three classical friendship layers (PVR Section 3.4):
natural_friendship() is a static lookup against the 7-planet table in
_friendship_tables.py; tatkalika_friendship() is computed directly from
relative sign position (PVR Section 3.4.2), uniformly for all 9 chart
points. Pancha-dha maitri (the 5-fold compound scheme combining natural
+ temporary) is a later addition, once both of these are verified.
"""

from agent.calculations.core._friendship_tables import (
    COMPOUND_RELATIONSHIP_MAP,
    NATURAL_FRIENDSHIP,
)

_CANONICAL_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

_NODES = ("Rahu", "Ketu")


def natural_friendship(planet_a: str, planet_b: str) -> str:
    """Look up planet_a's natural (sthira) relation to planet_b.

    Returns one of "Friend", "Neutral", "Enemy". Directional and asymmetric
    by design -- planet_b's relation to planet_a is a separate lookup, not
    derivable from this result.
    """
    for planet in (planet_a, planet_b):
        if planet in NATURAL_FRIENDSHIP:
            continue
        if planet in _NODES:
            raise ValueError(
                f"{planet!r}: natural friendship does not cover Rahu/Ketu by "
                f"design -- PVR Table 7 and all 4 AstroSage reference charts "
                f"stop at the 7 classical planets. Not a typo."
            )
        raise ValueError(
            f"Unrecognized planet {planet!r}; expected one of "
            f"{sorted(NATURAL_FRIENDSHIP.keys())}"
        )

    if planet_a == planet_b:
        raise ValueError(
            f"natural_friendship compares two different planets; "
            f"got planet_a == planet_b == {planet_a!r}"
        )

    entry = NATURAL_FRIENDSHIP[planet_a]
    for relation, list_name in (
        ("Friend", "friends"), ("Neutral", "neutral"), ("Enemy", "enemies")
    ):
        if planet_b in entry[list_name]:
            return relation

    raise ValueError(f"{planet_a!r} has no recorded relation to {planet_b!r}")


def tatkalika_friendship(sign_a: str, sign_b: str) -> str:
    """Compute sign_a's temporary (tatkalika) relation to sign_b (PVR Section 3.4.2).

    Returns "Friend" or "Enemy" -- there is no neutral state. Depends only on
    rasi position, not on which planet (if any) occupies it, so this applies
    uniformly to all 9 chart points, Rahu/Ketu included.
    """
    for sign in (sign_a, sign_b):
        if sign not in _CANONICAL_SIGNS:
            raise ValueError(
                f"Unrecognized sign {sign!r}; expected one of {_CANONICAL_SIGNS}"
            )

    # Count sign_a to sign_b inclusively, sign_a itself as position 1.
    # count==1 (same sign) falls into the enemy set below by construction --
    # two planets conjunct in one rasi are temporary enemies, per PVR.
    count = (_CANONICAL_SIGNS.index(sign_b) - _CANONICAL_SIGNS.index(sign_a)) % 12 + 1

    if count in (2, 3, 4, 10, 11, 12):
        return "Friend"
    return "Enemy"  # count in (1, 5, 6, 7, 8, 9)


def pancha_dha_maitri(planet_a: str, sign_a: str, planet_b: str, sign_b: str) -> str:
    """Compute the five-fold compound relationship (PVR Table 8) of planet_a
    (in sign_a) toward planet_b (in sign_b), combining natural + tatkalika
    friendship.

    Returns one of "Good Friend", "Friend", "Neutral", "Enemy", "Bad Enemy".
    Validation is delegated entirely to natural_friendship() and
    tatkalika_friendship() -- their ValueErrors propagate unchanged.
    """
    natural = natural_friendship(planet_a, planet_b)
    temporal = tatkalika_friendship(sign_a, sign_b)
    return COMPOUND_RELATIONSHIP_MAP[(natural, temporal)]
