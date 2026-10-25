"""Astro Agent -- PATYAYINI DASA engine (Varshaphala / sub-engine E).

Patyayini (Raman "Varshaphala" Ch.V, "Varshadasa") is a degree-driven annual
dasa. VALIDATED S156 against the JHora desktop oracle (Sulabh 2025 + 2026, order
exact 8/8 both years):

  1. BODIES = the 7 classical planets + the Lagna (Asc). Nodes (Rahu/Ketu) are
     EXCLUDED.
  2. ORDER = ascending degree-WITHIN-SIGN ("reject the signs", Raman Sec.49):
     take each body's longitude mod 30 and sort ascending.
  3. PATYAMSHA(body) = its degree-in-sign minus the PREVIOUS body's degree-in-sign;
     the FIRST body's patyamsha = its own degree-in-sign. These telescope so the
     patyamshas sum to the largest degree-in-sign.
  4. PERIOD(days) = cycle_days * patyamsha / max_degree_in_sign, where cycle_days
     = (next_pravesh - this_pravesh). Periods run in the sorted order from the
     pravesh and sum to the full cycle.

Pure stdlib -- takes sidereal longitudes, computes no astrology of its own and
needs no ephemeris. Fail-closed on bad input (raises ValueError with a meaningful
message); the fact-composer above this is the fail-SOFT boundary.

Python 3.11.
"""
from __future__ import annotations

__all__ = ["ASC", "patyayini_dasha"]

ASC = "Asc"
# 7 classical planets + Lagna; nodes excluded by doctrine.
_BODIES = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", ASC)


def patyayini_dasha(body_longitudes: dict[str, float],
                    pravesh_jd_ut: float,
                    next_pravesh_jd_ut: float) -> list[dict]:
    """Patyayini maha-dasa periods for one annual chart.

    Args:
        body_longitudes: sidereal longitudes (deg, 0..360) keyed by body name;
            must contain the 7 classical planets and "Asc". Extra keys
            (e.g. nodes) are ignored.
        pravesh_jd_ut: Julian Day (UT) of this Varsha Pravesh.
        next_pravesh_jd_ut: Julian Day (UT) of the next Varsha Pravesh.

    Returns:
        List of {"lord", "start_jd", "end_jd", "days", "patyamsha_deg"} in dasa
        order (ascending degree-in-sign). Period total == the cycle length.

    Raises:
        ValueError: a required body is missing, a longitude is non-finite, the
            cycle is non-positive, or every degree-in-sign is zero (degenerate).
    """
    cycle = float(next_pravesh_jd_ut) - float(pravesh_jd_ut)
    if not cycle > 0:
        raise ValueError(f"patyayini: non-positive cycle ({cycle} days)")

    deg_in_sign: dict[str, float] = {}
    for b in _BODIES:
        if b not in body_longitudes:
            raise ValueError(f"patyayini: missing body '{b}'")
        lon = float(body_longitudes[b])
        if lon != lon:  # NaN guard
            raise ValueError(f"patyayini: non-finite longitude for '{b}'")
        deg_in_sign[b] = lon % 30.0

    # Ascending degree-in-sign; tie-break by a stable body order for determinism.
    order = sorted(_BODIES, key=lambda b: (deg_in_sign[b], _BODIES.index(b)))

    max_deg = max(deg_in_sign.values())
    if not max_deg > 0:
        raise ValueError("patyayini: all degrees-in-sign are zero (degenerate chart)")

    periods: list[dict] = []
    cursor = float(pravesh_jd_ut)
    prev_deg = 0.0
    for b in order:
        patyamsha = deg_in_sign[b] - prev_deg          # first body: own degree
        prev_deg = deg_in_sign[b]
        days = cycle * patyamsha / max_deg
        periods.append({
            "lord": b,
            "start_jd": cursor,
            "end_jd": cursor + days,
            "days": days,
            "patyamsha_deg": patyamsha,
        })
        cursor += days
    return periods
