"""All yoga calculations -- one module.

Replaces catalog/raja_yogas.py, catalog/special.py and
catalog/neecha_bhanga.py, which were three files only because a Session 40
Claude Code prompt happened to name them that way in passing; the split was
never a design decision (verified against the original design-chat history,
S132). `catalog/pancha_mahapurusha.py` is deliberately NOT merged here -- it
takes degree-level placements and its own dataclasses, which this module's
fact-block-only contract cannot supply. See MERGE NOTE below.

CONTRACT. `detect(facts) -> list[dict]`, PURE over the already-computed fact
block: no ephemeris, no `chart_calculator` import, no chart fact computed
(S124 + S20 hold by construction). `detector.py` imports this; this imports
nothing from `detector`, so there is no cycle.

WHAT THIS MODULE SAYS, AND WHAT IT DOES NOT. It reports observed placements,
separations and dignities, and whether each condition held. It does NOT state
what any of it means, or which text defines it. That doctrine reaches the
reader from the corpus through the domain-tagged retrieval path, whole. A
sentence of doctrine written here would be a FRAGMENT standing in for a
chapter -- it reads as authoritative, so nothing goes back for the rest, and
the chapter's own conditions and qualifiers never arrive (S124; Sulabh's
ruling S132).

EVERY CHECK REPORTS A NOT-FIRED REASON. The negative row carries the chart
facts behind a "no", which a detector returning only hits throws away.

MERGE NOTE (S132). Merging the three modules removed two verbatim copies each
of `_ordinal` and `_house_lords`, and two duplicate `KENDRA_HOUSES`
definitions. Verified behaviour-identical against the real capture
`diagnostics/qa_capture/20260913T065603Z.md`: same 18 verdicts, same ids,
same fired flags, same evidence.

KNOWN GAP, NOT A DEFECT. The checks here are the six the S131 session needed
to reproduce one benchmark answer, plus Neecha Bhanga. JHora's Yogas tab for
this chart (reference/oracle_fixtures/sulabh.md 10c) lists SIXTEEN rows --
Vesi, Nipuna, Sunaphaa, Adhi, Daama, Kalpadruma, Yogada, Raja Sambandha and
others are NOT computed here. Absence of a yoga from this module's output
therefore means NOT IMPLEMENTED, never "you do not have it".

Python 3.11.
"""
from __future__ import annotations


def detect(facts: dict) -> list[dict]:
    """Every check in this module, fired or not."""
    return (_detect_raja(facts) + _detect_special(facts)
            + _detect_neecha(facts) + _detect_jhora_set(facts))



# ---- RAJA ----
KENDRA_HOUSES = (1, 4, 7, 10)
TRIKONA_HOUSES = (1, 5, 9)



def _house_lords(facts: dict) -> dict[int, dict]:
    """`house_lords` with integer keys. Tolerates the JSON string keys the
    capture round-trip produces."""
    raw = facts.get("house_lords") or {}
    out: dict[int, dict] = {}
    for k, v in raw.items():
        try:
            out[int(k)] = v
        except (TypeError, ValueError):
            continue
    return out


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    return f"{n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th') }"


def _aspects_between(facts: dict, a: str, b: str) -> bool:
    """True when `a` and `b` aspect each other, per the restated
    `aspected_by` map. One-way and mutual are not distinguished here."""
    ab = (facts.get("aspects") or {}).get("aspected_by") or {}
    return b in (ab.get(a) or []) or a in (ab.get(b) or [])


def _detect_raja(facts: dict) -> list[dict]:
    """Every check in this module, fired or not."""
    lords = _house_lords(facts)
    if not lords:
        return []

    out: list[dict] = []
    out.append(_dharma_karmadhipati(lords))
    out.extend(_kendra_trikona_links(facts, lords))
    return out


