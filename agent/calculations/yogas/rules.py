"""All yoga calculations -- one module.

Replaces catalog/raja_yogas.py, catalog/special.py and
catalog/neecha_bhanga.py, which were three files only because a Session 40
Claude Code prompt happened to name them that way in passing; the split was
never a design decision (verified against the original design-chat history,
S132). `catalog/pancha_mahapurusha.py` stays unwired -- not for want of
degrees, but because the Pancha Mahapurusha check here now subsumes it. That
check is DEGREE-ACCURATE (S133): it resolves each graha's dignity via
`core.dignity.get_dignity_status` over a detector-only `planet_degrees` key
(degree_in_sign, passed by yoga_facts, never entering the interpreter payload),
so a moolatrikona-only placement IS reachable. Everything else still reads the
fact block's own sign-level dignity label. See the import comment below and
`_pmp_qualifies`.

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
            + _detect_neecha(facts) + _detect_jhora_set(facts)
            + _detect_dhana(facts) + _detect_kalatra_santana(facts)
            + _detect_tier23(facts))



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


# ===========================================================================
# DHANA (wealth) and DARIDRA (penury) -- BPHS 1 ch41 and ch42.
#
# WHY THESE FIRST (S138). Measured against what users actually ask, the yoga
# layer was DEEP on one topic and EMPTY on five: career/status had Raja,
# Vipareeta, Pancha Mahapurusha and four Yogadas, while money -- the second
# commonest question -- had NOTHING. ch42 also supplies the first honest
# NEGATIVES in the catalogue: every yoga shipped before this one was good news,
# which is why answers read as flattery (SESSION_LOG S136 s12 item 6).
#
# SPEC SOURCE IS THE CORPUS ITSELF. Every rule below is the verse in
# `data/chapter_index_bphs.json` unit `bphs1_ch41` / `bphs1_ch42`, cited by
# sloka. The oracle grades the ANSWER and never supplies a formula (P-028), and
# no doctrine prose enters a `reason` -- reasons state the observed placement
# only (P-029).
#
# WHAT IS DELIBERATELY NOT BUILT, and why -- so no session re-derives it:
#   * ch41 vv.18-34 (Parijatamsa/Uttamamsa... divisional dignities of the
#     angular, 5th and 9th lords). Needs Dasa-Varga amsa dignity, which the
#     fact block does not carry. Not synthesisable.
#   * ch41 v16 ("the 9th and 5th lords are capable of bestowing wealth").
#     A DEFINITION, not a discriminating rule -- it is true of every chart, so
#     it would fire for everyone and read as a Barnum line (S119 invariant 3).
#   * ch42 vv.2, 3, 7(second half), 8, 10, 11, 13, 14, 15 -- every one turns on
#     a MARAKA lord, and ch42 does not define maraka. Taking the usual "2nd and
#     7th lords" from anywhere else would be a formula from a non-spec source
#     (P-028). Build when the maraka definition is sourced from BPHS itself.
#   * ch42 v5 needs "an enemy's sign", i.e. friendship tiers -- deliberately
#     OUT of the fact block as contested (S130). Not approximated.
#   * ch42 v9, v12 need dispositor-chains / an auspicious-house classification
#     the fact block does not define.
# ===========================================================================

_DUSTHANA = (6, 8, 12)


def _lord_house(lords, n):
    """House occupied by the lord of house `n`, or None."""
    row = lords.get(n)
    if not isinstance(row, dict):
        return None
    try:
        return int(row["in_house"])
    except (KeyError, TypeError, ValueError):
        return None


def _lord_graha(lords, n):
    row = lords.get(n)
    return row.get("lord") if isinstance(row, dict) else None


def _sign_house(facts, sign):
    """House number a sign occupies, derived from any graha standing in it."""
    for g in _GRAHAS:
        if _sign_of(facts, g) == sign:
            return _house_of(_pos(facts), g)
    return None


def _nth_sign(facts, n):
    """The sign on house `n`, counted from the ascendant sign."""
    asc = facts.get("ascendant_sign")
    if asc not in _SIGNS:
        return None
    return _SIGNS[(_SIGNS.index(asc) + n - 1) % 12]


def _in_own_sign(facts, graha):
    s = _sign_of(facts, graha)
    return bool(s) and _SIGN_LORD.get(s) == graha


# ---- ch41: YOGAS FOR GREAT AFFLUENCE (vv.2-8) ----

def _dhana_maha_5_11(facts, lords):
    """ch41 v8 closing note -- BPHS states the shared formula of vv.2-8 itself:
    "the 5th lord should be in the 5th while the 11th lord is in the 11th".

    The seven slokas above it are sign-locked instances of this; this rule is
    the general form the text gives, not an inference over them.
    """
    h5, h11 = _lord_house(lords, 5), _lord_house(lords, 11)
    fired = h5 == 5 and h11 == 11
    return _row("dhana_maha_5_11", "Maha Dhana (5th and 11th lords in own houses)",
                fired,
                f"the 5th lord is in the {_ordinal(h5)} and the 11th lord in the "
                f"{_ordinal(h11)}" if h5 and h11 else "the 5th or 11th lord's house is unknown",
                ["ch41_v8", f"5th_lord_house={h5}", f"11th_lord_house={h11}"])


def _dhana_affluence_specifics(facts):
    """ch41 vv.2-8, one row each. Each is a named graha in the 5th with named
    grahas in the 11th; every one is sign-locked and therefore rare, which is
    the text's own shape and not a defect."""
    n5, n11 = _nth_sign(facts, 5), _nth_sign(facts, 11)
    if not (n5 and n11):
        return []
    occ5 = _occupants(facts, n5)
    occ11 = _occupants(facts, n11)

    def row(rid, name, need5, need11, sloka):
        ok5 = all(g in occ5 for g in need5)
        ok11 = all(g in occ11 for g in need11)
        return _row(rid, name, ok5 and ok11,
                    f"the 5th ({n5}) holds {occ5 or 'nothing'} and the 11th "
                    f"({n11}) holds {occ11 or 'nothing'}",
                    [f"ch41_v{sloka}", f"5th_sign={n5}", f"11th_sign={n11}",
                     f"needs_5th={list(need5)}", f"needs_11th={list(need11)}"])

    out = []
    if _SIGN_LORD.get(n5) == "Venus":
        out.append(row("dhana_v2_venus_5_mars_11", "Great Affluence (Venus 5th, Mars 11th)",
                       ("Venus",), ("Mars",), 2))
    if _SIGN_LORD.get(n5) == "Mercury":
        out.append(row("dhana_v3_mercury_5", "Great Affluence (Mercury 5th; Moon, Mars, Jupiter 11th)",
                       ("Mercury",), ("Moon", "Mars", "Jupiter"), 3))
    if n5 == "Leo":
        out.append(row("dhana_v4_sun_5", "Great Affluence (Sun in Leo 5th; Saturn, Moon, Jupiter 11th)",
                       ("Sun",), ("Saturn", "Moon", "Jupiter"), 4))
    if _SIGN_LORD.get(n5) == "Saturn":
        out.append(row("dhana_v5_saturn_5_luminaries_11", "Great Affluence (Saturn own 5th; Sun and Moon 11th)",
                       ("Saturn",), ("Sun", "Moon"), 5))
    if _SIGN_LORD.get(n5) == "Jupiter":
        out.append(row("dhana_v6_jupiter_5_mercury_11", "Great Affluence (Jupiter own 5th, Mercury 11th)",
                       ("Jupiter",), ("Mercury",), 6))
    if _SIGN_LORD.get(n5) == "Mars":
        out.append(row("dhana_v7_mars_5_venus_11", "Great Affluence (Mars own 5th, Venus 11th)",
                       ("Mars",), ("Venus",), 7))
    if n5 == "Cancer":
        out.append(row("dhana_v8_moon_5_saturn_11", "Great Affluence (Moon in Cancer 5th, Saturn 11th)",
                       ("Moon",), ("Saturn",), 8))
    return out


# ---- ch41: YOGAS FOR WEALTH (vv.9-15) ----

_DHANA_LAGNA = (
    ("sun", "Sun", ("Mars", "Jupiter"), 9),
    ("moon", "Moon", ("Mercury", "Jupiter"), 10),
    ("mars", "Mars", ("Mercury", "Venus", "Saturn"), 11),
    ("mercury", "Mercury", ("Saturn", "Jupiter"), 12),
    ("jupiter", "Jupiter", ("Mercury", "Mars"), 13),
    ("venus", "Venus", ("Saturn", "Mercury"), 14),
    ("saturn", "Saturn", ("Mars", "Jupiter"), 15),
)


