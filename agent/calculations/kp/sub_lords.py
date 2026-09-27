"""
agent/calculations/kp/sub_lords.py
KP (Krishnamurti Paddhati) sub-lord table and lookup (S143).

WHAT THIS IS. KP subdivides each of the 27 nakshatras (13d20' each) into 9
segments, one per Vimshottari dasha lord, in the SAME 120-year proportion the
mahadasha cycle uses (Ketu 7, Venus 20, Sun 6, Moon 10, Mars 7, Rahu 18,
Jupiter 16, Saturn 19, Mercury 17 -- DASHA_ORDER/DASHA_YEARS, imported from
agent.chart_calculator, the SAME constants that already drive mahadasha
proportions; this is the single source of truth, not a second copy -- the
agent/calculations/dashas/vimshottari.py stub is a decoy, per the S143
handover, not where the real 120-year table lives). Within a nakshatra the 9
segments start at that nakshatra's OWN star lord and cycle through
DASHA_ORDER from there -- e.g. Ashwini (star lord Ketu) runs Ketu-Ketu,
Ketu-Venus, Ketu-Sun, ... Ketu-Mercury; Bharani (star lord Venus) runs
Venus-Venus, Venus-Sun, ... 27 nakshatras x 9 segments = 243 divisions of the
360-degree zodiac. This module builds that table once and looks up which
segment a longitude falls in -- purely mechanical/deterministic, no
cross-source doctrinal ambiguity the way some yoga definitions had.

AYANAMSHA. KP is calibrated to its OWN ayanamsha, not Lahiri -- segments run
as narrow as ~40 arcminutes, and the Lahiri/KP-ayanamsha gap (~5-6 arcmin) is
large enough to occasionally flip which sub-lord a cusp falls under (measured
S143: 2 of 48 oracle cusps flip between the two). The caller
(agent.chart_calculator.calculate_chart) computes
meta['house_cusps_kp_sidereal'] using swe.SIDM_KRISHNAMURTI specifically for
this reason -- see that module's S143 comment at the ayanamsha_kp block. This
module is agnostic to which ayanamsha produced the longitude it is given; it
only buckets a 0-360 sidereal degree into a sub-lord. Passing a
Lahiri-sidereal longitude here (e.g. meta['asc_lon_sidereal'] or a
house_lord_mapping degree) will silently give a KP answer under the wrong
ayanamsha -- always use house_cusps_kp_sidereal for this module.

VALIDATED (S143, offline) against AstroSage's own "KP System / Nakshatra
Nadi" cuspal tables (data/pdfs/{Sulabh's report, David, Sheridan, Surbhi} --
the "SUB" column of each report's Cuspal Positions table), 4 reference charts
x 12 cusps = 48 data points: 47/48 exact match using swe.SIDM_KRISHNAMURTI
ayanamsha on the caller's Placidus cusps. The one miss (David, cusp 12) sits
~4.9' from the nearest segment boundary -- the same class of cross-ephemeris/
geocoding residual chart_calculator.is_boundary_sensitive already documents
for sign boundaries (there: ~2-48 arcsec on Sun/Moon, amplified at house-cusp
precision, worse yet at David's 51N latitude), not a defect in this table's
construction. Cross-checked separately: SIDM_KRISHNAMURTI reproduced
AstroSage's own printed KP ayanamsha value to within ~23 arcsec on all 4
charts; SIDM_KRISHNAMURTI_VP291 ("KP New" in some tools) was off by ~49
arcsec on the same charts and was rejected on that basis, despite AstroSage
labelling its own column "K.P. New" -- vendor ayanamsha naming is not
standardized; SIDM_KRISHNAMURTI is what the numbers actually match. See
tests/calculations/kp/test_sub_lords.py for the full parametrized sweep,
including the one documented divergence.

Python 3.11.
"""
from __future__ import annotations

from fractions import Fraction

from agent.chart_calculator import DASHA_ORDER, DASHA_YEARS

NAKSHATRA_COUNT = 27
NAKSHATRA_SPAN_DEG = Fraction(360, NAKSHATRA_COUNT)  # 13 deg 20' exactly
_TOTAL_DASHA_YEARS = sum(DASHA_YEARS.values())  # 120, the Vimshottari cycle


