"""Jaimini stronger co-lord cascade -- P6, Master Build Plan order.

Implements PVR Ch.15 Section 15.5.1's "Stronger Co-Lord" cascade for
Scorpio (Mars/Ketu) and Aquarius (Saturn/Rahu) ONLY -- the two rasis
with a co-lord pair in this classical scheme. Every other sign has a
single classical lord and this module does not apply to it.

CITATION (PVR Narasimha Rao, "Vedic Astrology: An Integrated Approach",
Ch.15 Section 15.5.1, printed pp.201-203 / PDF pp.212-214 -- verbatim
extraction ratified in the two-source verification pass immediately
preceding this module, diagnostics/latest_run.md, cross-arbitrated
against PyJHora's house.py `stronger_planet`/`_stronger_planet_new`
family):

  Scope + framing (printed p.201 / PDF p.212):

    "15.5 Other Simple Strengths

    15.5.1
    Stronger Co-Lord

    When we find the arudha pada of a house falling in Scorpio or
    Aquarius, we need to find the stronger of Mars & Ketu (co-lords of
    Sc) and Saturn & Rahu (co-lords of Aq). The stronger lord acts its
    lord and decides the arudha pada. The stronger lord of Sc (or Aq)
    is also used in finding the duration of its dasa in many rasi
    dasas (e.g. Narayana dasa)."

  Basic Rule + cascade framing (printed p.202 / PDF p.213):

    "Basic rule: If one of the co-lords is in the rasi, take the other
    planet. For example, if Saturn is in Aq and Rahu is in a rasi
    other than Aq, Rahu becomes the primary lord of Aq. If not, we
    find the stronger of the 2 planets and the stronger planet becomes
    the primary lord.

    The stronger planet of two planets is determined using the
    following rules. We go from one rule to the next, only if we do
    not have a winner. If we have a winner in one step, we do not go
    through the remaining steps."

  Step (1) -- joiner count (printed p.202 / PDF p.213):

    "(1) If one planet is joined by more planets than the other, it is
    stronger. Suppose Saturn is in Pi with Mars and Sun and Rahu is in
    Ar with Jupiter. Then Saturn is stronger than Rahu, because he is
    with 2 planets and Rahu is only with one planet. So Saturn becomes
    the primary lord of Aq."

  Step (2) -- conjoin/aspect count (printed p.202 / PDF p.213):

    "(2) We find how many of the following planets conjoin/aspect a
    planet: (1) Jupiter, (2) Mercury, and, (3) dispositor. A planet
    conjoined/aspected by more of these 3 planets is stronger. We must
    use rasi aspects here. Suppose Saturn is in Ge with Mercury, Rahu
    is in Ar, Mars is in Le, Jupiter is in Ta. Saturn is conjoined by
    Mercury and his dispositor (who is Mercury again). His count is 2.
    Rahu in Ar is aspected by Mars, his dispositor, from Le. Neither
    Jupiter nor Mercury aspects or conjoins Rahu. So Rahu's count of 1
    loses to Saturn's count of 2 and Saturn is the stronger planet. He
    becomes the lord of Aq."

  Step (3) -- exaltation (printed p.202 / PDF p.213):

    "(3) If one planet is exalted and the other not, then the exalted
    planet is stronger. Suppose Saturn is in Li and Rahu is in Cn,
    with the same number of planets. Suppose we have a tie after step
    (2). Then we note that Saturn is exalted in Li and declare him as
    the stronger planet. He becomes the primary lord of Aq."

  Step (4) -- modality, dual/fixed/movable (printed p.202 / PDF p.213):

    "(4) If we have a tie after (3), we consider the natural strength
    of the rasi containing the planet. Dual rasis are stronger than
    fixed rasis and fixed rasis are stronger than movable rasis.
    Suppose Mars is in Ge and Ketu is in Aq and we have a tie between
    them after step (3). Then we declare Mars as the stronger planet
    and the primary lord of Sc, because he is in a dual rasi and Ketu
    is in a fixed rasi."

  Step (5)(a) -- dasa-duration tiebreak, OUT OF V1 SCOPE, see design
  lock D5 (printed pp.202-203 / PDF pp.213-214, footnote 53):

    "(5) (a) When finding dasa duration: If we have a tie after (4),
    we take the planet giving a larger length for dasa. Supose [sic]
    Saturn is in Ge and Rahu is in Vi and suppose we have a tie after
    (4). Suppose we want to find the stronger lord for Narayana dasa.
    Rahu in Vi gives 5 years and Saturn in Ge gives 8 years[53]. So
    Saturn is used instead of Rahu."

    Footnote 53 (printed p.202, foot of page): "We will learn the
    computation of dasa years in Narayana dasa later."

  Step (5)(b) -- advancement-in-sign tiebreak (printed p.203 / PDF
  p.214):

    "(b) When finding the lord for arudha padas etc: If we have a tie
    after (4), we take the planet that is more advanced in its rasi.
    We measure the advancement of Rahu and Ketu from the end of the
    rasi. Suppose Mars is at 23Li17 and Ketu is at 5Cn54. Suppose we
    have a tie after (4). Advancement of Mars in Li is 23deg17'.
    Advancement of Ketu from the end of Cn is 30deg - 5deg54' =
    24deg6'. Because Ketu is more advanced, Ketu is stronger than Mars
    and becomes the primary lord of Sc."

  Exercise 25 + full answer key (printed pp.203, 205-206 / PDF pp.214,
  216-217):

    "Exercise 25: Find the primary lord of Aq and Sc in Chart 12 for
    the purpose of arudha padas."

    "Rahu is alone and Saturn is alone. We have a tie after rule (1).
    Saturn is aspected by Mercury and not aspected/conjoined by
    Jupiter and his dispositor (Jupiter again). Rahu is aspected by
    Venus (his dispositor) and not aspected by Mercury and Jupiter.
    Both have a count of one and we have a tie after rule (2). Neither
    Saturn nor Rahu is exalted after rule (3). Now we use rule (4).
    Saturn is in a dual rasi and Rahu is in a movable rasi. So Saturn
    is stronger and he becomes the primary lord of Aq.

    Mars is in Sc and Ketu is elsewhere (in Ar). So we don't even have
    to go through the rules to find the stronger planet. We use the
    'basic rule' and declare Ketu as the primary lord of Sc."

DESIGN LOCKS (D1-D6) -- all V1 scope decisions made where PVR's own
text is silent; see diagnostics/latest_run.md's two-source
verification pass for the full ambiguity/deviation writeup each of
these resolves:

  D1 (Step 1 joiner scope): PVR's own worked example ("Saturn is in Pi
    with Mars and Sun") only ever uses classical grahas as joiners --
    it never tests whether Rahu/Ketu count as a joining body, and the
    rule text itself does not qualify the 8-graha vs 6-graha question
    either way. This module adopts 9-graha counting (all planets
    other than the candidate itself, nodes included) -- PyJHora-
    lineage precedent (house.py's `_stronger_planet_new` Rule-1
    iterates the full Sun-through-Ketu p_to_h dict with no node
    exclusion). Tiebreaker-decision class: revisit only if a future
    oracle chart's Step-1 joiner count flips outcome depending on
    7-vs-9 scope.

  D2 (Basic Rule both-resident gap): PVR's Basic Rule text only covers
    the case where exactly one co-lord occupies the contested sign
    ("If one of the co-lords is in the rasi, take the other planet").
    It is silent on both co-lords occupying the SAME contested sign
    simultaneously (Saturn AND Rahu both in Aquarius, or Mars AND Ketu
    both in Scorpio) -- a real, non-hypothetical transit configuration
    (e.g. 2022-23, when Saturn and Rahu were both transiting Aquarius
    for an extended window). Step 2's dispositor lookup is also
    circular in this exact configuration (see D3) -- a candidate
    residing in the very sign whose lordship is being contested makes
    "dispositor of the candidate's sign" self-referential in a way
    PVR's ordinary-lord convention was never built to resolve. This
    module fails closed with ValueError rather than silently guessing
    a winner; known V1 gap, not a bug.

  D3 (Step 2 dispositor definition): "Dispositor" = the ordinary
    classical lord of the candidate's occupied sign -- PVR's own
    Step-2 example uses this reading for BOTH a classical planet
    (Saturn in Gemini -> dispositor Mercury) and a node (Rahu in
    Aries -> dispositor Mars, "his dispositor"; reconfirmed in
    Exercise 25's answer, Rahu in Libra -> dispositor Venus). No
    special node-dispositor rule exists in the source; none is added
    here. For a candidate that happens to occupy Scorpio or Aquarius
    itself (as some OTHER sign it is merely transiting through, NOT
    the contested sign -- that both-resident configuration is already
    excluded upstream by the Basic Rule / D2 guard), this module uses
    the CLASSICAL lord (Mars for Scorpio, Saturn for Aquarius) as the
    dispositor, never re-entering this same cascade -- PVR's own
    examples always resolve "dispositor" via the ordinary lord, never
    via a nested stronger-co-lord call, and the co-lord question never
    recurses because a candidate can't occupy the very sign being
    contested without hitting the Basic Rule / D2 path first. Self-
    dispositor conjoins trivially (+1 automatically, mechanical no-
    exclusion reading, falls out of the general formula with no
    special-cased code): PVR's text never excludes a planet-is-its-
    own-dispositor case, and PyJHora's own conjoin-half implementation
    (house.py:335) offers no counter-evidence to exclude it either
    (that line has a separate id-space bug, unrelated to self-
    exclusion -- see diagnostics/latest_run.md's deviation flag).
    Revisit trigger: none identified; this is a mechanical reading of
    silence, not an oracle-backed choice.

  D4 (Step 3 Rahu/Ketu never exalted): PVR's own Step-3 example
    ("Saturn is exalted in Li") only ever exalts a classical planet;
    Section 15.5.1 never states an exaltation sign for Rahu or Ketu,
    and school-divergent alternatives exist (e.g. Rahu exalted in
    Taurus or Gemini under different classical traditions) that PVR
    does not adopt anywhere in this section. This module treats
    Rahu/Ketu as NEVER exalted for Step 3's purposes -- V1 lock, not a
    universal claim about node dignity. PyJHora's own Rule-3 cannot
    arbitrate this either way: its second branch compares
    `house_strengths_of_planets[planet2][planet2_house] >
    house_strengths_of_planets[planet2][planet2_house]` (planet2
    against itself, always False by construction -- doubly buggy, see
    diagnostics/latest_run.md), so it never actually exercises a
    Rahu/Ketu-exalted branch either. Revisit trigger: a real oracle
    chart (JHora) where a Rahu/Ketu exaltation claim changes a
    stronger-co-lord outcome.

  D5 (purpose="dasa_duration" out of V1 scope): PVR's Step 5(a)
    resolves a Step-4 tie using Narayana dasa duration length ("Rahu
    in Vi gives 5 years and Saturn in Ge gives 8 years") -- footnote
    53 explicitly defers that computation to a LATER chapter ("We
    will learn the computation of dasa years in Narayana dasa
    later."), i.e. PVR himself does not make Step 5(a) self-contained
    within Section 15.5.1. Implementing it here would be oracle-free
    code (no dasa-duration engine exists yet in this codebase to
    validate Step 5(a) against). purpose="dasa_duration" therefore
    raises ValueError rather than silently falling through to 5(b)'s
    different tiebreak -- V1 scope decision, revisit once Narayana
    dasa duration ships.

  D6 (Step 5(b) exact tie fails closed): if the two candidates'
    advancement-in-sign values are exactly equal to full float
    precision, this module raises ValueError rather than picking a
    winner arbitrarily -- same fail-closed posture and message style
    as karakas.py's exact-tie handling (see karakas.py's own CITATION
    for the PVR precedent behind this posture in the sibling chara-
    karaka advancement tie). PVR's Section 15.5.1 text itself never
    discusses a Step-5(b) exact tie (steps (1)-(5b) are presented as
    if always terminating); this module does not silently invent an
    insertion-order winner.

Oracle: none run against this module (pure kernel, no test file per
this task's scope). Downstream callers (a future arudha-lordship
module) carry their own validation passes.

Pure function, NO ephemeris calls (same pattern as karakas.py and
rasi_aspects.py): the caller supplies precomputed sidereal longitudes.

Uses jaimini.rasi_aspects.rasi_aspects_between for Step 2's aspect
check -- rasi drishti (sign aspect), per PVR's own explicit
instruction ("We must use rasi aspects here."). NEVER
calculations.aspects (graha drishti / planetary aspect) -- the two are
different classical mechanisms; conflating them here would silently
misimplement Step 2. See rasi_aspects.py's own LOUD docstring warning.
"""