def _dhana_lagna_own_sign(facts):
    """ch41 vv.9-15. One graha in ITS OWN SIGN RISING, conjunct with or
    aspected by the named supporters. "Conjunct or aspected by" is the text's
    own disjunction -- both arms are checked, neither is narrowed."""
    out = []
    asc = facts.get("ascendant_sign")
    for key, graha, supporters, sloka in _DHANA_LAGNA:
        in_lagna = (_house_of(_pos(facts), graha) == 1
                    and _in_own_sign(facts, graha)
                    and _sign_of(facts, graha) == asc)
        linked = [s for s in supporters
                  if _sign_of(facts, s) == _sign_of(facts, graha)
                  or _aspects_between(facts, graha, s)]
        fired = in_lagna and len(linked) == len(supporters)
        out.append(_row(
            f"dhana_lagna_{key}", f"Wealth ({graha} in own sign rising)", fired,
            (f"{graha} is in {_sign_of(facts, graha)}"
             + (" which is the rising sign" if in_lagna else ", not its own rising sign")
             + f"; of {', '.join(supporters)} it is joined or aspected by "
               f"{', '.join(linked) if linked else 'none'}"),
            [f"ch41_v{sloka}", f"ascendant={asc}", f"{graha}.sign={_sign_of(facts, graha)}",
             f"supporters_linked={linked}"]))
    return out


# ---- ch42: COMBINATIONS FOR PENURY ----

def _daridra_rules(facts, lords):
    """ch42. The maraka-dependent slokas are NOT here -- see the module note.

    These are the catalogue's first honest negatives, and vv.16-18 carry their
    own NULLIFICATION clauses, which are implemented as part of the rule rather
    than as a separate cancelling pass: the text states the condition and its
    undoing in one breath.
    """
    out = []
    pos = _pos(facts)
    asc_lord = _lord_graha(lords, 1)
    n2 = _nth_sign(facts, 2)
    occ2 = _occupants(facts, n2) if n2 else []

    # v4: the ascendant or the Moon with Ketu, while the ascendant lord is in the 8th.
    ketu_sign = _sign_of(facts, "Ketu")
    with_ketu = bool(ketu_sign) and ketu_sign in {facts.get("ascendant_sign"),
                                                  _sign_of(facts, "Moon")}
    lord1_h = _lord_house(lords, 1)
    out.append(_row("daridra_v4_ketu_lagna_lord_8th",
                    "Penury (Ketu with lagna or Moon; lagna lord in the 8th)",
                    with_ketu and lord1_h == 8,
                    f"Ketu is in {ketu_sign}; the ascendant lord is in the "
                    f"{_ordinal(lord1_h) if lord1_h else 'unknown house'}",
                    ["ch42_v4", f"ketu_sign={ketu_sign}", f"lagna_lord_house={lord1_h}"]))

    # v6: the ascendant lord conjunct a 6th/8th/12th lord OR Saturn, and
    # devoid of benefic aspect.
    if asc_lord:
        dl = {_lord_graha(lords, h) for h in _DUSTHANA} - {None}
        companions = [g for g in _GRAHAS
                      if g != asc_lord and _sign_of(facts, g) == _sign_of(facts, asc_lord)]
        bad = [g for g in companions if g in dl or g == "Saturn"]
        benefic_aspect = [g for g in _GRAHAS
                          if g != asc_lord and _is_benefic(facts, g)
                          and _aspects_between(facts, asc_lord, g)]
        out.append(_row("daridra_v6_lagna_lord_with_evil_lord",
                        "Penury (lagna lord with an evil-house lord or Saturn, unaspected by a benefic)",
                        bool(bad) and not benefic_aspect,
                        f"the ascendant lord {asc_lord} shares its sign with "
                        f"{companions or 'no graha'}; benefic aspect from "
                        f"{benefic_aspect or 'none'}",
                        ["ch42_v6", f"lagna_lord={asc_lord}", f"adverse_companions={bad}",
                         f"benefic_aspects={benefic_aspect}"]))

    # v7 (first half): the 5th and 9th lords in the 6th and 12th respectively.
    # The maraka-aspect half is NOT applied -- recorded, not approximated.
    h5, h9 = _lord_house(lords, 5), _lord_house(lords, 9)
    out.append(_row("daridra_v7_5th_in_6th_9th_in_12th",
                    "Penury (5th lord in the 6th, 9th lord in the 12th)",
                    h5 == 6 and h9 == 12,
                    f"the 5th lord is in the {_ordinal(h5) if h5 else 'unknown'} and "
                    f"the 9th lord in the {_ordinal(h9) if h9 else 'unknown'}",
                    ["ch42_v7", "maraka_condition_not_applied",
                     f"5th_lord_house={h5}", f"9th_lord_house={h9}"]))

    # vv.16-18: the 2nd house, WITH the nullifications the text supplies.
    mars_sat_2 = {"Mars", "Saturn"} <= set(occ2)
    merc_aspects = (_aspects_between(facts, "Mercury", "Mars")
                    and _aspects_between(facts, "Mercury", "Saturn"))
    out.append(_row("daridra_v16_mars_saturn_2nd",
                    "Wealth destroyed (Mars and Saturn together in the 2nd)",
                    mars_sat_2 and not merc_aspects,
                    f"the 2nd ({n2}) holds {occ2 or 'nothing'}; Mercury aspects both: "
                    f"{merc_aspects}",
                    ["ch42_v16-18", f"2nd_sign={n2}", f"2nd_occupants={occ2}",
                     f"mercury_aspects_both={merc_aspects}"]))
    # The same verse's positive arm, stated separately so the answer can carry it.
    out.append(_row("dhana_v17_mars_saturn_2nd_mercury_aspect",
                    "Great wealth (Mercury aspecting Mars and Saturn in the 2nd)",
                    mars_sat_2 and merc_aspects,
                    f"the 2nd ({n2}) holds {occ2 or 'nothing'}; Mercury aspects both: "
                    f"{merc_aspects}",
                    ["ch42_v16-18", f"2nd_occupants={occ2}"]))

    sun_2 = "Sun" in occ2
    sat_2 = "Saturn" in occ2
    sun_sat = _aspects_between(facts, "Sun", "Saturn")
    out.append(_row("daridra_v17_sun_2nd_saturn_aspect",
                    "Penury (Sun in the 2nd aspected by Saturn)",
                    sun_2 and sun_sat,
                    f"the 2nd ({n2}) holds {occ2 or 'nothing'}; Sun and Saturn aspect "
                    f"each other: {sun_sat}",
                    ["ch42_v17", f"2nd_occupants={occ2}", f"sun_saturn_aspect={sun_sat}"]))
    out.append(_row("dhana_v17_sun_2nd_unaspected",
                    "Riches and fame (Sun in the 2nd NOT aspected by Saturn)",
                    sun_2 and not sun_sat,
                    f"the 2nd ({n2}) holds {occ2 or 'nothing'}; Sun and Saturn aspect "
                    f"each other: {sun_sat}",
                    ["ch42_v17", f"2nd_occupants={occ2}"]))
    out.append(_row("daridra_v18_saturn_2nd_sun_aspect",
                    "Penury (Saturn in the 2nd aspected by the Sun)",
                    sat_2 and sun_sat,
                    f"the 2nd ({n2}) holds {occ2 or 'nothing'}; Sun and Saturn aspect "
                    f"each other: {sun_sat}",
                    ["ch42_v18", f"2nd_occupants={occ2}", f"sun_saturn_aspect={sun_sat}"]))
    return out


def _detect_dhana(facts: dict) -> list[dict]:
    """Every ch41/ch42 check, fired or not. Never raises: a bad rule costs a
    yoga, never the answer."""
    lords = _house_lords(facts)
    if not lords:
        return []
    out = [_dhana_maha_5_11(facts, lords)]
    out += _dhana_affluence_specifics(facts)
    out += _dhana_lagna_own_sign(facts)
    out += _daridra_rules(facts, lords)
    return [v for v in out if v]


# ===========================================================================
# KALATRA (marriage, BPHS 1 ch18) and SANTANA (children, BPHS 1 ch16).
#
# Tier 1 completion (S138). Marriage is the 5th commonest question users bring
# and had only Mangal Dosha; children is the 7th and had nothing at all.
#
# A PRODUCT BOUNDARY, NOT A TECHNICAL ONE -- the reason this batch is smaller
# than its chapters. ch18 vv.7-13 and ch16 v14 are computable and are NOT
# built: they characterise a spouse's sexual conduct ("harlot", "attached to
# other men"), describe a spouse's body, or declare the native "of questionable
# birth". ch18 v3b and ch19 v42 predict the DEATH of a spouse. Shipping any of
# that to a person reading about their own life is a call for Sulabh, not for
# this module, so they are REGISTERED here and left unbuilt. This is a
# different register from "not computable" and must not be collapsed into it.
#
# Also unbuilt, and these ARE technical:
#   * ch18 vv.4-5, ch16 vv.11-12 -- turn on planetary STRENGTH (shadbala),
#     which the fact block does not carry.
#   * ch18 v5, ch16 v8 (one arm) -- "an enemy's sign", i.e. friendship tiers,
#     deliberately OUT as contested (S130). The computable arms of ch16 v8 are
#     built; the inimical arm is not, and the rule says so in its evidence.
#   * combustion (ch18 v5, ch16 v1c) -- not a fact class.
#   * ch16 v9 -- needs Mandi/Gulika, not computed.
#   * ch16 v13 second arm -- the Moon's DECANATE needs degrees (S130: tables
#     are sign-level). The conjunction arm is built.
#
# Spec source is the corpus: `bphs1_ch18`, `bphs1_ch16`, cited by sloka.
# ===========================================================================


