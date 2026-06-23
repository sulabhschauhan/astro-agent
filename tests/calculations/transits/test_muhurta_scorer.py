"""Tests for agent/calculations/transits/muhurta_scorer.py -- P2.3.5 Muhurta
composite scorer (instant primitive).

Composes Chandrabala (P2.3.1), Tarabala (P2.3.3), and Panchaka (P2.3.4) into
a single MuhurtaScore. Locked design decisions (veto-vs-vote tier mapping,
favorable_count's Panchaka exclusion, deterministic warnings) live in
agent/calculations/transits/muhurta_scorer.py's module docstring -- not
duplicated here.

Imports go through the direct module path
(agent.calculations.transits.muhurta_scorer), not through
agent.calculations.transits -- that package's __init__.py is intentionally
empty (Session 21 locked convention).
"""

import dataclasses
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # project root

import pytest
import swisseph as swe

import agent.calculations.transits.muhurta_scorer as muhurta_scorer_module
from agent.calculations.transits.chandrabala import ChandrabalaCategory, ChandrabalaStatus
from agent.calculations.transits.muhurta_scorer import (
    MuhurtaScore,
    MuhurtaTier,
    compute_muhurta_score,
)
from agent.calculations.transits.panchaka import PanchakaCategory, PanchakaStatus
from agent.calculations.transits.tarabala import TarabalaCategory, TarabalaStatus, TaraName
from agent.chart_calculator import _calc_planets, calculate_chart

_NAK_SPAN = 360.0 / 27.0

# Canonical transit fixture moment: 2026-06-20 18:30 UTC. Shared with
# test_chandrabala.py / test_tarabala.py / test_gochara.py / test_sade_sati.py
# -- see test_gochara.py's ANCHOR CONVENTION note. Redefined inline per this
# test family's self-containment convention, not imported.
_JD_UT_20260620_1830_UTC = swe.julday(2026, 6, 20, 18.5)

# Lands transit Moon inside Sulabh's Janma Rashi (Scorpio) window -- same
# anchor as test_chandrabala.py's test_sulabh_janma_rashi_favorable.
_JD_UT_JANMA_RASHI = swe.julday(2026, 6, 27, 14.5)

# Lands transit Moon back in Sulabh's own natal nakshatra (Vishakha) -- same
# anchor as test_tarabala.py's test_sulabh_janma_tara_unfavorable.
_JD_UT_JANMA_TARA = swe.julday(2026, 6, 26, 2.0)

# Lands transit Moon inside the Panchak band ([300, 360) sidereal degrees).
_JD_UT_INSIDE_PANCHAK = 2461226.5  # 2026-07-05 00:00 UTC


def _natal_moon_sign(name: str, dob: str, tob: str, place: str) -> int:
    """Resolve a reference chart's natal Moon sign (0=Aries..11=Pisces),
    programmatically -- mirrors test_chandrabala.py's _natal_moon_sign()
    pattern. Self-contained, not imported from that test file.
    """
    chart = calculate_chart(name, dob, tob, place)
    jd_ut = chart["meta"]["jd_ut"]
    asc_lon = chart["meta"]["asc_lon_sidereal"]
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    natal_planets = _calc_planets(jd_ut, asc_lon)
    moon_lon = natal_planets["Moon"]["longitude"]
    return int(moon_lon / 30.0) % 12


def _natal_nakshatra(name: str, dob: str, tob: str, place: str) -> int:
    """Resolve a reference chart's natal Moon nakshatra (0=Ashwini..26=Revati),
    programmatically -- mirrors test_tarabala.py's _natal_nakshatra() pattern.
    Self-contained, not imported from that test file.
    """
    chart = calculate_chart(name, dob, tob, place)
    jd_ut = chart["meta"]["jd_ut"]
    asc_lon = chart["meta"]["asc_lon_sidereal"]
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    natal_planets = _calc_planets(jd_ut, asc_lon)
    moon_lon = natal_planets["Moon"]["longitude"]
    return int(moon_lon / _NAK_SPAN) % 27


