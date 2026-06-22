"""Tests for agent/calculations/transits/tarabala.py -- P2.3.3 Tarabala
(instant primitive).

Layer B: reference-chart fixtures, all computed programmatically (no
hand-copied expected values -- mirrors test_chandrabala.py's convention).
Locked design decisions (9-tara enum, Janma-Tara handling, nakshatra
convention, activity-dependent-Janma deferral) live in
agent/calculations/transits/tarabala.py's module docstring -- not
duplicated here.

Imports go through the direct module path
(agent.calculations.transits.tarabala), not through
agent.calculations.transits -- that package's __init__.py is intentionally
empty (Session 21 locked convention).
"""

import dataclasses
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # project root

import pytest
import swisseph as swe

import agent.calculations.transits.tarabala as tarabala_module
from agent.calculations.transits.tarabala import (
    TarabalaCategory,
    TaraName,
    compute_tarabala,
)
from agent.chart_calculator import _calc_planets, calculate_chart

_NAK_SPAN = 360.0 / 27.0

# Canonical transit fixture moment: 2026-06-20 18:30 UTC. Shared with
# test_chandrabala.py / test_gochara.py / test_sade_sati.py -- see
# test_gochara.py's ANCHOR CONVENTION note. Redefined inline per this test
# family's self-containment convention, not imported.
_JD_UT_20260620_1830_UTC = swe.julday(2026, 6, 20, 18.5)

# Second fixture moment: lands transit Moon back in Sulabh's own natal
# nakshatra (Vishakha), i.e. the Janma Tara case. Diagnostic scan found the
# Vishakha occupancy window ~2026-06-25 10:59 UTC -- 2026-06-26 13:46 UTC;
# 2026-06-26 02:00 UTC sits comfortably mid-window (~15h after ingress,
# ~12h before egress).
_JD_UT_JANMA_TARA = swe.julday(2026, 6, 26, 2.0)

# Locked 9-tara name/category table, redefined independently here (not
# imported from tarabala.py's private _TARA_NAMES_BY_NUMBER) -- mirrors
# test_chandrabala.py's pattern of redefining _FAVORABLE_HOUSES locally.
_EXPECTED_TARA_NAME_BY_NUMBER = {
    1: TaraName.JANMA,
    2: TaraName.SAMPAT,
    3: TaraName.VIPAT,
    4: TaraName.KSHEMA,
    5: TaraName.PRATYARI,
    6: TaraName.SADHAKA,
    7: TaraName.VADHA,
    8: TaraName.MITRA,
    9: TaraName.ATI_MITRA,
}
_FAVORABLE_TARA_NUMBERS = {2, 4, 6, 8, 9}


def _natal_nakshatra(name: str, dob: str, tob: str, place: str) -> int:
    """Resolve a reference chart's natal Moon nakshatra (0=Ashwini..26=Revati),
    programmatically -- mirrors test_chandrabala.py's _natal_moon_sign()
    pattern. Does NOT hand-copy from kundali_summary.txt.
    """
    chart = calculate_chart(name, dob, tob, place)
    jd_ut = chart["meta"]["jd_ut"]
    asc_lon = chart["meta"]["asc_lon_sidereal"]
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    natal_planets = _calc_planets(jd_ut, asc_lon)
    moon_lon = natal_planets["Moon"]["longitude"]
    return int(moon_lon / _NAK_SPAN) % 27


# ─── Fixture 1: Sulabh, canonical anchor ────────────────────────────────────

def test_sulabh_canonical_anchor_unfavorable():
    natal_nakshatra = _natal_nakshatra(
        "Sulabh", "6 Apr 1988", "00:30", "Calcutta, India"
    )
    # Cross-checked against data/default_user/kundali_summary.txt
    # ("Nakshatra: Vishakha") during P2.3.3 -- both agree.
    assert natal_nakshatra == 15  # Vishakha

    status = compute_tarabala(natal_nakshatra, _JD_UT_20260620_1830_UTC)

    assert status.natal_nakshatra == 15
    assert status.transit_nakshatra == 10, (
        f"Sulabh transit_nakshatra={status.transit_nakshatra}, expected 10 "
        "(Purva Phalguni at the canonical anchor)"
    )
    assert status.nakshatra_count == 23
    assert status.tara_number == 5
    assert status.tara_name == TaraName.PRATYARI
    assert status.category == TarabalaCategory.UNFAVORABLE
    assert status.is_janma_tara is False


# ─── Fixture 2: Sulabh, Janma-Tara case ─────────────────────────────────────