def _dignity_of(facts, graha):
    row = _pos(facts).get(graha)
    return row.get("dignity") if isinstance(row, dict) else None


def _navamsa_sign(facts, graha):
    row = ((facts.get("navamsa") or {}).get("placements") or {}).get(graha)
    return row.get("sign") if isinstance(row, dict) else None


def _aspects_house(facts, graha, house):
    by = (facts.get("aspects") or {}).get("aspects_by_planet") or {}
    try:
        return int(house) in {int(h) for h in (by.get(graha) or [])}
    except (TypeError, ValueError):
        return False


_NODES = ("Rahu", "Ketu")


def _bodies_in_sign(facts, sign, exclude=()):
    """Occupants INCLUDING Rahu and Ketu.

    `_occupants` deliberately walks `_GRAHAS`, the seven classical grahas, because
    its callers reason about benefic/malefic nature, dignity and lordship, none of
    which the nodes have. OCCUPANCY is a different question: ch16 vv.5 and 7 put
    KETU in the 5th, and reading them through `_occupants` made them silently
    unfireable on every chart. Found by a test written to fire the rule -- which
    is why rules get a chart built to fire them (Working Style #3).
    """
    return [g for g in tuple(_GRAHAS) + _NODES
            if g not in exclude and _sign_of(facts, g) == sign]


def _kalatra_rules(facts, lords):
    """ch18. Only the placement rules; see the module note for what is left out
    and on whose authority."""
    out = []
    l7 = _lord_graha(lords, 7)
    h7 = _lord_house(lords, 7)
    if not l7:
        return out
    own = _in_own_sign(facts, l7)
    exalted = _dignity_of(facts, l7) == _EXALTED
    sign7 = _sign_of(facts, l7)

    # v1: the 7th lord in his own sign or in exaltation.
    out.append(_row("kalatra_v1_7th_lord_strong_placed",
                    "Happiness through marriage (7th lord in own sign or exalted)",
                    own or exalted,
                    f"the 7th lord {l7} is in {sign7}"
                    + (" (its own sign)" if own else "")
                    + (f" [{_dignity_of(facts, l7)}]" if _dignity_of(facts, l7) else ""),
                    ["ch18_v1", f"7th_lord={l7}", f"sign={sign7}", f"own={own}",
                     f"exalted={exalted}"]))

    # v2: the 7th lord in the 6th, 8th or 12th -- EXCEPT when that placement is
    # its own sign or exaltation, which the verse excludes explicitly.
    in_dusthana = h7 in _DUSTHANA
    out.append(_row("kalatra_v2_7th_lord_in_dusthana",
                    "Affliction to the 7th lord (in the 6th, 8th or 12th)",
                    bool(in_dusthana) and not (own or exalted),
                    f"the 7th lord {l7} is in the "
                    f"{_ordinal(h7) if h7 else 'unknown house'}"
                    + (" but in its own sign or exaltation" if (own or exalted) else ""),
                    ["ch18_v2", f"7th_lord_house={h7}", f"own_or_exalted={own or exalted}"]))

    # v6: the 7th lord in a sign of Saturn or Venus and aspected by a benefic;
    # or the 7th lord in exaltation.
    sat_ven_sign = _SIGN_LORD.get(sign7) in ("Saturn", "Venus") if sign7 else False
    benefics = [g for g in _GRAHAS
                if g != l7 and _is_benefic(facts, g) and _aspects_between(facts, l7, g)]
    out.append(_row("kalatra_v6_plurality",
                    "Plurality indicated (7th lord in a Saturn/Venus sign with benefic aspect, or exalted)",
                    (sat_ven_sign and bool(benefics)) or exalted,
                    f"the 7th lord {l7} is in {sign7}; benefic aspect from "
                    f"{benefics or 'none'}",
                    ["ch18_v6", f"sign_lord={_SIGN_LORD.get(sign7)}",
                     f"benefic_aspects={benefics}", f"exalted={exalted}"]))
    return out


def _santana_rules(facts, lords):
    """ch16. The 5th house and its lord."""
    out = []
    l1, l5, l9 = (_lord_graha(lords, n) for n in (1, 5, 9))
    h1, h5, h9 = (_lord_house(lords, n) for n in (1, 5, 9))
    n5 = _nth_sign(facts, 5)
    occ5 = _bodies_in_sign(facts, n5) if n5 else []   # nodes included: vv.5, 7 name Ketu
    fallen5 = _dignity_of(facts, l5) == "Debilitated" if l5 else False

    # v1a: the ascendant and 5th lords in own signs, or in an angle, or in a trine.
    if l1 and l5:
        def placed_well(g, h):
            return bool(_in_own_sign(facts, g)) or (h in KENDRA_HOUSES) or (h in TRIKONA_HOUSES)
        out.append(_row("santana_v1_lords_well_placed",
                        "Happiness through children (lagna and 5th lords in own signs, angles or trines)",
                        placed_well(l1, h1) and placed_well(l5, h5),
                        f"the ascendant lord {l1} is in the {_ordinal(h1) if h1 else '?'} "
                        f"and the 5th lord {l5} in the {_ordinal(h5) if h5 else '?'}",
                        ["ch16_v1", f"lagna_lord={l1}", f"lagna_lord_house={h1}",
                         f"5th_lord={l5}", f"5th_lord_house={h5}"]))

    # v1b: the 5th lord in the 6th, 8th or 12th.
    out.append(_row("santana_v1b_5th_lord_in_dusthana",
                    "Obstruction to progeny (5th lord in the 6th, 8th or 12th)",
                    h5 in _DUSTHANA,
                    f"the 5th lord is in the {_ordinal(h5) if h5 else 'unknown house'}",
                    ["ch16_v1", f"5th_lord_house={h5}"]))

    # v4: the 5th lord in the 6th while the ascendant lord is conjunct Mars.
    mars_with_l1 = bool(l1) and l1 != "Mars" and _sign_of(facts, l1) == _sign_of(facts, "Mars")
    out.append(_row("santana_v4_5th_lord_6th_lagna_lord_mars",
                    "Loss of the first child (5th lord in the 6th, lagna lord with Mars)",
                    h5 == 6 and mars_with_l1,
                    f"the 5th lord is in the {_ordinal(h5) if h5 else '?'}; the ascendant "
                    f"lord {l1} shares its sign with Mars: {mars_with_l1}",
                    ["ch16_v4", f"5th_lord_house={h5}", f"lagna_lord_with_mars={mars_with_l1}"]))

    # v5: the 5th lord in fall in the 6th/8th/12th while Mercury and Ketu are in the 5th.
    merc_ketu_5 = {"Mercury", "Ketu"} <= set(occ5)
    out.append(_row("santana_v5_one_child_mercury_ketu",
                    "A single issue (5th lord fallen in a dusthana; Mercury and Ketu in the 5th)",
                    fallen5 and h5 in _DUSTHANA and merc_ketu_5,
                    f"the 5th lord {l5} is {_dignity_of(facts, l5) or 'in no head dignity'} "
                    f"in the {_ordinal(h5) if h5 else '?'}; the 5th ({n5}) holds {occ5 or 'nothing'}",
                    ["ch16_v5", f"5th_lord_fallen={fallen5}", f"5th_occupants={occ5}"]))

    # v6: the 5th lord in fall and NOT aspecting the 5th, while Saturn and
    # Mercury are in the 5th.
    sat_merc_5 = {"Saturn", "Mercury"} <= set(occ5)
    aspects_5 = bool(l5) and _aspects_house(facts, l5, 5)
    out.append(_row("santana_v6_one_child_saturn_mercury",
                    "A single issue (5th lord fallen and not aspecting the 5th; Saturn and Mercury there)",
                    fallen5 and not aspects_5 and sat_merc_5,
                    f"the 5th lord {l5} is {_dignity_of(facts, l5) or 'in no head dignity'}; "
                    f"it aspects the 5th: {aspects_5}; the 5th ({n5}) holds {occ5 or 'nothing'}",
                    ["ch16_v6", f"5th_lord_fallen={fallen5}", f"5th_lord_aspects_5th={aspects_5}",
                     f"5th_occupants={occ5}"]))

    # v7: the 9th lord in the ascendant, the 5th lord in fall, Ketu with Mercury in the 5th.
    out.append(_row("santana_v7_progeny_after_difficulty",
                    "Progeny only after difficulty (9th lord in the lagna; 5th lord fallen; Ketu and Mercury in the 5th)",
                    h9 == 1 and fallen5 and merc_ketu_5,
                    f"the 9th lord is in the {_ordinal(h9) if h9 else '?'}; the 5th lord is "
                    f"{_dignity_of(facts, l5) or 'in no head dignity'}; the 5th holds {occ5 or 'nothing'}",
                    ["ch16_v7", f"9th_lord_house={h9}", f"5th_lord_fallen={fallen5}",
                     f"5th_occupants={occ5}"]))

    # v8: the 5th lord in the 6th/8th/12th, or in fall, or in the 5th itself.
    # The verse's "inimical sign" arm is NOT applied -- friendship tiers are out.
    out.append(_row("santana_v8_issues_with_difficulty",
                    "Issues with difficulty (5th lord in a dusthana, in fall, or in the 5th itself)",
                    (h5 in _DUSTHANA) or fallen5 or h5 == 5,
                    f"the 5th lord {l5} is in the {_ordinal(h5) if h5 else '?'}"
                    + (f" [{_dignity_of(facts, l5)}]" if _dignity_of(facts, l5) else ""),
                    ["ch16_v8", "inimical_sign_arm_not_applied",
                     f"5th_lord_house={h5}", f"5th_lord_fallen={fallen5}"]))

    # v10: the Sun and Moon together in one rasi AND in the same navamsa.
    same_rasi = bool(_sign_of(facts, "Sun")) and _sign_of(facts, "Sun") == _sign_of(facts, "Moon")
    nav_sun, nav_moon = _navamsa_sign(facts, "Sun"), _navamsa_sign(facts, "Moon")
    same_nav = bool(nav_sun) and nav_sun == nav_moon
    out.append(_row("santana_v10_luminaries_same_rasi_and_navamsa",
                    "Raised by others (Sun and Moon in one sign and one navamsa)",
                    same_rasi and same_nav,
                    f"Sun and Moon share a sign: {same_rasi}; they share a navamsa "
                    f"({nav_sun} / {nav_moon}): {same_nav}",
                    ["ch16_v10", f"same_rasi={same_rasi}", f"Sun.navamsa={nav_sun}",
                     f"Moon.navamsa={nav_moon}"]))

    # v13: the 5th lord joined with the Moon. The DECANATE arm needs degrees.
    with_moon = bool(l5) and l5 != "Moon" and _sign_of(facts, l5) == _sign_of(facts, "Moon")
    out.append(_row("santana_v13_daughters",
                    "Daughters indicated (5th lord joined with the Moon)",
                    with_moon,
                    f"the 5th lord {l5} shares its sign with the Moon: {with_moon}",
                    ["ch16_v13", "decanate_arm_not_applied", f"5th_lord={l5}"]))
    return out


