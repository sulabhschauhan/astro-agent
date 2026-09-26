"""Tests for agent/calculations/transits/sade_sati.py — P2.2.2 Sade Sati.

Layer B: reference-chart parity against AstroSage's Sade Sati report,
dated 2026-06-20, for Sheridan and Surbhi; plus a THIRD reference chart,
Sulabh, added S142, against his own AstroSage Sade Sati report (printed
2026-05-24, data/pdfs/VedicReport5-24-202610-01-26PM.pdf) -- 24 rows
spanning 1987-2049, sign+phase 24/24 match, boundary dates within the
same +-1 day tolerance already accepted below. Locked design decisions
(Moon SIGN not nakshatra, phase taxonomy, retrograde-double-ingress
handling, macro-envelope gating) live in
agent/calculations/transits/sade_sati.py's module docstring -- not
duplicated here.

Tolerance note: AstroSage's Sade Sati report gives day-only granularity
(no time-of-day) AND AstroSage is an India-facing service, so its printed
calendar date is most likely IST, not UTC -- a date "D" can correspond to
anywhere from D-1 18:30 UTC to D 18:30 UTC (the IST/UTC offset is +5:30).
_DAY_TOLERANCE=1.5 (not 1.0) accounts for BOTH the day-only rounding and
this IST-day-boundary slop; Sheridan/Surbhi happened to fall under 1.0 by
chance of their specific dates, Sulabh's did not (measured S142: 1.04d and
1.19d over midnight UTC on two boundaries -- see the Sulabh tests below).
This is coarser than gochara.py's anchor-convention margin and does NOT
corroborate the provisional 18:30 UTC anchor on its own (see backlog
item #2, SESSION_LOG.md Session 21) -- a time-stamped oracle is needed
for that. Do not tighten this tolerance without a finer-grained source.
"""

import sys
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # project root

import swisseph as swe

from agent.calculations.transits.sade_sati import (
    compute_sade_sati, sade_sati_phase_for_signs, _saturn_sign, _phase_for_diff,
)
import pytest

# Canonical transit fixture moment: 2026-06-20 18:30 UTC. Shared with
# test_gochara.py's _JD_UT_20260620_1830_UTC -- see that file's ANCHOR
# CONVENTION note for the (provisional) 18:30 UTC / 00:00 IST-next-day
# rationale. Not redefined via import to keep this test file's fixture
# self-contained, matching test_gochara.py's own inline definition.
_JD_UT_20260620_1830_UTC = swe.julday(2026, 6, 20, 18.5)

_DAY_TOLERANCE = 1.5


def test_sheridan_sade_sati_rising_at_canonical_anchor():
    # Sheridan: natal Moon Aries (sign 0) -- playbook_export/reference/
    # reference_charts.md, Chart 3.
    status = compute_sade_sati(0, _JD_UT_20260620_1830_UTC)

    assert status.active is True
    assert status.phase == "RISING"
    assert status.saturn_sign == 11  # Pisces
    assert status.natal_moon_sign == 0

    pw = status.current_phase_window
    assert pw is not None
    assert pw.is_retrograde_split is True
    assert len(pw.segments) == 2

    # AstroSage Sheridan Sade Sati report, accessed Session 22:
    # row 13 "Saturn enters Pisces" ~2025-03-30; row 15 end "Saturn exits
    # Pisces" ~2028-02-23. Day-only granularity -- see module docstring.
    expected_first_ingress = swe.julday(2025, 3, 30, 0.0)
    expected_final_exit = swe.julday(2028, 2, 23, 0.0)
    assert abs(pw.first_ingress_jd - expected_first_ingress) <= _DAY_TOLERANCE, (
        f"Sheridan first_ingress_jd={pw.first_ingress_jd} vs AstroSage "
        f"row 13 ~{expected_first_ingress} (2025-03-30)"
    )
    assert abs(pw.final_exit_jd - expected_final_exit) <= _DAY_TOLERANCE, (
        f"Sheridan final_exit_jd={pw.final_exit_jd} vs AstroSage row 15 "
        f"end ~{expected_final_exit} (2028-02-23)"
    )

    # AstroSage row 19 end "Saturn exits Taurus" ~2032-05-30 -- the macro
    # envelope's overall close (RISING -> PEAK -> SETTING complete).
    macro = status.macro_sade_sati
    assert macro is not None
    expected_macro_end = swe.julday(2032, 5, 30, 0.0)
    assert abs(macro.overall_end_jd - expected_macro_end) <= _DAY_TOLERANCE, (
        f"Sheridan macro overall_end_jd={macro.overall_end_jd} vs AstroSage "
        f"row 19 end ~{expected_macro_end} (2032-05-30)"
    )


