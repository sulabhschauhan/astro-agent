"""Jaimini RASI drishti (sign aspect) -- P6, Master Build Plan order.

*** NOT graha drishti. ***
This module is Jaimini RASI drishti (sign aspects between the 12 rasis
themselves), governed by the movable/fixed/dual scheme below. It is a
completely different classical mechanism from
agent/calculations/core/aspects.py's graha drishti (planetary aspect,
PVR Ch.10 Section 10.2, house-position-based per planet). The two are
NEVER interchangeable and this module imports nothing from aspects.py.
Known consumers: PVR Section 15.5.1 stronger-co-lord step 2 ("conjoin/
aspect a planet"), the arudha layer (agent/calculations/jaimini/arudha.py).

CITATION (PVR Narasimha Rao, "Vedic Astrology: An Integrated Approach",
Ch.10 "Aspects and Argalas", Sections 10.1-10.4, printed pp.100-103 /
PDF pp.111-114, plus the Exercise 15 answer key, printed p.110 / PDF
p.121 -- verbatim extraction captured in the Session 57
source-verification pass, diagnostics/latest_run.md):

  Framing (Section 10.1, printed p.100 / PDF p.111):

    "There are 2 kinds of aspects: (1) graha drishti and (2) rasi
    drishti. Drishti means aspect. Each planet aspects certain houses
    from it with graha drishti (planetary aspect). The houses aspected
    are fixed based on the planet. In addition, rasis aspect each other
    and a planet aspects the rasis aspected by the rasi occupied by it.
    This is called rasi drishti (sign aspect)."

  The rule itself (Section 10.3, printed p.102 / PDF p.113):

    "Rasis aspect other rasis based on the following rules:
    - A movable rasi aspects all fixed rasis except the one adjacent
      to it.
    - A fixed rasi aspects all movable rasis except the one adjacent
      to it.
    - A dual rasi aspects all other dual rasis."

  Three worked per-sign examples, verbatim (Section 10.3, printed p.102
  / PDF p.113), one per rasi type:

    "For example, Ar is a movable sign. It aspects all the fixed signs
    except the one adjacent to it, i.e. Ta. So Ar aspects Le, Sc and Aq.

    Ta is a fixed sign. It aspects all the movable signs except the one
    adjacent to it, i.e. Ar. So Ta aspects Cn, Li and Cp.

    Ge is a dual sign. It aspects all other dual signs. So Ge aspects
    Vi, Sg and Pi."

  Symmetry, stated explicitly (Section 10.3, printed p.102 / PDF
  p.113):

    "It may be noted that sign Y will aspect sign X if sign X aspects
    sign Y. A visual representation of rasi aspects is given in Figure
    2. A line is drawn between every pair of signs that aspect each
    other."

  Planets carry the sign's aspect -- both directions stated explicitly
  (Section 10.1, printed p.100 / PDF p.111, and Section 10.3-10.4,
  printed p.102-103 / PDF pp.113-114):

    "In addition, rasis aspect each other and a planet aspects the
    rasis aspected by the rasi occupied by it."

    "A planet aspects the signs aspected by the sign it occupies. It
    also aspects the houses and planets in those signs. This aspect is
    called rasi drishti (sign aspect). For example, a planet in Libra
    will aspect the houses and planets in Aq, Ta and Le."

    "All planets in a sign will have rasi drishti on the same signs,
    just as people living in the same house see the same neighbors
    everyday and exert some influence over the same neighbors."

  Exercise 15 answer key -- per-planet worked table, 9 planets/nodes
  from "Chart 5" (printed p.110 / PDF p.121), verbatim:

    "Planet  | Aspected Rasis | Aspected Houses | Aspected Planets
    Sun     | Cn, Li, Cp     | 9th, 12th, 3rd  | Venus
    Moon    | Le, Sc, Aq     | 10th, 1st, 4th  | Rahu, Mars, Saturn, Ketu
    Mars    | Cp, Ar, Cn     | 3rd, 6th, 9th   | Venus, Moon
    Mercury | Pi, Ge, Vi     | 5th, 8th, 11th  | Jupiter
    Jupiter | Sg, Pi, Ge     | 2nd, 5th, 8th   | Mercury
    Venus   | Ta, Le, Sc     | 7th, 10th, 1st  | Sun, Rahu, Mars, Saturn
    Saturn  | Cp, Ar, Cn     | 3rd, 6th, 9th   | Venus, Moon
    Rahu    | Li, Cp, Ar     | 12th, 3rd, 6th  | Venus, Moon
    Ketu    | Ar, Cn, Li     | 6th, 9th, 12th  | Moon"

  Ketu anti-zodiacal note -- scope flag (Section 10.6 "Virodhargala",
  printed pp.105-106 / PDF pp.116-117): PVR states, for the SEPARATE
  argala/virodhargala mechanism only, NOT rasi drishti:

    "NOTE: If a sign contains Ketu, argalas and virodhargalas on it are
    counted anti-zodiacally. For example, let us say Ketu is in Vi.
    Then Le, Ge, Sc and Ta are the 2nd, 4th, 11th and 5th from Vi
    (counted anti-zodiacally) and planets in those signs cause argala
    on Vi and on the planets in Vi. Virodhargala is also counted
    similarly."

  This anti-zodiacal counting is explicitly scoped by PVR to "argalas
  and virodhargalas" only -- never stated to apply to rasi drishti.
  The Exercise 15 answer key's own Ketu row is the proof it does not
  transfer: Ketu occupies Aquarius (a fixed sign, inferred from the
  aspected-houses column) and its aspected-rasis row (Ar, Cn, Li)
  matches ordinary zodiacal movable/fixed/dual counting from Aquarius
  (excluding adjacent movable Capricorn) -- not a reversed count.

Oracle: none run against this module (pure primitive, no test file per
this task's scope). Downstream callers (arudha.py, a future Section
15.5.1 module) carry their own validation passes.

Pure functions, no ephemeris calls, no imports from
agent/calculations/core/aspects.py.
"""

