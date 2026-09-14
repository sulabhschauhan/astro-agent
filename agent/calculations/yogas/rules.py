"""All yoga calculations -- one module.

Replaces catalog/raja_yogas.py, catalog/special.py and
catalog/neecha_bhanga.py, which were three files only because a Session 40
Claude Code prompt happened to name them that way in passing; the split was
never a design decision (verified against the original design-chat history,
S132). `catalog/pancha_mahapurusha.py` is deliberately NOT wired -- it takes
degree_in_sign, which the fact block omits by lock (S129b/S130: no longitude).
The Pancha Mahapurusha check here works from the fact block's own dignity
label instead (Exalted / Own Sign), so a moolatrikona-only placement is
unreachable, the same accepted class as degree-keyed Neecha Bhanga (S130).
See MERGE NOTE below.

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

COVERAGE (S133). The checks here reproduce every JHora Yogas-tab row printed
for the two reference charts (sulabh.md 10c, surbhi.md 10c): the kendra-trikona
and Dharma-Karmadhipati raja links, the three Vipareeta own-house yogas, the
three Vipareeta dusthana-lord links (6-8, 6-12, 8-12), Gajakesari, Vesi,
Nipuna, Sunaphaa, Anaphaa, Adhi, the seven Naabhasa sankhya yogas
(Gola..Veenaa by occupied-sign count), Kalpadruma, Yogada (GL and HL) and
Maha Yogada, the AK-PiK and AK-AmK raja links, Neecha Bhanga per debilitated
planet, and the five Pancha Mahapurusha yogas. A yoga JHora prints that is
not one of these is NOT IMPLEMENTED, not "you do not have it"; the wider BPHS
set beyond the oracle rows stays out until these are validated (Sulabh, S132).

Python 3.11.
"""
from __future__ import annotations

# Pure table lookup (no ephemeris, no chart_calculator): resolves Exalted /
# Debilitated / Moolatrikona / Own from sign + degree_in_sign. Used only for
# the degree-accurate Pancha Mahapurusha check (S133); everything else stays
# on the fact block's own dignity label.
from agent.calculations.core.dignity import get_dignity_status


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
    out.append(_dharma_karmadhipati(facts, lords))
    out.extend(_kendra_trikona_links(facts, lords))
    return out


