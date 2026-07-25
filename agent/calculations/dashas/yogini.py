"""Yogini dasha system — 36-year cycle with 8 lords.

Mirrors chart_calculator.py's Vimshottari _calc_dasha() conventions
in structure (JD-float arithmetic, birth-anchored first period --
period 1's begin_jd is the actual birth moment, not the notional
full-period start JHora's UI displays for a birth-straddling MD, see
compute_yogini_dasha()'s docstring) but NOT in year length: this
module uses the sidereal year (365.256363d), not Vimshottari's
Julian year (365.25d) -- see _YOGINI_YEAR_DAYS below.
"""

from dataclasses import dataclass
from typing import Sequence

from agent.chart_calculator import NAKSHATRAS, _nakshatra

_YOGINI_YEAR_DAYS = 365.256363
"""Sidereal year in days. Matches JHora v8 Yogini MD computation.
Distinct from Vimshottari's Julian-year convention in
chart_calculator.py._calc_dasha (S72 flagged as candidate bug;
out of scope here)."""

# Yogini cycle in fixed order (index 0..7). Sum of years = 36.
# Full cycle = 36 years. Source: PVR "Vedic Astrology: An Integrated
# Approach", Yogini Dasa section.
_YOGINIS = [
    ("Mangala",  "Moon", 1),
    ("Pingala",  "Sun",  2),
    ("Dhanya",   "Jup",  3),
    ("Bhramari", "Mars", 4),
    ("Bhadrika", "Merc", 5),
    ("Ulka",     "Sat",  6),
    ("Siddha",   "Ven",  7),
    ("Sankata",  "Rah",  8),
]


@dataclass(frozen=True)
class YoginiPeriod:
    lord: str          # "Jup" | "Mars" | "Merc" | "Sat" | "Ven"
                       # | "Rah" | "Moon" | "Sun" -- matches the JHora
                       # fixture's abbreviated form (chart_calculator.py's
                       # own Vimshottari DASHA_ORDER uses full names
                       # instead, e.g. "Jupiter"; this module's lord
                       # strings intentionally follow the Yogini
                       # fixture/§2 locked-constants convention, not
                       # Vimshottari's, since they must compare equal
                       # against jhora_sulabh.md's Yogini table).
    yogini_name: str   # "Dhanya" | "Bhramari" | "Bhadrika" | "Ulka"
                       # | "Siddha" | "Sankata" | "Mangala" | "Pingala"
    begin_jd: float    # Julian Day UT
    end_jd: float      # Julian Day UT
    years: int         # 1..8, nominal integer years for this lord
                       # (per _YOGINIS; period 1's actual duration is
                       # truncated to the balance, but this field
                       # always carries the lord's full nominal years)


def compute_yogini_dasha(
    natal_moon_lon_sidereal: float,  # degrees, 0..360
    birth_jd_ut: float,
    n_cycles: int = 3,               # 3 x 36 = 108 years coverage
) -> list[YoginiPeriod]:
    """Compute the Yogini Mahadasha (MD) sequence from birth.

    CAVEAT: The (nakshatra_number + 2) % 8 formula is validated
    against ONE reference chart (Sulabh, Vishakha -> Dhanya).
    Alternative formulations exist in classical sources (Saravali,
    Muhurtha Chinthamani variants). Surbhi/Sheridan/David
    validation pending external JHora fetch. If any of those
    charts fails this formula, revisit before treating it as
    locked.

    Period-1 begin_jd is birth-anchored (== birth_jd_ut), mirroring
    chart_calculator.py's _calc_dasha() convention -- NOT the notional
    full-period start JHora's UI displays for a birth-straddling MD.
    Confirmed divergence (Session 72 design-chat ratified): JHora's
    displayed row-1 begin date is a display artifact showing the
    conceptual full period; the effective dasha for this app starts
    at birth with truncated duration = balance_years. Periods 2..N
    chain forward from period 1's end and match JHora's begin/end
    boundaries exactly.

    CARRY-FORWARD (S72): Vimshottari _calc_dasha in
    chart_calculator.py uses Julian year (365.25d). Empirical
    evidence from Yogini S72 diagnostic strongly suggests
    sidereal year (365.256363d) is the correct classical
    convention. Vimshottari's ±37-day AD drift envelope hides
    this at MD level. Candidate bug -- revisit in a dedicated
    Vimshottari-audit session.
    """
    nak_name, _pada, _lord = _nakshatra(natal_moon_lon_sidereal)
    nakshatra_number = NAKSHATRAS.index(nak_name) + 1

    starting_index = (nakshatra_number + 2) % 8

    nak_span_deg = 360.0 / 27.0            # 13°20'
    nak_start_deg = (nakshatra_number - 1) * nak_span_deg
    fraction_traversed = (
        (natal_moon_lon_sidereal - nak_start_deg) / nak_span_deg
    )

    _, starting_lord, starting_years = _YOGINIS[starting_index]
    balance_years = (1.0 - fraction_traversed) * starting_years
    balance_days = balance_years * _YOGINI_YEAR_DAYS

    periods: list[YoginiPeriod] = []
    cursor_jd = birth_jd_ut
    n_periods = n_cycles * 8
    for i in range(n_periods):
        yogini_name, lord, years = _YOGINIS[(starting_index + i) % 8]
        duration_days = balance_days if i == 0 else years * _YOGINI_YEAR_DAYS
        end_jd = cursor_jd + duration_days
        periods.append(
            YoginiPeriod(
                lord=lord,
                yogini_name=yogini_name,
                begin_jd=cursor_jd,
                end_jd=end_jd,
                years=years,
            )
        )
        cursor_jd = end_jd

    return periods


def current_yogini_md(
    periods: Sequence[YoginiPeriod],
    query_jd_ut: float,
) -> YoginiPeriod | None:
    return next(
        (p for p in periods if p.begin_jd <= query_jd_ut < p.end_jd), None
    )