# ─── Fixture 1: TIER_2 at canonical anchor (Sulabh) ─────────────────────────

def test_tier_2_at_canonical_anchor():
    natal_moon_sign = _natal_moon_sign(
        "Sulabh", "6 Apr 1988", "00:30", "Calcutta, India"
    )
    janma_nakshatra = _natal_nakshatra(
        "Sulabh", "6 Apr 1988", "00:30", "Calcutta, India"
    )
    assert natal_moon_sign == 7  # Scorpio
    assert janma_nakshatra == 15  # Vishakha

    score = compute_muhurta_score(
        _JD_UT_20260620_1830_UTC, natal_moon_sign, janma_nakshatra
    )

    assert score.chandrabala == ChandrabalaCategory.FAVORABLE
    assert score.tarabala == TarabalaCategory.UNFAVORABLE
    assert score.panchaka == PanchakaCategory.NOT_PANCHAK
    assert score.tier == MuhurtaTier.TIER_2
    assert score.favorable_count == 1
    assert score.warnings == ()


# ─── Fixture 2: TIER_1 at Sulabh Janma Rashi anchor ─────────────────────────

def test_tier_1_at_janma_rashi_anchor():
    natal_moon_sign = _natal_moon_sign(
        "Sulabh", "6 Apr 1988", "00:30", "Calcutta, India"
    )
    janma_nakshatra = _natal_nakshatra(
        "Sulabh", "6 Apr 1988", "00:30", "Calcutta, India"
    )

    score = compute_muhurta_score(_JD_UT_JANMA_RASHI, natal_moon_sign, janma_nakshatra)

    assert score.chandrabala == ChandrabalaCategory.FAVORABLE
    assert score.is_janma_rashi is True
    assert score.tarabala == TarabalaCategory.FAVORABLE
    assert score.panchaka == PanchakaCategory.NOT_PANCHAK
    assert score.tier == MuhurtaTier.TIER_1
    assert score.favorable_count == 2
    assert "Janma Rashi" in score.warnings


# ─── Fixture 3: TIER_3 (both unfavorable) at Sulabh Janma Tara anchor ───────

def test_tier_3_both_unfavorable_at_janma_tara_anchor():
    natal_moon_sign = _natal_moon_sign(
        "Sulabh", "6 Apr 1988", "00:30", "Calcutta, India"
    )
    janma_nakshatra = _natal_nakshatra(
        "Sulabh", "6 Apr 1988", "00:30", "Calcutta, India"
    )

    score = compute_muhurta_score(_JD_UT_JANMA_TARA, natal_moon_sign, janma_nakshatra)

    assert score.chandrabala == ChandrabalaCategory.UNFAVORABLE
    assert score.tarabala == TarabalaCategory.UNFAVORABLE
    assert score.is_janma_tara is True
    assert score.panchaka == PanchakaCategory.NOT_PANCHAK
    assert score.tier == MuhurtaTier.TIER_3
    assert score.favorable_count == 0
    assert "Janma Tara" in score.warnings


# ─── Fixture 4: TIER_3 via Panchaka override at IS_PANCHAK anchor ──────────

def test_tier_3_via_panchaka_override_at_real_anchor():
    natal_moon_sign = _natal_moon_sign(
        "Sulabh", "6 Apr 1988", "00:30", "Calcutta, India"
    )
    janma_nakshatra = _natal_nakshatra(
        "Sulabh", "6 Apr 1988", "00:30", "Calcutta, India"
    )

    score = compute_muhurta_score(
        _JD_UT_INSIDE_PANCHAK, natal_moon_sign, janma_nakshatra
    )

    # Sub-primitive states aren't pinned here -- they depend on the transit
    # Moon's exact sign/nakshatra position, which is incidental to this
    # fixture's purpose (only the Panchaka veto is under test).
    assert score.panchaka == PanchakaCategory.PANCHAK
    assert score.tier == MuhurtaTier.TIER_3
    assert "Panchaka" in score.warnings


