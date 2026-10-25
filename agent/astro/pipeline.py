"""

================================================================
PATH B IS THE PRODUCT (S129 cutover). THIS MODULE IS LIVE.

frontend/app.py:37 imports answer_question from
agent.astro.pipeline. A change here SHIPS TO USERS.
Path A (agent/infra/orchestrator) is retained, tested and intact
as the revert target, but is wired to no UI.
Read docs/ANSWER_PATHS.md before editing or proposing work here.

SUPERSEDES the S128 banner that stood here and said this module
had no non-test caller and shipped nothing. That was true at S128
and false from S129 on.
================================================================

Astro Agent -- FULL ANSWER PIPELINE.

  question -> plan (Stage 1) -> unit+domain selection (Stage 2)
           -> payload build (Stage 3) -> Interpreter/GPT-5 (Stage 4)
           -> Silence gate (Stage 5a) -> answer.

The Calculator (Stage 3.5) supplies the FACT BLOCK the Interpreter reads.
Today that block is the chart's ascendant, its lord->house map, and per-graha
planet positions (house + sign only, S129b). It widens by RESTATING more of
`agent/chart_calculator.py::calculate_chart()` -- never by implementing
`agent/calculations/core/chart_d1.py`, which is a permanent deliberate stub
(P-022). The LLM never computes a chart fact.

Dependency-injected `llm` (planner) and `interpreter_llm` (interpreter) so the
whole chain is testable with stubs and never calls the API in CI.
Python 3.11.
"""
from __future__ import annotations

import os
import time
from typing import Callable, Optional

from agent.astro import planner
from agent.astro import capability_gate
from agent.astro import interpreter as _interp
from agent.astro import silence_gate
from agent.astro import verifiability
from agent.astro import composer as _composer
from agent.astro import payload_builder
from agent.astro import timing_ranker
from agent.astro import house_roles
from agent.astro import capability_registry

PIPELINE_VERSION = "pipeline-1.2"


_ORDINAL_SUFFIX = {1: 'st', 2: 'nd', 3: 'rd'}


def _ordinal(n: int) -> str:
    """1 -> 1st. 11/12/13 take "th", which is why this is not n % 10 alone."""
    if 11 <= n % 100 <= 13:
        return str(n) + "th"
    return str(n) + _ORDINAL_SUFFIX.get(n % 10, "th")


def _transit_note(t: dict) -> str:
    """One antardasha's transit_facts entry -> a compact inline clause, e.g.
    "Sagittarius, house 1 from lagna, house 2 from Moon, Sade Sati SETTING
    (retrograde)". `t` is one value from build_transit_facts()'s "periods" dict
    -- see that module for the shape. Malformed keys are rendered as "?" rather
    than raising, since a transit annotation is corroborating context, never a
    fact worth failing the whole block over."""
    sign = t.get("saturn_sign", "?")
    hl = t.get("saturn_house_from_lagna", "?")
    hm = t.get("saturn_house_from_moon", "?")
    phase = t.get("sade_sati_phase", "NONE")
    note = f"{sign}, house {hl} from lagna, house {hm} from Moon"
    if phase and phase != "NONE":
        note += f", Sade Sati {phase}"
    if t.get("saturn_retrograde"):
        note += " (retrograde)"
    return note


