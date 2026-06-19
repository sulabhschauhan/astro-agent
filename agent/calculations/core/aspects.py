"""Graha drishti (planetary aspect) determination per PVR §10.2
plus locked Rahu/Ketu = 5/7/9 resolution. Sign-based, Whole Sign
houses. Data backed by _aspects_tables.ASPECTED_HOUSES_BY_PLANET.
"""

from agent.calculations.core._aspects_tables import ASPECTED_HOUSES_BY_PLANET

_CANONICAL_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

# Full aspecting-planet set: all 9 chart points, nodes included, per the
# locked classical-conflict resolution in _aspects_tables.py. Intentionally
# DIFFERENT from friendship.py's CLASSICAL_PLANETS (7 only) -- nodes cast
# aspects but do not participate in the natural-friendship table. Different
# semantic scope by classical design, not by oversight.
ASPECTING_PLANETS = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
    "Rahu", "Ketu",
)

assert set(ASPECTING_PLANETS) == set(ASPECTED_HOUSES_BY_PLANET.keys()), (
    f"ASPECTING_PLANETS {sorted(ASPECTING_PLANETS)} != "
    f"ASPECTED_HOUSES_BY_PLANET.keys() {sorted(ASPECTED_HOUSES_BY_PLANET.keys())} -- "
    f"these two sources of truth have drifted apart"
)


def _sign_at_position(start_sign: str, n: int) -> str:
    """Resolve the sign at classical house-position n counted from
    start_sign, with start_sign itself as position 1 (n=1 -> start_sign,
    n=7 -> the opposite sign, etc.).
    """
    target_index = (_CANONICAL_SIGNS.index(start_sign) + n - 1) % 12
    return _CANONICAL_SIGNS[target_index]


def signs_aspected_by(planet: str, planet_sign: str) -> tuple[str, ...]:
    """Resolve the sign(s) that `planet` aspects (graha drishti) when
    located in `planet_sign`, per PVR §10.2 plus the locked Rahu/Ketu
    5/7/9 resolution (see _aspects_tables.py for the full classical-conflict
    writeup).

    Returned tuple length is 1 (Sun/Moon/Mercury/Venus -- 7th house only) or
    3 (Mars/Jupiter/Saturn/Rahu/Ketu -- special aspects), in source-position
    order -- i.e. the same ordering as ASPECTED_HOUSES_BY_PLANET[planet],
    which is ascending by classical house position. For example, Saturn in
    Sagittarius returns (Aquarius, Gemini, Virgo) -- 3rd, 7th, 10th from
    Sagittarius in that order. This ordering is part of the contract;
    downstream callers may rely on position-to-sign correspondence.

    Args:
        planet: one of ASPECTING_PLANETS.
        planet_sign: one of the 12 canonical rasis, the sign planet occupies.

    Returns:
        Tuple of canonical sign names aspected by planet, in source-position
        order.

    Raises:
        ValueError: planet not in ASPECTING_PLANETS, or planet_sign not one
            of the 12 canonical rasis.
    """
    if planet not in ASPECTING_PLANETS:
        raise ValueError(
            f"Unrecognized planet {planet!r}. Valid planets are in "
            f"ASPECTING_PLANETS: {', '.join(ASPECTING_PLANETS)}."
        )
    if planet_sign not in _CANONICAL_SIGNS:
        raise ValueError(
            f"Unrecognized sign {planet_sign!r}. Valid signs are the 12 "
            f"canonical rasis (Aries through Pisces)."
        )

    positions = ASPECTED_HOUSES_BY_PLANET[planet]
    return tuple(_sign_at_position(planet_sign, n) for n in positions)


def does_planet_aspect_sign(planet: str, planet_sign: str, target_sign: str) -> bool:
    """Check whether `planet`, located in `planet_sign`, aspects
    `target_sign` per graha drishti (see signs_aspected_by for the
    classical source and ordering contract).

    Args:
        planet: one of ASPECTING_PLANETS.
        planet_sign: one of the 12 canonical rasis, the sign planet occupies.
        target_sign: one of the 12 canonical rasis, the sign being tested.

    Returns:
        True if planet aspects target_sign, else False.

    Raises:
        ValueError: planet not in ASPECTING_PLANETS, or planet_sign/
            target_sign not one of the 12 canonical rasis.
    """
    if target_sign not in _CANONICAL_SIGNS:
        raise ValueError(
            f"Unrecognized sign {target_sign!r}. Valid signs are the 12 "
            f"canonical rasis (Aries through Pisces)."
        )
    return target_sign in signs_aspected_by(planet, planet_sign)


def aspects_between(planet_a: str, sign_a: str, planet_b: str, sign_b: str) -> bool:
    """Check whether planet_a (in sign_a) aspects planet_b (in sign_b) per
    graha drishti.

    Classical aspects are positional: the aspect depends only on planet_a's
    aspect pattern (its class) and the two signs involved. planet_b's
    identity is used ONLY for scope validation (confirming it's a
    recognized chart point) -- it does not factor into the boolean result.
    planet_b's own aspect pattern is irrelevant here; call this again with
    the arguments swapped to test the reverse direction.

    Args:
        planet_a: one of ASPECTING_PLANETS, the aspecting planet.
        sign_a: one of the 12 canonical rasis, the sign planet_a occupies.
        planet_b: one of ASPECTING_PLANETS, the planet being checked for
            aspect (validation only -- see above).
        sign_b: one of the 12 canonical rasis, the sign planet_b occupies.

    Returns:
        True if planet_a aspects sign_b, else False.

    Raises:
        ValueError: planet_a or planet_b not in ASPECTING_PLANETS; sign_a
            or sign_b not one of the 12 canonical rasis; or planet_a ==
            planet_b (a planet aspecting itself is a malformed query).
    """
    if planet_a not in ASPECTING_PLANETS:
        raise ValueError(
            f"Unrecognized planet_a {planet_a!r}. Valid planets are in "
            f"ASPECTING_PLANETS: {', '.join(ASPECTING_PLANETS)}."
        )
    if planet_b not in ASPECTING_PLANETS:
        raise ValueError(
            f"Unrecognized planet_b {planet_b!r}. Valid planets are in "
            f"ASPECTING_PLANETS: {', '.join(ASPECTING_PLANETS)}."
        )
    if sign_a not in _CANONICAL_SIGNS:
        raise ValueError(
            f"Unrecognized sign_a {sign_a!r}. Valid signs are the 12 "
            f"canonical rasis (Aries through Pisces)."
        )
    if sign_b not in _CANONICAL_SIGNS:
        raise ValueError(
            f"Unrecognized sign_b {sign_b!r}. Valid signs are the 12 "
            f"canonical rasis (Aries through Pisces)."
        )
    if planet_a == planet_b:
        raise ValueError(
            f"aspects_between compares two different planets; got "
            f"planet_a == planet_b == {planet_a!r} -- a planet aspecting "
            f"itself is a malformed query."
        )

    return does_planet_aspect_sign(planet_a, sign_a, sign_b)