def test_surbhi_sade_sati_setting_at_canonical_anchor():
    # Surbhi: natal Moon Aquarius (sign 10) -- playbook_export/reference/
    # reference_charts.md, Chart 2.
    status = compute_sade_sati(10, _JD_UT_20260620_1830_UTC)

    assert status.active is True
    assert status.phase == "SETTING"
    assert status.saturn_sign == 11  # Pisces
    assert status.natal_moon_sign == 10

    pw = status.current_phase_window
    assert pw is not None
    assert pw.is_retrograde_split is True
    assert len(pw.segments) == 2

    # AstroSage Surbhi Sade Sati report, accessed Session 22:
    # row 16 "Saturn enters Pisces" ~2025-03-30; row 17 end "Saturn exits
    # Pisces" ~2028-02-23. Day-only granularity -- see module docstring.
    expected_first_ingress = swe.julday(2025, 3, 30, 0.0)
    expected_final_exit = swe.julday(2028, 2, 23, 0.0)
    assert abs(pw.first_ingress_jd - expected_first_ingress) <= _DAY_TOLERANCE, (
        f"Surbhi first_ingress_jd={pw.first_ingress_jd} vs AstroSage "
        f"row 16 ~{expected_first_ingress} (2025-03-30)"
    )
    assert abs(pw.final_exit_jd - expected_final_exit) <= _DAY_TOLERANCE, (
        f"Surbhi final_exit_jd={pw.final_exit_jd} vs AstroSage row 17 "
        f"end ~{expected_final_exit} (2028-02-23)"
    )

    # AstroSage row 12 "Saturn enters Capricorn" ~2020-01-24 (macro start);
    # final macro close coincides with the same Pisces exit as above.
    macro = status.macro_sade_sati
    assert macro is not None
    expected_macro_start = swe.julday(2020, 1, 24, 0.0)
    expected_macro_end = swe.julday(2028, 2, 23, 0.0)
    assert abs(macro.overall_start_jd - expected_macro_start) <= _DAY_TOLERANCE, (
        f"Surbhi macro overall_start_jd={macro.overall_start_jd} vs "
        f"AstroSage row 12 ~{expected_macro_start} (2020-01-24)"
    )
    assert abs(macro.overall_end_jd - expected_macro_end) <= _DAY_TOLERANCE, (
        f"Surbhi macro overall_end_jd={macro.overall_end_jd} vs AstroSage "
        f"row 17 end ~{expected_macro_end} (2028-02-23)"
    )


