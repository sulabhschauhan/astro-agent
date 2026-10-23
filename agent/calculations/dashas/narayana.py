"""Narayana Dasa -- Jaimini rasi (phalita) dasa. PVR Narasimha Rao "Vedic
Astrology: An Integrated Approach", Ch.18 (printed pp.231-240 / PDF pp.242-251).

This is the Jaimini rasi dasa PVR teaches as the primary one; it is what
"chara dasa" colloquially refers to in a PVR-grounded stack (PVR never uses the
name "chara dasa" -- the K.N.-Rao variant of that name is a different school and
is deliberately NOT implemented here).

COMPUTATION (V1 = D1/rasi chart only; PVR notes Narayana is computed per varga,
deferred):

  SEED -- the stronger of the 1st and 7th house (whole-sign), via
  jaimini.strength.stronger_rasi (§15.5.2, oracle-validated separately).

  PROGRESSION -- which rasis get dasas and in what order. PVR's Table 40 (p.234-
  235) prints all 12 seeds x 3 cases (normal / Saturn-in-seed / Ketu-in-seed);
  it is the book's own canonical output, so it is ENCODED here as the authority
  (same pattern as navamsa._NAVAMSA_START_SIGN -- a cited lookup, not a runtime
  re-derivation of the Brahma/Shiva/Vishnu movement rules). Saturn-in-seed and
  Ketu-in-seed select the (b)/(c) rows; Saturn takes precedence if (rarely) both
  occupy the seed.

  LENGTH (§18.2.2) -- count from the dasa rasi to its lord, FORWARD if the rasi
  is odd-footed, BACKWARD if even-footed; length = count - 1 years. Exceptions:
  count==1 (lord in own rasi) -> 12 years; lord exalted +1; lord debilitated -1.
  Second cycle: 12 - (first-cycle length).

  AQ/SC LORD (the D5 solve, ratified) -- these two signs are co-lorded. Steps
  1-4 of the stronger-co-lord cascade (§15.5.1) are PURPOSE-INDEPENDENT, so we
  reuse the validated jaimini.strength.stronger_co_lord(purpose="arudha") for
  them. ONLY when that cascade reaches Step 5 (deciding_step=="step_5b", or it
  fails closed on an exact Step-5b tie) do we apply PVR's dasa-duration Step 5(a)
  HERE: the co-lord that yields the LARGER dasa length is the lord. This keeps
  stronger_co_lord's D5 lock intact (it stays arudha-only) while giving Narayana
  the correct dasa-duration tie-break it needs -- see that module's D5 note.

VALIDATION: progression vs Table 40 + the 5 worked sequences (Ex.63-66, 68);
length formula vs Example 66's 12 worked cells. End-to-end (seed + per-chart
lengths) is oracle-checked against JHora Narayana on the 4 reference charts.

Pure function of (asc_sign, planet_longitudes) apart from NO ephemeris calls --
the caller supplies precomputed sidereal longitudes (same pattern as karakas.py
and the stronger-rasi/co-lord engines this composes).

Python 3.11.
"""
from __future__ import annotations

from dataclasses import dataclass

from agent.calculations.jaimini.strength import (
    _CANONICAL_SIGNS, _CLASSICAL_SIGN_LORDS, _CO_LORDS, _DUAL_SIGNS,
    _EXALTATION_SIGN, _FIXED_SIGNS, _MOVABLE_SIGNS, _REQUIRED_PLANETS,
    _sign_of, stronger_co_lord, stronger_rasi,
)

__all__ = ["compute_narayana_dasa", "compute_narayana_antardasha",
           "NarayanaDasa", "NarayanaPeriod", "DASA_PROGRESSION"]

# Odd-footed vs even-footed signs (§18.2.2 counting direction). NOT the same as
# odd/even signs: odd-footed = 1-3 + 7-9, even-footed = 4-6 + 10-12.
_ODD_FOOTED = frozenset({
    "Aries", "Taurus", "Gemini", "Libra", "Scorpio", "Sagittarius",
})

# Debilitation = 7th from exaltation (nodes absent, matching _EXALTATION_SIGN's
# D4 node exclusion -> no node exalt/debil length adjustment).
_DEBILITATION_SIGN = {
    p: _CANONICAL_SIGNS[(_CANONICAL_SIGNS.index(s) + 6) % 12]
    for p, s in _EXALTATION_SIGN.items()
}

# ── Dasa progression, COMPUTED from PVR's movement rules (§18.2.1, pp.231-234),
# not a transcribed table. The seed's MODALITY picks the movement (movable =
# Brahma, regular step of 1; fixed = Shiva, "every 6th" = step of 5; dual =
# Vishnu, trinal), the 9th-from-seed being odd/even-footed picks the base
# DIRECTION (forward / backward), and the exceptions override it: Saturn in the
# seed -> Brahma forward (regular zodiacal); Ketu in the seed -> reverse the base
# direction. A test cross-validates all 36 (12 seeds x {normal, saturn, ketu})
# against PVR's printed Table 40 (p.234-235), so the algorithm and PVR's own
# table independently agree on every row.

