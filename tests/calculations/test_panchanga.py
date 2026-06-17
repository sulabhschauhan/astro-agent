"""Tests for agent/calculations/core/panchanga.py — P1.2a/P1.2b."""

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
# Longitudinal percent-left tolerance: ±0.5 percentage points absolute.
PERCENT_TOLERANCE = 0.5
# Ayanamsa tolerance: pyswisseph SIDM_LAHIRI vs JHora's Lahiri ayanamsa carry
# a measured constant cross-implementation gap of ~57.77" across all 4
# fixtures (not noise/jitter — same value regardless of date/location, so not
# a code bug). This sits within the range separating historical Lahiri
# revisions (we swept ~50 SIDM_* modes; closest alternative, SIDM_LAHIRI_1940,
# is still 4.60" off — no standard mode reproduces JHora's figure exactly).
# It is also internally consistent with the P1.2b nakshatra/yoga percent_left
# deltas already tolerated under PERCENT_TOLERANCE: a pure ayanamsa offset of
# this size predicts a ~0.12% nakshatra shift and ~0.24% yoga shift (yoga
# carries the offset twice, since it sums two ayanamsa-shifted longitudes);
# observed deltas are the same order of magnitude and ratio (~0.14-0.15% /
# ~0.30%), confirming the gap lives in ayanamsa itself rather than a
# downstream calculation error. See playbook_export/decisions/
# ayanamsa-investigation.md ("pyswisseph vs JHora" section) for the full
# sweep and the existing ~2.2-2.7" pyswisseph-vs-AstroSage figure this
# extends. 60" (1 arcmin) gives headroom above the measured 57.77" without
# being loose enough to hide a real regression.
AYANAMSA_TOLERANCE_DEG = 60 / 3600


def _dms_to_decimal(dms: tuple) -> float:
    d, m, s = dms
    return d + m / 60 + s / 3600


# ── Module-level panchanga cache (one swe call set per fixture) ───────────────
_PANCHANGA_CACHE: dict[str, Panchanga] = {}


def _panchanga(fixture: dict) -> Panchanga:
    name = fixture["name"]
    if name not in _PANCHANGA_CACHE:
        _PANCHANGA_CACHE[name] = calculate_panchanga(
            fixture["moment"], fixture["latitude"], fixture["longitude"]
        )
    return _PANCHANGA_CACHE[name]


# ── P1.2a: sunrise / sunset ───────────────────────────────────────────────────

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


# ── Validation guards (unchanged from P1.2a) ─────────────────────────────────

def test_naive_datetime_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        calculate_panchanga(datetime(2026, 6, 16, 12, 30), 22.5, 88.0)


def test_polar_latitude_rejected():
    moment = datetime(2026, 6, 16, 12, 30, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="outside v1 supported range"):
        calculate_panchanga(moment, 70.0, 88.0)
    with pytest.raises(ValueError, match="outside v1 supported range"):
        calculate_panchanga(moment, -70.0, 88.0)


# ── P1.2b: core five + hora ───────────────────────────────────────────────────

@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["name"])
def test_panchanga_tithi(fixture):
    p = _panchanga(fixture)
    assert p.tithi.name == fixture["expected_tithi_name"], (
        f"{fixture['name']}: tithi name got {p.tithi.name!r}"
    )
    assert abs(p.tithi.percent_left - fixture["expected_tithi_percent_left"]) <= PERCENT_TOLERANCE, (
        f"{fixture['name']}: tithi percent_left {p.tithi.percent_left:.2f}% "
        f"vs expected {fixture['expected_tithi_percent_left']:.2f}%"
    )


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["name"])
def test_panchanga_vara(fixture):
    p = _panchanga(fixture)
    assert p.vara.name == fixture["expected_vara_name"], (
        f"{fixture['name']}: vara got {p.vara.name!r}"
    )


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["name"])
def test_panchanga_nakshatra(fixture):
    p = _panchanga(fixture)
    assert p.nakshatra.name == fixture["expected_nakshatra_name"], (
        f"{fixture['name']}: nakshatra name got {p.nakshatra.name!r}"
    )
    assert abs(p.nakshatra.percent_left - fixture["expected_nakshatra_percent_left"]) <= PERCENT_TOLERANCE, (
        f"{fixture['name']}: nakshatra percent_left {p.nakshatra.percent_left:.2f}% "
        f"vs expected {fixture['expected_nakshatra_percent_left']:.2f}%"
    )


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["name"])
def test_panchanga_yoga(fixture):
    p = _panchanga(fixture)
    assert p.yoga.name == fixture["expected_yoga_name"], (
        f"{fixture['name']}: yoga name got {p.yoga.name!r}"
    )
    assert abs(p.yoga.percent_left - fixture["expected_yoga_percent_left"]) <= PERCENT_TOLERANCE, (
        f"{fixture['name']}: yoga percent_left {p.yoga.percent_left:.2f}% "
        f"vs expected {fixture['expected_yoga_percent_left']:.2f}%"
    )


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["name"])
def test_panchanga_karana(fixture):
    p = _panchanga(fixture)
    assert p.karana.name == fixture["expected_karana_name"], (
        f"{fixture['name']}: karana name got {p.karana.name!r}"
    )
    assert abs(p.karana.percent_left - fixture["expected_karana_percent_left"]) <= PERCENT_TOLERANCE, (
        f"{fixture['name']}: karana percent_left {p.karana.percent_left:.2f}% "
        f"vs expected {fixture['expected_karana_percent_left']:.2f}%"
    )


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["name"])
def test_panchanga_hora_lord(fixture):
    p = _panchanga(fixture)
    assert p.hora_lord == fixture["expected_hora_lord"], (
        f"{fixture['name']}: hora_lord got {p.hora_lord!r}"
    )