def _detect_kalatra_santana(facts: dict) -> list[dict]:
    lords = _house_lords(facts)
    if not lords:
        return []
    return [v for v in (_kalatra_rules(facts, lords)
                        + _santana_rules(facts, lords)) if v]


# ===========================================================================
# TIER 2 + TIER 3 (S138). Longevity, home/conveyances, the ch24 lord table
# selected for education and foreign residence, and the Naabhasa /
# lunar / solar families the Tier-1 batches left half-finished.
#
# NOT IMPLEMENTED HERE, AND WHY -- each of these was read and rejected, not
# overlooked:
#   * ch19 v8, v15 and the third arm of v9 all turn on the ascendant lord
#     being "bereft of strength" / "exceedingly strong". The fact block
#     carries no strength measure (Shadbala is not computed), and a dignity
#     label is NOT a strength proxy. Implementing them against dignity would
#     ship a rule that answers a different question than the verse asks
#     (P-032). They stay out until a strength fact exists.
#   * ch19 v11 requires the 8th lord DEBILITATED IN THE ASCENDANT. R.
#     Santhanam's own note to v12 shows that by whole signs this is
#     unreachable for every ascendant -- it needs a bhava cusp falling in an
#     adjacent sign. A rule that can never fire is the `_GRAHAS`/nodes defect
#     again, so it is not written rather than written dead.
#   * Chandra-Mangal yoga (Moon + Mars) is NOT in BPHS. It is a Jataka
#     Parijata / Phaladeepika yoga. The retrieval corpus is BPHS only, so a
#     row for it could cite no verse and every claim resting on it would be
#     dropped by the ghost guard. Out of corpus, not out of scope.
#   * ch15 v5, v7, v9 read on Mercury's exaltation, the mother's happiness and
#     dumbness; they are computable but belong to no question topic this batch
#     was prioritised for. Deliberately deferred, not blocked.
#
# EXISTING ROWS NOT RETROFITTED. `_vesi`, `_sunaphaa`, `_anaphaa`, `_adhi`
# and `_naabhasa_sankhya` were written from the PVR spec and carry no sloka
# id in evidence. The new rows below cite BPHS directly. Retrofitting the old
# five is a separate, behaviour-visible change (their evidence lists are
# asserted in test_rules.py) and is NOT bundled into this batch.
# ===========================================================================

_MOVABLE_MODE, _FIXED_MODE, _DUAL_MODE = 0, 1, 2
_PANAPHARA = (2, 5, 8, 11)
_APOKLIMA = (3, 6, 9, 12)
_UPACHAYA = (3, 6, 10, 11)


def _g_house(facts, graha):
    """House occupied by `graha`, or None."""
    row = _pos(facts).get(graha)
    if not isinstance(row, dict):
        return None
    try:
        return int(row["house"])
    except (KeyError, TypeError, ValueError):
        return None


def _graha_houses(facts):
    """{graha: house} for the seven classical grahas that are placed.

    The Naabhasa family says "all the 7 planets" and means exactly those; the
    nodes are excluded by the text, not by an oversight of ours (contrast
    `_bodies_in_sign`, which exists because ch16 names Ketu).
    """
    return {g: h for g in _GRAHAS if (h := _g_house(facts, g)) is not None}


def _all_seven_placed(hm):
    return len(hm) == len(_GRAHAS)


def _occupied_houses(facts):
    return set(_graha_houses(facts).values())


def _sign_mode(sign):
    """0 movable, 1 fixed, 2 dual -- the index parity `_rasi_aspects` uses."""
    return _SIGNS.index(sign) % 3 if sign in _SIGNS else None


def _malefics_in(facts, houses):
    hm = _graha_houses(facts)
    return [g for g, h in hm.items() if h in houses and not _is_benefic(facts, g)]


def _benefics_in(facts, houses):
    hm = _graha_houses(facts)
    return [g for g, h in hm.items() if h in houses and _is_benefic(facts, g)]


# ---- ch19: LONGEVITY (Effects Of The Eighth House) ----

