"""Ashtottari dasha -- 108-year, 8-lord CONDITIONAL nakshatra graha dasa.

Source / spec: PVR Narasimha Rao "Vedic Astrology: An Integrated Approach"
(Ashtottari section); cross-read against PyJHora `ashtottari.py` for the
nakshatra->lord assignment. GROUND TRUTH is the JHora v8 desktop pull for Sulabh
(data/default_user/jhora_sulabh_dashas.md, all 8 MDs expanded to AD), NOT
PyJHora -- PyJHora is a reference port and has been wrong before (Narayana AD,
S154). Validated end-to-end in tests/calculations/test_ashtottari_dasha.py.

ARCHITECTURE -- this mirrors the Vimshottari `_calc_dasha` / Yogini
(`dashas/yogini.py`) model (JD-float arithmetic, nakshatra seed, balance at
birth, proportional sub-periods), NOT Narayana (a rasi dasa with no balance and
no proportional ADs). Two points where a naive Yogini copy would be WRONG:

  1. BALANCE IS OVER THE LORD'S FULL NAKSHATRA SPAN, not a single nakshatra.
     Each Ashtottari lord owns a BLOCK of nakshatras (Mars = stars 13-16 =
     53deg20'); the elapsed fraction at birth is measured across that whole
     block, not the 13deg20' of one nakshatra the way Yogini measures it.

  2. THE SEED MD STARTS PRE-BIRTH (full span), NOT truncated to birth. Yogini
     deliberately truncates period 1 to the birth moment (S72 call); the JHora
     Ashtottari oracle shows the full pre-birth seed MD with its pre-birth ADs,
     and the AD validation needs them, so this engine reproduces the full
     astronomical table. PHASE (past / current / future) is resolved at ANSWER
     time by the facts layer (S147 "intervals, not a baked now"), never here.

ANTARDASHA = PROPORTIONAL (Vimshottari-style): AD_span = MD_span * AD_lord_years
/ 108, sequence starting from the MD lord and running forward. This is settled
doctrine (no equal-vs-solar-arc fork, unlike Narayana). Proportional + mean-
sidereal year reproduces the JHora AD boundaries to <~2 days (measured residual;
same class as Yogini), nesting exactly inside each MD.

CONDITIONAL APPLICABILITY is NOT computed here -- it needs chart houses + the
lagna lord (co-lord resolved), not just the Moon's longitude, so it lives in the
facts layer as a separate, SURFACED (never gated) structured fact. This engine
always computes the full table; whether/how to weight it is the interpreter's.

Pure function of (natal Moon sidereal longitude, birth JD UT) -- no ephemeris
calls of its own (same contract as yogini.compute_yogini_dasha).

Python 3.11.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from agent.chart_calculator import NAKSHATRAS, _nakshatra

__all__ = [
    "AshtottariPeriod",
    "compute_ashtottari_dasha",
    "compute_ashtottari_bhukti",
    "current_ashtottari_period",
]

_ASHTOTTARI_YEAR_DAYS = 365.256363
"""Mean sidereal year in days. Matches JHora v8's dhasa default
(const.DHASA_YEAR_DURATION.MEAN_SIDEREAL_YEAR) and the Yogini engine's constant.
Distinct from Vimshottari's Julian-year (365.25) convention in
chart_calculator._calc_dasha (S72-flagged candidate bug, out of scope here).
Pinned by oracle match: reproduces Sulabh's JHora MD/AD boundaries to <~2 days."""

_HUMAN_SPAN_YEARS = 108
"""Total Ashtottari cycle = 108 years (the dasa's namesake)."""

# Dasa sequence order + nominal lord-years. Lord strings follow the Yogini
# fixture convention ("Merc"/"Sat"/"Jup"/"Rah"/"Ven") so the facts layer maps
# them to full planet names with the same table yogini_facts uses. Sum = 108.
_ASHTOTTARI: tuple[tuple[str, int], ...] = (
    ("Sun", 6),
    ("Moon", 15),
    ("Mars", 8),
    ("Merc", 17),
    ("Sat", 10),
    ("Jup", 19),
    ("Rah", 12),
    ("Ven", 21),
)

