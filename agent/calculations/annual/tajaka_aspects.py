"""Tajika annual aspect yogas -- Ithasala / Ishrafa and the companion yogas.

WHAT THIS IS
    The predictive layer of Tajika/Varshaphal: given the annual (Varsha Pravesh)
    chart, which planet pairs are in an APPLYING aspect (Ithasala -- the matter
    ripens this year) vs a SEPARATING one (Ishrafa/Eesarpha -- the matter is
    just past), plus the companion yogas built on them.

SPEC SOURCE (faithful port, NOT from memory -- Validation-Source rule):
    PyJHora `horoscope/transit/tajaka.py` + `tajaka_yoga.py`
    (naturalstupid/PyJHora, GNU AGPL). The deeptamsa orb table and the
    fixed speed order are PyJHora's `const.deeptaamsa_of_planets` /
    `const.order_of_planets_by_speed`:
        deeptamsa (Sun..Saturn) = 15,12,8,7,9,7,9 degrees
        speed order (slow->fast) = Sa, Ra, Ke, Ju, Ma, Su, Ve, Me, Mo

WHY NO JHORA DESKTOP ORACLE IS NEEDED (ruled with Sulabh, S169):
    Ithasala is a DETERMINISTIC function of the annual longitudes + the fixed
    deeptamsa table + the fixed speed order. Unlike the sahams (contested
    formulas -> needed a JHora oracle), there is no free parameter here, so
    there is nothing to grade against an external source -- only "is the
    arithmetic the definition?". Validation = hand-verified pairs + a
    byte-for-byte cross-check against PyJHora's own functions on the same
    positions (the test does both).

THREE MODELS, kept distinct -- do NOT conflate (S169):
    * Tajika sign-aspect  : 3/5/9/11 (benefic), 4/7/10 (malefic), 2/12
                            (neutral). 1/6/8 = no aspect. Used here.
    * Parashari Sphuta Drishti ("Planetary Aspect Evaluation" in JHora):
                            a DIFFERENT model (Mars 4/8, Jupiter 5/9,
                            Saturn 3/10 specials). Already in `drik_bala.py`.
                            NOT used here.
    * Ashtakavarga sodhya-pinda transit: unrelated. Already built.

RETROGRADE (ruled S169 -- best practice from the Tajika/horary literature):
    Applying vs separating is decided by ACTUAL SIGNED VELOCITY, not a
    faster/slower rule: the aspect is APPLYING if the degree-gap between the
    two planets is CLOSING, SEPARATING if OPENING. Each planet's real signed
    speed (direct > 0, retrograde < 0) is used, so faster-retro, slower-retro
    and both-retro all fall out of one computation -- there is no special case.
    This is the horary method Tajika inherits, and the Tajika Neelakanthi's
    "Khalasara" (false Ithasala -- a retrograde planet that looks applying but
    separates before exactitude) emerges from it automatically. Sources:
    Ernst Wilhelm Tajika Prashna; Tajika Neelakanthi (Khalasara); Gomes,
    Saptarishis. When signed speeds are NOT supplied, the engine falls back to
    a DIRECT-MOTION assumption (mean-speed order) and marks any retrograde-
    involved pair in `retro_provisional` so the caller knows that pair's
    direction is unverified until speeds are plumbed. Rahu/Ketu are excluded
    from Ithasala by doctrine (no deeptamsa).

    NOTE: a retrograde/combust planet ALSO spoils an otherwise-valid Ithasala
    into *Radda* (a weakened yoga) -- that is a separate QUALITY layer, listed
    in `deferred` (it needs combustion + dignity), not this direction layer.

NOT in scope here (recorded, not silently dropped):
    * radda, duhphali-kutta  -- need dignity + combustion + pancha-vargeeya
      bala; those engines exist in the project but wiring them is a separate
      step.
    * gairi-kamboola, khallasara -- unimplemented upstream in PyJHora itself
      (they `return None`); not ported rather than invented.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations

# --- planet identity, PyJHora-compatible ids (0=Sun .. 6=Saturn, 7/8=nodes) --
_NAME_TO_ID = {"Su": 0, "Mo": 1, "Ma": 2, "Me": 3, "Ju": 4, "Ve": 5,
               "Sa": 6, "Ra": 7, "Ke": 8}
_ID_TO_NAME = {v: k for k, v in _NAME_TO_ID.items()}
_CLASSICAL = (0, 1, 2, 3, 4, 5, 6)          # Sun..Saturn -- the only Ithasala players
_NODES = frozenset((7, 8))

# deeptamsa orb (degrees) per classical planet id -- PyJHora const.deeptaamsa_of_planets
_DEEPTAMSA = {0: 15.0, 1: 12.0, 2: 8.0, 3: 7.0, 4: 9.0, 5: 7.0, 6: 9.0}

# speed order slowest->fastest; a higher index == faster -- PyJHora const.order_of_planets_by_speed
_SPEED_ORDER = [6, 7, 8, 4, 2, 0, 5, 3, 1]

# Tajika sign-aspect valence by 0-indexed sign-offset (rasi2-rasi1)%12.
# benefic: trinal 5/9 (+4,+8) and sextile 3/11 (+2,+10);
# malefic: square 4/10 (+3,+9) and opposition 7 (+6);
# neutral: semi-sextile 2/12 (+1,+11). Offsets 0/5/7 (conj, 6th, 8th) = NO aspect.
_BENEFIC_OFFSETS = frozenset((2, 4, 8, 10))
_MALEFIC_OFFSETS = frozenset((3, 6, 9))
_NEUTRAL_OFFSETS = frozenset((1, 11))
_ASPECT_OFFSETS = _BENEFIC_OFFSETS | _MALEFIC_OFFSETS | _NEUTRAL_OFFSETS

_REQUIRED = ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "La")


@dataclass(frozen=True)
class AspectPair:
    """One classical planet pair's Tajika aspect state."""
    a: str                       # faster-id name is not implied; a<b by id
    b: str
    valence: str                 # benefic | malefic | neutral
    relation: str                # ithasala | ishrafa | none  (none = aspect, no deeptamsa)
    ithasala_type: str | None = None   # varthamaana | bhavishya | poorna (ithasala only)
    retro_provisional: bool = False    # a retrograde planet -> direction awaits ruling