def _ayush_rules(facts, lords):
    """ch19. Longevity combinations, both arms -- the chapter gives long-life
    and short-life yogas in the same breath and a detector that reported only
    one of them would misrepresent the chapter."""
    out = []
    l1, l5, l6, l8, l10, l12 = (_lord_graha(lords, n) for n in (1, 5, 6, 8, 10, 12))
    h1, h5, h6, h8, h10, h12 = (_lord_house(lords, n) for n in (1, 5, 6, 8, 10, 12))

    # v1: the 8th lord in an angle.
    out.append(_row("ayush_v1_8th_lord_in_kendra",
                    "Long life (8th lord in an angle)",
                    h8 in KENDRA_HOUSES,
                    f"the 8th lord {l8} is in the {_ordinal(h8) if h8 else 'unknown house'}",
                    ["ch19_v1", f"8th_lord={l8}", f"8th_lord_house={h8}"]))

    # v2: the 8th lord IN THE 8TH and joined either by the ascendant lord or by
    # a natural malefic. Both conditions, not either -- the verse's "be in the
    # 8th itself" is the second half of one sentence.
    in8 = [g for g, h in _graha_houses(facts).items() if h == 8]
    with_l1 = bool(l1) and l1 != l8 and l1 in in8
    malefic_co = [g for g in in8 if g != l8 and not _is_benefic(facts, g)]
    out.append(_row("ayush_v2_short_life_8th_lord_in_8th",
                    "Short life (8th lord in the 8th with the ascendant lord or a malefic)",
                    h8 == 8 and (with_l1 or bool(malefic_co)),
                    f"the 8th lord {l8} is in the {_ordinal(h8) if h8 else '?'}; the 8th "
                    f"holds {in8 or 'nothing'}",
                    ["ch19_v2", f"8th_lord={l8}", f"8th_lord_house={h8}",
                     f"8th_occupants={in8}", f"with_lagna_lord={with_l1}",
                     f"malefic_company={malefic_co}"]))

    # v3: "similarly consider Saturn and the 10th lord". The verse states the
    # analogy and nothing else; R. Santhanam's note to it spells out the two
    # placements the analogy produces. That expansion is the COMMENTARY's, not
    # Parasara's, and is flagged as such in evidence so a reader can discount it.
    sat_in_8 = _g_house(facts, "Saturn") == 8
    sat_company = [g for g in in8 if g != "Saturn"
                   and (g == l1 or not _is_benefic(facts, g))]
    out.append(_row("ayush_v3_saturn_in_8th_afflicted",
                    "Short life (Saturn in the 8th with the ascendant lord or a malefic)",
                    sat_in_8 and bool(sat_company),
                    f"Saturn is in the {_ordinal(_g_house(facts, 'Saturn')) if _g_house(facts, 'Saturn') else '?'}; "
                    f"its company there is {sat_company or 'none'}",
                    ["ch19_v3", "commentary_expansion=RSanthanam_note",
                     f"saturn_in_8th={sat_in_8}", f"company={sat_company}"]))
    l10_in_8 = h10 == 8
    l10_company = [g for g in in8 if g != l10
                   and (g == l1 or not _is_benefic(facts, g))]
    out.append(_row("ayush_v3b_10th_lord_in_8th_afflicted",
                    "Short life (10th lord in the 8th with the ascendant lord or a malefic)",
                    l10_in_8 and bool(l10_company),
                    f"the 10th lord {l10} is in the {_ordinal(h10) if h10 else '?'}; its "
                    f"company there is {l10_company or 'none'}",
                    ["ch19_v3", "commentary_expansion=RSanthanam_note",
                     f"10th_lord={l10}", f"10th_lord_house={h10}", f"company={l10_company}"]))

    # vv.4: three separate long-life yogas, kept as three rows because they are
    # three independent conditions and collapsing them would lose which one held.
    out.append(_row("ayush_v4_6th_lord_in_12th",
                    "Long life (6th lord in the 12th)",
                    h6 == 12,
                    f"the 6th lord {l6} is in the {_ordinal(h6) if h6 else 'unknown house'}",
                    ["ch19_v4", f"6th_lord={l6}", f"6th_lord_house={h6}"]))
    out.append(_row("ayush_v4b_6th_and_12th_lords_in_own_houses",
                    "Long life (6th lord in the 6th while the 12th lord is in the 12th)",
                    h6 == 6 and h12 == 12,
                    f"the 6th lord is in the {_ordinal(h6) if h6 else '?'} and the 12th "
                    f"lord in the {_ordinal(h12) if h12 else '?'}",
                    ["ch19_v4", f"6th_lord_house={h6}", f"12th_lord_house={h12}"]))
    out.append(_row("ayush_v4c_6th_lord_in_lagna_12th_lord_in_8th",
                    "Long life (6th lord in the ascendant while the 12th lord is in the 8th)",
                    h6 == 1 and h12 == 8,
                    f"the 6th lord is in the {_ordinal(h6) if h6 else '?'} and the 12th "
                    f"lord in the {_ordinal(h12) if h12 else '?'}",
                    ["ch19_v4", f"6th_lord_house={h6}", f"12th_lord_house={h12}"]))

    # v5: lords of the 5th, 8th and ascendant in own navamsas, own rasis OR
    # FRIENDLY SIGNS. The friendly-sign arm needs friendship tiers, which are
    # deliberately out of the fact block as contested (S130). Only the two
    # own-arms are applied, so this rule UNDER-fires by construction; the
    # evidence says so rather than the omission being silent.
    def own_rasi_or_navamsa(g):
        if not g:
            return False
        if _in_own_sign(facts, g):
            return True
        nav = _navamsa_sign(facts, g)
        return bool(nav) and _SIGN_LORD.get(nav) == g
    trio = [l1, l5, l8]
    trio_ok = all(own_rasi_or_navamsa(g) for g in trio) and all(trio)
    out.append(_row("ayush_v5_lords_1_5_8_in_own_rasi_or_navamsa",
                    "Long life (ascendant, 5th and 8th lords in own signs or own navamsas)",
                    trio_ok,
                    f"the ascendant lord {l1}, the 5th lord {l5} and the 8th lord {l8}: "
                    + ", ".join(f"{g}={own_rasi_or_navamsa(g)}" for g in trio),
                    ["ch19_v5", "friendly_sign_arm_not_applied",
                     f"lords={trio}",
                     f"navamsas={[_navamsa_sign(facts, g) for g in trio]}"]))

    # v6: the lords of the ascendant, 8th and 10th AND Saturn, each severally
    # in an angle, a trine or the 11th.
    good = set(KENDRA_HOUSES) | set(TRIKONA_HOUSES) | {11}
    quad = {"lagna lord": h1, "8th lord": h8, "10th lord": h10,
            "Saturn": _g_house(facts, "Saturn")}
    quad_ok = all(h in good for h in quad.values())
    out.append(_row("ayush_v6_lords_1_8_10_and_saturn_well_disposed",
                    "Long life (ascendant, 8th and 10th lords and Saturn each in an angle, a trine or the 11th)",
                    quad_ok,
                    "; ".join(f"{k} in the {_ordinal(v) if v else 'unknown house'}"
                              for k, v in quad.items()),
                    ["ch19_v6"] + [f"{k.replace(' ', '_')}_house={v}"
                                   for k, v in quad.items()]))

    # v9: the 8th lord IN FALL while the 8th holds a malefic. The verse's third
    # arm -- the ascendant lord bereft of strength -- is not applied (see the
    # section header); this rule therefore OVER-fires relative to the verse and
    # the evidence records which condition is missing.
    l8_fallen = _dignity_of(facts, l8) == _DEBILITATED if l8 else False
    malefics_in_8 = _malefics_in(facts, {8})
    out.append(_row("ayush_v9_8th_lord_fallen_with_malefic_in_8th",
                    "Short life (8th lord in fall with a malefic in the 8th)",
                    l8_fallen and bool(malefics_in_8),
                    f"the 8th lord {l8} is {_dignity_of(facts, l8) or 'in no head dignity'}; "
                    f"the 8th holds the malefic(s) {malefics_in_8 or 'none'}",
                    ["ch19_v9", "lagna_lord_strength_arm_not_applied",
                     f"8th_lord_fallen={l8_fallen}", f"malefics_in_8th={malefics_in_8}"]))

    # v10: the 8th house, the 8th lord and the 12th house all conjunct malefics.
    m8, m12 = _malefics_in(facts, {8}), _malefics_in(facts, {12})
    m_with_l8 = [g for g in _graha_houses(facts)
                 if g != l8 and h8 is not None and _g_house(facts, g) == h8
                 and not _is_benefic(facts, g)]
    out.append(_row("ayush_v10_malefics_on_8th_house_lord_and_12th",
                    "Immediate peril (malefics with the 8th house, the 8th lord and the 12th house)",
                    bool(m8) and bool(m12) and bool(m_with_l8),
                    f"malefics in the 8th: {m8 or 'none'}; in the 12th: {m12 or 'none'}; "
                    f"with the 8th lord {l8}: {m_with_l8 or 'none'}",
                    ["ch19_v10", f"malefics_8th={m8}", f"malefics_12th={m12}",
                     f"malefics_with_8th_lord={m_with_l8}"]))

    # v12: the 5th house, the 8th house and the 8th lord all conjunct malefics.
    m5 = _malefics_in(facts, {5})
    out.append(_row("ayush_v12_malefics_on_5th_8th_and_8th_lord",
                    "A very brief span (malefics with the 5th house, the 8th house and the 8th lord)",
                    bool(m5) and bool(m8) and bool(m_with_l8),
                    f"malefics in the 5th: {m5 or 'none'}; in the 8th: {m8 or 'none'}; "
                    f"with the 8th lord {l8}: {m_with_l8 or 'none'}",
                    ["ch19_v12", f"malefics_5th={m5}", f"malefics_8th={m8}",
                     f"malefics_with_8th_lord={m_with_l8}"]))

    # v13: the 8th lord in the 8th while the Moon is with malefics and receives
    # no benefic aspect.
    moon_h = _g_house(facts, "Moon")
    moon_malefics = [g for g in _graha_houses(facts)
                     if g != "Moon" and _g_house(facts, g) == moon_h
                     and not _is_benefic(facts, g)] if moon_h else []
    moon_benefic_aspect = [g for g in _GRAHAS
                           if g != "Moon" and _is_benefic(facts, g)
                           and _aspects_between(facts, "Moon", g)]
    out.append(_row("ayush_v13_8th_lord_in_8th_moon_besieged",
                    "Early peril (8th lord in the 8th; the Moon with malefics and unaspected by a benefic)",
                    h8 == 8 and bool(moon_malefics) and not moon_benefic_aspect,
                    f"the 8th lord is in the {_ordinal(h8) if h8 else '?'}; the Moon's "
                    f"malefic company is {moon_malefics or 'none'} and its benefic aspects "
                    f"are {moon_benefic_aspect or 'none'}",
                    ["ch19_v13", f"8th_lord_house={h8}", f"moon_malefic_company={moon_malefics}",
                     f"moon_benefic_aspects={moon_benefic_aspect}"]))

    # v14: the ascendant lord exalted, the Moon in the 11th, Jupiter in the 8th.
    l1_exalted = _dignity_of(facts, l1) == _EXALTED if l1 else False
    out.append(_row("ayush_v14_lagna_lord_exalted_moon_11th_jupiter_8th",
                    "Long life (ascendant lord exalted, the Moon in the 11th, Jupiter in the 8th)",
                    l1_exalted and moon_h == 11 and _g_house(facts, "Jupiter") == 8,
                    f"the ascendant lord {l1} is {_dignity_of(facts, l1) or 'in no head dignity'}; "
                    f"the Moon is in the {_ordinal(moon_h) if moon_h else '?'} and Jupiter in "
                    f"the {_ordinal(_g_house(facts, 'Jupiter')) if _g_house(facts, 'Jupiter') else '?'}",
                    ["ch19_v14", f"lagna_lord_exalted={l1_exalted}",
                     f"Moon_house={moon_h}", f"Jupiter_house={_g_house(facts, 'Jupiter')}"]))
    return out


# ---- ch15: HOME, PROPERTY AND CONVEYANCES (Effects Of The Fourth House) ----