def test_sulabh_janma_tara_unfavorable():
    natal_nakshatra = _natal_nakshatra(
        "Sulabh", "6 Apr 1988", "00:30", "Calcutta, India"
    )

    status = compute_tarabala(natal_nakshatra, _JD_UT_JANMA_TARA)

    assert status.transit_nakshatra == natal_nakshatra, (
        "transit Moon expected back in Sulabh's natal nakshatra (Vishakha) "
        f"at this JD; got transit_nakshatra={status.transit_nakshatra} vs "
        f"natal_nakshatra={natal_nakshatra}"
    )
    assert status.nakshatra_count == 1
    assert status.tara_number == 1
    assert status.tara_name == TaraName.JANMA
    assert status.category == TarabalaCategory.UNFAVORABLE
    assert status.is_janma_tara is True


# ─── Fixture 3: David, canonical anchor (cross-chart robustness) ───────────

def test_david_canonical_anchor_cross_chart():
    natal_nakshatra = _natal_nakshatra("David", "19 Jan 1976", "22:00", "London, UK")

    status = compute_tarabala(natal_nakshatra, _JD_UT_20260620_1830_UTC)

    assert status.natal_nakshatra == natal_nakshatra
    assert 0 <= status.transit_nakshatra <= 26

    # No AstroSage Tarabala report exists for David to pin against -- expected
    # value is derived from the same formula compute_tarabala uses, written
    # out independently here, not hand-copied. Cross-chart consistency check,
    # not an independent-oracle parity check (mirrors test_chandrabala.py).
    expected_count = ((status.transit_nakshatra - natal_nakshatra) % 27) + 1
    expected_tara_number = ((expected_count - 1) % 9) + 1
    expected_category = (
        TarabalaCategory.FAVORABLE
        if expected_tara_number in _FAVORABLE_TARA_NUMBERS
        else TarabalaCategory.UNFAVORABLE
    )
    assert status.nakshatra_count == expected_count
    assert status.tara_number == expected_tara_number
    assert status.tara_name == _EXPECTED_TARA_NAME_BY_NUMBER[expected_tara_number]
    assert status.category == expected_category
    assert status.is_janma_tara == (expected_count in {1, 10, 19})


# ─── Unit tests: mechanical correctness, no fixtures ───────────────────────

def test_tarabala_status_is_frozen():
    natal_nakshatra = _natal_nakshatra(
        "Sulabh", "6 Apr 1988", "00:30", "Calcutta, India"
    )
    status = compute_tarabala(natal_nakshatra, _JD_UT_20260620_1830_UTC)
    with pytest.raises(dataclasses.FrozenInstanceError):
        status.category = TarabalaCategory.FAVORABLE


def test_natal_nakshatra_below_range_raises():
    with pytest.raises(ValueError):
        compute_tarabala(-1, _JD_UT_20260620_1830_UTC)


def test_natal_nakshatra_above_range_raises():
    with pytest.raises(ValueError):
        compute_tarabala(27, _JD_UT_20260620_1830_UTC)


def test_is_janma_tara_iff_count_in_locked_set(monkeypatch):
    natal_nakshatra = 0  # Ashwini, arbitrary fixed reference
    for transit_sign in range(27):
        monkeypatch.setattr(
            tarabala_module, "_moon_nakshatra", lambda jd, s=transit_sign: s
        )
        status = compute_tarabala(natal_nakshatra, 0.0)
        expected_count = (transit_sign - natal_nakshatra) % 27 + 1
        assert status.nakshatra_count == expected_count
        assert status.is_janma_tara == (expected_count in {1, 10, 19}), (
            f"transit_sign={transit_sign}: count={expected_count}, "
            f"is_janma_tara={status.is_janma_tara}"
        )


def test_category_favorable_iff_tara_number_in_locked_set(monkeypatch):
    natal_nakshatra = 0  # count == transit_sign + 1, so tara_number == count here
    for tara_number in range(1, 10):
        transit_sign = tara_number - 1
        monkeypatch.setattr(
            tarabala_module, "_moon_nakshatra", lambda jd, s=transit_sign: s
        )
        status = compute_tarabala(natal_nakshatra, 0.0)
        assert status.tara_number == tara_number
        expected_category = (
            TarabalaCategory.FAVORABLE
            if tara_number in _FAVORABLE_TARA_NUMBERS
            else TarabalaCategory.UNFAVORABLE
        )
        assert status.category == expected_category, (
            f"tara_number={tara_number}: category={status.category}"
        )


def test_tara_name_enum_mapping_correctness(monkeypatch):
    natal_nakshatra = 0
    for tara_number, expected_name in _EXPECTED_TARA_NAME_BY_NUMBER.items():
        transit_sign = tara_number - 1
        monkeypatch.setattr(
            tarabala_module, "_moon_nakshatra", lambda jd, s=transit_sign: s
        )
        status = compute_tarabala(natal_nakshatra, 0.0)
        assert status.tara_number == tara_number
        assert status.tara_name == expected_name, (
            f"tara_number={tara_number}: tara_name={status.tara_name}, "
            f"expected {expected_name}"
        )