def test_surbhi_phase_none_inside_macro_envelope():
    # Surbhi, 2027-08-01 12:00 UTC: Saturn has temporarily crossed forward
    # into Aries (sign 0) -- the retrograde-double-ingress excursion
    # between the two Pisces segments seen in the canonical-anchor test
    # above. Aries is outside Surbhi's {Capricorn, Aquarius, Pisces}
    # envelope, so phase is NONE -- but transit_jd still falls inside the
    # overall macro window, so macro_sade_sati must stay populated. This
    # is the gating case the macro-envelope bug fix (Session 22) targets.
    transit_jd = swe.julday(2027, 8, 1, 12.0)
    status = compute_sade_sati(10, transit_jd)

    assert status.active is False
    assert status.phase == "NONE"
    assert status.saturn_sign == 0  # Aries
    assert status.current_phase_window is None

    macro = status.macro_sade_sati
    assert macro is not None
    expected_macro_start = swe.julday(2020, 1, 24, 0.0)
    expected_macro_end = swe.julday(2028, 2, 23, 0.0)
    assert abs(macro.overall_start_jd - expected_macro_start) <= _DAY_TOLERANCE, (
        f"Surbhi (NONE-phase) macro overall_start_jd={macro.overall_start_jd} "
        f"vs AstroSage row 12 ~{expected_macro_start} (2020-01-24)"
    )
    assert abs(macro.overall_end_jd - expected_macro_end) <= _DAY_TOLERANCE, (
        f"Surbhi (NONE-phase) macro overall_end_jd={macro.overall_end_jd} "
        f"vs AstroSage row 17 end ~{expected_macro_end} (2028-02-23)"
    )


# S142 (this session): third reference chart -- Sulabh, natal Moon Scorpio
# (sign 7), against his OWN AstroSage Sade Sati report
# (data/pdfs/VedicReport5-24-202610-01-26PM.pdf, printed 2026-05-24, pages
# 10-12; "Rasi: Scorpion"). Same day-only-granularity tolerance as
# Sheridan/Surbhi above. This is the chart the S141/S142 marriage-timing
# work is about, so it is the one reference chart where getting Sade Sati
# right actually matters to a real answer, not just to parity.

_SULABH_MOON_SIGN = 7  # Scorpio


def _mid_jd(y0, m0, d0, y1, m1, d1) -> float:
    """Julian day at the midpoint of a date range, noon UTC -- used only to
    land safely INSIDE a reported AstroSage window for the sign+phase sweep
    below, never for boundary precision (compute_sade_sati's own bisection
    supplies that, checked separately in the two anchor tests)."""
    a = datetime.date(y0, m0, d0)
    b = datetime.date(y1, m1, d1)
    mid = a + (b - a) / 2
    return swe.julday(mid.year, mid.month, mid.day, 12.0)


def test_sulabh_sade_sati_rising_at_2013_anchor():
    # AstroSage rows 9+10: Sade Sati, Libra, Rising -- 2011-11-15 -> 2012-05-15
    # and 2012-08-04 -> 2014-11-02 (the same retrograde-split phase window
    # AstroSage itself prints as two consecutive table rows). This is the
    # FALSE-POSITIVE window the S141 expert-mode pilot mis-selected for
    # marriage timing (Mercury-Venus antardasha, 2011-14): Saturn is only
    # RISING here, not yet at the Moon or ascendant.
    status = compute_sade_sati(_SULABH_MOON_SIGN, swe.julday(2013, 6, 1, 12.0))

    assert status.active is True
    assert status.phase == "RISING"
    assert status.saturn_sign == 6  # Libra
    assert status.natal_moon_sign == _SULABH_MOON_SIGN

    pw = status.current_phase_window
    assert pw is not None
    assert pw.is_retrograde_split is True
    assert len(pw.segments) == 2

    expected_seg0 = (swe.julday(2011, 11, 15, 0.0), swe.julday(2012, 5, 15, 0.0))
    expected_seg1 = (swe.julday(2012, 8, 4, 0.0), swe.julday(2014, 11, 2, 0.0))
    for (got_lo, got_hi), (exp_lo, exp_hi) in zip(pw.segments, (expected_seg0, expected_seg1)):
        assert abs(got_lo - exp_lo) <= _DAY_TOLERANCE, (
            f"Sulabh Rising segment start {got_lo} vs AstroSage {exp_lo}")
        assert abs(got_hi - exp_hi) <= _DAY_TOLERANCE, (
            f"Sulabh Rising segment end {got_hi} vs AstroSage {exp_hi}")