@dataclass(frozen=True)
class TajakaAspects:
    pairs: tuple[AspectPair, ...]                 # every aspecting classical pair
    ithasala: tuple[AspectPair, ...]              # applying subset (the "promise")
    ishrafa: tuple[AspectPair, ...]               # separating subset (just past)
    nakta: tuple[tuple[str, str, str], ...] = ()  # (mediator, p1, p2)
    yamaya: tuple[tuple[str, str, str], ...] = ()
    manahoo: tuple[tuple[str, str, str], ...] = ()  # (p1, p2, mars_or_saturn)
    kamboola_pairs: tuple[tuple[str, str], ...] = ()  # Moon-involved ithasala pairs
    ishkavala: bool = False
    induvara: bool = False
    retro_provisional: tuple[tuple[str, str], ...] = ()
    deferred: tuple[str, ...] = ("radda", "duhphali_kutta",
                                 "gairi_kamboola", "khallasara")


# --------------------------------------------------------------------------- #
# geometry primitives (port of PyJHora tajaka.py), operating on within-rasi    #
# longitudes keyed by planet id                                                #
# --------------------------------------------------------------------------- #

def _sign(lon: float) -> int:
    return int(lon // 30) % 12


def _in_rasi(lon: float) -> float:
    return lon % 30.0


def _aspect(rasi: dict, p1: int, p2: int) -> str | None:
    """Tajika sign aspect valence between two planets, or None if no aspect.
    Symmetric: the offset set is closed under k->12-k, so order is irrelevant.
    """
    off = (rasi[p2] - rasi[p1]) % 12
    if off in _BENEFIC_OFFSETS:
        return "benefic"
    if off in _MALEFIC_OFFSETS:
        return "malefic"
    if off in _NEUTRAL_OFFSETS:
        return "neutral"
    return None


def _within_deeptamsa(inr: dict, p1: int, p2: int) -> tuple[bool, str | None]:
    """Both within each other's deeptamsa (PyJHora both_planets_within_their_deeptamsa).
    Returns (is_ithasala_geometry, type). Nodes excluded by doctrine.
    """
    if p1 in _NODES or p2 in _NODES:
        return False, None
    l1, l2 = inr[p1], inr[p2]
    d1, d2 = _DEEPTAMSA[p1], _DEEPTAMSA[p2]
    chk1 = (l2 - d2) <= l1 <= (l2 + d2)              # p1 inside p2's orb
    chk2 = (l1 - d1) <= l2 <= (l1 + d1)              # p2 inside p1's orb
    chk1_1 = (not chk1) and (abs(l1 - (l2 - d2)) <= 1.0 or abs(l1 - (l2 + d2)) <= 1.0)
    chk2_1 = (not chk2) and (abs(l2 - (l1 - d1)) <= 1.0 or abs(l2 - (l1 + d1)) <= 1.0)
    present = chk1 and chk2
    typ = "varthamaana" if present else None
    if not present and ((chk1 and chk2_1) or (chk2 and chk1_1)):
        present, typ = True, "bhavishya"
    if abs(l1 - l2) <= 1.0:                          # exact within a degree
        typ = "poorna"
        present = True
    return present, typ


def _approaching(inr: dict, p1: int, p2: int, speeds: dict | None) -> bool:
    """Applying iff the degree-gap is CLOSING. `advanced` = higher within-rasi
    degree, `behind` = lower. The gap (advanced - behind) shrinks iff the
    advanced planet's signed velocity is below the behind planet's.

    best practice (signed speeds): gap closes iff v[advanced] < v[behind] --
      handles direct, faster-retro, slower-retro and both-retro uniformly.
    fallback (speeds=None): assume direct motion -> faster planet is the one
      with the higher mean speed; applying iff the faster planet is behind.
    """
    advanced = p2 if inr[p1] < inr[p2] else p1
    behind = p1 if advanced == p2 else p2
    if speeds is not None:
        return speeds[advanced] < speeds[behind]
    faster = p2 if _SPEED_ORDER.index(p1) < _SPEED_ORDER.index(p2) else p1
    return faster == behind


# --------------------------------------------------------------------------- #
# public entry                                                                  #
# --------------------------------------------------------------------------- #

def compute_tajaka_aspects(pts: dict, speeds: dict | None = None,
                           retrograde: frozenset = frozenset()) -> TajakaAspects:
    """pts: annual sidereal longitudes (deg, 0-360) keyed
    'Su','Mo','Ma','Me','Ju','Ve','Sa','La' (+'Ra','Ke' optional, ignored for
    Ithasala).

    speeds: OPTIONAL signed sidereal speeds (deg/day, retrograde < 0) keyed by
      the same names. When given, applying/separating is computed from real
      motion (best practice -- see module docstring). When None, the engine
      assumes direct motion and flags retrograde-involved pairs as provisional.
    retrograde: planet names retrograde in the annual chart; used ONLY in the
      speeds=None fallback, to mark provisional pairs. Ignored when speeds given
      (the sign of the speed already carries it).
    """
    for k in _REQUIRED:
        if k not in pts:
            raise ValueError(f"compute_tajaka_aspects: missing annual longitude {k!r}")

    rasi = {pid: _sign(pts[nm]) for nm, pid in _NAME_TO_ID.items() if nm in pts}
    inr = {pid: _in_rasi(pts[nm]) for nm, pid in _NAME_TO_ID.items() if nm in pts}
    spd = None
    if speeds is not None:
        spd = {_NAME_TO_ID[n]: speeds[n] for n in _NAME_TO_ID if n in speeds}
    retro_ids = {_NAME_TO_ID[n] for n in retrograde if n in _NAME_TO_ID}

    pairs: list[AspectPair] = []
    ith: list[AspectPair] = []
    ish: list[AspectPair] = []
    retro_prov: list[tuple[str, str]] = []

    for p1, p2 in combinations(_CLASSICAL, 2):
        val = _aspect(rasi, p1, p2)
        if val is None:
            continue
        in_orb, typ = _within_deeptamsa(inr, p1, p2)
        n1, n2 = _ID_TO_NAME[p1], _ID_TO_NAME[p2]
        # a pair's direction is provisional only in the fallback (no speeds)
        # AND when a retrograde planet is involved; with real speeds it's computed.
        prov = (spd is None) and bool(retro_ids & {p1, p2})
        if in_orb:
            if _approaching(inr, p1, p2, spd):
                ap = AspectPair(n1, n2, val, "ithasala", typ, prov)
                ith.append(ap)
            else:
                ap = AspectPair(n1, n2, val, "ishrafa", typ, prov)
                ish.append(ap)
            if prov:
                retro_prov.append((n1, n2))
        else:
            ap = AspectPair(n1, n2, val, "none", None, prov)
        pairs.append(ap)

    ith_t, ish_t = tuple(ith), tuple(ish)
    ith_ids = [(_NAME_TO_ID[a.a], _NAME_TO_ID[a.b]) for a in ith_t]

    return TajakaAspects(
        pairs=tuple(pairs), ithasala=ith_t, ishrafa=ish_t,
        nakta=_triples(inr, rasi, ith_ids, want_mediator_low=True),
        yamaya=_triples(inr, rasi, ith_ids, want_mediator_low=False),
        manahoo=_manahoo(inr, rasi, ith_ids),
        kamboola_pairs=tuple((_ID_TO_NAME[x], _ID_TO_NAME[y])
                             for x, y in ith_ids if 1 in (x, y)),
        ishkavala=_house_occupation(rasi, _sign(pts["La"]), {0, 1, 3, 4, 6, 7, 9, 10}),
        induvara=_house_occupation(rasi, _sign(pts["La"]), {2, 5, 8, 11}),
        retro_provisional=tuple(retro_prov),
    )


# --------------------------------------------------------------------------- #
# companion yogas (built on the ithasala pairs)                                 #
# --------------------------------------------------------------------------- #

def _triples(inr: dict, rasi: dict, ith_ids, want_mediator_low: bool):
    """Nakta (mediator less advanced) / Yamaya (mediator more advanced): a
    mediator planet forms ithasala with p1 and p2 while p1,p2 do NOT aspect.
    """
    from collections import defaultdict
    by_first, by_second = defaultdict(list), defaultdict(list)
    for x, y in ith_ids:
        by_first[x].append(y)
        by_second[y].append(x)
    out = []
    for med, partners in list(by_first.items()) + list(by_second.items()):
        if len(partners) < 2:
            continue
        for p1, p2 in combinations(sorted(set(partners)), 2):
            if _aspect(rasi, p1, p2) is not None:        # p1,p2 must NOT aspect
                continue
            med_low = inr[med] < inr[p1] and inr[med] < inr[p2]
            med_high = inr[med] > inr[p1] and inr[med] > inr[p2]
            if (want_mediator_low and med_low) or (not want_mediator_low and med_high):
                out.append((_ID_TO_NAME[med], _ID_TO_NAME[p1], _ID_TO_NAME[p2]))
    return tuple(dict.fromkeys(out))                      # dedupe, keep order


def _manahoo(inr: dict, rasi: dict, ith_ids):
    """Manahoo: the faster planet of an ithasala pair has Mars or Saturn within
    its deeptamsa (PyJHora get_manahoo_yoga_planet_pairs)."""
    out = []
    for x, y in ith_ids:
        faster = y if inr[y] < inr[x] else x             # less-advanced == faster here
        fs, fe = inr[faster] - _DEEPTAMSA[faster], inr[faster] + _DEEPTAMSA[faster]
        for ms in (2, 6):                                # Mars, Saturn
            if ms in (x, y):
                continue
            if fs < inr[ms] < fe:
                out.append((_ID_TO_NAME[x], _ID_TO_NAME[y], _ID_TO_NAME[ms]))
    return tuple(dict.fromkeys(out))


def _house_occupation(rasi: dict, asc_sign: int, allowed_offsets: set) -> bool:
    """True if every classical planet sits only in houses at `allowed_offsets`
    (0-indexed) from the annual Lagna sign."""
    allowed_signs = {(asc_sign + o) % 12 for o in allowed_offsets}
    return all(rasi[p] in allowed_signs for p in _CLASSICAL if p in rasi)