def _dharma_karmadhipati(lords: dict[int, dict]) -> dict:
    """Whether the 9th lord and the 10th lord occupy the same house."""
    n, t = lords.get(9), lords.get(10)
    if not (n and t):
        return {"id": "dharma_karmadhipati", "name": "Dharma-Karmadhipati Yoga",
                "fired": False, "reason": "the 9th or 10th lord is not known",
                "evidence": []}
    same = n.get("in_house") == t.get("in_house")
    if same:
        reason = (f"the 9th lord ({n['lord']}) and the 10th lord ({t['lord']}) "
                  f"both occupy the {_ordinal(int(n['in_house']))} house")
    else:
        reason = (f"the 9th lord ({n['lord']}) is in the "
                  f"{_ordinal(int(n['in_house']))} and the 10th lord "
                  f"({t['lord']}) is in the {_ordinal(int(t['in_house']))}; "
                  f"they do not occupy one house")
    return {
        "id": "dharma_karmadhipati",
        "name": "Dharma-Karmadhipati Yoga",
        "fired": bool(same),
        "reason": reason,
        "evidence": [f"house_lords.9.lord={n['lord']}",
                     f"house_lords.9.in_house={n.get('in_house')}",
                     f"house_lords.10.lord={t['lord']}",
                     f"house_lords.10.in_house={t.get('in_house')}"],
    }


def _kendra_trikona_links(facts: dict, lords: dict[int, dict]) -> list[dict]:
    """Lord of a house in KENDRA_HOUSES sharing a house with, or aspecting,
    the lord of a house in TRIKONA_HOUSES.

    One instance per (kendra house, trikona house) pair, so a chart with
    several links reports several, and a chart with none still reports every
    pair it checked.

    A planet ruling both houses is reported under a separate id, because it
    is one planet rather than a two-planet link.
    """
    out: list[dict] = []
    for k in KENDRA_HOUSES:
        for t in TRIKONA_HOUSES:
            # The 1st house appears in both tuples; the self-pair is
            # degenerate and is skipped.
            if k == t:
                continue
            kl, tl = lords.get(k), lords.get(t)
            if not (kl and tl):
                continue
            kp, tp = kl.get("lord"), tl.get("lord")
            rid = f"kendra_trikona_{k}_{t}"
            if kp == tp:
                out.append({
                    "id": rid, "name": f"Yogakaraka ({kp})", "fired": True,
                    "reason": (f"{kp} rules both the {_ordinal(k)} and the "
                               f"{_ordinal(t)}"),
                    "evidence": [f"house_lords.{k}.lord={kp}",
                                 f"house_lords.{t}.lord={tp}"]})
                continue

            conjunct = kl.get("in_house") == tl.get("in_house")
            aspected = _aspects_between(facts, kp, tp)
            # PVR p.146 names THREE associations: conjunction, graha drishti,
            # and parivartana (exchange) -- each lord sitting in the other's
            # house. S131 implemented only the first two. S132 adds the third.
            exchange = (kl.get("in_house") == t and tl.get("in_house") == k)
            fired = bool(conjunct or aspected or exchange)
            if conjunct:
                why = (f"the {_ordinal(k)} lord ({kp}) and the {_ordinal(t)} "
                       f"lord ({tp}) share the "
                       f"{_ordinal(int(kl['in_house']))} house")
            elif aspected:
                why = (f"the {_ordinal(k)} lord ({kp}) and the {_ordinal(t)} "
                       f"lord ({tp}) aspect each other")
            elif exchange:
                why = (f"the {_ordinal(k)} lord ({kp}) is in the {_ordinal(t)} "
                       f"and the {_ordinal(t)} lord ({tp}) is in the "
                       f"{_ordinal(k)} — they exchange houses")
            else:
                why = (f"the {_ordinal(k)} lord ({kp}) is in the "
                       f"{_ordinal(int(kl['in_house']))} and the "
                       f"{_ordinal(t)} lord ({tp}) is in the "
                       f"{_ordinal(int(tl['in_house']))}; they neither share a "
                       f"house nor aspect each other")
            out.append({
                "id": rid,
                "name": f"Raja Yoga ({_ordinal(k)}-{_ordinal(t)} lord link)",
                "fired": fired, "reason": why,
                "evidence": [f"house_lords.{k}.lord={kp}",
                             f"house_lords.{k}.in_house={kl.get('in_house')}",
                             f"house_lords.{t}.lord={tp}",
                             f"house_lords.{t}.in_house={tl.get('in_house')}"]})
    return out

# ---- SPECIAL ----
DUSTHANAS = (6, 8, 12)
KENDRA_FROM = (1, 4, 7, 10)


