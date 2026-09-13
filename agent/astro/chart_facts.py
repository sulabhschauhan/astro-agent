"""
Astro Agent -- CHART FACTS ADAPTER (Stage 3.5 input shim).

PATH B. Step 1 of the S129 cutover.

Restates `agent.chart_calculator.calculate_chart()` output into the
`chart_facts` shape `agent.astro.payload_builder.parse_lord_house_map`
accepts, which is what `pipeline._fact_block` and `silence_gate` both read:

    {"lord_house_map": {1: 5, 2: 9, ...}, "ascendant_sign": "Sagittarius"}

RESTATE, NEVER COMPUTE (S124 lock). This module does no astrology. It reads
two fields the calculator already produced and reshapes them. It imports no
ephemeris, no sign tables and no lord tables -- if a future edit needs one,
the edit belongs in the calculator, not here.

FAILS CLOSED. A partial or malformed map raises `ChartFactsError` rather than
returning 11 houses, mirroring `payload_builder.IncompleteChartError`'s own
hard law: the interpreter must never be handed a chart it can only half see,
because a missing house reads to it as an absent placement rather than as an
unknown one.

Python 3.11.
"""
from __future__ import annotations

from typing import Any

__all__ = ["ChartFactsError", "build_chart_facts"]

_EXPECTED_HOUSES = frozenset(range(1, 13))


class ChartFactsError(ValueError):
    """Raised when calculate_chart() output cannot yield a complete 12-house
    lord->house map plus an ascendant sign.

    Deliberately NOT a subclass of payload_builder.IncompleteChartError: that
    exception means "the caller handed the payload builder a bad chart_facts
    dict"; this one means "the calculator's own output could not be turned
    into one". Keeping them distinct keeps the blame boundary readable in a
    traceback.
    """


def build_chart_facts(chart: dict) -> dict:
    """Reshape `calculate_chart()` output into Path B's chart_facts dict.

    Args:
        chart: the dict returned by agent.chart_calculator.calculate_chart().
            Read-only -- never mutated.

    Returns:
        {"lord_house_map": {int: int} for houses 1..12,
         "ascendant_sign": str}

    Raises:
        ChartFactsError: on a missing/malformed source field, a house set that
            is not exactly {1..12}, a duplicate house, a null `lord_in_house`,
            or a blank ascendant. Never returns a partial map.
    """
    if not isinstance(chart, dict):
        raise ChartFactsError(
            "chart must be the dict returned by calculate_chart(); got "
            f"{type(chart).__name__}"
        )

    lord_house_map = _read_lord_house_map(chart)
    ascendant_sign = _read_ascendant(chart)
    planet_positions = _read_planet_positions(chart)
    house_lords = _read_house_lords(chart)
    aspects = _read_aspects(chart)
    navamsa = _read_navamsa(chart)

    facts = {"lord_house_map": lord_house_map,
             "ascendant_sign": ascendant_sign,
             "planet_positions": planet_positions,
             "house_lords": house_lords,
             "aspects": aspects}
    if navamsa:
        facts["navamsa"] = navamsa
    return facts


# ---------------------------------------------------------------- internals