def _base_direction(seed: str) -> int:
    """+1 forward / -1 backward, from whether the 9th-from-seed is odd-footed."""
    ninth = _CANONICAL_SIGNS[(_CANONICAL_SIGNS.index(seed) + 8) % 12]
    return 1 if ninth in _ODD_FOOTED else -1


def _brahma(si: int, d: int) -> list[int]:
    return [(si + d * k) % 12 for k in range(12)]           # regular, step 1


def _shiva(si: int, d: int) -> list[int]:
    return [(si + d * 5 * k) % 12 for k in range(12)]       # "every 6th" = step 5


def _vishnu(si: int, d: int) -> list[int]:
    # Trinal: four quadrant group-starts, each expanded to its three trines.
    # Forward goes seed -> 10th -> 7th -> 4th with +0/+4/+8; backward mirrors it.
    groups = (0, 9, 6, 3) if d == 1 else (0, 3, 6, 9)
    trines = (0, 4, 8) if d == 1 else (0, -4, -8)
    return [(si + g + t) % 12 for g in groups for t in trines]


def _compute_progression(seed: str, case: str) -> tuple[str, ...]:
    """The 12-rasi dasa sequence for a seed + exception case (normal/saturn/ketu),
    derived from §18.2.1's movement + direction + exception rules."""
    si = _CANONICAL_SIGNS.index(seed)
    if case == "saturn":
        idxs = _brahma(si, 1)                               # regular zodiacal fwd
    else:
        d = _base_direction(seed)
        if case == "ketu":
            d = -d                                          # reverse base direction
        if seed in _MOVABLE_SIGNS:
            idxs = _brahma(si, d)
        elif seed in _FIXED_SIGNS:
            idxs = _shiva(si, d)
        else:                                               # dual -> Vishnu
            idxs = _vishnu(si, d)
    return tuple(_CANONICAL_SIGNS[i] for i in idxs)


DASA_PROGRESSION: dict[str, dict[str, tuple[str, ...]]] = {
    seed: {case: _compute_progression(seed, case)
           for case in ("normal", "saturn", "ketu")}
    for seed in _CANONICAL_SIGNS
}


@dataclass(frozen=True)
class NarayanaPeriod:
    rasi: str
    lord: str
    years: int
    cycle: int  # 1 (first cycle) or 2 (second cycle)


@dataclass(frozen=True)
class NarayanaDasa:
    seed: str
    seed_rule: str            # deciding rule from stronger_rasi
    progression_case: str     # "normal" | "saturn" | "ketu"
    periods: tuple[NarayanaPeriod, ...]   # 24 (two cycles x 12), in time order


def _count_to_lord(rasi: str, lord_sign: str) -> int:
    """House count from `rasi` to `lord_sign`, counting `rasi` as 1. Forward if
    `rasi` is odd-footed, backward if even-footed (§18.2.2)."""
    ri = _CANONICAL_SIGNS.index(rasi)
    li = _CANONICAL_SIGNS.index(lord_sign)
    if rasi in _ODD_FOOTED:
        return (li - ri) % 12 + 1          # forward
    return (ri - li) % 12 + 1              # backward


def _length_for_lord(rasi: str, lord: str, lord_sign: str) -> int:
    """First-cycle dasa length (years) for `rasi` given `lord` sits in
    `lord_sign` (§18.2.2). count==1 -> 12; +1 exalted, -1 debilitated."""
    count = _count_to_lord(rasi, lord_sign)
    if count == 1:
        return 12                          # lord in its own rasi
    years = count - 1
    if _EXALTATION_SIGN.get(lord) == lord_sign:
        years += 1
    elif _DEBILITATION_SIGN.get(lord) == lord_sign:
        years -= 1
    return years


def _lord_and_length(rasi: str, occ: dict[str, str],
                     planet_longitudes: dict[str, float]) -> tuple[str, int]:
    """(lord, first-cycle length) for one dasa rasi. Single-lorded signs use the
    classical lord; Aq/Sc apply the D5 solve (see module docstring)."""
    if rasi not in _CO_LORDS:
        lord = _CLASSICAL_SIGN_LORDS[rasi]
        return lord, _length_for_lord(rasi, lord, occ[lord])

    c1, c2 = _CO_LORDS[rasi]
    # Steps 1-4 are purpose-independent; reuse the validated arudha cascade.
    reached_step5 = False
    cascade_winner = None
    try:
        res = stronger_co_lord(rasi, planet_longitudes, purpose="arudha")
        cascade_winner = res.winner
        reached_step5 = res.deciding_step == "step_5b"
    except ValueError:
        # D2 (both co-lords in the sign) or D6 (exact Step-5b tie) -> treat as
        # reaching Step 5, where the dasa-duration tie-break (5a) takes over.
        reached_step5 = True

    if not reached_step5:
        lord = cascade_winner
        return lord, _length_for_lord(rasi, lord, occ[lord])

    # Step 5(a), dasa-duration: the co-lord giving the LARGER length wins.
    len1 = _length_for_lord(rasi, c1, occ[c1])
    len2 = _length_for_lord(rasi, c2, occ[c2])
    if len1 != len2:
        lord = c1 if len1 > len2 else c2
    else:
        # Equal lengths: fall back to the arudha winner if the cascade produced
        # one (Step-5b), else the first co-lord. A true tie here is doubly rare.
        lord = cascade_winner or c1
    return lord, _length_for_lord(rasi, lord, occ[lord])