# label -> (owning house, the houses its lord must occupy to satisfy the check)
# PVR "Vedic Astrology: An Integrated Approach" p.145, verbatim definitions:
#   Harsha -- the 6th lord occupies the 6th house
#   Sarala -- the 8th lord occupies the 8th house
#   Vimala -- the 12th lord occupies the 12th house
# S131 coded these as the lord in one of the OTHER two dusthanas, citing
# Uttara Kalamrita. PVR is this project's primary spec source (CLAUDE.md
# Reference Materials) and says own house, so the spec source wins and the
# S131 reading is superseded. S132.
_VIPAREETA = {
    "Harsha Yoga": (6, (6,)),
    "Sarala Yoga": (8, (8,)),
    "Vimala Yoga": (12, (12,)),
}


def _tested_note(owner: int, targets: tuple[int, ...]) -> str:
    """States which houses this code tested -- a fact about the code, not a
    claim about any source. A wider reading of this check exists."""
    return (f"tested: the {_ordinal(owner)} lord in the "
            + " or the ".join(_ordinal(t) for t in targets)
            + f"; the {_ordinal(owner)} itself was not counted")



def _detect_special(facts: dict) -> list[dict]:
    out = _vipareeta(facts)
    gk = _gajakesari(facts)
    if gk:
        out.append(gk)
    return out


def _vipareeta(facts: dict) -> list[dict]:
    lords = _house_lords(facts)
    out: list[dict] = []
    for name, (owner, targets) in _VIPAREETA.items():
        row = lords.get(owner)
        rid = name.split()[0].lower() + "_yoga"
        if not row:
            out.append({"id": rid, "name": name, "fired": False,
                        "reason": f"the {_ordinal(owner)} lord is not known",
                        "evidence": [], "contested": True,
                        "contested_note": _tested_note(owner, targets)})
            continue
        where = row.get("in_house")
        fired = where in targets
        target_txt = " or the ".join(_ordinal(t) for t in targets)
        if fired:
            why = (f"the {_ordinal(owner)} lord ({row['lord']}) is in the "
                   f"{_ordinal(int(where))}")
        else:
            why = (f"the {_ordinal(owner)} lord ({row['lord']}) is in the "
                   f"{_ordinal(int(where))}, not the {target_txt}")
        out.append({
            "id": rid, "name": name, "fired": bool(fired), "reason": why,
            "evidence": [f"house_lords.{owner}.lord={row.get('lord')}",
                         f"house_lords.{owner}.in_house={where}"],
            "contested": True,
            "contested_note": _tested_note(owner, targets),
        })
    return out


def _gajakesari(facts: dict):
    """Moon-to-Jupiter separation, counted inclusively."""
    pos = facts.get("planet_positions") or {}
    moon, jup = pos.get("Moon"), pos.get("Jupiter")
    if not (isinstance(moon, dict) and isinstance(jup, dict)):
        return None
    try:
        mh, jh = int(moon["house"]), int(jup["house"])
    except (KeyError, TypeError, ValueError):
        return None

    # Counted inclusively from the Moon to Jupiter.
    sep = ((jh - mh) % 12) + 1
    fired = sep in KENDRA_FROM
    why = (f"Jupiter stands {_ordinal(sep)} from the Moon (Moon in the "
           f"{_ordinal(mh)}, Jupiter in the {_ordinal(jh)})")
    return {
        "id": "gajakesari_yoga", "name": "Gajakesari Yoga",
        "fired": bool(fired), "reason": why,
        "evidence": [f"planet_positions.Moon.house={mh}",
                     f"planet_positions.Jupiter.house={jh}"],
    }

# ---- NEECHA ----
_DEBILITATED = "Debilitated"
_EXALTED = "Exalted"


def _sign_to_lord(facts: dict) -> dict[str, str]:
    """sign -> ruling planet, inverted from `house_lords`.

    `house_lords` rows carry both `sign` and `lord`, so this is a lookup, not
    a calculation. Whole-sign houses mean each sign appears exactly once
    across the twelve rows; if that ever stops holding, a sign resolves to
    whichever row was read last and the caller reports it as unknown instead.
    """
    out: dict[str, str] = {}
    for row in (facts.get("house_lords") or {}).values():
        if not isinstance(row, dict):
            continue
        sign, lord = row.get("sign"), row.get("lord")
        if sign and lord:
            out[str(sign)] = str(lord)
    return out



def _house_of(pos: dict, graha: str):
    row = pos.get(graha)
    if not isinstance(row, dict):
        return None
    try:
        return int(row["house"])
    except (KeyError, TypeError, ValueError):
        return None


def _from_moon(house: int, moon_house: int) -> int:
    """Houses from the Moon to `house`, counted inclusively."""
    return ((house - moon_house) % 12) + 1


