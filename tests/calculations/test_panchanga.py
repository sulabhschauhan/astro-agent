"""Tests for agent/calculations/core/panchanga.py — P1.2a: sunrise/sunset + validation guards."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # project root

import pytest
from datetime import datetime, timedelta, timezone

from agent.calculations.core.panchanga import (
    calculate_sunrise,
    calculate_sunset,
    calculate_panchanga,
    PanchangaElement,
    ChoghadiyaWindow,
    Panchanga,
)
from tests.calculations.fixtures.panchanga_fixtures import FIXTURES

# JHora rounds to whole seconds; allow ±2 minutes for refraction model differences.
SUNRISE_SUNSET_TOLERANCE = timedelta(minutes=2)


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["name"])
def test_sunrise_matches_jhora(fixture):
    moment = fixture["moment"]
    expected_h, expected_m, expected_s = fixture["expected_sunrise_hms"]
    expected_sunrise = moment.replace(
        hour=expected_h, minute=expected_m, second=expected_s, microsecond=0
    )
    actual = calculate_sunrise(moment, fixture["latitude"], fixture["longitude"])
    delta = abs(actual - expected_sunrise)
    assert delta <= SUNRISE_SUNSET_TOLERANCE, (
        f"{fixture['name']}: sunrise off by {delta} "
        f"(expected {expected_sunrise}, got {actual})"
    )


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["name"])
def test_sunset_matches_jhora(fixture):
    moment = fixture["moment"]
    expected_h, expected_m, expected_s = fixture["expected_sunset_hms"]
    expected_sunset = moment.replace(
        hour=expected_h, minute=expected_m, second=expected_s, microsecond=0
    )
    actual = calculate_sunset(moment, fixture["latitude"], fixture["longitude"])
    delta = abs(actual - expected_sunset)
    assert delta <= SUNRISE_SUNSET_TOLERANCE, (
        f"{fixture['name']}: sunset off by {delta} "
        f"(expected {expected_sunset}, got {actual})"
    )


def test_naive_datetime_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        calculate_panchanga(datetime(2026, 6, 16, 12, 30), 22.5, 88.0)


def test_polar_latitude_rejected():
    moment = datetime(2026, 6, 16, 12, 30, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="outside v1 supported range"):
        calculate_panchanga(moment, 70.0, 88.0)
    with pytest.raises(ValueError, match="outside v1 supported range"):
        calculate_panchanga(moment, -70.0, 88.0)


def test_panchanga_not_implemented_yet():
    """P1.2a only ships sunrise/sunset. Full Panchanga lands in P1.2b."""
    moment = datetime(2026, 6, 16, 12, 30,
                      tzinfo=timezone(timedelta(hours=5, minutes=30)))
    with pytest.raises(NotImplementedError):
        calculate_panchanga(moment, 22.5666, 88.3666)
