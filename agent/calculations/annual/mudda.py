"""Astro Agent -- MUDDA (Varsha-Vimshottari) DASA engine (Varshaphala / sub-engine E).

Mudda dasa compresses the Vimshottari sequence into the solar year. VALIDATED
S156 against the JHora desktop oracle (Sulabh 2025/2026/2027):

  SEED (starting lord), exact 3/3 years:
      R = (completed_years + birth_nakshatra_no) mod 9
      start lord = SEQ[(R - 1) mod 9],  SEQ = Ketu..Mercury (Vimshottari order).
  (The shankerstudy "(... - 2)/9" is OCR-wrong -- it is +2 off; do not use it.
   One-chart caveat: the seed is validated on Sulabh x 3 years; confirm on a
   second chart before treating it as fully general.)

  PERIODS:
      cycle_days = next_pravesh - this_pravesh (the ACTUAL solar year, ~365.25 d
      -- NOT a 360-day / 30-day-month year; the "x3 days" rule is wrong).
      Each lord's length ~ (Vimshottari_years / 120) * cycle_days.
      Oracle shows small sub-division wobble (Venus +1.7d / Saturn -1.7d vs pure
      proportional in 2026); kept proportional here with that documented as a
      known residual, NOT fitted away.

Pure stdlib; computes no astrology of its own. Fail-closed on bad input.

Python 3.11.
"""
from __future__ import annotations

__all__ = ["VIMSHOTTARI_SEQUENCE", "VIMSHOTTARI_YEARS", "mudda_dasha"]

# Vimshottari order (index 0..8 == positions 1..9 in the dasa-seed formula).
VIMSHOTTARI_SEQUENCE = ("Ketu", "Venus", "Sun", "Moon", "Mars",
                        "Rahu", "Jupiter", "Saturn", "Mercury")
VIMSHOTTARI_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
_TOTAL_YEARS = 120  # sum of VIMSHOTTARI_YEARS


def mudda_start_lord(completed_years: int, birth_nakshatra_no: int) -> str:
    """Starting Mudda lord via R = (completed_years + nak_no) mod 9.

    Raises ValueError on out-of-range nakshatra number.
    """
    if not (1 <= int(birth_nakshatra_no) <= 27):
        raise ValueError(
            f"mudda: birth_nakshatra_no out of range (1..27): {birth_nakshatra_no}")
    r = (int(completed_years) + int(birth_nakshatra_no)) % 9
    return VIMSHOTTARI_SEQUENCE[(r - 1) % 9]


def mudda_dasha(completed_years: int,
                birth_nakshatra_no: int,
                pravesh_jd_ut: float,
                next_pravesh_jd_ut: float) -> list[dict]:
    """Mudda maha-dasa periods for one annual chart.

    Args:
        completed_years: whole years elapsed from birth to this pravesh.
        birth_nakshatra_no: Moon's birth nakshatra, 1..27 (Ashwini=1).
        pravesh_jd_ut, next_pravesh_jd_ut: Julian Days (UT) of this/next pravesh.

    Returns:
        List of 9 {"lord", "start_jd", "end_jd", "days"} in Vimshottari order
        from the seed lord; period total == the cycle length.

    Raises:
        ValueError: bad nakshatra number or non-positive cycle.
    """
    cycle = float(next_pravesh_jd_ut) - float(pravesh_jd_ut)
    if not cycle > 0:
        raise ValueError(f"mudda: non-positive cycle ({cycle} days)")

    start = mudda_start_lord(completed_years, birth_nakshatra_no)
    start_idx = VIMSHOTTARI_SEQUENCE.index(start)
    order = [VIMSHOTTARI_SEQUENCE[(start_idx + i) % 9] for i in range(9)]

    periods: list[dict] = []
    cursor = float(pravesh_jd_ut)
    for lord in order:
        days = cycle * VIMSHOTTARI_YEARS[lord] / _TOTAL_YEARS
        periods.append({
            "lord": lord,
            "start_jd": cursor,
            "end_jd": cursor + days,
            "days": days,
        })
        cursor += days
    return periods