def _detect_neecha(facts: dict) -> list[dict]:
    """One verdict per debilitated planet, fired or not."""
    pos = facts.get("planet_positions") or {}
    if not isinstance(pos, dict):
        return []

    sign_lord = _sign_to_lord(facts)
    nav = ((facts.get("navamsa") or {}).get("placements") or {})
    moon_house = _house_of(pos, "Moon")

    out: list[dict] = []
    for graha, row in pos.items():
        if not isinstance(row, dict) or row.get("dignity") != _DEBILITATED:
            continue
        out.append(_verdict(graha, row, sign_lord, pos, nav, moon_house))
    return out


def _verdict(graha: str, row: dict, sign_lord: dict[str, str], pos: dict,
             nav: dict, moon_house) -> dict:
    sign = str(row.get("sign") or "")
    evidence = [f"planet_positions.{graha}.sign={sign}",
                f"planet_positions.{graha}.dignity={_DEBILITATED}"]

    dispositor = sign_lord.get(sign)
    # (machine label, held, observed fact in plain words)
    conditions: list[tuple[str, bool, str]] = []

    if not dispositor:
        conditions.append(("dispositor_known", False,
                           f"the ruler of {sign} could not be identified from "
                           f"this chart summary"))
    else:
        disp_row = pos.get(dispositor) if isinstance(pos.get(dispositor), dict) else {}
        disp_dignity = disp_row.get("dignity")
        disp_house = _house_of(pos, dispositor)
        evidence.append(f"planet_positions.{dispositor}.dignity={disp_dignity}")
        evidence.append(f"planet_positions.{dispositor}.house={disp_house}")

        exalted = disp_dignity == _EXALTED
        conditions.append(("dispositor_exalted", exalted,
                           f"its ruler {dispositor} is "
                           f"{'exalted' if exalted else 'not exalted'}"))

        if disp_house is None:
            conditions.append(("dispositor_house_1_4_7_10", False,
                               f"{dispositor}'s house is not known"))
            conditions.append(("dispositor_1_4_7_10_from_moon", False,
                               f"{dispositor}'s house is not known"))
        else:
            k_lagna = disp_house in KENDRA_HOUSES
            conditions.append(("dispositor_house_1_4_7_10", k_lagna,
                               f"{dispositor} is in the {_ordinal(disp_house)}"))
            if moon_house is None:
                conditions.append(("dispositor_1_4_7_10_from_moon", False,
                                   "the Moon's house is not known"))
            else:
                sep = _from_moon(disp_house, moon_house)
                conditions.append(("dispositor_1_4_7_10_from_moon",
                                   sep in KENDRA_HOUSES,
                                   f"{dispositor} is {_ordinal(sep)} from the Moon"))

    nav_row = nav.get(graha) if isinstance(nav.get(graha), dict) else None
    if nav_row is None:
        conditions.append(("exalted_in_navamsa", False,
                           "the navamsa is not available for this reading"))
    else:
        nav_dignity = nav_row.get("dignity")
        nav_sign = nav_row.get("sign")
        evidence.append(f"navamsa.placements.{graha}.sign={nav_sign}")
        evidence.append(f"navamsa.placements.{graha}.dignity={nav_dignity}")
        nav_ex = nav_dignity == _EXALTED
        conditions.append(("exalted_in_navamsa", nav_ex,
                           f"in the navamsa {graha} is in {nav_sign}, "
                           f"{'where it is exalted' if nav_ex else 'not exalted'}"))

    fired = any(held for _, held, _ in conditions)
    held_notes = [note for _, held, note in conditions if held]
    failed_notes = [note for _, held, note in conditions if not held]

    observed = "; ".join(held_notes if fired else failed_notes)
    reason = (f"{graha} is debilitated in {sign}. " +
              ("Conditions met: " if fired else "No condition met: ") +
              observed + ".")

    evidence.extend(f"condition:{label}={'held' if held else 'failed'}"
                    for label, held, _ in conditions)
    evidence.append("condition:exaltation_sign_lord=not-evaluable")

    return {
        "id": f"neecha_bhanga_{graha.lower()}",
        "name": f"Neecha Bhanga ({graha})",
        "fired": bool(fired),
        "reason": reason,
        "evidence": evidence,
    }