def _read_lord_house_map(chart: dict) -> dict[int, int]:
    """Pull house -> lord_in_house out of chart['house_lord_mapping'].

    Source contract: agent/chart_calculator.py builds `house_lords` as a list
    of 12 dicts with keys house/sign/lord/lord_in_house, and returns it under
    'house_lord_mapping'.
    """
    try:
        rows = chart["house_lord_mapping"]
    except KeyError:
        raise ChartFactsError(
            "chart is missing 'house_lord_mapping' -- this is not "
            "calculate_chart() output, or the calculator's contract changed"
        ) from None

    if not isinstance(rows, list):
        raise ChartFactsError(
            "chart['house_lord_mapping'] must be a list of 12 dicts; got "
            f"{type(rows).__name__}"
        )
    if len(rows) != 12:
        raise ChartFactsError(
            f"chart['house_lord_mapping'] has {len(rows)} entries, expected 12"
        )

    lord_house_map: dict[int, int] = {}
    missing_placements: list[int] = []

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ChartFactsError(
                f"chart['house_lord_mapping'][{index}] must be a dict; got "
                f"{type(row).__name__}"
            )

        house = _coerce_int(
            row.get("house"), f"chart['house_lord_mapping'][{index}]['house']"
        )
        if house in lord_house_map or house in missing_placements:
            raise ChartFactsError(
                f"chart['house_lord_mapping'] lists house {house} more than once"
            )
        if house not in _EXPECTED_HOUSES:
            raise ChartFactsError(
                f"chart['house_lord_mapping'][{index}]['house'] is {house}; "
                "house numbers must lie in 1..12"
            )

        placement = row.get("lord_in_house")
        if placement is None:
            # The calculator emits None when the lord planet carries no house.
            # Collect rather than raise immediately, so the error names EVERY
            # unplaced house instead of only the first -- a chart broken this
            # way is usually broken in more than one place.
            missing_placements.append(house)
            continue

        lord_house_map[house] = _coerce_int(
            placement, f"chart['house_lord_mapping'][{index}]['lord_in_house']"
        )

    if missing_placements:
        raise ChartFactsError(
            "chart['house_lord_mapping'] has a null 'lord_in_house' for "
            f"house(s) {sorted(missing_placements)} -- refusing to build a "
            "partial lord_house_map"
        )

    resolved = set(lord_house_map)
    if resolved != _EXPECTED_HOUSES:
        raise ChartFactsError(
            "chart['house_lord_mapping'] did not resolve every house 1..12; "
            f"missing {sorted(_EXPECTED_HOUSES - resolved)}"
        )

    for house, placement in lord_house_map.items():
        if placement not in _EXPECTED_HOUSES:
            raise ChartFactsError(
                f"house {house}'s lord is placed in house {placement}; "
                "placements must lie in 1..12"
            )

    return lord_house_map


# Order is the classical Navagraha sequence, not dict order, so the rendered
# fact block is byte-stable across runs and diffable between charts.
_GRAHA_ORDER = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
                "Rahu", "Ketu")

# The two lunar nodes. They are included as POSITIONS -- BPHS ch.34 v.16 is
# explicit that their effect travels through the house they occupy and their
# association, not through lordship ("Rahu and Ketu give predominantly the
# effects as due to their conjunction with a house lord or as due to the house
# they occupy... they do not have a disposition of their own").
#
# But two of their calculator fields are CONSTANTS, not measurements, and are
# deliberately NOT restated:
#   - `dignity` is hardcoded "Neutral" (chart_calculator.py:424,430) because the
#     nodes own no sign; it is a placeholder, and the verse above says so too.
#   - `retrograde` is hardcoded True (same lines) because the chart uses
#     swe.MEAN_NODE, which regresses at 19.35 deg/yr on an 18.6-year cycle and
#     is never direct -- a constant that discriminates nothing. Moot now that
#     retrograde is not restated for ANY graha (see _read_planet_positions),
#     but recorded so a future widening does not reintroduce it for the nodes.
_NODES = frozenset({"Rahu", "Ketu"})


