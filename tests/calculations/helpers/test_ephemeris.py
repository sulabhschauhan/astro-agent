"""Tests for agent/calculations/helpers/ephemeris.py -- Session 52 wrapper
that closes the Session 44 ephemeris-consolidation debt (see that module's
own CITATION block).

This is a regression guard for the wrapper's own behavior, not for any
downstream module -- the 13 call sites it is meant to replace are not
touched or imported here. jd_ut values are derived the same way
test_combustion.py's fixtures derive them: via calculate_chart() on known
birth data, not hardcoded floats (Sulabh and David -- David reused
specifically because its Mercury is the corpus's one already-verified
real-chart retrograde case, per test_combustion.py's Layer A oracle row
("david", "mercury"): retro=True).

Geocoder monkeypatched by tests/conftest.py (session-scoped autouse); no
extra setup needed to call calculate_chart() here.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # project root

import pytest
import swisseph as swe

from agent.calculations.helpers.ephemeris import (
    EphemerisError,
    SiderealPosition,
    sidereal_longitude,
    sidereal_position,
)

_ALL_BODIES = list(range(swe.SUN, swe.MEAN_NODE + 1))  # SUN..MEAN_NODE inclusive


@pytest.fixture(scope="module")
def sulabh_jd():
    from agent.chart_calculator import calculate_chart
    chart = calculate_chart("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")
    return chart["meta"]["jd_ut"]


@pytest.fixture(scope="module")
def david_jd():
    from agent.chart_calculator import calculate_chart
    chart = calculate_chart("David", "19 Jan 1976", "22:00", "London, UK")
    return chart["meta"]["jd_ut"]


def _reference_longitude(jd_ut: float, planet: int) -> float:
    """Locally-computed value using the exact convention documented in
    ephemeris.py's own module docstring, independent of the wrapper under
    test."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    xx, ret = swe.calc_ut(jd_ut, planet, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
    assert ret >= 0
    return xx[0] % 360.0


# ── 1. Parity with existing convention (core regression guard) ──────────────

@pytest.mark.parametrize(
    "planet", [swe.MOON, swe.MEAN_NODE, swe.SATURN], ids=["moon", "mean_node", "saturn"]
)
def test_sidereal_longitude_matches_local_reference(sulabh_jd, planet):
    expected = _reference_longitude(sulabh_jd, planet)
    actual = sidereal_longitude(sulabh_jd, planet)
    assert actual == pytest.approx(expected, abs=1e-9)


# ── 2. sidereal_position speed semantics ─────────────────────────────────────

def test_sidereal_position_mercury_retrograde_speed_negative(david_jd):
    """David's Mercury is real-chart retrograde (test_combustion.py Layer A
    oracle row ("david", "mercury"): retro=True) -- reused here rather than
    inventing a new JD."""
    pos = sidereal_position(david_jd, swe.MERCURY)
    assert pos.speed < 0.0


def test_sidereal_position_sun_speed_positive(sulabh_jd):
    """Sun never retrogrades."""
    pos = sidereal_position(sulabh_jd, swe.SUN)
    assert pos.speed > 0.0


# ── 3. Longitude normalization ───────────────────────────────────────────────

@pytest.mark.parametrize("planet", _ALL_BODIES)
def test_sidereal_longitude_normalized(sulabh_jd, planet):
    lon = sidereal_longitude(sulabh_jd, planet)
    assert 0.0 <= lon < 360.0


# ── 4. sid_mode independence (per-call set_sid_mode, no global-state leak) ──

def test_sidereal_longitude_ignores_prior_global_sid_mode(sulabh_jd):
    expected = _reference_longitude(sulabh_jd, swe.MOON)

    # Restore Lahiri no matter what: legacy call sites (panchaka.py,
    # chandrabala.py, tarabala.py, etc.) rely on ambient Lahiri state until
    # they migrate to this wrapper -- leaking SIDM_RAMAN past this test
    # would silently skew their results in later-run tests.
    try:
        swe.set_sid_mode(swe.SIDM_RAMAN)
        actual = sidereal_longitude(sulabh_jd, swe.MOON)
    finally:
        swe.set_sid_mode(swe.SIDM_LAHIRI)

    assert actual == pytest.approx(expected, abs=1e-9)


# ── 5. Error path ─────────────────────────────────────────────────────────────

def test_sidereal_longitude_invalid_planet_raises_chained_ephemeris_error(sulabh_jd):
    invalid_planet = 99999
    with pytest.raises(EphemerisError) as exc_info:
        sidereal_longitude(sulabh_jd, invalid_planet)

    err = exc_info.value
    assert err.jd_ut == sulabh_jd
    assert err.planet == invalid_planet
    assert str(sulabh_jd) in str(err) or f"jd_ut={sulabh_jd}" in str(err)
    assert str(invalid_planet) in str(err)
    assert err.__cause__ is not None


# ── 6. Consistency between the two public functions ──────────────────────────

@pytest.mark.parametrize("planet", [swe.MOON, swe.SATURN], ids=["moon", "saturn"])
def test_sidereal_position_longitude_matches_sidereal_longitude(sulabh_jd, planet):
    pos = sidereal_position(sulabh_jd, planet)
    lon = sidereal_longitude(sulabh_jd, planet)
    assert pos.longitude == lon