# ============================================================================
# S132 -- the remaining checks from the JHora Yogas-tab oracle
# (reference/oracle_fixtures/sulabh.md 10c). Each condition below implements
# that table's OWN "Brief definition of yoga" column verbatim; the definition
# text is the oracle's, not this module's, and is NOT restated here.
# ============================================================================

_SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
          "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
_SIGN_LORD = {"Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
              "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
              "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
              "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"}
_GRAHAS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
# Natural benefics. Mercury's benefic status is association-dependent and the
# Moon's is phase-dependent; both need data the chart summary does not carry,
# so the narrow, always-true set is used and the widening is NOT guessed.
_NATURAL_BENEFICS = ("Jupiter", "Venus")
_KONA = (1, 5, 9)
_QUALIFYING = frozenset({"Exalted", "Own Sign"})


def _pos(facts):
    p = facts.get("planet_positions")
    return p if isinstance(p, dict) else {}


def _sign_of(facts, graha):
    row = _pos(facts).get(graha)
    return row.get("sign") if isinstance(row, dict) else None


def _houses_from(facts, graha, offsets):
    """Signs sitting `offsets` houses from `graha`, counted inclusively."""
    s = _sign_of(facts, graha)
    if s not in _SIGNS:
        return {}
    i = _SIGNS.index(s)
    return {o: _SIGNS[(i + o - 1) % 12] for o in offsets}


def _occupants(facts, sign, exclude=()):
    return [g for g in _GRAHAS
            if g not in exclude and _sign_of(facts, g) == sign]


def _rasi_aspects(a, b):
    """Jaimini rasi drishti, by sign position only.

    Signs come in three modes repeating every three: movable, fixed, dual.
    A movable sign aspects the fixed signs 4, 7 and 10 away; a fixed sign
    aspects the movable signs 2, 5 and 8 away; a dual sign aspects the other
    dual signs, which sit 3, 6 and 9 away. The adjacent sign is excluded by
    those offsets, so no separate exclusion is needed.
    """
    if a not in _SIGNS or b not in _SIGNS or a == b:
        return False
    ia, ib = _SIGNS.index(a), _SIGNS.index(b)
    gap = (ib - ia) % 12
    mode = ia % 3
    if mode == 0:
        return gap in (4, 7, 10) and ib % 3 == 1
    if mode == 1:
        return gap in (2, 5, 8) and ib % 3 == 0
    return gap in (3, 6, 9) and ib % 3 == 2


def _row(rid, name, fired, reason, evidence):
    return {"id": rid, "name": name, "fired": bool(fired),
            "reason": reason, "evidence": list(evidence)}


def _detect_jhora_set(facts: dict) -> list[dict]:
    out = []
    out.append(_vesi(facts))
    out.append(_nipuna(facts))
    out.append(_sunaphaa(facts))
    out.append(_adhi(facts))
    out.append(_daama(facts))
    out.append(_kalpadruma(facts))
    out.append(_vry_conjunct_or_samasaptaka(facts))
    out.extend(_karaka_rules(facts))
    out.extend(_yogada(facts))
    return [v for v in out if v]


def _vesi(facts):
    tgt = _houses_from(facts, "Sun", (2,)).get(2)
    occ = _occupants(facts, tgt, exclude=("Moon", "Sun")) if tgt else []
    return _row("vesi", "Vesi", bool(occ),
                    (f"{', '.join(occ)} in {tgt}, the 2nd from the Sun" if occ
                     else f"nothing but possibly the Moon in {tgt}, the 2nd from the Sun"),
                    [f"2nd_from_Sun={tgt}", f"occupants={occ}"])


def _nipuna(facts):
    ss, sm = _sign_of(facts, "Sun"), _sign_of(facts, "Mercury")
    if not (ss and sm):
        return _row("nipuna", "Nipuna (Budha-Aditya)", False,
                        "the Sun's or Mercury's sign is not known", [])
    # PVR p.126: "If Sun and Mercury are together (in one sign)". Opposition
    # ("mutual 7ths") appears in JHora's own screen text but NOT in the spec
    # source, so it is not implemented. Divergence recorded, not silently taken.
    gap = (_SIGNS.index(sm) - _SIGNS.index(ss)) % 12
    fired = gap == 0
    return _row("nipuna", "Nipuna (Budha-Aditya)", fired,
                    (f"Sun and Mercury are both in {ss}" if gap == 0
                     else f"Sun is in {ss} and Mercury in {sm}"),
                    [f"Sun.sign={ss}", f"Mercury.sign={sm}"])