def test_sheridan_nakshatra_boundary():
    """Sheridan fixture: Ardra at 0.85% left triggers is_boundary, next = Punarvasu."""
    sheridan = next(f for f in FIXTURES if f["name"] == "Sheridan_20260616_1230_SAST")
    p = _panchanga(sheridan)
    assert p.nakshatra.is_boundary is True, (
        f"Sheridan: expected is_boundary=True, "
        f"got percent_left={p.nakshatra.percent_left:.2f}%"
    )
    assert p.nakshatra.next_name == "Punarvasu", (
        f"Sheridan: expected next_name='Punarvasu', got {p.nakshatra.next_name!r}"
    )


# ── P1.2c: Choghadiya ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["name"])
def test_choghadiya_day_structure(fixture):
    p = _panchanga(fixture)
    wins = p.choghadiya_day
    assert len(wins) == 8, f"{fixture['name']}: expected 8 day choghadiyas, got {len(wins)}"
    assert wins[0].name == fixture["expected_chog_day_first"], (
        f"{fixture['name']}: day chog[0] name got {wins[0].name!r}"
    )
    # contiguous sunrise→sunset
    assert wins[0].start == p.sunrise
    for i in range(7):
        assert wins[i].end == wins[i + 1].start, (
            f"{fixture['name']}: day chog[{i}].end != chog[{i+1}].start"
        )
    assert abs((wins[-1].end - p.sunset).total_seconds()) < 0.001, (
        f"{fixture['name']}: day chog last end {wins[-1].end} != sunset {p.sunset}"
    )


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["name"])
def test_choghadiya_night_structure(fixture):
    p = _panchanga(fixture)
    wins = p.choghadiya_night
    assert len(wins) == 8, f"{fixture['name']}: expected 8 night choghadiyas, got {len(wins)}"
    assert wins[0].name == fixture["expected_chog_night_first"], (
        f"{fixture['name']}: night chog[0] name got {wins[0].name!r}"
    )
    # contiguous sunset→next_sunrise (span check only — next_sunrise not stored)
    assert wins[0].start == p.sunset
    for i in range(7):
        assert wins[i].end == wins[i + 1].start, (
            f"{fixture['name']}: night chog[{i}].end != chog[{i+1}].start"
        )


# ── P1.2c: Kalam windows ─────────────────────────────────────────────────────

@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["name"])
def test_rahu_kalam_duration(fixture):
    p = _panchanga(fixture)
    day_dur = (p.sunset - p.sunrise).total_seconds()
    expected = day_dur / 8
    actual = (p.rahu_kalam[1] - p.rahu_kalam[0]).total_seconds()
    assert abs(actual - expected) < 1.0, (
        f"{fixture['name']}: rahu_kalam duration {actual:.1f}s != day/8 {expected:.1f}s"
    )


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["name"])
def test_rahu_kalam_start_time(fixture):
    """Regression test: start time stored per fixture (implementation-derived)."""
    p = _panchanga(fixture)
    h, m, s = fixture["expected_rahu_kalam_start_hms"]
    expected = fixture["moment"].replace(hour=h, minute=m, second=s, microsecond=0)
    delta = abs((p.rahu_kalam[0] - expected).total_seconds())
    assert delta < 60, (
        f"{fixture['name']}: rahu_kalam start {p.rahu_kalam[0].strftime('%H:%M:%S')} "
        f"vs expected {expected.strftime('%H:%M:%S')} (diff {delta:.0f}s)"
    )


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["name"])
def test_yamaganda_duration(fixture):
    p = _panchanga(fixture)
    day_dur = (p.sunset - p.sunrise).total_seconds()
    expected = day_dur / 8
    actual = (p.yamaganda[1] - p.yamaganda[0]).total_seconds()
    assert abs(actual - expected) < 1.0, (
        f"{fixture['name']}: yamaganda duration {actual:.1f}s != day/8 {expected:.1f}s"
    )


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["name"])
def test_gulika_kalam_duration(fixture):
    p = _panchanga(fixture)
    day_dur = (p.sunset - p.sunrise).total_seconds()
    expected = day_dur / 8
    actual = (p.gulika_kalam[1] - p.gulika_kalam[0]).total_seconds()
    assert abs(actual - expected) < 1.0, (
        f"{fixture['name']}: gulika_kalam duration {actual:.1f}s != day/8 {expected:.1f}s"
    )