def _fact_block(chart_facts: dict) -> str:
    """Render the chart facts the Interpreter is allowed to reason from.

    GROWTH CONTRACT: every class of fact rendered here MUST have a matching key
    in `capability_gate.FACT_BLOCK_PROVIDES`, added in the SAME change.
    `tests/astro/test_capability_gate.py` pins the two together and fails if
    they drift -- that pin is what stops the gate declining a question the
    block can now answer, or the reverse.
    """
    lord_house, asc = payload_builder.parse_lord_house_map(chart_facts)
    lines = ["CHART FACTS (the only chart facts you may use):",
             f"Ascendant sign: {asc}"]

    # House lords. The named form is used when chart_facts carries `house_lords`
    # (S130); the bare form is the pre-S130 shape and stays byte-identical for
    # it, so a legacy chart_facts dict renders exactly as it always did.
    house_lords = chart_facts.get("house_lords") or {}
    for h in range(1, 13):
        hl = house_lords.get(h) or house_lords.get(str(h))
        if hl and hl.get("lord"):
            sign = f" ({hl['sign']})" if hl.get("sign") else ""
            lines.append(f"House {h}{sign}: its lord is {hl['lord']}, "
                         f"and {hl['lord']} sits in house {lord_house[h]}")
        else:
            lines.append(f"House {h}: its lord sits in house {lord_house[h]}")

    # GROUPINGS (S130). Pure regrouping of the twelve lines above -- no new
    # fact, no doctrine, no kendra/trikona labelling (that vocabulary lives in
    # the corpus, not here). It exists because the Interpreter was emitting
    # "the 9th lord in the 4th" and "the 10th lord in the 4th" as unrelated
    # claims across twelve rows and never noticing they name one house. Stating
    # the grouping is Working Style #23: feed the computed term, never ask the
    # model to bridge two representations.
    shared: dict[int, list[int]] = {}
    for h in range(1, 13):
        shared.setdefault(lord_house[h], []).append(h)
    together = [(dest, hs) for dest, hs in sorted(shared.items()) if len(hs) > 1]
    if together:
        lines.append("")
        lines.append("House lords that share a house (they are together there):")
        for dest, hs in together:
            names = ", ".join(_ordinal(h) for h in hs)
            lines.append(f"  the lords of houses {names} are all in house {dest}")

    if house_lords:
        rules: dict[str, list[int]] = {}
        for h in range(1, 13):
            hl = house_lords.get(h) or house_lords.get(str(h))
            if hl and hl.get("lord"):
                rules.setdefault(hl["lord"], []).append(h)
        multi = [(p_, hs) for p_, hs in rules.items() if len(hs) > 1]
        if multi:
            lines.append("")
            lines.append("Planets that rule more than one house:")
            for p_, hs in multi:
                lines.append(f"  {p_} rules houses "
                             + " and ".join(str(h) for h in sorted(hs)))

    # Planet positions (S129). Rendered in the classical Navagraha order that
    # chart_facts fixes, so the block is byte-stable across runs. Absent for a
    # chart_facts dict built from `fact_block_text` -- that legacy shape has no
    # planet data, and its absence is honest, not an error.
    # ASPECTS + CONJUNCTIONS (S130). Restated from calculate_chart(); see
    # chart_facts._read_aspects. `aspected_by` is the half that matters most --
    # it is what answers "is this placement afflicted", a check a benchmark
    # answer for this chart got wrong by eye.
    aspects = chart_facts.get("aspects") or {}
    conj = aspects.get("conjunctions") or []
    by_planet = aspects.get("aspects_by_planet") or {}
    aspected_by = aspects.get("aspected_by") or {}
    if conj or by_planet or aspected_by:
        lines.append("")
        lines.append("Aspects and conjunctions:")
    for c in conj:
        lines.append(f"  {c}")
    for planet, houses in by_planet.items():
        if houses:
            lines.append(f"  {planet} aspects houses "
                         + ", ".join(str(h) for h in houses))
    for planet, sources in aspected_by.items():
        if sources:
            lines.append(f"  {planet} is aspected by " + ", ".join(sources))

    # MUTUAL aspects. Same regrouping justification as the lord groupings
    # above: a one-way aspect and a mutual one carry different doctrinal
    # weight, and asking the model to cross-reference two lists to tell them
    # apart is the bridging failure Working Style #23 forbids. Stated here so
    # it cannot be guessed at.
    mutual = set()
    for planet, sources in aspected_by.items():
        for src in sources:
            if planet in (aspected_by.get(src) or []):
                mutual.add(tuple(sorted((planet, src))))
    if mutual:
        lines.append("")
        lines.append("Planets that aspect EACH OTHER (mutual, not one-way):")
        for a, b in sorted(mutual):
            lines.append(f"  {a} and {b}")
    positions = chart_facts.get("planet_positions") or {}
    if positions:
        lines.append("")
        for planet, pos in positions.items():
            standing = pos.get("dignity")
            mark = f" -- {standing.lower()} there" if standing else ""
            lines.append(
                f"{planet} is in house {pos['house']} ({pos['sign']}){mark}.")

        # DISPOSITOR CHAIN (S130). The lord of the SIGN a planet occupies.
        # Derived only from (sign, lord) pairs already present in house_lords
        # -- no lord table is introduced here. Stated because Neecha Bhanga
        # is a two-step relation (debilitated planet -> its dispositor's own
        # standing) and step two is otherwise a lookup the model has to
        # perform across two separate blocks.
        sign_lord = {}
        for h in range(1, 13):
            hl = house_lords.get(h) or house_lords.get(str(h))
            if hl and hl.get("sign") and hl.get("lord"):
                sign_lord[hl["sign"]] = hl["lord"]
        chain = []
        for planet, pos in positions.items():
            lord = sign_lord.get(pos.get("sign"))
            if not lord or lord == planet:
                continue
            lord_pos = positions.get(lord) or {}
            lord_sign = lord_pos.get("sign")
            lord_dig = lord_pos.get("dignity")
            if not lord_sign:
                continue
            tail = f" -- {lord_dig.lower()} there" if lord_dig else ""
            chain.append(f"  {planet} is in {pos['sign']}, whose lord is {lord}; "
                         f"{lord} is in {lord_sign}{tail}")
        if chain:
            lines.append("")
            lines.append("Each planet's sign-lord (its dispositor):")
            lines.extend(chain)

    # NAVAMSA / D9 (S130). Restated from agent/calculations/vargas/navamsa.py,
    # oracle-clean on 4/4 reference charts since S20 and unwired until now.
    # Carried because a debilitated planet exalted in D9 is one of the
    # classical Neecha Bhanga routes, and it is the ONLY route left open for
    # this chart once the dispositor tests fail.
    nav = chart_facts.get("navamsa") or {}
    nav_places = nav.get("placements") or {}
    if nav_places:
        lines.append("")
        d9l = nav.get("d9_lagna_sign")
        lines.append("In the Navamsa (D9) divisional chart"
                     + (f", whose ascendant is {d9l}:" if d9l else ":"))
        for planet, row in nav_places.items():
            standing = row.get("dignity")
            mark = f" -- {standing.lower()} there" if standing else ""
            lines.append(f"  {planet} is in {row['sign']} "
                         f"(D9 house {row['house']}){mark}")

    # YOGAS (S133). Computed deterministically from the facts above by
    # agent/calculations/yogas (composed onto chart_facts by the caller, like
    # the D9 block). A fired yoga is a CHART FACT, and so is a not-fired ruling
    # (S131) -- the "what I am ruling out" half the pipeline could not state
    # before. The reason strings carry the placements behind each verdict; the
    # interpreter grounds their MEANING in the retrieved chapters, it does not
    # invent it. GROWTH CONTRACT: "yogas" is in capability_gate.FACT_BLOCK_PROVIDES.
    yogas = chart_facts.get("yogas") or {}
    fired = yogas.get("fired") or []
    ruled_out = yogas.get("ruled_out") or []
    if fired:
        lines.append("")
        lines.append("Yogas PRESENT in the chart (computed from the facts above):")
        for y in fired:
            name = y.get("name") or y.get("id")
            reason = y.get("reason")
            lines.append(f"  {name}" + (f" -- {reason}" if reason else ""))
    if ruled_out:
        lines.append("")
        lines.append("Yogas CHECKED and NOT present in the chart:")
        lines.append("  " + "; ".join(
            (y.get("name") or y.get("id")) for y in ruled_out))

    # SHADBALA (point 1 wiring). Six-fold planetary strength, aggregated and
    # oracle-validated in agent/calculations/strength (Drik Bala 28/28 vs JHora
    # v8), composed onto chart_facts by the caller like yogas/transits. Shadbala
    # is a declared `unfittable` concept (predicates.py): no verification
    # predicate, no gate Requirement -- additive strength context.
    # GROWTH CONTRACT: "shadbala" is in capability_gate.FACT_BLOCK_PROVIDES.
    sb = chart_facts.get("shadbala") or {}
    sb_planets = sb.get("planets") or {}
    if sb_planets:
        lines.append("")
        lines.append("Planetary strength (Shadbala), in Rupas with the ratio to "
                     "the BPHS minimum (1.0 = exactly meets the requirement):")
        for _p, _row in sorted(sb_planets.items(), key=lambda kv: kv[1]["rank"]):
            _meets = "meets" if _row.get("meets_minimum") else "below"
            lines.append(f"  {_p}: {_row['rupa']} Rupas, {_row['ratio']}x the "
                         f"minimum, rank {_row['rank']}/7 ({_meets} the BPHS minimum)")
        _strong = sb.get("strongest"); _weak = sb.get("weakest")
        if _strong and _weak:
            lines.append(f"Strongest: {_strong}. Weakest: {_weak}.")
        _cav = sb.get("caveat")
        if _cav:
            lines.append(_cav)

    # ASHTAKAVARGA (point 1 wiring). Sarvashtakavarga (SAV) bindus per house +
    # each planet's own Bhinnashtakavarga (BAV), aggregated and oracle-validated
    # in agent/calculations/ashtakavarga (48/48 houses vs AstroSage, S54),
    # composed onto chart_facts by the caller like shadbala/yogas/transits.
    # Bindu counts carry no verification predicate (a numeric strength, like
    # shadbala) -> unfittable; no gate Requirement. GROWTH CONTRACT:
    # "ashtakavarga" is in capability_gate.FACT_BLOCK_PROVIDES.
    av = chart_facts.get("ashtakavarga") or {}
    sav_h = av.get("sav_by_house") or {}
    if sav_h:
        lines.append("")
        _avg = av.get("average_per_house")
        lines.append("Sarvashtakavarga (SAV), total bindus per house (whole-chart "
                     f"total 337; average per house ~{_avg}; more bindus = a "
                     "stronger house):")
        for _h in range(1, 13):
            if _h in sav_h:
                lines.append(f"  House {_h}: {sav_h[_h]} bindus")
        _sh = av.get("strongest_house"); _wh = av.get("weakest_house")
        if _sh and _wh:
            lines.append(f"Strongest house: {_sh} ({sav_h[_sh]} bindus). "
                         f"Weakest house: {_wh} ({sav_h[_wh]} bindus).")
        _pbav = av.get("planet_bav_in_sign") or {}
        if _pbav:
            _parts = ", ".join(f"{_p} {_pbav[_p]}" for _p in
                               ("Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn")
                               if _p in _pbav)
            lines.append("Each planet's own BAV bindus in the sign it occupies "
                         f"(0-8): {_parts}.")

    # JAIMINI (point 1 wiring). Chara karakas (PVR Ch.8, 8-karaka scheme:
    # the planet signifying each life role, AK soul .. DK spouse) + Arudha
    # Lagna (self-image) and Upapada Lagna (marriage/spouse), computed in
    # agent/calculations/jaimini and composed by the caller like the other
    # fact classes. Jaimini concepts carry no verification predicate
    # (Karakamsa/Arudha are `unfittable`); no gate Requirement. GROWTH
    # CONTRACT: "jaimini" is in capability_gate.FACT_BLOCK_PROVIDES.
    jai = chart_facts.get("jaimini") or {}
    kk = jai.get("chara_karakas") or {}
    if kk:
        _kg = {"AK": "soul/self", "AmK": "career/mind", "BK": "siblings",
               "MK": "mother", "PiK": "father", "PK": "children",
               "GK": "obstacles/cousins", "DK": "spouse"}
        lines.append("")
        lines.append("Jaimini chara karakas (the planet signifying each role, "
                     "assigned by degree):")
        for _ab in ("AK", "AmK", "BK", "MK", "PiK", "PK", "GK", "DK"):
            if _ab in kk:
                lines.append(f"  {_ab} ({_kg[_ab]}): {kk[_ab]}")
    _al = jai.get("arudha_lagna"); _ul = jai.get("upapada_lagna")
    if _al:
        lines.append(f"Arudha Lagna (AL -- how the person's life and image are "
                     f"perceived by others): {_al}.")
    if _ul:
        lines.append(f"Upapada Lagna (UL -- the marriage/spouse significator): {_ul}.")
    _km = jai.get("karakamsa")
    if _km:
        lines.append(f"Karakamsa (PVR Ch.7: the navamsa sign of the Atmakaraka "
                     f"{_km['atmakaraka']} -- the soul's reference point for the "
                     f"inner self, read in D9): {_km['sign']}.")
    _bp = jai.get("bhava_padas")
    if _bp:
        _ar_matter = {
            1: "self-image", 2: "wealth-image", 3: "effort/siblings-image",
            4: "home/property-image", 5: "creativity/children-image",
            6: "work/service-image", 7: "partnership-image",
            8: "transformation-image", 9: "fortune/dharma-image",
            10: "career/public-image", 11: "gains-image", 12: "loss/expense-image",
        }
        _bp_parts = "; ".join(f"A{_h} ({_ar_matter[_h]}): {_bp[_h]}"
                              for _h in range(1, 13) if _h in _bp)
        lines.append(
            "Bhava Arudhas (Jaimini -- the sign in which each house's matters are "
            "PERCEIVED by the world, distinct from the house itself; A1 is the "
            "Arudha Lagna, A12 the Upapada): " + _bp_parts + ".")

    # DIVISIONAL CHARTS (point 2; S153 widened to the full Shodashvarga minus
    # D1/D9). From the oracle-validated engine (agent/calculations/vargas/
    # divisional, all 14 rules x 4 charts) and composed by the caller like
    # navamsa/shadbala/jaimini. Which vargas appear is owned in ONE place --
    # divisional_facts._SURFACED; this render iterates whatever the composer
    # produced, with NO second hard-coded code list here (P-030). Varga
    # placements are a different reference frame than the D1 predicates ->
    # unfittable; no gate Requirement. GROWTH CONTRACT: "divisional" is in
    # capability_gate.FACT_BLOCK_PROVIDES.
    dv = chart_facts.get("divisional") or {}
    if dv:
        lines.append("")
        lines.append("Divisional charts (vargas) for the relevant life areas -- "
                     "each planet's sign and house FROM THAT VARGA's own lagna. "
                     "Weigh the varga relevant to the question, not every one:")
        for _code, _v in dv.items():
            if not _v:
                continue
            _pl = _v.get("placements") or {}
            _parts = ", ".join(
                f"{_p} {_pl[_p]['sign']}/h{_pl[_p]['house']}"
                for _p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
                           "Saturn", "Rahu", "Ketu") if _p in _pl)
            lines.append(f"  {_v['name']} ({_code}, {_v['domain']}) -- lagna "
                         f"{_v['lagna']}: {_parts}")

    # FRIENDSHIP (S152). Five-fold compound planetary friendship (Pancha-dha
    # maitri, PVR), composed by agent.astro.friendship_facts.build_friendship_facts
    # from each planet's natal sign. Directional, 7 classical planets (nodes
    # excluded by doctrine). Guarded on presence -> a facts dict without it renders
    # byte-identically (the legacy-dict pin). GROWTH CONTRACT: "friendship" is in
    # capability_gate.FACT_BLOCK_PROVIDES.
    fr = chart_facts.get("friendship") or {}
    fr_bp = fr.get("by_planet") or {}
    if fr_bp:
        fr_sg = fr.get("signs") or {}
        _FR_GLOSS = {"Adhimitra": "great friend", "Mitra": "friend",
                     "Sama": "neutral", "Satru": "enemy", "Adhisatru": "bitter enemy"}
        lines.append("")
        lines.append(
            "Five-fold planetary friendship (Pancha-dha maitri -- natural + "
            "temporary combined, PVR) -- COMPUTED, each planet's relation TOWARD "
            "the others (directional; 7 classical planets, nodes excluded by "
            "doctrine):")
        for _p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
            _b = fr_bp.get(_p)
            if not _b:
                continue
            # Render ALL five tiers, empties as "none" -- never drop an empty
            # tier. Dropping it (the pre-S153 behaviour) left a gap between the
            # tiers shown: on a chart whose "friend" (Mitra) tier was empty, the
            # interpreter saw only great-friend / neutral / enemy, and when asked
            # a friend-or-enemy question it back-filled the missing "friend" slot
            # out of the NEUTRAL planets -- reporting computed-neutral planets as
            # friends/enemies (live-run fidelity miss). An explicit "friend: none"
            # removes that vacuum so neutral reads as its own closed category.
            _parts = [
                f"{_FR_GLOSS[_lab]}: "
                f"{', '.join(_b[_lab]) if _b.get(_lab) else 'none'}"
                for _lab in ("Adhimitra", "Mitra", "Sama", "Satru", "Adhisatru")
            ]
            lines.append(f"  {_p} (in {fr_sg.get(_p, '?')}) -- " + "; ".join(_parts))

    # YOGINI DASHA (S152). Yogini Mahadasha sequence, composed by
    # agent.astro.yogini_facts.build_yogini_facts (MD only; the engine has no
    # antardasha). Periods are stored as dated intervals; past/current/future is
    # resolved HERE, at answer time, against today's date (ISO-string compare, so
    # this stays swisseph-free), never baked into the cached fact. Guarded on
    # presence. GROWTH CONTRACT: "yogini" is in capability_gate.FACT_BLOCK_PROVIDES.
    yog = chart_facts.get("yogini") or {}
    yog_mds = yog.get("mahadashas") or []
    if yog_mds:
        import datetime as _dt
        _today = _dt.date.today().isoformat()
        lines.append("")
        lines.append(
            "Yogini dasha (36-year cycle, 8 Yoginis) -- COMPUTED major periods "
            "(Mahadasha only). For a 'when' question, lead with the CURRENT and "
            "upcoming periods; a past period only on a retrospective question:")
        for _p in yog_mds:
            if _p["end"] < _today:
                _ph = "past"
            elif _p["start"] <= _today < _p["end"]:
                _ph = "CURRENT"
            else:
                _ph = "future"
            lines.append(f"  {_p['lord']} ({_p['yogini']}) {_p['start']} to "
                         f"{_p['end']} [{_ph}]")

    # NARAYANA DASA (S153). Jaimini rasi dasa (PVR Ch.18), composed by
    # agent.astro.narayana_facts.build_narayana_facts (MD only, two cycles).
    # Dated intervals; past/current/future resolved HERE at answer time against
    # today (ISO-string compare, swisseph-free), never baked into the cached
    # fact. Guarded on presence. GROWTH CONTRACT: "narayana" is in
    # capability_gate.FACT_BLOCK_PROVIDES.
    nar = chart_facts.get("narayana") or {}
    nar_mds = nar.get("mahadashas") or []
    if nar_mds:
        import datetime as _dtn
        _today_n = _dtn.date.today().isoformat()
        lines.append("")
        lines.append(
            f"Narayana dasa (Jaimini rasi dasa, PVR Ch.18) -- COMPUTED major "
            f"periods from the {nar.get('seed', '?')} seed; each rasi acts as the "
            f"progressed lagna for its period. For a 'when' question, lead with "
            f"the CURRENT and upcoming periods, a past one only on a "
            f"retrospective question. For the CURRENT major period its "
            f"sub-periods (antardasa) are listed too, and the same "
            f"lead-with-current/upcoming rule applies to them:")
        for _p in nar_mds:
            if _p["end"] < _today_n:
                _phn = "past"
            elif _p["start"] <= _today_n < _p["end"]:
                _phn = "CURRENT"
            else:
                _phn = "future"
            lines.append(f"  {_p['rasi']} (lord {_p['lord']}, {_p['years']}y) "
                         f"{_p['start']} to {_p['end']} [{_phn}]")
            # Antardasas only under the CURRENT MD (it spans years, so its 12
            # sub-periods already cover the near future). Guarded on presence.
            if _phn == "CURRENT":
                for _a in _p.get("antardashas") or []:
                    if _a["end"] < _today_n:
                        _pa = "past"
                    elif _a["start"] <= _today_n < _a["end"]:
                        _pa = "CURRENT"
                    else:
                        _pa = "future"
                    lines.append(f"    sub-period {_a['rasi']} {_a['start']} "
                                 f"to {_a['end']} [{_pa}]")

    # ASHTOTTARI DASA (S155). 108-year, 8-lord CONDITIONAL nakshatra dasa,
    # composed by agent.astro.ashtottari_facts.build_ashtottari_facts (MD +
    # proportional AD). Dated intervals; past/current/future resolved HERE at
    # answer time (ISO-string compare, swisseph-free), never baked in. The
    # applicability is SURFACED, not gated -- rendered as the three contested
    # criteria so the interpreter WEIGHTS the dasa, never as a pass/fail. Guarded
    # on presence. GROWTH CONTRACT: "ashtottari" is in FACT_BLOCK_PROVIDES.
    ash = chart_facts.get("ashtottari") or {}
    ash_mds = ash.get("mahadashas") or []
    ash_appl = ash.get("applicability") or {}
    if ash_mds or ash_appl:
        import datetime as _dta
        _today_a = _dta.date.today().isoformat()
        lines.append("")
        lines.append(
            "Ashtottari dasa (108-year, 8-lord CONDITIONAL nakshatra dasa) -- "
            "COMPUTED major periods. Ashtottari is CONDITIONAL: weight it by the "
            "applicability criteria below; do NOT treat it as unconditionally in "
            "force. For a 'when' question lead with the CURRENT and upcoming "
            "periods, a past one only on a retrospective question. The CURRENT "
            "major period's sub-periods (antardasa) are listed too:")
        for _p in ash_mds:
            if _p["end"] < _today_a:
                _pha = "past"
            elif _p["start"] <= _today_a < _p["end"]:
                _pha = "CURRENT"
            else:
                _pha = "future"
            lines.append(f"  {_p['lord']} ({_p['years']}y) {_p['start']} to "
                         f"{_p['end']} [{_pha}]")
            if _pha == "CURRENT":
                for _a in _p.get("antardashas") or []:
                    if _a["end"] < _today_a:
                        _paa = "past"
                    elif _a["start"] <= _today_a < _a["end"]:
                        _paa = "CURRENT"
                    else:
                        _paa = "future"
                    lines.append(f"    sub-period {_a['lord']} {_a['start']} "
                                 f"to {_a['end']} [{_paa}]")
        _crit = ash_appl.get("criteria") or {}
        if _crit:
            lines.append(
                f"  Applicability -- {ash_appl.get('criteria_met', 0)} of "
                f"{ash_appl.get('criteria_evaluated', len(_crit))} classical "
                f"criteria met (contested; these criteria are not equivalent, so "
                f"weight the dasa, do not treat as pass/fail):")

            def _verdict(_c: dict) -> str:
                _a = _c.get("applicable")
                return "MET" if _a is True else ("not met" if _a is False
                                                 else "undetermined")
            _pos = _crit.get("positional")
            if _pos:
                lines.append(
                    f"    positional: {_verdict(_pos)} (lagna lord "
                    f"{_pos.get('lagna_lord')} in house {_pos.get('lagna_lord_house')}; "
                    f"Rahu in house {_pos.get('rahu_house')})")
            _pak = _crit.get("paksha")
            if _pak:
                lines.append(
                    f"    paksha: {_verdict(_pak)} ({_pak.get('paksha')} paksha, "
                    f"{_pak.get('birth_period')} birth)")
            _nak = _crit.get("lagna_nakshatra")
            if _nak:
                lines.append(
                    f"    lagna nakshatra: {_verdict(_nak)} (lagna in "
                    f"{_nak.get('lagna_nakshatra')})")

    # VARSHAPHAL (Tajika annual chart, S156). CALCULATED annual engines -- varsha
    # pravesh + annual D1, Muntha, year-lord (Varshesha), Pancha-vargeeya bala,
    # and the Mudda/Patyayini/Yogini dashas -- validated vs the JHora oracle (see
    # data/default_user/jhora_sulabh_varshaphal.md), no curve-fitting. YEAR-FIXED:
    # describes the ANNUAL chart for the Varsha stamped in "year", distinct from
    # the natal chart; it switches at each solar return. Dashas are dated
    # intervals; current/past/future is resolved HERE at answer time.
    # GROWTH CONTRACT: "varshaphal" is in capability_gate.FACT_BLOCK_PROVIDES.
    # Guarded on presence -> renders byte-identically to before when absent.
    vp = chart_facts.get("varshaphal") or {}
    if vp.get("year"):
        import datetime as _dtv
        _today_v = _dtv.date.today().isoformat()
        al = vp.get("annual_lagna") or {}
        mu = vp.get("muntha") or {}
        yl = vp.get("year_lord") or {}
        lines.append("")
        lines.append(
            f"Varshaphal (Tajika annual chart) for the Varsha year {vp['year']} "
            f"-- CALCULATED, year-fixed. Pravesh {vp.get('pravesh')} to "
            f"{vp.get('pravesh_end')}, cast at {vp.get('cast')}. This is the "
            f"ANNUAL chart (one solar year), distinct from the natal chart: use "
            f"it for questions about this year, the natal chart for lifelong "
            f"themes. Do NOT conflate annual placements with natal ones:")
        lines.append(
            f"  Annual Lagna {al.get('sign')} {al.get('degree')} deg; Muntha in "
            f"{mu.get('sign')} (house {mu.get('house_from_lagna')} from the annual "
            f"Lagna).")
        if yl.get("winner"):
            lines.append(
                f"  Year-lord (Varshesha): {yl['winner']} "
                f"[rule: {yl.get('rule_path')}]. The year-lord colours the whole "
                f"annual chart; weight its condition heavily.")
        _vpos = vp.get("positions") or {}
        if _vpos:
            _vps = ", ".join(f"{_n} {_d.get('sign')} {_d.get('degree')} deg"
                             for _n, _d in _vpos.items())
            lines.append(f"  Annual positions: {_vps}.")
        _pv = vp.get("pancha_vargeeya_bala") or {}
        if _pv:
            _pvs = ", ".join(f"{_n} {_v.get('total')} ({_v.get('band')})"
                             for _n, _v in _pv.items())
            lines.append(
                f"  Pancha-vargeeya bala (annual strength, relative): {_pvs}.")
        _dashas = vp.get("dashas") or {}
        for _dk, _dlabel in (("mudda", "Mudda"), ("patyayini", "Patyayini"),
                             ("yogini", "Yogini")):
            _per = _dashas.get(_dk) or []
            if not _per:
                continue
            lines.append(f"  {_dlabel} dasa (annual; lead with CURRENT/upcoming "
                         f"for a 'when' question):")
            for _q in _per:
                if _q["end"] < _today_v:
                    _phv = "past"
                elif _q["start"] <= _today_v < _q["end"]:
                    _phv = "CURRENT"
                else:
                    _phv = "future"
                _extra = f" ({_q['yogini']})" if _q.get("yogini") else ""
                lines.append(f"    {_q['lord']}{_extra} {_q['start']} to "
                             f"{_q['end']} [{_phv}]")

    # LUCKY / UNLUCKY WEEKDAYS (S147). CALCULATED from the chart's own house
    # lordships by agent.astro.lucky_facts.build_lucky_facts -- a trikona (1/5/9)
    # lord's weekday is favourable, a dusthana-only (6/8/12) lord's weekday is to
    # be avoided (trikona dominates). Personalised, computed, never from the PDF.
    # Houses are carried so the interpreter can GROUND the verdict, not assert it.
    # GROWTH CONTRACT: "lucky_unlucky" is in capability_gate.FACT_BLOCK_PROVIDES.
    # Guarded on presence -> renders byte-identically to before when absent.
    lk = chart_facts.get("lucky_unlucky") or {}
    if lk and (lk.get("favourable_days") or lk.get("avoid_days")):
        wd = lk.get("weekdays") or {}

        def _lk_fmt(_day: str) -> str:
            _e = wd.get(_day) or {}
            _h = ", ".join(str(h) for h in _e.get("houses_ruled", []))
            return f"{_day} (ruled by {_e.get('lord')}, lord of house(s) {_h})"

        lines.append("")
        lines.append(
            "Lucky / unlucky weekdays -- COMPUTED from this chart's house "
            "lordships (functional benefic/malefic by trikona vs dusthana "
            "lordship; trikona dominates), NOT from any external source:")
        _fav = lk.get("favourable_days") or []
        _avd = lk.get("avoid_days") or []
        if _fav:
            lines.append("  Favourable: " + "; ".join(_lk_fmt(d) for d in _fav))
        if _avd:
            lines.append("  To avoid: " + "; ".join(_lk_fmt(d) for d in _avd))

    # MUHURTA (S147). Generic electional favourability over the planner's horizon,
    # composed in answer_question (plan- and time-dependent) and attached as
    # chart_facts["muhurta"]. GROWTH CONTRACT: "muhurta" is in
    # capability_gate.FACT_BLOCK_PROVIDES. Guarded on presence -> a chart_facts
    # without it renders byte-identically to before (the legacy-dict pin).
    mu = chart_facts.get("muhurta") or {}
    if mu:
        _srch = mu.get("searched") or {}
        lines.append("")
        lines.append(
            "Muhurta (electional timing) -- COMPUTED, GENERIC auspiciousness only "
            "(Chandrabala + Tarabala + Panchaka + panchanga shuddhi), NOT "
            f"event-specific. Searched {_srch.get('start')} to {_srch.get('end')}. "
            "EXPLAIN these computed windows; do NOT re-rank or invent dates. "
            "TIER_1 = clearly auspicious; TIER_2 = acceptable but weaker.")
        if mu.get("none_found"):
            lines.append(
                "  No auspicious window (TIER_1 or TIER_2) was found in that span. "
                "State this plainly -- do NOT manufacture a date.")
        else:
            def _mu_fmt(_r: dict) -> str:
                _w = ("; cautions: " + "; ".join(_r["warnings"])) if _r.get("warnings") else ""
                return (f"{_r['start']} to {_r['end']} [{_r['tier']}, favourable "
                        f"limbs {_r['favorable_count']}/2; tithi {_r['tithi']}, "
                        f"yoga {_r['yoga']}, karana {_r['karana']}{_w}]")
            _best = mu.get("best")
            _earliest = mu.get("earliest_good")
            if _best:
                lines.append(f"  BEST window: {_mu_fmt(_best)}")
            if _earliest and _earliest is not _best:
                lines.append(f"  EARLIEST good window: {_mu_fmt(_earliest)}")
            _order = "earliest first" if _srch.get("mode") == "count" else "strongest first"
            _wins = mu.get("windows") or []
            if _wins:
                lines.append(f"  Favourable windows ({_order}):")
                for _r in _wins:
                    lines.append(f"    - {_mu_fmt(_r)}")

    # INGRESS (S152, timeline kind). Each moving graha's NEXT sign change with
    # the sign and the house it moves into, from both the ascendant and the
    # Moon; composed by agent.astro.dated_facts.build_timeline_facts from ONE
    # shared build_timeline scan. Guarded on presence -> a facts dict without it
    # renders byte-identically (the legacy-dict pin). GROWTH CONTRACT: "ingress"
    # is in capability_gate.FACT_BLOCK_PROVIDES.
    ing = chart_facts.get("ingress") or {}
    ing_events = ing.get("events") or []
    if ing_events:
        _w = ing.get("window") or {}
        lines.append("")
        lines.append(
            "Upcoming planetary ingresses (next sign change per graha) -- COMPUTED; "
            f"searched from {_w.get('start')} to {_w.get('end_date')}. The seven "
            "moving grahas only (the lunar nodes Rahu/Ketu are NOT computed here). "
            "EXPLAIN the relevant one; never invent or shift a date:")
        for _e in ing_events:
            _rx = " (retrograde)" if _e.get("retrograde") else ""
            lines.append(
                f"  {_e['body']} enters {_e.get('to_sign')} on {_e.get('date')}{_rx} "
                f"-- house {_e.get('to_house_from_lagna')} from the ascendant, "
                f"house {_e.get('to_house_from_moon')} from the Moon "
                f"(leaving {_e.get('from_sign')})")

    # COMBUSTION (S152, timeline kind). Near-term combustion windows for the five
    # taragrahas (Sun/Moon excluded by doctrine), from the same shared scan.
    # Guarded on presence. GROWTH CONTRACT: "combustion" is in FACT_BLOCK_PROVIDES.
    comb = chart_facts.get("combustion") or {}
    comb_w = comb.get("windows") or []
    if comb_w:
        lines.append("")
        lines.append(
            "Combustion windows (a planet too close to the Sun) -- COMPUTED, the "
            "five taragrahas only (Sun and Moon excluded). EXPLAIN the relevant "
            "one; never invent a date:")
        for _c in comb_w:
            _now = " -- CURRENTLY combust" if _c.get("ongoing") else ""
            _rx = " (retrograde)" if _c.get("retrograde_at_mid") else ""
            lines.append(
                f"  {_c.get('planet')}: {_c.get('start')} to {_c.get('end')}{_rx}{_now}")

    # MASA (S152, timeline kind). The current + upcoming lunar months (amanta),
    # placement facts only -- an intercalary month's NAME is withheld (S148 lock),
    # reported by its sankranti count instead. From the same shared scan. Guarded
    # on presence. GROWTH CONTRACT: "masa" is in FACT_BLOCK_PROVIDES.
    masa = chart_facts.get("masa") or {}
    if masa.get("current") or masa.get("upcoming"):
        lines.append("")
        lines.append(
            "Lunar month (masa) calendar -- COMPUTED (amanta). Dates are UT "
            "instants; the exact LOCAL civil date can differ by a day. A month "
            "with sankranti_count != 1 is intercalary and its name is withheld by "
            "design -- report the count, do NOT name it:")

        def _masa_fmt(_m: dict) -> str:
            _nm = _m.get("name_sa") or "(intercalary -- name withheld)"
            return (f"{_nm}: {_m.get('start')} to {_m.get('end')} "
                    f"[sankranti_count {_m.get('sankranti_count')}]")

        _cur = masa.get("current")
        if _cur:
            lines.append(f"  Current month -- {_masa_fmt(_cur)}")
        for _m in masa.get("upcoming") or []:
            lines.append(f"  Upcoming -- {_masa_fmt(_m)}")

    # DASHA / TIMING (S141). Restated from calculate_chart()['dasha'] by
    # chart_facts._read_dasha -- Vimshottari mahadasha + antardasha. Pratyantar is
    # suppressed there (wrong lord at that granularity under the drift). The dates
    # carry the accepted +/-37-day antardasha drift (KNOWN_DIVERGENCES Gap D1),
    # stated inline so the interpreter presents month/quarter windows rather than
    # false-precise days. Appended last and guarded on presence, so a dasha-less
    # chart_facts dict renders byte-identically to before (the legacy-dict pin).
    # GROWTH CONTRACT: "dasha_periods" is in capability_gate.FACT_BLOCK_PROVIDES.
    dasha = chart_facts.get("dasha_periods") or {}
    md = dasha.get("mahadasha")
    # TRANSITS (S142). Per-antardasha Saturn gochara + Sade Sati phase, computed
    # by agent.astro.transit_facts.build_transit_facts (composed onto chart_facts
    # by the caller, like yogas/navamsa). Looked up here by the same "<lord>|
    # <start>" key the composer emits, so each antardasha line below carries its
    # own corroborating transit -- the cross-system check (Sade Sati / Saturn
    # gochara) a benchmark answer used to tell a real dasha window from a
    # same-math false positive (S141/S142). GROWTH CONTRACT: "transits" is in
    # capability_gate.FACT_BLOCK_PROVIDES.
    tperiods = (chart_facts.get("transits") or {}).get("periods") or {}
    # KP SIGNIFICATORS (S144). Per-planet houses signified, ephemeris-computed
    # (KP Reader II fourfold + Reader IV node agency) -- see
    # agent.astro.kp_significator_facts's docstring. Why it exists: the cuspal sub-lord
    # fact rendered below is a single fixed value and cannot discriminate
    # between two antardashas in the same mahadasha; this fact varies BY
    # WHICH LORD IS RUNNING, so tagging each antardasha with its own lord's
    # significations gives the interpreter an actual period-varying signal
    # instead of one it has to invent. GROWTH CONTRACT:
    # "kp_planet_significations" is in capability_gate.FACT_BLOCK_PROVIDES.
    sigs = (chart_facts.get("kp_planet_significations") or {}).get(
        "planet_significations") or {}
    if md:
        lines.append("")
        lines.append("Vimshottari dasha timeline -- the planetary periods "
                     "(mahadasha) and their sub-periods (antardasha) that sequence "
                     "WHEN the chart's promises ripen. Read the period whose lord "
                     "governs the matter asked about; every date you need is here, "
                     "so do not compute or estimate any period yourself.")
        if tperiods:
            lines.append("Each sub-period below that carries a [Saturn TRANSIT: ...] "
                         "tag also states where Saturn was PHYSICALLY TRANSITING at "
                         "that sub-period's midpoint (sign, house from lagna, house "
                         "from Moon, and the Sade Sati phase that implies) -- a fact "
                         "that changes from period to period. Use this to "
                         "corroborate or weigh against which sub-period an actual "
                         "event falls in -- classical practice cross-checks a dasha "
                         "period against transit the same way.")
        if sigs:
            lines.append("Each sub-period below that carries a "
                         "[signifies houses: ...] tag names the KP houses its OWN "
                         "lord signifies (a NATAL, fixed fact about that planet -- "
                         "see the KP house-significator table further below). A "
                         "lord that signifies the house your question is actually "
                         "about is a real, period-specific reason to weigh that "
                         "sub-period; a lord whose signified houses do NOT include "
                         "it is a real, period-specific reason to weigh against it.")
        cur_ad = dasha.get("antardasha") or {}
        cur_ad_key = (cur_ad.get("lord"), cur_ad.get("start"))
        tree = dasha.get("mahadasha_tree") or []
        if tree:
            # COMPLETE tree (S141 gap #2): past + current + next few mahadashas,
            # each with its nine antardashas and their date windows.
            for node in tree:
                nmd = node["mahadasha"]
                tag = {"past": " [past]", "current": " [CURRENT]",
                       "future": " [upcoming]"}.get(node.get("phase"), "")
                lines.append(f"  {nmd['lord']} major period "
                             f"({nmd['start']} to {nmd['end']}){tag}")
                for a in node.get("antardashas") or []:
                    star = ("   <- the sub-period running now"
                            if (a["lord"], a["start"]) == cur_ad_key else "")
                    t = tperiods.get(f"{a['lord']}|{a['start']}")
                    transit_tag = f" [Saturn TRANSIT: {_transit_note(t)}]" if t else ""
                    sig_houses = sigs.get(a["lord"])
                    sig_tag = (f" [signifies houses: "
                               f"{','.join(str(h) for h in sig_houses)}]"
                               if sig_houses else "")
                    lines.append(f"      {a['lord']} sub-period "
                                 f"({a['start']} to {a['end']})"
                                 f"{transit_tag}{sig_tag}{star}")
        else:
            # Legacy chart_facts with no tree (e.g. a pre-gap#2 replay dict):
            # fall back to the current major/sub period only.
            lines.append(f"  Current major period (mahadasha): {md['lord']} "
                         f"({md['start']} to {md['end']})")
            if cur_ad:
                lines.append(f"  Current sub-period (antardasha): {cur_ad['lord']} "
                             f"({cur_ad['start']} to {cur_ad['end']})")
        note = dasha.get("drift_note")
        if note:
            lines.append(f"  Note on precision: {note}")

    # KP (S143). The 7th house cusp's sub-lord (Krishnamurti Paddhati),
    # restated from chart['meta']['house_cusps_kp_sidereal'] -- a DIFFERENT
    # ayanamsha than every other fact in this block, see chart_calculator.py's
    # S143 comment -- by agent.astro.kp_facts.build_kp_facts (composed onto
    # chart_facts by the caller, like yogas/transits/navamsa). In KP, a
    # house's own sub-lord decides whether that house's matter is granted;
    # the 7th cusp's sub-lord is marriage's own significator condition, a
    # second cross-system corroboration alongside the Sade Sati/Saturn-transit
    # tags above -- same posture, feed it, do not gate on it (S141 lock).
    # GROWTH CONTRACT: "kp_seventh_cusp_sub_lord" and "kp_cusp_sub_lords" are
    # in capability_gate.FACT_BLOCK_PROVIDES.
    if sigs:
        lines.append("")
        sig_lines = "; ".join(
            f"{p}: houses {','.join(str(h) for h in hs)}" for p, hs in sigs.items()
        )
        lines.append(
            f"KP house significators (Krishnamurti Paddhati) -- NATAL, fixed for "
            f"this chart, ephemeris-computed (KP Reader II fourfold + node agency): {sig_lines}. "
            f"A planet that signifies a house is a candidate to deliver that "
            f"house's matter when it is the acting dasha/antardasha lord (see the "
            f"[signifies houses: ...] tags on the dasha timeline above). This is a "
            f"DIFFERENT KP technique from the cuspal sub-lord fact below -- weigh "
            f"both, neither substitutes for the other."
        )

    kp = chart_facts.get("kp") or {}
    kp_sub_lord = kp.get("seventh_cusp_sub_lord")
    if kp_sub_lord:
        lines.append("")
        lines.append(
            f"KP (Krishnamurti Paddhati) -- NATAL fact, fixed for this chart "
            f"(NOT a transiting position, and NOT the same quantity as any "
            f"[Saturn TRANSIT: ...] tag above even if the planet name matches): "
            f"the 7th house cusp's sub-lord is {kp_sub_lord}. In KP, a house's "
            f"own sub-lord decides whether that house's matter is granted -- "
            f"weigh this alongside the dasha window and any Sade Sati/"
            f"Saturn-transit corroboration above, but a shared planet name "
            f"between this natal sub-lord and a transiting planet is NOT itself "
            f"a corroboration -- they are unrelated quantities unless the "
            f"specific KP technique you are applying actually connects them."
        )

    # KP all-12 cusp sub-lords (S153). The 7th-cusp paragraph above stays for
    # its marriage-corroboration caution; this general line gives every house's
    # cuspal sub-lord so the interpreter can weigh the cusp relevant to whatever
    # was asked (career=10, wealth=2/11, health=6, ...). Same engine + KP
    # ayanamsha as above; NATAL and fixed. In KP a house's own cusp sub-lord
    # decides whether that house's matter is granted. GROWTH CONTRACT:
    # "kp_cusp_sub_lords" is in capability_gate.FACT_BLOCK_PROVIDES.
    kp_all = kp.get("cusp_sub_lords") or {}
    if kp_all:
        _house_matter = {
            1: "self/body", 2: "wealth/family/speech", 3: "siblings/courage",
            4: "home/mother/property", 5: "children/education", 6: "debts/health/enemies",
            7: "marriage/partnership", 8: "longevity/upheaval", 9: "fortune/dharma",
            10: "career/status", 11: "gains/fulfilment", 12: "loss/expenditure/moksha",
        }
        _kp_parts = "; ".join(
            f"{_h} ({_house_matter[_h]}): {kp_all[_h]}"
            for _h in range(1, 13) if _h in kp_all
        )
        lines.append("")
        lines.append(
            "KP cusp sub-lords (Krishnamurti Paddhati) -- NATAL, fixed for this "
            "chart, computed under the KP ayanamsha (not Lahiri). Each house's "
            "OWN cusp sub-lord decides whether that house's matter is granted; "
            "weigh the cusp relevant to the question, not every house. "
            + _kp_parts + "."
        )

    return "\n".join(lines)