def _sunaphaa(facts):
    tgt = _houses_from(facts, "Moon", (2,)).get(2)
    occ = _occupants(facts, tgt, exclude=("Sun", "Moon")) if tgt else []
    return _row("sunaphaa", "Sunaphaa", bool(occ),
                    (f"{', '.join(occ)} in {tgt}, the 2nd from the Moon" if occ
                     else f"nothing but possibly the Sun in {tgt}, the 2nd from the Moon"),
                    [f"2nd_from_Moon={tgt}", f"occupants={occ}"])


def _adhi(facts):
    """Natural benefics in the 6th, 7th or 8th from the Moon.

    AMBIGUITY IN THE SPEC SOURCE, RESOLVED BY THE ORACLE -- do not re-litigate.
    PVR p.128 reads "the natural benefics occupy 6th, 7th and 8th from Moon",
    which can be read as requiring ALL THREE houses occupied. Its own worked
    example contradicts that: it places the benefics in the 5th and 4th from
    the Moon. So PVR alone cannot settle it.

    The oracle does. On Sulabh's chart the 8th from the Moon (Gemini) is EMPTY,
    the 6th and 7th hold Jupiter and Venus -- and JHora fires Adhi listing
    exactly "Ju, Ve" (reference/oracle_fixtures/sulabh.md 10c). A strict
    all-three reading would report nothing there. So the loose reading is the
    one JHora implements, it is adopted here, and the giver set matches the
    oracle planet-for-planet, not merely fired/not-fired. S132.
    """
    tgts = _houses_from(facts, "Moon", (6, 7, 8))
    found = []
    for off, sign in sorted(tgts.items()):
        for g in _occupants(facts, sign):
            if g in _NATURAL_BENEFICS:
                found.append(f"{g} in {sign} ({off}th from the Moon)")
    return _row("adhi", "Adhi", bool(found),
                    ("; ".join(found) if found else
                     "no natural benefic in the 6th, 7th or 8th from the Moon"),
                    [f"{o}th_from_Moon={s}" for o, s in sorted(tgts.items())])


def _daama(facts):
    occupied = {_sign_of(facts, g) for g in _GRAHAS if _sign_of(facts, g)}
    n = len(occupied)
    return _row("daama_daamini", "Daama/Daamini", n == 6,
                    f"the seven grahas occupy {n} signs ({', '.join(sorted(occupied))})",
                    [f"distinct_signs={n}"])


def _kalpadruma(facts):
    """Lagna lord, his dispositor, and that planet's rasi and navamsa
    dispositors -- all four in own/exaltation sign or in a kendra/kona."""
    lag = facts.get("ascendant_sign")
    if lag not in _SIGNS:
        return _row("kalpadruma", "Kalpadruma/Parijata", False,
                        "the ascendant sign is not known", [])
    chain, ev = [], []
    p1 = _SIGN_LORD[lag]
    s1 = _sign_of(facts, p1)
    p2 = _SIGN_LORD.get(s1) if s1 else None
    s2 = _sign_of(facts, p2) if p2 else None
    p3 = _SIGN_LORD.get(s2) if s2 else None
    nav = ((facts.get("navamsa") or {}).get("placements") or {}).get(p2) or {}
    p4 = _SIGN_LORD.get(nav.get("sign")) if nav.get("sign") else None
    for label, g in (("lagna lord", p1), ("its dispositor", p2),
                     ("that planet's sign lord", p3),
                     ("its navamsa sign lord", p4)):
        if not g:
            return _row("kalpadruma", "Kalpadruma/Parijata", False,
                            f"the chain breaks at {label}", ev)
        row = _pos(facts).get(g) or {}
        # PVR p.140: "all the four planets are all in quadrants, trines or
        # exaltation signs". Own sign is NOT in the spec source -- not added.
        ok = (row.get("dignity") == "Exalted"
              or row.get("house") in (1, 4, 7, 10) + _KONA)
        chain.append((label, g, ok, row.get("dignity"), row.get("house")))
        ev.append(f"{label}={g}(house={row.get('house')},dignity={row.get('dignity')})")
    fired = all(c[2] for c in chain)
    txt = "; ".join(f"{g} in the {h}" + (f", {d.lower()}" if d else "")
                    for _, g, _, d, h in chain)
    return _row("kalpadruma", "Kalpadruma/Parijata", fired,
                    (txt if fired else "the chain is not all well placed: " + txt), ev)


