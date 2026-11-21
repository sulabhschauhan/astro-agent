"""TEMPORARY capture harness (S162) -- NOT a real test.

Prints the .se1 characterization goldens for Sulabh / Surbhi / Sheridan in the
exact shape of tests/regression/test_chart_calculator_characterization_david.py
(lagna chart, per-planet house/sign/dignity/retrograde, per-planet longitude).

Run once, with -s so the prints show:
    pytest tests/regression/_capture_goldens_S162.py -s -q

Paste the printed blocks back. The real per-chart drift-guard file(s) are
generated from them (sign/house cross-checked against each chart's oracle
fixture), after which THIS file is deleted. It always "passes" -- it asserts
nothing; it only captures.

Runs under the suite's conftest, so the geocoder is stubbed from
tests/fixtures/geocoded_locations.json -- the coordinates (and therefore the
captured goldens) are byte-identical to what the real drift-guard tests will
recompute.
"""
import pprint

from agent.chart_calculator import calculate_chart

# Canonical reference-chart inputs (same tuples the oracle fixtures use).
CHARTS = {
    "sulabh": {"name": "Sulabh", "dob": "6 Apr 1988", "tob": "00:30",
               "place": "Calcutta, India"},
    "surbhi": {"name": "Surbhi", "dob": "11 Sep 1992", "tob": "10:30",
               "place": "Patna, India"},
    "sheridan": {"name": "Sheridan", "dob": "27 May 1984", "tob": "08:00",
                 "place": "Durban, South Africa"},
}

_LAGNA_FIELDS = [
    "ascendant", "ascendant_lord", "rasi", "rasi_lord",
    "nakshatra", "nakshatra_pada", "nakshatra_lord",
]
_POS_FIELDS = ["house", "sign", "dignity", "retrograde"]


def test_capture_goldens():
    """Prints paste-ready golden blocks for the three reference charts."""
    for key, inp in CHARTS.items():
        chart = calculate_chart(**inp)
        lagna = {f: chart["lagna_chart"].get(f) for f in _LAGNA_FIELDS}
        positions = {}
        longitudes = {}
        for planet, data in chart["planetary_positions"].items():
            positions[planet] = {f: data.get(f) for f in _POS_FIELDS}
            longitudes[planet] = data.get("longitude")

        print(f"\n# ===== {key}: {inp['dob']} {inp['tob']} {inp['place']} =====")
        print(f"{key.upper()}_LAGNA_CHART = {pprint.pformat(lagna)}")
        print(f"{key.upper()}_PLANETARY_POSITIONS = "
              f"{pprint.pformat(positions, sort_dicts=True)}")
        print(f"{key.upper()}_LONGITUDES = "
              f"{pprint.pformat(longitudes, sort_dicts=True)}")