def _render(kept: list[dict], silent_on: list[str],
            declined_messages: list[str] | None = None) -> str:
    """Assemble the user-facing answer.

    `declined_messages` are the capability gate's plain-language notes about
    what could NOT be answered. They are appended, never interleaved, so the
    user always sees the limit alongside the answer rather than instead of it.
    """
    declined_messages = declined_messages or []
    if not kept:
        msg = "I can't answer this from the classical text and chart facts available."
        parts = [msg]
        if silent_on:
            parts.append("\n".join(f"- {s}" for s in silent_on))
        parts += declined_messages
        return "\n\n".join(parts)
    out = []
    for c in kept:
        cites = " ".join(f"[{i}]" for i in c.get("segment_ids", []))
        out.append(f"- {c['statement']} {cites}".rstrip())
    if silent_on:
        out.append("\nNot addressed: " + "; ".join(silent_on))
    body = "\n".join(out)
    if declined_messages:
        body += "\n\n" + "\n\n".join(declined_messages)
    return body


def answer_question(
    question: str,
    chart_facts: dict,
    *,
    chart: Optional[dict] = None,
    history: Optional[list] = None,
    llm: Optional[Callable] = None,
    interpreter_llm: Optional[Callable] = None,
    composer_llm: Optional[Callable] = None,
    compose: Optional[bool] = None,
    expert: Optional[bool] = None,
    token_budget: int = planner.DEFAULT_TOKEN_BUDGET,
    birth_time_confident: bool = True,
) -> dict:
    """End-to-end. Never raises for a model/gate problem -- refuses or fails
    open with the reason on the record.

    Stage 1.5 (`capability_gate.assess`) sits between planning and retrieval:
    it narrows the plan to what the fact block can actually support, so a
    question needing facts we do not have is declined in Python rather than
    handed to the Interpreter to guess at. See capability_gate's docstring.
    """
    # Per-stage wall clock. Cheap, always on: the capture needs it and a slow
    # stage is the first thing anyone asks about after a live run.
    _t = time.perf_counter()
    timings: dict[str, float] = {}

    def _lap(stage: str) -> None:
        nonlocal _t
        now = time.perf_counter()
        timings[stage] = round(now - _t, 3)
        _t = now

    plan = planner.plan_question(question, llm=llm, history=history)
    _lap("plan")
    verdict = capability_gate.assess(plan)
    _lap("capability_gate")

    if verdict.refuse_outright:
        return {"answer": "\n\n".join(verdict.messages),
                "refused": True,
                "reason": "capability_gate: " + ", ".join(i for i, _ in verdict.declined),
                "plan": plan,
                "declined": verdict.declined,
                "dropped_domains": verdict.dropped_domains,
                "capability_gate_version": verdict.gate_version,
                "trace": {"timings": timings, "payload": {},
                          "plan_before_gate": {"domains": list(plan.domains or []),
                                               "time_scope": plan.time_scope},
                          "gate_refused_outright": True,
                          "refused_at": "capability_gate"},
                "pipeline_version": PIPELINE_VERSION}

    # DISPATCH (S150): a computed-only plan -- one or more capabilities and NO
    # corpus domain -- is answered from its computed fact classes alone (already
    # in chart_facts; dated capabilities would compose at answer time, like the
    # muhurta block below). There is no corpus to retrieve, so build_from_plan
    # and its no-domains refusal are skipped and an empty payload stands in. A
    # plan with any corpus domain -- including a mixed corpus+capability plan --
    # still goes through build_from_plan unchanged. A plan with NEITHER domains
    # NOR capabilities falls to build_from_plan, which issues the honest refusal
    # exactly as before.
    _plan = verdict.plan
    _computed_only = bool(getattr(_plan, "capabilities", None)) and not _plan.domains
    if _computed_only:
        built = {"plan": _plan, "payload": {}, "tokens": 0,
                 "over_budget": False, "refused": False, "selection": None}
        _lap("select_and_build_payload")
    else:
        # BIRTH-TIME GATE (S145): birth_time_confident=False -> exclude KP (sub-lord
        # based, unsafe on a 2-3 min time error); BPHS-only, always under ceiling.
        built = planner.build_from_plan(verdict.plan, chart_facts,
                                        token_budget=token_budget,
                                        include_kp=birth_time_confident)
        _lap("select_and_build_payload")
        if built.get("refused"):
            return {"answer": f"(no answer) {built.get('refusal_reason', 'refused')}",
                    "refused": True, "reason": built.get("refusal_reason"),
                    "plan": built["plan"],
                    "declined": verdict.declined,
                    "capability_gate_version": verdict.gate_version,
                    "trace": {"timings": timings, "payload": built.get("payload") or {},
                              "refused_at": "payload_ceiling"},
                    "pipeline_version": PIPELINE_VERSION}

    # MUHURTA (S147). Unlike the chart-only composers (which the caller attaches
    # to chart_facts), electional timing is PLAN- and TIME-dependent: it needs the
    # planner's horizon (plan.muhurta_horizon) and a scan anchored at "now", so it
    # is composed HERE, after planning. Needs the raw chart (natal Moon sign +
    # nakshatra); if the caller passed none, muhurta is simply absent. The gate has
    # defaulted to a 2-year scan when the user named no horizon (S147), so a scan
    # is always reached for a muhurta question. Fail-soft: a compose failure costs
    # muhurta, never the answer. Lazy import keeps pipeline importable without
    # swisseph for the non-muhurta tests. Routed via the `muhurta` CAPABILITY
    # (S151) rather than a dedicated plan flag.
    if "muhurta" in (getattr(plan, "capabilities", None) or []) and chart is not None:
        try:
            from agent.astro.muhurta_facts import build_muhurta_facts
            import swisseph as _swe
            import datetime as _dt
            _n = _dt.datetime.now(_dt.timezone.utc)
            _start_jd = _swe.julday(_n.year, _n.month, _n.day,
                                    _n.hour + _n.minute / 60.0 + _n.second / 3600.0)
            # S147 (Sulabh): when the user named no window, DEFAULT to a 2-year
            # scan from now -- do NOT ask. Only an explicit timeframe overrides it.
            _hz = getattr(plan, "muhurta_horizon", None) or {"mode": "days", "value": 730}
            _mf = build_muhurta_facts(
                chart, _start_jd,
                horizon_days=_hz["value"] if _hz.get("mode") == "days" else None,
                want_count=_hz["value"] if _hz.get("mode") == "count" else None,
            )
            if _mf:
                chart_facts = {**chart_facts, "muhurta": _mf}
        except Exception:  # noqa: BLE001 -- muhurta is additive; never fatal
            pass

    # TIMELINE CAPABILITIES (S152). ingress / combustion / masa all project the
    # SAME sky over the SAME window, so they are composed from ONE shared
    # build_timeline scan (dated_facts.build_timeline_facts), routed by the
    # registry's kind="timeline" -- NOT one scan per capability (the bespoke
    # cabling the S151 lock forbade). Selection is the interpreter's: the full
    # trimmed set is attached and it picks the slice the question is about, like
    # every other fact class. Needs the raw chart; fail-soft (a scan failure
    # costs the dated facts, never the answer). Lazy import keeps pipeline (and
    # the non-dated tests) importable without swisseph.
    _tl_caps = [c for c in (getattr(_plan, "capabilities", None) or [])
                if c in capability_registry.timeline_capability_ids()]
    if _tl_caps and chart is not None:
        try:
            from agent.astro.dated_facts import build_timeline_facts
            _tf = build_timeline_facts(chart, _tl_caps)
            if _tf:
                chart_facts = {**chart_facts, **_tf}
        except Exception:  # noqa: BLE001 -- dated facts are additive; never fatal
            pass
    _lap("muhurta")

    fact_block = _fact_block(chart_facts)

    # MODEL ROUTING (S145): choose the interpreter model by the MEASURED payload
    # size (known now, before the call). Small enough for gpt-5's 400k window ->
    # gpt-5 (cleaner, stronger narrator); larger (e.g. the full curated KP corpus)
    # -> gpt-5.6-luna's 1.05M window. No pre-call guessing. Composer/planner are
    # unaffected -- luna is reserved for this one large-payload interpreter branch.
    _payload_approx = built.get("tokens", 0)
    _interp_model = (_interp.INTERPRETER_MODEL
                     if _payload_approx <= planner.GPT5_SAFE_APPROX
                     else _interp.LARGE_PAYLOAD_MODEL)

    # TIMING RANKING (S144). Deterministic convergence over dasha + KP
    # significators + Saturn transit, scored against THIS plan's target houses
    # (verdict.plan.houses -- e.g. [7,2,11] for marriage, [10,6,2,11] for
    # career; domain-neutral, one ranker for every life area). Appended to the
    # fact block so the interpreter EXPLAINS the top window instead of
    # re-ranking from its own priors -- the run-to-run variance that motivated
    # this. Fail-soft: an empty ranking leaves the block unchanged.
    # S145: role-weight the planner's flat target houses before ranking.
    # MARRIAGE ONLY today; every other domain -> all-promotion weights, i.e. the
    # ranking is byte-identical to pre-S145. Weighting zeroes the obstacle 8th
    # (mangalya) the planner emits for marriage, so it stops inflating runner-up
    # windows. Domain-neutrality of the ranker is preserved: it just honours the
    # weights it is handed. See agent/astro/house_roles.py.
    #
    # NOT A BUG (S145 Task 2a decision): plan.houses is the FULL set of houses a
    # Parashari would EXAMINE for a reading (marriage -> [2,7,8,11], the 8th being
    # mangalya/spouse-longevity), whereas the ranking's target set is the TIMING
    # subset (2,7,11). They differ by design: house_roles down-weights houses that
    # belong to the reading but not to onset-timing. The planner is deliberately
    # NOT narrowed -- keeping the 8th preserves reading breadth for any future
    # consumer of plan.houses, and costs nothing here (it scores 0).
    _target_weights = house_roles.weighted_targets(verdict.plan.domains,
                                                   verdict.plan.houses)
    # S148 (DIAGNOSTIC ONLY): retain the FULL scored ranking -- every antardasha
    # that scored > 0, not just the top-6 that render_ranking shows the model.
    # The interpreter still receives only the rendered top-6 text below; this
    # changes NOTHING about the answer. It exists so the capture can record what
    # scored where (the "is the 2026-2045 marriage gap a ranking artifact or a
    # calc bug" question could not be answered because only the winner was kept).
    _timing_ranking = timing_ranker.build_timing_ranking(chart_facts, _target_weights)
    _ranking_text = timing_ranker.render_ranking(_timing_ranking)
    if _ranking_text:
        fact_block = fact_block + "\n" + _ranking_text

    # EXPERT MODE (S141, the realignment). OFF by default -- the cited-claim path
    # below is unchanged. When on, the interpreter answers like an expert over the
    # COMPLETE fact block (facts hard-grounded, interpretation freed), and the
    # silence gate / composer / citation stripping are skipped entirely: there are
    # no verse-cited claims to verify or reorder. `expert=` wins over the env var,
    # exactly like `compose`. See interpreter.interpret_expert.
    if expert is None:
        expert = os.environ.get("ASTRO_EXPERT_MODE", "0") == "1"
    # Computed-only answers have no corpus verses to cite, so the cited-claim
    # (non-expert) path cannot apply; always render them in expert mode.
    if _computed_only:
        expert = True
    if expert:
        # CAPABILITY AWARENESS (S150 step 4). Give the interpreter the SAME
        # self-describing map the planner has: which computed capabilities are
        # available for THIS chart (fact_key present and non-empty) and which
        # inputs are present, plus the per-capability answering directives for
        # whatever the planner routed to. The interpreter answers on-map only,
        # declines off-map ("I don't compute that yet"), never upsells, and asks
        # at most one grounded clarification -- all governed by EXPERT_SYSTEM.
        _avail_keys = sorted(k for k, v in chart_facts.items() if v)
        _inputs_present = ("exact_birth_time",) if birth_time_confident else ()
        _cap_manifest = capability_registry.interpreter_manifest(
            _avail_keys, _inputs_present)
        _cap_directives = capability_registry.directives_for(
            getattr(_plan, "capabilities", None))
        ex = _interp.interpret_expert(question, fact_block, built["payload"],
                                      llm=interpreter_llm, model=_interp_model,
                                      history=history,
                                      capability_manifest=_cap_manifest,
                                      capability_directives=_cap_directives)
        _lap("interpreter_expert")
        # S147: fold any gate clarification (e.g. the muhurta "what window?" ask)
        # into the SHOWN answer. The non-expert _render path already appends
        # verdict.messages; without this the expert path (the live default) would
        # answer a mixed muhurta-without-horizon question but drop the ask. No
        # regression: verdict.messages is empty on every non-muhurta turn today.
        _expert_answer = ex["answer"]
        if verdict.messages:
            _msgs = "\n\n".join(verdict.messages)
            _expert_answer = (_expert_answer.rstrip() + "\n\n" + _msgs
                              if _expert_answer.strip() else _msgs)
        return {
            "answer": _expert_answer,
            "expert_mode": True,
            "refused": not _expert_answer.strip(),
            "plan": built["plan"],
            "declined": verdict.declined,
            "dropped_domains": verdict.dropped_domains,
            "capability_gate_version": verdict.gate_version,
            # No claim machinery ran; empty by construction so consumers (capture,
            # answer_view) see a familiar shape and never index a missing key.
            "kept_claims": [], "dropped_claims": [], "silent_on": [],
            "ghost_citations": [], "gate_stats": {}, "composed": None,
            "verifiability": None,
            "usage": ex["usage"], "tokens": built["tokens"], "model": ex["model"],
            "trace": {"timings": timings, "payload": built["payload"],
                      "fact_block": fact_block, "expert_mode": True,
                      # S148: the full scored ranking, for the capture only. The
                      # live path IS expert mode, so without this key here the
                      # probe would be blind exactly where it is needed.
                      "timing_ranking": _timing_ranking,
                      "plan_before_gate": {"domains": list(plan.domains or []),
                                           "houses": list(plan.houses or []),
                                           "time_scope": plan.time_scope}},
            "pipeline_version": PIPELINE_VERSION,
        }

    # chart_facts supplies the YOGA CATALOGUE for the precondition vocabulary
    # (S137). Without it the interpreter cannot name a yoga id and falls back to
    # `unfittable` -- measured on 20260919T072700Z, 9 of 15 predicates.
    interp = _interp.interpret(question, fact_block, built["payload"],
                               llm=interpreter_llm, chart_facts=chart_facts,
                               model=_interp_model)
    _lap("interpreter")
    gate = silence_gate.apply_silence_gate(interp, built["payload"], chart_facts)
    _lap("silence_gate")

    # Stage 5b -- THE COMPOSER. **ON by default since S136** (was off since
    # S131). It NEVER raises and never replaces the interpreter's claims: on
    # any failure `composed["composed"]` is false and the old bullet rendering
    # stands, so the worst case is the previous behaviour, not an error.
    #
    # WHY IT WAS OFF, AND WHY THAT REASON IS GONE. S131 shipped it dark because
    # the answers it would compose were not yet trustworthy -- ghost citations,
    # unused facts, and a payload riding the context ceiling. S136 closed all
    # three (live: 84,152 prompt tokens, 0 ghost citations, the silence gate
    # dropping a genuine false-precondition claim). The remaining gap was that
    # a correct answer still read as 16 undifferentiated classical conditionals
    # with no lead, no ranking and heavy repetition -- which is precisely what
    # this stage was built to fix (SESSION_LOG S136 section 12, items 1/4/5).
    #
    # KILL SWITCH: ASTRO_COMPOSER_ENABLED=0 restores the pre-S136 path exactly.
    # An explicit compose=True/False argument still wins over the environment,
    # so every existing test that pins either path is unaffected.
    if compose is None:
        compose = os.environ.get("ASTRO_COMPOSER_ENABLED", "1") != "0"
    composed: Optional[dict] = None
    if compose:
        composed = _composer.compose(question, gate, llm=composer_llm)
        _lap("composer")

    selection = built.get("selection")
    trace = {
        "timings": timings,
        # The plan the PLANNER produced, before the capability gate narrowed it.
        # `result["plan"]` is the post-gate plan; without this the gate's effect
        # is invisible and a reader mistakes the narrowed plan for Stage 1's own
        # output (observed on the first live capture, S129).
        "plan_before_gate": {"domains": list(plan.domains or []),
                             "houses": list(plan.houses or []),
                             "time_scope": plan.time_scope,
                             "whose_chart": plan.whose_chart,
                             "in_scope": plan.in_scope,
                             "source": plan.source},
        "gate_refused_outright": verdict.refuse_outright,
        "payload": built["payload"],          # carries the full verse text
        "fact_block": fact_block,
        "unit_ids": getattr(selection, "unit_ids", None),
        "per_domain_units": getattr(selection, "per_domain_units", None),
        "corpus_fraction": getattr(selection, "corpus_fraction", None),
        "timing_ranking": _timing_ranking,   # S148: full scored list (capture only)
        "estimated_real_tokens": built.get("estimated_real_tokens"),
        "over_budget": built.get("over_budget"),
        "tpm_note": built.get("tpm_note"),
        "interpreter_refused": interp.get("refused"),
        "interpreter_raw": interp.get("raw"),
        "gate_error": gate.error,
    }

    return {
        "trace": trace,
        "answer": _render(gate.kept_claims, gate.silent_on, verdict.messages),
        "refused": interp["refused"] and not gate.kept_claims,
        "plan": built["plan"],
        "declined": verdict.declined,
        "dropped_domains": verdict.dropped_domains,
        "capability_gate_version": verdict.gate_version,
        "kept_claims": gate.kept_claims,
        "dropped_claims": gate.dropped_claims,       # precondition-false, removed by the gate
        "silent_on": gate.silent_on,
        "ghost_citations": interp["ghost_citations"],  # must be []
        # S137 emission-contract health, passed through for the capture.
        "claims_with_preconditions": interp.get("claims_with_preconditions"),
        "precondition_rejects": interp.get("precondition_rejects"),
        "gate_stats": gate.stats,
        # S140: canonical first/second-class verifiability ledger, computed here
        # (the domain layer that owns the gate) so the capture layer renders it
        # as data and never computes a derived rate itself (test_qa_capture
        # imports-nothing guard; P-030 one-home discipline).
        "verifiability": verifiability.summarize(gate.stats),
        # Stage 5b output, or None when the composer did not run. `answer_view`
        # prefers it when present; `answer` above is always the Stage-5a render.
        "composed": composed,
        "usage": interp["usage"],
        "tokens": built["tokens"],
        "model": interp["model"],
        "pipeline_version": PIPELINE_VERSION,
    }