# ─── Monkeypatched: Panchaka veto with BOTH limbs FAVORABLE ────────────────

def test_tier_3_via_panchaka_veto_with_both_limbs_favorable(monkeypatch):
    fake_chandrabala_status = ChandrabalaStatus(
        natal_moon_sign=0,
        transit_moon_sign=2,
        house_from_natal_moon=3,
        category=ChandrabalaCategory.FAVORABLE,
        is_janma_rashi=False,
    )
    fake_tarabala_status = TarabalaStatus(
        natal_nakshatra=0,
        transit_nakshatra=1,
        nakshatra_count=2,
        tara_number=2,
        tara_name=TaraName.SAMPAT,
        category=TarabalaCategory.FAVORABLE,
        is_janma_tara=False,
    )
    fake_panchaka_status = PanchakaStatus(
        jd_ut=0.0,
        moon_longitude=310.0,
        category=PanchakaCategory.PANCHAK,
    )

    monkeypatch.setattr(
        muhurta_scorer_module, "compute_chandrabala", lambda *a, **kw: fake_chandrabala_status
    )
    monkeypatch.setattr(
        muhurta_scorer_module, "compute_tarabala", lambda *a, **kw: fake_tarabala_status
    )
    monkeypatch.setattr(
        muhurta_scorer_module, "compute_panchaka", lambda *a, **kw: fake_panchaka_status
    )

    score = compute_muhurta_score(0.0, 0, 0)

    assert score.chandrabala == ChandrabalaCategory.FAVORABLE
    assert score.tarabala == TarabalaCategory.FAVORABLE
    assert score.panchaka == PanchakaCategory.PANCHAK
    assert score.favorable_count == 2  # NOT 0 or 1 -- the count excludes Panchaka
    assert score.tier == MuhurtaTier.TIER_3  # veto fires
    assert "Panchaka" in score.warnings


# ─── Monkeypatched: warning order is stable ─────────────────────────────────

def test_warning_order_is_stable(monkeypatch):
    fake_chandrabala_status = ChandrabalaStatus(
        natal_moon_sign=0,
        transit_moon_sign=0,
        house_from_natal_moon=1,
        category=ChandrabalaCategory.FAVORABLE,
        is_janma_rashi=True,
    )
    fake_tarabala_status = TarabalaStatus(
        natal_nakshatra=0,
        transit_nakshatra=0,
        nakshatra_count=1,
        tara_number=1,
        tara_name=TaraName.JANMA,
        category=TarabalaCategory.UNFAVORABLE,
        is_janma_tara=True,
    )
    fake_panchaka_status = PanchakaStatus(
        jd_ut=0.0,
        moon_longitude=310.0,
        category=PanchakaCategory.PANCHAK,
    )

    monkeypatch.setattr(
        muhurta_scorer_module, "compute_chandrabala", lambda *a, **kw: fake_chandrabala_status
    )
    monkeypatch.setattr(
        muhurta_scorer_module, "compute_tarabala", lambda *a, **kw: fake_tarabala_status
    )
    monkeypatch.setattr(
        muhurta_scorer_module, "compute_panchaka", lambda *a, **kw: fake_panchaka_status
    )

    score = compute_muhurta_score(0.0, 0, 0)

    assert score.warnings == ("Janma Tara", "Janma Rashi", "Panchaka")


# ─── Monkeypatched: empty warnings tuple ────────────────────────────────────

