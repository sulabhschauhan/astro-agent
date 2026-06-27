"""Tests for agent/calculations/compatibility/mangal_dosha.py -- P2.4.5.

Layer A: structural, no ephemeris.
Layer B: AstroSage parity, real ephemeris via calculate_chart() (geocoder
  monkeypatched by tests/conftest.py; all locations must be in
  tests/fixtures/geocoded_locations.json).
Layer C: cancellation unit tests, synthetic chart_data dicts only.
Layer D: no-dosha cases, synthetic chart_data dicts only.
"""

import dataclasses
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # project root

import pytest

from agent.calculations.compatibility.mangal_dosha import (
    MANGAL_DOSHA_HOUSES,
    MangalDoshaResult,
    _check_c5,
    _house_from,
    compute_mangal_dosha,
)

_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def _make_chart(mars: int, lagna: int, moon: int, venus: int, jupiter: int) -> dict:
    """Build a minimal chart_data dict matching calculate_chart() structure."""
    return {
        "lagna_chart": {"ascendant": _SIGNS[lagna]},
        "planetary_positions": {
            "Mars": {"sign": _SIGNS[mars]},
            "Moon": {"sign": _SIGNS[moon]},
            "Venus": {"sign": _SIGNS[venus]},
            "Jupiter": {"sign": _SIGNS[jupiter]},
        },
    }


# ── Layer A: structural, no ephemeris ─────────────────────────────────────────

def test_a1_mangal_dosha_result_is_frozen():
    result = compute_mangal_dosha(_make_chart(mars=0, lagna=0, moon=0, venus=0, jupiter=2))
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.has_dosha = False


def test_a2_mangal_dosha_houses_constant():
    assert MANGAL_DOSHA_HOUSES == frozenset({1, 2, 4, 7, 8, 12})


def test_a3_house_from_same_sign_is_1():
    assert _house_from(0, 0) == 1


def test_a4_house_from_aries_ref_pisces_is_2():
    # Mars=Aries(0), ref=Pisces(11): ((0-11)%12)+1 = 1+1 = 2
    assert _house_from(0, 11) == 2


def test_a5_house_from_libra_ref_aries_is_7():
    # Mars=Libra(6), ref=Aries(0): ((6-0)%12)+1 = 6+1 = 7
    assert _house_from(6, 0) == 7


def test_a6_only_lagna_triggers_when_moon_and_venus_in_non_dosha_houses():
    # Mars=Aries(0), Lagna=Aries(0) → house 1 (dosha)
    # Moon=Aquarius(10)            → house ((0-10)%12)+1 = 3 (not dosha)
    # Venus=Sagittarius(8)         → house ((0-8)%12)+1  = 5 (not dosha)
    result = compute_mangal_dosha(_make_chart(mars=0, lagna=0, moon=10, venus=8, jupiter=2))
    assert result.dosha_triggers == ("Lagna",)


# ── Layer B: AstroSage parity, real ephemeris ─────────────────────────────────

def _chart(dob: str, tob: str, place: str) -> dict:
    from agent.chart_calculator import calculate_chart
    return calculate_chart("test", dob, tob, place)


def test_b1_sulabh_no_mangal_dosha_or_cancelled():
    # 6 Apr 1988 00:30 IST Calcutta. AstroSage: "No Mangal Dosha".
    result = compute_mangal_dosha(_chart("6 Apr 1988", "00:30", "Calcutta, India"))
    assert result.has_dosha is False or result.is_cancelled is True
    # details must expose all 5 sign fields and 3 house fields
    for key in ("mars_sign", "lagna_sign", "moon_sign", "venus_sign", "jupiter_sign",
                "mars_house_from_lagna", "mars_house_from_moon", "mars_house_from_venus"):
        assert key in result.details, f"details missing '{key}'"


def test_b2_surbhi_no_mangal_dosha_or_cancelled():
    # 11 Sep 1992 10:30 IST Patna. AstroSage: "No Mangal Dosha".
    result = compute_mangal_dosha(_chart("11 Sep 1992", "10:30", "Patna, India"))
    assert result.has_dosha is False or result.is_cancelled is True


def test_b3_pair1_boy_has_mangal_dosha():
    # 27 Feb 1995 12:00 IST Delhi. AstroSage: "Low Mangal Dosha" -- dosha present.
    # Do not assert is_cancelled -- leave open for V1.1.
    result = compute_mangal_dosha(_chart("1995-02-27", "12:00", "Delhi, India"))
    assert result.has_dosha is True


def test_b4_pair1_girl_no_mangal_dosha_or_cancelled():
    # 24 Jan 1995 12:00 IST Delhi. AstroSage: "No Mangal Dosha".
    result = compute_mangal_dosha(_chart("1995-01-24", "12:00", "Delhi, India"))
    assert result.has_dosha is False or result.is_cancelled is True


# ── Layer C: cancellation unit tests, synthetic dicts ─────────────────────────
#
# All tests set Moon and Venus at non-dosha-house positions from Lagna so
# only Lagna triggers, isolating the cancellation logic.

def test_c1_mars_own_sign_aries_cancels():
    # Mars=Aries(0), Lagna=Pisces(11) → house ((0-11)%12)+1=2 (dosha)
    # Moon=Taurus(1) → house 3 from Pisces; Venus=Cancer(3) → house 5; safe.
    # Jupiter=Gemini(2): ((2-0)%12)+1=3, not in {5,7,9}, no conj → C5 off.
    result = compute_mangal_dosha(_make_chart(mars=0, lagna=11, moon=1, venus=3, jupiter=2))
    assert result.has_dosha is True
    assert result.is_cancelled is True
    assert "C1_mars_own_sign" in result.cancellations


