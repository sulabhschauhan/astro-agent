"""Tests for agent/calculations/transits/sade_sati.py — P2.2.2 Sade Sati.

Layer B: reference-chart parity against AstroSage's Sade Sati report,
dated 2026-06-20, for Sheridan and Surbhi. Locked design decisions (Moon
SIGN not nakshatra, phase taxonomy, retrograde-double-ingress handling,
macro-envelope gating) live in agent/calculations/transits/sade_sati.py's
module docstring -- not duplicated here.

Tolerance note: AstroSage's Sade Sati report gives day-only granularity
(no time-of-day), so all boundary assertions use a +-1 day tolerance.
This is coarser than gochara.py's anchor-convention margin and does NOT
corroborate the provisional 18:30 UTC anchor on its own (see backlog
item #2, SESSION_LOG.md Session 21) -- a time-stamped oracle is needed
for that. Do not tighten this tolerance without a finer-grained source.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # project root

import swisseph as swe

from agent.calculations.transits.sade_sati import compute_sade_sati

# Canonical transit fixture moment: 2026-06-20 18:30 UTC. Shared with
# test_gochara.py's _JD_UT_20260620_1830_UTC -- see that file's ANCHOR
# CONVENTION note for the (provisional) 18:30 UTC / 00:00 IST-next-day
# rationale. Not redefined via import to keep this test file's fixture
# self-contained, matching test_gochara.py's own inline definition.
_JD_UT_20260620_1830_UTC = swe.julday(2026, 6, 20, 18.5)

_DAY_TOLERANCE = 1.0


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