def _read_planet_positions(chart: dict) -> dict[str, dict]:
    """Restate chart['planetary_positions'] as {planet: {house, sign, retrograde?}}.

    SCOPE, ratified S129 after a 6-role review:
      - house + sign + retrograde ONLY.
      - NO dignity. `_dignity()` (chart_calculator.py:147-163) is a 5-tier
        ladder with NO oracle table -- S127's test (53b90f3) is characterization
        only -- and docs/KNOWN_DIVERGENCES.md records the dignity vocabulary
        fragmenting three ways (BPHS literal / Kapoor-Raman / AstroSage).
        Classical doctrine keys hard on dignity, so an unvalidated label inside
        a block the prompt calls "the only chart facts you may use" becomes a
        FALSE PREMISE the silence gate cannot catch. Add it only with an oracle.
      - NO longitude. Surfaced by S127 (a65cb4c) and available, but a raw
        degree is not a doctrinal condition -- no BPHS verse keys on one -- so
        it would be tokens the interpreter cannot use.
      - NO retrograde, DROPPED during implementation on three independent
        grounds (S129, measured, not assumed):
          1. YIELD. Exactly 10 of 20,426 corpus sentences key on
             retrograde/vakri -- 0.05%, against 344 that key on planet-in-house.
          2. A TRUE/FALSE ERASES A STATION. Sulabh's Saturn moves at
             +0.0087 deg/day at birth, ~1/100th of normal speed, and stations
             retrograde 5.27 days later (1988-04-11 01:47 UT, bisected). The
             boolean `False` is astronomically right and doctrinally
             misleading: a near-stationary graha is a special state that a bare
             flag flattens.
          3. AN UNRESOLVED ORACLE CONFLICT sits on exactly this field --
             reference/oracle_fixtures/sulabh.md tags Saturn "(R)" and asserts
             at its own line 197 that this "matches production/AstroSage". It
             does not: production computes direct, correctly. Putting a field
             into the fact block while its oracle disagrees with production is
             the false-premise failure this module exists to avoid.
        Revisit when (3) is adjudicated AND a verse is found that needs it.

    A missing/short `planetary_positions` returns {} rather than raising: unlike
    the lord map (where a hole means a house silently reads as unplaced), an
    absent planet block is a complete, honest absence. The capability gate is
    what decides whether that absence blocks the question.
    """
    raw = chart.get("planetary_positions")
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ChartFactsError(
            "chart['planetary_positions'] must be a dict; got "
            f"{type(raw).__name__}"
        )

    out: dict[str, dict] = {}
    for planet in _GRAHA_ORDER:
        row = raw.get(planet)
        if row is None:
            continue
        if not isinstance(row, dict):
            raise ChartFactsError(
                f"chart['planetary_positions'][{planet!r}] must be a dict; got "
                f"{type(row).__name__}"
            )
        house = row.get("house")
        sign = row.get("sign")
        if house is None or sign is None:
            raise ChartFactsError(
                f"{planet} is missing house and/or sign "
                f"(house={house!r}, sign={sign!r}) -- refusing a partial position"
            )
        house_i = _coerce_int(house, f"chart['planetary_positions'][{planet!r}]['house']")
        if house_i not in _EXPECTED_HOUSES:
            raise ChartFactsError(
                f"{planet} is placed in house {house_i}; houses must lie in 1..12"
            )
        if not isinstance(sign, str) or not sign.strip():
            raise ChartFactsError(f"{planet}'s sign is missing or blank: {sign!r}")

        row_out = {"house": house_i, "sign": sign.strip()}
        standing = _uncontested_dignity(row.get("dignity"))
        if standing is not None:
            row_out["dignity"] = standing
        out[planet] = row_out
    return out


# The three dignity tiers `_dignity()` resolves from FIXED tables, before it
# ever consults planetary friendship (chart_calculator.py:147-162). These are
# the ones restated.
_UNCONTESTED_DIGNITY = frozenset({"Exalted", "Debilitated", "Own Sign"})


def _uncontested_dignity(value) -> str | None:
    """Exalted / Debilitated / Own Sign pass through; everything else is
    dropped. Returns None when there is nothing safe to state.

    WHY THE SPLIT (S130). S129b excluded dignity WHOLESALE, on the stated
    ground that "no oracle table exists to validate it" and that
    docs/KNOWN_DIVERGENCES.md "records the dignity vocabulary fragmenting
    three ways". Checked S130: KNOWN_DIVERGENCES.md contains no dignity entry.
    The three-way fragmentation it refers to is Gap S1, Saptavargaja Bala,
    which is about VIRUPA TIER WEIGHTS in Shadbala (Mooltrikona=45 / Own=30 /
    Pramudita=20 vs Kapoor 45/30/22.5/15) -- how much STRENGTH a tier scores,
    never which sign a planet is exalted in.

    `_dignity()` tests EXALTATION, then DEBILITATION, then _OWN_SIGNS -- all
    fixed constants locked in S21 from PVR Table 6 and never contested since --
    and only then falls through to _FRIENDS, which is the genuinely contested
    part. So the S129b reasoning correctly blocks the friendship tail and
    incorrectly blocks the head. This restates the head only.

    WHAT THIS UNBLOCKS: Neecha Bhanga Raja Yoga, which needs exactly a
    debilitated planet plus its dispositor's exaltation -- named in S21 as the
    reason dignity mattered at all ("most raja/dhana yogas and Neecha Bhanga
    literally require knowing exaltation/debilitation/own-sign status").

    STILL OUT: Friendly / Inimical / Neutral (contested tiering), and
    exaltation DEGREES -- the tables carry signs only, so deep-exaltation and
    degree-keyed Neecha Bhanga variants remain unreachable. Do not synthesise
    either here.
    """
    if isinstance(value, str) and value.strip() in _UNCONTESTED_DIGNITY:
        return value.strip()
    return None