# Nakshatra ownership: each lord owns a contiguous block of star numbers
# (1..27, inclusive). Canonical Ashtottari assignment (JHora default seed_star=6
# / Ardra-start); Rahu's block wraps past 27 (26, 27, 1, 2). Index-aligned with
# _ASHTOTTARI above. NOTE: the Krittika-start variant some commentaries use is a
# parked alternative -- this block reproduces Sulabh's oracle (Vishakha star 16
# -> Mars, MD start lord Mars), so it is the pinned canonical map.
_STAR_SPANS: tuple[tuple[int, int], ...] = (
    (6, 9),    # Sun
    (10, 12),  # Moon
    (13, 16),  # Mars
    (17, 19),  # Mercury
    (20, 22),  # Saturn
    (23, 25),  # Jupiter
    (26, 2),   # Rahu (wraps: 26, 27, 1, 2)
    (3, 5),    # Venus
)

_LORD_INDEX = {lord: i for i, (lord, _yrs) in enumerate(_ASHTOTTARI)}

_ONE_STAR_DEG = 360.0 / 27.0  # 13deg20'


@dataclass(frozen=True)
class AshtottariPeriod:
    lord: str          # "Sun"|"Moon"|"Mars"|"Merc"|"Sat"|"Jup"|"Rah"|"Ven"
    begin_jd: float    # Julian Day UT
    end_jd: float      # Julian Day UT
    years: int         # nominal lord-years (6..21); for an AD this is still the
                       # lord's nominal years, not the sub-period's scaled length


def _count_stars(start_star: int, end_star: int) -> int:
    """Inclusive count of nakshatras from start to end, wrapping past 27."""
    if end_star < start_star:
        return (end_star + 27) - start_star + 1
    return end_star - start_star + 1


def _lord_index_for_star(star: int) -> int:
    """Index into _ASHTOTTARI of the lord owning nakshatra `star` (1..27).

    Raises:
        ValueError: `star` outside 1..27 (should never happen from a real
            nakshatra number; a guard against upstream longitude corruption).
    """
    if not 1 <= star <= 27:
        raise ValueError(f"nakshatra number must be 1..27; got {star}")
    for i, (start_star, end_star) in enumerate(_STAR_SPANS):
        s, e, n = start_star, end_star, star
        if e < s:                 # wrapping block (Rahu): lift end and a low star
            e += 27
            if n < s:
                n += 27
        if s <= n <= e:
            return i
    # Unreachable: the 8 blocks tile all 27 stars. Fail loud if that ever breaks.
    raise ValueError(f"no Ashtottari lord owns nakshatra {star} (map corrupted)")


