"""
tests/conftest.py
Session-scoped autouse fixture making geocoding deterministic for the
whole pytest run. ~26 live Nominatim calls/full-suite-run (calculate_chart()
-> geocode_place() with no caching) were producing cumulative HTTP 429s
(geopy.exc.GeocoderRateLimited) on repeated runs -- see SESSION_LOG.md
Session 26.

Patches the Nominatim name inside agent.chart_calculator's own namespace
(not geopy globally) for the duration of the pytest session only; restored
after the session ends. No agent/ files are touched and production runs
of frontend/app.py outside pytest are unaffected.

Fixture values come from tests/fixtures/geocoded_locations.json, captured
live one-at-a-time with 2s delays (see project history). No fall-through to
live geocoding on a cache miss -- a KeyError means the query needs capturing
before it can be used in a test.
"""
import json
from pathlib import Path

import pytest
from geopy.location import Location

import agent.chart_calculator as chart_calculator

_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "geocoded_locations.json"
_GEOCODED_LOCATIONS = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))


class _FakeNominatim:
    """Drop-in replacement for geopy.geocoders.Nominatim, backed by the
    captured fixture instead of a live HTTP call."""

    def __init__(self, *args, **kwargs):
        pass

    def geocode(self, query, *, exactly_one=True, timeout=None, **kwargs):
        try:
            data = _GEOCODED_LOCATIONS[query]
        except KeyError:
            raise KeyError(
                f"'{query}' is not in tests/fixtures/geocoded_locations.json. "
                "Capture it with a live, 2s-delayed query and add it to the "
                "fixture before using it in a test -- no fall-through to "
                "live Nominatim is permitted here."
            ) from None
        location = Location(
            data["address"], (data["latitude"], data["longitude"], 0), data["raw"]
        )
        return location if exactly_one else [location]


@pytest.fixture(autouse=True, scope="session")
def _patch_geocoder():
    original = chart_calculator.Nominatim
    chart_calculator.Nominatim = _FakeNominatim
    yield
    chart_calculator.Nominatim = original