def _read_house_lords(chart: dict) -> dict[int, dict]:
    """Restate the two fields `_read_lord_house_map` throws away: `lord` and
    `sign`. Returns {house: {"lord": str, "sign": str, "in_house": int}}.

    WHY (S130). `lord_house_map` is house->house. It drops WHICH PLANET owns
    each house, so the fact block could not say "the 9th lord is Sun", and two
    lords sharing a house showed up only as two unrelated lines twelve rows
    apart. Measured on the live run: the Interpreter emitted "the 9th lord in
    the 4th" and "the 10th lord in the 4th" as SEPARATE claims and never
    noticed they name the same house -- which is the Dharma-Karmadhipati yoga.
    Asking the model to join those two lines is exactly the "never LLM-bridge
    two representations" failure (CLAUDE.md Working Style #23): compute the
    grouping, feed the grouping.

    STILL A RESTATEMENT. `calculate_chart()` already puts `lord` and `sign` on
    every `house_lord_mapping` row; this reads them. No sign table, no lord
    table, no astrology -- the module law at the top of this file holds.

    Absent/short source returns {} rather than raising: the 12-house contract
    is enforced by `_read_lord_house_map` on the SAME rows, so a hole here can
    only mean the calculator stopped emitting an optional label.
    """
    rows = chart.get("house_lord_mapping")
    if not isinstance(rows, list):
        return {}

    out: dict[int, dict] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        lord = row.get("lord")
        sign = row.get("sign")
        placement = row.get("lord_in_house")
        if not isinstance(lord, str) or not lord.strip():
            continue
        if placement is None:
            continue
        house = _coerce_int(row.get("house"),
                            f"chart['house_lord_mapping'][{index}]['house']")
        out[house] = {
            "lord": lord.strip(),
            "sign": sign.strip() if isinstance(sign, str) and sign.strip() else None,
            "in_house": _coerce_int(
                placement,
                f"chart['house_lord_mapping'][{index}]['lord_in_house']"),
        }
    return out

def _read_aspects(chart: dict) -> dict:
    """Restate the three aspect fields `calculate_chart()` already returns:
    `conjunctions`, `aspects_by_planet`, `aspected_by` (chart_calculator.py:
    437-471, surfaced at 737-741).

    WHY (S130). Two of the four yogas a benchmark answer found for this chart
    turn on an aspect, and the fact block carried none, so the Interpreter could
    not reach them at any prompt quality. `aspected_by` also catches the
    affliction check the benchmark itself got WRONG -- it called a 12th-house
    Moon "unaspected" when Venus in the 6th casts its 7th aspect onto it.

    RESTATEMENT, not calculation. Every value here is produced by
    `_calc_aspects` and discarded at the adapter today. No orb, no strength,
    no drishti arithmetic happens in this module -- the aspect RULES (7th for
    all, plus Mars 4/8, Jupiter 5/9, Saturn 3/10) live in the calculator, which
    is where the module law at the top of this file says they belong.

    NOT restated: nothing is filtered or ranked. A benefic/malefic split would
    need a dignity table this module deliberately does not have (see
    _read_planet_positions), and the corpus supplies that doctrine anyway.

    Absent source returns {} -- an honest absence, same posture as
    _read_planet_positions. The capability gate decides what that blocks.
    """
    conjunctions = chart.get("conjunctions")
    by_planet = chart.get("aspects_by_planet")
    aspected_by = chart.get("aspected_by")
    if not isinstance(by_planet, dict) and not isinstance(conjunctions, list):
        return {}

    out: dict = {}
    if isinstance(conjunctions, list):
        out["conjunctions"] = [c.strip() for c in conjunctions
                               if isinstance(c, str) and c.strip()]
    if isinstance(by_planet, dict):
        cleaned: dict[str, list[int]] = {}
        for planet in _GRAHA_ORDER:
            houses = by_planet.get(planet)
            if not isinstance(houses, list):
                continue
            seen: list[int] = []
            for h in houses:
                hi = _coerce_int(h, f"chart['aspects_by_planet'][{planet!r}]")
                if hi not in _EXPECTED_HOUSES:
                    raise ChartFactsError(
                        f"{planet} is recorded as aspecting house {hi}; "
                        "aspected houses must lie in 1..12")
                if hi not in seen:
                    seen.append(hi)
            cleaned[planet] = sorted(seen)
        out["aspects_by_planet"] = cleaned
    if isinstance(aspected_by, dict):
        out["aspected_by"] = {
            p: sorted({s for s in v if isinstance(s, str) and s.strip()})
            for p, v in aspected_by.items()
            if isinstance(v, list) and p in _GRAHA_ORDER
        }
    return out

