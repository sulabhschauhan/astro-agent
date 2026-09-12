"""
Characterization regression test for calculate_chart() -- David (the
hardest of the 4 canonical reference charts), public fields only.

Scope (1a): lagna_chart's ascendant/ascendant_lord/rasi/rasi_lord/
nakshatra/nakshatra_pada/nakshatra_lord, and each of the 9
planetary_positions bodies' house/sign/dignity/retrograde.

Scope (1b-lock): each of the 9 planetary_positions bodies' absolute
sidereal `longitude` (0-360 deg, Lahiri), additively surfaced by
calculate_chart() in 1b. This is a DRIFT-GUARD on production's own
reproducibility (tight 1e-6 deg tolerance), not a JHora/AstroSage
oracle-parity assertion -- see the JHora comparison note above
GOLDEN_LONGITUDES below and reference/oracle_fixtures/david.md for the
actual oracle reconciliation.

dasha/pratyantar, meta, and aspects remain explicitly OUT of scope.

This is a CHARACTERIZATION test, not an oracle-parity test: it locks
CURRENT production behavior of the zero-coverage D1 dignity/house path
so a future change is caught, not because these values are asserted
correct against JHora/AstroSage. See reference/oracle_fixtures/david.md
for the actual oracle-vs-production reconciliation.

Input is David's canonical fixture tuple, verbatim from
tests/test_chart_calculator.py's _MUNTHA_FIXTURES / tests/fixtures/
geocoded_locations.json ("David", "19 Jan 1976", "22:00", "London, UK").
The session-scoped, autouse `_patch_geocoder` fixture in tests/conftest.py
already stubs Nominatim for the whole suite -- no extra patching needed
here.
"""
import pytest

from agent.chart_calculator import calculate_chart

DAVID_INPUT = {
    "name": "David",
    "dob": "19 Jan 1976",
    "tob": "22:00",
    "place": "London, UK",
}

# GOLDEN: S127 human-reviewed characterization capture, cross-verified
# against a fresh capture on 2026-09-12. Locks CURRENT behavior of the
# zero-coverage production D1 path; NOT an oracle. sign/house/dignity/
# retrograde only -- longitudes deferred to 1b.
GOLDEN_LAGNA_CHART = {
    "ascendant": "Virgo",
    "ascendant_lord": "Mercury",
    "rasi": "Leo",
    "rasi_lord": "Sun",
    "nakshatra": "Magha",
    "nakshatra_pada": 4,
    "nakshatra_lord": "Ketu",
}

# GOLDEN: S127 human-reviewed characterization capture, cross-verified
# against a fresh capture on 2026-09-12. Locks CURRENT behavior of the
# zero-coverage production D1 path; NOT an oracle. sign/house/dignity/
# retrograde only -- longitudes deferred to 1b.
GOLDEN_PLANETARY_POSITIONS = {
    "Sun":     {"house": 5,  "sign": "Capricorn",  "dignity": "Inimical", "retrograde": False},
    "Moon":    {"house": 12, "sign": "Leo",         "dignity": "Friendly", "retrograde": False},
    "Mars":    {"house": 9,  "sign": "Taurus",      "dignity": "Neutral",  "retrograde": True},
    "Mercury": {"house": 5,  "sign": "Capricorn",   "dignity": "Neutral",  "retrograde": True},
    "Jupiter": {"house": 7,  "sign": "Pisces",      "dignity": "Own Sign", "retrograde": False},
    "Venus":   {"house": 3,  "sign": "Scorpio",     "dignity": "Neutral",  "retrograde": False},
    "Saturn":  {"house": 11, "sign": "Cancer",      "dignity": "Inimical", "retrograde": True},
    "Rahu":    {"house": 2,  "sign": "Libra",       "dignity": "Neutral",  "retrograde": True},
    "Ketu":    {"house": 8,  "sign": "Aries",       "dignity": "Neutral",  "retrograde": True},
}

# GOLDEN LONGITUDE: production sidereal (Lahiri, geometric/Camp-Y).
# Drift-guard, NOT JHora parity. Matched-mode JHora (Trad-Lahiri) deltas:
# max 30.7" (Venus), Sun -20.9" ~= annual aberration -- documented Camp-Y
# apparent-position divergence (S75/Gap A1), not drift.
_LONGITUDE_TOLERANCE_DEG = 1e-6
GOLDEN_LONGITUDES = {
    "Sun": 275.4382085195396,
    "Moon": 131.65790104926788,
    "Mars": 51.210713661689894,
    "Mercury": 282.74683007621394,
    "Jupiter": 353.9064231771519,
    "Venus": 238.73827069923064,
    "Saturn": 96.03364889141777,
    "Rahu": 204.73956801600377,
    "Ketu": 24.739568016003773,
}


@pytest.fixture(scope="module")
def david_chart():
    try:
        return calculate_chart(**DAVID_INPUT)
    except Exception as exc:
        raise RuntimeError(
            f"calculate_chart() failed for David's canonical fixture "
            f"input {DAVID_INPUT!r}: {type(exc).__name__}: {exc}"
        ) from exc


class TestLagnaChartCharacterization:
    @pytest.mark.parametrize("field", sorted(GOLDEN_LAGNA_CHART.keys()))
    def test_lagna_chart_field(self, david_chart, field):
        expected = GOLDEN_LAGNA_CHART[field]
        actual = david_chart["lagna_chart"].get(field)
        assert actual == expected, (
            f"David lagna_chart.{field}: expected {expected!r}, got {actual!r}"
        )


class TestPlanetaryPositionsCharacterization:
    @pytest.mark.parametrize("planet", sorted(GOLDEN_PLANETARY_POSITIONS.keys()))
    def test_planet_house_sign_dignity_retrograde(self, david_chart, planet):
        expected = GOLDEN_PLANETARY_POSITIONS[planet]
        actual = david_chart["planetary_positions"].get(planet, {})
        for field, expected_value in expected.items():
            actual_value = actual.get(field)
            assert actual_value == expected_value, (
                f"David {planet}.{field}: expected {expected_value!r}, "
                f"got {actual_value!r}"
            )


class TestPlanetaryLongitudeCharacterization:
    @pytest.mark.parametrize("planet", sorted(GOLDEN_LONGITUDES.keys()))
    def test_planet_longitude(self, david_chart, planet):
        expected = GOLDEN_LONGITUDES[planet]
        actual = david_chart["planetary_positions"].get(planet, {}).get("longitude")
        assert actual is not None, f"David {planet}.longitude: missing from output"
        diff = abs(actual - expected)
        assert diff <= _LONGITUDE_TOLERANCE_DEG, (
            f"David {planet}.longitude: expected {expected!r}, got {actual!r} "
            f"(diff {diff:.8f} deg exceeds tolerance {_LONGITUDE_TOLERANCE_DEG} deg)"
        )
