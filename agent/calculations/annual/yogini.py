"""Astro Agent -- VARSHA YOGINI DASA engine (Varshaphala / sub-engine E).

The annual (nakshatra) Yogini dasa, compressed into the solar year. VALIDATED
S156 against the JHora desktop oracle (Sulabh 2025/2026/2027 -- seed, order,
periods and start/end dates all match, dates within hours):

  SEED (starting yogini):
      effective_nak = (birth_nakshatra_no + completed_years - 1) mod 27 + 1
      seed yogini   = the yogini that rules effective_nak (star-list map below).
  ORDER = forward through the 8-yogini cycle from the seed.
  PERIOD(days) = (yogini_years / 36) * cycle_days, cycle = next_pravesh - pravesh.
  BALANCE/anchor = the seed yogini has `birth_nak_fraction_remaining` of its
      period left at the pravesh (the birth Moon's fractional position within its
      nakshatra is preserved because the seed advances by WHOLE nakshatras/year),
      so it starts (1 - frac) * seed_period BEFORE the pravesh and the cycle runs
      forward from there.

Yogini->nakshatra rulership and the 8-cycle order are ported verbatim from the
JHora engine (PyJHora dhasa.graha.yogini). Pure stdlib; fail-closed on bad input.

Python 3.11.
"""
from __future__ import annotations

__all__ = ["YOGINIS", "NAK_TO_YOGINI", "yogini_seed_index", "yogini_dasha"]

# Cycle order (index 0..7): (yogini name, graha lord, duration years). Sum = 36.
YOGINIS = (
    ("Mangala", "Moon", 1),
    ("Pingala", "Sun", 2),
    ("Dhanya", "Jupiter", 3),
    ("Bhramari", "Mars", 4),
    ("Bhadrika", "Mercury", 5),
    ("Ulka", "Saturn", 6),
    ("Siddha", "Venus", 7),
    ("Sankata", "Rahu", 8),
)
_TOTAL_YEARS = 36

# Nakshatra (1..27) ruled by each yogini (PyJHora dhasa_adhipathi_dict).
_STAR_LISTS = {
    0: (6, 14, 22), 1: (7, 15, 23), 2: (8, 16, 24), 3: (1, 9, 17, 25),
    4: (2, 10, 18, 26), 5: (3, 11, 19, 27), 6: (4, 12, 20), 7: (5, 13, 21),
}
NAK_TO_YOGINI = {nak: idx for idx, naks in _STAR_LISTS.items() for nak in naks}


def yogini_seed_index(birth_nakshatra_no: int, completed_years: int) -> int:
    """Cycle index (0..7) of the starting yogini for this Varsha.

    Raises ValueError on an out-of-range nakshatra number.
    """
    if not (1 <= int(birth_nakshatra_no) <= 27):
        raise ValueError(
            f"yogini: birth_nakshatra_no out of range (1..27): {birth_nakshatra_no}")
    eff_nak = (int(birth_nakshatra_no) + int(completed_years) - 1) % 27 + 1
    return NAK_TO_YOGINI[eff_nak]


def yogini_dasha(birth_nakshatra_no: int,
                 completed_years: int,
                 birth_nak_fraction_remaining: float,
                 pravesh_jd_ut: float,
                 next_pravesh_jd_ut: float) -> list[dict]:
    """Varsha Yogini maha-dasa periods for one annual chart.

    Args:
        birth_nakshatra_no: Moon's birth nakshatra, 1..27 (Ashwini=1).
        completed_years: whole years elapsed from birth to this pravesh.
        birth_nak_fraction_remaining: fraction (0..1] of the birth Moon's
            nakshatra still untraversed at birth (balance anchor).
        pravesh_jd_ut, next_pravesh_jd_ut: Julian Days (UT) of this/next pravesh.

    Returns:
        List of 8 {"yogini","lord","years","start_jd","end_jd","days"} in cycle
        order from the seed. The seed starts before the pravesh by its elapsed
        fraction; total span == the full cycle.

    Raises:
        ValueError: bad nakshatra number, non-positive cycle, or bad fraction.
    """
    cycle = float(next_pravesh_jd_ut) - float(pravesh_jd_ut)
    if not cycle > 0:
        raise ValueError(f"yogini: non-positive cycle ({cycle} days)")
    frac = float(birth_nak_fraction_remaining)
    if not (0.0 < frac <= 1.0):
        raise ValueError(f"yogini: fraction out of (0,1]: {frac}")

    s = yogini_seed_index(birth_nakshatra_no, completed_years)
    order = [YOGINIS[(s + i) % 8] for i in range(8)]

    # Seed yogini: `frac` of its period remains at the pravesh, so it began
    # (1 - frac) * seed_period before the pravesh.
    seed_period = order[0][2] / _TOTAL_YEARS * cycle
    cursor = float(pravesh_jd_ut) - (1.0 - frac) * seed_period

    periods: list[dict] = []
    for name, lord, years in order:
        days = years / _TOTAL_YEARS * cycle
        periods.append({
            "yogini": name, "lord": lord, "years": years,
            "start_jd": cursor, "end_jd": cursor + days, "days": days,
        })
        cursor += days
    return periods