def _read_navamsa(chart: dict) -> dict:
    """Restate a D9 chart the CALLER attached at chart["navamsa"].

    Returns {"d9_lagna_sign": str, "placements": {planet: {sign, house,
    dignity?}}} or {} when the caller supplied none.

    WHO COMPUTES IT, AND WHY NOT HERE. `agent/calculations/vargas/navamsa.py`
    has been built and oracle-clean since S20 -- `compute_navamsa(jd_ut,
    asc_lon_sidereal)`, 4/4 reference charts passing, David tested first
    specifically for pada-boundary sensitivity. It was never wired to anything
    because S20 locked "Don't touch chart_calculator. Don't retrofit D1" for
    architectural reasons, and nobody since decided D9 should stay away from
    USERS -- S20's own V1 scope table marks D9 as required for the two highest
    value marriage questions. The unwired state is drift, not policy.

    So the composition happens in the CALLER, which already imports both
    modules, and this adapter only restates the result. That keeps all three
    rules intact at once: chart_calculator untouched (S20), this module
    importing no calculator (its own law), and the fact block growing only by
    restatement (P-022).

    PRECISION NOTE. `calculate_chart()` exposes `meta.jd_ut` rounded to 6dp
    and `meta.asc_lon_sidereal` to 4dp. Feeding the rounded values costs at
    most ~0.00005 deg of lagna precision against a 3 deg 20' pada, i.e. a
    boundary case has to land within ~0.2 arc-seconds to flip. Accepted and
    recorded rather than resolved, because resolving it means exposing the
    unrounded values from chart_calculator -- which is the S20 lock.
    """
    raw = chart.get("navamsa")
    if not isinstance(raw, dict):
        return {}
    lagna = raw.get("d9_lagna_sign")
    placements = raw.get("placements")
    if not isinstance(placements, dict):
        return {}

    out: dict[str, dict] = {}
    for planet in _GRAHA_ORDER:
        row = placements.get(planet)
        if not isinstance(row, dict):
            continue
        sign = row.get("sign")
        house = row.get("house")
        if not isinstance(sign, str) or not sign.strip() or house is None:
            continue
        entry = {"sign": sign.strip(),
                 "house": _coerce_int(house, f"navamsa placement {planet}")}
        standing = _uncontested_dignity(row.get("dignity"))
        if standing is not None:
            entry["dignity"] = standing
        out[planet] = entry
    if not out:
        return {}
    result: dict = {"placements": out}
    if isinstance(lagna, str) and lagna.strip():
        result["d9_lagna_sign"] = lagna.strip()
    return result

def _read_ascendant(chart: dict) -> str:
    """Pull the ascendant sign out of chart['lagna_chart']['ascendant']."""
    try:
        lagna = chart["lagna_chart"]
    except KeyError:
        raise ChartFactsError(
            "chart is missing 'lagna_chart' -- this is not calculate_chart() "
            "output, or the calculator's contract changed"
        ) from None

    if not isinstance(lagna, dict):
        raise ChartFactsError(
            f"chart['lagna_chart'] must be a dict; got {type(lagna).__name__}"
        )

    ascendant = lagna.get("ascendant")
    if not isinstance(ascendant, str) or not ascendant.strip():
        raise ChartFactsError(
            "chart['lagna_chart']['ascendant'] is missing or blank; got "
            f"{ascendant!r}"
        )
    return ascendant.strip()


def _coerce_int(value: Any, field_label: str) -> int:
    """int() a source field, naming the exact field on failure.

    `bool` is rejected explicitly: it is an int subclass, so a stray True
    would otherwise silently become house 1.
    """
    if isinstance(value, bool):
        raise ChartFactsError(f"{field_label} is a bool ({value!r}), not a house number")
    try:
        return int(value)
    except (TypeError, ValueError) as e:
        raise ChartFactsError(f"{field_label} is not an integer: {value!r} ({e})") from e