from __future__ import annotations

from dataclasses import dataclass

from agent.calculations.jaimini.rasi_aspects import rasi_aspects_between

_REQUIRED_PLANETS: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)

_CANONICAL_SIGNS: tuple[str, ...] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

# Co-lord candidates for the two contested signs -- PVR Section
# 15.5.1's own scope ("...falling in Scorpio or Aquarius, we need to
# find the stronger of Mars & Ketu (co-lords of Sc) and Saturn & Rahu
# (co-lords of Aq)"). This module implements ONLY these two signs.
_CO_LORDS: dict[str, tuple[str, str]] = {
    "Scorpio": ("Mars", "Ketu"),
    "Aquarius": ("Saturn", "Rahu"),
}

# Classical (single) sign lords -- used ONLY for Step 2's dispositor
# lookup (design lock D3), never for anything else. Scorpio/Aquarius
# map to their CLASSICAL lord (Mars/Saturn), not a re-entrant
# stronger-co-lord call -- see D3.
_CLASSICAL_SIGN_LORDS: dict[str, str] = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}

# Step 3 exaltation signs -- PVR Section 15.5.1's own Step-3 example
# ("Saturn is exalted in Li") plus the classical standard for the
# other 6 grahas. Rahu/Ketu deliberately absent -- see design lock D4
# (never exalted for this module's Step 3).
_EXALTATION_SIGN: dict[str, str] = {
    "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn", "Mercury": "Virgo",
    "Jupiter": "Cancer", "Venus": "Pisces", "Saturn": "Libra",
}