def test_c2_mars_exalted_capricorn_cancels():
    # Mars=Capricorn(9), Lagna=Sagittarius(8) → house 2 (dosha)
    # Moon=Aquarius(10) → house 3 from Sag; Venus=Aries(0) → house 5; safe.
    # Jupiter=Gemini(2): ((2-9)%12)+1=6, not in {5,7,9}, no conj → C5 off.
    result = compute_mangal_dosha(_make_chart(mars=9, lagna=8, moon=10, venus=0, jupiter=2))
    assert result.has_dosha is True
    assert result.is_cancelled is True
    assert "C2_mars_exalted" in result.cancellations


def test_c3_mars_debilitated_cancer_cancels():
    # Mars=Cancer(3), Lagna=Gemini(2) → house 2 (dosha)
    # Moon=Leo(4) → house 3 from Gemini; Venus=Libra(6) → house 5; safe.
    # Jupiter=Virgo(5): ((5-3)%12)+1=3, not in {5,7,9}, no conj → C5 off.
    result = compute_mangal_dosha(_make_chart(mars=3, lagna=2, moon=4, venus=6, jupiter=5))
    assert result.has_dosha is True
    assert result.is_cancelled is True
    assert "C3_mars_debilitated" in result.cancellations


def test_c5_conjunction_cancels():
    # Mars=Taurus(1), Jupiter=Taurus(1): conjunction fires C5.
    # Lagna=Aries(0) → house 2 (dosha).
    # Moon=Gemini(2) → house 3 from Aries; Venus=Leo(4) → house 5; safe.
    result = compute_mangal_dosha(_make_chart(mars=1, lagna=0, moon=2, venus=4, jupiter=1))
    assert result.has_dosha is True
    assert result.is_cancelled is True
    assert "C5_jupiter_influence" in result.cancellations


def test_c5_aspect_cancels():
    # Mars=Taurus(1), Jupiter=Capricorn(9).
    # ((9-1)%12)+1 = 9 ∈ {5,7,9} → Jupiter's 5th aspect hits Taurus (C5).
    # Lagna=Aries(0) → house 2 (dosha).
    # Moon=Gemini(2) → house 3 from Aries; Venus=Leo(4) → house 5; safe.
    result = compute_mangal_dosha(_make_chart(mars=1, lagna=0, moon=2, venus=4, jupiter=9))
    assert result.has_dosha is True
    assert result.is_cancelled is True
    assert "C5_jupiter_influence" in result.cancellations
    # Verify the aspect formula directly.
    assert _check_c5(mars_sign=1, jupiter_sign=9) is True


def test_c7_cancer_lagna_yogakaraka_cancels():
    # Mars=Libra(6), Lagna=Cancer(3) → house ((6-3)%12)+1=4 (dosha).
    # Moon=Virgo(5) → house 3 from Cancer; Venus=Scorpio(7) → house 5; safe.
    # Jupiter=Taurus(1): ((1-6)%12)+1=8, not in {5,7,9}, no conj → C5 off.
    result = compute_mangal_dosha(_make_chart(mars=6, lagna=3, moon=5, venus=7, jupiter=1))
    assert result.has_dosha is True
    assert result.is_cancelled is True
    assert "C7_yogakaraka_lagna" in result.cancellations


def test_c7_leo_lagna_yogakaraka_cancels():
    # Mars=Scorpio(7), Lagna=Leo(4) → house ((7-4)%12)+1=4 (dosha).
    # Note: Mars=Scorpio also triggers C1 (own sign) -- both C1 and C7 fire;
    # the test checks "in", so this is expected and fine.
    # Moon=Libra(6) → house 3 from Leo; Venus=Sagittarius(8) → house 5; safe.
    # Jupiter=Virgo(5): ((5-7)%12)+1=11, not in {5,7,9}, no conj → C5 off.
    result = compute_mangal_dosha(_make_chart(mars=7, lagna=4, moon=6, venus=8, jupiter=5))
    assert result.has_dosha is True
    assert result.is_cancelled is True
    assert "C7_yogakaraka_lagna" in result.cancellations


def test_c_no_cancellation_fires():
    # Mars=Gemini(2), Lagna=Moon=Venus=Taurus(1): house 2 from all three (dosha).
    # Jupiter=Leo(4): ((4-2)%12)+1=3, not in {5,7,9}, no conj → C5 off.
    # C1: Gemini not Aries/Scorpio. C2: not Capricorn. C3: not Cancer.
    # C7: Lagna=Taurus, not Cancer/Leo.
    result = compute_mangal_dosha(_make_chart(mars=2, lagna=1, moon=1, venus=1, jupiter=4))
    assert result.has_dosha is True
    assert result.is_cancelled is False
    assert result.cancellations == ()


# ── Layer D: no-dosha cases ────────────────────────────────────────────────────

def test_d1_mars_house_3_from_all_three_no_dosha():
    # Mars=Gemini(2), Lagna=Moon=Venus=Aries(0): house ((2-0)%12)+1=3 from all.
    result = compute_mangal_dosha(_make_chart(mars=2, lagna=0, moon=0, venus=0, jupiter=5))
    assert result.has_dosha is False
    assert result.dosha_triggers == ()
    assert result.is_cancelled is False
    assert result.cancellations == ()


def test_d2_mars_house_6_from_all_three_no_dosha():
    # Mars=Virgo(5), Lagna=Moon=Venus=Aries(0): house ((5-0)%12)+1=6 from all.
    result = compute_mangal_dosha(_make_chart(mars=5, lagna=0, moon=0, venus=0, jupiter=3))
    assert result.has_dosha is False