def test_empty_warnings_tuple(monkeypatch):
    fake_chandrabala_status = ChandrabalaStatus(
        natal_moon_sign=0,
        transit_moon_sign=2,
        house_from_natal_moon=3,
        category=ChandrabalaCategory.FAVORABLE,
        is_janma_rashi=False,
    )
    fake_tarabala_status = TarabalaStatus(
        natal_nakshatra=0,
        transit_nakshatra=1,
        nakshatra_count=2,
        tara_number=2,
        tara_name=TaraName.SAMPAT,
        category=TarabalaCategory.FAVORABLE,
        is_janma_tara=False,
    )
    fake_panchaka_status = PanchakaStatus(
        jd_ut=0.0,
        moon_longitude=10.0,
        category=PanchakaCategory.NOT_PANCHAK,
    )

    monkeypatch.setattr(
        muhurta_scorer_module, "compute_chandrabala", lambda *a, **kw: fake_chandrabala_status
    )
    monkeypatch.setattr(
        muhurta_scorer_module, "compute_tarabala", lambda *a, **kw: fake_tarabala_status
    )
    monkeypatch.setattr(
        muhurta_scorer_module, "compute_panchaka", lambda *a, **kw: fake_panchaka_status
    )

    score = compute_muhurta_score(0.0, 0, 0)

    assert score.warnings == ()


# ─── Frozen dataclass enforcement ───────────────────────────────────────────

def test_muhurta_score_is_frozen():
    natal_moon_sign = _natal_moon_sign(
        "Sulabh", "6 Apr 1988", "00:30", "Calcutta, India"
    )
    janma_nakshatra = _natal_nakshatra(
        "Sulabh", "6 Apr 1988", "00:30", "Calcutta, India"
    )
    score = compute_muhurta_score(
        _JD_UT_20260620_1830_UTC, natal_moon_sign, janma_nakshatra
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        score.tier = MuhurtaTier.TIER_1


# ─── favorable_count range invariant (excludes Panchaka) ───────────────────

@pytest.mark.parametrize(
    "chandrabala_category,tarabala_category,expected_count",
    [
        (ChandrabalaCategory.FAVORABLE, TarabalaCategory.FAVORABLE, 2),
        (ChandrabalaCategory.FAVORABLE, TarabalaCategory.UNFAVORABLE, 1),
        (ChandrabalaCategory.UNFAVORABLE, TarabalaCategory.FAVORABLE, 1),
        (ChandrabalaCategory.UNFAVORABLE, TarabalaCategory.UNFAVORABLE, 0),
    ],
)
@pytest.mark.parametrize(
    "panchaka_category",
    [PanchakaCategory.NOT_PANCHAK, PanchakaCategory.PANCHAK],
)
def test_favorable_count_excludes_panchaka(
    monkeypatch, chandrabala_category, tarabala_category, expected_count, panchaka_category
):
    fake_chandrabala_status = ChandrabalaStatus(
        natal_moon_sign=0,
        transit_moon_sign=0,
        house_from_natal_moon=1 if chandrabala_category == ChandrabalaCategory.FAVORABLE else 2,
        category=chandrabala_category,
        is_janma_rashi=False,
    )
    fake_tarabala_status = TarabalaStatus(
        natal_nakshatra=0,
        transit_nakshatra=0,
        nakshatra_count=2 if tarabala_category == TarabalaCategory.FAVORABLE else 3,
        tara_number=2 if tarabala_category == TarabalaCategory.FAVORABLE else 3,
        tara_name=(
            TaraName.SAMPAT if tarabala_category == TarabalaCategory.FAVORABLE else TaraName.VIPAT
        ),
        category=tarabala_category,
        is_janma_tara=False,
    )
    fake_panchaka_status = PanchakaStatus(
        jd_ut=0.0,
        moon_longitude=310.0 if panchaka_category == PanchakaCategory.PANCHAK else 10.0,
        category=panchaka_category,
    )

    monkeypatch.setattr(
        muhurta_scorer_module, "compute_chandrabala", lambda *a, **kw: fake_chandrabala_status
    )
    monkeypatch.setattr(
        muhurta_scorer_module, "compute_tarabala", lambda *a, **kw: fake_tarabala_status
    )
    monkeypatch.setattr(
        muhurta_scorer_module, "compute_panchaka", lambda *a, **kw: fake_panchaka_status
    )

    score = compute_muhurta_score(0.0, 0, 0)

    assert score.favorable_count == expected_count
