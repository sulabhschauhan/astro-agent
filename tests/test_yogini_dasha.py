"""
tests/test_yogini_dasha.py
Unit tests for agent/calculations/dashas/yogini.py (Yogini dasha MD
computation). Formula validated against ONE reference chart (Sulabh);
Surbhi/Sheridan/David coverage is xfail pending external JHora fetch
(see yogini.py's module docstring CAVEAT).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import swisseph as swe

from agent.calculations.dashas.yogini import (
    YoginiPeriod,
    compute_yogini_dasha,
    current_yogini_md,
)
from agent.calculations.helpers import ephemeris
from agent.chart_calculator import calculate_chart

_ROOT = Path(__file__).parent.parent
_FIXTURE_PATH = _ROOT / "tests" / "fixtures" / "jhora_sulabh.md"


def _natal_inputs(name: str, dob: str, tob: str, place: str) -> tuple[float, float]:
    """(natal_moon_lon_sidereal, birth_jd_ut) for a canonical chart.

    calculate_chart()'s public return dict strips raw planetary
    longitudes (only house/sign/dignity/retrograde survive under
    planetary_positions), so degree-precision Moon longitude isn't
    obtainable from the chart dict directly. Re-derive it via the
    canonical ephemeris helper (CLAUDE.md "Ephemeris consolidation"
    lock) at the chart's own birth_jd_ut -- the same Lahiri-sidereal
    swe.calc_ut() call chart_calculator.py's _calc_planets() makes
    internally, so this reproduces the identical longitude value
    (sub-microsecond JD rounding aside, negligible for a ±1-day test
    tolerance).
    """
    chart = calculate_chart(name, dob, tob, place)
    birth_jd_ut = chart["meta"]["jd_ut"]
    natal_moon_lon_sidereal = ephemeris.sidereal_longitude(birth_jd_ut, swe.MOON)
    return natal_moon_lon_sidereal, birth_jd_ut


def _sulabh_natal_inputs() -> tuple[float, float]:
    return _natal_inputs("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")


def _ist_str_to_jd_ut(date_str: str) -> float:
    """Parse a 'YYYY-MM-DD HH:MM:SS' IST timestamp (jhora_sulabh.md's
    convention, matching its existing Vimsottari sections) into a UT
    Julian Day."""
    y, m, d = (int(x) for x in date_str[:10].split("-"))
    hh, mm, ss = (int(x) for x in date_str[11:].split(":"))
    hour_decimal = hh + mm / 60.0 + ss / 3600.0
    jd_ist = swe.julday(y, m, d, hour_decimal)
    return jd_ist - (5.5 / 24.0)


def _parse_yogini_fixture_rows() -> list[tuple[str, str, str]]:
    """Simple markdown table parser (no new dependency) for the
    '## Yogini Dasa (MD, from JHora v8)' section added to
    jhora_sulabh.md in Session 72. Returns (lord, begin_str, end_str)
    per row, in file order."""
    text = _FIXTURE_PATH.read_text(encoding="utf-8")
    section_start = text.index("## Yogini Dasa (MD, from JHora v8)")
    lines = text[section_start:].splitlines()
    rows: list[tuple[str, str, str]] = []
    in_table = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("| Lord |"):
            in_table = True
            continue
        if not in_table:
            continue
        if stripped.startswith("|---"):
            continue
        if not stripped.startswith("|"):
            break
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        rows.append((cells[0], cells[1], cells[2]))
    return rows


def test_starting_lord_sulabh_vishakha_to_dhanya():
    # Vishakha (16) must map to Dhanya (Jup).
    natal_moon_lon, birth_jd_ut = _sulabh_natal_inputs()
    periods = compute_yogini_dasha(natal_moon_lon, birth_jd_ut)
    assert periods[0].lord == "Jup"
    assert periods[0].yogini_name == "Dhanya"


def test_first_md_balance_at_birth():
    # First MD end date within ±1 day of the JHora fixture.
    natal_moon_lon, birth_jd_ut = _sulabh_natal_inputs()
    periods = compute_yogini_dasha(natal_moon_lon, birth_jd_ut)
    fixture_rows = _parse_yogini_fixture_rows()
    expected_end_jd = _ist_str_to_jd_ut(fixture_rows[0][2])
    assert abs(periods[0].end_jd - expected_end_jd) <= 1.0


def test_md_sequence_matches_jhora_fixture():
    # Parse jhora_sulabh.md Yogini section. Compare all 24 MDs: lord
    # match exact for every row; begin/end JDs within a ±1.0 day
    # tolerance for every row (re-measured post sidereal-year fix,
    # S72 diagnostic).
    #
    # A single root cause -- natal Moon longitude ephemeris precision
    # (JHora Ayanamsa 23-40-39.08 vs pyswisseph output) -- produces a
    # near-constant ~0.67-0.69 day offset. It originates in period 0's
    # balance calculation and then propagates unchanged through every
    # subsequent row (row i's begin_jd IS row i-1's end_jd), so it is
    # NOT isolated to row 0 -- an earlier ±0.25d tolerance for rows
    # 1..23 wrongly assumed isolation and was corrected after
    # re-measurement showed the offset present, and roughly constant,
    # across all 24 rows. The sidereal-year fix (_YOGINI_YEAR_DAYS)
    # already eliminated the SEPARATE compounding/growing drift a
    # Julian year produced here (confirmed: drift no longer grows with
    # elapsed time) -- this remaining ±1.0d covers only the fixed
    # ephemeris-precision offset.
    #
    # Row 0's begin_jd is NOT compared: JHora displays the conceptual
    # full period for a birth-straddling MD; this module's begin_jd is
    # birth-anchored by design (matches Vimshottari convention -- see
    # compute_yogini_dasha()'s docstring).
    natal_moon_lon, birth_jd_ut = _sulabh_natal_inputs()
    periods = compute_yogini_dasha(natal_moon_lon, birth_jd_ut)
    fixture_rows = _parse_yogini_fixture_rows()
    assert len(periods) == len(fixture_rows) == 24

    for i, (period, (lord, begin_str, end_str)) in enumerate(
        zip(periods, fixture_rows)
    ):
        assert period.lord == lord, f"row {i}: lord mismatch"
        expected_end_jd = _ist_str_to_jd_ut(end_str)
        assert abs(period.end_jd - expected_end_jd) <= 1.0, (
            f"row {i}: end_jd mismatch"
        )
        if i == 0:
            continue
        expected_begin_jd = _ist_str_to_jd_ut(begin_str)
        assert abs(period.begin_jd - expected_begin_jd) <= 1.0, (
            f"row {i}: begin_jd mismatch"
        )


def test_cycle_order_repeats():
    natal_moon_lon, birth_jd_ut = _sulabh_natal_inputs()
    periods = compute_yogini_dasha(natal_moon_lon, birth_jd_ut)
    for i in range(16):
        assert periods[i].lord == periods[i + 8].lord


def test_current_md_lookup_today():
    # As of 2026-07-24, current MD lord must be "Mars"
    # (2024-07-06 -> 2028-07-06 per fixture).
    natal_moon_lon, birth_jd_ut = _sulabh_natal_inputs()
    periods = compute_yogini_dasha(natal_moon_lon, birth_jd_ut)
    query_jd_ut = swe.julday(2026, 7, 24, 0.0)
    current = current_yogini_md(periods, query_jd_ut)
    assert current is not None
    assert current.lord == "Mars"


@pytest.mark.xfail(
    reason="Formula validated against Sulabh only; "
           "external Yogini fetch pending for other charts."
)
def test_starting_lord_surbhi():
    pytest.fail(
        "No JHora Yogini ground truth captured for Surbhi yet -- "
        "external fetch required before this assertion can be written."
    )


@pytest.mark.xfail(reason="same")
def test_starting_lord_sheridan():
    pytest.fail(
        "No JHora Yogini ground truth captured for Sheridan yet -- "
        "external fetch required before this assertion can be written."
    )


@pytest.mark.xfail(reason="same")
def test_starting_lord_david():
    pytest.fail(
        "No JHora Yogini ground truth captured for David yet -- "
        "external fetch required before this assertion can be written."
    )