from __future__ import annotations

_CANONICAL_SIGNS: tuple[str, ...] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

# Movable (chara) / fixed (sthira) / dual (dwiswabhava) classification --
# standard classical scheme, matches PVR's own worked examples (Ar
# movable, Ta fixed, Ge dual) and every row of the Exercise 15 answer
# key quoted above.
_MOVABLE_SIGNS = frozenset({"Aries", "Cancer", "Libra", "Capricorn"})
_FIXED_SIGNS = frozenset({"Taurus", "Leo", "Scorpio", "Aquarius"})
_DUAL_SIGNS = frozenset({"Gemini", "Virgo", "Sagittarius", "Pisces"})

assert _MOVABLE_SIGNS | _FIXED_SIGNS | _DUAL_SIGNS == set(_CANONICAL_SIGNS), (
    "movable/fixed/dual partition does not cover all 12 canonical signs"
)


def _build_rasi_aspect_sets() -> dict[str, frozenset[str]]:
    """Derive the rasi-drishti aspect set for each of the 12 signs
    directly from the movable/fixed/dual classification plus adjacency,
    per PVR Section 10.3's rule (see module CITATION). PVR prints the
    rule and 3 worked single-sign examples, not a full 12-sign table --
    the rule is the source-verbatim artifact, so this table is derived
    programmatically rather than hand-typed, and then cross-checked
    below against every worked example PVR does give (including all 9
    rows of the Exercise 15 answer key).
    """
    aspect_sets: dict[str, frozenset[str]] = {}
    for sign in _CANONICAL_SIGNS:
        index = _CANONICAL_SIGNS.index(sign)
        neighbors = {
            _CANONICAL_SIGNS[(index - 1) % 12],
            _CANONICAL_SIGNS[(index + 1) % 12],
        }
        if sign in _DUAL_SIGNS:
            # "A dual rasi aspects all other dual rasis" -- no adjacency
            # exclusion for the dual scheme.
            aspect_sets[sign] = frozenset(_DUAL_SIGNS - {sign})
            continue

        if sign in _MOVABLE_SIGNS:
            candidates = _FIXED_SIGNS
        else:
            candidates = _MOVABLE_SIGNS

        # Exactly one of the two neighbors is of the opposite
        # (movable<->fixed) class -- the other is always a dual sign,
        # by construction of the fixed movable/fixed/dual cycle around
        # the zodiac. That one neighbor is "the one adjacent to it"
        # PVR excludes.
        adjacent_of_opposite_class = candidates & neighbors
        assert len(adjacent_of_opposite_class) == 1, (
            f"{sign}: expected exactly 1 adjacent sign of the opposite "
            f"movable/fixed class, found {sorted(adjacent_of_opposite_class)}"
        )
        aspect_sets[sign] = frozenset(candidates - adjacent_of_opposite_class)

    return aspect_sets


