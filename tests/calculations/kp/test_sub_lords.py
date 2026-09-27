"""
tests/calculations/kp/test_sub_lords.py
Pure logic tests for the KP 243-division sub-lord table (S143) -- table
construction invariants and the lookup function's boundary behaviour. No
chart_calculator/ephemeris dependency; see test_kp_oracle_validation.py in
this same directory for the AstroSage cuspal-table cross-check across the
4 reference charts.
"""
from __future__ import annotations

import pytest

from agent.chart_calculator import DASHA_ORDER, DASHA_YEARS
from agent.calculations.kp.sub_lords import (
    NAKSHATRA_SPAN_DEG,
    SUB_LORD_TABLE,
    kp_house_sub_lord,
    sub_lord_for_longitude,
)

_TOTAL_YEARS = sum(DASHA_YEARS.values())  # 120


# ─── Table construction ────────────────────────────────────────────────────

def test_table_has_243_rows():
    assert len(SUB_LORD_TABLE) == 27 * 9 == 243


def test_table_starts_at_zero():
    assert SUB_LORD_TABLE[0][0] == 0.0


def test_table_strictly_increasing():
    starts = [row[0] for row in SUB_LORD_TABLE]
    assert starts == sorted(starts)
    assert len(set(starts)) == len(starts)  # no duplicate boundaries


def test_table_covers_the_full_circle_exactly():
    # Reconstruct segment widths from consecutive starts (+ wrap at 360) and
    # confirm they sum to exactly 360 -- Fraction arithmetic in _build_table
    # should leave zero float drift worth worrying about at this precision.
    starts = [row[0] for row in SUB_LORD_TABLE] + [360.0]
    widths = [b - a for a, b in zip(starts, starts[1:])]
    assert sum(widths) == pytest.approx(360.0, abs=1e-9)


def test_each_nakshatra_starts_with_its_own_star_lord():
    # nak_idx % 9 is the star-lord index (DASHA_ORDER repeats every 9
    # nakshatras, 27 = 9*3) -- the first of each nakshatra's 9 segments must
    # be that same lord.
    for nak_idx in range(27):
        first_row_of_nak = SUB_LORD_TABLE[nak_idx * 9]
        expected_lord = DASHA_ORDER[nak_idx % 9]
        assert first_row_of_nak[1] == expected_lord, (
            f"nakshatra {nak_idx}: first segment should be its own star lord "
            f"{expected_lord}, got {first_row_of_nak[1]}"
        )


def test_ashwini_first_segment_is_ketu_ketu_and_46m40s_wide():
    # The single most well-known KP invariant: 0deg00'00" Aries (Ashwini,
    # star lord Ketu) opens with Ketu's own sub -- Ketu-Ketu -- 7/120 of
    # Ashwini's 13d20', i.e. 46'40" exactly.
    assert SUB_LORD_TABLE[0] == (0.0, "Ketu")
    next_start = SUB_LORD_TABLE[1][0]
    expected_width_deg = (13 + 20 / 60) * (7 / 120)
    assert next_start == pytest.approx(expected_width_deg, abs=1e-9)
    assert next_start == pytest.approx(46 / 60 + 40 / 3600, abs=1e-6)


@pytest.mark.parametrize("nak_idx", range(27))
def test_segment_widths_are_vimshottari_proportional(nak_idx):
    rows = SUB_LORD_TABLE[nak_idx * 9:(nak_idx + 1) * 9]
    starts = [r[0] for r in rows]
    next_nak_start = (
        SUB_LORD_TABLE[(nak_idx + 1) * 9][0] if nak_idx < 26 else 360.0
    )
    widths = [b - a for a, b in zip(starts, starts[1:] + [next_nak_start])]
    for (_, lord), width in zip(rows, widths):
        expected = float(NAKSHATRA_SPAN_DEG) * DASHA_YEARS[lord] / _TOTAL_YEARS
        assert width == pytest.approx(expected, abs=1e-9), (
            f"nakshatra {nak_idx}, lord {lord}: width {width} != "
            f"expected {expected} ({DASHA_YEARS[lord]}/120 of the nakshatra span)"
        )


# ─── Lookup: boundary behaviour ────────────────────────────────────────────

def test_lookup_at_zero_is_ketu():
    assert sub_lord_for_longitude(0.0) == "Ketu"


def test_lookup_just_before_first_boundary_is_still_ketu():
    boundary = SUB_LORD_TABLE[1][0]
    assert sub_lord_for_longitude(boundary - 1e-6) == "Ketu"


def test_lookup_exactly_on_a_boundary_belongs_to_the_segment_that_starts_there():
    # KP convention: a cusp AT a sub-lord's own starting degree reads as
    # that sub-lord, not the one ending there.
    boundary, lord_at_boundary = SUB_LORD_TABLE[1]
    assert sub_lord_for_longitude(boundary) == lord_at_boundary


def test_lookup_wraps_above_360():
    assert sub_lord_for_longitude(360.0) == sub_lord_for_longitude(0.0)
    assert sub_lord_for_longitude(725.0) == sub_lord_for_longitude(5.0)


def test_lookup_wraps_negative():
    assert sub_lord_for_longitude(-1.0) == sub_lord_for_longitude(359.0)


def test_lookup_last_segment_before_360_is_saturn_end_of_revati():
    # Revati (nakshatra 26) has star lord Mercury -- DASHA_ORDER[26 % 9] ==
    # DASHA_ORDER[8] == "Mercury", the LAST entry in the 9-lord cycle. Its
    # sub-sequence therefore starts at Mercury and wraps all the way around,
    # so the 9th (final) segment is the lord immediately BEFORE Mercury in
    # DASHA_ORDER, i.e. Saturn -- not Mercury itself. (First pass at this
    # test wrongly assumed the cycle "closes on itself"; asserting Mercury
    # here failed against the real table and caught the mistake.)
    assert sub_lord_for_longitude(359.999) == "Saturn"


@pytest.mark.parametrize("nak_idx", range(27))
def test_every_nakshatra_boundary_flips_to_the_new_star_lord(nak_idx):
    boundary = float(NAKSHATRA_SPAN_DEG) * nak_idx
    assert sub_lord_for_longitude(boundary) == DASHA_ORDER[nak_idx % 9]


# ─── kp_house_sub_lord ─────────────────────────────────────────────────────

def _cusps_with_house7_at(lon: float) -> list[float]:
    cusps = [0.0] * 12
    cusps[6] = lon  # house 7 = index 6
    return cusps


def test_kp_house_sub_lord_reads_the_right_index():
    cusps = _cusps_with_house7_at(0.0)  # Ketu-Ketu
    assert kp_house_sub_lord(cusps, 7) == "Ketu"
    assert kp_house_sub_lord(cusps, 1) == sub_lord_for_longitude(0.0)


@pytest.mark.parametrize("bad_house", [0, -1, 13, 100])
def test_kp_house_sub_lord_rejects_out_of_range_house(bad_house):
    with pytest.raises(ValueError):
        kp_house_sub_lord(_cusps_with_house7_at(0.0), bad_house)


@pytest.mark.parametrize("bad_cusps", [None, [], [0.0] * 11, [0.0] * 13, "not a list"])
def test_kp_house_sub_lord_rejects_malformed_cusps(bad_cusps):
    with pytest.raises(ValueError):
        kp_house_sub_lord(bad_cusps, 7)
