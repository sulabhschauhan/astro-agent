"""
agent/calculations/kp/significator_engine.py
KP (Krishnamurti Paddhati) house-significator engine -- EPHEMERIS-COMPUTED,
not parsed. Distinct from significators.py (the AstroSage-PDF parser, kept as
the offline oracle). This module derives significators from the chart's own
computed primitives, so a served answer never depends on a PDF being present
(PDF-AS-ORACLE-ONLY, S143).

METHOD (K.S. Krishnamurti, KP Reader II -- Fundamentals of Astrology; node
agency: Reader IV). A planet P signifies a house by four classical routes,
in descending strength:
    tier 1  star_of_occupant : the house(s) P's STAR-LORD occupies
    tier 2  occupant         : the house(s) P occupies
    tier 3  star_of_owner    : the house(s) P's STAR-LORD owns
    tier 4  owner            : the house(s) P owns
NODE AGENCY (Rahu/Ketu only, additional to the fourfold above): a node also
signifies the houses of (i) its star-lord [already covered by tier 1/3 -- a
node has a star-lord like any planet], (ii) the planet(s) it is CONJOINED
with (same KP bhava), (iii) its SIGN-DISPOSITOR. Routes (ii)/(iii) are
emitted with tier=None -- their strength RANKING relative to the classical
1-4 tiers is doctrinally contested (Reader IV gives no closed ordering), so
this engine does NOT hardcode a number for them; the interpreter weighs them
against retrieved KP rules. Aspect-based node agency (a planet aspecting the
node) is deliberately OUT OF SCOPE for v1 -- conjunction-only, documented, to
keep the contested surface small; revisit if a reference chart needs it.

DOMAIN-NEUTRAL BY CONSTRUCTION: this computes significations for ALL 12 houses
of every planet. It has no concept of "marriage"/"career"/"children" -- the
question's house-set (marriage->2,7,11; career->2,6,10,11; children->2,5,11)
is applied downstream by significators_for_house() + the interpreter reading
retrieved classical rules, NOT by any branch here.

AYANAMSHA (KNOWN v1 LIMITATION, flagged for review): occupancy/ownership are
read off meta['house_cusps_kp_sidereal'] (KP/Krishnamurti ayanamsha) while
planet longitudes in planetary_positions are Lahiri. The Lahiri-KP gap is
~5-6 arcmin (see sub_lords.py), immaterial to which ~30deg house a planet
falls in EXCEPT within ~one gap-width of a cusp. Such planets are flagged in
the returned 'boundary_warnings'. The clean fix -- surface ayanamsha_kp in
meta and convert planet longitudes before placing them -- is a separate
surgical edit to chart_calculator, intentionally not bundled here.

Python 3.11.
"""
from __future__ import annotations

import logging

from agent.chart_calculator import SIGN_LORDS, _nakshatra, _sign

logger = logging.getLogger(__name__)

_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter",
            "Venus", "Saturn", "Rahu", "Ketu")
_NODES = ("Rahu", "Ketu")

# Classical fourfold strength, lower = stronger (KP Reader II). Node-agency
# routes intentionally carry no number -- see module docstring.
_TIER = {"star_of_occupant": 1, "occupant": 2, "star_of_owner": 3, "owner": 4}

# A planet within this many degrees of a KP cusp may be placed in the wrong
# house by the Lahiri-vs-KP ayanamsha mix (see AYANAMSHA note above).
# Justification: the gap is ~5-6 arcmin (~0.10deg); 0.25deg is a ~2.5x margin
# that flags the genuinely-ambiguous cases without spamming mid-house planets.
# Scope guard: only warns; never silently reassigns. TUNING NOTE: tighten once
# ayanamsha_kp is surfaced and longitudes are converted (then this can drop to
# a pure cross-ephemeris residual, ~arcsec).
_CUSP_BOUNDARY_THRESHOLD_DEG = 0.25


def _house_of_longitude(lon: float, cusps: list[float]) -> int:
    """1-12: the KP bhava a sidereal longitude falls in, by cusp spans.
    cusps[i] = start of house i+1; a house runs from its cusp to the next."""
    lon %= 360.0
    for h in range(12):
        start, end = cusps[h], cusps[(h + 1) % 12]
        if start < end:
            if start <= lon < end:
                return h + 1
        else:  # span wraps past 360
            if lon >= start or lon < end:
                return h + 1
    # Exhaustive 12-span cover of 0-360; unreachable for finite input.
    raise ValueError(f"_house_of_longitude: {lon} matched no cusp span {cusps!r}")


def _cusp_boundary_flags(planet_lon: dict[str, float], cusps: list[float]) -> list[str]:
    warnings: list[str] = []
    for p, lon in planet_lon.items():
        lon %= 360.0
        for c in cusps:
            d = abs((lon - c + 180.0) % 360.0 - 180.0)
            if d <= _CUSP_BOUNDARY_THRESHOLD_DEG:
                warnings.append(
                    f"{p} at {lon:.4f} is {d*60:.1f}' from a KP cusp -- "
                    f"house placement is ayanamsha-boundary-sensitive"
                )
                break
    return warnings