def test_sulabh_sade_sati_setting_at_2019_anchor():
    # AstroSage rows 12+14: Sade Sati, Sagittarius, Setting -- 2017-01-27 ->
    # 2017-06-20 and 2017-10-27 -> 2020-01-23 (again one retrograde-split
    # window across two table rows). This is the TRUE ~2019 marriage window
    # (Mercury-Rahu antardasha) the S141 benchmark (Output.txt) uses --
    # Saturn is SETTING here, i.e. transiting the ascendant's own house
    # (2nd from Moon), the corroboration transit_facts.py now surfaces.
    status = compute_sade_sati(_SULABH_MOON_SIGN, swe.julday(2019, 1, 1, 12.0))

    assert status.active is True
    assert status.phase == "SETTING"
    assert status.saturn_sign == 8  # Sagittarius
    assert status.natal_moon_sign == _SULABH_MOON_SIGN

    pw = status.current_phase_window
    assert pw is not None
    assert pw.is_retrograde_split is True
    assert len(pw.segments) == 2

    expected_seg0 = (swe.julday(2017, 1, 27, 0.0), swe.julday(2017, 6, 20, 0.0))
    expected_seg1 = (swe.julday(2017, 10, 27, 0.0), swe.julday(2020, 1, 23, 0.0))
    for (got_lo, got_hi), (exp_lo, exp_hi) in zip(pw.segments, (expected_seg0, expected_seg1)):
        assert abs(got_lo - exp_lo) <= _DAY_TOLERANCE, (
            f"Sulabh Setting segment start {got_lo} vs AstroSage {exp_lo}")
        assert abs(got_hi - exp_hi) <= _DAY_TOLERANCE, (
            f"Sulabh Setting segment end {got_hi} vs AstroSage {exp_hi}")


# Sign+phase sweep across every row AstroSage prints for Sulabh (8 Sade Sati
# windows split into 16 rows by retrograde, + 8 Small Panoti rows), 1987-2049.
# Cheap (no bisection) -- just _saturn_sign/_phase_for_diff at each window's
# midpoint -- so the whole 60-year span is covered, not just two anchors.
# Small Panoti (Saturn 4th/8th from Moon) rows assert NONE: that collapse is
# the S20 locked scope decision (out of scope for Sade Sati proper), not a
# gap -- AstroSage itself never labels these rows with a Sade Sati phase.
_SULABH_ASTROSAGE_ROWS = [
    # (sign, start_date, end_date, expected_phase_or_None)
    ("Sagittarius", (1987, 12, 17), (1990, 3, 20), "SETTING"),
    ("Sagittarius", (1990, 6, 21), (1990, 12, 14), "SETTING"),
    ("Aquarius", (1993, 3, 6), (1993, 10, 15), None),
    ("Aquarius", (1993, 11, 10), (1995, 6, 1), None),
    ("Aquarius", (1995, 8, 10), (1996, 2, 16), None),
    ("Gemini", (2002, 7, 23), (2003, 1, 8), None),
    ("Gemini", (2003, 4, 8), (2004, 9, 5), None),
    ("Gemini", (2005, 1, 14), (2005, 5, 25), None),
    ("Libra", (2011, 11, 15), (2012, 5, 15), "RISING"),
    ("Libra", (2012, 8, 4), (2014, 11, 2), "RISING"),
    ("Scorpio", (2014, 11, 3), (2017, 1, 26), "PEAK"),
    ("Sagittarius", (2017, 1, 27), (2017, 6, 20), "SETTING"),
    ("Scorpio", (2017, 6, 21), (2017, 10, 26), "PEAK"),
    ("Sagittarius", (2017, 10, 27), (2020, 1, 23), "SETTING"),
    ("Aquarius", (2022, 4, 29), (2022, 7, 12), None),
    ("Aquarius", (2023, 1, 18), (2025, 3, 29), None),
    ("Gemini", (2032, 5, 31), (2034, 7, 12), None),
    ("Libra", (2041, 1, 28), (2041, 2, 5), "RISING"),
    ("Libra", (2041, 9, 26), (2043, 12, 11), "RISING"),
    ("Scorpio", (2043, 12, 12), (2044, 6, 22), "PEAK"),
    ("Libra", (2044, 6, 23), (2044, 8, 29), "RISING"),
    ("Scorpio", (2044, 8, 30), (2046, 12, 7), "PEAK"),
    ("Sagittarius", (2046, 12, 8), (2049, 3, 6), "SETTING"),
    ("Sagittarius", (2049, 7, 10), (2049, 12, 3), "SETTING"),
]
_SIGN_INDEX = {"Aries": 0, "Taurus": 1, "Gemini": 2, "Cancer": 3, "Leo": 4, "Virgo": 5,
              "Libra": 6, "Scorpio": 7, "Sagittarius": 8, "Capricorn": 9,
              "Aquarius": 10, "Pisces": 11}