def _dharma_karmadhipati(facts: dict, lords: dict[int, dict]) -> dict:
    """The 9th and 10th lords in conjunction, mutual aspect, or exchange.
    (Oracle def: "conjunction, aspect or exchange of 9th/10th lords".)"""
    n, t = lords.get(9), lords.get(10)
    if not (n and t):
        return {"id": "dharma_karmadhipati", "name": "Dharma-Karmadhipati Yoga",
                "fired": False, "reason": "the 9th or 10th lord is not known",
                "evidence": []}
    nh, th = n.get("in_house"), t.get("in_house")
    conjunct = nh == th
    aspected = _aspects_between(facts, n["lord"], t["lord"])
    exchange = (nh == 10 and th == 9)
    fired = bool(conjunct or aspected or exchange)
    if conjunct:
        why = (f"the 9th lord ({n['lord']}) and the 10th lord ({t['lord']}) "
               f"both occupy the {_ordinal(int(nh))} house")
    elif exchange:
        why = (f"the 9th lord ({n['lord']}) is in the 10th and the 10th lord "
               f"({t['lord']}) is in the 9th -- they exchange houses")
    elif aspected:
        why = (f"the 9th lord ({n['lord']}) and the 10th lord ({t['lord']}) "
               f"aspect each other")
    else:
        why = (f"the 9th lord ({n['lord']}) is in the {_ordinal(int(nh))} and "
               f"the 10th lord ({t['lord']}) is in the {_ordinal(int(th))}; they "
               f"neither share a house, aspect each other, nor exchange")
    return {
        "id": "dharma_karmadhipati",
        "name": "Dharma-Karmadhipati Yoga",
        "fired": fired,
        "reason": why,
        "evidence": [f"house_lords.9.lord={n['lord']}",
                     f"house_lords.9.in_house={nh}",
                     f"house_lords.10.lord={t['lord']}",
                     f"house_lords.10.in_house={th}"],
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
                # A yogakaraka owns a quadrant AND a trine (PVR p.177). The 1st
                # is both a quadrant and a trine, so owning the 1st plus another
                # angle does NOT make a yogakaraka -- the quadrant must be one of
                # 4/7/10 and the trine one of 5/9. (Jupiter owning 1+4 for a
                # Sagittarius lagna is not a yogakaraka; Saturn owning 4+5 for a
                # Libra lagna is.) One planet, so there is no two-lord link to
                # report either way -- skip after the check.
                if k in (4, 7, 10) and t in (5, 9):
                    out.append({
                        "id": rid, "name": f"Yogakaraka ({kp})", "fired": True,
                        "reason": (f"{kp} rules both the {_ordinal(k)} (a "
                                   f"quadrant) and the {_ordinal(t)} (a trine)"),
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
                        "evidence": []})
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
# Sign of exaltation per graha -- fixed PVR Table 6 constant, the same class of
# lookup as _SIGN_LORD (a computation input, not doctrine prose). S133.
_EXALTATION_SIGN = {"Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn",
                    "Mercury": "Virgo", "Jupiter": "Cancer", "Venus": "Pisces",
                    "Saturn": "Libra"}


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

    # The lord of the sign where `graha` would be EXALTED, in a kendra from
    # lagna or from the Moon. Completes the classical cancellation set that
    # S131/S132 left as "not-evaluable". S133.
    exalt_sign = _EXALTATION_SIGN.get(graha)
    exalt_lord = sign_lord.get(exalt_sign) if exalt_sign else None
    if not exalt_lord:
        conditions.append(("exaltation_sign_lord_kendra", False,
                           f"the ruler of {graha}'s exaltation sign could not "
                           f"be identified from this chart summary"))
    else:
        el_house = _house_of(pos, exalt_lord)
        evidence.append(f"planet_positions.{exalt_lord}.house={el_house}")
        if el_house is None:
            conditions.append(("exaltation_sign_lord_kendra", False,
                               f"{exalt_lord}'s house is not known"))
        else:
            from_lagna = el_house in KENDRA_HOUSES
            from_moon = (moon_house is not None
                         and _from_moon(el_house, moon_house) in KENDRA_HOUSES)
            conditions.append((
                "exaltation_sign_lord_kendra", from_lagna or from_moon,
                f"{exalt_lord} (ruler of {graha}'s exaltation sign {exalt_sign}) "
                f"is in the {_ordinal(el_house)}"
                + ("" if (from_lagna or from_moon)
                   else ", not a kendra from lagna or the Moon")))

    fired = any(held for _, held, _ in conditions)
    held_notes = [note for _, held, note in conditions if held]
    failed_notes = [note for _, held, note in conditions if not held]

    observed = "; ".join(held_notes if fired else failed_notes)
    reason = (f"{graha} is debilitated in {sign}. " +
              ("Conditions met: " if fired else "No condition met: ") +
              observed + ".")

    evidence.extend(f"condition:{label}={'held' if held else 'failed'}"
                    for label, held, _ in conditions)

    return {
        "id": f"neecha_bhanga_{graha.lower()}",
        "name": f"Neecha Bhanga ({graha})",
        "fired": bool(fired),
        "reason": reason,
        "evidence": evidence,
    }


# ============================================================================
# The yogas JHora's Yogas tab prints for the reference charts. Each FORMULA
# below comes from the classical spec source (PVR / BPHS), cited in the
# function that uses it; JHora's tab only GRADES the answer -- it is never the
# source of a formula (P-028). Where PVR and JHora's on-screen definition text
# differ, PVR wins and the divergence is recorded at the function. S132/S133.
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
_NATURAL_MALEFICS = ("Sun", "Mars", "Saturn", "Rahu", "Ketu")
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


def _is_benefic(facts, graha):
    """Natural benefic status, as far as the fact block allows.

    Jupiter and Venus are unconditional benefics; Sun, Mars, Saturn, Rahu and
    Ketu are natural malefics. Mercury takes its company's character: benefic
    unless EVERY body ASSOCIATED with it -- sharing its house OR aspecting it --
    is a natural malefic (no association at all counts as benefic). The Moon is
    paksha-dependent and the fact block carries no phase, so it is treated as
    benefic -- an approximation, but the Moon is never its own reference planet
    in the yogas that call this, so it reaches no result.
    """
    if graha in _NATURAL_BENEFICS:
        return True
    if graha in _NATURAL_MALEFICS:
        return False
    if graha == "Moon":
        return True
    # Mercury: judged by its whole company -- same-house occupants and the
    # planets aspecting it (conjunction + graha drishti), across every body in
    # the block.
    pos = _pos(facts)
    row = pos.get(graha)
    house = row.get("house") if isinstance(row, dict) else None
    company = set()
    if house is not None:
        company.update(g for g, r in pos.items()
                       if g != graha and isinstance(r, dict)
                       and r.get("house") == house)
    aspected_by = (facts.get("aspects") or {}).get("aspected_by") or {}
    company.update(g for g in (aspected_by.get(graha) or []) if g != graha)
    if not company:
        return True
    return not all(c in _NATURAL_MALEFICS for c in company)


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
    out.append(_anaphaa(facts))
    out.append(_adhi(facts))
    out.append(_naabhasa_sankhya(facts))
    out.append(_kalpadruma(facts))
    out.extend(_vry_dusthana_pairs(facts))
    out.extend(_karaka_rules(facts))
    out.extend(_yogada(facts))
    out.extend(_pancha_mahapurusha(facts))
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


def _anaphaa(facts):
    """Any planet other than the Sun in the 12th from the Moon (the mirror of
    Sunaphaa's 2nd-from-Moon; Durudhara is both occupied)."""
    tgt = _houses_from(facts, "Moon", (12,)).get(12)
    occ = _occupants(facts, tgt, exclude=("Sun", "Moon")) if tgt else []
    return _row("anaphaa", "Anaphaa", bool(occ),
                    (f"{', '.join(occ)} in {tgt}, the 12th from the Moon" if occ
                     else f"nothing but possibly the Sun in {tgt}, the 12th from the Moon"),
                    [f"12th_from_Moon={tgt}", f"occupants={occ}"])


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
            if _is_benefic(facts, g):
                found.append(f"{g} in {sign} ({off}th from the Moon)")
    return _row("adhi", "Adhi", bool(found),
                    ("; ".join(found) if found else
                     "no natural benefic in the 6th, 7th or 8th from the Moon"),
                    [f"{o}th_from_Moon={s}" for o, s in sorted(tgts.items())])


# Naabhasa sankhya (numerical) family: the count of distinct signs the seven
# grahas occupy, 1..7, names exactly one yoga. Classical spec (BPHS Ch.35).
_NAABHASA_SANKHYA = {1: "Gola", 2: "Yuga", 3: "Sula", 4: "Kedara",
                     5: "Paasa", 6: "Daama", 7: "Veenaa"}


def _naabhasa_sankhya(facts):
    """The seven grahas occupy N distinct signs; the count names the yoga
    (Gola..Veenaa). One lookup -- exactly one count applies, so the row fires
    once the seven signs are known."""
    occupied = sorted({_sign_of(facts, g) for g in _GRAHAS if _sign_of(facts, g)})
    n = len(occupied)
    name = _NAABHASA_SANKHYA.get(n)
    if not name:
        return _row("naabhasa_sankhya", "Naabhasa sankhya", False,
                        "the seven grahas' signs are not fully known", [])
    return _row(f"naabhasa_{name.lower()}", name, True,
                    f"the seven grahas occupy {n} sign(s) ({', '.join(occupied)})",
                    [f"distinct_signs={n}", f"signs={occupied}"])


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


def _vry_dusthana_pairs(facts):
    """Vipareeta Raja Yoga by association: any two of the three dusthana lords
    (6th, 8th, 12th) in conjunction (one sign) or samasaptaka (mutual 7ths).
    One row per pair. JHora prints whichever pair actually associates -- Sulabh
    6-8, Surbhi 6-12 -- so all three pairs are checked, not only 6-8."""
    lords = _house_lords(facts)
    out = []
    for a, b in ((6, 8), (6, 12), (8, 12)):
        rid = f"vipareeta_{a}_{b}_link"
        name = f"Vipareeta ({_ordinal(a)}-{_ordinal(b)} lord link)"
        la, lb = lords.get(a), lords.get(b)
        if not (la and lb):
            out.append(_row(rid, name, False,
                            f"the {_ordinal(a)} or {_ordinal(b)} lord is not known", []))
            continue
        pa, pb = la["lord"], lb["lord"]
        if pa == pb:
            out.append(_row(rid, name, False,
                            f"one planet ({pa}) lords both the {_ordinal(a)} and "
                            f"the {_ordinal(b)}; there is no two-lord association",
                            [f"lord{a}={pa}", f"lord{b}={pb}"]))
            continue
        sa, sb = _sign_of(facts, pa), _sign_of(facts, pb)
        if not (sa and sb):
            out.append(_row(rid, name, False, "a lord's sign is not known", []))
            continue
        gap = (_SIGNS.index(sb) - _SIGNS.index(sa)) % 12
        fired = gap in (0, 6)
        out.append(_row(rid, name, fired,
                        (f"the {_ordinal(a)} lord ({pa}, {sa}) and the "
                         f"{_ordinal(b)} lord ({pb}, {sb}) are "
                         + ("in one sign" if gap == 0 else
                            "opposite each other (samasaptaka)" if gap == 6 else
                            f"{gap} signs apart, neither conjunct nor samasaptaka")),
                        [f"lord{a}={pa}@{sa}", f"lord{b}={pb}@{sb}"]))
    return out


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
    # Raja Sambandha is a FAMILY (PVR p.140 sec 11.8); JHora prints whichever
    # sub-combination fires, with that combination's own result text. The two
    # reference charts exercise two of them, so both are computed as their own
    # rows (each fired or not):
    #   (5) AmK in a TRINE from lagna  -> "a famous minister"      (Sulabh: Ju in 5th)
    #   (6) AmK in a QUADRANT or TRINE from AK -> "associate liked by a king" (Surbhi: Rahu 5th from AK)
    # PVR p.140-141 verbatim; NOT the oracle's brief-definition text (P-028).
    # The other 13 combinations in 11.8 are the wider set and stay out until
    # these are validated (Sulabh, S132).
    out.append(_raja_sambandha_lagna(facts, amk))
    out.append(_raja_sambandha_from_ak(facts, ak, amk))
    return out


def _raja_sambandha_lagna(facts, amk):
    """PVR 11.8 (5): amatya karaka in a trine (1/5/9) from lagna."""
    if not amk:
        return _row("raja_sambandha_lagna", "Raja Sambandha (AmK in a trine)",
                        False, "the amatya karaka is not available", [])
    h = (_pos(facts).get(amk) or {}).get("house")
    if h is None:
        return _row("raja_sambandha_lagna", "Raja Sambandha (AmK in a trine)",
                        False, f"the amatya karaka ({amk})'s house is not known",
                        [f"AmK={amk}"])
    fired = h in _KONA
    return _row("raja_sambandha_lagna", "Raja Sambandha (AmK in a trine)", fired,
                    (f"the amatya karaka ({amk}) is in the {_ordinal(int(h))}"
                     + ("" if fired else ", not a trine (1st/5th/9th) from lagna")),
                    [f"AmK={amk}", f"AmK.house={h}"])


def _raja_sambandha_from_ak(facts, ak, amk):
    """PVR 11.8 (6): amatya karaka in a quadrant or trine FROM the atma karaka."""
    if not (ak and amk):
        return _row("raja_sambandha_ak", "Raja Sambandha (AmK from AK)", False,
                        "the atma or amatya karaka is not available", [])
    sa, sm = _sign_of(facts, ak), _sign_of(facts, amk)
    if not (sa and sm):
        return _row("raja_sambandha_ak", "Raja Sambandha (AmK from AK)", False,
                        "the atma or amatya karaka's sign is not known",
                        [f"AK={ak}", f"AmK={amk}"])
    frm = ((_SIGNS.index(sm) - _SIGNS.index(sa)) % 12) + 1
    fired = frm in (1, 4, 5, 7, 9, 10)  # quadrant or trine from AK
    return _row("raja_sambandha_ak", "Raja Sambandha (AmK from AK)", fired,
                    (f"the amatya karaka ({amk}, {sm}) is the {_ordinal(frm)} "
                     f"from the atma karaka ({ak}, {sa})"
                     + ("" if fired else ", not a quadrant or trine from it")),
                    [f"AK={ak}@{sa}", f"AmK={amk}@{sm}", f"AmK_from_AK={frm}"])


def _yogada_link(facts, g, s, target):
    """How graha `g` (in sign `s`) is associated with `target` sign: it
    occupies it, owns it, or rasi-aspects it. None when unlinked."""
    if s == target:
        return "occupies"
    if _SIGN_LORD[target] == g:
        return "owns"
    if _rasi_aspects(s, target):
        return "aspects"
    return None


def _yogada(facts):
    """Yogada and Maha Yogada (PVR p.179). A graha ASSOCIATED -- occupies, owns
    or rasi-aspects -- with the lagna and a time-lagna is a Yogada of that
    time-lagna; associated with the lagna, the Ghati Lagna AND the Hora Lagna
    at once is a Maha Yogada. One row per qualifying graha; a summary not-fired
    row when none qualifies and the inputs were present."""
    lag = facts.get("ascendant_sign")
    gl = facts.get("ghati_lagna_sign")
    hl = facts.get("hora_lagna_sign")
    if lag not in _SIGNS:
        return [_row("yogada", "Yogada", False,
                         "the ascendant sign is not known", [])]
    have_gl, have_hl = gl in _SIGNS, hl in _SIGNS
    if not (have_gl or have_hl):
        return [_row("yogada", "Yogada", False,
                         "neither the Ghati Lagna nor the Hora Lagna is "
                         "available for this reading", [])]

    out = []
    for g in _GRAHAS:
        s = _sign_of(facts, g)
        if not s:
            continue
        to_lag = _yogada_link(facts, g, s, lag)
        if not to_lag:
            continue
        to_gl = _yogada_link(facts, g, s, gl) if have_gl else None
        to_hl = _yogada_link(facts, g, s, hl) if have_hl else None
        ev = [f"{g}.sign={s}", f"lagna={lag}"]
        if have_gl:
            ev.append(f"ghati_lagna={gl}")
        if have_hl:
            ev.append(f"hora_lagna={hl}")
        if to_gl and to_hl:
            out.append(_row(f"maha_yogada_{g.lower()}", f"Maha Yogada ({g})", True,
                            f"{g} {to_lag} the rising sign ({lag}), {to_gl} the "
                            f"Ghati Lagna ({gl}) and {to_hl} the Hora Lagna ({hl})",
                            ev))
        elif to_gl:
            out.append(_row(f"yogada_gl_{g.lower()}", f"Yogada GL ({g})", True,
                            f"{g} {to_lag} the rising sign ({lag}) and {to_gl} the "
                            f"Ghati Lagna ({gl})", ev))
        elif to_hl:
            out.append(_row(f"yogada_hl_{g.lower()}", f"Yogada HL ({g})", True,
                            f"{g} {to_lag} the rising sign ({lag}) and {to_hl} the "
                            f"Hora Lagna ({hl})", ev))
    if not out:
        out.append(_row("yogada", "Yogada", False,
                        f"no graha is linked to the rising sign ({lag}) and a "
                        f"time-lagna", [f"lagna={lag}"]))
    return out


# Pancha Mahapurusha: the five non-luminary grahas, each named for its yoga.
_PMP_NAMES = {"Mars": "Ruchaka", "Mercury": "Bhadra", "Jupiter": "Hamsa",
              "Venus": "Malavya", "Saturn": "Sasa"}
# Own house/moolatrikona/exaltation all qualify (BPHS Ch.75). Own house here
# means the planet's OWN SIGN; moolatrikona is a degree range inside it.
_QUALIFYING_PMP = frozenset({"Exalted", "Moolatrikona", "Own"})


def _pmp_qualifies(facts, g, sign):
    """(qualifies, dignity-label) for a Pancha Mahapurusha planet.

    DEGREE-ACCURATE when the detector's fact block carries `planet_degrees`
    (degree_in_sign per graha): get_dignity_status resolves Moolatrikona, so a
    moolatrikona-only placement now qualifies -- closing the gap the S132
    fact-block-only version left. Without degrees it FALLS BACK to the fact
    block's sign-level dignity label (Exalted / Own Sign), and moolatrikona-only
    is then unreachable (documented, not silent)."""
    degs = facts.get("planet_degrees") or {}
    deg = degs.get(g)
    if isinstance(deg, (int, float)) and 0.0 <= float(deg) < 30.0 and sign in _SIGNS:
        try:
            d = get_dignity_status(g, sign, float(deg))
        except Exception:  # noqa: BLE001 -- a bad value costs one yoga, never the run
            d = None
        return (d in _QUALIFYING_PMP, d or "no special dignity")
    label = (_pos(facts).get(g) or {}).get("dignity")
    # fact-block label uses "Own Sign"; normalise to the same words for display
    return (label in ("Exalted", "Own Sign"),
            label.lower() if isinstance(label, str) else "no special dignity")


def _pancha_mahapurusha(facts):
    """The five Pancha Mahapurusha yogas: Mars/Mercury/Jupiter/Venus/Saturn in
    a kendra (1,4,7,10) AND in own / moolatrikona / exalted sign. One row per
    planet, fired or not. Degree-accurate via `_pmp_qualifies` when the fact
    block carries planet degrees."""
    pos = _pos(facts)
    out = []
    for g, name in _PMP_NAMES.items():
        row = pos.get(g)
        if not isinstance(row, dict) or row.get("house") is None:
            out.append(_row(f"pmp_{name.lower()}", f"{name} (Pancha Mahapurusha)",
                            False, f"{g}'s placement is not known", []))
            continue
        house, sign = row.get("house"), row.get("sign")
        in_kendra = house in (1, 4, 7, 10)
        qualifies, dlabel = _pmp_qualifies(facts, g, sign)
        fired = bool(in_kendra and qualifies)
        if fired:
            why = f"{g} is in the {_ordinal(int(house))} (a kendra), {dlabel} in {sign}"
        else:
            place = (f"in the {_ordinal(int(house))}"
                     + ("" if in_kendra else " (not a kendra)"))
            dig = (f"{dlabel} in {sign}" if qualifies
                   else f"not in own, moolatrikona or exaltation sign ({sign})")
            why = f"{g} is {place}, {dig}"
        out.append(_row(f"pmp_{name.lower()}", f"{name} (Pancha Mahapurusha)",
                        fired, why,
                        [f"planet_positions.{g}.house={house}",
                         f"planet_positions.{g}.sign={sign}",
                         f"dignity={dlabel}"]))
    return out