def compute_ashtottari_dasha(
    natal_moon_lon_sidereal: float,  # degrees, [0, 360)
    birth_jd_ut: float,
    n_cycles: int = 1,               # 1 cycle = 8 MDs = 108 years (full life)
) -> list[AshtottariPeriod]:
    """Ashtottari Mahadasha (MD) sequence for a chart.

    The seed lord is the Ashtottari lord of the Moon's nakshatra; the balance at
    birth is the Moon's UNELAPSED fraction of that lord's full nakshatra BLOCK
    (see module docstring, point 1). The seed MD begins pre-birth at the balance-
    derived instant (point 2); subsequent MDs chain forward by full lord-years.

    Args:
        natal_moon_lon_sidereal: sidereal (Lahiri) Moon longitude in [0, 360).
        birth_jd_ut: birth Julian Day (UT).
        n_cycles: how many 108-year cycles to project (default 1 = a full life).

    Returns:
        MDs in time order, the seed MD first (its begin_jd is before birth).

    Raises:
        ValueError: longitude out of range, non-finite JD, or n_cycles < 1.
    """
    if not 0.0 <= natal_moon_lon_sidereal < 360.0:
        raise ValueError(
            f"Moon longitude must be in [0, 360); got {natal_moon_lon_sidereal}"
        )
    if not isinstance(birth_jd_ut, (int, float)) or birth_jd_ut != birth_jd_ut:
        raise ValueError(f"birth_jd_ut must be a finite number; got {birth_jd_ut!r}")
    if n_cycles < 1:
        raise ValueError(f"n_cycles must be >= 1; got {n_cycles}")

    nak_name, _pada, _lord = _nakshatra(natal_moon_lon_sidereal)
    star = NAKSHATRAS.index(nak_name) + 1          # 1..27
    seed_idx = _lord_index_for_star(star)
    _lord, seed_years = _ASHTOTTARI[seed_idx]
    start_star, end_star = _STAR_SPANS[seed_idx]

    # Elapsed fraction across the lord's FULL block (point 1). Lift the longitude
    # past 360 only for a wrapping block when the Moon sits in the low-numbered
    # tail of it, so the subtraction stays on one monotonic arc.
    start_deg = (start_star - 1) * _ONE_STAR_DEG
    ml = natal_moon_lon_sidereal
    if end_star < start_star and ml < start_deg:
        ml += 360.0
    total_span_deg = _count_stars(start_star, end_star) * _ONE_STAR_DEG
    elapsed_years = ((ml - start_deg) / total_span_deg) * seed_years
    md_start_jd = birth_jd_ut - elapsed_years * _ASHTOTTARI_YEAR_DAYS

    periods: list[AshtottariPeriod] = []
    cursor = md_start_jd
    for i in range(n_cycles * len(_ASHTOTTARI)):
        lord, years = _ASHTOTTARI[(seed_idx + i) % len(_ASHTOTTARI)]
        end = cursor + years * _ASHTOTTARI_YEAR_DAYS
        periods.append(
            AshtottariPeriod(lord=lord, begin_jd=cursor, end_jd=end, years=years)
        )
        cursor = end
    return periods


def compute_ashtottari_bhukti(md: AshtottariPeriod) -> list[AshtottariPeriod]:
    """The 8 proportional antardashas (bhuktis) nested inside Mahadasa `md`.

    Each AD gets MD_span * AD_lord_years / 108 of the MD's own duration, the
    sequence starting from the MD lord and running forward. Proportioning over
    the MD's ACTUAL span (end_jd - begin_jd) -- not a nominal lord-years span --
    means the 8 ADs nest exactly: the last AD ends on md.end_jd regardless of the
    year constant, so a truncated/partial MD subdivides correctly too.

    Args:
        md: one Mahadasha from compute_ashtottari_dasha().

    Returns:
        8 AD periods in time order, begin_jd of the first == md.begin_jd and
        end_jd of the last == md.end_jd.

    Raises:
        ValueError: md.lord is not an Ashtottari lord.
    """
    if md.lord not in _LORD_INDEX:
        raise ValueError(f"{md.lord!r} is not an Ashtottari lord")

    span = md.end_jd - md.begin_jd
    start_idx = _LORD_INDEX[md.lord]
    out: list[AshtottariPeriod] = []
    cursor = md.begin_jd
    for i in range(len(_ASHTOTTARI)):
        lord, years = _ASHTOTTARI[(start_idx + i) % len(_ASHTOTTARI)]
        dur = span * years / _HUMAN_SPAN_YEARS
        end = cursor + dur
        out.append(
            AshtottariPeriod(lord=lord, begin_jd=cursor, end_jd=end, years=years)
        )
        cursor = end
    # Pin the final boundary to md.end_jd so float drift never leaks past the MD.
    if out:
        last = out[-1]
        out[-1] = AshtottariPeriod(
            lord=last.lord, begin_jd=last.begin_jd, end_jd=md.end_jd, years=last.years
        )
    return out


def current_ashtottari_period(
    periods: Sequence[AshtottariPeriod],
    query_jd_ut: float,
) -> AshtottariPeriod | None:
    """The period in `periods` containing `query_jd_ut` (begin <= jd < end), or
    None if the query falls outside the projected range."""
    return next(
        (p for p in periods if p.begin_jd <= query_jd_ut < p.end_jd), None
    )