def _sukha_rules(facts, lords):
    """ch15. The 4th house: residence, lands, conveyances."""
    out = []
    l1, l4, l10, l11 = (_lord_graha(lords, n) for n in (1, 4, 10, 11))
    h1, h4, h10, h11 = (_lord_house(lords, n) for n in (1, 4, 10, 11))

    # v2: the 4th occupied by its own lord or by the ascendant lord, and
    # aspected by a benefic.
    occ4 = [g for g, h in _graha_houses(facts).items() if h == 4]
    tenanted = (h4 == 4) or (h1 == 4)
    benefic_aspects_4 = [g for g in _GRAHAS
                         if _is_benefic(facts, g) and _aspects_house(facts, g, 4)]
    out.append(_row("sukha_v2_residential_comforts",
                    "Residential comforts (the 4th held by its lord or the ascendant lord, with benefic aspect)",
                    tenanted and bool(benefic_aspects_4),
                    f"the 4th holds {occ4 or 'nothing'}; the 4th lord {l4} is in the "
                    f"{_ordinal(h4) if h4 else '?'} and the ascendant lord {l1} in the "
                    f"{_ordinal(h1) if h1 else '?'}; benefics aspecting the 4th: "
                    f"{benefic_aspects_4 or 'none'}",
                    ["ch15_v2", f"4th_lord_house={h4}", f"lagna_lord_house={h1}",
                     f"benefic_aspects_4th={benefic_aspects_4}"]))

    # v3: TRANSLATION DIVERGENCE, resolved to the Sanskrit. R. Santhanam's
    # English reads "the 5th lord"; the sloka reads सुखस्थानाधिप --
    # sukha-sthaana-adhipa, the lord of the 4th (sukha bhava). The surrounding
    # verses are all about the 4th and its lord, and a 5th-lord rule would be a
    # non-sequitur between v2 and v4. The 4th lord is taken; the divergence is
    # recorded in evidence, not buried.
    own4 = _in_own_sign(facts, l4) if l4 else False
    nav4 = _navamsa_sign(facts, l4) if l4 else None
    own_nav4 = bool(nav4) and _SIGN_LORD.get(nav4) == l4
    exalt4 = _dignity_of(facts, l4) == _EXALTED if l4 else False
    out.append(_row("sukha_v3_lands_and_conveyances",
                    "Lands, conveyances and houses (4th lord in its own sign, own navamsa or exaltation)",
                    own4 or own_nav4 or exalt4,
                    f"the 4th lord {l4} is in {_sign_of(facts, l4)} (navamsa {nav4})"
                    + (f" [{_dignity_of(facts, l4)}]" if _dignity_of(facts, l4) else ""),
                    ["ch15_v3", "translation_divergence=english_reads_5th_lord;sanskrit_reads_4th",
                     f"4th_lord={l4}", f"own_sign={own4}", f"own_navamsa={own_nav4}",
                     f"exalted={exalt4}"]))

    # v4: the 10th lord joins the 4th lord in an angle or a trine.
    together = (bool(l4) and bool(l10) and l4 != l10
                and _sign_of(facts, l4) is not None
                and _sign_of(facts, l4) == _sign_of(facts, l10))
    in_kendra_kona = h4 in (set(KENDRA_HOUSES) | set(TRIKONA_HOUSES))
    out.append(_row("sukha_v4_mansions",
                    "Beautiful mansions (10th lord joined with the 4th lord in an angle or a trine)",
                    together and in_kendra_kona,
                    f"the 4th lord {l4} and the 10th lord {l10} share a sign: {together}; "
                    f"they stand in the {_ordinal(h4) if h4 else '?'}",
                    ["ch15_v4", f"4th_lord={l4}", f"10th_lord={l10}",
                     f"together={together}", f"house={h4}"]))

    # v6: a benefic in the 4th while the 4th lord is exalted. The verse's third
    # condition -- the karaka of the mother endowed with STRENGTH -- is not
    # applied; no strength fact exists (see the section header).
    benefics_in_4 = _benefics_in(facts, {4})
    out.append(_row("sukha_v6_long_living_mother",
                    "A long-living mother (benefic in the 4th, the 4th lord exalted)",
                    bool(benefics_in_4) and exalt4,
                    f"the 4th holds the benefic(s) {benefics_in_4 or 'none'}; the 4th lord "
                    f"{l4} is {_dignity_of(facts, l4) or 'in no head dignity'}",
                    ["ch15_v6", "karaka_strength_arm_not_applied",
                     f"benefics_in_4th={benefics_in_4}", f"4th_lord_exalted={exalt4}"]))

    # v8: the Sun in the 4th, the Moon and Saturn in the 9th, Mars in the 11th.
    q = {g: _g_house(facts, g) for g in ("Sun", "Moon", "Saturn", "Mars")}
    out.append(_row("sukha_v8_quadrupeds",
                    "Cattle and quadrupeds (Sun in the 4th, Moon and Saturn in the 9th, Mars in the 11th)",
                    q["Sun"] == 4 and q["Moon"] == 9 and q["Saturn"] == 9 and q["Mars"] == 11,
                    "; ".join(f"{g} in the {_ordinal(h) if h else 'unknown house'}"
                              for g, h in q.items()),
                    ["ch15_v8"] + [f"{g}_house={h}" for g, h in q.items()]))

    # vv.10-14, CONVEYANCES -- four separate combinations, four rows.
    # v10: the ascendant lord a benefic, the 4th lord in the 11th, Venus in the
    # 12th. The verse's first arm reads "the 4th lord IN FALL or in the 11th";
    # R. Santhanam flags the fall arm as probably corrupt text in his own note.
    # Only the 11th arm is implemented, and the evidence says so.
    l1_benefic = bool(l1) and _is_benefic(facts, l1)
    venus_h = _g_house(facts, "Venus")
    out.append(_row("sukha_v10_conveyance_early",
                    "Conveyances early (benefic ascendant lord, 4th lord in the 11th, Venus in the 12th)",
                    l1_benefic and h4 == 11 and venus_h == 12,
                    f"the ascendant lord {l1} is a benefic: {l1_benefic}; the 4th lord is in "
                    f"the {_ordinal(h4) if h4 else '?'}; Venus is in the "
                    f"{_ordinal(venus_h) if venus_h else '?'}",
                    ["ch15_v10", "fall_arm_not_applied=flagged_corrupt_by_translator",
                     f"lagna_lord_benefic={l1_benefic}", f"4th_lord_house={h4}",
                     f"Venus_house={venus_h}"]))

    # v11: the Sun in the 4th while the 4th lord is exalted and with Venus.
    l4_with_venus = (bool(l4) and l4 != "Venus"
                     and _sign_of(facts, l4) is not None
                     and _sign_of(facts, l4) == _sign_of(facts, "Venus"))
    out.append(_row("sukha_v11_conveyance_mid",
                    "Conveyances in mid-life (Sun in the 4th; the 4th lord exalted and with Venus)",
                    q["Sun"] == 4 and exalt4 and l4_with_venus,
                    f"the Sun is in the {_ordinal(q['Sun']) if q['Sun'] else '?'}; the 4th "
                    f"lord {l4} is {_dignity_of(facts, l4) or 'in no head dignity'} and shares "
                    f"a sign with Venus: {l4_with_venus}",
                    ["ch15_v11", f"Sun_house={q['Sun']}", f"4th_lord_exalted={exalt4}",
                     f"4th_lord_with_Venus={l4_with_venus}"]))

    # v12: the 4th lord joined with the 10th lord IN THE 4TH LORD'S EXALTATION
    # NAVAMSA. Read strictly: they share a navamsa sign, and that sign is the
    # 4th lord's exaltation sign.
    _EXALT_SIGN = {"Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn",
                   "Mercury": "Virgo", "Jupiter": "Cancer", "Venus": "Pisces",
                   "Saturn": "Libra"}
    nav10 = _navamsa_sign(facts, l10) if l10 else None
    share_nav = bool(nav4) and nav4 == nav10 and l4 != l10
    in_exalt_nav = bool(nav4) and _EXALT_SIGN.get(l4) == nav4
    out.append(_row("sukha_v12_conveyance_late",
                    "Conveyances later in life (4th and 10th lords together in the 4th lord's exaltation navamsa)",
                    share_nav and in_exalt_nav,
                    f"the 4th lord {l4} is in navamsa {nav4} and the 10th lord {l10} in "
                    f"navamsa {nav10}; that navamsa is the 4th lord's exaltation sign: "
                    f"{in_exalt_nav}",
                    ["ch15_v12", f"4th_lord_navamsa={nav4}", f"10th_lord_navamsa={nav10}",
                     f"shared={share_nav}", f"is_exaltation_navamsa={in_exalt_nav}"]))

    # v13: an EXCHANGE between the 4th and 11th lords.
    exchange = h4 == 11 and h11 == 4
    out.append(_row("sukha_v13_conveyance_exchange",
                    "Conveyances through an exchange (4th and 11th lords in each other's houses)",
                    exchange,
                    f"the 4th lord {l4} is in the {_ordinal(h4) if h4 else '?'} and the 11th "
                    f"lord {l11} in the {_ordinal(h11) if h11 else '?'}",
                    ["ch15_v13", f"4th_lord_house={h4}", f"11th_lord_house={h11}"]))
    return out