@pytest.mark.parametrize("sign,start,end,expected_phase", _SULABH_ASTROSAGE_ROWS)
def test_sulabh_sign_and_phase_matches_astrosage_row(sign, start, end, expected_phase):
    jd = _mid_jd(*start, *end)
    got_sign = _saturn_sign(jd)
    assert got_sign == _SIGN_INDEX[sign], (
        f"Saturn sign at {start}-{end} midpoint: got {got_sign}, expected {sign}")
    diff = (got_sign - _SULABH_MOON_SIGN) % 12
    got_phase = _phase_for_diff(diff)
    expected = expected_phase or "NONE"  # Small Panoti rows -> NONE by design
    assert got_phase == expected, f"Phase at {start}-{end} midpoint: got {got_phase}, expected {expected}"


# S142: sade_sati_phase_for_signs -- the cheap sign-only classifier
# transit_facts.py calls once per antardasha. Cross-checked against the
# SAME two oracle-anchored full-scan results above (Sheridan RISING,
# Surbhi SETTING at the canonical anchor) rather than against a fresh
# oracle capture, since it is a pure restatement of _phase_for_diff, the
# same rule compute_sade_sati() itself uses -- there is no new ground
# truth to validate, only that the restatement matches.

def test_phase_for_signs_matches_full_scan_sheridan_rising():
    status = compute_sade_sati(0, _JD_UT_20260620_1830_UTC)
    assert sade_sati_phase_for_signs(0, status.saturn_sign) == "RISING" == status.phase


def test_phase_for_signs_matches_full_scan_surbhi_setting():
    status = compute_sade_sati(10, _JD_UT_20260620_1830_UTC)
    assert sade_sati_phase_for_signs(10, status.saturn_sign) == "SETTING" == status.phase


def test_phase_for_signs_matches_full_scan_surbhi_none():
    # Same NONE case as test_surbhi_phase_none_inside_macro_envelope above.
    transit_jd = swe.julday(2027, 8, 1, 12.0)
    status = compute_sade_sati(10, transit_jd)
    assert sade_sati_phase_for_signs(10, status.saturn_sign) == "NONE" == status.phase


@pytest.mark.parametrize("bad_moon,bad_saturn", [(-1, 0), (12, 0), (0, -1), (0, 12)])
def test_phase_for_signs_rejects_out_of_range(bad_moon, bad_saturn):
    with pytest.raises(ValueError):
        sade_sati_phase_for_signs(bad_moon, bad_saturn)


def test_phase_for_signs_agrees_with_full_scan_across_all_144_combinations():
    # Exhaustive fuzz: every (natal_moon_sign, saturn_sign) pair must agree
    # with the module's OWN _phase_for_diff, since sade_sati_phase_for_signs
    # is declared as a pure restatement of it, not an independent rule.
    from agent.calculations.transits.sade_sati import _phase_for_diff
    for moon in range(12):
        for saturn in range(12):
            expected = _phase_for_diff((saturn - moon) % 12)
            assert sade_sati_phase_for_signs(moon, saturn) == expected