# ── P1.2c: Abhijit Muhurta ───────────────────────────────────────────────────

@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["name"])
def test_abhijit_muhurta_duration(fixture):
    """Duration = day_length/15 (8th of 15 equal daytime muhurtas)."""
    p = _panchanga(fixture)
    day_dur = (p.sunset - p.sunrise).total_seconds()
    expected = day_dur / 15
    actual = (p.abhijit_muhurta[1] - p.abhijit_muhurta[0]).total_seconds()
    assert abs(actual - expected) < 1.0, (
        f"{fixture['name']}: abhijit duration {actual:.1f}s != day/15 {expected:.1f}s"
    )


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["name"])
def test_abhijit_muhurta_center_at_noon(fixture):
    """Center of Abhijit window = exact midpoint of day arc (local noon). Tolerance 1s."""
    p = _panchanga(fixture)
    center = p.abhijit_muhurta[0] + (p.abhijit_muhurta[1] - p.abhijit_muhurta[0]) / 2
    noon = p.sunrise + (p.sunset - p.sunrise) / 2
    delta = abs((center - noon).total_seconds())
    assert delta < 1.0, (
        f"{fixture['name']}: abhijit center {center.strftime('%H:%M:%S')} "
        f"off from noon {noon.strftime('%H:%M:%S')} by {delta:.1f}s"
    )


# ── P1.2d: ayanamsa ───────────────────────────────────────────────────────────
# Hardest case first: Sheridan (SAST timezone, southern hemisphere).

def test_ayanamsa_sheridan_hardest_case():
    sheridan = next(f for f in FIXTURES if f["name"] == "Sheridan_20260616_1230_SAST")
    p = _panchanga(sheridan)
    expected = _dms_to_decimal(sheridan["expected_ayanamsa_dms"])
    assert abs(p.ayanamsa - expected) <= AYANAMSA_TOLERANCE_DEG, (
        f"Sheridan: ayanamsa {p.ayanamsa:.6f} vs expected {expected:.6f} "
        f"(diff {abs(p.ayanamsa - expected) * 3600:.2f} arcsec)"
    )


def test_ayanamsa_sulabh():
    sulabh = next(f for f in FIXTURES if f["name"] == "Sulabh_20260616_1230_IST")
    p = _panchanga(sulabh)
    expected = _dms_to_decimal(sulabh["expected_ayanamsa_dms"])
    assert abs(p.ayanamsa - expected) <= AYANAMSA_TOLERANCE_DEG, (
        f"Sulabh: ayanamsa {p.ayanamsa:.6f} vs expected {expected:.6f} "
        f"(diff {abs(p.ayanamsa - expected) * 3600:.2f} arcsec)"
    )


def test_ayanamsa_surbhi():
    surbhi = next(f for f in FIXTURES if f["name"] == "Surbhi_20260616_1230_IST")
    p = _panchanga(surbhi)
    expected = _dms_to_decimal(surbhi["expected_ayanamsa_dms"])
    assert abs(p.ayanamsa - expected) <= AYANAMSA_TOLERANCE_DEG, (
        f"Surbhi: ayanamsa {p.ayanamsa:.6f} vs expected {expected:.6f} "
        f"(diff {abs(p.ayanamsa - expected) * 3600:.2f} arcsec)"
    )


def test_ayanamsa_david():
    david = next(f for f in FIXTURES if f["name"] == "David_20260616_1230_BST")
    p = _panchanga(david)
    expected = _dms_to_decimal(david["expected_ayanamsa_dms"])
    assert abs(p.ayanamsa - expected) <= AYANAMSA_TOLERANCE_DEG, (
        f"David: ayanamsa {p.ayanamsa:.6f} vs expected {expected:.6f} "
        f"(diff {abs(p.ayanamsa - expected) * 3600:.2f} arcsec)"
    )