# ---- ch24: THE BHAVA-LORD TABLE, SELECTED ----
#
# ch24 is a complete 12x12 table: verse 1 + (lord-1)*12 + (house-1) states the
# effects of the Nth lord in the Mth house, for every N and M. That makes the
# citation deterministic rather than a lookup someone has to maintain --
# `_ch24_verse` derives it, and the anchors below were each checked against the
# chapter's own section headings (v37 = 4th lord, v49 = 5th, v109 = 10th,
# v133 = 12th).
#
# ONLY A SELECTION IS EMITTED, not all 144 cells. Every cell is TRUE of some
# chart, so emitting all of them would put 144 rows into the ceiling for no
# gain: the detector's job is to answer the questions asked, and the cells
# below are the ones the education and foreign-residence questions rest on.
# Widening the selection is a one-line table edit, deliberately.

def _ch24_verse(lord: int, house: int) -> str:
    return f"ch24_v{1 + (lord - 1) * 12 + (house - 1)}"


# (lord, house) -> (topic tag, neutral row name)
_CH24_SELECTED: dict[tuple[int, int], tuple[str, str]] = {
    (4, 1): ("vidya", "Learning and property (4th lord in the ascendant)"),
    (4, 4): ("vidya", "Learning and comfort (4th lord in the 4th)"),
    (4, 7): ("vidya", "A high degree of education (4th lord in the 7th)"),
    (5, 1): ("vidya", "Scholarship (5th lord in the ascendant)"),
    (10, 5): ("vidya", "Learning of every branch (10th lord in the 5th)"),
    (12, 1): ("vidya", "Learning obstructed (12th lord in the ascendant)"),
    (12, 5): ("vidya", "Learning obstructed (12th lord in the 5th)"),
    (12, 7): ("vidya", "Learning obstructed (12th lord in the 7th)"),
    (6, 10): ("videsha", "Happiness in foreign countries (6th lord in the 10th)"),
    (11, 6): ("videsha", "Residence in foreign places (11th lord in the 6th)"),
    (11, 12): ("videsha", "Association with foreigners (11th lord in the 12th)"),
}


def _ch24_rules(facts, lords):
    out = []
    for (lord, house), (topic, name) in sorted(_CH24_SELECTED.items()):
        actual = _lord_house(lords, lord)
        g = _lord_graha(lords, lord)
        out.append(_row(f"ch24_l{lord}_h{house}", name,
                        actual == house,
                        f"the {_ordinal(lord)} lord {g} is in the "
                        f"{_ordinal(actual) if actual else 'unknown house'}",
                        [_ch24_verse(lord, house), f"topic={topic}",
                         f"lord={lord}", f"lord_graha={g}", f"lord_house={actual}"]))
    return out


# ---- ch35: NAABHASA (aasraya, dala, aakriti) ----
#
# The seven SANKHYA yogas are already emitted by `_naabhasa_sankhya`. ch35 v17
# closes the family with a suppression rule that rule does not honour:
# "None of these seven yogas will be operable, if another Nabhasa yoga
# explained earlier is derivable." The suppression row below states the
# condition explicitly rather than silently rewriting the sankhya row -- the
# sankhya row's own fired flag is left alone (changing it would move a verdict
# that test_rules.py and the oracle fixtures both assert), and the gate can
# read the suppression from this row's evidence.

def _aasraya(facts):
    """ch35 v7. All seven grahas in signs of one mode."""
    out = []
    hm = _graha_houses(facts)
    modes = {g: _sign_mode(_sign_of(facts, g)) for g in _GRAHAS}
    known = [m for m in modes.values() if m is not None]
    all_known = len(known) == len(_GRAHAS)
    for rid, name, mode in (("naabhasa_rajju", "Rajju", _MOVABLE_MODE),
                            ("naabhasa_musala", "Musala", _FIXED_MODE),
                            ("naabhasa_nala", "Nala", _DUAL_MODE)):
        out.append(_row(rid, name,
                        all_known and all(m == mode for m in known),
                        f"the seven grahas' sign modes are "
                        f"{ {g: m for g, m in modes.items()} }",
                        ["ch35_v7", f"required_mode={mode}",
                         f"modes={sorted(set(known))}", f"all_placed={all_known}"]))
    del hm
    return out


def _dala(facts):
    """ch35 v8. Three of the four angles occupied -- by benefics (Maala) or by
    malefics (Sarpa/Bhujanga).

    READING. The sloka says "3 angles occupied by benefics"; it does not say
    which three, nor that the fourth must be empty. Three DISTINCT angles each
    holding at least one such planet is taken as the condition. Recorded here
    because a stricter reading (exactly three, fourth vacant) is defensible and
    would change the verdict on real charts.
    """
    out = []
    ben = {h for h in KENDRA_HOUSES if _benefics_in(facts, {h})}
    mal = {h for h in KENDRA_HOUSES if _malefics_in(facts, {h})}
    out.append(_row("naabhasa_maala", "Maala", len(ben) >= 3,
                    f"angles holding a benefic: {sorted(ben) or 'none'}",
                    ["ch35_v8", "reading=three_distinct_angles_each_holding_one",
                     f"benefic_angles={sorted(ben)}"]))
    out.append(_row("naabhasa_sarpa", "Sarpa (Bhujanga)", len(mal) >= 3,
                    f"angles holding a malefic: {sorted(mal) or 'none'}",
                    ["ch35_v8", "reading=three_distinct_angles_each_holding_one",
                     f"malefic_angles={sorted(mal)}"]))
    return out


def _house_run(start, length):
    """`length` consecutive houses beginning at `start`, wrapping at 12."""
    return {((start - 1 + i) % 12) + 1 for i in range(length)}


# (rid, display name, sloka, set-of-houses that must contain ALL seven grahas)
_AAKRITI_CONFINED = (
    ("naabhasa_sakata", "Sakata", "ch35_v10", {1, 7}),
    ("naabhasa_vihaga", "Vihaga", "ch35_v10", {4, 10}),
    ("naabhasa_sringataka", "Sringataka", "ch35_v10", {1, 5, 9}),
    ("naabhasa_kamala", "Kamala", "ch35_v12", set(KENDRA_HOUSES)),
    ("naabhasa_yupa", "Yupa", "ch35_v13", _house_run(1, 4)),
    ("naabhasa_sara", "Sara", "ch35_v13", _house_run(4, 4)),
    ("naabhasa_sakthi", "Sakthi", "ch35_v13", _house_run(7, 4)),
    ("naabhasa_danda", "Danda", "ch35_v13", _house_run(10, 4)),
    ("naabhasa_nauka", "Nauka", "ch35_v14", _house_run(1, 7)),
    ("naabhasa_koota", "Koota", "ch35_v14", _house_run(4, 7)),
    ("naabhasa_chatra", "Chatra", "ch35_v14", _house_run(7, 7)),
    ("naabhasa_chapa", "Chapa", "ch35_v14", _house_run(10, 7)),
    ("naabhasa_chakra", "Chakra", "ch35_v15", {1, 3, 5, 7, 9, 11}),
    ("naabhasa_samudra", "Samudra", "ch35_v15", {2, 4, 6, 8, 10, 12}),
)

_GADA_PAIRS = ((1, 4), (4, 7), (7, 10), (10, 1))