def compute_narayana_dasa(
    asc_sign: str,
    planet_longitudes: dict[str, float],
) -> NarayanaDasa:
    """Narayana dasa (D1) for a chart.

    Args:
        asc_sign: the natal lagna's sign (D1).
        planet_longitudes: the 9 _REQUIRED_PLANETS absolute sidereal longitudes
            (Sun..Ketu), same contract as stronger_rasi/stronger_co_lord.

    Returns:
        NarayanaDasa with 24 periods (two cycles) in time order from birth.

    Raises:
        ValueError: unknown asc_sign; bad planet_longitudes (delegated to
            stronger_rasi); or a seed/co-lord tie that fails closed upstream.
    """
    if asc_sign not in _CANONICAL_SIGNS:
        raise ValueError(f"asc_sign must be a canonical sign; got {asc_sign!r}")

    seventh = _CANONICAL_SIGNS[(_CANONICAL_SIGNS.index(asc_sign) + 6) % 12]
    seed_res = stronger_rasi(asc_sign, seventh, planet_longitudes)
    seed = seed_res.winner

    occ = {p: _sign_of(planet_longitudes[p]) for p in _REQUIRED_PLANETS}
    if occ["Saturn"] == seed:
        case = "saturn"
    elif occ["Ketu"] == seed:
        case = "ketu"
    else:
        case = "normal"

    sequence = DASA_PROGRESSION[seed][case]

    periods: list[NarayanaPeriod] = []
    first_lengths: dict[str, tuple[str, int]] = {}
    for rasi in sequence:
        lord, years = _lord_and_length(rasi, occ, planet_longitudes)
        first_lengths[rasi] = (lord, years)
        periods.append(NarayanaPeriod(rasi=rasi, lord=lord, years=years, cycle=1))
    for rasi in sequence:
        lord, first = first_lengths[rasi]
        periods.append(NarayanaPeriod(rasi=rasi, lord=lord, years=12 - first, cycle=2))

    return NarayanaDasa(
        seed=seed, seed_rule=seed_res.deciding_rule,
        progression_case=case, periods=tuple(periods),
    )


# ── Antardasa progression (PVR §18.3; book-faithful per Example 67) ──────────
# Odd SIGNS (not odd-footed): Aries, Gemini, Leo, Libra, Sagittarius, Aquarius.
_NARAYANA_ODD_SIGNS = frozenset({
    "Aries", "Gemini", "Leo", "Libra", "Sagittarius", "Aquarius",
})

# forced dasa-lords matching JHora desktop; validated against Sulabh's AD oracle
_NARAYANA_DASA_LORD_OVERRIDE = {"Scorpio": "Ketu", "Aquarius": "Saturn"}


def compute_narayana_antardasha(
    dasa_rasi: str,
    planet_longitudes: dict[str, float],
) -> tuple[str, ...]:
    """The 12 antardasa rasis (time order) inside the mahadasa of `dasa_rasi`.

    Seed = stronger_rasi(dasa_rasi, 7th-from-it); first AD = the sign occupied
    by the seed's lord (Sc -> Ketu, Aq -> Saturn); direction is + if that sign is
    an odd sign else -; Saturn in the seed forces +, Ketu in the seed flips
    (Saturn wins if both, mirroring the MD convention).

    Raises:
        ValueError: unknown dasa_rasi; bad planet_longitudes (delegated).
    """
    if dasa_rasi not in _CANONICAL_SIGNS:
        raise ValueError(f"dasa_rasi must be a canonical sign; got {dasa_rasi!r}")

    seventh = _CANONICAL_SIGNS[(_CANONICAL_SIGNS.index(dasa_rasi) + 6) % 12]
    seed = stronger_rasi(dasa_rasi, seventh, planet_longitudes).winner

    occ = {p: _sign_of(planet_longitudes[p]) for p in _REQUIRED_PLANETS}
    lord = _NARAYANA_DASA_LORD_OVERRIDE.get(seed) or _CLASSICAL_SIGN_LORDS[seed]
    first = occ[lord]

    direction = 1 if first in _NARAYANA_ODD_SIGNS else -1
    if occ["Saturn"] == seed:
        direction = 1
    elif occ["Ketu"] == seed:
        direction = -direction

    fi = _CANONICAL_SIGNS.index(first)
    return tuple(_CANONICAL_SIGNS[(fi + direction * i) % 12] for i in range(12))