def _build_table() -> tuple[tuple[float, str], ...]:
    """The 243 (segment_start_deg, sub_lord) rows, ascending, covering 0-360
    exactly. Built with Fraction arithmetic throughout so segment boundaries
    are exact rationals, not accumulated float error, then converted to float
    only at the end for the lookup table."""
    rows: list[tuple[float, str]] = []
    for nak_idx in range(NAKSHATRA_COUNT):
        nak_start = Fraction(nak_idx) * NAKSHATRA_SPAN_DEG
        # This nakshatra's own star lord starts its sub-lord sequence.
        # DASHA_ORDER has 9 entries and repeats every 9 nakshatras (27 = 9*3),
        # so nak_idx % 9 IS the star lord's index -- the same relationship
        # chart_calculator's private _NAK_LORDS table encodes (Ketu, Venus,
        # ..., Mercury) x 3; derived here rather than importing that
        # underscore-prefixed table a second time.
        start_idx = nak_idx % 9
        offset = Fraction(0)
        for k in range(9):
            lord = DASHA_ORDER[(start_idx + k) % 9]
            width = NAKSHATRA_SPAN_DEG * Fraction(DASHA_YEARS[lord], _TOTAL_DASHA_YEARS)
            rows.append((float(nak_start + offset), lord))
            offset += width
    return tuple(rows)


SUB_LORD_TABLE: tuple[tuple[float, str], ...] = _build_table()
_SEGMENT_STARTS: tuple[float, ...] = tuple(r[0] for r in SUB_LORD_TABLE)


def sub_lord_for_longitude(sidereal_lon: float) -> str:
    """The KP sub-lord (planet name) for a sidereal longitude.

    Args:
        sidereal_lon: 0-360 degree sidereal longitude, KP/Krishnamurti
            ayanamsha (see module docstring -- NOT Lahiri).

    Returns:
        Planet name, one of DASHA_ORDER. Never raises for any float input
        (wrapped mod 360); this is a closed lookup over an exhaustive table.
    """
    lon = float(sidereal_lon) % 360.0
    # Manual bisect-right minus one: the segment whose start is <= lon,
    # exclusive of the next segment's start -- so a longitude exactly ON a
    # boundary belongs to the segment that BEGINS there (KP convention: a
    # cusp at a sub-lord's own starting degree reads as that sub-lord, not
    # the prior one). No bisect module dependency; the table is fixed-size
    # (243 rows) and rebuilt once at import, so a hand-rolled binary search
    # costs nothing extra and keeps this module import-free beyond stdlib
    # Fraction.
    lo, hi = 0, len(_SEGMENT_STARTS)
    while lo < hi:
        mid = (lo + hi) // 2
        if _SEGMENT_STARTS[mid] <= lon:
            lo = mid + 1
        else:
            hi = mid
    return SUB_LORD_TABLE[lo - 1][1]


def kp_house_sub_lord(house_cusps_kp_sidereal: list[float], house: int) -> str:
    """The KP sub-lord of one house's Placidus cusp.

    Args:
        house_cusps_kp_sidereal: chart['meta']['house_cusps_kp_sidereal'] from
            calculate_chart() -- 12 floats, index 0 = house 1's cusp.
        house: 1-12.

    Returns:
        Planet name.

    Raises:
        ValueError: house not in 1..12, or the cusps list is not length 12
            (a malformed/legacy chart dict) -- fail loud here; this is a
            direct index into caller-supplied data, not a fail-soft composer
            like transit_facts/yoga_facts, so a bad shape should surface
            immediately rather than silently return a wrong house's sub-lord.
    """
    if not (1 <= house <= 12):
        raise ValueError(f"kp_house_sub_lord: house must be 1-12, got {house}")
    if not isinstance(house_cusps_kp_sidereal, (list, tuple)) or len(house_cusps_kp_sidereal) != 12:
        raise ValueError(
            "kp_house_sub_lord: house_cusps_kp_sidereal must be a 12-element "
            f"list (meta['house_cusps_kp_sidereal']); got {house_cusps_kp_sidereal!r}"
        )
    return sub_lord_for_longitude(house_cusps_kp_sidereal[house - 1])