def _vry_conjunct_or_samasaptaka(facts):
    lords = _house_lords(facts)
    six, eight = lords.get(6), lords.get(8)
    if not (six and eight):
        return _row("vipareeta_6_8_link", "Vipareeta (6th-8th lord link)",
                        False, "the 6th or 8th lord is not known", [])
    s6, s8 = _sign_of(facts, six["lord"]), _sign_of(facts, eight["lord"])
    if not (s6 and s8):
        return _row("vipareeta_6_8_link", "Vipareeta (6th-8th lord link)",
                        False, "a lord's sign is not known", [])
    gap = (_SIGNS.index(s8) - _SIGNS.index(s6)) % 12
    fired = gap in (0, 6)
    return _row("vipareeta_6_8_link", "Vipareeta (6th-8th lord link)", fired,
                    (f"the 6th lord ({six['lord']}, {s6}) and the 8th lord "
                     f"({eight['lord']}, {s8}) are "
                     + ("in one sign" if gap == 0 else
                        "opposite each other" if gap == 6 else
                        f"{gap} signs apart")),
                    [f"lord6={six['lord']}@{s6}", f"lord8={eight['lord']}@{s8}"])


def _karaka_rules(facts):
    k = facts.get("chara_karakas")
    if not isinstance(k, dict) or not k:
        return [_row("raja_ak_pik", "Raja (AK-PiK)", False,
                         "the chara karakas are not available for this reading", []),
                _row("raja_sambandha", "Raja Sambandha", False,
                         "the chara karakas are not available for this reading", [])]
    out = []
    ak, pik, amk = k.get("AK"), k.get("PiK"), k.get("AmK")
    if ak and pik:
        sa, sp = _sign_of(facts, ak), _sign_of(facts, pik)
        ha = (_pos(facts).get(ak) or {}).get("house")
        hp = (_pos(facts).get(pik) or {}).get("house")
        together = sa is not None and sa == sp
        in_1_5 = ha in (1, 5) and hp in (1, 5)
        out.append(_row("raja_ak_pik", "Raja (AK-PiK)", together or in_1_5,
                            (f"the atma karaka ({ak}) and putri karaka ({pik}) are both in {sa}"
                             if together else
                             f"the atma karaka ({ak}, house {ha}) and putri karaka "
                             f"({pik}, house {hp}) are neither together nor both in the 1st or 5th"),
                            [f"AK={ak}@{sa}", f"PiK={pik}@{sp}"]))
    if amk:
        h = (_pos(facts).get(amk) or {}).get("house")
        out.append(_row("raja_sambandha", "Raja Sambandha", h in _KONA,
                            f"the amatya karaka ({amk}) is in the {_ordinal(int(h))}"
                            if h else f"the amatya karaka ({amk})'s house is not known",
                            [f"AmK={amk}", f"AmK.house={h}"]))
    return out


def _yogada(facts):
    """One row per graha associated with BOTH the lagna sign and the Ghati
    Lagna sign -- by occupying it, owning it, or rasi-aspecting it."""
    lag, gl = facts.get("ascendant_sign"), facts.get("ghati_lagna_sign")
    if lag not in _SIGNS or gl not in _SIGNS:
        return [_row("yogada_gl", "Yogada (GL)", False,
                         "the Ghati Lagna is not available for this reading", [])]
    out = []
    for g in _GRAHAS:
        s = _sign_of(facts, g)
        if not s:
            continue
        def linked(target):
            if s == target:
                return "occupies"
            if _SIGN_LORD[target] == g:
                return "owns"
            if _rasi_aspects(s, target):
                return "aspects"
            return None
        a, b = linked(lag), linked(gl)
        if a and b:
            out.append(_row(f"yogada_gl_{g.lower()}", f"Yogada GL ({g})", True,
                                f"{g} {a} the rising sign ({lag}) and {b} the "
                                f"Ghati Lagna sign ({gl})",
                                [f"{g}.sign={s}", f"lagna={lag}", f"ghati_lagna={gl}"]))
    if not out:
        out.append(_row("yogada_gl", "Yogada (GL)", False,
                            f"no graha is linked to both the rising sign ({lag}) "
                            f"and the Ghati Lagna sign ({gl})",
                            [f"lagna={lag}", f"ghati_lagna={gl}"]))
    return out