def compute_kp_significators(chart: dict) -> dict:
    """Ephemeris-computed KP house significators for all 9 planets.

    Args:
        chart: a calculate_chart() dict. Requires chart['planetary_positions']
            (each planet with a 'longitude', Lahiri sidereal) and
            chart['meta']['house_cusps_kp_sidereal'] (12 floats, index 0 =
            house 1's KP cusp).

    Returns:
        {
          "significators": {planet: {house_int: {"tier": int|None, "via": str}}},
          "boundary_warnings": [str, ...],
        }
        For each planet, the STRONGEST route to each house is kept (a numeric
        tier always beats a node-agency None; lower numeric beats higher).

    Raises:
        KeyError/ValueError/TypeError on a malformed chart shape -- fail LOUD
        here (this is a direct calculation, mirroring sub_lords.kp_house_sub_lord);
        the fail-SOFT boundary belongs in the fact composer that wraps this.
    """
    positions = chart["planetary_positions"]
    cusps = chart["meta"]["house_cusps_kp_sidereal"]
    if not isinstance(cusps, (list, tuple)) or len(cusps) != 12:
        raise ValueError(
            f"compute_kp_significators: house_cusps_kp_sidereal must be length 12, "
            f"got {cusps!r}"
        )

    planet_lon = {p: float(positions[p]["longitude"]) % 360.0
                  for p in _PLANETS if p in positions}

    # --- primitives, all KP-cuspal (not whole-sign) ---
    house_of = {p: _house_of_longitude(lon, cusps) for p, lon in planet_lon.items()}
    occupants: dict[int, list[str]] = {h: [] for h in range(1, 13)}
    for p, h in house_of.items():
        occupants[h].append(p)
    owner = {h: SIGN_LORDS[_sign(cusps[h - 1])] for h in range(1, 13)}  # KP cuspal owner
    owns: dict[str, list[int]] = {}
    for h, lord in owner.items():
        owns.setdefault(lord, []).append(h)
    star_lord = {p: _nakshatra(lon)[2] for p, lon in planet_lon.items()}

    def _emit(acc: dict[int, dict], house: int | None, via: str) -> None:
        if house is None:
            return
        tier = _TIER.get(via)  # None for node-agency routes
        cur = acc.get(house)
        if cur is None:
            acc[house] = {"tier": tier, "via": via}
        elif tier is not None and (cur["tier"] is None or tier < cur["tier"]):
            acc[house] = {"tier": tier, "via": via}

    significators: dict[str, dict[int, dict]] = {}
    for p in planet_lon:
        acc: dict[int, dict] = {}
        sl = star_lord[p]
        if sl in house_of:                       # tier 1: star-lord's occupancy
            _emit(acc, house_of[sl], "star_of_occupant")
        _emit(acc, house_of[p], "occupant")      # tier 2
        for h in owns.get(sl, []):               # tier 3: star-lord's ownership
            _emit(acc, h, "star_of_owner")
        for h in owns.get(p, []):                # tier 4: own ownership
            _emit(acc, h, "owner")
        if p in _NODES:                          # node agency (conjunction + dispositor)
            for c in occupants[house_of[p]]:
                if c == p:
                    continue
                _emit(acc, house_of[c], "node_conjunction")
                for h in owns.get(c, []):
                    _emit(acc, h, "node_conjunction")
            disp = SIGN_LORDS[_sign(planet_lon[p])]
            if disp in house_of:
                _emit(acc, house_of[disp], "node_dispositor")
            for h in owns.get(disp, []):
                _emit(acc, h, "node_dispositor")
        significators[p] = dict(sorted(acc.items()))

    return {
        "significators": significators,
        "boundary_warnings": _cusp_boundary_flags(planet_lon, list(cusps)),
    }


def significators_for_house(table: dict, house: int) -> list[tuple[str, int | None, str]]:
    """Domain-neutral reader: which planets signify `house`, strongest first.

    Args:
        table: compute_kp_significators()['significators'].
        house: 1-12.

    Returns:
        [(planet, tier, via), ...] sorted by strength. Numeric tiers ascend
        (1 strongest); node-agency (tier=None) sorts last but is retained --
        the interpreter decides how to weigh it, this engine does not drop it.
    """
    if not (1 <= house <= 12):
        raise ValueError(f"significators_for_house: house must be 1-12, got {house}")
    rows = [(p, sig[house]["tier"], sig[house]["via"])
            for p, sig in table.items() if house in sig]
    return sorted(rows, key=lambda r: (r[1] is None, r[1] if r[1] is not None else 99))