_RASI_ASPECT_SETS: dict[str, frozenset[str]] = _build_rasi_aspect_sets()

# PVR states symmetry explicitly ("sign Y will aspect sign X if sign X
# aspects sign Y", Section 10.3) -- assert it holds as a machine-checked
# invariant on the derived table, not just a citation.
for _sign, _targets in _RASI_ASPECT_SETS.items():
    for _target in _targets:
        assert _sign in _RASI_ASPECT_SETS[_target], (
            f"rasi drishti asymmetry: {_sign} aspects {_target} but not "
            f"vice versa -- violates PVR Section 10.3's stated symmetry"
        )
del _sign, _targets, _target

# Cross-check against every worked example PVR gives, using full-name
# equivalents of his abbreviations (Ar=Aries, Ta=Taurus, Ge=Gemini, plus
# the full Exercise 15 answer key). A failure here means the derivation
# above has drifted from the source text.
_PVR_WORKED_EXAMPLES = {
    "Aries": frozenset({"Leo", "Scorpio", "Aquarius"}),
    "Taurus": frozenset({"Cancer", "Libra", "Capricorn"}),
    "Gemini": frozenset({"Virgo", "Sagittarius", "Pisces"}),
}
for _sign, _expected in _PVR_WORKED_EXAMPLES.items():
    assert _RASI_ASPECT_SETS[_sign] == _expected, (
        f"{_sign}: derived aspect set {sorted(_RASI_ASPECT_SETS[_sign])} "
        f"!= PVR's worked example {sorted(_expected)}"
    )
del _sign, _expected


def signs_rasi_aspected_by(sign: str) -> frozenset[str]:
    """Resolve the rasis that `sign` aspects via rasi drishti (sign
    aspect), per PVR Ch.10 Section 10.3 (see module CITATION).

    Args:
        sign: one of the 12 canonical rasis (Aries through Pisces),
            Title-case, same vocabulary as
            agent/calculations/core/aspects.py.

    Returns:
        Frozenset of canonical sign names aspected by `sign` (3 signs,
        always -- 3 fixed for a movable sign, 3 movable for a fixed
        sign, or 3 other duals for a dual sign).

    Raises:
        ValueError: sign not one of the 12 canonical rasis.
    """
    if sign not in _CANONICAL_SIGNS:
        raise ValueError(
            f"Unrecognized sign {sign!r}. Valid signs are the 12 "
            f"canonical rasis (Aries through Pisces)."
        )
    return _RASI_ASPECT_SETS[sign]


def rasi_aspects_between(sign_a: str, sign_b: str) -> bool:
    """Check whether sign_a aspects sign_b via rasi drishti (sign
    aspect). Symmetric by PVR's own stated rule (see module CITATION):
    rasi_aspects_between(a, b) == rasi_aspects_between(b, a) always.

    Args:
        sign_a: one of the 12 canonical rasis (Aries through Pisces).
        sign_b: one of the 12 canonical rasis (Aries through Pisces).

    Returns:
        True if sign_a aspects sign_b, else False. False when
        sign_a == sign_b (a sign never rasi-aspects itself under the
        movable/fixed/dual rule).

    Raises:
        ValueError: sign_a or sign_b not one of the 12 canonical rasis.
    """
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
    return sign_b in _RASI_ASPECT_SETS[sign_a]
