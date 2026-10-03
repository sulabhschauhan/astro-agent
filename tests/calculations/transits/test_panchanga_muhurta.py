"""Tier-A panchanga-limb muhurta suitability: classification + computation.

Layer A: the classical suitability tables (pure, name-based) -- the doctrine.
Layer B: live score_panchanga_muhurta(jd_ut) against Sulabh's AstroSage birth
    panchanga (Krishna Chaturthi / Siddhi / Bava), validating the jd_ut-only
    tithi/yoga/karana computation end to end.
"""
from __future__ import annotations

import pytest

from agent.calculations.transits.panchanga_muhurta import (
    score_panchanga_muhurta, tithi_suitability, yoga_suitability,
    karana_suitability, INAUSPICIOUS_YOGAS,
)


# ── Layer A: classical suitability tables (pure) ─────────────────────────────

def test_nine_inauspicious_yogas():
    assert INAUSPICIOUS_YOGAS == frozenset({
        "Vishkambha", "Atiganda", "Shula", "Ganda", "Vyaghata", "Vajra",
        "Vyatipata", "Parigha", "Vaidhriti"})


@pytest.mark.parametrize("name", sorted(INAUSPICIOUS_YOGAS))
def test_inauspicious_yogas_flagged(name):
    assert yoga_suitability(name) == "avoid"


@pytest.mark.parametrize("name", ["Priti", "Siddhi", "Shubha", "Brahma"])
def test_benefic_yogas_auspicious(name):
    assert yoga_suitability(name) == "auspicious"


@pytest.mark.parametrize("name", [
    "Sukla Chaturthi", "Krishna Chaturthi", "Sukla Navami", "Krishna Navami",
    "Sukla Chaturdashi", "Krishna Chaturdashi", "Amavasya"])
def test_rikta_and_amavasya_avoided(name):
    assert tithi_suitability(name) == "avoid"


@pytest.mark.parametrize("name", ["Sukla Pratipada", "Sukla Panchami", "Purnima"])
def test_other_tithis_auspicious(name):
    assert tithi_suitability(name) == "auspicious"


def test_karana_suitability():
    assert karana_suitability("Vishti") == "avoid"            # Bhadra
    assert karana_suitability("Sakuni") == "caution"
    assert karana_suitability("Chatushpada") == "caution"
    assert karana_suitability("Naga") == "caution"
    assert karana_suitability("Bava") == "auspicious"
    assert karana_suitability("Kintughna") == "auspicious"


def test_score_rejects_nonpositive_jd():
    with pytest.raises(ValueError, match="jd_ut"):
        score_panchanga_muhurta(0.0)


# ── Layer B: live computation vs AstroSage birth panchanga (ephemeris) ───────

def test_live_sulabh_birth_panchanga():
    from agent.chart_calculator import calculate_chart
    chart = calculate_chart("Sulabh", "6 April 1988", "00:30", "Calcutta, India")
    pm = score_panchanga_muhurta(chart["meta"]["jd_ut"])
    # AstroSage birth panchanga (report page 1): Krishna Chaturthi / Siddhi / Bava
    assert pm.tithi == "Krishna Chaturthi"
    assert pm.yoga == "Siddhi"
    assert pm.karana == "Bava"
    # classification follows: Krishna Chaturthi is Rikta (avoid), others auspicious
    assert pm.tithi_suitability == "avoid"
    assert pm.yoga_suitability == "auspicious"
    assert pm.karana_suitability == "auspicious"
    assert pm.avoid_count == 1