def _aakriti(facts):
    """ch35 vv.9-15. Every one of these reads "ALL the planets", so each row
    requires the seven grahas to be PLACED and CONFINED to the named houses --
    not merely present in them. A rule that fired on partial occupancy would
    fire on nearly every chart."""
    out = []
    hm = _graha_houses(facts)
    complete = _all_seven_placed(hm)
    occ = set(hm.values())

    def confined(houses):
        return complete and occ <= set(houses)

    # v9: two SUCCESSIVE angles.
    gada = [p for p in _GADA_PAIRS if confined(p)]
    out.append(_row("naabhasa_gada", "Gada", bool(gada),
                    f"the seven grahas stand in houses {sorted(occ) or 'unknown'}",
                    ["ch35_v9", f"matching_angle_pairs={gada}",
                     f"occupied_houses={sorted(occ)}", f"all_placed={complete}"]))

    for rid, name, sloka, houses in _AAKRITI_CONFINED:
        out.append(_row(rid, name, confined(houses),
                        f"the seven grahas stand in houses {sorted(occ) or 'unknown'}; "
                        f"this yoga needs them confined to {sorted(houses)}",
                        [sloka, f"required_houses={sorted(houses)}",
                         f"occupied_houses={sorted(occ)}", f"all_placed={complete}"]))

    # v11: Hala -- all seven in one of the three trine-sets that exclude the
    # angles.
    hala_sets = ({2, 6, 10}, {3, 7, 11}, {4, 8, 12})
    hala = [sorted(s) for s in hala_sets if confined(s)]
    out.append(_row("naabhasa_hala", "Hala", bool(hala),
                    f"the seven grahas stand in houses {sorted(occ) or 'unknown'}",
                    ["ch35_v11", f"matching_sets={hala}", f"occupied_houses={sorted(occ)}",
                     f"all_placed={complete}"]))

    # v12: Vaapi -- all seven outside the angles, i.e. wholly in the succedent
    # houses or wholly in the cadent ones. The translation's "all the cadent
    # houses or all the succedent houses" is read as EITHER set, not both.
    vaapi = confined(_PANAPHARA) or confined(_APOKLIMA)
    out.append(_row("naabhasa_vaapi", "Vaapi", vaapi,
                    f"the seven grahas stand in houses {sorted(occ) or 'unknown'}",
                    ["ch35_v12", f"panaphara={sorted(_PANAPHARA)}",
                     f"apoklima={sorted(_APOKLIMA)}", f"occupied_houses={sorted(occ)}",
                     f"all_placed={complete}"]))

    # v11: Vajra and Yava.
    # READING, AND A DIVERGENCE FROM THE ENGLISH. R. Santhanam renders Vajra as
    # "all benefics in the ascendant and the 7th OR all malefics in the 4th and
    # 10th". Taken literally that arm alone fires on any chart with Jupiter and
    # Venus in the 1st/7th, whatever the other five grahas do -- which would
    # make Vajra near-universal and is not what an aakriti ("shape") yoga can
    # mean: every neighbouring verse in the family says "all the planets".
    # BOTH arms are therefore required AND the seven grahas must be confined to
    # the angles. This is the stricter reading; it is recorded, not silent.
    ben_h = {h for g, h in hm.items() if _is_benefic(facts, g)}
    mal_h = {h for g, h in hm.items() if not _is_benefic(facts, g)}
    in_kendras = confined(KENDRA_HOUSES)
    out.append(_row("naabhasa_vajra", "Vajra",
                    in_kendras and ben_h <= {1, 7} and mal_h <= {4, 10}
                    and bool(ben_h) and bool(mal_h),
                    f"benefics stand in houses {sorted(ben_h) or 'none'} and malefics in "
                    f"{sorted(mal_h) or 'none'}",
                    ["ch35_v11", "reading=both_arms_required_and_all_seven_in_angles",
                     f"benefic_houses={sorted(ben_h)}", f"malefic_houses={sorted(mal_h)}",
                     f"all_in_angles={in_kendras}"]))
    out.append(_row("naabhasa_yava", "Yava",
                    in_kendras and ben_h <= {4, 10} and mal_h <= {1, 7}
                    and bool(ben_h) and bool(mal_h),
                    f"benefics stand in houses {sorted(ben_h) or 'none'} and malefics in "
                    f"{sorted(mal_h) or 'none'}",
                    ["ch35_v11", "reading=both_arms_required_and_all_seven_in_angles",
                     f"benefic_houses={sorted(ben_h)}", f"malefic_houses={sorted(mal_h)}",
                     f"all_in_angles={in_kendras}"]))
    return out


def _naabhasa_sankhya_suppression(facts, others):
    """ch35 v17: the seven sankhya yogas are inoperable when any other Naabhasa
    yoga is derivable. Emitted as its own row so the suppression is VISIBLE --
    the sankhya row keeps its own verdict and this row states whether that
    verdict counts."""
    blockers = [r["id"] for r in others if r["fired"]]
    return _row("naabhasa_sankhya_suppressed",
                "Sankhya yogas suppressed (another Naabhasa yoga is derivable)",
                bool(blockers),
                f"other Naabhasa yogas holding: {blockers or 'none'}",
                ["ch35_v17", f"blocking_yogas={blockers}"])


def _detect_naabhasa(facts: dict) -> list[dict]:
    others = _aasraya(facts) + _dala(facts) + _aakriti(facts)
    return others + [_naabhasa_sankhya_suppression(facts, others)]


# ---- ch37 / ch38: LUNAR AND SOLAR YOGAS ----
#
# `_sunaphaa`, `_anaphaa`, `_vesi` and `_adhi` already exist above, written
# from the PVR spec. The rows below complete both families from BPHS itself:
# Durudhara and Kemadruma close the lunar set, Vosi and Ubhayachari the solar
# set. Each cites its sloka; the four existing rows do not, and are NOT
# retrofitted here (see the section header).

def _lunar_solar_rules(facts):
    out = []

    moon_2 = _houses_from(facts, "Moon", (2,)).get(2)
    moon_12 = _houses_from(facts, "Moon", (12,)).get(12)
    occ_m2 = _occupants(facts, moon_2, exclude=("Sun", "Moon")) if moon_2 else []
    occ_m12 = _occupants(facts, moon_12, exclude=("Sun", "Moon")) if moon_12 else []

    # ch37 v7: Durudhara -- both the 2nd and the 12th from the Moon occupied by
    # a planet other than the Sun.
    out.append(_row("durudhara", "Durudhara",
                    bool(occ_m2) and bool(occ_m12),
                    f"{occ_m2 or 'nothing'} in {moon_2}, the 2nd from the Moon; "
                    f"{occ_m12 or 'nothing'} in {moon_12}, the 12th from the Moon",
                    ["ch37_v7", f"2nd_from_Moon={moon_2}", f"occupants_2nd={occ_m2}",
                     f"12th_from_Moon={moon_12}", f"occupants_12th={occ_m12}"]))

    # ch37 v11: Kemadruma -- excluding the Sun, no planet WITH the Moon, nor in
    # the 2nd or 12th from it, nor in an angle from the ascendant. All four
    # clauses, so this is the strict form the sloka gives, not the loose
    # two-clause version many later texts use.
    moon_sign = _sign_of(facts, "Moon")
    with_moon = _occupants(facts, moon_sign, exclude=("Sun", "Moon")) if moon_sign else []
    in_kendra = [g for g, h in _graha_houses(facts).items()
                 if g not in ("Sun", "Moon") and h in KENDRA_HOUSES]
    known = bool(moon_sign) and bool(moon_2) and bool(moon_12)
    out.append(_row("kemadruma", "Kemadruma",
                    known and not (with_moon or occ_m2 or occ_m12 or in_kendra),
                    f"with the Moon: {with_moon or 'nothing'}; 2nd from it: "
                    f"{occ_m2 or 'nothing'}; 12th from it: {occ_m12 or 'nothing'}; "
                    f"in an angle from the ascendant: {in_kendra or 'nothing'}",
                    ["ch37_v11", f"with_Moon={with_moon}", f"occupants_2nd={occ_m2}",
                     f"occupants_12th={occ_m12}", f"in_kendra={in_kendra}"]))

    # ch37 v6: benefics in the upachayas from the Moon, graded by how many.
    up_signs = _houses_from(facts, "Moon", _UPACHAYA)
    up_benefics = sorted({g for off, s in up_signs.items()
                          for g in _occupants(facts, s)
                          if g != "Moon" and _is_benefic(facts, g)})
    out.append(_row("chandra_dhana_upachaya",
                    "Wealth from the Moon (benefics in the 3rd, 6th, 10th or 11th from it)",
                    bool(up_benefics),
                    f"benefics in the upachayas from the Moon: {up_benefics or 'none'} "
                    f"({len(up_benefics)} of 3 -- the sloka grades the effect by this count)",
                    ["ch37_v6", f"benefic_count={len(up_benefics)}",
                     f"benefics={up_benefics}",
                     f"upachaya_signs={[up_signs.get(o) for o in _UPACHAYA]}"]))

    # ch38 v1: Vosi -- a planet other than the Moon in the 12th from the Sun.
    # Ubhayachari -- both the 2nd and the 12th occupied. Vesi (the 2nd alone)
    # is already emitted by `_vesi`.
    sun_2 = _houses_from(facts, "Sun", (2,)).get(2)
    sun_12 = _houses_from(facts, "Sun", (12,)).get(12)
    occ_s2 = _occupants(facts, sun_2, exclude=("Moon", "Sun")) if sun_2 else []
    occ_s12 = _occupants(facts, sun_12, exclude=("Moon", "Sun")) if sun_12 else []
    out.append(_row("vosi", "Vosi", bool(occ_s12),
                    f"{occ_s12 or 'nothing but possibly the Moon'} in {sun_12}, the 12th "
                    f"from the Sun",
                    ["ch38_v1", f"12th_from_Sun={sun_12}", f"occupants={occ_s12}"]))
    out.append(_row("ubhayachari", "Ubhayachari",
                    bool(occ_s2) and bool(occ_s12),
                    f"{occ_s2 or 'nothing'} in {sun_2}, the 2nd from the Sun; "
                    f"{occ_s12 or 'nothing'} in {sun_12}, the 12th from the Sun",
                    ["ch38_v1", f"2nd_from_Sun={sun_2}", f"occupants_2nd={occ_s2}",
                     f"12th_from_Sun={sun_12}", f"occupants_12th={occ_s12}"]))
    return out


def _detect_tier23(facts: dict) -> list[dict]:
    lords = _house_lords(facts)
    if not lords:
        return []
    return [v for v in (_ayush_rules(facts, lords)
                        + _sukha_rules(facts, lords)
                        + _ch24_rules(facts, lords)
                        + _detect_naabhasa(facts)
                        + _lunar_solar_rules(facts)) if v]