# Step 4 modality ranks -- PVR Section 15.5.1 Step 4 verbatim: "Dual
# rasis are stronger than fixed rasis and fixed rasis are stronger
# than movable rasis." Higher rank wins.
_MOVABLE_SIGNS = frozenset({"Aries", "Cancer", "Libra", "Capricorn"})
_FIXED_SIGNS = frozenset({"Taurus", "Leo", "Scorpio", "Aquarius"})
_DUAL_SIGNS = frozenset({"Gemini", "Virgo", "Sagittarius", "Pisces"})


@dataclass(frozen=True)
class StrongerCoLordResult:
    sign: str
    winner: str
    loser: str
    # one of "basic_rule", "step_1", "step_2", "step_3", "step_4", "step_5b"
    deciding_step: str
    # (label, value) pairs, in evaluation order -- steps after the
    # deciding one are absent. Tuple of pairs (not a dict), for
    # hashability, matching CharaKarakasResult's shape discipline.
    diagnostics: tuple[tuple[str, object], ...]


def _sign_of(longitude: float) -> str:
    return _CANONICAL_SIGNS[int(longitude // 30) % 12]


def _advancement(planet: str, longitude: float) -> float:
    # Same convention as karakas.py: classical planets measure from
    # the beginning of the occupied sign; Rahu/Ketu measure from the
    # END of the occupied sign -- PVR verbatim, Step 5(b): "Advancement
    # of Ketu from the end of Cn is 30deg - 5deg54' = 24deg6'."
    remainder = longitude % 30.0
    if planet in ("Rahu", "Ketu"):
        return 30.0 - remainder
    return remainder


def _modality_rank(sign: str) -> int:
    if sign in _DUAL_SIGNS:
        return 3
    if sign in _FIXED_SIGNS:
        return 2
    return 1


def stronger_co_lord(
    sign: str,
    planet_longitudes: dict[str, float],
    purpose: str = "arudha",
) -> StrongerCoLordResult:
    """Resolve the stronger co-lord of Scorpio (Mars/Ketu) or Aquarius
    (Saturn/Rahu) per PVR Ch.15 Section 15.5.1 (see module CITATION).

    Args:
        sign: "Scorpio" or "Aquarius" -- the only two co-lorded signs
            this cascade is defined for.
        planet_longitudes: absolute sidereal longitudes in degrees
            ([0, 360) expected), Title-case planet-name keys. Exactly
            the 9 keys in _REQUIRED_PLANETS are required -- Sun, Moon,
            Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu.
        purpose: "arudha" (default) runs the full cascade through Step
            5(b). "dasa_duration" is out of V1 scope (design lock D5)
            and raises. Any other value raises.

    Returns:
        StrongerCoLordResult.

    Raises:
        ValueError: sign not "Scorpio"/"Aquarius"; purpose is
            "dasa_duration" (design lock D5, V1 scope) or any value
            other than "arudha"; planet_longitudes missing/extra keys;
            any longitude not in [0, 360) sidereal degrees (NaN
            included); both co-lord candidates occupy the contested
            sign simultaneously (design lock D2, Basic Rule gap); an
            exact advancement tie survives to Step 5(b) (design lock
            D6, fail-closed).
    """
    if sign not in _CO_LORDS:
        raise ValueError(
            f"Unrecognized sign {sign!r}. The stronger co-lord cascade "
            f"(PVR Ch.15 Section 15.5.1) is defined only for the two "
            f"co-lorded signs, 'Scorpio' (Mars/Ketu) and 'Aquarius' "
            f"(Saturn/Rahu) -- every other sign has a single classical "
            f"lord and this cascade does not apply to it."
        )

    if purpose == "dasa_duration":
        raise ValueError(
            "purpose='dasa_duration' is out of V1 scope (design lock "
            "D5): PVR's Step 5(a) resolves a Step-4 tie using Narayana "
            "dasa duration length, but footnote 53 explicitly defers "
            "that computation to a later chapter ('We will learn the "
            "computation of dasa years in Narayana dasa later.') -- no "
            "dasa-duration engine exists yet in this codebase to "
            "validate Step 5(a) against, so implementing it now would "
            "be oracle-free code. Use purpose='arudha' (Step 5(b)) "
            "instead, or revisit this once Narayana dasa duration ships."
        )
    if purpose != "arudha":
        raise ValueError(
            f"Unrecognized purpose {purpose!r}. Recognized values are "
            f"'arudha' (Step 5(b), the only cascade this module "
            f"implements) and 'dasa_duration' (Step 5(a), explicitly "
            f"out of V1 scope -- see design lock D5)."
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

    candidate_a, candidate_b = _CO_LORDS[sign]
    sign_occupancy = {p: _sign_of(planet_longitudes[p]) for p in _REQUIRED_PLANETS}
    sign_a = sign_occupancy[candidate_a]
    sign_b = sign_occupancy[candidate_b]

    a_resident = sign_a == sign
    b_resident = sign_b == sign

    if a_resident and b_resident:
        raise ValueError(
            f"{candidate_a} and {candidate_b} are BOTH in {sign} -- "
            f"design lock D2 (Basic Rule both-resident gap): PVR's "
            f"Basic Rule ('If one of the co-lords is in the rasi, take "
            f"the other planet') only covers the case where exactly "
            f"one co-lord occupies the contested sign; it is silent on "
            f"both occupying it simultaneously, and Step 2's dispositor "
            f"lookup is circular in this exact configuration (a "
            f"candidate residing in the very sign whose lordship is "
            f"being contested). This is a real transit configuration, "
            f"not a hypothetical -- e.g. Saturn and Rahu both "
            f"transited Aquarius in 2022-23. Known V1 gap: this module "
            f"fails closed rather than guessing a winner."
        )

    diagnostics: list[tuple[str, object]] = []

    # --- Basic Rule: exactly one candidate resident -> the OTHER wins ---
    if a_resident or b_resident:
        winner, loser = (
            (candidate_b, candidate_a) if a_resident else (candidate_a, candidate_b)
        )
        return StrongerCoLordResult(
            sign=sign, winner=winner, loser=loser,
            deciding_step="basic_rule", diagnostics=tuple(diagnostics),
        )

    # --- Step 1: joiner count (design lock D1: 9-graha scope) ---
    joiners_a = sum(
        1 for p in _REQUIRED_PLANETS
        if p != candidate_a and sign_occupancy[p] == sign_a
    )
    joiners_b = sum(
        1 for p in _REQUIRED_PLANETS
        if p != candidate_b and sign_occupancy[p] == sign_b
    )
    diagnostics.append(("step_1_joiners", (joiners_a, joiners_b)))
    if joiners_a != joiners_b:
        winner, loser = (
            (candidate_a, candidate_b) if joiners_a > joiners_b
            else (candidate_b, candidate_a)
        )
        return StrongerCoLordResult(
            sign=sign, winner=winner, loser=loser,
            deciding_step="step_1", diagnostics=tuple(diagnostics),
        )

    # --- Step 2: Jupiter/Mercury/dispositor conjoin-or-aspect count ---
    # (design lock D3). PVR's own oracle: "Saturn is conjoined by
    # Mercury and his dispositor (who is Mercury again). His count is
    # 2." -- counted PER ROLE, not per unique planet: Mercury-as-
    # listed-planet and Mercury-as-dispositor score separately even
    # though they are the same physical planet in that example. Max
    # count per candidate is 3.
    def _step2_tally(
        candidate: str, candidate_sign: str
    ) -> tuple[tuple[str, str, str, bool], ...]:
        dispositor = _CLASSICAL_SIGN_LORDS[candidate_sign]
        rows = []
        for role_label, role_planet in (
            ("Jupiter", "Jupiter"), ("Mercury", "Mercury"), ("dispositor", dispositor)
        ):
            role_sign = sign_occupancy[role_planet]
            conjoins = role_sign == candidate_sign
            # NEVER calculations.aspects (graha drishti) -- Step 2 is
            # explicitly rasi drishti ("We must use rasi aspects
            # here."), a different classical mechanism entirely.
            aspects = rasi_aspects_between(role_sign, candidate_sign)
            rows.append((candidate, role_label, role_planet, conjoins or aspects))
        return tuple(rows)

    tally_a = _step2_tally(candidate_a, sign_a)
    tally_b = _step2_tally(candidate_b, sign_b)
    count_a = sum(1 for row in tally_a if row[3])
    count_b = sum(1 for row in tally_b if row[3])
    diagnostics.append(("step_2_role_tally", tally_a + tally_b))
    diagnostics.append(("step_2_counts", (count_a, count_b)))
    if count_a != count_b:
        winner, loser = (
            (candidate_a, candidate_b) if count_a > count_b
            else (candidate_b, candidate_a)
        )
        return StrongerCoLordResult(
            sign=sign, winner=winner, loser=loser,
            deciding_step="step_2", diagnostics=tuple(diagnostics),
        )

    # --- Step 3: exaltation (design lock D4: Rahu/Ketu never exalted) ---
    exalted_a = _EXALTATION_SIGN.get(candidate_a) == sign_a
    exalted_b = _EXALTATION_SIGN.get(candidate_b) == sign_b
    diagnostics.append(("step_3_exalted", (exalted_a, exalted_b)))
    if exalted_a != exalted_b:
        winner, loser = (
            (candidate_a, candidate_b) if exalted_a else (candidate_b, candidate_a)
        )
        return StrongerCoLordResult(
            sign=sign, winner=winner, loser=loser,
            deciding_step="step_3", diagnostics=tuple(diagnostics),
        )

    # --- Step 4: modality (dual > fixed > movable) ---
    rank_a = _modality_rank(sign_a)
    rank_b = _modality_rank(sign_b)
    diagnostics.append(("step_4_modality_rank", (rank_a, rank_b)))
    if rank_a != rank_b:
        winner, loser = (
            (candidate_a, candidate_b) if rank_a > rank_b
            else (candidate_b, candidate_a)
        )
        return StrongerCoLordResult(
            sign=sign, winner=winner, loser=loser,
            deciding_step="step_4", diagnostics=tuple(diagnostics),
        )

    # --- Step 5(b): advancement-in-sign (design lock D6: exact tie fails closed) ---
    advancement_a = _advancement(candidate_a, planet_longitudes[candidate_a])
    advancement_b = _advancement(candidate_b, planet_longitudes[candidate_b])
    diagnostics.append(("step_5b_advancement", (advancement_a, advancement_b)))
    if advancement_a == advancement_b:
        raise ValueError(
            f"{candidate_a} and {candidate_b} have an exact advancement "
            f"tie in {sign} (identical to full float precision) after "
            f"exhausting all of PVR's Section 15.5.1 steps (1)-(5b). "
            f"Design lock D6: this module fails closed rather than "
            f"picking a winner arbitrarily -- PVR's own text never "
            f"discusses a Step-5(b) exact tie, and karakas.py's sibling "
            f"advancement-tie handling sets the precedent for this "
            f"fail-closed posture."
        )
    winner, loser = (
        (candidate_a, candidate_b) if advancement_a > advancement_b
        else (candidate_b, candidate_a)
    )
    return StrongerCoLordResult(
        sign=sign, winner=winner, loser=loser,
        deciding_step="step_5b", diagnostics=tuple(diagnostics),
    )
